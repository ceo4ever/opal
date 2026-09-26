---
module: worktree
role: 워크스페이스 축과 태스크 소유권 루트 계약의 단일 SSOT
load: pilot.start
---

# Worktree

## 모드 축과 직교하는 별개 축

워크스페이스 축(`--worktree`/약칭 `--wt`, 해제 `--no-wt`)은 모드 축(`--interactive`/`--semi-agentic`/`--agentic`)과 **직교**한다.

- 모드 축은 "PM이 얼마나 자율적으로 진행하는가"를, 워크스페이스 축은 "코드를 어느 작업본에서 만지는가"를 결정한다.
- 조합 가능: `//opd --agentic --wt`, `//opds --no-wt` 모두 유효하다.
- `mode_flag_conflict` 판정 대상이 **아니다**. 모드 플래그 개수 검사에 `--wt`·`--no-wt`를 세지 않는다.
- 서브 하네스 로딩 규칙에 영향을 주지 않는다.
- 판정은 `state-tool resolve-start`가 집행한다(`harness/modes.md` §라우팅 계약 2).

## 신규 태스크 기본 workspace와 명시 선택

| Pilot | 무플래그 신규 태스크 | `--no-wt` |
|---|---|---|
| `opd`·`opds`·`oppd`·`oppl` | worktree | 허브 작업본 |
| `oppb` | worktree(프로젝트 worktree 1개·Supervisor 구조) | `workspace_required_for_skill`로 거부 |
| 그 외 Pilot | 허브 작업본 | 허브 작업본(기본값과 같음) |

- `--wt`와 `--no-wt`를 함께 주면 `workspace_flag_conflict`로 거부한다.
- **[MUST] 기존 태스크 재개는 저장 workspace를 상속한다.** `state.json`의 `worktree` 키가 있으면 worktree, 없으면 허브다. 저장값과 다른 workspace 플래그는 `resume_axis_locked`로 거부하며 작업본을 옮기지 않는다.
- **[MUST] worktree로 판정된 태스크는 worktree 생성이 실패해도 허브로 폴백하지 않는다.** 허브 작업본은 사용자가 `--no-wt`를 명시했을 때만 쓴다. 실패 처리 절차는 `harness/task-process.md` 스텝 4.5가 소유하고, `state-tool init --workspace worktree`가 `--worktree` 없는 초기화를 `worktree_path_required`로 막는다.
- **[MUST] 작업본 안에서 새 작업본을 만들지 않는다.** `worktree-tool create`는 `--project-root`가 조상 허브의 `.opal-worktrees/` 하위이거나 Git linked worktree면 `PROJECT_ROOT_IS_WORKTREE`로 거부한다. 워크트리 세션이 새 태스크를 시작하려면 허브 절대경로를 `--project-root`로 지정한다(§cone 확장 계약).

## 허브 작업본 태스크

허브 작업본으로 판정된 태스크는 다음이 이 축 도입 이전과 같다.

- `state.json` 스키마: `worktree` 키가 **아예 생성되지 않는다**(`state-tool init`에 `--worktree`를 전달하지 않는다).
- STATE.md 렌더 결과 · 산출물 경로 · 워커 디스패치 프롬프트(`pm/dispatch-process.md` §작업 경로 블록 미주입).
- 코드 작업본은 프로젝트 기본 작업본(`workspace/` 등)이다.

## 작업본과 허브 경계

- 코드 작업본은 `{프로젝트}/.opal-worktrees/task_{NNN}/`이다.
- 태스크 캡슐(`tasks/{task_folder}`)과 `.opal`의 위치는 허브 고정이 아니라 **루트 소유권**으로 정해진다. 태스크 문서·`.opal` 설정·branch source는 `task_root`가, 허브 `.opal/MEMORY.json`은 `allocator_root`가 소유한다. 계약은 아래 §task root와 allocator root 계약이다.
- 생성·설정 부재·실패 복구 절차의 SSOT는 `harness/task-process.md` §오케스트레이터 공통 영역 스텝 4.5, 회수 동작은 `worktree-tool remove`다. 본 문서는 그 절차를 복제하지 않고 축의 정의와 루트 소유권 계약만 소유한다.

## task root와 allocator root 계약

