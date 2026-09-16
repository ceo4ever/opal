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

## 5. OPPB 확장 — acceptance cluster normalizer

`pilot: oppb`일 때만 이 절을 따른다. `opd`·`opds`·`opsdd` 경로는 이 절을 읽지 않고
§1~§4 그대로 동작한다. `oppb`는 이 절이 소유하는 additive 확장값이다.

입력이 둘 늘어난다.

- `run_root`: `<allocator_root>/.opal-runs/<run_id>` 절대경로
- `scope`: 검증 대상 미니 태스크 id (`workgraph.json`의 `mini_tasks[].id`)

경로 규율은 §1과 같다 — coverage 입력과 gate 이력은 `task_folder` 안에 쓰고, run root
아래 파일은 읽기만 한다. `workgraph.json`·`acceptance.json`에는 쓰지 않는다. 두 문서의
유일한 writer는 `controller.py`다.

### 5.1 acceptance cluster → coverage 입력

builder를 쓰지 않는다. `<run_root>/acceptance.json`을 읽어 §2가 그대로 소비하는
`<task_folder>/.scenario-coverage-input.json`을 만든다.

| coverage 입력 필드 | acceptance cluster 원천 |
|---|---|
| `goal` | `INTENT.md`의 프로젝트 목표 문장 |
| `requirements` | `criteria[].id` 전체 |
| `features` | `criteria[].contributing_tasks[]`의 미니 태스크 id 합집합 |
| `hypotheses` | `PROJECT-DESIGN.md`에 H-ID로 적힌 위험 가설만. 없으면 `[]` |
| `scenarios` | `producer_artifact`의 시나리오 행 |

각 시나리오 행은 `covers_requirements`에 그 행이 검증하는 `criteria[].id`,
`covers_features`에 그 조건의 `contributing_tasks` 중 실제로 검증하는 미니 태스크 id,
`covers_hypotheses`에 H-ID를 둔다. 판단 플래그 세 개는 `references/legacy-adapters.md`의
판단 플래그 절을 그대로 따른다 — 문서 근거가 없으면 `false`이고 추정하지 않는다.

`criteria[].satisfied`·`criteria[].evidence[]`·최상위 `evidence_index`는 읽기 전용
참고값이다. 게이트가 고치지 않는다 — 갱신 writer는 `controller.index_evidence` 하나다.

`acceptance.json` 부재, `contributing_tasks`가 `workgraph.json`의 미니 태스크 집합을
벗어남, `scope`가 `mini_tasks[].id`에 없음은 입력 오류다 — `verdict: escalate`,
`reason: input_error`로 즉시 반환한다.

이후 §2 결정론 검사와 §3 판단 검사는 pilot과 무관하게 동일하게 수행한다.

### 5.2 gate 결과 → Evidence Tool 입력

§4의 반환이 확정된 뒤에만 evidence 문서를 만든다. 문서를 `task_folder` 안에 쓰고
다음을 한 번 실행한다.

```bash
~/.opal/tools/oppb-runtime-tool/run.sh evidence submit --run-root <run_root> --file <evidence_file>
```

| evidence 필드 | 색인 전 검사 형식 | 게이트가 채우는 값 |
|---|---|---|
| `schema_version` | 정수. bool 거부 | `1` |
| `evidence_id` | 공백이 아닌 문자열. 색인 파일명이 된다 | `scenario-gate-<scope>-i<iteration>` |
| `scope` | 공백이 아닌 문자열. `workgraph.json`의 미니 태스크 id | 입력 `scope` |
| `code_head` | `^[0-9a-f]{40}$` | `run.json`의 `allocator_root`에서 읽은 `git rev-parse HEAD` |
| `scope_hash` | `^[0-9a-f]{64}$` | `workgraph.json`의 해당 미니 태스크가 공표한 `scope_hash`를 그대로 복사 |
| `verifier.kind` | 공백이 아닌 문자열 | `scenario-gate` |
| `verifier.attempt_id` | 공백이 아닌 문자열 | 이 게이트를 실행한 검증 attempt id |
| `result` | 문자열. 폐쇄 집합이 아니다 | §4의 `verdict` |
| `commands` | 각 원소가 비어있지 않은 문자열 argv 리스트. 빈 배열 허용 | 이 회차에 실제 실행한 명령 argv |

규율 넷을 지킨다.

- **scope hash를 계산하지 않는다.** 계산은 lease를 소유한 Controller의
  `controller.compute_scope_hash` 하나뿐이다. 게이트는 `workgraph.json`이 공표한 값을
  복사만 한다. 불일치는 색인 전에 `evidence_scope_hash_mismatch`로 거부된다.
- **runner attempt id를 쓰지 않는다.** 해당 미니 태스크의 `runner_attempt_id`와 같은
  `verifier.attempt_id`는 `evidence_not_independent`로 거부된다.
- **evidence_id를 재사용하지 않는다.** 색인은 CREATE 전용 원자 연산이라 같은
  `scope`·`evidence_id` 재제출은 `evidence_already_indexed`로 실패한다. 회차마다 새 id를 쓴다.
- **거부는 색인보다 먼저 끝난다.** schema·code head·scope hash·독립성 중 하나라도
  실패하면 색인 파일이 하나도 생기지 않는다. 실패 코드를 `.scenario-gate-history.json`의
  해당 회차에 기록하고 `verdict: escalate`, `reason: input_error`로 반환한다.

`verdict: pass` 회차의 evidence 색인이 성공한 뒤에만 호출자가
`task accept --run-root <run_root> --task-id <scope>`로 전이를 시도할 수 있다.
게이트는 `task accept`를 직접 호출하지 않는다.

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
| v1.8 | 2026-09-15 | OPPB acceptance cluster·Evidence Tool 입력 normalizer를 §5 additive 분기로 추가 (task 132/W-25) |
