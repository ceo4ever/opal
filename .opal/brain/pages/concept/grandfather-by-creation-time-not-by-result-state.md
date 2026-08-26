---
type: concept
title: 유예 기준은 결과 상태가 아니라 생성 시각으로 잡는다 — 「기록 0건이면 유예」의 자기무력화
tags:
- enforcement
- migration
- backward-compat
- state-tool
- lesson-learned
sources:
- task:103
related:
- enforce-rule-legacy-data-surfacing-lesson
- backward-compat-default-value-discipline
- enforcement-basis-must-be-structural-not-voluntary
created: '2026-08-26'
updated: '2026-08-26'
status: draft
---
## 개요

새 규범을 기존 데이터에 소급하지 않으려면 유예가 필요하다. 이때 유예 조건을 **결과 상태**(예: 「기록이 하나도 없으면 예전 것」)로 잡으면, 규범을 통째로 어긴 신규 대상이 정확히 그 조건을 만족해 빠져나간다. 유예는 **생성 시각**처럼 대상이 바꿀 수 없는 값으로 고정해야 한다 (근거: task:103 DONE.md §3.3).

## 결정 배경 (WHY)

- 워커 소요 기록을 강제하면서, 계측 도입 전에 만들어진 태스크는 소급 기록이 불가능하므로 유예 대상으로 두어야 했다.
- 첫 설계는 「해당 태스크에 워커 기록이 0건이면 유예」였다 — 예전 태스크는 당연히 0건이라는 관찰에서 나온 조건이다.
- 그러나 **전건 미기록인 신규 태스크도 0건**이다. 즉 규범을 가장 심하게 어긴 경우가 면제 조건과 정확히 일치해, 강제가 스스로 무의미해진다 (근거: task:103 DONE.md §3.3 유예 기준).
- 이 오류는 설계 단계 검토가 아니라 실증으로 발견됐다.

## 결정 내용

- 유예 기준을 태스크의 **생성 시각**으로 옮겼다 — 계측 도입일 이전에 생성된 태스크만 유예하고, 이후 생성분에는 예외를 두지 않는다 (근거: task:103 DONE.md §3.3).
- 생성 시각은 대상의 행동으로 바뀌지 않는 값이므로, 유예를 노리고 규범을 어기는 경로가 만들어지지 않는다.
- 같은 계열의 앞선 교훈은 enforce 규칙을 새로 세울 때 잔존 데이터를 배포 전에 실 데이터로 스캔해 표면화하라는 것이었다([[enforce-rule-legacy-data-surfacing-lesson]]) — 이 페이지는 그 스캔 이후 **어디까지를 legacy로 부를 것인가**의 기준을 다룬다.

## 영향 범위

마이그레이션·하위호환 유예를 두는 모든 규칙 신설. 유예 조건이 「위반의 결과와 구별되는가」를 먼저 확인해야 하며, 구별되지 않으면 그 유예는 우회로다.

## 관련 페이지

- [[enforce-rule-legacy-data-surfacing-lesson]]
- [[backward-compat-default-value-discipline]]
- [[enforcement-basis-must-be-structural-not-voluntary]]
