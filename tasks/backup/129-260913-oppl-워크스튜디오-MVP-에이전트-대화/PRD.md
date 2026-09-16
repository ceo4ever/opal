# PRD: WorkStudio MVP Agent Conversation

## 1. 제품 목표

WorkStudio MVP는 사용자가 로컬 OPAL Project를 열거나 새로 만든 뒤, Project의 PM Agent를 등록하고 실제 Terminal 위에서 Codex Agent와 대화할 수 있게 만드는 첫 실행 가능한 제품 경로다. WorkStudio의 제품 목표는 여러 OPAL Project의 PM·Worker와 실행 환경을 하나의 Desktop 앱에서 발견하고 시작하고 대화하고 관찰하는 것이다 (`workstudio/BACKLOG.md` §1, lines 5-9).

이번 MVP의 성공은 인트로에서 Agent 대화까지 하나의 실제 Project로 이어지고, 핵심 경로에 `simulated` 또는 `not_connected` 경계가 남지 않는 상태다 (`workstudio/BACKLOG.md` §2, lines 11-22; `tasks/129-260913-oppl-워크스튜디오-MVP-에이전트-대화/TASK.md` lines 6-12).

## 2. 대상 사용자와 가치

### 대상 사용자

- 로컬 OPAL Project를 여러 개 다루는 사용자
- Project별 PM Agent를 발견하고 실행 상태를 관찰하려는 사용자
- Terminal과 Agent 대화를 같은 작업 공간에서 이어가려는 사용자

### 사용자 가치

| 기능 범위 | 사용자 가치 |
|---|---|
| WS-F102 Project 열기·생성 | 사용자는 기존 폴더를 열거나 새 Project 폴더를 만들어 WorkStudio의 현재 workspace로 바로 전환한다. |
| WS-F103 PM Agent 발견·등록 | 사용자는 `.opal/AGENT.md` 기반 PM Agent를 별도 설정 없이 실행 후보로 확인한다. |
| WS-F104 실제 PTY Terminal | 사용자는 Project cwd에서 실제 shell Terminal을 열고 입력·출력·resize·종료를 다룬다. |
| WS-F105 Agent Launcher | 사용자는 등록된 Project와 Terminal 맥락에서 지원 Agent를 실행한다. |
| WS-F106 Agent Conversation | 사용자는 대화 화면에서 메시지를 보내고 Agent 응답·진행·종료 상태를 화자별로 본다. |

근거: MVP 여정과 기능 후보는 WorkStudio 백로그에 WS-F102~F106으로 정의되어 있다 (`workstudio/BACKLOG.md` §5, lines 75-85). USER_JOURNEY는 같은 흐름을 인트로, Project 열기/생성, PM 등록, Terminal 생성, Codex 발동, 대화 수행으로 매핑한다 (`tasks/129-260913-oppl-워크스튜디오-MVP-에이전트-대화/USER_JOURNEY.md` lines 7-20, 54-67).

## 3. 제품 범위

### 포함 범위

- 저장 상태가 없을 때 인트로 화면을 표시한다.
- 기존 폴더를 Project로 열고 현재 workspace로 전환한다.
- 사용자가 선택한 위치에 신규 Project 폴더를 만든다.
- 신규 Project는 폴더와 최소 `.opal/AGENT.md`만 초기화한다. Git 저장소 초기화는 하지 않는다.
- `.opal/AGENT.md`를 기준으로 Project PM Agent를 발견하고 등록한다.
- MVP Agent는 Codex 하나로 제한한다.
- 등록 Project를 cwd로 사용하는 실제 PTY Terminal을 생성한다.
- Terminal 입력, 출력, resize, interrupt, close, 정상 종료, 비정상 종료를 사용자 상태로 표시한다.
- Codex Agent를 Terminal 세션에서 발동한다.
- PTY는 transport로 사용하고, Agent 상태·이벤트·메시지 변환은 구조화된 Codex adapter 경계가 소유한다.
- 앱 종료 시 WorkStudio가 소유한 PTY와 Agent 프로세스를 종료한다.
- 최종 여정 스모크는 인트로에서 신규 Project 생성, PM 등록, 실제 PTY Terminal 생성, Codex 발동, 메시지 전송, 응답 표시, 앱 종료 teardown까지 관통한다.

