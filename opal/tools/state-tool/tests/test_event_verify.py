"""
@header {
  "module": "test_event_verify",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool event-verify 공개 CLI의 성공·누락·wrong-event·stale receipt 계약 검증",
  "exports": [],
  "depends": ["state_tool", "event_loader"]
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
STATE_TOOL = REPO_ROOT / "opal" / "tools" / "state-tool" / "state_tool.py"
EVENT_LOADER = REPO_ROOT / "opal" / "tools" / "event-loader" / "event_loader.py"


class EventVerifyCliTest(unittest.TestCase):
    def _load(self, event: str, receipt_path: Path) -> dict:
        completed = subprocess.run(
            [
                sys.executable,
                str(EVENT_LOADER),
                "load",
                "--event",
                event,
                "--source-root",
                str(REPO_ROOT),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json.loads(completed.stdout)
        receipt_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return payload

    def _verify(self, event: str, receipt_path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(STATE_TOOL),
                "event-verify",
                "--event",
                event,
                "--receipt",
                str(receipt_path),
                "--source-root",
                str(REPO_ROOT),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_current_receipt_passes_without_task_state(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "pilot-start.json"
            loaded = self._load("pilot.start", receipt)

            completed = self._verify("pilot.start", receipt)
            payload = json.loads(completed.stdout)

            self.assertEqual(completed.returncode, 0)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["event"], "pilot.start")
            self.assertEqual(payload["via"], "state-tool event-verify")
            self.assertEqual(payload["payload_bytes"], loaded["payload_bytes"])

    def test_missing_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            completed = self._verify("stage.execute", Path(directory) / "missing.json")
            payload = json.loads(completed.stdout)

            self.assertEqual(completed.returncode, 1)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"], "receipt_not_found")

    def test_wrong_event_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "stage.json"
            self._load("stage.execute", receipt)

            completed = self._verify("stage.test", receipt)
            payload = json.loads(completed.stdout)

            self.assertEqual(completed.returncode, 1)
            self.assertEqual(payload["error"], "event_mismatch")

    def test_stale_manifest_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "stage.json"
            loaded = self._load("stage.execute", receipt)
            loaded["receipt"]["manifest_sha256"] = "0" * 64
            receipt.write_text(json.dumps(loaded, ensure_ascii=False), encoding="utf-8")

            completed = self._verify("stage.execute", receipt)
            payload = json.loads(completed.stdout)

            self.assertEqual(completed.returncode, 1)
            self.assertEqual(payload["error"], "stale_receipt")


if __name__ == "__main__":
    unittest.main()