루트는 용도별로 두 개이며 **서로 대체하지 않는다**. 본 계약의 **원문은 이 절 한 곳에만 존재한다**. 런타임 구현은 이 문서를 가리키고 정의를 복제하지 않는다.

| 루트 | 결정 방법 | 소비자 | 쓰기 대상 |
|---|---|---|---|
| `task_root` | canonical task path에서 가장 가까운 `.git`·`.opal` 작업본 또는 명시 `task_home` | code-scan, event-loader, brain-tool, state의 설정·gate | branch의 `.opal`, `tasks`, source |
| `allocator_root` | worktree registry가 발급한 허브 절대 경로 | task-number, merge 후 history | 허브 `.opal/MEMORY.json` |

- 표의 "쓰기 대상" 열은 태스크 귀속 계약(채번·merge history)의 범위를 정의한다. 도구가 소유하는 허브 루트 미추적 디렉토리(`.opal-worktrees/`, `.opal-runs/`, `.opal-cache/`)는 이 조항의 적용 대상이 아니다.
- **[MUST] `task_root`는 표에 정의된 대로 canonical task path에서 가장 가까운 `.git`·`.opal` 작업본을 찾는 조상 탐색으로 결정할 수 있다.** 아래 `allocator_root` 추론 금지를 `task_root` 해석에 적용하지 않는다.
- **[MUST] `allocator_root`는 cwd, task path의 조상, `.opal-worktrees` 문자열로 추론하지 않는다.** 허브 PM이 worktree 생성 시 registry에 기록하고, merge 귀속 단계가 명시 인자로 전달한다.
- 워커와 일반 state 변경 명령에는 allocator write 권한을 주지 않는다.
- CLOSE 마지막 mark는 MEMORY history를 즉시 append하지 않고 `completed_unmerged`만 확정한다. history append는 merge 확인 후 귀속 명령만 수행한다.
- 워크트리의 `.opal/MEMORY.json`은 읽기 snapshot이며 state-tool의 쓰기 대상이 아니다.

### merge 경로

- 귀속은 merge **전** 브랜치에서 실행한 `finalize` 커밋으로 확정된다. merge는 그 커밋을 포함한 브랜치를 옮길 뿐이며 귀속을 새로 만들지 않는다.
- 허용 merge 경로는 두 가지다 — FF 가능 시 `git merge --ff-only`, merge 커밋을 남길 때 `git merge --no-ff`. 어느 쪽이든 귀속 결과는 동일하다.
- **[MUST] `git merge --no-ff --no-commit` 후 merge 커밋 안에서 귀속 후처리를 확정하는 단일 merge 커밋 경로는 현행 도구 계약이 아니다.** 그 시점에는 허브 `tasks/{task_folder}` 사본이 이미 존재하는데 `attribution_state`는 아직 `closed`가 아니므로 §상태 의존 해석에서도 차단이 정상 판정이고, 단일 복사본 불변식과 구조적으로 충돌한다.
- 생성·회수 절차의 원문은 `harness/task-process.md` §오케스트레이터 공통 영역이 소유한다. 이 절은 귀속 확정 시점과 허용 경로만 정의하고 절차를 복제하지 않는다.

## 실행 소유권(lease) 계약

실행 소유권은 한 태스크를 지금 누가 쓰고 있는지를 정하는 축이다. 이 절이 획득·이관·해제와
가드 적용 범위의 원문을 소유하며, 런타임 구현은 이 문서를 가리키고 정의를 복제하지 않는다.

### 저장 위치와 축 분리

| 축 | 위치 | 의미 |
|---|---|---|
| lease | `<canonical_task>/run/.runtime/owner.json` | 지금 이 태스크에 쓰기가 허용되는 세션 |
| registry `execution_ownership` | `<hub_root>/.opal-worktrees/.meta/task_{NNN}.json` | 실행 주체와 터미널 어댑터의 관측 기록 |

두 축은 서로를 대체하지 않는다. registry가 `worktree_session_owned`라는 사실만으로 그 세션이
쓰기 권한을 갖지 않으며, 권한 판정의 유일한 입력은 lease다.

### 획득

