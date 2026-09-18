# @header
# module: worktree_launcher.tests.test_adapter_orca
# layer: test
# domain: worktree-launcher
# description: RED-first — worktree_launcher.adapters.orca.launch() 공개 계약 검증 (S-16)
# exports: (none — pytest module)
# depends: worktree_launcher.adapters.orca (미구현), ownership-tool fixtures/launcher
"""RED 테스트 — 구현 전."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

FIXTURES_ROOT = (
    Path(__file__).parent.parent.parent / "ownership-tool" / "tests" / "fixtures" / "launcher"
)


def test_orca_launch_invokes_expected_argument_shape(monkeypatch, tmp_path):
    """호출 인자가 `terminal create --worktree path:<worktree_root> --command … --json` 형태이고
    worktree/checkout 생성 서브명령 0건."""
    from worktree_launcher.adapters import orca  # RED

    recorded = {}

    def fake_run(args, **kwargs):
        recorded["args"] = args
        response = json.loads((FIXTURES_ROOT / "orca-json-response.json").read_text(encoding="utf-8"))
        class _P:
            returncode = 0
            stdout = json.dumps(response)
            stderr = ""
        return _P()

    monkeypatch.setattr(orca, "_run_subprocess", fake_run)
    orca.launch(worktree_root=tmp_path, command="claude")

    args = recorded["args"]
    assert "terminal" in args and "create" in args
    assert any(a.startswith("--worktree") or a == "--worktree" for a in args)
    assert "--json" in args
    forbidden = {"worktree", "checkout"}
    joined = " ".join(args)
    assert "worktree add" not in joined
    assert "checkout -b" not in joined


def test_orca_absent_returns_failure_no_fallback(monkeypatch, tmp_path):
    """orca 부재·비-0 종료 → adapter 실패 반환(자동 폴백 없음)."""
    from worktree_launcher.adapters import orca  # RED

    def fake_run(args, **kwargs):
        raise FileNotFoundError("orca not found")

    monkeypatch.setattr(orca, "_run_subprocess", fake_run)
    result = orca.launch(worktree_root=tmp_path, command="claude")
    assert result["exit_code"] != 0
    assert result.get("fallback_attempted", False) is False


def test_prompt_receipt_missing_falls_back_to_sessionstart_claim_observation(tmp_path):
    """prompt receipt를 --json에서 얻지 못하면 SessionStart claim 관측 대체 경로가
    launch_mode와 함께 기록된다."""
    from worktree_launcher.adapters import orca  # RED

    response = {"ok": True, "terminal": {"handle": "orca-term-0002"}}
    result = orca.parse_response(response)
    assert "launch_mode" in result
