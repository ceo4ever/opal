# TASK: OPAL Console 칸반 현재 단계 표시 + 파이프라인 스테퍼 모호성 개선

> 작성일: 2026-06-16 | 작업 유형: 개선 | 적용 스킬: opd | 모드: semi-agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

OPAL Console 태스크 칸반에서 (1) 카드에 현재 진행 단계를 표시하고, (2) 상세 Sheet의 파이프라인 스테퍼가 "단계(stage)"인지 "단계 내부 서브항목"인지 모호한 표현을 명확히 구분하도록 개선한다.

## 배경

진행중 태스크가 칸반 카드만 봐서는 지금 어느 단계(TASK/PLAN/EXECUTE/TEST/CLOSE)에 있는지 알 수 없다. 또한 상세 Sheet의 파이프라인 스테퍼는 행(row) 단위로 점을 찍고 각 점에 stage명을 라벨링해서 `TASK TASK / PLAN PLAN PLAN / TEST TEST TEST`처럼 같은 이름이 반복 노출 — 단계를 표현하는 것인지 단계 내부 서브항목을 표현하는 것인지 모호하다.

## 배경 분석 (대화에서 도출)

코드 실측 결과:

- **카드 컴포넌트는 이미 `current_stage`를 렌더링**한다 (`dashboard/frontend/src/pages/tasks/TasksPage.tsx:172-176`, 회색 소형 mono 텍스트, `ml-auto`).
- 그러나 **state-tool은 top-level `current_stage` 필드를 기록하지 않는다** → state.json에서 항상 `None`.
  - 실측: `tasks/015-.../state.json` `current_stage: None`, `tasks/005-.../state.json` `current_stage: None`.
  - BE `routers/tasks.py` `_state_to_task_card`가 `state.get("current_stage", "")` 그대로 읽어 항상 빈 값 → 카드에 단계 미표시.
- 단계 정보는 `rows[]`에 살아있다: 각 행 `stage`(TASK/PLAN/EXECUTE/CLOSE 등) + `status`(done/pending/in_progress/blocked).
  - 예) 005 rows = TASK done, TASK done, TASK pending, PLAN pending… → 현재 단계 = TASK.
- 파이프라인 스테퍼(`PipelineStepper`, `TasksPage.tsx:244-274`)는 `pipeline[]`(=rows)를 그대로 1행=1점으로 렌더하고 각 점에 `row.stage`를 라벨 → 동일 stage 반복 노출(스크린샷의 `TASK TASK`, `PLAN PLAN PLAN`, `TEST TEST TEST`).
- 스크린샷 예시 태스크(152)는 CLOSE 행이 pending(미마감)인데도 진행중 80%로만 표시 — 카드에서 실제 단계를 알 수 없는 문제를 그대로 보여줌.

## 확정된 설계 방향 (대화에서 합의)

- **R1 현재 단계 파생은 BE에서 수행**한다 (단일 소스 → 카드·상세 자동 일관). 파생 규칙(권고): `in_progress` 행의 stage → 없으면 첫 미완료(pending/blocked) 행의 stage → 전부 done이면 마지막 stage(또는 `DONE`).
- **R2 스테퍼는 행이 아니라 단계(stage) 단위로 그룹핑**하여 단계를 1회씩 표시하고, 각 단계 내부 서브항목 개수/완료를 구분 가능하게 표현한다(예: 단계당 1스텝 + `(완료/전체)` 또는 세그먼트). 세부 표현은 PLAN에서 확정.

## 요구사항

- [ ] **R1. 칸반 카드 현재 단계 표시**
  - 무엇을: 카드(특히 진행중 컬럼)에 현재 진행 단계명을 표시
  - 어디에: BE `dashboard/backend/routers/tasks.py`(`_state_to_task_card`에 `current_stage` 파생 로직 추가) + FE `dashboard/frontend/src/pages/tasks/TasksPage.tsx`(`KanbanCard` 표기 가독성 승격)
  - 왜: state.json에 `current_stage`가 없어 항상 빈 값(실측 015/005)
  - AC: in_progress 태스크 카드에 현재 단계명(TASK/PLAN/EXECUTE/TEST/CLOSE 중 하나)이 비어있지 않게 표시된다. 파생 규칙(in_progress 행 → 첫 미완료 행 → 전부 done 시 마지막)이 적용되며, `GET /api/tasks` 응답의 해당 태스크 `current_stage`가 빈 문자열이 아니다. pytest 회귀 1건 이상 추가되어 통과한다.

- [ ] **R2. 파이프라인 스테퍼 모호성 제거**
  - 무엇을: 상세 Sheet 스테퍼를 stage 단위로 그룹핑하여 단계당 1개씩 표시 + 단계 내부 진행(서브항목 완료/전체) 구분
  - 어디에: FE `dashboard/frontend/src/pages/tasks/TasksPage.tsx`(`PipelineStepper`)
  - 왜: 현재 행 단위 렌더로 동일 stage명이 반복 노출되어 단계/서브항목 구분 모호(스크린샷)
  - AC: 스테퍼가 단계(TASK→PLAN→EXECUTE→TEST→CLOSE 등 stage 종류)를 중복 없이 1회씩 순서대로 표시하고, 각 단계의 서브항목 완료 상태(예: 완료/전체 카운트 또는 세그먼트)를 식별할 수 있다. 동일 stage 라벨 반복이 사라진다.

## 제약 조건

- **읽기 전용 불변**: 대시보드는 read-only. state-tool 쓰기 커맨드 호출 금지, dnd 비활성·🔒 badge 상시 등 기존 read-only 계약 유지.
- **BE 단일 소스**: 단계 파생은 BE에서 수행하고 FE는 표시만 한다(중복 로직 금지).
- **기존 테스트 회귀 금지**: dashboard/backend pytest 스위트 전체 통과 유지.
- **시그니처 색상 토큰 준수**: 상태 색상은 기존 `status-*` / `:root` 토큰 사용(하드코딩 금지).

## 기술 스택

- BE: Python 3 / FastAPI / pytest (`dashboard/backend/`)
- FE: React + TypeScript + Vite + shadcn/ui + TanStack Query (`dashboard/frontend/`)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | PROJECT.md | `docs/PROJECT.md` | 대시보드 구성·read-only 계약·문서 레지스트리 |
| D-2 | 소스 | tasks 라우터 | `dashboard/backend/routers/tasks.py` | `current_stage` 파생 추가 대상 + 칸반 계약 |
| D-3 | 소스 | 태스크 칸반 페이지 | `dashboard/frontend/src/pages/tasks/TasksPage.tsx` | 카드 표기 + 스테퍼 개선 대상 |
| D-4 | 소스 | 라우터 테스트 | `dashboard/backend/tests/test_routers.py` | R1 회귀 테스트 추가 위치 |
