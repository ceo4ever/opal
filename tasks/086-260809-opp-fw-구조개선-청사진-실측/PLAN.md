# PLAN: OPAL FW 구조개선 청사진 정식화 + 잔여 실측 (P0)

> 작성일: 2026-08-09
> 입력: TASK.md
> 출력: PLAN.md
> 작업 성격: **읽기 전용 실측 + 문서화** — 산출물은 본 태스크 폴더 내 md 5개뿐

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | pipeline-spec 스키마 | `opal/tools/state-tool/schema/pipeline-spec.schema.json` | AC-2 표현 가능성 판정 기준 (49줄 전문 확인) |
| D-2 | 설계 | pilot pipeline.json 4종 | `opal/skills/opal-pilot-{project,dev,dev-short,dev-wireframe}/references/pipeline.json` | AC-1 대조 원본 / AC-2 표현형 레퍼런스 |
| D-3 | 기획 | 프로젝트 정의 | `docs/PROJECT.md` | 컴포넌트 인벤토리 SSOT (§주요 컴포넌트 6절) |
| D-4 | 외부 | Opus 5 프롬프팅 가이드 | [platform.claude.com](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5) | P-5 진단·P1 정합 근거 |
| D-5 | 설계 | 하네스 SSOT | `opal/core/references/opal-harness.md` | AC-4 로드 사슬 기점 (330줄, §참조 문서 테이블 100-113) |
| D-6 | 설계 | 코드 컨벤션 | `docs/CONVENTIONS.md` | 태스크 산출물 구조·Guards·배포 경계 규율 |
| D-7 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | 산출물 근거 인용 포맷 (§2 / §3.1) |
| D-8 | 소스 | 태스크 state.json 27건 | `tasks/*/state.json` | AC-3 스폰 수 집계 원천 (실측 결과: 워커 식별 필드 부재) |
| D-9 | 설계 | pilot SKILL.md 10종 | `opal/skills/opal-pilot-*/SKILL.md` | AC-1 태깅 대상 / AC-2 추출 대상 |

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/skills/opal-pilot-project/SKILL.md` | opp 오케스트레이터 (274줄) | ❌ 읽기 전용 | 헤딩 18개 (`:11`~`:244`) |
| `opal/skills/opal-pilot-dev/SKILL.md` | opd 오케스트레이터 (416줄) | ❌ 읽기 전용 | - |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | opds 오케스트레이터 (383줄) | ❌ 읽기 전용 | 헤딩 24개 (`:12`~`:345`) |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | opdw 오케스트레이터 (302줄) | ❌ 읽기 전용 | - |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | oppd (818줄, 최대) | ❌ 읽기 전용 | - |
| `opal/skills/opal-pilot-project-loop/SKILL.md` | oppl (604줄) | ❌ 읽기 전용 | - |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | opwt (559줄) | ❌ 읽기 전용 | - |
| `opal/skills/opal-pilot-sdd/SKILL.md` | opsdd (544줄) | ❌ 읽기 전용 | - |
| `opal/skills/opal-pilot-gc/SKILL.md` | opgc (540줄) | ❌ 읽기 전용 | - |
| `opal/skills/opal-pilot-data-design/SKILL.md` | opdd (323줄) | ❌ 읽기 전용 | - |
| `opal/tools/state-tool/schema/pipeline-spec.schema.json` | 스키마 SSOT (49줄) | ❌ 읽기 전용 | `:10` skill enum 10종 / `:28` key 패턴 / `:24,:35` additionalProperties:false |
| `opal/core/references/opal-harness.md` | 공통 하네스 (330줄) | ❌ 읽기 전용 | `:100-113` 참조 문서 테이블 13행 |
| `opal/core/references/harness/*.md` | 조건부 로드 참조 17종 | ❌ 읽기 전용 | 86~426줄, 합계 실측 대상 |
| `tasks/*/state.json` (27건) | AC-3 원천 | ❌ 읽기 전용 | owner 값 3종만 (PM 255 / auto 69 / user 40) |
| `tasks/086-*/analysis/A1~A4.md` | 실측 부록 | ✅ 신규 생성 | TASK.md AC-1~AC-4 |
| `tasks/086-*/BLUEPRINT.md` | 청사진 SSOT | ✅ 신규 생성 | TASK.md AC-5 |

### 현재 상태 (실측)

**S-1. pilot 인벤토리 — 10종, pipeline.json 보유 4 / 미보유 6 (TASK.md 전제와 일치)**

| pilot 디렉토리 | alias | SKILL.md 줄수 | pipeline.json | stages | task_steps | pm_gate |
|---------------|-------|-------------|--------------|--------|-----------|---------|
| `opal-pilot-project` | opp | 274 | ✅ | 4 | 9 | 2 |
| `opal-pilot-dev-wireframe` | opdw | 302 | ✅ | 4 | 9 | 2 |
| `opal-pilot-dev-short` | opds | 383 | ✅ | 5 | 11 | 2 |
| `opal-pilot-dev` | opd | 416 | ✅ | 7 | 16 | 4 |
| `opal-pilot-data-design` | opdd | 323 | ❌ | - | - | - |
| `opal-pilot-gc` | opgc | 540 | ❌ | - | - | - |
| `opal-pilot-sdd` | opsdd | 544 | ❌ | - | - | - |
| `opal-pilot-write-tech` | opwt | 559 | ❌ | - | - | - |
| `opal-pilot-project-loop` | oppl | 604 | ❌ | - | - | - |
| `opal-pilot-project-dev` | oppd | 818 | ❌ | - | - | - |
| **합계** | | **4,763** | 4/10 | | | |

> 관측: **미보유 6 pilot이 보유 4 pilot보다 평균 SKILL.md가 길다** (미보유 평균 565줄 vs 보유 평균 344줄). 즉 데이터 주도 전환의 미적용 영역이 곧 산문 부피가 큰 영역이다 — AC-2·AC-5의 핵심 논거 후보.

**S-2. 스키마 표현력 경계 (D-1 실측)**

- `skill` enum이 이미 10종 전부 등재 — `opal/tools/state-tool/schema/pipeline-spec.schema.json:10` (`opp,opd,opds,opdw,opwt,opgc,oppd,opsdd,oppl,opdd`). **스키마는 6 pilot을 받아들일 의도로 이미 열려 있다.**
- 최상위·`meta`·`task_steps.items`·`pm_gate.items` 4개소 전부 `additionalProperties: false` (`:7,:14,:25,:40`) → **신규 키는 전부 스키마 개정 필요**. AC-2 판정의 1차 축.
- `task_steps.items`가 가진 표현 수단은 `id`/`key`/`stage`/`item`/`conditional` 5개뿐 (`:26-32`). 반복·분기·동적 행 수를 나타낼 필드가 없다 → oppd/opsdd의 Phase 루프(액션 N개 반복) 표현 가능성이 AC-2의 최대 쟁점.
- `key` 패턴 `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*(_[0-9]+)?$` (`:28`) — `stage.item` 2단 + 선택적 `_N` 접미. 3단 이상 계층(예: `phase3.act2.plan`) 표현 불가.

**S-3. AC-3 원천 데이터의 한계 (중대 발견)**

- `tasks/*/state.json` 27건의 `owner` 필드 값은 **`PM`(255) / `auto`(69) / `user`(40) 3종뿐** — 워커 에이전트 식별자가 기록되지 않는다.
- STATE.md 파이프라인 표에도 디스패치 주체·횟수 컬럼이 없다 (`tasks/085-.../STATE.md` 파이프라인 현황판 컬럼: `#`/단계/항목/상태/시점).
- ⇒ **"태스크당 디스패치 횟수"를 STATE.md/state.json에서 직접 집계할 수 없다.** AC-3은 대리 지표(proxy) 설계가 필수다. → §2 핵심 설계 A3에서 3계층 대리 지표를 정의한다.

**S-4. 태스크 표본 가용성**

| 항목 | 실측값 |
|------|--------|
| 태스크 디렉토리 | 28 (`tasks/backup/` 제외 시 27) |
| `state.json` 보유 | 27 |
| skill 분포 | opd 15 / opds 10 / opp 2 |
| `PLAN.md` 보유 | 26 |
| `ANALYSIS.md` 보유 | 15 |
| `TEST-SCENARIO.md` 보유 | 25 |
| `DONE.md` 보유 | 26 |
| `TEST.md` 보유 | **2** |

> AC-3 표본 요건("opd·opds 최소 10건")은 충족 가능(25건 후보). 단 `TEST.md`는 2건뿐이므로 **집계 근거로 사용 금지** — PLAN.md/ANALYSIS.md/DONE.md 3종으로 한정한다.

**S-5. 로드 사슬 구조 (AC-4 기점)**

- `opal/core/references/opal-harness.md:100-113` 조건부 참조 테이블 13행 — 각 행이 "로드 시점" 조건을 명시(예: Observability = "워커 디스패치 직전(매 디스패치마다)", 인용 규칙 = "TASK/ANALYSIS/PLAN 산출물 작성 시").
- `harness/` 실제 파일은 **17종**(`additional-work, citation-rules, coding-principles, doc-code-mismatch, header-rules, memory-learning, observability, parallel-execution, pm-improvement-loop, pm-review-gate, qa-standards, red-first, scenario-gate, skill-commands, state-template, state, task-process`) — 테이블 13행과 **4종 차이**. 즉 테이블에 등재되지 않은 채 다른 경로로 로드되는 문서가 존재한다 → AC-4 홉 분석의 주요 타깃.
- 모드 서브 하네스 3종은 배타 1택 로드 (`opal-harness.md:86-92`) — 정적 합산 시 3벌 전부 더하면 과대계상. AC-4 보정의 핵심 항목.
- `harness/` 파일 크기 실측: 최소 86줄(`red-first.md`) ~ 최대 426줄(`citation-rules.md`), 17종 합계는 A4에서 확정.

**S-6. pilot SKILL.md 섹션 구조 (AC-1 태깅 단위 근거)**

`opal-pilot-project`(18 헤딩) / `opal-pilot-dev-short`(24 헤딩) 실측 결과, 4 pilot이 공통 골격을 공유한다:

`Harness` → `STEP 1..N` (단계별, 하위에 `디스패치`/`완료 후` 서브섹션) → `STATE.md 도메인 치환값` → `PM Gate 점검 목록` → `Agentic / Semi-Agentic 모드` → `변경이력`

⇒ **헤딩 블록이 곧 태깅 단위**로 성립한다. AC-1은 헤딩 블록 단위 3분류로 설계 가능하다.

### 영향 범위

- **FW 소스 영향: 없음.** 본 태스크는 읽기 전용이며 `opal/`·`skills/`·`agents/`·`~/.opal/` 어느 것도 수정하지 않는다.
- **산출물 영향**: `tasks/086-260809-opp-fw-구조개선-청사진-실측/` 하위 5개 md 신규 생성.
- **후속 태스크 영향**: BLUEPRINT.md가 P1~P3 태스크의 참조 SSOT가 되므로, 여기서 확정한 절단선·수치가 후속 3개 태스크의 범위를 결정한다.

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | `tasks/086-.../analysis/A1-중복률.md` | pipeline.json↔SKILL.md WHAT/ENFORCE/WHY 3분류 비율표 | TASK.md AC-1 |
| N-2 | `tasks/086-.../analysis/A2-스키마소요.md` | 미보유 6 pilot 스키마 표현 가능/확장 필요 2분류표 | TASK.md AC-2 |
| N-3 | `tasks/086-.../analysis/A3-스폰실측.md` | 태스크당 디스패치 수 대리 지표 집계 (K4 기준선) | TASK.md AC-3 |
| N-4 | `tasks/086-.../analysis/A4-로드사슬.md` | 로드 사슬 실효값 + 홉 깊이 Top5 (K3 보정) | TASK.md AC-4 |
| N-5 | `tasks/086-.../BLUEPRINT.md` | AS-IS→TO-BE 청사진 SSOT (6개 구성요소) | TASK.md AC-5 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| - | 없음 | 읽기 전용 태스크 | TASK.md §제약 조건 |

> [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다."
> [MUST] `docs/CONVENTIONS.md` §Guards: "커밋은 사용자가 명시적으로 요청할 때만 수행한다 — EXECUTE 완료·DONE.md 생성·테스트 통과 후에도 자동 커밋 금지."
> [MUST] TASK.md §제약 조건: "읽기 전용: FW 소스·전역 배포본 수정 금지 (산출물은 태스크 폴더 내 md만)"

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | 없음 | - |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | A1 중복률 실측 | `analysis/A1-중복률.md` | 상 (분류 판정 4×20 블록) |
| 2 | A2 스키마 소요 도출 | `analysis/A2-스키마소요.md` | 상 (6 pilot × 3,388줄 구조 추출) |
| 3 | A3 스폰 수 실측 | `analysis/A3-스폰실측.md` | 중 (대리 지표 설계 + 25건 집계) |
| 4 | A4 로드 사슬 보정 | `analysis/A4-로드사슬.md` | 중 (조건 판정 + 홉 추적) |
| 5 | BLUEPRINT 전반부 (§1~§4) | `BLUEPRINT.md` | 중 (기존 진단 정식화) |
| 6 | BLUEPRINT 후반부 (§5~§6) | `BLUEPRINT.md` | 상 (A1~A4 결론 통합 + P1~P3 범위) |

> 1~4는 서로 독립(다른 파일, 공유 입력 없음) → 병렬. 5~6은 동일 파일 → 반드시 순차. 5~6은 1~4 전부에 의존.

### 핵심 설계

#### 공통 규율 (모든 산출물에 적용)

**C-1. 실측/추정 구분 표기 [MUST]**

> [MUST] TASK.md §제약 조건: "실측 우선: 추정치는 '추정'으로 명시하고 실측값과 구분"

모든 수치 셀에 신뢰도 마커를 접두한다. 마커 없는 수치는 부적합 처리한다.

| 마커 | 의미 | 사용 조건 |
|------|------|----------|
| `[M]` | 실측 (Measured) | 파일을 직접 읽거나 Bash 집계로 산출. 근거 인용 필수 |
| `[D]` | 파생 (Derived) | `[M]` 값들의 산술 연산 결과. 계산식 병기 필수 |
| `[E]` | 추정 (Estimated) | 원천 데이터 부재로 판단이 개입한 값. **추정 근거 문장 필수** |

각 산출물 최상단에 마커 범례를 고정 배치하고, 문서 말미에 `[E]` 항목만 모은 "추정 항목 일람" 표를 둔다 — 후속 P1~P3에서 무엇이 아직 근거 미확정인지 한눈에 보이게 한다.

**C-2. 근거 인용 [MUST]**

> [MUST] `opal/core/references/harness/citation-rules.md` §0: "상상·추정·기억 기반 기재 금지 — 모든 분석·설계 결정은 문서 근거(경로/URL + 섹션/줄번호)를 인용해야 한다."

- 코드/JSON 근거: `` `경로:줄번호` `` (→ D-7 §2.2)
- 문서 근거: `` `경로` §N `` (→ D-7 §2.1)
- 각 산출물 최상단에 §0 참조 문서 테이블(공통 컬럼 스키마 `# / 유형 / 문서·사이트 / 경로·URL / 참조 이유`)을 둔다 (→ D-7 §3.1).

**C-3. 집계 스크립트 격리 [MUST]**

Bash/Python 집계가 필요한 경우 스크립트는 **스크래치패드에만** 작성하고, 태스크 폴더·FW 소스에 남기지 않는다. 산출물에는 **재현 가능한 명령문(한 줄)만** 코드블록으로 기재한다 — 검증자가 동일 명령으로 재현할 수 있어야 한다.

**C-4. 산출량 상한**

각 A1~A4는 단일 md 1파일. 표 중심으로 작성하고 서술은 표 해석·결론에 한정한다. 원자료(raw) 덤프는 문서 말미 부록으로 접어 넣되, 부록이 본문보다 길어지면 상위 집계만 남기고 절단한다.

---

#### N-1. `analysis/A1-중복률.md` — 중복률 실측

**측정 단위**: SKILL.md의 **헤딩 블록**(`##`/`###`). 블록 줄수 = 헤딩 줄 ~ 다음 동급/상위 헤딩 직전 줄. 근거: 4 pilot이 공통 헤딩 골격을 공유함이 실측됨 (`opal/skills/opal-pilot-project/SKILL.md:11-244`, `opal/skills/opal-pilot-dev-short/SKILL.md:12-345`).

**분모 정의**: 총 줄수에서 **YAML frontmatter**와 **`## 변경이력` 블록**을 제외한 줄수를 분모로 한다. 변경이력은 파이프라인 정의와 무관한 이력 축적분이므로 포함 시 중복률이 체계적으로 과소평가된다. 분모 산정식을 문서에 명시한다.

**3분류 판정 기준** (블록 1개 = 1분류, 배타 할당):

| 분류 | 정의 | 판정 신호 | TO-BE 귀속 |
|------|------|----------|-----------|
| **WHAT** | 단계·순서·산출물·게이트 항목의 *열거* — pipeline.json이 이미 보유하거나 보유 가능한 정보 | STEP 헤딩의 단계명/순서, STATE.md 행 항목 열거, PM Gate 점검 목록, 산출물 파일명 열거 | pipeline.json (데이터) |
| **ENFORCE** | 기계가 집행 가능한 절차 — 도구 호출·검증 명령·상태 전이 | `state-tool run.sh` 호출, 도구 exit code 판정, 파일 존재 검사, 루핑 횟수 상한 | 도구 (state/test/backlog-tool) |
| **WHY** | 판단이 필요한 서술 — 기준·예외·에스컬레이션·트레이드오프 | 에스컬레이션 조건, 모드별 자율 판단 기준, "~인 경우 ~로 판단한다" 형태 | 경량 발동층 (산문 잔존) |

**경계 규칙 (판정 재현성 확보)**:
1. 한 블록에 2개 이상 성격이 섞이면 **줄수 기준 과반**으로 배타 할당하고, 혼재 사실을 `혼재` 컬럼에 `Y`로 표기한다.
2. 블록이 30줄을 초과하고 혼재하면 `###` 하위 블록으로 내려 재판정한다.
3. `## Harness` 블록은 로드 지시이므로 **ENFORCE**로 고정 분류한다 (판정 흔들림 방지).
4. 판정 불가 블록은 `WHY`로 보수 할당한다 — WHAT(제거 대상)을 과대 산정하지 않기 위한 안전 방향이다.

**대조 검증 (중복률의 실질 확인)**: WHAT 분류된 블록에 대해, 해당 내용이 실제로 pipeline.json에 **이미 존재하는지** 대조한다. `stages` / `task_steps[].stage,item,key` / `pm_gate[].stage,artifacts,checklist` 필드와 1:1 매칭 여부를 기록한다 (→ D-2). 결과를 2단으로 나눈다:
- **실중복(WHAT-D)**: pipeline.json에 동일 정보가 이미 있음 → **즉시 절단 가능**
- **잠재중복(WHAT-P)**: 데이터화 가능하나 현재 pipeline.json에 없음 → **P2 스키마/데이터 확장 대상**

이 분리가 A1의 최대 산출 가치다. 단순 비율만으로는 P2 범위를 결정할 수 없다.

**출력 구조**:
1. §0 참조 문서 / 마커 범례
2. §1 측정 방법 (단위·분모식·3분류 기준·경계 규칙)
3. §2 pilot별 분류표 4개 — 컬럼: `블록(헤딩)` / `줄범위` / `줄수` / `분류` / `혼재` / `pipeline.json 대응 필드` / `WHAT-D·P`
4. §3 요약 비율표 — 컬럼: `pilot` / `분모줄수[M]` / `WHAT[D]` / `ENFORCE[D]` / `WHY[D]` / `WHAT 비율[D]` / `WHAT-D 비율[D]`
5. §4 결론 — **P2 발동층 절단선 권고**(어느 블록군을 산문에서 제거하고 pipeline.json으로 이관할지) + 잔존 WHY 최소 골격 제안
6. §5 추정 항목 일람

**완료 판정 수치**: 4 pilot × 전 블록이 분류표에 1회씩 등장하고, 각 pilot의 `WHAT+ENFORCE+WHY 줄수 합 == 분모줄수`가 성립한다 (누락·중복 할당 검산).

---

#### N-2. `analysis/A2-스키마소요.md` — 스키마 확장 소요

**대상**: 미보유 6 pilot — oppd(818) / oppl(604) / opwt(559) / opsdd(544) / opgc(540) / opdd(323), 합계 3,388줄 (→ §1 S-1).

**추출 절차 (pilot 1종당)**:
1. `grep -n '^#\{1,4\} '`로 헤딩 인덱스 확보 → STEP/Phase 헤딩에서 **stages** 후보 추출
2. STEP 하위의 디스패치·산출물·게이트 서술 구간만 Read → **task_steps** 후보(`stage`/`item`) 추출
3. `PM Gate 점검 목록` 블록 Read → **pm_gate** 후보(`stage`/`artifacts`/`checklist`) 추출
4. 기존 4 pilot의 pipeline.json 표현형과 대조하여 가상 pipeline.json 골격을 구성 (→ D-2)

> [MUST] 입력 축소: 전체 통독 금지. grep으로 헤딩·키워드 위치를 특정한 뒤 해당 구간만 Read한다.

**판정 축 (스키마 대조, → D-1)**:

| 축 | 스키마 근거 | 판정 질문 |
|----|-----------|----------|
| A. skill enum | `:10` — 10종 전부 등재 | 신규 enum 값 필요? → **6종 모두 불필요(등재 완료)** [M] |
| B. 최상위 키 | `:6-8` required 4 + `additionalProperties:false` | 4키 외 최상위 키가 필요한가? |
| C. meta 표현력 | `:14-18` `mode_label`/`stages`만 | 모드 분기·조건부 파이프라인 표현 필요? |
| D. task_steps 필드 | `:26-32` `id/key/stage/item/conditional` 5개 | 반복·분기·동적 행 수 표현 필요? |
| E. key 패턴 | `:28` `stage.item(_N)?` 2단 | 3단 이상 계층 필요? |
| F. pm_gate 표현력 | `:38-46` `stage/artifacts/checklist` | 게이트 조건·루핑 상한 표현 필요? |

**2분류 판정**:
- **표현 가능(EXPRESSIBLE)**: 현행 스키마 필드만으로 pipeline.json 작성 가능. 근거로 **가상 task_steps 행 예시 2~3개**를 실제로 기재한다 (판정의 증명).
- **확장 필요(NEEDS-EXT)**: 표현 불가. **어느 축(A~F)에서 막히는지 + 필요한 최소 확장안 1개**를 반드시 명시한다. "확장 필요"만 적고 끝내면 P2 범위를 결정할 수 없다.

**예상 최대 쟁점 (조사 중 식별, 실측으로 확정할 것)**: oppd Phase 3 / opsdd Phase 4의 **액션 N개 자율 루프**는 행 수가 태스크마다 가변이다. 현행 `task_steps`는 정적 배열이고 `conditional: boolean` 하나뿐이므로(`:31`) 동적 행 수를 표현할 수단이 없다 → 축 D·E의 NEEDS-EXT 후보. 대응 액션 에이전트 존재를 근거로 확인한다(`opal-task-action-agent`, `opal-sdd-action-agent`).

**출력 구조**:
1. §0 참조 문서 / 마커 범례
2. §1 판정 방법 (추출 절차·6축 정의)
3. §2 pilot별 구조 추출표 6개 — 컬럼: `단계(stage)` / `항목(item)` / `key 후보` / `게이트 여부` / `근거 줄번호`
4. §3 2분류 판정표 — 컬럼: `pilot` / `판정` / `막히는 축` / `필요 확장안` / `근거`
5. §4 스키마 확장안 종합 — 축별로 묶어 **필요 변경 필드 목록 + 하위호환 영향**(기존 4 pilot의 pipeline.json이 그대로 유효한지) 판정
6. §5 P2 범위 권고 — 확장 없이 즉시 데이터화 가능한 pilot과 스키마 선행이 필요한 pilot을 분리
7. §6 추정 항목 일람

> [MUST] TASK.md §확정된 설계 방향: "불변 제약: 도구 게이트(state/test/backlog-tool) 제거 0건 / pilot alias 진입점 무중단 / 하위호환 기본값 규율" — §4 하위호환 영향 판정은 이 제약 위반 여부를 반드시 명시한다.

---

#### N-3. `analysis/A3-스폰실측.md` — 스폰 수 실측

**전제 (중대 제약, §1 S-3)**: `state.json`의 `owner` 필드는 `PM`/`auto`/`user` 3종뿐이며 **워커 에이전트 식별자를 기록하지 않는다**. STATE.md 파이프라인 표에도 디스패치 컬럼이 없다. 따라서 **직접 집계가 불가능**하며, 3계층 대리 지표로 재구성한다. 이 한계를 A3 §1 최상단에 명시한다.

**대리 지표 3계층**:

| 계층 | 지표 | 원천 | 마커 | 의미 |
|------|------|------|------|------|
| L1 | **정적 하한** — pipeline.json `task_steps` 중 워커 디스패치가 정의된 행 수 | `opal/skills/opal-pilot-*/references/pipeline.json` (→ D-2) | `[M]` | pilot별 최소 스폰 수 (재시도·분배 제외) |
| L2 | **실행 하한** — 태스크별 산출물 존재 + PLAN.md §실행 체크리스트 Step 수 | `tasks/*/PLAN.md`, `tasks/*/ANALYSIS.md` | `[M]` | EXECUTE 분배 디스패치 규모 포함 |
| L3 | **관측 보정** — DONE.md·STATE.md 의사결정 로그의 재시도·루핑·에스컬레이션 기록 | `tasks/*/DONE.md`, `tasks/*/STATE.md` §의사결정 로그 | `[E]` | 실패 재디스패치 가산분 |

**최종 K4 = L1 기반 + L2 분배 가산 + L3 보정**, 세 계층 값을 **모두 분리 표기**한다. 단일 합산 수치만 제시하지 않는다 — 후속 P1이 어느 계층을 줄일지 결정해야 하기 때문이다.

**표본 선정 [MUST]**:
- 대상: `PLAN.md` 보유 + `DONE.md` 보유 + skill ∈ {opd, opds} 인 완료 태스크. 최신순 정렬 후 **opd 최소 6건 + opds 최소 6건 = 12건 이상**(AC-3 요구 10건 상회).
- `TEST.md`는 27건 중 2건뿐(§1 S-4)이므로 **집계 근거에서 제외**한다.
- 표본 목록을 태스크 ID로 전부 열거한다 — 재현성 확보.

**집계 산출**:
1. 태스크당 스폰 수 (L1/L2/L3 각각) — 평균·중앙값·최대·최소
2. 단계별 분포 — TASK/ANALYSIS/PLAN/TEST-SCENARIO/EXECUTE/TEST/CLOSE 각 단계가 차지하는 스폰 비율
3. pilot별 비교 — opd vs opds (단계 수 7 vs 5의 실제 비용 차이)
4. **EXECUTE 분배 배수** — PLAN.md의 실행 체크리스트 Step 수가 EXECUTE 스폰을 몇 배로 늘리는지. P1의 "디스패치 규모 조건부화"가 겨냥할 지점.

**출력 구조**: §0 참조·범례 / §1 원천 한계와 대리 지표 설계 / §2 표본 목록 / §3 태스크별 집계표 / §4 요약 통계 / §5 단계별 분포 / §6 결론(P1 조건부화 기준선 권고) / §7 추정 항목 일람

**부수 산출 (필수 기재)**: 본 실측 과정에서 확인된 "state.json에 워커 식별 필드 부재"는 그 자체로 **관측성(observability) 갭**이다. §6에 P1~P3 후속 후보로 1항목 기재한다 — 단, 본 태스크에서 스키마를 변경하지 않는다.

---

#### N-4. `analysis/A4-로드사슬.md` — 로드 사슬 보정

**보정 대상 (AS-IS 정적 합산의 과대계상 요인 3종)**:
1. **모드 서브 하네스 3벌 중복** — `opal-harness.md:86-92`에 따라 3종 중 **1개만** 로드된다(semi-agentic 240줄 / interactive 185줄 / agentic 240줄). 정적 합산은 최대 425줄 과대.
2. **조건부 참조 미발동분** — `opal-harness.md:100-113` 13행은 각각 로드 조건을 가진다. 해당 태스크에서 조건이 성립하지 않은 문서는 실효 로드에서 제외한다.
3. **세션 캐시 스킵** — `opal-harness.md:92`: "해당 서브 하네스가 현재 세션 컨텍스트에 이미 로딩되어 있으면 Read를 스킵한다." 동일 문서 반복 참조는 1회로 계상한다.

**표본**: 최근 완료 태스크 **3건**(085 / 084 / 083). 각각의 `state.json`에서 `skill`·`mode`·실제 진행 stage를 확정한 뒤(예: 085 = opds/agentic/TASK→PLAN→EXECUTE→TEST→CLOSE, `tasks/085-.../state.json:2-4`), 그 조건에서 발동하는 문서만 합산한다.

**홉 정의 (재현 가능한 규칙)**:

| 홉 | 정의 | 예 |
|----|------|-----|
| 1홉 | pilot SKILL.md가 직접 Read 지시 | `opal-pilot-dev-short/SKILL.md` §Harness → `opal-harness.md` |
| 2홉 | 1홉 문서가 Read 지시 | `opal-harness.md:100-113` → `harness/observability.md` |
| 3홉 | 2홉 문서가 Read 지시 | `harness/pm-review-gate.md` → `pm/dispatch-process.md` |
| 4홉+ | 이하 동일 | - |

각 홉 간선에 **근거 줄번호**를 기재한다. 홉 추적은 `grep -n -E 'Read|references/|\.md`'`로 각 문서의 참조 지시를 뽑아 간선을 구성한다.

**Top 5 선정 기준 (명시 필수)**: 우선순위 = ① 홉 깊이(깊을수록 우선) → ② 발동 빈도(매 디스패치 > 단계별 > 조건부) → ③ 줄수. 동점 시 줄수 큰 쪽. 선정 기준을 문서에 적어 판정을 재현 가능하게 한다.

**미등재 문서 처리**: `harness/` 실파일 17종 vs `opal-harness.md` 테이블 13행의 **차이 4종**(§1 S-5)을 개별 확인한다. 각각에 대해 (a) 어디서 로드되는지 추적, (b) 미등재가 의도적인지 누락인지 판정, (c) 판정 불가면 `[E]`로 표기하고 P1 확인 항목으로 이관한다.

**출력 구조**: §0 참조·범례 / §1 보정 방법(3종 과대계상 요인·홉 정의) / §2 표본 3건 조건표 / §3 태스크별 실효 로드 문서 목록(컬럼: `문서` / `줄수[M]` / `홉` / `발동 조건` / `근거`) / §4 정적 합산 vs 실효값 대조표 / §5 홉 깊이 Top 5 + 1홉화 권고 / §6 미등재 4종 판정 / §7 추정 항목 일람

**핵심 산출**: TASK.md §배경 분석의 "16문서 3,144줄(정적 합산)"을 **실효값으로 대체**하고, 차이(과대계상분)를 요인별로 귀속시킨다. 이것이 P1 "규칙 인덱스 단일화" 대상 선정의 근거가 된다.

---

#### N-5. `BLUEPRINT.md` — 청사진 정식화

**성격**: P1~P3 태스크의 **참조 SSOT**. 후속 태스크가 이 문서만 읽고 범위를 확정할 수 있어야 한다 (→ TASK.md AC-5).

**6개 필수 구성요소 (AC-5 그대로)**:

| § | 구성요소 | 작성 원칙 |
|---|---------|----------|
| §1 | AS-IS 5층 구조 | 층별로 **구성요소·규모 실측값·역할** 3열. §1 S-1 실측 인벤토리 사용. 대화 기억이 아닌 파일 근거로 재확인 |
| §2 | 문제 P-1~P-5 | 각 문제에 **증상 / 실측 근거(A1~A4 인용) / 영향 / 귀속 Phase** 4항목. 근거 없는 문제 기재 금지 |
| §3 | TO-BE 전략·계층 | "WHAT=pipeline.json SSOT / ENFORCE=도구 / WHY=경량 발동층" 3계층을 층별 소유 대상과 함께 정의 (→ TASK.md §확정된 설계 방향) |
| §4 | AS-IS/TO-BE 비교표 | 축별 대조: 규모·중복·로드·스폰·변경비용. **AS-IS 열은 실측값, TO-BE 열은 목표값**이며 목표값은 전부 `[E]`로 표기 |
| §5 | P1~P3 범위·완료기준 초안 | Phase별로 **범위(포함/제외) / 완료기준(측정 가능) / 롤백 단위 / 불변 제약 확인** 4항목 |
| §6 | A1~A4 반영 결론 | 갭 4건이 각각 어떤 실측값으로 해소되었는지 대조표 + 잔여 미확정 항목 |

**§2 문제-Phase 귀속 규칙**: P-1~P-3(중복 3계열)·P-4~P-5(효율 2건)를 §5의 P1/P2/P3 중 정확히 하나에 귀속시킨다. 귀속 없는 문제가 남으면 그것은 "본 태스크 범위 밖"으로 명시한다 — 문제와 Phase의 매핑 누락이 후속 태스크 범위 공백을 만든다.

**§5 완료기준 작성 규칙 [MUST]**: 각 Phase 완료기준은 **A1~A4의 실측 수치를 대상으로 한 측정 가능 서술**이어야 한다.
- Good: "opp/opd/opds/opdw SKILL.md의 WHAT-D 블록(A1 §3)이 전부 제거되어 4 pilot 합계 분모줄수가 N줄 이하가 된다"
- Bad: "산문을 압축한다"

**§5 불변 제약 확인 항목 (Phase마다 반복 확인)**:
> [MUST] TASK.md §확정된 설계 방향: "도구 게이트(state/test/backlog-tool) 제거 0건 / pilot alias 진입점 무중단 / 하위호환 기본값 규율"

각 Phase의 완료기준 하단에 이 3개 제약의 준수 방식을 1줄씩 기재한다.

**§1·§3 근거 규율**: 대화에서 도출된 진단이라도 **파일 근거로 재확인**하여 인용을 붙인다. 근거를 붙일 수 없는 항목은 `[E]`로 표기하고 §6 잔여 미확정에 등재한다 (→ D-7 §0).

**분할 작성**: §1~§4를 Step 5에서, §5~§6을 Step 6에서 작성한다. §5·§6은 A1~A4 결론을 통합 해석해야 하므로 별도 Step으로 분리하여 판단 품질을 확보한다.

---

## 3. 실행 체크리스트

> 총 6개 Step | Phase 2개
>
> | Phase | Step | 실행 | agent | 비고 |
> |-------|------|------|-------|------|
> | 1 | 1, 2, 3, 4 | **병렬** | `opal-task-agent` ×4 | 독립 파일 4개, 공유 입력 없음 |
> | 2 | 5 → 6 | **순차** | `opal-task-agent` | 동일 파일(BLUEPRINT.md) — 병렬 금지. 둘 다 Step 1~4 의존 |

> **영역 매핑**: 전 Step이 Framework 영역(`opal/`·`skills/`·`agents/`·`docs/` 읽기 + `tasks/086-*/` 쓰기)이므로 전부 범용 워커 `opal-task-agent`를 배정한다.
>
> **산출 파일 상한**: 모든 Step의 산출 파일이 1개다 (상한 3 준수).
>
> [MUST] 전 Step 공통: FW 소스(`opal/`·`skills/`·`agents/`)와 전역 배포본(`~/.opal/`)을 수정하지 않는다. 쓰기는 `tasks/086-260809-opp-fw-구조개선-청사진-실측/` 하위로만 한다.
> [MUST] 전 Step 공통: 커밋·git 명령을 실행하지 않는다 (→ `docs/CONVENTIONS.md` §Guards).
> [MUST] 전 Step 공통: 대상 파일 전체 통독 금지. grep으로 위치를 특정한 뒤 해당 구간만 Read한다.

### Step 1: A1 중복률 실측 — pipeline.json↔SKILL.md 3분류

- [x] 완료
- **agent**: `opal-task-agent`
- **파일**: `tasks/086-260809-opp-fw-구조개선-청사진-실측/analysis/A1-중복률.md` (신규 1개)
- **작업 내용**:
  1. `analysis/` 디렉토리 생성 (`mkdir -p`)
  2. 4 pilot SKILL.md(opp 274 / opd 416 / opds 383 / opdw 302줄)에서 `grep -n '^#\{1,4\} '`로 헤딩 블록 인덱스 + 줄범위·줄수 산출
  3. frontmatter·`## 변경이력` 블록을 제외한 분모줄수 확정 (산정식 문서 기재)
  4. 블록별 WHAT/ENFORCE/WHY 배타 판정 — §2 N-1 판정 기준 + 경계 규칙 4항 적용. 판정에 필요한 구간만 Read
  5. WHAT 블록을 4종 pipeline.json의 `stages`/`task_steps`/`pm_gate` 필드와 대조하여 **WHAT-D(실중복) / WHAT-P(잠재중복)** 분리
  6. pilot별 분류표 4개 + 요약 비율표 + P2 절단선 권고 작성
  7. 모든 수치에 `[M]`/`[D]`/`[E]` 마커, 근거는 `경로:줄번호` 인용
