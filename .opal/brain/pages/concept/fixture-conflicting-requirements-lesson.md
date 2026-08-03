---
type: concept
title: 픽스처 요구 충돌 — RED 작성 시점 시나리오 간 요구 대조 필요
tags:
- lesson
- testing
- fixture
- red-first
- task-082
sources:
- task:082
related:
- fixture-vs-real-blind-spot-lesson
- red-test-determinism-abort-trap
created: '2026-08-03'
updated: '2026-08-03'
status: draft
---
## 개요

여러 검증 시나리오가 공유하는 픽스처 하나에 서로 양립할 수 없는 요구를 동시에 배정하면, 그 충돌은 시나리오를 작성하는 시점에는 드러나지 않고 구현을 통과시키려는 시점에야 드러난다.

## 결정 배경 (WHY)

이번 태스크에서 시나리오 두 쌍(S-2↔S-7, S-6a↔S-6b)이 같은 픽스처에 상호 배타적인 요구를 배정한 상태로 작성돼 있었고, 이 충돌은 구현을 통과시키는 단계에 들어가서야 발견됐다(근거: task:082 DONE.md §6 결함 #5 "GREEN 전환 중"). 조치는 픽스처를 분리하는 것으로 해소했다(근거: task:082 DONE.md §6 결함 #5).

## 결정 내용

시나리오를 먼저 작성하고 구현이 아직 없는 순서로 검증을 진행하는 방식에서는, 시나리오별로 어떤 픽스처에 어떤 요구를 배정했는지를 시나리오 작성 시점에 서로 대조해야 한다 — 구현이 시작되기 전에 요구 충돌을 잡을 수 있는 유일한 시점이 그때이기 때문이다. 이 대조를 건너뛰면 충돌이 구현 검증 단계까지 이연되어 뒤늦게 재작업을 유발한다.

## 영향 범위

여러 시나리오가 픽스처를 공유하는 모든 검증 설계 작업에 재사용 가능한 점검 절차다.

## 관련 페이지

- [[fixture-vs-real-blind-spot-lesson]]
- [[red-test-determinism-abort-trap]]
