"""
@header {
  "module": "test_task113_bootstrap_contract",
  "layer": "test",
  "domain": "opal-bootstrap",
  "description": "태스크 113 source-only 통합 감사 CLI의 자동 회귀 진입점",
  "exports": [],
  "depends": ["task113_bootstrap_audit"]
}
"""

from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


AUDIT = Path(__file__).with_name("task113_bootstrap_audit.py")


def _load_audit_module():
    spec = importlib.util.spec_from_file_location("task113_bootstrap_audit_tested", AUDIT)
    if spec is None or spec.loader is None:
        raise RuntimeError("audit import spec unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Task113BootstrapContractTest(unittest.TestCase):
    def test_source_audit_passes(self):
        completed = subprocess.run(
            [sys.executable, str(AUDIT), "--mode", "source", "--iterations", "3"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertTrue(completed.stdout.strip(), completed.stderr)
        payload = json.loads(completed.stdout)

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(payload["ok"])
        source = payload["results"][0]
        self.assertTrue(source["ok"])
        for state in ("general_assistant", "project_aware_assistant"):
            self.assertTrue(source["metrics"][state]["under_30kb"])
            self.assertTrue(source["metrics"][state]["at_least_70_percent_reduction"])

    def test_installed_parity_mode_passes_for_an_exact_source_mirror(self):
        audit = _load_audit_module()
        with tempfile.TemporaryDirectory() as directory:
            installed_root = Path(directory) / ".opal"
            for source_relative, installed_relative in audit.PARITY_PATHS:
                source = audit.REPO_ROOT / source_relative
                installed = installed_root / installed_relative
                installed.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, installed)

            result = audit.run_installed_parity(installed_root)

        self.assertTrue(result["ok"])
        self.assertEqual(len(result["checked"]), len(audit.PARITY_PATHS))


if __name__ == "__main__":
    unittest.main()
