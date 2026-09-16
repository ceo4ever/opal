# TRD: WorkStudio MVP Agent Conversation

## 1. 기술 목표

WorkStudio MVP는 인트로에서 Project 열기/생성, PM Agent 등록, 실제 PTY Terminal 생성, Codex Agent 발동, 대화 수행까지 하나의 Electron 데스크톱 경로로 연결한다. 완료 상태는 핵심 경로에 `simulated` 또는 `not_connected` 대체가 남지 않는 것이다 (`PRD.md` lines 3-7; `TASK.md` lines 6-12).

WorkStudio는 Dashboard/Console과 분리된 Electron 앱이며, UI와 preload/IPC 경계를 `workstudio/`가 소유한다 (`docs/PROJECT.md` lines 190-196). 현재 코드 구조도 `workstudio/electron/`을 main/preload IPC 경계, `workstudio/src/`를 renderer로 둔다 (`docs/ARCHITECTURE.md` lines 489-491). 따라서 기술 검증은 웹 서버가 아니라 Electron renderer → preload → main → filesystem/PTY/Agent process → renderer event의 관통으로 정의한다.

## 2. 현재 상태 AS-IS

### 이미 실제 경계가 있는 영역

- Electron main은 Project Registry를 `app.getPath("userData")/project-registry.json`에 저장하고, preload IPC로 Project 선택·등록·최근 목록·파일 트리를 제공한다 (`workstudio/electron/main.cjs` lines 38-45, 240-249).
- BrowserWindow 보안 설정은 `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`로 구성되어 있다 (`workstudio/electron/main.cjs` lines 251-263).
- preload는 `contextBridge.exposeInMainWorld("opalWorkStudio", { project })`만 노출하며, renderer는 `chooseDirectory`, `registerFromSelection`, `listRecent`, `listFiles` 같은 project API를 사용한다 (`workstudio/electron/preload.cjs` lines 11-24; `workstudio/src/workstudio/ipc.ts` lines 69-80).
- 파일 트리는 등록된 root 내부만 읽도록 realpath와 registered root 검증을 수행한다 (`workstudio/electron/main.cjs` lines 168-188).
- Project Registry는 `.opal/AGENT.md` 존재 여부로 OPAL Project를 감지하고 `agentPath`, `pmName`을 채운다 (`workstudio/electron/project-registry.cjs` lines 42-73).
- F101 회귀 테스트는 Project Registry 저장, realPath 중복 제거, missing/repair, registry 삭제와 데이터 보존, corrupt registry 복구를 검증한다 (`workstudio/electron/main.test.mjs` lines 53-160).

### 아직 mock에 머무는 영역

- domain type에는 `Boundary = "actual" | "simulated" | "not_connected"`가 있으며 RuntimeBinding은 현재 `boundary: "simulated"`로 고정되어 있다 (`workstudio/src/workstudio/types.ts` lines 11-17, 96-103).
- mock adapter는 terminal output을 `mock: ... [Simulated]`로 생성하고, environment boundary를 `not_connected`로 seed한다 (`workstudio/src/workstudio/mock-adapter.ts` lines 64-74, 114-123).
- Terminal surface는 UI에서 cwd와 shell 이름을 보여주지만 `BoundaryBadge type="simulated"`를 표시한다 (`workstudio/src/workstudio/WorkStudioApp.tsx` lines 927-967).
- Terminal 입력 처리는 실제 PTY가 아니라 `pwd`, `ls`, 그 외 mock 문자열을 renderer에서 직접 생성한다 (`workstudio/src/workstudio/WorkStudioApp.tsx` lines 1590-1611).
- Agent CLI surface는 관찰 전용 UI와 message list만 있고 역시 `BoundaryBadge type="simulated"`이다 (`workstudio/src/workstudio/WorkStudioApp.tsx` lines 992-1011).
- 현재 테스트도 “mock flow”와 “shell-like” UI를 검증하며 실제 PTY/Agent process를 검증하지 않는다 (`workstudio/src/workstudio/WorkStudioApp.test.tsx` lines 23-24, 403-424).

## 3. 목표 아키텍처 TO-BE

### 원칙

