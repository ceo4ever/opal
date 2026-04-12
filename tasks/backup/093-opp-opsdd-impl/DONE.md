# DONE: opsdd 스킬 구현 — 092 설계 기반

> 완료일: 2026-04-07 | 태스크: 093-opp-opsdd-impl | 스킬: opp

## 완료 요약

092 설계 기반으로 opsdd 스킬을 7단계 → 5단계 파이프라인으로 구현 완료.
tasks/ 단일 루트 통합, EXECUTE-LOOP 재작성, op-sdd-tasks 삭제 모두 반영.

## 변경 파일

| 파일 | 변경 유형 |
|------|---------|
| `opal/core/references/opal-harness.md` | §4 base_path 조건부 저장 경로 규칙 추가 (v2.9) |
| `opal/skills/opal-pilot-sdd/SKILL.md` | 7→5단계 파이프라인 재작성, tasks/ 단일 루트, ACT 구조 (v2.0) |
| `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | ACT 루프 구조로 전면 재작성 |
| `opal/skills/opal-pilot-sdd/references/verify-guide.md` | REVIEW Phase PM 직접 검증 가이드로 재작성 |
| `opal/skills/op-sdd-plan/SKILL.md` | op-sdd-tasks 통합, SPEC-PLAN.md에 ACT 분해 포함 (v2.0) |
| `opal/skills/op-sdd-tasks/` | 삭제 (op-sdd-plan에 통합) |
| `opal/skills/op-sdd-spec/SKILL.md` | 출력 경로 specs/ → tasks/ 수정 (v1.1) |

## PM Gate 특이사항

op-sdd-tasks/SKILL.md 삭제 후 personas/ 폴더 잔존 감지 → PM Gate에서 즉시 처리 (폴더 완전 삭제).