- 허브 세션은 `state init` 이후 첫 상태 전이에서 `claim_source=state_transition`으로 획득한다.
- 워크트리 세션은 부팅 시 `claim_source=session_start`로 획득한다.
- **[MUST] 어느 경로도 다른 세션의 live lease에서 소유권을 빼앗지 않는다.** 같은 세션의 재획득만 멱등하게 허용한다.

### 이관

`--wt` 태스크는 허브가 먼저 소유한 뒤 실행 주체를 띄우므로, 이관 없이는 워크트리 세션이 구조적으로
소유권을 받을 수 없다. 이관은 그 구간을 잇는 유일한 경로다.

- 이관은 터미널 기동 **직전**에 1회 수행하며, 대상은 registry가 발급한 `worktree_root`다.
- 이관 상태의 lease는 소유자가 없고 대상 루트만 지정된다. **대상 루트와 같거나 그 하위에서 온 획득만 수용하고, 허브와 제3 세션의 획득은 거부한다.**
- **[MUST] 이관 대상 루트는 registry 발급값을 명시 인자로 받는다.** cwd, task path의 조상, `.opal-worktrees` 문자열로 추론하지 않는다(§task root와 allocator root 계약).
- 이관에는 lease TTL과 분리된 자체 만료가 있다. 만료된 이관은 무소유로 접혀 허브가 되찾는다 — 터미널이 끝내 부팅하지 않는 경로에서 태스크가 영구히 잠기지 않게 하는 장치다.
- 이관 실패와 터미널 기동 실패는 이관을 취소하고 허브 소유로 원자 복귀한다. 취소 자체의 실패는 복귀를 막지 않고 진단으로만 남는다.

### 해제

- **[MUST] 소유권 이전은 현 소유자의 명시 해제 또는 만료를 거친다.** 제3자가 강제로 해제하는 표면을 두지 않는다.
- 세션 종료 훅은 그 세션이 소유한 lease만 해제한다. 종료 신호 없이 사라진 세션의 lease는 만료가 회수한다.
- **[MUST] 훅 이벤트의 세션은 봉투 `session_id`로만 식별한다.** 부모 세션의 환경변수를 상속한 자식 프로세스의 이벤트를 부모 신원으로 대체하지 않으며, 봉투 신원이 없는 이벤트는 진단만 남기고 소유권·세션 파일을 바꾸지 않는다. 환경변수 기반 식별은 일반 CLI 호출에만 쓴다.
- 잠긴 태스크의 수동 해제는 소유 세션에서 `ownership-tool`의 해제 서브명령으로 수행한다.

### 가드 적용 범위

- 쓰기 차단은 lease가 **타 세션 소유**로 판정될 때만 발동한다. 이관 중(무소유)과 만료는 차단 대상이 아니다.
- 상태 전이 도구는 획득 실패를 차단이 아니라 경고로 처리한다(fail-safe). 집행자는 쓰기 가드 하나이며 판정 지점을 늘리지 않는다.

## 실행 세션 기동과 터미널 회수 경계

워크스페이스 축은 "코드를 어느 작업본에서 만지는가"에 더해 **그 작업본을 누가 실행하는가**까지 정한다. 이 절은 경계만 소유하고 절차 원문은 `harness/task-process.md` §오케스트레이터 공통 영역(스텝 5.5)과 §`--wt` 체크포인트 커밋과 merge 경계가 소유한다.

| 국면 | 주체 | 경계 |
|---|---|---|
| 워크트리·브랜치 생성, 발급값 배달 | 허브 세션 | `worktree-tool`이 단일 소유자다. 터미널 도구가 대체하지 않는다 |
| 전용 터미널 기동 | 허브 세션 | `state init` 완료 후 terminal context의 현재 `host`와 같은 어댑터만 명시 주입하며 실패는 비차단이다 — 작업본은 이미 있으므로 허브 세션이 그 작업본에서 이어 수행하고 허브 `tasks/`로 옮기지 않는다 |
| 단계 실행·체크포인트 커밋·CLOSE | 워크트리 세션 (전용 세션 미기동·기동 실패 시 lease를 보유한 허브 세션) | `completed_unmerged`까지 진행한다. 체크포인트는 `worktree-tool checkpoint`로만 만든다 |
| `main` merge·push | 허브 세션 | 승인 경계는 `harness/guards.md` §커밋 규칙이, 허용 merge 경로는 위 §merge 경로가 소유한다 |
| 터미널 회수·worktree 제거 | 허브 세션 | 회수는 3중 가드 통과 뒤 터미널 스윕을 선행한다 |

