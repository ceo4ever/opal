# OPAL 워크트리 태스크 소유권 전환 제안서

> 상태: 적용완료
> 적용 범위: Phase 0·Phase 1(태스크 118). 규범 원문은 `opal/core/references/harness/worktree.md`가 소유한다 —
> §task root와 allocator root 계약 · §canonical path 발급 계약 · §cone 확장 계약 · §Phase 1 진입 legacy gate 절차.
> **미이관**: §8 multi-repo 계약(`task_artifacts.repo`)은 아직 owner 문서로 옮기지 않았다. Phase 4 착수 시
> 이 절을 `harness/worktree.md`로 이관한 뒤 소비한다. Phase 2·3은 롤아웃 로드맵이며 후속 태스크가 재계획한다.
> 작성: 알투(PM)
> 작성일: 2026-09-11
> 개정 기준일: 2026-09-12
> 목적: 워크트리를 선택한 태스크의 코드·태스크 산출물·실행 상태를 하나의 작업본이 소유하고, Git merge로 기본 작업본에 귀속시키는 계약을 정의한다.

---

## 1. 결론

`--worktree`를 선택한 태스크는 코드만 워크트리에서 수정하고 태스크 문서는 허브에서 수정하는
현행 분할 소유를 폐지한다. 활성 태스크의 코드와 `tasks/{현재 태스크}`는 해당 태스크 워크트리가
함께 소유한다. 완료 후 브랜치를 기본 브랜치에 merge하면 코드 변경과 새 태스크 폴더가 같은
변경 집합으로 귀속된다.

Git worktree는 저장소를 새로 clone하지 않고 같은 Git object store를 공유한다. 이 프로젝트의
monorepo worktree는 전체 checkout이 아니라 `worktree-tool`의 sparse-checkout cone을 사용한다.
현행 cone에는 코드 디렉터리만 있고 `tasks/`와 `.opal/`이 빠져 있다. 새 모델은 cone에 두
디렉터리를 추가해 기존 태스크·프로젝트 규범과 현재 태스크 캡슐을 worktree에 실체화한다.
기존 태스크를 수정하지 않으면 merge 대상이 되지 않으므로 현재 태스크 하나만 남기는 더 좁은
sparse 패턴은 사용하지 않는다.

핵심 원칙은 다음과 같다.

1. 워크트리 태스크의 canonical task path는 워크트리 안의 `tasks/{현재 태스크}`다.
2. PM과 워커는 같은 canonical task path를 사용한다.
3. 기존 태스크 폴더는 checkout돼 있어도 읽기 전용이며 현재 태스크 폴더만 생성·변경한다.
4. 코드, 태스크 문서, `state.json`, 표준 실행 로그와 태스크 락은 같은 브랜치 수명주기를 따른다.
5. `.opal`은 worktree에 checkout해 규범·설정·brain snapshot을 사용하되, 회고적 brain 학습은 후보만 남기고 merge 후 허브에서 수행한다.
6. 활성 실행 중 허브 공용 쓰기는 `last_task_number`와 `.opal-worktrees/.meta/` registry 두 가지뿐이다.
7. merge가 확인되기 전에는 워크트리를 제거하거나 태스크를 허브 완료본으로 간주하지 않는다.
8. `--worktree`를 사용하지 않는 태스크는 계속 허브 `tasks/`를 사용한다.

---

## 2. 배경

### 2.1 현행 구조

현행 `harness/worktree.md`는 다음처럼 소유권을 나눈다.

```text
허브 작업본
├── tasks/{현재 태스크}/    ← PM·상태·산출물
├── .opal/                  ← MEMORY·brain·프로젝트 정보
└── .opal-worktrees/
    └── task_NNN/           ← 코드 변경만
```

워크트리에서 실행하는 도구도 `tasks/`와 `.opal/`을 참조할 때 `.opal-worktrees` 세그먼트의
부모를 허브 루트로 계산한다. 반면 빌드·검증은 워크트리 소스를 사용한다.

### 2.2 현행 구조의 한계

하나의 태스크가 두 작업본에 갈라진다.

- 코드 diff와 태스크 의사결정·상태가 서로 다른 Git 작업본에 존재한다.
- 워커는 워크트리에서 실행하지만 task path는 허브로 역산해야 한다.
- PM과 워커가 서로 다른 cwd에서 같은 상태·로그·락을 찾기 위해 별도 허브 정규화가 필요하다.
- 브랜치를 merge해도 허브에서 따로 수정된 태스크 문서는 그 merge의 일부가 아니다.
- 워크트리 브랜치만으로 코드 변경과 실행 증거를 함께 리뷰하거나 복원할 수 없다.
- 현재 sparse cone이 `.opal`과 `tasks`를 제외해 과거 태스크를 인용하는 테스트가 워크트리에서 구조적으로 실패한다.

특히 실행 로그 제안의 `<task-path>/.opal-task.lock`은 task path 소유자가 명확하지 않으면 허브
프로세스와 워크트리 프로세스가 서로 다른 락을 잡을 수 있다. 허브 경로를 강제하는 것은 현행
규칙을 보존하는 보정일 뿐, 코드와 태스크 기록을 함께 격리한다는 worktree 목적을 충족하지 않는다.

#### 가장 큰 구조적 비용: 허브 루트 보정 계층

태스크 109에서 도입한 `.opal-worktrees` 세그먼트 기반 허브 정규화는 worktree에 `.opal`과
`tasks`가 없다는 결손을 보정하기 위해 존재한다. 이 규칙은 다음 런타임과 계약에 분산돼 있다.

| 영역 | 현행 보정 | worktree에 `.opal`이 있을 때 |
|---|---|---|
| `code-scan` | `hubRootFromPath()` 후 `findProjectRoot()` | 첫 `.opal` 조상인 worktree root에서 탐색 종료 |
| `event-loader` | `_hub_root()`가 `.opal-worktrees` 부모를 우선 반환 | 해당 우선 분기를 제거하면 `.git + .opal/AGENT.md`로 worktree root 반환 |
| `brain-tool` | `hub_root()`와 `_hub_cwd()` | cwd의 `.opal/brain`을 직접 사용 가능 |
| Console backend | `paths.py:hub_root()` | active registry와 task home 조회로 대체 |
| `state-tool` | 가장 가까운 `.opal/MEMORY.json`을 찾는 단일 `find_project_root()` | task 설정에는 맞지만 allocator/history에는 잘못된 worktree 사본 선택 |

공유 골든 표 `hub-root-cases.json`, code-scan·brain-tool·Console의 세 테스트 스위트,
`worktree.md`의 허브 루트 규칙과 부칙도 같은 보정 계층을 소유한다. `.opal`과 `tasks`를 cone에
넣으면 이 계층을 제거할 수 있어 새 경로 계약의 구현 비용을 상당 부분 상쇄한다.

보안 경계도 약해지지 않는다. worktree 안의 상향 탐색은 자기 `.opal`에서 멈추므로
`$HOME/.opal`까지 탈출하지 않는다. 다만 worktree 밖의 일반 경로에는 가장 가까운 Git 경계까지만
탐색하는 제한을 계속 적용한다. 제거 대상은 무제한 조상 탐색 방어가 아니라
`.opal-worktrees` 문자열을 발견하면 무조건 허브로 보내는 특례다.

---

## 3. 목표와 비목표

### 3.1 목표

- 워크트리 태스크의 코드·산출물·상태·로그를 같은 브랜치가 소유한다.
- 활성 태스크의 canonical path를 cwd 추측이 아니라 도구가 발급한 메타데이터로 결정한다.
- monorepo sparse cone에 `tasks`와 `.opal`을 포함해 프로젝트 작업본을 자기완결시킨다.
- `.opal-worktrees` 세그먼트 기반 허브 정규화와 그 중복 구현·골든표를 제거한다.
- task root와 allocator root를 분리해 브랜치 설정과 허브 동시 쓰기를 섞지 않는다.
- 회고적 brain 학습을 merge 후 허브 finalize로 모아 병렬 branch의 page·index·log 충돌을 없앤다.
- PM과 워커가 같은 `state.json`, run-log, task lock을 사용하게 한다.
- 기존 태스크 폴더가 함께 checkout되는 정상 Git 동작을 허용하되 비현재 태스크 변경을 차단한다.
- 태스크 생성, 실행, commit, merge, 정리의 수명주기를 닫는다.
- monorepo와 multi-repo에서 태스크 산출물이 어느 저장소에 귀속되는지 명시한다.
- 비워크트리 태스크와 기존 활성 태스크의 호환성을 유지한다.

