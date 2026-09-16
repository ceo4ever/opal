# CONTRACT: WorkStudio MVP Agent Conversation

> OPPL Loop 1 D4 산출물. Electron desktop 프로젝트이므로 OpenAPI를 만들지 않고 비-API 표면 직접 작성 경로를 사용한다. 기계가독 표면 인벤토리의 SSOT는 `surfaces.json`이다.

## 1. 계약 범위

본 계약은 WorkStudio MVP의 사용자 접촉 경계와 실행 경계를 확정한다.

- 인트로에서 기존 Project 열기 또는 신규 Project 생성
- `.opal/AGENT.md` 기반 PM Agent 발견·등록
- Project cwd 실제 PTY Terminal 생성·제어·event 구독
- Codex Agent 후보 조회·발동·메시지 전송·중지·event 구독
- Terminal scrollback과 Agent conversation 분리
- Electron 앱 종료 시 WorkStudio 소유 PTY/Agent teardown
- OPPL `electron-desktop` 실행 프로필

범위 밖: 다중 PM Coordination 자동화, Worker DAG, 내장 파일 편집기, Git 작업, 원격 Terminal, 세션 복원, 배포 패키징. 신규 Project 생성은 폴더와 최소 `.opal/AGENT.md`만 만들고 Git init을 수행하지 않는다.

근거: MVP 범위와 제외 범위는 PRD §3에 정의되어 있고, Terminal/Agent/process는 Electron main 소유라는 제약은 TASK lines 18-30 및 TRD §3~§5에 정리되어 있다.

## 2. 스키마 (Schema)

### 2.1 공통 결과

모든 preload IPC 호출은 다음 공통 결과 형태를 사용한다. 기존 Project IPC도 같은 형태를 사용한다(`workstudio/src/workstudio/ipc.ts` lines 11-25).

```ts
type IpcResult<T> =
  | { ok: true; value: T }
  | { ok: false; code: WorkStudioErrorCode; message: string };
```

`message`는 사용자에게 직접 노출 가능한 짧은 오류 설명이어야 한다. 오류 원문 stack, shell command, filesystem 내부 exception 객체는 renderer로 전달하지 않는다.

### 2.2 오류 코드

| 코드 | 의미 | 복구 |
|---|---|---|
| `cancelled` | 사용자가 폴더 선택을 취소했다. | 인트로 또는 현재 workspace를 유지한다. |
| `invalid_path` | 경로가 비어 있거나 directory가 아니거나 읽을 수 없다. | 다른 경로 선택 또는 생성 재시도. |
| `duplicate_path` | 이미 등록된 Project root다. | 기존 Project를 연다. |
| `missing_path` | 최근 Project path가 사라졌다. | 경로 복구 또는 목록 제거. |
| `not_found` | id에 대응하는 Project/Terminal/Agent session이 없다. | 목록 새로고침 또는 재생성. |
| `storage_error` | Project Registry 저장 실패. | 재시도 또는 권한 확인. |
| `outside_registered_root` | cwd/path가 등록 Project root 밖이다. | 요청 거부. |
| `read_failed` | 파일 또는 directory 읽기 실패. | 권한·경로 확인. |
| `too_large` | 안전하게 렌더하기에 directory 항목이 너무 많다. | 하위 경로 선택. |
| `create_failed` | 신규 Project 폴더 또는 `.opal/AGENT.md` 생성 실패. | 위치·이름 변경 후 재시도. |
| `pm_not_found` | `.opal/AGENT.md`가 없어 PM 실행 후보가 없다. | 다른 Project 선택 또는 Project 초기화. |
| `terminal_not_found` | terminal id가 존재하지 않는다. | 새 Terminal 생성. |
| `terminal_closed` | 닫힌 Terminal에 write/launch 요청이 들어왔다. | 새 Terminal 생성. |
| `pty_spawn_failed` | shell 또는 PTY 생성 실패. | shell/권한 확인 후 재시도. |
| `agent_not_registered` | Project에 실행 가능한 Codex 후보가 없다. | PM 발견·등록부터 다시 수행. |
| `agent_launch_failed` | Codex 실행 시작 실패. | Codex CLI 환경 확인 후 재시도. |
| `agent_not_running` | 실행 중 Agent session이 없다. | Agent 발동. |
| `not_supported` | 현재 profile 또는 플랫폼에서 지원하지 않는 동작이다. | profile/플랫폼 요구 확인. |

