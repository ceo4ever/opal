---
type: concept
title: 실행 주체 인계는 수신자 id가 아니라 대상 루트를 키로 한다
tags:
- lease
- ownership
- worktree
- handoff
- task-150
- pattern
sources:
- task:150
related: [actor-axis-orthogonal-to-mode, worktree-tool, state-tool, ownership-tool]
created: '2026-09-22'
updated: '2026-09-22'
status: draft
---
## 개요

실행 주체를 바꾸는 파이프라인에서 소유권을 **먼저 잡고 나중에 실행 주체를 띄우면** 그 주체는 구조적으로 소유권을 받을 수 없다. `--wt` 교착이 이 형태였다.

## 배경

`harness/task-process.md`는 `--wt` 태스크에 대해 스텝 5(`state init`) → 스텝 5.5(터미널 기동) 순서를 `[MUST]`로 요구한다. 워크트리 세션이 부팅 직후 `state.json`을 읽어야 하기 때문이다. 그런데 스텝 5 직후 허브 PM이 TASK 행을 mark하면 `state_tool.py`의 `_claim_task_lease_if_needed()`가 `claim_source=state_transition`으로 lease를 만든다. 그 다음 기동된 워크트리 세션의 `session_start` claim은 live foreign lease를 만나 거절된다.

두 요구가 동시에 참이라 순서만으로는 풀 수 없다 — 기동은 `state init` 뒤여야 하고, `state init` 뒤 첫 전이는 lease를 만든다.

## 해법 — 대상 지정 이관

단순 해제(무소유로 만들기)는 실패한다. 허브는 기동 후에도 상태 전이를 계속하고 매 전이가 재-claim하므로 수 초 내 소유를 되찾는다.

성립하는 모델은 **대상을 지정한 이관**이다.

- lease를 `handoff_pending` 상태로 원자 교체한다: 소유자 필드를 비우고 `handoff_to_worktree_root`에 registry 발급값을 적는다.
- claim은 claimant 루트가 그 대상 루트와 realpath 동치이거나 그 하위일 때만 수용한다. 허브 cwd는 허브 루트이므로 자연히 거부되고, 제3자 탈취도 같은 조건으로 막힌다.
- 기동 시점에는 새 세션의 id를 알 수 없다. **루트를 키로 쓰면 id를 몰라도 대상을 특정할 수 있다** — 이것이 이 모델의 핵심이다.
- 이관에는 lease TTL과 분리된 짧은 만료를 둔다. 터미널이 끝내 부팅하지 않는 경로에서 태스크가 영구히 잠기면 결함을 형태만 바꿔 재생산한다.
- 이관 실행 지점은 기동을 소유한 컴포넌트 안이어야 한다. 별도 명령으로 분리하면 "이관 성공 + 기동 실패" 조합에서 아무도 소유하지 않는 태스크가 남고 복귀 주체가 없다.

## 판정 로직을 늘리지 않는 조건

이관 레코드는 소유자 필드가 비어 있으므로 기존 `classify`가 이미 무소유를 반환한다. 그래서 쓰기 가드와 heartbeat에 이관 분기를 **추가하지 않아도** 가드 비차단과 heartbeat no-op이 동시에 성립한다. 새 상태를 도입할 때 기존 판정이 그 상태를 올바르게 접는지 먼저 확인하면 분기 증식을 피할 수 있다.

## 구현 시 순서 함정

`_is_live()`는 상태가 released가 아니고 만료 전이면 참을 반환하므로 이관 레코드도 live로 판정된다. 따라서 claim의 이관 분기는 기존 foreign 검사보다 **앞에** 와야 한다. 뒤에 두면 정작 이관 대상 세션이 foreign으로 거부되어 이관이 무의미해진다.

## 적용 범위

실행 주체 인계가 있는 모든 축에 같은 형태가 나타난다 — 소유권을 먼저 잡는 주체와 실제 실행 주체가 다르고, 인계 시점에 수신자 신원을 모를 때.

## 관련

- 실행 주체 축 자체의 정의는 [[actor-axis-orthogonal-to-mode]]가 소유한다 — 이 페이지는 그 축에서 소유권이 어떻게 넘어가는지만 다룬다.
- 워크트리 생성·회수와 registry 발급값 계약은 [[worktree-tool]]이 소유한다.
- 상태 전이가 lease를 획득하는 지점은 [[state-tool]]에 있다.
- lease 저장·판정·이관 API의 구현은 [[ownership-tool]]이 소유한다.
- 계약이 문서에 없어 이 결함이 리뷰를 통과한 경위는 [[contract-absent-from-harness-docs-passes-review]]에 있다.
