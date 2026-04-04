# DONE: 하네스/스킬 문서 4건 정비 — STATE.md 누락 방지 + 병렬 판별 추가

> 완료일: 2026-04-04

## 요약

하네스와 스킬 문서 간 암묵적/분산된 지침 4건(+확장 2건)을 명시적으로 정비하여, 오케스트레이터와 워커의 프로세스 누락을 방지했다.

## 변경 파일

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `opal/core/references/opal-harness.md` | §4 스킬/공통 영역 구분 마커 + STATE.md `[필수]` 강조 (R1, R2) |
| 2 | `opal/skills/op-task/SKILL.md` | 완료 보고 형식 위에 STATE.md 리마인더 추가 (R3) |
| 3 | `opal/skills/opal-pilot-dev-short/SKILL.md` | 에스컬레이션 규칙에 조기 에스컬레이션 조항 추가 (R4) |
| 4 | `opal/skills/op-dev-plan/references/plan-guide.md` | Phase 그룹핑 지침 추가 (R5) |
| 5 | `opal/skills/op-dev-plan/SKILL.md` | 품질 체크리스트에 Phase 그룹핑 항목 추가 (R6) |
| 6 | `opal/skills/op-task-plan/references/plan-guide.md` | Phase 그룹핑 지침 추가 (R7) |
| 7 | `opal/skills/op-task-plan/SKILL.md` | 품질 체크리스트에 Phase 그룹핑 항목 추가 (R8) |

## QA 결과

- QA-PLAN.md: Pass
- QA-EXECUTE.md: Pass
- PM Gate: Pass (R1~R8 전체 충족, 기존 프로세스 보존 확인)
