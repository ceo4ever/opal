---
template: sdlc-v2
---
# TASK: OPAL Product OS 데스크톱 Workbench 인터랙티브 목업

## Problem

OPAL Product OS의 제안 범위는 Project·Workstream·Task·Run과 Agent·Terminal·Browser·Files·Diff·Result를 한 Workbench에 결합한다. 현재는 이 구조를 설명하는 제안서만 있고, 사용자가 실제 데스크톱 화면에서 정보 구조·멘션·위임·Run 상태·검증 흐름을 클릭하며 검토할 수 없다. 이 상태에서 ACP·PTY·Browser·Worktree Runtime을 먼저 구현하면 화면과 사용 흐름이 바뀐 때 고비용 재작업이 발생한다 (`docs/proposals/archives/opal-product-os-desktop-workbench.md` §16 MVP와 단계별 구현).

## Proposed outcome

실제 Electron 창에서 실행되는 React 기반 인터랙티브 목업을 만든다. 사용자는 OPAL 프로젝트의 대표 Task를 생성하고, `@OPAL PM`에게 지시하고, PM이 전문 Agent에게 위임하고, Agent Run의 진행·Terminal·Browser·파일 변경·Git Diff·검증·결과를 하나의 Workbench에서 확인한다. 모든 실행 결과는 목업 데이터로 제공하고 Runtime 연동 전에 제품 구조와 인터랙션을 확정할 수 있게 한다 (`docs/proposals/archives/opal-product-os-desktop-workbench.md` §5 주요 사용자 흐름, §10 Workbench UX).

## Affected users and systems

- 사용자: OPAL을 활용해 하나 이상의 LLM CLI에 업무를 지시하고 결과를 검토하는 1인 개발자.
- 시스템: `dashboard/frontend/`의 React·TypeScript·Vite UI, 신규 Electron shell, 목업 데이터와 로컬 UI 상태.
- 포함: Project·Workstream·Task 탐색, Task 생성·Kanban 이동, Agent 설정, Conversation·멘션·위임, Run 상태, Workbench Tool View, Activity Log, Result 검토, 목업 복원.
- 제외: 실제 ACP Agent 세션, LLM API·CLI 프로세스, node-pty, agent-browser·Playwright 제어, Git Worktree, 실제 파일 변경, SQLite, 운영용 보안·패키징.

## Constraints

- C-1: 목업은 Runtime 연동 완료를 주장하지 않고, 목업·시뮬레이션·미구현 상태를 UI에서 명확히 구분한다.
- C-2: 대표 흐름은 `Project → TaskGroup(선택) → Task → Surface(터미널·에이전트·브라우저) → Files/Changes`로 유지한다. TaskGroup은 Project 아래 고정 분류축이 아니라 Task를 묶는 선택적 태그이며 사용자가 자유롭게 만들고 지운다. Run보다 오래 살아있는 도구 상태는 Execution Environment 개념으로 표현한다.
- C-3: `.opal/AGENT.md`는 OPAL PM으로 발견된 목업 Agent Definition으로 표현하고, Agent 정의와 runtime·model 연결 설정을 분리한다 (`docs/proposals/archives/opal-product-os-desktop-workbench.md` §9 Agent 모델).
- C-4: 사용자 지정 Agent를 추가하고, 추가한 Agent를 본문 Surface 탭에서 세션으로 열 수 있는 경로를 포함한다.
- C-5: 터미널·에이전트 세션의 원본 출력을 기본 화면에 무제한으로 노출하지 않는다.
- C-6: 기존 Console의 주요 화면과 스타일 자산을 재사용할 수 있게 하고, 목업 검증을 위해 관계없는 Console 기능을 제거하지 않는다 (`docs/PROJECT.md` §주요 컴포넌트 (OPAL Console)).
- C-7: 데스크톱 창은 현재 React/Vite 기반을 사용하며, 새 UI 상태는 실제 Runtime으로 교체 가능한 목업 경계 뒤에 둔다 (`dashboard/frontend/package.json`).
- C-8: 데스크톱 핵심 흐름을 우선한다. 본문 Surface 탭의 기본 split(좌우·상하 분할, pane 간 탭 이동)과 우측 사이드바 리사이즈는 이번 범위에 포함한다. Monaco 기반 실제 코드 편집, pane별 독립 검색·탭 그룹 저장 등 split 고급 기능, 실제 session recovery, 배포 packaging은 후속 태스크로 이월한다.
- C-9: 소스 수정 전에 wireframe.md를 확정하고, 구현은 그 화면 목록과 인터랙션을 임의로 확장하지 않는다.
- C-10: 위임·Run 추적·검증·결과 승인 UI는 이번 목업 범위에서 제외한다. LLM과의 대화는 본문 Surface 탭(터미널 또는 에이전트 세션)에서 일어나며, 결과 검토는 우측 `Changes`(git)에서 수행한다.

