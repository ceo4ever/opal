# STATE: 테스트 시나리오 작성 기준 개선

> 최종 갱신: 2026-09-29 09:55:50
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | 2026-09-28 18:46:09 | design-decision(detail): 목표-커버 mark 가드는 opd·opds의 test_scenario.scenario_gate·plan.scenario_gate 두 key만 대상, opsdd review.scenario_gate 제외 | 제안서 §7.2가 두 key만 명시, TASK 제외 범위 밖 확장 금지 |
| 2 | 2026-09-28 18:46:09 | design-decision(detail): advisory apply 회차와 반영 재판정 회차를 반복 상한 계산에서 제외, 재판정 실패는 retry_limit 재사용 | TASK AC-6·C-3, 제안서 §6.3·§7.1 |
| 3 | 2026-09-29 09:51:38 | design gate retry limit reset at i3 (owner=user) | 캡틴: i3 지적 반영 확인, i4 진행 |
| 4 | 2026-09-29 09:54:58 | design-decision(detail): 구형 이력 원소(counted 필드 없음)는 counted:true로 간주해 상한·no_progress 계산에 포함, opal-pilot-dev STEP 3.5 정합 확인은 W-2 확인 항목 | i4 evaluator 비차단 지적, 보수적 해석(상한 우회 방지) |

## 블로커
없음
