# PLAN: brain related 프론트매터 위키링크 정비 + validate 링크필드 집행 강화

> 작성일: 2026-07-10
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py` | `validate_frontmatter`·`cmd_add_page`·argparse 변경 대상 |
| D-2 | 설계 | brain-validate-flatness-enforcement | `.opal/brain/pages/concept/brain-validate-flatness-enforcement.md` | 035 평탄성 가드 설계 배경 + 034 사각지대 기록(quoted `[[]]` 미검출 원리) |
| D-3 | 소스 | brain-tool 테스트 | `opal/tools/brain-tool/tests/test_brain_tool.py` | R-3·R-5 테스트 추가 위치 + 기존 RED-first 패턴 |
| D-4 | 설계 | tools.md | `opal/core/references/tools.md` | brain-tool 커맨드 설명 갱신(R-6) |
| D-5 | 설계 | brain-tool entity 페이지 | `.opal/brain/pages/entity/brain-tool.md` | 인터페이스 설명 갱신(R-6) |
| D-6 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 코드/문서 컨벤션·배포 경계·변경이력 규칙 |

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/brain-tool/brain_tool.py` | brain CLI 본체 | O | `validate_frontmatter` 정의 `:274-301`, 035 평탄성 루프 `:294-299`, `return issues` `:301` |
| `opal/tools/brain-tool/brain_tool.py` | 상수 정의 | O | `OPTIONAL_FRONTMATTER = [...]` `:51` |
| `opal/tools/brain-tool/brain_tool.py` | add-page 인자 반영 | O | tags/sources CSV 평탄화 `:501-504`, validate 호출 `:507-509`, yaml dump `:511` |
| `opal/tools/brain-tool/brain_tool.py` | add-page argparse | O | `p_add.add_argument("--tags")`/`("--sources")` `:1191-1192` |
| `opal/tools/brain-tool/brain_tool.py` | @header 변경이력 | O | description 라인 `:6` (`[027]`·`[035]` 인라인 이력) |
| `opal/tools/brain-tool/tests/test_brain_tool.py` | 단위 테스트 | O | `make_args` 기본값 `:56-88`(related 키 없음), `_add_page` 헬퍼 `:130-140`, `TestAddPage` `:231`, `TestValidateFrontmatter` `:1410` |
| `.opal/brain/pages/entity/memory-tool.md` | 정비 대상 페이지 | O | related `:11-13` (`"[[state-tool]]"`, `"[[three-layer-memory-architecture]]"`) |
| `.opal/brain/pages/concept/fixture-vs-real-blind-spot-lesson.md` | 정비 대상 페이지 | O | related `:14-15` (`"[[memory-tool]]"`, `"[[agentic-output-direct-verification-lesson]]"`) |
| `.opal/brain/pages/concept/memory-lifecycle-graduation-workflow.md` | 정비 대상 페이지 | O | related `:12-13` (`"[[memory-tool]]"`, `"[[three-layer-memory-architecture]]"`) |
| `.opal/brain/pages/entity/skill-opal-pilot-data-design.md` | **추가 발견** 정비 후보 | 조건부(§5 R-K1) | related `:6` — `.md` 접미사 4항목 (TASK 미포착) |
| `opal/core/references/tools.md` | 도구 설명 문서 | O(R-6) | add-page `:479`, validate `:485` |
| `.opal/brain/pages/entity/brain-tool.md` | brain-tool 지식 페이지 | O(R-6) | validate 평탄성 설명 `:40`, related `:12` |
| `.opal/brain/pages/concept/brain-validate-flatness-enforcement.md` | 035 설계 페이지 | O(R-6) | 링크필드 집행 확장 기술 |

### 현재 상태

