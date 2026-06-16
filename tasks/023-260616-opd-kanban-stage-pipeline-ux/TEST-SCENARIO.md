# TEST SCENARIO: OPAL Console 칸반 현재 단계 표시 + 파이프라인 스테퍼 모호성 개선

> 작성일: 2026-06-16 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표 기반
> RED-first 트랙: **혼합** — BE 로직(파생/그룹/집계)은 RED-first 강제(비즈니스 로직·API 계약), FE 렌더(카드/스테퍼)는 구현 후 시각 검증(UI 화면). 근거: `red-first.md §1.5`.

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | `TaskDetailResponse.pipeline` 타입 변경(PipelineRow[]→PipelineStageGroup[]) | FE 타입 미동기 시 상세 Sheet 스테퍼 렌더 실패 | P1 | L1(BE 스키마)+L3(실렌더) | S-011, S-017 |
| H-2 | `_derive_current_stage` status 분기 | 전부 done 태스크에 빈/오류 stage 노출 | P1 | L1 | S-003 |
| H-3 | `_aggregate_status` 혼재 케이스(D-2) | done+pending 혼재 단계를 done으로 오집계 | P1 | L1 | S-008 |
| H-4 | 빈 rows / state=None 경로 | rows 빈 배열에서 IndexError → API 500 | P1 | L1 | S-004, S-012 |
| H-5 | FE 색상 토큰 하드코딩 | status-* 토큰 외 hex → 테마 깨짐, CONVENTIONS 위반 | P2 | L3 | S-014, S-016 |
| H-6 | 전체(read-only 계약) | state-tool 쓰기/파일편집 유입 → read-only 불변 위반 | P0 | L1(정적) | S-018 |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

| 테이블 | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| rows(in_progress) | `rows_ip` | TASK done·done / PLAN in_progress / EXECUTE pending | fixture (pytest, dict 리터럴) |
| rows(첫 미완료) | `rows_pending` | TASK done·done·pending / PLAN pending×N (005 모사) | fixture |
| rows(전부 done) | `rows_done` | TASK·PLAN·EXECUTE·CLOSE 전부 done (015 모사, 9행) | fixture |
| rows(혼재) | `rows_mixed` | EXECUTE done+pending 혼재 | fixture |
| rows(blocked) | `rows_blocked` | TEST 단계 blocked 포함 | fixture |
| rows(빈 배열) | `rows_empty` | `[]` | fixture |
| state 카드 | `state_card` | current_status=in_progress + rows_pending | fixture |
| Console 실데이터 | 진행중 태스크 1건 | state.json 존재, rows 다단계 | cmux 기동 후 실 스캔 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (호출) | Then (검증) |
|---------|------------|------------|------------|
| S-001 | rows_ip | `_derive_current_stage(rows_ip)` | 반환 = in_progress 행 stage("PLAN") |
| S-002 | rows_pending | `_derive_current_stage(rows_pending)` | 반환 = "TASK"(첫 미완료) |
| S-003 | rows_done | `_derive_current_stage(rows_done)` | 반환 = "CLOSE"(마지막) |
| S-004 | rows_empty | `_derive_current_stage([])` | 반환 = "" (예외 없음) |
| S-005 | state_card | `_state_to_task_card(...)` | `.current_stage != ""` |
| S-006 | rows(TASK·TASK·PLAN) | `_group_pipeline_stages(rows)` | [TASK(total=2), PLAN(total=1)] 2그룹, 순서 보존 |
| S-007 | rows(단계 전부 done) | `_aggregate_status(grp)` | "done" |
| S-008 | rows_mixed | `_aggregate_status(grp)` | "in_progress" |
| S-009 | rows_blocked | `_aggregate_status(grp)` | "blocked"(우선) |
| S-010 | rows(전부 pending) | `_aggregate_status(grp)` | "pending" |
| S-011 | rows_done | `get_task_detail` (TestClient) | `pipeline[]` 각 원소 stage/done_count/total/status 필드 보유 |
| S-012 | rows_empty/state=None | `get_task_detail` | `pipeline == []`, status 200(500 없음) |
| S-013 | Console 실데이터 진행중 태스크 | 칸반 진행중 카드 시각 확인 | 단계명(TASK/PLAN/EXECUTE/TEST/CLOSE 중) 뱃지 표시 |
| S-014 | 동일 | 진행중 카드 뱃지 색상 확인 | status 토큰 강조, hex 하드코딩 없음 |
| S-015 | 동일 | 상세 Sheet 스테퍼 시각 확인 | stage 1회씩 순서대로, `TASK TASK`/`PLAN PLAN PLAN` 반복 사라짐 |
| S-016 | 동일 | 스테퍼 각 단계 확인 | done/total 카운트(예: `TEST 0/3`) 표시, 색상 토큰 |
| S-017 | 동일 | 상세 Sheet 전체 렌더 확인 | Sheet 비파괴 정상 렌더(H-1) |
| S-018 | 변경 4파일 | grep 정적 확인 | state-tool 쓰기 커맨드·파일 쓰기 호출 부재 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력) — RED-first 트랙

