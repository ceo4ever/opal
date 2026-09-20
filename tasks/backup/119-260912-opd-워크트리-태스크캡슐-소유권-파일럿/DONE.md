# DONE: 워크트리 태스크 캡슐 소유권 — 생성 순서 전환과 monorepo 파일럿

## 결과

태스크 118이 깔아둔 배관에 밸브가 열렸다. `--worktree` 태스크는 이제 번호 발급 다음에 워크트리가 먼저 생기고, 태스크 폴더와 `state.json`이 그 워크트리 안에 만들어진다. 코드 변경과 태스크 캡슐이 같은 브랜치 커밋에 담기므로 브랜치 하나로 실행 증거까지 함께 리뷰·복원할 수 있다.

**차단 하나를 풀었다.** 118은 제안서 §5.4의 단일 복사본 불변식만 구현하고 §4.3의 상태 의존 해석을 빠뜨렸다. 그 결과 merge가 허브에 `tasks/{task_folder}`를 만드는 순간 `TASK_PATH_AMBIGUOUS`가 영구 발동하고, finalize 불가 → `MEMORY_INDEX_REQUEST_PENDING` 미해소 → `remove` 차단으로 연쇄됐다. `_assert_task_path_unambiguous`를 `_resolve_canonical_task_path`로 승격해 registry `attribution_state`가 `closed`일 때만 허브 merge 사본을 canonical로 반환하게 했다. 차단을 없앤 것이 아니라 상태 하나를 더 보게 한 것이며, active 3상태의 차단은 그대로다.

**계약 하나를 정정했다.** 제안서 §6.3의 `--no-ff --no-commit` 단일 merge 커밋 경로는 현행 도구로 실행할 수 없다. 그 시점에 허브 사본이 이미 존재하는데 `attribution_state`가 아직 `closed`가 아니어서, 상태 의존 해석에서도 차단이 정상 판정이기 때문이다. 단일 복사본 불변식과 구조적으로 충돌한다. 허용 경로를 `--ff-only`와 `--no-ff` 두 가지로 확정하고 귀속은 두 경우 모두 merge **전** 브랜치 finalize 커밋으로 확정한다.

**cone이 유일한 스위치임이 실측됐다.** `taskCapsuleCone`이 비어 있으면 `task_root`가 워크트리에서 허브로 탈출하고, 값이 들어가면 워크트리 자신에 착지한다. 118이 만든 장치들이 이 스위치 하나로 동시에 살아난다.

**유지된 것** — `--wt`를 쓰지 않는 실행은 변경 전과 바이트 동일하다. 118과 달리 CLI 표면을 늘리지 않아 `--help`·usage까지 예외 없이 동일했다. `task_ownership_version` 부재 태스크는 모호성 판정 자체를 건너뛰어 위치가 자동 이동되지 않는다.

**적용 경계** — 제안서 Phase 2까지다. Phase 3는 `--wt` 플래그 축 게이팅 채택으로 프로필별 batch 확산 개념이 성립하지 않아 잔여 항목이 없다. Phase 4 multi-repo는 범위 밖이다.

## 변경 파일

- `opal/tools/worktree-tool/worktree_tool.py`
- `opal/tools/worktree-tool/tests/test_worktree_tool.py`
- `opal/core/references/harness/worktree.md`
- `opal/core/references/harness/task-process.md`
- `opal/core/references/pm/dispatch-process.md`
- `opal/skills/opal-pilot-dev/SKILL.md`
- `opal/skills/opal-pilot-dev-short/SKILL.md`
- `.opal/worktree.json`
- `docs/proposals/archives/opal-worktree-task-ownership.md`
- `tasks/119-260912-opd-워크트리-태스크캡슐-소유권-파일럿/REGRESSION-EVIDENCE.md` (신설)
- `tasks/119-260912-opd-워크트리-태스크캡슐-소유권-파일럿/FIXTURE-EVIDENCE.md` (신설)
- `tasks/119-260912-opd-워크트리-태스크캡슐-소유권-파일럿/PILOT-EVIDENCE.md` (신설)
- `tasks/119-260912-opd-워크트리-태스크캡슐-소유권-파일럿/GC-CONVENTION-119.md` (신설)

파일럿 태스크 121이 별도로 `opal/core/references/opal-harness.md`·`tools.md`·`opal/skills/opal-project-init/SKILL.md`를 변경했다(커밋 `86d8dcd`).

## 검증

