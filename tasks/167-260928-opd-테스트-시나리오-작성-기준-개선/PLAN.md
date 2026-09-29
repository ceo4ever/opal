---
template: sdlc-v2
---
# PLAN: 테스트 시나리오 작성 기준 개선 — 중복·과잉 시나리오 억제와 advisory 응답 게이트

> 입력: [TASK.md](TASK.md) | 작성자: PM(coordinator — PM 경로, ANALYSIS.md 없음)

## Approach

제안서(`docs/proposals/opal-test-scenario-economy-gate.md`, 이하 D-1)의 §10 구현 순서를 그대로 네 묶음으로 나눈다.

1. 공통 작성 기준·유형 변환·evaluator 결과 계약 — 작성 가이드, test-tool 변환·검증, evaluator·test-agent 계약
2. PM 기본 경로 — `state-tool design-gate record`의 advisory 응답과 반영 재판정(refinement)
3. 목표-커버 게이트 경로 — 새 `test-tool scenario-gate-record`·`scenario-gate-verify`와 `state-tool mark` 가드
4. 프로젝트 문서 갱신과 제안서 이관

파일 소유권이 겹치지 않게 test-tool(W-1), 규범·에이전트 문서(W-2), state-tool(W-3), 프로젝트 문서(W-4)로 나눈다. W-3은 W-1이 만든 `scenario-gate-verify`를 호출하므로 뒤 실행 그룹에 둔다. 워크트리에서는 install하지 않고, 설치본 검증은 merge 후 허브에서 수행한다(허브 PM 지시).

### 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | 테스트 시나리오 작성 기준 개선 제안서 | `docs/proposals/opal-test-scenario-economy-gate.md` | 작성 기준·판정·집행 계약의 원천 |
| D-2 | 설계 | 목표-커버 게이트 SSOT | `opal/core/references/harness/scenario-gate.md` | 판정 축·종료 조건·통과 증거 |
| D-3 | 설계 | 설계 게이트 SSOT | `opal/core/references/harness/design-gate.md` | history verdict 5값·반복 상한·reset·오류 코드 |
| D-4 | 소스 | test-tool 시나리오 모듈 | `opal/tools/test-tool/lib/scenario.py` | coverage-build·scenario-init 현행 동작 |
| D-5 | 소스 | E2E 계약 검증 | `opal/tools/test-tool/lib/e2e_contract.py` | type enum 검증 |
| D-6 | 소스 | state-tool | `opal/tools/state-tool/state_tool.py` | design-gate start/record/reset, mark 가드 |
| D-7 | 설계 | 작성 가이드 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | Scenarios 표 열 계약 |
| D-8 | 설계 | 게이트 스킬 | `opal/skills/op-scenario-gate/SKILL.md` | 목표-커버·설계 게이트 절차와 history 기록 |
| D-9 | 설계 | evaluator 에이전트 | `opal/agents/opal-evaluator-agent/AGENT.md` | scenario-rubric·design-rubric 결과 계약 |
| D-10 | 설계 | test-agent | `opal/agents/opal-test-agent/AGENT.md` | test-scenario.json 변환 규칙 |
| D-11 | 소스 | 스킬 모의 테스트 실행기 | `opal/skills/opal-skill-tester/scripts/skill_tester.py` | `.scenario-gate-history.json` 소비자 |
| D-12 | 설계 | TEST 실행 주기 | `opal/core/references/harness/test-cycle.md` | 증거 재사용·최종 Gate |

### 확인 사실

