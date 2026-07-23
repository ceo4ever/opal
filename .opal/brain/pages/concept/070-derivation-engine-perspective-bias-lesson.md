---
type: concept
title: 070 사건 근본원인 — 도출 엔진 관점 편향과 게이트 집행
tags:
- lesson-learned
- testing
- scenario-gate
- root-cause
- task-073
sources:
- task:073
- task:070
related:
- scenario-goal-coverage-gate-loop
- state-tool-task-step-key-address
created: '2026-07-23'
updated: '2026-07-23'
status: draft
---
## 개요

태스크 070에서 핵심 목표(--row→key 주소 전환)를 검증하는 시나리오 자체가 존재하지 않은 채 TEST-SCENARIO 단계가 통과 처리된 사건이 있었다. 근본 원인은 "루브릭 부재"가 아니라 "도출 엔진의 관점 편향"이다.

## 원인 분석 (WHY)

- 070은 시나리오를 실제로 작성하고 통과시켰으나, 핵심 목표를 검증하는 시나리오 자체가 도출되지 않았다 — "시나리오가 FAIL했는데 놓친" 것이 아니라 "애초에 존재하지 않았다"는 점이 핵심이다(근거: task:073 ANALYSIS §4 발견⑤).
- 도출 엔진(`opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`)이 리스크 가설(파괴 관점, H-N)만 도출 입력으로 삼고 목표 달성(채택 관점)을 입력에 포함하지 않았다 — 파괴 관점 편향이다(근거: task:073 ANALYSIS §4 발견②, PLAN §2.1.2).
- 기존 PM Gate 완전성 검사는 "가설↔시나리오 매핑 완전"만 확인하고 "TASK 요구사항 전체 커버·목표 관점"을 검사하지 않아, 매핑 표 자체가 완전해 보여도 핵심 목표 누락을 잡지 못했다(근거: task:073 ANALYSIS §4 발견②).

## 교훈 및 집행

- 결정론 매핑 커버리지(요구/기능/리스크)만으로는 "관점 편향"을 못 잡는다 — 독립 평가자가 "목표 달성 관점에서 이 시나리오 집합이 충분한가"를 별도 판단축으로 채점해야 재발을 막는다.
- 이 교훈은 산문 권고가 아니라 tool-gated 게이트로 집행되었다 — 도출 엔진에 목표/채택 관점 입력을 추가하고, 게이트 통과 조건에 판단축(①목표달성·⑤채택/잔존·⑥경계/부정) 임계를 넣었다(→ [[scenario-goal-coverage-gate-loop]]).
- 자기적용(음성통제)으로 실증했다: 목표 시나리오를 의도적으로 누락한 페이로드로 게이트를 돌려 커버리지 미달·판단축 미달로 FAIL을 확인하고, 복원 후 누락 0·판단축 통과로 PASS 수렴을 확인했다(근거: task:073 DONE.md §3 R-8, §2 R-8).

## 관련 페이지

- [[scenario-goal-coverage-gate-loop]]
- [[state-tool-task-step-key-address]]
