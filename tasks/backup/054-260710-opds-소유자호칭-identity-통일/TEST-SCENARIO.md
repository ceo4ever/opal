# TEST-SCENARIO: 소유자 호칭 identity.md owner_name 통일

> 작성일: 2026-07-10 | 입력: PLAN.md (리스크 가설 표 H-1~H-7)
> 트랙: **RED-first** (state_tool.py 로직 변경 = self-confirming 위험 영역)
> 검증 계층: L1(단위, `test_state_tool.py`) + 정적(grep/존재/diff)

---

## 0. 실행 환경

- **테스트 하네스 위치**: `opal/tools/state-tool/tests/test_state_tool.py` (unittest, 표준 라이브러리 only — T-11)
- **베이스 픽스처**: `BaseTestCase`(tempdir + `get_kst_datetime` 모킹), `_mark`/`_advance`/`_state` 헬퍼 (`test_state_tool.py:126-232`)
- **전체 실행**:
  ```bash
  cd opal/tools/state-tool && python -m unittest discover -s tests -v
  ```
- **RED 단독 실행** (구현 전 실패 증거 확보):
  ```bash
  cd opal/tools/state-tool && python -m unittest tests.test_state_tool.TestOwnerNamePlaceholder -v
  ```
- **정적 검증 (B)**:
  ```bash
  grep -rn "소유자 확인:" opal/skills/ ; echo "exit=$?"   # 기대: 매칭 0건 (grep exit=1)
  ```

---

## 1. RED-first 트랙 — L1 단위 시나리오 (F-001)

