# OPAL Product OS 데스크톱 Workbench — 와이어프레임

> 작성일: 2026-09-12 | 작성자: AI | 버전: v9.0 (TASK별 PM Coordination Room·PM/Worker Workspace 계층 반영 — `ADDITIONAL-WORK-PROJECT-HIERARCHY.md` 44~49행)
> 대조 기준: `wireframe-v1.md` (1차 EXECUTE 6~8행이 이미 통과한 설계). 본 문서는 그 이후 다섯 차례 개정을 거쳐 확정된 최종본이며 중간 변경 이력은 서술하지 않는다(개정 근거는 `TASK.md`·`ADDITIONAL-WORK-PROJECT-HIERARCHY.md` Constraints/AC와 §9 미결 배치 요약 참조).
> SSOT 2원화: 기존 범위는 `TASK.md`(C-1~C-10, AC-1~19), 27~49행 추가 요구사항은 `ADDITIONAL-WORK-PROJECT-HIERARCHY.md`(AW-AC-1~27)가 기준이다. 충돌 시 후자의 §기존 계약과의 적용 규칙을 따른다.

## 1. 서비스 개요
- **서비스명**: OPAL Product OS Desktop Workbench
- **서비스 유형**: Electron 기반 로컬 데스크톱 개발 도구 목업(Local desktop development tool mockup)
- **대상 사용자**: 여러 프로젝트·LLM CLI Agent에게 업무를 맡기고 결과를 검토하는 1인 개발자
- **핵심 기능**:
  1. 좌측 사이드바를 **재귀 Project 트리**로 탐색한다. Project를 펼치면 하위 Project → 진행 TASK → 실행 Agent 순서로 드러나고 완료 TASK는 자동으로 숨긴다(AW-AC-3·14). `PROJECTS +`는 현재 선택 Project의 TASK 생성 Dialog를 연다(AW-AC-19)
  2. TASK는 `Project → TASK → 실행 Agent` 탐색 계층과 `TASK → Surface → Files/Changes` 작업 문맥을 유지한다. TaskGroup과 별도 TASK 필터 UI는 두지 않는다
  3. 본문 **Execution Workspace(실행 작업공간)**에 TASK별 PM Coordination Room·Sub PM Workspace·Worker Terminal·독립 Terminal과 기타 Surface를 동적 탭 + split으로 배치한다
  4. Surface 탭 자체에 실행 중 세션의 진행·완료·실패 상태를 표시(AC-16)
  5. 우측 사이드바 **Files / Changes** 2탭으로 파일 탐색·추가·삭제와 git 변경·커밋 mock 관리, 좌우 리사이즈. Repository Component가 여럿인 Project는 대상 repo를 먼저 선택한다(AW-AC-5)
  6. Agent Definition 확인과 Runtime Binding 목업 설정, 추가한 Agent를 Surface 탭 세션으로 여는 경로
  7. **PM Coordination Room**에서 사용자→Main PM 단일 지시, Main PM의 Sub PM 초대, PM 간 다자 대화, TASK 배정과 결과 취합을 처리한다. 초대 시 Sub PM Workspace가, Sub PM의 Worker 호출 시 관찰 전용 Worker Terminal이 열린다(AW-AC-23~27)
  8. 좌측 사이드바 하단 진입점으로 여는 **설정 화면**이 Agent·외관·Workbench·프로젝트·목업 상태 초기화를 한 곳에서 다룬다. 프로젝트 섹션은 최상위·하위 Project 생성·연결과 사후 관리를 함께 담당한다(AW-AC-20)

### 1.1 구현 경계와 원칙
| 구분 | 이번 목업 동작 | UI 표시 | 향후 교체 경계 |
|---|---|---|---|
| 실제(Actual) | Electron 창, React 라우팅/상태, 클릭·입력·DnD·split·리사이즈, `localStorage` 복원 | 상단 `Interactive mock` 배지 | 유지 |
| 시뮬레이션(Simulated) | Agent/터미널 세션 출력, 세션 상태 전이(진행→완료/실패), Browser 조작, git 스테이징·커밋 | 항목별 `Simulated` 배지와 점선 테두리 | `MockWorkbenchAdapter`를 Runtime Adapter로 교체 |
| 미구현(Not connected) | ACP/LLM CLI, PTY, CDP/agent-browser, Git/Worktree, SQLite, 실제 파일시스템 쓰기 | 관련 패널 `Runtime not connected` 안내 | 실제 Runtime 연결 |

- `Project(재귀 트리) → 진행 TASK → 실행 Agent`를 좌측 탐색 계층으로 실제 렌더한다. TaskGroup과 별도 필터 UI는 제거하고 완료 TASK를 자동으로 숨긴다. `oppl`·`opsdd` 내부 backlog·ACT는 트리에 추가하지 않는다(AW-AC-13~15).
- Agent Run 원본·도구 로그·검증 상세·승인 UI는 제외한다(C-10). Room에는 PM 수준 대화와 요약 이벤트만 표시하며 원본 실행은 관찰 전용 Sub PM/Worker Terminal에 둔다(§4.7).
- Terminal·Browser·Files(sidebar)·Diff는 Run이 아니라 `Execution Environment`가 소유하는 것으로 표시한다. 본문 Surface 탭도 활성 Task의 Environment 문맥 안에서 열린다.
- Agent Definition(`.opal/AGENT.md`)과 Runtime Binding(runtime/model/mode/permission)은 별도 데이터와 UI로 다룬다.
- 터미널·에이전트 세션의 원본 출력은 기본 화면에 무제한 노출하지 않는다(C-5) — scrollback은 최근 N줄만 렌더링하고 전문은 목업 범위에서 제공하지 않는다.

## 2. 전체 구조
### 2.1 레이아웃 유형
고정 3열 Desktop Shell: 좌측 Project/TASK/실행 Agent 트리, 중앙 Execution Workspace(PM Coordination Room + Sub PM/Worker Workspace + 독립 Terminal), 우측 Files/Changes. 최소 창 크기 `1280×760`.

`ResizablePanelGroup`(기존 `resizable.tsx` = react-resizable-panels 래퍼)로 3열 전체를 감싼다.
- 좌측 패널: 240~360px 리사이즈 가능. 패널 상단 우측 모서리에 접기 아이콘(R-5)으로 완전히 접을 수 있다. 패널 최하단에는 별도 바텀 바(`SidebarBottomBar`, R-7)가 고정되어 설정 아이콘(⚙️) 하나만 놓인다 — Orca의 도움말·위치찾기·레이아웃 아이콘은 캡틴이 요청 범위에서 제외했으므로 넣지 않는다.
- 중앙 패널: `minmax(480px, 1fr)`, split 시 내부에 중첩 `ResizablePanelGroup`(direction=horizontal|vertical) 생성. 양쪽 사이드바가 접히면 중앙 패널이 그만큼 넓어진다.
- 우측 패널: 168~480px 리사이즈, 기본 320px. 좌측과 동일하게 상단 우측 모서리 접기 아이콘으로 접을 수 있다.

좌·우 사이드바 접힘은 `react-resizable-panels`의 `collapsible`/`collapsedSize=0` 특성을 그대로 쓴다(신규 라이브러리 없음, §6). 접힌 패널은 폭 0으로 축소되고 본문 헤더 쪽에 얇은 세로 바 + 펼치기 아이콘만 남는다(Orca 참조: 패널 상단 우측 모서리 접기 아이콘).

좁은 창에서는 우측을 Sheet로 접되 모바일 레이아웃은 범위 밖이다.

### 2.2 네비게이션 구조
- **Project 트리**(v8.0): `PROJECTS +` 아래 Project→진행 TASK→실행 Agent를 한 트리에서 재귀 렌더한다. Project 행 클릭은 문맥 전환, TASK 행 클릭은 Execution Workspace 전환, Agent 행 클릭은 해당 실행 Surface 포커스다. 별도 필터 바는 없고 완료 TASK는 자동으로 숨긴다.
  - `PROJECTS +`는 현재 선택 Project에 TASK를 만들며 Pilot과 담당 PM/Agent를 선택한다. 참여 Project는 사용자가 선택하지 않고 Main PM이 Room에서 초대한다.
  - Project 생성·연결은 설정 화면의 프로젝트 섹션에서 최상위 또는 부모 Project를 지정해 수행한다.
- **본문 Surface 탭 바**: 탭 목록 + 마지막 탭 옆에 고정된 `+` 버튼(새 Surface, W-1/R-11) + 우측 `⌘K`(명령) + 오버플로 메뉴 + 검색 입력("열린 탭, 방문 기록, 파일, URL, agent 검색…"). **닫히지 않는 탭은 없다** — pinned 시스템 탭 개념 자체가 존재하지 않는다.
  - `+` 메뉴 항목: `PM Coordination` / `Terminal` / `Browser` / `Markdown` / `모바일 에뮬레이터`, 그 아래 LLM 에이전트 목록
  - `Terminal`은 사용자가 직접 조작하는 독립 셸이다. 조율 TASK의 Sub PM/Worker Agent Terminal은 해당 Agent가 제어하고 사용자는 관찰만 한다.
  - LLM과의 대화는 `Terminal`(예: CLI에서 직접 `claude`류 명령 실행) 또는 LLM 에이전트 Surface 탭 **안에서** 일어난다. 대화 전용 별도 화면은 없다.
  - 탭 드래그 → 본문 영역 좌/우/상/하 25% 가장자리에 드롭 시 해당 방향으로 split, 중앙 드롭 시 같은 pane 안에서 탭 순서 재배치. split된 pane 사이의 탭 드래그 이동도 지원한다.
  - 각 탭에 세션 상태 표시(진행/완료/실패)가 항상 붙는다(§4.1 인터랙션, §5 `SurfaceTabStatusIndicator`, AC-16).
- **우측 Files/Changes 탭**: Files(폴더·파일 트리, 추가/삭제) · Changes(git 스테이징·diff·커밋 목업). 결과 검토는 이 `Changes` 탭이 담당한다(C-10). 좌·우 사이드바 모두 패널 상단 우측 모서리 아이콘으로 접고 펼칠 수 있다(R-5, AC-10 확장).
- **좌측 사이드바 바텀 바 설정 아이콘**(R-7) → SCR-003 설정 화면. Agent 섹션에서 바로 "Surface에서 열기"로 세션 탭을 만들 수 있다(C-4). 헤더의 `Agents` 버튼은 폐기되어 진입 경로가 이 아이콘 하나로 일원화된다(R-9).

### 2.3 화면 흐름도
```text
[앱 시작/복원] → SCR-001 Shell(Project 트리) ── 헤더 Board ──→ SCR-002 Kanban(내부 New Task → Dialog)
       ↑               │                                  │ 생성/카드 클릭
       │               ├── PROJECTS `+` ──────→ SCR-002 Task 생성 Dialog(현재 선택 Project)
       │               ├── Project/TASK/Agent 트리 선택 ─→ 문맥 전환 또는 실행 Surface 포커스
       │               ├── 조율 TASK 행 클릭 ────→ SCR-008 PM Coordination Surface
       │               ├── 좌측 하단 설정(⚙️) ────→ SCR-003 설정 Dialog ─┬─ Project 생성/연결(SCR-007)
       │               │                                                └─ Agent Surface에서 열기 ─┐
       │               │                                  │ 저장/닫기                        │
       │               ├── 본문 `+` → Surface 탭 추가/드래그 split ─→ SCR-005 Surface 배치 ←──┘
       │               │        (Terminal 또는 Agent 탭 안에서 LLM 대화 발동, 탭에 상태 표시)
       │               ├── 우측 Files/Changes 전환 ─→ SCR-006 파일·git 패널(선택 repo 범위, 결과 검토 위치)
       └── 복원 ───────┴── Project 트리 펼침·선택 Project/TASK·Surface 탭/split 배치 복원
```

### 2.4 대표 클릭 시나리오
0. 좌측 사이드바 최하단 설정 아이콘을 클릭해 설정 화면을 열고, 외관 섹션에서 테마를 `다크`로 바꾼 뒤 닫는다(R-7·R-8).
1. 설정의 프로젝트 섹션에서 `/Volumes/Data/StoreLinkStudio/pug`·`blend`·`mams`를 연결한다. 이어서 `StoreLinkStudio`를 신규 생성하고 세 Project의 부모로 지정해 복합 Project 구조를 만든다(AW-AC-1·2·3·10·20).
2. Project 트리에서 `Pug`를 선택하고 `PROJECTS +`를 눌러 제목·설명·Pilot·담당 Agent를 입력해 `todo` TASK를 만든다(AW-AC-19).
3. 카드를 `In Progress`로 이동하고 클릭해 Workbench에 진입한다. 진입 시 본문은 빈 상태이며 `첫 Surface 열기` CTA만 보인다.
4. 본문 `+`에서 `Developer` LLM 에이전트를 선택해 Surface 탭을 열고 "로그인 오류를 구현해줘"를 대화로 보낸다. 탭에 `진행 중` 상태 표시가 붙는다.
5. 추가로 Agent에 귀속되지 않은 독립 `Terminal`·`Browser`를 열고, `Terminal` 탭을 화면 하단 가장자리로 드래그해 아래쪽으로 split한다. 이어서 `Developer` Agent Terminal 탭을 같은 pane의 탭 바 위 `Terminal` 옆으로 드래그해 탭 순서를 바꾼다(R-10, AW-AC-21·22).
6. Agent 탭의 세션 상태가 `완료`로 바뀌는 것을 탭에서 바로 확인한다.
7. 우측 사이드바를 `Files`로 전환해 변경된 파일을 확인하고, `Changes`로 전환해 스테이징 상태와 diff를 검토한 뒤 `커밋 mock`을 남긴다.
8. `StoreLinkStudio` 조율 TASK의 PM Coordination Surface에서 Main PM이 `Pug PM`에게 업무를 배정한다. Pug Project에 연결 TASK와 Pug PM Terminal이 생성되는 것을 확인하고, Sub PM의 상태·블로커·결과가 조율 대화로 상향되는 것을 확인한다.
9. 앱 재실행 시 마지막 Project 트리 펼침·선택 Project/TASK·Surface 탭 배치(split 포함)가 복원됨을 확인한다.

