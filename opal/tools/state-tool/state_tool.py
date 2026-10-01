# -*- coding: utf-8 -*-
"""
@header {
  "module": "state_tool",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "OPAL 파이프라인 현황판 JSON SSOT 관리 CLI. 서브커맨드: init/show/resolve-mode/resolve-start/advance/mark/block/validate/add-row/status/run-start/finalize-attribution/spec-validate/event-verify/log-event/gate-request/gate-resolve/design-gate(start|record|reset)/design-decision, gate-pass(deprecated). resolve-mode는 명시 플래그 > 유효 저장 mode > 신규 기본값(--skill 지정 시 NEW_TASK_DEFAULTS, 미지정 시 semi-agentic)으로 effective mode를 판정하고 기존 태스크의 명시 override는 mode만 원자 갱신한다. resolve-start는 Pilot 원문 플래그로 mode·workspace·actor 세 축을 판정한다 — 신규는 NEW_TASK_DEFAULTS(opd·opds·oppd·oppl·oppb=agentic·worktree, opd·opds actor=coordinator, 그 외 semi-agentic·hub)로 읽기 전용 판정과 init_args를 돌려주고(opd·opds는 _pilot_dev_pipeline_path()가 판정한 --rows-from 절대경로 — coordinator→pipeline-pm.json, worker+opd→pipeline.json, worker+opds→pipeline-short.json, 부재 시 spec_file_not_found), 재개는 저장값을 상속하며 다른 workspace·actor 플래그는 resume_axis_locked, 플래그 충돌은 mode_flag_conflict·workspace_flag_conflict·actor_flag_conflict, oppb 허브 요청은 workspace_required_for_skill로 거부한다. run-start <task-path>는 `run-<UTC YYYYMMDDHHMMSS>-<8자리 hex>` 형식의 새 run_id를 발급해 state.json.run_id에 기록하고 단일 라인 JSON으로 반환한다 — 현재 run은 항상 1개라 재호출 시 교체되며 이력을 누적하지 않고, run_id는 schema properties에만 있는 optional 필드라 init은 만들지 않으며 required 8필드는 불변이다(run_id 없는 기존 state.json도 계속 validate를 통과한다). 이 run_id는 run_log.active_run_id(run-log 계열, `run_<UUIDv4>`)와 서로 다른 축이다. event-verify는 단계 진입 전에 event-loader receipt의 이벤트·manifest·문서 hash 최신성을 검증하고 상태 파일은 변경하지 않는다. interactive/semi-agentic/agentic 3-way 모드를 지원하며 PLAN-equivalent 이전 단계(TASK/ANALYSIS/PLAN/TEST-SCENARIO/SPEC/REVIEW/DESIGN/WBS/WIREFRAME/DICT/MODEL/DDL·MIGRATION)는 semi-agentic 모드에서 사용자 검토를 강제한다. STATE.md는 state.json에서 파생되는 저널(의사결정 로그+블로커)이며 파이프라인 표·현재 상태·다음 액션 섹션은 없다(레거시 마커 포맷은 하위호환 인식만 유지). mark --step N/M은 N<M이면 in_progress를 유지하고 N==M에서만 done으로 닫는다. can_auto_approve_user_confirmation()은 CLOSE 축과 모드 축 2축 합성으로 사용자 확인 행 자동 승인 가부를 단일 판정하며, cmd_mark 사전검사와 cmd_validate 사후검사가 서로 다른 소비 범위(validate는 CLOSE 축 미평가)로 이를 참조한다. auto_approve_prior_user_confirmations()는 advance/mark가 대상 행 이전 구간의 미완 확인 행을 자동 승인하되 대상 행 자체가 CLOSE면 관여하지 않는다. 행 주소는 task-step 키 체계(--task-step/--task-step-id, --row는 deprecated)로 지정한다. check_gate_artifacts()는 task_steps[].gate.artifacts 존재를 검사하고(정적 경로·글롭 지원, 절대경로·'..' 이탈 토큰은 거부), 미충족 시 gate_artifact_missing으로 막되 --force+--note 조합에만 통과를 허용하며 그 경우 decision 로그에 gate_artifact_force를 강제 기록한다. verify 서브커맨드는 상호 배타적인 7개 검사 라우트를 갖는다 — --red-check(RED 증거 게이트), --fix-mode(+--changed-files/--test-globs, 테스트 불변성 게이트), --clarification-check(TASK 잠금 판정: sdlc-v2 5절 또는 legacy 명확화 4요소), --evidence-check(『명확화 결과』·『확정된 설계 방향』 인용을 근거 등급 4축으로 판정, 두 소스의 분모는 서로 분리 — confirmed_ratio는 명확화 결과 항목 수 기준 불변), --code-scan-citation-check(PLAN.md Work items 또는 legacy §4.2 파일 경로의 code-scan 인용 집행), --plan-contract-check(sdlc-v2 Work items 계약 검사), --run-log-completeness-check(135 W-4 run-log 완전성 진단, 비차단). task_root()는 task path 조상에서 .opal/MEMORY.json 앵커를 찾는 task root 목적 전용 탐색이며(118 D-4), 허브 쓰기 대상인 allocator root는 이 탐색으로 추론하지 않고 worktree registry 발급값을 명시 인자로만 받는다. 신규 pipeline은 명시적 close.final 행에서만 current_status를 completed_unmerged로 확정하고, close.final이 없는 legacy pipeline만 마지막 CLOSE 행을 final로 인정하며 MEMORY.json을 건드리지 않는다(118 D-4b, 136 W-2). 허브 .opal/MEMORY.json 이력 append는 finalize-attribution <task-path> --allocator-root <abs>가 전담한다 — link_memory_history()가 그 구현이고 동일 path 행이 있으면 건너뛰어 멱등이며, --allocator-root 미지정·상대경로는 추론 없이 exit 1로 거부된다. resolve_owner_placeholder()는 note 작성 경로(advance/mark/add-row/block/status/init)에서 '{owner_name}' 플레이스홀더를 identity.md owner_name으로 write-time 치환한다(부재 시 원문 유지, fail-safe). worker_duration_minutes는 1.0/1.1(run_log 블록 부재) 태스크에서는 종전과 동일하게 mark --worker-duration-minutes로 선택 기록되고, 워커 디스패치 행을 소요시간 없이 done 처리하면 --worker-duration-unknown 억제 인자가 없는 한 응답 warnings 배열에 worker_duration_missing이 실린다(exit 0 유지). 1.2 태스크(run_log 블록 보유)에서는 mark가 `_reconcile_worker_duration_minutes()`로 `_import_run_log_core()` 경로의 `run_log_core.reconcile_duration()`(W-6)을 호출해 해당 run의 terminal 사건(worker.completed/failed/blocked)에서 파생 분값을 읽는다(W-7, CONTRACT §2.5 시간 절, D-P8) — `--worker-run-id` 표면 인자가 없어 `_resolve_sole_terminal_worker_run_id()`가 `이 run의 terminal에 실린 worker_run_id가 정확히 1개`인 경우에만 그 값을 대상으로 삼고, 0건·2건 이상이면 조회를 건너뛰어 파생값 없음으로 처리한다. 파생값이 있으면 `--worker-duration-minutes` 미지정 시 자동 기록(경고 없음), 명시값이 파생값과 같으면 수용하되 `worker_duration_minutes_deprecated` 경고를 얹고, 다르면 상태 변경 이전 시점에 `worker_duration_conflict`(RUN_LOG_STATE_ERROR_CODES 등재, ERROR_CODES와 물리 분리)로 즉시 거부해 state.json을 손대지 않는다. 파생값을 아직 얻을 수 없으면(terminal 미기록 등) 명시값을 그대로 통과시켜 기존 수동 경로와 응답 키 집합이 바이트 동일하다(H-6, S-9). CONTRACT §2.5의 채널 등급·override 조항은 이번 범위에 포함하지 않는다(D-P9). build_todo_mirror()는 stdout 전용 파생 미러(state.json 비접촉)로 PostToolUse hook이 세션에 결정론적으로 주입한다. init --run-log-mode {shadow,active}는 CONTRACT §2.5 state-tool.init.run-log-mode를 구현한다 — shadow는 항상 지원하고, active는 `_resolve_active_channel()`이 호출자가 명시적으로 넘긴 `--profiles` 파일에서 `--channel-id` 항목을 찾은 경우에만 그 channel의 completion_profile/adapter_id/adapter_sha256/receipt_sha256을 completion_profile_receipt로 고정해 수용하며(135 W-4, H-4 — profiles.json 자체 생성·channel 자동 승격은 하지 않는다), 그 외(미지정 `--profiles`·미승인 channel)는 여전히 profile_not_found로 거부한다. _cmd_init_run_log()가 outbox 2단 원자 쓰기(_atomic_write_state_json, pending→기록 코어 init/append lock_held=True 호출→active)로 state.json schema_version 1.2 + run_log 블록과 첫 run.started 사건을 만든다. `_check_active_completion_evidence()`(135 W-4, CONTRACT §1.5)는 cmd_mark가 완료(--done, --step 최종 단계 포함) 전이를 시도할 때 row 주소 해석보다 먼저 실행되어, active mode + completion_profile≠cooperative인 run에 trusted terminal 사건 정확히 1건(그리고 observed_trajectory면 PM이 아닌 actor의 trusted activity 1건 이상)이 없으면 `completion_evidence_missing`으로 거부하고 state.json을 손대지 않는다. `verify --run-log-completeness-check`(135 W-4, CONTRACT §1.4/§1.5, 7번째 상호 배타 라우트)는 `_run_log_completeness_check()`로 state.json rows와 조각(committed)·보관함(pending) 사건을 대조해 `missing_state_changed`/`missing_pm_activity`/`missing_gate_event`/`unobserved_worker_boundary` 4종 누락 목록과, committed+pending 전 구간에서 조회하는 `last_observed_decision`/`last_observed_state_change`/`last_observed_boundary` 3필드(`{event_id, ts, ref}` 또는 None)를 항상 반환한다 — 구조 검증(run-log-tool validate-run)과 별개 축이며 read-only·비차단(exit 0)이다. `missing_pm_activity`는 CONTRACT §2.5 트리거 조문의 상태 앵커 2종(① `status=done` ∧ `owner=auto` ∧ `key` 보유 행에 `task_step` 일치 PM activity(decision)가 없으면 행마다 1건을 row_id 오름차순으로, ② `run_log.status=overridden`인데 run 전역에 PM activity(decision)가 0건이면 배열 마지막에 1건)을 committed+pending 합집합 사건과 대조해 채우며, 항목은 `row_id`·`row_key`·`stage`·`expected`·`anchor` 5키 고정이다(137 W-5). --run-log-mode 미지정 경로는 기존 save_state_json()을 그대로 타 바이트 동일성을 유지한다(D-L, C-3). _atomic_write_state_json()은 tmp→fsync→os.replace 원자 쓰기이며, run_log.pending_events가 있으면 쓰기 직전 기록 코어의 redact() 초크포인트를 통과시킨다(D-9, GC-001). _import_run_log_core()는 importlib.util.spec_from_file_location으로 기록 코어를 sys.path 오염 없이 단일 모듈 적재한다(GC-007) — 형제 배치 우선, 없으면 배포본(_run_log_core_dir(), D-C). RUN_LOG_STATE_ERROR_CODES는 run-log 계열 상태 도구 오류 코드(profile_not_found/run_log_missing/run_log_pending/run_log_outbox_full/run_log_write_failed/event_too_large) 전용 별도 테이블이며 ERROR_CODES 딕셔너리 리터럴과 물리 분리된다(D-A, F-6) — err()의 _error_template()가 ERROR_CODES→RUN_LOG_STATE_ERROR_CODES→DESIGN_GATE_ERROR_CODES 순으로 조회만 하고, 세 테이블 모두에 없는 코드는 .format() 호출 없이 code 문자열 그대로를 메시지로 쓴다(GC-008). run_log_commit()이 advance/mark/block/add-row/status의 상태 변경과 state.changed 적재(단일 event 또는 event list, build_state_changed_event, 조합 A7·event_id 사전 확정)를 한 번의 원자 쓰기로 커밋한 뒤 _run_log_drain()의 멱등 append와 보관함 비우기로 잇는다(CONTRACT §1.4, TRD D-2, D-3) — advance/mark는 auto_approve_prior_user_confirmations()가 자동 승인한 각 사용자 확인 행과 대상 행 전이를 각각 독립 state.changed로 만들어 event list로 넘기며, 리스트 admission은 순서대로 전부 통과해야만 보관함에 반영되는 전부-아니면-전무다(H-1) — append가 실패해도 상태 전이는 이미 커밋돼 교착되지 않고 응답 warnings에 run_log_pending만 실린다. run_log_outbox_admit()은 항목당 4 KiB·전체 128건(최악 512 KiB) 상한을 집행하며 일반 한도는 128 − 보관함 override 사건 수이고, 위반 시 각각 event_too_large·run_log_outbox_full로 전이를 시작하지 않는다. _run_log_drain()은 완전한 사건만 순서대로 재전송하고 첫 실패에서 멈추며 이미 조각에 있는 event_id는 건너뛰고, 보관함에 run.started가 있을 때만 실행 디렉터리·첫 조각을 다시 만든다(복구 가능 초기화). run_log_diagnose()는 validate에 합류해 보관함 잔량을 run_log_pending(recoverable_init 표시)으로, 활성 계약인데 조각·run.started가 없으면 run_log_missing으로 보고하며 스키마를 강등하거나 블록을 지우지 않는다(§1.4, AC-3). run_log 블록이 없는 1.0/1.1 태스크는 run_log_commit()이 곧바로 save_state_json()으로 우회해 산출물·응답 키 집합이 종전과 동일하다(C-3). state.schema.json은 schema_version 1.2와 run_log 블록(필수 7필드·pending_events maxItems 128)을 등재한다. init --actor {coordinator,worker}는 --skill opd/opds에서만 지원되며(그 외 skill과 조합 시 actor_unsupported_for_skill로 exit 1) 지정 시에만 state.json에 actor 키를 조건부 영속화하고, legacy --actor pm은 actor_pm_retired로 거부한다. init --workspace worktree는 --worktree 없이 worktree_path_required, --workspace hub는 oppb에서 workspace_required_for_skill로 기록 전에 거부한다. cmd_advance/cmd_mark는 상태 전이 진입 경계(load_state_json 직후)에서 `_claim_task_lease_if_needed()`를 1회 호출해 공통 resolver로 세션 신원이 해석될 때 `_import_ownership_lease()`(ownership_tool.lease, 형제 배치 우선·sys.path 비오염 패키지 적재)의 claim(claim_source=state_transition — 138 D-21 능동 소유권, claimant_root=os.getcwd() — 150 W-5)으로 `<task>/run/.runtime/owner.json` lease를 원자 생성하거나 기존 session_start lease를 승격한다(138 W-9) — cmd_init은 claim하지 않고, 해석 가능한 세션 신원 부재·적재 실패·타 세션 live lease(foreign_owner)·이관 대기 태스크의 대상 외 루트 재-claim(handoff_pending)은 모두 stderr 경고 1줄만 남긴 채 전이를 그대로 통과시키며(fail-safe) 응답 JSON 키 집합·종료코드·state.json 산출물도 바꾸지 않는다(150 AC-10, C-6). claimant_root 전달로 허브의 재-claim은 이관을 되돌리지 못하고(150 H-2) 워크트리 루트 cwd의 전이는 이관을 소비해 claim에 성공한다(SessionStart 실패 시 자가 치유) — 집행자는 PreToolUse 쓰기 가드 하나이며 state-tool은 판정 지점을 늘리지 않는다. run-log 사건 4개 기록부의 actor.session_id는 `_current_session_id()`(ownership-tool 공통 resolver의 OPAL→Claude→Codex→payload 우선순위, 플랫폼 고유 변수명은 해당 어댑터가 소유 — C-15)로 채워지며 미설정 시 종전과 동일하게 None이다(run-log CONTRACT §58 선택 필드, 스키마 무변경). log-event/gate-request/gate-resolve(135 W-3, CONTRACT §2.4)는 run_log_commit()의 같은 outbox/admission/drain 경로를 재사용해 PM activity·gate.requested·gate.resolved 사건을 기록하며 (actor_not_allowed/schema_invalid/refs_invalid/gate_not_requested/gate_duplicate/task_path_not_absolute를 방출), run_log_core는 호출하지 않아 TRD D-5 단방향 의존을 유지한다. log-event의 --event는 activity와 pm.report 2종을 수용한다(TASK-147 W-5, D-2, §2.4) — stop.decision은 이 표면이 수용하지 않으며 Stop hook receipt의 drain 경로가 조립한다(D-6). _build_pm_report_data()는 _build_pm_activity_data()의 형제 앞단 중복 방어로, --data 원문 JSON이나 --report-type/--transition-action/--user-input-required 인자에서 data 폐쇄 3키를 구성하고 report_type 2종·transition_action 4종 enum과 user_input_required boolean 위반을 schema_invalid로 거부한다 — 두 enum 인자에 argparse choices를 걸지 않는 것은 argparse usage 오류(exit 2)가 기록 코어의 schema_invalid와 갈리면 §1.3이 요구하는 「두 지점의 판정 결과가 항상 일치한다」가 깨지기 때문이다. _PM_REPORT_DATA_KEYS·_PM_REPORT_TYPE_ENUM·_PM_TRANSITION_ACTION_ENUM은 기록 코어 동명 상수의 물리 분리 사본이며 상수를 import하지 않는다(§3.1 단방향 의존). _build_pm_report_event()는 _build_pm_activity_event()의 형제로 조합 A4 pm.report 사건을 조립하고, run_log_commit()은 커밋할 사건 목록에 pm.report가 있으면 admission 전건 통과 직후 같은 원자 쓰기 안에서 state.run_log.last_report 파생 포인터(폐쇄 5키 event_id/report_type/transition_action/user_input_required/at)를 갱신한다(D-7) — admission이 거부되면 err()가 먼저 종료시키므로 사건도 포인터도 남지 않는다(H-2, 사건이 SSOT·포인터는 파생). 포인터에는 summary·reason 같은 자유 서술을 복제하지 않아 §1.3의 원본 프롬프트·비밀값 비저장이 포인터에도 유지된다. state.schema.json의 run_log 블록에는 last_report가 선택 필드로 등재되며 필수 7필드는 불변이다(§1.4). 157 PM 경로 독립 설계 게이트: _is_pm_design_path()가 rows의 key plan.design_gate 존재로만 PM 경로를 판정하고(참이 아니면 아래 가드·기록은 모두 no-op), state.design_gate 블록(status idle/evaluating/pass/fail/retry_limit, iteration, limit=DESIGN_GATE_LIMIT 3, limit_from, task_confirm_req_hash, current_attempt, passed/approved_bundle_hash, last_rewrite_target, history)이 해시·반복을 소유한다. 문서 묶음 hash는 TASK.md/PLAN.md/TEST-SCENARIO.md 파일 sha256의 결정론 결합, TASK 요구 hash는 Constraints·Acceptance criteria 본문 sha256이다. design-gate start는 PM 경로→execute.implement pending(design_gate_locked)→retry_limit→열린 시도(묶음 불변이면 design_gate_attempt_open, 변했으면 superseded로 닫고 진행)→plan.design_gate 앞 행 완료→문서 존재→TASK 요구 hash(task_reconfirm_required)→N=iteration+1→직전 rewrite 대상 불변(rewrite_target_unchanged) 순으로 상태 불변 거부한 뒤 _design_gate_deterministic_check()(TASK 5절, _check_plan_contract 전 항목, strict AC/C Work item 연결, Findings 4소절, 회귀 확인 경로의 변경 대상·직접 변경·문서 갱신 중복, 직접 변경·문서 갱신 경로의 Work item 부재, 미확인 가정 H-N 참조, 형제 test-tool을 sys.executable로 호출한 scenario-coverage-build/check exit 0)를 실행하고, 실패는 deterministic_fail 시도로 기록한 뒤 design_gate_deterministic_fail로, 통과는 status=evaluating·plan.design_gate in_progress·plan.user_confirm pending 복귀·gate.requested(design-gate-i{N})를 한 커밋으로 남긴다. design-gate record는 열린 시도·회차·묶음 불변(design_gate_input_changed) 검사 뒤, --verdict pass|rewrite에 한해 --evaluator-result JSON 최상위 input_bundle_hash·iteration이 현재 열린 시도의 bundle_hash·--iteration과 정확히 같은지 검사하며(ADD-1, 157) 없거나 다르면 design_gate_result_stale로 거부하고 상태를 불변으로 둔다(--verdict input_error는 이 검사에서 제외). 이어서 pass/rewrite의 evaluator 축 계약(design.axes 4키, scenario.scores 3키, pass는 4축 PASS·각 ≥1·평균 ≥1.5를 도구가 재계산)을 거부 시 상태 불변으로 검사하고, pass는 passed_bundle_hash와 plan.design_gate done, 비-pass는 fail(상한 도달 시 retry_limit + await_user/decision_request)과 gate.resolved(data.verdict approved/rejected)를 같은 커밋으로 남긴다. 검사 순서는 열린 시도·회차 → design_gate_input_changed → design_gate_result_stale → design_gate_result_invalid → design_gate_verdict_mismatch다. design-gate reset --owner user만 retry_limit을 해제한다(limit_from=iteration). design-decision은 PM 경로 PLAN 단계에서 detail(STATE.md 결정 로그 + PM activity, continue)과 external(plan.plan_md failed·current_status blocked, decision_request)을 기록한다. apply_pm_design_guards()는 advance/mark의 자동 승인 직후·저장 전 구간에서 확인 행 해시 기록(task.user_confirm→task_confirm_req_hash, plan.user_confirm→통과 hash 일치 시 approved_bundle_hash), 자동 승인 불가 mode의 --owner user 없는 확인 행 거부, plan.design_gate 완료 가드, execute.implement pending 진입 가드(pass·TASK 요구 hash·현재=통과=승인)를 --force 우회 없이 집행한다. advance는 --force(--note 필수)를 받는다. 신규 오류 코드는 ERROR_CODES(키 집합 동결)와 물리 분리된 DESIGN_GATE_ERROR_CODES 15종(design_gate_result_stale 포함)이며 design_gate_retry_limit·task_reconfirm_required는 AWAIT_USER_ERROR_CODES다. 167 advisory 응답 게이트: design-gate record는 refinement가 아닌 회차에서 evaluator 결과 최상위 advisories[](키 부재는 빈 배열, 원소 {id A-N, kind subsumed|mergeable|cheaper_layer|misclassified, targets S-ID ≥1, basis, recommendation})를 _validate_advisories()로 검사해 위반을 design_gate_result_invalid로 거부하고, --advisory-responses 파일([{id, response apply|retain, reason}])을 _load_advisory_responses()로 검사한다 — pass이고 advisories ≥1이면 필수, 그 외에는 선택이며, ID 집합 불일치·중복·공백 사유 retain·advisories 없는데 응답 존재는 advisory_response_invalid로 상태 불변 거부한다(검사 순서는 기존 design_gate_verdict_mismatch 뒤). 응답에 apply가 1건 이상이면 pass를 history verdict rewrite·reason advisory_apply·advisory_responses로 기록하고(--rewrite-target 필수, 없으면 design_gate_result_invalid) status fail·design_gate.refinement_pending=true로 둔다. 다음 start는 refinement_pending이면 current_attempt와 응답에 refinement: true를 싣는다(평소 false). advisory_apply도 rewrite이므로 다음 start 전에 --rewrite-target 대상 문서를 고쳐야 하며, 고치지 않으면 기존 ⑥ rewrite_target_unchanged로 거부된다. refinement 회차의 record는 advisories를 형식 검사·응답 요구 없이 빈 배열로 기록하며 pass면 refinement_pending=false(ⓐ), 비-pass면 reason advisory_refinement_failed와 retry_limit·await_user·decision_request(ⓑ)로 전이하고, start ⑦ 결정론 실패는 reason 앞에 'advisory_refinement_failed: '를 붙여 같은 retry_limit 전이(ⓒ)를 타며, superseded로 닫힌 refinement 시도는 refinement_pending을 유지한다(ⓓ). apply 회차와 refinement 회차(ⓐ~ⓓ)는 새 상태 값 없이 limit_from을 1 올려 반복 상한 계산에서 제외한다. history verdict는 기존 5값만 쓰고 record 원소에 advisories·advisory_responses·refinement 선택 필드를 더한다. reset은 refinement_pending을 false로 되돌린다. apply_scenario_gate_mark_guard()는 cmd_mark가 key test_scenario.scenario_gate·plan.scenario_gate 행을 미완에서 완료(--done, --step N/N)로 바꿀 때 row 해석 직후·상태 변경 이전에 형제 test-tool scenario-gate-verify --task-folder <task>를 sys.executable subprocess로 호출하고 exit 0이 아니면 scenario_gate_record_required(verify detail.reason·required_action에 scenario-gate-record 재실행 안내)로 state.json 불변 거부한다 — --force·--auto-pass·--as-worker로 우회할 수 없고 이미 완료된 행·다른 key·plan.design_gate에는 적용하지 않는다. advisory_response_invalid·scenario_gate_record_required는 DESIGN_GATE_ERROR_CODES에 추가되어 17종이다(ERROR_CODES 키 집합 동결 유지).",
  "note": "boot-summary는 허브 direct 태스크와 registry 발급 canonical task_path를 통합해 최신 3건, 잔여 건수, bounded 경로 이상을 읽기 전용 JSON으로 반환한다.",
  "exports": [
    "cmd_init", "cmd_show", "cmd_resolve_mode", "cmd_resolve_start", "cmd_advance", "cmd_mark",
    "cmd_block", "cmd_validate", "cmd_add_row", "cmd_status",
    "cmd_run_start", "new_run_id",
    "cmd_spec_validate", "cmd_event_verify", "cmd_gate_pass", "build_todo_mirror",
    "cmd_finalize_attribution", "link_memory_history", "task_root",
    "normalize_stored_mode", "can_auto_approve_user_confirmation",
    "auto_approve_prior_user_confirmations",
    "collect_boot_summary",
    "_collect_plan_target_files", "_check_code_scan_citation",
    "_check_sdlc_v2_task_contract", "_check_plan_contract",
    "_run_code_scan_citation_hook",
    "_cmd_init_run_log", "_atomic_write_state_json",
    "_import_run_log_core", "_run_log_core_dir", "_error_template",
    "run_log_outbox_admit", "save_state_json_atomic", "run_log_commit", "run_log_diagnose",
    "build_state_changed_event", "_run_log_drain", "_run_log_segment_records",
    "_run_log_block", "_run_log_event_bytes", "_run_log_is_override_event",
    "_resolve_sole_terminal_worker_run_id", "_reconcile_worker_duration_minutes",
    "cmd_log_event", "cmd_gate_request", "cmd_gate_resolve",
    "_require_absolute_task_path", "_run_log_all_records",
    "_validate_run_log_refs", "_build_pm_activity_data",
    "_build_pm_activity_event", "_build_pm_report_data",
    "_build_pm_report_event", "_build_gate_event",
    "_resolve_active_channel", "_check_active_completion_evidence",
    "_run_log_completeness_check",
    "_current_session_id", "_ownership_tool_dir", "_import_ownership_lease",
    "_import_ownership_fingerprint", "_claim_task_lease_if_needed",
    "_stop_decision_project_root", "_last_activity_before",
    "_build_stop_decision_event", "_load_pending_stop_decisions",
    "_drain_pending_stop_decisions", "_pending_stop_receipt_count",
    "DESIGN_GATE_ERROR_CODES", "_pilot_dev_pipeline_path", "_is_pm_design_path",
    "apply_pm_design_guards", "apply_scenario_gate_mark_guard",
    "_design_gate_deterministic_check",
    "cmd_design_gate_start", "cmd_design_gate_record", "cmd_design_gate_reset",
    "cmd_design_decision"
  ]
}
"""

# PLAN §2.1 구현 명세 — TASK T-11: 표준 라이브러리만 import
import argparse
import fcntl
import fnmatch
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────────────────────
# 상수 (PLAN §2.2 G-4, §2.18 E-1, §2.13 G-10)
# ─────────────────────────────────────────────────────────────────────────────

STAGE_ENUM = [
    "TASK", "ANALYSIS", "PLAN", "TEST-SCENARIO", "EXECUTE", "TEST",
    "WIREFRAME", "QA", "SPEC", "REVIEW", "DESIGN",
    "VERIFY", "SCAN", "CHECK", "REPORT", "WBS", "CLOSE",
    # 070 R-8: opdd 드리프트 정정 — opal-pilot-data-design 단계 enum 등록(enum 문자열 추가만, pipeline.json은 2차)
    "DICT", "MODEL", "DDL/MIGRATION",
    # 132 W-3: opal-pilot-project-build(oppb) 파일럿 신설 — 프로젝트 단계 enum 등록(additive-only, S-6)
    "P0", "P1", "P2", "P3", "P4", "P5",
]

# 070 F-001 R-1/R-6: pipeline.json 스펙 key 형식 — {stage_slug}.{item_slug}(_N)?
# (TASK.md §확정 방향 §6, PLAN §3.1.2)
KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*(_[0-9]+)?$")


def stage_to_slug(stage: str) -> str:
    """stage enum → slug. 소문자화 + '-'·'/' → '_'. (TASK §6, PLAN §3.1.2)"""
    return stage.lower().replace("-", "_").replace("/", "_")

# semi-agentic 모드 경계 — 이 stage 집합에 속하는 행은 EXECUTE-equivalent 이전으로 간주
# (PLAN-equivalent 단계까지 사용자 검토 강제) — D-DEC-5 (140)
MODE_BOUNDARY_STAGES = {
    "TASK", "ANALYSIS", "PLAN", "TEST-SCENARIO",
    "SPEC", "REVIEW", "DESIGN",
    "WBS", "WIREFRAME",
    # 094 R-11 G-1: opdd 설계 확정 3단계(070에서 STAGE_ENUM에는 등록됐으나
    # 경계 상수 누락 — semi-agentic 기본 모드에서 소유자 미노출 통과 결함)
    "DICT", "MODEL", "DDL/MIGRATION",
}

VALID_MODES = frozenset({"interactive", "semi-agentic", "agentic"})

# 156 DEC-1: 신규 태스크 기본값 표의 기계 사본. 축별 원문은 harness/modes.md(mode)·
# worktree.md(workspace)·actor.md(actor)가 소유한다. 표에 없는 Pilot은 _OTHER 값을 쓴다.
NEW_TASK_DEFAULTS = {
    "opd":  {"mode": "agentic", "workspace": "worktree", "actor": "coordinator"},
    "opds": {"mode": "agentic", "workspace": "worktree", "actor": "coordinator"},
    "oppd": {"mode": "agentic", "workspace": "worktree", "actor": None},
    "oppl": {"mode": "agentic", "workspace": "worktree", "actor": None},
    "oppb": {"mode": "agentic", "workspace": "worktree", "actor": None},
}
NEW_TASK_DEFAULTS_OTHER = {"mode": "semi-agentic", "workspace": "hub", "actor": None}
# actor 축을 지원하는 Pilot(harness/actor.md 지원 Pilot 폐쇄 목록)
ACTOR_SKILLS = frozenset({"opd", "opds"})
# worktree 해제를 허용하지 않는 Pilot(프로젝트 worktree 필수 구조)
WORKSPACE_REQUIRED_SKILLS = frozenset({"oppb"})


def new_task_defaults(skill):
    return NEW_TASK_DEFAULTS.get(skill, NEW_TASK_DEFAULTS_OTHER)


def normalize_stored_mode(mode):
    """Return the safe effective mode and its source for a stored raw value."""
    if isinstance(mode, str) and mode in VALID_MODES:
        return mode, "state", []
    return "interactive", "fail_closed", [{
        "code": "invalid_mode_requires_user",
        "stored_mode": mode,
    }]


# 093 F-003 R-3: '이 사용자 확인 행을 자동 승인해도 되는가' 단일 판정 (PLAN §3.3.2 (1))
def can_auto_approve_user_confirmation(stage, mode, *, include_close_axis=True):
    """R-3 — 사용자 확인 행 자동 승인 가부 단일 판정.

    반환: (allowed: bool, deny_reason: str | None)
      deny_reason ∈ {"close_requires_user", "interactive_requires_user",
                     "semi_agentic_pre_execute", "invalid_mode_requires_user"}

    두 축 합성:
      축1 CLOSE 여부  — interactive/fail-closed만 거부하고, semi-agentic/agentic은 허용
      축2 모드별 경계  — interactive는 전 stage 거부 / semi-agentic은 모드 경계 상수 한정 거부
    CLOSE는 모드 경계 상수에 속하지 않으므로 자율 모드에서 축2와 충돌하지 않는다.

    include_close_axis=False — 축1을 평가하지 않고 축2만 합성한다. cmd_validate 전용
    (H-4): 현행 validate는 CLOSE 축을 갖지 않으므로 CLOSE 행에도 모드 축 판정을 그대로
    적용해야 표 B V-7(CLOSE×interactive → auto_pass_in_interactive_mode)과
    V-8·V-9(CLOSE×semi-agentic/agentic → 위반 없음)가 동시에 성립한다.
    """
    _effective_mode, mode_source, _warnings = normalize_stored_mode(mode)
    if mode_source == "fail_closed":
        return (False, "invalid_mode_requires_user")
    mode = _effective_mode
    if mode == "interactive":
        return (False, "interactive_requires_user")      # 축2-a — stage 무관
    if include_close_axis and stage == "CLOSE":
        return (True, None)                                # 축1 — 자율 모드 CLOSE 진입
    if mode == "semi-agentic" and stage in MODE_BOUNDARY_STAGES:
        return (False, "semi_agentic_pre_execute")       # 축2-b — stage 한정
    return (True, None)                                  # agentic 전 구간 / semi-agentic 경계 밖


STATUS_LABEL_MAP = {
    "pending":     "⬜",
    "in_progress": "🔄",
    "done":        "✅",
    "failed":      "❌",
    "na":          "-",
}
LABEL_STATUS_MAP = {v: k for k, v in STATUS_LABEL_MAP.items()}

# 118 D-4b(AC-4): CLOSE 마지막 행 mark가 확정하는 완료 상태. 귀속(허브 MEMORY
#   history append)이 아직 수행되지 않았음을 뜻하며, merge 확인 뒤
#   `finalize-attribution`이 `done`으로 닫는다.
STATUS_COMPLETED_UNMERGED = "completed_unmerged"

TRANSITION_ACTIONS = frozenset({"continue", "await_user", "blocked", "complete"})
REPORT_TYPES = frozenset({"progress_report", "decision_request"})

# 094 F-003: current_status → 한글 라벨 (cmd_show '- 상태:' 라인 전용 SSOT)
STATUS_TEXT = {
    "in_progress":          "진행 중",
    "done":                 "완료",
    "blocked":              "블로커",
    "additional_work":      "추가작업중",
    "additional_work_done": "추가작업완료",
    STATUS_COMPLETED_UNMERGED: "완료(미귀속)",
}

# 118 D-4b: 이미 `done`으로 기록된 기존 state.json은 그대로 둔다 — 아래 집합은
#   "태스크가 완료 상태인가"를 묻는 소비처가 두 값을 동등하게 보게 하는 SSOT다.
TASK_COMPLETE_STATUSES = {"done", STATUS_COMPLETED_UNMERGED}

# PLAN §2.2 G-4 표준 항목 상수
# 새 표준 행 구조에서는 "작업 / PM Gate / 사용자 확인 / DONE.md 생성"만 사용한다.
#   "QA Gate"/"State Gate"는 deprecated — State Gate는 stage-transition guard(§M-A)로 이전,
#   QA Gate는 PM Gate로 통합됨. 단 in-flight 레거시 state.json 하위호환을 위해 enum에서 즉시
#   제거하지 않고 deprecated 항목으로 남겨둔다(이 상수는 강제 검증에 쓰이지 않는 문서용 SSOT).
STANDARD_ITEMS = {
    "작업", "PM Gate", "사용자 확인", "DONE.md 생성",
}
DEPRECATED_ITEMS = {
    "QA Gate", "State Gate",  # 014 Phase 4 — 신규 생성 권장 안 함, 레거시 허용
}
# gate-pass(deprecated) 전용 4행 패턴 — 레거시 state.json에만 존재.
GATE_PATTERN = ["QA Gate", "State Gate", "PM Gate", "State Gate"]

# PLAN §2.18 에러 코드 카탈로그 23종 SSOT — 라인 53부터
# 모든 error 응답 값은 이 상수의 키를 참조한다. 추가/임의 변형 금지.
ERROR_CODES = {
    "worker_scope_violation":         "워커가 자기 단계({worker_stage}) 외 행(row {row_id}, stage={stage}) 갱신 시도",
    "already_initialized":            "state.json이 이미 존재합니다. --force로 덮어쓰기 가능",
    "date_tool_failed":               "node ~/.opal/tools/date/date.js datetime 호출 실패 — STATE.md 변경 없음(원자성)",
    # 094 R-4/D-2: --import-existing은 저널화로 제거됨 — 파싱 대상(파이프라인 표) 자체가 STATE.md에서 소멸
    "import_existing_removed":
        "--import-existing은 094(STATE.md 저널화)에서 제거되었습니다 — "
        "STATE.md 파이프라인 표가 더 이상 존재하지 않습니다. "
        "행 구성은 --rows-from <pipeline.json> 또는 --rows-spec을 사용하세요.",
    "invalid_status_transition":      "current_status 전이 그래프(§2.11 G-7) 위반: {from_status} → {to_status}",
    "row_not_found":                  "--row {row_id}에 해당하는 행이 state.json에 없음",
    "invalid_stage_enum":             "--stage {value}는 §2.2 G-3 enum 16종에 없음",
    "gate_pattern_mismatch":          "--start {row} 위치 연속 4행이 [QA Gate, State Gate, PM Gate, State Gate] 패턴과 불일치",
    "gate_stage_mixed":               "gate-pass 4행이 모두 동일 stage가 아님",
    "state_not_initialized":          "state.json이 존재하지 않습니다. state init을 먼저 실행하세요",
    "state_json_malformed":           "state.json이 유효한 JSON object가 아닙니다",
    "user_confirmation_owner_mismatch": "사용자 확인 행(row {row_id})이 done이지만 owner가 user/auto가 아님",
    "owner_flag_conflict":            "--owner와 --auto-pass는 동시 사용 불가",
    "auto_pass_in_interactive_mode":  "interactive 모드에서 사용자 확인 행(row {row_id})이 owner=auto로 done 처리됨",
    "close_gate_violation":           "CLOSE 단계 첫 행 진입 — 직전 단계 사용자 확인 행이 owner=user/status=done이 아님",
    "agentic_close_gate_requires_user": "agentic/semi-agentic 모드 CLOSE 첫 행에 --auto-pass 사용 불가 (§2.16 G-13)",
    "semi_agentic_pre_execute_auto_pass_denied":
        "semi-agentic 모드에서 EXECUTE-equivalent 단계 이전 행(row {row_id}, stage={stage})에 --auto-pass 사용 불가 — PLAN-equivalent까지 사용자 검토 필수",
    "mode_flag_conflict":
        "다중 모드 플래그 동시 사용 — --interactive/--semi-agentic/--agentic 중 하나만 사용 가능",
    "note_required_for_force":        "--force 사용 시 --note 필수 (트리거 §2.17 #1/#3/#8)",
    "rows_spec_invalid_json":         "--rows-spec 인자가 유효한 JSON 배열이 아님",
    "skill_md_parse_error":           "--rows-from SKILL.md에서 행 추출 실패: {reason}",
    "task_path_not_found":            "<task-path> 디렉토리가 존재하지 않음: {path}",
    # 118 D-4b(AC-4): finalize-attribution — allocator_root는 명시 인자 전용이며 추론하지 않는다
    "allocator_root_required":
        "finalize-attribution에는 --allocator-root <절대경로>가 필수입니다 — "
        "cwd·task path 조상·'.opal-worktrees' 문자열로 추론하지 않습니다 "
        "(worktree.md §task root와 allocator root 계약). "
        "worktree-tool create가 발급한 allocator_root 값을 그대로 전달하세요",
    "allocator_root_not_absolute":
        "--allocator-root는 절대경로여야 합니다 (추론·상대해석 금지): {path}",
    "allocator_root_invalid":
        "--allocator-root에 .opal/MEMORY.json이 없습니다: {path}",
    "finalize_attribution_failed":
        "귀속 history append 실패: {detail}",
    "worker_stage_required":          "--as-worker 사용 시 --worker-stage 필수",
    "rows_input_conflict":            "--rows-spec과 --rows-from은 동시 사용 불가",
    "rows_acts_not_implemented":      "--rows-acts는 본 태스크 범위 밖 (시그니처만 정의 — R-13)",
    "mock_in_scenario":               "TEST-SCENARIO.md에 mock 코드 패턴 발견 — 헌법 §4 'Don't fake it' 위반: {lines}",
    "evidence_missing":               "TEST-SCENARIO.md Pass 시나리오에 실행 증거 누락 — 헌법 §4 'Completion requires evidence' 위반: {lines}",
    "stage_transition_violation":     "단계 건너뛰기 차단: 행 {row_id} 갱신 전에 앞 행 {incomplete_rows}이(가) 완료되지 않았음 (PLAN §M-A stage-transition guard)",
    "red_evidence_missing":           "RED 증거(실패 출력) 누락 — GREEN/EXECUTE 진입 차단: {detail}",
    "test_modified_in_fix":           "fix 루핑 중 RED 테스트 파일 수정 거부: {files}",
    "clarification_gate_unmet":
        "TASK 4요소(목표/범위/제약/완료기준) 미잠금 — 다음 단계 진입 거부 (PRINCIPLES §1 집행): {missing}",
    # 070 F-001 R-1/R-6: pipeline.json 스펙 로딩/검증 (PLAN §3.1.2)
    "spec_file_not_found":            "pipeline.json 스펙 파일 없음: {path}",
    "spec_invalid_json":              "pipeline.json JSON 파싱 실패: {detail}",
    "spec_validation_failed":         "pipeline.json 스펙 검증 실패: {detail}",
    # 070 F-003 R-4: task-step 주소 해석 (PLAN §3.3.2)
    "task_step_addr_required":        "행 주소 미지정 — {flags} 중 하나 필요",
    "task_step_addr_conflict":        "행 주소 플래그 2개 이상 동시 사용 — {flags} 중 하나만 사용",
    "task_step_not_found":            "{flag} {key}에 해당하는 행이 state.json에 없음",
    # 070 F-004 R-9: add-row --key (PLAN §3.4.2)
    "task_step_key_invalid":          r"key {key} 형식 위반 — 패턴 ^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*(_[0-9]+)?$",
    "task_step_key_duplicate":        "key {key} 중복 — 파일 내 유일해야 함",
    # 091 F-004 R-10/R-11: task_steps[].gate 스펙 검사 + mark 게이트 집행 (PLAN §3.4.2)
    "gate_artifact_missing":          "PM Gate 산출물 미충족 — 행 {row_id}({key}) 게이트 아티팩트 부재: {missing}",
    "spec_gate_type_invalid":         "task_steps[].gate가 object가 아님: {detail}",
    "spec_gate_missing_field":        "task_steps[].gate 필수 필드 누락: {detail}",
    "spec_gate_field_type_invalid":   "task_steps[].gate 필드 타입 오류(문자열 배열 필요): {detail}",
    "spec_gate_checklist_empty":      "task_steps[].gate.checklist가 비어 있음: {detail}",
    # 093 F-004 R-4: 자동 승인 불가 구간 — 캡틴 승인 필요 (PLAN §3.4.2)
    "user_confirmation_required":
        "자동 승인 불가 — 사용자 확인 행(row {row_id}, stage={stage})에 캡틴 승인이 필요합니다"
        " (사유: {reason}). 보고 → 캡틴 승인 → mark --done --owner user",
    # 098 F-003 R-4: 근거 등급 확정/미확정 판정 게이트 (PLAN §3.3.2)
    "evidence_check_flag_conflict":
        "--evidence-check와 --clarification-check는 동시 사용 불가 (무성 무시 방지)",
    # 106 F-004 R-4: code-scan 결과 인용 게이트 (PLAN §3.4.2 (4))
    "code_scan_citation_unmet":
        "PLAN.md에 code-scan 결과 인용 없음 — EXECUTE 진입 차단 (pm-review-gate.md 항목 14): {missing}",
    # 111 W-1: sdlc-v2 PLAN Work items 실행 계약 검증
    "plan_contract_unmet":
        "PLAN.md Work items 실행 계약 위반 — PLAN 단계 완료/EXECUTE 진입 거부: {violations}",
    # 122 W-2: --actor pm은 --skill opd/opds에서만 지원 (PLAN D-4/AC-1, PM 승인)
    "actor_unsupported_for_skill":
        "actor 축(--pm/--no-pm, --actor)은 opd/opds에서만 지원됩니다 — {skill}은 지원되지 않습니다",
    # 156 DEC-3/DEC-4/DEC-8: 세 축 resolver와 init workspace 게이트
    "workspace_flag_conflict":
        "--wt(--worktree)와 --no-wt는 동시에 사용할 수 없습니다",
    "actor_flag_conflict":
        "--pm과 --no-pm은 동시에 사용할 수 없습니다",
    "workspace_required_for_skill":
        "{skill}은 프로젝트 worktree가 필수입니다 — 허브 작업본(--no-wt, --workspace hub)을 쓸 수 없습니다",
    "resume_axis_locked":
        "기존 태스크 재개 중에는 {axis} 축을 바꿀 수 없습니다 (저장값 {stored}, 요청 {requested})",
    "actor_pm_retired":
        "--actor pm(PM 직접 수행)은 신규 태스크에 더 이상 쓰지 않습니다 — --actor coordinator 또는 worker를 사용하세요. legacy pm 태스크는 재개만 지원됩니다",
    "worktree_path_required":
        "--workspace worktree에는 --worktree <worktree_root 절대경로>가 필요합니다 — worktree 생성에 실패했다면 허브로 폴백하지 말고 중단하세요",
}

# ─────────────────────────────────────────────────────────────────────────────
# 경고 카탈로그 (103 R-21) — ERROR_CODES와 별개 사전이다.
#   경고는 에러가 아니다: exit 0을 유지하고 err()를 타지 않으며 상태 변경을 막지도
#   않는다. ERROR_CODES에 넣지 않는 이유는 두 가지다 — (1) err()는 sys.exit()로
#   끝나므로 카탈로그를 공유하면 "경고인데 차단"이라는 오용 경로가 생긴다,
#   (2) ERROR_CODES 키 집합은 회귀 테스트(TestErrorCodesCompleteness / S-40)가
#   HEAD와 대조해 고정하고 있어 종수를 늘리면 계약이 깨진다.
# ─────────────────────────────────────────────────────────────────────────────
WARNING_CODES = {
    "worker_duration_missing":
        "워커를 디스패치한 행(row {row_id}, stage={stage})을 완료 처리하면서 "
        "--worker-duration-minutes를 넘기지 않았습니다. 워커 완료 알림의 duration_ms는 "
        "세션과 함께 사라지고 행에는 완료 시각만 남아 시작 시각을 되살릴 수 없으므로, "
        "지금 적지 않으면 이 소요는 영구히 소실되고 통계에서 PM 몫으로 잘못 귀속됩니다 "
        "— 소급 복구 경로가 없습니다. 알림에 실린 duration_ms를 분으로 환산해 "
        "`--worker-duration-minutes <분>`으로 다시 mark하거나, 실제로 알 수 없는 경우"
        "(중단된 워커·PM 직접 수행·소급 불가 과거 데이터)라면 "
        "`--worker-duration-unknown`으로 미측정임을 명시하십시오.",
    # W-7 (PLAN D-P8, CONTRACT §2.5 시간 절): 1.2 태스크에서 명시값이 파생값과
    #   일치해 수용은 됐으나, 다음부터는 인자 없이 mark만 호출해도 W-6 코어 조회로
    #   자동 기록되므로 이 인자는 폐기 예정임을 알린다. 에러가 아니라 경고이므로
    #   ERROR_CODES/RUN_LOG_STATE_ERROR_CODES가 아니라 WARNING_CODES에 둔다.
    "worker_duration_minutes_deprecated":
        "--worker-duration-minutes {minutes}가 파생값과 일치해 수용됐습니다. 이 인자는 "
        "폐기 예정입니다 — 1.2 태스크는 워커 종료 사건에서 W-6 코어가 파생한 분값을 "
        "mark가 자동으로 기록하므로, 다음부터는 인자 없이 mark만 호출하십시오.",
}

# ─────────────────────────────────────────────────────────────────────────────
# run-log 계열 상태 도구 전용 오류 코드 (T02 워킹 스켈레톤, PLAN D-A)
#   ERROR_CODES 딕셔너리 리터럴과 물리적으로 분리한 별도 테이블이다 — 동결 테스트
#   (TestErrorCodesCompleteness: len(ERROR_CODES)==51, EXPECTED_CODES 일치,
#   README 카탈로그 헤더 수치, S-40 HEAD AST 키 집합 대조)가 ERROR_CODES **키 집합**만
#   보므로 이 테이블에 코드를 더해도 그 4건은 접촉되지 않는다. `err()`의 `_error_template()`
#   조회만 두 테이블을 합성한다. `profile_not_found`는 §3.1이 상태 도구 소유로 규정한
#   의미(profiles.json 배정값 판정)이므로 `run_log_core.RUN_LOG_ERROR_CODES`가 아니라
#   여기 둔다(T02 QA-SPEC F-6).
# ─────────────────────────────────────────────────────────────────────────────
RUN_LOG_STATE_ERROR_CODES = {
    "profile_not_found":
        "--run-log-mode active는 배포된 profiles.json에 --channel-id 항목이 필요합니다: {channel_id}",
    # T05 보관함·복구 (CONTRACT §2.2) — 상태 도구 표면에서 발생하는 run-log 계열 코드.
    "run_log_missing":
        "활성 로그 계약인데 기록 또는 필수 사건이 없습니다(legacy 강등 없음): {detail}",
    "run_log_pending":
        "보관함 사건 {count}건이 아직 표준 로그에 반영되지 않았습니다(한도 내 진행은 허용).",
    "run_log_outbox_full":
        "미전송 사건 보관함이 상한에 도달했습니다(pending={pending}, limit={limit}) — reconcile 또는 1회 override 외 전이가 차단됩니다.",
    "run_log_write_failed":
        "기록 append에 실패했습니다: {detail}",
    "event_too_large":
        "사건이 보관함 항목 상한을 초과했습니다({bytes}B > {limit}B) — 증거는 별도 파일로 분리하고 항목에는 경로·SHA-256만 넣으십시오.",
    # 135 W-4 (CONTRACT §1.5/§4.2) — active completion 등급이 요구하는 기계 증거 부족.
    "completion_evidence_missing":
        "active completion profile이 요구하는 trusted 증거가 부족합니다: {reason}",
    # W-7 (PLAN D-P8, CONTRACT §2.5 시간 절/§2.2): 1.2 태스크의 명시 --worker-duration-minutes가
    #   W-6 코어 조회 파생값과 다르면 거부한다. run_log_core.RUN_LOG_ERROR_CODES에도 같은 코드가
    #   있으나 그쪽은 run-log-tool CLI(reconcile-duration) 표면 전용 별도 테이블이다 — 이 항목은
    #   state-tool 표면(mark.completion-gate) 전용이며 물리 분리를 유지한다(D-A).
    "worker_duration_conflict":
        "명시한 --worker-duration-minutes({explicit_minutes}분)가 워커 종료 사건에서 파생된 "
        "분값({derived_minutes}분, worker_run_id={worker_run_id})과 다릅니다 — 파생값을 신뢰해 "
        "거부합니다. 인자 없이 다시 mark하면 파생값이 자동 기록됩니다.",
    # W-3 (135, CONTRACT §2.4 state-tool 신규 3개 서브명령: log-event/gate-request/gate-resolve)
    "task_path_not_absolute":
        "task path는 절대 경로여야 합니다(CONTRACT §3.2 M-2): {path}",
    "task_lock_timeout":
        "배타 락 대기가 상한을 초과했습니다(CONTRACT §2.7 M-4): {path}",
    "actor_not_allowed":
        "이 명령은 PM actor 사건만 기록합니다 — actor.kind={actor_kind}는 허용되지 않습니다.",
    "gate_not_requested":
        "gate_id={gate_id}에 선행 gate.requested가 없습니다.",
    "gate_duplicate":
        "gate_id={gate_id}에 대해 이미 {event} 사건이 기록되어 있습니다(중복).",
    # W-1 blocker(2026-09-16) — 소유자 승인 완료: 절대경로 refs 거부 전용 코드 신설.
    # CONTRACT §2.2 표·surfaces.json state-tool.log-event.err 등재는 W-5의 몫.
    "refs_invalid":
        "refs는 프로젝트 상대 경로만 허용합니다(절대 경로·원문 금지, CONTRACT §1.1): {ref}",
    "schema_invalid":
        "폐쇄형 스키마 위반(CONTRACT §1.1/§1.3): {detail}",
}

# ─────────────────────────────────────────────────────────────────────────────
# 157 설계 게이트 전용 오류 코드 (W-2, PLAN DEC-7~DEC-12, harness/design-gate.md 실패 코드 표)
#   ERROR_CODES 키 집합은 동결 테스트(len==59, EXPECTED_CODES, README 헤더 수치, S-40
#   HEAD 대조)가 고정하므로 RUN_LOG_STATE_ERROR_CODES(D-A) 선례대로 물리 분리한다.
#   `_error_template()`이 ERROR_CODES → RUN_LOG_STATE_ERROR_CODES → 이 테이블 순으로
#   조회한다. `user_confirmation_required`·`stage_transition_violation`은 기존
#   ERROR_CODES 항목을 그대로 재사용한다.
# ─────────────────────────────────────────────────────────────────────────────
DESIGN_GATE_ERROR_CODES = {
    "design_gate_not_applicable":
        "PM 경로(rows에 plan.design_gate 존재) 태스크가 아니라 설계 게이트 명령을 쓸 수 없습니다",
    "design_gate_locked":
        "execute.implement가 pending이 아니라(현재 {status}) 설계 게이트·설계 결정을 다시 열 수 없습니다",
    "design_gate_attempt_open":
        "열린 설계 게이트 시도(i{iteration})가 있습니다 — 먼저 design-gate record로 판정을 기록하세요",
    "design_gate_retry_limit":
        "설계 게이트 반복 상한({limit}회)에 도달했습니다 — 사용자 결정 후 design-gate reset --owner user가 필요합니다",
    "task_reconfirm_required":
        "TASK.md Constraints·Acceptance criteria가 TASK 확인 이후 바뀌었습니다 — TASK 재확인이 필요합니다",
    "design_gate_iteration_invalid":
        "--iteration {iteration}이 허용 회차({expected})가 아닙니다",
    "rewrite_target_unchanged":
        "직전 rewrite 대상({rewrite_target}) 문서가 직전 시도와 같습니다: {unchanged}",
    "design_gate_deterministic_fail":
        "설계 게이트 결정론 검사 실패(i{iteration}): {missing}",
    "design_gate_input_missing":
        "설계 게이트 대상 문서가 없습니다: {missing}",
    "design_gate_input_changed":
        "시도 시작 이후 문서 묶음이 바뀌었습니다 — 다시 start하세요 (현재 {bundle_hash})",
    "design_gate_result_stale":
        "evaluator 결과의 input_bundle_hash·iteration이 현재 열린 시도(hash {bundle_hash}, iteration {iteration})와"
        " 다릅니다(결과: hash {result_input_bundle_hash}, iteration {result_iteration}) —"
        " 최신 문서 묶음으로 evaluator를 다시 호출하세요",
    "design_gate_result_invalid":
        "evaluator 결과가 기록 계약을 충족하지 않습니다: {detail}",
    "design_gate_verdict_mismatch":
        "--verdict pass인데 설계 4축·시나리오 기준 미충족 (FAIL 축 {failed_axes}, 시나리오 평균 {scenario_average})",
    "design_gate_not_passed":
        "설계 게이트가 pass가 아닙니다(현재 {status}) — plan.design_gate 완료·EXECUTE 진입 불가",
    "design_bundle_mismatch":
        "현재 문서 묶음 hash({bundle_hash})가 설계 게이트 통과·승인 hash와 다릅니다 — 재평가·재승인이 필요합니다",
    # 167 — advisory 응답 게이트(설계 경로)와 목표-커버 게이트 행 mark 가드
    "advisory_response_invalid":
        "advisory 응답이 계약을 충족하지 않습니다: {detail}",
    "scenario_gate_record_required":
        "목표-커버 게이트 통과 기록이 없거나 최신이 아닙니다({reason}) — test-tool scenario-gate-record로 회차를 기록한 뒤 다시 mark하세요",
}

# TEST cycle errors are kept separate from the frozen legacy ERROR_CODES catalog.
TEST_CYCLE_ERROR_CODES = {
    "test_change_kind_requires_test": "--test-change-kind is valid only for TEST rows",
    "test_clock_already_open": "TEST interval is already open: {kind}/{id}",
    "test_clock_not_open": "No open TEST interval exists: {kind}/{id}",
}

# ─────────────────────────────────────────────────────────────────────────────
# 보관함 상한 (CONTRACT §1.4) — 항목당 4 KiB · 전체 128건(= 최악 512 KiB).
#   일반 admission 한도는 `TOTAL_LIMIT − (보관함에 있는 override 사건 수)`이며
#   별도 예약 슬롯 자료구조를 두지 않는다.
# ─────────────────────────────────────────────────────────────────────────────
RUN_LOG_OUTBOX_TOTAL_LIMIT = 128
RUN_LOG_OUTBOX_EVENT_MAX_BYTES = 4 * 1024
RUN_LOG_OUTBOX_TOTAL_MAX_BYTES = (
    RUN_LOG_OUTBOX_TOTAL_LIMIT * RUN_LOG_OUTBOX_EVENT_MAX_BYTES)

PIPELINE_MARKER_START = "<!-- pipeline:start -->"
PIPELINE_MARKER_END   = "<!-- pipeline:end -->"

# 094 F-003 (§3.3.2 (1)(2)): 레거시(001~093) STATE.md는 마커+표를 동결 텍스트로
# 보유한다. cmd_show가 그 동결 표를 최신인 양 반환하지 않도록 배너로 명시한다.
LEGACY_FROZEN_BANNER = (
    "> [레거시] 이 태스크의 STATE.md에는 파이프라인 표가 남아 있으나 더 이상 "
    "갱신되지 않는 동결 텍스트입니다. 현황의 SSOT는 state.json이며 아래 렌더가 최신입니다."
)

# current_status 전이 그래프 (PLAN §2.11 G-7)
# 118 D-4b: completed_unmerged는 CLOSE mark가 확정하는 완료 상태이며,
#   귀속(finalize-attribution) 후 done으로 닫힌다.
ALLOWED_TRANSITIONS = {
    "in_progress":          {"done", "blocked", "additional_work",
                             STATUS_COMPLETED_UNMERGED},
    "done":                 {"additional_work", "blocked"},
    "blocked":              {"in_progress", "done", "additional_work", STATUS_COMPLETED_UNMERGED},
    "additional_work":      {"additional_work_done", "blocked", "in_progress"},
    "additional_work_done": {"additional_work", "blocked"},
    STATUS_COMPLETED_UNMERGED: {"done", "additional_work", "blocked"},
}

# ─────────────────────────────────────────────────────────────────────────────
# 응답 헬퍼 (PLAN §2.1, D-11 패턴 차용)
# ─────────────────────────────────────────────────────────────────────────────

AWAIT_USER_ERROR_CODES = frozenset({
    "close_gate_violation",
    "agentic_close_gate_requires_user",
    "user_confirmation_required",
    "semi_agentic_pre_execute_auto_pass_denied",
    # 157 W-2: 설계 게이트 반복 상한·TASK 재확인은 사용자 대기다(DEC-9, DEC-11).
    "design_gate_retry_limit",
    "task_reconfirm_required",
})


def _is_close_final_row(row, state):
    """Task 136: 명시 final row에서만 CLOSE 완료를 확정한다.

    신규 pipeline은 close.final key를 사용한다. close.final이 없는 in-flight legacy
    pipeline은 기존 단일 CLOSE 마지막 행 계약을 유지한다.
    """
    if row.get("stage") != "CLOSE":
        return False
    if row.get("key") == "close.final":
        return True
    has_explicit_final = any(
        r.get("stage") == "CLOSE" and r.get("key") == "close.final"
        for r in state.get("rows", [])
    )
    if has_explicit_final:
        return False
    return (
        row.get("stage") == "CLOSE" and
        all(r.get("stage") != "CLOSE" for r in state.get("rows", [])[row["row_id"]:])
    )


def _transition_from_state(state):
    """Return (transition_action, report_type, next_action) for the current frontier."""
    current_status = state.get("current_status")
    next_action = state.get("next_action") or _derive_next_action(state)
    if current_status == "blocked":
        return "blocked", "decision_request", next_action
    if current_status in TASK_COMPLETE_STATUSES:
        return "complete", "progress_report", next_action

    mode = state.get("mode")
    rows = state.get("rows", [])
    for idx, row in enumerate(rows):
        if row.get("status") in _COMPLETE_STATUSES:
            continue
        if row.get("status") == "failed":
            return "blocked", "decision_request", next_action
        if row.get("item") == "사용자 확인":
            allowed, _ = can_auto_approve_user_confirmation(row.get("stage"), mode)
            if allowed:
                continue
            return "await_user", "decision_request", next_action
        if row.get("stage") == "CLOSE":
            first_close = idx == 0 or rows[idx - 1].get("stage") != "CLOSE"
            if first_close:
                allowed, _ = can_auto_approve_user_confirmation("CLOSE", mode)
                if not allowed:
                    return "await_user", "decision_request", next_action
        return "continue", "progress_report", next_action

    return "complete", "progress_report", next_action


def _transition_from_error(payload):
    code = payload.get("error")
    if code in AWAIT_USER_ERROR_CODES:
        return "await_user", "decision_request"
    return "blocked", "decision_request"


def _state_supports_transition_output(state):
    if state.get("current_status") in {"blocked", *TASK_COMPLETE_STATUSES}:
        return True
    return any(
        row.get("key") or row.get("item") == "사용자 확인"
        for row in state.get("rows", [])
    )


def _with_transition_fields(payload):
    """Add Task 136 transition fields without changing the single-line JSON contract."""
    if pathlib.Path(sys.argv[0]).name != "state_tool.py":
        payload.pop("_transition_state", None)
        return payload
    if payload.get("transition_action") not in TRANSITION_ACTIONS:
        state = payload.get("_transition_state")
        if isinstance(state, dict):
            if not _state_supports_transition_output(state):
                payload.pop("_transition_state", None)
                return payload
            action, report_type, next_action = _transition_from_state(state)
            payload.setdefault("transition_action", action)
            payload.setdefault("report_type", report_type)
            payload.setdefault("next_action", next_action)
        elif payload.get("ok") is False:
            action, report_type = _transition_from_error(payload)
            payload.setdefault("transition_action", action)
            payload.setdefault("report_type", report_type)
            payload.setdefault(
                "next_action",
                payload.get("required_action") or payload.get("message") or payload.get("error"),
            )
    if payload.get("transition_action") in TRANSITION_ACTIONS:
        payload.setdefault(
            "report_type",
            "decision_request" if payload["transition_action"] in ("await_user", "blocked")
            else "progress_report",
        )
        payload.setdefault("next_action", payload.get("next_action") or "-")
    payload.pop("_transition_state", None)
    return payload


def ok(command, **kwargs):
    """성공 응답 — 단일 라인 JSON, exit 0"""
    payload = {"ok": True, "command": command, **kwargs}
    print(json.dumps(_with_transition_fields(payload), ensure_ascii=False, default=str))

def _error_template(code):
    """Look up legacy, run-log, design-gate, then TEST-cycle error templates.

    두 테이블에 같은 키가 있으면 `ERROR_CODES`(상태 도구 자기 계약)가 선순위다 —
    이 딕셔너리 리터럴 자체는 어느 경로로도 변경되지 않는다(T02 QA-SPEC F-4).
    두 테이블 모두에 없으면 `None`을 반환한다 — 호출자(`err()`)가 이 미등록
    신호로 `.format()` 호출 자체를 건너뛴다(GC-008: 미등록 코드 문자열이
    포맷 문자열로 오인되는 사고를 막는다).
    """
    if code in ERROR_CODES:
        return ERROR_CODES[code]
    if code in RUN_LOG_STATE_ERROR_CODES:
        return RUN_LOG_STATE_ERROR_CODES[code]
    if code in DESIGN_GATE_ERROR_CODES:
        return DESIGN_GATE_ERROR_CODES[code]
    if code in TEST_CYCLE_ERROR_CODES:
        return TEST_CYCLE_ERROR_CODES[code]
    return None

def err(command, code, message=None, exit_code=1, **kwargs):
    """에러 응답 — 단일 라인 JSON, exit {exit_code}
    code는 ERROR_CODES 또는 RUN_LOG_STATE_ERROR_CODES 키 중 하나여야 한다 (§2.18 SSOT + D-A).
    추가 필드(kwargs)로 에러 컨텍스트(row_id, stage 등)를 포함한다.
    """
    if message is None:
        template = _error_template(code)
        if template is None:
            # 미등록 코드 — code 문자열 자체를 메시지로 쓰고 .format()은 건너뛴다(GC-008).
            message = code
        else:
            try:
                message = template.format(**kwargs)
            except (KeyError, IndexError):
                message = template
    payload = {"ok": False, "command": command, "error": code, "message": message}
    payload.update(kwargs)
    print(json.dumps(_with_transition_fields(payload), ensure_ascii=False, default=str))
    sys.exit(exit_code)


def _rl_err(command, code, message=None, exit_code=1, **kwargs):
    """CONTRACT §2.1 공통 응답 봉투 — run-log 계열 전용 **중첩** 오류 객체.

    기존 22종 도구의 평면 봉투(`err()`, `{"ok": false, "error": "<code>", ...}`)와
    의도적으로 다르다 — CONTRACT §2.1은 run-log 계열이 `error.code`/`error.message`/
    `error.detail`로 분리된 객체를 반환하도록 확정했고("기존 도구는 이 형태로
    이전하지 않는다"), 그 경계는 "run-log 계열 신규 표면인가"다(§2.1). 이 함수는
    `log-event`/`gate-request`/`gate-resolve` 3개 신규 표면 전용이며, 기존
    서브커맨드는 여전히 `err()`의 평면 봉투를 그대로 쓴다(C-2 기존 동작 보존).
    """
    if message is None:
        template = _error_template(code)
        if template is None:
            message = code
        else:
            try:
                message = template.format(**kwargs)
            except (KeyError, IndexError):
                message = template
    payload = {"ok": False, "command": command,
               "error": {"code": code, "message": message, "detail": kwargs}}
    print(json.dumps(payload, ensure_ascii=False, default=str))
    sys.exit(exit_code)

# ─────────────────────────────────────────────────────────────────────────────
# 시점 취득 (PLAN §2.11 G-5, TASK T-5)
# ─────────────────────────────────────────────────────────────────────────────

# 시각 문자열 형식 — 초 해상도가 1순위, 분 해상도가 하위호환 폴백이다 (103 R-19).
TS_PATTERN_SEC = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
TS_PATTERN_MIN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")


def _date_js_path():
    """date.js 실경로 — 형제 배치(`<tools>/date/date.js`) 우선, 없으면 배포본.

    배포 레이아웃(`~/.opal/tools/state-tool/`)에서는 형제 경로가 곧
    `~/.opal/tools/date/date.js`라 종전과 동일하게 해석된다. 레포 소스에서
    직접 실행할 때만 레포의 date.js를 쓰게 되어, 배포 전 검증이 가능하다.
    """
    sibling = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), os.pardir, "date", "date.js")
    sibling = os.path.normpath(sibling)
    if os.path.exists(sibling):
        return sibling
    return os.path.expanduser("~/.opal/tools/date/date.js")


def _run_log_core_dir():
    """run-log-tool 실경로 — 형제 배치(`<tools>/run-log-tool/`) 우선, 없으면 배포본.

    `_date_js_path()`와 동일한 관례다(D-C) — 배포 레이아웃(`~/.opal/tools/state-tool/`)
    에서는 형제 경로가 곧 `~/.opal/tools/run-log-tool`이라 종전과 동일하게 해석되고,
    레포 소스에서 직접 실행할 때만 레포의 run-log-tool을 쓰게 되어 배포 전 검증이
    가능하다.
    """
    sibling = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), os.pardir, "run-log-tool")
    sibling = os.path.normpath(sibling)
    if os.path.isdir(sibling):
        return sibling
    return os.path.expanduser("~/.opal/tools/run-log-tool")


_RUN_LOG_CORE_MODULE_CACHE = {}


def _import_run_log_core():
    """기록 코어를 같은 프로세스에서 단일 모듈로 적재한다 (TRD D-5 인프로세스 호출, D-C).

    하위 프로세스로 호출하지 않는다 — 하위 프로세스는 락을 재획득하려 해 D-4와
    충돌한다(TRD §동시성과 실패 모델). `sys.path`는 건드리지 않는다(GC-007) —
    `sys.path.insert(0, ...)`는 이후 프로세스 전체의 모든 import 탐색 순서를
    오염시켜 무관한 모듈이 이 디렉터리를 먼저 보게 만든다. 대신
    `importlib.util.spec_from_file_location`으로 `run_log_core.py` 파일 하나만
    지정 로드한다 — 디렉터리명에 하이픈이 있어 패키지 import가 불가능한 문제도
    이 방식이 같이 해소한다. 모듈 경로별로 캐시해 같은 프로세스 안 반복 호출이
    매번 다시 적재하지 않게 한다.
    """
    core_dir = _run_log_core_dir()
    module_path = os.path.join(core_dir, "run_log_core.py")
    cached = _RUN_LOG_CORE_MODULE_CACHE.get(module_path)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location("run_log_core", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _RUN_LOG_CORE_MODULE_CACHE[module_path] = module
    return module


# ─────────────────────────────────────────────────────────────────────────────
# 138 W-9 — 세션 소유권 lease 연동 (C-9, AC-12, AC-13, AC-27)
#
# 기존 전이 계약은 무변경이다 — 아래 어떤 실패도 state 갱신을 막지 않고 stderr
# 경고 1줄만 남긴다(fail-safe). 플랫폼 고유 세션 변수명은 ownership-tool의
# 어댑터가 단독 소유하므로(C-15) 이 모듈은 OPAL 중립 변수 하나만 읽는다.
# ─────────────────────────────────────────────────────────────────────────────

def _ownership_warn(code, message):
    """단일 라인 JSON 경고를 stderr로 낸다 (init --rows-from deprecated 경고 선례)."""
    print(json.dumps({"warning": code, "message": message}, ensure_ascii=False),
          file=sys.stderr)


def _current_session_id():
    """공통 ownership resolver로 중립·플랫폼 세션 신원을 해석한다."""
    try:
        return _import_ownership_lease().ownership_core.resolve_session_id(os.environ)
    except (ImportError, OSError, AttributeError) as exc:
        _ownership_warn("ownership_import_failed", str(exc))
        return None


def _ownership_tool_dir():
    """ownership-tool 실경로 — 형제 배치 우선, 없으면 배포본(`_run_log_core_dir()`와 동일 관례, D-C)."""
    sibling = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), os.pardir, "ownership-tool"))
    if os.path.isdir(sibling):
        return sibling
    return os.path.expanduser("~/.opal/tools/ownership-tool")


_OWNERSHIP_LEASE_MODULE_CACHE = {}
_OWNERSHIP_FINGERPRINT_MODULE_CACHE = {}


def _import_ownership_lease():
    """`ownership_tool.lease`를 `sys.path` 오염 없이 적재한다 (GC-007 관례).

    `lease.py`는 `from . import ownership_core` 상대 import를 쓰므로 단일 파일
    적재로는 부족하다 — 패키지 `ownership_tool`을 `submodule_search_locations`와
    함께 먼저 등록한 뒤 하위 모듈을 적재한다. 디렉터리명에 하이픈이 있어 일반
    패키지 import가 불가능한 점도 이 방식이 해소한다. 적재 실패는 호출자가
    예외로 받는다.
    """
    pkg_dir = os.path.join(_ownership_tool_dir(), "ownership_tool")
    cached = _OWNERSHIP_LEASE_MODULE_CACHE.get(pkg_dir)
    if cached is not None:
        return cached
    pkg_spec = importlib.util.spec_from_file_location(
        "ownership_tool", os.path.join(pkg_dir, "__init__.py"),
        submodule_search_locations=[pkg_dir])
    pkg = importlib.util.module_from_spec(pkg_spec)
    sys.modules["ownership_tool"] = pkg
    pkg_spec.loader.exec_module(pkg)
    lease_spec = importlib.util.spec_from_file_location(
        "ownership_tool.lease", os.path.join(pkg_dir, "lease.py"))
    lease = importlib.util.module_from_spec(lease_spec)
    sys.modules["ownership_tool.lease"] = lease
    lease_spec.loader.exec_module(lease)
    _OWNERSHIP_LEASE_MODULE_CACHE[pkg_dir] = lease
    return lease


def _import_ownership_fingerprint():
    """`ownership_tool.fingerprint`를 형제 도구의 모듈 API로 적재한다.

    Stop receipt는 ownership-tool의 런타임 저장소다. state-tool은 그 경로를
    직접 열거나 편집하지 않고, lease 적재와 같은 패키지 적재 경계를 통해 이
    모듈의 ``load_receipt``/``save_receipt`` API만 호출한다(W-7, §3.1).
    """
    pkg_dir = os.path.join(_ownership_tool_dir(), "ownership_tool")
    cached = _OWNERSHIP_FINGERPRINT_MODULE_CACHE.get(pkg_dir)
    if cached is not None:
        return cached

    # 전이 진입 시 lease가 먼저 적재된 경우에는 그 패키지 객체를 재사용한다.
    # 그렇지 않은 경로(log-event/gate 표면)도 독립적으로 동작하도록 패키지를
    # 먼저 등록한다. 이는 _import_ownership_lease()의 hyphen-directory 우회와
    # 같은 관례이며 sys.path를 변경하지 않는다.
    pkg = sys.modules.get("ownership_tool")
    if pkg is None or pkg_dir not in list(getattr(pkg, "__path__", []) or []):
        pkg_spec = importlib.util.spec_from_file_location(
            "ownership_tool", os.path.join(pkg_dir, "__init__.py"),
            submodule_search_locations=[pkg_dir])
        pkg = importlib.util.module_from_spec(pkg_spec)
        sys.modules["ownership_tool"] = pkg
        pkg_spec.loader.exec_module(pkg)

    fingerprint_spec = importlib.util.spec_from_file_location(
        "ownership_tool.fingerprint", os.path.join(pkg_dir, "fingerprint.py"))
    fingerprint = importlib.util.module_from_spec(fingerprint_spec)
    sys.modules["ownership_tool.fingerprint"] = fingerprint
    fingerprint_spec.loader.exec_module(fingerprint)
    _OWNERSHIP_FINGERPRINT_MODULE_CACHE[pkg_dir] = fingerprint
    return fingerprint


def _claim_task_lease_if_needed(task_path):
    """상태 전이 진입 경계에서 이 세션의 task lease를 1회 원자 생성한다 (W-9).

    claim 자체가 멱등이라(같은 세션 재-claim은 heartbeat 갱신) 같은 세션의 반복
    호출은 lease를 새로 만들지 않는다. 다른 세션의 live lease가 있으면 claim은
    `foreign_owner`로 실패하지만 이 역시 전이를 막지 않는다 — 소유권 집행은 stop
    hook 축의 책임이고 state-tool은 기록 축이다.

    claim 주체 루트로 `os.getcwd()`를 넘긴다(150 W-5) — lease가 이관 대기
    (`handoff_pending`)인 태스크는 이 루트가 이관 대상 워크트리 루트와 realpath
    동치이거나 그 하위일 때만 claim이 성립하므로, 허브의 재-claim은 `handoff_pending`
    거부가 되어 이관이 되돌려지지 않고(H-2) 워크트리 cwd의 전이는 SessionStart가
    실패했더라도 이관을 소비해 자가 치유된다. 그 거부는 `foreign_owner`와 **완전히
    동일한** fail-safe 경로로 접혀 stderr 경고 1줄만 남기고 전이를 통과시킨다 —
    응답 JSON 키 집합·종료코드·state.json 산출물은 불변이고(C-6, AC-10) 집행자는
    PreToolUse 쓰기 가드 하나다(state-tool은 판정 지점을 늘리지 않는다).

    반환값은 관측용 dict(`{"claimed": bool, "warning": str|None}`)이며 응답 JSON에
    싣지 않는다 — advance/mark 응답 키 집합을 바꾸지 않기 위해서다(C-3 취지).
    """
    # Distinguish an unavailable ownership module from a genuinely absent
    # session ID.  _current_session_id() is fail-safe and returns None for
    # both, so loading the module first preserves the actionable warning.
    try:
        lease = _import_ownership_lease()
    except Exception as exc:                      # noqa: BLE001 — fail-safe 경계
        warning = "ownership_claim_failed"
        _ownership_warn(warning,
                        f"task lease claim 실패({exc.__class__.__name__}: {exc}). "
                        "상태 전이는 그대로 진행됩니다.")
        return {"claimed": False, "warning": warning}

    session_id = _current_session_id()
    if session_id is None:
        warning = "ownership_session_id_missing"
        _ownership_warn(warning,
                        "해석 가능한 session ID가 없어 task lease를 claim하지 않았습니다. "
                        "상태 전이는 그대로 진행됩니다.")
        return {"claimed": False, "warning": warning}
    try:
        result = lease.claim(str(task_path), session_id=session_id,
                             claim_source="state_transition",
                             claimant_root=os.getcwd())
    except Exception as exc:                      # noqa: BLE001 — fail-safe 경계
        warning = "ownership_claim_failed"
        _ownership_warn(warning,
                        f"task lease claim 실패({exc.__class__.__name__}: {exc}). "
                        "상태 전이는 그대로 진행됩니다.")
        return {"claimed": False, "warning": warning}
    if not isinstance(result, dict) or not result.get("ok"):
        warning = "ownership_claim_skipped"
        diagnostic = result.get("diagnostic") if isinstance(result, dict) else None
        _ownership_warn(warning,
                        f"task lease를 claim하지 않았습니다(diagnostic={diagnostic}). "
                        "상태 전이는 그대로 진행됩니다.")
        return {"claimed": False, "warning": warning, "diagnostic": diagnostic}
    return {"claimed": True, "warning": None}


def _run_date_js(date_js, fmt):
    """date.js 1회 호출 → (returncode, stdout, stderr). 예외는 호출자가 처리한다."""
    result = subprocess.run(
        ["node", date_js, fmt],
        capture_output=True, text=True, timeout=10
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def get_kst_datetime(command="(unknown)"):
    """date.js 호출 → KST `YYYY-MM-DD HH:mm:ss` 반환 (103 R-19).

    `datetime-sec`(초 해상도)를 먼저 요청하고, 응답이 형식에 맞지 않으면
    `datetime`(분 해상도)으로 폴백한다 — date.js가 아직 `datetime-sec`를
    모르는 배포본이면 사용법 안내를 exit 0으로 출력하므로, 반환값 형식 검사가
    지원 여부 판정을 겸한다. 폴백 값은 종전과 바이트 동일한 분 해상도 문자열이며
    스키마·집계 양쪽이 두 형식을 모두 수용한다.

    두 형식 모두 얻지 못하면 date_tool_failed 에러 응답 후 exit 2.
    """
    date_js = _date_js_path()
    try:
        code, out, stderr = _run_date_js(date_js, "datetime-sec")
        if code == 0 and TS_PATTERN_SEC.match(out):
            return out

        code, out, stderr = _run_date_js(date_js, "datetime")
        if code == 0 and TS_PATTERN_MIN.match(out):
            return out

        err(command, "date_tool_failed",
            message=f"exit={code}, stderr={stderr}",
            exit_code=2)
    except Exception as e:
        err(command, "date_tool_failed", message=str(e), exit_code=2)

# ─────────────────────────────────────────────────────────────────────────────
# 파일 I/O 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def resolve_task_path(task_path_str, command):
    """task-path 디렉토리 존재 검증. 미존재 시 task_path_not_found + exit 1."""
    p = pathlib.Path(task_path_str).resolve()
    if not p.is_dir():
        err(command, "task_path_not_found", path=str(p))
    return p


@contextmanager
def state_writer_lock(task_path):
    """Serialize state-tool writers across processes for one task."""
    lock_path = pathlib.Path(task_path) / ".state-tool.lock"
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(lock_path, flags, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)

def load_state_json(task_path, command):
    """state.json 로드. 미존재 시 state_not_initialized + exit 1."""
    state_file = task_path / "state.json"
    if not state_file.exists():
        err(command, "state_not_initialized")
    with open(state_file, encoding="utf-8") as f:
        return json.load(f)

def _atomic_write_state_json(task_path, state):
    """tmp(같은 디렉터리) → fsync → os.replace 원자적 교체 (D-F).

    `opal/tools/memory-tool/memory_tool.py`의 `atomic_write_json()` 선례를 복제한다.
    run-log 초기화 경로(2단 커밋, D-E) 전용이며, 기존 `save_state_json()`은
    그대로 두어 `--run-log-mode` 미지정 경로가 이 함수를 타지 않게 한다(D-L).

    [MUST] `state["run_log"]["pending_events"]`가 있으면 디스크에 쓰기 **직전**
    각 사건을 `run_log_core.redact()`(공통 마스킹 초크포인트, D-9)에 통과시킨다.
    outbox(보관함)도 조각 파일과 동일하게 **원본 writer**이므로 D-9의 "모든 writer가
    공통 경로를 통과한다"가 이 경로에도 적용된다(GC-001) — 이 배치가 호출부에
    있지 않고 함수 안에 있으므로, 앞으로 이 함수를 호출하는 모든 코드가 자동으로
    초크포인트를 탄다(writer별 개별 마스킹 금지, D-9). `redact()`는 멱등이므로
    (이미 통과한 payload를 다시 통과시켜도 결과가 같다) 2단 커밋에서 같은 사건을
    중복 기재해도 안전하다.
    """
    run_log_block = state.get("run_log")
    if run_log_block and run_log_block.get("pending_events"):
        run_log_core = _import_run_log_core()
        run_log_block["pending_events"] = [
            run_log_core.redact(evt) for evt in run_log_block["pending_events"]
        ]

    state_file = pathlib.Path(task_path) / "state.json"
    # GC-101: 예측 가능한 tmp 이름(`state.json.tmp.{pid}`)은 그 이름으로 미리
    # 심볼릭 링크를 심어두는 경합에 노출된다 — 실측 재현: 링크 선점으로 임의
    # 파일을 state JSON으로 덮어쓰는 데 성공했다. `tempfile.mkstemp()`는 같은
    # 디렉터리에 예측 불가능한 이름을 `O_CREAT|O_EXCL`(+플랫폼이 지원하면
    # `O_NOFOLLOW`까지, CPython tempfile이 자동 부여)로 배타 생성해 이름
    # 선점 자체가 통하지 않게 한다. 생성 mode는 0600이며, `os.replace()`가
    # 이 tmp의 inode를 그대로 옮기므로 run-log 경로로 만든 `state.json`은
    # 0600이 된다(GC-004 잔여분) — `save_state_json()`을 쓰는 미지정 경로는
    # 이 함수를 타지 않으므로 그 경로의 기존 권한은 그대로다(D-L/C-3).
    fd, tmp_name = tempfile.mkstemp(
        prefix=f"{state_file.name}.tmp.", dir=str(state_file.parent))
    tmp_path = pathlib.Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(str(tmp_path), str(state_file))
    except Exception:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise


def save_state_json(task_path, state):
    """state.json 저장 (UTF-8, 들여쓰기 2칸).

    [MUST] `state["run_log"]["pending_events"]`가 있으면 쓰기 직전 각 사건을
    `redact()`에 통과시킨다(GC-001 잔여분) — 이 함수는 `_atomic_write_state_json`
    바깥의 여러 호출부(advance/mark/block/add-row/status 등)에서도 쓰이므로,
    shadow init 뒤 이 경로로 state.json이 다시 기록되는 모든 경우에 초크포인트를
    태워야 outbox 사건이 마스킹 없이 남는 경로가 없어진다. `run_log` 블록
    자체가 없으면(= `--run-log-mode` 미지정 태스크) 기록 코어를 **import조차
    하지 않고** 기존 경로와 완전히 동일하게 동작한다 — S-2 바이트 동일성(C-3)을
    지키기 위한 조건부 격리이며, 이 조건이 없으면 미지정 경로도 이 함수를
    타는 이상 매 호출마다 불필요한 import·분기가 끼어든다.
    """
    run_log_block = state.get("run_log")
    if run_log_block and run_log_block.get("pending_events"):
        run_log_core = _import_run_log_core()
        run_log_block["pending_events"] = [
            run_log_core.redact(evt) for evt in run_log_block["pending_events"]
        ]
    state_file = task_path / "state.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")


def save_state_json_atomic(task_path, state):
    """Atomically replace state.json after flushing the complete new payload."""
    state_file = task_path / "state.json"
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=str(task_path),
            prefix=".state.json.", suffix=".tmp", delete=False,
        ) as temp_file:
            temp_name = temp_file.name
            json.dump(state, temp_file, ensure_ascii=False, indent=2)
            temp_file.write("\n")
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_name, state_file)
        temp_name = None
    finally:
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass

# ─────────────────────────────────────────────────────────────────────────────
# 미전송 사건 보관함(outbox)·복구 — CONTRACT §1.4 / TRD D-2 (T05)
#   상태 원천이 기록 실패를 견디게 하는 계층이다. 상태 변경과 사건 적재를 한 번의
#   원자 쓰기로 커밋(①)한 뒤, 기록 코어의 멱등 append(②)와 보관함 비우기(③)로
#   잇는다. ②가 실패해도 ①은 이미 디스크에 있으므로 상태 전이가 기록 장애로
#   교착되지 않는다(제안서 §11 R-6).
# ─────────────────────────────────────────────────────────────────────────────

_RUN_LOG_RUN_ID_PATTERN = re.compile(r"^run_[A-Za-z0-9_-]+$")


def _run_log_block(state):
    """state의 로그 계약 블록(dict) 또는 None. None이면 1.0/1.1 태스크다(C-3)."""
    block = state.get("run_log") if isinstance(state, dict) else None
    return block if isinstance(block, dict) else None


def _run_log_event_bytes(event):
    """보관함 항목의 UTF-8 직렬화 바이트 수 — 상한 판정의 유일한 척도(§1.4)."""
    return len(json.dumps(event, ensure_ascii=False, default=str).encode("utf-8"))


def _run_log_is_override_event(event):
    """override bundle 구성원 여부. 일반 admission 한도 계산에서 제외된다(§1.4).

    `TOTAL_LIMIT − (보관함에 있는 override 사건 수)`가 일반 한도이므로, 별도 예약
    슬롯 자료구조를 두지 않고 이 표시만으로 한도를 계산한다. bundle 적재 자체는
    `--run-log-override`(T10 소유 CLI 표면)의 일이며 여기서는 세기만 한다.
    """
    data = event.get("data") if isinstance(event, dict) else None
    return bool(isinstance(data, dict) and data.get("override_bundle"))


def run_log_outbox_admit(block, event):
    """보관함 admission 판정 → (허용 여부, 오류 코드, detail) (§1.4 상한).

    - 항목당 UTF-8 4 KiB 초과: `event_too_large`. 조용한 절단·자동 외부 저장을 하지
      않는다 — 초과분을 별도 파일로 빼는 것은 호출자의 책임이다(§1.4).
    - 일반 한도(`TOTAL_LIMIT − override 수`) 도달 또는 전체 512 KiB 초과:
      `run_log_outbox_full`. 호출자는 전이를 시작하지 않는다(§2.2).
    """
    size = _run_log_event_bytes(event)
    if size > RUN_LOG_OUTBOX_EVENT_MAX_BYTES:
        return False, "event_too_large", {
            "bytes": size, "limit": RUN_LOG_OUTBOX_EVENT_MAX_BYTES}

    pending = list(block.get("pending_events") or [])
    override_count = sum(1 for e in pending if _run_log_is_override_event(e))
    general_limit = RUN_LOG_OUTBOX_TOTAL_LIMIT - override_count
    general_count = len(pending) - override_count
    if not _run_log_is_override_event(event) and general_count >= general_limit:
        return False, "run_log_outbox_full", {
            "pending": len(pending), "limit": general_limit}

    total_bytes = sum(_run_log_event_bytes(e) for e in pending) + size
    if total_bytes > RUN_LOG_OUTBOX_TOTAL_MAX_BYTES:
        return False, "run_log_outbox_full", {
            "bytes": total_bytes, "limit": RUN_LOG_OUTBOX_TOTAL_MAX_BYTES}

    return True, None, {"bytes": size}


def _run_log_segment_records(task_path, run_id):
    """조각을 **읽기 전용**으로 스캔한다 → 레코드 리스트, 조각 부재면 None.

    §3.1은 상태 도구의 조각 **쓰기**를 금지하며 읽기는 금지하지 않는다. 읽는 이유는
    두 가지다 — (a) 보관함 재전송이 이미 기록된 사건을 다시 쓰지 않게 하는 멱등
    판정, (b) 활성 계약인데 기록이 사라졌는지의 진단(§1.4). 어느 쪽도 사건을
    합성하지 않는다.

    `run_id`는 glob 패턴에 그대로 들어가므로 기록 코어와 같은 화이트리스트
    (`run_<영숫자·밑줄·하이픈>`)로 먼저 거른다 — `*` 같은 메타문자가 다른 run의
    조각까지 끌어오는 것을 막는다(GC-003 동형).
    """
    if not isinstance(run_id, str) or not _RUN_LOG_RUN_ID_PATTERN.match(run_id):
        return None
    run_dir = pathlib.Path(task_path) / "run"
    if run_dir.is_symlink() or not run_dir.is_dir():
        return None
    segments = sorted(run_dir.glob(f"run-log-{run_id}-*.jsonl"))
    if not segments:
        return None
    records = []
    for seg in segments:
        try:
            raw = seg.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in raw.splitlines():
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


# W-7 (PLAN D-P8/H-6) — terminal 사건 3종. CONTRACT §1.2 "terminal 공통 조건"의
# 정의와 동일 문자열이며, run_log_core._TERMINAL_EVENTS(비공개)를 다시 import하지
# 않고 상태 도구 쪽에 독립 상수로 둔다(D-5 단방향 의존 — 상태 도구가 코어의
# 비공개 심볼에 결합하지 않는다).
_RUN_LOG_TERMINAL_EVENTS = ("worker.completed", "worker.failed", "worker.blocked")


def _resolve_sole_terminal_worker_run_id(task_path, run_id):
    """활성 run의 조각에서 terminal 사건(worker.completed/failed/blocked)의
    `worker_run_id`를 조회한다 (W-7, PLAN.md W-6가 남긴 열린 질문에 대한 구현
    측 판정).

    `surfaces.json`의 `state-tool.mark.completion-gate` 표면에는 `--worker-run-id`
    인자가 없어 `mark`가 어느 워커의 파생값을 볼지 표면 계약만으로는 정할 수
    없다. CONTRACT §1.2 "terminal 공통 조건"이 "같은 worker_run_id에 정확히
    1건"을 보장하므로, 이 run의 조각 전체에서 terminal 사건에 실린 서로 다른
    `worker_run_id`가 **정확히 1개**뿐이면 그 값을 "이 run의 유일한 미해소
    terminal"로 간주해 반환한다(RED 테스트를 작성한 형제 워커가 fixture에서
    가정한 것과 같은 관례).

    0건(아직 워커가 종료 사건을 내지 않음)이거나 2건 이상(서로 다른
    `worker_run_id`가 섞여 있어 이 mark 호출이 가리키는 대상을 표면 계약만으로
    특정할 수 없음)이면 `None`을 반환한다 — 추측해 잘못된 워커의 값을 자동
    기록하지 않고, 호출자가 기존 수동 경로로 폴백하게 한다.
    """
    if not run_id:
        return None
    records = _run_log_segment_records(task_path, run_id) or []
    worker_run_ids = {
        rec.get("worker_run_id") for rec in records
        if isinstance(rec, dict)
        and rec.get("event") in _RUN_LOG_TERMINAL_EVENTS
        and rec.get("worker_run_id")
    }
    if len(worker_run_ids) != 1:
        return None
    return next(iter(worker_run_ids))


def _reconcile_worker_duration_minutes(task_path, state, explicit_minutes, command):
    """W-7 (PLAN D-P8, CONTRACT §2.5 시간 절) — 1.2 태스크에서 W-6 코어 조회
    (`run_log_core.reconcile_duration()`, `_import_run_log_core()` 경로)로 파생
    분값을 읽어 `--worker-duration-minutes` 명시값과 대조한다.

    반환은 `(mark가 행에 기록할 분값, deprecated 경고 dict|None)`이다.

    - `run_log` 블록이 없는 1.0/1.1 태스크는 손대지 않고 명시값을 그대로
      돌려준다 — 산출물·응답 키 집합이 종전과 바이트 동일해야 한다(H-6, S-9).
    - 파생값을 아직 얻을 수 없으면(terminal 미기록·조회 실패·`duration_ms`가
      `duration_unknown_reason` 경로로 `null`) 역시 명시값을 그대로 돌려준다 —
      모르는 것을 추측해 차단하지 않는다(CONTRACT §2.6과 같은 태도).
    - 명시값이 없으면 파생값을 그대로 기록값으로 승격한다(자동 기록, 경고 없음).
    - 명시값과 파생값이 같으면 수용하되 폐기 예정 경고를 함께 반환한다.
    - 명시값과 파생값이 다르면 `worker_duration_conflict`로 **즉시 거부**한다.
      이 함수는 `cmd_mark`가 아직 어떤 상태도 변경하지 않은 시점에서 호출돼야
      한다 — 그래야 거부 시 `state.json`이 손대지지 않은 채로 남는다(S-8③).
    """
    block = _run_log_block(state)
    if block is None:
        return explicit_minutes, None

    run_id = block.get("active_run_id")
    worker_run_id = _resolve_sole_terminal_worker_run_id(task_path, run_id)
    if worker_run_id is None:
        return explicit_minutes, None

    core = _import_run_log_core()
    result = core.reconcile_duration(str(task_path), run_id, worker_run_id)
    if not result.get("ok"):
        return explicit_minutes, None

    derived_minutes = (result.get("data") or {}).get("duration_minutes")
    if derived_minutes is None:
        return explicit_minutes, None

    if explicit_minutes is None:
        return derived_minutes, None

    if explicit_minutes == derived_minutes:
        return explicit_minutes, {
            "code": "worker_duration_minutes_deprecated",
            "message": WARNING_CODES["worker_duration_minutes_deprecated"].format(
                minutes=explicit_minutes),
        }

    err(command, "worker_duration_conflict",
        explicit_minutes=explicit_minutes, derived_minutes=derived_minutes,
        worker_run_id=worker_run_id)


def _run_log_drain(task_path, block, core):
    """보관함을 **순서대로** 재전송한다 → (재전송 건수, 실패 detail 또는 None).

    - 완전한 사건만 그대로 재전송한다. 현재 시각·stdout에서 사건을 합성하지
      않는다(§2.3 `reconcile` 불변식).
    - 첫 실패에서 멈추고 나머지를 보관함에 남긴다 — 건너뛰고 뒤를 먼저 쓰면
      조각의 순서가 보관함 순서와 어긋난다.
    - 이미 조각에 있는 `event_id`는 성공으로 간주하고 건너뛴다(멱등 재전송).
    - 보관함에 `run.started`가 있으면 실행 디렉터리·첫 조각을 다시 만든다 —
      이것이 §1.4의 "복구 가능 초기화"다. 그 근거가 없으면 조각을 만들지 않는다.
      만들면 삭제된 기록이 `run_log_missing` 대신 조용히 재생성된다.
    """
    pending = list(block.get("pending_events") or [])
    if not pending:
        return 0, None

    run_id = block.get("active_run_id")
    drained = 0
    failure = None

    with core.task_lock(str(task_path)) as acquired:
        if not acquired:
            return 0, {"code": "task_lock_timeout", "message": str(task_path)}

        if any(e.get("event") == "run.started" for e in pending):
            init_result = core.init(str(task_path), run_id, lock_held=True)
            if not init_result.get("ok"):
                return 0, init_result.get("error") or {"code": "run_log_write_failed"}

        records = _run_log_segment_records(task_path, run_id) or []
        recorded_ids = {r.get("event_id") for r in records}

        for event in pending:
            if event.get("event_id") in recorded_ids:
                drained += 1
                continue
            result = core.append(str(task_path), run_id, event, lock_held=True)
            if not result.get("ok"):
                failure = result.get("error") or {"code": "run_log_write_failed"}
                break
            drained += 1

    block["pending_events"] = pending[drained:]
    return drained, failure


def build_state_changed_event(state, *, task_id, command, from_status, to_status,
                              row=None, row_key=None, note=None):
    """`state.changed` 1건을 §1.1 필수 필드 전건으로 만든다 (§1.2 추가 조건 포함).

    조합 A7(`actor.kind=tool` + `provenance.type=direct` + `recorded_by.kind=tool`)
    이며 `event_id`를 여기서 사전 확정한다 — 보관함에 적재된 payload와 조각에
    기록되는 payload가 같은 식별자를 갖게 해 재전송이 멱등이 된다(§1.3 A7).
    """
    core = _import_run_log_core()
    block = _run_log_block(state) or {}
    event = {
        "schema_version": "1.0",
        "event_id": core.new_event_id(),
        "request_id": f"req_{uuid.uuid4()}",
        "task_id": task_id,
        "run_id": block.get("active_run_id"),
        "parent_run_id": None,
        "worker_run_id": None,
        "caused_by_event_id": None,
        "stage": (row or {}).get("stage"),
        "task_step": (row or {}).get("key"),
        "work_item": (row or {}).get("item"),
        "gate_id": None,
        "event": "state.changed",
        "actor": {"kind": "tool", "id": "state-tool", "provider": None,
                  "session_id": _current_session_id()},  # 138 W-9
        "provenance": {
            "type": "direct",
            "recorded_by": {"kind": "tool", "id": "state-tool"},
            "worker_log_token_id": None,
            "source": None,
        },
        "summary": f"{command}: {from_status} → {to_status}",
        "reason": None,
        "reason_code": None,
        "duration_ms": None,
        "duration_source": None,
        "duration_unknown_reason": None,
        "refs": None,
        "timestamp": core.utc_now_ms(),
        "data": {
            "from": from_status,
            "to": to_status,
            # §1.2는 state.changed에 data.row_key를 요구한다. key 없는 레거시 구조의
            # 행은 row_id로 폴백해 필수 필드가 null이 되지 않게 한다.
            "row_key": row_key if row_key is not None else (
                (row or {}).get("key")
                or (f"row:{row['row_id']}" if row and row.get("row_id") else None)),
        },
    }
    if note:
        event["data"]["note"] = note
    return event


def run_log_commit(task_path, state, command, event=None):
    """상태 변경 + 보관함 적재를 **한 번의 원자 쓰기**로 커밋한다 (D-2, D-3, §2.5).

    `run_log` 블록이 없는 태스크(1.0/1.1)는 기존 `save_state_json()`을 그대로 타고
    반환도 없다 — 미지정 경로의 산출물·응답 키 집합이 종전과 동일해야 한다(C-3).

    `event`는 단일 이벤트 dict(하위호환) 또는 이벤트 dict의 list를 받는다(D-3).
    list인 경우 `advance`/`mark`가 자동 승인한 각 사용자 확인 행의 `state.changed`와
    대상 행 전이의 `state.changed`를 함께 실어, 여러 상태 변경을 **한 번의
    admission·원자 쓰기**로 커밋한다(H-1) — admission 판정은 순서대로 전부
    통과해야만 `block["pending_events"]`에 반영되며, 도중 하나라도 거부되면
    `err()`가 즉시 종료시켜 그 어떤 이벤트도 보관함에 들어가지 않는다(부분
    admission 불가, S-4).

    순서:
      ① admission 판정(리스트 전원) → 위반이면 `err()`로 전이를 **시작하지 않는다**(state.json 미기록)
      ② `status=pending` + 보관함 일괄 적재 + 상태 변경을 1회 원자 쓰기로 커밋
      ③ 기록 코어 멱등 append(락 보유) — 실패해도 ②는 유지된다(교착 금지)
      ④ 성공분을 보관함에서 비우고 `status`를 확정하는 2차 원자 쓰기

    반환은 `ok()`에 병합할 응답 필드 dict다. append가 실패하면 `warnings`에
    `run_log_pending`을 실어 보내되 exit code는 바꾸지 않는다(§2.2 "한도 내 일반
    진행 허용").
    """
    block = _run_log_block(state)
    if block is None:
        save_state_json(task_path, state)
        return {}

    core = _import_run_log_core()

    # W-7 — Stop hook은 run-log에 직접 쓰지 않고 ownership receipt에 판정만
    # 적재한다. 다음 state-tool 커밋이 그 receipt를 A7 사건으로 중개한다. receipt
    # 항목은 **state outbox 원자 커밋 뒤에만** 제거한다. 따라서 admission 거부나
    # 상태 저장 실패가 나면 다음 전이에서 다시 시도할 증거가 사라지지 않는다.
    stop_decision_events, stop_receipt_token = _load_pending_stop_decisions(task_path, state)
    events = list(stop_decision_events)
    if event is not None:
        events.extend(event if isinstance(event, list) else [event])

    if events:
        # H-1: admission 판정을 working copy(pending 스냅샷 누적)로 전부 통과시킨
        # 뒤에만 block["pending_events"]를 갱신한다 — 전부-아니면-전무.
        _working_pending = list(block.get("pending_events") or [])
        for _ev in events:
            admitted, code, detail = run_log_outbox_admit(
                {**block, "pending_events": _working_pending}, _ev)
            if not admitted:
                err(command, code, **(detail or {}))
            _working_pending = _working_pending + [_ev]
        block["pending_events"] = _working_pending

        # TASK-147 D-7/H-2 — `pm.report` 커밋은 `run_log.last_report` 파생 포인터를
        # **같은 원자 쓰기 안에서** 갱신한다. 위 admission 루프가 하나라도 거부하면
        # `err()`가 이미 프로세스를 끝냈으므로 여기에 닿지 않는다 — 즉 거부된
        # 보고는 사건도 포인터도 남기지 않는다(사건이 SSOT, 포인터는 파생).
        # 포인터에는 §1.4 폐쇄 5키만 싣는다. `summary`·`reason` 같은 자유 서술은
        # 절대 복제하지 않는다 — 그것이 §1.3 "원본 프롬프트·chain-of-thought·
        # 비밀값을 어떤 필드에도 저장하지 않는다"를 포인터에서 지키는 방법이다.
        for _ev in events:
            if _ev.get("event") != "pm.report":
                continue
            _report_data = _ev.get("data") or {}
            block["last_report"] = {
                "event_id": _ev.get("event_id"),
                "report_type": _report_data.get("report_type"),
                "transition_action": _report_data.get("transition_action"),
                "user_input_required": _report_data.get("user_input_required"),
                "at": _ev.get("timestamp"),
            }

    if block.get("pending_events") and block.get("status") != "overridden":
        block["status"] = "pending"
    _atomic_write_state_json(task_path, state)

    # receipt는 outbox에 먼저 영속된 사건의 보조 증거일 뿐이다. 이 제거가 실패해도
    # 상태 전이와 이미 커밋된 보관함을 되돌리지 않는다. 다음 호출에서 receipt가
    # 남아 있음을 stderr 경고로만 드러낸다(fail-safe).
    receipt_failure = _drain_pending_stop_decisions(stop_receipt_token)
    if receipt_failure is not None:
        _ownership_warn(receipt_failure["code"],
                        "stop receipt pending_decisions 제거 실패: "
                        f"{receipt_failure.get('message')}")

    drained, failure = _run_log_drain(task_path, block, core)

    if not block.get("pending_events") and block.get("status") == "pending":
        block["status"] = "active"
    if drained or failure is not None or events:
        _atomic_write_state_json(task_path, state)

    pending_count = len(block.get("pending_events") or [])
    summary = {
        "status": block.get("status"),
        "pending": pending_count,
        "active_run_id": block.get("active_run_id"),
    }
    fields = {"run_log": summary}
    if failure is not None:
        summary["last_error"] = failure.get("code")
        fields["warnings"] = [{
            "code": "run_log_pending",
            "message": RUN_LOG_STATE_ERROR_CODES["run_log_pending"].format(
                count=pending_count),
        }]
    return fields


def run_log_diagnose(task_path, state):
    """로그 계약 블록의 진단 → violations 리스트 (§1.4 계약 무결성 / AC-3).

    **legacy 강등을 하지 않는다.** 활성 계약(블록 보유) 태스크에서 기록이 사라지면
    스키마를 1.1로 되돌리거나 블록을 지우는 대신 `run_log_missing` 위반을 낸다.
    보관함에 `run.started`가 남아 있으면 고장이 아니라 **복구 가능 초기화**이므로
    `run_log_pending`으로만 보고한다.

    읽기 전용이다 — 진단이 상태를 고치지 않는다(복구는 다음 전이의 재전송이 수행).
    """
    block = _run_log_block(state)
    if block is None:
        return []

    violations = []
    pending = list(block.get("pending_events") or [])
    run_id = block.get("active_run_id")

    if pending:
        recoverable_init = any(e.get("event") == "run.started" for e in pending)
        violations.append({
            "code": "run_log_pending",
            "row_id": None,
            "detail": (f"pending_events={len(pending)}, "
                       f"recoverable_init={str(recoverable_init).lower()}"),
        })
        override_count = sum(1 for e in pending if _run_log_is_override_event(e))
        if len(pending) - override_count >= RUN_LOG_OUTBOX_TOTAL_LIMIT - override_count:
            violations.append({
                "code": "run_log_outbox_full",
                "row_id": None,
                "detail": f"pending_events={len(pending)} (limit={RUN_LOG_OUTBOX_TOTAL_LIMIT})",
            })
        return violations

    records = _run_log_segment_records(task_path, run_id)
    if records is None:
        violations.append({
            "code": "run_log_missing",
            "row_id": None,
            "detail": f"run log segments not found for {run_id} (계약 유지, 강등하지 않음)",
        })
    elif not any(r.get("event") == "run.started" for r in records):
        violations.append({
            "code": "run_log_missing",
            "row_id": None,
            "detail": f"run.started not found in segments for {run_id}",
        })
    return violations


# ─────────────────────────────────────────────────────────────────────────────
# W-3 (135, CONTRACT §2.4) — log-event / gate-request / gate-resolve
#   surfaces.json이 선언한 3개 신규 표면. run_log_commit()의 outbox/admission/
#   drain 경로를 그대로 재사용한다 — 별도 기록 경로를 만들지 않는다.
# ─────────────────────────────────────────────────────────────────────────────

_PM_ACTIVITY_KIND_ENUM = {"decision", "validation", "retry", "progress"}

# ── TASK-147 D-2 — `pm.report` data 폐쇄 3키와 값 enum ──
# [MUST] 이 상수들은 기록 코어 `run_log_core._PM_REPORT_DATA_KEYS`·
# `_PM_REPORT_TYPES`·`_PM_TRANSITION_ACTIONS`의 **물리 분리 사본**이다(D-5·§3.1
# 단방향 의존 — 상태 도구는 기록 코어를 `_import_run_log_core()` 경로로만 만지고
# 검증 상수를 import해 결합을 만들지 않는다). 앞단 검증은 같은 규칙의 **중복
# 방어**이며 두 지점의 판정 결과는 항상 일치해야 한다(§1.3, TASK-147.S-6).
_PM_REPORT_DATA_KEYS = {"report_type", "transition_action", "user_input_required"}
_PM_REPORT_TYPE_ENUM = ("progress_report", "decision_request")
_PM_TRANSITION_ACTION_ENUM = ("continue", "await_user", "blocked", "complete")

# CONTRACT §1.4 — `run_log.last_report` 포인터의 폐쇄 5키(D-7).
_RUN_LOG_LAST_REPORT_KEYS = (
    "event_id", "report_type", "transition_action", "user_input_required", "at")


def _require_absolute_task_path(task_path_str, command):
    """CONTRACT §3.2 (M-2) — task path는 절대 경로여야 한다.

    기존 서브커맨드(advance/mark/...)는 `resolve_task_path()`로 상대경로를
    말없이 절대화하는 관례를 그대로 둔다(PRINCIPLES §3 수술적 변경 — 기존 경로
    불변). log-event/gate-request/gate-resolve 3개 신규 표면만 이 계약을
    새로 집행한다.
    """
    p = pathlib.Path(task_path_str)
    if not p.is_absolute():
        _rl_err(command, "task_path_not_absolute", path=task_path_str)
    return resolve_task_path(task_path_str, command)


def _run_log_all_records(task_path, block):
    """이미 조각에 기록된 사건 + 아직 드레인되지 않은 보관함 사건을 합쳐 반환한다.

    gate_id 유일성·선행관계 판정은 조각(진실의 원천)뿐 아니라 아직 드레인되지
    않은 보관함 항목까지 봐야 한다 — 그렇지 않으면 직전 호출이 기록 실패로
    보관함에만 남아 있는 상태에서 같은 gate_id가 중복 승인될 수 있다.
    """
    run_id = block.get("active_run_id")
    committed = _run_log_segment_records(task_path, run_id) or []
    pending = list(block.get("pending_events") or [])
    return committed + pending


def _stop_decision_project_root(task_path):
    """표준 ``<project>/tasks/<task>`` 배치에서 receipt 프로젝트 루트를 얻는다.

    이 함수는 receipt 경로를 만들지 않는다. 경로 계산·읽기·쓰기 모두
    ownership-tool의 fingerprint API가 소유하고, 여기서는 대상 task가 표준
    ``tasks/`` 아래인지 확인하는 데만 쓴다.
    """
    task_dir = pathlib.Path(task_path).resolve()
    if task_dir.parent.name != "tasks":
        return None
    return task_dir.parent.parent


def _timestamp_sort_key(value):
    """UTC 시각의 결정론적 비교 키. 잘못된 값은 판정 후보에서 제외한다."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc).timestamp()


def _last_activity_before(records, decided_at):
    """판정 시각 *직전* 마지막 activity의 event_id를 시각·ID 순으로 고른다."""
    decision_key = _timestamp_sort_key(decided_at)
    if decision_key is None:
        return None
    candidates = []
    for record in records:
        if not isinstance(record, dict) or record.get("event") != "activity":
            continue
        timestamp_key = _timestamp_sort_key(record.get("timestamp"))
        event_id = record.get("event_id")
        if timestamp_key is None or timestamp_key >= decision_key or not isinstance(event_id, str):
            continue
        candidates.append((timestamp_key, event_id))
    return max(candidates)[1] if candidates else None


def _build_stop_decision_event(state, *, task_id, receipt_decision, last_activity_event_id):
    """ownership-tool receipt의 닫힌 판정 축만 A7 ``stop.decision``으로 조립한다.

    receipt의 task_path/decided_at 외 자유 필드, Stop envelope, last assistant
    message는 사건에 옮기지 않는다. ``data`` 6키와 summary는 각각 CONTRACT
    §1.3/§1.3.1의 유일한 저장 후보이며, event/request ID는 같은 사전 확정 값이다.
    """
    core = _import_run_log_core()
    block = _run_log_block(state) or {}
    event_id = core.new_event_id()
    report_event_id = receipt_decision.get("report_event_id")
    data = {
        "decision_kind": receipt_decision.get("decision_kind"),
        "diagnostics": list(receipt_decision.get("diagnostics") or []),
        "block_count": receipt_decision.get("block_count"),
        "claim_source": receipt_decision.get("claim_source"),
        "report_event_id": report_event_id,
        "last_activity_event_id": last_activity_event_id,
    }
    return {
        "schema_version": "1.0",
        "event_id": event_id,
        "request_id": event_id,
        "task_id": task_id,
        "run_id": block.get("active_run_id"),
        "parent_run_id": None,
        "worker_run_id": None,
        "caused_by_event_id": report_event_id,
        "stage": None,
        "task_step": None,
        "work_item": None,
        "gate_id": None,
        "event": "stop.decision",
        "actor": {"kind": "tool", "id": "ownership-tool", "provider": None,
                  "session_id": _current_session_id()},
        "provenance": {
            "type": "direct",
            "recorded_by": {"kind": "tool", "id": "state-tool"},
            "worker_log_token_id": None,
            "source": None,
        },
        "summary": core.render_event_summary("stop.decision", data),
        "reason": None,
        "reason_code": None,
        "duration_ms": None,
        "duration_source": None,
        "duration_unknown_reason": None,
        "refs": None,
        "timestamp": receipt_decision.get("decided_at"),
        "data": data,
    }


def _load_pending_stop_decisions(task_path, state):
    """현재 세션·대상 태스크의 receipt를 API로 읽어 drain 후보를 만든다.

    반환한 receipt token은 state의 첫 원자 커밋 뒤에만 비운다. 따라서 admission이
    거부되거나 state 저장이 실패한 경우 receipt는 증거로 남는다.
    """
    session_id = _current_session_id()
    project_root = _stop_decision_project_root(task_path)
    if session_id is None or project_root is None:
        return [], None
    try:
        fingerprint = _import_ownership_fingerprint()
        receipt = fingerprint.load_receipt(str(project_root), session_id)
    except Exception as exc:  # noqa: BLE001 — receipt 경계는 상태 전이를 막지 않는다.
        _ownership_warn("ownership_stop_receipt_load_failed",
                        f"stop receipt 조회 실패({exc.__class__.__name__}: {exc}).")
        return [], None
    if not isinstance(receipt, dict):
        return [], None

    pending = receipt.get("pending_decisions")
    if not isinstance(pending, list):
        return [], None
    canonical_task_path = pathlib.Path(task_path).resolve()
    selected_indexes = []
    for index, decision in enumerate(pending):
        if not isinstance(decision, dict) or not isinstance(decision.get("task_path"), str):
            continue
        # `/var` → `/private/var`처럼 동등한 task 경로가 표기만 다른 macOS
        # 배치를 수용하되, receipt의 경로는 비교 외 어떤 파일 연산에도 쓰지 않는다.
        try:
            is_target = pathlib.Path(decision["task_path"]).resolve() == canonical_task_path
        except (OSError, RuntimeError):
            is_target = False
        if is_target:
            selected_indexes.append(index)
    if not selected_indexes:
        return [], None

    records = _run_log_all_records(task_path, _run_log_block(state) or {})
    events = []
    admitted_indexes = []
    core = _import_run_log_core()
    for index in selected_indexes:
        decision = pending[index]
        try:
            event = _build_stop_decision_event(
                state, task_id=pathlib.Path(task_path).name,
                receipt_decision=decision,
                last_activity_event_id=_last_activity_before(records, decision.get("decided_at")))
        except (KeyError, TypeError, ValueError):
            # 비정상 receipt를 보관함에 복사하면 원문이 pending_events라는 우회
            # 저장소에 남을 수 있다. receipt는 남기고, 값 자체는 경고에도 싣지 않는다.
            _ownership_warn("ownership_stop_receipt_schema_invalid",
                            "stop receipt 판정이 폐쇄 event 형태로 조립되지 않아 보류했습니다.")
            continue
        if core.validate_event(event) or core.validate_provenance(event):
            _ownership_warn("ownership_stop_receipt_schema_invalid",
                            "stop receipt 판정이 run-log 폐쇄 스키마를 통과하지 않아 보류했습니다.")
            continue
        events.append(event)
        admitted_indexes.append(index)
    if not events:
        return [], None
    return events, {
        "fingerprint": fingerprint,
        "project_root": str(project_root),
        "receipt": receipt,
        "selected_indexes": frozenset(admitted_indexes),
    }


def _drain_pending_stop_decisions(token):
    """state outbox 커밋 뒤 선택한 receipt 항목만 ownership API로 제거한다."""
    if token is None:
        return None
    receipt = dict(token["receipt"])
    pending = receipt.get("pending_decisions") or []
    receipt["pending_decisions"] = [
        decision for index, decision in enumerate(pending)
        if index not in token["selected_indexes"]
    ]
    try:
        result = token["fingerprint"].save_receipt(token["project_root"], receipt)
    except Exception as exc:  # noqa: BLE001 — receipt 경계는 상태 전이를 막지 않는다.
        return {"code": "ownership_stop_receipt_drain_failed",
                "message": f"{exc.__class__.__name__}: {exc}"}
    if not isinstance(result, dict) or not result.get("ok"):
        return {"code": "ownership_stop_receipt_drain_failed",
                "message": (result or {}).get("error") if isinstance(result, dict) else None}
    return None


def _pending_stop_receipt_count(task_path):
    """현재 세션 receipt에서 대상 task의 미커밋 Stop 판정 수를 읽기 전용 조회한다.

    D-14의 ``missing_stop_decision``은 hook 미실행과 receipt에는 있으나 아직
    outbox로 drain되지 않은 경우를 구별해야 한다. receipt 경로를 직접 열지 않고
    W-7과 같은 ownership-tool API만 사용하며, 완전성 진단 자체는 어떤 실패도
    경고·쓰기 없이 빈 값으로 폴백한다.
    """
    session_id = _current_session_id()
    project_root = _stop_decision_project_root(task_path)
    if session_id is None or project_root is None:
        return 0
    try:
        receipt = _import_ownership_fingerprint().load_receipt(
            str(project_root), session_id)
    except Exception:  # noqa: BLE001 — read-only 진단은 항상 비차단이다.
        return 0
    pending = receipt.get("pending_decisions") if isinstance(receipt, dict) else None
    if not isinstance(pending, list):
        return 0
    canonical_task_path = pathlib.Path(task_path).resolve()
    count = 0
    for decision in pending:
        if not isinstance(decision, dict) or not isinstance(decision.get("task_path"), str):
            continue
        try:
            if pathlib.Path(decision["task_path"]).resolve() == canonical_task_path:
                count += 1
        except (OSError, RuntimeError):
            continue
    return count


_RUN_LOG_TERMINAL_EVENTS = ("worker.completed", "worker.failed", "worker.blocked")


def _check_active_completion_evidence(task_path, block, command):
    """135 W-4 (AC-6, C-2, H-4) — active 완료 게이트.

    `completion_profile`이 `cooperative`가 아닌 active run의 완료 전이는
    trusted terminal 사건 정확히 1건을 요구하고, `observed_trajectory`는
    추가로 trusted `activity` 1건 이상을 요구한다(CONTRACT §1.5). 증거가
    부족하면 `completion_evidence_missing`으로 거부해 state.json을 손대지
    않는다(호출 시점이 아직 원자 쓰기 이전이어야 한다).
    """
    if block.get("mode") != "active":
        return
    profile = block.get("completion_profile")
    if profile == "cooperative":
        return

    records = _run_log_all_records(task_path, block)
    terminal_events = [r for r in records if r.get("event") in _RUN_LOG_TERMINAL_EVENTS]
    if len(terminal_events) != 1:
        err(command, "completion_evidence_missing",
            reason="terminal_missing_or_multiple", terminal_count=len(terminal_events))

    if profile == "observed_trajectory":
        activity_events = [
            r for r in records
            if r.get("event") == "activity" and (r.get("actor") or {}).get("kind") != "PM"
        ]
        if not activity_events:
            err(command, "completion_evidence_missing", reason="activity_missing")


_RUN_LOG_BOUNDARY_EVENTS = (
    "run.started", "run.completed",
    "worker.started", "worker.completed", "worker.failed", "worker.blocked",
)


def _run_log_completeness_check(task_path):
    """135 W-4 (AC-5~AC-8, D-6) — state.json run_log 계약과 JSONL 사건을 대조해
    완전성 갭을 진단한다(읽기 전용, 비차단, exit 0).

    구조 검증(run-log-tool validate-run)과는 별개 축이다 — 순번·스키마가
    유효해도 기대되는 상태 전이·PM 활동·gate 쌍·worker 경계가 실제로 관측됐는지는
    이 함수만이 판정한다(AC-8, C-4/C-5, TASK-135.S-9).

    반환 필드:
      - `missing_state_changed` / `missing_pm_activity` / `missing_gate_event` /
        `unobserved_worker_boundary`: 누락 목록 4종. `missing_pm_activity`는
        CONTRACT §2.5 트리거 조문의 상태 앵커 2종(자동 승인 행 / override)을
        committed+pending 합집합 사건과 대조해 채운다(137 W-5, D-1~D-6).
      - `last_observed_decision` / `last_observed_state_change` / `last_observed_boundary`:
        관측 지점 3필드(`{event_id, ts, ref}` 또는 없으면 None) — 누락 목록과
        무관하게 항상 반환한다(AC-7, 사람 판독이 아닌 결정론 조회).

    run_log 블록이 없는 태스크(1.0/1.1)는 모든 목록이 비고 3필드가 전부 None이다
    (C-3, 완전성 검사 대상이 아님).
    """
    result = {
        "missing_state_changed": [],
        "missing_pm_activity": [],
        "missing_gate_event": [],
        "unobserved_worker_boundary": [],
        # TASK-147 D-14/D-10(b) — 정지 원인 4분류와 오인 방지 activity 축.
        # 모든 항목은 아래 구현부의 고정 키만 쓰며, 자유 summary·reason을 읽거나
        # 응답으로 복사하지 않는다. 기존 4축/관측 3필드는 순서·의미 모두 불변이다.
        "report_intent_inconsistent": [],
        "missing_stop_decision": [],
        "stop_decision_allowed": [],
        "stop_block_without_followup": [],
        "unanchored_activity": [],
        "last_observed_decision": None,
        "last_observed_state_change": None,
        "last_observed_boundary": None,
    }

    state_file = pathlib.Path(task_path) / "state.json"
    if not state_file.is_file():
        return result
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return result

    block = _run_log_block(state)
    if block is None:
        return result

    run_id = block.get("active_run_id")
    committed = _run_log_segment_records(task_path, run_id) or []
    # 관측 지점 3필드는 아직 조각에 드레인되지 않은 보관함 사건까지 포함해 "마지막으로
    # 관측된 지점"을 결정론적으로 조회한다(AC-7) — _run_log_all_records() 재사용.
    all_records = _run_log_all_records(task_path, block)

    # ── 누락 ① missing_state_changed — committed(진짜 persist된) 로그만 근거로 삼는다.
    #   보관함에만 있는 사건은 run_log_pending이 별도로 진단하므로(§1.4), 여기서
    #   "누락"으로 다시 잡으면 두 진단이 뒤섞인다.
    committed_transitions = {}
    for rec in committed:
        if rec.get("event") == "state.changed" and isinstance(rec.get("data"), dict):
            row_key = rec["data"].get("row_key")
            to_status = rec["data"].get("to")
            committed_transitions.setdefault(row_key, set()).add(to_status)

    rows = state.get("rows") or []
    missing_state_changed = []
    for row in rows:
        row_key = row.get("key") or (f"row:{row['row_id']}" if row.get("row_id") else None)
        status = row.get("status")
        observed = committed_transitions.get(row_key, set())
        if status in ("in_progress", "done") and status not in observed:
            missing_state_changed.append({
                "row_id": row.get("row_id"), "row_key": row_key,
                "stage": row.get("stage"), "expected": status,
            })
        elif status == "done" and "in_progress" not in observed:
            # 자동 승인 등으로 in_progress 체크포인트 없이 곧바로 done에 도달한 경우
            # (S-9) — 구조적으로는 유효하지만 완전성 관점에서는 관측 중간 지점 갭이다.
            missing_state_changed.append({
                "row_id": row.get("row_id"), "row_key": row_key,
                "stage": row.get("stage"), "expected": "in_progress",
            })

    # 마지막 done 행 바로 다음 행이 여전히 pending이면(TASK 보고 후 중단 재현,
    # TASK-135.S-8) 다음 stage 진입 자체가 관측되지 않은 것이다.
    done_indices = [i for i, r in enumerate(rows) if r.get("status") == "done"]
    if done_indices:
        _next_idx = max(done_indices) + 1
        if _next_idx < len(rows) and rows[_next_idx].get("status") == "pending":
            _next_row = rows[_next_idx]
            _next_key = _next_row.get("key") or (
                f"row:{_next_row['row_id']}" if _next_row.get("row_id") else None)
            missing_state_changed.append({
                "row_id": _next_row.get("row_id"), "row_key": _next_key,
                "stage": _next_row.get("stage"), "expected": "in_progress",
                "detail": "다음 stage 진입 관측 없음(TASK 보고 후 중단 후보)",
            })
    result["missing_state_changed"] = missing_state_changed

    # ── 누락 ② missing_gate_event — gate.requested만 있고 gate.resolved가 없는 경우.
    requested_ids = {rec.get("gate_id") for rec in all_records if rec.get("event") == "gate.requested"}
    resolved_ids = {rec.get("gate_id") for rec in all_records if rec.get("event") == "gate.resolved"}
    result["missing_gate_event"] = [
        {"gate_id": gid, "expected": "gate.resolved"}
        for gid in sorted(requested_ids - resolved_ids) if gid
    ]

    # ── 누락 ③ unobserved_worker_boundary — worker.started만 있고 terminal이 없는 경우.
    started_ids = {rec.get("worker_run_id") for rec in all_records if rec.get("event") == "worker.started"}
    terminal_ids = {rec.get("worker_run_id") for rec in all_records
                    if rec.get("event") in _RUN_LOG_TERMINAL_EVENTS}
    result["unobserved_worker_boundary"] = [
        {"worker_run_id": wid} for wid in sorted(started_ids - terminal_ids) if wid
    ]

    # ── 누락 ④ missing_pm_activity — CONTRACT §2.5 트리거 조문(앵커 2종, 137 D-1~D-6).
    #   대조 집합은 committed 조각 + 보관함(pending)의 합집합(all_records)이다 — 보관함에
    #   적재된 PM activity도 이미 생산된 사건으로 본다(§1.4, D-3). 상태 앵커는 state.json의
    #   현재 사실이므로 이 판정은 state-tool 전담이다(§3.1 단방향 의존, C-4).
    pm_decisions = [
        rec for rec in all_records
        if rec.get("event") == "activity"
        and (rec.get("actor") or {}).get("kind") == "PM"
        and isinstance(rec.get("data"), dict)
        and rec["data"].get("kind") == "decision"
    ]
    decision_steps = {rec.get("task_step") for rec in pm_decisions}

    missing_pm_activity = []
    # 앵커 ① 자동 승인 행 — status=="done" ∧ owner=="auto" ∧ key 보유. key가 없는 행은
    #   대조 주소가 없어 판정 대상이 아니다(§2.5 범위 한정 (a)). row_id 오름차순(§2.5 정렬).
    auto_rows = [
        row for row in rows
        if row.get("status") == "done" and row.get("owner") == "auto" and row.get("key")
    ]
    for row in sorted(auto_rows, key=lambda r: r["row_id"]):
        if row["key"] not in decision_steps:
            missing_pm_activity.append({
                "row_id": row.get("row_id"), "row_key": row.get("key"),
                "stage": row.get("stage"), "expected": "activity(decision)",
                "anchor": "auto_approved_row",
            })

    # 앵커 ② override — run_log.status=="overridden"인데 run 전역에 PM activity(decision)가
    #   하나도 없으면 1건. 주소 대조를 하지 않으며 배열 마지막에 붙는다(§2.5 정렬).
    if block.get("status") == "overridden" and not pm_decisions:
        missing_pm_activity.append({
            "row_id": None, "row_key": None, "stage": None,
            "expected": "activity(decision)", "anchor": "override_bundle",
        })
    result["missing_pm_activity"] = missing_pm_activity

    # ── TASK-147 D-14 — Stop 판정 4분류 + D-10(b) activity 오인 방지.
    #
    # `all_records`는 조각의 append 순서 뒤에 outbox 순서를 붙인 결정론적 사건열이다.
    # 이 축은 timestamp나 summary 같은 자유 서술을 재해석하지 않는다. 특히 fixture의
    # 수동 시각이 실제 append 시각과 달라도 사건 *순서*라는 계약을 보존한다.
    # 각 배열은 이 사건열 순서(동일 입력이면 동일 순서)로 생성한다.
    report_intent_inconsistent = []
    missing_stop_decision = []
    stop_decision_allowed = []
    stop_block_without_followup = []
    unanchored_activity = []
    # missing_stop_decision의 뒤 앵커가 된 사건은 해당 "다음 턴"을 증명하는
    # 용도다. 같은 사건을 unanchored_activity에도 중복 계상하면 D-14의 4분류가
    # 서로 배타라는 S-9 계약을 깨므로 구조적 앵커로 소비한다.
    missing_stop_anchor_event_ids = set()
    receipt_pending_count = _pending_stop_receipt_count(task_path)

    # activity 앵커는 마지막 state.changed 이후 아직 소비하지 않은 1건이다. 따라서
    # 같은 상태 변화에 기대어 activity를 반복해 "진전"으로 세는 길이 생기지 않는다.
    # data.kind/사건 존재만 보며 summary는 어떤 비교에도 쓰지 않는다.
    available_state_anchor_id = None
    for index, rec in enumerate(all_records):
        if not isinstance(rec, dict):
            continue
        event_type = rec.get("event")
        if event_type == "state.changed":
            available_state_anchor_id = rec.get("event_id")
            continue

        if event_type == "pm.report":
            data = rec.get("data") if isinstance(rec.get("data"), dict) else {}
            report_type = data.get("report_type")
            transition_action = data.get("transition_action")
            user_input_required = data.get("user_input_required")
            if ((report_type == "decision_request" and transition_action == "continue")
                    or (report_type == "progress_report" and user_input_required is True)):
                report_intent_inconsistent.append({
                    "event_id": rec.get("event_id"),
                    "report_type": report_type,
                    "transition_action": transition_action,
                    "user_input_required": user_input_required,
                })

            # "부재"는 바로 다음 사건이라는 뒤 앵커가 있을 때만 확정한다. 다음
            # stop.decision이면 hook이 실행된 것이고, 어떤 다른 사건이면 그 사이에
            # Stop 판정이 없었던 것이다. 마지막 보고는 뒤 앵커가 없어 제외한다.
            if index + 1 < len(all_records):
                next_rec = all_records[index + 1]
                if isinstance(next_rec, dict) and next_rec.get("event") != "stop.decision":
                    missing_stop_anchor_event_ids.add(next_rec.get("event_id"))
                    missing_stop_decision.append({
                        "report_event_id": rec.get("event_id"),
                        "next_event_id": next_rec.get("event_id"),
                        "receipt_pending": receipt_pending_count > 0,
                    })
            continue

        if event_type == "stop.decision":
            data = rec.get("data") if isinstance(rec.get("data"), dict) else {}
            decision_kind = data.get("decision_kind")
            if isinstance(decision_kind, str) and decision_kind.startswith("allow_"):
                stop_decision_allowed.append({
                    "event_id": rec.get("event_id"),
                    "decision_kind": decision_kind,
                })
            if decision_kind == "block_continue":
                boundary_event_id = None
                has_followup = False
                for later_rec in all_records[index + 1:]:
                    if not isinstance(later_rec, dict):
                        continue
                    later_event = later_rec.get("event")
                    if later_event in ("stop.decision", "run.completed"):
                        boundary_event_id = later_rec.get("event_id")
                        break
                    if later_event in ("activity", "state.changed"):
                        has_followup = True
                        break
                if not has_followup:
                    stop_block_without_followup.append({
                        "event_id": rec.get("event_id"),
                        "boundary_event_id": boundary_event_id,
                    })
            continue

        if event_type != "activity":
            continue
        if rec.get("event_id") in missing_stop_anchor_event_ids:
            continue
        if available_state_anchor_id is None:
            unanchored_activity.append({
                "event_id": rec.get("event_id"),
                "anchor_event_id": None,
                "reason": "no_state_change_anchor",
            })
        else:
            # 한 state.changed는 activity 한 건의 구조 앵커일 뿐이다. 이 소비 규칙은
            # 동일 결과의 반복을 summary 파싱 없이 결정론적으로 드러낸다.
            available_state_anchor_id = None

    result["report_intent_inconsistent"] = report_intent_inconsistent
    result["missing_stop_decision"] = missing_stop_decision
    result["stop_decision_allowed"] = stop_decision_allowed
    result["stop_block_without_followup"] = stop_block_without_followup
    result["unanchored_activity"] = unanchored_activity

    # ── 관측 지점 3필드 (AC-7) — committed+pending 전 구간에서 마지막 레코드를 찾는다.
    def _observation(rec):
        if not rec:
            return None
        return {"event_id": rec.get("event_id"), "ts": rec.get("timestamp"), "ref": rec.get("event")}

    decisions = [
        rec for rec in all_records
        if rec.get("event") == "activity" and isinstance(rec.get("data"), dict)
        and rec["data"].get("kind") == "decision"
    ]
    state_changes = [rec for rec in all_records if rec.get("event") == "state.changed"]
    boundaries = [rec for rec in all_records if rec.get("event") in _RUN_LOG_BOUNDARY_EVENTS]

    result["last_observed_decision"] = _observation(decisions[-1] if decisions else None)
    result["last_observed_state_change"] = _observation(state_changes[-1] if state_changes else None)
    result["last_observed_boundary"] = _observation(boundaries[-1] if boundaries else None)

    return result


def _validate_run_log_refs(refs, command):
    """CONTRACT §1.1 refs 제약 — 프로젝트 상대 경로만 허용, 절대 경로는 거부한다
    (원문 그대로 저장하지 않는다는 선택 대신, 명시적 거부를 택한다 — 회신에 명시).
    """
    if not refs:
        return None
    normalized = list(refs)
    for ref in normalized:
        if pathlib.Path(ref).is_absolute():
            _rl_err(command, "refs_invalid", ref=ref)
    return normalized


def _build_pm_activity_data(args, command):
    """CONTRACT §1.3 PM activity 폐쇄 목록 — `data`는 `kind` 1개 키만 허용하고
    값은 `{decision, validation, retry, progress}` 4종 enum이다. 위반은
    `schema_invalid`로 거부한다(§1.1 폐쇄형 스키마 위반 범위).

    이 검증은 **기록 코어 집행의 앞단 중복 방어**다(137 D-9) — 같은 폐쇄 판정을
    기록 코어의 `validate_event()`도 수행하며 두 지점의 판정 결과는 항상 일치한다.
    CLI 인자 단계에서 더 구체적인 detail을 내기 위해 유지한다.
    """
    raw_data = getattr(args, "data", None)
    if raw_data:
        try:
            parsed = json.loads(raw_data)
        except json.JSONDecodeError as exc:
            _rl_err(command, "schema_invalid", detail=f"--data가 유효한 JSON이 아님: {exc}")
        if not isinstance(parsed, dict) or set(parsed.keys()) != {"kind"}:
            _rl_err(command, "schema_invalid",
                detail="activity data는 kind 1개 키만 허용합니다(CONTRACT §1.3 폐쇄 목록)")
        kind = parsed.get("kind")
    else:
        kind = args.kind
    if kind not in _PM_ACTIVITY_KIND_ENUM:
        _rl_err(command, "schema_invalid",
            detail=f"data.kind={kind!r}는 4종 enum 밖입니다(CONTRACT §1.3)")
    return {"kind": kind}


def _build_pm_report_data(args, command):
    """CONTRACT §1.3 `pm.report` 폐쇄 목록 — `data`는 `report_type`·
    `transition_action`·`user_input_required` **정확히 3키**이고 값은 각각
    2종·4종 enum과 boolean이다. 위반은 `schema_invalid`로 거부한다(D-2).

    `_build_pm_activity_data()`의 **형제**이며 같은 앞단 중복 방어 형태를 그대로
    복제한다 — 집행 지점은 기록 코어 `validate_event()` 한 곳이고(§1.3), 여기서는
    CLI 인자 단계에서 더 구체적인 detail을 내기 위해 같은 판정을 한 번 더 한다.
    [MUST] 두 지점의 판정 결과는 항상 일치한다(TASK-147.S-6이 이를 단언한다) —
    그래서 `--report-type`·`--transition-action` 값 검증을 argparse `choices`로
    하지 않는다. argparse가 거르면 앞단 오류 코드가 usage 오류(exit 2)가 되어
    기록 코어의 `schema_invalid`와 갈린다.
    """
    raw_data = getattr(args, "data", None)
    if raw_data:
        try:
            parsed = json.loads(raw_data)
        except json.JSONDecodeError as exc:
            _rl_err(command, "schema_invalid", detail=f"--data가 유효한 JSON이 아님: {exc}")
        if not isinstance(parsed, dict) or set(parsed.keys()) != _PM_REPORT_DATA_KEYS:
            keys = sorted(parsed.keys()) if isinstance(parsed, dict) else None
            _rl_err(command, "schema_invalid",
                detail=f"pm.report data는 {sorted(_PM_REPORT_DATA_KEYS)} 3키 폐쇄입니다"
                       f"(CONTRACT §1.3) — 받은 키: {keys}")
        report_type = parsed.get("report_type")
        transition_action = parsed.get("transition_action")
        user_input_required = parsed.get("user_input_required")
    else:
        report_type = getattr(args, "report_type", None)
        transition_action = getattr(args, "transition_action", None)
        raw_flag = getattr(args, "user_input_required", None)
        if raw_flag is None:
            user_input_required = None
        elif isinstance(raw_flag, bool):
            user_input_required = raw_flag
        elif raw_flag in ("true", "false"):
            user_input_required = (raw_flag == "true")
        else:
            user_input_required = raw_flag

    if report_type not in _PM_REPORT_TYPE_ENUM:
        _rl_err(command, "schema_invalid",
            detail=f"data.report_type={report_type!r}는 2종 enum 밖입니다(CONTRACT §1.3)")
    if transition_action not in _PM_TRANSITION_ACTION_ENUM:
        _rl_err(command, "schema_invalid",
            detail=f"data.transition_action={transition_action!r}는 4종 enum 밖입니다"
                   "(CONTRACT §1.3)")
    if not isinstance(user_input_required, bool):
        _rl_err(command, "schema_invalid",
            detail=f"data.user_input_required={user_input_required!r}는 boolean이어야 "
                   "합니다(CONTRACT §1.3)")
    return {
        "report_type": report_type,
        "transition_action": transition_action,
        "user_input_required": user_input_required,
    }


def _build_pm_activity_event(state, *, task_id, command, kind, summary, reason, refs,
                             stage, task_step, work_item):
    """PM `activity` 사건(조합 A4: actor.kind=PM, provenance.type=direct,
    recorded_by.kind=PM) — §1.1 공통 필드 전건 + §1.3 폐쇄 목록 준수 payload.
    """
    core = _import_run_log_core()
    block = _run_log_block(state) or {}
    return {
        "schema_version": "1.0",
        "event_id": core.new_event_id(),
        "request_id": f"req_{uuid.uuid4()}",
        "task_id": task_id,
        "run_id": block.get("active_run_id"),
        "parent_run_id": None,
        "worker_run_id": None,
        "caused_by_event_id": None,
        "stage": stage,
        "task_step": task_step,
        "work_item": work_item,
        "gate_id": None,
        "event": "activity",
        "actor": {"kind": "PM", "id": "PM", "provider": None,
                  "session_id": _current_session_id()},  # 138 W-9
        "provenance": {
            "type": "direct",
            "recorded_by": {"kind": "PM", "id": "PM"},
            "worker_log_token_id": None,
            "source": None,
        },
        "summary": summary,
        "reason": reason,
        "reason_code": None,
        "duration_ms": None,
        "duration_source": None,
        "duration_unknown_reason": None,
        "refs": refs,
        "timestamp": core.utc_now_ms(),
        "data": kind,
    }


def _build_pm_report_event(state, *, task_id, command, data, stage, task_step,
                           work_item):
    """PM `pm.report` 사건(조합 A4: actor.kind=PM, provenance.type=direct,
    recorded_by.kind=PM) — §1.1 공통 필드 전건 + §1.3 `data` 폐쇄 3키 준수 payload.

    `_build_pm_activity_event()`의 **형제**다 — 공통 필드 골격은 동일하고 `event`와
    `data`만 다르다. `activity`의 하위 축이 아니라 별도 사건이므로 완료 게이트에
    기여하지 않는다(D-1·D-2). D-16은 호출자 자유 서술을 저장 후보로 만들지 않는다:
    기록 코어의 결정론 renderer가 구조화 3축만 받아 summary를 만들고, 나머지 서술
    축은 null로 닫는다.
    """
    core = _import_run_log_core()
    block = _run_log_block(state) or {}
    return {
        "schema_version": "1.0",
        "event_id": core.new_event_id(),
        "request_id": f"req_{uuid.uuid4()}",
        "task_id": task_id,
        "run_id": block.get("active_run_id"),
        "parent_run_id": None,
        "worker_run_id": None,
        "caused_by_event_id": None,
        "stage": stage,
        "task_step": task_step,
        "work_item": work_item,
        "gate_id": None,
        "event": "pm.report",
        "actor": {"kind": "PM", "id": "PM", "provider": None,
                  "session_id": _current_session_id()},
        "provenance": {
            "type": "direct",
            "recorded_by": {"kind": "PM", "id": "PM"},
            "worker_log_token_id": None,
            "source": None,
        },
        "summary": core.render_event_summary("pm.report", data),
        "reason": None,
        "reason_code": None,
        "duration_ms": None,
        "duration_source": None,
        "duration_unknown_reason": None,
        "refs": None,
        "timestamp": core.utc_now_ms(),
        "data": data,
    }


def cmd_log_event(args):
    """state-tool log-event — PM direct 사건 기록 (CONTRACT §2.4 state-tool.log-event).

    `--event`는 `activity`·`pm.report` 2종을 수용한다(TASK-147 D-2, §2.4).
    `stop.decision`은 이 표면이 수용하지 않는다 — 그 사건은 Stop hook receipt의
    drain 경로가 조립한다(D-6).

    `actor.kind=worker` 지정은 `actor_not_allowed`로 거부한다(§9) — 이 표면은
    PM actor 사건만 수용한다. run_log_commit()의 공통 outbox/admission/drain
    경로를 그대로 재사용한다.
    """
    command = "log-event"
    actor_kind = getattr(args, "actor", None) or "PM"
    if actor_kind != "PM":
        _rl_err(command, "actor_not_allowed", actor_kind=actor_kind)

    task_path = _require_absolute_task_path(args.task_path, command)
    state = load_state_json(task_path, command)

    event_name = getattr(args, "event", None)

    if event_name == "pm.report":
        # D-16 / CONTRACT §1.3.1 — legacy `--summary`는 CLI 호환을 위해 수용하되
        # 저장하지 않는다. 반대로 reason/refs는 사건의 닫힌 서술 축을 열므로 어떤
        # 값도 검증·정규화하지 않고 쓰기 전에 schema_invalid로 거부한다.
        if getattr(args, "reason", None) is not None or getattr(args, "refs", None) is not None:
            _rl_err(command, "schema_invalid",
                    detail="pm.report는 --reason 또는 --refs를 허용하지 않습니다(CONTRACT §1.3.1)")
        report_data = _build_pm_report_data(args, command)
        event = _build_pm_report_event(
            state, task_id=task_path.name, command=command,
            data=report_data, stage=getattr(args, "stage", None),
            task_step=getattr(args, "task_step", None),
            work_item=getattr(args, "work_item", None))
    else:
        refs = _validate_run_log_refs(getattr(args, "refs", None), command)
        data_kind = _build_pm_activity_data(args, command)
        event = _build_pm_activity_event(
            state, task_id=task_path.name, command=command,
            kind=data_kind, summary=args.summary, reason=getattr(args, "reason", None),
            refs=refs, stage=getattr(args, "stage", None),
            task_step=getattr(args, "task_step", None),
            work_item=getattr(args, "work_item", None))

    fields = run_log_commit(task_path, state, command, event=event)
    warnings = fields.get("warnings") or []
    if any(w.get("code") == "run_log_pending" for w in warnings):
        pending_count = ((fields.get("run_log") or {}).get("pending") or 0)
        _rl_err(command, "run_log_pending", count=pending_count)

    status = (fields.get("run_log") or {}).get("status")
    ok(command, event_id=event["event_id"], status=status)


def _build_gate_event(state, *, task_id, command, event_name, gate_id, actor_kind,
                      summary, reason, data):
    """`gate.requested`/`gate.resolved` 공통 골격 — §1.1 공통 필드 전건.

    `actor.kind=PM`이면 조합 A4, `user`면 A5, `auto`면 A6이다. 세 조합 모두
    `recorded_by.kind ∈ {PM, tool}`(A4)·`{PM, tool}`(A5)·`{tool}`(A6)을 허용하므로
    `recorded_by.kind="tool"`(state-tool 자신)로 통일해도 세 조합 모두에 유효하다.
    """
    core = _import_run_log_core()
    block = _run_log_block(state) or {}
    return {
        "schema_version": "1.0",
        "event_id": core.new_event_id(),
        "request_id": f"req_{uuid.uuid4()}",
        "task_id": task_id,
        "run_id": block.get("active_run_id"),
        "parent_run_id": None,
        "worker_run_id": None,
        "caused_by_event_id": None,
        "stage": None,
        "task_step": None,
        "work_item": None,
        "gate_id": gate_id,
        "event": event_name,
        "actor": {"kind": actor_kind, "id": actor_kind, "provider": None,
                  "session_id": _current_session_id()},  # 138 W-9
        "provenance": {
            "type": "direct",
            "recorded_by": {"kind": "tool", "id": "state-tool"},
            "worker_log_token_id": None,
            "source": None,
        },
        "summary": summary,
        "reason": reason,
        "reason_code": None,
        "duration_ms": None,
        "duration_source": None,
        "duration_unknown_reason": None,
        "refs": None,
        "timestamp": core.utc_now_ms(),
        "data": data,
    }


def cmd_gate_request(args):
    """state-tool gate-request — `gate.requested` 기록 (CONTRACT §2.4 state-tool.gate-request).

    같은 `gate_id`의 중복 requested는 `gate_duplicate`로 거부한다(§4.4). 조각 +
    아직 드레인되지 않은 보관함 양쪽에서 유일성을 판정한다.
    """
    command = "gate-request"
    task_path = _require_absolute_task_path(args.task_path, command)
    state = load_state_json(task_path, command)
    block = _run_log_block(state)

    if block is not None:
        existing = _run_log_all_records(task_path, block)
        if any(r.get("event") == "gate.requested" and r.get("gate_id") == args.gate_id
               for r in existing):
            _rl_err(command, "gate_duplicate", gate_id=args.gate_id, event="gate.requested")

    event = _build_gate_event(
        state, task_id=task_path.name, command=command,
        event_name="gate.requested", gate_id=args.gate_id, actor_kind="PM",
        summary=args.summary, reason=None, data=None)

    fields = run_log_commit(task_path, state, command, event=event)
    warnings = fields.get("warnings") or []
    if any(w.get("code") == "run_log_pending" for w in warnings):
        pending_count = ((fields.get("run_log") or {}).get("pending") or 0)
        _rl_err(command, "run_log_pending", count=pending_count)

    status = (fields.get("run_log") or {}).get("status")
    ok(command, event_id=event["event_id"], gate_id=args.gate_id, status=status)


def cmd_gate_resolve(args):
    """state-tool gate-resolve — `gate.resolved` 기록 (CONTRACT §2.4 state-tool.gate-resolve).

    선행 `gate.requested` 없는 resolve는 `gate_not_requested`, 같은 `gate_id`의
    중복 resolved는 `gate_duplicate`로 거부한다. 대기 시간(`waited_ms`)은 두
    사건의 UTC timestamp 차분으로만 계산한다(§2.4 계약 불변식) — 벽시계를
    별도로 다시 재지 않는다.
    """
    command = "gate-resolve"
    task_path = _require_absolute_task_path(args.task_path, command)
    state = load_state_json(task_path, command)
    block = _run_log_block(state)

    existing = _run_log_all_records(task_path, block) if block is not None else []
    requested = [r for r in existing
                 if r.get("event") == "gate.requested" and r.get("gate_id") == args.gate_id]
    if not requested:
        _rl_err(command, "gate_not_requested", gate_id=args.gate_id)
    if any(r.get("event") == "gate.resolved" and r.get("gate_id") == args.gate_id
           for r in existing):
        _rl_err(command, "gate_duplicate", gate_id=args.gate_id, event="gate.resolved")

    actor_kind_map = {"PM": "PM", "user": "user", "auto": "auto"}
    actor_kind = actor_kind_map.get(args.owner, "PM")

    event = _build_gate_event(
        state, task_id=task_path.name, command=command,
        event_name="gate.resolved", gate_id=args.gate_id, actor_kind=actor_kind,
        summary=getattr(args, "note", None) or f"gate {args.gate_id} resolved: {args.verdict}",
        reason=getattr(args, "note", None),
        data={"verdict": args.verdict})

    core = _import_run_log_core()
    requested_ts = requested[0].get("timestamp")
    waited_ms = None
    if requested_ts:
        try:
            fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
            t0 = datetime.strptime(requested_ts, fmt).replace(tzinfo=timezone.utc)
            t1 = datetime.strptime(event["timestamp"], fmt).replace(tzinfo=timezone.utc)
            waited_ms = int((t1 - t0).total_seconds() * 1000)
        except ValueError:
            waited_ms = None

    fields = run_log_commit(task_path, state, command, event=event)
    warnings = fields.get("warnings") or []
    if any(w.get("code") == "run_log_pending" for w in warnings):
        pending_count = ((fields.get("run_log") or {}).get("pending") or 0)
        _rl_err(command, "run_log_pending", count=pending_count)

    status = (fields.get("run_log") or {}).get("status")
    ok(command, event_id=event["event_id"], gate_id=args.gate_id,
       waited_ms=waited_ms, status=status)


def load_state_md(task_path):
    """STATE.md 텍스트 반환. 없으면 None."""
    md_file = task_path / "STATE.md"
    if not md_file.exists():
        return None
    with open(md_file, encoding="utf-8") as f:
        return f.read()

def save_state_md(task_path, content):
    """STATE.md 저장."""
    md_file = task_path / "STATE.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(content)

# ─────────────────────────────────────────────────────────────────────────────
# 소유자 호칭 치환 (PLAN §3.1.2, TASK 054)
# ─────────────────────────────────────────────────────────────────────────────

def resolve_owner_placeholder(text: str) -> str:
    """note 등 사용자 free text에 담긴 '{owner_name}' 플레이스홀더를 identity.md의
    owner_name 값으로 write-time 치환한다.

    fail-safe(원문 유지): 플레이스홀더 미포함, identity.md 부재, owner_name 공란/미발견,
    또는 파일 읽기·파싱 중 예외 발생 시 모두 원문 text를 그대로 반환한다 — note 저장
    자체를 실패시키지 않는다. 경로는 OPAL_HOME env 우선(플랫폼 독립, ~/.opal 하드코딩 분기 금지).
    T-11: 표준 라이브러리(re/os/pathlib)만 사용 — PyYAML 등 신규 패키지 도입 금지.
    """
    if not text or "{owner_name}" not in text:
        return text
    try:
        opal_home = os.environ.get("OPAL_HOME") or os.path.expanduser("~/.opal")
        identity_path = pathlib.Path(opal_home) / "identity.md"
        if not identity_path.exists():
            return text
        content = identity_path.read_text(encoding="utf-8")
        fm_match = re.search(r"^---\s*$(.*?)^---\s*$", content, re.M | re.S)
        block = fm_match.group(1) if fm_match else content
        m = re.search(r"^owner_name:\s*(.*)$", block, re.M)
        if not m:
            return text
        owner_name = m.group(1).strip().strip("\"'")
        if not owner_name:
            return text
        return text.replace("{owner_name}", owner_name)
    except Exception:
        return text

# ─────────────────────────────────────────────────────────────────────────────
# 마크다운 렌더 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def render_pipeline_table(rows):
    """state.json rows[]를 마크다운 표로 렌더 (마커 제외).
    094: cmd_show --format md의 유일한 렌더 경로로 용도가 격하되었다 — 파일에
    고정 저장하는 미러가 아니라 요청 시 생성하는 뷰(§3.2.2 (4)). '비고' 열에
    row.note를 노출해, 렌더가 STATE.md 동결 텍스트가 아니라 state.json 최신
    값을 반영함을 조회 결과로도 구분할 수 있게 한다(F-003 렌더 원천 단일화)."""
    lines = [
        "## 파이프라인 현황판",
        "",
        "> 상태값: ⬜ 대기 / 🔄 진행 중 / ✅ 완료 / ❌ 실패 / - 해당 없음",
        "> **수행 원칙**: 위에서 아래로 순서대로 처리한다. 현재 행이 ✅가 아니면 다음 행으로 진행 불가.",
        "",
        "| # | 단계 | 항목 | 상태 | 시점 | 비고 |",
        "|---|------|------|------|------|------|",
    ]
    for row in rows:
        ts = row.get("timestamp") or ""
        note = row.get("note") or ""
        lines.append(
            f"| {row['row_id']} | {row['stage']} | {row['item']} | {row['status_label']} | {ts} | {note} |"
        )
    return "\n".join(lines)

def update_state_md_header(md_content, new_datetime):
    """G-5(D-3 존치): STATE.md '> 최종 갱신:' 라인 교체. 저널 축소판에서도
    계속 호출되어 advance/mark 후 헤더 타임스탬프가 갱신된다(094 §3.1.2 (3))."""
    return re.sub(
        r"^(> 최종 갱신: ).*$",
        lambda m: f"{m.group(1)}{new_datetime}",
        md_content, count=1, flags=re.MULTILINE
    )

# ─────────────────────────────────────────────────────────────────────────────
# 의사결정 로그 자동 기재 (PLAN §2.17 G-14/G-15, 094 §3.1.2 (2)(6))
# ─────────────────────────────────────────────────────────────────────────────

def _escape_table_cell(value):
    """094 S-32: 의사결정 로그 표 셀에 들어갈 값의 '|'·개행을 이스케이프해
    표 구조 파괴(열 증가·행 분열)를 방지한다. '|' → '&#124;', 개행 → '<br>' —
    원문 토큰은 삭제되지 않고 치환되므로 복원 가능성이 보존된다."""
    text = "" if value is None else str(value)
    return text.replace("|", "&#124;").replace("\r\n", "<br>").replace("\n", "<br>")


def ensure_journal_skeleton(md, task_title, now_str):
    """저널 필수 골격('## 의사결정 로그' 표 헤더)을 보증한다 (094 §3.1.2 (2)).
    - md is None            → _build_new_state_md(task_title, now_str) 반환
    - 표 헤더 정규식 미매칭 → 헤딩이 있으면 그 직후에 표 헤더만 복구 삽입,
                              헤딩조차 없으면 파일 끝에 '## 의사결정 로그' 빈 표 블록을 append
    - 이미 존재            → md 원문 그대로 반환 (멱등)
    레거시 STATE.md(마커·표 보유)는 본문을 일절 건드리지 않는다 — append/삽입만 수행한다.
    """
    if md is None:
        return _build_new_state_md(task_title, now_str)

    full_pattern = re.compile(r"## 의사결정 로그\n\| # \| 시점 \| 결정 \| 근거 \|\n\|[-| ]+\|\n")
    if full_pattern.search(md):
        return md  # 이미 골격 존재 — 멱등

    header_block = "| # | 시점 | 결정 | 근거 |\n|---|------|------|------|\n"
    heading_match = re.search(r"^## 의사결정 로그\n", md, re.MULTILINE)
    if heading_match:
        # 헤딩은 있으나 표 헤더/구분행이 손상됨 — 헤딩 직후에 표 헤더만 복구
        insert_at = heading_match.end()
        return md[:insert_at] + header_block + md[insert_at:]

    # 헤딩 자체가 없음 — 파일 끝에 전체 섹션 append
    return md.rstrip("\n") + "\n\n## 의사결정 로그\n" + header_block


def append_decision_log(md_content, now_str, decision, reason):
    """STATE.md '## 의사결정 로그' 표에 1행 추가.
    표가 없거나 헤더를 못 찾으면 무시 (자유 텍스트 영역 외 안전 보장).
    """
    pattern = re.compile(
        r"(## 의사결정 로그\n\| # \| 시점 \| 결정 \| 근거 \|\n\|[-| ]+\|\n)((?:\|[^\n]*\|\n)*)",
        re.MULTILINE
    )
    m = pattern.search(md_content)
    if not m:
        return md_content  # 표 없으면 조용히 패스

    # 기존 행 수 파악 → 새 # 컬럼값
    # 094: 오프바이원 수정 — 캡처 그룹 문자열이 '\n'으로 시작하지 않는 경계
    # (기존 행이 정확히 1개일 때)를 정확히 세기 위해 실제 '|'로 시작하는 줄
    # 수를 직접 카운트한다(기존 "\n| " count 방식은 그 경계에서 0으로 오카운트).
    existing_rows = m.group(2)
    row_count = len([l for l in existing_rows.splitlines() if l.strip().startswith("|")])
    new_num = row_count + 1
    safe_decision = _escape_table_cell(decision)
    safe_reason   = _escape_table_cell(reason)
    new_row = f"| {new_num} | {now_str} | {safe_decision} | {safe_reason} |\n"

    replacement = m.group(1) + existing_rows + new_row
    return md_content[:m.start()] + replacement + md_content[m.end():]

# ─────────────────────────────────────────────────────────────────────────────
# 저널 후처리 (094: 구 '미러 동기화'에서 의미 재정의 — fail-open)
# ─────────────────────────────────────────────────────────────────────────────

def _redact_path_like(text):
    """예외 메시지에 섞여 나오는 절대경로/홈 디렉토리 경로를 파일명(basename)
    으로 치환한다(R-11 SEC 후속 — journal_warning.reason 경로 노출 차단,
    PLAN.md §5.4). 특정 OS·예외의 메시지 포맷(Errno 구조 등)을 가정하지 않고,
    공백으로 나눈 토큰 중 '/'로 시작하거나 사용자 홈 경로로 시작하는 것을
    일반적으로 탐지해 basename만 남긴다 — 예외 타입명·파일명 등 진단 가치는
    보존하고 경로 프리픽스만 절삭한다."""
    home = str(pathlib.Path.home())

    def _shrink(token):
        m = re.match(r"^([\"'`]*)(.*?)([\"'`.,;:]*)$", token, re.DOTALL)
        prefix, core, suffix = m.groups() if m else ("", token, "")
        if core and (core.startswith("/") or core.startswith(home)):
            base = os.path.basename(core.rstrip("/")) or core
            return f"{prefix}{base}{suffix}"
        return token

    return " ".join(_shrink(tok) for tok in text.split(" "))


def sync_state_md(task_path, state, now_str, command, decision=None, reason=None):
    """저널 후처리 (094 §3.1.2 (3)):
    1. G-5(D-3) 최종 갱신 헤더 교체
    2. decision이 있으면 저널 골격을 보증(ensure_journal_skeleton)한 뒤
       G-14/G-15 의사결정 로그 기재
    반환: dict | None — 실패 시 {"journal_warning": {...}}, 성공(또는 no-op) 시 None.
    [MUST] 어떤 경로에서도 err()/sys.exit()를 호출하지 않는다(fail-open) — 저널
    쓰기 실패가 파이프라인을 막아서는 안 되지만, 실패 자체는 stdout
    journal_warning으로 표면화해 결정 로그 원문이 조용히 증발하지 않게 한다.
    """
    try:
        md = load_state_md(task_path)
        if decision is not None:
            md = ensure_journal_skeleton(md, state.get("task_id", "task"), now_str)
        if md is None:
            return None  # 갱신할 저널 없음 + 기재할 결정 없음 → no-op

        md = update_state_md_header(md, now_str)
        if decision is not None:
            md = append_decision_log(md, now_str, decision, reason or "(none)")

        save_state_md(task_path, md)
        return None
    except Exception as e:  # 디스크/권한 등 I/O 오류만 도달
        return {"journal_warning": {
            "reason": _redact_path_like(f"{type(e).__name__}: {e}"),
            "decision": decision, "note": reason,
        }}

# ─────────────────────────────────────────────────────────────────────────────
# 행 조회 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def find_row(state, row_id, command):
    """row_id에 해당하는 행 반환. 없으면 row_not_found + exit 1."""
    for row in state["rows"]:
        if row["row_id"] == row_id:
            return row
    err(command, "row_not_found", row_id=row_id)

def find_row_index(state, row_id, command):
    """row_id에 해당하는 인덱스 반환. 없으면 row_not_found + exit 1."""
    for i, row in enumerate(state["rows"]):
        if row["row_id"] == row_id:
            return i
    err(command, "row_not_found", row_id=row_id)


def resolve_row_index(state, command, key_val=None, id_val=None, row_val=None,
                      addr_label="task-step"):
    """key/id/deprecated-row 3주소를 row_index로 통일 해석 (070 F-003 R-4, PLAN §3.3.2).

    - addr_label로 에러 메시지에 노출할 실제 플래그명을 결정한다:
        "after"    → add-row 컨텍스트: --after-task-step/--after-task-step-id/--after
        그 외(기본) → advance/mark/block 컨텍스트: --task-step/--task-step-id/--row(deprecated)
    - 제공된 주소 개수 집계(None 아닌 것):
        0개  → err(command, 'task_step_addr_required', flags=...)
        2개+ → err(command, 'task_step_addr_conflict', flags=...)
    - key_val: rows[]에서 row['key']==key_val 탐색. 미매칭 시 'task_step_not_found'
      (flag=키 주소 플래그명, candidates=존재하는 key 목록).
    - id_val / row_val: row_id 동등비교(find_row_index 로직 재사용). 미매칭 시 'row_not_found'.
    반환: row_index(int).
    """
    if addr_label == "after":
        flags = "--after-task-step/--after-task-step-id/--after"
        key_flag = "--after-task-step"
    else:
        flags = "--task-step/--task-step-id/--row(deprecated)"
        key_flag = "--task-step"

    provided = [v for v in (key_val, id_val, row_val) if v is not None]
    if len(provided) == 0:
        err(command, "task_step_addr_required", flags=flags)
    if len(provided) >= 2:
        err(command, "task_step_addr_conflict", flags=flags)

    if key_val is not None:
        for i, row in enumerate(state["rows"]):
            if row.get("key") == key_val:
                return i
        candidates = [r.get("key") for r in state["rows"] if r.get("key")]
        err(command, "task_step_not_found", key=key_val, flag=key_flag, candidates=candidates)

    row_id = id_val if id_val is not None else row_val
    return find_row_index(state, row_id, command)

# ─────────────────────────────────────────────────────────────────────────────
# 단계 건너뛰기 차단 (PLAN §M-A stage-transition guard)
# ─────────────────────────────────────────────────────────────────────────────

# 완료로 간주하는 상태값 — 이 상태의 앞 행은 건너뛰기 검증에서 제외
_COMPLETE_STATUSES = {"done", "additional_work_done", "na"}

# 093 F-005: --auto-pass note 접두 (기존 state.json·하네스 문서가 참조 — 문자열 불변)
_AUTO_PASS_PREFIX = "agentic auto-pass"


def build_todo_mirror(state, action):
    """076 R-1: state.json rows[] → 단계(stage) 단위 todo 미러 페이로드.

    action: "create"(init) | "update"(advance/mark/block).
    비영속 — ok() stdout 페이로드에만 사용하며 save_state_json 미접촉
    (H-3, state.schema.json §root additionalProperties:false 위반 회피).

    파생 규칙(state.md §파이프라인 todo 미러 정합):
      - na 행은 집계에서 중립(제외) — agentic auto-na 오판 방지(DEC-2).
      - effective 없음 or 전부 done/additional_work_done → completed.
      - 전부 pending → pending.
      - 그 외(in_progress·failed·부분완료 혼합) → in_progress
        — 블로커(failed)는 in_progress 유지(DEC-3, todo에 실패 상태 없음).

    단계 순서는 rows 등장 순서를 보존한다(dict.fromkeys 패턴, _build_new_state_md 선례).
    status 열거값(pending/in_progress/completed)은 네이티브 할일 도구 status와 직접 매핑되어
    소유자(PM)가 그대로 릴레이한다(DEC-1)."""
    rows = state.get("rows", [])
    stages = list(dict.fromkeys(r["stage"] for r in rows))
    todos = []
    for stage in stages:
        srows = [r for r in rows if r["stage"] == stage]
        effective = []
        for r in srows:
            if r.get("status") == "na":
                continue                       # na 중립(DEC-2, 기존)
            if r.get("item") == "사용자 확인":   # R-11 G-3-b: 자동 승인 예정 행도 중립
                allowed, _ = can_auto_approve_user_confirmation(
                    r.get("stage"), state.get("mode"))
                if allowed:
                    continue
            effective.append(r.get("status"))
        if not effective or all(s in ("done", "additional_work_done") for s in effective):
            st = "completed"
        elif all(s == "pending" for s in effective):
            st = "pending"
        else:  # in_progress / failed / 부분완료 혼합 → in_progress(블로커 유지 DEC-3)
            st = "in_progress"
        todos.append({
            "id":         f"stage:{stage}",       # 세션 내 안정 키
            "content":    f"{stage} 단계",         # TaskCreate/TaskUpdate content
            "activeForm": f"{stage} 단계 진행 중",  # 진행형 표현(native todo 스키마)
            "status":     st,                      # pending | in_progress | completed
        })
    return {"action": action, "todos": todos}


def _derive_next_action(state):
    """072 G-16: 파이프라인 프론티어(첫 미완료 행)에서 '다음 액션' 문자열 파생.
    전체 완료 시 '태스크 완료'(M-2). 070 정합: row 순서 스캔 + _COMPLETE_STATUSES 재사용
    (resolve_row_index/task-step key 체계 무접촉)."""
    mode = state.get("mode")
    rows = state.get("rows", [])
    for idx, row in enumerate(rows):
        st = row.get("status")
        if st in _COMPLETE_STATUSES:
            continue
        # R-11 G-3-a: 다음 진입 시 도구가 자동 승인할 사용자 확인 행은 프론티어가 아니다.
        # CLOSE 직전 행도 can_auto_approve_user_confirmation()의 같은 mode 판정을 따른다.
        if row.get("item") == "사용자 확인":
            allowed, _ = can_auto_approve_user_confirmation(row.get("stage"), mode)
            if allowed:
                continue
        stage, item = row.get("stage", ""), row.get("item", "")
        if st == "in_progress":
            return f"{stage} {item} 진행 중"
        if st == "failed":
            return f"{stage} {item} 블로커 해소"
        return f"{stage} {item} 진입"   # pending
    return "태스크 완료"


# ─────────────────────────────────────────────────────────────────────────────
# CLOSE 완료 시 메모리 히스토리 자동 연결 (PLAN 088 §2.1~§2.7, §2.9)
# ─────────────────────────────────────────────────────────────────────────────

# historyRow stage 값 — D-6 확정(2026-08-11부로 "완료·커밋" 표기 폐기)
HISTORY_STAGE_DONE = "완료"
# result(핵심결과) 초기값 — 빈 문자열 대신 PM 보강 대기를 식별 가능하게 표면화(§2.6)
HISTORY_RESULT_PLACEHOLDER = "(PM 보강 대기)"
# task_id("{NNN}-{yymmdd}-{skill}-{설명}") → title 파생 패턴(§2.6). 불일치 시 원문 폴백.
HISTORY_TITLE_PATTERN = re.compile(r"^(\d{3})-\d{6}-[a-z]+-(.+)$")

# 형제 memory-tool CLI 경로 — state-tool/memory-tool은 항상 같은 tools/ 부모를 공유한다(§2.2)
_MEMORY_TOOL = pathlib.Path(__file__).resolve().parent.parent / "memory-tool" / "memory_tool.py"


def task_root(task_path):
    """task_path의 조상 중 .opal/MEMORY.json을 파일로 가진 첫 디렉토리를 반환한다(§2.3).
    없으면 None — 호출자는 subprocess를 아예 띄우지 말고 조기 반환해야 한다.

    118 D-4: 이 탐색은 **task root 목적 전용**이다(설정·gate·인용 판정). 허브
    `.opal/MEMORY.json` 쓰기 대상인 allocator root는 이 함수로 구하지 않는다 —
    worktree registry 발급값을 명시 인자로만 전달받는다. 계약 원문은
    `opal/core/references/harness/worktree.md` §task root와 allocator root 계약이다.
    하위호환 alias는 두지 않는다 — 미갱신 호출이 NameError로 즉시 드러나야 한다(118 H-1).
    """
    p = pathlib.Path(task_path).resolve()
    for cand in (p, *p.parents):
        if (cand / ".opal" / "MEMORY.json").is_file():
            return cand
    return None


def derive_history_title(task_id):
    """task_id(태스크 폴더명)에서 히스토리 title을 파생한다(§2.6).
    '{NNN}-{yymmdd}-{skill}-{설명}' 패턴이면 '{NNN} {설명(하이픈→공백)}',
    패턴 불일치 시 task_id 원문으로 폴백(state.json에 별도 제목 필드가 없음)."""
    m = HISTORY_TITLE_PATTERN.match(task_id or "")
    if not m:
        return task_id
    number, rest = m.group(1), m.group(2)
    return f"{number} {rest.replace('-', ' ')}"


def build_history_reminder(title, memory_file):
    """result(핵심결과) 보강을 즉시 실행 가능한 명령 문자열로 안내한다(§2.7).
    PM 실행 경로는 사용자 대면 표준인 run.sh로 안내한다."""
    return (
        "[메모리 히스토리] 작업 히스토리 행이 자동 생성되었다(핵심결과 미기재). 지금 보강하라:\n"
        f'"$HOME/.opal/tools/memory-tool/run.sh" update --file {memory_file} '
        f'--kind history --title "{title}" --result "<무엇을 바꿨는지 + 결과>"'
    )


def _run_memory_tool(argv):
    """형제 memory_tool.py를 sys.executable subprocess로 실행한다(§2.2 — import·run.sh 경유 배제).
    반환: (returncode, dict|None) — stdout 중 마지막으로 파싱되는 JSON 라인. 파싱 실패 시 None."""
    result = subprocess.run(
        [sys.executable, str(_MEMORY_TOOL), *argv],
        capture_output=True, text=True, timeout=10,
    )
    parsed = None
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except (ValueError, TypeError):
            continue
        if isinstance(obj, dict):
            parsed = obj
    return result.returncode, parsed


def link_memory_history(task_path, state, allocator_root):
    """허브 `.opal/MEMORY.json`에 작업 히스토리 행을 멱등으로 append한다(§2.1/§2.4/§2.5).

    118 D-4/D-4b: 호출자는 `finalize-attribution` 서브커맨드 **하나뿐**이다. CLOSE
    마지막 행 mark는 더 이상 이 함수를 호출하지 않는다. `allocator_root`는 **명시
    인자**이며 이 함수는 조상 탐색으로 이를 추론하지 않는다 — cwd, task path의 조상,
    `.opal-worktrees` 문자열 어느 것도 근거로 쓰지 않는다(worktree.md §task root와
    allocator root 계약).

    항상 payload dict를 반환하고 예외를 전파하지 않는다 — err()를 호출하지 않으며,
    memory-tool 부재/실패/타임아웃이 있어도 호출자를 예외로 끊지 않는다(R-4).
    판정 키는 path(§2.4) — show로 사전 조회해 동일 path 행이 있으면 append를 건너뛴다.
    """
    try:
        if allocator_root is None:
            return {"status": "skipped",
                    "warning": "allocator_root가 전달되지 않음 — 추론하지 않는다(118 D-4)"}
        project_root = pathlib.Path(allocator_root).resolve()
        if not (project_root / ".opal" / "MEMORY.json").is_file():
            return {"status": "skipped",
                    "warning": f"allocator_root에 .opal/MEMORY.json이 없음: {project_root}"}
        if not _MEMORY_TOOL.is_file():
            return {"status": "skipped",
                    "warning": f"memory_tool.py를 찾지 못함: {_MEMORY_TOOL}"}

        memory_file = project_root / ".opal" / "MEMORY.json"
        resolved_task = pathlib.Path(task_path).resolve()
        try:
            rel_path = resolved_task.relative_to(project_root).as_posix() + "/"
        except ValueError:
            # 워크트리 작업본의 task path는 허브(allocator_root) 하위가 아니다.
            # 허브 기준 표준 위치(tasks/{task_folder}/)로 기록한다 — allocator_root를
            # task path 조상에서 되추론하지 않기 위한 폴백이다(118 D-4).
            rel_path = f"tasks/{resolved_task.name}/"
        title = derive_history_title(state.get("task_id", ""))

        rc, show_result = _run_memory_tool(["show", "--file", str(memory_file)])
        if rc != 0 or show_result is None:
            warning = (show_result or {}).get("message") or f"memory-tool show 실패 (rc={rc})"
            return {"status": "failed", "warning": str(warning)}

        history_rows = show_result.get("history_rows") or []
        if any(r.get("path") == rel_path for r in history_rows):
            return {
                "status": "duplicate_skipped",
                "title": title, "path": rel_path, "stage": HISTORY_STAGE_DONE,
                "memory_file": str(memory_file),
                "reminder": build_history_reminder(title, memory_file),
            }

        rc, append_result = _run_memory_tool([
            "append", "--file", str(memory_file), "--kind", "history",
            "--title", title, "--stage", HISTORY_STAGE_DONE,
            "--path", rel_path, "--summary", HISTORY_RESULT_PLACEHOLDER,
        ])
        if rc != 0 or append_result is None:
            warning = (append_result or {}).get("message") or f"memory-tool append 실패 (rc={rc})"
            return {"status": "failed", "warning": str(warning)}

        return {
            "status": "created",
            "title": title, "path": rel_path, "stage": HISTORY_STAGE_DONE,
            "memory_file": str(memory_file),
            "reminder": build_history_reminder(title, memory_file),
        }
    except Exception as e:
        return {"status": "failed", "warning": str(e)}


def check_stage_transition_guard(state, row_index, command, force=False, scope="full"):
    """대상 행(row_index) 앞의 행이 완료 상태인지 검증.
    미완 행이 있으면 stage_transition_violation 에러 응답 후 exit 1.
    force=True면 우회 (--note 필수는 호출자가 이미 보장).

    완료로 간주: done / additional_work_done / na (agentic auto-na 포함).
    이미 done인 행을 재 mark 하는 경우(멱등)도 앞 행 검증 통과 후 허용.

    scope="full"         (PM 경로, 기본): 대상 행 앞의 모든 행이 완료여야 함.
    scope="prior_stage_only" (워커 경로): 대상 행의 stage보다 앞 stage에 속한
                             행만 검증. 같은 stage 내 앞 행은 검증 제외.
    """
    if force:
        return

    row = state["rows"][row_index]
    # 이미 완료 상태인 행의 재 mark(멱등) — 앞 행이 미완이어도 허용
    if row.get("status") in _COMPLETE_STATUSES:
        return

    target_stage = row["stage"]

    # prior_stage_only: 대상 행의 stage가 처음 등장하는 인덱스를 경계로 삼는다.
    # 그 인덱스 미만의 행(= 앞 단계 행)만 검증한다.
    if scope == "prior_stage_only":
        # 대상 stage가 처음 등장하는 위치를 찾는다
        stage_start = 0
        for i, r in enumerate(state["rows"]):
            if r["stage"] == target_stage:
                stage_start = i
                break
        check_up_to = stage_start  # [0, stage_start) 범위만 검증
    else:
        check_up_to = row_index    # [0, row_index) 전체 검증

    incomplete = []
    for i in range(check_up_to):
        prev = state["rows"][i]
        # CLOSE 직전 사용자 확인은 일반 단계 전이 미완료가 아니라
        # check_close_gate가 owner=user까지 판정하는 소유권 게이트다.
        if target_stage == "CLOSE" and prev.get("item") == "사용자 확인":
            continue
        if prev.get("status") not in _COMPLETE_STATUSES:
            incomplete.append(prev["row_id"])

    if incomplete:
        err(command, "stage_transition_violation",
            row_id=row["row_id"],
            incomplete_rows=incomplete)


# ─────────────────────────────────────────────────────────────────────────────
# 자동 승인 훅 (093 F-002 R-2, PLAN §3.2.2)
# ─────────────────────────────────────────────────────────────────────────────

def auto_approve_prior_user_confirmations(
    state, row_index, command, *,
    as_worker=False, force=False, now_str=None,
):
    """R-2 조항 2 집행 — 대상 행 진입 시 앞의 미완 '사용자 확인' 행을 자동 승인한다.

    반환: 자동 승인한 row_id 리스트 (list[int]). 승인 대상이 없으면 [].
    부작용: state["rows"][i]를 in-place 갱신 (호출자가 save_state_json 책임).
    거부: 자동 승인 불가 구간이면 err(command, "user_confirmation_required", ...) 후 exit 1.

    [MUST] 이 함수는 save_state_json을 호출하지 않는다 — 가드 전량 통과 후 1회 저장
    패턴을 유지해, 후속 가드 실패 시 파일이 오염되지 않는다 (H-8).
    """
    if as_worker:
        return []          # 워커 경로 — 자동 승인 없음 (DEC-C)
    if force:
        return []          # --force 우회 경로 — 가드 자체가 스킵되므로 훅도 no-op

    target_row = state["rows"][row_index]
    approved = []
    for i in range(row_index):                        # [0, row_index) — full scope와 동일 범위
        prev = state["rows"][i]
        if prev.get("item") != "사용자 확인":
            continue
        if prev.get("status") in _COMPLETE_STATUSES:  # done / additional_work_done / na
            continue                                  # 멱등 — 기존 na 행도 재승인하지 않는다 (R-6)
        if prev["stage"] == "CLOSE":
            continue                                  # DEC-D 2차 방어

        allowed, deny_reason = can_auto_approve_user_confirmation(   # DEC-D 3차 방어 포함
            prev["stage"], state.get("mode", "interactive"))
        if not allowed:
            err(command, "user_confirmation_required",               # F-004
                row_id=prev["row_id"], stage=prev["stage"],
                key=prev.get("key"), item=prev["item"],
                mode=state.get("mode"), reason=deny_reason,
                required_action=(
                    f"보고 → 캡틴 승인 → state mark <task-path> "
                    f"--task-step {prev.get('key') or prev['row_id']} --done --owner user"
                ))

        prev["status"]       = "done"
        prev["status_label"] = "✅"
        prev["owner"]        = "auto"
        prev["timestamp"]    = now_str
        prev["note"]         = f"auto-approved on {target_row['stage']} entry"
        approved.append(prev["row_id"])
    return approved


# ─────────────────────────────────────────────────────────────────────────────
# CLOSE 진입 게이트 검증 (PLAN §2.16 G-13)
# ─────────────────────────────────────────────────────────────────────────────

def check_close_gate(state, row_index, command, auto_pass=False, force=False, owner=None):
    """CLOSE 단계 첫 행 갱신 시 게이트 검증.
    위반 시 close_gate_violation 또는 agentic_close_gate_requires_user.
    force=True면 스킵.

    owner: 이번 호출로 이 행에 적용될 예정인 --owner 값(cmd_mark 전용, 094 R-11 G-2).
    CLOSE 첫 행 갱신 시점에는 row["owner"]가 아직 갱신 전(=기존 값, 통상 'PM')이므로
    확인 행 0개 파이프라인의 소유자 승인 판정은 반드시 이 인자로 해야 한다 —
    row.get("owner")를 참조하면 항상 갱신 전 값을 보게 되어 폴백이 무의미해진다.
    """
    row = state["rows"][row_index]
    if row["stage"] != "CLOSE":
        return  # CLOSE 아니면 무관

    # CLOSE 단계 첫 행 여부 확인
    is_first_close = (row_index == 0 or state["rows"][row_index - 1]["stage"] != "CLOSE")
    if not is_first_close:
        return

    if force:
        return  # force 우회

    # The shared mode decision also owns close-gate admission.  Keep the legacy
    # agentic_close_gate_requires_user catalog entry for compatibility, but do not
    # emit it on this mode-aware path.
    allowed, _ = can_auto_approve_user_confirmation("CLOSE", state.get("mode"))
    if allowed:
        return

    # 직전 단계 사용자 확인 행 검색 (역순)
    prev_user_row = None
    for i in range(row_index - 1, -1, -1):
        if state["rows"][i].get("item") == "사용자 확인":
            prev_user_row = state["rows"][i]
            break

    if prev_user_row is None:
        # 094 R-11 G-2: 확인 행이 없는 파이프라인(opgc 등) — CLOSE 첫 행 자체를
        # 소유자 승인 지점으로 삼는다(정상 형태로 인정, 데드락 폴백).
        if owner != "user":
            err(command, "close_gate_violation",
                violation_detail=(
                    "pipeline has no user confirmation row — "
                    "CLOSE first row must be marked with --owner user"))
        return

    # A prior explicit user confirmation is the interactive/fail-closed CLOSE
    # admission.  Do not require a second --owner user on the first CLOSE row:
    # that would make a completed confirmation ineffective and would also make
    # `advance` impossible despite the owner already having approved the gate.
    if prev_user_row["status"] != "done" or prev_user_row.get("owner") != "user":
        err(command, "close_gate_violation",
            violation_detail=(
                f"user confirmation row {prev_user_row['row_id']} is not done with owner=user "
                f"(status={prev_user_row['status']}, owner={prev_user_row.get('owner')})"
            ))

# ─────────────────────────────────────────────────────────────────────────────
# PM Gate 아티팩트 검증 (091 F-004 R-11, PLAN §3.4.2 (2))
# ─────────────────────────────────────────────────────────────────────────────

def _is_safe_artifact_token(t):
    """gate.artifacts 토큰의 태스크 폴더 밖 이탈 여부 검사 (H-4).
    절대경로이거나 '..' 파트를 포함하면 안전하지 않음 → False."""
    pp = pathlib.PurePosixPath(t)
    if pp.is_absolute():
        return False
    if ".." in pp.parts:
        return False
    return True

def check_gate_artifacts(task_path, row, command, force=False):
    """091 R-11: gate.artifacts 존재 검증. 미충족 시 gate_artifact_missing으로 mark 거부.
    gate 미보유 행 또는 artifacts가 빈 배열이면 즉시 return — 기존 동작 불변(H-3)."""
    gate = row.get("gate")
    if not isinstance(gate, dict):
        return None
    tokens = gate.get("artifacts") or []
    if not tokens:
        return None
    base = pathlib.Path(task_path)
    missing = []
    for t in tokens:
        if not _is_safe_artifact_token(t):        # 절대경로·상위경로 토큰 거부 (H-4)
            missing.append(t)
            continue
        if any(c in t for c in "*?["):
            if not any(base.glob(t)):
                missing.append(t)
        elif not (base / t).exists():
            missing.append(t)
    if not missing:
        return None
    if force:
        return missing                            # 우회 — 호출자가 의사결정 로그에 기재
    err(command, "gate_artifact_missing",
        row_id=row["row_id"], key=row.get("key"), missing=missing)

def build_gate_payload(row):
    """091 R-11(b): 게이트 통과 시 stdout으로 반환할 checklist 페이로드.
    dict로 감싼다 — todo_mirror_hook._extract_payload가 dict만 통과시킨다(H-6)."""
    gate = row.get("gate")
    if not isinstance(gate, dict):
        return None
    return {
        "key":       row.get("key"),
        "stage":     row["stage"],
        "item":      row["item"],
        "artifacts": gate.get("artifacts") or [],
        "checklist": gate.get("checklist") or [],
        "reminder":  "[PM Gate 점검] 아래 checklist 전 항목을 확인한 뒤 다음 단계로 진행하라. "
                     "SSOT는 해당 pilot references/pipeline.json task_steps[].gate 이다.",
    }

# ─────────────────────────────────────────────────────────────────────────────
# 행 주입 공통 처리 (PLAN §2.20)
# ─────────────────────────────────────────────────────────────────────────────

def build_rows_from_spec(spec_json_str, command, mode):
    """--rows-spec inline JSON → rows[] 반환 (§2.20.1)."""
    try:
        items = json.loads(spec_json_str)
    except json.JSONDecodeError as e:
        err(command, "rows_spec_invalid_json", detail=str(e))
    if not isinstance(items, list):
        err(command, "rows_spec_invalid_json", detail="top-level not array")

    rows = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            err(command, "rows_spec_invalid_json", detail=f"item[{i}] is not object")
        stage = item.get("stage")
        name  = item.get("item")
        if not stage or not name:
            err(command, "rows_spec_invalid_json",
                detail=f"item[{i}] missing 'stage' or 'item'")
        if stage not in STAGE_ENUM:
            err(command, "rows_spec_invalid_json",
                detail=f"item[{i}].stage '{stage}' not in enum")
        if len(name) < 1:
            err(command, "rows_spec_invalid_json",
                detail=f"item[{i}].item is empty")

        owner_default = item.get("owner_default", "PM")
        row = {
            "row_id":       i + 1,
            "stage":        stage,
            "item":         name,
            "status":       "pending",
            "status_label": "⬜",
            "timestamp":    None,
            "owner":        owner_default,
            "note":         None,
        }
        if item.get("gate"):
            row["gate"] = item["gate"]  # 091 F-004 R-9(a): --rows-spec 인라인 경로도 동형 지원

        rows.append(row)
    return rows

def build_rows_from_skill_md(skill_md_path, command, mode):
    """--rows-from SKILL.md 파싱 → rows[] 반환 (§2.20.2 10단계)."""
    p = pathlib.Path(skill_md_path)
    if not p.exists():
        err(command, "skill_md_parse_error", path=str(p), reason="file not found")

    # 단계 1: 파일 읽기
    content = p.read_text(encoding="utf-8")

    # 단계 2: 헤더 패턴 매칭
    header_pattern = re.compile(
        r"^(##|###|####)\s+.*STATE\.md\s*도메인\s*치환값.*$",
        re.MULTILINE
    )
    hm = header_pattern.search(content)
    if not hm:
        err(command, "skill_md_parse_error",
            path=str(p), reason="header not found")

    # 단계 3: 헤더 이후 섹션 본문 추출
    section_start = hm.end()
    # 다음 같은 레벨 또는 상위 헤더 직전까지
    level = len(hm.group(1))  # ## → 2, ### → 3 등
    next_header_pattern = re.compile(
        r"^#{1," + str(level) + r"}\s+",
        re.MULTILINE
    )
    nh = next_header_pattern.search(content, section_start)
    section = content[section_start: nh.start() if nh else len(content)]

    # 단계 4: 마크다운 표 헤더 식별
    table_header_pattern = re.compile(
        r"^\|\s*#\s*\|\s*(?:단계|Phase)\s*\|\s*항목\s*\|",
        re.MULTILINE
    )
    thm = table_header_pattern.search(section)
    if not thm:
        err(command, "skill_md_parse_error",
            path=str(p), reason="table header not found")

    # 단계 5: 구분선 다음부터 데이터 행 추출
    after_header_pos = thm.end()
    # 구분선 건너뛰기
    sep_end = section.find("\n", after_header_pos)
    sep_end2 = section.find("\n", sep_end + 1)
    data_text = section[sep_end2 + 1:]

    # 단계 6: 각 행 파싱
    row_pattern = re.compile(
        r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([⬜🔄✅❌\-])\s*\|",
        re.MULTILINE
    )
    matches = row_pattern.findall(data_text)

    # 단계 7: 0건이면 에러
    if not matches:
        err(command, "skill_md_parse_error",
            path=str(p), reason="no rows found")

    rows = []
    for i, (rid, stage, item, status_label) in enumerate(matches):
        stage = stage.strip()
        item  = item.strip()

        # 단계 9: stage enum 검증
        if stage not in STAGE_ENUM:
            err(command, "invalid_stage_enum",
                value=stage, detail=f"row {rid}")

        # 단계 8: status_label → status 매핑
        status = LABEL_STATUS_MAP.get(status_label, "pending")

        row = {
            "row_id":       i + 1,
            "stage":        stage,
            "item":         item,
            "status":       "pending",  # init 시 모두 pending으로 초기화
            "status_label": "⬜",
            "timestamp":    None,
            "owner":        "PM",
            "note":         None,
        }
        rows.append(row)
    return rows

# ─────────────────────────────────────────────────────────────────────────────
# pipeline.json 스펙 로딩·검증 (070 F-001/F-002, PLAN §3.1.2/§3.2.2)
# ─────────────────────────────────────────────────────────────────────────────

def load_pipeline_spec(spec_path, command):
    """pipeline.json 로드. 없으면 spec_file_not_found, 파싱 실패 시 spec_invalid_json."""
    p = pathlib.Path(spec_path)
    if not p.exists():
        err(command, "spec_file_not_found", path=str(p))
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(command, "spec_invalid_json", detail=str(e))


def validate_pipeline_spec(spec):
    """pipeline.json 스펙 검증 → violations[] (070 F-001 R-1/R-6, PLAN §3.1.2 DEC-2).

    검사 항목:
    ① 필수 필드(spec_version/skill/meta/task_steps) 존재       → spec_missing_field
    ② skill enum 정합                                          → spec_skill_invalid
    ③ task_steps[].stage ∈ STAGE_ENUM                          → spec_stage_invalid
    ④ key 형식(KEY_PATTERN)                                    → spec_key_format_invalid
    ⑤ key 유일성(스펙 내)                                       → spec_key_duplicate
    ⑥ id 1..N 순차                                              → spec_id_sequence_invalid
    ⑦ key의 stage_slug가 실제 stage와 정합                     → spec_key_stage_mismatch
    반환: [{code, id?, key?, detail}] (cmd_validate violations 포맷 차용)
    """
    violations = []

    required_top = ["spec_version", "skill", "meta", "task_steps"]
    for f in required_top:
        if f not in spec:
            violations.append({"code": "spec_missing_field", "detail": f"missing field: {f}"})
    if violations:
        # 최상위 필수 필드가 없으면 하위 검사(task_steps 순회 등)는 의미가 없다
        return violations

    skill_enum = ["opp", "opd", "opds", "opdw", "opwt", "opgc", "oppd", "opsdd", "oppl", "opdd", "oppb"]  # 132 W-3보강: oppb spec-validate 허용 (P9 pipeline.json skill='oppb')
    if spec.get("skill") not in skill_enum:
        violations.append({"code": "spec_skill_invalid", "detail": f"skill '{spec.get('skill')}' not in enum"})

    task_steps = spec.get("task_steps") or []
    seen_keys = {}
    for idx, ts in enumerate(task_steps):
        ts_id = ts.get("id")
        ts_key = ts.get("key")
        ts_stage = ts.get("stage")

        if ts_stage not in STAGE_ENUM:
            violations.append({"code": "spec_stage_invalid", "id": ts_id, "key": ts_key,
                                "detail": f"stage '{ts_stage}' not in STAGE_ENUM"})

        if ts_key is not None:
            if not KEY_PATTERN.match(ts_key):
                violations.append({"code": "spec_key_format_invalid", "id": ts_id, "key": ts_key,
                                    "detail": f"key '{ts_key}' does not match pattern"})
            if ts_key in seen_keys:
                violations.append({"code": "spec_key_duplicate", "id": ts_id, "key": ts_key,
                                    "detail": f"key '{ts_key}' duplicated (also id {seen_keys[ts_key]})"})
            else:
                seen_keys[ts_key] = ts_id

            if ts_stage in STAGE_ENUM and "." in ts_key:
                expected_slug = stage_to_slug(ts_stage)
                actual_slug = ts_key.split(".", 1)[0]
                if actual_slug != expected_slug:
                    violations.append({"code": "spec_key_stage_mismatch", "id": ts_id, "key": ts_key,
                                        "detail": f"key stage_slug '{actual_slug}' != stage_to_slug('{ts_stage}')='{expected_slug}'"})

        if ts_id != idx + 1:
            violations.append({"code": "spec_id_sequence_invalid", "id": ts_id, "key": ts_key,
                                "detail": f"expected id {idx + 1}, got {ts_id}"})

        # 091 F-004 R-10: task_steps[].gate 검사 4건 (PLAN §3.4.2 (1))
        gate = ts.get("gate")
        if gate is not None:
            if not isinstance(gate, dict):
                violations.append({"code": "spec_gate_type_invalid", "id": ts_id, "key": ts_key,
                                   "detail": f"gate must be object, got {type(gate).__name__}"})
            else:
                for f in ("artifacts", "checklist"):
                    if f not in gate:
                        violations.append({"code": "spec_gate_missing_field", "id": ts_id, "key": ts_key,
                                           "detail": f"gate missing field: {f}"})
                    elif not isinstance(gate[f], list) or any(not isinstance(x, str) for x in gate[f]):
                        violations.append({"code": "spec_gate_field_type_invalid", "id": ts_id, "key": ts_key,
                                           "detail": f"gate.{f} must be array of string"})
                if isinstance(gate.get("checklist"), list) and len(gate["checklist"]) == 0:
                    violations.append({"code": "spec_gate_checklist_empty", "id": ts_id, "key": ts_key,
                                       "detail": "gate.checklist must not be empty"})

    return violations


def build_rows_from_pipeline_json(spec_path, command, mode):
    """.json 스펙 → rows[] (070 F-002 R-2, PLAN §3.2.2). 절차:
    1. spec = load_pipeline_spec(spec_path, command)
    2. violations = validate_pipeline_spec(spec); 있으면 spec_validation_failed
    3. task_steps[] 순회하며 row 구성(key·conditional 영속. 093 F-001 이후 모드별 분기 없음
       — 사용자 확인 행도 전 모드 pending/PM으로 초기화되고 자동 승인은 진입 훅이 담당)
    """
    spec = load_pipeline_spec(spec_path, command)
    violations = validate_pipeline_spec(spec)
    if violations:
        err(command, "spec_validation_failed", detail=violations[0])

    rows = []
    for i, ts in enumerate(spec["task_steps"]):
        row = {
            "row_id":       i + 1,
            "stage":        ts["stage"],
            "item":         ts["item"],
            "key":          ts["key"],
            "status":       "pending",
            "status_label": "⬜",
            "timestamp":    None,
            "owner":        "PM",
            "note":         None,
        }
        if ts.get("conditional"):
            row["conditional"] = True  # DEC-1 — 순수 메타데이터, 자동 na 없음
        if ts.get("gate"):
            row["gate"] = ts["gate"]  # 091 F-004 R-9(a): init-time 정적 스냅샷 영속화

        rows.append(row)
    return rows

# ─────────────────────────────────────────────────────────────────────────────
# 9개 서브 명령 구현
# ─────────────────────────────────────────────────────────────────────────────

# ── 1. init ──────────────────────────────────────────────────────────────────

def _resolve_active_channel(args, command):
    """135 W-4 (H-4) — active init의 채널 배정 조회.

    [MUST 범위] 호출자가 **명시적으로 전달한** `--profiles` 파일에 `--channel-id`
    항목이 있을 때만 채널을 반환한다. `profiles.json`을 새로 만들거나 배포하지
    않으며, channel을 자동 승격하지도 않는다 — 미승인 channel(또는 `--profiles`
    미지정)은 그대로 `profile_not_found`로 거부한다(RED 회귀 가드).
    """
    channel_id = getattr(args, "channel_id", None)
    profiles_arg = getattr(args, "profiles", None)
    if not profiles_arg or not channel_id:
        return None
    try:
        profiles_data = json.loads(pathlib.Path(profiles_arg).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(profiles_data, dict):
        return None
    for channel in profiles_data.get("channels") or []:
        if isinstance(channel, dict) and channel.get("channel_id") == channel_id:
            return channel
    return None


def _cmd_init_run_log(task_path, args, state, command):
    """--run-log-mode 처리 (CONTRACT §2.5 state-tool.init.run-log-mode).

    shadow는 항상 지원한다. active는 호출자가 명시적으로 넘긴 `--profiles`
    파일에 `--channel-id` 항목이 있을 때만 수용하고(_resolve_active_channel,
    H-4), 그 외에는 기존과 동일하게 `profile_not_found`로 거부한다 — 배정
    자동화·profiles.json 자체 생성은 이 범위에 포함하지 않는다.

    성공 시 `state`를 in-place로 갱신하고(schema_version="1.2" + run_log 블록),
    outbox 2단 커밋(TRD 데이터 흐름 (a))을 그대로 밟는다 — 1차 원자 쓰기(status=pending +
    run.started 보관함 적재) → run/ 디렉터리·첫 조각 생성 + 같은 event_id로 append →
    2차 원자 쓰기(보관함 비우고 status=active). ok() 응답에 병합할
    {run_id, run_log, status} 딕셔너리를 반환한다.
    """
    active_channel = None
    if args.run_log_mode == "active":
        active_channel = _resolve_active_channel(args, command)
        if active_channel is None:
            err(command, "profile_not_found", channel_id=args.channel_id or "(미지정)")

    run_log_core = _import_run_log_core()

    run_id = run_log_core.new_run_id()
    request_id = f"req_{uuid.uuid4()}"
    event_id = run_log_core.new_event_id()
    ts = run_log_core.utc_now_ms()

    # CONTRACT §1.1 run.started 필수 필드 전건 — 사전 확정(D-E, §1.3 A7 "사전 확정 event ID").
    started_event = {
        "schema_version": "1.0",
        "event_id": event_id,
        "request_id": request_id,
        "task_id": task_path.name,
        "run_id": run_id,
        "parent_run_id": None,
        "worker_run_id": None,
        "caused_by_event_id": None,
        "stage": None,
        "task_step": None,
        "work_item": None,
        "gate_id": None,
        "event": "run.started",
        "actor": {"kind": "tool", "id": "state-tool", "provider": None,
                  "session_id": _current_session_id()},  # 138 W-9
        "provenance": {
            "type": "direct",
            "recorded_by": {"kind": "tool", "id": "state-tool"},
            "worker_log_token_id": None,
            "source": None,
        },
        "summary": "run started (shadow)",
        "reason": None,
        "reason_code": None,
        "duration_ms": None,
        "duration_source": None,
        "duration_unknown_reason": None,
        "refs": None,
        "timestamp": ts,
    }

    if active_channel is not None:
        completion_profile_receipt = {
            "channel_id": active_channel.get("channel_id"),
            "adapter_id": active_channel.get("adapter_id"),
            "adapter_sha256": active_channel.get("adapter_sha256"),
            "receipt_sha256": active_channel.get("receipt_sha256"),
        }
        run_log_block = {
            "contract_version": "1.0",
            "mode": "active",
            "completion_profile": active_channel.get("completion_profile", "cooperative"),
            "completion_profile_receipt": completion_profile_receipt,
            "active_run_id": run_id,
            "status": "pending",
            "pending_events": [started_event],
        }
    else:
        run_log_block = {
            "contract_version": "1.0",
            "mode": "shadow",
            "completion_profile": "cooperative",
            "completion_profile_receipt": None,
            "active_run_id": run_id,
            "status": "pending",
            "pending_events": [started_event],
        }
    state["schema_version"] = "1.2"
    state["run_log"] = run_log_block

    # 1차 원자 쓰기 — status=pending + run.started 보관함 적재
    _atomic_write_state_json(task_path, state)

    with run_log_core.task_lock(str(task_path)) as acquired:
        if not acquired:
            err(command, "task_lock_timeout", path=str(task_path))

        init_result = run_log_core.init(str(task_path), run_id, lock_held=True)
        if not init_result.get("ok"):
            e = init_result.get("error", {})
            err(command, e.get("code", "run_log_write_failed"), message=e.get("message"))

        append_result = run_log_core.append(str(task_path), run_id, started_event, lock_held=True)
        if not append_result.get("ok"):
            e = append_result.get("error", {})
            err(command, e.get("code", "run_log_write_failed"), message=e.get("message"))

        # 2차 원자 쓰기 — 보관함 비우고 status=active
        run_log_block["status"] = "active"
        run_log_block["pending_events"] = []
        _atomic_write_state_json(task_path, state)

    return {"run_id": run_id, "run_log": run_log_block, "status": run_log_block["status"]}


def cmd_init(args):
    """PLAN §2.11 G-8 — state.json + STATE.md 생성"""
    command = "init"
    # init은 신규 태스크 폴더를 최초 초기화하는 명령이므로, 상위 디렉토리가 쓰기
    # 가능하면 리프 디렉토리를 자동 생성한다(하위호환: 기존 디렉토리 존재 시 무해,
    # 생성 불가 시 기존과 동일하게 task_path_not_found).
    _p = pathlib.Path(args.task_path)
    if not _p.is_dir():
        try:
            _p.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass  # 아래 resolve_task_path가 동일하게 task_path_not_found 처리
    task_path = resolve_task_path(args.task_path, command)

    # 156 DEC-4/DEC-8: actor·workspace 게이트는 state.json/STATE.md 기록 이전에 검증한다.
    actor = getattr(args, "actor", None)
    if actor == "pm":
        err(command, "actor_pm_retired")
    if actor and args.skill not in ACTOR_SKILLS:
        err(command, "actor_unsupported_for_skill", skill=args.skill)
    workspace = getattr(args, "workspace", None)
    if workspace == "worktree" and not getattr(args, "worktree", None):
        err(command, "worktree_path_required")
    if workspace == "hub" and args.skill in WORKSPACE_REQUIRED_SKILLS:
        err(command, "workspace_required_for_skill", skill=args.skill)

    # --rows-acts 시그니처 정의만 (§2.20.3, R-13)
    if getattr(args, "rows_acts", None):
        err(command, "rows_acts_not_implemented",
            note="opsdd ACT dynamic injection is out of scope for task 134. Track at R-13.",
            exit_code=2)

    # 094 R-4/D-2: --import-existing 제거 — STATE.md 저널화로 파싱 대상(파이프라인
    # 표)이 소멸했으므로 명시적으로 거부한다. argparse 정의는 하위 호환을 위해
    # 유지하되 help는 감춘다(§3.2.2 (2)).
    if getattr(args, "import_existing", False):
        err(command, "import_existing_removed")

    # C-1: --rows-spec / --rows-from 배타 (§2.19)
    if args.rows_spec and args.rows_from:
        err(command, "rows_input_conflict")

    state_file = task_path / "state.json"

    # C-4: --force 사용 시 --note 필수 (§2.17 트리거 #1)
    if args.force and not args.note:
        err(command, "note_required_for_force")

    # 멱등성 검증 (T-8)
    if state_file.exists() and not args.force and not args.import_existing:
        err(command, "already_initialized")

    # 시점 취득 (T-5)
    now_str = get_kst_datetime(command)

    # 행 구성 결정
    rows = []

    if args.rows_spec:
        rows = build_rows_from_spec(args.rows_spec, command, args.mode)
    elif args.rows_from:
        # 070 R-2: --rows-from 확장자 분기 — .json(신규 pipeline.json 스펙) vs
        # .md(레거시 SKILL.md 파싱, deprecated stderr 경고 1줄).
        if args.rows_from.endswith(".json"):
            rows = build_rows_from_pipeline_json(args.rows_from, command, args.mode)
        else:
            print('{"warning":"--rows-from <SKILL.md> markdown 파싱은 deprecated. '
                  'references/pipeline.json으로 이관하세요 (task 070)."}', file=sys.stderr)
            rows = build_rows_from_skill_md(args.rows_from, command, args.mode)
    else:
        # 행 없이 init — 최소 1행 빈 구조는 허용 안 함, 경고 없이 빈 rows로 진행
        rows = []

    # task_id = 마지막 디렉토리명
    task_id = task_path.name

    # 070 후속 R-3: rows[]에 key가 하나라도 있으면(pipeline.json 경로) schema_version
    # "1.1" 승격. .md 파싱/--rows-spec/--import-existing(key 없음) 경로는 "1.0" 유지.
    # 단순·결정론 규칙(PLAN §3.2.2 diff, task 070 후속 Part B).
    schema_version = "1.1" if any(r.get("key") for r in rows) else "1.0"

    # 072 F-001: '다음 액션' state.json 영속화 (R-1) — 계산식은 기존 관례 그대로 재사용
    next_action = args.next_action or "PLAN 단계 진입"

    state = {
        "task_id":        task_id,
        "skill":          args.skill,
        "mode":           args.mode,
        "schema_version": schema_version,
        "created_at":     now_str,
        "updated_at":     now_str,
        "current_status": "in_progress",
        "rows":           rows,
        "next_action":    next_action,
    }

    # 092 F-5: worktree 경로 조건부 영속화.
    # [MUST] 미지정 시 키 자체를 생성하지 않는다 — 기존 state.json과 스키마·바이트 동일(TASK F-5 AC).
    if getattr(args, "worktree", None):
        state["worktree"] = args.worktree

    # 122 W-2 (D-4): actor 조건부 영속화 — --worktree(위 092 F-5)와 동형 패턴.
    # [MUST] 미지정 시 키 자체를 생성하지 않는다(S-1 회귀 보존, AC-4).
    if getattr(args, "actor", None):
        state["actor"] = args.actor

    # force 사용 시 기존 state.json의 created_at 보존
    if state_file.exists() and args.force:
        try:
            old = json.loads(state_file.read_text(encoding="utf-8"))
            state["created_at"] = old.get("created_at", now_str)
        except Exception:
            pass

    # 기본값 shadow(135 ADD-2) — `off`를 명시했을 때만 기존 1.1 경로를 그대로
    # 타고, 그 외에는 run-log 2단 커밋 경로로 분기한다.
    run_log_response_fields = {}
    if getattr(args, "run_log_mode", None) not in (None, "off"):
        run_log_response_fields = _cmd_init_run_log(task_path, args, state, command)
    else:
        save_state_json(task_path, state)

    # 094 §3.2.2 (2): STATE.md 저널 생성 (import 분기 소멸 — 항상 신규 템플릿)
    task_title = args.task_title or task_id
    new_md = _build_new_state_md(task_title, now_str)
    save_state_md(task_path, new_md)

    # force 사용 시 의사결정 로그 기재 (§2.17 트리거 #1)
    if args.force:
        updated_md = load_state_md(task_path)
        updated_md = append_decision_log(
            updated_md, now_str,
            "force flag used at init",
            resolve_owner_placeholder(args.note)
        )
        save_state_md(task_path, updated_md)

    ok(command,
       task_path=str(task_path),
       task_id=task_id,
       rows_count=len(rows),
       created_at=now_str,
       # 094 D-2: --import-existing 제거 후에도 응답 키는 유지하고 값만 고정(제약 ③)
       import_existing=False,
       todo_mirror=build_todo_mirror(state, "create"),
       **run_log_response_fields)


def _build_new_state_md(task_title, now_str):
    """신규 STATE.md 저널 템플릿 생성 (094 §3.1.2 (1), D-1).
    파생 섹션(마커/파이프라인 표/'## 현재 상태'/'## 다음 액션')을 전부 제거하고
    의사결정 로그·블로커만 남긴 저널로 재정의한다. 기계 상태(rows/현재 상태/
    다음 액션)의 SSOT는 state.json 단일이며, 조회는 `state-tool show`로 일원화된다."""
    return f"""# STATE: {task_title}

> 최종 갱신: {now_str}
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|

## 블로커
없음
"""

# ── 2. show ───────────────────────────────────────────────────────────────────

def cmd_show(args):
    """094 §3.3.2 — 파이프라인 현황 조회. R-5: state.json이 파생 표시의 유일한
    렌더 원천이다(md/json 공통). 레거시(001~093, 마커+표 보유) STATE.md는 동결
    텍스트로만 취급되며 절대 최신 현황으로 오반환되지 않는다(H-5)."""
    command = "show"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)
    fmt       = getattr(args, "format", "md") or "md"

    md = load_state_md(task_path)
    legacy = bool(md) and (PIPELINE_MARKER_START in md and PIPELINE_MARKER_END in md)

    if fmt == "json":
        ok(command, format="json", marker_present=legacy, data=state,
           mode=state.get("mode"), current_status=state.get("current_status"),
           _transition_state=state)
        return

    if fmt == "full":
        if md is None:
            ok(command, format="full", content="(STATE.md 없음)",
               _transition_state=state)
            return
        banner = (LEGACY_FROZEN_BANNER + "\n\n") if legacy else ""
        ok(command, format="full", content=banner + md,
           _transition_state=state)
        return

    # md (기본) — state.json 단일 파생(§3.3.2 (1))
    head = [
        "## 현재 상태",
        f"- 모드: {state.get('mode')}",
        f"- 상태: {STATUS_TEXT.get(state.get('current_status'), state.get('current_status'))}",
        f"- 다음 액션: {state.get('next_action') or '-'}",
        "",
    ]
    body = render_pipeline_table(state["rows"])
    banner = (LEGACY_FROZEN_BANNER + "\n\n") if legacy else ""
    ok(command, format="md", marker_present=legacy,
       content=banner + "\n".join(head) + body,
       _transition_state=state)

# ── 3. advance ────────────────────────────────────────────────────────────────

def _load_state_for_resolve(command, task_path):
    state_file = task_path / "state.json"
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        err(command, "state_json_malformed", message=str(exc))
    if not isinstance(state, dict):
        err(command, "state_json_malformed",
            message="state.json top-level value must be an object")
    return state


def _persist_mode_override(command, task_path, state, effective_mode):
    """기존 태스크의 명시 mode override — mode만 원자 갱신한다(modes.md 라우팅 계약 3)."""
    previous_mode = state.get("mode")
    persisted = previous_mode != effective_mode
    journal_warning = None
    if persisted:
        now_str = get_kst_datetime(command)
        state["mode"] = effective_mode
        save_state_json_atomic(task_path, state)
        journal_warning = sync_state_md(
            task_path, state, now_str, command,
            decision=f"mode override: {previous_mode!r} -> {effective_mode}",
            reason="source=explicit; user --mode flag",
        )
    return persisted, journal_warning


def cmd_resolve_mode(args):
    """Resolve explicit > stored valid mode > new-task default(Pilot별 표, 미지정 semi-agentic)."""
    command = "resolve-mode"
    task_path = pathlib.Path(args.task_path).resolve()
    state_file = task_path / "state.json"

    if not state_file.exists():
        if not args.new_task:
            if not task_path.is_dir():
                err(command, "task_path_not_found", path=str(task_path))
            err(command, "state_not_initialized")
        default_mode = (new_task_defaults(args.skill)["mode"]
                        if getattr(args, "skill", None) else "semi-agentic")
        effective_mode = args.mode or default_mode
        source = "explicit" if args.mode else "default"
        ok(command, effective_mode=effective_mode, source=source,
           persisted=False, previous_mode=None, old_mode=None,
           new_mode=effective_mode, warnings=[])
        return

    state = _load_state_for_resolve(command, task_path)
    previous_mode = state.get("mode")
    stored_mode, stored_source, warnings = normalize_stored_mode(previous_mode)
    if args.mode is None:
        ok(command, effective_mode=stored_mode, source=stored_source,
           persisted=False, previous_mode=previous_mode,
           old_mode=previous_mode, new_mode=stored_mode, warnings=warnings)
        return

    effective_mode = args.mode
    persisted, journal_warning = _persist_mode_override(command, task_path, state, effective_mode)
    payload = dict(
        effective_mode=effective_mode, source="explicit", persisted=persisted,
        previous_mode=previous_mode, old_mode=previous_mode,
        new_mode=effective_mode, warnings=[],
    )
    if journal_warning:
        payload.update(journal_warning)
    ok(command, **payload)


# 157 DEC-1: tools/state-tool → 루트(소스 opal/, 설치본 ~/.opal/) 아래 skills/ 형제 배치(H-1).
_PILOT_DEV_REFS_DIR = (
    pathlib.Path(__file__).resolve().parent.parent.parent
    / "skills" / "opal-pilot-dev" / "references")


def _pilot_dev_pipeline_path(skill, actor):
    """DEC-1 — coordinator→pipeline-pm.json, worker+opd→pipeline.json, worker+opds→pipeline-short.json."""
    if actor == "coordinator":
        name = "pipeline-pm.json"
    elif skill == "opd":
        name = "pipeline.json"
    else:
        name = "pipeline-short.json"
    return _PILOT_DEV_REFS_DIR / name


def cmd_resolve_start(args):
    """156 DEC-2/DEC-3 — Pilot 시작·재개의 mode·workspace·actor 세 축 판정.

    신규(--new-task)는 읽기 전용이며 state init 인자를 돌려준다. 재개는 저장값을 상속하고,
    저장값과 다른 workspace·actor 플래그는 resume_axis_locked로 거부한다. 재개 중 명시
    mode 플래그만 resolve-mode와 같은 원자 갱신을 수행한다."""
    command = "resolve-start"
    skill = args.skill
    mode_flags = [m for m, on in (("interactive", args.interactive),
                                  ("semi-agentic", args.semi_agentic),
                                  ("agentic", args.agentic)) if on]
    if len(mode_flags) > 1:
        err(command, "mode_flag_conflict")
    if args.wt and args.no_wt:
        err(command, "workspace_flag_conflict")
    if args.pm and args.no_pm:
        err(command, "actor_flag_conflict")
    explicit_mode = mode_flags[0] if mode_flags else None
    explicit_ws = "worktree" if args.wt else ("hub" if args.no_wt else None)
    explicit_actor = "coordinator" if args.pm else ("worker" if args.no_pm else None)

    task_path = pathlib.Path(args.task_path).resolve()
    state_file = task_path / "state.json"
    warnings = []

    if state_file.exists() and not args.new_task:
        state = _load_state_for_resolve(command, task_path)
        stored_ws = "worktree" if state.get("worktree") else "hub"
        if "actor" in state:
            stored_actor, actor_source = state.get("actor"), "state"
        else:
            stored_actor, actor_source = "worker", "legacy_default"
        if explicit_ws and explicit_ws != stored_ws:
            err(command, "resume_axis_locked", axis="workspace",
                stored=stored_ws, requested=explicit_ws)
        if explicit_actor and explicit_actor != stored_actor:
            err(command, "resume_axis_locked", axis="actor",
                stored=stored_actor, requested=explicit_actor)
        payload = dict(workspace=stored_ws, workspace_source="state",
                       actor=stored_actor, actor_source=actor_source)
        if explicit_mode:
            persisted, journal_warning = _persist_mode_override(
                command, task_path, state, explicit_mode)
            payload.update(effective_mode=explicit_mode, mode_source="explicit",
                           persisted=persisted)
            if journal_warning:
                payload.update(journal_warning)
        else:
            mode, mode_source, mode_warnings = normalize_stored_mode(state.get("mode"))
            warnings.extend(mode_warnings)
            payload.update(effective_mode=mode, mode_source=mode_source, persisted=False)
        ok(command, skill=skill, new_task=False, warnings=warnings, **payload)
        return

    if not args.new_task:
        if not task_path.is_dir():
            err(command, "task_path_not_found", path=str(task_path))
        err(command, "state_not_initialized")

    defaults = new_task_defaults(skill)
    if explicit_actor and skill not in ACTOR_SKILLS:
        if args.pm:
            err(command, "actor_unsupported_for_skill", skill=skill)
        warnings.append({"code": "no_pm_redundant", "skill": skill})
        explicit_actor = None
    if explicit_ws == "hub" and skill in WORKSPACE_REQUIRED_SKILLS:
        err(command, "workspace_required_for_skill", skill=skill)

    mode = explicit_mode or defaults["mode"]
    workspace = explicit_ws or defaults["workspace"]
    if skill in ACTOR_SKILLS:
        actor = explicit_actor or defaults["actor"]
        actor_source = "explicit" if explicit_actor else "default"
    else:
        actor, actor_source = "worker", "default"

    init_args = ["--skill", skill, "--mode", mode, "--workspace", workspace]
    if skill in ACTOR_SKILLS:
        init_args += ["--actor", actor]
        # 157 DEC-1: opd/opds 신규는 파이프라인 파일까지 도구가 판정한다. 재개 응답과
        #   다른 Pilot의 init_args는 불변이다.
        rows_from = _pilot_dev_pipeline_path(skill, actor)
        if not rows_from.is_file():
            err(command, "spec_file_not_found", path=str(rows_from))
        init_args += ["--rows-from", str(rows_from)]
    ok(command, skill=skill, new_task=True,
       effective_mode=mode, mode_source="explicit" if explicit_mode else "default",
       workspace=workspace, workspace_source="explicit" if explicit_ws else "default",
       actor=actor, actor_source=actor_source, persisted=False,
       init_args=init_args, warnings=warnings)


def cmd_advance(args):
    """PLAN §2.1, T-7 — ⬜→🔄 전환"""
    command = "advance"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)
    # 138 W-9: 상태 전이 진입 경계에서만 lease를 claim한다(init은 claim하지 않는다).
    _claim_task_lease_if_needed(task_path)
    row_index = resolve_row_index(state, command,
                                  getattr(args, "task_step", None),
                                  getattr(args, "task_step_id", None),
                                  args.row)
    row       = state["rows"][row_index]

    if row["status"] not in ("pending",):
        err(command, "row_not_found",
            message=f"row {row['row_id']} is already {row['status']}, advance only allows pending→in_progress",
            row_id=row["row_id"])

    # 157 W-2: advance --force(설계 게이트 가드 우회 불가 검증용 표면)도 mark와 같이 --note 필수.
    if getattr(args, "force", False) and not args.note:
        err(command, "note_required_for_force")

    # 단계 건너뛰기 차단 (PLAN §M-A)
    # PM 경로: 앞 모든 행 검증 (full). 워커 경로: 앞 단계 행만 검증 (prior_stage_only).
    _guard_scope = "prior_stage_only" if getattr(args, "as_worker", False) else "full"

    # 093 F-002 R-2: 앞 단계 미완 사용자 확인 행 자동 승인 (stage-transition guard보다 먼저)
    now_str = get_kst_datetime(command)
    # W-2/D-3: auto_approve_prior_user_confirmations()가 in-place로 status를 done
    # 갱신하므로, 각 행의 갱신 전 상태(data.from)를 먼저 스냅샷해 둔다.
    _rl_prior_status_by_row_id = {r["row_id"]: r.get("status") for r in state["rows"][:row_index]}
    auto_approved = auto_approve_prior_user_confirmations(
        state, row_index, command,
        as_worker=getattr(args, "as_worker", False),
        force=getattr(args, "force", False), now_str=now_str)

    # 157 DEC-6/DEC-11: PM 경로 확인 해시 기록·EXECUTE 진입 가드(자동 승인 직후·저장 전,
    #   --force 우회 불가). PM 경로가 아니면 no-op.
    apply_pm_design_guards(task_path, state, row_index, command,
                           auto_approved=auto_approved, target_done=False)

    check_stage_transition_guard(state, row_index, command, force=False,
                                 scope=_guard_scope)

    # CLOSE 진입 게이트 (§2.16 G-13) — 선행 행이 모두 완료된 뒤 판정한다.
    check_close_gate(state, row_index, command)

    # CLOSE/PM Gate artifacts must reject an advance before any in-memory auto
    # approval can be persisted.  This mirrors cmd_mark's pre-save guard.
    check_gate_artifacts(task_path, row, command,
                         force=getattr(args, "force", False))

    # 005 명확화 게이트 — TASK→다음 단계 첫 행 진입 차단 (상태 변경 전)
    _run_clarification_hook(task_path, state, row_index, command,
                            auto_pass=getattr(args, "auto_pass", False),
                            force=getattr(args, "force", False))

    # 106 code-scan 인용 게이트 — EXECUTE 첫 행 진입 차단 (save_state_json() 이전)
    _run_code_scan_citation_hook(task_path, state, row_index, command,
                                 auto_pass=getattr(args, "auto_pass", False),
                                 force=getattr(args, "force", False))

    row["status"]       = "in_progress"
    row["status_label"] = "🔄"
    row["timestamp"]    = now_str
    if args.note:
        row["note"] = resolve_owner_placeholder(args.note)

    state["updated_at"] = now_str

    # 072 F-002/F-003: '다음 액션' 자동 파생(프론티어) + --next-action 오버라이드(비지속, M-3)
    state["next_action"] = getattr(args, "next_action", None) or _derive_next_action(state)
    # T05/D-3: 1.2 태스크는 자동 승인된 각 행 + 대상 행 전이를 각각 독립
    #   state.changed로 만들어 한 번의 admission·원자 쓰기로 커밋한다(W-2, H-1).
    #   1.0/1.1 태스크는 run_log_commit()이 곧바로 save_state_json()으로 우회하므로
    #   산출물·응답 키 집합이 종전과 동일하다(C-3).
    _rl_events = [
        build_state_changed_event(
            state, task_id=task_path.name, command=command,
            from_status=_rl_prior_status_by_row_id.get(_rid), to_status="done",
            row=next(r for r in state["rows"] if r["row_id"] == _rid),
            note=f"auto-approved on {row['stage']} entry")
        for _rid in auto_approved
    ]
    _rl_events.append(build_state_changed_event(
        state, task_id=task_path.name, command=command,
        from_status="pending", to_status="in_progress", row=row,
        note=resolve_owner_placeholder(args.note)))
    _rl_fields = run_log_commit(task_path, state, command, event=_rl_events)

    _jw = sync_state_md(task_path, state, now_str, command)
    ok(command, row_id=row["row_id"], stage=row["stage"], item=row["item"],
       status="in_progress", timestamp=now_str,
       auto_approved=auto_approved,
       todo_mirror=build_todo_mirror(state, "update"),
       _transition_state=state,
       **(_jw or {}), **(_rl_fields or {}))

# ── 4. mark ───────────────────────────────────────────────────────────────────

def _parse_step(step_str):
    """--step "N/M" → (N, M) 반환. 형식 위반/None이면 None 반환 (보수적 — 기존 done 동작 유지).
    017: 다중 Step 조기 done 가드. 표준 라이브러리만(re) — T-11.
    """
    m = re.fullmatch(r"\s*(\d+)\s*/\s*(\d+)\s*", step_str or "")
    if not m:
        return None
    n, total = int(m.group(1)), int(m.group(2))
    if total < 1 or n < 0 or n > total:
        return None
    return (n, total)


def _worker_duration_minutes(value):
    """--worker-duration-minutes 값 파서 — 0 이상 정수(분)만 허용 (103 R-15).

    argparse `type=`으로 소비되어 음수(`-5`)·소수(`1.5`)·비수치(`abc`)·공문자열을
    파싱 시점에 거부한다(exit 2). ERROR_CODES를 신설하지 않는 이유는 `--owner`
    choices 위반이나 `--task-step-id` 정수 위반과 동일한 "CLI 인자 형식 오류"
    계열이기 때문이다 — 기존 인자 검증 경로와 동일하게 argparse가 처리한다.

    0은 유효값이다(측정했으나 1분 미만). '측정하지 않음'은 인자 미지정으로
    표현되며 그 경우 행에 필드 자체가 생기지 않는다(집계 기준 16-a 축퇴).
    """
    if not re.fullmatch(r"\d+", str(value).strip()):
        raise argparse.ArgumentTypeError(
            f"0 이상 정수(분)여야 합니다: {value!r}")
    return int(value)


# ─────────────────────────────────────────────────────────────────────────────
# 103 강제 2단 — 차단 코드 카탈로그
#
# ERROR_CODES와 물리적으로 분리한다. 이유는 WARNING_CODES와 동일하다 —
# ERROR_CODES 키 집합은 회귀 테스트가 실측/HEAD 대조로 고정하고 있어 종수를
# 늘리면 계약이 깨진다. `err(..., message=...)`로 문구를 직접 넘기면 카탈로그를
# 늘리지 않고도 전용 코드를 쓸 수 있다.
# ─────────────────────────────────────────────────────────────────────────────
BLOCK_CODES = {
    "worker_duration_undeclared":
        "CLOSE 진입 차단 — 워커 디스패치 규범 단계의 행 {count}건이 워커 소요를 "
        "기록하지도, 미측정을 선언하지도 않았습니다: {rows}. "
        "각 행에 `--worker-duration-minutes <분>`으로 소요를 넣거나, 워커를 돌리지 "
        "않았다면 `--worker-duration-unknown`으로 미측정임을 명시하십시오. "
        "침묵은 통과하지 못합니다 — 워커 완료 알림의 duration_ms는 세션과 함께 "
        "사라지고 행에는 완료 시각만 남아 사후 복구가 불가능하기 때문입니다. "
        "부득이하면 `--force --note <사유>`로 강제 통과할 수 있으며, 그 사실이 "
        "의사결정 로그에 남습니다.",
}

# 워커 디스패치가 **규범**인 단계. 하네스 §1 「디스패치 의무 원칙」이 워커 디스패치로
# 정의한 단계들이며, TASK(TASK.md 작성)·CLOSE(DONE.md 작성)는 PM 직접 수행이 규범이라
# 제외한다. 이 집합과 아래 `_WORKER_DISPATCH_ITEM_PREFIX`가 결합해 **PM의 자발적
# 표시(--as-worker)에 의존하지 않는** 판정 근거를 만든다.
_WORKER_DISPATCH_STAGES = {
    "ANALYSIS", "PLAN", "TEST-SCENARIO", "EXECUTE", "TEST",
    "WIREFRAME", "SPEC", "DESIGN", "REVIEW", "VERIFY", "SCAN", "CHECK",
    "REPORT", "WBS", "DICT", "MODEL", "DDL/MIGRATION",
}

# 같은 단계 안에서도 「작업」 행만 워커 디스패치 지점이다. `PM Gate`·`사용자 확인`·
# `목표-커버 게이트`는 PM/사용자 판정 행이므로 소요를 요구하면 전부 오탐이 된다.
# 실 pipeline.json 10종 실측: 작업 행 item은 "작업" 또는 "작업 (…)" 형태다.
_WORKER_DISPATCH_ITEM_PREFIX = "작업"

# 워커 소요 계측이 도입된 날(`worker_duration_minutes` 필드 신설). 이 날짜 **이전에
# 생성된** 태스크는 선언할 수단 자체가 없었으므로 CLOSE 차단에서 유예한다.
# 이후 생성 태스크에는 예외가 없다 — 캡틴 지시 「반드시 적용」.
_WORKER_MEASUREMENT_EPOCH = "2026-08-26"


def is_worker_dispatch_row(row):
    """이 행이 **워커 디스패치가 규범인 지점**인지 판정한다 (103 강제 2단).

    핵심은 `--as-worker`/`--worker-stage`를 **보지 않는다**는 점이다. 그 인자는 PM이
    자발적으로 붙이는 신호이고, 붙이지 않으면 판정 자체가 성립하지 않아 규범이 통째로
    우회된다(실측: 다른 프로젝트 태스크가 15행 전건 미기록으로 통과). 그래서 근거를
    행의 `stage`·`item`에서 가져온다 — PM 의사와 무관한 파이프라인 구조다.
    """
    if row.get("stage") not in _WORKER_DISPATCH_STAGES:
        return False
    item = (row.get("item") or "").strip()
    if not item.startswith(_WORKER_DISPATCH_ITEM_PREFIX):
        return False
    # 사용자 확인 행은 캡틴 승인 지점이지 워커 디스패치 지점이 아니다.
    return row.get("owner") != "user"


def collect_undeclared_worker_rows(state):
    """워커 소요가 **기록도 선언도 없는** 완료 행을 모은다 (CLOSE 차단 판정 근거).

    「미측정 선언」(`worker_duration_unknown: true`)과 「침묵」(둘 다 부재)을 가른다.
    집계는 둘을 같게 다루지만(축퇴 규칙 16-a), 게이트는 반드시 달리 다뤄야 한다 —
    그러지 않으면 선언할 이유가 사라지고 강제가 무의미해진다.
    """
    out = []
    for row in state.get("rows", []):
        if row.get("status") != "done":
            continue
        if not is_worker_dispatch_row(row):
            continue
        if row.get("worker_duration_minutes") is not None:
            continue
        if row.get("worker_duration_unknown"):
            continue
        out.append(row)
    return out


def check_worker_duration_declared(state, row_index, command, force=False):
    """CLOSE 첫 행 진입 시 워커 소요 미선언 행이 남아 있으면 **차단**한다.

    경고(`worker_duration_missing`)는 조기 발견용이고 이 함수가 최종 방어다.
    경고만으로는 무시하면 그대로 통과하므로, 태스크를 닫는 지점에서 한 번은
    반드시 걸리게 한다. 통과 경로는 「소요 기록」 또는 「미측정 선언」 둘뿐이며,
    `--force`는 의사결정 로그를 남기는 최후 수단이다.

    **소급 유예는 `created_at` 기준이다** — 태스크가 계측 도입 시점
    (`_WORKER_MEASUREMENT_EPOCH`) **이전에 생성**됐으면 통과시킨다. 그 시기의 태스크는
    `worker_duration_minutes` 필드가 존재하지 않아 선언할 방법 자체가 없었고, 그것까지
    막으면 과거 태스크를 영구히 닫을 수 없다.

    「기록이 한 건도 없으면 유예」로 두지 않는 이유가 핵심이다 — 그 규칙은 **워커를
    돌리고도 한 건도 기록하지 않은 신규 태스크**를 그대로 통과시켜(실측 사례 존재)
    강제가 무의미해진다. 생성 시점 기준이면 도입 이후 태스크에는 **예외가 없다**.

    `created_at` 부재·파싱 실패는 유예로 처리한다(fail-safe) — 판정 불가를 차단으로
    바꾸면 정상 태스크가 닫히지 않는 쪽이 더 위험하다.
    """
    if force:
        return
    row = state["rows"][row_index]
    if row.get("stage") != "CLOSE":
        return
    is_first_close = (row_index == 0
                      or state["rows"][row_index - 1].get("stage") != "CLOSE")
    if not is_first_close:
        return

    created = (state.get("created_at") or "")[:10]
    if not created or created < _WORKER_MEASUREMENT_EPOCH:
        return  # 계측 도입 이전 생성 — 소급 유예 (부재·파싱 실패도 fail-safe로 유예)

    missing = collect_undeclared_worker_rows(state)
    if not missing:
        return

    labels = ", ".join(
        f"row {r.get('row_id')} {r.get('stage')}/{r.get('item')}" for r in missing)
    err(command, "worker_duration_undeclared",
        message=BLOCK_CODES["worker_duration_undeclared"].format(
            count=len(missing), rows=labels),
        undeclared_rows=[r.get("row_id") for r in missing])


def build_worker_duration_warning(args, row, worker_minutes):
    """103 R-21 — 워커 디스패치 행을 소요 없이 완료 처리했을 때의 경고를 만든다.

    반환은 경고 dict 1개 또는 None이다. **상태를 만지지 않고 exit code도 바꾸지
    않는다** — 산출물(`state.json`/`STATE.md`)은 경고 유무와 무관하게 바이트 동일이며,
    경고는 오직 `mark` stdout JSON의 `warnings` 배열에만 실린다.

    판정은 4개 관문을 모두 통과해야 성립한다. 오탐(정당한 호출에 뜨는 경고)이
    반복되면 PM이 경고 전체를 무시하게 되므로, 각 관문은 "이 경고가 실제로 유실을
    막는 상황"만 남기도록 좁힌다:

      (1) 이미 값이 실렸으면 경고할 것이 없다.
      (2) `--worker-duration-unknown`으로 미측정을 **명시**했으면 침묵한다
          (§(c) 억제 — 정당한 미측정을 소음으로 만들지 않는다).
      (3) `--as-worker` 또는 `--worker-stage`가 있어야 한다. 이 두 인자는 "이 행은
          워커가 수행했다"는 유일한 기계 판독 신호다. PM 직접 수행 행은 둘 다 없이
          호출되므로 구조적으로 제외된다.
      (4) 이 호출로 행이 실제 `done`이 되어야 한다. `--action-step N/M`(N<M)은 행을
          `in_progress`로 남기며 소요는 마지막 Step에서 합산 기록하는 것이 규범이므로,
          중간 진행 보고마다 경고를 내면 전부 오탐이다.

    추가로 `owner == "user"`인 행은 제외한다. 사용자 확인 행은 캡틴 승인 지점이지
    워커 디스패치 지점이 아니므로, 설령 `--as-worker`가 함께 실렸더라도 여기에 소요를
    요구하는 것은 오탐이다(캡틴 지시 §1(a) 명시 제외 대상).

    093 F-005 재-auto-pass no-op 경로는 이 함수에 도달하기 전에 조기 반환하므로,
    이미 완료된 행을 다시 두드리는 멱등 호출에도 경고가 뜨지 않는다.
    """
    if worker_minutes is not None:
        return None
    if getattr(args, "worker_duration_unknown", False):
        return None
    # (3) 워커 신호 — 인자(PM의 자발적 표시) **또는** 행 구조(파이프라인 규범).
    # 후자를 더한 것이 103 강제 2단의 핵심이다. 인자만 보면 PM이 `--as-worker`를
    # 붙이지 않는 순간 경고가 침묵해 규범이 통째로 우회된다(실측 사례 존재).
    _arg_signal = bool(getattr(args, "as_worker", False)
                       or getattr(args, "worker_stage", None))
    if not (_arg_signal or is_worker_dispatch_row(row)):
        return None
    if row.get("status") != "done":
        return None
    if row.get("owner") == "user":
        return None

    code = "worker_duration_missing"
    return {
        "code": code,
        "message": WARNING_CODES[code].format(
            row_id=row.get("row_id"), stage=row.get("stage")),
    }


def cmd_mark(args):
    """PLAN §2.1, T-7, §2.4, §2.15 G-12, §2.16 G-13 — ⬜/🔄→✅"""
    command = "mark"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)
    # 138 W-9: advance와 같은 단일 경계 — 상태 전이 진입 시 1회 claim(멱등).
    _claim_task_lease_if_needed(task_path)

    # 135 W-4 (AC-6, C-2, H-4): active 완료 전이는 trusted worker 증거가 충분해야
    #   한다. row 주소 해석 이전에 판정한다 — mark는 --done이 필수 인자이므로
    #   (--step N/M에서 N<M인 부분 완료를 제외하면) 항상 완료 시도이며, row 해석
    #   실패(row_not_found 등)가 이 게이트보다 먼저 소비되지 않게 한다.
    _rl_gate_step_str = getattr(args, "step", None) or getattr(args, "action_step", None)
    _rl_gate_step_pair = _parse_step(_rl_gate_step_str) if _rl_gate_step_str else None
    _rl_gate_will_complete = (_rl_gate_step_pair is None) or (_rl_gate_step_pair[0] == _rl_gate_step_pair[1])
    _rl_gate_block = _run_log_block(state)
    if _rl_gate_block is not None and _rl_gate_will_complete:
        _check_active_completion_evidence(task_path, _rl_gate_block, command)

    # C-2: --owner / --auto-pass 배타 (§2.19)
    if args.auto_pass and args.owner and args.owner != "auto":
        err(command, "owner_flag_conflict")

    # C-3: --as-worker → --worker-stage 필수 (§2.19)
    if args.as_worker and not args.worker_stage:
        err(command, "worker_stage_required")

    # C-4: --force → --note 필수 (§2.17 트리거 #3, #8)
    if args.force and not args.note:
        err(command, "note_required_for_force")

    row_index = resolve_row_index(state, command,
                                  getattr(args, "task_step", None),
                                  getattr(args, "task_step_id", None),
                                  args.row)
    row       = state["rows"][row_index]

    # 167 mark 가드: 목표-커버 게이트 행 완료 전 scenario-gate-verify(형제 test-tool) 통과 필수.
    #   상태 변경·자동 승인 이전이라 거부 시 state.json이 불변이며 --force·--auto-pass·
    #   --as-worker로 우회할 수 없다.
    apply_scenario_gate_mark_guard(task_path, row, command,
                                   target_done=_rl_gate_will_complete)

    # 워커 권한 게이트 (§2.4, T-10)
    if args.as_worker:
        allowed_stage = args.worker_stage
        if row["stage"] != allowed_stage:
            if args.force:
                # §2.17 트리거 #3 기재 후 진행
                pass  # 아래 note에서 처리
            else:
                err(command, "worker_scope_violation",
                    worker_stage=allowed_stage,
                    row_id=row["row_id"],
                    stage=row["stage"])

    # 단계 건너뛰기 차단 (PLAN §M-A)
    # PM 경로: 앞 모든 행 검증 (full). 워커 경로: 앞 단계 행만 검증 (prior_stage_only).
    _guard_scope = "prior_stage_only" if args.as_worker else "full"

    # 093 F-002 R-2: 앞 단계 미완 사용자 확인 행 자동 승인 (stage-transition guard보다 먼저)
    now_str = get_kst_datetime(command)
    # W-2/D-3: auto_approve_prior_user_confirmations()가 in-place로 status를 done
    # 갱신하므로, 각 행의 갱신 전 상태(data.from)를 먼저 스냅샷해 둔다.
    _rl_prior_status_by_row_id = {r["row_id"]: r.get("status") for r in state["rows"][:row_index]}
    auto_approved = auto_approve_prior_user_confirmations(
        state, row_index, command,
        as_worker=args.as_worker, force=args.force, now_str=now_str)

    # 157 DEC-6/DEC-11: PM 경로 확인 해시 기록·게이트/EXECUTE 가드(자동 승인 직후·저장 전,
    #   --force 우회 불가). PM 경로가 아니면 no-op.
    apply_pm_design_guards(task_path, state, row_index, command,
                           auto_approved=auto_approved,
                           target_done=_rl_gate_will_complete,
                           owner=args.owner, auto_pass=args.auto_pass)

    check_stage_transition_guard(state, row_index, command, force=args.force,
                                 scope=_guard_scope)

    # CLOSE 진입 게이트 (§2.16 G-13) — 선행 행이 모두 완료된 뒤 판정한다.
    check_close_gate(state, row_index, command,
                     auto_pass=args.auto_pass, force=args.force, owner=args.owner)

    # 103 강제 2단 (b) — 워커 소요 미선언 행이 남아 있으면 CLOSE 진입을 차단한다.
    # 상태 변경 전 구간이라 거부 시 파일이 오염되지 않는다.
    check_worker_duration_declared(state, row_index, command, force=args.force)

    # 005 명확화 게이트 — TASK→다음 단계 첫 행 진입 차단 (상태 변경 전)
    _run_clarification_hook(task_path, state, row_index, command,
                            auto_pass=args.auto_pass, force=args.force)

    # 106 code-scan 인용 게이트 — EXECUTE 첫 행 진입 차단 (save_state_json() 이전)
    _cs_forced_missing = _run_code_scan_citation_hook(
        task_path, state, row_index, command,
        auto_pass=args.auto_pass, force=args.force)

    # semi-agentic 모드에서 EXECUTE-equivalent 이전 행은 --auto-pass 거부
    # (D-DEC-5, 093 F-003 단일 판정 소비 — PLAN §3.3.2 (2))
    if args.auto_pass:
        _allowed, _deny = can_auto_approve_user_confirmation(row["stage"], state.get("mode"))
        if not _allowed and _deny == "invalid_mode_requires_user":
            err(command, "user_confirmation_required",
                row_id=row["row_id"], stage=row["stage"],
                mode=state.get("mode"), reason=_deny,
                required_action="resolve-mode <task-path> --mode <mode>")
        if not _allowed and _deny == "semi_agentic_pre_execute":   # [MUST] 이 사유만 소비 (DEC-E)
            err(command, "semi_agentic_pre_execute_auto_pass_denied",
                row_id=row["row_id"], stage=row["stage"])

    # 091 F-004 R-11: PM Gate 산출물 검증 (H-1 — save_state_json() 이전 검증 구간에 위치)
    _gate_forced_missing = check_gate_artifacts(task_path, row, command, force=args.force)

    # 017: 다중 Step 진행률 파싱 + 조기 done 가드 (R-1, C-1, C-5)
    # 070 R-5: --action-step은 dest="step" 공유 별칭(argparse) — 직접 호출(테스트)
    #   경로에서는 args.step/args.action_step이 분리된 속성일 수 있으므로 폴백 병합한다.
    _step_str = getattr(args, "step", None) or getattr(args, "action_step", None)
    _step_pair = _parse_step(_step_str) if _step_str else None

    # 103 R-15: 워커 소요(분). 미지정(None)이면 행에 필드를 만들지 않는다 — 기존
    #   태스크 무영향(집계 기준 16-a 축퇴). 값 검증(0 이상 정수)은 argparse
    #   type=_worker_duration_minutes가 파싱 시점에 수행한다.
    _worker_minutes = getattr(args, "worker_duration_minutes", None)

    # 093 F-005 R-5 멱등성 — 이미 auto 승인된 행에 대한 재-auto-pass는 상태 변경 없이 성공 반환
    #   (--force·--action-step N/M·owner=user done 행은 조건에서 제외 — 기존 경로 유지)
    # 103 R-15: --worker-duration-minutes가 실린 호출은 기록할 값이 있으므로 no-op
    #   대상에서 뺀다. 기존 호출은 이 값이 항상 None이라 조건이 종전과 동일하다.
    if (args.auto_pass and not args.force and not _step_str
            and _worker_minutes is None
            and row.get("status") == "done" and row.get("owner") == "auto"):
        ok(command, row_id=row["row_id"], stage=row["stage"], item=row["item"],
           status="done", timestamp=row.get("timestamp"), idempotent=True,
           todo_mirror=build_todo_mirror(state, "update"),
           _transition_state=state)
        return

    # W-7 (PLAN D-P8, CONTRACT §2.5 시간 절): 1.2 태스크에서 W-6 코어 조회로
    #   파생 분값을 읽어 명시값과 대조한다. 1.0/1.1(run_log 블록 부재)이거나
    #   파생값을 아직 얻을 수 없으면 명시값을 그대로 돌려받아 기존 경로와
    #   바이트 동일하다(H-6, S-9). 아직 어떤 상태 변경도 없는 시점이므로
    #   불일치로 거부돼도 state.json은 손대지지 않은 채로 남는다(S-8③).
    _worker_minutes, _worker_duration_deprecated_warning = (
        _reconcile_worker_duration_minutes(task_path, state, _worker_minutes, command))

    # T05: state.changed의 data.from은 전이 **이전** 행 상태다(§1.2).
    _rl_from_status = row.get("status")

    if _step_pair is not None:
        _n, _total = _step_pair
        row["step"] = f"{_n}/{_total}"           # 진행률 영속화
        if _n < _total:
            # 마지막 Step 아님 → done으로 닫지 않고 in_progress 유지 (조기 done 차단)
            row["status"]       = "in_progress"
            row["status_label"] = "🔄"
        else:
            # n == total → 마지막 Step → done (R-2)
            row["status"]       = "done"
            row["status_label"] = "✅"
    else:
        # --step 미지정/비정형 → 기존 즉시 done (C-4 하위 호환)
        row["status"]       = "done"
        row["status_label"] = "✅"
    row["timestamp"]    = now_str

    # 103 R-15: 지정된 경우에만 기록 — 미지정 행은 키 자체가 생기지 않는다(H-1).
    if _worker_minutes is not None:
        row["worker_duration_minutes"] = _worker_minutes
    # 103 강제 2단 (c) — 미측정 **선언**을 행에 남긴다. 남기지 않으면 CLOSE 차단이
    # 「선언했음」과 「침묵」을 구별할 수 없어 강제가 성립하지 않는다.
    if getattr(args, "worker_duration_unknown", False):
        row["worker_duration_unknown"] = True

    # note 소유자 호칭 치환 (PLAN §3.1.2, TASK 054) — 3분기 공용 1회 산출
    note_text = resolve_owner_placeholder(args.note)

    # owner 결정
    if args.auto_pass:
        row["owner"] = "auto"
        # 093 F-005 R-5: 접두 3분기 — 빈 note / 이미 접두 보유(중첩 방지) / 신규 부여
        if not note_text:
            row["note"] = _AUTO_PASS_PREFIX
        elif note_text.startswith(f"{_AUTO_PASS_PREFIX}:"):
            row["note"] = note_text
        else:
            row["note"] = f"{_AUTO_PASS_PREFIX}: {note_text}"
    elif args.owner:
        row["owner"] = args.owner
        if note_text:
            row["note"] = note_text
    else:
        row["owner"] = "PM"
        if note_text:
            row["note"] = note_text

    state["updated_at"] = now_str

    # CLOSE 단계 마지막 행 → current_status = done (§2.11 G-6)
    # Task 136: 신규 pipeline은 close.final에서만 완료를 확정한다. close.final이
    # 없는 in-flight legacy pipeline은 기존 단일 CLOSE 마지막 행 호환을 유지한다.
    is_close_final = _is_close_final_row(row, state)
    # 017: in_progress(N<M)로 남긴 행은 완료 전환에서 제외 — 다중 Step CLOSE 마지막 행 오판 방지
    # 118 D-4b(AC-4): CLOSE 최종 행은 `completed_unmerged`만 확정한다. 귀속(MEMORY
    #   history append)은 merge 확인 뒤 `finalize-attribution`이 전담한다.
    if is_close_final and row["status"] == "done":
        state["current_status"] = STATUS_COMPLETED_UNMERGED

    # 072 F-002/F-003: '다음 액션' 자동 파생(프론티어) + --next-action 오버라이드(비지속, M-3)
    state["next_action"] = getattr(args, "next_action", None) or _derive_next_action(state)

    # 135 W-4: active 완료 게이트는 함수 진입 시점(row 해석 이전)에 이미 판정했다
    #   (_rl_gate_will_complete) — 여기서 다시 검사하지 않는다(중복 방지).

    # W-2/D-3: 자동 승인된 각 행 + 대상 행 전이를 각각 독립 state.changed로 만들어
    #   한 번의 admission·원자 쓰기로 커밋한다(H-1).
    _rl_events = [
        build_state_changed_event(
            state, task_id=task_path.name, command=command,
            from_status=_rl_prior_status_by_row_id.get(_rid), to_status="done",
            row=next(r for r in state["rows"] if r["row_id"] == _rid),
            note=f"auto-approved on {row['stage']} entry")
        for _rid in auto_approved
    ]
    _rl_events.append(build_state_changed_event(
        state, task_id=task_path.name, command=command,
        from_status=_rl_from_status, to_status=row["status"], row=row,
        note=note_text))
    _rl_fields = run_log_commit(task_path, state, command, event=_rl_events)

    # TEST stage done 시 verify 자동 훅 (PLAN 013)
    if row["stage"] == "TEST":
        scenario_path = _find_scenario_file(task_path, None)
        if scenario_path is not None:
            lines = scenario_path.read_text(encoding="utf-8").splitlines()
            mock_lines = _check_mock_patterns(lines)
            if mock_lines:
                err("mark", "mock_in_scenario", lines=mock_lines)
            missing_lines = _check_evidence(lines)
            if missing_lines:
                err("mark", "evidence_missing", lines=missing_lines)

    decision = None
    reason_text = None

    # §2.17 트리거 #2 auto-pass 로그
    if args.auto_pass:
        decision = f"agentic auto-pass at row {row['row_id']}, item={row['item']}"
        reason_text = (args.note or "agentic mode")

    # §2.17 트리거 #3 worker force 로그
    if args.as_worker and args.force:
        requested = args.worker_stage
        actual = row["stage"]
        decision = f"worker_scope_force at row {row['row_id']}, requested_stage={requested}, actual_stage={actual}"
        reason_text = args.note

    # 091 F-004 R-11(H-5): --force로 게이트 아티팩트 미충족을 우회한 경우 강제 기록
    if _gate_forced_missing:
        decision = (f"gate_artifact_force at row {row['row_id']}, key={row.get('key')}, "
                    f"missing={_gate_forced_missing}")
        reason_text = args.note

    # 106: --force로 code-scan 결과 인용 게이트를 우회한 경우 강제 기재 (091 H-5 동형)
    if _cs_forced_missing:
        decision = (f"code_scan_citation_force at row {row['row_id']}, key={row.get('key')}, "
                    f"missing={_cs_forced_missing}")
        reason_text = args.note

    _jw = sync_state_md(task_path, state, now_str, command,
                        decision=decision, reason=reason_text)

    # 118 D-4b(AC-4): 088 §2.1의 "CLOSE 마지막 행 mark 시 즉시 history append"는
    #   제거됐다. mark는 허브 `.opal/MEMORY.json`을 어떤 경로로도 건드리지 않으며
    #   `completed_unmerged` 확정까지만 책임진다. history append는 merge 확인 뒤
    #   `state-tool finalize-attribution <task-path> --allocator-root <abs>`가 전담한다
    #   (worktree.md §task root와 allocator root 계약).
    #   mark 응답이 항상 ok:true인 현행 계약은 그대로 유지한다.

    _ok_kwargs = dict(row_id=row["row_id"], stage=row["stage"], item=row["item"],
                      status=row["status"], timestamp=now_str, owner=row["owner"],
                      auto_approved=auto_approved,
                      todo_mirror=build_todo_mirror(state, "update"),
                      _transition_state=state)
    # 103 R-15: 기록한 경우에만 응답에 실어 PM이 반영값을 확인할 수 있게 한다.
    #   미지정 호출의 응답 키 집합은 종전과 완전히 동일하다(H-11 하위호환).
    if _worker_minutes is not None:
        _ok_kwargs["worker_duration_minutes"] = _worker_minutes
    if getattr(args, "worker_duration_unknown", False):
        _ok_kwargs["worker_duration_unknown"] = True
    # 103 R-21: 워커 디스패치 행인데 소요가 비었으면 경고를 실어 보낸다.
    #   경고가 없으면 `warnings` 키 자체를 만들지 않는다 — 기존 mark 호출의 응답
    #   키 집합이 종전과 완전히 동일해야 하기 때문이다(H-11, S-5와 동일 계약).
    _warning = build_worker_duration_warning(args, row, _worker_minutes)
    if _warning is not None:
        _ok_kwargs["warnings"] = [_warning]
    # W-7 (PLAN D-P8): 명시값이 1.2 파생값과 일치해 수용된 경우의 deprecated 경고.
    if _worker_duration_deprecated_warning is not None:
        _ok_kwargs.setdefault("warnings", []).append(_worker_duration_deprecated_warning)
    # T05: 보관함 잔량·기록 실패는 exit code를 바꾸지 않고 응답에만 실린다(§2.2
    #   run_log_pending "한도 내 일반 진행 허용"). 1.0/1.1 태스크는 빈 dict라
    #   응답 키 집합이 종전과 완전히 동일하다.
    if _rl_fields:
        _rl_warnings = _rl_fields.pop("warnings", None)
        _ok_kwargs.update(_rl_fields)
        if _rl_warnings:
            _ok_kwargs.setdefault("warnings", []).extend(_rl_warnings)
    _gate_payload = build_gate_payload(row)
    if _gate_payload is not None:
        _ok_kwargs["gate_checklist"] = _gate_payload
    if _jw:
        _ok_kwargs.update(_jw)
    ok(command, **_ok_kwargs)

# ── 5. block ──────────────────────────────────────────────────────────────────

def cmd_block(args):
    """PLAN §2.17 트리거 #7 — any→❌. current_status → blocked 자동 전환."""
    command = "block"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)
    row_index = resolve_row_index(state, command,
                                  getattr(args, "task_step", None),
                                  getattr(args, "task_step_id", None),
                                  args.row)
    row       = state["rows"][row_index]

    now_str = get_kst_datetime(command)
    row["status"]       = "failed"
    row["status_label"] = "❌"
    row["timestamp"]    = now_str
    row["note"]         = f"block: {resolve_owner_placeholder(args.reason)}"

    # current_status → blocked 자동 전환 (§2.11 G-7)
    prev_status = state["current_status"]
    state["current_status"] = "blocked"
    state["updated_at"]     = now_str

    _rl_fields = run_log_commit(
        task_path, state, command,
        event=build_state_changed_event(
            state, task_id=task_path.name, command=command,
            from_status=prev_status, to_status="blocked", row=row))
    _jw = sync_state_md(task_path, state, now_str, command)

    ok(command, row_id=row["row_id"], stage=row["stage"], item=row["item"],
       status="failed", current_status="blocked", timestamp=now_str,
       todo_mirror=build_todo_mirror(state, "update"),
       _transition_state=state,
       **(_jw or {}), **(_rl_fields or {}))

# ── 6. validate ───────────────────────────────────────────────────────────────

def cmd_validate(args):
    """PLAN §2.6, §2.15 G-12 — 정합성 검증 → violations[]"""
    command = "validate"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)

    violations = []

    # 스키마 기본 필드 검증
    required_fields = ["task_id", "skill", "mode", "schema_version",
                        "created_at", "updated_at", "current_status", "rows"]
    for f in required_fields:
        if f not in state:
            violations.append({"code": "schema_violation", "row_id": None,
                                "detail": f"missing field: {f}"})

    # 행 순서 정합성 (완료되지 않은 행 뒤에 완료된 행 존재 여부는 단순 경고)
    # 사용자 확인 행 owner 검증 (§2.15 G-12)
    raw_mode = state.get("mode")
    mode, mode_source, _mode_warnings = normalize_stored_mode(raw_mode)
    if mode_source == "fail_closed":
        violations.append({
            "code": "invalid_mode",
            "row_id": None,
            "detail": f"invalid stored mode: {raw_mode!r}; user resolution required",
        })
    for row in state.get("rows", []):
        if row.get("item") == "사용자 확인" and row.get("status") == "done":
            owner = row.get("owner")
            if owner not in ("user", "auto"):
                violations.append({
                    "code":   "user_confirmation_owner_mismatch",
                    "row_id": row["row_id"],
                    "detail": f"owner={owner}"
                })
            if owner == "auto":
                # 093 F-003 단일 판정 소비 — CLOSE 축은 평가하지 않는다
                # (H-4: 현행 validate는 CLOSE stage 자체로는 위반을 내지 않는다. 표 B V-7~V-9)
                _allowed, _deny = can_auto_approve_user_confirmation(
                    row.get("stage"), mode, include_close_axis=False)
                if not _allowed and _deny == "interactive_requires_user":
                    violations.append({
                        "code":   "auto_pass_in_interactive_mode",
                        "row_id": row["row_id"],
                        "detail": f"interactive mode but owner=auto"
                    })
                if not _allowed and _deny == "semi_agentic_pre_execute":
                    # PLAN-equivalent 이전 행에 owner=auto는 위반 (D-DEC-5)
                    violations.append({
                        "code":   "semi_agentic_pre_execute_auto_pass_denied",
                        "row_id": row["row_id"],
                        "detail": f"semi-agentic mode but owner=auto on stage={row.get('stage')}"
                    })

    # T05: 로그 계약 블록 진단 합류 (§1.4 / AC-3). 1.0/1.1 태스크는 빈 리스트라
    #   응답이 종전과 동일하다.
    violations.extend(run_log_diagnose(task_path, state))

    count = len(violations)
    is_ok = count == 0
    print(json.dumps({
        "ok": is_ok, "command": command,
        "violations": violations, "violations_count": count
    }, ensure_ascii=False))
    sys.exit(0 if is_ok else 1)

# ── 6b. spec-validate (070 F-001 R-6) ───────────────────────────────────────

def cmd_spec_validate(args):
    """spec-validate <pipeline.json> — 단일 라인 JSON (070 R-6, DEC-2).
    {ok, command:'spec-validate', violations:[...], violations_count:N}, exit 0/1.
    (cmd_validate 출력 계약과 동일)
    """
    command = "spec-validate"
    spec = load_pipeline_spec(args.spec_path, command)
    violations = validate_pipeline_spec(spec)
    count = len(violations)
    is_ok = count == 0
    print(json.dumps({
        "ok": is_ok, "command": command,
        "violations": violations, "violations_count": count
    }, ensure_ascii=False))
    sys.exit(0 if is_ok else 1)

# ── 7. add-row ────────────────────────────────────────────────────────────────

def _auto_row_key(state, stage, item):
    """{stage_slug}.{item_slug}_{n} 자동 생성 (070 F-004 R-9, PLAN §3.4.2).
    전체 rows[] 스캔 유일성 — 동일 base로 이미 존재하는 key 개수 +1부터 증가,
    충돌 없을 때까지 증가.
    """
    stage_slug = stage_to_slug(stage)
    m = re.match(r"[a-zA-Z][a-zA-Z0-9]*", item or "")
    item_slug = m.group(0).lower() if m else "item"
    base = f"{stage_slug}.{item_slug}"

    existing_keys = {r.get("key") for r in state["rows"] if r.get("key")}
    n = 1
    candidate = f"{base}_{n}"
    while candidate in existing_keys:
        n += 1
        candidate = f"{base}_{n}"
    return candidate


def cmd_add_row(args):
    """PLAN §2.12 G-9 — 추가작업 행 삽입"""
    command = "add-row"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)

    # stage enum 검증 (§2.12 G-9 단계 5)
    if args.stage not in STAGE_ENUM:
        err(command, "invalid_stage_enum", value=args.stage)
    change_kind = getattr(args, "test_change_kind", None)
    if change_kind and args.stage != "TEST":
        err(command, "test_change_kind_requires_test")
    # 기존 행 식별 (070 F-003 R-4: --after-task-step/--after-task-step-id/--after(deprecated))
    after_index = resolve_row_index(state, command,
                                    getattr(args, "after_task_step", None),
                                    getattr(args, "after_task_step_id", None),
                                    args.after,
                                    addr_label="after")

    # 070 F-004 R-9: --key 명시 지정 또는 자동 생성 (전체 스캔 유일성)
    existing_keys = {r.get("key") for r in state["rows"] if r.get("key")}
    explicit_key = getattr(args, "key", None)
    if explicit_key:
        if not KEY_PATTERN.match(explicit_key):
            err(command, "task_step_key_invalid", key=explicit_key)
        if explicit_key in existing_keys:
            err(command, "task_step_key_duplicate", key=explicit_key)
        new_key = explicit_key
    else:
        new_key = _auto_row_key(state, args.stage, args.item)

    now_str = get_kst_datetime(command)

    new_row = {
        "row_id":       after_index + 2,  # 임시 — 아래서 재정렬
        "stage":        args.stage,
        "item":         args.item,
        "key":          new_key,
        "status":       "pending",
        "status_label": "⬜",
        "timestamp":    None,
        "owner":        None,
        "note":         resolve_owner_placeholder(args.note) or None,
    }
    if change_kind:
        new_row["test_change_kind"] = change_kind

    # 삽입 (G-9 단계 3)
    state["rows"].insert(after_index + 1, new_row)

    # row_id 재정렬 (G-9 단계 4) — 삽입 후 전체 재번호 (기존 key는 불변)
    for i, row in enumerate(state["rows"]):
        row["row_id"] = i + 1

    # current_status 자동 전환 (G-9 단계 8, G-7)
    prev_status = state["current_status"]
    # 118 D-4b: completed_unmerged도 완료 상태이므로 done과 동일하게 추가작업으로 연다.
    if prev_status in TASK_COMPLETE_STATUSES:
        state["current_status"] = "additional_work"
    elif prev_status == "additional_work_done":
        state["current_status"] = "additional_work"

    state["updated_at"] = now_str
    _rl_fields = run_log_commit(
        task_path, state, command,
        event=build_state_changed_event(
            state, task_id=task_path.name, command=command,
            from_status=None, to_status="pending",
            row=new_row, row_key=new_key))

    # §2.17 트리거 #5 의사결정 로그
    decision = f"additional row inserted after row {after_index + 1}: stage={args.stage}, item={args.item}, key={new_key}, new_row_id={after_index + 2}"
    reason   = args.note or "additional work entry"

    _jw = sync_state_md(task_path, state, now_str, command,
                        decision=decision, reason=reason)

    ok(command,
       row_id=after_index + 2,
       key=new_key,
       rows_count=len(state["rows"]),
       current_status=state["current_status"],
       _transition_state=state,
       **(_jw or {}), **(_rl_fields or {}))

# ── 8. status ─────────────────────────────────────────────────────────────────

def cmd_status(args):
    """PLAN §2.11 G-7 — current_status 명시 전환"""
    command = "status"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)

    from_status = state["current_status"]
    to_status   = args.set

    # 전이 그래프 검증 (§2.11 G-7)
    allowed = ALLOWED_TRANSITIONS.get(from_status, set())
    if to_status not in allowed:
        err(command, "invalid_status_transition",
            **{"from": from_status, "to": to_status},
            message=f"{from_status} → {to_status} 전이는 허용되지 않음")

    now_str = get_kst_datetime(command)
    state["current_status"] = to_status
    state["updated_at"]     = now_str
    # 태스크 수준 전이에는 대응 행이 없으므로 row_key를 'current_status'로 둔다
    # (§1.2 state.changed의 data.row_key 필수 조건을 행 부재 경로에서 충족).
    _rl_fields = run_log_commit(
        task_path, state, command,
        event=build_state_changed_event(
            state, task_id=task_path.name, command=command,
            from_status=from_status, to_status=to_status,
            row_key="current_status",
            note=resolve_owner_placeholder(args.note)))

    # §2.17 트리거 #4
    decision = f"current_status changed: {from_status} → {to_status}"
    reason   = resolve_owner_placeholder(args.note) or "(none)"

    _jw = sync_state_md(task_path, state, now_str, command,
                        decision=decision, reason=reason)

    ok(command, **{"from": from_status, "to": to_status}, timestamp=now_str,
       _transition_state=state,
       **(_jw or {}), **(_rl_fields or {}))


def cmd_test_clock(args):
    """Record the UTC event time of a TEST execution or human wait boundary."""
    command = "test-clock"
    task_path = resolve_task_path(args.task_path, command)
    state = load_state_json(task_path, command)
    intervals = state.get("test_timing", {}).get("intervals", [])
    active = next((item for item in intervals
                   if item["kind"] == args.kind and item["id"] == args.id
                   and item["ended_at"] is None), None)
    if args.action == "start" and active is not None:
        err(command, "test_clock_already_open", kind=args.kind, id=args.id)
    if args.action == "stop" and active is None:
        err(command, "test_clock_not_open", kind=args.kind, id=args.id)
    at = datetime.now(timezone.utc).isoformat()
    if args.action == "start":
        intervals.append({"kind": args.kind, "id": args.id,
                          "started_at": at, "ended_at": None})
    else:
        active["ended_at"] = at
    state["test_timing"] = {"intervals": intervals}
    state["updated_at"] = get_kst_datetime(command)
    _atomic_write_state_json(task_path, state)
    ok(command, action=args.action, kind=args.kind, id=args.id, at=at)


def _interval_union_seconds(intervals):
    """Return elapsed seconds across completed intervals, merging overlaps."""
    spans = sorted((datetime.fromisoformat(item["started_at"]),
                    datetime.fromisoformat(item["ended_at"]))
                   for item in intervals if item["ended_at"] is not None)
    if not spans:
        return None
    total = 0.0
    start, end = spans[0]
    for next_start, next_end in spans[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            total += (end - start).total_seconds()
            start, end = next_start, next_end
    return total + (end - start).total_seconds()


def _interval_sum_seconds(intervals):
    durations = [(datetime.fromisoformat(item["ended_at"]) -
                  datetime.fromisoformat(item["started_at"])).total_seconds()
                 for item in intervals if item["ended_at"] is not None]
    return sum(durations) if durations else None


def cmd_test_metrics(args):
    """Read only TEST timing and typed iteration counts."""
    command = "test-metrics"
    task_path = resolve_task_path(args.task_path, command)
    state = load_state_json(task_path, command)
    intervals = state.get("test_timing", {}).get("intervals", [])
    test_rows = [row for row in state["rows"] if row["stage"] == "TEST"]
    ok(command,
       auto_seconds=_interval_sum_seconds([i for i in intervals if i["kind"] == "auto"]),
       human_wait_seconds=_interval_union_seconds([i for i in intervals if i["kind"] == "human"]),
       fix_count=sum(row.get("test_change_kind") == "fix" for row in test_rows),
       requirement_change_count=sum(row.get("test_change_kind") == "requirement_change"
                                    for row in test_rows),
       legacy_unclassified_rows=sum("test_change_kind" not in row for row in test_rows),
       open_intervals=[i for i in intervals if i["ended_at"] is None])


# ── 8a. run-start (131 D8) ───────────────────────────────────────────────────

# 131 D8: run_id 형식 계약 — `run-<UTC YYYYMMDDHHMMSS>-<8자리 소문자 hex>`.
# state.schema.json properties.run_id의 pattern과 동일 문자열이어야 한다.
RUN_ID_PATTERN = re.compile(r"^run-[0-9]{14}-[0-9a-f]{8}$")


def new_run_id():
    """새 run_id 발급 — UTC 초 해상도 타임스탬프 + 8자리 hex 무작위 접미사.

    타임스탬프는 태스크 시각 표기(KST)와 달리 UTC로 고정한다(131 D8). 같은 초에
    재발급해도 hex 접미사가 id를 구분한다.
    """
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"run-{stamp}-{os.urandom(4).hex()}"


def cmd_run_start(args):
    """131 D8 — `run-start <task-path>`: 새 run_id 발급 + state.json 기록.

    현재 run은 항상 1개다. 재호출하면 기존 run_id를 새 id로 교체하며 이력을
    누적하지 않는다(run_ids/runs 같은 목록을 만들지 않는다). run_id는 optional
    필드이므로 init이 만들지 않고 이 커맨드만 생성한다.
    """
    command = "run-start"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)

    previous = state.get("run_id")
    run_id   = new_run_id()
    state["run_id"] = run_id
    save_state_json(task_path, state)

    ok(command, run_id=run_id, previous_run_id=previous)


# ── 8b. finalize-attribution (118 D-4b / AC-4) ───────────────────────────────

def cmd_finalize_attribution(args):
    """`finalize-attribution <task-path> --allocator-root <abs>` — 귀속 전담 커맨드.

    118 D-4b: CLOSE 마지막 행 mark에서 분리된 허브 `.opal/MEMORY.json` history
    append를 이 커맨드 하나가 전담한다. merge 확인 뒤 허브 PM이 worktree registry
    발급값(`allocator_root`)을 **명시 인자**로 넘겨 호출한다.

    [MUST] allocator_root는 추론하지 않는다 — cwd, task path의 조상,
    `.opal-worktrees` 문자열 어느 것도 근거로 쓰지 않는다. 미지정·상대경로는
    이 도구의 기존 에러 관례(err(), 단일 라인 JSON `ok:false`+`error`, exit 1)로
    거부한다(worktree.md §task root와 allocator root 계약).

    멱등: 동일 path 행이 이미 있으면 append를 건너뛰고 `duplicate_skipped`로
    응답한다(exit 0, ok:true).
    """
    command = "finalize-attribution"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)

    raw_root = getattr(args, "allocator_root", None)
    if raw_root is None or not str(raw_root).strip():
        err(command, "allocator_root_required")
    raw_root = str(raw_root).strip()
    if not os.path.isabs(raw_root):
        err(command, "allocator_root_not_absolute", path=raw_root)
    allocator_root = pathlib.Path(raw_root).resolve()
    if not (allocator_root / ".opal" / "MEMORY.json").is_file():
        err(command, "allocator_root_invalid", path=str(allocator_root))

    result = link_memory_history(task_path, state, allocator_root)
    status = result.get("status")
    if status not in ("created", "duplicate_skipped"):
        err(command, "finalize_attribution_failed",
            detail=str(result.get("warning") or status),
            attribution=result, allocator_root=str(allocator_root))

    ok(command, attribution=result, allocator_root=str(allocator_root),
       task_id=state.get("task_id", ""))


# ── boot summary (read-only) ─────────────────────────────────────────────────

def _boot_current_stage(state):
    """Return the stage at the current pipeline frontier.

    ``current_status`` is the task-level authority for selecting a task; rows
    provide the most useful stage signal.  Malformed rows are deliberately
    ignored so a single damaged state file cannot affect the project summary.
    """
    rows = state.get("rows")
    if not isinstance(rows, list):
        return ""
    for status in ("in_progress", "failed", "pending"):
        for row in rows:
            if isinstance(row, dict) and row.get("status") == status:
                stage = row.get("stage")
                if isinstance(stage, str) and stage:
                    return stage
    return ""


BOOT_SUMMARY_ITEM_LIMIT = 3
BOOT_SUMMARY_ANOMALY_LIMIT = 8
ACTIVE_ATTRIBUTION_STATES = {"attribution_pending", "completed_unmerged"}


def _boot_candidate(task_dir, include_mode=False):
    """Return one validated state candidate without changing its source file."""
    state_file = task_dir / "state.json"
    if not state_file.is_file() or state_file.is_symlink():
        return None
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            return None
        status = state.get("current_status")
        updated = state.get("updated_at")
        if status not in {"in_progress", "blocked"} or not isinstance(updated, str):
            return None
        if not (TS_PATTERN_MIN.match(updated) or TS_PATTERN_SEC.match(updated)):
            return None
        task_id = state.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            task_id = task_dir.name
        next_action = state.get("next_action", "")
        if not isinstance(next_action, str):
            next_action = ""
        item = {
            "title": task_id,
            "stage": _boot_current_stage(state),
            "next_action": next_action,
        }
        if include_mode:
            mode, mode_source, _mode_warnings = normalize_stored_mode(state.get("mode"))
            item.update({"mode": mode, "mode_source": mode_source})
        return updated, item
    except (OSError, UnicodeError, json.JSONDecodeError, AttributeError, TypeError):
        return None


def _boot_anomaly(code, detail=""):
    anomaly = {"code": code}
    if detail:
        anomaly["detail"] = detail
    return anomaly


def _registry_meta_files(meta_root):
    """`.meta/task_*/meta.json`만 이름순으로 반환한다.

    구 구조 파일(`.meta/task_{NNN}.json`)은 읽지도 옮기지도 않는다. 이 함수가
    이 파일 안의 유일한 경로 계산 지점이며, 모든 소비 지점은 이 함수를 거친다.
    """
    if not meta_root.is_dir():
        return []
    try:
        entries = sorted(meta_root.iterdir(), key=lambda p: p.name)
    except OSError:
        return []
    result = []
    for entry in entries:
        if not entry.is_dir() or not entry.name.startswith("task_"):
            continue
        meta_file = entry / "meta.json"
        if meta_file.is_file() and not meta_file.is_symlink():
            result.append(meta_file)
    return result


def _collect_boot_summary_details(project_root, include_mode=False):
    """Collect direct and registry-issued canonical candidates read-only."""
    root = pathlib.Path(project_root).resolve()
    direct = {}
    tasks_root = root / "tasks"
    if tasks_root.is_dir():
        try:
            entries = sorted(tasks_root.iterdir())
        except OSError:
            entries = []
        for task_dir in entries:
            if not task_dir.is_dir() or task_dir.is_symlink():
                continue
            candidate = _boot_candidate(task_dir, include_mode=include_mode)
            if candidate is not None:
                direct[task_dir.name] = candidate

    anomalies = []
    registry_rows = []
    meta_root = root / ".opal-worktrees" / ".meta"
    meta_files = _registry_meta_files(meta_root)
    required = {"task_path", "task_folder", "allocator_root"}
    for meta_file in meta_files:
        meta_label = meta_file.parent.name
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            anomalies.append(_boot_anomaly("registry_meta_corrupt", meta_label))
            continue
        if not isinstance(meta, dict) or any(
                key not in meta or not isinstance(meta[key], str) or not meta[key]
                for key in required):
            anomalies.append(_boot_anomaly("registry_meta_missing_fields", meta_label))
            continue
        attribution_state = meta.get("attribution_state")
        if "attribution_state" in meta and (
                not isinstance(attribution_state, str) or not attribution_state):
            anomalies.append(_boot_anomaly("registry_attribution_state_invalid", meta_label))
            continue
        if attribution_state == "closed":
            continue
        if (attribution_state is not None
                and attribution_state not in ACTIVE_ATTRIBUTION_STATES):
            anomalies.append(_boot_anomaly("registry_attribution_state_invalid", meta_label))
            continue
        task_folder = meta["task_folder"]
        if pathlib.PurePath(task_folder).name != task_folder or task_folder in {".", ".."}:
            anomalies.append(_boot_anomaly("registry_task_folder_invalid", meta_label))
            continue
        try:
            task_path = pathlib.Path(meta["task_path"])
            allocator_root = pathlib.Path(meta["allocator_root"])
            if not task_path.is_absolute() or not allocator_root.is_absolute():
                anomalies.append(_boot_anomaly("registry_meta_path_not_absolute", meta_label))
                continue
            if allocator_root.resolve() != root:
                anomalies.append(_boot_anomaly("registry_allocator_root_mismatch", meta_label))
                continue
            if not task_path.is_dir() or task_path.is_symlink():
                anomalies.append(_boot_anomaly("registry_task_path_missing", task_folder))
                continue
            canonical_path = task_path.resolve()
        except (OSError, RuntimeError, ValueError):
            anomalies.append(_boot_anomaly("registry_task_path_missing", task_folder))
            continue
        if canonical_path.name != task_folder:
            anomalies.append(_boot_anomaly("registry_task_path_mismatch", task_folder))
            continue
        registry_rows.append({
            "task_folder": task_folder,
            "task_path": canonical_path,
            "meta_name": meta_label,
        })

    folder_counts = {}
    path_counts = {}
    for row in registry_rows:
        folder_counts[row["task_folder"]] = folder_counts.get(row["task_folder"], 0) + 1
        path_key = str(row["task_path"])
        path_counts[path_key] = path_counts.get(path_key, 0) + 1

    candidates = []
    active_registry_folders = {row["task_folder"] for row in registry_rows}
    duplicate_folders = set()
    for row in registry_rows:
        path_key = str(row["task_path"])
        if folder_counts[row["task_folder"]] > 1 or path_counts[path_key] > 1:
            duplicate_folders.add(row["task_folder"])
            continue
        candidate = _boot_candidate(row["task_path"], include_mode=include_mode)
        if candidate is not None:
            candidates.append(candidate)

    for task_folder in sorted(duplicate_folders):
        anomalies.append(_boot_anomaly("registry_active_duplicate", task_folder))
    for task_folder in sorted(active_registry_folders.intersection(direct)):
        anomalies.append(_boot_anomaly("task_path_ambiguous", task_folder))
    for task_folder, candidate in direct.items():
        if task_folder not in active_registry_folders:
            candidates.append(candidate)

    candidates.sort(key=lambda entry: (entry[0], entry[1]["title"]), reverse=True)
    items = [entry[1] for entry in candidates[:BOOT_SUMMARY_ITEM_LIMIT]]
    return {
        "items": items,
        "other_count": max(0, len(candidates) - len(items)),
        "anomalies": anomalies[:BOOT_SUMMARY_ANOMALY_LIMIT],
    }


def collect_boot_summary(project_root):
    """Return the newest direct/canonical item using the legacy list shape."""
    return _collect_boot_summary_details(project_root, include_mode=False)["items"][:1]


def cmd_boot_summary(args):
    """Emit a bounded, read-only summary for session.project bootstrap."""
    command = "boot-summary"
    details = _collect_boot_summary_details(args.project_root, include_mode=True)
    items = details["items"]
    payload = {"ok": True, "command": command, **details}
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # Keep the public result bounded even for adversarially long state fields.
    mutable = [
        (row, key)
        for row in items
        for key in ("title", "stage", "next_action", "mode", "mode_source")
        if key in row
    ] + [
        (row, "detail")
        for row in payload["anomalies"]
        if "detail" in row
    ]
    for row, key in mutable:
        limit = 120 if key != "stage" else 40
        row[key] = row[key][:limit]
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # Counts, item structure, and anomaly codes are immutable while values trim.
    while len(encoded.encode("utf-8")) > 1024:
        populated = [(row, key) for row, key in mutable if row.get(key)]
        if not populated:
            break
        row, key = max(
            populated,
            key=lambda pair: len(pair[0][pair[1]].encode("utf-8")),
        )
        row[key] = row[key][:-1]
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    print(encoded)

# ── 9. gate-pass ──────────────────────────────────────────────────────────────

def cmd_gate_pass(args):
    """PLAN §2.13 G-10 — 4행 Gate 일괄 처리.

    [DEPRECATED — 014 Phase 4] 새 표준 행 구조(opds 10행)에는 "QA Gate"/"State Gate"
    행이 존재하지 않으므로 [QA Gate, State Gate, PM Gate, State Gate] 4행 패턴이 성립할 수
    없다. 신규 태스크는 gate-pass를 사용하지 않으며, PM Gate는 단일 mark로 통과한다.
    이 명령은 아직 옛 행 구조를 보유한 in-flight 레거시 state.json 하위호환을 위해서만
    유지되며, 성공 응답에 deprecated=True를 포함한다. 후속 버전에서 제거 예정.
    """
    command = "gate-pass"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)

    start_id = args.start
    rows     = state["rows"]

    # start_id 위치 찾기
    start_index = None
    for i, row in enumerate(rows):
        if row["row_id"] == start_id:
            start_index = i
            break
    if start_index is None:
        err(command, "row_not_found", row_id=start_id)

    # 4행 범위 확인
    if start_index + 3 >= len(rows):
        err(command, "gate_pattern_mismatch",
            message=f"rows {start_id}~{start_id+3} out of range (total rows: {len(rows)})",
            expected="QA Gate at row N")

    gate_rows = rows[start_index:start_index + 4]

    # 시작 행 검증 (§2.13 G-10 단계 1)
    if gate_rows[0]["item"] != "QA Gate":
        err(command, "gate_pattern_mismatch",
            expected=f"QA Gate at row {start_id}",
            found=gate_rows[0]["item"])

    # 연속 4행 패턴 검증 (§2.13 G-10 단계 2)
    found_pattern = [r["item"] for r in gate_rows]
    if found_pattern != GATE_PATTERN:
        err(command, "gate_pattern_mismatch",
            expected=GATE_PATTERN,
            found=found_pattern)

    # stage 일관성 검증 (§2.13 G-10 단계 3)
    stages = {r["stage"] for r in gate_rows}
    if len(stages) > 1:
        err(command, "gate_stage_mixed",
            message=f"4행 stage가 혼합됨: {list(stages)}")

    now_str = get_kst_datetime(command)
    stage   = gate_rows[0]["stage"]

    # 순차 ✅ 처리 (§2.13 G-10 단계 4)
    passed_ids = []
    for row in gate_rows:
        row["status"]       = "done"
        row["status_label"] = "✅"
        row["timestamp"]    = now_str
        if not row.get("owner"):
            row["owner"] = "PM"
        passed_ids.append(row["row_id"])

    state["updated_at"] = now_str
    save_state_json(task_path, state)

    # §2.17 트리거 #6
    decision = f"Gate Pass: rows {passed_ids[0]}~{passed_ids[-1]}, stage={stage}"
    reason   = args.note or "(none)"

    _jw = sync_state_md(task_path, state, now_str, command,
                        decision=decision, reason=reason)

    ok(command, rows_passed=passed_ids, stage=stage, timestamp=now_str,
       deprecated=True,
       deprecation_note="gate-pass is deprecated (014 Phase 4): new standard rows have no QA/State Gate rows; use single mark for PM Gate.",
       **(_jw or {}))

# ── 10. verify ───────────────────────────────────────────────────────────────

# 헌법 §4 "Don't fake it" — TEST-SCENARIO.md mock 코드 패턴 검출
# M-2 / (034): 코드 사용 패턴만 정규식 매칭; 단순 "mock" 단어/설명 문구는 제외.
#   'MagicMock' 맨 단어 대안 제거 — 산문(예: PM Gate 표준 문구 "MagicMock 등 부재")을
#   오탐하던 #1 원인. 실제 MagicMock() 호출은 'Mock\(' 대안이 이미 커버한다(잉여 입증: PLAN §2.1.2).
_MOCK_CODE_PATTERNS = re.compile(
    r"unittest\.mock|@patch\b|mock\.patch|Mock\(|@mock\."
)

# Pass 행 결과 키워드
_PASS_KEYWORDS = re.compile(r"^\s*(Pass|PASS|✅)\s*$")


def _find_scenario_file(task_path, scenario_arg):
    """TEST-SCENARIO.md 경로를 결정한다.
    --scenario 인자가 있으면 그 경로를 사용, 없으면 <task_path>/TEST-SCENARIO.md 시도.
    파일이 없으면 None 반환 (doc-only skip 처리).
    """
    if scenario_arg:
        p = pathlib.Path(scenario_arg)
    else:
        p = pathlib.Path(task_path) / "TEST-SCENARIO.md"
    return p if p.exists() else None


def _check_mock_patterns(lines):
    """코드 패턴 검출 — 위반 라인 번호 목록 반환.

    034 #2: 인라인 백틱(`...`) 코드 예시는 문서화/설명 표기이므로 검사 전 제거한다.
            코드펜스(```) 내부·백틱 밖 bare 라인의 실제 mock 코드는 그대로 검출(헌법 §4 유지).
            코드펜스 경계선(```/~~~으로 시작하는 줄) 자체는 검사 제외.
            백틱 미닫힘 시 해당 구간 미제거(fail-safe — 의심 시 검사 방향).
    """
    violations = []
    in_fence = False
    for lineno, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue                          # 펜스 경계선 자체는 검사 제외
        if in_fence:
            target = line                     # 코드펜스 내부 = 실제 코드 → 원문 검사
        else:
            target = re.sub(r"`[^`]*`", "", line)   # 인라인 백틱 구간 제거 후 검사
        if _MOCK_CODE_PATTERNS.search(target):
            violations.append(lineno)
    return violations


def _check_evidence(lines):
    """Pass 시나리오에 실행 증거 누락 검출 — 위반 라인 번호 목록 반환.

    탐지 전략:
    - 마크다운 표의 각 행(| ... |)을 파싱한다.
    - 셀 중 하나가 Pass/PASS/✅인 행에서 "실행 명령" 또는 "결과/출력"에 해당하는
      셀이 비어있으면 (empty or whitespace-only) 위반으로 간주한다.
    - 열 헤더는 "결과", "출력", "실행 명령"을 포함하는 행으로 인식한다.
    - 헤더를 찾기 전에 Pass 행이 나타나면 보수적 판정(위반 아님).
    """
    violations = []
    header_indices = []   # 증거 관련 열 인덱스 (실행 명령/출력)
    result_indices = []   # "결과" 열 인덱스 (Pass 판별용)
    in_header = False

    for lineno, line in enumerate(lines, start=1):
        # 마크다운 표 행 판별
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        # 구분선 행(|---|) 스킵
        if re.match(r"^\|[\s\-:]+\|", stripped):
            continue

        cells = [c.strip() for c in stripped.split("|")]
        # split 결과는 앞뒤 빈 문자열 포함 → [1:-1] 로 실제 셀만
        cells = cells[1:-1] if len(cells) > 2 else cells

        # 헤더 행 감지: "결과" 또는 "실행 명령" 또는 "출력" 셀 포함
        is_header = any(
            c in ("결과", "실행 명령", "출력", "결과/출력") for c in cells
        )
        if is_header:
            header_indices = [
                i for i, c in enumerate(cells)
                if c in ("실행 명령", "출력", "결과/출력")
            ]
            # "결과" 열 인덱스를 별도로 기억 (Pass 판별용)
            result_indices = [
                i for i, c in enumerate(cells)
                if c == "결과"
            ]
            in_header = True
            continue

        if not in_header:
            continue

        # 데이터 행: 결과 열이 Pass/PASS/✅인지 확인
        is_pass_row = any(
            i < len(cells) and _PASS_KEYWORDS.match(cells[i])
            for i in result_indices
        )
        if not is_pass_row:
            continue

        # 증거 열(실행 명령/결과/출력)이 비어있으면 위반
        for i in header_indices:
            if i < len(cells) and cells[i] == "":
                violations.append(lineno)
                break

    return violations


def _check_red_evidence(lines):
    """RED 증거 누락 검출 (016 RED-first) — 위반 라인 번호 목록 반환.

    탐지 전략 (_check_evidence 패턴 미러):
    - 마크다운 표에서 "RED 증거" 헤더 열을 찾는다.
    - 데이터 행에서 "RED 증거" 셀이 비어있으면(empty/whitespace) 위반으로 간주한다.
    - "RED 증거" 헤더가 없으면 보수적 판정(위반 아님 — RED 게이트 미적용 표).
    근거: PLAN 016 §3.2.2 — RED 단계 실패 출력 증거 선확보. 헌법 §4.
    """
    violations = []
    red_idx = None
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:]+\|", stripped):  # 구분선 행 스킵
            continue
        cells = [c.strip() for c in stripped.split("|")]
        cells = cells[1:-1] if len(cells) > 2 else cells
        if red_idx is None:
            # 헤더 행 탐지: "RED 증거" 셀 포함
            if any(c == "RED 증거" for c in cells):
                red_idx = next(i for i, c in enumerate(cells) if c == "RED 증거")
            continue
        # 데이터 행: RED 증거 셀이 비어있으면 위반
        if red_idx < len(cells) and cells[red_idx] == "":
            violations.append(lineno)
    return violations


def _match_test_files(changed_files, test_globs):
    """changed_files 중 test_globs(fnmatch) 패턴에 매칭되는 파일 목록 반환 (016 테스트 불변성).

    러너/언어/경로 하드코딩 금지 — 패턴은 호출자가 주입(--test-globs, C-2).
    표준 라이브러리 fnmatch만 사용 (T-11).
    """
    matched = []
    for f in (changed_files or []):
        for pat in (test_globs or []):
            if fnmatch.fnmatch(f, pat):
                matched.append(f)
                break
    return matched


# ── 명확화 게이트 헬퍼 (005) ─────────────────────────────────────────────────

# 명확화 4요소 — 행 라벨(첫 셀)에서 키워드로 식별. 순서/표기 변형 흡수.
_CLARIFICATION_ELEMENTS = ["목표", "범위", "제약", "완료기준"]

# "N/A: <사유>" 또는 "NA: <사유>" 는 PASS로 간주 (명시적 해당없음).
_NA_PATTERN = re.compile(r"^N/?A\s*[:：]", re.IGNORECASE)
# 공란 / "TBD"(대소문자 무관) / "-" 단독 → FAIL (미확정으로 간주).
_TBD_PATTERN = re.compile(r"^\s*(TBD|-)?\s*$", re.IGNORECASE)

_SDLC_V2_REQUIRED_TASK_SECTIONS = (
    "Problem",
    "Proposed outcome",
    "Affected users and systems",
    "Constraints",
    "Acceptance criteria",
)

_WORK_ITEMS_REQUIRED_COLUMNS = (
    "작업",
    "담당",
    "변경 대상",
    "구체적 변경",
    "선행 작업",
    "실행 그룹",
    "완료 기준 연결",
)

_WORK_ITEM_ID_RE = re.compile(r"\bW-\d+\b")
_PLAN_GROUP_RE = re.compile(r"\bP(\d+)\b", re.IGNORECASE)
_PLAN_COMPLETION_REF_RE = re.compile(r"\b(AC|C)-\d+\b")


def _read_markdown(path):
    try:
        return pathlib.Path(path).read_text(encoding="utf-8")
    except OSError:
        return None


def _first_frontmatter_template(text):
    """첫 YAML frontmatter의 template 값을 반환한다. v2 판정은 exact 라인만 허용한다."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            for line in lines[1:idx]:
                stripped = line.strip()
                if stripped == "template: sdlc-v2":
                    return "sdlc-v2"
                if stripped.startswith("template:"):
                    return stripped[len("template:"):].strip()
            return None
    return None


def _is_sdlc_v2_markdown(path):
    text = _read_markdown(path)
    return bool(text is not None and _first_frontmatter_template(text) == "sdlc-v2")


def _normalize_md_cell(cell):
    return re.sub(r"\s+", " ", cell.replace("`", "").strip())


def _section_body_by_heading(text, heading):
    """H2 heading 본문을 다음 H2 전까지 반환한다. 없으면 None."""
    lines = text.splitlines()
    start = None
    wanted = heading.strip().lower()
    for idx, line in enumerate(lines):
        m = re.match(r"^##\s+(.+?)\s*$", line.strip())
        if m and m.group(1).strip().lower() == wanted:
            start = idx + 1
            break
    if start is None:
        return None
    body = []
    for line in lines[start:]:
        if re.match(r"^##\s+", line.strip()):
            break
        body.append(line)
    return "\n".join(body).strip()


def _check_sdlc_v2_task_contract(task_md_path):
    """sdlc-v2 TASK.md 필수 5절이 존재하고 비어 있는지 검사한다."""
    text = _read_markdown(task_md_path)
    if text is None:
        return None
    if _first_frontmatter_template(text) != "sdlc-v2":
        return None
    missing = []
    for heading in _SDLC_V2_REQUIRED_TASK_SECTIONS:
        body = _section_body_by_heading(text, heading)
        if body is None or _TBD_PATTERN.match(body):
            missing.append(heading)
    return missing


def _extract_ids_from_section(text, heading, prefix):
    body = _section_body_by_heading(text, heading)
    if body is None:
        return set()
    return set(re.findall(r"\b" + re.escape(prefix) + r"-\d+\b", body))


def _extract_ac_c_ids(task_md_path):
    text = _read_markdown(task_md_path)
    if text is None:
        return set(), set()
    return (
        _extract_ids_from_section(text, "Acceptance criteria", "AC"),
        _extract_ids_from_section(text, "Constraints", "C"),
    )


def _parse_markdown_table(lines, required_columns):
    header_idx = None
    headers = None
    required_norm = [_normalize_md_cell(c) for c in required_columns]
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("|") or "|" not in stripped[1:]:
            continue
        cells = [_normalize_md_cell(c) for c in stripped.strip("|").split("|")]
        if all(c in cells for c in required_norm):
            header_idx = idx
            headers = cells
            break
    if header_idx is None:
        return None, []

    rows = []
    for line in lines[header_idx + 1:]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows:
                break
            continue
        cells = [_normalize_md_cell(c) for c in stripped.strip("|").split("|")]
        if cells and all(set(c) <= {"-", ":"} for c in cells):
            continue
        if len(cells) < len(headers):
            cells += [""] * (len(headers) - len(cells))
        rows.append(dict(zip(headers, cells)))
    return headers, rows


def _extract_work_items(plan_md_path, include_headers=False):
    text = _read_markdown(plan_md_path)
    if text is None or _first_frontmatter_template(text) != "sdlc-v2":
        return (None, None) if include_headers else None
    body = _section_body_by_heading(text, "Work items")
    if body is None:
        return ([], []) if include_headers else []
    _headers, rows = _parse_markdown_table(
        body.splitlines(), _WORK_ITEMS_REQUIRED_COLUMNS)
    if include_headers:
        return _headers, rows
    return rows


def _work_item_id(row):
    m = _WORK_ITEM_ID_RE.search(row.get("작업", ""))
    return m.group(0) if m else None


def _work_item_targets(row):
    raw = row.get("변경 대상", "")
    candidates = []
    for m in re.finditer(r"`([^`]+\.[A-Za-z0-9]+)`", raw):
        candidates.append(m.group(1))
    raw_without_ticks = re.sub(r"`[^`]+`", " ", raw)
    candidates.extend(re.findall(
        r"(?:[A-Za-z0-9_.가-힣-]+/)+[A-Za-z0-9_.가-힣-]+\.[A-Za-z0-9]+",
        raw_without_ticks,
    ))
    targets = []
    for tok in candidates:
        tok = tok.strip(" .;()[]")
        if tok and _is_safe_artifact_token(tok) and tok not in targets:
            targets.append(tok)
    return targets


def _work_item_dependencies(row):
    raw = row.get("선행 작업", "")
    if raw in ("", "-", "없음", "N/A"):
        return []
    return _WORK_ITEM_ID_RE.findall(raw)


def _work_item_group_number(row):
    m = _PLAN_GROUP_RE.search(row.get("실행 그룹", ""))
    return int(m.group(1)) if m else None


def _has_path_between(graph, start, goal, seen=None):
    seen = seen or set()
    if start in seen:
        return False
    seen.add(start)
    if start == goal:
        return True
    return any(_has_path_between(graph, nxt, goal, seen) for nxt in graph.get(start, []))


def _check_plan_contract(task_path):
    """sdlc-v2 PLAN.md Work items 계약을 검사한다. legacy PLAN은 skip 신호를 반환."""
    task_dir = pathlib.Path(task_path)
    plan_md = task_dir / "PLAN.md"
    text = _read_markdown(plan_md)
    if text is None:
        return {"status": "skipped", "reason": "plan_md_absent", "missing": []}
    if _first_frontmatter_template(text) != "sdlc-v2":
        return {"status": "skipped", "reason": "legacy_plan", "missing": []}

    headers, rows = _extract_work_items(plan_md, include_headers=True)
    if rows is None:
        return {"status": "skipped", "reason": "legacy_plan", "missing": []}
    missing = []
    if not rows:
        missing.append("Work items table")
    if tuple(headers or ()) != _WORK_ITEMS_REQUIRED_COLUMNS:
        missing.append("Work items: required 7 columns")

    ids = []
    previous_group = None
    for pos, row in enumerate(rows, 1):
        wid = _work_item_id(row)
        if wid is None:
            missing.append(f"row {pos}: W-ID")
            continue
        ids.append(wid)
        for col in _WORK_ITEMS_REQUIRED_COLUMNS:
            if _TBD_PATTERN.match(row.get(col, "")):
                missing.append(f"{wid}: {col}")
        if _work_item_group_number(row) is None:
            missing.append(f"{wid}: 실행 그룹 Pn")
        if not _PLAN_COMPLETION_REF_RE.search(row.get("완료 기준 연결", "")):
            missing.append(f"{wid}: 완료 기준 연결 AC/C")
        cur_group = _work_item_group_number(row)
        if cur_group is not None:
            if previous_group is not None and cur_group < previous_group:
                missing.append(f"{wid}: P group order")
            previous_group = cur_group

    duplicates = sorted({wid for wid in ids if ids.count(wid) > 1})
    missing += [f"duplicate {wid}" for wid in duplicates]
    id_set = set(ids)

    graph = {wid: [] for wid in id_set}
    row_by_id = {}
    for row in rows:
        wid = _work_item_id(row)
        if wid:
            row_by_id[wid] = row
    for row in rows:
        wid = _work_item_id(row)
        if not wid:
            continue
        for dep in _work_item_dependencies(row):
            if dep not in id_set:
                missing.append(f"{wid}: unknown dependency {dep}")
            else:
                graph.setdefault(dep, []).append(wid)
                dep_group = _work_item_group_number(row_by_id.get(dep, {}))
                cur_group = _work_item_group_number(row)
                if dep_group is not None and cur_group is not None and dep_group >= cur_group:
                    missing.append(f"{wid}: dependency group order {dep}")

    for wid in id_set:
        if any(_has_path_between(graph, nxt, wid, set()) for nxt in graph.get(wid, [])):
            missing.append(f"cycle at {wid}")
            break

    for i, left in enumerate(rows):
        lid = _work_item_id(left)
        lgroup = _work_item_group_number(left)
        if lid is None or lgroup is None:
            continue
        ltargets = set(_work_item_targets(left))
        for right in rows[i + 1:]:
            rid = _work_item_id(right)
            if rid is None or _work_item_group_number(right) != lgroup:
                continue
            overlap = sorted(ltargets & set(_work_item_targets(right)))
            if not overlap:
                continue
            left_depends = rid in _work_item_dependencies(left)
            right_depends = lid in _work_item_dependencies(right)
            if not left_depends and not right_depends:
                missing.append(f"P{lgroup}: file conflict {lid}/{rid}: {', '.join(overlap)}")

    task_md = task_dir / "TASK.md"
    ac_ids, c_ids = _extract_ac_c_ids(task_md)
    known_refs = ac_ids | c_ids
    if known_refs:
        for row in rows:
            wid = _work_item_id(row)
            if not wid:
                continue
            text_refs = set(re.findall(r"\b(?:AC|C)-\d+\b", row.get("완료 기준 연결", "")))
            unknown = sorted(text_refs - known_refs)
            if unknown:
                missing.append(f"{wid}: unknown completion ref {', '.join(unknown)}")

    return {
        "status": "pass" if not missing else "unmet",
        "reason": None,
        "missing": missing,
        "violations": missing,
        "work_items": ids,
    }


def _run_clarification_hook(task_path, state, row_index, command, auto_pass=False, force=False):
    """TASK→다음 단계 첫 행 진입 시 명확화 게이트 자동 훅 (005).

    발동 조건:
    - state에 TASK 단계가 존재해야 함 (TASK 행이 없는 파이프라인은 skip).
    - 대상 행이 TASK 단계가 아니어야 함.
    - 대상 행이 자기 stage의 첫 번째 행이어야 함 (is_first_of_stage).
    - 직전 행의 stage == TASK 이어야 함 (= TASK 단계 바로 다음 첫 행).

    정책 A(graceful skip): TASK.md/섹션 부재 시 pass (하위호환).
    --auto-pass 우회 불가 (close_gate 동형, §2.16 G-13 정합).
    --force 시 우회 허용 (긴급 탈출구, --note 필수는 호출자가 이미 보장).
    """
    rows = state["rows"]
    row = rows[row_index]

    # TASK 단계가 파이프라인에 존재하지 않으면 skip
    task_stage_exists = any(r["stage"] == "TASK" for r in rows)
    if not task_stage_exists:
        return

    # 대상 행이 TASK 단계면 skip (TASK 내부 전환은 게이트 대상 아님)
    if row["stage"] == "TASK":
        return

    # 대상 행이 자기 stage의 첫 행인지 확인
    is_first_of_stage = (row_index == 0 or rows[row_index - 1]["stage"] != row["stage"])
    if not is_first_of_stage:
        return

    # 직전 행이 TASK 단계인지 확인 (= TASK 마지막 행 직후 첫 다음 단계 행)
    prev_is_task = (row_index > 0 and rows[row_index - 1]["stage"] == "TASK")
    if not prev_is_task:
        return

    # --auto-pass 우회 거부 (close_gate 동형)
    if auto_pass:
        err(command, "clarification_gate_unmet",
            missing=["auto-pass cannot bypass clarification gate"])

    # --force 시 우회 허용
    if force:
        return

    # 하위호환: TASK.md 부재 → skip
    task_md = _find_task_md(task_path, None)
    if task_md is None:
        return

    # sdlc-v2 TASK는 새 필수 5절 계약으로 검사하고, legacy만 명확화 표를 소비한다.
    missing = _check_clarification_gate(task_md)
    if missing is None:
        return  # 하위호환: "## 명확화 결과" 섹션 부재 → skip

    if missing:
        err(command, "clarification_gate_unmet", missing=missing)


# ─────────────────────────────────────────────────────────────────────────────
# 106 F-004/F-005: code-scan 결과 인용 게이트 (PLAN §3.4.2 (1)~(5))
# ─────────────────────────────────────────────────────────────────────────────

# code-scan.js DEFAULT_CONFIG.extensions(code-scan.js:43) 사본 — 프로젝트
# .opal/code-scan.json이 extensions를 생략했을 때의 폴백이다. code-scan.js:351이
# `user.extensions || DEFAULT_CONFIG.extensions`로 **치환**(병합 아님)하므로 동형으로 둔다.
_CODE_SCAN_DEFAULT_EXTENSIONS = (
    ".py", ".js", ".ts", ".vue", ".jsx", ".tsx", ".svelte",
    ".kt", ".kts", ".java", ".swift",
)

# pm-review-gate.md 항목 14 Pass 조건 토큰 — 판정 기준을 **신설하지 않고** 그 문서의
# 조건(조회 계열 결과 필드 / code-map 계열 결과 필드 / 명령 인용)을 그대로 집행한다.
# 토큰 경계는 `[\w-]` 부재로 잡는다: `depends_on`(Step 의존 필드)이 `depends`로
# 오인되면 전 PLAN이 무조건 통과해 게이트가 무력화된다.
_CODE_SCAN_CITATION_RES = tuple(
    (_tok, re.compile(r"(?<![\w-])" + re.escape(_tok) + r"(?![\w-])"))
    for _tok in (
        "domain", "layer", "depends", "exports",          # 조회 계열 결과 필드
        "write_to", "reason", "coverage", "counts",        # code-map 계열 결과 필드
        "code-scan",                                       # 명령 인용
    )
)

# §4.2 실행 체크리스트 섹션 헤딩 / 각 Step의 '**파일**:' 라인
_PLAN_SECTION_42_RE = re.compile(r"^###\s+4\.2(\s|$)")
_PLAN_TARGET_FILE_RE = re.compile(r"^\s*[-*]\s*\*\*파일\*\*\s*:(.*)$")


def _collect_plan_target_files(plan_md_path):
    """PLAN.md 대상 파일을 수집한다.

    sdlc-v2는 Work items의 `변경 대상` 열을 우선 사용한다. legacy PLAN은
    §4.2 각 Step의 '**파일**:' 라인에서 경로 토큰을 수집한다.
    """
    work_items = _extract_work_items(plan_md_path)
    if work_items is not None:
        targets = []
        for row in work_items:
            for target in _work_item_targets(row):
                if target not in targets:
                    targets.append(target)
        return targets

    try:
        lines = pathlib.Path(plan_md_path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    in_section = False
    targets = []
    for line in lines:
        if line.startswith("### "):                     # h3 경계에서만 섹션 판정
            in_section = bool(_PLAN_SECTION_42_RE.match(line))
            continue
        if not in_section:
            continue
        m = _PLAN_TARGET_FILE_RE.match(line)
        if not m:
            continue
        for tok in re.split(r"[,\s]+", m.group(1).replace("`", "")):
            tok = tok.strip()
            if not tok or not os.path.splitext(tok)[1]:  # 확장자 없는 산문 토큰 폐기
                continue
            if not _is_safe_artifact_token(tok):
                continue
            targets.append(tok)
    return targets


def _check_code_scan_citation(plan_md_path):
    """PLAN.md 본문에 code-scan 결과 인용이 있는지 판정한다 (PLAN §3.4.2 (2)).

    판정 기준은 신설하지 않는다 — pm-review-gate.md 항목 14 Pass 조건 토큰 중
    1건 이상이 본문에 존재하면 통과다.
    반환: [] 통과 / ["citation_absent"] 미충족 / None(실행 입력 섹션 자체 부재 → 하위호환 skip).
    """
    try:
        body = pathlib.Path(plan_md_path).read_text(encoding="utf-8")
    except OSError:
        return None
    has_sdlc_work_items = (
        _first_frontmatter_template(body) == "sdlc-v2"
        and _section_body_by_heading(body, "Work items") is not None
    )
    has_legacy_42 = any(_PLAN_SECTION_42_RE.match(ln) for ln in body.splitlines())
    if not has_sdlc_work_items and not has_legacy_42:
        return None                                     # 하위호환: §4.2 섹션 부재
    if any(rx.search(body) for _, rx in _CODE_SCAN_CITATION_RES):
        return []
    return ["citation_absent"]


def _run_code_scan_citation_hook(task_path, state, row_index, command,
                                 auto_pass=False, force=False):
    """EXECUTE 단계 첫 행 진입 시 code-scan 결과 인용 게이트 자동 훅 (PLAN §3.4.2 (3)).

    **게이트 순서 자체가 계약이다.** [MUST] `opal/tools/code-scan/code-map-hook.js:121-124`가
    "이 게이트는 ⑥ code-map 로딩보다 **반드시 위**에 있어야 한다 … 순서 자체가 계약이며,
    게이트 위에서 code-map을 읽어서는 안 된다"로 동형 규율을 못 박고 있다. 아래 순서를
    바꾸면 조용히 이탈해야 할 트리에서 거부·출력이 발생한다:

        ① 발동 조건 → ② force 우회 → ③ 자산 게이트 → ④ 산출물 게이트
        → ⑤ 적용 범위 게이트 → ⑥ auto_pass 거부 → ⑦ 판정

    [MUST] ⑥(auto_pass 거부)은 graceful skip인 ③④⑤ **뒤**에 둔다 — 앞에 두면
    문서 전용 태스크·code-scan 미보급 프로젝트에서 거부가 발생해 R-5 오탐 0건이
    깨진다(H-7). 형제 훅 `_run_clarification_hook`은 auto_pass 거부를 skip보다
    앞에 두므로, 그 배치를 그대로 답습하지 않는다.

    반환: None(발동 안 함/skip/통과) · missing 리스트(force로 우회한 경우 —
    호출자가 의사결정 로그에 기재한다, `check_gate_artifacts` 동형).
    """
    rows = state["rows"]
    row = rows[row_index]

    # ① 발동 조건 — 대상 행이 EXECUTE 단계이고, 자기 stage의 첫 행일 때만 발동
    if row["stage"] != "EXECUTE":
        return
    if row_index > 0 and rows[row_index - 1]["stage"] == "EXECUTE":
        return

    # ② --force 우회 허용 (긴급 탈출구 — --note 필수는 호출자가 이미 보장).
    #    [MUST] force는 **거부(err)만** 무력화하고 조기 반환하지 않는다 — ③④⑤의
    #    graceful skip과 ⑥⑦의 판정을 force에서도 그대로 통과시켜 "실제로 거부될
    #    상태였는지"를 확정한 뒤, 우회 사유를 호출자에게 반환해 의사결정 로그
    #    기재를 강제한다(091 `gate_artifact_force` 동형 — 거부될 상태가 아니면
    #    None을 돌려 무기재). ②의 계약("조용히 이탈해야 할 트리에서 거부·출력
    #    금지")은 ⑥⑦의 err가 force에서 발생하지 않으므로 그대로 보존된다:
    #    `pm-review-gate.md` §표준 검토 항목 14가 단언하는 기재를 도구가 집행한다.

    # ③ 자산 게이트 (F-005) — code-scan 미보급 프로젝트는 조용히 통과(code_scan_unavailable).
    #    code-map 자산(manifest) 존재는 요구하지 않는다: headerSource=inline +
    #    code-map 부재는 정상 상태이며, 이를 조건으로 걸면 inline 프로젝트 전건이
    #    스킵되어 R-4가 무력화된다(PLAN §3.5.2).
    root = task_root(task_path)
    if root is None:
        return
    cfg_path = root / ".opal" / "code-scan.json"
    if not cfg_path.is_file():
        return
    try:
        config = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if config.get("headerSource") not in ("inline", "manifest"):
        return

    # ④ 산출물 게이트 — PLAN.md 부재 시 하위호환 skip(plan_md_absent)
    plan_md = pathlib.Path(task_path) / "PLAN.md"
    if not plan_md.is_file():
        return

    # ⑤ 적용 범위 게이트 (F-005) — §4.2 대상 파일에 code-scan 적용 확장자가
    #    0건이면 순수 문서 태스크다(doc_only_task).
    extensions = config.get("extensions") or list(_CODE_SCAN_DEFAULT_EXTENSIONS)
    if not any(os.path.splitext(t)[1] in extensions
               for t in _collect_plan_target_files(plan_md)):
        return

    # ⑥ --auto-pass 우회 거부 (close_gate·clarification_gate 동형) — [MUST] ③④⑤ 뒤
    if auto_pass:
        _missing = ["auto-pass cannot bypass code-scan citation gate"]
        if force:
            return _missing
        err(command, "code_scan_citation_unmet", missing=_missing)

    # ⑦ 판정 — None(§4.2 섹션 부재)·[](통과) 모두 통과, 그 외 거부
    missing = _check_code_scan_citation(plan_md)
    if missing:
        if force:
            return missing                        # 우회 — 호출자가 의사결정 로그에 기재
        err(command, "code_scan_citation_unmet", missing=missing)


def _find_task_md(task_path, task_md_arg):
    """TASK.md 경로 결정. --task-md 우선, 없으면 <task_path>/TASK.md. 부재 시 None."""
    p = pathlib.Path(task_md_arg) if task_md_arg else pathlib.Path(task_path) / "TASK.md"
    return p if p.exists() else None


def _locate_clarification_table(lines):
    """"## 명확화 결과" 섹션의 표를 "위치"만 탐색한다 (H-8 — 표 탐색은 공유,
    셀 해석·판정은 호출자별로 분리).

    반환: (section_lines, header_cells, header_line_idx) 튜플.
    섹션/표 부재 시 None (호출자가 graceful skip 정책 적용).
    """
    # 1) "## 명확화 결과" 헤더 위치 탐색
    section_start = None
    for i, line in enumerate(lines):
        if re.match(r"^##\s+명확화\s*결과", line.strip()):
            section_start = i
            break
    if section_start is None:
        return None  # 섹션 부재

    # 2) 다음 ## 헤더 직전까지 섹션 추출
    section_lines = []
    for line in lines[section_start + 1:]:
        if re.match(r"^##\s+", line.strip()):
            break
        section_lines.append(line)

    # 3) 표 헤더 행 탐색 — "|" 로 시작하고 구분선이 아닌 첫 행
    header_cells = None
    header_line_idx = None
    for idx, line in enumerate(section_lines):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:]+\|", stripped):
            continue  # 구분선 행 스킵
        cells = [c.strip() for c in stripped.split("|")]
        cells = cells[1:-1] if len(cells) > 2 else cells
        header_cells = cells
        header_line_idx = idx
        break

    if header_cells is None:
        return None  # 표 부재
    return section_lines, header_cells, header_line_idx


# "## 확정된 설계 방향" 불릿 파서 상수 (100 F-007, PLAN §3.7.2)
_DIRECTION_HEADING_RE = re.compile(r"^##\s+확정된\s*설계\s*방향")
# 최상위 불릿 = 들여쓰기 0칸에서 시작하는 `- ` / `* ` / `+ `
_TOP_LEVEL_BULLET_RE = re.compile(r"^[-*+]\s+")


def _locate_confirmed_direction_items(lines):
    """"## 확정된 설계 방향" 섹션의 **최상위 불릿**을 항목으로 수집한다
    (100 F-007, PLAN §3.7.2).

    `## 명확화 결과`는 표지만 이 섹션은 불릿 리스트다 — 탐색 단위가 다르므로
    `_locate_clarification_table`(표 탐색)을 재사용하지 않는 **형제 함수**로
    둔다(H-8: 표 탐색은 공유, 불릿 탐색은 분리).

    반환: [{"element", "confirmed", "dependency", "source"}] 리스트.
      - 섹션 부재 → None (호출자 graceful skip — 레거시 TASK.md 회귀 없음)
      - 섹션은 있으나 최상위 불릿 0건 → [] (분모 0 나눗셈은 호출자가 회피)

    불릿에는 확정값/의존 사실 열 구분이 없으므로 `confirmed`·`dependency`에
    같은 불릿 본문을 넣는다 — 태그(`[결정]`/`[사실]`) 판정과 인용 추출이 같은
    문자열을 대상으로 수행된다. verdict 판정은 프로젝트 루트(`root`)를 쥔
    호출자(`_check_evidence_gate`) 몫이다.

    [계약] `element`는 불릿 본문 원문을 그대로 담는다 — 인덱스형 불투명 라벨은
    PM이 어떤 항목이 미확정인지 식별할 수 없게 하므로 계약 위반이다.
    중첩(들여쓴) 불릿과 그 이어쓰기 행은 항목으로 수집하지 않는다.
    """
    section_start = None
    for i, line in enumerate(lines):
        if _DIRECTION_HEADING_RE.match(line.strip()):
            section_start = i
            break
    if section_start is None:
        return None  # 섹션 부재

    texts = []
    in_nested = False
    for line in lines[section_start + 1:]:
        stripped = line.strip()
        if re.match(r"^##\s+", stripped):
            break  # 다음 ## 헤더 직전까지
        if not stripped:
            continue
        m = _TOP_LEVEL_BULLET_RE.match(line)
        if m:
            in_nested = False
            texts.append(line[m.end():].strip())
            continue
        if _TOP_LEVEL_BULLET_RE.match(stripped):
            in_nested = True  # 들여쓴 중첩 불릿 — 최상위가 아니므로 비수집
            continue
        if texts and not in_nested and line[:1].isspace():
            texts[-1] = (texts[-1] + " " + stripped).strip()  # 최상위 불릿 이어쓰기

    return [{"element": t, "confirmed": t, "dependency": t,
             "source": "confirmed_direction"} for t in texts]


def _parse_clarification_table(lines):
    """TASK.md "## 명확화 결과" 섹션의 표를 파싱.

    반환: {element_label: confirmed_value_cell_text} 딕셔너리.
    섹션/표 부재 시 None 반환 (호출자가 graceful skip).
    "확정값" 열을 헤더에서 식별; 없으면 라벨 다음(2번째) 셀을 확정값으로 폴백.

    [098] `_locate_clarification_table`(표 탐색)을 호출하는 얇은 래퍼 — 기존
    dict 반환 계약은 그대로 유지한다(H-8, 하위호환 파서 무접촉).
    """
    located = _locate_clarification_table(lines)
    if located is None:
        return None
    section_lines, header_cells, header_line_idx = located

    # "확정값" 열 인덱스 식별. 미발견 시 폴백: 라벨 다음(인덱스 1) 셀
    confirmed_col_idx = None
    for ci, cell in enumerate(header_cells):
        if "확정값" in cell:
            confirmed_col_idx = ci
            break
    if confirmed_col_idx is None and len(header_cells) >= 2:
        confirmed_col_idx = 1
    if confirmed_col_idx is None:
        return None  # 표 부재(열 2개 미만)

    # 데이터 행 파싱 — 첫 셀이 4요소 키워드를 포함하면 {라벨: 확정값셀}
    result = {}
    for line in section_lines[header_line_idx + 1:]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:]+\|", stripped):
            continue
        cells = [c.strip() for c in stripped.split("|")]
        cells = cells[1:-1] if len(cells) > 2 else cells
        if not cells:
            continue
        label = cells[0]
        # 4요소 중 하나와 매칭되는지 확인
        for elem in _CLARIFICATION_ELEMENTS:
            if elem in label:
                confirmed_val = cells[confirmed_col_idx] if confirmed_col_idx < len(cells) else ""
                result[elem] = confirmed_val
                break

    return result


def _check_clarification_gate(task_md_path):
    """TASK 잠금 검증. 반환: missing[] (빈 리스트면 PASS).

    sdlc-v2는 필수 5절(Problem/Proposed outcome/Affected users and systems/
    Constraints/Acceptance criteria)을 검사한다. legacy는 기존 명확화 4요소
    표를 검사한다.
    None 반환 = legacy 섹션/표 부재 (호출자가 하위호환 정책 적용 — graceful skip).
    """
    sdlc_missing = _check_sdlc_v2_task_contract(task_md_path)
    if sdlc_missing is not None:
        return sdlc_missing

    lines = task_md_path.read_text(encoding="utf-8").splitlines()
    table = _parse_clarification_table(lines)
    if table is None:
        return None  # 섹션/표 부재 신호

    missing = []
    for elem in _CLARIFICATION_ELEMENTS:
        cell = table.get(elem)
        if cell is None:                        # 요소 행 자체가 표에 없음
            missing.append(elem)
        elif _NA_PATTERN.match(cell.strip()):
            continue                             # N/A: <사유> → PASS
        elif _TBD_PATTERN.match(cell):          # 공란 / TBD / "-" → FAIL
            missing.append(elem)
    return missing


# ─────────────────────────────────────────────────────────────────────────────
# 근거 등급 확정/미확정 판정 (098 F-003, PLAN §3.3.2)
# ─────────────────────────────────────────────────────────────────────────────

# 인용 토큰 추출 — 인라인 코드 스팬(백틱)·마크다운 링크·단축 참조(→ D-N ...) 3종.
# 백틱 스팬에 괄호 주석이 바로 동반되면(예: `path`(`func`)) 앞뒤 백틱 스팬과 그
# 괄호를 통째로 소비해 괄호 내용은 별도 토큰으로 취급하지 않는다.
_CITATION_TOKEN_RE = re.compile(
    r"\[[^\]]*\]\([^)]+\)"      # ③ 마크다운 링크
    r"|\(→[^)]*\)"               # ④ 단축 참조
    r"|`[^`]+`(?:\([^)]*\))?"    # ①·② 인라인 코드 스팬 (+ 선택적 괄호 주석 폐기)
)

# 형식① `경로:N` / `경로:N-M` 판별
_CITATION_LINE_RE = re.compile(r"^(.+):(\d+)(?:-\d+)?$")

# 등급 패턴 기본 세트(1차, PLAN §3.3.2) — E1(실행 관측)·E3(생성 코드)은 경로
# 패턴으로 판별 불가하므로 자동 부여 대상이 아니다(unknown으로 귀결, H-11).
_EVIDENCE_GRADE_PATTERNS = (
    ("E5", (".opal/brain/**", ".opal/code-scan.json", "*code-map*")),
    ("E4", ("docs/**", "*.md")),
    ("E2", ("**/tests/**", "test_*.py", "*.py", "*.ts", "*.tsx", "*.js", "*.sh", "*.json")),
)


def _extract_citations(cell):
    """'의존 사실' 셀에서 인용 토큰 원문 목록을 추출한다.
    백틱 밖 산문·단독 괄호 주석은 경로 후보가 아니다 — 백틱 안 경로 스팬 또는
    마크다운 링크·단축 참조만 취한다. 셀이 비었거나 '-'이면 [] 반환."""
    if not cell or not cell.strip() or cell.strip() == "-":
        return []
    tokens = []
    for m in _CITATION_TOKEN_RE.finditer(cell):
        text = m.group(0)
        if text.startswith("`"):
            tokens.append(re.match(r"`[^`]+`", text).group(0))  # 앞 스팬만(괄호 주석 폐기)
        else:
            tokens.append(text)
    return tokens


def _grade_path_pattern(path):
    """경로 문자열 → 등급('E5'|'E4'|'E2'|'unknown'). 매칭 패턴 없으면 'unknown'."""
    for grade, patterns in _EVIDENCE_GRADE_PATTERNS:
        if any(fnmatch.fnmatch(path, pat) for pat in patterns):
            return grade
    return "unknown"


def _resolve_citation_exists(path, line_no, root=None):
    """프로젝트 루트(`root`) 기준 경로 존재 판정.
    line_no 지정(형식①): 파일 존재 AND line_no <= 파일 총 줄수.
    line_no 미지정(형식②): 경로 존재만(파일/디렉토리 무관), §N 유효성은 미검사.
    절대경로·'..' 이탈 토큰은 `_is_safe_artifact_token` 재사용으로 미존재 처리
    (fail-safe — PLAN §5.4 보안 요구). `root`는 호출자(`_check_evidence_gate`)가
    1회 계산해 전달한다(098 ADD-2 — 배포 경로에서도 등가 판정). `root`가
    None이면(호출자 전달 실패) 기존 fail-safe대로 미존재 처리한다."""
    if not _is_safe_artifact_token(path):
        return False
    if root is None:
        return False
    target = root / path
    if line_no is None:
        return target.exists()
    if not target.is_file():
        return False
    try:
        with target.open("r", encoding="utf-8", errors="replace") as f:
            total_lines = sum(1 for _ in f)
    except OSError:
        return False
    return line_no <= total_lines


def _grade_citation(raw, root=None):
    """인용 토큰 원문 → (grade, exists). PLAN §3.3.2 인용 형식별 파싱 계약 4종.

    ① `경로:N`/`경로:N-M` — 경로 패턴 매핑 등급 + 파일·줄 실존 검사.
    ② `` `경로` §N `` (및 §N 없는 바른 백틱 경로) — 경로 패턴 매핑 등급 + 경로
       존재만(§N 유효성 미검사).
    ③ `[사이트명](URL)` — 네트워크 접근 금지, grade:'unknown' exists:None.
    ④ `(→ D-N §N)` 단축 참조 — 테이블 역참조 미해석, grade:'unknown' exists:None.
    디렉토리 없는 파일명 단독 토큰(경로에 '/' 없음)은 저장소 탐색을 수행하지
    않고 grade:'unknown' exists:None으로 반환한다. `root`는 호출자가 1회
    계산한 프로젝트 루트를 그대로 `_resolve_citation_exists`로 릴레이한다
    (098 ADD-2)."""
    if raw.startswith("[") or raw.startswith("(→"):
        return "unknown", None

    inner = raw[1:-1] if raw.startswith("`") and raw.endswith("`") else raw
    m = _CITATION_LINE_RE.match(inner)
    if m:
        path, line_no = m.group(1), int(m.group(2))
    else:
        path, line_no = inner, None

    if "/" not in path:
        return "unknown", None

    grade = _grade_path_pattern(path)
    exists = _resolve_citation_exists(path, line_no, root)
    return grade, exists


def _has_decision_tag(cell):
    """확정값 셀에 사용자의 `[결정]` 태그가 있는지 확인 — 결정은 근거 판정
    대상이 아니다(PLAN §3.3.2, TASK.md §확정된 설계 방향 (5))."""
    return "[결정]" in (cell or "")


def _has_fact_tag(cell):
    """확정값 셀/불릿 본문에 `[사실]` 태그가 있는지 확인 — 상류에서 이미 대조
    확인된 사실이라는 표식이다(100 F-007, PLAN §3.7.2)."""
    return "[사실]" in (cell or "")


# confirmed로 계수하는 verdict 집합 — `확정`(근거 판정 통과·[결정] 면제)과
# `승계`([사실] 상류 대조 확인 승계) 둘 다 confirmed다(PLAN 100 §3.7.2).
_CONFIRMED_VERDICTS = ("확정", "승계")


def _evaluate_evidence_item(confirmed_cell, dependency_cell, root=None):
    """항목 1건 판정 — 도구 4축(① 인용 존재 ② 인용 유효 ③ 등급 부여 ④ E5 단독
    아님). 반환: (verdict, reasons, citations).

    [결정] 태그가 확정값 셀에 있으면 근거 없이도 확정 유지(축 판정을 건너뛴다).
    ③④ 및 grade:'unknown' 토큰은 "E5 아닌 근거"로 계수해 e5_sole_citation
    오탐을 방지한다. `root`는 호출자가 1회 계산한 프로젝트 루트를
    `_grade_citation`으로 릴레이한다(098 ADD-2).

    100 F-007: `[사실]` 태그가 있는 항목이 유효 인용(E2/E4 + 실존)으로 4축을
    통과하면 verdict는 `확정`이 아니라 `승계`다 — 상류에서 대조 확인된 사실을
    승계했음을 표시하며(재확인 면제), 계수상으로는 `확정`과 동등하다
    (`_CONFIRMED_VERDICTS`). 태그가 없는 기존 명확화 표 항목의 판정 결과는
    그대로 `확정`이다(하위호환)."""
    if _has_decision_tag(confirmed_cell):
        return "확정", [], []

    raws = _extract_citations(dependency_cell)
    if not raws:
        return "미확정", ["citation_missing"], []

    citations = []
    for raw in raws:
        grade, exists = _grade_citation(raw, root)
        citations.append({"raw": raw, "grade": grade, "exists": exists})

    # 인용 중 하나라도 "유효 등급(E2/E4) + 실존"이면 그 인용 하나로 확정된다 —
    # E5는 단독으로 확정시키지 못하고(④), 다른 인용의 존재 실패는 확정 인용이
    # 있으면 전체를 끌어내리지 않는다(S-35 양성 대조군).
    if any(c["grade"] in ("E2", "E4") and c["exists"] is True for c in citations):
        return ("승계" if _has_fact_tag(confirmed_cell) else "확정"), [], citations

    reasons = []
    if any(c["exists"] is False for c in citations):
        reasons.append("citation_path_not_found")

    non_unknown = [c for c in citations if c["grade"] != "unknown"]
    if not non_unknown:
        reasons.append("grade_unknown")

    e5_citations = [c for c in citations if c["grade"] == "E5"]
    non_e5_evidence = [c for c in citations if c["grade"] != "E5"]
    if e5_citations and not non_e5_evidence:
        reasons.append("e5_sole_citation")

    return "미확정", reasons, citations


def _check_evidence_gate(task_md_path):
    """TASK.md '## 명확화 결과' 표를 근거 등급 4축으로 판정한다(PLAN §3.3.2).

    반환: {"items":[{element,verdict,reasons,citations,source}],
    "confirmed_ratio": float, "direction_confirmed_ratio": float|None,
    "unconfirmed": [element,...]}. 섹션/표/'의존 사실' 열 부재 시 None(호출자가
    graceful skip). `unknown` 등급은 confirmed_ratio에서 미확정으로 계상한다
    (분자 제외·분모 포함) — 도구는 차단하지 않는다(exit 0 유지).

    100 F-007(PD-1 분리형): '## 확정된 설계 방향' 최상위 불릿을
    `_locate_confirmed_direction_items`로 함께 수집해 `items[]`에 병합하고,
    각 항목의 출처를 `source`(`clarification` | `confirmed_direction`)로
    구분한다. 두 소스는 **비율 분모를 공유하지 않는다** — 기존
    `confirmed_ratio`의 분모는 '## 명확화 결과' 항목 수로 불변이고(소비자
    계약 보호), 방향 항목 비율은 신규 키 `direction_confirmed_ratio`로 따로
    낸다(섹션 부재·항목 0건이면 None — 분모 0 나눗셈 없음).

    098 ADD-2: 인용 실존 판정용 프로젝트 루트를 여기서 1회 계산해 각 항목으로
    전달한다 — `task_md_path`(실제 태스크 경로) 기준 파생을 우선 시도하고
    (배포본이 `~/.opal/tools/state-tool/`에 있어도 태스크 경로는 항상 실제
    프로젝트 안에 있으므로 정상 판정), 실패 시 기존 `__file__` 기준 파생으로
    폴백한다(테스트 픽스처처럼 태스크 경로가 프로젝트 밖 임시 디렉토리인
    경우의 하위호환)."""
    root = (task_root(task_md_path)
            or task_root(str(pathlib.Path(__file__).resolve())))
    lines = task_md_path.read_text(encoding="utf-8").splitlines()
    located = _locate_clarification_table(lines)
    if located is None:
        return None
    section_lines, header_cells, header_line_idx = located

    confirmed_col_idx = None
    dependency_col_idx = None
    for ci, cell in enumerate(header_cells):
        if confirmed_col_idx is None and "확정값" in cell:
            confirmed_col_idx = ci
        if dependency_col_idx is None and "의존" in cell:
            dependency_col_idx = ci
    if confirmed_col_idx is None and len(header_cells) >= 2:
        confirmed_col_idx = 1
    if confirmed_col_idx is None or dependency_col_idx is None:
        return None  # 확정값/의존 사실 열 부재 — 레거시 스키마, graceful skip

    items = []
    for line in section_lines[header_line_idx + 1:]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:]+\|", stripped):
            continue
        cells = [c.strip() for c in stripped.split("|")]
        cells = cells[1:-1] if len(cells) > 2 else cells
        if not cells:
            continue
        label = cells[0]
        elem = next((e for e in _CLARIFICATION_ELEMENTS if e in label), None)
        if elem is None:
            continue
        confirmed_cell = cells[confirmed_col_idx] if confirmed_col_idx < len(cells) else ""
        dependency_cell = cells[dependency_col_idx] if dependency_col_idx < len(cells) else ""
        verdict, reasons, citations = _evaluate_evidence_item(confirmed_cell, dependency_cell, root)
        items.append({
            "element": elem, "verdict": verdict, "reasons": reasons, "citations": citations,
            "source": "clarification",
        })

    if not items:
        return None  # 데이터 행 부재 — graceful skip

    # [MUST] PD-1 — 기존 confirmed_ratio의 분모는 여기서 확정되며(명확화 결과
    # 항목 수), 아래 방향 항목 병합의 영향을 받지 않는다. 분모 확대는 이 키를
    # 읽는 소비자를 조용히 깨뜨린다.
    confirmed_count = sum(1 for it in items if it["verdict"] in _CONFIRMED_VERDICTS)
    ratio = confirmed_count / len(items)
    unconfirmed = [it["element"] for it in items
                   if it["verdict"] not in _CONFIRMED_VERDICTS]

    # 100 F-007 — '## 확정된 설계 방향' 불릿 병합(별도 분모)
    direction_ratio = None
    direction_rows = _locate_confirmed_direction_items(lines)
    if direction_rows:  # None(섹션 부재)·[](항목 0건) 모두 graceful skip
        direction_items = []
        for row in direction_rows:
            verdict, reasons, citations = _evaluate_evidence_item(
                row["confirmed"], row["dependency"], root)
            direction_items.append({
                "element": row["element"], "verdict": verdict,
                "reasons": reasons, "citations": citations,
                "source": row["source"],
            })
        direction_confirmed = sum(1 for it in direction_items
                                  if it["verdict"] in _CONFIRMED_VERDICTS)
        direction_ratio = direction_confirmed / len(direction_items)
        unconfirmed += [it["element"] for it in direction_items
                        if it["verdict"] not in _CONFIRMED_VERDICTS]
        items += direction_items

    return {"items": items, "confirmed_ratio": ratio,
            "direction_confirmed_ratio": direction_ratio,
            "unconfirmed": unconfirmed}


# ─────────────────────────────────────────────────────────────────────────────
# 157 PM 경로 독립 설계 게이트 (DEC-3~DEC-12, 원문 SSOT harness/design-gate.md)
#   PM 경로 판정은 rows에 key `plan.design_gate`가 있는지로만 내린다(DEC-3). 판정이
#   거짓이면 아래 가드·기록은 모두 no-op이라 기존 태스크 코드 경로와 응답 키 집합이
#   변하지 않는다(C-1).
# ─────────────────────────────────────────────────────────────────────────────

DESIGN_GATE_ROW_KEY = "plan.design_gate"
DESIGN_GATE_DOCS = ("TASK.md", "PLAN.md", "TEST-SCENARIO.md")
# 반복 상한 수치의 원문은 harness/guards.md §자동 루핑 제약 표가 소유한다(현재 3회).
DESIGN_GATE_LIMIT = 3
DESIGN_GATE_AXES = ("completeness", "decision_clarity", "executability", "recoverability")
DESIGN_GATE_SCENARIO_KEYS = ("goal", "adoption", "boundary")
DESIGN_GATE_FINDINGS_SECTIONS = ("직접 변경", "회귀 확인", "문서 갱신", "미확인 가정")
_DESIGN_REWRITE_DOCS = {
    "plan": ("PLAN.md",),
    "scenario": ("TEST-SCENARIO.md",),
    "both": ("PLAN.md", "TEST-SCENARIO.md"),
}
# 형제 test-tool — state-tool과 같은 인터프리터(sys.executable)로 직접 호출한다.
# 소스(opal/tools)·설치본(~/.opal/tools) 모두 형제 배치다(_MEMORY_TOOL 선례).
_TEST_TOOL_PY = pathlib.Path(__file__).resolve().parent.parent / "test-tool" / "test_tool.py"
# 167 — advisory 결과 계약(PLAN Decisions: advisory 결과 계약)과 목표-커버 게이트 행 key
_ADVISORY_KINDS = ("subsumed", "mergeable", "cheaper_layer", "misclassified")
_ADVISORY_ID_RE = re.compile(r"^A-\d+$")
_SCENARIO_ID_RE = re.compile(r"^S-\d+$")
SCENARIO_GATE_ROW_KEYS = ("test_scenario.scenario_gate", "plan.scenario_gate")
_FINDINGS_TOKEN_CHARS_RE = re.compile(r"^[A-Za-z0-9_.가-힣/-]+$")
# ADD-3: 백틱 토큰의 경로 판정 기준 — '/' 포함 또는 마지막 확장자가 알려진 파일 확장자일 때만 경로로 본다.
# os.replace, json.loads, v1.2 같은 코드 심볼/버전 표기를 경로로 오판하지 않기 위함.
_FINDINGS_KNOWN_EXTS = {
    "py", "md", "json", "js", "ts", "tsx", "jsx", "yaml", "yml", "toml",
    "sh", "txt", "csv", "html", "css", "sql", "cfg", "ini",
}


def _is_pm_design_path(state):
    """DEC-3 — PM 경로 판정 단일 지점."""
    return any(r.get("key") == DESIGN_GATE_ROW_KEY for r in state.get("rows", []))


def _design_gate_block(state):
    """PM 경로 태스크의 state.design_gate 블록(DEC-5). 없으면 초기값으로 만든다."""
    block = state.get("design_gate")
    if not isinstance(block, dict):
        block = {
            "status": "idle",
            "iteration": 0,
            "limit": DESIGN_GATE_LIMIT,
            "limit_from": 0,
            "task_confirm_req_hash": None,
            "current_attempt": None,
            "passed_bundle_hash": None,
            "approved_bundle_hash": None,
            "last_rewrite_target": None,
            "history": [],
        }
        state["design_gate"] = block
    return block


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _design_bundle(task_path, command):
    """DEC-4 — (파일별 sha256 dict, 묶음 hash). 부재 시 design_gate_input_missing."""
    base = pathlib.Path(task_path)
    missing = [name for name in DESIGN_GATE_DOCS if not (base / name).is_file()]
    if missing:
        err(command, "design_gate_input_missing", missing=missing)
    files = {name: _sha256_bytes((base / name).read_bytes()) for name in DESIGN_GATE_DOCS}
    joined = "\n".join(f"{name}\n{files[name]}" for name in DESIGN_GATE_DOCS)
    return files, _sha256_bytes(joined.encode("utf-8"))


def _task_requirement_hash(task_path, command):
    """DEC-4 — TASK.md `## Constraints`·`## Acceptance criteria` 본문 sha256."""
    task_md = pathlib.Path(task_path) / "TASK.md"
    text = _read_markdown(task_md)
    if text is None:
        err(command, "design_gate_input_missing", missing=["TASK.md"])
    constraints = _section_body_by_heading(text, "Constraints") or ""
    acceptance = _section_body_by_heading(text, "Acceptance criteria") or ""
    payload = f"## Constraints\n{constraints}\n## Acceptance criteria\n{acceptance}"
    return _sha256_bytes(payload.encode("utf-8"))


def _row_index_by_key(state, key):
    for idx, row in enumerate(state.get("rows", [])):
        if row.get("key") == key:
            return idx
    return None


def apply_pm_design_guards(task_path, state, row_index, command, *, auto_approved,
                           target_done, owner=None, auto_pass=False):
    """DEC-6·DEC-11 — advance/mark의 자동 승인 직후·저장 전 구간 가드와 확인 해시 기록.

    PM 경로가 아니면 즉시 반환한다. 거부는 err()로 종료되고 save 이전이라 state.json이
    바뀌지 않는다(H-2). `--force`는 이 함수를 우회하지 못한다(호출자가 force를 넘기지 않는다).
    EXECUTE 가드는 `execute.implement`가 pending인 진입 전이에서만 적용한다.
    """
    if not _is_pm_design_path(state):
        return
    rows = state["rows"]
    row = rows[row_index]
    key = row.get("key")

    # DEC-6 — 자동 승인 불가 mode에서 --owner user 없는 확인 행 mark 거부
    if (target_done and row.get("item") == "사용자 확인" and not auto_pass
            and owner != "user" and row.get("status") not in _COMPLETE_STATUSES):
        allowed, deny_reason = can_auto_approve_user_confirmation(row["stage"], state.get("mode"))
        if not allowed:
            err(command, "user_confirmation_required",
                row_id=row["row_id"], stage=row["stage"], key=key, item=row["item"],
                mode=state.get("mode"), reason=deny_reason,
                required_action=(f"보고 → 캡틴 승인 → state mark <task-path> "
                                 f"--task-step {key or row['row_id']} --done --owner user"))

    dg = state.get("design_gate") if isinstance(state.get("design_gate"), dict) else {}
    entering_execute = key == "execute.implement" and row.get("status") == "pending"
    bundle = None
    if entering_execute:
        if dg.get("status") != "pass":
            err(command, "design_gate_not_passed", status=dg.get("status") or "idle")
        if _task_requirement_hash(task_path, command) != dg.get("task_confirm_req_hash"):
            err(command, "task_reconfirm_required")
        _files, bundle = _design_bundle(task_path, command)
        if bundle != dg.get("passed_bundle_hash"):
            err(command, "design_bundle_mismatch", bundle_hash=bundle,
                passed_bundle_hash=dg.get("passed_bundle_hash"))

    if key == DESIGN_GATE_ROW_KEY and target_done:
        if dg.get("status") != "pass":
            err(command, "design_gate_not_passed", status=dg.get("status") or "idle")
        _files, bundle = _design_bundle(task_path, command)
        if bundle != dg.get("passed_bundle_hash"):
            err(command, "design_bundle_mismatch", bundle_hash=bundle,
                passed_bundle_hash=dg.get("passed_bundle_hash"))

    newly_done = [r for r in rows if r["row_id"] in set(auto_approved or [])]
    if target_done and row.get("item") == "사용자 확인":
        newly_done.append(row)
    for confirm in newly_done:
        ckey = confirm.get("key")
        if ckey == "task.user_confirm":
            _design_gate_block(state)["task_confirm_req_hash"] = (
                _task_requirement_hash(task_path, command))
        elif ckey == "plan.user_confirm":
            if bundle is None:
                _files, bundle = _design_bundle(task_path, command)
            block = _design_gate_block(state)
            if bundle != block.get("passed_bundle_hash"):
                err(command, "design_bundle_mismatch", row_id=confirm["row_id"],
                    bundle_hash=bundle, passed_bundle_hash=block.get("passed_bundle_hash"))
            block["approved_bundle_hash"] = bundle

    if entering_execute:
        if _design_gate_block(state).get("approved_bundle_hash") != bundle:
            err(command, "design_bundle_mismatch", bundle_hash=bundle,
                approved_bundle_hash=state["design_gate"].get("approved_bundle_hash"))


def apply_scenario_gate_mark_guard(task_path, row, command, *, target_done):
    """167 mark 가드 — 목표-커버 게이트 행(`test_scenario.scenario_gate`·`plan.scenario_gate`)을
    미완에서 완료로 바꿀 때 형제 test-tool `scenario-gate-verify`를 subprocess로 호출한다.

    exit 0이 아니면 `scenario_gate_record_required`로 거부한다. 저장 이전에 호출되므로
    state.json은 바뀌지 않는다. `--force`·`--auto-pass`·`--as-worker`는 이 함수를 우회하지
    못한다(호출자가 어떤 플래그도 넘기지 않는다). 이미 완료된 행, 다른 key, 부분 진행
    (`--step N/M`, N<M)에는 적용하지 않는다. `plan.design_gate`는 기존 설계 게이트 가드 소관이다.
    """
    if not target_done or row.get("key") not in SCENARIO_GATE_ROW_KEYS:
        return
    if row.get("status") in _COMPLETE_STATUSES:
        return
    task_dir = pathlib.Path(task_path)
    reason = None
    verify_error = None
    try:
        completed = subprocess.run(
            [sys.executable, str(_TEST_TOOL_PY), "scenario-gate-verify",
             "--task-folder", str(task_dir)],
            capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.SubprocessError) as e:
        completed = None
        reason = "verify_unavailable"
        verify_error = f"{type(e).__name__}: {e}"
    if completed is not None:
        if completed.returncode == 0:
            return
        try:
            payload = json.loads(completed.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            payload = {}
        payload = payload if isinstance(payload, dict) else {}
        detail = payload.get("detail") if isinstance(payload.get("detail"), dict) else {}
        reason = detail.get("reason") or payload.get("error") or f"exit_{completed.returncode}"
        verify_error = payload.get("error")
    extra = {"verify_error": verify_error} if verify_error else {}
    err(command, "scenario_gate_record_required",
        row_id=row.get("row_id"), key=row.get("key"), reason=reason,
        detail={"reason": reason}, **extra,
        required_action=(
            f"test-tool scenario-gate-record --task-folder {task_dir} --iteration <N> "
            "--evaluator-result <json> [--advisory-responses <json>]로 현재 문서 묶음의 회차를 "
            "다시 기록해 pass를 확인한 뒤 state mark <task-path> "
            f"--task-step {row.get('key')} --done을 재실행하세요"))


# ── 결정론 검사 (DEC-8) ────────────────────────────────────────────────────────

def _h3_sections(body):
    """H2 본문 안의 H3 소절 → {제목: 본문}."""
    sections = {}
    current = None
    buf = []
    for line in body.splitlines():
        m = re.match(r"^###\s+(.+?)\s*$", line.strip())
        if m:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = m.group(1).strip()
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def _findings_paths(body):
    paths = []
    for tok in re.findall(r"`([^`]+)`", body or ""):
        tok = tok.strip()
        if not _FINDINGS_TOKEN_CHARS_RE.match(tok):
            continue
        has_slash = "/" in tok
        ext = tok.rsplit(".", 1)[-1].lower() if "." in tok else ""
        looks_like_path = has_slash or ext in _FINDINGS_KNOWN_EXTS
        if looks_like_path and _is_safe_artifact_token(tok) and tok not in paths:
            paths.append(tok)
    return paths


def _path_matches(path, candidates):
    for cand in candidates:
        if path == cand or cand.endswith("/" + path) or path.endswith("/" + cand):
            return True
    return False


def _run_scenario_coverage(task_path):
    """DEC-8 ⑦ — test-tool coverage build+check. 반환: missing 문자열 리스트."""
    task_dir = pathlib.Path(task_path)

    def _call(argv):
        try:
            completed = subprocess.run([sys.executable, str(_TEST_TOOL_PY), *argv],
                                       capture_output=True, text=True, timeout=300)
        except (OSError, subprocess.SubprocessError) as e:
            return None, {"detail": f"{type(e).__name__}: {e}"}
        try:
            payload = json.loads(completed.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            payload = {}
        return completed.returncode, payload if isinstance(payload, dict) else {}

    code, payload = _call(["scenario-coverage-build", "--task-folder", str(task_dir),
                           "--template", "sdlc-v2"])
    if code != 0:
        if code == 17:
            return [f"scenario coverage input_error: {payload.get('detail')}"]
        return [f"scenario coverage build failed (exit {code}): {payload.get('detail') or payload.get('error')}"]
    code, payload = _call(["scenario-coverage-check", "--coverage-input",
                           str(task_dir / ".scenario-coverage-input.json")])
    if code == 0:
        return []
    if code == 16:
        detail = payload.get("detail") if isinstance(payload.get("detail"), dict) else {}
        missing = detail.get("missing") or {}
        out = []
        for label, kind in (("requirements", "requirement"), ("features", "feature"),
                            ("hypotheses", "hypothesis")):
            for ref in missing.get(label) or []:
                out.append(f"scenario coverage missing {kind} {ref}")
        return out or ["scenario coverage unmet"]
    if code == 17:
        return [f"scenario coverage input_error: {payload.get('detail')}"]
    return [f"scenario coverage check failed (exit {code}): {payload.get('detail') or payload.get('error')}"]


def _design_gate_deterministic_check(task_path):
    """DEC-8 ①~⑦ — 전 항목을 모아 missing 리스트로 반환한다(빈 리스트면 통과)."""
    task_dir = pathlib.Path(task_path)
    missing = []

    # ① sdlc-v2 TASK 필수 5절
    task_missing = _check_sdlc_v2_task_contract(task_dir / "TASK.md")
    if task_missing is None:
        missing.append("TASK.md: sdlc-v2 frontmatter")
    else:
        missing += [f"TASK.md: {h}" for h in task_missing]

    # ② 기존 PLAN 계약 전 항목 + strict AC/C 연결
    plan_result = _check_plan_contract(task_dir)
    if plan_result.get("status") == "skipped":
        missing.append(f"PLAN.md: {plan_result.get('reason')}")
    missing += list(plan_result.get("missing") or [])
    rows = _extract_work_items(task_dir / "PLAN.md") or []
    linked = set()
    targets = []
    for row in rows:
        linked |= set(re.findall(r"\b(?:AC|C)-\d+\b", row.get("완료 기준 연결", "")))
        for t in _work_item_targets(row):
            if t not in targets:
                targets.append(t)
    ac_ids, c_ids = _extract_ac_c_ids(task_dir / "TASK.md")
    for ref in sorted(ac_ids | c_ids, key=lambda r: (r.split("-")[0], int(r.split("-")[1]))):
        if ref not in linked:
            missing.append(f"uncovered requirement {ref}")

    # ③~⑥ Findings 4소절
    plan_text = _read_markdown(task_dir / "PLAN.md") or ""
    findings = _section_body_by_heading(plan_text, "Findings")
    if findings is None:
        missing.append("Findings section")
    else:
        subs = _h3_sections(findings)
        for name in DESIGN_GATE_FINDINGS_SECTIONS:
            if name not in subs:
                missing.append(f"Findings: {name} missing")
            elif not subs[name].strip():
                missing.append(f"Findings: {name} empty")
        change_paths = _findings_paths(subs.get("직접 변경")) + _findings_paths(subs.get("문서 갱신"))
        for path in _findings_paths(subs.get("회귀 확인")):
            if _path_matches(path, targets) or path in change_paths:
                missing.append(f"regression target listed as change: {path}")
        for path in change_paths:
            if not _path_matches(path, targets):
                missing.append(f"finding not in work items: {path}")
        if "미확인 가정" in subs:
            risk_ids = set(re.findall(r"\bH-\d+\b", _section_body_by_heading(plan_text, "Risks") or ""))
            body = subs["미확인 가정"]
            items = [ln.strip()[2:].strip() for ln in body.splitlines()
                     if ln.strip().startswith(("- ", "* "))]
            if not items and body.strip():
                items = [body.strip()]
            for item in items:
                refs = re.findall(r"\bH-\d+\b", item)
                unknown = [h for h in refs if h not in risk_ids]
                if unknown:
                    missing.append(f"unconfirmed assumption references unknown {', '.join(unknown)}")
                elif not refs and "없음" not in item:
                    missing.append(f"unconfirmed assumption without Risks H-N reference: {item[:80]}")

    # ⑦ scenario coverage (실제 test-tool 프로세스)
    missing += _run_scenario_coverage(task_dir)
    return missing


def _decision_clarity_lint(task_path):
    """170 AC-2 — decision_clarity 유보 어휘 후보 린트 (판정 아님, 후보 위치만 반환).

    PLAN.md 본문에서 펜스 코드 블록(```)과 인라인 코드 스팬(`...`)을 제외한 산문만,
    고정 패턴 12개(추후 결정/추후 확정/추후 논의/적절히/적절한/필요시/필요에 따라/
    상황에 따라/경우에 따라/TBD/TODO/미정)로 줄 단위 스캔해
    "PLAN.md:<줄번호>: <해당 줄 발췌>" 문자열 리스트를 반환한다. 설계 4축의 최종 판정은
    evaluator 소관이므로 이 함수는 FAIL을 선언하지 않는다(PLAN Decisions 참조).
    """
    plan_path = pathlib.Path(task_path) / "PLAN.md"
    if not plan_path.is_file():
        return []
    patterns = (
        "추후 결정", "추후 확정", "추후 논의", "적절히", "적절한",
        "필요시", "필요에 따라", "상황에 따라", "경우에 따라",
        "TBD", "TODO", "미정",
    )
    candidates = []
    in_fence = False
    for lineno, line in enumerate(plan_path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        prose = re.sub(r"`[^`]*`", "", line)
        if any(pat in prose for pat in patterns):
            candidates.append(f"PLAN.md:{lineno}: {line.strip()}")
    return candidates


# ── run-log 사건 조립 공용 ─────────────────────────────────────────────────────

def _design_row_change(state, task_path, command, row, to_status, events, *, owner=None, note=None):
    """행 상태를 바꾸고 state.changed 사건을 events에 쌓는다."""
    from_status = row.get("status")
    if from_status == to_status:
        return
    row["status"] = to_status
    row["status_label"] = STATUS_LABEL_MAP.get(to_status, row.get("status_label"))
    if owner is not None:
        row["owner"] = owner
    if note:
        row["note"] = note
    if _run_log_block(state) is not None:
        events.append(build_state_changed_event(
            state, task_id=pathlib.Path(task_path).name, command=command,
            from_status=from_status, to_status=to_status, row=row, note=note))


def _design_gate_event(state, task_path, command, event_name, iteration, summary, data):
    if _run_log_block(state) is None:
        return None
    return _build_gate_event(
        state, task_id=pathlib.Path(task_path).name, command=command,
        event_name=event_name, gate_id=f"design-gate-i{iteration}", actor_kind="PM",
        summary=summary, reason=None, data=data)


def _require_pm_design_path(state, command):
    if not _is_pm_design_path(state):
        err(command, "design_gate_not_applicable")


# ── design-gate start (DEC-7) ─────────────────────────────────────────────────

def cmd_design_gate_start(args):
    command = "design-gate start"
    task_path = resolve_task_path(args.task_path, command)
    state = load_state_json(task_path, command)
    _require_pm_design_path(state, command)                                    # ①
    rows = state["rows"]
    exec_idx = _row_index_by_key(state, "execute.implement")
    if exec_idx is not None and rows[exec_idx].get("status") != "pending":
        err(command, "design_gate_locked", status=rows[exec_idx].get("status"))  # ②
    dg_view = state.get("design_gate") if isinstance(state.get("design_gate"), dict) else {}
    if dg_view.get("status") == "retry_limit":                                 # ③
        err(command, "design_gate_retry_limit", iteration=dg_view.get("iteration"),
            limit=dg_view.get("limit", DESIGN_GATE_LIMIT))
    files, bundle = _design_bundle(task_path, command)
    open_attempt = dg_view.get("current_attempt") or {}
    superseded = None
    if dg_view.get("status") == "evaluating":                                  # ③-0
        # 열린 시도의 묶음이 그대로면 먼저 record해야 한다. 묶음이 바뀌어 record가
        # design_gate_input_changed로만 끝나는 시도는 새 start가 대체한다(회차는 이미 소비).
        if open_attempt.get("bundle_hash") == bundle:
            err(command, "design_gate_attempt_open", iteration=open_attempt.get("iteration"))
        superseded = open_attempt
    gate_idx = _row_index_by_key(state, DESIGN_GATE_ROW_KEY)
    check_stage_transition_guard(state, gate_idx, command, force=False)        # ③-1
    if _task_requirement_hash(task_path, command) != dg_view.get("task_confirm_req_hash"):
        err(command, "task_reconfirm_required")                                # ④
    iteration = int(dg_view.get("iteration") or 0)
    if args.iteration != iteration + 1:                                        # ⑤
        err(command, "design_gate_iteration_invalid",
            iteration=args.iteration, expected=iteration + 1)
    history = dg_view.get("history") or []
    # 167: refinement_pending이면 이번 시도는 refinement 회차다(advisory 반영 전이).
    refinement = bool(dg_view.get("refinement_pending"))
    # advisory_apply rewrite도 일반 rewrite와 같이 --rewrite-target 대상 문서를 고쳐야 한다(⑥).
    if history and history[-1].get("verdict") == "rewrite":                    # ⑥
        target = dg_view.get("last_rewrite_target")
        prev_files = (dg_view.get("current_attempt") or {}).get("files") or {}
        unchanged = [name for name in _DESIGN_REWRITE_DOCS.get(target, ())
                     if files.get(name) == prev_files.get(name)]
        if unchanged:
            err(command, "rewrite_target_unchanged", rewrite_target=target, unchanged=unchanged)

    now_str = get_kst_datetime(command)
    dg = _design_gate_block(state)
    attempt = {"iteration": args.iteration, "bundle_hash": bundle, "files": files,
               "started_at": now_str, "refinement": refinement}
    pre_events = []
    if superseded:
        superseded_item = {
            "iteration": superseded.get("iteration"), "verdict": "superseded",
            "rewrite_target": None, "bundle_hash": superseded.get("bundle_hash"),
            "reason": "document bundle changed before record", "at": now_str}
        if superseded.get("refinement") is True:
            # 167 ⓓ — refinement 결과로 보지 않는다. refinement_pending은 유지되고, 이 회차는
            # 상한을 소비하지 않는다(limit_from +1).
            superseded_item["refinement"] = True
            dg["limit_from"] = int(dg.get("limit_from") or 0) + 1
        dg["history"] = list(dg.get("history") or []) + [superseded_item]
        dg["status"] = "fail"
        _sup_event = _design_gate_event(
            state, task_path, command, "gate.resolved", superseded.get("iteration"),
            f"design gate i{superseded.get('iteration')} resolved: superseded",
            {"verdict": "rejected"})
        if _sup_event is not None:
            pre_events.append(_sup_event)
    missing = _design_gate_deterministic_check(task_path)                      # ⑦
    if missing:
        dg["iteration"] = args.iteration
        dg["current_attempt"] = attempt
        fail_reason = "; ".join(missing)
        fail_item = {
            "iteration": args.iteration, "verdict": "deterministic_fail",
            "rewrite_target": None, "bundle_hash": bundle,
            "reason": fail_reason[:500], "at": now_str}
        if refinement:
            # 167 ⓒ — refinement 회차의 결정론 실패는 상한과 무관하게 retry_limit으로 전이하고
            # 상한을 소비하지 않는다(limit_from +1).
            fail_item["reason"] = ("advisory_refinement_failed: " + fail_reason)[:500]
            fail_item["refinement"] = True
            dg["limit_from"] = int(dg.get("limit_from") or 0) + 1
            limit_reached = True
        else:
            limit_reached = args.iteration - int(dg.get("limit_from") or 0) >= int(dg.get("limit") or DESIGN_GATE_LIMIT)
        dg["history"] = list(dg.get("history") or []) + [fail_item]
        dg["status"] = "retry_limit" if limit_reached else "fail"
        state["updated_at"] = now_str
        run_log_commit(task_path, state, command, event=pre_events or None)
        sync_state_md(task_path, state, now_str, command)
        extra = {}
        if limit_reached:
            extra = {"transition_action": "await_user", "report_type": "decision_request"}
        err(command, "design_gate_deterministic_fail", missing=missing,
            iteration=args.iteration, status=dg["status"], refinement=refinement, **extra)

    events = list(pre_events)
    dg["status"] = "evaluating"
    dg["iteration"] = args.iteration
    dg["current_attempt"] = attempt
    dg["passed_bundle_hash"] = None
    dg["approved_bundle_hash"] = None
    _design_row_change(state, task_path, command, rows[gate_idx], "in_progress", events,
                       note=f"design gate i{args.iteration} evaluating")
    rows[gate_idx]["timestamp"] = now_str
    confirm_idx = _row_index_by_key(state, "plan.user_confirm")
    if confirm_idx is not None and rows[confirm_idx].get("status") in _COMPLETE_STATUSES:
        _design_row_change(state, task_path, command, rows[confirm_idx], "pending", events,
                           note=f"design gate i{args.iteration} reopened")
        rows[confirm_idx]["timestamp"] = now_str
    gate_event = _design_gate_event(state, task_path, command, "gate.requested", args.iteration,
                                    f"design gate i{args.iteration} requested", None)
    if gate_event is not None:
        events.append(gate_event)
    state["updated_at"] = now_str
    state["next_action"] = _derive_next_action(state)
    _rl_fields = run_log_commit(task_path, state, command, event=events or None)
    _jw = sync_state_md(task_path, state, now_str, command)
    ok(command, status="evaluating", iteration=args.iteration,
       gate_id=f"design-gate-i{args.iteration}", bundle_hash=bundle, refinement=refinement,
       _transition_state=state, **(_jw or {}), **(_rl_fields or {}))


# ── design-gate record (DEC-9) ────────────────────────────────────────────────

def _load_evaluator_result(path):
    try:
        data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    return data if isinstance(data, dict) else None


def _evaluator_axes(result):
    """(axes dict, scores dict) 또는 계약 형식이 아니면 None."""
    if not isinstance(result, dict):
        return None
    design = result.get("design")
    scenario = result.get("scenario")
    if not isinstance(design, dict) or not isinstance(scenario, dict):
        return None
    axes = design.get("axes")
    scores = scenario.get("scores")
    if not isinstance(axes, dict) or not isinstance(scores, dict):
        return None
    if any(k not in axes for k in DESIGN_GATE_AXES):
        return None
    if any(k not in scores for k in DESIGN_GATE_SCENARIO_KEYS):
        return None
    for k in DESIGN_GATE_SCENARIO_KEYS:
        if isinstance(scores[k], bool) or not isinstance(scores[k], (int, float)):
            return None
    return axes, scores


def _validate_advisories(advisories):
    """167 advisory 결과 계약 — 위반 사유 문자열 또는 None. 키 부재는 빈 배열로 본다."""
    if advisories is None:
        return None
    if not isinstance(advisories, list):
        return "advisories must be a list"
    seen = set()
    for item in advisories:
        if not isinstance(item, dict):
            return "advisory item must be an object"
        advisory_id = item.get("id")
        if not isinstance(advisory_id, str) or not _ADVISORY_ID_RE.match(advisory_id):
            return f"advisory.id must be A-N: {advisory_id!r}"
        if advisory_id in seen:
            return f"advisory.id duplicated: {advisory_id}"
        seen.add(advisory_id)
        if item.get("kind") not in _ADVISORY_KINDS:
            return f"advisory.kind invalid: {item.get('kind')!r}"
        targets = item.get("targets")
        if (not isinstance(targets, list) or not targets
                or any(not isinstance(t, str) or not _SCENARIO_ID_RE.match(t) for t in targets)):
            return f"advisory.targets must be a non-empty S-ID list ({advisory_id})"
        for field in ("basis", "recommendation"):
            if not isinstance(item.get(field), str) or not item.get(field).strip():
                return f"advisory.{field} is required ({advisory_id})"
    return None


def _load_advisory_responses(command, path, advisories, *, required):
    """167 advisory 응답 형식 — 검증된 응답 리스트를 반환하고 위반은 advisory_response_invalid."""
    if not path:
        if required:
            err(command, "advisory_response_invalid",
                detail="--advisory-responses required: pass result has advisories")
        return []
    try:
        responses = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as e:
        err(command, "advisory_response_invalid", detail=f"cannot load --advisory-responses: {e}")
    if not isinstance(responses, list):
        err(command, "advisory_response_invalid", detail="advisory responses must be a list")
    advisory_ids = {a.get("id") for a in advisories}
    seen = []
    for item in responses:
        if not isinstance(item, dict):
            err(command, "advisory_response_invalid", detail="advisory response item must be an object")
        response_id = item.get("id")
        if response_id in seen:
            err(command, "advisory_response_invalid", detail=f"duplicate advisory response id: {response_id}")
        seen.append(response_id)
        if item.get("response") not in ("apply", "retain"):
            err(command, "advisory_response_invalid",
                detail=f"invalid advisory response: {item.get('response')!r} ({response_id})")
        if item.get("response") == "retain" and not str(item.get("reason") or "").strip():
            err(command, "advisory_response_invalid",
                detail=f"retain response requires a non-blank reason ({response_id})")
    if set(seen) != advisory_ids:
        err(command, "advisory_response_invalid",
            detail=(f"advisory response id set mismatch: expected {sorted(advisory_ids)}, "
                    f"got {sorted(str(i) for i in seen)}"))
    return responses


def cmd_design_gate_record(args):
    command = "design-gate record"
    task_path = resolve_task_path(args.task_path, command)
    state = load_state_json(task_path, command)
    _require_pm_design_path(state, command)
    dg_view = state.get("design_gate") if isinstance(state.get("design_gate"), dict) else {}
    attempt = dg_view.get("current_attempt") or {}
    if dg_view.get("status") != "evaluating":
        err(command, "design_gate_iteration_invalid", iteration=args.iteration,
            expected=None, detail="no open design gate attempt — run design-gate start first")
    if args.iteration != attempt.get("iteration"):
        err(command, "design_gate_iteration_invalid", iteration=args.iteration,
            expected=attempt.get("iteration"))
    _files, bundle = _design_bundle(task_path, command)
    if bundle != attempt.get("bundle_hash"):
        err(command, "design_gate_input_changed", bundle_hash=bundle,
            attempt_bundle_hash=attempt.get("bundle_hash"))

    verdict = args.verdict
    reason = None
    # 167: refinement 회차 판정은 start가 attempt에 남긴 플래그로만 내린다.
    refinement = attempt.get("refinement") is True
    advisories = []
    advisory_responses = []
    if verdict in ("pass", "rewrite"):
        raw_result = _load_evaluator_result(args.evaluator_result)
        if isinstance(raw_result, dict):
            result_hash = raw_result.get("input_bundle_hash")
            result_iteration = raw_result.get("iteration")
            if result_hash != bundle or result_iteration != args.iteration:
                err(command, "design_gate_result_stale", bundle_hash=bundle,
                    iteration=args.iteration, result_input_bundle_hash=result_hash,
                    result_iteration=result_iteration)
        parsed = _evaluator_axes(raw_result)
        if parsed is None:
            err(command, "design_gate_result_invalid",
                detail="evaluator result must contain design.axes(4) and scenario.scores(3)")
        axes, scores = parsed
        if not refinement:
            # 167 advisory 결과 계약 — refinement 회차는 형식 검사 없이 무시한다.
            advisory_error = _validate_advisories(raw_result.get("advisories"))
            if advisory_error:
                err(command, "design_gate_result_invalid", detail=advisory_error)
            advisories = list(raw_result.get("advisories") or [])
        if verdict == "rewrite" and not args.rewrite_target:
            err(command, "design_gate_result_invalid", detail="--rewrite-target required for rewrite")
        values = [float(scores[k]) for k in DESIGN_GATE_SCENARIO_KEYS]
        average = sum(values) / len(values)
        failed_axes = [k for k in DESIGN_GATE_AXES if str(axes.get(k)).upper() != "PASS"]
        if verdict == "pass":
            if failed_axes or any(v < 1 for v in values) or average < 1.5:
                err(command, "design_gate_verdict_mismatch", failed_axes=failed_axes,
                    scenario_scores=scores, scenario_average=round(average, 3))
        else:
            parts = []
            if failed_axes:
                parts.append("design FAIL: " + ", ".join(failed_axes))
            parts.append(f"scenario average {round(average, 3)}")
            reason = "; ".join(parts)
        if not refinement:
            # 167 응답 요구 시점 — pass·advisories ≥1이면 필수, 그 외에는 선택(주어지면 검사·기록).
            advisory_responses = _load_advisory_responses(
                command, getattr(args, "advisory_responses", None),
                advisories, required=(verdict == "pass" and bool(advisories)))
    else:
        reason = "evaluator result not in contract format"

    apply_count = sum(1 for r in advisory_responses if r.get("response") == "apply")
    advisory_apply = verdict == "pass" and not refinement and apply_count >= 1
    if advisory_apply and not args.rewrite_target:
        err(command, "design_gate_result_invalid",
            detail="--rewrite-target required when advisory responses include apply")

    now_str = get_kst_datetime(command)
    dg = _design_gate_block(state)
    rows = state["rows"]
    gate_idx = _row_index_by_key(state, DESIGN_GATE_ROW_KEY)
    events = []
    recorded_verdict = verdict
    if advisory_apply:
        # 167 advisory 반영 전이 — pass를 rewrite/advisory_apply로 기록하고 refinement를 예약한다.
        recorded_verdict = "rewrite"
        reason = "advisory_apply"
    elif refinement and verdict != "pass":
        # 167 ⓑ — refinement 회차 비-pass
        reason = "advisory_refinement_failed"
    rewrite_target = args.rewrite_target if recorded_verdict == "rewrite" else None
    dg["history"] = list(dg.get("history") or []) + [{
        "iteration": args.iteration, "verdict": recorded_verdict, "rewrite_target": rewrite_target,
        "bundle_hash": bundle, "reason": reason, "at": now_str,
        "advisories": advisories, "advisory_responses": advisory_responses,
        "refinement": refinement}]
    extra = {}
    if refinement or advisory_apply:
        # 167 상한 비소비 — apply 회차와 refinement 회차는 limit_from을 1 올려 제외한다.
        dg["limit_from"] = int(dg.get("limit_from") or 0) + 1
    if recorded_verdict == "pass":
        dg["status"] = "pass"
        dg["passed_bundle_hash"] = bundle
        if refinement:
            dg["refinement_pending"] = False                                  # ⓐ
        _design_row_change(state, task_path, command, rows[gate_idx], "done", events,
                           owner="PM", note=f"design gate i{args.iteration} pass")
        rows[gate_idx]["timestamp"] = now_str
    else:
        dg["status"] = "fail"
        if rewrite_target:
            dg["last_rewrite_target"] = rewrite_target
        if advisory_apply:
            dg["refinement_pending"] = True
        elif refinement:
            dg["status"] = "retry_limit"                                       # ⓑ
            extra = {"transition_action": "await_user", "report_type": "decision_request"}
        elif args.iteration - int(dg.get("limit_from") or 0) >= int(dg.get("limit") or DESIGN_GATE_LIMIT):
            dg["status"] = "retry_limit"
            extra = {"transition_action": "await_user", "report_type": "decision_request"}
    gate_event = _design_gate_event(
        state, task_path, command, "gate.resolved", args.iteration,
        f"design gate i{args.iteration} resolved: {recorded_verdict}"
        + (f" ({reason})" if reason in ("advisory_apply", "advisory_refinement_failed") else "")
        + (f" (rewrite_target={rewrite_target})" if rewrite_target else ""),
        {"verdict": "approved" if recorded_verdict == "pass" else "rejected"})
    if gate_event is not None:
        events.append(gate_event)
    state["updated_at"] = now_str
    state["next_action"] = _derive_next_action(state)
    _rl_fields = run_log_commit(task_path, state, command, event=events or None)
    _jw = sync_state_md(task_path, state, now_str, command)
    ok(command, status=dg["status"], iteration=args.iteration, verdict=recorded_verdict,
       rewrite_target=rewrite_target, gate_id=f"design-gate-i{args.iteration}",
       bundle_hash=bundle, reason=reason, refinement=refinement,
       next_refinement=bool(dg.get("refinement_pending")) and dg["status"] == "fail",
       _transition_state=state,
       **extra, **(_jw or {}), **(_rl_fields or {}))


# ── design-gate reset (DEC-10) ────────────────────────────────────────────────

def cmd_design_gate_reset(args):
    command = "design-gate reset"
    task_path = resolve_task_path(args.task_path, command)
    state = load_state_json(task_path, command)
    _require_pm_design_path(state, command)
    if args.owner != "user":
        err(command, "user_confirmation_required", row_id=DESIGN_GATE_ROW_KEY,
            stage="PLAN", reason="design_gate_reset_requires_user",
            required_action="design-gate reset <task-path> --owner user --note <사유>")
    dg_view = state.get("design_gate") if isinstance(state.get("design_gate"), dict) else {}
    if dg_view.get("status") != "retry_limit":
        ok(command, reset=False, status=dg_view.get("status") or "idle",
           iteration=dg_view.get("iteration") or 0)
        return
    now_str = get_kst_datetime(command)
    dg = _design_gate_block(state)
    dg["status"] = "idle"
    dg["limit_from"] = int(dg.get("iteration") or 0)
    # 167: ⓑⓒ 뒤 reset은 refinement를 해제하고 일반 회차부터 다시 시작한다.
    dg["refinement_pending"] = False
    state["updated_at"] = now_str
    _rl_fields = run_log_commit(task_path, state, command, event=None)
    note = resolve_owner_placeholder(args.note) if args.note else None
    _jw = sync_state_md(task_path, state, now_str, command,
                        decision=f"design gate retry limit reset at i{dg['iteration']} (owner=user)",
                        reason=note or "(none)")
    ok(command, reset=True, status="idle", iteration=dg["iteration"],
       limit_from=dg["limit_from"], transition_action="continue",
       **(_jw or {}), **(_rl_fields or {}))


# ── design-decision (DEC-12) ──────────────────────────────────────────────────

def cmd_design_decision(args):
    command = "design-decision"
    task_path = resolve_task_path(args.task_path, command)
    state = load_state_json(task_path, command)
    _require_pm_design_path(state, command)
    rows = state["rows"]
    exec_idx = _row_index_by_key(state, "execute.implement")
    if exec_idx is not None and rows[exec_idx].get("status") != "pending":
        err(command, "design_gate_locked", status=rows[exec_idx].get("status"))
    frontier = next((r for r in rows if r.get("status") not in _COMPLETE_STATUSES), None)
    if frontier is None or frontier.get("stage") != "PLAN":
        incomplete = [r["row_id"] for r in rows
                      if r.get("stage") == "TASK" and r.get("status") not in _COMPLETE_STATUSES]
        plan_idx = _row_index_by_key(state, "plan.plan_md")
        err(command, "stage_transition_violation",
            row_id=rows[plan_idx]["row_id"] if plan_idx is not None else None,
            incomplete_rows=incomplete)

    now_str = get_kst_datetime(command)
    summary = resolve_owner_placeholder(args.summary)
    basis = resolve_owner_placeholder(args.basis)
    events = []
    decision = f"design-decision({args.scope}): {summary}"
    if args.scope == "detail":
        if _run_log_block(state) is not None:
            events.append(_build_pm_activity_event(
                state, task_id=task_path.name, command=command,
                kind={"kind": "decision"},
                summary=decision, reason=basis, refs=None,
                stage="PLAN", task_step=frontier.get("key"), work_item=None))
        state["updated_at"] = now_str
        _rl_fields = run_log_commit(task_path, state, command, event=events or None)
        _jw = sync_state_md(task_path, state, now_str, command, decision=decision, reason=basis)
        ok(command, scope="detail", summary=summary, transition_action="continue",
           report_type="progress_report", next_action=state.get("next_action") or _derive_next_action(state),
           **(_jw or {}), **(_rl_fields or {}))
        return

    plan_idx = _row_index_by_key(state, "plan.plan_md")
    row = rows[plan_idx]
    prev_status = state.get("current_status")
    row["status"] = "failed"
    row["status_label"] = "❌"
    row["timestamp"] = now_str
    row["note"] = f"block: design-decision external: {summary}"
    state["current_status"] = "blocked"
    state["updated_at"] = now_str
    if _run_log_block(state) is not None:
        events.append(build_state_changed_event(
            state, task_id=task_path.name, command=command,
            from_status=prev_status, to_status="blocked", row=row))
    _rl_fields = run_log_commit(task_path, state, command, event=events or None)
    _jw = sync_state_md(task_path, state, now_str, command, decision=decision, reason=basis)
    ok(command, scope="external", summary=summary, row_id=row["row_id"],
       key=row.get("key"), status="failed", current_status="blocked",
       transition_action="blocked", report_type="decision_request",
       next_action=f"사용자 결정: {summary}",
       todo_mirror=build_todo_mirror(state, "update"),
       **(_jw or {}), **(_rl_fields or {}))


def cmd_verify(args):
    """PLAN 013 §verify — TEST-SCENARIO.md mock 코드 패턴 + 증거 누락 검사.
    016 확장: --red-check(RED 증거 게이트) / --fix-mode(테스트 불변성).
    005 확장: --clarification-check(TASK 4요소 잠금 게이트).
    098 확장: --evidence-check(근거 등급 확정/미확정 판정 라우터, 차단 없음).
    106 확장: --code-scan-citation-check(PLAN.md code-scan 결과 인용 게이트, unmet 시 exit 1).
    111 확장: --plan-contract-check(sdlc-v2 Work items 계약 검사, unmet 시 exit 1).
    대상 파일 부재 시 doc-only skip (ok).
    """
    command = "verify"
    task_path = args.task_path
    scenario_arg = getattr(args, "scenario", None)
    red_check = getattr(args, "red_check", False)
    fix_mode = getattr(args, "fix_mode", False)
    changed_files = getattr(args, "changed_files", None) or []
    test_globs = getattr(args, "test_globs", None)
    clarification_check = getattr(args, "clarification_check", False)
    evidence_check = getattr(args, "evidence_check", False)
    code_scan_citation_check = getattr(args, "code_scan_citation_check", False)
    plan_contract_check = getattr(args, "plan_contract_check", False)
    run_log_completeness_check = getattr(args, "run_log_completeness_check", False)
    design_gate_check = getattr(args, "design_gate_check", False)
    task_md_arg = getattr(args, "task_md", None)

    # 098/106/135/170 — 게이트 플래그 동시 지정 거부 (무성 무시 방지, PLAN §3.3.2 / §3.4.2 (5))
    _gate_flags = [_n for _n, _v in (
        ("--clarification-check", clarification_check),
        ("--evidence-check", evidence_check),
        ("--code-scan-citation-check", code_scan_citation_check),
        ("--plan-contract-check", plan_contract_check),
        ("--run-log-completeness-check", run_log_completeness_check),
        ("--design-gate-check", design_gate_check),
    ) if _v]
    if len(_gate_flags) > 1:
        err(command, "evidence_check_flag_conflict", flags=_gate_flags)

    # 135 W-4 (AC-5~AC-8) — run-log 완전성 진단 라우터 (읽기 전용, 비차단)
    if run_log_completeness_check:
        result = _run_log_completeness_check(task_path)
        print(json.dumps({
            "ok": True, "command": command,
            **result,
        }, ensure_ascii=False))
        sys.exit(0)

    # 170 AC-1 — design-gate 결정론 사전검사 (evaluator 호출 전 무차단 사전점검,
    # 회차·상태 비소비). state.json 부재·PM 경로 아님은 다른 5개 플래그와 동일하게
    # graceful skip(exit 0)으로 처리한다(load_state_json의 하드 오류 경로를 타지 않는다).
    if design_gate_check:
        task_dir = pathlib.Path(task_path)
        state_file = task_dir / "state.json"
        if not state_file.exists():
            print(json.dumps({
                "ok": True, "command": command,
                "design_gate_check": "skipped",
                "reason": "state.json not found",
            }, ensure_ascii=False))
            sys.exit(0)
        with open(state_file, encoding="utf-8") as f:
            dgc_state = json.load(f)
        if not _is_pm_design_path(dgc_state):
            print(json.dumps({
                "ok": True, "command": command,
                "design_gate_check": "skipped",
                "reason": "not a PM design path",
            }, ensure_ascii=False))
            sys.exit(0)
        deterministic_missing = _design_gate_deterministic_check(task_dir)
        decision_clarity_candidates = _decision_clarity_lint(task_dir)
        print(json.dumps({
            "ok": True, "command": command,
            "design_gate_check": "unmet" if deterministic_missing else "pass",
            "deterministic_missing": deterministic_missing,
            "decision_clarity_candidates": decision_clarity_candidates,
        }, ensure_ascii=False))
        sys.exit(0)

    # 005 — TASK 4요소 잠금 게이트 (fix_mode와 같은 조기 반환 패턴 — 독립 분기)
    if clarification_check:
        task_md_path = _find_task_md(task_path, task_md_arg)
        if task_md_path is None:
            # 정책 A(graceful skip): TASK.md 파일 부재 → skip ok
            print(json.dumps({
                "ok": True, "command": command,
                "clarification_check": "skipped",
                "reason": "TASK.md not found (backward-compat skip)",
            }, ensure_ascii=False))
            sys.exit(0)
        missing = _check_clarification_gate(task_md_path)
        if missing is None:
            # 정책 A(graceful skip): 섹션/표 부재 → skip ok
            print(json.dumps({
                "ok": True, "command": command,
                "clarification_check": "skipped",
                "template": "legacy",
                "reason": "no sdlc-v2 contract or '## 명확화 결과' section (backward-compat skip)",
            }, ensure_ascii=False))
            sys.exit(0)
        if missing:
            err(command, "clarification_gate_unmet", missing=missing)
        print(json.dumps({
            "ok": True, "command": command,
            "clarification_check": "pass",
            "template": "sdlc-v2" if _is_sdlc_v2_markdown(task_md_path) else "legacy",
        }, ensure_ascii=False))
        sys.exit(0)

    # 111 — sdlc-v2 PLAN Work items 계약 검사.
    if plan_contract_check:
        result = _check_plan_contract(task_path)
        if result["status"] == "skipped":
            print(json.dumps({
                "ok": True, "command": command,
                "plan_contract_check": "skipped",
                "reason": result["reason"],
            }, ensure_ascii=False))
            sys.exit(0)
        if result["status"] != "pass":
            err(command, "plan_contract_unmet",
                message="PLAN.md Work items 계약 미충족",
                plan_contract_check="unmet",
                missing=result["missing"],
                violations=result["violations"],
                work_items=result.get("work_items", []))
        print(json.dumps({
            "ok": True, "command": command,
            "plan_contract_check": "pass",
            "work_items": result.get("work_items", []),
            "work_item_ids": result.get("work_items", []),
        }, ensure_ascii=False))
        sys.exit(0)

    # 098 — 근거 등급 확정/미확정 판정 라우터 (clarification_check 뒤·fix_mode 앞,
    # 기존 조기 반환 순서 불변)
    if evidence_check:
        task_md_path = _find_task_md(task_path, task_md_arg)
        if task_md_path is None:
            # 정책 A(graceful skip): TASK.md 파일 부재 → skip ok
            print(json.dumps({
                "ok": True, "command": command,
                "evidence_check": "skipped",
                "reason": "TASK.md not found (backward-compat skip)",
            }, ensure_ascii=False))
            sys.exit(0)
        gate = _check_evidence_gate(task_md_path)
        if gate is None:
            # 정책 A(graceful skip): 섹션/표/'의존 사실' 열 부재 → skip ok
            print(json.dumps({
                "ok": True, "command": command,
                "evidence_check": "skipped",
                "reason": "no '## 명확화 결과' section or '의존 사실' column (backward-compat skip)",
            }, ensure_ascii=False))
            sys.exit(0)
        status = "pass" if gate["confirmed_ratio"] >= 1.0 else "routed"
        print(json.dumps({
            "ok": True, "command": command,
            "evidence_check": status,
            "items": gate["items"],
            "confirmed_ratio": gate["confirmed_ratio"],
            "direction_confirmed_ratio": gate["direction_confirmed_ratio"],
            "unconfirmed": gate["unconfirmed"],
        }, ensure_ascii=False))
        sys.exit(0)

    # 106 — code-scan 결과 인용 판정 라우터 (evidence_check 뒤·fix_mode 앞,
    #   기존 조기 반환 순서 불변). [MUST] 게이트 순서는 _run_code_scan_citation_hook의
    #   ③④⑤⑦와 동일하다 — 같은 입력에 두 집행 지점(verify / advance·mark)이 다른
    #   판정을 내면 게이트가 신뢰를 잃는다. reason은 훅과 동일 3값으로 닫는다.
    if code_scan_citation_check:
        plan_md = pathlib.Path(task_path) / "PLAN.md"
        reason = None
        root = task_root(task_path)
        config = None
        cfg_path = (root / ".opal" / "code-scan.json") if root is not None else None
        if cfg_path is not None and cfg_path.is_file():
            try:
                config = json.loads(cfg_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                config = None
        if (not isinstance(config, dict)
                or config.get("headerSource") not in ("inline", "manifest")):
            reason = "code_scan_unavailable"        # ③ 자산 게이트 (F-005)
        elif not plan_md.is_file():
            reason = "plan_md_absent"               # ④ 산출물 게이트 (하위호환)
        targets = _collect_plan_target_files(plan_md) if reason is None else []
        if reason is None:
            extensions = config.get("extensions") or list(_CODE_SCAN_DEFAULT_EXTENSIONS)
            if not any(os.path.splitext(t)[1] in extensions for t in targets):
                reason = "doc_only_task"            # ⑤ 적용 범위 게이트 (F-005)
        if reason is not None:
            print(json.dumps({
                "ok": True, "command": command,
                "code_scan_citation_check": "skipped",
                "reason": reason,
                "target_files": targets,
                "matched_tokens": [],
            }, ensure_ascii=False))
            sys.exit(0)
        # ⑦ 판정 — None(§4.2 섹션 부재)·[](통과) 모두 통과
        body = plan_md.read_text(encoding="utf-8")
        matched = [tok for tok, rx in _CODE_SCAN_CITATION_RES if rx.search(body)]
        missing = _check_code_scan_citation(plan_md)
        if missing:
            err(command, "code_scan_citation_unmet",
                code_scan_citation_check="unmet", missing=missing,
                target_files=targets, matched_tokens=matched)
        print(json.dumps({
            "ok": True, "command": command,
            "code_scan_citation_check": "pass",
            "reason": None,
            "target_files": targets,
            "matched_tokens": matched,
        }, ensure_ascii=False))
        sys.exit(0)

    # 016 — fix 루핑 테스트 불변성 검사 (산출물 무관, 명시 입력 기반 deterministic)
    if fix_mode:
        if not test_globs:
            # deterministic 입력(test-globs) 없음 → 검사 skip (오탐 방지)
            print(json.dumps({
                "ok": True, "command": command,
                "immutability_check": "skipped (no test-globs)",
            }, ensure_ascii=False))
            sys.exit(0)
        matched = _match_test_files(changed_files, test_globs)
        if matched:
            err(command, "test_modified_in_fix", files=matched)
        print(json.dumps({
            "ok": True, "command": command,
            "immutability_check": "pass", "matched_test_files": [],
        }, ensure_ascii=False))
        sys.exit(0)

    scenario_path = _find_scenario_file(task_path, scenario_arg)
    if scenario_path is None:
        # doc-only / 인프라 부재: TEST-SCENARIO.md 없음 → skip ok (graceful skip)
        print(json.dumps({
            "ok": True, "command": command,
            "skipped": True, "reason": "TEST-SCENARIO.md not found (doc-only skip)"
        }, ensure_ascii=False))
        sys.exit(0)

    lines = scenario_path.read_text(encoding="utf-8").splitlines()

    # 검사 1 — mock 코드 패턴
    mock_lines = _check_mock_patterns(lines)
    if mock_lines:
        err(command, "mock_in_scenario", lines=mock_lines)

    # 검사 2 — 증거 누락
    missing_lines = _check_evidence(lines)
    if missing_lines:
        err(command, "evidence_missing", lines=missing_lines)

    # 검사 3 (016) — RED 증거 게이트 (--red-check 시에만; 미지정 시 하위 호환)
    checks = {"mock_in_scenario": "pass", "evidence_missing": "pass"}
    if red_check:
        red_lines = _check_red_evidence(lines)
        if red_lines:
            err(command, "red_evidence_missing",
                detail="빈 RED 증거 행: {}".format(red_lines))
        checks["red_evidence_missing"] = "pass"

    print(json.dumps({
        "ok": True, "command": command,
        "scenario": str(scenario_path),
        "checks": checks,
    }, ensure_ascii=False))
    sys.exit(0)


def cmd_event_verify(args):
    """event-loader receipt를 검증하고 결과와 종료 코드를 그대로 전달한다.

    state.json과 STATE.md는 읽거나 쓰지 않는다. 따라서 파일럿이 pilot.start 또는
    stage.* 이벤트를 검증할 때 기존 파이프라인 상태 API에 영향을 주지 않는다.
    """
    loader = pathlib.Path(__file__).resolve().parent.parent / "event-loader" / "event_loader.py"
    if not loader.is_file():
        print(json.dumps({
            "ok": False,
            "command": "event-verify",
            "error": "event_loader_not_found",
            "path": str(loader),
        }, ensure_ascii=False))
        sys.exit(1)

    command = [
        sys.executable,
        str(loader),
        "verify",
        "--receipt",
        args.receipt,
        "--event",
        args.event,
    ]
    for option, value in (
        ("--manifest", args.manifest),
        ("--source-root", args.source_root),
        ("--deployed-root", args.deployed_root),
        ("--project-root", args.project_root),
    ):
        if value:
            command.extend((option, value))

    completed = subprocess.run(command, capture_output=True, text=True)
    output = completed.stdout.strip()
    try:
        payload = json.loads(output)
    except (TypeError, ValueError):
        payload = {
            "ok": False,
            "command": "event-verify",
            "error": "event_loader_failed",
            "detail": completed.stderr.strip() or output or "event-loader returned no JSON",
        }
    else:
        payload["via"] = "state-tool event-verify"
    print(json.dumps(payload, ensure_ascii=False))
    sys.exit(completed.returncode if completed.returncode in (0, 1, 2) else 2)


# ─────────────────────────────────────────────────────────────────────────────
# argparse 설정 (PLAN §2.19 E-2 매트릭스 그대로)
# ─────────────────────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="state-tool",
        description="OPAL 파이프라인 현황판 JSON SSOT 관리 CLI (PLAN §2.19 E-2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
서브 명령 (11종):
  init          state.json + STATE.md 생성
  show          현황판 출력 (md/json/full)
  advance       ⬜→🔄 전환
  mark          ⬜/🔄→✅ 전환 (--done 필수)
  block         any→❌ 전환 + current_status=blocked
  validate      정합성 검증 → violations[]
  add-row       추가작업 행 삽입
  status        current_status 명시 전환
  finalize-attribution  merge 확인 후 허브 MEMORY history 귀속 (--allocator-root 필수)
  spec-validate pipeline.json 스펙 검증 (070 R-6)
  event-verify  단계 진입용 event-loader receipt 검증 (상태 비접촉)
  gate-pass     [DEPRECATED] Gate 4행 일괄 ✅ 처리 (레거시 state.json 전용)

행 주소(070): --task-step <key> / --task-step-id <n> / --row <n>[deprecated] 중 하나만 지정.
호출 형식: ~/.opal/tools/state-tool/run.sh <command> <task-path> [options]
종료 코드: 0=ok  1=violation/scope_error  2=internal_error
"""
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ── init ──
    p_init = sub.add_parser("init", help="state.json + STATE.md 생성 (§2.11 G-8)")
    p_init.add_argument("task_path", metavar="<task-path>")
    p_init.add_argument("--skill", required=True,
                        choices=["opp","opd","opds","opdw","opwt","opgc","oppd","opsdd","oppl","opdd","oppb"])
    p_init.add_argument("--mode", required=True,
                        choices=["interactive","semi-agentic","agentic"])
    p_init.add_argument("--task-title")
    p_init.add_argument("--next-action")
    rows_group = p_init.add_mutually_exclusive_group()  # C-1
    rows_group.add_argument("--rows-spec", metavar="<inline-json>")
    rows_group.add_argument("--rows-from", metavar="<path>",
                        help="SKILL.md(레거시, deprecated 경고) 또는 pipeline.json(070 신규, 확장자로 분기)")
    p_init.add_argument("--rows-acts", metavar="<inline-json>",
                        help="opsdd ACT 동적 주입 (시그니처만, 미구현 — R-13)")
    p_init.add_argument("--force", action="store_true")
    p_init.add_argument("--note")
    # 094 D-2: 저널화로 파싱 대상(파이프라인 표)이 소멸 — cmd_init이 즉시 거부.
    # 인자 정의는 하위 호환을 위해 유지하되 help는 감춘다(§3.2.2 (2)).
    p_init.add_argument("--import-existing", action="store_true", dest="import_existing",
                        help=argparse.SUPPRESS)
    p_init.add_argument("--worktree", metavar="<path>",
                        help="worktree 코드 작업본 절대경로 (092). 미지정 시 state.json에 키를 생성하지 않는다.")
    # CONTRACT §2.5 state-tool.init.run-log-mode — 기본값 shadow(135 ADD-2).
    # 모든 신규 태스크가 기록 계약을 갖게 해 pilot별 적용 여부에 따른 집계 구멍을
    # 없앤다. `off`는 기존 1.1 경로를 그대로 타는 명시적 비활성화다.
    p_init.add_argument("--run-log-mode", dest="run_log_mode",
                        choices=["shadow", "active", "off"], default="shadow",
                        help="실행 로그 계약 활성화 모드 (기본 shadow. off는 1.1 경로 유지, "
                             "active는 --profiles의 --channel-id 항목이 있을 때만 수용)")
    p_init.add_argument("--channel-id", dest="channel_id",
                        help="--run-log-mode active 전용 (T02 범위 밖 — profiles.json 미배포)")
    p_init.add_argument("--profiles", dest="profiles",
                        help="--run-log-mode active 전용 (T02 범위 밖)")
    # 156 DEC-4: pm은 legacy 값이라 choices에 남겨 두고 cmd_init이 actor_pm_retired로 거부한다.
    p_init.add_argument("--actor", choices=["coordinator", "worker", "pm"],
                        help="실행 주체(opd/opds 전용). 미지정 시 state.json에 키를 생성하지 않는다.")
    p_init.add_argument("--workspace", choices=["worktree", "hub"],
                        help="resolve-start가 판정한 작업본. worktree는 --worktree 필수, "
                             "oppb는 hub 불가. 미지정 시 기존 동작.")
    p_init.set_defaults(func=cmd_init)

    # ── show ──
    p_show = sub.add_parser("show", help="현황판 출력 (§2.14 G-11)")
    p_show.add_argument("task_path", metavar="<task-path>")
    p_show.add_argument("--format", dest="format", choices=["md","json","full"], default="md")
    p_show.set_defaults(func=cmd_show)

    p_mode = sub.add_parser(
        "resolve-mode",
        help="effective mode 판정 (explicit > state > new-task default)",
    )
    p_mode.add_argument("task_path", metavar="<task-path>")
    p_mode.add_argument("--mode", choices=sorted(VALID_MODES))
    p_mode.add_argument("--new-task", action="store_true", dest="new_task")
    p_mode.add_argument("--skill", help="신규 태스크 기본 mode를 Pilot별 표로 판정 (미지정 시 semi-agentic)")
    p_mode.set_defaults(func=cmd_resolve_mode)

    # ── resolve-start (156) ──
    p_start = sub.add_parser(
        "resolve-start",
        help="Pilot 시작·재개의 mode·workspace·actor 판정 (신규는 init 인자 반환)",
    )
    p_start.add_argument("task_path", metavar="<task-path>")
    p_start.add_argument("--skill", required=True,
                         choices=["opp","opd","opds","opdw","opwt","opgc","oppd","opsdd","oppl","opdd","oppb"])
    p_start.add_argument("--new-task", action="store_true", dest="new_task")
    p_start.add_argument("--interactive", action="store_true")
    p_start.add_argument("--semi-agentic", action="store_true", dest="semi_agentic")
    p_start.add_argument("--agentic", action="store_true")
    p_start.add_argument("--wt", "--worktree", action="store_true", dest="wt")
    p_start.add_argument("--no-wt", action="store_true", dest="no_wt")
    p_start.add_argument("--pm", action="store_true")
    p_start.add_argument("--no-pm", action="store_true", dest="no_pm")
    p_start.set_defaults(func=cmd_resolve_start)

    # ── advance ──
    p_adv = sub.add_parser("advance", help="⬜→🔄 전환 (T-7)")
    p_adv.add_argument("task_path", metavar="<task-path>")
    p_adv.add_argument("--task-step", dest="task_step", metavar="<key>",
                       help="070: task-step key 주소 (예: plan.pm_gate)")
    p_adv.add_argument("--task-step-id", dest="task_step_id", type=int, metavar="<n>",
                       help="070: task-step 숫자 주소(신규, row_id와 동일 의미)")
    p_adv.add_argument("--row", type=int, metavar="<n>",
                       help="[deprecated] --task-step / --task-step-id 사용 권장")
    p_adv.add_argument("--note")
    p_adv.add_argument("--force", action="store_true",
                       help="게이트 산출물·명확화·code-scan 인용 가드 우회(--note 필수). "
                            "157 PM 경로 설계 게이트 가드는 우회하지 못한다")
    p_adv.add_argument("--next-action",
                       help="072: '다음 액션' per-transition 오버라이드(비지속, M-3) — "
                            "미지정 시 프론티어에서 자동 파생")
    p_adv.set_defaults(func=cmd_advance)

    # ── mark ──
    p_mark = sub.add_parser("mark", help="⬜/🔄→✅ 전환 (T-7, §2.4, §2.15)")
    p_mark.add_argument("task_path", metavar="<task-path>")
    p_mark.add_argument("--task-step", dest="task_step", metavar="<key>",
                       help="070: task-step key 주소 (예: plan.pm_gate)")
    p_mark.add_argument("--task-step-id", dest="task_step_id", type=int, metavar="<n>",
                       help="070: task-step 숫자 주소(신규, row_id와 동일 의미)")
    p_mark.add_argument("--row", type=int, metavar="<n>",
                       help="[deprecated] --task-step / --task-step-id 사용 권장")
    p_mark.add_argument("--done", action="store_true", required=True)
    p_mark.add_argument("--note")
    p_mark.add_argument("--as-worker", action="store_true", dest="as_worker")
    p_mark.add_argument("--worker-stage",
                        choices=STAGE_ENUM,
                        dest="worker_stage")
    # 070 R-5: --action-step은 --step의 신규 별칭 — dest 공유로 _parse_step/row["step"] 로직 무변경
    p_mark.add_argument("--step", dest="step", metavar="N/M")
    p_mark.add_argument("--action-step", dest="step", metavar="N/M",
                        help="EXECUTE 액션 진행률 (구 --step 별칭, 070 R-5)")
    # 103 R-21: 소요 '값'과 소요 '미상 선언'은 동시에 성립할 수 없으므로 배타 그룹으로
    #   묶는다. 둘 다 주면 argparse가 exit 2로 거부한다 — `--owner`/`--auto-pass`와
    #   동일 계열의 CLI 인자 형식 오류이므로 ERROR_CODES를 신설하지 않는다(45종 불변).
    duration_group = p_mark.add_mutually_exclusive_group()
    duration_group.add_argument("--worker-duration-minutes", dest="worker_duration_minutes",
                        type=_worker_duration_minutes, metavar="<minutes>",
                        help="103 R-15: 이 행에서 워커가 실제 실행한 시간(분, 0 이상 정수). "
                             "원천은 하네스 duration_ms — 분으로 환산해 전달한다. "
                             "지정 시에만 rows[].worker_duration_minutes에 기록되며, "
                             "미지정 시 필드를 만들지 않는다(기존 태스크 무영향)")
    duration_group.add_argument("--worker-duration-unknown", action="store_true",
                        dest="worker_duration_unknown",
                        help="103 R-21: 이 행의 워커 소요를 알 수 없음을 명시한다"
                             "(중단된 워커·PM 직접 수행·소급 불가 과거 데이터). "
                             "worker_duration_missing 경고를 억제하며, 행에 필드를 "
                             "만들지 않는다 — 기록 결과는 인자 미지정과 완전히 동일하다")
    owner_group = p_mark.add_mutually_exclusive_group()  # C-2
    owner_group.add_argument("--owner", choices=["PM","worker","user","auto"])
    owner_group.add_argument("--auto-pass", action="store_true", dest="auto_pass")
    p_mark.add_argument("--force", action="store_true")
    p_mark.add_argument("--next-action",
                        help="072: '다음 액션' per-transition 오버라이드(비지속, M-3) — "
                             "미지정 시 프론티어에서 자동 파생")
    p_mark.set_defaults(func=cmd_mark)

    # ── block ──
    p_blk = sub.add_parser("block", help="any→❌ 전환 + current_status=blocked (§2.17 트리거 #7)")
    p_blk.add_argument("task_path", metavar="<task-path>")
    p_blk.add_argument("--task-step", dest="task_step", metavar="<key>",
                       help="070: task-step key 주소 (예: plan.pm_gate)")
    p_blk.add_argument("--task-step-id", dest="task_step_id", type=int, metavar="<n>",
                       help="070: task-step 숫자 주소(신규, row_id와 동일 의미)")
    p_blk.add_argument("--row", type=int, metavar="<n>",
                       help="[deprecated] --task-step / --task-step-id 사용 권장")
    p_blk.add_argument("--reason", required=True)
    p_blk.set_defaults(func=cmd_block)

    # ── validate ──
    p_val = sub.add_parser("validate", help="정합성 검증 → violations[] (§2.6, F-10)")
    p_val.add_argument("task_path", metavar="<task-path>")
    p_val.set_defaults(func=cmd_validate)

    # ── add-row ──
    p_add = sub.add_parser("add-row", help="추가작업 행 삽입 (§2.12 G-9)")
    p_add.add_argument("task_path", metavar="<task-path>")
    p_add.add_argument("--after-task-step", dest="after_task_step", metavar="<key>",
                       help="070: 앵커 행 key 주소")
    p_add.add_argument("--after-task-step-id", dest="after_task_step_id", type=int, metavar="<n>",
                       help="070: 앵커 행 숫자 주소(신규, row_id와 동일 의미)")
    p_add.add_argument("--after", type=int, metavar="<n>",
                       help="[deprecated] --after-task-step / --after-task-step-id 사용 권장")
    p_add.add_argument("--stage", required=True, choices=STAGE_ENUM)
    p_add.add_argument("--item", required=True)
    p_add.add_argument("--key", metavar="<key>",
                       help="070 R-9: 신규 행 key 명시 지정 (미지정 시 자동 생성)")
    p_add.add_argument("--note")
    p_add.add_argument("--test-change-kind", choices=["fix", "requirement_change"])
    p_add.set_defaults(func=cmd_add_row)

    # ── status ──
    p_sts = sub.add_parser("status", help="current_status 명시 전환 (§2.11 G-7)")
    p_sts.add_argument("task_path", metavar="<task-path>")
    p_sts.add_argument("--set", dest="set", required=True,
                       choices=["in_progress","done","blocked",
                                "additional_work","additional_work_done",
                                STATUS_COMPLETED_UNMERGED])
    p_sts.add_argument("--note")
    p_sts.set_defaults(func=cmd_status)

    p_clock = sub.add_parser("test-clock", help="Record TEST execution or human wait interval")
    p_clock.add_argument("action", choices=["start", "stop"])
    p_clock.add_argument("task_path", metavar="<task-path>")
    p_clock.add_argument("--kind", required=True, choices=["auto", "human"])
    p_clock.add_argument("--id", required=True)
    p_clock.set_defaults(func=cmd_test_clock)

    p_metrics = sub.add_parser("test-metrics", help="Read only TEST timing and iteration counts")
    p_metrics.add_argument("task_path", metavar="<task-path>")
    p_metrics.set_defaults(func=cmd_test_metrics)

    # ── run-start (131 D8) ──
    p_run = sub.add_parser(
        "run-start",
        help="새 run_id 발급 + state.json 기록 (131 D8) — 재호출 시 교체, 이력 누적 없음")
    p_run.add_argument("task_path", metavar="<task-path>")
    p_run.set_defaults(func=cmd_run_start)

    # ── finalize-attribution (118 D-4b / AC-4) ──
    p_fin = sub.add_parser(
        "finalize-attribution",
        help="merge 확인 후 허브 .opal/MEMORY.json history 귀속 (118 AC-4)")
    p_fin.add_argument("task_path", metavar="<task-path>")
    # required=True로 두지 않는다 — 미지정도 이 도구의 err() 관례(exit 1 + 단일 라인
    # JSON)로 거부해야 하기 때문이다(argparse의 exit 2/usage 출력 회피).
    p_fin.add_argument("--allocator-root", dest="allocator_root", metavar="<abs>",
                       help="worktree registry가 발급한 허브 절대 경로 (추론하지 않음)")
    p_fin.set_defaults(func=cmd_finalize_attribution)

    # ── boot-summary ──
    p_boot = sub.add_parser(
        "boot-summary",
        help="프로젝트 하위 미완료 태스크 1건의 읽기 전용 부트 요약",
    )
    p_boot.add_argument("project_root", metavar="<project-root>")
    p_boot.set_defaults(func=cmd_boot_summary)

    # Friendly alias used by bootstrap integrations; both routes share the
    # exact same implementation and output contract.
    p_boot_alias = sub.add_parser("boot-brief", help=argparse.SUPPRESS)
    p_boot_alias.add_argument("project_root", metavar="<project-root>")
    p_boot_alias.set_defaults(func=cmd_boot_summary)

    # ── gate-pass ──
    p_gp = sub.add_parser("gate-pass",
                          help="[DEPRECATED] Gate 4행 일괄 ✅ 처리 — 레거시 state.json 전용 (§2.13 G-10, 014 Phase 4)")
    p_gp.add_argument("task_path", metavar="<task-path>")
    p_gp.add_argument("--start", type=int, required=True)
    p_gp.add_argument("--note")
    p_gp.set_defaults(func=cmd_gate_pass)

    # ── spec-validate (070 R-6) ──
    p_spec = sub.add_parser("spec-validate", help="pipeline.json 스펙 검증 (070 R-6, DEC-2)")
    p_spec.add_argument("spec_path", metavar="<pipeline.json>")
    p_spec.set_defaults(func=cmd_spec_validate)

    # ── event-verify ──
    p_evt = sub.add_parser(
        "event-verify",
        help="단계 진입 전 event-loader receipt 최신성 검증 (상태 파일 비접촉)",
    )
    p_evt.add_argument("--event", required=True,
                       help="검증할 정확한 이벤트 id (예: pilot.start, stage.execute)")
    p_evt.add_argument("--receipt", required=True,
                       help="event-loader load 응답 또는 receipt object JSON 파일")
    p_evt.add_argument("--manifest", help="events.json 경로")
    p_evt.add_argument("--source-root", dest="source_root",
                       help="framework source checkout root")
    p_evt.add_argument("--deployed-root", dest="deployed_root",
                       help="installed OPAL root")
    p_evt.add_argument("--project-root", dest="project_root",
                       help="current project root")
    p_evt.set_defaults(func=cmd_event_verify)

    # ── verify ──
    p_vfy = sub.add_parser(
        "verify",
        help="TEST-SCENARIO.md mock 코드 패턴 + 증거 누락 검사 (PLAN 013, 헌법 §4)"
    )
    p_vfy.add_argument("task_path", metavar="<task-path>")
    p_vfy.add_argument("--scenario", metavar="<path>",
                       help="TEST-SCENARIO.md 경로 명시 (기본: <task-path>/TEST-SCENARIO.md)")
    # 016 RED-first 게이트
    p_vfy.add_argument("--red-check", action="store_true", dest="red_check",
                       help="RED 증거(실패 출력) 게이트 — 누락 시 red_evidence_missing")
    p_vfy.add_argument("--changed-files", nargs="*", default=[], dest="changed_files",
                       help="fix 루핑 변경 파일 목록 (테스트 불변성 입력)")
    p_vfy.add_argument("--test-globs", nargs="*", default=None, dest="test_globs",
                       help="테스트 파일 식별 glob 패턴 (프로젝트 탐지값 주입 — 하드코딩 금지)")
    p_vfy.add_argument("--fix-mode", action="store_true", dest="fix_mode",
                       help="fix 루핑 컨텍스트 — 테스트 파일 수정 시 test_modified_in_fix")
    # 005 명확화 게이트
    p_vfy.add_argument("--clarification-check", action="store_true", dest="clarification_check",
                       help="TASK 4요소 잠금 게이트 — 미충족 시 clarification_gate_unmet (PRINCIPLES §1 집행)")
    p_vfy.add_argument("--task-md", metavar="<path>", dest="task_md",
                       help="TASK.md 경로 명시 (기본: <task-path>/TASK.md)")
    # 098 근거 등급 확정/미확정 판정 게이트
    p_vfy.add_argument("--evidence-check", action="store_true", dest="evidence_check",
                       help="근거 등급 확정/미확정 판정 라우터 — 항목별 판정+사유를 "
                            "반환하되 차단하지 않음(exit 0 유지, PLAN §3.3.2)")
    # 106 code-scan 결과 인용 게이트
    p_vfy.add_argument("--code-scan-citation-check", action="store_true",
                       dest="code_scan_citation_check",
                       help="PLAN.md code-scan 결과 인용 게이트 — 미충족 시 "
                            "code_scan_citation_unmet(exit 1). 자산·산출물·적용 범위 "
                            "3조건 미해당 시 skipped(exit 0, PLAN §3.4.2)")
    p_vfy.add_argument("--plan-contract-check", action="store_true",
                       dest="plan_contract_check",
                       help="sdlc-v2 PLAN.md Work items 계약 검사 — 필수 열/W-ID/선행/그룹/"
                            "AC-C 연결/동일 그룹 파일 충돌 미충족 시 plan_contract_unmet(exit 1). "
                            "legacy PLAN은 skipped(exit 0)")
    # 135 W-4 (AC-5~AC-8) — run-log 완전성 진단 (읽기 전용, 비차단)
    p_vfy.add_argument("--run-log-completeness-check", action="store_true",
                       dest="run_log_completeness_check",
                       help="state.json run_log 계약과 JSONL 사건을 대조해 누락·관측"
                            "지점을 진단한다(비차단, exit 0 유지). run_log 블록이 없으면"
                            "skipped 취급")
    # 170 AC-1 — design-gate 결정론 사전검사 (evaluator 호출 전, 회차·상태 비소비)
    p_vfy.add_argument("--design-gate-check", action="store_true",
                       dest="design_gate_check",
                       help="design-gate ①~⑦ 결정론 검사 + decision_clarity 유보 어휘 "
                            "후보 린트를 회차·상태 소비 없이 실행한다(비차단, exit 0 유지). "
                            "state.json 부재·PM 경로 아님은 skipped 취급")
    p_vfy.set_defaults(func=cmd_verify)

    # ── log-event (135 W-3, CONTRACT §2.4 state-tool.log-event) ──
    p_log = sub.add_parser(
        "log-event",
        help="PM direct activity 기록 (CONTRACT §2.4 state-tool.log-event)")
    p_log.add_argument("task_path", metavar="<task-path>")
    p_log.add_argument("--event", required=True, choices=["activity", "pm.report"],
                       help="activity 또는 pm.report(TASK-147 D-2, §2.4). "
                            "stop.decision은 이 표면이 수용하지 않는다(D-6 — Stop hook "
                            "receipt drain 경로가 조립한다)")
    p_log.add_argument("--kind", choices=sorted(_PM_ACTIVITY_KIND_ENUM),
                       help="--event activity에서 --data 미지정 시 필수. "
                            "data.kind 값(§1.3 4종 enum)")
    # ── TASK-147 W-5 — `--event pm.report`의 data 폐쇄 3축 ──
    # [MUST] choices를 걸지 않는다. argparse가 거르면 앞단 거부가 usage 오류(exit 2)가
    # 되어 기록 코어의 `schema_invalid`와 판정이 갈린다(§1.3 중복 방어 일치 계약).
    # 값 검증은 `_build_pm_report_data()`가 한다.
    p_log.add_argument("--report-type", dest="report_type",
                       help="--event pm.report에서 --data 미지정 시 필수. "
                            "data.report_type(§1.3 2종 enum: "
                            f"{', '.join(_PM_REPORT_TYPE_ENUM)})")
    p_log.add_argument("--transition-action", dest="transition_action",
                       help="--event pm.report에서 --data 미지정 시 필수. "
                            "data.transition_action(§1.3 4종 enum: "
                            f"{', '.join(_PM_TRANSITION_ACTION_ENUM)})")
    p_log.add_argument("--user-input-required", dest="user_input_required",
                       help="--event pm.report에서 --data 미지정 시 필수. "
                            "data.user_input_required(true|false)")
    p_log.add_argument("--summary", required=True)
    p_log.add_argument("--reason")
    p_log.add_argument("--stage")
    p_log.add_argument("--task-step", dest="task_step")
    p_log.add_argument("--work-item", dest="work_item")
    p_log.add_argument("--refs", nargs="*", default=None)
    p_log.add_argument("--data",
                       help="사건 data 객체 원문 JSON(§1.3 폐쇄 목록 검증 대상). "
                            "미지정 시 activity는 --kind로, pm.report는 "
                            "--report-type/--transition-action/--user-input-required로 구성")
    p_log.add_argument("--format", dest="format", choices=["json"])
    p_log.set_defaults(func=cmd_log_event)

    # ── gate-request (135 W-3, CONTRACT §2.4 state-tool.gate-request) ──
    p_greq = sub.add_parser(
        "gate-request",
        help="gate.requested 기록 (CONTRACT §2.4 state-tool.gate-request)")
    p_greq.add_argument("task_path", metavar="<task-path>")
    p_greq.add_argument("--gate-id", dest="gate_id", required=True)
    p_greq.add_argument("--summary", required=True)
    p_greq.add_argument("--stage")
    p_greq.add_argument("--task-step", dest="task_step")
    p_greq.add_argument("--format", dest="format", choices=["json"])
    p_greq.set_defaults(func=cmd_gate_request)

    # ── gate-resolve (135 W-3, CONTRACT §2.4 state-tool.gate-resolve) ──
    p_gres = sub.add_parser(
        "gate-resolve",
        help="gate.resolved 기록 (CONTRACT §2.4 state-tool.gate-resolve)")
    p_gres.add_argument("task_path", metavar="<task-path>")
    p_gres.add_argument("--gate-id", dest="gate_id", required=True)
    p_gres.add_argument("--verdict", required=True, choices=["approved", "rejected", "auto"])
    p_gres.add_argument("--owner", required=True, choices=["PM", "user", "auto"])
    p_gres.add_argument("--note")
    p_gres.add_argument("--format", dest="format", choices=["json"])
    p_gres.set_defaults(func=cmd_gate_resolve)

    # ── design-gate (157 DEC-7/DEC-9/DEC-10) ──
    p_dg = sub.add_parser("design-gate", help="PM 경로 독립 설계 게이트 (start|record|reset)")
    dg_sub = p_dg.add_subparsers(dest="design_gate_command", metavar="<start|record|reset>")
    dg_sub.required = True
    p_dgs = dg_sub.add_parser("start", help="결정론 검사 후 설계 게이트 시도 시작 (gate.requested)")
    p_dgs.add_argument("task_path", metavar="<task-path>")
    p_dgs.add_argument("--iteration", type=int, required=True, metavar="N")
    p_dgs.set_defaults(func=cmd_design_gate_start)
    p_dgr = dg_sub.add_parser("record", help="evaluator design-rubric 판정 기록 (gate.resolved)")
    p_dgr.add_argument("task_path", metavar="<task-path>")
    p_dgr.add_argument("--iteration", type=int, required=True, metavar="N")
    p_dgr.add_argument("--verdict", required=True, choices=["pass", "rewrite", "input_error"])
    p_dgr.add_argument("--evaluator-result", dest="evaluator_result", required=True, metavar="<json>")
    p_dgr.add_argument("--rewrite-target", dest="rewrite_target", choices=["plan", "scenario", "both"])
    p_dgr.add_argument("--advisory-responses", dest="advisory_responses", metavar="<json>",
                       help="advisory 응답 파일 [{id, response: apply|retain, reason}] (167)")
    p_dgr.set_defaults(func=cmd_design_gate_record)
    p_dgx = dg_sub.add_parser("reset", help="반복 상한(retry_limit) 해제 — 사용자 결정 전용")
    p_dgx.add_argument("task_path", metavar="<task-path>")
    p_dgx.add_argument("--owner", choices=["PM", "worker", "user", "auto"])
    p_dgx.add_argument("--note")
    p_dgx.set_defaults(func=cmd_design_gate_reset)

    # ── design-decision (157 DEC-12) ──
    p_dd = sub.add_parser("design-decision", help="PM 경로 PLAN 단계 설계 결정 분류 기록")
    p_dd.add_argument("task_path", metavar="<task-path>")
    p_dd.add_argument("--scope", required=True, choices=["external", "detail"])
    p_dd.add_argument("--summary", required=True)
    p_dd.add_argument("--basis", required=True)
    p_dd.set_defaults(func=cmd_design_decision)

    return parser

# ─────────────────────────────────────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = build_parser()
    args   = parser.parse_args()
    state_writers = {
        "advance", "mark", "block", "add-row",
        "status", "test-clock", "run-start", "gate-pass", "log-event",
        "gate-request", "gate-resolve", "design-gate", "design-decision",
    }
    resolve_mode_write = (
        args.command == "resolve-mode" and args.mode is not None
        and (pathlib.Path(args.task_path) / "state.json").exists()
    )
    if args.command in state_writers or resolve_mode_write:
        task_path = resolve_task_path(args.task_path, args.command)
        with state_writer_lock(task_path):
            args.func(args)
    else:
        args.func(args)

if __name__ == "__main__":
    main()
