# TEST — OPAL Console 태스크 진행 통계 (동적 검증)

> 실행일: 2026-08-25 18:05~18:08 | 실행 주체: `opal-test-agent` (mode: BE + FE)
> 입력: `TEST-SCENARIO.md`(49건, TS-042 PM 재정의 18:05 반영) · `STATS-BASELINE.md`(§7 스코프 정정 포함) · `TASK.md` §완료기준 · `RED-EVIDENCE.md`
> 역할: **검증자**. 구현·테스트 코드 수정 0건. 실패는 고치지 않고 판정으로 남긴다.

---

## 0. 판정 요약

| 구분 | 건수 |
|------|------|
| **PASS** | **45** (L1 30 · L2 M1 15) |
| **FAIL** | **0** |
| **BLOCKED** (미집행 — 환경 미비) | **2** (TS-062 · TS-063, 둘 다 M2) |
| **보류** (L3 `[SUPERVISOR]` — PM 위임) | **2** (TS-060 · TS-061) |
| 계 | 49 |

**판정: Partial Fail** — 실행한 45건에 FAIL 0건이고 완료기준 7항이 전건 PASS이나, **M2(실연동 E2E) 2건을 집행하지 못했다**. `TEST-SCENARIO.md` §7 판정 규칙 「실연동 검증이 불가하면 통과 처리하지 말고 BLOCKED로 표면화한다」에 따라 **All Pass를 선언하지 않는다**. 품질 결함이 아니라 **검증 커버리지 미달**이며, 해소 조건은 §5에 기재했다.

---

## 1. 실행 기준선 — 명령 원문과 출력

| # | 명령 | 결과 |
|---|------|------|
| 1 | `~/.opal/.venv/bin/python -m pytest dashboard/backend/tests/ -q` | `297 passed, 1 skipped in 16.36s` (exit 0) |
| 2 | `~/.opal/.venv/bin/python -m pytest dashboard/backend/tests/test_stats.py dashboard/backend/tests/test_cache.py -v` | `25 passed in 0.08s` (exit 0) |
| 3 | `cd dashboard/frontend && npx vitest run --reporter=verbose` | `Test Files 9 passed (9) / Tests 104 passed (104)` |
| 4 | `cd dashboard/frontend && npm run build` | `✓ built in 749ms` |
| 5 | `~/.opal/.venv/bin/python <scratchpad>/verify.py` (in-process `TestClient`, 프로젝트 소스) | 전 엔드포인트 HTTP 200 — §3 대조표 |
| 6 | `/opt/homebrew/bin/ruff check dashboard/backend/{stats,cache,models}.py dashboard/backend/routers/{tasks,dashboard}.py` | `All checks passed!` |
| 7 | `npx eslint` (신규·수정 FE 4파일) | 위반 0건 |
| 8 | `npx tsc --noEmit` | `TS5101`(tsconfig `baseUrl` deprecated) 1건 — **착수 전 기존 결함, 신규 코드 무관** |

**서버 기동 방식** — 포트 7823은 낡은 배포 사본이 점유 중이므로 사용하지 않았다. `fastapi.testclient.TestClient`로 **프로젝트 소스를 in-process 기동**해 실응답을 얻었다. 7823 프로세스는 건드리지 않았다.

---

## 2. 승계 판정 3건 (재수행 불요 — 기록만)

| 항목 | 판정 | 주체 · 근거 |
|------|------|------------|
| 목표-커버 게이트 | **PASS** | `opal-evaluator-agent` / `SCENARIO-GATE-1.md` — 결정론 exit 0 · 루브릭 goal 2 / adoption 2 / boundary 2, 평균 2.0 |
| 완료기준 (1) 베이스라인 대조 | **PASS** | EXECUTE Step 13 검증자 — 10항목 전건 일치, 값 오류 0건 |
| RED-first 규약 | **충족** | `RED-EVIDENCE.md` — 21건 RED(exit≠0) → GREEN, 작성자≠구현자 |

RED 증거 재확인: R1 `2 failed, 3 passed` / R2 `20 failed` (`ModuleNotFoundError: dashboard.backend.stats`) / R3 `16 failed, 55 passed`. 오타·문법 기인 실패 0건. RED 대상 21건이 현재 전건 GREEN임을 §1 명령 1·2로 확인했다.

---

## 3. 베이스라인 ↔ 실응답 독립 대조 (자기확인 금지 원천 준수)

기대값은 **`STATS-BASELINE.md`에서만** 가져왔다. 구현 출력을 기대값으로 되쓰지 않았다.

### 3.1 태스크 `101` — 베이스라인 §3

