from __future__ import annotations

import json
import pathlib
import stat
import sys
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))

from lib.e2e import driver_conformance  # noqa: E402
from lib.e2e import drivers as e2e_drivers  # noqa: E402
from lib.e2e.drivers import declarative  # noqa: E402


class TestDeclarativeDriver(unittest.TestCase):
    def _project(self, *, complete=True):
        temporary = tempfile.TemporaryDirectory()
        root = pathlib.Path(temporary.name)
        bin_path = root / "fake-browser"
        bin_path.write_text(
            """#!/usr/bin/env python3
import json, sys
op = sys.argv[1] if len(sys.argv) > 1 else ''
outputs = {
 'probe': {'available': True, 'capabilities': {}},
 'open': {'handle': 'h1', 'owned': True, 'current_url': 'about:blank'},
 'snapshot': {'snapshot': {}, 'current_url': 'about:blank', 'artifact_path': None},
 'reload': {'ok': True, 'action_result': {}, 'current_url': 'about:blank'},
 'wait': {'satisfied': True, 'wait_kind': 'assertion_condition', 'elapsed_ms': 1},
 'assert': {'id': 'driver-conformance', 'expected': '', 'actual': '', 'passed': True},
 'capture': {'artifacts': {}, 'redacted': True, 'redaction_failed': False},
 'close': {'closed': True, 'released': ['h1'], 'leaked': []},
}
print(json.dumps(outputs[op]))
""",
            encoding="utf-8",
        )
        bin_path.chmod(bin_path.stat().st_mode | stat.S_IXUSR)
        operations = {
            "probe": {"argv": ["probe"]},
            "open": {"argv": ["open", "{url}"]},
            "snapshot": {"argv": ["snapshot", "{handle}"]},
            "act": {"map": {"reload": ["reload"]}},
            "wait": {"argv": ["wait", "{wait_kind}"]},
            "assert": {"argv": ["assert", "{expected}"]},
            "capture": {"argv": ["capture", "{handle}"]},
            "close": {"argv": ["close", "{handle}"]},
        }
        if not complete:
            operations.pop("capture")
        manifest = {
            "driver": "fake-json",
            "session_mode": "standalone",
            "binary": {"env": "FAKE_BROWSER"},
            "ops": operations,
            "capabilities": {},
        }
        directory = root / ".opal" / "e2e" / "drivers"
        directory.mkdir(parents=True)
        (directory / "fake.json").write_text(json.dumps(manifest), encoding="utf-8")
        return temporary, root, bin_path

    def test_one_manifest_registers_a_driver_that_passes_live_conformance(self):
        temporary, root, binary = self._project()
        self.addCleanup(temporary.cleanup)
        registry = declarative.load_project_manifests(str(root))
        self.assertEqual(list(registry), [("fake-json", "standalone")])
        result = driver_conformance.verify_registered_driver(
            "fake-json", registry=registry, runtime_context={"env": {"FAKE_BROWSER": str(binary)}}
        )
        self.assertTrue(result["ok"], result)

    def test_incomplete_eight_operation_manifest_is_not_registered(self):
        temporary, root, _binary = self._project(complete=False)
        self.addCleanup(temporary.cleanup)
        with self.assertRaises(e2e_drivers.DriverError) as caught:
            declarative.load_project_manifests(str(root))
        self.assertEqual(caught.exception.detail_code, "declarative_driver_conformance_required")

    def test_resolver_discovers_project_manifest_without_python_module(self):
        temporary, root, binary = self._project()
        self.addCleanup(temporary.cleanup)
        candidates, _ = e2e_drivers.resolve_candidates(
            runtime_context={"project_root": str(root), "env": {"FAKE_BROWSER": str(binary)}},
            candidate_order=[{"driver": "fake-json", "session_mode": "standalone", "opt_in": False}],
            manifest={"drivers": {"fake-json": {"minimum_version": "0.0.0", "tested_range": "*", "ci_pin": "0.0.0"}}},
        )
        self.assertEqual(candidates[0]["outcome"], "selected")


if __name__ == "__main__":
    unittest.main()
