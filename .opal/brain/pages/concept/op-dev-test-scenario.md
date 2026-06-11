---
type: concept
title: op-dev-test-scenario — 테스트 시나리오 작성 단계 스킬
tags:
- dev
- test
- skill
sources:
- skill:op-dev-test-scenario
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

PLAN.md 리스크 가설 표를 기반으로 데이터 설계·L1/L2/L3 계층 시나리오·4열 매핑 표를 작성하는 TEST-SCENARIO 단계 스킬.

## 역할·호출 시점·핵심 규칙

- **역할**: TEST-SCENARIO.md 생성; 리스크 가설 표 기반 L1(단위)·L2(통합)·L3(E2E) 계층 시나리오 설계
- **호출 시점**: 오케스트레이터(opal-pilot-dev) STEP 3.5에서 PM(알투+캡틴 페어)이 직접 수행 — 워커 디스패치 없음
- **핵심 규칙**: 필수 입력 TASK.md + PLAN.md(리스크 가설 표); PLAN 워커와 다른 작성자가 수행(self-confirming 방지)

## 파일 참조

`file_path: opal/skills/op-dev-test-scenario/SKILL.md`

## 관련

- [[skill-opal-pilot-dev]] — 이 스킬을 STEP 3.5에서 PM이 직접 수행하도록 지시하는 Dev 오케스트레이터
- [[op-dev-plan]] — 리스크 가설 표를 포함하는 PLAN.md를 생성하는 선행 단계 스킬
