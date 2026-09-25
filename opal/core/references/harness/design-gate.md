---
module: design-gate
role: PM 경로(opd/opds coordinator) 독립 설계 게이트 규칙 SSOT
load: stage.design
상속: opal/core/PRINCIPLES.md §4
---

# 독립 설계 게이트

## 적용 범위

PM 경로 태스크에만 적용한다. PM 경로 판정은 `state.json` `rows`에 key `plan.design_gate`가 존재하는지로만 내린다. 저장 행으로 재개하는 기존 태스크, `--no-pm`, opd/opds 이외 Pilot은 이 게이트 코드 경로를 타지 않는다.

## 흐름

1. PLAN 단계에서 `PLAN.md`(`## Findings` 포함)를 작성한다.
2. `TEST-SCENARIO.md`를 작성한다.
3. `op-scenario-gate`를 `gate: design` 입력으로 호출한다. 내부에서 다음 순서로 진행한다.
   1. `state-tool design-gate start <task> --iteration N`
   2. evaluator `design-rubric` phase를 1회 디스패치 — 입력에 `start` 응답의 `bundle_hash`를 `input_bundle_hash`로 함께 전달한다.
   3. `state-tool design-gate record <task> --iteration N --verdict <verdict> --evaluator-result <json> [--rewrite-target ...]` — evaluator 결과 JSON 최상위는 전달받은 `input_bundle_hash`와 `iteration`을 그대로 반환해야 한다(ADD-1, verdict pass|rewrite 전용, input_error 제외).
4. `record`가 `pass`를 반환하면 설계 확인(`plan.user_confirm`)을 진행하고 EXECUTE로 넘어간다.
5. `record`가 `pass`가 아니면 `rewrite-target` 문서를 고쳐 다시 1부터 반복한다.

### 열린 시도와 문서 묶음 변경 (`start` ③-0)

`status=evaluating`인 열린 시도가 있는 상태에서 `start`를 다시 호출하면:

- 현재 문서 묶음 hash가 열린 시도의 `bundle_hash`와 **같으면** `design_gate_attempt_open`으로 거부한다(먼저 `record` 필요).
- 현재 문서 묶음 hash가 열린 시도의 `bundle_hash`와 **다르면**(PM이 record 전에 문서를 다시 고친 경우) 그 열린 시도를 history에 `verdict: superseded`로 닫아 회차를 소비하고, `gate.resolved`(`summary`에 superseded 명시, `data.verdict: rejected`)를 남긴 뒤 새 `start` 절차를 계속 진행한다.

## run-log 계약

`start` 통과 시 gate.requested, `record` 시 gate.resolved를 상태 변경과 같은 커밋으로 남긴다. `gate_id=design-gate-i{N}`을 사용하고, `data.verdict`는 run-log 폐쇄 enum(`approved`/`rejected`/`auto`)을 따라 pass→`approved`, 그 외→`rejected`로 쓴다. 설계 게이트 verdict 원문(pass/rewrite/input_error 등)은 run-log `data.verdict`에 담지 않고 `summary`와 `design_gate.history`에 남긴다.

`design_gate.history[].verdict`는 `pass`·`rewrite`·`input_error`·`deterministic_fail`·`superseded` 5값만 쓴다. `deterministic_fail`은 `start` ⑦ 결정론 검사 실패 시도, `superseded`는 위 ③-0에서 record 없이 닫힌 시도를 기록한다.

## 결정론 검사 항목 (`design-gate start` ⑦)

1. sdlc-v2 TASK 필수 5절 존재
2. 기존 PLAN 계약 검사 전 항목 + strict: TASK의 모든 AC/C가 어느 Work item `완료 기준 연결`에도 없으면 `uncovered requirement AC-N`(시나리오 연결 여부와 무관하게 적용)
3. PLAN `## Findings`에 H3 `직접 변경`·`회귀 확인`·`문서 갱신`·`미확인 가정`이 모두 존재하고 본문이 비지 않음(`없음.` 허용)
4. `회귀 확인`의 백틱 경로가 어느 Work item `변경 대상`에 있거나 `직접 변경`·`문서 갱신`에도 있으면(superset) `regression target listed as change`
5. `직접 변경`·`문서 갱신`의 백틱 경로가 어느 Work item `변경 대상`에도 없으면 `finding not in work items`(④⑤의 경로 판정: 백틱 토큰이 `/`를 포함하거나 마지막 확장자가 알려진 파일 확장자일 때만 경로로 보고, `os.replace`·`json.loads`·`v1.2` 같은 코드 심볼·버전 표기는 무시한다)
6. `미확인 가정` 항목은 `없음` 또는 PLAN `## Risks`에 존재하는 `H-N` 참조를 포함
7. `test-tool scenario-coverage-build --template sdlc-v2` + `scenario-coverage-check`를 subprocess로 실행해 exit 0을 요구(16→missing 병합, 17→`input_error`)