- Electron main이 filesystem, Project 생성, PTY, Agent process를 소유한다.
- renderer는 typed preload IPC와 구독 이벤트만 사용한다.
- Project Registry는 Project의 단일 사실 저장소로 유지한다.
- Terminal byte stream과 Agent conversation store는 분리한다.
- Codex adapter가 실행 명령, lifecycle, PTY event 해석, conversation event 변환을 소유한다.
- 앱 종료 시 WorkStudio가 생성한 PTY와 Agent process를 모두 teardown한다. 세션 복원은 MVP 범위 밖이다 (`TASK.md` lines 26-30; `PRD.md` lines 204-217).

### 구성

```text
Renderer UI
  ├─ Project onboarding / workspace
  ├─ Terminal surface
  └─ Agent conversation surface
        │ typed preload API + event subscriptions
Preload bridge
        │ ipcRenderer.invoke / ipcRenderer.on wrappers
Electron main
  ├─ ProjectGateway
  ├─ ProjectRegistry
  ├─ AgentRegistry
  ├─ TerminalGateway
  ├─ CodexAgentAdapter
  └─ ConversationStore
        │
Filesystem / node-pty / Codex CLI process
```

근거: Terminal 참조 계약은 Electron main의 `TerminalGateway`가 PTY를 단독 소유하고 renderer는 typed preload IPC만 사용하도록 정의한다 (`workstudio/BACKLOG.md` lines 108-131). Project·PTY·Agent process는 Electron main 소유라는 TASK 제약도 동일하다 (`TASK.md` lines 18-30).

## 4. 책임 경계

| 영역 | 책임 | 금지/주의 |
|---|---|---|
| Project create/open | 기존 폴더 선택, 신규 폴더 생성, 최소 `.opal/AGENT.md` 초기화, root realpath 검증, registry 등록 | 신규 Project에서 Git init 금지. Project Registry와 중복되는 별도 저장소 금지 (`TASK.md` lines 23-27). |
| PM discovery/registration | `.opal/AGENT.md` 존재 확인, agent path와 표시명 구성, Project state의 실행 후보 등록 | renderer가 파일을 직접 읽거나 Agent 실행 파일을 결정하지 않음. |
| TerminalGateway | PTY 생성, write, resize, interrupt, close, data/status/exit event emit, teardown | cwd는 등록 Project root여야 함. renderer 임의 cwd 금지 (`workstudio/BACKLOG.md` lines 124-130). |
| typed IPC/preload | project, terminal, agent, conversation API를 좁은 함수로 노출하고 event unsubscribe를 제공 | Node API, shell, filesystem 객체를 renderer에 노출하지 않음 (`workstudio/src/workstudio/ipc.test.ts` lines 20-40). |
| Codex adapter | Codex 실행 명령 구성, PTY transport 연결, ready/running/failed/exited 상태 변환, conversation event 추출 | renderer가 임의 command/path/args를 전달하지 않음 (`workstudio/BACKLOG.md` lines 126-128). |
| Conversation store/UI | 사용자 메시지, Agent 응답, 진행, 종료 event를 화자별로 표시하고 Terminal scrollback과 분리 | PTY byte stream을 대화 기록 원본으로 그대로 저장하지 않음. |

## 5. 기술 요구사항

### 5.1 Project create/open

- 기존 `chooseDirectory`, `registerFromSelection`, `listRecent`, `openRecent`, `repairRecent`, `removeRecent`, `listFiles` 계약을 유지한다 (`workstudio/src/workstudio/ipc.ts` lines 69-80).
- `createProject` IPC를 추가해 사용자가 지정한 parent path와 Project name으로 폴더를 만들고 `.opal/AGENT.md`를 생성한다.
- `createProject`는 Git 저장소를 만들지 않는다.
- 생성된 Project는 즉시 기존 Project Registry에 등록한다.
- 생성 실패는 `create_failed`, `permission_denied`, `duplicate_path`, `invalid_path`처럼 복구 가능한 오류 코드로 반환한다.
- 기존 폴더 선택 취소는 `cancelled`로 처리하고 workspace state를 변경하지 않는다. 현재 first-run 테스트가 취소 시 welcome 유지 상태를 검증한다 (`workstudio/src/workstudio/FirstRunWelcome.test.tsx` lines 48-65).

### 5.2 PM discovery/registration

