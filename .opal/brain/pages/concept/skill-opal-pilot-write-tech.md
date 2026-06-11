---
type: concept
title: opal-pilot-write-tech — 서비스 기획 산출물 오케스트레이터
tags:
- skill
- pilot
- orchestrator
- write-tech
- documentation
sources:
- skill:opal-pilot-write-tech
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

서비스 기획 산출물 네트워크 오케스트레이터. 기술 산출물(PRD, TRD, 서비스 정책서, IA 등)을 논리적 네트워크로 관리하며, PM이 워커를 병렬 디스패치하여 문서 간 일관성을 보장한다.

## 배경·문제 (WHY)

기획 산출물은 상호 의존 관계가 있어 단순 문서 작성이 아닌 교차 논리 검토와 정합성 검증이 필요하다. 문서가 인터페이스 원칙으로 프로젝트 docs/만 참조하고 다른 스킬 존재를 모른다.

## 결정 내용 (HOW)

필수 4종(PRD/TRD/정책서/IA) + 선택 5종. 순서 체인: PRD → TRD → 서비스 정책서 → IA. 독립 문서는 병렬 작성, 의존 문서는 순차. opal-planning-agent 워커 디스패치.

## 영향·관계

oppd(프로젝트 라이프사이클)의 Phase 1에서 위임받아 실행. opal-planning-agent 워커에 의존한다.

## 관련

- [[opwt-v4-output-system]] — 이 스킬의 산출물 네트워크 출력 시스템 설계 문서
- [[opal-project-definition]] — 기획 산출물 작성 시 참조하는 프로젝트 컨텍스트 기준 문서
- [[skill-opal-pilot-project-dev]] — 이 스킬을 Phase 1에서 위임하는 상위 라이프사이클 오케스트레이터

## 근거 출처

file_path: `opal/skills/opal-pilot-write-tech/SKILL.md`
