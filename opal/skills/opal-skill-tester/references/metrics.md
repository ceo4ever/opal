# Pilot 측정 지표 기준

실행기(`scripts/skill_tester.py`)가 실행마다 아래 지표를 수집하고 판정한다. 결과·준수 범주는 합격 조건, 효율·재작업 범주는 과거 이력(같은 변형·시나리오 최근 3회 중앙값) 대비 추세 경고다. 실행마다 편차가 있으므로 효율 수치 하나로 결론을 내리지 않는다.

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
| `gate_evidence` | Pilot 프로필(아래 표)의 게이트 증거가 모두 충족 | true |
| `checkpoint_commits` / `raw_commits` | 일반 worktree Pilot은 기본 브랜치 대비 커밋 중 허브 registry `execution_ownership.checkpoint_shas`에 있는 것(`worktree-tool checkpoint`)과 없는 것(`git commit` 직접 실행)을 구분한다. OPPB는 merge·finalize 후 worktree와 활성 registry가 회수되므로 `p4.project_checkpoint`·`p5.worktree_finalize` 행과 task-local 닫힌 archive로 대체 판정한다. | 일반 worktree: 도구 커밋 ≥ 1 + 우회 커밋 0. OPPB: finalize archive PASS |

Pilot 프로필은 `scripts/skill_tester.py`의 `PROFILES`가 소유한다. 프로필이 없는 Pilot은 "판정 프로필 없음"으로 불합격 처리되므로, 새 Pilot을 시험하려면 먼저 프로필을 추가한다.

| Pilot | 게이트 증거 | 단계 이정표(구현 시작·완료 / 테스트 완료) |
|---|---|---|
| opd·opds | 설계 게이트 `design_gate.status=pass` 또는 `.scenario-gate-history.json` 마지막 pass, 그리고 `test-scenario.json` 전 시나리오 pass | `execute.implement` / `test.pm_gate` |
| opsdd | `.scenario-gate-history.json` 마지막 pass, 그리고 `review.scenario_gate`·`verify.ts_green` 행 done | `execute.act_run` / `verify.pm_gate` |
| opd2 | `verify.verifier_evidence`·`verify.review` 행 done | `execute.implement` / `verify.review` |
| oppb | P1·P3·P4·P5 필수 gate/checkpoint/finalize 행 done, canonical 태스크의 `.oppb-run/<run_id>/run.closed.json` 존재, 허브 `.opal-runs` 미생성, `state.worktree` 경로 회수 | `p3.continuous_execution` / `p4.pm_gate` / `p5.worktree_finalize` |

`runlog_pending`이 0이 아니면 기록 코어가 어떤 사건을 거부해 drain이 멈춘 상태다. 첫 pending 사건을 보고서에 함께 싣는다.

## 3. 효율 (이력 대비 경고)

| 지표 | 수집 방법 |
|---|---|
| `wall_min` | 최종 수행 시간: 테스트 세션 시작부터 종료까지 실제 경과 시간(TASK~CLOSE 전 과정, 서브에이전트 대기 포함) |
| `cost_usd`, `turns`, `output_tokens` | 세션 JSON 결과(`--output-format json`) |
| `subagent_runs` | run-log `worker.started` 사건 수 |
| `phase_min` | run-log `state.changed` 이정표로 계산한 설계(시작~`execute.implement` 시작)·구현·테스트(~`test.pm_gate` 완료)·CLOSE(~`close.final`) 구간 |

과거 기록이 있으면 `wall_min`·`cost_usd`·`subagent_runs`가 최근 3회 중앙값 대비 ±20% 밖일 때 경고한다.

| 보조 지표 | 수집 방법 |
|---|---|
| `stage_min` | run-log `state.changed`로 계산한 단계별(TASK·SPEC·…·CLOSE) 소요 분 |
| `stage_log` | `AGENTIC-LOG.md` 단계 열 기준 GATE·ERROR·FIX·DECISION 행 수 |
| `corrections` | `AGENTIC-LOG.md` ERROR(발견)·FIX(교정) 행 내용 |
| `decision_requests` | run-log `pm.report`의 `decision_request` 수 |
| `framework` | 실행 시작 시점의 설치 VERSION + state-tool·Pilot SKILL.md sha256 앞 6자리 |

## 4. 재작업 (이력 대비 경고)

| 지표 | 수집 방법 |
|---|---|
| `gate_iterations` | 설계 게이트 history 길이 또는 목표-커버 게이트 history 길이 |
| `log_error`, `log_fix` | `AGENTIC-LOG.md`의 `ERROR`·`FIX` 행 수 |
| `worker_blocked` | run-log `worker.blocked` 사건 수 |

최근 3회 중앙값보다 늘어나면 경고한다.

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
