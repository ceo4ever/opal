# PLAN: E2E 테스트 실행 개선 — test-tool playwright 폴백 + TEST-SCENARIO 배선 + OPAL_TEST_TOOLS_GLOBAL 등록

> 작성일: 2026-06-24 | 입력: TASK.md (ANALYSIS.md 없음)
> 모드: Multi-Feature (기능 5개)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

test-tool 배포 후에도 다른 프로젝트의 TEST 단계에서 E2E가 실행되지 않는 3개 구조적 원인(① M2 시나리오 미작성 ② playwright fallback stub ③ OPAL_TEST_TOOLS_GLOBAL 미설정)을 5개 파일 수정으로 해소한다. 코드 1파일(e2e_adapter.py)·문서 3파일(가이드/SKILL/AGENT)·설치 스크립트 1파일(install-mac.sh)에 한정한 외과적 변경이며, 기존 동작 유지 + 추가만 한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | test-scenario-guide.md M2 트리거 기준 명확화 | TASK F-001 | P0 | 없음 |
| F-002 | op-dev-test-scenario SKILL.md PM Gate FE→M2 체크 항목 추가 | TASK F-002 | P0 | F-001 |
| F-003 | e2e_adapter.py playwright fallback `mcp_action` 필드 추가 | TASK F-003 | P0 | 없음 |
| F-004 | opal-test-agent AGENT.md playwright MCP 실행 절차 명시 | TASK F-004 | P0 | F-003 |
| F-005 | install-mac.sh OPAL_TEST_TOOLS_GLOBAL shell rc 등록 | TASK F-005 | P0 | 없음 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 ── F-002        (원인 1: M2 시나리오 작성 기준)
F-003 ── F-004        (원인 2: playwright fallback 배선)
F-005                 (원인 3: 글로벌 템플릿 env var)
```

세 갈래는 서로 독립이며 각 갈래 내부만 순차 의존이다.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-003 `e2e_adapter.py` `_run_playwright_fallback` 반환 dict | 기존 소비자(`test_tool.py` `cmd_integration`, opal-test-agent)가 읽는 `e2e` dict 키 집합 — 기존 키(`driver`/`fallback_reason`/`status`/`url`) 유지 + `mcp_action`/`mcp_url` 추가. 키 누락/오타 시 F-004 절차가 동작 안 함 | P1 | L1 (단위) | S-1 후보 |
| H-2 | F-003 `_run_playwright_fallback` 호출 경로 2곳 (`has_cmux=False` line 170-179, `FALLBACK_CODES` line 190-199) | 두 호출 경로 모두 동일 dict 형태를 반환해야 함 — 한쪽만 수정 시 cmux 미구성 경로에서 `mcp_action` 누락 | P1 | L1 (단위, 양 경로 파라미터화) | S-2 후보 |
| H-3 | F-003 기존 회귀 — `escalate=true`(ESCALATE_CODES) 경로는 폴백 금지 계약 유지 | mcp_action 필드 추가가 에스컬레이션 경로에 새지 않아야 함(폴백 금지 — 헌법 플랫폼 가드) | P0 | L1 (회귀, 에스컬레이션 5종 driver≠playwright) | S-3 후보 |
| H-4 | F-005 `install-mac.sh` shell rc 등록 블록 | 멱등성 계약 — 재실행 시 중복 export 라인 누적 금지(마커 가드). 잘못된 export 경로(`~` 미전개 등)로 resolver가 글로벌 템플릿을 못 읽음 | P1 | L2 (실 rc 파일 append 후 재실행 → 중복 없음 re-read) | S-4 후보 |
| H-5 | F-001/F-002 문서 트리거 기준 | M2 의무 기준 표가 모호하면 작성자가 여전히 M2 누락. 검증 계층 결정 규칙 표(가이드 §Step 3)와 변경영역×M 매핑 표(가이드 §Step 3-b)의 FE 행이 정합해야 함 | P1 | L1 (산출물 검사 — 문서 내 grep + 정합성) | S-5 후보 |
| H-6 | F-004 AGENT.md 절차 ↔ F-003 반환 필드 정합 | AGENT.md가 참조하는 필드명(`mcp_action`/`mcp_url`)이 e2e_adapter.py 실제 반환 키와 불일치 시 절차가 공허해짐 (FE↔BE 용어 일관성, citation-rules.md §7) | P1 | L1 (산출물 검사 — 필드명 교차 일치) | S-6 후보 |

**[MUST]** `opal/core/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names. Don't improve adjacent code." → 명시된 5파일만 수정, 인접 코드 개선·리팩터링 금지.

**[MUST]** `opal/core/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement. No speculative abstraction." → 기존 동작 유지 + 필드/절차 추가만.

**[MUST]** `opal/tools/test-tool/lib/e2e_adapter.py:6`: "uname/cmux --version 하드코딩 분기 금지 — cmux-tool 에러코드 소비(어댑터)로만 플랫폼 가드 흡수." → mcp_action 필드 추가는 에러코드 소비 결과에 부가하는 것이며, 플랫폼 분기 로직을 신설하지 않는다.

---

## 2. 기능별 분석

### F-001: test-scenario-guide.md M2 트리거 기준 명확화

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | TEST-SCENARIO.md 작성 가이드 — 계층(L)·실행방식(M) 결정 규칙 SSOT | 수정 |

#### 2.1.2 현재 구현

- `test-scenario-guide.md:50-58` "계층 결정 규칙 표" — 변경 영역 7종 × L1/L2/L3 의무. FE 화면/컴포넌트 행은 `L2 의무 = API 연동 흐름`, `L3 의무 = 사용자 시각 확인 [SUPERVISOR]` (`test-scenario-guide.md:56`).
- `test-scenario-guide.md:75-85` "변경 영역 7종 × M1/M2/M3 매핑 표" — FE 화면/컴포넌트 행 M2 = "cmux 1순위 → playwright 폴백" (`test-scenario-guide.md:83`).
- `test-scenario-guide.md:87-94` "검증 깊이 × 실행 방식 가능 조합" — L1×M2 = `—` (불가), L2×M2 = `✓` (`test-scenario-guide.md:91-93`). **이 표에 L1×M2가 불가인 이유 주석이 없다** → 작성자가 "FE 변경인데 L1만 잡으면 M2를 못 쓴다"는 인과를 이해하지 못해 M2 시나리오 자체를 누락.
- **결손**: M2가 *의무*인 경우(FE 변경 포함 시)를 명시한 열/주석이 없음. 매핑 표는 "M2 예시"만 제시하고 "언제 M2가 필수인가"를 말하지 않는다 (→ 원인 1).

#### 2.1.3 영향 범위

- 상위 소비자: `op-dev-test-scenario/SKILL.md` Step 1이 이 가이드를 Read하여 작성 (`SKILL.md:31-37`). F-002와 직접 연동.
- 하위 영향: 작성된 TEST-SCENARIO.md의 M2 시나리오 유무 → opal-test-agent의 `test-tool integration` 호출 여부(`AGENT.md:170`)를 좌우.
- 정합성 대상: 같은 파일 내 계층 결정 규칙 표(§Step 3)와 변경영역×M 매핑 표(§Step 3-b)의 FE 행이 일관해야 함 (H-5).

---

### F-002: op-dev-test-scenario SKILL.md PM Gate FE→M2 체크 항목 추가

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/op-dev-test-scenario/SKILL.md` | TEST-SCENARIO 작성 스킬 — 통일 형식 + PM Gate 체크리스트 + 작성 체크리스트 | 수정 |

