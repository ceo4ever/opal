# ANALYSIS: OPAL Console 태스크 진행 통계

> 작성일: 2026-08-25 | 입력: TASK.md (2026-08-25 15:10 재작성본) | 출력: ANALYSIS.md
> 트랙: 개발 (citation-rules §1.5) | 분석 깊이: 기능 개선 — 변경 대상 + 직접 의존 (analysis-core §4)

---

## 확정 입력 판정

### (A) `[결정]` 태그 9건 — 결정 계열

| 항목 | 판정 | 근거 |
|------|------|------|
| D-1 통계 목적 2개(병목 개선·캡틴 대기 축소), 2계열 분해가 둘을 함께 답한다 (`TASK.md:19`) | 해당없음(결정) | - |
| D-2 A-1~A-4·B-1~B-4 8블록 전부 채택 (`TASK.md:110`) | 해당없음(결정) | - |
| D-3 통계 목적은 2개이며 작업·대기 2계열 분해로 답한다 (`TASK.md:111`) | 해당없음(결정) | - |
| D-4 소요 계산은 집계 기준 1~2, 근무시간 보정·야간 공백 제외 미적용 (`TASK.md:112`) | 해당없음(결정) | - |
| D-5 범위는 상세+대시보드 양쪽, 통계 전용 화면 신설 없음 (`TASK.md:113`) | 해당없음(결정) | - |
| D-6 집계 정의를 `stats.py` 순수 모듈 1곳에 격리, FE 무계산 (`TASK.md:114`) | 해당없음(결정) | - |
| D-7 칸반 읽기 전용 유지, 통계 블록도 조회 전용 (`TASK.md:115`) | 해당없음(결정) | - |
| D-8 상세 Sheet 2탭 분리, 기본 활성 「태스크 대시보드」 (`TASK.md:116`) | 해당없음(결정) | - |
| D-9 B-4를 워크플로우 필터 진입점으로 승격 (`TASK.md:117`) | 해당없음(결정) | - |

### (B) `[사실]` 태그 4건 — 사실 계열

| 항목 | 판정 | 근거 |
|------|------|------|
| F-1 `done` 262행 전건이 `timestamp`·`owner` 보유 → 추가 계측 불필요 (`TASK.md:118`) | **수정필요** | 주장(전건 보유·추가 계측 불필요)은 확인. 수치만 이동 — 재측정 시 done **263**행·`in_progress` 1행·`pending` 28행·`na` 11행(합 303). `done` 행 `timestamp` 결측 0건, `owner` 결측 0건. TASK.md 작성(15:07) 후 103 자신의 `task.user_confirm` 행이 15:09에 done 전환되어 발생한 자기참조 이동 (`tasks/103-260825-opd-태스크-진행통계/state.json:24-33`). E1 — 스코프: `tasks/*/state.json` 23파일 전수, 명령 `python3` 인라인 집계 |
| F-2 `PipelineRow`가 `owner`·`gate`·`note`·`key` 미노출 → 응답 모델 확장 선행 (`TASK.md:119`) | 유효(대조 확인) | `dashboard/backend/models.py:136-140` — 필드 4개(`row`·`stage`·`status`·`updated_at`)뿐. E2 |
| F-3 집계 엔드포인트·차트 컴포넌트·30초 TTL 캐시 기존재 → B는 확장 (`TASK.md:120`) | 유효(대조 확인) | `dashboard/backend/routers/dashboard.py:109-110`(엔드포인트)·`:46`(전 태스크 수집), `dashboard/frontend/src/pages/dashboard/DashboardPage.tsx:132`·`:168`·`:253`·`:375`(4컴포넌트), `dashboard/backend/cache.py:17`(TTL 30초). E2 |
| F-4 `pending` 행 `owner`는 `init` 기본값이라 실시간 대기 귀속에 쓸 수 없다 (`TASK.md:121`) | 유효(대조 확인) | 실측 `pending` 28행 **전건** `owner=PM`, 예외 0건. E1 — 스코프: `tasks/*/state.json` 23파일 전수 |

### (C) 집계 기준 14항목 — 결정 계열 (캡틴 확정, `TASK.md:92-107`)

| # | 항목 | 판정 | 근거 |
|---|------|------|------|
| 1 | 소요 앵커 = `created_at` → 각 done 행 차분 | 해당없음(결정) | - |
| 2 | 제외 행 = `pending`·`na` | **사실오류** | 열거 누락 — 실측 행 상태에 `in_progress`가 존재한다(103 `analysis.analysis_md` 1행, `tasks/103-260825-opd-태스크-진행통계/state.json:34-43`). 기준 1이 "각 done 행"으로 한정하므로 결과는 동일하나, 기준 2의 열거만으로 구현하면 `in_progress` 행이 합산에 섞인다. §8 확정값 참조. E1 |
| 3 | 모수 = B는 완료만 / A는 실시간 | 해당없음(결정) | - |
| 4 | 비교 단위 = 워크플로우(`skill`)별, 혼합 미제공 | 해당없음(결정) | - |
| 5 | 대표값 = 중앙값 주·평균 보조, n<5 「표본 부족」 | 해당없음(결정) | - |
| 6 | 2계열 = `owner=user` 대기 / `PM`·`auto` 작업 | 해당없음(결정) | - |
| 7 | 게이트 = `gate` 키 존재, 092 이전 「미기록」 | 해당없음(결정) | - |
| 8 | 블로커 = 행 `status=failed`, 현재 전건 0 | 해당없음(결정) | 부수 확인: `failed` 행 실측 0건. E1 |
| 9 | 산출물 = 화이트리스트 폐기, `.md` 전수 + 유형 분류 | 해당없음(결정) | - |
| 10 | 검증 = `STATS-BASELINE.md` 1회 생성 후 대조 | 해당없음(결정) | - |
| 11 | 실시간 총 리드타임 = 진행 중이면 현재 시각까지 | 해당없음(결정) | - |
| 12 | 현재 행 = `in_progress` 우선, 없으면 첫 `pending` | 해당없음(결정) | - |
| 13 | 현재 행 소요 = 직전 done 행 → 현재 시각 | 해당없음(결정) | - |
| 14 | 실시간 대기 귀속 = 완료 행 `owner`, 현재 행 `key`의 `*.user_confirm` | 해당없음(결정) | - |

