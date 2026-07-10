---
type: concept
title: erd-modeler deprecate — op-data-model/ddl로 분해, //erm 하위호환
tags: [architecture-decision, deprecation, erd-modeler, migration]
sources: [task:019]
related: [op-data-model-skill, op-data-ddl-skill, opdd-pipeline-flow]
created: 2026-06-12
updated: 2026-06-12
status: active
---

## 개요

standalone `skills/erd-modeler`를 `op-data-model`(모델링 로직)과 `op-data-ddl`(DDL 로직)로 분해 이관하고 deprecated 처리했다. `//erm` alias는 `op-data-model` 단독 호출 alias로 2개 마이너 버전간 하위호환을 유지한다.

## 결정 배경 (WHY)

- erd-modeler가 사전 참조(`../data-dictionary/references/...`)를 하드코딩했으나 `data-dictionary` 디렉토리가 실제로 존재하지 않아 참조가 깨진 상태였다.
- 모델링·DDL 기능이 단일 파일에 통합되어 있어 opdd 파이프라인의 단계별 디스패치 구조와 맞지 않았다.
- `naming-convention.md`가 MySQL 9 타입만 지원하여 PG/MSSQL/Oracle 지원 부재.

## 결정 내용

1. **이관 분해**:
   - `erd-modeler SKILL.md §4(모델링 로직 :82-191)` → `op-data-model/SKILL.md`
   - `erd-modeler SKILL.md §5(DDL 로직 :194-253)` → `op-data-ddl/SKILL.md`
   - `references/naming-convention.md` → `op-data-dictionary/references/`
   - `references/mermaid-guide.md` → `op-data-model/references/`
   - `references/dbml-guide.md` → `op-data-ddl/references/`
2. **erd-modeler 처리**:
   - `skills/erd-modeler/SKILL.md` 상단에 `[DEPRECATED]` 배너 추가
   - 레지스트리 항목에 deprecated 표기
   - 깨진 참조(`../data-dictionary/references/`) 해소 (이관 안내로 대체)
3. **//erm 하위호환** (U-3):
   - alias `erm` 유지, op-data-model로 라우팅
   - 유지 기간: 최소 2개 마이너 버전 (별도 후속 공지 후 제거)
   - 3단 안내: (a) SKILL.md 헤더 배너, (b) 레지스트리 description deprecated 표기, (c) 호출 시 마이그레이션 안내

## 영향 범위

- `skills/erd-modeler/SKILL.md` — deprecated 배너 + 깨진 참조 해소
- `opal/core/references/opal-skills-registry.json` — erd-modeler 항목 deprecated + //erm 라우팅
- `opal/skills/op-data-model/SKILL.md` — //erm alias 수신처
- 기존 //erm 사용자 — 안내 후 2 마이너 버전 유예

## 관련 페이지

- [[op-data-model-skill.md]]
- [[op-data-ddl-skill.md]]
- [[op-data-dictionary-skill.md]]