### 2.3 Project

```ts
interface ProjectDirectorySelection {
  id?: string;
  path: string;
  realPath: string;
  name: string;
  isOpalProject: boolean;
  agentPath?: string;
  pmName?: string;
}

interface RecentProject extends ProjectDirectorySelection {
  id: string;
  createdAt: string;
  lastAccessedAt: string;
  status: "available" | "missing";
}

interface CreateProjectInput {
  parentPath: string;
  name: string;
}
```

`CreateProjectInput.name`은 path separator와 빈 문자열을 허용하지 않는다. 생성 결과는 `RecentProject`이며, 성공 시 `isOpalProject === true`, `agentPath`는 `<realPath>/.opal/AGENT.md`여야 한다.

### 2.4 Agent Candidate

```ts
interface AgentCandidate {
  id: string;
  projectId: string;
  name: string;
  role: "Project PM" | "Codex";
  source: "project" | "framework";
  path: string;
  status: "ready" | "idle" | "offline";
  launcherEligible: boolean;
}
```

MVP에서 `.opal/AGENT.md`로 발견된 Project PM은 context/registration candidate이며 `launcherEligible:false`다. 실행 가능한 candidate는 Codex 하나뿐이며 `launcherEligible:true`다. Project PM은 Project 맥락과 후보 표시를 제공하지만 renderer가 PM이나 임의 실행 파일을 직접 실행 대상으로 지정하지 않는다.

### 2.5 Terminal

```ts
interface TerminalSession {
  terminalId: string;
  projectId: string;
  cwd: string;
  shell: string;
  cols: number;
  rows: number;
  status: "starting" | "running" | "closing" | "exited" | "failed";
  exitCode?: number;
  signal?: string;
  createdAt: string;
  updatedAt: string;
}

interface TerminalDataEvent {
  terminalId: string;
  chunk: string;
  sequence: number;
}

interface TerminalStatusEvent {
  terminalId: string;
  status: TerminalSession["status"];
  reason?: string;
}

interface TerminalExitEvent {
  terminalId: string;
  exitCode?: number;
  signal?: string;
}
```

`cwd`는 등록된 Project root와 같거나 그 하위여야 한다. `sequence`는 TerminalGateway가 단조 증가시키며 renderer는 출력 순서 보존에만 사용한다.

### 2.6 Codex Agent Session

```ts
interface AgentSession {
  sessionId: string;
  projectId: string;
  agentId: "codex";
  terminalId: string;
  status: "starting" | "running" | "waiting_input" | "failed" | "exited";
  startedAt: string;
  updatedAt: string;
  exitCode?: number;
  failureSummary?: string;
}

interface AgentMessage {
  id: string;
  sessionId: string;
  terminalId: string;
  agentId: "codex";
  role: "user" | "agent" | "system";
  body: string;
  timestamp: string;
  status: "queued" | "sent" | "streaming" | "done" | "failed";
}

type AgentSessionEvent =
  | { type: "starting"; session: AgentSession }
  | { type: "running"; session: AgentSession }
  | { type: "waiting_input"; session: AgentSession }
  | { type: "message"; sessionId: string; message: AgentMessage }
  | { type: "failed"; session: AgentSession; code: WorkStudioErrorCode; message: string }
  | { type: "exited"; session: AgentSession; exitCode?: number; signal?: string };
```

Agent message 기록은 Terminal scrollback과 별도 store다. PTY byte stream은 transport와 scrollback의 원천일 수 있지만 conversation store의 schema를 대체하지 않는다.

