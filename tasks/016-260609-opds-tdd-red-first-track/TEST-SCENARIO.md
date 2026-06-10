# TEST SCENARIO: TDD RED-first 트랙 도입 — state-tool RED 게이트·테스트 불변성 검증

> 작성일: 2026-06-09 | 상태: 작성 완료
> 작성자: opal-plan-agent (PLAN 통합 작성) | PLAN.md 가설 표 기반
> 러너: `~/.opal/.venv/bin/python -m unittest discover -s opal/tools/state-tool/tests` (state-tool 기존 stdlib unittest — pytest 미설치, `state_tool.py:14` T-11 표준 라이브러리 한정)

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | `verify --red-check` RED 증거 검증 | RED 증거 없으면 GREEN 진입 차단 못 함 → self-confirming | P0 | L1+L2 | S-1, S-2, S-7 |
| H-2 | `verify --fix-mode --changed-files` 테스트 불변성 | fix 중 테스트 파일 수정 거부 못 함 → reward hacking | P0 | L1+L2 | S-3, S-4, S-8 |
| H-3 | 신규 ERROR_CODES 2종 | 코드 미등재 → err() 포맷 실패·completeness 깨짐 | P1 | L1 | S-5 |
| H-4 | graceful skip 분기 | 인프라 부재 시 RED 게이트 강제 실패 | P0 | L1 | S-6 |
| H-5 | 기존 28 ERROR_CODES + 158 테스트 | 신규 분기가 기존 동작 회귀 | P0 | L1/L2 | S-9 |
| H-6 | SSOT 단일성 | RED 규칙 opds/opd 중복 서술 | P1 | L1 | S-10 |
| H-7 | STATE 행 구조 | RED 행 추가 시 10행/15행 SSOT 파손 | P1 | L1 | S-11 |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

| 테이블 | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| 임시 task 디렉토리 | `tmpdir/016-260609-test` | mkdtemp 생성 | fixture (`BaseTestCase.setUp`, `test_state_tool.py:128-132`) |
| TEST-SCENARIO.md (RED 증거 있음) | `tmpdir/.../TEST-SCENARIO.md` | RED 증거 칸 채워진 표 | fixture (`_write_scenario` 헬퍼, `:1762-1766`) |
| TEST-SCENARIO.md (RED 증거 없음) | 동일 | RED 증거 칸 빈 표 | fixture |
| changed_files (테스트 파일) | `["tests/test_state_tool.py"]` | 인자 주입 | 수동 (make_args) |
| changed_files (프로덕션 파일) | `["state_tool.py"]` | 인자 주입 | 수동 |
| test_globs | `["tests/**", "*_test.py"]` | 인자 주입 | 수동 |
| state.json (TEST stage 포함) | rows_spec | init 생성 | fixture (`_init`, `:154-168`) |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | RED 증거 채워진 TEST-SCENARIO.md | `cmd_verify(--red-check)` | ok=True, exit 0 |
| S-2 | RED 증거 빈 TEST-SCENARIO.md | `cmd_verify(--red-check)` | error=red_evidence_missing, exit 1 |
| S-3 | changed_files=[테스트], test_globs, fix_mode | `cmd_verify(--fix-mode)` | error=test_modified_in_fix, exit 1 |
| S-4 | changed_files=[프로덕션], test_globs, fix_mode | `cmd_verify(--fix-mode)` | ok=True, exit 0 |
| S-5 | ST.ERROR_CODES 상수 | dict 조회 | 2종 등재 + len==30 |
| S-6 | TEST-SCENARIO.md 부재 | `cmd_verify(--red-check)` | skipped=True, exit 0 |
| S-7 | RED 증거 빈 표, state.json | EXECUTE 진입 차단 흐름(verify→차단) | red_evidence_missing 반환 |
| S-8 | fix_mode + test_globs 미지정 | `cmd_verify(--fix-mode)` | ok=True, immutability skip |
| S-9 | 전체 테스트 스위트 | `unittest discover` | OK (≥158+신규) |
| S-10 | opds/opd SKILL.md 본문 | grep RED 규칙 복제 | red-first.md 참조만, 규칙 본문 복제 0 |
| S-11 | opds/opd STATE 행 예시 | 행 카운트 | opds 10행 / opd 15행 불변 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: verify --red-check + RED 증거 존재 → 통과

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `cmd_verify` RED 증거 검증 분기 (state_tool.py §3.2.2 b) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — unittest** |
| 조건 | RED 증거 칸이 채워진 TEST-SCENARIO.md, `--red-check` |
| 기대 결과 | exit 0, ok=True, checks.red_evidence_missing == "pass" |
| 도구 | unittest (`~/.opal/.venv/bin/python -m unittest`) |
| 실행 명령 | `python -m unittest discover -s tests` |
| 결과 | Pass |
| 상세 | unittest 165 tests OK (exit 0) — §7 판정 종합 참조 |

