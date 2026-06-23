# ANALYSIS: 브레인 entity 지식 품질 개선 — ingest @header 전사 탈피

> 작성일: 2026-06-23
> 입력: TASK.md
> 출력: ANALYSIS.md

---

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | TASK.md | `tasks/038-260623-opd-브레인-지식품질-개선/TASK.md` | 스코프·요구사항·확정 설계방향 SSOT |
| D-2 | 설계 | citation-rules | `opal/core/references/harness/citation-rules.md` | §8.1 적용대상·§8.8 부록분리·§8.9 5W1H 금지 |
| D-3 | 소스 | opal-brain SKILL | `opal/skills/opal-brain/SKILL.md` | init 시드 entity 규율·템플릿 수정 대상 |
| D-4 | 소스 | op-brain-ingest SKILL | `opal/skills/op-brain-ingest/SKILL.md` | STEP 4 entity 작성 규율·템플릿 수정 대상 |
| D-5 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py` | cmd_init/cmd_analyze/cmd_lint/cmd_ingest_scan/--force 동작 |
| D-6 | 소스 | page-entity.md 템플릿 | `opal/tools/brain-tool/templates/page-entity.md` | add-page 호출 시 실제 적용되는 entity 페이지 구조 |
| D-7 | 소스 | 현재 entity 페이지 (ref) | `.opal/brain/pages/entity/brain-tool.md` | 현재 프로젝트 entity 구조 참조 샘플 |
| D-8 | 소스 | 현재 entity 페이지 (ref) | `.opal/brain/pages/entity/state-tool.md` | 현재 프로젝트 entity 구조 참조 샘플 |

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/skills/opal-brain/SKILL.md` | init 시드 entity 작성 절차·본문 구조 명세 | 필요 | L120-128 (시드 entity 본문 구조) |
| `opal/skills/op-brain-ingest/SKILL.md` | CLOSE ingest entity 작성 규율·템플릿 | 필요 | L168-197 (STEP 4 entity 예시) |
| `opal/tools/brain-tool/templates/page-entity.md` | add-page 호출 시 실제 적용 템플릿 | 검토 필요 | L1-37 (전체) |
| `opal/tools/brain-tool/brain_tool.py` | cmd_init/cmd_analyze/cmd_ingest_scan/--force 집행 | 코드 변경 없음(분석 한정) | L386-459 (cmd_init), L977-1048 (cmd_analyze), L1068-1146 (cmd_ingest_scan) |
| `opal/core/references/harness/citation-rules.md` | §8.5 검증 연결 표 | 가벼운 정합 필요 | L363-366 (§8.5) |

### 1.2 아키텍처 패턴

brain entity 페이지 생성 경로는 세 갈래이며 각각 독립적인 절차를 갖는다:

1. **`//opbr init` 시드 경로 (주 경로)**: SKILL.md L120-128 → `brain-tool analyze` 결과(seed_candidates) 기반 → LLM이 entity 본문 작성 → `brain-tool add-page` 호출.
2. **단건 `//opbr ingest <소스>` 경로**: SKILL.md L184-200 → 단일 소스 Read → LLM 본문 작성 → `brain-tool add-page`.
3. **CLOSE `op-brain-ingest` 경로**: op-brain-ingest SKILL STEP 4 → 신규 컴포넌트 판정 시 entity 1건 작성.

페이지 저장 메커니즘은 결정론적 도구(`brain-tool add-page`)가 집행하며, 본문 작성만 LLM 담당이다 (`brain_tool.py:465-525`).

### 1.3 의존성 맵

```
opal-brain SKILL.md (절차 명세)
    └── brain-tool analyze    → seed_candidates 반환   (brain_tool.py:977-1048)
    └── brain-tool add-page   → 페이지 생성·검증       (brain_tool.py:465-525)
    └── brain-tool index      → index.md 재생성        (brain_tool.py:531-545)

page-entity.md 템플릿
    └── brain_tool.py:490 — read_template("page-entity.md", command) 로 로드

op-brain-ingest SKILL.md (CLOSE 워커 절차)
    └── brain-tool add-page (동일 집행 도구 사용)
```

