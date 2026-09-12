# GC CONVENTION REPORT — 2026-09-12T21-07-30

## 1. 헤더

- 실행 일시: 시작 2026-09-12 21:07:30 / 완료 2026-09-12 21:10:00 / 소요 2분 30초
- 범위: `WorkStudio` / 대상 파일 51개
- 에이전트: `opal-convention-checker` fallback worker
- 기준 문서: `docs/CONVENTIONS.md`, `docs/PROJECT.md`, `workstudio/eslint.config.js`, `workstudio/tsconfig*.json`
- APPLY 수행 여부: N (read-only PM Gate)
- 검사 상태: pass

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 2 |
| 심각도 분포 | Critical 0 / High 0 / Medium 0 / Low 2 / Info 0 |
| 집행 수준 분포 | Blocking 0 / Advisory 2 / Informational 0 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 2 |
| 파일별 상위 Top 5 | `workstudio/src/workstudio/WorkStudioApp.tsx` (1건) / `workstudio/src/workstudio/WorkStudioApp.test.tsx` (1건) |
| 카테고리별 빈도 | 파일 네이밍 (2 파일) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 |

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (0건)

### Low (2건)

- [?] GC-C001 [workstudio/src/workstudio/WorkStudioApp.tsx:1] React component 파일명이 kebab-case 규칙과 다름
  - 카테고리: 파일 네이밍
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §네이밍 규칙)
  - 설명: 프로젝트 문서는 파일/폴더 이름을 English kebab-case로 규정하지만, 이 파일은 PascalCase component 파일명이다.
  - 판단: Dashboard React 코드에는 `App.tsx`, `SettingsPage.tsx`, `DashboardPage.tsx` 등 PascalCase component 파일이 이미 존재해 React 컴포넌트 관례와 프로젝트 일반 파일명 규칙이 충돌한다. lint/typecheck/test/build 통과가 PM 실측으로 보고되었으므로 차단 이슈가 아니라 advisory로 둔다.
  - 해결 방안: WorkStudio에서도 strict kebab-case를 집행할지, React component 파일은 PascalCase 예외로 문서화할지 결정한다. strict 집행 시 `work-studio-app.tsx`로 rename하고 import 경로를 함께 변경한다.
  - 자동 수정: N
  - 참조: `docs/CONVENTIONS.md` §파일/폴더, `dashboard/frontend/src/App.tsx` 및 `dashboard/frontend/src/pages/*/*Page.tsx` 관측 패턴

- [?] GC-C002 [workstudio/src/workstudio/WorkStudioApp.test.tsx:1] React test 파일명이 kebab-case 규칙과 다름
  - 카테고리: 파일 네이밍
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §네이밍 규칙)
  - 설명: 프로젝트 문서는 파일/폴더 이름을 English kebab-case로 규정하지만, 이 테스트 파일은 대상 component 이름을 보존한 PascalCase test 파일명이다.
  - 판단: Dashboard React 테스트에도 `TasksPage.stats.test.tsx`, `DashboardPage.stats.test.tsx` 등 PascalCase component 기반 테스트 파일명이 관측된다. 실행 설정이 이를 금지하지 않아 advisory로 둔다.
  - 해결 방안: WorkStudio component 파일명 예외를 문서화하거나, strict kebab-case 집행을 선택하면 `work-studio-app.test.tsx`로 rename하고 import 경로를 함께 변경한다.
  - 자동 수정: N
  - 참조: `docs/CONVENTIONS.md` §파일/폴더, `dashboard/frontend/src/pages/*/*Page*.test.tsx` 관측 패턴

### Info (0건)

## 4. 문서 업데이트 제안

- 빈도 트리거 미발동: 동일 fingerprint가 3개 이상 파일에서 발견되지 않았다.
- 새 카테고리 트리거 미발동: 파일 네이밍은 기존 카테고리다.

## 5. 문서 작성 유도

- `docs/CONVENTIONS.md` 존재 확인 — 작성 유도 없음.

## 6. 통과 확인

- target manifest의 51개 파일은 모두 존재하고 project root 내부에 있다.
- trailing whitespace, tab indentation, EOF newline 누락, `@header` 누락은 발견되지 않았다.
- PM 실측으로 보고된 `npm run lint`, `npm run typecheck`, `npm run test`(38), `npm run build`, Electron syntax, code-scan inline 42/42 결과를 보조 증거로 반영했다.
