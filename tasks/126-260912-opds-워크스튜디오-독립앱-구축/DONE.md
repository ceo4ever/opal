# DONE: OPAL WorkStudio 독립 앱 구축

> 완료일: 2026-09-12 22:30 KST | 스킬: `//opds` | 모드: agentic | 작업 방식: 격리 worktree

## 완료 요약

기존 Dashboard에 포함돼 있던 Workbench 목업을 독립 Electron 앱 `workstudio/`로 분리하고 제품명을 **OPAL WorkStudio**로 확정했다. Project·Task·Agent 탐색, PM Coordination, 독립 Terminal, Project Files를 하나의 실행 작업공간으로 구성했으며, 저장 상태가 없는 최초 실행에는 프로젝트 진입 방식을 고르는 Welcome 화면이 먼저 열린다.

## 구현 결과

1. **독립 앱 경계**
   - `workstudio/`가 자체 package, Vite renderer, Electron main/preload를 소유한다.
   - Dashboard의 Workbench 진입점과 소스 결합을 제거하고 Console 역할만 유지했다.
2. **Project 등록과 탐색**
   - 좌측 사이드바의 Project 추가 버튼에서 OS 디렉터리 선택기를 연다.
   - `.opal/AGENT.md`가 있는 Project는 OPAL Project로 감지하고 Project PM을 함께 등록한다.
   - Project→진행 Task→실행 Agent 재귀 트리와 Task 직행 생성 경로를 제공한다.
3. **PM Coordination 가독성**
   - PM별 avatar label과 안정적인 색상 토큰을 적용했다.
   - 대화와 배정·초대·결정·결과 같은 시스템 이벤트를 시각적으로 구분했다.
4. **실행 작업공간**
   - 독립 Terminal을 shell 형태의 입력·출력·scrollback UI로 구성했다.
   - Agent Terminal, Browser, Markdown 등 Surface 탭과 split/reorder 동작을 보존했다.
5. **Files 패널 복원**
   - 선택된 단일 Project는 실제 read-only IPC 파일 트리를 표시한다.
   - 복합 Project는 하위 Project/repository root를 가상 루트로 표시한다.
   - 경로 이탈, 읽기 실패, 빈 폴더, 항목 과다 상태를 명시적으로 처리한다.
6. **최초 실행 Welcome**
   - 저장된 WorkStudio 상태가 없으면 `기존 프로젝트 열기`, `새 프로젝트 만들기`, `데모 둘러보기`를 표시한다.
   - 선택 취소·오류 시 Welcome을 유지하고, Project 선택 성공 또는 데모 진입 후 상태를 저장한다.
   - 최근 Project Registry의 실제 영속화는 후속 범위로 남기고 현재는 empty state를 표시한다.

## 주요 변경 파일

| 구분 | 경로 | 내용 |
|---|---|---|
| 신규 앱 | `workstudio/` | 독립 Electron/Vite WorkStudio 전체 |
| 핵심 UI | `workstudio/src/workstudio/WorkStudioApp.tsx` | Project 트리, Coordination, Surface, Files, Welcome |
| 상태 계층 | `workstudio/src/workstudio/mock-adapter.ts` | seed·persisted UI·Workspace mutation |
| Desktop IPC | `workstudio/electron/main.cjs`, `preload.cjs` | Project 선택·등록·read-only 파일 조회 |
| 테스트 | `workstudio/src/workstudio/*.test.ts*` | UI, IPC, adapter, first-run 계약 |
| Dashboard | `dashboard/frontend/` | Workbench 제거 및 기존 lint 결손 정리 |
| 문서 | `docs/PROJECT.md`, `docs/ARCHITECTURE.md` | WorkStudio와 Dashboard 소유 경계 |

## 검증 결과

| 범위 | 결과 |
|---|---|
| WorkStudio lint | PASS |
| WorkStudio typecheck | PASS |
| WorkStudio Vitest | **4 files, 42 tests PASS** |
| WorkStudio production build | PASS |
| Electron main/preload syntax | PASS |
| Dashboard lint/typecheck/build | PASS |
| Dashboard Vitest | **9 files, 123 tests PASS** |
| Test scenarios | **S-1~S-9 PASS, fail/block 0** |
| First-run additional scenarios | **AW-FR-1~AW-FR-5 PASS** |
| Convention check | Critical/High 0 |
| Code scan | inline coverage 100%, violations 0 |

## 실행 확인

- 최신 production build로 Electron 앱을 실행했다.
- 기존 사용자 저장 데이터는 삭제하지 않았다.
- 최초 실행 화면 확인용 창은 `/private/tmp/opal-workstudio-first-run-preview` 격리 프로필로 실행해 Welcome 화면이 즉시 노출되도록 했다.

## 경계와 후속 후보

- 독립 Terminal은 현재 결정론적 simulated shell이며 실제 PTY 연결은 후속 범위다.
- PM/Agent Runtime 실연동은 포함하지 않았고 Agent CLI는 관찰용 mock이다.
- 최근 Project 목록의 Registry 영속화·재열기 기능은 별도 Project Registry 태스크가 적합하다.
- Vite 번들은 500 kB 경고가 있으나 기능·빌드 실패는 아니다. 제품화 단계에서 code splitting을 검토한다.
- 적용 대상으로 소비한 `docs/proposals/` 문서가 없어 CLOSE 제안서 아카이브 절차는 자연 스킵했다.
- 커밋·worktree merge는 캡틴의 명시 지시 전까지 수행하지 않는다.
