"""
@header {
  "module": "test_e2e_verdict_negative",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "T06 판정 부정 검증 — 필수 증적 5종 중 1종 결손·빈 assertion_results·expected/actual 키 누락은 pass가 되지 않고, 증적 불완전 run은 real-usage로 기록되지 않으며, 모든 pass 판정이 validate_pass_requirements 단일 관문을 통과하고 우회 경로가 없음을 고정한다.",
  "scenarios": ["S-5", "S-6"],
  "exports": [
    "TestMissingEvidenceNeverPasses", "TestAssertionResultsNeverPassEmpty",
    "TestIncompleteEvidenceIsNeverRealUsage", "TestSinglePassGate"
  ]
}

W-4. `lib/e2e_contract.py`와 `lib/scenario.py`는 **소비만** 한다(TASK.md C-1) — 이 스위트는
계약 모듈을 고치지 않고 그 관문이 실제로 닫혀 있는지만 관측한다. S-5·S-6의 동결 RED가
`build_verdict` 호출 1회를 보는 것과 달리, 여기서는 (a) 결손 종류별 반복, (b) 관문 우회
경로 부재, (c) 판정 산출 형태 자체를 고정한다.
"""
from __future__ import annotations

import inspect
import pathlib
import re
import sys
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(_TOOL_DIR))

from lib import e2e_contract  # noqa: E402
from lib.e2e import evidence as e2e_evidence  # noqa: E402

# CONTRACT.md §A.1/§A.4/§A.5/§A.6 공통 필수 증적 5종. 이름은 evidence.py가 소유한다.
REQUIRED_EVIDENCE = e2e_evidence.COMMON_REQUIRED_EVIDENCE

_REPEAT = 5


def _passing_result(**overrides):
    """관문을 통과하도록 만든 최소 result — 각 테스트가 한 축씩만 무너뜨린다."""
    result = {
        "status": "pass",
        "profile": "api",
        "surface_kind": "api",
        "actors": ["api"],
        "observed_executors": ["api"],
        "assertion_results": [{"id": "a1", "expected": 200, "actual": 200}],
        "required_evidence": list(REQUIRED_EVIDENCE),
        "observed_evidence": list(REQUIRED_EVIDENCE),
    }
    result.update(overrides)
    return result


class TestMissingEvidenceNeverPasses(unittest.TestCase):
    """AC-6 — 필수 증적 5종 중 1종만 빠져도 pass가 아니고, 무엇이 빠졌는지 이름으로 나온다."""

    def test_control_case_with_all_five_evidence_kinds_passes(self):
        """부정 검증이 '항상 fail이라 통과'하는 허수가 아님을 먼저 고정한다."""
        verdict = e2e_contract.build_verdict(_passing_result())
        self.assertEqual(verdict["status"], "pass", verdict)

    def test_each_missing_kind_blocks_pass_and_is_named_on_every_repeat(self):
        for kind in REQUIRED_EVIDENCE:
            observed = [item for item in REQUIRED_EVIDENCE if item != kind]
            for attempt in range(_REPEAT):
                with self.subTest(missing=kind, attempt=attempt):
                    verdict = e2e_contract.build_verdict(_passing_result(observed_evidence=observed))
                    self.assertNotEqual(verdict["status"], "pass")
                    self.assertFalse(verdict["ok"])
                    detail = verdict.get("detail")
                    self.assertIsInstance(detail, dict)
                    self.assertIn(kind, detail.get("missing_evidence") or [])

    def test_missing_evidence_names_only_what_is_actually_missing(self):
        observed = [item for item in REQUIRED_EVIDENCE if item != "cleanup"]
        verdict = e2e_contract.build_verdict(_passing_result(observed_evidence=observed))
        self.assertEqual(verdict["detail"]["missing_evidence"], ["cleanup"])

    def test_no_observed_evidence_at_all_blocks_pass(self):
        verdict = e2e_contract.build_verdict(_passing_result(observed_evidence=[]))
        self.assertNotEqual(verdict["status"], "pass")
        self.assertEqual(sorted(verdict["detail"]["missing_evidence"]), sorted(REQUIRED_EVIDENCE))