## Acceptance criteria

> 번호는 안정적으로 유지한다. 결번(AC-7·8·9·11)은 C-10으로 범위에서 제외된 항목이며 재사용하지 않는다.

- AC-1: Electron 앱이 로컬에서 실행되고 React Workbench를 데스크톱 창에 표시한다.
- AC-2: 사용자가 여러 Project 중 하나를 선택해 전환하고, 선택한 Project 안에서 사용자가 만든 TaskGroup으로 Task 목록을 묶어 상태를 확인할 수 있다.
- AC-3: 사용자가 Task를 생성하고 Kanban 상태를 이동한 후 선택한 Task의 Workbench로 진입할 수 있다.
- AC-4: 설정 화면의 Agent 섹션에 프레임워크 제공 Agent와 사용자 추가 Agent가 표시되며, 각 Agent의 역할·runtime·model·상태를 확인하고 목업 설정을 변경할 수 있다.
- AC-5: 사용자가 본문에서 터미널 또는 에이전트 Surface 탭을 열어 LLM 세션을 발동하고 대화를 주고받는 흐름을 시뮬레이션한다.
- AC-6: 하나의 Task에서 Terminal·Browser·Markdown·모바일 에뮬레이터·LLM 에이전트 Surface 탭을 `+`로 추가하고 닫고 전환하며, 각 Surface의 대표 목업 데이터를 확인할 수 있다.
- AC-10: 선택한 Project·TaskGroup·Task·Surface 탭 구성과 split 배치, 좌·우 사이드바 접힘 상태, 파일 트리 펼침 상태가 앱 재실행 후 복원되는 시나리오를 시뮬레이션한다.
- AC-12: 제품 검토자가 대표 시나리오를 처음부터 끝까지 클릭하고 Project·TaskGroup·Task·Surface·Environment의 관계와 파일·git 검토 위치를 판단할 수 있다.
- AC-13: 변경된 프런트엔드는 lint·typecheck·build를 통과하고 목업용 핵심 흐름을 검증하는 테스트가 통과한다.
- AC-14: 사용자가 본문 Surface 탭을 드래그해 좌우 또는 상하로 split하고, split된 pane 사이에서 탭을 이동할 수 있다.
- AC-15: 사용자가 우측 사이드바 `Files` 탭에서 폴더·파일을 탐색하고 추가·삭제하며, `Changes` 탭에서 git 변경 목록과 커밋 흐름을 목업으로 확인할 수 있다. 좌·우 사이드바는 각각 폭을 드래그로 조절하고 접고 펼칠 수 있다.
- AC-16: 실행 중인 Surface 세션의 상태를 탭 자체의 표시(진행·완료·실패)로 구분할 수 있다.
- AC-17: 파일 트리가 계층 구조로 표시되며, 폴더를 셰브론으로 접고 펼치고, 폴더·파일 아이콘과 git 상태 표기(수정·미추적·무시됨)를 구분해 확인할 수 있다.
- AC-18: `Changes` 탭이 변경 파일을 디렉터리별로 묶어 건수와 함께 보여주고, 파일별 추가·삭제 라인 수를 표시한다.
- AC-19: 사용자가 좌측 사이드바 하단 설정 아이콘으로 설정 화면에 진입해 Agent·외관·Workbench·프로젝트·목업 5개 섹션을 전환하고, 외관(테마·폰트 크기)과 Workbench 기본값(새 탭 기본 종류·사이드바 기본 접힘·트리 들여쓰기)을 변경하며, 목업 상태를 초기값으로 되돌릴 수 있다.

## Open questions

없음. 시각 스타일·상세 레이아웃·상호작용 배치는 WIREFRAME 단계에서 제안하고 사용자 검토로 확정한다.

## 추가 작업 연결

- [재귀형 프로젝트 관리와 PM 조율](./ADDITIONAL-WORK-PROJECT-HIERARCHY.md) — 파이프라인 27~37행의 추가 요구사항·수용 기준 SSOT. 기존 계약과 충돌하는 항목(C-2·AC-2·C-10·AC-15·AC-18·AC-19)은 연결 문서의 대체표를 우선 적용한다.
