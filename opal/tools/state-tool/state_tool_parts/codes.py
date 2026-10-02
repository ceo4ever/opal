# -*- coding: utf-8 -*-
"""
@header {
  "module": "state_tool_parts.codes",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "state-tool 상수·코드표 — 단계·모드 enum, 오류 코드 테이블, 자동 승인 판정",
  "exports": [
    "STAGE_ENUM",
    "ERROR_CODES",
    "can_auto_approve_user_confirmation"
  ]
}
"""

import re


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
    "opd2": {"mode": "agentic", "workspace": "worktree", "actor": None},
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
    "design_gate_partial_invalid":
        "design-gate combine 부분 결과가 계약을 충족하지 않습니다: {detail}",
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
# 168 W-1: opd2 전용 mark 가드 오류 코드 — DESIGN_GATE_ERROR_CODES(18종, 동결)와
#   물리 분리한다(scenario_gate_record_required 선례, D-1). `_error_template()`이
#   ERROR_CODES → RUN_LOG_STATE_ERROR_CODES → DESIGN_GATE_ERROR_CODES →
#   TEST_CYCLE_ERROR_CODES → 이 테이블 순으로 조회한다.
# ─────────────────────────────────────────────────────────────────────────────
OPD2_GATE_ERROR_CODES = {
    "opd2_gate_record_required":
        "opd2 게이트 판정이 통과하지 않았습니다({reason}) — lifecycle.py verify-mark로 "
        "Builder/Verifier/Reviewer 게이트를 다시 확인한 뒤 다시 mark하세요",
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
