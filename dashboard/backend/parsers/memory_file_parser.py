"""
@header {
  "module": "parsers.memory_file_parser",
  "layer": "service",
  "domain": "console",
  "description": "memory/*.md 블록쿼트 메타(> key: value) 파싱. 읽기 전용 — open(read)만 사용, mtime 불변(H-6)",
  "exports": ["parse_memory_file"],
  "depends": []
}
"""
from __future__ import annotations

import os
import re


# > key: value 블록쿼트 메타 패턴
_BLOCKQUOTE_META_RE = re.compile(r"^>\s*([^:]+):\s*(.+)$")

# 단일 블록쿼트 라인 (key: value 형식 아닌 것)
_BLOCKQUOTE_RE = re.compile(r"^>\s*(.+)$")


def parse_memory_file(file_path: str) -> dict:
    """memory/*.md 파일 → 블록쿼트 메타 + 제목 + 본문 구조화 dict.

    Args:
        file_path: memory/*.md 파일 경로 (읽기 전용 접근)

    Returns:
        {
            "title": str,                    # # 제목
            "meta": {key: value, ...},       # > key: value 블록쿼트 메타
            "content": str,                  # 전체 원문
            "path": str
        }

    파싱 실패 시 graceful — 최소 구조 반환.
    mtime 불변 보장 — open(read)만 사용.
    """
    try:
        return _do_parse(file_path)
    except Exception as exc:
        return {
            "title": "",
            "meta": {},
            "content": "",
            "path": file_path,
            "warning": f"memory file 파싱 실패: {exc}",
        }


def _do_parse(file_path: str) -> dict:
    if not os.path.isfile(file_path):
        return {"title": "", "meta": {}, "content": "", "path": file_path}

    # 읽기 전용 — open(mode='r')만
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()
    title = ""
    meta: dict[str, str] = {}

    for line in lines:
        # 제목 추출 (첫 번째 # 헤딩)
        if not title and line.startswith("# "):
            title = line[2:].strip()
            continue

        # 블록쿼트 메타 파싱: > key: value
        m = _BLOCKQUOTE_META_RE.match(line)
        if m:
            key = m.group(1).strip()
            value = m.group(2).strip()
            meta[key] = value

    return {
        "title": title,
        "meta": meta,
        "content": content,
        "path": file_path,
    }
