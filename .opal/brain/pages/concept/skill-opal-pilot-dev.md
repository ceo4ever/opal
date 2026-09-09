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
- task:111
related:
- sdlc-v2-development-artifact-contract
- skill-opal-pilot-dev-short
- op-dev-analysis
- op-dev-plan
- op-dev-test-scenario
created: '2026-06-11'
updated: '2026-09-09'
status: active
---
## 개요

대규모 개발 작업을 TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST → CLOSE로 수행하는 오케스트레이터다.

## 현재 계약

- 신규 태스크는 [[sdlc-v2-development-artifact-contract]]를 사용한다.
- 프로젝트 지식과 code map을 먼저 확인하고 `docs/PROJECT.md` 레지스트리에서 작업에 관련된 문서만 선별한다.
- PLAN `Work items`의 담당·파일 소유권·선행 관계·실행 그룹을 기준으로 구현을 순차 또는 병렬 디스패치한다.
- PM은 런타임에서 실제 제공되는 capability와 용도만 워커에게 주입한다.
- interactive, semi-agentic, agentic의 사용자 확인과 CLOSE 경계는 기존 계약을 유지한다.

## 근거

`opal/skills/opal-pilot-dev/SKILL.md:74`, `opal/skills/opal-pilot-dev/SKILL.md:124`, `opal/skills/opal-pilot-dev/SKILL.md:129`, task:111.

## 관련 페이지

- [[sdlc-v2-development-artifact-contract]]
- [[skill-opal-pilot-dev-short]]
- [[op-dev-analysis]]
- [[op-dev-plan]]
- [[op-dev-test-scenario]]
