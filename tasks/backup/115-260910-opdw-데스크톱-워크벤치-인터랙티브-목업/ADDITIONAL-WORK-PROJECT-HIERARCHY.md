# 추가 작업: 재귀형 프로젝트 관리와 PM 조율

> 태스크 115 추가 작업 SSOT
> 요구사항 확정: `state.json` 26행 완료 | 1차 설계·구현: 27~31행 | PM 조율 작업공간 보완: 32~37행 | 실행 작업공간 UX 보완: 38~43행 | PM Coordination Room 보완: 44~49행

## 배경

현재 목업은 Project를 단일 repository 경로와 평면 선택기로 표현한다. 실제 관리 대상은 Pug·Blend·MAMS처럼 각자 PM과 TASK를 가진 독립 Project이며, 사용자는 이 Project들을 다시 하나의 상위 Project로 묶어 Main PM이 조율할 수 있어야 한다.

이 추가 작업은 기존 Surface·split·Files/Changes 인터랙션을 유지하면서 Project 생성·계층·PM 책임과 교차 Project TASK 조율을 클릭 가능한 목업으로 검증한다.

## 기존 계약과의 적용 규칙

- `TASK.md`는 기존 범위의 기준이고, 이 문서는 27~49행에서 추가·변경된 요구사항의 기준이다.
- 같은 쟁점에서 두 문서의 문구가 충돌하면 이 문서의 아래 대체표를 적용한다. 나머지 기존 계약은 그대로 유지한다.
- `TASK.md`에는 이 문서의 연결정보만 둔다. 추가 수용 기준을 `TASK.md`의 기존 AC 번호에 합치거나 재번호화하지 않는다.
- 수용 기준은 기존 `AC-*`와 추가 `AW-AC-*` 두 네임스페이스로 구분한다. `wireframe.md` 추적표는 두 집합을 모두 별도 ID 그대로 추적한다.

| 기존 계약 | 27~37행 적용 계약 |
|---|---|
| C-2·AC-2의 평면 Project 선택과 TaskGroup | 재귀 Project 트리에서 Project를 선택·전환한다. TaskGroup과 별도 TASK 필터 UI는 제거하며 완료 TASK는 탐색 트리에서 자동으로 숨긴다. |
| C-10의 위임·Run 추적·검증·결과 승인 UI 제외 | Agent Run 수준의 위임·원본 실행 추적·검증 상세·승인 UI는 계속 제외한다. Project PM 수준의 TASK 배정, 상태 상향 집계, PM 간 조율 요약과 Main PM 최종 판단만 추가한다. |
| AC-15·AC-18의 단일 Project Files/Changes | 기존 Files/Changes 동작은 유지하되 Repository Component가 여러 개면 현재 repo를 먼저 구분하고 선택된 repo 범위의 파일·변경 목록을 표시한다. |
| AC-19의 설정 화면 프로젝트 섹션 | Project 생성·기존 연결과 사후 관리는 설정 화면의 프로젝트 섹션에서 담당한다. `PROJECTS +`는 현재 선택 Project의 TASK 추가 진입점이다. |

## 확정된 개념

### Project

- Project는 PM·TASK·문서·의사결정의 책임 경계다.
- Project는 자체 관리 repo와 PM Agent 한 명을 가진다.
- Project는 부모가 없는 최상위 Project이거나 다른 Project의 자식일 수 있다.
- 자식이 없으면 단순 Project, 자식이 생기면 복합 Project가 된다. 유형은 생성 시 고정하지 않는다.
- 복합 Project 안에 복합 Project를 둘 수 있으며 같은 모델을 재귀적으로 적용한다.
- Project는 정본 부모를 하나만 가진다. 다른 계층에서는 링크로 참조하며 다중 부모 구조는 만들지 않는다.

### Repository Component

- Repository Component는 Project가 작업 대상으로 관리하는 실제 코드 repo 또는 monorepo 내부 영역이다.
- Repository Component는 독립 PM·TASK·프로젝트 의사결정을 갖지 않는다.
- Pug의 backend·frontend·admin·iOS·Android repo는 Pug Project의 Repository Component다.
- Blend의 backend·batch·admin·monitor repo는 Blend Project의 Repository Component다.
- MAMS의 backend·docker·frontend·frontend_test·frontend_wireframe 영역은 MAMS Project가 관리하는 monorepo 구성이다.

