# TASK: TEST-SCENARIO 목표계열 선작성 — PLAN 병렬 도출 트랙 신설

> 작성일: 2026-08-19 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

TEST-SCENARIO 도출 입력을 **TASK 유래(목표·채택 관점)**와 **PLAN 유래(리스크·파괴 관점)** 2계열로 명시 분리하고, TASK 유래 계열을 PLAN 워커 실행과 **병렬 선작성**하는 트랙을 SSOT 문서에 신설한다.

## 배경

현행 파이프라인은 PLAN 완료 → TEST-SCENARIO 작성 → EXECUTE 순차다. 캡틴이 "시나리오 작성과 구현 병렬"을 검토 요청했고, 실측 결과 그 안은 헌법·하네스 위반(완료기준 사후 생성, RED-first 역전, 도구 차단)으로 부적격 판정됐다. 이어 캡틴이 제시한 대안 "PLAN하면서 시나리오 만들기"는 순서를 뒤집지 않고 앞당기는 방향이라 위반 지점이 없으며, 070 관점 편향 사건의 근본 해소에 오히려 더 가깝다.

## 배경 분석 (대화에서 도출)

### 1. 시나리오∥구현 병렬안이 부적격인 이유 (기각 근거)

| # | 사실 | 근거 |
|---|------|------|
| 1 | EXECUTE 워커가 TEST-SCENARIO.md를 **완료 판정 기준**으로 소비한다 (`scenario_source` 필수 입력, 완료기준 = L1/L2 시나리오 PASS, 자가점검 = 시나리오 실행 명령 추출) | `opal/skills/opal-pilot-dev/SKILL.md:131-134` |
| 2 | 완료기준 사후 생성은 헌법이 명시 금지한다 | [MUST] `opal/core/PRINCIPLES.md` §1: "Lock acceptance criteria before execution. Criteria added later are rationalization." |
| 3 | RED 증거 없는 GREEN 진입 금지 (강제 대상 5종: 비즈니스 로직·DB 스키마·API 계약·인증/인가·버그 수정) | `opal/core/references/harness/red-first.md:24`, `:33-38` |
| 4 | 도구가 이미 차단한다 — `check_stage_transition_guard`가 PM 경로에서 앞 행 전부 완료를 검증하고, advance 경로는 `force=False` 하드코딩 | `opal/tools/state-tool/state_tool.py:634`, `:1423` |
| 5 | 목표-커버 게이트 `verdict: rewrite`는 실측 발생 사건이다 (091 iter1이 070 실패모드 검출) | `.opal/MEMORY.json` history / `opal/skills/opal-pilot-dev/SKILL.md:97` |

### 2. 도출 입력이 2계열로 이미 분리되어 있다 (채택 근거)

| 계열 | 도출 입력 | 원천 | 대응 루브릭 축 | 근거 |
|------|----------|------|--------------|------|
| 파괴 관점 | 리스크 가설 H-N | PLAN.md §리스크 가설 표 | ③기능커버 ④리스크커버 | `test-scenario-guide.md:25-31` |
| 채택 관점 | 요구사항 R / 목표 문장 / 채택·잔존 기준 | TASK.md | ①목표달성 ②요구커버 ⑤채택·잔존 ⑥경계·부정 | `test-scenario-guide.md:33-36` |

게이트 입력 페이로드도 동일 경계다 — `goal`·`requirements`는 TASK 유래, `features`·`hypotheses`만 PLAN 유래 (`opal/core/references/harness/scenario-gate.md` §3).

즉 **루브릭 6축 중 4축이 PLAN 없이 도출 가능**하고, ③④ 2축만 PLAN 확정을 요구한다.

### 3. 선작성이 품질을 개선하는 이유

070 사건의 근본 원인은 루브릭 부재가 아니라 **도출 엔진의 관점 편향**이다 — [MUST] `scenario-gate.md` §1: "리스크 가설(파괴 관점, H-N)만 도출 입력으로 쓰고 목표 달성(채택 관점)이 커버리지 게이트에 없었다". 편향의 원인이 PLAN 선행 그 자체이므로, PLAN을 **읽지 않은 상태**에서 목표에서 시나리오를 도출하면 PLAN 관점 오염이 원천 차단된다. 또한 선작성 시나리오와 PLAN이 어긋나면 그 불일치가 PLAN PM Gate 시점의 조기 경보로 작동한다(현행은 EXECUTE 직전까지 검출 지연).

### 4. 검증 2원화가 깨지지 않는다

