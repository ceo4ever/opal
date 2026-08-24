---
type: concept
title: 분리형 반환 계약 — 기존 키의 분모를 확대하지 않는다
tags:
- api-contract
- return-value
- denominator
- silent-break
- opd
sources:
- task:100
related:
- new-ssot-pointer-not-value-copy
created: '2026-08-24'
updated: '2026-08-24'
status: draft
---
## 개요

공유 반환 값의 분모(대상 항목 집합)를 확대해야 할 때, 기존 키의 의미·분모는 그대로 두고 신규 키를 추가하는 "분리형"을 채택했다. 값의 형식(비율 등)이 그대로면 분모가 바뀌어도 소비자가 감지하지 못하는 조용한 계약 파괴가 되기 때문이다(근거: task:100 PLAN.md PD-1).

## 결정 배경 (WHY)

- (근거: task:100 PLAN.md PD-1) `state_tool.py`의 `confirmed_ratio`에 "확정된 설계 방향" 항목까지 포함시켜 분모를 늘리는 방안이 있었으나, 이는 기존 소비자가 알던 "명확화 결과 전용" 분모 정의를 몰래 바꾸는 것과 같다.
- 값 형식(예: 0.0~1.0 비율)이 그대로 유지되므로, 분모가 바뀌었다는 사실이 반환 값만 봐서는 드러나지 않는다 — 이것이 "조용한" 계약 파괴다.

## 결정 내용

- 기존 `confirmed_ratio` 키는 분모·의미를 불변으로 유지한다(명확화 결과 항목 전용).
- 확정된 설계 방향 항목의 비율은 신규 키 `direction_confirmed_ratio`로 분리 반환한다.
- `items[]`·`unconfirmed[]`는 병합하되, 각 항목에 출처를 구분하는 `source` 필드(`clarification` | `confirmed_direction`)를 추가해 소비자가 필요 시 분리 계산할 수 있게 한다(근거: `opal/tools/state-tool/state_tool.py:2554-2557`, `opal/tools/state-tool/README.md:288-289`).
- 신규 키 추가는 이를 모르는 기존 소비자에게 무해하지만, 기존 키의 분모 확대는 유해하다는 비대칭이 이 결정의 핵심 판단 기준이다.

## 영향 범위

여러 소비자가 참조하는 공유 반환 계약(CLI JSON, API 응답 등)에서 대상 범위를 확장해야 할 때 일반적으로 적용 가능한 패턴 — 분모를 넓히지 말고 새 키를 만든다.

## 관련 페이지

- [[new-ssot-pointer-not-value-copy]]
