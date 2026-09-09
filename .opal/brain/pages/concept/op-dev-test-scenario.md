---
type: concept
title: op-dev-test-scenario — 테스트 시나리오 작성 단계 스킬
tags:
- dev
- test
- skill
sources:
- skill:op-dev-test-scenario
- task:111
related:
- sdlc-v2-development-artifact-contract
- op-dev-plan
- test-tool
- scenario-goal-coverage-gate-loop
created: '2026-06-11'
updated: '2026-09-09'
status: active
---
## 개요

TASK의 완료 기준·제약과 PLAN의 실제 위험을 실행 전 검증 기준으로 연결하는 시나리오 작성 스킬이다.

## 현재 계약

출력은 Setup과 Scenarios 두 절만 사용한다. 각 시나리오는 검증 대상, 조건, 행동, 기대 결과, 방법·환경, 시점을 가진다. 결과와 증거를 문서에 쓰지 않고 test-tool이 관리하는 `test-scenario.json`에 기록한다. 시점이 `구현 전 RED`인 행만 `red_required: true`가 된다.

## 근거

`opal/skills/op-dev-test-scenario/SKILL.md:16`, `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:18`, task:111.

## 관련 페이지

- [[sdlc-v2-development-artifact-contract]]
- [[op-dev-plan]]
- [[test-tool]]
- [[scenario-goal-coverage-gate-loop]]