#### 2.2.2 현재 구현

- `SKILL.md:155-164` "PM Gate 체크 (7대 강제 룰)" — mock 부재/사전데이터/Given-When-Then/가설매핑/계층명시/SUPERVISOR/실행방식(M) 8개 체크박스. **"FE 변경 시 M2 시나리오 포함 여부"를 강제하는 항목이 없다** (→ 원인 1).
- `SKILL.md:164` 마지막 항목: "모든 시나리오에 실행 방식(M1/M2/M3) 명시" — *명시*만 요구하고 *FE 변경이면 M2가 존재해야 한다*는 의무는 없음.
- `SKILL.md:175-189` "시나리오 작성 체크리스트" — 자체 검증용. test-tool resolve 호출은 가이드 §Step 4-a가 SSOT (`test-scenario-guide.md:138-144`)이므로 SKILL.md는 PM Gate 체크 항목 추가에 집중.

#### 2.2.3 영향 범위

- 상위: `opal-pilot-dev` STEP 3.5 PM이 이 PM Gate로 TEST-SCENARIO.md를 검수 (`SKILL.md:13`).
- 하위: PM Gate 통과 = EXECUTE 진입 허가 (`SKILL.md:190-192`). 체크 항목 추가 시 FE 변경 태스크는 M2 누락 시 Gate FAIL.
- F-001 의존: 가이드의 M2 의무 기준이 먼저 명확해야 PM Gate 체크가 판단 근거를 가짐.

---

### F-003: e2e_adapter.py playwright fallback `mcp_action` 필드 추가

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/test-tool/lib/e2e_adapter.py` | cmux-tool 에러코드 소비 → 폴백/에스컬레이션 결정 어댑터 | 수정 |
| BE | `opal/tools/test-tool/tests/test_test_tool.py` | test-tool 행위 계약 테스트 (mcp_action 단언 추가) | 수정 |

#### 2.3.2 현재 구현

- `e2e_adapter.py:119-132` `_run_playwright_fallback(url, fallback_reason)` — 현재 반환: `{"driver":"playwright", "fallback_reason":<reason>, "status":"fallback", "url":<url>}`. docstring(`:124`): "실제 playwright 호출은 구현 범위 밖 … 실제 playwright 실행은 오케스트레이터/캡틴 책임."
- 호출 경로 2곳 (H-2):
  - `e2e_adapter.py:172` — `has_cmux=False` (cmux 미구성), reason="cmux not configured"
  - `e2e_adapter.py:192` — `FALLBACK_CODES` 매칭 시, reason=error_code
- 반환 dict가 `e2e` 키로 묶여 `cmd_integration`(`test_tool.py:170-187`)에서 JSON 출력 → opal-test-agent가 `result["e2e"]`를 읽는다.
- 기존 테스트 계약 (`test_test_tool.py:555-577` `_assert_playwright_fallback`): `e2e.driver == "playwright"` + `fallback_reason` 키 존재 + reason에 error_code 포함만 단언. **`mcp_action` 추가는 기존 단언을 깨지 않음(additive).**
- `test_test_tool.py:510`: "기대 결과(driver=playwright on fallback)는 변경 없음 — 호출 메커니즘만 수정" — 기존 폴백 계약 안정성 명시.

#### 2.3.3 영향 범위

- 상위 소비자: `test_tool.py` `cmd_integration`(`:170`) — 반환 dict를 그대로 JSON 직렬화. 키 추가는 투명(키 화이트리스트 없음).
- 하위 소비자: opal-test-agent(F-004) — `e2e.mcp_action`/`e2e.mcp_url`을 읽어 playwright MCP 호출. F-004와 필드명 정합 필수 (H-6).
- 회귀 주의: ESCALATE_CODES 경로(`:200-221`)는 `_run_playwright_fallback`을 호출하지 않으므로 mcp_action이 새지 않아야 함 (H-3) — 이 경로는 `driver:None, status:escalated`를 직접 구성하므로 수정 불필요.

---

### F-004: opal-test-agent AGENT.md playwright MCP 실행 절차 명시

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/agents/opal-test-agent/AGENT.md` | 테스트 워커 — M1/M2/M3 처리 절차 SSOT | 수정 |

#### 2.4.2 현재 구현

- `AGENT.md:170` M2 처리 절차: "`test-tool integration --scope fe|be`을 호출하여 cmux 1순위 → 미가용 시 playwright 폴백·실DB를 집행한다. 도구가 폴백/에스컬레이션을 JSON으로 반환한다. 에스컬레이션 … 또는 도구 환경 미비 시 즉시 PM에 반환." **playwright 폴백 JSON(`driver:playwright`)을 받은 *후* 무엇을 하는지가 없다** → 폴백 결정만 받고 실제 playwright MCP를 호출하는 절차 부재 (→ 원인 2).
- `AGENT.md:172`: "M2 자동 실행이 환경·도구 미비로 불가 시 즉시 PM 반환." — fallback을 "환경 미비"로 오인하여 PM 반환할 위험. fallback은 환경 미비가 아니라 "cmux 대신 playwright MCP로 진행" 신호임을 구분해야 함.
- playwright MCP 도구는 디스패치 시스템 reminder에 노출됨: `mcp__playwright__browser_navigate`, `mcp__playwright__browser_snapshot`, `mcp__playwright__browser_take_screenshot` 등.