### 3.2 비목표

- Git worktree를 별도 clone으로 바꾸지 않는다.
- 현재 태스크만 남기는 비표준 sparse 패턴이나 non-cone sparse checkout은 도입하지 않는다.
- 여러 브랜치의 `.opal/MEMORY.json`을 자동 병합하는 범용 merge 엔진을 만들지 않는다.
- 사용자의 merge·rebase·충돌 해결 권한을 자동화 도구가 대신 행사하지 않는다.
- 기존 완료 태스크를 일괄 이동하거나 과거 브랜치를 재작성하지 않는다.
- task branch 밖의 사용자 변경을 자동 commit하거나 되돌리지 않는다.

---

## 4. 용어와 소유권 모델

### 4.1 용어

| 용어 | 정의 |
|---|---|
| 허브 작업본 | 사용자가 연 프로젝트 기본 작업본. 프로젝트 공용 조정 데이터와 worktree registry를 소유한다. |
| 태스크 워크트리 | `.opal-worktrees/task_{NNN}` 아래 생성된 태스크 브랜치 작업본 또는 multi-repo 작업본 집합 |
| 현재 태스크 | 해당 worktree metadata의 `task_id`와 연결된 유일한 태스크 |
| task home | 현재 태스크의 프로젝트 파일을 해석하는 기준 작업본 |
| canonical task path | `<task_home>/tasks/<task_folder>`의 정규화된 절대 경로 |
| 태스크 캡슐 | 현재 태스크 폴더 안의 TASK·PLAN·state·검증·완료·실행 로그 전체 |
| task root | 태스크 문서·브랜치 설정·brain 조회·코드 스캔의 기준인 현재 작업본 루트 |
| allocator root | task number와 merge 후 brain·MEMORY 귀속 쓰기에만 쓰는 명시적 허브 절대 경로 |
| brain 학습 후보 | 작업 중 발견했지만 태스크의 직접 산출물은 아닌 회고적 지식. 태스크 캡슐에 근거만 남기고 merge 후 허브에서 판정한다. |

### 4.2 목표 구조

단일 저장소 또는 monorepo의 기본 구조는 다음과 같다.

```text
허브 작업본/
├── .git/
├── .opal/
├── tasks/
│   └── 기존 완료·비워크트리 태스크
└── .opal-worktrees/
    ├── .meta/
    │   └── task_NNN.json         ← 허브 공용 위치 레지스트리
    └── task_NNN/
        ├── .git                  ← 허브 Git 저장소를 가리키는 worktree 연결
        ├── 소스 코드
        ├── .opal/                ← 브랜치 snapshot과 브랜치 변경
        └── tasks/
            ├── 기존 태스크들     ← checkout되지만 기본적으로 변경 금지
            └── NNN-.../          ← 현재 태스크 캡슐 SSOT
```

Git merge는 파일의 존재가 아니라 base 대비 변경을 반영한다. 기존 `tasks/*`가 워크트리에 함께
있어도 수정되지 않았다면 diff와 merge에 포함되지 않는다.

monorepo의 sparse cone은 기존 코드 경로에 다음 두 항목을 더한다.

```text
tasks
.opal
```

이 확장은 `repos`와 분리된 신규 optional 설정 키 `taskCapsuleCone`(`list[str]`, 기본값 `[]`)이
소유한다. monorepo 분기의 `sparse-checkout set`에만 `repos`에 이어 전개하고 multi-repo 분기에는
적용하지 않는다 — `repos`의 "독립 저장소 목록"이라는 의미를 보존해야 하기 때문이다. 타입 위반은
기존 `CONFIG_INVALID_TYPE`, 경로 이탈은 기존 `CONFIG_PATH_ESCAPE`로 보고하며 신규 에러 코드를
만들지 않는다. 기본값 `[]`의 전개는 no-op이므로 비워크트리·기존 워크트리 동작을 바이트 동일하게
보전한다. 위 두 항목을 담은 운영 권고값 `["tasks", ".opal"]`은 Phase 2 활성화 값이며 이 키가
도입되는 단계의 기본값이 아니다. 계약 원문은 `harness/worktree.md` §cone 확장 계약이 소유한다.

전체 `tasks/`를 선택하는 이유는 과거 태스크 인용과 실파일 fixture를 유지하기 위해서다. 현재
태스크 폴더만 선택하면 비현재 태스크 변경은 구조적으로 막을 수 있지만, 과거 TASK·PLAN·DONE을
참조하는 표준 프로세스와 회귀 테스트가 계속 실패한다. 이 저장소의 git-tracked `tasks/**`는
파일 1,114개, 그중 Markdown 888개다(2026-09-12, `feat/OP-TASK-118` 기준). 측정은
`git ls-files tasks`의 출력 행 수와 그중 `.md`로 끝나는 행 수로 한다 — `find tasks -type f`
기준은 활성 태스크의 미커밋 파일 때문에 같은 세션 안에서도 값이 계속 변해 재현되지 않으므로
근거 수치로 쓰지 않는다. 어느 기준이든 파일 수보다 기존 계약의 완전성을 우선한다. 비현재
태스크 무변경은 R-2 gate로 집행한다.

현재 `.opal/code-scan.json`은 `tasks`를 이미 exclude한다. 따라서 cone에 `tasks`를 추가해도
code-scan의 스캔 대상과 탐색 비용은 늘지 않는다. 변화하는 것은 과거 태스크 인용과 실파일
fixture의 가용성이다.

### 4.3 경로별 소유권

| 자산 | 워크트리 태스크 실행 중 소유자 | 귀속 방식 |
|---|---|---|
| 소스 코드·테스트 | 태스크 브랜치 | 일반 Git merge |
| `tasks/{현재 태스크}` | 태스크 브랜치 | 일반 Git merge |
| 현재 태스크의 `state.json`, `STATE.md` | 태스크 브랜치 | 태스크 폴더와 함께 merge |
| 현재 태스크의 run-log·검증 산출물 | 태스크 브랜치 | 추적 정책에 따라 merge |
| 현재 태스크의 `.opal-task.lock` | 태스크 워크트리 runtime | gitignore, merge하지 않음 |
| `.opal`의 규범·프로젝트 파일과 명세가 직접 요구한 brain 문서 | 태스크 브랜치 | 선언된 변경분만 일반 merge |
| 회고적 brain 학습 | 태스크 캡슐이 후보·근거를 소유 | merge 후 최신 허브 brain에서 page 생성·갱신 여부 판정 |
| `.opal/brain/index.md`, `log.md` | 허브 귀속 후처리 | 학습 page 확정 후 허브에서 재구성·기록 |
| `last_task_number` | 허브 `.opal/MEMORY.json`의 기존 원자적 allocator | 생성 전에 allocator root에서 1회 발급 |
| 활성 worktree registry | 허브 `.opal-worktrees/.meta/` | runtime SSOT, 브랜치에 복제하지 않음 |
| CLOSE 후 프로젝트 history 갱신 | merge 확인 후 허브 | merge된 태스크를 가리키는 후처리 |

`.opal`의 추적 파일은 worktree에 실체화하고 현재 브랜치가 사용하는 규범·설정·지식으로 취급한다.
활성 실행 중 여러 브랜치가 즉시 공유하는 허브 쓰기는 `last_task_number`와 registry뿐이다.
MEMORY history와 회고적 brain 학습·집계 갱신은 active branch의 공유 쓰기가 아니라 merge 뒤 기본 브랜치에서
실행하는 귀속 후처리다.

