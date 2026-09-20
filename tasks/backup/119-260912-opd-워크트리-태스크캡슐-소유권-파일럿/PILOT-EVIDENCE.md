# PILOT-EVIDENCE: 태스크 121 실환경 수명주기 완주

> W-10 산출물 | 파일럿 대상: `tasks/121-260912-opd-하네스-구형절-참조-정리`
> 배포본: 소유자가 허브 `main`(`a5bfb77`)에서 install 수행. PM이 반영 실측 확인.

## 0. 전제 확인

| 항목 | 실측 |
|---|---|
| 배포본 `_resolve_canonical_task_path` | 3건 (119 반영) |
| 배포본 `worktree.md` §상태 의존 해석 | 3건 |
| 배포본 `task-process.md` `--task-folder` | 1건 |
| 태스크 120 산출물 보존 | `op-gc-{convention,security,report}/SKILL.md` 3건 존재 (롤백 없음) |

## 1. 생성 — 새 순서 (AC-1·AC-2·AC-3)

`harness/task-process.md` 문면대로 실행했다.

1. 채번 — `memory-tool task-number --file <허브 절대경로>/.opal/MEMORY.json --bump` → `121`
2. worktree 생성 — `worktree-tool create --project-root <허브> --task 121 --skill opd --task-folder 121-260912-opd-하네스-구형절-참조-정리`
3. `mkdir -p <task_path>`
4. TASK.md 작성 (워크트리 안)
5. `state-tool init <task_path> --skill opds --worktree <worktree_root>`

**발급된 canonical metadata 6필드**

| 필드 | 값 |
|---|---|
| `worktree_root` | `.opal-worktrees/task_121` |
| `task_home` | `.opal-worktrees/task_121` |
| `task_folder` | `121-260912-opd-하네스-구형절-참조-정리` |
| `task_path` | `.opal-worktrees/task_121/tasks/121-260912-opd-하네스-구형절-참조-정리` |
| `allocator_root` | 허브 절대경로 |
| `artifact_repo` | `.` |
| `task_ownership_version` | `2` |

119 이전에는 `task_folder`·`task_path`가 `None`이었다(태스크 119 착수 시 실측).

**cone 자동 실체화** — `sparse-checkout list`에 `.opal`·`tasks` 포함, 워크트리에 두 디렉터리 실재. `.opal/worktree.json`의 `taskCapsuleCone` 활성값이 신규 슬롯에 그대로 적용됐다.

**`create`는 `task_path`를 만들지 않는다** — 2단계 직후 `ls -d <task_path>` → `No such file or directory`. D-2가 별도 `mkdir` 스텝을 둔 근거가 실환경에서 재확인됐다.

**허브 무오염** — 생성 전 구간에서 `ls -d <허브>/tasks/121-*` → `no matches`. `state.json`도 워크트리 안에만 생성됐다.

## 2. 실행 — 파일럿 주제

태스크 121의 작업은 태스크 118이 보류한 후속이다. `opal-harness.md`의 `§2.5 워크스페이스 축` 매핑 행을 제거하려면 그 번호를 인용하는 두 문서를 먼저 owner로 돌려야 했다.

- `tools.md:1028` → `harness/worktree.md` 두 절 + `harness/task-process.md` 스텝 4.5
- `opal-project-init/SKILL.md:84` → `harness/worktree.md` §모드 축과 직교하는 별개 축
- `opal-harness.md` 매핑 행 1줄 제거

결과: `opal-harness.md §2.5` 활성 인용 **0건**, 매핑 행 부재, 표 자체는 보존, `worktree-tool` **83 passed**.

**게이트가 작동한 사례** — `execute.implement` mark가 `code_scan_citation_unmet`으로 차단됐다. 실제로 `code-scan depends opal-harness.md`를 조회하니 `depended by: (none)`이었고, 이 태스크의 결합이 코드맵이 아니라 Markdown 문자열 인용임이 드러났다. 그 판정을 PLAN에 근거로 기재한 뒤 게이트가 통과했다. 형식 충족이 아니라 조회 자체가 설계 정보를 만든 경우다.

## 3. CLOSE → finalize → merge → 귀속 → 회수 (AC-6·AC-7·AC-8·AC-12·AC-13)

| 단계 | 명령 | 관측 |
|---|---|---|
| CLOSE | `state-tool mark … close.done_md --done` | `current_status: 완료(미귀속)`. 허브 `tasks/121-*` **0건**, MEMORY history 121 행 **0건** (AC-7) |
| finalize | `worktree-tool finalize --project-root <허브> --task 121` | `state: closed`, `previous_state: completed_unmerged`, `declared: [brain/index.md, brain/log.md, MEMORY.json]`, `observed: []`, `violations: []`, `committed: false`, `done_file_found: true` |
| 캡슐 커밋 | `git -C <wt> commit` | **11파일 1커밋** — 코드 3파일(`opal-harness.md`·`tools.md`·`opal-project-init/SKILL.md`) + 캡슐 8파일(TASK·PLAN·TEST-SCENARIO·DONE·STATE·state.json·test-scenario.json·coverage-input) (AC-6) |
| merge | `git merge --ff-only feat/OP-TASK-121` | 충돌 0건. 허브 `tasks/121-*`에 캡슐 출현 |
| **경로 재해석** | `worktree-tool status --project-root <허브> --task 121` | **`task_path_source: hub_merged`**, `task_path`가 허브 경로. 차단 없음 (AC-4) |
| 귀속 | `state-tool finalize-attribution <task-path> --allocator-root <허브>` | `status: created` 1회 → 재실행 `status: duplicate_skipped` (AC-8) |
| 상태 종결 | `state-tool status <task-path> --set done` | `completed_unmerged → done` |
| 회수 | `worktree-tool remove --project-root <허브> --task 121` | `forced: false`, `bypassed_guards: []` (AC-12) |

**이 표의 `hub_merged` 행이 태스크 119의 핵심 성과다.** 태스크 118 상태에서는 merge가 허브 사본을 만드는 순간 `_assert_task_path_unambiguous`가 `TASK_PATH_AMBIGUOUS`로 영구 차단하고, finalize 불가 → `MEMORY_INDEX_REQUEST_PENDING` 미해소 → `remove` 차단으로 연쇄됐다(태스크 119 ANALYSIS Q5/Q6 fixture 실측). 제안서 §4.3의 상태 의존 해석을 구현해 그 연쇄가 실환경에서 풀렸음을 확인했다.

## 4. 최종 상태

- 허브 `main` = `86d8dcd`, worktree 1건(`task_119`만 잔존), registry `task_119.json` 1건.
- MEMORY history에 `121 하네스 구형절 참조 정리 | 완료` 행 존재, `result` 보강 완료.
- 파일럿 과정에서 가드 우회 **0건**, 운영 저장소 침범 **0건**.

## 5. 파일럿 중 발견한 PM 판단 사항

**파일럿 태스크에 `opd` 풀 파이프라인(16행)을 붙인 것은 과다했다.** 문서 3파일 포인터 교체 규모에 `opds` short(11행)가 맞고, 제안서 §11 Phase 2도 "`opds` 한 프로필"을 지정했다. `state-tool init --force`로 재초기화해 교정했으며, 그 사실을 `state.json` note에 남겼다. 다음 파일럿 설계 시 주제 규모와 프로필을 함께 결정해야 한다.
