---
type: concept
title: 3계층 기억 아키텍처 — MEMORY / brain / tasks
tags:
- architecture
- memory
- brain
- long-term
- tasks
sources:
- task:016
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: active
---
## 개념 요약

OPAL PM의 기억 계층을 단기·장기 검색·장기 원본의 3계층으로 명문화한 아키텍처 결정. MEMORY.md(단기 FIFO 10) → brain(장기 검색·요약) → tasks/(장기 원본) 흐름으로 과거 결정을 복리 활용한다.

## 배경·문제 (WHY)

015까지 PM은 MEMORY.md(단기 10건)와 tasks/ 원본만 보유했다. tasks/는 원본이지만 대량 분산으로 검색 불가능하고, MEMORY.md는 FIFO 10건으로 오래된 결정이 소멸했다. "장기 원본 검색 → 상세 drill-down" 경로가 없어 과거 결정이 재발명되었다.

## 결정 내용 (HOW)

| 계층 | 위치 | 역할 | 수명 |
|------|------|------|------|
| 단기 기억 | `MEMORY.md` | PM 운영 기억·피드백 (FIFO 10건) | 최근 N건만 |
| 장기 검색 | `.opal/brain/` | 태스크·문서 WHY/HOW 요약 + `task:NNN` 포인터 | 영속 |
| 장기 원본 | `tasks/NNN/` | DONE.md·PLAN.md 전문 원본 | 영속 |

- **brain search → tasks drill-down**: `brain-tool search <키워드>`로 후보 페이지 발견 → `sources: [task:NNN]` 포인터로 원본 drill-down.
- **`ingest task:NNN` 모드**: 태스크 DONE/PLAN에서 가치 지식을 concept 페이지로 적재. sources에 `task:NNN` 형식 기록.
- **001~015 소급 백필**: op-brain-ingest 포함/제외 기준 재사용(백필 기준 SSOT 단일화) — 9건 적재, 3건 제외.
- **SCHEMA 명문화**: `opal/tools/brain-tool/templates/schema-template.md`에 3계층 역할·drill-down 흐름 절 추가.

## 영향·관계

- `opal/tools/brain-tool/templates/schema-template.md` — 3계층 기억 절 + `sources: [task:NNN]` 형식
- `opal/skills/opal-brain/SKILL.md` — ingest task:NNN 모드 + 백필 절차
- `opal/skills/op-brain-ingest/SKILL.md` — 백필 기준 = CLOSE ingest 기준 동일(SSOT) 명시

## 근거 출처

`task:016` PLAN §0 M-3, TASK §확정 §6 — `opal/tools/brain-tool/templates/schema-template.md` 3계층 절.

## 관련

- [[opal-brain-system]] — 3계층 중 "장기 검색" 계층을 담당하는 시스템
- [[wiki-intelligence-decisions-016]] — 3계층 명문화를 확정한 016 의사결정
