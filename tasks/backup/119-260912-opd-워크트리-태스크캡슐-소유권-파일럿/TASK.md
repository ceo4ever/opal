---
template: sdlc-v2
---
# TASK: 워크트리 태스크 캡슐 소유권 — 생성 순서 전환과 monorepo 파일럿

## Problem

태스크 118이 허브 루트 보정을 걷어내고 `task_root`/`allocator_root` 계약과 발급·거부·finalize 기계장치를 전부 넣었지만, **그 장치를 켜는 스위치가 잠겨 있다.** cone 확장 키 `taskCapsuleCone`의 기본값이 빈 리스트라 워크트리를 만들어도 `tasks/`·`.opal/`이 실체화되지 않고, 태스크 생성 순서도 "폴더 생성 → TASK.md 작성 → worktree 생성" 그대로여서 파이프라인이 태스크 폴더를 여전히 허브에 만든다.

그 결과 워크트리 태스크는 아직도 코드와 태스크 기록이 두 작업본으로 갈라진다. 브랜치만으로는 코드 변경과 실행 증거를 함께 리뷰하거나 복원할 수 없고, PM과 워커가 서로 다른 루트에서 같은 상태·로그·락을 찾는다. 태스크 118 자신이 이 분할 상태로 수행됐다.

전환에 필요한 계약은 이미 `harness/worktree.md`가 소유하고 있고, Phase 1 진입 legacy gate도 active legacy worktree 0건으로 충족됐다. 남은 것은 순서를 뒤집고 스위치를 켠 뒤, 실제 태스크 하나를 그 방식으로 완주시켜 수명주기가 닫히는지 확인하는 일이다.

## Proposed outcome

`--worktree` 태스크를 만들면 번호 발급 다음에 워크트리가 먼저 생기고, 태스크 폴더와 `state.json`이 그 워크트리 안에 생성된다. PM과 워커가 같은 canonical task path를 쓰고, 태스크 캡슐과 코드가 같은 브랜치 커밋에 담긴다.

한 파이프라인 프로필에서 실제 태스크를 이 방식으로 끝까지 돌려, CLOSE → commit → merge 확인 → finalize → 귀속 → worktree 회수까지 수명주기가 실제 Git에서 닫히는 것이 확인된다. merge 방식 두 경로(`--no-ff --no-commit` 단일 커밋과 FF 후 finalize 커밋)가 모두 동작하고, 기존 태스크 폴더는 base 대비 변경되지 않는다.

워크트리를 쓰지 않는 태스크와 전환 전에 만들어진 태스크는 기존 위치 계약을 그대로 유지한다.

## Affected users and systems

- OPAL PM과 워커: 워크트리 태스크의 생성 순서와 산출물 위치가 바뀐다.
- 규범 문서: `harness/task-process.md`(생성 순서), `harness/worktree.md`(cone 활성화 값), `pm/dispatch-process.md`(경로 구분 전달).
- 오케스트레이터: 파일럿 대상 프로필 1종의 SKILL.md.
- 도구: `worktree-tool`(생성 순서·발급), `state-tool`(캡슐 경로 수용·finalize-attribution 접합), `memory-tool`·`brain-tool`(귀속 경로), Console(활성 워크트리 태스크 조회).
- 설정: `.opal/worktree.json`의 `taskCapsuleCone`.
- 범위 제외: Phase 3 전 파이프라인 확산, Phase 4 multi-repo와 `task_artifacts.repo` 계약. 파일럿 프로필 외 오케스트레이터의 생성 경로 전환.

## Constraints