---

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | TASK.md (103) | `tasks/103-260825-opd-태스크-진행통계/TASK.md` | 확정 입력·집계 기준 14항목·R-1~R-14 원천 |
| D-2 | 설계 | 시스템 아키텍처 | `docs/ARCHITECTURE.md` §OPAL Console | 읽기 전용 원칙·라우터/어댑터 구조·쓰기 예외 2건의 경계 |
| D-3 | 설계 | 코드 및 문서 컨벤션 | `docs/CONVENTIONS.md` §구현 규칙 | @header·Citation·State·배포 경계·플랫폼 분기 격리 |
| D-4 | 소스 | 태스크 라우터 | `dashboard/backend/routers/tasks.py` | 상세 응답 생성부 — R-2·R-3·R-4·집계기준 9 대상 |
| D-5 | 소스 | 응답 모델 | `dashboard/backend/models.py` | `PipelineRow`·`PipelineStageGroup`·`DashboardSummaryResponse` — R-2·R-10 대상 |
| D-6 | 소스 | 대시보드 라우터 | `dashboard/backend/routers/dashboard.py` | 기존 집계 경로 — R-10 확장 대상 |
| D-7 | 소스 | TTL 캐시 | `dashboard/backend/cache.py` | 30초 TTL + mtime 무효화 계약 — 성능 제약 근거 |
| D-8 | 소스 | 태스크 칸반 화면 | `dashboard/frontend/src/pages/tasks/TasksPage.tsx` | 상세 Sheet·`@header` 읽기 전용 — R-5~R-9 대상 |
| D-9 | 소스 | 대시보드 화면 | `dashboard/frontend/src/pages/dashboard/DashboardPage.tsx` | 기존 차트·`ToggleGroup` 필터 패턴 — R-11 대상 |
| D-10 | 소스 | 전역 디자인 토큰 | `dashboard/frontend/src/index.css` | 시그니처 3색·상태색 5종·hex 금지 — R-13 근거 |
| D-11 | 소스 | UI 상태 스토어 | `dashboard/frontend/src/store/ui-store.ts` | `contextProject` 패턴 — 워크플로우 필터 상태 위치 판정 |
| D-12 | 소스 | 라우터 계약 테스트 | `dashboard/backend/tests/test_routers.py` | `PipelineRow` 확장 시 회귀 판정 |
| D-13 | 설계 | state.json 스키마 | `~/.opal/tools/state-tool/schema/state.schema.json` | `gate`·`owner`·`status` 필드 도메인 — 직렬화 모델 근거 |
| D-14 | 소스 | state-tool README | `~/.opal/tools/state-tool/README.md` | 행 갱신 경로·`--owner`·`--auto-pass` 의미 |
| D-15 | 기획 | 승인 목업 3화면 | `tasks/103-260825-opd-태스크-진행통계/mockup/` | A-1~A-4·B-1~B-4 시각 형태 근거 |
| D-16 | 설계 | DONE.md (021) | `tasks/backup/021-260615-opd-opal-console/DONE.md` | Console 신설 결정 C-2/C-12·Sheet 통일 규격 |
| D-17 | 설계 | DONE.md (023) | `tasks/backup/023-260616-opd-kanban-stage-pipeline-ux/DONE.md` | `PipelineStageGroup` 도입·"파생은 BE 단일 소스" 선례 |

**선조회 3단 결과 (analysis-core §1)**

- **1단 brain** — PM 선조회 승계: `brain-tool search "대시보드 통계 state.json 집계"` **0건**(total 0). 재도출하지 않음.
- **2단 code-scan** — PM 선조회 승계: `code-scan search "dashboard"` 7파일(`main.py`·`models.py`·`routers/dashboard.py`·`tests/test_routers.py`·`tests/test_deploy_smoke.py`·`DashboardPage.tsx`·`router.tsx`). 재도출하지 않음. **주의**: `.opal/code-scan.json` `exclude`에 `tasks`가 포함되어 태스크 산출물은 code-scan 색인 대상이 아니다.
- **3단 docs 레지스트리** — `docs/ARCHITECTURE.md`·`docs/CONVENTIONS.md` 2건 참조(D-2·D-3).
- **3단-B 과거 태스크 산출물 — 수행함**. 트리거 **T1 참**(1단 brain 0건). 조회 대상: `tasks/backup/021-*`(Console 신설, D-16)·`tasks/backup/023-*`(파이프라인 그룹 스키마, D-17)·`tasks/backup/061-*`(설정 라우터 — `docs/ARCHITECTURE.md` §프로젝트별 환경 설정 화면으로 대체 확인). 결과: 023 DONE §3 "단계 파생은 BE 단일 소스 — FE는 표시만(중복 로직 금지)"가 D-6(`stats.py` 격리, FE 무계산)의 직접 선례다.

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 영역 | 경로 | 역할 | 변경 유형 | 근거(줄번호) |
|------|------|------|----------|-------------|
| BE | `dashboard/backend/stats.py` | 집계 정의 SSOT 순수 모듈 — 소요·2계열·워크플로우별 집계·실시간 파생 | 신규 | `TASK.md:114` (D-6) |
| BE | `dashboard/backend/models.py` | `PipelineRow` 5필드 확장 + `PipelineGate`·통계 응답 모델 신설 + `TaskDetailResponse`·`DashboardSummaryResponse` 확장 | 수정 | `dashboard/backend/models.py:136-140`, `:143-148`, `:151-161`, `:84-92` |
| BE | `dashboard/backend/routers/tasks.py` | `get_task_detail`에 소요·실시간 파생 결합, `_group_pipeline_stages` 행 매핑 교정, `_get_artifact_files` 화이트리스트 폐기 | 수정 | `dashboard/backend/routers/tasks.py:259-267`, `:414-434`, `:89-96` |
| BE | `dashboard/backend/routers/dashboard.py` | `get_dashboard`에 워크플로우별 집계 결합 (`stats.py` 호출) | 수정 | `dashboard/backend/routers/dashboard.py:136-138`, `:210-221` |
| BE | `dashboard/backend/cache.py` | 캐시 계약 — 변경 없음, 호출부에서 `source_path` 전달로 활용 | 수정 없음 | `dashboard/backend/cache.py:17`, `:43-52`, `:56-59` |
| BE | `dashboard/backend/tests/test_routers.py` | `stats.py` 집계·`PipelineRow` 확장·결측 내성 RED-first 케이스 추가 | 수정 | `dashboard/backend/tests/test_routers.py:567`, `:627-660`, `:665-668` |
| FE | `dashboard/frontend/src/pages/tasks/TasksPage.tsx` | 상세 Sheet 2탭 재구성 + A-1~A-4 렌더 + 타입 동기 | 수정 | `dashboard/frontend/src/pages/tasks/TasksPage.tsx:1-9`, `:62-88`, `:383-427` |
| FE | `dashboard/frontend/src/pages/dashboard/DashboardPage.tsx` | B-1~B-4 렌더 + 워크플로우 필터 + 타입 동기 | 수정 | `dashboard/frontend/src/pages/dashboard/DashboardPage.tsx:55-88`, `:168-195`, `:436-441` |
| FE | `dashboard/frontend/src/index.css` | 시그니처 3색·상태색 5종 토큰 — 조회 전용, 신규 색 추가 불필요 | 수정 없음 | `dashboard/frontend/src/index.css` `:root` (`--brand-primary`/`--status-*` 5종) |
| 환경 | `dashboard/frontend/package.json` | recharts 3.8.1 기보유 — 스택 막대에 추가 의존 불필요 | 수정 없음 | `dashboard/frontend/package.json` `dependencies.recharts` |
| 공통 | `tasks/103-260825-opd-태스크-진행통계/STATS-BASELINE.md` | 기준일 2026-08-25 스냅샷 — 완료기준 대조 원천 | 신규 | `TASK.md:206-210` (R-14) |