## 3. 화면 목록
| ID | 화면명 | 유형 | 경로 | 메뉴그룹 | 설명 |
|---|---|---|---|---|---|
| SCR-001 | Desktop Workbench Shell | detail | `/workbench/:projectId/:taskId` | Project | 3열 shell, 좌측 재귀 Project 트리(v6.0), 순수 동적 Surface 탭 |
| SCR-002 | Task 생성 Dialog/Kanban | crud | `/workbench/:projectId?view=board&dialog=new-task` | Task | 제목·설명·Pilot·담당 Main PM을 선택해 Task 생성, Kanban 상태 이동. 참여 Project 선택은 없음 |
| SCR-003 | 설정 화면(Agent·외관·Workbench·프로젝트·목업) | settings | `/workbench/:projectId?settings=agent\|appearance\|workbench\|project\|mock` | Global | Agent Catalog·Binding, 외관·Workbench 기본값·프로젝트 관리·목업 초기화를 다룬다. **v8.0**: 프로젝트 섹션에서 최상위/하위 Project 신규 생성·기존 연결과 사후 관리를 함께 제공한다(AW-AC-20) |
| *(SCR-004 결번)* | — | — | — | — | 위임·Run 추적·검증·결과 승인 화면이었으나 C-10으로 범위 제외. 번호를 재사용하지 않는다 |
| SCR-005 | Surface 탭 배치·Split Workbench | detail | `/workbench/:projectId/:taskId?surfaces=...` | Task | Terminal/Browser/Markdown/Emulator/Agent Surface의 동적 탭·split·세션 상태 관리 |
| SCR-006 | Files/Changes 사이드바 | monitor/crud | `/workbench/:projectId/:taskId?rail=files\|changes` | Task | 프로젝트(선택 repo 범위) 파일 탐색·추가/삭제, git 변경·커밋과 결과 검토 |
| SCR-007(신규 v6.0) | Project 생성/연결 Dialog | form | `/workbench/:projectId?dialog=new-project\|link-project&parent=<projectId?>` | Project | 최상위 또는 선택 Project의 자식으로 신규 생성/기존 OPAL Project 연결(AW-AC-1·2·3) |
| SCR-008(v7.0 재정의) | PM Coordination Surface | detail/action | `/workbench/:projectId/:taskId?surface=coordination` | Task | Main/Sub PM 대화, 구조화 이벤트, Sub PM 배정으로 하위 TASK·실행 Surface 생성(AW-AC-7~9·16~18) |

## 4. 화면별 상세 설계
### 4.1 Desktop Workbench Shell (SCR-001)
- **유형**: detail
- **경로**: `/workbench/:projectId/:taskId`
- **진입점**: 앱 시작 복원, Kanban 카드, Task 목록
- **초기값**: `project_opal / (그룹 없음) / task_login_fix / Surface 없음(빈 상태)`

#### 레이아웃
```text
┌ [Pug ▾] ─ Development / Login fix ─ [Interactive mock] ───────── [⌘K] ┐
├───────────────┬───────────────────────────────────────────┬───────────────┤
│ PROJECTS  [+]│ Developer① ⣾  Terminal② ●  Browser③ ✓ [+]│ FILES CHANGES[»]│
│[«]           │┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈split┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈│ v src/  [M]   │
│v StoreLinkStudio│ Developer① [Simulated]        │ Terminal②    │   v workbench/[3]│
│  PM:Main·TASK 1│ > 로그인 오류를 구현해줘        │ $ npm run dev│    📄WorkbenchApp.tsx [M]│
│ v ●Pug  PM:PugPM│ Developer: 원인을 분석합니다    │ > ready [Sim]│    📄types.ts   [U]│
│   ▾ TASKS [+] │ [입력............] [Send]       ├──────────────┤    📄mock-adapter.ts│
│   [상태][Pilot]│                                  │ Browser③     │  > components/  │
│   ●Login fix  │                                  │ localhost:5173│  node_modules/ *ignored*│
│     └Developer│                                  │ (canvas mock) │              │
│   ○Empty task │                                  │              │              │
│  >Blend PM:BlendPM│                                  │              │              │
│  >MAMS PM:MamsPM │                                  │              │              │
├──────────────┤                                  │              │              │
│ [⚙️ 설정]    │                                  │              │              │
└──────────────┴────────────────────────────────────────────┴──────────────┘
   ↔ 리사이즈, [«]접기   ↔ split 경계 리사이즈 가능(react-resizable-panels)  ↔ 리사이즈, [»]접기
   (⣾=진행중 스피너 ●=완료 점 ✓=완료 배지, §4.4 세션 상태 표시 참조)
   (Project 트리: v/>=Project 펼침/접힘 셰브론, ●=블로커 있음/○=없음, PM: 행에 고정 표시, §4.6a)
   (Files 트리: v/>=폴더 펼침/접힘 셰브론, 📄=파일 아이콘, 우측 [M]수정/[U]미추적/[⊘]무시, ignored 이탤릭, 그룹 헤더 우측 건수 배지)
   ([⚙️ 설정] = 좌측 사이드바 바텀 바, 클릭 시 SCR-003 설정 화면 Dialog가 열린다. R-7)

접힘 상태(좌측 접힘 예):
┌[»]┬────────────────────────────────────────────┬──────────────┐
│   │ Developer① ⣾  Terminal② ●  Browser③ ✓  [+]│ FILES CHANGES│
```
좌측 패널이 접히면 바텀 바(설정 아이콘)도 함께 접혀 숨겨진다. 펼치기 아이콘을 눌러 패널을 복원해야 설정에 접근할 수 있다.
Project 트리 셰브론(`v`/`>`)은 §4.6a에서 정의한 `ProjectTreeRow`가 소유하며, 펼침 상태는 `PersistedUI.expandedProjectIds`로 저장·복원한다(AW-AC-11). 트리에서 선택한 Project가 헤더 브레드크럼(`[Pug ▾]`)과 본문 문맥을 함께 결정한다.

#### Component hierarchy
```text
WorkbenchShell
├─ AppHeader(ProjectBreadcrumb, MockBadge, CommandButton)
├─ ResizablePanelGroup(direction=horizontal)
│  ├─ ResizablePanel(collapsible, WorkbenchSidebar(
│  │    SidebarCollapseToggle,
│  │    ProjectTreeHeader(Label"PROJECTS", AddTaskButton→SCR-002),
│  │    ProjectTree(ProjectTreeRow*(ProjectTree 재귀, ActiveTaskTreeRow*(AgentTreeRow*)) — §4.6a),
│  │    SidebarBottomBar(SettingsButton)))
│  ├─ ResizableHandle
│  ├─ ResizablePanel(ExecutionWorkspace)
│  │  └─ SurfaceWorkspace(PM Coordination | Agent Terminal | Independent Terminal | 기타 Surface)
│  │     └─ SurfaceSplitRoot(ResizablePanelGroup 재귀 — SurfacePane*)
│  │        └─ SurfacePane(SurfaceTabBar-local[DynamicTabs+StatusIndicator], SurfaceBody[가장자리 split 드롭 타깃], ActiveSurfaceView | PmCoordinationSurface[§4.7])
│  ├─ ResizableHandle
│  └─ ResizablePanel(collapsible, RightRail(RailCollapseToggle, RepoScopeSelect[Repository Component 2개 이상일 때만, §4.5], FilesTab | ChangesTab))
├─ NewTaskDialog(TaskBoard의 Dialog와 공유 — `PROJECTS +`와 Kanban `New Task` 두 진입점이 동일 컴포넌트 사용)
├─ NewOrLinkProjectDialog(SCR-007 — SettingsDialog Project 섹션에서 신규/연결 모드와 parentProjectId를 지정)
└─ SettingsDialog(SettingsNav(AgentTab, AppearanceTab, WorkbenchTab, ProjectTab, MockTab), SettingsPanel)
```
`ProjectTree`는 Project만 그리는 컨테이너가 아니다. 펼친 Project 바로 아래에 해당 Project의 TASK, 각 TASK 아래에 현재 실행 Agent를 렌더하고, 자식 Project도 같은 규칙으로 재귀 렌더한다. `oppl`·`opsdd` 내부 backlog·ACT만 제외한다(AW-AC-13·15). PM Coordination도 닫기·이동·split 가능한 정식 Surface다.

#### 구성 요소
| 영역 | UI 요소 | shadcn 컴포넌트 | 데이터/설명 |
|---|---|---|---|
| header | Project breadcrumb·목업 배지 | Button, Separator, Badge | 선택 project와 현재 group/task. `Agents` 버튼 폐기(R-9) |
| sidebar | Project→진행 TASK→실행 Agent 재귀 트리·TASK 생성·접기·설정 | Sidebar, ScrollArea, Badge, Button, Collapsible | AW-AC-14·15·19 |
| surface tab bar | 동적 탭 전부, `+` 메뉴, 검색, 명령, 오버플로, 탭별 상태 표시 | Tabs(커스텀 확장), Command, Dialog, Input, Button, DropdownMenu | pinned 개념 없음. HTML5 native drag(`draggable`/`dragstart`/`dragover`/`drop`) 소스·타깃 |
| surface pane | split 레이아웃, 각 pane 로컬 탭 바 | Resizable(ResizablePanelGroup/Panel/Handle) | 기존 설치된 `resizable.tsx` 재사용 |
| right rail | Files/Changes 2탭·접기 아이콘 | Tabs, ScrollArea, Badge, Button, Dialog(추가), AlertDialog(삭제) | 결과 검토는 이 rail이 최종 위치, R-5 접기 |

#### 기능
1. Project 행은 Project 문맥, TASK 행은 TASK Workbench, Agent 행은 해당 실행 Surface로 전환한다.
1a. Project 행을 셰브론으로 펼치면 하위 Project(있으면) → TASK 목록 → 실행 Agent 노드가 단계적으로 드러난다. 자식이 없는 Project는 단순 Project로, 있으면 복합 Project로 표시되며 이 구분은 `parentProjectId`/자식 존재 여부에서 파생하고 별도 필드로 저장하지 않는다(AW-AC-3, §7).
2. TaskGroup과 TASK 필터는 데이터·UI에서 제거한다. `status === done`인 TASK는 좌측 트리에서 제외하되 Board와 저장 데이터에는 유지한다.
3. 본문 Surface 탭은 전부 동적이며 닫을 수 있다. Task 진입 시 기본으로 열리는 탭은 없다(빈 상태에서 사용자가 `+`로 시작).
4. LLM 대화는 Terminal Surface 또는 LLM 에이전트 Surface 탭 안에서 발생한다. 별도 Conversation 화면·`@mention` 위임 경로는 없다.
5. 동적 탭을 드래그해 본문 영역 가장자리에 드롭하면 `ResizablePanelGroup`이 재귀적으로 분할되고, split된 pane 사이에서도 탭을 드래그로 옮길 수 있다.
6. 모든 Surface 탭은 세션 상태(idle/running/completed/failed)를 탭 자체에 표시한다(AC-16, §4.4).
7. 우측 사이드바는 Files(트리 네비게이션+추가/삭제)와 Changes(git 스테이징/diff/커밋) 2탭이며 좌우로 리사이즈된다.
8. 좌측(Project/TASK/Agent)과 우측(Files/Changes) 사이드바는 독립적으로 접고 펼칠 수 있고 상태를 복원한다.
9. Files 트리는 폴더 노드를 셰브론(`>`펼침/`v`접힘)으로 접고 펼치며, 각 행은 폴더·파일 아이콘과 우측 정렬 git 상태 배지(`M`/`U`/`⊘`)를 표시한다. ignored 항목은 이탤릭으로 표기하고 들여쓰기는 깊이당 12~16px로 좁게 유지한다(a).
10. Changes는 파일을 디렉터리별로 그룹핑하고 그룹 헤더에 건수 배지를 단다. `변경 사항 N`(staged)과 `추적되지 않은 파일 N`(unstaged) 두 섹션으로 나누며, 각 파일 행에 `+n -m` 추가/삭제 라인 수를 표시한다(c, d).
11. 조율 TASK 행은 참여 Project 칩을 표시하고, 클릭 시 저장된 Surface 배치 중 `PM Coordination` 탭을 포커스한다(AW-AC-7·16).