TEST-SCENARIO 분리 이유는 시간 순서가 아니라 작성자 분리 규정이다 — `opal/skills/opal-pilot-dev/SKILL.md:89`: "self-confirming 방지를 위해 PLAN 워커(opal-plan-agent)와 다른 작성자가 수행한다". 선작성 주체는 그대로 알투(PM)+캡틴 페어이고 PLAN.md는 `opal-plan-agent`가 작성하므로 분리가 유지된다.

### 5. pilot별 현행 배선 차이 (실측)

| pilot | TEST-SCENARIO 위치 | 게이트 행 key | 근거 |
|-------|-------------------|--------------|------|
| opd | 독립 stage (TEST-SCENARIO) | `test_scenario.scenario_gate` | `opal/skills/opal-pilot-dev/references/pipeline.json` task_steps id 9~11 |
| opds | PLAN stage 흡수 | `plan.scenario_gate` | `opal/skills/opal-pilot-dev-short/SKILL.md` STEP 2 |

opds는 이미 PLAN stage에 흡수되어 있어 본 규칙과 구조적 정합성이 가장 높다. 단 양쪽 모두 "PLAN.md 수신 **후**" 순차 작성이라, 병렬 선작성은 두 pilot 모두 신규 배선이 필요하다.

### 6. 도구 변경이 불필요한 이유

STATE 행 순서를 그대로 두고 선작성을 **행 밖 초안 작업**으로 수행하면, `check_stage_transition_guard`(`state_tool.py:634`)를 건드릴 필요가 없다. 행 mark는 기존 순서대로 진행된다.

## 확정된 설계 방향 (대화에서 합의)

| # | 확정 내용 | 근거 |
|---|----------|------|
| D-1 | 시나리오∥구현 병렬은 **기각**한다 | 배경 분석 §1 (헌법 §1 / red-first / 도구 차단) |
| D-2 | PLAN∥시나리오 **전체** 병렬도 아니다 — TASK 유래 계열(①②⑤⑥)만 선작성 대상 | 배경 분석 §2 |
| D-3 | PLAN 확정 후 PLAN 유래 계열(③④) **보강 라운드 필수** — 선작성만으로 종료 금지 | `test-scenario-guide.md:25-31` |
| D-4 | 목표-커버 게이트는 **PLAN 확정 + 보강 완료 후 1회만** 호출 | F/H 매핑 결정론 유지 (`scenario-gate.md` §3) |
| D-5 | 작성 주체는 알투(PM)+캡틴 페어 유지 — 검증 2원화 불변 | 배경 분석 §4 |
| D-6 | 데이터 설계(Step 2)·계층 결정(Step 3)은 변경 영역 의존이라 **선작성 대상 아님** | `test-scenario-guide.md:38-56` |
| D-7 | 도구 코드 변경 0 — 선작성은 STATE 행 밖 초안으로 수행 | 배경 분석 §6 |
| D-8 | RED-first 강제 트랙의 RED→GREEN 순서는 **불변** — 본 태스크는 시나리오 도출 시점만 앞당긴다 | `red-first.md:24` |

## 명확화 결과

> TASK 4요소를 잠근다. 각 요소는 확정값 또는 명시적 "N/A: <사유>"로 채운다 (공란·TBD 금지).

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | TEST-SCENARIO 도출 입력을 TASK 유래/PLAN 유래 2계열로 분리하고, TASK 유래 계열을 PLAN 워커 실행과 병렬 선작성하는 트랙을 SSOT 3문서 + pilot 2문서에 신설한다 | - | 배경 분석 §2 |
| 범위 | **포함**: `red-first.md`·`test-scenario-guide.md`·`scenario-gate.md`·`opal-pilot-dev/SKILL.md`·`opal-pilot-dev-short/SKILL.md` 5문서 + 변경이력 + install 재배포. **제외**: 도구 코드(state-tool·test-tool) 변경, `pipeline.json` 행 구조 변경, opsdd·oppl·oppd 3 pilot 배선(후속 태스크) | - | D-7 / 배경 분석 §5 |
| 제약 | ① 도구 변경 0 ② STATE 행 순서·구성 불변 ③ 검증 2원화(작성자≠PLAN 워커) 불변 ④ RED-first 강제 트랙 RED→GREEN 순서 불변 ⑤ 배포 경계 — `~/.opal/` 직접 편집 금지, 프로젝트 소스 수정 후 install 재배포 ⑥ 변경이력 표 행 추가 의무 | - | D-5 / D-7 / D-8 / `.opal/AGENT.md` §금지사항 |
| 완료기준 | 5문서에 규칙이 반영되고(R-1~R-5 AC 전부 충족), 5문서 변경이력에 095 행이 추가되고, install 후 배포본과 프로젝트 소스가 정합하며, TEST-SCENARIO 시나리오가 전부 PASS | - | R-1~R-6 AC |

