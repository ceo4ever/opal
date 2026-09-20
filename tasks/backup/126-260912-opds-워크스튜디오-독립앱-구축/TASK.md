---
template: sdlc-v2
---
# TASK: OPAL WorkStudio 독립 앱 구축

## Problem

데스크톱 실행 작업공간 목업이 현재 OPAL Console의 `dashboard/frontend/src/workbench/`와 query flag에 결합되어 있어, 조회 중심 Dashboard와 실행·조율 중심 WorkStudio의 제품 경계가 분리되지 않는다 (`dashboard/frontend/src/App.tsx`, `dashboard/frontend/src/workbench/WorkbenchApp.tsx:1095-1345`). 또한 현재 화면은 Project 등록이 설정 안에 숨겨져 있고, PM Coordination 메시지는 User와 그 외 발신자만 구분하며, 독립 Terminal은 채팅형 입력 UI이고, 실 경로가 없는 복합 Project를 선택하면 우측 Files 트리가 비어 보인다 (`dashboard/frontend/src/workbench/WorkbenchApp.tsx:365-387`, `dashboard/frontend/src/workbench/WorkbenchApp.tsx:787-818`, `dashboard/frontend/src/workbench/WorkbenchApp.tsx:1113-1122`).

## Proposed outcome

제품명을 `OPAL WorkStudio`로 확정하고 저장소 루트에 `workstudio/` 독립 데스크톱 앱을 만든다. 기존 Workbench 목업을 Dashboard에서 이관해 Dashboard는 조회 앱으로 유지하고, WorkStudio는 Project 등록·PM 조율·Terminal·Files를 한 실행 작업공간에서 제공한다. 사용자는 좌측에서 기존 폴더를 선택하거나 새 폴더를 만든 뒤 Project로 등록할 수 있고, 기존 OPAL Project이면 `.opal/AGENT.md`를 읽어 PM Agent를 자동 등록한다. PM 대화는 발신자별로 명확히 구분하며, 독립 Terminal은 일반 셸과 유사한 화면을 제공하고, 우측 Files는 좌측에서 선택한 Project의 계층을 표시한다.

## Affected users and systems

- 사용자: 여러 OPAL Project와 PM·Agent 작업을 데스크톱에서 조율하는 1인 개발자.
- 신규 앱: 저장소 루트 `workstudio/`의 React renderer, Electron main/preload, 앱 전용 테스트·빌드 설정.
- 기존 앱: `dashboard/`의 Workbench query 진입점과 Workbench 전용 소스 제거 또는 독립 앱 참조 해제. Dashboard의 기존 7개 조회 화면은 유지한다 (`docs/ARCHITECTURE.md` §OPAL Console).
- 로컬 시스템: 사용자가 명시적으로 선택한 디렉터리, 선택 경로의 `.opal/AGENT.md`, 선택 Project의 읽기 전용 파일 트리.

## Constraints

