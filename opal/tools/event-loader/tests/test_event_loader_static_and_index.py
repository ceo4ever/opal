"""
@header {
  "module": "test_event_loader_static_and_index",
  "layer": "test",
  "domain": "opal-tools",
  "description": "static-check의 worker.dispatch 계약 인자·게이트 대상 검사, manifest contract/selection 형식 검증, agent-index 출력을 CLI 공개 출력으로 검증 (S-10, D-14, D-15)",
  "exports": [],
  "depends": ["event_loader"]
}
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[4]
LOADER = REPO_ROOT / "opal" / "tools" / "event-loader" / "event_loader.py"
MANIFEST = REPO_ROOT / "opal" / "core" / "references" / "events.json"
FULL = "--contract-version 2 --agent opal-be-agent --role builder --dispatch-id disp-00000001"
FLAG = "--require-default-manifest"


def run(*args: str) -> tuple[int, dict]:
    done = subprocess.run(
        [sys.executable, str(LOADER), *args, "--source-root", str(REPO_ROOT), "--project-root", str(REPO_ROOT)],
        capture_output=True,
        text=True,
        check=False,
    )
    return done.returncode, json.loads(done.stdout)


class StaticCheckDispatchTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def check(self, relative: str, text: str) -> list[dict]:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        _, payload = run("static-check", "--event", "worker.dispatch", "--path", str(path))
        return payload["violations"]

    def test_missing_contract_args_listed(self):
        found = self.check(
            "doc.md",
            "worker.dispatch event-loader\nrun.sh load --event worker.dispatch --agent x\n",
        )
        hit = [v for v in found if v["code"] == "dispatch_contract_args_missing"]
        self.assertEqual(len(hit), 1, found)
        self.assertEqual(hit[0]["missing"], ["--contract-version", "--role", "--dispatch-id"])

    def test_full_args_pass(self):
        found = self.check("doc.md", f"worker.dispatch event-loader\nrun.sh verify --receipt r --event worker.dispatch {FULL} {FLAG}\n")
        self.assertEqual([v for v in found if v["code"].startswith("dispatch_")], [])

    def test_verify_line_without_default_manifest_flag_flagged(self):
        found = self.check("doc.md", f"worker.dispatch event-loader\nrun.sh verify --receipt r --event worker.dispatch {FULL}\n")
        hit = [v for v in found if v["code"] == "dispatch_gate_default_manifest_missing"]
        self.assertEqual(len(hit), 1, found)
        self.assertEqual(hit[0]["line"], 2)

    def test_load_line_is_not_subject_to_default_manifest_flag(self):
        found = self.check("doc.md", f"worker.dispatch event-loader\nrun.sh load --event worker.dispatch {FULL}\n")
        self.assertEqual([v for v in found if v["code"].startswith("dispatch_gate_")], [])

    def test_load_and_verify_on_one_line_passes_when_flag_present(self):
        text = f"worker.dispatch event-loader\n`load --event worker.dispatch {FULL}` 후 `verify --event worker.dispatch {FULL} {FLAG}`\n"
        found = self.check("doc.md", text)
        self.assertEqual([v for v in found if v["code"].startswith("dispatch_gate_")], [])

    def test_manifest_override_args_flagged(self):
        for override in ("--manifest m.json", "--deployed-root /x", "--source-root /y"):
            found = self.check("doc.md", f"worker.dispatch event-loader\nrun.sh verify --receipt r --event worker.dispatch {FULL} {FLAG} {override}\n")
            codes = [v["code"] for v in found]
            self.assertIn("dispatch_gate_manifest_override", codes, (override, found))
            self.assertNotIn("dispatch_gate_default_manifest_missing", codes)

    def test_gate_agent_name_must_match_folder(self):
        text = f"worker.dispatch event-loader\nrun.sh verify --receipt r --event worker.dispatch {FULL} {FLAG}\n"
        mismatch = self.check("agents/opal-fe-agent/AGENT.md", text)
        self.assertIn("dispatch_gate_agent_mismatch", [v["code"] for v in mismatch])
        placeholder = self.check("agents/opal-fe-agent/AGENT.md", text.replace("opal-be-agent", "<agent>"))
        self.assertNotIn("dispatch_gate_agent_mismatch", [v["code"] for v in placeholder])
        own = self.check("agents/opal-be-agent/AGENT.md", text)
        self.assertNotIn("dispatch_gate_agent_mismatch", [v["code"] for v in own])


class ManifestShapeTest(unittest.TestCase):
    def violations(self, mutate) -> list[str]:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        event = next(e for e in manifest["events"] if e["id"] == "worker.dispatch")
        mutate(event)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.json"
            path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            _, payload = run("static-check", "--manifest-only", "--manifest", str(path))
        return [v.get("code") for v in payload.get("violations", [])] or [payload.get("error")]

    def test_repository_manifest_is_valid(self):
        self.assertEqual(run("static-check", "--manifest-only")[0], 0)

    def test_contract_shape_rejected(self):
        self.assertIn("contract_invalid", self.violations(lambda e: e.update(contract={"current": 2, "supported": [1], "legacy_accepted": True})))
        self.assertIn("contract_invalid", self.violations(lambda e: e.update(contract={"current": 2, "supported": [2], "legacy_accepted": "yes"})))

    def test_selection_shape_rejected(self):
        self.assertIn("selection_invalid", self.violations(lambda e: e["selection"].update(document="nope")))
        self.assertIn("selection_invalid", self.violations(lambda e: e["selection"].update(mode="all")))
        self.assertIn("selection_invalid", self.violations(lambda e: e["selection"].update(exclude_sections="x")))


class AgentIndexTest(unittest.TestCase):
    def test_index_has_only_light_sections_and_agent_names(self):
        rc, payload = run("agent-index")
        self.assertEqual(rc, 0, payload)
        self.assertEqual([s["title"] for s in payload["sections"]], ["전문 에이전트 매핑 테이블", "폴백 규칙", "탐색 경로"])
        self.assertIn("opal-be-agent", payload["agents"])
        for forbidden in ("BaseRepository", "에이전트 추가 가이드", "플랫폼 sub-agent 어댑터"):
            self.assertNotIn(forbidden, payload["content"])


if __name__ == "__main__":
    unittest.main()