> 변경 유형 값 도메인은 `신규`/`수정`이나, 「참조는 하되 편집하지 않음」이 확정된 3건은 `수정 없음`으로 명시했다 — PLAN이 이 3건을 편집 대상으로 오인하지 않도록 하기 위함이다.

### 1.2 아키텍처 패턴

- **읽기 전용 대시보드**가 기본 원칙이며, 쓰기 예외는 브레인 질의 라우터·설정 라우터 2곳으로만 격리돼 있다 (`docs/ARCHITECTURE.md` §OPAL Console). 본 태스크는 GET 경로만 건드리므로 예외를 늘리지 않는다.
- **파생은 BE 단일 소스** — `_derive_current_stage`·`_aggregate_status`·`_group_pipeline_stages` 3헬퍼가 `tasks.py`에 모여 있고 FE는 표시만 한다 (`dashboard/backend/routers/tasks.py:174-269`). 023 DONE §3이 이 규약을 명문화했다 (D-17). D-6의 `stats.py` 격리는 같은 규약의 연장이며, 단 **소유 위치가 라우터에서 순수 모듈로 이동**하는 점이 새롭다.
- **응답 모델은 additive 확장** — 078이 `MemoryRowResponse.title`·`HistoryRowResponse.result`를 기본값 있는 additive로 추가하고 FE 미사용 상태로 두었다 (`dashboard/backend/models.py:36`, `:172`, `:182`). `PipelineRow` 확장도 이 선례를 따르면 하위 호환이 유지된다.
- **절대경로는 query param** — path segment 금지 (`dashboard/backend/routers/tasks.py:75-86`, `dashboard/frontend/src/router.tsx` `@header`). 신규 파라미터(워크플로우 필터)도 query param을 쓰거나 FE 로컬 필터로 처리한다.
- **캐시는 라우터 진입 직후 조회 → 응답 직전 저장** 패턴 (`dashboard/backend/routers/tasks.py:398-401`, `:433`).

### 1.3 의존성 맵

- `main.py` → `routers.dashboard`·`routers.tasks` 포함 7라우터 등록 (`dashboard/backend/main.py:30`, `:95-101`).
- `routers/tasks.py` → `models`·`scanner`·`config`·`cache`·`parsers.markdown_reader` (`dashboard/backend/routers/tasks.py:16`, `:28-37`).
- `routers/dashboard.py` → `models`·`scanner`·`config`·`cache`, 그리고 **`routers.tasks.COLUMN_MAP`을 함수 내부에서 지연 import** (`dashboard/backend/routers/dashboard.py:151`). 이미 두 라우터가 결합돼 있으므로 `stats.py` 공유 호출은 새로운 결합이 아니라 **기존 결합을 순수 모듈로 정리**하는 방향이다.
- 신설 `stats.py`의 의존은 표준 라이브러리(`datetime`·`statistics`)만으로 충분하다 — 라우터·캐시·모델 어느 쪽에도 의존하지 않는 순수 모듈로 둘 수 있다(모델 의존을 넣으면 라우터↔모델↔stats 순환 위험이 생긴다).
- FE: `TasksPage.tsx` → `api`·shadcn 8종·`MarkdownView`·`ui-store` (`dashboard/frontend/src/pages/tasks/TasksPage.tsx:8`). `DashboardPage.tsx` → `api`·`recharts`·`card`/`badge`/`table`/`skeleton`/`toggle-group`·`ui-store` (`dashboard/frontend/src/pages/dashboard/DashboardPage.tsx:8`).
- 순환 의존 없음.

### 1.4 테스트 현황

- **BE(pytest)** — `dashboard/backend/tests/` 10파일. 파이프라인 관련 계약은 `test_routers.py`에 집중: `test_group_pipeline_order`(`:567`), `test_detail_pipeline_groups`(`:627`), `test_detail_empty_rows`(`:665`), `test_aggregate_*` 4종(`:585`~`:613`), `test_derive_stage_*` 6종(`:516`~`:543`, `:718`, `:731`), `state.json` 부재 추론 4종(`:394`~`:451`). RED-first 규약이 `@header`에 명시돼 있다 (`dashboard/backend/tests/test_routers.py:6`).
- **`PipelineRow` 확장의 회귀 영향은 0건**으로 판정한다 — 기존 계약 검증은 `PipelineStageGroup`의 `stage`/`done_count`/`total`/`status` 4속성만 `hasattr`로 확인하고 `PipelineRow` 필드를 직접 assert하지 않는다 (`dashboard/backend/tests/test_routers.py:653-660`). 신규 5필드를 전부 기본값 있는 additive로 추가하면 기존 케이스는 그대로 통과한다.
- **FE(vitest)** — `happy-dom` + `@testing-library/react` 구성 (`dashboard/frontend/vitest.config.ts`). 현재 테스트 7파일이 전부 `lib/`·`pages/brain/`에 있고 **`TasksPage`·`DashboardPage`에 대한 컴포넌트 테스트는 0건**이다. A/B 블록의 렌더 AC를 FE 테스트로 잡으려면 신규 테스트 파일이 필요하다.
- 실행 명령:

```bash
python3 -m pytest dashboard/backend/tests/test_routers.py
cd /Volumes/Data/AIStudio/workspace/ai-framework/dashboard/frontend && npm run test && npm run build
```

---

## 2. 외부 조사 결과

### 2.1 라이브러리/API 조사

- **외부 조사 불필요** — 신규 외부 의존이 0건이다. 스택 막대(A-2·B-2)는 이미 설치된 recharts 3.8.1의 `BarChart`+`stackId`로 구현 가능하며, 현행 코드는 `AreaChart`·`PieChart`만 사용 중이라 `BarChart` import만 추가된다 (`dashboard/frontend/src/pages/dashboard/DashboardPage.tsx:14-27`). 탭은 `@radix-ui/react-tabs` 기반 `components/ui/tabs.tsx`가 이미 상세 Sheet에서 쓰이고 있다 (`dashboard/frontend/src/pages/tasks/TasksPage.tsx:399`).
- 중앙값·평균은 Python 표준 `statistics` 모듈로 충분하다 — numpy/pandas 도입 불필요.

### 2.2 버전 호환성

| 대상 | 버전 | 비고 |
|------|------|------|
| recharts | ^3.8.1 | `BarChart`/`stackId` 지원 — 추가 설치 없음 |
| React | ^19.2.6 | - |
| TypeScript | ~6.0.2 (`tsc -b` 빌드 게이트) | 타입 동기 누락 시 빌드 실패 |
| FastAPI/Pydantic | `models.py`가 `pydantic.BaseModel` v2 스타일 | `dashboard/backend/models.py:44` |
| state.json schema_version | `1.0` 또는 `1.1` 병행 | 1.0은 `key` 없음 — `*.user_confirm` 패턴 판정이 무력화될 수 있다 (`~/.opal/tools/state-tool/schema/state.schema.json`) |

