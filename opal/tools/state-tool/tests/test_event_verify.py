"""
@header {
  "module": "test_event_verify",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool event-verify 공개 CLI의 성공·누락·wrong-event·stale receipt 및 worker.dispatch 계약 인자 전달 검증",
  "exports": [],
  "depends": ["state_tool", "event_loader"]
}
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

# 구형 worker.dispatch 호출이 운영 원장(~/.opal/state)에 기록되지 않도록 임시 원장으로 고정한다.
os.environ["OPAL_EVENT_LOADER_LEDGER"] = str(Path(tempfile.mkdtemp(prefix="opal-verify-test-ledger-")) / "legacy-dispatch.jsonl")

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

    def _load_dispatch(self, receipt_path: Path, dispatch_id: str = "dsp-0123456789") -> None:
        completed = subprocess.run(
            [sys.executable, str(EVENT_LOADER), "load", "--event", "worker.dispatch",
             "--source-root", str(REPO_ROOT), *self._dispatch_args(dispatch_id)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        receipt_path.write_text(completed.stdout, encoding="utf-8")

    @staticmethod
    def _dispatch_args(dispatch_id: str = "dsp-0123456789", skip: str = "") -> list[str]:
        pairs = [("--contract-version", "2"), ("--agent", "opal-be-agent"),
                 ("--role", "builder"), ("--dispatch-id", dispatch_id)]
        return [x for flag, value in pairs if flag != skip for x in (flag, value)]

    def _verify_dispatch(self, receipt_path: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(STATE_TOOL), "event-verify", "--event", "worker.dispatch",
             "--receipt", str(receipt_path), "--source-root", str(REPO_ROOT), *args],
            capture_output=True, text=True, check=False,
        )

    def test_worker_dispatch_contract_args_pass_through(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "dispatch.json"
            self._load_dispatch(receipt)
            completed = self._verify_dispatch(receipt, self._dispatch_args())
            payload = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 0, completed.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["via"], "state-tool event-verify")

    def test_worker_dispatch_missing_arg_error_is_forwarded(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "dispatch.json"
            self._load_dispatch(receipt)
            completed = self._verify_dispatch(receipt, self._dispatch_args(skip="--role"))
            payload = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"], "contract_args_missing")

    def test_worker_dispatch_id_mismatch_is_forwarded(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "dispatch.json"
            self._load_dispatch(receipt)
            completed = self._verify_dispatch(receipt, self._dispatch_args("dsp-9999999999"))
            payload = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertEqual(payload["error"], "dispatch_id_mismatch")

    def test_empty_contract_args_on_legacy_receipt_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "legacy.json"
            self._load("worker.dispatch", receipt)
            completed = self._verify_dispatch(
                receipt,
                ["--agent", "", "--role", "", "--dispatch-id", "", "--contract-version", ""],
            )
            payload = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"], "contract_arg_invalid")

    def test_contract_args_on_undeclared_receipt_rejected_via_state_tool(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = json.loads((REPO_ROOT / "opal" / "core" / "references" / "events.json").read_text(encoding="utf-8"))
            event = next(e for e in manifest["events"] if e["id"] == "worker.dispatch")
            event.pop("contract", None)
            event.pop("selection", None)
            manifest_path = Path(directory) / "events.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            loaded = subprocess.run(
                [sys.executable, str(EVENT_LOADER), "load", "--event", "worker.dispatch",
                 "--source-root", str(REPO_ROOT), "--manifest", str(manifest_path)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(loaded.returncode, 0, loaded.stdout + loaded.stderr)
            receipt = Path(directory) / "undeclared.json"
            receipt.write_text(loaded.stdout, encoding="utf-8")
            completed = self._verify_dispatch(receipt, self._dispatch_args("dsp-NOT-THE-REAL-ONE") + ["--manifest", str(manifest_path)])
            payload = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["error"], "contract_not_declared")

    def test_receipt_from_copied_manifest_requires_same_manifest_via_state_tool(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = json.loads((REPO_ROOT / "opal" / "core" / "references" / "events.json").read_text(encoding="utf-8"))
            event = next(e for e in manifest["events"] if e["id"] == "worker.dispatch")
            event.pop("selection", None)
            event["required_docs"] = event["required_docs"][:1]
            manifest_path = Path(directory) / "events.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            loaded = subprocess.run(
                [sys.executable, str(EVENT_LOADER), "load", "--event", "worker.dispatch",
                 "--source-root", str(REPO_ROOT), "--manifest", str(manifest_path), *self._dispatch_args()],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(loaded.returncode, 0, loaded.stdout + loaded.stderr)
            receipt = Path(directory) / "reduced.json"
            receipt.write_text(loaded.stdout, encoding="utf-8")
            bad = self._verify_dispatch(receipt, self._dispatch_args())
            self.assertEqual(bad.returncode, 1, bad.stdout)
            self.assertEqual(json.loads(bad.stdout)["error"], "stale_receipt")
            good = self._verify_dispatch(receipt, self._dispatch_args() + ["--manifest", str(manifest_path)])
            self.assertEqual(good.returncode, 0, good.stdout)
            self.assertTrue(json.loads(good.stdout)["ok"])

    def test_stage_execute_call_shape_unchanged_without_contract_args(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "stage.json"
            self._load("stage.execute", receipt)
            payload = json.loads(self._verify("stage.execute", receipt).stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["via"], "state-tool event-verify")


if __name__ == "__main__":
    unittest.main()