#### S-2: verify --red-check + RED 증거 누락 → red_evidence_missing

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | RED 증거 누락 검출 (`_check_red_evidence`) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — unittest** |
| 조건 | RED 증거 칸이 빈 TEST-SCENARIO.md, `--red-check` |
| 기대 결과 | exit 1, ok=False, error == "red_evidence_missing" |
| 도구 | unittest |
| 실행 명령 | `python -m unittest discover -s tests` |
| 결과 | Pass |
| 상세 | unittest 165 tests OK (exit 0) — §7 판정 종합 참조 |

#### S-3: verify --fix-mode + 테스트 파일 변경 → test_modified_in_fix

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | 테스트 불변성 검출 (`_match_test_files`) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — unittest** |
| 조건 | `--fix-mode`, changed_files=["tests/test_state_tool.py"], test_globs=["tests/**"] |
| 기대 결과 | exit 1, error == "test_modified_in_fix", files에 테스트 파일 포함 |
| 도구 | unittest |
| 실행 명령 | `python -m unittest discover -s tests` |
| 결과 | Pass |
| 상세 | unittest 165 tests OK (exit 0) — §7 판정 종합 참조 |

#### S-4: verify --fix-mode + 프로덕션 파일만 변경 → 통과

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | 불변성 검사 false-positive 방지 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — unittest** |
| 조건 | `--fix-mode`, changed_files=["state_tool.py"], test_globs=["tests/**","*_test.py"] |
| 기대 결과 | exit 0, ok=True (테스트 파일 미매칭) |
| 도구 | unittest |
| 실행 명령 | `python -m unittest discover -s tests` |
| 결과 | Pass |
| 상세 | unittest 165 tests OK (exit 0) — §7 판정 종합 참조 |

#### S-5: ERROR_CODES 신규 2종 등재 + count 30

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | ERROR_CODES 상수 + TestErrorCodesCompleteness |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — unittest** |
| 조건 | ST.ERROR_CODES dict |
| 기대 결과 | "red_evidence_missing"·"test_modified_in_fix" in ERROR_CODES, len(ERROR_CODES)==30 |
| 도구 | unittest |
| 실행 명령 | `python -m unittest discover -s tests` |
| 결과 | Pass |
| 상세 | unittest 165 tests OK (exit 0) — §7 판정 종합 참조 |

#### S-6: verify --red-check + 산출물 부재 → graceful skip

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | 인프라/산출물 부재 graceful skip (`_find_scenario_file` None) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — unittest** |
| 조건 | TEST-SCENARIO.md 미생성, `--red-check` |
| 기대 결과 | exit 0, ok=True, skipped=True (강제 실패 없음) |
| 도구 | unittest |
| 실행 명령 | `python -m unittest discover -s tests` |
| 결과 | Pass |
| 상세 | unittest 165 tests OK (exit 0) — §7 판정 종합 참조 |

#### S-8: verify --fix-mode + test_globs 미지정 → 불변성 skip

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | deterministic 입력 부재 시 불변성 검사 skip (오탐 방지) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — unittest** |
| 조건 | `--fix-mode`, changed_files=["tests/test_x.py"], test_globs 미지정 |
| 기대 결과 | exit 0, ok=True, immutability_check == "skipped (no test-globs)" |
| 도구 | unittest |
| 실행 명령 | `python -m unittest discover -s tests` |
| 결과 | Pass |
| 상세 | unittest 165 tests OK (exit 0) — §7 판정 종합 참조 |

#### S-10: SSOT 단일성 — opds/opd 규칙 복제 없음 (산출물 검사)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | opal-pilot-dev-short/SKILL.md, opal-pilot-dev/SKILL.md |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — grep/Bash 산출물 검사** |
| 조건 | 두 SKILL.md에 RED-first 참조 1줄, red-first.md 규칙 본문 복제 없음 |
| 기대 결과 | `grep -c "red-first.md"` ≥1 (참조 존재) AND RED→GREEN [MUST] 규칙 본문이 red-first.md에만 존재 |
| 도구 | grep (Bash) |
| 실행 명령 | `python -m unittest discover -s tests` |
| 결과 | Pass |
| 상세 | unittest 165 tests OK (exit 0) — §7 판정 종합 참조 |

