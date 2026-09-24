---
template: sdlc-v2
---
# PLAN: PM 설계 경로 단일화와 독립 설계 게이트

> 입력: [TASK.md](TASK.md) | 작성: PM(actor=coordinator, 현행 opds 계약 — C-9)

## 참조 문서

| # | 유형 | 문서 | 경로 | 참조 이유 |
|---|---|---|---|---|
| D-1 | 소스 | state-tool | `opal/tools/state-tool/state_tool.py` | 초기화 인자·단계 가드·자동 승인·게이트 산출물·AC/C 검사·gate 사건 |
| D-2 | 설계 | Dev Pilot pipeline | `opal/skills/opal-pilot-dev/references/pipeline.json`, `pipeline-short.json` | 현행 행 구성(보존 대상) |
| D-3 | 설계 | 목표-커버 게이트 | `opal/core/references/harness/scenario-gate.md`, `opal/skills/op-scenario-gate/SKILL.md` | 결정론→evaluator 흐름, 종료 조건 |
| D-4 | 설계 | evaluator | `opal/agents/opal-evaluator-agent/AGENT.md` | phase 체계와 결과 계약 |
| D-5 | 설계 | agentic harness | `opal/core/references/opal-harness-agentic.md` | §4 대행 검토, §5 Gate 루핑 |
| D-6 | 설계 | guards | `opal/core/references/harness/guards.md` | §자동 루핑 제약 상한 표 |
| D-7 | 설계 | 이벤트 manifest | `opal/core/references/events.json`, `opal/tools/event-loader/event_loader.py` | 이벤트 목록·표준 이벤트 집합 |
| D-8 | 설계 | 트랙 라우팅 | `opal/skills/opal-pilot-dev/references/track-routing.md` §2 | 결정 범위 3종(C-5) |
| D-9 | 설계 | actor | `opal/core/references/harness/actor.md` | PM 조율 계약·독립 검증 경계 |
| D-10 | 소스 | test-tool coverage | `opal/tools/test-tool/lib/scenario.py` | sdlc-v2 coverage build/check exit 계약 |

code-scan 결과(`code-scan scan <file> --json`, headerSource=inline):

| 파일 | module | layer | domain | depends | exports(발췌) |
|---|---|---|---|---|---|
| `opal/tools/state-tool/state_tool.py` | state_tool | util | opal-pipeline | 없음 | cmd_init, cmd_resolve_start, cmd_advance, cmd_mark, cmd_validate |
| `opal/tools/event-loader/event_loader.py` | event_loader | util | opal-tools | 없음 | load_event, verify_receipt, static_check |
| `opal/tools/test-tool/lib/scenario.py` | scenario | util | opal-tools | lib.e2e_contract | cmd_scenario_coverage_check, add_scenario_subparsers |

## Approach

opd/opds 신규 `coordinator` 태스크에만 새 PM 경로 파이프라인(`pipeline-pm.json`)을 적용한다. `resolve-start`가 파이프라인 파일까지 init 인자로 판정하고, 설계 게이트는 `state-tool design-gate` 서브커맨드가 결정론 검사·해시 기록·반복 상한·run-log 사건을 소유한다. evaluator는 새 phase `design-rubric` 1회로 설계 4축과 시나리오 3축을 함께 판정한다. PM 경로 여부는 state.json의 행 key(`plan.design_gate` 존재)로만 판정하므로 기존 태스크 재개·`--no-pm`·다른 Pilot은 코드 경로를 타지 않는다(C-1).

## Findings

### 직접 변경

- `opal/tools/state-tool/state_tool.py` — 신규 init_args에 `--rows-from`이 없다(`state_tool.py:3842-3844`). AC/C 검사는 참조 존재만 본다(`state_tool.py:5553-5564`). 게이트 검사는 산출물 존재만 본다(`state_tool.py:3037-3061`). 확인 행 자동 승인은 상태만 바꾸고 문서 내용을 기록하지 않는다(`state_tool.py:2912-2958`). gate 사건 조립기는 있으나 게이트 행과 묶이지 않는다(`state_tool.py:2243-2371`).
- `opal/tools/state-tool/schema/state.schema.json` — 루트 `additionalProperties: false`라 새 `design_gate` 블록 등재가 필요하다.
- `opal/skills/opal-pilot-dev/references/pipeline-pm.json` — 신설.
- `opal/core/references/events.json`, `opal/tools/event-loader/event_loader.py` — 표준 이벤트 집합이 코드 상수로 고정돼 있다(`event_loader.py:26-41`, 불일치 시 `event_loader.py:182-183`이 누락·초과로 판정).
- `opal/skills/op-scenario-gate/SKILL.md`, `opal/agents/opal-evaluator-agent/AGENT.md` — evaluator는 `scenario_source`만 읽는다(`opal/agents/opal-evaluator-agent/AGENT.md:120`).
- `opal/skills/op-dev-plan/references/plan-guide.md` — PM 경로 Findings 형식 부재.
- `opal/core/references/opal-harness-agentic.md`, `opal/core/references/harness/guards.md` — Normal/Minor 3회 초과 진행 규칙(`opal-harness-agentic.md:98-118`), 목표-커버 게이트 상한 3회(`guards.md:90`).

