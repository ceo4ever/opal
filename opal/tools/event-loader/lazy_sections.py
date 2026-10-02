"""
@header {
  "module": "lazy_sections",
  "layer": "util",
  "domain": "opal-tools",
  "description": "문서 절 단위 선택 로딩: 선언 검증, 컨텍스트 기반 전달·미전달 선별(의존 폐포·[MUST] 강제), 목차 조립, 추가 절 선별",
  "exports": ["validate_declaration", "select_units", "fetch_units"],
  "depends": ["agent_sections"]
}
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from agent_sections import parse_sections

LOAD_VALUES = ("always", "conditional", "on_demand")
ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]*")
MUST_MARK = "[MUST"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _nbytes(text: str) -> int:
    return len(text.encode("utf-8"))


def _split(text: str, unit_level: int) -> tuple[str, list[dict[str, Any]], list[int]]:
    """(머리말, 단위 목록, 첫 단위 이후 unit_level보다 얕은 헤딩 level 목록).

    단위 = unit_level 헤딩 + 다음 unit_level 헤딩 직전까지(하위·펜스 포함).
    첫 단위 이후의 얕은 헤딩은 앞 단위에 흡수되어 내용이 유실되지 않는다.
    """
    preamble = ""
    units: list[dict[str, Any]] = []
    shallow: list[int] = []
    for sec in parse_sections(text):
        if sec.level == unit_level:
            units.append({"title": sec.title, "text": sec.text})
        elif not units:
            preamble += sec.text
        else:
            if 0 < sec.level < unit_level:
                shallow.append(sec.level)
            units[-1]["text"] += sec.text
    return preamble, units, shallow


def _level(declaration: dict[str, Any]) -> int:
    level = declaration.get("unit_level", 2)
    return level if isinstance(level, int) and not isinstance(level, bool) and level > 0 else 2


def _sections(declaration: dict[str, Any]) -> list[dict[str, Any]]:
    secs = declaration.get("sections")
    return [s for s in secs if isinstance(s, dict)] if isinstance(secs, list) else []


def validate_declaration(declaration: dict[str, Any], text: str) -> list[dict[str, Any]]:
    """선언과 문서의 정합성 위반 목록. 위반 없으면 빈 리스트."""
    out: list[dict[str, Any]] = []

    def bad(reason: str, **extra: Any) -> None:
        out.append({"code": "section_declaration_invalid", "reason": reason, **extra})

    if not isinstance(declaration, dict):
        return [{"code": "section_declaration_invalid", "reason": "declaration_not_object"}]
    fmt_ok = True
    raw = declaration.get("sections")
    if not isinstance(raw, list) or not raw:
        bad("sections_missing_or_empty")
        fmt_ok = False
    level_raw = declaration.get("unit_level", 2)
    if not isinstance(level_raw, int) or isinstance(level_raw, bool) or level_raw < 1:
        bad("unit_level_not_positive_int")
        fmt_ok = False
    if "contexts" in declaration and not isinstance(declaration["contexts"], dict):
        bad("contexts_not_object")
    for i, s in enumerate(raw if isinstance(raw, list) else []):
        if not isinstance(s, dict):
            bad("section_not_object", index=i)
            fmt_ok = False
            continue
        sid = s.get("id")
        if not isinstance(sid, str) or not ID_PATTERN.fullmatch(sid):
            bad("id_pattern", index=i, id=sid)
        if s.get("load") not in LOAD_VALUES:
            bad("load_value", index=i, id=sid, load=s.get("load"))
        if not isinstance(s.get("title"), str) or not s.get("title"):
            bad("title_missing", index=i, id=sid)
        if "depends" in s and not (isinstance(s["depends"], list) and all(isinstance(d, str) for d in s["depends"])):
            bad("depends_not_list", index=i, id=sid)
    if not fmt_ok:
        return out

    level = level_raw
    secs = _sections(declaration)
    _pre, units, shallow = _split(text, level)
    unit_text_by_title: dict[str, str] = {}
    title_count: dict[str, int] = {}
    for u in units:
        title_count[u["title"]] = title_count.get(u["title"], 0) + 1
        unit_text_by_title.setdefault(u["title"], u["text"])

    # id 중복
    seen: set[str] = set()
    for s in secs:
        sid = s.get("id")
        if isinstance(sid, str):
            if sid in seen:
                out.append({"code": "section_id_duplicate", "id": sid})
            seen.add(sid)

    declared_titles = {s.get("title") for s in secs}
    for s in secs:
        title = s.get("title")
        if isinstance(title, str) and title not in unit_text_by_title:
            out.append({"code": "section_title_not_found", "id": s.get("id"), "title": title})
    for title, count in title_count.items():
        if count > 1:
            out.append({"code": "section_title_duplicate", "title": title, "count": count})
    for u in units:
        if u["title"] not in declared_titles:
            out.append({"code": "section_undeclared", "title": u["title"]})

    if shallow:
        out.append({"code": "section_unit_level_invalid", "unit_level": level, "levels": sorted(set(shallow))})

    for s in secs:
        if s.get("load") == "conditional" and not s.get("when"):
            out.append({"code": "section_conditional_without_when", "id": s.get("id")})
        if s.get("load") == "on_demand" and MUST_MARK in unit_text_by_title.get(s.get("title"), ""):
            out.append({"code": "section_must_not_ondemand", "id": s.get("id"), "title": s.get("title")})

    # 의존
    ids = {s.get("id") for s in secs}
    graph: dict[str, list[str]] = {}
    for s in secs:
        sid = s.get("id")
        deps = s.get("depends") or []
        for d in deps:
            if d not in ids:
                out.append({"code": "section_depends_unknown", "id": sid, "depends": d})
        if isinstance(sid, str):
            graph.setdefault(sid, []).extend(d for d in deps if d in ids)
    cyc = _find_cycle(graph)
    if cyc:
        out.append({"code": "section_depends_cycle", "cycle": cyc})
    return out


def _find_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> list[str] | None:
        state[node] = 1
        stack.append(node)
        for nxt in graph.get(node, []):
            if state.get(nxt, 0) == 1:
                return stack[stack.index(nxt):] + [nxt]
            if state.get(nxt, 0) == 0:
                found = visit(nxt)
                if found:
                    return found
        stack.pop()
        state[node] = 2
        return None

    for node in graph:
        if state.get(node, 0) == 0:
            found = visit(node)
            if found:
                return found
    return None


def _when_satisfied(when: Any, context: dict[str, str]) -> bool:
    """키가 컨텍스트에 없으면(조건 불명) 충족으로 본다 — 보수적으로 전달."""
    if not isinstance(when, dict):
        return True
    for key, values in when.items():
        if key not in context:
            continue
        allowed = values if isinstance(values, list) else [values]
        if context[key] not in allowed:
            return False
    return True


def _closure(seeds: set[str], deps: dict[str, list[str]], stop: set[str] | None = None) -> set[str]:
    result = set(seeds)
    todo = list(seeds)
    while todo:
        cur = todo.pop()
        for d in deps.get(cur, []):
            if d in result or (stop and d in stop) or d not in deps:
                continue
            result.add(d)
            todo.append(d)
    return result


def _index(text: str, declaration: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    """(머리말, 문서 순서 단위 목록). 단위: id(선언 없으면 None), title, text, spec."""
    preamble, units, _ = _split(text, _level(declaration))
    by_title: dict[str, dict[str, Any]] = {}
    for s in _sections(declaration):
        by_title.setdefault(s.get("title"), s)
    used: set[str] = set()
    out: list[dict[str, Any]] = []
    for u in units:
        spec = by_title.get(u["title"])
        if spec is not None and spec["id"] in used:
            spec = None  # 제목 중복의 뒤쪽 단위는 선언 없는 단위로 취급
        if spec is not None:
            used.add(spec["id"])
        out.append({"id": spec["id"] if spec else None, "title": u["title"], "text": u["text"], "spec": spec})
    return preamble, out


def select_units(text: str, declaration: dict[str, Any], context: dict[str, str]) -> dict[str, Any]:
    preamble, units = _index(text, declaration)
    declared = [u for u in units if u["id"] is not None]
    deps = {u["id"]: list((u["spec"].get("depends") or [])) for u in declared}

    base: set[str] = set()
    for u in declared:
        load = u["spec"].get("load")
        if load == "always" or (load == "conditional" and _when_satisfied(u["spec"].get("when"), context)):
            base.add(u["id"])
    forced = [u["id"] for u in declared if u["id"] not in base and MUST_MARK in u["text"]]
    chosen = _closure(base | set(forced), deps)

    delivered = [u["id"] for u in declared if u["id"] in chosen]
    omitted = [u["id"] for u in declared if u["id"] not in chosen]

    body = ""
    toc_lines: list[str] = []
    for u in units:
        if u["id"] is None or u["id"] in chosen:
            body += u["text"]
        else:
            toc_lines.append(f"- {u['id']} — {u['title']} ({_nbytes(u['text'])}B)")
    if omitted:
        toc = (
            "> 미전달 절 목차 — 아래 절은 이 응답에 포함되지 않았다. 필요하면 "
            "`event-loader section --receipt <receipt-path> --id <id>[,<id>...]`로 가져온다.\n\n"
            + "\n".join(toc_lines)
            + "\n\n"
        )
        content = preamble + toc + body
    else:
        content = preamble + body
    return {
        "delivered": delivered,
        "omitted": omitted,
        "forced_by_must": forced,
        "unit_sha256": {u["id"]: _sha(u["text"]) for u in declared},
        "content": content,
        "original_bytes": _nbytes(text),
        "content_bytes": _nbytes(content),
    }


def fetch_units(
    text: str,
    declaration: dict[str, Any],
    context: dict[str, str],
    delivered_ids: list[str],
    requested_ids: list[str],
) -> dict[str, Any]:
    _pre, units = _index(text, declaration)
    declared = [u for u in units if u["id"] is not None]
    known = {u["id"] for u in declared}
    for rid in requested_ids:
        if rid not in known:
            raise ValueError(f"section_not_found: {rid}")
    deps = {u["id"]: list((u["spec"].get("depends") or [])) for u in declared}
    delivered = set(delivered_ids)

    already: list[str] = []
    wanted: list[str] = []
    for rid in requested_ids:
        if rid in delivered:
            if rid not in already:
                already.append(rid)
        elif rid not in wanted:
            wanted.append(rid)
    closure = _closure(set(wanted), deps, stop=delivered)
    sections = [
        {
            "id": u["id"],
            "title": u["title"],
            "content": u["text"],
            "sha256": _sha(u["text"]),
            "bytes": _nbytes(u["text"]),
            "via": "requested" if u["id"] in wanted else "depends",
        }
        for u in declared
        if u["id"] in closure
    ]
    return {"sections": sections, "already_delivered": already}
