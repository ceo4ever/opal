# PLAN: OPAL Console 칸반 현재 단계 표시 + 파이프라인 스테퍼 모호성 개선

> 작성일: 2026-06-16 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

OPAL Console 태스크 칸반의 두 UX 모호성을 해소한다. (R1) 진행중 카드가 항상 빈 `current_stage`를 표시하는 문제를 BE 단일 소스 파생으로 해결하고 카드 표기를 가독성 있게 승격한다. (R2) 상세 Sheet 파이프라인 스테퍼가 행(row) 단위로 동일 stage명을 반복 노출하는 문제를 BE에서 stage 그룹으로 변환(옵션 A)하여 단계당 1스텝 + 단계 내 완료/전체 표현으로 개선한다. 모든 단계 파생/그룹핑은 BE에 집중하고 FE는 표시만 한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | BE 현재 단계 파생 (`_derive_current_stage`) | R1 (BE 부분) | P0 | 없음 |
| F-002 | BE 파이프라인 stage 그룹 변환 + 스키마 | R2 (BE 부분) | P0 | 없음 |
| F-003 | FE 카드 현재 단계 표기 가독성 승격 | R1 (FE 부분) | P0 | F-001 |
| F-004 | FE 파이프라인 스테퍼 stage 그룹 렌더 | R2 (FE 부분) | P0 | F-002 |

> R1 = F-001(BE 파생) + F-003(FE 표기), R2 = F-002(BE 그룹 변환) + F-004(FE 렌더). TASK.md R1/R2 AC 전체 커버.

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (BE 단계 파생) ──────────► F-003 (FE 카드 표기)
F-002 (BE 그룹 변환+스키마) ────► F-004 (FE 스테퍼 렌더)
```

> BE(F-001/F-002)는 상호 독립이며 병렬 가능. FE(F-003/F-004)는 각자의 BE 계약(파생값/그룹 스키마)에 선행 의존. 따라서 Phase 1(BE) → Phase 2(FE) 순서.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-002 `models.py` `TaskDetailResponse.pipeline` 타입을 `list[PipelineRow]` → `list[PipelineStageGroup]`로 변경 | FE `TaskDetail.pipeline` 타입 미동기 시 상세 Sheet 스테퍼 깨짐(undefined 접근/렌더 실패) | P1 | L1(BE 스키마 단위) + L3(cmux 실렌더) 의무 | S-후보: F-004 동기 누락 회귀 |
| H-2 | F-001 `_derive_current_stage` status 우선순위 분기 | 전부 done인 완료 태스크에 빈 stage 또는 잘못된 stage 노출(규칙 ③ 누락) | P1 | L1(3규칙 단위) 의무 | S-후보: 015 완료 태스크 = CLOSE |
| H-3 | F-002 단계 status 집계 (D-2) 혼재 케이스 | done+pending 혼재 단계를 done으로 오집계 → 스테퍼가 미완료 단계를 완료로 표시 | P1 | L1(혼재 케이스 단위) 의무 | S-후보: 혼재 단계 = in_progress |
| H-4 | F-001/F-002 빈 rows / state=None 태스크 | rows 빈 배열에서 IndexError 또는 빈 그룹 → 상세 API 500 | P1 | L1(빈 rows 단위) + L2(state=None 경로) 의무 | S-후보: 빈 pipeline → [] 반환 |
| H-5 | F-003/F-004 색상 토큰 하드코딩 | `status-*` 토큰 외 hex 하드코딩 시 다크모드/테마 깨짐, CONVENTIONS 위반 | P2 | L3(시각 확인) 권고 | S-후보: stageStatusClass 재사용 검증 |
| H-6 | 전체 (read-only 계약) | state-tool 쓰기/파일편집 유입 시 read-only 불변 위반 | P0 | L1(전 변경 read 한정 확인) 의무 | S-후보: write 커맨드 부재 검증 |

**가설 도출 근거**: H-1은 ANALYSIS.md §4 "스키마 변경 시 FE 타입 동시 수정 필수(누락 시 상세 Sheet 깨짐)" 직접 인용. H-2/H-3은 D-2 집계 규칙·R1 파생 규칙의 분기 엣지케이스. H-4는 `tasks.py:312` `state.get("rows", [])` 빈 배열 경로. H-6은 [MUST] read-only 불변(TASK.md §제약).

---

## 2. 기능별 분석

### F-001: BE 현재 단계 파생 (`_derive_current_stage`)

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/routers/tasks.py` | `_derive_current_stage` 신규 헬퍼 + `_state_to_task_card`/`get_task_detail` 적용 | 수정 |
| BE | `dashboard/backend/tests/test_routers.py` | 파생 3규칙 단위 + 카드 회귀 | 수정 |

#### 2.1.2 현재 구현

ANALYSIS.md §1 참조. `_state_to_task_card`(`tasks.py:170-203`)는 `state.get("current_stage", "")`(`:199`)를 그대로 읽어 state.json에 해당 필드가 없으므로 항상 `""`. `get_task_detail`(`tasks.py:279-340`)도 `:333`에서 동일하게 `state.get("current_stage", "")`. 단계 정보는 `state["rows"]` 각 행의 `stage`/`status`에 존재하며, 두 함수 모두 이미 `rows`를 보유(`:189`, `:312`) → 추가 조회 불요. state.json 없는 태스크는 `_infer_column_from_artifacts`(`tasks.py:103-151`)가 `current_stage`를 "진행"/"DONE"/"" 로 이미 반환 — 유지.

#### 2.1.3 영향 범위

