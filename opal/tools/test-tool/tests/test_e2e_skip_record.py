"""T06 — skipped reruns are explicit previous-evidence reuse records."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))

from lib.e2e import freshness  # noqa: E402


class SkipRecordTests(unittest.TestCase):
    def test_reuse_is_appended_without_creating_a_second_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".e2e" / "freshness.json"
            evidence = Path(tmp) / "artifacts" / "pass" / "run.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                json.dumps({"status": "pass", "evidence_complete": True}), encoding="utf-8"
            )
            entry = freshness.record_pass(
                path,
                source={"journey_hash": "j", "fragment_hashes": {}, "surface_id": "s"},
                target_commit="c",
                driver_identity={"driver": "ego-lite", "session_mode": "standalone"},
                achieved_fidelity="real-usage",
                run_id="e2e-20260920-001",
                run_json_path=str(evidence),
            )
            event = freshness.record_reuse(
                path, entry=entry, requested_fidelity="real-http"
            )
            ledger = freshness.load_ledger(path)
            self.assertEqual(len(ledger["entries"]), 1)
            self.assertEqual(len(ledger["events"]), 1)
            self.assertEqual(event["kind"], "evidence_reuse")
            self.assertEqual(event["description"], "이전 증적 재인용")
            self.assertEqual(event["reused_run_id"], "e2e-20260920-001")
            self.assertEqual(event["run_json_path"], str(evidence.resolve()))

    def test_source_identity_changes_only_for_referenced_fragment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            journeys = root / "docs" / "e2e" / "journeys"
            fragments = root / "docs" / "e2e" / "fragments"
            journeys.mkdir(parents=True)
            fragments.mkdir(parents=True)
            journey = journeys / "checkout.md"
            journey.write_text("journey", encoding="utf-8")
            (fragments / "login.md").write_text("login-v1", encoding="utf-8")
            (fragments / "unused.md").write_text("unused-v1", encoding="utf-8")
            scenario = {
                "id": "checkout", "surface_ref": "checkout",
                "journey_source": str(journey), "fragment_ids": ["login"],
            }
            before = freshness.source_identity(scenario, project_root=root)
            (fragments / "unused.md").write_text("unused-v2", encoding="utf-8")
            self.assertEqual(before, freshness.source_identity(scenario, project_root=root))
            (fragments / "login.md").write_text("login-v2", encoding="utf-8")
            self.assertNotEqual(before, freshness.source_identity(scenario, project_root=root))


if __name__ == "__main__":
    unittest.main()
