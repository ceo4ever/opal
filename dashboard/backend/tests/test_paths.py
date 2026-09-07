"""
@header {
  "module": "tests.test_paths",
  "layer": "test",
  "domain": "console",
  "description": "dashboard.backend.paths.hub_root()가 opal/core/references/hub-root-cases.json 골든 케이스 C-1~C-7 전건에서 opal-harness.md §2.5 (4) 규칙과 동일한 문자열을 반환하는지 대조한다(H-1). 절대 프리픽스를 임의로 정해 input_rel/expected_rel을 그 위에 조립하는 합성 경로 방식으로 실제 파일시스템 생성 없이 검증한다. 항등 케이스(C-3·C-6)는 반환값이 입력 문자열과 바이트 동일함을 명시적으로 단정한다(TS-012). 골든 표는 이 스위트 전용 사본이 아니라 brain-tool·code-scan 스위트와 공유하는 단일 파일이다(TS-060).",
  "exports": [],
  "depends": ["paths"]
}
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from dashboard.backend import paths

# 골든 표 경로 — 3스위트 공유 단일 파일(사본 금지, TS-060).
# dashboard/backend/tests/test_paths.py -> parents[0]=tests, [1]=backend, [2]=dashboard, [3]=repo_root
_CASES_PATH = (
    Path(__file__).resolve().parents[3] / "opal" / "core" / "references" / "hub-root-cases.json"
)


def _load_cases():
    with open(_CASES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["cases"]


_CASES = _load_cases()

# 항등(반환값 == 입력)이어야 하는 케이스 — TS-012가 요구하는 바이트 동일 단정 대상.
_IDENTITY_CASE_IDS = {"C-3", "C-6"}

# 합성 절대 프리픽스 — 실제 파일시스템 생성 불필요(§3.2.3 골든 표 설계 의도).
_PREFIX = "/synthetic/root"


def _build_input(case):
    return f"{_PREFIX}/{case['input_rel']}" if case["input_rel"] else _PREFIX


def _build_expected(case):
    return f"{_PREFIX}/{case['expected_rel']}" if case["expected_rel"] else _PREFIX


class TestHubRootGoldenCases:
    """골든 케이스 C-1~C-7 전건 동치 검증(TS-011)."""

    @pytest.mark.parametrize("case", _CASES, ids=lambda c: c["id"])
    def test_hub_root_matches_golden_case(self, case):
        input_path = _build_input(case)
        expected_path = _build_expected(case)

        actual = paths.hub_root(input_path)

        assert actual == expected_path, (
            f"{case['id']} ({case['desc']}): "
            f"expected={expected_path!r} actual={actual!r}"
        )

    @pytest.mark.parametrize(
        "case", [c for c in _CASES if c["id"] in _IDENTITY_CASE_IDS], ids=lambda c: c["id"]
    )
    def test_identity_cases_are_byte_identical_to_input(self, case):
        """항등 케이스는 반환값이 입력 문자열과 바이트 동일해야 한다(TS-012)."""
        input_path = _build_input(case)

        actual = paths.hub_root(input_path)

        assert actual == input_path
        assert actual is not None
        assert isinstance(actual, str)
