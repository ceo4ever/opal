---
module: worktree
role: 워크스페이스 축과 태스크 소유권 루트 계약의 단일 SSOT
load: pilot.start
---

# Worktree

## 모드 축과 직교하는 별개 축

`--worktree`(약칭 `--wt`)는 모드 축(`--interactive`/`--semi-agentic`/`--agentic`)과 **직교**한다.

- 모드 축은 "PM이 얼마나 자율적으로 진행하는가"를, 워크스페이스 축은 "코드를 어느 작업본에서 만지는가"를 결정한다.
- 조합 가능: `//opd --agentic --wt`, `//opds --wt` 모두 유효하다.
- `mode_flag_conflict` 판정 대상이 **아니다**. 모드 플래그 개수 검사에 `--wt`를 세지 않는다.
- 서브 하네스 로딩 규칙에 영향을 주지 않는다.

## `--wt` 미사용 시 = 현행 동작 100% 유지

플래그가 없으면 다음이 전부 현행과 동일하다. 어떤 조건부 분기도 실행되지 않는다.

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

- **[MUST] `allocator_root`는 cwd, task path의 조상, `.opal-worktrees` 문자열로 추론하지 않는다.** 허브 PM이 worktree 생성 시 registry에 기록하고, merge 귀속 단계가 명시 인자로 전달한다.
- 워커와 일반 state 변경 명령에는 allocator write 권한을 주지 않는다.
- CLOSE 마지막 mark는 MEMORY history를 즉시 append하지 않고 `completed_unmerged`만 확정한다. history append는 merge 확인 후 귀속 명령만 수행한다.
- 워크트리의 `.opal/MEMORY.json`은 읽기 snapshot이며 state-tool의 쓰기 대상이 아니다.

## canonical path 발급 계약

canonical task path의 **기계 계약은 worktree-tool metadata/schema가 소유한다.** 이 문서는 인터페이스와 의미만 참조하고 경로 판정 알고리즘을 복제하지 않는다.

- `worktree-tool create` 성공 응답과 `.opal-worktrees/.meta/task_{NNN}.json`이 다음 6종 필드를 소유한다: `allocator_root`, `task_home`, `task_folder`, `task_path`, `artifact_repo`, `task_ownership_version`.
- **불변식**: `task_path == realpath(task_home/tasks/task_folder)`.
- `task_folder`는 **basename만 허용**한다. `/`, `..`, NUL과 경로 구분자를 포함하면 거부한다.
- PM·워커·state-tool·run-log-tool은 이 발급값을 전달받아 사용한다. cwd에서 `.opal-worktrees` 문자열을 찾아 task path를 추측하지 않는다.
- **[MUST] 등록된 worktree 태스크에 허브 `tasks/{task_folder}`가 동시에 존재하면 자동 선택하지 않고 `task_path_ambiguous`로 차단한다.**
- `task_ownership_version`이 없는 태스크는 legacy다. 실행 중 태스크 위치를 자동 이동하지 않고 기존 허브 task path를 유지한다. legacy worktree가 허브 자산을 필요로 하면 registry/meta의 명시 `project_root`를 전달한다.

## cone 확장 계약

- 설정 키 `taskCapsuleCone`, 타입 `list[str]`, **기본값 `[]`**.
- monorepo 분기에서만 `repos`에 이어 sparse-checkout cone에 전개한다. **multi-repo 분기에는 적용하지 않는다.**
- 기본값 `[]`의 전개는 no-op이므로 비워크트리·기존 워크트리 동작은 바이트 동일하게 보전된다.
- 운영 권고값 `["tasks", ".opal"]`은 **Phase 2 활성화 값**이다. 이 단계의 기본값이 아니며, 운영 worktree의 기본 cone을 지금 이 값으로 바꾸지 않는다.

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
