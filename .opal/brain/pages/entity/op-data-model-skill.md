---
type: entity
title: op-data-model (MODEL 단계 스킬)
tags: [skill, stage-skill, data-design, modeling, erd, mermaid, dbml]
sources: [task:019]
related: [skill-opal-pilot-data-design, op-data-dictionary-skill, op-data-ddl-skill, opdd-pipeline-flow]
created: 2026-06-12
updated: 2026-06-12
status: active
---

## 개요

DB 설계 파이프라인의 MODEL 단계 스킬. `concept(개념) → logical(논리) → physical(물리)` 3모드 분리 발동으로 데이터 모델링을 수행한다. `//erm` alias의 하위호환 목적지이기도 하다.

## 설계 배경 (WHY)

`erd-modeler`의 모델링 로직(`SKILL.md:82-191`)을 계승·분해하여 독립 단계 스킬로 이관했다. 논리 모드의 속성명이 DICT 표준사전 용어를 SSOT로 소비해야 하므로 DICT 후속 단계로 고정된다.

## 인터페이스

- **stage**: `MODEL`
- **dispatched_by**: `opal-pilot-data-design`
- **alias**: `//erm` (하위호환 — erd-modeler deprecation 정책)
- **스킬 경로**: `opal/skills/op-data-model/SKILL.md`
- **references**:
  - `opal/skills/op-data-model/references/mermaid-guide.md` (개념/논리 Mermaid 문법 이관본)

## 3모드 산출물 양식

| 모드 | 트리거 옵션 | 산출물 경로 | 규칙 |
|------|-----------|-----------|------|
| concept | `--concept` | `{설계}/개념모델링/ERD_{영역}.mermaid` + `.md` | Mermaid erDiagram, M:N 허용, FK 없음 |
| logical | `--logical` | `{설계}/논리모델링/ERD_{영역}_논리.mermaid` + `.md` | 속성명 = DICT 표준사전 용어 SSOT |
| physical | `--physical` | `{설계}/물리모델링/{프로젝트}.dbml` | DBML, 명명규칙·타입=도메인사전 |

## 관련 페이지

- [[skill-opal-pilot-data-design]]
- [[op-data-dictionary-skill]]
- [[op-data-ddl-skill]]
- [[erd-modeler-deprecation]]
- [[dict-선행-model-ssot]]
- [[opdd-pipeline-flow]]