- 상위 의존(호출자): `list_tasks`(`:206`) → `_state_to_task_card`, `get_task_detail`(`:279`) 라우트.
- 하위 의존(피호출): `state["rows"]` 데이터 구조(행별 `stage`/`status`).
- 공유 상태: `cache`(`tasks_list:*`, `task_detail:*`) — 로직 변경 후 캐시 키 불변이므로 서버 재기동 시 신규 값 반영. 테스트는 헬퍼 직접 호출로 캐시 우회.
- 관련 테스트: `test_state_to_task_card_no_state_*`(`test_routers.py:344-368`) 패턴.

---

### F-002: BE 파이프라인 stage 그룹 변환 + 스키마

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/models.py` | `PipelineStageGroup` 신규 + `TaskDetailResponse.pipeline` 타입 변경 | 수정 |
| BE | `dashboard/backend/routers/tasks.py` | `_group_pipeline_stages` 신규 + `get_task_detail` 적용 | 수정 |
| BE | `dashboard/backend/tests/test_routers.py` | 그룹 변환 + detail 응답 검증 | 수정 |

#### 2.2.2 현재 구현

`get_task_detail`(`tasks.py:312-321`)이 `rows`를 행 단위 `PipelineRow`(`models.py:116-121`: row/stage/status/updated_at)로 1:1 매핑하여 `pipeline` 배열에 담는다. `TaskDetailResponse.pipeline: list[PipelineRow]`(`models.py:131`). FE는 이 배열을 그대로 행 단위 렌더 → 동일 stage 반복(ANALYSIS.md §2). 동일 stage가 연속/분산되어 여러 행으로 존재하는 것이 모호성의 근원.

#### 2.2.3 영향 범위

- 상위 의존: `get_task_detail` 라우트 응답 스키마(내부 클라이언트=Console FE 단독 소비, 외부 API 없음 → 스키마 변경 관리 용이, ANALYSIS.md §2 옵션 A 근거).
- 하위 의존: `PipelineRow`(그룹 내부 `rows`로 보존), `PipelineStageGroup`(신규).
- 공유 상태: `cache` `task_detail:*` — 캐시된 응답 객체 타입 변경(서버 재기동 시 반영).
- 관련 테스트: `test_api_tasks_detail_query_param`(`:272`) 등 detail 계약 테스트.

---

### F-003: FE 카드 현재 단계 표기 가독성 승격

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| FE | `dashboard/frontend/src/pages/tasks/TasksPage.tsx` | `KanbanCard` current_stage 표기 뱃지화(진행중 강조) | 수정 |

#### 2.3.2 현재 구현

`KanbanCard`(`TasksPage.tsx:117-193`)는 `card.current_stage`를 회색 소형 mono 텍스트 + `ml-auto`로 이미 렌더(`:172-176`). BE가 값을 채우면 동작하나, 회색 텍스트라 진행중 카드에서 단계가 눈에 띄지 않음(TASK.md R1 "가독성 승격"). `TaskCard.current_stage: string`(`:59`)은 이미 정의됨 → 타입 변경 불요.

#### 2.3.3 영향 범위

- 상위 의존: `KanbanColumnView`(`:199`) → `KanbanCard`.
- 하위 의존: `Badge`(이미 import, `:30`), `stageStatusClass`(`:106-111`, status-* 토큰).
- 공유 상태: 없음(표시 전용).
- 관련 테스트: cmux 실렌더 시각 확인(자동 단위 테스트 비대상).

---

### F-004: FE 파이프라인 스테퍼 stage 그룹 렌더

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| FE | `dashboard/frontend/src/pages/tasks/TasksPage.tsx` | `PipelineStepper` stage 그룹 렌더 + `TaskDetail.pipeline`/`PipelineRow` 타입 동기 | 수정 |

#### 2.4.2 현재 구현

`PipelineStepper`(`TasksPage.tsx:244-274`)가 `pipeline: PipelineRow[]`(`:64-69`)를 `.map`으로 행 단위 점+`row.stage` 라벨 렌더(`:251-271`) → 동일 stage 반복. `TaskDetail.pipeline: PipelineRow[]`(`:79`). `TaskDrawer`(`:324`)가 `detail.pipeline`을 `PipelineStepper`에 전달(`:379`). `stageStatusClass`(`:106-111`)는 status → bg-status-* 토큰 매핑 — 그룹 status에 재사용.

#### 2.4.3 영향 범위

- 상위 의존: `TaskDrawer`(`:379`) → `PipelineStepper`.
- 하위 의존: `PipelineRow` 인터페이스(`:64-69`)·`TaskDetail.pipeline`(`:79`) → 그룹 스키마로 동기.
- 공유 상태: 없음(표시 전용).
- 관련 테스트: cmux 실렌더(스테퍼에 동일 stage 반복 사라짐 시각 확인).

---

## 3. 기능별 설계

### F-001: BE 현재 단계 파생 (`_derive_current_stage`)

#### 3.1.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| - | (없음) | - | - | - |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/routers/tasks.py` | BE | `_derive_current_stage(rows)` 헬퍼 신규 + `_state_to_task_card`/`get_task_detail`에서 `state.get("current_stage") or _derive_current_stage(rows)` 적용 | (→ D-2 §1), ANALYSIS.md §1 "구현 위치" |
| 2 | `dashboard/backend/tests/test_routers.py` | BE | 파생 3규칙 단위 + state 있는 카드 회귀 | `test_routers.py:344-368` 패턴 |

#### 3.1.2 API·데이터 모델·화면 설계

**함수 시그니처 — `_derive_current_stage`** (R1 파생 규칙, TASK.md §확정·ANALYSIS.md §1)

