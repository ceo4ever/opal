---
type: concept
title: op-sdd-verify — SDD 명세/태스크 검증 단계 스킬
tags:
- sdd
- verify
- skill
sources:
- skill:op-sdd-verify
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

mode에 따라 SPEC.md 또는 TASKS.md를 검증하고 VERIFY.md 저널에 결과를 누적 기록하는 SDD 검증 단계 스킬.

## 역할·호출 시점·핵심 규칙

- **역할**: VERIFY.md(해당 섹션 추가) 생성; mode=spec 시 TEST-SCENARIOS.md도 생성
- **호출 시점**: opsdd 오케스트레이터가 SPEC-VERIFY(Phase 2) 또는 TASKS-VERIFY(Phase 5) Phase를 디스패치할 때; 실행 주체 opal-task-agent
- **핵심 규칙**: 필수 입력 mode + spec_path; mode는 `spec` 또는 `tasks` 중 하나

## 파일 참조

`file_path: opal/skills/op-sdd-verify/SKILL.md`

## 관련

- [[skill-opal-pilot-sdd]] — 이 스킬을 SPEC-VERIFY 및 TASKS-VERIFY Phase에서 디스패치하는 SDD 오케스트레이터
- [[op-sdd-spec]] — SPEC.md를 생성하는 선행 단계 스킬(mode=spec 검증 대상)