- 유형 선언은 문서에서 JSON까지 전달되지 않는다. coverage builder는 표를 헤더 이름으로 읽지만 `유형`을 해석하지 않는다(→ D-4:901-990). test-agent 변환 규칙에는 `type`이 없다(→ D-10:47-52). 표 열 계약에도 `유형`이 없다(→ D-7 §Scenarios).
- `type` 허용값에 `check`가 없다(→ D-5:432, `opal/tools/test-tool/schema/test-scenario.schema.json:95-97`). `type`이 null이면 통과하고(→ D-5:432), `red_required`가 없으면 true로 읽는다(→ D-4:197).
- 목표-커버 게이트 이력은 스킬이 직접 append한다(→ D-8 §4). 이 이력을 쓰는 도구 명령(`scenario-gate-record`)은 아직 없다(→ D-4:1181-1191의 DISPATCH 9종).
- `state-tool mark`가 게이트 행을 완료로 바꿀 때 이력을 검사하는 가드는 PM 경로의 `plan.design_gate`에만 있다(→ D-6 `apply_pm_design_guards`). `test_scenario.scenario_gate`(`opal/skills/opal-pilot-dev/references/pipeline.json:30`)와 `plan.scenario_gate`(`opal/skills/opal-pilot-dev/references/pipeline-short.json:15`)에는 없다.
- 설계 게이트 record는 비-pass를 fail로 처리하고, 상한 도달 시 `retry_limit`과 `await_user`로 전이한다(→ D-6 `cmd_design_gate_record`). history item 스키마에 추가 속성 금지(`additionalProperties`)는 없다(`opal/tools/state-tool/schema/state.schema.json` design_gate).
- `.scenario-gate-history.json`은 JSON 배열이며, skill-tester는 마지막 원소의 `verdict`만 읽는다(→ D-11:315-323).
- install은 `opal/tools/` 전체를 `~/.opal/tools/`로 복사하므로(`scripts/install-mac.sh:1418`) install 스크립트는 바꾸지 않는다.
- 기준 회귀는 `~/.opal/.venv/bin/python -m pytest -q opal/tools/test-tool/tests/test_scenario.py opal/tools/state-tool/tests/test_design_gate.py` 실행 결과 `79 passed, 49 subtests passed`다(2026-09-28 18:42, 워크트리 소스 기준).

## Findings

### 직접 변경

