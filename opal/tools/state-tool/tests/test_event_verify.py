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


class EventVerifyRequireDefaultManifestTest(unittest.TestCase):
    """S-5 (f): state-tool event-verify가 --require-default-manifest를 loader에 그대로 전달한다(판정은 loader 소유)."""

    FLAG = "--require-default-manifest"
    MANIFEST = REPO_ROOT / "opal" / "core" / "references" / "events.json"

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.tmp = Path(self._dir.name).resolve()
        self.project = self.tmp / "project"
        self.project.mkdir()
        env = {k: v for k, v in os.environ.items() if not k.startswith("OPAL_EVENT_LOADER_") and k != "OPAL_DEPLOYED_ROOT"}
        env["HOME"] = str(self.tmp)
        self.env = env

    @staticmethod
    def _contract_args() -> list[str]:
        return ["--contract-version", "2", "--agent", "opal-be-agent", "--role", "builder", "--dispatch-id", "dsp-0123456789"]

    def _load(self, name: str, *extra: str) -> Path:
        completed = subprocess.run(
            [sys.executable, str(EVENT_LOADER), "load", "--event", "worker.dispatch", "--source-root", str(REPO_ROOT),
             "--project-root", str(self.project), "--deployed-root", str(self.tmp / "deployed"), *self._contract_args(), *extra],
            capture_output=True, text=True, check=False, env=self.env,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        path = self.tmp / name
        path.write_text(completed.stdout, encoding="utf-8")
        return path

    def _verify(self, receipt: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(STATE_TOOL), "event-verify", "--event", "worker.dispatch", "--receipt", str(receipt),
             "--source-root", str(REPO_ROOT), "--project-root", str(self.project), "--deployed-root", str(self.tmp / "deployed"),
             *self._contract_args(), *extra],
            capture_output=True, text=True, check=False, env=self.env,
        )

    def _reduced_copy(self) -> Path:
        manifest = json.loads(self.MANIFEST.read_text(encoding="utf-8"))
        event = next(e for e in manifest["events"] if e["id"] == "worker.dispatch")
        event.pop("selection", None)
        event["required_docs"] = event["required_docs"][:1]
        path = self.tmp / "copy" / "events.json"
        path.parent.mkdir()
        path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        return path

    def test_flag_with_default_manifest_passes_and_reports_manifest_default(self):
        completed = self._verify(self._load("ok.json"), self.FLAG)
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(payload["ok"])
        self.assertIs(payload["manifest_default"], True)
        self.assertEqual(payload["manifest_path"], str(self.MANIFEST.resolve()))
        self.assertEqual(payload["via"], "state-tool event-verify")

    def test_flag_with_copied_manifest_is_rejected_with_loader_error_and_exit_code(self):
        copy = self._reduced_copy()
        receipt = self._load("copy.json", "--manifest", str(copy))
        completed = self._verify(receipt, "--manifest", str(copy), self.FLAG)
        payload = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"], "manifest_not_default")
        self.assertEqual(payload["expected"], str(self.MANIFEST.resolve()))
        self.assertEqual(payload["actual"], str(copy.resolve()))

    def test_flag_is_forwarded_only_when_given(self):
        copy = self._reduced_copy()
        receipt = self._load("copy2.json", "--manifest", str(copy))
        without = self._verify(receipt, "--manifest", str(copy))
        payload = json.loads(without.stdout)
        self.assertEqual(without.returncode, 0, without.stdout + without.stderr)
        self.assertTrue(payload["ok"])
        self.assertNotIn("manifest_default", payload)
        plain = self._verify(self._load("plain.json"))
        plain_payload = json.loads(plain.stdout)
        self.assertEqual(plain.returncode, 0, plain.stdout + plain.stderr)
        self.assertNotIn("manifest_default", plain_payload)


if __name__ == "__main__":
    unittest.main()
