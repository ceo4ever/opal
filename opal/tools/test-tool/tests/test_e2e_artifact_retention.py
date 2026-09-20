"""E2E 저장 경계와 산출물 보존 정책 검증."""
from __future__ import annotations

import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from lib.e2e import orchestrator


class TestE2eArtifactRetention(unittest.TestCase):
    def test_default_root_is_project_local_ignored_artifact_directory(self):
        with tempfile.TemporaryDirectory() as project_root:
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("OPAL_E2E_ARTIFACT_ROOT", None)
                self.assertEqual(
                    orchestrator.default_artifact_root(project_root),
                    str(pathlib.Path(project_root) / ".e2e" / "artifacts"),
                )

    def test_explicit_artifact_root_override_wins(self):
        with tempfile.TemporaryDirectory() as configured:
            with mock.patch.dict(os.environ, {"OPAL_E2E_ARTIFACT_ROOT": configured}):
                self.assertEqual(orchestrator.default_artifact_root("/unused"), configured)

    def test_retention_keeps_only_the_most_recent_completed_runs(self):
        with tempfile.TemporaryDirectory() as root:
            parent = pathlib.Path(root)
            for ordinal in range(1, 6):
                run_id = f"e2e-20260920-{ordinal:03d}"
                run_dir = parent / run_id
                run_dir.mkdir()
                (run_dir / "run.json").write_text(
                    json.dumps({"run_id": run_id, "ended_at": f"2026-09-20T00:00:0{ordinal}Z"}),
                    encoding="utf-8",
                )

            active = parent / "e2e-20260920-999"
            active.mkdir()
            removed = orchestrator.enforce_artifact_retention(parent, keep=2)

            self.assertEqual(len(removed), 3)
            self.assertEqual(
                sorted(path.name for path in parent.iterdir()),
                ["e2e-20260920-004", "e2e-20260920-005", "e2e-20260920-999"],
            )

    def test_retention_rejects_zero_keep_count(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                orchestrator.enforce_artifact_retention(pathlib.Path(root), keep=0)


if __name__ == "__main__":
    unittest.main()