### TASK와 Pilot

- 모든 업무 단위는 TASK 하나로 통일한다.
- 대규모 업무를 위한 별도 엔티티나 별칭을 만들지 않는다.
- 업무 규모와 수행 방법은 TASK의 Pilot(`opp`, `opd`, `opds`, `opdw`, `oppl`, `opsdd` 등)로 표현한다.
- TaskGroup과 별도 TASK 필터 UI는 사용하지 않는다. 진행 중인 업무만 트리에 표시하고 완료 TASK는 자동으로 숨기되 데이터와 조율 이력은 유지한다.
- TASK는 하나의 Project가 소유한다.
- 교차 Project 업무는 상위 조율 TASK가 하위 Project의 수행 TASK를 참조하는 방식으로 연결한다.
- `oppl`·`opsdd`가 내부적으로 만드는 backlog·ACT·단계는 좌측 Project 트리의 별도 Project나 TASK 노드로 펼치지 않는다.
- 좌측 탐색 계층은 `Project → TASK → 실행 Agent`로 고정하고, TASK와 Agent 노드는 Project 트리 안에서 펼쳐 확인한다. Pilot 내부 단위와 진행률은 선택한 TASK의 Workbench 상세에서만 확인한다.

### Main PM과 Sub PM

- 모든 Project는 PM Agent 한 명을 가진다.
- Main/Sub는 고정 직급이 아니라 현재 Project 계층에서의 상대적 역할이다.
- 자식 Project를 가진 Project의 PM은 직속 자식 PM들의 Main PM이다.
- 부모 Project가 있는 Project의 PM은 부모 기준 Sub PM이며, 동시에 자기 자식들에게는 Main PM일 수 있다.
- Main PM은 직속 Sub PM에게 업무를 배정하고 상태·결정·블로커·결과를 취합해 최종 조율한다.
- Sub PM들은 필요한 경우 서로 의존성과 인터페이스를 조율한다. 이 조율 결과는 상위 조율 타임라인에 요약되어 Main PM이 전체 상황을 잃지 않게 한다.

## 대표 구조

```text
StoreLinkStudio Project — Main PM
├─ 조율 TASK [oppl] [PUG] [BLEND] [MAMS]
│  ├─ PM Coordination Surface — Main PM ↔ Pug·Blend·MAMS PM
│  └─ 연결된 하위 TASK 상태·블로커·결정·결과
├─ Pug Project — Pug PM
│  ├─ TASK
│  │  └─ 실행 Agent → Terminal/Browser/Markdown Surface
│  └─ Repository Components 6
├─ Blend Project — Blend PM
│  ├─ TASK
│  └─ Repository Components 4
└─ MAMS Project — MAMS PM
   ├─ TASK
   └─ Monorepo Components
```

`StoreLinkStudio Project`도 상위 Project의 자식이 될 수 있다. 이 경우 StoreLinkStudio PM은 상위 기준 Sub PM이면서 Pug·Blend·MAMS 기준 Main PM이다.

대표 seed로 사용할 세 Project는 모두 `.opal/AGENT.md`가 존재하는 OPAL Project임을 확인했다: `/Volumes/Data/StoreLinkStudio/pug`, `/Volumes/Data/StoreLinkStudio/blend`, `/Volumes/Data/StoreLinkStudio/mams`.

## 화면 요구사항

### Project 탐색

- 좌측 사이드바를 평면 Project Select가 아닌 재귀 Project 트리로 바꾼다.
- `PROJECTS` 헤더의 `+`는 현재 선택 Project에 TASK를 추가하는 진입점이다. 아이콘에는 `TASK 추가` 툴팁과 접근성 이름을 둔다.
- 각 Project 행은 이름, PM, 진행 TASK 수, 블로커 상태를 표시한다.
- Project를 펼치면 하위 Project, TASK, 실행 Agent를 단계적으로 확인할 수 있다.
- PM은 Project 행에 고정 표시하고, PM·전문 워커의 실제 실행 세션은 해당 TASK 아래 표시한다.
- TaskGroup과 상태·Pilot·담당자·참여 Project·검색 필터 영역은 제거한다. `done` TASK는 좌측 트리에서 자동으로 숨긴다.