#### S-001: in_progress 행 → 해당 stage 파생

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R1 규칙①) |
| 대상 | `_derive_current_stage` |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | rows_ip (PLAN 행이 in_progress) |
| 기대 결과 | 반환값 == "PLAN" |
| 도구 | pytest |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{op-dev-test-agent가 채움}_ |
| 상세 | _{op-dev-test-agent가 채움}_ |

#### S-002: in_progress 없음 → 첫 미완료 stage (005 케이스)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R1 규칙②) |
| 대상 | `_derive_current_stage` |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | rows_pending (TASK done·done·pending, PLAN pending) |
| 기대 결과 | 반환값 == "TASK" |
| 도구 | pytest |
| 실행 명령 | _{EXECUTE 워커가 채움}_ |
| 결과 | _{채움}_ |
| 상세 | _{채움}_ |

#### S-003: 전부 done → 마지막 stage (015 케이스) [H-2]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 (R1 규칙③) |
| 대상 | `_derive_current_stage` |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | rows_done (9행 전부 done, 마지막 CLOSE) |
| 기대 결과 | 반환값 == "CLOSE" |
| 도구 | pytest |
| 실행 명령 | _{채움}_ |
| 결과 | _{채움}_ |
| 상세 | _{채움}_ |

#### S-004: 빈 rows → "" (IndexError 없음) [H-4]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `_derive_current_stage` |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | `[]` 입력 |
| 기대 결과 | 반환값 == "", 예외 미발생 |
| 도구 | pytest |
| 실행 명령 | _{채움}_ |
| 결과 | _{채움}_ |
| 상세 | _{채움}_ |

#### S-005: state 있는 카드 current_stage 비어있지 않음

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R1 AC) |
| 대상 | `_state_to_task_card` |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | state_card (current_status=in_progress + rows_pending) |
| 기대 결과 | 반환 카드 `.current_stage != ""` (== "TASK") |
| 도구 | pytest |
| 실행 명령 | _{채움}_ |
| 결과 | _{채움}_ |
| 상세 | _{채움}_ |

#### S-006: stage 그룹 변환 + 등장순서 보존

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R2 그룹핑) |
| 대상 | `_group_pipeline_stages` |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | rows = [TASK, TASK, PLAN] |
| 기대 결과 | 2그룹 [stage=TASK total=2, stage=PLAN total=1], 순서 보존 |
| 도구 | pytest |
| 실행 명령 | _{채움}_ |
| 결과 | _{채움}_ |
| 상세 | _{채움}_ |

#### S-007: 집계 — 전부 done → done

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (D-2 ②) |
| 대상 | `_aggregate_status` |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | 단계 내 행 전부 done |
| 기대 결과 | "done" |
| 도구 | pytest |
| 실행 명령 | _{채움}_ |
| 결과 | _{채움}_ |
| 상세 | _{채움}_ |

