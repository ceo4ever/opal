# op-scenario-gate

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-dev`·`opal-pilot-sdd`가 시나리오 검증 단계에서 디스패치합니다.

TEST-SCENARIO 또는 pilot별 등가 산출물의 목표·요구·위험 커버리지를 판정하는 게이트입니다.

## 역할

Producer(PM이 작성한 시나리오 산출물)와 evaluator(`opal-evaluator-agent`)를 분리한 상태에서, 결정론 검사와 독립 평가 두 증거가 모두 있어야 `pass`로 판정합니다.

- **결정론 검사**: `test-tool scenario-coverage-build`/`scenario-coverage-check`로 커버리지 입력을 만들고 기계적으로 검사
- **판단 검사**: 결정론 검사를 통과한 경우에만 `opal-evaluator-agent`를 `scenario-rubric` phase로 디스패치해 `scores`/`gaps`/`verdict`를 받음

호출자가 루프와 pipeline 상태를 관리하며, 이 스킬 자체는 gate 행을 mark하지 않습니다.

## 입력

- `task_folder`: 태스크 폴더
- `producer_artifact`: 검증할 시나리오 산출물 (task_folder 하위 경로여야 함)
- `pilot`: `opd`, `opds`, `opsdd` (`oppb`는 §5 확장 경로)
- `iteration`: 최초 1부터 시작하는 반복 회차

## 출력

`pass` / `rewrite` / `escalate` 셋 중 하나의 판정과 회차 이력.

```json
{
  "verdict": "pass | rewrite | escalate",
  "reason": "converged | recoverable | retry_limit | no_progress | input_error",
  "missing": {"requirements": [], "features": [], "hypotheses": []},
  "scores": {"goal": 0, "adoption": 0, "boundary": 0},
  "gaps": [],
  "iteration": 1
}
```

이력은 `<task_folder>/.scenario-gate-history.json`에 회차마다 추가됩니다. `pass`는 coverage-check exit 0과 evaluator pass가 모두 있을 때만 가능하며, `rewrite`면 PM이 missing/gaps만 보완해 다음 회차를 다시 호출하고, `escalate`면 호출자가 루프를 중단하고 사용자에게 보고합니다.

## 호출 시점

`opal-pilot-dev`(opd) 계열과 `opal-pilot-sdd`(opds)가 시나리오 산출물 검증이 필요한 시점에 호출합니다. `oppb`는 acceptance cluster를 coverage 입력으로 정규화하는 §5 확장 경로를 추가로 따르며, gate 결과를 Evidence Tool에 제출합니다.

## 관련 문서

- `opal/core/references/harness/scenario-gate.md` (판정 축·종료 조건·통과 증거 SSOT)
- `opal/skills/op-scenario-gate/references/legacy-adapters.md`