### 1.4 테스트 현황

- `opal/tools/brain-tool/tests/test_brain_tool.py` 존재 확인.
- brain-tool cmd_init·add-page·lint 등 핵심 명령 pytest 커버.
- 도구(brain_tool.py) 변경 없이 스킬 문서·page-entity.md 템플릿만 수정 시: brain-tool pytest 회귀 위험 없음. page-entity.md는 add-page가 파일명으로 로드하며 내부 섹션명을 검증하지 않으므로 회귀 0 예상.

---

## 2. 분석 결과 — 목표별 정밀화

### A. entity 작성 경로 정밀 매핑

#### A-1. opal-brain SKILL init 시드 entity 현재 구조

**위치**: `opal/skills/opal-brain/SKILL.md` L120-128 ("핵심 엔티티 시드" 절, Step 5)

현재 SKILL.md가 지시하는 entity 본문 구조 (L127-128):
```
본문 구조: `## 개요`, `## 설계 배경 (WHY)`, `## 인터페이스`, `## 관련 페이지`
```
이것은 **4섹션** 구조다. `## 책임 (WHAT)`, `## 관계 (HOW)`, `## 소스 커버리지`(부록)가 없다.

**실제 적용 템플릿**: `opal/tools/brain-tool/templates/page-entity.md` (add-page 호출 시 brain_tool.py:490이 로드)

현재 page-entity.md 섹션 구조:
```
## 개요
## 책임 (WHAT)
## 설계 배경 (WHY) — brain 누적
## 관계 (HOW)
## 코드 참조
```
이것은 이미 **5섹션** 구조다.

> **핵심 불일치 발견**: `opal/skills/opal-brain/SKILL.md` L127-128의 4섹션 명세가 실제 `page-entity.md` 템플릿의 5섹션 현실과 이미 drift되어 있다. SKILL.md가 코드(템플릿) 현실을 따라잡지 못한 상태.

#### A-2. op-brain-ingest SKILL STEP 4 entity 현재 구조

**위치**: `opal/skills/op-brain-ingest/SKILL.md` L168-197 (페이지 구조 예시 — entity 타입)

현재 STEP 4 entity 예시 섹션:
```
## 개요
## 설계 배경 (WHY)
## 인터페이스
## 관련 페이지
```
이것도 **4섹션** 구조. `## 책임 (WHAT)`, `## 관계 (HOW)`, `## 소스 커버리지`(부록) 없음.

#### A-3. 5섹션 표준 전환 시 수정 지점 목록

| # | 파일 | 수정 내용 | 줄 범위 |
|---|------|----------|---------|
| M-1 | `opal/skills/opal-brain/SKILL.md` | 본문 구조 4섹션 → 5섹션 표준으로 교체 + @header 전사 금지 [MUST] 추가 + 입력 큐레이션 선행 절차 추가 + provenance 3종 규칙 추가 | L120-128 (핵심 엔티티 시드 Step 5) |
| M-2 | `opal/skills/opal-brain/SKILL.md` | 재생성 런북 신규 절 추가 | `## STEP: init` 하단 신규 |
| M-3 | `opal/skills/op-brain-ingest/SKILL.md` | STEP 4 entity 예시 4섹션 → 5섹션 표준 + 동일 규칙 추가 | L168-197 |
| M-4 | `opal/tools/brain-tool/templates/page-entity.md` | 현재 5섹션 구조 유지, 마지막 섹션 `## 코드 참조` → `## 소스 커버리지` 개명 + 각 섹션 가이던스 텍스트 개선 + @header 전사 금지·provenance 주석 추가 | L18-37 |
| M-5 | `opal/core/references/harness/citation-rules.md` | §8.5 검증 연결 표 보강(가벼운 정합) | L363-366 |

> M-4: 도구 코드(brain_tool.py) 변경 없음. 템플릿 내용만 변경.

---

### B. 입력 큐레이션 수단 판단 근거

#### B-1. PROJECT.md 문서 레지스트리 활용 가능성

