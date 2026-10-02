"""
@header {
  "module": "test_lazy_sections",
  "layer": "test",
  "domain": "opal-tools",
  "description": "lazy_sections 모듈 공개 함수(선언 검증·선별·본문 조립·추가 절 선별)를 임시 문서·선언 픽스처로 검증 (S-8)",
  "exports": ["ValidateDeclarationTests", "SelectUnitsTests", "FetchUnitsTests"],
  "depends": ["lazy_sections"]
}
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

TOOL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_DIR))

import lazy_sections  # noqa: E402  (구현 전에는 ImportError로 RED)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


PREAMBLE = (
    "---\nmodule: fixture\n---\n\n# Fixture Doc\n\n> PREAMBLE_MARK 인용문\n\n소개 문단 INTRO_MARK\n\n"
)

CORE = "## Core Rules\n\nBODY-core 항상 전달. [MUST] 핵심 규칙.\n\n### Core Child\n\nBODY-core-child\n\n"
DEV_ONLY = "## Dev Only\n\nBODY-dev-only dev 트랙 전용.\n\n"
PLAN_ONLY = "## Plan Only\n\nBODY-plan-only plan 트랙 전용.\n\n"
HELPER = "## Helper\n\nBODY-helper dev-only가 의존.\n\n"
DEEP = "## Deep\n\nBODY-deep helper가 의존(전이).\n\n"
PLAN_REF = "## Plan Ref\n\nBODY-plan-ref plan-only가 의존.\n\n"
APPENDIX = (
    "## Ref Appendix\n\nBODY-ref-appendix 참조용.\n\n```\n## fake-heading-in-fence\nBODY-fence\n```\n\n"
    "### Appendix Child\n\nBODY-appendix-child\n\n"
)
HIDDEN = "## Hidden Rule\n\nBODY-hidden-rule 선언은 on_demand지만 [MUST] 반드시 지킨다.\n\n"

DOC = PREAMBLE + CORE + DEV_ONLY + PLAN_ONLY + HELPER + DEEP + PLAN_REF + APPENDIX + HIDDEN

UNIT_TEXT = {
    "core": CORE,
    "dev-only": DEV_ONLY,
    "plan-only": PLAN_ONLY,
    "helper": HELPER,
    "deep": DEEP,
    "plan-ref": PLAN_REF,
    "ref-appendix": APPENDIX,
    "hidden-rule": HIDDEN,
}


def decl() -> dict:
    return {
        "document": "fixture",
        "unit_level": 2,
        "contexts": {"track": ["dev", "plan"]},
        "sections": [
            {"id": "core", "title": "Core Rules", "load": "always"},
            {"id": "dev-only", "title": "Dev Only", "load": "conditional", "when": {"track": ["dev"]}, "depends": ["helper"]},
            {"id": "plan-only", "title": "Plan Only", "load": "conditional", "when": {"track": ["plan"]}, "depends": ["plan-ref"]},
            {"id": "helper", "title": "Helper", "load": "on_demand", "depends": ["deep"]},
            {"id": "deep", "title": "Deep", "load": "on_demand"},
            {"id": "plan-ref", "title": "Plan Ref", "load": "on_demand"},
            {"id": "ref-appendix", "title": "Ref Appendix", "load": "on_demand"},
            {"id": "hidden-rule", "title": "Hidden Rule", "load": "on_demand"},
        ],
    }


def codes(violations) -> list[str]:
    return [v["code"] for v in violations]


def declare(sections: list[dict], **extra) -> dict:
    out = {"document": "fixture", "unit_level": 2, "contexts": {"track": ["dev", "plan"]}, "sections": sections}
    out.update(extra)
    return out


class ValidateDeclarationTests(unittest.TestCase):
    def test_valid_declaration_has_only_the_must_ondemand_violation(self):
        # 픽스처는 의도적으로 [MUST]가 있는 on_demand 단위(hidden-rule)를 포함한다.
        self.assertEqual(codes(lazy_sections.validate_declaration(decl(), DOC)), ["section_must_not_ondemand"])

    def test_clean_declaration_returns_empty_list(self):
        d = decl()
        d["sections"][-1]["load"] = "always"  # hidden-rule을 always로
        self.assertEqual(lazy_sections.validate_declaration(d, DOC), [])

    def test_must_ondemand_is_reported_with_unit_id(self):
        found = [v for v in lazy_sections.validate_declaration(decl(), DOC) if v["code"] == "section_must_not_ondemand"]
        self.assertEqual(len(found), 1)
        self.assertIn("hidden-rule", json.dumps(found[0], ensure_ascii=False))

    def test_conditional_unit_with_must_is_not_reported(self):
        d = decl()
        d["sections"][-1]["load"] = "conditional"
        d["sections"][-1]["when"] = {"track": ["dev"]}
        self.assertEqual(lazy_sections.validate_declaration(d, DOC), [])

    def test_title_not_found(self):
        d = decl()
        d["sections"][1]["title"] = "Dev Only Typo"
        d["sections"][-1]["load"] = "always"
        result = lazy_sections.validate_declaration(d, DOC)
        self.assertIn("section_title_not_found", codes(result))
        self.assertIn("dev-only", json.dumps([v for v in result if v["code"] == "section_title_not_found"], ensure_ascii=False))

    def test_title_duplicate_in_document(self):
        text = DOC + "## Dev Only\n\nBODY-dup\n\n"
        d = decl()
        d["sections"][-1]["load"] = "always"
        self.assertIn("section_title_duplicate", codes(lazy_sections.validate_declaration(d, text)))

    def test_undeclared_unit(self):
        text = DOC + "## Extra Unit\n\nBODY-extra\n\n"
        d = decl()
        d["sections"][-1]["load"] = "always"
        result = lazy_sections.validate_declaration(d, text)
        found = [v for v in result if v["code"] == "section_undeclared"]
        self.assertEqual(len(found), 1, result)
        self.assertIn("Extra Unit", json.dumps(found[0], ensure_ascii=False))

    def test_fenced_heading_is_not_a_unit_so_not_undeclared(self):
        d = decl()
        d["sections"][-1]["load"] = "always"
        result = lazy_sections.validate_declaration(d, DOC)
        self.assertNotIn("section_undeclared", codes(result))
        self.assertNotIn("fake-heading-in-fence", json.dumps(result, ensure_ascii=False))

    def test_id_duplicate(self):
        d = decl()
        d["sections"][-1]["load"] = "always"
        d["sections"][4]["id"] = "helper"  # deep -> helper 중복
        self.assertIn("section_id_duplicate", codes(lazy_sections.validate_declaration(d, DOC)))

    def test_depends_unknown(self):
        d = decl()
        d["sections"][-1]["load"] = "always"
        d["sections"][0]["depends"] = ["ghost"]
        result = lazy_sections.validate_declaration(d, DOC)
        found = [v for v in result if v["code"] == "section_depends_unknown"]
        self.assertEqual(len(found), 1, result)
        self.assertIn("ghost", json.dumps(found[0]))

    def test_depends_cycle_two_nodes(self):
        d = decl()
        d["sections"][-1]["load"] = "always"
        d["sections"][4]["depends"] = ["helper"]  # helper -> deep -> helper
        self.assertIn("section_depends_cycle", codes(lazy_sections.validate_declaration(d, DOC)))

    def test_depends_cycle_self_loop(self):
        d = decl()
        d["sections"][-1]["load"] = "always"
        d["sections"][3]["depends"] = ["helper"]
        self.assertIn("section_depends_cycle", codes(lazy_sections.validate_declaration(d, DOC)))

    def test_unit_level_violation_shallower_heading_after_first_unit(self):
        text = DOC + "# Late Top Heading\n\nBODY-late\n\n"
        d = decl()
        d["sections"][-1]["load"] = "always"
        self.assertIn("section_unit_level_invalid", codes(lazy_sections.validate_declaration(d, text)))

    def test_shallower_heading_in_preamble_is_allowed(self):
        d = decl()
        d["sections"][-1]["load"] = "always"
        self.assertNotIn("section_unit_level_invalid", codes(lazy_sections.validate_declaration(d, DOC)))

    def test_conditional_without_when(self):
        for when in (None, {}):
            with self.subTest(when=when):
                d = decl()
                d["sections"][-1]["load"] = "always"
                d["sections"][1].pop("when")
                if when is not None:
                    d["sections"][1]["when"] = when
                self.assertIn("section_conditional_without_when", codes(lazy_sections.validate_declaration(d, DOC)))

    def test_declaration_format_invalid(self):
        def mutate(fn):
            d = decl()
            d["sections"][-1]["load"] = "always"
            fn(d)
            return d

        cases = {
            "no_sections": lambda d: d.pop("sections"),
            "bad_id_pattern": lambda d: d["sections"][0].__setitem__("id", "Bad_ID"),
            "bad_load_value": lambda d: d["sections"][0].__setitem__("load", "lazy"),
            "unit_level_not_int": lambda d: d.__setitem__("unit_level", "two"),
            "contexts_not_dict": lambda d: d.__setitem__("contexts", ["track"]),
        }
        for name, fn in cases.items():
            with self.subTest(name):
                self.assertIn("section_declaration_invalid", codes(lazy_sections.validate_declaration(mutate(fn), DOC)))

    def test_violations_are_dicts_with_code(self):
        for v in lazy_sections.validate_declaration(decl(), DOC):
            self.assertIsInstance(v, dict)
            self.assertIn("code", v)


class SelectUnitsTests(unittest.TestCase):
    def select(self, context, text=DOC, declaration=None):
        return lazy_sections.select_units(text, declaration or decl(), context)

    def test_dev_context_delivers_always_conditional_and_transitive_closure(self):
        result = self.select({"track": "dev"})
        # dev-only → helper → deep(전이), hidden-rule은 [MUST]로 강제. 원문 순서.
        self.assertEqual(result["delivered"], ["core", "dev-only", "helper", "deep", "hidden-rule"])
        self.assertEqual(result["omitted"], ["plan-only", "plan-ref", "ref-appendix"])

    def test_plan_context(self):
        result = self.select({"track": "plan"})
        self.assertEqual(result["delivered"], ["core", "plan-only", "plan-ref", "hidden-rule"])
        self.assertEqual(result["omitted"], ["dev-only", "helper", "deep", "ref-appendix"])

    def test_unknown_context_key_missing_delivers_conditionals(self):
        result = self.select({})
        self.assertEqual(
            result["delivered"], ["core", "dev-only", "plan-only", "helper", "deep", "plan-ref", "hidden-rule"]
        )
        self.assertEqual(result["omitted"], ["ref-appendix"])

    def test_on_demand_only_unit_never_delivered_without_dependency_or_must(self):
        for ctx in ({"track": "dev"}, {"track": "plan"}, {}):
            with self.subTest(ctx=ctx):
                self.assertIn("ref-appendix", self.select(ctx)["omitted"])

    def test_must_in_on_demand_is_forced_and_recorded(self):
        result = self.select({"track": "dev"})
        self.assertIn("hidden-rule", result["delivered"])
        self.assertEqual(result["forced_by_must"], ["hidden-rule"])

    def test_must_in_always_unit_is_not_recorded_as_forced(self):
        result = self.select({"track": "dev"})
        self.assertIn("core", result["delivered"])
        self.assertNotIn("core", result["forced_by_must"])

    def test_must_in_conditional_not_satisfied_is_forced(self):
        d = decl()
        d["sections"][2]["load"] = "conditional"  # plan-only
        text = DOC.replace("BODY-plan-only plan 트랙 전용.", "BODY-plan-only [MUST] plan 필수.")
        result = self.select({"track": "dev"}, text=text, declaration=d)
        self.assertIn("plan-only", result["delivered"])
        self.assertIn("plan-only", result["forced_by_must"])

    def test_no_must_means_forced_is_empty(self):
        text = DOC.replace("[MUST]", "필수")
        result = self.select({"track": "dev"}, text=text)
        self.assertEqual(result["forced_by_must"], [])
        self.assertNotIn("hidden-rule", result["delivered"])
        self.assertIn("hidden-rule", result["omitted"])

    def test_unit_sha256_covers_every_unit_with_unit_text_hash(self):
        result = self.select({"track": "dev"})
        self.assertEqual(set(result["unit_sha256"]), set(UNIT_TEXT))
        for unit_id, text in UNIT_TEXT.items():
            self.assertEqual(result["unit_sha256"][unit_id], sha(text), unit_id)

    def test_byte_counters(self):
        result = self.select({"track": "dev"})
        self.assertEqual(result["original_bytes"], len(DOC.encode("utf-8")))
        self.assertEqual(result["content_bytes"], len(result["content"].encode("utf-8")))

    def test_content_has_preamble_toc_then_delivered_units_in_order(self):
        result = self.select({"track": "dev"})
        content = result["content"]
        self.assertTrue(content.startswith(PREAMBLE), "머리말이 본문 맨 앞에 그대로 와야 한다")
        positions = [content.index(UNIT_TEXT[i]) for i in result["delivered"]]
        self.assertEqual(positions, sorted(positions))
        first_unit = positions[0]
        for omitted in result["omitted"]:
            line = f"- {omitted} — "
            self.assertIn(line, content)
            self.assertGreaterEqual(content.index(line), len(PREAMBLE))
            self.assertLess(content.index(line), first_unit, "목차는 머리말 뒤 전달 단위 앞")

    def test_toc_line_format_title_and_bytes(self):
        content = self.select({"track": "dev"})["content"]
        for unit_id, title in (("plan-only", "Plan Only"), ("plan-ref", "Plan Ref"), ("ref-appendix", "Ref Appendix")):
            expected = f"- {unit_id} — {title} ({len(UNIT_TEXT[unit_id].encode('utf-8'))}B)"
            self.assertIn(expected, content)

    def test_toc_has_fetch_instruction(self):
        content = self.select({"track": "dev"})["content"]
        self.assertIn("event-loader section --receipt", content)
        self.assertIn("--id", content)

    def test_omitted_unit_bodies_and_children_absent_delivered_present(self):
        content = self.select({"track": "dev"})["content"]
        for marker in ("BODY-plan-only", "BODY-plan-ref", "BODY-ref-appendix", "BODY-appendix-child", "BODY-fence"):
            self.assertNotIn(marker, content, marker)
        for marker in ("BODY-core", "BODY-core-child", "BODY-dev-only", "BODY-helper", "BODY-deep", "BODY-hidden-rule", "PREAMBLE_MARK", "INTRO_MARK"):
            self.assertIn(marker, content, marker)

    def test_toc_not_listing_delivered_units(self):
        content = self.select({"track": "dev"})["content"]
        for unit_id in ("core", "dev-only", "helper", "deep", "hidden-rule"):
            self.assertNotIn(f"- {unit_id} — ", content)

    def test_toc_not_listing_fenced_heading_or_child_headings_as_units(self):
        content = self.select({"track": "dev"})["content"]
        self.assertNotIn("fake-heading-in-fence", content)
        self.assertNotIn("- appendix-child", content)

    def test_dev_content_is_smaller_than_original_when_units_omitted(self):
        # 큰 미전달 단위 하나가 있으면 목차를 더해도 원본보다 작아야 한다.
        big = DOC.replace("BODY-ref-appendix 참조용.", "BODY-ref-appendix " + "참조 문장입니다. " * 200)
        result = self.select({"track": "dev"}, text=big)
        self.assertLess(result["content_bytes"], result["original_bytes"])

    def test_fenced_heading_in_delivered_unit_stays_in_unit_body(self):
        d = decl()
        d["sections"][6]["load"] = "always"  # ref-appendix 전달
        result = self.select({"track": "dev"}, declaration=d)
        self.assertIn("ref-appendix", result["delivered"])
        self.assertIn("## fake-heading-in-fence\nBODY-fence\n```", result["content"])
        self.assertNotIn("fake-heading-in-fence", json.dumps(result["delivered"] + result["omitted"]))
        self.assertEqual(set(result["unit_sha256"]), set(UNIT_TEXT), "펜스 안 헤딩이 단위로 잡히면 안 된다")

    def test_no_omitted_units_means_no_toc_and_content_equals_original(self):
        d = decl()
        for s in d["sections"]:
            s["load"] = "always"
            s.pop("when", None)
        result = self.select({"track": "dev"}, declaration=d)
        self.assertEqual(result["omitted"], [])
        self.assertEqual(result["content"], DOC)
        self.assertEqual(result["content_bytes"], result["original_bytes"])
        self.assertNotIn("event-loader section", result["content"])

    def test_all_delivered_via_context_has_no_toc(self):
        # 조건 불명 + 전부 전달되는 선언: ref-appendix만 always로 두면 미전달 0개
        d = decl()
        d["sections"][6]["load"] = "always"
        result = self.select({}, declaration=d)
        self.assertEqual(result["omitted"], [])
        self.assertEqual(result["content"], DOC)
        self.assertNotIn("event-loader section --receipt", result["content"])

    def test_preamble_always_delivered_even_when_everything_else_omitted(self):
        d = declare(
            [
                {"id": "only-cond", "title": "Core Rules", "load": "conditional", "when": {"track": ["plan"]}},
                {"id": "rest", "title": "Dev Only", "load": "on_demand"},
            ]
        )
        # CORE는 [MUST]를 담아 조건 불성립이어도 강제 전달되므로(D-10) 이 시나리오에서는 [MUST] 없는 단위를 쓴다
        plain_core = "## Core Rules\n\nBODY-core 일반 규칙.\n\n"
        text = PREAMBLE + plain_core + DEV_ONLY
        result = lazy_sections.select_units(text, d, {"track": "dev"})
        self.assertEqual(result["delivered"], [])
        self.assertTrue(result["content"].startswith(PREAMBLE))
        self.assertIn("- only-cond — Core Rules (", result["content"])
        self.assertIn("- rest — Dev Only (", result["content"])

    def test_select_does_not_mutate_inputs(self):
        d = decl()
        before = copy.deepcopy(d)
        ctx = {"track": "dev"}
        self.select(ctx, declaration=d)
        self.assertEqual(d, before)
        self.assertEqual(ctx, {"track": "dev"})

    def test_dependency_closure_is_transitive_for_conditional_only(self):
        # dev-only → helper → deep: 컨텍스트 plan에서는 어느 것도 전달되지 않는다
        result = self.select({"track": "plan"})
        for unit_id in ("dev-only", "helper", "deep"):
            self.assertIn(unit_id, result["omitted"])

    def test_always_unit_dependencies_are_pulled_in(self):
        d = decl()
        d["sections"][0]["depends"] = ["ref-appendix"]
        result = self.select({"track": "plan"}, declaration=d)
        self.assertIn("ref-appendix", result["delivered"])


class FetchUnitsTests(unittest.TestCase):
    CTX = {"track": "dev"}

    def delivered(self):
        return lazy_sections.select_units(DOC, decl(), self.CTX)["delivered"]

    def fetch(self, requested, delivered=None):
        return lazy_sections.fetch_units(
            DOC, decl(), self.CTX, self.delivered() if delivered is None else delivered, requested
        )

    def test_requested_omitted_unit_returned_with_hash_bytes_and_content(self):
        result = self.fetch(["ref-appendix"])
        self.assertEqual([s["id"] for s in result["sections"]], ["ref-appendix"])
        section = result["sections"][0]
        self.assertEqual(section["title"], "Ref Appendix")
        self.assertEqual(section["content"], APPENDIX)
        self.assertEqual(section["sha256"], sha(APPENDIX))
        self.assertEqual(section["bytes"], len(APPENDIX.encode("utf-8")))
        self.assertEqual(section["via"], "requested")
        self.assertEqual(result["already_delivered"], [])

    def test_hash_matches_select_units_unit_sha256(self):
        selected = lazy_sections.select_units(DOC, decl(), self.CTX)
        section = self.fetch(["plan-only"])["sections"][0]
        self.assertEqual(section["sha256"], selected["unit_sha256"]["plan-only"])

    def test_dependency_closure_included_and_marked(self):
        result = self.fetch(["plan-only"])
        by_id = {s["id"]: s for s in result["sections"]}
        self.assertEqual(set(by_id), {"plan-only", "plan-ref"})
        self.assertEqual(by_id["plan-only"]["via"], "requested")
        self.assertEqual(by_id["plan-ref"]["via"], "depends")

    def test_transitive_dependencies_included(self):
        result = self.fetch(["helper"], delivered=["core"])
        self.assertEqual({s["id"] for s in result["sections"]}, {"helper", "deep"})

    def test_sections_in_document_order(self):
        result = self.fetch(["ref-appendix", "plan-only"])
        ids = [s["id"] for s in result["sections"]]
        self.assertEqual(ids, ["plan-only", "plan-ref", "ref-appendix"])

    def test_already_delivered_requested_ids_are_listed_and_not_returned(self):
        result = self.fetch(["core", "ref-appendix"])
        self.assertEqual(result["already_delivered"], ["core"])
        self.assertEqual([s["id"] for s in result["sections"]], ["ref-appendix"])

    def test_only_already_delivered_returns_no_sections(self):
        result = self.fetch(["core", "deep"])
        self.assertEqual(result["sections"], [])
        self.assertEqual(result["already_delivered"], ["core", "deep"])

    def test_delivered_dependency_is_not_returned_again(self):
        # plan-only는 plan-ref에 의존하는데 plan-ref가 이미 전달된 경우
        result = self.fetch(["plan-only"], delivered=["core", "plan-ref"])
        self.assertEqual([s["id"] for s in result["sections"]], ["plan-only"])

    def test_unknown_id_raises_section_not_found(self):
        with self.assertRaises(ValueError) as ctx:
            self.fetch(["no-such-unit"])
        self.assertIn("section_not_found: no-such-unit", str(ctx.exception))

    def test_unknown_id_among_valid_ids_still_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.fetch(["ref-appendix", "ghost"])
        self.assertIn("section_not_found: ghost", str(ctx.exception))

    def test_fetch_result_keys(self):
        result = self.fetch(["ref-appendix"])
        self.assertEqual(set(result), {"sections", "already_delivered"})
        self.assertEqual(set(result["sections"][0]), {"id", "title", "content", "sha256", "bytes", "via"})


if __name__ == "__main__":
    unittest.main()