- **[MUST] 기동은 `state init` 이후다.** 워크트리 세션은 부팅 직후 `state.json`을 읽으므로, 그 전에 띄우면 첫 턴이 읽을 상태가 없다.
- **[MUST] host와 multiplexer를 섞지 않는다.** `terminal-context`의 `host`만 adapter 선택에 사용한다. `tmux` 같은 `multiplexers`와 설치·전역 실행 중인 다른 앱은 선택 근거가 아니다. 기동 직전에 재감지하며 `unknown`·미지원 host는 추측 폴백 없이 허브 소유를 유지한다.
- **시작 발화는 기동 명령 인자가 소유한다.** 태스크 식별은 워크트리와 canonical task의 1:1 관계와 `state.json`이 이미 결정론적으로 해결하므로 별도 캡슐 파일이나 터미널 입력 채널을 만들지 않는다.
- 어댑터가 구성되지 않은 환경에서는 워크트리만 생기고 터미널은 열리지 않는다. 허브 세션이 그 워크트리를 그대로 작업하며, 이는 축 도입 이전과 같은 동작이다.
- 허브가 워크트리 세션의 종료를 아는 수단은 registry `attribution_state`(`completed_unmerged`) 조회 하나다. 별도 통지 채널을 만들지 않는다.

## canonical path 발급 계약

canonical task path의 **기계 계약은 worktree-tool metadata/schema가 소유한다.** 이 문서는 인터페이스와 의미만 참조하고 경로 판정 알고리즘을 복제하지 않는다.

- `worktree-tool create` 성공 응답과 `.opal-worktrees/.meta/task_{NNN}.json`이 다음 6종 필드를 소유한다: `allocator_root`, `task_home`, `task_folder`, `task_path`, `artifact_repo`, `task_ownership_version`.
- **불변식**: `task_path == realpath(task_home/tasks/task_folder)`.
- `task_folder`는 **basename만 허용**한다. `/`, `..`, NUL과 경로 구분자를 포함하면 거부한다.
- PM·워커·state-tool·run-log-tool은 이 발급값을 전달받아 사용한다. cwd에서 `.opal-worktrees` 문자열을 찾아 task path를 추측하지 않는다.
- **[MUST] 등록된 worktree 태스크에 허브 `tasks/{task_folder}`가 동시에 존재하면 자동 선택하지 않고 `task_path_ambiguous`로 차단한다.** 이 차단의 적용 범위는 아래 §상태 의존 해석이 정한다.
- `task_ownership_version`이 없는 태스크는 legacy다. 실행 중 태스크 위치를 자동 이동하지 않고 기존 허브 task path를 유지한다. legacy worktree가 허브 자산을 필요로 하면 registry/meta의 명시 `project_root`를 전달한다.

### 상태 의존 해석

canonical path 판정은 registry meta의 `attribution_state` 한 값을 **더 본다**. 차단 계약을 제거하는 완화가 아니라 적용 상태를 한정하는 확장이다.

| `attribution_state` | canonical task path | 허브 사본이 동시에 존재할 때 |
|---|---|---|
| 키 부재 · `completed_unmerged` · `attribution_pending` (= active) | 등록된 worktree task path | `task_path_ambiguous`로 차단한다 |
| `closed` (= merge 확인 후) | 허브에 merge된 `tasks/{task_folder}` | 차단하지 않는다 |

- **[MUST] `task_path_ambiguous` 차단은 active 상태에만 적용한다.** active 3상태의 판정은 무변경이며, 통과가 열리는 값은 `closed` 하나뿐이다.
- `closed`는 `finalize` 성공 경로에서만 기록된다. merge 뒤 허브 사본은 정상 결과이므로 이를 차단하면 `finalize`·`status` 재진입이 영구 차단된다.
- `task_ownership_version` 부재 legacy 메타는 이 판정에 들어가지 않는다(위 legacy 항 유지).

## cone 확장 계약

