# TASK: OPAL Console 태스크 진행 통계

> 작성일: 2026-08-25 | 작업 유형: 개선 | 적용 스킬: opd | 모드: semi-agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

OPAL Console 태스크 칸반의 상세 패널에 진행 통계 4블록(A-1~A-4)을, 대시보드 화면에 횡단 통계 4블록(B-1~B-4)을 추가한다. 통계의 원천은 `tasks/*/state.json` 파이프라인 행이며, 지금 화면이 보여주지 못하는 병목·진척·게이트·작업량 4개 축을 수치로 드러낸다.

## 배경

태스크 상세 패널은 현재 파이프라인 스테퍼(단계별 점 + `done_count/total`)와 산출물 탭만 제공한다(`dashboard/frontend/src/pages/tasks/TasksPage.tsx:264`). 어느 단계에서 시간이 걸렸는지, 누가 무엇 때문에 멈췄는지, 지금 어디까지 왔는지를 화면에서 읽을 수 없다.

반면 원천 데이터인 `state.json`에는 행마다 `timestamp`·`owner`·`gate`·`note`가 쌓여 있어, 추가 계측 없이 소요 시간·대기 시간·게이트 통과율을 계산할 수 있다. 데이터는 이미 있는데 화면이 버리고 있는 상태다.

## 배경 분석 (대화에서 도출)

이 태스크 착수 전, 알투(PM)가 `tasks/*/state.json` 22개 파일·287행을 직접 계산하고 목업을 만들어 캡틴 승인을 받았다. 아래는 그 과정에서 확인된 사실이다.

### (1) 원천 데이터 실측

| 항목 | 실측값 |
|------|--------|
| state.json 보유 태스크 | 22건 (`tasks/080-*` ~ `tasks/102-*`) |
| 파이프라인 행 총계 | 287행 |
| 행 필드 충족률 | `row_id`·`stage`·`item`·`key`·`status`·`status_label`·`timestamp`·`owner`·`note` 287/287 (100%) |
| 선택 필드 | `gate` 34행, `step` 5행 |
| 리드타임 중앙값 / 평균 | 342분 / 614분 |
| 캡틴 확인 대기 누계 | 2,079분 (총 리드타임 12,887분의 16.1%) |
| 단계별 평균 소요 | TASK 32분 · ANALYSIS 59분 · PLAN 119분 · TEST-SCENARIO 236분 · EXECUTE 220분 · TEST 139분 · CLOSE 31분 |

### (2) 현행 API가 통계 재료를 버리는 지점

- `PipelineRow`는 `row`·`stage`·`status`·`updated_at` 4필드만 노출한다 (`dashboard/backend/models.py:136-140`). 원천 `state.json` 행이 가진 `owner`·`gate`·`note`·`timestamp`가 프론트에 도달하지 않는다.
- 진행률은 `완료 rows / 전체 rows` 단일 수식뿐이다 (`dashboard/backend/routers/tasks.py:291-293`, `:417-419`). 시간 축 지표가 없다.
- 산출물 카운트는 6종 화이트리스트로 고정돼 있다 (`dashboard/backend/routers/tasks.py:92`). 태스크 101은 실제 `.md` 9개를 보유하나 카운트는 화이트리스트 교집합만 센다.

### (3) 대시보드 집계 경로는 이미 존재한다

- `GET /api/dashboard`가 이미 구현돼 있고(`dashboard/backend/routers/dashboard.py:109-110`), `_collect_all_tasks`가 프로젝트 전 태스크의 `state.json`을 수집한다(`dashboard/backend/routers/dashboard.py:46`).
- 프론트에도 `MetricCard`·`ActivityChart`·`StatusPieChart`·`RecentTable` 컴포넌트가 이미 있다(`dashboard/frontend/src/pages/dashboard/DashboardPage.tsx:132`, `:168`, `:253`, `:375`).
- 따라서 B-1~B-4는 **집계 API 신설이 아니라 기존 `/api/dashboard` 확장**으로 처리하는 것이 타당하다. (목업 게시 시점에는 "집계 API 신설 필요"로 보고했으나, 실측 결과 기존 경로가 있어 정정한다.)

### (4) 선재 결함 — 칸반 카드 제목이 전건 폴더명

