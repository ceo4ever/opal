---
template: sdlc-v2
---
# PLAN: OPAL WorkStudio 독립 앱 구축

> 입력: [TASK.md](TASK.md)

## Approach

`dashboard/frontend/src/workbench/*`의 검증된 목업 자산을 저장소 루트 `workstudio/`의 독립 Electron + React 앱으로 이관하고, Dashboard는 조회 전용 Console로 되돌린다. 첫 실행 그룹은 새 앱 골격과 타입/어댑터 경계를 만들고, 두 번째 실행 그룹은 Project 등록 IPC·PM Coordination·Terminal·Files UX를 기능 단위로 보강한다. 마지막 실행 그룹은 Dashboard 중복 제거, 문서 레지스트리 갱신, WorkStudio와 Dashboard 회귀 검증으로 닫는다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 제품·코드 소유권 | 사용자 대면 명칭은 `OPAL WorkStudio`, 앱 루트는 `workstudio/`다. WorkStudio renderer/main/preload/test/build 설정은 `workstudio/`가 소유하고, Dashboard는 WorkStudio 실행 코드와 query flag를 소유하지 않는다. | TASK C-1, C-2. 현재 Dashboard `App.tsx`는 `?workbench=1`로 Workbench를 import한다(`dashboard/frontend/src/App.tsx:16-20`). `docs/PROJECT.md`는 현재 Console FE만 `dashboard/frontend/`로 등재한다(`docs/PROJECT.md:219-223`). |
| Scaffold 방식 | `workstudio/`는 Dashboard FE의 React/Vite/Tailwind/shadcn 설정과 필요한 UI primitives를 복사·이관해 독립 `package.json` 스크립트(`dev`, `build`, `typecheck`, `lint`, `test`, `desktop`, `electron:syntax`)를 제공한다. 공유 패키지 추출은 이번 범위에서 하지 않는다. | TASK AC-1, AC-2. 기존 FE 스택과 명령은 `dashboard/frontend/package.json:6-15`, 의존성은 `dashboard/frontend/package.json:17-79`에서 확인된다. |
| Electron 보안 경계 | Renderer는 Node.js API를 직접 사용하지 않고 `window.opalWorkStudio` typed preload API만 호출한다. Main은 `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`를 유지하고 preload만 추가한다. | TASK C-3. 현재 Electron main도 격리 옵션을 유지하지만 preload/IPC가 없다(`dashboard/frontend/electron/main.cjs:17-25`). |
| IPC API 계약 | preload는 `project.chooseDirectory()`, `project.inspectDirectory(path)`, `project.listFiles(scope)`, `project.registerFromSelection(selection)`를 노출한다. 응답은 `{ ok: true, value } | { ok: false, code, message }` 형식이며 `code`는 `cancelled`, `invalid_path`, `duplicate_path`, `outside_registered_root`, `read_failed`, `too_large`, `not_supported` 중 하나다. | TASK AC-4, AC-5, AC-8, C-4. Console backend의 프로젝트 식별 기준은 `.opal/AGENT.md` 마커 스캔이다(`docs/ARCHITECTURE.md:329-332`). |
| 파일 접근 정책 | 파일 트리 읽기는 등록된 Project `repositoryPath` 또는 등록된 Repository Component `path` 하위로 제한한다. `node_modules`, `.git`, `.opal/.venv`, `dist`, `build`, 대용량/숨김 캐시 디렉터리는 기본 제외하고, 한 디렉터리의 자식 수가 임계값을 넘으면 `too_large` 노드를 렌더한다. Files는 이번 단계에서 읽기 전용이며 생성/삭제 버튼은 제거하거나 disabled 상태로 남긴다. | TASK C-4, AC-8. 기존 Files UI는 mock tree와 새 파일/삭제 액션을 제공한다(`dashboard/frontend/src/workbench/WorkbenchApp.tsx:1007-1027`, `dashboard/frontend/src/workbench/WorkbenchApp.tsx:1294-1314`). |
| OPAL Project 자동 PM 등록 | 선택 폴더에 `.opal/AGENT.md`가 있으면 `Project`와 `AgentDefinition(source:"project", path:<선택폴더>/.opal/AGENT.md)`을 한 동작으로 추가한다. `.opal/AGENT.md`가 없으면 Project만 등록하고 자동 PM 발견을 표시하지 않는다. 같은 정규화 경로는 중복 등록을 거부한다. | TASK C-5, AC-5. OPAL project-aware 감지는 `.opal/AGENT.md` 존재를 신호로 삼는다(`docs/ARCHITECTURE.md:63-70`). |
| Project 추가와 TASK 추가 분리 | `PROJECTS` 헤더에는 `Project 추가`와 `TASK 추가`가 별도 icon button으로 표시된다. `Project 추가`는 디렉터리 선택/등록 dialog를 열고, `TASK 추가`는 현재 선택 Project의 Task dialog를 연다. | TASK AC-3. 기존 `PROJECTS +`는 TASK 추가 하나뿐이다(`dashboard/frontend/src/workbench/WorkbenchApp.tsx:1197-1200`), task 115 추가 문서는 기존 목업에서 `PROJECTS +`를 TASK 추가로 정의했다(`tasks/115-260910-opdw-데스크톱-워크벤치-인터랙티브-목업/ADDITIONAL-WORK-PROJECT-HIERARCHY.md:92-108`). |
| PM Coordination 표시 | 일반 메시지는 발신자 이름, avatar/initial, PM별 안정 색상 토큰, timestamp를 함께 렌더한다. 시스템 이벤트(`invitation`, `assignment`, `blocker`, `decision`, `result`, `worker_spawn`)는 이벤트 아이콘·행위자·대상 PM을 가진 system card로 유지한다. 색상만으로 발신자를 구분하지 않는다. | TASK C-6, AC-6. 현재 `EventRow`는 `user`와 나머지만 구분한다(`dashboard/frontend/src/workbench/WorkbenchApp.tsx:365-387`). Room 요구는 일반 메시지와 구조화 이벤트 구분을 명시한다(`tasks/115-260910-opdw-데스크톱-워크벤치-인터랙티브-목업/ADDITIONAL-WORK-PROJECT-HIERARCHY.md:121-130`). |
| 독립 Terminal 경계 | `SurfaceKind="terminal"`은 실제 PTY 없이 모노스페이스 scrollback, prompt, cwd/shell label, command history, Enter 실행 mock output을 제공한다. PM/Worker `agent_cli` 관찰 터미널은 read-only로 유지한다. | TASK C-7, AC-7. 기존 터미널은 `author: body` 채팅형 메시지와 Send 버튼을 사용한다(`dashboard/frontend/src/workbench/WorkbenchApp.tsx:787-818`). Task 115은 독립 Terminal과 관찰 전용 Agent Terminal을 구분한다(`tasks/115-260910-opdw-데스크톱-워크벤치-인터랙티브-목업/ADDITIONAL-WORK-PROJECT-HIERARCHY.md:126-140`). |
| 복합 Project Files | 선택 Project가 실 경로 없는 복합 Project이면 빈 Files 대신 직속 하위 Project와 Repository Component를 root node로 만든다. 각 root 아래는 해당 실 경로의 읽기 전용 파일 트리를 lazy load한다. | TASK AC-9. StoreLinkStudio seed는 상위 Project가 실 경로 없는 조율용 Project이고 파일 노드는 자식/컴포넌트에만 존재한다(`dashboard/frontend/src/workbench/mock-adapter.ts:47-73`, `dashboard/frontend/src/workbench/mock-adapter.ts:186-224`). |
| 데이터 모델 변화 | WorkStudio domain type은 `Project.repositoryPath`를 `repositoryPath?: string`으로 완화하고 `Project.kind`는 저장하지 않는다. `AgentDefinition`에는 `avatarLabel?`, `colorToken?`, `projectId?`를 추가한다. `SurfaceTab` terminal message는 `TerminalEntry[]`로 분리하되 agent CLI의 기존 `messages` 호환은 유지한다. File tree에는 `sourceRootId`, `absolutePath?`, `loadState`, `errorCode?`, `readonly: true`를 추가한다. | TASK AC-5~AC-9. 기존 `Project.repositoryPath`는 필수이고 복합 Project도 문자열 placeholder를 쓴다(`dashboard/frontend/src/workbench/types.ts:18-37`, `dashboard/frontend/src/workbench/mock-adapter.ts:50-54`). |
| Dashboard cutover | 새 앱이 build/test 가능한 뒤 Dashboard에서 Workbench import, query flag, Electron Workbench main script, workbench source ownership을 제거한다. Dashboard 7개 조회 화면과 기존 build는 유지한다. | TASK AC-2, C-8. OPAL Console은 읽기 전용 대시보드로 정의된다(`docs/ARCHITECTURE.md:264-332`). |
| 컨벤션 적용 | [MUST] `docs/CONVENTIONS.md` §구현 규칙: "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다 (해당 확장자에 한해)." 신규/이관 TS/TSX/CJS 파일은 code-scan target 판정에 맞춰 @header를 유지한다. | TASK C-8, `docs/CONVENTIONS.md:110-118`. |
| 문서 레지스트리 갱신 | `docs/PROJECT.md`의 프로젝트 구성과 OPAL Console 설명에 `WorkStudio` 구성요소(`workstudio/`, React/TypeScript/Vite/Electron, opal-fe-agent)를 추가하고, `dashboard/`가 조회 Console임을 유지한다. 필요 시 `docs/ARCHITECTURE.md §OPAL Console`에 WorkStudio 분리 사실을 짧게 반영한다. | TASK AC-1, AC-2. 현재 레지스트리는 `Framework`, `Console FE`, `Console BE`만 가진다(`docs/PROJECT.md:215-223`). |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. WorkStudio 앱 골격 이관 | opal-fe-agent | `workstudio/package.json`, `workstudio/index.html`, `workstudio/vite.config.*`, `workstudio/tsconfig*.json`, `workstudio/eslint.config.*`, `workstudio/src/**`, `workstudio/electron/main.cjs` | Dashboard Workbench 목업을 `workstudio/`로 이관하고 앱 title/window title/브랜드를 `OPAL WorkStudio`로 변경한다. React entry는 WorkStudio shell만 렌더하고 Dashboard router/query client를 끌어오지 않는다. 기존 UI primitive와 CSS 중 필요한 파일만 앱 내부로 복사한다. | 없음 | P1 | AC-1, C-1, C-2, C-8 |
| W-2. WorkStudio domain/runtime adapter 계약 정리 | opal-fe-agent | `workstudio/src/workstudio/types.ts`, `workstudio/src/workstudio/mock-adapter.ts`, `workstudio/src/workstudio/*adapter*`, `workstudio/src/workstudio/*.test.ts*` | 타입명을 WorkStudio 기준으로 정리하고 `Project.repositoryPath?`, PM avatar/color, terminal entry, file tree load state, duplicate path guard를 반영한다. localStorage key는 `opal.workstudio.*`로 변경하고 기존 `opal.workbench.*`와 충돌하지 않게 한다. | W-1 | P2 | AC-1, AC-5, AC-6, AC-7, AC-8, AC-9, C-1, C-6, C-7 |
| W-3. Electron preload IPC와 파일 시스템 읽기 구현 | opal-be-agent | `workstudio/electron/main.cjs`, `workstudio/electron/preload.cjs`, `workstudio/src/workstudio/ipc.ts`, `workstudio/src/vite-env.d.ts`, `workstudio/electron/*.test.*` | `dialog.showOpenDialog({ properties:["openDirectory","createDirectory"] })` 기반 폴더 선택, `.opal/AGENT.md` 탐지, 중복/무효 경로 처리, 등록 root 하위 read-only directory listing IPC를 구현한다. path normalize/realpath 검증과 excluded directory/too-large 정책을 main에서 적용한다. | W-1 | P2 | AC-4, AC-5, AC-8, AC-9, C-3, C-4, C-5 |
| W-4. Project 추가와 TASK 추가 UX 분리 | opal-fe-agent | `workstudio/src/workstudio/WorkStudioApp.tsx`, `workstudio/src/workstudio/components/*Project*`, `workstudio/src/workstudio/WorkStudioApp.test.tsx` | `PROJECTS` 헤더에 `FolderPlus` 계열 Project 추가와 `ListPlus`/`Plus` 계열 TASK 추가를 별도 버튼·tooltip·aria-label로 배치한다. Project dialog는 IPC 선택/취소/오류/OPAL PM 발견/중복 등록 상태를 표시하고 성공 시 Project tree와 PM agent를 즉시 갱신한다. | W-2, W-3 | P3 | AC-3, AC-4, AC-5, C-4, C-5 |
| W-5. PM Coordination 발화자 식별 개선 | opal-fe-agent | `workstudio/src/workstudio/WorkStudioApp.tsx`, `workstudio/src/workstudio/mock-adapter.ts`, `workstudio/src/workstudio/WorkStudioApp.test.tsx` | `EventRow`를 speaker-aware component로 분리하고 User/Main PM/Sub PM별 avatar/initial/name/color token을 렌더한다. 시스템 이벤트 카드는 이벤트 유형 icon, 행위자, 대상, timestamp를 분리 표시한다. 색상 없는 환경에서도 이름·이니셜로 구분되는 테스트를 추가한다. | W-2, W-4 | P4 | AC-6, C-6 |
| W-6. 독립 Terminal 셸형 UI | opal-fe-agent | `workstudio/src/workstudio/WorkStudioApp.tsx`, `workstudio/src/workstudio/mock-adapter.ts`, `workstudio/src/workstudio/WorkStudioApp.test.tsx` | `terminal` surface를 monospaced scrollback + prompt + cwd/shell label + command history로 렌더한다. Enter 입력은 `$ <command>`와 deterministic mock output을 순서대로 append하고, read-only `agent_cli`는 기존 관찰 전용 UX를 유지한다. | W-2, W-5 | P5 | AC-7, C-7, C-8 |
| W-7. Files rail 실제/복합 Project 트리 | opal-fe-agent | `workstudio/src/workstudio/WorkStudioApp.tsx`, `workstudio/src/workstudio/mock-adapter.ts`, `workstudio/src/workstudio/WorkStudioApp.test.tsx` | 우측 Files는 선택 Project 기준으로 IPC `listFiles`를 호출한다. 단순 Project는 실제 root tree를 lazy render하고, 복합 Project는 직속 하위 Project/Repository Component를 root node로 표시한다. 미선택/빈 폴더/읽기 실패/too large 상태를 서로 다른 empty/error row로 구분하며 새 파일/삭제 액션은 제거 또는 disabled 처리한다. | W-2, W-3, W-6 | P6 | AC-8, AC-9, C-4, C-8 |
| W-8. Dashboard Workbench 결합 제거 | opal-fe-agent | `dashboard/frontend/src/App.tsx`, `dashboard/frontend/electron/main.cjs`, `dashboard/frontend/src/workbench/**`, `dashboard/frontend/package.json`, `dashboard/frontend/src/**/*.test.ts*` | Dashboard `App.tsx`에서 Workbench import와 `?workbench=1` 분기를 제거한다. Dashboard Electron script가 Workbench title/query를 주입하지 않도록 정리하거나 Console용으로만 유지한다. 이관 후 중복 Workbench 구현이 남지 않게 삭제/참조 제거하고 Dashboard 기존 화면 테스트를 갱신한다. | W-1, W-2, W-4, W-5, W-6, W-7 | P7 | AC-2, C-2, C-8 |
| W-9. 문서 레지스트리와 아키텍처 반영 | opal-task-agent | `docs/PROJECT.md`, `docs/ARCHITECTURE.md` | 프로젝트 구성 표에 `WorkStudio`(`workstudio/`, React/TypeScript/Vite/Electron, opal-fe-agent)를 추가한다. OPAL Console 설명은 조회 Dashboard로 유지하고 WorkStudio가 별도 데스크톱 실행 앱이라는 경계를 짧게 반영한다. | W-1, W-8 | P8 | AC-1, AC-2, C-1, C-2 |
| W-11. Dashboard 기존 lint 결손 최소 정리 | opal-task-agent | `dashboard/frontend/src/components/ui/{badge,button,sidebar,textarea,toggle}.tsx`, `dashboard/frontend/src/hooks/use-mobile.tsx`, `dashboard/frontend/src/pages/brain/BrainPage.tsx`, `dashboard/frontend/src/pages/dashboard/DashboardPage.stats.test.tsx` | 전체 lint의 기존 14건만 동작 변경 없이 정리한다. UI primitive는 WorkStudio의 검증된 동형 수정을 적용하고 BrainPage export 규칙과 test 미사용 변수는 ESLint 지적만 제거한다. 기존 헤더 미등록 파일을 수정할 때는 inline `@header`를 추가한다. code-scan은 `BrainPage.tsx` domain=`brain`, layer=`page`를, `DashboardPage.stats.test.tsx` domain=`dashboard`, layer=`test`를 보고했고 UI/hook은 기존 미등록으로 확인됐다. | W-8 | P9 | AC-2, AC-10, C-8 |
| W-10. WorkStudio/Dashboard 검증 묶음 | opal-test-agent | `workstudio/src/**/*.test.ts*`, `workstudio/electron/*.test.*`, `dashboard/frontend/src/**/*.test.ts*`, `tasks/126-260912-opds-워크스튜디오-독립앱-구축/TEST.md` | RED-first 테스트 시나리오를 확정한 뒤 WorkStudio unit/component/IPC tests, `npm run lint`, `npm run typecheck`, `npm run test`, `npm run build`, `npm run electron:syntax`를 실행한다. Dashboard는 `npm run lint`, `npm run typecheck`, `npm run test`, `npm run build`로 Workbench 제거 회귀를 확인한다. | W-3, W-4, W-5, W-6, W-7, W-8, W-9, W-11 | P10 | AC-1, AC-2, AC-10, C-8 |

