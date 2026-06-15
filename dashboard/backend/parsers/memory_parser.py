"""
@header {
  "module": "parsers.memory_parser",
  "layer": "service",
  "domain": "console",
  "description": "MEMORY.md 메모리 표·작업 히스토리 표 파싱. 읽기 전용 — open(read)만 사용, mtime 불변(H-6)",
  "exports": ["parse_memory_index", "MemoryIndex"],
  "depends": []
}
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class MemoryRow:
    date: str
    category: str
    status: str
    file: str
    description: str


@dataclass
class HistoryRow:
    date: str
    task: str
    stage: str
    path: str
    start: str | None = None
    end: str | None = None


@dataclass
class MemoryIndex:
    rows: list[MemoryRow] = field(default_factory=list)
    history: list[HistoryRow] = field(default_factory=list)
    warning: str | None = None


# md 표 행 파싱: | col1 | col2 | ... |
_TABLE_ROW_RE = re.compile(r"^\|(.+)\|$")
_SEPARATOR_RE = re.compile(r"^\|[\s\-\|]+\|$")


def _parse_table_rows(lines: list[str]) -> list[list[str]]:
    """md 표 행 파싱 → 셀 값 리스트 목록.

    헤더 행, 구분선 행을 건너뛰고 데이터 행만 반환.
    """
    rows: list[list[str]] = []
    for line in lines:
        if not _TABLE_ROW_RE.match(line.strip()):
            continue
        if _SEPARATOR_RE.match(line.strip()):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append(cells)
    return rows


def _extract_section_lines(content: str, heading: str) -> list[str]:
    """## heading 아래 다음 ## 이전까지의 줄 목록 반환."""
    lines = content.splitlines()
    in_section = False
    result: list[str] = []

    for line in lines:
        if line.startswith("## ") and heading in line:
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            result.append(line)

    return result


def parse_memory_index(content: str) -> dict:
    """MEMORY.md 내용 → rows/history 구조화 dict.

    Args:
        content: MEMORY.md 파일 전체 텍스트 (read-only 입력)

    Returns:
        {
            "rows": [{"date": str, "category": str, "status": str, "file": str, "description": str}],
            "history": [{"date": str, "task": str, "stage": str, "path": str, "start": str|None, "end": str|None}]
        }

    파싱 실패 시 graceful — 빈 배열 + warning 필드 반환.
    """
    try:
        return _do_parse(content)
    except Exception as exc:
        return {
            "rows": [],
            "history": [],
            "warning": f"MEMORY.md 파싱 실패: {exc}",
        }


def _do_parse(content: str) -> dict:
    rows: list[dict] = []
    history: list[dict] = []

    # ── 메모리 표 파싱 ──────────────────────────────────────────
    # ## 메모리 섹션 내 표: | 등록일시 | 카테고리 | 상태 | 파일 | 설명 |
    mem_lines = _extract_section_lines(content, "메모리")
    table_rows = _parse_table_rows(mem_lines)

    for cells in table_rows:
        if len(cells) < 5:
            continue
        # 헤더 행 스킵 (첫 번째 셀이 "등록일시" 등)
        if cells[0] in ("등록일시", "date", "카테고리", "---"):
            continue
        rows.append(
            {
                "date": cells[0],
                "category": cells[1],
                "status": cells[2],
                "file": cells[3].strip("`"),  # 백틱 제거
                "description": cells[4],
            }
        )

    # ── 히스토리 표 파싱 ────────────────────────────────────────
    # ## 작업 히스토리 섹션 내 표: | 등록일자 | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |
    hist_lines = _extract_section_lines(content, "히스토리")
    hist_rows = _parse_table_rows(hist_lines)

    for cells in hist_rows:
        if len(cells) < 4:
            continue
        if cells[0] in ("등록일자", "date", "---"):
            continue
        history.append(
            {
                "date": cells[0],
                "task": cells[1],
                "stage": cells[2] if len(cells) > 2 else "",
                "path": cells[3] if len(cells) > 3 else "",
                "start": cells[4] if len(cells) > 4 else None,
                "end": cells[5] if len(cells) > 5 else None,
            }
        )

    return {"rows": rows, "history": history}
