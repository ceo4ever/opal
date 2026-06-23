# PLAN: 브레인 entity 지식 품질 개선 — ingest @header 전사 탈피 (신규 작성 규율)

> 작성일: 2026-06-23 | 입력: TASK.md, ANALYSIS.md
> 모드: Flat (단일 기능 — entity 작성 규율 표준화)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

brain의 **entity 페이지**가 `//opbr init` 시드 과정에서 code-scan @header를 **기계 전사(transcription)**하여 WHAT 덤프로 전락하는 문제를, 코드 변경 없이 **스킬·템플릿·참조 문서의 작성 규율 표준화**로 해결한다. entity 본문을 **5섹션 표준**(개요/책임 WHAT/설계배경 WHY/관계 HOW/소스 커버리지)으로 통일하고, @header 전사 금지·입력 큐레이션 선행·provenance 3종 태깅을 SKILL [MUST]로 명문화한다. 기존 저품질 brain은 **전체 삭제 후 개선된 스킬로 재생성**하는 런북으로 처리한다(소급 보정·부분 재시드·enrich·도구 게이트 = 전부 미구현).

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | entity 작성 규율 5섹션 표준화 + provenance 집행 + 재생성 런북 + §8 정합 | R-1, R-2, R-3(SKILL 절차 채택), R-4, R-5 | P0 | 없음 |

> **단일 기능 사유**: 5개 수정 지점(M-1~M-5)과 drift 정합은 모두 "entity 작성 규율"이라는 단일 논리 묶음에 속하며, 함께 일관되게 변경·검증되어야 의미가 성립한다(템플릿·시드 SKILL·ingest SKILL·참조 문서가 동일 5섹션·동일 규칙을 가리켜야 정합). 따라서 Flat 모드를 적용한다. ANALYSIS.md에 `features[]` 명시 없음 → Multi 강제 조건 미해당.

### 1.3 기능 의존 그래프

