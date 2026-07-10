---
type: concept
title: opdd 설계 산출물 경로 패턴 — opwt 차용 + {설계} 변수
tags: [architecture-decision, data-design, path, ssot, opwt]
sources: [task:019]
related: [opdd-pipeline-flow, op-data-dictionary-skill, skill-opal-pilot-write-tech]
created: 2026-06-12
updated: 2026-06-12
status: active
---

## 개요

opdd 파이프라인의 설계 산출물 저장 경로를 `opwt(opal-pilot-write-tech)` 패턴으로 결정했다. 프로젝트별 설계 루트 `{설계}`를 `docs/PROJECT.md`에 1회 선언하고, op-data-* 스킬이 이를 변수로 읽어 경로를 해소한다.

## 결정 배경 (WHY)

- 설계 검토서(`docs/proposals/opal-data-design.md`)가 사전 위치를 `{설계}/사전/`으로 명시했으나, `opal-db-agent`의 기존 경로 토큰은 `docs/db/`로 달라 SSOT 혼선 발생 (R-T1).
- 경로 하드코딩은 프로젝트마다 다른 디렉토리 구조에 대응 불가.
- opwt의 "PROJECT.md SSOT + default 트리 + 자동 감지" 패턴이 동일 문제를 이미 해결한 선례.

## 결정 내용

1. **PROJECT.md 1회 선언**: 설계 루트 `{설계}` 경로를 `docs/PROJECT.md`에 등록.
2. **기본 트리** (opwt `XXX.{이름}/` prefix 패턴, 10 간격):
   ```
   200.설계/
     210.사전/       # 표준단어사전.md, 도메인사전.md, 코드사전.md + xlsx 뷰
     220.개념모델링/
     230.논리모델링/
     240.물리모델링/
     250.DDL/
   ```
3. **자동 감지 3분기** (opwt Q6 패턴):
   - ① PROJECT.md 등록 경로 있음 → 사용
   - ② 루트에 `200.설계/` 존재 → 사용
   - ③ 둘 다 없음 → default 제안 + 사용자 직접 입력
4. **db-agent 토큰 통일**: 기존 `docs/db/` 토큰을 `{설계}` 변수 참조로 교체 → 불일치 해소.

## 영향 범위

- `opal/skills/op-data-dictionary/SKILL.md` — `{설계}/사전/` 경로 변수 사용
- `opal/skills/op-data-model/SKILL.md` — `{설계}/개념모델링/`, `{설계}/논리모델링/`, `{설계}/물리모델링/`
- `opal/skills/op-data-ddl/SKILL.md` — `{설계}/250.DDL/`
- `opal/agents/opal-db-agent/AGENT.md` — `{설계}` 변수 참조로 통일
- `opal/skills/opal-pilot-data-design/SKILL.md` — TASK 단계 경로 감지 로직

## 관련 페이지

- [[opdd-pipeline-flow.md]]
- [[op-data-dictionary-skill.md]]
- [[skill-opal-pilot-write-tech.md]]
