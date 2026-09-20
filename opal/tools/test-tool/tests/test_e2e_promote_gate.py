"""T07 — docs/e2e promotion is owned by complete test-tool pass evidence."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))

from lib.e2e import promotion  # noqa: E402


class PromotionGateTests(unittest.TestCase):
    def _run_json(self, root: str, **overrides) -> Path:
        path = Path(root) / "run.json"
        payload = {
            "run_id": "e2e-20260920-001",
            "scenario_id": "checkout",
            "status": "pass",
            "exit_code": 0,
            "executed": True,
            "evidence_complete": True,
            "missing_evidence": [],
        }
        payload.update(overrides)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_complete_matching_pass_is_eligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = promotion.evaluate_promotion(
                self._run_json(tmp), journey_id="checkout"
            )
        self.assertTrue(result["ok"])
        self.assertTrue(result["eligible"])
        self.assertEqual(result["reason"], "pass_evidence_verified")

    def test_non_pass_and_incomplete_evidence_are_never_eligible(self):
        cases = (
            ({"status": "fail", "exit_code": 6}, "status_not_pass"),
            ({"exit_code": 6}, "exit_not_pass"),
            ({"evidence_complete": False}, "evidence_incomplete"),
            ({"missing_evidence": ["screenshot"]}, "missing_evidence"),
            ({"missing_evidence": None}, "missing_evidence"),
            ({"executed": False}, "run_not_executed"),
        )
        for overrides, reason in cases:
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as tmp:
                result = promotion.evaluate_promotion(self._run_json(tmp, **overrides))
                self.assertFalse(result["eligible"])
                self.assertEqual(result["reason"], reason)

    def test_unrelated_pass_cannot_promote_another_journey(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = promotion.evaluate_promotion(
                self._run_json(tmp), journey_id="profile-update"
            )
        self.assertFalse(result["eligible"])
        self.assertEqual(result["reason"], "journey_mismatch")

    def test_cli_exit_is_gate_result_and_payload_is_structured(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._run_json(tmp)
            proc = subprocess.run(
                [sys.executable, str(TOOL_ROOT / "test_tool.py"), "e2e", "promote-check",
                 "--journey", "checkout", "--run-json", str(path)],
                capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["command"], "e2e promote-check")
            self.assertTrue(payload["eligible"])

            path = self._run_json(tmp, status="infra_error", exit_code=7)
            proc = subprocess.run(
                [sys.executable, str(TOOL_ROOT / "test_tool.py"), "e2e", "promote-check",
                 "--journey", "checkout", "--run-json", str(path)],
                capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(proc.returncode, 1)
            self.assertFalse(json.loads(proc.stdout)["eligible"])


if __name__ == "__main__":
    unittest.main()
