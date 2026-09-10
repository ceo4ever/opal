---
type: concept
title: op-sdd-action-plan — SDD 내부 Action Plan 단계 스킬
tags:
- sdd
- action-plan
- skill
- internal
sources:
- skill:op-sdd-action-plan
- task:112
related:
- skill-opal-pilot-sdd
- sdd-internal-stage-skill-ownership
created: '2026-06-11'
updated: '2026-09-10'
status: active
---
## 개념 요약

SDD Action Agent가 ACT PLAN 단계에서 사용하는 내부 단계 스킬이다. Task 112 이후 최상위 공개 스킬이 아니라 `opal-pilot-sdd/internal-skills/op-sdd-action-plan/` 아래에 위치한다.

## 역할·호출 시점·핵심 규칙

- 역할: SDD 액션 실행을 위한 액션 계획 산출물을 작성한다.
- 호출 시점: `opal-sdd-action-agent`의 ACT PLAN 단계.
- 소유 경계: SDD Action Agent와 SDD Pilot 내부 단계 전용. 독립 최상위 skill registry 표면으로 취급하지 않는다.

## 파일 참조

`file_path: opal/skills/opal-pilot-sdd/internal-skills/op-sdd-action-plan/SKILL.md`

## 관련

- [[skill-opal-pilot-sdd]]
- [[sdd-internal-stage-skill-ownership]]
