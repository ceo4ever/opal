---
type: concept
title: 테스트 시나리오 파이프라인 재설계 (2차원 매트릭스 + self-confirming 4분리)
tags:
- testing
- pipeline
- framework
- flow
- task
sources:
- task:004
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

OPAL 테스트 시나리오 작성 시점·작성자·파이프라인 구조를 전면 재설계했다. PLAN 워커와 분리된 self-confirming 4분리 구도(PLAN / TEST-SCENARIO / EXECUTE / TEST)와 L×M 2차원 검증 매트릭스가 핵심이다.

## 배경·문제 (WHY)

mams 프로젝트에서 단위 테스트 PASS 후 운영 회귀 12건이 발생했다. PLAN 워커가 AC 중심으로 "당연한 시나리오"를 양산하는 self-confirming 구조가 원인이었다.

## 결정 내용 (HOW)

- 작성 시점: PLAN 직후 STEP 3.5로 신설 — PM(알투)+캡틴 페어 작성, PLAN 워커와 분리.
- 검증 차원: 2차원 매트릭스 — 깊이 L1(기능)/L2(통합)/L3(시스템) × 방식 M1(수동)/M2(자동)/M3(탐색적).
- mock 0 강제: grep 감지 시 PM Gate FAIL.
- `scenario_source` input 추가로 EXECUTE 워커가 시나리오를 참조하도록 흐름 변경.
- L3 [SUPERVISOR] 즉시 PM 반환 의무화.

## 영향·관계

- 변경 파일: `opal-pilot-dev/SKILL.md` (4→5단계), `op-dev-test-scenario/SKILL.md`, `op-dev-execute/SKILL.md`, `op-dev-plan/SKILL.md`, `opal-test-agent/AGENT.md`.
- [[opal-architecture]] 파이프라인 흐름 변경.

## 근거 출처

`sources: task:004` — DONE.md §1~§2 참조.