- 시나리오 전수 — `test-tool scenario-status` → `locked: true, total 30, passed 30, failed 0, blocked 0`. `red_required`는 S-8 하나이며 RED 증거가 기록돼 있다.
- 도구 스위트 — `worktree-tool` 83 passed / `state-tool` 425 passed·3 skipped / `memory-tool` 202 passed. 합산 **710 passed, 실패 0**. 118부터 달고 있던 선존재 실패 1건은 태스크 092의 stale 문서 단언이었고 이번에 해소됐다.
- 비워크트리 바이트 동일(C-1) — 데이터 루트를 `/private/tmp` 고정 fixture에 두고 단일 배포 경로에 base·after를 순차 install해 도구 코드만 스왑했다. 6명령 × (stdout·stderr·exit) = **18/18 바이트 동일, 정규화 0회**. 비공허성도 함께 실증(배포본 6파일 sha256이 전부 DIFF인 상태에서 출력 동일). 상세: `REGRESSION-EVIDENCE.md`.
- 수명주기 fixture — `/private/tmp` monorepo fixture에서 새 순서 전 구간·fallback 4지점 중단 주입·cone on/off·상태 의존 해석 4상태·경로 B를 `--ff-only`와 `--no-ff` 두 경로로 완주·기존 22개 태스크 폴더 변경 0건·memory/brain 경계·legacy 보존을 실측했다. D-6은 반증 실험으로 확인했다 — `--no-ff --no-commit` 중단 상태에서 finalize가 실제로 차단된다. 상세: `FIXTURE-EVIDENCE.md`.
- 실환경 파일럿 — 태스크 121이 생성 → 실행 → CLOSE → finalize → 캡슐 커밋 → merge → `finalize-attribution` → `status --set done` → `remove`까지 완주했다. 커밋 `86d8dcd`에 코드 3파일과 캡슐 8파일이 함께 있고, merge 직후 `task_path_source: hub_merged`가 관측됐다. 가드 우회 0건. 상세: `PILOT-EVIDENCE.md`.
- 배포 — 소유자가 허브 `main`에서 install 수행. 배포 누락 621파일 중 0건, 변경 6파일 source↔installed 바이트 동일. 태스크 120 산출물 롤백 위험은 실제로 발생하지 않았다.
- 컨벤션 — `opal-convention-checker` 결과 Critical 0 / High 0 (`GC-CONVENTION-119.md`). 지적된 `@header` stale 1건은 CLOSE 전 정정 완료.
- 상태 무결성 — `state-tool validate` violations 0, 임시 fixture 잔여물 0건, 운영 저장소 침범 0건.

## 회고적 학습 후보

.opal/brain/pages/concept/state-aware-path-resolution-unblocks-merge.md
.opal/brain/pages/concept/switch-first-plumbing-later-verification.md
.opal/brain/pages/concept/red-timing-follows-implementation-subject.md
.opal/brain/pages/concept/stale-doc-assertions-outlive-restructuring.md

## 참고

**AC-4·AC-9 재정의** — `.opal-task.lock`은 `docs/proposals/opal-task-run-log.md`에만 있고 구현이 0건이라 AC-4의 "동일 lock inode 관측"이 검증 불가능했다. "동일 canonical `task_path`·동일 `realpath(state.json)` 관측"으로 재정의했고 lock 도입은 실행 로그 제안서 구현 태스크로 이연한다. AC-9는 위 계약 정정에 따라 두 merge 경로로 재정의했다.

**후속 — AC-10 하드닝** — `brain_tool.finalize_brain_root()`가 `--allocator-root`의 절대경로 여부만 검사해(`brain_tool.py:315`) `.opal-worktrees/` 안 경로도 수용한다. AC-10이 집행하는 경로(CLOSE가 후보만 선언 → merge 후 허브 판정)는 정상 동작하므로 S-15는 PASS지만, "워크트리 brain 쓰기 불가"는 구조적 불변식이 아니다. 하드닝하려면 brain-tool이 registry를 읽어 허브를 알아야 하므로 도구 간 의존을 새로 만든다 — 별도 태스크 소관이다.

**후속 — Phase 4 multi-repo** — 실사용 대상이 확인됐다. `/Volumes/Data/StoreLinkStudio/pug`는 OPAL 프로젝트이면서 `workspace/` 아래 독립 `.git` 6개(`frontend`·`frontend_app`·`frontend_admin`·`backend`·`app_ios`·`app_android`, `.gitmodules` 없음)를 가진 multi-repo다. 루트 repo가 `.opal/`·`tasks/` 235파일을 추적하므로 `task_artifacts.repo` 대상이 명확하다. 다만 `.opal/worktree.json`이 없어 `worktree-tool init`부터 필요하고, 6개 repo가 baseBranch를 `main`/`develop`으로 나눠 쓰는데 단일 `baseBranch` 필드로는 표현되지 않는다 — 제안서 §8이 다루지 않은 설계 공백이다.

**후속 — `merge` 커밋 type 등재** — `docs/CONVENTIONS.md` §커밋 규칙 Type 표에 `merge`가 없다. 저장소 전역에서 095·107·108·109·118이 이미 쓰던 관례이므로 표에 행을 신설하는 편이 사실과 맞는다.

**타 태스크 영향 — GC 체커 경로** — 태스크 120이 검사 참조 문서를 `op-gc-convention` 스킬로 이관해 `opal-pilot-gc`의 디스패치 파라미터(`checklist_path`·`template_path`)가 stale이다. 이번 컨벤션 진단은 체커가 새 경로로 대체해 수행했다.