#### 2.4.3 영향 범위

- 상위: `opal-pilot-dev` TEST 단계 PM이 이 에이전트를 디스패치 (`AGENT.md:1-9`).
- 하위: TEST-SCENARIO.md M2 시나리오의 결과 채움 — playwright MCP 실행 출력이 증거가 됨(헌법 §4 "Completion requires evidence").
- F-003 의존: 절차가 참조하는 필드명(`e2e.mcp_action`/`e2e.mcp_url`)이 F-003 반환 키와 정확히 일치해야 함 (H-6).

---

### F-005: install-mac.sh OPAL_TEST_TOOLS_GLOBAL shell rc 등록

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/install-mac.sh` | OPAL 설치 스크립트 — shell rc 등록·자산 배포 | 수정 |

#### 2.5.2 현재 구현

- `resolver.py:188-196` 글로벌 템플릿 해석: env var `OPAL_TEST_TOOLS_GLOBAL` 미설정 시 `global_yaml_path = None` → 글로벌 탐색 건너뜀 → 추론(infer) 폴백. 주석(`:189-191`): "프로덕션 install은 env var을 설정한다." **그러나 install-mac.sh에 해당 등록 코드가 없다** (→ 원인 3).
- `install-mac.sh:884-906` `register_path_in_shell_rc(bin_dir)` — 기존 PATH 등록 패턴. 멱등 마커 블록(`# === OPAL PATH ===` ~ `# === OPAL PATH END ===`)을 rc 파일 3종(`.zshrc`/`.bashrc`/`.profile`)에 1회 append. `grep -qF "$marker"`로 중복 가드 (`:893`).
- `install-mac.sh:846-879` `install_opal_bin()` — `register_path_in_shell_rc` 호출 지점(`:859`). install_opal()에서 `:1125`에 호출됨.
- `~/.opal/templates/test-tools.yaml`은 이미 배포됨(`install_opal`의 `templates` clean_dirs 포함, `:931`) — env var만 등록하면 resolver가 글로벌 소스로 인식.

#### 2.5.3 영향 범위

- 상위: `main()` → `install_opal()`(`:1673`) → `install_opal_bin()`(`:1125`).
- 하위: 다른 프로젝트에서 `test-tool resolve` 시 `source:"global"` 경로 활성화 → `~/.opal/templates/test-tools.yaml`의 cmux/playwright tier가 로드됨 → integration 호출 가능.
- 회귀 주의: 멱등성(H-4) — 재설치 시 중복 export 라인 누적 금지. 기존 `register_path_in_shell_rc` 마커 패턴을 재사용.

---

## 3. 기능별 설계

### F-001: test-scenario-guide.md M2 트리거 기준 명확화

#### 3.1.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 가이드 | ① 변경영역×M 매핑 표에 "M2 의무" 판단 기준 1행 추가(FE 관련 변경 포함 시 L2/M2 의무) ② 검증깊이×실행방식 조합표(L1×M2=`—`)에 불가 사유 1줄 주석 추가 | (→ D-2 §Step 3-b) |

#### 3.1.2 API·데이터 모델·화면 설계

해당 없음 (문서 변경). 아래 2개 편집 지점을 명세한다:

**편집 1 — 변경영역×M 매핑 표 보강 (`test-scenario-guide.md:75-85`)**

표 직후 또는 표 헤더 근처에 "M2 의무 트리거" 기준을 명문화한다. FE 관련 변경(FE 화면·컴포넌트·인증/인가·외부 API 연동)이 변경 영역에 **포함되면 L2/M2 시나리오를 의무로 포함**한다는 규칙을 추가한다. 현행 표는 영역별 "M2 예시"만 제시하므로(`test-scenario-guide.md:83-85`), 그 아래에 다음 취지의 명시 문구를 둔다:

> [MUST] 변경 영역에 FE 화면/컴포넌트·인증/인가·외부 API 연동 중 하나라도 포함되면 해당 시나리오에 L2/M2(E2E 자동화)를 **의무로 포함**한다. M2 누락 = PM Gate FAIL. (DB 스키마·비즈니스 로직 단독 변경은 M2 면제.)

근거: TASK.md AC "변경 영역 매핑 표에 M2 의무 열(FE 포함 시 필수) 존재" (→ D-7 TASK §F-001 AC).

**편집 2 — L1×M2 불가 사유 주석 (`test-scenario-guide.md:87-94`)**

검증 깊이×실행 방식 조합 코드블록 직후에 1줄 주석을 추가한다:

> L1×M2가 불가(`—`)인 이유: L1(기능 단위)은 함수·컴포넌트 단위 격리 검증이라 브라우저·외부 시스템 자동화(M2)의 대상이 아니다. **FE 변경의 E2E 검증은 L2/M2로 작성**한다(L1에 M2를 얹으려다 M2 자체를 누락하는 실수 방지).

근거: TASK.md AC "L1×M2 불가 이유 1줄 주석 존재" (→ D-7 TASK §F-001 AC). 헌법 §3 Surgical — 기존 조합표 값(`✓`/`—`)은 변경하지 않고 주석만 추가.

#### 3.1.3 환경 변경
해당 없음.

#### 3.1.4 배치/마이그레이션
해당 없음. (소스 수정 후 install 배포 — F-005와 동일 install 사이클에 포함)

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | F-001 AC: M2 의무 열·주석 존재 | 산출물 검사 | 가이드에 "FE … 포함 시 … L2/M2 … 의무" 문구 존재 + L1×M2 불가 사유 1줄 주석 존재 (grep) |
| TS-002 | F-001 정합성 | 산출물 검사 | 변경영역×M 매핑 표 FE 행과 계층결정 규칙 표 FE 행이 상호 모순 없음 |

---

### F-002: op-dev-test-scenario SKILL.md PM Gate FE→M2 체크 항목 추가

#### 3.2.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 2 | `opal/skills/op-dev-test-scenario/SKILL.md` | 스킬 | "PM Gate 체크 (7대 강제 룰)" 블록(`SKILL.md:155-164`)에 "FE 변경 감지 시 M2 시나리오 포함 여부 확인" 체크박스 1개 추가 + "시나리오 작성 체크리스트"(`:175-189`)에 대응 항목 추가 | (→ D-3 §PM Gate 체크) |

