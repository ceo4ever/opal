# PLAN: TEST-SCENARIO 목표-커버리지 루브릭 게이트 루프 (공유 컴포넌트, opd 선적용)

> 작성일: 2026-07-23 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature | 실행 모드: 복잡

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

TEST-SCENARIO 단계를 "목표 달성 검증"으로 재정의하고, 루브릭 채점 기반 작은 수렴 루프(Producer → 커버리지 도구 게이트 → 독립 Evaluator 루브릭 채점 → 종료조건 판정 → 재작성)를 공유 컴포넌트로 구현한다. 규칙 SSOT 1(scenario-gate.md) + test-tool 확장(신규 서브명령) + evaluator 재사용(신규 phase) + 얇은 단계 스킬 1(op-scenario-gate)로 구성하며, 1차로 opd에만 접합한다. 070 사건(핵심 목표가 라이브 미반영인 채 완료 처리)의 근본 원인 — 도출 엔진이 파괴 관점(H-N)만 입력으로 쓰고 목표 달성(채택) 관점이 커버리지 게이트에 없던 것 — 을 tool-gated 게이트로 집행한다.

> [MUST] `opal/core/PRINCIPLES.md:14` §Core Stance: "Done means verified behavior, not a generated document." — R-8 자기적용이 이 원칙의 집행이다.
> [MUST] `opal/core/PRINCIPLES.md:15` §Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose." — 커버리지 게이트는 test-tool exit code로 집행하며 산문 권고로 그치지 않는다.
> [MUST] TASK.md §설계방향 5: "공유 컴포넌트 = 재사용+최소신규 — 규칙 SSOT 신규 1 + test-tool 확장(신규 도구 아님) + evaluator 재사용(신규 에이전트 아님) + 얇은 단계 스킬 신규 1. 새 오케스트레이터 pilot 없음."

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | scenario-gate 규칙 SSOT 신설 + harness §1 루프 상한 행 | R-1 (+ R-T5) | P0 | 없음 |
| F-002 | test-tool 커버리지 서브명령 확장 (scenario-coverage-check) | R-2 | P0 | F-001 |
| F-003 | opal-evaluator-agent scenario-rubric phase 신설 | R-3 (+ R-T6) | P0 | F-001 |
| F-004 | op-scenario-gate 단계 스킬 신설 (루프 컨트롤) | R-4 | P0 | F-001, F-002, F-003 |
| F-005 | opd STEP 3.5 접합 (pipeline.json 게이트 행 + SKILL 배선) | R-5 (+ R-T2) | P0 | F-004 |
| F-006 | op-task AC 패턴 보강 (교체형 목표=잔존0·채택) | R-6 | P1 | 없음 |
| F-007 | test-tool 커버리지 서브명령 단위 테스트 (RED-first) | R-7 | P0 | F-001 |
| F-008 | 자기적용 실증 (음성통제 + 정상수렴) | R-8 (+ R-T7) | P0 | F-001~F-005, F-007 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-006 (독립, 상류 동반)

F-001 ─┬─ F-007 (RED) ─ F-002 (GREEN) ─┐
       ├─ F-003 ───────────────────────┼─ F-004 ─ F-005 ─┐
       └────────────────────────────────┘                ├─ F-008
                                                          │
       (F-001·F-002·F-003·F-004·F-005·F-007 완료) ────────┘
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨. (파괴 관점 — 목표 달성 관점은 R-8 자기적용 루프가 별도 커버)

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-002 scenario-coverage-check 판정 로직 | R/F/H↔시나리오 매핑 누락을 결정론 판정 — 미커버가 있는데 `ok` 반환(거짓 초록불) | P0 | L1(단위, 실 subprocess) | S-1 후보 |
| H-2 | F-002 신규 exit code (coverage_unmet/coverage_input_invalid) | 기존 scenario-* exit 8~15와 충돌 → 기존 7서브명령 dispatch 회귀 | P0 | L1(회귀, 기존 스위트 재실행) | S-2 후보 |
| H-3 | F-005 pipeline.json 신규 게이트 행 | state-tool `spec-validate` 거부 / `--rows-from` 파싱 실패 / stage-transition guard가 EXECUTE 차단 안 함 | P1 | L2(state-tool 실 CLI 실행) | S-3 후보 |
| H-4 | F-004 op-scenario-gate 종료조건 | MAX=3 초과 미감지(무한 루프) / 무진전 연속2회 미감지 / 수렴조건 오판(누락 있는데 PASS) | P0 | L1·L2(종료조건 표 대조 + 실행) | S-4 후보 |
| H-5 | F-004·F-005 Producer≠Evaluator 분리 | PM이 게이트 우회하고 test_scenario.user_confirm mark → self-confirming 재발 | P0 | L2(우회 시 차단 확인) | S-5 후보 |
| H-6 | F-003 evaluator phase 열거 확장 | 4번째 phase 추가가 기존 design-review/spec-review/drift-recheck 계약 회귀 → oppl G 게이트 깨짐 | P1 | L1(additive 계약 대조) | S-6 후보 |
| H-7 | F-008 음성통제 | 목표-커버 시나리오를 의도적으로 누락했는데 게이트가 PASS(음성통제 실패) → 게이트 무력 | P0 | L2·L3(자기적용 실증) | S-7 후보 |

**가설 도출 근거 요약**: H-1·H-4·H-7은 "거짓 초록불"(게이트가 있으나 목표 누락을 못 잡음) — 070 재발 방지의 핵심(→ ANALYSIS §4 발견⑤). H-2·H-3·H-6은 additive 확장의 회귀 리스크(→ ANALYSIS §1.2 에러코드 네임스페이스·additive 스키마 규율). H-5는 self-confirming 차단의 tool-gated 집행(→ ANALYSIS R-T4).

---

## 2. 기능별 분석

### F-001: scenario-gate 규칙 SSOT 신설 + harness §1 루프 상한 행

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서/SSOT | `opal/core/references/harness/scenario-gate.md` | 루브릭 6축·판정 주체 분리·루프 프로세스·정규화 계약·종료조건 SSOT | 신규 |
| 문서/SSOT | `opal/core/references/opal-harness.md` | §1 자동 루핑 제약 표 — 신규 루프 유형 행 추가 | 수정 |
| 스킬 | `opal/skills/op-dev-test-scenario/SKILL.md` | scenario-gate.md 참조 + PM Gate에 "목표 커버" 항목 추가 | 수정 |
| 가이드 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 도출 엔진에 목표/채택 관점 입력 추가 (Step 1 보강) | 수정 |

#### 2.1.2 현재 구현
- scenario-gate.md 부재 — 루브릭·정규화 계약·종료조건의 SSOT가 없다(→ ANALYSIS §1.1 R-1).
- `test-scenario-guide.md:11-13` 목적이 "리스크 가설 기반 시나리오 설계 + TDD red-green" 2개뿐 — "목표 달성(채택 관점)"이 목적 목록에 없다(→ ANALYSIS §4 발견②). `test-scenario-guide.md:20-29` Step 1은 PLAN §리스크 가설 표만 도출 입력으로 규정.
- `op-dev-test-scenario/SKILL.md:159-165` PM Gate 7대 룰은 "가설↔시나리오 매핑 완전"만 검사하고 "TASK 요구사항 R 전체 커버·목표 커버" 항목이 없다.
- `opal-harness.md:48-56` §1 표는 7개 행(lint∞/build 2/unit·integration 3/E2E 1/QA설계 0/워커폴백 1/PLAN재진입 2) — MAX=3 루브릭 게이트 루프에 대응 행이 없다(→ ANALYSIS R-T5).

#### 2.1.3 영향 범위
- scenario-gate.md는 R-2(도구)·R-3(평가자)·R-4(스킬)의 공통 기준 원천이 된다 — 하류 3기능이 모두 이 SSOT를 참조.
- harness §1 신규 행은 loop-control.md의 "본 표를 참조·비복제"(`loop-control.md:41,143`) 원칙에 따라 scenario-gate.md가 수치를 복제하지 않고 참조하도록 한다.

