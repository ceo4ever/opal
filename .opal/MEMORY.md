# opal Memory Index

> 최종 갱신: 2026-03-30 16:05

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

| # | 등록일시 | 카테고리 | 상태 | 파일 | 설명 |
|---|----------|----------|------|------|------|
| 1 | 2026-03-22 | task | 예정 | [memory/project_security_task.md](memory/project_security_task.md) | 보안 전용 스킬+에이전트 생성 |
| 3 | 2026-03-27 | project | 유효 | [memory/project_opi_vision.md](memory/project_opi_vision.md) | opi 비전: 프로젝트=WHAT/WHY, 스킬=HOW |
| 4 | 2026-03-30 14:00 | task | 완료 | [memory/task_agentic_loop.md](memory/task_agentic_loop.md) | oppd에 agentic 자율 루핑(QA/TEST) 장치 설계 |
| 5 | 2026-03-31 16:30 | feedback | 유효 | [memory/feedback_qa_checklist.md](memory/feedback_qa_checklist.md) | EXECUTE 후 PM이 QA 체크리스트 반드시 갱신 — DONE.md 전 필수 |
## 작업 히스토리 (최대 10개, FIFO)

| # | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |
|---|------|------|------|---------|---------|
| 0 | erd-modeler 스킬 범용화 (059) | 완료 | tasks/059-erd-modeler-universalize/ | 2026-03-31 17:00 | 2026-03-31 17:30 |
| 1 | 하네스 모듈화 — 공통+모드별 분리 (058) | 완료 | tasks/058-harness-modularize/ | 2026-03-31 15:40 | 2026-03-31 16:30 |
| 1 | opal-pilot agentic mode 추가 (057) | 완료 | tasks/057-opal-pilot-agentic-mode/ | 2026-03-31 14:00 | 2026-03-31 15:30 |
| 1 | opal-task-action-agent 신규 생성 (056) | 완료 | tasks/056-opal-task-action-agent/ | 2026-03-30 16:47 | 2026-03-30 17:29 |
| 1 | opi tasks/ 태스크 기록 추가 (055) | 완료 | tasks/055-opi-task-record/ | 2026-03-30 16:00 | 2026-03-30 16:05 |
| 1 | docs-guide 프로젝트 구조 섹션 역할 분리 (054) | 완료 | tasks/054-docs-guide-project-structure/ | 2026-03-30 15:30 | 2026-03-30 15:48 |
| 2 | oppd agentic 자율 루핑 + 병렬 실행 설계 (053) | 완료 | tasks/053-oppd-agentic-loop/ | 2026-03-30 14:33 | 2026-03-30 15:45 |
| 3 | 오케스트레이터 정비 — opw 삭제 + 리네이밍 + oppd opwt 연동 (052) | 완료 | tasks/052-orchestrator-cleanup/ | 2026-03-30 13:30 | 2026-03-30 14:16 |
| 4 | OPAL 전용 스킬 소스 이동 (051) | 완료 | tasks/051-opal-skill-source-move/ | 2026-03-30 | 2026-03-30 |
| 5 | opi 범용 프로젝트 분석 개선 (050) | 완료 | tasks/050-opi-universal-analysis/ | 2026-03-30 | 2026-03-30 |
| 6 | 워커 에이전트 프로젝트 컨텍스트 자율 로딩 (049) | 완료 | tasks/049-agent-project-context/ | 2026-03-30 | 2026-03-30 |
| 7 | CLAUDE.md 슬림화 + PM 컨텍스트 최적화 (047) | 완료 | tasks/047-opi-claude-md-slim/ | 2026-03-30 | 2026-03-30 |