#### 3.2.2 API·데이터 모델·화면 설계

해당 없음 (문서 변경). 편집 지점:

**편집 — PM Gate 체크 체크박스 추가 (`SKILL.md:155-164`)**

기존 8개 체크박스 목록 끝에 1개 추가:

> - [ ] **FE 변경 시 M2 시나리오 포함** — 변경 영역에 FE 화면/컴포넌트·인증/인가·외부 API 연동이 포함되면 L2/M2(E2E 자동화) 시나리오가 §3에 최소 1건 존재 (없으면 PM Gate FAIL — test-scenario-guide.md §Step 3-b M2 의무 트리거)

동일 취지 항목을 "시나리오 작성 체크리스트"(`SKILL.md:175-189`)에도 1줄 추가하여 작성자 자체검증과 PM Gate를 정합시킨다.

근거: TASK.md AC "PM Gate 체크리스트에 \"FE 변경 시 M2 시나리오 포함 여부 확인\" 항목 존재" (→ D-7 TASK §F-002 AC). F-001의 M2 의무 트리거 규칙을 참조 포인터로 연결 (단일 SSOT — 가이드).

#### 3.2.3 환경 변경
해당 없음.

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-003 | F-002 AC: PM Gate FE→M2 항목 존재 | 산출물 검사 | SKILL.md PM Gate 블록에 "FE 변경 시 M2 시나리오 포함" 체크박스 존재 (grep) |

---

### F-003: e2e_adapter.py playwright fallback `mcp_action` 필드 추가

#### 3.3.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 3 | `opal/tools/test-tool/lib/e2e_adapter.py` | BE | `_run_playwright_fallback` 반환 dict에 `mcp_action`/`mcp_url` 추가 + docstring 갱신 | `opal/tools/test-tool/lib/e2e_adapter.py:119-132` |
| 4 | `opal/tools/test-tool/tests/test_test_tool.py` | BE | `_assert_playwright_fallback`에 `mcp_action`/`mcp_url` 단언 추가 + cmux 미구성(`has_cmux=False`) 경로 단언 추가 | `opal/tools/test-tool/tests/test_test_tool.py:555-577` |

#### 3.3.2 API·데이터 모델·화면 설계

**함수 시그니처 (변경 없음, 반환 dict만 확장)**

```python
def _run_playwright_fallback(url: Optional[str], fallback_reason: str) -> Dict[str, Any]:
    return {
        "driver": "playwright",
        "fallback_reason": fallback_reason,
        "status": "fallback",
        "url": url,
        "mcp_action": "browser_navigate",   # 신규 — opal-test-agent가 호출할 playwright MCP 액션
        "mcp_url": url,                       # 신규 — browser_navigate 대상 URL (url과 동일값)
    }
```

설계 근거:
- 기존 4개 키(`driver`/`fallback_reason`/`status`/`url`)는 **그대로 유지** — 기존 테스트 계약 비파괴 (→ D-1:127-132, `test_test_tool.py:565-577`).
- `mcp_action` 고정값 `"browser_navigate"` — TASK.md F-003 명세 dict와 정합 (`{"driver":"playwright","status":"fallback","mcp_action":"browser_navigate","mcp_url":"<url>"}`) (→ D-7 TASK §F-003).
- `mcp_url`은 `url` 인자를 그대로 전달 — opal-test-agent가 `mcp__playwright__browser_navigate`의 url 파라미터로 사용. `url`이 `None`이면 `mcp_url`도 `None`(에이전트가 PM 반환 판단).
- [MUST] `opal/tools/test-tool/lib/e2e_adapter.py:6`: "cmux 분기는 cmux-tool 에러코드 소비로만" — 본 변경은 폴백 *결과 dict*에 필드만 부가하며 플랫폼 분기 로직을 신설하지 않음(헌법 플랫폼 독립).
- [MUST] `opal/core/PRINCIPLES.md` §3: ESCALATE_CODES 경로(`e2e_adapter.py:200-221`)는 `_run_playwright_fallback`을 호출하지 않으므로 **수정하지 않는다** (폴백 금지 계약 유지, H-3).

**docstring 갱신**: `_run_playwright_fallback` docstring(`:123-126`)의 "실제 playwright 호출은 구현 범위 밖"을 "폴백 결정 + opal-test-agent가 소비할 playwright MCP 액션(`mcp_action`/`mcp_url`)을 반환. 실제 MCP 실행은 opal-test-agent 책임(AGENT.md M2 절차)"으로 정정.

**테스트 보강 (test_test_tool.py)**:
- `_assert_playwright_fallback`(`:555-577`)에 단언 추가: `self.assertEqual(e2e.get("mcp_action"), "browser_navigate")`, `self.assertIn("mcp_url", e2e)`.
- cmux 미구성 경로(`has_cmux=False`, `e2e_adapter.py:170-179`) 단언을 신규 케이스로 추가 — test-tools.yaml에 cmux tier 없는 fixture로 `mcp_action` 반환 확인 (H-2). 케이스명 프리픽스 `[T041/L1-fallback]`.

#### 3.3.3 환경 변경
해당 없음.

#### 3.3.4 배치/마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-004 | F-003 AC: 반환 dict에 mcp_action 존재 + pytest 통과 | 기능 테스트 | FALLBACK_CODES 4종 + cmux 미구성 경로 모두 `e2e.mcp_action=="browser_navigate"` + `mcp_url` 존재. 기존 단언 비파괴 |
| TS-005 | F-003 회귀: 에스컬레이션 폴백 금지 유지 | 회귀 테스트 | ESCALATE_CODES 5종 → `driver != "playwright"`, `mcp_action` 부재, `escalate=true`, exit=7 (기존 S-7 통과 유지) |

---

### F-004: opal-test-agent AGENT.md playwright MCP 실행 절차 명시

#### 3.4.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 5 | `opal/agents/opal-test-agent/AGENT.md` | 에이전트 | M2 처리 절차(`AGENT.md:170`)에 "폴백 JSON(`driver:playwright`) 수신 후 playwright MCP 직접 호출" 단계 + browser_navigate/snapshot 예시 보강 | `opal/agents/opal-test-agent/AGENT.md:168-172` |

#### 3.4.2 API·데이터 모델·화면 설계

**편집 — M2 처리 절차 보강 (`AGENT.md:170-172`)**

