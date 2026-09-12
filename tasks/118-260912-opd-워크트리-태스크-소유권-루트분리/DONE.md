# DONE: 워크트리 태스크 소유권 — cone 착지 실측과 허브 루트 보정 제거

## 결과

`.opal-worktrees` 세그먼트를 발견하면 무조건 허브로 보내던 정규화가 활성 계약에서 사라지고, 루트가 용도별 두 개로 분리됐다. 태스크 문서·설정·코드 스캔을 해석하는 `task_root`와, 채번·귀속 쓰기에만 쓰는 `allocator_root`다. `allocator_root`는 cwd·조상·경로 문자열로 추론하지 않고 `worktree-tool`이 발급한 metadata로만 전달된다.

네 런타임에 중복 구현돼 있던 보정이 제거됐다 — `code-scan.js`의 `hubRootFromPath`, `event_loader.py`의 `_hub_root`, `brain_tool.py`의 `hub_root`/`_hub_cwd`, `dashboard/backend/paths.py`의 `hub_root`(프로덕션 호출자 0건이던 죽은 코드). 세 런타임이 공유하던 골든표 `hub-root-cases.json`과 그 소비 스위트 4개도 각 런타임의 착지 계약 테스트로 교체됐다.

`state-tool`의 `find_project_root`는 `task_root`로 개명되고 하위호환 alias 없이 호출 3곳이 갱신됐다. CLOSE mark가 MEMORY history를 즉시 append하던 동작은 제거되고 `completed_unmerged`만 확정하며, 귀속은 신규 `finalize-attribution`이 명시 `allocator_root`를 받아 전담한다. `memory-tool`은 워크트리 경로 쓰기 6종을 거부하고, 신규 메모리만 태스크 캡슐의 index 요청으로 지연한 뒤 허브 finalize에서 title 동등성 판정으로 1회 반영한다. `worktree-tool`은 canonical path 6필드를 발급하고, 허브·워크트리 중복 폴더를 차단하며, 미처리 index 요청이 남은 슬롯의 회수를 막고, finalize 재진입을 전체 dirty가 아니라 선언 집합 부분집합(`S ⊆ D`)으로 판정한다.

**유지된 것** — `--wt`를 쓰지 않는 실행의 동작과 출력은 변경 전과 바이트 동일하다. 신규 기능은 전부 "인자·설정이 주어졌을 때만 켜지는 분기"로 설계됐다: cone 확장 키 `taskCapsuleCone`의 기본값은 빈 리스트, `resolve_task_dir`의 다중 루트는 keyword-only 기본 `None`, `memory-tool`의 `pending_requests`는 신규 인자가 없으면 응답 키 자체를 만들지 않는다. 기존 활성 슬롯(115·116·118)은 `task_ownership_version` 부재로 legacy 판정되어 위치가 자동 이동되지 않으며, 실 허브에서 Console의 registry 화이트리스트는 빈 배열을 반환해 현행 동작이 그대로다.

**적용한 경계** — 제안서의 Phase 0(cone 착지 실측)과 Phase 1(보정 제거·루트 분리)까지다. Phase 2 monorepo pilot, Phase 3 확산, Phase 4 multi-repo와 태스크 생성 순서 재정렬은 범위 밖이다. 운영 worktree의 기본 cone은 이 태스크에서 활성화하지 않았다 — 실측은 전부 disposable fixture와 shadow cone에서만 수행했다.

## 변경 파일

