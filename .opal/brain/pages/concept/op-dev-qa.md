---
type: concept
title: op-dev-qa — Dev 문서 QA 검증 기준 라이브러리
tags:
- dev
- qa
- skill
sources:
- skill:op-dev-qa
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

PM Gate 문서검증 시 참조하는 Dev 문서 QA 검증 기준 라이브러리. 별도 QA 에이전트 디스패치 없이 PM이 직접 참조하여 검증한다.

## 역할·호출 시점·핵심 규칙

- **역할**: 문서 QA(요구사항→설계 검토) 검증 기준 제공; 공통 검증 원칙·단계별 검증 ID·QA-{단계}.md 형식 규정
- **호출 시점**: PM Gate 문서검증 시 참조; 단계에 따라 qa-dev-guide 또는 qa-wireframe-guide를 참조
- **핵심 규칙**: 동작 검증(TEST/TEST-SCENARIO/verify)과 무관한 문서 QA 전용; 별도 워커 디스패치 없음; 검증 산출물은 QA-{단계}.md

## 파일 참조

`file_path: opal/skills/op-dev-qa/SKILL.md`

## 관련

- [[skill-opal-pilot-dev]] — 이 QA 기준 라이브러리를 PM Gate 검증에서 참조하는 Dev 오케스트레이터
- [[op-dev-plan]] — 이 스킬이 검증 대상으로 삼는 PLAN.md를 생성하는 단계 스킬
