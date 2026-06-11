---
type: concept
title: OPAL Coding Principles SSOT 신설
tags:
- framework
- principles
- ssot
- task
sources:
- task:001
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

카파시 행동 원칙을 흡수하여 `opal/core/references/harness/coding-principles.md`를 영구 SSOT로 신설하고, 워커 3종(FE/BE/Task 에이전트)이 EXECUTE 진입 시 자가 로드하도록 의무화했다.

## 배경·문제 (WHY)

코딩 원칙이 분산 표현되어 워커가 일관되게 참조하지 못했다. 외부 출처(카파시 CLAUDE.md) 의존도를 제거하고 OPAL 자립 SSOT로 내재화할 필요가 있었다.

## 결정 내용 (HOW)

- `coding-principles.md` 영문 신규 작성 (6섹션, Rarity Matrix 포함), 외부 출처 표현 제거(M: AW-1).
- FE 에이전트: wireframe/execute 진입 시 §4 Read 의무. BE·Task 에이전트: execute 진입 시 §4 Read 의무(M-3 도메인별 차별화).
- `opal-harness.md` §10 신설로 하네스 공식 등재; `op-task/SKILL.md` AC 가이드에 영문 인용 + Bad/Good 예시 추가.

## 영향·관계

- 적용 범위: `opal-fe-agent`, `opal-be-agent`, `opal-task-agent`, `op-task/SKILL.md`, `op-dev-test-scenario/SKILL.md`.
- [[opal-conventions]] 과 상호 보완(컨벤션 = 구조 규칙, coding-principles = 행동 원칙).

## 근거 출처

`sources: task:001` — DONE.md §2 M-1~AW-1 참조.
