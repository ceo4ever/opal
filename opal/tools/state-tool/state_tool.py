"""
@header {
  "module": "state_tool",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "OPAL 파이프라인 현황판 JSON SSOT 관리 CLI — 9개 서브 명령(init/show/advance/mark/block/validate/add-row/status/gate-pass[deprecated]) + verify + 3-way 모드(interactive/semi-agentic/agentic) 지원. 014 Phase 4: 새 표준 행 구조(QA Gate/State Gate 행 없음)와 정합 — gate-pass deprecate, CLOSE 마지막 행 판정 항목명 비의존화. 016: verify --red-check(RED 증거 게이트) + --fix-mode/--changed-files/--test-globs(테스트 불변성 게이트) 추가 — RED-first TDD 트랙 deterministic 집행. 017: mark --step N/M 다중 Step 조기 done 가드 — N<M이면 in_progress 유지(done 미처리) + 진행률(step) 영속화, N==M에서만 done; 미완 행은 기존 stage-transition guard가 단계전환·CLOSE 진입을 자동 차단. 005: verify --clarification-check + TASK→다음단계 자동 훅 — TASK 4요소(목표/범위/제약/완료기준) 미잠금 시 다음 단계 진입 거부(PRINCIPLES §1 집행), 정책 A graceful skip(섹션/파일 부재 시 하위호환).",
  "exports": [
    "cmd_init", "cmd_show", "cmd_advance", "cmd_mark",
    "cmd_block", "cmd_validate", "cmd_add_row", "cmd_status", "cmd_gate_pass"
  ]
}
"""

# PLAN §2.1 구현 명세 — TASK T-11: 표준 라이브러리만 import
import argparse
import fnmatch
import json
import os
import pathlib
import re
import subprocess
import sys
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# 상수 (PLAN §2.2 G-4, §2.18 E-1, §2.13 G-10)
# ─────────────────────────────────────────────────────────────────────────────

STAGE_ENUM = [
    "TASK", "ANALYSIS", "PLAN", "TEST-SCENARIO", "EXECUTE", "TEST",
    "WIREFRAME", "QA", "SPEC", "REVIEW", "DESIGN",
    "VERIFY", "SCAN", "CHECK", "REPORT", "WBS", "CLOSE"
]

# semi-agentic 모드 경계 — 이 stage 집합에 속하는 행은 EXECUTE-equivalent 이전으로 간주
# (PLAN-equivalent 단계까지 사용자 검토 강제) — D-DEC-5 (140)
MODE_BOUNDARY_STAGES = {
    "TASK", "ANALYSIS", "PLAN", "TEST-SCENARIO",
    "SPEC", "REVIEW", "DESIGN",
    "WBS", "WIREFRAME",
}

STATUS_LABEL_MAP = {
    "pending":     "⬜",
    "in_progress": "🔄",
    "done":        "✅",
    "failed":      "❌",
    "na":          "-",
}
LABEL_STATUS_MAP = {v: k for k, v in STATUS_LABEL_MAP.items()}

# PLAN §2.2 G-4 표준 항목 상수
# 014 Phase 4: 새 표준 행 구조에서는 "작업 / PM Gate / 사용자 확인 / DONE.md 생성"만 사용한다.
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
    "marker_missing":                 "STATE.md에 <!-- pipeline:start --> ~ <!-- pipeline:end --> 마커 누락",
    "already_initialized":            "state.json이 이미 존재합니다. --force로 덮어쓰기 가능",
    "date_tool_failed":               "node ~/.opal/tools/date/date.js datetime 호출 실패 — STATE.md 변경 없음(원자성)",
    "import_failed":                  "기존 STATE.md 파싱 실패 — 마크다운 표 정규식 매칭 0건",
    "invalid_status_transition":      "current_status 전이 그래프(§2.11 G-7) 위반: {from_status} → {to_status}",
    "row_not_found":                  "--row {row_id}에 해당하는 행이 state.json에 없음",
    "invalid_stage_enum":             "--stage {value}는 §2.2 G-3 enum 16종에 없음",
    "gate_pattern_mismatch":          "--start {row} 위치 연속 4행이 [QA Gate, State Gate, PM Gate, State Gate] 패턴과 불일치",
    "gate_stage_mixed":               "gate-pass 4행이 모두 동일 stage가 아님",
    "state_not_initialized":          "state.json이 존재하지 않습니다. state init을 먼저 실행하세요",
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
}

PIPELINE_MARKER_START = "<!-- pipeline:start -->"
PIPELINE_MARKER_END   = "<!-- pipeline:end -->"

# current_status 전이 그래프 (PLAN §2.11 G-7)
ALLOWED_TRANSITIONS = {
    "in_progress":          {"done", "blocked", "additional_work"},
    "done":                 {"additional_work", "blocked"},
    "blocked":              {"in_progress", "done"},
    "additional_work":      {"additional_work_done", "blocked", "in_progress"},
    "additional_work_done": {"additional_work", "blocked"},
}

# ─────────────────────────────────────────────────────────────────────────────
# 응답 헬퍼 (PLAN §2.1, D-11 패턴 차용)
# ─────────────────────────────────────────────────────────────────────────────

def ok(command, **kwargs):
    """성공 응답 — 단일 라인 JSON, exit 0"""
    print(json.dumps({"ok": True, "command": command, **kwargs}, ensure_ascii=False, default=str))

