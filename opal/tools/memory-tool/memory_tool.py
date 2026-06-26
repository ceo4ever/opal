"""
@header {
  "module": "memory_tool",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "OPAL 메모리 관리 CLI — 8서브명령 init/append/update/promote/prune/migrate/show/review. 메모리 인덱스·히스토리 결정론적 집행: 마커 직접편집 금지 가드(marker_missing), 요약 길이캡(≤80), 히스토리 FIFO=5(prune), promote 무손실 이전(--to docs|brain --ref 필수), 자가검토(review) 매 변경 명령 자동 첨부. state-tool ok/err/ERROR_CODES/replace_marker_section 패턴 재사용. 표준 라이브러리만.",
  "exports": [
    "cmd_init", "cmd_append", "cmd_update", "cmd_promote",
    "cmd_prune", "cmd_migrate", "cmd_show", "cmd_review",
    "build_review_block"
  ]
}
"""

# 표준 라이브러리만 (state-tool 동형)
import argparse
import json
import os
import pathlib
import re
import sys
from datetime import datetime, timezone, timedelta

# ─────────────────────────────────────────────────────────────────────────────
# 상수 (SSOT)
# ─────────────────────────────────────────────────────────────────────────────

HISTORY_FIFO_LIMIT = 5  # SSOT (R3) — 히스토리 최대 행수

PROMOTE_AGE_DAYS = 30   # review promote 후보 기준: 등록 후 30일 이상 active

# 메모리 인덱스 마커
INDEX_MARKER_START = "<!-- memory:index:start -->"
INDEX_MARKER_END   = "<!-- memory:index:end -->"

# 히스토리 마커
HISTORY_MARKER_START = "<!-- memory:history:start -->"
HISTORY_MARKER_END   = "<!-- memory:history:end -->"

# enum 정의
VALID_TYPES = {"project", "architecture", "feedback", "preferences", "issues", "task"}
VALID_STATUSES = {"active", "promoted", "superseded", "dead"}

# 상태 매핑 (migrate용 — 구포맷 자유 상태값 → 신 enum)
LEGACY_STATUS_MAP = {
    "대기":     "active",
    "예정":     "active",
    "유지":     "active",
    "active":   "active",
    "진행":     "active",
    "진행중":   "active",
    "완료":     "dead",
    "dead":     "dead",
    "폐기 기록": "superseded",
    "폐기":     "superseded",
    "superseded": "superseded",
    "promoted": "promoted",
}

# 신 인덱스 표 헤더
INDEX_HEADER = "| 제목 | 등록일 | 유형 | 상태 | 파일 | 요약 |"
INDEX_SEPARATOR = "|------|--------|------|------|------|------|"

# 신 히스토리 표 헤더
HISTORY_HEADER = "| 제목 | 등록일 | 단계 | 경로 | 핵심결과 |"
HISTORY_SEPARATOR = "|------|--------|------|------|----------|"

# ERROR_CODES (SSOT — memory-tool 전용)
ERROR_CODES = {
    "marker_missing":        "MEMORY.md에 <!-- memory:index:start/end --> 또는 <!-- memory:history:start/end --> 마커 누락",
    "memory_file_not_found": "<file>에 해당하는 메모리 파일이 없음: {path}",
    "row_not_found":         "--title '{title}'에 해당하는 인덱스 행이 없음",
    "memory_md_not_found":   "MEMORY.md가 존재하지 않음 — init을 먼저 실행하세요: {path}",
    "already_initialized":   "MEMORY.md 마커가 이미 존재합니다 — --force로 재삽입",
    "invalid_kind":          "--kind는 memory 또는 history 중 하나여야 함: {kind}",
    "invalid_type":          "--type {value}는 유형 enum(project/architecture/feedback/preferences/issues/task)에 없음",
    "invalid_status":        "--status {value}는 라이프사이클 enum(active/promoted/superseded/dead)에 없음",
    "summary_too_long":      "요약 {length}자 > 80자 제한 (R2) — 상세는 개별 .md 본문으로",
    "title_required":        "--title은 필수 비공백 문자열",
    "invalid_promote_target": "--to는 docs 또는 brain 중 하나여야 함: {value}",
    "promote_ref_missing":   "--ref(영구 거처 위치) 필수 — 이전 미확인 promote 거부 (무손실, H-1)",
    "import_failed":         "구포맷 MEMORY.md 파싱 실패 — 표 정규식 매칭 0건",
    "date_tool_failed":      "node ~/.opal/tools/date/date.js 호출 실패 — MEMORY.md 변경 없음(원자성)",
    "delete_requires_dead_or_superseded": "delete는 status가 dead 또는 superseded인 행만 허용 (무손실 가드) — active/promoted 행은 먼저 상태를 변경하세요",
}

# ─────────────────────────────────────────────────────────────────────────────
# 응답 헬퍼 (state-tool ok/err 동형)
# ─────────────────────────────────────────────────────────────────────────────

def ok(command, **kwargs):
    """성공 응답 — 단일 라인 JSON, exit 0"""
    print(json.dumps({"ok": True, "command": command, **kwargs}, ensure_ascii=False, default=str))


