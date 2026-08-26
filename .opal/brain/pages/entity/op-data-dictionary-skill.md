---
type: entity
title: op-data-dictionary (DICT 단계 스킬)
tags: [skill, stage-skill, data-design, dictionary, db]
sources: [task:019]
related: [skill-opal-pilot-data-design, op-data-model-skill, opdd-pipeline-flow]
created: 2026-06-12
updated: 2026-06-12
status: active
---

## 개요

DB 설계 파이프라인의 DICT 단계 스킬. 표준사전·코드사전의 CRUD 주체이며, md SSOT 3종(`표준단어사전.md` / `도메인사전.md` / `코드사전.md`)을 관리하고 xlsx를 단방향 export한다.

## 설계 배경 (WHY)

기존 `erd-modeler`는 사전을 읽기 전용으로만 참조하고 CRUD 주체가 없었다. 사전이 MODEL의 속성명·타입 SSOT이므로 전담 스킬로 분리하고 `opal-db-agent`를 CRUD 주체로 지정했다.

## 인터페이스

- **stage**: `DICT`
- **dispatched_by**: `opal-pilot-data-design`
- **스킬 경로**: `opal/skills/op-data-dictionary/SKILL.md`
- **references**:
  - `opal/skills/op-data-dictionary/references/naming-convention.md` (수식어/분류어·명명규칙 이관본)
  - `opal/skills/op-data-dictionary/references/db-type-mapping.md` (D001~ ↔ MySQL/PG/MSSQL/Oracle 타입 매핑)

## 주요 동작

- **md SSOT 3종**: `{설계}/사전/표준단어사전.md` / `도메인사전.md` / `코드사전.md`
- **xlsx export**: md → xlsx 단방향 (역방향 금지 — SSOT 혼선 방지)
- **모드 분기**: 기존 사전 주입 + 커버리지 충분 시 "검증·보강 모드" / 부재 시 "신규 작성 모드"
- **CRUD 주체**: `opal-db-agent`
- **db-type-mapping**: D001~D022 도메인 타입 × 4 DBMS (MySQL/PostgreSQL/MSSQL/Oracle) 매핑표

## 관련 페이지

- [[skill-opal-pilot-data-design]]
- [[op-data-model-skill]]
- [[dict-선행-model-ssot]]
- [[opdd-design-artifacts-path-pattern]]
- [[opdd-pipeline-flow]]

