# ANALYSIS: TEST-SCENARIO 목표-커버리지 루브릭 게이트 루프 (공유 컴포넌트, opd 선적용)

> 작성일: 2026-07-23
> 입력: TASK.md
> 출력: ANALYSIS.md

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | op-dev-test-scenario SKILL(프로젝트 소스) | `opal/skills/op-dev-test-scenario/SKILL.md` | R-5 접합 대상·현행 결함 근거(§4 실증) |
| D-2 | 설계 | test-scenario-guide(프로젝트 소스) | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | R-1 도출 엔진 결함 근거 |
| D-3 | 설계 | opal-evaluator-agent | `opal/agents/opal-evaluator-agent/AGENT.md` | R-3 재사용 대상(루브릭 모드 신설 위치) |
| D-4 | 소스 | test-tool scenario.py | `opal/tools/test-tool/lib/scenario.py` | R-2 확장 대상, 기존 서브명령 계약 패턴 |
| D-5 | 설계 | 070 회고 근거 | `tasks/070-260720-opd-태스크스텝-키주소-1차/AGENTIC-LOG.md` | 결함 사례 원본(캡틴 지적 경위) |
| D-6 | 설계 | opal-pilot-dev SKILL | `opal/skills/opal-pilot-dev/SKILL.md` | R-5 STEP 3.5 접합·행 테이블 위치 |
| D-7 | 설계 | op-task SKILL | `opal/skills/op-task/SKILL.md` | R-6 AC 가이드 보강 위치 |
| D-8 | 설계 | oppl loop-control 가이드 | `opal/skills/opal-pilot-project-loop/references/loop-control.md` | R-4 종료조건 설계 선례(반복상한/무진전/목표체크) |
| D-9 | 설계 | opal-harness.md §1 | `opal/core/references/opal-harness.md` | 루핑 상한 SSOT — 신규 루프도 이 절과 정합해야 함 |
| D-10 | 소스 | backlog-tool coverage-check | `opal/tools/backlog-tool/backlog_tool.py:589-620` | 결정론 커버리지 게이트 기존 패턴(R-2 설계 참고) |
| D-11 | 소스 | opal-pilot-dev-short(opds) SKILL | `opal/skills/opal-pilot-dev-short/SKILL.md` | 5 pilot 매핑(§3) — PLAN 흡수형 |
| D-12 | 설계 | op-dev-plan SKILL | `opal/skills/op-dev-plan/SKILL.md` | opds가 TEST-SCENARIO.md를 흡수 작성하는 실제 지점 |
| D-13 | 설계 | opal-pilot-sdd SKILL + verify-guide | `opal/skills/opal-pilot-sdd/SKILL.md`, `opal/skills/opal-pilot-sdd/references/verify-guide.md` | 5 pilot 매핑 — opsdd REVIEW Phase FR↔TS 커버리지 선례 |
| D-14 | 설계 | opal-pilot-project-dev + opal-task-action-agent | `opal/skills/opal-pilot-project-dev/SKILL.md`, `opal/agents/opal-task-action-agent/AGENT.md` | 5 pilot 매핑 — oppd 액션에이전트 내부형 |
| D-15 | 소스 | test-scenario.schema.json | `opal/tools/test-tool/schema/test-scenario.schema.json` | R-2 스키마 확장 지점(additive 필드 관례) |
| D-16 | 소스 | test-tool scenario 테스트 | `opal/tools/test-tool/tests/test_scenario.py` | R-7 테스트 배치 위치·기존 패턴(23건) |
| D-17 | 설계 | red-first.md | `opal/core/references/harness/red-first.md` | R-1 SSOT 문서 구조 템플릿(front-matter+[MUST] 절 양식) |
| D-18 | 설계 | PRINCIPLES.md §4 | `opal/core/PRINCIPLES.md:14,38` | 이 태스크의 헌법적 근거 |
| D-19 | 소스 | 072 TASK.md | `tasks/072-260723-opd-다음액션-자동파생/TASK.md` | 파일 접점 충돌 점검 |
| D-20 | 소스 | git log | `f6ec48b` (커밋 로그) | 072가 이미 main에 병합 완료됨을 확인 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조.

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/core/references/harness/scenario-gate.md` | (신규) 루브릭 6축+루프+정규화 계약 SSOT | 생성 | - (R-1) |
| `opal/skills/op-dev-test-scenario/SKILL.md` | opd TEST-SCENARIO 작성 스킬 — 현재 §3 검증 시나리오가 리스크 가설(H-N)만 도출 | 수정 | `opal/skills/op-dev-test-scenario/SKILL.md:13,71-75,155-165,176-190` |
| `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 도출 프로세스 5단계 가이드 — Step 1이 PLAN 가설 표만 입력으로 규정 | 수정 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:9-29` |
| `opal/agents/opal-evaluator-agent/AGENT.md` | verdict-only 심판 에이전트 — phase 3종(design-review/spec-review/drift-recheck)만 존재 | 수정 | `opal/agents/opal-evaluator-agent/AGENT.md:27,37-55` |
| `opal/tools/test-tool/lib/scenario.py` | test-scenario.json SSOT 서브명령 7종 — R/F/H↔시나리오 매핑 판정 서브명령 부재 | 수정 | `opal/tools/test-tool/lib/scenario.py:352-455,511-519` |
| `opal/tools/test-tool/schema/test-scenario.schema.json` | scenario 항목 스키마 — 069가 additive 필드로 확장한 선례(required_fidelity/fidelity/surface_ref) | 수정(가능성) | `opal/tools/test-tool/schema/test-scenario.schema.json:36,80-91` |
| `opal/tools/test-tool/test_tool.py` | CLI 라우터 — `**SCENARIO_DISPATCH` 스프레드로 scenario.py 신규 서브명령을 자동 흡수 | 변경 불요(확인됨) | `opal/tools/test-tool/test_tool.py:40,238-246` |
| `opal/tools/test-tool/tests/test_scenario.py` | scenario.py 단위 테스트 23건 — 신규 서브명령 테스트 부재 | 수정 | `opal/tools/test-tool/tests/test_scenario.py:134-548` |
| `opal/skills/op-scenario-gate/SKILL.md` | (신규) 단계 스킬 — 커버리지 도구→평가자→verdict+gaps+재작성 루프 컨트롤 | 생성 | - (R-4) |
| `opal/skills/opal-pilot-dev/SKILL.md` | opd 오케스트레이터 — STEP 3.5가 PM 직접 작성 후 바로 사용자 승인으로 진행, 게이트 호출 없음 | 수정 | `opal/skills/opal-pilot-dev/SKILL.md:84-98,274-311` |
| `opal/skills/op-task/SKILL.md` | AC 작성 가이드 — 교체형 목표의 잔존/채택 기준 의무 패턴 부재 | 수정 | `opal/skills/op-task/SKILL.md:89-105` |

### 1.2 아키텍처 패턴

- **분리형 SSOT + 얇은 CLI 래퍼**: test-tool은 로직을 재구현하지 않고 결정론 판정만 수행하며(`opal/tools/test-tool/test_tool.py:18-19`: "yaml 해석 → 명령 실행(subprocess) → JSON 증거 반환하는 얇은 래퍼"), 루프 자체는 보유하지 않는다(`test_tool.py:20`: "루프 한도 비보유... 재시도 루프는 오케스트레이터 책임"). 이 원칙은 신설할 op-scenario-gate에도 그대로 적용된다 — 결정론 커버리지 판정은 test-tool(신규 서브명령)에, 재작성 루프 컨트롤은 op-scenario-gate 스킬(오케스트레이터/PM 레벨)에 위치시켜야 한다.
- **모듈 격리 원칙**: scenario.py는 "resolver/runner/e2e_adapter와 완전 격리되어 기존 4서브명령 로직에 간섭하지 않는다"(`opal/tools/test-tool/lib/scenario.py:6`)는 자기 선언 규율을 갖고 있다. R-2 신규 서브명령도 같은 파일(scenario.py) 내 추가 함수 + `SCENARIO_DISPATCH` 딕셔너리 등록 방식이 기존 패턴과 정합한다(`scenario.py:352-388,511-519`의 `scenario-fidelity-check`/`scenario-conformance` 추가 사례가 최근 선례, 069).
- **에러코드 네임스페이스 분리**: scenario.py는 자체 `SCENARIO_ERROR_CODES`(exit 8~14)를 test_tool.py의 기존 `ERROR_CODES`(exit 0~7)와 충돌 없이 신규 배정하는 관례를 갖는다(`scenario.py:32-34,67-76`). R-2 신규 서브명령도 exit 15부터 이어서 배정해야 회귀 보호 원칙(`scenario.py:32-34`)에 부합한다.
- **verdict-only·readonly 서브에이전트 패턴**: opal-evaluator-agent는 `tools: [Read, Grep, Glob, Bash]`만 보유(Edit/Write 미부여, `opal/agents/opal-evaluator-agent/AGENT.md:9`)하고 Phase 1(내장 루브릭 로드)→Phase 2(CONTRACT.md 병합)→Phase 3(순회 판정)→Phase 4(결과계약)→Phase 5(보고서)→Phase 6(반환) 6-Phase 구조를 갖는다(`AGENT.md:37-114`). R-3의 "시나리오 루브릭 모드"는 이 구조에 `phase: "scenario-rubric"`(가칭) 값을 추가하고 Phase 1에 루브릭 ①⑤⑥ 축을 삽입하는 확장이지 신규 에이전트가 아니다.
- **additive 스키마 확장 규율**: 069가 test-scenario.schema.json에 `required_fidelity`/`fidelity`/`surface_ref`를 "optional additive 필드(required 배열 미포함) — 기존 파일 무파손"(`opal/tools/test-tool/schema/test-scenario.schema.json:36`) 원칙으로 추가한 선례가 있다. R-2가 스키마 확장을 필요로 한다면 동일 원칙을 따라야 한다.
- **PM 직접 작성 + self-confirming 방지 원칙**: opd STEP 3.5는 "PLAN 워커(opal-plan-agent)와 다른 작성자가 수행"(`opal/skills/op-dev-test-scenario/SKILL.md:14`)한다는 원칙을 이미 갖고 있으나, 이 원칙은 "PLAN 작성자 ≠ TEST-SCENARIO 작성자"에 국한되며 "TEST-SCENARIO 작성자(PM) ≠ TEST-SCENARIO 채점자"는 존재하지 않는다 — 이것이 R-3/R-4가 메우는 공백이다.

### 1.3 의존성 맵

```
opal-pilot-dev/SKILL.md (오케스트레이터)
  └─ STEP 3.5 → op-dev-test-scenario/SKILL.md (PM 직접 수행, 워커 디스패치 없음)
       └─ references/test-scenario-guide.md (Step 1~5 프로세스 Read)
            └─ Step 1: PLAN.md §리스크 가설 표 Read (유일한 도출 입력)
       └─ (신설 예정) → op-scenario-gate/SKILL.md
            ├─ test-tool scenario-*(R-2 신규 서브명령) — 결정론 커버리지 판정
            └─ opal-evaluator-agent(phase: scenario-rubric, R-3) — 루브릭 판단축 채점
                 └─ verdict+gaps 반환 → op-scenario-gate 재작성 루프 컨트롤(R-4, MAX=3/무진전2/수렴)
       └─ (기존) 사용자 승인 게이트 → STEP 4 EXECUTE