생략 (단일 기능, Flat 모드).

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨. ANALYSIS §F(H-1~H-7) + §5(R-T1~R-T5)를 흡수·정리한다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | M-1·M-3 SKILL 텍스트 강화 (entity 작성 행동) | "SKILL [MUST] 강화 → AI가 실제로 WHY를 합성한다"는 행동 계약 (강화만으로 변하지 않을 위험) | P0 | L2(시연 — 개선 SKILL로 entity 1건 재생성) | S-시연: WHY 섹션에 provenance 3종 중 하나가 실제로 명시되는지 (ANALYSIS H-1, R-T1) |
| H-2 | M-2 재생성 런북 정확성 | "`init --force`로 재생성된다"는 운영 절차 계약 — 실제로는 pages/ 미삭제(ANALYSIS C-1) | P1 | L1(문서 검사) + L2(실 brain-tool로 `init --force` 후 pages/ 잔존 확인) | S-런북: 런북 ②가 "`pages/entity/` 직접 삭제 또는 `.opal/brain/` 전체 삭제"로 기재 + `--force` 한계 명시 (ANALYSIS H-2) |
| H-3 | M-1·M-3·M-4 5섹션 헤딩 (`## 책임 (WHAT)` 등 괄호 레이블) | citation-rules §8.9 [MUST] "5W1H 섹션 헤딩 강제 금지" 계약 위반 위험 | P1 | L1(문서 검사 — §8.9 원문 대조) | S-§8.9: 5섹션 헤딩이 `## 누가/왜/어떻게` 형식이 아님을 PLAN·SKILL 근거로 확인 (ANALYSIS H-3, E) |
| H-4 | M-4 `## 코드 참조` → `## 소스 커버리지` 개명 | brain-tool add-page가 템플릿 내부 섹션명을 검증하는가 (검증 시 pytest 깨짐) | P1 | L1(단위 — brain-tool pytest 회귀 0) | S-회귀: `pytest opal/tools/brain-tool/tests/` 전체 통과, 회귀 0 (ANALYSIS H-4, R-T3, §1.4) |
| H-5 | provenance 3종 집행 수단 | "[MUST] SKILL 텍스트만으로 집행 가능"한가 (도구 게이트 미채택 결정) | P1 | L2(시연으로 효과 관찰) | H-1과 동일 시연으로 커버. 도구 게이트 미채택은 캡틴 확정 #3 (ANALYSIS H-5, R-T2) |
| H-6 | M-1 입력 큐레이션 선행 절차 | 큐레이션 선행이 init 시드 소요를 허용 불가 수준으로 늘리는가 | P2 | L3(정성 — seed_candidates ~7개 기준 추정) | S-비용: 큐레이션 절차가 seed 후보 수 대비 합리적인지 검토 (ANALYSIS H-6) |
| H-7 | drift 정합 (opal-brain SKILL L213-221 "코드 @header → entity" 행) | ingest --all 표가 코드 현실(ingest-scan은 docs/skills/tasks→concept만)과 모순 — 문서 신뢰 계약 | P2 | L1(문서 검사 — brain_tool.py ingest-scan 분기 대조) | S-drift: 해당 행이 코드 현실에 맞게 정정됨 (ANALYSIS H-7, §2-보완 사실2, 캡틴 확정 #4) |
| H-8 | M-2 재생성 시 synthesis 유실 | synthesis는 query 파생물 — ingest-scan 미대상이라 init로 복구 불가 | P0 | L1(문서 검사 — 런북에 백업 절차 ① 명시) | S-런북에 synthesis 백업·복원 절차와 유실 리스크가 명시됨 (ANALYSIS C-2, R-T4) |

**가설 도출 관점 요약**: H-1/H-5는 "Enforce, don't just advise" 검증 가능성 가설(텍스트 강화의 실효), H-2/H-8은 운영 절차 정확성 가설(런북), H-3/H-7은 문서 정합 가설(§8.9 / drift), H-4는 도구 회귀 가설(개명 안전성), H-6은 비용 가설.

---

## 2. 기능별 분석

> Flat 모드 — F 하위 섹션 없이 평면 작성.

### 2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-brain/SKILL.md` | init 시드 entity 작성 절차·본문 구조 명세 (L106-128) + ingest --all drift 표(L213-221) + 재생성 런북 위치 | 수정 |
| 스킬 | `opal/skills/op-brain-ingest/SKILL.md` | CLOSE ingest entity 작성 규율·페이지 예시 (L168-197) | 수정 |
| 가이드 | `opal/tools/brain-tool/templates/page-entity.md` | add-page 호출 시 실제 적용되는 entity 페이지 템플릿 (L1-37) | 수정 |
| 참조 | `opal/core/references/harness/citation-rules.md` | §8.5 검증 연결 표 (L361-366) | 수정 |
| 도구 | `opal/tools/brain-tool/brain_tool.py` | cmd_init/cmd_analyze/cmd_ingest_scan/--force 집행 | 변경 없음 (분석·회귀 검증 한정) |
| 환경 | `scripts/install-mac.sh` (또는 `opal install`) | `opal/` 소스 → `~/.opal/` 재배포 | 실행만 (코드 미변경, L3 캡틴 직접) |

### 2.2 현재 구현 (ANALYSIS 참조 — 간략)

ANALYSIS §A·§C·§D에서 확인된 현 상태(실제 코드·문서 Read 기반):

- **entity 생성 주 경로 = `//opbr init` 시드**. brain-tool ingest-scan은 docs(doc)/skills(skill)/tasks(task)만 스캔하며 코드 파일→entity 분기가 없다 (`brain_tool.py:1068-1146`, ANALYSIS §2-보완 사실1·2). 따라서 entity는 init analyze→seed_candidates 경로에서 LLM이 본문을 작성한다 (`opal/skills/opal-brain/SKILL.md:106-128`).
- **불일치(drift)**: SKILL.md 두 곳의 entity 본문 예시가 **4섹션**(`opal-brain/SKILL.md:128` = 개요/설계배경 WHY/인터페이스/관련 페이지; `op-brain-ingest/SKILL.md:182-196` = 개요/설계배경 WHY/인터페이스/관련 페이지)인 반면, 실제 적용 템플릿 `page-entity.md:18-36`은 이미 **5섹션**(개요/책임 WHAT/설계배경 WHY/관계 HOW/코드 참조)이다 (ANALYSIS §A-1·§4-1).
- **`init --force` 한계**: `cmd_init`는 SCHEMA.md·index.md·log.md만 템플릿으로 덮어쓰고 `pages/`는 `exist_ok=True`로 보존 → `--force`만으로는 재생성 불가 (`brain_tool.py:386-459`, ANALYSIS §C-1).
- **§8.5 현재 문구**(`citation-rules.md:365`): "brain ingest 워커: … STEP 4 작성 규칙이 이 §8을 따른다" — generic. opal-brain init entity 경로는 미연결 (ANALYSIS §D).
- **ingest --all 표 drift**(`opal-brain/SKILL.md:220`): `| 코드 @header | entity | @header 필드 흡수 + source_ref 포인터 |` 행이 존재하나 ingest-scan에 코드 스캔 분기가 없어 실현되지 않는 죽은 행 (ANALYSIS §2-보완 사실2, §4-4).

### 2.3 영향 범위

- **직접**: 위 4개 파일(스킬 2·템플릿 1·참조 1). 모두 Markdown — 도구(`brain_tool.py`) 코드 무변경.
- **간접**: 기존 entity 페이지(`.opal/brain/pages/entity/*.md`)는 소급 변경 없음 — 프로젝트별 재시드(런북) 실행 시 새 규율 적용 (ANALYSIS §3.2). brain-tool pytest는 템플릿 내용 변경에 무관(add-page는 파일명으로 로드, 내부 섹션명 미검증) → 회귀 0 예상 (ANALYSIS §1.4).
- **배포**: `opal/` 소스 수정 → `install` 재배포로 `~/.opal/` 반영 (L3 캡틴 직접). `~/.opal/` 직접 편집 금지.

---

## 3. 기능별 설계

> Flat 모드 — F 하위 섹션 없이 평면 작성.
> 인용: `(→ D-N §N)` = §8.3 참조 테이블 단축. 코드/문서 위치는 `` `경로:줄번호` ``.

### 3.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| — | 없음 | — | 신규 파일 없음 (Surgical Changes — 기존 파일 수정만) | (→ D-1 §Simplicity) |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| M-1 | `opal/skills/opal-brain/SKILL.md` | 스킬 | 핵심 엔티티 시드 절(L106-128): entity 본문 4섹션 → **5섹션 표준** + 입력 큐레이션 선행 절차 [MUST] + @header 전사 금지 [MUST] + provenance 3종 규칙 [MUST] | `opal/skills/opal-brain/SKILL.md:128` (→ D-3 §A-3) |
| M-1b | `opal/skills/opal-brain/SKILL.md` | 스킬 | ingest --all 배치 정책 표(L213-221) "코드 @header → entity" 행 drift 정정 — 코드 현실(ingest-scan: docs/skills/tasks→concept) 반영 | `opal/skills/opal-brain/SKILL.md:220` (→ D-3 §2-보완 사실2) |
| M-2 | `opal/skills/opal-brain/SKILL.md` | 스킬 | `## STEP: init` 하단에 **재생성 런북 신규 절** — synthesis 백업 → `pages/entity/` 직접 삭제(또는 `.opal/brain/` 전체) → init 재실행 → synthesis 복원. `--force` 한계·synthesis 유실 리스크 명시 | `opal/skills/opal-brain/SKILL.md:160` (init 보고 직후) (→ D-5 §C-1) |
| M-3 | `opal/skills/op-brain-ingest/SKILL.md` | 스킬 | STEP 4 entity 예시(L168-197) 4섹션 → **5섹션 표준** + 동일 규칙(@header 전사 금지·provenance·소스 커버리지 line number) | `opal/skills/op-brain-ingest/SKILL.md:168-197` (→ D-4 §A-2) |
| M-4 | `opal/tools/brain-tool/templates/page-entity.md` | 가이드 | 마지막 섹션 `## 코드 참조` → `## 소스 커버리지` 개명 + 각 섹션 가이던스 강화(WHAT 인용·WHY provenance·HOW·부록 line number) + @header 전사 금지 주석 | `opal/tools/brain-tool/templates/page-entity.md:34` (→ D-6 §A-3) |
| M-5 | `opal/core/references/harness/citation-rules.md` | 참조 | §8.5 brain ingest 워커 항목 구체화(§8.2·§8.8 명문화) + opal-brain init entity 경로 연결 항목 추가 | `opal/core/references/harness/citation-rules.md:365` (→ D-2 §D) |

> 변경이력 의무: M-1·M-1b·M-2가 동일 파일(opal-brain SKILL) → 변경이력 1행. M-3(op-brain-ingest), M-5(citation-rules) 각 1행. M-4(page-entity.md)는 현재 변경이력 표가 없는 템플릿 → 표 신규 추가는 과잉(Simplicity); 추적은 SKILL 변경이력으로 충분하므로 템플릿에는 변경이력 추가하지 않는다 (→ D-7 §CONVENTIONS 변경이력 의무는 "스킬·에이전트·참조 문서" 대상 — 템플릿은 비대상).

### 3.2 작성 규율 설계 (스킬·템플릿 콘텐츠 명세)

> 본 절은 코드가 아닌 **문서 콘텐츠**를 설계한다. EXECUTE 워커는 아래 명세를 기존 파일에 반영한다.

#### 3.2.1 entity 5섹션 표준 (M-1·M-3·M-4 공통 골격)

5개 섹션 헤딩과 각 섹션의 작성 규율:

| # | 섹션 헤딩 (고정) | 역할 | 작성 규율 |
|---|----------------|------|----------|
| 1 | `## 개요` | 비즈니스 프레이밍 — 이 엔티티가 무엇이고 왜 존재하는지 1~3문장 | 비즈니스 용어 우선. 코드 식별자 본문 주어 금지 (→ D-2 §8.2) |
| 2 | `## 책임 (WHAT)` | 노출 인터페이스·책임을 기능 단위로 서술 | 각 책임에 `` `file_path:line` `` 인용 병기 (→ D-2 §8.4) |
| 3 | `## 설계 배경 (WHY)` | 왜 이렇게 설계했는가 — 결정·기각된 대안·맥락 | **provenance 3종 태깅 [MUST]**(3.2.2). HOW 누수 금지(관계 서술은 §관계로). 5W1H는 사고틀로만(§8.9) |
| 4 | `## 관계 (HOW)` | 의존·피의존·협력 엔티티 | wikilink `[[페이지명]]` (SCHEMA §4 링크 규칙) |
| 5 | `## 소스 커버리지` | 코드 식별자·enum·exports를 **부록으로 분리** | line number 포함 `` `file_path:line` `` 표. 본문(1~4)에서 강등 배치 (→ D-2 §8.8) |

> **[MUST] @header 전사 금지**: code-scan @header(module/layer/domain/exports)를 본문 1~4섹션에 기계 복사하지 않는다. @header 필드는 frontmatter와 §소스 커버리지(부록)에만 둔다. 본문은 사고하여 합성한다 (TASK §확정 설계방향 / `~/.opal/PRINCIPLES.md` "Don't fake it").

#### 3.2.2 provenance 3종 규칙 (M-1·M-3 [MUST])

`## 설계 배경 (WHY)`의 각 주장 문장은 아래 3종 중 하나의 태그를 갖는다 (TASK §51 "provenance 절대 가드", 캡틴 확정 #3):

| 태그 | 의미 | 사용 조건 |
|------|------|----------|
| `(근거: <doc>/POL-N/task:NNN PLAN§X)` | 문서·정책·태스크에서 확인된 WHY | 큐레이션된 입력에 WHY 출처가 있을 때 |
| `(추론: 코드패턴)` | 코드 구조에서 추론한 WHY (직접 근거 없음) | 코드만으로 합리적 추론 시 — 단정 금지 |
| `(WHY 미확보)` | WHY 입력이 없어 미확보 | 솔직 표기 — 날조 금지 (`~/.opal/PRINCIPLES.md` "Don't fake it") |

> **[MUST] 집행 수단 = SKILL 텍스트만 (도구 게이트 미채택)**. brain-tool은 의미 판정 불가 + Simplicity First → 도구 코드 변경 없음 (캡틴 확정 #3, ANALYSIS §B-3·H-5).

#### 3.2.3 입력 큐레이션 선행 절차 (M-1 [MUST])

entity 본문 작성 **전**에 WHY 소스를 큐레이션하는 선행 절차를 init 시드 Step 5에 [MUST]로 삽입 (캡틴 확정 #5, ANALYSIS §B-3 SKILL 절차 채택):

1. `docs/PROJECT.md` 문서 레지스트리에서 해당 모듈 관련 docs 확인.
2. 관련 태스크 `tasks/NNN/PLAN.md`(설계 결정) 확인 — git 커밋 메시지 태스크 번호로 역추적 가능 (ANALYSIS §B-2, 본 프로젝트 커밋 일관성 확인됨).
3. 관련 기존 brain 페이지(concept/entity) 후보 확인.
4. 위 입력에서 WHY를 합성. 입력에 WHY가 없으면 §설계 배경에 `(추론: 코드패턴)` 또는 `(WHY 미확보)`로 솔직 표기.

> why-sources 도구화는 미채택 — 결과가 "후보 목록"이고 선별은 LLM이 수행하므로 SKILL 절차로 동일 효과 (ANALYSIS §B-3, Simplicity First).

#### 3.2.4 재생성 런북 (M-2)

`## STEP: init` 하단 신규 절 `### 재생성 런북 (brain 전체 재시드)`:

```
① 백업: .opal/brain/pages/synthesis/ + 수기 편집 페이지를 별도 경로로 복사
   (⚠️ synthesis는 query 파생물 — ingest-scan 미대상이라 init로 복구 불가 → 유실 방지 필수)
② 삭제: .opal/brain/pages/entity/ 직접 삭제 (entity만 재생성) 또는 .opal/brain/ 전체 삭제
   ⚠️ //opbr init --force 만으로는 pages/ 가 보존되어 재생성되지 않는다 (brain_tool.py:436-440)
③ 재생성: //opbr init (개선된 5섹션 규율 적용)  [+ 필요 시 ingest --all로 concept 재생성]
④ 복원: 백업한 synthesis/ + 수기 페이지를 .opal/brain/pages/ 로 복원
```

> 운영자가 프로젝트별로 실행하는 절차 — 본 태스크 EXECUTE 범위는 런북 **문서화**까지이며 실데이터 재시드 실행은 포함하지 않는다 (TASK §범위 "타 프로젝트 실데이터 보정" 제외).

#### 3.2.5 §8.5 정합 (M-5)

`citation-rules.md:365` brain ingest 워커 항목을 구체화하고 init 경로 항목을 추가 (ANALYSIS §D):

- 변경 전: "brain ingest 워커: `op-brain-ingest/SKILL.md` STEP 4 작성 규칙이 이 §8을 따른다."
- 변경 후(권고):
  - "brain ingest 워커: `op-brain-ingest/SKILL.md` STEP 4 entity 작성 규칙이 §8.2(코드 식별자 본문 주어 금지)·§8.8(부록 분리)을 명문화한다."
  - "brain init 시드: `opal-brain/SKILL.md` 핵심 엔티티 시드 entity 작성 규칙이 §8.2·§8.8을 명문화한다 (소스 커버리지 부록 분리)."

#### 3.2.6 §8.9 충돌 회피 근거 (PLAN 명시 — 캡틴 확정 핵심 제약)

> **[MUST] `opal/core/references/harness/citation-rules.md` §8.9**: "5W1H를 페이지 섹션 구조 템플릿으로 강제하는 것을 금지한다. … `## 누가`, `## 왜`, `## 어떻게` 등을 배치하지 않는다." (`citation-rules.md:405`)

5섹션 표준은 §8.9를 **위반하지 않는다**. 근거(ANALYSIS §E):

| 5섹션 헤딩 | §8.9 위반 여부 | 근거 |
|-----------|--------------|------|
| `## 개요` | 위반 아님 | 5W1H 헤딩 아님 |
| `## 책임 (WHAT)` | 위반 아님 | 주 헤딩은 도메인 의미("책임"). `## 무엇을` 형식 아님 — WHAT은 괄호 보조 레이블 |
| `## 설계 배경 (WHY)` | 위반 아님 | 주 헤딩은 "설계 배경". `## 왜` 형식 아님 |
| `## 관계 (HOW)` | 위반 아님 | 주 헤딩은 "관계". `## 어떻게` 형식 아님 |
| `## 소스 커버리지` | 위반 아님 | 5W1H 헤딩 아님 |

→ §8.9가 금지하는 것은 `## 누가/왜/어떻게` **형식의 헤딩**이며, 도메인 의미 헤딩 뒤의 괄호 보조 레이블(WHAT/WHY/HOW)은 금지 대상이 아니다. EXECUTE 시 SKILL 본문에 이 근거를 1줄 주석으로 부기하여 향후 오해를 방지한다.

#### 3.2.7 환경 변경

해당 없음 (패키지·설정 변경 없음). 배포는 §3.2.8 참조.

#### 3.2.8 배치/마이그레이션

해당 없음 (DB·배치 없음). 단, EXECUTE 완료 후 **배포 단계 필요** — `opal/` 소스 수정분을 `scripts/install-mac.sh`(또는 `opal install`)로 `~/.opal/`에 재배포하여 발효 (L3 캡틴 직접, TASK §제약 배포 경계). 이는 코드 작업이 아닌 배포 실행이므로 Step 6에 분리한다.

### 3.3 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC | 산출물 검사 | `page-entity.md`·`opal-brain/SKILL.md`·`op-brain-ingest/SKILL.md` 세 곳의 entity 구조가 **동일 5섹션**(개요/책임 WHAT/설계배경 WHY/관계 HOW/소스 커버리지)으로 일치하고, @header 전사 금지가 [MUST]로 기재됨 |
| TS-002 | R-2 AC | 산출물 검사 | init 시드 Step과 ingest STEP 4에 입력 큐레이션 선행 절차 + provenance 3종 규칙이 [MUST]로 명문화됨 |
| TS-003 | R-3 AC (SKILL 절차 채택) | 산출물 검사 | brain-tool 코드 변경 없음 — `git diff opal/tools/brain-tool/brain_tool.py` 빈 결과. 입력 큐레이션이 SKILL 절차로만 처리됨 |
| TS-004 | R-4 AC | 산출물 검사 | `opal-brain/SKILL.md`에 재생성 런북(synthesis 백업 → 삭제 → init → 복원)이 기재되고, `--force` 한계 + synthesis 유실 리스크가 명시됨 |
| TS-005 | R-5 AC | 산출물 검사 | citation-rules §8.5가 변경 내용과 모순 없음 — brain ingest·init entity 항목이 §8.2·§8.8을 가리킴 |
| TS-006 | R-1·R-3 회귀 | 회귀 테스트 | `pytest opal/tools/brain-tool/tests/` 전체 통과 — `## 코드 참조`→`## 소스 커버리지` 개명에도 회귀 0 (add-page는 파일명 로드, 섹션명 미검증) |
| TS-007 | 완료기준 ④ 시연 | 기능 테스트 (시연) | 배포본에서 개선된 init로 entity 1건 재생성 — WHY 섹션에 provenance 3종 중 하나가 실제 명시되고 5섹션 구조를 준수함 (RED-first 대안, H-1 검증) |
| TS-008 | drift 정합 | 산출물 검사 | `opal-brain/SKILL.md` ingest --all 표의 "코드 @header → entity" 행이 코드 현실(ingest-scan 미스캔)에 맞게 정정됨 |

> **RED-first 판단** (`opal/core/references/harness/red-first.md`): 본 태스크는 **도구 코드 변경이 없으므로** 실패하는 단위 테스트를 선작성하는 고전적 RED-first가 적용되지 않는다. 검증은 (i) **회귀 테스트**(TS-006 — 개명이 기존 pytest를 깨지 않음을 GREEN으로 확인)와 (ii) **시연 검증**(TS-007 — 개선 SKILL로 entity 1건 재생성하여 행동 변화를 관찰)으로 대체한다. 시연은 "Don't fake it" 집행 효과를 실측하는 유일한 동적 검증 수단이다 (캡틴 RED-first 지시).

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1, 2, 3, 4 | opal-task-agent | 병렬 가능 (단, Step 1·2는 동일 파일 → 순차) | 4개 파일 콘텐츠 수정 |
| 2 | F-001 | 5 | opal-task-agent | 순차 (Phase 1 완료 후) | 정합 검증 — 4파일이 동일 5섹션을 가리키는지 cross-check |
| 3 | F-001 | 6 | PM 직접 | 순차 | 배포(install 재배포) + 시연 — L3 캡틴 직접 |

### 4.2 실행 체크리스트

> 총 6개 Step | Phase 3개 | 실행 모드: **단순** (§6 판별 참조)
> 전 Step 영역=Framework(스킬/가이드/참조), agent=opal-task-agent (캡틴 EXECUTE 영역/agent 배정). Step 6만 PM 직접(배포·시연).

#### Step 1: opal-brain SKILL — entity 5섹션 + 큐레이션 + provenance + @header 전사 금지

- [x] 완료
- **소속 기능**: F-001
- **영역**: 스킬 (Framework)
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-brain/SKILL.md` (L106-128 핵심 엔티티 시드 절)
- **작업 내용**: ① 본문 구조 4섹션 → 5섹션 표준(§3.2.1)으로 교체. ② 입력 큐레이션 선행 절차 [MUST] 삽입(§3.2.3). ③ @header 전사 금지 [MUST] + provenance 3종 규칙 [MUST] 추가(§3.2.2). ④ §8.9 충돌 없음 근거 1줄 주석 부기(§3.2.6).
- **완료 기준**: L128 본문 구조가 5섹션으로 교체되고, @header 전사 금지·provenance·큐레이션이 [MUST]로 기재됨. concept/flow/synthesis/term 절은 무변경(캡틴 확정 #1).
- **테스트**: TS-001, TS-002
- **실행 방법**: direct
- **의존**: 없음

#### Step 2: opal-brain SKILL — 재생성 런북 신규 절 + ingest --all drift 정정

- [x] 완료
- **소속 기능**: F-001
- **영역**: 스킬 (Framework)
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-brain/SKILL.md` (`## STEP: init` 하단 L160 직후 + L213-221 표)
- **작업 내용**: ① `### 재생성 런북 (brain 전체 재시드)` 신규 절 추가(§3.2.4) — synthesis 백업·`--force` 한계·유실 리스크 명시. ② ingest --all 표 "코드 @header → entity" 행(L220) drift 정정(§3.2 M-1b) — 코드 현실(ingest-scan: docs/skills/tasks→concept) 반영. ③ 변경이력 1행 추가(Step 1·2 통합, `(038)`, KST `2026-06-23`).
- **완료 기준**: 런북 절이 4단계(백업→삭제→init→복원)로 기재되고 `--force` 한계가 명시됨. drift 행이 정정됨. 변경이력 행 1개 추가.
- **테스트**: TS-004, TS-008
- **실행 방법**: direct
- **의존**: Step 1 (동일 파일 — 순차 수정, 충돌 방지)

#### Step 3: op-brain-ingest SKILL — STEP 4 entity 예시 5섹션 + 동일 규칙

- [x] 완료
- **소속 기능**: F-001
- **영역**: 스킬 (Framework)
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-brain-ingest/SKILL.md` (L168-197 entity 예시)
- **작업 내용**: STEP 4 entity 페이지 예시를 4섹션 → 5섹션 표준(§3.2.1)으로 교체 + @header 전사 금지·provenance·소스 커버리지 line number 규칙 추가(§3.2.1·§3.2.2). 변경이력 1행 추가(`(038)`, KST).
- **완료 기준**: entity 예시가 5섹션으로 일치하고 Step 1과 동일 규칙을 가리킴. term/concept 예시 무변경. 변경이력 행 추가.
- **테스트**: TS-001, TS-002
- **실행 방법**: direct
- **의존**: 없음 (Step 1과 다른 파일 — 병렬 가능)

#### Step 4: page-entity.md 템플릿 — 섹션 개명 + 가이던스 강화

- [x] 완료
- **소속 기능**: F-001
- **영역**: 가이드 (Framework)
- **agent**: opal-task-agent
- **파일**: `opal/tools/brain-tool/templates/page-entity.md` (L18-37)
- **작업 내용**: ① 마지막 섹션 `## 코드 참조` → `## 소스 커버리지`로 개명(L34). ② 각 섹션 가이던스 강화(§3.2.1) — WHAT 인용·WHY provenance·HOW wikilink·소스 커버리지 line number 부록. ③ @header 전사 금지 주석 추가. (frontmatter 키는 무변경 — add-page 계약 보존)
- **완료 기준**: 5섹션 헤딩이 `## 개요 / ## 책임 (WHAT) / ## 설계 배경 (WHY) / ## 관계 (HOW) / ## 소스 커버리지`로 확정되고 가이던스·@header 금지 주석 반영. frontmatter 무변경.
- **테스트**: TS-001, TS-006
- **실행 방법**: direct
- **의존**: 없음 (다른 파일 — 병렬 가능)

#### Step 5: citation-rules §8.5 정합 + 4파일 cross-check

- [x] 완료
- **소속 기능**: F-001
- **영역**: 참조 (Framework)
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/citation-rules.md` (L361-366 §8.5)
- **작업 내용**: ① §8.5 brain ingest 워커 항목 구체화 + init entity 경로 항목 추가(§3.2.5). 변경이력 1행 추가(`(027)`→ 신규 `(038)` 행, KST). ② **정합 cross-check**: Step 1·3·4 산출물의 5섹션 헤딩·@header 금지·provenance 문구가 서로 모순 없는지 확인(불일치 발견 시 해당 Step 재작업 요청).
- **완료 기준**: §8.5가 §8.2·§8.8을 명문화한 구체 문구로 갱신됨. 4파일 entity 규율이 일관됨(헤딩 동일·규칙 동일). 변경이력 행 추가.
- **테스트**: TS-005, TS-001(cross-check)
- **실행 방법**: direct
- **의존**: Step 1, 3, 4 (정합 cross-check가 선행 산출물 필요)

#### Step 6: 배포 + entity 1건 재생성 시연 (PM/캡틴)

- [ ] 완료
- **소속 기능**: F-001
- **영역**: 환경 (배포·검증)
- **agent**: PM 직접 (L3 캡틴 — 배포 경계상 워커가 install/실데이터 시연 불가)
- **파일**: `scripts/install-mac.sh` 실행 (소스 미변경) + 임의 brain entity 1건
- **작업 내용**: ① `opal/` 소스 수정분을 install 재배포로 `~/.opal/` 반영. ② 배포본 개선 init로 entity 1건 재생성 시연 — WHY에 provenance 3종 중 하나 명시·5섹션 준수 확인(TS-007). ③ `pytest opal/tools/brain-tool/tests/` 회귀 0 확인(TS-006).
- **완료 기준**: 재배포 성공 + 시연 entity가 5섹션·provenance 충족 + pytest 회귀 0.
- **테스트**: TS-006, TS-007
- **실행 방법**: direct (PM/캡틴)
- **의존**: Step 2, 5 (전 소스 수정 완료 후 배포)

> **docs/ 갱신 Step 판단**: 본 변경은 스킬·템플릿·참조의 내부 작성 규율 개선으로, `docs/ARCHITECTURE.md`의 brain 컴포넌트 구조나 `docs/CONVENTIONS.md`의 규칙을 바꾸지 않는다(brain 4모드·brain-tool 8서브명령 불변, 신규 패턴·API 없음). 따라서 docs/ 갱신 Step을 추가하지 않는다 (plan-guide §4.2 갱신 대상 판단 기준 대조 — 해당 없음).

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | 동일 파일(`opal-brain/SKILL.md`) 순차 수정 — 충돌 방지 |
| Step 1 ∥ Step 3 ∥ Step 4 | 독립 파일(opal-brain / op-brain-ingest / page-entity.md), 동일 5섹션 명세를 각자 반영 |
| Step 3·4 → Step 5 | Step 5 cross-check가 선행 산출물(5섹션 일관성) 필요 |
| Step 2·5 → Step 6 | 배포는 전 소스 수정 완료 후 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | entity 5섹션 표준 4파일 일관성 | TS-001 | 3파일 entity 구조가 동일 5섹션 + @header 전사 금지 [MUST] |
| F-001 | 큐레이션·provenance 명문화 | TS-002 | init 시드·ingest STEP 4에 큐레이션 선행 + provenance 3종 [MUST] |
| F-001 | 도구 무변경(SKILL 절차 채택) | TS-003 | `brain_tool.py` diff 빈 결과 |
| F-001 | 재생성 런북 + 유실 리스크 | TS-004 | 런북 4단계 + `--force` 한계 + synthesis 유실 명시 |
| F-001 | §8.5 정합 | TS-005 | §8.5가 §8.2·§8.8 명문화·init 경로 연결, 모순 없음 |
| F-001 | 시연 행동 검증 | TS-007 | 재생성 entity가 provenance 충족·5섹션 준수 |
| F-001 | drift 정정 | TS-008 | ingest --all 표 "코드 @header → entity" 행 정정 |

### 5.2 회귀 테스트

- [ ] `pytest opal/tools/brain-tool/tests/` 전체 통과 — `## 코드 참조`→`## 소스 커버리지` 개명에도 회귀 0 (TS-006)
- [ ] brain 4모드(init/ingest/query/lint) 기존 동작 불변 — brain_tool.py 무변경 확인
- [ ] concept/flow/synthesis/term 템플릿·규율 무변경 (캡틴 확정 #1)

### 5.3 코드/문서 품질

- [ ] 변경이력 행 추가 — opal-brain SKILL·op-brain-ingest SKILL·citation-rules 각 1행 (KST `2026-06-23`, `(038)`) (→ D-7 §CONVENTIONS 변경이력 의무)
- [ ] §8.9 충돌 없음 근거가 SKILL/PLAN에 명시됨 (§3.2.6)
- [ ] 배포 경계 준수 — `~/.opal/` 직접 편집 없음, `opal/` 소스만 수정 후 install 재배포 (→ D-1)
- [ ] 5섹션 헤딩이 §8.9 금지 형식(`## 누가/왜/어떻게`) 아님

### 5.4 보안

- [ ] 변경 파일에 하드코딩 토큰·시크릿 없음 (Markdown 문서만 — 해당 없음 예상, 확인)
- [ ] brain-tool 단방향 보존 — wiki→origin 역수정 규칙 문구 훼손 없음 (TASK §제약)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 6개 (단, Step 6은 PM 배포·시연) | 경계 — 코드 작업 Step은 5개 |
| 변경 파일 수 | 4개 (스킬 2·템플릿 1·참조 1) | 복잡 경계 |
| 모듈 범위 | 단일 — brain 작성 규율(entity)에 국한 | 단순 |
| 작업 유형 | 문서·템플릿 콘텐츠 개선 (코드 무변경) | 단순 |
| 외부 의존성 | 없음 (신규 패키지·API·도구 없음) | 단순 |
| **실행 모드** | **단순** | 모든 Step `direct`, 동일 agent(opal-task-agent) 순차/병렬, 별도 에이전트 토폴로지 불필요 |

> 변경 파일 4개는 복잡 경계이나, 4파일이 **동일한 단일 콘텐츠(5섹션 표준)**를 각자 반영하는 동질 작업이고 코드 변경·외부 의존성·다중 모듈이 모두 없으므로 **단순 모드**로 판정한다. §7 실행 아키텍처는 생략한다.

---

## 7. 실행 아키텍처 (복잡 모드 시)

해당 없음 — 단순 모드 (§6). 생략.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 스킬·참조·템플릿 | Markdown + YAML frontmatter | (해당 community-skill 없음 — 순수 문서 작업) |
| 도구 회귀 | Python 3 / pytest (brain_tool.py — 변경 없음, 회귀 검증만) | — |
| 배포 | Bash (`scripts/install-mac.sh`) | — |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| 없음 | 외부 라이브러리 API 조사 불필요 — Markdown/Python stdlib 작업 (ANALYSIS §6.3) |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` | Enforce don't just advise / Don't fake it / Simplicity / Surgical Changes |
| D-2 | 설계 | 인용 규칙 §8 | `opal/core/references/harness/citation-rules.md` (§8.2·§8.5·§8.8·§8.9) | 코드 식별자 본문 주어 금지·부록 분리·5W1H 헤딩 금지·검증 연결 |
| D-3 | 소스 | opal-brain SKILL | `opal/skills/opal-brain/SKILL.md` (L106-128, L160, L213-221) | init 시드 entity 규율·런북 위치·drift 표 (수정 대상) |
| D-4 | 소스 | op-brain-ingest SKILL | `opal/skills/op-brain-ingest/SKILL.md` (L168-197) | STEP 4 entity 예시·작성 규율 (수정 대상) |
| D-5 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py` (L386-459 cmd_init, L1068-1146 ingest-scan) | `--force` pages/ 보존·코드 스캔 분기 부재 (분석 한정) |
| D-6 | 소스 | page-entity.md 템플릿 | `opal/tools/brain-tool/templates/page-entity.md` (L18-37) | add-page 적용 entity 구조 (수정 대상) |
| D-7 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 변경이력 의무·배포 경계·플랫폼 분기 규칙 |
| D-8 | 참조 | 좋은 예시 | `pointail/.opal/brain/pages/entity/advertiser/advertiser-admin-management.md` | 5섹션·부록 분리 참조 기준 (TASK §D-6) |
| D-9 | 설계 | TASK·ANALYSIS | `tasks/038-260623-opd-브레인-지식품질-개선/{TASK,ANALYSIS}.md` | 스코프·M-1~M-5·H-1~H-7·R-T1~R-T5 SSOT |

> **[MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무**: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함." → Step 2·3·5에 변경이력 행 추가 반영.
> **[MUST] `docs/CONVENTIONS.md` §배포 경계**: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/` …)에서 수행한다." → 전 EXECUTE Step이 `opal/` 소스만 수정, 발효는 Step 6 install 재배포(L3 캡틴).
> **[MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리**: "스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다." → 5섹션 규율·런북은 플랫폼 독립 기술.

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-T1 | SKILL 텍스트 강화가 실제 집행 효과를 갖는지 검증 어려움 | F-001 | 중 | TS-007 시연으로 행동 변화 실측 (H-1·H-5). 도구 게이트는 의미 판정 불가로 미채택 — 시연이 유일 동적 검증 |
| R-T2 | provenance 3종이 [MUST]만으로 누락될 위험 | F-001 | 중 | `(WHY 미확보)` 태그를 명시적 옵션으로 제공해 "솔직 표기"를 강제 — 누락보다 미확보 표기가 안전 (Don't fake it) |
| R-T3 | `## 코드 참조`→`## 소스 커버리지` 개명 시 기존 페이지 구 섹션명 불일치 | F-001 | 낮 | 기존 페이지는 런북 재생성 시 새 규율 적용 — 소급 변경 없음(ANALYSIS §3.2). pytest 회귀 0(TS-006) |
| R-T4 | 재생성 시 synthesis(query 파생) 유실 | F-001 | 높 | 런북 ① synthesis 백업을 [MUST] 첫 단계로 + 유실 리스크 ⚠️ 명시(§3.2.4, H-8) |
| R-T5 | drift 정정이 본 태스크 스코프 외 변경으로 비칠 위험 | F-001 | 낮 | 캡틴 확정 #4로 "의식적 스코프 추가" 확정 — PLAN M-1b·TS-008로 명시 (H-7) |
| R-T6 | `init --force` 오해로 운영자가 pages/ 미삭제 후 재생성 실패 | F-001 | 중 | 런북에 `--force` 한계를 ⚠️로 명시(§3.2.4, H-2) — brain_tool.py:436-440 근거 |

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-06-23 16:31 | 초기 작성 — 038 entity 지식 품질 개선 PLAN (Flat, 단순 모드, 6 Step). M-1~M-5 + drift 정합 설계, RED-first 시연 대체, H-1~H-8 리스크 가설 표 (038) |