### 2.7 Execution Profile

```ts
interface ExecutionProfile {
  id: "electron-desktop";
  requiredFidelity: "real-desktop-ipc";
  skeletonOracle: [
    "Electron app starts",
    "renderer calls preload IPC",
    "Electron main performs filesystem or PTY work",
    "renderer observes returned value or event and updates UI"
  ];
}
```

현재 OPPL reference의 fidelity ladder는 `mock < real-http < real-usage`를 정의한다. WorkStudio는 비-API Electron desktop이므로 본 계약은 `real-desktop-ipc`를 desktop profile의 required fidelity로 선언한다. OPPL 도구가 아직 이를 알지 못하면 D5/D6 선행 변경 표면(`oppl-electron-profile`)을 먼저 완료해야 한다.

## 3. 시그니처 (Signature)

### 3.1 Project API

```ts
project.chooseDirectory(): Promise<IpcResult<ProjectDirectorySelection>>
project.inspectDirectory(path: string): Promise<IpcResult<ProjectDirectorySelection>>
project.registerFromSelection(selection: ProjectDirectorySelection): Promise<IpcResult<RecentProject>>
project.listRecent(): Promise<IpcResult<{ projects: RecentProject[]; recovery?: RegistryRecovery }>>
project.openRecent(id: string): Promise<IpcResult<RecentProject>>
project.repairRecent(id: string, path: string): Promise<IpcResult<RecentProject>>
project.removeRecent(id: string): Promise<IpcResult<{ id: string }>>
project.listFiles(scope: { rootPath: string; path?: string; relativePath?: string }): Promise<IpcResult<ProjectFileNode[]>>
project.createProject(input: CreateProjectInput): Promise<IpcResult<RecentProject>>
```

`createProject`는 신규 계약이다. 기존 Project API는 현재 preload/main/ipc 타입에 존재한다(`workstudio/electron/preload.cjs` lines 13-22; `workstudio/electron/main.cjs` lines 240-249; `workstudio/src/workstudio/ipc.ts` lines 69-80).

### 3.2 Agent Registry API

```ts
agent.listRegistered(projectId: string): Promise<IpcResult<AgentCandidate[]>>
agent.registerProjectPm(projectId: string): Promise<IpcResult<AgentCandidate>>
```

`registerProjectPm`은 Project root의 `.opal/AGENT.md` marker를 기준으로 PM context/registration candidate를 생성한다. 성공 결과는 `role:"Project PM"`과 `launcherEligible:false`를 가져야 한다. PM 미발견은 `pm_not_found`를 반환한다.

### 3.3 Terminal API

```ts
terminal.create(input: { projectId: string; cols: number; rows: number; shell?: string }): Promise<IpcResult<TerminalSession>>
terminal.write(input: { terminalId: string; data: string }): Promise<IpcResult<{ sequence: number }>>
terminal.resize(input: { terminalId: string; cols: number; rows: number }): Promise<IpcResult<TerminalSession>>
terminal.interrupt(input: { terminalId: string }): Promise<IpcResult<TerminalSession>>
terminal.close(input: { terminalId: string }): Promise<IpcResult<TerminalSession>>
terminal.onData(handler: (event: TerminalDataEvent) => void): () => void
terminal.onStatus(handler: (event: TerminalStatusEvent) => void): () => void
terminal.onExit(handler: (event: TerminalExitEvent) => void): () => void
```

모든 event subscription은 unsubscribe 함수를 반환한다. renderer unmount 또는 Terminal tab close 시 unsubscribe가 호출되어야 한다.

### 3.4 Codex Agent API

```ts
agent.launchCodex(input: { projectId: string; terminalId?: string }): Promise<IpcResult<AgentSession>>
agent.send(input: { sessionId: string; message: string }): Promise<IpcResult<{ messageId: string }>>
agent.stop(input: { sessionId: string }): Promise<IpcResult<AgentSession>>
agent.onEvent(handler: (event: AgentSessionEvent) => void): () => void
```