| 항목 | 베이스라인 §3 | 실응답 (in-process) | 판정 |
|------|--------------|--------------------|------|
| 총 리드타임 | 425분 / `7시간 5분` | `total_minutes=425` · `total_label="7시간 5분"` | 일치 |
| 작업 / 대기 | 105 / 320 | `work_minutes=105` · `wait_minutes=320` | 일치 |
| 대기 비중 | 75% | `wait_ratio=75` | 일치 |
| 최장 단계 | TEST-SCENARIO | `peak_stage="TEST-SCENARIO"` · `is_peak` true 1건 | 일치 |
| 단계별 7행 | 24(0/24)·22(17/5)·13(11/2)·295(10/285)·18(18/0)·51(47/4)·2(2/0) | `[('TASK',24,0,24),('ANALYSIS',22,17,5),('PLAN',13,11,2),('TEST-SCENARIO',295,10,285),('EXECUTE',18,18,0),('TEST',51,47,4),('CLOSE',2,2,0)]` | **전건 일치** |
| 행 수 / 게이트 | 19 / 4 | `rows=19` · `gate != null` 4건 | 일치 |
| `.md` 산출물 | 9 | `artifacts=9` · 유형 `pipeline 5 · verification 2 · log 2` | 일치 |

사표 필드 교정 실측: `row` 값이 `[1..19]` 연속 · `updated_at` 빈 문자열 **0건**.

### 3.2 워크플로우 — 베이스라인 §4, 동결 코호트 21건 필터

| skill | 베이스라인 중앙값 | 응답 `median_minutes` | **코호트 ID 필터 재계산** | 대기 비중 | 표본 부족 | 판정 |
|-------|-----------------|---------------------|------------------------|----------|----------|------|
| opd | 799 (`13시간 19분`) | 799 / `13시간 19분` | n=7 · **799** · ID 집합 일치 | 21 | false | 일치 |
| opds | 276 (원값 275.5) | 276 / `4시간 36분` | n=10 · **275.5** (반올림 전 원값) | 4 | false | 일치 |
| opp | 75 (`1시간 15분`) | 75 / `1시간 15분` | n=4 · **75.0** | 54 | **true** | 일치 |

`102` 완료 여부와 무관하게 §2 ID 목록으로 필터한 재계산이 799/276/75와 일치했다 (완료기준 (3) 충족 방식).

### 3.3 전역 — 이동값 규약 적용 (하한·항등 단정)

| 항목 | 실측 | 단정 방식 | 판정 |
|------|------|----------|------|
| 완료 / 전체 | 21 / 23 | `completed + 진행중 == total` 항등 · `completed >= 21` 하한 | 성립 |
| `artifact_total` | **194** | `artifact_total == sum(artifact_by_type)` 항등 (`93+51+43+7 = 194`) · `>= 192` 하한 | 성립 |
| `artifact_by_type` | `pipeline 93 · verification 51 · log 43 · other 7` | 4키 존재 · `other` 버킷으로 미분류 누락 0 | 성립 |

**194는 베이스라인 §7이 확정한 「`state.json` 보유 23태스크」 스코프값과 일치한다.** 절대값 불일치를 실패로 판정하지 않았다 (§6.2 이동값 규약).

### 3.4 결측 내성 실증 — 지시 (d)

| 태스크 | HTTP | `available` | `is_running` | 현재 행 | `gate_recorded` / `gate_count` | 판정 |
|--------|------|-------------|--------------|---------|-------------------------------|------|
| `089` (`state.json` 부재) | **200** | false | false | — | false / 0 | **오류 없이 동작** · `pipeline` 빈 배열 · 예외 0건 |
| `102` (진행 중, `in_progress` 행 0건) | 200 | true | true | `row_id=2` · `task.user_confirm` · **`current_series=wait`** | true / 4 | **첫 `pending` 귀속 + key 패턴 판정** (`owner=PM` 기본값에 속지 않음) |
| `103` (진행 중, `in_progress` 행 보유) | 200 | true | true | `row_id=13` · `test.run_tests` · `current_series=work` | true / 4 | **`in_progress` 행 우선** 불변식 성립 |
| `091` (게이트 미기록 레거시) | 200 | true | false | — | **false / 0** | 「게이트 0건」과 「미기록」이 두 필드로 구분됨 |

세 결측·진행 경로 전건에서 **500·예외 0건**. `103`의 현재 행이 실행 시점에 `test.run_tests`로 이동해 있으나, 시나리오 규약대로 값이 아닌 **불변식**으로 단정해 판정에 영향이 없다.

---

## 4. 시나리오 49건 전건 판정표

### 4.1 L1 — 기능 단위 30건 (전건 M1)

