---
type: concept
title: 음수 차단은 사후 0-clamp가 아니라 상한 clamp로 — 합 항등 보존과 오기록 적발
tags:
- aggregation
- statistics
- invariant
- opal-console
- design-decision
sources:
- task:103
related:
- degeneracy-rule-preserves-past-values-on-axis-split
- measurement-tool-more-fallible-than-artifact-lesson
created: '2026-08-26'
updated: '2026-08-26'
status: draft
---
## 개요

여러 계열의 합이 전체와 일치해야 하는 집계에서 음수를 막을 때, 계산 후에 음수를 0으로 눌러 담으면 합 항등이 깨진다. 음수가 나올 수 있는 항목에 **상한을 걸어** 먼저 몫을 확보하고 나머지를 유도값으로 두면 항등이 항상 성립한다 (근거: task:103 TASK.md 집계 기준 16-d).

## 결정 배경 (WHY)

- 세 계열 중 PM 몫은 직접 측정하지 않고 「행 소요에서 캡틴과 워커를 뺀 나머지」로 유도한다.
- 워커 기록값이 행 소요보다 크면 이 유도값이 음수가 되고, 화면에 음수 막대가 그려진다.
- 사후에 음수를 0으로 눌러 담으면 세 계열의 합이 행 소요보다 커져, 「총 = PM + 워커 + 캡틴」이라는 화면의 약속이 깨진다.

## 결정 내용

- 워커 몫을 `기록값`과 `소요 − 캡틴` 중 작은 값으로 취하는 **상한 clamp**를 적용한다 — 나머지가 PM이 되므로 합이 항상 행 소요와 일치한다 (근거: task:103 TASK.md 집계 기준 16-d).
- clamp가 실제로 걸린 행은 플래그로 표면화한다 — 조용히 값을 고치면 원천 데이터의 오류가 화면 뒤에 숨는다.
- 야간 제외 보정을 얹을 때도 순서를 유지한다 — 워커 몫을 먼저 확보하고 남은 몫에서만 제외분을 뺀다. 워커 실행 시간은 실측 벽시계라 제외 구간을 적용하면 실제보다 짧아지기 때문이다 (근거: task:103 TASK.md 집계 기준 17-d).
- 이 clamp는 도입 직후 **자기 오기록을 잡아냈다** — 행 소요 20분인 행에 워커 45분이 기록되자 clamp가 걸리고 시나리오가 실패로 표면화했으며, 실제로는 워커가 끊겨 PM이 직접 완주한 행이었다 (근거: task:103 DONE.md §4.4).

## 영향 범위

합 항등을 약속하는 모든 분해 지표. 유도값을 쓰는 설계에서는 「어디에 상한을 걸 것인가」가 곧 항등 보존 설계이며, 사후 보정은 마지막 수단이 아니라 잘못된 수단이다.

## 관련 페이지

- [[degeneracy-rule-preserves-past-values-on-axis-split]]
- [[measurement-tool-more-fallible-than-artifact-lesson]]
