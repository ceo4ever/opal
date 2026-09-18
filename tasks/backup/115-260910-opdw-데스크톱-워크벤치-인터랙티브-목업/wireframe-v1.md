# OPAL Product OS Desktop Workbench — 와이어프레임

> 작성일: 2026-09-11 | 작성자: AI | 버전: v1.0

## 1. 서비스 개요
- **서비스명**: OPAL Product OS Desktop Workbench
- **서비스 유형**: Electron 기반 로컬 데스크톱 개발 도구 목업(Local desktop development tool mockup)
- **대상 사용자**: 여러 LLM CLI Agent에게 업무를 맡기고 결과를 검토하는 1인 개발자
- **핵심 기능**:
  1. Project·Workstream·Task 탐색과 Task Kanban 관리
  2. `@OPAL PM` 요청, 전문 Agent 위임, Run 상태 시뮬레이션
  3. Conversation·Terminal·Browser·Files·Diff·Result 통합 검토
  4. Agent Definition 확인과 Runtime Binding 목업 설정
  5. Activity·Browser 조작·Playwright Verification·Result 승인 연결

### 1.1 구현 경계와 원칙
| 구분 | 이번 목업 동작 | UI 표시 | 향후 교체 경계 |
|---|---|---|---|
| 실제(Actual) | Electron 창, React 라우팅/상태, 클릭·입력·DnD, `localStorage` 복원 | 상단 `Interactive mock` 배지 | 유지 |
| 시뮬레이션(Simulated) | Agent 답변·위임, Run 전이, Terminal 출력, Browser 조작, 검증·Diff·Result | 항목별 `Simulated` 배지와 점선 테두리 | `MockWorkbenchAdapter`를 Runtime Adapter로 교체 |
| 미구현(Not connected) | ACP/LLM CLI, PTY, CDP/agent-browser, Playwright, Git/Worktree, SQLite | 관련 패널 `Runtime not connected` 안내 | 실제 Runtime 연결 |

- `Project → Workstream → Task → Conversation → Run → Verification → Result` 흐름을 유지한다.
- Terminal·Browser·Files·Diff는 Run이 참조하는 `Execution Environment` 소유로 표시한다.
- Agent Definition(`.opal/AGENT.md`)과 Runtime Binding(runtime/model/mode/permission)은 별도 데이터와 UI로 다룬다.
- Activity는 요약 event만 기본 노출하며 원본 로그 전문은 목업 범위에서 제공하지 않는다.

## 2. 전체 구조
### 2.1 레이아웃 유형
고정 3열 Desktop Shell: 좌측 Project/Stream/Task, 중앙 Workbench, 우측 Context/Activity. 최소 창 크기 `1280×760`; 중앙 열 `minmax(600px, 1fr)`, 좌측 280px, 우측 320px. 좁은 창에서는 우측을 Sheet로 접되 모바일 레이아웃은 범위 밖이다.

### 2.2 네비게이션 구조
- Project selector: `OPAL` → SCR-001
  - Workstreams: `Product`, `Development`, `Review` → Task 목록 필터
  - Tasks: Task 행 → SCR-001의 선택 Task 교체
  - `+ New Task` → SCR-002
- Workbench tabs
  - `Conversation`, `Runs`, `Terminal`, `Browser`, `Files`, `Diff`, `Verification`, `Result`
  - `Activity` 우측 rail → SCR-004
- Global `Agents` → SCR-003

### 2.3 화면 흐름도
```text
[앱 시작/복원] → SCR-001 Shell ── + New Task ──→ SCR-002 Dialog/Kanban
       ↑               │                                  │ 생성/카드 클릭
       │               ├── Agents ───────────────→ SCR-003 Catalog Sheet
       │               │                                  │ 저장/닫기
       │               ├── @OPAL PM 전송 → PM 응답 → Developer child Run
       │               │                                  │
       └── 복원 ───────┴── Tool tab/Activity 선택 ─→ SCR-004 검토 상태
                                                          │ Result 승인
                                                          └→ Task status=done
```