test_tool.py (CLI 라우터)
  └─ dispatch = {resolve, check, unit, integration, **SCENARIO_DISPATCH}
       └─ lib/scenario.py: SCENARIO_DISPATCH 딕셔너리(7개 키) — R-2 신규 키 추가만으로 자동 라우팅됨

opal-evaluator-agent/AGENT.md
  └─ phase 파라미터 분기(design-review / spec-review / drift-recheck) — R-3가 4번째 phase 추가
```

- oppl의 test-scenario.json(spec존/result존)은 **oppl 전용 SSOT**이며 opd의 TEST-SCENARIO.md(마크다운 §1~§7 통일 형식)와는 **별개의 데이터 표현**이다 — 서로 import/참조 관계가 없다(각 5 pilot이 상이한 산출물 포맷을 쓴다는 TASK.md 배경 분석과 일치). 이는 §4 핵심 발견 ①에서 상술한다.

### 1.4 테스트 현황

- `opal/tools/test-tool/tests/test_scenario.py` — 23개 테스트, `BaseScenarioTestCase` 공통 fixture 기반, 클래스별로 게이트 성격 분리(`TestScenarioLockRedGate`, `TestScenarioMarkLockGate`, `TestScenarioFidelityCheckUnmet`, `TestScenarioConformance` 등, `test_scenario.py:134-548`). R-2 신규 서브명령은 이 패턴(`TestExistingSuiteRegressionPresence` 클래스가 기존 4서브명령 dispatch 키 불변을 확인하는 회귀 보호 테스트, `test_scenario.py:272-306`)를 그대로 확장해야 한다.
- `opal/tools/test-tool/tests/test_test_tool.py` — 12개 테스트, resolve/check/unit/integration 4서브명령 커버. scenario.py와 격리되어 있어 R-2 변경의 영향을 받지 않는다.
- opal-evaluator-agent는 서브에이전트(마크다운 AGENT.md)이며 자체 단위 테스트 파일이 없다 — verdict 판정 로직이 프롬프트 기반이라 test-tool처럼 pytest 대상이 아니다. R-3 확장의 검증은 R-8 자기적용(이 태스크 자신의 TEST-SCENARIO 루프 실행)으로 대체된다.
- op-scenario-gate(R-4, 신규 스킬)는 마크다운 스킬 문서이므로 별도 유닛 테스트 대상이 아니며, R-2(test-tool 서브명령)만 R-7 유닛 테스트 대상이다.

---

## 2. 외부 조사 결과

해당 없음 — 이 태스크는 순수 프레임워크 내부 개선이며 외부 라이브러리·API 의존이 없다(기술 스택: Python stdlib argparse/json, Markdown).

---

## 3. 영향 범위

### 3.1 직접 영향

- 신규 생성: `opal/core/references/harness/scenario-gate.md`(R-1), `opal/skills/op-scenario-gate/SKILL.md`(R-4)
- 수정: `opal/skills/op-dev-test-scenario/SKILL.md` + `references/test-scenario-guide.md`(R-1 접합·도출 엔진 보강), `opal/tools/test-tool/lib/scenario.py`(+ schema 가능성, R-2), `opal/agents/opal-evaluator-agent/AGENT.md`(R-3), `opal/skills/opal-pilot-dev/SKILL.md` STEP 3.5(R-5), `opal/skills/op-task/SKILL.md` AC 가이드(R-6), `opal/tools/test-tool/tests/test_scenario.py`(R-7)
- 이 태스크(073) 자신의 `TEST-SCENARIO.md`(R-8 자기적용 — 신규 루프를 직접 시연)

### 3.2 간접 영향

- **opd 파이프라인 흐름 전체**: STEP 3.5에 게이트가 삽입되면 opd SKILL.md `## 단계 목록`/`STATE.md` 행 테이블(`opal/skills/opal-pilot-dev/SKILL.md:274-311`, 특히 9~10행)에 신규 행(예: `test_scenario.scenario_gate`) 추가가 필요할 수 있다 — 이는 state-tool의 task-step key 주소 체계(070/072 회전)와 정합해야 한다. **단, 이 태스크는 state-tool 자체(state_tool.py/schema/tests)를 변경하지 않는다** — 072가 이미 그 표면을 확정·병합했다(§5 리스크 참조).
- **다른 4 pilot(opds/opsdd/oppl/oppd)**: 1차 범위 제외(TASK.md §확정된 설계 방향 7)이나, 계약 호환성만 확인 대상. §4 핵심 발견 ①에서 각 pilot의 시나리오 산출물 포맷 차이를 근거로 "정규화 계약 접합점"의 필요성을 뒷받침한다.
- **opal-evaluator-agent의 기존 3 phase 호출자(oppl)**: R-3가 phase 열거값을 확장(4번째 `scenario-rubric` 추가)해도 기존 `design-review`/`spec-review`/`drift-recheck` 호출 경로(`opal/agents/opal-evaluator-agent/AGENT.md:27`)는 무변경 유지되어야 한다(additive 확장 원칙).

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음
- [x] API 인터페이스 변경 — test-tool CLI에 신규 서브명령 추가(additive, 기존 서브명령 무변경), opal-evaluator-agent phase 열거값에 신규 값 추가(additive)
- [ ] 설정/환경변수 변경 — 해당 없음
- [ ] 빌드/배포 파이프라인 변경 — 해당 없음 (커밋·install은 사용자 명시 지시 시만, TASK.md §제약 조건)