- **완료 기준**:
  - 4 pilot 전 헤딩 블록이 분류표에 정확히 1회씩 등장
  - pilot별 `WHAT+ENFORCE+WHY 줄수 합 == 분모줄수` 검산 통과 (4/4)
  - 각 WHAT 블록에 pipeline.json 대응 필드 또는 `없음(WHAT-P)` 기재
  - §4에 절단 대상 블록군이 pilot별로 명시됨
  - 마커 없는 수치 0건
- **테스트**: 검산식 4건 수동 확인 / 분류표 행 수 == grep 헤딩 수 대조 / 인용 경로 무작위 3건 실재 확인
- **의존**: 없음

### Step 2: A2 스키마 확장 소요 — 미보유 6 pilot

- [x] 완료
- **agent**: `opal-task-agent`
- **파일**: `tasks/086-260809-opp-fw-구조개선-청사진-실측/analysis/A2-스키마소요.md` (신규 1개)
- **작업 내용**:
  1. `analysis/` 디렉토리 확보 (`mkdir -p`)
  2. `pipeline-spec.schema.json` 49줄 Read → 판정 6축(A~F) 확정
  3. 6 pilot(oppd 818 / oppl 604 / opwt 559 / opsdd 544 / opgc 540 / opdd 323)에 대해 §2 N-2 추출 절차 4단계 수행 — grep 헤딩 인덱스 → STEP 하위 구간만 선택 Read
  4. pilot별 구조 추출표(stage/item/key 후보/게이트/근거줄) 작성
  5. 6축 대조 → EXPRESSIBLE / NEEDS-EXT 2분류. EXPRESSIBLE은 가상 task_steps 행 2~3개 예시 기재, NEEDS-EXT는 막히는 축 + 최소 확장안 1개 기재
  6. 스키마 확장안 종합 + **하위호환 영향 판정**(기존 4 pilot pipeline.json 유효성) + P2 범위 권고