| ID | 계층 | 방식 | 결과 | 근거 (대응 케이스 · 실측) |
|----|------|------|------|--------------------------|
| TS-001 | L1 | M1 pytest | **PASS** | `test_stats.py::test_ts001_task_static_total_two_series` · 425=105+320, 비중 75 |
| TS-002 | L1 | M1 pytest | **PASS** | `test_ts002_task_static_stage_breakdown` · 7그룹 베이스라인 §3.2 전건 일치 |
| TS-003 | L1 | M1 pytest | **PASS** | `test_ts003_backward_timestamp_clamped_and_monotonic_anchor` · `086` row5 −1분 → 0 clamp, 총합 450 항등 |
| TS-004 | L1 | M1 pytest | **PASS** | `test_ts004_empty_rows` · `_missing_created_at` · `_unparsable_timestamp_skips_without_advancing_anchor` 3케이스 |
| TS-005 | L1 | M1 pytest | **PASS** | `test_ts005_live_current_row_and_key_pattern_series` · `now` 고정 주입, `current_series=wait` |
| TS-006 | L1 | M1 pytest | **PASS** | `test_ts006_completed_task_ignores_now` · `now` 2회 변경에도 425 불변 |
| TS-007 | L1 | M1 pytest | **PASS** | `test_ts007_workflow_stats_frozen_cohort` · 799/276/75 · 21/4/54 · opp만 `sample_insufficient` |
| TS-008 | L1 | M1 pytest | **PASS** | `test_ts008_stats_module_import_boundary` · import 집합이 표준 라이브러리로 한정 |
| TS-009 | L1 | M1 pytest | **PASS** | `test_ts009_format_duration_rules` 파라미터 10건 전개 전건 통과 (`None→—` · `0→0분` · `120→2시간` 경계 포함) |
| TS-016 | L1 | M1 pytest | **PASS** | `test_cache.py` 5케이스 · 미변경 히트 / `os.utime` 후 미스 / `source_path=None` TTL 축 / 공개 시그니처·`TTL_SECONDS` 불변 |
| TS-030 | L1 | M1 vitest | **PASS** | `[T103/L1-R5]` 두 탭 렌더와 기본 활성 · 배지 9 |
| TS-031 | L1 | M1 vitest | **PASS** | `[T103/L1-R5b]` 탭별 자체 스크롤 |
| TS-032 | L1 | M1 vitest | **PASS** | `[T103/L1-R6]` 4타일 문자열 + **목업 라벨(「완료 단계」·「게이트 · 블로커」) 부재 단정 확인** |
| TS-033 | L1 | M1 vitest | **PASS** | `[T103/L1-R7]` 막대 7개 · 최장 강조 · 2색 분할 |
| TS-034 | L1 | M1 vitest | **PASS** | `[T103/L1-R8]` 오름차순 19항목 · 최대 공백 · 라벨 동반 |
| TS-035 | L1 | M1 vitest | **PASS** | `[T103/L1-R9]` 19행 · `GATE` 4건 · 2열 분리 · 스크롤 격리 |
| TS-036 | L1 | M1 vitest | **PASS** | `[T103/L1-R12b]` 결측 축소 표시 + `[T103/L1-R12b2]` 게이트 「미기록」 표기 |
| TS-037 | L1 | M1 정적검사 | **PASS** | `[T103/L1-R13]` + 검증자 재실행 `grep -cE '#[0-9a-fA-F]{3,8}' TasksPage.tsx` → **0** |
| TS-038 | L1 | M1 vitest | **PASS** | `[T103/L1-REG3]` 칸반 읽기 전용 계약 불변 |
| TS-039 | L1 | M1 vitest | **PASS** | `[T103/L1-R5c]` 탭 바 가로 스크롤 격리 |
| TS-040 | L1 | M1 vitest | **PASS** | `[T103/L1-R11]` B-4 필터 연동 · API 재호출 0건 |
| TS-041 | L1 | M1 vitest | **PASS** | `[T103/L1-R11b]` 표본 부족 배지 (n=4만) |
| TS-042 | L1 | M1 vitest | **PASS** | `[T103/L1-R11c]` B-2 모수 표기 — **PM 재정의(18:05) 문면 기준 판정**: `n=` 표기 존재 + 워크플로우 전환 시 로스터·`n` 동반 변경. 폐기된 혼합 집계 값(EXECUTE 21·TEST 17·TS 7)은 판정 대상에서 제외 |
| TS-043 | L1 | M1 vitest | **PASS** | `[T103/L1-R10d]` 완료 21 / 전체 23 병기 · 산출물 규모 |
| TS-044 | L1 | M1 vitest | **PASS** | `[T103/L1-R12c]` 대시보드 결측 축소 표시 |
| TS-045 | L1 | M1 정적검사 | **PASS** | `[T103/L1-R13b]` + 검증자 재실행 `DashboardPage.tsx` hex 매칭 **0** · `PIE_COLORS` diff 0줄 |
| TS-046 | L1 | M1 vitest | **PASS** | `[T103/L1-REG3b]` 기존 5블록 렌더 불변 |
| TS-047 | L1 | M1 vitest | **PASS** | `[T103/L1-R11d]` 혼합 중앙값 `5시간 42분` 0건 · B-3 진행중 막대 0건(7개 전건 완료) · B-4가 `button` 필터. A화면 목업 라벨 축은 `[T103/L1-R6]`이 커버 |
| TS-050 | L1 | M1 산출물검사 | **PASS** | 검증자 직접 실행 — §1~§6 6절 전건 존재 · §2.1 코호트 ID **21건 전량**(opd 7·opds 10·opp 4) · 측정 명령 원문 2블록 · 근거등급 E1 기재 · 「91」 계수 표기 **0건** |
| TS-053 | L1 | M1 산출물검사 | **PASS** | 검증자 직접 실행 — `dashboard/` 하위(node_modules 제외) 스냅샷·베이스라인 파일 **0건**, `__snapshots__` 디렉터리 0건. 코드 내 참조는 기대값 출처 주석뿐 |

