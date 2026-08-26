# TEST SCENARIO: OPAL Console 태스크 진행 통계

> 작성일: 2026-08-25 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | 입력: TASK.md(16:05) · ANALYSIS.md · PLAN.md(1,379줄) §리스크 가설 표 + TS-001~TS-053 초안
> 작성자 ≠ PLAN 작성자(`opal-plan-agent`) ≠ 구현 워커(`opal-be-agent`·`opal-fe-agent`) — self-confirming 방지 (`~/.opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` §목적 1)

---

## 0. 문서 규약

### 0.1 시나리오 ID — PLAN 승계

본 문서의 시나리오 ID는 PLAN.md §3.N.5가 이미 배정한 **`TS-NNN`을 그대로 쓴다**(SKILL 양식의 `S-N` 자리). PLAN §4.2 각 Step의 「테스트」 필드가 이 ID를 참조하므로 재번호를 매기지 않는다. 본 단계의 작업은 **재도출이 아니라 구체화**다 — Given/When/Then 3필드, 사전 조건 데이터, 계층(L)·실행 방식(M), RED 기대 실패를 채웠다.

**PLAN 초안 대비 증분 4건** (가설 커버 누락 보강 — `scenario-gate.md` §2 ④):

| 신규 ID | 사유 | 커버 가설 |
|---------|------|----------|
| TS-018 | H-6의 "캐시 히트 응답에서도 실시간 값이 재계산된다"가 TS-001~053에 대응 시나리오 0건 | H-6 |
| TS-039 | H-12의 "탭 9개 폭 초과"가 TS-035(A-4 표 스크롤)와 다른 계약인데 전용 시나리오 0건 | H-12 |
| TS-047 | H-11의 "목업 폐기 블록을 그대로 구현"이 잔존 0 관점으로 단정되지 않음 | H-11 |
| TS-060~063 | 계층 의무 — L3 [SUPERVISOR] 부재, FE 변경·API 엔드포인트 변경의 L2/M2 의무 미충족 | H-7·H-11·H-12·H-3 |

### 0.2 RED-first 트랙 분기 (PM 확정 — 재론 금지)

`~/.opal/references/harness/red-first.md` §1.5 하이브리드 자동분기 적용 결과다.

| 영역 | 트랙 | 근거 |
|------|------|------|
| `dashboard/backend/stats.py` | **RED-first 강제** | 비즈니스 로직 (집계 정의 SSOT) |
| `dashboard/backend/models.py` · `routers/tasks.py` · `routers/dashboard.py` | **RED-first 강제** | API 계약 |
| `dashboard/backend/cache.py` | **RED-first 강제** | 버그 수정(회귀 방지) — P-8 시계 혼용 |
| `dashboard/frontend/**` (`TasksPage.tsx` · `DashboardPage.tsx`) | 구현-후-검증 허용 | UI 화면·컴포넌트 |

- RED-first 대상 시나리오는 각 시나리오 표에 **`RED 기대 실패`** 행을 갖는다. 실패 테스트를 먼저 작성·실행해 **exit code ≠ 0**을 증거로 남긴 뒤 구현에 들어간다 ([MUST] `~/.opal/references/harness/red-first.md` §1).
- **회귀 시나리오(TS-017·TS-024)는 RED 대상이 아니다** — 기존 테스트가 이미 GREEN이어야 하는 것을 확인하는 시나리오이므로 RED 개념이 성립하지 않는다.
- 어느 트랙이든 **① 테스트 코드 산출물 ② 작성자≠구현자 ③ TEST 단계 검증**은 유지한다 (동 §1.5 공통 불변).

### 0.3 [MUST] 픽스처 원칙 — 실 데이터만

[MUST] `~/.opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` §Step 4: "시나리오 본문에 가짜 객체 대체 키워드 사용 금지. 대안: 실 fixture / factory / seed 데이터 사용."

- 모든 픽스처는 **실 `tasks/*/state.json` 파일**이거나 그 **동결 복사본**이다. 값을 지어낸 픽스처는 0건이다.
- 결측 케이스(`FX-EMPTY`·`FX-NOCREATED`·`FX-BADTS`)는 실 101 파일에서 **필드를 제거·훼손한 파생본**이며, 없는 데이터를 만들어 넣은 것이 아니다.
- FE 픽스처는 실 응답 스냅샷을 API 클라이언트 계층에 주입한다(수단은 EXECUTE 워커가 선례 `dashboard/frontend/src/pages/brain/brain-navigation-guard.test.tsx:31-39`를 따른다). **검증 대상 구현 자체를 가짜 응답으로 대체하지 않는다** — BE 구현은 실제로 호출·검증한다.

### 0.4 [MUST] 기대값 원천 — 자기확인 금지

[MUST] PLAN.md P-5 근거 3: "`STATS-BASELINE.md`는 `stats.py` **출력이 아니라** ANALYSIS §8 「재검증 완료 수치」(E1, PM 인라인 집계로 독립 재측정된 값)로 작성한다."

본 문서의 기대 수치도 동일 원천이며, **구현이 낸 값을 기대값으로 되쓰지 않는다**. 아래 3계층이 서로를 검증한다.

```
ANALYSIS §8 (독립 재측정 E1) ─→ STATS-BASELINE.md §3~§5 ─→ 화면/응답 표시값
                              └─→ 본 문서 기대값 ────────────┘
```

작성 시점에 PM이 전수 재확인한 항목(E1 — 스코프 `tasks/*/state.json` 23파일, 명령: `python3` 인라인 앵커 차분 집계): 101 총 425 = 작업 105 + 대기 320(75%) · 단계별 7행 · 행 19 · 게이트 4 · 086 `plan.user_confirm` −1분 · 코호트 중앙값 opd 799 / opds 275.5 / opp 75 · 대기 비중 21/4/54 · 단계 모수 EXECUTE 21 · TEST 17 · TEST-SCENARIO 7 · `092` 이전 11개 태스크 게이트 0건 · 101 `.md` 9개.

### 0.5 [MUST] 이동값 처리 규약

[MUST] `TASK.md` §제약 조건: "실시간 파생값은 렌더 시각에 따라 변하므로 완료기준 수치 AC는 완료 태스크로만 잡는다. 진행 중 태스크의 AC는 값이 아니라 동작으로 기술한다."

| 이동값 | 단정 방식 |
|--------|----------|
| 진행 중 태스크의 현재 행·경과 시간 | **동결 복사본 + `now` 고정 주입**으로 L1에서 값 단정. 실 파일 대상 L2는 **불변식만** 단정(현재 행이 `in_progress` 우선·없으면 첫 `pending`) |
| `completed_tasks` / `total_tasks` (21 / 23) | 값 단정은 **동결 코호트 입력(FX-COHORT)** 에서만. 실 API L2는 항등(`completed + 진행중 = total`)과 하한(`completed ≥ 21`)으로 단정 |
| `artifact_total` (`.md` 전수) | 값 고정 금지 — 본 태스크 산출물 추가로 증가한다(작성 시점 실측 194, TASK.md 기재 192). **`artifact_total == artifact_by_type 합계` 항등**으로 단정 |
| R-4 AC의 "103 현재 행 = `task.user_confirm`" | AC 작성 시점 값이며 현재 103의 현재 행은 `test_scenario.test_scenario_md`다. **그 형태를 실 데이터로 보유한 `FX-102`(첫 pending = `task.user_confirm`, 대기 귀속)로 값 단정**하고, 103은 구조 단정으로 검증한다 |

### 0.6 [MUST] 실시간 함수 결정론

[MUST] `PLAN.md` §8 확정값: "`stats.py` 시간 주입 — 전 실시간 함수가 `now` 파라미터(기본 `None`)를 받는다."

실시간 시나리오(TS-005·006·013·018·060)는 `now`를 **고정 주입**해 기술한다. 벽시계에 의존하는 단정을 쓰지 않는다.

### 0.7 테스트 스택·위치 (`test-tool resolve` 결과)

`~/.opal/tools/test-tool/run.sh resolve --project .` 출력 (source: global):

| tier × scope | 도구 | 본 문서 대응 |
|--------------|------|------------|
| unit.be.unit | pytest | M1 — BE L1 |
| unit.fe.unit | vitest (+ happy-dom, Testing Library) | M1 — FE L1 |
| integration.be.api_db | pytest + httpx (실 데이터, 가짜 대체 금지) | M1 — BE L2 |
| integration.e2e | **cmux (1순위) → playwright (폴백)** | M2 — TS-062·063 |
| integration.supervisor | captain-manual | M3 — TS-060·061 |

**테스트 파일 배치 (모듈 미러링, `test-scenario-guide.md` §Step 4-b)**

| 대상 모듈 | 테스트 파일 | 상태 |
|----------|-----------|------|
| `dashboard/backend/stats.py` | `dashboard/backend/tests/test_stats.py` | 신규 (PLAN Step 8) |
| `dashboard/backend/cache.py` | `dashboard/backend/tests/test_cache.py` | **신규 — PLAN 파일 목록 보정 1건** |
| `dashboard/backend/routers/*.py` · `models.py` | `dashboard/backend/tests/test_routers.py` | 기존 파일에 케이스 추가 |
| `TasksPage.tsx` | `dashboard/frontend/src/pages/tasks/TasksPage.stats.test.tsx` | 신규 (PLAN P-6) |
| `DashboardPage.tsx` | `dashboard/frontend/src/pages/dashboard/DashboardPage.stats.test.tsx` | 신규 (PLAN P-6) |

> **보정 근거**: PLAN Step 2의 테스트는 TS-016(`cache.py`)인데 Step 8 파일 목록은 `test_stats.py`·`test_routers.py` 2종뿐이다. [MUST] `test-scenario-guide.md` §Step 4-b: "모듈 1개 = 테스트 파일 1개." `cache.py`는 라우터도 집계 코어도 아니므로 `test_cache.py`가 미러 대상이다. 현행 `dashboard/backend/tests/` 11파일에 `cache` 대상 케이스 0건임을 실측 확인했다 (E1 — 스코프: `dashboard/backend/tests/` 11파일, 명령 `grep -rn "def test_.*cache" dashboard/backend/tests/`).

케이스명 프리픽스: `[T103/L{계층}-{AC}]` (예: `[T103/L1-R3]`).

---

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표 H-1~H-12 **전건 전재**. 「시나리오」 열만 본 단계에서 확정했다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | `stats.py` 앵커 차분 (F-001) | 역행 타임스탬프에서 소요가 음수 → 스택 막대가 음수 폭으로 파손, opp(n=4) 집계 왜곡 | P0 | L1 | TS-003 |
| H-2 | `stats.py` 앵커 진전 규칙 (F-001) | `in_progress`·`pending`·`na`·파싱 실패 행이 앵커를 진전시키면 뒤따르는 done 행의 소요가 통째로 소실 | P0 | L1 · L2 | TS-001, TS-002, TS-004, TS-009, TS-011, TS-012, TS-034 |
| H-3 | `PipelineRow` 7필드 additive (F-002) | Pydantic 필수 필드로 추가 시 결측 행에서 ValidationError → 상세 패널 500 | P1 | L1 · L2 | TS-004, TS-010, TS-015, TS-024, TS-036, TS-044, TS-063 |
| H-4 | `_get_artifact_files` 화이트리스트 폐기 (F-002) | 소비자 3곳 동반 변동 — 칸반 카드 배지·아카이브 카드 값 변화가 회귀로 오판 | P1 | L2 | TS-014, TS-017, TS-022 |
| H-5 | `dashboard.py` ↔ `tasks.py` 헬퍼 공유 (F-003) | 순환 import — `stats.py`가 모델·라우터를 import하면 라우터↔모델↔stats 순환 | P1 | L1 · L2 | TS-008, TS-023 |
| H-6 | 실시간 파생 캐시 (F-002) | 실시간 값을 캐시에 넣으면 최대 30초 정지 → 분 단위 표시에서 최대 1분 오차 | P2 | L1 · L2 · L3 | TS-005, TS-006, TS-013, TS-018, TS-060 |
| H-7 | 상세 Sheet 2탭 재구성 (F-004) | 읽기 전용 계약 위반 — 탭·표 추가 과정에서 dnd sensors 재활성·🔒 badge 소실 | P0 | L1 · L3 | TS-038, TS-046, TS-060 |
| H-8 | recharts 스택 막대 색상 (F-004·F-005) | hex 리터럴 유입 → [MUST] 토큰 경유 규칙 위반 | P1 | L1 | TS-037, TS-045, TS-062 |
| H-9 | `cache.py` 시계 혼용 수정 (P-8) | `source_path` 전달 시 캐시가 상시 무효화 → 매 요청 전수 재계산(성능 제약 위반) / 수정 오류 시 stale 응답 고착 | P1 | L1 | TS-016 |
| H-10 | 베이스라인 코호트 (F-006) | `102` 완료로 opd 모수 7→8 이동 → 완료기준 (3) 수치 AC가 시점 의존으로 비결정론화 | P1 | L1 · L2 | TS-007, TS-020, TS-021, TS-041, TS-050, TS-051, TS-052, TS-053 |
| H-11 | 목업 ↔ TASK.md 재작성본 충돌 (F-004·F-005) | EXECUTE 워커가 목업을 열고 폐기된 B 블록(혼합 중앙값·스킬/모드 분포)·A-1 4타일을 그대로 구현 | P1 | L1 · L3 | TS-032, TS-033, TS-035, TS-040, TS-042, TS-043, TS-047, TS-061 |
| H-12 | `artifacts` 전수 전환 (F-004) | 탭 9개가 Sheet 폭 초과 → 패널 본문이 가로로 밀림 | P2 | L1 · L2 · L3 | TS-030, TS-031, TS-035, TS-039, TS-062 |

