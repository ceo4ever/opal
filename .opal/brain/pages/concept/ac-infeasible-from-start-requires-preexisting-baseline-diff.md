---
type: concept
title: AC가 착수 시점부터 실현 불가일 수 있다
tags:
- verification
- ac
- task-114
sources:
- task:114
related:
- verification-dual-track-catches-author-blind-spots
created: '2026-09-09'
updated: '2026-09-09'
status: draft
---
## 개요

완료기준(AC)이 「검사 결과 error 0건」처럼 절대 기준으로 서술되어 있으면, 착수 시점에 리포지토리가 이미 무관한 선존 결함을 안고 있는 경우 그 절대 기준은 무엇을 해도 달성 불가능하다. 이런 경우 `git stash` 등으로 선존 여부를 판정하고, 완료기준을 「이번 변경이 유발한 오류 0건」으로 재해석해야 한다.

## 결정 배경 (WHY)

(근거: task:114 DONE.md §4-3) 태스크 114의 완료기준 중 하나는 `validate` 실행 시 error 0건이었다. 그러나 착수 시점에 이미 `op-scenario-gate: unregistered` 결함이 리포지토리에 존재했고, 이는 태스크 114 착수 이전부터 있던 것이라 태스크 114의 구현이 무엇을 해도 절대 기준(0건)을 달성할 수 없는 상태였다.

## 결정 내용

- `git stash`로 이번 변경분을 임시로 제거한 뒤 동일 검사를 실행해, 결함이 선존하는지(스태시 상태에서도 나타나는지) 확인한다.
- 선존이 확인되면, 완료기준을 원문 그대로("error 0건")가 아니라 **"이번 변경이 유발한 오류 0건"**으로 재해석해 판정한다.
- 이번 사례에서는 실행 도중 별도 배포로 `dangling` 결함이 해소되어 전체 오류는 0건이 됐고, 잔여 1건(`unregistered`)은 선존·무관으로 판정해 완료기준을 충족한 것으로 처리했다.

## 영향 범위

- 절대 수치 기준의 완료기준(AC)을 다루는 모든 태스크에서, 착수 시점 실현 가능성을 먼저 점검해야 한다는 일반 원칙이다. ANALYSIS 단계에서 "신규 이슈 아님"으로 판정한 사안이라도, 그 판정이 착수 시점 실현 가능성 자체를 놓쳤을 수 있다는 점을 함께 유의해야 한다(task:114 DONE.md §3 — 테스트 워커가 이 누락을 PLAN 설계 결함으로 적발했다).

## 관련 페이지

- [[verification-dual-track-catches-author-blind-spots]]