### 4.2 L2 — 프로세스 통합 17건

| ID | 계층 | 방식 | 결과 | 근거 |
|----|------|------|------|------|
| TS-010 | L2 | M1 pytest+httpx | **PASS** | `test_t103_ts010_pipeline_row_source_keys_and_gate_object` · 5키 보유 · `gate` 객체 4건 |
| TS-011 | L2 | M1 | **PASS** | `test_t103_ts011_deprecated_aliases_filled` + 검증자 실측 `row=[1..19]` · `updated_at` 빈 0건 |
| TS-012 | L2 | M1 | **PASS** | `test_t103_ts012_detail_stats_matches_baseline` + §3.1 대조표 전건 일치 |
| TS-013 | L2 | M1 | **PASS** | `test_t103_ts013_*` 3케이스 + §3.4 실측 (102 `wait` / 103 `in_progress` 우선 / 101 정지) |
| TS-014 | L2 | M1 | **PASS** | `test_t103_ts014_artifacts_full_enumeration_and_classification` + 실측 9건 · `pipeline 5 · verification 2 · log 2 · other 0` |
| TS-015 | L2 | M1 | **PASS** | `test_t103_ts015_*` 2케이스 + §3.4 실측 (`089` 200 / `091` `gate_recorded=false`) |
| TS-017 | L2 | M1 pytest 전체 | **PASS** | `297 passed, 1 skipped` · `[T103/L2-REG2]` 3케이스 · **HEAD 대비 테스트 케이스 삭제 0건**(65개 전건 보존, 현재 95개) — §6 주 참조 |
| TS-018 | L2 | M1 | **PASS** | `test_t103_ts018_*` 2케이스 · 캐시 payload에 실시간 키 부재로 결정론 단정 |
| TS-020 | L2 | M1 | **PASS** | `test_t103_ts020_dashboard_task_counts_identity` + 실측 21+2=23 항등 |
| TS-021 | L2 | M1 | **PASS** | `test_t103_ts021_workflow_stats_cohort_filtered_medians` + §3.2 코호트 필터 재계산 일치 |
| TS-022 | L2 | M1 | **PASS** | `test_t103_ts022_artifact_total_identity` + 실측 `194 == 93+51+43+7` |
| TS-023 | L2 | M1 | **PASS** | `test_t103_ts023_response_uses_source_terminology` + 실측 두 응답 전 키에 `workflow` **0건**, `skill`·`timestamp`·`row_id` 존재 |
| TS-024 | L2 | M1 | **PASS** | `test_t103_ts024_*` 3케이스 · 기존 8필드 타입·중첩·의미 불변 · additive 5필드 기본값 보유 |
| TS-051 | L2 | M1 대조 | **PASS** | §3.1 전건 일치 (베이스라인 = API 응답). 화면 축은 FE 컴포넌트 케이스가 동일 문자열(`7시간 5분` 등)을 단정 — **실브라우저 축은 TS-062 BLOCKED과 연동**(§5) |
| TS-052 | L2 | M1 대조 | **PASS** | §3.2 — §2 ID 목록 필터 재계산이 799/276/75 일치, `102` 완료 여부 무관 |
| TS-062 | L2 | **M2** | **BLOCKED** | 실행 불가 — §5 |
| TS-063 | L2 | **M2** | **BLOCKED** | 실행 불가 — §5 (계약 내용 자체는 in-process에서 전건 확인, 아래 주) |

> **TS-063 보조 확인** — M2(Swagger UI) 집행은 막혔으나, 시나리오의 기대 결과는 프로젝트 소스 in-process 호출로 전건 성립함을 확인했다: 두 엔드포인트 HTTP 200 · 상세에 `stats`·`artifact_items` 존재 · `pipeline[].rows[]` 신규 키 존재 · 대시보드에 `workflow_stats`·`completed_tasks`·`total_tasks`·`artifact_total`·`artifact_by_type` 존재 · `089` 호출 200 · **`/api/tasks`·`/api/dashboard` 경로에 POST/PUT/DELETE/PATCH 라우트 0건**(`openapi.json` 실측). **이는 M1 증거이며 M2 의무를 대체하지 않는다.**