### 2.4 대표 클릭 시나리오
1. `Development`를 선택하고 `+ New Task`에서 제목·설명·lead Agent를 입력해 `todo` 카드를 만든다.
2. 카드를 `In Progress`로 이동하고 클릭해 Workbench에 진입한다.
3. Conversation에 `@OPAL PM 로그인 오류를 구현해줘`를 보내 PM 응답과 Developer child Run을 생성한다.
4. `Runs → Terminal → Browser → Files → Diff`를 순서대로 눌러 동일 `env_01`의 대표 목업을 본다.
5. `Verification`에서 Browser 조작 기록과 Playwright assertion/evidence를 구분해 확인한다.
6. `Result`에서 변경·검증·잔여 문제를 확인하고 `결과 승인(Approve result)`을 누른다.
7. 앱 재실행 시 마지막 Project·Workstream·Task·Tool View와 Conversation mock이 복원됨을 확인한다.

## 3. 화면 목록
| ID | 화면명 | 유형 | 경로 | 메뉴그룹 | 설명 |
|---|---|---|---|---|---|
| SCR-001 | Desktop Workbench Shell | detail | `/workbench/:taskId` | Project | 3열 shell, Task Conversation/Run/Tool View |
| SCR-002 | Task 생성 Dialog/Kanban | crud | `/workbench?view=board&dialog=new-task` | Workstream | Task 생성과 Kanban 이동 후 진입 |
| SCR-003 | Agent Catalog·Binding Sheet | settings | `/workbench?sheet=agents` | Global | Agent 역할과 runtime/model 목업 설정 |
| SCR-004 | Activity·Verification·Result 검토 | monitor | `/workbench/:taskId?tab=verification` | Task | 사건·조작·검증·결과와 승인 검토 |

## 4. 화면별 상세 설계
### 4.1 Desktop Workbench Shell (SCR-001)
- **유형**: detail/monitor
- **경로**: `/workbench/:taskId`
- **진입점**: 앱 시작 복원, Kanban 카드, Task 목록
- **초기값**: `project_opal / Development / task_login_fix / Conversation`

#### 레이아웃
```text
┌ OPAL ▾ ─ Development / Login fix ─ [Interactive mock] ─ [Agents] [⌘K] ┐
├──────────────┬──────────────────────────────────────┬──────────────────┤
│ WORKSTREAMS  │ Login fix             [in progress] │ CONTEXT          │
│ Product  2   │ env_01 · mock worktree · disconnected│ Project / Task   │
│ Development 3├──────────────────────────────────────┤ Environment      │
│ Review    1  │ Conversation Runs Terminal Browser   ├──────────────────┤
│              │ Files Diff Verification Result       │ ACTIVITY         │
│ TASKS        ├──────────────────────────────────────┤ 10:01 message    │
│ ● Login fix  │ @OPAL PM: 요청을 분석합니다 [Mock]   │ 10:02 delegated  │
│ ○ Empty task │  └ @Developer run_02 [running 60%]   │ 10:03 tool       │
│              │                                      │ [모두 보기]      │
│ [+ New Task] │ [@ mention 요청 입력........] [Send] │                  │
└──────────────┴──────────────────────────────────────┴──────────────────┘
```

#### Component hierarchy
```text
WorkbenchShell
├─ AppHeader(ProjectSelector, BreadcrumbText, MockBadge, AgentButton)
├─ WorkbenchSidebar(WorkstreamNav, TaskList, NewTaskButton)
├─ TaskWorkspace(TaskHeader, EnvironmentBadge, ToolTabs, ToolView, Composer)
└─ ContextRail(EntityRelations, ActivityPreview)
```

#### 구성 요소
| 영역 | UI 요소 | shadcn 컴포넌트 | 데이터/설명 |
|---|---|---|---|
| header | Project 선택·breadcrumb text·목업 배지 | Select, Button, Separator, Badge | 선택 project와 현재 stream/task; breadcrumb는 text/button 조합 |
| sidebar | Stream·Task 목록·생성 | Sidebar, ScrollArea, Badge, Button | stream별 count, task status |
| content | Task header·8개 Tool tab | Tabs, Badge, Progress, Separator | activeToolView, active/child Run |
| conversation | 메시지·멘션 composer | Avatar, Card, Textarea, Command, Dialog, Button | mention 후보는 anchored Dialog 안 Command로 표시 |
| context | 관계와 Activity preview | Card, ScrollArea, Tooltip | Project/Task/Run/Environment ID |

#### 기능
1. Product·Development·Review를 전환해 해당 Task와 상태를 표시한다.
2. 모든 Tool tab은 같은 Task와 Environment 문맥을 유지하며 대표 mock panel을 표시한다.
3. Run chip은 `queued/running/waiting/completed/failed` 색상과 현재 단계/진행률을 표시한다.