기존 M2 항목(`:170`)에 fallback 수신 후 절차를 추가한다. 핵심 분기:

1. `test-tool integration` JSON의 `e2e.driver` 확인.
2. `e2e.driver == "cmux"` + `status == "pass"` → cmux가 E2E 완료. 출력을 증거로 기록.
3. `e2e.driver == "playwright"` + `status == "fallback"` → **환경 미비가 아님**. `e2e.mcp_action`(예: `browser_navigate`)과 `e2e.mcp_url`을 읽어 playwright MCP를 직접 호출하여 E2E 수행:
   - `mcp__playwright__browser_navigate` (url = `e2e.mcp_url`)
   - `mcp__playwright__browser_snapshot` 또는 `mcp__playwright__browser_take_screenshot` 으로 시나리오 기대 결과 검증 증거 캡처
   - 시나리오별 추가 인터랙션(`browser_click`/`browser_fill_form`/`browser_wait_for`)은 TEST-SCENARIO.md When/Then에 따라 수행
   - 실행 출력(snapshot/스크린샷 경로)을 시나리오 "결과/상세"에 증거로 기록 (헌법 §4 "Completion requires evidence")
4. `escalate == true` (URL·네트워크·명령 오류) 또는 `mcp_url`이 `None` → 즉시 PM 반환(자동 우회 금지).

근거: TASK.md AC "M2 섹션에 playwright MCP tool 사용 절차 및 시나리오별 browser_navigate/snapshot 사용 예시 존재" (→ D-7 TASK §F-004 AC).
- [MUST] 필드명 정합 (H-6): AGENT.md가 참조하는 `e2e.mcp_action`/`e2e.mcp_url`은 F-003 `_run_playwright_fallback` 반환 키와 **글자 그대로 일치**해야 한다 (citation-rules.md §7 FE↔BE 용어 일관성).
- 기존 "M2 자동 실행이 환경·도구 미비로 불가 시 즉시 PM 반환"(`:172`)은 유지하되, **fallback ≠ 환경 미비**임을 위 3단계로 구분 (헌법 §3 — 기존 문장 보존 + 분기 추가).

#### 3.4.3 환경 변경
해당 없음.

#### 3.4.4 배치/마이그레이션
해당 없음.

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-006 | F-004 AC: playwright MCP 절차·예시 존재 | 산출물 검사 | AGENT.md M2 섹션에 `mcp__playwright__browser_navigate`/`browser_snapshot` 예시 + `e2e.mcp_action`/`e2e.mcp_url` 참조 존재 (grep) |
| TS-007 | F-004 정합성 (H-6) | 산출물 검사 | AGENT.md의 `mcp_action`/`mcp_url` 토큰이 e2e_adapter.py 반환 키와 일치 (교차 grep) |

---

### F-005: install-mac.sh OPAL_TEST_TOOLS_GLOBAL shell rc 등록

#### 3.5.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 6 | `scripts/install-mac.sh` | 배치 | shell rc에 `export OPAL_TEST_TOOLS_GLOBAL=~/.opal/templates/test-tools.yaml` 멱등 등록 함수 추가 + `install_opal_bin`/`install_opal`에서 호출 + 변경이력 행 추가 | `scripts/install-mac.sh:884-906`, `:846-879` |

#### 3.5.2 API·데이터 모델·화면 설계

**설계 — 멱등 등록 (기존 register_path_in_shell_rc 패턴 재사용)**

기존 `register_path_in_shell_rc`(`:884-906`)의 마커 가드 패턴을 동일하게 적용한다. 두 가지 구현 옵션 중 **(A) 신규 헬퍼 함수**를 권고(기존 함수 비침습 — 헌법 §3 Surgical):

```bash
# 셸 rc 파일에 OPAL_TEST_TOOLS_GLOBAL 환경변수를 1회만 등록 (idempotent)
# 사용: register_test_tools_global_in_shell_rc
register_test_tools_global_in_shell_rc() {
    local marker="# === OPAL TEST_TOOLS_GLOBAL ==="
    local marker_end="# === OPAL TEST_TOOLS_GLOBAL END ==="
    local rc_files=("$USER_HOME/.zshrc" "$USER_HOME/.bashrc" "$USER_HOME/.profile")
    local export_line='export OPAL_TEST_TOOLS_GLOBAL="$HOME/.opal/templates/test-tools.yaml"'

    for rc in "${rc_files[@]}"; do
        [[ -f "$rc" ]] || continue
        if grep -qF "$marker" "$rc"; then
            success "OPAL_TEST_TOOLS_GLOBAL 이미 등록됨: $rc"
            continue
        fi
        printf '\n%s\n%s\n%s\n' "$marker" "$export_line" "$marker_end" >> "$rc"
        success "OPAL_TEST_TOOLS_GLOBAL 등록 → $rc"
    done
}
```

호출 지점: `install_opal_bin()` 내 `register_path_in_shell_rc "$bin_dir"` 직후(`:859`)에 `register_test_tools_global_in_shell_rc` 1줄 추가. (동일 함수에서 shell rc를 다루므로 응집도 높음.)

설계 근거:
- export 값에 리터럴 `$HOME`을 따옴표로 보존(`"$HOME/.opal/..."`) — rc 로드 시점에 전개되어 사용자별 홈 경로로 해석. (`~`는 큰따옴표 안에서 미전개되므로 `$HOME` 사용 — H-4 잘못된 경로 방지.) resolver는 `os.environ.get("OPAL_TEST_TOOLS_GLOBAL")`로 전개된 절대 경로를 받음 (`resolver.py:192`).
- [MUST] 멱등성 (H-4): `grep -qF "$marker"` 가드로 재실행 시 중복 append 방지 — 기존 `register_path_in_shell_rc`(`:893`)와 동일 패턴.
- [MUST] `opal/core/PRINCIPLES.md` §2 Simplicity: 기존 PATH 등록 패턴을 복제하되 새 추상화 도입 안 함(단일 목적 함수). §3 Surgical: 기존 `register_path_in_shell_rc` 본문은 건드리지 않음.
- TASK.md AC: "install-mac.sh 실행 후 `~/.zshrc`(또는 `.bash_profile`)에 `export OPAL_TEST_TOOLS_GLOBAL=~/.opal/templates/test-tools.yaml` 행 존재" (→ D-7 TASK §F-005 AC). 실제 등록 파일은 기존 패턴과 정합하여 `.zshrc`/`.bashrc`/`.profile` 3종.