### 회귀 확인

- `opal/skills/opal-pilot-dev/references/pipeline.json`, `opal/skills/opal-pilot-dev/references/pipeline-short.json` — 내용 불변(C-2).
- `opal/tools/test-tool/lib/scenario.py` — coverage build/check를 호출만 한다(exit 0/16/17 계약 불변).
- `scripts/tests/task136_mode_transition_contract.py`, `opal/tools/state-tool/tests/test_pilot_shared_contract.py` — 기존 pipeline 목록·Pilot 공유 계약 회귀.
- `opal/skills/opal-pilot-write-tech/SKILL.md`, `opal/skills/opal-pilot-project/SKILL.md`, `opal/skills/opal-pilot-sdd/SKILL.md` — 단계 이벤트 매핑 불변(AC-10).

### 문서 갱신

- `opal/skills/opal-pilot-dev/SKILL.md`, `opal/skills/opal-pilot-dev/README.md` — PM 경로 절차, init 계약, 결정 체크포인트.
- `opal/core/references/harness/actor.md` — 독립 검증 행 표에 `plan.design_gate` 추가(`actor.md:104`).
- `opal/core/references/harness/skill-commands.md` — opd/opds 기본 경로 설명(`skill-commands.md:34-40`).
- `opal/core/references/harness/design-gate.md` — 신설 SSOT.
- `opal/tools/state-tool/README.md` — 새 서브커맨드·오류 코드.
- `docs/PROJECT.md` — Dev 파이프라인 표·actor 주석·문서 레지스트리.

### 미확인 가정

