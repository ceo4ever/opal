---
type: concept
title: 칸반 current_stage 파생 규칙 (도달 단계 기준)
tags: [opal-console, kanban, pipeline, be-single-source]
sources: [task:023]
related: [[opal-console, kanban-pipeline-stage-grouping, test-real-data-validation-lesson]]
created: 2026-06-16
updated: 2026-06-16
status: active
---

## 개요

OPAL Console 태스크 칸반 카드의 `current_stage`는 state.json에 기록되지 않으므로 BE가 `rows[]`에서 동적 파생한다. **미시작(pending) 단계는 current_stage로 표시하지 않는다** — 도달한(in_progress/done 포함) 단계만 현재 단계로 인정한다.

## 결정 배경 (WHY)

- state-tool은 top-level `current_stage` 필드를 기록하지 않아 state.json에서 항상 `None`
- 단계 정보는 `rows[]`에 살아있음: 각 행 `stage`(TASK/PLAN/EXECUTE/CLOSE 등) + `status`(done/pending/in_progress/blocked)
- 실측(태스크 152): 진행중 카드가 미시작 `CLOSE`를 현재 단계로 표기하는 결함 발생
- 기존 규칙(첫 미완료 행의 stage)은 아직 도달하지 않은 단계를 current_stage로 노출하는 모순 → 도달 단계 기준으로 교정

## 결정 내용

**`_derive_current_stage(rows)` 파생 규칙 (최종 확정)**:

```
① in_progress 행이 있으면 그 행의 stage
② 없으면 마지막 도달(done/na/skipped/in_progress) 단계의 stage
③ 전부 pending이면 첫 단계
- rows 비어있으면 "" 반환
```

**핵심**: 미시작(pending) 단계는 current_stage로 표시하지 않는다. CLOSE 행이 pending이더라도, 실제 진행중인 단계(예: EXECUTE in_progress)가 current_stage가 된다.

**단일 소스 원칙**: BE `dashboard/backend/routers/tasks.py` `_derive_current_stage` 헬퍼가 유일 구현. FE는 BE 응답 `current_stage` 값을 그대로 표시만 한다(중복 로직 금지).

**적용 지점**:
- `_state_to_task_card`: `state.get("current_stage") or _derive_current_stage(rows)`
- `get_task_detail`: 동일 패턴 (카드·상세 일관)

## 영향 범위

- `dashboard/backend/routers/tasks.py` — `_derive_current_stage` 헬퍼, `_state_to_task_card`, `get_task_detail`
- `dashboard/frontend/src/pages/tasks/TasksPage.tsx` — `KanbanCard` (표시만, 로직 없음)

## 관련 페이지

- [[opal-console]]
- [[kanban-pipeline-stage-grouping]]
- [[test-real-data-validation-lesson]]