`docs/PROJECT.md`가 존재하며 프로젝트별 문서 레지스트리(관련 docs 목록)를 보유하고 있다. entity 작성 전 WHY 소스 주입의 1차 재료로 적합하다. 단, 문서 레지스트리는 프로젝트마다 구조가 다르므로 자동 도구로 파싱하기 어렵다(비정형 Markdown).

#### B-2. git blame → task 역추적 신뢰성

git log 표본 확인 결과, 이 프로젝트의 커밋 메시지는 **일관되게 태스크 번호를 괄호 안에 참조**한다:
```
feat(console): 프로젝트 브레인 질의 콘솔 연동 + 비동기 잡 타임아웃 견고화 (036, 037)
fix(brain): validate_frontmatter에 tags/sources/related 평탄성 검사 추가
feat(027): OPAL Brain 비즈니스 용어집(term) 관리 체계
```
태스크 번호 참조가 일관적이므로 git blame → 커밋 → 태스크 번호 추출 → `tasks/NNN/PLAN.md` 역참조 경로는 기술적으로 유효하다. 단, 다음 조건에 의존한다:
- 커밋 메시지에 태스크 번호 명시 (이 프로젝트: 일관적)
- 파일이 여러 태스크에 걸쳐 수정된 경우 WHY 후보가 복수 → LLM이 선별 필요

#### B-3. 결정 권고

**권고안: SKILL 절차 강제 (brain-tool why-sources 도구화 미채택)**

근거:
1. **복잡도 대비 이득 미달**: `brain-tool why-sources` 신규 구현 시 git subprocess + 커밋 파싱 + PLAN.md 역추적 로직 추가가 필요하나, 결과는 "WHY 소스 후보 목록"이며 선별은 여전히 LLM이 수행한다. SKILL 절차로 동일 효과를 얻을 수 있다 (Simplicity First).
2. **SKILL 절차로 충분**: init 시드 Step 5에 "entity 작성 전 PROJECT.md 문서 레지스트리에서 관련 docs 확인 + 관련 태스크 PLAN.md 확인 + 관련 brain 페이지 후보 확인을 [MUST]로 강제"하면 WHY 큐레이션 선행이 명문화된다.
3. **R-3 코드 변경 없음 경로 채택** → pytest 회귀 0.
4. **도구화 조건**: 추후 `init --full`(전체 모듈 시드)로 수백 entity를 처리하는 시나리오가 현실화되면 자동화를 재검토한다.

---

### C. 재생성 런북 위치·동작

#### C-1. `init --force` 실제 동작 (코드 확인)

`brain_tool.py:386-459` (`cmd_init`) 분석:

- L401-403: `--force` 시 `brain_already_initialized` guard를 우회하고 계속 진행.
- L436-440: `brain_root.mkdir(parents=True, exist_ok=True)` + 하위 dirs `exist_ok=True` → **기존 pages/ 디렉토리 및 페이지 파일 보존**.
- L449-451: `SCHEMA.md` / `index.md` / `log.md`를 템플릿으로 **덮어쓰기**.

**결론**: `init --force`는 SCHEMA.md·index.md·log.md를 템플릿으로 초기화하지만, **`pages/` 하위 기존 페이지를 삭제하지 않는다**. 기존 entity/concept/synthesis 페이지는 보존된다.

> **PM 확정 사실 정정**: TASK.md 런북 ② "`.opal/brain` 삭제 (또는 `//opbr init --force`)"에서 `//opbr init --force`만으로는 pages/ 페이지가 삭제되지 않으므로, "재생성" 목적에 `--force`만으로는 불충분하다. 런북에 이 사실을 명확히 명시해야 한다.

**진정한 재생성 절차**:
- `.opal/brain/pages/entity/` 선택 삭제 후 init 재실행, 또는
- `.opal/brain/` 전체 삭제 후 init (synthesis·concept도 함께 재생성)

#### C-2. synthesis 백업 필요성 재확인

