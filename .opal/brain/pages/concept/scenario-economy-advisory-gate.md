---
type: concept
title: 테스트 시나리오 작성 경제성 — 중복·과잉 억제와 advisory 응답 게이트
tags:
- testing
- scenario-gate
- test-scenario
- advisory
- opd
- opds
sources:
- task:167
related: [scenario-goal-coverage-gate-loop, op-scenario-gate-skill, test-tool, state-tool, op-dev-test-scenario]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

TEST-SCENARIO 작성 시 중복·과잉 시나리오를 구조적으로 억제하고, 독립 평가자(evaluator)가 발견한 개선 여지를 담당자가 일방적으로 무시하거나 채택하지 못하게 ID 단위 응답을 강제하는 계약이다. 제안서(`docs/proposals/archives/opal-test-scenario-economy-gate.md`)의 설계를 작성 가이드·test-tool·state-tool에 반영했다(task:167).

## 결정 배경 (WHY)

- 작성 기준이 없어 별도 시나리오로 쪼갤지, assertion으로 통합할지, Check로 낮출지가 담당자 재량에만 맡겨져 과잉·중복 시나리오가 누적됐다. 고유 결함 신호·같은 실행·가장 저렴한 충분 계층이라는 3개 판단 기준을 작성 가이드에 명문화했다(근거: task:167 DONE.md AC-1).
- 시나리오 표에 `유형` 열이 있어도 그 선언이 coverage builder → test-agent → `test-scenario.json`까지 전달되지 않아, 유형에 따른 자동 검사(check+RED 모순 차단 등)를 걸 수 없었다(근거: task:167 PLAN 확인 사실).
- evaluator의 개선 제안이 구조화돼 있지 않아 반영 여부가 담당자 재량으로 소실됐다. 개선 여지를 `advisories[]`로 구조화하고 ID 단위 응답(`apply`/`retain`+사유)을 강제한 뒤, `apply`가 있으면 대상 문서를 고쳐 재판정(refinement)하도록 설계했다(근거: task:167 DONE.md AC-4~AC-6).

## 결정 내용

- **유형 열 전환·전달**: `Scenarios` 표에 `유형` 열이 있으면 모든 행이 `unit·integration·contract·regression·e2e·check` 중 하나여야 하며, 누락·오값은 `coverage_input_invalid` exit 17로 거부한다. builder가 각 시나리오에 `type`·`red_required`를 실어 payload를 만들고, test-agent가 `scenario-init` 입력에 그대로 전달해 `test-scenario.json`까지 유형이 도달한다.
- **check+RED 모순 차단**: 유형 `check`이면서 구현 전 RED 대상인 행은 builder와 `scenario-init` 양쪽에서 거부한다. `red_required`가 없는 check는 true로 읽히므로 역시 거부 대상이다.
- **정확 중복 차단**: 유형·조건·행동·기대 결과·방법·환경·시점 6셀이 모두 같은 두 행은 builder가 exit 17(`duplicate scenario content`)로 거부한다. 기대 결과만 다른 행은 통과한다.
- **advisory 결과 계약**: evaluator의 `scenario-rubric`·`design-rubric` 결과에 pass 점수와 분리된 최상위 `advisories[]`(원소: `{id: A-N, kind: subsumed|mergeable|cheaper_layer|misclassified, targets: [S-ID], basis, recommendation}`)를 추가했다. refinement 입력에서는 빈 배열만 반환한다.
- **advisory 응답 게이트**: PM은 `run/<gate>-i<N>-responses.json`에 `[{id, response: apply|retain, reason}]`를 써서 기록 명령에 넘긴다. 응답 ID 집합은 advisory ID 집합과 정확히 같아야 하고, `retain`은 공백이 아닌 사유가 필요하다. 위반하면 기록을 거부하고 상태를 바꾸지 않는다.
- **반영 전이(refinement)**: `apply`가 1건 이상이면 history에 `verdict: rewrite`·`reason: advisory_apply`를 기록하고 대상 문서를 고쳐 반복 상한을 소비하지 않는 refinement 1회로 재판정한다. refinement가 실패하면 기존 `retry_limit`·`reset --owner user` 경로로 들어간다.
- **목표-커버 게이트 기록·검증 분리**: 새 `test-tool scenario-gate-record`가 매 회차 이력을 원자 기록하고(스킬은 더 이상 이력을 직접 편집하지 않는다), `scenario-gate-verify`가 마지막 원소의 `verdict: pass`와 현재 문서 묶음 hash 일치를 검사한다. `state-tool mark`가 `test_scenario.scenario_gate`·`plan.scenario_gate` 행을 완료로 바꿀 때 이 검증을 강제 호출하며 `--force`·`--auto-pass`로도 우회할 수 없다.

## 영향 범위

- `opal/tools/test-tool/lib/scenario.py`, `opal/tools/test-tool/lib/e2e_contract.py`, `opal/tools/test-tool/schema/test-scenario.schema.json`
- `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/schema/state.schema.json`
- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`, `opal/skills/op-scenario-gate/SKILL.md`, `opal/skills/op-scenario-gate/README.md`
- `opal/agents/opal-evaluator-agent/AGENT.md`, `opal/agents/opal-test-agent/AGENT.md`
- `opal/core/references/harness/scenario-gate.md`, `opal/core/references/harness/design-gate.md`, `opal/core/references/harness/test-cycle.md`

## 관련 페이지

- [[scenario-goal-coverage-gate-loop]]
- [[op-scenario-gate-skill]]
- [[test-tool]]
- [[state-tool]]
- [[op-dev-test-scenario]]
