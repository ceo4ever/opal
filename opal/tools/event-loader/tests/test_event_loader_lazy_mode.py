"""
@header {
  "module": "test_event_loader_lazy_mode",
  "layer": "test",
  "domain": "opal-tools",
  "description": "절 단위 로딩 실험 모드(--section-mode lazy)의 load/measure/verify/section/load-report를 CLI 공개 출력으로 검증 (S-10, S-11). 임시 소스 루트·매니페스트 픽스처 사용",
  "exports": [],
  "depends": ["event_loader", "lazy_sections"]
}
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[4]
LOADER = REPO_ROOT / "opal" / "tools" / "event-loader" / "event_loader.py"
REAL_MANIFEST = REPO_ROOT / "opal" / "core" / "references" / "events.json"
HARNESS_REL = "opal/core/references/harness"
SECTIONS_REL = "opal/core/references/sections"

PAD = "채움 문장입니다. " * 60

LAZY_DOC = (
    "---\nmodule: lazy-doc\n---\n\n# Lazy Doc\n\n> PREAMBLE_MARK 인용문\n\n소개 INTRO_MARK\n\n"
    "## Core Rules\n\nBODY-core 항상. [MUST] 핵심 규칙.\n\n"
    "## Dev Only\n\nBODY-dev-only dev 전용.\n\n"
    f"## Plan Only\n\nBODY-plan-only plan 전용. {PAD}\n\n"
    f"## Helper\n\nBODY-helper dev-only 의존. {PAD}\n\n"
    f"## Plan Ref\n\nBODY-plan-ref plan-only 의존. {PAD}\n\n"
    f"## Ref Appendix\n\nBODY-ref-appendix 참조. {PAD}\n\n```\n## fence-heading\n```\n\n"
    "## Hidden Rule\n\nBODY-hidden-rule on_demand지만 [MUST] 지킨다.\n\n"
)
PLAIN_DOC = "# Plain Doc\n\n전부 그대로 전달되는 문서 PLAIN_MARK\n\n## Part\n\n내용\n"

LAZY_DECL = {
    "document": "lazy-doc",
    "unit_level": 2,
    "contexts": {"track": ["dev", "plan"]},
    "sections": [
        {"id": "core", "title": "Core Rules", "load": "always"},
        {"id": "dev-only", "title": "Dev Only", "load": "conditional", "when": {"track": ["dev"]}, "depends": ["helper"]},
        {"id": "plan-only", "title": "Plan Only", "load": "conditional", "when": {"track": ["plan"]}, "depends": ["plan-ref"]},
        {"id": "helper", "title": "Helper", "load": "on_demand"},
        {"id": "plan-ref", "title": "Plan Ref", "load": "on_demand"},
        {"id": "ref-appendix", "title": "Ref Appendix", "load": "on_demand"},
        {"id": "hidden-rule", "title": "Hidden Rule", "load": "on_demand"},
    ],
}

DEV_DELIVERED = ["core", "dev-only", "helper", "hidden-rule"]
DEV_OMITTED = ["plan-only", "plan-ref", "ref-appendix"]


def sha(data: bytes | str) -> str:
    raw = data.encode("utf-8") if isinstance(data, str) else data
    return hashlib.sha256(raw).hexdigest()


def find_key(obj, key):
    """중첩 dict/list에서 첫 번째 key 값을 찾는다(없으면 None)."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = find_key(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_key(value, key)
            if found is not None:
                return found
    return None


class LazyBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.project = self.tmp / "project"
        self.project.mkdir()
        self.ledger = self.tmp / "ledger" / "legacy-dispatch.jsonl"
        self.source = self.tmp / "src"
        self.manifest = self.tmp / "events.json"
        self.build_fixture()

    # ---- fixture -------------------------------------------------------
    def doc_path(self, doc_id: str) -> Path:
        return self.source / HARNESS_REL / f"{doc_id}.md"

    def decl_path(self) -> Path:
        return self.source / SECTIONS_REL / "lazy-doc.json"

    def build_fixture(self):
        (self.source / HARNESS_REL).mkdir(parents=True)
        (self.source / SECTIONS_REL).mkdir(parents=True)
        self.doc_path("lazy-doc").write_text(LAZY_DOC, encoding="utf-8")
        self.doc_path("plain-doc").write_text(PLAIN_DOC, encoding="utf-8")
        self.decl_path().write_text(json.dumps(LAZY_DECL, ensure_ascii=False, indent=2), encoding="utf-8")

        def doc_entry(doc_id):
            return {
                "id": doc_id,
                "source": f"{{source_root}}/{HARNESS_REL}/{doc_id}.md",
                "deployed": f"{{deployed_root}}/references/harness/{doc_id}.md",
            }

        manifest = json.loads(REAL_MANIFEST.read_text(encoding="utf-8"))
        for event in manifest["events"]:
            if event["id"] == "stage.design":
                event["required_docs"] = [doc_entry("lazy-doc"), doc_entry("plain-doc")]
                event["sectioning"] = [
                    {
                        "document": "lazy-doc",
                        "source": f"{{source_root}}/{SECTIONS_REL}/lazy-doc.json",
                        "deployed": "{deployed_root}/references/sections/lazy-doc.json",
                    }
                ]
            elif event["id"] == "stage.execute":
                event["required_docs"] = [doc_entry("plain-doc")]
                event.pop("sectioning", None)
        self.manifest.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")

    # ---- CLI -----------------------------------------------------------
    def run_loader(self, *args, source_root=None, manifest=None):
        env = dict(os.environ)
        env["OPAL_EVENT_LOADER_LEDGER"] = str(self.ledger)
        command = [sys.executable, str(LOADER), *args]
        command += ["--source-root", str(source_root or self.source)]
        command += ["--project-root", str(self.project)]
        command += ["--manifest", str(manifest or self.manifest)]
        done = subprocess.run(command, capture_output=True, text=True, env=env, cwd=REPO_ROOT, check=False)
        if not done.stdout.strip():
            return done.returncode, {"ok": False, "error": "no_json_output", "stderr": done.stderr.strip()}
        return done.returncode, json.loads(done.stdout)

    def save(self, name: str, payload: dict) -> Path:
        path = self.tmp / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def lazy_args(self, track="dev"):
        args = ["--section-mode", "lazy"]
        if track is not None:
            args += ["--section-context", f"track={track}"]
        return args

    def lazy_load(self, name="lazy.json", track="dev", event="stage.design"):
        rc, payload = self.run_loader("load", "--event", event, *self.lazy_args(track))
        self.assertEqual(rc, 0, payload)
        self.assertTrue(payload["ok"], payload)
        return self.save(name, payload), payload

    def plain_load(self, name="plain.json", event="stage.design"):
        rc, payload = self.run_loader("load", "--event", event)
        self.assertEqual(rc, 0, payload)
        return self.save(name, payload), payload

    @staticmethod
    def doc(payload, doc_id):
        return next(d for d in payload["documents"] if d["id"] == doc_id)

    def assert_rejected(self, result, code):
        rc, payload = result
        self.assertNotEqual(rc, 0, payload)
        self.assertFalse(payload.get("ok"), payload)
        self.assertEqual(payload.get("error"), code, payload)
        return payload

    def assert_rejected_any(self, result, codes):
        rc, payload = result
        self.assertNotEqual(rc, 0, payload)
        self.assertFalse(payload.get("ok"), payload)
        self.assertIn(payload.get("error"), codes, payload)
        return payload

    def verify_lazy(self, response_path, *extra, event="stage.design"):
        return self.run_loader("verify", "--receipt", str(response_path), "--event", event, "--section-mode", "lazy", *extra)


