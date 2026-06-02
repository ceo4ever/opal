"""
@header {
  "module": "state_tool",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "OPAL 파이프라인 현황판 JSON SSOT 관리 CLI — 9개 서브 명령(init/show/advance/mark/block/validate/add-row/status/gate-pass) + 3-way 모드(interactive/semi-agentic/agentic) 지원",
  "exports": [
    "cmd_init", "cmd_show", "cmd_advance", "cmd_mark",
    "cmd_block", "cmd_validate", "cmd_add_row", "cmd_status", "cmd_gate_pass"
  ]
}
"""

# PLAN §2.1 구현 명세 — TASK T-11: 표준 라이브러리만 import
import argparse
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
STANDARD_ITEMS = {
    "작업", "QA Gate", "State Gate", "PM Gate", "사용자 확인",
}
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

    # CLOSE 진입 게이트 (§2.16 G-13)
    check_close_gate(state, row_index, command)

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

    # CLOSE 진입 게이트 (§2.16 G-13)
    check_close_gate(state, row_index, command,
                     auto_pass=args.auto_pass, force=args.force)

    # semi-agentic 모드에서 EXECUTE-equivalent 이전 행은 --auto-pass 거부 (D-DEC-5)
    if args.auto_pass and state.get("mode") == "semi-agentic":
        if row["stage"] in MODE_BOUNDARY_STAGES:
            err(command, "semi_agentic_pre_execute_auto_pass_denied",
                row_id=row["row_id"], stage=row["stage"])

    now_str = get_kst_datetime(command)
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

    # CLOSE 마지막 State Gate → current_status = done (§2.11 G-6)
    progress_text = None
    status_text   = None
    is_close_last = (
        row["stage"] == "CLOSE" and
        row.get("item") == "State Gate" and
        (row_index == len(state["rows"]) - 1 or
         state["rows"][row_index + 1]["stage"] != "CLOSE")
    )
    if is_close_last:
        state["current_status"] = "done"
        status_text = "완료"

    # EXECUTE Step 진행 표기 (§2.11 G-6)
    if args.as_worker and getattr(args, "step", None):
        progress_text = f"Step {args.step} 완료"

    save_state_json(task_path, state)

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
       status="done", timestamp=now_str, owner=row["owner"])

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
    """PLAN §2.13 G-10 — 4행 Gate 일괄 처리"""
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

    ok(command, rows_passed=passed_ids, stage=stage, timestamp=now_str)

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
  gate-pass   Gate 4행 일괄 ✅ 처리

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
    p_gp = sub.add_parser("gate-pass", help="Gate 4행 일괄 ✅ 처리 (§2.13 G-10)")
    p_gp.add_argument("task_path", metavar="<task-path>")
    p_gp.add_argument("--start", type=int, required=True)
    p_gp.add_argument("--note")
    p_gp.set_defaults(func=cmd_gate_pass)

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