- `opal/tools/test-tool/lib/scenario.py`: 유형 열 파싱과 엄격 검사, 정확 중복·check+RED 거부, payload의 `type`·`red_required`, `scenario-init`의 check+RED 거부, 새 명령 `scenario-gate-record`·`scenario-gate-verify`
- `opal/tools/test-tool/lib/e2e_contract.py`: `check` 유형 허용과 `check`+`red_required=true` 거부
- `opal/tools/test-tool/schema/test-scenario.schema.json`: type enum에 `check` 추가
- `opal/tools/test-tool/tests/test_scenario.py`: 위 계약의 테스트
- `opal/tools/test-tool/README.md`: 새 명령 두 개와 오류 코드
- `opal/tools/state-tool/state_tool.py`: design-gate record의 advisory 응답·refinement, 목표-커버 게이트 행 mark 가드
- `opal/tools/state-tool/schema/state.schema.json`: design_gate 선택 필드
- `opal/tools/state-tool/tests/test_design_gate.py`: 두 경로의 state-tool 계약 테스트
- `opal/tools/state-tool/tests/test_mode_transition_contract.py`, `opal/tools/state-tool/tests/test_state_tool_mode_contracts.py`: 목표-커버 게이트 행을 mark하는 기존 fixture에 `scenario-gate-record` pass 이력 준비를 추가(assert 불변, EXECUTE 중 허브 PM 대리 승인으로 추가)
- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`, `opal/skills/op-scenario-gate/SKILL.md`, `opal/skills/op-scenario-gate/README.md`, `opal/agents/opal-evaluator-agent/AGENT.md`, `opal/agents/opal-test-agent/AGENT.md`, `opal/core/references/harness/scenario-gate.md`, `opal/core/references/harness/design-gate.md`, `opal/core/references/harness/test-cycle.md`: 규범·절차 갱신

### 회귀 확인

- `opal/skills/opal-skill-tester/scripts/skill_tester.py`: 이력 배열의 마지막 `verdict`를 읽는 방식이 그대로 동작하는지 확인
- `opal/skills/op-scenario-gate/references/legacy-adapters.md`: legacy 변환은 바꾸지 않으며, 기록 명령이 legacy가 만든 coverage 입력을 받는지 확인
- `opal/skills/opal-pilot-dev/SKILL.md`: STEP 3.5의 mark 시점 서술이 새 가드와 모순되지 않는지 확인
- 기존 `test-scenario.json` 소비 경로(`scenario-lock`·`scenario-mark`·`scenario-status`)의 `red_required` 누락 호환

### 문서 갱신

- `docs/PROJECT.md`: `test-tool scenario-*` 행과 TEST-SCENARIO 목표-커버 게이트 절에 advisory·기록 명령 추가
- `docs/proposals/opal-test-scenario-economy-gate.md` → `docs/proposals/archives/opal-test-scenario-economy-gate.md`: 구현 완료 후 이관(D-1 §13)

### 미확인 가정

- H-1
- H-2

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 유형 열 전환 규칙 | `Scenarios` 표 헤더에 `유형`이 있으면 모든 행의 값이 `unit·integration·contract·regression·e2e·check` 중 하나여야 한다. 누락·오값은 `coverage_input_invalid` exit 17로 거부한다. 헤더에 `유형`이 없으면 유형 검사 없이 기존 변환을 유지한다 | AC-2, C-2, D-1 §5.1 |
| payload의 유형 전달 | builder는 각 scenario에 `type`(유형 열이 없으면 `null`)과 `red_required`(`시점`에 `구현 전 RED`가 있으면 true)를 넣는다. test-agent는 `scenario-init` 입력의 `type`에 유형 열 값을 그대로 넣고, 유형 열이 없으면 `type`을 넣지 않는다 | AC-2, D-1 §5 전달 경로 |
| check+RED 모순 | 유형 `check`인 행의 `시점`에 `구현 전 RED`가 있으면 builder가 exit 17로 거부한다. `scenario-init`은 `type=check`이면서 `red_required=true`인 항목을 `scenario_contract_invalid` exit 17로 거부한다. `red_required`가 없는 check는 true로 읽히므로 역시 거부된다. 거부는 새로 쓰는 문서에만 적용되고, 이미 잠긴 JSON의 읽기에는 적용하지 않는다 | AC-3, C-1, D-1 §5 |
| 정확 중복 | 유형 열이 있는 문서에서 `유형·조건·행동·기대 결과·방법·환경·시점` 여섯 셀(공백 정규화 후)이 모두 같은 두 행은 builder가 exit 17(`duplicate scenario content: [S-a, S-b]`)로 거부한다. 기대 결과만 다른 행은 통과한다 | AC-3, D-1 §6.1 |
| advisory 결과 계약 | evaluator의 `scenario-rubric`·`design-rubric` 결과는 pass 점수와 분리된 최상위 `advisories[]`를 가진다. 원소는 `{id: "A-N", kind: subsumed|mergeable|cheaper_layer|misclassified, targets: [S-ID ≥1], basis, recommendation}`다. 입력 `refinement: true`에서는 `advisories: []`만 반환한다. 두 기록 도구는 refinement가 아닌 회차에서 형식 위반을 결과 무효로 거부한다(설계 경로 `design_gate_result_invalid`, 목표-커버 경로 exit 18 `scenario_gate_record_invalid`). refinement 회차에서는 evaluator가 비어 있지 않은 `advisories[]`를 돌려줘도 두 도구 모두 형식 검사 없이 무시하고, 응답을 요구하지 않으며, 이력에는 `advisories: []`로 기록한다 | AC-4, D-1 §6.2 |
| advisory 응답 형식 | PM은 `run/<gate>-i<N>-responses.json`에 `[{id, response: apply|retain, reason}]`를 쓰고 기록 명령에 `--advisory-responses`로 넘긴다. 응답 ID 집합은 advisory ID 집합과 정확히 같아야 하고 중복이 없어야 한다. `retain`은 공백이 아닌 `reason`이 필요하다. 위반하면 기록을 거부하고(설계 경로 `advisory_response_invalid`, 목표-커버 경로 exit 19 `advisory_response_invalid`) 상태를 바꾸지 않는다. 응답 타당성은 판단하지 않는다 | AC-5, D-1 §6.3 |
| 응답 요구 시점 | evaluator가 pass이고 refinement 회차가 아니며 `advisories[]`가 1건 이상일 때만 응답을 요구한다. advisories가 빈 배열이면 `--advisory-responses`를 생략할 수 있고, 주어진 응답도 빈 배열이어야 한다. 비-pass 회차는 문서를 다시 쓰므로 응답이 선택이다. 응답이 있으면 기록한다 | AC-5 "게이트를 완료할 수 없다"는 완료 시점 요구 |
| advisory 반영 전이(설계 경로) | PM이 evaluator pass를 `--verdict pass`와 응답 파일로 기록할 때 응답이 완전하고 `apply`가 1건 이상이면 도구가 history에 `verdict: rewrite`·`reason: advisory_apply`·`advisory_responses`를 기록한다. `--rewrite-target`이 필수이고(없으면 `design_gate_result_invalid`, 상태 불변), status는 `fail`, `refinement_pending=true`다. 이 회차는 반복 상한 계산에서 제외한다. 다음 `start`는 해당 attempt에 `refinement: true`를 기록하고 응답에 `refinement: true`를 싣는다(평소에는 `false`). 스킬 §6은 이 값을 evaluator 입력 `refinement`로 그대로 넘긴다. refinement 회차의 결과는 다음과 같다. ⓐ record pass → 기존 pass 전이, `refinement_pending=false`. ⓑ record 비-pass(rewrite·input_error) → history의 해당 verdict에 `reason: advisory_refinement_failed`를 붙이고 `status=retry_limit`·`await_user`·`decision_request`로 전이한다. ⓒ start ⑦ 결정론 검사 실패 → history `verdict: deterministic_fail`, reason 앞에 `advisory_refinement_failed: `를 붙이고 같은 `retry_limit` 전이를 탄다. ⓓ record 전에 문서가 바뀌어 다음 start가 이 시도를 `superseded`로 닫으면 refinement 결과로 보지 않는다. `refinement_pending`을 유지하므로 다음 start도 refinement 회차다. ⓑⓒ 뒤 `reset --owner user`는 `refinement_pending=false`로 되돌리고 일반 회차부터 다시 시작한다 | AC-6, C-3, D-1 §7.1 |
| 상한 비소비 계산 | 설계 경로는 `advisory_apply` 회차와 refinement 회차(ⓐ~ⓓ 전부)를 `limit_from` 기반 상한 비교(`state_tool.py:6891`의 start ⑦ 실패 계산과 record 비-pass 계산 둘 다)에서 제외한다. 판정 기준은 record 시점의 apply 여부와 attempt `refinement` 플래그다. 제외 방식은 `limit_from`을 1 올리는 것이며, 새 상태 값은 만들지 않는다(C-3). 목표-커버 경로는 이력 원소의 `counted: false`로 표시하고, 상한은 `counted: true` 원소 수로 계산한다 | AC-6 |
| 목표-커버 기록 명령 | `test-tool scenario-gate-record --task-folder P --iteration N [--evaluator-result R] [--advisory-responses A] [--producer-artifact TEST-SCENARIO.md]`. 스킬은 evaluator 디스패치 여부와 무관하게 **매 회차 1회** 호출한다. builder(`scenario-coverage-build`)가 exit 17이면 builder는 남아 있던 `.scenario-coverage-input.json`을 지워 이전 입력이 재판정되지 않게 한다. 스킬은 evaluator를 부르지 않고 `scenario-gate-record --task-folder P --iteration N --input-error <builder detail>`을 호출한다. 이 모드는 coverage·evaluator·응답 검사 없이 `verdict: escalate`·`reason: input_error`·`counted: true`·`input_error: <detail>` 원소를 기록한다. refinement 회차여도 reason은 `input_error`다(입력 차단이 refinement 판정보다 앞선다). 스킬 §1의 'builder exit 17은 입력 오류로 중단'은 이 기록 뒤 `escalate`/`input_error` 반환으로 유지된다. 일반 모드 처리 순서: ① 이력 마지막 iteration+1 == N 검사(아니면 exit 18) ② `.scenario-coverage-input.json`을 coverage-check와 같은 로직으로 재판정. 파일 부재·파손·필수 키 누락이면 evaluator 결과 없이 `verdict: escalate`·`reason: input_error`·`counted: true` 원소를 기록하고 exit 0으로 반환한다 ③ 누락이 있으면 evaluator 결과가 없어도 된다(주어지면 점수만 기록). 누락이 없는데 evaluator 결과가 없으면 exit 18이다 ④ evaluator 결과가 있으면 3축 점수로 pass를 재계산해 evaluator `verdict`와 대조한다(불일치 exit 18) ⑤ advisory·응답 검사 ⑥ 묶음 hash 계산: `TASK.md`·`PLAN.md` 중 존재하는 파일과 producer 파일의 sha256을 이 순서로 `이름\n해시` 줄로 이어 sha256한다. producer 파일이 없으면 exit 18이다 ⑦ 원소 `{iteration, missing, scores, gaps, verdict, reason, advisories, advisory_responses, refinement, counted, bundle_hash, files, at}`를 배열 끝에 붙여 tmp→`os.replace`로 원자 저장 ⑧ `{verdict, reason, iteration, next_refinement}` 반환. 판정표(위에서 먼저 맞는 행): refinement 회차(직전 원소 `reason: advisory_apply`로 도구가 판정)에서 누락 0·evaluator pass면 `pass`/`converged`/`counted: false`, 그 외면 `escalate`/`advisory_refinement_failed`/`counted: false` → 일반 회차 누락 0·evaluator pass·apply 1건 이상이면 `rewrite`/`advisory_apply`/`counted: false`/`next_refinement: true` → 누락 0·evaluator pass면 `pass`/`converged` → 이번 원소를 포함한 `counted: true` 원소가 상한(3, `guards.md` 목표-커버 행)에 도달하면 `escalate`/`retry_limit` → 직전 두 counted 원소 대비 연속 2회 개선 없음(누락 수가 줄지 않고 점수 합이 오르지 않음, 점수 없음은 0)이면 `escalate`/`no_progress` → 그 외 `rewrite`/`recoverable`. 스킬 반환 verdict·reason은 이 값을 그대로 쓴다. evaluator 입력 `refinement`는 직전 record 응답의 `next_refinement`를 그대로 넘긴다. 도구의 refinement 판정은 이 입력과 무관하게 이력으로만 내린다 | AC-5, AC-6, C-4, D-1 §7.2, D-2 §종료 조건 |
| 목표-커버 검증 명령 | `test-tool scenario-gate-verify --task-folder P [--producer-artifact ...]`: 이력 파일이 있고, 마지막 원소가 `verdict: pass`이며, 그 `bundle_hash`가 현재 묶음 hash와 같을 때만 exit 0이다. 아니면 exit 20 `scenario_gate_not_passed`와 `detail.reason`을 반환한다. 이력 파일 부재는 `history_missing`, 배열이 아니거나 비어 있거나 마지막 원소에 `bundle_hash`가 없는 구형 원소는 `history_invalid`, 마지막 verdict가 pass가 아니면 `not_passed`, 해시 불일치는 `bundle_changed`다. 묶음 hash는 기록 명령과 같은 함수로 계산한다. 마지막 pass는 기록 시점에 응답 완전성과 refinement 최종 pass를 이미 통과한 원소다. apply 원소는 `verdict: rewrite`이므로 refinement 전에는 통과하지 않는다 | AC-7 |
| mark 가드 | `state-tool mark`가 key `test_scenario.scenario_gate` 또는 `plan.scenario_gate` 행을 미완에서 완료(`--done`, `--step N/N`)로 바꿀 때 형제 test-tool의 `scenario-gate-verify`를 subprocess로 호출한다. exit 0이 아니면 `scenario_gate_record_required`로 거부하고 state.json을 바꾸지 않는다. `--force`·`--auto-pass`·`--as-worker`로 우회할 수 없다. 이미 완료된 행과 다른 key에는 적용하지 않는다. `plan.design_gate`에는 적용하지 않는다(기존 가드). 오류 코드는 `DESIGN_GATE_ERROR_CODES` 테이블에 추가한다(ERROR_CODES 키 집합 동결 유지) | AC-7, C-1, D-1 §7.2 |
| 가드 범위 | mark 가드는 opd·opds 두 행 key만 대상으로 한다. opsdd `review.scenario_gate`는 기록 명령은 쓰되 mark 가드는 추가하지 않는다 | D-1 §7.2가 두 key만 명시. TASK 제외 범위 밖 확장을 하지 않음 |
| oppb evidence 실패 기록 | `op-scenario-gate` §5.2의 "실패 코드를 이력의 해당 회차에 기록"을 기록 명령으로 바꾼다. `scenario-gate-record --task-folder P --iteration N --evidence-error <code>`는 이력 마지막 원소의 iteration이 N일 때만 그 원소에 `evidence_error: <code>`를 추가한다. 동시에 `verdict: escalate`·`reason: input_error`로 바꿔 원자 저장한다. N이 다르거나 이력이 없으면 exit 18이다. 이 모드와 `--input-error` 모드는 서로 배타적이고, 다른 선택 인자와도 함께 쓸 수 없다(위반 시 exit 18). 스킬은 이력을 직접 편집하지 않는다 | C-4, S-1 |
| 이력 형식 호환 | `.scenario-gate-history.json`은 배열을 유지하고 원소에 필드를 추가만 한다 | H-2, D-11:322-323 |
| 증거 공유 | 여러 S-ID가 같은 SHA·명령·환경의 증거 경로를 참조할 수 있다. 판정은 S-ID별 assertion `expected`/`actual`로 기록하며 `test-scenario.json` 필드를 추가하지 않는다. test-cycle.md §EXECUTE 증거 재사용 뒤에 한 문단으로 둔다 | C-5, D-1 §8 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. test-tool 유형 변환·정확 중복·게이트 기록 | opal-task-agent (test-tool 파일 단독 소유) | `opal/tools/test-tool/lib/scenario.py`, `opal/tools/test-tool/lib/e2e_contract.py`, `opal/tools/test-tool/schema/test-scenario.schema.json`, `opal/tools/test-tool/tests/test_scenario.py`, `opal/tools/test-tool/README.md` | Decisions의 유형 열 전환·payload 전달·check+RED·정확 중복·advisory 결과·응답 형식·목표-커버 기록(판정표·evaluator 없는 회차·`--input-error` 모드·builder 실패 시 이전 입력 삭제 포함)·oppb evidence 실패 기록·검증 명령을 구현한다. `SCENARIO_ERROR_CODES`에 `scenario_gate_record_invalid`(exit 18)·`advisory_response_invalid`(exit 19)·`scenario_gate_not_passed`(exit 20)를 추가하고 dispatch·subparser·@header exports를 갱신한다. README에 두 명령과 exit 코드를 추가한다. 테스트는 RED-first로 먼저 실패를 관찰한다 | 없음 | P1 | AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, C-1, C-2, C-4 |
| W-2. 작성 기준·게이트 규범·에이전트 계약 문서 | opal-task-agent (문서 단독 소유) | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`, `opal/skills/op-scenario-gate/SKILL.md`, `opal/skills/op-scenario-gate/README.md`, `opal/agents/opal-evaluator-agent/AGENT.md`, `opal/agents/opal-test-agent/AGENT.md`, `opal/core/references/harness/scenario-gate.md`, `opal/core/references/harness/design-gate.md`, `opal/core/references/harness/test-cycle.md` | 가이드에 D-1 §3의 별도 시나리오·통합·Check·계층·경계 기준과 `유형` 열(표 열 계약·출력 템플릿·완료 검사)을 넣는다. 스킬 §4는 매 회차 `scenario-gate-record` 호출(evaluator 입력 `refinement`는 직전 record 응답의 `next_refinement`)로 바꾸고, §5.2의 이력 기록은 `--evidence-error` 호출로 바꾼다. §1의 builder exit 17은 `--input-error` 기록 뒤 escalate 반환으로 바꾼다. §6은 start 응답 `refinement`를 evaluator 입력으로 넘기는 규칙과 응답 파일·`--advisory-responses`를 추가한다. 두 경로 반환 reason enum에 `advisory_apply`·`advisory_refinement_failed`를 추가한다. evaluator에는 `advisories[]` 계약과 `refinement` 입력을, test-agent에는 `type` 변환을, scenario-gate.md에는 advisory·refinement 판정 의미를, design-gate.md에는 history reason·refinement·신규 오류 코드 2종을, test-cycle.md에는 증거 공유 문단을 넣는다. 수기 변경이력 행은 추가하지 않는다 | 없음 | P1 | AC-1, AC-2, AC-4, AC-5, AC-6, C-3, C-4, C-5 |
| W-3. state-tool advisory·refinement와 목표-커버 mark 가드 | opal-task-agent (state-tool 파일 단독 소유) | `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/schema/state.schema.json`, `opal/tools/state-tool/tests/test_design_gate.py`, `opal/tools/state-tool/tests/test_mode_transition_contract.py`, `opal/tools/state-tool/tests/test_state_tool_mode_contracts.py` | `design-gate record`에 `--advisory-responses`를 추가하고 Decisions의 advisory 반영 전이·상한 비소비 계산을 구현한다. `design-gate start`는 `refinement_pending`이면 attempt와 응답에 `refinement: true`를 싣고, refinement 회차의 결정론 실패를 ⓒ대로 처리한다. `reset`은 `refinement_pending`을 false로 되돌린다. `cmd_mark`에 Decisions의 mark 가드를 넣는다. `DESIGN_GATE_ERROR_CODES`에 `advisory_response_invalid`·`scenario_gate_record_required`를 추가한다. 스키마에는 design_gate `refinement_pending`, attempt `refinement`, history `advisory_responses`·`advisories`·`refinement`를 선택 필드로 추가한다. @header 설명을 갱신한다. 테스트는 RED-first로 먼저 실패를 관찰한다 | W-1 | P2 | AC-5, AC-6, AC-7, C-1, C-3 |
| W-4. 프로젝트 문서 동기화와 제안서 이관 | opal-task-agent (문서 단독 소유) | `docs/PROJECT.md`, `docs/proposals/opal-test-scenario-economy-gate.md`, `docs/proposals/archives/opal-test-scenario-economy-gate.md` | PROJECT.md의 `test-tool scenario-*` 행에 `scenario-gate-record`·`scenario-gate-verify`와 advisory 응답을 추가하고, TEST-SCENARIO 목표-커버 게이트 절 tool-gated 문단에 mark 가드를 추가한다. 제안서를 `docs/proposals/archives/opal-test-scenario-economy-gate.md`로 `git mv`하고 상태 줄을 `채택·구현 완료(태스크 167)`로 바꾼다 | W-1, W-2, W-3 | P3 | AC-1, AC-7 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. install 직후 목표-커버 게이트 행이 미완인 진행 중 태스크는 새 기록 명령으로 만든 이력이 없어서 mark가 거부된다 | 진행 중 opd·opds(worker 경로) 태스크의 게이트 행 완료 | 해당 태스크가 게이트 행에서 멈춤 | 거부 응답의 `required_action`에 `scenario-gate-record` 재실행 절차를 싣고, 이미 완료된 행에는 가드를 적용하지 않는다(S-7) |
| H-2. 이력 원소 형식을 바꾸면 skill-tester가 게이트 통과를 잘못 읽는다 | `skill_tester.py`의 이력 배열 마지막 `verdict` 판독 | 모의 테스트 합격 판정 오류 | 배열을 유지하고 필드만 추가한다. 기록 명령이 만든 이력을 같은 판독 로직으로 읽어 확인한다(S-6) |