- 설정 키 `taskCapsuleCone`, 타입 `list[str]`, **기본값 `[]`**.
- monorepo 분기에서만 `repos`에 이어 sparse-checkout cone에 전개한다. **multi-repo 분기에는 적용하지 않는다.**
- 기본값 `[]`의 전개는 no-op이므로 비워크트리·기존 워크트리 동작은 바이트 동일하게 보전된다.
- **현행 운영값은 `["tasks", ".opal"]`이다.** 허브 `.opal/worktree.json`이 `taskCapsuleCone`으로 이 값을 선언하며, 새 worktree는 `.opal`과 `tasks`가 실체화된 상태로 생성된다. 스키마 기본값은 여전히 `[]`이고, 키를 제거하면 즉시 전환 전 동작으로 돌아간다.
- 워크트리에 내려온 `.opal/worktree.json`은 **읽기 snapshot**이다. 이 사본을 근거로 워크트리가 자기를 허브로 간주하지 않는다.
- **[MUST] `worktree-tool` 호출은 항상 허브 `--project-root <허브 절대경로>`를 명시한다.** cwd나 워크트리 사본으로 프로젝트 루트를 추론하지 않는다.

## multi-repo 캡슐 소유권 계약

적용 범위는 `layout: "multi-repo"` 분기 하나다. monorepo·비워크트리 경로는 이 절의 어떤 항목도 소비하지 않는다. 생성·회수 절차의 원문은 `harness/task-process.md` §오케스트레이터 공통 영역이 소유하며, 이 절은 축 정의와 계약만 소유한다.

### 캡슐 소유 repo 지정

- 설정 키는 `task_artifacts.repo`다. **[MUST] 1차 도입은 예약값 `"."`(루트 저장소)만 허용한다.** 다른 값은 `TASK_ARTIFACT_REPO_UNSUPPORTED`로 차단하고 확장 선행 조건을 오류 메시지에 담는다.
- 1차 한정의 근거는 §canonical path 발급 계약의 `task_path` 불변식과 canonical resolver의 허브 후보 경로 고정이다. `repos[]` 원소를 캡슐 소유 repo로 지정하려면 두 고정을 먼저 확장해야 한다. **이 절은 그 불변식을 재서술하거나 완화하지 않는다.**
- **[MUST] `tasks_path`·`opal_path`를 설정 키로 노출하지 않는다.** 캡슐 경로는 `tasks`, 프로젝트 자산 경로는 `.opal`로 고정한다.
- `repos[]`에 `"."`를 추가하지 않는다. `repos`의 "worktree를 만들 코드 저장소 목록"이라는 의미와 `list[str]` 타입을 보존한다.
- `task_artifacts`가 없는 multi-repo는 기존 `TASK_ARTIFACT_REPO_MISSING` 차단을 유지한다. 컨테이너 디렉토리만 있고 루트가 Git 저장소가 아닌 multi-repo는 `"."` 모델의 대상이 아니다.

### 루트 Git 적격 R-1~R-5

`create` pre-flight에서 다음 5개 조건을 검사하고, 하나라도 불만족이면 `TASK_ARTIFACT_REPO_INVALID`로 차단한다. 오류 응답에 불만족 조건 번호를 동봉한다.

**[MUST] 판정 순서는 R-1~R-4 → §추적 범위 겹침 차단 → R-5다.** `git check-ignore -q <rel>`은 그 경로 아래에 추적 파일이 하나라도 있으면 rc=1(미ignore)을 반환하므로, R-5를 겹침보다 먼저 판정하면 겹침 위반이 R-5로 먼저 걸려 `TASK_ARTIFACT_REPO_OVERLAP`에 도달하지 못한다. 두 조건은 배타적 원인이며 원인별 전용 오류를 준다 — 추적하면 `TASK_ARTIFACT_REPO_OVERLAP`, 추적하지 않고 ignore도 하지 않으면 `TASK_ARTIFACT_REPO_INVALID`(`violations: ["R-5"]`). `check-ignore --no-index`는 추적 중인 경로도 통과시켜 R-5의 의미를 "실효 ignore"에서 "규칙 존재"로 약화시키므로 쓰지 않는다.

