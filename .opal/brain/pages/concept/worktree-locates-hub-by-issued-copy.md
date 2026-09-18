---
type: concept
title: 워크트리는 허브를 탐색하지 않고 발급값 사본으로 찾는다
tags:
- worktree
- ownership
- issued-value
- hook
- task-138
sources:
- task:138
related:
- worktree-task-root-allocator-root-split
- worktree-tool
- worktree-slot-existence-to-occupancy-judgment
- worktree-workspace-isolation-axis
- red-corpus-precedes-contract-fabricates-layout
created: '2026-09-18'
updated: '2026-09-18'
status: draft
---
## 개요

워크트리 세션은 자기 위치에서 허브를 **탐색해 알아낼 수 없다**. 하네스 계약이 cwd·태스크 경로 조상·`.opal-worktrees` 문자열을 근거로 한 추론을 [MUST]로 금지하기 때문이다. 해법은 추론이 아니라 **발급**이다 — 워크트리 생성 시 허브가 registry 발급값 사본을 워크트리 안에 내려보내고, 소비자는 그 사본만 읽는다(근거: task:138 PLAN.md D-20).

## 결정 배경 (WHY)

- 실물 워크트리의 파일 cone은 `.opal`·`tasks` 둘뿐이라 `.opal-worktrees/.meta/`가 존재하지 않는다. hook이 `payload["cwd"]`를 project_root로 삼고 그 아래 registry를 읽는 구조였기 때문에, 프로덕션 워크트리 세션에서 registry 0건을 읽어 소유권 claim이 **영구 미발화**했다(근거: task:138 PLAN.md D-20 발견 경위).
- 워크트리 안의 기존 파일 어디에도 허브를 가리키는 포인터가 없었다. 그리고 `opal/core/references/harness/worktree.md` §task root와 allocator root 계약이 "`allocator_root`는 cwd, task path의 조상, `.opal-worktrees` 문자열로 추론하지 않는다"를 [MUST]로 못 박고 있으므로, 탐색으로 메우는 것은 계약 위반이다. 계약 안에서 남는 선택지는 발급뿐이었다.
- 배달 경로는 이미 실재했다 — `.opal`이 워크트리 cone에 포함되어 있어 새 디렉터리를 만들지 않고도 사본을 놓을 자리가 있었다.

## 결정 내용

- `worktree-tool`이 워크트리 생성 성공 경로에서 `<worktree_root>/.opal/task-ownership.json`에 registry 발급 6종(`allocator_root`·`task_home`·`task_folder`·`task_path`·`artifact_repo`·`task_ownership_version`)을 기록한다. 기존 워크트리는 상태 조회 경로에서 **멱등 보강**한다 — 있으면 no-op, 값이 달라졌으면 registry 기준으로 덮어쓴다(근거: task:138 PLAN.md W-21).
- 소비자는 공용 해석 함수 하나(`ownership_core.resolve_roots(cwd)`)만 쓴다. 분기는 셋이다 — ① `<cwd>/.opal-worktrees/.meta/`가 있으면 허브 세션(`allocator_root = cwd`) ② 없으면 발급값 사본에서 `allocator_root`·`task_path`를 취득 ③ 둘 다 없으면 **추측하지 않고** `roots_unresolved` 진단만 남기고 통과한다.
- 어느 분기에서도 cwd 문자열 자르기·부모 디렉터리 순회·`.opal-worktrees` 문자열 탐색을 하지 않으며, 이 금지는 테스트가 집행한다(`opal/tools/ownership-tool/ownership_tool/ownership_core.py` @header).
- 사본은 **읽기 snapshot**이다. 워크트리는 이 사본을 근거로 자기를 허브로 간주하지 않는다 — 허브 여부는 ① 분기의 registry 디렉터리 실재로만 결정된다.
- `task_ownership_version`이 없는 legacy 워크트리는 사본 없이도 기존 경로로 통과한다 — 발급 도입이 기존 워크트리를 차단하지 않는다.

## 영향 범위

`opal/tools/worktree-tool/worktree_tool.py`(사본 기록·멱등 보강)와 `opal/tools/ownership-tool/ownership_tool/ownership_core.py`(`resolve_roots`), 그리고 그것을 소비하는 SessionStart·PostToolUse heartbeat·SessionEnd·PreToolUse·Stop 훅 전건. 앞으로 워크트리 세션이 허브의 값을 알아야 할 때마다 같은 형태를 재사용한다 — 새 키가 필요하면 탐색 로직을 늘리는 것이 아니라 **발급 목록에 키를 추가**한다.

## 관련 페이지

- [[worktree-task-root-allocator-root-split]]
- [[worktree-tool]]
- [[worktree-slot-existence-to-occupancy-judgment]]
- [[worktree-workspace-isolation-axis]]
- [[red-corpus-precedes-contract-fabricates-layout]]