`state.json.worktree`는 merge 뒤에도 실행 출처를 보존하는 역사 필드로 해석한다. 활성 상태의
canonical path를 이 문자열만으로 계산하지 않는다. registry가 `active`일 때는 등록된 worktree
task path를, merge 확인 뒤 `closed`일 때는 허브에 merge된 task path를 반환한다. 따라서 제거된
worktree 절대 경로가 완료 태스크의 현재 위치로 오인되지 않는다.

---

## 5. canonical path 계약

### 5.1 위치 발급

`worktree-tool create` 성공 응답과 `.opal-worktrees/.meta/task_{NNN}.json`은 다음 값을 소유한다.

```json
{
  "task_id": "116",
  "workspace_mode": "worktree",
  "worktree_root": "/abs/project/.opal-worktrees/task_116",
  "task_home": "/abs/project/.opal-worktrees/task_116",
  "task_folder": "116-260911-opds-example",
  "task_path": "/abs/project/.opal-worktrees/task_116/tasks/116-260911-opds-example",
  "artifact_repo": ".",
  "allocator_root": "/abs/project"
}
```

- `task_path`는 `task_home/tasks/task_folder`와 동일한 `realpath`여야 한다.
- `task_folder`는 basename만 허용하며 `/`, `..`, NUL과 경로 구분자를 거부한다.
- PM, 워커, state-tool, run-log-tool은 이 발급값을 전달받아 사용한다.
- cwd에서 `.opal-worktrees` 문자열을 찾아 task path를 추측하지 않는다.
- 등록된 worktree 태스크에 허브 `tasks/{task_folder}`가 동시에 있으면 자동 선택하지 않고 `task_path_ambiguous`로 차단한다.

### 5.2 task root와 allocator root

루트는 용도별로 두 개이며 서로 대체하지 않는다.

| 루트 | 결정 방법 | 소비자 | 쓰기 대상 |
|---|---|---|---|
| `task_root` | canonical task path에서 가장 가까운 `.git`·`.opal` 작업본 또는 명시 `task_home` | code-scan, event-loader, brain-tool, state의 설정·gate | branch의 `.opal`, `tasks`, source |
| `allocator_root` | worktree registry가 발급한 허브 절대 경로 | task-number, merge 후 history | 허브 `.opal/MEMORY.json` |

`allocator_root`는 cwd, task path의 조상, `.opal-worktrees` 문자열로 추론하지 않는다. 허브 PM은
worktree를 만들 때 이 값을 registry에 기록하고, CLOSE 후 merge 귀속 단계가 명시 인자로
memory-tool에 전달한다. worker와 일반 state 변경 명령에는 allocator write 권한을 주지 않는다.

현행 `state-tool.find_project_root()`는 두 역할을 함께 맡고 있으므로 분리한다.

- code-scan 설정 gate는 `task_root()`를 사용한다.
- CLOSE 마지막 mark는 MEMORY history를 즉시 append하지 않고 `completed_unmerged`만 확정한다.
- merge 확인 명령만 `allocator_root`의 MEMORY history를 append한다.
- worktree `.opal/MEMORY.json`은 읽기 snapshot이며 state-tool의 쓰기 대상이 아니다.

### 5.3 비워크트리와 legacy

| 상태 | canonical task path |
|---|---|
| 신규 `--wt` 태스크 | registry의 절대 `task_path` |
| 신규 비워크트리 태스크 | `<hub>/tasks/<task_folder>` |
| 전환 전 생성된 활성 worktree 태스크 | 기존 `state.json`이 있는 허브 task path 유지 |
| 완료 legacy 태스크 | 현재 위치 유지 |

기존 활성 태스크를 실행 중간에 자동 이동하지 않는다. 태스크별 `task_ownership_version`으로 신규
계약과 legacy 계약을 구분한다. legacy worktree가 허브 자산을 필요로 하면 기존 registry/meta의
명시적 `project_root`를 전달한다. `.opal-worktrees` 경로 문자열을 잘라 허브를 추론하는 구현은
legacy 호환을 이유로 유지하지 않는다.

### 5.4 단일 복사본 불변식

현재 태스크의 쓰기 가능한 태스크 캡슐은 하나만 존재해야 한다.

- 신규 worktree 태스크는 허브에 같은 `task_folder`를 미리 만들지 않는다.
- 도구는 허브와 워크트리 양쪽에 같은 폴더가 있으면 쓰지 않는다.
- symlink로 두 위치를 연결해 단일성을 흉내 내지 않는다.
- migration은 source와 destination의 hash를 검증한 명시 명령으로만 수행한다.

---

## 6. 태스크 수명주기

### 6.1 생성 순서

현행의 “허브 태스크 생성 → worktree 생성” 순서를 다음으로 바꾼다.

```text
1. 허브 allocator가 task number를 원자 발급
2. task folder 이름과 브랜치 이름을 메모리에서 확정
3. worktree-tool create가 cone에 tasks·.opal을 포함해 브랜치와 worktree를 생성
4. worktree의 .opal·tasks 착지와 task_root를 검증
5. registry에 allocator_root/task_home/task_path를 원자 기록
6. 워크트리 안에 tasks/{현재 태스크} 생성
7. op-task가 전달받은 canonical task path에 TASK.md 작성
8. state-tool init을 canonical task path에서 실행
9. PM·워커 모두 같은 task_path로 실행
```

worktree 생성이 실패하면 registry와 worktree 생성물을 도구가 롤백한 뒤, 사용자가 선택한 기존
fallback 정책에 따라 허브 비워크트리 태스크를 생성한다. 실패 전에 허브 task folder를 만들지
않으므로 빈 폴더나 이중 SSOT가 남지 않는다.

### 6.2 실행

- 디스패치 프롬프트는 `project_root`, `task_home`, `task_path`, 필요한 repo worktree path를 구분해 전달한다.
- 태스크 문서·state·run-log·락은 `task_path` 아래에서만 읽고 쓴다.
- 빌드·테스트·코드 스캔은 task branch의 소스 경로를 사용한다.
- 현재 태스크 외 `tasks/*` 변경은 기본적으로 conformance gate가 거부한다.
- 프로젝트 공용 docs와 TASK/PLAN이 직접 산출물로 선언한 `.opal/brain` 경로만 일반 branch diff로 허용한다.
- 회고적 brain 학습은 worktree의 brain 파일을 바꾸지 않고 `DONE.md`의 표준 학습 후보 절에 제목·요약·근거를 남긴다.

### 6.3 완료와 merge

pipeline CLOSE와 worktree 회수는 같은 사건이 아니다.

1. 워크트리 안에서 TEST와 CLOSE를 완료한다.
2. 현재 태스크 캡슐과 코드 변경을 같은 branch commit 집합에 포함한다.
3. 기존 worktree-tool guard로 dirty·unpushed·unmerged 상태를 검사한다.
4. 사용자가 선택한 방식으로 branch를 기본 브랜치에 merge한다.
5. 도구가 merge commit 또는 ancestor 관계로 해당 branch 귀속을 확인한다.
6. 허브에서 merge된 `tasks/{현재 태스크}`의 hash와 registry의 완료 hash를 대조한다.
7. merge된 태스크의 brain 학습 후보를 최신 허브 brain과 대조해 page 생성·갱신·생략을 판정하고, index 재생성과 log 기록까지 수행한다.
8. 최신 허브 MEMORY에 현재 태스크의 memory index 요청과 history를 적용하고 history FIFO를 정리한다.
9. 7·8단계가 만든 추적 변경을 merge commit에 포함하거나 직후 단일 finalize commit으로 확정한다.
10. 미처리 memory index 요청 0건과 허브의 미커밋 귀속 변경 0건을 검증한다.
11. registry를 closed로 바꾸고 worktree를 제거할 수 있게 한다.

merge 전 CLOSE는 “태스크 실행 완료”지만 “허브 귀속 완료”는 아니다. Console과 status는 이를
`completed_unmerged`로 표시한다. merge 전에는 허브 `tasks/`에 별도 완료본을 복사하지 않는다.

merge 귀속 후처리의 주체는 merge를 수행하는 coordinator(PM 또는 사용자)다. 두 경로만 허용한다.

