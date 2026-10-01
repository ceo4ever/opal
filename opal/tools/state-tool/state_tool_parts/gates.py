# -*- coding: utf-8 -*-
"""
@header {
  "module": "state_tool_parts.gates",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "state-tool 검증 게이트 — plan 계약·명확화·근거·RED·설계 게이트, verify·event-verify",
  "exports": [
    "cmd_verify",
    "cmd_event_verify",
    "cmd_design_gate_start",
    "cmd_design_gate_combine",
    "_previous_gaps_for",
    "_gap_id",
    "_check_plan_contract"
  ]
}
"""

import fnmatch
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

from . import base
from .codes import (
    STATUS_LABEL_MAP,
    can_auto_approve_user_confirmation,
)
from .base import (
    _COMPLETE_STATUSES,
    _derive_next_action,
    err,
    load_state_json,
    ok,
    resolve_task_path,
)
from .run_log import (
    _build_gate_event,
    _build_pm_activity_event,
    _run_log_block,
    _run_log_completeness_check,
    build_state_changed_event,
    run_log_commit,
)
from .journal import (
    build_todo_mirror,
    resolve_owner_placeholder,
    sync_state_md,
    task_root,
)
from .guards import (
    _is_safe_artifact_token,
    check_stage_transition_guard,
)

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
            or task_root(str(pathlib.Path(__file__).resolve().parent.parent / "state_tool.py")))
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
_TEST_TOOL_PY = pathlib.Path(__file__).resolve().parent.parent.parent / "test-tool" / "test_tool.py"
# 168 W-1 — opd2 스킬 루트의 lifecycle.py. state_tool.py 위치에서 두 단계 상위
# (parents[2])가 tools/의 부모이며, 그 밑 skills/opal-pilot-dev2가 형제 스킬 디렉터리다.
# 소스(opal/tools/state-tool → opal/skills/opal-pilot-dev2)·설치본
# (~/.opal/tools/state-tool → ~/.opal/skills/opal-pilot-dev2) 모두 같은 상대 구조다.
_OPD2_LIFECYCLE_PY = (
    pathlib.Path(__file__).resolve().parents[3]
    / "skills" / "opal-pilot-dev2" / "scripts" / "lifecycle.py"
)
# 168 W-1 — opd2 기계 게이트가 걸리는 task_steps 키 집합(PLAN Decisions "C-1을
# opd2 전용 mark 가드로 확장"). 다른 Pilot도 같은 이름의 키(예: execute.implement,
# plan.plan_md)를 쓰므로 apply_opd2_gate_mark_guard()는 이 키 집합만으로 판정하지
# 않고 반드시 skill == "opd2"인 태스크에만 적용한다.
OPD2_GATE_ROW_KEYS = (
    "task.intent_md",
    "design.spec_md",
    "plan.plan_md",
    "execute.implement",
    "verify.verifier_evidence",
    "verify.review",
)
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


