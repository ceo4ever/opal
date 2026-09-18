---
template: sdlc-v2
---
# ANALYSIS: 워크트리 태스크 캡슐 소유권 — 생성 순서 전환과 monorepo 파일럿

> 입력: [TASK.md](TASK.md) | 조사 기준: `main` @ `48f958d`, 2026-09-12 확인. 실측은 `/private/tmp/.../scratchpad/q119`(cone on)·`q119b`(cone on→off) 두 Git fixture에서 `git -C`로만 수행(C-8).

## §0 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | worktree.md | `opal/core/references/harness/worktree.md` | 루트 소유권·cone·canonical path 규범 SSOT |
| D-2 | 설계 | task-process.md | `opal/core/references/harness/task-process.md` | 생성 순서 원문(변경 대상) |
| D-3 | 설계 | done-template.md | `opal/core/references/harness/done-template.md` | `S ⊆ D` 선언 집합 계약 |
| D-4 | 설계 | dispatch-process.md | `opal/core/references/pm/dispatch-process.md` | 워커 경로 주입 계약 |
| D-5 | 소스 | worktree_tool.py | `opal/tools/worktree-tool/worktree_tool.py` | 발급·cone·finalize·guard |
| D-6 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | `task_root`·`init --worktree`·귀속·상태 전이 |
| D-7 | 소스 | memory_tool.py | `opal/tools/memory-tool/memory_tool.py` | 워크트리 쓰기 거부·index 요청 |
| D-8 | 소스 | brain_tool.py / event_loader.py | `opal/tools/brain-tool/brain_tool.py`, `opal/tools/event-loader/event_loader.py` | cone 활성화 소비자 |
| D-9 | 설계 | opal-pilot-dev SKILL | `opal/skills/opal-pilot-dev/SKILL.md` | `opd`/`opds` 프로필 분기·CLOSE 스텝 |
| D-10 | 설계 | 제안서(아카이브) | `docs/proposals/archives/opal-worktree-task-ownership.md` | §6.1·§6.3·§11 Phase 2 설계 원천 |

## Findings