---

### F-002: test-tool 커버리지 서브명령 확장 (scenario-coverage-check)

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE(Python) | `opal/tools/test-tool/lib/scenario.py` | 신규 핸들러 `cmd_scenario_coverage_check` + 파서 등록 + `SCENARIO_DISPATCH` 키 추가 | 수정 |
| BE(Python) | `opal/tools/test-tool/test_tool.py` | `**SCENARIO_DISPATCH` 스프레드로 자동 흡수 | 변경 불요 (확인됨) |
| 환경 | `opal/tools/test-tool/schema/test-scenario.schema.json` | 미변경 (coverage-input은 transient 페이로드, test-scenario.json SSOT 아님) | 변경 불요 |

#### 2.2.2 현재 구현
- `scenario.py:511-519` `SCENARIO_DISPATCH` 7키(init/lock/mark/status/red/fidelity-check/conformance). R/F/H↔시나리오 매핑 커버리지 판정 서브명령 부재(→ ANALYSIS §1.1 R-2).
- `test_tool.py:238-246` dispatch가 `{resolve/check/unit/integration, **SCENARIO_DISPATCH}`로 병합 — scenario.py에 키만 추가하면 자동 라우팅(→ ANALYSIS §4 발견④, `test_tool.py:238-246`).
- 에러코드 실사용 현황(`scenario.py:67-76` + `_error`/`_respond` 호출): exit 8(red_not_confirmed)·9(scenario_not_locked)·10(scenario_not_initialized)·11(scenario_spec_invalid_json)·12(scenario_already_locked)·13(fidelity_unmet)·14(surface_unverified). exit 15는 `surfaces_file_not_found`에 정보용 배정(실호출은 applicable:false exit 0). → 신규 서브명령은 exit 16부터 배정(15 회피, ANALYSIS §1.2 에러코드 규율).

#### 2.2.3 영향 범위
- `test_test_tool.py`(resolve/check/unit/integration 12건)와 격리 — 무영향(→ ANALYSIS §1.4).
- 기존 scenario-* 7서브명령 dispatch 키 불변이 회귀 보호 대상(H-2) — `TestExistingSuiteRegressionPresence` 패턴 확장(`test_scenario.py:272-306` 계열).

---

### F-003: opal-evaluator-agent scenario-rubric phase 신설

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트/문서 | `opal/agents/opal-evaluator-agent/AGENT.md` | phase 열거값에 `scenario-rubric` 추가 + Phase 1에 판단축 ①⑤⑥ 루브릭 삽입 + Phase 5 보고서 파일명 규칙 | 수정 |

#### 2.3.2 현재 구현
- `AGENT.md:27` phase 3종(design-review/spec-review/drift-recheck). `AGENT.md:37-55` Phase 1 Base 루브릭 10차원(계약 완전성 등). `AGENT.md:90-95` 보고서 경로 3분기 + VERIFICATION.md 폴백.
- 기존 루브릭은 Likert 1–5(통과선 ≥4) — 본 태스크 루브릭은 2점 척도(0~2, 판단축 각≥1 AND 평균≥1.5)로 상이 → scenario-rubric phase 전용 척도로 분리 정의(→ ANALYSIS §1.2 verdict-only·readonly 패턴).
- `tools: [Read, Grep, Glob, Bash]`만 — Edit/Write 미부여(`AGENT.md:9`), verdict-only·readonly 유지.

#### 2.3.3 영향 범위
- 기존 3 phase 호출자(oppl G 게이트·설계 루프 D6)는 additive 확장으로 무변경(H-6, → ANALYSIS §3.2).
- opd 태스크 폴더에 VERIFICATION.md 관례 부재 → 전용 파일명 `SCENARIO-GATE-{N}.md` 명시 필요(R-T6).

---

### F-004: op-scenario-gate 단계 스킬 신설 (루프 컨트롤)

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/op-scenario-gate/SKILL.md` | 정규화 페이로드 빌드 → test-tool 커버리지 게이트 → evaluator 디스패치 → 종료조건 3종 판정 → 재작성 루프 | 신규 |

#### 2.4.2 현재 구현
- 부재. 재사용 선례: oppl Loop 2가 `backlog-tool coverage-check`(결정론, `backlog_tool.py:589-620`) + `opal-evaluator-agent`(판단) + `loop-control.md` 종료조건을 이미 병행(→ ANALYSIS §4 발견③). R-4는 이 3중 구조를 시나리오 문서 1건 단위로 축소 재사용.
- 분리형 SSOT + 얇은 래퍼 원칙(`test_tool.py:18-20`: 도구는 결정론 판정만, 루프는 오케스트레이터 책임) → 결정론 커버리지는 test-tool(F-002), 루프 컨트롤은 op-scenario-gate(PM 레벨)에 배치.

#### 2.4.3 영향 범위
- 단일 호출 지점 — 1차는 opd STEP 3.5(F-005)만 호출. 후속 확산(oppl/opds/opsdd/oppd)은 pilot별 정규화 페이로드 변환기만 추가하면 재사용(정규화 계약이 이 확장성의 근거, → ANALYSIS §4 발견①, R-T3).

---

### F-005: opd STEP 3.5 접합

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 오케스트레이터 리소스 | `opal/skills/opal-pilot-dev/references/pipeline.json` | `test_scenario.scenario_gate` 행 추가 (id 9와 10 사이) | 수정 |
| 오케스트레이터/문서 | `opal/skills/opal-pilot-dev/SKILL.md` | STEP 3.5에 op-scenario-gate 호출 + 게이트 행 advance/mark 배선 + 사람 열람 미러 표 갱신 | 수정 |

#### 2.5.2 현재 구현
- `pipeline.json:14-16` 현행 15행 — id 9(`test_scenario.test_scenario_md`) → id 10(`test_scenario.user_confirm`). 게이트 행 없음.
- `opal-pilot-dev/SKILL.md:84-98` STEP 3.5는 PM이 TEST-SCENARIO.md 작성 후 곧바로 `test_scenario.test_scenario_md --done` mark → 사용자 승인. 게이트 호출 없음(070 결함 지점, → ANALYSIS §1.1 R-5).
- state-tool 검증(직접 코드 확인): `state_tool.py:717-731` spec-validate는 `task_steps[].stage ∈ STAGE_ENUM` + KEY_PATTERN(`{stage_slug}.{item_slug}`)만 검사하고 고정 key 목록에 의존하지 않는다. `check_stage_transition_guard`(`state_tool.py:469-511`)는 행 완료 여부만 일반 판정. → 신규 행 `test_scenario.scenario_gate`(stage `TEST-SCENARIO`, 기존 enum)는 **state_tool.py/schema 변경 없이** 흡수된다.

#### 2.5.3 영향 범위
- 070이 도입한 task-step 키 주소 체계 — 070 이후 addressing은 key 기반이라 id shift가 mode-boundary(`test_scenario.user_confirm` 기준) 로직을 깨지 않는다(`SKILL.md:324-325,351`).
- state-tool 자체는 변경 대상 아님(범위 제외, R-T1/R-T2) — pipeline.json은 스킬 리소스이므로 편집 허용.

---

### F-006: op-task AC 패턴 보강 (상류 동반)

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/op-task/SKILL.md` | AC 작성 가이드에 "교체형 목표 → 잔존0·채택 기준 의무" 패턴 추가 | 수정 |

#### 2.6.2 현재 구현
- `op-task/SKILL.md:100-105` AC 작성 가이드 — Bad/Good 예시 2행. "교체형 목표"(구형→신형 전환) 감지 시 잔존/채택 기준 의무 규칙 부재. 루브릭 ①축(목표달성)·⑤축(채택/잔존)이 채점 가능하려면 AC 단계에서 채택/잔존 기준이 명시돼야 한다(→ TASK §설계방향 6).