### 4.3 L3 — 사용자 협업 2건

| ID | 계층 | 방식 | 결과 | 처리 |
|----|------|------|------|------|
| TS-060 | L3 | M3 `[SUPERVISOR]` | **보류** | 실행하지 않고 PM에 위임 — §6 요청 양식 |
| TS-061 | L3 | M3 `[SUPERVISOR]` | **보류** | 동상 |

`[SUPERVISOR]` 마커 시나리오는 검증자가 임의 판정하지 않는다. L3는 AC 판정 주체가 아니므로(PLAN P-6) 위 보류가 완료기준 판정을 뒤집지 않는다.

---

## 5. BLOCKED 2건 — 사유와 해소 조건

**사유: 포트 7823 배포본이 낡아 신규 기능을 서빙하지 않는다.**

실측 증거:

```
$ lsof -i :7823 -sTCP:LISTEN
Python  46927 iskang ... TCP localhost:7823 (LISTEN)

$ curl -s "http://127.0.0.1:7823/api/dashboard?project=/Volumes/Data/AIStudio/workspace/ai-framework"
HTTP=200
keys: ['activity_trend','additional_work','alerts','blockers',
       'recent_activities','running_tasks','status_distribution','total_projects']
workflow_stats present: False
```

TS-062·TS-063의 「조건」은 대상 URL을 `http://127.0.0.1:7823`로 고정한다. 그 URL이 서빙하는 것은 **본 태스크 구현 이전의 배포 사본**이며(`workflow_stats` 등 신규 5필드 전무), 여기에 E2E를 걸면 **구현이 아니라 낡은 사본을 측정한 거짓 FAIL**이 나온다.

취하지 않은 우회 3가지와 이유:

| 우회안 | 취하지 않은 이유 |
|--------|----------------|
| 7823 프로세스 종료 후 재기동 | 캡틴 소유 프로세스 — PM 지시로 종료 금지 |
| 임의 포트로 콘솔 재기동해 E2E | 시나리오 「조건」이 고정한 대상 URL 이탈 + 검증자가 배포 환경을 프로비저닝하는 월권. `main.py`가 프로젝트 루트 `dist/`를 찾으므로 FE 서빙에 배포 절차가 필요하다 |
| in-process 결과로 M2를 PASS 처리 | **금지** — M1 증거로 M2 의무를 대체하는 것은 통과 위장이다 (`TEST-SCENARIO.md` §7) |

**해소 조건** — 7823을 프로젝트 소스로 재배포(캡틴 소유 작업)한 뒤 `curl .../api/dashboard | grep workflow_stats`로 신선도를 확인하고, TS-062(cmux 1순위 → playwright 폴백)·TS-063(Swagger `/docs`)을 재집행한다. 재집행 시 나머지 47건은 유효하므로 2건만 돌리면 된다.

---

## 6. L3 2건 — PM 요청 양식

캡틴 확인이 필요한 2건이다. 아래 양식을 그대로 전달하면 된다. **단, §5의 배포본 신선도 문제가 이 2건에도 그대로 걸린다** — 현재 7823 화면에는 A·B 블록이 없으므로, **재배포 이후에 요청해야 한다.**

### TS-060 — 병목 식별 시각 확인

```
[SUPERVISOR 요청 — TS-060 병목 식별 시각 확인]
선행 조건: 127.0.0.1:7823이 본 태스크 구현본으로 재배포되어 있을 것
           (확인: /api/dashboard 응답에 workflow_stats 키가 있으면 최신)
확인 대상: http://127.0.0.1:7823 → 태스크 칸반 → 101 카드 → 「태스크 대시보드」 탭
확인 절차:
  1) 101 상세를 열고 A-1 4타일에서 「최장 단계」를 읽는다
  2) A-2 스택 막대에서 그 단계의 대기/작업 분할을 확인한다
  3) A-3 타임라인에서 대기가 발생한 시각 구간을 확인한다
  4) A-4 표에서 위 3개가 가리키는 원본 행을 대조한다
  5) 진행 중 태스크(102 또는 103) 상세를 열어 「진행 중」 배지를 확인한다
판정 기준 (6항 전건 충족 시 PASS):
  (a) 최장 단계가 TEST-SCENARIO임을 A-1·A-2에서 즉시 식별
  (b) 그 단계의 대기 285분 / 작업 10분 분해를 A-2 2색 스택에서 판독
  (c) A-3에서 대기 발생 시각 구간(17:41→22:26) 확인
  (d) A-4에서 (a)~(c)의 원본 행 대조
  (e) 진행 중 태스크 총 리드타임 타일에 「진행 중」 배지
  (f) 담당 구분이 색 단독이 아니라 라벨 동반 (색각 비의존)
회신 형식: PASS / FAIL + 미충족 항목 번호 + 관측 내용 1~2줄
검증자 주: 위 (a)~(d)의 수치 근거는 L1·L2에서 이미 PASS다.
          이 확인이 묻는 것은 「값이 맞는가」가 아니라 「화면만 보고 판단되는가」다.
```