```python
def _derive_current_stage(rows: list[dict]) -> str:
    """rows에서 현재 진행 단계명 파생 (BE 단일 소스).

    규칙 (PM 확정, R1 파생):
      ① in_progress 행이 있으면 그 행의 stage
      ② 없으면 첫 미완료(pending 또는 blocked) 행의 stage
      ③ 전부 done이면 마지막 행의 stage
      - rows 비어있으면 "" 반환
    """
```

알고리즘 의사코드:

```
if not rows: return ""
for r in rows:
    if r.get("status") == "in_progress": return r.get("stage", "")   # 규칙 ①
for r in rows:
    if r.get("status") in ("pending", "blocked"): return r.get("stage", "")  # 규칙 ②
return rows[-1].get("stage", "")   # 규칙 ③ (전부 done)
```

> [MUST] 단계 파생은 BE 단일 소스 — FE 중복 로직 금지 (TASK.md §제약 "BE 단일 소스: 단계 파생은 BE에서 수행하고 FE는 표시만 한다(중복 로직 금지)").

**적용 지점**:
- `_state_to_task_card`(`tasks.py:199`): `current_stage=state.get("current_stage") or _derive_current_stage(rows)` — state에 값이 있으면(미래 호환) 우선, 없으면 파생. `rows`는 `:189`에서 이미 추출됨.
- `get_task_detail`(`tasks.py:333`): 동일 패턴 적용. `rows`는 `:312`에서 추출됨 → 카드·상세 일관 (ANALYSIS.md §1).
- state=None 경로(`:172-182`)는 `_infer_column_from_artifacts`가 이미 stage 반환 → 변경 없음.

> [MUST] 읽기 전용: 파생은 메모리 내 read 연산 — state-tool 쓰기/파일편집 없음 (TASK.md §제약, `docs/CONVENTIONS.md` §State).

#### 3.1.3 환경 변경

해당 없음.

#### 3.1.4 배치/마이그레이션

해당 없음 (state.json 스키마 미변경 — top-level `current_stage` 미기록 상태 유지, BE가 rows에서 파생).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R1 규칙① | 기능 테스트 | in_progress 행 있는 rows → 그 행의 stage 반환 |
| TS-002 | R1 규칙② | 기능 테스트 | in_progress 없고 TASK done·done·pending → "TASK"(첫 미완료) 반환 (005 케이스) |
| TS-003 | R1 규칙③ | 기능 테스트 | 전부 done(9행) → 마지막 stage "CLOSE" 반환 (015 케이스) |
| TS-004 | R1 엣지 | 기능 테스트 | 빈 rows → "" 반환 (IndexError 없음) |
| TS-005 | R1 AC(응답) | 회귀 테스트 | state 있는 카드 `current_stage`가 빈 문자열 아님 (`_state_to_task_card` 직접 호출) |

---

### F-002: BE 파이프라인 stage 그룹 변환 + 스키마

#### 3.2.1 파일 변경 계획

**신규 생성**

| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| - | (없음 — 모델/헬퍼 추가는 기존 파일 내) | - | - | - |

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/models.py` | BE | `PipelineStageGroup` 신규 + `TaskDetailResponse.pipeline: list[PipelineStageGroup]`로 변경, `PipelineRow` 보존(그룹 내부) | (→ D-1 §옵션A), ANALYSIS.md §2 |
| 2 | `dashboard/backend/routers/tasks.py` | BE | `_group_pipeline_stages(rows)` 신규 + `get_task_detail`에서 행 매핑(`:313-321`)을 그룹 변환으로 교체 | (→ D-2 §2 집계규칙) |
| 3 | `dashboard/backend/tests/test_routers.py` | BE | 그룹 변환 단위(집계규칙) + detail 응답 그룹 스키마 검증 | `test_routers.py` 패턴 |

#### 3.2.2 API·데이터 모델·화면 설계

**데이터 모델 — `PipelineStageGroup`** (옵션 A, ANALYSIS.md §2 권고)

`models.py`에 신규 추가:

```python
class PipelineStageGroup(BaseModel):
    stage: str                       # "TASK" | "PLAN" | "EXECUTE" | "TEST" | "CLOSE" 등
    done_count: int                  # 단계 내 done 행 수
    total: int                       # 단계 내 전체 행 수
    status: str                      # 집계 status: done|in_progress|pending|blocked
    rows: list[PipelineRow] = []     # 단계 내부 행 보존 (디버그/툴팁 확장 여지)
```

`PipelineRow`(`models.py:116-121`)는 **삭제하지 않고 보존** — `PipelineStageGroup.rows`의 내부 타입으로 재사용 (의사결정: rows 보존하여 후속 툴팁/세부 확장 여지 + import 호환).

**스키마 변경 전후 — `TaskDetailResponse.pipeline`**

| 항목 | 변경 전 (`models.py:131`) | 변경 후 |
|------|--------------------------|---------|
| 타입 | `pipeline: list[PipelineRow] = []` | `pipeline: list[PipelineStageGroup] = []` |
| 의미 | 행 1:1 | stage 그룹 1:1 |

> [MUST] 스키마 변경 시 FE `TaskDetail.pipeline` 타입 동시 수정 필수 — 누락 시 상세 Sheet 깨짐 (ANALYSIS.md §4 회귀 리스크, H-1). F-004와 동일 Phase 의존.

**함수 시그니처 — `_group_pipeline_stages`** (D-2 집계 규칙)

```python
def _group_pipeline_stages(rows: list[dict]) -> list[PipelineStageGroup]:
    """rows를 stage 단위로 그룹핑하여 PipelineStageGroup 배열 반환 (BE 단일 소스).

    - stage 등장 순서 보존 (원본 rows 순서 = 파이프라인 진행 순서)
    - 동일 stage의 연속/분산 행을 하나의 그룹으로 합침
    - done_count/total/status 집계 (D-2 규칙)
    """