synthesis 페이지는 query 파생 결과로, `ingest-scan` 대상이 아니어서 `init`로 재생성 불가. `.opal/brain/` 전체 삭제 시 유실된다. TASK.md 런북 ①(synthesis/ 백업)은 필수 절차가 맞다.

#### C-3. 런북 문서화 위치

`opal/skills/opal-brain/SKILL.md` 내 `## STEP: init` 하단에 `### 재생성 런북 (brain 전체 재시드)` 절 신규 추가. 운영자가 init 모드 문서에서 런북을 찾는 것이 자연스럽다.

---

### D. citation §8 연결점

**§8.5 검증 연결 표 현재 문구** (`opal/core/references/harness/citation-rules.md:363-366`):

```
- brain ingest 워커: `opal/skills/op-brain-ingest/SKILL.md` STEP 4 작성 규칙이 이 §8을 따른다.
```

이번 변경은 op-brain-ingest STEP 4를 수정하는 것이므로 현재 문구와 방향이 일치한다. 단, 변경 후 STEP 4가 5섹션 표준·provenance·입력 큐레이션을 추가하면 §8.5 문구를 보다 구체적으로 갱신하는 것이 정합 완결에 적합하다:

- **현재**: "STEP 4 작성 규칙이 이 §8을 따른다" (generic)
- **개선 후 권고**: "STEP 4 entity 작성 규칙이 §8.2(코드 식별자 본문 주어 금지)·§8.8(부록 분리)을 명문화한다" (구체적)

`opal/skills/opal-brain/SKILL.md` init entity 절차도 개선되므로, §8.5에 opal-brain init entity 경로 연결 항목 추가를 PLAN에서 검토한다.

---

### E. §8.9 충돌 회피 확인

**§8.9 원문** (`opal/core/references/harness/citation-rules.md:401-411`):
> `[MUST] 5W1H를 페이지 섹션 구조 템플릿으로 강제하는 것을 금지한다.` brain 페이지나 기획 산출물의 섹션 헤딩으로 `## 누가`, `## 왜`, `## 어떻게` 등을 배치하지 않는다.

**5섹션 표준 헤딩과의 충돌 여부**:

| 5섹션 헤딩 | §8.9 금지 여부 | 근거 |
|-----------|--------------|------|
| `## 개요` | 허용 | 5W1H 아님 |
| `## 책임 (WHAT)` | 허용 | 주 헤딩은 "책임"(도메인 역할). `## 무엇을` 형식 아님 |
| `## 설계 배경 (WHY)` | 허용 | 주 헤딩은 "설계 배경". `## 왜` 형식 아님 |
| `## 관계 (HOW)` | 허용 | 주 헤딩은 "관계". `## 어떻게` 형식 아님 |
| `## 소스 커버리지` | 허용 | 5W1H 아님 |

**결론**: 5섹션 표준은 §8.9를 위반하지 않는다. 주 헤딩은 도메인 의미 중심이며, 5W1H(WHAT/WHY/HOW)는 괄호 보조 레이블로만 부기된다. §8.9가 금지하는 것은 `## 누가`, `## 왜`, `## 어떻게` 형식의 헤딩이지, 괄호 보조 레이블이 아니다.

단, 괄호 레이블(WHAT/WHY/HOW)이 헤딩의 "의미 주어"처럼 읽힐 수 있으므로, PLAN/SKILL 수정 시 §8.9 충돌 없음 근거를 명시하는 것이 안전하다.

---

### F. 리스크 가설 (H-N) 후보

PLAN·TEST-SCENARIO가 검증해야 할 가설 목록:

