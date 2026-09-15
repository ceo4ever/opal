"""
@header {
  "module": "test_red_s6_assertion_results_gate",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "RED — S-6: assertion_results가 빈 배열이거나 expected/actual 키가 없는 run 결과는 build_verdict/validate_pass_requirements 관문에서 pass가 되지 않고, real-usage 충실도로 기록되지 않아야 한다. 실제 CLI(`test-tool integration`) 경로에서도 성공한 실행이 real-usage로 잘못 승격되지 않는지 함께 확인한다.",
  "scenarios": ["S-6"],
  "exports": ["TestAssertionResultsGateUnit", "TestAssertionResultsGateViaCli"]
}

RED 근거: opal/tools/test-tool/lib/e2e_adapter.py:217-225는 성공 경로에서 항상
`assertion_results: []`로 build_verdict를 호출한다. 현재 코드는 이 경우 이미 fail로
막히지만(assertion_required), CONTRACT.md가 요구하는 "증적이 불완전한 run은 real-usage
충실도로 기록되지 않는다"는 계약을 실제 CLI 출력이 `fidelity` 필드로 명시적으로
증명하지 않는다 — e2e_adapter의 verdict 정규화 결과에는 `fidelity` 키 자체가 없다.
이 테스트는 실제 정수(整数) 필드 부재를 RED로 드러낸다.
"""
from __future__ import annotations

import importlib
import json
import os
import pathlib
import stat
import subprocess
import sys
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
_RUN_SH = _TOOL_DIR / "run.sh"
sys.path.insert(0, str(_TOOL_DIR))


def _contract():
    return importlib.import_module("lib.e2e_contract")


class TestAssertionResultsGateUnit(unittest.TestCase):
    """S-6 (unit half): 빈 assertion_results / expected·actual 결손은 pass가 되면 안 된다."""

    def _base_result(self):
        return {
            "status": "pass",
            "profile": "api",
            "surface_kind": "api",
            "actors": ["api"],
            "observed_executors": ["api"],
            "required_evidence": ["semantic_assertion"],
            "observed_evidence": ["semantic_assertion"],
        }

    def test_empty_assertion_results_never_pass(self):
        contract = _contract()
        result = self._base_result()
        result["assertion_results"] = []
        verdict = contract.build_verdict(result)
        self.assertNotEqual(verdict.get("status"), "pass")

    def test_missing_expected_actual_never_pass(self):
        contract = _contract()
        result = self._base_result()
        result["assertion_results"] = [{"id": "a1"}]  # no expected/actual
        verdict = contract.build_verdict(result)
        self.assertNotEqual(verdict.get("status"), "pass")

    def test_incomplete_assertion_result_is_never_real_usage_fidelity(self):
        """CONTRACT.md 계약: 증적이 불완전한 run은 real-usage로 기록되지 않는다.
        빈 assertion_results로 fail이 되더라도, normalized 결과에 fidelity가 있다면
        real-usage여서는 안 된다 — 그리고 애초에 fail 판정 자체에 fidelity 필드가
        없어서도 안 된다(하네스가 나중에 이 필드를 신뢰해 승격 판단에 쓸 수 있어야 함)."""
        contract = _contract()
        result = self._base_result()
        result["assertion_results"] = []
        result["fidelity"] = "real-usage"  # 악의적/버그로 잘못 주입된 값
        verdict = contract.build_verdict(result)
        normalized = verdict.get("normalized") or {}
        self.assertNotEqual(
            normalized.get("fidelity"), "real-usage",
            "an incomplete-evidence run must never be recorded as real-usage fidelity",
        )


def _run(args, env=None):
    cmd = ["bash", str(_RUN_SH)] + args
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, data


def _make_cmux_success_stub(stub_dir):
    stub_path = stub_dir / "cmux-tool-stub"
    script = """#!/bin/bash
case "$1" in
  open) echo '{"ok": true, "surface": "surf-1"}' ;;
  navigate) echo '{"ok": true}' ;;
  close) echo '{"ok": true}' ;;
  *) echo '{"ok": true}' ;;
esac
exit 0
"""
    stub_path.write_text(script)
    stub_path.chmod(stub_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return stub_path


class TestAssertionResultsGateViaCli(unittest.TestCase):
    """S-6 (CLI half, the actual RED target): 실제 integration 경로의 출력에 fidelity
    필드가 존재하고, 빈 assertion_results 경로에서는 절대 real-usage가 아니어야 한다."""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.project_root = self.tmpdir / "project"
        self.project_root.mkdir()
        (self.project_root / ".opal").mkdir()
        (self.project_root / ".opal" / "test-tools.yaml").write_text(
            """
version: "2.0"
source_label: project
stack: {language: ts, framework: nextjs, runtime: node}
tiers:
  unit:
    fe: {}
    be: {}
  integration:
    e2e:
      - name: cmux
        priority: 1
        via: cmux-tool
"""
        )
        self.stub_dir = self.tmpdir / "stub"
        self.stub_dir.mkdir()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_cli_output_carries_fidelity_and_never_real_usage_with_empty_assertions(self):
        stub_path = _make_cmux_success_stub(self.stub_dir)
        env = os.environ.copy()
        env["OPAL_CMUX_TOOL_CMD"] = str(stub_path)

        code, stdout, data = _run(
            ["integration", "--project-root", str(self.project_root)], env=env
        )

        e2e_block = data.get("e2e") or {}
        # RED target: e2e_adapter의 성공 경로는 assertion_results=[]를 무조건 전달하므로
        # fail이 되고(맞는 동작), 그 결과 어디에도 CONTRACT.md가 요구하는 fidelity 필드가
        # 실려 나오지 않는다 — real-usage 미승격을 '증명'할 관측 가능한 필드 자체가 없다.
        self.assertIn(
            "fidelity", e2e_block,
            f"CLI integration output must carry an explicit fidelity field to prove "
            f"non-promotion to real-usage; got e2e block: {e2e_block!r} (full: {data!r})",
        )
        self.assertNotEqual(e2e_block.get("fidelity"), "real-usage")


if __name__ == "__main__":
    unittest.main()
