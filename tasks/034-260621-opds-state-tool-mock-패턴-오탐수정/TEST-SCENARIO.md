# TEST SCENARIO: state-tool mock 가드 false positive 수정 (#1 정규식 + #2 메타-순환)

> 작성일: 2026-06-21 | 상태: 작성 완료 (범위 #1+#2 확대 재작성)
> 작성자: 알투(PM) | PLAN.md 리스크 가설 표 기반
> **RED-first 트랙: 적용** (버그 수정 = `opal/core/references/harness/red-first.md` §1.5 강제 트랙)

> **메타-태스크 자기 통과 설계 (PM Gate Rule #1 정합)**: 본 태스크의 검증 대상이 mock 패턴 검출 가드이므로 코드 토큰(`Mock()`/`@patch`/`unittest.mock` 등)을 예시로 인용해야 한다. 본 문서는 **#2 수정(인라인 백틱 인식)을 전제**로, 모든 코드 토큰 예시를 **인라인 백틱**(`` `...` ``)으로 감싸 표기한다 — #2 발효 후 `_check_mock_patterns`가 인라인 백틱 구간을 제거하고 검사하므로 본 문서는 자기 통과(exit 0)한다. **실제 입력 문자열**(bare 라인 / 코드펜스)은 `tests/test_state_tool.py`(`.py` — 가드 비검사)에 둔다. 본 문서 본문에는 인라인 백틱 밖 bare 코드 토큰도, 코드펜스 내부 실제 mock 코드도 두지 않는다. → 본 문서가 `state-tool verify`/`mark` TEST 검사를 통과하는 것 자체가 #2(메타-순환 해소)의 GREEN 증거다(자기검증).

---

## 1. 리스크 가설 표

> PLAN.md 리스크 가설 표를 TEST-SCENARIO 형식으로 정렬. H-N ↔ S-N 매핑은 §4 참조.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | `_MOCK_CODE_PATTERNS` 정규식 (`state_tool.py:1320-1322`) — #1 | 정탐 회귀 — 실제 `` `MagicMock()` `` 미검출 (헌법 §4 본질 파괴) | P0 | L1 | S-2, S-4~S-8 |
| H-2 | `_MOCK_CODE_PATTERNS` 정규식 — #1 | 오탐 잔존(산문) — 산문 MagicMock 단어 계속 검출 | P1 | L1 | S-1, S-3 |
| H-3 | `_check_mock_patterns` 인라인 백틱 전처리 (`state_tool.py:1340-1346`) — #2 | 오탐 잔존(문서 예시) — 인라인 백틱 코드 예시 계속 검출 → 메타-순환 | P0 | L1 | S-12, S-13 |
| H-4 | `_check_mock_patterns` 전처리 — #2 | 정탐 회귀(코드펜스/bare) — 전처리 과도로 실제 코드 통과 (헌법 §4 무력화) | P0 | L1 | S-2, S-4~S-8, S-14 |
| H-5 | `_check_mock_patterns` 공개 동작 — mark 훅(`:1014-1020`) / verify(`:1704-1707`) | exit code/JSON 계약 — 두 호출 지점 공유 함수 동시 영향 | P1 | L2 | S-9, S-10 |
| H-6 | 다른 5개 대안 (`` `unittest.mock` `` / `` `@patch` `` / `` `mock.patch` `` / `` `Mock()` `` / `` `@mock.` ``) | 비대상 회귀 — Surgical 위반으로 5대안 약화 | P1 | L1 | S-4~S-8 |
| H-7 | 배포 경계 (소스 ↔ `~/.opal/tools/state-tool/`) | 배포 미반영 — 런타임 배포본 오탐 잔존 | P1 | L3 | S-11 |

---

## 2. 테스트 데이터 설계

> **표기 규약**: 아래 표의 코드 토큰 예시는 모두 인라인 백틱으로 감싼다(#2 전제). 실제 입력 문자열은 `tests/test_state_tool.py` 내부에 bare/코드펜스로 둔다.

### 2.1 사전 조건 데이터

| 테이블 | 식별자 (예시 — 백틱 표기) | 상태 | 출처 |
|--------|--------------------------|------|------|
| (DB 없음 — 파일 픽스처 기반) | 산문 라인 `"- [x] mock/patch/MagicMock 등 시나리오 본문에 부재"` | RED #1 입력 (산문 오탐 대상) | 수동 fixture (op-dev-test-scenario SKILL §7 `:157` 표준 PM Gate 문구) |
| (파일 픽스처) | 인라인 백틱 예시 라인 `"대상 m=Mock() 토큰을 문서화"`를 백틱으로 감싼 형태 | RED #2 입력 (문서 예시 오탐 대상) | 수동 fixture (`.py` 내부에서 백틱 포함 문자열로 구성) |
| (파일 픽스처) | 코드 라인 `"x = MagicMock()"` (bare) | 정탐 입력 (검출되어야 함) | 수동 fixture |
| (파일 픽스처) | 5패턴 라인 (bare) `"from unittest.mock import patch"`, `"@patch('m.f')"`, `"with mock.patch('x'):"`, `"m = Mock()"`, `"@mock.patch('x')"` | 정탐 입력 (회귀) | 수동 fixture |
| (파일 픽스처) | 코드펜스 내부 `"m = Mock()"` (펜스 안 bare) | 정탐 입력 (#2 후에도 검출) | 수동 fixture (`.py` 내부 코드펜스 라인 배열) |
| (파일 픽스처) | tmp `TEST-SCENARIO.md` (산문/백틱 예시 버전 / 코드 버전) | CLI 통합 입력 | `tmp_path` (기존 `test_state_tool.py` 픽스처 패턴 미러) |
| (실 파일) | 034 자신의 `TEST-SCENARIO.md` (본 문서) | 자기검증 입력 (exit 0이어야 함) | 본 산출물 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (입력) | When (호출) | Then (관찰) |
|---------|------------|------------|------------|
| S-1 (RED #1) | 산문 라인 1줄 | `_check_mock_patterns([산문])` (정규식 수정 **전**) | 반환 `≠ []` (검출=버그) → 단언 FAIL = RED 증거 |
| S-2 (GREEN) | bare 라인 `"x = MagicMock()"` | `_check_mock_patterns` (수정 **후**) | `[1]` (검출 유지) |
| S-3 | PM Gate 표준 문구 전체 줄 (`:157`) | `_check_mock_patterns` (수정 후) | `[]` (비검출) |
| S-4 | bare `"from unittest.mock import patch"` | `_check_mock_patterns` | `[1]` 검출 유지 |
| S-5 | bare `"@patch('m.f')"` | `_check_mock_patterns` | `[1]` 검출 유지 |
| S-6 | bare `"with mock.patch('x'):"` | `_check_mock_patterns` | `[1]` 검출 유지 |
| S-7 | bare `"m = Mock()"` | `_check_mock_patterns` | `[1]` 검출 유지 |
| S-8 | bare `"@mock.patch('x')"` | `_check_mock_patterns` | `[1]` 검출 유지 |
| S-9 | tmp `TEST-SCENARIO.md` (산문·백틱 예시 / bare 코드) | `state-tool verify --task-path <tmp>` | 정당 텍스트 → exit 0; bare 코드 → exit 1 `error=mock_in_scenario` |
| S-10 | tmp `TEST-SCENARIO.md` + TEST stage 행 state.json | `state-tool mark` (TEST stage done) | 정당 텍스트 → 차단 안 됨(exit 0); bare 코드 → exit 1 `mock_in_scenario` |
| S-11 | 수정·재배포된 배포본 | `~/.opal/tools/state-tool/run.sh verify` 또는 `grep` | 배포본 #1(정규식 `MagicMock|` 없음)+#2(전처리) 반영; 034 문서 exit 0 |
| S-12 (RED→GREEN #2) | 인라인 백틱 코드 예시 라인 (`.py`에서 백틱 포함 문자열로 구성) | `_check_mock_patterns` (전처리 수정 전→후) | 수정 전: `≠ []` (검출=메타-순환 버그, RED). 수정 후: `[]` (비검출) |
| S-13 (자기검증) | 034 자신의 `TEST-SCENARIO.md` (본 문서) | `_check_mock_patterns` + `state-tool verify` (수정 후) | `_check_mock_patterns` → `[]`; `verify` → exit 0 (메타-순환 해소 증명) |
| S-14 (정탐 유지) | 코드펜스 내부 bare 코드 + 백틱·bare 동시 라인 | `_check_mock_patterns` (수정 후) | 코드펜스 내부 → 검출; 백틱+bare 동시 라인 → bare 검출 (헌법 §4 보존) |

---

## 3. 검증 시나리오

### RED 증거 (수정 전 필수 캡처 — red-first.md §1)

> [MUST] `opal/core/references/harness/red-first.md` §1: "RED 단계에서 실패 테스트 코드를 작성·실행하여 실패(exit code≠0)를 증거로 기록한 뒤 GREEN(구현) 진입. RED 증거 없이 GREEN 진입 금지."

| RED 증거 항목 | 내용 | 캡처 위치 |
|--------------|------|----------|
| RED #1 단언 | 산문 라인(`"- [x] mock/patch/MagicMock 등 ... 부재"`) → `_check_mock_patterns` 반환이 `[]`이어야 한다는 단언 (수정 전 `[1] != []` FAIL) | `tests/test_state_tool.py` 신규 케이스 (S-1) |
| RED #2 단언 | 인라인 백틱 코드 예시 라인 → `_check_mock_patterns` 반환이 `[]`이어야 한다는 단언 (수정 전 검출되어 FAIL) | `tests/test_state_tool.py` 신규 케이스 (S-12) |
| RED 기대 | 정규식·전처리 수정 **전** 두 단언 모두 **FAIL** | `2 failed, 184 deselected` — AssertionError: [1] != [] (TS-001: 산문 오탐, TS-012: 백틱 예시 오탐) |
| RED 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -k "test_mock_guard_prose_magicmock_no_false_positive or test_mock_guard_inline_backtick_example_no_false_positive" -v` | 실행 완료 — exit code 1 (2 FAILED) |

---

### L1. 기능 단위 (자동, 실 입력 — `_check_mock_patterns` 반환값 관찰)

#### S-1: 산문 MagicMock 단어 오탐 (#1) — RED→GREEN 핵심

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `_check_mock_patterns` (정규식 첫 대안 제거 후 산문 비검출) |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 입력: 산문 PM Gate 문구 라인 1줄 (`.py` 내부 문자열). 정규식 수정 전(RED)→후(GREEN) |
| 기대 결과 | 수정 전: 반환 `[1]` (검출=버그, RED FAIL). 수정 후: 반환 `[]` (비검출, GREEN PASS) |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestVerify::test_mock_guard_prose_magicmock_no_false_positive -v` |
| 결과 | **Pass** |
| 상세 | `test_mock_guard_prose_magicmock_no_false_positive PASSED` — 산문 PM Gate 문구("- [x] mock/patch/MagicMock 등 시나리오 본문에 부재") 입력 시 `_check_mock_patterns` 반환 `[]` 확인. 수정 전 RED: `[1] != []` FAIL 기록 완료(§3 RED 증거 표). 수정 후 GREEN: 1 passed (exit 0). |

#### S-2: 실제 `` `MagicMock()` `` 정탐 유지

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-4 |
| 대상 | `_check_mock_patterns` — bare `` `MagicMock()` `` 코드는 `` `Mock(` `` 대안으로 계속 검출 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 입력: bare 코드 라인 (`.py` 내부 문자열). 정규식 수정 후 |
| 기대 결과 | 반환 `[1]` (검출 유지). 가드 본질(헌법 §4) 보존 입증 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestVerify::test_mock_guard_real_magicmock_call_detected -v` |
| 결과 | **Pass** |
| 상세 | `test_mock_guard_real_magicmock_call_detected PASSED` — bare 코드 라인 `"svc = MagicMock()"` 입력 시 `_check_mock_patterns` 반환 `[1]` 확인. `Mock(` 대안이 `MagicMock()` 호출을 여전히 커버 — 가드 본질(헌법 §4) 보존 입증. |

#### S-3: PM Gate 표준 문구 비검출

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `_check_mock_patterns` — op-dev-test-scenario SKILL §7 `:157` 표준 PM Gate 문구 전체 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 입력: SKILL §7 `:157` 원문 줄 (`.py` 내부 문자열) |
| 기대 결과 | 반환 `[]` (비검출). opd/opds 전 태스크 산문 차단 해소 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestVerify::test_mock_guard_pm_gate_standard_phrase -v` |
| 결과 | **Pass** |
| 상세 | `test_mock_guard_pm_gate_standard_phrase PASSED` — SKILL §7 `:157` 표준 PM Gate 문구 전체 입력 시 `_check_mock_patterns` 반환 `[]` 확인. opd/opds 모든 태스크의 PM Gate 체크박스 라인 오탐 차단 해소 입증. |

#### S-4 ~ S-8: 5개 코드 패턴 회귀 (bare 라인, 검출 유지)

| 시나리오 | 가설 | 입력 (bare, `.py` 내부 문자열) | 기대 (반환) | 실행 방식 | 결과 |
|---------|------|------------------------------|------------|----------|------|
| S-4 | H-6 | `` `from unittest.mock import patch` `` 형태 | `[1]` 검출 | M1 (pytest) | **Pass** — `test_mock_guard_unittest_mock_detected PASSED` (1 passed) |
| S-5 | H-6 | `` `@patch('m.f')` `` 형태 | `[1]` 검출 | M1 (pytest) | **Pass** — `test_mock_guard_at_patch_detected PASSED` (1 passed) |
| S-6 | H-6 | `` `with mock.patch('x'):` `` 형태 | `[1]` 검출 | M1 (pytest) | **Pass** — `test_mock_guard_mock_patch_detected PASSED` (1 passed) |
| S-7 | H-6 | `` `m = Mock()` `` 형태 | `[1]` 검출 | M1 (pytest) | **Pass** — `test_mock_guard_mock_call_detected PASSED` (1 passed) |
| S-8 | H-6 | `` `@mock.patch('x')` `` 형태 | `[1]` 검출 | M1 (pytest) | **Pass** — `test_mock_guard_at_mock_dot_detected PASSED` (1 passed) |

> 실행 명령: `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -k "test_mock_guard_unittest_mock_detected or test_mock_guard_at_patch_detected or test_mock_guard_mock_patch_detected or test_mock_guard_mock_call_detected or test_mock_guard_at_mock_dot_detected" -v` → `5 passed, 192 deselected` (exit 0)

> 각 S-4~S-8은 계층 L1 / 실행 방식 M1 / 대상 `_check_mock_patterns` 반환값. 입력은 `.py` 내부에 **bare 라인**으로 둔다. 기존 `test_verify_detects_*`(`test_state_tool.py:1809-1840`)와 중복 회피 — 반환값 레벨 정탐으로 보강하고 미커버(`mock.patch`/`Mock()`/`@mock.`) 신규.

#### S-12: 인라인 백틱 코드 예시 오탐 (#2) — RED→GREEN 핵심

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `_check_mock_patterns` 인라인 백틱 제거 전처리 — 문서화용 백틱 코드 예시 비검출 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | 입력: 인라인 백틱으로 감싼 코드 토큰을 포함한 라인 (`.py` 내부에서 백틱 포함 문자열로 구성, 예: 설명문 + `` `m = Mock()` `` 백틱 구간). 전처리 수정 전(RED)→후(GREEN) |
| 기대 결과 | 수정 전: 반환 `≠ []` (백틱 구간 내부까지 매칭=메타-순환 버그, RED FAIL). 수정 후: 반환 `[]` (백틱 구간 제거 후 비검출, GREEN PASS) |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestVerify::test_mock_guard_inline_backtick_example_no_false_positive -v` |
| 결과 | **Pass** |
| 상세 | `test_mock_guard_inline_backtick_example_no_false_positive PASSED` — 인라인 백틱 구간(`` `m = Mock()` ``, `` `MagicMock()` `` 등)을 포함한 설명 라인 입력 시 `_check_mock_patterns` 반환 `[]` 확인. 수정 전 RED: `≠ []` FAIL 기록 완료(§3 RED #2 증거). 수정 후 GREEN: 1 passed (exit 0). 메타-순환 해소 핵심 증거. |

#### S-14: 코드펜스/혼합 라인 정탐 유지 (헌법 §4 — 전처리 과도 방지)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `_check_mock_patterns` — 코드펜스 내부 + 인라인 백틱과 bare가 같은 줄에 공존 시 정탐 |
| 계층 | L1 |
| **실행 방식** | **M1 (pytest)** |
| 조건 | (a) 코드펜스(```` ``` ````) 내부에 bare mock 코드 라인 배열 (`.py` 내부 라인 리스트). (b) 같은 줄에 백틱 예시 + 백틱 밖 bare 코드 토큰이 공존하는 라인 |
| 기대 결과 | (a) 코드펜스 내부 라인 검출(`[N]`). (b) 백틱 밖 bare 토큰 검출(라인 포함). "목업 때우기 코드"는 계속 차단 |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestVerify::test_mock_guard_codefence_and_mixed_line_detected -v` |
| 결과 | **Pass** |
| 상세 | `test_mock_guard_codefence_and_mixed_line_detected PASSED` — (a) 코드펜스 내부 bare mock 코드 라인: 검출(`[N]`) 확인. (b) 같은 줄에 인라인 백틱 예시 + 백틱 밖 bare 코드 공존: bare 토큰 검출 확인. 전처리 과도로 정탐이 우회되지 않음 — 헌법 §4 "Don't fake it" 유지 입증. |

### L2. 프로세스 통합 (자동, CLI exit code/JSON 관찰)

#### S-9: `verify --check` 통합 (양 호출 지점 정합)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `cmd_verify` — 실 tmp `TEST-SCENARIO.md` 파일 + 실 CLI 호출 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest, `cmd_verify` 직접 호출 + `redirect_stdout` — 기존 `_call_verify` 패턴 미러)** |
| 조건 | (a) 산문 + 인라인 백틱 코드 예시만 포함한 TEST-SCENARIO.md (b) bare 코드(`` `svc = MagicMock()` `` 형태를 bare로) 포함 버전 |
| 기대 결과 | (a) exit 0, `ok=True`, `checks.mock_in_scenario="pass"`. (b) exit 1, `error="mock_in_scenario"` |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestVerify::test_verify_no_false_positive_doc_example -v` |
| 결과 | **Pass** |
| 상세 | `test_verify_no_false_positive_doc_example PASSED` — (a) 산문+인라인 백틱 코드 예시만 포함한 tmp TEST-SCENARIO.md: `cmd_verify` exit 0, `ok=True`, `checks.mock_in_scenario="pass"` 확인. (b) bare 코드 포함 버전: exit 1, `error="mock_in_scenario"` 확인. 양 호출 지점(verify) 정합 입증. |

#### S-10: `mark` TEST stage 자동 훅 통합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `cmd_mark` TEST stage done 훅 (`state_tool.py:1014-1020`) — 동일 함수 공유 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest, 실 state.json init + 실 TEST-SCENARIO.md + 실 mark 호출 — 기존 `test_mark_test_stage_mock_in_scenario_blocks` 패턴 미러)** |
| 조건 | TEST stage 행 + (a) 산문·백틱 예시 TEST-SCENARIO.md (b) bare 코드 포함 버전 |
| 기대 결과 | (a) mark 성공 exit 0 (오탐 차단 없음). (b) exit 1 `error="mock_in_scenario"` (정탐 차단 유지) |
| 도구 | pytest |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestVerify::test_mark_test_stage_doc_example_not_blocked -v` |
| 결과 | **Pass** |
| 상세 | `test_mark_test_stage_doc_example_not_blocked PASSED` — TEST stage 행 + (a) 산문·백틱 예시 TEST-SCENARIO.md: `cmd_mark` exit 0 (오탐 차단 없음) 확인. (b) bare 코드 포함 버전: exit 1, `error="mock_in_scenario"` (정탐 차단 유지) 확인. mark 훅(`state_tool.py:1014-1020`) 정합 입증. |

### L3. 사용자 협업 / 배포 검증

#### S-11: install 재배포 후 배포본 발효 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | 배포본 `~/.opal/tools/state-tool/state_tool.py` #1+#2 반영 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업) — M2 자동화 병기: `./scripts/install-mac.sh` 실행 후 `grep` 으로 배포본 정규식(`MagicMock|` 부재) 확인 + 배포본 `verify`로 034 문서 exit 0** |
| 조건 | 소스 수정·전체 pytest 통과 후 install 재배포 |
| 기대 결과 | 배포본 정규식에 `MagicMock|` 대안 부재 + `_check_mock_patterns` 인라인 백틱 전처리 반영. 배포본 `verify`로 034 TEST-SCENARIO.md → exit 0. [MUST] 배포본 직접 수정 금지 |
| 실행자 | [SUPERVISOR] — 캡틴이 재배포 실행·확인 |
| 결과 | 캡틴 확인 대기 |
| 상세 | 캡틴 확인 대기 — `./scripts/install-mac.sh` 실행 권한은 캡틴(사용자) 전용. 소스 기준 pytest 197 passed 완료 후 배포 승인 요청. |

#### S-13: 034 자기 TEST-SCENARIO.md 통과 (메타-순환 해소 증명)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | 본 문서(034 `TEST-SCENARIO.md`) 자신이 `_check_mock_patterns` / `verify` TEST 검사를 통과 |
| 계층 | L2 |
| **실행 방식** | **M1 (pytest, 본 문서를 픽스처로 복사 후 `cmd_verify` 호출) — M2 병기: `state-tool verify --scenario <본 문서>`** |
| 조건 | #1+#2 수정 후. 입력: 034 자신의 TEST-SCENARIO.md 전체 |
| 기대 결과 | `_check_mock_patterns(본문서.splitlines())` → `[]`; `verify` exit 0, `mock_in_scenario="pass"`. 메타-순환(가드를 검증하는 문서가 가드에 막힘) 해소 증명 |
| 도구 | pytest / state-tool CLI |
| 실행 명령 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py::TestVerify::test_verify_passes_own_test_scenario_md -v` |
| 결과 | **Pass** |
| 상세 | `test_verify_passes_own_test_scenario_md PASSED` — 034 자신의 TEST-SCENARIO.md(본 문서)를 픽스처로 복사 후 `cmd_verify` 호출 결과: exit 0, `mock_in_scenario="pass"` 확인. `_check_mock_patterns(본문서.splitlines())` → `[]` 입증. 메타-순환(가드를 검증하는 문서가 가드에 막히는 문제) 해소 완전 증명. |

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-2 AC (RED #1) | H-2 | L1 | S-1 | `tests/test_state_tool.py`:`test_mock_guard_prose_magicmock_no_false_positive` | 수정 전 FAIL = RED 증거 |
| R-1 AC (정탐) | H-1 | L1 | S-2 | `tests/test_state_tool.py`:`test_mock_guard_real_magicmock_call_detected` | `` `Mock(` `` 가 `` `MagicMock()` `` 커버 |
| R-1 AC (PM Gate 문구) | H-2 | L1 | S-3 | `tests/test_state_tool.py`:`test_mock_guard_pm_gate_standard_phrase` | SKILL §7 `:157` 원문 |
| R-2 AC (c) 회귀 | H-6 | L1 | S-4 | `tests/test_state_tool.py`:`test_mock_guard_unittest_mock_detected` | |
| R-2 AC (c) 회귀 | H-6 | L1 | S-5 | `tests/test_state_tool.py`:`test_mock_guard_at_patch_detected` | |
| R-2 AC (c) 회귀 | H-6 | L1 | S-6 | `tests/test_state_tool.py`:`test_mock_guard_mock_patch_detected` | |
| R-2 AC (c) 회귀 | H-6 | L1 | S-7 | `tests/test_state_tool.py`:`test_mock_guard_mock_call_detected` | |
| R-2 AC (c) 회귀 | H-6 | L1 | S-8 | `tests/test_state_tool.py`:`test_mock_guard_at_mock_dot_detected` | |
| R-1/R-3 AC (verify) | H-5 | L2 | S-9 | `tests/test_state_tool.py`:`test_verify_no_false_positive_doc_example` | 기존 `_call_verify` 미러 |
| R-1/R-3 AC (mark 훅) | H-5 | L2 | S-10 | `tests/test_state_tool.py`:`test_mark_test_stage_doc_example_not_blocked` | 기존 mark 훅 테스트 미러 |
| 배포 발효 | H-7 | L3 | S-11 | (수동) `install-mac.sh` + grep/verify | [SUPERVISOR] |
| R-3 AC (RED→GREEN #2) | H-3 | L1 | S-12 | `tests/test_state_tool.py`:`test_mock_guard_inline_backtick_example_no_false_positive` | 수정 전 FAIL = RED #2 증거 |
| R-3 AC (자기검증) | H-3 | L2 | S-13 | `tests/test_state_tool.py`:`test_verify_passes_own_test_scenario_md` | 034 본 문서 픽스처 |
| R-3 AC (정탐 유지) | H-4 | L1 | S-14 | `tests/test_state_tool.py`:`test_mock_guard_codefence_and_mixed_line_detected` | 코드펜스/혼합 라인 |

---

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | `python3 -m py_compile` | **Pass** | `state_tool.py` + `test_state_tool.py` 모두 `SYNTAX OK`. stdlib `re`만 사용, 외부 의존 없음. flake8/ruff 미설치 환경이므로 문법 검사로 대체(불가 사유 명시). |
| 2 | 타입 체크 | 정적 분석(수동) | **Pass** | `_check_mock_patterns(lines: list) -> list[int]` 시그니처·반환 계약 불변. `re.sub` 반환 `str`, `_MOCK_CODE_PATTERNS.search(target)` 호출 계약 동일. mypy 미설치 환경 — 정적 판단으로 대체(불가 사유 명시). |
| 3 | 포맷터 | 정적 분석(수동) | **Pass** | diff 22줄 추가/5줄 제거. 들여쓰기 4-space 일관, 주석 스타일 기존 파일과 동일. black/ruff-format 미설치 환경 — 시각 검사로 대체(불가 사유 명시). |
| 4 | diff 범위 검사 | `git diff HEAD~1` | **Pass (Surgical)** | 변경 hunk 3개: (1) description 필드 1줄 갱신, (2) `_MOCK_CODE_PATTERNS` 정규식 1줄(`MagicMock|` 대안 제거 — #1), (3) `_check_mock_patterns` 함수 루프 전처리 추가(#2). 총 22줄 추가/5줄 제거. 다른 함수/로직 미접촉 — Surgical 기준 완전 충족. |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | **Pass** | `grep -n "password\|secret\|api_key\|token\|credential\|AWS_\|private_key"` 결과 0건(정규식·테스트 문자열만 존재). 신규 추가 라인에 시크릿 패턴 없음. |
| 2 | .gitignore 확인 | **Pass** | `git status --short opal/tools/state-tool/` → 기존 `state_tool.py`, `test_state_tool.py` 수정만. 신규 파일 없음. `.gitignore`에 `*.py[cod]`, `__pycache__/` 커버 확인. |
| 3 | ReDoS 위험 | **Pass** | `_MOCK_CODE_PATTERNS`: 대안 제거(단순화). `re.sub(r"\`[^\`]*\`", "", line)`: `[^` `` ` `` `]*` 부정 문자셋은 선형 복잡도, 중첩 한정사 없음. `python3 -c "import re; re.compile(..."` 컴파일 OK 확인. 백트래킹 폭발 위험 없음. |
| 4 | 가드 본질 무력화 여부 | **Pass** | S-2(MagicMock 정탐), S-4~S-8(5개 코드 패턴 회귀), S-14(코드펜스/혼합 라인) 모두 Pass — 헌법 §4 "Don't fake it" mock 차단 완전 유지. `--force` 우회 미도입. 인라인 백틱 제거 전처리가 코드펜스 내부·bare 코드는 그대로 통과시켜 가드 무력화 없음. |

## 7. 판정

**All Pass** — 소스 기준 pytest 197 passed / 0 failed (exit 0). S-1~S-10·S-12~S-14 모두 Pass. S-11은 [SUPERVISOR] 캡틴 확인 대기(배포 미실행 — 소스 기준 테스트 완료). 코드 품질 4종 Pass. 보안 4종 Pass.

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 — **본 문서는 #2(인라인 백틱 인식) 발효 후 자기 통과 설계**: 모든 코드 토큰 예시를 인라인 백틱으로 감싸 표기하고 bare 코드·코드펜스 실제 mock 코드를 본문에 두지 않음. 실제 입력 문자열은 `tests/test_state_tool.py`(`.py`)에 격리. → `verify`/`mark` exit 0 (S-13 자기검증 Pass)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 (S-11)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전 (H-1~H-7 ↔ S-1~S-14)
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] **RED-first 적용**: RED 증거(§3 RED 증거 표 — #1·#2 각각) 캡처 후 GREEN 진입 (red-first.md §1)
