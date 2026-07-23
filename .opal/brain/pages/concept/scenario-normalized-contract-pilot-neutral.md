---
type: concept
title: 시나리오 정규화 계약 — pilot-중립 페이로드 설계
tags:
- contract
- scenario-gate
- normalization
- multi-pilot
- task-073
sources:
- task:073
related:
- scenario-goal-coverage-gate-loop
- oppl-surface-inventory-contract
created: '2026-07-23'
updated: '2026-07-23'
status: draft
---
## 개요

5개 pilot(opd/opds/opsdd/oppl/oppd)의 시나리오 산출물 포맷이 서로 달라(JSON vs 마크다운 테이블), 목표-커버 게이트를 여러 pilot이 공유하는 컴포넌트로 재사용하려면 pilot-중립 정규화 계약이 필요했다.

## 배경 (WHY)

- opd는 마크다운 TEST-SCENARIO.md(가설 표+매핑 표), opds는 PLAN.md 흡수형, opsdd는 TEST-SCENARIOS.md(자체 FR↔TS 커버리지 보유), oppl은 test-scenario.json(spec/result 분리), oppd는 액션 에이전트 내부 파이프라인의 한 단계 — 근본적으로 JSON과 마크다운 테이블이라는 포맷 이질성이 있다(근거: task:073 ANALYSIS §4 발견①).
- 도구(test-tool) 서브명령이 특정 pilot의 원본 포맷에 종속되면 향후 다른 pilot으로 확산할 때 재작업이 필요해진다(근거: task:073 ANALYSIS §1 R-T3).

## 결정 내용

- 입력 계약(정규화 JSON): `{goal, requirements[], features[], hypotheses[], scenarios[]}` — `scenarios[]`의 각 항목은 `{id, covers_requirements[], covers_features[], covers_hypotheses[], is_goal_scenario, is_adoption_scenario, is_boundary_scenario}`(근거: `opal/core/references/harness/scenario-gate.md` §3).
- 출력 계약: 결정론 파트 `{missing: {requirements[], features[], hypotheses[]}}` + 판단 파트 `{scores: {goal, adoption, boundary}, gaps[]}`.
- 변환 책임은 단계 스킬(op-scenario-gate)이 지고, 도구는 pilot-중립 페이로드만 소비한다 — pilot별 원본 포맷을 도구가 직접 파싱하지 않는다(근거: `opal/tools/test-tool/lib/scenario.py:474` docstring, task:073 PLAN §3.1.2).
- 1차 적용(opd)에서는 op-scenario-gate가 TEST-SCENARIO.md의 가설 표·매핑 표 + TASK.md 요구사항/AC + PLAN.md 기능/리스크를 읽어 이 페이로드로 변환한다.
- 확장 근거: 후속 pilot 확산 시 pilot별 정규화 변환기만 추가하면 동일 게이트(도구+평가자)를 재사용할 수 있다(근거: task:073 DONE.md §6 확산 후속).

## 관련 페이지

- [[scenario-goal-coverage-gate-loop]]
- [[oppl-surface-inventory-contract]]