def err(command, code, message=None, exit_code=1, **kwargs):
    """에러 응답 — 단일 라인 JSON, exit {exit_code}
    code는 ERROR_CODES 키 중 하나여야 한다 (§2.18 SSOT).
    추가 필드(kwargs)로 에러 컨텍스트(row_id, stage 등)를 포함한다.
    """
    if message is None:
        template = ERROR_CODES.get(code, code)
        try:
            message = template.format(**kwargs)
        except (KeyError, IndexError):
            message = template
    payload = {"ok": False, "command": command, "error": code, "message": message}
    payload.update(kwargs)
    print(json.dumps(payload, ensure_ascii=False, default=str))
    sys.exit(exit_code)

# ─────────────────────────────────────────────────────────────────────────────
# 시점 취득 (PLAN §2.11 G-5, TASK T-5)
# ─────────────────────────────────────────────────────────────────────────────

def get_kst_datetime(command="(unknown)"):
    """node ~/.opal/tools/date/date.js datetime 호출 → KST YYYY-MM-DD HH:mm 반환
    실패 시 date_tool_failed 에러 응답 후 exit 2.
    """
    date_js = os.path.expanduser("~/.opal/tools/date/date.js")
    try:
        result = subprocess.run(
            ["node", date_js, "datetime"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0 or not result.stdout.strip():
            err(command, "date_tool_failed",
                message=f"exit={result.returncode}, stderr={result.stderr.strip()}",
                exit_code=2)
        return result.stdout.strip()
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

def load_state_json(task_path, command):
    """state.json 로드. 미존재 시 state_not_initialized + exit 1."""
    state_file = task_path / "state.json"
    if not state_file.exists():
        err(command, "state_not_initialized")
    with open(state_file, encoding="utf-8") as f:
        return json.load(f)

def save_state_json(task_path, state):
    """state.json 저장 (UTF-8, 들여쓰기 2칸)."""
    state_file = task_path / "state.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")

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
# 마크다운 렌더 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def render_pipeline_table(rows):
    """state.json rows[]를 마크다운 표로 렌더 (마커 제외)."""
    lines = [
        "## 파이프라인 현황판",
        "",
        "> 상태값: ⬜ 대기 / 🔄 진행 중 / ✅ 완료 / ❌ 실패 / - 해당 없음",
        "> **수행 원칙**: 위에서 아래로 순서대로 처리한다. 현재 행이 ✅가 아니면 다음 행으로 진행 불가.",
        "",
        "| # | 단계 | 항목 | 상태 | 시점 |",
        "|---|------|------|------|------|",
    ]
    for row in rows:
        ts = row.get("timestamp") or ""
        lines.append(
            f"| {row['row_id']} | {row['stage']} | {row['item']} | {row['status_label']} | {ts} |"
        )
    return "\n".join(lines)

def replace_pipeline_section(md_content, new_table_content):
    """STATE.md 마커 영역을 new_table_content로 교체 반환.
    마커 없으면 None 반환 (호출자가 marker_missing 처리).
    """
    start_idx = md_content.find(PIPELINE_MARKER_START)
    end_idx   = md_content.find(PIPELINE_MARKER_END)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        return None
    before = md_content[:start_idx]
    after  = md_content[end_idx + len(PIPELINE_MARKER_END):]
    return f"{before}{PIPELINE_MARKER_START}\n{new_table_content}\n{PIPELINE_MARKER_END}{after}"

def update_state_md_header(md_content, new_datetime):
    """G-5: STATE.md '> 최종 갱신:' 라인 교체."""
    return re.sub(
        r"^(> 최종 갱신: ).*$",
        lambda m: f"{m.group(1)}{new_datetime}",
        md_content, count=1, flags=re.MULTILINE
    )

def update_current_status_section(md_content, progress=None, status_text=None):
    """G-6: '## 현재 상태' 섹션 내 '- 진행:' / '- 상태:' 라인 갱신 (None이면 미변경)."""
    if progress is not None:
        md_content = re.sub(
            r"^(- 진행: ).*$",
            lambda m: f"{m.group(1)}{progress}",
            md_content, count=1, flags=re.MULTILINE
        )
    if status_text is not None:
        md_content = re.sub(
            r"^(- 상태: ).*$",
            lambda m: f"{m.group(1)}{status_text}",
            md_content, count=1, flags=re.MULTILINE
        )
    return md_content

# ─────────────────────────────────────────────────────────────────────────────
# 의사결정 로그 자동 기재 (PLAN §2.17 G-14/G-15)
# ─────────────────────────────────────────────────────────────────────────────

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
    existing_rows = m.group(2)
    row_count = existing_rows.count("\n| ")  # "|" 로 시작하는 줄 수
    new_num = row_count + 1
    new_row = f"| {new_num} | {now_str} | {decision} | {reason} |\n"

    replacement = m.group(1) + existing_rows + new_row
    return md_content[:m.start()] + replacement + md_content[m.end():]

# ─────────────────────────────────────────────────────────────────────────────
# 공통 STATE.md 갱신 후처리 (G-5, G-6, 마커 교체)
# ─────────────────────────────────────────────────────────────────────────────

def sync_state_md(task_path, state, now_str, command,
                  progress=None, status_text=None,
                  decision=None, reason=None):
    """갱신 명령 공통 후처리:
    1. STATE.md 마커 영역 교체 (marker_missing 시 err)
    2. G-5 최종 갱신 헤더 교체
    3. G-6 현재 상태 섹션 갱신
    4. G-14/G-15 의사결정 로그 기재 (decision/reason이 None이면 생략)
    """
    md = load_state_md(task_path)
    if md is None:
        # STATE.md 자체가 없으면 마커 에러로 처리
        err(command, "marker_missing")

    new_table = render_pipeline_table(state["rows"])
    replaced  = replace_pipeline_section(md, new_table)
    if replaced is None:
        err(command, "marker_missing")

    replaced = update_state_md_header(replaced, now_str)
    replaced = update_current_status_section(replaced, progress=progress, status_text=status_text)

    if decision is not None:
        replaced = append_decision_log(replaced, now_str, decision, reason or "(none)")

    save_state_md(task_path, replaced)

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

# ─────────────────────────────────────────────────────────────────────────────
# 단계 건너뛰기 차단 (PLAN §M-A stage-transition guard)
# ─────────────────────────────────────────────────────────────────────────────

# 완료로 간주하는 상태값 — 이 상태의 앞 행은 건너뛰기 검증에서 제외
_COMPLETE_STATUSES = {"done", "additional_work_done", "na"}


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
        if prev.get("status") not in _COMPLETE_STATUSES:
            incomplete.append(prev["row_id"])

    if incomplete:
        err(command, "stage_transition_violation",
            row_id=row["row_id"],
            incomplete_rows=incomplete)


# ─────────────────────────────────────────────────────────────────────────────
# CLOSE 진입 게이트 검증 (PLAN §2.16 G-13)
# ─────────────────────────────────────────────────────────────────────────────

def check_close_gate(state, row_index, command, auto_pass=False, force=False):
    """CLOSE 단계 첫 행 갱신 시 게이트 검증.
    위반 시 close_gate_violation 또는 agentic_close_gate_requires_user.
    force=True면 스킵.
    """
    row = state["rows"][row_index]
    if row["stage"] != "CLOSE":
        return  # CLOSE 아니면 무관

    # CLOSE 단계 첫 행 여부 확인
    is_first_close = (row_index == 0 or state["rows"][row_index - 1]["stage"] != "CLOSE")
    if not is_first_close:
        return

    # agentic / semi-agentic 모드 + auto-pass 거부 (§2.16 G-13 / D-DEC-5b)
    if auto_pass and state.get("mode") in ("agentic", "semi-agentic"):
        err(command, "agentic_close_gate_requires_user", row_id=row["row_id"])

    if force:
        return  # force 우회

    # 직전 단계 사용자 확인 행 검색 (역순)
    prev_user_row = None
    for i in range(row_index - 1, -1, -1):
        if state["rows"][i].get("item") == "사용자 확인":
            prev_user_row = state["rows"][i]
            break

    if prev_user_row is None:
        err(command, "close_gate_violation",
            violation_detail="no preceding user confirmation row found")

    if prev_user_row["status"] != "done" or prev_user_row.get("owner") != "user":
        err(command, "close_gate_violation",
            violation_detail=(
                f"user confirmation row {prev_user_row['row_id']} is not done with owner=user "
                f"(status={prev_user_row['status']}, owner={prev_user_row.get('owner')})"
            ))

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
        # agentic 자동 마킹 (§2.20.1 — CLOSE 사용자 확인 행 제외)
        if mode == "agentic" and name == "사용자 확인" and stage != "CLOSE":
            row["status"]       = "na"
            row["status_label"] = "-"
            row["owner"]        = "auto"
            row["note"]         = "agentic auto-na at init"

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
        # 단계 10: agentic 자동 마킹 (§2.20.1 동일 규칙)
        if mode == "agentic" and item == "사용자 확인" and stage != "CLOSE":
            row["status"]       = "na"
            row["status_label"] = "-"
            row["owner"]        = "auto"
            row["note"]         = "agentic auto-na at init"

        rows.append(row)
    return rows

# ─────────────────────────────────────────────────────────────────────────────
# 기존 STATE.md import 파싱 (PLAN §2.5, T-13)
# ─────────────────────────────────────────────────────────────────────────────

def parse_existing_state_md(md_content, command):
    """마크다운 표 정규식 파싱 → rows[] 반환. 0건 시 import_failed."""
    row_pattern = re.compile(
        r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([⬜🔄✅❌\-])\s*\|\s*([^|]*?)\s*\|",
        re.MULTILINE
    )
    matches = row_pattern.findall(md_content)
    if not matches:
        err(command, "import_failed")

    rows = []
    for i, (rid, stage, item, status_label, timestamp) in enumerate(matches):
        stage     = stage.strip()
        item      = item.strip()
        timestamp = timestamp.strip() or None
        status    = LABEL_STATUS_MAP.get(status_label, "pending")

        # stage 검증
        if stage not in STAGE_ENUM:
            stage = "TASK"  # fallback — import 시는 관대하게 처리

        row = {
            "row_id":       i + 1,
            "stage":        stage,
            "item":         item,
            "status":       status,
            "status_label": status_label if status_label != "-" else "-",
            "timestamp":    timestamp,
            "owner":        "PM",
            "note":         None,
        }
        rows.append(row)
    return rows

# ─────────────────────────────────────────────────────────────────────────────
# 9개 서브 명령 구현
# ─────────────────────────────────────────────────────────────────────────────

# ── 1. init ──────────────────────────────────────────────────────────────────

def cmd_init(args):
    """PLAN §2.11 G-8 — state.json + STATE.md 생성"""
    command = "init"
    task_path = resolve_task_path(args.task_path, command)

    # --rows-acts 시그니처 정의만 (§2.20.3, R-13)
    if getattr(args, "rows_acts", None):
        err(command, "rows_acts_not_implemented",
            note="opsdd ACT dynamic injection is out of scope for task 134. Track at R-13.",
            exit_code=2)

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
    import_mode = args.import_existing

    if import_mode:
        md_content = load_state_md(task_path)
        if md_content:
            try:
                rows = parse_existing_state_md(md_content, command)
            except SystemExit:
                if not (args.rows_spec or args.rows_from):
                    raise  # rows_spec/from fallback 없으면 그대로 실패
                rows = []  # fallback으로 아래에서 처리

    if not rows:
        if args.rows_spec:
            rows = build_rows_from_spec(args.rows_spec, command, args.mode)
        elif args.rows_from:
            rows = build_rows_from_skill_md(args.rows_from, command, args.mode)
        else:
            # 행 없이 init — 최소 1행 빈 구조는 허용 안 함, 경고 없이 빈 rows로 진행
            rows = []

    # task_id = 마지막 디렉토리명
    task_id = task_path.name

    state = {
        "task_id":        task_id,
        "skill":          args.skill,
        "mode":           args.mode,
        "schema_version": "1.0",
        "created_at":     now_str,
        "updated_at":     now_str,
        "current_status": "in_progress",
        "rows":           rows,
    }

    # force 사용 시 기존 state.json의 created_at 보존
    if state_file.exists() and args.force:
        try:
            old = json.loads(state_file.read_text(encoding="utf-8"))
            state["created_at"] = old.get("created_at", now_str)
        except Exception:
            pass

    save_state_json(task_path, state)

    # STATE.md 생성 or 갱신
    first_stage = rows[0]["stage"] if rows else "TASK"
    task_title  = args.task_title or task_id
    next_action = args.next_action or "PLAN 단계 진입"
    table_str   = render_pipeline_table(rows)

    if import_mode:
        # 기존 STATE.md에 마커 영역만 교체/삽입 (G-8 import 정책)
        existing_md = load_state_md(task_path) or ""
        new_md = replace_pipeline_section(existing_md, table_str)
        if new_md is None:
            # 마커 없음 — 마커 영역을 파이프라인 표 직전에 삽입 시도
            # 파이프라인 현황판 헤더 찾아 마커로 감싸기
            ph = existing_md.find("## 파이프라인 현황판")
            if ph != -1:
                # 현황판 섹션 끝 찾기 (다음 ## 헤더 직전)
                next_h = re.search(r"\n## ", existing_md[ph + 1:])
                end_pos = ph + 1 + next_h.start() if next_h else len(existing_md)
                before  = existing_md[:ph]
                after   = existing_md[end_pos:]
                new_md  = f"{before}{PIPELINE_MARKER_START}\n{table_str}\n{PIPELINE_MARKER_END}\n{after}"
            else:
                # 아예 없으면 STATE.md 끝에 추가
                new_md = existing_md.rstrip("\n") + f"\n\n{PIPELINE_MARKER_START}\n{table_str}\n{PIPELINE_MARKER_END}\n"
        new_md = update_state_md_header(new_md, now_str)
        new_md = update_current_status_section(
            new_md, progress=f"{first_stage} 단계", status_text="진행 중"
        )
    else:
        # 신규 STATE.md 생성 (G-8 템플릿)
        new_md = _build_new_state_md(
            task_title, now_str, args.mode, first_stage,
            rows, table_str, next_action
        )

    save_state_md(task_path, new_md)

    # force 사용 시 의사결정 로그 기재 (§2.17 트리거 #1)
    if args.force:
        updated_md = load_state_md(task_path)
        updated_md = append_decision_log(
            updated_md, now_str,
            "force flag used at init",
            args.note
        )
        save_state_md(task_path, updated_md)

    ok(command,
       task_path=str(task_path),
       task_id=task_id,
       rows_count=len(rows),
       created_at=now_str,
       import_existing=import_mode)


def _build_new_state_md(task_title, now_str, mode, first_stage,
                        rows, table_str, next_action):
    """신규 STATE.md 템플릿 생성 (PLAN §2.11 G-8)."""
    stage_list = list(dict.fromkeys(r["stage"] for r in rows))
    stage_summary = " / ".join(stage_list) if stage_list else "(행 없음)"

    return f"""# STATE: {task_title}

> 최종 갱신: {now_str}

## 현재 상태
- 모드: {mode}
- 단계: {stage_summary}
- 진행: {first_stage} 단계
- 상태: 진행 중

{PIPELINE_MARKER_START}
{table_str}
{PIPELINE_MARKER_END}

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|

## 블로커
없음

## 다음 액션
{next_action}
"""

# ── 2. show ───────────────────────────────────────────────────────────────────

def cmd_show(args):
    """PLAN §2.14 G-11 — 파이프라인 현황판 출력"""
    command = "show"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)
    fmt       = getattr(args, "format", "md") or "md"

    md = load_state_md(task_path)

    if fmt == "json":
        marker_present = False
        if md:
            marker_present = (PIPELINE_MARKER_START in md and PIPELINE_MARKER_END in md)
        ok(command, format="json", marker_present=marker_present, data=state)

    elif fmt == "full":
        if md is None:
            ok(command, format="full", content="(STATE.md 없음)")
            return
        has_markers = (PIPELINE_MARKER_START in md and PIPELINE_MARKER_END in md)
        if not has_markers:
            warning = "<!-- WARNING: pipeline markers missing — table region is unrendered. Run `state init --import-existing` to recover. -->\n"
            ok(command, format="full", content=warning + md)
        else:
            ok(command, format="full", content=md)

    else:  # md (기본)
        has_markers = md and (PIPELINE_MARKER_START in md and PIPELINE_MARKER_END in md)
        if not has_markers:
            # fallback: state.json rows[]로 표 재구성 (§2.14 G-11)
            table = render_pipeline_table(state["rows"])
            header = "# 파이프라인 현황판 (마커 누락 — fallback 출력)\n\n"
            print(json.dumps({
                "ok": True, "command": command, "format": "md",
                "marker_present": False,
                "content": header + table
            }, ensure_ascii=False), file=sys.stderr)
            # stdout에는 정상 출력
            print(json.dumps({
                "ok": True, "command": command, "format": "md",
                "marker_present": False,
                "content": header + table
            }, ensure_ascii=False))
            return

        # 현황판 섹션만 추출
        start_idx = md.find(PIPELINE_MARKER_START) + len(PIPELINE_MARKER_START)
        end_idx   = md.find(PIPELINE_MARKER_END)
        pipeline_section = md[start_idx:end_idx].strip()

        # ## 현재 상태 섹션 추출
        m = re.search(r"(## 현재 상태\n(?:- [^\n]+\n){1,6})", md)
        current_status_section = m.group(1).strip() if m else ""

        content = (current_status_section + "\n\n" + pipeline_section) if current_status_section else pipeline_section
        ok(command, format="md", marker_present=True, content=content)

