# -*- coding: utf-8 -*-
"""
@header {
  "module": "state_tool_parts.commands_core",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "state-tool 핵심 서브커맨드 — init·show·resolve·advance·mark·block·validate·add-row·status",
  "exports": [
    "cmd_init",
    "cmd_show",
    "cmd_advance",
    "cmd_mark",
    "cmd_validate"
  ]
}
"""

import argparse
import json
import pathlib
import re
import sys
import uuid

from . import base
from .codes import (
    ACTOR_SKILLS,
    ALLOWED_TRANSITIONS,
    KEY_PATTERN,
    LEGACY_FROZEN_BANNER,
    PIPELINE_MARKER_END,
    PIPELINE_MARKER_START,
    STAGE_ENUM,
    STATUS_COMPLETED_UNMERGED,
    STATUS_TEXT,
    TASK_COMPLETE_STATUSES,
    WARNING_CODES,
    WORKSPACE_REQUIRED_SKILLS,
    _is_close_final_row,
    can_auto_approve_user_confirmation,
    new_task_defaults,
    normalize_stored_mode,
    stage_to_slug,
)
from .base import (
    _atomic_write_state_json,
    _claim_task_lease_if_needed,
    _current_session_id,
    _derive_next_action,
    err,
    load_state_json,
    ok,
    resolve_task_path,
    save_state_json,
    save_state_json_atomic,
)
from .run_log import (
    _check_active_completion_evidence,
    _reconcile_worker_duration_minutes,
    _run_log_block,
    build_state_changed_event,
    run_log_commit,
    run_log_diagnose,
)
from .journal import (
    _AUTO_PASS_PREFIX,
    _build_new_state_md,
    append_decision_log,
    build_todo_mirror,
    load_state_md,
    render_pipeline_table,
    resolve_owner_placeholder,
    resolve_row_index,
    save_state_md,
    sync_state_md,
)
from .guards import (
    _resolve_active_channel,
    auto_approve_prior_user_confirmations,
    build_gate_payload,
    build_rows_from_pipeline_json,
    build_rows_from_skill_md,
    build_rows_from_spec,
    check_close_gate,
    check_gate_artifacts,
    check_stage_transition_guard,
    load_pipeline_spec,
    validate_pipeline_spec,
)
from .gates import (
    _check_evidence,
    _check_mock_patterns,
    _find_scenario_file,
    _run_clarification_hook,
    _run_code_scan_citation_hook,
    apply_opd2_gate_mark_guard,
    apply_pm_design_guards,
    apply_scenario_gate_mark_guard,
)


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

    run_log_core = base._import_run_log_core()

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
    now_str = base.get_kst_datetime(command)

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
        now_str = base.get_kst_datetime(command)
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
    pathlib.Path(__file__).resolve().parent.parent.parent.parent
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
    now_str = base.get_kst_datetime(command)
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

    # 168 W-1 mark 가드: opd2 게이트 행 완료 전 lifecycle.py verify-mark(형제 스킬 스크립트)
    #   통과 필수. 상태 변경·자동 승인 이전이라 거부 시 state.json이 불변이며
    #   --force·--auto-pass·--as-worker로 우회할 수 없다. skill != "opd2"이면 no-op.
    apply_opd2_gate_mark_guard(task_path, row, command,
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
    now_str = base.get_kst_datetime(command)
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

    now_str = base.get_kst_datetime(command)
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

    now_str = base.get_kst_datetime(command)

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

    now_str = base.get_kst_datetime(command)
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