#### 인터랙션
| 이벤트 | 동작 | 결과 |
|---|---|---|
| Stream/Task 클릭 | selection 갱신 후 저장 | 목록 필터 또는 선택 Task Workbench 표시 |
| Tool tab 클릭 | `activeToolView` 갱신 | Terminal/Browser/Files/Diff 등 대표 mock 전환 |
| `@` 입력 | Agent mention Command 열기 | OPAL PM·Developer·Reviewer 선택 가능 |
| `@OPAL PM` 전송 | 600ms waiting 후 mock event 재생 | PM 메시지, parent Run, Developer 위임 표시 |
| `@Developer` 전송 | queued→running mock timer 시작 | 독립 Developer Run과 Activity 추가 |

#### Empty/loading/error states
| 상태 | 표시와 회복 동작 |
|---|---|
| 빈 Task | 중앙 Empty State: `아직 대화와 Run이 없습니다` + `첫 요청 보내기` |
| Agent 응답 대기 | 메시지 skeleton, `응답 대기 중(Simulated)` 및 취소 버튼 |
| Run 진행 | 단계명·Progress·animated status dot; Tool tab 사용 가능 |
| Run 실패 | destructive Alert, 실패 요약, `다시 실행`으로 새 Run 생성(기존 Run 보존) |

### 4.2 Task 생성 Dialog/Kanban state (SCR-002)
- **유형**: crud/form
- **경로**: `/workbench?view=board&dialog=new-task`
- **진입점**: Sidebar `+ New Task`; 생성 후 Kanban 유지

#### 레이아웃
```text
┌ Development / Tasks ───────────────────────────────────── [+ New Task] ┐
│ TODO (2)           IN PROGRESS (1)       REVIEW (1)       DONE (3)    │
│ ┌Login empty┐      ┌API login fix┐       ┌Check diff┐     ┌Setup┐     │
│ └───────────┘      └─────────────┘       └──────────┘     └─────┘     │
│        ┌ 새 Task ────────────────────────────────────────────┐         │
│        │ 제목* [________________]  Workstream [Development▾] │         │
│        │ 설명* [..........................................] │         │
│        │ Lead Agent [OPAL PM▾]  초기 상태 [Todo▾]           │         │
│        │                         [취소] [Task 만들기]         │         │
│        └────────────────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────────────────┘
```

#### Component hierarchy
```text
TaskBoard(TaskBoardHeader, KanbanColumns(TaskCard*))
└─ NewTaskDialog(NativeForm(Label, Input, Textarea, Select), DialogFooter)
```

#### 구성 요소
| 영역 | UI 요소 | shadcn 컴포넌트 | 데이터/설명 |
|---|---|---|---|
| content | 4열 Kanban·Task card | Card, Badge, ScrollArea | todo/in_progress/review/done |
| modal | 제목·설명·Stream·lead·상태 | Dialog, Label, Input, Textarea, Select | native form; title/description/workstreamId/leadAgentId/status |
| feedback | validation·생성 완료 | Alert | 필수값과 mock 저장 성공을 inline Alert로 표시 |

#### 기능 및 인터랙션
| 이벤트 | 동작 | 결과 |
|---|---|---|
| 빈 제목/설명으로 제출 | client validation | field error, Dialog 유지 |
| 유효 제출 | Task mock 생성, `task.created` 기록 | Todo 카드 추가·inline Alert, Dialog 닫힘 |
| 카드 drag/drop | 허용 열로 status 변경 | 카드 이동·`task.status_changed` 기록·localStorage 저장 |
| 카드 클릭 | Task 선택 | SCR-001 Conversation 진입 |

#### Empty/loading/error states
- 빈 Workstream: `Task가 없습니다`와 `첫 Task 만들기`; 생성 중에는 submit spinner/중복 클릭 방지.
- mock 저장 실패 toggle이 켜지면 Alert와 `다시 시도`; 입력값과 카드 원상태를 보존한다.

### 4.3 Agent Catalog·runtime/model 설정 Sheet (SCR-003)
- **유형**: settings
- **경로**: `/workbench?sheet=agents`
- **진입점**: App header `Agents`

