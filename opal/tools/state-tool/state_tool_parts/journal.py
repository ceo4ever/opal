# -*- coding: utf-8 -*-
"""
@header {
  "module": "state_tool_parts.journal",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "state-tool 저널 — STATE.md 생성·동기화, 행 탐색, 모드 판정, todo 미러, 히스토리·메모리 연동",
  "exports": [
    "sync_state_md",
    "task_root",
    "build_todo_mirror",
    "link_memory_history"
  ]
}
"""

import json
import os
import pathlib
import re
import subprocess
import sys

from .codes import (
    can_auto_approve_user_confirmation,
)
from .base import (
    err,
)


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
_MEMORY_TOOL = pathlib.Path(__file__).resolve().parent.parent.parent / "memory-tool" / "memory_tool.py"


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