근거: MVP 범위는 백로그에 명시되어 있으며 (`workstudio/BACKLOG.md` §2, lines 24-32), 신규 Project, Codex 단일, adapter 경계, teardown 결정은 TASK 제약으로 확정되어 있다 (`tasks/129-260913-oppl-워크스튜디오-MVP-에이전트-대화/TASK.md` lines 26-30).

### 제외 범위

- 다중 PM Coordination 자동화
- Worker DAG와 병렬 실행 관리
- 내장 파일 편집기
- Git stage, commit, PR/MR
- 신규 Project 생성 시 Git init
- 원격 SSH, WSL, 컨테이너 Terminal
- Terminal 세션 복원과 Agent 대화 복원
- 자동 업데이트와 배포 서명

근거: WorkStudio 백로그의 MVP 제외 범위는 다중 PM Coordination, Worker DAG, 내장 파일 편집기, Git 작업, 원격 Terminal, 배포 서명을 제외한다 (`workstudio/BACKLOG.md` §2, lines 34-41). 세션 복원은 WS-M2 후보이며 MVP 이후 범위다 (`workstudio/BACKLOG.md` §4, lines 65-73; `tasks/129-260913-oppl-워크스튜디오-MVP-에이전트-대화/TASK.md` line 30).

## 4. 제품 경계와 플랫폼

WorkStudio는 Dashboard/Console과 분리된 Electron 데스크톱 앱이다. Project 문서에 따르면 `workstudio/`는 React, TypeScript, Vite, Electron 기반 독립 데스크톱 작업 앱이며 (`docs/PROJECT.md` lines 43-44), OPAL WorkStudio는 로컬 프로젝트 폴더 선택, 작업 공간, PM Coordination, 독립 Terminal, 파일 트리를 다루고 UI와 Electron preload/IPC 경계를 소유한다 (`docs/PROJECT.md` §주요 컴포넌트 (OPAL WorkStudio), lines 190-196).

Architecture 문서는 네이티브 폴더 선택, PM Coordination 작업 공간, 독립 Terminal, 파일 트리 UI가 Console이 아니라 WorkStudio 데스크톱 앱의 소유라고 구분한다 (`docs/ARCHITECTURE.md` §OPAL Console, lines 266-268). 코드 구조도 `workstudio/electron/`을 main/preload IPC 경계, `workstudio/src/`를 renderer로 둔다 (`docs/ARCHITECTURE.md` lines 489-491).

따라서 본 MVP의 검증 경로는 웹 서버·Swagger 중심이 아니라 실제 Electron renderer → preload IPC → Electron main → filesystem/PTY/Agent process 관통으로 정의해야 한다.

## 5. 사용자 여정

1. 저장된 workspace가 없으면 WorkStudio가 인트로를 연다.
2. 사용자는 기존 Project 폴더를 선택하거나 신규 Project 폴더를 만든다.
3. 시스템은 Project root를 검증하고 Project Registry에 저장한 뒤 현재 workspace로 전환한다.
4. 시스템은 `.opal/AGENT.md`에서 PM Agent를 발견하고 등록 후보로 표시한다.
5. 사용자는 PM Agent를 등록한다.
6. 사용자는 Project cwd에서 실제 Terminal을 생성한다.
7. 사용자는 Codex Agent를 발동한다.
8. 사용자는 대화 화면에서 메시지를 보내고 응답과 진행 상태를 확인한다.
9. Terminal 또는 앱 종료 시 시스템은 종료 상태를 표시하고 WorkStudio 소유 프로세스를 정리한다.

근거: 세부 여정은 USER_JOURNEY의 사용자 여정 표와 정상 흐름 다이어그램에 정의되어 있다 (`tasks/129-260913-oppl-워크스튜디오-MVP-에이전트-대화/USER_JOURNEY.md` lines 7-39).

## 6. 기능 요구사항

### F102. Project 열기·생성

- 기존 폴더 열기는 OS 폴더 선택기를 통해 사용자가 선택한 경로를 Project root 후보로 받아야 한다.
- 폴더 선택 취소는 실패가 아니라 인트로 유지 상태로 처리해야 한다.
- 선택한 경로가 접근 불가, 삭제됨, Project 조건 불충족이면 사용자에게 구분된 상태로 보여야 한다.
- 신규 Project 생성은 사용자가 선택한 위치와 이름으로 폴더를 만든 뒤 최소 `.opal/AGENT.md`를 초기화해야 한다.
- 신규 Project 생성은 Git 저장소를 초기화하지 않아야 한다.
- 유효한 Project는 기존 Project Registry에 저장하고 현재 workspace로 전환해야 한다.
- F101의 저장된 Project, 최근 접근 순서, 인트로, Files tree, workspace 화면 동작은 회귀하지 않아야 한다.