| 질문 | 확인한 사실 | 근거 | 설계에 미치는 영향 |
|---|---|---|---|
| **Q1** 생성 순서 원문 위치 | 순서를 서술하는 문단은 `task-process.md` §태스크 번호 채번 규칙 3·4항(폴더 생성 → TASK.md), §오케스트레이터 공통 영역 스텝 4.5(worktree create), 스텝 5(`state init`) **세 곳뿐**이다. | `opal/core/references/harness/task-process.md:17-36`, `:38-53`, `:55-70` | AC-1 변경 대상이 이 3문단으로 확정된다. 재정렬은 4.5를 채번 3항 앞으로 끌어올리고 3항을 "워크트리 안 폴더 생성"으로 바꾸는 편집이다. |
| **Q1** 오케스트레이터 자체 서술 | `--wt`/worktree-tool을 소비하는 SKILL은 `opal-pilot-dev` **하나**다. 그 SKILL은 생성 순서를 재서술하지 않고 CLOSE 스텝 5에서 `worktree-tool status`만 호출한다. `opal-pilot-project-dev`·`-loop`·`-sdd`의 "worktree"는 `.worktrees/{id}/`를 쓰는 무관한 병렬 격리 서술이고 worktree-tool을 호출하지 않는다. | `opal/skills/opal-pilot-dev/SKILL.md:301-305`; `opal/skills/opal-pilot-project-dev/SKILL.md:513-522`, `opal-pilot-project-loop/SKILL.md:494`, `opal-pilot-sdd/SKILL.md:240-242` | 순서 전환의 SKILL 측 변경 후보는 `opal-pilot-dev` 1건으로 좁혀진다. 나머지 pilot은 회귀 경계(무변경 확인)로만 둔다. |
| **Q1** 채번 호출의 루트 취약점 | 채번 예시가 상대경로 `--file .opal/MEMORY.json`이다. 새 순서에서 PM cwd가 워크트리면 이 경로가 cone 사본을 가리키고 `task-number`는 `WORKTREE_WRITE_REJECTED`로 거부된다(실측). | `task-process.md:22-24`; `memory_tool.py:1855`; 실측 fixture q119 | 채번 문단에 **allocator 절대경로 명시**를 강제해야 한다. 순서만 바꾸고 경로를 그대로 두면 새 순서 1스텝에서 즉시 실패한다. |
| **Q2** `--task-folder` 배선 | 인자·검증·발급이 모두 구현돼 있다: `--task-folder`(dest `task_folder`), basename 전용 검증, 6필드 발급 + 불변식 검증. 실측에서 `task_folder`/`task_path`가 정상 발급됐다. 파이프라인 스텝 4.5의 `create` 예시에는 이 인자가 **없다**. | `worktree_tool.py:1534`, `:667-682`, `:684-735`, `:855-858`; `task-process.md:41-46`; 실측 `create ... --task-folder 002-260912-opds-파일럿` → `task_path` 발급 | 스텝 4.5 명령 블록에 `--task-folder <폴더명>` 추가가 필요 변경이다. 인자 신설은 불필요. |
| **Q2** 폴더명 확정 시점 | `op-task`는 `task_path`를 **입력으로 받고**, 폴더 채번은 호출자/하네스 소유라고 명시한다 → 폴더명은 TASK.md 작성 전에 이미 PM이 확정한다(현행 순서도 3항 폴더 생성 → 4항 TASK.md). | `~/.opal/skills/op-task/SKILL.md` §실행 계약 2항, §프로세스 2 | 폴더명 확정 시점이 순서 전환의 제약이 **아니다**. `create --task-folder`에 넘길 값이 이미 존재한다. |
| **Q2** `create`는 폴더를 만들지 않는다 | 발급 직후 `task_path` 디렉토리는 미존재(실측 `task_path exists? no`). 발급은 경로 계약만 확정한다. | 실측 fixture q119 | 새 순서에 "워크트리 안 폴더 생성" 스텝이 **별도로** 필요하다. `create` 성공이 폴더 생성을 뜻하지 않는다. |
| **Q3** 프로필 단위 분기 가능성 | `opd`와 `opds`는 **한 SKILL**(`opal-pilot-dev`)이 `references/pipeline.json` / `pipeline-short.json`으로 분기해 수행한다. 생성 순서는 두 프로필이 공유하는 `task-process.md`가 소유하므로, 프로필 단위 부분 활성화는 순서 원문을 복제해야만 가능하다. | `opal/skills/opal-pilot-dev/SKILL.md:4-5`, `:36-55`; `opal/skills/opal-pilot-dev/references/{pipeline.json,pipeline-short.json}` | 프로필 축 게이팅은 SSOT 복제를 강요한다. **게이트를 `--wt` 플래그 축으로 두는 것을 권고**한다 — `--wt`는 `opal-pilot-dev` 외 어디서도 소비되지 않으므로 "한 프로필" 범위가 사실상 보장된다. |
| **Q3** 중복 SKILL 리스크 | `opal-pilot-dev-short`가 별도 SKILL로 존재·배포돼 있고 description에서 `opds`를 자기 트리거로 선언한다(`--skill opds`로 `state init`까지 호출). 반면 `opal-pilot-dev`도 `opds`를 자기 트리거로 선언한다. | `opal/skills/opal-pilot-dev-short/SKILL.md:2-6`, `:249`; `opal/skills/opal-pilot-dev/SKILL.md:4-5`; 두 스킬 모두 `~/.opal/skills/`에 배포됨 | `opds`가 어느 SKILL로 라우팅될지 비결정적이다. 파일럿 대상을 `opds`로 **명명**하면 순서 미전환 SKILL로 빠질 수 있다. 대상을 SKILL 이름(`opal-pilot-dev`)으로 지정해야 한다. |
| **Q4** `state init`의 캡슐 경로 수용 | 워크트리 안 `task_path`를 그대로 받아 `state.json`/`STATE.md`를 생성한다(실측 `ok: true`). `--worktree`는 별개 인자로 **코드 작업본 절대경로**를 `state["worktree"]`에 조건부 저장할 뿐 task path 해석에 관여하지 않는다. | `state_tool.py:1422-1425`, `:3989-3990`; 실측 `state.json` = `{task_id, skill, mode, ..., worktree: <wt_root>}` | `--worktree` 의미는 변경 불필요. 새 순서에서 `<task-path>`만 워크트리 안 경로로 바뀐다. |
| **Q4** `task_root` 착지 (핵심 플립) | **cone on**: `task_root(워크트리 task path)` = **워크트리 자신**. **cone off**: 같은 경로에서 **허브**로 탈출한다(`.opal/MEMORY.json` 앵커가 워크트리에 없어 조상 탐색이 허브까지 올라감). 두 값을 같은 fixture에서 대조 실측했다. | `state_tool.py:730-744`; 실측 q119 → `.../task_002`, q119b task_004 → `.../hub` | cone 활성화가 `task_root` 계약을 실제로 켜는 **유일한** 스위치다. AC-3과 AC-4는 같은 변경의 두 관측면이며 분리 구현할 수 없다. |
| **Q4** cone 실체화 범위 | cone `[".opal","tasks"]`로 `.opal/AGENT.md`·`MEMORY.json`·`code-scan.json`·`worktree.json`·`brain/**`과 `tasks/**`가 전부 실체화된다(sparse-checkout cone 모드, gitignore 무관 — 추적 파일 기준). 허브 현황은 `.opal` 추적 파일 357건, `tasks` 1143건. | `worktree_tool.py:948-952`; `git ls-files .opal` = 357, `git ls-files tasks` = 1143; 실측 sparse list = `.opal src tasks` | 워크트리 1개당 약 1500 파일이 추가 실체화된다. `.opal/worktree.json` 사본도 함께 내려오므로 워크트리 안에서 worktree-tool을 호출하면 자신을 허브로 오인할 여지가 있다(중첩 설정 위험). |
| **Q5** finalize 두 도구의 역할 분담 | `worktree-tool finalize`는 **워크트리 안에서** `S ⊆ D`를 판정하고 관측 경로만 stage해 `chore(opal): finalize task NNN attribution` 단일 커밋을 **브랜치에** 만든 뒤, meta의 `memory_index_requests_resolved`에 append하고 캡슐 요청을 `applied`로 바꾼다. `state-tool finalize-attribution <task-path> --allocator-root <abs>`는 **허브** `.opal/MEMORY.json`에 history 1행을 멱등 append한다(동일 path 존재 시 `duplicate_skipped`). 둘은 서로를 호출하지 않는다. | `worktree_tool.py:1388-1508`; `state_tool.py:2277-2310`, `:789-840`; 실측 q119b finalize → `committed: true`, `state: closed` | 두 명령 모두 CLOSE 이후 호출자가 없다. 파이프라인에 **두 호출 지점**을 별도로 접합해야 하며 순서 의존이 있다(아래 deadlock 항 참조). |
| **Q5** `status --set done` 미호출 (118 이월) | 전이 그래프에 `completed_unmerged → done`이 있고 `--set` choices에도 `done`이 있다. CLOSE 마지막 행 mark는 `completed_unmerged`까지만 확정하고, `finalize-attribution`은 `current_status`를 **건드리지 않는다**. 이 전이를 호출하는 문서·SKILL 지점이 전수 조사에서 0건이다. | `state_tool.py:250-257`, `:1952-1957`, `:2292-2310`, `:4094-4096` | AC-13 수명주기가 `completed_unmerged`에서 영구 정지한다. merge 확인 후 `status --set done`을 호출할 주체를 파이프라인에 신설해야 한다(권고: `finalize-attribution` 성공 직후 같은 스텝). |
| **Q5·Q6** **merge 후 finalize 구조적 차단 (blocking)** | merge가 허브에 `tasks/{task_folder}`를 만드는 순간 `cmd_status`와 `cmd_finalize`가 **둘 다** `TASK_PATH_AMBIGUOUS`로 거부된다(워크트리 사본과 허브 사본 2후보). `cmd_remove`는 이 가드를 호출하지 않아 통과한다. 결과: merge 후에는 finalize가 영구 불가 → `MEMORY_INDEX_REQUEST_PENDING`이 해소되지 않아 `remove`도 차단(실측 path A). | `worktree_tool.py:1035-1057`, `:1063`(status), `:1399`(finalize), `cmd_remove`는 미호출; 실측 q119 path A → finalize `TASK_PATH_AMBIGUOUS`, remove `MEMORY_INDEX_REQUEST_PENDING` | 제안서 §6.3의 "merge 확인 → finalize" 순서는 현행 도구로 **실행 불가능**하다. PLAN은 (a) finalize를 merge **앞**으로 옮기거나 (b) 가드에 merge 산물 예외를 넣거나 둘 중 하나를 결정해야 한다. |
| **Q6** 두 merge 경로 실측 | **경로 B(FF 후 finalize 커밋)**: finalize(merge 전) → 캡슐 커밋 → `git merge --ff-only` → `remove` **성공**. 수명주기가 실제로 닫힌다. **경로 A(`--no-ff --no-commit`)**: merge 자체는 성공(`Automatic merge went well; stopped before committing`)하고 허브에서 brain/MEMORY 후처리 후 단일 merge 커밋도 만들어지지만, 그 뒤 `worktree-tool finalize`가 위 차단으로 실패한다. | 실측 q119b(경로 B 전 구간 ok), q119(경로 A merge ok → finalize 차단) | 현행 도구는 "단일 merge 커밋 안에 귀속 확정"(경로 A)을 지원하지 않는다 — finalize는 **항상** 워크트리 브랜치에 별도 커밋을 만든다. AC-9는 경로 A의 의미를 재정의하거나 도구를 바꿔야 달성된다. |
| **Q6** finalize 후 캡슐 dirty | finalize가 `memory-index-request.json`의 status를 `applied`로 바꾸면서 캡슐이 dirty가 된다(실측 ` M tasks/003-t/memory-index-request.json`). 이 상태로는 `remove`의 dirty guard가 막는다. | `worktree_tool.py:1497`; 실측 q119b | 새 순서에 "finalize 후 캡슐 변경을 태스크 커밋에 포함"하는 스텝이 필수다(제안서 §6.3이 의도한 동작). 이 커밋이 merge 전에 일어나야 merge 결과에 포함된다 → 경로 B 순서를 강화한다. |
| **Q7** fallback 계약 | 현행 스텝 4.5의 `ok: false` 분기는 "**태스크 폴더·TASK.md를 롤백하지 않는다**"가 전제다 — 새 순서에서는 그 시점에 폴더도 TASK.md도 아직 없으므로 이 문장이 성립하지 않는다. 도구는 부분 실패 시 자기 생성물만 all-or-nothing 롤백한다. | `task-process.md:49-52`; `worktree_tool.py:960-962` | AC-2·AC-15는 문장 교체로 충족된다: `ok:false` → "허브 `tasks/`에 폴더를 생성하고 `--worktree` 없이 스텝 5로 진행". 새 순서가 오히려 이중 SSOT를 **구조적으로** 불가능하게 만든다(폴더를 나중에 만들므로). |
| **Q8** memory-tool 거부 게이트 | 게이트는 `task_root`가 아니라 **경로 문자열 `.opal-worktrees` 세그먼트**로 판정하므로 cone 활성화에 영향받지 않는다. 실측: `task-number`·`prune`·`append --kind history` → `WORKTREE_WRITE_REJECTED`; `append --kind memory --task-path` → `deferred: true` + `memory-index-request.json` 8필드 pending 기록; 워크트리 `.opal/MEMORY.json`은 무변경(git status에 미등장). | `memory_tool.py:850-881`, `:1145-1149`; 실측 q119 | AC-11의 기계장치는 **이미 동작한다**. cone 활성화 후 회귀 확인만 필요하고 코드 변경 후보가 아니다. |
| **Q8** code-scan 스캔 결과 | 허브 `.opal/code-scan.json`의 `exclude`에 `tasks`와 `.opal-worktrees`가 **이미** 들어 있다. 이 파일은 추적 파일이라 cone으로 워크트리에 동일 내용이 실체화된다. `scopes`는 `opal/`·`dashboard/...`로 cone의 코드 디렉터리 안이다. | `.opal/code-scan.json` `exclude` 배열; `git ls-files .opal/code-scan.json` | cone 활성화가 code-scan 결과를 바꾸지 않는다(`tasks/` 실체화가 exclude로 흡수됨). `create`가 그 exclude 부재 시 비차단 경고를 내므로 fixture 검증 시 경고 유무를 확인 지표로 쓸 수 있다. |
| **Q8** brain-tool / event-loader | `brain-tool`은 cwd 자신을 task root로 쓰고 `.opal/brain/SCHEMA.md` 부재 시 `brain_not_initialized`로 거부한다 → cone 없이는 워크트리에서 조회 불가, cone 활성화가 이를 **해소**한다. `event-loader._project_root`는 `.git` **와** `.opal/AGENT.md`를 함께 가진 첫 조상을 찾고, 없으면 Git 경계에서 끊고 cwd를 반환한다 → cone 없는 워크트리에서는 잘못된 루트로 폴백한다. | `brain_tool.py:232-244`, `:269-290`, `:300-317`; `event_loader.py:85-98` | cone 활성화는 회귀가 아니라 **두 도구의 워크트리 정상 동작 전제**다. 회귀 확인 대상은 "cone on 상태에서 비워크트리 실행이 변하지 않는가"로 한정된다. |
| **AC-4 충돌** | `.opal-task.lock`은 실행 로그 **제안서**(`docs/proposals/opal-task-run-log.md:457,503`)에만 존재하며 코드·도구에 구현이 0건이다(레포 전수 grep). | `grep -rn "opal-task.lock"` → TASK.md·제안서 3건만 매치 | AC-4의 "동일 `.opal-task.lock` inode 관측"은 현 시점 **검증 불가능**하다. PLAN은 AC-4를 realpath 동일성으로 축소하거나 lock 구현을 범위에 넣을지 결정해야 한다. |