`agent.listRegistered`와 `agent.launchCodex`는 등록된 Project PM context를 사용해 Codex 후보를 산출·발동한다. 반환 candidate 중 실행 가능한 항목은 `role:"Codex"`와 `launcherEligible:true`를 가져야 하며, Project PM candidate는 실행 후보로 반환하지 않는다. renderer는 command, executable path, arbitrary cwd, raw shell args를 전달하지 않는다. Codex 실행 명령은 main의 Codex adapter가 Project/Terminal context와 고정 adapter 설정으로 구성한다.

## 4. 경계 (Boundary)

| 경계 | 소유자 | 계약 |
|---|---|---|
| Renderer UI | React renderer | 사용자 입력, 화면 상태, event 표시. Node/fs/process/pty 직접 접근 금지. |
| Preload bridge | Electron preload | `window.opalWorkStudio`에 좁은 typed API만 노출. Node API 노출 금지. |
| ProjectGateway/Registry | Electron main | folder picker, createProject, realpath 검증, registry 저장, `.opal/AGENT.md` marker 확인. |
| TerminalGateway | Electron main | PTY process 생성·제어·event emit·teardown. cwd 등록 root 검증. |
| CodexAgentAdapter | Electron main | Codex 후보/launch/send/stop, PTY transport 연결, lifecycle/message event 변환. |
| ConversationStore | renderer 또는 main volatile store | Agent message/event를 Terminal scrollback과 분리해 관리. MVP persistence 없음. |
| OPPL profile | OPPL framework | `electron-desktop` skeleton과 `real-desktop-ipc` fidelity를 profile-aware로 판정. 기존 web profile 회귀 금지. |

보안 불변조건:

- `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true` 유지.
- renderer 임의 command/path/executable 전달 금지.
- Terminal `cwd`는 등록 Project root 또는 하위 경로로 검증.
- file listing과 Terminal cwd 모두 realpath 기반 root containment를 사용.
- Agent 실행 명령은 등록 adapter가 구성.
- Terminal scrollback과 Agent conversation을 분리.
- WorkStudio가 소유한 PTY/Agent만 teardown.
- 세션 복원은 MVP 범위 밖.

## 5. 상태 전이

### 5.1 Project

```text
idle -> selecting|creating -> validating -> registered -> active
selecting -> cancelled -> idle
validating -> invalid_path|duplicate_path
creating -> create_failed|registered
active -> missing_path
```

### 5.2 Terminal

```text
starting -> running -> closing -> exited
starting -> failed
running -> failed
running -> exited
```

`terminal.write`, `terminal.resize`, `terminal.interrupt`는 `running` 상태에서만 성공한다. `terminal.close`는 `running|failed`에서 idempotent하게 종료 상태로 수렴해야 한다.

### 5.3 Codex Agent

```text
registered -> starting -> running -> waiting_input -> running -> exited
starting -> failed
running -> failed
running -> exited
```

Terminal exit은 연결 Agent session의 `exited` 또는 `failed` event를 유발한다. Agent session이 닫히면 conversation input은 비활성화된다.

### 5.4 App Teardown

```text
running sessions -> app before-quit/window-all-closed -> closing -> exited|killed
```

종료 중 새 Terminal/Agent launch 요청은 `terminal_closed` 또는 `agent_not_running`으로 거부한다.

## 6. 기계검증절 (Machine-Verifiable Section)

### 6.1 표면 인벤토리

`surfaces.json`은 본 계약의 기계가독 표면 SSOT다. 모든 표면은 `id`, `resource`, `auth`, `request_shape`, `response_shape`, `kind`를 가진다. WorkStudio는 인증 기능이 없는 로컬 desktop 앱이므로 모든 MVP 표면의 `auth`는 `none`이다.

필수 표면:

