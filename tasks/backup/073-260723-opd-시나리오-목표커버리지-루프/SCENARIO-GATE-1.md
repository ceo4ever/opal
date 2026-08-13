# SCENARIO-GATE-1: 자기적용 음성통제 (iteration 1 — FAIL 증거)

> 생성: 2026-07-23 | 게이트: op-scenario-gate | pilot: opd | iteration: 1
> 대상: 073 자신의 TEST-SCENARIO.md (R-8 자기적용 dogfooding)
> 성격: **음성통제(negative control)** — 목표 검증 시나리오를 의도적으로 누락시켜 게이트가 FAIL을 내는지 실증

## 조작 (의도적 누락)

073의 목표("게이트가 목표 누락을 실제로 잡는다")를 검증하는 자기적용 시나리오 **S-7(음성통제)·S-8(정상수렴)을 페이로드에서 의도적으로 제거**하였다. 이 두 시나리오는 R-8·F-008·H-7을 커버한다.

입력 페이로드: `.scenario-coverage-input-NEG.json` (S-7/S-8 제외, 나머지 S-1~S-6 + PMGATE-R1/R6 유지)

## 결정론 게이트 결과 (test-tool scenario-coverage-check)

```
$ test-tool scenario-coverage-check --coverage-input .scenario-coverage-input-NEG.json
{"ok": false, "command": "scenario-coverage-check", "error": "coverage_unmet",
 "detail": {"missing": {"requirements": ["R-8"], "features": ["F-008"], "hypotheses": ["H-7"]}}}
exit=16
```

## 판정

- **coverage-check**: `exit 16` (coverage_unmet) — 미커버 `{requirements: [R-8], features: [F-008], hypotheses: [H-7]}`.
- **op-scenario-gate 종료조건**: 결정론 하드 게이트 미충족(누락≠0) → 판단 게이트(evaluator) 진입 이전에 **verdict: rewrite (FAIL)** 확정. Producer에게 "누락된 목표 검증 시나리오(R-8/H-7 커버)를 작성하라"는 gaps 반환.

## 실증 의미

- 태스크의 **핵심 목표를 검증하는 시나리오가 누락되면 게이트가 결정론적으로 FAIL**하고 재작성을 유도한다.
- 이는 070 사건(핵심 목표 `--row`→key 채택 검증 시나리오가 애초에 도출되지 않은 채 완료 처리)을 **이 게이트가 실제로 차단했을 것**임을 실증한다 — "시나리오가 FAIL했는데 놓친" 게 아니라 "그 시나리오가 없었다"는 결함을 목표-커버 게이트가 잡아낸다.
- 음성통제 **PASS**: 누락 → FAIL이 확인됨 (게이트가 무력하지 않음). TS-015 / H-7 충족.