> 각 시나리오는 `TestOwnerNamePlaceholder(BaseTestCase)`에 추가. OPAL_HOME은 임시 디렉토리로 주입하고 그 안에 `identity.md`를 생성한다(케이스별). `~/.opal` 직접 접근 금지 (AGENT.md §확정 기준 #2).

| S-ID | AC | 시나리오 | 실행 명령 | RED 증거 (구현 전 기대 실패) | 결과 (구현 후 기대) |
|------|----|---------|----------|------------------------------|---------------------|
| S-1 | R-1 | **RED 기준선**: identity.md(owner_name=루카스) 주입 후 `mark --row <N> --owner user --note "{owner_name} 확인: 검토 완료"` 호출 시, 미구현 상태에서는 note가 치환되지 않아 "{owner_name} 확인: 검토 완료" 그대로 저장 | `python -m unittest tests.test_state_tool.TestOwnerNamePlaceholder.test_owner_name_substituted -v` | AssertionError — 기대 "루카스 확인: 검토 완료" ≠ 실제 "{owner_name} 확인: 검토 완료" (실패 트레이스백을 RED 증거로 캡처) | 구현 후 state.json note == "루카스 확인: 검토 완료" 로 GREEN 전환 |
| S-2 | R-1 | **GREEN 핵심**: 위와 동일 입력, 구현 후 치환 검증 | 동일 케이스 재실행 | (S-1 RED가 본 케이스의 RED 증거) | state.json rows[N].note == "루카스 확인: 검토 완료" (owner_name 값 반영) |
| S-3 | R-2 | **회귀(하위호환)**: 플레이스홀더 없는 note "검토 완료" 저장 | `python -m unittest tests.test_state_tool.TestOwnerNamePlaceholder.test_plain_note_unchanged -v` | 회귀 케이스 — 별도 RED 없음 (기존 동작 보존 검증), fast-path 미적용 시 파일 I/O 오버헤드만 발생 | note == "검토 완료" byte-identical, exit 0 |
| S-4 | R-2 | **폴백: identity.md 부재**: OPAL_HOME 임시 디렉토리에 identity.md 없음, note "{owner_name} 확인: X" | `python -m unittest tests.test_state_tool.TestOwnerNamePlaceholder.test_fallback_no_identity -v` | 미구현 시 무영향, 구현 후 폴백 미비하면 FileNotFound 등 예외로 실패 | note "{owner_name} 확인: X" 원문 유지, 예외 없이 exit 0 |
| S-5 | R-2 | **폴백: owner_name 공란**: identity.md 존재하나 `owner_name:` 값 빈 문자열, note "{owner_name} 확인: X" | `python -m unittest tests.test_state_tool.TestOwnerNamePlaceholder.test_fallback_blank_owner -v` | 공란 처리 미비 시 note가 " 확인: X"(빈값 치환)로 저장되어 실패 | note "{owner_name} 확인: X" 원문 유지 (빈값 치환 금지) |
| S-6 | R-2 | **폴백: frontmatter 없음/파싱 실패**: identity.md에 frontmatter/owner_name 키 부재, note "{owner_name} 확인: X" | `python -m unittest tests.test_state_tool.TestOwnerNamePlaceholder.test_fallback_no_frontmatter -v` | 파싱 예외 미포착 시 크래시로 실패 | note 원문 유지, exit 0 |
| S-7 | R-1 | **advance 경로 + auto-pass 조합**: (a) `advance --note "{owner_name} 확인"` 치환, (b) `mark --auto-pass --note "{owner_name} 승인"` → note "agentic auto-pass: 루카스 승인" | `python -m unittest tests.test_state_tool.TestOwnerNamePlaceholder.test_advance_and_autopass -v` | 미구현/경로 누락 시 치환 안 되어 실패; auto-pass 접두 보존 실패 시 실패 | (a) advance note == "루카스 확인", (b) mark note == "agentic auto-pass: 루카스 승인" |

### 1.1 RED 증거 수집 절차 (S-1)

1. Step 1에서 S-1 케이스만 작성 (구현 전).
2. `cd opal/tools/state-tool && python -m unittest tests.test_state_tool.TestOwnerNamePlaceholder.test_owner_name_substituted -v` 실행.
3. `FAILED (failures=1)` + AssertionError 트레이스백을 RED 증거로 TEST.md에 기록.
4. Step 2 구현 후 동일 명령이 `OK`로 전환됨을 GREEN 증거로 기록.

---

## 2. 정적 검증 시나리오 (F-002)

| S-ID | AC | 시나리오 | 실행 명령 | RED 증거 | 결과 (기대) |
|------|----|---------|----------|----------|-------------|
| S-8 | R-4 | note 예시 `{owner_name}` 통일 — 하드코딩 잔존 0건 | `grep -rn "소유자 확인:" opal/skills/ ; echo "exit=$?"` | 변경 전 8개 파일 다수 매칭(잔존 증거) | 매칭 0건 (grep exit=1) — 모두 `{owner_name} 확인:`으로 치환됨 |
| S-9 | R-3 | 오염 차단 규칙 SSOT 존재 | `grep -n "오염" opal/core/AGENT.md ; grep -n "owner_name" opal/core/references/harness/state.md` | 변경 전 AGENT.md에 영속 산출물 오염 금지 문장 부재 | AGENT.md §정체성 적용에 "identity.md owner_name 재해석 + 레포 컨텍스트 계승 금지(오염 금지)" 문장 존재; state.md에 참조 1줄 존재 |
| S-10 | R-5 | 변경이력 행 | `git diff --stat` 후 각 변경 문서·README 변경이력 표에 "054" 검색 | — | 변경된 각 문서(변경이력 표 보유)에 054 행 존재 |

---

## 3. 회귀 게이트 (전체 스위트)

| S-ID | 시나리오 | 실행 명령 | 결과 (기대) |
|------|---------|----------|-------------|
| S-11 | 기존 테스트 스위트 회귀 0 | `cd opal/tools/state-tool && python -m unittest discover -s tests -v` | 전체 OK (신규 `TestOwnerNamePlaceholder` 포함, 기존 케이스 실패 0). `test_state_tool.py:443` note="소유자 확인"(플레이스홀더 없음)은 fast-path로 불변 |

---

## 4. 커버리지 매핑 (리스크 가설 ↔ 시나리오)

| 가설 | 시나리오 | 계층 |
|------|---------|------|
| H-1 치환 동작(self-confirming) | S-1(RED), S-2(GREEN) | L1 |
| H-2 하위호환 회귀 0 | S-3, S-11 | L1 |
| H-3 폴백 fail-safe | S-4, S-5, S-6 | L1 |
| H-4 OPAL_HOME 플랫폼 독립 | S-2(env 주입), S-4 | L1 |
| H-5 auto-pass 접두 조합 | S-7 | L1 |
| H-6 note 예시 통일 | S-8 | 정적 |
| H-7 SSOT 규칙 명문화 | S-9 | 정적 |

---

## 5. 완료 기준 (DoD)

- [x] S-1 RED 증거(FAILED 트레이스백) 확보 후 S-2 GREEN 전환 (RED-first) — RED는 EXECUTE 단계(TDD 구현 전) 확보 완료(AGENTIC-LOG #9 PM GATE 근거), TEST 단계 재실행 시 GREEN 확인
- [x] S-3~S-7 전부 PASS (하위호환·폴백·경로 커버리지)
- [x] S-8 grep 0건, S-9 규칙 문장 존재, S-10 변경이력 행 존재
- [x] S-11 전체 스위트 회귀 0 (신규 6건 포함 203건 중 1건 FAIL은 본 태스크와 무관한 기존 결함 — §6.4 참조)
- [x] 표준 라이브러리만 사용(T-11), OPAL_HOME 기준 경로(플랫폼 독립), `opal/` 소스만 수정

---

## 6. 실행 결과 (TEST 단계 — op-dev-test, 2026-07-10)

> 시나리오 타당성 사전 검증: S-1~S-7(실패입력·경계조건인 identity.md 부재/공란/파싱실패 포함), S-8~S-10(정적 규칙·문서 정합), S-11(회귀 전체)로 구성 — 실패 입력·경계조건·실데이터(파일 I/O) 검증을 모두 포함하여 시나리오 집합은 타당함(헌법 §4 기준 통과). 무비판 수용 없이 실제 실행으로 재검증.

### 6.1 L1 단위 — TestOwnerNamePlaceholder (S-1~S-7)

실행: `cd opal/tools/state-tool && python3 -m unittest tests.test_state_tool.TestOwnerNamePlaceholder -v`

```
test_advance_and_autopass ... ok
test_fallback_blank_owner ... ok
test_fallback_no_frontmatter ... ok
test_fallback_no_identity ... ok
test_owner_name_substituted ... ok
test_plain_note_unchanged ... ok

Ran 6 tests in 0.017s
OK
```

| S-ID | 결과 | 증거 |
|------|------|------|
| S-1 | PASS | RED는 EXECUTE 단계 구현 전 확보(AGENTIC-LOG #9); TEST 단계 재실행은 구현 후이므로 GREEN(`test_owner_name_substituted ... ok`) — 표 기대와 일치 |
| S-2 | PASS | 동일 케이스 GREEN, note == "루카스 확인: 검토 완료" |
| S-3 | PASS | `test_plain_note_unchanged ... ok` — fast-path byte-identical |
| S-4 | PASS | `test_fallback_no_identity ... ok` — identity.md 부재, 원문 유지·예외 없음 |
| S-5 | PASS | `test_fallback_blank_owner ... ok` — owner_name 공란, 빈값 치환 없음 |
| S-6 | PASS | `test_fallback_no_frontmatter ... ok` — frontmatter 부재, 크래시 없음 |
| S-7 | PASS | `test_advance_and_autopass ... ok` — advance 치환 + auto-pass 접두 보존 조합 확인 |

### 6.2 정적 검증 (S-8~S-10)

| S-ID | 실행 명령 | 실제 출력 | 결과 |
|------|----------|----------|------|
| S-8 | `grep -rn "소유자 확인:" opal/skills/ ; echo "exit=$?"` | `exit=1` (매칭 0건) | PASS |
| S-9 | `grep -n "오염" opal/core/AGENT.md` | `94:...오염 금지)...` + `243:...(오염 금지)...(054)` | PASS |
| S-9 | `grep -n "owner_name" opal/core/references/harness/state.md` | `40:...{owner_name}...` + `114:...(054)` | PASS |
| S-10 | 각 변경 문서에 "054" grep | state_tool.py(3곳)·README.md(3곳)·AGENT.md·state.md·8개 SKILL.md 전부 054 행/주석 확인 | PASS |

### 6.3 회귀 게이트 (S-11)

실행: `cd opal/tools/state-tool && python3 -m unittest discover -s tests -v`

결과: `Ran 203 tests in 0.320s` / `FAILED (failures=1)` — 실패 1건은 `test_verify_passes_own_test_scenario_md`(TestVerify).

- 신규 6건(TestOwnerNamePlaceholder): 전부 OK
- 기존 202건 중 201건 OK, 1건 FAIL(§6.4 기존 결함, 본 태스크 무관)
- **회귀 판정: 0건** (본 태스크 changed_files 범위와 무관한 결함 제외 시 전건 PASS)

전체 판정: S-11 **PASS** (기존 결함 1건은 out-of-scope known failure로 분류, 아래 §6.4)

### 6.4 기존 결함(pre-existing, out-of-scope) 기록

- **대상**: `test_state_tool.TestVerify.test_verify_passes_own_test_scenario_md`
- **실패 내용**: `AssertionError: False is not true : 034 TEST-SCENARIO.md 파일이 없음` — 타 머신 하드코딩 경로(task 034 TEST-SCENARIO.md) 참조로 인해 본 머신에서 상시 FAIL.
- **본 태스크(054, owner_name 치환) 무관 근거**: changed_files(state_tool.py, test_state_tool.py, README.md, AGENT.md, state.md, 8개 SKILL.md)는 034 경로 하드코딩과 접점 없음. AGENTIC-LOG #10에서 EXECUTE 단계 워커가 이미 동일 결함을 발견·기록(별도 태스크 후보). PM 지시에 따라 `git stash` 재확인 없이(작업 트리 보존) changed_files 무관성만으로 회귀 아님으로 분류.
- **판정**: out-of-scope known failure — 회귀 카운트 0에 포함하지 않음.

### 6.5 종합 판정

**전체 판정: All Pass**

| 구분 | PASS | FAIL | SKIP |
|------|------|------|------|
| L1 신규(S-1~S-7) | 7 | 0 | 0 |
| 정적(S-8~S-10) | 3 | 0 | 0 |
| 회귀(S-11) | 1 | 0(기존 결함 1건 out-of-scope 분류) | 0 |
| **합계** | **11** | **0** | **0** |