- 22개 `state.json` 전부에 `title` 키가 없다(실측: 22/22 누락).
- `tasks.py`는 `state.get("title", task_id)`로 폴백한다(`dashboard/backend/routers/tasks.py:297`, `:423`) → 칸반 카드·상세 헤더 제목이 전건 폴더명으로 표시된다.
- 반면 `dashboard.py`는 `_resolve_task_title`로 TASK.md의 H1을 읽어 사람이 쓴 제목을 복원한다(`dashboard/backend/routers/dashboard.py:90`). 같은 프로젝트 안에서 두 라우터의 제목 해석이 불일치한다.
- 본 태스크 범위 밖의 선재 결함이나, 통계 화면이 태스크를 식별해 보여주는 이상 표시 품질에 직접 영향을 준다.

### (5) 목업 검증

알투(PM)가 실측값으로 목업을 작성해 캡틴에게 제시했고 승인받았다. 목업은 콘솔의 시그니처 3색·상태색 5종(`dashboard/frontend/src/index.css` `:root`)을 그대로 계승했다.

## 확정된 설계 방향 (대화에서 합의)

- `[결정]` 상세 4블록(A-1 요약 숫자 카드 · A-2 단계별 가로 막대 · A-3 타임라인 · A-4 단계별 상세 표)과 대시보드 4블록(B-1 요약 카드 · B-2 단계별 평균 막대 · B-3 태스크별 리드타임 · B-4 스킬·모드 분포) 8개를 전부 채택한다.
- `[결정]` 통계 목적 4축을 모두 다룬다 — 병목(어디서 오래 걸렸나) · 진척(지금 어디까지) · 블로커·게이트(누가/무엇이 막았나) · 작업량(산출물·규모).
- `[결정]` 소요 시간 계산 기준은 **직전 행 완료 시각 → 이 행 완료 시각 = 이 행의 소요**로 한다. 근무시간 보정·야간 공백 제외는 적용하지 않는다.
- `[결정]` 통계 범위는 태스크 상세와 대시보드 양쪽이다. 별도 통계 전용 화면은 만들지 않는다.
- `[사실]` `state.json` 287행 전건이 `timestamp`·`owner`를 보유하므로 위 기준 계산에 추가 계측이 필요 없다 (본 문서 §배경 분석 (1)).
- `[사실]` `PipelineRow`가 `owner`·`gate`·`note`를 노출하지 않아 A-1·A-3·A-4는 응답 모델 확장이 선행되어야 한다 (`dashboard/backend/models.py:136-140`).
- `[사실]` 대시보드 집계 엔드포인트와 차트 컴포넌트가 이미 존재하므로 B 블록은 신설이 아닌 확장이다 (본 문서 §배경 분석 (3)).
- `[결정]` 칸반 읽기 전용 원칙을 유지한다 — 통계 블록도 조회 전용이며 쓰기 동작을 추가하지 않는다.
- `[결정]` 상세 Sheet 본문을 **2탭으로 분리**한다 — 「태스크 대시보드」 탭에 파이프라인 스테퍼와 A-1~A-4를, 「산출물」 탭에 문서 뷰어를 담는다. 태스크 식별 헤더(ID·배지·기간)는 탭 위에 고정한다. 기본 활성 탭은 「태스크 대시보드」다.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 태스크 상세에 통계 4블록(A-1~A-4), 대시보드에 통계 4블록(B-1~B-4)을 추가해 병목·진척·게이트·작업량 4축을 수치로 표시한다 | - | - |
| 범위 | **포함** — BE: `PipelineRow` 확장(`owner`·`gate`·`note`·`timestamp`), 태스크 상세 응답에 소요 시간 파생값 추가, `/api/dashboard` 집계 확장. FE: `TasksPage.tsx` 상세 Sheet 본문을 2탭(태스크 대시보드 / 산출물)으로 재구성 + 「태스크 대시보드」 탭에 A-1~A-4, `DashboardPage.tsx`에 B-1~B-4. **제외** — 통계 전용 신규 화면, 쓰기 동작, 근무시간 보정 로직, 제목 폴백 결함 수정(§배경 분석 (4), 별건) | - | `dashboard/backend/models.py:136-140` · `dashboard/backend/routers/dashboard.py:109-110` · `dashboard/frontend/src/pages/tasks/TasksPage.tsx:264` |
| 제약 | 칸반 읽기 전용 유지 · `state.json` 직접 편집 금지(state-tool 전용) · 색상은 `index.css` `:root` 토큰 경유(hex 하드코딩 금지) · 코드 파일 변경 시 `@header` 규칙 적용 · `state.json` 부재 태스크에서 통계 블록이 깨지지 않아야 함 | - | `dashboard/frontend/src/pages/tasks/TasksPage.tsx:1-9` · `docs/CONVENTIONS.md` |
| 완료기준 | (1) 태스크 상세가 「태스크 대시보드」·「산출물」 2탭으로 나뉘고, 대시보드 탭에 A-1~A-4 4블록이 렌더되며 101번 태스크 기준 총 리드타임 7시간 5분·캡틴 대기 5시간 20분·게이트 4건이 실측값과 일치한다 (2) 대시보드에서 B-1~B-4 4블록이 렌더되고 22건 기준 중앙값 342분·단계 평균 7개 값이 실측값과 일치한다 (3) `state.json`이 없는 태스크에서 상세 패널이 오류 없이 열린다 (4) 색상 하드코딩 hex가 신규 코드에 0건이다 (5) 기존 칸반·대시보드 화면의 기존 기능이 회귀하지 않는다 | - | 본 문서 §배경 분석 (1) |