- **완료 기준**:
  - 6 pilot 전부에 EXPRESSIBLE/NEEDS-EXT 판정이 부여됨
  - NEEDS-EXT 전건에 막히는 축(A~F 중) + 최소 확장안이 명시됨
  - EXPRESSIBLE 전건에 가상 task_steps 행 예시가 있고 `key` 패턴 `:28`을 만족함
  - §4에 불변 제약 3종(도구 게이트 유지 / alias 무중단 / 하위호환) 위반 여부가 판정됨
  - 스키마 인용이 전부 `schema.json:N` 형식
- **테스트**: 가상 key 값 전건을 `:28` 정규식에 수동 대조 / 6 pilot 추출 stage 수 == SKILL.md STEP 헤딩 수 대조 / 판정표 행 수 == 6
- **의존**: 없음

### Step 3: A3 스폰 수 실측 — K4 위임 비용 기준선

- [x] 완료
- **agent**: `opal-task-agent`
- **파일**: `tasks/086-260809-opp-fw-구조개선-청사진-실측/analysis/A3-스폰실측.md` (신규 1개)
- **작업 내용**:
  1. `analysis/` 디렉토리 확보 (`mkdir -p`)
  2. **원천 한계 먼저 확정·기재**: `tasks/*/state.json`의 `owner` 값 분포를 재확인(PM/auto/user 3종)하고, 직접 집계 불가 사실을 §1에 명시
  3. 표본 선정 — `PLAN.md`+`DONE.md` 보유 & skill ∈ {opd, opds}, 최신순 opd 6건 이상 + opds 6건 이상(총 12건 이상). 표본 ID 전건 열거. `TEST.md`는 근거 제외
  4. L1(정적 하한): 4종 pipeline.json의 워커 디스패치 정의 행 수 집계
  5. L2(실행 하한): 표본별 산출물 존재 + PLAN.md 실행 체크리스트 Step 수 집계
  6. L3(관측 보정): DONE.md·STATE.md 의사결정 로그에서 재시도·루핑·에스컬레이션 기록 추출 → `[E]` 표기
  7. 요약 통계(평균·중앙값·최대·최소) + 단계별 분포 + opd/opds 비교 + **EXECUTE 분배 배수** 산출
  8. §6에 P1 조건부화 기준선 권고 + 관측성 갭(워커 식별 필드 부재) 후속 후보 1항목 기재
