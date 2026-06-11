---
type: concept
title: opal-pilot-project — 프로젝트 범용 오케스트레이터
tags:
- skill
- pilot
- orchestrator
- project
sources:
- skill:opal-pilot-project
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

프로젝트 범용 오케스트레이터. 문서 작성·간단한 코드 수정·설정 변경·워크플로우 수행 등 모든 범용 태스크를 4단계 파이프라인(TASK → PLAN → EXECUTE → CLOSE)으로 수행한다.

## 배경·문제 (WHY)

코드 개발(opds) 또는 기획 산출물 세트(opwt) 외의 범용 프로젝트 작업을 처리할 표준 오케스트레이터가 필요하다. 코드 개발 전용은 opds, 기획 산출물은 opwt를 사용한다.

## 결정 내용 (HOW)

TASK → PLAN → EXECUTE → CLOSE 4단계. 하네스 모드(--interactive/--agentic/--semi-agentic) 지원. state-tool로 단계 진행 관리. 코드 개발이 아닌 모든 범용 작업의 기본 진입점.

## 영향·관계

opds(코드 개발)·opwt(기획 산출물)·oppd(프로젝트 라이프사이클)와 상호 보완적으로 사용된다.

## 관련

- [[op-task-plan]] — PLAN 단계에서 참조하는 범용 태스크 계획 워커 스텝
- [[op-task-execute]] — EXECUTE 단계에서 범용 태스크를 실행하는 워커 스텝
- [[opal-project-definition]] — 범용 오케스트레이터의 컨텍스트 로딩 기준 문서

## 근거 출처

file_path: `opal/skills/opal-pilot-project/SKILL.md`
