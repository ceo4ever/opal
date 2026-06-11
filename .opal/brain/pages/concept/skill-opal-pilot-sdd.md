---
type: concept
title: opal-pilot-sdd — SDD 오케스트레이터
tags:
- skill
- pilot
- orchestrator
- sdd
- spec-driven
sources:
- skill:opal-pilot-sdd
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

SDD(Spec-Driven Development) 오케스트레이터. 명세 기반 개발을 6단계 파이프라인(TASK → SPEC → REVIEW → DESIGN → EXECUTE-LOOP → VERIFY → CLOSE)으로 수행한다.

## 배경·문제 (WHY)

SPEC.md를 SSOT로 삼아 검증 → 설계 → ACT 분해 → 반복 실행 → E2E 검증을 체계적으로 수행해야 복잡한 기능 개발의 품질을 보장할 수 있다. 단일 태스크는 opds/opd를 사용한다.

## 결정 내용 (HOW)

EXECUTE-LOOP에서 opal-sdd-action-agent에 단일 디스패치. 기능 단위로 SPEC.md 작성 → PM 직접 검증 + TEST-SCENARIOS.md 작성 → 아키텍처 설계 + ACT 분해 → 반복 실행. PM이 전체 조율.

## 영향·관계

opal-sdd-action-agent(ACT 실행)에 의존. opd/opds보다 명세 기반의 더 엄격한 파이프라인. oppd(프로젝트 라이프사이클)의 하위 실행 단위로도 사용된다.

## 관련

- [[op-sdd-spec]] — SPEC 단계에서 작성하는 명세 워커 스텝
- [[op-sdd-plan]] — DESIGN 단계에서 ACT를 분해하는 설계 워커 스텝
- [[opal-project-definition]] — SDD 파이프라인의 컨텍스트 로딩 기준 문서

## 근거 출처

file_path: `opal/skills/opal-pilot-sdd/SKILL.md`