- **완료 기준**:
  - 표본 12건 이상이 ID로 열거되고 각각 L1/L2/L3 값이 채워짐
  - L1/L2/L3가 합산되지 않고 **분리 표기**됨
  - L3 전건이 `[E]` + 추정 근거 문장 보유
  - 단계별 분포 합이 100%(또는 총 스폰 수)와 일치
  - §6에 조건부화 기준선이 수치로 제시됨
- **테스트**: 표본 태스크 디렉토리 실재 확인(전건) / 평균 재계산 검산 / `TEST.md` 인용 0건 확인
- **의존**: 없음

### Step 4: A4 로드 사슬 보정 — K3 실효값 + 홉 Top5

- [x] 완료
- **agent**: `opal-task-agent`
- **파일**: `tasks/086-260809-opp-fw-구조개선-청사진-실측/analysis/A4-로드사슬.md` (신규 1개)
- **작업 내용**:
  1. `analysis/` 디렉토리 확보 (`mkdir -p`)
  2. 표본 3건(085/084/083)의 `state.json`에서 `skill`·`mode`·진행 stage 확정
  3. `opal-harness.md:86-92`(모드 배타 로드)·`:92`(세션 캐시 스킵)·`:100-113`(조건부 13행)을 근거로 3종 과대계상 요인 정의
  4. 표본별 실효 로드 문서 목록 재구성 — 발동 조건이 성립한 문서만. 각 행에 줄수·홉·발동조건·근거
  5. 홉 추적 — 각 문서에서 `grep -n -E 'Read|references/|\.md`'`로 참조 간선 추출, 간선마다 근거 줄번호 기재
  6. 정적 합산(16문서 3,144줄) vs 실효값 대조표 — 차이를 요인별 귀속
  7. 홉 깊이 Top 5 선정(기준: 홉>빈도>줄수) + 1홉화 권고
  8. `harness/` 실파일 17종 vs 테이블 13행의 차이 4종 개별 판정
