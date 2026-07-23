---
type: concept
title: opds 시나리오 producer 확립 — 공용 스킬 미접촉 SSOT 상충 해소
tags:
- opds
- ssot-conflict
- producer
- shared-skill
- task-075
sources:
- task:075
related:
- skill-opal-pilot-dev-short
- op-dev-test-scenario
- op-scenario-gate-skill
- scenario-gate-pilot-fit-criteria
- readme-ssot-principle
created: '2026-07-23'
updated: '2026-07-23'
status: draft
---
## 개요

opds 오케스트레이터는 설계 워커가 "PLAN과 시나리오 문서를 통합 작성한다"고 서술했으나, 그 설계 워커 스킬은 시나리오 문서를 출력 범위에서 명시 제외한다 — 두 SSOT 문서가 상충했다. opds에 게이트를 접합하려면 시나리오 문서(게이트 입력)가 반드시 생성돼야 하는데, 이 상충 때문에 생성이 보장되지 않았다. task:075는 공용 워커 스킬을 건드리지 않고 opds 오케스트레이터 쪽 서술만 보강해 producer를 확립하는 방식으로 해소했다.

## 결정 배경 (WHY)

- opds STEP 2 서술은 설계 워커가 PLAN 문서와 시나리오 문서를 통합 작성한다고 기술했다(근거: `opal/skills/opal-pilot-dev-short/SKILL.md:54`, task:075 PLAN §2.2.2). 그러나 그 설계 워커 스킬은 시나리오 문서를 출력에서 명시 제외한다(근거: `opal/skills/op-dev-plan/SKILL.md:6,35,146`, task:075 PLAN §2.2.2). 두 SSOT가 상충해 opds 실행 시 게이트 입력(시나리오 문서)이 생성되지 않을 위험이 있었다(근거: task:075 ANALYSIS 발견①).
- 게이트가 존재하지 않는 산출물을 가리키면 빈 산출물을 채점하려다 오판하거나 블로커가 된다 — producer 존재 보장이 접합의 선결 조건이다(근거: task:075 PLAN 리스크 H-1).
- 이 설계 워커 스킬은 opd와 opds가 공유하는 공용 스킬이다. 여기를 수정하면 opd 파이프라인이 회귀할 위험이 있다(근거: task:075 PLAN §2.2.3).

## 결정 내용

- **공용 스킬 미접촉 원칙**: 상충의 한쪽인 공용 설계 워커 스킬은 절대 건드리지 않는다. opd 1차 접합의 회귀를 원천 차단하기 위해서다(근거: task:075 DONE.md §3 캡틴 결정 옵션1).
- **producer는 오케스트레이터가 확립**: opds STEP 2 서술을 "설계 워커는 PLAN 문서만 작성하고, 시나리오 문서는 작성자(PM+소유자 페어)가 통일 시나리오 형식을 참조해 직접 작성한다"로 교체한다. 이는 작성자와 설계 워커를 분리해 self-confirming을 막는, opd STEP 3.5와 동형인 절차다(근거: task:075 PLAN §3.2.2, DONE.md §3).
- 실증: 공용 설계 워커 스킬의 diff가 0임을 확인해 opd 무영향을 입증했다(근거: task:075 DONE.md §3).
- 일반 원칙: 여러 오케스트레이터가 공유하는 스킬과 특정 오케스트레이터 전용 서술이 상충할 때, 공용 쪽을 바꾸면 다른 소비자가 회귀하므로 전용 오케스트레이터 쪽을 보강해 해소하는 것이 안전하다.

## 영향 범위

- `opal/skills/opal-pilot-dev-short/SKILL.md` — STEP 2 producer 확립 서술 + 게이트 배선(수정).
- `opal/skills/op-dev-plan/SKILL.md` — 공용 설계 워커 스킬(미접촉, diff 0).
- `opal/skills/opal-pilot-dev/SKILL.md` — opd 1차 접합(회귀 방지 대상, 무변경).

## 관련 페이지

- [[skill-opal-pilot-dev-short]]
- [[op-dev-test-scenario]]
- [[op-scenario-gate-skill]]
- [[scenario-gate-pilot-fit-criteria]]
- [[readme-ssot-principle]]