| 가설 ID | 가설 내용 | 검증 방법 |
|---------|----------|----------|
| H-1 | SKILL.md 텍스트 강화만으로 AI 행동이 실제로 달라지는가 | 개선된 SKILL로 entity 1건 재생성 시연 — WHY 섹션에 provenance 3종 중 하나가 명시되는지 확인 |
| H-2 | `init --force`가 pages/ 페이지를 삭제하지 않는 사실이 런북에 정확히 반영되는가 | 런북 절차 ②가 "`.opal/brain/pages/entity/` 삭제 또는 `.opal/brain/` 전체 삭제"로 기재되는지 검토 |
| H-3 | `## 책임 (WHAT)` 등 괄호 보조 레이블이 §8.9 위반으로 해석될 위험이 있는가 | citation-rules §8.9 원문과 5섹션 헤딩 비교 — 이미 허용 확인, PLAN에 근거 기술 |
| H-4 | page-entity.md `## 코드 참조` → `## 소스 커버리지` 개명이 기존 pytest를 깨는가 | pytest 실행 — add-page는 파일명으로 로드, 내부 섹션명 미검증 → 회귀 0 예상 |
| H-5 | provenance 3종 규칙이 SKILL [MUST]만으로 집행 가능한가, 도구 게이트가 필요한가 | "Enforce, don't just advise" 원칙 적용 수준 결정 필요 — PLAN에서 결정 |
| H-6 | 입력 큐레이션 선행 절차가 init 시드 소요 시간을 허용 불가 수준으로 늘리는가 | seed_candidates 수(현재 프로젝트: ~7개)로 추정 — 허용 가능 예상 |
| H-7 | opal-brain SKILL L214-221의 "코드 @header → entity" drift 수정이 이번 태스크 스코프에 포함되는가 | TASK.md 스코프 섹션과 대조 — 현재 미포함으로 보이나 PLAN에서 명시 필요 |

---

## 2-보완. PM 확정 사실 원문 재확인 및 정밀화

### 사실 1: entity 생성 경로 — 확인

**근거** (`brain_tool.py:1068-1146`, `opal/skills/opal-brain/SKILL.md:203-232`):
- ingest-scan은 docs(kind:doc) / skills(kind:skill) / tasks(kind:task) 세 종류만 스캔한다.
- 코드 파일(@header) 스캔 분기 없음.
- entity 주 경로 = `//opbr init` 시드(analyze→seed_candidates). **PM 사실 1 완전 정확**.

### 사실 2: 문서↔코드 불일치 — 확인

**근거** (`opal/skills/opal-brain/SKILL.md:214-221`):
- ingest --all 배치 정책 표에 `| 코드 @header | entity | @header 필드 흡수 + source_ref 포인터 |` 행이 존재.
- brain_tool.py:1068-1146 ingest-scan에 코드 파일 스캔 분기 없음 → drift 확인.
- **PM 사실 2 완전 정확**.

### 사실 3: 멱등 skip — 확인

**근거** (`brain_tool.py:1069-1079`):
- `scan_pages(brain_root)` → 기존 페이지의 sources frontmatter 집합 수집 → `_is_ingested(ref)` 비교.
- 페이지 삭제 시 sources 집합에서도 제거 → 재생성 대상. **PM 사실 3 완전 정확**.

### 사실 4: cmd_lint 탐지 전용 — 확인

**근거** (`brain_tool.py:803-921`):
- 함수 마지막 `ok(command, issues=issues, ...)` 만 호출. 파일 수정 코드 없음.
- **PM 사실 4 완전 정확**.

---

## 3. 영향 범위

### 3.1 직접 영향

| 파일 | 변경 내용 |
|------|----------|
| `opal/skills/opal-brain/SKILL.md` | init 시드 entity 본문 구조(4→5섹션) + @header 전사 금지 [MUST] + 입력 큐레이션 절차 + 재생성 런북 신규 절 |
| `opal/skills/op-brain-ingest/SKILL.md` | STEP 4 entity 예시(4→5섹션) + 동일 규칙 추가 |
| `opal/tools/brain-tool/templates/page-entity.md` | 마지막 섹션 개명 + 가이던스 텍스트 개선 |
| `opal/core/references/harness/citation-rules.md` | §8.5 검증 연결 표 보강(가벼운 정합) |

### 3.2 간접 영향