### Project 생성과 연결

- 사용자는 최상위 Project를 새로 만들거나 기존 OPAL Project를 연결할 수 있다.
- 선택한 Project 아래에서도 신규 Project 생성과 기존 Project 연결을 수행할 수 있다.
- 신규 Project 생성·기존 연결은 설정 화면의 프로젝트 섹션으로 일원화한다. 최상위 또는 부모 Project를 선택해 생성·연결할 수 있다.
- 설정 화면의 프로젝트 섹션은 생성·연결과 등록된 Project의 경로·PM·부모 관계·제거를 함께 관리한다.
- 신규 생성 Dialog는 이름, 경로, PM Agent를 입력받고 관리 repo·OPAL 구조 생성이 예정됨을 표시한다.
- 기존 연결 Dialog는 경로와 발견된 `.opal/AGENT.md`의 PM 정보를 보여준다.
- 실제 폴더·Git·`.opal` 생성은 수행하지 않고 목업 상태로만 시뮬레이션한다.
- Project에 Repository Component를 추가·제거하고 구성 목록을 확인할 수 있다.

### TASK와 조율

- 선택한 Project에서 TASK를 생성하고 Pilot을 선택할 수 있다.
- 일반 TASK와 조율 TASK는 같은 TASK 엔티티를 사용한다.
- 조율 TASK마다 하나의 `PM Coordination Room`을 만든다. Project 전체에 영구 대화방 하나를 두지 않는다.
- 사용자는 Main PM에게만 지시할 수 있다. 사용자 입력 UI에는 Sub PM 대상 선택, 이벤트 유형, Pilot 선택을 두지 않는다.
- 사용자가 조율 TASK를 만들 때 참여 Project를 직접 고르지 않는다. 조율 TASK는 소유 Project/Main PM만으로 시작한다.
- Main PM은 업무 맥락을 판단해 직속 또는 관련 Project의 Sub PM을 Room에 초대하며 Room의 소유자·최종 조율자다.
- 초대된 Sub PM들은 Main PM 및 같은 Room의 다른 Sub PM과 대화하면서 의존성·인터페이스·블로커를 조율한다.
- 조율 TASK에는 초대된 Project 칩과 연결된 하위 TASK 상태를 표시한다.
- Main PM이 Sub PM에게 TASK를 요청하고 Sub PM이 수행 TASK를 생성하는 흐름을 시뮬레이션한다.
- 조율 TASK의 중앙 영역에는 Main PM과 초대된 Sub PM들이 대화하는 전용 `PM Coordination Room Surface`를 둔다. 일반 터미널과 구분되는 다자간 대화 Surface이며 split과 탭 이동을 지원한다.
- Room 헤더에는 소유자 Main PM, 초대된 Sub PM, 각 PM Workspace 상태를 표시한다. `PM 초대 요청`은 사용자→Main PM 요청으로 기록된 뒤 Main PM 초대 이벤트로 처리한다.
- Room의 일반 메시지는 발신자를 구분하는 대화 버블로, `초대·배정·상태·블로커·결정·결과`는 같은 흐름 안의 시스템 카드로 표시한다.
- Main PM이 대화 입력에서 Sub PM에게 업무를 배정하면 대상 Project에 연결된 하위 TASK가 생성되고, 해당 TASK에 PM/Worker 실행 Agent와 Terminal Surface가 만들어지는 흐름을 시뮬레이션한다.
- Main PM이 Sub PM을 초대하면 해당 PM Agent가 발동되고 `Sub PM Workspace` Terminal이 즉시 열린다.
- Sub PM Workspace는 해당 Sub PM이 Worker Agent를 호출·지시·보고받는 작업공간이다. Worker 호출 시 부모 Sub PM과 연결된 Worker Terminal을 추가로 연다.
- Sub PM Workspace와 Worker Terminal은 사용자에게 관찰 전용이다. 사용자는 이 Terminal에 직접 입력하지 않고 Room의 Main PM 입력창만 사용한다.
- 독립 Terminal은 사용자 직접 입력이 가능하며 PM/Worker Agent Terminal과 구분한다.
- Sub PM은 자기 TASK에서 여러 Worker Terminal·Browser·Markdown·Emulator Surface를 동시에 실행할 수 있다. Main PM Room에는 원시 실행 로그 대신 연결 TASK의 상태·블로커·결과 요약만 상향된다.
- PM Coordination Surface에는 Agent Run 원본, 도구 실행 로그, 검증 상세, 승인 조작을 표시하지 않는다.
- Main PM의 최종 통합 판단과 하위 PM의 개별 결과를 구분한다.

