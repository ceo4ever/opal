---
template: sdlc-v2
---
# TEST-SCENARIO: 워크트리 multi-repo 캡슐 소유권 — 계약 이관과 worktree-tool 구현

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: macOS · Python 3 · Git 2.25+ · `python3 -m pytest opal/tools/worktree-tool/tests/`.
  모든 도구 호출은 CLI(subprocess) 공개 인터페이스로 수행하고 내부 함수를 직접 부르지 않는다.
- 공통 데이터 — **base fixture(M0)**: 임시 디렉토리에 생성하는 multi-repo 형상.
  루트가 Git 저장소이고 `tasks/.gitkeep`·`.opal/AGENT.md`·`.opal/MEMORY.json`을 추적한다.
  `workspace/` 아래 독립 repo 2개(`workspace/alpha` base `main`, `workspace/beta` base `develop`)를
  두고, 루트는 `workspace/`를 **추적하지 않으며 `.gitignore`에 등재한다**(R-5). 루트 `.gitignore`에
  `.opal-worktrees/`도 등재한다. `.opal/worktree.json`은 `layout: multi-repo`,
  `repos: ["workspace/alpha","workspace/beta"]`, `task_artifacts: {"repo":"."}`,
  `baseBranch: "main"`, `baseBranchOverrides: {"workspace/beta":"develop"}`를 선언한다.
  제안서 §2의 pug 실측 형상과 동형이다(H-5).
- 공통 데이터 — **위반 변형**: M0에서 한 조건만 깨뜨린 파생 fixture.
  V1(루트 `.git` 제거) · V2(`tasks` 미추적) · V3(`.opal/AGENT.md` 미추적) ·
  V4(`.opal/MEMORY.json` 미추적) · V5(루트 `.gitignore`에서 `workspace/` 제거) ·
  V6(루트가 `workspace/alpha` 하위 1파일을 추적 — overlap).
- 공통 데이터 — **회귀 fixture(R0)**: monorepo 형상 1종과 비워크트리 실행 1종. 태스크 119
  `REGRESSION-EVIDENCE.md` §0.1 설계에 따라 고정 데이터 루트에 1회 구성하고 base·after 두 실행
  사이에 건드리지 않는다.
- 대역 사용과 한계: 사용하지 않음. 모든 Git 상태는 실제 `git` 명령으로 만들고 관찰한다.
  단 `/Volumes/Data/StoreLinkStudio/pug` 실환경 연동은 본 태스크 범위 밖이므로(D-22), 아래 모든
  판정은 **fixture 한정**이다. 실환경 완주는 후속 태스크가 소유한다(H-5).