- **완료 기준**:
  - 표본 3건 각각에 실효 로드 문서 목록과 합계 줄수가 산출됨
  - 정적↔실효 차이가 3종 요인에 귀속되어 잔차 0 또는 잔차 사유 명시
  - Top 5 각 항목에 홉 수·간선 근거 줄번호·1홉화 권고가 있음
  - 미등재 4종 각각에 로드 경로 추적 결과 + 의도/누락 판정
  - 선정 기준이 문서에 명시되어 재현 가능
- **테스트**: 표본 3건 state.json의 skill/mode 값 실재 확인 / 홉 간선 근거 3건 무작위 실재 확인 / 실효값 ≤ 정적 합산 성립 확인
- **의존**: 없음

### Step 5: BLUEPRINT §1~§4 — AS-IS 진단·TO-BE 전략·비교표

- [x] 완료
- **agent**: `opal-task-agent`
- **파일**: `tasks/086-260809-opp-fw-구조개선-청사진-실측/BLUEPRINT.md` (신규 1개)
- **작업 내용**:
  1. A1~A4 4개 산출물을 Read하여 실측 결론 확보
  2. 문서 골격 생성 — 헤더(작성일·성격·참조 SSOT 선언) + §0 참조 문서 테이블 + 마커 범례
  3. **§1 AS-IS 5층 구조** — 층별 구성요소·규모 실측값·역할 3열. PLAN §1 S-1 인벤토리 + `docs/PROJECT.md` §주요 컴포넌트로 재확인
  4. **§2 문제 P-1~P-5** — 각각 증상/실측 근거(A1~A4 §인용)/영향/귀속 Phase 4항목. 근거 없는 문제 기재 금지
  5. **§3 TO-BE 전략·계층** — WHAT/ENFORCE/WHY 3계층 + 층별 소유 대상 정의
  6. **§4 AS-IS/TO-BE 비교표** — 축: 규모·중복·로드·스폰·변경비용. AS-IS는 실측, TO-BE 목표값은 전부 `[E]`
  7. §5·§6 자리표시 헤딩만 배치 (내용은 Step 6)