- H-1(Risks): 설치본에서 `state-tool`과 `skills/`의 상대 배치가 소스와 같다.
- 그 외 없음.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| DEC-1 파이프라인 선택 | `resolve-start --new-task`가 opd/opds에 대해 `init_args`에 `--rows-from <절대경로>`를 추가한다. `coordinator`→`pipeline-pm.json`, `worker`+opd→`pipeline.json`, `worker`+opds→`pipeline-short.json`. 경로는 `state_tool.py` 기준 `../../skills/opal-pilot-dev/references/`로 해석하고 파일이 없으면 `spec_file_not_found`로 거부한다. 재개 응답에는 넣지 않는다. 다른 Pilot의 init_args는 불변 | AC-1 "도구 판정". 소스·설치본 모두 `tools/`와 `skills/`가 같은 루트 아래 있다(`scripts/install-mac.sh:1286`) |
| DEC-2 PM 경로 행 | `pipeline-pm.json`(`skill: "opd"`, `meta.mode_label: "PM Design Path"`, `meta.stages: ["TASK","PLAN","EXECUTE","TEST","CLOSE"]` — `meta`는 스키마상 두 키만 허용(`opal/tools/state-tool/schema/pipeline-spec.schema.json`)) EXECUTE 전 6행: `task.task_md`(TASK 작업) · `task.user_confirm`(TASK 사용자 확인) · `plan.plan_md`(PLAN 작업) · `plan.test_scenario_md`(PLAN "TEST-SCENARIO 작성") · `plan.design_gate`(PLAN "설계 게이트", gate.artifacts=TASK/PLAN/TEST-SCENARIO) · `plan.user_confirm`(PLAN "사용자 확인" = 설계 확인). 이후 행은 `pipeline-short.json` id 7~16과 key·item 동일 | 확인 행 item은 자동 승인 판정 키(`item != "사용자 확인"` 건너뜀, `state_tool.py:2934`)라 문자열을 유지한다. `skill`은 spec 검증 enum(`state_tool.py:3249`)과 Pilot registry alias 대조 테스트를 통과하는 값이다 |
| DEC-3 PM 경로 판정 | `_is_pm_design_path(state)` = rows에 key `plan.design_gate`가 있음. 새 가드·기록은 모두 이 판정이 참일 때만 작동 | 저장 행으로 재개하는 기존 태스크와 `--no-pm`이 코드 경로를 타지 않는다(C-1) |
| DEC-4 문서 묶음 해시 | 대상 = 태스크 폴더의 `TASK.md`, `PLAN.md`, `TEST-SCENARIO.md`. 파일별 sha256과 묶음 hash = sha256(`"TASK.md\n"+h1+"\nPLAN.md\n"+h2+"\nTEST-SCENARIO.md\n"+h3`). 파일 부재는 `design_gate_input_missing`. TASK 요구 hash = `## Constraints`·`## Acceptance criteria` 본문(`_section_body_by_heading`)의 sha256 | 바이트 단위 비교가 가장 단순한 결정론이다. TASK 확인은 AC/C 변경에만 묶는다(AC-6) |
| DEC-5 state 저장 | PM 경로 태스크에만 `state.design_gate` 블록: `status`(`idle`/`evaluating`/`pass`/`fail`/`retry_limit`), `iteration`, `limit`(=3), `limit_from`(reset 시점 iteration, 초기 0), `task_confirm_req_hash`, `current_attempt{iteration, bundle_hash, files, started_at}`, `passed_bundle_hash`, `approved_bundle_hash`, `last_rewrite_target`, `history[]{iteration, verdict, rewrite_target, bundle_hash, reason, at}`. `state.schema.json`에 선택 속성으로 등재 | 해시·반복을 한 블록이 소유해 EXECUTE 가드가 한 곳만 읽는다 |
| DEC-6 확인 해시 기록 | PM 경로에서 `task.user_confirm`이 done이 되는 순간(자동 승인·`mark` 모두) `task_confirm_req_hash`를 기록한다. `plan.user_confirm`이 done이 되는 순간 현재 묶음 hash가 `passed_bundle_hash`와 같지 않으면 `design_bundle_mismatch`로 거부하고, 같으면 `approved_bundle_hash`에 기록한다. 해당 stage의 자동 승인이 허용되지 않는 mode에서 `--owner user` 없이 확인 행을 mark하면 `user_confirmation_required`로 거부한다 | 승인이 문서 내용에 묶인다(AC-6). 확인 주체 규칙은 기존 자동 승인 판정(`can_auto_approve_user_confirmation`, `state_tool.py:124`)을 재사용한다 |
| DEC-7 `design-gate start` | `state-tool design-gate start <task> --iteration N`. 순서: ① PM 경로 아님→`design_gate_not_applicable` ② `execute.implement`가 pending 아님→`design_gate_locked` ③ `status=retry_limit`→`design_gate_retry_limit` ③-1 `plan.design_gate` 앞 행이 미완이면 기존 `stage_transition_violation`(`check_stage_transition_guard` 재사용) ④ TASK 요구 hash≠`task_confirm_req_hash`→`task_reconfirm_required` ⑤ `N≠iteration+1`→`design_gate_iteration_invalid` ⑥ 직전 verdict가 rewrite면 `last_rewrite_target` 문서(plan→PLAN.md, scenario→TEST-SCENARIO.md, both→둘 다)의 hash가 직전 시도와 같을 때 `rewrite_target_unchanged` ⑦ 결정론 검사(DEC-8). ①~⑥은 상태를 바꾸지 않는다. ⑦ 실패는 시도로 기록(`verdict: deterministic_fail`, iteration 증가)하고 `design_gate_deterministic_fail`로 missing을 반환한다. 통과하면 `status=evaluating`, `current_attempt` 기록, `passed/approved` 해시 삭제, `plan.design_gate` 행을 in_progress로, `plan.user_confirm`이 done이면 pending으로 되돌리고 gate.requested(`gate_id=design-gate-i{N}`)를 같은 원자 커밋으로 남긴다 | 재평가 시작이 이전 승인을 무효화해 "재평가만 통과하고 이전 승인 재사용" 경로를 막는다(AC-6). rewrite 대상 불변 재판정을 막는다(AC-5) |
| DEC-8 결정론 검사 | ① sdlc-v2 TASK 필수 5절(`_check_sdlc_v2_task_contract`) ② 기존 `_check_plan_contract` 전 항목 + strict: TASK의 모든 AC/C가 어느 Work item `완료 기준 연결`에도 없으면 `uncovered requirement AC-N`(시나리오 연결 여부 무관) ③ PLAN `## Findings`에 H3 `직접 변경`·`회귀 확인`·`문서 갱신`·`미확인 가정`이 모두 있고 본문이 비지 않음(`없음.` 허용) ④ `회귀 확인`의 백틱 경로가 Work item `변경 대상`에 있으면 `regression target listed as change` ⑤ `직접 변경`·`문서 갱신`의 백틱 경로가 어느 Work item `변경 대상`에도 없으면 `finding not in work items` ⑥ `미확인 가정` 항목은 `없음` 또는 PLAN Risks에 존재하는 `H-N` 참조를 포함 ⑦ `test-tool scenario-coverage-build --template sdlc-v2` + `scenario-coverage-check`를 subprocess로 실행해 exit 0 요구(16→missing 병합, 17→`input_error`). `verify --plan-contract-check`는 strict 없이 기존 동작 유지 | AC-2·AC-3·C-7. test-tool 호출은 형제 도구 subprocess 선례(`_MEMORY_TOOL`, `state_tool.py:2726`)와 같은 방식이다 |
| DEC-9 `design-gate record` | `state-tool design-gate record <task> --iteration N --verdict pass\|rewrite\|input_error --evaluator-result <json> [--rewrite-target plan\|scenario\|both]`. 검사: `status=evaluating`, N=`current_attempt.iteration`, 현재 묶음 hash=`current_attempt.bundle_hash`(다르면 `design_gate_input_changed`, 상태 불변), evaluator JSON에 `design.axes` 4키(`completeness`,`decision_clarity`,`executability`,`recoverability`)와 `scenario.scores` 3키가 있음(`design_gate_result_invalid`), `--verdict pass`는 4축 전부 PASS이고 시나리오 각 ≥1·평균 ≥1.5일 때만 허용(`design_gate_verdict_mismatch`), rewrite는 `--rewrite-target` 필수. pass→`status=pass`, `passed_bundle_hash` 기록, `plan.design_gate` done. 비-pass→`status=fail`, history 추가, `iteration - limit_from`이 limit에 도달하면 `status=retry_limit`과 `transition_action=await_user`·`report_type=decision_request`(심각도 무관). 모든 경우 gate.resolved를 같은 커밋으로 남긴다. run-log `data.verdict`는 기존 폐쇄 enum(`approved`/`rejected`/`auto`, `state-tool gate-resolve --verdict` choices)을 따라 pass→`approved`, 그 외→`rejected`로 쓰고 설계 게이트 verdict 원문은 `summary`와 state history에 남긴다 | AC-4·AC-5·AC-6·AC-7·AC-9. 판정 수치는 도구가 재계산해 산문 판단을 배제한다(C-6) |
| DEC-10 `design-gate reset` | `state-tool design-gate reset <task> --owner user --note <사유>`만 `retry_limit`을 해제한다(`status=idle`, `limit_from=iteration`, iteration 번호는 이어서 사용해 `gate_id=design-gate-i{N}` 중복(`gate_duplicate`, `state_tool.py:2300-2302`)을 피한다. history 보존, 의사결정 로그 기록). `--owner user` 없으면 `user_confirmation_required` | 반복 상한 뒤 재개는 사용자 결정이다(AC-7) |
| DEC-11 게이트·EXECUTE 가드 | PM 경로에서 `mark plan.design_gate --done`은 `status=pass`이고 현재 hash=`passed_bundle_hash`일 때만 허용(`design_gate_not_passed`/`design_bundle_mismatch`). `advance`/`mark execute.implement`는 자동 승인 이후·저장 전에 `status=pass` ∧ 현재=passed=approved ∧ TASK 요구 hash=`task_confirm_req_hash`를 요구한다. 실패 코드: `design_gate_not_passed`, `design_bundle_mismatch`, `task_reconfirm_required`. `--force`로 우회하지 못한다 | EXECUTE 진입을 상태 저장 전 검사로 집행한다(C-6, AC-6, AC-7) |
| DEC-12 설계 결정 기록 | `state-tool design-decision <task> --scope external\|detail --summary <text> --basis <text>`. PM 경로 PLAN 단계에서만 허용. `detail`→STATE.md 의사결정 로그 + PM activity(decision) 사건, `continue`. `external`→`plan.plan_md` 행을 `block`과 같은 방식으로 failed·`current_status=blocked`, `transition_action=blocked`/`decision_request`, 사유에 summary. 해소는 기존 `status --set`·`advance` 재개 경로 | AC-8을 도구로 판정 가능하게 한다. 분류 기준은 트랙 라우팅 결정 범위 3종이다(C-5, → D-8 §2) |
| DEC-13 설계 이벤트 | `events.json`에 `stage.design`(required: analysis-core, citation-rules, red-first, scenario-gate, design-gate / predecessors: pilot.start / consumer: `opal/skills/opal-pilot-dev/SKILL.md`)을 추가하고 `STANDARD_EVENTS`에 등재. 기존 `stage.*` 문서 목록은 불변 | AC-10, C-2 |
| DEC-14 evaluator phase | `phase: design-rubric` 추가. 입력 `task_md`·`plan_md`·`scenario_source`·`iteration`. 설계 4축 PASS/FAIL(앵커: 요구·변경 범위 완전성 — AC/C·Findings가 Work item·시나리오로 빠짐없이 이어짐 / 결정·계약 명확성 — 외부 동작·인터페이스·실패 정책·구조·저장 방식을 구현자에게 남기면 FAIL / 실행 가능성 — Work item만으로 추가 설계 없이 구현 가능 / 적용·복구 가능성 — 설치·검증·실패 복구 경로 존재) + 기존 scenario-rubric 3축 0~2. 반환 `{design:{axes,gaps}, scenario:{scores,average,gaps}, verdict, rewrite_target}`. 파일 생성 없음. 기존 5 phase 불변 | AC-4·AC-5. 설계·시나리오를 한 번에 보되 판정은 분리한다 |
| DEC-15 게이트 호출자 | `op-scenario-gate`에 입력 `gate: design`(pilot opd/opds, PM 경로)을 추가: `design-gate start` → evaluator `design-rubric` 1회 → `design-gate record`. 기존 입력(무 `gate`)의 흐름은 불변 | 호출 절차를 스킬이, 판정 기록을 도구가 소유한다 |
| DEC-16 agentic 개정 | agentic §4에 "PM 경로 설계 구간(`plan.plan_md`~`plan.user_confirm`)은 PM 대행 검토 대신 설계 게이트 판정을 따른다", §5에 "설계 게이트는 이 루핑 규칙을 적용하지 않고 `design-gate`의 상한 도달 시 사용자 대기" 한정 조항을 추가. `guards.md` 상한 표에 "설계 게이트 3회 → 사용자 대기(심각도 무관)" 행 추가 | C-4, AC-7 |
| DEC-17 트랙 제안 | PM 경로 태스크는 opd/opds가 같은 행을 쓰므로 강등·강업 제안(track-routing §3, track-escalation)을 수행하지 않는다. 대신 PLAN 작성 중 새 결정을 DEC-12로 분류한다 | 두 트랙이 같은 파이프라인을 쓰는 Proposed outcome의 귀결이다 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. RED 테스트 작성 | opal-test-agent (red mode) | `opal/tools/state-tool/tests/test_design_gate.py`, `opal/tools/event-loader/tests/test_event_loader_design_event.py`, `opal/tools/event-loader/tests/test_event_loader_extended.py` | TEST-SCENARIO의 `구현 전 RED` 시나리오를 공개 CLI(subprocess)로 검증하는 테스트를 작성하고 실패를 관찰한다. `test_event_loader_extended.py`의 `STANDARD_EVENTS` 기대 튜플에 `stage.design`을 추가한다 | 없음 | P1 | AC-1, AC-2, AC-3, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10 |
| W-2. state-tool 설계 게이트 구현 | opal-task-agent | `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/schema/state.schema.json`, `opal/tools/state-tool/README.md` | DEC-1, DEC-3~DEC-12 구현. `design-gate {start,record,reset}`·`design-decision` argparse 등록, ERROR_CODES에 신규 코드 등재(`design_gate_locked`·`design_gate_input_changed`·`design_gate_not_passed`·`design_bundle_mismatch`·`task_reconfirm_required`·`rewrite_target_unchanged`·`design_gate_retry_limit` 등), `design_gate_retry_limit`·`task_reconfirm_required`를 `AWAIT_USER_ERROR_CODES`에 추가, gate 사건은 `_build_gate_event`를 재사용해 상태 커밋과 같은 `run_log_commit` 호출로 남김. 파일 @header에 새 계약 반영. schema에 `design_gate`·`actor` 선택 속성 등재. README 서브커맨드·오류 코드 절 갱신 | W-1 | P2 | AC-1, AC-2, AC-3, AC-5, AC-6, AC-7, AC-8, AC-9, C-1, C-6, C-7 |
| W-3. PM 경로 파이프라인·설계 이벤트·harness | opal-task-agent | `opal/skills/opal-pilot-dev/references/pipeline-pm.json`, `opal/core/references/events.json`, `opal/tools/event-loader/event_loader.py`, `opal/core/references/harness/design-gate.md`, `opal/core/references/harness/guards.md` | DEC-2 파이프라인 신설. DEC-13 `stage.design` 추가와 `STANDARD_EVENTS` 등재. `design-gate.md` 신설(흐름·해시·rewrite 대상·상한·확인 해시·결정 분류·실패 코드, 원문 SSOT). guards 상한 표에 설계 게이트 행 추가(DEC-16) | W-1 | P2 | AC-1, AC-7, AC-10, C-2, C-3, C-5 |
| W-4. 게이트 호출자·evaluator·PLAN 가이드 | opal-task-agent | `opal/skills/op-scenario-gate/SKILL.md`, `opal/skills/op-scenario-gate/README.md`, `opal/agents/opal-evaluator-agent/AGENT.md`, `opal/skills/op-dev-plan/references/plan-guide.md` | DEC-15 `gate: design` 절 추가. DEC-14 `design-rubric` phase(입력·4축 앵커·결과 계약·파일 미생성) 추가. plan-guide에 PM 경로 `## Findings` 4소절 형식과 결정론 검사 규칙(DEC-8 ③~⑥) 추가 | W-1 | P2 | AC-3, AC-4, AC-5, C-3, C-7 |
| W-5. Pilot·harness·레지스트리 문서 갱신 | opal-task-agent | `opal/skills/opal-pilot-dev/SKILL.md`, `opal/skills/opal-pilot-dev/README.md`, `opal/core/references/opal-harness-agentic.md`, `opal/core/references/harness/actor.md`, `opal/core/references/harness/skill-commands.md`, `docs/PROJECT.md` | SKILL: init은 `resolve-start` init_args를 그대로 사용, `coordinator` 신규는 PM 경로 절(단계→`stage.design`, PLAN+Findings→TEST-SCENARIO→`op-scenario-gate gate: design`→설계 확인→EXECUTE), DEC-12 결정 체크포인트, DEC-17. README·skill-commands 기본 경로 설명. agentic §4·§5 한정 조항(DEC-16). actor 독립 검증 행 표에 `plan.design_gate` 추가. PROJECT.md Dev 파이프라인 표·actor 주석·레지스트리에 `design-gate.md`·`pipeline-pm.json` 등재. PM 경로 자기 검토 게이트를 현행으로 서술하는 문장 제거 | W-2, W-3, W-4 | P3 | AC-8, AC-11, AC-12, C-4, C-5, C-8 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 설치본에서 `tools/state-tool`과 `skills/opal-pilot-dev/references`가 같은 루트 아래 있다 | DEC-1의 `--rows-from` 절대경로 해석 | 설치 후 신규 태스크 init 실패 | 경로 부재 시 `spec_file_not_found`로 즉시 거부(DEC-1), 설치 후 실측 시나리오로 확인 |
| H-2. 확인 행 hash 기록이 자동 승인 루프와 같은 저장 전 구간에서 실행된다 | DEC-6·DEC-11 원자성 | 거부 시 state.json이 부분 갱신됨 | 기록·검증을 `auto_approve_prior_user_confirmations` 직후, 저장 전에 수행하고 거부 시 파일 불변을 테스트 |

## Release and recovery

- 적용 순서: P1 RED(W-1) → `scenario-lock` → P2(W-2·W-3·W-4 병렬, 파일 비중첩) → P3(W-5) → 전체 회귀 → `scripts/install-mac.sh` 재설치.
- 검증 범위: 결정론 — state-tool·event-loader 신규 테스트와 `opal/tools/state-tool/run-tests.sh`, event-loader·test-tool·`scripts/tests` 회귀 전체. 판단 — evaluator `design-rubric`을 결함 PLAN 픽스처에 실제 디스패치. 실제 적용 — 설치본에서 임시 폴더에 `resolve-start --new-task` + `init` 실행 후 행 구성·`design-gate` 동작 관측, `event-loader load --event stage.design` 성공.
- 이 태스크 자체는 현행 `pipeline-short.json`으로 진행하며 새 파이프라인은 merge·install 후 신규 태스크부터 적용된다(C-9).
- 실패 시: 설치 전에는 워크트리 커밋을 되돌린다. 설치 후 결함이면 신규 태스크만 영향받으므로 `--no-pm`으로 우회 가능하고, 이전 커밋으로 재설치해 복구한다. 기존 태스크 state는 변경하지 않으므로 복구 대상이 아니다.