- 기존 entity 페이지(`.opal/brain/pages/entity/*.md`): 소급 변경 없음 — 런북 실행(프로젝트별 재시드) 시 새 규율 적용.
- brain-tool 코드: SKILL 절차 경로 채택 시 변경 없음.
- 배포: `opal/` 소스 수정 → `install` 재배포로 `~/.opal/`에 반영 (L3 캡틴 직접 수행).

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경: 없음
- [ ] API 인터페이스 변경: 없음 (brain-tool CLI 변경 없음)
- [ ] 설정/환경변수 변경: 없음
- [ ] 빌드/배포 파이프라인 변경: 없음 (install 재배포만)
- [x] pytest 회귀: page-entity.md 내용 변경만, brain_tool.py 변경 없음 → 회귀 0 예상

---

## 4. 핵심 발견 사항

1. **page-entity.md 템플릿이 이미 5섹션**: 실제 add-page 템플릿(`opal/tools/brain-tool/templates/page-entity.md`)은 이미 5섹션(개요/책임 WHAT/설계배경 WHY/관계 HOW/코드참조) 구조이나, SKILL.md 두 곳(opal-brain L127-128, op-brain-ingest L168-197)의 entity 예시가 4섹션으로 뒤처져 있다. SKILL.md가 템플릿 현실을 반영하도록 업데이트하는 것이 주요 수정 작업이다.

2. **`init --force`는 pages/를 삭제하지 않는다**: `cmd_init` --force는 SCHEMA·index·log만 템플릿으로 초기화하고 `pages/` 하위 페이지는 보존(`exist_ok=True`). TASK.md 런북 ② "또는 `//opbr init --force`"는 부정확하며, 런북에서 정정 필요.

3. **SKILL 절차 강제가 도구화보다 적합**: git blame→task 역추적은 기술적으로 가능하나, Simplicity First 원칙상 SKILL 절차 강화로 R-2·R-3를 달성할 수 있다. `brain-tool why-sources` 도구 신규 구현 불필요.

4. **ingest --all 표의 drift**: opal-brain SKILL.md L214-221 표의 "코드 @header → entity" 행이 ingest-scan 미구현으로 drift된 상태. 이번 태스크 스코프(entity 작성 규율 개선)와는 별개 이슈이나, 같은 SKILL.md 수정 시 함께 처리할지 PLAN에서 명시 필요.

5. **§8.9 충돌 없음 확인**: 5섹션 표준의 헤딩(`## 개요`, `## 책임 (WHAT)`, `## 설계 배경 (WHY)`, `## 관계 (HOW)`, `## 소스 커버리지`)은 §8.9가 금지하는 "## 누가/왜/어떻게" 형식이 아니므로 위반 없음.

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-T1 | SKILL.md 언어 강화가 실제 집행 효과를 갖는지 검증 어려움 | 중 | `~/.opal/PRINCIPLES.md` "Enforce, don't just advise" |
| R-T2 | provenance 3종 규칙이 LLM [MUST]로만 강제될 경우 워커가 누락할 위험 | 중 | `TASK.md` §제약 "Don't fake it" |
| R-T3 | page-entity.md 마지막 섹션 개명 시, 기존 entity 페이지가 구 섹션명 유지 → 불일치 | 낮 | `opal/tools/brain-tool/templates/page-entity.md:34` |
| R-T4 | 재생성 런북에서 synthesis 백업 없이 `.opal/brain/` 삭제 시 query 파생 지식 유실 | 높 | `TASK.md` §확정 설계방향 "⚠️ 리스크" |
| R-T5 | SKILL.md L214-221 drift 수정 스코프 포함 여부 미결 | 낮-중 | `opal/skills/opal-brain/SKILL.md:214-221` |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어 | Python | 3.x (brain_tool.py) |
| 포맷 | Markdown + YAML frontmatter | — |
| 테스트 | pytest | — |
| 도구 | brain-tool CLI (`run.sh` venv 래퍼) | — |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| `op-brain-ingest` | CLOSE ingest entity 경로 수정 대상 |
| `opal-brain` | init 시드 entity 경로 + 런북 문서화 수정 대상 |

### 6.3 추천 MCP

없음 — 외부 라이브러리 조사 불필요 (순수 Markdown/Python stdlib 작업).

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-06-23 | 초기 작성 — 038 entity 지식 품질 개선 분석 (038) |