- C-1: `--wt`를 쓰지 않는 실행의 동작·출력은 변경 전과 바이트 동일해야 한다.
- C-2: `~/.opal/` 배포 파일을 직접 수정하지 않는다. 프로젝트 소스만 수정하고 install로 배포한다.
- C-3: 파일럿은 실제 태스크로 수행하되, 실패 시 신규 태스크만 hub-owned 방식으로 명시 fallback하고 생성 중인 폴더를 두 위치에 남기지 않는다.
- C-4: 파이프라인 행 상태 변경은 `state-tool`로만 수행한다. `state.json`·`test-scenario.json` 직접 편집 금지.
- C-5: 전환 전에 생성된 태스크(`task_ownership_version` 부재)의 위치를 자동 이동하지 않는다.
- C-6: 플랫폼 분기를 어댑터 계층 밖에 추가하지 않는다.
- C-7: git 관리 Markdown에 수기 누적 이력 절을 만들지 않는다.
- C-8: 임시 Git fixture는 `/private/tmp` 하위에만 만들고 `git -C`로만 조작한다. 운영 `.opal-worktrees/` 하위에 fixture worktree를 만들지 않는다.
- C-9: 태스크 118이 확정한 계약(`task_root`/`allocator_root` 분리, canonical path 6필드 발급, `S ⊆ D` finalize 재진입, 워크트리 MEMORY 쓰기 거부)을 약화하지 않는다.

## Acceptance criteria

- AC-1: `--wt` 태스크의 생성 순서가 번호 발급 → worktree 생성 → 워크트리 안 태스크 폴더 생성 → TASK.md 작성 → `state init` 순으로 바뀌고, `harness/task-process.md`가 그 순서를 소유한다.
- AC-2: worktree 생성이 실패하면 허브에 빈 태스크 폴더나 이중 캡슐이 남지 않고, 사용자가 선택한 fallback으로 허브 비워크트리 태스크가 생성된다.
- AC-3: `.opal/worktree.json`의 `taskCapsuleCone`이 운영값으로 활성화되고, 신규 워크트리에 `.opal/AGENT.md`·`.opal/MEMORY.json`·`.opal/brain`·`tasks`가 실체화된다.
- AC-4: PM과 워커가 같은 canonical task path를 사용하며, 서로 다른 cwd의 두 프로세스가 동일 realpath와 동일 `.opal-task.lock` inode를 관측한다.
- AC-5: 현재 태스크 외 기존 `tasks/*`가 base 대비 변경 0건임이 실제 Git diff로 판정된다.
- AC-6: 파일럿 태스크의 코드 변경과 태스크 캡슐이 같은 브랜치 커밋 집합에 포함되고, main merge 결과에 둘 다 나타난다.
- AC-7: CLOSE 후 상태가 `completed_unmerged`로 확정되고, merge 확인 전에는 허브 `tasks/`에 완료본이 복사되지 않는다.
- AC-8: merge 확인 후 `finalize-attribution`이 허브 MEMORY history를 정확히 1건 append하고, 재실행이 중복을 만들지 않는다.
- AC-9: `--no-ff --no-commit` 단일 merge 커밋 경로와 FF 후 finalize 커밋 경로가 실제 Git fixture에서 모두 통과한다.
- AC-10: 회고적 brain 학습이 워크트리에서 page·index·log를 변경하지 않고 후보만 남기며, merge 후 허브에서 create/update/skip 판정과 index 재생성·log 기록이 수행된다.
- AC-11: 신규 메모리가 워크트리에서 `memory-index-request`로 지연되고 finalize에서 정확히 1회 반영되며, 기존 행 변경·prune·`*.local.md` 변경은 워크트리에서 거부된다.
- AC-12: 미처리 index 요청이 남은 슬롯의 `worktree-tool remove`가 거부되고, 전부 처리된 뒤에는 기존 3중 가드만 적용된다.
- AC-13: 파일럿 태스크가 생성 → 실행 → CLOSE → commit → merge → finalize → remove 수명주기를 실제로 완주한다.
- AC-14: 비워크트리 실행 결과가 변경 전과 바이트 동일함이 실행 캡처 대조로 실증된다.
- AC-15: 파일럿 실패 시 fallback 절차가 문서에 기재되고, 실패 주입 시 두 위치에 폴더가 남지 않음이 확인된다.
- AC-16: 전환 전 생성된 태스크와 비워크트리 태스크의 위치 계약이 유지됨이 확인된다.
