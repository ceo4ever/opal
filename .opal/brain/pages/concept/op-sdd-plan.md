---
type: concept
title: op-sdd-plan — SDD 아키텍처 설계 + ACT 분해 스킬
tags:
- sdd
- plan
- skill
sources:
- skill:op-sdd-plan
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

SPEC.md + TEST-SCENARIOS.md를 기반으로 기능 수준의 아키텍처 설계와 ACT 분해(SPEC-PLAN.md)를 작성하는 SDD DESIGN Phase 스킬.

## 역할·호출 시점·핵심 규칙

- **역할**: SPEC-PLAN.md 생성 — 아키텍처 설계 + ACT 분해 + 병렬/순서 의존관계 통합; 실행 에이전트 opal-task-agent, model advanced
- **호출 시점**: 오케스트레이터(opal-pilot-sdd)가 DESIGN Phase를 디스패치할 때
- **핵심 규칙**: 필수 입력 SPEC.md, TEST-SCENARIOS.md; citation-rules.md 준수 필수

## 파일 참조

`file_path: opal/skills/op-sdd-plan/SKILL.md`

## 관련

- [[skill-opal-pilot-sdd]] — 이 스킬을 DESIGN Phase에서 디스패치하는 SDD 오케스트레이터
- [[op-sdd-spec]] — SPEC.md를 생성하는 선행 단계 스킬
- [[op-sdd-action-plan]] — 이 스킬의 산출물(SPEC-PLAN.md)을 입력으로 받는 ACT 전용 PLAN 스킬