### F103. PM Agent 발견·등록

- Project root 안의 `.opal/AGENT.md`를 기준으로 PM Agent를 발견해야 한다.
- PM Agent가 발견되면 사용자가 등록할 수 있는 실행 후보로 표시해야 한다.
- PM Agent가 없거나 읽을 수 없으면 실행 후보 없음 상태를 표시하고 등록을 진행하지 않아야 한다.
- 등록된 PM Agent는 이후 Codex Agent 발동과 대화 화면의 Project 맥락으로 연결되어야 한다.

### F104. 실제 PTY Terminal

- Terminal은 등록된 Project root를 cwd로 사용해야 한다.
- Electron main이 PTY 프로세스를 소유하고 renderer는 typed preload IPC만 사용해야 한다.
- Terminal은 create, write, resize, interrupt, close를 지원해야 한다.
- Terminal event는 data, status, exit를 구분해야 한다.
- `cwd`는 등록된 Project root로 검증해야 한다.
- 출력 순서, resize, interrupt, 정상 종료, 비정상 종료, 앱 종료 시 teardown을 검증해야 한다.
- Terminal scrollback과 Agent 대화 기록은 PTY byte stream과 분리해 관리해야 한다.

근거: Terminal 구현 참조 계약은 Electron main의 TerminalGateway가 PTY 프로세스를 단독 소유하고 renderer가 typed preload IPC를 사용하도록 정의한다 (`workstudio/BACKLOG.md` §6, lines 97-131).

### F105. Agent Launcher

- MVP에서 사용자가 실행할 수 있는 Agent는 Codex 하나로 제한한다.
- Agent 실행 명령은 등록된 Agent adapter가 구성해야 하며, renderer가 임의 실행 파일을 직접 지정하지 않아야 한다.
- Agent는 Project cwd의 Terminal 세션에서 실제로 발동되어야 한다.
- 실행 중, 시작 실패, 명령 실패, 정상 종료, 비정상 종료를 구분해야 한다.

### F106. Agent Conversation

- 사용자는 대화 화면에서 메시지를 입력하고 Agent 세션으로 전송할 수 있어야 한다.
- 시스템은 Agent 응답, 진행, 종료 상태를 화자별로 구분해 표시해야 한다.
- PTY transport와 사용자 대화 모델은 분리되어야 한다.
- Codex adapter는 PTY byte stream에서 대화 이벤트와 상태 이벤트를 구조화해 renderer로 전달해야 한다.
- Terminal이 종료되면 대화 입력을 비활성화하고 재시작 또는 새 Terminal 생성 경로를 제공해야 한다.

## 7. 상태와 예외 흐름

| 상태 | 제품 요구 |
|---|---|
| 폴더 선택 취소 | 인트로를 유지하고 기존 workspace 또는 Project Registry를 변경하지 않는다. |
| 잘못된 Project 경로 | 접근 불가, 삭제됨, Project 조건 불충족을 구분해 표시한다. |
| 신규 Project 생성 실패 | 권한, 중복 이름, 파일 생성 실패를 구분해 재시도 가능하게 한다. |
| PM Agent 미발견 | 실행 후보 없음 상태를 표시하고 PM 등록과 Agent 발동을 막는다. |
| Terminal 생성 실패 | shell, cwd, 권한 오류를 Terminal 생성 실패로 표시한다. |
| Agent 실행 실패 | adapter 시작 실패, 명령 실패, 종료 코드를 구분해 표시한다. |
| Terminal 예기치 못한 종료 | 대화 입력을 비활성화하고 exit code 또는 signal을 보여준다. |
| 앱 종료 | WorkStudio가 소유한 PTY와 Agent 프로세스를 teardown한다. |

근거: 취소·실패·종료 상태는 USER_JOURNEY에 복구 경로와 함께 정의되어 있다 (`tasks/129-260913-oppl-워크스튜디오-MVP-에이전트-대화/USER_JOURNEY.md` lines 41-52). TASK도 취소, 잘못된 경로, Agent 실행 실패, Terminal 종료를 구분된 사용자 상태로 표시해야 한다고 정의한다 (`tasks/129-260913-oppl-워크스튜디오-MVP-에이전트-대화/TASK.md` lines 10-12, 32-43).