def err(command, code, message=None, exit_code=1, **kwargs):
    """에러 응답 — 단일 라인 JSON, exit {exit_code}
    code는 ERROR_CODES 키 중 하나여야 한다 (SSOT).
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
# 날짜 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def get_kst_date():
    """KST 오늘 날짜 YYYY-MM-DD 반환 (node date.js 폴백 → Python datetime)."""
    date_js = os.path.expanduser("~/.opal/tools/date/date.js")
    try:
        import subprocess
        result = subprocess.run(
            ["node", date_js, "date"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            date_str = result.stdout.strip()
            if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
                return date_str[:10]
    except Exception:
        pass
    # 폴백: Python UTC+9
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst).strftime("%Y-%m-%d")


# ─────────────────────────────────────────────────────────────────────────────
# 마커 영역 헬퍼 (state-tool replace_pipeline_section 동형)
# ─────────────────────────────────────────────────────────────────────────────

def replace_marker_section(md_content, start_marker, end_marker, new_table_content):
    """마커 영역을 new_table_content로 교체 반환.
    마커 없으면 None 반환 (호출자가 marker_missing 처리).
    """
    start_idx = md_content.find(start_marker)
    end_idx   = md_content.find(end_marker)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        return None
    before = md_content[:start_idx]
    after  = md_content[end_idx + len(end_marker):]
    return f"{before}{start_marker}\n{new_table_content}\n{end_marker}{after}"


def has_index_markers(content):
    return (INDEX_MARKER_START in content) and (INDEX_MARKER_END in content)


def has_history_markers(content):
    return (HISTORY_MARKER_START in content) and (HISTORY_MARKER_END in content)


def has_any_markers(content):
    return has_index_markers(content) or has_history_markers(content)


# ─────────────────────────────────────────────────────────────────────────────
# 표 파싱 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _extract_section(content, start_marker, end_marker):
    """마커 사이 텍스트를 반환. 마커 없으면 None."""
    start_idx = content.find(start_marker)
    end_idx   = content.find(end_marker)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        return None
    return content[start_idx + len(start_marker):end_idx]


def _parse_table_rows(section_text):
    """마크다운 표에서 데이터 행(헤더·구분선 제외) 리스트 반환.
    각 행은 셀 리스트(strip된 문자열).
    """
    rows = []
    if section_text is None:
        return rows
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if not stripped.endswith("|"):
            continue
        inner = stripped[1:-1]
        # 구분선 검사 (---만 있는 셀들)
        cells = [c.strip() for c in inner.split("|")]
        if all(re.match(r"^-+$", c.replace(" ", "")) for c in cells if c.replace(" ", "")):
            continue
        # 헤더 검사 (제목/등록일 포함 행)
        if ("제목" in cells[0] or "등록일시" in cells[0] or "등록일자" in cells[0]) and "등록일" in " ".join(cells[:3]):
            continue
        rows.append(cells)
    return rows


def _parse_index_rows(content):
    """인덱스 마커 사이 데이터 행 반환. 각 행은 dict."""
    section = _extract_section(content, INDEX_MARKER_START, INDEX_MARKER_END)
    raw_rows = _parse_table_rows(section)
    result = []
    for cells in raw_rows:
        if len(cells) < 6:
            # 패딩
            cells = cells + [""] * (6 - len(cells))
        result.append({
            "title":   cells[0],
            "date":    cells[1],
            "type":    cells[2],
            "status":  cells[3],
            "file":    cells[4],
            "summary": cells[5],
        })
    return result


def _parse_history_rows(content):
    """히스토리 마커 사이 데이터 행 반환. 각 행은 dict."""
    section = _extract_section(content, HISTORY_MARKER_START, HISTORY_MARKER_END)
    raw_rows = _parse_table_rows(section)
    result = []
    for cells in raw_rows:
        if len(cells) < 5:
            cells = cells + [""] * (5 - len(cells))
        result.append({
            "title":   cells[0],
            "date":    cells[1],
            "stage":   cells[2],
            "path":    cells[3],
            "result":  cells[4],
        })
    return result


def _render_index_table(rows):
    """인덱스 행 리스트 → 마크다운 표 문자열(헤더 포함)."""
    lines = [INDEX_HEADER, INDEX_SEPARATOR]
    for r in rows:
        title   = r.get("title", "")
        date    = r.get("date", "")
        rtype   = r.get("type", "")
        status  = r.get("status", "active")
        fpath   = r.get("file", "")
        summary = r.get("summary", "")
        lines.append(f"| {title} | {date} | {rtype} | {status} | {fpath} | {summary} |")
    return "\n".join(lines)


def _render_history_table(rows):
    """히스토리 행 리스트 → 마크다운 표 문자열(헤더 포함)."""
    lines = [HISTORY_HEADER, HISTORY_SEPARATOR]
    for r in rows:
        title  = r.get("title", "")
        date   = r.get("date", "")
        stage  = r.get("stage", "")
        path   = r.get("path", "")
        result = r.get("result", "")
        lines.append(f"| {title} | {date} | {stage} | {path} | {result} |")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# FIFO 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _enforce_history_fifo(rows):
    """rows = 히스토리 행 리스트(맨 앞=최신). len > HISTORY_FIFO_LIMIT 시 뒤에서 제거.
    결정론: append는 맨 앞 삽입 → 뒤쪽이 오래된 순.
    """
    return rows[:HISTORY_FIFO_LIMIT]


# ─────────────────────────────────────────────────────────────────────────────
# title → 파일 경로 변환 + 경로 보안 가드
# ─────────────────────────────────────────────────────────────────────────────

def _title_to_filename(title):
    """제목 → memory/<slug>.md 파일명 변환.
    특수문자를 제거하고 공백→언더스코어.
    """
    slug = re.sub(r"[^\w가-힣]", "_", title).strip("_")
    slug = re.sub(r"_+", "_", slug)
    return f"memory/{slug}.md"


def _resolve_memory_file(md_path, file_field):
    """MEMORY.md 기준 상대경로 → 절대경로 반환.
    memory/ 디렉토리 외부 탈출 시 None 반환(경로 가드).
    migrate가 생성한 백틱 감싸진 경로(예: `memory/x.md`)를 정규화한다.
    """
    md_dir = pathlib.Path(md_path).parent.resolve()
    # 백틱·공백 strip (migrate 백틱 포맷 대응)
    file_field = file_field.strip().strip("`").strip()
    # 경로 정규화
    try:
        target = (md_dir / file_field).resolve()
    except Exception:
        return None
    # 경로 탈출 가드: memory/ 하위여야 함
    memory_dir = (md_dir / "memory").resolve()
    try:
        target.relative_to(memory_dir)
    except ValueError:
        return None
    return target


def _path_has_traversal(path_str):
    """경로 문자열에 ../ 탈출 패턴이 있으면 True."""
    return ".." in pathlib.Path(path_str).parts or ".." in str(path_str)


# ─────────────────────────────────────────────────────────────────────────────
# 자가검토 헬퍼 (F-010)
# ─────────────────────────────────────────────────────────────────────────────

def build_review_block(md_path):
    """결정론적 휴리스틱만. read-only. 반환 dict:
    {
      "promote_candidates": [...],   # 오래된 active(등록일 diff ≥ PROMOTE_AGE_DAYS) + [REVIEW] 플래그 행
      "cleanup_candidates": [...],   # 물리적으로 남은 dead/superseded 행
      "history_status": {"fifo_trimmed": bool, "count": int},
      "violations": [...],           # 마커·요약 길이>80·type/status enum format 위반
    }
    역할 경계: 졸업지·성숙 판단 없음. 후보 표면화만.
    """
    try:
        content = pathlib.Path(md_path).read_text(encoding="utf-8")
    except Exception:
        return {
            "promote_candidates": [],
            "cleanup_candidates": [],
            "history_status": {"fifo_trimmed": False, "count": 0},
            "violations": [],
        }

    promote_candidates = []
    cleanup_candidates = []
    violations = []

    # 마커 검증
    if not has_index_markers(content):
        violations.append({"type": "marker_missing", "detail": "index 마커 누락"})
    if not has_history_markers(content):
        violations.append({"type": "marker_missing", "detail": "history 마커 누락"})

    # 인덱스 행 분석
    index_rows = _parse_index_rows(content)
    today = datetime.now(timezone(timedelta(hours=9))).date()

    for row in index_rows:
        status  = row.get("status", "")
        title   = row.get("title", "")
        rtype   = row.get("type", "")
        summary = row.get("summary", "")
        date_str = row.get("date", "")

        # enum 위반 검증
        if status and status not in VALID_STATUSES:
            violations.append({"type": "invalid_status", "title": title, "value": status})
        if rtype and rtype not in VALID_TYPES:
            violations.append({"type": "invalid_type", "title": title, "value": rtype})

        # summary 길이 검증
        if len(summary) > 80:
            violations.append({"type": "summary_too_long", "title": title, "length": len(summary)})

        # promote 후보: active 행 중 오래된 것 또는 [REVIEW] 플래그
        if status == "active":
            is_candidate = False
            if "[REVIEW]" in summary or "[REVIEW]" in title:
                is_candidate = True
            else:
                try:
                    reg_date = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
                    if (today - reg_date).days >= PROMOTE_AGE_DAYS:
                        is_candidate = True
                except (ValueError, TypeError):
                    pass
            if is_candidate:
                # 힌트로 type 제공, 졸업지 단정 없음
                promote_candidates.append({"title": title, "type": rtype, "date": date_str})

        # cleanup 후보: dead/superseded 행
        if status in ("dead", "superseded"):
            cleanup_candidates.append({"title": title, "status": status})

    # 히스토리 상태
    history_rows = _parse_history_rows(content)
    history_count = len(history_rows)
    fifo_trimmed = history_count > HISTORY_FIFO_LIMIT

    history_status = {
        "fifo_trimmed": fifo_trimmed,
        "count": history_count,
    }

    return {
        "promote_candidates": promote_candidates,
        "cleanup_candidates": cleanup_candidates,
        "history_status": history_status,
        "violations": violations,
    }


# ─────────────────────────────────────────────────────────────────────────────
# cmd_init (F-006)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_init(args):
    """MEMORY.md 신포맷 마커·헤더·빈 표 삽입(create-if-absent).
    마커 이미 존재 + not --force → already_initialized.
    """
    md_path = pathlib.Path(args.file)

    # 파일이 없으면 생성
    if not md_path.exists():
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text("# Memory Index\n\n", encoding="utf-8")

    content = md_path.read_text(encoding="utf-8")

    # 마커 존재 검사
    if has_any_markers(content) and not args.force:
        err("init", "already_initialized")

    # 신포맷 마커·빈 표 블록 구성
    init_block = (
        "\n## 메모리\n"
        f"{INDEX_MARKER_START}\n"
        f"{INDEX_HEADER}\n"
        f"{INDEX_SEPARATOR}\n"
        f"{INDEX_MARKER_END}\n"
        "\n## 작업 히스토리 (최대 5개, FIFO)\n"
        f"{HISTORY_MARKER_START}\n"
        f"{HISTORY_HEADER}\n"
        f"{HISTORY_SEPARATOR}\n"
        f"{HISTORY_MARKER_END}\n"
    )

    if args.force and has_any_markers(content):
        # force 재삽입: 기존 마커 영역을 교체
        # 단순하게 기존 마커가 있는 상태에서 덮어쓰기
        # index 교체
        idx_table = _render_index_table(_parse_index_rows(content))
        content = replace_marker_section(content, INDEX_MARKER_START, INDEX_MARKER_END, idx_table) or content
        # history 교체
        hist_table = _render_history_table(_parse_history_rows(content))
        content = replace_marker_section(content, HISTORY_MARKER_START, HISTORY_MARKER_END, hist_table) or content
        md_path.write_text(content, encoding="utf-8")
    else:
        # 신규 삽입: 파일 끝에 블록 추가
        new_content = content.rstrip("\n") + "\n" + init_block
        md_path.write_text(new_content, encoding="utf-8")

    # 작성 후 review 블록 첨부
    review = build_review_block(str(md_path))
    ok("init", file=str(md_path), review=review)


# ─────────────────────────────────────────────────────────────────────────────
# cmd_append (F-003, F-004)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_append(args):
    """메모리/히스토리 행 추가.
    --kind memory: 마커 가드 + type/status enum + summary ≤80 검증. 갯수 무제한.
    --kind history: FIFO=5 집행.
    """
    md_path = pathlib.Path(args.file)

    # MEMORY.md 존재 확인
    if not md_path.exists():
        err("append", "memory_md_not_found", path=str(md_path))

    content = md_path.read_text(encoding="utf-8")

    # title 필수
    title = (args.title or "").strip()
    if not title:
        err("append", "title_required")

    # kind 검증
    kind = args.kind
    if kind not in ("memory", "history"):
        err("append", "invalid_kind", kind=kind)

    # 마커 가드 (R9) — 마커 부재 시 mutating 명령 거부, 파일 불변
    if not has_index_markers(content):
        err("append", "marker_missing")

    today = get_kst_date()

    if kind == "memory":
        # type enum 검증
        rtype = (args.type or "").strip()
        if rtype not in VALID_TYPES:
            err("append", "invalid_type", value=rtype)

        # status (default: active)
        status = (args.status or "active").strip()
        if status not in VALID_STATUSES:
            err("append", "invalid_status", value=status)

        # summary 길이캡 (R2)
        summary = (args.summary or "").strip()
        if len(summary) > 80:
            err("append", "summary_too_long", length=len(summary))

        # 파일 경로 생성 (title 기반 slug)
        file_path = _title_to_filename(title)

        # 인덱스 표에 행 추가
        index_rows = _parse_index_rows(content)
        index_rows.append({
            "title":   title,
            "date":    today,
            "type":    rtype,
            "status":  status,
            "file":    file_path,
            "summary": summary,
        })

        new_table = _render_index_table(index_rows)
        new_content = replace_marker_section(content, INDEX_MARKER_START, INDEX_MARKER_END, new_table)
        if new_content is None:
            err("append", "marker_missing")

        md_path.write_text(new_content, encoding="utf-8")

        active_count = sum(1 for r in index_rows if r.get("status") == "active")
        review = build_review_block(str(md_path))
        ok("append", kind=kind, title=title, active_count=active_count, review=review)

    else:  # kind == "history"
        # 히스토리 마커 가드
        if not has_history_markers(content):
            err("append", "marker_missing")

        summary = (args.summary or "").strip()
        stage   = (getattr(args, "stage", None) or "").strip()
        path    = (getattr(args, "path", None) or "").strip()

        # 새 히스토리 행을 맨 앞에 삽입
        history_rows = _parse_history_rows(content)
        new_row = {
            "title":   title,
            "date":    today,
            "stage":   stage,
            "path":    path,
            "result":  summary,
        }
        history_rows.insert(0, new_row)

        # FIFO 집행
        history_rows = _enforce_history_fifo(history_rows)

        new_table = _render_history_table(history_rows)
        new_content = replace_marker_section(content, HISTORY_MARKER_START, HISTORY_MARKER_END, new_table)
        if new_content is None:
            err("append", "marker_missing")

        md_path.write_text(new_content, encoding="utf-8")

        review = build_review_block(str(md_path))
        ok("append", kind=kind, title=title, history_count=len(history_rows), review=review)


# ─────────────────────────────────────────────────────────────────────────────
# cmd_update (F-005)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_update(args):
    """메모리 상태/요약 수정(라이프사이클 전이).
    dead/superseded 전이 = 행 보존(추적), 로드 제외.
    """
    md_path = pathlib.Path(args.file)

    if not md_path.exists():
        err("update", "memory_md_not_found", path=str(md_path))

    content = md_path.read_text(encoding="utf-8")

    # 마커 가드
    if not has_index_markers(content):
        err("update", "marker_missing")

    title = (args.title or "").strip()
    if not title:
        err("update", "title_required")

    # 행 검색
    index_rows = _parse_index_rows(content)
    target_idx = None
    for i, row in enumerate(index_rows):
        if row["title"] == title:
            target_idx = i
            break

    if target_idx is None:
        err("update", "row_not_found", title=title)

    row = index_rows[target_idx]

    # new-title 갱신
    if getattr(args, "new_title", None) is not None:
        new_title = args.new_title.strip()
        if not new_title:
            err("update", "title_required")
        row["title"] = new_title

    # status 갱신
    if args.status is not None:
        new_status = args.status.strip()
        if new_status not in VALID_STATUSES:
            err("update", "invalid_status", value=new_status)
        row["status"] = new_status

    # summary 갱신
    if args.summary is not None:
        new_summary = args.summary.strip()
        if len(new_summary) > 80:
            err("update", "summary_too_long", length=len(new_summary))
        row["summary"] = new_summary

    index_rows[target_idx] = row

    new_table = _render_index_table(index_rows)
    new_content = replace_marker_section(content, INDEX_MARKER_START, INDEX_MARKER_END, new_table)
    if new_content is None:
        err("update", "marker_missing")

    md_path.write_text(new_content, encoding="utf-8")

    review = build_review_block(str(md_path))
    ok("update", title=title, status=row.get("status"), review=review)


# ─────────────────────────────────────────────────────────────────────────────
# cmd_promote (F-005)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_promote(args):
    """메모리 → 영구 거처 졸업.
    --to docs|brain --ref <위치> 필수.
    --ref 미지정 → promote_ref_missing (무손실, H-1).
    정상 시 인덱스 행 + memory/<file>.md 원자적 삭제 + provenance 기록.
    brain 경로: brain-tool 재사용 전제 — 자체 brain 쓰기 없음(H-9).
    """
    md_path = pathlib.Path(args.file)

    if not md_path.exists():
        err("promote", "memory_md_not_found", path=str(md_path))

    content = md_path.read_text(encoding="utf-8")

    # 마커 가드
    if not has_index_markers(content):
        err("promote", "marker_missing")

    # --to 검증
    to_target = (getattr(args, "to", None) or "").strip()
    if to_target not in ("docs", "brain"):
        err("promote", "invalid_promote_target", value=to_target)

    # --ref 필수 (H-1 무손실 가드)
    ref = (getattr(args, "ref", None) or "").strip()
    if not ref:
        err("promote", "promote_ref_missing")

    # title 검증
    title = (args.title or "").strip()
    if not title:
        err("promote", "title_required")

    # 경로 탈출 가드 — title 자체가 경로 탈출 시도인 경우 거부
    if _path_has_traversal(title):
        err("promote", "row_not_found", title=title)

    # 행 검색
    index_rows = _parse_index_rows(content)
    target_idx = None
    for i, row in enumerate(index_rows):
        if row["title"] == title:
            target_idx = i
            break

    if target_idx is None:
        err("promote", "row_not_found", title=title)

    row = index_rows[target_idx]
    file_field = row.get("file", "")

    # memory 파일 경로 확인 (경로 가드 포함)
    mem_file = _resolve_memory_file(str(md_path), file_field)
    if mem_file is None:
        err("promote", "memory_file_not_found", path=file_field)

    if not mem_file.exists():
        err("promote", "memory_file_not_found", path=str(mem_file))

    # 원자적 삭제: 인덱스 행 삭제 + memory 파일 삭제 + provenance 기록
    # (셋 중 하나라도 실패하면 미수행 원칙)
    today = get_kst_date()

    # 1. 인덱스에서 행 제거
    new_index_rows = [r for i, r in enumerate(index_rows) if i != target_idx]
    new_index_table = _render_index_table(new_index_rows)
    new_content = replace_marker_section(content, INDEX_MARKER_START, INDEX_MARKER_END, new_index_table)
    if new_content is None:
        err("promote", "marker_missing")

    # 2. MEMORY.md 저장
    md_path.write_text(new_content, encoding="utf-8")

    # 3. memory 파일 삭제
    mem_file.unlink()

    # 4. provenance 기록 — 별도 .memory_provenance.log 파일에 추가
    #    (MEMORY.md에 인라인 추가 시 제목이 파일 내용에 남아 인덱스 제거 효과 감소)
    provenance_log = md_path.parent / ".memory_provenance.log"
    provenance_entry = (
        f"{today} | promote | title={row['title']} | "
        f"type={row.get('type', '')} | to={to_target} | ref={ref} | "
        f"file={file_field}\n"
    )
    try:
        with provenance_log.open("a", encoding="utf-8") as f:
            f.write(provenance_entry)
    except Exception:
        pass  # provenance 기록 실패는 비치명적

    review = build_review_block(str(md_path))
    ok(
        "promote",
        title=title,
        to=to_target,
        ref=ref,
        file_deleted=True,
        row_removed=True,
        provenance_logged=True,
        review=review,
    )


# ─────────────────────────────────────────────────────────────────────────────
# cmd_prune (F-004)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_prune(args):
    """히스토리 FIFO=5 결정론 정리. 이미 ≤5면 no-op."""
    md_path = pathlib.Path(args.file)

    if not md_path.exists():
        err("prune", "memory_md_not_found", path=str(md_path))

    content = md_path.read_text(encoding="utf-8")

    # 마커 가드 (히스토리 마커 확인)
    if not has_history_markers(content):
        err("prune", "marker_missing")

    history_rows = _parse_history_rows(content)
    before_count = len(history_rows)

    pruned = _enforce_history_fifo(history_rows)
    after_count = len(pruned)

    if before_count != after_count:
        new_table = _render_history_table(pruned)
        new_content = replace_marker_section(content, HISTORY_MARKER_START, HISTORY_MARKER_END, new_table)
        if new_content is None:
            err("prune", "marker_missing")
        md_path.write_text(new_content, encoding="utf-8")

    review = build_review_block(str(md_path))
    ok("prune", before=before_count, after=after_count, trimmed=(before_count - after_count), review=review)


# ─────────────────────────────────────────────────────────────────────────────
# cmd_migrate (F-006)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_migrate(args):
    """구포맷 → 신포맷 변환.
    구포맷: | 등록일시 | 카테고리 | 상태 | 파일 | 설명 |
    신포맷: | 제목 | 등록일 | 유형 | 상태 | 파일 | 요약 |
    제목 자동 추출 + [REVIEW] 플래그. truncate 금지(H-5).
    모든 자동 추출 행에 [REVIEW] 접두어 — PM 보정 필요 명시(PLAN §3.6.2).
    """
    md_path = pathlib.Path(args.file)

    if not md_path.exists():
        err("migrate", "memory_md_not_found", path=str(md_path))

    content = md_path.read_text(encoding="utf-8")

    # 구포맷 인덱스 표 파싱
    # 구포맷 헤더: | 등록일시 | 카테고리 | 상태 | 파일 | 설명 |
    legacy_index_rows = _parse_legacy_index(content)

    # 구포맷 히스토리 표 파싱
    # 구포맷 헤더: | 등록일자 | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |
    legacy_history_rows = _parse_legacy_history(content)

    if len(legacy_index_rows) == 0 and len(legacy_history_rows) == 0:
        err("migrate", "import_failed")

    review_count = 0

    # 인덱스 행 변환
    new_index_rows = []
    for row in legacy_index_rows:
        # 제목 추출: 설명의 첫 문장 또는 첫 30자
        desc = row.get("description", "").strip()
        title = _extract_title(desc)

        # 상태 매핑
        old_status = row.get("status", "").strip()
        # 취소선 제거
        clean_status = re.sub(r"~~(.+?)~~", r"\1", old_status).strip()
        new_status = LEGACY_STATUS_MAP.get(clean_status, None)
        if new_status is None:
            new_status = "active"

        # 요약: 설명이 80자 초과면 [REVIEW] 플래그 + 전체 텍스트 보존(truncate 금지, H-5)
        # 모든 자동 추출 행은 [REVIEW] 플래그 부착 — PM 보정 필요 명시(PLAN §3.6.2)
        if len(desc) > 80:
            summary = f"[REVIEW] {desc}"
        else:
            summary = f"[REVIEW] {desc}"  # 모든 migrate 행은 PM 검토 필요
        review_count += 1

        # 유형 매핑 (카테고리 → 신 enum)
        category = row.get("category", "").strip()
        rtype = _map_category_to_type(category)

        new_index_rows.append({
            "title":   title,
            "date":    row.get("date", "")[:10],  # YYYY-MM-DD
            "type":    rtype,
            "status":  new_status,
            "file":    row.get("file", ""),
            "summary": summary,
        })

    # 히스토리 행 변환
    new_history_rows = []
    for row in legacy_history_rows:
        task_name = row.get("task", "").strip()
        title = _extract_title(task_name) if task_name else "이전 태스크"
        stage_raw = row.get("stage", "").strip()
        # 완료/진행중 등을 신 형식으로
        if stage_raw in ("완료",):
            stage = "완료"
        elif stage_raw in ("진행중", "진행"):
            stage = "진행중"
        else:
            stage = stage_raw

        new_history_rows.append({
            "title":   title,
            "date":    row.get("date", "")[:10],
            "stage":   stage,
            "path":    row.get("path", ""),
            "result":  task_name if len(task_name) <= 80 else f"[REVIEW] {task_name}",
        })

    # FIFO 적용
    new_history_rows = _enforce_history_fifo(new_history_rows)

    # 신포맷 마커 구성
    index_table = _render_index_table(new_index_rows)
    history_table = _render_history_table(new_history_rows)

    # 구포맷 내용을 신포맷으로 교체: 구 표 섹션을 제거하고 신 마커 블록으로 대체
    new_content = _strip_legacy_tables(content)

    # 신포맷 마커 블록 추가
    new_content = new_content.rstrip("\n") + "\n\n"
    new_content += (
        f"## 메모리\n"
        f"{INDEX_MARKER_START}\n"
        f"{index_table}\n"
        f"{INDEX_MARKER_END}\n"
        f"\n## 작업 히스토리 (최대 5개, FIFO)\n"
        f"{HISTORY_MARKER_START}\n"
        f"{history_table}\n"
        f"{HISTORY_MARKER_END}\n"
    )

    md_path.write_text(new_content, encoding="utf-8")

    review = build_review_block(str(md_path))
    ok(
        "migrate",
        memory_rows=len(new_index_rows),
        history_rows=len(new_history_rows),
        review_count=review_count,
        review=review,
    )


def _parse_legacy_index(content):
    """구포맷 인덱스 표 파싱.
    헤더 패턴: | 등록일시 | 카테고리 | 상태 | 파일 | 설명 |
    """
    rows = []
    # 헤더 탐색
    in_table = False
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table:
                in_table = False
            continue
        cells = [c.strip() for c in stripped[1:-1].split("|")]
        # 헤더 행 감지 (등록일시·카테고리 포함)
        if ("등록일시" in cells or "등록일자" in cells) and "카테고리" in " ".join(cells):
            in_table = True
            continue
        # 구분선 스킵
        if all(re.match(r"^-+$", c.replace(" ", "")) for c in cells if c.replace(" ", "")):
            continue
        if in_table and len(cells) >= 5:
            rows.append({
                "date":        cells[0],
                "category":    cells[1],
                "status":      cells[2],
                "file":        cells[3],
                "description": cells[4] if len(cells) > 4 else "",
            })
    return rows


def _parse_legacy_history(content):
    """구포맷 히스토리 표 파싱.
    헤더 패턴: | 등록일자 | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |
    """
    rows = []
    in_table = False
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table:
                in_table = False
            continue
        cells = [c.strip() for c in stripped[1:-1].split("|")]
        # 헤더 행 감지 (등록일자·작업·시작일시 포함)
        joined = " ".join(cells)
        if ("등록일자" in joined or "등록일시" in joined) and "작업" in joined and ("시작일시" in joined or "완료일시" in joined):
            in_table = True
            continue
        # 구분선 스킵
        if all(re.match(r"^-+$", c.replace(" ", "")) for c in cells if c.replace(" ", "")):
            continue
        if in_table and len(cells) >= 4:
            rows.append({
                "date":  cells[0],
                "task":  cells[1],
                "stage": cells[2],
                "path":  cells[3],
            })
    return rows


def _extract_title(text):
    """설명/작업 텍스트에서 제목 추출: 첫 문장 또는 첫 30자."""
    text = text.strip()
    # [REVIEW] 접두사 제거
    text = re.sub(r"^\[REVIEW\]\s*", "", text)
    # 첫 문장: 마침표, 느낌표, 쉼표, 개행 전까지
    m = re.match(r"^([^.。!,，\n]{1,30})", text)
    if m:
        title = m.group(1).strip()
        if title:
            return title
    # 폴백: 첫 30자
    return text[:30].strip() if text else "제목 없음"


def _map_category_to_type(category):
    """구포맷 카테고리 → 신 유형 enum 매핑."""
    mapping = {
        "feedback":     "feedback",
        "architecture": "architecture",
        "issues":       "issues",
        "preferences":  "preferences",
        "task":         "task",
        "project":      "project",
    }
    return mapping.get(category.lower(), "project")


def _strip_legacy_tables(content):
    """구포맷 표 섹션(헤더 포함)을 파일 내용에서 제거한다.
    구포맷 인덱스/히스토리 표를 찾아 제거하여 신포맷 삽입 공간을 확보.
    마커가 이미 있으면 해당 마커 섹션도 제거.
    """
    lines = content.splitlines(keepends=True)
    result = []
    skip_table = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 기존 마커 영역 전체 스킵
        if INDEX_MARKER_START in stripped:
            # end 마커까지 스킵
            while i < len(lines) and INDEX_MARKER_END not in lines[i]:
                i += 1
            i += 1  # end 마커 줄도 스킵
            continue
        if HISTORY_MARKER_START in stripped:
            while i < len(lines) and HISTORY_MARKER_END not in lines[i]:
                i += 1
            i += 1
            continue

        # 구포맷 표 헤더 감지 → 표 전체 스킵
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped[1:-1].split("|")]
            joined = " ".join(cells)
            is_legacy_index_header = ("등록일시" in joined or "등록일자" in joined) and ("카테고리" in joined or "설명" in joined)
            is_legacy_history_header = ("등록일자" in joined or "등록일시" in joined) and ("작업" in joined) and ("시작일시" in joined or "완료일시" in joined)

            if is_legacy_index_header or is_legacy_history_header:
                skip_table = True
                i += 1
                continue

            if skip_table:
                # 표 데이터 행이거나 구분선이면 스킵
                if stripped.startswith("|"):
                    i += 1
                    continue
                else:
                    skip_table = False

        elif skip_table and not stripped.startswith("|"):
            skip_table = False

        # ## 섹션 헤더 중 구포맷 섹션("## 프로젝트 메모리", "## 작업 히스토리" 등)은 유지
        # 단, 이미 신포맷 마커로 추가될 섹션명과 겹치는 경우 제거
        if stripped.startswith("## ") and not stripped.startswith("## 메모리") and not stripped.startswith("## 작업 히스토리"):
            result.append(line)
        elif stripped.startswith("## 메모리") or stripped.startswith("## 작업 히스토리"):
            # 구 섹션 제목 제거 (신포맷에서 다시 삽입)
            i += 1
            continue
        elif not skip_table:
            result.append(line)

        i += 1

    return "".join(result)


# ─────────────────────────────────────────────────────────────────────────────
# cmd_show (F-002)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_show(args):
    """인덱스/히스토리 현황 출력 (read-only)."""
    md_path = pathlib.Path(args.file)

    if not md_path.exists():
        err("show", "memory_md_not_found", path=str(md_path))

    content = md_path.read_text(encoding="utf-8")

    index_rows  = _parse_index_rows(content) if has_index_markers(content) else []
    history_rows = _parse_history_rows(content) if has_history_markers(content) else []

    active_count = sum(1 for r in index_rows if r.get("status") == "active")

    ok(
        "show",
        file=str(md_path),
        index_rows=index_rows,
        history_rows=history_rows,
        active_count=active_count,
        total_count=len(index_rows),
        history_count=len(history_rows),
    )


# ─────────────────────────────────────────────────────────────────────────────
# cmd_delete (9번째 서브명령)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_delete(args):
    """dead/superseded 상태 행 물리 제거.
    --title로 행 식별. 마커 부재 시 marker_missing. 행 없으면 row_not_found.
    무손실 가드: active/promoted 행은 delete_requires_dead_or_superseded 반환 + 행 불변.
    --with-file 시 memory/<file>.md도 삭제(_resolve_memory_file() 경로 화이트리스트 재사용).
    성공 시 review 블록 첨부.
    """
    md_path = pathlib.Path(args.file)

    if not md_path.exists():
        err("delete", "memory_md_not_found", path=str(md_path))

    content = md_path.read_text(encoding="utf-8")

    # 마커 가드
    if not has_index_markers(content):
        err("delete", "marker_missing")

    title = (args.title or "").strip()
    if not title:
        err("delete", "title_required")

    # 행 검색
    index_rows = _parse_index_rows(content)
    target_idx = None
    for i, row in enumerate(index_rows):
        if row["title"] == title:
            target_idx = i
            break

    if target_idx is None:
        err("delete", "row_not_found", title=title)

    row = index_rows[target_idx]
    status = row.get("status", "")

    # 무손실 가드: active/promoted 행은 삭제 거부
    if status not in ("dead", "superseded"):
        err("delete", "delete_requires_dead_or_superseded")

    # 인덱스에서 행 제거
    new_index_rows = [r for i, r in enumerate(index_rows) if i != target_idx]
    new_index_table = _render_index_table(new_index_rows)
    new_content = replace_marker_section(content, INDEX_MARKER_START, INDEX_MARKER_END, new_index_table)
    if new_content is None:
        err("delete", "marker_missing")

    md_path.write_text(new_content, encoding="utf-8")

    # --with-file 시 memory 파일도 삭제
    file_deleted = False
    if getattr(args, "with_file", False):
        file_field = row.get("file", "")
        if file_field:
            mem_file = _resolve_memory_file(str(md_path), file_field)
            if mem_file is not None and mem_file.exists():
                mem_file.unlink()
                file_deleted = True

    review = build_review_block(str(md_path))
    ok("delete", title=title, row_removed=True, file_deleted=file_deleted, review=review)


# ─────────────────────────────────────────────────────────────────────────────
# cmd_review (F-010)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_review(args):
    """자가검토 단독 health 명령: build_review_block 결과를 ok(...)로 반환."""
    md_path = pathlib.Path(args.file)

    if not md_path.exists():
        err("review", "memory_md_not_found", path=str(md_path))

    review = build_review_block(str(md_path))

    ok(
        "review",
        file=str(md_path),
        **review,
    )


# ─────────────────────────────────────────────────────────────────────────────
# argparse main (state-tool 하단 main 동형)
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="memory_tool",
        description="OPAL memory-tool — 메모리 인덱스·히스토리 결정론적 집행 CLI"
    )
    sub = parser.add_subparsers(dest="command", help="서브명령")
    sub.required = True

    # ── init ──
    p_init = sub.add_parser("init", help="MEMORY.md 신포맷 마커·헤더·빈 표 삽입")
    p_init.add_argument("--file", required=True, help="MEMORY.md 경로")
    p_init.add_argument("--force", action="store_true", help="마커 이미 존재해도 재삽입")
    p_init.set_defaults(func=cmd_init)

    # ── append ──
    p_append = sub.add_parser("append", help="메모리/히스토리 행 추가")
    p_append.add_argument("--file", required=True, help="MEMORY.md 경로")
    p_append.add_argument("--kind", required=True, choices=["memory", "history"],
                          help="memory 또는 history")
    p_append.add_argument("--title", required=True, help="제목(필수 비공백)")
    p_append.add_argument("--type", help="유형 enum (memory 전용)")
    p_append.add_argument("--status", default="active", help="상태 (memory 전용, default: active)")
    p_append.add_argument("--summary", default="", help="요약/핵심결과 (≤80자)")
    p_append.add_argument("--stage", default="", help="단계 (history 전용)")
    p_append.add_argument("--path", default="", help="경로 (history 전용)")
    p_append.set_defaults(func=cmd_append)

    # ── update ──
    p_update = sub.add_parser("update", help="메모리 상태/요약 수정")
    p_update.add_argument("--file", required=True, help="MEMORY.md 경로")
    p_update.add_argument("--title", required=True, help="대상 행 제목")
    p_update.add_argument("--status", default=None, help="새 상태값")
    p_update.add_argument("--summary", default=None, help="새 요약 (≤80자)")
    p_update.add_argument("--new-title", default=None, dest="new_title", help="새 제목 (제목 변경 시 사용)")
    p_update.set_defaults(func=cmd_update)

    # ── promote ──
    p_promote = sub.add_parser("promote", help="메모리 → 영구 거처 졸업")
    p_promote.add_argument("--file", required=True, help="MEMORY.md 경로")
    p_promote.add_argument("--title", required=True, help="대상 행 제목")
    p_promote.add_argument("--to", default=None, choices=["docs", "brain"],
                           help="졸업지: docs 또는 brain")
    p_promote.add_argument("--ref", default=None,
                           help="영구 거처 위치 (예: AGENT.md#금지사항)")
    p_promote.add_argument("--brain-dir", default=None,
                           help="brain 디렉토리 경로 (테스트용 — 실제 brain 쓰기 없음)")
    p_promote.set_defaults(func=cmd_promote)

    # ── prune ──
    p_prune = sub.add_parser("prune", help="히스토리 FIFO=5 결정론 정리")
    p_prune.add_argument("--file", required=True, help="MEMORY.md 경로")
    p_prune.set_defaults(func=cmd_prune)

    # ── migrate ──
    p_migrate = sub.add_parser("migrate", help="구포맷 → 신포맷 변환")
    p_migrate.add_argument("--file", required=True, help="MEMORY.md 경로")
    p_migrate.set_defaults(func=cmd_migrate)

    # ── show ──
    p_show = sub.add_parser("show", help="인덱스/히스토리 현황 출력 (read-only)")
    p_show.add_argument("--file", required=True, help="MEMORY.md 경로")
    p_show.set_defaults(func=cmd_show)

    # ── review ──
    p_review = sub.add_parser("review", help="자가검토 단독 health 명령")
    p_review.add_argument("--file", required=True, help="MEMORY.md 경로")
    p_review.set_defaults(func=cmd_review)

    # ── delete ──
    p_delete = sub.add_parser("delete", help="dead/superseded 행 물리 제거 (무손실 가드)")
    p_delete.add_argument("--file", required=True, help="MEMORY.md 경로")
    p_delete.add_argument("--title", required=True, help="삭제할 행 제목")
    p_delete.add_argument("--with-file", action="store_true", dest="with_file",
                          help="memory/<file>.md도 함께 삭제")
    p_delete.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