class SectionLazyLoadTests(LazyBase):
    """S-10 (a)(b)"""

    def test_lazy_load_delivers_preamble_must_conditional_dependency_and_toc(self):
        _, payload = self.lazy_load()
        content = self.doc(payload, "lazy-doc")["content"]
        for marker in ("PREAMBLE_MARK", "INTRO_MARK", "BODY-core", "[MUST", "BODY-dev-only", "BODY-helper", "BODY-hidden-rule"):
            self.assertIn(marker, content, marker)
        for marker in ("BODY-plan-only", "BODY-plan-ref", "BODY-ref-appendix"):
            self.assertNotIn(marker, content, marker)
        for omitted in DEV_OMITTED:
            self.assertIn(f"- {omitted} — ", content)
        self.assertIn("event-loader section --receipt", content)

    def test_must_lines_of_original_are_all_present_in_lazy_body(self):
        _, payload = self.lazy_load()
        content = self.doc(payload, "lazy-doc")["content"]
        for line in LAZY_DOC.splitlines():
            if "[MUST" in line:
                self.assertIn(line, content)

    def test_non_target_document_is_verbatim(self):
        _, payload = self.lazy_load()
        plain = self.doc(payload, "plain-doc")
        self.assertEqual(plain["content"], PLAIN_DOC)
        self.assertEqual(plain["sha256"], sha(PLAIN_DOC))

    def test_lazy_total_body_is_smaller_than_plain_load(self):
        _, lazy = self.lazy_load()
        _, plain = self.plain_load()
        lazy_total = sum(len(d["content"].encode("utf-8")) for d in lazy["documents"])
        plain_total = sum(len(d["content"].encode("utf-8")) for d in plain["documents"])
        self.assertLess(lazy_total, plain_total)
        self.assertEqual(lazy["payload_bytes"], lazy_total)
        self.assertLess(lazy["payload_bytes"], plain["payload_bytes"])

    def test_receipt_schema_3_and_section_mode_record(self):
        _, payload = self.lazy_load()
        receipt = payload["receipt"]
        self.assertEqual(receipt["schema_version"], 3)
        section_mode = receipt["section_mode"]
        self.assertEqual(find_key(section_mode, "mode"), "lazy")
        self.assertEqual(find_key(section_mode, "context"), {"track": "dev"})
        self.assertEqual(find_key(section_mode, "delivered"), DEV_DELIVERED)
        self.assertEqual(find_key(section_mode, "omitted"), DEV_OMITTED)
        self.assertEqual(find_key(section_mode, "forced_by_must"), ["hidden-rule"])
        self.assertEqual(set(find_key(section_mode, "unit_sha256")), {s["id"] for s in LAZY_DECL["sections"]})
        self.assertIn(sha(self.decl_path().read_bytes()), json.dumps(section_mode))
        self.assertTrue(re.fullmatch(r"[0-9a-f]{64}", receipt["body_sha256"]))

    def test_receipt_document_entry_has_delivered_and_source_values(self):
        _, payload = self.lazy_load()
        entry = next(d for d in payload["receipt"]["documents"] if d["id"] == "lazy-doc")
        delivered = self.doc(payload, "lazy-doc")["content"]
        self.assertEqual(entry["sha256"], sha(delivered))
        self.assertEqual(entry["bytes"], len(delivered.encode("utf-8")))
        self.assertEqual(entry["source_sha256"], sha(LAZY_DOC))
        self.assertEqual(entry["source_bytes"], len(LAZY_DOC.encode("utf-8")))

    def test_receipt_source_payload_bytes_is_original_sum(self):
        _, payload = self.lazy_load()
        expected = len(LAZY_DOC.encode("utf-8")) + len(PLAIN_DOC.encode("utf-8"))
        self.assertEqual(payload["receipt"]["source_payload_bytes"], expected)
        self.assertEqual(payload["receipt"]["payload_bytes"], payload["payload_bytes"])

    def test_unspecified_context_is_unknown_so_conditionals_delivered(self):
        _, payload = self.lazy_load(track=None)
        section_mode = payload["receipt"]["section_mode"]
        delivered = find_key(section_mode, "delivered")
        for unit in ("core", "dev-only", "plan-only", "helper", "plan-ref", "hidden-rule"):
            self.assertIn(unit, delivered)
        self.assertEqual(find_key(section_mode, "omitted"), ["ref-appendix"])

    def test_plan_context_selects_other_conditional(self):
        _, payload = self.lazy_load(track="plan")
        section_mode = payload["receipt"]["section_mode"]
        self.assertEqual(find_key(section_mode, "delivered"), ["core", "plan-only", "plan-ref", "hidden-rule"])

    def test_invalid_context_value_rejected(self):
        result = self.run_loader("load", "--event", "stage.design", "--section-mode", "lazy", "--section-context", "track=nope")
        self.assert_rejected(result, "section_context_invalid")

    def test_invalid_context_key_rejected(self):
        result = self.run_loader("load", "--event", "stage.design", "--section-mode", "lazy", "--section-context", "bogus=dev")
        self.assert_rejected(result, "section_context_invalid")

    def test_unknown_section_mode_value_rejected(self):
        rc, payload = self.run_loader("load", "--event", "stage.design", "--section-mode", "eager")
        self.assertNotEqual(rc, 0, payload)
        self.assertFalse(payload.get("ok"), payload)

    def test_measure_reports_lazy_byte_fields_and_omitted_count(self):
        _, loaded = self.lazy_load()
        rc, measured = self.run_loader("measure", "--event", "stage.design", *self.lazy_args("dev"))
        self.assertEqual(rc, 0, measured)
        self.assertEqual(measured["payload_bytes"], loaded["payload_bytes"])
        self.assertEqual(measured["source_payload_bytes"], len(LAZY_DOC.encode("utf-8")) + len(PLAIN_DOC.encode("utf-8")))
        self.assertLess(measured["payload_bytes"], measured["source_payload_bytes"])
        self.assertEqual(measured["response_bytes"], loaded["response_bytes"])
        self.assertEqual(measured["omitted_unit_count"], len(DEV_OMITTED))
        self.assertFalse([key for key in measured if "cost" in key])


