---
type: concept
title: TEST-SCENARIO 목표-커버리지 루브릭 게이트 루프 — 결정론+판단 분리
tags:
- testing
- scenario-gate
- tool-gated
- rubric
- opd
- task-073
- task-075
sources:
- task:073
- task:075
- task:167
related: [test-scenario-pipeline-redesign, op-dev-test-scenario, oppl-coverage-conformance-axis-split, loop-upper-bound-ssot-pattern, scenario-gate-pilot-fit-criteria, op-scenario-gate-skill, scenario-economy-advisory-gate, state-tool]
created: '2026-07-23'
updated: '2026-10-01'
status: draft
---
## 개요

TEST-SCENARIO 단계를 "목표 달성 검증"으로 재정의하는 작은 수렴 루프다. Producer(작성) → 결정론 커버리지 게이트(도구) → 독립 평가자 루브릭 채점(판단) → 종료조건 판정 → 재작성 순으로 돌며, 1차로 opd 파이프라인에 접합한 뒤 task:075에서 opds·opsdd로 확산했다. task:167에서 평가자의 개선 제안을 구조화된 advisory 응답 게이트로, 목표-커버 게이트 이력 기록·검증을 도구 명령으로 승격했다.

## 결정 배경 (WHY)

- 기존 TEST-SCENARIO 검증은 "가설↔시나리오 매핑 완전성"만 검사하고 "TASK 요구사항 전체 커버·목표 달성 관점"이 빠져 있었다(근거: task:073 ANALYSIS §4 발견②).
- 070 사건에서 핵심 목표를 검증하는 시나리오 자체가 도출되지 않은 채 완료 처리된 사례가 있었다 — 결정론 매핑 검사만으로는 "관점이 애초에 없는" 문제를 못 잡는다(근거: task:073 ANALYSIS §4 발견⑤, → [[070-derivation-engine-perspective-bias-lesson]]).
- oppl Loop 2가 이미 "결정론 커버리지 게이트 + 독립 판단자(평가자) + 종료조건" 3중 구조를 실증한 선례를 갖고 있어, 이를 시나리오 문서 1건 단위로 축소 재사용했다(근거: task:073 ANALYSIS §4 발견③).
- 루프가 정착된 뒤에도 evaluator가 찾아낸 개선 여지(중복·통합 가능·더 싼 계층으로 대체 가능 등)가 구조화돼 있지 않아 반영 여부가 담당자 재량으로 소실됐고, 목표-커버 게이트 이력을 스킬이 직접 append하던 방식이라 기록 누락을 기계적으로 막을 수 없었다(근거: task:167 PLAN 확인 사실 "목표-커버 게이트 이력은 스킬이 직접 append한다").

## 결정 내용

- 루브릭 6축을 판정 주체 기준으로 분리한다: ②요구 커버·③기능 커버·④리스크 커버는 도구가 결정론으로 판정하고, ①목표 달성·⑤채택/잔존·⑥경계/부정은 독립 평가자가 판단축으로 채점한다(근거: `opal/core/references/harness/scenario-gate.md` §2).
- 종료조건 3종: (1) 수렴 — 커버리지 누락 0 AND 판단축 각 ≥1점 AND 평균 ≥1.5점(0~2 척도)이면 PASS. (2) 반복 상한 — 3회 초과 시 사용자 에스컬레이션. (3) 무진전 — 연속 2회 gaps·점수 개선이 없으면 사용자 에스컬레이션(근거: `opal/core/references/harness/scenario-gate.md` §5).
- tool-gated 2증거 원칙: 게이트 통과 선언은 도구의 exit 0(누락 없음)과 평가자의 verdict pass가 모두 존재할 때만 가능하다 — 담당자가 스스로 통과를 선언할 수 없다(근거: `opal/core/references/harness/scenario-gate.md` §6).
- 루프 상한 수치는 harness SSOT(`opal/core/references/opal-harness.md` §1)에 신규 행으로 등록했고, 이 규칙 문서는 수치를 복제하지 않고 참조만 한다(근거: task:073 PLAN §3.1.2).
- **advisory 응답 게이트(task:167)**: evaluator가 pass이고 refinement 회차가 아니며 `advisories[]`가 1건 이상이면, PM이 ID 단위로 `apply`/`retain`(+사유)을 응답해야 게이트를 완료로 기록할 수 있다. `apply`가 있으면 history에 `verdict: rewrite`·`reason: advisory_apply`를 남기고 대상 문서를 고쳐 반복 상한을 소비하지 않는 refinement 1회로 재판정한다(근거: task:167 PLAN Decisions "advisory 반영 전이"). advisories가 빈 배열이면 응답은 선택이다.
- **목표-커버 기록·검증 명령화(task:167)**: `test-tool scenario-gate-record`가 매 회차 1회 호출되어 coverage 재판정·evaluator 결과·advisory 응답 검사·묶음 hash 계산·판정(pass/rewrite/escalate)을 원자 기록한다. `scenario-gate-verify`는 마지막 원소가 `verdict: pass`이고 현재 묶음 hash와 일치할 때만 exit 0이다. `state-tool mark`가 `test_scenario.scenario_gate`·`plan.scenario_gate` 행을 완료로 바꿀 때 이 검증을 강제 호출하며 `--force`·`--auto-pass`로도 우회할 수 없다(근거: task:167 PLAN Decisions "목표-커버 기록 명령"·"mark 가드").

## 영향 범위

- `opal/core/references/harness/scenario-gate.md` — 이 결정의 SSOT 문서(루브릭 6축·정규화 계약·종료조건·tool-gated 원칙, advisory·refinement 판정 의미 추가).
- `opal/tools/test-tool/lib/scenario.py:474` — 결정론 커버리지 판정 서브명령(`scenario-coverage-check`, exit 16/17). `:1377` `scenario-gate-record`, `:1639` `scenario-gate-verify`(task:167 신설).
- `opal/agents/opal-evaluator-agent/AGENT.md:59` — 판단축 채점 phase(`scenario-rubric`) 추가. task:167부터 결과에 `advisories[]` 포함.
- `opal/skills/op-scenario-gate/SKILL.md` — 루프 컨트롤 스킬(신규, → [[op-scenario-gate-skill]]). task:167부터 매 회차 `scenario-gate-record` 호출로 이력 기록을 넘긴다.
- `opal/skills/opal-pilot-dev/SKILL.md` — opd STEP 3.5 접합(1차 적용).
- `opal/skills/opal-pilot-dev-short/SKILL.md` — opds STEP 2 PLAN 접합(task:075 확산).
- `opal/skills/opal-pilot-sdd/SKILL.md` — opsdd Phase 2 REVIEW 접합(task:075 확산, self-confirming 해소).
- `opal/tools/state-tool/state_tool.py` — task:167부터 `design-gate record --advisory-responses`(PM 경로)와 `cmd_mark`의 목표-커버 게이트 행 검증 가드를 추가(→ [[state-tool]]).

## 관련 페이지

- [[test-scenario-pipeline-redesign]]
- [[op-dev-test-scenario]]
- [[oppl-coverage-conformance-axis-split]]
- [[loop-upper-bound-ssot-pattern]]
- [[070-derivation-engine-perspective-bias-lesson]]
- [[op-scenario-gate-skill]]
- [[scenario-gate-pilot-fit-criteria]]
- [[scenario-economy-advisory-gate]]
- [[state-tool]]
