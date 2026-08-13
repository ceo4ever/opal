# PLAN: 브레인 미실체 지식 등록 차단 게이트

> 작성일: 2026-07-22 | 입력: TASK.md (ANALYSIS.md 없음 — 코드 직접 분석)
> 모드: Multi-Feature | 실행 모드: **복잡**
> 작성자: opal-plan-agent

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

브레인(지식 위키)에 "미실체 지식"(개선사항·오류·향후 계획·미확정 설계 등 아직 실재하지 않는 것)이 등록되는 것을 2층으로 차단한다. **1층**은 판별 기준을 SSOT 문서(op-brain-ingest §STEP3 + opal-brain ingest 절)에 명문화하는 WHAT 규칙이고, **2층**은 brain-tool `add-page`가 미실체 마커를 감지해 거부(`--force`+`--note` 우회)하고 `lint`가 이미 등록된 미실체 페이지를 신규 kind로 소급 검출하는 결정론적 backstop이다. 확정·실재 지식(query/ask synthesis 포함)은 그대로 허용한다.

**[핵심 코드 근거 — 설계를 좌우하는 사실]** `cmd_add_page`는 사용자 본문을 받지 않고 **템플릿 본문**을 그대로 기록한다(`opal/tools/brain-tool/brain_tool.py:503-504`, `:527`). 인자 `path`는 파일명 파생에만 쓰이며(`:491-495`), 대상 파일이 이미 있으면 `duplicate_page`로 거부한다(`:497-498`). 템플릿 본문에는 마커가 없으므로(→ D-10) 현재 구조에서는 add-page가 실제 본문을 볼 수 없다. 따라서 R-3의 "본문 미실체 마커 감지 거부"가 성립하려면 add-page에 **본문 입력 경로(`--body-file`)를 신설**해야 한다. 반면 `cmd_lint`는 디스크상의 모든 페이지 본문을 스캔하므로(`:825-872`) 작성 경로와 무관하게 동작하는 진짜 backstop이다. 이 2특성이 아래 설계의 뼈대다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 미실체 판별 기준 SSOT 명문화 (WHAT 규칙, 1층) | R-1, R-2 | P0 | F-002 |
| F-002 | 미실체 탐지 도구 게이트 (add-page 거부 + lint 소급, 2층) | R-3, R-4 | P0 | 없음 |
| F-003 | RED-first 회귀·계약 테스트 | R-5 | P0 | F-002(계약), F-003 RED는 선행 |
| F-004 | install 재배포 검증 | R-6 | P0 | F-001, F-002, F-003 |

> F-002가 공유 탐지 코어(`detect_speculative_markers`)를 R-3·R-4에 함께 제공하므로 두 요구사항을 한 기능으로 응집한다.

### 1.3 기능 의존 그래프 (ASCII)

```
F-003(RED 테스트 선작성) ─▶ F-002(GREEN 도구 구현) ─┬─▶ F-001(스킬 SSOT 문서) ─▶ F-004(install 재배포)
                                                    └────────────────────────────▶ (동일 배포에 포함)
```

RED-first 트랙이므로 실행 순서상 F-003의 RED 테스트가 F-002 구현보다 **먼저** 작성·실패 확인된다(§7 C-4).

---

## 리스크 가설 표

> PLAN 단계 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | `detect_speculative_markers` (F-002) | 오검출(FP) — 정상 concept의 정착 헤딩이 마커 토큰을 부분 포함해 정당 지식이 거부됨 | P1 | L1(단위) + 정상 회귀 | S-4, S-7 |
| H-2 | add-page `--body-file` 미도입 시 게이트 미발동 (F-001↔F-002 접합) | 스킬이 여전히 템플릿 본문으로 add-page 호출 → 실제 본문 미스캔 → 게이트 무력화 | P1 | L2(스킬 예시 grep + 실 호출) + lint backstop | S-6, S-11 |
| H-3 | `--force` 우회 정책 (F-002) | `--force`만으로(note 없이) 통과되면 백도어 — 무통제 우회 | P1 | L1 | S-2, S-3 |
| H-4 | lint `speculative` kind (F-002) | 기존 정상 active concept 과검출 → 노이즈·신뢰 저하 / 또는 미실체 페이지 미검출 | P1 | L1(정탐+오탐 양방향) | S-6, S-7 |
| H-5 | add-page 거부의 CLOSE 영향 (F-002↔op-brain-ingest) | `speculative_content` 거부가 hard-fail로 처리되면 CLOSE 자동 ingest 중단 | **P0** | L2(에러 대응 표 skip-and-continue 정합) | S-10 |
| H-6 | 하위호환 (F-002) | 기존 add-page 호출(`--body-file` 없음)이 템플릿 본문 경로에서 회귀 | P1 | L1 | S-5, S-12 |
| H-7 | frontmatter 신규 키 (F-002) | `speculative_override`/`override_note`가 `validate_frontmatter`/index 렌더를 깨뜨림 | P2 | L1 | S-3, S-12 |
| H-8 | draft-term 경로 불변 (M-3, F-002) | `_score_page` term 한정 draft 필터(`:619-629`) 손상 → query 진입점③ 회귀 | P1 | L1(회귀) | S-9 |
| H-9 | 배포 경계 (F-004) | `~/.opal/` 직접 수정 위반 / install 배포 누락 → 소스-배포 drift | P1 | L3(사람 게이트) | S-13 |
| H-10 | 추적성 (F-001, F-002) | @header `[071]` 태그·스킬 변경이력 누락 → 이력 추적 실패 | P2 | L1 | S-11, S-12 |