#### 레이아웃
```text
┌ Workbench (dimmed) ───────────────────┬ AGENT CATALOG ────────────────┐
│                                      │ [검색...] [All▾]          [X]│
│                                      │ ● OPAL PM  project/default   │
│                                      │   Product lead · ready        │
│                                      │ ○ Developer framework · idle │
│                                      │ ○ Reviewer  framework · idle │
│                                      │ ○ UI Coach  user · offline   │
│                                      ├ Runtime Binding [Simulated] ─┤
│                                      │ Runtime [Codex ACP▾]          │
│                                      │ Model   [gpt-5.5▾] Mode [ask▾]│
│                                      │ Definition .opal/AGENT.md     │
│                                      │        [되돌리기] [설정 저장] │
└──────────────────────────────────────┴───────────────────────────────┘
```

#### Component hierarchy
```text
AgentCatalogSheet
├─ CatalogToolbar(SearchInput, SourceFilter)
├─ AgentList(AgentListItem*)
└─ BindingForm(DefinitionSummary, RuntimeSelect, ModelSelect, ModeSelect, Actions)
```

#### 구성 요소
| 영역 | UI 요소 | shadcn 컴포넌트 | 데이터/설명 |
|---|---|---|---|
| sheet | 검색·source 필터·Agent 목록 | Sheet, Input, Select, ScrollArea, Badge, Avatar | PM/Developer/Reviewer/user Agent |
| detail | 역할·source·definition path | Card, Separator, Tooltip | definition은 readonly |
| settings | runtime·model·mode·permission | Label, Select, Switch, Button | native form; binding만 mock 수정 |

#### 기능 및 인터랙션
| 이벤트 | 동작 | 결과 |
|---|---|---|
| Agent 선택 | definition과 binding 조회 | 역할/source/status와 설정 표시 |
| runtime 변경 | runtime별 model 목록 필터 | model 기본값 갱신, unsaved badge |
| 저장 | binding mock 저장 | inline Alert + Activity `agent.binding_updated`; 과거 Run snapshot 불변 |
| 닫기(미저장) | 확인 AlertDialog | `계속 편집/변경 폐기` 선택 |

#### Empty/loading/error states
- 검색 결과 없음: 필터 초기화 버튼. Catalog loading: 4개 row skeleton.
- Runtime 미연결 Agent: `offline / Runtime not connected`; binding 저장은 가능하되 실제 실행 가능으로 표시하지 않는다.
- 설정 실패 mock: 이전 binding 유지, inline error와 재시도 버튼.

### 4.4 Activity·Browser Verification·Result 검토 상태 (SCR-004)
- **유형**: monitor/detail
- **경로**: `/workbench/:taskId?tab=verification`
- **진입점**: Workbench Tool tabs 또는 Activity `모두 보기`

#### 레이아웃
```text
┌ Login fix ─ env_01 [Simulated] ─ [Activity filter▾] ────────────────┐
├──────────────┬──────────────────────────────────────────────────────┤
│ ACTIVITY     │ Browser | Verification | Result                     │
│ 10:01 message├──────────────────────────┬───────────────────────────┤
│ 10:02 delegate│ BROWSER ACTIONS [Mock]  │ PLAYWRIGHT [Not connected]│
│ 10:03 run    │ 1 navigate /login ✓     │ PASS AC-5  mention flow   │
│ 10:04 tool   │ 2 fill email ✓          │ PASS AC-8  evidence ↗     │
│ 10:05 file   │ 3 click submit ✓        │ FAIL AC-11 error state    │
│ 10:06 verify │ screenshot preview      │ cmd / exit / trace        │
│ 10:07 result ├──────────────────────────┴───────────────────────────┤
│              │ RESULT: 3 files · 2 pass · 1 fail · 1 remaining     │
│              │ [Diff 보기] [Evidence 열기] [결과 승인 disabled]    │
└──────────────┴──────────────────────────────────────────────────────┘
```

#### Component hierarchy
```text
ReviewWorkspace
├─ ActivityTimeline(ActivityFilter, EventGroup*)
└─ ReviewTabs
   ├─ BrowserPanel(ActionLog, ScreenshotPreview)
   ├─ VerificationPanel(CheckList, EvidenceLinks, FailureAlert)
   └─ ResultPanel(ChangeSummary, VerificationSummary, RemainingIssues, ApprovalBar)
```

