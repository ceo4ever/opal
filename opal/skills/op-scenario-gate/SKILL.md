---
name: op-scenario-gate
description: |
  TEST-SCENARIO 또는 pilot별 등가 산출물의 목표·요구·위험 커버리지를 판정한다.
  필수 입력은 task_folder, producer_artifact, pilot, iteration이며 pass, rewrite, escalate 중 하나를 반환한다.
  선택 입력 gate: design을 주면 opd/opds PM 경로 전용 설계 게이트로 동작한다(§6).
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
- 지원하지 않는 pilot과 경로 이탈은 입력 오류로 중단한다. builder exit 17은 evaluator를 부르지 않고 다음을 호출한 뒤 `verdict: escalate`, `reason: input_error`로 반환한다.

```bash
~/.opal/tools/test-tool/run.sh scenario-gate-record --task-folder <task_folder> --iteration <iteration> --input-error <builder detail>
```

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
refinement: <직전 scenario-gate-record 응답의 next_refinement. 없으면 false>
```

evaluator는 `scores`, `gaps`, `verdict`, `advisories[]`만 반환한다. 반복별 Markdown 보고서는 만들지 않는다.

## 4. 종료와 반환

매 회차(evaluator 디스패치 여부와 무관하게) 1회 다음을 호출해 이력을 기록한다. 이 스킬은
`.scenario-gate-history.json`을 직접 append하지 않는다.

```bash
~/.opal/tools/test-tool/run.sh scenario-gate-record --task-folder <task_folder> --iteration <iteration> [--evaluator-result <evaluator 결과 JSON 경로>] [--advisory-responses <run/scenario-gate-i<iteration>-responses.json>] --producer-artifact <producer_artifact>
```

advisory가 1건 이상이고 refinement 회차가 아니면 응답을 요구한다. PM은 응답을
`<task_folder>/run/scenario-gate-i<iteration>-responses.json`에 `[{id, response: apply|retain, reason}]`로
써서 `--advisory-responses`로 넘긴다.

판정은 `scenario-gate-record`가 반환한 값을 그대로 쓴다.

```json
{
  "verdict": "pass | rewrite | escalate",
  "reason": "converged | recoverable | retry_limit | no_progress | input_error | advisory_apply | advisory_refinement_failed",
  "missing": {"requirements": [], "features": [], "hypotheses": []},
  "scores": {"goal": 0, "adoption": 0, "boundary": 0},
  "gaps": [],
  "iteration": 1,
  "next_refinement": false
}
```

`pass`는 coverage-check exit 0과 evaluator pass가 모두 있을 때만 가능하다.
`rewrite`(`reason: advisory_apply`)면 응답에서 `apply`한 advisory를 반영해 다음 회차를
`refinement` 입력으로 재호출한다. 그 외 `rewrite`면 PM이 missing/gaps만 보완해 다음 회차로
다시 호출한다. `escalate`면 호출자가 루프를 중단하고 사용자에게 보고한다.

## 5. OPPB 확장 — acceptance cluster normalizer

`pilot: oppb`일 때만 이 절을 따른다. `opd`·`opds`·`opsdd` 경로는 이 절을 읽지 않고
§1~§4 그대로 동작한다. `oppb`는 이 절이 소유하는 additive 확장값이다.

입력이 둘 늘어난다.

- `run_root`: `<oppb_task_path>/.oppb-run/<run_id>` 절대경로
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
  실패하면 색인 파일이 하나도 생기지 않는다. 이력 편집은 스킬이 직접 하지 않고 다음을 호출해
  기록하며, 도구가 해당 회차를 `verdict: escalate`, `reason: input_error`로 바꿔 반환한다.

```bash
~/.opal/tools/test-tool/run.sh scenario-gate-record --task-folder <task_folder> --iteration <iteration> --evidence-error <실패 코드>
```

`verdict: pass` 회차의 evidence 색인이 성공한 뒤에만 호출자가
`task accept --run-root <run_root> --task-id <scope>`로 전이를 시도할 수 있다.
게이트는 `task accept`를 직접 호출하지 않는다.

## 6. 설계 게이트 (`gate: design`)

입력 `gate: design`은 pilot이 `opd`/`opds`이고 태스크 state가 PM 경로(state.json 행 key에 `plan.design_gate`가 있음)일 때만 유효하다. 이 절은 §1~§4의 `.scenario-gate-history.json`을 쓰지 않는다 — 이력은 `state.json`의 `design_gate.history`가 소유한다. 원문 SSOT는 `opal/core/references/harness/design-gate.md`다.

### 6.1 절차

① 시작

```bash
~/.opal/tools/state-tool/run.sh design-gate start <task_folder> --iteration <N>
```

실패 코드별 처리:

- `design_gate_deterministic_fail`: 반환된 missing으로 PM이 PLAN/TEST-SCENARIO를 보완한 뒤 N+1로 재호출한다.
- `design_gate_retry_limit`, `task_reconfirm_required`: 사용자에게 에스컬레이션한다.
- 그 외 입력 오류: 중단한다.

start 응답의 `refinement`(bool)를 그대로 보관한다 — ②의 evaluator 입력으로 넘긴다.

② `worker.dispatch`로 `opal-evaluator-agent`를 로드·검증한 뒤 다음 입력으로 1회 디스패치한다.

```yaml
phase: design-rubric
task_folder: <task_folder>
task_md: <task_folder>/TASK.md
plan_md: <task_folder>/PLAN.md
scenario_source: <producer_artifact 또는 TEST-SCENARIO.md>
iteration: <N>
input_bundle_hash: <①start 응답의 bundle_hash>
refinement: <①start 응답의 refinement>
previous_gaps: <조회 규칙상 존재할 때만 포함 — 아래 참조>
```

`previous_gaps` 조회 규칙: `state.json`의 `design_gate.history`를 최신부터 역순 순회해 `verdict`가
`deterministic_fail`·`input_error`·`superseded`가 아닌 **가장 최근** 회차를 찾고, 그 회차의
`run/design-gate-i{k}.json`에서 design+scenario gaps를 합쳐 가져온다. 그 회차의 파일이 없어도 더
이전 회차를 계속 본다. **그 회차의 gaps 배열이 비어 있으면 순회를 멈추고 생략한다** — 더 이전
회차로 거슬러 올라가지 않는다. 끝까지 없으면 생략한다.

gaps 항목 id는 "문자열에서 첫 번째 `: ` 앞부분 전체. `: `가 없으면 전체 문자열이 id다"로 정의한다
(신규·레거시 포맷 모두에 적용되는 단일 규칙 — `opal-evaluator-agent/AGENT.md`의 정의와 바이트
동일, 두 곳을 따로 유지하지 않고 그대로 복사해 둔다).

`previous_gaps`를 보냈다면, ③의 stale 확인에 앞서 응답 `resolved_gaps`의 완전성을 검증한다:
`resolved_gaps[].id` 집합이 보낸 `previous_gaps` 각 항목의 id(위 id 정의 적용) 집합과 정확히
같아야 한다. 다르면(누락 또는 초과) `--verdict input_error`로 기록한다.

③ evaluator 반환 JSON을 `<task_folder>/run/design-gate-i<N>.json`에 저장하기 전에, 그 JSON 최상위 `input_bundle_hash`·`iteration`이 ②에서 전달한 값과 같은지 확인한다. 다르거나 없으면(evaluator가 값을 누락·오기했다는 뜻이므로) `--verdict input_error`로 기록한다(`state-tool`이 이 stale 결과를 `design_gate_result_stale`로 다시 거부하지 않도록 사전에 걸러낸다). 그 외 인자 매핑: evaluator `verdict: pass` → `--verdict pass`, `verdict: fail` → `--verdict rewrite --rewrite-target <evaluator rewrite_target>`, evaluator `status: blocked` 또는 결과 JSON이 계약 형식이 아니면 `--verdict input_error`로 기록한다.

evaluator 결과의 `advisories[]`가 1건 이상이고 refinement 회차가 아니면 pass 기록 전에 응답을
요구한다. PM은 `<task_folder>/run/design-gate-i<N>-responses.json`에 `[{id, response: apply|retain, reason}]`를
써서 `--advisory-responses`로 넘긴다.

```bash
~/.opal/tools/state-tool/run.sh design-gate record <task_folder> --iteration <N> --verdict <pass|rewrite|input_error> --evaluator-result <run/design-gate-i<N>.json> [--rewrite-target <plan|scenario|both>] [--advisory-responses <run/design-gate-i<N>-responses.json>]
```

`--verdict pass`이고 응답에 `apply`가 1건 이상이면 도구가 history를 `verdict: rewrite`·
`reason: advisory_apply`로 자동 변환해 기록한다(스킬이 verdict를 직접 바꾸지 않는다). 이때
`--rewrite-target`은 필수다.

④ 반환

```json
{"verdict": "pass | rewrite | escalate", "reason": "... | advisory_apply | advisory_refinement_failed", "rewrite_target": "plan|scenario|both|null", "iteration": 1, "refinement": false}
```

`rewrite`(`reason` 그 외 값)면 PM이 `rewrite_target` 문서만 보완해 N+1로 다시 호출한다.
`rewrite`(`reason: advisory_apply`)면 PM이 apply한 advisory 전부를 `rewrite_target` 문서에
한 번에 반영한 뒤(제안서 §6.3 — 한 묶음 반영, 한 번 재판정) 다음 `start`를 호출한다. 그
`start`가 `refinement: true` 회차다. 대상 문서 hash가 바뀌지 않았으면 기존
`rewrite_target_unchanged`로 거부된다. refinement 회차의 결과가 `rewrite`(`reason:
advisory_refinement_failed`)이면 `record` 응답이 `status=retry_limit`이므로 `escalate`로
반환한다. `record` 응답이 `status=retry_limit`이면 그 외 경우도 `escalate`로 반환한다.

이 경로에서는 §1~§5의 절차·이력·evidence 제출을 수행하지 않는다.

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
