# STATE: 컴포넌트 리네이밍 + 레거시 정리

> 최종 갱신: 2026-03-29 16:30

## 현재 상태
- 모드: Short Task
- 단계: TASK ✅ / PLAN ✅ / EXECUTE
- 진행: -
- 상태: 대기 중

## 완료 산출물
| 산출물 | 상태 |
|--------|------|
| TASK.md | ✅ 완료 |
| PLAN.md | ✅ 완료 |
| TEST-SCENARIO.md | 스킵 (문서 전용) |
| DONE.md | 대기 |

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | TASK | otp → opal-pilot, dtp → op-dev/op-task | OPAL 소속 명확화 + dev/범용 구분 |
| 2 | TASK | otp-wf → opal-pilot-dev-wireframe | wireframe도 코드 작업(shadcn) → dev 도메인 |
| 3 | TASK | worker → agent | agents/ 디렉토리에 AGENT.md로 정의되므로 |
| 4 | TASK | op-qa → op-task-qa | 범용 스킬을 op-task-* 네임스페이스로 통일 |
| 5 | TASK | dev-task-pilot + 레거시 에이전트 6개 삭제 | 032 전환 완료, 신규 에이전트가 대체 |
| 6 | TASK | 041 JSON 레지스트리 기반으로 작업 | skills.md 테이블 이미 제거, JSON이 SSOT |

## 블로커
없음

## 다음 액션
PLAN 단계 진행