## 요구사항

- [ ] **R-1** `red-first.md`에 목표계열 선작성 트랙 규칙 절 신설
  - 무엇을: PLAN 워커 실행과 병렬로 TASK 유래 입력만으로 시나리오를 선작성하는 규칙을 §번호 부여 절로 추가
  - 어디에: `opal/core/references/harness/red-first.md` (§1.5 적용 기준 하위 또는 인접)
  - 왜: 도출 입력 2계열 분리가 이미 실재하며(배경 분석 §2), RED-first 순서와 충돌하지 않음(D-8)
  - AC: 신설 절에 (a) 선작성 가능 입력 3종(목표 문장·요구사항 R·채택/잔존 기준) (b) PLAN 확정 후 ③④축 보강 필수 (c) 작성자≠PLAN 워커 유지 3항목이 모두 명시되고, 각 항목에 근거 인용이 붙어 있다

- [ ] **R-2** `test-scenario-guide.md` Step 1을 2계열로 분할
  - 무엇을: 현행 Step 1(가설 표 + TASK 목표/R 병행 Read)을 "선작성 가능 입력(TASK 유래)"과 "PLAN 확정 후 입력(PLAN 유래)" 2블록으로 재구성
  - 어디에: `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` §작성 프로세스 Step 1
  - 왜: 현행은 두 계열이 한 Step에 섞여 있어 선작성 가능 범위를 판별할 수 없음 (`test-scenario-guide.md:25-36`)
  - AC: Step 1이 2블록으로 분리되고, 루브릭 축 매핑(TASK 유래 → ①②⑤⑥ / PLAN 유래 → ③④)이 표로 존재하며, Step 2·3은 선작성 대상이 아님이 명시된다

- [ ] **R-3** `scenario-gate.md`에 게이트 호출 시점 규율 명시
  - 무엇을: 목표-커버 게이트를 "PLAN 확정 + 보강 완료 후 1회만" 호출하는 규율을 [MUST] 토큰으로 추가
  - 어디에: `opal/core/references/harness/scenario-gate.md` §4 루프 프로세스
  - 왜: 선작성 시점에 게이트를 호출하면 F/H가 미확정이라 ③④축 결정론 판정이 불가 (`scenario-gate.md` §3)
  - AC: [MUST] 토큰이 붙은 문장으로 호출 시점이 기재되고, 선작성 시점 호출 금지 근거(F/H 매핑 결정론)가 함께 기재된다

- [ ] **R-4** `opal-pilot-dev-short/SKILL.md` STEP 2 배선
  - 무엇을: PLAN 워커 디스패치와 동시에 목표계열 선작성을 착수하고, PLAN.md 수신 후 보강 → 게이트 호출로 이어지는 절차를 순서 있는 단계로 기재
  - 어디에: `opal/skills/opal-pilot-dev-short/SKILL.md` STEP 2 (PLAN 디스패치 절)
  - 왜: opds는 게이트 행이 PLAN stage에 흡수되어 본 규칙과 구조 정합성이 가장 높음 (배경 분석 §5)
  - AC: STEP 2에 (a) PLAN 디스패치 직후 선작성 착수 (b) PLAN.md 수신 후 ③④축 보강 (c) 보강 완료 후 게이트 1회 호출 3단계가 순서대로 기재되고, `plan.scenario_gate` 행 mark 시점이 (c) 이후임이 명시된다

- [ ] **R-5** `opal-pilot-dev/SKILL.md` STEP 3(PLAN)·3.5 배선
  - 무엇을: **STEP 3(PLAN)**에 선작성 착수를, STEP 3.5(TEST-SCENARIO)에 보강 + 게이트 절차를 각각 기재
  - 어디에: `opal/skills/opal-pilot-dev/SKILL.md` STEP 3 / STEP 3.5
  - 왜: opd는 TEST-SCENARIO가 독립 stage라 착수 지점과 완결 지점이 서로 다른 STEP에 놓임 (배경 분석 §5)
  - AC: **`## STEP 3: PLAN` 하위**에 선작성 착수 지시가 존재하고, STEP 3.5에 보강 → 게이트 호출 순서가 기재되며, `test_scenario.scenario_gate` 행 mark 시점이 보강 완료 이후임이 명시되고, **`## STEP 2: ANALYSIS` 절 diff가 0건**이다
  - **[정정 이력]** 최초 기재는 "STEP 2(PLAN)"이었으나 실측 결과 opd의 STEP 2는 **ANALYSIS**이고 PLAN은 **STEP 3**이다(`opal/skills/opal-pilot-dev/SKILL.md:32,57`). 문서/코드 불일치 규칙(코드=실질적 문서)에 따라 STEP 3으로 정정했다 — PLAN 워커 발견 H-h. 최초 지목대로 배선하면 ANALYSIS 단계(PM Gate 이전)에 선작성이 붙어 PLAN 착수보다 이르게 도출이 시작된다.

