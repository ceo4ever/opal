# TASK: 테스트 수행 도구 체계 — FE/BE 2단계(단위·통합) 재정의

> 작성일: 2026-06-23 | 작업 유형: 개선 | 적용 스킬: opd | 모드: semi-agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

테스트 에이전트가 테스트를 수행하기 위해 사용하는 도구 체계를 **단위 테스트 / 통합 테스트 2단계**로 재정의하고, FE/BE 각 단계별로 적용할 도구를 명시적으로 못박는다. 단위 테스트는 구현(EXECUTE) 단계, 통합 테스트는 테스트(TEST) 단계에서 수행하며, 각 단계는 PASS가 될 때까지 FAIL 시 수정→재테스트 루프를 강제한다. **핵심: 산문 지시가 아니라 신규 `test-tool`(결정론적 집행기)이 test-tools.yaml을 읽고 단계별 도구를 실행·판정하도록 만든다** (헌법 Core Stance "Enforce, don't just advise").

## 배경

테스트 수행 도구 규정에 구조적 결함이 누적되어 워커가 "무슨 도구로, 어느 단계에서" 테스트할지 비결정적이다.

## 배경 분석 (대화에서 도출)

재검토로 확인한 현행 결함 3종:

1. **도구 결정 인프라가 "이중 규정 + 죽은 레지스트리"로 분기** — `opal/core/references/test-tools-schema.yaml`·`opal/templates/test-tools.yaml`은 `check`/`install`/`required` 자동 설치 게이트라는 좋은 설계를 갖췄으나, 이를 소비한다는 `dtp-agent`/`dtp-test`가 코드베이스에 부재(grep 결과 스키마·템플릿 자신만 언급 = 삭제된 파이프라인의 고아 참조). 실제 살아있는 경로(`op-dev-test-scenario` + `opal-test-agent`)는 전혀 다른 4단계 탐지(CONVENTIONS→스택문서→설정파일→글로브)를 쓰며 test-tools.yaml을 조회하지 않음. 같은 문서(`test-scenario-guide.md`) 안에서 L1 작성요령은 "test-tools.yaml에서 결정"(L107), Step 4-a는 "4단계 탐지로 결정"(L131~142) — 한 문서 내 충돌. → 도구 결정 SSOT 부재.

2. **FE/BE 도구 경계가 "도구명 없는 의무"로 규정** — `opal/agents/opal-test-agent/personas/test-engineer.md`·`AGENT.md`는 FE에 접근성(WCAG) 검사, BE에 실 DB 통합·트랜잭션 검증을 의무화하나 *무슨 도구로* 하는지 매핑이 없음. `test-scenario-guide.md` 변경영역×M 매핑표(L77~85)는 BE(pytest) 편중, FE는 `vitest+RTL / cmux / playwright` 한 줄.

3. **E2E 도구 우선순위(cmux vs playwright)가 비결정적** — `test-scenario-guide.md` L72·L83은 "cmux/playwright/cypress" 나열만(우선순위 X), `opal-test-agent/AGENT.md` L161은 "playwright/cmux" 역순 표기 → 워커마다 다른 선택. cmux는 macOS 전용(`opal/core/references/tools.md` L297)인데 플랫폼 가드가 테스트 규정에 없음.

## 확정된 설계 방향 (대화에서 합의)

### A. 테스트 2단계 체계 — 파이프라인 단계 1:1 매핑 (캡틴 확정)

| 테스트 단계 | 구성 | 수행 파이프라인 단계 | 수행 주체 |
|------------|------|--------------------|----------|
| **1단계 단위 테스트** | lint + 문법·타입(build) + 기능(unit) | **EXECUTE(구현)** | 구현 워커(opal-fe-agent / opal-be-agent) 자가검증 |
| **2단계 통합 테스트** | E2E(cmux→playwright) + 실환경·사람제어 | **TEST** | opal-test-agent + 캡틴 `[SUPERVISOR]` |

### B. FE/BE × 2단계 도구 매트릭스 (확정 — 스택 py/ts 자동 해석)