---

## 4. 핵심 발견 사항

**① 5 pilot의 시나리오 산출물은 데이터 표현이 서로 달라 "정규화 계약"이 R-4의 핵심 난제다.**
opd는 마크다운 `TEST-SCENARIO.md`(리스크 가설 표 §1 + 4열 매핑 표 §4, `op-dev-test-scenario/SKILL.md:71-75,130-134`)를, opds는 `op-dev-plan` 워커가 PLAN.md와 통합 작성하는 동일 마크다운 포맷(`opal/skills/op-dev-plan/SKILL.md:6,34-35,146,176-180`, `opal-pilot-dev-short/SKILL.md:54`)을, opsdd는 PM이 REVIEW Phase에서 직접 작성하는 `TEST-SCENARIOS.md`(복수형, `opal/skills/opal-pilot-sdd/SKILL.md:44,158-162`)를 쓰며 이미 자체 FR↔TS 커버리지 확인 단계를 보유한다(`opal/skills/opal-pilot-sdd/references/verify-guide.md:23-24,137-172` — "AC 커버리지: 모든 AC에서 최소 1개 시나리오", "FR 커버리지: 모든 FR이 최소 1개 AC → 1개 TS에 연결"). 반면 oppl은 `test-scenario.json`(spec존/result존 분리 JSON, `opal/tools/test-tool/schema/test-scenario.schema.json`)을, oppd는 opal-task-action-agent 내부에서 PLAN→QA→TEST-SCENARIO→EXECUTE 파이프라인의 한 단계로 TEST-SCENARIO.md를 생성한다(`opal/agents/opal-task-action-agent/AGENT.md:45-99`). 즉 **JSON(oppl) vs 마크다운 테이블(나머지 4종)**이라는 근본적 포맷 이질성이 있어, test-tool 신규 서브명령이 곧바로 5 pilot 공통 게이트가 될 수 없다 — TASK.md §확정된 설계 방향 5가 "정규화 계약(입력=목표·R·F·H·시나리오 / 출력=누락·점수·gaps)"을 명시적으로 요구하는 이유가 여기 있다. 1차 opd 선적용 범위에서는 op-scenario-gate 스킬이 TEST-SCENARIO.md §1/§4 표를 읽어 정규화된 입력으로 변환한 뒤 test-tool에 전달(또는 test-tool 신규 서브명령이 `--coverage-input <JSON>` 형태의 pilot-중립 페이로드를 받는 방식)하는 설계가 필요하다.