## 8. 수용 기준

| ID | 기준 |
|---|---|
| PRD-AC-01 | 저장 상태가 없는 WorkStudio 실행에서 인트로가 열리고, 기존 Project 열기와 신규 Project 생성 액션이 표시된다. |
| PRD-AC-02 | 기존 폴더를 선택하면 Project root 검증 후 현재 workspace로 전환되고 Project Registry에 저장된다. |
| PRD-AC-03 | 신규 Project 생성은 폴더와 최소 `.opal/AGENT.md`를 만들며 Git 저장소를 초기화하지 않는다. |
| PRD-AC-04 | `.opal/AGENT.md`가 있는 Project를 열면 PM Agent가 발견되고 등록 후 실행 후보로 표시된다. |
| PRD-AC-05 | 등록 Project를 cwd로 사용하는 실제 PTY Terminal을 생성하고 입력, 출력, resize, interrupt, close, 종료 이벤트를 관찰할 수 있다. |
| PRD-AC-06 | Codex Agent를 선택하면 Project Terminal 세션에서 실제로 발동되고 실행 중, 실패, 종료 상태가 구분된다. |
| PRD-AC-07 | 대화 화면에서 보낸 메시지가 실제 Agent 세션에 전달되고 응답, 진행, 종료 상태가 화자별로 표시된다. |
| PRD-AC-08 | 폴더 선택 취소, 생성 실패, PM 미발견, Terminal 생성 실패, Agent 실행 실패, Terminal 예기치 못한 종료가 서로 다른 복구 가능 상태로 표시된다. |
| PRD-AC-09 | 앱 종료 시 WorkStudio가 소유한 PTY와 Agent 프로세스가 teardown되고 세션 복원은 수행하지 않는다. |
| PRD-AC-10 | 인트로→Project 열기/생성→PM 등록→Terminal 생성→Agent 발동→대화 수행 E2E가 하나의 실제 Project에서 통과하고 핵심 경로 mock 경계가 0건이다. |
| PRD-AC-11 | 기존 WS-F101 Project Registry, 인트로, Files tree, workspace 화면 회귀 테스트가 통과한다. |
| PRD-AC-12 | OPPL 실행 스켈레톤은 Electron renderer→preload→main 관통을 판정하고, WorkStudio MVP에 BE 서버·Swagger를 요구하지 않는다. |

근거: TASK 수용 기준은 기존 폴더 열기·신규 Project 생성, `.opal/AGENT.md` 기반 PM 발견, 실제 PTY Terminal, Agent 발동, 대화 전달, E2E mock 0, 오류 상태 구분, F101 회귀, Electron 실행 스켈레톤, PTY·Agent 통합 검증을 요구한다 (`tasks/129-260913-oppl-워크스튜디오-MVP-에이전트-대화/TASK.md` lines 32-43).

## 9. 회귀 경계

WS-F101은 MVP의 선행 기반이며 새 구현의 직접 변경 대상이 아니라 회귀 보호 대상이다. Project Registry는 등록한 Project와 최근 접근 순서가 재실행 후에도 유지되는 기능으로 이미 `done` 상태다 (`workstudio/BACKLOG.md` §5, lines 79-80).

MVP 구현은 다음을 깨지 않아야 한다.

- 저장된 Project 목록과 최근 접근 순서
- 저장 상태가 없을 때 인트로 표시
- 현재 workspace 전환
- Files tree와 workspace 화면의 기본 표시
- Project Registry를 중복하는 별도 사실 저장소 미생성

근거: TASK는 Project Registry, 인트로, Files tree, workspace 화면의 회귀 테스트 통과를 수용 기준으로 둔다 (`tasks/129-260913-oppl-워크스튜디오-MVP-에이전트-대화/TASK.md` lines 40-41). 신규 Project 생성은 기존 Project Registry와 중복되는 별도 저장소를 만들지 않는다는 제약도 있다 (`tasks/129-260913-oppl-워크스튜디오-MVP-에이전트-대화/TASK.md` lines 23-24).

## 10. OPPL 선행 요구

