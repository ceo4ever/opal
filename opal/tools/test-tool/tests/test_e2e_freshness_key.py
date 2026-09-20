"""T06 — six-part E2E freshness key and reuse eligibility."""

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


class FreshnessKeyTests(unittest.TestCase):
    def test_key_contains_all_six_contract_components_and_is_order_stable(self):
        first = freshness.compose_key(
            journey_hash="journey",
            fragment_hashes={"login": "a", "cart": "b"},
            surface_id="checkout",
            target_commit="abc123",
            driver="ego-lite",
            session_mode="standalone",
            achieved_fidelity="real-usage",
        )
        reordered = freshness.compose_key(
            journey_hash="journey",
            fragment_hashes={"cart": "b", "login": "a"},
            surface_id="checkout",
            target_commit="abc123",
            driver="ego-lite",
            session_mode="standalone",
            achieved_fidelity="real-usage",
        )
        self.assertEqual(first, reordered)
        self.assertEqual(
            set(first["components"]),
            {
                "journey_hash", "fragment_hashes", "surface_id",
                "target_commit", "driver_identity", "achieved_fidelity",
            },
        )

    def test_changed_selected_driver_blocks_order_file_bypass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_json = root / "artifacts" / "old" / "run.json"
            run_json.parent.mkdir(parents=True)
            run_json.write_text(
                json.dumps({"status": "pass", "evidence_complete": True}), encoding="utf-8"
            )
            path = root / ".e2e" / "freshness.json"
            source = {
                "journey_hash": "journey", "fragment_hashes": {"login": "a"},
                "surface_id": "checkout",
            }
            freshness.record_pass(
                path,
                source=source,
                target_commit="commit",
                driver_identity={"driver": "ego-lite", "session_mode": "standalone"},
                achieved_fidelity="real-usage",
                run_id="old",
                run_json_path=str(run_json),
            )
            reusable = freshness.find_reusable(
                path,
                source=source,
                target_commit="commit",
                driver_identity={"driver": "cmux", "session_mode": "owned-surface"},
                required_fidelity="mock",
            )
            self.assertIsNone(reusable)

    def test_missing_evidence_and_insufficient_fidelity_are_not_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "freshness.json"
            evidence = root / "run.json"
            evidence.write_text(
                json.dumps({"status": "pass", "evidence_complete": True}), encoding="utf-8"
            )
            source = {
                "journey_hash": "j", "fragment_hashes": {}, "surface_id": "surface"
            }
            identity = {"driver": "api", "session_mode": None}
            freshness.record_pass(
                path, source=source, target_commit="c", driver_identity=identity,
                achieved_fidelity="real-http", run_id="run", run_json_path=str(evidence),
            )
            self.assertIsNone(freshness.find_reusable(
                path, source=source, target_commit="c", driver_identity=identity,
                required_fidelity="real-usage",
            ))
            evidence.unlink()
            self.assertIsNone(freshness.find_reusable(
                path, source=source, target_commit="c", driver_identity=identity,
                required_fidelity="mock",
            ))


if __name__ == "__main__":
    unittest.main()