class TestAssertionResultsNeverPassEmpty(unittest.TestCase):
    """AC-6 — assertion_results가 비거나 expected/actual 키가 없으면 pass가 아니다."""

    def test_empty_assertion_results_never_pass_on_every_repeat(self):
        for attempt in range(_REPEAT):
            with self.subTest(attempt=attempt):
                verdict = e2e_contract.build_verdict(_passing_result(assertion_results=[]))
                self.assertNotEqual(verdict["status"], "pass")
                self.assertEqual(verdict["error"], "assertion_required")

    def test_missing_expected_key_is_rejected(self):
        verdict = e2e_contract.build_verdict(
            _passing_result(
                assertions=[{"id": "a1", "expected": 200}],
                assertion_results=[{"id": "a1", "actual": 200}],
            )
        )
        self.assertNotEqual(verdict["status"], "pass")
        self.assertEqual(verdict["error"], "assertion_expected_actual_missing")

    def test_missing_actual_key_is_rejected(self):
        verdict = e2e_contract.build_verdict(
            _passing_result(
                assertions=[{"id": "a1", "expected": 200}],
                assertion_results=[{"id": "a1", "expected": 200}],
            )
        )
        self.assertNotEqual(verdict["status"], "pass")
        self.assertEqual(verdict["error"], "assertion_expected_actual_missing")

    def test_null_expected_and_actual_are_allowed_because_the_keys_exist(self):
        """§A.5 [MUST] — 값은 null일 수 있으나 키는 반드시 존재해야 한다."""
        verdict = e2e_contract.build_verdict(
            _passing_result(assertion_results=[{"id": "a1", "expected": None, "actual": None}])
        )
        self.assertEqual(verdict["status"], "pass", verdict)

    def test_expected_actual_mismatch_is_fail_not_pass(self):
        verdict = e2e_contract.build_verdict(
            _passing_result(assertion_results=[{"id": "a1", "expected": 200, "actual": 500}])
        )
        self.assertEqual(verdict["status"], "fail")
        self.assertEqual(verdict["error"], "assertion_failed")

    def test_a_declared_assertion_with_no_result_is_not_silently_dropped(self):
        verdict = e2e_contract.build_verdict(
            _passing_result(
                assertions=[{"id": "a1", "expected": 200}, {"id": "a2", "expected": "ok"}],
                assertion_results=[{"id": "a1", "expected": 200, "actual": 200}],
            )
        )
        self.assertNotEqual(verdict["status"], "pass")
        self.assertEqual(verdict["error"], "assertion_expected_actual_missing")


class TestIncompleteEvidenceIsNeverRealUsage(unittest.TestCase):
    """AC-6 — 증적이 불완전한 run은 real-usage 충실도로 기록되지 않는다."""

    def test_injected_real_usage_is_not_carried_out_of_a_failed_verdict(self):
        for kind in REQUIRED_EVIDENCE:
            observed = [item for item in REQUIRED_EVIDENCE if item != kind]
            with self.subTest(missing=kind):
                verdict = e2e_contract.build_verdict(
                    _passing_result(observed_evidence=observed, fidelity="real-usage")
                )
                normalized = verdict.get("normalized") or {}
                self.assertNotEqual(normalized.get("fidelity"), "real-usage")

    def test_empty_assertions_with_injected_real_usage_is_not_real_usage(self):
        verdict = e2e_contract.build_verdict(_passing_result(assertion_results=[], fidelity="real-usage"))
        normalized = verdict.get("normalized") or {}
        self.assertNotEqual(normalized.get("fidelity"), "real-usage")

    def test_orchestrator_never_copies_required_fidelity_into_the_result(self):
        """요구치(`required_fidelity`)를 달성치(`fidelity`)로 베끼면 증적 없는 run이
        real-usage로 기록된다. orchestrator의 달성 충실도 계산이 그 경로를 막는다."""
        from lib.e2e import orchestrator as e2e_orchestrator

        self.assertEqual(
            e2e_orchestrator._achieved_fidelity(evidence_complete=False, candidates=[], handles=[]),
            "mock",
        )
        # 증적이 완전해도 selected 후보가 없으면 real-usage가 아니다.
        self.assertEqual(
            e2e_orchestrator._achieved_fidelity(evidence_complete=True, candidates=[], handles=[]),
            "mock",
        )
        source = inspect.getsource(e2e_orchestrator._finalize)
        self.assertNotIn(
            "required_fidelity",
            source,
            "run.json의 fidelity를 시나리오 required_fidelity로 채우면 안 된다",
        )


