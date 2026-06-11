---
type: concept
title: opal-pilot-dev — Full Task 오케스트레이터
tags:
- skill
- pilot
- orchestrator
- dev
sources:
- skill:opal-pilot-dev
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

대규모 개발 작업을 위한 Full Task 오케스트레이터. 7단계 파이프라인(TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST → CLOSE)으로 코드 개발 작업을 수행한다.

## 배경·문제 (WHY)

복잡한 개발 태스크는 분석·설계·실행·검증의 각 단계가 명확히 분리되어야 품질을 보장할 수 있다. 규모가 작은 작업은 opds(Short Task)를 사용한다.

## 결정 내용 (HOW)

오케스트레이터가 각 단계에서 전문 워커(op-dev-analysis, opal-plan-agent, opal-test-agent 등)를 디스패치. 하네스 모드(--interactive/--agentic/--semi-agentic)로 자동화 수준을 선택. state-tool로 단계 진행 상태 관리.

## 영향·관계

opds(Short)와 같은 하네스를 공유. ANALYSIS 단계가 추가된 대규모 전용 경로. opal-pilot-sdd(SDD) 및 opds와 트레이드오프 관계.

## 관련

- [[op-dev-analysis]] — ANALYSIS 단계에서 디스패치하는 코드 분석 워커 스텝
- [[op-dev-plan]] — PLAN 단계에서 디스패치하는 설계 워커 스텝
- [[opal-project-definition]] — Full Task 파이프라인의 컨텍스트 로딩 기준 문서

## 근거 출처

file_path: `opal/skills/opal-pilot-dev/SKILL.md`
