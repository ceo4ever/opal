"""
@header {
  "module": "test_red_s26_candidate_no_switch_infra_error",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "RED — S-26: 후보 1이 infra_error로 실패하면 candidates[]에 그 시도만 기록되고(가용성이 별도로 먼저 증명된 후보 2로) 전환하지 않으며, run이 infra_error로 확정돼야 한다.",
  "scenarios": ["S-26"],
  "exports": ["TestCanTryNextProviderContractUnit", "TestCandidate2AvailabilityAssertedFirst", "TestNoSwitchAfterInfraError"]
}

교정 배경 — PM 지시(3건):
1. §B.1.1 인자 계약: `--scenario`·`--task-path`·`--target`(3종 enum) 3개 필수 인자를
   전부 넘긴다. 이전 호출은 `--scenario-id`(dest는 같지만 문서 표기와 다름)만 쓰고
   `--task-path`를 생략해 argparse가 아니라 `run_e2e` 내부에서 blocked/exit 19로
   막혔다 — driver 구현과 무관한 실패였다.
2. `test-scenario.json`(태스크 루트)은 `locked: true`이고 재시드가 영구 차단됐으므로
   손대지 않는다. 대신 이 테스트가 자기 fixture(`profile: "browser"` + browser step)를
   임시 폴더에 직접 써서 그 경로를 `--task-path`로 넘긴다.
3. `candidates[]`는 §A.1.2가 확정한 "후보 **탐색** 기록"이며 outcome enum은
   `selected`|`excluded`|`provider_unavailable`|`infra_error` 4종뿐이다(실측:
   `lib/e2e/drivers/__init__.py` `OUTCOME_*` 상수). "가용성을 먼저 단언한 스텁 후보 2"는
   `e2e_drivers.resolve_candidates(registry=...)`가 공개 확장점(파라미터)으로 이미
   지원하므로, 이를 통해 후보 2(cmux)만 등록한 상태에서 `selected`가 되는지 먼저
   증명한 뒤(TestCandidate2AvailabilityAssertedFirst), 실제 CLI(`e2e run`) 경로에서
   후보 1에 infra_error를 주입해도 후보 2가 시도되지 않음을 검증한다.

실측(§C.4 근거): `OPAL_E2E_AGENT_BROWSER_BIN`으로 후보 1(`agent-browser`,
`orca-managed`)의 바이너리를 대체해, `--version`은 tested_range(`0.27.x`) 밖의
버전(`9.9.9`)을 보고하고 `session list` 호출은 타임아웃하게 만들면
`lib/e2e/drivers/__init__.py:resolve_candidates`의 `outside_tested_range` 분기가
`outcome=infra_error`로 기록하고 즉시 `break`한다 — `candidates[]`에는 그 1건만
남고 cmux(후보 2)·standalone(후보 3) 시도 기록이 없다. 그러나 `lib/e2e/orchestrator.py`
의 `run_e2e`는 `selected`가 0건이면 무조건 `executor_unavailable`로 끝내
(`if not selected: ... STATUS_EXECUTOR_UNAVAILABLE`) candidate 자체의 `infra_error`를
run 최종 상태로 승격하지 않는다 — 이것이 W-5가 보고한 실제 잔여 결함이며, 이 테스트의
RED 지점이다.
"""
from __future__ import annotations

import importlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
_TEST_TOOL_PY = _TOOL_DIR / "test_tool.py"
_SOURCE_ROOT = _TOOL_DIR.parent.parent.parent
_PYTHON = sys.executable
sys.path.insert(0, str(_TOOL_DIR))


def _contract():
    return importlib.import_module("lib.e2e_contract")


def _drivers():
    return importlib.import_module("lib.e2e.drivers")


class TestCanTryNextProviderContractUnit(unittest.TestCase):
    """전제 계약: infra_error에서는 다음 후보로 넘어갈 수 없어야 한다 (이미 성립해야 함)."""

    def test_infra_error_candidate_cannot_try_next(self):
        contract = _contract()
        self.assertFalse(
            contract.can_try_next_provider({"status": "infra_error", "error": "e2e_infra_error"}),
        )


class _StubDriver:
    """`e2e_drivers.resolve_candidates(registry=...)`가 기대하는 최소 인터페이스만
    구현한 스텁 — 실제 driver 구현(`lib/e2e/drivers/agent_browser.py` 등)을 흉내내지
    않고, 공개 확장점(factory 콜러블)만 채운다."""

    def __init__(self, *, available: bool, version: str = "1.0.0"):
        self.binary_path = "/fake/stub-driver"
        self.resolution_source = "stub"
        self.declared_version = version
        self._available = available

    def dispatch(self, operation, payload=None):
        assert operation == "probe"
        return {"available": self._available, "version": self.declared_version}