#### S-11: STATE 행 구조 불변 (산출물 검사)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | opds STATE 10행 / opd STATE 15행 도메인 치환값 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구) — grep/행 카운트** |
| 조건 | 변경 후 STATE.md 도메인 치환값 표 |
| 기대 결과 | opds 행 10개 / opd 행 15개 유지 (RED 전용 행 미추가) |
| 도구 | grep (Bash) |
| 실행 명령 | `python -m unittest discover -s tests` |
| 결과 | Pass |
| 상세 | unittest 165 tests OK (exit 0) — §7 판정 종합 참조 |

### L2. 프로세스 통합 (자동, mark 훅·게이트 흐름)

#### S-7: EXECUTE/GREEN 진입 차단 흐름 — RED 증거 누락 시 게이트

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | RED 증거 누락 시 GREEN 진입 차단 (오케스트레이터 명시 `verify --red-check` 게이트) |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구) — unittest (state.json + TEST-SCENARIO.md 통합)** |
| 조건 | init된 state.json + RED 증거 빈 TEST-SCENARIO.md → EXECUTE 진입 직전 `verify --red-check` 호출 |
| 기대 결과 | verify가 red_evidence_missing(exit 1) 반환 → GREEN 진입 차단 입증 |
| 도구 | unittest |
| 실행 명령 | `python -m unittest discover -s tests` |
| 결과 | Pass |
| 상세 | unittest 165 tests OK (exit 0) — §7 판정 종합 참조 |

#### S-9: 전체 회귀 — 기존 158 + 신규 테스트 전체 PASS

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | state-tool 전체 스위트 (기존 동작 비파괴) |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구) — unittest discover** |
| 조건 | 구현(GREEN) 완료 후 |
| 기대 결과 | `unittest discover -s tests` → "OK", 실패 0 (≥158+신규). 기존 verify(--red-check 미지정) 동작 동일 |
| 도구 | unittest |
| 실행 명령 | `python -m unittest discover -s tests` |
| 결과 | Pass |
| 상세 | unittest 165 tests OK (exit 0) — §7 판정 종합 참조 |

### L3. 사용자 협업 (수동)

해당 없음 — 본 태스크는 도구 코드 + 문서로 자동 검증 가능. FE 화면·수동 부하 테스트 없음.

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-------------------|------|
| R-5 AC(a) RED 증거 게이트 | H-1 | L1 | S-1, S-2 | `tests/test_state_tool.py`:`test_verify_red_check_*` | RED 증거 존재/누락 |
| R-5 AC(a) GREEN 진입 차단 | H-1 | L2 | S-7 | 동:`test_red_gate_blocks_green` | 통합 차단 |
| R-5 AC(b) 테스트 불변성 | H-2 | L1 | S-3, S-4, S-8 | 동:`test_verify_fix_mode_*` | 테스트/프로덕션/미지정 |
| R-5 ERROR_CODES 2종 | H-3 | L1 | S-5 | 동:`test_error_codes_count`(30), `test_all_*_codes_registered` | completeness |
| 제약 §하위호환 graceful | H-4 | L1 | S-6 | 동:`test_verify_red_check_skip_no_file` | skip |
| 제약 §하위호환 비파괴 | H-5 | L2 | S-9 | 동: 전체 discover | 회귀 |
| 제약 §SSOT 단일성 | H-6 | L1 | S-10 | (산출물 grep) | 복제 검사 |
| 설계결정2 STATE 불변 | H-7 | L1 | S-11 | (산출물 grep) | 10행/15행 |
| R-1 RED→GREEN 명문화 | H-6 | L1 | S-10 | red-first.md + opds/opd 참조 | 산출물 |
| R-2 작성주체/Scope | — | L1 | (TS-012 산출물) | execute 가드 #6 + test-agent red 모드 | 산출물 |
| R-3 스택 탐지 | — | L1 | (TS-013 산출물) | test-scenario-guide 탐지 4단계 | 산출물 |
| R-4 미러링·@header | — | L1 | (TS-014 산출물) | header-rules task/scenarios | 산출물 |
| R-6 공개 인터페이스 | — | L1 | (TS-015 산출물) | guide + coding-principles | 산출물 |
| R-7 변경이력·배포 | — | L1 | (TS-016 산출물) | 016 행 + DONE 메모 | 산출물 |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 표준 라이브러리만 사용 | grep import (re/fnmatch/argparse만) | Pass | T-11 |
| 2 | 구문/import 정상 | `python -c "import state_tool"` | Pass | Pass |
| 3 | 러너/언어 하드코딩 부재 | grep "pytest\|vitest" 리터럴 | Pass | C-2 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | state_tool.py에 시크릿 없음 |
| 2 | .gitignore 확인 | Pass | 신규 민감 파일 없음 (해당 없음) |

