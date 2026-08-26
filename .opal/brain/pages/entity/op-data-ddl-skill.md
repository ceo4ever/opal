---
type: entity
title: op-data-ddl (DDL 단계 스킬)
tags: [skill, stage-skill, data-design, ddl, migration, dbml]
sources: [task:019]
related: [skill-opal-pilot-data-design, op-data-model-skill, opdd-pipeline-flow]
created: 2026-06-12
updated: 2026-06-12
status: active
---

## 개요

DB 설계 파이프라인의 DDL 단계 스킬. MODEL 물리 산출물(DBML)을 입력으로 받아 DDL SQL을 추출하고 ORM 마이그레이션 스크립트를 생성한다. **물리(DBML) 완료 이후에만 실행 가능**하다.

## 설계 배경 (WHY)

`erd-modeler`의 DDL 로직(`SKILL.md:194-253`)을 계승·분해하여 독립 단계 스킬로 이관했다. DDL은 물리 모델의 기계적 추출이므로 MODEL 물리 확정 후 PM 자율 실행이 가능하다.

## 인터페이스

- **stage**: `DDL`
- **dispatched_by**: `opal-pilot-data-design`
- **스킬 경로**: `opal/skills/op-data-ddl/SKILL.md`
- **references**:
  - `opal/skills/op-data-ddl/references/dbml-guide.md` (물리 DBML 문법 이관본)
- **필수 전제**: MODEL 물리(DBML) 산출 완료

## 주요 동작

- **DBML→DDL**: `dbml2sql --mysql/--postgres/--mssql` (CLI 부재 시 수동 폴백)
- **역공학**: `sql2dbml`
- **마이그레이션**: ORM 마이그레이션 스크립트 생성
- **타입 매핑**: op-data-dictionary의 도메인사전(db-type-mapping.md) 참조

## 관련 페이지

- [[skill-opal-pilot-data-design]]
- [[op-data-model-skill]]
- [[opdd-pipeline-flow]]
