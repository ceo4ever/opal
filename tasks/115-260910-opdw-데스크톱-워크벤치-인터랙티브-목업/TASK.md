---
template: sdlc-v2
---
# TASK: OPAL Product OS 데스크톱 Workbench 인터랙티브 목업

## Problem

OPAL Product OS의 제안 범위는 Project·Workstream·Task·Run과 Agent·Terminal·Browser·Files·Diff·Result를 한 Workbench에 결합한다. 현재는 이 구조를 설명하는 제안서만 있고, 사용자가 실제 데스크톱 화면에서 정보 구조·멘션·위임·Run 상태·검증 흐름을 클릭하며 검토할 수 없다. 이 상태에서 ACP·PTY·Browser·Worktree Runtime을 먼저 구현하면 화면과 사용 흐름이 바뀐 때 고비용 재작업이 발생한다 (`docs/proposals/opal-product-os-desktop-workbench.md` §16 MVP와 단계별 구현).

## Proposed outcome

실제 Electron 창에서 실행되는 React 기반 인터랙티브 목업을 만든다. 사용자는 OPAL 프로젝트의 대표 Task를 생성하고, `@OPAL PM`에게 지시하고, PM이 전문 Agent에게 위임하고, Agent Run의 진행·Terminal·Browser·파일 변경·Git Diff·검증·결과를 하나의 Workbench에서 확인한다. 모든 실행 결과는 목업 데이터로 제공하고 Runtime 연동 전에 제품 구조와 인터랙션을 확정할 수 있게 한다 (`docs/proposals/opal-product-os-desktop-workbench.md` §5 주요 사용자 흐름, §10 Workbench UX).

## Affected users and systems

- 사용자: OPAL을 활용해 하나 이상의 LLM CLI에 업무를 지시하고 결과를 검토하는 1인 개발자.
- 시스템: `dashboard/frontend/`의 React·TypeScript·Vite UI, 신규 Electron shell, 목업 데이터와 로컬 UI 상태.
- 포함: Project·Workstream·Task 탐색, Task 생성·Kanban 이동, Agent 설정, Conversation·멘션·위임, Run 상태, Workbench Tool View, Activity Log, Result 검토, 목업 복원.
- 제외: 실제 ACP Agent 세션, LLM API·CLI 프로세스, node-pty, agent-browser·Playwright 제어, Git Worktree, 실제 파일 변경, SQLite, 운영용 보안·패키징.

## Constraints

- C-1: 목업은 Runtime 연동 완료를 주장하지 않고, 목업·시뮬레이션·미구현 상태를 UI에서 명확히 구분한다.
- C-2: 대표 흐름은 `Project → Workstream → Task → Conversation → Run → Verification → Result`로 유지한다. Run보다 오래 살아있는 도구 상태는 Execution Environment 개념으로 표현한다 (`docs/proposals/opal-product-os-desktop-workbench.md` §4 용어와 도메인 모델).
- C-3: `.opal/AGENT.md`는 OPAL PM으로 발견된 목업 Agent Definition으로 표현하고, Agent 정의와 runtime·model 연결 설정을 분리한다 (`docs/proposals/opal-product-os-desktop-workbench.md` §9 Agent 모델).
- C-4: 사용자 지정 Agent를 추가하고 `@mention`으로 PM·전문 Agent를 호출하는 경로를 포함한다.
- C-5: Conversation·Run·Tool·Verification·Result 이력은 하나의 Task Activity로 연결하되, 대용량 원본 로그를 기본 화면에 무제한으로 노출하지 않는다 (`docs/proposals/opal-product-os-desktop-workbench.md` §13 데이터와 로그).
- C-6: 기존 Console의 주요 화면과 스타일 자산을 재사용할 수 있게 하고, 목업 검증을 위해 관계없는 Console 기능을 제거하지 않는다 (`docs/PROJECT.md` §주요 컴포넌트 (OPAL Console)).
- C-7: 데스크톱 창은 현재 React/Vite 기반을 사용하며, 새 UI 상태는 실제 Runtime으로 교체 가능한 목업 경계 뒤에 둔다 (`dashboard/frontend/package.json:6-47`).
- C-8: 데스크톱 핵심 흐름을 우선하고 Monaco·split pane 고도화·실제 session recovery·배포 packaging은 후속 태스크로 이월한다.
- C-9: 소스 수정 전에 wireframe.md를 확정하고, 구현은 그 화면 목록과 인터랙션을 임의로 확장하지 않는다.

## Acceptance criteria

- AC-1: Electron 앱이 로컬에서 실행되고 React Workbench를 데스크톱 창에 표시한다.
- AC-2: 사용자가 OPAL Project에서 Product·Development·Review Workstream을 전환하고 Task 목록과 상태를 확인할 수 있다.
- AC-3: 사용자가 Task를 생성하고 Kanban 상태를 이동한 후 선택한 Task의 Workbench로 진입할 수 있다.
- AC-4: Agent Catalog에 OPAL PM·Developer·Reviewer와 사용자 추가 Agent가 표시되며, 각 Agent의 역할·runtime·model·상태를 확인하고 목업 설정을 변경할 수 있다.
- AC-5: Task Conversation에서 `@OPAL PM`과 `@Developer`를 멘션하면 각각 PM 응답·위임과 Developer Run 생성을 시뮬레이션한다.
- AC-6: 하나의 Task에서 Conversation·Terminal·Browser·Files·Diff·Result 화면을 전환하고 각 화면의 대표 목업 데이터를 확인할 수 있다.
- AC-7: Run의 queued·running·waiting·completed·failed 상태와 진행 중인 단계가 Workbench 내에 구분되어 표시된다.
- AC-8: Browser 조작 기록과 Playwright 검증 결과가 다른 정보로 표시되고, PASS/FAIL에 수용 기준과 증거 목업이 연결된다.
- AC-9: Activity Log에 대화·위임·Run·도구·파일 변경·검증·결과 사건이 시간순으로 나타난다.
- AC-10: 선택한 Project·Workstream·Task·Tool View와 목업 대화 상태가 앱 재실행 후 복원되는 시나리오를 시뮬레이션한다.
- AC-11: 빈 Task·Run 진행·Agent 응답 대기·Run 실패·검증 실패의 주요 상태가 각각 검토 가능한 화면으로 존재한다.
- AC-12: 제품 검토자가 대표 시나리오를 처음부터 끝까지 클릭하고 Project·Workstream·Task·Run·Environment의 관계, PM 위임 흐름, 결과 승인 위치를 판단할 수 있다.
- AC-13: 변경된 프런트엔드는 lint·typecheck·build를 통과하고 목업용 핵심 흐름을 검증하는 테스트가 통과한다.

## Open questions

없음. 시각 스타일·상세 레이아웃·상호작용 배치는 WIREFRAME 단계에서 제안하고 사용자 검토로 확정한다.