## 요구사항

- [ ] **R-1** 파이프라인 행 응답 확장 — `PipelineRow`에 `owner`·`gate`·`note`·`timestamp`를 추가한다.
  - 어디에: `dashboard/backend/models.py:136-140`
  - 왜: A-1·A-3·A-4가 담당·게이트·비고를 표시해야 하는데 현재 응답에 없다 (확정 방향 §`[사실]` 2)
  - AC: `GET /api/tasks/detail` 응답의 `pipeline[].rows[]` 각 원소가 `owner`·`gate`·`note`·`timestamp` 키를 포함하고, 태스크 101 기준 `gate=true`인 행이 4건이다.

- [ ] **R-2** 태스크 소요 시간 파생 — 행별 소요(분)와 단계별 소요 합계, 총 리드타임, `owner=user` 행 소요 합계를 응답에 포함한다.
  - 어디에: `dashboard/backend/routers/tasks.py` (`get_task_detail`)
  - 왜: 확정 기준(직전 행 완료 → 이 행 완료)의 계산 주체를 BE로 고정해 FE 중복 구현을 막는다 (확정 방향 §`[결정]` 3)
  - AC: 태스크 101 응답에서 총 리드타임 425분, `owner=user` 소요 합계 320분, 단계별 합계가 TASK 24 / ANALYSIS 22 / PLAN 13 / TEST-SCENARIO 295 / EXECUTE 18 / TEST 51 / CLOSE 2분으로 반환된다.

- [ ] **R-11** 상세 Sheet 2탭 분리 — 본문을 「태스크 대시보드」·「산출물」 두 탭으로 나누고, 태스크 식별 헤더는 탭 위에 고정한다.
  - 어디에: `dashboard/frontend/src/pages/tasks/TasksPage.tsx` (`TaskDrawer`)
  - 왜: 통계 4블록이 추가되면 단일 스크롤 본문에서 산출물 뷰어가 하단으로 밀려 도달성이 떨어진다 (확정 방향 §`[결정]` 6)
  - AC: 상세 Sheet에 탭 2개가 렌더되고 기본 활성 탭이 「태스크 대시보드」이며, 「산출물」 탭에 문서 개수 배지가 표시된다. 탭 전환 시 각 탭 본문이 자체 영역에서만 세로 스크롤되고 Sheet 헤더는 고정 유지된다.

- [ ] **R-3** A-1 요약 숫자 카드 — 총 리드타임·완료 단계·캡틴 확인 대기·게이트/블로커 4타일을 렌더한다.
  - 어디에: `dashboard/frontend/src/pages/tasks/TasksPage.tsx` — 「태스크 대시보드」 탭, 파이프라인 스테퍼 아래
  - 왜: 진척과 대기 비중을 한눈에 보기 위함 (확정 방향 §`[결정]` 1·2)
  - AC: 태스크 101 상세에서 4타일이 렌더되고 값이 각각 `7시간 5분` / `6 / 6` / `5시간 20분` / `4 / 0`으로 표시된다.

