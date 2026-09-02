---
module: scenario-gate
role: TEST-SCENARIO 목표-커버리지 루브릭 게이트 루프 규칙 SSOT
load: op-scenario-gate 호출 시 / TEST-SCENARIO 작성 시
상속: opal/core/PRINCIPLES.md §4, §Core Stance(enforce-don't-advise)
---

# scenario-gate — TEST-SCENARIO 목표-커버리지 루브릭 게이트 루프

## 1. 목적

TEST-SCENARIO 단계는 두 가지 역할(① 리스크 가설 기반 시나리오 설계 ② TDD red-green 연결, `test-scenario-guide.md:11-14`)에 더해 **③ 목표 달성(채택 관점) 검증**을 세 번째 역할로 삼는다. 본 문서가 이 세 번째 역할의 판정 규칙 SSOT다.

> **070 사건 근거**: 070(`tasks/070-260720-opd-태스크스텝-키주소-1차`)은 TEST-SCENARIO.md를 작성하고 시나리오를 통과시켰으나, 핵심 목표(`--row`→key 주소 채택)를 검증하는 시나리오 자체가 도출되지 않았다 — "시나리오가 FAIL했는데 놓친" 것이 아니라 "애초에 그 시나리오가 존재하지 않았다"(→ ANALYSIS.md 073 §4 발견⑤, `AGENTIC-LOG.md` 결함 사례 원본). 근본 원인은 "루브릭 부재"가 아니라 **도출 엔진의 관점 편향** — 리스크 가설(파괴 관점, H-N)만 도출 입력으로 쓰고 목표 달성(채택 관점)이 커버리지 게이트에 없었다. 결정론 매핑 커버리지(§2 ②③④)만으로는 이 결함을 못 잡는다 — 매핑 표는 "존재하는 시나리오끼리의 완전성"만 검사하기 때문이다. 반드시 독립 평가자가 "목표 달성 관점에서 이 시나리오 집합이 충분한가"를 별도로 판단(§2 ①⑤⑥)해야 하는 이유가 여기에 있다.

## 2. 루브릭 6축 + 판정 주체 분리 [MUST]

| 축 | 정의 | 판정 주체 | 척도 |
|----|------|----------|------|
| ① 목표 달성 | 사용자/운영 계층에서 태스크 목표를 검증하는 시나리오 존재 | opal-evaluator-agent(판단) | 0~2 |
| ② 요구 커버 | TASK R·AC ↔ 시나리오 매핑 완전 | test-tool(결정론) | 누락 수 |
| ③ 기능 커버 | PLAN F ↔ 시나리오 매핑 완전 | test-tool(결정론) | 누락 수 |
| ④ 리스크 커버 | PLAN H ↔ 시나리오 매핑 완전 | test-tool(결정론) | 누락 수 |
| ⑤ 채택/잔존 | 교체형 목표=구형 잔존0·신형 채택 검증 시나리오 존재 | opal-evaluator-agent(판단) | 0~2 |
| ⑥ 경계/부정 | 경계값·부정 경로 시나리오 존재 | opal-evaluator-agent(판단) | 0~2 |

> [MUST] ②③④는 test-tool `scenario-coverage-check` 결정론, ①⑤⑥은 opal-evaluator-agent `scenario-rubric` phase 판단이다. 이 경계는 본 문서가 SSOT다 — 도구·평가자 어느 쪽도 상대방 축을 대신 판정하지 않는다. (→ TASK.md §확정된 설계 방향 2)

## 3. 정규화 계약 (pilot-중립) [MUST]

게이트 입출력은 5 pilot(opd/opds/opsdd/oppl/oppd) 어디에서 호출되든 동일한 형태를 따른다. pilot별 문서 형식(TEST-SCENARIO.md, PLAN.md 등)에서 이 계약으로의 변환 책임은 **호출 스킬**(op-scenario-gate)이 지며, test-tool·evaluator는 pilot-중립 페이로드만 소비한다.

**입력 (정규화 JSON 페이로드)**:
```
{
  "goal": "<태스크 목표 문장>",
  "requirements": ["R-1", ...],
  "features": ["F-001", ...],
  "hypotheses": ["H-1", ...],
  "scenarios": [
    {
      "id": "S-1",
      "covers_requirements": ["R-1"],
      "covers_features": ["F-001"],
      "covers_hypotheses": ["H-1"],
      "is_goal_scenario": true,
      "is_adoption_scenario": false,
      "is_boundary_scenario": false
    }
  ]
}
```

**출력 — 결정론 파트** (test-tool `scenario-coverage-check`):
```
{ "missing": { "requirements": [], "features": [], "hypotheses": [] } }
```
`missing`의 세 배열 중 하나라도 비어있지 않으면 FAIL(§2 ②③④ 미달).

**출력 — 판단 파트** (opal-evaluator-agent `scenario-rubric`):
```
{ "scores": { "goal": 0, "adoption": 0, "boundary": 0 }, "gaps": [] }
```

**opd 1차 접합**: op-scenario-gate 스킬이 TEST-SCENARIO.md §1(가설 표)·§4(매핑 표) + TASK.md R/AC + PLAN.md F/H를 읽어 위 입력 페이로드로 변환한다(→ ANALYSIS.md 073 §4 발견①).

## 4. 루프 프로세스

```
Producer(작성) → scenario-coverage-check(결정론 게이트) → opal-evaluator-agent(scenario-rubric, 판단) → 종료조건 판정 → 재작성
```

1. **Producer**: PM + 사용자 페어가 TEST-SCENARIO.md(또는 pilot별 등가 문서)를 작성/재작성한다.
2. **coverage-check (결정론)**: test-tool `scenario-coverage-check`가 §3 정규화 입력을 받아 §2 ②③④ 매핑 누락을 판정한다.
3. **evaluator (판단)**: opal-evaluator-agent가 `scenario-rubric` phase로 §2 ①⑤⑥ 판단축을 채점하고 gaps를 반환한다.
4. **종료조건 판정**: §5 3종 중 하나로 귀결된다.
5. **재작성**: 미수렴이면 Producer가 gaps를 반영해 재작성하고 1로 되돌아간다.

> [MUST] Producer≠Evaluator — 매 반복마다 작성자(PM+사용자)와 채점자(opal-evaluator-agent)가 분리 유지된다. self-confirming(PM 단독으로 게이트 통과 선언) 방지가 목적이다(→ TASK.md §확정된 설계 방향 3).

> **[MUST] 호출 시점 — PLAN 확정 + 보강 완료 후 1회**: 목표-커버 게이트는 ① PLAN.md 확정(F-NNN·H-N 확정) **AND** ② 도출 입력 2계열 보강 완료(→ `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` §작성 프로세스 Step 1 "보강 완료 판정" 3조건) 두 조건을 모두 충족한 뒤 **1회** 호출한다. 목표계열 선작성 시점(PLAN 워커 실행 중)에는 호출하지 않는다. (여기서 "1회"는 최초 진입 1회를 뜻하며, `verdict: rewrite` 수신 후의 §4-5 재작성 루프 재호출은 이 규율의 예외가 아니라 동일 게이트 1건의 반복이다.)

> **금지 근거**: 선작성 시점에는 §3 정규화 입력의 `features`·`hypotheses`가 미확정(빈 배열 또는 부분)이다. 이 상태로 호출하면 §2 ③기능커버·④리스크커버를 결정론 판정할 수 없고, §3 "`missing`의 세 배열 중 하나라도 비어있지 않으면 FAIL(§2 ②③④ 미달)"에 따라 확정 FAIL이 되어 §5-2 반복 상한을 무의미하게 소모한다. 트랙 규칙 SSOT는 `opal/core/references/harness/red-first.md` §1.6이다.

> **도구 층 정합**: pilot의 게이트 행(opd `test_scenario.scenario_gate` / opds `plan.scenario_gate`)은 state-tool stage-transition guard가 앞 행 전부 완료를 요구하므로(`opal/tools/state-tool/state_tool.py:634`, advance 경로는 `force=False` 하드코딩 `:1423`), PLAN.md 작성 행 미완 상태의 조기 `advance`는 `stage_transition_violation`으로 거부된다. 본 규율은 그 도구 집행과 정합하는 산문 규율이며, 도구 코드를 변경하지 않는다.

## 5. 종료조건 3종 [MUST]

1. **수렴(PASS)**: 커버리지 누락 = 0 (hard gate, §2 ②③④) **AND** 판단축(①⑤⑥) 각 ≥ 1점(0점 축 없음) **AND** 평균 ≥ 1.5점(2점 척도 0~2).
2. **반복 상한**: MAX 초과 → 사용자 에스컬레이션. **상한 수치는 본 문서가 복제하지 않는다** — `opal/core/references/opal-harness.md` §1 "시나리오 목표-커버 게이트 (루브릭 미달)" 행이 유일한 SSOT이며, 본 문서·op-scenario-gate는 그 행을 참조만 한다 (`loop-control.md:41,143` "본 표를 참조·복제하지 않음" 원칙 준용).
3. **무진전**: 연속 2회 gaps·점수 개선 없음 → 사용자 에스컬레이션 (신호 정의는 `opal/skills/opal-pilot-project-loop/references/loop-control.md` §4 준용).

## 6. tool-gated 집행 [MUST]

게이트 PASS는 다음 두 증거가 **모두** 존재할 때만 성립한다:
- test-tool `scenario-coverage-check` exit 0 (누락 = 0)
- opal-evaluator-agent `scenario-rubric` verdict pass (§5-1 판단축 임계 충족)

PM은 위 두 도구 출력 없이 게이트 통과를 산문으로 선언할 수 없다 (`opal/core/PRINCIPLES.md:15` "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose.").

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-23 | 최초 작성 — 루브릭 6축·판정주체분리·정규화계약·루프 프로세스·종료조건 3종·tool-gated 집행 SSOT 신설 (073) |
| v1.1 | 2026-08-19 20:59 | §4에 `[MUST]` 호출 시점 규율 블록 신설 — PLAN 확정+보강 완료 후 1회 호출 / 선작성 시점 호출 금지 근거(F·H 미확정 → ③④ 결정론 판정 불가) / state-tool stage-transition guard 정합 (095) |
| v1.2 | 2026-09-02 17:22 | 에이전트명·소유자 호칭 리터럴 제거 — 규범 산문은 역할어(`PM`/`사용자`/`소유자`)로, 산출물·보고 문면은 `{owner_name}` 플레이스홀더로 전환해 런타임에 소유자 호칭으로 대체된다. 프레임워크 재사용성 확보 (L2 직접 수정) |
