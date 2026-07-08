# TASK: state-tool mock 가드 false positive 수정

> 작성일: 2026-06-21 | 작업 유형: 오류(버그 수정) | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

`state_tool.py`의 mock 코드 검출 가드(`_MOCK_CODE_PATTERNS`)가 산문/설명 문구의 `MagicMock` **단어**를 실제 mock 코드로 오탐(false positive)하는 버그를 수정한다. 실제 mock 코드 검출 능력(헌법 §4 "Don't fake it")은 유지한다.

## 배경

태스크 033 TEST 단계에서 `state-tool mark --row 12`가 `mock_in_scenario` 에러로 거부됐다. 원인 분석 결과, TEST-SCENARIO.md의 **정상 체크리스트 문구**가 mock 가드 정규식에 걸린 것으로, 도구의 의도(주석)와 실제 동작이 모순됨을 확인했다.

## 배경 분석 (대화에서 도출)

PM이 코드를 직접 확인한 결과:

- **검출 정규식** (`opal/tools/state-tool/state_tool.py:1320-1322`):
  ```python
  # (L1319 주석) 코드 사용 패턴만 정규식 매칭; 단순 "mock" 단어/설명 문구는 제외
  _MOCK_CODE_PATTERNS = re.compile(r"MagicMock|unittest\.mock|@patch\b|mock\.patch|Mock\(|@mock\.")
  ```
- 6개 대안 중 **5개는 코드 토큰 동반**(`.`/`@`/`(`)이라 산문에 안 나오지만, **첫 항목 `MagicMock`만 "맨 단어"** — 점·괄호·@ 없이 단어가 어디 있든 매칭된다. 주석의 *"단순 단어 제외"* 의도와 모순.
- **호출 지점** (`state_tool.py:1013-1020`): `mark`가 `stage == "TEST"` 행을 done 처리할 때 TEST-SCENARIO.md 전체를 자동 스캔(`_check_mock_patterns`). `verify --check`(`:1632~`)도 동일 패턴 사용.
- **오탐 대상**: op-dev-test-scenario SKILL §7 표준 PM Gate 문구 `"mock/patch/MagicMock 등 시나리오 본문에 부재"`의 `MagicMock` 단어. → 이 SKILL로 작성한 모든 opd/opds 태스크가 TEST mark에서 구조적으로 걸릴 잠재.
- **중복 단서**: `Mock\(` 패턴이 이미 `MagicMock()`의 끝부분 `Mock(`을 매칭하므로, 실제 `MagicMock()` 코드는 `Mock\(`로도 검출된다 → `MagicMock`(맨 단어) 대안은 잉여이거나 호출 형태로 한정해야 한다.

## 확정된 설계 방향 (대화에서 합의)

