"""
@header {
  "module": "parsers.skill_parser",
  "layer": "service",
  "domain": "console",
  "description": "SKILL.md 원문(YAML frontmatter + heading 기반 본문)을 보수적으로 파싱한다. yaml.safe_load로 frontmatter를 읽고, ## Usage/When to use/Arguments/Options/Examples/Use cases heading만 인식해 섹션을 잘라낸다. 추출 실패 필드는 null/빈 배열로 돌리며 내용을 발명하지 않는다(PLAN DEC-10). 실행·LLM 추론 없음, 읽기 전용(open mode='r')만 사용.",
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
_HEADING_RE = re.compile(r"^##[ \t]+(.+?)[ \t]*$", re.MULTILINE)
_FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)

_SECTION_KEY_BY_HEADING = {
    "usage": "usage",
    "when to use": "when_to_use",
    "arguments": "arguments",
    "options": "options",
    "examples": "examples",
    "use cases": "use_cases",
}

_ITEM_RE = re.compile(
    r"^-\s*`(?P<name>[^`]+)`\s*(?:\((?P<meta>[^)]*)\))?\s*(?::\s*(?P<desc>.*))?$"
)


def parse_skill_source(path: Path) -> dict[str, Any]:
    """SKILL.md 파일을 읽어 frontmatter·본문 섹션을 추출한다.

    Args:
        path: SKILL.md 절대/상대 경로 (호출자가 허용 root 하위임을 검증한 값)

    Returns:
        dict: available, content_hash, source_name, description,
        usage_markdown, when_to_use_markdown, quick_start, arguments,
        options, examples, use_cases.
        파일이 없으면 available=False + 나머지 null/빈 배열.

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

    sections = _split_sections(body)
    usage_markdown = sections.get("usage")

    return {
        "available": True,
        "content_hash": content_hash,
        "source_name": fm_data.get("name"),
        "description": fm_data.get("description"),
        "usage_markdown": usage_markdown,
        "when_to_use_markdown": sections.get("when_to_use"),
        "quick_start": _parse_quick_start(usage_markdown),
        "arguments": _parse_items(sections.get("arguments")),
        "options": _parse_items(sections.get("options")),
        "examples": _parse_examples(sections.get("examples")),
        "use_cases": _parse_use_cases(sections.get("use_cases")),
    }


def _empty_result() -> dict[str, Any]:
    return {
        "available": False,
        "content_hash": None,
        "source_name": None,
        "description": None,
        "usage_markdown": None,
        "when_to_use_markdown": None,
        "quick_start": None,
        "arguments": [],
        "options": [],
        "examples": [],
        "use_cases": [],
    }


def _split_frontmatter(text: str) -> tuple[str | None, str]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    return m.group(1), text[m.end():]


def _split_sections(body: str) -> dict[str, str | None]:
    matches = list(_HEADING_RE.finditer(body))
    sections: dict[str, str | None] = {}
    for idx, m in enumerate(matches):
        heading = m.group(1).strip().lower()
        key = _SECTION_KEY_BY_HEADING.get(heading)
        if key is None:
            continue
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        content = body[start:end].strip()
        sections[key] = content or None
    return sections


def _parse_items(section_text: str | None) -> list[dict[str, Any]]:
    if not section_text:
        return []
    items: list[dict[str, Any]] = []
    for line in section_text.splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        m = _ITEM_RE.match(line)
        if not m:
            continue
        meta_parts = [p.strip() for p in (m.group("meta") or "").split(",") if p.strip()]
        arg_type = meta_parts[0] if meta_parts else None
        required = any(p.lower() == "required" for p in meta_parts)
        default = None
        for p in meta_parts:
            if p.lower().startswith("default:"):
                default = p.split(":", 1)[1].strip()
        items.append(
            {
                "name": m.group("name"),
                "type": arg_type,
                "required": required,
                "default": default,
                "description": (m.group("desc") or "").strip() or None,
            }
        )
    return items


def _parse_examples(section_text: str | None) -> list[dict[str, Any]]:
    if not section_text:
        return []
    examples: list[dict[str, Any]] = []
    for m in _FENCE_RE.finditer(section_text):
        command = m.group(1).strip()
        if command:
            examples.append({"command": command, "description": None})
    return examples


def _parse_use_cases(section_text: str | None) -> list[str]:
    if not section_text:
        return []
    use_cases: list[str] = []
    for line in section_text.splitlines():
        line = line.strip()
        if line.startswith("-"):
            item = line.lstrip("-").strip()
            if item:
                use_cases.append(item)
    return use_cases


def _parse_quick_start(usage_markdown: str | None) -> dict[str, Any] | None:
    if not usage_markdown:
        return None
    m = _FENCE_RE.search(usage_markdown)
    if not m:
        return None
    command = m.group(1).strip()
    if not command:
        return None
    return {"command": command}
