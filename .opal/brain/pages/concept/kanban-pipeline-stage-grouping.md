---
type: concept
title: 파이프라인 스테퍼 stage 그룹화 (BE 단일 소스, na/skipped 제외)
tags: [opal-console, pipeline, stage-grouping, be-single-source]
sources: [task:023]
related: [opal-console, kanban-current-stage-derivation]
created: 2026-06-16
updated: 2026-06-16
status: active
---

## 개요

OPAL Console 태스크 상세 Sheet 파이프라인 스테퍼는 `rows[]`를 행 단위가 아니라 **stage 단위로 그룹핑**하여 단계당 1스텝으로 표시한다. 그룹 내 status 집계 및 done/total 카운트에서 `na`/`skipped`는 제외한다. 그룹핑은 BE 단일 소스.

## 결정 배경 (WHY)

- 기존 행 단위 렌더: 동일 stage명이 반복 노출(`TASK TASK`, `PLAN PLAN PLAN`, `TEST TEST TEST`) — 단계인지 서브항목인지 모호
- `na`/`skipped` 행을 그대로 집계하면 실제 진행 카운트가 부풀려지거나 잘못된 status가 노출됨

## 결정 내용

### `PipelineStageGroup` 모델 (`dashboard/backend/models.py`)

```python
class PipelineStageGroup(BaseModel):
    stage: str          # "TASK" | "PLAN" | "EXECUTE" | "TEST" | "CLOSE" 등
    done_count: int     # 단계 내 done 행 수 (na/skipped 제외)
    total: int          # 단계 내 전체 행 수 (na/skipped 제외)
    status: str         # 집계 status
    rows: list[PipelineRow] = []   # 원본 행 보존 (툴팁/확장 여지)
```

`TaskDetailResponse.pipeline` 타입: `list[PipelineRow]` → `list[PipelineStageGroup]`

### `_aggregate_status` 집계 규칙 (D-2, na/skipped 제외)

```
① 하나라도 blocked   → "blocked"    (blocked 우선)
② 전부 done          → "done"
③ 하나라도 in_progress 또는 done+pending 혼재 → "in_progress"
④ 전부 pending       → "pending"
```

`na`/`skipped` status는 "해당없음"으로 집계에서 제외. done_count/total 카운트도 동일.

### FE 렌더 구조 (표시 전용)

```
{pipeline.map((g, idx) => (
  <div>
    <dot className={stageStatusClass(g.status)} />
    <span>{g.stage}</span>
    <span muted>{g.done_count}/{g.total}</span>
    {idx < pipeline.length-1 && <ChevronRight />}
  </div>
))}
```

FE `PipelineStageGroup` 인터페이스는 BE 모델 미러 — 그룹핑 로직 FE 중복 금지.

## 영향 범위

- `dashboard/backend/models.py` — `PipelineStageGroup` 신규, `TaskDetailResponse.pipeline` 타입 변경
- `dashboard/backend/routers/tasks.py` — `_group_pipeline_stages`, `_aggregate_status` 헬퍼
- `dashboard/frontend/src/pages/tasks/TasksPage.tsx` — `PipelineStepper` 그룹 렌더, `PipelineStageGroup` 인터페이스 신규

## 관련 페이지

- [[opal-console]]
- [[kanban-current-stage-derivation]]