| # | 조건 | 판정 |
|---|---|---|
| R-1 | 루트에 `.git`이 존재하고 유효한 Git 저장소다 | `git -C <root> rev-parse --git-dir` 성공 |
| R-2 | 루트가 `tasks/`를 추적한다 | `git -C <root> ls-files -- tasks` 비어 있지 않음 |
| R-3 | 루트가 `.opal/AGENT.md`를 추적한다 | `git -C <root> ls-files -- .opal/AGENT.md` 비어 있지 않음 |
| R-4 | 루트가 `.opal/MEMORY.json`을 추적한다 | `git -C <root> ls-files -- .opal/MEMORY.json` 비어 있지 않음 |
| R-5 | 루트가 각 `repos[]` 경로를 ignore한다 | 각 `rel ∈ repos`에 대해 `git -C <root> check-ignore -q <rel>` 성공 |

- **[MUST] R-2~R-4는 각각 판정한다.** 합산 결과 1건으로 통과시키면 `tasks/`만 추적하고 `.opal/`은 ignore하는 프로젝트가 통과해, merge 시 귀속 대상(`.opal/brain/**`·`.opal/MEMORY.json`)이 브랜치에 담기지 않는다.
- **[MUST] R-5는 추적이 아니라 ignore 축이며, R-2~R-4(`ls-files`)로 대체되지 않는다.** 미추적이면서 ignore되지 않은 경로가 정확히 이 구멍이다. slot root가 full checkout이므로 자식 worktree가 그 안에 생기는 순간 루트 slot의 `git status --porcelain`이 `?? <rel>`을 반환하고, dirty 가드가 `--force` 없는 `remove`를 영구 차단해 아래 §merge와 귀속의 "루트 포함 전건 통과"가 도달 불가가 된다.
- slot dirty 판정에서 `repos[]` 경로를 예외 처리하지 않는다. dirty 판정기는 layout과 무관하게 `status`·`remove`가 공유하는 단일 판정기이므로, 경로 예외는 루트가 실제로 보는 변경까지 무시하고 monorepo·비워크트리 판정에 분기를 만든다.

### slot root 배치

`task_artifacts.repo`가 `"."`이면 **slot root 자체가 루트 저장소의 worktree이고, 곧 `task_home`이다.** 캡슐 전용 하위 worktree를 따로 만들지 않으며, `create`는 `task_home = <slot root>` · `artifact_repo = "."`를 발급한다.

```text
.opal-worktrees/task_{NNN}/         ← 루트 repo worktree (= task_home)
├── tasks/{task_folder}/            ← 태스크 캡슐
├── .opal/                          ← 프로젝트 자산
└── workspace/
    ├── frontend/                   ← workspace/frontend repo worktree
    └── backend/                    ← workspace/backend repo worktree
```

- 허브의 디렉토리 구조와 동형이므로 워커가 보는 상대경로가 허브와 같다.
- 루트 slot은 full checkout이다. multi-repo 분기의 cone 미적용은 §cone 확장 계약이 소유한다 — 루트가 `repos[]`를 추적하지 않으므로(아래 §추적 범위 겹침 차단) full checkout이 코드 repo와 겹치지 않는다.

### 추적 범위 겹침 차단

- 루트 저장소가 `repos[]`의 어느 경로든 1파일 이상 추적하면 `TASK_ARTIFACT_REPO_OVERLAP`으로 차단한다. 판정은 각 `rel ∈ repos`에 대해 `git -C <root> ls-files -- <rel>`이 비어 있음이다.
- **[MUST] 판정 시점은 worktree 생성 전이며, 위반 시 아무것도 만들지 않는다.** 오류 응답에 위반 경로를 동봉한다.
- **[MUST] 이 판정은 R-1~R-4 뒤, R-5 앞에 둔다.** 추적 겹침은 R-5 판정을 오염시키므로 먼저 걸러야 한다.
- 겹치면 루트 worktree의 full checkout과 코드 repo worktree가 같은 경로에 착지해 어느 쪽이 이기는지 정의되지 않는다. 자동 해소하지 않고 명시 차단한다.

### ordered `plan_entries` 단일 소비