class SectionLazyRejectTests(LazyBase):
    """S-10 (f)"""

    def test_event_without_sectioning_rejected(self):
        result = self.run_loader("load", "--event", "stage.execute", "--section-mode", "lazy")
        self.assert_rejected(result, "section_mode_not_declared")

    def test_measure_event_without_sectioning_rejected(self):
        result = self.run_loader("measure", "--event", "stage.execute", "--section-mode", "lazy")
        self.assert_rejected(result, "section_mode_not_declared")

    def test_contract_args_with_declared_event_conflict(self):
        result = self.run_loader(
            "load", "--event", "stage.design", "--section-mode", "lazy", "--section-context", "track=dev",
            "--contract-version", "2", "--agent", "opal-be-agent", "--role", "builder", "--dispatch-id", "disp-00000001",
        )
        self.assert_rejected(result, "section_mode_conflict")

    def test_worker_dispatch_contract_args_with_section_mode_rejected(self):
        # 실제 매니페스트·실제 소스 루트: 계약 호출에는 절 단위 모드를 쓸 수 없다.
        result = self.run_loader(
            "load", "--event", "worker.dispatch", "--section-mode", "lazy",
            "--contract-version", "2", "--agent", "opal-be-agent", "--role", "builder", "--dispatch-id", "disp-00000002",
            source_root=REPO_ROOT, manifest=REAL_MANIFEST,
        )
        self.assert_rejected_any(result, {"section_mode_not_declared", "section_mode_conflict"})