- 정규식 첫 대안 `MagicMock`을 **코드 호출 형태로 한정**(`MagicMock\(`)하거나, `Mock\(`로 커버되는 잉여 대안임을 확인하고 제거한다. (최종 방식은 PLAN에서 결정)
- 나머지 5개 대안(`unittest\.mock`/`@patch\b`/`mock\.patch`/`Mock\(`/`@mock\.`)은 코드 형태라 **불변**.
- 실제 mock 코드(`MagicMock()`, `from unittest.mock import ...`, `@patch`, `Mock()` 등)는 **계속 검출**되어야 한다 (가드 본질 유지).

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | `_MOCK_CODE_PATTERNS`의 `MagicMock` 단어 오탐 제거 — 코드 호출 형태로 한정/잉여 제거, 실제 mock 코드 검출은 유지 | - | `state_tool.py:1320-1322` |
| 범위 | **포함(스코프 확대 — 캡틴 B 결정 2026-06-21)**: ①`state_tool.py` 정규식 수정(산문 `MagicMock` 단어 오탐=#1) ②`_check_mock_patterns` 검사 로직에 **마크다운 구조 인식/메타 예외** 추가(가드가 mock 검증·문서화 텍스트를 차단하는 메타-순환=#2) + `tests/test_state_tool.py` RED-first 케이스. **제외**: op-dev-test-scenario SKILL 문구 변경(도구 수정이 근본), 033 산출물 소급 변경 | - | #2는 034 PLAN 재검토 중 PM 실측(TEST-SCENARIO 자기 가드 22건 매칭)으로 발견 |
| 제약 | ①헌법 §4 가드 본질 유지(실제 mock 코드 계속 검출) ②RED-first 강제(버го 수정=회귀 방지 트랙) ③배포 경계(소스 수정 후 install 재배포, `~/.opal/` 직접 수정 금지) ④변경이력 행 추가 | - | `red-first.md §1.5` 버그 수정=강제 |
| 완료기준 | (1)`MagicMock` 단어만 포함한 산문(SKILL 표준 문구)은 검출 통과 (2)실제 `MagicMock()`/`@patch`/`unittest.mock` 등 코드는 여전히 검출 (3)기존 `test_state_tool.py` 회귀 0 + 신규 RED→GREEN 케이스 통과 | - | pytest 실측 |

## 요구사항

- [ ] **R-1 (정규식 수정)**: `_MOCK_CODE_PATTERNS`(`state_tool.py:1320-1322`)에서 `MagicMock` 맨 단어 대안을 코드 호출 형태(`MagicMock\(`)로 한정하거나, `Mock\(`로 커버되는 잉여 대안으로 판단 시 제거한다. **무엇을**: 정규식 첫 대안 수정. **어디에**: `opal/tools/state-tool/state_tool.py:1320-1322`. **왜**: 산문 `MagicMock` 단어 오탐(배경 분석). **AC**: `MagicMock`(단어)만 있는 라인은 `_check_mock_patterns`가 비검출, `MagicMock(`/기타 코드 패턴은 검출. 변경이력(코드 @header 또는 주석) 반영.
- [ ] **R-2 (RED-first 테스트)**: `tests/test_state_tool.py`에 mock 가드 케이스를 추가한다. **무엇을**: (a)`"mock/patch/MagicMock 등 부재"` 산문 라인 → 비검출(현재 RED) (b)`x = MagicMock()` 코드 → 검출(GREEN 유지) (c)다른 5패턴 회귀. **어디에**: `tests/test_state_tool.py`. **왜**: 버그 재현·고정(회귀 방지). **AC**: 수정 전 (a) 케이스 FAIL(RED 증거), 수정 후 전체 PASS.
- [ ] **R-3 (#2 메타-순환 해결)**: `_check_mock_patterns`가 mock 가드를 검증·문서화하는 정당한 텍스트(인라인 백틱/표 설명의 코드 패턴 예시)를 오탐하지 않도록 마크다운 구조를 인식한다. **무엇을**: 검사 로직이 실제 코드(코드펜스 ``` 블록 등)와 설명 텍스트(인라인 `` ` `` 백틱·표·산문)를 구분 — 정당한 mock-검증 텍스트는 통과, 실제 "목업으로 때우는 코드"는 계속 검출(헌법 §4 본질 유지). 최적 방식(코드펜스 상태추적 / 인라인 백틱 제외 / 메타 마커)은 PLAN이 코드 분석 후 결정. **어디에**: `state_tool.py` `_check_mock_patterns`(`:1340-1346`) 또는 호출 전처리. **왜**: mock 가드를 테스트하는 태스크의 TEST 단계가 구조적으로 막히는 메타-순환(PM 실측 22건). **AC**: 034 자신의 TEST-SCENARIO.md(코드패턴 예시 포함)가 `mark`/`verify` TEST 검사를 통과(exit 0) + 코드펜스 내 실제 mock 코드는 검출 유지.

## 제약 조건

- **가드 본질 유지**: 헌법 §4 "Don't fake it" — 실제 mock 코드를 시나리오로 때우는 행위는 계속 차단해야 한다. 오탐만 제거하고 정탐은 유지.
- **RED-first 강제**: 버그 수정(회귀 방지)은 `red-first.md §1.5` 강제 트랙. RED 증거(현 정규식이 산문을 잡음) 확보 후 GREEN.
- **배포 경계**: 소스 `opal/tools/state-tool/state_tool.py` 수정 후 install 재배포해야 `~/.opal/` 배포본 발효. 배포본 직접 수정 금지.
- **최소 변경(Surgical)**: 정규식 1곳 + 테스트만. 다른 패턴·로직 변경 금지.
- **변경이력**: state_tool.py 변경 시 추적 가능 기록(주석/이력).

## 기술 스택

- Python (state_tool.py — argparse CLI), pytest (`tests/test_state_tool.py`)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | 수정 대상 — 정규식(`:1320-1322`)·호출(`:1013-1020`)·verify(`:1632~`) |
| D-2 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` | RED-first 테스트 추가 대상 |
| D-3 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` | 버그 수정=RED-first 강제 트랙(§1.5) |
| D-4 | 설계 | op-dev-test-scenario SKILL | `~/.opal/skills/op-dev-test-scenario/SKILL.md` | 오탐된 표준 PM Gate 문구(§7) 출처 |
| D-5 | 참조 | brain concept | `.opal/brain/pages/concept/state-tool-mock-guard-skill-false-positive.md` | 033에서 기록한 버그 분석 |