```

**stage 그룹 변환 알고리즘 의사코드** (등장 순서 보존):

```
groups = []                          # [(stage, [row, ...]), ...] 등장 순서
index = {}                           # stage -> groups 내 위치
for r in rows:
    st = r.get("stage", "")
    if st not in index:
        index[st] = len(groups); groups.append((st, []))
    groups[index[st]][1].append(r)
result = []
for stage, grp_rows in groups:
    result.append(PipelineStageGroup(
        stage=stage,
        done_count=count(status=="done"),
        total=len(grp_rows),
        status=_aggregate_status(grp_rows),     # D-2
        rows=[PipelineRow(...) for r in grp_rows],
    ))
return result
```

**status 집계 규칙 — `_aggregate_status`** (D-2 PM 확정):

```
[MUST] D-2 단계 status 집계:
  ① 하나라도 blocked 있으면          → "blocked"   (blocked 우선)
  ② 전부 done                       → "done"
  ③ 하나라도 in_progress
     또는 혼재(done+pending 섞임)    → "in_progress"
  ④ 전부 pending                    → "pending"
```

의사코드:

```
statuses = [r.get("status", "") for r in grp_rows]
if any(s == "blocked" for s in statuses): return "blocked"           # ①
if all(s == "done" for s in statuses): return "done"                  # ②
if any(s == "in_progress" for s in statuses) or any(s == "done" for s in statuses): return "in_progress"  # ③ (in_progress 또는 done 혼재)
return "pending"                                                       # ④ (전부 pending)
```

> 주: ②에서 전부 done이 걸러진 뒤이므로, ③의 `any done`은 곧 "done+pending 혼재" 또는 "done+in_progress"를 의미 → in_progress로 집계 (D-2 "혼재(done+pending 섞임)→in_progress").

**적용 지점** — `get_task_detail`(`tasks.py:312-335`):

```
rows = state.get("rows", [])
pipeline = _group_pipeline_stages(rows)        # 기존 행 1:1 매핑(:313-321) 교체
...
result = TaskDetailResponse(..., pipeline=pipeline, current_stage=... or _derive_current_stage(rows), ...)
```

빈 rows → `_group_pipeline_stages([])` = `[]` 반환 (H-4: IndexError 없음). state=None 경로(`:303-310`)는 `pipeline` 기본값 `[]` 유지 — 변경 없음.

> [MUST] 그룹핑은 BE 단일 소스 — FE 중복 금지 (TASK.md §제약). 옵션 A가 이를 강화 (ANALYSIS.md §2).
> [MUST] 읽기 전용: 그룹 변환은 메모리 내 read 연산 (TASK.md §제약).

#### 3.2.3 환경 변경

해당 없음.

#### 3.2.4 배치/마이그레이션

해당 없음 (응답 DTO 변경만 — DB/state.json 스키마 불변).

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-006 | R2 그룹핑 | 기능 테스트 | TASK·TASK·PLAN rows → [TASK(total=2), PLAN(total=1)] 2그룹, 등장순서 보존 |
| TS-007 | R2 집계② | 기능 테스트 | 단계 내 전부 done → status="done" |
| TS-008 | R2 집계③(혼재) | 기능 테스트 | done+pending 혼재 단계 → status="in_progress" |
| TS-009 | R2 집계①(blocked) | 기능 테스트 | blocked 포함 단계 → status="blocked" (우선) |
| TS-010 | R2 집계④ | 기능 테스트 | 전부 pending → status="pending" |
| TS-011 | R2 AC(응답) | 통합 테스트 | `get_task_detail` 응답 `pipeline`이 그룹 배열(stage/done_count/total/status 필드) |
| TS-012 | R2 엣지 | 회귀 테스트 | 빈 rows → pipeline=[] (500 없음) |

---

### F-003: FE 카드 현재 단계 표기 가독성 승격

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/frontend/src/pages/tasks/TasksPage.tsx` | FE | `KanbanCard` current_stage 표기를 회색 텍스트(`:172-176`)에서 Badge로 승격, 진행중 컬럼 강조 | (→ D-3 §TASK.md "가독성 승격"), `TasksPage.tsx:172-176` |

#### 3.3.2 API·데이터 모델·화면 설계

##### 화면: 태스크 칸반 — 카드 현재 단계 뱃지

- **ID**: FE-1
- **유형**: dashboard
- **action**: modify
- **경로**: `/tasks`
- **파일**: `dashboard/frontend/src/pages/tasks/TasksPage.tsx`
- **shadcn 컴포넌트**: Badge (이미 import `:30`)
- **UI 작업**: `KanbanCard`(`:117-193`) badge 행(`:161-177`)의 current_stage 렌더 수정. 현재 회색 mono `<span>`(`:172-176`)을 `<Badge>`로 승격하여 가독성↑. 진행중 컬럼(`card.column === "in_progress"`)일 때 status 토큰 강조(예: `border-status-running text-status-running` outline badge), 그 외 컬럼은 secondary/outline 약한 강조. `ml-auto` 우측 정렬 유지. 빈 stage일 때 미표시(`{card.current_stage && ...}` 가드 유지). 색상은 `stageStatusClass`(`:106-111`)/`status-*` 토큰만 사용 — 하드코딩 금지.
- **API 연동**: 없음 (기존 `GET /api/tasks` 응답 `current_stage` 필드 사용 — F-001이 값을 채움). FE 로직 추가 없음(표시 전용).