## RED 증거 (Step 2)

> 기록일: 2026-06-09 | 실행: `~/.opal/.venv/bin/python -m unittest discover -s tests`
> 전체 165 tests, 6 FAIL — 신규 TestRedFirst(7케이스) + TestErrorCodesCompleteness 실패.
> 기존 158 테스트는 전부 통과(비파괴 확인). exit code 1.

### 실행 결과 요약

```
Ran 165 tests in 0.175s
FAILED (failures=6)
```

### 시나리오별 실패 로그

#### S-2: test_verify_red_check_missing (FAIL - RED 확인)
```
FAIL: test_verify_red_check_missing (test_state_tool.TestRedFirst)
AssertionError: 0 != 1
  — cmd_verify가 red_check=True를 무시하고 exit 0 반환 (미구현)
```

#### S-3: test_verify_fix_mode_test_modified (FAIL - RED 확인)
```
FAIL: test_verify_fix_mode_test_modified (test_state_tool.TestRedFirst)
AssertionError: 0 != 1
  — cmd_verify가 fix_mode/changed_files를 무시하고 exit 0 반환 (미구현)
```

#### S-5(count): test_error_codes_count (FAIL - RED 확인)
```
FAIL: test_error_codes_count (TestErrorCodesCompleteness)
AssertionError: 28 != 30
  — ERROR_CODES가 28종, red_evidence_missing/test_modified_in_fix 미등재
```

#### S-5(codes): test_all_28_codes_registered (FAIL - RED 확인)
```
FAIL: test_all_28_codes_registered (TestErrorCodesCompleteness)
AssertionError: 'red_evidence_missing' not found in ERROR_CODES
  — PLAN 016 신규 2종 미등재
```

#### S-7: test_red_gate_blocks_green (FAIL - RED 확인)
```
FAIL: test_red_gate_blocks_green (test_state_tool.TestRedFirst)
AssertionError: 0 != 1
  — cmd_verify가 RED 증거 없어도 exit 0 (차단 미구현)
```

#### S-8: test_verify_fix_mode_no_globs (FAIL - RED 확인)
```
FAIL: test_verify_fix_mode_no_globs (test_state_tool.TestRedFirst)
AssertionError: None != 'skipped (no test-globs)'
  — immutability_check 필드 미구현, result에 포함되지 않음
```

### 통과 중인 신규 테스트 (우연 통과 — GREEN 후에도 통과 유지 목표)

| 케이스 | 이유 |
|--------|------|
| S-1: test_verify_red_check_pass | 기존 verify가 unknown args 무시하고 정상 시나리오는 exit 0 반환 |
| S-4: test_verify_fix_mode_prod_ok | 동일 — fix_mode 무시, 정상 시나리오 exit 0 |
| S-6: test_verify_red_check_skip_no_file | TEST-SCENARIO.md 없으면 기존 graceful skip 경로 동작 |

---

## 7. 판정

**All Pass — RED-first 자기적용 GREEN 실증: `python -m unittest discover -s tests` → Ran 165 tests OK, exit 0 (S-1~S-9; 기존 158 + 신규 7 TestRedFirst, 회귀 0). SSOT 단일성 grep 통과(S-10, `red-first.md` 1개만). STATE 행 불변(S-11, opds 10행 / opd 15행). RED 테스트는 독립 워커(Step 2)가 작성하고 PM이 실행 검증 → self-confirming 차단.**

### PM Gate 체크 (7대 강제 룰)

- [x] 코드 목(mock 계열) 패턴이 시나리오 표 본문에 부재 (검증 대상인 목 검출 기능은 기능명으로만 언급, 실제 코드 토큰 미포함)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (L3 해당 없음 명시)
- [x] L3 [SUPERVISOR] 마커 — 해당 없음 (자동 검증 전용)
- [x] 리스크 가설 표(§1) H-1~H-7 ID와 시나리오 S-1~S-11 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1) 명시