**정량 확인**: 가설 12건 → 시나리오 49건 (가설 N건 → 시나리오 N건 이상 충족). 미매핑 가설 0건.

---

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> 「테이블」 열은 본 태스크의 데이터 원천(파일)이다. DB가 없는 파일 기반 시스템이므로 파일 경로를 식별자로 쓴다.

| 테이블(원천) | 식별자 | 상태 | 출처 |
|-------------|--------|------|------|
| `tasks/{id}/state.json` | `FX-101` = `tasks/101-260824-opd-핸드오프-스키마-계약정합/state.json` | `current_status=done` · 19행 전건 `done` · 게이트 4행(row 4·7·10·17) · `created_at` 2026-08-24 16:32 · 마지막 done 23:37 | 실 파일 동결 복사본 (2026-08-25 기준일) |
| `tasks/{id}/state.json` | `FX-086` = `tasks/086-260810-opp-아키텍처-다이어그램-재작성/state.json` | `current_status=done` · 10행 · **row 5 `plan.user_confirm` 15:46 < row 4 15:47 (역행)** · `created_at` 15:18 · 마지막 done 22:48 | 실 파일 동결 복사본 |
| `tasks/{id}/state.json` | `FX-102` = `tasks/102-260824-opd-태스크분석-경계재정의/state.json` | `current_status=in_progress` · 16행 · `in_progress` 행 **0건** · 첫 `pending` = row 2 `task.user_confirm` · `owner` 전건 `PM`(기본값) · `created_at` 2026-08-24 17:33 | 실 파일 동결 복사본 (2026-08-25 16:03 스냅샷) |
| `tasks/{id}/state.json` | `FX-103` = `tasks/103-260825-opd-태스크-진행통계/state.json` | `current_status=in_progress` · 16행 · row 9 `test_scenario.test_scenario_md` **`in_progress`** · 직전 done = row 8 (16:03) · `created_at` 2026-08-25 13:14 | 실 파일 동결 복사본 (2026-08-25 16:03 스냅샷) |
| 태스크 폴더 | `FX-089` = `tasks/089-260811-opi-opal/` | **`state.json` 부재** · `.md` 산출물만 존재 | 실 폴더 (편집 없음) |
| `tasks/{id}/state.json` | `FX-LEGACY` = `tasks/091-260813-opd-파이프라인-스펙-중복정리/state.json` | `current_status=done` · `gate` 키 보유 행 **0건** (`092` 이전 11개 태스크 공통) | 실 파일 |
| `tasks/*/state.json` 집합 | `FX-COHORT` = 동결 코호트 21건 (opd 080·091·092·093·094·100·101 / opds 081·082·083·085·090·095·096·097·098·099 / opp 084·086·087·088) | 전건 `current_status=done` | 실 파일 집합 + `STATS-BASELINE.md` §2 ID 목록 |
| `FX-101` 파생 | `FX-EMPTY` | `rows: []` (다른 키 동일) | `FX-101`에서 배열 비움 |
| `FX-101` 파생 | `FX-NOCREATED` | `created_at` 키 제거 | `FX-101`에서 키 삭제 |
| `FX-101` 파생 | `FX-BADTS` | row 3 `timestamp` = `"2026-08-24T17:13"` (ISO 표기 — `%Y-%m-%d %H:%M` 불일치) | `FX-101`에서 1필드 훼손 |
| 임시 파일 | `FX-TOUCH` = `tmp_path/state.json` | 임의 내용 1회 기록 → 캐시 저장 → `touch` 가능 | pytest `tmp_path` fixture |
| API 응답 스냅샷 | `FX-DETAIL-101` = `GET /api/tasks/detail?project=<abs>&task_id=101-...` 응답 | `stats.available=true` · `stats` 수치는 **`STATS-BASELINE.md` §5에서 수기 기입** (구현 출력 복사 금지) | 실응답 형태 + 베이스라인 수치 |
| API 응답 스냅샷 | `FX-DETAIL-NOSTATS` | `stats.available=false` · `pipeline: []` · `artifacts: []` | `FX-089` 경로의 실응답 형태 |
| API 응답 스냅샷 | `FX-DASH` = `GET /api/dashboard?project=<abs>` 응답 | `workflow_stats` 3건(opd/opds/opp) · 수치는 **`STATS-BASELINE.md` §3에서 수기 기입** | 실응답 형태 + 베이스라인 수치 |
| API 응답 스냅샷 | `FX-DASH-EMPTY` | `workflow_stats: []` · `completed_tasks: 0` | `FX-DASH`에서 배열 비움 |
| 산출물 문서 | `STATS-BASELINE.md` | PLAN Step 1 생성물 · §1~§6 · §2에 코호트 21건 ID | ANALYSIS.md §8 「재검증 완료 수치」(E1) |
| 배포본 콘솔 | `http://127.0.0.1:7823` | 기동 상태 · 프로젝트 = ai-framework 절대경로 | PLAN Step 13 실행 환경 |

### 2.2 시나리오별 데이터 흐름 (Given / When / Then)

| 시나리오 | Given (read) | When (호출) | Then (re-read) |
|---------|-------------|------------|---------------|
| TS-001 | `FX-101` (19행 done, `created_at` 16:32) | `task_static_stats(FX-101)` | `total_minutes` 425 · `work_minutes` 105 · `wait_minutes` 320 · `wait_ratio` 75 |
| TS-002 | `FX-101` | `task_static_stats(FX-101)["stages"]` | 7그룹 — TASK 24(0/24) · ANALYSIS 22(17/5) · PLAN 13(11/2) · TEST-SCENARIO 295(10/285) · EXECUTE 18(18/0) · TEST 51(47/4) · CLOSE 2(2/0), `is_peak`는 TEST-SCENARIO 1건 |
| TS-003 | `FX-086` (row 5 15:46 역행) | `row_durations(FX-086)` + `task_static_stats(FX-086)` | row 5 `duration_minutes` 0 · 음수 0건 · `total_minutes` 450 = (22:48 − 15:18) |
| TS-004 | `FX-EMPTY` · `FX-NOCREATED` · `FX-BADTS` | 각 입력으로 `task_static_stats` 호출 | 예외 0건 · `FX-EMPTY`·`FX-NOCREATED`는 `available=false` · `FX-BADTS`는 row 3 소요 `None`이고 row 4 이후 소요가 row 2 앵커 기준으로 유지(앵커 미진전) |
| TS-005 | `FX-102` (in_progress 행 0건) | `task_live_stats(FX-102, now=2026-08-25 16:10)` | `current_row_id` 2 · `current_key` `task.user_confirm` · `current_series` `wait` · `total_minutes` 1357 · `is_running` true |
| TS-006 | `FX-101` (완료) | `task_live_stats(FX-101, now=2026-08-24 23:40)` / `now=2026-12-31 00:00` 2회 | 두 호출 모두 `total_minutes` 425 · `is_running` false · `current_row_id` 없음 |
| TS-007 | `FX-COHORT` 21건 | `workflow_stats(FX-COHORT)` | 3건 — opd n=7 median 799 / opds n=10 median 276(원값 275.5) / opp n=4 median 75 · `wait_ratio` 21/4/54 · `opp.sample_insufficient` true, opd·opds false |
| TS-008 | `dashboard/backend/stats.py` 소스 | 모듈 import + AST/`sys.modules` 검사 | import 대상이 `datetime`·`statistics`로 한정 · `dashboard.backend` 하위 모듈 import 0건 |
| TS-009 | 없음 (순수 함수) | `format_duration(x)` — `None`·0·45·105·276·285·295·320·425 | `—` · `0분` · `45분` · `1시간 45분` · `4시간 36분` · `4시간 45분` · `4시간 55분` · `5시간 20분` · `7시간 5분` |
| TS-010 | 실 `tasks/101-*/state.json` + 기동된 앱 | `GET /api/tasks/detail?project=<abs>&task_id=101-...` | `pipeline[].rows[]` 각 원소가 `owner`·`gate`·`note`·`timestamp`·`key` 5키 보유 · `gate` 비-null 행 4건 · `gate`가 `{artifacts, checklist}` 객체(불리언 아님) |
| TS-011 | 동상 | 동상 | `rows[]` 평탄화에서 `row`가 1~19 연속 · `updated_at` 빈 문자열 0건 · `row == row_id`, `updated_at == timestamp` |
| TS-012 | 동상 | 동상 | `stats.total_minutes` 425 · `work` 105 · `wait` 320 · `wait_ratio` 75 · `pipeline[]` 7그룹 소요가 TS-002와 동일 |
| TS-013 | 실 `tasks/102-*`·`tasks/103-*` + `tasks/101-*` | `GET /api/tasks/detail` 3회 | 102·103: `is_running` true · 현재 행이 `in_progress` 우선·없으면 첫 `pending` · `current_series`가 `key`의 `*.user_confirm` 패턴 판정(전건 `owner=PM`에 속지 않음) / 101: `is_running` false · 425 고정 |
| TS-014 | 실 `tasks/101-*/` (`.md` 9개) | `GET /api/tasks/detail` (101) | `artifacts` 길이 9 · `artifact_items` 유형 분포 pipeline 5 · verification 2 · log 2 · other 0 |
| TS-015 | `FX-089` (state.json 부재) · `FX-LEGACY` (gate 0건) | `GET /api/tasks/detail` 2회 | 둘 다 HTTP 200 · `FX-089`는 `stats.available` false · `FX-LEGACY`는 `stats.gate_recorded` false (`gate_count` 0과 구분) |
| TS-016 | `FX-TOUCH` + `CacheStore` 인스턴스 | `set(k, v, source_path=FX-TOUCH)` → `get(k)` → `os.utime(FX-TOUCH)` → `get(k)` | 1차 `get` = 저장값(히트) · `touch` 후 `get` = `None`(미스) · TTL 30초 내에서 성립 |
| TS-017 | 기존 `dashboard/backend/tests/` 11파일 | `python3 -m pytest dashboard/backend/tests/` | 전건 green · 기존 응답 필드 제거·타입 변경 0건. **[PM 2026-08-25 18:20]** Step 8이 전용 케이스 3건을 `[T103/L2-REG2]`로 신설했다(칸반 카드 9필드 · 상세 10+5+4필드(`101`·`089` 파라미터화) · `artifact_count` 예외 항등). 「기존 케이스 수정 0건」은 런타임 메타 테스트로 인코딩하지 않았다 — 케이스명 하드코딩은 정당한 리팩터링에서도 실패하는 오탐 자산이라, `git diff -U0`으로 테스트 코드 삭제 0줄을 확인해 대체했다 |
| TS-018 | 실 `tasks/103-*` + 기동된 앱 | `GET /api/tasks/detail` (103) 2회 연속 — 2차는 캐시 TTL 내 | 두 응답의 정적 파생 동일 · `stats.current_elapsed_minutes`는 2차에서 **재계산**됨(캐시 값 고착 아님) |
| TS-020 | 실 `tasks/*/state.json` 23건 | `GET /api/dashboard?project=<abs>` | `completed_tasks + 진행중 = total_tasks` 항등 · `completed_tasks ≥ 21` · `workflow_stats`의 태스크 합 = `completed_tasks` |
| TS-021 | `FX-COHORT` 필터 적용 실 데이터 | 동상 | `workflow_stats` 3건 · `skill` opd/opds/opp · 코호트 필터 기준 중앙값 799/276/75 · `wait_ratio` 21/4/54 |
| TS-022 | 실 `tasks/*/` `.md` 전수 | 동상 | `artifact_total == sum(artifact_by_type.values())` · `artifact_by_type` 4키(pipeline/verification/log/other) |
| TS-023 | 대시보드·상세 응답 JSON 전문 | `GET /api/dashboard` + `GET /api/tasks/detail` | 응답 JSON에 `workflow` 키 0건 · `skill`·`timestamp`·`row_id` 키 사용 · `stats.py`가 라우터·모델 import 0건 |
| TS-024 | 기존 `DashboardSummaryResponse` 8필드 | `GET /api/dashboard` | `total_projects`·`running_tasks`·`blockers`·`additional_work`·`status_distribution`·`activity_trend`·`alerts`·`recent_activities` 값·타입 불변 |
| TS-030 | `FX-DETAIL-101` 주입 | 상세 Sheet 렌더 | 탭 2개(「태스크 대시보드」·「산출물」) · 기본 활성 「태스크 대시보드」 · 산출물 탭 배지 9 |
| TS-031 | 동상 | 탭 전환 조작 | 각 탭 본문이 자체 영역에서만 세로 스크롤 · `SheetHeader`(ID·배지·기간) 고정 유지 |
| TS-032 | 동상 | A-1 렌더 | 4타일 = `7시간 5분` / `1시간 45분` / `5시간 20분 (75%)` / `TEST-SCENARIO` |
| TS-033 | 동상 | A-2 렌더 | 막대 7개 · TEST-SCENARIO가 최장(`4시간 55분`) 강조 · 그 막대가 대기 285 : 작업 10으로 2색 분할 |
| TS-034 | 동상 | A-3 렌더 | 시각 오름차순 19항목 · TEST-SCENARIO 사용자 확인 구간 공백 `4시간 45분` 표시 · 담당 구분이 색 단독이 아니라 라벨 동반 |
| TS-035 | 동상 | A-4 렌더 | 19행 · `GATE` 표시 4건 · 소요가 작업·대기 2열로 분리 · 표가 자체 가로 스크롤 컨테이너 안에서만 스크롤 |
| TS-036 | `FX-DETAIL-NOSTATS` 주입 | 상세 Sheet 렌더 | A-1~A-4 자리에 "데이터 없음" · 렌더 예외 0건 · 콘솔 에러 0건 |
| TS-037 | 신규·수정 FE 파일 소스 | 정적 검사 (`#[0-9a-fA-F]{3,8}` 매칭) | hex 색상 리터럴 0건 |
| TS-038 | `FX-DETAIL-101` + 칸반 목록 | 칸반 렌더 + 드래그 시도 | 카드 드래그 불가 · 🔒 badge 상시 표시 · 5컬럼 배치·정렬 불변 |
| TS-039 | `FX-DETAIL-101` (탭 9개) | 「산출물」 탭 렌더 | `TabsList`가 자체 `overflow-x-auto` 컨테이너 안에서만 가로 스크롤 · Sheet 본문 가로 밀림 0 |
| TS-040 | `FX-DASH` 주입 | B-4에서 워크플로우 선택 | B-1~B-3이 선택 `skill`로 좁혀짐 · API 재호출 0건 |
| TS-041 | 동상 | opp 선택 | 「표본 부족」 배지 표시 (n=4) · opd·opds 선택 시 배지 미표시 |
| TS-042 | 동상 | B-2 렌더 | 각 단계 막대에 `n=` 표기 존재 · 워크플로우 전환 시 단계 로스터와 `n`이 함께 변경 (opd n=7 · opds n=10 · opp n=4) — **PM 재정의 2026-08-25 18:05** |
| TS-043 | 동상 | B-1 렌더 | 완료 21 / 전체 23 병기 · 산출물 `.md` 수 · 선택 워크플로우 중앙값 표시 |
| TS-044 | `FX-DASH-EMPTY` 주입 | 대시보드 렌더 | B-1~B-4 자리에 "데이터 없음" · 콘솔 에러 0건 |
| TS-045 | 신규·수정 FE 파일 소스 | 정적 검사 | hex 색상 리터럴 0건 |
| TS-046 | `FX-DASH` 주입 | 대시보드 렌더 | 기존 4메트릭·활동추이·상태 파이·알림·최근활동 렌더 불변 |
| TS-047 | 동상 + `mockup/dashboard.html` 폐기 목록 | 대시보드 전체 렌더 | 혼합 중앙값 `5시간 42분` 문자열 0건 · B-3에 진행 중(`102`·`103`) 막대 0건 · B-4가 분포 차트가 아니라 필터로 동작 |
| TS-050 | `STATS-BASELINE.md` | 산출물 검사 | §1~§6 6절 존재 · §2에 코호트 태스크 ID 21건 전량 · §1에 측정 명령·스코프 · 「91」 표기 0건 |
| TS-051 | `STATS-BASELINE.md` §5 + 기동된 콘솔 | `GET /api/tasks/detail` (101) + 화면 표시값 | 베이스라인 §5 수치와 응답·화면 표시값이 전건 일치 (완료기준 (1)(2)) |
| TS-052 | `STATS-BASELINE.md` §2 코호트 + 기동된 콘솔 | `GET /api/dashboard` → §2 ID로 필터 재계산 | 799/276/75분과 일치 (완료기준 (3)) · `102` 완료 여부와 무관 |
| TS-053 | `dashboard/` 트리 | 파일 검사 | `dashboard/` 하위에 스냅샷 파일 0건 |
| TS-060 | 기동된 콘솔 + 실 101 데이터 | [SUPERVISOR] 캡틴이 101 상세를 열고 A-1~A-4를 읽는다 | 병목 단계(TEST-SCENARIO)와 캡틴 대기 구간(285분)을 화면만 보고 식별 가능 · 진행 중 태스크에서 「진행 중」 배지 확인 |
| TS-061 | 기동된 콘솔 + 실 대시보드 | [SUPERVISOR] 캡틴이 B-4로 opd→opds→opp를 전환한다 | 워크플로우별 대기 비중 차이(21%/4%/54%)를 화면에서 대조 가능 · 혼합 집계가 화면에 0건 |
| TS-062 | 기동된 콘솔 (127.0.0.1:7823) | cmux(1순위)→playwright(폴백) E2E — 칸반 진입 → 101 카드 클릭 → 탭 전환 → 산출물 탭 | 2탭·A블록 렌더 · 탭 바 가로 스크롤 격리 · 브라우저 콘솔 에러 0건 |
| TS-063 | 기동된 콘솔 Swagger UI (`http://127.0.0.1:7823/docs`) | cmux browser로 `/api/tasks/detail`·`/api/dashboard` 실행 | 두 엔드포인트 200 · 응답 스키마에 신규 필드 존재 · 결측 태스크(`089`)에서도 200 |