#### 구성 요소
| 영역 | UI 요소 | shadcn 컴포넌트 | 데이터/설명 |
|---|---|---|---|
| activity | 시간순 사건·type 필터 | ScrollArea, Select, Badge, Accordion | message/delegation/run/tool/file/verification/result |
| browser | 조작 step·URL·screenshot | Card, Table, Badge | screenshot 비율은 CSS `aspect-ratio`; 탐색 성공은 검증 PASS 근거 아님 |
| verification | assertion·AC·evidence | Tabs, Accordion, Alert, Button | status/command/exitCode/artifacts |
| result | 변경·검증·산출물·잔여 문제 | Card, Separator, Switch, Button | 확인 입력은 Switch; 실패 시 승인 disabled |

#### 기능 및 인터랙션
| 이벤트 | 동작 | 결과 |
|---|---|---|
| Activity event 클릭 | 관련 Run/Tool tab을 선택 | 동일 event context 강조 |
| Browser action 클릭 | 해당 screenshot mock 선택 | URL·step·timestamp 표시, `Simulated` 유지 |
| Verification row 펼침 | assertion·AC·evidence 표시 | evidence link는 mock preview Dialog 열기 |
| 실패 검증 `재실행` | running→pass/fail 시나리오 재생 | 새 verification event 추가, 과거 결과 보존 |
| 모든 check PASS + 확인 체크 | 승인 활성화 | 클릭 시 Task `done`, `result.approved` Activity 추가 |

#### Empty/loading/error states
- Activity 없음: `아직 기록된 사건이 없습니다`; 필터 결과 없음: 필터 초기화.
- Verification running: check skeleton과 진행률; Browser 미연결: screenshot placeholder와 연결 안내.
- Verification failed: 실패 assertion, expected/actual, evidence, 재실행. Result는 승인 비활성 및 실패 사유를 표시한다.

## 5. 공통 컴포넌트
| 컴포넌트 | shadcn 기반 | UI kit 상태 | 사용 화면 | 설명 |
|---|---|---|---|---|
| `RuntimeBoundaryBadge` | Badge, Tooltip | 기존(Existing) | SCR-001, 003, 004 | Actual/Simulated/Not connected를 일관되게 표시 |
| `RunStatusBadge` | Badge, Progress | 기존 | SCR-001, 004 | 5개 대표 Run 상태와 단계/진행률 |
| `EntityContext` | Card, Button, Separator | 기존 | SCR-001, 004 | breadcrumb는 기존 요소 조합; Project→Task→Run→Environment 관계 |
| `ActivityTimeline` | ScrollArea, Accordion, Badge | 기존 | SCR-001, 002, 003, 004 | Collapsible 대신 Accordion; event를 sequence 오름차순 표시 |
| `EmptyState` | Card, Button | 기존 | 전체 | 상태 설명과 단일 회복 CTA |
| `MockFailureToggle` | Switch, Tooltip | 기존 | 전체 | 제품 검토용 실패/대기 상태 전환; 개발 환경에서만 표시 |

신규(New) 공통 컴포넌트 의존은 없다. `Breadcrumb`, `Popover`, `Field/Form`, `RadioGroup`, `Collapsible`, `AspectRatio`, `Checkbox`, `Toast`는 각각 기존 Button/Separator, Dialog/Command, Label/native form, Select/Switch, Accordion, CSS, Switch, Alert로 대체한다.

## 6. shadcn 설치 목록
| 구분 | 컴포넌트 | 사용 화면 | 조치 |
|---|---|---|---|
| 기존(Existing) | sidebar, tabs, scroll-area, separator | SCR-001, SCR-004 | 현재 UI kit 재사용 |
| 기존 | button, badge, card, tooltip, alert, skeleton | 전체 | 현재 UI kit 재사용 |
| 기존 | dialog, label, input, textarea, select | SCR-001, SCR-002, SCR-003 | 현재 UI kit 재사용 |
| 기존 | sheet, alert-dialog, avatar, command | SCR-001, SCR-003 | 현재 UI kit 재사용 |
| 기존 | progress, accordion, table, switch | SCR-001, SCR-004 | 현재 UI kit 재사용 |
| 신규(New) | 없음 | - | 추가 설치 없음 |

신규 설치 명령: 없음. `dashboard/frontend/src/components/ui/`에 이미 존재하는 컴포넌트만 사용한다.