`verify --plan-contract-check`는 strict 없이 기존 동작을 유지한다.

## EXECUTE 가드 적용 시점

`execute.implement` 진입 가드(설계 게이트 pass·TASK 요구 hash·통과·승인 hash 일치 확인)는 `execute.implement` 행이 `pending`인 진입 전이 시점에만 적용한다. 다른 행의 advance/mark나 이미 `in_progress`/`done`인 `execute.implement`에는 재적용하지 않는다.

## 문서 묶음 해시와 확인 해시

- 대상 문서는 태스크 폴더의 `TASK.md`, `PLAN.md`, `TEST-SCENARIO.md`다.
- 묶음 hash = `sha256("TASK.md\n"+h1+"\nPLAN.md\n"+h2+"\nTEST-SCENARIO.md\n"+h3)`(h1~h3은 각 파일의 sha256).
- 대상 파일이 없으면 `design_gate_input_missing`.
- TASK 요구 hash = TASK.md `## Constraints`·`## Acceptance criteria` 본문의 sha256.
- `task.user_confirm`이 done이 되는 순간 TASK 요구 hash를 `task_confirm_req_hash`에 기록한다.
- `plan.user_confirm`이 done이 되는 순간 현재 묶음 hash가 `passed_bundle_hash`와 다르면 `design_bundle_mismatch`로 거부하고, 같으면 `approved_bundle_hash`에 기록한다.
- 자동 승인이 허용되지 않는 mode에서 `--owner user` 없이 확인 행을 mark하면 `user_confirmation_required`로 거부한다.

## rewrite 대상과 재판정 조건

- `record`의 `--verdict rewrite`는 `--rewrite-target plan|scenario|both`를 필수로 요구한다.
- 직전 verdict가 rewrite였던 다음 `start`에서는 `last_rewrite_target` 문서(plan→PLAN.md, scenario→TEST-SCENARIO.md, both→둘 다)의 hash가 직전 시도와 같으면 `rewrite_target_unchanged`로 거부한다(상태 불변). `both`는 PLAN.md·TEST-SCENARIO.md 둘 중 하나라도 hash가 불변이면 거부한다(둘 다 바뀌어야 통과).
- `start` 통과 시 `passed_bundle_hash`·`approved_bundle_hash`를 삭제해 이전 승인을 무효화한다.
- `record`의 거부(`design_gate_input_changed`·`design_gate_result_stale`·`design_gate_result_invalid`·`design_gate_verdict_mismatch`)는 상태를 바꾸지 않고 시도를 열린 채 둔다(회차 미소비). `iteration`은 마지막으로 시작된 시도 번호이며 결정론 실패 시도도 1회로 센다.
- `--verdict pass|rewrite`는 `--evaluator-result` JSON 최상위 `input_bundle_hash`가 현재 열린 시도의 `bundle_hash`와 같고 `iteration`이 `--iteration` N과 같아야 한다(ADD-1, 157) — 없거나 다르면 `design_gate_result_stale`로 거부한다. 검사 순서는 열린 시도·회차 → `design_gate_input_changed` → `design_gate_result_stale` → `design_gate_result_invalid` → `design_gate_verdict_mismatch`다.
- `--verdict input_error`는 evaluator 결과가 계약 형식이 아닐 때(evaluator blocked 포함) 쓰며 축 필수 검사와 `design_gate_result_stale` 검사 모두 적용하지 않는다.
- 열린 시도(`status=evaluating`)가 없는 상태에서 `record`를 호출하면 `design_gate_iteration_invalid`로 거부한다(먼저 `start` 필요).

## 반복 상한과 reset

반복 상한 수치는 `harness/guards.md` §자동 루핑 제약 표가 소유한다(현재 값: 3회). 상한 도달 시 `status=retry_limit`이 되고 `transition_action=await_user`·`report_type=decision_request`(심각도 무관)로 사용자 대기한다. 결정론 검사(⑦) 실패로 상한에 도달한 경우도 동일하게 `retry_limit`이며 별도 완화가 없다. `state-tool design-gate reset <task> --owner user --note <사유>`만 `retry_limit`을 해제한다. `--owner user`가 없으면 `user_confirmation_required`로 거부한다. reset은 history를 보존하고 iteration 번호를 이어서 사용해 `gate_id=design-gate-i{N}` 중복을 피한다. `status≠retry_limit`인 상태에서 `reset`을 호출하면 상태를 바꾸지 않고 `reset: false`로 응답하는 no-op이다.

## 설계 결정 분류 (`design-decision`)