| 경로 | 처리 |
|---|---|
| merge commit에 포함 | `git merge --no-ff --no-commit <branch>`로 FF를 명시적으로 막고, commit 확정 전 brain/MEMORY 후처리를 실행해 merge commit 하나로 확정 |
| merge 직후 finalize | FF를 허용했거나 이미 merge commit이 만들어졌다면 즉시 `chore(opal): finalize task NNN attribution` 단일 commit으로 후처리 변경 확정 |

`git merge --no-commit`만으로는 fast-forward를 막지 못한다. FF가 가능할 때 `--no-ff`가 없으면
HEAD가 이미 branch 끝으로 이동하므로 첫 경로로 판정하지 않고 두 번째 경로를 적용한다.

후처리는 `completed_unmerged → attribution_pending → closed` 상태를 따른다. commit 생성이나
clean 검증이 실패하면 `attribution_pending`에 머물며 closed 판정, worktree remove, 다음 귀속
후처리를 허용하지 않는다. 도구가 사용자의 다른 미커밋 변경을 함께 stage하거나 commit하지
않으며, 추적 후처리 파일인 `.opal/MEMORY.json`과 해당 후보로 생성·갱신한
`.opal/brain/pages/*`, `.opal/brain/index.md`, `.opal/brain/log.md`만 정확히 선별한다.

memory index 요청 파일은 이 선별 대상이 아니다. 요청 파일은 태스크 브랜치가 소유하는 추적
파일이므로 그 처리 완료 전이(`status: applied`)는 태스크 커밋에 들어가고, finalize commit은
brain page·index·log와 MEMORY 귀속분만 확정한다. 요청을 처리 완료로 표시하는 시점이 귀속 commit
확정 이후라는 §7.4 계약과, 캡슐 파일 변경을 같은 finalize commit에 넣는다는 서술은 양립하지
않는다 — 유효한 계약은 전자다. finalize의 clean 검증 범위도 같은 이유로 `.opal/brain/**`과
`.opal/MEMORY.json`에 한정한다. 캡슐의 dirty는 이 게이트의 판정 대상이 아니며, 이후 `remove`가
기존 dirty guard(`GUARD_DIRTY`)로 막아 coordinator가 그 변경을 태스크 커밋에 포함하도록
유도한다.

귀속 후처리와 새 task-number 발급은 registry의 프로젝트 finalize lock으로 직렬화한다. 진입
판정은 "미커밋이 하나라도 있으면 차단"이 아니라 선언된 집합에 대한 부분집합 판정이다. 선언
집합은 DONE.md `## 회고적 학습 후보`에 선언된 page 경로에 `.opal/brain/index.md`,
`.opal/brain/log.md`, `.opal/MEMORY.json`을 더한 것이고, 관측 집합은
`git status --porcelain -z -uall` 결과 중 `.opal/brain/**`과 `.opal/MEMORY.json`에 해당하는
경로다. 관측 집합이 선언 집합의 부분집합이면 재개를 허용하고, 아니면 위반 경로 목록과 함께
`ATTRIBUTION_COMMIT_BLOCKED`로 거부한다. `.opal/MEMORY.json`의 선행 diff는 allocator가 만든
`last_task_number` 변경만 허용한다. 판정 범위 밖(소스·태스크 문서)의 dirty는 이 게이트의 판정
대상이 아니다.

선언과 관측은 양쪽 모두 레포 루트 상대 POSIX 경로로 정규화해 비교한다. NUL 구분 출력이
비ASCII 경로의 따옴표 감싸기를 구조적으로 제거하고, rename·copy는 신·구 경로를 모두 관측한다.
이 정규화가 어긋나면 부분집합 판정이 늘 거짓이 되어, 1차 실행이 남긴 미커밋 brain page가
재실행 자신을 영구히 차단한다. 선언 집합의 거처는 `harness/done-template.md`가 소유한다.

finalize commit은 현재 task의 brain page/index/log와 MEMORY history·index 반영분, 그리고 그 시점의
유효한 allocator 값을 함께 확정한다.
lock 해제 후 다음 채번이 MEMORY를 다시 dirty하게 만들 수 있으므로 R-18의 clean 판정은 전체
`git status`가 아니라 미커밋 brain 집계와 `.opal/MEMORY.json` 귀속 변경이 0건인지를 검사한다.

### 6.4 삭제와 복구

- worktree remove는 dirty, unpushed, unmerged뿐 아니라 task capsule 부재와 hash 불일치도 거부한다.
- registry가 `attribution_pending`이면 worktree remove를 거부한다.
- 미처리 memory index 요청이 있으면 worktree remove를 거부한다.
- `--force`는 사용자 명시 승인과 손실 대상 목록을 요구하며 branch는 삭제하지 않는다.
- worktree 디렉터리가 사라졌지만 branch가 남아 있으면 같은 branch로 복구 worktree를 생성한다.
- branch까지 없고 merge도 되지 않았다면 자동 복구 가능하다고 보고하지 않는다.
- merge가 확인되면 허브의 태스크 폴더가 새 canonical path가 되고 registry는 역사 포인터만 유지하거나 정리한다.

---

## 7. `.opal` 경계와 병렬 merge

### 7.1 worktree로 이전하는 자산

추적되는 `.opal` 자산은 해당 branch가 checkout한 버전을 사용한다.

- `.opal/AGENT.md`
- `.opal/brain/pages/`와 `SCHEMA.md`
- `.opal/code-scan.json` 등 버전 관리되는 프로젝트 규범·설정
- task 구현이 함께 변경해야 하는 `.opal` 문서와 스키마
- `.opal/MEMORY.json`의 읽기 snapshot

태스크 시작 후 기본 브랜치의 규범이 바뀌었다면 일반 Git rebase/merge로 받아들인다. 런타임이
worktree `.opal`을 무시하고 허브 최신본을 몰래 섞지 않는다. 어떤 규범과 설정으로 작업했는지가
branch commit으로 재현돼야 한다.

Git에 추적되지 않는 `.opal` 로컬 설정은 sparse cone만으로 실체화되지 않는다.
`.opal/setting.local.json`처럼 worktree 실행에 필요한 파일은 `.opal/worktree.json`의 기존
`copy[]`에 명시해 생성 시 복사한다. copy 대상이 아니면 해당 로컬 설정은 worktree에서
미지원임을 경고하고, 조용히 허브 파일을 읽거나 전역 설정만으로 동일하다고 간주하지 않는다.
copy는 파일만 지원한다. 디렉터리 입력은 `copy_directory_unsupported` 경고로 건너뛴다.

`worktree-tool create`는 현행의 상대 경로 문자열 응답을 다음 `copied[]` metadata로 확장한다.

```json
{
  "source": ".opal/setting.local.json",
  "destination": ".opal/setting.local.json",
  "source_sha256": "...",
  "destination_sha256": "...",
  "copied_at": "2026-09-12T00:00:00.000Z",
  "return_required": false
}
```

source와 destination은 task/allocator root 기준 상대 경로만 허용한다. 내용이나 비밀값은
metadata에 기록하지 않는다. 두 SHA-256은 `copy2` 직후 계산해 일치해야 하며, 이 검증이
`copied_at`의 판정 시점이다. Phase 1의 copy는 worktree로 향하는 단방향 전달만 지원하므로
`return_required`는 항상 `false`다. 이후 worktree에서 destination이 바뀌어 hash가 달라져도
회수 대상이나 R-19 위반으로 보지 않는다.

`.opal/memory/*.local.md`는 Git ignore 규칙이 정의한 machine-local 자산이다. `copy[]` 입력으로
전달하거나 worktree에서 생성·수정·삭제하지 않으며, memory-tool은 worktree에서 해당 요청을
`local_memory_hub_only`로 거부하고 허브에서 수행하라는 경고를 반환한다. 이 파일에는 copy-back
또는 양방향 동기화 계약을 만들지 않는다.

### 7.2 활성 실행 중 허브에 남는 두 자산

활성 task branch와 별도 수명주기를 가져야 하는 것은 다음 두 가지뿐이다.