#### S-008: 집계 — 혼재(done+pending) → in_progress [H-3]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 (D-2 ③) |
| 대상 | `_aggregate_status` |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | rows_mixed (done+pending) |
| 기대 결과 | "in_progress" |
| 도구 | pytest |
| 실행 명령 | _{채움}_ |
| 결과 | _{채움}_ |
| 상세 | _{채움}_ |

#### S-009: 집계 — blocked 포함 → blocked 우선 [H-3]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 (D-2 ①) |
| 대상 | `_aggregate_status` |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | rows_blocked (blocked + 그 외 혼재) |
| 기대 결과 | "blocked" |
| 도구 | pytest |
| 실행 명령 | _{채움}_ |
| 결과 | _{채움}_ |
| 상세 | _{채움}_ |

#### S-010: 집계 — 전부 pending → pending

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (D-2 ④) |
| 대상 | `_aggregate_status` |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | 단계 내 행 전부 pending |
| 기대 결과 | "pending" |
| 도구 | pytest |
| 실행 명령 | _{채움}_ |
| 결과 | _{채움}_ |
| 상세 | _{채움}_ |

### L2. 프로세스 통합 (자동, 실 API read) — RED-first 트랙

#### S-011: get_task_detail 응답 pipeline 그룹 스키마 [H-1]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 (R2 AC) |
| 대상 | `GET /api/tasks/detail` (FastAPI TestClient) |
| 계층 | L2 |
| 실행 방식 | M1 (pytest + TestClient) |
| 조건 | rows_done 보유 태스크 픽스처 |
| 기대 결과 | 응답 `pipeline[]` 각 원소가 stage·done_count·total·status 필드 보유, 행 단위 아님 |
| 도구 | pytest |
| 실행 명령 | _{채움}_ |
| 결과 | _{채움}_ |
| 상세 | _{채움}_ |

#### S-012: 빈 rows / state=None → pipeline=[] 200 [H-4]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `GET /api/tasks/detail` |
| 계층 | L2 |
| 실행 방식 | M1 (pytest + TestClient) |
| 조건 | rows_empty 또는 state.json 없는 태스크 |
| 기대 결과 | status 200, `pipeline == []`, 500 미발생 |
| 도구 | pytest |
| 실행 명령 | _{채움}_ |
| 결과 | _{채움}_ |
| 상세 | _{채움}_ |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커) — 구현 후 시각 검증

#### S-013: 진행중 카드 단계 뱃지 표시 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R1 AC 카드 표시) |
| 대상 | 칸반 진행중 카드 (`/tasks`) |
| 계층 | L3 |
| 실행 방식 | M3 (사용자 협업 — cmux 실렌더) |
| 조건 | Console 기동 + 진행중 태스크 1건 이상 존재 |
| 기대 결과 | 진행중 카드에 비어있지 않은 단계명(TASK/PLAN/EXECUTE/TEST/CLOSE 중 하나) 뱃지 표시 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | _{캡틴 확인 후 기록}_ |
| 상세 | _{캡틴 확인 후 기록}_ |

#### S-014: 진행중 카드 단계 뱃지 색상 토큰 강조 [SUPERVISOR] [H-5]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | 진행중 카드 단계 뱃지 |
| 계층 | L3 |
| 실행 방식 | M3 (사용자 협업) |
| 조건 | Console 기동 |
| 기대 결과 | 단계 뱃지가 status 토큰으로 강조되어 식별 가능 (hex 하드코딩 아님) |
| 실행자 | [SUPERVISOR] |
| 결과 | _{캡틴 확인 후 기록}_ |
| 상세 | _{캡틴 확인 후 기록}_ |

#### S-015: 스테퍼 stage 중복 제거 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | (R2 AC 중복 제거) |
| 대상 | 상세 Sheet 파이프라인 스테퍼 |
| 계층 | L3 |
| 실행 방식 | M3 (사용자 협업) |
| 조건 | 다단계 태스크 카드 클릭 → 상세 Sheet 오픈 |
| 기대 결과 | 스테퍼가 stage를 중복 없이 1회씩 순서대로 표시 — `TASK TASK`/`PLAN PLAN PLAN`/`TEST TEST TEST` 반복 사라짐 |
| 실행자 | [SUPERVISOR] |
| 결과 | _{캡틴 확인 후 기록}_ |
| 상세 | _{캡틴 확인 후 기록}_ |