#### 2.6.3 영향 범위
- 독립 상류 변경 — F-001~F-005와 파일 교집합 없음. 병렬 가능.

---

### F-007: test-tool 커버리지 서브명령 단위 테스트 (RED-first)

#### 2.7.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| test(Python) | `opal/tools/test-tool/tests/test_scenario.py` | scenario-coverage-check 행위 계약 테스트 + exit 16/17 + 회귀 보호 확장 | 수정 |

#### 2.7.2 현재 구현
- `test_scenario.py:118-127` `BaseScenarioTestCase`(임시 폴더 fixture), `_run`(subprocess 실호출, mock 금지 `red-first.md §4`). 23건, 게이트별 클래스 분리.
- `test_scenario.py:272-306` `TestExistingSuiteRegressionPresence`가 기존 dispatch 키 불변 회귀 보호 — 신규 서브명령도 이 패턴으로 회귀 0 보장(→ ANALYSIS §1.4).

#### 2.7.3 영향 범위
- RED-first 트랙(F-002 = Python 비즈니스 로직, `red-first.md:29-34` 강제 대상) — 테스트 먼저 작성해 RED 증거 확보 후 F-002 impl이 GREEN. 작성자≠구현자(`red-first.md:51-52` [MUST]).

---

### F-008: 자기적용 실증 (음성통제 + 정상수렴)

#### 2.8.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `tasks/073-260723-opd-시나리오-목표커버리지-루프/TEST-SCENARIO.md` | 073 자신의 시나리오 문서 (PM 작성, R-8 대상) | 신규(태스크 산출물) |
| 배치 | `tasks/073-.../SCENARIO-GATE-{N}.md` | 자기적용 게이트 실행 증거 (evaluator 산출) | 신규(실증 증거) |

#### 2.8.2 현재 구현
- 073 자신의 STEP 3.5는 구 흐름으로 TEST-SCENARIO.md를 이미/추후 작성(게이트 기계는 EXECUTE에서 건설 → 순환 의존, R-T7). R-8은 R-1~R-5 구현 완료 후 **등가 자기적용 절차**를 재수행하는 별도 실증 단계.

#### 2.8.3 영향 범위
- 소스 무변경 — 완성된 게이트를 073 자신의 시나리오에 돌려 (a)음성통제 (b)정상수렴을 증거로 남긴다. "Done means verified behavior"(PRINCIPLES §4)의 집행.

---

## 3. 기능별 설계

### F-001: scenario-gate 규칙 SSOT 신설 + harness §1 행

#### 3.1.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/core/references/harness/scenario-gate.md` | 문서/SSOT | 루브릭 6축 + 정규화 계약 + 루프 프로세스 + 종료조건 3종 | (→ D-17 red-first.md 양식) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 2 | `opal/core/references/opal-harness.md` | 문서/SSOT | §1 표에 루프 상한 행 1개 추가 | `opal-harness.md:48-56` |
| 3 | `opal/skills/op-dev-test-scenario/SKILL.md` | 스킬 | scenario-gate.md 참조 + PM Gate에 "목표 커버" 룰 | `op-dev-test-scenario/SKILL.md:159-165` |
| 4 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 가이드 | 목적에 "목표 달성 관점" + Step 1에 목표/R/채택 입력 추가 | `test-scenario-guide.md:11-29` |

#### 3.1.2 문서 구조 설계

`scenario-gate.md` front-matter(→ D-17 `red-first.md:1-6` 양식) + 절 구성(→ TASK §명확화 잠금 파라미터 그대로 반영):

```
---
module: scenario-gate
role: TEST-SCENARIO 목표-커버리지 루브릭 게이트 루프 규칙 SSOT
load: op-scenario-gate 호출 시 / TEST-SCENARIO 작성 시
상속: opal/core/PRINCIPLES.md §4, §Core Stance(enforce-don't-advise)
---
```

- **§1 목적** — TEST-SCENARIO를 "목표 달성 검증"으로 재정의. 070 사건 근거 인용.
- **§2 루브릭 6축 + 판정 주체 분리** [MUST]:
  | 축 | 정의 | 판정 주체 | 척도 |
  |----|------|----------|------|
  | ① 목표 달성 | 사용자/운영 계층에서 태스크 목표를 검증하는 시나리오 존재 | opal-evaluator-agent(판단) | 0~2 |
  | ② 요구 커버 | TASK R·AC ↔ 시나리오 매핑 완전 | test-tool(결정론) | 누락 수 |
  | ③ 기능 커버 | PLAN F ↔ 시나리오 매핑 완전 | test-tool(결정론) | 누락 수 |
  | ④ 리스크 커버 | PLAN H ↔ 시나리오 매핑 완전 | test-tool(결정론) | 누락 수 |
  | ⑤ 채택/잔존 | 교체형 목표=구형 잔존0·신형 채택 검증 시나리오 존재 | opal-evaluator-agent(판단) | 0~2 |
  | ⑥ 경계/부정 | 경계값·부정 경로 시나리오 존재 | opal-evaluator-agent(판단) | 0~2 |
  > [MUST] ②③④는 test-tool `scenario-coverage-check` 결정론, ①⑤⑥은 opal-evaluator-agent `scenario-rubric` phase 판단. 이 경계는 본 문서가 SSOT다. (→ TASK §설계방향 2)
- **§3 정규화 계약** (pilot-중립) [MUST]:
  - 입력(정규화 JSON 페이로드): `{goal, requirements[], features[], hypotheses[], scenarios[]}` — `scenarios[]` 각 항목은 `{id, covers_requirements[], covers_features[], covers_hypotheses[], is_goal_scenario, is_adoption_scenario, is_boundary_scenario}`.
  - 출력(결정론 파트): `{missing: {requirements[], features[], hypotheses[]}}` — 하나라도 비어있지 않으면 FAIL.
  - 출력(판단 파트): `{scores: {goal, adoption, boundary}, gaps[]}`.
  - opd 1차 접합: op-scenario-gate 스킬이 TEST-SCENARIO.md §1(가설 표)·§4(매핑 표) + TASK R/AC + PLAN F/H를 읽어 위 페이로드로 변환(변환 책임은 스킬, 도구는 pilot-중립 페이로드만 소비). (→ ANALYSIS §4 발견①, R-T3)
- **§4 루프 프로세스**: Producer(작성) → `scenario-coverage-check`(결정론 게이트) → opal-evaluator-agent(`scenario-rubric`, 판단) → 종료조건 판정 → 재작성. Producer≠Evaluator 매 반복 유지.
- **§5 종료조건 3종** [MUST] (TASK 잠금 파라미터 그대로):
  1. **수렴(PASS)**: 커버리지 누락=0 (hard gate) AND 판단축 각 ≥1점(0점 축 없음) AND 평균 ≥1.5점(2점 척도 0~2).
  2. **반복 상한**: MAX=3 초과 → 캡틴 에스컬레이션. (수치는 opal-harness.md §1 신규 행 참조 — 본 문서 비복제, `loop-control.md:41` 원칙)
  3. **무진전**: 연속 2회 gaps·점수 개선 없음 → 캡틴 에스컬레이션. (신호 정의는 `loop-control.md:59-68` §4 참조)
