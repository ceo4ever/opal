# ANALYSIS: 칸반 현재 단계 표시 + 파이프라인 스테퍼 모호성 개선

> 작성일: 2026-06-16 | 단계: ANALYSIS | 대상: TASK.md R1/R2
> 분석 방식: op-dev-analysis 워커(코드/state.json 실측) → PM 정리

## 1. R1 — `current_stage` 항상 빈 값: 근본 원인 확정

| 항목 | 내용 |
|------|------|
| 증상 | 진행중 카드에 단계명 미표시 |
| 원인 | state.json top-level에 `current_stage` 필드 자체가 없음(state-tool 미기록). `tasks.py:199`/`:333`이 `state.get("current_stage", "")` → 항상 `""` |
| 데이터 가용성 | 단계 정보는 `rows[]`에 존재 — 각 행 `stage`(TASK/PLAN/EXECUTE/TEST/CLOSE) + `status`(done/pending/in_progress/blocked). `_state_to_task_card`·`get_task_detail` 모두 이미 `rows`를 손에 들고 있음 → 추가 조회 불요 |

**파생 규칙(TASK.md 확정) 실데이터 검증**:

| 태스크 | rows 상태 | 규칙 적용 결과 |
|--------|----------|---------------|
| 015 (완료) | 9행 전부 done | 전부 done → 마지막 stage = `CLOSE` |
| 005 (진행중) | TASK done·done·pending, PLAN 전부 pending … | in_progress 없음 → 첫 미완료(TASK pending) → `TASK` |

규칙: `① in_progress 행의 stage → ② 없으면 첫 미완료(pending/blocked) 행의 stage → ③ 전부 done이면 마지막 행 stage`. ✅ 실데이터에서 의도대로 동작.

**구현 위치**:
- 신규 헬퍼 `_derive_current_stage(rows: list[dict]) -> str` (단일 소스)
- `_state_to_task_card`(L170~203): state 있을 때 `state.get("current_stage") or _derive_current_stage(rows)`
- `get_task_detail`(L279~340, L333): 동일 파생 적용 → 카드·상세 일관
- state.json 없는 태스크는 기존 `_infer_column_from_artifacts`가 이미 stage 문자열("진행"/"DONE") 반환 — 유지

## 2. R2 — 파이프라인 스테퍼 모호성: 메커니즘 + 그룹핑 방안

**현 메커니즘**: `PipelineStepper`(TasksPage.tsx:244~274)가 `detail.pipeline`(=rows)를 **행 단위**로 점+라벨 렌더 → 같은 stage가 행 수만큼 반복(`TASK TASK`, `PLAN PLAN PLAN`, `TEST TEST TEST`). "단계"인지 "단계 내 서브항목"인지 모호.

**그룹핑 방안 트레이드오프**:

| 옵션 | 방식 | 장점 | 단점 |
|------|------|------|------|
| **A (권고)** | BE에서 rows → stage 그룹(`stage`/`done_count`/`total`/`status`) 변환 후 전달 | BE 단일 소스 원칙 강화, FE 단순, 1회 계산 | `TaskDetailResponse.pipeline` 스키마 변경(내부 클라이언트라 관리 용이) |
| B | FE에서 그룹핑 | BE 무변경 | FE 복잡↑, 매 렌더 계산, 로직 위치 분산 |

→ BE가 이미 rows 전수 보유 + TASK.md "BE 단일 소스" 확정 → **옵션 A 권고**. 단계 status = 전부 done이면 done / 하나라도 in_progress·혼재면 in_progress / 전부 pending이면 pending.

**FE 표현(권고)**: 단계당 1스텝(TASK→PLAN→EXECUTE→TEST→CLOSE) + 단계 내 `완료/전체` 카운트(예: `EXECUTE 1/1`, `TEST 0/3`) 또는 세그먼트. 색상은 기존 `stageStatusClass`/`status-*` 토큰 재사용.

## 3. 변경 파일 목록

| 파일 | 변경 | 영역 |
|------|------|------|
| `dashboard/backend/routers/tasks.py` | `_derive_current_stage` 신규 + 2곳 호출 + (옵션A) pipeline 그룹 변환 | BE |
| `dashboard/backend/models.py` | (옵션A) `PipelineStageGroup` 신규 + `TaskDetailResponse.pipeline` 타입 | BE |
| `dashboard/frontend/src/pages/tasks/TasksPage.tsx` | `PipelineStepper` stage 그룹 렌더 + 카드 단계 표기 가독성 승격 / 타입 동기 | FE |
| `dashboard/backend/tests/test_routers.py` | `_derive_current_stage` 단위(3규칙) + 카드/detail current_stage 회귀 | BE |

`KanbanCard`의 current_stage 렌더(L172~176)는 이미 존재 — BE가 값을 채우면 동작. 가독성 승격(뱃지화)만 FE 추가.

## 4. 제약·리스크

- **[MUST] read-only 계약**: 변경은 전부 BE read 로직 + FE 표시 → state-tool 쓰기·파일 편집 없음. 위반 없음.
- **[MUST] BE 단일 소스**: 파생/그룹핑 BE 집중, FE 중복 금지. 옵션 A가 이를 강화.
- **색상 토큰**: `status-*`/`:root` 토큰만 사용, 하드코딩 금지.
- **회귀 리스크**: `TaskDetailResponse.pipeline` 스키마 변경 시 FE 타입 동시 수정 필수(누락 시 상세 Sheet 깨짐) → TEST에서 cmux 실렌더 검증.

## 5. PLAN 진입 시 확정할 결정

- D-1: R2 그룹핑 옵션 A vs B (권고 A)
- D-2: 단계 status 집계 규칙 (혼재 시 in_progress 처리)
- D-3: FE 단계 내 진행 표현(카운트 vs 세그먼트)
- D-4: BE/FE 워커 매핑(opal-be-agent / opal-fe-agent) 및 Phase 구성