**② 현행 결함의 정확한 위치는 "도출 엔진"과 "완전성 검사" 두 곳이다.**
`test-scenario-guide.md:11-13`은 목적을 "1. 리스크 가설 기반 시나리오 설계... 2. TDD red-green 연결" 두 가지로만 규정하며, "목표 달성(채택 관점)"은 목적 목록에 없다. Step 1(`:20-29`)은 "PLAN.md §리스크 가설 표를 Read하여 H-N 목록을 파악"만 지시하고 TASK.md 요구사항(R)이나 목표 문장을 입력으로 삼지 않는다. `op-dev-test-scenario/SKILL.md`의 PM Gate 7대 룰(`:155-165`)과 시나리오 작성 체크리스트(`:176-190`)는 "가설↔시나리오 매핑 완전"(:160)·"L1/L2/L3 계층 명시"(:161)만 검사하며 "TASK.md 요구사항 R 전체 커버" 항목이 없다. 대조적으로 opds(op-dev-plan 경로)의 PM Gate에는 이미 "TEST-SCENARIO.md 시나리오가 TASK.md 요구사항 전체를 커버하는가"(`opal-pilot-dev-short/SKILL.md:63`) 체크가 존재한다 — **opd에는 이 항목이 아예 없다**는 것이 070 사건(핵심 목표 미검증인 채 완료 처리)의 직접 원인이다.