#### 인터랙션
| 이벤트 | 동작 | 결과 |
|---|---|---|
| Project 트리 행 클릭 | activeProjectId 갱신, 그룹/Task/Surface 재로드 | 좌측 목록·본문·rail 전부 교체 |
| Project 행 셰브론 클릭 | 해당 Project 펼침/접힘 토글 | 자식 Project·TASK 노드 렌더 여부 전환, `PersistedUI.expandedProjectIds` 갱신(AW-AC-11) |
| `PROJECTS +` 클릭 | `NewTaskDialog` 오픈 | 현재 선택 Project에 제목·설명·Pilot·담당 Agent, 조율 TASK이면 참여 Project 저장 |
| 설정 > 프로젝트 > 생성/연결 | `NewOrLinkProjectDialog` 오픈 | 최상위 또는 부모 Project를 선택해 신규 생성·기존 연결 |
| TASK/Agent 트리 행 클릭 | TASK 선택 또는 Surface 포커스 | 중앙 Execution Workspace와 우측 repo 문맥 전환 |
| Surface `+` 클릭(탭 바 안, 마지막 탭 옆, W-1/R-11) | 메뉴 오픈(터미널/브라우저/Markdown/에뮬레이터 + Agent 목록) | 선택 항목으로 새 동적 탭 생성, 활성 pane에 추가, 초기 상태 `idle` |
| Terminal/Agent 탭 안에서 메시지 전송 | mock 응답 스크립트 재생, 탭 상태 `running`으로 전환 | 응답 완료 시 `completed`, 실패 toggle 시 `failed` |
| 동적 탭 드래그→pane 본문 가장자리 드롭 | split 방향 결정(top/bottom/left/right) | 새 `SurfacePane` 생성, 기존 탭 이동 |
| 동적 탭 드래그→탭 바(다른 pane 포함) 드롭 | 드롭 위치 기준 삽입 인덱스로 탭 편입/재배치(R-10, §4.4) | 원본 pane에 탭이 남아있지 않으면 pane 자동 축소 |
| 탭 닫기(X) | 동적 탭 제거 | pane에 남은 탭 0개면 pane 제거·인접 pane 확장 |
| 좌측 바텀 바 설정 아이콘 클릭 | `SettingsDialog` 오픈, 마지막 방문 섹션(기본 Agent) 표시 | Workbench는 dimmed 유지, 닫으면 원 상태로 복귀 |
| 좌/우 사이드바 접기 아이콘 클릭 | 해당 `ResizablePanel`을 `collapsedSize=0`으로 축소, 얇은 펼치기 바로 대체 | `PersistedUI.sidebarCollapsed`/`railCollapsed` 갱신·저장 |
| 접힘 바 클릭 또는 펼치기 아이콘 클릭 | 이전 폭으로 패널 복원 | 접기 이전 폭(`sidebarWidthPx`/`railWidthPx`) 유지 |
| Files ▸ 폴더 행 셰브론 클릭 | 해당 폴더 펼침/접힘 토글 | 자식 노드 렌더 여부만 전환, 데이터는 유지 |
| 우측 Files ▸ 파일 우클릭 | 컨텍스트 메뉴(추가/삭제) | 목업 파일 트리 mutate |
| 우측 Changes ▸ 그룹 헤더 클릭 | 그룹 접기/펼치기 | 그룹 내 파일 목록 표시 토글(로컬 UI 상태) |
| 우측 Changes ▸ 파일 클릭 | 해당 diff Surface 탭을 동적 탭으로 오픈 | 본문에 Diff 탭 추가 또는 기존 탭 포커스 |
| 사이드바 핸들 드래그 | 좌/우 패널 폭 조정 | 240~360px(좌), 168~480px(우) 제한 |

#### Empty/loading/error states
| 상태 | 표시와 회복 동작 |
|---|---|
| Project 없음 | 중앙 Empty State: `연결된 Project가 없습니다` + `Project 연결(mock)` |
| 빈 Task(Surface 없음) | 중앙 Empty State: `열린 작업 공간이 없습니다` + `+ Surface 열기` |
| Surface 세션 running | 탭에 스피너, 본문에 skeleton/진행 표시 |
| Surface 세션 failed | 탭에 실패 배지(destructive), 본문에 실패 Alert + `다시 실행` |
| Surface pane split 후 탭 0개 | pane 자동 제거, 인접 pane이 공간 흡수 |

### 4.2 Task 생성 Dialog/Kanban state (SCR-002)
- **유형**: crud/form
- **경로**: `/workbench/:projectId?view=board&dialog=new-task`
- **진입점**: ① 좌측 사이드바 TASKS 헤더 `+` — 보드를 거치지 않고 Dialog가 바로 열린다(W-2/R-12). ② 헤더 `Board` 버튼으로 연 Kanban 안의 `New Task` — 생성 후 Kanban 유지. 두 진입점은 동일한 `NewTaskDialog` 컴포넌트를 공유한다.

#### 레이아웃
```text
┌ OPAL Tasks ─────────────────────────────────────────── [+ New Task] ┐
│ TODO (2)           IN PROGRESS (1)       REVIEW (1)       DONE (3)    │
│ ┌Login empty┐      ┌API login fix┐       ┌Check diff┐     ┌Setup┐     │
│ └───────────┘      └─────────────┘       └──────────┘     └─────┘     │
│        ┌ 새 Task ────────────────────────────────────────────┐         │
│        │ 제목* [________________]  Pilot* [opd_________▾]    │
│        │ 설명* [..........................................] │         │
│        │ Lead Agent* [OPAL PM▾]  초기 상태 [Todo▾]           │         │
│        │                         [취소] [Task 만들기]         │         │
│        └────────────────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────────────────┘
```

#### Component hierarchy
```text
TaskBoard(KanbanColumns(TaskCard*))
└─ NewTaskDialog(NativeForm(Label, Input, Textarea, PilotSelect, AgentSelect), DialogFooter)
```

#### 구성 요소
| 영역 | UI 요소 | shadcn 컴포넌트 | 데이터/설명 |
|---|---|---|---|
| content | 4열 Kanban·TASK card | Card, Badge, ScrollArea | activeProject 범위 |
| modal | 제목·설명·Pilot·lead·상태 | Dialog, Label, Input, Textarea, Select | 참여 Project는 Main PM이 Room에서 초대하므로 사용자 입력에서 제외 |
| feedback | validation·생성 완료 | Alert | 필수값과 mock 저장 성공을 inline Alert로 표시 |

#### 기능 및 인터랙션
| 이벤트 | 동작 | 결과 |
|---|---|---|
| 빈 제목/설명으로 제출 | client validation | field error, Dialog 유지 |
| 유효 제출 | Task mock 생성 | 선택 Pilot·담당 Main PM을 보존하고 Todo 카드 추가; 참여 Project는 소유 Project만 초기화 |
| 카드 drag/drop | 허용 열로 status 변경 | 카드 이동·localStorage 저장 |
| 카드 클릭 | Task 선택 | SCR-001 진입(빈 Surface 상태) |

#### Empty/loading/error states
- Project에 TASK가 없으면 `첫 TASK 만들기`를 표시한다.
- mock 저장 실패 toggle이 켜지면 Alert와 `다시 시도`; 입력값과 카드 원상태를 보존한다.

### 4.3 설정 화면 — Agent·외관·Workbench·프로젝트·목업 (SCR-003, v5.0 재정의)
- **유형**: settings
- **경로**: `/workbench/:projectId?settings=agent|appearance|workbench|project|mock`
- **진입점**: 좌측 사이드바 바텀 바 설정 아이콘(R-7)
- **표현 형식**: **Dialog(large, 좌측 섹션 목록 + 우측 패널)**. 근거는 아래 참조.

#### 표현 형식 선택 근거
기존 UI kit 범위(§6)에서 세 후보를 검토했다.
1. **Sheet 확장(기존 AgentSheet 방식 유지)** — 폭이 좁아 5개 섹션(Agent/외관/Workbench/프로젝트/목업)을 좌측 내비게이션과 함께 담기엔 비좁고, Agent 섹션만 해도 목록+상세+바인딩 폼 3단 구성이라 Sheet 한 폭에 다시 넣으면 v4.0에서 이미 쓰던 레이아웃이 더 눌린다.
2. **전체 화면 라우트 신설** — Workbench 자체가 이미 3열 shell이라 설정을 위해 전체 화면을 새로 차지하면 뒤 맥락(현재 Project/Task)을 잃고, 라우팅 상태(`surfaces=`, `rail=` 등)와의 공존 처리가 늘어난다.
3. **Dialog(large) + 내부 좌측 섹션 목록 + 우측 패널(채택)** — 이미 설치된 `Dialog`(SCR-002에서 사용 중)를 `max-w-4xl h-[75vh]` 정도로 키우고 내부를 좌우로 나누면, VS Code/Orca류 설정 창과 동일한 정보구조를 신규 컴포넌트 없이 구현할 수 있다. Workbench 컨텍스트(현재 Project) 위에 뜨는 모달이라 "설정을 잠깐 보고 돌아온다"는 사용 패턴에 맞고, 닫으면 Workbench 상태가 그대로 보존된다.

**SCR-003 처리 방식**: 번호를 **재정의**한다(결번 처리하지 않음). 화면 기능(Agent Catalog·Binding)은 폐기되지 않고 그대로 설정 화면의 한 섹션으로 이동했을 뿐이라 `SCR-004`(위임·Run 화면, 기능 자체가 사라짐)와는 성격이 다르다. 새 SCR 번호를 발급하면 AC-4가 가리키는 화면 ID가 끊기므로, 기존 SCR-003 자리에서 유형(`settings`)과 진입 경로만 갱신하는 쪽이 추적성을 지킨다.

#### 레이아웃
```text
┌ 설정 ─────────────────────────────────────────────────── [Interactive mock] [X]┐
│ ┌ Agent        │  Runtime Binding [Simulated]                                 │
│ │ 외관         │  ● OPAL PM   project/default · ready                          │
│ │ Workbench    │  ○ Developer framework · idle    [Surface에서 열기]           │
│ │ 프로젝트     │  ○ Reviewer  framework · idle                                 │
│ │ 목업         │  ○ UI Coach  user · offline                                   │
│ └──────────────┤  ─────────────────────────────────────────                   │
│                │  Runtime [Codex ACP▾]  Model [gpt-5.5▾]  Mode [ask▾]          │
│                │  Definition .opal/AGENT.md (readonly)                        │
│                │                              [되돌리기] [설정 저장]           │
└────────────────┴────────────────────────────────────────────────────────────┘

섹션 전환 시 우측 패널만 교체(예: 외관):
│ ┌ Agent        │  테마  ( ) 시스템 (●) 라이트 ( ) 다크                         │
│ │ 외관◀        │  폰트 크기  ( ) 작게 (●) 보통 ( ) 크게                        │
│ │ Workbench    │                                                              │

예: Workbench:
│ │ Workbench◀   │  새 탭 기본 종류 [Terminal▾]                                  │
│ │              │  좌측 사이드바 기본 접힘  [ ]   우측 rail 기본 접힘 [ ]        │
│ │              │  파일 트리 들여쓰기(px)  [14]                                 │

예: 프로젝트(v6.0: 사후 관리 전용 — 생성·연결은 제공하지 않는다. 추가문서 대체표 4):
│ │ 프로젝트◀    │  StoreLinkStudio  (최상위) PM:Main            [부모 변경] [제거]│
│ │              │   ├ Pug   /Volumes/.../pug     PM:PugPM   [경로 변경] [제거]  │
│ │              │   ├ Blend /Volumes/.../blend   PM:BlendPM [경로 변경] [제거]  │
│ │              │   └ MAMS  /Volumes/.../mams    PM:MamsPM  [경로 변경] [제거]  │

예: 목업:
│ │ 목업◀        │  목업 상태 초기화                                             │
│ │              │  localStorage를 지우고 seed 데이터로 되돌립니다.               │
│ │              │                                        [상태 초기화]         │
```

#### Component hierarchy
```text
SettingsDialog
├─ SettingsNav(NavItem: Agent|외관|Workbench|프로젝트|목업)
└─ SettingsPanel
   ├─ AgentSection(CatalogToolbar(SearchInput, SourceFilter), AgentList(AgentListItem*(OpenInSurfaceButton)), BindingForm(DefinitionSummary, RuntimeSelect, ModelSelect, ModeSelect, Actions))
   ├─ AppearanceSection(ThemeRadioGroup, FontSizeRadioGroup)
   ├─ WorkbenchSection(DefaultSurfaceKindSelect, SidebarDefaultSwitch, RailDefaultSwitch, TreeIndentInput)
   ├─ ProjectSection(ProjectTreeList(ProjectRow*(PathLabel, PMLabel, ParentLabel, ChangePathButton, ChangeParentButton, RemoveButton)) — **생성·연결 버튼 없음, 사후 관리 전용(v6.0)**)
   └─ MockSection(ResetMockStateButton, ConfirmAlertDialog)
```
`AgentSection`은 v4.0 `AgentCatalogSheet`의 하위 구조(`CatalogToolbar`/`AgentList`/`BindingForm`)를 그대로 옮긴 것이며 기능 변경은 없다(C-3 Agent 정의·runtime 설정 분리 유지).