> 실측: 현재 `tasks/*/state.json` 23건은 전부 행에 `key`를 보유한다(결측 0). 1.0 레거시는 `tasks/backup/` 쪽에만 존재할 수 있으나 `_collect_all_tasks`는 `tasks/` 직하만 스캔한다 (`dashboard/backend/routers/dashboard.py:48-53`).

---

## 3. 영향 범위

### 3.1 직접 영향

- `dashboard/backend/stats.py` (신규) — 집계 정의 SSOT.
- `dashboard/backend/models.py` — `PipelineRow` 5필드 additive, `PipelineGate` 신설, `TaskDetailResponse`·`DashboardSummaryResponse` additive 확장.
- `dashboard/backend/routers/tasks.py` — `get_task_detail` 응답 조립, `_group_pipeline_stages` 행 매핑, `_get_artifact_files` 산출물 열거.
- `dashboard/backend/routers/dashboard.py` — `get_dashboard` 응답 조립.
- `dashboard/frontend/src/pages/tasks/TasksPage.tsx` — Sheet 본문 구조 + 통계 4블록.
- `dashboard/frontend/src/pages/dashboard/DashboardPage.tsx` — 통계 4블록 + 필터.
- 변경되는 인터페이스: `GET /api/tasks/detail` 응답(additive), `GET /api/dashboard` 응답(additive), `GET /api/tasks` 응답의 `artifact_count` **값**(스키마 불변, 값 변동).

### 3.2 간접 영향

- **`_get_artifact_files` 폐기의 3중 소비자** — 이 함수는 `TaskDetailResponse.artifacts`(`dashboard/backend/routers/tasks.py:409`, `:430`)뿐 아니라 `TaskCardResponse.artifact_count`(`:283`, `:304`)와 아카이브 카드(`:361`)에서도 호출된다. 화이트리스트를 `.md` 전수로 바꾸면 **칸반 카드의 산출물 개수 배지가 전 카드에서 동반 변동**한다(101 기준 5 → 9). 완료기준 (7) "기존 기능 회귀 없음"과의 경계를 PLAN이 명시해야 한다.
- **산출물 탭 목록 확장** — `.md` 전수 전환 시 `STATE.md`·`AGENTIC-LOG.md`·`GC-CONVENTION-*.md`·`SCENARIO-GATE-*.md`가 탭에 노출된다. 집계기준 9의 "유형 분류"가 여기서 필요하다.
- **테스트** — `test_routers.py`의 산출물 추론 케이스 4종(`:394`~`:451`)이 `_get_artifact_files` 결과를 간접 사용하는지 PLAN 단계에서 확인 대상.
- **배포** — `scripts/install-mac.sh`의 `install_dashboard()`가 `dashboard/` 패키지 구조를 그대로 복사하므로, `stats.py` 신규 파일은 별도 배포 스크립트 수정 없이 포함된다 (D-16 §2). `test_deploy_smoke.py`가 배포 컨텍스트 기동을 검증한다.
- **설정/환경변수·DB·CI 변경 없음.**

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음 (DB 없음, 원천은 `state.json` 파일)
- [x] API 인터페이스 변경 — `GET /api/tasks/detail`·`GET /api/dashboard` **additive 확장**. 기존 필드 제거·타입 변경 0건 → 하위 호환 유지
- [ ] 설정/환경변수 변경 — 해당 없음
- [ ] 빌드/배포 파이프라인 변경 — 해당 없음 (신규 파일은 기존 패키지 복사 경로에 포함)
- [x] 공유 라이브러리 변경 — `stats.py`를 `tasks.py`·`dashboard.py` 두 라우터가 공유. 순환 import 방지를 위해 `stats.py`는 라우터·모델에 의존하지 않는 순수 모듈로 둔다

---

## 4. 핵심 발견 사항

**(1) `PipelineRow`의 기존 2필드는 원천에 존재하지 않는 죽은 필드다.**
`_group_pipeline_stages`는 행을 `row`·`updated_at` 키에서 읽어 매핑한다 (`dashboard/backend/routers/tasks.py:259-267`). 그러나 `state.json` 행 키 합집합은 `row_id`·`stage`·`item`·`key`·`status`·`status_label`·`timestamp`·`owner`·`note`·`gate`·`step` 11종이며 **`row`·`updated_at`은 어느 태스크에도 없다**(E1 — 스코프: `tasks/*/state.json` 23파일 전수, 행 303건). 결과적으로 `PipelineRow.row`는 항상 **그룹 내부 0-based enumerate 인덱스**로 폴백하고, `PipelineRow.updated_at`은 **전건 빈 문자열**이다. R-2가 `timestamp`를 추가하면 `updated_at`과 의미 중복이 생기고, R-9(A-4에 19행 렌더 + 행 식별)는 `row`가 아니라 `row_id`를 필요로 한다. 선재 결함이므로 R-2 범위 안에서 함께 교정해야 한다.

**(2) 캐시는 30초 TTL만 유효하고 mtime 무효화는 이 두 경로에서 작동하지 않는다.**
`CacheStore.get`은 `source_path`가 지정된 항목에 한해 `os.path.getmtime()` 비교로 무효화한다 (`dashboard/backend/cache.py:43-52`). 그런데 `task_detail`·`tasks_list`·`dashboard` 세 호출부 모두 **`source_path`를 넘기지 않고** 캐시에 저장한다 (`dashboard/backend/routers/tasks.py:377`, `:411`, `:433`, `dashboard/backend/routers/dashboard.py:220`). 따라서 F-3의 "30초 TTL + mtime 무효화 캐시" 중 실제 작동하는 것은 TTL 축뿐이다. 실시간 파생(집계기준 11·13)을 응답에 그대로 캐시하면 값이 최대 30초 정지하고, 분 단위 표시에서 최대 1분 오차가 난다.

**(3) 타임스탬프 역행 행이 실재한다 — 음수 소요.**
`086-260810-opp-아키텍처-다이어그램-재작성`의 `plan.user_confirm` 행은 직전 done 행 `15:47`보다 이른 `15:46`을 갖는다(E1 — 스코프: `tasks/*/state.json` 23파일 전수 앵커 차분). 소요 −1분이 발생하며, clamp 없이 합산하면 워크플로우 집계(opp n=4, 표본 부족 구간)가 왜곡되고 스택 막대가 음수 폭으로 깨진다. TASK.md 어디에도 기재되지 않은 신규 사실이며, R-12 「결측 내성」의 3경로(부재·빈 rows·파싱 실패) 밖에 있다.

**(4) R-5의 산출물 배지 AC(101=9)는 BE 변경에 의존한다.**
R-5는 변경 위치를 `TasksPage.tsx`로만 지정하나(`TASK.md:151-155`), 현행 화이트리스트 6종으로 101을 세면 5개다(`TASK.md`·`PLAN.md`·`DONE.md`·`TEST-SCENARIO.md`·`ANALYSIS.md`). 9는 `.md` 전수 값이다(추가 4: `AGENTIC-LOG.md`·`GC-CONVENTION-260824.md`·`SCENARIO-GATE-1.md`·`STATE.md`, E1). 즉 R-5 AC 충족은 집계기준 9(화이트리스트 폐기, `dashboard/backend/routers/tasks.py:89-96`) **선행**을 전제한다 — FE 단독으로는 달성 불가.