class SectionLazyVerifyTests(LazyBase):
    """S-10 (c)(d)(e)"""

    def test_verify_lazy_receipt_with_flag_ok(self):
        resp, _ = self.lazy_load()
        rc, verified = self.verify_lazy(resp)
        self.assertEqual(rc, 0, verified)
        self.assertTrue(verified["ok"], verified)

    def test_lazy_receipt_without_flag_rejected(self):
        resp, _ = self.lazy_load()
        result = self.run_loader("verify", "--receipt", str(resp), "--event", "stage.design")
        self.assert_rejected(result, "section_mode_args_missing")

    def test_plain_receipt_with_lazy_flag_mismatch(self):
        resp, _ = self.plain_load()
        result = self.verify_lazy(resp)
        self.assert_rejected(result, "section_mode_mismatch")

    def test_plain_receipt_without_flag_still_verifies(self):
        resp, _ = self.plain_load()
        rc, verified = self.run_loader("verify", "--receipt", str(resp), "--event", "stage.design")
        self.assertEqual(rc, 0, verified)
        self.assertTrue(verified["ok"], verified)

    def test_document_one_char_change_rejected(self):
        resp, _ = self.lazy_load()
        path = self.doc_path("lazy-doc")
        path.write_text(path.read_text(encoding="utf-8").replace("BODY-plan-only", "BODY-plan-onlY"), encoding="utf-8")
        result = self.verify_lazy(resp)
        self.assert_rejected_any(result, {"document_hash_mismatch", "section_declaration_changed"})

    def test_declaration_change_rejected(self):
        resp, _ = self.lazy_load()
        changed = json.loads(self.decl_path().read_text(encoding="utf-8"))
        changed["sections"][3]["load"] = "always"  # helper를 always로
        self.decl_path().write_text(json.dumps(changed, ensure_ascii=False, indent=2), encoding="utf-8")
        result = self.verify_lazy(resp)
        self.assert_rejected_any(result, {"section_declaration_changed", "document_hash_mismatch"})

    def test_tampered_response_body_rejected(self):
        resp, payload = self.lazy_load()
        payload["documents"][0]["content"] += "x"
        tampered = self.save("tampered.json", payload)
        result = self.verify_lazy(tampered)
        self.assertFalse(result[1]["ok"], result)
        self.assertNotEqual(result[0], 0)