- **§6 tool-gated 집행** [MUST]: 게이트 PASS는 test-tool exit 0(누락=0) AND evaluator verdict pass(판단축 임계 충족) 두 증거가 모두 존재할 때만. PM은 두 도구 출력 없이 게이트 통과를 선언할 수 없다. (`PRINCIPLES.md:15` enforce-don't-advise)

opal-harness.md §1 신규 행(→ R-T5):
```
| 시나리오 목표-커버 게이트 (루브릭 미달) | 3회 | 캡틴(사용자) 에스컬레이션 |
```
> [MUST] `opal-harness.md` §1이 루핑 상한 수치 SSOT — scenario-gate.md·op-scenario-gate는 3회를 복제하지 않고 이 행을 참조한다(`loop-control.md:143` "본 문서는 참조만, 복제하지 않음" 원칙 준용).

#### 3.1.3 환경 변경
해당 없음.

#### 3.1.4 배치/마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC | 산출물 검사 | scenario-gate.md에 6축·판정주체분리·정규화계약·3종료조건 절이 모두 존재하고 op-dev-test-scenario가 이를 참조 |
| TS-002 | R-T5 | 산출물 검사 | opal-harness.md §1에 신규 루프 행(3회) 존재 + scenario-gate.md가 수치 복제 없이 참조 |

---

### F-002: test-tool 커버리지 서브명령 (scenario-coverage-check)

#### 3.2.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/test-tool/lib/scenario.py` | BE(Python) | `cmd_scenario_coverage_check` 핸들러 + 파서 + `SCENARIO_DISPATCH["scenario-coverage-check"]` + 에러코드 2종 | `scenario.py:352-388,511-519` |

#### 3.2.2 API·데이터 모델 설계

```python
# scenario.py — SCENARIO_ERROR_CODES에 추가 (exit 15는 회피, 16부터 배정)
"coverage_unmet":          "요구/기능/가설 미커버 존재 — scenario-coverage-check 거부(R-2)",   # exit 16
"coverage_input_invalid":  "--coverage-input JSON 파싱/스키마 실패 — scenario-coverage-check 거부",  # exit 17

def cmd_scenario_coverage_check(args: argparse.Namespace) -> None:
    """scenario-coverage-check — 정규화 페이로드의 R/F/H ↔ 시나리오 매핑 커버리지를
    결정론 판정한다(루브릭 ②③④). test-scenario.json SSOT 미접촉 — pilot-중립 transient
    페이로드(--coverage-input <path> 또는 stdin)만 소비한다(축 분리, ANALYSIS §4 발견①).
    ①⑤⑥ 판단축은 판정하지 않는다(opal-evaluator-agent 소관)."""
```
- 입력 계약: `--coverage-input <path>`(JSON 파일) 필수. 페이로드 = `{goal, requirements[], features[], hypotheses[], scenarios[]}` (→ scenario-gate.md §3). `goal`은 통과 응답에 echo만(도구는 목표달성 판정 안 함).
- 판정 로직: `covered_r = ⋃ scenarios[].covers_requirements`; `missing.requirements = requirements - covered_r` (F·H 동일). 셋 중 하나라도 non-empty → `_error("coverage_unmet", "scenario-coverage-check", 16, detail={missing})`. 모두 empty → `_respond({ok:True, command, all_covered:True, counts:{...}}, 0)`.
- 파싱/스키마 실패(파일 부재·JSON 오류·필수 키 누락) → `_error("coverage_input_invalid", ..., 17, detail=...)`.
- [MUST] exit 16/17 배정 전 EXECUTE 워커는 `scenario.py` 실사용 최대 exit code를 재확인하고(현행 14, 15는 정보용 예약) 충돌 없이 16부터 이어 배정한다 (`scenario.py:32-34` 회귀 보호 원칙).
- [MUST] `_respond`/`_error`는 단일라인 JSON 계약 유지(`scenario.py:96-112`) — 기존 서브명령과 동일 출력 규약.
- [MUST] 기존 7서브명령 로직·`SCENARIO_ERROR_CODES` 기존 키 무변경 — 추가만(additive, `scenario.py:6` 모듈 격리 규율).

> 근거: `scenario.py:96-112`(_respond/_error 계약), `scenario.py:352-388`(fidelity-check 핸들러 선례), `test_tool.py:238-246`(자동 dispatch 병합).

#### 3.2.3 환경 변경
해당 없음 (Python stdlib argparse/json).

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-003 | R-2 AC (누락 시 FAIL) | 기능 테스트 | R/F/H 중 미커버 존재 시 exit 16 + `detail.missing`에 미매핑 목록 |
| TS-004 | R-2 AC (완전 시 ok) | 기능 테스트 | 전 R/F/H 커버 시 exit 0 + `all_covered:true` |
| TS-005 | R-2 (입력 검증) | 기능 테스트 | 잘못된 페이로드/부재 파일 시 exit 17 |
| TS-006 | H-2 (회귀) | 회귀 테스트 | 기존 7서브명령 dispatch 키·exit 8~14 불변 |

---

### F-003: opal-evaluator-agent scenario-rubric phase

#### 3.3.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/agents/opal-evaluator-agent/AGENT.md` | 에이전트/문서 | phase 열거값 `scenario-rubric` 추가 + Phase 1 판단축 루브릭 + Phase 5 보고서명 규칙 | `AGENT.md:27,37-55,90-95` |

#### 3.3.2 설계

- `AGENT.md:27` phase 설명에 `scenario-rubric`(op-scenario-gate 루프에서 목표-커버 시나리오 판단축 채점) 추가.
- Phase 1: `phase == "scenario-rubric"`일 때 전용 2점 척도 루브릭 적용(기존 Likert 1–5와 분리):
  | 판단축 | 척도 | 통과선 | 앵커 |
  |--------|------|--------|------|
  | ① 목표 달성 | 0~2 | ≥1 | 0: 목표 검증 시나리오 없음 / 2: 사용자·운영 계층에서 목표를 직접 검증 |
  | ⑤ 채택/잔존 | 0~2 | ≥1 | 0: 교체형인데 잔존/채택 미검증 / 2: 구형 잔존0·신형 채택 모두 검증 |
  | ⑥ 경계/부정 | 0~2 | ≥1 | 0: 정상 경로만 / 2: 경계·부정 경로 시나리오 존재 |
  > [MUST] verdict 규칙: 세 축 각 ≥1점(0점 축 없음) AND 평균 ≥1.5 → `verdict: pass`, 아니면 `fail` + 미달 축별 `gaps[]`. (→ scenario-gate.md §5-1, TASK 잠금 파라미터)
- Phase 4 결과 계약 확장: `{scores:{goal,adoption,boundary}, average, gaps[], verdict}` 반환.
- Phase 5 보고서 경로 분기 추가: `phase == "scenario-rubric"` → `{task_folder}/SCENARIO-GATE-{iteration}.md` (iteration은 입력 파라미터, op-scenario-gate가 회차 부여). VERIFICATION.md 폴백 대신 전용 파일명 명시(→ R-T6).
- 입력 명세에 `iteration`(회차)·`scenario_source`(정규화 페이로드 또는 TEST-SCENARIO.md 경로) 파라미터 추가.
- [MUST] 기존 3 phase(design-review/spec-review/drift-recheck) 판정·보고서 경로 무변경 — additive(H-6, `AGENT.md:92-94`). readonly·verdict-only·`tools` 불변(`AGENT.md:9,123`).

> 근거: `AGENT.md:37-55`(Base 루브릭 표), `AGENT.md:90-95`(보고서 경로 분기).

#### 3.3.3 환경 변경 / 3.3.4 배치
해당 없음.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-007 | R-3 AC | 산출물 검사 | AGENT.md에 scenario-rubric phase·판단축 루브릭·verdict 규칙·SCENARIO-GATE-{N}.md 경로 존재 |
| TS-008 | H-6 (회귀) | 산출물 검사 | 기존 3 phase 계약·척도·보고서 경로 무변경 (additive 확인) |

---

### F-004: op-scenario-gate 단계 스킬

#### 3.4.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/skills/op-scenario-gate/SKILL.md` | 스킬 | 커버리지 도구→평가자→종료조건 루프 컨트롤 (단일 호출 지점) | (→ D-8 loop-control.md) |

#### 3.4.2 설계

프로세스(SKILL.md 본문):
1. **입력**: `task_folder`, `producer_artifact`(opd=TEST-SCENARIO.md), `pilot`(=opd), `iteration`(초기 1).
2. **정규화 페이로드 빌드**: TEST-SCENARIO.md §1(가설)·§4(매핑) + TASK.md R/AC + PLAN.md F/H를 읽어 scenario-gate.md §3 페이로드 JSON 생성 → `{task_folder}/.scenario-coverage-input.json`.
3. **결정론 게이트**: `test-tool scenario-coverage-check --coverage-input <path>` 호출.
   - exit 16(누락 존재) → 커버리지 FAIL, `missing` 수집 → 종료조건 판정(6)으로.
   - exit 0 → 판단축 채점(4)으로.
4. **판단 게이트**: `opal-evaluator-agent` 디스패치 `phase=scenario-rubric, iteration=<N>, scenario_source=<페이로드/TEST-SCENARIO.md>`. verdict + scores + gaps + `SCENARIO-GATE-{N}.md` 수신.
5. **종료조건 3종 판정** (scenario-gate.md §5):
   - 수렴: 누락=0 AND 판단축 각≥1 AND 평균≥1.5 → `verdict: pass`(게이트 통과) 반환.
   - 반복 상한: N>3(MAX) → `verdict: escalate` 반환 (캡틴 에스컬레이션).
   - 무진전: (missing∪gaps) 연속 2회 동일/미개선 → `verdict: escalate`.
   - 그 외(recoverable, N≤3, 진전): `verdict: rewrite` + gaps 반환 → Producer(PM+캡틴)가 재작성 후 iteration+1로 재호출.
6. **반환 계약**: `{verdict: pass|rewrite|escalate, missing, scores, gaps[], report_path, iteration}`.

> [MUST] tool-gated: 게이트 pass 반환은 반드시 (3)의 exit 0 AND (4)의 evaluator verdict pass 두 증거가 있을 때만 — PM 자체 판단으로 pass를 만들 수 없다(H-5, `PRINCIPLES.md:15`).
> [MUST] Producer≠Evaluator: 작성자(PM+캡틴)와 채점자(opal-evaluator-agent 서브에이전트 디스패치)를 매 반복 분리 유지(`AGENT.md:16-18` 생성자≠평가자 헌법, TASK §설계방향 3).
> [MUST] 루프 상한/무진전 수치는 scenario-gate.md §5(→ opal-harness.md §1)를 참조하며 SKILL 본문에 복제하지 않는다.

#### 3.4.3 환경 변경 / 3.4.4 배치
해당 없음.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-009 | R-4 AC (재사용) | 산출물 검사 | 단일 호출로 커버리지→평가자→종료조건이 정의되고, 정규화 페이로드로 pilot-중립 |
| TS-010 | H-4 (경계 종료) | 통합 테스트 | 3종료조건이 명시되고 각 verdict(pass/rewrite/escalate) 분기 존재 |

---

### F-005: opd STEP 3.5 접합

#### 3.5.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-pilot-dev/references/pipeline.json` | 오케스트레이터 리소스 | `test_scenario.scenario_gate` 행 추가(id 10, stage TEST-SCENARIO, item "목표-커버 게이트") | `pipeline.json:14-16` |
| 2 | `opal/skills/opal-pilot-dev/SKILL.md` | 오케스트레이터/문서 | STEP 3.5에 op-scenario-gate 호출+게이트 행 배선, 미러 표 15→16행 | `SKILL.md:84-98,281-302` |

#### 3.5.2 설계 — R-5 접합 방식 결정 (R-T2 해소)

**결정: pipeline.json에 신규 task-step 행 추가 (Option B 채택)**. `test_scenario.test_scenario_md` 완료 조건 흡수(Option A) 대신 신규 행을 선택한다.

근거:
- state-tool 코드 직접 확인(`state_tool.py:717-731` spec-validate, `:469-511` stage-transition guard): 고정 key 목록 비의존 + stage enum(`TEST-SCENARIO` 기존 포함) + KEY_PATTERN(`test_scenario.scenario_gate` 부합) → **state_tool.py/schema 무변경**으로 신규 행 흡수(범위 제외 제약 R-T1/R-T2 준수).
- stage-transition guard가 게이트 행 미완료 시 EXECUTE(`execute.implement`) 진입 mark를 자동 거부 → R-5 AC "게이트 미통과 시 EXECUTE 차단"을 **구조적으로 집행**(산문 아님, `PRINCIPLES.md:15`). Option A(흡수)는 이 구조적 차단이 없어 산문 의존.
- red-first.md §6이 RED를 EXECUTE 내부로 흡수한 것과 달리, 목표-커버 게이트는 독립 산출물(SCENARIO-GATE-{N}.md)·독립 채점자를 갖는 QA성 체크포인트 → PM Gate 행과 동격으로 별도 행이 정합.

pipeline.json 신규 행 (id 9와 10 사이 삽입, 이후 id 재부여):
```json
{ "id": 10, "key": "test_scenario.scenario_gate", "stage": "TEST-SCENARIO", "item": "목표-커버 게이트" }
```
- 순서: id 9 `test_scenario.test_scenario_md`(작성) → id 10 `test_scenario.scenario_gate`(게이트) → id 11 `test_scenario.user_confirm`(사용자 확인). 이후 execute~close 행 id +1.

opal-pilot-dev/SKILL.md STEP 3.5 개정:
- TEST-SCENARIO.md 작성(`test_scenario.test_scenario_md --done` mark) 후 → `test_scenario.scenario_gate` advance → **op-scenario-gate 호출** → `verdict: pass`일 때만 게이트 행 `--done` mark → 사용자 승인(`test_scenario.user_confirm`).
- `verdict: rewrite` → PM+캡틴 재작성 후 재호출(루프). `verdict: escalate` → 사용자 에스컬레이션.
- 사람 열람 미러 표(`SKILL.md:281-302`) 15→16행 갱신 + "게이트 행은 op-scenario-gate `verdict:pass` 후에만 mark" 주석.

> [MUST] state-tool 자체(state_tool.py/schema/tests)는 변경하지 않는다 — pipeline.json(스킬 리소스)만 편집(R-T1/R-T2, TASK §제약).
> [MUST] EXECUTE 워커는 신규 pipeline.json에 대해 `state-tool spec-validate`를 실행해 무코드변경 흡수를 실증한다(H-3). 만약 spec-validate가 거부하면 즉시 블로커 보고 후 Option A(흡수)로 폴백한다.

#### 3.5.3 환경 변경 / 3.5.4 배치
해당 없음.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-011 | R-5 AC / H-3 | 통합 테스트 | 신규 pipeline.json으로 `state-tool init` + `spec-validate` 통과, 게이트 행 미완 시 EXECUTE 행 mark 거부 |
| TS-012 | R-5 AC / H-5 | 통합 테스트 | op-scenario-gate verdict≠pass일 때 게이트 행 mark 안 됨 → EXECUTE 차단 유지 |

---

### F-006: op-task AC 패턴 보강

#### 3.6.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/op-task/SKILL.md` | 스킬 | AC 작성 가이드에 교체형 목표 패턴 추가 | `op-task/SKILL.md:100-105` |

#### 3.6.2 설계
- `op-task/SKILL.md:100` AC 작성 가이드 하위에 규칙 추가: "교체형 목표(구형→신형 전환·대체·마이그레이션)를 감지하면 AC에 (a)구형 잔존0 (b)신형 채택 검증 기준을 의무로 포함한다." + Bad/Good 예시 1행.
- 목적: 루브릭 ①(목표달성)·⑤(채택/잔존)이 하류에서 채점 가능하도록 상류 AC 품질을 보장(→ TASK §설계방향 6).
- [MUST] 상류 동반 변경 — R-1~R-5와 파일 교집합 없음, 독립.

#### 3.6.3 환경 / 3.6.4 배치
해당 없음.

#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-013 | R-6 AC | 산출물 검사 | op-task/SKILL.md AC 가이드에 교체형 목표=잔존0·채택 패턴 + 예시 존재 |

---

### F-007: test-tool 커버리지 서브명령 단위 테스트

#### 3.7.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/test-tool/tests/test_scenario.py` | test(Python) | scenario-coverage-check 계약 테스트 클래스 + 회귀 클래스 확장 | `test_scenario.py:118-127,272-306` |

#### 3.7.2 설계
- 신규 테스트 클래스(`BaseScenarioTestCase` 상속, subprocess 실호출, mock 금지 `red-first.md §4`):
  - `TestScenarioCoverageCheckUnmet`: 미커버 R/F/H 시 exit 16 + `missing` (TS-003).
  - `TestScenarioCoverageCheckComplete`: 전 커버 시 exit 0 + `all_covered:true` (TS-004).
  - `TestScenarioCoverageInputInvalid`: 부재/오류 페이로드 시 exit 17 (TS-005).
  - `TestExistingSuiteRegressionPresence` 확장 또는 신규 회귀 케이스: 기존 7서브명령 키·exit 불변 (TS-006/H-2).
- [MUST] RED-first: 이 테스트를 F-002 impl 전에 작성해 RED(전부 FAIL) 증거 확보 → F-002가 GREEN 전환. 작성자≠구현자(`red-first.md:51-52`).
- 공개 인터페이스(exit code + stdout JSON)만 단언, 내부 함수 결합 금지(`red-first.md:64-67`).

#### 3.7.3 환경 / 3.7.4 배치
해당 없음 (pytest 9.1.0, 기존 스위트).

#### 3.7.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-014 | R-7 AC | 회귀 테스트 | `test_scenario.py` 전체 스위트 PASS (기존 23건 + 신규) + `test_test_tool.py` 회귀 0 |

---

### F-008: 자기적용 실증

#### 3.8.1 파일 변경 계획
**신규 생성** (태스크 산출물, 소스 아님)
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `tasks/073-.../SCENARIO-GATE-1.md` 등 | 배치 | 자기적용 게이트 실행 증거 | (→ R-8) |

#### 3.8.2 설계 — 실행 순서 (R-T7 해소)
- [MUST] R-1~R-5 + R-7 구현·GREEN 완료 후에만 R-8 실행(순환 의존 해소, R-T7).
- **(a) 음성통제**: 073 TEST-SCENARIO.md에서 목표-커버 시나리오(예: "opd STEP 3.5 게이트가 EXECUTE를 실제 차단하는지")를 의도적으로 누락한 페이로드로 op-scenario-gate 호출 → 커버리지 exit 16 또는 evaluator ①=0 → `verdict: rewrite`(게이트 FAIL) → 재작성 유도 확인. 증거 = SCENARIO-GATE-1.md(FAIL).
- **(b) 정상수렴**: 누락 시나리오 복원 후 재호출 → 누락=0 AND 판단축 각≥1 AND 평균≥1.5 → `verdict: pass`(수렴). 증거 = SCENARIO-GATE-2.md(PASS).
- 두 증거 모두 태스크 폴더에 남겨 "게이트가 목표 누락을 실제로 잡는다"를 실증(PRINCIPLES §4 "Done means verified behavior").

#### 3.8.3 환경 / 3.8.4 배치
해당 없음.

#### 3.8.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-015 | R-8 AC / H-7 (음성통제) | 통합 테스트 | 목표-커버 시나리오 의도 누락 시 게이트 FAIL→재작성 유도 (SCENARIO-GATE-1.md에 FAIL 증거) |
| TS-016 | R-8 AC (정상수렴) | 통합 테스트 | 누락 복원 후 게이트 PASS 수렴 (SCENARIO-GATE-2.md에 PASS 증거) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001, F-006 | 1, 2 | opal-task-agent | 병렬 가능 | F-001=하류 계약 정의(선행), F-006=독립 상류 |
| 2 | F-007 → F-002 | 3, 4 | opal-test-agent(red) → opal-be-agent | 순차 (RED→GREEN) | 동일 test-tool 모듈 |
| 2 | F-003 | 5 | opal-task-agent | Phase2 내 병렬 | evaluator AGENT.md (독립 파일) |
| 3 | F-004 | 6 | opal-task-agent | 순차 | F-001·F-002·F-003 완료 후 |
| 4 | F-005 | 7 | opal-task-agent | 순차 | F-004 완료 후 |
| 5 | (docs) | 8 | PM 직접 | 순차 | 신규 컴포넌트 → PROJECT.md |
| 6 | F-008 | 9 | PM 직접 | 순차 | 전 구현 완료 후 자기적용 |

### 4.2 실행 체크리스트
> 총 9개 Step | Phase 6개 | 실행 모드: 복잡

#### Step 1: scenario-gate.md SSOT + harness §1 루프 행
- [x] 완료
- **소속 기능**: F-001
- **영역**: 문서/SSOT
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/scenario-gate.md`(신규), `opal/core/references/opal-harness.md`(수정), `opal/skills/op-dev-test-scenario/SKILL.md`(수정), `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`(수정)
- **작업 내용**: §3.1.2 구조대로 scenario-gate.md 작성(6축·판정주체분리·정규화계약·루프·3종료조건·tool-gated). opal-harness.md §1에 "시나리오 목표-커버 게이트 3회" 행 추가. op-dev-test-scenario SKILL/guide가 scenario-gate.md를 참조하고 목표/채택 관점을 도출 입력·PM Gate에 추가.
- **완료 기준**: TS-001·TS-002 충족 — 4개 절 존재 + harness 행 존재 + 수치 비복제 참조 + op-dev-test-scenario 참조 반영
- **테스트**: TS-001, TS-002
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: op-task AC 패턴 보강
- [x] 완료
- **소속 기능**: F-006
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-task/SKILL.md`
- **작업 내용**: AC 작성 가이드에 교체형 목표=잔존0·채택 의무 패턴 + Bad/Good 예시 1행 추가.
- **완료 기준**: TS-013 충족
- **테스트**: TS-013
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 1과 병렬)