| 테스트 단계 | 검사 | BE 도구 | FE 도구 | FAIL 시 한도 |
|------------|------|---------|---------|------------|
| **1단계 단위**<br>(EXECUTE) | lint | ruff(py)/eslint(ts) | eslint | 수정→재검증 (∞) |
| | 문법·타입(build) | mypy·pyright(py)/tsc(ts) | tsc --noEmit | 수정→재검증 (2회) |
| | 기능(unit) | pytest(py)/vitest(ts) | vitest + RTL | 수정→재검증 (3회) |
| | 보안(공통) | gitleaks | gitleaks | 즉시 차단 |
| **2단계 통합**<br>(TEST) | API·프로세스+실DB | pytest+httpx+실DB(testcontainers/fixture, mock 금지) | — | 수정→재검증 (3회) |
| | E2E 자동화 | **cmux 1순위 → playwright 폴백** | **cmux 1순위 → playwright 폴백** | 1회 재시도 후 에스컬레이션 |
| | 실환경·사람제어 | 캡틴 수동 `[SUPERVISOR]` | 캡틴 화면 시각 확인 `[SUPERVISOR]` | 캡틴 게이트 |

### C. E2E 우선순위 — cmux 1순위 / playwright 폴백 (캡틴 확정)

cmux browser 1순위, "안되면" playwright 폴백. cmux는 macOS 전용이므로 비-macOS·CI 환경에서는 자연히 "안되는" 경우에 해당하여 playwright로 폴백된다 → 별도 플랫폼 분기 없이 단일 규칙으로 처리. (OPAL의 wtm-agent도 cmux 1순위/playwright 폴백 원칙과 일관)

### D. PASS-or-fix 루프 강제

- 단위(EXECUTE): FAIL → 구현 워커 재수정 → 재테스트 (`verification-loop-guide.md` L1∞/L2 2회/L3a 3회 한도, harness §1 SSOT)
- 통합(TEST): FAIL → fix 모드 워커 재수정 → 재테스트 (E2E 1회, `opal-pilot-dev/SKILL.md` STEP 5 FAIL 루핑)

### E. 신규 `test-tool` — 결정론적 테스트 집행기 (캡틴 확정)

OPAL 도구 패턴(`state-tool`·`brain-tool`·`cmux-tool`)을 따르는 단일 도구 `~/.opal/tools/test-tool/run.sh` (JSON 반환). test-tools.yaml을 읽는 주체이자 테스트 실행 주체. **얇은 결정론적 래퍼** — 테스트 러너를 재구현하지 않고 yaml 해석→맞는 명령 실행→JSON 증거 반환 (헌법 §2 과설계 금지).

| 서브명령 | 역할 | 사용 단계 |
|---------|------|----------|
| `resolve [--stack]` | test-tools.yaml 해석(resolution_order: project→global→추론) → FE/BE×단계 도구셋 JSON 반환 | 시나리오 작성·디스패치 전 |
| `check [--category]` | check 명령 실행 → 설치/미설치 + required 플래그 반환 (설치 게이트) | 단계 진입 전 |
| `unit [--scope fe\|be] [--changed-files]` | **단위 tier**: lint→build/type→unit 계층 실행, stop-on-fail, JSON 증거 | **EXECUTE** |
| `integration [--scope fe\|be]` | **통합 tier**: E2E(cmux 1순위→playwright 폴백, 플랫폼 가드 내장) + API·실DB, JSON 증거 | **TEST** |

- 도구가 Pass/Fail을 구조화 반환 → 오케스트레이터가 PASS-or-fix 루프 구동 (D와 연동).
- test-tools.yaml의 실 소비자가 되어 R-2(레지스트리 고아화) 근본 해소.
- **self-confirming 고위험**(도구가 테스트를 집행) → RED-first 필수(작성자≠구현자).

#### E-1. cmux 가용성 정밀 계약 (캡틴 지시 — "대충 체크 금지", 실측 근거)

test-tool의 `integration`/`check`는 cmux 가용성을 **직접 재구현하지 않는다**(`cmux --version`·`uname` 단발 체크 금지 — 부정확·중복). 대신 **cmux-tool을 호출하고 그 JSON 에러코드를 소비**하여 폴백을 결정한다 (어댑터 계층 격리 + 도구 재사용, wtm-agent와 동일 패턴).

cmux-tool 4-gate preflight (`opal/tools/cmux-tool/lib/dispatch.sh:44-57` + `README.md:145-160`):

| Gate | 판정 | 에러코드(exit) |
|------|------|---------------|
| 1. 세션 컨텍스트 | `CMUX_SURFACE_ID` 설정 여부 (cmux 터미널 세션 내부여야 함) | `not_in_cmux`(2) |
| 2. 바이너리 | `command -v cmux` | `cmux_not_installed`(3) |
| 3. browser open | `cmux browser open` 성공 | `open_failed`(5) |
| 4. surface 파싱 | open 출력 파싱 | `surface_parse_failed`(5) |