## Acceptance criteria traceability

| 완료 기준 | 연결 Work items | RED-first 테스트 시나리오 초안 |
|---|---|---|
| AC-1 | W-1, W-10 | WorkStudio package scripts가 존재하지 않는 상태에서 실패하는 테스트/명령을 먼저 확인한 뒤, 창 title/앱 title/스크립트 실행을 검증한다. |
| AC-2 | W-8, W-9, W-10, W-11 | Dashboard `App.tsx`가 Workbench import 없이 router를 렌더하고 `?workbench=1`이 Workbench를 열지 않음을 regression test로 고정한다. |
| AC-3 | W-4, W-10 | `Project 추가`와 `TASK 추가` aria-label을 각각 조회하고, 클릭 시 서로 다른 dialog가 열리는 component test를 먼저 작성한다. |
| AC-4 | W-3, W-4, W-10 | mocked preload API가 `cancelled`, `invalid_path`, success selection을 반환할 때 state 변경/안내가 계약대로 갈리는 테스트를 작성한다. |
| AC-5 | W-2, W-3, W-4, W-10 | `.opal/AGENT.md`가 있는 mock folder 선택 시 Project와 PM agent가 함께 추가되고 같은 realpath 재등록은 거부되는 테스트를 작성한다. |
| AC-6 | W-5, W-10 | User/Main PM/Pug PM/Blend PM/MAMS PM 메시지가 이름+initial/avatar+색상 class로 구분되고 system event card가 icon/행위자를 갖는 DOM test를 작성한다. |
| AC-7 | W-6, W-10 | 독립 Terminal에서 `pwd` 입력 후 `$ pwd`와 mock output이 순서대로 scrollback에 추가되고 Agent terminal에는 input이 없는 테스트를 작성한다. |
| AC-8 | W-3, W-7, W-10 | 단순 Project 선택 시 IPC file tree 결과가 폴더 펼침/빈 폴더/읽기 실패 상태로 렌더되는 테스트를 작성한다. |
| AC-9 | W-7, W-10 | 실 경로 없는 StoreLinkStudio 선택 시 빈 패널이 아니라 Pug/Blend/MAMS 또는 repo component root가 나타나는 테스트를 작성한다. |
| AC-10 | W-10, W-11 | WorkStudio 전체 명령과 Dashboard 회귀 명령을 TEST 증거로 남기고, IPC/UX 핵심 흐름 실패 시 EXECUTE로 되돌린다. |

