---
type: concept
title: 판정 도구 오작동 방향 고정 — unknown 미확정 계상 + 강등 4축 AND
tags:
- evidence
- tooling
- fail-safe
- opds
sources:
- task:098
related:
- decision-vs-fact-claim-separation
- demote-promote-recursion-guard-timing-threshold-split
created: '2026-08-21'
updated: '2026-08-21'
status: draft
speculative_override: true
override_note: 도메인 용어 '미확정'(등급 판정 결과값 이름)이 미실체 마커로 오탐됨 — 본 페이지는 이미 완료·구현된 task:098
  확정 설계 내용이며 향후 계획이 아님
---
## 개요

판정 도구가 오작동할 때 항상 한쪽 방향으로만 안전하게 벗어나도록 설계한다. 근거 등급 판정에서는 `unknown` 등급을 미확정으로 계상하되 절대 파이프라인을 차단하지 않고(exit 0 유지), 트랙 강등 판정에서는 4개 축을 모두 만족해야만(AND) 강등이 일어나도록 해서 실패가 항상 "강등 불발" 쪽으로 떨어지게 만든다.

## 결정 배경 (WHY)

- (근거: task:098 DONE §3, PLAN §3.3.2) `unknown`은 "도구가 검증하지 못했다"는 뜻이므로 확정으로 계수할 수 없다 — 증거 없는 완료를 인정하지 않는다는 원칙과 직결된다. 그렇다고 즉시 차단하면 판정 실패가 파이프라인을 멈추는 부작용이 생긴다.
- (근거: task:098 DONE §3, PLAN §3.4.2) 트랙 강등 판정에서 확정률·변경 파일 수 어느 한 축도 단독으로는 opd/opds 트랙을 가르지 못했다(실측: opds 4건 중 2건이 100%, 2건이 71%·61%; opd도 100%가 다수). 그래서 4축 AND(확정률·파일수·신규개념·검증계층)만 강등 조건으로 채택했다.
- 판정 로직이 결국 실패하는 순간이 오더라도, 그 실패가 "잘못 강등시킨다"보다 "강등을 시키지 않는다"는 쪽으로 향하게 만드는 것이 더 안전하다 — 과소 판정은 사람이 나중에 보완할 수 있지만 과잉 강등·과잉 차단은 되돌리기 어렵다.

## 결정 내용

- `unknown` 등급 항목은 확정률 계산에서 분자 제외·분모 포함(미확정으로 계상)하되, `state-tool verify --evidence-check`는 항상 exit 0을 반환하는 라우터로 설계한다(기존 차단형 게이트와 반환 계약을 분리).
- PM이 ⑤⑥축 판단으로 `unknown` 항목을 확정으로 승격할 수 있고, 승격 시 근거를 산출물에 기재해야 한다.
- 트랙 강등은 4축 전건 충족(AND)만 발동한다 — 한 축이라도 미충족이면 강등하지 않는다.

## 영향 범위

`state_tool.py` `cmd_verify --evidence-check` 분기, `track-routing.md` 강등 규칙. 판정 도구를 신설할 때 일반적으로 적용 가능한 설계 원칙이다 — "무엇을 오작동의 안전한 방향으로 삼을지"를 먼저 정하고 그 다음 판정 로직을 짠다.

## 관련 페이지

- [[decision-vs-fact-claim-separation]]
- [[demote-promote-recursion-guard-timing-threshold-split]]
