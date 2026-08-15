# ANALYSIS: 파이프라인 사용자 확인 행 — 자동 승인 경로 일원화

> 작성일: 2026-08-15
> 입력: TASK.md
> 출력: ANALYSIS.md
> 코드 루트: `/Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_093/` (HEAD `d58a5df`, 092 포함)
> 문서 루트: `/Volumes/Data/AiStudio/workspace/opal/tasks/093-260815-opd-사용자확인행-자동승인-일원화/`

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| R-0 | 기획 | TASK.md | `tasks/093-260815-opd-사용자확인행-자동승인-일원화/TASK.md` | 요구사항 F-1~F-6, 확정 설계 방향 R-1~R-6 원본 |
| R-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` (코드 루트) | 변경 본체 — auto-na 3분기, 가드, mark/advance, 판정 로직 |
| R-2 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` (코드 루트) | 회귀 기준 — auto-na 고정 테스트 전수 식별 |
| R-3 | 소스 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` (코드 루트) | status enum·mode enum SSOT |
| R-4 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` (코드 루트) | CLOSE 진입 게이트/커밋 규칙 Guards |
| R-5 | 설계 | opal-harness-agentic.md | `opal/core/references/opal-harness-agentic.md` (코드 루트) | agentic `--auto-pass` 지시 SSOT — F-6 정합 대상 |
| R-6 | 설계 | opal-harness-semi-agentic.md | `opal/core/references/opal-harness-semi-agentic.md` (코드 루트) | semi-agentic `--auto-pass` 지시 SSOT — F-6 정합 대상 |
| R-7 | 설계 | opal-pilot-* SKILL.md 10종 | `opal/skills/opal-pilot-*/SKILL.md` (코드 루트) | pilot 문서의 `--auto-pass` PM 지시 지점 — F-6 정합 대상 |
| R-8 | 소스 | 092 state.json | `tasks/092-260815-opd-워크트리-작업공간-분리/state.json` | 결함 실측 증거 — na/done 혼재, note 이중 접두 3건 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조.

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/state-tool/state_tool.py` | 상태 초기화·전이·게이트·검증 전체 로직 본체 | O | `:50-54`(경계 상수), `:456`(완료 집합), `:481`(todo na 중립), `:634-679`(전이 가드), `:685-723`(CLOSE 게이트), `:785-924, 1021-1058`(빌더 3종 auto-na), `:1409-1457`(advance), `:1474-1660`(mark), `:1691-1748`(validate) |
| `opal/tools/state-tool/tests/test_state_tool.py` | 6084줄 — 9개 명령 happy path + 23종(현 44종) 에러 코드 회귀 | O(회귀 확인) | `:293-309`, `:2200-2221`, `:4795-4840`(§1.5 상세) |
| `opal/tools/state-tool/schema/state.schema.json` | rows[].status enum SSOT | 불필요(존치) | `:69`(status enum에 `na` 존치 — R-6 하위호환) |
| `opal/tools/state-tool/todo_mirror_hook.py` | todo_mirror 페이로드를 세션 네이티브 todo에 주입하는 PostToolUse 훅 | 확인 필요(간접 영향) | `build_todo_mirror` 소비자 — §3.2 |
| `opal/core/references/opal-harness-agentic.md` | agentic `--auto-pass` PM 명시 호출 지시 SSOT | O | `:70, 81-86, 91, 156`(§4 절차) |
| `opal/core/references/opal-harness-semi-agentic.md` | semi-agentic `--auto-pass` PM 명시 호출 지시 | O | `:44, 54-55, 60` |
| `opal/core/references/opal-harness.md` | Guards — CLOSE 진입 게이트·커밋 규칙 | 확인 필요(F-2 훅과 상충 없음 확인) | `:33` |
| `opal/skills/opal-pilot-dev/SKILL.md` 외 pilot 9종 | 단계별 사용자 확인 행 mark 지시(P-8) | O | §1.6 표 참조 |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | "조건부 행 자동 na 처리는 미구현" 서술 — F-1 이후 오기재화 | O | `:158` |

### 1.2 아키텍처 패턴

- `state_tool.py`는 서브커맨드 디스패치형 CLI(`build_parser` → `cmd_*` 함수)이며, 모든 검증은 `save_state_json()` 이전 순차 가드 함수 호출(`check_stage_transition_guard` → `check_close_gate` → `_run_clarification_hook` → (`cmd_mark` 전용) semi-agentic 경계 검사 → `check_gate_artifacts`)로 구성된다 — 상태 변경 전 전량 통과가 원칙(부분 상태 변경 회피, `:1531` 주석 "H-1 — save_state_json() 이전 검증 구간").
- 에러 코드는 `ERROR_CODES` 딕셔너리 단일 SSOT(`:81-133`)에 모이며, `err()` 헬퍼(`:155`)가 이를 참조해 표준 JSON 에러 응답을 방출한다. F-4 신규 에러 코드는 이 패턴을 따라야 한다.
- "행 완료 여부" 판정은 `_COMPLETE_STATUSES = {"done", "additional_work_done", "na"}` 단일 상수(`:456`)로 위임되어 있고, 가드 함수(`check_stage_transition_guard`)는 이 집합만 참조 — na 존치 시 이 지점은 변경 불필요.
- "자동 승인 가능 여부" 판정은 반대로 **단일 지점에 위임되어 있지 않고 4곳에 하드코딩 중복**(§1.5 배경분석 (6) 그대로 확인됨) — F-3의 통합 대상.

### 1.3 의존성 맵

```
cmd_init ── build_rows_from_spec / build_rows_from_skill_md / build_rows_from_pipeline_json
              └─ (agentic 분기 3곳, 동일 패턴 복붙) → row["status"]="na"