> [MUST] 색상은 `status-*`/`:root` 토큰만 사용, 하드코딩 금지 (TASK.md §제약 "시그니처 색상 토큰 준수").
> [MUST] 읽기 전용 불변: dnd 비활성·🔒 badge 상시 유지 (`TasksPage.tsx:6` @header, `:531-538`).
> [MUST] 단계 파생 FE 중복 금지 — BE `current_stage` 값을 그대로 표시만 한다 (TASK.md §제약).

#### 3.3.3 환경 변경

해당 없음.

#### 3.3.4 배치/마이그레이션

해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-013 | R1 AC(카드 표시) | 통합 테스트(cmux 실렌더) | 진행중 카드에 비어있지 않은 단계명(TASK/PLAN/EXECUTE/TEST/CLOSE 중 하나)이 강조 뱃지로 표시 |
| TS-014 | R1 가독성 | 통합 테스트(cmux 실렌더) | 진행중 컬럼 카드의 단계 뱃지가 status 토큰으로 강조되어 식별 가능 |

---

### F-004: FE 파이프라인 스테퍼 stage 그룹 렌더

#### 3.4.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/frontend/src/pages/tasks/TasksPage.tsx` | FE | `PipelineRow`/`TaskDetail.pipeline` 타입을 그룹 스키마로 동기 + `PipelineStepper` stage 그룹 렌더로 변경 | (→ D-1 §옵션A), `TasksPage.tsx:64-69,79,244-274` |

#### 3.4.2 API·데이터 모델·화면 설계

**타입 동기 (FE)** — BE `PipelineStageGroup` 계약과 일치 (H-1 방지):

```typescript
interface PipelineRow {          // 보존 (그룹 내부 rows 타입)
  row: number;
  stage: string;
  status: string;
  updated_at: string;
}

interface PipelineStageGroup {   // 신규 — BE PipelineStageGroup 미러
  stage: string;
  done_count: number;
  total: number;
  status: string;                // done|in_progress|pending|blocked
  rows: PipelineRow[];
}

interface TaskDetail {
  ...
  pipeline: PipelineStageGroup[];   // 기존 PipelineRow[] (:79) → 그룹 배열로 변경
  ...
}
```

##### 화면: 태스크 상세 Sheet — 파이프라인 스테퍼 (stage 그룹)

- **ID**: FE-2
- **유형**: detail
- **action**: modify
- **경로**: `/tasks` (우측 Sheet 패널)
- **파일**: `dashboard/frontend/src/pages/tasks/TasksPage.tsx`
- **shadcn 컴포넌트**: (기존 div 기반 스테퍼 — ChevronRight 아이콘 유지)
- **UI 작업**: `PipelineStepper`(`:244-274`) 시그니처를 `{ pipeline: PipelineStageGroup[] }`로 변경. `.map`을 그룹 단위로 렌더 — **단계당 1스텝**(stage명 1회), 각 스텝 점 색상은 그룹 `status`를 `stageStatusClass`(`:106-111`)에 적용, stage 라벨 아래에 `완료/전체` 카운트(예: `EXECUTE 1/1`, `TEST 0/3`) 표시. 그룹 간 `ChevronRight`(`:267-269`) 구분 유지. 빈 pipeline → 기존 "파이프라인 데이터 없음"(`:245-247`) 유지. 동일 stage 라벨 반복이 사라짐 (R2 AC). 색상은 `status-*` 토큰만.
- **API 연동**: `GET /api/tasks/detail?project=&task_id=` 응답 `pipeline`(F-002 그룹 배열) 소비. `TaskDrawer`(`:379`)가 `detail.pipeline`을 그대로 전달 — 호출부 변경 불요(타입만 동기).

렌더 구조(의사):

```
{pipeline.map((g, idx) => (
  <Fragment key={g.stage}>
    <div column-center>
      <div dot className={stageStatusClass(g.status)} />
      <span>{g.stage}</span>
      <span muted>{g.done_count}/{g.total}</span>   // 단계 내 완료/전체
    </div>
    {idx < pipeline.length-1 && <ChevronRight />}
  </Fragment>
))}
```

> [MUST] 단계 그룹핑은 BE 단일 소스 — FE는 BE 그룹 배열을 표시만 하며 그룹핑 로직 중복 금지 (TASK.md §제약, ANALYSIS.md §2 옵션A).
> [MUST] 색상은 `status-*`/`:root` 토큰만 — `stageStatusClass` 재사용, 하드코딩 금지 (TASK.md §제약).

**데이터 흐름 (BE→FE)**:

```
state.json rows[]
  └─(BE) _group_pipeline_stages → PipelineStageGroup[]  ─┐
  └─(BE) _derive_current_stage  → current_stage          │
        get_task_detail 응답 ─────────────────────────────┘
  └─(HTTP) GET /api/tasks/detail
        └─(FE) TaskDrawer useQuery<TaskDetail>
              └─ PipelineStepper(detail.pipeline)  → 단계당 1스텝 + done/total
```

#### 3.4.3 환경 변경

해당 없음.

#### 3.4.4 배치/마이그레이션

