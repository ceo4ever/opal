"""
@header {
  "module": "test_red_s5_missing_evidence_gate",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "RED — S-5: 필수 증적 5종(metadata·server log·action log·assertion expected/actual·cleanup) 중 1종을 제거한 run 결과가 lib.e2e_contract.build_verdict / validate_pass_requirements 관문을 통해 pass가 되지 않고 missing_evidence에 제거 항목이 명시되는지 5회 반복 검증한다. 실제 CLI(`test-tool integration`) 경로가 이 5종 증적을 build_verdict에 실제로 전달하는지까지 함께 확인한다.",
  "scenarios": ["S-5"],
  "exports": ["TestMissingEvidenceGateUnit", "TestMissingEvidenceGateViaCli"]
}

RED 근거: opal/tools/test-tool/lib/e2e_adapter.py:217-225의 유일한 pass 경로는
`build_verdict`를 `assertion_results: []`, `required_evidence: ["semantic_assertion"]`,
`observed_evidence: []`로 **무조건** 호출한다. 즉 실제 CLI(`test-tool integration`)가
CONTRACT.md §A.1 필수 5종 증적(metadata/server_log/action_log/assertion_evidence/
cleanup)을 관측·요구하는 경로가 전혀 없다 — required_evidence는 항상 단일 항목
`semantic_assertion`으로 고정된다. TestMissingEvidenceGateViaCli는 성공적인 cmux
스텁 실행이라도 build_verdict에 CONTRACT 5종 required_evidence가 전달되는지 검증하며,
현재는 그렇지 않으므로 RED다.
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


_REQUIRED_EVIDENCE_KINDS = (
    "metadata",
    "server_log",
    "action_log",
    "assertion_evidence",
    "cleanup",
)


def _full_result(*, omit: str | None = None):
    evidence = list(_REQUIRED_EVIDENCE_KINDS)
    if omit is not None:
        evidence.remove(omit)
    return {
        "status": "pass",
        "profile": "api",
        "surface_kind": "api",
        "actors": ["api"],
        "observed_executors": ["api"],
        "assertion_results": [
            {"id": "a1", "expected": "200", "actual": "200"},
        ],
        "required_evidence": list(_REQUIRED_EVIDENCE_KINDS),
        "observed_evidence": evidence,
    }


class TestMissingEvidenceGateUnit(unittest.TestCase):
    """S-5 (unit half): build_verdict 관문 자체는 5종 중 1종 결손을 정확히 거부해야 한다
    (이 부분은 이미 통과할 수 있다 — 아래 CLI half가 실제 RED 지점이다)."""

    def test_each_missing_evidence_kind_blocks_pass_and_is_named(self):
        contract = _contract()
        for kind in _REQUIRED_EVIDENCE_KINDS:
            with self.subTest(missing=kind):
                result = _full_result(omit=kind)
                verdict = contract.build_verdict(result)
                self.assertNotEqual(verdict.get("status"), "pass")
                detail = verdict.get("detail") or {}
                missing_evidence = detail.get("missing_evidence") if isinstance(detail, dict) else None
                self.assertIsNotNone(missing_evidence)
                self.assertIn(kind, missing_evidence)


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
    """open/navigate/close 전부 성공하는 cmux-tool stub — '완전한 실행'을 시뮬레이션."""
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


class TestMissingEvidenceGateViaCli(unittest.TestCase):
    """S-5 (CLI half, the actual RED target): 실제 `integration` 경로가 CONTRACT §A.1
    5종 required_evidence를 build_verdict에 전달하는지 검증한다."""

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

    def test_successful_run_still_never_requires_contract_5_evidence_kinds(self):
        stub_path = _make_cmux_success_stub(self.stub_dir)
        env = os.environ.copy()
        env["OPAL_CMUX_TOOL_CMD"] = str(stub_path)

        code, stdout, data = _run(
            ["integration", "--project-root", str(self.project_root)], env=env
        )

        # 이 자체가 RED의 핵심 증거: 성공적인(open/navigate/close 전부 ok) 실행이라도
        # e2e_adapter.py:217-225가 무조건 required_evidence=["semantic_assertion"]으로
        # build_verdict를 호출하기 때문에, CONTRACT.md §A.1이 요구하는 5종
        # (metadata/server_log/action_log/assertion_evidence/cleanup) 중 무엇도
        # required_evidence 로 반영되지 않는다.
        detail = data.get("detail")
        required_evidence_seen = set()
        if isinstance(detail, dict):
            required_evidence_seen = set(detail.get("required_evidence") or [])
        e2e_block = data.get("e2e") or {}
        required_evidence_seen |= set(e2e_block.get("required_evidence") or [])

        missing_from_pipeline = [k for k in _REQUIRED_EVIDENCE_KINDS if k not in required_evidence_seen]
        self.assertEqual(
            missing_from_pipeline, [],
            "e2e_adapter must surface CONTRACT.md §A.1's 5 required evidence kinds "
            f"(metadata/server_log/action_log/assertion_evidence/cleanup) — currently "
            f"missing: {missing_from_pipeline}. code={code} stdout={stdout}",
        )


if __name__ == "__main__":
    unittest.main()
