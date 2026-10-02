"""
@header {
  "module": "test_split_surface",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool 분할의 외부 표면 보존과 분할 사실을 검증한다. 분할 전 state_tool.py에서 추출한 fixture(최상위 이름 집합·ERROR_CODES 59종·서브커맨드 목록)를 분할 후 state_tool 모듈이 모두 유지하는지, state_tool_parts 9개 모듈이 존재하고 state_tool.py가 진입점 규모(1,000줄 미만)인지 확인한다.",
  "exports": ["TestSurfacePreserved", "TestSplitStructure"],
  "depends": ["state_tool.py", "state_tool_parts/*.py", "fixtures/state_tool_surface.json"]
}
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

_TOOL_DIR = Path(__file__).parent.parent
_FIXTURE = Path(__file__).parent / "fixtures" / "state_tool_surface.json"
_PARTS_DIR = _TOOL_DIR / "state_tool_parts"
_STATE_TOOL_PY = _TOOL_DIR / "state_tool.py"

_EXPECTED_PARTS = (
    "codes",
    "base",
    "run_log",
    "journal",
    "guards",
    "gates",
    "commands_core",
    "commands_run",
    "cli",
)
_EXPECTED_ERROR_CODE_COUNT = 59
_MAX_ENTRYPOINT_LINES = 1000

if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))
import state_tool as ST  # noqa: E402


def _load_fixture() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _help_subcommands() -> list[str]:
    """`state_tool.py --help`(공개 CLI 표면)의 서브커맨드 이름 목록을 출력에서 읽는다."""
    result = subprocess.run(
        [sys.executable, str(_STATE_TOOL_PY), "--help"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"--help exit {result.returncode}: {result.stderr}"
    names: list[str] = []
    in_block = False
    for line in result.stdout.splitlines():
        if line.startswith("positional arguments:"):
            in_block = True
            continue
        if in_block:
            if not line.strip():
                break
            m = re.match(r"^    (\S+)(?:\s|$)", line)
            if m:
                names.append(m.group(1))
    return names


class TestSurfacePreserved(unittest.TestCase):
    """분할 전 표면이 분할 후에도 그대로다 (AC-4, C-1)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.fx = _load_fixture()

    def test_fixture_is_pre_split_snapshot(self) -> None:
        """fixture 자체가 분할 전 규모(이름 수백 개·코드 59종·서브커맨드 25종)를 담고 있다."""
        self.assertGreaterEqual(len(self.fx["top_level_names"]), 290)
        self.assertEqual(len(self.fx["error_codes"]), _EXPECTED_ERROR_CODE_COUNT)
        self.assertEqual(len(self.fx["subcommands"]), 25)
        for must in ("main", "build_parser", "ERROR_CODES", "cmd_advance", "_derive_next_action",
                     "_COMPLETE_STATUSES", "_check_evidence", "_build_new_state_md",
                     "get_kst_datetime", "_import_ownership_lease", "_import_run_log_core"):
            self.assertIn(must, self.fx["top_level_names"], f"fixture에 {must} 누락")

    def test_top_level_names_superset(self) -> None:
        """분할 전 최상위 이름(밑줄 시작 포함)이 전부 state_tool 모듈에서 읽힌다."""
        missing = [n for n in self.fx["top_level_names"] if not hasattr(ST, n)]
        self.assertEqual(missing, [], f"state_tool 모듈에서 사라진 이름 {len(missing)}건: {missing[:20]}")

    def test_error_codes_preserved(self) -> None:
        """ERROR_CODES는 59종이고 키 집합이 분할 전과 같다."""
        self.assertEqual(len(ST.ERROR_CODES), _EXPECTED_ERROR_CODE_COUNT)
        self.assertEqual(sorted(ST.ERROR_CODES.keys()), self.fx["error_codes"])

    def test_help_subcommands_identical(self) -> None:
        """`--help`가 보여주는 서브커맨드 목록이 분할 전과 같다."""
        self.assertEqual(sorted(_help_subcommands()), self.fx["subcommands"])

    def test_build_parser_subcommands_identical(self) -> None:
        """build_parser()가 등록한 서브커맨드 집합이 분할 전과 같다."""
        import argparse

        parser = ST.build_parser()
        subs: list[str] = []
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                subs = list(action.choices.keys())
        self.assertEqual(sorted(subs), self.fx["subcommands"])


class TestSplitStructure(unittest.TestCase):
    """분할 사실 — 책임별 9개 모듈과 진입점 규모 (AC-3, AC-4)."""

    def test_parts_package_exists(self) -> None:
        self.assertTrue(_PARTS_DIR.is_dir(), f"{_PARTS_DIR} 디렉토리가 있어야 함")
        self.assertTrue((_PARTS_DIR / "__init__.py").is_file(), "state_tool_parts/__init__.py가 있어야 함")

    def test_nine_part_modules_exist(self) -> None:
        missing = [m for m in _EXPECTED_PARTS if not (_PARTS_DIR / f"{m}.py").is_file()]
        self.assertEqual(missing, [], f"state_tool_parts/ 아래 누락 모듈: {missing}")

    def test_no_extra_part_modules(self) -> None:
        """모듈 수는 정확히 9개다(__init__ 제외)."""
        found = sorted(p.stem for p in _PARTS_DIR.glob("*.py") if p.stem != "__init__") if _PARTS_DIR.is_dir() else []
        self.assertEqual(found, sorted(_EXPECTED_PARTS))

    def test_state_tool_py_is_entrypoint_sized(self) -> None:
        lines = len(_STATE_TOOL_PY.read_text(encoding="utf-8").splitlines())
        self.assertLess(lines, _MAX_ENTRYPOINT_LINES, f"state_tool.py가 {lines}줄 — 진입점 수준(1,000줄 미만)이어야 함")


if __name__ == "__main__":
    unittest.main()