# ── 3. advance ────────────────────────────────────────────────────────────────

def cmd_advance(args):
    """PLAN §2.1, T-7 — ⬜→🔄 전환"""
    command = "advance"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)
    row_index = find_row_index(state, args.row, command)
    row       = state["rows"][row_index]

    if row["status"] not in ("pending",):
        err(command, "row_not_found",
            message=f"row {args.row} is already {row['status']}, advance only allows pending→in_progress",
            row_id=args.row)

    # 단계 건너뛰기 차단 (PLAN §M-A)
    # PM 경로: 앞 모든 행 검증 (full). 워커 경로: 앞 단계 행만 검증 (prior_stage_only).
    _guard_scope = "prior_stage_only" if getattr(args, "as_worker", False) else "full"
    check_stage_transition_guard(state, row_index, command, force=False,
                                 scope=_guard_scope)

    # CLOSE 진입 게이트 (§2.16 G-13)
    check_close_gate(state, row_index, command)

    # 005 명확화 게이트 — TASK→다음 단계 첫 행 진입 차단 (상태 변경 전)
    _run_clarification_hook(task_path, state, row_index, command,
                            auto_pass=getattr(args, "auto_pass", False),
                            force=getattr(args, "force", False))

    now_str = get_kst_datetime(command)
    row["status"]       = "in_progress"
    row["status_label"] = "🔄"
    row["timestamp"]    = now_str
    if args.note:
        row["note"] = args.note

    state["updated_at"] = now_str
    save_state_json(task_path, state)

    progress = f"{row['stage']} 단계"
    sync_state_md(task_path, state, now_str, command, progress=progress)
    ok(command, row_id=args.row, stage=row["stage"], item=row["item"],
       status="in_progress", timestamp=now_str)

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


