---
template: sdlc-v2
---
# PLAN: WorkStudio Project Registry

> 입력: [TASK.md](TASK.md)

## Approach

WS-F101은 기존 mock Project state와 별도로, Electron main이 소유하는 영속 Project Registry를 추가한다. Renderer는 typed preload IPC만 호출하고, 인트로의 최근 프로젝트 목록·Project 추가·유실 경로 복구·목록 제거 흐름을 이 레지스트리에 연결한다. 새 폴더 생성과 `.opal` 초기화는 이번 태스크에서 UI 안내만 유지하고 실제 생성은 하지 않는다. 근거: `tasks/128-260913-opds-워크스튜디오-프로젝트-레지스트리/TASK.md:20`, `tasks/128-260913-opds-워크스튜디오-프로젝트-레지스트리/TASK.md:24`

`code-scan scan workstudio` 결과 WorkStudio는 43개 파일로 식별되며, 핵심 변경 후보는 `workstudio/electron/main.cjs`, `workstudio/electron/preload.cjs`, `workstudio/src/workstudio/ipc.ts`, `workstudio/src/workstudio/WorkStudioApp.tsx`, `workstudio/src/workstudio/mock-adapter.ts`, 관련 테스트다. 현재 main process는 Project folder inspection과 read-only file tree IPC를 소유하고, BrowserWindow는 `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`로 구성되어 있다. 근거: `workstudio/electron/main.cjs:87`, `workstudio/electron/main.cjs:209`, `workstudio/electron/main.cjs:223`

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| Registry 소유권 | [MUST] `tasks/128-260913-opds-워크스튜디오-프로젝트-레지스트리/TASK.md` §Constraints: "영속 프로젝트 레지스트리의 읽기·쓰기는 Electron main이 소유하고 renderer는 typed preload IPC만 사용한다." Renderer는 `window.opalWorkStudio.project.*`만 호출하고 파일 시스템·Node API를 직접 사용하지 않는다. | 보안 경계와 기존 typed IPC 구조가 이미 있다. 근거: `workstudio/electron/preload.cjs:13`, `workstudio/src/workstudio/ipc.ts:48`, `workstudio/src/workstudio/ipc.test.ts:20` |
| 저장 형식 | registry 파일은 schema version을 갖는 JSON으로 저장한다. 손상 JSON, version 불일치, 필수 필드 누락은 앱 종료가 아니라 빈 registry + non-fatal recovery signal로 처리한다. | TASK가 schema version과 안전 복구를 요구한다. 근거: `tasks/128-260913-opds-워크스튜디오-프로젝트-레지스트리/TASK.md:23` |
| Project 항목 계약 | Project registry item은 `id`, `name`, `path`, `realPath`, `isOpalProject`, `agentPath?`, `pmName?`, `createdAt`, `lastAccessedAt`, `status: available\|missing`을 가진다. `realPath` 중복은 동일 항목 갱신으로 처리하고, 열기 성공 시 `lastAccessedAt`을 갱신해 내림차순 정렬한다. | AC-1~AC-3와 중복 등록 흐름을 한 계약에서 닫는다. 기존 main은 realpath와 `.opal/AGENT.md` 감지를 이미 수행한다. 근거: `workstudio/electron/main.cjs:48`, `workstudio/electron/main.cjs:65`, `workstudio/electron/main.cjs:78` |
| 목록 제거와 디스크 삭제 분리 | [MUST] `tasks/128-260913-opds-워크스튜디오-프로젝트-레지스트리/TASK.md` §Constraints: "목록 제거는 레지스트리 항목만 제거하며 디스크의 프로젝트 폴더나 파일을 삭제하지 않는다." 삭제 API 이름은 `removeRecentProject`처럼 registry 대상임을 드러내고 `fs.rm`/`unlink`류를 사용하지 않는다. | AC-6은 사용자 데이터 보존 계약이다. 근거: `tasks/128-260913-opds-워크스튜디오-프로젝트-레지스트리/TASK.md:33` |
| 유실 경로 처리 | registry load/list 시 존재하지 않는 경로는 `missing`으로 표시하고 일반 open은 차단한다. 사용자가 새 폴더를 선택해 복구하면 같은 `id`의 `realPath`, `path`, OPAL marker metadata, `lastAccessedAt`, `status`를 갱신한다. | AC-4와 AC-5를 별도 삭제/재등록이 아닌 동일 항목 복구로 만족한다. 근거: `tasks/128-260913-opds-워크스튜디오-프로젝트-레지스트리/TASK.md:31`, `tasks/128-260913-opds-워크스튜디오-프로젝트-레지스트리/TASK.md:32` |
| 범위 제외 | [MUST] `tasks/128-260913-opds-워크스튜디오-프로젝트-레지스트리/TASK.md` §Constraints: "WS-F102 이후 기능인 새 폴더 생성과 `.opal` 초기화는 구현하지 않는다." `showOpenDialog`의 `createDirectory`는 WS-F101에서 제거하거나 실제 생성으로 연결하지 않는다. | Project 생성은 백로그상 WS-F102이며, WS-F101은 기존 폴더 등록·재열기 기반이다. 근거: `workstudio/BACKLOG.md:80`, `workstudio/BACKLOG.md:81` |
| 보안 경계 유지 | [MUST] `tasks/128-260913-opds-워크스튜디오-프로젝트-레지스트리/TASK.md` §Constraints: "`contextIsolation: true`, `nodeIntegration: false` 보안 경계를 유지한다." | 기존 Electron 설정과 테스트가 이 계약을 이미 고정한다. 근거: `workstudio/electron/main.cjs:223`, `workstudio/src/workstudio/ipc.test.ts:42` |
| 문서·컨벤션 | [MUST] `docs/CONVENTIONS.md` §Citation Rules: "TASK.md / PLAN.md / ANALYSIS.md / QA 산출물 등을 작성할 때 모든 주장은 근거를 인용한다 (`{경로}:{라인}` 또는 `docs/문서명 §섹션`)." 코드 생성·수정 파일은 `code-scan target <file>` 판정에 따라 @header를 유지·작성한다. | 인용과 @header는 프로젝트 산출물 품질 게이트다. 근거: `docs/CONVENTIONS.md:222`, `docs/CONVENTIONS.md:230` |
| Worktree 재발 방지 | `.opal/worktree.json`의 `repos`에는 `workstudio`가 포함되어야 하며, WS-F101 작업본에서 WorkStudio 코드와 백로그가 빠지지 않게 유지한다. | 이번 PLAN 재시도 전 blocker가 `workstudio/` 누락이었고, 현재 설정은 `workstudio`를 포함한다. 근거: `.opal/worktree.json:3`, `.opal/worktree.json:10` |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. Electron registry gateway | opal-fe-agent | `workstudio/electron/main.cjs`, `workstudio/electron/preload.cjs`, `workstudio/src/workstudio/ipc.ts`, 신규 `workstudio/electron/project-registry.cjs` 또는 main 내부 동등 모듈 | `app.getPath("userData")` 하위 registry JSON 읽기·쓰기, schema version, atomic write, corrupt/unsupported recovery, realpath 기반 dedupe, missing 판정, register/open/remove/repair/list typed IPC를 추가한다. 기존 `chooseDirectory`는 기존 폴더 선택만 수행하고 새 폴더 생성·`.opal` 초기화로 확장하지 않는다. | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, C-1, C-2, C-3, C-4, C-5 |
| W-4. Worktree 설정과 백로그 정합 | PM 직접 | `.opal/worktree.json`, `workstudio/BACKLOG.md` | `.opal/worktree.json`의 `repos`에 `workstudio`가 포함된 상태를 유지해 WS-F101 작업본이 WorkStudio 코드와 백로그를 포함하도록 한다. `workstudio/BACKLOG.md`의 WS-F101 실행 태스크 열을 `tasks/128-260913-opds-워크스튜디오-프로젝트-레지스트리/`로 연결하고 상태 전환은 실제 EXECUTE/merge 진행에 맞춘다. | 없음 | P1 | AC-7, AC-8 |
| W-2. Renderer recent Project flow | opal-fe-agent | `workstudio/src/workstudio/WorkStudioApp.tsx`, `workstudio/src/workstudio/types.ts`, `workstudio/src/workstudio/mock-adapter.ts` | 최초 실행 인트로의 "최근 프로젝트"를 registry list로 채우고 last access 정렬·missing badge·open disabled·repair action·remove-from-list action을 렌더한다. 성공 open은 현재 workspace Project로 전환하고 file tree root가 선택 Project를 보게 한다. mock adapter의 seed/demo state는 데모 진입에만 남기고 Project Registry의 영속 사실로 쓰지 않는다. | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-8, C-1, C-3, C-5 |
| W-3. Registry regression tests | opal-fe-agent | `workstudio/electron/main.test.mjs`, `workstudio/src/workstudio/ipc.test.ts`, `workstudio/src/workstudio/FirstRunWelcome.test.tsx`, `workstudio/src/workstudio/WorkStudioApp.test.tsx` | 정상 등록·취소·중복 등록·손상 registry·unsupported version·missing path·repair·remove without disk delete를 자동 테스트로 고정한다. 기존 first-run welcome, Project 선택, Files tree, secure IPC 회귀 테스트도 유지한다. 검증 명령은 `npm --prefix workstudio run test`, `npm --prefix workstudio run typecheck`, `npm --prefix workstudio run electron:syntax`다. | W-1, W-2 | P3 | AC-7, AC-8, C-1, C-2, C-3, C-4, C-5 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. renderer localStorage mock snapshot과 main registry가 서로 다른 Project 사실을 저장할 수 있다 | 최근 프로젝트 목록, active Project, 파일 트리 root가 서로 다르게 보일 수 있다 | 재실행 후 사용자가 다른 Project로 복원되거나 missing 상태가 가려진다 | W-2에서 registry는 Project 목록의 실제 source로, localStorage는 UI/demo 상태로 역할을 분리한다. |
| H-2. registry write 중 앱 종료나 JSON 손상 발생 | 앱 시작 시 registry load가 예외를 던질 수 있다 | WorkStudio 최초 화면 진입 실패 | W-1에서 temp file + rename 방식과 corrupt recovery를 구현하고, W-3에서 손상 데이터 테스트를 추가한다. |
| H-3. missing path 복구가 새 항목 생성으로 처리될 수 있다 | 동일 Project가 중복되고 last access 정렬이 틀어진다 | 사용자가 기존 항목을 복구했는데 히스토리가 분리된다 | W-1의 repair API는 기존 `id` 갱신만 허용하고, W-2는 missing 항목의 repair CTA에서만 호출한다. |

## Release and recovery

- 적용 순서: P1에서 W-1과 W-4를 먼저 끝낸 뒤, P2 W-2로 renderer 흐름을 연결하고, P3 W-3으로 회귀 테스트를 고정한다.
- 검증 범위: 결정론 검증은 `~/.opal/tools/state-tool/run.sh verify <task-folder> --plan-contract-check`, `~/.opal/tools/state-tool/run.sh verify <task-folder> --code-scan-citation-check`, `npm --prefix workstudio run test`, `npm --prefix workstudio run typecheck`, `npm --prefix workstudio run electron:syntax`를 사용한다.
- 실측 경계: registry 파일은 사용자 data directory에만 생성하며, 테스트는 임시 userData/fixture 경로를 써 실제 사용자 registry를 오염시키지 않는다.
- 실패 시: main registry IPC가 불안정하면 W-2 변경을 되돌려 기존 mock/demo 진입만 유지할 수 있어야 한다. registry 파일 손상은 삭제 없이 recovery path가 빈 목록으로 격리하며, 원본 파일을 덮기 전 백업 또는 quarantine 이름으로 보존하는 구현을 우선한다.