- [ ] **R-4** A-2 단계별 가로 막대 — 단계별 소요 시간을 막대 길이로 비교 표시하고 최장 단계를 강조한다.
  - 어디에: `dashboard/frontend/src/pages/tasks/TasksPage.tsx` — 「태스크 대시보드」 탭
  - 왜: 병목 단계를 즉시 식별하기 위함 (확정 방향 §`[결정]` 2)
  - AC: 태스크 101 상세에서 7개 막대가 렌더되고 TEST-SCENARIO 막대가 최장으로 강조되며 `4시간 55분`으로 표기된다.

- [ ] **R-5** A-3 타임라인 — 행 시각을 순서대로 배치하고 담당(PM/캡틴/자동)을 색과 라벨로 구분하며, 직전 행 대비 공백이 큰 구간을 별도 표시한다.
  - 어디에: `dashboard/frontend/src/pages/tasks/TasksPage.tsx` — 「태스크 대시보드」 탭
  - 왜: 대기 구간이 어디서 발생했는지 시간축으로 드러내기 위함 (확정 방향 §`[결정]` 2)
  - AC: 태스크 101 상세에서 시각이 오름차순으로 렌더되고, 17:41 → 22:26 구간이 공백 `4시간 45분`으로 표시되며, 담당 구분이 색 단독이 아니라 라벨을 동반한다.

- [ ] **R-6** A-4 단계별 상세 표 — 단계·항목·상태·담당·시각·소요를 표로 렌더하고 게이트 행을 표시한다.
  - 어디에: `dashboard/frontend/src/pages/tasks/TasksPage.tsx` — 「태스크 대시보드」 탭
  - 왜: 블록 3개가 요약한 내용의 원본을 확인할 수 있어야 한다 (확정 방향 §`[결정]` 1)
  - AC: 태스크 101 상세에서 19행이 렌더되고 게이트 표시가 4건이며, 표가 자체 가로 스크롤 컨테이너 안에서만 스크롤된다.

- [ ] **R-7** 대시보드 집계 확장 — `/api/dashboard` 응답에 리드타임 중앙값·평균, 단계별 평균 소요, 태스크별 리드타임 목록, 캡틴 대기 비중, 게이트·블로커 합계, 산출물 규모를 추가한다.
  - 어디에: `dashboard/backend/routers/dashboard.py` (`get_dashboard`), `dashboard/backend/models.py` (`DashboardSummaryResponse`)
  - 왜: 기존 집계 경로가 있으므로 신설 대신 확장한다 (확정 방향 §`[사실]` 3)
  - AC: `GET /api/dashboard?project=<ai-framework 절대경로>` 응답에서 중앙값 342분, 평균 614분, 단계 평균 7개 값(32/59/119/236/220/139/31분), 캡틴 대기 비중 16%가 반환된다.

- [ ] **R-8** B-1~B-4 대시보드 렌더 — 요약 카드·단계별 평균 막대·태스크별 리드타임·스킬/모드 분포 4블록을 대시보드 화면에 추가한다.
  - 어디에: `dashboard/frontend/src/pages/dashboard/DashboardPage.tsx`
  - 왜: 태스크 1건이 빠른지 느린지는 횡단 비교가 있어야 판단된다 (확정 방향 §`[결정]` 4)
  - AC: 대시보드에서 4블록이 렌더되고, B-1 태스크 22건·중앙값 5시간 42분, B-2 최장 단계 TEST-SCENARIO, B-3 최장 태스크 100번, B-4 opds 10 / opd 8 / opp 4가 표시된다.

- [ ] **R-9** 결측 내성 — `state.json`이 없거나 `rows`가 비었거나 `timestamp`가 파싱 불가한 태스크에서 통계 블록이 오류 없이 축소 표시된다.
  - 어디에: BE 파생 계산부 + FE 8블록 전부
  - 왜: 아카이브·구형식 태스크는 `state.json` 없이 산출물로 컬럼을 추론한다 (`dashboard/backend/routers/tasks.py:120` `_infer_column_from_artifacts`)
  - AC: `state.json` 없는 태스크 상세를 열면 예외 없이 패널이 열리고 통계 블록 자리에 "데이터 없음"이 표시되며, 콘솔 에러가 0건이다.

