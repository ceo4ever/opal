---
type: concept
title: 교체형 목표의 검증 범위 함정 — 주장의 범위와 검증의 범위를 맞춰야 한다
tags:
- lesson
- verification
- gate-design
- scenario-gate
- task-090
sources:
- task:090
related:
- scenario-goal-coverage-gate-loop
- 070-derivation-engine-perspective-bias-lesson
- pipeline-json-full-adoption-migration
created: '2026-08-13'
updated: '2026-08-13'
status: draft
---
## 개요

목표를 "무언가를 다른 것으로 완전히 바꿔서, 옛 방식을 쓰는 곳이 하나도 남지 않게 한다"처럼 전부-교체형으로 세울 때, 그 주장이 미치는 범위와 실제로 검증한 범위가 다르면 "검증했다"는 말이 "주장했다"는 말을 실제로 뒷받침하지 못하는 격차가 생긴다.

## 결정 배경 (WHY)

- (근거: task:090 DONE.md §3, D-10) 이번 태스크의 목표 중 하나는 "예전 방식(SKILL.md 표 파싱)을 부르는 곳이 레포 전체에 0건"이라는, 범위가 레포 전체인 주장이었다. 그런데 1차 검증은 새로 전환한 10개 pilot 안에서만 예전 방식을 부르는 곳이 없는지를 확인했다 — 주장은 "전체"인데 검증은 "새로 만든 부분"으로 좁았다.
- (근거: task:090 DONE.md D-10) 이 틈은 목표 달성 여부를 점검하는 루브릭의 "채택/잔존" 판단축이 1차 점검에서 잡아냈다. 검증 범위를 pilot 내부에서 레포 전역으로 넓히면서 격차가 해소됐다.

## 결정 내용

- 목표 문장이 "전부/전체/하나도 남지 않게" 같은 전수(exhaustive) 표현을 담고 있으면, 검증 계획을 세울 때 "그 전수 범위와 실제로 확인하는 범위가 같은가"를 별도로 확인한다. 새로 만든 대상 안에서만 확인하는 것은 "새로 만든 것이 잘 됐다"는 것만 보여줄 뿐, "예전 것이 전부 사라졌다"는 것은 보여주지 못한다.
- 이런 틈은 결과물을 만든 쪽이 스스로 알아차리기 어렵다 — 자기가 만든 부분만 눈에 들어오기 때문이다. 그래서 검증 범위가 목표 범위를 실제로 덮는지는 별도의 축(독립적인 커버리지 점검)으로 확인하는 편이 안전하다.

## 관련 페이지

- [[scenario-goal-coverage-gate-loop]]
- [[070-derivation-engine-perspective-bias-lesson]]
- [[pipeline-json-full-adoption-migration]]