- Project 등록 시 `.opal/AGENT.md` 존재 여부는 Electron main에서 확인한다. 현재 registry는 marker 접근 가능 여부로 `isOpalProject`, `agentPath`, `pmName`을 채운다 (`workstudio/electron/project-registry.cjs` lines 51-68).
- MVP에서는 `.opal/AGENT.md` 전문 파싱 없이 marker 기반 PM 등록을 유지하되, `agentPath`, `projectId`, `displayName`, `source: "project"`, `status: "ready"`를 renderer state에 반영한다.
- PM 미발견은 Project 등록 실패가 아니라 Agent 실행 후보 없음 상태다. 이 상태에서는 Agent Launcher를 비활성화한다 (`USER_JOURNEY.md` lines 45-52).

### 5.3 TerminalGateway

- main process에 `TerminalGateway`를 추가한다.
- Gateway는 `terminalId`, `projectId`, `cwd`, `shell`, `cols`, `rows`, `status`, `exitCode`, `signal`, `createdAt`, `updatedAt`을 가진 in-memory session map을 소유한다.
- `cwd`는 Project Registry에 등록된 root와 동일하거나 그 하위 경로여야 한다. MVP 기본값은 Project root다.
- 실제 PTY 구현은 `node-pty` 도입을 1순위 후보로 한다. WorkStudio 현재 dependencies/devDependencies와 lockfile에는 `node-pty`가 없으므로 신규 의존성 추가가 필요하다 (`workstudio/package.json` lines 17-71; lockfile 검색 결과 `node-pty` 없음).
- `node-pty`는 Electron 네이티브 모듈 rebuild가 필요한 플랫폼 빌드 리스크가 있다. 구현 태스크는 macOS 우선 검증, Electron 버전 호환, CI/로컬 `npm install`/`npm run desktop` 실패 가능성, packaging 전 `electron-rebuild` 또는 대체 빌드 절차 필요 여부를 확인해야 한다.
- shell 기본값은 OS 기본 shell을 사용하되, UI에는 실제 shell명을 표시한다. 현재 UI는 zsh 문자열을 정적으로 표시하므로 실제 session metadata로 대체해야 한다 (`workstudio/src/workstudio/WorkStudioApp.tsx` lines 927-967).

### 5.4 Codex adapter

- MVP Agent는 Codex 하나다 (`TASK.md` line 28; `PRD.md` lines 204-213).
- adapter는 main process에서만 실행 명령을 구성한다. renderer는 agent id와 terminal id 또는 project id만 전달한다.
- adapter는 Codex CLI 가용성 점검, launch, prompt write, status parse, exit handling을 소유한다.
- adapter event는 최소 `starting`, `running`, `waiting_input`, `message`, `failed`, `exited`로 정규화한다.
- adapter는 PTY transport를 사용하되 conversation store에는 구조화 event만 전달한다.
- MVP에서는 Codex session 복원은 하지 않는다. 앱 종료 또는 terminal close 시 agent session도 종료한다.

### 5.5 Conversation store/UI

- conversation store는 renderer state 또는 main-side volatile store 중 하나로 시작할 수 있지만, MVP에서는 persistence를 만들지 않는다.
- 메시지 모델은 `id`, `conversationId`, `terminalId`, `agentId`, `role`, `body`, `timestamp`, `status`를 포함한다.
- Agent 진행 상태와 종료 상태는 message와 별도 event로 표시할 수 있어야 한다.
- Terminal 종료 시 conversation input을 비활성화하고 새 Terminal/Agent 재시작 경로를 제공한다 (`USER_JOURNEY.md` lines 49-52).

## 6. Typed Contract 후보

기존 IPC 결과 형태는 `{ ok: true, value } | { ok: false, code, message }`이며 renderer-facing project API에 이미 적용되어 있다 (`workstudio/src/workstudio/ipc.ts` lines 11-25). MVP는 같은 형태를 terminal/agent/conversation으로 확장한다.