### Execution Workspace 문맥

- 가운데 영역의 공식 명칭은 `Execution Workspace(실행 작업공간)`다. 현재 선택한 TASK를 수행·조율·관찰하는 다중 pane 작업영역이다.
- Execution Workspace와 우측 Files/Changes는 현재 선택한 TASK와 그 TASK 소유 Project의 문맥을 따른다.
- 조율 TASK에서는 PM Coordination Surface를 기본 Surface로 열고, 실행 Surface와 나란히 split할 수 있다. 사용자가 만든 탭과 split 배치는 재실행 후 복원한다.
- PM Coordination pane은 Main/Sub PM의 대화와 배정·상태·블로커·결정·결과만 다룬다.
- Agent Terminal pane은 특정 PM 또는 Worker Agent 실행 세션에 귀속되며 TASK 아래 Agent 노드와 연결한다.
- 독립 Terminal pane은 Agent에 귀속되지 않는 사용자의 일반 셸이다. Surface `+`에서 언제든 추가하고 다른 pane과 split할 수 있다.
- Repository Component가 여러 개인 Project에서는 Files/Changes에 현재 대상 repo를 구분해 표시한다.
- 기존 Surface 추가·닫기·split·탭 이동과 사이드바 리사이즈 기능을 유지한다.

## 목업 데이터 계약

- `Project`: `id`, `name`, `repositoryPath`, `parentProjectId?`, `pmAgentId`, `repositoryComponentIds[]`
- `RepositoryComponent`: `id`, `projectId`, `name`, `path`, `kind(repo|monorepo-area)`
- `Task`: 기존 필드 + `ownerProjectId`, `pilot`, `participantProjectIds[]`, `coordinationTaskId?`
- `CoordinationEvent`: `id`, `taskId`, `projectId`, `pmAgentId`, `type(instruction|invitation|assignment|status|coordination|blocker|decision|result|worker_spawn)`, `summary`, `timestamp`. `pmAgentId=user`는 Main PM에게 보낸 사용자 지시를 뜻한다.
- `CoordinationRoom`: `id`, `taskId`, `mainProjectId`, `mainPmAgentId`, `invitedProjectIds[]`. 조율 TASK당 하나이며 사용자 입력 수신자는 Main PM으로 고정한다.
- `SurfaceTab`의 Agent Terminal은 `agentId`와 선택적 `parentAgentId`로 PM→Worker 호출 관계를 표현하고, Room 문맥의 Agent Terminal은 사용자 관찰 전용으로 렌더한다.
- `SurfaceKind`: 기존 종류 + `coordination`. 조율 TASK의 기본 PM 대화 Surface이며 일반 실행 Terminal과 구분한다.
- Main PM의 `assignment` 이벤트는 대상 Project의 하위 TASK·Environment·PM 실행 Agent Surface를 함께 생성하고 `coordinationTaskId`로 원자적으로 연결한다.
- Project의 단순/복합 유형은 `parentProjectId`와 자식 존재 여부로 파생하며 별도 고정 필드로 저장하지 않는다.
- Project 계층은 순환을 허용하지 않는다.
- Project 트리 펼침 상태, 선택 Project·TASK, 생성·연결된 목업 Project를 앱 재실행 후 복원한다.

## 추가 수용 기준

