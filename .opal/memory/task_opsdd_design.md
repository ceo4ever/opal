---
type: task
status: 완료
created_at: 2026-04-03 17:00
updated_at: 2026-04-06
---

# opal-pilot-sdd (opsdd) 오케스트레이터 스킬 설계 (080)

태스크 경로: `tasks/080-opp-opsdd-design-proposal/`

## 결과

opsdd 오케스트레이터 + 4개 단계 스킬 + 4개 references 가이드 구현 완료.

| 항목 | 내용 |
|------|------|
| 스킬명 | `opal-pilot-sdd` (약어: opsdd) |
| 파이프라인 | SPEC → SPEC-VERIFY → SPEC-PLAN → TASKS → TASKS-VERIFY → EXECUTE-LOOP → DONE (7단계) |
| 설계 방안 | C안: TASK=진입점, SPEC=SSOT. specs/(SDD) + tasks/(OPAL) 분리 |
| 신규 파일 | 13개 (SKILL.md 5 + personas 4 + references 4) |
| 수정 파일 | 5개 (PROJECT/ARCHITECTURE/CONVENTIONS/registry/skills) |

## 후속 작업

- oppd Phase 3 액션 스킬 등록 (별도 태스크)
- 배포: install-mac.sh 갱신 (캡틴 지시 시)