#### Step 3: test-tool 커버리지 서브명령 RED 테스트 작성
- [ ] 완료
- **소속 기능**: F-007
- **영역**: test(Python)
- **agent**: opal-test-agent (mode: red)
- **파일**: `opal/tools/test-tool/tests/test_scenario.py`
- **작업 내용**: §3.7.2 신규 테스트 클래스 4종 작성(coverage_unmet exit16 / complete exit0 / input_invalid exit17 / 회귀). subprocess 실호출·mock 금지. RED 증거(전부 FAIL) 기록.
- **완료 기준**: 신규 케이스가 RED(FAIL)로 실행됨 — RED 증거 확보
- **테스트**: TS-003~TS-006, TS-014 (RED 상태)
- **실행 방법**: sub-agent
- **의존**: Step 1 (scenario-gate.md §3 정규화 계약 확정 후)

#### Step 4: test-tool scenario-coverage-check 구현 (GREEN)
- [x] 완료
- **소속 기능**: F-002
- **영역**: BE(Python)
- **agent**: opal-be-agent
- **파일**: `opal/tools/test-tool/lib/scenario.py`
- **작업 내용**: §3.2.2 `cmd_scenario_coverage_check` + 파서 + `SCENARIO_DISPATCH` 키 + 에러코드 exit 16/17 배정. 기존 7서브명령·에러코드 무변경.
- **완료 기준**: TS-003~TS-006 GREEN + TS-014 스위트 PASS + `test_test_tool.py` 회귀 0
- **테스트**: TS-003, TS-004, TS-005, TS-006, TS-014
- **실행 방법**: sub-agent
- **의존**: Step 3 (RED 증거 후 GREEN)