#### S-016: 스테퍼 단계 내 완료/전체 표현 [SUPERVISOR] [H-5]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 (R2 AC 서브항목) |
| 대상 | 상세 Sheet 스테퍼 각 단계 |
| 계층 | L3 |
| 실행 방식 | M3 (사용자 협업) |
| 조건 | 다단계 태스크 상세 Sheet |
| 기대 결과 | 각 단계에 완료/전체 카운트(예: `TEST 0/3`) 표시, 단계 내 진행 식별 가능, status 토큰 색상 |
| 실행자 | [SUPERVISOR] |
| 결과 | _{캡틴 확인 후 기록}_ |
| 상세 | _{캡틴 확인 후 기록}_ |

#### S-017: 상세 Sheet 비파괴 렌더 (타입 동기) [SUPERVISOR] [H-1]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | 상세 Sheet 전체 |
| 계층 | L3 |
| 실행 방식 | M3 (사용자 협업) + npm run build tsc 선행 |
| 조건 | 스키마 변경 후 FE 타입 동기 완료 |
| 기대 결과 | 상세 Sheet가 깨지지 않고 정상 렌더(스테퍼·산출물 탭 포함), 콘솔 에러 없음 |
| 실행자 | [SUPERVISOR] |
| 결과 | _{캡틴 확인 후 기록}_ |
| 상세 | _{캡틴 확인 후 기록}_ |

### L1(정적). read-only 계약 불변

#### S-018: read-only 불변 정적 확인 [H-6]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | 변경 4파일 |
| 계층 | L1 (정적 grep) |
| 실행 방식 | M1 (grep) |
| 조건 | EXECUTE 완료 후 changed_files |
| 기대 결과 | state-tool 쓰기 커맨드(init/advance/mark/block) 호출·파일 쓰기(open(w)/Path.write) 부재. 변경은 read/응답가공/표시 한정 |
| 도구 | grep |
| 실행 명령 | _{채움}_ |
| 결과 | _{채움}_ |
| 상세 | _{채움}_ |

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R1 규칙① | - | L1 | S-001 | `tests/test_routers.py`:test_derive_stage_in_progress | |
| R1 규칙② | - | L1 | S-002 | :test_derive_stage_first_pending | 005 케이스 |
| R1 규칙③ | H-2 | L1 | S-003 | :test_derive_stage_all_done | 015 케이스 |
| R1 엣지 | H-4 | L1 | S-004 | :test_derive_stage_empty | |
| R1 AC(응답) | - | L1 | S-005 | :test_card_current_stage_filled | |
| R2 그룹핑 | - | L1 | S-006 | :test_group_pipeline_order | |
| R2 집계② | - | L1 | S-007 | :test_aggregate_all_done | |
| R2 집계③ | H-3 | L1 | S-008 | :test_aggregate_mixed | |
| R2 집계① | H-3 | L1 | S-009 | :test_aggregate_blocked | |
| R2 집계④ | - | L1 | S-010 | :test_aggregate_all_pending | |
| R2 AC(응답) | H-1 | L2 | S-011 | :test_detail_pipeline_groups | |
| R2 엣지 | H-4 | L2 | S-012 | :test_detail_empty_rows | |
| R1 AC(카드 표시) | - | L3 | S-013 | cmux 실렌더 | [SUPERVISOR] |
| R1 가독성 | H-5 | L3 | S-014 | cmux 실렌더 | [SUPERVISOR] |
| R2 AC(중복 제거) | - | L3 | S-015 | cmux 실렌더 | [SUPERVISOR] |
| R2 AC(서브항목) | H-5 | L3 | S-016 | cmux 실렌더 | [SUPERVISOR] |
| R2 회귀(타입 동기) | H-1 | L3 | S-017 | npm run build + cmux | [SUPERVISOR] |
| read-only 불변 | H-6 | L1정적 | S-018 | grep | |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | ruff (BE) | ✅ Pass | All checks passed (EXECUTE BE 워커 확인) |
| 2 | 타입 체크 | tsc (`npm run build`, FE) | ✅ Pass | tsc -b && vite build 성공, 타입 에러 0건 (H-1 동기 확인) |
| 3 | 포맷터 | ruff format (BE) | ✅ Pass | ruff clean |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | ✅ Pass | 표시/응답가공 로직만, 시크릿 없음 |
| 2 | .gitignore 확인 | ✅ Pass | 신규 비밀파일 없음 |
| 3 | read-only 불변(state-tool 쓰기·파일 쓰기 부재) | ✅ Pass | S-018 grep — state-tool 쓰기/open(w)/write 호출 부재 (BE 2파일) |