1. `last_task_number`: 동시 채번 유일성을 위해 worktree 생성 전 allocator root에서 원자적으로 1회 증가한다.
2. `.opal-worktrees/.meta/` registry: Git 추적 대상이 아니며 활성 슬롯·task path·allocator root·merge 상태를 소유한다.

runtime lock은 위 두 자산 각각의 도구 내부 구현이며 별도의 업무 데이터 SSOT로 세지 않는다.
MEMORY history와 회고적 brain 학습·집계 갱신은 활성 중 허브 공유 쓰기가 아니라 merge가 확인된 뒤 기본
브랜치에서 수행하는 귀속 후처리다.

### 7.3 append·집계 파일 처리

병렬 branch가 같은 집계 파일을 append·재렌더하면 merge conflict가 생긴다. 파일별 계약은 다음과
같다.

| 자산 | SSOT 여부 | worktree 실행 | merge 후 처리 |
|---|---|---|---|
| 명세가 직접 요구한 brain 문서 | 태스크 산출물 | TASK/PLAN에 선언된 경로만 작성·수정 | 일반 merge |
| 회고적 brain 학습 후보 | 판단 근거 | `DONE.md` 표준 절에 제목·요약·근거 기록, brain 파일 변경 금지 | 최신 허브 brain 기준 page 생성·갱신·생략 판정 |
| 회고적 brain page | 학습 원본 | 자동 생성·수정 금지 | 후보 채택 시 허브에서 생성·갱신 |
| `brain/index.md` | pages에서 재생성 가능한 파생물 | 생성·수정 금지 | 최종 pages 기준 `brain-tool index`로 재생성 |
| `brain/log.md` | 현행 append-only 원본 | 직접 append 금지 | 후보 판정과 page 변경을 허브에서 1회 기록 |
| `MEMORY.json.history[]` | 프로젝트 history | worktree 사본에 append 금지 | merge 확인 뒤 allocator root에서 1회 append |
| tracked `.opal/memory/*.md` | 메모리 본문 원본 | 신규 본문은 branch에 작성; 기존 본문 변경·삭제는 Phase 1에서 거부 | 신규 본문은 일반 merge, 기존 본문 변경은 허브 명시 작업 |
| `MEMORY.json.memories[]` | 메모리 index | 사본 변경 금지, 신규 등록은 최소 index 요청으로 기록 | finalize가 최신 allocator root 문서에 적용 |
| `.opal/memory/*.local.md` | machine-local 메모리 | 생성·수정·삭제·copy[] 전달 금지 | 허브에서만 memory-tool로 관리, Git merge 제외 |

`DONE.md`의 brain 학습 후보는 실행할 operation이 아니라 merge 후 판단할 근거다. 각 후보는
제목·요약·근거 파일 또는 검증 결과를 기록하며, 후보가 없으면 `없음`을 명시한다. coordinator는
최신 허브 brain에서 중복과 기존 내용을 확인해 `create`, `update`, `skip` 중 하나를 결정하고 그
결과·대상 page·원천 task를 `brain/log.md`에 남긴다. 별도 operation journal이나 worktree
overlay는 두지 않는다.

`brain/log.md`는 pages로 재생성할 수 있는 파생물이 아니므로 후보 판정과 실제 page 변경을
귀속 단계에서 1회 기록한다. `brain/index.md`는 같은 단계의 최종 pages에서 재생성한다. 태스크
명세가 특정 brain 문서 자체를 산출물로 요구한 경우만 예외적으로 branch에서 변경하며, 이때도
index와 log는 worktree에서 갱신하지 않는다.

### 7.4 memory index 요청

Phase 1은 범용 operation journal이나 MEMORY overlay를 만들지 않는다. 빈도가 높은 신규 메모리
등록만 최소 요청으로 지연하고, 기존 행을 바꾸는 저빈도 명령은 범위에서 분리한다.

| 명령 | worktree 계약 | finalize/허브 계약 |
|---|---|---|
| `append --kind memory` | tracked 본문을 branch에 쓰고 태스크 캡슐에 `memory-index-request` 1건 기록 | merge된 본문과 요청을 확인한 뒤 최신 MEMORY에 index row 추가 |
| `update --kind memory` | Phase 1에서 거부 | merge 후 허브에서 명시 실행; 자동 지연 적용은 후속 설계 |
| `promote` | Phase 1에서 거부 | merge 후 허브에서 명시 실행; 자동 지연 적용은 후속 설계 |
| `delete` | Phase 1에서 거부 | merge 후 허브에서 명시 실행; 자동 지연 적용은 후속 설계 |
| `prune` | worktree 호출 금지 | finalize의 history append 경로가 최신 history에 FIFO=5를 자동 적용 |
| `append/update --kind history` | 직접 실행 금지 | CLOSE/finalize가 merge된 task 기준으로 1회 수행 |
| `task-number` | worktree 호출 금지 | 생성 전 allocator root에서만 실행 |

요청은 태스크 캡슐의 추적 파일 `{task_path}/memory-index-request.json`에 `task_id`, `title`,
`type`, `status`, `file`, `summary`, `body_sha256`, `requested_at` 8필드만 기록한다. 메모리
본문이나 범용 명령 payload, `op_id`, 기대 행 hash는 넣지 않는다.

요청의 "내용"과 "처리 완료" 상태는 거처가 다르다. 내용은 위 캡슐 추적 파일이 소유하고, 처리
완료 상태는 registry meta의 `memory_index_requests_resolved`(처리한 `body_sha256` 목록)가
소유한다. registry는 Git 비추적이라 merge로 허브에 전달되지 않으므로 내용의 거처가 될 수 없고,
`state.json`은 state-tool 전용 소유라 배제한다. 반대로 처리 완료 상태는 허브 로컬에서만 의미가
있고 merge로 전달할 필요가 없다. `remove` guard는 meta의 `task_path`로 캡슐 파일을 읽어
`memory_index_requests_resolved`에 없는 `body_sha256`이 하나라도 남아 있으면 미처리 요청으로
판정해 거부한다.

`show/review`는 MEMORY snapshot을 가상 변경하지 않고 기존 index와 같은 태스크의
`pending_requests` 목록을 구분해 반환한다.

현행 memory-tool에는 title 중복 차단이 없으므로 finalize 경로에 이를 추가한다. finalize lock
안에서 최신 허브 MEMORY와 merge된 본문을 다시 읽어 다음처럼 판정한다.

1. 같은 title이 없으면 schema와 `file`·`body_sha256`을 검증하고 기존 `memory-tool append --kind memory` 경로로 추가한다.
2. 같은 title의 행이 있고 `file`과 현재 본문 hash가 요청과 같으면 이미 적용된 요청으로 간주한다.
3. 같은 title이지만 file 또는 본문 hash가 다르면 `memory_title_duplicate`로 차단하고 `attribution_pending`을 유지한다.

이 동등성 검사가 append와 finalize 사이 중단 후 재실행의 멱등성을 제공한다. 요청은 index 반영과
귀속 commit이 끝난 뒤에만 처리 완료로 표시한다. `update/promote/delete`에 필요한 선행 행 hash,
충돌 진단과 지연 적용은 실제 수요와 충돌 자료를 모은 뒤 별도 단계와 스키마 승인을 받는다.

### 7.5 금지

- 같은 논리 자산을 허브와 worktree에 동시에 갱신하지 않는다.
- worktree 실행 중 허브 `.opal/brain`에 직접 쓰지 않는다.
- 태스크 명세에 선언되지 않은 회고적 학습을 worktree의 brain page·index·log에 직접 쓰지 않는다.
- worktree `MEMORY.json`의 `last_task_number`, `history[]`, `memories[]`를 직접 갱신하지 않는다.
- worktree에서 기존 memory 행·본문이나 `.opal/memory/*.local.md`를 변경하지 않는다.
- CLOSE mark가 조상 탐색으로 MEMORY 위치를 정해 history를 즉시 append하지 않는다.
- merge되지 않은 worktree MEMORY 내용을 허브 history로 간주하지 않는다.
- allocator root를 worker prompt의 상대 경로로 전달하거나 cwd에서 추론하지 않는다.
- untracked `.opal` 파일을 registry·copy 계약 없이 허브에서 직접 읽지 않는다.

