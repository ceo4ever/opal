# TASK: 파이프라인 현황판 JSON 분리 + state-tool 도입 (B안)

> 작성일: 2026-05-01 | 갱신: 2026-05-01 19:05 (검토 보강 v2) | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청 — STATE.md 파이프라인 현황판의 토큰 효율화 + 절차 강제력 강화
> 출력: TASK.md

## 작업 목표

STATE.md의 "파이프라인 현황판" 표를 단일 진실(SSOT)이 JSON인 구조로 분리하고, Python 기반 `state-tool`로만 갱신 가능하게 만들어 LLM의 절차 우회/오갱신을 차단한다. STATE.md의 표 영역은 툴이 자동 렌더한 뷰로 유지하여 사람 가독성도 함께 보장한다.

## 배경

현재 STATE.md의 파이프라인 현황판은 마크다운 표를 LLM이 손으로 편집하는 구조다. `opal/core/references/opal-harness.md` §3과 `opal/core/references/harness/state.md`에서 "갱신 미수행 시 다음 단계 진입 금지"라는 [MUST] 규칙이 있지만, 검증은 PM Gate에서 사람·AI의 수동 자가 점검에 의존한다. 이로 인해 다음 사고가 잠재된다:

- 이전 행 ✅ 없이 다음 단계 진입 (순서 강제 우회)
- 단계명/항목명 오타로 표 깨짐
- 시점(타임스탬프) 누락 또는 오기
- 모드(interactive/agentic)와 표 행 구성 불일치
- "파이프라인 현황판 행 상태 정합성" PM Gate 검증의 회피 가능성 (`opal/core/references/harness/pm-review-gate.md` 검증 항목)

또한 STATE.md 전체가 매 갱신마다 컨텍스트에 들어가는 토큰 비용이 누적된다. 파이프라인 표 영역(약 25줄)을 JSON으로 분리하면 절감 효과가 있으나, 본 태스크의 1차 가치는 **절차 강제력**, 2차 가치가 토큰 효율화다.

## 배경 분석 (대화에서 도출)

### 현재 구조 분석

| 영역 | 현재 위치 | 갱신 주체 | 갱신 방식 |
|------|---------|---------|---------|
| 파이프라인 현황판 표 | `STATE.md` 본문 | 오케스트레이터(PM) + 워커 | 마크다운 표 직접 편집 |
| 의사결정 로그 | `STATE.md` 본문 | PM | 자유 텍스트 |
| 블로커 | `STATE.md` 본문 | PM/워커 | 자유 텍스트 |
| 다음 액션 | `STATE.md` 본문 | PM | 자유 텍스트 |

### 영향 범위 식별 — 소스(`opal/`) 기준 약 42개