- **완료 기준**:
  - §1~§4가 모두 작성되고 §5·§6 헤딩이 배치됨
  - §1 5개 층 전부에 규모 실측값 + 근거 인용
  - §2 P-1~P-5 전건에 A1~A4 중 최소 1개 인용 + 귀속 Phase(P1/P2/P3/범위밖)
  - §4 TO-BE 열 전 셀에 `[E]` 마커
  - 근거 없는 서술 0건 (→ D-7 §0)
- **테스트**: §2 5건 × 4항목 충족 확인 / A1~A4 인용 경로·섹션 실재 확인 / §4 축 5개 존재 확인
- **의존**: Step 1, 2, 3, 4

### Step 6: BLUEPRINT §5~§6 — P1~P3 범위·완료기준 + 실측 반영 결론

- [x] 완료
- **agent**: `opal-task-agent`
- **파일**: `tasks/086-260809-opp-fw-구조개선-청사진-실측/BLUEPRINT.md` (수정 — Step 5 산출물에 §5·§6 채움)
- **작업 내용**:
  1. Step 5 산출 BLUEPRINT.md §1~§4 Read (전체 통독 대신 §2 귀속표·§4 비교표 중심)
  2. **§5 P1~P3 범위·완료기준 초안** — Phase별 4항목: 범위(포함/제외) / 완료기준(A1~A4 수치 기반, 측정 가능) / 롤백 단위 / 불변 제약 3종 준수 방식
     - P1: 하네스 압축 + Opus 5 정합 — A4 실효값·A3 스폰 기준선 기반
     - P2: 데이터 주도 전환 — A1 WHAT-D/WHAT-P 절단선 + A2 스키마 확장 범위 기반
     - P3: 액션 에이전트 통합 + 2차 도구화 — A1 ENFORCE 분류 + A2 NEEDS-EXT 기반
  3. §2 문제 귀속과 §5 Phase 범위의 **역방향 대조** — P-1~P-5가 전부 어느 Phase에든 담겼는지 확인, 미귀속 시 "범위 밖" 명시
  4. **§6 A1~A4 반영 결론** — 갭 4건 대조표(갭 / 이전 상태 / 실측값 / 근거 / 해소 여부) + 잔여 미확정(`[E]`) 항목 통합 일람
  5. Edit로 §5·§6 구간만 부분 편집 (전체 재작성 금지)
