# DONE: WorkStudio Project Registry

## 결과

WorkStudio가 Electron `userData` 아래의 versioned JSON Project Registry를 통해 등록 프로젝트를 영속화하고, 최근 접근 순으로 보여주며, 재실행 후에도 다시 열 수 있게 되었다. 경로가 없어진 항목은 일반 열기를 차단하고 같은 ID로 복구하며, 목록 제거는 디스크 파일을 삭제하지 않는다. 손상·미지원 registry는 원본을 보존하고 빈 목록과 non-fatal recovery signal로 복구한다.

Renderer는 typed preload IPC만 사용하며 `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`를 유지했다. 신규 폴더 생성과 `.opal` 초기화는 WS-F102 범위로 남겨 실행 경로를 추가하지 않았다.

## 변경 파일

- `.opal/worktree.json`
- `workstudio/BACKLOG.md`
- `workstudio/electron/project-registry.cjs`
- `workstudio/electron/main.cjs`
- `workstudio/electron/main.test.mjs`
- `workstudio/electron/preload.cjs`
- `workstudio/src/workstudio/ipc.ts`
- `workstudio/src/workstudio/ipc.test.ts`
- `workstudio/src/workstudio/WorkStudioApp.tsx`
- `workstudio/src/workstudio/WorkStudioApp.test.tsx`
- `workstudio/src/workstudio/FirstRunWelcome.test.tsx`
- `tasks/128-260913-opds-워크스튜디오-프로젝트-레지스트리/`

## 검증

- `npm --prefix workstudio run test` — 52/52 PASS
- `npm --prefix workstudio run typecheck` — PASS
- `npm --prefix workstudio run lint` — PASS
- `npm --prefix workstudio run electron:syntax` — PASS
- TEST-SCENARIO S-1~S-6 — 6/6 PASS
- changed code-scan — 지원 TS/TSX 2/2 coverage, 위반 0건
- 상태·PLAN 계약 검증 — 위반 0건
- 컨벤션 검사 — Critical/High/Medium 0건, 기존 PascalCase 파일명 Low advisory 4건

## 회고적 학습 후보

.opal/brain/pages/entity/workstudio-project-registry.md
.opal/brain/pages/concept/electron-main-owned-project-registry.md

## 참고

- `workstudio/BACKLOG.md`의 WS-F101은 머지 전이므로 `in_progress`를 유지한다. 메인 머지 후 `done`으로 전환해야 한다.
- 다음 MVP 수직 슬라이스는 WS-F102 Project 열기·생성이다.