---

## 3. 검증 시나리오

### 3.0 RED 실행 배치 (RED-first 강제 트랙 — 21건)

[MUST] `~/.opal/references/harness/red-first.md` §1: "RED 단계에서 실패 테스트 코드를 작성·실행하여 실패(exit code≠0)를 증거로 기록한 뒤 GREEN(구현) 진입. RED 증거 없이 GREEN 진입 금지."
[MUST] 동 §2: "RED 테스트 코드 작성 주체는 EXECUTE 구현 워커(op-dev-execute)와 분리한다. RED 작성은 opal-test-agent(mode: red)가 담당한다."

PLAN §4.2는 BE 테스트를 Step 8(구현 후)에 배치했다. RED-first 강제 트랙에서는 **해당 구현 Step보다 앞선 RED 배치**가 선행 조건이므로 아래 3배치로 분해한다. Step 8은 RED 케이스의 GREEN 확인 + 잔여 회귀 케이스 확장으로 수행한다.

| 배치 | 시나리오 | 대상 파일 | 선행 위치 | RED 증거 |
|------|---------|----------|----------|---------|
| **R1** | TS-016 | `dashboard/backend/tests/test_cache.py` (신규) | PLAN Step 2 **직전** | `touch` 후에도 히트하거나 미변경에도 미스 → 실패 |
| **R2** | TS-001~TS-009 | `dashboard/backend/tests/test_stats.py` (신규) | PLAN Step 3 **직전** | `dashboard.backend.stats` 모듈 부재 → ImportError로 실패 |
| **R3** | TS-010~TS-015, TS-018, TS-020~TS-023 | `dashboard/backend/tests/test_routers.py` (기존 파일 추가) | PLAN Step 5·7 **직전** | 응답에 `stats`·`artifact_items`·`workflow_stats` 키 부재, `rows[]`에 신규 5키 부재 → KeyError/assert 실패 |

- [MUST] 동 §3: GREEN/fix 루핑 중 **RED 테스트 파일 수정 금지**. 통과를 위해 단정을 약화·삭제·완화하면 블로커다.
- [MUST] 동 §4: 내부 구현·private 결합 금지 — 공개 시그니처 반환값·HTTP 응답·exit code로만 검증한다.
- RED 증거는 `tasks/103-260825-opd-태스크-진행통계/RED-EVIDENCE.md`에 배치별 실행 명령·exit code로 기록한다.

---

### L1. 기능 단위 (자동, 실 데이터 입력) — 30건

