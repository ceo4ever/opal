# TEST-SCENARIO: state-tool 다중 Step 조기 done 가드

> 작성일: 2026-06-10 | 입력: PLAN.md §리스크 가설 표 + §3.2.5 | 트랙: **RED-first 자기적용** (red-first.md §1.5 — self-confirming 위험: 상태 전이 로직)
> 러너: `opal/tools/state-tool/tests/` unittest (T-11 표준 라이브러리만, pytest 금지)
> [MUST] 본 시나리오의 L1 케이스(S-1~S-4, S-8)가 곧 R-1/R-5의 RED 테스트다. 미구현 상태에서 실패(exit≠0)를 증거로 기록한 뒤 GREEN 진입한다 (red-first.md §1).

---

## 1. 리스크 가설 → 검증 계층 매핑

| 가설 | 변경 단위 | 운영 영향 | 검증 계층 | 시나리오 |
|------|----------|---------|----------|---------|
| H-1 | done 무조건 분기 교체 | P0 | L1+L2 | S-1, S-5, S-6 |
| H-2 | `step` 신규 키 영속화 | P1 | L1+L2 | S-1, S-2, S-5, S-6 |
| H-3 | in_progress 자동 차단 (단계 전환) | P0 | L1 | S-3 |
| H-4 | CLOSE 진입 차단 | P0 | L1 | S-4 |
| H-5 | 비정형 step 파싱 | P2 | L1 | S-7 |
| H-6 | ERROR_CODES count 30 비파괴 | P1 | L2 | S-6 |

- **L1(단위)**: state.json 관측 행위(status/step/exit code)로 검증 — 공개 인터페이스 (red-first.md §4).
- **L2(통합/회귀)**: 전체 unittest discover + 완전성 테스트.

---

## 2. AC ↔ 가설 ↔ 계층 ↔ 시나리오 ↔ 테스트파일:케이스 매핑표

| TS-ID | AC (TASK R-N) | 가설 | 계층 | 시나리오 | 테스트파일 : 케이스(예정) |
|-------|---------------|------|------|---------|--------------------------|
| TS-001 | R-1: `--done --step 1/7` → in_progress + `step:"1/7"` | H-1, H-2 | L1 | S-1 | `test_state_tool.py::TestMultiStepDoneGuard::test_step_n_lt_m_keeps_in_progress` |
| TS-002 | R-2: `--done --step 7/7` → done | H-2 | L1 | S-2 | `test_state_tool.py::TestMultiStepDoneGuard::test_step_n_eq_m_marks_done` |
| TS-003 | R-5 ②: 미완(1/7) 행 뒤 단계 전환 거부 | H-3 | L1 | S-3 | `test_state_tool.py::TestMultiStepDoneGuard::test_incomplete_step_blocks_next_stage` |
| TS-004 | R-5 ③: 미완 선행 행 + CLOSE 진입 거부 | H-4 | L1 | S-4 | `test_state_tool.py::TestMultiStepDoneGuard::test_incomplete_step_blocks_close_entry` |
| TS-005 | R-3/C-4: `--step` 없는 mark·단일·비-EXECUTE·구 state.json | H-1, H-2 | L2 | S-5 | `test_state_tool.py::TestMultiStepDoneGuard::test_no_step_legacy_immediate_done` |
| TS-006 | R-3: 전체 회귀 + count==30 | H-1, H-6 | L2 | S-6 | 전체 `unittest discover` + `TestErrorCodesCompleteness::test_error_codes_count` |
| TS-007 | H-5 경계: 비정형 step | H-5 | L1 | S-7 | `test_state_tool.py::TestMultiStepDoneGuard::test_malformed_step_falls_back_to_done` |
| TS-008 | R-1 추가: 순차 1/7→2/7→7/7 | H-1, H-2 | L1 | S-8 | `test_state_tool.py::TestMultiStepDoneGuard::test_sequential_step_progress_then_done` |

---

## 3. 시나리오 상세 (L1 = RED 케이스)

> 공통 픽스처: `BaseTestCase`(`test_state_tool.py:123`) + `_init`(`:154`) + `_mark`(`:176`, `step=` 지원) + `_mock_now()`(date.js 모킹). EXECUTE 다중 Step 검증용 rows_spec은 `TASK→PLAN→EXECUTE→CLOSE/사용자 확인` 또는 EXECUTE 단일 행 흡수 구조 사용.

### S-1 — N<M done 차단 + 진행률 저장 (RED → TS-001)

| 항목 | 내용 |
|------|------|
| 전제 | rows: `[TASK 작업, PLAN 작업, EXECUTE 작업, CLOSE 사용자 확인]`. row1·row2 done 처리(앞 단계 완료) |
| 실행 명령 | `mark --row 3 --done --as-worker --worker-stage EXECUTE --step 1/7` |
| 기대 결과 | exit 0. state.json row3: `status=="in_progress"`, `status_label=="🔄"`, `step=="1/7"` (done 아님) |
| RED 증거 | 미구현 시 row3 `status=="done"` → `assertEqual(status,"in_progress")` AssertionError (exit≠0) |
| Pass 판정 | `status=="in_progress"` AND `row.get("step")=="1/7"` |

