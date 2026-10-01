---
type: concept
title: 설계 게이트 scope 병렬 판정과 combine 결합
tags:
- design-gate
- evaluator
- state-tool
sources:
- task:172
related: [design-gate-gaps-resolution-roundtrip, opal-evaluator-agent, op-scenario-gate-skill, state-tool]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

설계 게이트 판정을 설계 4축과 시나리오 3축으로 나눠 병렬로 호출하고, 결과를 결정론 규칙으로 결합하는 방식이다. 이전 지적의 조립도 도구가 맡도록 바꿔 PM의 회차별 추론을 없앴다.

## 결정 배경 (WHY)

(근거: task:172 DONE.md) 검증 시간을 모델 판단과 결정론으로 나누는 것이 태스크의 방향이었다. 이전 지적 조립은 시간과 무관하게 결정론으로 고정할 수 있었다. 판정 병렬화는 시간 단축을 기대한 시도였으나 실측에서 이득이 확인되지 않았다.

## 결정 내용

- 평가자 `design-rubric` 입력에 `scope`(`design`/`scenario`/`all`)를 추가했다.
- `state-tool design-gate start` 응답이 `previous_gaps`·`previous_gaps_by_scope`·`previous_gaps_iteration`을 싣는다 (`opal/tools/state-tool/state_tool.py:6972`).
- `design-gate combine`이 두 부분 결과를 결합해 단일 판정과 같은 형식으로 쓴다 (`opal/tools/state-tool/state_tool.py:7478`). 통과는 설계 4축 전부 통과·점수 각 1 이상·평균 1.5 이상일 때만이며, 수정 대상은 plan·scenario·both로 정한다. 상태·락·run-log를 건드리지 않는다.
- `design-gate record`는 바뀌지 않았다. 검사 순서와 기존 오류 코드가 유지된다.
- `op-scenario-gate` §6.1은 병렬 두 호출 + `combine` 절차다 (`opal/skills/op-scenario-gate/SKILL.md:187`).

## 미확인·한계

- 시간 이득 미확인: 단일 호출 평균 96.1초, 병렬 쌍 벽시계 평균 91.8초. 설계 판정 호출 하나가 단일 호출 전체와 비슷하게 걸린다. 병렬은 기본값으로 유지된다.
- S-13 실패: 설치된 evaluator를 병렬 한 쌍으로 호출해 `pass-161`을 판정시켰더니 결합 결과가 `fail`이었다. 진단 표본은 모두 같은 `decision_clarity` 축 실패라 분리가 판정을 바꾼다는 근거는 없으나 이전 측정의 `pass`와 어긋난 원인은 분리하지 못했다. 후속 과제다.
- 후속 후보: 설계 판정이 느린 원인 분석, 설계 축을 더 나누는 안, 기본값을 `scope: all`로 되돌리는 안.

## 영향 범위

evaluator 정의, `state-tool` design-gate, `op-scenario-gate` §6.1, 설계 게이트 하네스 문서.

## 관련 페이지

- [[design-gate-gaps-resolution-roundtrip]]
- [[opal-evaluator-agent]]
- [[op-scenario-gate-skill]]
- [[state-tool]]
