"""
@header {
  "module": "test_event_loader_section_declarations",
  "layer": "test",
  "domain": "opal-tools",
  "description": "대상 문서 4종의 절 선언(sections/*.json)이 소스 문서와 정합하고 [MUST] 줄이 모든 컨텍스트 조합에서 보존되는지 검증 (S-9)",
  "exports": [],
  "depends": ["lazy_sections"]
}
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
import sys
import unittest

TOOL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_DIR.parents[2]
sys.path.insert(0, str(TOOL_DIR))

import lazy_sections  # noqa: E402

SECTIONS_DIR = REPO_ROOT / "opal" / "core" / "references" / "sections"
DECLARATIONS = ("citation-rules", "design-gate", "pm-review-gate", "pm-process")


def _load(name: str) -> tuple[dict, str]:
    decl = json.loads((SECTIONS_DIR / f"{name}.json").read_text(encoding="utf-8"))
    text = (REPO_ROOT / decl["document"]).read_text(encoding="utf-8")
    return decl, text


def _contexts(decl: dict) -> list[dict[str, str]]:
    ctx = decl.get("contexts") or {}
    keys = sorted(ctx)
    combos: list[dict[str, str]] = [{}]
    for values in itertools.product(*(ctx[k] for k in keys)):
        combos.append(dict(zip(keys, values)))
    return combos


class SectionDeclarationTests(unittest.TestCase):
    def test_declarations_valid(self) -> None:
        for name in DECLARATIONS:
            with self.subTest(declaration=name):
                decl, text = _load(name)
                self.assertEqual(lazy_sections.validate_declaration(decl, text), [])

    def test_ids_unique_across_documents(self) -> None:
        seen: dict[str, str] = {}
        for name in DECLARATIONS:
            decl, _ = _load(name)
            for s in decl["sections"]:
                self.assertNotIn(s["id"], seen, f"{s['id']} 중복: {seen.get(s['id'])} / {name}")
                seen[s["id"]] = name

    def test_id_pattern(self) -> None:
        import re

        pat = re.compile(r"^[a-z][a-z0-9-]{1,40}$")
        for name in DECLARATIONS:
            decl, _ = _load(name)
            for s in decl["sections"]:
                self.assertRegex(s["id"], pat)

    def test_must_lines_preserved_in_every_context(self) -> None:
        for name in DECLARATIONS:
            decl, text = _load(name)
            _pre, units = lazy_sections._index(text, decl)
            must_lines = [ln for ln in text.splitlines() if lazy_sections.MUST_MARK in ln]
            for ctx in _contexts(decl):
                result = lazy_sections.select_units(text, decl, ctx)
                for ln in must_lines:
                    owner = next((u for u in units if ln in u["text"]), None)
                    with self.subTest(document=name, context=ctx, line=ln[:60]):
                        if ln in result["content"]:
                            continue
                        self.assertIsNotNone(owner, "preamble 밖 소유 단위 없음")
                        spec = owner["spec"]
                        self.assertEqual(spec["load"], "conditional")
                        self.assertFalse(lazy_sections._when_satisfied(spec.get("when"), ctx))

    def test_review_covers_every_unit(self) -> None:
        for name in DECLARATIONS:
            decl, _ = _load(name)
            review = {r["id"]: r for r in decl["review"]}
            for s in decl["sections"]:
                with self.subTest(document=name, id=s["id"]):
                    self.assertIn(s["id"], review)
                    self.assertEqual(review[s["id"]]["load"], s["load"])
                    self.assertTrue(review[s["id"]]["reason"].strip())
            self.assertEqual(set(review), {s["id"] for s in decl["sections"]})

    def test_delivered_bytes_not_larger_than_original(self) -> None:
        for name in DECLARATIONS:
            decl, text = _load(name)
            for ctx in _contexts(decl):
                result = lazy_sections.select_units(text, decl, ctx)
                with self.subTest(document=name, context=ctx):
                    self.assertLessEqual(result["content_bytes"], result["original_bytes"])
                    saved = result["original_bytes"] - result["content_bytes"]
                    print(
                        f"[reduction] {name} ctx={ctx}: {result['original_bytes']}B -> "
                        f"{result['content_bytes']}B (-{saved}B), omitted={result['omitted']}"
                    )


if __name__ == "__main__":
    unittest.main()