#### 3.5.3 환경 변경

- 등록 환경변수: `OPAL_TEST_TOOLS_GLOBAL=$HOME/.opal/templates/test-tools.yaml` (사용자 shell rc).
- 신규 마커: `# === OPAL TEST_TOOLS_GLOBAL ===` / `# === OPAL TEST_TOOLS_GLOBAL END ===`.

#### 3.5.4 배치/마이그레이션

- install-mac.sh 재실행으로 적용. 기 설치 사용자는 재설치 또는 수동 export 1줄 추가로 활성화 (CLOSE 보고 시 안내 권고).

#### 3.5.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-008 | F-005 AC: rc에 export 행 존재 | 통합 테스트 | 임시 HOME에 빈 `.zshrc` 두고 함수 실행 → `.zshrc`에 `export OPAL_TEST_TOOLS_GLOBAL=...test-tools.yaml` 행 1개 존재 |
| TS-009 | F-005 멱등성 (H-4) | 통합 테스트 | 함수 2회 실행 후 `.zshrc`의 export 행이 정확히 1개 (중복 없음) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001, F-003, F-005 | 1, 3, 5 | (아래 Step별) | 병렬 가능 | 3갈래 독립, 서로 다른 파일 |
| 2 | F-002, F-004 | 2, 4 | (아래 Step별) | Phase 1 갈래 완료 후 | F-002←F-001, F-004←F-003 |
| 3 | 배포·검증 | 6 | PM 직접 | 순차 | install 배포 + 문서 갱신 판단 |

### 4.2 실행 체크리스트

> 총 6개 Step | Phase 3개 | 실행 모드: 복잡

#### Step 1: test-scenario-guide.md M2 트리거 기준 명확화
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`
- **작업 내용**: ① 변경영역×M 매핑 표(`:75-85`)에 "M2 의무 트리거" 규칙 추가 — FE 화면/컴포넌트·인증/인가·외부 API 연동 포함 시 L2/M2 의무([MUST] 문구) ② 검증깊이×실행방식 조합표(`:87-94`)에 L1×M2 불가 사유 1줄 주석 추가 ③ 변경이력 표(`:191-198`)에 v2.5 행 추가
- **완료 기준**: 가이드에 "FE … 포함 시 … L2/M2 … 의무" 문구 + L1×M2 불가 사유 주석 + 변경이력 행 존재 (grep). 계층결정 규칙 표 FE 행과 모순 없음
- **테스트**: TS-001, TS-002 (산출물 검사)
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: SKILL.md PM Gate FE→M2 체크 항목 추가
- [ ] 완료
- **소속 기능**: F-002
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-dev-test-scenario/SKILL.md`
- **작업 내용**: PM Gate 체크 블록(`:155-164`)에 "FE 변경 시 M2 시나리오 포함" 체크박스 1개 추가(test-scenario-guide.md §Step 3-b 참조 포인터) + 시나리오 작성 체크리스트(`:175-189`)에 대응 항목 1줄 추가 + 변경이력(`:200-208`)에 v1.7 행 추가
- **완료 기준**: PM Gate 블록에 "FE 변경 시 M2 시나리오 포함" 체크박스 존재 + 변경이력 행 존재 (grep)
- **테스트**: TS-003 (산출물 검사)
- **실행 방법**: sub-agent
- **의존**: Step 1 (F-001 M2 의무 트리거 규칙을 참조)

