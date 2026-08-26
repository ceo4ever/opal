---
type: concept
title: 표기 해상도 부족은 가독성이 아니라 정확성 문제다 — 25시간을 82분으로 읽힌 사례
tags:
- observability
- timestamp
- opal-console
- lesson-learned
sources:
- task:103
related:
- state-md-journal-redefinition
- degeneracy-rule-preserves-past-values-on-axis-split
created: '2026-08-26'
updated: '2026-08-26'
status: draft
---
## 개요

시각 표기의 해상도를 낮추면 짧아 보이는 것이 아니라 **틀리게 읽힌다**. 날짜 없이 시:분만 보여 주면 하루를 넘긴 구간이 같은 날 안의 짧은 구간처럼 보인다 (근거: task:103 DONE.md §3, state.json 행 16 비고).

## 결정 배경 (WHY)

- 파이프라인 행의 시점을 분 해상도로 표기하던 화면에서, 날짜 경계를 넘은 구간이 실제보다 짧게 읽히는 문제가 7개 태스크 8곳에서 확인됐다.
- 가장 큰 사례는 태스크 100의 한 구간으로, 82분처럼 읽히던 값이 실제로는 25시간 22분이었다.
- 이 통계의 목적이 병목 식별인 이상, 가장 오래 걸린 구간을 가장 심하게 잘못 읽는 표기는 목적 자체를 무너뜨린다.

## 결정 내용

- 시각 표기를 날짜와 초를 포함한 형식으로 확장했다 — 기존 표기는 손대지 않고 새 형식을 추가해, 구버전 배포본은 분 해상도로 자연 폴백한다 (근거: task:103 state.json 행 16).
- 스키마의 형식 제약도 초 부분을 선택 항목으로 넓혀 기존 데이터 전건이 그대로 통과하게 했다.
- 라벨 생성을 백엔드 단일 지점으로 옮겨, 화면마다 다른 표기가 생기는 경로를 없앴다.

## 영향 범위

시간을 보여 주는 모든 현황판·보고서. 표기 해상도는 미관이 아니라 데이터 정확성의 일부이며, 특히 「가장 오래 걸린 것」을 찾는 화면에서는 해상도 부족이 결론을 반대로 뒤집는다.

## 관련 페이지

- [[state-md-journal-redefinition]]
- [[degeneracy-rule-preserves-past-values-on-axis-split]]
