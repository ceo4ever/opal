---
type: concept
title: 워커 중단 시 재개 대신 산출물 실측 판정 — 중단과 미완은 별개 사실
tags:
- agentic
- worker
- pm-discipline
- resilience
- task-095
sources:
- task:095
- task:081
related:
- long-running-worker-infra-failure-mitigation
- agentic-output-direct-verification-lesson
- mitigation-recurs-without-ssot-registration
- scenario-prewrite-goal-series-track
created: '2026-08-19'
updated: '2026-08-19'
status: draft
---
## 개요

워커가 인프라 오류로 조기 종료했을 때 기본 반응은 재개다. 그러나 산출물을 실측해 담당 범위가 전건 완료로 확인되면 재개하지 않고 PM 교차 검증으로 대체하는 것이 옳다 — 재개는 완료분을 덮어쓸 위험을 새로 만든다.

## 배경 (WHY)

- 최초 적용 태스크의 테스트 단계에서 워커가 API 오류로 조기 종료했다. 보고를 받지 못한 상태였으므로 완료 범위를 알 수 없는 상황이었다(근거: task:095 DONE.md §6 워커 중단 대응).
- 산출물을 직접 읽어 대조한 결과 담당 16건이 전건 완료돼 있었다. 이 상태에서 워커를 재개하면 이미 작성된 판정을 다시 쓰게 되고, 산출물 덮어쓰기 위험이 생긴다(근거: task:095 DONE.md §6).
- 판정 절차는 이미 하네스 규칙으로 확립돼 있었다 — 산출물을 확정하고 실행 체크리스트와 대조해 완료·잔여를 판정한 뒤 잔여만 재배치하며, 완료분 덮어쓰기를 금지한다(`opal/core/references/harness/pm-review-gate.md:17`, task:081에서 신설).

## 결정 내용

- 워커 중단 시 재개 판단은 워커의 종료 사유가 아니라 **산출물 실측**으로 한다. 담당 범위가 전건 완료면 재개하지 않고 PM이 산출물을 직접 읽어 교차 검증한다(근거: task:095 DONE.md §6).
- 교차 검증은 워커 보고를 옮기는 것이 아니라 PM이 산출물을 직접 읽고 재판정하는 것이다 — 최초 적용 태스크에서 게이트 판단 13회를 전건 이 방식으로 수행했다(근거: task:095 DONE.md §6, → [[agentic-output-direct-verification-lesson]]).
- 일반 원칙: 중단은 실패의 증거가 아니다. 중단과 미완은 별개 사실이며, 둘을 구분하는 유일한 수단이 산출물 실측이다.

## 영향 범위

- `opal/core/references/harness/pm-review-gate.md:17` — 실측 판정 3단계 절차의 규칙 SSOT(본 태스크에서 변경하지 않고 적용).
- 최초 적용 태스크의 테스트 단계 판정 — 시나리오 18건 전건 통과 판정이 이 경로로 확정됐다(근거: task:095 DONE.md §4).

## 관련 페이지

- [[long-running-worker-infra-failure-mitigation]]
- [[agentic-output-direct-verification-lesson]]
- [[mitigation-recurs-without-ssot-registration]]
- [[scenario-prewrite-goal-series-track]]
