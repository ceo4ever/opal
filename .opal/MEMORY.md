# opal Memory Index

> 최종 갱신: 2026-03-29

## 메모리 카테고리

| 카테고리 | 설명 | 완료 시 |
|----------|------|---------|
| task | 일회성 작업 계획/예정 | 삭제 |
| project | 프로젝트 비전, 방향성 등 지속 지식 | 유지 (폐기 시 삭제) |
| architecture | 아키텍처 설계 결정과 근거 | 유지 (변경 시 갱신) |
| feedback | 캡틴의 작업 방식 피드백 | 유지 (철회 시 삭제) |
| preferences | 이 프로젝트에서 캡틴이 선호하는 방식 | 유지 |
| issues | 반복되는 이슈와 해결법 | 유지 |

> 메모리 파일은 `memory/` 디렉토리에 저장한다.
> 새 메모리가 생기면 이 인덱스에 파일 경로와 설명을 추가한다.
> **task 타입은 완료 시 메모리 파일 + 인덱스 항목을 삭제한다.**

## 메모리

| 카테고리 | 상태 | 파일 | 설명 |
|----------|------|------|------|
| task | 예정 | [memory/project_security_task.md](memory/project_security_task.md) | 보안 전용 스킬+에이전트 생성 |
| task | 예정 | [memory/project_skill_source_move.md](memory/project_skill_source_move.md) | OPAL 전용 스킬 소스 opal/skills/로 이동 |
| project | 유효 | [memory/project_opi_vision.md](memory/project_opi_vision.md) | opi 비전: 프로젝트=WHAT/WHY, 스킬=HOW |

## 작업 히스토리 (최대 10개, FIFO)

| # | 작업 | 단계 | 경로 | 날짜 |
|---|------|------|------|------|
| 0 | op-task-qa → op-dev-qa 리네이밍 + 범용 op-task-qa 신규 (046) | 완료 | tasks/046-qa-skill-rename/ | 2026-03-29 |
| 0 | 멀티 플랫폼 모델 매핑 참조 + 스킬 적용 (044) | 완료 (8aaec44) | tasks/044-model-mapping-reference/ | 2026-03-29 |
| 0 | opal-project-pilot + 범용 스킬 + 에이전트 리네이밍 (045) | 완료 (6fa0438) | tasks/045-opal-project-pilot/ | 2026-03-29 |
| 1 | opi 프로젝트 최신화 | 완료 | docs/, .opal/ | 2026-03-29 |
| 1 | opal-doc-standard v2.0 문서 유형 확장 (043) | 완료 (76b6010) | tasks/043-doc-standard-enhancement/ | 2026-03-29 |
| 2 | 컴포넌트 리네이밍 + 레거시 정리 (042) | 완료 (16b6f1a) | tasks/042-skills-registry-reclassify/ | 2026-03-29 |
| 2 | otp-write-tech 스킬 개발 (039) | 완료 | tasks/039-otp-write-tech-skill/ | 2026-03-29 |
| 2 | otp-write 스킬 개발 + opal-doc-standard 통합 (038) | 완료 (a07df3c) | tasks/038-otp-write-skill/ | 2026-03-29 |
| 3 | PLAN+TODO 통합 + TEST-SCENARIO 스킵 조건 (037) | 완료 (555db49) | tasks/037-plan-todo-merge/ | 2026-03-28 |
| 4 | otp 파이프라인 TEST-SCENARIO 재배치 + 커밋 규칙 (036) | 완료 (a3ebc8e) | tasks/036-otp-pipeline-test-scenario-reorder/ | 2026-03-28 |
| 5 | opal-project-dev-pilot 스킬 개발 (034) | 완료 (e20bad2) | tasks/034-opal-dev-pilot/ | 2026-03-27 |
| 6 | opi 전면 재설계 + PM 역할 실체화 (033) | 완료 (1b041b1) | tasks/033-opal-framework-doc-pm-restructure/ | 2026-03-27 |
| 7 | dtp 컴포지션 아키텍처 전환 (032) | 완료 (ff9b13d) | tasks/032-dtp-to-otp-restructure/ | 2026-03-26 |
| 8 | 태스크 진행 단계 메모리 추적 기능 추가 | 완료 (359a7dd) | - | 2026-03-22 |
| 9 | context-compactor 스킬 (031) | PLAN ✅ → TODO 대기 | tasks/031-context-compactor-skill/ | 2026-03-22 |
| 10 | opal-project-init scope=opal-only 모드 추가 | 완료 (dfb2a18) | - | 2026-03-21 |