#### Step 3: e2e_adapter.py playwright fallback mcp_action 필드 추가
- [ ] 완료
- **소속 기능**: F-003
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/test-tool/lib/e2e_adapter.py`, `opal/tools/test-tool/tests/test_test_tool.py`
- **작업 내용**: `_run_playwright_fallback`(`:119-132`) 반환 dict에 `mcp_action:"browser_navigate"`, `mcp_url:url` 추가 + docstring 정정. 테스트(`_assert_playwright_fallback :555-577`)에 mcp_action/mcp_url 단언 추가 + cmux 미구성(`has_cmux=False`) 경로 케이스 추가(`[T041/L1-fallback]`). ESCALATE 경로 미변경(폴백 금지 유지)
- **완료 기준**: `pytest`(또는 `python3 -m unittest`) 전체 통과 — FALLBACK 4종 + cmux 미구성 경로 mcp_action 단언 PASS + 기존 ESCALATE 5종 회귀 PASS
- **테스트**: TS-004, TS-005 (기능/회귀 테스트, M1)
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 4: opal-test-agent AGENT.md playwright MCP 실행 절차 명시
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 에이전트
- **agent**: opal-task-agent
- **파일**: `opal/agents/opal-test-agent/AGENT.md`
- **작업 내용**: M2 처리 절차(`:170-172`)에 fallback JSON(`e2e.driver:playwright`) 수신 후 playwright MCP 직접 호출 4단계 분기 추가 — `e2e.mcp_action`/`e2e.mcp_url` 읽어 `mcp__playwright__browser_navigate` → `browser_snapshot`/`browser_take_screenshot` 증거 캡처. fallback≠환경미비 구분. 변경이력(`:178-185`)에 v1.6 행 추가. **필드명을 Step 3 e2e_adapter.py 반환 키와 글자 그대로 일치**(H-6)
- **완료 기준**: AGENT.md M2 섹션에 `mcp__playwright__browser_navigate`/`browser_snapshot` 예시 + `e2e.mcp_action`/`e2e.mcp_url` 참조 + 변경이력 행 존재 (grep). e2e_adapter.py 반환 키와 토큰 교차 일치
- **테스트**: TS-006, TS-007 (산출물 검사)
- **실행 방법**: sub-agent
- **의존**: Step 3 (반환 필드명 정합 필수)

#### Step 5: install-mac.sh OPAL_TEST_TOOLS_GLOBAL shell rc 등록
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: `register_test_tools_global_in_shell_rc()` 신규 함수 추가(기존 `register_path_in_shell_rc :884-906` 멱등 마커 패턴 재사용, 마커 `# === OPAL TEST_TOOLS_GLOBAL ===`) + `install_opal_bin()`(`:859`)에서 호출 1줄 추가 + 변경이력 헤더(`:11-31`)에 신규 버전 행 추가. export 값은 `"$HOME/.opal/templates/test-tools.yaml"`
- **완료 기준**: 임시 HOME 빈 `.zshrc`에 함수 2회 실행 → export 행 정확히 1개(멱등). `bash -n scripts/install-mac.sh` 문법 통과
- **테스트**: TS-008, TS-009 (통합 테스트)
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 6: install 배포 + docs/ 갱신 판단
- [ ] 완료
- **소속 기능**: F-001~F-005
- **영역**: 문서
- **agent**: PM 직접
- **파일**: (해당 시) `docs/` 문서 — 현 프로젝트 docs/ 부재 시 스킵
- **작업 내용**: 5파일 수정 완료 후 `scripts/install-mac.sh`로 `~/.opal/` 배포(직접 편집 금지 — D-7 §1). docs/ 갱신 필요 여부 판단(test-tool/test-scenario 절차 변경이 ARCHITECTURE/CONVENTIONS에 영향 시 갱신; 본 프로젝트 docs/ 미존재로 추정 시 스킵)
- **완료 기준**: install 재배포로 `~/.opal/skills/op-dev-test-scenario/`, `~/.opal/agents/opal-test-agent/`, `~/.opal/tools/test-tool/`에 수정 반영 확인. shell rc에 OPAL_TEST_TOOLS_GLOBAL 등록 확인
- **테스트**: 배포 후 `test-tool resolve`가 `source:"global"` 반환(글로벌 템플릿 존재 시) 또는 env var 등록 확인
- **실행 방법**: direct
- **의존**: Step 1, 2, 3, 4, 5

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 ∥ Step 3 ∥ Step 5 | 3갈래 독립 — 가이드/Python/install 서로 다른 파일, 의존 없음 |
| Step 1 → Step 2 | F-002 PM Gate가 F-001 M2 의무 트리거 규칙을 참조 (단일 SSOT 정합) |
| Step 3 → Step 4 | F-004 절차가 F-003 반환 필드명(`mcp_action`/`mcp_url`)을 글자 그대로 참조 (H-6) |
| Step 5 독립 | 다른 4 Step과 파일·의존 무관 |
| Step 6 ← all | 배포는 전체 수정 완료 후 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | M2 의무 트리거 규칙 + L1×M2 불가 사유 주석 | TS-001 | 가이드에 FE 포함 시 L2/M2 의무 문구 + 불가 사유 주석 존재 |
| F-001 | 표 간 정합성 | TS-002 | 변경영역×M 표 FE 행 ↔ 계층결정 규칙 표 FE 행 무모순 |
| F-002 | PM Gate FE→M2 체크 항목 | TS-003 | PM Gate 블록에 FE→M2 체크박스 존재 |
| F-003 | mcp_action/mcp_url 필드 반환 | TS-004 | FALLBACK 4종 + cmux 미구성 경로 모두 mcp_action="browser_navigate" + mcp_url 존재, pytest 통과 |
| F-003 | 에스컬레이션 폴백 금지 회귀 | TS-005 | ESCALATE 5종 driver≠playwright, mcp_action 부재, exit=7 |
| F-004 | playwright MCP 절차·예시 | TS-006 | AGENT.md M2에 browser_navigate/snapshot 예시 + mcp_action/mcp_url 참조 존재 |
| F-004 | 필드명 정합 (H-6) | TS-007 | AGENT.md 토큰 ↔ e2e_adapter.py 반환 키 일치 |
| F-005 | shell rc export 등록 | TS-008 | rc에 OPAL_TEST_TOOLS_GLOBAL export 행 존재 |
| F-005 | 멱등성 (H-4) | TS-009 | 2회 실행 후 export 행 정확히 1개 |

### 5.2 회귀 테스트
- [ ] `test-tool` 기존 unittest 스위트(`opal/tools/test-tool/tests/test_test_tool.py`) 전체 PASS — 특히 S-6(폴백 4종)·S-7(에스컬레이션 5종) 기존 케이스 비파괴
- [ ] `bash -n scripts/install-mac.sh` 문법 검증 PASS — 신규 함수 추가가 스크립트 파싱을 깨지 않음
- [ ] resolver.py 기존 동작 비변경 확인 (소비측만 변경, resolver는 미수정)

### 5.3 코드/문서 품질
- [ ] 4개 문서 파일(가이드/SKILL/AGENT) + install-mac.sh 변경이력 표에 신규 버전 행 추가 (변경이력 의무)
- [ ] @header 규칙 — e2e_adapter.py @header(`:2-11`)는 exports 변경 없음(내부 함수 수정)으로 갱신 불요. 단 description의 "폴백 결정" 의미 보존 확인
- [ ] 프로젝트 컨벤션(2-Layer: 소스 수정→install 배포) 준수 — `~/.opal/` 직접 편집 없음

### 5.4 보안
- [ ] .env, 인증 파일이 .gitignore에 포함 (본 변경은 시크릿 미도입)
- [ ] 코드에 하드코딩된 토큰/시크릿 없음 — 추가 export는 파일 경로(시크릿 아님)
- [ ] shell rc append가 사용자 기존 rc 내용을 파괴하지 않음 (append-only + 마커 가드)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 6개 | 복잡 |
| 변경 파일 수 | 6개 (소스 5 + 테스트 1) | 복잡 |
| 모듈 범위 | 다중 (test-tool / test-scenario 스킬 / test-agent / install) | 복잡 |
| 작업 유형 | 개선 (3개 원인 동시 해소) | 복잡 |
| 외부 의존성 | playwright MCP 배선(신규 절차) | 복잡 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 (병렬):
  Agent-A (opal-task-agent) ── Step 1 (test-scenario-guide.md)
  Agent-B (opal-be-agent)   ── Step 3 (e2e_adapter.py + 테스트)
  Agent-C (opal-task-agent) ── Step 5 (install-mac.sh)

Batch 2 (Batch 1 갈래별 완료 후):
  Agent-A' (opal-task-agent) ── Step 2 (SKILL.md)  [Step 1 후]
  Agent-D  (opal-task-agent) ── Step 4 (AGENT.md)  [Step 3 후]

Batch 3:
  PM 직접 ── Step 6 (install 배포 + docs/ 판단)