## Change boundary

| 경로·인터페이스 | 역할 | 변경 영향 |
|---|---|---|
| `opal/core/references/harness/task-process.md:17-36` | 채번 규칙 3·4항(폴더 → TASK.md) | **직접 변경.** 순서 재정렬 + 채번 `--file`을 allocator 절대경로로 명시 |
| `opal/core/references/harness/task-process.md:38-53` | 스텝 4.5 worktree create | **직접 변경.** 채번 직후로 이동, `--task-folder` 추가, `ok:false` fallback 문장 교체 |
| `opal/core/references/harness/task-process.md:55-70` | 스텝 5 `state init` | **직접 변경.** `<task-path>`가 워크트리 안 canonical path임을 명시 |
| `opal/core/references/harness/worktree.md` §cone 확장 계약 | 운영 권고값의 Phase 표기 | **직접 변경.** `["tasks",".opal"]`을 Phase 2 활성값 → 현행 운영값으로 승격 |
| `opal/core/references/harness/worktree.md` §task root와 allocator root 계약 | CLOSE·귀속 순서 서술 | **직접 변경 후보.** deadlock 해소 결정(merge 전 finalize)을 반영해야 §6.3 원문과 정합 |
| `.opal/worktree.json` | `taskCapsuleCone` 키 부재 → 기본 `[]` | **직접 변경.** `[".opal","tasks"]` 추가(AC-3의 스위치) |
| `opal/skills/opal-pilot-dev/SKILL.md` STEP 6 CLOSE 5항 | worktree 정리 안내 | **직접 변경.** merge 확인 → `worktree-tool finalize` → `state-tool finalize-attribution --allocator-root` → `status --set done` → `remove` 접합 |
| `opal/core/references/pm/dispatch-process.md:135` | 워커 경로 주입 1문장 | **직접 변경 후보.** 문서 루트를 canonical `task_path`(워크트리 안)로 명시 |
| `opal/tools/worktree-tool/worktree_tool.py:1035-1057,1063,1399` | `_assert_task_path_unambiguous` + 호출부 | **직접 변경 후보(결정 의존).** merge 산물 허브 사본 예외를 신설하는 경로를 택할 경우 |
| `opal/core/references/harness/done-template.md` | `S ⊆ D` 선언 계약 | **회귀 경계.** 변경 불요 — finalize 실측이 계약대로 동작 |
| `opal/tools/memory-tool/memory_tool.py` 워크트리 게이트 | 경로 세그먼트 기반 거부 | **회귀 경계.** cone 활성화와 독립 — 변경 불요, AC-11 재확인만 |
| `opal/tools/state-tool/state_tool.py:730-744, 1422-1425` | `task_root`, `init --worktree` | **회귀 경계.** 변경 불요 — cone이 켜지면 의도대로 워크트리에 착지 |
| `opal/tools/brain-tool/brain_tool.py`, `opal/tools/event-loader/event_loader.py` | cwd/앵커 기반 루트 해석 | **회귀 경계.** cone on 워크트리 정상 동작 확인 + 비워크트리 무변화 확인(AC-14) |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | `opds` 중복 트리거 | **회귀 경계 + 리스크.** 순서 전환 미적용 시 `opds` 라우팅이 구 경로로 빠진다 |
| `opal/skills/opal-pilot-{project-dev,project-loop,sdd}/SKILL.md` | 무관한 `.worktrees/` 격리 | **회귀 경계.** worktree-tool 비소비 — 무변경 확인만 |
| `docs/PROJECT.md` 문서 레지스트리 | 규범 문서 목록 | **갱신 후보.** worktree.md·task-process.md 역할 서술이 달라지면 반영 |

