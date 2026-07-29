"""
@header {
  "module": "parsers.memory_parser",
  "layer": "service",
  "domain": "console",
  "description": "MEMORY.json 메모리 인덱스·작업 히스토리 파싱 (078 JSON 전환, F-009). json.loads 기반 매핑 — md 표 정규식 파싱 폐기. 읽기 전용 — open(read)/json.loads만 사용, mtime 불변(H-6). 함수명 parse_memory_index(content) 하위호환 유지",
  "exports": ["parse_memory_index", "MemoryIndex"],
  "depends": []
}
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class MemoryRow:
    date: str
    category: str
    status: str
    file: str
    description: str
    title: str = ""


@dataclass
class HistoryRow:
    date: str
    task: str
    stage: str
    path: str
    start: str | None = None
    end: str | None = None
    result: str = ""


@dataclass
class MemoryIndex:
    rows: list[MemoryRow] = field(default_factory=list)
    history: list[HistoryRow] = field(default_factory=list)
    warning: str | None = None


def parse_memory_index(content: str) -> dict:
    """MEMORY.json 내용 → rows/history 구조화 dict.

    Args:
        content: MEMORY.json 파일 전체 텍스트 (read-only 입력)

    Returns:
        {
            "rows": [{"date": str, "category": str, "status": str, "file": str,
                       "description": str, "title": str}],
            "history": [{"date": str, "task": str, "stage": str, "path": str,
                          "start": None, "end": None, "result": str}]
        }

    파싱 실패 시(파일 없음/JSON 파싱 오류/구조 불일치) graceful — 빈 배열 + warning 필드 반환.
    """
    try:
        return _do_parse(content)
    except Exception as exc:
        return {
            "rows": [],
            "history": [],
            "warning": f"MEMORY.json 파싱 실패: {exc}",
        }


def _do_parse(content: str) -> dict:
    doc = json.loads(content)

    rows: list[dict] = []
    for m in doc.get("memories", []):
        rows.append(
            {
                "date": m.get("date", ""),
                "category": m.get("type", ""),
                "status": m.get("status", ""),
                "file": m.get("file", ""),
                "description": m.get("summary", ""),
                "title": m.get("title", ""),
            }
        )

    history: list[dict] = []
    for h in doc.get("history", []):
        history.append(
            {
                "date": h.get("date", ""),
                "task": h.get("title", ""),
                "stage": h.get("stage", ""),
                "path": h.get("path", ""),
                "start": None,
                "end": None,
                "result": h.get("result", ""),
            }
        )

    return {"rows": rows, "history": history}