#### TS-001: 101 총 리드타임 2계열 분해

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `stats.py` `task_static_stats` — 앵커 차분·2계열 귀속 (F-001) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `FX-101` 동결 복사본(19행 전건 `done`, `created_at` 2026-08-24 16:32, 마지막 done 23:37). `owner=user` 5행(row 2·5·8·11·18)이 대기 계열 |
| 기대 결과 | `total_minutes` == 425 · `work_minutes` == 105 · `wait_minutes` == 320 · `work + wait == total` · `wait_ratio` == 75 · `total_label` == `7시간 5분` |
| RED 기대 실패 | `dashboard.backend.stats` 미존재 → `ImportError`. exit code ≠ 0 |
| 도구 | pytest (`test-tool resolve` unit.be.unit) |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-002: 101 단계별 작업·대기 합계 7그룹

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `stats.py` `task_static_stats(...)["stages"]` (F-001) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `FX-101`. 단계는 TASK·ANALYSIS·PLAN·TEST-SCENARIO·EXECUTE·TEST·CLOSE 7종이며 원 행 순서에서 연속 |
| 기대 결과 | 7그룹 · TASK 24(work 0 / wait 24) · ANALYSIS 22(17/5) · PLAN 13(11/2) · TEST-SCENARIO 295(10/285) · EXECUTE 18(18/0) · TEST 51(47/4) · CLOSE 2(2/0) · `is_peak` true는 TEST-SCENARIO 1건 · 7그룹 `total_minutes` 합 == 425 |
| RED 기대 실패 | 동상 (`ImportError`) → 구현 후 `stages` 키 부재 시 `KeyError` |
| 도구 | pytest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-003: 역행 타임스탬프 0 clamp + 단조 앵커 총합 항등

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `stats.py` `row_durations`·`task_static_stats` — 음수 clamp·단조 앵커 (F-001) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `FX-086`. row 4 `plan.pm_gate` 15:47(done) 다음 row 5 `plan.user_confirm` 15:46(done, `owner=auto`) — 차분 −1분 |
| 기대 결과 | row 5 `duration_minutes` == 0 · 전 행 `duration_minutes >= 0` (음수 0건) · `total_minutes` == 450 == (22:48 − 15:18) — clamp 후에도 총합 항등 보존 · row 6 소요가 45분(15:47 앵커 기준)으로 부풀지 않음 |
| RED 기대 실패 | clamp·단조 앵커 미구현 시 row 5 == −1, 총합 449 → assert 실패 |
| 도구 | pytest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-004: 결측 내성 3경로 — 빈 rows · created_at 결측 · 파싱 실패

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-3 |
| 대상 | `stats.py` 결측 차단 단일 지점 (F-001) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `FX-EMPTY`(`rows: []`) · `FX-NOCREATED`(`created_at` 키 없음) · `FX-BADTS`(row 3 `timestamp`가 `2026-08-24T17:13` ISO 표기) 3케이스 |
| 기대 결과 | 3케이스 전건 예외 0건(IndexError·ValueError·KeyError 미발생) · `FX-EMPTY`·`FX-NOCREATED` → `available` false · `FX-BADTS` → row 3 `duration_minutes` `None`이고 **앵커 미진전**이므로 row 4 소요가 row 2 앵커(16:56) 기준으로 계산됨 · `FX-BADTS`의 나머지 행 소요는 `FX-101`과 동일 |
| RED 기대 실패 | 방어 없는 구현에서 `strptime` `ValueError` 또는 `rows[0]` `IndexError` 발생 → 테스트 에러 |
| 도구 | pytest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-005: 실시간 현재 행 식별 + key 패턴 대기 귀속 (now 고정 주입)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `stats.py` `task_live_stats(state, now)` — 집계기준 12·13·14 (F-001) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `FX-102` 동결본(`in_progress` 행 0건, 첫 `pending` = row 2 `task.user_confirm`, **`pending` 15행 전건 `owner=PM` 기본값**, `created_at` 2026-08-24 17:33, 마지막 done = row 1 17:33) + `now=datetime(2026,8,25,16,10)` 고정 주입 |
| 기대 결과 | `is_running` true · `current_row_id` == 2 · `current_key` == `task.user_confirm` · `current_series` == `wait` (**`owner=PM`을 쓰지 않고 `key` 패턴으로 판정**) · `total_minutes` == 1357 · `current_elapsed_minutes` == 1357 |
| RED 기대 실패 | `owner` 기반 귀속 구현에서 `current_series`가 `work`로 나옴 → assert 실패. `now` 파라미터 부재 시 `TypeError` |
| 도구 | pytest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-006: 완료 태스크는 실시간을 쓰지 않는다 (now 무관 고정)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `stats.py` `task_live_stats` — 집계기준 11 (F-001) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `FX-101`(`current_status=done`) + `now`를 2회 다르게 주입 — `2026-08-24 23:40` / `2026-12-31 00:00` |
| 기대 결과 | 두 호출 모두 `total_minutes` == 425 (동일) · `is_running` false · `current_row_id` `None` · `current_elapsed_minutes` `None` |
| RED 기대 실패 | 완료 분기 없이 `now`를 항상 쓰는 구현에서 2차 호출이 425 ≠ 값으로 벌어짐 → assert 실패 |
| 도구 | pytest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-007: 동결 코호트 21건 워크플로우별 집계

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `stats.py` `workflow_stats(states)` — 집계기준 3·4·5 (F-001) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `FX-COHORT` 21건 (`STATS-BASELINE.md` §2 ID 목록으로 필터한 실 `state.json` 집합). 진행 중 2건(`102`·`103`)은 입력에서 제외된다 |
| 기대 결과 | 반환 3건(`skill` = opd·opds·opp) · opd n=7 `median_minutes` 799 (`13시간 19분`) · opds n=10 `median_minutes` 276 (**원 중앙값 275.5의 정수 반올림 — 짝수 n 경계**) · opp n=4 `median_minutes` 75 (`1시간 15분`) · `wait_ratio` 21 / 4 (**원값 3.68% 반올림 경계**) / 54 · `sample_insufficient`가 opp만 true · 응답 키가 `skill`(`workflow` 아님) |
| RED 기대 실패 | `workflow_stats` 미구현 → `AttributeError`. 반올림 규칙 미정 시 opds가 275 또는 275.5로 나와 assert 실패 |
| 도구 | pytest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-008: `stats.py` 순수 모듈 경계 (순환 import 차단)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `dashboard/backend/stats.py` import 목록 (F-001) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `stats.py` 소스 파일. [MUST] `PLAN.md` §8 확정값: "`stats.py` 의존 범위 — 표준 라이브러리(`datetime`·`statistics`)만. 모델·라우터·캐시 import 금지" |
| 기대 결과 | AST 파싱 결과 import 대상이 `datetime`·`statistics`(및 `__future__`)로 한정 · `dashboard.backend` 하위 모듈 import 0건 · 파일 I/O 호출(`open`·`json.load`·`os.path`) 0건 |
| RED 기대 실패 | 모듈 부재 → `FileNotFoundError`/`ImportError` |
| 도구 | pytest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-009: `format_duration` 표시 문자열 5규칙 (P-7)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `stats.py` `format_duration(minutes)` — BE 표시 문자열 단일 소유 (F-001) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 순수 함수. 입력은 A-1·A-2·B-1이 실제로 표시하는 값 계열을 포함한다 |
| 기대 결과 | `None`→`—` · `0`→`0분` · `45`→`45분` · `105`→`1시간 45분` · `276`→`4시간 36분` · `285`→`4시간 45분` · `295`→`4시간 55분` · `320`→`5시간 20분` · `425`→`7시간 5분` · `120`→`2시간`(나머지 0이면 「분」 생략) |
| RED 기대 실패 | 함수 미존재 → `AttributeError`. 0분·`None` 경계 미처리 시 `0시간 0분`·`None분` 등으로 실패 |
| 도구 | pytest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-016: `cache.py` mtime 무효화 실동작 (P-8 시계 교정)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | `dashboard/backend/cache.py` `CacheStore.get`/`set` — wall-clock 비교 교정 (F-002 / PLAN Step 2) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | `FX-TOUCH`(pytest `tmp_path/state.json`). **교정 전 실측**: `set`이 저장하는 `expires_at`은 `time.monotonic()` 기반(약 609,212)이고 `get`은 이를 epoch `os.path.getmtime()`(약 1,781,516,662)과 직접 비교해 `current_mtime > cached_since`가 **항상 참** → `source_path` 지정 항목이 상시 무효화된다 (`dashboard/backend/cache.py:45-51`·`:58-60`) |
| 기대 결과 | (a) `set(k, v, source_path=FX-TOUCH)` 직후 `get(k)`가 저장값 반환(**히트**) — 파일 미변경 시 TTL 30초 내 상시 무효화되지 않는다 (b) `os.utime(FX-TOUCH)` 후 `get(k)`가 `None`(**미스**) (c) `source_path=None` 항목은 TTL 축만으로 히트 (d) 공개 시그니처 `get`/`set`/`invalidate`/`clear` 무변경 · `TTL_SECONDS` 값 불변 |
| RED 기대 실패 | 교정 전 코드에서 (a)가 `None`을 반환 → assert 실패. exit code ≠ 0이 P-8 결함의 회귀 방지 증거다 |
| 도구 | pytest (`dashboard/backend/tests/test_cache.py` 신규) |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-030: 상세 Sheet 2탭 분리 + 산출물 배지 9

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-12 |
| 대상 | `TasksPage.tsx` `TaskDrawer` 2탭 재구성 (F-004, R-5) |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest + Testing Library)** |
| 조건 | `FX-DETAIL-101` 주입(`artifacts` 9건 — `TASK`·`ANALYSIS`·`PLAN`·`TEST-SCENARIO`·`DONE`·`SCENARIO-GATE-1`·`GC-CONVENTION-260824`·`STATE`·`AGENTIC-LOG`). 배지 9는 **BE 화이트리스트 폐기(TS-014) 선행 필수** — FE 단독으로는 5까지만 나온다 |
| 기대 결과 | 탭 2개 렌더 · 접근 가능한 이름이 「태스크 대시보드」·「산출물」 · 기본 활성 탭이 「태스크 대시보드」 · 「산출물」 탭에 배지 텍스트 `9` |
| 도구 | vitest (`test-tool resolve` unit.fe.unit) |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-031: 탭 전환 시 헤더 고정 + 탭별 자체 세로 스크롤

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-12 |
| 대상 | `TasksPage.tsx` Sheet 레이아웃 (F-004, R-5) |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest + Testing Library)** |
| 조건 | `FX-DETAIL-101` 주입 후 「산출물」 탭 → 「태스크 대시보드」 탭 전환 조작 |
| 기대 결과 | 두 탭 모두에서 `SheetHeader`의 태스크 ID·상태 배지·기간이 계속 렌더 · 각 `TabsContent`가 자체 스크롤 컨테이너를 보유(세로 스크롤이 Sheet 전체가 아닌 탭 본문에서 발생) · 탭 전환으로 API 재호출 0건 |
| 도구 | vitest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-032: A-1 요약 4타일 표시 문자열

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | `TasksPage.tsx` `StatsSummaryCards` (F-004, R-6) |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest + Testing Library)** |
| 조건 | `FX-DETAIL-101` 주입 — `stats.total_label` `7시간 5분` · `work_label` `1시간 45분` · `wait_label` `5시간 20분` · `wait_ratio` 75 · `peak_stage` `TEST-SCENARIO`. 값은 `STATS-BASELINE.md` §5 수기 기입분 |
| 기대 결과 | 4타일 — `7시간 5분` / `1시간 45분` / `5시간 20분 (75%)` / `TEST-SCENARIO` · **목업 A-1 구성(「완료 단계」·「게이트·블로커」)이 렌더되지 않음**(H-11 폐기 경계) · FE에 시간 포맷 산술 코드 0건(BE 라벨 직독) |
| 도구 | vitest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-033: A-2 단계별 2색 스택 막대 7개 + 최장 강조

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | `TasksPage.tsx` `StageStackBars` (F-004, R-7) |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest + Testing Library)** |
| 조건 | `FX-DETAIL-101` 주입 — `pipeline[]` 7그룹(TS-002 수치), TEST-SCENARIO가 `is_peak` |
| 기대 결과 | 막대 7개 · TEST-SCENARIO 막대에 최장 강조 표식 + `4시간 55분` · 그 막대가 작업 10 : 대기 285 두 구획으로 분할(**단일색 채움 아님** — 목업 폐기 경계) · 폭 비율이 `total_minutes / max(total_minutes)`에서 파생 |
| 도구 | vitest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-034: A-3 타임라인 오름차순 + 최대 공백 + 라벨 동반

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `TasksPage.tsx` `RowTimeline` (F-004, R-8) |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest + Testing Library)** |
| 조건 | `FX-DETAIL-101` 주입 — `pipeline[].rows[]` 평탄화 19행, row 11(`test_scenario.user_confirm`, 17:41→22:26)이 `is_max_gap` |
| 기대 결과 | 시각(`time_label`)이 오름차순 19항목 · row 11 구간에 공백 `4시간 45분` + 「최대 공백」 표기 · 담당 구분이 색 단독이 아니라 `owner_label`(`PM`/`캡틴`/`자동`) 텍스트를 동반 |
| 도구 | vitest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-035: A-4 상세 표 19행 + 게이트 4건 + 2열 분리 + 스크롤 격리

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11, H-12 |
| 대상 | `TasksPage.tsx` `RowDetailTable` (F-004, R-9) |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest + Testing Library)** |
| 조건 | `FX-DETAIL-101` 주입 — 19행 중 `gate` 비-null 4행(row 4 `analysis.pm_gate` · row 7 `plan.pm_gate` · row 10 `test_scenario.scenario_gate` · row 17 `test.pm_gate`) |
| 기대 결과 | 데이터 행 19 · `GATE` 표시 4건 · 소요 열이 작업·대기 **2열로 분리**(목업 단일 열 폐기) · 표 래퍼가 자체 `overflow-x-auto` 컨테이너 · 표의 `#` 열이 1~19 연속(`row_id` 직독) |
| 도구 | vitest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-036: 상세 결측 축소 표시 (데이터 없음)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `TasksPage.tsx` A-1~A-4 결측 분기 (F-004, R-12) |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest + Testing Library)** |
| 조건 | `FX-DETAIL-NOSTATS` 주입(`stats.available` false · `pipeline` 빈 배열 · `artifacts` 빈 배열) — `FX-089`(`state.json` 부재 태스크) 경로의 실응답 형태 |
| 기대 결과 | A-1~A-4 자리에 "데이터 없음" 1줄 · 렌더 예외 0건 · 콘솔 에러 0건 · Sheet가 정상적으로 열림 · `stats.gate_recorded` false일 때 게이트 지표가 `0`이 아니라 「미기록」 |
| 도구 | vitest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-037: 상세 화면 hex 색상 리터럴 0건

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | `TasksPage.tsx` + `TasksPage.stats.test.tsx` (F-004, R-13) |
| 계층 | L1 |
| **실행 방식** | **M1 (정적 검사 — vitest 케이스 또는 lint 규칙)** |
| 조건 | [MUST] `dashboard/frontend/src/index.css` `:root`: "모든 컴포넌트는 이 토큰(또는 shadcn 표준 토큰)을 경유해야 한다. hex 하드코딩 금지 — oklch() 함수 값만 사용한다." 신규·수정 FE 파일 소스 전문 |
| 기대 결과 | 정규식 `#[0-9a-fA-F]{3,8}` 매칭 0건 · 2계열 색이 `var(--brand-primary)`(작업)·`var(--brand-tertiary)`(대기) CSS 변수 문자열 전달 패턴 · 기존 `PIE_COLORS`(`DashboardPage.tsx:246-251`)는 **수정하지 않음**(인접 개선 금지) |
| 도구 | vitest / grep |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-038: 칸반 읽기 전용 회귀 0

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `TasksPage.tsx` 칸반 보드 (F-004, P-4 회귀 경계 3) |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest + Testing Library)** |
| 조건 | [MUST] `dashboard/frontend/src/pages/tasks/TasksPage.tsx:1-9` `@header`: "[MUST] 읽기 전용: dnd-kit sensors 비활성·🔒 badge 상시·grab 커서 미사용". 칸반 목록 응답 주입 후 렌더 |
| 기대 결과 | 5컬럼 배치·정렬 불변 · 🔒 badge 상시 렌더 · dnd sensors 비활성(드래그 조작으로 컬럼 이동 발생 0건) · grab 커서 클래스 0건 · 통계 블록에 쓰기·편집·정렬 토글 조작 0건 |
| 도구 | vitest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-039: 산출물 탭 9개 가로 스크롤 격리 (신규 보강 — H-12)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-12 |
| 대상 | `TasksPage.tsx` 「산출물」 탭 `TabsList` (F-004, R-5 / TASK §제약 「가로 스크롤 격리」) |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest + Testing Library)** |
| 조건 | `FX-DETAIL-101` 주입 — `artifact_items` 9건이 `pipeline`(5) → `verification`(2) → `log`(2) → `other`(0) 순으로 정렬. Sheet 폭은 `w-[min(50vw,800px)]` (`TasksPage.tsx:366`) |
| 기대 결과 | `TabsList`가 `overflow-x-auto` 래퍼 안에 존재 · Sheet 본문 컨테이너에 가로 스크롤 0 · 탭 순서가 pipeline → verification → log → other · 유형 라벨(파이프라인/검증/로그/기타)이 구분자로 표시 |
| 도구 | vitest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-040: B-4 필터 → B-1~B-3 좁힘 (API 재호출 0)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | `DashboardPage.tsx` `WorkflowFilter` (F-005, R-11) |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest + Testing Library)** |
| 조건 | `FX-DASH` 주입(`workflow_stats` 3건). 필터 상태는 `DashboardPage` 로컬 `useState` + 기존 `ToggleGroup` 패턴 |
| 기대 결과 | opd → opds → opp 선택 시 B-1 중앙값·B-2 단계 막대·B-3 태스크 막대가 해당 `skill` 값으로 교체 · **API 재호출 0건**(주입한 응답 조회 횟수 불변) · B-4가 분포 차트가 아니라 필터 진입점으로 동작 |
| 도구 | vitest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-041: 표본 부족 배지 (n<5 경계)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `DashboardPage.tsx` B-4·B-1 배지 (F-005, R-11 / 집계기준 5) |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest + Testing Library)** |
| 조건 | `FX-DASH` 주입 — opd n=7 · opds n=10 · opp n=4(`sample_insufficient` true) |
| 기대 결과 | opp 선택 시 「표본 부족」 배지 표시 · opd·opds 선택 시 배지 0건 · 배지 판정이 FE 계산이 아니라 `sample_insufficient` 직독 |
| 도구 | vitest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-042: B-2 단계별 `n=` 모수 표기

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | `DashboardPage.tsx` `WorkflowStageBars` (F-005, R-11) |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest + Testing Library)** |
| 조건 | `FX-DASH` 주입 — 워크플로우별 `stages[]`. 각 단계의 `n`은 **그 워크플로우의 완료 태스크 수**다(opd 7단계 전건 n=7 · opds 5단계 전건 n=10 · opp 4단계 전건 n=4) |
| 기대 결과 | 각 단계 막대 라벨에 `n=` 표기 존재 · **B-4로 워크플로우를 전환하면 단계 로스터와 각 단계 `n`이 함께 바뀐다** · FE가 전역 단일 모수를 가정하지 않고 각 단계의 자체 `n`을 읽는다 · 목업의 혼합 단계별 평균 표기 0건 |
| **[PM 재정의 2026-08-25 18:05]** | 원 조건절의 「EXECUTE 21 · TEST 17 · TEST-SCENARIO 7」은 **폐기된 혼합 집계 설계**의 값이라 워크플로우 축이 살아 있는 한 어떤 단일 응답에도 그 형태로 존재하지 않는다(`TASK.md` 집계 기준 4 「혼합 집계 미제공」과 충돌). 기대 결과 3항 중 「`n=` 표기」·「혼합 평균 0건」은 R-11 AC에 그대로 대응해 유효하므로 **무효 선언이 아니라 재정의**한다. 원 의도(단일 모수 가정 금지)는 위 문면에 보존됐다. 판정: EXECUTE Step 13 검증자 / 반영: PM |
| 도구 | vitest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-043: B-1 요약 5타일 (완료/전체 병기)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | `DashboardPage.tsx` `WorkflowSummaryCards` (F-005, R-10) |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest + Testing Library)** |
| 조건 | `FX-DASH` 주입 — `completed_tasks` 21 · `total_tasks` 23 · `artifact_total` · 선택 `skill`의 `median_label`·`mean_label`·`wait_ratio` |
| 기대 결과 | 완료 21 / 전체 23 병기 · 산출물 `.md` 수 표시 · 선택 워크플로우 중앙값이 주 지표로, 평균이 보조로 표시 · opd 선택 시 `13시간 19분`(799분) |
| 도구 | vitest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-044: 대시보드 결측 축소 표시

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `DashboardPage.tsx` B-1~B-4 결측 분기 (F-005, R-12) |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest + Testing Library)** |
| 조건 | `FX-DASH-EMPTY` 주입(`workflow_stats: []` · `completed_tasks: 0`) |
| 기대 결과 | B-1~B-4 자리에 "데이터 없음" 1줄 · 렌더 예외 0건 · 콘솔 에러 0건 · 기존 5블록은 정상 렌더 |
| 도구 | vitest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-045: 대시보드 hex 색상 리터럴 0건

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | `DashboardPage.tsx` 신규 코드 + `DashboardPage.stats.test.tsx` (F-005, R-13) |
| 계층 | L1 |
| **실행 방식** | **M1 (정적 검사)** |
| 조건 | 신규·수정 FE 파일 소스 전문. 신규 코드의 색은 `var(--brand-primary)`·`var(--brand-tertiary)`·`var(--brand-secondary)` |
| 기대 결과 | `#[0-9a-fA-F]{3,8}` 매칭 0건 · 기존 `PIE_COLORS` 블록 변경 0건(diff 미포함) |
| 도구 | vitest / grep |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-046: 대시보드 기존 5블록 회귀 0

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `DashboardPage.tsx` 기존 블록 (F-005, P-4 회귀 경계 3) |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest + Testing Library)** |
| 조건 | `FX-DASH` 주입. B 블록은 기존 5블록 **아래**에 추가된다 |
| 기대 결과 | 4메트릭 카드·활동 추이 차트·상태 파이·알림·최근 활동 표가 전건 렌더 · 배치 순서 불변 · 기존 블록 값이 B 블록 추가로 변하지 않음 |
| 도구 | vitest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-047: 목업 폐기 블록 잔존 0 (신규 보강 — H-11)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | `DashboardPage.tsx` B-1~B-4 (F-005) · 목업 ↔ TASK.md 재작성본 경계 |
| 계층 | L1 |
| **실행 방식** | **M1 (vitest + Testing Library)** |
| 조건 | `FX-DASH` 주입. [MUST] `PLAN.md` §3.5.2: "목업은 레이아웃·정보 밀도의 시각 형태 근거로만 계승하고, 수치 정의·블록 의미는 TASK.md 재작성본을 따른다" |
| 기대 결과 | 화면 전체 텍스트에 혼합 중앙값 `5시간 42분` 0건 · B-3에 진행 중(`102`·`103`) 막대 0건(완료 태스크만) · B-4가 「스킬·모드 분포」 막대가 아니라 필터 컨트롤 · A 화면에서 목업 A-1 타일 라벨(「완료 단계」·「게이트·블로커」) 0건 |
| 도구 | vitest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-050: `STATS-BASELINE.md` 구조 6절 + 코호트 21건

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `tasks/103-260825-opd-태스크-진행통계/STATS-BASELINE.md` (F-006, R-14) |
| 계층 | L1 |
| **실행 방식** | **M1 (산출물 검사 — grep/스크립트)** |
| 조건 | PLAN Step 1 산출물. §3~§5 수치 원천은 ANALYSIS.md §8 「재검증 완료 수치」(E1) |
| 기대 결과 | §1~§6 6절 전건 존재 · §2에 코호트 태스크 ID 21건 전량 열거(opd 7 · opds 10 · opp 4) · §1에 측정 명령 원문·스코프·근거 등급 E1 기재 · 「91」 표기 0건(정정값 92 사용) · §6에 이동값 경고와 각 값의 측정 시각 병기 |
| 도구 | grep / python3 |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-053: 런타임 경로 스냅샷 0건

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `dashboard/` 트리 (F-006, R-14) |
| 계층 | L1 |
| **실행 방식** | **M1 (산출물 검사)** |
| 조건 | [MUST] `TASK.md` R-14 AC: "런타임 경로에는 스냅샷 파일을 두지 않는다." |
| 기대 결과 | `dashboard/` 하위에 `STATS-BASELINE`·통계 스냅샷 파일 0건 · 스냅샷은 태스크 폴더에만 존재 |
| 도구 | find / grep |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