class SectionFetchTests(LazyBase):
    """S-11"""

    def setUp(self):
        super().setUp()
        self.parent_path, self.parent = self.lazy_load("parent.json", "dev")

    def fetch(self, *ids, name="fetch.json", parent=None):
        args = ["section", "--receipt", str(parent or self.parent_path)]
        for section_id in ids:
            args += ["--id", section_id]
        return self.run_loader(*args)

    def fetch_ok(self, *ids, name="fetch.json"):
        rc, payload = self.fetch(*ids)
        self.assertEqual(rc, 0, payload)
        self.assertTrue(payload["ok"], payload)
        return self.save(name, payload), payload

    def unit_text(self, title):
        match = re.search(rf"^## {re.escape(title)}\n.*?(?=^## |\Z)", LAZY_DOC, re.MULTILINE | re.DOTALL)
        return match.group(0)

    def test_fetch_omitted_unit_returns_body_and_separate_receipt(self):
        before = self.parent_path.read_bytes()
        _, payload = self.fetch_ok("plan-ref")
        self.assertEqual([s["id"] for s in payload["sections"]], ["plan-ref"])
        section = payload["sections"][0]
        text = self.unit_text("Plan Ref")
        self.assertEqual(section["document"], "lazy-doc")
        self.assertEqual(section["title"], "Plan Ref")
        self.assertEqual(section["content"], text)
        self.assertEqual(section["sha256"], sha(text))
        self.assertEqual(section["bytes"], len(text.encode("utf-8")))
        self.assertEqual(section["via"], "requested")
        receipt = payload["receipt"]
        self.assertEqual(receipt["kind"], "section_fetch")
        self.assertEqual(receipt["schema_version"], 3)
        self.assertEqual(receipt["parent"]["load_id"], self.parent["load_id"])
        self.assertRegex(receipt["parent"]["receipt_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(receipt["event"], "stage.design")
        self.assertEqual(payload["parent_load_id"], self.parent["load_id"])
        self.assertNotEqual(payload["load_id"], self.parent["load_id"])
        self.assertEqual(payload["payload_bytes"], len(text.encode("utf-8")))
        self.assertIn("response_bytes", payload)
        self.assertRegex(receipt["body_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(self.parent_path.read_bytes(), before, "부모 receipt 파일이 바뀌면 안 된다")

    def test_fetch_already_delivered_is_listed(self):
        rc, payload = self.fetch("core")
        self.assertEqual(rc, 0, payload)
        self.assertTrue(payload["ok"], payload)
        self.assertEqual(payload["already_delivered"], ["core"])
        self.assertEqual(payload["sections"], [])

    def test_fetch_unknown_id_rejected(self):
        self.assert_rejected(self.fetch("no-such-unit"), "section_not_found")

    def test_fetch_with_dependency_includes_dependency(self):
        _, payload = self.fetch_ok("plan-only")
        by_id = {s["id"]: s for s in payload["sections"]}
        self.assertEqual(set(by_id), {"plan-only", "plan-ref"})
        self.assertEqual(by_id["plan-only"]["via"], "requested")
        self.assertEqual(by_id["plan-ref"]["via"], "depends")

    def test_fetch_requires_valid_parent(self):
        path = self.doc_path("lazy-doc")
        path.write_text(path.read_text(encoding="utf-8").replace("BODY-plan-ref", "BODY-plan-reF"), encoding="utf-8")
        result = self.fetch("plan-ref")
        rc, payload = result
        self.assertNotEqual(rc, 0, payload)
        self.assertIn(payload.get("error"), {"document_hash_mismatch", "section_declaration_changed"}, payload)

    def test_verify_fetch_response_with_parent_ok(self):
        fetch_path, _ = self.fetch_ok("plan-only")
        rc, verified = self.verify_lazy(fetch_path, "--parent-receipt", str(self.parent_path))
        self.assertEqual(rc, 0, verified)
        self.assertTrue(verified["ok"], verified)

    def test_verify_fetch_response_wrong_parent_rejected(self):
        fetch_path, _ = self.fetch_ok("plan-only")
        other_path, _ = self.lazy_load("other-parent.json", "plan")
        result = self.verify_lazy(fetch_path, "--parent-receipt", str(other_path))
        self.assert_rejected(result, "section_parent_mismatch")

    def test_verify_fetch_response_tampered_body_rejected(self):
        _, payload = self.fetch_ok("plan-ref")
        payload["sections"][0]["content"] = payload["sections"][0]["content"].replace("BODY-plan-ref", "BODY-plan-reF")
        tampered = self.save("fetch-tampered.json", payload)
        result = self.verify_lazy(tampered, "--parent-receipt", str(self.parent_path))
        self.assert_rejected(result, "section_hash_mismatch")

    def test_verify_fetch_response_without_parent_rejected(self):
        fetch_path, _ = self.fetch_ok("plan-ref")
        result = self.verify_lazy(fetch_path)
        self.assert_rejected(result, "section_parent_required")

    def test_verify_fetch_response_with_changed_parent_document_rejected(self):
        fetch_path, _ = self.fetch_ok("plan-ref")
        path = self.doc_path("lazy-doc")
        path.write_text(path.read_text(encoding="utf-8").replace("BODY-core", "BODY-corE"), encoding="utf-8")
        result = self.verify_lazy(fetch_path, "--parent-receipt", str(self.parent_path))
        self.assertNotEqual(result[0], 0, result[1])
        self.assertFalse(result[1]["ok"], result[1])
        self.assertIn(result[1].get("error"), {"document_hash_mismatch", "section_declaration_changed"}, result[1])

    def test_load_report_sums_by_load_id_and_counts_fetches(self):
        fetch_path, fetched = self.fetch_ok("plan-only", name="fetch-report.json")
        rc, verified = self.verify_lazy(fetch_path, "--parent-receipt", str(self.parent_path))
        self.assertEqual(rc, 0, verified)
        verify_file = self.save("verify-result.json", verified)
        rc, report = self.run_loader(
            "load-report", "--receipt", str(self.parent_path), str(fetch_path), str(self.parent_path), str(verify_file)
        )
        self.assertEqual(rc, 0, report)
        self.assertEqual(report["payload_bytes"], self.parent["payload_bytes"] + fetched["payload_bytes"])
        self.assertEqual(report["response_bytes"], self.parent["response_bytes"] + fetched["response_bytes"])
        self.assertEqual(report["section_fetch_count"], 1)
        self.assertEqual(report["skipped_verify_results"], 1)


if __name__ == "__main__":
    unittest.main()