`state-tool design-decision <task> --scope external|detail --summary <text> --basis <text>`는 PM 경로 PLAN 단계에서만 허용한다. 결정 범위 3종은 `opal/skills/opal-pilot-dev/references/track-routing.md` §2를 따른다.

- `detail`(구현 세부, 외부 영향 없음): STATE.md 의사결정 로그 + PM activity(decision) 사건 기록, `continue`.
- `external`(목표·수용 기준 / 외부 동작·정책·계약 / 구조·기술 선택 중 하나에 해당): `plan.plan_md` 행을 `block`과 같은 방식으로 failed·`current_status=blocked` 처리하고 `transition_action=blocked`/`decision_request`, 사유에 summary를 남긴다. 해소는 기존 `status --set`·`advance` 재개 경로를 따른다.

두 scope 모두 기록 자체는 성공이므로 `ok: true`·exit 0이다.

`design-decision`은 `execute.implement`가 pending이 아니면 `design_gate_locked`로 거부한다. 또한 미완 frontier 행이 PLAN 단계가 아니면(TASK 미완 또는 이미 PLAN을 지난 상태) `stage_transition_violation`으로 거부한다 — PM 경로 PLAN 단계 밖에서는 결정을 기록할 수 없다.

## agentic에서의 관계

PM 경로 설계 구간(`plan.plan_md`~`plan.user_confirm`)은 agentic 대행 검토 대신 이 설계 게이트 판정을 따른다. 설계 게이트는 agentic Gate 루핑 규칙을 적용하지 않으며, `design-gate`의 상한 도달 시에만 사용자 대기한다.

## 실패 코드

아래 15종은 `DESIGN_GATE_ERROR_CODES`(ERROR_CODES와 물리 분리된 별도 테이블) 소속이다. `design_gate_iteration_invalid`는 `--iteration N`이 `iteration+1`이 아닐 때와, 열린 시도 없이 `record`를 호출했을 때(먼저 `start` 필요) 두 경우 모두에 쓴다.

| 코드 | 의미 |
|---|---|
| `design_gate_not_applicable` | PM 경로가 아닌 태스크에서 설계 게이트 명령을 호출 |
| `design_gate_locked` | `execute.implement`가 pending이 아닌 상태에서 `start`·`design-decision` 호출 |
| `design_gate_attempt_open` | `status=evaluating`인 채 열린 시도가 있고 현재 문서 묶음이 그 시도와 같은 상태에서 새 `start` 호출(먼저 `record` 필요) |
| `design_gate_retry_limit` | 반복 상한 도달(결정론 실패 포함), `reset` 전에는 `start` 불가 |
| `task_reconfirm_required` | TASK 요구 hash가 `task_confirm_req_hash`와 불일치 |
| `design_gate_iteration_invalid` | `--iteration N`이 `iteration+1`이 아니거나, 열린 시도 없이 `record` 호출 |
| `rewrite_target_unchanged` | 직전 rewrite 대상 문서(both는 둘 중 하나)의 hash가 직전 시도와 동일 |
| `design_gate_deterministic_fail` | 결정론 검사(①~⑦) 실패 |
| `design_gate_input_missing` | 대상 문서(TASK/PLAN/TEST-SCENARIO) 부재 |
| `design_gate_input_changed` | `record` 시점 현재 묶음 hash가 `current_attempt.bundle_hash`와 불일치 |
| `design_gate_result_stale` | evaluator 결과 JSON 최상위 `input_bundle_hash`·`iteration`이 현재 열린 시도와 불일치 또는 부재 (pass·rewrite에만 적용, ADD-1) |
| `design_gate_result_invalid` | evaluator 결과 JSON에 필수 축 누락 또는 rewrite인데 `--rewrite-target` 누락 (pass·rewrite에만 적용) |
| `design_gate_verdict_mismatch` | `--verdict pass`인데 설계 4축·시나리오 기준 미충족 |
| `design_gate_not_passed` | `status≠pass`인 상태에서 `plan.design_gate`를 done 처리 시도 |
| `design_bundle_mismatch` | 현재 묶음 hash가 `passed_bundle_hash`/`approved_bundle_hash`와 불일치 |

아래 2종은 이 태스크가 신설한 코드가 아니라 기존 `ERROR_CODES`를 재사용한다.

| 코드 | 의미 |
|---|---|
| `user_confirmation_required` | 자동 승인 불가 mode에서 `--owner user` 없이 확인 행 mark 시도, 또는 `--owner user` 없이 `design-gate reset` 호출 |
| `stage_transition_violation` | `design-decision` 호출 시점의 미완 frontier 행이 PLAN 단계가 아님(단계 건너뛰기 차단 가드 재사용) |