---

## 8. multi-repo 계약

multi-repo 프로젝트에서는 `.opal-worktrees/task_NNN/`가 여러 저장소 worktree의 컨테이너일 수
있어 slot root 자체가 Git branch가 아닐 수 있다. 이 경우 태스크 캡슐을 어느 저장소가 merge할지
정하지 않으면 “완료 후 main으로 간다”는 전제가 성립하지 않는다.

worktree 설정에 `task_artifacts.repo`를 명시한다.

```json
{
  "task_artifacts": {
    "repo": "workspace",
    "tasks_path": "tasks",
    "opal_path": ".opal"
  }
}
```

- 지정 repo의 worktree가 `task_home`이다.
- `tasks_path`와 `opal_path`는 해당 repo 안의 상대 경로다.
- 현재 태스크 캡슐은 그 repo branch에 commit·merge된다.
- 여러 repo의 코드 변경은 각각 기존 base-ref/merged guard를 통과해야 한다.
- 설정이 없거나 지정 repo에 `tasks/`가 없으면 local task ownership을 활성화하지 않고 명시적 `task_artifact_repo_missing`으로 중단한다.
- 임의로 slot root에 비추적 task folder를 만들어 성공으로 처리하지 않는다.

1차 pilot은 단일 저장소/monorepo에서 수행하고, multi-repo 활성화는 위 설정과 다중 merge 검증이
구현된 뒤 별도 단계로 연다.

---

## 9. 태스크 락과 run-log 연계

워크트리 태스크의 공용 배타 락은 다음 하나다.

```text
<canonical-task-path>/.opal-task.lock
```

- PM과 워커는 registry가 발급한 동일한 canonical task path를 사용한다.
- 허브 `.opal-task.lock`을 별도로 만들지 않는다.
- task lock은 runtime 파일이며 gitignore 대상이다.
- state-tool과 run-log-tool의 동시성·timeout·프로세스 종료 시 해제 계약은 run-log 제안이 소유한다.
- worktree 태스크의 run-log segment는 태스크 캡슐에 포함돼 branch와 함께 merge된다.
- `.oppl-run/`이나 raw 로그의 추적 여부는 각 로그 제안의 보존 정책을 따른다.

`docs/proposals/opal-task-run-log.md`의 task path와 R-4 fixture는 허브 강제 정규화가 아니라
canonical task path resolver를 참조한다. Phase 1 적용(태스크 118)으로 세그먼트 기반 허브 강제
정규화가 활성 계약에서 제거됐으므로 이 참조는 `harness/worktree.md` §task root와 allocator root
계약을 따른다. 동시성 fixture는 허브 PM과 워크트리 worker가 registry를 통해 같은 워크트리 lock을
획득하는 것을 검증한다.

---

## 10. 도구·문서 변경 범위

### 10.1 도구

| 대상 | 변경 |
|---|---|
| `worktree-tool create` | monorepo cone 확장 키 `taskCapsuleCone`(`list[str]`, 기본 `[]`, 운영 권고값 `["tasks", ".opal"]`은 Phase 2 활성화 값) 신설, task folder 생성 전 worktree 생성, allocator_root/task_home/task_path 발급, copied[] 상대경로·create 직후 SHA-256·시각 metadata 기록, 디렉터리 copy와 local memory 전달 경고 |
| `worktree-tool status/list` | task ownership, canonical path, merge 귀속 상태 표시 |
| `worktree-tool remove` | task capsule commit·push·merge·hash guard 추가 |
| `state-tool` | `find_project_root`를 `task_root`와 명시적 allocator root 소비 경로로 분리; CLOSE history append를 merge 후 명령으로 이전 |
| `state-tool init/show` | canonical task path 수용, `task_ownership_version`과 worktree metadata 검증 |
| task 생성 도구/절차 | 번호 발급과 folder 생성 분리, worktree 성공 후 folder 생성 |
| run-log-tool | 전달받은 canonical task path 아래 lock·segment 사용 |
| `code-scan` | `hubRootFromPath` 제거, worktree의 `.opal`을 찾은 `findProjectRoot`를 task root로 사용 |
| `event-loader` | `.opal-worktrees` 우선 허브 분기 제거, 명시 project root 또는 현재 `.git + .opal/AGENT.md` 사용 |
| `brain-tool` | `hub_root/_hub_cwd` 제거, task root에서는 조회와 선언된 직접 산출물만 허용; 회고적 학습의 page/index/log 쓰기는 명시 allocator root의 finalize 경로로 제한 |
| Console/backend | `paths.py:hub_root` 제거, hub `tasks/`와 active registry의 worktree task를 합쳐 조회하되 task ID 중복 거부 |
| `scanner.resolve_task_dir` | 허용 루트를 hub tasks root와 registry가 등록한 active task root의 realpath 화이트리스트로 확장; 요청값 기반 루트 추가 금지 |
| `routers/doctor.py` | 입력 경로의 리터럴 상태를 보는 동작은 유지하고 폐기된 “허브 정규화 예외” 주석·계약만 제거 |
| memory-tool | worktree MEMORY 직접 쓰기 거부, 신규 memory index 요청 기록·pending_requests 조회, title 동등성 기반 finalize; 기존 행 변경과 local memory는 worktree에서 거부 |
| merge 귀속 명령 | branch merge·task hash 확인 후 brain 후보 판정·page/index/log와 MEMORY index 요청·history·prune을 확정하고 허용 diff만 단일 commit 처리 |

### 10.2 문서 SSOT

| 문서 | 변경 |
|---|---|
| `harness/worktree.md` | 허브 고정 규칙을 task ownership과 `.opal` 분류 계약으로 교체 |
| `harness/task-process.md` | 생성 순서를 번호→worktree→task folder→state init으로 변경 |
| `opal/skills/op-task/SKILL.md` | 생성된 canonical task path에만 TASK.md를 쓰도록 입력·출력 설명 정렬 |
| `pm/dispatch-process.md` | project_root/task_home/task_path/source path 구분 전달 |
| `harness/observability.md` | merge 후 MEMORY history 갱신 시점 정의 |
| `harness/memory-learning.md` | worktree의 tracked 본문/index 요청 분리, 기존 행 변경·local memory의 허브 전용 경계, merge 후 finalize 정의 |
| brain 학습 owner 문서·DONE template | 직접 brain 산출물과 회고적 학습 후보 분리, 후보 필드·create/update/skip 판정·merge 후 finalize 정의 |
| memory/worktree tool README·schema | memory-index-request·pending_requests·copied[] create-time hash·오류 코드·finalize 공개 인터페이스 반영 |
| 각 `opal-pilot-*` | task path를 허브 상대 경로로 가정하는 지시 제거 |
| `docs/PROJECT.md` | tasks·worktree·`.opal` 소유권과 문서 위치 등록 |
| `docs/CONVENTIONS.md` | 허브 루트 포인터를 task root·allocator root 경계로 교체 |
| `opal/core/references/opal-harness.md` | 구형 §2.5 허브 해석 포인터를 새 worktree 소유권 owner 문서 포인터로 교체 |
| `dashboard/backend/routers/doctor.py` | `worktree.md`의 진단 도구 예외 절과 함께 예외 설명·stale §2.5(4) 포인터 제거 |
| `hub-root-cases.json` | 세그먼트 기반 허브 수렴 폐지와 함께 제거; task/allocator root fixture로 대체 |
| code-scan·brain-tool·Console 테스트 | 공유 골든표 테스트를 task root 착지와 명시 allocator root 테스트로 교체 |
| 활성 코드·테스트의 header/주석 | `opal-harness.md §2.5 (4)`·hub-root-cases·hub_root 설명과 import를 새 계약에 맞게 제거·교체 |
| run-log 제안서 | canonical task path와 worktree lock fixture 반영 |

문서에는 경로 판정 알고리즘을 복제하지 않는다. canonical task path의 기계 계약은 worktree-tool
metadata/schema가 소유하고, 하네스 문서는 그 인터페이스와 의미를 참조한다.

---

## 11. 단계별 도입

### Phase 0 — cone 확장과 착지 실측