### TS-061 — 워크플로우 대조 시각 확인

```
[SUPERVISOR 요청 — TS-061 워크플로우 대조 시각 확인]
선행 조건: 동상 (재배포 후)
확인 대상: http://127.0.0.1:7823 → 대시보드 → 기존 5블록 아래 B-1~B-4
확인 절차:
  1) B-4에서 opd를 선택하고 B-1의 대기 비중을 읽는다
  2) opds → opp로 전환하며 같은 값을 읽어 비교한다
  3) opp 선택 상태에서 「표본 부족」 배지를 확인한다
  4) B-2 단계 막대에서 병목 단계를, B-3에서 태스크별 편차를 확인한다
  5) 화면 전체에서 혼합 집계(워크플로우 구분 없는 중앙값) 표기를 찾아본다 — 있으면 FAIL
판정 기준 (6항 전건 충족 시 PASS):
  (a) 대기 비중 차이(21% / 4% / 54%)를 화면 대조만으로 인지
  (b) opp 선택 시 「표본 부족」 배지로 n=4 해석 주의가 전달됨
  (c) B-2에서 워크플로우별 병목 단계 식별 가능
  (d) B-3에서 태스크별 리드타임 편차와 최장/최단 확인 가능
  (e) 혼합 집계 수치가 화면 어디에도 없음
  (f) 필터 전환이 즉시 반영되고 로딩 재요청이 발생하지 않음
회신 형식: PASS / FAIL + 미충족 항목 번호 + 관측 내용 1~2줄
검증자 주: (a)의 21/4/54와 (e)의 혼합 집계 0건은 L1·L2에서 이미 PASS다.
          이 확인이 묻는 것은 판독 가능성이다.
```

---

## 7. 완료기준 7항 판정 (`TASK.md` §완료기준)

| # | 완료기준 | 판정 | 근거 |
|---|---------|------|------|
| (1) | `STATS-BASELINE.md` 수치와 화면 표시값이 전건 일치 | **PASS** | EXECUTE Step 13 검증자 판정 승계(10항목 일치) + 검증자 독립 재확증 — §3.1 대조표 전건 일치, 불일치 0건. 화면 축은 FE 컴포넌트 케이스가 동일 문자열을 단정 |
| (2) | 상세 2탭 + A-1~A-4 렌더 + 101이 425 = 105 + 320(75%) | **PASS** | TS-030·031(2탭·기본 활성) · TS-032~035(A-1~A-4) · TS-001·012 및 §3.1 실측 425/105/320/75 |
| (3) | 대시보드 B-1~B-4 워크플로우별 렌더 + opd/opds/opp 중앙값 799·276·75 | **PASS** | TS-040~043·047(B-1~B-4) · TS-007·021·052 및 §3.2 — **코호트 동결 필터 기준**으로 799/276/75 일치 |
| (4) | 진행 중 태스크(102·103)에서 현재 행 식별 + `key` 패턴 대기 귀속 | **PASS** | §3.4 실측 — `102` → `row_id=2`·`task.user_confirm`·`wait`(전건 `owner=PM`인데도 `wait` 귀속) / `103` → `in_progress` 행 우선. TS-005·013 |
| (5) | `state.json` 없는 태스크에서 상세 패널이 오류 없이 열림 | **PASS** | §3.4 — `089` HTTP **200**(500 아님) · `available=false` · `pipeline` 빈 배열 · 예외 0건. TS-015·036 |
| (6) | 신규 코드 hex 색상 하드코딩 0건 | **PASS** | TS-037·045 케이스 + 검증자 재실행 grep — `TasksPage.tsx` 0건 · `DashboardPage.tsx` 0건 · `PIE_COLORS` diff 0줄 |
| (7) | 기존 칸반·대시보드 기능 회귀 0 | **PASS** | `297 passed, 1 skipped`(BE) · `104 passed`(FE) · TS-017·024·038·046 · **HEAD 대비 테스트 케이스 삭제 0건** · `artifact_count` 값 증가는 P-4 4항 명시적 예외 |

**완료기준 7항 전건 PASS.**

---

