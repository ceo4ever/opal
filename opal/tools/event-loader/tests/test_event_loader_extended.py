"""
@header {
  "module": "test_event_loader_extended",
  "layer": "test",
  "domain": "opal-tools",
  "description": "14개 이벤트의 load/verify, zero-payload session, project-root 격리 계약 회귀",
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
STANDARD_EVENTS = (
    "session.disabled",
    "session.worker",
    "session.assistant",
    "session.project",
    "pm.activate",
    "pilot.start",
    "stage.task",
    "stage.analysis",
    "stage.plan",
    "stage.test_scenario",
    "stage.execute",
    "stage.test",
    "stage.close",
    "worker.dispatch",
)


class EventLoaderExtendedContractTest(unittest.TestCase):
    def _run(
        self,
        *args: str,
        cwd: Path | None = None,
        deployed_root: Path | None = None,
        project_root: Path | None = REPO_ROOT,
    ) -> tuple[subprocess.CompletedProcess[str], dict]:
        command = [
            sys.executable,
            str(LOADER),
            *args,
            "--source-root",
            str(REPO_ROOT),
        ]
        if deployed_root is not None:
            command.extend(["--deployed-root", str(deployed_root)])
        if project_root is not None:
            command.extend(["--project-root", str(project_root)])
        completed = subprocess.run(
            command,
            cwd=cwd or REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertTrue(completed.stdout.strip(), completed.stderr)
        return completed, json.loads(completed.stdout)

    def test_manifest_declares_exactly_fourteen_standard_events(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        events = manifest["events"]

        self.assertEqual(tuple(event["id"] for event in events), STANDARD_EVENTS)
        self.assertEqual(len(events), 14)
        for event in events:
            self.assertEqual(
                set(event),
                {
                    "id",
                    "required_docs",
                    "optional_docs",
                    "predecessors",
                    "receipt_required",
                    "consumer",
                },
            )

    def test_every_event_loads_and_its_receipt_verifies(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            deployed = temp / "deployed"
            deployed.mkdir()

            for event in STANDARD_EVENTS:
                with self.subTest(event=event):
                    loaded_result, loaded = self._run(
                        "load",
                        "--event",
                        event,
                        deployed_root=deployed,
                    )
                    self.assertEqual(loaded_result.returncode, 0, loaded_result.stderr)
                    self.assertTrue(loaded["ok"])
                    self.assertEqual(loaded["event"], event)
                    for document in loaded["documents"]:
                        self.assertEqual(
                            len(document["content"].encode("utf-8")),
                            document["bytes"],
                        )
                        self.assertEqual(len(document["sha256"]), 64)

                    receipt_path = temp / f"{event.replace('.', '-')}.json"
                    receipt_path.write_text(
                        json.dumps(loaded, ensure_ascii=False),
                        encoding="utf-8",
                    )
                    verified_result, verified = self._run(
                        "verify",
                        "--receipt",
                        str(receipt_path),
                        "--event",
                        event,
                        deployed_root=deployed,
                    )
                    self.assertEqual(verified_result.returncode, 0, verified_result.stderr)
                    self.assertTrue(verified["ok"])
                    self.assertEqual(verified["event"], event)
                    self.assertEqual(verified["payload_bytes"], loaded["payload_bytes"])

    def test_disabled_and_worker_are_distinct_zero_document_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            deployed = Path(directory) / "deployed"
            deployed.mkdir()
            payloads: dict[str, dict] = {}

            for event in ("session.disabled", "session.worker"):
                completed, payload = self._run(
                    "load",
                    "--event",
                    event,
                    deployed_root=deployed,
                )
                self.assertEqual(completed.returncode, 0)
                self.assertEqual(payload["document_count"], 0)
                self.assertEqual(payload["required_document_count"], 0)
                self.assertEqual(payload["payload_bytes"], 0)
                self.assertEqual(payload["documents"], [])
                payloads[event] = payload

            self.assertNotEqual(
                payloads["session.disabled"]["receipt"]["event"],
                payloads["session.worker"]["receipt"]["event"],
            )
            self.assertNotEqual(
                payloads["session.disabled"]["receipt"],
                payloads["session.worker"]["receipt"],
            )

    def test_missing_required_document_is_structured_failure(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        assistant = next(
            event for event in manifest["events"] if event["id"] == "session.assistant"
        )
        assistant["required_docs"][0]["source"] = "{source_root}/missing-agent-kernel.md"

        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            fixture = temp / "events.json"
            fixture.write_text(json.dumps(manifest), encoding="utf-8")
            completed, payload = self._run(
                "load",
                "--event",
                "session.assistant",
                "--manifest",
                str(fixture),
                deployed_root=temp / "deployed",
            )

        self.assertEqual(completed.returncode, 1)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"], "document_not_found")
        self.assertEqual(payload["document"], "agent-kernel")

    def test_non_project_cwd_does_not_promote_parent_home_opal_to_project(self):
        home = Path.home().resolve()
        with tempfile.TemporaryDirectory(dir=home) as directory:
            cwd = Path(directory).resolve()
            deployed = cwd / "deployed"
            deployed.mkdir()
            completed, payload = self._run(
                "load",
                "--event",
                "pm.activate",
                cwd=cwd,
                deployed_root=deployed,
                project_root=None,
            )

        self.assertEqual(completed.returncode, 1)
        self.assertEqual(payload["error"], "document_not_found")
        self.assertEqual(payload["document"], "project-agent")
        self.assertEqual(Path(payload["path"]), cwd / ".opal" / "AGENT.md")
        self.assertNotEqual(Path(payload["path"]), home / ".opal" / "AGENT.md")


if __name__ == "__main__":
    unittest.main()
