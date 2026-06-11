---
type: concept
title: op-sdd-spec — SDD 명세 작성 단계 스킬
tags:
- sdd
- spec
- skill
sources:
- skill:op-sdd-spec
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

TASK.md와 프로젝트 컨텍스트를 분석하여 10섹션 표준 구조의 SPEC.md를 작성하는 SDD SPEC 단계 스킬.

## 역할·호출 시점·핵심 규칙

- **역할**: SPEC.md 생성 — 10섹션 표준 구조(목적·배경·기능 요구사항·비기능 요구사항·데이터·인터페이스·제약·리스크·테스트 전략·부록)
- **호출 시점**: 오케스트레이터(opal-pilot-sdd)가 SPEC 단계를 디스패치할 때; 실행 주체 opal-task-agent, model advanced
- **핵심 규칙**: 필수 입력 TASK.md; 선택 입력 docs/PROJECT.md, docs/ARCHITECTURE.md, 코드베이스

## 파일 참조

`file_path: opal/skills/op-sdd-spec/SKILL.md`

## 관련

- [[skill-opal-pilot-sdd]] — 이 스킬을 SPEC 단계에서 디스패치하는 SDD 오케스트레이터
- [[op-sdd-verify]] — 이 스킬의 산출물(SPEC.md)을 검증하는 후속 단계 스킬
