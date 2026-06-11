---
type: concept
title: op-task — TASK.md 작성 단계 스킬
tags:
- task
- skill
sources:
- skill:op-task
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

사용자 요청을 구조화된 TASK.md로 정리하고 모호한 요구사항을 명확화하며 작업 유형·기술 스택을 사전 판별하는 TASK 단계 스킬.

## 역할·호출 시점·핵심 규칙

- **역할**: TASK.md 작성; 사용자와 대화하며 요구사항 확인; 오케스트레이터가 직접 수행(서브에이전트 생성 없음)
- **호출 시점**: 오케스트레이터(opal-pilot-dev, opal-pilot-dev-short, opal-pilot-dev-wireframe)가 TASK 단계를 디스패치할 때
- **핵심 규칙**: 필수 입력 사용자 요청 텍스트; citation-rules.md 준수 필수; 페르소나 personas/service-planner.md 로드

## 파일 참조

`file_path: opal/skills/op-task/SKILL.md`

## 관련

- [[skill-opal-pilot-project]] — 이 스킬을 TASK 단계에서 디스패치하는 Project 오케스트레이터
- [[op-task-plan]] — 이 스킬의 산출물(TASK.md)을 입력으로 받아 계획을 수립하는 후속 단계 스킬
