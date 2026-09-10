---
type: concept
title: op-sdd-spec — SDD 내부 SPEC 단계 스킬
tags:
- sdd
- spec
- skill
- internal
sources:
- skill:op-sdd-spec
- task:112
related:
- skill-opal-pilot-sdd
- sdd-internal-stage-skill-ownership
- op-sdd-plan
created: '2026-06-11'
updated: '2026-09-10'
status: active
---
## 개념 요약

SDD SPEC 단계에서 SPEC.md를 작성하는 내부 단계 스킬이다. Task 112 이후 최상위 공개 스킬이 아니라 `opal-pilot-sdd/internal-skills/op-sdd-spec/` 아래에서 SDD Pilot이 디스패치한다.

## 역할·호출 시점·핵심 규칙

- 역할: TASK.md와 프로젝트 컨텍스트를 분석해 SDD SPEC 산출물을 작성한다.
- 호출 시점: `opal-pilot-sdd`의 SPEC 단계 worker dispatch.
- 소유 경계: SDD Pilot 내부 단계 전용. 독립 최상위 skill registry 표면으로 취급하지 않는다.

## 파일 참조

`file_path: opal/skills/opal-pilot-sdd/internal-skills/op-sdd-spec/SKILL.md`

## 관련

- [[skill-opal-pilot-sdd]]
- [[sdd-internal-stage-skill-ownership]]
- [[op-sdd-plan]]
