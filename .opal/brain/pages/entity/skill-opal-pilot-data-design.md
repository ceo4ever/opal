---
type: entity
title: opal-pilot-data-design (opdd)
tags: [pilot, orchestrator, data-design, db]
sources: [task:019]
related: [op-data-dictionary-skill, op-data-model-skill, op-data-ddl-skill, opdd-pipeline-flow]
created: 2026-06-12
updated: 2026-06-12
status: active
---

## 개요

DB 설계 파이프라인 오케스트레이터. `TASK → DICT → MODEL → DDL/MIGRATION → QA → CLOSE` 6단계를 조율하며, 전 단계 워커로 `opal-db-agent` 단일 에이전트를 디스패치한다.

## 설계 배경 (WHY)

DB 설계 업무가 standalone `erd-modeler`로 처리되던 것을 OPAL 표준 3층 체계(pilot + 단계 스킬 + 에이전트)로 내재화했다. 사전(DICT)이 모델(MODEL)의 속성명·타입 SSOT이므로 DICT 선행을 파이프라인 구조로 강제한다.

## 인터페이스

- **alias**: `opdd`
- **트리거**: `^opal-pilot-data-design$`, `^opdd$`, `(?i)(데이터\s*설계|DB\s*설계|데이터\s*모델링\s*파이프라인)`
- **파이프라인**: `TASK → DICT → MODEL(개념→논리→물리) → DDL/MIGRATION → QA → CLOSE`
- **STATE 행**: 15행 (semi-agentic 기준)
- **모드 경계**: MODEL 사용자 확인 행(행 8) 통과 후 PM 자율
- **DDL 의존**: MODEL 물리(DBML) 산출 이후에만 DDL 단계 실행 가능 (state-tool stage-transition guard)
- **스킬 경로**: `opal/skills/opal-pilot-data-design/SKILL.md`

## STATE 행 구조 (15행)

| 행 | 단계 | 항목 |
|----|------|------|
| 1-2 | TASK | 작업 / 사용자확인 |
| 3-5 | DICT | 작업 / PM Gate / 사용자확인 |
| 6-8 | MODEL | 작업 / PM Gate / 사용자확인 ← 모드 경계 |
| 9-11 | DDL/MIGRATION | 작업 / PM Gate / 사용자확인 |
| 12-14 | QA | 작업 / PM Gate / 사용자확인 |
| 15 | CLOSE | DONE.md 생성 |

## 관련 페이지

- [[op-data-dictionary-skill.md]]
- [[op-data-model-skill.md]]
- [[op-data-ddl-skill.md]]
- [[opdd-pipeline-flow.md]]
- [[dict-선행-model-ssot.md]]
