---
type: concept
title: 관측 필드는 기록 시점에 설계돼야 사후 실측 가능 — state.json 워커 식별 부재 교훈
tags:
- observability
- state-tool
- lesson-learned
- task-086
sources:
- task:086
related:
- fw-structure-p0-blueprint
- observability-3layer-protocol-renderer-trigger-separation
- state-tool
created: '2026-08-09'
updated: '2026-08-09'
status: draft
---
## 개요

관측 데이터(디스패치 횟수 등)는 발생 시점에 기록되도록 미리 설계되지 않으면, 나중에 아무리 정교한 방법으로도 직접 실측할 수 없다.

## 결정 배경 (WHY)

FW 구조개선 P0에서 태스크당 디스패치 수(K4)를 실측하려 했으나, `tasks/*/state.json`의 `owner` 필드 값이 `PM`/`auto`/`user` 3종뿐이고 STATE.md 파이프라인 표에도 디스패치 주체·횟수 컬럼이 없어, 실제로 어떤 워커 에이전트가 몇 번 스폰되었는지 원천 데이터에서 직접 집계할 수 없었다(근거: `A3-스폰실측.md` §1, task:086 `PLAN.md` §1 S-3). 이 때문에 K4는 대리 지표 3계층(L1 정적 하한/L2 실행 하한/L3 관측 보정)으로 재구성해야 했고, 그중 L3는 근거 없이 `[E]`(추정)로만 표기할 수밖에 없었다(근거: `A3-스폰실측.md:279-287`).

## 결정 내용

관측 필드 부재는 사후에 분석 기법으로 보완할 수 있는 문제가 아니라 **기록 시점의 설계 문제**다 — 도구(state-tool 등)의 SSOT 스키마에 관측하고자 하는 값(예: 실제 디스패치된 agent 이름 + 시도 회차)을 선제적으로 필드로 넣어두어야, 이후 태스크에서 실측이 가능해진다. 본 태스크는 이 관측성 갭을 스키마 변경 없이 대리 지표로만 우회했고, `state.json`/`task_steps` 확장 자체는 범위 밖으로 명시하고 후속 태스크 후보(B-1)로 등재했다(근거: `BLUEPRINT.md` §6.2 B-1, `A3-스폰실측.md:175`).

## 영향 범위

`opal/tools/state-tool/`의 `state.json` 스키마에 워커 식별 필드(디스패치된 agent 이름·시도 회차)를 추가하는 후속 설계 판단이 필요하며, 이는 P1~P3 완료기준에는 포함되지 않고 별도 후속 태스크 후보로만 남아 있다.

## 관련 페이지

- [[fw-structure-p0-blueprint]]
- [[observability-3layer-protocol-renderer-trigger-separation]]
- [[state-tool]]