- `intro-first-run`
- `project-open-existing`
- `project-create-new`
- `pm-discover-register`
- `workspace-files-tree`
- `terminal-create`
- `terminal-io-control`
- `terminal-events`
- `agent-list-launch`
- `agent-send-stop`
- `agent-conversation-events`
- `app-teardown`
- `journey-smoke`
- `oppl-electron-profile`

### 6.2 Conformance Oracle

| 표면 | 결정론 검증 oracle |
|---|---|
| `intro-first-run` | 저장 상태가 없을 때 intro dialog와 open/create/demo action이 렌더된다. |
| `project-open-existing` | 기존 OPAL fixture 선택 시 registry 저장, active workspace 전환, PM 후보 표시가 발생한다. cancel/invalid/duplicate는 서로 다른 오류 상태다. |
| `project-create-new` | temp parent에 Project folder와 `.opal/AGENT.md`가 생성되고 `.git`은 생성되지 않는다. 결과는 registry에 저장된다. |
| `pm-discover-register` | `.opal/AGENT.md`가 있으면 Project PM context/registration candidate가 `launcherEligible:false`로 표시된다. PM 미발견 시 `pm_not_found` 또는 실행 후보 없음 상태가 된다. |
| `workspace-files-tree` | active Project 기준 `project.listFiles`가 등록 root 내부 실제 파일 구조를 반환하고, 우측 Files tree가 이를 표시한다. workspace 전환 시 root와 tree 내용이 새 active Project 기준으로 갱신된다. |
| `terminal-create` | 등록 Project root cwd로 실제 PTY session이 생성되고 `TerminalSession.status`가 `running`에 도달한다. root 밖 cwd는 `outside_registered_root`다. |
| `terminal-io-control` | write는 PTY에 전달되고 resize/interrupt/close는 session 상태 또는 event로 관찰된다. 닫힌 session write는 `terminal_closed`다. |
| `terminal-events` | `onData/onStatus/onExit`는 event를 전달하고 unsubscribe 후 추가 event를 받지 않는다. |
| `agent-list-launch` | 등록 PM context에서 Codex 후보만 `launcherEligible:true`로 산출된다. launch는 renderer command 없이 main adapter가 수행한다. 실패는 `agent_launch_failed`다. |
| `agent-send-stop` | send는 running session에만 성공하고 message id를 반환한다. stop은 session을 종료 상태로 수렴시킨다. |
| `agent-conversation-events` | agent message/progress/exit event가 conversation store에 반영되고 Terminal scrollback과 분리된다. |
| `app-teardown` | app quit 시 WorkStudio 소유 Terminal/Agent sessions가 종료되고 세션 복원을 시도하지 않는다. |
| `journey-smoke` | fresh state에서 신규 Project 생성→PM 등록→Terminal→Codex→message→response/event→teardown까지 통과하고 mock boundary count가 0이다. |
| `oppl-electron-profile` | OPPL D5/D6가 `electron-desktop` profile에서 BE 서버/Swagger를 요구하지 않고 renderer→preload→main evidence로 skeleton을 판정한다. 웹 profile은 기존 조건을 유지한다. |

### 6.3 Fidelity

현행 verification reference는 `mock < real-http < real-usage`를 정의한다. 본 desktop 계약은 `real-desktop-ipc`를 요구한다. OPPL 도구가 해당 fidelity를 아직 모르면 `oppl-electron-profile` 표면을 선행 완료해야 하며, 임시로 `real-usage` 이상의 Electron E2E evidence를 attached evidence로 기록할 수 있다. `mock` fidelity는 MVP done 판정에 사용할 수 없다.

### 6.4 Required Test Evidence

- `npm run typecheck`
- `npm run test`
- Electron main/preload source contract test
- Project create/open registry test
- TerminalGateway unit/integration test using real PTY on supported local platform
- CodexAdapter lifecycle test with fake transport and at least one real launch smoke when local Codex CLI is available
- Electron desktop journey smoke
- `test-tool scenario-conformance --task-path <task> --surfaces surfaces.json`
- `backlog-tool coverage-check <task> --surfaces surfaces.json`

