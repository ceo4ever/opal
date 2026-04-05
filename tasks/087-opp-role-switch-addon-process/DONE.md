# DONE: 알투 역할 전환 규칙 + 태스크 추가작업 프로세스 정의

> 완료일: 2026-04-05

## 완료 산출물

| 산출물 | 경로 |
|--------|------|
| TASK.md | tasks/087-opp-role-switch-addon-process/TASK.md |
| PLAN.md | tasks/087-opp-role-switch-addon-process/PLAN.md |
| QA-PLAN.md | tasks/087-opp-role-switch-addon-process/QA-PLAN.md |
| QA-EXECUTE.md | tasks/087-opp-role-switch-addon-process/QA-EXECUTE.md |
| DONE.md | tasks/087-opp-role-switch-addon-process/DONE.md |

## 변경 파일

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `opal/core/references/opal-harness.md` | B 그룹: 추가작업 프로세스 (STATE.md 상태값, ADD_DONE.md 템플릿, 진입 조건, 스킬별 검증 오버라이드, DONE.md 보존 원칙) |
| 2 | `opal/core/AGENT.md` | A 그룹: 역할 전환 규칙 (5가지 케이스 테이블, PM 전환 제안, PM 모드 표시, 캡틴 오버라이드) |
| 3 | `opal/skills/op-task/SKILL.md` | C 그룹: 대화 내용 반영 의무, 요구사항 작성 기준 (무엇을/어디에/왜/AC), 인터뷰 강화 |
| 4 | `opal/skills/opal-pilot-project/SKILL.md` | 추가작업 참조 가이드 |
| 5 | `opal/skills/opal-pilot-dev-short/SKILL.md` | 추가작업 참조 가이드 |
| 6 | `opal/skills/opal-pilot-dev/SKILL.md` | 추가작업 참조 가이드 |
| 7 | `opal/skills/opal-pilot-write-tech/SKILL.md` | 추가작업 참조 가이드 |

## QA 결과

- QA-PLAN: Needs Revision → Warning 2건 해소 후 승인
- QA-EXECUTE: Pass (Warning 1건 — 변경이력 누락 → PM Gate에서 직접 해소)

## 미반영 사항 (향후 검토)

| # | 항목 | 설명 |
|---|------|------|
| 1 | 비서 하네스 | 비서 모드에 경량 하네스 적용 여부 — 구조적 결정 필요 |
| 2 | Artifact Gate | 산출물 기반 강제 — QA 산출물 없으면 다음 단계 진입 불가 (메모리 #8) |
