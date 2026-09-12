# DONE: OPAL Product OS 데스크톱 Workbench 인터랙티브 목업

## 결과

Electron에서 실행되는 React 목업을 Project 계층 기반의 Execution Workspace로 개편했다. Project는 단순·복합 고정 유형 없이 재귀 계층을 구성하며, repository 내 영역은 독립 PM이 없는 Repository Component로 구분한다. TaskGroup과 별도 미니 프로젝트 엔티티는 제거하고 실행 규모를 Pilot 속성을 가진 TASK로 단일화했다.

중앙 Execution Workspace는 TASK별 PM Coordination Room, Sub PM Workspace, Worker Agent Terminal, 사용자가 직접 조작하는 독립 Terminal을 동적 탭과 split pane으로 배치한다. 사용자 지시는 Main PM으로만 전달되며, Main PM의 Sub PM 초대는 Room 참여자와 관찰 전용 Workspace를 함께 생성한다. Sub PM의 Worker 호출은 부모 PM에 연결된 관찰 전용 Terminal로 표현한다. 기존 Files/Changes, 탭 이동·분할, 설정, repository scope 목업은 유지했다.

## 변경 파일

- `dashboard/frontend/src/workbench/WorkbenchApp.tsx`
- `dashboard/frontend/src/workbench/WorkbenchApp.test.tsx`
- `dashboard/frontend/src/workbench/mock-adapter.ts`
- `dashboard/frontend/src/workbench/types.ts`
- `tasks/115-260910-opdw-데스크톱-워크벤치-인터랙티브-목업/TASK.md`
- `tasks/115-260910-opdw-데스크톱-워크벤치-인터랙티브-목업/ADDITIONAL-WORK-PROJECT-HIERARCHY.md`
- `tasks/115-260910-opdw-데스크톱-워크벤치-인터랙티브-목업/wireframe.md`
- `tasks/115-260910-opdw-데스크톱-워크벤치-인터랙티브-목업/GC-CONVENTION-20260912-1026.md`
- `tasks/115-260910-opdw-데스크톱-워크벤치-인터랙티브-목업/GC-CONVENTION-20260912-1200.md`
- `tasks/115-260910-opdw-데스크톱-워크벤치-인터랙티브-목업/GC-CONVENTION-20260912-1252.md`
- `tasks/115-260910-opdw-데스크톱-워크벤치-인터랙티브-목업/AGENTIC-LOG.md`
- `tasks/115-260910-opdw-데스크톱-워크벤치-인터랙티브-목업/state.json`
- `tasks/115-260910-opdw-데스크톱-워크벤치-인터랙티브-목업/STATE.md`
- `docs/proposals/archives/opal-product-os-desktop-workbench.md`

## 검증

- `npm test -- --run`: 10개 파일, 153개 테스트 통과
- `npm run typecheck`: 통과
- `npm run build`: 통과
- 변경 4파일 ESLint: 통과
- `npm run electron:syntax`: 통과
- `git diff --check`: 통과
- `state-tool validate`: 위반 0건
- 컨벤션 독립 점검: Critical·High·Medium·Low·Info 0건

## 회고적 학습 후보

.opal/brain/pages/entity/opal-console.md

## 참고

- Runtime(ACP·PTY·Browser·Worktree) 실제 연동은 목업 범위 밖이다.
- 초기 제안서 `opal-product-os-desktop-workbench.md`는 확정된 v9 모델과 충돌하므로 `폐기`로 archive한다.
