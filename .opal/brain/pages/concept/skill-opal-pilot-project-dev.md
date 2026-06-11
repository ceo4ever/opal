---
type: concept
title: opal-pilot-project-dev — 프로젝트 개발 라이프사이클 오케스트레이터
tags:
- skill
- pilot
- orchestrator
- project-dev
- lifecycle
sources:
- skill:opal-pilot-project-dev
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

프로젝트 개발 라이프사이클 오케스트레이터. 아이디어부터 개발 완료까지 3 Phase 파이프라인(PLAN → WBS → EXECUTE)으로 관리한다. opwt로 기획 산출물 작성, opal-task-action-agent로 액션 자율 실행.

## 배경·문제 (WHY)

아이디어에서 제품까지 전체 라이프사이클을 일관된 파이프라인으로 관리할 오케스트레이터가 필요하다. PM이 기획·코드 실행을 각 전문 스킬/에이전트에 위임하고 조율한다.

## 결정 내용 (HOW)

Phase 1: opwt로 PRD/TRD 작성 → Phase 2: WBS 수립 → Phase 3: opal-task-action-agent로 액션 자율 실행. PM 검수 → 사용자 확정 순서 강제. STATE.md 기반 세션 독립 재개.

## 영향·관계

opwt(기획 산출물), opal-task-action-agent(코드 실행), opp(범용)와 연계. opi(opal-project-init) 없이도 docs/PROJECT.md 존재 시 단독 호출 가능.

## 관련

- [[skill-opal-pilot-write-tech]] — Phase 1에서 위임받아 기획 산출물(PRD/TRD)을 작성하는 스킬
- [[skill-opal-project-init]] — 라이프사이클 오케스트레이터 실행 전 선행 조건인 환경 초기화 스킬
- [[opal-project-definition]] — 전체 라이프사이클 관리의 컨텍스트 로딩 기준 문서

## 근거 출처

file_path: `opal/skills/opal-pilot-project-dev/SKILL.md`