cmd_advance / cmd_mark
  ├─ check_stage_transition_guard(state, row_index, command, force, scope)
  │     └─ _COMPLETE_STATUSES 참조 (na 포함)
  ├─ check_close_gate(state, row_index, command, auto_pass, force)
  │     └─ MODE_BOUNDARY_STAGES 무관 — CLOSE는 전 모드 owner=user 필수(무조건)
  ├─ _run_clarification_hook(...)
  ├─ (cmd_mark 전용) semi-agentic 사전 검사: `row["stage"] in MODE_BOUNDARY_STAGES` (`:1527`)
  └─ check_gate_artifacts(...)

cmd_validate
  └─ 사후 검증: owner in (user,auto) 아니면 위반 / interactive+auto → 위반 / semi-agentic+auto+MODE_BOUNDARY_STAGES → 위반

build_todo_mirror(state, action)  ← cmd_init/advance/mark/block 공통 소비
  └─ effective = [s for s in statuses if s != "na"]  (na 중립)

todo_mirror_hook.py  ← ok() stdout의 todo_mirror 필드를 PostToolUse에서 소비(간접 소비자, 코드 미변경 대상이나 na 제거로 인한 effective 재계산 영향 없음 — pending도 동일 취급되므로 무영향)
```

- import/require 없음(표준 라이브러리 단일 파일, `:6` 설명 "9개 명령 ... 외부 의존 없음"과 일치).
- `run.sh`가 `state_tool.py`를 subprocess로 감싸는 유일한 진입점(테스트 다수가 `_run070`류 헬퍼로 subprocess 실호출).

### 1.4 테스트 현황

- 단일 테스트 파일 6084줄, `unittest` 기반. 클래스 단위로 기능 묶음(`TestPipelineSpecValidate`, `TestPipelineJsonInit`, `TestTaskStepGate` 등).
- 직접 호출(`ST.cmd_mark` 등) 경로와 `run.sh` subprocess 실호출 경로가 혼재 — CLOSE 게이트·`--task-step` 주소 회귀 테스트는 subprocess 경로 사용(`_run070`, `:4807` 부근).
- na/auto-pass 관련 테스트는 §1.5에서 전수 식별.

## 2. 외부 조사 결과 (해당 시)

해당 없음 — 순수 내부 리팩터링, 외부 라이브러리 의존 없음(`state_tool.py` 표준 라이브러리 기반, `:6` 헤더 설명).

## 3. 영향 범위

### 3.1 직접 영향

- `opal/tools/state-tool/state_tool.py` — 빌더 3곳(auto-na 제거), `cmd_advance`/`cmd_mark`(F-2 훅 삽입), 신규 단일 판정 함수(F-3), `ERROR_CODES`(F-4), mark 멱등성(F-5).
- `opal/tools/state-tool/schema/state.schema.json` — 변경 없음(`na` enum 값 존치, R-6).
- `opal/core/references/opal-harness-agentic.md`, `opal-harness-semi-agentic.md`, `opal/skills/opal-pilot-*/SKILL.md` — `--auto-pass` PM 명시 지시 문구를 신규 훅 계약과 정합(F-6).

### 3.2 간접 영향

- `opal/tools/state-tool/todo_mirror_hook.py` — `build_todo_mirror`의 소비자. na 제거로 `effective` 계산에서 값이 하나 줄지만(더 이상 `!= "na"` 필터 대상 없음) `pending`도 동일하게 `effective`에 남으므로 산출 로직(§4.4 `test_ts005_na_neutral`)은 **결과값이 우연히 동일**하게 유지된다(§1.5 참조) — 코드 변경 불필요하나 회귀 확인 필요.
- 워커 경로(`--as-worker` + `scope="prior_stage_only"`, `:658-665`) — F-2 훅을 어디에 넣든 이 스코프 분기와 상호작용한다(§1.6 삽입 지점 비교의 핵심 리스크).
- `link_memory_history()`(CLOSE 마지막 행 mark 시 발동, `:581-` 부근) — CLOSE 게이트 통과 후에만 실행되므로 F-2/F-3 변경과 직접 충돌 없음. 단, F-2가 CLOSE 직전 행(사용자 확인)을 잘못 자동 승인하면 이 히스토리 연결이 오발동할 위험(§1.6 리스크로 별도 기재).
- 기존 `tasks/*/state.json` 중 agentic 모드로 init된 파일 전체 — 신규 로직 적용 후에도 읽기 경로(`_COMPLETE_STATUSES`, `check_stage_transition_guard`)가 그대로 `na`를 완료로 인정하므로 즉시 깨지지 않음(§1.4 하위호환 분석).

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음
- [ ] API 인터페이스 변경 — CLI 인자 자체는 변경 없음(F-2는 기존 `advance`/`mark` 내부 동작 확장). 단, F-4 신규 에러 코드 1~2종은 `ERROR_CODES` 계약 확장(하위호환 유지, 추가만)
- [ ] 설정/환경변수 변경 — 없음
- [x] 빌드/배포 파이프라인 변경 — 없음(전역 배포는 CLOSE 이후 캡틴 수동 `install-mac.sh` 실행, TASK.md 제약 그대로)

## 4. 핵심 발견 사항

1. **auto-na는 "완료 처리"가 아니라 "가드 우회용 플레이스홀더"다.** `_COMPLETE_STATUSES`(`:456`)에 포함되어 건너뛰기 가드는 통과하지만 `timestamp`가 영구히 `null`로 남고, `build_todo_mirror`에서도 명시적으로 `na` 문자열을 하드코딩 필터링(`:481`)해야 할 정도로 "정상 상태값이 아닌 예외"로 취급되고 있다. R-1(전 모드 `pending/PM` 통일)은 이 예외 분기를 완전히 제거하는 것으로, 코드베이스 자체에 이미 "na는 특별 취급이 필요한 이물질"이라는 흔적이 여러 곳(`:456`, `:481`, `:639`)에 남아 있어 근거가 명확하다.

2. **"자동 승인 가능 여부" 판정이 실제로는 3곳(4곳 아님)에 분산되어 있고, 그중 CLOSE 게이트는 모드 무관 상수 규칙이라 통합 대상에서 성격이 다르다.** TASK.md는 4개 지점(`:50`, `:716`, `:1525-1529`, `:1718-1730`)을 언급하지만, 실측 결과 `check_close_gate`(`:685-723`)는 `MODE_BOUNDARY_STAGES`를 전혀 참조하지 않고 "CLOSE 첫 행이면 무조건 auto_pass 거부 + 무조건 owner=user 요구"라는 **모드 독립 상수 규칙**이다. 반면 나머지 3곳(`MODE_BOUNDARY_STAGES` 정의부 `:50`, `cmd_mark`의 semi-agentic 사전검사 `:1525-1529`, `cmd_validate`의 사후검사 `:1725-1731`)만 "모드별 경계"를 실제로 갈라 쓰는 지점이다. 즉 F-3 단일 판정 함수는 **"CLOSE 여부"(무조건 거부)**와 **"MODE_BOUNDARY_STAGES 소속 여부"(semi-agentic 한정 거부)**라는 서로 다른 두 축을 하나의 함수 시그니처(`stage, mode` → bool)로 합성해야 하며, CLOSE는 `MODE_BOUNDARY_STAGES` 집합에 원래 없어(`:50-54`) 두 조건이 상호 배타적이므로 순서 문제는 실질적으로 없다.

3. **interactive 모드는 mark 시점에 auto_pass를 막는 코드가 전혀 없다 — `cmd_validate`가 사후에만 위반으로 잡아낸다.** `cmd_mark`(`:1474-1660`) 전체를 훑어도 `mode == "interactive"`를 검사하는 분기가 없다(`grep interactive` 결과 `:1709, :1719`만 존재하며 둘 다 `cmd_validate` 내부). 즉 현재 코드에서 interactive 모드로 `mark --auto-pass`를 호출하면 **성공적으로(exit 0) `owner=auto/done`이 저장되며, 오직 별도로 `state validate`를 실행해야만 `auto_pass_in_interactive_mode` 위반이 사후 발견된다.** TASK.md R-3 "interactive 불가"는 회귀 테스트(`test_auto_pass_in_interactive_mode`, `:856-865`)상으로도 "mark 자체는 통과하고 validate만 위반을 낸다"는 사실을 그대로 재확인시킨다. F-3/F-4 설계 시 이 지점을 **mark 시점 즉시 차단(exit 1)으로 승격할지, 기존처럼 사후 validate 위반으로 유지할지**를 결정해야 하며, TASK.md 문면상 R-4("전용 에러 반환")은 즉시 차단을 요구하는 것으로 읽히므로 이 갭이 F-4 구현 범위에 포함되어야 한다.

4. **F-2 자동 승인 훅과 "워커 스코프"(`--as-worker` + `scope=prior_stage_only`)의 상호작용이 가장 큰 설계 리스크다.** 실측 테스트 `test_close_gate_regression_via_task_step_addressing_subprocess`(`:4807-`)의 주석 자체가 "opp 스펙 row 2/5/8(사용자 확인)은 agentic 자동 na로 이미 완료 — 나머지만 mark"라고 명시한다. F-1로 이 행들이 `pending`이 되면, F-2 훅이 **정확히 언제(어느 mark/advance 호출 시점에) 몇 단계 앞의 미완 사용자 확인 행까지 자동 승인하는지**가 정의되지 않으면 이 테스트류가 `stage_transition_violation`으로 즉시 깨진다. 훅이 "직전 1단계"만 처리하는지 "모든 선행 미완 행"을 처리하는지에 따라 워커 경로(`prior_stage_only`, 자기 단계 앞 stage만 봄)와의 정합이 갈린다 — §1.6에서 3개 삽입 지점 후보별로 이 리스크를 분리 평가한다.

5. **092 state.json 실측 결과, note 이중 접두 결함은 TASK.md가 지목한 2건(rows 5·8)이 아니라 3건**(row_id 미상 3곳, `note` 필드에 `"agentic auto-pass: agentic auto-pass: ..."` 패턴 — PM Gate 강화 검토/PLAN PM Gate/목표-커버 게이트 관련 3개 행) 확인됨(`tasks/092-.../state.json:71, 116, 163`). F-5 멱등성 수정의 회귀 시나리오로 이 3건 모두를 커버해야 한다.

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| CLOSE 게이트와 F-2 훅 충돌 가능성 | F-2 훅이 "다음 단계 첫 행 진입 시 앞 단계 미완 사용자 확인 행 자동 승인"을 CLOSE 진입에도 적용하면, CLOSE 직전 행을 owner=auto로 자동 마킹해버려 `check_close_gate`가 요구하는 owner=user 요건을 우회하는 심각한 회귀가 된다 | 높음 | `state_tool.py:685-723`(CLOSE는 전 모드 owner=user 강제), TASK.md R-3("CLOSE 직전은 전 모드 불가") |
| 워커 스코프(`prior_stage_only`)와 F-2 훅 순서 미정의 | F-2가 `cmd_mark`/`cmd_advance` 가드 구간에 삽입될 경우, 워커 경로(`scope="prior_stage_only"`)가 자기 단계 이전만 검증하는 것과 달리 F-2 훅이 몇 단계 전까지 자동 승인 대상으로 스캔할지 미정 — 무한정 앞으로 스캔 시 워커 권한 게이트(`:1499-1509` `worker_scope_violation`)를 우회해 워커가 자기 단계 밖 행을 실질적으로 갱신하는 효과가 발생할 수 있음 | 높음 | `state_tool.py:634-679`(scope 분기), `:1498-1509`(워커 권한 게이트), `tests/test_state_tool.py:4807-4840`(실측 회귀 시나리오) |
| interactive 모드 mark 시점 auto_pass 미차단 | 현재 `cmd_mark`에 interactive 모드 전용 즉시 차단 로직이 없어 F-4("전용 에러 반환")를 mark 시점에 신설하려면 새 분기 추가가 필요 — 기존 `test_auto_pass_in_interactive_mode`(사후 validate 위반 기대)와 신규 즉시 차단 기대가 동일 테스트명 하에서 충돌할 수 있음 | 중간 | `state_tool.py:1474-1660`(cmd_mark 전체, interactive 분기 부재), `tests/test_state_tool.py:856-865, 1195-1200` |
| na 중립 테스트의 의미 약화 | `test_ts005_na_neutral`(`:5356-5367`)은 F-1 적용 후에도 "우연히" 동일 결과(pending)를 반환해 그린으로 남지만, 테스트가 원래 검증하려던 "na 필터링 로직"은 더 이상 그 경로를 타지 않게 되어 테스트의 의도와 실제 검증 대상이 어긋난다 | 낮음 | `state_tool.py:481`(na 필터), `tests/test_state_tool.py:5356-5367` |
| 092 state.json 등 in-flight agentic 파일의 CLOSE 진입 실측 미확인 | 092 태스크가 아직 CLOSE 전이라면 F-1/F-2 배포 후 그 파일이 실제로 CLOSE까지 무사고로 진행되는지 실측 검증이 필요(스키마 통과만으로는 불충분, 게이트 로직 변경의 실동작 확인 필요) | 중간 | `tasks/092-260815-opd-워크트리-작업공간-분리/state.json` |
| 문서-코드 불일치: `MODE_BOUNDARY_STAGES` 지점 개수 | TASK.md 배경분석 (6)은 판정 지점을 4곳(`:50, :716, :1525-1529, :1718-1730`)이라 서술하나, 실측상 `:716`(`check_close_gate`)은 `MODE_BOUNDARY_STAGES`를 참조하지 않는 별개 규칙(모드 무관 CLOSE 상수 규칙)이다 — PM 보고 필요 | 중간 | `state_tool.py:685-723`(전체 함수 본문에 `MODE_BOUNDARY_STAGES` 미참조) |

> **문서/코드 불일치 보고**: TASK.md 배경분석 (6)·F-3 "어디에" 항목이 지목한 4개 판정 지점 중 `check_close_gate`(`:685-723`)는 실측상 `MODE_BOUNDARY_STAGES`를 전혀 사용하지 않으며, "CLOSE 첫 행이면 모드에 상관없이 무조건 owner=user 필요"라는 별도의 상수 규칙으로 구현되어 있다. F-3 통합 시 이 두 축(모드별 경계 vs CLOSE 무조건 규칙)을 혼동하지 않도록 PM 검토가 필요하다.

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어 | Python | 3.14 (`~/.opal/.venv`, TASK.md §기술스택) |
| 실행 대상 | `state_tool.py` | 표준 라이브러리 전용, 외부 의존 없음(`:6` 헤더) |
| 테스트 | pytest/unittest | `opal/tools/state-tool/tests/test_state_tool.py` (unittest 기반) |
| 스키마 | JSON Schema draft-07 | `opal/tools/state-tool/schema/state.schema.json:2` |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| (해당 없음) | 순수 Python 표준 라이브러리 리팩터링 — 프레임워크 특화 스킬 불필요 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| (해당 없음) | 외부 라이브러리/API 조사 불필요 — 프로젝트 내부 로직 리팩터링 |

## 부록: 상세 근거 (인용 원본)

### A.1 사용자 확인 행 생성·전이 코드 경로 전수 (요구사항 1 대응)

| # | 함수 | 역할 | 경로:줄번호 |
|---|------|------|-------------|
| 1 | `build_rows_from_spec` | `--rows-spec` 인라인 JSON → rows[], agentic 자동 na | `state_tool.py:785-832`(분기 `:824-829`) |
| 2 | `build_rows_from_skill_md` | `--rows-from` SKILL.md 파싱 → rows[], agentic 자동 na | `state_tool.py:834-924`(분기 `:916-921`) |
| 3 | `build_rows_from_pipeline_json` | `--rows-from` pipeline.json → rows[], agentic 자동 na | `state_tool.py:1021-1058`(분기 `:1050-1055`) |
| 4 | `cmd_advance` | pending→in_progress, 전이 가드+CLOSE 게이트+명확화 훅 호출 | `state_tool.py:1409-1457` |
| 5 | `cmd_mark` | done 전환, owner 결정(`--auto-pass`/`--owner`/기본 PM), 멱등성 없음 | `state_tool.py:1474-1660`(owner 결정 `:1561-1575`, note 접두 `:1563-1568`) |
| 6 | `check_stage_transition_guard` | 앞 행 완료 여부 검증(`_COMPLETE_STATUSES` 참조) | `state_tool.py:634-679` |
| 7 | `check_close_gate` | CLOSE 첫 행 owner=user 강제(모드 무관) | `state_tool.py:685-723` |
| 8 | `cmd_validate` | 사후 정합성 검증(owner/mode 조합 위반 탐지) | `state_tool.py:1691-1748`(사용자 확인 검증 `:1708-1732`) |
| 9 | `build_todo_mirror` | todo 미러 집계, na 중립 처리 | `state_tool.py:459-494`(na 필터 `:481`) |

### A.2 mode×stage 자동 승인 판정 현황표 (요구사항 2 대응, F-3 경계 불변 조건 기준)

CLOSE 게이트(owner=user 강제)는 모드·stage 무관 상수 규칙이므로 별도 행으로 분리했다.

| 대상 stage 분류 | interactive | semi-agentic | agentic |
|------------------|-------------|--------------|---------|
| `MODE_BOUNDARY_STAGES`(TASK/ANALYSIS/PLAN/TEST-SCENARIO/SPEC/REVIEW/DESIGN/WBS/WIREFRAME) | mark 시점 미차단(사후 validate만 위반 표시, `:1719`) | `mark --auto-pass` 즉시 거부(`semi_agentic_pre_execute_auto_pass_denied`, `:1527-1529`) | 자동 승인 허용(제약 없음) |
| 그 외 일반 stage(EXECUTE/TEST/QA/VERIFY/SCAN/CHECK/REPORT 등, MODE_BOUNDARY_STAGES 미포함) | mark 시점 미차단(사후 validate만) | 자동 승인 허용(제약 없음, MODE_BOUNDARY_STAGES 밖) | 자동 승인 허용 |
| CLOSE(첫 행) | `--auto-pass` 시도 시 즉시 거부 아님(`auto_pass and mode in (agentic, semi-agentic)` 조건만 체크, `:700` — interactive는 이 조건에 안 걸림) 단 owner=user 미충족 시 `close_gate_violation` | `--auto-pass` 즉시 거부(`agentic_close_gate_requires_user`, `:700-701`) | `--auto-pass` 즉시 거부(`agentic_close_gate_requires_user`, `:700-701`) |

> 주의: interactive + CLOSE 첫 행 + `--auto-pass` 조합은 `:700`의 모드 조건(`agentic`, `semi-agentic`만 검사)에 걸리지 않으므로 `agentic_close_gate_requires_user`로는 거부되지 않고, 이어지는 owner=user 검증(`:717`)에서 `close_gate_violation`으로 거부된다 — 결과적으로 거부되지만 **에러 코드가 다르다**. F-3 통합 시 이 세부 차이가 "경계 불변" 판정에 포함되어야 한다(TASK.md AC "모드×단계 조합에 대한 판정 결과가 변경 전과 동일함을 테스트로 확인").

### A.3 F-2 훅 삽입 지점 후보 비교 (요구사항 3 대응)

| 후보 | 위치 | 워커 스코프(`prior_stage_only`)와의 상호작용 | 멱등성 | 부분 상태 변경 위험 |
|------|------|----------------------------------------------|--------|----------------------|
| (a) `check_stage_transition_guard` 내부 | `state_tool.py:634-679` — 이미 앞 행을 순회하며 완료 여부를 판정하는 루프(`:669-673`) 안에 위치 | 이 함수가 이미 `scope` 인자로 `prior_stage_only`/`full`을 구분하므로 **자동 승인 대상도 동일 스코프로 자연히 제한**된다(워커는 자기 단계 이전 행만 승인, `:658-665` 범위 재사용) — 상호작용이 가장 명확 | 이 함수는 읽기 전용 검증만 수행하고 `err()`만 호출(`:676-678`) — row 딕셔너리를 직접 변경하려면 이 함수의 시그니처/책임을 "검증기"에서 "검증+변경기"로 바꿔야 함(기존 계약 위반 소지) | `err()`가 즉시 `sys.exit`하는 구조이므로, 이 함수 내부에서 여러 행을 자동 승인하다가 중간에 실패하면 `save_state_json` 호출 전(가드는 항상 `save_state_json` 이전에 실행, `:1531` 주석 패턴)이라 **상태 미저장으로 자동 롤백**되어 안전 — 단 이 함수가 `state` 딕셔너리를 in-place로 mutate하면 호출자가 이후 실패해도 이미 메모리상 mutate된 상태로 다른 검증(`check_close_gate`)에 잘못된 값을 넘길 가능성 있음(주의 필요) |
| (b) `cmd_advance`/`cmd_mark`의 가드 구간 전용 훅 | `cmd_advance:1425-1437`(가드 3종 호출부), `cmd_mark:1511-1523`(가드 4종 호출부) 사이에 신규 호출 삽입 | 두 커맨드 모두 이미 `_guard_scope = "prior_stage_only" if ... else "full"`(`:1427`, `:1513`)을 계산해두므로 이 변수를 그대로 재사용 가능 — 단 `cmd_advance`와 `cmd_mark` 두 곳에 동일 로직을 중복 구현해야 함(현재 코드도 가드 3~4종 호출이 두 함수에 거의 동일하게 중복되어 있는 기존 패턴과 일치, `:1425-1437` vs `:1511-1529`) | 신규 함수로 만들 경우 멱등성(F-5)을 처음부터 설계에 반영 가능(이미 done인 행은 no-op) — 가장 통제하기 쉬움 | `save_state_json` 이전 구간에 위치시키면 (a)와 동일하게 안전. 단, 두 함수에 중복 삽입해야 하므로 **한쪽만 수정하고 다른 쪽을 누락하는 실수 위험**이 (a)/(c)보다 큼(TASK.md도 "어디에: cmd_advance/cmd_mark의 가드 구간"이라 지목 — 이 중복 반영이 전제된 것으로 보임) |
| (c) 별도 pre-transition 훅(신규 독립 함수, 두 커맨드가 공통 호출) | 신규 함수(예 `_auto_approve_pending_user_confirmations`)를 만들어 `cmd_advance`/`cmd_mark` 양쪽에서 호출 | (b)와 동일하게 `_guard_scope` 재사용 가능하며, 독립 함수이므로 워커 스코프 계산 로직을 함수 인자로 명시적으로 전달해야 함(암묵적 전역 의존 제거) | 함수 자체가 독립적이라 F-5 멱등성·F-4 에러코드 반환을 한 곳에 응집 — 테스트 대상도 단일 함수로 좁혀져 유닛 테스트 작성이 가장 쉬움 | (b)와 동일하게 `save_state_json` 이전 위치 보장 시 안전. **중복 삽입 위험은 (b)와 동일하게 존재하지만, 로직 자체가 한 곳에 있어 "삽입 누락"이 아니라 "호출 누락"만 신경 쓰면 되므로 리스크가 약간 낮음** |

**권고**: (c) 별도 함수 + `cmd_advance`/`cmd_mark` 양쪽 호출 — TASK.md F-2 "어디에" 조항과 부합하면서(가드 구간에 위치), (a)처럼 기존 순수 검증 함수의 책임을 오염시키지 않고, (b)처럼 로직 중복 없이 한 곳에서 멱등성(F-5)·에러 반환(F-4)을 함께 구현할 수 있다. 단, PM은 F-3 단일 판정 함수를 이 신규 함수(c)가 호출하도록 설계해 "판정"과 "집행"의 책임을 분리해야 한다(판정=F-3 함수, 집행=F-2 신규 함수).

### A.4 `na` 하위호환 영향 상세 (요구사항 4 대응)

- `_COMPLETE_STATUSES = {"done", "additional_work_done", "na"}`(`:456`) — 변경 없음. F-1은 "신규 생성"만 막을 뿐 읽기 경로의 `na` 인정을 제거하지 않음(TASK.md R-6과 일치).
- `build_todo_mirror`의 `effective = [s for s in statuses if s != "na"]`(`:481`) — 변경 없음. 기존 `na` 보유 행이 있어도 여전히 중립 처리되어 회귀 없음.
- `state.schema.json:69` `"status": {"enum": ["pending", "in_progress", "done", "failed", "na"]}` — 변경 불필요(제거 시 기존 `na` 보유 state.json이 스키마 검증에서 걸림 — TASK.md 제약과 일치하여 반드시 존치).
- 기존 태스크 `tasks/092-260815-opd-워크트리-작업공간-분리/state.json:20-30` — `status="na", owner="auto", timestamp=null, note="agentic auto-na at init"` 행 실측 확인. F-1~F-5 적용 후에도 이 파일에 대해 `advance`/`mark`/`validate`를 실행할 때 에러 없이 동작해야 한다(F-6 AC (a)).

### A.5 auto-na 고정 회귀 테스트 전수 (요구사항 5 대응)

**F-1 적용 시 직접 깨지는 테스트(assert가 `status == "na"`를 명시적으로 요구) — 2건**:

| # | 테스트 | 경로:줄번호 | 사유 |
|---|--------|-------------|------|
| 1 | `test_init_agentic_auto_na_user_confirmation` | `tests/test_state_tool.py:293-309` | `self.assertEqual(task_user["status"], "na")`(`:304`) — F-1 후 `pending`이 되어 실패 |
| 2 | `test_rows_from_agentic_auto_na` | `tests/test_state_tool.py:2200-2221` | `self.assertEqual(task_user["status"], "na")`(`:2219`) — 동일 사유 |

**F-1만으로는 깨지지 않으나 F-2(자동 승인 훅) 부재 시 깨지는 테스트 — 최소 1건, 설계 확정 전 확인 필요**:

| # | 테스트 | 경로:줄번호 | 사유 |
|---|--------|-------------|------|
| 3 | `test_close_gate_regression_via_task_step_addressing_subprocess` | `tests/test_state_tool.py:4807-4840` | 주석이 "opp 스펙 row 2/5/8(사용자 확인)은 agentic 자동 na로 이미 완료 — 나머지(1,3,4,6,7)만 mark"(`:4826-4827`)라고 명시 — F-1 후 이 행들이 `pending`으로 남아, F-2 훅이 해당 시점까지 이 행들을 자동 승인하지 않으면 row 9(`close.done_md`) mark 시 `stage_transition_violation`으로 실패 |

**논리적으로는 영향받지만 우연히 그린 유지(주의 표시만 필요) — 1건**:

| # | 테스트 | 경로:줄번호 | 사유 |
|---|--------|-------------|------|
| 4 | `test_ts005_na_neutral` | `tests/test_state_tool.py:5356-5367` | F-1 후 TASK 스테이지의 두 행이 모두 `pending`이 되어 `all(s == "pending")` 분기(`:484`)로 여전히 `pending` 결과 — 어서션은 통과하지만 원래 검증 대상(`na` 필터)을 더 이상 실측하지 못함 |

**직접 na를 행 딕셔너리에 수동 주입(초기화 로직과 무관)하여 F-1의 영향을 받지 않는 대조군 — 참고용**:

- `tests/test_state_tool.py:2882-2900`("앞 행이 na면 완료로 간주") — `state["rows"][0]["status"] = "na"`로 수동 설정(init 경로 미사용), `_COMPLETE_STATUSES` 존치로 무영향
- `tests/test_state_tool.py:1248-1260`(`test_g13_agentic_close_gate_auto_pass_rejected`), `:2136-2150`(`test_c6_agentic_auto_pass_close_first_row`) — 둘 다 CLOSE 게이트가 `MODE_BOUNDARY_STAGES`/na와 무관하게 "CLOSE 첫 행 + auto_pass + mode∈(agentic,semi-agentic)"만으로 즉시 거부(`:700-701`)하므로 앞 TASK 행의 na/pending 여부와 무관하게 통과. 단 주석(`:1251` "agentic 모드에서 TASK 사용자 확인 행은 auto-na로 초기화됨")은 F-1 이후 사실과 어긋나는 설명이 되므로 주석 갱신 권고
- `tests/test_state_tool.py:4585-4602`(`test_conditional_field_persisted_as_pure_metadata`) — conditional 메타데이터가 na로 자동전환되지 않음을 검증(대상 행이 item="작업"/"PM Gate"라 애초에 사용자 확인 분기 미해당) — 무영향

**요약**: 직접 깨지는 테스트 **2건**, F-2 미구현 시 깨지는 테스트 **1건**(최소, 실제로는 F-2 훅의 스캔 범위 설계에 따라 opp/opd/opdw 등 pipeline.json 기반 다른 subprocess 회귀 테스트에도 유사 패턴이 있을 수 있어 EXECUTE 단계에서 `grep -n "auto.na로 이미 완료\|agentic 자동 na"` 전체 재확인 권고), 우연히 그린 유지되나 의도 약화 **1건**.

### A.6 pilot 10종 문서 `--auto-pass` PM 지시 지점 전수 (요구사항 6 대응)

F-2 훅 도입 후 "PM이 사용자 확인 행에 `--auto-pass`를 명시 호출해야 한다"는 지시가 자동 훅과 문구상 모순되는 지점 — CLOSE 첫 행 거부 지시(F-2 영향 없음, 그대로 유지)와 **일반 단계 사용자 확인 행 자동 통과 지시**(F-2로 대체되어야 할 지점)를 구분했다.

**일반 단계 자동 통과 지시(F-2 도입 시 "PM 명시 호출" → "훅이 자동 처리"로 수정 필요)**:

| 문서 | 경로:줄번호 | 현재 문구 요지 |
|------|-------------|----------------|
| opal-harness-agentic.md | `opal/core/references/opal-harness-agentic.md:70` | "일반 단계 Gate 통과 시 (`--auto-pass`는 사용자 확인 행 전용)" — PM이 사용자 확인 행에 한해 명시 호출한다는 전제 |
| opal-harness-agentic.md | `opal/core/references/opal-harness-agentic.md:81-86` | `mark ... --auto-pass --note "agentic auto-pass: ..."` 호출 예시 + "명시 시 note에 자동 기재" 설명 |
| opal-harness-semi-agentic.md | `opal/core/references/opal-harness-semi-agentic.md:44, 54-55` | 동일 패턴의 semi-agentic 버전 |
| opal-pilot-dev/SKILL.md | `opal/skills/opal-pilot-dev/SKILL.md:322` | "[MUST] agentic 모드 STATE 갱신: ... `--auto-pass --note '<PM 판단 근거>'` 호출" |
| opal-pilot-dev-short/SKILL.md | `opal/skills/opal-pilot-dev-short/SKILL.md:290` | 동일 패턴 |
| opal-pilot-dev-wireframe/SKILL.md | `opal/skills/opal-pilot-dev-wireframe/SKILL.md:245` | 동일 패턴 |
| opal-pilot-project/SKILL.md | `opal/skills/opal-pilot-project/SKILL.md:195` | 동일 패턴 |
| opal-pilot-gc/SKILL.md | `opal/skills/opal-pilot-gc/SKILL.md:457, 459` | 동일 패턴 |
| opal-pilot-sdd/SKILL.md | `opal/skills/opal-pilot-sdd/SKILL.md:442, 444` | 동일 패턴 |
| opal-pilot-project-loop/SKILL.md | `opal/skills/opal-pilot-project-loop/SKILL.md:435` | "D7 게이트까지 PM이 자율 검토·확정하고(`--auto-pass` + `--note` 근거)" |
| opal-pilot-project-dev/SKILL.md | `opal/skills/opal-pilot-project-dev/SKILL.md:158` | "(조건부 행 자동 `na` 처리는 미구현이며 후속 과제다 — `na`는 현재 init 시점 agentic 사용자 확인 행에만 부여된다.)" — F-1 적용 후 이 서술 자체가 사실과 어긋남(더 이상 `na` 부여 자체가 없음), 전면 수정 또는 삭제 필요 |

**CLOSE 첫 행 거부 지시(F-2와 무관, R-3 "CLOSE 직전은 전 모드 불가"로 그대로 유지 — 수정 불필요, 참고용 전수 목록)**:

- `opal-pilot-data-design/SKILL.md:228, 285`, `opal-pilot-dev-short/SKILL.md:199, 292, 312`, `opal-pilot-dev-wireframe/SKILL.md:163, 246, 251`, `opal-pilot-dev/SKILL.md:267, 324, 345`, `opal-pilot-gc/SKILL.md:345, 461`, `opal-pilot-project/SKILL.md:138, 197, 217`, `opal-pilot-sdd/SKILL.md:299, 446, 452`, `opal-pilot-project-loop/SKILL.md:443, 512`, `opal-pilot-write-tech/SKILL.md:385, 504`, `opal-pilot-project-dev/SKILL.md:785`
- `opal-harness.md:33`, `opal-harness-agentic.md:91, 156, 237`, `opal-harness-semi-agentic.md:60`

## 완료 후 동작

워커는 QA를 직접 호출하지 않는다. 오케스트레이터가 QA 단계 실행 여부를 결정한다.