def cmd_mark(args):
    """PLAN §2.1, T-7, §2.4, §2.15 G-12, §2.16 G-13 — ⬜/🔄→✅"""
    command = "mark"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)

    # C-2: --owner / --auto-pass 배타 (§2.19)
    if args.auto_pass and args.owner and args.owner != "auto":
        err(command, "owner_flag_conflict")

    # C-3: --as-worker → --worker-stage 필수 (§2.19)
    if args.as_worker and not args.worker_stage:
        err(command, "worker_stage_required")

    # C-4: --force → --note 필수 (§2.17 트리거 #3, #8)
    if args.force and not args.note:
        err(command, "note_required_for_force")

    row_index = find_row_index(state, args.row, command)
    row       = state["rows"][row_index]

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
                    row_id=args.row,
                    stage=row["stage"])

    # 단계 건너뛰기 차단 (PLAN §M-A)
    # PM 경로: 앞 모든 행 검증 (full). 워커 경로: 앞 단계 행만 검증 (prior_stage_only).
    _guard_scope = "prior_stage_only" if args.as_worker else "full"
    check_stage_transition_guard(state, row_index, command, force=args.force,
                                 scope=_guard_scope)

    # CLOSE 진입 게이트 (§2.16 G-13)
    check_close_gate(state, row_index, command,
                     auto_pass=args.auto_pass, force=args.force)

    # 005 명확화 게이트 — TASK→다음 단계 첫 행 진입 차단 (상태 변경 전)
    _run_clarification_hook(task_path, state, row_index, command,
                            auto_pass=args.auto_pass, force=args.force)

    # semi-agentic 모드에서 EXECUTE-equivalent 이전 행은 --auto-pass 거부 (D-DEC-5)
    if args.auto_pass and state.get("mode") == "semi-agentic":
        if row["stage"] in MODE_BOUNDARY_STAGES:
            err(command, "semi_agentic_pre_execute_auto_pass_denied",
                row_id=row["row_id"], stage=row["stage"])

    now_str = get_kst_datetime(command)

    # 017: 다중 Step 진행률 파싱 + 조기 done 가드 (R-1, C-1, C-5)
    _step_str = getattr(args, "step", None)
    _step_pair = _parse_step(_step_str) if _step_str else None
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

    # owner 결정
    if args.auto_pass:
        row["owner"] = "auto"
        if args.note:
            row["note"] = f"agentic auto-pass: {args.note}"
        else:
            row["note"] = "agentic auto-pass"
    elif args.owner:
        row["owner"] = args.owner
        if args.note:
            row["note"] = args.note
    else:
        row["owner"] = "PM"
        if args.note:
            row["note"] = args.note

    state["updated_at"] = now_str

    # CLOSE 단계 마지막 행 → current_status = done (§2.11 G-6)
    # 014 Phase 4: 새 표준 구조의 CLOSE 마지막 행은 "DONE.md 생성"이고, 레거시 구조는
    #   "State Gate"였다. 항목명에 의존하지 않고 "CLOSE 단계의 마지막 행" 여부로 판정한다.
    progress_text = None
    status_text   = None
    is_close_last = (
        row["stage"] == "CLOSE" and
        (row_index == len(state["rows"]) - 1 or
         state["rows"][row_index + 1]["stage"] != "CLOSE")
    )
    # 017: in_progress(N<M)로 남긴 행은 current_status=done 전환에서 제외 — 다중 Step CLOSE 마지막 행 오판 방지
    if is_close_last and row["status"] == "done":
        state["current_status"] = "done"
        status_text = "완료"

    # EXECUTE Step 진행 표기 (§2.11 G-6)
    if args.as_worker and getattr(args, "step", None):
        progress_text = f"Step {args.step} 완료"

    save_state_json(task_path, state)

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
        decision = f"agentic auto-pass at row {args.row}, item={row['item']}"
        reason_text = (args.note or "agentic mode")

    # §2.17 트리거 #3 worker force 로그
    if args.as_worker and args.force:
        requested = args.worker_stage
        actual = row["stage"]
        decision = f"worker_scope_force at row {args.row}, requested_stage={requested}, actual_stage={actual}"
        reason_text = args.note

    sync_state_md(task_path, state, now_str, command,
                  progress=progress_text, status_text=status_text,
                  decision=decision, reason=reason_text)

    ok(command, row_id=args.row, stage=row["stage"], item=row["item"],
       status=row["status"], timestamp=now_str, owner=row["owner"])