## 7. Mock data contract와 상태 규칙
```ts
type RunStatus = 'queued'|'running'|'waiting'|'completed'|'failed';
type Boundary = 'actual'|'simulated'|'not_connected';
type ToolView = 'conversation'|'runs'|'terminal'|'browser'|'files'|'diff'|'verification'|'result';
type TaskStatus = 'todo'|'in_progress'|'review'|'done';
interface Project { id:string; name:string; repositoryPath:string; workstreamIds:string[] }
interface Workstream { id:string; projectId:string; name:'Product'|'Development'|'Review'; taskIds:string[] }
interface Task { id:string; workstreamId:string; title:string; description:string; status:TaskStatus; leadAgentId:string; environmentId:string; runIds:string[]; resultId?:string }
interface Environment { id:string; taskId:string; worktreeLabel:string; terminalSessionIds:string[]; browserSessionId?:string; boundary:Boundary }
interface AgentDefinition { id:string; name:string; role:string; source:'project'|'framework'|'user'; path:string; status:'ready'|'idle'|'offline' }
interface RuntimeBinding { agentId:string; runtime:string; model:string; mode:string; permission:'ask'|'allow'; boundary:'simulated' }
interface Run { id:string; taskId:string; environmentId:string; agentId:string; parentRunId?:string; status:RunStatus; stage:string; progress:number; bindingSnapshot:RuntimeBinding }
interface ActivityEvent { id:string; sequence:number; timestamp:string; taskId:string; runId?:string; environmentId:string; type:'message'|'delegation'|'run'|'tool'|'file'|'verification'|'result'; summary:string; boundary:Boundary }
interface Verification { id:string; taskId:string; runId:string; status:'running'|'passed'|'failed'; checks:{acId:string; status:'passed'|'failed'; evidence:string[]}[]; command:string; exitCode:number|null; artifacts:string[]; boundary:'simulated' }
interface Result { id:string; taskId:string; changedFiles:string[]; verificationId:string; artifacts:string[]; remainingIssues:string[]; approved:boolean }
interface PersistedUI { projectId:string; workstreamId:string; taskId?:string; activeToolView:ToolView; conversationMessages:unknown[] }
```

- 단일 `MockWorkbenchAdapter`가 seed 조회와 mutation(`createTask`, `moveTask`, `sendMention`, `updateBinding`, `rerunVerification`, `approveResult`)을 제공한다.
- mock timer는 Run을 `queued→running→waiting→completed`로 진행하며 failure toggle에서 `running→failed`; 상태마다 Activity Event를 append한다.
- `localStorage['opal.workbench.mock.v1']`에는 `PersistedUI`와 mock Conversation만 저장한다. schema version 불일치/파싱 오류 시 seed로 복구하고 non-blocking Alert를 표시한다.
- Activity는 `sequence` 오름차순, append-only로 렌더링한다. Run 실패 후 재시도는 새 Run ID를 만든다.

## 8. Acceptance criteria traceability
| AC | 화면/상태 | 구현·검토 지점 |
|---|---|---|
| AC-1 | SCR-001 | Electron 창에서 React 3열 Shell과 Actual/Mock 배지 표시 |
| AC-2 | SCR-001, 002 | 3 Workstream 전환, Task 상태 목록/Kanban |
| AC-3 | SCR-002→001 | Dialog 생성, DnD 상태 이동, 카드로 Workbench 진입 |
| AC-4 | SCR-003 | PM·Developer·Reviewer·user Agent와 Definition/Binding 분리 |
| AC-5 | SCR-001 | 두 mention 경로, PM 응답/위임과 Developer Run simulation |
| AC-6 | SCR-001, 004 | 8 Tool tab과 대표 Conversation/Terminal/Browser/Files/Diff/Result mock |
| AC-7 | SCR-001 | queued/running/waiting/completed/failed와 stage/progress |
| AC-8 | SCR-004 | Browser actions와 Playwright checks 분리, AC/evidence 연결 |
| AC-9 | SCR-001, 004 | 7종 Activity Event 시간순 목록 |
| AC-10 | SCR-001 | PersistedUI·Conversation localStorage 복원 시나리오 |
| AC-11 | SCR-001~004 | 빈 Task, 진행, 응답 대기, Run 실패, 검증 실패 상태 |
| AC-12 | SCR-001→002→001→003→004 | end-to-end 클릭 흐름, 엔티티 관계, 위임, 승인 위치 |
| AC-13 | 전체 | 변경 프런트엔드 lint·typecheck·build 통과와 생성→mention→verification→result 핵심 흐름 테스트 |
