---
type: entity
title: test-tool
tags:
- tool
- testing
- pipeline
sources:
- task:039
- task:111
related:
- state-tool
- sdlc-v2-development-artifact-contract
- test-two-tier-system
- scenario-goal-coverage-gate-loop
created: 2026-06-23
updated: '2026-09-09'
status: active
---
## 개요

OPAL 테스트 실행과 시나리오 상태를 결정론적으로 관리하는 CLI 도구다.

## 책임 (WHAT)

- 기존 resolve, check, unit, integration 명령을 유지한다.
- scenario-coverage-build가 sdlc-v2의 AC/C/H/S를 정규화하고 coverage-check가 누락을 판정한다.
- scenario-init, scenario-red, scenario-lock으로 시나리오 명세와 선택적 RED 증거를 동결한다.
- scenario-mark가 PASS, FAIL, BLOCKED와 실행 증거를 기록하고 scenario-status가 전체 결과와 필수 RED 진행을 반환한다.

## 설계 배경 (WHY)

상태와 증거를 Markdown 산문에서 분리해 같은 판정을 반복 추론하지 않게 하고, 구현 전 RED가 필요한 행만 도구가 차단하도록 만들었다. 필드가 없는 기존 JSON은 모든 행을 RED 대상으로 보아 하위호환을 유지한다. (근거: task:111 PLAN `Decisions and contracts`)

## 관계 (HOW)

- [[sdlc-v2-development-artifact-contract]]의 테스트 결과 SSOT를 담당한다.
- [[state-tool]]은 단계·승인을 담당하며 두 도구의 상태 소유권은 겹치지 않는다.
- [[test-two-tier-system]]의 단위·통합 실행 경계를 유지한다.
- [[scenario-goal-coverage-gate-loop]]에 결정론 coverage 결과를 제공한다.

## 소스 커버리지

| 식별자 | 경로 | 설명 |
|---|---|---|
| scenario handlers | `opal/tools/test-tool/lib/scenario.py:154` | 시나리오 정규화와 결과 관리 |
| selective RED lock | `opal/tools/test-tool/lib/scenario.py:257` | RED 대상만 잠금 검사 |
| result status | `opal/tools/test-tool/lib/scenario.py:358` | PASS/FAIL/BLOCKED와 필수 RED 집계 |
| regression tests | `opal/tools/test-tool/tests/test_scenario.py:395` | 선택적 RED와 BLOCKED 공개 CLI 검증 |
