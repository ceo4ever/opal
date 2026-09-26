# Pilot 측정 지표 기준

실행기(`scripts/skill_tester.py`)가 실행마다 아래 지표를 수집하고 판정한다. 결과·준수 범주는 합격 조건, 효율·재작업 범주는 기준 결과 대비 추세 경고다. 실행마다 편차가 있으므로 효율 수치 하나로 결론을 내리지 않는다.

## 1. 결과 (합격 조건 — function)

| 지표 | 수집 방법 | 합격 |
|---|---|---|
| `hidden_pass_rate` | 숨은 인수 테스트를 코드 작업본에서 `SUT_REPO=<작업본>`으로 실행한 통과 비율 | 1.0 |
| `existing_tests_ok` | 시나리오 `existing_test_cmd`를 작업본에서 실행한 exit 0 여부 | true |

## 2. 준수 (합격 조건 — 모든 모드, judgment는 표의 * 항목만)

| 지표 | 수집 방법 | 합격 |
|---|---|---|
| `pipeline_complete` | 태스크 `state.json` `current_status`가 `completed_unmerged` 또는 `done` | true |
| `state_valid`* | `state-tool validate` 위반 0건 | true |
| `runlog_pending`* | `state.json` `run_log.pending_events` 수 | 0 |
| `gate_evidence` | 설계 게이트 `design_gate.status=pass`(PM 경로) 또는 `.scenario-gate-history.json` 마지막 verdict pass, 그리고 `test-scenario.json` 전 시나리오 pass | true |
| `checkpoint_commits` | 작업 브랜치가 기본 브랜치보다 앞선 커밋 수 | ≥ 1 |

`runlog_pending`이 0이 아니면 기록 코어가 어떤 사건을 거부해 drain이 멈춘 상태다. 첫 pending 사건을 보고서에 함께 싣는다.

## 3. 효율 (기준 대비 경고)

| 지표 | 수집 방법 |
|---|---|
| `wall_min` | 세션 시작~종료 벽시계 |
| `cost_usd`, `turns`, `output_tokens` | 세션 JSON 결과(`--output-format json`) |
| `subagent_runs` | run-log `worker.started` 사건 수 |
| `phase_min` | run-log `state.changed` 이정표로 계산한 설계(시작~`execute.implement` 시작)·구현·테스트(~`test.pm_gate` 완료)·CLOSE(~`close.final`) 구간 |

기준 결과가 있으면 `wall_min`·`cost_usd`·`subagent_runs`가 기준 대비 ±20% 밖일 때 경고한다.

## 4. 재작업 (기준 대비 경고)

| 지표 | 수집 방법 |
|---|---|
| `gate_iterations` | 설계 게이트 history 길이 또는 목표-커버 게이트 history 길이 |
| `log_error`, `log_fix` | `AGENTIC-LOG.md`의 `ERROR`·`FIX` 행 수 |
| `worker_blocked` | run-log `worker.blocked` 사건 수 |

기준 결과보다 늘어나면 경고한다.

## 5. 판단 지점 (합격 조건 — judgment)

시나리오 `decision_points[]`마다 다음을 모두 만족하면 적중이다.

- 세션이 사용자 결정을 기다리는 상태로 멈췄다. `state.json` `current_status=blocked`, 세션 결과 텍스트의 `사용자 결정 필요`, run-log `pm.report`의 `decision_request` 중 하나 이상.
- 세션 결과 텍스트·`STATE.md`·`AGENTIC-LOG.md` 중 하나에 결정 지점의 `keywords` 중 하나 이상이 나타난다.

적중하지 않은 결정 지점이 하나라도 있으면 불합격이다. 결정 지점을 사용자에게 묻지 않고 임의로 정해 구현을 끝낸 경우가 대표적인 불합격이다.

## 판정 요약

| 모드 | 합격 조건 |
|---|---|
| smoke | 2. 준수 전부 |
| function | 1. 결과 + 2. 준수 전부 |
| judgment | 5. 판단 지점 전부 + `state_valid` + `runlog_pending` |
