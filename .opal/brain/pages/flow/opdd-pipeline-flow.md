---
type: flow
title: opdd 파이프라인 흐름 — DB 설계 표준 3층 파이프라인
tags: [pipeline, data-design, flow, opdd, db]
sources: [task:019]
related: [skill-opal-pilot-data-design, op-data-dictionary-skill, op-data-model-skill, op-data-ddl-skill, dict-선행-model-ssot]
created: 2026-06-12
updated: 2026-06-12
status: active
---

## 개요

`opal-pilot-data-design(opdd)` 파이프라인의 전체 흐름. DB 설계 업무를 OPAL 표준 3층 체계(pilot + 단계 스킬 + 에이전트)로 구현한다.

## 파이프라인 흐름

```
TASK (PM 직접)
  ↓
DICT (op-data-dictionary)          ← 사전이 MODEL의 속성명·타입 SSOT
  ↓
MODEL (op-data-model)
  ↓ 개념 → 논리 → 물리 (순차 3모드)
  ↓ 물리(DBML) 완료 확인 [gate]
  ↓
DDL/MIGRATION (op-data-ddl)        ← 물리 DBML 산출 이후에만 실행 가능
  ↓
QA (PM Gate)
  ↓
CLOSE (DONE.md)
```

## 단계별 디스패치

- 전 단계 워커: `opal-db-agent` 단일 에이전트
- DICT·MODEL·DDL: `opal-db-agent`가 해당 op-data-* 스킬을 로드하여 실행

## 핵심 의존 제약

| 의존 | 설명 |
|------|------|
| DICT → MODEL | 사전이 속성명·타입 SSOT (절대 선행) |
| MODEL 물리 → DDL | state-tool stage-transition guard 자동 차단 |
| MODEL 사용자 확인 → PM 자율 | 행 8 이후 DDL/QA PM 자율 실행 |

## 모드 경계 (semi-agentic)

- **행 1-8** (TASK·DICT·MODEL): 각 단계 사용자 확인 필수
- **행 8 이후** (DDL·QA·CLOSE): PM 자율 실행 가능
- **행 15** (CLOSE): 사용자 승인 필수 (공통)

## 산출물 트리 (default)

```
{설계}/
  210.사전/
    표준단어사전.md
    도메인사전.md
    코드사전.md
    (xlsx 뷰 — export 파생물)
  220.개념모델링/
    ERD_{영역}.mermaid + .md
  230.논리모델링/
    ERD_{영역}_논리.mermaid + .md
  240.물리모델링/
    {프로젝트}.dbml
  250.DDL/
    (DDL SQL + 마이그레이션 스크립트)
```

## 관련 페이지

- [[skill-opal-pilot-data-design.md]]
- [[op-data-dictionary-skill.md]]
- [[op-data-model-skill.md]]
- [[op-data-ddl-skill.md]]
- [[dict-선행-model-ssot.md]]
- [[opdd-design-artifacts-path-pattern.md]]