- `opal/core/references/harness/worktree.md` (허브 루트 해석 규칙 → task/allocator root 계약·canonical path 발급·cone 확장·Phase 1 legacy gate 4개 절로 교체)
- `opal/core/references/harness/done-template.md` (신설 — 표준 CLOSE DONE 템플릿 SSOT + 회고적 학습 후보 계약)
- `opal/core/references/harness/task-process.md`
- `opal/core/references/harness/memory-learning.md`
- `opal/core/references/harness/observability.md`
- `opal/core/references/opal-harness.md`
- `opal/core/references/hub-root-cases.json` (삭제)
- `opal/skills/opal-pilot-dev/SKILL.md`
- `opal/tools/worktree-tool/worktree_tool.py`
- `opal/tools/worktree-tool/tests/test_worktree_tool.py`
- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/tests/test_state_tool.py`
- `opal/tools/state-tool/README.md`
- `opal/tools/state-tool/schema/state.schema.json`
- `opal/tools/memory-tool/memory_tool.py`
- `opal/tools/memory-tool/tests/test_memory_tool.py`
- `opal/tools/event-loader/event_loader.py`
- `opal/tools/event-loader/README.md`
- `opal/tools/event-loader/tests/test_event_loader_worktree_root.py` (신설)
- `opal/tools/brain-tool/brain_tool.py`
- `opal/tools/brain-tool/tests/test_brain_tool.py`
- `opal/tools/code-scan/code-scan.js`
- `opal/tools/code-scan/tests/test-hub-root.js`
- `opal/tools/code-scan/tests/test-scan-root-landing.js` (신설)
- `dashboard/backend/paths.py` (삭제)
- `dashboard/backend/scanner.py`
- `dashboard/backend/routers/tasks.py`
- `dashboard/backend/routers/doctor.py`
- `dashboard/backend/tests/test_paths.py` (삭제)
- `dashboard/backend/tests/test_scanner.py`
- `dashboard/backend/tests/test_routers.py`
- `dashboard/backend/tests/test_parsers.py`
- `dashboard/backend/tests/test_adapters.py`
- `docs/CONVENTIONS.md`
- `docs/PROJECT.md`
- `docs/proposals/opal-worktree-task-ownership.md`
- `tasks/118-260912-opd-워크트리-태스크-소유권-루트분리/PHASE0-BASELINE.md` (신설)
- `tasks/118-260912-opd-워크트리-태스크-소유권-루트분리/REGRESSION-EVIDENCE.md` (신설)
- `tasks/118-260912-opd-워크트리-태스크-소유권-루트분리/GC-CONVENTION-118.md` (신설)

## 검증

- 시나리오 전수 — `test-tool scenario-status` → `total 26 / passed 26 / failed 0 / blocked 0`. RED 대상 13건은 `scenario-red`에 실제 실패 출력을 기록한 뒤 `scenario-lock`(2026-09-12T09:54:49+09:00)을 통과하고 GREEN 전환됐다.
- 도구 스위트 — `worktree-tool` 74 passed / 1 failed(선존재, 아래 §참고) · `state-tool` 404 passed / 3 skipped · `memory-tool` 202 passed · `brain-tool` 156 passed · `event-loader` 11 passed / `test_event_loader_worktree_root.py` 3 passed · `code-scan` `test-hub-root.js` 4 + `test-scan-root-landing.js` 3 pass.
- Console BE — shadow cone fixture에서 변경 전 383 passed / 변경 후 376 passed·0 failed. 증분 −7 = `test_paths.py` 제거 −9 + S-16 신규 +2. 경로 순회 부정 케이스 TS-045 12건은 테스트 무수정으로 통과.
- 비워크트리 바이트 동일(C-1) — 단일 절대경로에 base 트리를 두고 캡처한 뒤 같은 경로에 변경 코드만 덮어쓰고 재캡처해 `cmp`로 직접 판정(정규화 0회). W-14가 19/19, TEST 워커가 독립 재실행으로 11/11, 양쪽 모두 stdout·stderr·exit code 전부 일치.
- 배포(C-2) — 격리 HOME에 `scripts/install-mac.sh` 실제 실행(exit 0). 신설 `harness/done-template.md` 배포 확인, 삭제 2건(`hub-root-cases.json`·`dashboard/backend/paths.py`) 배포본 전파 확인, `harness/` 파일 목록과 `opal/tools/` 전체 `find` 목록 소스↔배포본 diff 0줄.
- 제거 심볼 전수 — `_hub_root` 0건 / `hub-root-cases` 0건 / `§2.5 (4)` 0건. 잔존 `hub_root` 2건·`hubRootFromPath` 3건은 전부 "심볼이 제거됐음"을 단언하는 가드(`test_brain_tool.py:2528-2529`, `test-hub-root.js:153,156,157`)이며 서술형 잔재는 0건이다.
- 컨벤션 — `opal-convention-checker` 결과 Critical 0 / High 0 (`GC-CONVENTION-118.md`). 지적된 `@header` stale 2건은 CLOSE 전 정정 완료.
- 머지 적합성 — 118 패치를 태스크 117이 포함된 `main`(`5227f65`)에 `git apply --check --3way` → 충돌 0건.

## 회고적 학습 후보

.opal/brain/pages/concept/worktree-task-root-allocator-root-split.md
.opal/brain/pages/concept/absence-assertion-is-enforcement-not-residue.md
.opal/brain/pages/concept/byte-identical-proof-requires-data-root-fixed.md
.opal/brain/pages/concept/rename-without-alias-surfaces-missed-callers.md
.opal/brain/pages/concept/worktree-workspace-isolation-axis.md

## 참고

**릴리스 선결 조건 [MUST]** — 브랜치 `feat/OP-TASK-118`의 base는 `e8b6c4f`이고 허브 `main`은 `5227f65`로 앞서 있다. 그 델타에 태스크 117의 `event_loader.py` 변경이 포함되고, `install_opal()`은 대상 디렉터리를 `rm -rf` 후 복사한다. **현 워크트리 소스로 실 `~/.opal/`에 install하면 117이 배포한 event-loader가 조용히 롤백된다.** 배포본 md5가 `main` 판본과 일치함을 실측 확인했다. 실 배포는 118을 `main` 위로 rebase 또는 merge한 뒤에만 수행한다.

**worktree 회수** — `.opal-worktrees/task_118`은 머지 대기 상태다. 커밋·머지는 소유자 권한이므로 수행하지 않았다. 머지·PR 처리 후 `~/.opal/tools/worktree-tool/run.sh remove --project-root <루트> --task 118`로 회수한다.

**Phase 2 이연** — 제안서 §6.1의 태스크 생성 순서 재정렬(번호→worktree→task folder→state init)과 `harness/task-process.md` 스텝 4.5 개정. `worktree-tool` 스위트의 `test_s24_pipeline_flag_flows_from_create_into_state` 1건이 이 미적용 때문에 실패하며, 허브 base에서도 동일하게 실패함을 확인했다.

**Phase 2 이연** — `completed_unmerged → done` 전이의 호출 지점. `state-tool`의 상태 전이 그래프와 `finalize-attribution`은 구현됐으나, 파이프라인의 어느 스텝이 `status --set done`을 호출할지는 배선 문제이며 생성 순서 재정렬과 함께 결정한다.

**미처리 — 타 세션 점유** — `docs/proposals/opal-task-run-log.md`의 허브 루트 세그먼트 전제 문장을 새 계약 포인터로 교체하는 작업. 이 태스크 진행 중 다른 세션이 해당 파일을 재작성 중이어서 손대지 않았다(AC 미연결 항목).

**후속 — 제안서 아카이브 보류** — `docs/proposals/opal-worktree-task-ownership.md`의 잔여 인용은 0건이지만 Phase 2~4가 미적용이므로 `적용완료` 아카이브 대상이 아니다. 상태 어휘만 4종 규칙(`제안`·`검토`·`적용완료`·`폐기`)에 맞춰 정정했다. Phase 4 완료 시 `docs/proposals/archives/`로 이관한다.

**후속 — `§2.5` 호환 매핑 행** — `opal-harness.md:56`의 매핑 행은 `opal/core/references/tools.md:1028`과 `opal/skills/opal-project-init/SKILL.md:84`가 여전히 인용하므로 제거하지 않았다. 두 인용처를 owner 문서(`harness/worktree.md`)로 직접 돌린 뒤에야 행을 걷어낼 수 있다.

**후속 — 선재 변경이력 표** — `harness/memory-learning.md`의 `## 변경이력` 표는 선재분이며 이 태스크가 추가하지 않았다. 프로젝트 메모리의 "변경이력 제거 A안 확정" 범위에서 별도로 처리한다.