- **완료 기준**:
  - §5에 P1/P2/P3 각각 4항목이 전부 작성됨
  - 각 Phase 완료기준이 A1~A4의 구체 수치를 대상으로 하여 Pass/Fail 판정 가능
  - 각 Phase에 불변 제약 3종(도구 게이트 0건 제거 / alias 무중단 / 하위호환) 준수 방식 기재
  - §6 대조표에 갭 4건이 전부 등장하고 각각 해소/부분해소/미해소 판정
  - §2의 P-1~P-5 전건이 §5 Phase에 귀속되거나 "범위 밖" 명시
  - AC-5의 6개 구성요소(①~⑥)가 BLUEPRINT.md에 모두 존재
- **테스트**: AC-5 6요소 체크리스트 대조 / P-1~P-5 귀속 역방향 대조 / 완료기준 문장에 수치 포함 여부 전건 확인 / 갭 4건 대조표 행 수 == 4
- **의존**: Step 5 (동일 파일 — 병렬 금지)

---

## 4. QA 체크리스트

### 기능 테스트 (TASK.md 요구사항 대응)

- [ ] **AC-1**: `analysis/A1-중복률.md`에 4 pilot(opp/opd/opds/opdw)별 WHAT/ENFORCE/WHY 줄수 기준 비율표가 있고, 섹션 단위 분류표가 근거로 첨부되어 있다
- [ ] **AC-1 확장**: WHAT이 실중복(WHAT-D)/잠재중복(WHAT-P)으로 분리되어 P2 절단선 권고가 도출되었다
- [ ] **AC-2**: `analysis/A2-스키마소요.md`에 미보유 6 pilot(oppd/oppl/opsdd/opwt/opgc/opdd)의 단계·게이트·디스패치 구조가 추출되고, EXPRESSIBLE/NEEDS-EXT 2분류표가 있다
- [ ] **AC-2 확장**: NEEDS-EXT 전건에 막히는 스키마 축과 최소 확장안이 명시되었다
- [ ] **AC-3**: `analysis/A3-스폰실측.md`에 opd·opds 표본 10건 이상의 태스크당 디스패치 수(평균·최대)와 단계별 분포가 있다
- [ ] **AC-3 제약**: 원천 데이터 한계(owner 필드 워커 미기록)가 명시되고 대리 지표 3계층이 분리 표기되었다
- [ ] **AC-4**: `analysis/A4-로드사슬.md`에 최근 태스크 2~3건 기준 실효 로드 문서 목록과 홉 깊이 Top 5가 있다
- [ ] **AC-4 확장**: 정적 합산 대비 과대계상분이 요인별로 귀속되었다
- [x] **AC-5**: `BLUEPRINT.md`에 ①AS-IS 5층 ②P-1~P-5 ③TO-BE 전략·계층 ④비교표 ⑤P1~P3 범위·완료기준 ⑥A1~A4 반영 결론이 모두 있다

### 일관성 테스트

