"""
@header {
  "module": "parsers.skill_parser",
  "layer": "service",
  "domain": "console",
  "description": "SKILL.md 원문을 읽어 YAML frontmatter(name·description)와 frontmatter를 제거한 본문 원문, content_hash만 반환한다. 본문은 heading으로 잘라 슬롯화하지 않는다 — 본문 구조는 스킬마다 자유 형식이며 표준 heading 추출은 전수 0/55로 성립하지 않는다(태스크 143 DEC-3). yaml.safe_load 실패 시 SkillMarkdownParseError를 올리고, 파일이 없으면 available=False + 나머지 null. 실행·LLM 추론 없음, 읽기 전용(open mode='r')만 사용.",
  "exports": ["parse_skill_source", "SkillMarkdownParseError"],
  "depends": []
}
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml


class SkillMarkdownParseError(Exception):
    """SKILL.md frontmatter YAML 파싱 실패.

    호출자(adapter)는 이를 잡아 도메인 에러(code=parse_error)로 변환한다.
    """


_FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)


def parse_skill_source(path: Path) -> dict[str, Any]:
    """SKILL.md 파일을 읽어 frontmatter와 본문 원문을 반환한다.

    Args:
        path: SKILL.md 절대/상대 경로 (호출자가 허용 root 하위임을 검증한 값)

    Returns:
        dict: available, content_hash, source_name, description, body.
        `body`는 frontmatter를 제거한 본문 원문이며 파싱·가공하지 않는다.
        파일이 없으면 available=False + 나머지 null.

    Raises:
        SkillMarkdownParseError: frontmatter YAML 파싱 실패(예: 깨진 YAML).
    """
    if not path.is_file():
        return _empty_result()

    text = path.read_text(encoding="utf-8")
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

    frontmatter_text, body = _split_frontmatter(text)
    fm_data: dict[str, Any] = {}
    if frontmatter_text is not None:
        try:
            loaded = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as exc:
            raise SkillMarkdownParseError(str(exc)) from exc
        if isinstance(loaded, dict):
            fm_data = loaded

    return {
        "available": True,
        "content_hash": content_hash,
        "source_name": fm_data.get("name"),
        "description": fm_data.get("description"),
        "body": body,
    }


def _empty_result() -> dict[str, Any]:
    return {
        "available": False,
        "content_hash": None,
        "source_name": None,
        "description": None,
        "body": None,
    }


def _split_frontmatter(text: str) -> tuple[str | None, str]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    return m.group(1), text[m.end():]
