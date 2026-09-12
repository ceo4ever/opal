---
template: sdlc-v2
---
# TEST-SCENARIO: OPAL WorkStudio 독립 앱 구축

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: task 126 worktree의 Node.js/npm 환경에서 `workstudio/`와 `dashboard/frontend/`를 독립 패키지로 설치·실행한다. Electron main/preload는 Node 테스트와 syntax check로, renderer는 Vitest + Testing Library/jsdom으로 검증한다.
- 공통 데이터: ① `.opal/AGENT.md`가 있는 OPAL 프로젝트 임시 폴더, ② 마커가 없는 일반 폴더, ③ 같은 realpath를 가리키는 중복 경로, ④ 하위 Project/Repository Component에만 실경로가 있는 StoreLinkStudio 복합 Project seed를 사용한다.
- 대역 사용과 한계: renderer 컴포넌트 테스트에서 `window.opalWorkStudio`와 directory dialog 결과를 대역한다. 이 대역은 Electron 실행 시 preload 노출 여부나 OS native dialog 표시를 대신하지 않으므로, build 후 Electron smoke로 preload 가용성·보안 옵션·앱 타이틀을 별도 확인한다. 실제 PTY, 파일 쓰기, PM Runtime 연동은 범위 밖이다.
- 실행 조건: 자동 테스트와 정적 명령을 우선하고, OS dialog가 필요한 Electron smoke만 로컬 디스플레이 환경에서 수동 확인한다. `구현 전 RED`는 구현자와 다른 테스트 주체가 실패를 기록한 뒤 lock한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-10, C-1, H-1 | `workstudio/`가 독립 package로 준비된다. | WorkStudio의 test, lint, typecheck, build, Electron syntax 명령을 각각 실행하고 생성 번들의 title을 검사한다. | 모든 명령이 exit 0이고 앱·창·문서 title이 `OPAL WorkStudio`로 일치하며 Dashboard 런타임을 import하지 않는다. | npm 정적/자동 검증 + bundle 검사 | 구현 후 |
| S-2 | AC-2, AC-10, C-2, C-8, H-1, H-3 | WorkStudio 이관 기능 테스트가 통과하고 Dashboard cutover가 적용된다. | Dashboard lint, typecheck, test, build를 실행하고 `App.tsx`, package script, source tree에서 Workbench import·`?workbench=1`·중복 구현을 탐색한다. | Dashboard 7개 조회 화면 회귀 검증이 통과하고 WorkStudio 실행 코드와 query flag가 Dashboard에 남지 않는다. | Vitest + npm 정적 명령 + `rg` 잔존 검사 | 구현 후 |
| S-3 | AC-3, AC-4, C-5 | 사이드바에 Project/TASK 추가 트리거와 mocked preload API가 있다. | 두 aria-label을 각각 클릭하고 Project 선택 success/cancel/error를 순서대로 반환한다. | 서로 다른 dialog가 열리며 Project flow는 폴더 선택/생성을 요청하고, cancel은 데이터를 바꾸지 않고, error는 code별 안내를 보여준다. | Testing Library + preload mock | 구현 전 RED |
| S-4 | AC-5, C-3, C-4, C-5, H-2 | OPAL/일반/중복 임시 폴더와 root 밖 symlink·제외 디렉터리·임계 초과 트리가 준비된다. | main IPC에서 폴더를 inspect/register/list하고 renderer에서 Node 직접 접근 없이 typed preload만 호출한다. | OPAL 폴더는 Project와 project-source PM이 함께 등록되고, 일반 폴더는 Project만 등록되며, 중복·root 이탈은 계약된 error code로 거부된다. 제외 디렉터리는 노출되지 않고 임계 초과는 `too_large`로 표시된다. | Node unit/integration test + preload contract test | 구현 전 RED |
| S-5 | AC-6, C-6 | User, Main PM, Pug/Blend/MAMS PM의 일반 메시지와 시스템 이벤트 seed가 있다. | PM Coordination room을 렌더링하고 각 메시지와 시스템 card의 접근 가능 텍스트·class·icon을 검사한다. | 각 일반 메시지가 이름, avatar/initial, 안정적 색상 token, timestamp를 갖고 색상을 제거해도 발화자가 구분된다. 시스템 card는 이벤트 종류, 행위자, 대상을 별도로 보여준다. | Testing Library DOM test | 구현 전 RED |
| S-6 | AC-7, C-7, C-8 | 독립 Terminal tab과 read-only Agent CLI tab이 있다. | 독립 Terminal에 `pwd`를 입력해 Enter를 누르고 이전 명령을 history로 호출한 뒤 Agent CLI를 연다. | shell/cwd label, monospace prompt, `$ pwd`와 deterministic mock output이 scrollback 순서로 추가되고 history가 유지된다. Agent CLI에는 명령 입력 컨트롤이 없다. | Testing Library keyboard interaction | 구현 전 RED |
| S-7 | AC-8, C-4, C-8, H-2 | 실경로가 있는 단순 Project와 success/empty/read_failed/too_large listFiles 응답이 준비된다. | Project를 선택하고 Files rail의 folder를 펼쳐 각 응답을 렌더링한다. | 선택 Project root 하위의 read-only 트리만 lazy render되고 empty/error/too-large 상태가 서로 다른 row로 표시되며 새 파일·삭제 행위는 제공되지 않는다. | Testing Library + IPC mock | 구현 전 RED |
| S-8 | AC-9, C-4 | 실경로가 없고 하위 Project/Repository Component에만 경로가 있는 StoreLinkStudio를 선택한다. | Files rail을 열고 가상 root와 하위 root 노드를 펼친다. | 빈 패널 대신 Pug/Blend/MAMS 또는 등록 repository component가 root로 보이고, 각 실경로 하위 트리만 불러온다. | Testing Library + IPC mock | 구현 전 RED |
| S-9 | AC-1, AC-2, C-1, C-2 | 앱 이관과 Dashboard cutover 후 프로젝 문서가 갱신된다. | `docs/PROJECT.md`와 `docs/ARCHITECTURE.md`의 구성·소유·실행 경계를 구현 트리와 대조한다. | `workstudio/`가 React/TypeScript/Vite/Electron 및 opal-fe-agent 소유로 등록되고 Dashboard는 조회 Console, WorkStudio는 독립 desktop app으로 일치한다. | 문서/파일 구조 정적 검사 | 구현 후 |