#### 구성 요소
| 영역 | UI 요소 | shadcn 컴포넌트 | 데이터/설명 |
|---|---|---|---|
| nav | 5개 섹션 버튼 | Button(ghost, active 강조) | 좌측 세로 목록, 클릭으로 우측 패널만 교체 |
| Agent | 검색·source 필터·목록·binding 폼 | Input, Select, ScrollArea, Badge, Avatar, Button, Label, Switch | v4.0 AgentSheet 구성과 동일(C-3 정의/바인딩 분리 유지) |
| 외관 | 테마·폰트 크기 | RadioGroup(또는 기존 Select로 대체) | `Settings.theme`/`fontScale`, 즉시 미리보기 적용(로컬) |
| Workbench | 새 탭 기본 종류·좌우 사이드바 기본 접힘·트리 들여쓰기 | Select, Switch, Input(number) | `Settings.defaultNewSurfaceKind`/`sidebarCollapsedDefault`/`railCollapsedDefault`/`treeIndentPx`. **새 Task 진입 시 기본값**이며 이미 저장된 `PersistedUI`의 현재 접힘 상태를 덮어쓰지 않는다 |
| 프로젝트 | Project 생성·연결·등록 트리·경로·PM·부모 관계 | Card/div, Button, Dialog | 최상위/하위 Project 생성·기존 OPAL Project 연결 + 경로/부모 변경·제거(§7, AW-AC-20) |
| 목업 | 상태 초기화 버튼 | Button(destructive), AlertDialog | `localStorage['opal.workbench.mock.v4']`와 `opal.workbench.settings.v1`를 지우고 seed로 복귀 |

#### 기능 및 인터랙션
| 이벤트 | 동작 | 결과 |
|---|---|---|
| 좌측 섹션 클릭 | 우측 패널 교체 | 마지막 방문 섹션은 세션 중 기억(재실행 시 복원 대상 아님) |
| (Agent) Agent 선택 | definition과 binding 조회 | 역할/source/status와 설정 표시 |
| (Agent) runtime 변경 | runtime별 model 목록 필터 | model 기본값 갱신, unsaved badge |
| (Agent) `Surface에서 열기` | 해당 Agent binding으로 LLM 에이전트 Surface 탭 생성 | Dialog 닫힘, 본문에 새 탭 추가·포커스(C-4) |
| (Agent) 저장 | binding mock 저장 | inline Alert; 이미 열린 세션의 binding snapshot은 불변 |
| (외관) 테마/폰트 라디오 변경 | 즉시 적용 | `updateSettings` mock 저장, 새로고침 없이 반영 |
| (Workbench) 값 변경 | 즉시 적용 | `updateSettings` mock 저장, 다음 신규 Task/앱 실행부터 기본값으로 사용 |
| (프로젝트) `Project 생성`/`기존 Project 연결` | `NewOrLinkProjectDialog` 오픈 | 부모 Project 선택 후 mock Project 추가·트리 갱신 |
| (프로젝트) `경로 변경` | 경로 입력 Dialog | mock으로 `Project.repositoryPath` 갱신 |
| (프로젝트) `부모 변경`(v6.0) | 부모 Project 선택 Dialog(순환 방지 검증) | mock으로 `Project.parentProjectId` 갱신, Project 트리 재배치. 순환이 되는 선택은 비활성 처리(§7) |
| (프로젝트) `제거` | 확인 AlertDialog | Project 목록에서 제거(연결된 Task/데이터는 이번 범위에서 함께 정리하지 않음 — 목업 한계 명시). 자식이 있는 Project 제거 시 자식은 최상위로 승격 |
| (목업) `상태 초기화` | 확인 AlertDialog(`정말 초기화할까요?`) | 승인 시 두 localStorage 키 삭제 후 seed로 재부팅, Dialog 닫고 Workbench 새로고침 |
| Dialog 바깥/ESC/[X] | 닫기 | 미저장 Agent binding이 있으면 v4.0과 동일하게 `계속 편집/변경 폐기` 확인 |

#### Empty/loading/error states
- Agent 검색 결과 없음: 필터 초기화 버튼. Catalog loading: 4개 row skeleton.
- Runtime 미연결 Agent: `offline / Runtime not connected`; `Surface에서 열기`는 비활성 처리하고 사유 Tooltip 표시.
- 설정 저장 실패 mock: 이전 값 유지, inline error와 재시도 버튼.
- 프로젝트 0건: `등록된 Project가 없습니다`와 `Project 생성`·`기존 Project 연결` CTA를 표시한다.

### 4.4 Surface 탭 배치·Split Workbench (SCR-005)
- **유형**: detail
- **경로**: `/workbench/:projectId/:taskId?surfaces=<split-tree>`
- **진입점**: SCR-001 본문 `+` 메뉴, 탭 드래그, SCR-003 `Surface에서 열기`

#### 레이아웃 (2-way split 예시: 좌 Terminal, 우 상하 Browser/Developer)
```text
┌ Terminal① ● Browser② ✓ Developer③ ⣾ [+]                              ┐
├──────────────────────────────┬──────────────────────────────────────┤
│ Terminal①  [완료 ●]          │ Browser②  [완료 ✓]                    │
│ $ npm run dev        [Sim]   │ [Simulated 배지] localhost:5173       │
│ > ready                       │ (browser canvas mock)                │
│                                ├────────────────────────────────────┤
│                                │ Developer③  [진행중 ⣾]              │
│                                │ > 로그인 오류를 구현해줘             │
│                                │ Developer: 원인을 분석 중...         │
└──────────────────────────────┴──────────────────────────────────────┘
        ↔ 드래그로 폭 조정              ↕ 드래그로 높이 조정
```

#### Component hierarchy
```text
SurfaceSplitRoot(ResizablePanelGroup)
├─ SurfacePane(SurfaceTabBar, SurfaceView=TerminalSurface)
└─ ResizablePanelGroup(direction=vertical)
   ├─ SurfacePane(SurfaceTabBar, SurfaceView=BrowserSurface)
   └─ SurfacePane(SurfaceTabBar, SurfaceView=AgentCliSurface[agent=developer])
```

#### 구성 요소
| Surface 유형 | 표시 | 목업 동작 |
|---|---|---|
| Terminal | xterm 유사 mock 출력, 채팅형 CLI 대화 가능 | 고정 스크립트 라인 재생, `[Simulated]` |
| Browser | URL바 + canvas placeholder | 고정 조작 로그, `[Simulated]` |
| Markdown | 텍스트 프리뷰 | 정적 mock 문서, `[Simulated]` |
| 모바일 에뮬레이터 | 기기 프레임 + 화면 mock | 정적 스크린 이미지, `[Not connected]`(CDP 미연결) |
| LLM 에이전트(Agent Catalog 항목) | 채팅형 mock 세션 | 고정 응답 스크립트, `[Simulated]`; LLM 대화가 발생하는 주 채널 |
| Diff(Changes에서 오픈) | 변경 파일 patch 뷰 | 정적 mock diff, `[Simulated]` |

#### 세션 상태 표시(AC-16)
- 상태 값: `idle`(신규 생성, 아직 입력 없음) → `running`(mock 응답/명령 진행 중) → `completed` 또는 `failed`.
- 탭 표시: `idle`은 표시 없음, `running`은 애니메이션 스피너 아이콘, `completed`는 작은 초록 점(dot), `failed`는 destructive 색 배지(느낌표).
- 상태는 탭 라벨 좌측 아이콘 슬롯에 표시하며 별도 목록 화면을 두지 않는다. 여러 Surface 탭을 동시에 열어둔 경우에도 탭 바만 훑으면 진행 상황을 알 수 있다.
- `failed` 탭 hover 시 Tooltip으로 실패 요약 1줄을 보여준다(전문은 노출하지 않음, C-5).

#### 탭 바 / pane 본문 드롭 타깃 분리 (R-10, AC-14 결함 수정)
v4.0까지 `SurfacePane`은 탭 바를 포함한 pane 전체를 단일 드롭 타깃으로 썼고, `computeEdge`가 좌표 비율(`y<0.25`→상단 분할 등)로만 판정했다. 탭 바가 pane 최상단(`y≈0.03`)에 있어 탭 옆에 놓아도 항상 `y<0.25`에 걸려 "상단 분할"로 처리되고, 같은 pane 내 탭 재배치(center 판정)에는 도달할 수 없었다. 이는 확정된 AC-14("split된 pane 사이에서 탭을 이동할 수 있다")를 온전히 만족하지 못하는 결함이며 새 AC를 만들지 않고 아래로 해결한다.

- **탭 바(`SurfaceTabBar`-local)를 pane 본문과 별개의 드롭 타깃으로 분리**한다. 탭 바 자체가 `onDragOver`/`onDrop`을 갖는다.
- 탭 바 위 드롭: 드롭 x좌표와 각 탭 요소의 중심점을 비교해 **삽입 인덱스**를 계산한다. `sourcePaneId === targetPaneId`면 해당 인덱스로 탭 순서를 바꾸고, 다르면 탭을 그 인덱스에 끼워 넣으며 pane을 옮긴다(둘 다 기존 `moveSurfaceTab(tabId, targetPaneId, index)` 어댑터 mutation 그대로 사용, 시그니처에 `index` 인자 추가).
- **pane 본문(`SurfaceBody`, 탭 바 아래 영역)만 `computeEdge` 대상**으로 좁힌다. `computeEdge`에 넘기는 `rect`를 pane 전체가 아니라 탭 바를 제외한 본문 영역의 `DOMRect`로 바꾼다. 본문 위 드롭은 기존과 동일하게 좌/우/상/하 25% 가장자리 판정으로 split한다. `"center"`(같은 pane 편입) 분기는 본문에서 더 이상 쓰지 않는다 — 그 역할은 탭 바 드롭이 대체한다.
- 드롭 힌트: 탭 바는 탭 사이에 얇은 삽입 caret(세로 바)을 표시하고, 본문은 기존 가장자리 하이라이트 오버레이를 유지해 두 영역이 시각적으로도 구분된다.

#### 인터랙션
| 이벤트 | 동작 | 결과 |
|---|---|---|
| `+` → 항목 선택 | 새 SurfacePane 탭 생성(`idle`) | 활성 pane에 추가, 포커스 이동 |
| 탭 드래그 → **탭 바**에 드롭 | 드롭 x좌표로 삽입 인덱스 계산 | 같은 pane이면 탭 순서 변경, 다른 pane이면 해당 인덱스로 탭 편입(R-10) |
| 탭 드래그 → **pane 본문**(가장자리 25%)에 드롭 | split 미리보기 오버레이 표시 후 드롭 | 새 pane 생성(react-resizable-panels 재귀) |
| 탭 닫기(X) | 동적 탭 제거 | pane에 남은 탭 0개면 pane 제거·인접 pane 확장 |
| split handle 드래그 | pane 크기 조정 | 비율 저장(PersistedUI) |
| 세션에 메시지/명령 전송 | mock 타이머로 `running` 진행 | 완료/실패 시 탭 상태 전환, hover 요약 갱신 |

#### Empty/loading/error states
- Surface 없음(모든 동적 탭 닫힘): pane이 완전히 사라지고 SCR-001 빈 상태로 복귀.
- LLM 에이전트 CLI 미연결: `Runtime not connected` 안내 + Agent 설정으로 이동 링크. 탭 상태는 `idle` 고정.

### 4.5 Files/Changes 사이드바 (SCR-006)
- **유형**: monitor/crud
- **경로**: `/workbench/:projectId/:taskId?rail=files|changes`
- **진입점**: SCR-001 우측 사이드바 탭

#### 레이아웃
```text
┌ FILES  CHANGES        [»]──────────┐   ┌ FILES  CHANGES        [»]──────────┐
│ Repo [backend        ▾](Pug 6개일 때만)│  │ Repo [backend        ▾]            │
│ [+ 새 파일] [+ 새 폴더]            │   │ 변경 사항 2                        │
│ v src/                        [M] │   │  dashboard/frontend        (1)     │
│   v workbench/            [3][M] │   │   M WorkbenchApp.tsx  +12 -3        │
│     📄 types.ts               [U] │   │  tasks/115-…                (1)     │
│     📄 mock-adapter.ts        [M] │   │   M wireframe.md      +80 -6        │
│     📄 WorkbenchApp.tsx  (우클릭:  │   │ 추적되지 않은 파일 1                │
│                            삭제)  │   │  docs/proposals             (1)     │
│   > components/                   │   │   U new-file.md       +40           │
│ node_modules/          *[⊘]* (이탤릭)│   │ [파일 클릭 → Diff Surface 탭 열기]  │
│                                    │   │ [커밋 메시지............] [커밋 mock]│
└────────────────────────────────────┘   └─────────────────────────────────────┘
   ↔ 좌우 리사이즈(전체 rail 폭), [»]로 rail 전체 접기      ↔ 동일 rail 폭 공유
   (v/>=폴더 셰브론, [M]수정/[U]미추적/[⊘]무시, 그룹 헤더 건수 배지, +n -m diff 통계)
   (Repo 셀렉트는 선택 Project의 `repositoryComponentIds.length > 1`일 때만 표시된다. AW-AC-5, 추가문서 대체표 3)
```

#### Component hierarchy
```text
RightRail(RailTabs, RailCollapseToggle, RepoScopeSelect[repositoryComponentIds.length>1일 때만, v6.0])
├─ FilesTab(FileTreeToolbar(NewFileButton, NewFolderButton), FileTree(FileTreeRow*(Chevron, KindIcon, Label, GitStatusBadge, DeleteButton), FileTree재귀-형제))
└─ ChangesTab(ChangeGroupList(ChangeGroup*(GroupHeader+CountBadge, ChangeRow*(StatusBadge, Path, DiffStatLabel))), CommitComposer)
```

