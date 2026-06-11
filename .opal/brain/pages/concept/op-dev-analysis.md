---
type: concept
title: op-dev-analysis — 코드베이스 분석 및 기술 컨텍스트 수집
tags:
- dev
- analysis
- skill
sources:
- skill:op-dev-analysis
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

TASK.md를 기반으로 기존 코드를 분석하고 기술 스택을 식별하여 추천 스킬/MCP를 매핑하는 ANALYSIS 단계 스킬.

## 역할·호출 시점·핵심 규칙

- **역할**: 코드베이스 분석 및 기술 컨텍스트 수집; 결과물 ANALYSIS.md 생성
- **호출 시점**: 오케스트레이터(opal-pilot-dev)가 ANALYSIS 단계를 디스패치할 때
- **핵심 규칙**: 필수 입력 TASK.md; 출력 ANALYSIS.md; citation-rules.md 준수 필수; 워커 에이전트 실행(폴백: opal-task-agent)

## 파일 참조

`file_path: opal/skills/op-dev-analysis/SKILL.md`

## 관련

- [[skill-opal-pilot-dev]] — 이 스킬을 ANALYSIS 단계에서 디스패치하는 Dev 오케스트레이터
- [[op-dev-plan]] — ANALYSIS.md를 입력으로 받아 구현 계획을 수립하는 다음 단계 스킬