## 8. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 (BE) | ruff | **Pass** | `All checks passed!` — `stats.py`·`cache.py`·`models.py`·`routers/{tasks,dashboard}.py`. 주: `~/.opal/.venv`에 ruff 미설치, `/opt/homebrew/bin/ruff` 사용 |
| 2 | 린트 (FE) | eslint | **Pass** | 신규·수정 4파일 위반 0건 |
| 3 | 타입 체크 (BE) | mypy | **N/A** | **mypy 미설치**(venv·시스템 모두). 도구 미비로 미집행 — 우회하지 않고 표면화한다 |
| 4 | 타입 체크 (FE) | tsc / `npm run build` | **Pass (기존 결함 1건 분리)** | 빌드 성공(`✓ built in 749ms`). `tsc --noEmit`의 `TS5101`(tsconfig `baseUrl` deprecated)은 **착수 전부터 있던 기존 결함**이며 신규 코드 기인이 아니다 |
| 5 | `@header` 갱신 | 수동 | **Pass** | 신규·수정 코드 12파일 전건 `@header` 보유 |
| 6 | 사변적 추가 0건 | diff 검토 | **Pass** | `PIE_COLORS` 변경 0줄 · `TTL_SECONDS` 값 불변 · `cache.py` 변경이 P-8 시계 분리(3-tuple→4-tuple)에 한정 · `tasks.py` 제목 폴백 미변경 |
| 7 | RED 테스트 불변성 | diff 검토 | **Pass** | GREEN 루핑 중 RED 단정 약화·삭제 0건. `test_routers.py` 삭제 5줄은 전부 `@header` 메타블록 재기술이며 **테스트 코드 0줄** (HEAD 65개 class/def 전건 보존 확인) |

---

## 9. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | **Pass** | 신규·수정 7파일에 키·토큰·비밀번호 리터럴 0건 |
| 2 | `.gitignore` 확인 | **Pass** | `.env` 항목 존재 (`.gitignore:32`) |
| 3 | 신규 쓰기 엔드포인트 0건 | **Pass** | `openapi.json` 실측 — `/api/tasks`·`/api/dashboard` 경로에 POST/PUT/DELETE/PATCH **0건**. 읽기 전용 원칙의 예외를 늘리지 않았다 |
| 4 | 경로 조작 방어 | **Pass** | `artifacts` 전수화로 노출 파일이 늘었으나 `GET /api/tasks/artifact`가 traversal을 차단한다. 실측: `name=../../../etc/passwd` → **400** · `name=../101-.../TASK.md` → **400** · `name=TASK.md` → 200 |
| 5 | XSS 경로 | **Pass (변경 없음)** | 응답에 `note` 원문이 실리나 렌더 경로는 기존 `MarkdownView`를 그대로 사용하며 방어 수준 변경 0건 |

---

## 10. 시나리오 타당성 사전 검증 (헌법 §4)

작성자 필드를 무비판 수용하지 않고 실행 전에 시나리오 집합의 타당성을 확인했다.

| 축 | 충족 | 근거 |
|----|------|------|
| 실패 입력 / 결측 | 충족 | TS-004(빈 rows·`created_at` 결측·파싱 실패) · TS-015(파일 부재) · TS-036·044(빈 응답) |
| 경계조건 | 충족 | TS-003(음수 clamp) · TS-006(완료 경계) · TS-007(짝수 n 중앙값 275.5 · 비중 3.68% 반올림 · n<5) · TS-009(0·`None`) · TS-016(mtime 경계) · TS-039(폭 초과) |
| 실데이터 / 실연동 | 충족 | 전 픽스처가 실 `tasks/*/state.json` 또는 그 동결 복사본. L2가 실 파일 → 실 API 호출 경로. 가짜 객체로 검증 대상 구현을 대체한 시나리오 0건 |

**「약한 시나리오」 반환 사유 없음** — 집행 요건을 충족해 실행에 들어갔다.

또한 목업 대체 여부를 점검한 결과, **지시된 실연동이 목업으로 대체된 사례 0건**이다. FE 케이스는 API 클라이언트 계층에 실응답 스냅샷을 주입하되(선례 패턴) BE 구현 자체는 L2에서 실제 호출·검증했다.

---

## 11. 발견 사항 (결함 아님 — 기록용)

1. **`tsc TS5101`은 기존 결함이다.** `tsconfig.json:8` `baseUrl` deprecated 경고. 본 태스크 착수 전부터 존재하며 신규 코드와 무관하다. 별건으로 다룰 사안이지 본 태스크의 회귀가 아니다.
2. **mypy 미설치.** `test-tool resolve`가 BE typecheck 필수 도구로 지정하나 환경에 없다. 통과 처리하지 않고 N/A로 표면화했다.
3. **`103` 현재 행이 실행 중 이동했다.** 시나리오 작성 시점 `test_scenario.test_scenario_md` → 검증 시점 `test.run_tests`(row 13). 이동값 규약대로 불변식 단정이라 판정에 영향 없다 — 규약이 실제로 작동함을 보여준 사례다.
4. **`artifact_total` 194.** 베이스라인 §5 기준 시점 값 192에서 증가했으나 §7이 확정한 「`state.json` 보유 23태스크」 스코프값과 일치한다. §6.2 예고대로 하한 단정으로 처리했고 실패로 판정하지 않았다.
5. **`test_routers.py` 삭제 5줄.** `TEST-SCENARIO.md` TS-017 주가 「테스트 코드 삭제 0줄」을 확인 수단으로 명시했는데 `git diff --numstat`는 5줄 삭제를 보고한다. 실물 확인 결과 **전부 `@header` 메타블록 재기술**이고 테스트 코드는 0줄이다(HEAD 65개 class/def 전건 보존). 문면과 실측이 갈릴 수 있는 지점이라 기록해 둔다.