#### 구성 요소
| 영역 | UI 요소 | shadcn 컴포넌트 | 데이터/설명 |
|---|---|---|---|
| repo scope | 현재 대상 repo 선택 | Select | **v6.0 신규**. Project의 Repository Component가 2개 이상이면 표시하고, 1개 이하면 숨긴다. 선택값이 Files/Changes 트리·목록 범위를 결정한다(AW-AC-5, 추가문서 대체표 3) |
| Files | 셰브론 접기/펼침, 폴더·파일 아이콘, git 상태 배지, ignored 이탤릭, 추가/삭제, rail 접기 | ScrollArea, Button, Input(rename), AlertDialog(삭제 확인) | mock 파일 트리, 실제 파일시스템 미반영(`Not connected`). R-6 구조 수정 대상 |
| Changes | 디렉터리별 그룹(건수 배지) + `변경 사항 N`/`추적되지 않은 파일 N` 2섹션, 파일별 `+n -m`, 커밋 입력 | ScrollArea, Badge, Textarea, Button | mock git status·diff 통계, 커밋은 `Simulated`. 결과 검토의 최종 위치(C-10) |

#### 기능 및 인터랙션
| 이벤트 | 동작 | 결과 |
|---|---|---|
| Repo 셀렉트 변경(v6.0) | activeRepositoryComponentId 갱신 | Files 트리·Changes 목록이 선택 repo 범위로 재로드(AW-AC-5) |
| `+ 새 파일/폴더` | 이름 입력 인라인 | mock 트리에 노드 추가 |
| 폴더 행 셰브론 클릭 | 펼침/접힘 토글 | 자식 `FileTree` 재귀 렌더 여부 전환. 펼침 상태는 `FileNode`가 아니라 `PersistedUI.expandedFolderIds`에 저장되어 재실행 후 복원된다(AC-10) |
| 노드 우클릭 `삭제` | AlertDialog 확인 | mock 트리에서 제거 |
| Changes 그룹 헤더 클릭 | 그룹 펼침/접힘 토글 | 그룹 내 파일 행 표시 전환 |
| Changes 파일 클릭 | 동적 Diff Surface 탭 오픈(신규 또는 기존 포커스) | 본문에서 diff 내용과 `+n -m` 통계 확인 |
| `커밋 mock` | staged 항목을 커밋 mock 기록으로 이동 | 실제 git 미반영 |
| rail 핸들 드래그 | 폭 조정 168~480px | PersistedUI에 폭 저장 |
| rail 접기 아이콘 클릭(R-5) | rail 전체를 `collapsedSize=0`으로 축소 | PersistedUI.railCollapsed 저장, 얇은 펼치기 바로 대체 |

**R-6 구조 수정(중요)**: 현재 `WorkbenchApp.tsx:379-391`의 `FileTree`는 자식 재귀 호출이 행 `<div className="group flex items-center justify-between …">` **안쪽**에 있어 `flex items-center`로 인해 자식 트리가 라벨·삭제버튼과 가로로 나란히 배치되고 계단형 트리가 깨진다. 개정 구조는 행(`FileTreeRow`)과 자식 재귀(`FileTree`)를 **형제**로 렌더한다.
```text
<div className="flex flex-col">           {/* 노드 wrapper: 행 + 자식이 세로로 쌓임 */}
  <FileTreeRow …>                          {/* flex items-center — 셰브론/아이콘/라벨/배지/삭제 한 줄 */}
  {expanded && node.children && (
    <FileTree nodes={node.children} depth={depth + 1} … />   {/* 행의 형제, 아래에 쌓임 */}
  )}
</div>
```

#### Empty/loading/error states
- Files 빈 프로젝트: `파일이 없습니다` + `새 파일 만들기`.
- Changes 변경 없음: 두 섹션 모두 `변경 사항이 없습니다` / `추적되지 않은 파일이 없습니다`.
- 삭제 대상이 존재하지 않을 때(경합): inline error, 목록 새로고침.
- rail 접힘 상태: FilesTab/ChangesTab 콘텐츠 렌더 생략, 얇은 세로 바 + 펼치기 아이콘만 표시.

### 4.6 Project 트리·생성/연결 Dialog (SCR-007, 신규 v6.0)
- **유형**: form (트리는 SCR-001 사이드바에 상주, Dialog는 SCR-007)
- **경로**: `/workbench/:projectId?dialog=new-project|link-project&parent=<projectId?>`
- **진입점**: 설정 화면의 프로젝트 섹션 `Project 생성` 또는 `기존 Project 연결`; parentProjectId는 Dialog에서 선택한다.

#### 4.6a Project 트리 행 규칙
- 행 구성: 셰브론(자식 있을 때만) · Project 이름 · PM 배지 · 진행 TASK 수 배지 · 블로커 점(●있음/○없음).
- 펼치면 자식 Project와 해당 Project의 TASK가 드러나며, TASK를 펼치면 실제 실행 Agent 노드가 드러난다. `oppl`·`opsdd`의 내부 backlog·ACT·단계는 추가하지 않는다(AW-AC-13·15).
- PM은 Project 행에 고정 표시하고, PM·전문 워커의 실제 실행 세션은 TASK 아래(실행 Agent 노드)에 표시한다(추가문서 §화면 요구사항 Project 탐색).
- 펼침 상태는 `PersistedUI.expandedProjectIds`(Project id 집합)로 저장·복원한다(AW-AC-11).

#### 레이아웃 (신규 생성 탭)
```text
┌ Project 추가 ──────────────────────────────────── [X] ┐
│ [신규 생성] [기존 연결]                                │
│ ────────────────────────────────────────────────────  │
│ 부모: (최상위) 또는 "Pug 아래에 추가"                   │
│ 이름*  [____________________]                          │
│ 경로*  [____________________]                          │
│ PM Agent [OPAL PM ▾]                                   │
│ ⓘ 관리 repo·OPAL 구조 생성은 실제로 수행하지 않고        │
│    목업 상태로만 시뮬레이션됩니다.                        │
│                                    [취소] [Project 만들기]│
└────────────────────────────────────────────────────────┘

(기존 연결 탭)
┌ Project 추가 ──────────────────────────────────── [X] ┐
│ [신규 생성] [기존 연결◀]                               │
│ 부모: (최상위) 또는 "Pug 아래에 추가"                   │
│ 경로*  [/Volumes/Data/StoreLinkStudio/blend_______]     │
│ ⓘ 발견됨: .opal/AGENT.md → PM "Blend PM", repo 4개      │
│                                       [취소] [연결하기]  │
└────────────────────────────────────────────────────────┘
```

#### Component hierarchy
```text
NewOrLinkProjectDialog(parentProjectId?)
├─ DialogTabs(NewProjectTab | LinkProjectTab)
├─ NewProjectTab(Label, Input[name], Input[path], Select[pmAgentId], MockBoundaryNote)
└─ LinkProjectTab(Input[path], DiscoveredAgentPreview(PMName, RepoComponentCount), MockBoundaryNote)
```
설정 화면 `ProjectSection`이 동일한 `NewOrLinkProjectDialog`를 열며 신규/연결 모드와 `parentProjectId`를 전달한다. 좌측 `PROJECTS +`는 이 Dialog를 호출하지 않고 TASK 생성에 사용한다.

#### 구성 요소
| 영역 | UI 요소 | shadcn 컴포넌트 | 데이터/설명 |
|---|---|---|---|
| 탭 | 신규 생성 / 기존 연결 | Tabs | 진입 시 기본은 신규 생성 |
| 신규 생성 | 이름·경로·PM 선택, 안내 문구 | Label, Input, Select, Alert | 실제 폴더·Git·`.opal` 생성 없이 mock `Project` 레코드만 추가(제외 범위) |
| 기존 연결 | 경로 입력, 발견된 PM·repo 구성 미리보기 | Input, Card, Badge | `.opal/AGENT.md` 존재를 mock으로 가정하고 PM·Repository Component 후보를 표시 |

#### 기능 및 인터랙션
| 이벤트 | 동작 | 결과 |
|---|---|---|
| 이름/경로 미입력 제출(신규) | client validation | field error, Dialog 유지 |
| 신규 생성 제출 | mock `Project` 추가(`parentProjectId` 지정값 반영) | Project 트리에 즉시 반영, 부모가 있으면 그 아래 펼침 상태로 포커스(AW-AC-1) |
| 경로 입력 후(연결) | mock 발견 결과 조회 | PM·repo 구성 미리보기 갱신, 경로 미존재 mock 처리 시 안내 |
| 연결하기 제출 | mock `Project` 추가(연결) | Project 트리에 반영(AW-AC-2), `repositoryComponentIds` seed 반영 |
| Dialog 바깥/ESC/[X] | 닫기 | 입력값 폐기 |

#### Empty/loading/error states
- 연결 경로에서 `.opal/AGENT.md`를 mock 상 발견하지 못한 경우: `OPAL Project를 찾을 수 없습니다` + 재입력 유도.
- 순환 발생 부모 선택(자기 자신의 하위를 부모로 지정 등): 제출 버튼 비활성 + 사유 Tooltip(§7 순환 금지).

### 4.7 PM Coordination Room (SCR-008, v9.0 재정의)
- **유형**: detail/action Surface
- **경로**: `/workbench/:projectId/:taskId?surface=coordination`
- **진입점**: 조율 TASK 선택 시 기본 탭으로 포커스. 일반 Surface와 동일하게 이동·닫기·split 가능
- **경계**: 사용자 입력은 Main PM에게만 전달한다. Main PM이 Room을 소유하고 Sub PM을 초대·조율한다. Sub PM/Worker Terminal은 Agent가 제어하고 사용자는 관찰만 한다.

#### 레이아웃
```text
┌ PM Coordination Room — 재귀형 프로젝트 관리 ──────────────────────┐
│ Owner: Main PM   Invited: Pug PM ●  Blend PM ●   [PM 초대 요청]    │
│ Workspace: Pug PM ●running  Blend PM ●running                     │
├───────────────────────────────────────────────────────────────────┤
│ User → Main PM  "스토어링크 통합 작업을 진행해줘"                    │
│ Main PM         "Pug·Blend PM을 초대해 역할을 나누겠습니다"          │
│ [초대] Pug PM·Blend PM → Sub PM Workspace Terminal 자동 생성       │
│ Pug PM ↔ Blend PM  "공통 ProjectTree 계약 합의"                    │
│ [배정] Main PM → Pug PM "재귀 트리 UI"                             │
├───────────────────────────────────────────────────────────────────┤
│ Main PM에게 지시 [____________________________________] [지시 전송] │
└───────────────────────────────────────────────────────────────────┘

초대 후 Execution Workspace
┌ PM Room ─────────┬ Pug PM Workspace ─────────┐
│ PM 다자 대화      │ 관찰 전용 · PM Agent 실행  │
│                  │ ├ FE Agent Terminal        │
│                  │ └ Test Agent Terminal      │
└──────────────────┴────────────────────────────┘
```

#### Component hierarchy
```text
PmCoordinationRoomSurface
├─ RoomHeader(MainPmOwner, InvitedSubPmChip*, WorkspaceStatus*, InviteRequestButton)
├─ MainPmFinalJudgement(Badge, Text) — Sub PM 결과와 시각적으로 구분(카드 배경/라벨)
├─ SubTaskStatusRollup(StatusDot*, ProjectLabel*) — 하위 TASK 상태 상향 집계
├─ RoomMessageList(UserBubble | PmBubble | SystemEventCard)
└─ MainPmComposer(MessageInput, SendInstructionButton)

SubPmWorkspaceSurface(readOnlyForUser=true)
├─ WorkspaceHeader(SubPm, Status, ObserverBadge)
├─ AgentSessionOutput
└─ WorkerWorkspaceList(WorkerTerminal*)
```

#### 구성 요소
| 영역 | UI 요소 | shadcn 컴포넌트 | 데이터/설명 |
|---|---|---|---|
| 헤더 | Owner Main PM·초대된 Sub PM·Workspace 상태·PM 초대 요청 | Badge, Button, Dialog | `CoordinationRoom` |
| Main PM 판단 | 최종 통합 판단 카드 | Card, Badge | `Task.ownerProjectId`가 Main PM인 TASK에서만 표시, Sub PM 결과 카드와 스타일로 구분(AW-AC-9) |
| 상태 집계 | Project별 하위 TASK 상태 점 | Badge, Tooltip | `coordinationTaskId`로 연결된 하위 TASK들의 상태를 상향 집계 |
| 대화 | User/Main/Sub PM 버블 + 초대·배정·상태·블로커·결정·결과 카드 | ScrollArea, Badge, Separator | `CoordinationEvent[]`; 발신자와 이벤트를 한 흐름에 표시 |
| 입력 | `Main PM에게 지시` 본문 | Input, Button | 대상·유형·Pilot 선택 없음. 항상 User→Main PM `instruction` 기록 |
| PM Workspace | Sub PM 세션 출력·Worker Terminal 목록 | Tabs, ScrollArea, Badge | 초대 시 자동 생성, 사용자 관찰 전용 |

#### 기능 및 인터랙션
| 이벤트 | 동작 | 결과 |
|---|---|---|
| 조율 TASK 행 클릭 | 저장된 `coordination` Surface 포커스 | 기존 split 배치와 함께 표시 |
| 사용자 지시 전송 | User→Main PM `instruction` 추가 | Room 대화에 표시, Sub PM 직접 대상 지정 불가 |
| `PM 초대 요청` | User 요청→Main PM `invitation` 처리 | Room 멤버 추가 + Sub PM Agent 발동 + 관찰 전용 Workspace Terminal 생성 |
| Main PM 배정 | 대상 Project TASK·Environment·Sub PM Workspace 연결 | 상위 TASK에 `coordinationTaskId`로 연결 |
| Sub PM Worker 호출 | `parentAgentId=Sub PM` Worker Terminal 생성 | Sub PM Workspace 및 Project→TASK→Agent 트리에 표시 |
| Agent 노드 클릭 | 연결된 실행 Surface 포커스 | 대상 Project/TASK Workbench로 이동 |