```ts
type WorkStudioErrorCode =
  | ExistingProjectErrorCode
  | "create_failed"
  | "pm_not_found"
  | "terminal_not_found"
  | "terminal_closed"
  | "pty_spawn_failed"
  | "outside_registered_root"
  | "agent_not_registered"
  | "agent_launch_failed"
  | "agent_not_running";

interface TerminalSession {
  terminalId: string;
  projectId: string;
  cwd: string;
  shell: string;
  status: "starting" | "running" | "closing" | "exited" | "failed";
  exitCode?: number;
  signal?: string;
}

interface TerminalApi {
  create(input: { projectId: string; cols: number; rows: number; shell?: string }): Promise<IpcResult<TerminalSession>>;
  write(input: { terminalId: string; data: string }): Promise<IpcResult<{ sequence: number }>>;
  resize(input: { terminalId: string; cols: number; rows: number }): Promise<IpcResult<TerminalSession>>;
  interrupt(input: { terminalId: string }): Promise<IpcResult<TerminalSession>>;
  close(input: { terminalId: string }): Promise<IpcResult<TerminalSession>>;
  onData(handler: (event: TerminalDataEvent) => void): () => void;
  onStatus(handler: (event: TerminalStatusEvent) => void): () => void;
  onExit(handler: (event: TerminalExitEvent) => void): () => void;
}

interface AgentApi {
  listRegistered(projectId: string): Promise<IpcResult<AgentCandidate[]>>;
  launchCodex(input: { projectId: string; terminalId?: string }): Promise<IpcResult<AgentSession>>;
  send(input: { sessionId: string; message: string }): Promise<IpcResult<{ messageId: string }>>;
  stop(input: { sessionId: string }): Promise<IpcResult<AgentSession>>;
  onEvent(handler: (event: AgentSessionEvent) => void): () => void;
}
```

preload는 `contextBridge`로 위 함수를 좁혀 노출하고, event subscription은 반드시 unsubscribe 함수를 반환해야 한다. main은 channel 이름을 `workstudio:terminal:*`, `workstudio:agent:*`처럼 namespace로 분리한다.

## 7. 상태 모델과 생명주기

### Project lifecycle

```text
idle
  → selecting | creating
  → validating
  → registered
  → active
  → missing | invalid | create_failed
```

### Terminal lifecycle

```text
creating
  → running
  → closing
  → exited

creating
  → failed

running
  → failed
```

Terminal status event는 `running`, `failed`, `exited`를 renderer에 전달한다. `exit` event는 `exitCode`와 `signal`을 포함한다. 이 shape은 백로그의 Terminal 계약과 맞춘다 (`workstudio/BACKLOG.md` lines 112-122).

### Agent lifecycle

```text
registered
  → starting
  → running
  → waiting_input
  → exited

starting | running
  → failed
```

Agent session은 Terminal session에 종속된다. Terminal이 종료되면 연결된 Agent session은 `exited` 또는 `failed`로 닫히고, conversation input은 disabled가 된다.

### 앱 teardown

- `before-quit` 또는 `window-all-closed`에서 TerminalGateway의 모든 session을 close/kill한다.
- Codex adapter는 자신이 시작한 process만 종료한다.
- 강제 종료 timeout을 둔다.
- 종료 중 발생한 오류는 renderer에 새로 알리지 않고 main 로그로만 남긴다.

## 8. 오류 모델

| 코드 | 발생 영역 | 의미 | 사용자 상태 |
|---|---|---|---|
| `cancelled` | Project open | 사용자가 폴더 선택을 취소 | 인트로 유지 |
| `invalid_path` | Project open/create | 경로가 없거나 directory가 아님 | 다른 경로 선택 |
| `duplicate_path` | Project registry | 이미 등록된 Project | 기존 Project 열기 유도 |
| `create_failed` | Project create | 폴더 또는 `.opal/AGENT.md` 생성 실패 | 위치/이름 변경 재시도 |
| `pm_not_found` | Agent discovery | `.opal/AGENT.md` 없음 | Agent 실행 비활성 |
| `outside_registered_root` | Terminal/File | 등록 root 밖 cwd/path 요청 | 요청 거부 |
| `pty_spawn_failed` | Terminal | shell/PTy 생성 실패 | Terminal 재시도 |
| `terminal_closed` | Terminal/Agent | 닫힌 Terminal에 write/launch 요청 | 새 Terminal 생성 |
| `agent_launch_failed` | Agent | Codex 실행 실패 | 재시도 또는 환경 안내 |
| `agent_not_running` | Conversation | 실행 중 Agent 없음 | launch 유도 |

오류 흐름은 USER_JOURNEY의 취소·실패·종료 상태와 대응되어야 한다 (`USER_JOURNEY.md` lines 41-52).

## 9. 보안 경계

