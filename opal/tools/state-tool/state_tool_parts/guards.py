# -*- coding: utf-8 -*-
"""
@header {
  "module": "state_tool_parts.guards",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "state-tool 가드 — 전이 검사, 게이트 산출물 검사, 행 빌드",
  "exports": [
    "check_gate_artifacts",
    "build_rows_from_pipeline_json"
  ]
}
"""

import json
import pathlib
import re

from .codes import (
    KEY_PATTERN,
    LABEL_STATUS_MAP,
    STAGE_ENUM,
    can_auto_approve_user_confirmation,
    stage_to_slug,
)
from .base import (
    _COMPLETE_STATUSES,
    err,
)


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

    skill_enum = ["opp", "opd", "opds", "opdw", "opwt", "opgc", "oppd", "opsdd", "oppl", "opdd", "oppb", "opd2"]  # 132 W-3보강: oppb spec-validate 허용 (P9 pipeline.json skill='oppb'); 168 W-1: opd2 등록
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