#### Empty/loading/error states
- Room 이벤트 0건: `Main PM에게 첫 지시를 보내세요`.
- 초대된 Sub PM 0명: `Main PM이 아직 PM을 초대하지 않았습니다`.
- Workspace 생성 실패 mock: 초대 카드에 실패 상태와 Main PM 재시도 표시.

## 5. 공통 컴포넌트
| 컴포넌트 | shadcn 기반 | UI kit 상태 | 사용 화면 | 설명 |
|---|---|---|---|---|
| `RuntimeBoundaryBadge` | Badge, Tooltip | 기존(Existing) | 전체 | Actual/Simulated/Not connected를 일관되게 표시 |
| `EntityContext` | Card, Button, Separator | 기존 | SCR-001 | Project(재귀)→TASK→실행 Agent→Surface 관계 표시 |
| `EmptyState` | Card, Button | 기존 | 전체 | 상태 설명과 단일 회복 CTA |
| `MockFailureToggle` | Switch, Tooltip | 기존 | 전체 | 제품 검토용 실패/대기 상태 전환; 개발 환경에서만 표시 |
| `ProjectTree`(신규 조합, v6.0 — `ProjectSelector` 폐기) | Sidebar, ScrollArea, Collapsible | 기존 primitive 조합, 로직 신규 | SCR-001 | 재귀 Project 트리 렌더. 자식은 `ProjectTreeRow` 재귀 |
| `ProjectTreeRow`(신규 조합, v6.0) | Button/div + lucide `ChevronRight`/`ChevronDown`, Badge(PM/TASK 수/블로커) | 기존 primitive 조합, 로직 신규 | SCR-001 | Project 행: 이름·PM·진행 TASK 수·블로커 상태, 셰브론 펼침/접힘, hover 시 하위 추가 `+` |
| `TaskParticipantChip`(신규 조합, v6.0) | Badge(square) | 기존 primitive 조합, 로직 신규 | SCR-001, 008 | TASK 행의 참여 Project 칩(`▢PUG▢`), 조율 TASK는 복수 표시 |
| `SurfaceTabBar`(신규 조합, R-10 갱신) | Tabs 확장 + DropdownMenu + Command | 기존 primitive 조합, 로직 신규 | SCR-001, 005 | 동적 탭만 존재, `+` 메뉴. **v5.0부터 자체 드롭 타깃**(탭 삽입 인덱스 계산)을 가지며 pane 본문의 가장자리 split 드롭 타깃과 분리된다(R-10) |
| `SurfaceTabStatusIndicator`(신규 조합, AC-16) | Badge/spinner(lucide `Loader2` 등 기존 아이콘) + Tooltip | 기존 primitive 조합, 로직 신규 | SCR-001, 005 | 탭 라벨 옆 idle/running/completed/failed 표시. **`RunStatusBadge`·`ActivityTimeline`을 대체** — Run/Activity 화면이 폐기됨에 따라 세션 상태를 탭 자체로 옮긴 것 |
| `SplitPaneHost`(신규 사용) | `resizable.tsx`(react-resizable-panels) | **이미 설치된 기존 의존성** | SCR-005 | 재귀적 split 레이아웃, 신규 npm 설치 없음 |
| `RightRailTabs`(신규 조합) | Tabs, ScrollArea | 기존 요소 조합 | SCR-006 | Files/Changes 2탭 |
| `SidebarCollapseToggle`(신규 조합, R-5) | Button + lucide `PanelLeftClose`/`PanelLeftOpen`(좌), `PanelRightClose`/`PanelRightOpen`(우) | 기존 primitive 조합, 로직 신규 | SCR-001 | `ResizablePanel`의 `collapsible`/`collapsedSize=0`을 트리거, 패널 상단 우측 모서리 배치 |
| `FileTreeRow`(신규 조합, R-6·a) | Button/div + lucide `ChevronRight`/`ChevronDown`(셰브론), `Folder`/`FileText`(아이콘), Badge(git 상태) | 기존 primitive 조합, 로직 신규 | SCR-001, 006 | 셰브론 접기/펼침, 아이콘, 우측 정렬 `M`/`U`/`⊘` 배지, ignored 이탤릭. `FileTree` 재귀는 이 행의 형제로 렌더(R-6 구조 수정) |
| `ChangeGroupList`(신규 조합, c·d) | Card/div + Badge(건수), 기존 텍스트 스타일(diff 통계) | 기존 primitive 조합, 로직 신규 | SCR-006 | 디렉터리별 그룹 + 건수 배지, `변경 사항 N`/`추적되지 않은 파일 N` 2섹션, 파일별 `+n -m` |
| `SidebarBottomBar`(신규 조합, R-7) | Button + lucide `Settings` | 기존 primitive 조합, 로직 신규 | SCR-001 | 좌측 사이드바 최하단 고정 바, 설정 아이콘 1개만 배치. 좌측 패널 접힘과 함께 숨겨짐 |
| `SettingsDialog`(신규 조합, R-8) | Dialog(large) + `SettingsNav`(Button 목록) + `SettingsPanel` | 기존 primitive 조합, 로직 신규 | SCR-003 | Agent·외관·Workbench·프로젝트·목업 5섹션을 좌측 목록 + 우측 패널로 표시. v4.0 `AgentCatalogSheet`를 Agent 섹션으로 흡수(§4.3). **v6.0**: 프로젝트 섹션은 사후 관리 전용, 생성·연결 버튼 없음 |
| `NewOrLinkProjectDialog`(신규 조합, v6.0) | Dialog + Tabs + Label/Input/Select + Alert | 기존 primitive 조합, 로직 신규 | SCR-007 | 신규 생성/기존 연결 2탭, `parentProjectId` prop으로 최상위·하위 추가 겸용(§4.6) |
| `RepoScopeSelect`(신규 조합, v6.0) | Select | 기존 요소 조합 | SCR-006 | Repository Component가 2개 이상인 Project에서만 표시, Files/Changes 범위 선택(AW-AC-5) |
| `PmCoordinationRoomSurface`(v9.0) | Card, Badge, ScrollArea, Dialog, Input, Button | 기존 primitive 조합, 로직 신규 | SCR-008 | 사용자→Main PM 단일 입력, Sub PM 초대, 다자 PM 대화·구조화 이벤트. 일반 Surface와 동일하게 탭·split 지원 |

> 폐기: `RunStatusBadge`, `ActivityTimeline`(Run 없음, Activity Log 없음 — C-10), `AgentCatalogSheet`(Sheet 컨테이너, 로직은 `SettingsDialog`의 Agent 섹션으로 이동 — R-8), `ProjectSelector`(평면 Select, `ProjectTree`로 전면 교체 — v6.0, 추가문서 대체표 1). 대체물은 `SurfaceTabStatusIndicator`(탭 상태)·`SettingsDialog`(Agent 설정)·`ProjectTree`(Project 탐색) 세 항목이다.

## 6. shadcn 설치 목록
| 구분 | 컴포넌트 | 사용 화면 | 조치 |
|---|---|---|---|
| 기존(Existing) | sidebar, tabs, scroll-area, separator | 전체 | 현재 UI kit 재사용 |
| 기존 | button, badge, card, tooltip, alert, skeleton | 전체 | 현재 UI kit 재사용 |
| 기존 | dialog, alert-dialog, label, input, textarea, select | SCR-001, 002, 003, 006 | 현재 UI kit 재사용 |
| 기존 | sheet, avatar, command, dropdown-menu | SCR-001, 003 | 현재 UI kit 재사용 |
| **기존, 이번에 처음 사용** | **resizable**(react-resizable-panels 래퍼, `components/ui/resizable.tsx`에 이미 존재) | SCR-001(3열 리사이즈), SCR-005(split) | 신규 설치 아님 — 기존 파일 확인 완료(`dashboard/frontend/src/components/ui/resizable.tsx`) |
| 신규(New) | 없음 | - | 탭 드래그·split 드롭 판정은 HTML5 native drag events로 직접 구현한다(아래 확정 참조). 추가 설치 없음 |

**판단 근거(설치 전 확인)**: `dashboard/frontend/package.json`과 `components/ui/`를 확인한 결과 `react-resizable-panels`가 shadcn `resizable` 컴포넌트로 이미 wrap되어 있어 pane 리사이즈에 그대로 쓴다.

**사이드바 접기(R-5)**: `react-resizable-panels`는 `ResizablePanel`에 `collapsible`/`collapsedSize`/`onCollapse`/`onExpand` prop을 이미 제공한다(현재 설치 버전에서 확인). 신규 설치 없이 좌·우 `ResizablePanel`에 `collapsible collapsedSize={0} minSize={...}`를 지정하고 접기/펼치기 아이콘 클릭 시 `panelRef.current.collapse()/.expand()`를 호출하는 방식으로 구현한다.

**트리·배지 아이콘(a·R-6)**: `dashboard/frontend/package.json`에 `lucide-react`가 이미 설치돼 있고 `WorkbenchApp.tsx`가 이미 그 아이콘들(`Bot`, `Boxes`, `ChevronRight` 등)을 쓰고 있다. 셰브론(`ChevronRight`/`ChevronDown`), 폴더/파일(`Folder`/`FileText`), 접기 토글(`PanelLeftClose`/`PanelLeftOpen`/`PanelRightClose`/`PanelRightOpen`) 모두 `lucide-react`에 존재하는 기존 아이콘이다. 신규 아이콘 라이브러리 설치는 필요 없다.

**설정 화면(R-7·R-8)**: `dialog.tsx`(SCR-002 Task 생성에서 이미 사용 중)를 `max-w-4xl h-[75vh]` 크기로 재사용하고 내부를 좌측 섹션 목록(`Button` ghost 목록) + 우측 `ScrollArea` 패널로 구성한다. 신규 shadcn 컴포넌트 설치 없음. 설정 아이콘은 `lucide-react`의 `Settings`(이미 설치)를 쓴다.

**탭 드래그·split 구현 방식: B(HTML5 native drag events) 확정** — 캡틴 승인(2026-09-11).

`draggable` 속성과 `dragstart`/`dragover`/`drop` 이벤트로 탭 드래그와 pane 가장자리 드롭존 판정을 직접 구현한다. 신규 npm 설치는 없다. pane 폭·높이 조절만 기존 `resizable`(react-resizable-panels 래퍼)을 사용한다.

근거 두 가지.

1. **참조 대상인 Orca가 같은 방식을 쓴다.** `/Applications/Orca.app/Contents/Resources/app.asar`를 실측한 결과 타일링·드래그 라이브러리가 하나도 없다(`dockview`·`react-mosaic`·`flexlayout`·`golden-layout`·`rc-dock`·`allotment`·`splitpanes`·`react-resizable-panels`·`dnd-kit` 전부 0건). 대신 `dragstart`·`onDragOver`·`PointerEvent`가 검출되며, split 모델 식별자로 `splitDirection`(69회)·`splitRight`·`splitDown`·`splitPane`·`tabGroup`·`paneId`·`leafId`·`workspaceLayout`이 관측된다. 본 문서 §7의 `SplitDirection`·`SplitNode`·`SurfaceLayout` 모델과 같은 구조다.
2. **`@dnd-kit`의 이점이 이 맥락에서 성립하지 않는다.** dnd-kit의 우위는 접근성과 터치 대응인데, 데스크톱 Electron 전용 앱이라 터치 입력이 없다. 목업 단계에서는 의존성과 코드가 적은 쪽이 낫다.

`@dnd-kit/core`는 이미 설치되어 있으나 이번 범위에서 사용하지 않는다. 신규 설치 명령: **없음**.

**v7.0 소요 확인**: Project/TASK/Agent 트리와 `PmCoordinationSurface`는 기존 `ScrollArea`·`Badge`·`Button`·`Select`·`Input`·`Card`를 조합한다. 신규 shadcn 및 npm 의존성은 없다.