## Critical assumptions

| 가정 | 확인 방법·결과 | 남은 한계 |
|---|---|---|
| cone `[".opal","tasks"]`가 sparse-checkout으로 실제 실체화된다 | fixture q119에서 `create` 후 `sparse-checkout list` = `.opal src tasks`, `ls -a` 확인 | 허브 실물 규모(추적 파일 약 1500건)에서의 `create` 소요시간·디스크는 미측정 |
| `task_root`가 워크트리에 착지한다 | q119(cone on)=워크트리 / q119b task_004(cone off)=허브 대조 실측 | 실제 허브 워크트리(task_119)는 cone 미활성이라 미실측 — 활성화 후 재확인 필요 |
| 워크트리 MEMORY 쓰기 거부·index 요청이 동작한다 | q119에서 `task-number`/`prune`/`append --kind history` 거부, `append --kind memory` deferred 기록 실측 | `*.local.md` 변경 거부(AC-11 후단)는 fixture에 local 메모리가 없어 미실측 |
| 수명주기가 실제 Git에서 닫힌다 | q119b 경로 B: finalize(commit) → 캡슐 커밋 → `--ff-only` merge → `remove` 전부 ok. 기존 태스크 `tasks/001-x` diff 0건 | **merge 후** finalize 경로는 차단 확인(q119 경로 A). 제안서 §6.3 순서 그대로는 재현 불가 |
| `--wt` 미사용 실행이 바이트 동일하다 | cone 전개는 `create`의 monorepo 분기 안에서만 일어나고(`worktree_tool.py:948-952`), 비워크트리 경로에 분기가 없음을 코드로 확인 | 실행 캡처 대조(AC-14)는 미수행 — cone 활성화 **전후** 동일 명령 출력 바이트 비교를 EXECUTE/TEST에서 수행해야 한다 |
| AC-4의 lock inode 검증이 가능하다 | `.opal-task.lock` 구현 0건(레포 전수 grep) | **미충족.** 현 코드베이스로는 검증 불가 — AC 재정의 또는 범위 확대 결정 필요 |
| `opds` 호출이 `opal-pilot-dev`로 라우팅된다 | 두 SKILL이 모두 `opds`를 트리거로 선언하고 둘 다 배포됨을 확인 | 실제 라우팅 우선순위는 스킬 로더 동작에 달려 있어 미실측 — 파일럿 대상을 SKILL 이름으로 지정해 회피 권고 |

