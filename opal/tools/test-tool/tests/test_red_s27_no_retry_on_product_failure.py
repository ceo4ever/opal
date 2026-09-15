"""
@header {
  "module": "test_red_s27_no_retry_on_product_failure",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "RED — S-27: 후보 1에서 제품 자체 실패(assertion 불일치/인증 실패)가 발생하고 가용성 선-단언된 스텁 후보 2가 있어도, 다른 mode로 재시도해 성공으로 덮지 않는다. 최초 실패가 최종 verdict(fail/blocked)로 남고 후보 2 시도 기록이 없어야 한다.",
  "scenarios": ["S-27"],
  "exports": ["TestRetrySuppressionContractUnit", "TestCandidate2AvailabilityAssertedFirst", "TestNoRetryOrSwitchOnProductFailure"]
}

교정 배경 — PM 지시:
1. §B.1.1 인자 계약(`--scenario`·`--task-path`·`--target` 3종 enum 필수)에 맞춰 호출을
   고쳤다. S-1~S-4와 동일한 교정.
2. `test-scenario.json`(태스크 루트)은 잠겨 있고 재시드가 막혔으므로, 이 테스트가
   임시 폴더에 자기 fixture(`profile: "browser"` + browser step)를 직접 써서
   `--task-path`로 넘긴다.
3. `candidates[]`의 `outcome`은 §A.1.2 확정 enum(`selected`|`excluded`|
   `provider_unavailable`|`infra_error`) 4종뿐이고 "실행 **결과**"가 아니라 "후보
   **탐색** 기록"이다. 이전에 넣은 `outcome ∈ ("fail","assertion_failed","auth_failed")`
   단언은 계약과 충돌하므로 제거했다. 제품 실패는:
   - candidate1이 실제로 **선택되어 실행됐다는 사실**(`outcome=="selected"`)로,
   - 그 뒤 **run의 최종 status**(`fail`|`blocked`)와 **candidate 2 이후에 실제
     시도 기록이 없다는 사실**(`reason=="not_attempted_after_selection"`)로 관측한다.
   MV-38(`CONTRACT.md:858`)이 이 순서·중단 규칙의 정식 근거다.

실측: 현재 `lib/e2e/orchestrator.py`의 `run_e2e`는 candidate가 `selected`되면 실제
스텝 실행·assertion 판정 없이 `journal.to(STATUS_BLOCKED, {"detail_code":
"e2e_scenario_runner_absent"})`로 즉시 끝난다(시나리오 실행기는 W-7 이후 소유). 따라서
이 시점에는 "assertion 불일치로 인한 제품 실패"까지 재현할 수 없고, 관측 가능한 것은
"selected된 유일한 후보 이후 어떤 후보도 실제로 시도되지 않았다"는 구조뿐이다 — 이는
retry 억제·mode 전환 억제 둘 다의 필요 조건이며, 이 테스트가 그 부분을 실측 검증한다.
남은 gap(assertion 평가·제품 실패 판정 자체의 부재)이 RED 지점이다.
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


class TestRetrySuppressionContractUnit(unittest.TestCase):
    """전제 계약: 제품 실패(assertion 불일치)는 provider_unavailable이 아니므로
    can_try_next_provider가 false여야 한다 (이미 성립해야 함)."""

    def test_assertion_failure_cannot_try_next_provider(self):
        contract = _contract()
        candidate_result = {
            "status": "fail",
            "assertion_results": [{"id": "a1", "expected": "200", "actual": "401"}],
        }
        self.assertFalse(contract.can_try_next_provider(candidate_result))

    def test_auth_failure_is_not_provider_unavailable(self):
        contract = _contract()
        legacy = contract.normalize_legacy_verdict({"status": "escalated", "error": "auth_failed"})
        self.assertNotEqual(legacy.get("status"), "provider_unavailable")


class _StubDriver:
    def __init__(self, *, available: bool, version: str = "1.0.0"):
        self.binary_path = "/fake/stub-driver"
        self.resolution_source = "stub"
        self.declared_version = version
        self._available = available

    def dispatch(self, operation, payload=None):
        assert operation == "probe"
        return {"available": self._available, "version": self.declared_version}


class TestCandidate2AvailabilityAssertedFirst(unittest.TestCase):
    """S-27 조건 원문: "S-26과 같은 방식으로 가용성을 먼저 단언한 스텁 후보 2가
    존재하는 상태"를 재사용한다 — cmux(order=2)를 단독 등록해 selected가 됨을
    먼저 확인한다."""

    def test_candidate2_alone_is_selected_when_available(self):
        drivers = _drivers()
        registry = {("cmux", "owned-surface"): lambda **kw: _StubDriver(available=True)}
        candidates, _probes = drivers.resolve_candidates(registry=registry)
        cmux_entries = [c for c in candidates if c.get("driver") == "cmux"]
        self.assertEqual(len(cmux_entries), 1, f"cmux must appear exactly once: {candidates}")
        self.assertEqual(
            cmux_entries[0].get("outcome"), "selected",
            f"candidate 2(cmux) availability must be provable in isolation: {candidates}",
        )


class TestNoRetryOrSwitchOnProductFailure(unittest.TestCase):
    """S-27 (CLI half, actual RED target): 후보 1이 선택돼 실행된 뒤에는 다른 후보로
    전환하지 않고, 최초 결과가 최종 verdict로 남아야 한다."""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.task_path = self.tmpdir / "fixture"
        self.task_path.mkdir()
        (self.task_path / "test-scenario.json").write_text(
            json.dumps(
                {
                    "schema_version": "2.0",
                    "task_id": "s27-fixture-task",
                    "locked": False,
                    "scenarios": [
                        {
                            "id": "s27-fixture",
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
        # 후보 1(agent-browser, orca-managed)이 selected되도록 정상 응답하는 스텁.
        # 호출 인자를 기록해 "retry 없이 딱 1회씩만 호출됐는지"를 관측한다(retry 억제).
        self.call_log = self.tmpdir / "calls.log"
        self.stub_bin = self.tmpdir / "product-failure-agent-browser"
        self.stub_bin.write_text(
            "#!/bin/bash\n"
            f'echo "$@" >> "{self.call_log}"\n'
            'if [[ "$1" == "--version" ]]; then\n'
            '  echo "agent-browser 0.27.3"\n'
            "  exit 0\n"
            "fi\n"
            'if [[ "$1" == "session" && "$2" == "list" ]]; then\n'
            '  echo "sessions: none active"\n'
            "  exit 0\n"
            "fi\n"
            "echo '{}'\n"
            "exit 0\n"
        )
        self.stub_bin.chmod(0o755)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_product_failure_not_overwritten_by_retry_and_no_candidate2_attempt(self):
        import os
        env = os.environ.copy()
        env["OPAL_E2E_AGENT_BROWSER_BIN"] = str(self.stub_bin)

        with tempfile.TemporaryDirectory() as artifact_dir:
            env["OPAL_E2E_ARTIFACT_DIR"] = artifact_dir
            proc = subprocess.run(
                [
                    _PYTHON, str(_TEST_TOOL_PY),
                    "e2e", "run",
                    "--scenario", "s27-fixture",
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

            # (a) candidates[]가 비어 있으면 안 된다 — 후보 1의 시도 기록이 실재해야 한다.
            candidates = data.get("candidates") or []
            self.assertNotEqual(
                candidates, [],
                "candidates[] must not be empty — candidate 1's attempt must be recorded "
                "(an empty list is not proof of retry/switch suppression, RED target)",
            )

            candidate1_entries = [c for c in candidates if c.get("order") == 1]
            self.assertEqual(
                len(candidate1_entries), 1,
                f"exactly one order=1 (candidate 1) attempt record expected: {candidates}",
            )
            candidate1 = candidate1_entries[0]

            # (b) candidate1의 outcome은 §A.1.2 enum 중 "selected"여야 한다 — 실제로
            # 선택돼 실행됐다는 뜻이며, "fail"/"assertion_failed" 같은 결과값이 아니다
            # (candidates[]는 실행 결과 기록이 아니라 후보 탐색 기록이다).
            self.assertEqual(
                candidate1.get("outcome"), "selected",
                f"candidate 1 must be recorded as selected (candidates[] records discovery, "
                f"not execution outcome): {candidate1}",
            )

            # (c)+(d-2) mode 전환 억제: order>1인 항목이 있어도 전부 "시도되지 않음" 표식
            # (reason=not_attempted_after_selection)이어야 한다 — 실제 attempt(outcome이
            # selected/infra_error 등 실행을 거친 값)가 있으면 안 된다.
            later_entries = [c for c in candidates if c.get("order", 0) > 1]
            for entry in later_entries:
                self.assertEqual(
                    entry.get("reason"), "not_attempted_after_selection",
                    f"no later candidate may show a real attempt after candidate 1 was selected: {candidates}",
                )

            # (d-1) retry 억제 — PM 교정: "총 호출 횟수 상한"이 아니라 "같은 연산이
            # 반복 호출되지 않는다"로 측정 대상을 정정한다. §B.2 프로토콜은 open·close
            # 등 probe 이후 연산을 추가로 호출하므로(실측 5회↑), 총량 상한은 정상적인
            # 단일 실행(각 연산 1회씩)조차 "재시도"로 오판정한다 — 그것이 이 assertion의
            # 실제 실패 사유였다(주석이 스스로 "no internal retry loop"라고 말하면서
            # 총량을 재고 있었다). 이제는 probe 연산(`--version`, `session list`)이든
            # 프로토콜 연산(`open <url>`, `tab close` 등)이든 상관없이, **같은 연산
            # 시그니처가 이 run 안에서 두 번 이상 나타나지 않는지**만 검사한다. 이는
            # browser step 실행이 나중에 배선돼 open·act·close 호출이 늘어나도(각 연산
            # 1회씩이라면) 계속 성립하는 형태다 — 실패 뒤 "같은 연산"이 반복될 때만
            # retry로 판정한다.
            if self.call_log.is_file():
                raw_calls = [
                    line for line in self.call_log.read_text(encoding="utf-8").splitlines() if line.strip()
                ]

                def _operation_signature(line: str) -> str:
                    tokens = line.split()
                    if not tokens:
                        return line
                    if tokens[0] == "--version":
                        return "version"
                    if len(tokens) >= 2 and tokens[0] == "session" and tokens[1] == "list":
                        return "probe_session_list"
                    if len(tokens) >= 2 and tokens[0] == "tab" and tokens[1] == "close":
                        return "close"
                    if tokens[0] == "open":
                        return "open"
                    # 알려지지 않은 §B.2 연산도 연산 이름(첫 토큰)만으로 시그니처를
                    # 만든다 — url 같은 가변 인자로 서로 다른 호출을 분리하지 않는다.
                    return tokens[0]

                signatures = [_operation_signature(line) for line in raw_calls]
                duplicated = sorted({sig for sig in signatures if signatures.count(sig) > 1})
                self.assertEqual(
                    duplicated, [],
                    f"no single operation may be invoked more than once in this run "
                    f"(that would be an internal retry, not the normal §B.2 protocol "
                    f"sequence which calls each operation once): calls={raw_calls}",
                )

            # 최초 결과가 최종 verdict로 남아야 한다. 현재 구현은 assertion 판정 자체가
            # 없어(scenario runner 부재) status가 "blocked"로 고정된다 — 이는 계약이
            # 허용하는 최종 상태값이지만, "제품 실패가 fail로 판정된다"는 실질 동작은
            # 아직 없다(RED 지점: 아래에서 실패해도 정상이며 사유가 이 gap을 가리켜야 한다).
            self.assertIn(
                data.get("status"), ("fail", "blocked"),
                f"first product-level failure must remain the final verdict: {data}",
            )


if __name__ == "__main__":
    unittest.main()
