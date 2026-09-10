---
type: concept
title: SDD 내부 단계 스킬 소유권
tags:
- sdd
- skill
- pilot
- ownership
sources:
- task:112
related:
- skill-opal-pilot-sdd
- op-sdd-spec
- op-sdd-plan
- op-sdd-action-plan
- op-sdd-verify
created: '2026-09-10'
updated: '2026-09-10'
status: draft
---
## 개요

SDD 단계 전용 스킬은 최상위 공개 스킬이 아니라 `opal-pilot-sdd`가 소유하는 내부 단계 자산으로 둔다. Task 112는 active 단계 3종을 `opal-pilot-sdd/internal-skills/`로 이동하고, 오래된 `op-sdd-verify` 물리 스킬은 제거하면서 현행 REVIEW 검증 계약을 `verify-guide.md`에 유지했다.

## 결정 배경 (WHY)

`op-sdd-spec`, `op-sdd-plan`, `op-sdd-action-plan`은 실제 소비자가 SDD Pilot 또는 SDD Action Agent로 한정되어 있었다. 최상위 스킬처럼 배포하면 사용 표면이 실제 소유 경계보다 넓어지고, `op-sdd-verify`처럼 더 이상 직접 호출되지 않는 단계 계약이 살아 있는 것처럼 보이는 문제가 생긴다.

## 결정 내용

- SPEC, PLAN, ACTION PLAN 단계 스킬 3종은 `opal/skills/opal-pilot-sdd/internal-skills/` 아래에 둔다.
- SDD Pilot과 SDD Action Agent의 worker prompt는 내부 경로를 직접 가리킨다.
- `op-sdd-verify` 물리 스킬은 제거한다.
- REVIEW의 S-1~S-6 검증 규칙은 `opal/skills/opal-pilot-sdd/references/verify-guide.md`가 계속 소유한다.
- 설치·archive·cleanup 검증은 제거된 top-level 폴더가 전역 설치본에 재생성되지 않는지 확인한다.

## 영향 범위

- `opal/skills/opal-pilot-sdd/SKILL.md`
- `opal/skills/opal-pilot-sdd/internal-skills/`
- `opal/skills/opal-pilot-sdd/references/verify-guide.md`
- `opal/agents/opal-sdd-action-agent/AGENT.md`
- `opal/core/references/opal-skills-registry.json`
- 설치 cleanup 및 archive/download 계약 테스트

## 관련 페이지

- [[skill-opal-pilot-sdd]]
- [[op-sdd-spec]]
- [[op-sdd-plan]]
- [[op-sdd-action-plan]]
- [[op-sdd-verify]]
