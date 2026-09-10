---
type: concept
title: op-sdd-plan — SDD 내부 PLAN 단계 스킬
tags:
- sdd
- plan
- skill
- internal
sources:
- skill:op-sdd-plan
- task:112
related:
- skill-opal-pilot-sdd
- sdd-internal-stage-skill-ownership
- op-sdd-spec
created: '2026-06-11'
updated: '2026-09-10'
status: active
---
## 개념 요약

SDD PLAN 단계에서 SPEC을 실행 계획으로 전환하는 내부 단계 스킬이다. Task 112 이후 최상위 공개 스킬이 아니라 `opal-pilot-sdd/internal-skills/op-sdd-plan/` 아래에서 SDD Pilot이 디스패치한다.

## 역할·호출 시점·핵심 규칙

- 역할: SDD 흐름의 PLAN 산출물을 작성한다.
- 호출 시점: `opal-pilot-sdd`의 PLAN 단계 worker dispatch.
- 소유 경계: SDD Pilot 내부 단계 전용. 독립 최상위 skill registry 표면으로 취급하지 않는다.

## 파일 참조

`file_path: opal/skills/opal-pilot-sdd/internal-skills/op-sdd-plan/SKILL.md`

## 관련

- [[skill-opal-pilot-sdd]]
- [[sdd-internal-stage-skill-ownership]]
- [[op-sdd-spec]]