현재 OPPL의 일반 실행 스켈레톤은 웹 프로젝트의 BE 서버, Swagger 또는 OpenAPI UI, FE dev server, FE→BE 실호출 관통을 전제로 한다. WorkStudio는 별도 Electron 데스크톱 앱이므로 (`docs/PROJECT.md` lines 190-196; `docs/ARCHITECTURE.md` lines 489-491), MVP 실행 전에 OPPL이 Electron 프로젝트를 동등한 실행 스켈레톤으로 판정할 수 있어야 한다.

Electron 프로필은 최소한 다음을 판정해야 한다.

- Electron 앱이 실행된다.
- renderer 화면이 preload IPC를 통해 Electron main에 실제 요청을 보낸다.
- Electron main이 filesystem 또는 PTY 같은 로컬 기능을 수행한다.
- 결과 이벤트가 renderer로 돌아와 사용자 화면 상태를 바꾼다.
- 이 경로가 HTTP 서버나 Swagger 부재 때문에 실패 처리되지 않는다.

이 요구는 WorkStudio 기능 자체가 아니라 MVP 검증을 가능하게 하는 선행 품질 요구다.

## 11. 측정과 검증

| 검증 대상 | 측정 방법 |
|---|---|
| 핵심 여정 연결 | 저장 상태 없는 실행에서 USER_JOURNEY의 정상 흐름을 신규 Project 기준으로 1회 관통한다. |
| 기존 Project 경로 | 기존 OPAL Project 선택 후 PM Agent 발견과 Codex 실행 후보 표시까지 관통한다. |
| 실제 PTY | PTY 생성, 입력, 출력, resize, interrupt, close, exit event를 자동 테스트로 확인한다. |
| Agent 발동 | Codex adapter가 실제 Terminal 세션에서 시작·실패·종료 상태를 구조화하는지 확인한다. |
| 대화 수행 | 사용자 메시지 전송 후 Agent 응답 또는 진행 이벤트가 화자별로 표시되는지 확인한다. |
| 오류 상태 | 취소, 생성 실패, PM 미발견, Terminal 실패, Agent 실패, 예기치 못한 종료를 각각 독립 시나리오로 확인한다. |
| F101 회귀 | Project Registry, 인트로, Files tree, workspace 화면의 기존 테스트를 함께 실행한다. |
| OPPL Electron 프로필 | renderer→preload→main 관통 증거가 있는 실행 스켈레톤으로 판정한다. |

## 12. 결정 완료와 남은 결정

### 결정 완료

- 신규 Project는 폴더와 최소 `.opal/AGENT.md`만 초기화한다.
- 신규 Project 생성에서 Git init은 제외한다.
- MVP Agent는 Codex 하나로 제한한다.
- Agent 대화는 PTY transport를 사용하되, 상태·이벤트·메시지 변환은 구조화된 Codex adapter가 소유한다.
- 앱 종료 시 WorkStudio 소유 PTY와 Agent 프로세스를 teardown한다.
- 세션 복원은 MVP 이후로 이월한다.

### 남은 결정

없음. 위 결정은 TASK 제약과 USER_JOURNEY에 반영되어 있으며, 구현 중 외부 노출 계약 변경이나 MVP 범위 확장이 발견되면 OPPL 거버넌스에 따라 별도 결정을 요청해야 한다.

## 13. 개발자 부록: 근거가 되는 기술 경계

- `workstudio/`는 React+TypeScript+Vite+Electron 기반 독립 데스크톱 앱이다 (`docs/PROJECT.md` lines 43-44, 241-246).
- WorkStudio는 Dashboard/Console과 실행 경로를 공유하지 않고 UI와 Electron preload/IPC 경계를 소유한다 (`docs/PROJECT.md` lines 190-196).
- Architecture의 코드 구조는 `workstudio/electron/`을 main/preload IPC 경계, `workstudio/src/`를 renderer로 둔다 (`docs/ARCHITECTURE.md` lines 489-491).
- TerminalGateway는 Electron main에서 PTY 프로세스를 단독 소유하고 renderer는 typed preload IPC만 사용한다 (`workstudio/BACKLOG.md` lines 108-110).
- Terminal 계약은 create, write, resize, interrupt, close와 data, status, exit 이벤트를 포함한다 (`workstudio/BACKLOG.md` lines 112-122).
- Terminal 필수 원칙은 등록 Project root 검증, adapter가 실행 명령 구성, 출력·resize·interrupt·종료·teardown 검증, scrollback과 Agent 대화 기록 분리를 포함한다 (`workstudio/BACKLOG.md` lines 124-131).