**(5) 승인 목업의 B 블록은 TASK.md 재작성본에 의해 이미 폐기됐다.**
목업(14:15 승인)의 B-1은 혼합 리드타임 중앙값 「5시간 42분」(=342분)을, B-2는 혼합 단계별 평균을, B-4는 「스킬·모드 분포」를 제시한다 (`mockup/dashboard.html`). 그러나 TASK.md 재작성본(15:07)의 집계기준 4는 혼합 집계를 **미제공**으로 확정했고, D-9는 B-4를 **워크플로우 필터 진입점**으로 승격했다. A-1도 목업 4타일(총 리드타임/완료 단계/캡틴 확인 대기/게이트·블로커)과 R-6 AC 4타일(총 리드타임/작업/대기·비중/최장 단계)이 다르다. TO-BE 근거 서열상 소유자 결정·요구사항 문서가 설계 산출물보다 상위이므로(citation-rules §9 (b)) **TASK.md가 이긴다**. 목업은 레이아웃·정보 밀도의 시각 형태 근거로만 계승한다.

**(6) 실측 재검증 결과 TASK.md §배경 분석의 수치 4건이 이동했고, 그중 1건은 편차가 크다.**

| 항목 | TASK.md 기재 | 재측정(2026-08-25) | 성격 |
|------|-------------|-------------------|------|
| 행 상태 분포 | done 262 · pending 30 · na 11 | done 263 · in_progress 1 · pending 28 · na 11 | 자기참조 이동 + `in_progress` 누락 |
| `owner` 분포 | PM 225 · auto 43 · user 35 | PM 224 · auto 43 · user 36 | 자기참조 이동 |
| `*.user_confirm` 중 `owner=auto` | 33건 | **41건** (전체 `user_confirm` 87행) | 편차 8건 — 재산출 필요 |
| 화이트리스트 교집합 | 92개 (48%) | 91개 | 편차 1건 |

`.md` 전수 192개·완료 21건/전체 23건·워크플로우별 중앙값 799/276/75분·대기 비중 21%/4%/54%·단계별 모수(EXECUTE 21·TEST 17·TEST-SCENARIO 7)·101의 425분=105+320(75%)과 단계별 7행 분해는 **전건 일치**했다(E1 — 스코프: `tasks/*/state.json` 23파일 전수 + `tasks/*/` `.md` 파일 수, 명령 `python3` 인라인 집계). 이동하는 수치는 R-14 `STATS-BASELINE.md`가 흡수해야 하며, 베이스라인에는 값뿐 아니라 **모수를 구성한 태스크 ID 목록**을 함께 적어야 한다.

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-A1 음수 소요 | 역행 타임스탬프 1건으로 소요가 −1분이 된다. clamp 없으면 합계 왜곡·막대 렌더 파손 | **High** | `tasks/086-260810-opp-아키텍처-다이어그램-재작성/state.json` `plan.user_confirm` (E1, 전수 스캔) |
| R-A2 `updated_at`/`row` 사표 | 원천에 없는 필드를 매핑 중 — A-3·A-4가 행 식별·시각을 이 필드에서 읽으면 전건 공백 | **High** | `dashboard/backend/routers/tasks.py:259-267` vs 행 키 합집합 11종(E1) |
| R-A3 산출물 카운트 동반 변동 | 화이트리스트 폐기가 칸반 카드 `artifact_count`까지 바꾼다 — 회귀 판정과 충돌 소지 | **High** | `dashboard/backend/routers/tasks.py:89-96`, `:283`, `:304`, `:361` |
| R-A4 완료기준 수치의 이동 모수 | 완료기준 (3)의 799/276/75분은 완료 opd 7·opds 10·opp 4 기준. 102(opd)가 먼저 완료되면 opd n=8이 되어 중앙값이 바뀐다 | **High** | `TASK.md:129`, 실측 진행 중 태스크 `102`·`103`(E1) |
| R-A5 캐시 정지 | 실시간 파생을 캐시에 넣으면 값이 최대 30초 정지 — 분 단위 표시에서 최대 1분 오차 | Medium | `dashboard/backend/cache.py:17`, `:38-40`; `dashboard/backend/routers/tasks.py:433` |
| R-A6 용어 불일치 (FE↔BE↔원천) | 동일 개념 3토큰: 원천 `timestamp` ↔ API `PipelineRow.updated_at` ↔ FE `PipelineRow.updated_at`. R-2가 `timestamp`를 추가하면 한 모델에 두 토큰 공존 | Medium | `~/.opal/tools/state-tool/schema/state.schema.json` `rows.items.timestamp`; `dashboard/backend/models.py:140`; `dashboard/frontend/src/pages/tasks/TasksPage.tsx:62-67` |
| R-A7 용어 불일치 (행 식별자) | 원천 `row_id` ↔ API `PipelineRow.row` | Medium | 동상, `dashboard/backend/models.py:137` |
| R-A8 용어 불일치 (워크플로우) | 본문 용어 「워크플로우」 ↔ 원천·응답 필드 `skill`. 응답 필드명 미확정 | Medium | `TASK.md:96`("워크플로우(`skill`)별"), `~/.opal/tools/state-tool/schema/state.schema.json` `skill` |
| R-A9 목업↔요구사항 충돌 | 승인 목업의 B-1/B-2/B-4·A-1 타일 구성이 TASK.md 재작성본과 다르다 | Medium | `mockup/dashboard.html` vs `TASK.md:96`·`:117`·`:161-164` |
| R-A10 FE 컴포넌트 테스트 부재 | `TasksPage`·`DashboardPage` 테스트 0건 — A/B 렌더 AC를 잡을 기반이 없다 | Medium | `dashboard/frontend/src/` `*.test.ts*` 7파일 전부 `lib/`·`pages/brain/` |
| R-A11 `in_progress` 행 누락 | 집계기준 2의 제외 열거에 `in_progress`가 없다. 실측 1행 존재 | Medium | `TASK.md:94`, `tasks/103-260825-opd-태스크-진행통계/state.json:34-43` (E1) |
| R-A12 게이트 지표 모수 편중 | `gate` 보유 태스크 12건 / 미보유 11건(092 이전). 횡단 게이트 통과율은 반쪽 모수 | Low | 실측 12/23(E1); `TASK.md:99` (기준 7이 「미기록」으로 이미 대응) |
| R-A13 순환 import | `dashboard.py`가 이미 `routers.tasks.COLUMN_MAP`을 함수 내 지연 import 중. `stats.py`가 모델·라우터에 의존하면 순환 위험 | Low | `dashboard/backend/routers/dashboard.py:151` |
| R-A14 hex 하드코딩 | 신규 차트 색을 recharts에 직접 넘길 때 hex 리터럴 유입 위험 | Low | `[MUST]` `dashboard/frontend/src/index.css` `:root`: "hex 하드코딩 금지 — oklch() 함수 값만 사용한다" / 기존 준수 사례 `DashboardPage.tsx:202-232`(CSS 변수 문자열 전달) |

