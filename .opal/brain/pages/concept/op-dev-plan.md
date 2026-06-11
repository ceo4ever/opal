---
type: concept
title: op-dev-plan — 구현 계획 수립 단계 스킬
tags:
- dev
- plan
- skill
sources:
- skill:op-dev-plan
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

TASK.md + ANALYSIS.md(선택)를 기반으로 탑다운 기능 중심 구조의 실행 가능한 구현 청사진(PLAN.md)을 작성하는 PLAN 단계 스킬.

## 역할·호출 시점·핵심 규칙

- **역할**: 기능(F-NNN) 단위 분석·설계·QA 추적; Flat/Multi-Feature 모드 자동 선택; 실행 체크리스트·복잡도 판별·기능-QA 매트릭스·리스크 가설 표 포함 PLAN.md 생성
- **호출 시점**: 오케스트레이터(opal-pilot-dev, opal-pilot-dev-short)가 PLAN 단계를 디스패치할 때
- **핵심 규칙**: 필수 입력 TASK.md; ANALYSIS.md 유무에 따라 분석 깊이 자동 조절; TEST-SCENARIO.md는 PM이 별도 작성(STEP 3.5)

## 파일 참조

`file_path: opal/skills/op-dev-plan/SKILL.md`

## 관련

- [[skill-opal-pilot-dev]] — 이 스킬을 PLAN 단계에서 디스패치하는 Dev 오케스트레이터
- [[op-dev-analysis]] — PLAN 입력물(ANALYSIS.md)을 생성하는 선행 단계 스킬
- [[op-dev-todo]] — PLAN.md를 기반으로 파일 단위 체크리스트를 상세 분해하는 후속 단계 스킬