## 7. 루브릭절 (Rubric Section)

Evaluator는 D6/G 게이트에서 아래 기준을 우선 판정한다. Likert 항목 통과선은 4 이상이다.

| 항목 | 기준 |
|---|---|
| 계약 완전성 | PRD-AC-01~12와 USER_JOURNEY의 인트로/프로젝트/PM/터미널/에이전트/대화/오류·종료 표면이 모두 `surfaces.json`과 CONTRACT에 존재한다. |
| 계약 일관성 | `CONTRACT.md`, `surfaces.json`, PRD, TRD의 surface id, 상태, 오류 코드, ownership가 서로 충돌하지 않는다. |
| 설계 정합 | Electron main/preload/renderer 경계가 기존 WorkStudio 구조와 보안 설정을 유지하면서 실제 PTY/Agent를 main에 배치한다. |
| 표면 완전성 | `surfaces.json`이 사용자 접촉 표면과 OPPL 선행 profile 표면을 빠짐없이 등재한다. |
| auth 필드 완전성 | 모든 표면이 `auth`를 선언하고, MVP에 인증 표면이 없음을 `auth:none`으로 일관되게 표현한다. |
| origin 선언 | 비-웹 Electron desktop이므로 N/A. `origins`는 `null`이어야 한다. |
| 워킹 스켈레톤 태스크 | `electron-desktop` profile에서 Electron app start, renderer→preload IPC, main filesystem/PTY 수행, renderer event 반영 4항을 충족하는 실행 스켈레톤 태스크가 존재한다. |
| 보안 불변조건 | contextIsolation 유지, nodeIntegration 금지, renderer 임의 command/path 금지, cwd root 검증, unsubscribe 반환이 테스트 가능하게 명시되어 있다. |
| drift 필요성 | 구현 중 renderer command 전달, conversation/scrollback 혼합, Project Registry 중복 저장소, mock boundary 잔존이 발견되면 drift=yes로 PM에 반환한다. |

## 8. 변경 거버넌스

- 내부 구현만 바꾸고 signature/schema/boundary가 유지되면 계약 변경 없이 진행한다.
- error code, event shape, state enum, surface id 변경은 인터페이스 변경이므로 영향 슬라이스 재검증이 필요하다.
- PRD-AC, MVP 범위, Electron profile 의미, Codex 단일 Agent 결정, 신규 Project Git init 제외 결정의 변경은 사용자 승인 대상이다.
- 루프 액션 에이전트는 CONTRACT.md를 직접 수정하지 않는다. drift를 감지하면 `status: blocked`로 PM에 반환한다.

## 9. PRD-AC 추적성

| PRD AC | Surface |
|---|---|
| PRD-AC-01 | `intro-first-run` |
| PRD-AC-02 | `project-open-existing` |
| PRD-AC-03 | `project-create-new` |
| PRD-AC-04 | `pm-discover-register` |
| PRD-AC-05 | `terminal-create`, `terminal-io-control`, `terminal-events` |
| PRD-AC-06 | `agent-list-launch` |
| PRD-AC-07 | `agent-send-stop`, `agent-conversation-events` |
| PRD-AC-08 | `project-open-existing`, `project-create-new`, `pm-discover-register`, `terminal-create`, `terminal-io-control`, `agent-list-launch`, `agent-send-stop`, `agent-conversation-events` |
| PRD-AC-09 | `app-teardown` |
| PRD-AC-10 | `journey-smoke` |
| PRD-AC-11 | `project-open-existing`, `workspace-files-tree`, `journey-smoke` |
| PRD-AC-12 | `oppl-electron-profile`, `journey-smoke` |

## 10. Decision Required

없음. 다만 OPPL core가 `electron-desktop` profile과 `real-desktop-ipc` fidelity를 아직 모르는 상태라면 이는 구현 선행 표면(`oppl-electron-profile`)으로 처리한다. 별도 사용자 결정이 아니라 도구 계약 보강 작업이다.