### S-2 — 마지막 Step done (RED → TS-002)

| 항목 | 내용 |
|------|------|
| 전제 | S-1과 동일 구조. row1·row2 done. row3을 1/7→...→6/7 진행(in_progress) 후 |
| 실행 명령 | `mark --row 3 --done --as-worker --worker-stage EXECUTE --step 7/7` |
| 기대 결과 | exit 0. row3 `status=="done"`, `status_label=="✅"`, `step=="7/7"` |
| RED 증거 | 미구현 시 step 미저장 → `assertEqual(row.get("step"),"7/7")` 실패 |
| Pass 판정 | `status=="done"` AND `step=="7/7"` |

### S-3 — 단계 전환 미완 거부 (RED → TS-003)

| 항목 | 내용 |
|------|------|
| 전제 | row1·row2 done. row3(EXECUTE) `--step 1/7`로 in_progress 처리 후, 다음 단계 행(CLOSE row4) mark/advance 시도 |
| 실행 명령 | `mark --row 4 --done` (또는 `advance --row 4`) |
| 기대 결과 | exit 1, `error=="stage_transition_violation"`, `incomplete_rows`에 row3(=3) 포함 |
| RED 증거 | 미구현 시 row3가 done이 되어 차단 안 됨 → exit 0 → `assertEqual(error,"stage_transition_violation")` 실패 |
| Pass 판정 | `error=="stage_transition_violation"` AND `3 in incomplete_rows` |

### S-4 — CLOSE 진입 미완 거부 (RED → TS-004)

| 항목 | 내용 |
|------|------|
| 전제 | rows: `[TASK 작업, EXECUTE 작업, CLOSE 사용자 확인, CLOSE DONE.md 생성]`. row1 done, row2(EXECUTE) `--step 2/5`(in_progress) |
| 실행 명령 | CLOSE 첫 행 `mark --row 3 --done --owner user` (또는 advance) |
| 기대 결과 | exit 1, `error=="stage_transition_violation"` (선행 in_progress EXECUTE 행이 stage-transition guard로 close gate 도달 전 차단) |
| RED 증거 | 미구현 시 row2 done → CLOSE 진입 가능 → exit 0 실패 |
| Pass 판정 | `error=="stage_transition_violation"` AND `2 in incomplete_rows` |

### S-8 — 순차 진행률 누적 후 done (RED → TS-008)

| 항목 | 내용 |
|------|------|
| 전제 | S-1 구조. row1·row2 done |
| 실행 명령 | row3에 `--step 1/7` → `--step 2/7` → `--step 7/7` 순차 mark |
| 기대 결과 | 1/7·2/7 후 `status=="in_progress"` & `step` 갱신; 7/7 후 `status=="done"` & `step=="7/7"` |
| RED 증거 | 미구현 시 1/7 mark에서 즉시 done → 2/7 mark는 멱등 통과(상태 불변) → done 조기 발생으로 실패 |
| Pass 판정 | 중간 in_progress 유지, 최종 done |

---

## 4. 시나리오 상세 (L2 = 회귀/하위호환)

### S-5 — 하위 호환: --step 없는 mark / 단일 / 비-EXECUTE / 구 state.json (TS-005)

| 항목 | 내용 |
|------|------|
| 실행 명령 1 | `mark --row 1 --done` (`--step` 미지정) |
| 기대 1 | 즉시 `status=="done"` (기존 동작 불변) |
| 실행 명령 2 | `step` 키 없는 기존 state.json(직접 작성)에 mark/show/validate |
| 기대 2 | KeyError 없이 정상 동작 (`row.get("step")` None-safe) |
| 실행 명령 3 | 단일 Step 비-EXECUTE 행 mark |
| 기대 3 | 즉시 done |
| Pass 판정 | 3종 모두 기존 동작 유지, 예외 없음 |

### S-6 — 전체 회귀 + ERROR_CODES 완전성 (TS-006)

| 항목 | 내용 |
|------|------|
| 실행 명령 | `python3 -m unittest discover -s tests -p 'test_*.py'` (state-tool 디렉토리) |
| 기대 결과 | `Ran N tests ... OK` (기존 165 + 신규 전부 PASS). `TestErrorCodesCompleteness::test_error_codes_count`에서 `len(ERROR_CODES)==30` 유지 |
| 실행 증거 | 콘솔 `Ran <N> tests in <t>s` + `OK` 출력 캡처 |
| Pass 판정 | exit 0, 실패/에러 0건, count==30 |

### S-7 — 비정형 step 경계 (TS-007)

| 항목 | 내용 |
|------|------|
| 실행 명령 | `mark --row R --done --step "abc"` / `"3"` / `"0/0"` / `"8/7"` |
| 기대 결과 | `_parse_step`가 None 반환 → 기존 done 경로. 크래시(traceback) 없음, exit 0, status=done |
| Pass 판정 | 모든 비정형 입력에서 예외 없이 done 처리 (보수적 폴백) |

---

## 5. RED-first 집행 절차 (자기적용)