해당 없음.

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-015 | R2 AC(중복 제거) | 통합 테스트(cmux 실렌더) | 스테퍼가 stage를 중복 없이 1회씩 순서대로 표시 — `TASK TASK`/`PLAN PLAN PLAN` 반복 사라짐 |
| TS-016 | R2 AC(서브항목) | 통합 테스트(cmux 실렌더) | 각 단계에 완료/전체 카운트(예: `TEST 0/3`)가 표시되어 단계 내 진행 식별 가능 |
| TS-017 | R2 회귀(타입 동기) | 통합 테스트(cmux 실렌더) | 상세 Sheet가 깨지지 않고 정상 렌더(H-1 방지 — 타입 동기 확인) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001, F-002 | 1, 2, 3 | opal-be-agent | 순차(동일 파일 `tasks.py`/`models.py`) | BE 파생+그룹+스키마. FE 선행 의존 |
| 2 | F-003, F-004 | 4 | opal-fe-agent | 단일 Step(동일 파일 `TasksPage.tsx`) | Phase 1 완료 후. 카드+스테퍼+타입 동기 |
| 3 | 문서 | 5 | PM 직접 | 순차 | BACKEND.md/FRONTEND.md 갱신 |

> BE(F-001/F-002)가 FE(F-003/F-004)의 계약(파생값·그룹 스키마) 선행 의존 → Phase 1 → 2. F-003/F-004는 동일 파일(`TasksPage.tsx`) 수정이므로 1 Step으로 묶어 파일 충돌 방지.

### 4.2 실행 체크리스트

> 총 5개 Step | Phase 3개 | 실행 모드: 복잡

#### Step 1: BE 현재 단계 파생 헬퍼 + 적용
- [x] 완료
- **소속 기능**: F-001
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/routers/tasks.py`
- **작업 내용**: `_derive_current_stage(rows: list[dict]) -> str` 헬퍼 신규(규칙 ①in_progress→②첫 미완료→③마지막 done, 빈 rows→""). `_state_to_task_card`(`:199`)·`get_task_detail`(`:333`)에서 `state.get("current_stage") or _derive_current_stage(rows)` 적용. @header `exports`/`description`에 헬퍼 반영, `depends` 검토.
- **완료 기준**: 헬퍼가 3규칙대로 동작(005→TASK, 015→CLOSE), state 있는 카드 `current_stage` 비어있지 않음, 기존 pytest 회귀 없음.
- **테스트**: TS-001~TS-005
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: BE 파이프라인 stage 그룹 스키마 (models)
- [x] 완료
- **소속 기능**: F-002
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/models.py`
- **작업 내용**: `PipelineStageGroup`(stage/done_count/total/status/rows) 신규. `TaskDetailResponse.pipeline` 타입을 `list[PipelineRow]`(`:131`) → `list[PipelineStageGroup]`로 변경. `PipelineRow`(`:116-121`) 보존(그룹 내부 타입). @header `exports`에 `PipelineStageGroup` 추가.
- **완료 기준**: 스키마 임포트 정상, `PipelineRow` 미삭제, mypy/pydantic 검증 통과.
- **테스트**: TS-011 (응답 스키마)
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 1과 독립이나 동일 PR/에이전트 내 순차)

#### Step 3: BE stage 그룹 변환 헬퍼 + detail 적용
- [x] 완료
- **소속 기능**: F-002
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/routers/tasks.py`, `dashboard/backend/tests/test_routers.py`
- **작업 내용**: `_group_pipeline_stages(rows)` + `_aggregate_status(grp_rows)`(D-2: blocked우선→전부done→in_progress/혼재→pending) 신규. `get_task_detail` 행 1:1 매핑(`:313-321`)을 그룹 변환으로 교체(빈 rows→[]). 테스트: `_derive_current_stage` 3규칙·빈 rows, `_group_pipeline_stages` 집계 4규칙·등장순서·빈 rows, detail 응답 그룹 스키마. @header 갱신.
- **완료 기준**: `get_task_detail` `pipeline`이 그룹 배열, 집계 규칙 통과, 빈 rows 500 없음, `cd dashboard/backend && python -m pytest tests/test_routers.py` 전체 통과.
- **테스트**: TS-006~TS-012
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 2

#### Step 4: FE 카드 단계 뱃지 + 스테퍼 그룹 렌더 + 타입 동기
- [x] 완료
- **소속 기능**: F-003, F-004
- **영역**: FE
- **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/pages/tasks/TasksPage.tsx`
- **작업 내용**: (F-003) `KanbanCard` current_stage 회색 텍스트(`:172-176`)를 Badge로 승격, 진행중 컬럼 status 토큰 강조. (F-004) `PipelineStageGroup` 인터페이스 신규 + `TaskDetail.pipeline`(`:79`) 타입 동기, `PipelineRow`(`:64-69`) 보존. `PipelineStepper`(`:244-274`)를 그룹 단위 렌더(단계당 1스텝 + `done_count/total` + `stageStatusClass(g.status)`)로 변경. 색상 `status-*` 토큰만. read-only 불변(dnd 비활성·🔒 badge) 유지. @header 갱신.
- **완료 기준**: `cd dashboard/frontend && npm run build`(tsc) 통과, 진행중 카드 단계 뱃지 표시, 스테퍼 stage 1회씩+카운트 표시, 동일 stage 반복 사라짐, 상세 Sheet 정상 렌더(H-1).
- **테스트**: TS-013~TS-017 (cmux 실렌더)
- **실행 방법**: sub-agent
- **의존**: Step 1 (current_stage 값), Step 3 (그룹 스키마)

