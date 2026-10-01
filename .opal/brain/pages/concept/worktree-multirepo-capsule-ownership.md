---
type: concept
title: 워크트리 multi-repo 캡슐 소유권
tags:
- worktree
- multi-repo
- proposal
sources:
- doc:docs/proposals/archives/opal-worktree-multirepo-ownership.md
related: [worktree-task-root-allocator-root-split, worktree-tool, worktree-workspace-isolation-axis]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

여러 저장소로 이뤄진 프로젝트에서 태스크 산출물을 어느 저장소가 소유할지, 저장소별 기준 브랜치와 중첩 작업본의 생성·회수 순서를 정한 적용완료 제안서다(태스크 124). 규범 원문은 워크트리 하네스 문서의 multi-repo 캡슐 소유권 절이 소유한다(`docs/proposals/archives/opal-worktree-multirepo-ownership.md:3-8`).

## 핵심 결정

- 태스크 산출물을 추적하는 주체가 하위 저장소 목록 밖의 프로젝트 루트 저장소인 구조가 실제로 존재한다. 그래서 산출물 소유 저장소 지목에 "프로젝트 루트"를 뜻하는 예약값을 두고, 1차에는 이 값만 허용한다. 루트가 Git 저장소이며 태스크·PM 프로필·메모리를 추적할 때로 한정한다(`docs/proposals/archives/opal-worktree-multirepo-ownership.md:19-30`).
- 저장소별 기준 브랜치는 선택적 재정의 맵으로 지정한다(`docs/proposals/archives/opal-worktree-multirepo-ownership.md:31`).
- 중첩 작업본은 생성 순서대로 만들고 회수·롤백은 역순으로 하며, 전부 성공한 뒤에만 메타를 지운다. 일부만 회수된 뒤의 재시도는 경로 실재와 Git 등록 두 축으로 멱등 판정해 강제 옵션 없이 가능하다(`docs/proposals/archives/opal-worktree-multirepo-ownership.md:32-33`).
- 모든 국면이 하나의 순서 있는 계획 목록을 소비해 검사 대상과 생성 대상이 갈라지지 않게 하고, 단일 저장소 프로젝트에는 영향이 없다(`docs/proposals/archives/opal-worktree-multirepo-ownership.md:35-39`).

## 관련 페이지

- [[worktree-task-root-allocator-root-split]] — 선행 태스크 소유권 계약
- [[worktree-tool]]
- [[worktree-workspace-isolation-axis]]