- AW-AC-1: 사용자가 최상위 Project를 신규 생성하고 Project 트리에서 확인할 수 있다.
- AW-AC-2: 사용자가 기존 OPAL Project를 최상위 또는 선택한 Project의 자식으로 연결할 수 있다.
- AW-AC-3: 복합 Project 안에 복합 Project를 중첩하고 재귀 트리로 탐색할 수 있다.
- AW-AC-4: 모든 Project 행에서 해당 Project의 PM을 식별할 수 있다.
- AW-AC-5: Project와 Repository Component가 서로 다른 관리 단위로 표시되고, Component를 추가·제거하며 선택 repo별 Files/Changes를 서로 다르게 확인할 수 있다.
- AW-AC-6: 모든 업무가 TASK로 표시되고 생성 시 수행 Pilot을 선택·구분할 수 있다.
- AW-AC-7: Main PM의 조율 TASK가 하위 Project의 수행 TASK와 연결된다.
- AW-AC-8: Sub PM 간 조율 내용이 상위 조율 타임라인에 요약된다.
- AW-AC-9: Main PM의 최종 판단과 각 Sub PM의 결과를 구분해 확인할 수 있다.
- AW-AC-10: Pug·Blend·MAMS가 StoreLinkStudio Project 아래에 연결된 대표 구조를 검토할 수 있다.
- AW-AC-11: 선택 Project·TASK·Project 트리 펼침과 생성·연결 상태가 앱 재실행 후 복원된다.
- AW-AC-12: 기존 Surface·split·Files/Changes 핵심 인터랙션이 회귀하지 않는다.
- AW-AC-13: `oppl`·`opsdd` TASK의 내부 단위는 Project 트리에 추가 노드로 나타나지 않고 TASK 상세에서만 확인할 수 있다.
- AW-AC-14: TaskGroup과 별도 필터 UI 없이 진행 중인 TASK를 탐색하며 완료 TASK는 트리에서 자동으로 숨겨진다.
- AW-AC-15: Project를 펼치면 그 Project의 TASK와 실제 실행 Agent가 트리 노드로 표시된다.
- AW-AC-16: 조율 TASK에서 Main PM과 Sub PM이 `PM Coordination Surface`로 대화하고 구조화된 배정·상태·조율·블로커·결정·결과를 확인할 수 있다.
- AW-AC-17: Main PM의 Sub PM 업무 배정으로 대상 Project의 연결 TASK와 PM/Worker 실행 Surface가 생성된다.
- AW-AC-18: Sub PM TASK에서 여러 실행 Surface가 동시에 동작하고, Main PM 조율 화면에는 원시 로그가 아닌 상태·블로커·결과 요약만 표시된다.
- AW-AC-19: `PROJECTS +`로 현재 선택 Project의 TASK 생성 Dialog를 바로 열 수 있다.
- AW-AC-20: 최상위·하위 Project의 신규 생성과 기존 연결은 설정 화면의 프로젝트 섹션에서 수행할 수 있다.
- AW-AC-21: Execution Workspace에서 PM Coordination pane과 여러 Agent Terminal pane을 동시에 배치·조작할 수 있다.
- AW-AC-22: Agent에 귀속되지 않은 독립 Terminal pane을 추가하고 split·이동·닫을 수 있다.
- AW-AC-23: 조율 TASK마다 Main PM이 소유하는 PM Coordination Room이 하나 생성된다.
- AW-AC-24: 사용자는 Main PM 입력창에만 지시할 수 있고 Sub PM·Worker Agent Terminal에는 직접 입력할 수 없다.
- AW-AC-25: Main PM의 Sub PM 초대 요청 처리로 Room 참여자와 해당 Sub PM Workspace Terminal이 함께 생성된다.
- AW-AC-26: 초대된 Main/Sub PM들이 한 Room에서 발신자별 대화와 초대·배정·상태·블로커·결정·결과를 함께 확인할 수 있다.
- AW-AC-27: Sub PM이 Worker Agent를 호출하면 부모 Sub PM과 연결된 관찰 전용 Worker Terminal이 생성되고 실행 Agent 트리에 표시된다.

## 제외 범위

- 실제 디렉터리와 Git repo 생성·clone·이동
- 실제 `.opal/AGENT.md`·`tasks/` 초기화
- 실제 Main PM·Sub PM 프로세스 호출과 Agent Runtime 연결
- 실제 PM 간 메시지 전송·큐·동시성 제어
- 실제 교차 repo Git 변경·커밋
- 데이터베이스 영속화와 마이그레이션

위 항목은 본 목업으로 정보구조와 사용자 흐름을 확정한 뒤 Runtime 개발 태스크에서 구현한다.