## 7. Mock data contract와 상태 규칙
```ts
type Boundary = 'actual'|'simulated'|'not_connected';
type TaskStatus = 'todo'|'in_progress'|'review'|'done';
type SplitDirection = 'horizontal'|'vertical';
type SurfaceKind = 'coordination'|'terminal'|'browser'|'markdown'|'mobile_emulator'|'agent_cli'|'diff';
type SessionStatus = 'idle'|'running'|'completed'|'failed'; // AC-16 — 탭 자체 상태 표시

// v6.0: Project는 재귀 트리 노드다(추가문서 §목업 데이터 계약). 단순/복합 유형은 parentProjectId·자식 존재 여부로 파생하며 별도 필드로 저장하지 않는다. 계층은 순환을 허용하지 않는다.
interface Project {
  id:string; name:string; repositoryPath:string;
  parentProjectId?:string;            // 신규(v6.0) — 없으면 최상위. 정본 부모 하나만 가짐(다중 부모 없음)
  pmAgentId:string;                   // 신규(v6.0) — Project당 PM Agent 1명
  repositoryComponentIds:string[];    // 신규(v6.0) — 관리 대상 Repository Component
}
// 신규(v6.0): Repository Component 는 Project가 관리하는 실제 repo/monorepo 영역이다. 독립 PM·TASK·의사결정을 갖지 않는다.
interface RepositoryComponent { id:string; projectId:string; name:string; path:string; kind:'repo'|'monorepo-area' }
type Pilot = 'opp'|'opd'|'opds'|'opdw'|'oppl'|'opsdd';
interface Task {
  id:string; projectId:string; title:string; description:string; status:TaskStatus; leadAgentId:string; environmentId:string;
  ownerProjectId:string;              // 신규(v6.0) — TASK를 소유하는 단일 Project
  pilot:Pilot;
  participantProjectIds:string[];     // v9.0 — Main PM이 Room에 초대한 Project 집합. 사용자 Task 생성 입력에는 노출하지 않음
  coordinationTaskId?:string;         // 신규(v6.0) — 이 TASK가 상위 조율 TASK에 속할 때 그 TASK id
}
interface Environment { id:string; taskId:string; worktreeLabel:string; terminalSessionIds:string[]; browserSessionId?:string; boundary:Boundary }
// 신규(v6.0): Project PM 수준 조율 이벤트. Agent Run 원본·도구 로그·검증 상세·승인 조작 필드는 두지 않는다(추가문서 113행).
type CoordinationEventType = 'instruction'|'invitation'|'assignment'|'status'|'coordination'|'blocker'|'decision'|'result'|'worker_spawn';
interface CoordinationEvent { id:string; taskId:string; projectId:string; pmAgentId:string; type:CoordinationEventType; summary:string; timestamp:string }
interface CoordinationRoom { id:string; taskId:string; mainProjectId:string; mainPmAgentId:string; invitedProjectIds:string[] }
interface AgentDefinition { id:string; name:string; role:string; source:'project'|'framework'|'user'; path:string; status:'ready'|'idle'|'offline' }
interface RuntimeBinding { agentId:string; runtime:string; model:string; mode:string; permission:'ask'|'allow'; boundary:'simulated' }

// R-3: 동적 Surface 탭 + split 트리 (Run·Conversation·Activity·Verification·Result 타입은 C-10으로 제거됨)
interface SurfaceTab {
  id:string; taskId:string; kind:SurfaceKind; title:string;
  agentId?:string;                 // kind='agent_cli'일 때 바인딩된 Agent
  parentAgentId?:string;           // v9.0 — Worker를 호출한 Sub PM Agent
  readOnlyForUser?:boolean;        // v9.0 — PM/Worker Workspace Terminal은 true
  boundary:Boundary;
  closable:true;
  sessionStatus:SessionStatus;     // AC-16 — 탭 라벨의 상태 표시
  failureSummary?:string;          // sessionStatus='failed'일 때 hover 1줄 요약
  messages?: { author:string; body:string }[]; // terminal/agent_cli 세션 로그. coordination은 CoordinationEvent[] 사용
}
type SplitNode =
  | { type:'leaf'; paneId:string; tabIds:string[]; activeTabId:string }
  | { type:'split'; direction:SplitDirection; sizes:number[]; children:SplitNode[] };
interface SurfaceLayout { taskId:string; root:SplitNode }

// 우측 rail
type GitFileStatus = 'modified'|'untracked'|'ignored'|'clean'; // a·R-6 — 트리 행 우측 배지(M/U/⊘, clean은 배지 없음)
interface FileNode {
  id:string; projectId:string; path:string; kind:'file'|'folder'; children?:FileNode[];
  gitStatus:GitFileStatus;   // 신규(a) — 트리 행 우측 배지, ignored는 라벨 이탤릭 렌더 트리거
}
// 폴더 펼침 상태는 FileNode에 두지 않고 PersistedUI.expandedFolderIds(집합)로만 관리한다 — 데이터(seed)와 UI 상태를 분리해 동기화 이슈를 없앤다.
interface ChangeEntry {
  id:string; projectId:string; path:string; status:'staged'|'unstaged'; diffPreview:string;
  linesAdded:number;         // 신규(d) — `+n` 표시
  linesRemoved:number;       // 신규(d) — `-m` 표시. 추가만 있으면 `-0`은 렌더에서 생략(`+n` 단독 표기)
}

// R-8: 화면 목업 데이터(PersistedUI)와 분리된 사용자 환경설정. localStorage 키도 별도(아래 참조) —
// 근거: PersistedUI는 "지금 열려 있는 화면 상태의 스냅샷"(activeProjectId·탭 배치·rail 폭 등)이고,
// Settings는 "앞으로의 기본값/환경"(테마, 새 항목 기본값)이라 갱신 빈도·소유 주체(사용자 의도 vs 조작 결과)가 다르다.
// 섞으면 "목업 상태 초기화"가 테마 같은 사용자 선호까지 되돌리는 부작용이 생겨 별도 타입으로 둔다.
type ThemeMode = 'system'|'light'|'dark';
type FontScale = 'sm'|'md'|'lg';
interface Settings {
  version:1;
  theme:ThemeMode;
  fontScale:FontScale;
  defaultNewSurfaceKind:SurfaceKind;   // Workbench §4.3 — 신규 Task 진입 시 `+` 기본 선택 항목(자동 오픈은 아님, §4.1 기능3 유지)
  sidebarCollapsedDefault:boolean;     // 신규 Task/Project 최초 진입 시 기본 접힘값(기존 PersistedUI.sidebarCollapsed는 그대로 마지막 상태 유지)
  railCollapsedDefault:boolean;
  treeIndentPx:number;                 // 12~16
}

interface PersistedUI {
  version:4;
  activeProjectId:string;
  taskStatusFilter?:TaskStatus;
  taskPilotFilter?:Pilot;
  taskAssigneeFilter?:string;
  taskParticipantProjectFilter?:string;
  taskSearch:string;
  taskId?:string;
  surfaceLayoutByTask: Record<string, SurfaceLayout>;
  railTab: 'files'|'changes';
  railWidthPx: number;
  sidebarWidthPx: number;
  sidebarCollapsed: boolean; // 좌측 Project/TASK/Agent 패널 접힘 상태
  railCollapsed: boolean;    // 신규(R-5) — 우측 Files/Changes 패널 접힘 상태
  expandedFolderIds: string[]; // 신규(a) — 트리 셰브론 펼침 상태 복원(AC-10 확장), 폴더 FileNode.id 집합
  expandedProjectIds: string[]; // 신규(v6.0) — Project 트리 셰브론 펼침 상태 복원(AW-AC-11), Project.id 집합
  activeRepositoryComponentId?: string; // 신규(v6.0) — Repository Component가 여럿인 Project의 현재 Files/Changes 대상(AW-AC-5)
}
```

- 단일 `MockWorkbenchAdapter`가 Project/TASK/Surface/Files/Changes mutation을 제공한다. v7.0에서 TaskGroup mutation을 제거하고 `createTask(pilot, leadAgent, participants)`와 `sendCoordinationMessage`, `assignSubProjectTask`를 추가한다. 배정 mutation은 하위 TASK·Environment·PM Agent Surface·상위 assignment 이벤트를 함께 생성한다.
- mock timer는 `sendSurfaceMessage` 이후 대상 `SurfaceTab.sessionStatus`를 `running→completed`로 진행하며 failure toggle에서 `running→failed`로 전이시킨다. 이 상태 전이가 Run 상태 추적을 대체한다(C-10).
- `localStorage['opal.workbench.mock.v4']`에는 UI 상태뿐 아니라 `Project`/`RepositoryComponent`/`Task`/`CoordinationEvent`/`Environment`/`SurfaceTab`과 repo별 Files/Changes 스냅샷을 함께 저장한다. 생성 TASK가 복원될 때 Environment나 실행 Surface가 유실되지 않아야 한다.
- **`PersistedUI.version` 승격 여부(v6.0 판단)**: **승격하지 않는다, `version:4` 유지.** v5.0에서도 `sidebarCollapsed`·`railCollapsed`·`expandedFolderIds`를 동일한 `version:4` 아래 추가 필드로 도입한 선례를 따른다 — 이 목업의 버전 필드는 "저장 포맷이 이전 키(`v1`~`v3`)와 호환되지 않아 seed로 재시작해야 하는 파괴적 변경"에만 쓰고, 필드 추가처럼 비파괴적 확장에는 쓰지 않는다는 기존 관례를 유지한다. `expandedProjectIds`/`activeRepositoryComponentId` 부재는 로드 시 빈 배열/undefined로 안전하게 채워진다.
- **신규**: `localStorage['opal.workbench.settings.v1']`에 `Settings`를 별도 저장한다(R-8, 위 타입 주석의 분리 근거 참조). `MockSection`의 `상태 초기화`(R-8)는 `opal.workbench.mock.v4`와 `opal.workbench.settings.v1` **두 키를 모두 삭제**한 뒤 seed로 재부팅한다 — 목업 상태만이 아니라 환경설정도 "처음 상태"로 돌리는 것이 검토자 기대에 맞다는 판단. seed 복귀 시 Pug·Blend·MAMS 대표 구조(§4.6 실측 seed)도 초기 상태로 되돌아간다.
- `SplitNode` 트리는 leaf(pane)와 split(방향+비율+자식) 재귀 구조이며, pane의 `tabIds`가 비면 부모 split에서 해당 leaf를 제거하고 형제가 공간을 흡수한다.
- 터미널/에이전트 세션의 `messages`는 최근 N개(예: 50)만 유지해 렌더링한다(C-5) — 원본 전문은 목업 범위에서 별도로 저장하지 않는다.
- Project 계층은 순환을 허용하지 않는다. `updateProjectParent`/`createProject`는 지정하려는 부모가 자기 자신이거나 자신의 자손이면 mutation을 거부한다(§4.6 Empty/error states).

### 7.1 대표 seed 데이터 (v7.0)
Project 트리의 seed는 실측 구조를 그대로 반영한다(캡틴 지시 원문, §9 근거 참조).

| Project | 부모 | 경로 | PM | Repository Component |
|---|---|---|---|---|
| StoreLinkStudio | (최상위) | (가상, 실 경로 없음 — Main PM 조율용 상위 Project) | Main PM | 없음(자식이 Component 소유) |
| Pug | StoreLinkStudio | `/Volumes/Data/StoreLinkStudio/pug` | Pug PM | `app_android`·`app_ios`·`backend`·`frontend`·`frontend_admin`·`frontend_app` (kind=`repo` ×6) |
| Blend | StoreLinkStudio | `/Volumes/Data/StoreLinkStudio/blend` | Blend PM | `backend`·`batch`·`frontend_admin`·`frontend_monitor` (kind=`repo` ×4) |
| MAMS | StoreLinkStudio | `/Volumes/Data/StoreLinkStudio/mams` | MAMS PM | `backend`·`docker`·`frontend`·`frontend_test`·`frontend_wireframe` (kind=`monorepo-area` ×5) |

조율 TASK `coord-storelinkstudio-hierarchy`는 `coordination` 기본 Surface와 Pug·Blend·MAMS 연결 TASK를 가지며 §4.7 대화·배정 흐름의 seed다.

## 8. Acceptance criteria traceability
| AC | 화면/상태 | 구현·검토 지점 |
|---|---|---|
| AC-1 | SCR-001 | Electron 창에서 React 3열 Shell과 Actual/Mock 배지 표시 |
| AC-2 | SCR-001, 002 | 재귀 Project→진행 TASK→Agent 트리에서 문맥을 전환하고 완료 TASK가 자동으로 숨겨지는 것을 확인 |
| AC-3 | SCR-002→001 | Dialog 생성, DnD 상태 이동, 카드로 Workbench 진입 |
| AC-4 | SCR-003 (Agent 섹션) | 프레임워크 제공 Agent·user Agent와 Definition/Binding 분리, 상태 확인·목업 설정 변경. **진입 경로가 좌측 사이드바 설정 아이콘 → 설정 화면으로 변경**(R-7·R-9, §10 TASK.md 개정 제안 참조) |
| AC-5 | SCR-001, 005 | 본문에서 Terminal 또는 LLM 에이전트 Surface 탭을 열어 세션을 발동하고 대화를 주고받는 흐름 시뮬레이션 |
| AC-6 | SCR-005 | Terminal·Browser·Markdown·모바일 에뮬레이터·LLM 에이전트 Surface 탭 추가(`+`)·닫기·전환 |
| AC-10 | SCR-001 | 선택 Project·TASK·Surface split·트리/폴더 펼침·repo 범위와 생성된 실행 환경을 복원 |
| AC-12 | SCR-001→002→005→008 | Project→TASK→Agent→Surface 흐름과 PM 대화→Sub PM 배정→하위 TASK 생성→결과 상향 흐름 |
| AC-13 | 전체 | 변경 프런트엔드 lint·typecheck·build 통과와 생성→Surface 오픈→세션 상태 전이→git 검토 핵심 흐름 테스트, split·drag·rail 리사이즈 회귀 테스트 포함 |
| AC-14 | SCR-005 | 동적 Surface 탭을 드래그해 pane 본문 가장자리에 드롭하면 split, **탭 바에 드롭하면 같은 pane 내 순서 변경 또는 다른 pane으로 편입**(v5.0: 탭 바/본문 드롭 타깃 분리로 결함 수정, R-10) |
| AC-15 | SCR-001, SCR-006 | Files 추가/삭제, Changes 스테이징/커밋 mock 동작, rail 폭 드래그 조정, **좌·우 사이드바 접기/펼치기(R-5)**. **v6.0(추가문서 대체표 3)**: Repository Component가 여럿인 Project는 `RepoScopeSelect`로 현재 repo를 먼저 구분한 뒤 선택 repo 범위의 Files/Changes를 표시 |
| AC-16 | SCR-005 | Surface 탭 라벨의 idle/running/completed/failed 상태 표시(스피너·점·배지), failed hover 요약 |
| AC-17 | SCR-006 | Files 트리가 셰브론 펼침/접힘·폴더/파일 아이콘·우측 git 상태 배지(`M`/`U`/`⊘`)·ignored 이탤릭으로 렌더되고, 자식 트리가 행의 형제로 올바르게 계단형 배치된다(R-6·a) |
| AC-18 | SCR-006 | Changes가 디렉터리별 그룹(건수 배지)과 `변경 사항 N`/`추적되지 않은 파일 N` 2섹션으로 표시되고, 파일별 `+n -m` diff 통계를 확인할 수 있다(c·d) |
| **AC-19(신규)** | SCR-001, SCR-003 | 사용자가 설정 화면에서 Agent·외관·Workbench·프로젝트·목업 5섹션을 확인하고 설정·초기화를 수행한다. **v8.0**: 프로젝트 섹션은 최상위/하위 Project 생성·연결과 사후 관리를 함께 담당한다 |