def apply_opd2_gate_mark_guard(task_path, row, command, *, target_done):
    """168 W-1 mark 가드 — opd2 태스크의 opd2 게이트 행(`OPD2_GATE_ROW_KEYS`)을
    미완에서 완료로 바꿀 때 형제 스킬 `opal-pilot-dev2/scripts/lifecycle.py verify-mark`를
    호출해 opd2 자체 기계 게이트(아티팩트 결합 해시·범위·evidence·역할 분리·RED 증거 등,
    D-11:173-277)가 통과했는지 확인한다.

    `apply_scenario_gate_mark_guard()`와 완전히 동일한 시그니처·호출 규약이며 row 해석
    직후·상태 변경 이전에 실행되므로 거부 시 state.json은 바뀌지 않는다. `--force`·
    `--auto-pass`·`--as-worker`는 이 함수를 우회하지 못한다(호출자가 어떤 플래그도 넘기지
    않는다). 이미 완료된 행, 다른 key, 부분 진행(`--step N/M`, N<M)에는 적용하지 않는다.

    다른 Pilot도 `execute.implement`·`plan.plan_md` 같은 동일한 키 이름을 쓰므로,
    `state.json`을 다시 읽어 `skill == "opd2"`인 태스크에만 적용하고 그 외 Pilot의
    `cmd_mark` 분기·행 구성·전이 동작은 건드리지 않는다(PLAN C-1 확장 범위).
    """
    if not target_done or row.get("key") not in OPD2_GATE_ROW_KEYS:
        return
    if row.get("status") in _COMPLETE_STATUSES:
        return
    task_dir = pathlib.Path(task_path)
    state = load_state_json(task_dir, command)
    if state.get("skill") != "opd2":
        return
    reason = None
    verify_error = None
    try:
        completed = subprocess.run(
            [sys.executable, str(_OPD2_LIFECYCLE_PY), "verify-mark",
             "--task", str(task_dir), "--key", row.get("key")],
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
    err(command, "opd2_gate_record_required",
        row_id=row.get("row_id"), key=row.get("key"), reason=reason,
        detail={"reason": reason}, **extra,
        required_action=(
            f"{_OPD2_LIFECYCLE_PY} verify-mark --task {task_dir} --key {row.get('key')}가 "
            "통과하도록 opd2 Builder/Verifier/Reviewer 게이트 판정을 다시 확인한 뒤 "
            f"state mark <task-path> --task-step {row.get('key')} --done을 재실행하세요"))


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


_PREVIOUS_GAPS_SKIP_VERDICTS = ("deterministic_fail", "input_error", "superseded")


def _gap_id(text):
    """gaps 항목 id — 첫 번째 `: ` 앞부분 전체, `: `가 없으면 전체 문자열 (evaluator 계약 정의)."""
    return text.split(": ", 1)[0]


def _gap_strings(part):
    """부분 객체(design 또는 scenario)의 gaps 중 문자열 항목만 순서대로 반환한다."""
    gaps = part.get("gaps") if isinstance(part, dict) else None
    if not isinstance(gaps, list):
        return []
    return [g for g in gaps if isinstance(g, str)]


def _previous_gaps_for(task_path, state):
    """이전 회차 지적 조립 — (previous_gaps, previous_gaps_by_scope, previous_gaps_iteration).

    design_gate.history를 최신부터 역순 순회해 verdict가 deterministic_fail·input_error·
    superseded가 아닌 첫 회차 k의 run/design-gate-i{k}.json을 읽는다. 파일이 없거나 읽을 수
    없으면 더 이전 회차로 계속 가고, 읽었다면 gaps가 비어 있어도 거기서 멈춘다. 읽은 파일이
    없으면 ([], 빈 scope 둘, None)이다. 상태·파일 외 입력이 없는 순수 함수다.
    """
    dg = state.get("design_gate") if isinstance(state.get("design_gate"), dict) else {}
    for item in reversed(dg.get("history") or []):
        if not isinstance(item, dict) or item.get("verdict") in _PREVIOUS_GAPS_SKIP_VERDICTS:
            continue
        k = item.get("iteration")
        if isinstance(k, bool) or not isinstance(k, int):
            continue
        path = pathlib.Path(task_path) / "run" / f"design-gate-i{k}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        by_scope = {"design": _gap_strings(data.get("design")),
                    "scenario": _gap_strings(data.get("scenario"))}
        return by_scope["design"] + by_scope["scenario"], by_scope, k
    return [], {"design": [], "scenario": []}, None


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

    now_str = base.get_kst_datetime(command)
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
    _prev, _prev_by_scope, _prev_iteration = _previous_gaps_for(task_path, state)
    ok(command, status="evaluating", iteration=args.iteration,
       gate_id=f"design-gate-i{args.iteration}", bundle_hash=bundle, refinement=refinement,
       previous_gaps=_prev, previous_gaps_by_scope=_prev_by_scope,
       previous_gaps_iteration=_prev_iteration,
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

    now_str = base.get_kst_datetime(command)
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


# ── design-gate combine (172 D-5) ─────────────────────────────────────────────

def _combine_load_partial(command, label, path):
    try:
        data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as e:
        err(command, "design_gate_partial_invalid", detail=f"cannot load {label} result: {e}")
    if not isinstance(data, dict):
        err(command, "design_gate_partial_invalid", detail=f"{label} result must be a JSON object")
    return data


def _combine_check_partial(command, label, result, prev_ids):
    """③ 부분 결과 형식 검사 — 위반은 design_gate_partial_invalid(detail에 사유)."""
    def bad(detail):
        err(command, "design_gate_partial_invalid", detail=f"{label}: {detail}")

    if result.get("scope") != label:
        bad(f"scope must be {label!r}, got {result.get('scope')!r}")
    part = result.get(label)
    if not isinstance(part, dict):
        bad(f"missing {label} object")
    if label == "design":
        axes = part.get("axes")
        if not isinstance(axes, dict):
            bad("design.axes must be an object")
        missing = [k for k in DESIGN_GATE_AXES if k not in axes]
        if missing:
            bad(f"design.axes missing {missing}")
    else:
        scores = part.get("scores")
        if not isinstance(scores, dict):
            bad("scenario.scores must be an object")
        for k in DESIGN_GATE_SCENARIO_KEYS:
            if k not in scores:
                bad(f"scenario.scores missing {k}")
            if isinstance(scores[k], bool) or not isinstance(scores[k], (int, float)):
                bad(f"scenario.scores.{k} must be a number")
    gaps = part.get("gaps", [])
    if not isinstance(gaps, list) or any(not isinstance(g, str) for g in gaps):
        bad(f"{label}.gaps must be a list of strings")
    resolved = result.get("resolved_gaps", [])
    if not isinstance(resolved, list):
        bad("resolved_gaps must be a list")
    ids = set()
    for item in resolved:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            bad("resolved_gaps item must be an object with string id")
        if item.get("status") not in ("resolved", "unresolved"):
            bad(f"resolved_gaps status must be resolved|unresolved ({item.get('id')!r}: "
                f"{item.get('status')!r})")
        ids.add(item["id"])
    if ids != set(prev_ids):
        bad(f"resolved_gaps id set mismatch: expected {sorted(prev_ids)}, got {sorted(ids)}")
    if not isinstance(result.get("advisories", []), list):
        bad("advisories must be a list")


def cmd_design_gate_combine(args):
    """설계·시나리오 부분 결과를 단일 design-rubric 결과 형식 파일 하나로 결합한다.

    state.json·run-log·락을 건드리지 않는다(읽기 전용). 출력은 임시 파일에 쓴 뒤 os.replace.
    """
    command = "design-gate combine"
    task_path = resolve_task_path(args.task_path, command)
    state = load_state_json(task_path, command)
    _require_pm_design_path(state, command)
    dg_view = state.get("design_gate") if isinstance(state.get("design_gate"), dict) else {}
    attempt = dg_view.get("current_attempt") or {}
    if dg_view.get("status") != "evaluating":                                  # ①
        err(command, "design_gate_iteration_invalid", iteration=args.iteration,
            expected=None, detail="no open design gate attempt — run design-gate start first")
    if args.iteration != attempt.get("iteration"):
        err(command, "design_gate_iteration_invalid", iteration=args.iteration,
            expected=attempt.get("iteration"))
    bundle = attempt.get("bundle_hash")
    partial = {"design": _combine_load_partial(command, "design", args.design_result),
               "scenario": _combine_load_partial(command, "scenario", args.scenario_result)}
    for label in ("design", "scenario"):                                       # ②
        res = partial[label]
        if res.get("input_bundle_hash") != bundle or res.get("iteration") != args.iteration:
            err(command, "design_gate_result_stale", bundle_hash=bundle,
                iteration=args.iteration, result_input_bundle_hash=res.get("input_bundle_hash"),
                result_iteration=res.get("iteration"), scope=label)
    _prev, prev_by_scope, _prev_iteration = _previous_gaps_for(task_path, state)
    for label in ("design", "scenario"):                                       # ③
        _combine_check_partial(command, label, partial[label],
                               [_gap_id(g) for g in prev_by_scope[label]])

    design, scenario = partial["design"]["design"], partial["scenario"]["scenario"]
    axes = design["axes"]
    scores = scenario["scores"]
    values = [float(scores[k]) for k in DESIGN_GATE_SCENARIO_KEYS]
    average = sum(values) / len(values)
    design_ok = all(str(axes.get(k)).upper() == "PASS" for k in DESIGN_GATE_AXES)
    scenario_ok = all(v >= 1 for v in values) and average >= 1.5
    if design_ok and scenario_ok:
        verdict, rewrite_target = "pass", None
    else:
        verdict = "fail"
        rewrite_target = "both" if (not design_ok and not scenario_ok) else (
            "plan" if not design_ok else "scenario")
    resolved_gaps = (list(partial["design"].get("resolved_gaps", []))
                     + list(partial["scenario"].get("resolved_gaps", [])))
    advisories = [] if attempt.get("refinement") is True else list(
        partial["scenario"].get("advisories", []))
    combined = {
        "input_bundle_hash": bundle,
        "iteration": args.iteration,
        "design": {"axes": axes, "gaps": list(design.get("gaps", []))},
        "scenario": {"scores": scores, "average": round(average, 3),
                     "gaps": list(scenario.get("gaps", []))},
        "resolved_gaps": resolved_gaps,
        "advisories": advisories,
        "verdict": verdict,
        "rewrite_target": rewrite_target,
    }
    out_path = pathlib.Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=out_path.name + ".", suffix=".tmp", dir=str(out_path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(combined, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_name, out_path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    ok(command, output_path=str(out_path), verdict=verdict, rewrite_target=rewrite_target,
       resolved_gaps_count=len(resolved_gaps))


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
    now_str = base.get_kst_datetime(command)
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

    now_str = base.get_kst_datetime(command)
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
        try:
            dgc_state = json.loads(state_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            print(json.dumps({
                "ok": True, "command": command,
                "design_gate_check": "skipped",
                "reason": "state.json not found",
            }, ensure_ascii=False))
            sys.exit(0)
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
    loader = pathlib.Path(__file__).resolve().parent.parent.parent / "event-loader" / "event_loader.py"
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
        ("--agent", getattr(args, "agent", None)),
        ("--role", getattr(args, "role", None)),
        ("--role-doc", getattr(args, "role_doc", None)),
        ("--dispatch-id", getattr(args, "dispatch_id", None)),
        ("--contract-version", getattr(args, "contract_version", None)),
    ):
        if value is not None:
            command.extend((option, value))
    if getattr(args, "require_default_manifest", False):
        command.append("--require-default-manifest")

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
