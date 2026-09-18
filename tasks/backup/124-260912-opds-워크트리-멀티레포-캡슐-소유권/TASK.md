---
template: sdlc-v2
---
# TASK: 워크트리 multi-repo 캡슐 소유권 — 계약 이관과 worktree-tool 구현

## Problem

multi-repo 프로젝트는 `--worktree`를 쓸 수 없다. `worktree-tool create`가
`TASK_ARTIFACT_REPO_MISSING`으로 차단하고(`opal/tools/worktree-tool/worktree_tool.py:701-703`),
태스크 캡슐을 소유할 저장소를 지목하는 `task_artifacts` 계약이 구현되지 않았다.
저장소 전역에서 `task_artifacts` 구현은 0건이다.

실사용 대상이 확인됐다. `/Volumes/Data/StoreLinkStudio/pug`는 OPAL 프로젝트이면서 `workspace/`
아래 독립 `.git` 6개를 가진 multi-repo이고, 캡슐 164파일을 추적하는 주체는 `repos[]`에 나타나지
않는 **루트 저장소**다. `_find_independent_git_dirs()`가 루트를 후보에서 명시적으로 제외하기
때문이다(`:501-502`). 선행 제안서 §8은 지정 repo가 `repos[]`의 한 원소라고 암묵 전제해 이
구조에 적용되지 않는다.

또한 루트 worktree가 slot root가 되는 중첩 구조에서는 현행 회수 경로가 안전하지 않다.
`cmd_remove`가 생성 정순으로 순회하고(`:1204-1214`), `git worktree remove` 실패를 관측하지 않으며
(`:1213`), 메타와 slot을 조건 없이 삭제한다(`:1216`, `:1228`). 자식이 남은 채 메타만 사라지면
그 태스크는 도구로 복구할 수 없다.

## Proposed outcome

루트 저장소가 태스크 캡슐을 소유하는 multi-repo 프로젝트에서 `--worktree` 태스크를 생성·실행·
회수할 수 있다. `task_artifacts.repo: "."`를 선언하면 slot root 자체가 루트 저장소의 worktree가
되고 그 아래에 코드 저장소 worktree들이 허브와 동형으로 배치된다. base branch는 저장소마다 다르게
지정할 수 있다.

회수는 생성의 역순으로 수행되며, 한 저장소라도 제거에 실패하면 메타와 slot이 보존되어 재시도할
수 있다. 부분 회수 이후 재호출은 `--force` 없이 성공한다. 도구는 불일치를 자동 복구하지 않는다.

monorepo와 비워크트리 실행은 설정·출력·동작 어느 축에서도 변하지 않는다.

## Affected users and systems

- `opal/tools/worktree-tool/` — `worktree_tool.py`와 테스트 스위트
- `opal/core/references/harness/worktree.md` — 계약 규범 원문
- `docs/proposals/opal-worktree-multirepo-ownership.md` — 적용 완료 시 `archives/`로 이관
- `docs/proposals/archives/opal-worktree-task-ownership.md` — 헤더에 §8 대체 포인터 1행
- multi-repo OPAL 프로젝트 사용자 — 현재 `--worktree` 사용 불가 상태가 해소된다
- 범위 제외: `/Volumes/Data/StoreLinkStudio/pug` 실환경 파일럿(제안서 §11의 4~5단계).
  외부 저장소 사전 조건 처리가 선행되어야 하므로 별도 태스크가 소유한다.
- 범위 제외: `repos[]` 원소를 캡슐 repo로 지정하는 경로. 제안서가 후속 제안 후보로 분리했다.

## Constraints

- C-1: 설계 원문은 `docs/proposals/opal-worktree-multirepo-ownership.md`가 소유한다. 이 문서와
  다른 계약을 구현하지 않으며, 변경이 필요하면 제안서를 먼저 고친다.
- C-2: monorepo 프로젝트의 `create`·`list`·`status`·`remove`·`finalize`·`init` 6명령 출력이
  변경 전과 바이트 동일해야 한다. `init` 초안의 키 집합과 순서를 포함한다.
- C-3: 비워크트리 실행이 변경 전과 바이트 동일해야 한다.
- C-4: `repos[]`의 타입(`list[str]`)과 의미를 바꾸지 않는다.
- C-5: multi-repo 분기에 `taskCapsuleCone` sparse-checkout을 적용하지 않는다
  (태스크 118 결정, `harness/worktree.md` §cone 확장 계약).
- C-6: 회수 실패 시 도구가 `git worktree prune`을 호출하거나 미등록 디렉토리를 삭제하지 않는다.
- C-7: 계약 규범 원문은 `harness/worktree.md`가 소유한다. 제안서를 규범 SSOT로 남기지 않고
  `docs/CONVENTIONS.md` §제안서 생명주기에 따라 `archives/`로 이관한다.
