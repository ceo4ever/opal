# opal-skill-tester 보고서 — function-todo-crud (function)

TODO CRUD 웹 앱

| 실행 | 판정 | 숨은 테스트 | 완료 | 상태검증 | run-log 적체 | 게이트 증거 | 체크포인트 커밋 | 최종 수행 시간(분) | $ | 서브에이전트 | 게이트 반복 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| opds-design-opus-high-impl-sonnet-low-r1 | **FAIL** | 6 passed in 2.61s | True | True | 0 | True | 도구 0/우회 0 | 30.0 | 15.81 | 9 | 1 |
| opds-design-opus-high-impl-sonnet-low-r2 | **FAIL** | 6 passed in 4.81s | True | True | 0 | True | 도구 0/우회 0 | 30.6 | 13.1 | 6 | 1 |
| opds-design-opus-high-impl-sonnet-medium-r1 | **FAIL** | 6 passed in 4.49s | False | True | 0 | False | 도구 2/우회 0 | 26.4 | 11.01 | 5 | 1 |
| opds-design-opus-high-impl-sonnet-medium-r2 | **FAIL** | 6 passed in 1.59s | True | True | 0 | True | 도구 0/우회 0 | 42.8 | 18.31 | 11 | 1 |
| opds-design-opus-medium-impl-haiku-medium-r1 | **FAIL** | 6 passed in 5.83s | True | False | 2 | True | 도구 0/우회 0 | 37.6 | 13.33 | 0 | 1 |
| opds-design-opus-medium-impl-haiku-medium-r2 | **FAIL** | 6 passed in 1.83s | True | True | 0 | True | 도구 0/우회 0 | 29.2 | 12.56 | 5 | 1 |
| opds-r1 | **FAIL** | 6 passed in 5.88s | True | True | 0 | True | 도구 0/우회 0 | 25.6 | 12.5 | 10 | 1 |
| opds-r2 | **FAIL** | 6 passed in 2.25s | True | True | 0 | True | 도구 0/우회 0 | 23.3 | 10.47 | 8 | 1 |

## 불합격 사유와 경고

- **opds-design-opus-high-impl-sonnet-low-r1**: 준수 불충족: checkpoint_commits
- **opds-design-opus-high-impl-sonnet-low-r2**: 준수 불충족: checkpoint_commits
- **opds-design-opus-high-impl-sonnet-medium-r1**: 준수 불충족: pipeline_complete; 준수 불충족: gate_evidence
- **opds-design-opus-high-impl-sonnet-medium-r2**: 준수 불충족: checkpoint_commits
- **opds-design-opus-medium-impl-haiku-medium-r1**: 준수 불충족: state_valid; 준수 불충족: runlog_pending; 준수 불충족: checkpoint_commits; 첫 run-log 적체 사건: {"event": "state.changed", "task_step": null, "summary": "status: completed_unmerged → done", "data": {"from": "completed_unmerged", "to": "done", "row_key": "current_status"}}
- **opds-design-opus-medium-impl-haiku-medium-r2**: 준수 불충족: checkpoint_commits
- **opds-r1**: 준수 불충족: checkpoint_commits
- **opds-r2**: 준수 불충족: checkpoint_commits

## 변형 비교 (반복 평균 (최소~최대))

| 지표 | //opds | //opds design=opus/high impl=sonnet/low | //opds design=opus/high impl=sonnet/medium | //opds design=opus/medium impl=haiku/medium |
|---|---|---|---|---|
| wall_min | 24.45 (23.30~25.60) | 30.30 (30.00~30.60) | 34.60 (26.40~42.80) | 33.40 (29.20~37.60) |
| cost_usd | 11.48 (10.47~12.50) | 14.46 (13.10~15.81) | 14.66 (11.01~18.31) | 12.95 (12.56~13.33) |
| turns | 120.00 (119.00~121.00) | 74.00 (20.00~128.00) | 128.00 (107.00~149.00) | 70.00 (19.00~121.00) |
| subagent_runs | 9.00 (8.00~10.00) | 7.50 (6.00~9.00) | 8.00 (5.00~11.00) | 2.50 (0.00~5.00) |
| gate_iterations | 1.00 (1.00~1.00) | 1.00 (1.00~1.00) | 1.00 (1.00~1.00) | 1.00 (1.00~1.00) |
| hidden_pass_rate | 1.00 (1.00~1.00) | 1.00 (1.00~1.00) | 1.00 (1.00~1.00) | 1.00 (1.00~1.00) |
| test_fix_iterations | 0.00 (0.00~0.00) | 0.00 (0.00~0.00) | 0.00 (0.00~0.00) | 0.00 (0.00~0.00) |
| 합격 | 0/2 | 0/2 | 0/2 | 0/2 |

## 품질 하한 판정

기준 변형: //opds — 하한은 숨은 테스트 통과율 평균과 PASS 비율이 모두 기준 이상일 때 충족한다.

- //opds design=opus/high impl=sonnet/low — 하한 충족 (숨은 테스트 평균 1.00, PASS 0.00)
- //opds design=opus/high impl=sonnet/medium — 하한 충족 (숨은 테스트 평균 1.00, PASS 0.00)
- //opds design=opus/medium impl=haiku/medium — 하한 충족 (숨은 테스트 평균 1.00, PASS 0.00)

## 단계별 소요(분)

- opds-design-opus-high-impl-sonnet-low-r1: {'design': 7.9, 'execute': 5.2, 'test': 10.0, 'close': 1.8}
- opds-design-opus-high-impl-sonnet-low-r2: {'design': 10.1, 'execute': 4.7, 'test': 8.1, 'close': 2.6}
- opds-design-opus-high-impl-sonnet-medium-r1: {'design': 10.3, 'execute': 4.3}
- opds-design-opus-high-impl-sonnet-medium-r2: {'design': 11.3, 'execute': 6.6, 'test': 17.6, 'close': 2.2}
- opds-design-opus-medium-impl-haiku-medium-r1: {}
- opds-design-opus-medium-impl-haiku-medium-r2: {'design': 5.8, 'execute': 12.9, 'test': 5.2, 'close': 1.4}
- opds-r1: {'design': 8.0, 'execute': 4.1, 'test': 7.9, 'close': 1.9}
- opds-r2: {'design': 8.0, 'execute': 3.1, 'test': 7.0, 'close': 1.6}