1. disposable fixture 또는 명시적 shadow cone에만 `tasks`와 `.opal` 추가
2. 해당 fixture/shadow worktree를 생성해 `.git`, `.opal/AGENT.md`, `.opal/MEMORY.json`, `.opal/brain`, `tasks` 실체화 확인
3. code-scan, state-tool, event-loader, brain-tool, Console의 현재 root 판정을 변경 없이 계측
4. code-scan의 첫 `.opal` 조상, event-loader의 Git+AGENT, state-tool의 nearest MEMORY가 worktree에 착지하는지 확인
5. 태스크 107에서 구조적으로 실패했던 `tasks` 실파일 의존 회귀 스위트를 다시 실행해 새 기준선 확정

Phase 0은 소유권을 아직 바꾸지 않고 전제만 실측한다. cone 확장만으로 root가 worktree에
착지하지 않는 소비자가 있으면 Phase 1 제거 범위에 추가한다. 이 실측은 disposable Git fixture나
명시적 shadow cone으로만 수행하며 운영 태스크의 기본 cone을 먼저 바꾸지 않는다. 현행
state-tool을 둔 채 운영 worktree에 MEMORY를 실체화하면 CLOSE가 그 사본에 history를 쓰므로,
Phase 1의 root 분리 전에는 새 cone을 일반 활성화하지 않는다.

### Phase 1 — hub-root 보정 제거와 루트 분리

Phase 1 진입 전 다음 legacy gate를 먼저 통과해야 한다.

```text
active legacy worktree == 0
OR
모든 active legacy slot에 .opal·tasks cone 소급 확장 + root·설정 회귀 검증 완료
```

기본 경로는 기존 worktree를 완료·merge·remove해 0건으로 drain하는 것이다. 소급 확장은 태스크
중단이 불가능할 때만 사용하며, 각 slot에서 `.opal/AGENT.md`, `.opal/code-scan.json`, 필요한
`tasks` fixture가 실체화되고 code-scan·event-loader가 기대한 설정을 읽는지 검증한다. 문서의
명시 `project_root` 약속만으로는 CLI 인자가 없는 code-scan 호출을 보호할 수 없으므로 파일
실체화나 drain 없이 Phase 1에 진입할 수 없다.

1. `hub-root-cases.json`과 `.opal-worktrees` 세그먼트 수렴 규칙 제거
2. code-scan·event-loader·brain-tool·Console의 허브 강제 보정 제거; brain-tool의 조회·직접 산출물과 allocator-root finalize 쓰기 분리
3. state-tool의 `find_project_root`를 task root와 allocator root 경로로 분리
4. CLOSE 시 MEMORY 즉시 append를 중단하고 merge 후 귀속 명령으로 이동
5. worktree metadata에 `allocator_root`, `task_home`, `task_folder`, `task_path`, `artifact_repo`, ownership version 추가
6. copy[]의 create-time copied hash metadata·파일 전용 경고·단방향 전달 계약 구현
7. memory-tool의 신규 index 요청·pending_requests와 title 동등성 기반 finalize 구현
8. canonical task path resolver와 중복·탈출 경로 검증 구현
9. 현행 hub-fixed 태스크를 변경하지 않는 legacy 분기 유지
10. Console이 active worktree task를 읽기 전용으로 함께 발견하는 shadow 조회 구현
11. scanner의 허용 루트를 registry 기반 realpath 화이트리스트로 확장하고 doctor 예외 계약 제거
12. 활성 코드·header·주석·테스트의 stale `opal-harness.md §2.5 (4)` 포인터 정리

Phase 1 완료 조건은 허브 실행의 비워크트리 동작이 바이트 동일하고, worktree 실행의 root·설정·
task fixture 기준선이 새 계약으로 전부 통과하는 것이다.

### Phase 2 — monorepo pilot

1. `opds` 한 프로필에서 번호→worktree→task folder→TASK→state init 순서 활성화
2. task folder·state·로그를 worktree branch 안에 생성
3. PM과 worker의 동일 task path/lock 검증
4. 직접 brain 산출물의 branch merge와 회고적 후보의 worktree 무쓰기·merge 후 page/index/log 반영 검증
5. tracked memory 본문 merge, 신규 index 요청 반영, 기존 행 변경·prune·local memory의 worktree 거부 검증
6. CLOSE → commit → merge 확인 → finalize lock → brain 집계 → MEMORY index/history·prune → 귀속 commit → remove 수명주기 검증
7. `--no-ff --no-commit` merge와 FF 후 finalize commit 두 경로를 실제 Git fixture로 검증
8. 기존 태스크 폴더 무변경과 main merge 결과를 실제 Git diff로 판정

pilot 실패 시 신규 태스크만 hub-owned 방식으로 명시 fallback하며, 생성 중인 폴더를 두 위치에
남기지 않는다.

### Phase 3 — monorepo 확산

- pilot별 task path 가정을 conformance fixture로 제거한다.
- batch 단위로 worktree local ownership을 기본값으로 전환한다.
- 마지막 batch에서 신규 worktree 태스크에 대한 hub-fixed 생성 경로를 폐지한다.
- 기존 active/legacy 태스크의 위치 계약은 종료할 때까지 유지한다.

### Phase 4 — multi-repo

- `task_artifacts.repo` schema와 설정 마이그레이션
- 지정 repo의 task capsule commit·merge 검증
- 복수 repo의 base-ref, push, merge 완료 결합 조건
- 설정 없는 multi-repo의 명시적 차단과 안내

---

## 12. 요구사항·검증 추적표

| ID | 요구사항 | 판정 방법 |
|---|---|---|
| R-1 | 워크트리 태스크의 코드와 태스크 캡슐은 같은 branch가 소유한다 | branch diff에 소스와 현재 task folder가 함께 존재 |
| R-2 | 기존 task folder checkout은 허용하되 변경하지 않는다 | base 대비 현재 태스크 외 `tasks/*` diff 0건 |
| R-3 | canonical task path는 cwd 추측이 아니라 metadata로 결정한다 | 허브·worktree·하위 cwd에서 동일 resolver 결과 |
| R-4 | 같은 태스크 캡슐의 쓰기 가능한 복사본은 하나다 | hub/worktree 중복 fixture가 `task_path_ambiguous`로 실패 |
| R-5 | PM과 worker가 같은 state·run-log·lock을 사용한다 | 서로 다른 cwd의 프로세스가 동일 realpath/inode를 관측 |
| R-6 | worktree 생성 실패가 빈 태스크나 이중 SSOT를 남기지 않는다 | 단계별 fault injection 후 생성물 목록 0 또는 단일 정상본 |
| R-7 | 실행 완료·귀속 처리·최종 완료를 구분한다 | CLOSE 후 `completed_unmerged`, merge 후 `attribution_pending`, 귀속 commit·clean 확인 후 closed |
| R-8 | merge되지 않은 task capsule은 remove로 소실되지 않는다 | dirty·unpushed·unmerged·hash mismatch 각각 거부 |
| R-9 | 활성 중 허브 공용 쓰기는 allocator와 registry뿐이다 | worktree MEMORY·hub brain 무변경, allocator·registry writer conformance |
| R-10 | task number는 병렬 생성에서도 중복되지 않는다 | 허브 allocator 병렬 fixture에서 유일한 NNN 발급 |
| R-11 | 허브 실행은 회귀하지 않고 worktree 기준선은 새 구조로 재수립한다 | 비워크트리 출력 바이트 동일 + cone 확장 뒤 구조적 실패 0건의 새 worktree golden |
| R-12 | Console이 허용된 hub/worktree task를 안전하게 찾는다 | registry realpath 화이트리스트 안에서 ID별 1건, 요청 기반 외부 경로 거부 |
| R-13 | branch merge가 현재 태스크만 main에 추가한다 | 기존 task tree hash 불변, 신규 task와 의도한 공용 변경만 존재 |
| R-14 | multi-repo task capsule은 지정된 repo에 귀속된다 | 설정 repo merge 성공 및 미설정/오지정 차단 |
| R-15 | run-log의 락과 segment가 task branch 수명주기를 따른다 | PM/worker 동시 append와 merge 후 로그 hash 일치 |
| R-16 | 세그먼트 기반 허브 보정은 활성 계약에 잔존하지 않는다 | 4런타임 구현·header/주석/import·골든표·3스위트·현행 규범의 참조 0건; 역사 tasks/archive 제외 |
| R-17 | task root와 allocator root를 혼용하지 않는다 | code-scan은 branch 설정, CLOSE는 worktree MEMORY 무변경, merge 후 허브 history 1건 |
| R-18 | 귀속 학습·집계가 충돌·미커밋 상태로 유실되지 않는다 | 후보별 create/update/skip 기록, 최종 pages 기준 index 재생성·log/history/memory index 요청 적용, 허브 미커밋 귀속 변경 0건 |
| R-19 | untracked `.opal` 설정은 명시적으로 단방향 전달된다 | create 직후 copied[] 상대경로·양끝 hash 일치, 이후 불일치 비위반, 디렉터리·local memory 입력 경고 |
| R-20 | hub-root 제거가 active legacy worktree를 깨뜨리지 않는다 | Phase 1 전 legacy 0건 또는 슬롯별 cone·root·설정 회귀 증거 |
| R-21 | 일반적인 신규 memory 학습이 MEMORY 공유 쓰기 없이 보존된다 | tracked 본문 merge + index 요청 1건; 동일 title 재실행은 동등 처리, 불일치는 차단 |
| R-22 | merge 방식과 귀속 commit 경로가 실제 Git FF 의미론과 일치한다 | `--no-ff --no-commit` 단일 merge commit과 FF+finalize commit fixture 통과 |