- **정규화 대상 6항목 실측 확정** — 3페이지 모두 quoted block form `"[[slug]]"` (D-1 인접 파일 grep으로 6건 정확 일치). 정규화 후 슬러그 4종(`state-tool`, `three-layer-memory-architecture`, `memory-tool`, `agentic-output-direct-verification-lesson`)은 모두 실제 페이지 파일과 1:1 매칭됨을 확인 — 정규화가 broken_link를 유발하지 않는다.
- **validate 사각지대 재확인** — `validate_frontmatter`의 035 평탄성 루프(`brain_tool.py:294-299`)는 `related`가 "flat list of strings"인지만 본다. `"[[state-tool]]"`은 정상 `str`이므로 통과한다 (→ D-2 §결정 배경). 근본 구멍: quoted `[[...]]` 문자열이 값 형식 검사를 통과.
- **add-page 인자 실측** — argparse는 `--type`·`--title`·`--tags`·`--sources`뿐, `--related` 없음(`brain_tool.py:1189-1192`). CSV 평탄화는 tags/sources만 `[x.strip() for x in ...split(",")]` 패턴으로 처리(`:501-504`). `related`는 미처리 → 손편집 유입 확정.
- **테스트 하네스** — mock 금지, 실제 `brain_tool.py` import 호출(`test_brain_tool.py:19,41`). `make_args` 기본값에 `related` 키가 없어(`:56-88`) `--related` 도입 시 기본값 추가가 필수. 035 검증 로직은 RED-first(테스트 선작성→FAIL 확인→구현) 패턴으로 도입됨(→ D-2 §RED-first 강제).

### 영향 범위

- `validate_frontmatter` 반환 계약(issue 문자열 리스트)은 불변 — 기존 호출부(`cmd_validate`, `cmd_add_page:507`)는 그대로 동작. 신규 검사는 issue를 **추가**만 하므로 기존 검증(필수 5필드·type·status enum·035 평탄성)은 훼손되지 않는다.
- `--related` 추가는 add-page 경로에만 영향. 미지정 시 `args.related`가 falsy → 템플릿 기본값 유지(기존 동작 불변).
- **영역 간 파급(신규 발견)**: 링크필드 `.md` 거부 규칙이 실 저장소 `.opal/brain`의 `skill-opal-pilot-data-design.md`(related `.md` 접미사 4항목, `:6`)를 신규로 `frontmatter_invalid` 표면화 → §5 R-K1로 에스컬레이션.

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| - | (없음) | 신규 파일 없음 — 기존 파일 수정만 | - |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `.opal/brain/pages/entity/memory-tool.md` | related 2항목 `"[[...]]"` → 평탄 슬러그 | `:11-13` |
| M-2 | `.opal/brain/pages/concept/fixture-vs-real-blind-spot-lesson.md` | related 2항목 정규화 | `:14-15` |
| M-3 | `.opal/brain/pages/concept/memory-lifecycle-graduation-workflow.md` | related 2항목 정규화 | `:12-13` |
| M-4 | `opal/tools/brain-tool/tests/test_brain_tool.py` | validate 링크필드 RED 테스트 추가(R-3) | `TestValidateFrontmatter:1410` |
| M-5 | `opal/tools/brain-tool/brain_tool.py` | `validate_frontmatter` 링크필드 검사 + `LINK_FRONTMATTER` 상수 + @header `[053]`(R-2) | `:51`, `:294-301`, `:6` |
| M-6 | `opal/tools/brain-tool/tests/test_brain_tool.py` | add-page `--related` RED 테스트 + `make_args` 기본값 `related=None`(R-5) | `:56-88`, `TestAddPage:231` |
| M-7 | `opal/tools/brain-tool/brain_tool.py` | `--related` argparse + `cmd_add_page` CSV 평탄화(R-4) | `:501-504`, `:1192` |
| M-8 | `opal/core/references/tools.md` | validate 링크필드 검사 + add-page `--related` 설명(R-6) | `:479,485` |
| M-9 | `.opal/brain/pages/entity/brain-tool.md` | 인터페이스 절 링크필드 집행 기술(R-6) | `:40` |
| M-10 | `.opal/brain/pages/concept/brain-validate-flatness-enforcement.md` | 035 집행의 링크필드 확장 기술(R-6) | 전체 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | (없음) | 삭제 없음 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | R-1 페이지 3종 정규화 | M-1/M-2/M-3 | 하 |
| 2 | R-3 validate 링크필드 RED 테스트 | M-4 | 중 |
| 3 | R-2 validate 링크필드 검사 구현 | M-5 | 중 |
| 4 | R-5 add-page `--related` RED 테스트 | M-6 | 중 |
| 5 | R-4 `--related` 플래그 구현 | M-7 | 중 |
| 6 | R-6 문서 반영 + 전체 스위트 회귀 확인 | M-8/M-9/M-10 | 하 |