## Handoff

- **PLAN에서 결정할 것 1 (최우선, 나머지 설계를 좌우)**: merge–finalize deadlock 해소 방식. (a) 수명주기를 **finalize → 캡슐 커밋 → merge → `finalize-attribution` → `status --set done` → `remove`**로 재정의(문서만 변경, 실측으로 통과 확인됨) vs (b) `_assert_task_path_unambiguous`에 merge 산물 예외를 신설(코드 변경, C-9의 118 계약 약화 위험). (a)를 권고한다.
- **PLAN에서 결정할 것 2**: AC-9의 경로 A(`--no-ff --no-commit` 단일 merge 커밋) 정의. 현행 `worktree-tool finalize`는 항상 브랜치에 별도 커밋을 만들므로, 경로 A를 "허브에서 brain/MEMORY 후처리를 merge 커밋에 흡수하고 finalize는 registry 상태만 닫는 경로"로 재정의할지 판단.
- **PLAN에서 결정할 것 3**: 파일럿 게이트 축. `--wt` 플래그 축(권고) vs 프로필 축. 프로필 축을 택하면 `task-process.md`의 순서 원문을 복제해야 하므로 SSOT가 깨진다. 병행하여 `opal-pilot-dev-short`의 `opds` 중복 트리거 처리(폐기 표기 / description 수정 / 범위 밖 유지)를 정한다.
- **PLAN에서 결정할 것 4**: AC-4의 `.opal-task.lock` 조항 — realpath 동일성으로 축소 vs lock 구현을 이번 범위에 포함. 미구현 사실이 확정됐으므로 현행 문언 그대로는 달성 불가다.
- **PLAN에서 결정할 것 5**: 채번 명령의 allocator 절대경로 표기 방식과, 새 순서에서 채번이 worktree create보다 앞서므로 `allocator_root` 발급 전 프로젝트 루트를 그대로 쓰는 것으로 충분한지 확인.
- **PLAN에서 결정할 것 6**: cone으로 워크트리에 내려오는 `.opal/worktree.json` 사본의 취급(워크트리 안에서 worktree-tool 재호출 시 자기 오인 방지 가드 필요 여부).
- **착수 차단**: 없음.
