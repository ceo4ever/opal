# BACKLOG: WorkStudio MVP Agent Conversation

> 최종 갱신: 2026-09-13 01:35
> 모드: agentic
> 목표: Intro부터 실제 Codex Agent 대화까지 WS-F102~F106 완주

<!-- backlog:start -->
## 백로그

> 상태값: pending / in_progress / done / blocked

| ID | 제목 | 영역 | 우선순위 | 상태 | 의존 | 커버 표면 |
|----|------|------|--------|------|------|----------|
| T001 | OPPL Electron 실행 스켈레톤 프로필 | 공통 | P0 | pending | - | intro-first-run, project-open-existing, oppl-electron-profile |
| T002 | WS-F102 Project 생성·열기 | 통합 | P0 | pending | T001 | project-open-existing, project-create-new |
| T003 | WS-F103 PM Agent 발견·등록 | 통합 | P0 | pending | T002 | pm-discover-register |
| T004 | WS-F104 TerminalGateway 및 typed IPC | be | P0 | pending | T001, T002 | terminal-create, terminal-io-control, terminal-events, app-teardown |
| T005 | WS-F104 실제 Terminal UI 연결 | fe | P1 | pending | T004 | terminal-create, terminal-io-control, terminal-events |
| T006 | WS-F105 Codex Agent Launcher | be | P1 | pending | T003, T004 | agent-list-launch, agent-send-stop, app-teardown |
| T007 | WS-F106 Agent Conversation | fe | P1 | pending | T005, T006 | agent-send-stop, agent-conversation-events |
| T008 | WorkStudio MVP 최종 여정 통합 | 통합 | P2 | pending | T003, T005, T006, T007 | intro-first-run, project-open-existing, project-create-new, pm-discover-register, workspace-files-tree, terminal-create, terminal-io-control, terminal-events, agent-list-launch, agent-send-stop, agent-conversation-events, app-teardown, journey-smoke, oppl-electron-profile |
<!-- backlog:end -->