# ── 5. block ──────────────────────────────────────────────────────────────────

def cmd_block(args):
    """PLAN §2.17 트리거 #7 — any→❌. current_status → blocked 자동 전환."""
    command = "block"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)
    row_index = find_row_index(state, args.row, command)
    row       = state["rows"][row_index]

    now_str = get_kst_datetime(command)
    row["status"]       = "failed"
    row["status_label"] = "❌"
    row["timestamp"]    = now_str
    row["note"]         = f"block: {args.reason}"

    # current_status → blocked 자동 전환 (§2.11 G-7)
    prev_status = state["current_status"]
    state["current_status"] = "blocked"
    state["updated_at"]     = now_str

    save_state_json(task_path, state)
    sync_state_md(task_path, state, now_str, command, status_text="블로커")

    ok(command, row_id=args.row, stage=row["stage"], item=row["item"],
       status="failed", current_status="blocked", timestamp=now_str)

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
    mode = state.get("mode", "interactive")
    for row in state.get("rows", []):
        if row.get("item") == "사용자 확인" and row.get("status") == "done":
            owner = row.get("owner")
            if owner not in ("user", "auto"):
                violations.append({
                    "code":   "user_confirmation_owner_mismatch",
                    "row_id": row["row_id"],
                    "detail": f"owner={owner}"
                })
            if owner == "auto" and mode == "interactive":
                violations.append({
                    "code":   "auto_pass_in_interactive_mode",
                    "row_id": row["row_id"],
                    "detail": f"interactive mode but owner=auto"
                })
            if owner == "auto" and mode == "semi-agentic":
                # PLAN-equivalent 이전 행에 owner=auto는 위반 (D-DEC-5)
                if row.get("stage") in MODE_BOUNDARY_STAGES:
                    violations.append({
                        "code":   "semi_agentic_pre_execute_auto_pass_denied",
                        "row_id": row["row_id"],
                        "detail": f"semi-agentic mode but owner=auto on stage={row.get('stage')}"
                    })

    # 마커 존재 여부
    md = load_state_md(task_path)
    if md and not (PIPELINE_MARKER_START in md and PIPELINE_MARKER_END in md):
        violations.append({
            "code": "marker_missing", "row_id": None,
            "detail": "STATE.md pipeline markers not found"
        })

    count = len(violations)
    is_ok = count == 0
    print(json.dumps({
        "ok": is_ok, "command": command,
        "violations": violations, "violations_count": count
    }, ensure_ascii=False))
    sys.exit(0 if is_ok else 1)

