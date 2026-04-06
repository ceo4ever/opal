# opal Memory Index

> 최종 갱신: 2026-04-01 21:30

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
| 5 | 2026-03-31 16:30 | feedback | 유효 | [memory/feedback_qa_checklist.md](memory/feedback_qa_checklist.md) | EXECUTE 후 PM이 QA 체크리스트 반드시 갱신 — DONE.md 전 필수 |
| 6 | 2026-04-02 11:30 | feedback | 유효 | [memory/feedback_skip_qa_warning.md](memory/feedback_skip_qa_warning.md) | [경고] 배포(Sync) 전 QA Gate 생략 금지 — 068 태스크 실수 재발 방지 |


## 작업 히스토리 (최대 10개, FIFO)

| # | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |
|---|------|------|------|---------|---------|
| 0 | Artifact Gate 설계 및 적용 (090) | 완료 | tasks/090-opp-artifact-gate/ | 2026-04-06 | 2026-04-06 |
| 0 | opi docs 백업 기능 추가 (088) | 완료 | tasks/088-opp-opi-docs-backup/ | 2026-04-06 | 2026-04-06 |
| 0 | opsdd 오케스트레이터 스킬 설계 (080) | 완료 | tasks/080-opp-opsdd-design-proposal/ | 2026-04-03 | 2026-04-06 |
| 0 | 역할 전환 규칙 + 추가작업 프로세스 (087) | 완료 | tasks/087-opp-role-switch-addon-process/ | 2026-04-05 | 2026-04-05 |
| 0 | opal-pm 레퍼런스 구축 (086) | 완료 | tasks/086-opp-opal-pilot-pm/ | 2026-04-05 | 2026-04-05 |
| 0 | QA 체크리스트 갱신 강제 (085) | 완료 | tasks/085-opp-qa-checklist-enforcement/ | 2026-04-05 | 2026-04-05 |
| 0 | opi 최신화 모드 정밀도 개선 (084) | 완료 | tasks/084-opp-opi-update-mode-enhance/ | 2026-04-05 | 2026-04-05 |
| 0 | 하네스/스킬 문서 4건 정비 (083) | 완료 | tasks/083-opp-harness-plan-fixes/ | 2026-04-04 | 2026-04-04 |
| 0 | opsdd 스킬 설계 방안 검토 (080) | PLAN 대기 | tasks/080-opp-opsdd-design-proposal/ | 2026-04-03 17:00 | - |
| 0 | opi 프로젝트 최신화 (077) | 완료 | tasks/077-opi-project-update/ | 2026-04-03 | 2026-04-03 |
| 0 | xlsx-tool CLI + Python .venv 통합 (076) | 완료 | tasks/076-opp-xlsx-tool/ | 2026-04-03 | 2026-04-03 |
| 0 | oppd WBS 전환 태스크 (075) | 완료 | tasks/075-opp-oppd-wbs-transition/ | 2026-04-02 | 2026-04-02 |
| 0 | opi 프로젝트 최신화 (074) | 완료 | tasks/074-opi-project-update/ | 2026-04-02 | 2026-04-02 |
| 0 | OPAL 스킬 MCP 사전 확인 메커니즘 (073) | 완료 | tasks/073-opp-mcp-skill-registration/ | 2026-04-02 | 2026-04-02 |
| 0 | 오케스트레이터 게이트 점검 — TASK.md 체크박스 + 누락 게이트 (072) | 완료 | tasks/072-opp-gate-checklist-fix/ | 2026-04-02 | 2026-04-02 |
| 0 | wtm 스킬 개선 3건 통합 (070) | 완료 | tasks/070-opp-wtm-improvements/ | 2026-04-02 | 2026-04-02 |
| 0 | OPAL 하네스 개선 3건 통합 (071) | 완료 | tasks/071-opp-harness-improvements/ | 2026-04-02 | 2026-04-02 |
| 0 | 하네스 병렬 원칙 + opwt 재설계 (067) | 완료 | tasks/067-opp-harness-parallel-opwt-redesign/ | 2026-04-01 | 2026-04-01 |
| 0 | 오케스트레이터 스킬 게이트 (066) | 완료 | tasks/066-opp-orchestrator-skill-gate/ | 2026-04-01 21:10 | 2026-04-01 21:30 |
| 0 | 부트스트랩 Eager/Lazy + 서브에이전트 생략 (063) | 완료 | tasks/063-bootstrap-lazy-load/ | 2026-04-01 20:00 | 2026-04-01 21:00 |
| 0 | opwt IA JSON+Mermaid 이중 출력 (065) | 완료 | tasks/065-opwt-ia-mermaid/ | 2026-04-01 19:50 | 2026-04-01 20:00 |
| 0 | opwt 외부 API 명세서 관리 타입 추가 (064) | 완료 | tasks/064-opwt-external-api-spec/ | 2026-04-01 19:30 | 2026-04-01 19:45 |
| 0 | opwt 외부 참조 산출물 + wtm wireframe (062) | 완료 | tasks/062-opwt-external-refs/ | 2026-04-01 18:00 | 2026-04-01 19:00 |
| 0 | 부트스트랩 하네스 가드 (060) | 완료 | tasks/060-bootstrap-harness-guard/ | 2026-03-31 17:45 | 2026-03-31 18:30 |
| 1 | erd-modeler 스킬 범용화 (059) | 완료 | tasks/059-erd-modeler-universalize/ | 2026-03-31 17:00 | 2026-03-31 17:30 |
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