- **[MUST] 루트를 포함한 전 entry 목록은 `plan_entries` 하나가 소유하고, pre-flight·base-ref 해석·worktree 생성·metadata `entries`·rollback·remove가 모두 이 목록만 소비한다.** 생성부가 `repos` 설정값을 따로 순회하지 않는다.
- 루트 entry는 `plan_entries`의 맨 앞이며, metadata `entries`는 이 순서를 보존한다.
- 목록이 둘로 갈라지면 pre-flight 통과 결과가 생성 결과를 보장하지 못한다 — 루트가 검사 대상이면서 실제로는 생성되지 않는다.

### repo별 base branch

- 설정 키 `baseBranchOverrides`, 타입 optional `dict[str, str]`, 기본값 `{}`.
- **[MUST] 키는 `repos[]`의 원소 또는 `"."`와 정확히 일치해야 하며, 불일치 키는 `CONFIG_UNKNOWN_REPO`로 차단한다.** 오타가 조용히 전역값으로 폴백하면 잘못된 base에서 브랜치가 갈라진다. 루트 repo의 키는 `"."`다.
- 해석은 `resolve_base_ref(git_root, overrides.get(rel, baseBranch))`다. override는 declared base 자리에 값을 넣을 뿐이며, declared 부재 시의 폴백 순서를 바꾸거나 새 우선순위를 신설하지 않는다.
- **[MUST] 이 키와 `CONFIG_UNKNOWN_REPO` 검증은 multi-repo 분기 전용이다.** monorepo 분기는 값이 있어도 소비하지 않으며 경고하지 않는다.
- `init` 초안은 multi-repo 분기에서만 키를 늘린다. `baseBranch`는 R-1을 만족할 때만, `task_artifacts`는 R-1~R-5 전건을 만족할 때만 제시한다. `baseBranchOverrides`는 초안에 넣지 않는다.

### 생성·회수 순서

| 국면 | 순서 | 근거 |
|---|---|---|
| 생성 | 루트 → 자식 | 자식 worktree의 부모 디렉토리가 루트 worktree 안에 있어야 한다 |
| 롤백 | 자식 → 루트 | 자식이 남아 있으면 루트를 제거할 수 없다 |
| 회수(`remove`) | 자식 → 루트 | 위와 같다 |

- **[MUST] 회수·롤백은 생성의 역순으로 순회한다.**
- **[MUST] 전 entry의 `git worktree remove`가 성공한 뒤에만 메타와 slot root를 삭제한다.** 각 호출의 반환코드를 확인하고, 하나라도 실패하면 `WORKTREE_REMOVE_FAILED`(실패 repo·stderr 동봉)로 반환하며 메타 삭제와 slot 삭제를 실행하지 않는다. 메타가 남아 있어야 재시도와 수동 복구가 가능하다.
- **[MUST] 성공한 회수는 registry lock을 보유한 상태에서 메타를 삭제하고, 같은 inode의 `<meta>.lock` 이름도 잠금 해제 전에 회수한다.** 대기 writer는 lock 획득 뒤 메타 존재를 재검사하며, 메타가 없으면 `META_NOT_FOUND`로 중단해 삭제된 registry를 재생성하지 않는다. 가드·entry 회수 실패에서는 메타와 lock을 함께 보존한다.
- `--force`는 가드 우회에만 적용되며 이 실패 판정을 우회하지 않는다.
- 롤백 실패도 같은 계약을 따른다. 자기 생성물을 역순 회수하다 실패하면 slot을 지워 흔적을 없애지 않고, 잔존 entry의 경로·repo·branch를 오류 payload에 실어 수동 복구 대상을 명시한다.

### 부분 회수 이후의 멱등 재시도

entry별로 **경로 실재**와 **Git 등록** 두 축을 따로 보고 판정한다. 등록 판정은 create pre-flight가 쓰는 기존 판정기(`git worktree list --porcelain`)를 재사용하며 새 기준을 만들지 않는다.

| 경로 | Git 등록 | 판정 | 동작 |
|---|---|---|---|
| 없음 | 없음 | 이미 회수됨 | skip — 오류 아님 |
| 없음 | 있음 | 등록 고아 | `WORKTREE_REMOVE_FAILED`로 차단·보존 |
| 있음 | 없음 | 미등록 잔여 디렉토리 | `WORKTREE_REMOVE_FAILED`로 차단·보존 |
| 있음 | 있음 | 정상 | 가드 판정 후 회수 |

