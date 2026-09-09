---
name: op-scenario-gate
description: |
  TEST-SCENARIO 또는 pilot별 등가 산출물의 목표·요구·위험 커버리지를 판정한다.
  필수 입력은 task_folder, producer_artifact, pilot, iteration이며 pass, rewrite, escalate 중 하나를 반환한다.
---

# op-scenario-gate

## 입력과 책임

- `task_folder`: 태스크 폴더
- `producer_artifact`: 검증할 시나리오 산출물
- `pilot`: `opd`, `opds`, `opsdd`
- `iteration`: 최초 1부터 시작하는 반복 회차

호출자가 루프와 pipeline 상태를 관리한다. 이 스킬은 gate 행을 mark하지 않는다.
Producer는 PM이고 evaluator는 `opal-evaluator-agent`다. 두 역할을 같은 주체가 수행하지 않는다.

먼저 `opal/core/references/harness/scenario-gate.md`를 읽는다. 판정 축, 종료 조건,
통과 증거는 그 문서가 소유한다.

## 1. 정규화

모든 읽기·쓰기는 `task_folder` 안에서 수행한다. `producer_artifact`도 그 하위 경로여야 한다.

- `opd` 또는 `opds`의 TASK가 `template: sdlc-v2`이면 다음 builder를 한 번 실행한다.

```bash
~/.opal/tools/test-tool/run.sh scenario-coverage-build --task-folder <task_folder> --template sdlc-v2
```

- 그 외에는 `references/legacy-adapters.md`에서 현재 pilot 절만 읽어
  `<task_folder>/.scenario-coverage-input.json`을 만든다.
- 지원하지 않는 pilot, 경로 이탈, builder exit 17은 입력 오류로 중단한다.

## 2. 결정론 검사

```bash
~/.opal/tools/test-tool/run.sh scenario-coverage-check --coverage-input <task_folder>/.scenario-coverage-input.json
```

- exit 0: evaluator 단계로 진행
- exit 16: `detail.missing`을 gaps로 변환하고 종료 조건을 판정
- exit 17: `verdict: escalate`, `reason: input_error`로 즉시 반환

## 3. 판단 검사

결정론 검사가 통과한 경우에만 `opal-evaluator-agent`를 다음 입력으로 디스패치한다.

```yaml
phase: scenario-rubric
task_folder: <task_folder>
target_artifacts:
  - <producer_artifact>
iteration: <iteration>
scenario_source: <producer_artifact>
```

evaluator는 `scores`, `gaps`, `verdict`만 반환한다. 반복별 Markdown 보고서는 만들지 않는다.

## 4. 종료와 반환

`scenario-gate.md`의 우선순위대로 pass, 반복 상한, 무진전, rewrite를 판정한다.
매 회차의 `{iteration, missing, scores, gaps, verdict}`는
`<task_folder>/.scenario-gate-history.json`에 추가한다.

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

`pass`는 coverage-check exit 0과 evaluator pass가 모두 있을 때만 가능하다.
`rewrite`면 PM이 missing/gaps만 보완해 다음 회차로 다시 호출한다.
`escalate`면 호출자가 루프를 중단하고 사용자에게 보고한다.

## 변경이력

| 버전 | 날짜 | 변경내용 |
|---|---|---|
| v1.0 | 2026-07-23 | 결정론 coverage와 독립 evaluator를 연결한 목표-커버 게이트 신설 (073/F-004) |
| v1.1 | 2026-07-23 15:28 KST | opds·opsdd legacy 변환기 추가 (075/F-001) |
| v1.2 | 2026-09-02 17:22 KST | 소유자 호칭을 런타임 플레이스홀더로 전환 (L2 직접 수정) |
| v1.3 | 2026-09-09 14:18 KST | sdlc-v2 scenario-coverage-build 경로와 legacy 분기 추가 (task 111/W-5) |
| v1.4 | 2026-09-09 14:58 KST | 중복 S-ID와 test substitute 증거 경계 반영 (task 111/W-5 보완) |
| v1.5 | 2026-09-09 15:07 KST | sdlc-v2 PLAN Risks H를 optional로 변경 (task 111/W-5 보완) |
| v1.6 | 2026-09-09 15:33 KST | 신규 실행 경로만 SKILL에 유지하고 pilot별 legacy 변환표를 조건부 adapter로 분리. 중복 결과 스키마와 불필요한 test-tool resolve 호출 제거 (task 111/W-13) |
| v1.7 | 2026-09-09 15:33 KST | 반복별 SCENARIO-GATE-N.md 생성을 제거하고 판정 이력을 `.scenario-gate-history.json` 한 곳에 기록 (task 111/W-13) |
