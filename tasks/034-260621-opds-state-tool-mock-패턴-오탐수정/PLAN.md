# PLAN: state-tool mock 가드 false positive 수정 (#1 정규식 + #2 메타-순환)

> 작성일: 2026-06-21 | 입력: TASK.md (R-3 추가, 범위 #1+#2 확대) | ANALYSIS.md 없음 → 코드 직접 분석
> 모드: Multi-Feature (F-001 정규식 / F-002 메타-순환) | 실행 모드: 단순

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`state_tool.py`의 mock 코드 검출 가드(`_MOCK_CODE_PATTERNS` + `_check_mock_patterns`)가 **정당한 텍스트**(산문 단어 / 문서화용 인라인 백틱 코드 예시 / 표 셀)를 실제 mock 코드로 오탐하는 두 층위의 버그를 근본 수정한다. **#1(F-001)**: 정규식 첫 대안 `MagicMock`(맨 단어)이 점·괄호·@ 없이 어디서든 매칭되어 산문(예: op-dev-test-scenario SKILL §7 PM Gate 표준 문구 `"mock/patch/MagicMock 등 시나리오 본문에 부재"`)을 오탐한다. **#2(F-002)**: #1을 고쳐도 나머지 5개 코드형 대안(`unittest\.mock`/`@patch\b`/`mock\.patch`/`Mock\(`/`@mock\.`)이 **문서화용 인라인 백틱 코드 예시**(`` `m = Mock()` ``, `` `@patch('m.f')` `` 등)를 라인 단위 스캔에서 그대로 매칭하여, mock 가드 자체를 검증·문서화하는 태스크(034 포함)의 TEST 단계가 구조적으로 막히는 **메타-순환**이 발생한다(PM 실측: 034 TEST-SCENARIO.md 현 상태에서 #1 적용 후에도 raw 스캔 22건 매칭 — §2.2(e) 입증). **실제 mock으로 구현을 때우는 코드 검출 능력(헌법 §4 "Don't fake it")은 유지**하고, 산문·문서 예시 오탐만 제거한다.

[MUST] `opal/core/PRINCIPLES.md` §4: "Don't fake it: never substitute a mock for a real integration you were asked to build. If you can't build it, return BLOCKED — do not declare done." → 본 수정은 시나리오 본문에 **실제 mock 코드**(코드펜스 내부 또는 인라인 백틱 밖의 bare 라인)를 두는 행위 차단을 **유지**한다. 인라인 백틱(`` `...` `` — 문서화/예시 표기)으로 감싼 코드 토큰 언급만 통과시킨다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | mock 가드 정규식 오탐 제거 (`MagicMock` 맨 단어 제거) | R-1, R-2 | P0 | 없음 |
| F-002 | 메타-순환 해소 — `_check_mock_patterns` 인라인 백틱 인식 전처리 | R-3 | P0 | F-001 |

> 2개 기능 → **Multi-Feature 모드**. §2·§3을 F-NNN 하위 섹션으로 전개.

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (정규식 #1: MagicMock 맨 단어 제거)
   │  (선행 — 정규식이 5개 코드형 대안만 남은 상태가 F-002 전처리 설계의 전제)
   ▼
F-002 (메타-순환 #2: _check_mock_patterns 인라인 백틱 제거 전처리)
   │  단일 함수 개선 → mark TEST 훅(:1014-1020) + verify --check(:1704-1707) 양 호출 지점 동시 발효
   ▼
(034 자신의 TEST-SCENARIO.md가 mark/verify TEST 검사를 exit 0으로 통과 — 자기검증/메타-순환 해소)
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | `_MOCK_CODE_PATTERNS` 정규식 (`state_tool.py:1320-1322`) — #1 | **정탐 회귀** — `MagicMock` 대안 제거 시 실제 `MagicMock()` 코드가 미검출. 헌법 §4 가드 본질 파괴 | P0 (self-confirming 테스트 허용) | L1 (정규식/`_check_mock_patterns` 반환값 단위) | S-2 (정탐 유지), S-4~S-8 (5패턴 회귀) |
| H-2 | `_MOCK_CODE_PATTERNS` 정규식 — #1 | **오탐 잔존(산문)** — 산문 `MagicMock` 단어 계속 검출 → SKILL PM Gate 문구 차단 | P1 | L1 (산문 비검출 단위) | S-1 (RED→GREEN), S-3 (PM Gate 표준 문구) |
| H-3 | `_check_mock_patterns` 인라인 백틱 전처리 (`state_tool.py:1340-1346`) — #2 | **오탐 잔존(문서 예시)** — 인라인 백틱 코드 예시(`` `m = Mock()` `` 등)를 계속 검출 → mock 가드 검증 태스크 TEST 구조적 차단(메타-순환) | P0 (mock 가드 검증 태스크 자체가 불가능) | L1 (인라인 백틱 비검출 단위) | S-12 (백틱 예시 비검출), S-13 (034 자기 통과) |
| H-4 | `_check_mock_patterns` 인라인 백틱 전처리 — #2 | **정탐 회귀(코드펜스/bare)** — 전처리가 과도하여 코드펜스 내부 또는 인라인 백틱 밖 bare 라인의 실제 mock 코드까지 통과 → 헌법 §4 무력화 | P0 | L1 (코드펜스/bare 정탐 유지 단위) | S-2, S-4~S-8 (bare), S-14 (코드펜스 정탐) |
| H-5 | `_check_mock_patterns` 공개 동작 — mark TEST 훅(`:1014-1020`) / verify --check(`:1704-1707`) | **exit code/JSON 계약** — 두 호출 지점이 동일 함수 공유. 단일 함수 개선이 `mark`(자동 훅)·`verify`(명시 검사) 양쪽 exit code(0/1)·`error: mock_in_scenario` 동시 영향 | P1 | L2 (CLI 통합 — 실 TEST-SCENARIO.md 픽스처 + 실 호출) | S-9 (verify 통합), S-10 (mark TEST 훅 통합) |
| H-6 | 다른 5개 대안 (`unittest\.mock`/`@patch\b`/`mock\.patch`/`Mock\(`/`@mock\.`) | **비대상 회귀** — Surgical 위반으로 5대안이 의도치 않게 변경/약화 | P1 | L1 (5패턴 개별 검출 단위) | S-4~S-8 |
| H-7 | 배포 경계 (소스 `opal/tools/state-tool/state_tool.py` ↔ 배포본 `~/.opal/tools/state-tool/`) | **배포 미반영** — 소스만 수정·install 재배포 누락 시 런타임(배포본)은 여전히 오탐. `~/.opal/` 직접 수정은 컨벤션 위반 | P1 | L3 (배포 후 배포본 경로 실행 확인) | S-11 (배포 검증) |

> 가설 도출 예시 정합: H-1/H-4는 "Repository 반환 계약 변경 → 호출자 오류"형(정탐 회귀로 가드 무력화), H-5는 "병렬/공유 상태"형(단일 전역 함수를 2개 호출 지점이 공유), H-3은 "mock 통과 후 실 검사 실패"의 역(逆) — 정당한 텍스트가 검사에 막히는 메타-순환.

---

## 2. 기능별 분석

### F-001: mock 가드 정규식 오탐 제거

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 (Python 프레임워크 도구) | `opal/tools/state-tool/state_tool.py` | mock 가드 정규식 정의(`:1320-1322`) | 수정 |
| 공통 (테스트) | `opal/tools/state-tool/tests/test_state_tool.py` | 기존 mock 검출 테스트(`:1809-1853`, `:1938`) + RED-first 신규 케이스 | 수정 |

#### 2.1.2 현재 구현

ANALYSIS.md 없음 → 직접 코드 분석 수행.

**(a) 정규식 정의** (`state_tool.py:1320-1322`):

```python
# 헌법 §4 "Don't fake it" — TEST-SCENARIO.md mock 코드 패턴 검출
# M-2: 코드 사용 패턴만 정규식 매칭; 단순 "mock" 단어/설명 문구는 제외
_MOCK_CODE_PATTERNS = re.compile(
    r"MagicMock|unittest\.mock|@patch\b|mock\.patch|Mock\(|@mock\."
)
```

6개 대안:

| # | 대안 | 토큰 동반 | 산문 오탐 위험 |
|---|------|----------|--------------|
| 1 | `MagicMock` | **없음 (맨 단어)** | **있음 (#1 버그 원인)** — 점·괄호·@ 없이 어디서든 매칭 |
| 2 | `unittest\.mock` | `.` | 없음 (단, 백틱 예시 오탐은 #2 영역) |
| 3 | `@patch\b` | `@` + 단어경계 | 없음 (#2 영역) |
| 4 | `mock\.patch` | `.` | 없음 (#2 영역) |
| 5 | `Mock\(` | `(` | 없음 (#2 영역) |
| 6 | `@mock\.` | `@`·`.` | 없음 (#2 영역) |

#### 2.1.3 영향 범위

- **상위 의존(호출자)**: `cmd_mark`(TEST stage 자동 훅 `:1014-1020`), `cmd_verify`(--check `:1704-1707`). 두 명령의 exit code(0/1) 및 `mock_in_scenario` 에러 조건이 정규식+`_check_mock_patterns`에 직결.
- **하위 의존(피호출자)**: 없음 (정규식은 stdlib `re`만 의존).
- **관련 테스트**: `test_verify_detects_magicmock`(`:1809`), `test_verify_detects_unittest_mock`(`:1823`), `test_verify_detects_at_patch`(`:1832`), `test_verify_no_false_positive_on_plain_mock_word`(`:1842`), `test_mark_test_stage_mock_in_scenario_blocks`(`:1938`).

---

### F-002: 메타-순환 해소 — `_check_mock_patterns` 인라인 백틱 인식 전처리

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 (Python 프레임워크 도구) | `opal/tools/state-tool/state_tool.py` | `_check_mock_patterns`(`:1340-1346`) — 라인 단위 정규식 스캔 함수 (mark 훅·verify 공유) | 수정 |
| 공통 (테스트) | `opal/tools/state-tool/tests/test_state_tool.py` | F-002 신규 케이스 (백틱 비검출 / 코드펜스·bare 정탐 / 034 자기 통과) | 수정 |

#### 2.2.2 현재 구현

**(b) 검출 함수** (`state_tool.py:1340-1346`, 공개 관찰 인터페이스):

```python
def _check_mock_patterns(lines):
    """코드 패턴 검출 — 위반 라인 번호 목록 반환."""
    violations = []
    for lineno, line in enumerate(lines, start=1):
        if _MOCK_CODE_PATTERNS.search(line):
            violations.append(lineno)
    return violations
```

현재는 **각 라인 원문(raw)을 그대로** 정규식에 통과시킨다. 마크다운 구조(인라인 백틱·코드펜스·표 셀)를 인식하지 않으므로, 문서화용으로 인라인 백틱에 감싼 코드 토큰(`` `m = Mock()` `` 등)도 실제 코드와 동일하게 검출된다.

[MUST] `opal/core/references/harness/red-first.md` §4: "내부 구현/private 결합 금지, 공개 인터페이스·관찰 행위(반환값/exit code/관측 출력)로 검증." → 테스트는 `_check_mock_patterns` 반환값(라인 목록) 또는 `mark`/`verify` exit code/JSON으로만 검증한다 (정규식 객체·전처리 내부 직접 단언 금지).

**(c) 호출 지점 2곳** (동일 함수 공유 — 단일 수정으로 양쪽 동시 교정):

1. `mark` TEST stage done 자동 훅 (`state_tool.py:1014-1020`):
   ```python
   if row["stage"] == "TEST":
       scenario_path = _find_scenario_file(task_path, None)
       if scenario_path is not None:
           lines = scenario_path.read_text(encoding="utf-8").splitlines()
           mock_lines = _check_mock_patterns(lines)
           if mock_lines:
               err("mark", "mock_in_scenario", lines=mock_lines)
   ```
2. `verify --check` (`state_tool.py:1704-1707`):
   ```python
   mock_lines = _check_mock_patterns(lines)
   if mock_lines:
       err(command, "mock_in_scenario", lines=mock_lines)
   ```
   > **`--force` 분기 부재 확인**: 두 호출 지점 모두 mock 검사에 `--force` 우회 분기가 **없다**(`check_stage_transition_guard`/`check_close_gate`의 force와 무관 — `:355`, `:412`). 본 PLAN은 force 우회를 **도입하지 않는다**(§3.2.2 D-DEC-3 — force는 가드 본질 무력화이므로 채택 거부).

#### 2.2.3 영향 범위

- **공유 상태**: `_check_mock_patterns`는 mark 훅·verify가 공유하는 단일 함수 → 함수 내 전처리 1회 추가 = **양 호출 지점 동시 발효**(H-5).
- **메타-순환 구조**: mock 가드를 검증·문서화하는 TEST-SCENARIO.md(034 자신 포함)는 가드 패턴을 예시로 인용해야 하는데, 현재는 그 예시가 가드에 걸려 TEST mark가 거부된다.

#### 2.2.4 직접 시뮬레이션 결과 (입증 — 추측 금지)

`python3` 직접 실행으로 **#1 적용 후(post-#1) 정규식** `r"unittest\.mock|@patch\b|mock\.patch|Mock\(|@mock\."`을 (가) 원문 스캔 (나) 인라인 백틱 제거 전처리 후 스캔으로 비교한 결과 (§2.2(e)):

**(e-1) 설계 후보별 트레이드오프** (3개 후보를 동일 입력군에 매칭):

| 입력군 | (i) 코드펜스 내부만 검사 | (ii) 인라인 백틱 제거 후 검사 | (iii) 메타 마커 스킵 |
|--------|------------------------|------------------------------|---------------------|
| 정당한 문서 예시 (인라인 백틱 / 표 셀) | 통과 ✅ | **통과 ✅** | 통과(파일 전체) |
| 실제 mock 코드 — **bare 라인** (백틱·펜스 밖) | **미검출 ❌ (회귀)** | **검출 ✅** | 미검출 ❌ (마커 시) |
| 실제 mock 코드 — 코드펜스 내부 | 검출 ✅ | 검출 ✅ | 미검출 ❌ (마커 시) |

> **핵심 입증**: 기존 테스트 `test_verify_detects_unittest_mock`(`:1823`)·`test_verify_detects_at_patch`(`:1832`)·`test_mark_test_stage_mock_in_scenario_blocks`(`:1938`)는 실제 mock 코드를 **bare 라인**(코드펜스 없이)으로 둔다. 따라서 **(i) 코드펜스 내부만 검사**는 이 3개 테스트를 회귀시킨다(미검출). **(iii) 메타 마커**는 마커가 있는 파일 전체를 스킵 → 헌법 §4 무력화 위험 + 마커 표준화 비용. **(ii) 인라인 백틱 제거 전처리**만이 ① 문서 예시(백틱/표 셀) 통과 ② bare 라인 실제 코드 검출 유지 ③ 코드펜스 내부 검출 유지를 **모두** 충족한다.

**(e-2) 실측 — 034 자신의 TEST-SCENARIO.md (현 상태, #2 미적용)**:

| 스캔 방식 | hits | 의미 |
|----------|------|------|
| post-#1 원문(raw) 스캔 | **22건** | 메타-순환 BLOCK (PM 실측 일치) |
| post-#1 + 인라인 백틱 제거 (ii) | **0건** | TEST mark/verify exit 0 통과 (메타-순환 해소) |

> 위 22건은 모두 인라인 백틱(`` `...` ``) 또는 표 셀 백틱 내부의 문서화 코드 예시다. 코드펜스(```` ``` ````) 내부 실제 mock 코드는 034 본문에 0건. → **(ii)가 034를 통과시키면서 헌법 §4 정탐은 보존**됨이 실측으로 확정.

**(e-3) 엣지 케이스 (ii) 전처리 정확성 실측**:

| 입력 | (ii) 후처리 결과 | 기대 |
|------|-----------------|------|
| `` `m = Mock()` 예시 토큰 `` (백틱만) | 비검출 | 통과 ✅ |
| `` `Mock()` is the example: x = Mock() `` (백틱 + bare 동시) | **검출**(bare 잔존) | 검출 ✅ (실제 코드 잡음) |
| `` `Mock( unclosed then real x=Mock() `` (백틱 미닫힘) | **검출**(미닫힘 → 미제거) | 검출 ✅ (fail-safe) |
| 코드펜스 내부 `m = Mock()` (백틱 없음) | 검출 | 검출 ✅ |

> **fail-safe 성질**: 백틱 미닫힘 시 해당 구간을 제거하지 않으므로 "의심 시 검사" 방향 — 가드 약화 위험 없음.

---

## 3. 기능별 설계

### F-001: mock 가드 정규식 오탐 제거

#### 3.1.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 공통 | 정규식 첫 대안 `MagicMock|` **제거** → `r"unittest\.mock|@patch\b|mock\.patch|Mock\(|@mock\."`. `MagicMock()` 정탐은 `Mock\(`가 커버. 주석(`:1319`)에 잉여 제거 근거 + `(034)` 표기, @header `description`(`:6`)에 `034:` 변경이력 추가 | `state_tool.py:1320-1322`, 시뮬레이션 §2.1.2, (→ D-5) |
| 2 | `opal/tools/state-tool/tests/test_state_tool.py` | 공통 | F-001 RED-first 케이스: 산문 `MagicMock` 비검출(RED→GREEN) + `MagicMock()` 정탐 유지 + 5패턴 회귀 | `tests/test_state_tool.py:1809-1853`, (→ D-3 §4) |

#### 3.1.2 설계 결정

##### D-DEC-1: 정규식 #1 수정 방식 — 대안 (b) `MagicMock` 제거 (권장, 기존 PLAN §D-DEC-1 유지)

**결정**: `_MOCK_CODE_PATTERNS`에서 첫 대안 `MagicMock`(맨 단어)을 **제거**한다.

```python
# 수정 후 (state_tool.py:1320-1322)
# M-2 / 034: 코드 사용 패턴만 매칭. 'MagicMock' 맨 단어 대안 제거 —
#   산문(예: PM Gate 표준 문구 "...MagicMock 등 부재")을 오탐하던 #1 원인.
#   실제 MagicMock() 호출은 'Mock\(' 대안이 이미 커버한다(잉여 입증: §2.1.2).
_MOCK_CODE_PATTERNS = re.compile(
    r"unittest\.mock|@patch\b|mock\.patch|Mock\(|@mock\."
)
```

**근거**: `re.compile(r"Mock\(").search("x = MagicMock()")` → `True`. 즉 `Mock\(`(대안 #5)가 실제 `MagicMock()` 호출의 끝부분 `Mock(`을 **이미 매칭**한다 → 대안 #1은 잉여. 제거(b)가 더 surgical(대안 1개 감소, 새 의미 도입 없음). TASK.md §27 "잉여" 단서와 정합 (→ D-1). 두 안(a `MagicMock\(` 한정 / b 제거)이 케이스 전부 동일 결과 → (b) 채택, 주석으로 `Mock\(` 커버 근거 명시.

[MUST] `opal/core/PRINCIPLES.md` §4: "Don't fake it: never substitute a mock for a real integration you were asked to build." → 본 #1 수정은 산문 오탐만 제거하고 5개 코드 패턴 + `MagicMock()` 정탐(via `Mock\(`)을 보존한다.

---

### F-002: 메타-순환 해소 — `_check_mock_patterns` 인라인 백틱 인식 전처리

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 3 | `opal/tools/state-tool/state_tool.py` | 공통 | `_check_mock_patterns`(`:1340-1346`)에 **인라인 백틱 제거 전처리** 추가 — 검사 전 각 라인의 `` `...` `` 인라인 코드 구간을 제거한 사본으로 정규식 매칭. 코드펜스 내부·bare 라인은 원문 그대로 매칭(정탐 유지). 함수 docstring/주석에 `(034 #2)` 근거 + 헌법 §4 정탐 유지 명시 | `state_tool.py:1340-1346`, 시뮬레이션 §2.2.4, (→ D-1, D-5) |
| 4 | `opal/tools/state-tool/tests/test_state_tool.py` | 공통 | F-002 케이스: 인라인 백틱 코드 예시 비검출(S-12) + 코드펜스/bare 정탐 유지(S-14) + 034 자기 TEST-SCENARIO.md 통과(S-13) + mark/verify 통합(S-9/S-10) | `tests/test_state_tool.py`, (→ D-3 §4) |

#### 3.2.2 설계 결정

##### D-DEC-2: #2 방식 — (ii) 인라인 백틱 제거 전처리 (채택)

**결정**: `_check_mock_patterns`가 각 라인을 정규식에 통과시키기 **전에**, 라인 내 인라인 백틱 코드 구간(`` `...` ``)을 제거한 사본을 만들어 그 사본으로 매칭한다. 코드펜스(```` ``` ````) 내부 라인과 인라인 백틱 밖 텍스트는 영향받지 않는다.

**함수 시그니처 (불변 — 반환 계약 보존)**:
```python
def _check_mock_patterns(lines):  # (lines: list[str]) -> list[int]  — 시그니처/반환 계약 불변
    """코드 패턴 검출 — 위반 라인 번호 목록 반환.

    034 #2: 인라인 백틱(`...`) 코드 예시는 문서화/설명 표기이므로 검사 전 제거한다.
            코드펜스(```) 내부·백틱 밖 bare 라인의 실제 mock 코드는 그대로 검출(헌법 §4 유지).
    """
    violations = []
    in_fence = False
    for lineno, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue                       # 펜스 경계선 자체는 검사 제외
        if in_fence:
            target = line                  # 코드펜스 내부 = 실제 코드 → 원문 검사
        else:
            target = re.sub(r"`[^`]*`", "", line)   # 인라인 백틱 구간 제거 후 검사
        if _MOCK_CODE_PATTERNS.search(target):
            violations.append(lineno)
    return violations
```

**설계 근거 (후보 트레이드오프 §2.2.4(e-1) → (ii) 채택)**:
- **(i) 코드펜스 내부만 검사**: 기존 테스트 3개(`:1823`/`:1832`/`:1938`)가 실제 mock 코드를 **bare 라인**으로 두므로 회귀(미검출) → **거부**.
- **(iii) 메타 마커**: 파일 전체 스킵 → 헌법 §4 무력화 + 표준화 비용 → **거부**.
- **(ii) 인라인 백틱 제거**: 문서 예시(백틱/표 셀) 통과 + bare 라인 + 코드펜스 정탐 유지 → **채택**. 034 현 TEST-SCENARIO.md를 22건→0건으로 통과시키면서(§2.2.4(e-2)) 헌법 §4 정탐 전부 보존(§2.2.4(e-3)).
- **코드펜스 상태추적 병행**: (ii)만으로도 충분하나, 코드펜스 내부에 인라인 백틱이 드물게 등장할 경우를 대비해 펜스 내부는 원문 그대로 검사하여 "실제 목업 때우기 코드(통상 코드펜스)"의 검출을 명시적으로 강화한다. → (ii) + 코드펜스 인식 **조합**.

> **op-dev-test-scenario 작성 관행 확인 결과**(survey): SKILL §7은 코드 예시에 코드펜스/인라인 백틱을 명시 지시하지 않으나, TEST-SCENARIO.md 템플릿은 **표 + 인라인 백틱**으로 코드 토큰을 표기하는 것이 실제 관행이다(034 포함 전수 인라인 백틱). → (ii)가 작성 관행과 정합.

[MUST] `opal/core/PRINCIPLES.md` §4: "Don't fake it: never substitute a mock for a real integration you were asked to build." → (ii)는 인라인 백틱(문서화 표기) 안의 코드 토큰 언급만 통과시키고, **인라인 백틱 밖 bare 라인 + 코드펜스 내부의 실제 mock 코드는 계속 검출**한다. "시나리오 본문에 실제 mock 코드" 차단 본질을 유지한다.

##### D-DEC-3: `--force` 우회 도입 거부

[MUST] `opal/core/PRINCIPLES.md` §4 (가드 본질) → mock 검사에 `--force` 우회를 **도입하지 않는다**. 배경 브리프의 "mark TEST 훅에 `--force` 분기 부재로 거부됨" 진단은 표면 증상이며, 근본 원인은 오탐 자체다. force 우회는 누구든 실제 mock 검사를 무력화할 수 있어 헌법 §4를 약화시킨다. (ii) 전처리로 오탐을 제거하면 034 TEST 행 mark는 우회 없이 자연 통과한다(§2.2.4(e-2)).

##### D-DEC-4: Surgical 경계

[MUST] `TASK.md` §제약 조건 — 최소 변경(Surgical): "state_tool.py 변경을 정규식(#1) + `_check_mock_patterns` 검사 로직(#2)에 한정. 다른 로직 불변." → 정규식 대안 #2~#6, `_check_evidence`, `_check_red_evidence`, `cmd_mark`/`cmd_verify` 본문은 **불변**. 변경은 ① 정규식 문자열 1줄(#1) ② `_check_mock_patterns` 내부 루프 전처리(#2) ③ 인접 주석/docstring ④ @header description ⑤ 테스트 파일에 한정.

[MUST] `opal/core/PRINCIPLES.md` §3 Surgical: "Touch only what the plan names. Don't refactor what isn't broken." → `re` 모듈은 이미 import됨(`state_tool.py:20`), 신규 import 불요.

#### 3.2.3 공통 — 환경/배치

[MUST] `docs/CONVENTIONS.md` §구현 규칙 — 배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`...)에서 수행한다. 변경 후 `./scripts/install-mac.sh`로 재배포하여 검증한다." → 소스 수정 후 `./scripts/install-mac.sh` 재배포로 배포본(`~/.opal/tools/state-tool/state_tool.py`)에 발효(H-7).

[MUST] `docs/CONVENTIONS.md` §구현 규칙 — @header/변경이력: "코드 파일을 생성·수정할 때 ... @header 블록을 작성한다." → @header `description`(`:6`)에 기존 014/016/017/005 누적 패턴을 따라 `034:` 변경 요약 1줄 추가(#1 정규식 + #2 인라인 백틱 인식).

### 3.3 환경 변경

해당 없음 (stdlib `re`만 사용, 이미 import됨, 신규 패키지 없음).

### 3.4 배치/마이그레이션

소스 수정 후 **`./scripts/install-mac.sh` 재배포** 필요 — 런타임 배포본에 #1+#2 반영(H-7). DB 마이그레이션·크론 없음.

### 3.5 테스트 시나리오 (AC ↔ TS 매핑)

> RED-first 강제 트랙 (버그 수정 — `red-first.md` §1.5). RED→GREEN 순서 적용. 상세는 TEST-SCENARIO.md.
> **실제 입력 문자열은 `tests/test_state_tool.py`(.py — 가드 비검사)에 둔다.** TEST-SCENARIO.md 본문은 인라인 백틱/표로 예시를 표기하여 #2 적용 후 자기 통과 가능하게 작성한다.

| TS-ID | AC 매핑 | F | 유형 | 기대 결과 |
|-------|---------|---|------|----------|
| TS-001 | R-2 AC (RED #1) | F-001 | 회귀 (RED) | 수정 전: `_check_mock_patterns(["...mock/patch/MagicMock 등 부재"])` ≠ `[]`(검출=버그). FAIL=RED 증거 |
| TS-002 | R-1 AC | F-001 | 기능 (GREEN) | 수정 후: 위 산문 → `[]`. `["x = MagicMock()"]` → `[1]` 검출 유지 |
| TS-003 | R-1 AC | F-001 | 기능 | SKILL §7:157 PM Gate 표준 문구 → `verify`/`mark` exit 0 |
| TS-004~008 | R-2 AC (c) | F-001 | 회귀 | 5패턴(bare) 각각 `[1]` 검출 유지 |
| TS-009 | R-1/R-3 AC, H-5 | F-002 | 통합 | `verify` CLI: 산문/백틱 예시 TEST-SCENARIO.md → exit 0; bare `MagicMock()` → exit 1 `mock_in_scenario` |
| TS-010 | R-1/R-3 AC, H-5 | F-002 | 통합 | `mark` TEST 훅: 산문/백틱 → 차단 안 됨(exit 0); bare `MagicMock()` → exit 1 차단 |
| TS-011 | H-7 | 공통 | 회귀 | 기존 184 + 신규 → pytest 0 fail; install 재배포 후 배포본 동작 동일 |
| TS-012 | R-3 AC (RED #2) | F-002 | 회귀 (RED→GREEN) | 수정 전: `_check_mock_patterns(["대상 `` `m = Mock()` `` 입력"])` ≠ `[]`(백틱 예시 검출=메타-순환 버그, RED). 수정 후: `[]`(비검출) |
| TS-013 | R-3 AC (자기검증) | F-002 | 통합 | 034 자신의 TEST-SCENARIO.md → `verify`/`mark` TEST 검사 exit 0 (메타-순환 해소 증명) |
| TS-014 | R-3 AC (정탐 유지) | F-002 | 기능 | 코드펜스(```` ``` ````) 내부 `m = Mock()` → `[N]` 검출 유지; 백틱+bare 동시 라인 → bare 검출 유지 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 (RED) | F-001, F-002 | 1 | opal-task-agent | 순차 | #1 산문 RED + #2 백틱 예시 RED 단언 작성·실행 → 실패(RED 증거) 확보 |
| 2 (GREEN #1) | F-001 | 2 | opal-task-agent | 순차 | 정규식 `MagicMock|` 제거 → #1 RED 테스트 GREEN |
| 3 (GREEN #2) | F-002 | 3 | opal-task-agent | 순차 | `_check_mock_patterns` 인라인 백틱 전처리 → #2 RED 테스트 GREEN |
| 4 (회귀+자기검증) | F-001, F-002 | 4, 5 | opal-task-agent | 순차 | 5패턴 회귀 + 034 자기 TEST-SCENARIO.md 통과 + 코드펜스/bare 정탐 |
| 5 (전체회귀+배포) | 공통 | 6 | opal-task-agent | 순차 | 전체 pytest 회귀 + install 재배포 검증 |
| 6 (문서) | 공통 | 7 | PM 직접 | 순차 | docs/ 갱신 판단 |

### 4.2 실행 체크리스트

> 총 7개 Step | Phase 6개 | 실행 모드: **단순**
> RED-first 강제 트랙 — EXECUTE 진입 전 RED 증거 게이트(red-first.md §1.5). RED 증거는 **테스트 코드 실패(exit≠0)** 형태(코드 단위 RED). TEST-SCENARIO.md §RED 증거 표를 채운 뒤 게이트 통과.

#### Step 1: RED — #1 산문 + #2 백틱 예시 오탐 재현 테스트 작성·실행 (실패 확인)
- [x] 완료
- **소속 기능**: F-001, F-002
- **영역**: 공통 (테스트)
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: 두 RED 단언을 추가한다. (#1) `self.assertEqual(ST._check_mock_patterns(["- [x] mock/patch/MagicMock 등 시나리오 본문에 부재"]), [])` (TS-001). (#2) 인라인 백틱 코드 예시 비검출 단언 — 입력 문자열은 `.py` 내부에 두므로 백틱 포함 라인을 직접 구성: `self.assertEqual(ST._check_mock_patterns(["대상 `m = Mock()` 토큰을 문서화"]), [])` (TS-012). **이 시점에 정규식·전처리 미수정** → 두 RED 단언이 FAIL해야 한다.
- **완료 기준**: 신규 RED 단언 2건이 **FAIL**(현 코드가 검출=버그) → RED 증거 캡처(pytest 출력 `2 failed` 또는 케이스별 1 failed). 실패 로그를 TEST-SCENARIO.md §RED 증거 표에 기록.
- **테스트**: TS-001 (RED #1), TS-012 (RED #2)
- **실행 방법**: direct
- **의존**: 없음

#### Step 2: GREEN #1 — 정규식 `MagicMock` 대안 제거
- [x] 완료
- **소속 기능**: F-001
- **영역**: 공통 (Python 프레임워크 도구)
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/state_tool.py`
- **작업 내용**: `_MOCK_CODE_PATTERNS`(`:1320-1322`)에서 첫 대안 `MagicMock`을 제거하여 `r"unittest\.mock|@patch\b|mock\.patch|Mock\(|@mock\."`로 변경(D-DEC-1). 인접 주석(`:1319`)에 잉여 제거 근거 + `(034)`, @header `description`(`:6`)에 `034:` 변경이력 1줄 추가. **다른 5개 대안·`_check_mock_patterns` 본문 불변(D-DEC-4).**
- **완료 기준**: Step 1의 #1 RED 단언(TS-001) GREEN 전환 + `_check_mock_patterns(["x = MagicMock()"])` → `[1]` 정탐 유지(TS-002). 정규식 diff = 첫 대안 `MagicMock|` 제거 1곳 + 주석/header.
- **테스트**: TS-002
- **실행 방법**: direct
- **의존**: Step 1

#### Step 3: GREEN #2 — `_check_mock_patterns` 인라인 백틱 인식 전처리
- [x] 완료
- **소속 기능**: F-002
- **영역**: 공통 (Python 프레임워크 도구)
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/state_tool.py`
- **작업 내용**: `_check_mock_patterns`(`:1340-1346`)에 D-DEC-2 설계대로 ① 코드펜스 상태추적(```` ``` ````/`~~~` 진입/이탈) ② 펜스 밖 라인은 `re.sub(r"`[^`]*`", "", line)`로 인라인 백틱 구간 제거 후 매칭 ③ 펜스 내부·bare 라인은 원문 매칭을 추가한다. 함수 시그니처·반환 계약 불변. docstring에 `(034 #2)` 근거 + 헌법 §4 정탐 유지 명시.
- **완료 기준**: Step 1의 #2 RED 단언(TS-012) GREEN 전환(백틱 예시 → `[]`) + 코드펜스 내부 mock → 검출 유지(TS-014) + 백틱+bare 동시 라인 → bare 검출 유지(TS-014). `MagicMock()` bare 라인 정탐 유지.
- **테스트**: TS-012 (GREEN), TS-014
- **실행 방법**: direct
- **의존**: Step 2

#### Step 4: 5패턴 회귀 + mark/verify 통합 보강 테스트
- [x] 완료
- **소속 기능**: F-001, F-002
- **영역**: 공통 (테스트)
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: 5개 코드 패턴(bare 라인) 검출 유지(TS-004~008) + `verify` 통합(TS-009: 산문/백틱 예시 → exit 0, bare `MagicMock()` → exit 1) + `mark` TEST 훅 통합(TS-010) 단언 추가/보강. 기존 `test_verify_detects_*`(`:1809-1840`)와 중복 회피 — 미커버인 `mock.patch`/`Mock()`/`@mock.`/백틱 예시 비차단을 신규 추가.
- **완료 기준**: 신규 5패턴 + verify/mark 통합 테스트 PASS. 기존 `test_verify_no_false_positive_on_plain_mock_word`(`:1842`)·`test_verify_detects_unittest_mock`(`:1823`)·`test_verify_detects_at_patch`(`:1832`) 회귀 0.
- **테스트**: TS-004 ~ TS-010
- **실행 방법**: direct
- **의존**: Step 3

#### Step 5: 034 자기 TEST-SCENARIO.md 통과 검증 (메타-순환 해소 증명)
- [x] 완료
- **소속 기능**: F-002
- **영역**: 공통 (검증)
- **agent**: opal-task-agent
- **파일**: `tasks/034-260621-opds-state-tool-mock-패턴-오탐수정/TEST-SCENARIO.md` (입력, 읽기 전용)
- **작업 내용**: 재배포 전 소스 기준으로, 034 자신의 TEST-SCENARIO.md를 입력으로 `_check_mock_patterns` 및 `cmd_verify`를 호출하여 exit 0(비검출)을 확인한다(TS-013). 메타-순환(가드를 검증하는 문서가 가드에 막힘)이 해소됐음을 자기검증으로 증명. **TEST-SCENARIO.md를 통과 목적으로 수정하지 않는다**(test 불변성과 별개 — 본문은 PM이 #2 방식에 맞춰 이미 작성).
- **완료 기준**: 034 TEST-SCENARIO.md → `_check_mock_patterns` 반환 `[]` + `verify` exit 0. (TS-013)
- **테스트**: TS-013
- **실행 방법**: direct
- **의존**: Step 4

#### Step 6: 전체 회귀 실행 + install 재배포 검증
- [x] 완료 (pytest 197 passed — install 재배포는 캡틴 승인 사안으로 제외)
- **소속 기능**: 공통
- **영역**: 환경 (배포)
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py` (실행), `scripts/install-mac.sh` (재배포 실행)
- **작업 내용**: `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py`로 전체(기존 184 + 신규) 회귀 0 fail 확인. 이어 `./scripts/install-mac.sh` 재배포 후 배포본(`~/.opal/tools/state-tool/state_tool.py`)에 #1(`MagicMock|` 부재)·#2(인라인 백틱 전처리) 반영 확인(`grep` 또는 배포본 `verify`로 034 TEST-SCENARIO.md exit 0). [MUST] 배포본 직접 수정 금지.
- **완료 기준**: pytest 0 fail. 배포본 정규식 = 소스(`MagicMock|` 없음) + `_check_mock_patterns` 전처리 반영. 배포본 `verify`로 034 TEST-SCENARIO.md/PM Gate 산문 → exit 0 (TS-011, TS-013).
- **테스트**: TS-011
- **실행 방법**: direct
- **의존**: Step 5

#### Step 7: docs/ 갱신 판단 (선택)
- [ ] 완료
- **소속 기능**: 공통
- **영역**: 문서
- **agent**: PM 직접
- **파일**: (판단 후 필요 시) 없음 (기본)
- **작업 내용**: 본 변경은 **기존 가드 버그 수정**(정규식 + 검사 전처리)이며 외부 계약(API/컴포넌트/시스템 구조/새 규칙) 변경이 없으므로 docs/ 갱신 **불요로 판단**(기본값). mock 가드 마크다운 구조 인식은 도구 내부 동작이며 CONVENTIONS.md 신규 규칙이 아니다. 버그 근본원인·교훈은 `.opal/brain/pages/concept/state-tool-mock-guard-skill-false-positive.md`(D-4)에 존재 → CLOSE 단계 brain ingest 훅이 #2 메타-순환 교훈을 갱신. PM 최종 확인.
- **완료 기준**: docs/ 갱신 불요 확정 또는 필요 시 해당 문서 1행 갱신.
- **테스트**: 해당 없음 (문서 판단)
- **실행 방법**: direct
- **의존**: Step 6

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | RED→GREEN 강제 순서 (red-first.md §1). #1 RED 증거 확보 후 정규식 수정 |
| Step 2 → Step 3 | #1(정규식 5개 코드형 대안만 남음)이 #2 전처리 설계의 전제. #1 GREEN 후 #2 진입 |
| Step 3 → Step 4 | 정규식+전처리 수정 후에야 5패턴/통합 회귀 변별력 있음 |
| Step 4 → Step 5 | 단위/통합 GREEN 후 034 자기 통과(메타-순환) 검증 의미 있음 |
| Step 5 → Step 6 | 전체 회귀 통과 후 배포 검증 의미 있음 |
| Step 6 → Step 7 | 코드·배포 완료 후 docs/ 영향 판단 |
| 전 Step 순차 | 동일 파일 2개(state_tool.py, test_state_tool.py) 교차 수정 — 파일 충돌 방지 위해 순차. 병렬 없음 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 산문 `MagicMock` 단어 오탐 제거 (#1) | TS-001, TS-002, TS-003 | RED 단언이 수정 전 FAIL → 수정 후 PASS. PM Gate 표준 문구 `verify` exit 0 |
| F-001 | 실제 `MagicMock()` 정탐 유지 | TS-002, TS-009 | `_check_mock_patterns(["x = MagicMock()"])` → `[1]`; `verify` exit 1 `mock_in_scenario` |
| F-001 | 5개 코드 패턴(bare) 회귀 무손실 | TS-004 ~ TS-008 | 5패턴 각각 검출 유지 |
| F-002 | 인라인 백틱 코드 예시 오탐 제거 (#2) | TS-012, TS-013 | 백틱 예시 비검출(RED→GREEN); 034 자기 TEST-SCENARIO.md exit 0 |
| F-002 | 코드펜스/bare 실제 mock 정탐 유지 (헌법 §4) | TS-014, TS-002, TS-004~008 | 코드펜스 내부·bare 라인 검출 유지; 백틱+bare 동시 라인 → bare 검출 |
| F-002 | mark/verify 양 호출 지점 정합 | TS-009, TS-010 | 동일 입력에 verify·mark TEST 훅 exit code 동일(정당 텍스트 0 / 실제 코드 1) |
| 공통 | 전체 회귀 + 배포 발효 | TS-011 | pytest 0 fail; 배포본 #1+#2 반영 |

### 5.2 회귀 테스트
- [ ] 기존 `test_state_tool.py` 184개 테스트 전부 통과 (회귀 0)
- [ ] 기존 `test_verify_detects_magicmock`(`:1809`, 코드펜스 내부) → 검출 유지
- [ ] 기존 `test_verify_detects_unittest_mock`(`:1823`, bare)·`test_verify_detects_at_patch`(`:1832`, bare) → 검출 유지 (★ #2 (i) 코드펜스-only 방식이었다면 회귀했을 케이스 — (ii) 채택으로 보존)
- [ ] 기존 `test_mark_test_stage_mock_in_scenario_blocks`(`:1938`, bare) → 차단 유지
- [ ] 기존 `test_verify_no_false_positive_on_plain_mock_word`(`:1842`) → 비검출 유지

### 5.3 코드/문서 품질
- [ ] 정규식 변경이 **첫 대안 `MagicMock|` 제거 1곳**으로 한정 (D-DEC-1/D-DEC-4)
- [ ] `_check_mock_patterns` 변경이 **인라인 백틱 제거 + 코드펜스 상태추적 전처리**로 한정, 시그니처/반환 계약 불변 (D-DEC-2/D-DEC-4)
- [ ] `--force` 우회 미도입 (D-DEC-3)
- [ ] @header `description`에 `034:` 변경이력 1줄 추가 (014/016/017/005 누적 패턴 준수)
- [ ] 정규식 주석 + `_check_mock_patterns` docstring에 근거·헌법 §4 정탐 유지 명시
- [ ] RED-first 트랙 — RED 증거(테스트 실패 로그) TEST-SCENARIO.md에 기록 (#1+#2 각각)

### 5.4 보안
- [ ] 정규식/전처리 변경에 ReDoS 위험 없음 — `re.sub(r"`[^`]*`", ...)`는 백트래킹 폭발 패턴 아님(부정 문자셋 `[^`]` 선형). 대안 제거는 복잡도 감소 방향
- [ ] 하드코딩 시크릿/토큰 없음 (정규식 + 테스트 문자열만)
- [ ] 가드 본질 무력화 없음 — 헌법 §4 mock 차단 능력 유지 (코드펜스·bare 정탐 보존; force 우회 미도입)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 7개 (코드 변경 실질 3개: #1 정규식 / #2 전처리 / 테스트) | 단순 (경계) |
| 변경 파일 수 | 2개 (state_tool.py + test_state_tool.py) | 단순 (3개 이하) |
| 모듈 범위 | 단일 모듈 (state_tool) | 단순 |
| 작업 유형 | 오류 수정 (정규식 1줄 + 함수 내 전처리) | 단순 |
| 외부 의존성 | 없음 (stdlib re, 기존 import) | 단순 |
| **실행 모드** | **단순** | |

> 모든 기준이 단순 → §7 실행 아키텍처 생략. 전 Step `direct` 실행. (#2 추가로 Step이 5→7로 늘었으나 단일 모듈·2파일·stdlib 한정이라 단순 모드 유지.)

---

## 7. 실행 아키텍처

해당 없음 (단순 모드).

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 프레임워크 도구 | Python 3 (stdlib `re`, `argparse` CLI) | (trailofbits/modern-python — 정규식 1줄 + 함수 내 전처리로 신규 패턴 도입 없어 미참조) |
| 테스트 | pytest / unittest (`test_state_tool.py`) | red-first.md (RED-first 강제 트랙) |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | stdlib `re` 동작은 `python3` 직접 시뮬레이션(§2.2.4)으로 검증 — 외부 문서 불요 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | 수정 대상 — 정규식(`:1320-1322`)·`_check_mock_patterns`(`:1340-1346`)·호출(`:1014-1020`, `:1704-1707`) |
| D-2 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` | 기존 mock 테스트(`:1809-1853`, `:1938`) + RED-first 신규 추가 대상 |
| D-3 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` | 버그 수정=RED-first 강제 트랙(§1.5), 공개 인터페이스 검증(§4) |
| D-4 | 참조 | brain concept | `.opal/brain/pages/concept/state-tool-mock-guard-skill-false-positive.md` | 033 버그 분석 — #1 fix 방향(b 권장) 근거 |
| D-5 | 설계 | op-dev-test-scenario SKILL | `~/.opal/skills/op-dev-test-scenario/SKILL.md` §7 | 오탐된 PM Gate 표준 문구(`:157`) 출처 — TS-003 입력 + 작성 관행(인라인 백틱) 확인 |
| D-6 | 설계 | PRINCIPLES.md (헌법) | `opal/core/PRINCIPLES.md` §4 | "Don't fake it" — 가드 본질 [MUST] |
| D-7 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 배포 경계 / @header·변경이력 [MUST] 규칙 |
| D-8 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 포맷·[MUST] 토큰 규정 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 정탐 회귀 — `MagicMock()` 미검출 (H-1) | F-001 | P0 (가드 무력화) | `Mock\(`가 커버함을 시뮬레이션 입증(§2.1.2) + TS-002로 단언 고정 |
| R-2 | 오탐 잔존(산문) — 산문 계속 검출 (H-2) | F-001 | P1 (PM Gate 차단) | RED-first로 산문 비검출 고정(TS-001→TS-002) |
| R-3 | 오탐 잔존(문서 예시) — 백틱 예시 계속 검출 (H-3) | F-002 | P0 (mock 가드 검증 태스크 불가) | (ii) 인라인 백틱 제거 전처리 + TS-012/TS-013 자기검증 고정 |
| R-4 | 정탐 회귀(코드펜스/bare) — 전처리 과도 (H-4) | F-002 | P0 (헌법 §4 무력화) | 펜스 내부·bare 원문 검사 유지 + 백틱 미닫힘 fail-safe(§2.2.4(e-3)) + TS-014로 단언 고정. (i) 코드펜스-only 거부(기존 3 테스트 회귀 입증) |
| R-5 | 양 호출 지점 불일치 (H-5) | F-002 | P1 | 단일 함수 공유 — 단일 수정 동시 발효. mark·verify 통합 테스트(TS-009/010) |
| R-6 | Surgical 위반 — 비대상 대안/로직 변경 (H-6) | F-001 | P1 | diff를 정규식 1곳 + `_check_mock_patterns` 루프 전처리로 한정(D-DEC-4) + 5패턴 회귀(TS-004~008) |
| R-7 | 배포 미반영 (H-7) | 공통 | P1 | Step 6에서 install 재배포 + 배포본 #1+#2 반영 확인(TS-011). 배포본 직접 수정 금지 |
| R-8 | `--force` 우회 유혹 — 가드 약화 | F-002 | P0 | D-DEC-3에서 명시 거부. 오탐 제거로 우회 불요 |
