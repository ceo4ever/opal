---
type: concept
title: 순서 역전은 표기 문제가 아니다 — 파생 계산의 귀속까지 오염한다
tags:
- state-tool
- incident
- aggregation
- lesson-learned
sources:
- task:103
related:
- upper-bound-clamp-preserves-sum-identity
- force-flag-side-effect-trial-run-first
created: '2026-08-26'
updated: '2026-08-26'
status: draft
---
## 개요

행 순서가 뒤집힌 것을 「표기상의 문제」로 판단하면 틀린다. 행 사이의 시간 간격으로 소요를 계산하는 구조에서는 순서 역전이 **파생 계산의 귀속까지 오염**한다 (근거: task:103 DONE.md §4.3).

## 결정 배경 (WHY)

- 추가 행을 삽입하는 명령을 같은 앵커로 두 번 호출했더니, 새로 들어간 두 행의 순서가 뒤집혀 나중 작업이 앞에 놓였다.
- 처음에는 「표기 순서만 역전이고 실제 수행 순서는 맞다」고 판단하고 넘어갔다.
- 그 판단이 틀렸다 — 소요는 앞 행의 시점과 자기 시점의 차이로 계산되므로, 순서가 뒤집히면 구간 201분이 통째로 앞 행에 흡수된다.
- 그 결과 워커 39분이 소요 0인 행에 얹혀 전액 상한 clamp에 걸렸다 (근거: task:103 DONE.md §4.3).

## 결정 내용

- 순서 역전을 발견하면 표기 문제로 분류하지 않고, 그 순서를 입력으로 쓰는 파생 계산을 함께 점검한다.
- 복구는 사용자 승인을 받아 행 내용을 논리 순서로 재배치하고 워커 소요를 실측값(37분)으로 정정하는 방식으로 진행했다.
- 같은 앵커로 반복 호출할 때 역순으로 삽입되는 도구 거동 자체는 결함으로 별도 이월했다 (근거: task:103 DONE.md §6 이월 2).

## 영향 범위

행 순서가 값의 일부인 모든 상태 파일. 순서·시점·소요가 서로를 유도하는 구조에서는 「보기에만 이상한 것」이 없으며, 표시 계층의 이상은 계산 계층의 이상과 같은 무게로 다뤄야 한다.

## 관련 페이지

- [[upper-bound-clamp-preserves-sum-identity]]
- [[force-flag-side-effect-trial-run-first]]