- 실행 조건: 자동 실행. 실 `~/.opal/`에 배포하지 않으며 S-16·S-17의 install은 격리 `HOME`의
  임시 배포 경로에만 수행하고 측정 후 삭제한다(C-8).

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1 | M0, 태스크 번호 900 | `worktree-tool create --project-root <M0> --task 900 --task-folder 900-... ` | `ok: true`. `git worktree list`에 루트·alpha·beta 3건이 등록된다. slot root `.opal-worktrees/task_900`이 루트 저장소의 worktree이고 `workspace/alpha`·`workspace/beta`가 그 아래에 있다 | integration(CLI+git) | 구현 전 RED |
| S-2 | AC-2 | S-1 성공 직후 | `create` 응답과 `.opal-worktrees/.meta/task_900.json`을 읽는다 | `task_home == <slot root>`, `artifact_repo == "."`, `task_path == realpath(task_home/tasks/<task_folder>)`가 성립한다 | integration(CLI) | 구현 전 RED |
| S-3 | AC-3, AC-16 | V1~V5 각각 | 각 fixture에서 `create` 실행 | 전건 `ok: false`, `error == "TASK_ARTIFACT_REPO_INVALID"`. payload `violations`가 해당 조건 1건만 담는다(V1→`R-1` … V5→`R-5`) | integration(CLI) | 구현 전 RED |
| S-4 | AC-3, C-2 | V1~V5 각각 | `create` 실패 직후 `git worktree list`와 `.opal-worktrees/` 상태 확인 | worktree 0건, slot 디렉토리 미생성. 부수 효과 이전 차단(all-or-nothing) | integration(CLI+git) | 구현 전 RED |
| S-5 | AC-4 | V1~V5 각각 | `worktree-tool init --project-root <V*> --dry-run` | 초안에 `task_artifacts` 키가 없다. V1에서는 `baseBranch`·`_baseBranch_candidates`도 없다 | integration(CLI) | 구현 전 RED |
| S-6 | AC-4, H-4 | V1(루트 비-Git) | V1에서 `create`가 아니라 base-ref 해석 경로를 관찰할 수 있도록, `baseBranch` 미선언 설정으로 alpha·beta의 base-ref를 해석한다 | 각 자식 repo의 base-ref가 자기 `origin/HEAD`(없으면 자기 `HEAD`)로 해석되고 빈 문자열이 아니다 | integration(CLI+git) | 구현 전 RED |
| S-7 | AC-5 | M0에서 `task_artifacts.repo`를 `"workspace/alpha"`로 바꾼 변형 | `create` 실행 | `ok: false`, `error == "TASK_ARTIFACT_REPO_UNSUPPORTED"` | integration(CLI) | 구현 전 RED |
| S-8 | AC-5 | M0에서 `task_artifacts` 키를 제거한 변형 | `create` 실행 | `ok: false`, `error == "TASK_ARTIFACT_REPO_MISSING"` — 기존 계약이 그대로 유지된다 | integration(CLI) | 구현 후 |
| S-9 | AC-6 | V6(overlap) | `create` 실행 | `ok: false`, `error == "TASK_ARTIFACT_REPO_OVERLAP"`(R-5의 `TASK_ARTIFACT_REPO_INVALID`가 아니다 — D-24 판정 순서), payload에 위반 경로 `workspace/alpha`. worktree 0건 | integration(CLI+git) | 구현 전 RED |
| S-10 | AC-7 | M0 | `create` 성공 후 pre-flight 대상 집합과 `git worktree list` 등록 집합을 대조한다 | 두 집합이 정확히 일치한다(루트 포함 3건). 생성 국면이 `cfg["repos"]`를 독립 순회하지 않음이 결과로 드러난다 | integration(CLI+git) | 구현 전 RED |
| S-11 | AC-8 | M0 | `create` 후 `.opal-worktrees/.meta/task_900.json`의 `entries[].base_ref` 확인 | 루트·alpha는 `main`, beta는 `develop`으로 동결 기록된다 | integration(CLI) | 구현 전 RED |
| S-12 | AC-8 | M0에서 `baseBranchOverrides`에 `"workspace/gamma"` 키를 추가한 변형 | `create` 실행 | `ok: false`, `error == "CONFIG_UNKNOWN_REPO"`, 위반 키 동봉 | integration(CLI) | 구현 전 RED |
| S-13 | AC-9, AC-16 | S-1 성공 상태에서 브랜치를 base에 merge해 가드를 해소 | `worktree-tool remove --project-root <M0> --task 900` (**`--force` 없이**) | `ok: true`. 루트 slot의 `git status --porcelain`이 공백이라 `GUARD_DIRTY`가 발생하지 않는다. git 호출 순서가 자식(beta·alpha) → 루트다. slot root가 회수된다 | integration(CLI+git) | 구현 전 RED |
| S-14 | AC-9 | `create` 중간 실패를 주입한 M0 변형 — beta의 `baseBranchOverrides`를 존재하지 않는 ref로 두어 pre-flight는 통과하고 생성 국면에서만 실패시킨다(PM 승인 폴백) | `create` 실행 | `ok: false`. 롤백이 자식 → 루트 역순으로 수행되고 `git worktree list` 잔여 0건, slot 디렉토리 잔여 0건 | integration(CLI+git) | 구현 전 RED |
| S-15 | AC-10, C-6 | S-1 성공 후 `workspace/alpha` worktree를 `git worktree lock`으로 제거 불가 상태로 만든다. 3중 가드는 전부 깨끗해야 한다 — 추적 파일 수정 방식은 `GUARD_DIRTY`에 먼저 걸려 `WORKTREE_REMOVE_FAILED` 경로를 관측할 수 없다(PM 승인 폴백) | `remove` 실행 | `ok: false`, `error == "WORKTREE_REMOVE_FAILED"`, 실패 repo·경로·stderr 동봉. `.opal-worktrees/.meta/task_900.json`과 slot root가 **보존**된다 | integration(CLI+git) | 구현 전 RED |
| S-16 | AC-10 | S-15 직후(자식 일부는 이미 회수, alpha는 `git worktree unlock`으로 차단 해소) | `remove` 재호출 (**`--force` 없이**) | `ok: true`. 이미 회수된 entry는 skip되고 남은 entry부터 진행된다. 재시도가 `--force`를 요구하지 않는다 | integration(CLI+git) | 구현 전 RED |
| S-17 | AC-11, C-6 | (a) 경로만 삭제해 Git 등록만 남긴 entry, (b) `git worktree remove`로 등록만 지우고 디렉토리를 남긴 entry | 각각 `remove` 실행 | 두 경우 모두 `ok: false`, `error == "WORKTREE_REMOVE_FAILED"`. `git worktree prune`이 호출되지 않고(git 호출 로그로 관측) (b)의 디렉토리가 삭제되지 않는다 | integration(CLI+git) | 구현 전 RED |
| S-18 | AC-12, C-2, C-8, H-3 | R0 monorepo fixture, 고정 데이터 루트 | 격리 `HOME`의 단일 배포 경로에 base 소스 install → `create`·`list`·`status`·`remove`·`finalize`·`init` 6명령의 stdout/stderr/exit 캡처 → 같은 경로에 after 소스 install → 재캡처 → `cmp` | 18쌍(6명령 × 3채널) 전건 바이트 동일, 정규화 0회. `init` 초안의 키 집합·순서도 동일. 배포본 sha256이 DIFF인 상태에서 출력이 동일함을 함께 기록해 비공허성을 확보한다 | integration(실행 출력 비교) | 구현 후 |
| S-19 | AC-13, C-3 | R0 비워크트리 fixture | S-18과 같은 절차로 비워크트리 명령군 캡처·`cmp` | 전건 바이트 동일, 정규화 0회 | integration(실행 출력 비교) | 구현 후 |
| S-20 | AC-15, H-2 | 구현 완료 상태 | `python3 -m pytest opal/tools/worktree-tool/tests/ -q` | 전건 GREEN. 기존 회귀 `test_s10_remove_force_bypasses_guard_and_records_it`·`test_s28_remove_twice_is_reported_cleanly_after_success`·`test_s14_error_codes_are_all_distinct`·`test_t118_s6_error_codes_stay_within_existing_set`가 수정 없이 통과한다 | unit+integration(pytest) | 구현 후 |
| S-21 | AC-14, C-7 | W-2·W-8 완료 상태 | `harness/worktree.md`의 §multi-repo 캡슐 소유권 계약 존재 확인 + `docs/proposals/`와 `archives/` 파일 위치 확인 + `archives/opal-worktree-task-ownership.md` 헤더 확인 | 규범 절이 존재하고 R-1~R-5·회수 순서·2축 멱등 판정을 담는다. 제안서가 `archives/`에 있고 `docs/proposals/`에 잔존 0건. 선행 제안서 헤더에 §8 대체 포인터 1행이 있다 | 결정론 검사(파일·grep) | 구현 후 |
| S-22 | C-1 | 구현 완료 상태 | 구현된 계약과 제안서 §4·§5·§6을 항목 대조한다 | 제안서에 없는 계약이 구현에 없고, 제안서가 정한 계약이 빠짐없이 구현돼 있다. 구현 중 제안서와 달라진 항목이 있으면 제안서가 먼저 개정돼 있다 | 결정론 검사(문서·코드 대조) | 구현 후 |
| S-23 | C-4 | 구현 완료 상태 | `validate_worktree_config`의 `repos` 검사와 `sparse-checkout set` 소비부를 확인한다 | `repos`가 여전히 `list[str]`이고 의미가 "worktree를 만들 코드 저장소 목록"으로 유지된다. `"."`가 `repos[]`에 추가되지 않았다 | 결정론 검사(코드) + S-18 회귀 | 구현 후 |
| S-24 | C-5, D-11 | M0 | `create` 실행 중 git 호출 로그를 관측한다 | multi-repo 경로에서 `sparse-checkout` 호출이 0건이다. `taskCapsuleCone`이 전개되지 않는다 | integration(CLI+git 호출 관측) | 구현 전 RED |
| S-25 | C-9 | 구현 완료 상태 | `worktree_tool.py`·`test_worktree_tool.py`의 `@header`를 읽고 `code-scan validate --changed <변경 파일>`을 실행한다 | `description`이 신규 계약(R-1~R-5·overlap·plan_entries 단일 소비·회수 역순·2축 멱등·오류 코드 5종)을 반영한다. validate 통과 | 결정론 검사(code-scan) | 구현 후 |
| S-26 | H-1, AC-16 | M0(R-5 만족) | `create` 성공 직후 루트 slot에서 `git status --porcelain` 실행 | 출력이 공백이다. 자식 worktree 생성이 루트 slot을 dirty로 만들지 않는다 | integration(CLI+git) | 구현 전 RED |
| S-27 | H-1 | V5(R-5 미충족)를 pre-flight 없이 강제 통과시킨 대조군 | 루트 slot에서 `git status --porcelain` 실행 | `?? workspace/`가 나타난다 — R-5가 없으면 루트가 항상 dirty가 됨을 반증으로 고정한다. 이 대조군은 구현 경로가 아니라 조건의 필요성을 증명한다. 구현 전후 동일 관측이 정상이므로 RED 대상이 아니다 | integration(CLI+git) | 구현 후 |
| S-28 | H-5 | M0 | M0 형상과 제안서 §2 pug 실측표(루트가 `tasks`+`.opal` 추적, `workspace/` 0파일 추적, 자식 base branch 상이)를 대조한다 | 세 축이 모두 일치한다. 불일치 축이 있으면 fixture를 수정한다 | 결정론 검사(fixture 구성 대조) | 구현 전 RED |
