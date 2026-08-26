---
type: concept
title: 예외는 침묵이 아니라 선언이어야 한다 — 미측정 선언과 0의 구별
tags:
- enforcement
- measurement
- state-tool
- contract
- lesson-learned
sources:
- task:103
related:
- enforcement-basis-must-be-structural-not-voluntary
- unresolvable-not-absent-two-vocabulary-split
- degraded-execution-with-explicit-gap
created: '2026-08-26'
updated: '2026-08-26'
status: draft
---
## 개요

측정값을 요구하는 규범에는 반드시 예외가 생긴다. 이때 예외를 **아무것도 적지 않는 것**으로 두면 위반과 예외가 같은 모습이 되어 구별할 수 없다. 예외는 침묵이 아니라 **명시적 선언**이어야 한다 (근거: task:103 DONE.md §3.3).

## 결정 배경 (WHY)

- 워커 소요를 알 수 없는 경우가 실제로 있다 — 워커가 중간에 끊겨 PM이 직접 완주했거나, 애초에 워커를 돌리지 않은 행이다 (근거: task:103 DONE.md §4.4).
- 그런 행을 그냥 비워 두면, 규범을 어겨 안 적은 행과 적을 것이 없어 비운 행이 데이터상 완전히 같아진다.
- 값이 없는 상태를 두 어휘로 갈라야 한다는 문제는 이 프로젝트에서 이미 한 번 다뤄졌다 — 「해결 불가」와 「부재」를 같은 표현으로 뭉뚱그리면 소비자가 판단할 수 없다는 결론이다([[unresolvable-not-absent-two-vocabulary-split]]).

## 결정 내용

- 미측정을 선언하는 전용 경로를 두고, 그 선언을 행에 **영속화**한다 — 선언 플래그가 행에 남아야 나중에도 침묵과 구별된다(`opal/tools/state-tool/state_tool.py:1849`).
- 선언과 `0`은 다른 값이다 — 선언은 「측정하지 않았다」이고, `0`은 「측정했고 1분 미만이었다」다 (근거: `~/.opal/references/opal-harness.md` §3 워커 완료 mark 규범).
- 차단 게이트는 기록과 선언 둘 다 없는 행만 거부한다. 선언한 행은 통과시키되 그 사실이 데이터에 남는다(`opal/tools/state-tool/state_tool.py:1626`).

## 영향 범위

측정값·근거·판정을 요구하는 모든 계약. 필수 필드를 도입할 때는 값과 함께 「값이 없음을 밝히는 방법」을 같이 설계해야 하며, 그러지 않으면 규범이 예외 상황에서 먼저 무너진다.

## 관련 페이지

- [[enforcement-basis-must-be-structural-not-voluntary]]
- [[unresolvable-not-absent-two-vocabulary-split]]
- [[degraded-execution-with-explicit-gap]]