- C-8: `~/.opal/` 배포 파일을 직접 수정하지 않는다. 프로젝트 소스를 고치고 install로 배포한다.
- C-9: 변경한 코드 파일의 `@header`를 현재 사실로 갱신한다.

## Acceptance criteria

- AC-1: `task_artifacts.repo: "."`를 선언한 multi-repo fixture에서 `create`가 성공하고, 루트를
  포함한 전 저장소가 `git worktree list`에 등록된다. slot root가 루트 저장소의 worktree이고
  코드 저장소 worktree들이 그 아래에 배치된다.
- AC-2: 발급된 `task_path`가 slot root 아래 `tasks/{task_folder}`이고 불변식
  `task_path == realpath(task_home/tasks/task_folder)`를 만족한다.
- AC-3: 루트 Git 적격 조건 R-1~R-5(제안서 §4.1)를 각각 단독 위반하는 fixture 5종에서
  `TASK_ARTIFACT_REPO_INVALID`로 차단되고, 오류 payload에 위반 조건 번호가 실린다.
- AC-4: 같은 5종 fixture의 `init` 초안에 `task_artifacts` 키가 나타나지 않는다. R-1 위반
  fixture에서는 `baseBranch`·`_baseBranch_candidates`도 나타나지 않고, 각 코드 저장소의 base-ref가
  자기 `origin/HEAD`(없으면 자기 `HEAD`)로 해석되어 빈 문자열이 나오지 않는다.
- AC-5: `task_artifacts.repo`에 `"."` 외 값을 넣으면 `TASK_ARTIFACT_REPO_UNSUPPORTED`로,
  `task_artifacts` 미설정 multi-repo는 기존대로 `TASK_ARTIFACT_REPO_MISSING`으로 차단된다.
- AC-6: 루트 저장소가 `repos[]` 경로를 1파일 이상 추적하는 fixture에서
  `TASK_ARTIFACT_REPO_OVERLAP`으로 차단되고 worktree가 하나도 생성되지 않는다.
- AC-7: pre-flight를 통과한 entry 집합과 실제 생성된 worktree 집합이 일치한다. 생성 루프가
  `cfg["repos"]`를 독립 순회하지 않고 ordered `plan_entries` 하나만 소비한다.
- AC-8: `baseBranchOverrides`로 저장소별 base branch가 각각 해석되어 `.meta/task_{NNN}.json`에
  동결 기록된다. `repos[]`·`"."` 어느 쪽과도 일치하지 않는 키는 `CONFIG_UNKNOWN_REPO`로 차단된다.
- AC-9: `remove`가 자식 저장소를 먼저 회수한 뒤 루트를 회수한다. create 중간 실패 fixture에서
  롤백이 자식 → 루트 역순으로 수행되고 잔여물이 0건이다.
- AC-10: 자식 worktree 하나를 제거 불가 상태로 만든 fixture에서 `WORKTREE_REMOVE_FAILED`가
  반환되고 메타와 slot이 보존된다. 이어서 `--force` 없이 재호출하면 이미 회수된 entry는 skip되고
  남은 entry부터 진행된다.
- AC-11: 경로는 없고 Git 등록만 남은 entry, 그리고 경로만 있고 등록이 없는 entry 모두
  `WORKTREE_REMOVE_FAILED`로 차단된다. 도구가 `git worktree prune`을 호출하지 않고 해당 디렉토리도
  삭제하지 않는다.
- AC-12: monorepo 프로젝트(ai-framework)에서 6명령 출력이 변경 전과 바이트 동일하다(C-2). 태스크
  119 `REGRESSION-EVIDENCE.md`와 같은 fixture 방식으로 실측 증거를 남긴다.
- AC-13: 비워크트리 실행이 변경 전과 바이트 동일하다(C-3).
- AC-14: `harness/worktree.md`에 multi-repo 캡슐 소유권 계약이 규범으로 존재하고, 제안서가
  `docs/proposals/archives/`로 이관되며, `archives/opal-worktree-task-ownership.md` 헤더에 §8
  대체 포인터 1행이 추가된다. `docs/proposals/`에 이 제안서의 잔존이 0건이다.
- AC-15: `worktree-tool` 테스트 스위트 전건 통과. 신규 계약 각각에 대응하는 테스트가 존재한다.
- AC-16: R-5를 만족하는 fixture에서 자식 worktree 생성 직후 루트 slot의
  `git status --porcelain`이 비어 있고, `--force` 없는 `remove`가 `GUARD_DIRTY` 없이 자식 → 루트
  역순으로 완주한다.
