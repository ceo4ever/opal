from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))

from lib.e2e import drivers as e2e_drivers  # noqa: E402
from lib.e2e import orchestrator  # noqa: E402


class TestCandidateOrderFile(unittest.TestCase):
    def test_order_file_is_passed_to_candidate_resolver(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            config = root / ".opal" / "e2e"
            config.mkdir(parents=True)
            expected = [
                {"driver": "custom", "session_mode": "standalone", "opt_in": False},
                {"driver": "playwright", "session_mode": "standalone", "opt_in": True},
            ]
            (config / "order.json").write_text(
                json.dumps({"candidate_order": expected}), encoding="utf-8"
            )
            scenario = {"profile": "browser", "surface_kind": "web", "steps": []}
            with mock.patch.object(
                orchestrator.e2e_drivers, "resolve_candidates", return_value=([], [])
            ) as resolve:
                orchestrator._resolve_executor_candidates(
                    scenario, runtime_context={"project_root": str(root)}
                )
            self.assertEqual(resolve.call_args.kwargs["candidate_order"], expected)

    def test_missing_order_file_preserves_cdrv3_default(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNone(e2e_drivers.load_candidate_order(directory))

    def test_invalid_order_is_rejected_instead_of_silently_falling_back(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            config = root / ".opal" / "e2e"
            config.mkdir(parents=True)
            (config / "order.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(e2e_drivers.DriverError) as caught:
                e2e_drivers.load_candidate_order(str(root))
            self.assertEqual(caught.exception.detail_code, "candidate_order_invalid")


if __name__ == "__main__":
    unittest.main()
