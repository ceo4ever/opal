---
type: concept
title: 근거 등급 5단계 + AS-IS/TO-BE 관할 2축
tags:
- evidence
- citation
- architecture
- opds
sources:
- task:098
related:
- decision-vs-fact-claim-separation
- verdict-tool-fail-safe-direction-design
- clarification-gate
created: '2026-08-21'
updated: '2026-08-21'
status: draft
---
## 개요

산출물의 근거를 5단계(E1 실행 관측 ~ E5 파생 스냅샷)로 서열화하고, AS-IS(현재 상태) 판단과 TO-BE(개선 방향) 판단을 별도 축으로 관할을 나눈다. 두 축을 나누는 이유는 소스코드가 AS-IS 근거로는 최상위권이지만 TO-BE 근거로는 최하위이기 때문이다.

## 결정 배경 (WHY)

- (근거: task:098 DONE §3) 근거에 등급 서열이 없으면, 소스코드처럼 접근이 쉬운 원천이 TO-BE 판단의 근거로도 남용된다. 코드에 "무엇이 개선되어야 하는가"를 물으면 코드는 자기 자신의 현재 동작만 답할 수 있어 "현행이 정답"이라는 답만 나온다.
- (근거: task:098 DONE §3) 이 상태에서는 개선 태스크 자체가 구조적으로 불가능해진다 — 코드가 스스로의 개선 근거를 부정하는 순환에 갇히기 때문이다.
- (근거: task:098 DONE §2 R-1) 그래서 서열은 단일 축이 아니라 AS-IS/TO-BE 2축으로 분리됐다. AS-IS 서열은 실행 관측이 최상위(E1>E2>E3>E4>E5)이고, TO-BE 서열은 정책·요구사항 문서가 최상위이며 소스코드는 최하위다.

## 결정 내용

- 근거 등급 5단계(E1 실행 관측 ~ E5 파생 스냅샷·brain/code-map 같은 스냅샷 원천)를 신설하고, 등급이 낮은 원천만 있는 주장은 미확정으로 계상한다.
- AS-IS 축과 TO-BE 축의 서열을 분리해 관할을 명시한다 — 같은 소스코드라도 "현재 무엇이 동작하는가"를 답할 때와 "무엇을 바꿔야 하는가"를 답할 때 서열이 다르다.
- E5(brain·code-map 등 파생 스냅샷)는 단독 인용을 금지하고 E1~E4 동반 인용을 강제한다 — brain·code-map은 stale 가능한 스냅샷이라는 전제(OPAL 하네스 규정) 때문이다.

## 영향 범위

TASK.md 작성, ANALYSIS·PLAN의 확정 입력 판정, state-tool의 근거 판정 로직(`--evidence-check`) 전반. 향후 모든 태스크의 "무엇이 문제이고 무엇을 바꿀 것인가" 서술이 이 2축 위에서 근거를 배치해야 한다.

## 관련 페이지

- [[decision-vs-fact-claim-separation]]
- [[verdict-tool-fail-safe-direction-design]]
- [[clarification-gate]]