---

## 13. 수용 기준

- [ ] 신규 monorepo `--wt` 태스크는 worktree 생성 후 그 안에 태스크 폴더를 만든다.
- [ ] monorepo sparse cone에 `tasks`와 `.opal`이 포함되고 worktree root에 둘 다 실체화된다.
- [ ] 현재 태스크 외 기존 `tasks/*`는 base 대비 변경되지 않는다.
- [ ] PM·worker·state-tool·run-log-tool이 metadata의 동일 canonical task path를 사용한다.
- [ ] 허브와 worktree에 같은 현재 태스크 폴더가 있으면 자동 선택하지 않고 차단한다.
- [ ] 코드와 현재 태스크 캡슐이 같은 branch commit과 merge 결과에 포함된다.
- [ ] CLOSE 후 merge 전 상태와 merge 귀속 완료 상태가 구분된다.
- [ ] 귀속 후처리 변경은 merge commit 또는 직후 단일 finalize commit에 포함되고 허브에 미커밋 귀속 변경이 남지 않는다.
- [ ] merge commit 경로는 `--no-ff --no-commit`으로 FF를 막고, FF를 허용한 경우에는 직후 finalize commit을 사용한다.
- [ ] 귀속 commit 실패 시 `attribution_pending`에서 closed·remove가 차단된다.
- [ ] merge 확인 전 worktree remove가 태스크 캡슐을 소실하지 않는다.
- [ ] `.opal`의 branch 변경은 branch에서 수행하고, 활성 중 허브 쓰기는 `last_task_number`와 registry로 한정된다.
- [ ] CLOSE는 worktree MEMORY에 history를 쓰지 않고 merge 확인 뒤 허브 MEMORY에 정확히 1건 기록한다.
- [ ] tracked memory 본문은 branch로 merge되고 신규 MEMORY index 요청은 finalize에서 정확히 1회 반영된다.
- [ ] show/review는 MEMORY를 overlay하지 않고 같은 태스크의 `pending_requests`를 별도로 표시한다.
- [ ] 동일 title·file·본문 hash의 재실행은 적용 완료로 판정하고, 같은 title의 불일치는 `memory_title_duplicate`로 차단한다.
- [ ] update/promote/delete/prune과 `.local.md` 변경은 worktree에서 허용되지 않으며 prune은 history 반영 뒤 허브 finalize가 수행한다.
- [ ] 회고적 brain 학습은 worktree에서 후보만 남기며 brain page·index·log를 변경하지 않는다.
- [ ] merge 후 각 brain 후보가 최신 허브 기준으로 create/update/skip 판정되고 page·index·log와 판정 기록이 단일 귀속 commit에 포함된다.
- [ ] TASK/PLAN이 직접 요구한 brain 문서만 branch 산출물로 merge되며 index·log는 허브 finalize가 처리한다.
- [ ] `.opal-worktrees` 세그먼트 기반 hub-root 구현·골든표·규칙 문서가 제거된다.
- [ ] 활성 코드의 header·주석·import와 현행 테스트에 stale `opal-harness.md §2.5 (4)` 포인터가 없다.
- [ ] 비워크트리 실행 결과는 기존과 바이트 동일하고 worktree 회귀 기준선은 구조적 실패 없이 재수립된다.
- [ ] Phase 1 진입 시 active legacy worktree가 0건이거나 모든 legacy slot의 cone·root 회귀 검증이 완료돼 있다.
- [ ] untracked `.opal` 로컬 설정은 copy[]로 전달되거나 미지원 경고를 내며 허브 파일로 암묵 fallback하지 않는다.
- [ ] copied[] metadata는 create 직후 양끝 상대 경로·동일 SHA-256·복사 시각을 기록하고, 이후 `return_required=false` 자산의 불일치는 위반으로 보지 않는다.
- [ ] `.opal/memory/*.local.md`의 copy[] 전달과 worktree 생성·수정·삭제는 허브 전용 경고로 거부된다.
- [ ] Console task resolver는 hub와 registry 등록 worktree의 realpath 화이트리스트 밖 경로를 거부한다.
- [ ] doctor의 입력 경로 진단 동작은 유지되지만 폐기된 정규화 예외 계약은 남지 않는다.
- [ ] 비워크트리 및 전환 전 active 태스크는 기존 task path를 유지한다.
- [ ] multi-repo는 `task_artifacts.repo`가 없으면 local ownership을 활성화하지 않는다.
- [ ] 실제 Git fixture에서 기존 태스크 tree hash가 merge 전후 동일하다.
- [ ] run-log 동시성 fixture에서 허브 PM과 worktree worker가 같은 lock inode를 사용한다.

---

## 14. 채택 시 후속 결정

본 제안을 채택하면 다음 결정을 순서대로 수행한다.

1. shadow cone에 `tasks`와 `.opal`을 추가하고 5개 root 소비자의 실제 착지를 측정한다.
2. active legacy worktree를 drain하거나 모든 legacy slot의 cone·root 회귀를 완료한다.
3. `harness/worktree.md`의 허브 고정·세그먼트 수렴 규칙을 task/allocator root 계약으로 교체한다.
4. 4개 런타임의 hub-root 구현·stale 포인터와 공유 골든표를 제거하고 state-tool root 역할을 분리한다.
5. `task-process.md`의 생성 순서를 worktree-first로, `op-task`의 입력을 canonical task path로 정렬한다.
6. worktree metadata schema를 allocator root와 canonical task path의 SSOT로 확장한다.
7. untracked `.opal`의 create-time hashed 단방향 copy 계약과 Console registry realpath 화이트리스트를 구현한다.
8. memory-tool의 신규 index 요청·pending_requests·title 동등성 finalize 계약을 구현한다.
9. brain 후보 판정·page/index/log와 MEMORY index/history·prune의 merge 후 귀속·단일 commit 명령을 구현한다.
10. `--no-ff --no-commit`과 FF+finalize 두 merge 경로를 실제 Git으로 검증한다.
11. run-log 제안서의 lock 경로와 R-4를 새 resolver 기준으로 개정한다.
12. monorepo 한 프로필에서 실제 branch merge pilot을 통과시킨다.
13. multi-repo는 artifact repo 계약이 구현될 때까지 현행 hub-owned 방식으로 유지한다.

이 제안은 “워크트리에도 태스크 파일을 복사한다”는 동기화 설계가 아니다. 활성 태스크 캡슐의
소유권을 branch로 옮기고, Git merge를 유일한 허브 귀속 경로로 삼는 설계다.