**[MUST] 인용 (재해석 금지)**

- `[MUST]` `dashboard/frontend/src/pages/tasks/TasksPage.tsx:1-9` `@header`: "[MUST] 읽기 전용: dnd-kit sensors 비활성·🔒 badge 상시·grab 커서 미사용"
- `[MUST]` `dashboard/frontend/src/index.css` `:root`: "모든 컴포넌트는 이 토큰(또는 shadcn 표준 토큰)을 경유해야 한다. hex 하드코딩 금지 — oklch() 함수 값만 사용한다."
- `[MUST]` `docs/CONVENTIONS.md` §State 관리: "파이프라인 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. `state.json` 직접 편집 금지"
- `[MUST]` `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `scripts/`)에서 수행한다."
- `[MUST]` `docs/CONVENTIONS.md` §플랫폼 분기 격리: "스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다"
- `[MUST]` `docs/CONVENTIONS.md` §@header 규칙: "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다" — 본 프로젝트는 `.opal/code-scan.json` `headerSource: "inline"`이므로 **인라인 주석**에 기록한다

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| BE 프레임워크 | FastAPI + uvicorn (127.0.0.1:7823) | `dashboard/backend/main.py:145` |
| BE 스키마 | Pydantic v2 `BaseModel` | `dashboard/backend/models.py:44` |
| BE 테스트 | pytest + httpx TestClient | `dashboard/backend/tests/test_routers.py:69` |
| FE 프레임워크 | React | ^19.2.6 |
| FE 언어/빌드 | TypeScript ~6.0.2 / Vite ^8.0.12 | `npm run build` = `tsc -b && vite build` |
| FE 상태 | TanStack Query ^5.101.0 · Zustand ^5.0.14 | - |
| FE UI | Tailwind ^4.3.1 · shadcn ^4.11.0 · Radix 12종 | - |
| FE 차트 | recharts | ^3.8.1 |
| FE 테스트 | Vitest ^4.1.9 + happy-dom ^20.10.6 + Testing Library | `dashboard/frontend/vitest.config.ts` |
| 원천 데이터 | `tasks/*/state.json` schema_version 1.0/1.1 | `~/.opal/tools/state-tool/schema/state.schema.json` |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| `op-dev-plan` | 다음 단계 — 기능별 설계 + Step 분해 + 에이전트 배정 |
| `op-dev-test-scenario` | RED-first 시나리오 — BE 집계 정확성 + FE 렌더 AC |
| `opal-fe-agent` / `opal-be-agent` | EXECUTE Step의 영역별 워커 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| shadcn | `Tabs`·`Table`·`ToggleGroup` 사용례 확인 (신규 컴포넌트 추가 시에만) |
| playwright | L3 시각 확인 — 배포본 7823 실데이터로 A/B 블록 렌더 검증 |

> context7·WebSearch는 **불필요** — 신규 외부 의존 0건(§2.1).

---

## 7. 지정 분석 질문 답변

**Q1. `stats.py` 순수 모듈 경계 — 집계 정의 SSOT를 어디까지 담고, 응답 형태는 어떻게 두는가.**

`stats.py`는 **집계 기준 14항목 전부**를 소유하고, 표준 라이브러리(`datetime`·`statistics`)에만 의존하는 순수 모듈로 둔다. 모델·라우터·캐시를 import하지 않는다(R-A13 회피). 라우터는 `state` dict를 넘기고 dataclass/dict를 받아 Pydantic 모델로 감싸기만 한다. 함수 시그니처 후보:

```python
def row_durations(state: dict, now: datetime | None = None) -> list[dict]
def task_stats(state: dict, now: datetime | None = None) -> dict
def workflow_stats(states: list[dict]) -> dict[str, dict]
```

`now` 주입은 **실시간 파생을 테스트 가능하게 만드는 핵심 장치**다 — 고정 `now`를 넘기면 결정론적 assert가 가능해져, "실시간 값의 AC 금지" 제약(`TASK.md:225`)을 BE 단위 테스트 층에서는 우회할 수 있다.

FE 중복 계산을 막으려면 응답이 **표시 가능한 최종형**이어야 한다. 분(minute) 정수와 함께 "7시간 5분" 같은 표시 문자열까지 BE가 내려주면 FE는 포맷 로직조차 갖지 않는다 — D-6의 "FE는 계산하지 않고 받은 값만 렌더한다"를 문자 그대로 만족한다. 비중(%)·최장 단계명·「표본 부족」 판정(n<5)·「미기록」 판정(092 이전)도 전부 BE 산출값으로 내린다.

**Q2. `PipelineRow` 확장의 파급.**

기존 테스트 회귀는 **0건**으로 판정한다(§1.4). 이유는 계약 검증이 `PipelineStageGroup` 4속성에만 걸려 있고 `PipelineRow` 필드를 직접 assert하지 않기 때문이다(`dashboard/backend/tests/test_routers.py:653-660`). 단 세 가지가 함께 처리돼야 한다.

1. 신규 5필드(`owner`·`gate`·`note`·`timestamp`·`key`)는 전부 **기본값 있는 additive**로 추가한다 — 078 선례(`dashboard/backend/models.py:36`).
2. `_group_pipeline_stages`의 행 매핑을 `row_id`·`timestamp` 원천 키로 교정한다(R-A2). `PipelineRow.row`/`updated_at`은 하위 호환을 위해 남기되 값을 `row_id`/`timestamp`에서 채운다 — 제거하면 FE 타입(`TasksPage.tsx:62-67`)과 동시 변경이 필요해 회귀 표면이 넓어진다.
3. `stage` 그룹은 **전건 연속**임을 실측 확인했으므로(E1 — 23태스크 전건, 분산 stage 0건) A-3 타임라인·A-4 표를 `pipeline[].rows[]` 평탄화로 재구성해도 원 행 순서가 보존된다. 별도 평탄 배열 필드를 신설할 필요가 없다.

**Q3. 실시간 파생의 캐시 상호작용.**

**정적 파생만 캐시하고 실시간 파생은 캐시 밖 응답 조립 시점에 계산한다.** 근거는 §4(2) — 캐시 항목은 30초 TTL이므로 실시간 값을 안에 넣으면 최대 30초 정지한다. 구체적으로,

- 캐시 키는 현행 유지: `task_detail:{project}:{task_id}` (`dashboard/backend/routers/tasks.py:398`).
- 캐시 저장 시 **`source_path`에 해당 태스크의 `state.json` 경로를 전달**한다 — 지금은 미전달이라 mtime 무효화가 죽어 있다(§4(2)). 파일 1개 stat이므로 전수 스캔이 아니며 성능 제약(`TASK.md:224`)을 위반하지 않는다.
- 캐시에는 `state` 기반 정적 파생(행별 소요·단계별 작업/대기 합계·완료 태스크의 총 리드타임·게이트 건수)만 담는다.
- 진행 중 태스크의 현재 행 경과·실시간 총 리드타임은 캐시 히트 이후 `now`를 주입해 계산한 뒤 응답에 합성한다.
- `/api/dashboard`는 모수가 **완료 태스크만**이므로(집계기준 3) 실시간 성분이 없다 — 현행 캐시 그대로 두면 된다. 다중 파일 소스라 단일 `source_path` mtime 무효화는 적용 불가하며, TTL 30초로 충분하다.

**Q4. `gate` 객체 직렬화.**

**타입 모델을 채택한다** — 자유 dict가 아니다. 근거: 스키마가 `gate`를 `required: ["artifacts", "checklist"]` + `additionalProperties: false`로 닫아 두었고 두 값 모두 문자열 배열이다 (`~/.opal/tools/state-tool/schema/state.schema.json` `rows.items.properties.gate`). 구조가 확정돼 있으므로 `PipelineGate(BaseModel)` 신설 후 `PipelineRow.gate`를 optional 타입 모델로 둔다. 이렇게 하면 R-2 AC("`gate`가 `artifacts`·`checklist`를 가진 객체로 직렬화된다, 불리언 아님")가 **스키마 층에서 자동 보증**되고 FE 타입도 정확해진다. `None`은 "게이트 행 아님"을 뜻하며, 092 이전 태스크의 「미기록」 표기 판정과는 별개 축이다(전자는 행 단위, 후자는 태스크 단위).

**Q5. 워크플로우 필터의 FE 상태 관리.**

**`DashboardPage` 로컬 `useState`를 쓴다.** 근거 3가지.
1. `contextProject`가 ui-store에 있는 이유는 **전 화면 공유 + URL 동기**가 필요해서다(`dashboard/frontend/src/store/ui-store.ts:17-19`, `dashboard/frontend/src/pages/tasks/TasksPage.tsx:494-497`). 워크플로우 필터는 대시보드 화면 안에서만 의미가 있어 이 조건에 해당하지 않는다.
2. ui-store의 `partialize`가 테마만 영속화하므로(`dashboard/frontend/src/store/ui-store.ts:74`) 스토어에 둬도 새로고침 보존 이득이 없다.
3. 같은 화면의 기간 필터가 이미 로컬 `useState` + `ToggleGroup`으로 구현돼 있다(`dashboard/frontend/src/pages/dashboard/DashboardPage.tsx:437`, `:184-195`). B-4를 이 패턴에 맞추면 신규 개념 0으로 붙는다.

필터링은 **FE에서 수행**한다 — BE가 워크플로우별로 이미 분리된 집계를 내려주므로(집계기준 4) 필터는 응답 객체에서 키를 고르는 동작이며, 필터 변경마다 API를 재호출할 이유가 없다.

**Q6. 결측 내성 3경로의 차단 지점.**

| 경로 | 차단 지점 | 처리 | 근거 |
|------|----------|------|------|
| `state.json` 부재 | **BE 라우터** — 이미 조기 반환 경로 존재 | 통계 필드를 `None`으로 채워 200 반환. FE는 `null` → "데이터 없음" 렌더 | `dashboard/backend/routers/tasks.py:403-412` |
| `rows` 비어있음 | **BE `stats.py`** | `_group_pipeline_stages`가 이미 빈 배열을 반환하므로(`:233-234`) `stats.py`도 동일하게 빈 집계 반환. IndexError 금지 | `dashboard/backend/routers/tasks.py:233-234`, `dashboard/backend/tests/test_routers.py:665-668` |
| `timestamp` 파싱 실패 | **BE `stats.py` 단일 지점** (신규) | `"%Y-%m-%d %H:%M"` 고정 포맷. 실패 행은 소요 합산에서 제외하되 **앵커(직전 done 시각)를 진전시키지 않는다**. 추가로 음수 소요는 0으로 clamp (R-A1) | `~/.opal/tools/state-tool/schema/state.schema.json` `timestamp.pattern`; 역행 실측 `tasks/086-260810-opp-아키텍처-다이어그램-재작성/state.json` |

세 경로 모두 **BE에서 차단**한다. FE는 `null`/빈 배열 수신 시 축소 표시만 담당하며 자체 방어 로직을 갖지 않는다 — D-6의 "FE는 계산하지 않는다"에 방어 판정도 포함된다. 이렇게 두면 R-12 AC의 "콘솔 에러 0건"이 FE 조건문 누락에 좌우되지 않는다.

---

## 8. 다음 단계 입력 — PLAN이 재조사 없이 쓸 수 있는 확정값

| 항목 | 확정값 | 근거 |
|------|--------|------|
| `stats.py` 의존 범위 | 표준 라이브러리(`datetime`·`statistics`)만. 모델·라우터·캐시 import 금지 | R-A13, `dashboard/backend/routers/dashboard.py:151` |
| `stats.py` 시간 주입 | 전 실시간 함수가 `now` 파라미터(기본 `None`)를 받는다 | Q1 — 실시간 AC 금지 제약(`TASK.md:225`)의 테스트 우회 장치 |
| 소요 합산 대상 행 | `status == "done"` 인 행만. `pending`·`na`·`in_progress`·`failed` 전부 제외 | 집계기준 1(`TASK.md:93`) + R-A11 열거 보정 |
| 음수 소요 처리 | 0으로 clamp | R-A1, `tasks/086-260810-opp-아키텍처-다이어그램-재작성/state.json` `plan.user_confirm` (E1) |
| 파싱 실패 행 처리 | 소요 제외 + 앵커 미진전 | Q6 |
| `gate` 응답 타입 | `PipelineGate(BaseModel)` — `artifacts`·`checklist` 문자열 배열 2필드. `PipelineRow.gate`는 optional | Q4, `~/.opal/tools/state-tool/schema/state.schema.json` |
| `PipelineRow` 확장 방식 | 기본값 있는 additive 5필드. 기존 `row`·`updated_at`은 존치하되 값을 `row_id`·`timestamp`에서 채워 사표 상태를 해소 | Q2, §4(1), `dashboard/backend/models.py:36` (078 선례) |
| 기존 BE 테스트 회귀 | **0건** — 계약 검증이 `PipelineStageGroup` 4속성에만 걸려 있음 | `dashboard/backend/tests/test_routers.py:653-660` |
| A-3/A-4 데이터 소스 | `pipeline[].rows[]` 평탄화로 충분. 별도 평탄 배열 필드 신설 불필요 | Q2 — stage 전건 연속 실측(E1, 23태스크) |
| 캐시 전략 | 정적 파생만 캐시(키 현행 유지 + `source_path`에 태스크 `state.json` 경로 전달), 실시간 파생은 캐시 밖 조립 | Q3, §4(2) |
| `/api/dashboard` 캐시 | 현행 유지 — 모수가 완료 태스크만이라 실시간 성분 없음 | Q3, 집계기준 3 |
| 워크플로우 필터 상태 | `DashboardPage` 로컬 `useState` + 기존 `ToggleGroup` 패턴. ui-store 미사용, API 재호출 없음 | Q5, `dashboard/frontend/src/pages/dashboard/DashboardPage.tsx:437`·`:184-195` |
| 결측 내성 차단층 | 3경로 전부 BE. FE는 `null`/빈 배열 축소 표시만 | Q6 |
| 신규 외부 의존 | **0건** — recharts 3.8.1·radix tabs 기보유 | §2.1, `dashboard/frontend/package.json` |
| A-1 타일 구성 | TASK.md R-6 AC 채택(총 리드타임/작업/대기·비중/최장 단계). 목업 A-1 4타일 구성은 폐기 | §4(5), citation-rules §9 (b) |
| B 블록 정의 | TASK.md 재작성본 채택(워크플로우별 분리·B-4=필터). 목업 B의 혼합 집계·「스킬·모드 분포」는 폐기, 시각 형태만 계승 | §4(5), 집계기준 4·D-9 |
| R-5 선행 조건 | 산출물 배지 101=9는 `_get_artifact_files` 화이트리스트 폐기(BE) 선행 필요 — FE 단독 달성 불가 | §4(4), `dashboard/backend/routers/tasks.py:89-96` (E1) |
| `_get_artifact_files` 파급 | 소비자 3곳(`artifacts` 2회·`artifact_count` 2회·아카이브 카드 1회) 동반 변동 | §3.2, `dashboard/backend/routers/tasks.py:283`·`:304`·`:361`·`:409`·`:430` |
| `STATS-BASELINE.md` 필수 기재 | 수치 + **모수를 구성한 태스크 ID 목록** + 측정 명령·스코프 | R-A4, §4(6), citation-rules §9 (a) E1 스코프 요구 |
| 재검증 완료 수치 (그대로 사용) | 완료 21/전체 23 · 중앙값 opd 799·opds 276·opp 75분 · 대기 비중 21%/4%/54% · `.md` 192 · 101 총 425=작업 105+대기 320(75%) · 101 단계별 TASK 24(0/24)·ANALYSIS 22(17/5)·PLAN 13(11/2)·TEST-SCENARIO 295(10/285)·EXECUTE 18(18/0)·TEST 51(47/4)·CLOSE 2(2/0) · 101 행 19·게이트 4 | E1 — 스코프: `tasks/*/state.json` 23파일 전수 + `tasks/*/` `.md` 파일 수, 명령 `python3` 인라인 앵커 차분 |
| 재산출 필요 수치 | `*.user_confirm` 중 `owner=auto` **41건**(TASK.md 33건) · 행 상태 분포 done 263·in_progress 1·pending 28·na 11 · `owner` PM 224·auto 43·user 36 | §4(6) (E1, 동상) |
| **[PM 정정]** 화이트리스트 교집합 | **92** — §4(6) 표의 「91」은 계수 오류가 아니라 **스코프 엇갈림**이다. 전체 `.md` 192는 `103` 폴더를 **포함**한 값이고, 화이트리스트 91은 `103`을 **제외**한 값이다(실측: `103` 7파일 전량 제외 시 190/**91**, `103`의 `TASK.md`·`ANALYSIS.md` 포함 시 192/**92**). 한 행 안에서 두 스코프가 섞였다. 같은 스코프로 세면 92가 옳다 | E1 — PM 재실측, `tasks/*/` `.md` 폴더별 화이트리스트 교집합 열거 + `103` 산출물 역산 |
| @header 기록 위치 | **인라인 주석** — `.opal/code-scan.json` `headerSource: "inline"` | `docs/CONVENTIONS.md` §@header 규칙 |
| 배포 영향 | 없음 — `stats.py`는 기존 `install_dashboard()` 패키지 복사 경로에 포함 | §3.2, `tasks/backup/021-260615-opd-opal-console/DONE.md` §2 |

### PLAN 결정 필요

| 항목 | 쟁점 | 근거 |
|------|------|------|
| P-1 워크플로우 응답 필드명 | 본문 용어 「워크플로우」 ↔ 원천 필드 `skill`. 응답 키를 `skill`로 갈지 `workflow`로 갈지 미확정. FE 타입·BE 모델·목업 라벨 3곳이 이 결정에 걸린다 | R-A8; `TASK.md:96`; `~/.opal/tools/state-tool/schema/state.schema.json` `skill` |
| P-2 소요 시각 필드 이름 | `PipelineRow`에 `timestamp` 추가 시 사표 `updated_at`과 공존. 존치·별칭·deprecated 표기 중 택1 | R-A6; `dashboard/backend/models.py:140` |
| P-3 산출물 유형 분류 축 | 집계기준 9의 "유형 분류" 분류 체계 미정. 산출물 탭 노출 범위(`STATE.md`·`AGENTIC-LOG.md` 포함 여부)가 여기 걸린다 | `TASK.md:101`; §3.2 |
| P-4 회귀 경계 선언 | `artifact_count` 값 변동을 완료기준 (7) "회귀 없음"의 예외로 명시할지 | R-A3; `TASK.md:129` |
| P-5 완료기준 (3) 검증 시점 | 102(opd) 완료 시 opd 모수 7→8로 중앙값 이동. 베이스라인 모수 고정 방식(태스크 ID 목록 명시 vs 검증 시점 재측정) 택1 | R-A4 |
| P-6 FE 컴포넌트 테스트 도입 | `TasksPage`·`DashboardPage` 테스트 0건. A/B 렌더 AC를 vitest 컴포넌트 테스트로 잡을지, L3 시각 확인으로 대체할지 | R-A10; `dashboard/frontend/vitest.config.ts` |
| P-7 표시 문자열 소유 | "7시간 5분" 포맷을 BE가 내릴지 FE 유틸이 만들지. D-6 "FE 무계산"의 해석 범위 | Q1; `TASK.md:114` |

---

## 부록 — 분석 품질 자체 검증 (analysis-core §7)

- **완전성**: TASK.md `[결정]` 9 · `[사실]` 4 · 집계기준 14 전건 판정(누락 0). R-1~R-14는 §1.1·§3·§8에 전건 매핑. §0 참조 문서 17건 작성. 선조회 3단 + 3단-B(T1) 결과 명시.
- **정확성**: 인용 경로 전건 실재 확인. 버전은 `package.json`·`vitest.config.ts`·`state.schema.json`에서 추출. 수치 주장은 전건 E1 전수 스캔으로 재측정.
- **유용성**: 직접·간접 영향 분리 기재. 제약/리스크 14건 전건 근거 부착. §8이 PLAN 재조사 없는 확정값 24행 + 미결 7건 제공.
- **근거 표기**: §1.1 근거 열 전건 충족. 소스코드 원문 블록 **0건** — 코드펜스 2개는 실행 명령·함수 시그니처 한정.
- **decision_required**: R-A6·R-A7·R-A8 3건이 `terminology_mismatch` 유형이며 P-1·P-2로 에스컬레이션한다 (citation-rules §7.5 — PM 자율 결정 금지).
