---
type: concept
title: opal-pilot-dev-short — opds logical Short profile
tags:
- skill
- pilot
- orchestrator
- dev-short
- opds
- compatibility
sources:
- skill:opal-pilot-dev-short
- task:111
- task:112
related:
- dev-pilot-profile-unification
- skill-opal-pilot-dev
- sdlc-v2-development-artifact-contract
- op-dev-plan
- op-dev-test-scenario
created: '2026-06-11'
updated: '2026-09-10'
status: active
---
## 개요

Short 개발 표면은 계속 존재하지만, 더 이상 독립 물리 오케스트레이터가 아니다. Task 112 이후 `opal-pilot-dev-short`는 registry의 logical entry와 `opds` alias로 남고, 실제 실행은 canonical [[skill-opal-pilot-dev]]의 Short profile이 맡는다.

## 현재 계약

- 사용자 호출 `//opds`는 유지한다.
- state-tool 식별자 `skill=opds`와 기존 11개 pipeline 행은 유지한다.
- Short pipeline 파일은 `opal/skills/opal-pilot-dev/references/pipeline-short.json`로 이동한다.
- PLAN 이후 범위가 커졌다고 판단되면 Full profile로 승격을 제안하거나 전환한다.
- 물리 `opal/skills/opal-pilot-dev-short/` 폴더는 제거 대상이며 설치본에도 재생성되지 않아야 한다.

## 근거

`opal/core/references/opal-skills-registry.json`, `opal/skills/opal-pilot-dev/SKILL.md`, `opal/skills/opal-pilot-dev/references/pipeline-short.json`, task:112.

## 관련 페이지

- [[dev-pilot-profile-unification]]
- [[skill-opal-pilot-dev]]
- [[sdlc-v2-development-artifact-contract]]
- [[op-dev-plan]]
- [[op-dev-test-scenario]]