#### Step 5: opal-evaluator-agent scenario-rubric phase
- [x] 완료
- **소속 기능**: F-003
- **영역**: 에이전트/문서
- **agent**: opal-task-agent
- **파일**: `opal/agents/opal-evaluator-agent/AGENT.md`
- **작업 내용**: §3.3.2 phase 열거 `scenario-rubric` 추가 + 판단축 2점 척도 루브릭 + verdict 규칙(각≥1 AND 평균≥1.5) + Phase 5 `SCENARIO-GATE-{N}.md` 경로 + iteration 입력. 기존 3 phase 무변경.
- **완료 기준**: TS-007·TS-008 충족
- **테스트**: TS-007, TS-008
- **실행 방법**: sub-agent
- **의존**: Step 1 (scenario-gate.md §2 판정주체·§5 임계 확정 후). Step 3/4와 병렬 가능(다른 파일).

#### Step 6: op-scenario-gate 단계 스킬 신설
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-scenario-gate/SKILL.md`(신규)
- **작업 내용**: §3.4.2 루프 프로세스 6단계(정규화 빌드→coverage-check→evaluator→종료조건→반환). tool-gated·Producer≠Evaluator·수치 비복제 [MUST] 명문화.
- **완료 기준**: TS-009·TS-010 충족
- **테스트**: TS-009, TS-010
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 4, Step 5

#### Step 7: opd STEP 3.5 접합 (pipeline.json + SKILL)
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 오케스트레이터/문서
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-dev/references/pipeline.json`, `opal/skills/opal-pilot-dev/SKILL.md`
- **작업 내용**: §3.5.2 pipeline.json에 `test_scenario.scenario_gate` 행(id 10) 추가+id 재부여. SKILL STEP 3.5에 op-scenario-gate 호출·게이트 행 배선·미러 표 16행 갱신. state-tool 자체 무변경.
- **완료 기준**: TS-011·TS-012 충족 — `state-tool spec-validate` 통과 + 게이트 행 미완 시 EXECUTE mark 거부
- **테스트**: TS-011, TS-012
- **실행 방법**: sub-agent
- **의존**: Step 6

