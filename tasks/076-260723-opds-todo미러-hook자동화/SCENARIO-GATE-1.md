# SCENARIO-GATE-1: 목표-커버리지 루브릭 게이트 판정

> phase: scenario-rubric | iteration: 1 | pilot: opds (dogfooding)
> 대상: `TEST-SCENARIO.md` | 기준 SSOT: `opal/core/references/harness/scenario-gate.md` §2·§5-1
> 판정 주체: opal-evaluator-agent (Producer≠Evaluator) | 기록: 알투(PM) — 평가자는 verdict-only(Write 미부여)

## tool-gated 2증거

| 증거 | 결과 |
|------|------|
| ② ③ ④ 결정론 커버리지 (test-tool scenario-coverage-check) | **exit 0** — all_covered:true (R6/F4/H11/시나리오9 전부 커버) |
| ① ⑤ ⑥ 판단 루브릭 (opal-evaluator-agent scenario-rubric) | **verdict: pass** |

## 판단축별 채점 (2점 척도)

| 축 | 점수 | 근거 |
|----|------|------|
| ① 목표 달성 | 2 | S-9(L3, [SUPERVISOR])가 태스크 목표(시작 시 todo 생성→단계마다 갱신→CLOSE까지 유지)를 사용자 계층에서 직접 검증. 핵심 가설 H-4(hook→PM 도구 유발) 실세션 판정 |
| ⑤ 채택/잔존 | 2 | 교체형 목표 양쪽 검증 — 구형 잔존0(S-8 prose-only grep) + 신형 채택(S-9 실세션 hook 트리거 동작). 070 채택 시나리오 부재 재발 없음 |
| ⑥ 경계/부정 | 2 | 경계값(S-1 na중립·파생, S-2 영속 경계) + 부정 경로(S-5 fail-safe 3종, S-6 clobber 멱등, S-4 경고 혼입 추출) |

## 종합

- scores: `{goal: 2, adoption: 2, boundary: 2}` | average: **2.0** | gaps: **0건**
- 종료조건(§5-1): 세 축 각 ≥1 ✓ AND 평균 2.0 ≥ 1.5 ✓ → **수렴 PASS**
- verdict: **pass** → 게이트 행(plan.scenario_gate) mark 근거