- **[MUST] 불일치 2종을 도구가 자동 복구하지 않는다. `git worktree prune`을 호출하지 않고, 미등록 잔여 디렉토리를 삭제하지 않는다.** prune의 대상은 해당 repo의 모든 stale 관리정보라 다른 태스크의 슬롯 정보까지 지울 수 있고, Git이 모르는 디렉토리의 내용은 사용자 파일일 수 있다. 두 경우 모두 실패 repo·경로·관측된 불일치 종류를 payload에 담아 반환하고 메타와 slot을 보존한다.
- 이 판정은 `--force` 없이 동작한다 — 재시도가 가드 우회를 요구하지 않는다.
- 부분 회수 재시도는 "경로 없음 + 등록 없음 → skip" 한 칸으로 성립한다. 나머지 두 칸은 재시도가 아니라 불일치 보고용이다.
- `WORKTREE_NOT_FOUND`는 이 경로에서 발동하지 않는다. 메타 자체의 부재는 `META_NOT_FOUND`가 소유하며 그 계약은 바뀌지 않는다.

### merge와 귀속

허용 merge 경로와 귀속 확정 시점은 §merge 경로가 소유하며 multi-repo도 동일하다. 아래는 multi-repo 추가 조건이다.

- **[MUST] 캡슐은 지정 repo(루트) 하나에만 commit·merge된다.** 코드 repo의 merge와 독립 판정이다.
- `worktree-tool finalize`와 `state-tool finalize-attribution`은 루트 repo에서만 수행한다 — 귀속 커밋 대상(`.opal/brain/**`·`.opal/MEMORY.json`)이 루트 추적 범위 안에 있다.
- **[MUST] `remove`의 3중 가드(dirty → unpushed → unmerged)는 루트를 포함한 전 entry가 통과할 때만 회수한다.** 코드 repo 하나라도 미머지면 캡슐이 merge됐어도 회수되지 않는다.

## Phase 1 진입 legacy gate 절차

Phase 1(허브 보정 제거·루트 분리) 진입 전 다음 gate를 통과한다.

```text
active legacy worktree == 0
OR
모든 active legacy slot에 .opal·tasks cone 소급 확장 + root·설정 회귀 검증 완료
```

- **기본 경로는 drain이다** — 기존 worktree를 완료·merge·remove해 active legacy 0건으로 만든다.
- 소급 확장은 태스크 중단이 불가능할 때만 사용한다. 각 slot에서 `.opal/AGENT.md`, `.opal/code-scan.json`, 필요한 `tasks` fixture가 실체화되고 code-scan·event-loader가 기대한 설정을 읽는지 검증한다.
- 문서의 명시 `project_root` 약속만으로는 CLI 인자가 없는 code-scan 호출을 보호하지 못한다. 파일 실체화나 drain 없이 Phase 1에 진입하지 않는다.
- **[MUST] gate의 실제 통과(drain 또는 소급 확장)는 Phase 2 진입 전 조건이며, 이 절차를 문서에 기재하는 태스크의 완료 조건이 아니다.** gate 미통과 상태에서 Phase 1 코드가 머지되어 있으면 남은 legacy slot에서의 code-scan·event-loader 결과를 신뢰하지 않는다.

### Codex identity 연결 (task 155)

플랫폼 env는 ownership-tool의 Claude/Codex adapter가 소유한다. core resolver는
OPAL 중립 ID 우선과 기존 Claude 우선을 보존하고 native Codex root session을 해석한다.
훅 payload-only 경계는 유지한다. launcher는 시작 ID를 고정해 handoff/cancel에 명시 전달하고,
공개 session-launch가 부모 신원을 제거한다. 설치된 Codex bootstrap의 codex-start는 실제
새 native ID를 payload로 정규화하여 등록·claim·heartbeat를 수행한다. 최종 registry 전이는
worktree-tool ownership-set --owner-from-lease 경유이며, pending일 때 부모 ID를 owner로
남기지 않는다. 실제 기동/lease/registry 증거가 없으면 E2E 완료로 판정하지 않는다.
