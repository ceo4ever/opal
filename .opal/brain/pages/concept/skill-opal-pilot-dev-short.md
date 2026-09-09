---
type: concept
title: opal-pilot-dev-short — Short Task 오케스트레이터
tags:
- skill
- pilot
- orchestrator
- dev-short
sources:
- skill:opal-pilot-dev-short
- task:111
related:
- sdlc-v2-development-artifact-contract
- skill-opal-pilot-dev
- op-dev-plan
- op-dev-test-scenario
created: '2026-06-11'
updated: '2026-09-09'
status: active
---
## 개요

소규모 개발 작업을 TASK → PLAN → EXECUTE → TEST → CLOSE로 수행하는 오케스트레이터다.

## 현재 계약

- 신규 태스크는 [[sdlc-v2-development-artifact-contract]]를 사용한다.
- PLAN과 TEST-SCENARIO는 한 묶음으로 검토하지만 PM이 각각 한 번 작성하며 PLAN 워커가 시나리오를 대신 쓰지 않는다.
- 구현은 PLAN `Work items`의 선행 관계와 실행 그룹을 따른다.
- 기존 11개 pipeline 행과 interactive, semi-agentic, agentic의 승인 경계를 유지한다.
- 범위가 커지면 Full Task로 전환을 제안한다.

## 근거

`opal/skills/opal-pilot-dev-short/SKILL.md:42`, `opal/skills/opal-pilot-dev-short/SKILL.md:83`, task:111.

## 관련 페이지

- [[sdlc-v2-development-artifact-contract]]
- [[skill-opal-pilot-dev]]
- [[op-dev-plan]]
- [[op-dev-test-scenario]]