#### Step 8: docs/ 갱신 (PROJECT.md 신규 컴포넌트)
- [ ] 완료
- **소속 기능**: F-001~F-005 (신규 공유 컴포넌트 도입)
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/PROJECT.md`
- **작업 내용**: 신규 공유 컴포넌트(scenario-gate.md SSOT·op-scenario-gate 스킬·test-tool scenario-coverage-check·evaluator scenario-rubric phase)를 PROJECT.md 관련 컴포넌트 표/변경이력에 반영.
- **완료 기준**: PROJECT.md에 신규 컴포넌트 항목 + 변경이력 1행 기재
- **테스트**: 산출물 검사 (PM Gate)
- **실행 방법**: direct
- **의존**: Step 1~7 완료 후

#### Step 9: 자기적용 실증 (음성통제 + 정상수렴)
- [ ] 완료
- **소속 기능**: F-008
- **영역**: 배치
- **agent**: PM 직접
- **파일**: `tasks/073-.../TEST-SCENARIO.md`, `tasks/073-.../SCENARIO-GATE-{N}.md`
- **작업 내용**: §3.8.2 완성된 op-scenario-gate를 073 자신의 TEST-SCENARIO에 적용 — (a)목표-커버 시나리오 의도 누락→게이트 FAIL→재작성 유도 (b)복원→PASS 수렴. 두 증거 남김.
- **완료 기준**: TS-015(FAIL 증거)·TS-016(PASS 증거) 둘 다 실증
- **테스트**: TS-015, TS-016
- **실행 방법**: direct
- **의존**: Step 1, 4, 5, 6, 7 (R-1~R-5 + R-7 완료 후)

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 ∥ Step 2 | 독립 파일(harness/scenario-gate vs op-task), 독립 기능 |
| Step 3 → Step 4 | RED-first — 동일 test-tool 모듈, 테스트(RED) 후 구현(GREEN), 작성자≠구현자 |
| Step 5 ∥ Step 3/4 | evaluator AGENT.md는 test-tool과 다른 파일 — 병렬 가능 (둘 다 Step 1 계약 의존) |
| Step 6 ← Step 1,4,5 | op-scenario-gate는 SSOT·도구·평가자 3자를 배선 |
| Step 7 ← Step 6 | opd 접합은 op-scenario-gate 완성 후 |
| Step 8 ← Step 1~7 | 신규 컴포넌트 확정 후 문서 갱신 |
| Step 9 ← Step 1,4,5,6,7 | 자기적용은 게이트 기계 완성 후 (R-T7 순환 의존 해소) |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | SSOT 6축·계약·종료조건 완비 + harness 행 | TS-001, TS-002 | 4개 절 존재 + harness 행 존재 + 수치 비복제 |
| F-002 | 커버리지 결정론 판정 정확 | TS-003, TS-004, TS-005 | 미커버=exit16+missing / 완전=exit0 / 오류=exit17 |
| F-003 | scenario-rubric phase + 척도 + 보고서명 | TS-007 | phase·판단축·verdict규칙·SCENARIO-GATE-{N}.md 존재 |
| F-004 | 루프 컨트롤 종료조건 3종 | TS-009, TS-010 | 커버리지→평가자→3종료조건 verdict 분기 존재 |
| F-005 | 게이트 행 + EXECUTE 차단 | TS-011, TS-012 | spec-validate 통과 + 게이트 미통과 시 EXECUTE mark 거부 |
| F-006 | 교체형 목표 AC 패턴 | TS-013 | 잔존0·채택 패턴 + 예시 존재 |
| F-007 | 단위 테스트 + 회귀 0 | TS-006, TS-014 | 전체 스위트 PASS + 기존 키/exit 불변 |
| F-008 | 자기적용 음성통제 + 수렴 | TS-015, TS-016 | FAIL→재작성 유도 + PASS 수렴 둘 다 증거 |

### 5.2 회귀 테스트
- [ ] 기존 scenario-* 7서브명령 dispatch 키·exit 8~14 불변 (H-2)
- [ ] `test_test_tool.py` 12건 무영향 (scenario.py 격리)
- [ ] opal-evaluator-agent 기존 3 phase(design/spec/drift) 계약·보고서 경로 무변경 (H-6)
- [ ] opd 기존 파이프라인 흐름(15행 키)이 게이트 행 추가로 mode-boundary·id 참조를 깨지 않음
- [ ] state-tool 자체(state_tool.py/schema/tests) 무변경 확인 (범위 제외)

### 5.3 코드/문서 품질
- [ ] scenario.py @header exports/description에 신규 서브명령 반영 (`scenario.py:6-21` 규율)
- [ ] SCENARIO_ERROR_CODES 신규 키가 기존과 exit 충돌 없음 (16부터)
- [ ] 각 수정 문서에 변경이력 행 추가 (버전·KST 일시·내용)
- [ ] 인라인 인용((→ D-N §N) 또는 경로:줄번호) 유지, 프로젝트 컨벤션 준수

### 5.4 보안
- [ ] .env·인증 파일 무관 (프레임워크 내부 변경, 신규 시크릿 없음)
- [ ] 코드에 하드코딩 토큰/시크릿 없음
- [ ] coverage-input 페이로드 파싱 시 임의 파일 경로 신뢰 — task_folder 하위 경로만 소비(경로 이탈 방지 확인)

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 9개 | 복잡 |
| 변경 파일 수 | 소스 11개(신규 2 + 수정 9) | 복잡 |
| 모듈 범위 | 다중 (harness SSOT·test-tool·evaluator·스킬 2·오케스트레이터) | 복잡 |
| 작업 유형 | 프레임워크 대규모 개선 (신규 공유 컴포넌트) | 복잡 |
| 외부 의존성 | 없음 (Python stdlib·Markdown) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
```
Batch 1 (병렬):  opal-task-agent[Step1: F-001]  ∥  opal-task-agent[Step2: F-006]
Batch 2:         opal-test-agent(red)[Step3: F-007 RED]  →  opal-be-agent[Step4: F-002 GREEN]
                 opal-task-agent[Step5: F-003]  (Batch2 내 병렬, Step1 완료 후)
