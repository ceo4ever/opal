---
type: concept
title: 신규 SSOT 신설 시 타 SSOT 수치 복제 금지 — 포인터만
tags:
- ssot
- dedup
- architecture
- opds
sources:
- task:098
related:
- dedup-pointer-over-copy
- demote-promote-recursion-guard-timing-threshold-split
created: '2026-08-21'
updated: '2026-08-21'
status: draft
---
## 개요

새 규칙 SSOT 문서를 신설할 때, 이미 다른 SSOT 문서가 보유한 수치(임계값 등)를 복제해 적지 않고 포인터만 둔다. 수치를 복제하는 순간 두 SSOT가 어긋나는 첫 지점이 생긴다.

## 결정 배경 (WHY)

- (근거: task:098 DONE §3, PLAN §3.4.2 H-12) 트랙 강등 규칙(신설 문서 `track-routing.md`)의 강등 임계값(변경 파일 ≤9)은 기존 승격 임계값(`opal-pilot-dev-short/SKILL.md`의 ≥10)과 상호배타여야 왕복을 막을 수 있다. 이때 승격 임계값 수치 자체를 신설 문서에 복제하면, 승격 임계값이 나중에 바뀔 때 신설 문서가 이를 모르고 stale 상태로 남는다.
- 이미 있는 값을 복제하지 않고 포인터로만 참조하면, 원본이 갱신될 때 참조하는 쪽도 자동으로 최신 값을 따라간다.

## 결정 내용

- 승격 임계값 SSOT는 기존 문서(`opal-pilot-dev-short/SKILL.md` §에스컬레이션 규칙)에만 유지하고, 신설 문서(`track-routing.md`)는 이를 복제하지 않고 포인터 한 줄만 둔다.
- 새 규칙 문서를 쓸 때마다 "이 수치가 다른 SSOT에 이미 있는가"를 먼저 확인하고, 있으면 값을 옮기지 않고 참조만 남긴다.

## 영향 범위

규칙 SSOT를 신설하는 모든 후속 작업. 임계값·수치·목록처럼 갱신 가능성이 있는 값은 특히 이 원칙의 대상이다.

## 관련 페이지

- [[dedup-pointer-over-copy]]
- [[demote-promote-recursion-guard-timing-threshold-split]]