## 7. 판정

**Partial Pass (자동 전부 Pass, L3 [SUPERVISOR] 캡틴 확인 대기) — 근거 아래.**

### 자동 검증 결과 (L1/L2/정적)

| 시나리오 | 결과 | 증거 |
|---------|------|------|
| S-001~S-012 (BE 파생·집계·그룹·detail) | ✅ Pass | `pytest test_routers.py` 신규 12/12 GREEN, 전체 45 passed 0 failed |
| S-018 (read-only 정적) | ✅ Pass | grep — 쓰기 커맨드/파일 쓰기 부재 |
| (추가) 실 API L2 | ✅ Pass | 소스 백엔드(7824) + 실 state.json(023): `current_stage='TEST'`, pipeline 7그룹(TASK~CLOSE) 각 stage/done_count/total/status 정상, 중복 라벨 없음 |
| S-013~S-017 (FE 실렌더) | ✅ Pass | 캡틴 [SUPERVISOR] 확인 (2026-06-16) — 152 카드 단계 뱃지 `TEST`, 스테퍼 단계당 1회+카운트, 동일 라벨 반복 사라짐, Sheet 정상 렌더 |

> L1/L2 RED→GREEN 증거: RED 12/12 실패(함수 미구현) → GREEN 12/12 통과. 테스트 불변 유지(구현으로 통과).

### fix 루프 (1회) — TEST 실데이터 검증서 발견·교정

| 항목 | 내용 |
|------|------|
| 발견 | 진행중 카드가 미시작 `CLOSE` 표기(첫 pending 규칙) + `na`/`skipped` status 미고려 (실데이터 152) |
| 교정 | `_derive_current_stage`=도달 단계 기준(미시작 단계 표시 금지), `_aggregate_status`/카운트=na/skipped 제외 |
| RED→GREEN | 신규 4 테스트 RED(AssertionError) → 구현 수정 후 GREEN. 최종 **49 passed / 0 failed** |
| 검증 | 배포본(7823) 152: 카드·상세 `current_stage='TEST'`, 스테퍼 `TEST 2/2 done`·`CLOSE 0/1 pending` |

**최종 판정: All Pass** — L1/L2 49 passed, L3 캡틴 확인 PASS, read-only 불변 Pass, 코드품질(ruff/tsc) Pass.

### PM Gate 체크 (7대 강제 룰)

- [x] 테스트 더블(가짜 객체·자동 대체) 시나리오 본문에 부재 — 실 dict 픽스처·실 TestClient·grep만 사용
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (아래)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M3) 명시

### L3 [SUPERVISOR] PM 표준 요청 양식 (TEST 단계 사용)

```
캡틴, S-013~S-017은 사용자 협업 검증이 필요합니다.
요청 내용: Console를 cmux로 기동(opal-cli console start) 후
  ① 칸반 진행중 카드에 단계 뱃지가 표시되는지 (S-013/014)
  ② 다단계 태스크 상세 Sheet 스테퍼가 stage 1회씩 + done/total로 표시되고
     동일 stage 반복이 사라졌는지 (S-015/016)
  ③ 상세 Sheet가 깨지지 않고 정상 렌더되는지 (S-017)
기대 결과: 위 각 항목 충족
확인 후 결과(PASS/FAIL + 상세)를 알려주세요.
```
