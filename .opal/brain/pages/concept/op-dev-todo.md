---
type: concept
title: op-dev-todo — 실행 체크리스트 확장 단계 스킬
tags:
- dev
- todo
- skill
sources:
- skill:op-dev-todo
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

Full Task 전용으로 PLAN.md 구현 계획을 파일 단위 작업으로 상세 분해하고 QA 체크리스트·복잡도 판별을 수행하는 TODO 단계 스킬.

## 역할·호출 시점·핵심 규칙

- **역할**: TODO.md(Part A 실행 체크리스트 + Part B QA 체크리스트 + Part C 복잡도 판별) 생성
- **호출 시점**: 오케스트레이터(opal-pilot-dev)가 TODO 단계를 디스패치할 때 — Full Task 전용(Short Task 불가)
- **핵심 규칙**: 필수 입력 PLAN.md; ANALYSIS.md 선택 입력; Short Task에서는 실행 체크리스트가 PLAN.md에 통합됨

## 파일 참조

`file_path: opal/skills/op-dev-todo/SKILL.md`

## 관련

- [[skill-opal-pilot-dev]] — 이 스킬을 Full Task TODO 단계에서 디스패치하는 Dev 오케스트레이터
- [[op-dev-plan]] — 이 스킬의 필수 입력물(PLAN.md)을 생성하는 선행 단계 스킬