1. **RED (Step 1, opal-test-agent mode:red)**: S-1~S-4, S-8 테스트를 `TestMultiStepDoneGuard`에 작성 → 현재 코드에서 실행 → 실패(AssertionError, exit≠0) 출력을 RED 증거로 기록.
2. **GREEN (Step 2, opal-task-agent)**: `_parse_step` + `cmd_mark` 분기 구현 → S-1~S-4, S-8 PASS. **RED 테스트 파일 수정 금지** (red-first.md §3, `verify --fix-mode --test-globs`로 집행 가능).
3. **회귀 (Step 3)**: S-5·S-7 추가 + 전체 discover(S-6).
4. **선택적 게이트**: TEST 단계에서 `verify --red-check` ON 가능 — 단, 본 태스크 RED 증거는 unittest 실패 출력 자체로 충족(시나리오 표의 "RED 증거" 열이 SSOT). 표 형식 게이트 적용 시 "RED 증거" 헤더 열에 실패 출력 기재.

> [MUST] 어느 시나리오든 비즈니스 로직 목(mock 계열) 코드 금지 — `_mock_now()`는 date.js 부수효과 격리용 기존 픽스처로 허용(헌법 §4 "Don't fake it"의 비즈니스 로직 목과 구분). 검증 대상(status 전이)은 실제 state.json 관측으로 판정.

---

## RED 증거 (Step 1)

> 실행일: 2026-06-10 | 실행 명령: `cd opal/tools/state-tool && ~/.opal/.venv/bin/python -m unittest discover -s tests 2>&1 | tail -40`
> 총 172 테스트 실행 (기존 165 + 신규 7). 기존 165 비파괴 확인.

### 실패 테스트 목록 (exit code: 1)

| TS-ID | 테스트 메서드명 | 실패 메시지 요약 |
|-------|--------------|----------------|
| TS-001 | `TestMultiStepDoneGuard.test_step_n_lt_m_stays_in_progress` | `AssertionError: 'done' != 'in_progress' : N<M(1<7)이면 status=in_progress이어야 함, 실제: done` |
| TS-002 | `TestMultiStepDoneGuard.test_step_n_eq_m_done` | `AssertionError: None != '7/7' : state.json 행에 step=='7/7' 저장되어야 함, 실제: None` |
| TS-003 | `TestMultiStepDoneGuard.test_incomplete_step_blocks_next_stage` | `AssertionError: None != 'stage_transition_violation' : EXECUTE 행이 in_progress이면 다음 단계 mark가 stage_transition_violation으로 거부되어야 함` |
| TS-004 | `TestMultiStepDoneGuard.test_incomplete_step_blocks_close` | `AssertionError: None != 'stage_transition_violation' : EXECUTE 행이 in_progress이면 CLOSE mark가 stage_transition_violation으로 거부되어야 함` |
| TS-008 | `TestMultiStepDoneGuard.test_sequential_step_progress` | `AssertionError: 'done' != 'in_progress' : step 1/7 후 in_progress 기대, 실제: done` |

### 우연 통과 테스트 (미구현 상태에서도 PASS)

| TS-ID | 테스트 메서드명 | 사유 |
|-------|--------------|------|
| TS-005 | `TestMultiStepDoneGuard.test_no_step_backward_compat` | 현재도 --step 없는 mark=즉시 done (기존 동작 불변) |
| TS-007 | `TestMultiStepDoneGuard.test_malformed_step_falls_back` | 현재도 비정형 step=즉시 done (크래시 없음) |

### 결과 요약

```
Ran 172 tests in 0.207s
FAILED (failures=5)
```

- **exit code**: 1 (FAIL = RED 확인)
- **기존 165 비파괴**: 확인 (신규 5개만 실패)
- **RED 대상**: TS-001, TS-002, TS-003, TS-004, TS-008 (미구현으로 실패 — 정상 RED)
- **GREEN 진입 조건**: `state_tool.py`에 `_parse_step` + `cmd_mark` N<M 분기 구현 후 5개 전부 PASS

---

## 6. 완료 판정 (DoD)

- [x] S-1~S-4, S-8: RED 5 FAIL 증거 기록(§RED 증거) 후 GREEN PASS — `Ran 172 tests OK, exit 0`
- [x] S-5, S-7: 하위호환·경계 PASS (172 스위트 포함)
- [x] S-6: 전체 165+신규 7 = **172 PASS**, `test_error_codes_count`==30 유지 (신규 ERROR_CODE 0)
- [x] RED 테스트 파일 GREEN 중 미수정 (불변성 — GREEN은 `state_tool.py`만 수정, PM 직접)
- [ ] install 재배포 후 smoke 1회 정상 — **016과 일괄 후속**(캡틴 승인 후)

## 7. 판정

**All Pass — RED-first 자기적용 GREEN 실증: `python -m unittest discover -s tests` → Ran 172 tests OK, exit 0 (RED 5 FAIL → GREEN 172). 기존 165 비파괴, `test_error_codes_count`==30. ②단계전환·③CLOSE 가드는 기존 stage-transition guard 재사용(TS-003/004로 차단 실증). 작성자(RED 워커)≠구현자(GREEN PM).** install(smoke)만 016과 일괄 후속.