**③ 재사용 자산은 이미 "결정론 게이트 + 독립 판단자 + 종료조건" 3중 구조를 실증한 선례가 있다.**
oppl의 Loop 2는 `backlog-tool coverage-check`(결정론, `opal/tools/backlog-tool/backlog_tool.py:589-620` — surfaces.json 대비 미커버 표면 결정론 판정)와 `opal-evaluator-agent`(판단, verdict-only) 조합을 이미 병행 운용하며, `loop-control.md`가 8개 안전 요소 중 5개(반복상한/예산/무진전/목표체크/사람게이트)를 종료조건으로 명문화한다(`opal/skills/opal-pilot-project-loop/references/loop-control.md:11-26`). 특히 §4 무진전 감지의 "동일 실패 반복"·"검증 왕복(fail에 고정된 채 회전 소진)" 신호(`loop-control.md:59-68`)는 TASK.md가 잠근 "무진전=연속 2회 gaps·점수 개선 없음" 파라미터의 직접 설계 선례다. R-4는 이 패턴을 test-tool(결정론)+opal-evaluator-agent(판단)+op-scenario-gate(루프 컨트롤) 조합으로 재사용하되, oppl 스케일(태스크 단위 Loop)보다 훨씬 작은 스케일(시나리오 문서 1건 단위)로 축소 적용하는 것이 R-4의 성격이다.