- 기존 BrowserWindow 보안 설정인 `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`를 유지한다 (`workstudio/electron/main.cjs` lines 251-263).
- renderer는 filesystem, PTY, process, shell path에 직접 접근하지 않는다.
- renderer는 command string이나 executable path를 Agent launch API에 전달하지 않는다.
- Terminal cwd는 등록 Project root로 검증한다.
- file listing의 realpath root 검증 패턴을 Terminal cwd 검증에도 재사용한다 (`workstudio/electron/main.cjs` lines 168-188).
- preload는 project/terminal/agent/conversation의 typed API만 노출한다. 현재 테스트도 preload가 Node fs를 노출하지 않음을 검증한다 (`workstudio/src/workstudio/ipc.test.ts` lines 20-40).
- scrollback과 conversation은 민감한 출력이 될 수 있으므로 MVP에서는 persistence하지 않는다.

## 10. Testability 전략

### L1 단위/계약 테스트

- `TerminalGateway` cwd 검증, session map, write/resize/close, exit event 순서 테스트
- `CodexAdapter` command 구성과 status 변환 테스트. 실제 Codex 실행 대신 adapter transport fake로 RED/GREEN
- `ProjectGateway.createProject`가 폴더와 `.opal/AGENT.md`만 만들고 `.git`을 만들지 않는 테스트
- typed IPC source test에 `terminal`, `agent`, `conversation` API 존재와 secure webPreferences 회귀 추가

### L2 renderer 통합 테스트

- first-run에서 신규 Project 생성 → PM 표시 → Terminal 생성 버튼 활성화
- Terminal surface가 static cwd/mock output 대신 event 기반 scrollback을 표시
- Agent launch 실패/성공 상태 표시
- Terminal exit 시 conversation input disabled
- 기존 Project Registry, Files tree, first-run 회귀 테스트 유지 (`workstudio/src/workstudio/FirstRunWelcome.test.tsx` lines 23-164; `workstudio/src/workstudio/WorkStudioApp.test.tsx` lines 349-460).

### L3 Electron 실행 스켈레톤

- Electron 앱 실행
- renderer가 preload API로 Project/Terminal create 호출
- main이 filesystem 또는 PTY를 실제 수행
- renderer가 status/data/exit event를 수신해 화면 상태를 바꿈
- 이 profile은 HTTP server 또는 Swagger를 요구하지 않는다.

## 11. OPPL Electron 실행 프로필

OPPL D5는 현재 실행 스켈레톤의 의존 루트 태스크로 BE 서버 기동, Swagger/OpenAPI UI, FE dev server, FE→BE 실 호출, 필요 시 로그인 관통을 의무화한다 (`opal/skills/opal-pilot-project-loop/SKILL.md` lines 200-209). evaluator도 워킹 스켈레톤 루브릭에서 같은 4항을 요구한다 (`opal/agents/opal-evaluator-agent/AGENT.md` lines 54-60).

WorkStudio는 Electron 데스크톱 앱이므로 다음 변경이 필요하다.

- `surfaces.json` 또는 CONTRACT 단계에서 project profile을 `electron-desktop`으로 선언한다.
- D5 skeleton 판정은 `web-http`와 `electron-desktop` profile 중 하나를 선택한다.
- `electron-desktop` skeleton은 Electron 실행, renderer→preload→main IPC, main의 filesystem/PTy 수행, renderer event 반영을 4항으로 판정한다.
- 기존 웹 profile은 변경하지 않고 default로 유지한다.
- evaluator의 워킹 스켈레톤 루브릭은 profile별 구성 항목을 참조하도록 수정한다.
- `real-http` 충실도와 별도로 `real-desktop-ipc` 또는 `real-usage` 충실도를 허용한다.

회귀 방지는 “웹 프로젝트는 기존 BE+Swagger+FE→BE 경로를 그대로 요구하고, Electron profile 선언이 있는 프로젝트만 desktop skeleton으로 분기”하는 방식으로 한다.

## 12. PRD 수용 기준 추적성

