---
type: concept
title: 단계 내부 모드는 STATE 행이 아니다
tags:
- pipeline
- state-tool
- mode
- skip
- task-104
sources:
- task:104
related:
- state-tool-task-step-key-address
- phase-name-stage-value-homonym-boundary
- opdd-pipeline-flow
created: '2026-08-30'
updated: '2026-08-30'
status: draft
---
## 개요

파이프라인 단계(STATE 행) 내부에 여러 「모드」가 순차 실행되는 구조에서, 특정 모드를 건너뛰는 개정은 STATE 행을 삭제하는 것이 아니라 그 단계 디스패치 프롬프트의 실행 순서 문언을 분기하는 것으로 구현된다.

## 결정 배경 (WHY)

- (근거: task:104 TASK A-1·A-2, PLAN §2.3) opdd의 개념→논리→물리 3모드는 `pipeline.json`의 `task_steps[]`에서 `model.modeling` **1개 행**으로만 존재한다. 3모드 순차 실행 자체는 STATE 행이 아니라 STEP 3 디스패치 프롬프트의 `**실행 순서**` 줄이 산문으로 지시하는 것이었다.
- (근거: task:104 DONE §3.3) 따라서 「개념모델링을 스킵한다」는 요구는 행을 지우는 문제가 아니라, 그 산문 줄이 트랙에 따라 다른 문자열을 반환하도록 분기하는 문제였다. 행을 건드릴 이유가 아예 없었다.

## 결정 내용

- 모드 스킵·순서 변경 요구가 들어오면 먼저 그 모드가 STATE 행으로 존재하는지, 아니면 한 행 내부의 실행 순서 문언인지부터 확인한다. 후자라면 `pipeline.json`의 `task_steps[]` 행 수·key는 절대 건드리지 않는다.
- 행 수·key 불변은 `state-tool`이 key로 행을 주소지정하는 계약의 전제이며, 기존에 이미 진행 중인 태스크의 `state.json`과의 호환을 위해서도 반드시 지켜야 한다.
- 실제 분기는 디스패치 프롬프트에 트랙(또는 조건)별 실행 순서 문자열을 나란히 적는 방식으로 구현한다 — 조건이 없을 때는 기존 문구가 그대로 남아 회귀 0을 보장한다.

## 영향 범위

- STATE 행 1개 안에서 여러 하위 모드·서브스텝을 순차 실행하는 모든 파이프라인 설계(예: opdd MODEL의 개념/논리/물리). 이런 구조에서 모드 단위 개정 요구를 받으면 STATE 스키마 변경으로 오인하지 않는다.
- `state-tool init --rows-from` 등 `task_steps[]` 행 수·key에 의존하는 하위 도구의 하위호환도 함께 보존된다.

## 관련 페이지

- [[state-tool-task-step-key-address]]
- [[phase-name-stage-value-homonym-boundary]]
- [[opdd-pipeline-flow]]