---

## 12. 검증자 준수 사항

- 구현·테스트 코드 수정 **0건**. `TEST-SCENARIO.md`·`TASK.md`·`PLAN.md`·`STATS-BASELINE.md` 수정 0건. `state.json` 편집 0건.
- 포트 7823 프로세스 **종료하지 않음**.
- 기대값은 `STATS-BASELINE.md`에서만 취득. 구현 출력을 기대값으로 되쓴 항목 0건.
- 이동값(`.md` 전수·화이트리스트·모수)은 절대값 불일치를 실패로 판정하지 않고 항등·하한으로 처리.
- 도구·환경 미비(M2 2건, mypy)는 우회하지 않고 BLOCKED / N/A로 표면화.


---

## 12. 마감 갱신 — BLOCKED 해소 · L3 확인 · 확장 검증 (PM, 2026-08-26 16:20)

### 12.1 BLOCKED 2건 → PASS

`§5`가 남긴 BLOCKED 2건은 **재배포로 해소**됐다. 캡틴이 콘솔을 재배포·재기동한 뒤 PM이 재집행했다.

| ID | 판정 | 실측 |
|----|------|------|
| TS-062 (B 블록 실연동) | **PASS** | `/api/dashboard` 실응답 — 완료 21 / 전체 23, 중앙값 opd 799 · opds 276 · opp 75, 대기 비중 21 / 4 / 54. 베이스라인과 전건 일치 |
| TS-063 (A 블록 실연동) | **PASS** | `/api/tasks/detail` 실응답 — `101` 총 425 = PM 105 + 워커 0 + 캡틴 320, rows 19 · gate 4 · 산출물 9, `row` 1~19 연속, `updated_at` 공백 0. `089`(state.json 부재) HTTP 200 · `available=false` · 예외 0 |

### 12.2 L3 2건 → PASS

캡틴이 화면에서 직접 확인했다(2026-08-26). FAIL 항목 지적 없음.

| ID | 판정 | 확인 대상 |
|----|------|----------|
| TS-060 (병목 식별 시각 확인) | **PASS** | 태스크 상세 A-1~A-4 — 최장 단계 즉시 식별·대기/작업 분해 판독·시각 구간·원본 행 대조·「진행 중」 배지·담당 라벨 동반 |
| TS-061 (워크플로우 대조 시각 확인) | **PASS** | 대시보드 B-1~B-4 — 필터 전환 시 좁혀짐·대기 비중 변화·「표본 부족」 배지 |

### 12.3 범위 확장분 검증 (캡틴 지시 4건)

TEST 단계 이후 캡틴 지시로 범위가 4회 확장됐고, 각각 검증을 마쳤다.

| 확장 | 실측 |
|------|------|
| 3계열 분해(PM·워커·캡틴) | `101` 425 = PM 105 + 워커 0 + 캡틴 320 (기존 2계열과 **항등**) · `103` 분해 성립 · clamp 0 |
| 시각 표기 `YY-MM-DD HH:mm:ss` | 날짜 경계 오독 7태스크 8곳 해소 · 기존 276행 스키마 전건 통과 · 신규 기록은 초까지 |
| 차트 호버 툴팁 | A-2·B-2·B-3·A-1 구획별 툴팁 · 「워커 미측정」 막대 전체 툴팁 · 겹침 차단 |
| 야간 시간대 보정 | `opd` 중앙값 799 → **425**(-47%) · `101` 불변 · 워커 미보정 실증 · 설정 2층 머지 |

### 12.4 최종 테스트 (2026-08-26 16:18)

| 스위트 | 착수 기준선 | 최종 |
|--------|------------|------|
| `state-tool` | 374 | **396 passed**, 3 skipped |
| BE (`dashboard/backend`) | 249 | **357 passed**, 1 skipped |
| FE (`vitest`) | 85 | **123 passed** / 9 files |
| 빌드 | — | `✓ built` |

기존 케이스 회귀 **0건**. `tsc`의 `TS5101` 1건은 `tsconfig.json` `baseUrl` deprecation으로 착수 전부터 있던 기존 결함이다.

### 12.5 최종 판정 — **All Pass**

`§0`의 Partial Fail은 BLOCKED 2건이 해소되어 **All Pass로 갱신**한다. 시나리오 49건 + 부록 B 확장분 전건 PASS, FAIL 0건, 미집행 0건.
