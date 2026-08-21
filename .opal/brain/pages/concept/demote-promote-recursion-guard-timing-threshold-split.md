---
type: concept
title: 강등·승격 재귀 차단 — 판정 시점 분리 + 임계 상호배타
tags:
- track-routing
- recursion
- architecture
- opds
sources:
- task:098
related:
- verdict-tool-fail-safe-direction-design
- evidence-tier-asis-tobe-jurisdiction
created: '2026-08-21'
updated: '2026-08-21'
status: draft
---
## 개요

트랙 강등(opd→opds)과 승격(opds→opd) 규칙이 같은 축을 양방향으로 판정하면 왕복(강등했다가 다시 승격하는) 구조가 생길 수 있다. 이를 판정 시점 분리와 임계값 상호배타 조합으로 막는다.

## 결정 배경 (WHY)

- (근거: task:098 DONE §3, PLAN §3.4.2 H-4) 강등 판정과 승격 판정이 같은 시점에 같은 축을 검사하면, 강등 조건과 승격 조건이 동시에 성립할 여지가 생겨 트랙이 왕복할 위험이 있다.
- (근거: task:098 PLAN §3.4.2) 승격 규칙은 이미 두 시점(요구사항 개수 기준 조기 판정, PLAN 결과의 파일 수 기준 판정)으로 존재했다(`opal-pilot-dev-short/SKILL.md`). 강등 규칙을 신설하면서 이 기존 승격 시점과 겹치지 않는 별도 시점을 골라야 왕복을 막을 수 있었다.

## 결정 내용

- 강등 판정 시점은 **TASK 완료 직후 1회**로 고정하고, 승격 판정 시점은 **PLAN 결과**로 고정한다 — 시점 자체가 겹치지 않는다.
- 강등 임계값(변경 파일 수 ≤9)과 승격 임계값(≥10)을 상호배타로 설정한다 — 두 조건이 동시에 참이 될 수 없는 값 범위를 골랐다.
- 두 조건 중 하나만 판정 도구에서 시점 분리와 상호배타 임계값을 함께 확인해야 재귀(강등↔승격 반복)가 원천적으로 성립하지 않는다 — 시점 분리만으로는 부족하고, 임계 상호배타만으로도 부족하다. 둘을 함께 적용해야 한다.

## 영향 범위

`track-routing.md`(신설 SSOT)와 `opal-pilot-dev-short/SKILL.md`(승격 규칙 SSOT). 같은 종류의 양방향 라우팅 규칙(A↔B 전환)을 설계할 때 일반화 가능한 패턴이다 — 판정 시점이 겹치는 양방향 라우터는 왕복한다.

## 관련 페이지

- [[verdict-tool-fail-safe-direction-design]]
- [[evidence-tier-asis-tobe-jurisdiction]]
