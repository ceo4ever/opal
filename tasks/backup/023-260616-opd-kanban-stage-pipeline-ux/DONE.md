# DONE: OPAL Console 칸반 현재 단계 표시 + 파이프라인 스테퍼 모호성 개선

> 완료일: 2026-06-16 17:13 | 스킬: opd (semi-agentic) | 태스크: 023

## 1. 목표 달성

OPAL Console 태스크 칸반의 두 UX 모호성을 해소했다.
- **R1**: 진행중 카드가 항상 빈 단계를 표시하던 문제를 BE 파생으로 해결, 카드에 현재 단계 뱃지 표시.
- **R2**: 상세 Sheet 파이프라인 스테퍼가 행 단위로 동일 stage명을 반복하던 모호성을 stage 그룹 단위(단계당 1회 + `완료/전체` 카운트)로 개선.

## 2. 변경 파일 (수정 4)

| 파일 | 변경 |
|------|------|
| `dashboard/backend/routers/tasks.py` | `_derive_current_stage`(도달 단계 기준)·`_aggregate_status`(na/skipped 제외)·`_group_pipeline_stages` 신규, `_state_to_task_card`/`get_task_detail` 적용 |
| `dashboard/backend/models.py` | `PipelineStageGroup` 신규, `TaskDetailResponse.pipeline` 타입 `list[PipelineRow]`→`list[PipelineStageGroup]`, `PipelineRow` 보존 |
| `dashboard/frontend/src/pages/tasks/TasksPage.tsx` | `KanbanCard` 단계 뱃지 승격(진행중 강조), `PipelineStepper` 그룹 렌더(단계당 1스텝+`n/m`), 타입 동기 |
| `dashboard/backend/tests/test_routers.py` | 신규 16 테스트(파생 3규칙·집계 4규칙·그룹·detail·도달단계·na 제외) |

## 3. 핵심 설계 결정

- **단계 파생은 BE 단일 소스** — FE는 표시만(중복 로직 금지).
- **`current_stage` = 도달 단계** — ① in_progress 행 stage → ② 없으면 마지막 도달(done/na/skipped/in_progress) 단계 → ③ 전부 pending이면 첫 단계. **미시작(pending) 단계는 current_stage로 표시하지 않는다** (진행중↔CLOSE 모순 해소).
- **stage 그룹 status 집계** — `na`/`skipped`는 "해당없음"으로 제외, blocked 우선 → in_progress → 전부 done → 혼재 in_progress → pending. 카운트도 na/skipped 제외.
- **read-only 불변** — 전 변경 read/응답가공/표시 한정, state-tool 쓰기·파일 쓰기 없음.

## 4. 검증 결과

- pytest **49 passed / 0 failed** (신규 16 포함, 회귀 없음), ruff clean, FE `npm run build` tsc 0 에러.
- RED-first: BE 로직 RED 12/12 + fix RED 4/4 → 전부 GREEN(테스트 불변).
- L3 [SUPERVISOR] 캡틴 시각 확인 PASS — 배포본(7823) 실데이터(152) 카드·스테퍼 `TEST` 정상.
- 정식 재배포(install [5]) 완료 + 데몬 재기동 + /health ok.

## 5. fix 루프 (TEST 실데이터 검증서 발견)

진행중 카드가 미시작 `CLOSE`를 표기하고 `na`/`skipped` status를 미고려하던 결함을 실데이터(152)에서 발견 → 도달단계 규칙 + na/skipped 제외로 교정. (021 교훈: 실렌더가 build-only를 보완한 사례.)

## 6. 후속 후보

- 전부 na/skipped인 단계의 `0/0` 카운트 표기 — 현 실데이터 미발생, 발생 시 FE에서 단계명만 표시하도록 개선.
- 미커밋 상태 — 커밋은 캡틴 지시 시 수행.
