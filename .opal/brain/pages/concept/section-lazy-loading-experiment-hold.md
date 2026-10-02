---
type: concept
title: 절 단위 로딩 실험 — 규범 문서는 기본값 전환 보류
tags:
- event-loader
- token-economy
- measurement
sources:
- task:177
related: [event-response-single-body, worker-dispatch-target-section-selection, lazy-loading-scope-framework-docs-only, lazy-receipt-full-field-recompute]
created: '2026-10-02'
updated: '2026-10-02'
status: draft
---
## 개요

이벤트 문서를 절 단위로 나눠 필요한 절만 싣는 지연 로딩을, 명시적으로 켠 호출에서만 동작하는 실험 모드로 구현해 측정했다. 결과는 기본값 전환 보류다. 규범 문서는 `[MUST` 줄을 모두 보존해야 하므로 뺄 수 있는 절이 거의 없어 이득이 작고, 응답 바이트는 오히려 늘었다.

## 결정 배경 (WHY)

앞선 단일 본문 구조 개선([[event-response-single-body]]) 뒤에 남은 부담은 문서 본문 자체의 크기였고, 절별 지연 로딩이 다음 후보였다 (근거: task:177 PLAN§D-18). 기본값 후보 기준을 실행 전에 고정했다: `[MUST` 보존 100%, 켬 정답률이 끔보다 낮은 프로브 0개, 대상 이벤트 본문 합계 감소율 25% 이상을 모두 만족해야 한다. 기준을 결과 전에 고정해 사후 합리화를 막았다 (근거: task:177 PLAN§D-18).

## 결정 내용

- 측정 결과: 설계 단계 이벤트 본문 53,305 → 48,059바이트(9.84% 감소), 나머지 세 이벤트 0%, 네 이벤트 합계 2.34% 감소. 응답 바이트는 모든 이벤트에서 2.7~12.4% 증가했다(목차·receipt 비용). `[MUST` 보존은 316/316줄이다.
- 프로브 40회 호출: 엄격 채점에서 켬 19/20 대 끔 20/20, 의미 기준 20/20 대 20/20이다. 차이 1건은 채점 정규식 미스였다.
- 기준을 하나도 못 채우는 항목이 있어 판정은 보류다. 표본이 작아 통계적 동등성은 주장하지 않는다.
- 감소가 작은 구조적 이유: 대상 4종이 대부분 규범이라 `[MUST` 보존을 지키면 뺄 수 있는 절이 설계 게이트 문서의 4개 절(5,628바이트)뿐이었다.
- 감소율을 올리려면 검토 게이트 문서의 검토 절차(문서의 71%, `[MUST`를 포함한 단일 단위)와 인용 규칙의 큰 절처럼 큰 단위를 먼저 잘게 쪼개야 한다. 기본값 후보로 올리려면 전체 파이프라인 반복 실행(비용·승인 필요)이 전제다.

## 영향 범위

켜지 않은 호출의 응답·receipt·검증 결과는 시작 시점 로더와 동일하다(작업 디스패치만 의도한 문서 수정으로 186바이트 차이). 켠 호출 전용 선언은 `opal/core/references/sections/*.json`과 `opal/core/references/events.json`의 절 분할 선언이 소유한다. 측정 하니스와 증거는 태스크 폴더 `MEASURE.md`·`measure/`에 있다.

## 관련 페이지

- [[event-response-single-body]]
- [[worker-dispatch-target-section-selection]]
- [[lazy-loading-scope-framework-docs-only]]
- [[lazy-receipt-full-field-recompute]]