#### Step 5: docs/ 갱신 (BACKEND.md / FRONTEND.md)
- [ ] 완료
- **소속 기능**: F-001~F-004
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/BACKEND.md`, `docs/FRONTEND.md` (존재 시)
- **작업 내용**: BACKEND.md에 `get_task_detail` pipeline 그룹 스키마(`PipelineStageGroup`)·`current_stage` 파생 반영. FRONTEND.md에 카드 단계 뱃지·스테퍼 그룹 렌더 반영. (해당 문서 부재 시 스킵 + ARCHITECTURE.md §OPAL Console 응답 계약 변경 검토.)
- **완료 기준**: 변경된 API 응답 계약/컴포넌트가 docs/에 반영(또는 부재 확인).
- **테스트**: 문서 검토
- **실행 방법**: direct
- **의존**: Step 3, Step 4

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 3 | `_group_pipeline_stages` 적용 시 `get_task_detail`에 `_derive_current_stage`도 함께 적용 — 동일 파일 `tasks.py` 순차 |
| Step 2 → Step 3 | Step 3 그룹 변환이 Step 2 `PipelineStageGroup` 모델에 의존 |
| Step 1·2·3 (BE) → Step 4 (FE) | FE가 BE 파생값(current_stage)·그룹 스키마(pipeline)에 의존. 계약 선행 |
| Step 3 ∥ (개념적) Step 4 불가 | FE 타입 동기가 BE 스키마 확정 필요(H-1) → 순차 강제 |
| F-003 + F-004 → 1 Step(Step 4) | 동일 파일 `TasksPage.tsx` 수정 — 파일 충돌 방지 위해 단일 에이전트/Step |
| Step 5 (문서) | Step 3·4 코드 확정 후 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 현재 단계 파생 3규칙 정확성 | TS-001~TS-004 | in_progress→해당stage / 첫 미완료(005=TASK) / 전부done(015=CLOSE) / 빈rows="" |
| F-001 | 카드 current_stage 비어있지 않음 | TS-005 | state 있는 카드 `current_stage != ""` |
| F-002 | stage 그룹 변환·등장순서 | TS-006 | 동일 stage 1그룹 합침, 순서 보존 |
| F-002 | status 집계 4규칙(D-2) | TS-007~TS-010 | 전부done=done / 혼재=in_progress / blocked=blocked우선 / 전부pending=pending |
| F-002 | detail 응답 그룹 스키마 | TS-011 | `pipeline[]`이 stage/done_count/total/status 필드 |
| F-002 | 빈 rows 안전성 | TS-012 | pipeline=[], API 500 없음 |
| F-003 | 진행중 카드 단계 뱃지 가독성 | TS-013, TS-014 | 비어있지 않은 단계명이 status 토큰 강조 뱃지로 표시 |
| F-004 | 스테퍼 stage 중복 제거 | TS-015 | stage 1회씩 순서대로, 반복 사라짐 |
| F-004 | 단계 내 완료/전체 표현 | TS-016 | done_count/total 카운트 표시 |
| F-004 | 상세 Sheet 비파괴(타입 동기) | TS-017 | Sheet 정상 렌더(H-1 방지) |

### 5.2 회귀 테스트
- [ ] `cd dashboard/backend && python -m pytest tests/test_routers.py` 전체 통과 (기존 18개 export 케이스 + 신규)
- [ ] state.json 없는 태스크 카드/상세 동작 유지 (`_infer_column_from_artifacts`, TS-012 빈 경로)
- [x] `cd dashboard/frontend && npm run build` tsc 타입 체크 통과 (TaskDetail.pipeline 타입 동기 누락 없음)
- [ ] 칸반 5컬럼 정렬·진행률·badge 기존 동작 유지

### 5.3 코드/문서 품질
- [x] 변경 4파일 @header `description`/`exports`/`depends` 갱신 (CONVENTIONS §@header 규칙 `docs/CONVENTIONS.md` §170-174) — TasksPage.tsx @header description 스테퍼 그룹 렌더 반영
- [x] [MUST] BE 단일 소스 — FE에 단계 파생/그룹핑 로직 중복 없음
- [x] [MUST] 색상 `status-*`/`:root` 토큰만, 하드코딩 hex 없음
- [ ] docs/ 갱신(BACKEND.md/FRONTEND.md) 반영 또는 부재 확인 (Step 5)

### 5.4 보안
- [x] [MUST] 읽기 전용 불변: state-tool 쓰기 커맨드·파일 편집 없음, dnd 비활성·🔒 badge 상시 유지 (`docs/CONVENTIONS.md` §State, TASK.md §제약)
- [x] 코드에 하드코딩된 토큰/시크릿 없음 (표시 로직만)
- [x] path traversal 등 신규 입력 경로 없음 (응답 가공만 — 신규 query param 미도입)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 5개 | 단순 |
| 변경 파일 수 | 4개 (tasks.py, models.py, TasksPage.tsx, test_routers.py) | 복잡 |
| 모듈 범위 | 다중 (BE 라우터+스키마+테스트, FE 페이지) | 복잡 |
| 작업 유형 | 개선(스키마 변경 + UX 재구성) | 복잡 |
| 외부 의존성 | 없음 (신규 패키지/도구 없음) | 단순 |
| **실행 모드** | **복잡** | (변경 파일 4개·다중 모듈·스키마 변경) |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 (BE):  opal-be-agent  ── Step 1, 2, 3 (tasks.py + models.py + test_routers.py)
                     │ (계약: current_stage 값, PipelineStageGroup 스키마)
                     ▼
Batch 2 (FE):  opal-fe-agent  ── Step 4 (TasksPage.tsx)
                     │
                     ▼
Batch 3 (문서): PM 직접        ── Step 5 (BACKEND.md / FRONTEND.md)
```