## Constraint traceability

| 제약 | 연결 Work items | 계약 |
|---|---|---|
| C-1 | W-1, W-9 | `OPAL WorkStudio`와 `workstudio/` 외 명칭/폴더를 사용자 대면 정식명으로 쓰지 않는다. |
| C-2 | W-1, W-8, W-9 | Dashboard는 WorkStudio 코드를 소유하지 않고, 중복 구현은 제거한다. |
| C-3 | W-3 | Renderer Node 접근 금지, typed preload IPC만 허용한다. |
| C-4 | W-3, W-7 | 등록 root 하위 read-only 파일 탐색만 허용하고 path escape/대용량/숨김 캐시 정책을 main에서 집행한다. |
| C-5 | W-3, W-4 | OPAL Project 자동 PM 등록은 `.opal/AGENT.md` 존재에 한정한다. |
| C-6 | W-5 | 이름+avatar/initial+색상 단서와 system card 구분을 함께 제공한다. |
| C-7 | W-6 | 실제 PTY 없이 shell-like terminal mock으로만 구현한다. |
| C-8 | W-1~W-11 | 기존 Surface/split/tree 회귀를 테스트하고 신규/수정 코드의 @header 규칙을 지킨다. |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. Dashboard UI primitive를 WorkStudio로 복사하면서 import alias/tsconfig가 어긋날 수 있다. | WorkStudio build/typecheck와 Dashboard build가 동시에 실패할 수 있다. | AC-1, AC-2 완료 지연 | W-1에서 alias와 tsconfig를 먼저 고정하고 W-10에서 두 앱 build를 모두 검증한다. |
| H-2. Electron 파일 트리 IPC가 실제 디렉터리 크기·권한·symlink에 따라 느려지거나 root 밖 파일을 노출할 수 있다. | Files rail의 read-only 보안 계약(C-4)이 깨질 수 있다. | 로컬 파일 노출·앱 멈춤 | W-3에서 realpath root containment, 제외 디렉터리, 자식 수 제한, error node 계약을 main process에 둔다. |
| H-3. Workbench 소스를 Dashboard에서 삭제하기 전에 WorkStudio 이관 테스트가 안정화되지 않으면 두 앱 모두 깨질 수 있다. | AC-1/AC-2 동시 실패 | 실행 앱과 조회 앱 모두 회귀 | W-8은 P4로 후행시키고 W-1~W-7의 WorkStudio 테스트 통과 후 제거한다. |