**용어 일관성 검토(citation-rules §7)**: FE↔BE/ERD↔코드 영역 쌍 없음(도구·문서 태스크). 신규 토큰 `speculative`(kind)·`speculative_content`(error code)·`speculative_override`/`override_note`(frontmatter)는 코드-스킬-테스트 3영역에서 **동일 철자**로 사용하도록 §2.1에서 고정한다. 불일치 리스크 없음 → `decision_required` 없음.

---

## 2. 기능별 분석

### F-001: 미실체 판별 기준 SSOT 명문화 (WHAT 규칙, 1층)

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/op-brain-ingest/SKILL.md` | §STEP3 제외 기준 SSOT (R-1) + 에러 대응 표 | 수정 |
| 스킬 | `opal/skills/opal-brain/SKILL.md` | STEP ingest 절 / lint issue kind 표 (R-2) | 수정 |
| 문서 | `opal/tools/brain-tool/README.md` | add-page/lint 서브명령 문서 정합 | 수정 |

#### 2.1.2 현재 구현
- op-brain-ingest §STEP3 "제외 기준" 표는 "오타·포맷 / trivial 설정값 / 이미 존재(멱등) / 임시·실험적 변경" 4행만 다루며 "미래·개선·오류·미확정" 부류가 없다 (`op-brain-ingest/SKILL.md:69-77`). 이 표는 `//opbr ingest task:NNN` 백필에서도 재사용되는 유일 SSOT다(`:51`).
- op-brain-ingest 하단 "brain-tool 에러 대응" 표는 `duplicate_page`/`invalid_page_type`/`frontmatter_invalid`/"그 외 ok:false"를 모두 **skip-and-continue**로 처리하고 "어떤 에러도 CLOSE를 중단시키지 않는다"를 명문화한다 (`:286-296`).
- opal-brain ingest 단일 소스 절차(`opal-brain/SKILL.md:220-239`)·ingest --all 표(`:251-259`)·task:NNN(`:286-298`)·synthesis 파일링(`:438-448`)이 모두 add-page를 호출한다. lint issue kind 표는 8종을 나열한다(`:487-496`).
- query 진입점③(미등록 term draft 등록 제안)은 `:391-406`, search 기본 draft 제외는 `:383-389`.

#### 2.1.3 영향 범위
- op-brain-ingest §STEP3 SSOT는 opal-brain task:NNN 백필(`opal-brain/SKILL.md:283-285`)이 참조한다 → **정의는 op-brain-ingest 한 곳에만** 추가하고 opal-brain은 참조로 재사용(별도 정의 금지, R-2 AC).
- add-page 호출 예시에 `--body-file`이 추가되면(F-002 접합) 게이트가 실제 발동한다(H-2). 예시 미갱신 시 lint(F-002)만 backstop.

### F-002: 미실체 탐지 도구 게이트 (add-page 거부 + lint 소급, 2층)

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/brain-tool/brain_tool.py` | `cmd_add_page`(R-3 거부 게이트)·`cmd_lint`(R-4 소급 검출)·공유 탐지 코어·`ERROR_CODES`·argparse | 수정 |

#### 2.2.2 현재 구현
- `cmd_add_page` (`brain_tool.py:478-540`): 동적 타입 검증(`:485-488`) → 파일명 파생(`:491-495`) → 존재 시 `duplicate_page`(`:497-498`) → **템플릿 로드 후 본문은 템플릿 그대로**(`:503-504`) → frontmatter 인자 치환 + `status="draft"` 강제(`:509-519`) → `validate_frontmatter`(`:521-524`) → `page_content = f"---\n{fm_yaml}\n---\n{body}"` 기록(`:526-528`) → index 재생성(`:530-534`). argparse에 `--force`/`--note`/`--body-file` **없음**(`:1202-1210`).
- `cmd_lint` (`:818-936`): 페이지 스캔(`:825`) → 페이지 루프에서 stale/broken_link/orphan/missing_link/unsourced 검출(`:836-872`) → term 채택 프로젝트 한정 term_duplicate/alias_collision(`:874-935`) → `ok(command, issues=..., issues_count=...)`. issue 항목 형식은 `{"kind","page","detail"}`(`:843-844` 등).
- 공유 유틸: `_norm`(소문자+공백제거, `:603-609`), `parse_frontmatter`(`:259-272`), `ok`/`err`(`:165-183`), `ERROR_CODES` 카탈로그(`:144-159`, 임의 변형 금지 — "모든 error 응답 값은 이 상수의 키를 참조"), `STATUS_ENUM`(`:54`), `validate_frontmatter`(`:275-314`, 미지정 키는 검사하지 않음 → 신규 키 통과).
- `_score_page` term 한정 draft 필터(`:612-629`) — [R-6 결정 2026-06-17] "draft 필터는 type=='term'에만 적용". **이번 태스크 불변(M-3).**

#### 2.2.3 영향 범위
- `add-page`를 호출하는 상류: op-brain-ingest STEP5-1(`op-brain-ingest/SKILL.md:219-233`), opal-brain ingest 4경로(`opal-brain/SKILL.md:227,251-259,290-298,438-448`), init entity 시드(`:120-126`). init 시드는 코드 @header 기반이라 미실체와 무관.
- `duplicate_page` 거부가 op-brain-ingest에서 멱등 skip으로 흡수되듯(`op-brain-ingest/SKILL.md:291`), 신규 `speculative_content`도 "그 외 ok:false" 행(`:294`)으로 자연 흡수됨 → **CLOSE 비차단(H-5)**. R-1에서 전용 행을 추가해 명문화.
- 신규 frontmatter 키(`speculative_override`/`override_note`)는 `validate_frontmatter`가 미검사(H-7 안전) — 회귀 테스트로 확인.

### F-003: RED-first 회귀·계약 테스트

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/brain-tool/tests/test_brain_tool.py` | add-page 거부/우회/회귀 + lint speculative 정탐/오탐 + draft-term 불변 테스트 클래스 신설 | 수정 |

