---
template: sdlc-v2
---
# TEST-SCENARIO: 워크트리 태스크 캡슐 소유권 — 생성 순서 전환과 monorepo 파일럿

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: macOS / git 2.x(worktree·sparse-checkout cone) / Python 3.14 / Node.js. 허브 `/Volumes/Data/AIStudio/workspace/ai-framework`, 코드 작업본 `.opal-worktrees/task_119`(브랜치 `feat/OP-TASK-119`, base `main`).
- 공통 데이터: monorepo fixture는 `git clone --local <허브>` 후 `git -C <fixture> worktree add`로 만든다. 모든 git 조작은 `git -C`만 쓰고 `cd`를 쓰지 않는다(C-8 — 직전 태스크에서 `cd` 조용한 실패로 운영 허브에 워크트리가 생성된 사고가 2회 있었다). fixture는 `/private/tmp` 하위에만 두고 측정 후 삭제한다.
- 대역 사용과 한계: 사용하지 않음. 생성 순서·cone 착지·상태 의존 경로 해석·merge 수명주기는 전부 실제 git 저장소와 실제 CLI 실행으로 검증한다. 운영 `.opal/MEMORY.json`·`.opal/brain`은 쓰기 대상으로 삼지 않고 fixture 사본에서만 검증한다.
- 실행 조건: 자동 실행. 단 S-19·S-20은 실 `~/.opal/` 배포를 전제하며, 배포는 소유자가 수행한다(PM은 격리 HOME 검증까지만 한다). 파일럿(S-20)의 merge 판단도 소유자 권한이다.
- 배포 선결 조건: 배포 전 `git -C <허브> rev-parse main`이 119 브랜치 base와 같은지 확인한다. 다르면 base가 뒤처진 상태로 install해 타 태스크 배포분이 롤백된다(직전 태스크 실측 사례).

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, C-1 | `--wt` 없는 태스크 생성 | fixture에서 현행 순서로 태스크를 만들고 폴더 생성·TASK.md·`state init` 결과를 base와 대조 | 생성 순서와 산출물 위치가 변경 전과 동일하다. `--wt` 분기가 발동하지 않는다 | integration — 실제 CLI, `/private/tmp` fixture | 구현 전 RED |
| S-2 | AC-1 | `--wt` 태스크 생성 | 재정렬된 순서(번호 → `create --task-folder` → `mkdir -p task_path` → TASK.md → `state init`)를 `harness/task-process.md` 문면대로 실행 | 태스크 폴더와 `state.json`이 **워크트리 안**에 생성되고 허브 `tasks/`에는 생기지 않는다 | integration — 실제 CLI | 구현 전 RED |
| S-3 | AC-1, AC-3 | 채번 명령의 `--file` 인자 | cwd가 워크트리인 상태에서 재정렬된 1스텝(채번)을 실행 | 허브 절대경로로 채번이 성공한다. 상대경로였다면 `WORKTREE_WRITE_REJECTED`로 실패했을 지점이 통과한다 | integration — 실제 CLI | 구현 전 RED |
| S-4 | AC-2, AC-15, C-3 | `worktree-tool create` 실패 주입 | 브랜치 점유·경로 충돌 등으로 `create`를 실패시킨 뒤 fallback 경로를 실행 | 허브에 빈 태스크 폴더나 이중 캡슐이 남지 않는다. fallback으로 허브 비워크트리 태스크가 생성되고 폴더가 **한 위치에만** 존재한다 | integration — fault injection | 구현 전 RED |
| S-5 | AC-3 | `taskCapsuleCone` 활성화 | 새 설정으로 워크트리를 만들고 `git -C <wt> sparse-checkout list`와 실제 실체화를 확인 | cone에 `.opal`·`tasks`가 포함되고 `.opal/AGENT.md`·`.opal/MEMORY.json`·`.opal/brain`·`tasks`가 워크트리에 실체화된다 | integration — 실제 git | 구현 전 RED |
| S-6 | AC-3, C-1 | `taskCapsuleCone` 미설정 fixture | 키 없는 설정으로 `create` 실행 | cone이 `repos` 목록과 동일하다. 키 미지정이 여전히 no-op이다 | unit+integration — worktree-tool 테스트 | 구현 후 |
| S-7 | AC-4, C-9 | registry `attribution_state`가 active 3상태(부재·`completed_unmerged`·`attribution_pending`) | 허브 `tasks/{task_folder}`와 워크트리 캡슐이 동시에 존재하는 상태에서 `worktree-tool status`·`finalize` 호출 | 세 상태 모두 `TASK_PATH_AMBIGUOUS`로 차단된다. 단일 복사본 불변식이 약화되지 않는다 | unit+integration — worktree-tool 테스트 | 구현 전 RED |
| S-8 | AC-4 | registry `attribution_state`가 `closed` | merge 확인 후 같은 조건에서 `status`·`finalize` 호출 | 차단되지 않고 **허브에 merge된 task path**를 canonical로 반환한다. `finalize`는 커밋 없이 멱등 반환한다 | unit+integration — worktree-tool 테스트 | 구현 전 RED |
| S-9 | AC-4 | PM cwd(허브)와 워커 cwd(워크트리) 두 프로세스 | 양측이 `worktree-tool status`가 반환한 canonical `task_path`를 입력받아 `realpath(<task_path>/state.json)`을 관측 | 두 관측값이 동일 문자열이다 | integration — 서로 다른 cwd의 실제 프로세스 | 구현 전 RED |
| S-10 | AC-5 | 현재 태스크 외 기존 `tasks/*` | 새 순서로 태스크를 만들고 base 대비 `git -C <wt> diff --stat tasks/` 실행 | 현재 태스크 폴더 외 변경 0건이다 | 결정론 검사 — 실제 git diff | 구현 후 |
| S-11 | AC-6 | 파일럿 태스크의 코드 변경과 캡슐 | 브랜치 커밋 집합과 merge 결과를 `git show --stat`·`git diff main`으로 확인 | 코드 변경과 태스크 캡슐이 **같은 브랜치 커밋 집합**에 있고 merge 결과에 둘 다 나타난다 | integration — 실제 git | 구현 후 |
| S-12 | AC-7 | CLOSE 완료 직후 | `state-tool show`로 상태를 확인하고 허브 `tasks/`를 조회 | 상태가 `completed_unmerged`이고 merge 확인 전 허브 `tasks/`에 완료본 사본이 없다 | integration — 실제 CLI | 구현 후 |
| S-13 | AC-8 | merge 확인 후 `finalize-attribution` | (a) 정상 1회 실행, (b) 동일 인자 재실행, (c) `--allocator-root` 미지정·상대경로 | (a) 허브 MEMORY history 정확히 1건 append. (b) 중복 append 없음(멱등). (c) 추론 없이 거부 | unit+integration — state-tool 테스트 | 구현 후 |
| S-14 | AC-9 | merge 두 경로 | 경로 B 수명주기를 `git merge --ff-only`와 `git merge --no-ff`로 각각 완주 | 두 경로 모두 finalize 커밋이 merge **전** 브랜치에 확정되고 수명주기가 닫힌다. `--no-ff --no-commit` 단일 merge 커밋 경로는 현행 계약이 아님이 문서에 명시돼 있다 | integration — 실제 git fixture | 구현 전 RED |
| S-15 | AC-10 | 회고적 brain 학습 | 워크트리에서 학습 후보를 남기고 `.opal/brain/pages`·`index.md`·`log.md` 변경 여부를 확인. merge 후 허브에서 판정 수행 | 워크트리에서 brain page·index·log가 변경되지 않고 후보만 `DONE.md`에 선언된다. merge 후 허브에서 create/update/skip 판정과 index 재생성·log 기록이 수행된다 | integration — 실제 파일 상태 | 구현 후 |
| S-16 | AC-11 | 워크트리에서 memory-tool 호출 | `append --kind memory`와 `update`/`prune`/`*.local.md` 변경을 각각 실행 | 신규 메모리는 `memory-index-request`로 지연되고 finalize에서 정확히 1회 반영된다. 기존 행 변경·prune·`*.local.md` 변경은 거부된다 | unit+integration — memory-tool 테스트 | 구현 후 |
| S-17 | AC-12 | 미처리 index 요청이 남은 슬롯 | `worktree-tool remove` 실행 후, 요청을 해소하고 재실행 | 미처리 시 `MEMORY_INDEX_REQUEST_PENDING`으로 거부되고, 해소 후에는 기존 3중 가드(dirty·unpushed·unmerged)만 적용된다 | integration — 실제 슬롯 | 구현 후 |
| S-18 | AC-16, C-5 | `task_ownership_version` 부재 legacy 태스크와 비워크트리 태스크 | 변경 전후로 위치와 registry 상태를 대조 | 위치가 자동 이동되지 않는다. legacy 메타는 모호성 판정 자체를 건너뛴다 | integration — 실제 상태 대조 | 구현 후 |
| S-19 | AC-14, C-1, C-2 | base 소스와 변경 후 소스 | 격리 `HOME`에 각각 install해 **도구 코드만 스왑**하고, 데이터 루트를 `/private/tmp` 고정 fixture로 둔 채 동일 명령 stdout·stderr를 캡처해 `diff` | 모든 대조에서 차이 0줄이다. 대상: `state-tool show`·`validate`, `worktree-tool list`, `memory-tool show --boot-brief`, `code-scan scan`, `event-loader load --event session.project`. 신규 CLI 표면(`--help`·usage·오용 호출)은 대조 대상에서 제외한다 | integration — 실제 install + diff | 설치 후 |
| S-20 | AC-13, AC-6, AC-7, AC-8, C-3 | 실 배포 후 신규 실태스크 1건 | `//opd --wt`로 생성해 생성 → 실행 → CLOSE → finalize → 캡슐 커밋 → merge → `finalize-attribution` → `status --set done` → `remove`까지 완주 | 수명주기가 실제 Git에서 닫힌다. 실패 시 신규 태스크만 허브 비워크트리로 명시 fallback하고 두 위치에 폴더를 남기지 않는다 | manual+integration — 실제 파이프라인. merge 판단은 소유자 권한 | 배포 후 |
| S-21 | H-1, C-9 | D-1 가드 변경 후 | 118이 확정한 4계약(루트 분리·6필드 발급·`S ⊆ D` finalize 재진입·워크트리 MEMORY 쓰기 거부)의 기존 테스트를 재실행 | 네 계약의 기존 테스트가 전부 통과한다. 상태 인지가 **더해졌을 뿐** 불변식이 약화되지 않았다 | unit — 각 도구 스위트 | 구현 후 |
| S-22 | H-2 | 순서 전환 중간 실패 | 새 순서의 각 스텝(채번 후·create 후·mkdir 후·TASK.md 후)에서 중단을 주입 | 어느 지점에서 멈춰도 허브와 워크트리 양쪽에 캡슐이 동시에 남지 않는다 | integration — fault injection | 구현 후 |
| S-23 | H-3 | cone 활성화 후 워크트리의 `.opal` 사본 | 워크트리 안에서 `state-tool`·`memory-tool`·`brain-tool`·`event-loader`·`code-scan`을 호출 | `task_root`가 워크트리 자신에 착지하고, memory-tool 거부 게이트가 동작하며, `.opal/code-scan.json` 사본이 스캔 결과를 바꾸지 않는다. `.opal/worktree.json` 사본은 읽기 snapshot이며 `worktree-tool` 호출은 허브 `--project-root` 명시로 수행된다 | integration — 실제 CLI | 구현 후 |
| S-24 | H-4, C-2 | 배포 직전 | `git -C <허브> rev-parse main`과 119 브랜치 base를 대조 | 동일하면 배포 진행, 다르면 배포를 중단하고 rebase/merge를 선행한다. 타 태스크 배포분 롤백이 발생하지 않는다 | 결정론 검사 — git 대조 | 설치 후 |
| S-25 | H-6, AC-13 | 파일럿 태스크의 변경 대상 | 파일럿 주제의 변경 파일 목록과 119의 변경 7파일을 대조 | 겹침 0건이다. 파일럿이 119 산출물을 덮어쓰지 않는다 | 결정론 검사 — 경로 대조 | 배포 후 |
| S-27 | C-4 | 태스크 119와 파일럿 태스크의 상태 파일 | 작업 전 구간의 `state.json`·`test-scenario.json` 변경 이력을 확인 — 도구 경유 변경만 있었는지 `git diff`와 도구 호출 로그로 대조 | 두 파일에 도구 외 직접 편집 흔적이 0건이다. 모든 행 상태 변경이 `state-tool`, 시나리오 결과가 `test-tool`을 거쳤다 | 결정론 검사 — diff + 호출 대조 | 구현 후 |
| S-28 | C-6 | 변경된 소스 전체 | 어댑터 계층(`install-mac.sh`·`opal/bootstrapper/`) 밖에 플랫폼 조건 분기가 추가됐는지 검사 | 하드코딩 플랫폼 분기 0건이다. 신규 코드가 Claude/Cursor/Gemini를 직접 분기하지 않는다 | 결정론 검사 — grep + 변경 파일 리뷰 | 구현 후 |
| S-29 | C-7 | 변경된 git 관리 Markdown 전체 | `변경이력`·`Changelog`·`개정 이력` 절이 **신규로** 생성됐는지 검사 | 신규 수기 누적 이력 절 0건이다. 선재 이력 표(`harness/memory-learning.md` 등)는 증분 없이 그대로다 | 결정론 검사 — grep | 구현 후 |
| S-30 | C-8 | 이 태스크가 만든 모든 임시 fixture | 전 작업 구간 종료 후 `/private/tmp` 하위 fixture 잔여물과 운영 허브 상태를 실측. `cd <dir> && git` 패턴 사용 여부도 검사 | fixture 잔여물 0건이고 운영 `.opal-worktrees/`에 fixture worktree가 생성된 흔적이 0건이다. 허브 `git worktree list`와 브랜치 목록이 작업 전과 동일하다 | 결정론 검사 — ls + git 대조 | 구현 후 |
| S-26 | AC-13, H-5 | 재정의된 AC-4·AC-9의 검증 가능성 | `.opal-task.lock` 구현 부재 상태에서 재정의된 기준(동일 canonical `task_path`·동일 `realpath(state.json)`)으로 판정 | 재정의된 기준이 실제로 관측 가능하고, lock 도입은 실행 로그 제안서 구현 태스크로 이연됐음이 문서에 기재돼 있다 | 결정론 검사 — 문서 + 실측 | 구현 후 |
