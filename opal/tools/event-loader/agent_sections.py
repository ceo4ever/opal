"""
@header {
  "module": "agent_sections",
  "layer": "util",
  "domain": "opal-tools",
  "description": "마크다운 절 파서(코드 펜스 인식)와 에이전트 레지스트리 항목 선별. 펜스 안 헤딩은 절이 아니다",
  "exports": ["Section", "parse_sections", "select_agent_entries"]
}
"""

from __future__ import annotations

import re
from typing import Any

HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
ENTRY_LEVEL = 3


class Section:
    """level 0 = 첫 헤딩 앞 머리말, heading = 헤딩 원문 줄, body = 다음 헤딩 직전까지(펜스 포함)."""

    def __init__(self, level: int, title: str, heading: str, body: str) -> None:
        self.level = level
        self.title = title
        self.heading = heading
        self.body = body

    @property
    def text(self) -> str:
        return self.heading + self.body


def parse_sections(text: str) -> list[Section]:
    """헤딩 단위 평면 절 목록. 코드 펜스(``` / ~~~, 4개 이상, 미종결 포함) 안 헤딩은 본문이다."""
    sections: list[Section] = []
    current = Section(0, "", "", "")
    fence: tuple[str, int] | None = None  # (문자, 길이)
    for line in text.splitlines(keepends=True):
        stripped = line.rstrip("\r\n")
        if fence is not None:
            m = re.match(r"^ {0,3}(`{3,}|~{3,})[ \t]*$", stripped)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1]:
                fence = None
            current.body += line
            continue
        m = FENCE_OPEN.match(stripped)
        if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
            fence = (m.group(1)[0], len(m.group(1)))
            current.body += line
            continue
        h = HEADING.match(stripped)
        if h:
            sections.append(current)
            current = Section(len(h.group(1)), h.group(2).strip(), line, "")
            continue
        current.body += line
    sections.append(current)
    return [s for s in sections if s.level > 0 or s.body]


def _subtree_end(sections: list[Section], index: int) -> int:
    level = sections[index].level
    end = index + 1
    while end < len(sections) and sections[end].level > level:
        end += 1
    return end


def select_agent_entries(text: str, selection: dict[str, Any], agent: str) -> dict[str, Any]:
    """제외 절(하위 포함)을 빼고, 대상 에이전트 항목(### <id>)만 남긴다.

    full_for_agents에 속한 에이전트는 모든 항목을 유지한다.
    """
    excluded_titles = set(selection.get("exclude_sections", []))
    full_agents = set(selection.get("full_for_agents", []))
    full = agent in full_agents
    sections = parse_sections(text)
    drop = [False] * len(sections)
    excluded: list[str] = []
    entries: list[tuple[int, str]] = []
    i = 0
    while i < len(sections):
        sec = sections[i]
        if sec.level > 0 and sec.title in excluded_titles:
            end = _subtree_end(sections, i)
            for j in range(i, end):
                drop[j] = True
            excluded.append(sec.title)
            i = end
            continue
        if sec.level == ENTRY_LEVEL:
            token = sec.title.split()[0] if sec.title.split() else ""
            if re.fullmatch(r"opal-[A-Za-z0-9-]+", token):
                entries.append((i, token))
        i += 1
    kept_ids: list[str] = []
    dropped_ids: list[str] = []
    for idx, token in entries:
        if drop[idx]:
            continue
        if full or token == agent:
            kept_ids.append(token)
            continue
        end = _subtree_end(sections, idx)
        for j in range(idx, end):
            drop[j] = True
        dropped_ids.append(token)
    content = "".join(s.text for s, d in zip(sections, drop) if not d)
    if full:
        target = "full"
    else:
        target = "present" if agent in kept_ids else "absent"
    return {
        "content": content,
        "agent": agent,
        "target": target,
        "kept_entries": kept_ids,
        "dropped_entries": dropped_ids,
        "excluded_sections": excluded,
        "original_bytes": len(text.encode("utf-8")),
        "content_bytes": len(content.encode("utf-8")),
    }
