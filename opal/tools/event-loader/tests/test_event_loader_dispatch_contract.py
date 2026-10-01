"""
@header {
  "module": "test_event_loader_dispatch_contract",
  "layer": "test",
  "domain": "opal-tools",
  "description": "worker.dispatch 계약 2·구형 호환·응답 중복 제거·구형 원장·측정 계약을 CLI 공개 출력으로 검증 (S-1, S-2, S-4~S-9)",
  "exports": [],
  "depends": ["event_loader"]
}
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[4]
LOADER = REPO_ROOT / "opal" / "tools" / "event-loader" / "event_loader.py"
MANIFEST = REPO_ROOT / "opal" / "core" / "references" / "events.json"
AGENTS_MD = REPO_ROOT / "opal" / "core" / "references" / "agents.md"
BASELINE_FULL_BYTES = 46244
GENERAL_AGENTS = ("opal-be-agent", "opal-test-agent", "opal-security-checker")
FULL_AGENTS = ("opal-plan-agent", "opal-task-action-agent", "opal-sdd-action-agent", "opal-loop-action-agent")
EVENT_IDS = ("session.assistant", "pm.activate", "stage.plan", "stage.design")
ID1 = "disp-00000001"
ID2 = "disp-00000002"
LEGACY_TS = ("2026-10-01T00:00:00Z", "2026-10-02T00:00:00Z", "2026-10-03T00:00:00Z")


def _agent_headings(text: str) -> set[str]:
    return set(re.findall(r"^### (opal-[a-z0-9-]+-(?:agent|checker))\b", text, re.MULTILINE))


class ContractBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.project = self.tmp / "project"
        self.project.mkdir()
        self.ledger = self.tmp / "ledger" / "legacy-dispatch.jsonl"
        self.counter = 0

    # ---- helpers -------------------------------------------------------
    def run_loader(self, *args, project=None, source_root=None, manifest=None, ledger="default", now=None):
        env = dict(os.environ)
        if ledger == "default":
            env["OPAL_EVENT_LOADER_LEDGER"] = str(self.ledger)
        elif ledger is not None:
            env["OPAL_EVENT_LOADER_LEDGER"] = str(ledger)
        if now:
            env["OPAL_EVENT_LOADER_NOW"] = now
        command = [sys.executable, str(LOADER), *args, "--source-root", str(source_root or REPO_ROOT)]
        command += ["--project-root", str(project or self.project)]
        if manifest:
            command += ["--manifest", str(manifest)]
        done = subprocess.run(command, capture_output=True, text=True, env=env, cwd=REPO_ROOT, check=False)
        if not done.stdout.strip():
            # argparse 거부 등 JSON 없는 종료는 미지원 인자/서브명령 실패로 취급한다.
            return done.returncode, {"ok": False, "error": "no_json_output", "stderr": done.stderr.strip()}
        return done.returncode, json.loads(done.stdout)

    def contract_args(self, agent="opal-be-agent", role="builder", dispatch_id=ID1, version="2", role_doc=None, omit=()):
        pairs = [("--contract-version", version), ("--agent", agent), ("--role", role), ("--dispatch-id", dispatch_id)]
        if role_doc:
            pairs.append(("--role-doc", str(role_doc)))
        out: list[str] = []
        for flag, value in pairs:
            if flag.lstrip("-") in omit:
                continue
            out += [flag, value]
        return out

    def save(self, name: str, payload: dict) -> Path:
        path = self.tmp / name
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def new_load(self, name="resp.json", event="worker.dispatch", **kwargs):
        extra = kwargs.pop("extra", [])
        run_kwargs = {k: kwargs.pop(k) for k in ("project", "source_root", "manifest") if k in kwargs}
        code, payload = self.run_loader("load", "--event", event, *self.contract_args(**kwargs), *extra, **run_kwargs)
        self.assertEqual(code, 0, payload)
        self.assertTrue(payload["ok"], payload)
        return self.save(name, payload), payload

    def verify(self, response_path, *, event="worker.dispatch", omit_event=False, **kwargs):
        extra = kwargs.pop("extra", [])
        run_kwargs = {k: kwargs.pop(k) for k in ("project", "source_root", "manifest") if k in kwargs}
        args = ["verify", "--receipt", str(response_path)]
        if not omit_event:
            args += ["--event", event]
        return self.run_loader(*args, *self.contract_args(**kwargs), *extra, **run_kwargs)

    def legacy_load(self, name="legacy.json", **run_kwargs):
        code, payload = self.run_loader("load", "--event", "worker.dispatch", **run_kwargs)
        return code, payload, self.save(name, payload)

    @staticmethod
    def doc_content(payload, doc_id):
        return next(doc["content"] for doc in payload["documents"] if doc["id"] == doc_id)

    @staticmethod
    def body_bytes(payload):
        return sum(len(doc["content"].encode("utf-8")) for doc in payload["documents"])

    def assert_rejected(self, result, code):
        rc, payload = result
        self.assertNotEqual(rc, 0, payload)
        self.assertFalse(payload.get("ok"), payload)
        self.assertEqual(payload.get("error"), code, payload)
        return payload

    def make_source_tree(self) -> tuple[Path, Path]:
        """agents.md 등을 임의로 바꿔도 되는 임시 source root와 manifest 사본."""
        root = self.tmp / "src"
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        event = next(e for e in manifest["events"] if e["id"] == "worker.dispatch")
        for doc in event["required_docs"]:
            rel = doc["source"].replace("{source_root}/", "")
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / rel, target)
        agent_dir = root / "opal" / "agents" / "opal-be-agent"
        agent_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / "opal" / "agents" / "opal-be-agent" / "AGENT.md", agent_dir / "AGENT.md")
        manifest_path = root / "opal" / "core" / "references" / "events.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(MANIFEST, manifest_path)
        return root, manifest_path

    def manifest_copy(self, name, *, supported=(2,), legacy_accepted=True) -> Path:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        event = next(e for e in manifest["events"] if e["id"] == "worker.dispatch")
        event["contract"] = {"current": 2, "supported": list(supported), "legacy_accepted": legacy_accepted}
        path = self.tmp / name
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return path


class ResponseShapeTest(ContractBase):
    """S-1: 응답 중복 제거와 response_version 2."""

    def _assert_deduplicated(self, payload, event_id):
        self.assertEqual(payload.get("response_version"), 2)
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        declared = next(e for e in manifest["events"] if e["id"] == event_id)
        self.assertEqual([d["id"] for d in payload["required_documents"]], [d["id"] for d in declared["required_docs"]])
        for entry in payload["required_documents"] + payload["optional_documents"]:
            self.assertNotIn("content", entry)
            self.assertEqual(sorted(entry), ["bytes", "id", "path", "sha256", "token"])
        for doc in payload["documents"]:
            self.assertIsInstance(doc.get("content"), str)
        ids = [doc["id"] for doc in payload["documents"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(payload["payload_bytes"], self.body_bytes(payload))
        required_ids = [d["id"] for d in payload["required_documents"]]
        self.assertEqual(required_ids, [d["id"] for d in declared["required_docs"]])
        raw = json.dumps(payload, ensure_ascii=False)
        for doc in payload["documents"]:
            if len(doc["content"]) > 200:
                self.assertEqual(raw.count(json.dumps(doc["content"], ensure_ascii=False)), 1, doc["id"])

    def test_standard_events_load_with_single_body_copy(self):
        for event_id in EVENT_IDS:
            with self.subTest(event=event_id):
                code, payload = self.run_loader("load", "--event", event_id, project=REPO_ROOT)
                self.assertEqual(code, 0, payload)
                self._assert_deduplicated(payload, event_id)

    def test_worker_dispatch_new_contract_single_body_copy(self):
        _, payload = self.new_load()
        self._assert_deduplicated(payload, "worker.dispatch")
        self.assertEqual(payload["receipt"]["schema_version"], 2)

    def test_other_events_keep_receipt_schema_version_one(self):
        code, payload = self.run_loader("load", "--event", "stage.plan", project=REPO_ROOT)
        self.assertEqual(payload["receipt"]["schema_version"], 1)


class AgentSelectionLoadTest(ContractBase):
    """S-2: worker.dispatch 선별 로드."""

    @classmethod
    def legacy_reference(cls):
        return None

    def setUp(self):
        super().setUp()
        code, legacy, _ = self.legacy_load()
        self.assertEqual(code, 0, legacy)
        self.legacy = legacy
        self.legacy_registry = self.doc_content(legacy, "agent-registry")
        self.legacy_total = self.body_bytes(legacy)

    def test_general_agents_get_single_entry_and_smaller_body(self):
        for agent in GENERAL_AGENTS:
            with self.subTest(agent=agent):
                _, payload = self.new_load(agent=agent)
                registry = self.doc_content(payload, "agent-registry")
                self.assertEqual(_agent_headings(registry), {agent})
                for forbidden in ("에이전트 추가 가이드", "향후 추가 에이전트", "BaseRepository"):
                    self.assertNotIn(forbidden, registry)
                self.assertLess(self.body_bytes(payload), self.legacy_total)
                self.assertLess(self.body_bytes(payload), BASELINE_FULL_BYTES)
                self.assertIsInstance(payload.get("selection"), dict)
                self.assertIsInstance(payload["receipt"].get("selection"), dict)

    def test_untouched_sections_stay_byte_identical(self):
        start = self.legacy_registry.index("## 전문 에이전트 매핑 테이블")
        end = self.legacy_registry.index("## web-to-markdown 에이전트")
        preserved = self.legacy_registry[start:end]
        head = self.legacy_registry[: self.legacy_registry.index("## opal-pilot 에이전트")]
        for agent in GENERAL_AGENTS:
            with self.subTest(agent=agent):
                _, payload = self.new_load(agent=agent)
                registry = self.doc_content(payload, "agent-registry")
                self.assertIn(preserved, registry)
                self.assertTrue(registry.startswith(head))

    def test_full_entry_agents_keep_all_entries_and_drop_only_excluded(self):
        expected = _agent_headings(self.legacy_registry)
        for agent in FULL_AGENTS:
            with self.subTest(agent=agent):
                _, payload = self.new_load(agent=agent)
                registry = self.doc_content(payload, "agent-registry")
                self.assertEqual(_agent_headings(registry), expected)
                self.assertNotIn("## 에이전트 추가 가이드", registry)
                self.assertNotIn("## 향후 추가 에이전트", registry)
                self.assertNotIn("BaseRepository", registry)

    def test_other_documents_are_full_text_for_every_call(self):
        for agent in GENERAL_AGENTS + FULL_AGENTS:
            _, payload = self.new_load(agent=agent)
            for doc_id in ("dispatch-process", "context-injection", "observability"):
                with self.subTest(agent=agent, doc=doc_id):
                    self.assertEqual(self.doc_content(payload, doc_id), self.doc_content(self.legacy, doc_id))

    def test_project_only_agent_reports_absent_target_entry(self):
        agent_dir = self.project / ".opal" / "agents" / "mams-custom-agent"
        agent_dir.mkdir(parents=True)
        (agent_dir / "AGENT.md").write_text("# custom\n", encoding="utf-8")
        _, payload = self.new_load(agent="mams-custom-agent")
        self.assertEqual(payload["selection"].get("target_entry"), "absent")
        self.assertEqual(_agent_headings(self.doc_content(payload, "agent-registry")), set())

    def test_unknown_agent_is_not_found(self):
        rc, payload = self.run_loader("load", "--event", "worker.dispatch", *self.contract_args(agent="no-such-agent"))
        self.assert_rejected((rc, payload), "agent_not_found")


class ArgumentGateTest(ContractBase):
    """S-4: 호출 묶음 인자와 verify 거부 코드."""

    def setUp(self):
        super().setUp()
        self.role_doc = self.tmp / "role-a.md"
        self.role_doc.write_text("role a\n", encoding="utf-8")
        self.role_doc_b = self.tmp / "role-b.md"
        self.role_doc_b.write_text("role b\n", encoding="utf-8")

    def test_matching_arguments_verify_ok(self):
        resp, _ = self.new_load()
        rc, payload = self.verify(resp)
        self.assertEqual(rc, 0, payload)
        self.assertTrue(payload["ok"])

    def test_other_agent_rejected(self):
        resp, _ = self.new_load()
        self.assert_rejected(self.verify(resp, agent="opal-test-agent"), "dispatch_target_mismatch")

    def test_other_role_rejected(self):
        resp, _ = self.new_load()
        self.assert_rejected(self.verify(resp, role="reviewer"), "dispatch_role_mismatch")

    def test_role_doc_difference_rejected(self):
        resp, _ = self.new_load(role_doc=self.role_doc)
        self.assert_rejected(self.verify(resp, role_doc=self.role_doc_b), "dispatch_role_mismatch")
        self.assert_rejected(self.verify(resp), "dispatch_role_mismatch")
        plain, _ = self.new_load("plain.json")
        self.assert_rejected(self.verify(plain, role_doc=self.role_doc), "dispatch_role_mismatch")
        rc, payload = self.verify(resp, role_doc=self.role_doc)
        self.assertEqual(rc, 0, payload)

    def test_other_dispatch_id_rejected(self):
        resp, _ = self.new_load()
        self.assert_rejected(self.verify(resp, dispatch_id=ID2), "dispatch_id_mismatch")

    def test_each_missing_argument_rejected_by_verify_and_load(self):
        resp, _ = self.new_load()
        for name in ("agent", "role", "dispatch-id", "contract-version"):
            with self.subTest(op="verify", omitted=name):
                payload = self.assert_rejected(self.verify(resp, omit=(name,)), "contract_args_missing")
                text = json.dumps(payload, ensure_ascii=False).replace("_", "-")
                self.assertIn(name, text)
            with self.subTest(op="load", omitted=name):
                result = self.run_loader("load", "--event", "worker.dispatch", *self.contract_args(omit=(name,)))
                payload = self.assert_rejected(result, "contract_args_missing")
                self.assertIn(name, json.dumps(payload, ensure_ascii=False).replace("_", "-"))

    def test_invalid_format_rejected(self):
        resp, _ = self.new_load()
        self.assert_rejected(self.verify(resp, role="A b"), "contract_arg_invalid")
        self.assert_rejected(self.verify(resp, dispatch_id="abc"), "contract_arg_invalid")
        for bad in ({"role": "A b"}, {"dispatch_id": "abc"}):
            with self.subTest(load=bad):
                result = self.run_loader("load", "--event", "worker.dispatch", *self.contract_args(**bad))
                self.assert_rejected(result, "contract_arg_invalid")

    def test_receipt_object_without_response_body_rejected(self):
        _, payload = self.new_load()
        only_receipt = self.save("receipt-only.json", payload["receipt"])
        self.assert_rejected(self.verify(only_receipt), "response_body_missing")

    def test_roles_do_not_accept_each_others_receipts(self):
        verifier_doc = self.tmp / "verifier.md"
        verifier_doc.write_text("verifier\n", encoding="utf-8")
        reviewer_doc = self.tmp / "reviewer.md"
        reviewer_doc.write_text("reviewer\n", encoding="utf-8")
        ver, _ = self.new_load("ver.json", role="verifier", role_doc=verifier_doc, dispatch_id=ID1)
        rev, _ = self.new_load("rev.json", role="reviewer", role_doc=reviewer_doc, dispatch_id=ID2)
        self.assertEqual(self.verify(ver, role="verifier", role_doc=verifier_doc, dispatch_id=ID1)[0], 0)
        self.assertEqual(self.verify(rev, role="reviewer", role_doc=reviewer_doc, dispatch_id=ID2)[0], 0)
        for result in (
            self.verify(rev, role="verifier", role_doc=verifier_doc, dispatch_id=ID1),
            self.verify(ver, role="reviewer", role_doc=reviewer_doc, dispatch_id=ID2),
        ):
            rc, payload = result
            self.assertNotEqual(rc, 0)
            self.assertIn(payload.get("error"), {"dispatch_role_mismatch", "dispatch_id_mismatch"})


class ContractNotDeclaredTest(ContractBase):
    """GC-001/GC-005: 계약 미선언 이벤트 + 계약 인자 거부, 형식 검사의 개행 거부."""

    def undeclared_manifest(self) -> Path:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        event = next(e for e in manifest["events"] if e["id"] == "worker.dispatch")
        event.pop("contract", None)
        event.pop("selection", None)
        path = self.tmp / "undeclared-manifest.json"
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def test_verify_with_contract_args_on_undeclared_receipt_rejected(self):
        manifest = self.undeclared_manifest()
        code, payload = self.run_loader("load", "--event", "worker.dispatch", manifest=manifest)
        self.assertEqual(code, 0, payload)
        resp = self.save("undeclared.json", payload)
        self.assert_rejected(self.verify(resp, dispatch_id="dsp-NOT-THE-REAL-ONE", manifest=manifest), "contract_not_declared")

    def reduced_manifest(self) -> Path:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        event = next(e for e in manifest["events"] if e["id"] == "worker.dispatch")
        event.pop("selection", None)
        event["required_docs"] = event["required_docs"][:1]
        path = self.tmp / "reduced-manifest.json"
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def test_verify_without_manifest_rejects_receipt_from_copied_manifest(self):
        manifest = self.reduced_manifest()
        code, payload = self.run_loader("load", "--event", "worker.dispatch", *self.contract_args(), manifest=manifest)
        self.assertEqual(code, 0, payload)
        resp = self.save("reduced.json", payload)
        rejected = self.verify(resp)
        self.assert_rejected(rejected, "stale_receipt")
        self.assertIn(str(manifest), json.dumps(rejected[1], ensure_ascii=False))

    def test_verify_with_same_copied_manifest_passes(self):
        manifest = self.reduced_manifest()
        code, payload = self.run_loader("load", "--event", "worker.dispatch", *self.contract_args(), manifest=manifest)
        self.assertEqual(code, 0, payload)
        resp = self.save("reduced.json", payload)
        code, result = self.verify(resp, manifest=manifest)
        self.assertEqual(code, 0, result)
        self.assertTrue(result["ok"], result)

    def test_default_boundary_receipt_still_verifies(self):
        for event in ("pilot.start",):
            code, payload = self.run_loader("load", "--event", event)
            self.assertEqual(code, 0, payload)
            resp = self.save(f"{event}.json", payload)
            code, result = self.run_loader("verify", "--receipt", str(resp), "--event", event)
            self.assertEqual(code, 0, result)

    def test_load_and_measure_with_contract_args_rejected_on_undeclared_event(self):
        self.assert_rejected(
            self.run_loader("load", "--event", "pilot.start", *self.contract_args()), "contract_not_declared"
        )
        manifest = self.undeclared_manifest()
        self.assert_rejected(
            self.run_loader("load", "--event", "worker.dispatch", *self.contract_args(), manifest=manifest),
            "contract_not_declared",
        )
        rc, payload = self.run_loader("measure", "--event", "pilot.start", *self.contract_args())
        self.assertFalse(payload.get("ok"), payload)
        self.assertEqual(payload.get("error"), "contract_not_declared", payload)

    def test_trailing_newline_in_role_and_dispatch_id_rejected(self):
        resp, _ = self.new_load()
        self.assert_rejected(self.verify(resp, role="builder\n"), "contract_arg_invalid")
        self.assert_rejected(self.verify(resp, dispatch_id=ID1 + "\n"), "contract_arg_invalid")


class TamperDetectionTest(ContractBase):
    """S-5: 본문·에이전트 문서·출처·문서·매니페스트 변조."""

    def _mutated_response(self, payload):
        mutated = copy.deepcopy(payload)
        mutated["documents"][0]["content"] += "x"
        return self.save("mutated.json", mutated)

    def test_content_tamper_is_body_hash_mismatch(self):
        _, payload = self.new_load()
        self.assert_rejected(self.verify(self._mutated_response(payload)), "body_hash_mismatch")

    def test_unchanged_passes(self):
        resp, _ = self.new_load()
        self.assertEqual(self.verify(resp)[0], 0)

    def test_agent_document_change_is_agent_changed(self):
        agent_dir = self.project / ".opal" / "agents" / "opal-be-agent"
        agent_dir.mkdir(parents=True)
        agent_file = agent_dir / "AGENT.md"
        agent_file.write_text("project copy v1\n", encoding="utf-8")
        resp, _ = self.new_load()
        self.assertEqual(self.verify(resp)[0], 0)
        agent_file.write_text("project copy v2\n", encoding="utf-8")
        self.assert_rejected(self.verify(resp), "agent_changed")

    def test_origin_switch_framework_to_project(self):
        resp, payload = self.new_load()
        self.assertEqual(payload["receipt"]["agent"]["origin"], "framework")
        agent_dir = self.project / ".opal" / "agents" / "opal-be-agent"
        agent_dir.mkdir(parents=True)
        (agent_dir / "AGENT.md").write_text("project copy\n", encoding="utf-8")
        body = self.assert_rejected(self.verify(resp), "agent_changed")
        text = json.dumps(body, ensure_ascii=False)
        self.assertIn("framework", text)
        self.assertIn("project", text)

    def test_origin_switch_project_to_framework(self):
        agent_dir = self.project / ".opal" / "agents" / "opal-be-agent"
        agent_dir.mkdir(parents=True)
        agent_file = agent_dir / "AGENT.md"
        agent_file.write_text("project copy\n", encoding="utf-8")
        resp, payload = self.new_load()
        self.assertEqual(payload["receipt"]["agent"]["origin"], "project")
        agent_file.unlink()
        body = self.assert_rejected(self.verify(resp), "agent_changed")
        text = json.dumps(body, ensure_ascii=False)
        self.assertIn("framework", text)
        self.assertIn("project", text)

    def test_registry_change_is_hash_or_stale(self):
        root, manifest = self.make_source_tree()
        resp, _ = self.new_load(source_root=root, manifest=manifest)
        self.assertEqual(self.verify(resp, source_root=root, manifest=manifest)[0], 0)
        registry = root / "opal" / "core" / "references" / "agents.md"
        registry.write_text(registry.read_text(encoding="utf-8") + "\n변경\n", encoding="utf-8")
        rc, body = self.verify(resp, source_root=root, manifest=manifest)
        self.assertNotEqual(rc, 0)
        self.assertIn(body.get("error"), {"document_hash_mismatch", "stale_receipt"})

    def test_manifest_change_is_stale_receipt(self):
        root, manifest = self.make_source_tree()
        resp, _ = self.new_load(source_root=root, manifest=manifest)
        manifest.write_text(manifest.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        self.assert_rejected(self.verify(resp, source_root=root, manifest=manifest), "stale_receipt")


class LegacyCompatibilityTest(ContractBase):
    """S-6: 구형 호출 호환."""

    def test_legacy_load_is_full_with_warning(self):
        code, payload, _ = self.legacy_load()
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["receipt"]["schema_version"], 1)
        self.assertEqual(payload.get("contract"), "legacy")
        self.assertIn("legacy_dispatch_contract", [w.get("code") for w in payload.get("warnings", [])])
        self.assertEqual(self.doc_content(payload, "agent-registry"), AGENTS_MD.read_text(encoding="utf-8"))

    def test_legacy_receipt_verifies_without_args(self):
        _, _, resp = self.legacy_load()
        rc, payload = self.run_loader("verify", "--receipt", str(resp), "--event", "worker.dispatch")
        self.assertEqual(rc, 0, payload)
        self.assertTrue(payload.get("legacy_verified"))
        self.assertEqual(payload.get("contract"), "legacy")
        self.assertIn("legacy_dispatch_contract", [w.get("code") for w in payload.get("warnings", [])])

    def test_legacy_receipt_with_contract_args_is_contract_mismatch(self):
        _, _, resp = self.legacy_load()
        self.assert_rejected(self.verify(resp), "contract_mismatch")

    def test_new_receipt_without_args_is_args_missing(self):
        resp, _ = self.new_load()
        rc, payload = self.run_loader("verify", "--receipt", str(resp), "--event", "worker.dispatch")
        self.assert_rejected((rc, payload), "contract_args_missing")

    def test_partial_args_load_rejected(self):
        for args in (["--agent", "opal-be-agent"], ["--contract-version", "2"], ["--role", "builder", "--dispatch-id", ID1]):
            with self.subTest(args=args):
                result = self.run_loader("load", "--event", "worker.dispatch", *args)
                self.assert_rejected(result, "contract_args_missing")


class ContractVersionManifestTest(ContractBase):
    """S-7: supported / legacy_accepted 선언."""

    def test_unsupported_version_rejected_with_reload_guidance(self):
        manifest = self.manifest_copy("m-accept.json")
        result = self.run_loader("load", "--event", "worker.dispatch", *self.contract_args(version="3"), manifest=manifest)
        body = self.assert_rejected(result, "unsupported_contract_version")
        self.assertIn("재로드", json.dumps(body, ensure_ascii=False))
        resp, _ = self.new_load(manifest=manifest)
        self.assert_rejected(self.verify(resp, version="3", manifest=manifest), "unsupported_contract_version")

    def test_legacy_rejected_when_not_accepted(self):
        accept = self.manifest_copy("m-accept.json", legacy_accepted=True)
        reject = self.manifest_copy("m-reject.json", legacy_accepted=False)
        code, legacy_payload, _ = self.legacy_load(manifest=accept)
        self.assertEqual(code, 0, legacy_payload)
        # 구형 receipt를 거부 사본의 매니페스트에 묶어 해시 불일치가 아닌 정책 거부만 보게 한다.
        rebound = copy.deepcopy(legacy_payload)
        rebound["receipt"]["manifest_path"] = str(reject)
        rebound["receipt"]["manifest_sha256"] = hashlib.sha256(reject.read_bytes()).hexdigest()
        resp = self.save("legacy-rebound.json", rebound)
        self.assert_rejected(self.run_loader("load", "--event", "worker.dispatch", manifest=reject), "legacy_dispatch_rejected")
        result = self.run_loader("verify", "--receipt", str(resp), "--event", "worker.dispatch", manifest=reject)
        self.assert_rejected(result, "legacy_receipt_rejected")

    def test_new_contract_still_works_when_legacy_rejected(self):
        reject = self.manifest_copy("m-reject.json", legacy_accepted=False)
        resp, _ = self.new_load(manifest=reject)
        rc, payload = self.verify(resp, manifest=reject)
        self.assertEqual(rc, 0, payload)
        self.assertTrue(payload["ok"])


class LegacyLedgerTest(ContractBase):
    """S-8: 구형 호출 원장과 legacy-report."""

    def _three_legacy_calls(self):
        code, load1, resp = self.legacy_load(now=LEGACY_TS[0])
        self.assertEqual(code, 0, load1)
        rc, ver = self.run_loader("verify", "--receipt", str(resp), "--event", "worker.dispatch", now=LEGACY_TS[1])
        self.assertEqual(rc, 0, ver)
        code, load2, _ = self.legacy_load("legacy2.json", now=LEGACY_TS[2])
        self.assertEqual(code, 0, load2)

    def _report(self, *args):
        rc, payload = self.run_loader("legacy-report", *args)
        self.assertEqual(rc, 0, payload)
        return payload

    def test_ledger_lines_and_report_windows(self):
        self._three_legacy_calls()
        lines = [json.loads(line) for line in self.ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.assertEqual([line["ts"] for line in lines], list(LEGACY_TS))
        self.assertEqual([line["op"] for line in lines], ["load", "verify", "load"])
        for line in lines:
            self.assertEqual(line["event"], "worker.dispatch")
            self.assertIn("project_root", line)

        whole = self._report()
        self.assertEqual(whole["count"], 3)
        self.assertEqual(whole["first_ts"], LEGACY_TS[0])
        self.assertEqual(whole["last_ts"], LEGACY_TS[2])
        self.assertEqual(whole["by_op"], {"load": 2, "verify": 1})

        since = self._report("--since", "2026-10-01T12:00:00Z")
        self.assertEqual(since["count"], 2)
        self.assertEqual(since["first_ts"], LEGACY_TS[1])
        self.assertEqual(since["by_op"], {"load": 1, "verify": 1})

        until = self._report("--until", "2026-10-02T12:00:00Z")
        self.assertEqual(until["count"], 2)
        self.assertEqual(until["last_ts"], LEGACY_TS[1])

        after = self._report("--since", "2026-10-04T00:00:00Z")
        self.assertEqual(after["count"], 0)

    def test_report_without_ledger_is_zero(self):
        self.assertEqual(self._report()["count"], 0)

    def test_new_contract_calls_are_not_recorded(self):
        resp, _ = self.new_load()
        self.assertEqual(self.verify(resp)[0], 0)
        self.assertFalse(self.ledger.exists() and self.ledger.read_text(encoding="utf-8").strip())
        self.assertEqual(self._report()["count"], 0)

    def test_ledger_write_failure_warns_without_blocking(self):
        blocker = self.tmp / "not-a-dir"
        blocker.write_text("file", encoding="utf-8")
        code, payload = self.run_loader("load", "--event", "worker.dispatch", ledger=blocker / "ledger.jsonl")
        self.assertEqual(code, 0, payload)
        self.assertTrue(payload["ok"])
        self.assertIn("ledger_write_failed", [w.get("code") for w in payload.get("warnings", [])])


class MeasureAndLoadReportTest(ContractBase):
    """S-9: measure / load-report."""

    @staticmethod
    def canonical_size(payload: dict) -> int:
        zeroed = copy.deepcopy(payload)
        zeroed["response_bytes"] = 0
        if isinstance(zeroed.get("receipt"), dict) and "response_bytes" in zeroed["receipt"]:
            zeroed["receipt"]["response_bytes"] = 0
        return len(json.dumps(zeroed, ensure_ascii=False, sort_keys=True).encode("utf-8"))

    def test_measure_reports_separate_byte_fields(self):
        _, loaded = self.new_load(agent="opal-be-agent")
        rc, measured = self.run_loader("measure", "--event", "worker.dispatch", *self.contract_args(agent="opal-be-agent"))
        self.assertEqual(rc, 0, measured)
        for field in ("payload_bytes", "source_payload_bytes", "response_bytes"):
            self.assertIsInstance(measured.get(field), int, field)
        self.assertEqual(measured["payload_bytes"], loaded["payload_bytes"])
        self.assertLess(measured["payload_bytes"], measured["source_payload_bytes"])
        self.assertEqual(measured["response_bytes"], loaded["response_bytes"])
        self.assertEqual(loaded["response_bytes"], self.canonical_size(loaded))
        self.assertFalse([key for key in measured if "cost" in key])

    def test_load_report_dedupes_by_load_id_and_skips_verify_results(self):
        be_path, be = self.new_load("be.json", agent="opal-be-agent")
        test_path, tst = self.new_load("test.json", agent="opal-test-agent", dispatch_id=ID2)
        rc, verified = self.verify(be_path)
        self.assertEqual(rc, 0, verified)
        verify_file = self.save("verify-result.json", verified)
        rc, report = self.run_loader(
            "load-report", "--receipt", str(be_path), str(test_path), str(be_path), str(verify_file)
        )
        self.assertEqual(rc, 0, report)
        self.assertEqual(report["payload_bytes"], be["payload_bytes"] + tst["payload_bytes"])
        self.assertEqual(report["response_bytes"], be["response_bytes"] + tst["response_bytes"])
        self.assertNotEqual(report["payload_bytes"], report["response_bytes"])
        for key in report:
            self.assertNotIn("cost", key)
            self.assertNotIn("elapsed", key)
            self.assertNotIn("seconds", key)


if __name__ == "__main__":
    unittest.main()