---

### L2. 프로세스 통합 (자동, 실 `state.json` read → API 호출 → 응답 re-read) — 17건

> 본 태스크는 쓰기 동작이 0건인 조회 전용 기능이다([MUST] `TASK.md` §제약 조건 「읽기 전용 유지」). 따라서 L2의 `read → CUD → re-read` 사이클은 **`read(실 state.json) → 호출(GET API) → re-read(응답·재조회)`** 로 성립한다. 실 파일을 편집해 사이클을 만들지 않는다 — [MUST] `docs/CONVENTIONS.md` §State 관리: "`state.json` 직접 편집 금지."

#### TS-010: `PipelineRow` 5키 확장 + `gate` 객체 직렬화

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `models.py` `PipelineRow`·`PipelineGate` + `tasks.py` `_group_pipeline_stages` (F-002, R-2) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + httpx TestClient — 실 `tasks/*/state.json` 대상)** |
| 조건 | 실 `tasks/101-260824-opd-핸드오프-스키마-계약정합/state.json`(19행, `gate` 보유 4행). 요청: `GET /api/tasks/detail?project=<ai-framework 절대경로>&task_id=101-260824-opd-핸드오프-스키마-계약정합` |
| 기대 결과 | HTTP 200 · `pipeline[].rows[]` 각 원소가 `owner`·`gate`·`note`·`timestamp`·`key` 5키 보유 · `gate` 비-null 행 정확히 4건 · `gate`가 `{"artifacts": [...], "checklist": [...]}` 객체로 직렬화(**불리언 아님**) · 나머지 15행의 `gate`는 `null` · 신규 필드 전건 기본값 보유(ValidationError 0건) |
| RED 기대 실패 | 확장 전 응답의 `rows[]`가 `row`·`stage`·`status`·`updated_at` 4키뿐 → 5키 존재 assert 실패 |
| 도구 | pytest + httpx (`test-tool resolve` integration.be.api_db) |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-011: 사표 필드 교정 — `row` 1~19 연속 · `updated_at` 빈 문자열 0건

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `tasks.py` `_group_pipeline_stages` 행 매핑 교정 (F-002, R-2 AC(추가)) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + httpx TestClient)** |
| 조건 | 실 101 `state.json`. **현행 결함**: `_group_pipeline_stages`가 원천에 없는 `row`·`updated_at` 키를 읽어(`dashboard/backend/routers/tasks.py:259-267`) `row`는 그룹 내부 0-based 인덱스로 폴백하고 `updated_at`은 전건 빈 문자열이 된다 |
| 기대 결과 | `pipeline[].rows[]` 평탄화 19행에서 `row` 값이 **1·2·…·19 연속**(그룹마다 0으로 리셋되지 않음) · `updated_at` 빈 문자열 **0건** · 전 행에서 `row == row_id` 및 `updated_at == timestamp` · 원천 용어 키 `row_id`·`timestamp`가 함께 존재 |
| RED 기대 실패 | 교정 전 응답에서 `row`가 각 그룹 0부터 다시 시작하고 `updated_at`이 19건 전건 `""` → assert 실패 |
| 도구 | pytest + httpx |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-012: 상세 응답 소요 파생 — BE 값이 L1 계산과 동일

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `tasks.py` `get_task_detail` ← `stats.py` 결합 (F-002, R-3) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + httpx TestClient)** |
| 조건 | 실 101 `state.json`. 기대값 원천은 `STATS-BASELINE.md` §5(= ANALYSIS §8 E1 독립 재측정) |
| 기대 결과 | `stats.total_minutes` 425 · `work_minutes` 105 · `wait_minutes` 320 · `wait_ratio` 75 · `stats.total_label` `7시간 5분` · `pipeline[]` 7그룹의 `work_minutes`/`wait_minutes`/`total_minutes`가 TS-002 수치와 **완전 동일** · `pipeline[].is_peak` true가 TEST-SCENARIO 1건 · 그룹 소요 합 == `total_minutes` |
| RED 기대 실패 | `stats` 키 부재 → `KeyError`. 라우터가 자체 계산하면 L1 값과 어긋나 assert 실패 |
| 도구 | pytest + httpx |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-013: 실시간 파생 응답 — 진행 중 2건 구조 단정 + 완료 1건 값 단정

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `tasks.py` `get_task_detail` ← `task_live_stats` (F-002, R-4) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + httpx TestClient)** |
| 조건 | 실 `tasks/102-*`(현재 `in_progress` 행 0건, 첫 `pending` = `task.user_confirm`) · 실 `tasks/103-*`(row 9 `in_progress`) · 실 `tasks/101-*`(완료). **진행 중 2건은 이동값이므로 값이 아니라 동작을 단정한다** ([MUST] `TASK.md` §제약 조건) |
| 기대 결과 | 102·103: `stats.is_running` true · `current_row_id`가 `in_progress` 행이 있으면 그 행, 없으면 **첫 `pending` 행** · `current_series`가 `current_key`의 `*.user_confirm` 여부와 일치(`wait`/`work`) · `pending` 행 `owner`가 전건 `PM`인데도 `user_confirm` 행이 `wait`로 귀속됨 · `total_minutes`가 `created_at`→현재 시각 기준으로 직전 호출보다 감소하지 않음 / 101: `is_running` false · `total_minutes` 425 고정 · `current_row_id` `null` |
| RED 기대 실패 | `stats.current_*` 키 부재 → `KeyError`. `owner` 기반 귀속 시 102의 `current_series`가 `work`로 나와 assert 실패 |
| 도구 | pytest + httpx |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-014: 산출물 전수 9건 + 4유형 분류

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `tasks.py` `_get_artifact_files` 전수화 + `classify_artifact` (F-002, 집계기준 9 · R-5 선행) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + httpx TestClient)** |
| 조건 | 실 `tasks/101-260824-opd-핸드오프-스키마-계약정합/` — `.md` 9개(`AGENTIC-LOG`·`ANALYSIS`·`DONE`·`GC-CONVENTION-260824`·`PLAN`·`SCENARIO-GATE-1`·`STATE`·`TASK`·`TEST-SCENARIO`). 현행 화이트리스트 6종 교집합으로는 5건 |
| 기대 결과 | `artifacts` 길이 9 · `artifact_items` 유형 분포 pipeline 5(`TASK`·`ANALYSIS`·`PLAN`·`TEST-SCENARIO`·`DONE`) · verification 2(`SCENARIO-GATE-1`·`GC-CONVENTION-260824`) · log 2(`STATE`·`AGENTIC-LOG`) · other 0 · `artifact_items` 길이 == `artifacts` 길이 · 정렬이 pipeline → verification → log → other · `_get_artifact_files` 시그니처 무변경(소비자 호출 코드 변경 0건) |
| RED 기대 실패 | 화이트리스트 폐기 전 `artifacts` 길이 5 → assert 실패. `artifact_items` 키 부재 → `KeyError` |
| 도구 | pytest + httpx |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-015: 결측 태스크 200 + 게이트 「미기록」 구분

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `tasks.py` `get_task_detail` 결측 경로 + `stats.gate_recorded` (F-002, R-12) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + httpx TestClient)** |
| 조건 | 실 `tasks/089-260811-opi-opal/`(**`state.json` 부재** — 프로젝트 내 유일 실사례) · 실 `tasks/091-260813-opd-파이프라인-스펙-중복정리/state.json`(`092` 이전 11개 태스크 공통으로 `gate` 보유 행 0건) |
| 기대 결과 | `089`: HTTP 200(500 아님) · `stats.available` false · `pipeline` 빈 배열 · 예외 로그 0건 / `091`: HTTP 200 · `stats.available` true · `stats.gate_recorded` **false** · `gate_count` 0 — 즉 「게이트 0건」과 「게이트 미기록」이 **서로 다른 두 필드로 구분**된다 / `101`: `gate_recorded` true · `gate_count` 4 |
| RED 기대 실패 | `stats`·`gate_recorded` 키 부재 → `KeyError`. 필수 필드로 추가한 구현에서 `089` 경로가 ValidationError 500 |
| 도구 | pytest + httpx |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-017: BE 기존 테스트 회귀 0 + 스키마 additive 확인

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `dashboard/backend/tests/` 11파일 + 응답 스키마 (P-4 회귀 경계 1·2) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest 전체 실행)** |
| 조건 | 변경 전 기준선: `python3 -m pytest dashboard/backend/tests/` 전건 green. **예외 선언(P-4 4항)**: `artifact_count`·`artifacts[]`의 **값 증가**(101 기준 5→9)는 집계기준 9의 의도된 결과이며 회귀가 아니다 — 기존 테스트에 이 값을 assert하는 케이스가 0건임을 실측 확인(E1 — 스코프 `dashboard/backend/tests/` 11파일, 명령 `grep -rn "artifact_count" dashboard/backend/tests/`) |
| 기대 결과 | 전건 green(exit code 0) · 기존 응답 필드의 제거·타입 변경·의미 변경 0건 · 기존 케이스 수정 0건(테스트 약화·삭제 금지) |
| RED 기대 실패 | 해당 없음 — **회귀 시나리오는 RED-first 대상이 아니다**(항상 GREEN이어야 한다) |
| 도구 | pytest |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-018: 캐시 히트 응답에서도 실시간 값 재계산 (신규 보강 — H-6)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `tasks.py` `get_task_detail` 캐시 경계 — 정적만 캐시, 실시간은 캐시 밖 조립 (F-002, R-4) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + httpx TestClient)** |
| 조건 | 실 `tasks/103-*/state.json`(진행 중). 동일 요청을 TTL 30초 내 2회 연속 호출한다. [MUST] `PLAN.md` §3.2.2: "캐시에는 정적 파생만 담는다. 진행 중 태스크의 실시간 파생은 캐시 히트 이후 `task_live_stats(state, now=datetime.now())`로 계산해 응답에 합성한다" |
| 기대 결과 | 1·2차 응답의 **정적 파생 동일**(`pipeline[]` 그룹 소요·`gate_count`) · 2차 응답의 `stats.current_elapsed_minutes`가 캐시 값 고착이 아니라 재계산 결과(2차 ≥ 1차) · 완료 태스크(101) 2회 호출은 두 값 모두 425 불변 |
| RED 기대 실패 | 실시간 값까지 캐시에 넣은 구현에서 2차 `current_elapsed_minutes`가 1차와 동일 고착 → 재계산 assert 실패 |
| 도구 | pytest + httpx |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-020: 대시보드 모수 — 완료/전체 항등

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `dashboard.py` `get_dashboard` (F-003, R-10) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + httpx TestClient)** |
| 조건 | 실 `tasks/*/state.json` 23파일. 요청: `GET /api/dashboard?project=<ai-framework 절대경로>`. **`completed_tasks`·`total_tasks`는 이동값**(102·103 완료 시 증가)이므로 항등·하한으로 단정한다(§0.5) |
| 기대 결과 | `completed_tasks + (진행 중 수) == total_tasks` · `completed_tasks >= 21` · `total_tasks >= 23` · `workflow_stats[].n` 합 == `completed_tasks` · `workflow_stats[].tasks[]` 원소 총수 == `completed_tasks` |
| RED 기대 실패 | `completed_tasks`·`total_tasks` 키 부재 → `KeyError` |
| 도구 | pytest + httpx |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-021: 워크플로우별 응답 — 코호트 필터 기준 중앙값·대기 비중

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `dashboard.py` ← `stats.py` `workflow_stats` (F-003, R-10) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + httpx TestClient)** |
| 조건 | 실 `/api/dashboard` 응답에서 `STATS-BASELINE.md` §2 동결 코호트 21건 ID로 필터한 뒤 대조. 기대값 원천은 베이스라인 §3 |
| 기대 결과 | `workflow_stats` 3건 · 키가 `skill`(opd·opds·opp) · 코호트 필터 기준 `median_minutes` 799 / 276 / 75 · `wait_ratio` 21 / 4 / 54 · `sample_insufficient`가 opp만 true · `median_label`이 `13시간 19분` / `4시간 36분` / `1시간 15분` · 혼합 집계 필드 0건(집계기준 4 — 혼합 미제공) |
| RED 기대 실패 | `workflow_stats` 키 부재 → `KeyError`. 혼합 집계 구현 시 3건 분리 assert 실패 |
| 도구 | pytest + httpx |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-022: 산출물 규모 항등 (`artifact_total` = 유형별 합계)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `dashboard.py` 산출물 규모 결합 (F-003, R-10 · P-3) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + httpx TestClient)** |
| 조건 | 실 `tasks/*/` `.md` 전수. **이동값** — TASK.md 기재 192, 작성 시점 실측 194, 본 태스크 산출물로 계속 증가한다(§0.5). 따라서 절대값을 고정하지 않는다 |
| 기대 결과 | `artifact_total == sum(artifact_by_type.values())` · `artifact_by_type`이 `pipeline`·`verification`·`log`·`other` 4키 · `artifact_total >= 192` · `other` 버킷이 존재해 미분류 파일이 누락되지 않음 |
| RED 기대 실패 | `artifact_total`·`artifact_by_type` 키 부재 → `KeyError` |
| 도구 | pytest + httpx |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-023: 필드 명명 계약 — `workflow` 키 0건 · 순수 모듈 경계

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | 응답 JSON 전문 + `stats.py` import 경계 (F-003, 집계기준 15) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + httpx TestClient)** |
| 조건 | [MUST] `TASK.md` 집계 기준 15: "응답 키는 `state.json` 스키마 용어(`skill`·`timestamp`·`row_id`)를 쓴다. 사표 필드 `updated_at`·`row`는 deprecated 별칭으로 존치하되 값을 채운다. 「워크플로우」는 UI 표시 라벨로만 남는다." `GET /api/dashboard` + `GET /api/tasks/detail` 두 응답을 재귀 순회 |
| 기대 결과 | 두 응답 JSON의 전 키 집합에 `workflow` **0건** · `skill`·`timestamp`·`row_id` 키 사용 · `row`·`updated_at`은 존재하되 값이 채워짐(빈 문자열·0 폴백 0건) · `stats.py`가 라우터·모델·캐시를 import하지 않아 순환 import 0건 |
| RED 기대 실패 | 확장 전 응답에 `skill`·`row_id` 키가 없어 assert 실패 |
| 도구 | pytest + httpx |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-024: `DashboardSummaryResponse` 기존 8필드 불변

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `models.py` `DashboardSummaryResponse` additive 확장 (F-003, P-4 회귀 경계 1) |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest + httpx TestClient)** |
| 조건 | 변경 전후 `GET /api/dashboard` 응답의 기존 8필드 비교 |
| 기대 결과 | `total_projects`·`running_tasks`·`blockers`·`additional_work`·`status_distribution`·`activity_trend`·`alerts`·`recent_activities` 8필드의 **타입·의미 불변** · 확장은 additive만(필드 제거 0건) · 신규 5필드가 전건 기본값 보유 |
| RED 기대 실패 | 해당 없음 — 회귀 시나리오 |
| 도구 | pytest + httpx |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-051: 베이스라인 §5 ↔ 101 응답·화면 표시값 전건 일치 (완료기준 (1)(2))

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `STATS-BASELINE.md` §5 ↔ 실 응답 ↔ 화면 (F-006, 완료기준 (1)(2)) |
| 계층 | L2 |
| **실행 방식** | **M1 (배포본 콘솔 실응답 대조 — pytest/httpx 또는 스크립트)** |
| 조건 | 배포본 콘솔 기동(`http://127.0.0.1:7823`). 베이스라인 §5 수치는 ANALYSIS §8 E1 독립 재측정분이며 **`stats.py` 출력을 받아 적지 않았다**(P-5 근거 3) |
| 기대 결과 | 101 총 425분 = 작업 105 + 대기 320(75%) · 단계별 7행 TASK 24(0/24)·ANALYSIS 22(17/5)·PLAN 13(11/2)·TEST-SCENARIO 295(10/285)·EXECUTE 18(18/0)·TEST 51(47/4)·CLOSE 2(2/0) · 행 19 · 게이트 4 — 이 값들이 **베이스라인 = API 응답 = 화면 표시** 3자 전건 일치 · 불일치 1건이라도 있으면 FAIL |
| RED 기대 실패 | 해당 없음 — Step 13 대조 검증. RED 증거는 R1~R3 배치에서 이미 확보 |
| 도구 | pytest + httpx / curl |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-052: 코호트 동결 재계산 대조 (완료기준 (3))

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `STATS-BASELINE.md` §2 코호트 ↔ `/api/dashboard` (F-006, 완료기준 (3)) |
| 계층 | L2 |
| **실행 방식** | **M1 (배포본 콘솔 실응답 대조)** |
| 조건 | 배포본 콘솔 기동. 검증 시점에 `102`가 완료됐을 수 있다 — **코호트 목록으로 필터해 비교한다**(P-5). 재측정 방식(그 시점 완료 태스크 전체) 채택 금지 |
| 기대 결과 | §2 ID 목록(opd 7 · opds 10 · opp 4)으로 필터한 재계산이 799 / 276 / 75분과 일치 · `102` 완료 여부와 무관하게 동일 결과 · 대기 비중 21 / 4 / 54 일치 |
| RED 기대 실패 | 해당 없음 — Step 13 대조 검증 |
| 도구 | pytest + httpx / python3 |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-062: FE E2E — 상세 2탭 + A블록 실브라우저 렌더 (M2 의무)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8, H-12 |
| 대상 | `/tasks` 칸반 → 101 상세 Sheet (F-004) |
| 계층 | L2 |
| **실행 방식** | **M2 (E2E 자동화 — cmux 1순위 → playwright 폴백)** |
| 조건 | [MUST] `test-scenario-guide.md` §Step 3-b: "변경 영역에 FE 화면/컴포넌트·인증/인가·외부 API 연동 중 하나라도 포함되면 해당 시나리오에 L2/M2(E2E 자동화)를 의무로 포함한다. M2 누락 = PM Gate FAIL." 배포본 콘솔 기동(`http://127.0.0.1:7823`), 실 프로젝트 데이터 |
| 기대 결과 | 칸반 진입 → 101 카드 클릭 → 상세 Sheet 오픈 · 탭 2개 렌더, 기본 활성 「태스크 대시보드」 · A-1 4타일·A-2 막대 7개·A-3 타임라인·A-4 표 19행이 실브라우저에서 렌더 · 「산출물」 탭 배지 9 · 탭 바가 자체 컨테이너에서만 가로 스크롤(Sheet 본문 가로 밀림 0) · **브라우저 콘솔 에러 0건** |
| 도구 | cmux (`cmux-tool`) 1순위 → playwright 폴백 (`test-tool resolve` integration.e2e) |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

