# @header
# module: worktree_launcher.tests.test_adapter_orca
# layer: test
# domain: worktree-launcher
# description: RED-first — worktree_launcher.adapters.orca.launch() 공개 계약 검증 (S-16). fixtures/README.md 계약대로 `orca-json-response.json`의 `{WT}` 플레이스홀더를 tmp 경로로 치환해 읽고, handle이 `adapter_handle`로 반환됨을 단언한다.
# exports: (none — pytest module)
# depends: worktree_launcher.adapters.orca (미구현), ownership-tool fixtures/launcher
"""RED 테스트 — 구현 전."""
from __future__ import annotations

import json

from conftest import load_launcher_fixture


def test_orca_launch_invokes_expected_argument_shape(monkeypatch, tmp_path):
    """호출 인자가 `terminal create --worktree path:<worktree_root> --command … --json` 형태이고
    worktree/checkout 생성 서브명령 0건. handle은 `adapter_handle`로 반환된다(S-16)."""
    from worktree_launcher.adapters import orca  # RED

    recorded = {}
    response = load_launcher_fixture("orca-json-response.json", hub=tmp_path, wt_parent=tmp_path)

    def fake_run(args, **kwargs):
        recorded["args"] = args
        class _P:
            returncode = 0
            stdout = json.dumps(response)
            stderr = ""
        return _P()

    monkeypatch.setattr(orca, "_run_subprocess", fake_run)
    result = orca.launch(worktree_root=tmp_path, command="claude")

    args = recorded["args"]
    assert "terminal" in args and "create" in args
    assert any(a.startswith("--worktree") or a == "--worktree" for a in args)
    assert "--json" in args
    joined = " ".join(args)
    assert "worktree add" not in joined
    assert "checkout -b" not in joined
    assert result["adapter_handle"] == response["terminal"]["handle"]


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