**④ test-tool의 아키텍처는 신규 서브명령 추가 비용이 낮다.**
`test_tool.py` main()의 dispatch 딕셔너리는 `{"resolve":..., "check":..., "unit":..., "integration":..., **SCENARIO_DISPATCH}` 형태로 `lib/scenario.py`의 `SCENARIO_DISPATCH`를 스프레드 병합한다(`test_tool.py:238-246`). 즉 R-2 신규 서브명령은 `scenario.py`에 핸들러 함수 + `add_scenario_subparsers`에 파서 등록 + `SCENARIO_DISPATCH` 딕셔너리 키 추가만으로 완결되며 **`test_tool.py` 자체는 수정 불필요**하다 — 069가 `scenario-fidelity-check`/`scenario-conformance` 2종을 추가할 때 실증된 패턴과 동일하다.

**⑤ 070 사건의 근본 원인은 "루브릭 부재"가 아니라 "도출 엔진의 관점 편향"이다.**
070은 실제로 TEST-SCENARIO.md를 작성하고 시나리오를 통과시켰으나(§7 판정 완료), 핵심 목표(`--row`→key 채택)를 검증하는 시나리오 자체가 도출되지 않았다 — 즉 "시나리오가 FAIL했는데 놓친" 것이 아니라 "애초에 그 시나리오가 존재하지 않았다." 이는 R-2(결정론 매핑 커버리지)만으로는 못 잡는다(매핑 표는 존재하는 시나리오끼리의 완전성만 검사하므로) — 반드시 R-3(독립 평가자가 "목표 달성 관점에서 이 시나리오 집합이 충분한가"를 별도로 판단)가 병행되어야 하는 이유이며, TASK.md 루브릭 6축 중 ②③④(도구 결정론)와 ①⑤⑥(평가자 판단)를 분리한 설계(TASK.md §확정된 설계 방향 2)가 이 발견과 정합한다.

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-T1 | 072(state-tool STATE.md 다음액션)는 이미 `f6ec48b` 커밋으로 main에 병합 완료되었고, 변경 파일은 `state_tool.py`/`schema/state.schema.json`/`tests/test_state_tool.py`/`README.md`/`state-template.md`/`task-process.md`뿐이다 — 본 태스크의 편집 대상(scenario-gate.md/test-tool scenario.py/evaluator-agent/opd SKILL/op-task SKILL)과 **파일 경로 교집합이 없다.** 파일 충돌 리스크는 실질적으로 해소된 상태다. | 낮음(해소됨) | `f6ec48b` 커밋 stat, `tasks/072-260723-opd-다음액션-자동파생/TASK.md:68-74` |
| R-T2 | opd STEP 3.5에 게이트를 삽입하면 신규 state-tool task-step 키(예: `test_scenario.scenario_gate`)가 필요할 수 있으나, **본 태스크는 state-tool 자체(state_tool.py/schema)를 변경하지 않는다**(TASK.md 범위 제외) — PLAN 단계에서 기존 키 재활용(예: `test_scenario.test_scenario_md` 완료 조건에 게이트 통과 포함) 또는 별도 키 신설 여부를 결정해야 한다. | 중간 | `opal/skills/opal-pilot-dev/SKILL.md:94,274-311` |
| R-T3 | 5 pilot 산출물 포맷 이질성(§4 발견①: JSON vs 마크다운) 때문에 R-2 test-tool 서브명령의 입력 계약을 "oppl test-scenario.json 전용"으로 좁게 설계하면 향후 opds/opsdd/oppd 확산(후속 태스크) 시 재작업이 필요하다 — PLAN 단계에서 pilot-중립 입력(정규화 JSON 페이로드 또는 파일 경로 파라미터화)을 처음부터 고려해야 확산 비용이 낮아진다. | 중간 | TASK.md §확정된 설계 방향 5, §4 발견① |
| R-T4 | Producer≠Evaluator 분리를 opd STEP 3.5에 적용할 때, 현재 STEP 3.5는 "오케스트레이터(PM)가 직접 작성 — 워커 디스패치 없음"(`op-dev-test-scenario/SKILL.md:13`)이므로 Producer=PM이다. Evaluator를 opal-evaluator-agent(서브에이전트 디스패치)로 두면 자동으로 분리되나, PM이 스스로 게이트 결과를 무시하고 진행할 개연성(자체 우회)을 op-scenario-gate 스킬이 tool-gated로 차단해야 한다("enforce, don't just advise" — `opal/core/PRINCIPLES.md:15`). | 중간 | `opal/core/PRINCIPLES.md:14-15,38` |
| R-T5 | 루프 무한 차단 — TASK.md가 잠근 MAX=3/무진전 연속 2회 파라미터는 `opal-harness.md` §1 표(`opal-harness.md:44-58`)의 기존 7개 행("QA 설계/아키텍처: 0회"가 가장 근접) 어디에도 정확히 대응하지 않는 **신규 루프 유형**이다. `loop-control.md`가 "본 문서는 참조만, 복제하지 않음"(`loop-control.md:143`) 원칙을 따르듯, scenario-gate.md도 §1 표에 없는 수치(MAX=3)를 독자적으로 정의하는 근거를 명시해야 하며, 필요하다면 opal-harness.md §1에 신규 행(예: "시나리오 목표-커버 게이트 루브릭 미달")을 추가하는 것이 PLAN 단계의 검토 후보다. | 중간 | `opal/core/references/opal-harness.md:44-58`, `loop-control.md:30-43` |
| R-T6 | opal-evaluator-agent에 4번째 phase(`scenario-rubric`)를 추가할 때, 기존 Phase 5 보고서 경로 분기(`{task_folder}/QA-SPEC*.md` 계열, `AGENT.md:90-95`)에 신규 phase의 보고서 파일명 규칙이 없으면 "위 산출물 경로가 이미 존재하는 프로젝트 리포트 관례와 충돌하면 VERIFICATION.md에 추가 기록"(`AGENT.md:95`) 폴백 조항이 발동하는데, opd 태스크 폴더에는 `VERIFICATION.md` 관례가 없으므로 R-3 설계 시 전용 파일명(예: `SCENARIO-GATE-{N}.md`)을 명시적으로 정의해야 한다. | 낮음 | `opal/agents/opal-evaluator-agent/AGENT.md:90-95` |
| R-T7 | R-8 자기적용 — 073 자신의 STEP 3.5는 "구현 예정 절차(R-1~R-5)"를 놓고 시연할 수 없는 순환 의존이 생긴다. PLAN 단계에서 "073은 EXECUTE로 R-1~R-5 구현 완료 후 STEP 3.5(또는 그 등가 자기적용 절차)를 재수행하여 목표-커버 시나리오 누락 음성통제+정상수렴 둘 다 실증한다"는 순서 조정이 필요하다. | 중간 | TASK.md §확정된 설계 방향 8, R-8 |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어 | Python | 3.14 (`test-tool` `__pycache__` cpython-314 표기 확인) |
| 테스트 프레임워크 | pytest | 9.1.0 (`tests/__pycache__/*-pytest-9.1.0.pyc` 표기 확인) |
| 스키마 | JSON Schema Draft-07 | `test-scenario.schema.json:2` |
| 문서 | Markdown (SSOT·스킬·AGENT.md) | - |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| (해당 없음) | 이 태스크는 OPAL 프레임워크 자체의 내부 개선이며 외부 커뮤니티 스킬 의존이 없다 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| (해당 없음) | 순수 내부 마크다운/Python 변경, 외부 라이브러리 조사 불요 |