#### TS-063: BE API E2E — Swagger UI 실행 (M2 의무)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `GET /api/tasks/detail` · `GET /api/dashboard` (F-002·F-003) |
| 계층 | L2 |
| **실행 방식** | **M2 (Swagger UI via cmux — `test-tool integration --url <swagger_url>`)** |
| 조건 | [MUST] `test-scenario-guide.md` §Step 3-b: "변경 영역에 **API 엔드포인트**가 포함되면 L2/M2(Swagger via cmux) 시나리오를 의무로 포함한다." Swagger URL: `http://127.0.0.1:7823/docs` |
| 기대 결과 | 두 엔드포인트 200 · 상세 응답 스키마에 `stats`·`artifact_items` 존재하고 `pipeline[].rows[]`에 신규 7필드 존재 · 대시보드 응답에 `workflow_stats`·`completed_tasks`·`total_tasks`·`artifact_total`·`artifact_by_type` 존재 · 결측 태스크(`089-260811-opi-opal`)로 호출해도 200 · 신규 쓰기 엔드포인트 0건(POST/PUT/DELETE 추가 없음) |
| 도구 | cmux browser (`test-tool integration --url http://127.0.0.1:7823/docs`) |
| 실행 명령 | → `TEST.md` §1 실행 기준선(명령 원문·출력) |
| 결과 | → `TEST.md` §4 시나리오 49건 전건 판정표 |
| 상세 | → `TEST.md` §4 해당 시나리오 행 |