Batch 3:         opal-task-agent[Step6: F-004]        (Batch1·2 완료 후)
Batch 4:         opal-task-agent[Step7: F-005]        (Batch3 완료 후)
Batch 5:         PM 직접[Step8: docs] → PM 직접[Step9: F-008 자기적용]
```
- **파일 충돌 방지**: test-tool 모듈(scenario.py/test_scenario.py)은 Step3→Step4 순차 동일 흐름 — 다른 에이전트지만 RED→GREEN 순서로 충돌 없음. 문서/스킬 파일은 각 Step이 배타적 파일 소유.
- **agent 배정 근거**:
  - **Python(Step 4 F-002 impl)=opal-be-agent**: 신규 결정론 게이트 로직·에러코드 네임스페이스·JSON 계약·argparse는 실질 백엔드 Python 엔지니어링 — BE 전문 에이전트가 적합. 단 프레임워크 고유 규율(@header·exit code 16 배정·모듈 격리·KST·단일라인 JSON)을 디스패치 프롬프트에 [MUST]로 주입해 컨벤션 격차를 보완한다. (대안: PROJECT.md Framework→opal-task-agent 매핑. 본 PLAN은 Python 깊이를 근거로 BE 배정, PM이 오버라이드 가능.)
  - **RED 테스트(Step 3 F-007)=opal-test-agent(mode:red)**: red-first.md §2 [MUST] "RED 작성 주체는 구현자(op-dev-execute)와 분리" → 테스트 작성=test-agent(red), 구현=be-agent로 작성자≠구현자를 구조적으로 충족.
  - **마크다운 SSOT·스킬·AGENT.md(Step 1·2·5·6·7)=opal-task-agent**: 프레임워크 문서/스킬 범용 전문 — PROJECT.md Framework 매핑 정합. 인용·변경이력·[MUST] 규율에 익숙.
  - **docs·자기적용(Step 8·9)=PM 직접**: docs/ 갱신은 PM 직접 규칙, 자기적용은 op-scenario-gate 루프 오케스트레이션+evaluator 디스패치라 PM 소관.

### C-2. 스킬 요구사항
- 신규 스킬: `op-scenario-gate`(F-004) — 3개 이상 pilot 재사용 후보이나 1차는 opd 단일 호출(TASK §범위). 기존 스킬 매칭: 없음(신규 얇은 단계 스킬).
- 기존 재사용: op-dev-test-scenario(접합), opal-evaluator-agent(phase 확장), test-tool(서브명령 확장) — 모두 확장이며 신규 pilot·tool·agent 없음(TASK §설계방향 5 준수).

### C-3. 도구 요구사항
- test-tool CLI(신규 서브명령 scenario-coverage-check) — Python stdlib만.
- state-tool CLI(`init`/`spec-validate`/`mark`) — 검증용 호출만, 코드 무변경.
- pytest 9.1.0 — 기존 스위트.
- MCP·외부 패키지 없음.

### C-4. 테스트 전략
- **기능 테스트**: `test_scenario.py` 신규 케이스 — `bash opal/tools/test-tool/run.sh scenario-coverage-check ...` subprocess 실호출로 exit code+JSON 단언. `python -m pytest opal/tools/test-tool/tests/test_scenario.py`.
- **회귀 테스트**: `python -m pytest opal/tools/test-tool/tests/` 전체 — 기존 23+12건 무회귀.
- **통합 테스트(L2)**: state-tool 실 CLI로 신규 pipeline.json init→spec-validate→게이트 행 미완 시 EXECUTE mark 거부 확인.
- **자기적용(L2/L3)**: op-scenario-gate 실행으로 음성통제(FAIL)·정상수렴(PASS) 증거 — R-8.
- **코드 품질**: @header 정합·변경이력·단일라인 JSON 계약.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| test-tool 확장 | Python 3.14 stdlib (argparse/json), pytest 9.1.0 | (프레임워크 내부, 외부 커뮤니티 스킬 없음) |
| SSOT·스킬·AGENT.md | Markdown | - |
| 파이프라인 스펙 | JSON (pipeline.json, JSON Schema Draft-07) | - |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (해당 없음) | 순수 내부 개선, 외부 라이브러리 조사 불요 (→ ANALYSIS §6.3) |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | op-dev-test-scenario SKILL | `opal/skills/op-dev-test-scenario/SKILL.md` | R-1 접합·현행 결함(PM Gate 목표커버 부재) |
| D-2 | 설계 | test-scenario-guide | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | R-1 도출 엔진 결함 근거 |
| D-3 | 설계 | opal-evaluator-agent | `opal/agents/opal-evaluator-agent/AGENT.md` | R-3 재사용 대상(scenario-rubric phase) |
| D-4 | 소스 | test-tool scenario.py | `opal/tools/test-tool/lib/scenario.py` | R-2 확장 대상·에러코드/dispatch 패턴 |
| D-6 | 설계 | opal-pilot-dev SKILL | `opal/skills/opal-pilot-dev/SKILL.md` | R-5 STEP 3.5 접합 |
| D-8 | 설계 | oppl loop-control 가이드 | `opal/skills/opal-pilot-project-loop/references/loop-control.md` | R-4 종료조건·무진전·비복제 선례 |
| D-9 | 설계 | opal-harness.md §1 | `opal/core/references/opal-harness.md` | 루핑 상한 SSOT — 신규 행 추가 위치 (R-T5) |
| D-10 | 소스 | backlog-tool coverage-check | `opal/tools/backlog-tool/backlog_tool.py:589-620` | R-2 결정론 커버리지 게이트 패턴 |
| D-15 | 소스 | test-scenario.schema.json | `opal/tools/test-tool/schema/test-scenario.schema.json` | R-2 스키마 무변경 판단 근거 |
| D-16 | 소스 | test_scenario 테스트 | `opal/tools/test-tool/tests/test_scenario.py` | R-7 테스트 배치·회귀 패턴 |
| D-17 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` | R-1 SSOT 양식 + RED-first·§6 행 흡수 선례 |
| D-18 | 설계 | PRINCIPLES.md | `opal/core/PRINCIPLES.md:14-15,35-40` | 헌법 §4·enforce-don't-advise 근거 |
| D-21 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py:469-511,717-731` | R-5 신규 행 무코드변경 흡수 검증 |
| D-22 | 소스 | opd pipeline.json | `opal/skills/opal-pilot-dev/references/pipeline.json` | R-5 게이트 행 추가 위치 |
| D-23 | 설계 | op-task SKILL | `opal/skills/op-task/SKILL.md` | R-6 AC 가이드 보강 위치 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2·§3.1. 유형: 설계/소스/외부. (D 번호는 ANALYSIS §0 표 재사용 + 신규 D-21~D-23 추가)

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 1 | 커버리지 도구 거짓 초록불(미커버인데 ok) | F-002 | P0 | H-1 L1 테스트(미커버 케이스 exit16 단언) + 판단축 evaluator 병행(①⑤⑥) |
| 2 | 신규 exit code 충돌·기존 서브명령 회귀 | F-002, F-007 | P0 | exit 16부터 배정, 실사용 최대치 재확인 + 회귀 보호 테스트(H-2) |
| 3 | pipeline.json 신규 행이 state-tool 거부/차단 실패 | F-005 | P1 | H-3 L2 실 CLI(spec-validate·guard) 검증, 거부 시 Option A 폴백 |
| 4 | 종료조건 오류(무한 루프/조기 탈출) | F-004 | P0 | H-4 종료조건 3종 명문화 + 수치 harness §1 참조(MAX=3) |
| 5 | PM 자체 우회(self-confirming 재발) | F-004, F-005 | P0 | H-5 tool-gated(2증거 필수) + 게이트 행 구조적 차단 + Producer≠Evaluator |
| 6 | evaluator phase 확장이 oppl 회귀 | F-003 | P1 | H-6 additive 확장, 기존 3 phase 무변경 검증 |
| 7 | 자기적용 순환 의존 | F-008 | P0 | R-T7 — R-1~R-5+R-7 완료 후 등가 자기적용 실행(Step 9 의존 배치) |
| 8 | 타 세션 072 파일 충돌 | 전체 | 낮음(해소) | 072는 f6ec48b 병합 완료·파일 교집합 없음(→ ANALYSIS R-T1). state-tool 무변경으로 이중 안전 |