#### 2.3.2 현재 구현
- `BrainTestCase` 베이스: tmpdir 격리(`test_brain_tool.py:97-103`), `_call`(exit_code+result, `:107-121`), `_init`(`:123-129`), `_add_page`(`:131-141`), `_write_term_page`(add-page 우회 직접 파일 작성 — status/본문 제어용, `:143-165`), `make_args`(argparse 유사 Namespace, `:56-87`), `_mock_kst`(`:51-53`).
- add-page 테스트는 `_add_page`로 호출(템플릿 본문). lint 테스트는 본문 제어가 필요할 때 파일 직접 write(`:788-799`, `:817-825`, `:891-895`). **미실체 fixture도 이 "직접 write" 패턴을 따른다**(mock 금지 계약, `:19` / `:93`).

#### 2.3.3 영향 범위
- `make_args` 기본값에 신규 인자(`note`, `body_file`) 추가 필요(`:56-87`). `force`는 이미 존재(`:60`).
- RED 작성자는 opal-test-agent(mode: red) — 구현자(op-dev-execute)와 분리(red-first §2, → D-8).

### F-004: install 재배포 검증

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/install-mac.sh` | 소스→`~/.opal/` 배포 (실행만, 파일 수정 없음) | 실행 |

#### 2.4.2 현재 구현
- `./scripts/install-mac.sh`가 `opal/` 소스를 `~/.opal/`로 배포하며 변경이력 섹션을 자동 strip한다(`docs/CONVENTIONS.md` §변경이력 작성 의무·§배포 경계).

#### 2.4.3 영향 범위
- 배포 경계상 사람 게이트(SUPERVISOR). 배포 후 `~/.opal/tools/brain-tool/brain_tool.py`가 소스와 일치(신규 `--body-file`/`speculative` 반영)해야 함(R-6 AC).

---

## 3. 기능별 설계

### F-001: 미실체 판별 기준 SSOT 명문화

#### 3.1.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/op-brain-ingest/SKILL.md` | 스킬 | §STEP3 제외 기준 표에 "미실체(미래·개선·오류·미확정 설계)" 행 추가 + 판별 신호(구조적 헤딩 우선) 1줄 + 에러 대응 표에 `speculative_content` skip-and-continue 행 + STEP5-1 add-page 예시에 `--body-file` 반영 + 변경이력 | (→ D-3 §STEP3), `op-brain-ingest/SKILL.md:69-77,286-296` |
| 2 | `opal/skills/opal-brain/SKILL.md` | 스킬 | ingest 절에 "미실체 제외 — op-brain-ingest §STEP3 SSOT 참조" 문구(별도 정의 금지) + lint issue kind 표에 `speculative` 행 + ingest add-page 예시에 `--body-file` 반영 + 변경이력. **query 진입점③·synthesis 흐름·search draft 필터는 불변(M-3)** | (→ D-4), `opal-brain/SKILL.md:283-285,487-496` |
| 3 | `opal/tools/brain-tool/README.md` | 문서 | add-page `--force`/`--note`/`--body-file`·`speculative_content`·lint `speculative` kind 문서 정합 | (→ D-5) |

#### 3.1.2 설계 결정 (WHAT 규칙 문안)

- **R-1 제외 기준 신규 행** — op-brain-ingest §STEP3 제외 기준 표에 다음 의미의 행을 추가한다 (→ D-3 §STEP3):
  - 제외 사유: **"미실체 지식 — 아직 실재하지 않는 것"**
  - 예시: "개선사항·오류·향후 계획·미확정 설계, 착수 전 설계 기록, 미해결 이슈". 이런 내용은 brain이 아니라 memory로 보낸다(활용은 memory에서).
  - 판별 신호 1줄: "구조적 신호(섹션 헤딩·전용 섹션)에 미실체 마커가 있으면 제외. 정상 지식이 산문에서 '향후'를 단순 언급하는 경우는 제외하지 않는다(오검출 최소화)." — 도구 게이트(F-002)의 탐지 방식과 정합.
