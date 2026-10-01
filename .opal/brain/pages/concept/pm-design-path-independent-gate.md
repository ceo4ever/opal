---
type: concept
title: PM 설계 경로 단일화와 독립 설계 게이트
tags:
- pm
- design-gate
- task
sources:
- task:157
related: [actor-axis-orthogonal-to-mode, scenario-goal-coverage-gate-loop, opal-evaluator-agent, state-tool]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

opd·opds의 신규 PM 조율 태스크가 두 트랙 공통 PM 경로 파이프라인으로 시작하고, EXECUTE 전에 결정론 검사와 독립 평가자 판정을 함께 거치는 설계 게이트를 통과하도록 한 결정이다(`tasks/157-260924-opds-PM-설계경로-단일화와-독립-설계게이트/DONE.md:5`, `opal/skills/opal-pilot-dev/references/pipeline-pm.json`).

## 핵심 결정

- EXECUTE 전 행은 TASK 작성·확인, PLAN 작성, TEST-SCENARIO 작성, 설계 게이트, 설계 확인 여섯 개다. 별도 분석 단계 없이 PLAN 안 Findings 절에 직접 변경·회귀 확인·문서 갱신·미확인 가정을 나눠 적는다(`tasks/157-260924-opds-PM-설계경로-단일화와-독립-설계게이트/DONE.md:5-7`).
- 설계 게이트는 TASK 구조, 작업 항목의 완료조건 전수 연결, Findings 규칙, 시나리오 커버리지를 결정론으로 검사하고, 독립 평가자가 설계 4축과 시나리오 3축을 한 번에 판정한다(`tasks/157-260924-opds-PM-설계경로-단일화와-독립-설계게이트/DONE.md:8`).
- TASK·PLAN·TEST-SCENARIO 묶음 해시를 평가 시작·종료·승인 시점에 기록하고, 현재 묶음과 평가 통과 묶음과 승인 묶음이 모두 같을 때만 EXECUTE에 들어간다. 재평가는 이전 승인을 무효화한다(`tasks/157-260924-opds-PM-설계경로-단일화와-독립-설계게이트/DONE.md:9`).
- 반복 상한 3회에 도달하면 심각도와 무관하게 사용자 대기이고 해제는 사용자 리셋뿐이다. 설계 중 결정은 외부 영향(사용자 대기)과 세부(PM 기록)로 나눠 기록한다(`tasks/157-260924-opds-PM-설계경로-단일화와-독립-설계게이트/DONE.md:10-11`).
- 기존 파이프라인과 저장 행으로 재개하는 기존 태스크는 바꾸지 않는다. PM 경로 판정은 설계 게이트 행 존재로만 한다(`tasks/157-260924-opds-PM-설계경로-단일화와-독립-설계게이트/DONE.md:14`).

## 관련 페이지

- [[actor-axis-orthogonal-to-mode]]
- [[scenario-goal-coverage-gate-loop]]
- [[opal-evaluator-agent]] · [[state-tool]]