| PRD AC | TRD 반영 |
|---|---|
| PRD-AC-01 | First-run state와 Project open/create API. 기존 welcome 테스트 유지, createProject 추가. |
| PRD-AC-02 | Project Registry register/open flow 유지, realpath 검증과 duplicate 처리. |
| PRD-AC-03 | createProject가 폴더와 `.opal/AGENT.md`만 생성하고 `.git` 미생성 테스트. |
| PRD-AC-04 | `.opal/AGENT.md` marker 기반 PM discovery와 AgentCandidate 등록. |
| PRD-AC-05 | TerminalGateway create/write/resize/interrupt/close와 data/status/exit event. |
| PRD-AC-06 | CodexAdapter launchCodex, lifecycle event, launch failure model. |
| PRD-AC-07 | Conversation store/UI와 Agent event/message 분리. |
| PRD-AC-08 | 오류 코드 표와 사용자 복구 상태. |
| PRD-AC-09 | app teardown에서 WorkStudio 소유 PTY/Agent 종료, persistence 없음. |
| PRD-AC-10 | Electron E2E skeleton + final journey smoke. |
| PRD-AC-11 | F101 Project Registry, welcome, Files tree, workspace 기존 테스트 유지. |
| PRD-AC-12 | OPPL `electron-desktop` profile 분기와 웹 profile 회귀 방지. |

## 13. 구현 순서 제안

1. OPPL Electron profile 선행 보강: D5/evaluator skeleton profile 분기.
2. Project create API: 신규 폴더 + `.opal/AGENT.md` 초기화 + registry 등록.
3. PM discovery state 정리: marker 기반 candidate와 launcher eligibility.
4. TerminalGateway typed IPC: `node-pty` 도입, cwd 검증, event subscription.
5. Terminal UI 연결: mock output 제거, status/exit 표시.
6. Codex adapter: Terminal transport 위 launch/send/stop/event 변환.
7. Conversation UI/store: message/status/error 표시와 Terminal 종료 연동.
8. Journey smoke와 F101 회귀 묶음 검증.

## 14. 리스크와 완화

| 리스크 | 영향 | 완화 |
|---|---|---|
| `node-pty` Electron native build 실패 | TerminalGateway 구현 차단 | macOS 우선 install/build 검증, Electron 38 호환 확인, rebuild 절차 문서화. |
| renderer가 command/cwd를 과도하게 제어 | 보안 경계 약화 | renderer는 projectId, terminalId, message만 전달하고 main/adapter가 command와 cwd 결정. |
| Codex CLI output 파싱 불안정 | 대화 event 품질 저하 | MVP는 최소 lifecycle/message 추출로 시작하고 raw PTY scrollback을 별도 표시. |
| mock state와 actual state 혼재 | `simulated` 경계 잔존 | actual Terminal/Agent surface는 boundary를 `actual`로 전환하고 mock adapter seed는 demo 전용으로 격리. |
| OPPL profile 변경의 웹 회귀 | 기존 oppl 프로젝트 실패 | profile 명시 분기와 기존 default 유지, evaluator 루브릭도 profile-aware로 변경. |

## 15. Decision Required

없음. MVP 범위의 제품 결정은 PRD와 TASK에서 확정되어 있다. 구현 중 Codex CLI 실행 인자, prompt 전송 방식, `node-pty` rebuild 절차는 개발 태스크 내 기술 선택으로 닫을 수 있으며, 외부 계약 변경이나 MVP 범위 확장이 필요할 때만 별도 결정을 요청한다.

## 16. 근거 요약

- WorkStudio 목표와 MVP 여정: `workstudio/BACKLOG.md` lines 5-32.
- WorkStudio Terminal 계약: `workstudio/BACKLOG.md` lines 97-131.
- 기술 기반 작업: `workstudio/BACKLOG.md` lines 133-142.
- 보안 IPC 설정: `workstudio/electron/main.cjs` lines 251-263, `workstudio/electron/preload.cjs` lines 11-24.
- 현재 renderer IPC 타입: `workstudio/src/workstudio/ipc.ts` lines 11-84.
- 현재 mock Terminal/Agent 상태: `workstudio/src/workstudio/mock-adapter.ts` lines 64-74, 114-199; `workstudio/src/workstudio/WorkStudioApp.tsx` lines 927-1011, 1590-1611.
- 현재 Project Registry 구현과 테스트: `workstudio/electron/project-registry.cjs` lines 42-220; `workstudio/electron/main.test.mjs` lines 53-160.
- OPPL 웹 skeleton 강제 지점: `opal/skills/opal-pilot-project-loop/SKILL.md` lines 200-209, `opal/agents/opal-evaluator-agent/AGENT.md` lines 54-60.