class TestSinglePassGate(unittest.TestCase):
    """C-1 / §E.2 — pass 판정은 validate_pass_requirements 단일 관문을 통과하며 우회 경로가 없다."""

    def test_build_verdict_routes_every_pass_claim_through_the_single_gate(self):
        calls = []
        original = e2e_contract.validate_pass_requirements

        def _spy(scenario, result):
            calls.append((scenario, result))
            return original(scenario, result)

        e2e_contract.validate_pass_requirements = _spy
        try:
            verdict = e2e_contract.build_verdict(_passing_result())
        finally:
            e2e_contract.validate_pass_requirements = original
        self.assertEqual(verdict["status"], "pass")
        self.assertEqual(len(calls), 1, "pass 판정은 관문을 정확히 한 번 통과해야 한다")

    def test_no_pass_verdict_is_constructed_outside_the_gate(self):
        """E2E run 경로에서 관문 밖에 `status="pass"`를 조립하는 코드가 없다.

        검사 범위는 이 하네스가 소유한 실행 경로(`lib/e2e/**`·`lib/e2e_adapter.py`)다.
        `lib/scenario.py`의 `scenario-mark` 응답은 CLI 명령 echo이지 run 판정이 아니며
        태스크 125 소유분이므로(C-1) 범위 밖이다.
        """
        scanned = sorted((_TOOL_DIR / "lib" / "e2e").rglob("*.py")) + [_TOOL_DIR / "lib" / "e2e_adapter.py"]
        offenders = []
        for path in scanned:
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if re.search(r'"status"\s*:\s*"pass"', stripped) or re.search(r"'status'\s*:\s*'pass'", stripped):
                    # build_verdict 입력으로 pass를 **주장**하는 것은 허용된다. 금지 대상은
                    # 판정 결과를 직접 pass로 조립해 반환하는 경로다.
                    offenders.append(f"{path.relative_to(_TOOL_DIR)}:{number}: {stripped}")
        for offender in offenders:
            with self.subTest(offender=offender):
                self.assertIn(
                    "build_verdict",
                    _context_of(offender),
                    f"관문을 거치지 않은 pass 조립으로 보인다: {offender}",
                )

    def test_status_to_exit_is_the_only_source_of_exit_codes(self):
        """NR-1 — pass 아닌 판정이 새 exit 값을 만들지 않는다."""
        for status in e2e_contract.FINAL_STATUSES:
            with self.subTest(status=status):
                self.assertIn(e2e_contract.status_to_exit(status), (0, 6, 7, 18, 19, 20))

    def test_verdict_shape_is_stable_for_every_rejection_path(self):
        rejections = [
            _passing_result(assertion_results=[]),
            _passing_result(observed_evidence=[]),
            _passing_result(assertion_results=[{"id": "a1"}], assertions=[{"id": "a1", "expected": 1}]),
        ]
        for index, result in enumerate(rejections):
            with self.subTest(case=index):
                verdict = e2e_contract.build_verdict(result)
                self.assertEqual(sorted(verdict), ["detail", "error", "normalized", "ok", "status"])
                self.assertFalse(verdict["ok"])


def _context_of(offender: str) -> str:
    """`path:line: text`에서 해당 파일의 앞뒤 문맥을 돌려준다."""
    path_part, number, _ = offender.split(":", 2)
    lines = (_TOOL_DIR / path_part).read_text(encoding="utf-8").splitlines()
    index = int(number) - 1
    return "\n".join(lines[max(0, index - 6): index + 3])


if __name__ == "__main__":
    unittest.main()
