---
type: concept
title: RED 코퍼스를 구현 계약보다 먼저 쓰면 실재하지 않는 레이아웃을 전제한다
tags:
- red-first
- fixture
- test-design
- lesson
- task-138
sources:
- task:138
related:
- fixture-vs-real-blind-spot-lesson
- fixture-conflicting-requirements-lesson
- fixture-ownership-separation-closes-reward-hacking
- red-timing-follows-implementation-subject
- worktree-tasks-fixture-structural-limit
created: '2026-09-18'
updated: '2026-09-18'
status: draft
---
## 개요

RED 코퍼스(테스트 fixture + 단언)를 구현 계약이 확정되기 전에 쓰면, 코퍼스는 **실재하지 않는 레이아웃·아키텍처를 전제**하게 되고 그 fixture가 구현 결함을 가린다. 태스크 138에서 이 실패모드가 **4회** 재발했고, 교정 방향은 매번 동일했다 — **fixture를 실물에 맞추고, 구현을 계약에 맞춘다**. 반대 방향(실물을 fixture에 맞추거나, 계약을 구현에 맞추는 것)은 한 번도 채택되지 않았다.

## 결정 배경 (WHY)

- **1회차 — shadow 술어가 fixture 레이아웃에 맞춰 작성됨**. `resolver.resolve_hub`의 shadow 조건이 "canonical task_path가 허브 밖"(`not _is_inside(canonical, hub_root)`)이었는데, 실물 canonical은 `<hub_root>/.opal-worktrees/task_NNN/tasks/…`로 **허브 안**이라 조건이 항상 거짓이었다. fixture만 워크트리 루트를 허브의 형제로 두어 이 구멍을 가렸고, 허브 실물 읽기전용 실측에서 태스크 목표(오탐 종결) 자체가 미달성임이 드러났다(근거: task:138 AGENTIC-LOG 엔트리 42). 교정은 fixture 실물 동형화를 **먼저** 하고(엔트리 46) 술어 정정을 뒤에 두는 순서였다(엔트리 44·45).
- **2회차 — 워크트리에 없는 registry를 전제**. 실물 워크트리의 파일 cone은 `.opal`·`tasks` 둘뿐이라 `.opal-worktrees/.meta/`가 존재하지 않는데, hook과 fixture가 그 디렉터리를 전제해 프로덕션에서 registry 0건을 읽고 claim이 영구 미발화했다(근거: task:138 PLAN.md D-20). 같은 계열의 setup 결함이 스위트 단위로 3회 반복되자, 원인을 개별 사고가 아니라 "RED 코퍼스가 테스트별 시나리오 조립 없이 작성된 구조적 결함"으로 판정하고 남은 표면을 일괄 종결했다(엔트리 51·52).
- **3회차 — fixture가 계약 가드를 우회하는 경로를 요구**. 어떤 테스트가 **미등록 허브 루트**에 소유권 상태 전이를 걸고 성공을 요구했는데, 그것을 만족시키려면 receipt 가드를 건너뛰는 미등록 upsert 경로를 구현해야 했다 — 즉 fixture를 통과시키는 순간 지키려던 불변식이 뚫린다(엔트리 79). 판정은 fixture 교정이었고, 상태 전이는 **등록된 canonical task path에만** 동작하도록 좁혔다(엔트리 80).
- **4회차 — RED가 계약보다 먼저 쓰여 상상된 아키텍처를 담음**. launcher RED가 평면 `owner.json`(`data["status"]`)을 전제했으나 실제 SSOT는 registry meta의 중첩 `execution_ownership.state`였다. 그대로 GREEN을 만들면 launcher가 소유권 도구를 호출하지 않는 **사설 ownership writer**를 갖게 되어 dual-writer 방지가 무너진다. 원인은 이 RED가 해당 계약이 존재하기 전에 작성된 것이다(엔트리 88).

## 결정 내용

- RED 코퍼스는 **대상 계약(SSOT 경로·스키마·가드)이 확정된 뒤** 작성한다. 계약이 아직 없으면 fixture는 구현자의 상상을 고정하는 장치가 되고, 그 상상은 Gate를 통과한 뒤에야 실물에서 깨진다.
- fixture 레이아웃은 **실물과 동형**이어야 한다. 실물 디렉터리 배치를 모르면 먼저 읽고 쓴다 — fixture가 편의상 단순화한 배치는 술어의 오류를 가리는 가장 흔한 경로다.
- 충돌이 드러나면 교정 방향은 고정이다 — **fixture는 실물 쪽으로, 구현은 계약 쪽으로** 움직인다. 테스트를 통과시키려고 계약을 넓히는 제안(미등록 경로 허용, 타입 추론 규칙 신설 등)은 기각한다.
- 교정 순서도 고정이다 — fixture를 먼저 실물에 맞춰 **결함이 RED로 노출되게** 한 뒤 구현을 고친다. 한 워커에 둘을 묶으면 fixture를 술어에 맞춰 조정하는 역방향 오염이 가능해지므로 생성자와 구현자를 분리한다(엔트리 45·52).
- 술어를 **소유한** 모듈의 자기 스위트에 그 술어의 positive/negative 단언이 있는지 확인한다. 138에서는 shadow 분류 단언이 상위 조립기 스위트에만 있고 술어 소유 스위트에는 0건이라, Gate가 결함 술어를 통과시켰다(엔트리 47).

## 영향 범위

RED-first를 채택한 모든 태스크의 코퍼스 작성 시점과 Work item 순서에 적용된다. 특히 신설 도구·신설 저장소처럼 "계약 자체가 이 태스크에서 만들어지는" 작업에서, 코퍼스를 계약 확정 이전 단계에 배치하면 4회차와 동일한 형태로 재발한다.

## 관련 페이지

- [[fixture-vs-real-blind-spot-lesson]]
- [[fixture-conflicting-requirements-lesson]]
- [[fixture-ownership-separation-closes-reward-hacking]]
- [[red-timing-follows-implementation-subject]]
- [[worktree-tasks-fixture-structural-limit]]
