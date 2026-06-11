---
type: concept
title: op-task-plan — 범용 계획 수립 단계 스킬
tags:
- task
- plan
- skill
sources:
- skill:op-task-plan
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

TASK.md를 분석하여 도메인 무관 실행 계획(PLAN.md)을 작성하는 범용 계획 수립 스킬. op-dev-plan의 도메인 무관 버전이다.

## 역할·호출 시점·핵심 규칙

- **역할**: PLAN.md(현황 조사 + 실행 체크리스트) 생성; 언어/프레임워크 특화 없이 범용 계획 작성
- **호출 시점**: 오케스트레이터(opal-pilot-project)가 PLAN 단계를 디스패치할 때
- **핵심 규칙**: 필수 입력 TASK.md; citation-rules.md 준수 필수; 워커 에이전트 실행(폴백: PM 직접)

## 파일 참조

`file_path: opal/skills/op-task-plan/SKILL.md`

## 관련

- [[skill-opal-pilot-project]] — 이 스킬을 PLAN 단계에서 디스패치하는 Project 오케스트레이터
- [[op-task]] — 이 스킬의 필수 입력물(TASK.md)을 생성하는 선행 단계 스킬
- [[op-task-execute]] — 이 스킬의 산출물(PLAN.md)을 입력으로 받아 실행하는 후속 단계 스킬