# ── 7. add-row ────────────────────────────────────────────────────────────────

def cmd_add_row(args):
    """PLAN §2.12 G-9 — 추가작업 행 삽입"""
    command = "add-row"
    task_path = resolve_task_path(args.task_path, command)
    state     = load_state_json(task_path, command)

    # stage enum 검증 (§2.12 G-9 단계 5)
    if args.stage not in STAGE_ENUM:
        err(command, "invalid_stage_enum", value=args.stage)

    # 기존 행 식별
    after_index = find_row_index(state, args.after, command)

    now_str = get_kst_datetime(command)

    new_row = {
        "row_id":       args.after + 1,  # 임시 — 아래서 재정렬
        "stage":        args.stage,
        "item":         args.item,
        "status":       "pending",
        "status_label": "⬜",
        "timestamp":    None,
        "owner":        None,
        "note":         args.note or None,
    }

    # 삽입 (G-9 단계 3)
    state["rows"].insert(after_index + 1, new_row)

    # row_id 재정렬 (G-9 단계 4) — 삽입 후 전체 재번호
    for i, row in enumerate(state["rows"]):
        row["row_id"] = i + 1

    # current_status 자동 전환 (G-9 단계 8, G-7)
    prev_status = state["current_status"]
    if prev_status == "done":
        state["current_status"] = "additional_work"
    elif prev_status == "additional_work_done":
        state["current_status"] = "additional_work"

    state["updated_at"] = now_str
    save_state_json(task_path, state)

    # §2.17 트리거 #5 의사결정 로그
    decision = f"additional row inserted after row {args.after}: stage={args.stage}, item={args.item}, new_row_id={after_index + 2}"
    reason   = args.note or "additional work entry"

    sync_state_md(task_path, state, now_str, command,
                  status_text=("추가작업중" if state["current_status"] == "additional_work" else None),
                  decision=decision, reason=reason)

    ok(command,
       row_id=after_index + 2,
       rows_count=len(state["rows"]),
       current_status=state["current_status"])

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
    save_state_json(task_path, state)

    # G-6 상태 텍스트 매핑
    status_text_map = {
        "in_progress":          "진행 중",
        "done":                 "완료",
        "blocked":              "블로커",
        "additional_work":      "추가작업중",
        "additional_work_done": "추가작업완료",
    }
    status_text = status_text_map.get(to_status)

    # §2.17 트리거 #4
    decision = f"current_status changed: {from_status} → {to_status}"
    reason   = args.note or "(none)"

    sync_state_md(task_path, state, now_str, command,
                  status_text=status_text, decision=decision, reason=reason)

    ok(command, **{"from": from_status, "to": to_status}, timestamp=now_str)

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

    sync_state_md(task_path, state, now_str, command,
                  decision=decision, reason=reason)

    ok(command, rows_passed=passed_ids, stage=stage, timestamp=now_str,
       deprecated=True,
       deprecation_note="gate-pass is deprecated (014 Phase 4): new standard rows have no QA/State Gate rows; use single mark for PM Gate.")

