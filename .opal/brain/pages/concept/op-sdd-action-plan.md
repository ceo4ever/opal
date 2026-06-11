---
type: concept
title: op-sdd-action-plan — SDD ACT 전용 경량 PLAN 스킬
tags:
- sdd
- plan
- skill
sources:
- skill:op-sdd-action-plan
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

SPEC.md + SPEC-PLAN.md + TEST-SCENARIOS.md + ACT 정의를 기반으로 ACT 범위의 실행 가능한 구현 청사진을 작성하는 SDD ACT 전용 경량 PLAN 스킬.

## 역할·호출 시점·핵심 규칙

- **역할**: ACT 범위 PLAN.md 생성; plan-guide.md / personas / community-skills 로딩 없음 — SDD 컨텍스트로 대체
- **호출 시점**: opal-sdd-action-agent가 ACT PLAN 단계를 디스패치할 때
- **핵심 규칙**: 필수 입력 SPEC.md, SPEC-PLAN.md, TEST-SCENARIOS.md, ACT 정의; citation-rules.md 준수 필수

## 파일 참조

`file_path: opal/skills/op-sdd-action-plan/SKILL.md`

## 관련

- [[skill-opal-pilot-sdd]] — 이 스킬이 속한 SDD 파이프라인을 관장하는 오케스트레이터
- [[op-sdd-plan]] — SPEC-PLAN.md(ACT 분해 포함)를 생성하는 선행 단계 스킬