```

**그룹핑 근거**:
- 파일 충돌 방지: 6 Step이 모두 서로 다른 파일 → 충돌 없음.
- 모듈 응집: Step 1·2(test-scenario 문서 모듈)는 동일 에이전트 계열로 연속 처리 가능. Step 3·4(playwright 배선)는 BE→에이전트 순서.
- 병렬 극대화: Batch 1에서 3갈래 동시 디스패치.

### C-2. 스킬 요구사항

- 본 태스크는 EXECUTE 단계에서 `op-dev-execute` 스킬로 각 Step을 구현. 신규 스킬 불요 (기존 op-dev 파이프라인 내).
- 갭 판별: 동일 패턴 3개 미만 → 인라인 지침으로 충분 (각 Step "작업 내용"이 지침).

### C-3. 도구 요구사항

- CLI: `python3 -m unittest`(또는 pytest) — test-tool 테스트 실행 (Step 3 검증).
- CLI: `bash -n` — install-mac.sh 문법 검증 (Step 5).
- MCP: playwright MCP — F-004 절차가 배선 대상이나 *구현 시점*에는 문서 명시만(실제 호출은 TEST 단계 런타임). PLAN/EXECUTE에서 MCP 직접 호출 불요.
- 패키지: 신규 설치 없음.

### C-4. 테스트 전략

- 기능 테스트: `opal/tools/test-tool/tests/test_test_tool.py` — Step 3 mcp_action 단언 추가 후 전체 스위트 실행. 명령: `cd opal/tools/test-tool && python3 -m unittest discover tests` (또는 `run.sh` 경유).
- 회귀 테스트: 기존 S-1~S-7 전체 PASS 유지 확인 (특히 폴백·에스컬레이션).
- 산출물 검사: 문서 3파일(F-001/002/004)은 grep 기반 산출물 검사 — opal-test-agent가 TEST 단계에서 PASS 조건 확인.
- install 검증: 임시 HOME 격리 후 `register_test_tools_global_in_shell_rc` 2회 실행 멱등성 확인 (TS-008/009).
- TEST 모드: `test_mode=be` 권고 — 본 변경 주축이 Python 어댑터 + 스크립트/문서. FE 화면 없음.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| test-tool 어댑터 | Python 3.x (stdlib only) | (해당 없음 — stdlib, 신규 의존 없음) |
| 테스트 | unittest (subprocess 기반 행위 계약) | - |
| 설치 스크립트 | Bash | - |
| 문서 | Markdown | opal-doc-standard (변경이력 의무) |

> 외부 라이브러리 신규 도입 없음 → context7/shadcn MCP 조회 불요. playwright MCP는 런타임 소비 대상(배선만).

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 설계 단계 MCP 조회 불요 — stdlib·Bash·Markdown 변경. playwright MCP는 F-004가 문서로 배선만 하며 PLAN에서 호출하지 않음 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | e2e_adapter.py | `opal/tools/test-tool/lib/e2e_adapter.py` | `_run_playwright_fallback` 반환 dict 수정 대상 + 호출 경로 2곳 |
| D-2 | 소스 | test-scenario-guide.md | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | M2 트리거·L1×M2 조합표 수정 대상 |
| D-3 | 소스 | op-dev-test-scenario SKILL.md | `opal/skills/op-dev-test-scenario/SKILL.md` | PM Gate 체크리스트 수정 대상 |
| D-4 | 소스 | opal-test-agent AGENT.md | `opal/agents/opal-test-agent/AGENT.md` | M2 playwright MCP 절차 배선 대상 |
| D-5 | 소스 | install-mac.sh | `scripts/install-mac.sh` | OPAL_TEST_TOOLS_GLOBAL 등록 + register_path_in_shell_rc 패턴 재사용 |
| D-6 | 소스 | resolver.py | `opal/tools/test-tool/lib/resolver.py:188-227` | OPAL_TEST_TOOLS_GLOBAL 소비 위치 — 글로벌 소스 해석 |
| D-7 | 기획 | TASK.md | `tasks/041-260624-opd-e2e-테스트-실행-개선/TASK.md` | 요구사항 F-001~F-005 + AC + 제약 |
| D-8 | 설계 | PRINCIPLES.md (헌법) | `opal/core/PRINCIPLES.md` §2·§3·§4 | Simplicity/Surgical/증거 원칙 |
| D-9 | 소스 | test_test_tool.py | `opal/tools/test-tool/tests/test_test_tool.py:504-595` | 기존 폴백 테스트 계약 — mcp_action 단언 추가 위치 |
| D-10 | 소스 | test_tool.py | `opal/tools/test-tool/test_tool.py:163-187` | cmd_integration — e2e dict JSON 직렬화 소비 경로 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1 참조.

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | mcp_action 필드 추가가 기존 폴백 테스트 단언을 깨뜨릴 가능성 | F-003 | P1 | additive 변경(기존 4키 보존). 기존 `_assert_playwright_fallback`은 driver/fallback_reason만 단언 → 비파괴 (H-1) |
| R-2 | 두 폴백 호출 경로 중 한쪽만 수정하여 cmux 미구성 경로에서 mcp_action 누락 | F-003 | P1 | 단일 함수 `_run_playwright_fallback` 수정 → 두 호출처 자동 반영. cmux 미구성 경로 테스트 케이스 신규 추가 (H-2) |
| R-3 | ESCALATE 경로에 mcp_action 누출 (폴백 금지 위반) | F-003 | P0 | ESCALATE 경로는 `_run_playwright_fallback` 미호출 → 수정 대상 아님. S-7 회귀 테스트로 driver≠playwright 확인 (H-3) |
| R-4 | install 재실행 시 export 라인 중복 누적 | F-005 | P1 | 기존 register_path_in_shell_rc 멱등 마커 패턴 재사용 + 2회 실행 멱등 테스트 (H-4) |
| R-5 | AGENT.md 참조 필드명이 e2e_adapter.py 실제 키와 불일치 | F-004 | P1 | Step 4를 Step 3 후 순차 배치 + 교차 grep 검증 (H-6, citation-rules.md §7) |
| R-6 | M2 의무 규칙이 가이드 내 두 표(계층결정/M매핑) 사이에서 모순 | F-001 | P1 | TS-002 정합성 산출물 검사 — FE 행 상호 무모순 확인 (H-5) |
| R-7 | 기 설치 사용자는 재배포 전까지 env var 미적용 → 글로벌 템플릿 여전히 미동작 | F-005 | P2 | CLOSE 보고 시 "재설치 또는 수동 export 1줄" 안내. resolver는 미설정 시 추론 폴백으로 안전 동작(회귀 아님) |
