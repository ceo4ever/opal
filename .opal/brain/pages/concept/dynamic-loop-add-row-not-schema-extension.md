---
type: concept
title: 동적 반복 구조는 add-row 런타임 규약으로 해결되는 패턴
tags:
- state-tool
- pipeline
- schema
- pattern
- task-086
sources:
- task:086
related:
- pipeline-json-spec
- fw-structure-p0-blueprint
- loop-upper-bound-ssot-pattern
created: '2026-08-09'
updated: '2026-08-09'
status: draft
---
## 개요

동적 반복 구조(태스크마다 행 수가 가변인 액션 루프)는 pipeline.json 정적 스키마를 확장해야만 표현 가능하다고 예상됐으나, 실측 결과 이미 런타임 `add-row` 규약으로 해결되어 있는 패턴이었다.

## 결정 배경 (WHY)

FW 구조개선 P0의 PLAN 단계에서는 oppd Phase 3·opsdd Phase 4의 "액션 N개 자율 루프"가 정적 배열 `task_steps`와 `conditional: boolean` 하나뿐인 현행 스키마로 표현 불가능해 스키마 확장(축 D·E NEEDS-EXT)이 필요할 것으로 예상했다(근거: task:086 `PLAN.md` §2 N-2 "예상 최대 쟁점"). 그러나 A2 실측에서 이 예상은 **기각**되었다 — 동적 루프는 애초에 정적 스키마가 표현할 대상이 아니라, `state-tool add-row`가 STATE.md 런타임에서 행을 추가하는 기존 규약으로 이미 처리되고 있었고, oppl(`:159-163`)·opsdd(`:248`)에서 2회 실증되었다(근거: `A2-스키마소요.md:206`).

## 결정 내용

미보유 6 pilot(oppd/oppl/opwt/opsdd/opgc/opdd) 전건이 현행 pipeline-spec 스키마로 EXPRESSIBLE(확장 불필요)로 판정되었다 — 6축(A~F) 전부 현행 스키마로 표현 가능하며, 하위호환 영향도 없다(근거: `A2-스키마소요.md:247,266`). **일반화된 교훈**: 정적 구조가 반복·가변 행 수를 표현하지 못한다고 확인되면 곧바로 "스키마 확장이 필요하다"로 단정하지 말고, 먼저 런타임 확장 도구(add-row 등)로 이미 해결된 규약이 있는지 실증 사례를 확인해야 한다. 확장 제안이 앞서면 스키마 변경 리스크가 무확장으로도 가능한 작업 전체를 인질로 잡는다(근거: `BLUEPRINT.md` §5.2 근거②).

## 영향 범위

P2(데이터 주도 전환) 1차 범위가 스키마 무확장으로 확정되는 근거가 되었다. `opal/tools/state-tool/state_tool.py`의 `add-row` 서브명령과 `pipeline-spec.schema.json`의 `task_steps.items`(`id`/`key`/`stage`/`item`/`conditional`) 필드 정의는 변경되지 않는다.

## 관련 페이지

- [[fw-structure-p0-blueprint]]
- [[pipeline-json-spec]]
- [[loop-upper-bound-ssot-pattern]]
