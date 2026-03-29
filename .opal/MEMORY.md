# opal Memory Index

> 최종 갱신: 2026-03-21

## 메모리 카테고리

| 카테고리 | 파일 | 설명 |
|----------|------|------|
| architecture_decisions | - | 왜 이 기술/설계를 선택했는지 |
| domain_knowledge | - | 대화하면서 쌓인 도메인 지식 |
| preferences | - | 이 프로젝트에서 캡틴이 선호하는 방식 |
| issues | - | 반복되는 이슈와 해결법 |

> 메모리 파일은 `memory/` 디렉토리에 저장한다 (예: `memory/architecture_decisions.md`).
> 새 메모리가 생기면 이 인덱스에 파일 경로와 설명을 추가한다.

## 작업 히스토리 (최대 10개, FIFO)

| # | 작업 | 단계 | 경로 | 날짜 |
|---|------|------|------|------|
| 1 | otp-write-tech 스킬 개발 (039) | TODO ✅ → EXECUTE 대기 | tasks/039-otp-write-tech-skill/ | 2026-03-29 |
| 2 | otp-write 스킬 개발 + opal-doc-standard 통합 (038) | 완료 (a07df3c) | tasks/038-otp-write-skill/ | 2026-03-29 |
| 3 | PLAN+TODO 통합 + TEST-SCENARIO 스킵 조건 (037) | 완료 (555db49) | tasks/037-plan-todo-merge/ | 2026-03-28 |
| 4 | otp 파이프라인 TEST-SCENARIO 재배치 + 커밋 규칙 (036) | 완료 (a3ebc8e) | tasks/036-otp-pipeline-test-scenario-reorder/ | 2026-03-28 |
| 5 | opal-project-dev-pilot 스킬 개발 (034) | 완료 (e20bad2) | tasks/034-opal-dev-pilot/ | 2026-03-27 |
| 6 | opi 전면 재설계 + PM 역할 실체화 (033) | 완료 (1b041b1) | tasks/033-opal-framework-doc-pm-restructure/ | 2026-03-27 |
| 7 | dtp 컴포지션 아키텍처 전환 (032) | 완료 (ff9b13d) | tasks/032-dtp-to-otp-restructure/ | 2026-03-26 |
| 8 | 태스크 진행 단계 메모리 추적 기능 추가 | 완료 (359a7dd) | - | 2026-03-22 |
| 9 | context-compactor 스킬 (031) | PLAN ✅ → TODO 대기 | tasks/031-context-compactor-skill/ | 2026-03-22 |
| 10 | opal-project-init scope=opal-only 모드 추가 | 완료 (dfb2a18) | - | 2026-03-21 |

## 프로젝트

| 카테고리 | 파일 | 설명 |
|----------|------|------|
| project | [memory/project_security_task.md](memory/project_security_task.md) | 030에서 분리된 보안 전용 스킬+에이전트 생성 예정 |
| project | [memory/project_otp_doc_plan.md](memory/project_otp_doc_plan.md) | otp-doc 문서 전용 스킬 계획 — otp-dev 계열 완료 후 설계 예정 |
| project | [memory/project_opi_vision.md](memory/project_opi_vision.md) | opi 비전: 프로젝트=WHAT/WHY 정의, 스킬=HOW 수행. opi 산출물이 모든 스킬의 컨텍스트 |
| architecture | [memory/architecture_otp_harness_vertical.md](memory/architecture_otp_harness_vertical.md) | otp 범용 하네스 + 버티컬 전문 스킬 분리 아키텍처 방향 |
| project | [memory/project_json_tooling.md](memory/project_json_tooling.md) | JSON 하네스/레지스트리 + Node.js MCP 도구화 (041 예정) |
| project | [memory/project_multi_platform_model_mapping.md](memory/project_multi_platform_model_mapping.md) | 워커 model override가 Claude 전용 — 멀티 플랫폼 모델 매핑 표준화 필요 (캡틴 일괄 정리 예정) |
| feedback | [memory/feedback_otp_pipeline_discipline.md](memory/feedback_otp_pipeline_discipline.md) | otp 파이프라인 단계 스킵 금지 + EXECUTE 후 무단 커밋 금지 |