**그룹핑 근거**:
- 파일 충돌 방지: `tasks.py`/`models.py`/`test_routers.py`(BE)를 opal-be-agent 단일 에이전트에 집중. `TasksPage.tsx`(F-003+F-004) 단일 Step → opal-fe-agent.
- 모듈 응집도: BE 3 Step은 동일 라우터/스키마 레이어.
- 병렬 극대화: BE↔FE는 계약 선행 의존(H-1)으로 순차 강제 — 병렬 불가.

### C-2. 스킬 요구사항

| 에이전트 | 스킬 | 비고 |
|---------|------|------|
| opal-be-agent | op-dev-execute (EXECUTE 단계 스킬) | 기존 스킬 매칭, 갭 없음 |
| opal-fe-agent | op-dev-execute + ui-designer(plan-driven, §3.4.2 FE-1/FE-2 입력) | FE 화면 설계 §3.N.2 서브섹션 소비 |

> 갭 판별: 신규 패턴 1~2개 Step(그룹 변환·뱃지 승격)은 인라인 지침으로 충분 — 신규 스킬 후보 아님.

### C-3. 도구 요구사항

| 도구 | 용도 |
|------|------|
| python -m pytest (BE) | 회귀 + 신규 단위 |
| npm run build / tsc (FE) | 타입 체크 (H-1 동기 검증) |
| cmux/playwright (TEST) | 상세 Sheet 실렌더 시각 확인 (TS-013~017) |

신규 패키지 설치 없음.

### C-4. 테스트 전략

- **기능 테스트**: `dashboard/backend/tests/test_routers.py` — `_derive_current_stage`(TS-001~005)·`_group_pipeline_stages`/`_aggregate_status`(TS-006~012). 실행: `cd dashboard/backend && python -m pytest tests/test_routers.py -v`.
- **회귀 테스트**: 동일 스위트 전체 통과(기존 케이스 비파괴). FE `npm run build` 타입 체크.
- **통합/실렌더**: cmux로 Console 기동 후 진행중 카드 단계 뱃지(TS-013/014) + 상세 Sheet 스테퍼 그룹 렌더(TS-015~017) 시각 확인.
- **코드 품질**: ruff(BE)/tsc(FE), @header 갱신 확인.
- **보안**: read-only 불변(state-tool 쓰기/파일편집 부재) 확인.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| BE | Python 3 / FastAPI / Pydantic / pytest | trailofbits/modern-python (async/타입 패턴) |
| FE | React + TypeScript + Vite + shadcn/ui + TanStack Query | vercel-labs/react-best-practices, shadcn |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (미사용) | 기존 코드 패턴(stageStatusClass·Badge·TanStack Query) 재사용으로 충분 — 신규 라이브러리 API 조회 불요 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | TASK.md | `tasks/023-260616-opd-kanban-stage-pipeline-ux/TASK.md` | R1/R2 요구사항·AC·제약(read-only/BE단일소스/색상토큰)·옵션A 확정 |
| D-2 | 설계 | ANALYSIS.md | `tasks/023-260616-opd-kanban-stage-pipeline-ux/ANALYSIS.md` | 근본원인·파생규칙 실데이터검증·옵션A 권고·status 집계·변경파일 |
| D-3 | 소스 | tasks 라우터 | `dashboard/backend/routers/tasks.py:170-340` | `_state_to_task_card`/`get_task_detail` 현 구현·rows 보유·캐시 |
| D-4 | 소스 | models 스키마 | `dashboard/backend/models.py:104-133` | `PipelineRow`/`TaskDetailResponse.pipeline` 현 스키마 |
| D-5 | 소스 | 칸반 페이지 | `dashboard/frontend/src/pages/tasks/TasksPage.tsx:64-274` | KanbanCard·PipelineStepper·타입·stageStatusClass 현 구현 |
| D-6 | 소스 | 라우터 테스트 | `dashboard/backend/tests/test_routers.py:344-368` | 회귀 테스트 추가 위치·헬퍼 직접 호출 패턴 |
| D-7 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` §170-186 | @header 규칙·State(read-only) 인용 의무 |

> [MUST] `docs/CONVENTIONS.md` §182-186 State: "파이프라인 STATE.md 행 상태 변경은 state-tool로만 수행한다" → 본 태스크는 read-only 표시 로직만 변경, state-tool 미호출.
> [MUST] `docs/CONVENTIONS.md` §170-172 @header: "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다" → 변경 4파일 @header 갱신을 §5.3·Step에 포함.

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 1 | pipeline 스키마 변경 시 FE 타입 미동기 → 상세 Sheet 깨짐 (H-1) | F-002, F-004 | P1 | Step 4에서 `PipelineStageGroup` 타입 동시 동기 + `npm run build` tsc 게이트 + cmux 실렌더(TS-017) |
| 2 | status 집계 혼재(done+pending) 오집계 (H-3) | F-002 | P1 | D-2 규칙 명문화(②전부done 후 ③any done=혼재→in_progress) + TS-008 단위 |
| 3 | 전부 done 태스크 빈 stage (H-2) | F-001 | P1 | 규칙③ 마지막 행 stage 폴백 + TS-003(015=CLOSE) |
| 4 | 빈 rows / state=None 경로 500 (H-4) | F-001, F-002 | P1 | 빈 rows→""/[] 가드 + TS-004/TS-012, state=None 경로 무변경 |
| 5 | 색상 하드코딩으로 테마 깨짐 (H-5) | F-003, F-004 | P2 | `stageStatusClass`/`status-*` 토큰만 재사용, §5.3 체크 |
| 6 | read-only 계약 위반(쓰기 유입) (H-6) | 전체 | P0 | 전 변경 read 한정(파생·그룹·표시), state-tool 미호출, §5.4 보안 체크 |