## Release and recovery

- 적용 순서: P1(W-1·W-2 병렬) → P2(W-3) → P3(W-4). 각 그룹 PM Gate 뒤 `worktree-tool checkpoint`로 워크트리 체크포인트를 만든다.
- 검증 범위: 결정론 검사는 test-tool·state-tool 단위·계약 테스트다. 통합 검사는 워크트리 소스 CLI를 임시 태스크 폴더에서 실제 호출하는 흐름이다. 최종 Gate는 `opal/tools/test-tool/tests`·`opal/tools/state-tool/tests` 전체 회귀 1회다.
- 설치본 검증: 워크트리에서는 install하지 않는다. merge 후 허브에서 `scripts/install-mac.sh`를 실행한 뒤 다음을 확인한다. `~/.opal/tools/test-tool/run.sh scenario-gate-verify --help` 성공, `~/.opal/tools/state-tool/run.sh`로 임시 태스크의 목표-커버 게이트 행 mark 거부 재현, 설치본 evaluator로 중복 시나리오 fixture의 advisory 반환 1회 확인. 이 단계는 허브 PM이 캡틴 승인 후 수행한다.
- 실측(이전 AC-8): 이 태스크의 최초 TEST-SCENARIO 작성본과 advisory 반영 후 최종본 각각의 행동 시나리오 수·RED 대상 수·Check 수를 AGENTIC-LOG.md와 DONE.md에 기록하고, 통합 또는 유지 결과를 설명한다(D-1 §9 마지막 문단, §11-11). 이 태스크의 설계 게이트는 설치본(구 evaluator)으로 수행하므로 advisory가 나오지 않을 수 있다. 그때는 최초본과 최종본이 같음을 사유와 함께 기록한다.
- 실패 시: 설치 전 실패는 워크트리 브랜치 수정 또는 체크포인트 이후 보정 커밋으로 복구한다. 설치 후 문제가 생기면 허브에서 merge 이전 커밋으로 되돌린 소스로 install을 재실행한다. 이미 잠긴 `test-scenario.json`과 완료된 게이트 행은 이 변경으로 바뀌지 않는다(C-1).
