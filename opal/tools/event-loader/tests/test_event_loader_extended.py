"""
@header {
  "module": "test_event_loader_extended",
  "layer": "test",
  "domain": "opal-tools",
  "description": "이벤트 load/verify, zero-payload session, project-root 격리와 다건 bounded 프로젝트 브리핑 계약 회귀",
  "exports": [],
  "depends": ["event_loader"]
}
"""

from __future__ import annotations

import json
from pathlib import Path
import runpy
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

    def test_project_brief_renders_ready_to_emit_markdown(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            task_dir = fixture / "tasks" / "999-fixture"
            task_dir.mkdir(parents=True)
            (task_dir / "state.json").write_text(
                json.dumps({
                    "task_id": "999-fixture",
                    "mode": "agentic",
                    "current_status": "in_progress",
                    "updated_at": "2026-09-12 08:00:00",
                    "next_action": "계속 진행",
                    "rows": [{"status": "in_progress", "stage": "EXECUTE"}],
                }, ensure_ascii=False),
                encoding="utf-8",
            )
            memory = fixture / ".opal" / "MEMORY.json"
            memory.parent.mkdir()
            memory.write_text(json.dumps({
                "version": 1,
                "last_task_number": 999,
                "memories": [{
                    "title": "검토 후보",
                    "date": "2026-09-12",
                    "type": "improvement",
                    "status": "candidate",
                    "file": "memory/candidate.md",
                    "summary": "출력 계약 확인",
                }],
                "history": [],
            }, ensure_ascii=False), encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, str(LOADER), "project-brief",
                 "--source-root", str(REPO_ROOT),
                 "--project-root", str(fixture)],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout.rstrip("\n"),
            "[부트스트랩] ✅ session.project ⏳ PM\n\n"
            "📌 이어보기\n"
            "- 999-fixture — EXECUTE · 다음: 계속 진행 · 모드: agentic (state)\n\n"
            "📌 우선 검토\n"
            "- 검토 후보 — 출력 계약 확인",
        )

    def test_project_brief_empty_project_keeps_short_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [sys.executable, str(LOADER), "project-brief",
                 "--source-root", str(REPO_ROOT),
                 "--project-root", directory],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout,
            "[부트스트랩] ✅ session.project ⏳ PM\n",
        )

    def test_project_brief_output_is_bounded_to_1024_utf8_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            task_dir = fixture / "tasks" / "999-fixture"
            task_dir.mkdir(parents=True)
            (task_dir / "state.json").write_text(
                json.dumps({
                    "task_id": "긴제목" * 300,
                    "mode": "agentic",
                    "current_status": "in_progress",
                    "updated_at": "2026-09-12 08:00:00",
                    "next_action": "긴다음행동" * 300,
                    "rows": [{"status": "in_progress", "stage": "EXECUTE"}],
                }, ensure_ascii=False),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(LOADER), "project-brief",
                 "--source-root", str(REPO_ROOT),
                 "--project-root", str(fixture)],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertLessEqual(len(completed.stdout.rstrip("\n").encode("utf-8")), 1024)
        self.assertTrue(completed.stdout.startswith("[부트스트랩] ✅ session.project ⏳ PM"))

    def test_project_brief_renders_many_items_remainder_and_anomaly_count_bounded(self):
        """Task 133 S-5 / PLAN D-5, H-2: multi-item public rendering stays bounded."""
        compose = runpy.run_path(str(LOADER))["compose_project_brief"]
        state_payload = {
            "ok": True,
            "items": [
                {
                    "title": f"40{number}-" + "긴 다국어 제목 " * 60,
                    "stage": "EXECUTE",
                    "next_action": "긴 다음 행동 " * 60,
                }
                for number in (5, 4, 3)
            ],
            "other_count": 2,
            "anomalies": [{"code": "registry_meta_corrupt"}],
        }
        memory_payload = {
            "ok": True,
            "review_rows": [{
                "title": "장문 검토 후보 " * 40,
                "summary": "장문 검토 요약 " * 40,
            }],
        }

        markdown = compose(state_payload, memory_payload)

        for title in ("405-", "404-", "403-"):
            self.assertIn(title, markdown)
        self.assertIn("그 외 2건", markdown)
        self.assertIn("경로 이상 1건", markdown)
        self.assertLessEqual(len(markdown.encode("utf-8")), 1024)

    def test_project_brief_cli_preserves_inputs_and_multitask_counts(self):
        """Task 133 S-5 / AC-6, AC-8: CLI observes the same bounded contract read-only."""
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            for number in range(1, 6):
                task_dir = fixture / "tasks" / f"40{number}-fixture"
                task_dir.mkdir(parents=True)
                (task_dir / "state.json").write_text(json.dumps({
                    "task_id": f"40{number}-" + "다국어 제목 " * 70,
                    "current_status": "in_progress",
                    "updated_at": f"2026-09-13 {number + 10:02d}:00:00",
                    "next_action": "다국어 다음 행동 " * 70,
                    "rows": [{"status": "in_progress", "stage": "EXECUTE"}],
                }, ensure_ascii=False), encoding="utf-8")
            meta = fixture / ".opal-worktrees" / ".meta"
            meta.mkdir(parents=True)
            (meta / "task_499.json").write_text("{broken", encoding="utf-8")
            memory = fixture / ".opal" / "MEMORY.json"
            memory.parent.mkdir(exist_ok=True)
            memory.write_text(json.dumps({
                "version": 1,
                "last_task_number": 499,
                "memories": [{
                    "title": "검토 후보 " * 60,
                    "date": "2026-09-13",
                    "type": "improvement",
                    "status": "candidate",
                    "file": "memory/candidate.md",
                    "summary": "검토 요약 " * 60,
                }],
                "history": [],
            }, ensure_ascii=False), encoding="utf-8")
            inputs = {path: path.read_bytes() for path in fixture.rglob("*") if path.is_file()}

            completed = subprocess.run(
                [sys.executable, str(LOADER), "project-brief",
                 "--source-root", str(REPO_ROOT),
                 "--project-root", str(fixture)],
                capture_output=True,
                text=True,
                check=False,
            )

            after = {path: path.read_bytes() for path in inputs}

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("그 외 2건", completed.stdout)
        self.assertIn("경로 이상 1건", completed.stdout)
        self.assertLessEqual(len(completed.stdout.rstrip("\n").encode("utf-8")), 1024)
        self.assertEqual(inputs, after)

    def test_project_brief_omits_only_the_failed_query_block(self):
        compose = runpy.run_path(str(LOADER))["compose_project_brief"]
        state_payload = {
            "ok": True,
            "items": [{
                "title": "999-fixture",
                "stage": "TEST",
                "next_action": "검증 계속",
                "mode": "agentic",
                "mode_source": "state",
            }],
        }
        memory_payload = {
            "ok": True,
            "review_rows": [{"title": "검토 후보", "summary": "확인 필요"}],
        }

        state_only = compose(state_payload, None)
        memory_only = compose(None, memory_payload)

        self.assertIn("📌 이어보기", state_only)
        self.assertNotIn("📌 우선 검토", state_only)
        self.assertNotIn("📌 이어보기", memory_only)
        self.assertIn("📌 우선 검토", memory_only)

    def test_s6_boot_summary_adds_normalized_mode_and_source(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            task_dir = fixture / "tasks" / "999-fixture"
            task_dir.mkdir(parents=True)
            (task_dir / "state.json").write_text(json.dumps({
                "task_id": "999-fixture",
                "mode": "agentic",
                "current_status": "in_progress",
                "updated_at": "2026-09-12 08:00:00",
                "next_action": "계속 진행",
                "rows": [{"status": "in_progress", "stage": "EXECUTE"}],
            }), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(REPO_ROOT / "opal/tools/state-tool/state_tool.py"),
                 "boot-summary", str(fixture)],
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIn("mode", payload["items"][0], payload)
        self.assertIn("mode_source", payload["items"][0], payload)
        self.assertEqual(payload["items"][0]["mode"], "agentic")
        self.assertEqual(payload["items"][0]["mode_source"], "state")

    def test_s6_invalid_legacy_mode_is_visible_as_fail_closed(self):
        compose = runpy.run_path(str(LOADER))["compose_project_brief"]
        markdown = compose({
            "ok": True,
            "items": [{
                "title": "legacy",
                "stage": "PLAN",
                "next_action": "검토",
                "mode": "interactive",
                "mode_source": "fail_closed",
            }],
        }, None)
        self.assertIn("📌 이어보기", markdown)
        self.assertIn("interactive", markdown)
        self.assertIn("fail_closed", markdown)

    def test_s6_project_brief_mode_output_remains_bounded_and_partial_failure_isolated(self):
        compose = runpy.run_path(str(LOADER))["compose_project_brief"]
        state_payload = {
            "ok": True,
            "items": [{
                "title": "긴태스크" * 300,
                "stage": "EXECUTE",
                "next_action": "긴다음행동" * 300,
                "mode": "agentic",
                "mode_source": "state",
            }],
        }
        state_only = compose(state_payload, None)
        self.assertLessEqual(len(state_only.encode("utf-8")), 1024)
        self.assertIn("📌 이어보기", state_only)
        self.assertIn("agentic", state_only)
        self.assertIn("state", state_only)
        memory_only = compose(None, {
            "ok": True,
            "review_rows": [{"title": "검토 후보", "summary": "확인 필요"}],
        })
        self.assertNotIn("📌 이어보기", memory_only)
        self.assertIn("📌 우선 검토", memory_only)


if __name__ == "__main__":
    unittest.main()