- [ ] A1~A4의 실측값이 BLUEPRINT.md §2·§4·§6에 인용될 때 수치가 일치한다 (전사 오류 0)
- [ ] pilot alias 표기가 전 산출물에서 통일되어 있다 (opp/opd/opds/opdw/opwt/opgc/oppd/opsdd/oppl/opdd — `pipeline-spec.schema.json:10` 기준)
- [ ] 단계명 표기가 pipeline.json `meta.stages`와 일치한다 (TASK/ANALYSIS/PLAN/TEST-SCENARIO/EXECUTE/TEST/CLOSE/WIREFRAME)
- [ ] BLUEPRINT.md §2의 P-1~P-5가 §5의 P1~P3에 빠짐없이 귀속되었다 (역방향 대조)
- [ ] TASK.md §배경 분석의 기존 수치와 본 태스크 실측값이 다른 경우, 차이가 명시적으로 기록되었다
- [ ] 3계층 용어(WHAT/ENFORCE/WHY)가 A1과 BLUEPRINT §3에서 동일 정의로 사용된다

### 문서 품질

- [ ] 모든 수치에 `[M]`/`[D]`/`[E]` 마커가 부여되었고, 각 산출물에 범례와 추정 항목 일람이 있다
- [ ] 모든 근거가 `경로:줄번호` 또는 `문서 §섹션` 형식으로 인용되었다 (→ `harness/citation-rules.md` §2)
- [ ] 각 산출물 최상단에 §0 참조 문서 테이블(공통 5컬럼)이 있다 (→ 동 §3.1)
- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따른다 (→ `docs/CONVENTIONS.md` §언어 규칙)
- [ ] kebab-case 또는 프로젝트 관례를 따르는 파일명을 사용한다 (`A1-중복률.md` 등 TASK.md 지정 경로 준수)
- [ ] 산출물이 태스크 폴더 내 5개 md뿐이며 FW 소스·`~/.opal/` 변경이 0건이다 (`git status`로 확인 — 커밋은 하지 않음)
- [ ] 집계 스크립트가 태스크 폴더에 남아 있지 않고, 재현 명령문이 산출물에 기재되었다

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R-1 | **AC-3 원천 데이터 부재** — `state.json`의 `owner`가 PM/auto/user 3종뿐이라 디스패치 횟수를 직접 집계할 수 없다 (§1 S-3) | AC-3이 실측이 아닌 추정으로 전락 | L1(정적, `[M]`)/L2(실행, `[M]`)/L3(관측 보정, `[E]`) 3계층 대리 지표로 재구성하고 분리 표기. 한계를 A3 §1 최상단에 명시. 관측성 갭을 P1~P3 후속 후보로 등재 |
| R-2 | **AC-1 분류 판정의 주관성** — WHAT/ENFORCE/WHY 경계가 판정자마다 흔들리면 비율이 재현되지 않는다 | P2 절단선 근거가 무너짐 | 경계 규칙 4항 사전 고정(과반 배타 할당 / 30줄 초과 시 하위 재판정 / Harness 블록 ENFORCE 고정 / 판정 불가 시 WHY 보수 할당) + `혼재` 컬럼으로 흔들림 노출 + pipeline.json 실대조로 WHAT-D 검증 |
| R-3 | **A2 입력 규모** — 미보유 6 pilot 합계 3,388줄로 전체 통독 시 컨텍스트 초과 | Step 2 워커 중단 또는 품질 저하 | grep 헤딩 인덱스 우선 → STEP 하위 구간만 선택 Read. pilot 1종씩 순차 처리하고 각 pilot 추출표를 완결 저장 후 다음으로 이동(증분 저장) |
| R-4 | **A4 홉 추적 발산** — 참조 간선이 4홉 이상 확산되면 탐색이 끝나지 않는다 | Step 4 지연 | 탐색 깊이를 **4홉에서 절단**하고 절단 사실을 문서에 명시. Top 5 선정 기준(홉>빈도>줄수)을 먼저 고정하여 탐색 목표를 한정 |
| R-5 | **TASK.md 배경 수치와 실측 불일치** — TASK.md:22 "opd 15·opds 11·opp 1"인데 실측은 opd 15/opds 10/opp 2 (§1 S-4) | 청사진 근거 신뢰도 저하 | 실측값을 채택하고, BLUEPRINT.md §6 또는 각 A 문서에 "TASK.md 기재값 대비 차이" 행을 남긴다. TASK.md는 수정하지 않는다 |
| R-6 | **Step 5·6 동일 파일 경합** — 병렬 실행 시 BLUEPRINT.md 덮어쓰기 | 산출물 손실 | Phase 2로 분리하여 순차 강제. Step 6은 Edit 부분 편집만 사용하고 Write 재작성 금지 |
| R-7 | **읽기 전용 위반** — 워커가 개선안을 발견하고 FW 소스를 직접 수정 | 태스크 범위 이탈 + 배포 경계 위반 | 전 Step 프롬프트에 [MUST] 읽기 전용 제약을 명시. Step 6 완료 후 `git status`로 `tasks/086-*` 외 변경 0건 확인(커밋은 하지 않음) |
| R-8 | **§5 완료기준의 모호성** — "압축한다" 류 서술은 P1~P3에서 Pass/Fail 판정 불가 | 후속 태스크 범위 표류 | §5 완료기준 작성 규칙(A1~A4 수치 대상 + 측정 가능)을 [MUST]로 고정하고 Good/Bad 예시를 PLAN §2 N-5에 명시. QA에서 "수치 포함 여부 전건 확인" |
| R-9 | **A2 스키마 확장안이 하위호환을 깬다** — 확장 제안이 기존 4 pilot pipeline.json을 무효화 | 불변 제약 위반 | A2 §4에 하위호환 영향 판정을 필수 섹션으로 배치. `additionalProperties:false` 4개소(`schema.json:7,14,25,40`) 각각에 대해 기존 4종 유효성 확인 |
| R-10 | **용어 불일치** — 3계층 명칭(WHAT/ENFORCE/WHY)이 A1과 BLUEPRINT §3에서 다르게 정의될 위험 (→ D-7 §7 영역 간 용어 일관성) | 절단선 해석 충돌 | A1 §1에서 3계층을 1회 정의하고 BLUEPRINT §3이 A1 정의를 인용 참조한다(재정의 금지). QA 일관성 항목으로 검증 |

---

## 6. 문서/코드 불일치 기록

> 규칙: 문서와 실제 코드가 다르면 **코드(실질적 문서) 기준**으로 작업하고 불일치를 기록한다.

| # | 문서 기재 | 실측 (코드/파일) | 채택 | 근거 |
|---|----------|-----------------|------|------|
| M-1 | TASK.md:22 "opd 15·opds 11·opp 1" (합 27) | opd 15 / opds 10 / opp 2 (합 27, 086 포함) | 실측 | `tasks/*/state.json` `"skill"` 집계 |
| M-2 | TASK.md:23 AC-3 "STATE.md/DONE.md에서 태스크당 디스패치 횟수" 집계 가능 전제 | STATE.md·state.json에 워커 식별 필드 없음 (`owner` = PM/auto/user) | 실측 → 대리 지표 설계 | `tasks/*/state.json` `"owner"` 값 분포 |
| M-3 | `opal-harness.md:100-113` 참조 문서 테이블 13행 | `opal/core/references/harness/` 실파일 17종 | 실측 → A4 §6에서 4종 차이 개별 판정 | 디렉토리 목록 |
| M-4 | TASK.md:22 "16문서 3,144줄(정적 합산)" | 모드 서브 하네스 3종 배타 로드(`opal-harness.md:86-92`)로 최대 425줄 과대계상 | 실측 → A4에서 실효값 보정 | `opal-harness.md:86-92` |
