---
template: sdlc-v2
---
# TASK: opal-harness.md 구형 절 참조 정리

## Problem

`opal/core/references/opal-harness.md`의 구형 절 참조 호환 매핑 표에 `§2.5 워크스페이스 축` 행이 남아 있다. 이 행은 legacy 인용을 owner 문서로 돌려주는 역할인데, 아직 두 문서가 그 번호를 직접 인용한다 — `opal/core/references/tools.md:1028`과 `opal/skills/opal-project-init/SKILL.md:84`가 "하네스 규약의 SSOT는 `opal-harness.md` §2.5"라고 적고 있다.

`opal-harness.md`에는 번호 절이 하나도 남아 있지 않다(태스크 118 실측). 즉 두 인용은 실존하지 않는 절을 가리키고 매핑 표를 한 번 거쳐야 해석된다. 태스크 118이 이 행을 제거하려다, 인용이 살아 있어 지우면 dangling이 생긴다는 이유로 보류했다.

## Proposed outcome

두 인용처가 owner 문서를 직접 가리킨다. 워크스페이스 축과 루트 해석은 `harness/worktree.md`가, 생성·복구 절차는 `harness/task-process.md`가 소유하므로 각 인용이 실제로 필요한 쪽을 지목한다.

그 위에서 `opal-harness.md`의 `§2.5` 매핑 행을 제거해도 dangling 인용이 생기지 않는다.

## Affected users and systems

- 규범 문서: `opal/core/references/opal-harness.md`, `opal/core/references/tools.md`, `opal/skills/opal-project-init/SKILL.md`.
- 이 문서들을 읽는 PM·워커의 탐색 경로.
- 범위 제외: `harness/worktree.md`·`harness/task-process.md` 본문(이미 owner로 정리됨), 다른 구형 절 번호의 매핑 행.

## Constraints

- C-1: 매핑 표의 다른 행을 건드리지 않는다.
- C-2: `~/.opal/` 배포 파일을 직접 수정하지 않는다. 프로젝트 소스만 수정한다.
- C-3: 규범 원문을 인용처로 복제하지 않는다 — 포인터만 교체한다.
- C-4: git 관리 Markdown에 수기 누적 이력 절을 만들지 않는다.

## Acceptance criteria

- AC-1: `tools.md:1028`과 `opal-project-init/SKILL.md:84`가 `opal-harness.md §2.5` 대신 owner 문서(`harness/worktree.md` 또는 `harness/task-process.md`)의 실존 절을 가리킨다.
- AC-2: 저장소 활성 문서에서 `opal-harness.md §2.5` 인용이 0건이다(역사 `tasks/` 기록과 `docs/proposals/` 제외).
- AC-3: `opal-harness.md`의 `§2.5 워크스페이스 축` 매핑 행이 제거되고 다른 행은 변경되지 않는다.
- AC-4: 교체된 포인터가 실존 절을 가리킨다(dangling 0건).
- AC-5: `worktree-tool` 스위트가 변경 전과 동일하게 통과한다 — `test_s24`의 구형 절 참조 호환 매핑 단언이 깨지지 않는다.