- **R-2 SSOT 재사용** — opal-brain ingest 절에는 기준을 **재정의하지 않고** "미실체 제외는 op-brain-ingest §STEP3 기준을 SSOT로 재사용한다"를 명시한다(별도 정의 금지, R-2 AC / (→ D-4 §283-285) 기존 백필 재사용 패턴과 동형).
- **[MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 YYYY-MM-DD HH:mm (KST) ... 변경내용은 태스크 번호를 괄호로 포함"** → 두 SKILL.md 변경이력에 `(071)` 행 추가.
- **[MUST] `docs/CONVENTIONS.md` §배포 경계: "~/.opal/ 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(opal/...)에서 수행한다"** → 모든 변경은 `opal/` 소스 경로에서 수행(R-6에서 배포).
- op-brain-ingest 에러 대응 표에 신규 행: `speculative_content` → "미실체 마커 감지 거부. 해당 페이지를 건너뛰고 나머지 계속 진행(skip-and-continue). CLOSE 비차단." (`op-brain-ingest/SKILL.md:294` "그 외 ok:false" 정책의 구체화).

#### 3.1.3 환경 변경
해당 없음.

#### 3.1.4 배치/마이그레이션
해당 없음 (기존 active concept 자동 거부·삭제 없음 — 하위호환 제약).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-101 | R-1 AC | 산출물 검사(grep) | op-brain-ingest §STEP3 제외 기준 표에 미실체 행 + 예시(개선·오류·향후·미확정 설계) 존재 |
| TS-102 | R-2 AC | 산출물 검사(grep) | opal-brain ingest 절이 op-brain-ingest §STEP3를 SSOT 참조 + lint 표에 `speculative` 행 존재 |
| TS-103 | R-1/R-2 접합 | 산출물 검사(grep) | 두 SKILL add-page 예시에 `--body-file` 반영 + 에러 대응 표에 `speculative_content` skip 행 |

### F-002: 미실체 탐지 도구 게이트

#### 3.2.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/brain-tool/brain_tool.py` | BE | ①`SPECULATIVE_MARKERS` 상수 ②`detect_speculative_markers()` 함수 ③`ERROR_CODES["speculative_content"]` ④`cmd_add_page` 본문 게이트+`--body-file`/`--force`/`--note` ⑤`cmd_lint` `speculative` kind ⑥argparse 확장 ⑦@header 갱신 | `brain_tool.py:478-540,818-936,144-159,1202-1249` |

#### 3.2.2 API·데이터 모델·설계

- **신규 상수** `SPECULATIVE_MARKERS: list[str]` (모듈 상수, `STATUS_ENUM` 인접 배치 `:54` 부근):
  - `_norm`(소문자+공백제거) 정규화된 고신호 토큰 목록. 초안: `["미착수","미확정","향후계획","개선필요","개선사항","todo","미해결","착수전","설계기록단계","작성예정","초안단계","추후작성"]`.
  - **[MUST] 보수적 사전 — 오검출 최소화(TASK §제약 "마커 오검출 최소화")**: 정상 정착 지식 헤딩에 부분문자열로 끼기 어려운 복합 토큰만 채택. 단독 `향후`/`예정`/`이슈`는 FP 위험으로 제외(복합형만 사용). 사전은 확장 가능하며 SSOT는 이 상수.
- **신규 함수** `detect_speculative_markers(title: str, body: str) -> list[str]` (@header exports 추가):
  - **M-1 결정 = 구조적 신호 우선(섹션 헤딩 + 제목 스캔)**. 스캔 대상 = `title` 1줄 + 본문에서 `#`로 시작하는 헤딩 라인만(`ln.lstrip().startswith("#")`). 각 대상을 `_norm`으로 정규화(`:603-609` 재사용) 후 `SPECULATIVE_MARKERS` 부분문자열 매칭.
  - 반환: 매칭된 마커 목록(중복 제거). 빈 목록 = 정상.
  - **판정 임계(M-2)**: 매칭 마커 ≥ 1 → 미실체. 산문(비헤딩 본문)은 스캔하지 않아 정당 지식의 "향후" 단순 언급은 트리거하지 않음(H-1 방어).
  - 근거: pointail 사례 헤딩 "구현 영향 범위 (HOW) — 아직 미착수, 설계 기록 단계"·"미확정 이슈"가 `## ` 섹션 헤딩 형태 → `_norm` 후 "미착수"·"설계기록단계"·"미확정" 매칭됨(TASK §실증 케이스).
- **신규 에러코드(M-2)** `ERROR_CODES["speculative_content"]` (`:144-159` 카탈로그에 추가): 메시지 `"미실체 지식으로 판정되어 등록을 거부: {detail}. 확정·실재 지식만 brain에 등록합니다. 우회는 --force --note '<사유>'."`
- **`cmd_add_page` 게이트 (R-3)** — 시그니처 불변, 내부 흐름에 삽입:
  1. `--body-file` 처리: `getattr(args,"body_file",None)`가 있으면 그 파일을 읽어 `parse_frontmatter`로 본문부 추출(frontmatter 있으면 body부만 사용, 없으면 전체) → 이 본문이 페이지 본문이 되고(템플릿 본문 대체) 스캔 대상이 됨. 미지정 시 **기존 템플릿 본문 경로 그대로**(하위호환 H-6, `:503-504` 불변).
  2. `validate_frontmatter` 통과(`:521-524`) 직후 `markers = detect_speculative_markers(args.title, body)` 호출.
  3. `markers`가 있고 `not args.force` → `err("add-page","speculative_content", detail=..., markers=markers)` (ok:false, exit 1).
  4. `markers`가 있고 `args.force`이나 `not args.note` → `err(..., "speculative_content", message="미실체 마커 감지 — --force 우회 시 --note '<사유>' 필수", markers=markers)` (백도어 차단 H-3).
  5. `markers`가 있고 `args.force and args.note` → 통과하되 **경고 기재(M-2 위치·형식)**: (a) frontmatter에 `speculative_override: true`, `override_note: <args.note>` 주입(디스크 영속) (b) 최종 `ok(...)`에 `warning="speculative_content_overridden"`, `speculative_markers=markers`, `override_note=args.note` 추가.
  - `speculative_override`/`override_note`는 `validate_frontmatter` 미검사 키 → 통과(H-7). yaml.safe_dump bool/str 정상 직렬화.
- **`cmd_lint` `speculative` kind (R-4)** — 페이지 루프(`:836-872`) 내 unsourced 검사(`:869-872`) 다음에 삽입:
  - `title = fm.get("title","")`; `markers = detect_speculative_markers(title, body)`; `markers`면 `issues.append({"kind":"speculative","page":rel,"detail":"미실체 마커 검출(섹션 헤딩): " + ", ".join(markers), "markers": markers})`.
  - `fm.get("speculative_override")`가 참이면 detail에 " (override 기재됨: <note>)" 부기하되 **여전히 리포트**(검출까지만, 자동 삭제·수정 없음 — 하위호환 제약).
  - term_duplicate/alias_collision(`:874-935`)와 독립. 모든 타입 페이지 대상(concept/entity/flow/synthesis/term 무관).
- **argparse 확장** (`:1202-1210` add-page): `p_add.add_argument("--force", action="store_true")`, `p_add.add_argument("--note")`, `p_add.add_argument("--body-file", dest="body_file")`. lint 파서(`:1247-1249`)는 변경 없음(새 kind는 인자 불필요).
- **@header 갱신**: `exports`에 `detect_speculative_markers` 추가, description에 `[071]` 태그로 "add-page 미실체 거부 게이트(--body-file/--force/--note, speculative_content) + lint speculative kind + SPECULATIVE_MARKERS 구조적 헤딩 탐지" 기재 (**[MUST] `docs/CONVENTIONS.md` §@header 규칙: "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다"**).

> **[MUST] `~/.opal/PRINCIPLES.md` Core Stance(enforce, don't advise)** — 규칙(LLM)만으로는 새므로(pointail 전례) 도구 게이트로 backstop한다. add-page(쓰기시)·lint(소급) 2중 결정론 집행 (→ D-6).
> **draft-term 경로 불변(M-3)**: `_score_page`(`:612-629`)·query 진입점③·`--include-draft`는 **변경하지 않는다**. 미실체는 draft가 아니라 거부·검출 대상이라는 R-6(2026-06-17) 결정과 정합(TASK 대상 파일 주석).

#### 3.2.3 환경 변경
해당 없음 (stdlib + 기존 PyYAML만 사용).

#### 3.2.4 배치/마이그레이션
해당 없음. 기존 등록된 active concept를 자동 거부·삭제하지 않음 — lint 검출까지만(하위호환 제약).

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-201 | R-3 AC | 기능(RED) | 미실체 본문(`--body-file`) add-page → ok:false + error=`speculative_content` |
| TS-202 | R-3 AC | 기능(RED) | `--force`만(note 없음) → 여전히 거부(note 필수) |
| TS-203 | R-3 AC | 기능(RED) | `--force --note "<사유>"` → ok:true + warning + frontmatter `speculative_override:true`/`override_note` |
| TS-204 | R-3 회귀 | 회귀(RED) | 정상 concept 본문(`--body-file`, 마커 없음) → ok:true(거부 없음) |
| TS-205 | 하위호환 | 회귀(RED) | `--body-file` 미지정 기존 호출 → 템플릿 본문 정상 생성(ok:true) |
| TS-206 | R-4 AC | 기능(RED) | pointail 등가 fixture(concept/active + 미실체 헤딩) 직접 write → lint issues에 kind=`speculative` |
| TS-207 | R-4 회귀 | 회귀(RED) | 정상 active concept → lint에 `speculative` 미출현 |
| TS-208 | R-4 비파괴 | 기능(RED) | `speculative_override` 페이지 → lint 여전히 리포트 + 페이지 미변경(삭제·수정 없음) |
| TS-209 | M-3 불변 | 회귀(RED) | draft term search 기본 제외 유지 + `_score_page` term 한정 필터 불변 |

### F-003: RED-first 회귀·계약 테스트

#### 3.3.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/brain-tool/tests/test_brain_tool.py` | BE | `make_args`에 `note`/`body_file` 기본값 추가 + 미실체 게이트 테스트 클래스(`TestSpeculativeGate071`) 신설(TS-201~209) + `_add_page` 헬퍼에 body_file/force/note 전달 확장 + 미실체 fixture 헬퍼 | `test_brain_tool.py:56-87,131-141` |

#### 3.3.2 설계
- **fixture 헬퍼** `_write_concept_page(name, title, status, body, sources)` — `_write_term_page`(`:143-165`) 패턴 준용, add-page 우회 직접 write로 status/본문 제어. pointail 등가 본문 = `## 개요\n...\n## 구현 영향 범위 (HOW) — 아직 미착수, 설계 기록 단계\n...\n## 미확정 이슈\n...`.
- **정상 fixture** = 헤딩 `## 개요`/`## 결정 내용 (HOW)`/`## 영향·관계`만, sources 있음 → 마커 0.
- **body-file fixture** = tmpdir에 스크래치 `.md` 작성 후 `--body-file`로 전달(add-page 경로 검증).
- **[MUST] `test_brain_tool.py:19` mock 금지**: 실제 `brain_tool.py`를 import 호출. KST만 `_mock_kst()` 격리. tmpdir 격리로 실 `.opal/brain` 불오염(`:93`).
- **RED-first(→ D-8 §2)**: 이 테스트는 opal-test-agent(mode: red)가 작성하며 구현자(op-dev-execute)와 분리. RED 실행 시 함수·인자 부재로 실패(exit≠0) 증거 확보 후 GREEN 진입. GREEN/fix 중 RED 테스트 수정 금지(§3).

#### 3.3.3 환경 변경
해당 없음 (pytest 기존 인프라).

#### 3.3.4 배치/마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-301 | R-5 AC | 회귀 | 기존 test_brain_tool.py 전량 통과(회귀 0) — 신규 클래스 포함 All Pass |
| TS-302 | R-5 AC | 산출물 검사 | 신규 테스트가 TS-201~209 계약을 커버(케이스 매핑 존재) |

### F-004: install 재배포 검증

#### 3.4.1 파일 변경 계획
**신규/수정 없음** — `./scripts/install-mac.sh` **실행만** 수행(파일 변경 아님).

#### 3.4.2 설계
- 소스(`opal/`) 확정 후 `./scripts/install-mac.sh` 실행 → `~/.opal/tools/brain-tool/brain_tool.py`·`~/.opal/skills/{op-brain-ingest,opal-brain}/SKILL.md` 재배포. 배포본이 `--body-file`/`speculative` 반영·소스 일치 확인(R-6 AC).
- **[MUST] `docs/CONVENTIONS.md` §배포 경계** 준수 — `~/.opal/` 직접 편집 금지, install 경유. 사람 게이트(SUPERVISOR).

#### 3.4.3 환경 변경 / 3.4.4 배치
install 스크립트 실행(사람 게이트). 마이그레이션 없음.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-401 | R-6 AC | 통합/배포 | 배포 후 `~/.opal/tools/brain-tool/brain_tool.py` grep `speculative`/`body-file` 매칭 + 소스와 일치 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)
| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-003(RED) | 1 | opal-test-agent | 순차 | RED 테스트 선작성·실패 증거 (red-first §1) |
| 2 | F-002 | 2 | opal-be-agent | 순차 | GREEN 구현 → RED→pass |
| 3 | F-001 | 3, 4 | opal-task-agent | 병렬 가능 | 스킬 SSOT + README (독립 파일) |
| 4 | F-003 | 5 | opal-test-agent | 순차 | 전체 pytest 회귀 확인 |
| 5 | F-004 | 6 | PM 직접 | 순차 | install 재배포 (SUPERVISOR 게이트) |

### 4.2 실행 체크리스트
> 총 6개 Step | Phase 5개 | 실행 모드: **복잡**

#### Step 1: RED 테스트 선작성 (미실체 게이트 계약)
- [ ] 완료
- **소속 기능**: F-003
- **영역**: BE
- **agent**: opal-test-agent
- **파일**: `opal/tools/brain-tool/tests/test_brain_tool.py`
- **작업 내용**: `make_args`에 `note=None`/`body_file=None` 추가. `TestSpeculativeGate071` 클래스 신설 — TS-201~209 커버: add-page 미실체 거부(`--body-file`), `--force`만 거부, `--force --note` 통과+override 기재, 정상 concept 통과, `--body-file` 미지정 하위호환, lint speculative 정탐(pointail 등가 fixture)·오탐 없음(정상 active)·override 비파괴, draft-term 불변. fixture는 `_write_concept_page` 직접 write + 스크래치 body-file(mock 금지).
- **완료 기준**: `pytest opal/tools/brain-tool/tests/test_brain_tool.py -k SpeculativeGate071` 실행 시 신규 케이스가 **실패(RED)** — 함수/인자 부재로 exit≠0. 실패 로그를 증거로 기록.
- **테스트**: TS-201~209, TS-302 (RED 상태)
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: brain_tool.py 게이트 GREEN 구현
- [ ] 완료
- **소속 기능**: F-002
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/brain-tool/brain_tool.py`
- **작업 내용**: ①`SPECULATIVE_MARKERS` 상수(`:54` 부근) ②`detect_speculative_markers(title,body)` 함수(구조적 헤딩+제목 스캔, `_norm` 재사용) ③`ERROR_CODES["speculative_content"]`(`:144-159`) ④`cmd_add_page`(`:478-540`)에 `--body-file` 본문 주입 + 게이트(거부/`--force`+`--note` 우회/override 기재) ⑤`cmd_lint`(`:836-872` 이후)에 `speculative` kind ⑥argparse add-page에 `--force`/`--note`/`--body-file`(`:1202-1210`) ⑦@header exports+description `[071]`. **[MUST] `_score_page` draft 필터(`:619-629`)·query 관련 코드 불변(M-3).**
- **완료 기준**: Step 1의 RED 케이스 전부 **GREEN(통과)**. RED 테스트 파일 미수정(red-first §3). `python3 -m pyflakes`(가능 시) 오류 0.
- **테스트**: TS-201~209 GREEN
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: SSOT 스킬 문서 명문화 (R-1/R-2)
- [x] 완료
- **소속 기능**: F-001
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-brain-ingest/SKILL.md`, `opal/skills/opal-brain/SKILL.md`
- **작업 내용**: op-brain-ingest §STEP3 제외 기준 표에 미실체 행+예시+판별 신호 1줄, 에러 대응 표에 `speculative_content` skip 행, STEP5-1 add-page 예시에 `--body-file` 반영, 변경이력 `(071)`. opal-brain ingest 절에 "미실체 제외 — op-brain-ingest §STEP3 SSOT 참조"(별도 정의 금지), lint issue kind 표에 `speculative` 행, ingest add-page 예시에 `--body-file`, 변경이력 `(071)`. **query 진입점③·synthesis·search draft 불변(M-3).**
- **완료 기준**: TS-101/102/103 grep 통과. 두 파일 변경이력에 `(071)` 행. opal-brain에 미실체 기준 재정의 없음(SSOT 참조만).
- **테스트**: TS-101, TS-102, TS-103
- **실행 방법**: sub-agent
- **의존**: Step 2 (신규 인자/에러코드 확정 후 예시 정합)

#### Step 4: brain-tool README 정합
- [x] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/tools/brain-tool/README.md`
- **작업 내용**: add-page `--force`/`--note`/`--body-file`, `speculative_content` 에러, lint `speculative` kind를 README 서브명령 문서에 반영.
- **완료 기준**: README grep `--body-file`·`speculative` 매칭. 서브명령 개수·에러 카탈로그 서술 정합.
- **테스트**: TS-103(문서 정합 일부)
- **실행 방법**: sub-agent
- **의존**: Step 2 (∥ Step 3와 병렬 가능)

#### Step 5: 전체 pytest 회귀 확인
- [ ] 완료
- **소속 기능**: F-003
- **영역**: BE
- **agent**: opal-test-agent
- **파일**: `opal/tools/brain-tool/tests/test_brain_tool.py` (실행)
- **작업 내용**: `pytest opal/tools/brain-tool/tests/test_brain_tool.py -v` 전량 실행. 신규 + 기존 케이스 All Pass, 회귀 0 확인.
- **완료 기준**: exit 0, 실패 0. 기존 케이스(add-page/lint/search/validate/term 등) 무회귀.
- **테스트**: TS-301, TS-302
- **실행 방법**: sub-agent
- **의존**: Step 2, Step 3, Step 4

#### Step 6: install 재배포 + 배포본 검증
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 배치
- **agent**: PM 직접
- **파일**: `scripts/install-mac.sh` (실행만)
- **작업 내용**: 캡틴 배포 승인 후 `./scripts/install-mac.sh` 실행. 배포본 `~/.opal/tools/brain-tool/brain_tool.py`·SKILL 2종이 소스와 일치 확인.
- **완료 기준**: 배포본 grep `speculative`/`body-file` 매칭 + 소스 diff 0(변경이력 strip 제외). **[MUST] `docs/CONVENTIONS.md` §배포 경계** 준수(직접 편집 금지).
- **테스트**: TS-401
- **실행 방법**: direct (SUPERVISOR 게이트)
- **의존**: Step 5

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | RED-first — 테스트 실패 증거 후 구현(red-first §1) |
| Step 2 → Step 3 | 스킬 예시가 신규 인자/에러코드에 정합해야 함 |
| Step 3 ∥ Step 4 | 독립 파일(SKILL vs README), 충돌 없음 |
| Step 2,3,4 → Step 5 | 전체 회귀는 코드+문서 확정 후 |
| Step 5 → Step 6 | 배포는 검증 통과 후(사람 게이트) |
| Step 1·2·5 = opal-test-agent/opal-be-agent 분리 | red-first §2 작성자≠구현자 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | op-brain-ingest §STEP3 미실체 행 + 예시 | TS-101 | grep 매칭 + 예시 4종 존재 |
| F-001 | opal-brain SSOT 참조(재정의 없음) + lint 표 speculative 행 | TS-102 | grep 매칭 + 별도 정의 부재 |
| F-001 | add-page 예시 `--body-file` + 에러표 skip 행 | TS-103 | 두 SKILL·README grep 매칭 |
| F-002 | add-page 미실체 거부 | TS-201 | ok:false + `speculative_content` |
| F-002 | `--force` note 필수 | TS-202 | note 없으면 거부 |
| F-002 | `--force --note` 우회 + 경고 기재 | TS-203 | ok:true + override frontmatter + warning |
| F-002 | 정상 concept 통과(회귀) | TS-204 | ok:true |
| F-002 | 하위호환(`--body-file` 미지정) | TS-205 | 템플릿 본문 ok:true |
| F-002 | lint 미실체 소급 검출 | TS-206 | issues에 kind=`speculative` |
| F-002 | lint 정상 active 오탐 없음 | TS-207 | `speculative` 미출현 |
| F-002 | lint 비파괴(override 리포트+미변경) | TS-208 | 리포트 유지 + 페이지 불변 |
| F-002 | draft-term 불변(M-3) | TS-209 | 기본 draft 제외 유지 |
| F-003 | 전체 회귀 0 | TS-301 | pytest exit 0 |
| F-004 | 배포본 소스 일치 | TS-401 | 배포본 grep + diff 0 |

### 5.2 회귀 테스트
- [ ] 기존 `test_brain_tool.py` 전량 통과(add-page/index/log/search/sync-header/lint/validate/analyze/ingest-scan/term).
- [ ] `_score_page` term 한정 draft 필터·query 진입점③ 동작 불변(M-3).
- [ ] 기존 add-page 정상 호출(`--body-file` 없음)·기존 brain 페이지 무손상.
- [ ] 기존 active concept 자동 거부·삭제 없음(lint 검출까지만).

### 5.3 코드/문서 품질
- [ ] `brain_tool.py` @header exports/description `[071]` 갱신.
- [ ] 두 SKILL·README 변경이력·문서 정합(KST 일시 + `(071)`).
- [ ] `ERROR_CODES` 카탈로그 키만 error 응답에 사용(`:143` 규칙 준수).

### 5.4 보안
- [ ] 하드코딩 토큰/시크릿 없음(`SPECULATIVE_MARKERS`는 업무 마커 문자열, 시크릿 아님).
- [ ] `--body-file` 경로 처리 시 임의 경로 읽기 부작용 검토(도구 로컬 실행·읽기 전용, 쓰기는 대상 페이지만).
- [ ] `~/.opal/` 직접 수정 없음(소스만 수정 후 install).

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 6개 | 복잡 |
| 변경 파일 수 | 5개 (brain_tool.py·tests·2 SKILL·README) | 복잡 |
| 모듈 범위 | 도구+테스트+스킬+문서 다중 | 복잡 |
| 작업 유형 | 도구 동작 변경(거부·신규 검출) + 기준 명문화 | 복잡 |
| 외부 의존성 | 없음(stdlib+PyYAML 기존) | 단순 |
| **실행 모드** | **복잡** | 하나라도 복잡 → 복잡 모드 |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
```
Batch1: [opal-test-agent] Step1 (RED 작성)
   │  (RED 실패 증거)
Batch2: [opal-be-agent] Step2 (GREEN 구현, brain_tool.py 단독)
   │
Batch3: [opal-task-agent] Step3(SKILL 2종) ∥ Step4(README)   ← 독립 파일, 병렬
   │
Batch4: [opal-test-agent] Step5 (전체 pytest 회귀)
   │
Batch5: [PM 직접] Step6 (install 재배포, SUPERVISOR)
```
- 파일 충돌 방지: `brain_tool.py`는 opal-be-agent 단독(Step2). `test_brain_tool.py`는 opal-test-agent 단독(Step1·5). SKILL/README는 opal-task-agent.
- 작성자≠구현자: RED(opal-test-agent) vs 구현(opal-be-agent) 분리(red-first §2).

### C-2. 스킬 요구사항
- 신규 스킬 갭 없음. 기존 op-dev-execute(GREEN)·opal-test-agent(RED) 워크플로우로 커버.

### C-3. 도구 요구사항
- Python3 + PyYAML(기존), pytest(기존), `./scripts/install-mac.sh`(기존). 신규 CLI/MCP/패키지 없음.

### C-4. 테스트 전략 (RED-first ON)
- **RED-first 트랙 적용**(red-first §1.5): 이번 변경은 **도구 동작 변경(add-page 거부·lint 신규 검출) = self-confirming 위험 높음 + API/계약 성격** → RED-first 강제 카테고리. → D-8 §1.5.
- **RED**: opal-test-agent(mode: red)가 Step1에서 실패 테스트 작성·실행(exit≠0 증거).
- **GREEN**: op-dev-execute(opal-be-agent)가 Step2 구현 → 통과. RED 파일 수정 금지(§3).
- **state-tool 연동**: EXECUTE `verify --red-check` **ON**(RED 증거 게이트).
- **회귀**: Step5 전체 pytest. **공개 인터페이스 검증**(CLI JSON 반환값 `ok`/`error`/`issues`/`markers` — private 결합 금지, §4).
- **graceful skip 무해당**: 테스트 인프라(pytest) 존재.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 | Python3 CLI (argparse, PyYAML, subprocess) | (trailofbits/modern-python 참고 — 신규 패턴 불요) |
| 테스트 | pytest / unittest (tmpdir 격리, mock 금지) | red-first 트랙 |
| 문서 | Markdown SKILL/README | citation-rules |
| 배포 | bash install-mac.sh | 배포 경계 |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 라이브러리 신규 API 불요 — stdlib+기존 PyYAML만 사용, context7/shadcn 무해당 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py` | add-page/lint/탐지 코어/ERROR_CODES 대상 (R-3·R-4) |
| D-2 | 소스 | test_brain_tool.py | `opal/tools/brain-tool/tests/test_brain_tool.py` | 테스트 패턴·fixture·mock 금지 계약 (R-5) |
| D-3 | 소스 | op-brain-ingest SKILL | `opal/skills/op-brain-ingest/SKILL.md` | §STEP3 제외 기준 SSOT·에러 대응 표 (R-1) |
| D-4 | 소스 | opal-brain SKILL | `opal/skills/opal-brain/SKILL.md` | ingest/query 진입점③·synthesis·lint kind 표 (R-2·M-3) |
| D-5 | 소스 | brain-tool README | `opal/tools/brain-tool/README.md` | 서브명령·에러 문서 정합 |
| D-6 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` | enforce-don't-advise / Core Stance |
| D-7 | 설계 | CONVENTIONS | `docs/CONVENTIONS.md` | 배포 경계·@header·변경이력·언어 규칙 [MUST] |
| D-8 | 설계 | red-first | `opal/core/references/harness/red-first.md` | RED-first 트랙 적용 판단 |
| D-9 | 설계 | citation-rules | `opal/core/references/harness/citation-rules.md` | 인용 규칙·§8 브레인 본문 비즈니스 용어 |
| D-10 | 소스 | page-concept 템플릿 | `opal/tools/brain-tool/templates/page-concept.md` | 템플릿 본문에 마커 부재 → add-page 현행 미탐지 근거 |
| D-11 | 기획 | TASK.md | `tasks/071-260722-opds-브레인-미실체지식-차단/TASK.md` | 확정 설계 방향·미확정 4건(M-1~M-4)·실증 케이스 |

> 인용 형식: citation-rules §3.1. 유형: 기획/설계/소스/외부.

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 9-1 | 마커 오검출(FP) — 정착 지식 거부 | F-002 | P1 | 구조적 헤딩+제목만 스캔(산문 제외), 보수적 복합 토큰 사전, 정상 회귀 테스트(TS-204/207) |
| 9-2 | 게이트 미발동 — 스킬이 `--body-file` 미사용 | F-001/002 | P1 | 스킬 예시에 `--body-file` 반영(R-1/R-2) + lint 소급 backstop(작성 경로 무관) |
| 9-3 | CLOSE 차단 — add-page 거부가 hard-fail | F-002 | P0 | op-brain-ingest skip-and-continue 정합 + 에러 대응 표 전용 행(TS-103/S-10) |
| 9-4 | 하위호환 파손 — 기존 add-page 회귀 | F-002 | P1 | `--body-file` 미지정 시 템플릿 경로 완전 불변(TS-205), 전체 회귀(TS-301) |
| 9-5 | draft-term 회귀(M-3) | F-002 | P1 | `_score_page`·query 진입점③ 코드 무접촉 + 회귀 테스트(TS-209) |
| 9-6 | 배포 drift / 경계 위반 | F-004 | P1 | 소스만 수정 후 install, 배포본 diff 검증(TS-401), SUPERVISOR 게이트 |
| 9-7 | 추적성 누락 | F-001/002 | P2 | @header `[071]`·변경이력 `(071)` 체크(QA §5.3) |