### AW-AC 추적표 (추가문서 27~49행, 별도 네임스페이스)
| AW-AC | 화면/상태 | 구현·검토 지점 |
|---|---|---|
| AW-AC-1 | SCR-003, SCR-007 | 설정의 프로젝트 섹션에서 최상위 Project를 만들고 Project 트리에서 확인 |
| AW-AC-2 | SCR-003, SCR-007 | 설정에서 기존 OPAL Project를 최상위 또는 선택 Project의 자식으로 연결 |
| AW-AC-3 | SCR-001 (§4.6a) | 복합 Project 안에 복합 Project를 중첩(StoreLinkStudio→Pug/Blend/MAMS)하고 재귀 트리로 펼쳐 탐색 |
| AW-AC-4 | SCR-001 (§4.6a) | 모든 Project 행에 PM 배지가 고정 표시됨 |
| AW-AC-5 | SCR-003, SCR-006 | Component 추가·제거·목록과 선택 repo마다 분리된 Files/Changes 확인 |
| AW-AC-6 | SCR-001, SCR-002 | TASK 생성 시 Pilot을 선택하고 트리·카드에서 구분 |
| AW-AC-7 | SCR-001, SCR-008 | Main PM의 조율 TASK(`participantProjectIds`)가 하위 Project의 수행 TASK(`coordinationTaskId`)와 연결됨 |
| AW-AC-8 | SCR-008 | Coordination Surface의 `coordination` 이벤트로 Sub PM 간 조율 내용이 상위에 요약됨 |
| AW-AC-9 | SCR-008 | `MainPmFinalJudgement` 카드와 개별 `result` 이벤트가 스타일로 구분되어 최종 판단·Sub PM 결과를 분리 확인 |
| AW-AC-10 | SCR-001 (§7.1 seed) | Pug·Blend·MAMS가 StoreLinkStudio Project 아래 연결된 대표 구조를 트리에서 검토 |
| AW-AC-11 | SCR-001 | `PersistedUI.expandedProjectIds`·`activeProjectId`·`taskId`와 생성·연결된 Project 엔티티 스냅샷이 앱 재실행 후 복원(§7 근거) |
| AW-AC-12 | SCR-001, SCR-005, SCR-006 | 기존 Surface 추가/닫기/split/탭 이동(§4.4)과 사이드바 리사이즈(§4.1)가 v6.0 변경 후에도 회귀하지 않음(AC-13 테스트 범위에 포함) |
| AW-AC-13 | SCR-001 (§4.6a) | `oppl`·`opsdd` TASK의 내부 backlog·ACT·단계가 Project 트리에 추가 노드로 나타나지 않고, 해당 TASK의 Workbench 상세에서만 확인됨 |
| AW-AC-14 | SCR-001, SCR-002 | TaskGroup·필터 UI가 없고 완료 TASK가 트리에서 자동으로 숨겨짐 |
| AW-AC-15 | SCR-001 | 펼친 Project 아래 TASK, 펼친 TASK 아래 실행 Agent가 실제 트리 노드로 표시 |
| AW-AC-16 | SCR-005, SCR-008 | Main/Sub PM 대화와 구조화 이벤트가 `coordination` Surface 탭 안에서 동작 |
| AW-AC-17 | SCR-008→001 | Main PM 배정이 대상 Project의 연결 TASK·Environment·PM 실행 Surface를 생성 |
| AW-AC-18 | SCR-001, SCR-005, SCR-008 | Sub PM TASK의 여러 실행 Surface와 Main PM의 요약 대화를 분리해 동시 확인 |
| AW-AC-19 | SCR-001, SCR-002 | `PROJECTS +`로 선택 Project의 TASK 생성 Dialog를 즉시 열기 |
| AW-AC-20 | SCR-003, SCR-007 | 설정의 프로젝트 섹션에서 최상위·하위 Project 생성·연결 수행 |
| AW-AC-21 | SCR-005, SCR-008 | Execution Workspace에 PM Coordination과 여러 Agent Terminal pane 동시 배치 |
| AW-AC-22 | SCR-005 | Agent에 귀속되지 않은 독립 Terminal pane 추가·split·이동·닫기 |
| AW-AC-23 | SCR-008 | 조율 TASK마다 Main PM 소유 PM Coordination Room 하나 생성 |
| AW-AC-24 | SCR-008, SCR-005 | 사용자 입력은 Main PM composer에만 존재하고 Sub PM/Worker Terminal은 관찰 전용 |
| AW-AC-25 | SCR-008→005 | Main PM의 Sub PM 초대 처리로 Room 참여자와 Sub PM Workspace Terminal 동시 생성 |
| AW-AC-26 | SCR-008 | User/Main/Sub PM 발신자별 다자 대화와 구조화 시스템 이벤트를 한 Room에서 확인 |
| AW-AC-27 | SCR-005, SCR-001 | Sub PM의 Worker 호출로 부모 PM에 연결된 관찰 전용 Worker Terminal과 Agent 트리 노드 생성 |

## 9. 미결 배치 요약 (현재 상태)

| # | 쟁점 | 현재 배치 |
|---|---|---|
| 1 | Activity Log 거처 | **해소(폐기)**. C-10으로 Run 위임 추적·Activity Log 자체가 범위 밖이 되어 거처 문제가 소멸했다. |
| 2 | Files·Diff 중복 | 계속 유효. 우측 사이드바 `Files`=프로젝트 전역 트리 네비게이션+추가/삭제, `Changes`=git 상태+커밋 mock. 특정 파일 diff 열람은 `Changes`에서 파일 클릭 시 동적 Diff Surface 탭으로 본문에 연다(§4.5). |
| 3 | Run·Verification·Result 위치 | **해소(폐기)**. C-10으로 위임 추적·검증·결과 승인 UI 자체가 범위 밖이 되었다. 결과 검토는 우측 `Changes`(git)로 대체됐다. |
| 4 | Agent 탭 ↔ Conversation `@mention` 관계 | **해소(통합)**. Conversation 화면과 `@mention` 위임 경로가 폐기되어 이원 구조 자체가 사라졌다. LLM과의 모든 대화는 Terminal 또는 LLM 에이전트 Surface 탭 하나의 채널로 일어난다. |
| 5 | 좌·우 사이드바 완전 접기 범위 | v4에서 확정. `ResizablePanel`의 `collapsible` 특성으로 구현하며 신규 의존성 없음(§6). |
| 6 | 채택하지 않은 항목(b 검색·e 브랜치/PR·f 명령/오버플로·g 좌측 아이콘 레일) | v4 범위 밖. 캡틴이 명시적으로 고르지 않았으므로 이번 문서에 반영하지 않는다. |
| 7 | SCR-003 결번 vs 재정의(R-8) | v5.0에서 **재정의**로 확정. Agent Catalog·Binding 기능이 폐기가 아니라 설정 화면의 한 섹션으로 이동했으므로 번호를 유지해 AC-4 추적성을 지킨다(§4.3 표현 형식 선택 근거). |
| 8 | 설정 항목 저장 위치(R-8) | v5.0에서 확정. `PersistedUI`(화면 상태 스냅샷)와 분리된 별도 `Settings` 타입·별도 localStorage 키(`opal.workbench.settings.v1`)로 관리한다(§7). `PersistedUI.version`은 4로 유지, 승격하지 않는다. |
| 9 | 탭 바/pane 드롭 타깃 분리(R-10) | v5.0에서 확정. AC-14 안에서 결함 수정으로 처리하며 새 AC를 만들지 않는다(§4.4). |
| 10 | MAMS Repository Component 실측값 불일치(v6.0) | 추가문서 43행은 MAMS 영역을 `backend·frontend·batch`로 적었으나, 실측(`/Volumes/Data/StoreLinkStudio/mams/workspace/`)은 `backend·docker·frontend·frontend_test·frontend_wireframe` 5개이고 `batch`는 없다. 본 문서 §7.1 seed는 실측값을 채택했다. 추가문서 자체는 캡틴 소유이므로 수정하지 않는다. |
| 11 | Project 생성/연결 Dialog 진입점(v8.0 갱신) | 설정 화면의 프로젝트 섹션으로 일원화한다. `PROJECTS +`는 선택 Project의 TASK 추가로 사용한다. |
| 12 | `PersistedUI.version` 승격 여부(v6.0) | 승격하지 않음. `expandedProjectIds`·`activeRepositoryComponentId` 필드 추가는 v5.0의 `sidebarCollapsed` 등과 동일하게 비파괴적 확장이라 `version:4`를 유지한다(§7 근거). |
| 13 | 신규 의존성 필요 여부(v6.0) | 불필요. Project 트리·Dialog·조율 타임라인 모두 기존 shadcn primitive(Sidebar/ScrollArea/Collapsible/Dialog/Tabs/Card/Badge)로 구성되며 신규 npm 설치는 없다(§6). |
| 14 | TASK GROUPS·PM 조율 작업공간(v7.0) | TaskGroup 제거, PM Coordination을 정식 Surface로 채택, Main PM 배정이 하위 TASK·실행 Surface를 생성하는 것으로 캡틴 승인(2026-09-12). |
| 15 | 실행 작업공간 UX(v8.0) | 필터 UI 제거·완료 TASK 자동 숨김, `PROJECTS +`의 TASK 빠른 추가 전환, 중앙 명칭을 Execution Workspace로 확정하고 PM Coordination/Agent Terminal/독립 Terminal을 구분한다. Project 생성·연결은 설정으로 이동한다. |
| 16 | PM Coordination Room(v9.0) | 조율 TASK별 Room, 사용자→Main PM 단일 입력, Main PM의 Sub PM 초대, 초대 시 Sub PM Workspace 자동 발동, Sub PM→Worker Terminal 계층, Agent Terminal 관찰 전용을 확정한다. |

## 10. TASK.md 개정 제안 (실제 TASK.md는 미수정 — PM이 캡틴 결정으로 적용)

- **v7.0 적용**: 좌측 탐색은 Project/TASK/Agent이며 TaskGroup은 제거한다. 복원 대상은 선택 Project·TASK·Surface 탭/split·사이드바·트리/폴더 펼침·repo 범위와 생성된 실행 환경이다.
- **신규 AC 채택 여부**: 위 두 문구 확장이 받아들여지면 AC-17(트리 구조·표기)·AC-18(Changes 그룹핑·diff 통계)만 신규로 남는다. TASK.md AC 목록에 AC-17·AC-18을 추가하고 결번 주석("AC-7·8·9·11")은 그대로 유지한다.
- 위 제안은 캡틴 결정 사항이며, 이 문서(wireframe.md)의 §8 추적표는 제안이 그대로 채택된다는 가정 하에 작성했다. 캡틴이 AC-15/AC-10 문구를 확장하지 않기로 하면 AC-17·AC-18 대신 R-5도 별도 AC로 분리해야 한다.

### v5.0 추가 제안 (R-7~R-9)

- **AC-4 문구 개정 제안(필수)**: 현재 "Agent Catalog에 프레임워크 제공 Agent와 사용자 추가 Agent가 표시되며, 각 Agent의 역할·runtime·model·상태를 확인하고 목업 설정을 변경할 수 있다."는 진입 경로를 명시하지 않아 그대로 두어도 문구상 모순은 없다. 다만 헤더 `Agents` 버튼이 폐기되므로(R-9) 진입 경로를 특정하는 서술이 있다면 갱신이 필요하다. 현재 AC-4 원문에는 진입 경로 서술이 없어 **문구 변경 없이도 성립**하지만, 명확화를 원하면 "좌측 사이드바 설정 화면에서"를 추가하는 안을 제안한다.
- **AC-19 신설 제안(필수)**: 설정 화면(외관·Workbench 기본값·프로젝트 목록·목업 상태 초기화)은 AC-4(Agent)·AC-15(사이드바 리사이즈/접기)·AC-10(복원 시나리오) 어느 것으로도 커버되지 않는 새 기능이다. §8에 기재한 AC-19 문구 그대로 TASK.md에 추가하는 안을 제안한다(결번 AC-7·8·9·11은 계속 재사용하지 않는다).
- **AC-14 문구는 변경하지 않는다**: R-10은 기존 AC-14 문구("split된 pane 사이에서 탭을 이동할 수 있다")가 이미 요구한 동작의 구현 결함을 고치는 것이며 요구 범위를 넓히지 않는다.
- 이번 라운드도 캡틴 결정 사항이며, 실제 TASK.md는 미수정 상태로 남겨 PM이 적용하도록 한다.