- C-1: 정식 제품명은 `OPAL WorkStudio`, 루트 앱 폴더는 `workstudio/`로 통일한다. `OPAL Product OS Workbench`를 사용자 대면 제품명으로 남기지 않는다.
- C-2: `dashboard/`는 기존 Console 기능과 라우트를 유지하고 WorkStudio 실행 코드를 소유하지 않는다. 이관 뒤 동일 Workbench 구현을 두 앱에 중복 유지하지 않는다.
- C-3: Electron renderer는 Node.js API에 직접 접근하지 않는다. 폴더 선택·OPAL Project 탐지·파일 목록은 context isolation을 유지한 typed preload IPC 경계로만 제공한다 (`dashboard/frontend/electron/main.cjs:17-25`).
- C-4: 파일 접근은 사용자가 선택·등록한 Project 경로로 제한하고, Files는 읽기 전용 탐색부터 제공한다. 경로 이탈과 숨김/대용량 디렉터리 처리 기준을 PLAN에서 명시한다.
- C-5: 기존 OPAL Project 판정은 선택 폴더의 `.opal/AGENT.md` 존재로 수행하고, 탐지 성공 시 Project와 PM Agent를 한 동작으로 등록한다 (`docs/ARCHITECTURE.md:328-332`). 비 OPAL 폴더는 자동 PM 탐지를 주장하지 않는다.
- C-6: PM 메시지는 색상만으로 구분하지 않고 발신자 이름과 아바타 또는 이니셜을 함께 표시한다. 초대·배정·상태·블로커·결정·결과 이벤트는 일반 대화와 구분되는 시스템 카드로 유지한다 (`tasks/115-260910-opdw-데스크톱-워크벤치-인터랙티브-목업/wireframe.md` §4.7).
- C-7: 독립 Terminal은 이번 단계에서 실제 PTY를 연결하지 않는 시뮬레이션 경계를 유지하되, 채팅형 화면이 아니라 모노스페이스 scrollback·프롬프트·명령 이력 중심의 셸 UI로 표현한다.
- C-8: 기존 Surface 탭·split·Project→TASK→Agent 트리와 Dashboard의 기존 기능을 회귀시키지 않는다. 코드 파일 변경 시 `docs/CONVENTIONS.md` §@header 규칙을 따른다.

## Acceptance criteria

- AC-1: 저장소 루트 `workstudio/`에서 독립적인 개발 실행, 테스트, 타입 검사, production build, Electron 실행 명령을 제공하고 창 제목과 사용자 대면 명칭이 `OPAL WorkStudio`로 표시된다.
- AC-2: Dashboard는 기존 조회 화면으로 정상 빌드되며, query flag나 Dashboard 내부 Workbench 구현 없이도 동작한다. 이전 Workbench 구현의 중복 소유가 남지 않는다.
- AC-3: 좌측 `PROJECTS` 헤더에 `Project 추가`와 `TASK 추가`가 서로 다른 아이콘·툴팁·접근성 이름으로 표시되고 각각 올바른 Dialog를 연다.
- AC-4: Electron에서 Project 추가를 열면 사용자가 기존 디렉터리를 선택하거나 시스템 Dialog에서 새 폴더를 만든 뒤 선택할 수 있다. 취소·무효 경로는 상태를 변경하지 않고 명확한 안내를 표시한다.
- AC-5: 선택한 폴더에 `.opal/AGENT.md`가 있으면 Project 경로와 발견된 PM Agent가 자동 등록되고 Project 트리에 즉시 나타난다. 같은 경로의 중복 등록은 차단된다.
- AC-6: PM Coordination 일반 메시지에 발신자 이름과 아바타/이니셜 및 PM별 일관된 색상 단서가 표시된다. User·Main PM·각 Sub PM을 서로 식별할 수 있고 시스템 이벤트 카드는 이벤트 유형 아이콘과 행위자를 표시한다.
- AC-7: 독립 Terminal Surface가 일반 터미널처럼 모노스페이스 scrollback, 현재 작업 경로 또는 셸 표시, 프롬프트와 명령 입력을 제공한다. Enter로 실행한 mock 명령이 명령 이력과 출력에 순서대로 추가된다.
- AC-8: 우측 Files 탭은 좌측에서 선택한 단순 Project의 실제 읽기 전용 파일 트리를 표시한다. 폴더를 펼치고 접을 수 있으며 빈 폴더·읽기 실패·미선택 상태를 구분한다.
- AC-9: 실 경로가 없는 복합 Project를 선택하면 빈 패널 대신 직속 하위 Project 또는 Repository Component를 루트 노드로 보여주고, 각 노드 아래 파일 트리를 탐색할 수 있다.
- AC-10: WorkStudio 핵심 흐름과 IPC 경계에 대한 자동화 테스트가 추가되고, WorkStudio lint·typecheck·test·build 및 Dashboard 회귀 검증이 모두 통과한다.

## Open questions

없음. 제품명·앱 폴더·네 가지 UX 방향은 소유자 결정으로 확정됐다.