---

### L3. 사용자 협업 (수동, `[SUPERVISOR]` 마커) — 2건

> L3는 **목표 달성(채택 관점) 검증**을 담당한다 — 수치 일치는 L1·L2가 판정하고, "이 화면으로 병목과 대기를 실제로 판단할 수 있는가"는 사람만 판정할 수 있다 (`~/.opal/references/harness/scenario-gate.md` §2 ①축).
> **AC 판정 주체가 아니다** — [MUST] `PLAN.md` P-6: "L3 시각 확인(playwright)은 병행하되 AC 판정 주체가 아니다." L3 FAIL은 개선 입력이며, PASS/FAIL 판정은 L1·L2 결과로 한다.

#### TS-060: 병목·대기 구간을 화면만으로 식별 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6, H-7, H-11 |
| 대상 | 태스크 상세 「태스크 대시보드」 탭 A-1~A-4 (F-004) — **태스크 목표 ①「병목 개선」** |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업).** M2 병행 가능 — TS-062가 렌더 사실만 자동 확인한다 |
| 조건 | 배포본 콘솔 기동(`http://127.0.0.1:7823`), 실 프로젝트 데이터. 대상: 완료 태스크 `101` 1건 + 진행 중 태스크 1건 |
| 기대 결과 | (a) 101 상세를 열어 **최장 단계가 TEST-SCENARIO임을 A-1·A-2에서 즉시 식별** (b) 그 단계의 대기 285분 / 작업 10분 분해를 A-2 2색 스택에서 읽을 수 있음 (c) A-3에서 대기가 어느 시각 구간에 발생했는지(17:41→22:26) 확인 가능 (d) A-4에서 (a)~(c)의 원본 행을 대조 가능 (e) 진행 중 태스크에서 총 리드타임 타일에 「진행 중」 배지 표시 (f) 담당 구분이 색 단독이 아니라 라벨을 동반해 색각 의존이 없음 |
| 실행자 | `[SUPERVISOR]` — 캡틴 수동 확인 필요 |
| 결과 | → `TEST.md` §6 L3 요청 양식 (캡틴 확인 대기) |
| 상세 | → `TEST.md` §6 L3 요청 양식 |

**PM 표준 요청 양식 (TS-060)**

```
[SUPERVISOR 요청 — TS-060 병목 식별 시각 확인]
확인 대상: http://127.0.0.1:7823 → 태스크 칸반 → 101 카드 → 「태스크 대시보드」 탭
확인 절차:
  1) 101 상세를 열고 A-1 4타일에서 「최장 단계」를 읽는다
  2) A-2 스택 막대에서 그 단계의 대기/작업 분할을 확인한다
  3) A-3 타임라인에서 대기가 발생한 시각 구간을 확인한다
  4) A-4 표에서 위 3개가 가리키는 원본 행을 대조한다
  5) 진행 중 태스크(102 또는 103) 상세를 열어 「진행 중」 배지를 확인한다
판정 기준: 위 (a)~(f) 6항 전건 충족 시 PASS
회신 형식: PASS / FAIL + 미충족 항목 번호 + 관측 내용 1~2줄
```

#### TS-061: 워크플로우별 대기 비중 대조로 캡틴 대기 구간 판단 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | 대시보드 B-1~B-4 (F-005) — **태스크 목표 ②「캡틴 대기 축소」** |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업).** M2 병행 가능 |
| 조건 | 배포본 콘솔 기동, 실 프로젝트 데이터. B-4 필터로 opd → opds → opp 전환 |
| 기대 결과 | (a) 세 워크플로우의 **대기 비중 차이(21% / 4% / 54%)를 화면 대조만으로 인지** (b) opp 선택 시 「표본 부족」 배지가 보여 n=4 해석 주의가 전달됨 (c) B-2에서 워크플로우별 병목 단계(EXECUTE 계열)를 식별 가능 (d) B-3에서 태스크별 리드타임 편차와 최장/최단을 확인 가능 (e) **혼합 집계 수치가 화면 어디에도 없음**(집계기준 4) (f) 필터 전환이 즉시 반영되고 로딩 재요청이 발생하지 않음 |
| 실행자 | `[SUPERVISOR]` — 캡틴 수동 확인 필요 |
| 결과 | → `TEST.md` §6 L3 요청 양식 (캡틴 확인 대기) |
| 상세 | → `TEST.md` §6 L3 요청 양식 |

**PM 표준 요청 양식 (TS-061)**

```
[SUPERVISOR 요청 — TS-061 워크플로우 대조 시각 확인]
확인 대상: http://127.0.0.1:7823 → 대시보드 → 기존 5블록 아래 B-1~B-4
확인 절차:
  1) B-4에서 opd를 선택하고 B-1의 대기 비중을 읽는다
  2) opds → opp로 전환하며 같은 값을 읽어 비교한다
  3) opp 선택 상태에서 「표본 부족」 배지를 확인한다
  4) B-2 단계 막대에서 병목 단계를, B-3에서 태스크별 편차를 확인한다
  5) 화면 전체에서 혼합 집계(워크플로우 구분 없는 중앙값) 표기를 찾아본다 — 있으면 FAIL
판정 기준: 위 (a)~(f) 6항 전건 충족 시 PASS
회신 형식: PASS / FAIL + 미충족 항목 번호 + 관측 내용 1~2줄
```

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

### 4.1 요구사항 AC 매핑 (R-1 ~ R-14)

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 AC (집계 소유·중복 0) | H-5 | L1 · L2 | TS-008, TS-012, TS-023 | `dashboard/backend/tests/test_stats.py:test_stats_module_is_pure [T103/L1-R1]` · `dashboard/backend/tests/test_routers.py:test_detail_stats_matches_core [T103/L2-R1]` | 라우터·FE 중복 계산 0건 |
| R-2 AC (5키·게이트 4·객체) | H-3 | L2 | TS-010 | `test_routers.py:test_pipeline_row_extended_keys [T103/L2-R2]` | `gate` 불리언 아님 |
| R-2 AC(추가) (사표 필드 교정) | H-2 | L2 | TS-011 | `test_routers.py:test_pipeline_row_legacy_aliases_filled [T103/L2-R2b]` | `row` 1~19 연속 · `updated_at` 빈 문자열 0 |
| R-3 AC (425 = 105 + 320 · 단계별 7행) | H-2 | L1 · L2 | TS-001, TS-002, TS-012 | `test_stats.py:test_task_total_series_split [T103/L1-R3]` · `test_stats.py:test_stage_breakdown [T103/L1-R3b]` · `test_routers.py:test_detail_stats_values [T103/L2-R3]` | 기대값 원천 = 베이스라인 §5 |
| R-4 AC (현재 행·key 귀속·완료 고정) | H-6 | L1 · L2 | TS-005, TS-006, TS-013, TS-018 | `test_stats.py:test_live_current_row_and_series [T103/L1-R4]` · `test_stats.py:test_completed_ignores_now [T103/L1-R4b]` · `test_routers.py:test_detail_live_stats [T103/L2-R4]` · `test_routers.py:test_live_recomputed_on_cache_hit [T103/L2-R4c]` | 진행 중은 동작 단정 |
| R-5 AC (탭 2·기본 활성·배지 9·스크롤) | H-12 | L1 · L2 | TS-030, TS-031, TS-039, TS-062 | `TasksPage.stats.test.tsx:두 탭 렌더와 기본 활성 [T103/L1-R5]` · `TasksPage.stats.test.tsx:탭별 자체 스크롤 [T103/L1-R5b]` · `TasksPage.stats.test.tsx:탭 바 가로 스크롤 격리 [T103/L1-R5c]` | 배지 9는 TS-014 선행 |
| R-5 선행 조건 (전수 9) | H-4 | L2 | TS-014 | `test_routers.py:test_artifacts_full_scan_and_types [T103/L2-R5pre]` | FE 단독 달성 불가 |
| R-6 AC (A-1 4타일 · 진행 중 배지) | H-11 | L1 · L3 | TS-032, TS-009, TS-060 | `TasksPage.stats.test.tsx:A-1 4타일 문자열 [T103/L1-R6]` · `test_stats.py:test_format_duration_rules [T103/L1-R6b]` | 목업 A-1 구성 폐기 |
| R-7 AC (A-2 7막대·최장·2색) | H-11 | L1 | TS-033 | `TasksPage.stats.test.tsx:A-2 스택 막대 [T103/L1-R7]` | 단일색 채움 폐기 |
| R-8 AC (A-3 오름차순·공백·라벨) | H-2 | L1 | TS-034 | `TasksPage.stats.test.tsx:A-3 타임라인 [T103/L1-R8]` | 색 단독 금지 |
| R-9 AC (A-4 19행·게이트 4·2열·스크롤) | H-11, H-12 | L1 | TS-035 | `TasksPage.stats.test.tsx:A-4 상세 표 [T103/L1-R9]` | 소요 2열 분리 |
| R-10 AC (완료 21/전체 23 · 중앙값 · 비중 · 산출물) | H-10, H-4 | L1 · L2 | TS-007, TS-020, TS-021, TS-022, TS-043 | `test_stats.py:test_workflow_stats_cohort [T103/L1-R10]` · `test_routers.py:test_dashboard_counts_identity [T103/L2-R10]` · `test_routers.py:test_dashboard_workflow_stats [T103/L2-R10b]` · `test_routers.py:test_artifact_total_identity [T103/L2-R10c]` | 모수·산출물은 이동값 규약 적용 |
| R-11 AC (필터·표본 부족·`n=`) | H-11, H-10 | L1 | TS-040, TS-041, TS-042, TS-047 | `DashboardPage.stats.test.tsx:B-4 필터 연동 [T103/L1-R11]` · `:표본 부족 배지 [T103/L1-R11b]` · `:B-2 모수 표기 [T103/L1-R11c]` · `:목업 폐기 잔존 0 [T103/L1-R11d]` | API 재호출 0건 |
| R-12 AC (결측 3경로 · 「미기록」) | H-2, H-3 | L1 · L2 | TS-004, TS-015, TS-036, TS-044 | `test_stats.py:test_missing_tolerance [T103/L1-R12]` · `test_routers.py:test_missing_state_returns_200 [T103/L2-R12]` · `TasksPage.stats.test.tsx:결측 축소 표시 [T103/L1-R12b]` · `DashboardPage.stats.test.tsx:결측 축소 표시 [T103/L1-R12c]` | 「0」과 「미기록」 구분 |
| R-12 AC(추가) (음수 clamp) | H-1 | L1 | TS-003 | `test_stats.py:test_negative_duration_clamped [T103/L1-R12d]` | `086` 실측 −1분 |
| R-12 AC(추가) (`source_path` mtime 작동) | H-9 | L1 | TS-016 | `dashboard/backend/tests/test_cache.py:test_mtime_invalidation_wallclock [T103/L1-R12e]` | P-8 시계 교정 |
| R-13 AC (hex 0건) | H-8 | L1 | TS-037, TS-045 | `TasksPage.stats.test.tsx:hex 리터럴 0건 [T103/L1-R13]` · `DashboardPage.stats.test.tsx:hex 리터럴 0건 [T103/L1-R13b]` | 토큰 경유 |
| R-14 AC (베이스라인 기재 · 런타임 0) | H-10 | L1 | TS-050, TS-053 | 산출물 검사 스크립트 `[T103/L1-R14]` · `[T103/L1-R14b]` | 「91」 표기 0건 |

### 4.2 완료기준 · PLAN 확정 매핑

| 완료기준 / 확정 | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|----------------|---------|---------|---------|-----------------|------|
| (1) 베이스라인 ↔ 화면 표시값 전건 일치 | H-10 | L2 | TS-051 | 대조 스크립트 `[T103/L2-CC1]` | 자기확인 금지 |
| (2) 2탭 + A-1~A-4 + 101 425/105/320 | H-11, H-12 | L1 · L2 · L3 | TS-030, TS-032, TS-051, TS-060 | 상동 + FE 케이스 | — |
| (3) B-1~B-4 워크플로우별 799/276/75 | H-10, H-11 | L2 · L3 | TS-052, TS-021, TS-061 | 대조 스크립트 `[T103/L2-CC3]` | 코호트 동결 필터 |
| (4) 진행 중 태스크 현재 행 · key 귀속 | H-6 | L1 · L2 | TS-005, TS-013 | `[T103/L1-R4]` · `[T103/L2-R4]` | 값 아닌 동작 단정 |
| (5) `state.json` 없는 태스크 오류 없이 열림 | H-3 | L1 · L2 | TS-015, TS-036 | `[T103/L2-R12]` · `[T103/L1-R12b]` | `FX-089` 실사례 |
| (6) 신규 코드 hex 0건 | H-8 | L1 | TS-037, TS-045 | `[T103/L1-R13]` · `[T103/L1-R13b]` | — |
| (7) 기존 기능 회귀 0 (P-4 4항) | H-4, H-7, H-3 | L1 · L2 | TS-017, TS-024, TS-038, TS-046 | `pytest` 전체 · `[T103/L2-REG2]`(TS-017 전용, Step 8 신설) · `[T103/L2-REG1]` · `[T103/L1-REG3]` · `[T103/L1-REG3b]` | `artifact_count` 값 증가는 **명시적 예외** |
| 집계기준 15 (필드 명명) | H-5 | L2 | TS-023 | `test_routers.py:test_no_workflow_key [T103/L2-N15]` | `workflow` 키 0건 |
| P-7 (표시 문자열 BE 소유) | H-2 | L1 | TS-009, TS-032 | `[T103/L1-R6b]` | FE 포맷 함수 0건 |
| API 엔드포인트 M2 의무 | H-3 | L2 | TS-063 | cmux Swagger `[T103/L2-M2api]` | `test-tool integration --url` |
| FE 화면 M2 의무 | H-8, H-12 | L2 | TS-062 | cmux → playwright `[T103/L2-M2fe]` | 콘솔 에러 0건 |
| 목표 ① 병목 개선 (사용자 계층) | H-6, H-7, H-11 | L3 | TS-060 | `[SUPERVISOR]` | 목표달성 시나리오 |
| 목표 ② 캡틴 대기 축소 (사용자 계층) | H-11 | L3 | TS-061 | `[SUPERVISOR]` | 목표달성 시나리오 |