class TestCandidate2AvailabilityAssertedFirst(unittest.TestCase):
    """S-26 조건 원문: "후보 2의 가용성을 먼저 단언한 뒤" 후보 1에 infra_error를
    주입한다. 여기서는 실제 후보 2(cmux, order=2)를 `resolve_candidates(registry=...)`
    로 단독 등록해 `selected`가 됨을 먼저 확인한다 — 이 단계는 아직 실패할 이유가 없다
    (공개 확장점을 그대로 쓰는 unit 검증)."""

    def test_candidate2_alone_is_selected_when_available(self):
        drivers = _drivers()
        registry = {("cmux", "owned-surface"): lambda **kw: _StubDriver(available=True)}
        candidates, _probes = drivers.resolve_candidates(registry=registry)
        cmux_entries = [c for c in candidates if c.get("driver") == "cmux"]
        self.assertEqual(len(cmux_entries), 1, f"cmux must appear exactly once: {candidates}")
        self.assertEqual(
            cmux_entries[0].get("outcome"), "selected",
            f"candidate 2(cmux) availability must be provable in isolation before candidate 1 fails: {candidates}",
        )


class TestNoSwitchAfterInfraError(unittest.TestCase):
    """S-26 (CLI half, actual RED target): 후보 1의 infra_error 이후 후보 2로
    전환하지 않고, run이 infra_error로 확정돼야 한다."""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.task_path = self.tmpdir / "fixture"
        self.task_path.mkdir()
        (self.task_path / "test-scenario.json").write_text(
            json.dumps(
                {
                    "schema_version": "2.0",
                    "task_id": "s26-fixture-task",
                    "locked": False,
                    "scenarios": [
                        {
                            "id": "s26-fixture",
                            "surface_kind": "browser",
                            "profile": "browser",
                            "actors": ["browser"],
                            "steps": [
                                {"id": "st-1", "executor": "browser", "step_role": "verify", "action": "open"},
                            ],
                            "assertions": [{"id": "a1", "expected": "ok"}],
                            "required_evidence": ["metadata"],
                        },
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        # 후보 1(agent-browser, orca-managed)을 infra_error로 만드는 스텁:
        # --version은 tested_range("0.27.x") 밖의 버전을 보고하고, session list는
        # 타임아웃시켜 `_run_cli`가 None을 반환 → DriverError("agent_browser_probe_exec_failed")
        # → outside_tested_range=True → outcome=infra_error (실측 확인됨).
        self.stub_bin = self.tmpdir / "infra-error-agent-browser"
        self.stub_bin.write_text(
            "#!/bin/bash\n"
            'if [[ "$1" == "--version" ]]; then\n'
            '  echo "agent-browser 9.9.9"\n'
            "  exit 0\n"
            "fi\n"
            "sleep 30\n"
        )
        self.stub_bin.chmod(0o755)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_infra_error_confirmed_final_and_no_candidate2_attempt(self):
        import os
        env = os.environ.copy()
        env["OPAL_E2E_AGENT_BROWSER_BIN"] = str(self.stub_bin)

        with tempfile.TemporaryDirectory() as artifact_dir:
            env["OPAL_E2E_ARTIFACT_DIR"] = artifact_dir
            proc = subprocess.run(
                [
                    _PYTHON, str(_TEST_TOOL_PY),
                    "e2e", "run",
                    "--scenario", "s26-fixture",
                    "--task-path", str(self.task_path),
                    "--target", "source-worktree",
                    "--worktree-root", str(_SOURCE_ROOT),
                ],
                capture_output=True,
                text=True,
                env=env,
                timeout=60,
            )
            self.assertNotEqual(
                proc.returncode, 2,
                f"'e2e run' subcommand missing (RED target): {proc.stderr!r}",
            )
            data = json.loads(proc.stdout)

            candidates = data.get("candidates") or []
            self.assertNotEqual(candidates, [], f"candidate 1's attempt must be recorded: {data}")

            infra_error_orders = [c["order"] for c in candidates if c.get("outcome") == "infra_error"]
            self.assertTrue(infra_error_orders, f"candidates[] must record the infra_error attempt: {candidates}")
            max_infra_order = max(infra_error_orders)
            larger_orders = [c for c in candidates if c.get("order", 0) > max_infra_order]
            self.assertEqual(
                larger_orders, [],
                f"no candidate entry with order greater than the infra_error entry's order "
                f"(candidate 2 must not be attempted after infra_error): {candidates}",
            )

            # 실측 RED 지점: candidate가 infra_error여도 selected가 0건이면 orchestrator는
            # 무조건 executor_unavailable로 끝낸다 — CONTRACT.md §A.1.2·MV-38이 요구하는
            # "run이 infra_error로 확정된다"를 아직 만족하지 못한다.
            self.assertEqual(
                data.get("status"), "infra_error",
                f"final verdict must be infra_error when a candidate attempt is infra_error, "
                f"not merely executor_unavailable (RED target): {data}",
            )


if __name__ == "__main__":
    unittest.main()
