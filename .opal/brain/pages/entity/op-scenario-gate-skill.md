---
type: entity
title: op-scenario-gate (단계 스킬)
module: <code-scan @header module>
layer: <code-scan @header layer>
domain: <code-scan @header domain>
exports: []
source_ref: '<코드 파일 경로 — 예: opal/tools/state-tool/state_tool.py>'
header_synced: <YYYY-MM-DD>
tags:
- skill
- stage-skill
- testing
- scenario-gate
- tool-gated
sources:
- task:073
- task:075
related:
- scenario-goal-coverage-gate-loop
- opal-evaluator-agent
- test-tool
- scenario-gate-pilot-fit-criteria
created: '2026-07-23'
updated: '2026-07-23'
status: draft
---
## 개요

op-scenario-gate는 TEST-SCENARIO 단계에서 목표-커버리지 루브릭 게이트 루프를 컨트롤하는 얇은 단계 스킬이다. 결정론 커버리지 판정(test-tool)과 독립 판단(opal-evaluator-agent)을 단일 호출 지점으로 묶어 종료조건 3종을 판정한다.

## 책임 (WHAT)

- 정규화 페이로드 빌드 — 산출물(가설·매핑 표)과 TASK/PLAN 문서를 읽어 pilot-중립 JSON을 생성한다(`opal/skills/op-scenario-gate/SKILL.md`).
- 결정론 게이트 호출 — `test-tool scenario-coverage-check`(`opal/tools/test-tool/lib/scenario.py:474`) 실행 후 exit code(0/16/17)로 커버리지 완전성을 판정한다.
- 판단 게이트 호출 — opal-evaluator-agent를 `scenario-rubric` phase(`opal/agents/opal-evaluator-agent/AGENT.md:59`)로 디스패치해 판단축 채점과 `SCENARIO-GATE-{N}.md` 보고서를 받는다.
- 종료조건 판정 — 수렴(pass)/반복상한(escalate)/무진전(escalate)/재작성(rewrite) 4분기 verdict를 반환한다.

## 설계 배경 (WHY)

- test-tool은 결정론 판정만 수행하고 루프를 보유하지 않는다는 기존 원칙(`opal/tools/test-tool/test_tool.py:18-20`)을 유지하기 위해, 재작성 루프 컨트롤을 별도 스킬로 분리했다(근거: task:073 ANALYSIS §1.2 분리형 SSOT+얇은 CLI 래퍼 원칙).
- Producer(작성자)와 Evaluator(채점자)를 매 반복 분리해 self-confirming(자체 확인 재발)을 구조적으로 차단한다(근거: task:073 PLAN §3.4.2 [MUST] Producer≠Evaluator).
- 단일 호출 지점 설계 덕분에 후속 pilot 확산 시 정규화 변환기만 추가하면 재사용 가능하다는 예측이 세워졌고(근거: task:073 DONE.md §6), task:075에서 opds·opsdd로 확산하며 실증됐다 — 세 pilot이 동일 스킬을 공유하고 pilot 분기는 Step 2 변환기에 국한된다(근거: task:075 DONE.md §1).

## 관계 (HOW)

- [[test-tool]] — `scenario-coverage-check` 서브명령을 결정론 게이트로 호출한다.
- [[opal-evaluator-agent]] — `scenario-rubric` phase로 판단축 채점을 디스패치한다.
- [[scenario-goal-coverage-gate-loop]] — 이 스킬이 집행하는 루프 설계 결정.
- [[scenario-gate-pilot-fit-criteria]] — 어느 pilot에 접합하는지 판정한 기준.
- 접합 지점: opd(opal-pilot-dev) STEP 3.5, opds(opal-pilot-dev-short) STEP 2 PLAN, opsdd(opal-pilot-sdd) Phase 2 REVIEW 3종(근거: task:075 DONE.md §2).

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `op-scenario-gate/SKILL.md` | `opal/skills/op-scenario-gate/SKILL.md` | 단계 스킬 본문(신규, 140줄) |
| `cmd_scenario_coverage_check` | `opal/tools/test-tool/lib/scenario.py:474` | 결정론 커버리지 서브명령 핸들러 |
| `scenario-rubric` phase | `opal/agents/opal-evaluator-agent/AGENT.md:59` | 판단축 채점 phase(Phase 1-S, 신규) |