# ── 10. verify ───────────────────────────────────────────────────────────────

# 헌법 §4 "Don't fake it" — TEST-SCENARIO.md mock 코드 패턴 검출
# M-2: 코드 사용 패턴만 정규식 매칭; 단순 "mock" 단어/설명 문구는 제외
_MOCK_CODE_PATTERNS = re.compile(
    r"MagicMock|unittest\.mock|@patch\b|mock\.patch|Mock\(|@mock\."
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
    """코드 패턴 검출 — 위반 라인 번호 목록 반환."""
    violations = []
    for lineno, line in enumerate(lines, start=1):
        if _MOCK_CODE_PATTERNS.search(line):
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

    # 명확화 게이트 검사
    missing = _check_clarification_gate(task_md)
    if missing is None:
        return  # 하위호환: "## 명확화 결과" 섹션 부재 → skip

    if missing:
        err(command, "clarification_gate_unmet", missing=missing)


def _find_task_md(task_path, task_md_arg):
    """TASK.md 경로 결정. --task-md 우선, 없으면 <task_path>/TASK.md. 부재 시 None."""
    p = pathlib.Path(task_md_arg) if task_md_arg else pathlib.Path(task_path) / "TASK.md"
    return p if p.exists() else None


def _parse_clarification_table(lines):
    """TASK.md "## 명확화 결과" 섹션의 표를 파싱.

    반환: {element_label: confirmed_value_cell_text} 딕셔너리.
    섹션/표 부재 시 None 반환 (호출자가 graceful skip).
    "확정값" 열을 헤더에서 식별; 없으면 라벨 다음(2번째) 셀을 확정값으로 폴백.
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
    confirmed_col_idx = None
    for idx, line in enumerate(section_lines):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:]+\|", stripped):
            continue  # 구분선 행 스킵
        cells = [c.strip() for c in stripped.split("|")]
        cells = cells[1:-1] if len(cells) > 2 else cells
        if header_cells is None:
            header_cells = cells
            header_line_idx = idx
            # "확정값" 열 인덱스 식별
            for ci, cell in enumerate(cells):
                if "확정값" in cell:
                    confirmed_col_idx = ci
                    break
            # 미발견 시 폴백: 라벨 다음(인덱스 1) 셀
            if confirmed_col_idx is None and len(cells) >= 2:
                confirmed_col_idx = 1
            break

    if header_cells is None or confirmed_col_idx is None:
        return None  # 표 부재

    # 4) 데이터 행 파싱 — 첫 셀이 4요소 키워드를 포함하면 {라벨: 확정값셀}
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
    """4요소 잠금 검증. 반환: missing[] (빈 리스트면 PASS).

    None 반환 = 섹션/표 부재 (호출자가 하위호환 정책 적용 — graceful skip).
    각 요소: 확정값 셀이 공란/"TBD"/"-"이면 미충족. "N/A: <사유>"는 충족.
    """
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


def cmd_verify(args):
    """PLAN 013 §verify — TEST-SCENARIO.md mock 코드 패턴 + 증거 누락 검사.
    016 확장: --red-check(RED 증거 게이트) / --fix-mode(테스트 불변성).
    005 확장: --clarification-check(TASK 4요소 잠금 게이트).
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
    task_md_arg = getattr(args, "task_md", None)

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
                "reason": "no '## 명확화 결과' section (backward-compat skip)",
            }, ensure_ascii=False))
            sys.exit(0)
        if missing:
            err(command, "clarification_gate_unmet", missing=missing)
        print(json.dumps({
            "ok": True, "command": command,
            "clarification_check": "pass",
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


# ─────────────────────────────────────────────────────────────────────────────
# argparse 설정 (PLAN §2.19 E-2 매트릭스 그대로)
# ─────────────────────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="state-tool",
        description="OPAL 파이프라인 현황판 JSON SSOT 관리 CLI (PLAN §2.19 E-2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
서브 명령 (9종):
  init        state.json + STATE.md 생성
  show        현황판 출력 (md/json/full)
  advance     ⬜→🔄 전환
  mark        ⬜/🔄→✅ 전환 (--done 필수)
  block       any→❌ 전환 + current_status=blocked
  validate    정합성 검증 → violations[]
  add-row     추가작업 행 삽입
  status      current_status 명시 전환
  gate-pass   [DEPRECATED] Gate 4행 일괄 ✅ 처리 (레거시 state.json 전용)

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
                        choices=["opp","opd","opds","opdw","opwt","opgc","oppd","opsdd"])
    p_init.add_argument("--mode", required=True,
                        choices=["interactive","semi-agentic","agentic"])
    p_init.add_argument("--task-title")
    p_init.add_argument("--next-action")
    rows_group = p_init.add_mutually_exclusive_group()  # C-1
    rows_group.add_argument("--rows-spec", metavar="<inline-json>")
    rows_group.add_argument("--rows-from", metavar="<path>")
    p_init.add_argument("--rows-acts", metavar="<inline-json>",
                        help="opsdd ACT 동적 주입 (시그니처만, 미구현 — R-13)")
    p_init.add_argument("--force", action="store_true")
    p_init.add_argument("--note")
    p_init.add_argument("--import-existing", action="store_true", dest="import_existing")
    p_init.set_defaults(func=cmd_init)

    # ── show ──
    p_show = sub.add_parser("show", help="현황판 출력 (§2.14 G-11)")
    p_show.add_argument("task_path", metavar="<task-path>")
    p_show.add_argument("--format", dest="format", choices=["md","json","full"], default="md")
    p_show.set_defaults(func=cmd_show)

    # ── advance ──
    p_adv = sub.add_parser("advance", help="⬜→🔄 전환 (T-7)")
    p_adv.add_argument("task_path", metavar="<task-path>")
    p_adv.add_argument("--row", type=int, required=True)
    p_adv.add_argument("--note")
    p_adv.set_defaults(func=cmd_advance)

    # ── mark ──
    p_mark = sub.add_parser("mark", help="⬜/🔄→✅ 전환 (T-7, §2.4, §2.15)")
    p_mark.add_argument("task_path", metavar="<task-path>")
    p_mark.add_argument("--row", type=int, required=True)
    p_mark.add_argument("--done", action="store_true", required=True)
    p_mark.add_argument("--note")
    p_mark.add_argument("--as-worker", action="store_true", dest="as_worker")
    p_mark.add_argument("--worker-stage",
                        choices=STAGE_ENUM,
                        dest="worker_stage")
    p_mark.add_argument("--step", metavar="N/M")
    owner_group = p_mark.add_mutually_exclusive_group()  # C-2
    owner_group.add_argument("--owner", choices=["PM","worker","user","auto"])
    owner_group.add_argument("--auto-pass", action="store_true", dest="auto_pass")
    p_mark.add_argument("--force", action="store_true")
    p_mark.set_defaults(func=cmd_mark)

    # ── block ──
    p_blk = sub.add_parser("block", help="any→❌ 전환 + current_status=blocked (§2.17 트리거 #7)")
    p_blk.add_argument("task_path", metavar="<task-path>")
    p_blk.add_argument("--row", type=int, required=True)
    p_blk.add_argument("--reason", required=True)
    p_blk.set_defaults(func=cmd_block)

    # ── validate ──
    p_val = sub.add_parser("validate", help="정합성 검증 → violations[] (§2.6, F-10)")
    p_val.add_argument("task_path", metavar="<task-path>")
    p_val.set_defaults(func=cmd_validate)

    # ── add-row ──
    p_add = sub.add_parser("add-row", help="추가작업 행 삽입 (§2.12 G-9)")
    p_add.add_argument("task_path", metavar="<task-path>")
    p_add.add_argument("--after", type=int, required=True)
    p_add.add_argument("--stage", required=True, choices=STAGE_ENUM)
    p_add.add_argument("--item", required=True)
    p_add.add_argument("--note")
    p_add.set_defaults(func=cmd_add_row)

    # ── status ──
    p_sts = sub.add_parser("status", help="current_status 명시 전환 (§2.11 G-7)")
    p_sts.add_argument("task_path", metavar="<task-path>")
    p_sts.add_argument("--set", dest="set", required=True,
                       choices=["in_progress","done","blocked",
                                "additional_work","additional_work_done"])
    p_sts.add_argument("--note")
    p_sts.set_defaults(func=cmd_status)

    # ── gate-pass ──
    p_gp = sub.add_parser("gate-pass",
                          help="[DEPRECATED] Gate 4행 일괄 ✅ 처리 — 레거시 state.json 전용 (§2.13 G-10, 014 Phase 4)")
    p_gp.add_argument("task_path", metavar="<task-path>")
    p_gp.add_argument("--start", type=int, required=True)
    p_gp.add_argument("--note")
    p_gp.set_defaults(func=cmd_gate_pass)

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
    p_vfy.set_defaults(func=cmd_verify)

    return parser

# ─────────────────────────────────────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = build_parser()
    args   = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
