---
type: concept
title: 모델·effort 측정 결과와 현행 유지 결정
tags:
- model
- effort
- measurement
- decision
sources:
- task:176
related: [opst-variant-design-impl-settings, agent-effort-policy-inherit-by-default, crud-scenario-fails-checkpoint-commits-at-baseline]
created: '2026-10-02'
updated: '2026-10-02'
status: draft
---
## 개요

설계·구현 모델과 effort를 바꾸는 후보 세 개를 현행과 측정했으나 어느 것도 두 시나리오에서 일관된 속도·비용 이득을 보이지 않아, 현행(설계·구현 모두 sonnet 5.5, effort 미선언)을 유지하기로 결정했다.

## 결정 배경 (WHY)

- (근거: task:176 DONE.md 측정 결과) 세션 16개(현행 + 후보 3 x 시나리오 2 x 반복 2), 비용 $198.5, 약 2.8시간. 후보는 C1(설계 opus/high, 구현 sonnet/low), C2(설계 opus/high, 구현 sonnet/medium), C3(설계 opus/medium, 구현 haiku/medium).
- 숨은 테스트 통과율은 전 후보 100%여서 품질 하한은 모두 충족했지만, 시간·비용에서 이득이 없었다. stockctl 평균 시간(분): 현행 22.6, C1 20.1, C2 22.7, C3 32.4. todo-crud: 현행 24.5, C1 30.3, C2 34.6, C3 33.4. 비용($)은 stockctl 10.7/11.2/11.9/12.0, todo-crud 11.5/14.5/14.7/13.0.
- C1의 stockctl 약 11% 단축은 현행의 편차(18.4~26.7) 안이다. C3(haiku)는 두 시나리오 모두 느렸다. TEST 수정 반복은 전 실행 0, 설계 게이트 반복은 전 실행 1이다.
- 반복 2회는 표본이 작아 우연과 실제 차이를 구분하기 어렵다. 이전 측정에서 `xhigh`가 약 6배 느렸으므로 후보를 `high` 이하로 한정했다 (근거: task:176 PLAN 결정 "후보 설정").

## 결정 내용

- 소유자가 현행 유지를 결정했다. 에이전트 정의와 설정 시드는 바뀌지 않았다.
- 결과 기록은 태스크 폴더 `skill-tests/` 아래 두 폴더(`record.json`, `REPORT.md`, `report.html`)에 있다.

## 관련 페이지

- [[opst-variant-design-impl-settings]]
- [[agent-effort-policy-inherit-by-default]]
- [[crud-scenario-fails-checkpoint-commits-at-baseline]]