- [ ] **R-6** 변경이력 기재 + install 재배포
  - 무엇을: 수정한 5문서 변경이력 표에 095 행 추가 후 install로 `~/.opal/` 재배포
  - 어디에: 5개 수정 문서 각 변경이력 표 + `scripts/install-mac.sh` 실행
  - 왜: [MUST] `.opal/AGENT.md` §금지사항: "변경이력 누락 금지 — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무" / "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다"
  - AC: 5문서 전부 변경이력 표에 일시(KST)+095 태스크 번호를 포함한 행이 추가되고, install 후 배포본과 프로젝트 소스의 해당 5파일 diff가 0건이다

## 제약 조건

- **도구 변경 0** — `state-tool`·`test-tool` 등 Python 도구 코드를 수정하지 않는다. 선작성은 STATE 행 밖 초안 작업으로 수행한다 (D-7).
- **STATE 행 순서·구성 불변** — `pipeline.json` `task_steps[]`를 수정하지 않는다. `check_stage_transition_guard`(`state_tool.py:634`) 동작에 영향을 주지 않는다.
- **검증 2원화 불변** — 시나리오 작성 주체는 알투(PM)+캡틴 페어, PLAN.md 작성 주체는 `opal-plan-agent`로 분리 유지 (D-5).
- **RED-first 강제 트랙 순서 불변** — 비즈니스 로직·DB 스키마·API 계약·인증/인가·버그 수정 5종의 RED→GREEN 순서는 손대지 않는다 (D-8).
- **배포 경계** — [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다".
- **SSOT 단일화** — 하네스 규칙은 `opal/core/references/harness/` SSOT에만 정의하고 pilot SKILL.md는 참조만 한다. [MUST] `.opal/AGENT.md` §프로젝트별 추가 지침: "하네스 변경 시: `opal/core/references/opal-harness.md`(SSOT)를 수정한다. 다른 곳에서 발췌·복제하지 않는다".
- **후속 분리** — opsdd·oppl·oppd 3 pilot 배선은 본 태스크 범위 밖이며 별도 태스크로 처리한다.

## 기술 스택

- Markdown SSOT 문서 (하네스 참조 문서 / 스킬 SKILL.md / 스킬 references)
- Python 3 도구 (`state-tool`·`test-tool` — 본 태스크에서는 **참조만**, 수정 대상 아님)
- Bash (`scripts/install-mac.sh` — 배포)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | OPAL 헌법 | `opal/core/PRINCIPLES.md` | §1 완료기준 사전 잠금 / §4 RED-first 원칙 SSOT |
| D-2 | 설계 | RED-first 트랙 규칙 | `opal/core/references/harness/red-first.md` | R-1 수정 대상 + 트랙 분기 기준 SSOT |
| D-3 | 설계 | 목표-커버 게이트 규칙 | `opal/core/references/harness/scenario-gate.md` | R-3 수정 대상 + 루브릭 6축·정규화 계약 SSOT |
| D-4 | 설계 | TEST-SCENARIO 작성 가이드 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | R-2 수정 대상 + 도출 입력 2계열 원천 |
| D-5 | 설계 | Short Task 오케스트레이터 | `opal/skills/opal-pilot-dev-short/SKILL.md` | R-4 수정 대상 |
| D-6 | 설계 | Full Task 오케스트레이터 | `opal/skills/opal-pilot-dev/SKILL.md` | R-5 수정 대상 + EXECUTE 완료기준 의존 근거 |
| D-7 | 소스 | state-tool | `opal/tools/state-tool/state_tool.py` | stage-transition guard 동작 확인(수정 대상 아님) |
| D-8 | 설계 | PM 프로필 | `.opal/AGENT.md` | 배포 경계·변경이력·SSOT 금지사항 |
