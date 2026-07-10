---
type: concept
title: DICT가 MODEL을 선행한다 — 사전이 속성명·타입 SSOT
tags: [architecture-decision, data-design, ssot, pipeline]
sources: [task:019]
related: [opdd-pipeline-flow, op-data-dictionary-skill, op-data-model-skill]
created: 2026-06-12
updated: 2026-06-12
status: active
---

## 개요

opdd 파이프라인에서 DICT(표준사전) 단계가 MODEL(데이터 모델링) 단계를 반드시 선행한다. 표준사전이 논리/물리 모델링의 속성명·타입을 결정하는 SSOT이기 때문이다.

## 결정 배경 (WHY)

- 논리 모델의 속성명은 DICT `표준단어사전.md`의 수식어/분류어 약어 조합 규칙을 따른다.
- 물리 모델의 컬럼 타입은 DICT `도메인사전.md`(D001~D022)의 DBMS별 매핑을 따른다.
- DICT 없이 MODEL을 수행하면 속성명·타입 SSOT가 공백 상태가 되어 하류 DDL까지 오염된다.

## 결정 내용

1. opdd STATE에서 DICT(행 3-5)가 MODEL(행 6-8) 앞에 위치한다.
2. DICT 단계는 절대 건너뛰지 않는다 — 기존 사전이 있으면 "검증·보강 모드"로 발동, 부재 시 "신규 작성 모드"로 발동.
3. DDL은 MODEL 물리(DBML) 완료 이후에만 실행 가능 (state-tool stage-transition guard 자동 차단).

## 영향 범위

- `opal/skills/opal-pilot-data-design/SKILL.md` — 파이프라인 순서 강제
- `opal/skills/op-data-model/SKILL.md` — 논리 모드: "속성명 = DICT 표준사전 용어 [MUST]"
- `opal/skills/op-data-ddl/SKILL.md` — "물리(DBML) 산출 이후에만 실행 가능 [MUST]"
- `docs/proposals/opal-data-design.md` §3.2 — 원천 설계 결정

## 관련 페이지

- [[opdd-pipeline-flow.md]]
- [[op-data-dictionary-skill.md]]
- [[op-data-model-skill.md]]