- **폴백 트리거 4종**(`not_in_cmux`/`cmux_not_installed`/`surface_parse_failed`/`open_failed`) → playwright(phase2) 자동 폴백.
- **나머지 5종**(`usage`/`invalid_surface`/`goto_failed`/`wait_failed`/`eval_failed`) → 입력·실행 오류 = **폴백 금지·에스컬레이션**(URL/네트워크/명령 오류를 playwright로 우회 금지).
- 실측(2026-06-23): 현재 환경 cmux 설치됨 + Darwin + `CMUX_SURFACE_ID` 설정 → Gate1·2 통과(가용). Gate3·4는 실제 open 시점 판정.
- 플랫폼 가드(macOS 전용)는 Gate1·2가 자연 흡수 — 비-macOS/미설치 시 `cmux_not_installed`/`not_in_cmux` → 폴백. 별도 `uname` 분기 불필요.

#### E-2. E2E 실행 모델 — 격리 신규 surface(mode A) (캡틴 확정)

test-tool의 `integration`은 cmux browser를 **매 테스트마다 새로 열고 닫는다**(mode A). 이미 열린 브라우저에 붙는 방식(mode B/C)이 아니다.

- **근거**: cmux-tool 3모드(`opal/tools/cmux-tool/run.sh:21-23`) — A: URL 지정→신규 surface 열기→테스트→`tab close` / B·C: `--surface <handle>` 사용자 기존 surface 재사용(cleanup 절대 금지). 테스트는 결정성·재현성·사용자 세션 비훼손을 위해 **반드시 mode A**(격리 신규 surface).
- **실행 흐름**: 신규 open → 대상 앱 URL `navigate` → 시나리오 스텝(`click`/`fill`/`wait`/`eval` 단언) → Pass/Fail 증거 캡처 → surface `close`(mode A 정리).
- **SUT 경계**: cmux browser는 **드라이버**일 뿐, 테스트 대상 앱(dev 서버/localhost)은 별도로 가동되어 있어야 한다. test-tool의 앱 기동/확인 책임 경계(기동까지 할지, 가동 전제만 검사할지)는 PLAN에서 설계.
- playwright 폴백 시도 동일 모델(headless 신규 컨텍스트 open→구동→teardown).

## 명확화 결과

> TASK 4요소를 잠근다.

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | 테스트 도구 체계를 단위(EXECUTE)/통합(TEST) 2단계로 재정의 + FE/BE×단계 도구 매트릭스 명시 + PASS-or-fix 루프 강제 + 고아 레지스트리(dtp-*) 현행화 | - | 확정 설계 방향 A~D |
| 범위 | **포함**: ①신규 `test-tool` 빌드(Python + run.sh, 4서브명령 resolve/check/unit/integration) + RED-first 테스트 ②test-tools.yaml/schema 2단계 재구조화 ③test-scenario-guide.md·opal-test-agent/AGENT.md·test-engineer.md·verification-loop-guide.md가 test-tool을 호출하도록 배선 ④도구 레지스트리(tools.md·harness §9) 등록. **제외**: 실 프로젝트 .opal/test-tools.yaml 인스턴스 생성(템플릿/스키마만), pytest/vitest/cmux 등 외부 러너 자체 재구현(test-tool은 얇은 래퍼), CI 파이프라인 구성, install 재배포(캡틴 직접) | - | 배경 분석 1~3 + 확정 설계 E |
| 제약 | ①헌법 플랫폼 독립(cmux=macOS→playwright 폴백으로 흡수) ②`~/.opal/` 직접 편집 금지(소스 `opal/` 수정 후 install 재배포) ③변경이력 행 추가 의무 ④mock 금지 룰 유지 ⑤SSOT 단일 기재(루프 한도=harness §1, 검증명령=verification-loop-guide) | - | `.opal/AGENT.md` 금지사항 |
| 완료기준 | ①`test-tool` 4서브명령(resolve/check/unit/integration)이 동작하고 JSON 반환 + RED-first 테스트 GREEN ②`test-tool resolve`가 test-tools.yaml을 읽어 FE/BE×단계 도구셋 반환(실 소비자 = R-2 해소) ③`test-tool integration`이 cmux→playwright 폴백·macOS 가드 동작 ④test-tools.yaml에 단위/통합 2단계 구조 + FE/BE 매트릭스 존재 ⑤test-scenario-guide.md·AGENT.md·test-engineer.md·verification-loop-guide.md가 test-tool 호출로 배선 + 2단계 명명·E2E 우선순위(cmux→playwright)·단계 매핑 명시 ⑥dtp-* 고아 참조 현행화(grep 잔존 0건) ⑦tools.md·harness §9에 test-tool 등록 ⑧각 변경 파일 변경이력 행 추가 | - | 확정 설계 방향 A~E |

