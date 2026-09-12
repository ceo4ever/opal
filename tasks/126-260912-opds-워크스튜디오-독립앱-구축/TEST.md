---
template: sdlc-v2
---
# TEST: OPAL WorkStudio 독립 앱 구축

> 입력: [TEST-SCENARIO.md](TEST-SCENARIO.md), [PLAN.md](PLAN.md)

## Verdict

All Pass.

- `test-tool scenario-status`: locked=true, total=9, passed=9, failed=0, blocked=0, awaiting_human=0.
- RED-first 대상 6개(S-3~S-8)는 모두 사전 RED 증거가 lock된 상태에서 GREEN 검증을 통과했다.
- 보안 빠른 스캔: `apiKey|api_key|secret|password|token\s*=|BEGIN (RSA|OPENSSH|PRIVATE)` 패턴 0건.

## Commands

| Scope | Command | Exit | Evidence |
|---|---:|---:|---|
| WorkStudio | `npm run lint` | 0 | ESLint completed with no findings. |
| WorkStudio | `npm run typecheck` | 0 | `tsc -b --noEmit` completed. |
| WorkStudio | `npm run test` | 0 | Vitest: 3 test files, 38 tests passed. |
| WorkStudio | `npm run build` | 0 | `tsc -b && vite build` completed; `dist/index.html` generated. |
| WorkStudio | `npm run electron:syntax` | 0 | `node --check electron/main.cjs` completed. |
| WorkStudio | `node --check electron/preload.cjs` | 0 | Preload syntax check completed. |
| Dashboard | `npm run lint` | 0 | ESLint completed with no findings. |
| Dashboard | `npm run typecheck` | 0 | `tsc -b --noEmit` completed. |
| Dashboard | `npm run test` | 0 | Vitest: 9 test files, 123 tests passed. |
| Dashboard | `npm run build` | 0 | `tsc -b && vite build` completed. |
| Dashboard | `npm run electron:syntax` | 0 | `node --check electron/main.cjs` completed. |
| Static | `rg workbench/WorkbenchApp|workbench=1|OPAL_WORKBENCH|src/workbench dashboard/frontend` | 1 | No matches; Dashboard Workbench coupling absent. |
| Static | `find dashboard/frontend/src/workbench -maxdepth 1 -type f -print` | 0 | No files returned. |
| Static | `rg WorkStudio docs/PROJECT.md docs/ARCHITECTURE.md` | 0 | WorkStudio ownership and Console boundary documented. |

## Scenario Results

| ID | Result | Evidence summary |
|---|---|---|
| S-1 | PASS | WorkStudio lint/typecheck/test/build/electron syntax passed; title is `OPAL WorkStudio`; Dashboard runtime import absent. |
| S-2 | PASS | Dashboard lint/typecheck/test/build/electron syntax passed; Workbench query/import/source remnants absent. |
| S-3 | PASS | Project add and TASK add are separate controls; preload success/cancel/error flow passed. |
| S-4 | PASS | Typed preload, secure Electron main options, OPAL marker inspection, duplicate/root escape/read_failed/too_large file IPC contracts passed. |
| S-5 | PASS | PM Coordination renders speaker names, initials/avatar, stable color tokens, and structured system cards. |
| S-6 | PASS | Independent Terminal is shell-like with scrollback/history; Agent CLI remains read-only. |
| S-7 | PASS | Simple Project Files uses read-only IPC tree and renders success/empty/read_failed/too_large without create/delete actions. |
| S-8 | PASS | Composite Project Files renders child Project/repository roots instead of an empty panel. |
| S-9 | PASS | `docs/PROJECT.md` and `docs/ARCHITECTURE.md` match WorkStudio/Dashboard ownership boundary. |

## Warnings And Boundaries

- WorkStudio and Dashboard Vite builds passed with chunk-size warnings over 500 kB. This is not a functional failure but should be considered if startup/download size becomes important.
- WorkStudio Vitest emitted Vite native config loader warnings for `__dirname` and Node `--localstorage-file` warnings. Tests still exited 0.
- Renderer preload and OS dialog behavior were verified with mock/static Electron contract tests. A real native dialog smoke test was not run in this worker.
- PTY is intentionally out of scope: independent Terminal is a deterministic simulated shell, not a real PTY.
- PM Runtime/Agent Runtime integration is out of scope for this task; Agent CLI remains read-only simulated observation.
- WorkStudio internal compatibility names such as `WorkbenchState` remain in the new app code. They do not create Dashboard coupling, but can be renamed in a later cleanup if the product naming pass needs to be exhaustive.

## Artifacts

- Scenario SSOT: [test-scenario.json](test-scenario.json)
- Test report: [TEST.md](TEST.md)

## Addendum: First-Run Onboarding

요청 후속으로 저장 상태가 없는 최초 실행 Welcome 화면을 추가 검증했다. 기존 locked S-1~S-9는 변경하지 않고 [ADDITIONAL-WORK-FIRST-RUN.md](ADDITIONAL-WORK-FIRST-RUN.md)를 보강 계약으로 둔다.

| Scope | Command | Exit | Evidence |
|---|---:|---:|---|
| RED | `npm run test -- FirstRunWelcome.test.tsx` | 1 | 구현 전 4 tests failed; welcome dialog/action buttons absent. |
| WorkStudio | `npm run test -- FirstRunWelcome.test.tsx WorkStudioApp.test.tsx ipc.test.ts` | 0 | Vitest: 3 test files, 41 tests passed. |
| WorkStudio | `npm run lint` | 0 | ESLint completed with no findings. |
| WorkStudio | `npm run typecheck` | 0 | `tsc -b --noEmit` completed. |
| WorkStudio | `npm run test` | 0 | Vitest: 4 test files, 42 tests passed. |
| WorkStudio | `npm run build` | 0 | `tsc -b && vite build` completed. |
| WorkStudio | `npm run electron:syntax` | 0 | `node --check electron/main.cjs` completed. |
| Dashboard | `npm run lint` | 0 | ESLint completed with no findings. |
| Dashboard | `npm run typecheck` | 0 | `tsc -b --noEmit` completed. |
| Dashboard | `npm run test` | 0 | Vitest: 9 test files, 123 tests passed. |
| Dashboard | `npm run build` | 0 | `tsc -b && vite build` completed. |
| Static | `code-scan validate --changed workstudio/src/workstudio/WorkStudioApp.tsx,workstudio/src/workstudio/FirstRunWelcome.test.tsx --json` | 0 | inline coverage 100%, violations 0. |

### Addendum Scenario Results

| ID | Result | Evidence summary |
|---|---|---|
| AW-FR-1 | PASS | 최초 실행 Welcome dialog에 `기존 프로젝트 열기`, `새 프로젝트 만들기`, `데모 둘러보기`가 노출된다. |
| AW-FR-2 | PASS | 저장된 최근 Project가 없으면 `최근 프로젝트가 없습니다` empty state가 노출된다. |
| AW-FR-3 | PASS | 기존 Project 선택 취소 시 온보딩이 유지되고, 성공 시 Workspace로 진입하며 등록 Project/PM이 보인다. |
| AW-FR-4 | PASS | `데모 둘러보기`는 seed Workspace로 진입하고 `opal.workstudio.mock.v1` 상태를 기록해 재실행 시 Welcome을 반복하지 않는다. |
| AW-FR-5 | PASS | WorkStudio 42 tests와 Dashboard 123 tests가 모두 통과했다. |
