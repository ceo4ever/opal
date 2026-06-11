---
type: concept
title: opal-pilot-dev-short — Short Task 오케스트레이터
tags:
- skill
- pilot
- orchestrator
- dev-short
sources:
- skill:opal-pilot-dev-short
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

코드 변경이 수반되는 모든 개발 작업의 기본 진입점. Short Task 오케스트레이터로 5단계 파이프라인(TASK → PLAN → EXECUTE → TEST → CLOSE)을 수행한다.

## 배경·문제 (WHY)

대부분의 개발 작업은 ANALYSIS 단계 없이도 PLAN에서 충분히 분석 가능하다. 규모가 커지면 PLAN 단계에서 Full Task(opd) 에스컬레이션을 자동 제안한다.

## 결정 내용 (HOW)

하네스 모드(--interactive/--agentic/--semi-agentic) 지원. state-tool로 단계별 진행 관리. PLAN 단계에서 전문 워커(opal-plan-agent) 디스패치. 코드 개발 전용 — 기획문서/PR리뷰/단순설정은 다른 스킬 사용.

## 영향·관계

opd(Full Task)의 경량 버전. opp(범용 프로젝트)와 구분: opds는 코드 개발 전용. OPAL 파이프라인에서 가장 자주 사용되는 기본 오케스트레이터.

## 관련

- [[op-dev-plan]] — PLAN 단계에서 디스패치하는 설계 워커 스텝
- [[op-dev-execute]] — EXECUTE 단계에서 디스패치하는 코드 실행 워커 스텝
- [[opal-project-definition]] — Short Task 파이프라인의 컨텍스트 로딩 기준 문서

## 근거 출처

file_path: `opal/skills/opal-pilot-dev-short/SKILL.md`
