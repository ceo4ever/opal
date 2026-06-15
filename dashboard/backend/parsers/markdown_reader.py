"""
@header {
  "module": "parsers.markdown_reader",
  "layer": "service",
  "domain": "console",
  "description": "TASK/PLAN/DONE.md 산출물 원문 read. 읽기 전용 — open(read)만 사용, mtime 불변(H-6). 존재하지 않는 파일은 None 반환",
  "exports": ["read_markdown"],
  "depends": []
}
"""
from __future__ import annotations

import os


def read_markdown(file_path: str) -> str | None:
    """마크다운 파일 원문 읽기 (읽기 전용).

    Args:
        file_path: 읽을 파일 경로

    Returns:
        파일 내용 str, 또는 파일 없으면 None

    Note:
        - open(mode='r')만 사용 — 쓰기/이동 금지 (mtime 불변, H-6)
        - 예외 전파 없이 None 반환 (graceful)
    """
    if not os.path.isfile(file_path):
        return None

    try:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None