## Release and recovery

- 적용 순서: P1에서 `workstudio/` 앱 골격을 먼저 세우고, P2에서 타입·IPC 계약을 고정한다. P3~P6에서 같은 핵심 UI 파일을 순차 보강하고, P7 Dashboard cutover, P8 문서 갱신, P9 Dashboard lint 결손 정리, P10 검증을 수행한다.
- 검증 범위: WorkStudio는 unit/component/IPC mock과 lint/typecheck/test/build/electron syntax를 확인한다. Dashboard는 Workbench 제거 후 lint/typecheck/test/build 회귀를 확인한다. 실제 PTY, 실제 파일 쓰기, 실제 PM Runtime 호출은 이번 범위 밖이다.
- 실측 경계: 파일 트리 IPC는 등록 root containment와 제외/too-large 정책이 자동 테스트로 확인될 때 통과로 본다. UX는 Testing Library DOM 테스트에서 aria-label, 상태 문구, tree node, scrollback 순서가 확인될 때 통과로 본다.
- 실패 시: P4 전 실패는 `workstudio/` 내부 변경만 되돌려 Dashboard 기존 Workbench 결합을 유지할 수 있다. P4 후 실패는 Dashboard `App.tsx`/Electron main의 Workbench 제거 diff를 우선 되돌리고 WorkStudio 변경은 별도 앱 폴더에 남겨 재작업한다. 커밋·배포는 사용자 승인 전 수행하지 않는다.