원칙: 정비(R-1)는 코드 무의존이라 선행 병렬 처리. 검증 강화는 D-2가 명시한 RED-first(테스트→FAIL→구현) 순서로, `brain_tool.py`·`test_brain_tool.py` 각각을 동일 파일 순차 편집으로 진행.

### 핵심 설계

> 인라인 인용 규정: `opal/core/references/harness/citation-rules.md` §2.

**[MUST]** `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, ...)에서 수행한다." — 모든 코드 변경 대상은 `opal/tools/brain-tool/brain_tool.py`(프로젝트 소스)이며 `~/.opal/tools/brain-tool/`이 아니다. 브레인 페이지 정비 대상은 프로젝트 자산 `.opal/brain/pages/`이다(배포본 아님).

**[MUST]** `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm`(KST), ... 변경내용은 태스크 번호를 괄호로 포함." — R-6 문서(tools.md·brain-tool entity 페이지·D-2 페이지) 및 brain_tool.py @header에 `(053)`/`[053]` 이력 반영.

**[MUST]** `docs/CONVENTIONS.md` §언어 규칙: "파일/폴더 이름 English, kebab-case (Python 파일은 snake_case)"; "코드/변수/필드명 English" — 신규 상수·플래그명은 영어(`LINK_FRONTMATTER`, `--related`).

**[MUST]** `.opal/AGENT.md` §금지사항 / CONVENTIONS §State: "STATE.md 마크다운 직접 편집 금지 — state-tool만 사용." — 본 PLAN에는 STATE 편집 Step을 포함하지 않는다(PM이 state-tool로 수행).

#### M-5: `validate_frontmatter` 링크필드 검사 (R-2 — 최우선 enforce)

- 상수 추가: `OPTIONAL_FRONTMATTER`(`:51`) 바로 아래 `LINK_FRONTMATTER = ["related"]` 신설. **범위를 `related`로 한정** — `sources`는 `task:045`·`code:x`·`POL-1`·`ia:...` 등 링크 토큰을 정당하게 담으므로 `.md`/`[[]]` 거부 대상에서 제외. R-2 AC가 "related 요소"로 명시(TASK.md R-2)한 것과 일치.
- 검사 삽입 위치: 035 평탄성 루프(`:294-299`) 다음, `return issues`(`:301`) 직전. 035 루프가 먼저 비-문자열/비-리스트를 걸러내므로, 링크필드 루프는 `isinstance(x, str)` 가드 후 토큰만 검사(중복·오탐 방지).
- 검사 규칙: `related` 각 요소 문자열이 `"[["` 포함 · `"]]"` 포함 · `.endswith(".md")` 중 하나라도 참이면 issue 추가. issue 문자열 예: `f"{key} must be a plain page slug (no '[[', ']]', or '.md'): {x}"`.
- 통과 유지: `None`(부재)·빈 리스트·정상 슬러그(`state-tool`)는 issue 미발생 → 기존 동작 불변. (→ D-2 §통과 조건: 부재·빈 리스트 자동 통과)
- 반환 계약·시그니처 불변 — issue 문자열을 append만 함. `cmd_validate`·`cmd_add_page:507-509`가 이 issues로 `frontmatter_invalid` violation을 자동 표면화.
- @header(`:6`) description 끝에 `[053] validate_frontmatter 링크필드(related) 값 검사 추가 — '[[', ']]', '.md' 포함 슬러그를 frontmatter_invalid로 집행; add-page에 --related(CSV→평탄 리스트) 플래그 추가.` 인라인 이력 추가 (035 표기 방식 준용, → D-1:6).

#### M-7: `--related` 플래그 (R-4 — 손편집 유인 감소)

- argparse: `p_add.add_argument("--sources")`(`:1192`) 다음 `p_add.add_argument("--related")` 추가(D-1:1192). help 문자열 병기(예: `"관련 페이지 슬러그 CSV (예: state-tool,brain-tool)"`).
- `cmd_add_page`: tags/sources 평탄화 블록(`:501-504`) 다음에 동일 패턴으로
  `if args.related: fm_tpl["related"] = [r.strip() for r in args.related.split(",") if r.strip()]` 추가.
- 순서상 이 값은 이후 `validate_frontmatter`(`:507`)를 통과해야 하므로, `--related`에 `[[x]]`/`x.md`를 넣으면 M-5 검사가 즉시 거부 — 도구가 손편집 유인을 원천 차단(enforce 일관).
- 미지정 시 `args.related` falsy → 템플릿 기본값 유지(AC: 기존 동작 불변).

#### M-4 / M-6: 테스트 (R-3 / R-5 — mock 금지, 실제 import 호출)

- M-4(R-3, `TestValidateFrontmatter:1410`에 메서드 추가):
  - 거부 케이스: `related=["[[state-tool]]"]` → `"must be a plain page slug"` issue 포함; `related=["state-tool.md"]` → issue 포함; `related=["a]]"]`/`related=["[[a"]]` 부분 토큰도 검출.
  - 통과 케이스: `related=["state-tool","brain-tool"]` → 링크필드 issue 0; `related=None`·`related=[]` → issue 0.
  - RED 확인: 구현(M-5) 전 실행 시 거부 케이스가 FAIL(현재 통과)해야 한다 — D-2 §RED-first.
- M-6(R-5, `TestAddPage:231` 계열 + `_add_page` 헬퍼 확장):
  - `make_args` 기본값(`:56-88`)에 `"related": None` 추가(미추가 시 AttributeError). `_add_page` 헬퍼(`:130-140`)에 `related=None` 파라미터 추가하여 args에 전달.
  - `--related a,b` 지정 → 생성 페이지 frontmatter `related: [a, b]` 평탄 리스트 검증(파일 재파싱).
  - 미지정 → 템플릿 기본값 유지(기존 `test_add_page_frontmatter_valid` 회귀 확인).
  - RED 확인: 구현(M-7) 전 `related` 미인식으로 FAIL/에러.

#### M-8 / M-9 / M-10: 문서 반영 (R-6)

- M-8 `tools.md`: validate 라인(`:485`) 설명에 "링크필드(related) `[[]]`/`.md` 거부" 추가, add-page 라인(`:479`) 또는 인접에 `--related` 언급. 변경이력 행 `(053)` 추가(문서에 변경이력 표 있으면).
- M-9 `brain-tool.md` entity 인터페이스 절(`:40` 인접): "링크필드(related) 검사 — 요소가 `[[`/`]]`/`.md`를 포함하면 `frontmatter_invalid`로 거부(`brain_tool.py`)" 1줄 추가. 비즈니스 용어 우선(citation-rules §8) — 코드 식별자는 근거 괄호로 병기.
- M-10 `brain-validate-flatness-enforcement.md`(D-2): 035 평탄성 집행이 quoted `[[]]`를 못 잡던 사각지대를 053 링크필드 검사가 닫았음을 "유사 계열"/"영향 범위"에 추가 기술. concept 페이지 본문은 자연어 서술(citation-rules §8.1).

## 3. 실행 체크리스트

> 총 9개 Step | Phase 4개
> (2026-07-10 13:05 PM Gate: R-K1 승인에 따라 Step 3-b 추가 — AGENTIC-LOG #3)

> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1, 2, 3, 3-b | 병렬 | R-1 페이지 정규화 — 독립 파일 |
> | 2 | 4, 5 | 순차 | validate RED(테스트 파일)→구현(brain_tool.py), RED-first |
> | 3 | 6, 7 | 순차 | add-page RED(테스트 파일)→구현(brain_tool.py), RED-first |
> | 4 | 8 | 순차 | R-6 문서 + 전체 스위트 회귀 확인 |

### Step 1: memory-tool.md related 정규화 (R-1)
- [x] 완료
- **파일**: `.opal/brain/pages/entity/memory-tool.md`
- **작업 내용**: related 리스트(`:11-13`)를 `"[[state-tool]]"`→`state-tool`, `"[[three-layer-memory-architecture]]"`→`three-layer-memory-architecture`로 평탄 슬러그화(따옴표·`[[`·`]]` 제거). 본문 링크(`:51-52`)는 손대지 않는다(별건 broken_link 제외 — TASK §범위).
- **완료 기준**: 파일 related에 `[[`/`]]`/`.md` 미포함, 두 슬러그가 실제 페이지 파일명과 일치
- **테스트**: `grep -n "\[\[" ` 해당 related 구간 0건; `yaml.safe_load`로 flat `list[str]` 파싱 확인
- **의존**: 없음
- **agent**: opal-task-agent

### Step 2: fixture-vs-real-blind-spot-lesson.md related 정규화 (R-1)
- [x] 완료
- **파일**: `.opal/brain/pages/concept/fixture-vs-real-blind-spot-lesson.md`
- **작업 내용**: related(`:14-15`)를 `memory-tool`, `agentic-output-direct-verification-lesson`로 평탄 슬러그화.
- **완료 기준**: related에 `[[`/`]]`/`.md` 미포함, 슬러그가 실제 페이지와 일치
- **테스트**: 해당 related 구간 `[[` grep 0건
- **의존**: 없음
- **agent**: opal-task-agent

### Step 3: memory-lifecycle-graduation-workflow.md related 정규화 (R-1)
- [x] 완료
- **파일**: `.opal/brain/pages/concept/memory-lifecycle-graduation-workflow.md`
- **작업 내용**: related(`:12-13`)를 `memory-tool`, `three-layer-memory-architecture`로 평탄 슬러그화.
- **완료 기준**: related에 `[[`/`]]`/`.md` 미포함, 슬러그가 실제 페이지와 일치
- **테스트**: 해당 related 구간 `[[` grep 0건
- **의존**: 없음
- **agent**: opal-task-agent

### Step 3-b: skill-opal-pilot-data-design.md related 정규화 (R-1 확장 — R-K1 승인분)
- [x] 완료
- **파일**: `.opal/brain/pages/entity/skill-opal-pilot-data-design.md`
- **작업 내용**: related(`:6`)의 `.md` 접미사 4항목을 `op-data-dictionary-skill`, `op-data-model-skill`, `op-data-ddl-skill`, `opdd-pipeline-flow`로 정규화(`.md` 제거). 대상 페이지 실재 확인 완료(entity 3건 + flow 1건 — PM Gate 실측).
- **완료 기준**: related에 `[[`/`]]`/`.md` 미포함, 4개 슬러그가 실제 페이지 파일명과 일치
- **테스트**: 해당 related 구간 `.md` grep 0건; `yaml.safe_load` flat `list[str]` 파싱 확인
- **의존**: 없음
- **agent**: opal-task-agent

### Step 4: validate 링크필드 RED 테스트 (R-3)
- [x] 완료
- **파일**: `opal/tools/brain-tool/tests/test_brain_tool.py`
- **작업 내용**: `TestValidateFrontmatter`(`:1410`)에 링크필드 거부/통과 케이스 메서드 추가 — 거부(`related=["[[state-tool]]"]`, `["state-tool.md"]`), 통과(`related=["state-tool"]`, `None`, `[]`). §2 M-4 명세 준수.
- **완료 기준**: 구현(Step 5) 전 실행 시 거부 케이스가 FAIL(현재 통과 = RED 증거 확보), 통과 케이스는 PASS
- **테스트**: `run.sh` pytest로 신규 테스트만 실행 → 거부 케이스 FAIL 로그 확보
- **의존**: 없음 (단, 동일 파일 Step 6과 순차)
- **agent**: opal-task-agent

### Step 5: validate_frontmatter 링크필드 검사 구현 (R-2)
- [x] 완료
- **파일**: `opal/tools/brain-tool/brain_tool.py`
- **작업 내용**: `LINK_FRONTMATTER = ["related"]` 상수 추가(`:51` 인접), `validate_frontmatter`의 035 루프 다음·`return issues` 직전(`:294-301`)에 링크필드 토큰 검사 추가, @header(`:6`) `[053]` 이력 추가. §2 M-5 명세 준수.
- **완료 기준**: Step 4 거부 케이스 GREEN, 통과 케이스 GREEN, 기존 `TestValidateFrontmatter`·`TestValidateFlatness035` 회귀 0
- **테스트**: pytest `TestValidateFrontmatter` 전체 GREEN
- **의존**: Step 4 (RED 증거 선행)
- **agent**: opal-task-agent

### Step 6: add-page `--related` RED 테스트 (R-5)
- [x] 완료
- **파일**: `opal/tools/brain-tool/tests/test_brain_tool.py`
- **작업 내용**: `make_args` 기본값(`:56-88`)에 `"related": None` 추가, `_add_page` 헬퍼(`:130-140`)에 `related` 파라미터 추가, `TestAddPage`(`:231`)에 `--related` 지정/미지정 케이스 추가. §2 M-6 명세 준수.
- **완료 기준**: 구현(Step 7) 전 실행 시 `--related` 지정 케이스 FAIL/에러(RED), 기존 add-page 테스트 회귀 0
- **테스트**: pytest 신규 add-page 케이스 RED 로그 확보
- **의존**: Step 4 (동일 테스트 파일 순차 편집)
- **agent**: opal-task-agent

### Step 7: `--related` 플래그 구현 (R-4)
- [x] 완료
- **파일**: `opal/tools/brain-tool/brain_tool.py`
- **작업 내용**: `p_add`에 `--related` argparse 추가(`:1192` 인접), `cmd_add_page`에 CSV 평탄화 블록 추가(`:501-504` 인접). §2 M-7 명세 준수.
- **완료 기준**: Step 6 `--related` 케이스 GREEN(frontmatter `related: [a, b]`), 미지정 케이스 GREEN(기본값 유지)
- **테스트**: pytest `TestAddPage` 전체 GREEN
- **의존**: Step 5 (동일 소스 파일 순차 편집), Step 6 (RED 증거)
- **agent**: opal-task-agent

### Step 8: 문서 반영 + 전체 스위트 회귀 확인 (R-6)
- [x] 완료
- **파일**: `opal/core/references/tools.md`, `.opal/brain/pages/entity/brain-tool.md`, `.opal/brain/pages/concept/brain-validate-flatness-enforcement.md`
- **작업 내용**: §2 M-8/M-9/M-10 명세대로 링크필드 검사·`--related` 설명 및 변경이력 `(053)` 반영. 이어 brain-tool 전체 pytest 스위트 실행하여 회귀 0 확인, `grep -rn "\[\[" ` (정비 3페이지 related 구간) 0건 확인.
- **완료 기준**: 3개 문서 갱신 완료(변경이력 포함), 전체 스위트 GREEN(회귀 0), 완료기준 (a)~(e) 충족
- **테스트**: `run.sh` pytest 전체; 완료기준 grep/validate/lint 수동 확인
- **의존**: Step 3, Step 3-b, Step 5, Step 7
- **agent**: opal-task-agent

## 4. QA 체크리스트

### 기능 테스트
- [x] R-1: 3페이지 related에 `[[`/`]]`/`.md` 미포함, 슬러그가 실제 페이지와 일치 (완료기준 a)
- [x] R-1: 정규화 후 `lint`의 해당 6 missing_link 소거 (완료기준 b)
- [x] R-2: 강화된 `validate_frontmatter`가 `[[x]]`/`x.md` related 값을 `frontmatter_invalid`로 거부 (완료기준 c)
- [x] R-2: `None`·`[]`·정상 슬러그는 통과(기존 동작 불변)
- [x] R-3: 링크필드 거부·통과 케이스 신규 테스트 GREEN
- [x] R-4: `add-page --related a,b` → frontmatter `related: [a, b]` 평탄 리스트, 미지정 시 기본값 유지 (완료기준 d)
- [x] R-5: `--related` 지정/미지정 케이스 신규 테스트 GREEN
- [x] R-6: tools.md·brain-tool entity·D-2 페이지에 링크필드 검사·`--related` 설명 반영

### 일관성 테스트
- [x] 기존 brain-tool 테스트 스위트 전체 GREEN(회귀 0) (완료기준 e) — 118 passed
- [x] `validate_frontmatter` 시그니처·반환 계약 불변 (필수 5필드·type·status·035 평탄성 훼손 없음)
- [x] RED-first 준수 — 구현 전 거부 케이스 FAIL 로그 확보 (→ D-2 §RED-first)
- [x] 링크필드 검사 범위가 `related`로 한정되어 `sources` 토큰(`task:`·`code:`·`ia:`)을 오탐하지 않음
- [x] 변경 대상이 프로젝트 소스(`opal/tools/brain-tool/`)이며 `~/.opal/` 배포본 직접 편집 없음

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명(`LINK_FRONTMATTER`, `--related`) 규칙 준수
- [x] 변경이력 표/@header에 `(053)`/`[053]` 및 KST 일시 반영
- [x] brain concept/entity 페이지 본문이 비즈니스 용어 우선(citation-rules §8) — 코드 식별자 근거 병기
- [x] YAML frontmatter가 flat `list[str]`로 올바르게 파싱됨

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R-K1 | **[decision_required·scope_gap]** 링크필드 `.md` 거부 규칙이 실 저장소 `skill-opal-pilot-data-design.md`의 related(`.md` 접미사 4항목, `:6`)를 신규 `frontmatter_invalid`로 표면화. TASK §범위는 3페이지/6항목만 포함하고 `.md` 접미사 정비를 "별건"으로 제외했으나, 그 제외는 **본문 위키링크** 대상이고 이 건은 **related 프론트매터** `.md`라 R-2 enforce와 직접 충돌 | 강화 배포 후 실 brain `validate`가 이 페이지를 violation으로 보고(현재 valid:true) → 실 저장소 무결성 저하 | **권고**: R-1 정규화에 이 4항목도 포함(`op-data-dictionary-skill`·`op-data-model-skill`·`op-data-ddl-skill`·`opdd-pipeline-flow` — 모두 실제 페이지 존재 확인). 소규모·enforce 의도와 정합. **단, TASK 명시 범위 밖이므로 PM/캡틴 승인 필요** — ✅ 2026-07-10 13:05 PM agentic DECISION 승인(AGENTIC-LOG #3) → Step 3-b 추가 완료 |
| R-K2 | 링크필드 검사 범위 과확장(`sources`까지 포함) 시 `task:045`·`code:x`·`ia:...` 정당 토큰 오탐 → 광범위 회귀 | 다수 기존 페이지 validate 실패 | `LINK_FRONTMATTER=["related"]`로 범위 한정(§2 M-5). `sources`·`tags` 미포함 확정 |
| R-K3 | 정규화 슬러그가 실제 파일명과 불일치 시 broken_link 유발 | lint 오류 | 6항목 슬러그 4종 전부 실제 페이지 존재 사전 확인 완료(§1 현재 상태). Step 완료 기준에 슬러그-파일명 일치 검증 포함 |
| R-K4 | `make_args` 기본값 미갱신 시 `--related` 도입 후 기존 add-page 테스트 AttributeError | 기존 테스트 회귀 | Step 6에서 `make_args`에 `related: None` 선반영, 미지정 케이스로 회귀 검증 |
| R-K5 | RED-first 생략 시 검증 로직 self-confirming(구현이 테스트를 부당 통과시킴) | 결함 잠복 | Step 4·6을 구현 Step 전에 배치, 구현 전 FAIL 로그 확보 의무화(→ D-2 §RED-first) |
| R-K6 | tools.md `커맨드 (8 서브명령)` 표기(`:475`)가 실제 10 서브명령과 불일치(@header `:6` 기준) | 문서 정확도 | TASK 범위 밖(별건). R-6 편집 중 발견 시 결과 보고에 기록만, 본 태스크에서 수정하지 않음(surgical) |
