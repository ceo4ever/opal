---
type: concept
title: sdlc-v2 개발 산출물 계약
tags:
- sdlc
- development
- artifact
- ssot
- pipeline
sources:
- task:111
related:
- skill-opal-pilot-dev
- skill-opal-pilot-dev-short
- op-dev-analysis
- op-dev-plan
- op-dev-execute
- op-dev-test-scenario
- test-tool
created: '2026-09-09'
updated: '2026-09-09'
status: draft
---
## 개요

개발 태스크의 판단 문서를 TASK, ANALYSIS, PLAN, TEST-SCENARIO 네 종류로 제한하고 각 문서가 다음 단계에 필요한 정보만 소유하는 계약이다.

## 결정 배경 (WHY)

기존 산출물은 요구·위험·상태·검증 결과를 여러 문서에 반복해 에이전트가 같은 내용을 다시 추론하고 사용자가 현재 유효한 결론을 찾기 어려웠다. 실제 MAMS 태스크를 대입해 요구 보존과 문서 축소를 함께 검토했다. (근거: task:111 PLAN `Decisions and contracts`)

## 결정 내용

- TASK는 문제, 목표 결과, 영향 대상, 제약, 완료 기준을 소유한다.
- ANALYSIS는 확인한 사실, 변경 경계, 중요한 가정, PLAN 인계만 소유한다.
- PLAN은 결정과 계약, 실행 가능한 Work items, 위험, 적용·복구를 소유한다.
- TEST-SCENARIO는 공통 Setup과 관찰 가능한 Scenarios만 소유한다.
- 단계·승인은 `state.json`, 테스트 결과·증거는 `test-scenario.json`이 소유한다.
- 신규 문서는 `template: sdlc-v2`로 판별하고 기존 태스크는 legacy 읽기 경로로 재개한다.

## 영향 범위

개발 pilot, 단계 스킬, state-tool, test-tool, PM 컨텍스트 주입과 프로젝트 문서 선택 계약에 적용된다. 진행 모드와 CLOSE 승인 경계는 유지된다.

## 관련 페이지

- [[skill-opal-pilot-dev]]
- [[skill-opal-pilot-dev-short]]
- [[op-dev-analysis]]
- [[op-dev-plan]]
- [[op-dev-execute]]
- [[op-dev-test-scenario]]
- [[test-tool]]