**※ ~/.opal/는 배포본이므로 모든 수정은 소스 경로에서 수행** (`opal/.opal/AGENT.md` §확정 기준 #2).

#### A. STATE 갱신 직접 다룸 (강 영향) — 27개

**하네스 (core/) — 8개**:

| 파일 | 영향 내용 |
|------|---------|
| `opal/core/AGENT.md` | STATE 언급 — 본문 검토 후 갱신 표현 수정 |
| `opal/core/references/opal-harness.md` §3 | State 모듈 stub에 "state-tool 호출만 허용" [MUST] 추가 |
| `opal/core/references/opal-harness.md` §9 | 도구 테이블에 `state-tool` 행 추가 |
| `opal/core/references/opal-harness-interactive.md` | Gate 통과 후 STATE 갱신 절차 → 툴 호출로 교체 |
| `opal/core/references/opal-harness-agentic.md` | PM 대행 갱신 절차 → 툴 호출로 교체 |
| `opal/core/references/harness/state.md` ★ | 갱신 로직 본체 — 마크다운 편집 → `state advance/mark` 호출 |
| `opal/core/references/harness/state-template.md` ★ | LLM 직접 작성 금지 [MUST] + `state init` 호출 명시 |
| `opal/core/references/harness/task-process.md` | TASK 시작 시 STATE.md 생성 → `state init` 호출 |
| `opal/core/references/harness/additional-work.md` | 추가작업 행 추가 → `state add-row` 호출 |

(harness §9 도구 테이블 갱신은 1개로 카운트)

**오케스트레이터 (skills/opal-pilot-*) — 8개**:

`opal-pilot-dev`, `opal-pilot-dev-short`, `opal-pilot-dev-wireframe`, `opal-pilot-gc`, `opal-pilot-project`, `opal-pilot-project-dev`, `opal-pilot-sdd`, `opal-pilot-write-tech` — 각 SKILL.md의 "STATE.md 도메인 치환값" + STATE 갱신 표현 갱신

**단계 스킬 (skills/op-*) — 3개**:

| 파일 | 영향 내용 |
|------|---------|
| `opal/skills/op-task/SKILL.md` | TASK 단계 STATE.md 생성 리마인더 → `state init` 호출 |
| `opal/skills/op-dev-analysis/SKILL.md` | STATE 언급 — 본문 검토 후 갱신 |
| `opal/skills/op-dev-execute/references/execute-guide.md` | EXECUTE Step 갱신 → `state mark --as-worker` 호출 |

> **op-task-*, op-task-qa, op-dev-{plan,qa,test-scenario,todo,wireframe}, op-sdd-*, op-spec-validator는 STATE 갱신 책임 없음** (오케스트레이터/하네스가 위임). 영향 없음 확인 완료.

**에이전트 (agents/) — 8개** ⭐신규 식별:

`opal-be-agent`, `opal-db-agent`, `opal-fe-agent`, `opal-plan-agent`, `opal-sdd-action-agent`, `opal-task-agent`, `opal-task-action-agent`, `opal-planning-agent/personas/service-planner.md` — 워커 행위 규칙(STATE 갱신 책임)이 박혀있을 가능성. PLAN 단계에서 본문 분류·갱신.

#### B. 가이드/참조 문서 (약 영향) — 12개

| 영역 | 파일 (언급 횟수) |
|------|----------------|
| `core/references/harness/` | `parallel-execution.md` (1), `qa-standards.md` (2) |
| `skills/opal-pilot-project-dev/references/` | `parallel-execution-guide.md` (9), `verification-loop-guide.md` (8), `wbs-guide.md` (2), `roadmap-guide.md` (2), `prd-guide.md` (1), `trd-guide.md` (1) |
| `skills/opal-pilot-sdd/references/` | `execute-loop-guide.md` (8), `spec-plan-guide.md` (3), `verify-guide.md` (1) |
| `skills/opal-pilot-gc/references/` | `done-template.md` (1) |

> 언급 횟수 5건 이상은 실질 갱신 가능성 높음. PLAN에서 단순 참조 vs 실질 갱신을 grep + 본문 분류.

#### C. 등록부/배포 — 3개

| 파일 | 영향 내용 |
|------|---------|
| `opal/core/references/tools.md` | `state-tool` 사용법 등록 |
| `opal/core/references/opal-harness.md` §9 도구 테이블 | `state-tool` 행 추가 (강 영향에서 카운트) |
| `scripts/install-mac.sh` | `state-tool/` 배포 함수 추가, `run.sh` 실행 권한 부여 |

#### D. 영향 없음 (확인 완료)

`op-task-execute`, `op-task-plan`, `op-task-qa`, `op-dev-plan`, `op-dev-qa`, `op-dev-test-scenario`, `op-dev-todo`, `op-dev-wireframe`, `op-sdd-{action-plan, plan, spec, verify}`, `op-spec-validator`

### OPAL Tools 패턴 정합성

`opal/core/references/opal-harness.md` §9에 정의된 OPAL Tools 패턴을 따른다 (`opal/tools/xlsx-tool/run.sh:1-13` 참조):

- 위치: `opal/tools/state-tool/run.sh` (소스), 배포 시 `~/.opal/tools/state-tool/`
- Python 베이스: `~/.opal/.venv/bin/python` (xlsx-tool과 동일 — 단, state-tool은 표준 라이브러리만 import)
- 출력: JSON (`{"ok": true/false, ...}`)
- 호출: PM·워커 모두 Bash로 호출

## 확정된 설계 방향 (대화에서 합의)

대화에서 캡틴과 합의된 사항:

1. **B안 (하이브리드)** 채택 — 파이프라인 표만 JSON으로 분리, 의사결정 로그/블로커/다음 액션은 STATE.md 자유 텍스트로 유지
2. **단일 진실 = JSON** — STATE.md의 표는 `state-tool`이 자동 렌더한 미러 (사람 가독성 유지 목적)
3. **호출 주체 분담**:
   - PM(오케스트레이터): `init`, `advance`, `mark`(대부분), `block`, `validate`, `show`, `add-row`
   - 워커: 자기가 디스패치된 단계의 진행 기록만 (`mark --as-worker`)
   - 워커가 다른 단계 행을 수정하려 하면 툴이 거부
4. **하네스 강제 지점**: `harness/state.md`에 "파이프라인 행 상태 변경은 `state-tool`로만 수행한다"를 [MUST]로 추가, 워커 프롬프트에도 명시
5. **의사결정 로그/블로커/다음 액션은 본 태스크 범위 밖** — STATE.md에 자유 텍스트로 그대로 유지
6. **마이그레이션은 단계적**: 도구 구현 → 하네스 갱신 → op-task / op-dev-analysis 갱신 → pilot 시리즈 → 에이전트 → 가이드 → 회귀 테스트 순

### 기술 결정 (검토 v2에서 추가 확정)

| # | 항목 | 확정 |
|---|------|------|
| T-1 | state.json 위치 | `tasks/{NNN}-.../state.json` (STATE.md와 같은 폴더) |
| T-2 | 상태값 enum 매핑 | `pending`(⬜), `in_progress`(🔄), `done`(✅), `failed`(❌), `na`(-) |
| T-3 | 종료 코드 규약 | `0=ok`, `1=violation/scope_error`, `2=internal_error` |
| T-4 | 에러 응답 형식 | `{"ok": false, "error": "<code>", "message": "<text>", "violations": [...]?}` (xlsx-tool 패턴 차용) |
| T-5 | 시점 기록 방법 | `node ~/.opal/tools/date/date.js datetime` 호출 (KST 일관성) |
| T-6 | 마커 형식 | `<!-- pipeline:start -->` ~ `<!-- pipeline:end -->` HTML 주석. 마커 손실 시 `init`은 거부, `show`는 fallback으로 표 영역 추정 출력 |
| T-7 | `advance` vs `mark` 분리 | `advance`: ⬜→🔄 한정. `mark`: ⬜/🔄→✅ 한정. `block`: any→❌. 역할 명확 분리 |
| T-8 | `init` 멱등성 | 기본 거부 (`{"ok": false, "error": "already_initialized"}`), `--force`로 덮어쓰기 |
| T-9 | agentic 자율 통과 | `mark --auto-pass` 별도 플래그 (감사 트레일 명확화). 행 시점 `note`에 "agentic auto-pass" 자동 기재 |
| T-10 | 워커 권한 게이트 | `--as-worker` + 환경 추론 — 워커가 디스패치된 단계의 "작업" 행 한정 (EXECUTE만이 아님). 다른 행 시도 시 `worker_scope_violation` 반환 |
| T-11 | Python 베이스 | `~/.opal/.venv/bin/python` 사용. 표준 라이브러리만 import (`json`, `argparse`, `pathlib`, `subprocess`, `re`, `sys`) |
| T-12 | 호출 형식 | 현 형태(`~/.opal/tools/state-tool/run.sh <command> ...`) 유지. 별칭 도입은 별도 후속 태스크 |
| T-13 | 134 자기 자신 마이그레이션 | EXECUTE 끝 회귀 테스트로 `state init --import-existing` 수행 (현 STATE.md를 파싱하여 state.json 생성). 단, 임포트 명령 정확 동작은 PLAN에서 설계 |

## 요구사항

### 기능 요구사항 — state-tool 도구

- [ ] **F-1** `opal/tools/state-tool/` 디렉토리에 도구 본체와 래퍼를 작성한다
  - **무엇을**: `state_tool.py` (본체) + `run.sh` (래퍼) + `schema/state.schema.json` (스키마) + `README.md` (사용법)
  - **어디에**: `opal/tools/state-tool/`
  - **왜**: OPAL Tools 패턴 정합성 — `opal/core/references/opal-harness.md` §9
  - **AC**: `~/.opal/tools/state-tool/run.sh --help` 실행 시 7개 서브 명령(`init`, `show`, `advance`, `mark`, `block`, `validate`, `add-row`)이 안내되며 모든 응답이 JSON 단일 객체이다

- [ ] **F-2** 서브 명령 7종 시그니처와 동작
  - **무엇을**: 아래 시그니처대로 구현
  - **AC**: 각 명령이 다음 동작 + JSON 결과 + 종료 코드(T-3)를 정확히 반환한다
    - `init <task-path> --skill <opp|opd|opds|opdw|opwt|opgc|oppd|opsdd> --mode <interactive|agentic> [--force] [--import-existing]`: state.json + STATE.md 초기 생성. `--import-existing`은 기존 STATE.md 파싱 후 흡수
    - `show <task-path> [--format md|json]`: 기본 마크다운 표, `--format json`이면 state.json 그대로 출력
    - `advance <task-path> --row <N> [--note <text>]`: ⬜→🔄 전환 한정 (T-7)
    - `mark <task-path> --row <N> --done [--note <text>] [--as-worker] [--auto-pass]`: ⬜/🔄→✅ 전환. `--as-worker`는 권한 검증(T-10) 통과 시 허용. `--auto-pass`는 agentic 자율 통과(T-9)
    - `block <task-path> --row <N> --reason <text>`: any→❌ 전환. STATE.md 블로커 섹션 자유 텍스트는 PM이 별도 수행
    - `validate <task-path>`: 행 순서, 모드 일치, 필수 행 누락, 마커 손상, 스키마 위반 검사 → `{ok, violations[]}`
    - `add-row <task-path> --after <N> --stage <단계명> --item <항목명>`: 추가작업 행 삽입 (`opal/core/references/harness/additional-work.md` 참조)

- [ ] **F-3** state.json 스키마 정의
  - **무엇을**: JSON Schema (Draft-07) 작성
  - **어디에**: `opal/tools/state-tool/schema/state.schema.json`
  - **AC**: 아래 스키마를 따르며, 위반 시 모든 명령이 거부하고 `violations[]`를 반환한다

  ```json
  {
    "task_id": "134-260501-opp-pipeline-state-tool",
    "skill": "opp",
    "mode": "interactive",
    "schema_version": "1.0",
    "created_at": "2026-05-01 17:58",
    "updated_at": "2026-05-01 19:05",
    "current_status": "in_progress",
    "rows": [
      {
        "row_id": 1,
        "stage": "TASK",
        "item": "작업",
        "status": "done",
        "status_label": "✅",
        "timestamp": "2026-05-01 17:58",
        "owner": "PM",
        "note": null
      }
    ]
  }
  ```

  필드 규정: `current_status` enum = `in_progress | done | blocked | additional_work | additional_work_done`. `status` enum = T-2 매핑. `owner` enum = `PM | worker | user | auto`.

- [ ] **F-4** STATE.md 자동 동기화
  - **무엇을**: `init`/`advance`/`mark`/`block`/`add-row` 실행 시 STATE.md의 파이프라인 영역만 마커(T-6)로 안전 교체
  - **AC**: 의사결정 로그/블로커/다음 액션 영역은 보존된다. 마커 손실 시 `init` 실패 + `{"ok": false, "error": "marker_missing"}` 반환

- [ ] **F-5** 워커 권한 게이트 (T-10)
  - **무엇을**: `--as-worker` 플래그가 있으면 워커가 디스패치된 단계의 "작업" 행만 수정 가능. 다른 단계/항목 시도 시 거부
  - **어디에**: `state_tool.py` 권한 검증
  - **AC**: PLAN 디스패치된 워커가 EXECUTE 행을 mark 시도하면 `{"ok": false, "error": "worker_scope_violation", "exit": 1}` 반환. 디스패치 단계 식별 방식은 PLAN에서 결정 (예: `--worker-stage <stage>` 명시 인자 vs 환경 변수)

- [ ] **F-6** 시점 자동 기록 (T-5)
  - **AC**: 모든 갱신 명령은 `node ~/.opal/tools/date/date.js datetime`을 subprocess로 호출하여 KST 시점을 받아 `timestamp` 필드와 `updated_at`을 갱신한다

### 하네스/스킬 갱신 요구사항

- [ ] **F-7** `opal/core/references/harness/state.md` 갱신
  - **AC**: "파이프라인 행 상태 변경은 `state-tool`로만 수행한다" [MUST] 추가. 갱신 주체 테이블이 "툴 호출 명령"으로 갱신된다 (예: "TASK 완료 → `state init`", "단계 시작 → `state advance --row N`")

- [ ] **F-8** `opal/core/references/harness/state-template.md` 역할 축소
  - **AC**: "[MUST] STATE.md 직접 작성 금지, `state init` 호출"이 본문 상단에 추가된다. 기존 템플릿 본문은 `state-tool`의 출력 형식 참조용으로 유지

- [ ] **F-9** `opal/core/references/harness/task-process.md` STATE.md 생성 절차 교체
  - **AC**: §오케스트레이터 공통 영역 5번 항목이 `~/.opal/tools/state-tool/run.sh init {경로} --skill {약어} --mode {모드}` 호출로 교체된다

- [ ] **F-10** `opal/core/references/harness/pm-review-gate.md` 자동 검증 추가
  - **AC**: PM Gate 자가 진단 절차에 "`state validate` 실행 → violations 0건 확인" 단계가 추가된다. violations 있으면 PM Gate 차단

- [ ] **F-11** `opal/core/references/harness/additional-work.md` 행 추가 절차 교체
  - **AC**: 추가작업 진입 시 행 삽입이 `state add-row --after {N} --stage CLOSE --item ...`로 표기된다

- [ ] **F-12** `opal/core/references/opal-harness-interactive.md` + `opal-harness-agentic.md` Gate 후 STATE 갱신 절차 교체
  - **AC**: "QA Gate 완료 즉시 — State Gate"의 갱신 동작이 `state mark --row {N} --done`으로 표기된다. agentic의 자율 통과는 `state mark --row {N} --done --auto-pass`로 표기

- [ ] **F-13** `opal/core/references/opal-harness.md` §3 + §9 갱신
  - **AC**: §3 stub에 `state-tool` [MUST] 추가, §9 도구 테이블에 `state-tool` 행 추가 (트리거: TASK 단계 시작 / Gate 직후 / 추가작업 진입)

- [ ] **F-14** `opal/core/AGENT.md` STATE 표현 정합성 갱신
  - **AC**: 본문 중 STATE 갱신 표현이 새 흐름과 일치하도록 수정 (구체 위치는 PLAN에서 본문 검토 후 결정)

- [ ] **F-15** 8개 오케스트레이터 SKILL.md 갱신
  - **대상**: `opal-pilot-dev`, `opal-pilot-dev-short`, `opal-pilot-dev-wireframe`, `opal-pilot-gc`, `opal-pilot-project`, `opal-pilot-project-dev`, `opal-pilot-sdd`, `opal-pilot-write-tech`
  - **AC**: 각 SKILL.md의 "STATE.md 도메인 치환값" 섹션은 `state-tool`이 모드/스킬별로 자동 생성하도록 매핑 명시. 본문 중 "STATE.md 갱신" 표현이 `state-tool` 호출로 교체. 모드/스킬별 행 구성 매핑 위치(SKILL.md 유지 vs state-tool 내부 하드코딩)는 PLAN에서 결정

- [ ] **F-16** 3개 단계 스킬 갱신
  - **대상**: `op-task/SKILL.md`, `op-dev-analysis/SKILL.md`, `op-dev-execute/references/execute-guide.md`
  - **AC**: 각 파일에 "STATE 갱신은 `state init` 또는 `state mark --as-worker`로만 수행한다 (자기 단계 한정)" [MUST] 추가. 기존 STATE 갱신 표현 교체

- [ ] **F-17** 8개 에이전트 정의 갱신 ⭐신규
  - **대상**: `agents/opal-{be, db, fe, plan, sdd-action, task, task-action}-agent/AGENT.md`, `agents/opal-planning-agent/personas/service-planner.md`
  - **AC**: 각 에이전트 정의에서 STATE 갱신 책임 표현이 `state-tool` 호출로 일관되게 갱신된다. 워커 권한 게이트(T-10)와 정합성 확인

- [x] **F-18** 가이드 문서 12개 분류 + 갱신 ⭐신규
  - **대상**: B 카테고리 12개 (project-dev 6, sdd 3, gc 1, harness 2)
  - **AC**: PLAN 단계에서 grep + 본문 분석으로 "실질 갱신" vs "단순 참조"를 분류. 실질 갱신 항목만 본문 수정. 분류 결과는 PLAN.md에 명시

- [ ] **F-19** 도구 등록부 갱신 ⭐신규
  - **대상**: `opal/core/references/tools.md`
  - **AC**: `state-tool` 사용법(서브 명령 7종, 응답 형식, 종료 코드)이 등록된다. xlsx-tool 등록 형식과 일관

### 배포 요구사항

- [ ] **F-20** `scripts/install-mac.sh` 갱신
  - **AC**: `state-tool/` 디렉토리가 `~/.opal/tools/state-tool/`로 정상 복사되며 `run.sh`가 실행 권한(chmod +x)을 가진다. .venv 사전 조건은 xlsx-tool과 동일하므로 추가 설정 불필요

### 검증 요구사항

- [ ] **F-21** 단위 테스트
  - **AC**: 7개 서브 명령 각각의 happy path + 주요 에러(권한 위반, 순서 위반, 마커 손실, 멱등성 위반) 시나리오에 대해 단위 테스트가 통과한다. 테스트 위치는 PLAN에서 결정

- [ ] **F-22** 회귀 테스트 (134 자기 자신)
  - **AC**: 본 태스크의 STATE.md를 EXECUTE 끝에서 `state init --import-existing` 으로 흡수하여 state.json 생성. 이후 CLOSE State Gate까지 `state-tool`로 정상 진행. `state validate` violations 0건 반환

- [ ] **F-23** 추가 회귀 표본 — PLAN에서 결정
  - **AC**: dummy 태스크를 별도 만들어 모드(interactive/agentic) × 오케스트레이터(opp 외 1종) 양쪽 검증. 표본 수는 PLAN에서 결정

## 제약 조건

- **개발/배포 경계**: 본 태스크는 "개발" 범위 (`opal/.opal/AGENT.md` §개발 vs 배포 경계 원칙). `~/.opal/`에 직접 복사·실행은 금지. 배포는 캡틴의 별도 지시로 `install-mac.sh`를 통해 수행
- **`~/.opal/` 직접 수정 금지** (`opal/.opal/AGENT.md` §확정 기준 #2): 모든 수정은 `opal/` 소스 경로에서 수행. 매핑 — `~/.opal/AGENT.md` → `opal/core/AGENT.md`, `~/.opal/references/` → `opal/core/references/`, `~/.opal/skills/` → `opal/skills/`, `~/.opal/agents/` → `opal/agents/`, `~/.opal/tools/` → `opal/tools/`
- **레거시 호환**: 기존 STATE.md(이미 완료된 태스크 ~133)는 소급 변경하지 않는다. `state init`은 신규 태스크부터 적용. 134 자기 자신은 회귀 테스트로 마이그레이션 (T-13)
- **Python 의존성 제약**: `~/.opal/.venv/bin/python` 사용 + 표준 라이브러리만 import. `requirements.txt` 변경 없음
- **에스케이프 해치**: `--force` 플래그(권한·멱등성 우회) 사용 시 STATE.md "의사결정 로그"에 자동으로 경고 항목 추가 (예: "force flag used at row N — reason required")
- **모드별 행 구성 차이**: interactive vs agentic 모드의 행 구성이 다르므로(`opal/core/references/harness/state-template.md` §파이프라인 현황판 행 구성 규칙), `init`이 모드를 받아 적절히 구성. agentic 모드는 일부 사용자 확인 행이 `na`(-) 으로 자동 채워짐
- **마이그레이션 순서 엄수** — 도구 구현 → 단위 테스트 통과 → 하네스 §3+§9 갱신 → state.md/state-template.md/task-process.md 갱신 → op-task 갱신 → opp(opal-pilot-project) 갱신 → 134 자기 자신 회귀 → 나머지 pilot 일괄 → 단계 스킬 → 에이전트 → 가이드 → 도구 등록부. 각 단계 통과 전 다음 단계 진입 금지

## 기술 스택

- **언어**: Python 3 (표준 라이브러리만)
- **출력 형식**: JSON (OPAL Tools 표준)
- **셸 래퍼**: `run.sh` (bash) — `~/.opal/.venv/bin/python` 호출 (xlsx-tool 패턴)
- **스키마**: JSON Schema Draft-07
- **시점 취득**: `node ~/.opal/tools/date/date.js datetime` (subprocess)
- **배포**: `scripts/install-mac.sh`

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §3 State 모듈 stub, §9 OPAL Tools 도구 우선 원칙 |
| D-2 | 설계 | harness/state.md | `opal/core/references/harness/state.md` | 현재 STATE 갱신 로직 본체 (★ 가장 큰 변경 대상) |
| D-3 | 설계 | harness/state-template.md | `opal/core/references/harness/state-template.md` | 파이프라인 현황판 행 구성 규칙 + 마이그레이션 시 LLM 직접 작성 금지 명시 |
| D-4 | 설계 | harness/task-process.md | `opal/core/references/harness/task-process.md` | TASK 단계 STATE.md 생성 절차 |
| D-5 | 설계 | harness/pm-review-gate.md | `opal/core/references/harness/pm-review-gate.md` | PM Gate 검증 절차에 `state validate` 추가 |
| D-6 | 설계 | harness/additional-work.md | `opal/core/references/harness/additional-work.md` | 추가작업 행 추가 규칙 |
| D-7 | 설계 | opal-harness-interactive.md | `opal/core/references/opal-harness-interactive.md` | interactive 모드 Gate 후 STATE 갱신 |
| D-8 | 설계 | opal-harness-agentic.md | `opal/core/references/opal-harness-agentic.md` | agentic 모드 PM 대행 갱신, auto-pass |
| D-9 | 설계 | opal-pilot-project SKILL.md | `opal/skills/opal-pilot-project/SKILL.md` | STATE.md 도메인 치환값 — 마이그레이션 표본 |
| D-10 | 소스 | xlsx-tool 본체 | `opal/tools/xlsx-tool/run.sh:1-13` | OPAL Tools 구현 패턴 — venv 호출 + JSON 출력 |
| D-11 | 소스 | xlsx-tool Python | `opal/tools/xlsx-tool/xlsx-tool.py` | argparse + JSON 응답 형식 참조 |
| D-12 | 설계 | .opal/AGENT.md | `opal/.opal/AGENT.md` | 개발/배포 경계 원칙, `~/.opal/` 직접 수정 금지, 매핑 규칙 |
| D-13 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 산출물 인용 규칙 |
| D-14 | 설계 | opal-pm.md | `opal/core/references/opal-pm.md` | PM 검토 게이트 / 자가 진단 절차 (state validate 통합 위치) |
| D-15 | 외부 | JSON Schema Draft-07 | [JSON Schema](https://json-schema.org/draft-07/json-schema-release-notes.html) | F-3 스키마 표준 |

## 미확정 사항 (PLAN에서 결정)

- [MUST] `opal/core/references/harness/citation-rules.md` §0: "상상·추정·기억 기반 기재 금지 — 모든 분석·설계 결정은 문서 근거(경로/URL + 섹션/줄번호)를 인용해야 한다."

다음 항목은 PLAN 단계에서 워커가 조사·결정한다:

1. **영향 범위 재검증** — B 카테고리(가이드 12개)의 "실질 갱신 vs 단순 참조" 분류, 에이전트(agents/) 8개의 STATE 갱신 책임 본문 검토. 영향 합계가 ~42 → ±N 으로 정정될 수 있음 (PLAN 첫 Step에 grep + 본문 검증 명시)
2. **모드×스킬별 행 구성 매핑 위치** — 8개 SKILL.md "STATE.md 도메인 치환값"에 분산 vs `state-tool` 내부 하드코딩 — 결합도/유연성 트레이드오프 결정
3. **워커 권한 검증 방식 상세** — `--as-worker --worker-stage <stage>` 명시 인자 vs 환경 변수(`OPAL_WORKER_STAGE`) vs 디스패치 컨텍스트(`[WORKER]` 마커와의 통일성). 현재 워커 프롬프트 패턴 분석 필요
4. **마이그레이션 시점의 백업 정책** — 기존 STATE.md를 변경하는 하네스 갱신 직전에 자동 백업할지, 캡틴이 git 커밋으로 충분한지
5. **에스케이프 해치 감사 로그** — STATE.md 의사결정 로그 자동 기재 외에 별도 감사 로그 파일(`tasks/{NNN}/.audit.log`)을 둘지
6. **회귀 테스트 표본 수** — F-23 dummy 태스크 1건으로 충분한지, 모드 2종 × 오케스트레이터 2종 = 4종 매트릭스로 갈지
7. **`state init --import-existing` 파싱 정확도** — 마크다운 표 정규식 파싱이 모든 기존 STATE.md를 처리할 수 있는지. 처리 불가 시 fallback 정책
8. **단위 테스트 위치** — `opal/tools/state-tool/tests/` vs 별도 테스트 디렉토리. 기존 도구의 테스트 컨벤션 확인 필요
9. **`opal/core/AGENT.md` STATE 표현 갱신 범위** — 본문 grep 결과 정확한 라인 식별 후 결정
