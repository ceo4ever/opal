# DONE: QA 체크리스트 갱신 강제 — QA 에이전트 책임 + PM Gate 확인

> 완료일: 2026-04-05

## 변경 파일 (7개)

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `opal/core/references/opal-harness.md` | §2 QA 체크리스트 검증 — 2단계 갱신 구조 + PM 직접 갱신 금지 원칙 |
| 2 | `opal/core/references/opal-harness-interactive.md` | §3 PM Gate에 체크리스트 갱신 상태 확인 절차 + §4 QA 재소환으로 변경 |
| 3 | `opal/skills/op-task-qa/SKILL.md` | Step 4 "체크리스트 갱신" 프로세스 추가 |
| 4 | `opal/skills/op-dev-qa/SKILL.md` | Step 4 "체크리스트 갱신" 프로세스 추가 |
| 5 | `opal/skills/opal-pilot-project/SKILL.md` | PLAN/EXECUTE PM Gate에 갱신 확인 + QA 재소환 |
| 6 | `opal/skills/opal-pilot-dev-short/SKILL.md` | PLAN/EXECUTE PM Gate에 갱신 확인 + QA 재소환 |
| 7 | `opal/skills/opal-pilot-dev/SKILL.md` | PLAN/EXECUTE PM Gate에 갱신 확인 + QA 재소환 |

## 핵심 변경 사항

**2단계 갱신 구조**:
1. **QA 에이전트 1차 갱신**: QA 수행 시 체크리스트를 Read → 검증 통과 항목 `[x]` 갱신
2. **PM Gate 2차 확인**: 갱신 상태 확인 → 미갱신 시 QA 에이전트 재소환 (PM 직접 갱신 금지)

**적용 범위**: 모든 QA Gate(PLAN QA, EXECUTE QA) + 모든 PM Gate에 공통 적용