- [ ] **R-10** 토큰 경유 — 신규 UI 색상은 `index.css` `:root` 토큰만 사용한다.
  - 어디에: 신규 FE 코드 전체
  - 왜: `[MUST] index.css` `:root` 주석: "hex 하드코딩 금지 — oklch() 함수 값만 사용한다"
  - AC: 신규·수정 FE 파일에서 hex 색상 리터럴이 0건이다.

## 제약 조건

- **읽기 전용 유지** — 칸반은 읽기 전용 화면이다(`dashboard/frontend/src/pages/tasks/TasksPage.tsx:1-9` `@header`: "[MUST] 읽기 전용"). 통계 블록에 쓰기·편집 동작을 추가하지 않는다.
- **`state.json` 직접 편집 금지** — `[MUST]` `.opal/AGENT.md` §금지사항: "STATE.md 마크다운 직접 편집 금지 — `state-tool`만 사용." 본 태스크는 조회만 하며 상태를 쓰지 않는다.
- **색상 토큰 경유** — `[MUST]` `dashboard/frontend/src/index.css` `:root` 주석: "모든 컴포넌트는 이 토큰(또는 shadcn 표준 토큰)을 경유해야 한다. hex 하드코딩 금지 — oklch() 함수 값만 사용한다."
- **@header 규칙** — 코드 파일 생성·수정 시 `@header` 메타블록을 갱신한다 (`opal/core/references/harness/header-rules.md`).
- **플랫폼 분기 금지** — `.opal/AGENT.md` §금지사항: "하드코딩된 플랫폼 분기 추가 금지".
- **배포 경계** — `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- **가로 스크롤 격리** — 표·막대 등 넓은 콘텐츠는 자체 컨테이너에서만 가로 스크롤한다. 패널 본문이 가로로 밀리지 않아야 한다.
- **성능** — 대시보드 집계는 프로젝트 전 태스크의 `state.json`을 읽는다. 기존 캐시 경로(`dashboard/backend/cache.py`)를 그대로 사용하고 무캐시 전수 스캔을 추가하지 않는다.

## 기술 스택

- **Console FE** — React, TypeScript, Vite, Tailwind CSS, shadcn/ui, TanStack Query (`dashboard/frontend/package.json`)
- **Console BE** — Python, FastAPI, Pydantic, uvicorn (`dashboard/backend/`)
- **테스트** — Vitest (FE, `dashboard/frontend/vitest.config.ts`), pytest (BE, `dashboard/backend/tests/`)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | 프로젝트 정의 (SSOT) | `docs/PROJECT.md` | §주요 컴포넌트 (OPAL Console) — Console FE/BE 구성과 전문 에이전트 매핑 |
| D-2 | 설계 | 시스템 아키텍처 | `docs/ARCHITECTURE.md` | §OPAL Console — 라우터·어댑터 구조 |
| D-3 | 설계 | 코드 및 문서 컨벤션 | `docs/CONVENTIONS.md` | 네이밍·@header·구현 규칙 |
| D-4 | 소스 | 태스크 라우터 | `dashboard/backend/routers/tasks.py` | 상세 응답 생성부 — R-1·R-2 대상 |
| D-5 | 소스 | 응답 모델 | `dashboard/backend/models.py` | `PipelineRow`·`TaskDetailResponse`·`DashboardSummaryResponse` — R-1·R-7 대상 |
| D-6 | 소스 | 대시보드 라우터 | `dashboard/backend/routers/dashboard.py` | 기존 집계 경로 — R-7 확장 대상 |
| D-7 | 소스 | 태스크 칸반 화면 | `dashboard/frontend/src/pages/tasks/TasksPage.tsx` | 상세 Sheet — R-3~R-6 대상 |
| D-8 | 소스 | 대시보드 화면 | `dashboard/frontend/src/pages/dashboard/DashboardPage.tsx` | 기존 차트 컴포넌트 — R-8 대상 |
| D-9 | 소스 | 전역 디자인 토큰 | `dashboard/frontend/src/index.css` | 시그니처 3색·상태색 5종 — R-10 근거 |
