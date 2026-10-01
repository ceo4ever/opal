---
type: concept
title: opal-pilot-dev — Full/Short 개발 오케스트레이터
tags:
- skill
- pilot
- orchestrator
- dev
- opd
- opds
sources:
- skill:opal-pilot-dev
- task:111
- task:112
- task:170
related: [dev-pilot-profile-unification, sdlc-v2-development-artifact-contract, skill-opal-pilot-dev-short, op-dev-analysis, op-dev-plan, op-dev-test-scenario, design-gate-deterministic-pretier-separation]
created: '2026-06-11'
updated: '2026-10-01'
status: active
---
## 개요

개발 작업을 수행하는 canonical 오케스트레이터다. Task 112 이후 이 스킬은 Full Task(`//opd`)와 Short Task(`//opds`)를 모두 소유하며, 호출 name/alias와 profile 선택 규칙에 따라 서로 다른 pipeline을 초기화한다.

## 현재 계약

- Full profile은 TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST → CLOSE 흐름과 16행 상태 계약을 유지한다.
- Short profile은 TASK → PLAN → EXECUTE → TEST → CLOSE 흐름과 11행 상태 계약을 유지하며, pipeline 정의는 canonical 폴더의 `pipeline-short.json`에 둔다.
- `opds` logical entry와 alias는 유지하지만 물리 `opal-pilot-dev-short` 구현 폴더는 제거한다.
- 신규 태스크는 [[sdlc-v2-development-artifact-contract]]를 사용한다.
- PLAN `Work items`의 담당·파일 소유권·선행 관계·실행 그룹을 기준으로 구현을 순차 또는 병렬 디스패치한다.
- interactive, semi-agentic, agentic의 사용자 확인과 CLOSE 경계는 기존 계약을 유지한다.
- **설계 게이트 PM 경로 사전검사(task:170)**: §PM 경로(actor=coordinator 신규) 절차는 PLAN 작성 완료 후 `design-gate start` 호출 전에 `state-tool verify --design-gate-check`를 실행해 `deterministic_missing`을 해소하고 `decision_clarity_candidates`를 자가점검하도록 요구한다. PLAN이 새 가드·명령·상태·오류 코드 등 새 검증 대상을 추가/변경했으면 같은 회차 안에서 TEST-SCENARIO.md도 갱신해야 한다(상세: [[design-gate-deterministic-pretier-separation]]).

## 라우팅 계약

Full→Short 강등은 TASK 직후 1회 판단한다. Short→Full 승격은 PLAN 결과 수신 직후 1회 판단한다. 두 판정은 서로 다른 시점과 서로 다른 profile 경계를 사용해 왕복 재귀를 막는다.

## 근거

`opal/skills/opal-pilot-dev/SKILL.md`, `opal/skills/opal-pilot-dev/references/pipeline.json`, `opal/skills/opal-pilot-dev/references/pipeline-short.json`, `opal/skills/opal-pilot-dev/references/track-escalation.md`, task:111, task:112, task:170.

## 관련 페이지

- [[dev-pilot-profile-unification]]
- [[sdlc-v2-development-artifact-contract]]
- [[skill-opal-pilot-dev-short]]
- [[op-dev-analysis]]
- [[op-dev-plan]]
- [[op-dev-test-scenario]]
- [[design-gate-deterministic-pretier-separation]]