### 4.3 기능(F) 커버 확인 — `scenario-gate.md` §2 ③축

| F-ID | 시나리오 | 건수 |
|------|---------|------|
| F-001 집계 코어 `stats.py` | TS-001 ~ TS-009 | 9 |
| F-002 태스크 상세 API 확장 | TS-010 ~ TS-018 (TS-016 포함) | 9 |
| F-003 대시보드 집계 API 확장 | TS-020 ~ TS-024, TS-063 | 6 |
| F-004 상세 화면 2탭 + A-1~A-4 | TS-030 ~ TS-039, TS-060, TS-062 | 12 |
| F-005 대시보드 B-1~B-4 | TS-040 ~ TS-047, TS-061 | 9 |
| F-006 베이스라인 · 대조 검증 | TS-050 ~ TS-053 | 4 |

미커버 F **0건** · 미커버 R **0건** · 미커버 H **0건**.

### 4.4 목표-커버 게이트 정규화 입력 요약 (`scenario-gate.md` §3)

호출 스킬(`op-scenario-gate`)이 변환할 판단축 플래그를 미리 확정해 둔다.

| 축 | 해당 시나리오 |
|----|-------------|
| `is_goal_scenario` (①) | TS-051, TS-052, TS-060, TS-061 |
| `is_adoption_scenario` (⑤ — 교체형 4건: 화이트리스트→전수 · 혼합→워크플로우별 · 목업→재작성본 · 사표 필드→원천 용어) | TS-011, TS-014, TS-023, TS-042, TS-047 |
| `is_boundary_scenario` (⑥) | TS-003(음수), TS-004(결측 3경로), TS-006(완료 경계), TS-007(n<5 · 짝수 n 중앙값 275.5 · 비중 3.68% 반올림), TS-009(0·`None` 경계), TS-015(파일 부재 · 게이트 미기록), TS-016(mtime 경계), TS-036·TS-044(빈 응답), TS-039(폭 초과), TS-041(표본 부족) |

> 게이트는 **PLAN 확정 + 보강 완료 후 1회** 호출한다 ([MUST] `scenario-gate.md` §4). 본 문서는 PLAN 확정본(1,379줄) 기반이며 선작성 트랙을 쓰지 않았으므로 보강 대기 마커는 0건이다.

---

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 (BE) | ruff | → `TEST.md` §8 | → `TEST.md` §8 |
| 2 | 린트 (FE) | eslint | → `TEST.md` §8 | → `TEST.md` §8 |
| 3 | 타입 체크 (BE) | mypy | → `TEST.md` §8 | → `TEST.md` §8 |
| 4 | 타입 체크 (FE) | tsc (`npm run build` = `tsc -b && vite build`) | → `TEST.md` §8 | → `TEST.md` §8 |
| 5 | `@header` 갱신 | 수동/`code-scan` | → `TEST.md` §8 | 신규·수정 코드 파일 전건 인라인 주석 (`.opal/code-scan.json` `headerSource: "inline"`) |
| 6 | 사변적 추가 0건 | diff 검토 | → `TEST.md` §8 | `PIE_COLORS`·`tasks.py` 제목 폴백·`TTL_SECONDS`는 건드리지 않는다 |
| 7 | RED 테스트 불변성 | diff 검토 | → `TEST.md` §8 | [MUST] `red-first.md` §3 — GREEN 루핑 중 RED 테스트 파일 수정 0건 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | → `TEST.md` §8 | 신규 코드에 토큰·시크릿 0건 |
| 2 | `.gitignore` 확인 | → `TEST.md` §8 | `.env`·인증 파일 포함 여부 |
| 3 | 신규 쓰기 엔드포인트 0건 | → `TEST.md` §8 | GET 경로만 변경 — 읽기 전용 원칙의 예외를 늘리지 않는다 |
| 4 | 경로 조작 방어 | → `TEST.md` §8 | `artifacts` 전수화로 노출 파일이 늘어난다 — `GET /api/tasks/artifact`의 `name`이 태스크 폴더 밖(`../`)을 읽지 않는지 확인 |
| 5 | XSS 경로 | → `TEST.md` §8 | 응답에 `note` 원문이 실린다 — 마크다운 렌더 경로가 기존 `MarkdownView` 수준 방어를 유지하는지 확인 |

## 7. 판정

**종합 판정과 근거는 `TEST.md` §0 판정 요약이 소유한다** — 45 PASS · 0 FAIL · 2 BLOCKED(M2 실연동) · 2 보류(L3), Partial Fail.

### 판정 규칙

- **AC 판정 주체는 L1·L2 (M1/M2)** 다. L3(M3)는 목표 달성 관점의 개선 입력이며 단독으로 PASS/FAIL을 뒤집지 않는다 ([MUST] `PLAN.md` P-6).
- RED-first 강제 트랙 21건은 **RED 증거(exit code ≠ 0) 기록이 없으면 GREEN을 인정하지 않는다** ([MUST] `red-first.md` §1).
- 실연동 검증이 불가하면 통과 처리하지 말고 **BLOCKED로 표면화**한다.

### PM Gate 체크 (7대 강제 룰)

- [x] 금지 토큰(가짜 객체 대체 키워드) 시나리오 본문 부재 — 전 픽스처가 실 `tasks/*/state.json` 또는 그 동결 복사본/파생본 (§0.3)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐 — 17개 픽스처, 빈 칸 0
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐 — 49행 전건
- [x] 가설↔시나리오 매핑(§4) 완전 — 미매핑 시나리오 0건, 미커버 가설 0건
- [x] L1/L2/L3 계층 명시 — L1 30 · L2 17 · L3 2 = 49건 전건
- [x] L3 `[SUPERVISOR]` 마커 존재 + PM 요청 양식 첨부 — TS-060·TS-061 각 1건
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 1:N 매핑 완전 — H-1~H-12 전건
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시 — M1 45 · M2 2 · M3 2
- [x] **FE 변경 시 M2 시나리오 포함** — TS-062(cmux→playwright) 1건 + API M2 TS-063 1건
- [x] **목표 커버** — R-1~R-14 전건이 §4.1에 커버되고, 사용자/운영 계층 목표달성 시나리오가 §3에 4건(TS-051·TS-052·TS-060·TS-061) 존재

### 계층·방식 분포

| 구분 | L1 | L2 | L3 | 합계 |
|------|----|----|----|------|
| M1 (테스트 도구) | 30 | 15 | — | 45 |
| M2 (E2E 자동화) | — | 2 | — | 2 |
| M3 (사용자 협업) | — | — | 2 | 2 |
| **합계** | **30** | **17** | **2** | **49** |

### RED-first 대상 (21건)

`TS-001` `TS-002` `TS-003` `TS-004` `TS-005` `TS-006` `TS-007` `TS-008` `TS-009` `TS-010` `TS-011` `TS-012` `TS-013` `TS-014` `TS-015` `TS-016` `TS-018` `TS-020` `TS-021` `TS-022` `TS-023`

RED 대상 제외: 회귀 시나리오 2건(TS-017·TS-024) · FE 구현-후-검증 트랙 18건(TS-030~047) · 산출물/대조 4건(TS-050~053) · M2/M3 4건(TS-060~063).

### PM 보정 기록 (PLAN 대비)

| # | 보정 | 근거 |
|---|------|------|
| 1 | 시나리오 4계열 증분 (TS-018 · TS-039 · TS-047 · TS-060~063) | H-6·H-11·H-12 가설 커버 누락 + L3 부재 + M2 의무 미충족 |
| 2 | `dashboard/backend/tests/test_cache.py` 신설 명시 | [MUST] `test-scenario-guide.md` §Step 4-b 모듈 미러링 — PLAN Step 8 파일 목록에 `cache.py` 미러 누락 |
| 3 | RED 실행 배치 R1~R3을 구현 Step **앞**으로 분해 (§3.0) | [MUST] `red-first.md` §1 — PLAN Step 8(구현 후 일괄)은 RED-first 강제 트랙과 양립 불가 |
| 4 | R-4 AC의 "103 = `task.user_confirm`" 값 단정을 `FX-102`로 이관 | 이동값 — 현재 103의 현재 행은 `test_scenario.test_scenario_md`. [MUST] `TASK.md` §제약 「진행 중 태스크의 AC는 값이 아니라 동작으로 기술한다」 |
| 5 | `completed_tasks`/`total_tasks`/`artifact_total` 절대값 단정을 항등·하한으로 전환 | 이동값 — 작성 시점 `.md` 실측 194(TASK.md 기재 192) |
| 6 | opds 중앙값 275.5 → 276 반올림, 대기 비중 3.68% → 4 반올림을 경계 단정으로 명시 | PLAN이 반올림 규칙을 명시하지 않아 구현 분기 여지가 있다 (TS-007) |


---

## 부록 A — 판정 소유권 (PM 정정 2026-08-26 11:05)

본 문서는 **시나리오 정의**를 소유하고, **실행 결과와 판정은 `TEST.md`가 소유한다.**

작성 시점 템플릿이 시나리오마다 「실행 명령」·「결과」·「상세」 칸을 두었으나, TEST 단계가 판정을 `TEST.md`에 별도로 기록하면서 그 칸들이 **158건 빈 슬롯으로 남았다**. 같은 결과를 두 문서가 나눠 가지면 재실행마다 양쪽을 갱신해야 하고, 한쪽만 갱신되면 조용히 갈린다. 그래서 슬롯을 지우고 포인터로 바꿨다.

| 칸 | 소유 문서 |
|----|----------|
| 실행 명령 | `TEST.md` §1 실행 기준선 |
| 결과 · 상세 | `TEST.md` §4 시나리오 49건 전건 판정표 |
| L3 결과 | `TEST.md` §6 L3 요청 양식 |
| 코드 품질 | `TEST.md` §8 |
| 종합 판정 | `TEST.md` §0 판정 요약 |

**이 누락은 PM Gate에서 놓쳤다** — 눈으로 훑어서는 158건을 셀 수 없다. 기계 검사(미완 슬롯 0건)를 CLOSE 게이트에 두어야 재발하지 않는다.

---

## 부록 B — 3계열 확장 시나리오 (캡틴 지시 2026-08-25 18:30, PM 등재 21:22)

R-15~R-18로 범위가 확대되며 신설된 시나리오다. 본문 TS-001~TS-063은 2계열 시점 산출물이며 축퇴 규칙(집계 기준 16-a)에 따라 **전건 유효**하다 — 워커 미기록 태스크에서 `PM == 기존 작업`, `캡틴 == 기존 대기`이기 때문이다.

| ID | 계층 | 방식 | 대상 | 기대 결과 |
|----|------|------|------|----------|
| TS-101~105 | L1 | M1 (pytest) | `stats.py` 3계열 | 축퇴 규칙 · 「0」과 「미측정」 구분 · 상한 clamp · 항등 |
| TS-106~108 | L2 | M1 (pytest) | 라우터 3계열 결합 | 응답 4층에 3계열 + `worker_measured` 실림 |
| TS-106~109 | L1 | M1 (vitest) | A-1 4타일 · A-2 3색 스택 | `103` 4구획 항등(483 = 23+146+130+184) · `101` 시각 회귀 0(`a2-seg-work` 폭 배열 동일) |
| TS-110~111 | L1 | M1 (vitest) | B-1 구성 스트립 · B-2 3색 | 워크플로우 3계열 반영 |

**채번 충돌 주의** — BE(pytest)와 FE(vitest)가 `TS-106~108`을 각각 채번해 겹친다. 실행 도구가 달라 판정에는 영향이 없으나, 후속 태스크가 이 표를 인용할 때는 도구를 함께 적어야 한다.

**핵심 실증값**

| 태스크 | 총 | PM | 워커 | 캡틴 | `worker_measured` |
|---|---|---|---|---|---|
| `101` (미기록) | 425 | **105** | 0 | **320** | false |
| `103` (기록) | 299 (정적) | 23 | 146 | 130 | true |

`101`의 PM 105 · 캡틴 320이 기존 2계열 `작업 105` · `대기 320`과 항등이다. 워크플로우 중앙값 799/276/75와 대기 비중 21/4/54도 불변이다.
