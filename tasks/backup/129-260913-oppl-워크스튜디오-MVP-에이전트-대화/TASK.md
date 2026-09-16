---
template: sdlc-v2
---
# TASK: WorkStudio MVP Agent Conversation

## Problem

WorkStudio는 Project Registry까지는 영속화했지만, 기존 폴더 열기와 신규 Project 생성 이후의 PM Agent 발견, 실제 PTY Terminal, Agent 발동, 양방향 대화가 아직 하나의 실제 경로로 연결되지 않았다. WS-F102~F106은 모두 후보 상태이며 MVP 완료 조건은 인트로에서 Agent 대화까지 핵심 경로에 `simulated` 또는 `not_connected` 경계가 남지 않는 것이다 (`workstudio/BACKLOG.md:11`, `workstudio/BACKLOG.md:22`, `workstudio/BACKLOG.md:81`).

## Proposed outcome

사용자가 WorkStudio 인트로에서 기존 Project를 열거나 신규 Project를 만들고, 해당 Project의 PM Agent를 발견해 등록한 뒤 Project cwd의 실제 PTY Terminal에서 지원 Agent를 발동하여 메시지와 응답을 대화 화면에서 주고받는다. 취소·잘못된 경로·Agent 실행 실패·Terminal 종료는 구분된 사용자 상태로 표시된다 (`workstudio/BACKLOG.md:11`, `workstudio/BACKLOG.md:24`).

## Affected users and systems

WorkStudio 데스크톱 앱 사용자와 `workstudio/`의 Electron main, preload IPC, React renderer, Project Registry, Terminal·Agent 세션 상태 및 테스트가 영향받는다. 데스크톱 수직 슬라이스를 올바르게 검증하도록 `oppl`의 실행 스켈레톤 계약도 필요한 최소 범위에서 영향받는다. 다중 PM Coordination 자동화, Worker DAG, 내장 편집기, Git 작업, 원격 Terminal, 배포 패키징은 제외한다 (`workstudio/BACKLOG.md:34`).

## Constraints

- C-1: Project 파일 시스템, PTY, Agent 프로세스는 Electron main이 소유하고 renderer는 typed preload IPC만 사용한다 (`workstudio/BACKLOG.md:105`).
- C-2: `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`를 포함한 기존 보안 경계를 유지한다 (`workstudio/electron/main.cjs:260`).
- C-3: Orca Terminal은 UX와 생명주기 참조용으로만 사용하고 비공개 코드를 import하거나 복사하지 않는다 (`workstudio/BACKLOG.md:103`).
- C-4: MVP 핵심 경로에 mock·`simulated`·`not_connected` 대체를 두지 않고 실제 프로세스와 실제 IPC/PTY 사용으로 검증한다 (`workstudio/BACKLOG.md:22`).
- C-5: 신규 Project 생성은 기존 Project Registry와 중복되는 별도 사실 저장소를 만들지 않는다 (`workstudio/electron/project-registry.cjs:75`).
- C-6: Agent 프로세스 실패·PTY 종료·잘못된 Project 경로는 비정상 종료로 숨기지 않고 명시적 상태로 표시한다 (`workstudio/BACKLOG.md:31`).
- C-7: Electron 데스크톱 프로젝트에 `oppl`을 적용할 때 불필요한 HTTP 서버·Swagger를 생성하지 않고, 실제 renderer→preload→main 관통을 동등한 실행 스켈레톤으로 검증할 수 있게 한다 (`opal/skills/opal-pilot-project-loop/SKILL.md` §Loop 1 — D5).
- C-8: 신규 Project는 MVP에서 폴더와 최소 `.opal/AGENT.md`만 생성하며 Git 저장소 초기화는 하지 않는다.
- C-9: MVP 최초 지원 Agent는 Codex 하나로 제한한다.
- C-10: Agent 대화는 PTY를 transport로 사용하되, 상태·이벤트·메시지 변환은 Codex adapter 경계가 소유한다.
- C-11: 앱 종료 시 WorkStudio가 소유한 PTY·Agent 프로세스를 종료하며 세션 복원은 WS-M2로 이월한다.

## Acceptance criteria

- AC-1: 기존 폴더를 Project로 열거나 사용자가 선택한 위치에 신규 Project 폴더를 만들어 현재 workspace로 전환할 수 있다.
- AC-2: OPAL Project를 열면 `.opal/AGENT.md`의 PM Agent가 발견되고 등록 후 실행 후보로 표시된다.
- AC-3: 등록 Project를 cwd로 사용하는 실제 PTY Terminal을 생성하고 입력·출력·resize·종료를 수행할 수 있다.
- AC-4: MVP에서 확정한 최초 지원 Agent를 선택해 Project Terminal 세션에서 실제로 발동하고 실행·실패·종료 상태를 구분할 수 있다.
- AC-5: 사용자가 대화 화면에서 메시지를 전송하면 실제 Agent 세션에 전달되고 응답·진행·종료 상태가 화자별로 구분되어 표시된다.
- AC-6: 인트로→Project 열기/생성→PM 등록→Terminal 생성→Agent 발동→대화 수행 전체가 하나의 실제 Project에서 E2E로 통과하고 핵심 경로의 mock 경계가 0건이다.
- AC-7: 폴더 선택 취소, 생성 실패, PM 미발견, Agent 실행 실패, Terminal 예기치 못한 종료가 각각 구분된 복구 가능 상태로 표시된다.
- AC-8: 기존 WS-F101 Project Registry, 인트로, Files tree, workspace 화면의 회귀 테스트가 통과한다.
- AC-9: `oppl`이 Electron 프로젝트에서 실제 renderer→preload→main 관통을 실행 스켈레톤으로 판정하며 BE 서버·Swagger를 요구하지 않는다.
- AC-10: 실제 PTY·Agent 통합 경로와 보안 경계가 자동 테스트 및 최종 여정 스모크로 검증된다.
