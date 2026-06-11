---
type: concept
title: op-task-qa — 범용 문서 QA 검증 기준
tags:
- skill
- qa
- document
sources:
- skill:op-task-qa
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

범용 문서 QA 검증 기준 라이브러리. PM Gate가 TASK.md·PLAN.md 등 산출물을 직접 검증할 때 참조하는 스킬이다.

## 배경·문제 (WHY)

코드 개발 외의 범용 산출물(기획·설계 문서)에 대한 QA 기준을 별도로 표준화할 필요가 있었다. 별도 QA Gate 에이전트 없이 PM Gate가 직접 이 기준을 참조하는 구조다.

## 결정 내용 (HOW)

PM Gate 문서검증 시점에 참조. 검증 대상 입력은 산출물 경로 + 단계명(TASK/PLAN/EXECUTE). 산출물 형식: `QA-{단계}.md`. 코드 개발 QA는 op-dev-qa, 범용 문서 QA는 이 스킬을 사용한다.

## 영향·관계

op-dev-qa(코드 개발 전용 QA)와 상호 보완적으로 사용. 모든 pilot 오케스트레이터의 PM Gate 단계에서 참조된다.

## 관련

- [[op-dev-qa]] — 코드 개발 전용 QA 스킬로, 이 스킬과 상호 보완 관계
- [[opal-project-definition]] — PM Gate가 참조하는 프레임워크 전체 정의
- [[op-task-plan]] — PM Gate 검증 대상 산출물의 PLAN 단계 스킬

## 근거 출처

file_path: `opal/skills/op-task-qa/SKILL.md`