## 요구사항

- [ ] **R1.** test-tools.yaml/schema를 단위·통합 2단계 구조로 재구조화하고, FE/BE 도구 매트릭스(확정 B)를 반영한다. 도구 결정 단일 SSOT로 격상한다.
- [ ] **R2.** `dtp-agent`/`dtp-test` 고아 참조를 현행 경로(`op-dev-test-scenario` / `opal-test-agent`)로 교체한다. (grep 잔존 0건)
- [ ] **R3.** test-scenario-guide.md의 도구 결정 이중 규정(L107 vs L131~142)을 단일 SSOT로 통합하고, 2단계 명명 + FE/BE 도구 + E2E 우선순위(cmux→playwright) + 단계 매핑(단위=EXECUTE/통합=TEST)을 명시한다.
- [ ] **R4.** opal-test-agent/AGENT.md + test-engineer.md persona에 2단계 체계와 단계별 도구, PASS-or-fix 루프를 반영한다. persona의 "도구명 없는 의무"(접근성 등)에 도구를 매핑한다.
- [ ] **R5.** verification-loop-guide.md의 L1~L4 계층 서술을 캡틴의 2단계 명명(단위=EXECUTE/통합=TEST)과 정합시킨다(재라벨링·배선).
- [ ] **R6.** E2E 우선순위 cmux 1순위/playwright 폴백 + macOS 플랫폼 가드를 테스트 규정에 명문화한다.
- [ ] **R7.** 신규 `test-tool`을 빌드한다 — `~/.opal/tools/test-tool/run.sh` + Python 구현, 4서브명령(resolve/check/unit/integration). test-tools.yaml 해석(resolution_order), 단계별 계층 실행(stop-on-fail), cmux→playwright 폴백(플랫폼 가드), JSON 증거 반환. self-confirming 고위험 → RED-first(작성자≠구현자).
- [ ] **R8.** 6문서(test-scenario-guide·AGENT.md·test-engineer.md·verification-loop-guide + tools.md·harness §9)가 test-tool을 호출/등록하도록 배선한다. 산문 도구 결정을 `test-tool resolve` 호출로 대체.

## 제약 조건

- 헌법 플랫폼 독립 원칙 — cmux(macOS 전용)는 폴백 규칙으로 흡수, 하드코딩 분기 금지
- `~/.opal/` 배포본 직접 편집 금지 — 소스 `opal/` 수정 후 install 재배포 (배포는 캡틴 직접/지시)
- 문서 변경이력 표 행 추가 의무 (일시 KST + 태스크 번호 039)
- mock 금지 룰(헌법 §4 "Don't fake it") 유지
- 루프 한도 SSOT는 `opal-harness.md` §1, 검증 명령 SSOT는 `verification-loop-guide.md` — 수치·명령 복제 금지, 포인터 참조

## 기술 스택

- 프레임워크 문서/스킬/에이전트/레퍼런스 (Markdown·YAML) + 도구 스키마 (YAML)
- 대상 테스트 도구(규정 대상): pytest/vitest/jest(unit), eslint/ruff(lint), tsc/mypy/pyright(type), cmux/playwright(E2E), gitleaks(security)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | test-tools-schema.yaml | `opal/core/references/test-tools-schema.yaml` | 도구 레지스트리 스키마 (고아 dtp-* 참조) |
| D-2 | 설계 | test-tools.yaml 템플릿 | `opal/templates/test-tools.yaml` | 도구 레지스트리 인스턴스 템플릿 |
| D-3 | 설계 | test-scenario-guide.md | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | M1/M2/M3 실행방식 + 스택 탐지 + 도구 매핑 (이중 규정) |
| D-4 | 설계 | opal-test-agent AGENT.md | `opal/agents/opal-test-agent/AGENT.md` | 테스트 워커 3모드 + M1/M2/M3 처리 |
| D-5 | 설계 | test-engineer.md | `opal/agents/opal-test-agent/personas/test-engineer.md` | 테스트 페르소나 (도구명 없는 의무) |
| D-6 | 설계 | verification-loop-guide.md | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | L1~L4 검증 루프 + PASS-or-fix 한도 |
| D-7 | 설계 | opal-harness.md §1 | `opal/core/references/opal-harness.md` | 자동 루핑 제약 한도 SSOT |
| D-8 | 설계 | tools.md | `opal/core/references/tools.md` | cmux-tool macOS 전용 명시 |
