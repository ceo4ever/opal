# @header
# module: worktree_launcher.tests.test_adapter_generic
# layer: test
# domain: worktree-launcher
# description: RED-first — worktree_launcher.adapters.generic / opal_agent_fallback 공개 계약 검증 (S-17)
# exports: (none — pytest module)
# depends: worktree_launcher.adapters.generic, worktree_launcher.adapters.opal_agent_fallback (미구현)
"""RED 테스트 — 구현 전."""
from __future__ import annotations

import ast
from pathlib import Path


def test_generic_adapter_substitutes_template_placeholders_only(tmp_path):
    """generic: 템플릿 {cwd}·{command} 치환만."""
    from worktree_launcher.adapters import generic  # RED

    template = "some-term --cwd {cwd} --run {command}"
    rendered = generic.render_template(template, cwd=str(tmp_path), command="claude")
    assert str(tmp_path) in rendered
    assert "claude" in rendered
    assert "{cwd}" not in rendered and "{command}" not in rendered


def test_generic_adapter_source_has_zero_os_name_branches():
    """generic 소스에 OS 이름 분기 0건(정적 검사)."""
    from worktree_launcher.adapters import generic  # RED

    src = Path(generic.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    forbidden_literals = {"darwin", "linux", "win32", "windows"}
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value.lower() in forbidden_literals:
                found.append(node.value)
    assert not found, f"OS-name branch literal found: {found}"


def test_opal_agent_fallback_launch_calls_agent_config_with_claude_provider(monkeypatch, tmp_path):
    """fallback: AgentConfig(provider="claude", cwd=<worktree_root>) 호출,
    반환 session id가 adapter_handle에 기록되고 session_id로 재호출(resume) 가능."""
    from worktree_launcher.adapters import opal_agent_fallback  # RED

    captured = {}

    def fake_call_agent(config):
        captured["config"] = config
        return {"session_id": "fallback-sess-0001"}

    monkeypatch.setattr(opal_agent_fallback, "call_agent", fake_call_agent)
    result = opal_agent_fallback.launch(worktree_root=tmp_path, command="claude")

    cfg = captured["config"]
    assert cfg.provider == "claude"
    assert str(cfg.cwd) == str(tmp_path)
    assert result["adapter_handle"] == "fallback-sess-0001"
    assert "launch_mode" in result


def test_fallback_reported_cwd_mismatch_triggers_launch_failed(monkeypatch, tmp_path):
    """fake가 reported_cwd != worktree_root를 보고하면 S-15의 launch_failed 경로로 이어진다."""
    from worktree_launcher.adapters import opal_agent_fallback  # RED

    def fake_call_agent(config):
        return {"session_id": "fallback-sess-0002", "reported_cwd": "/somewhere/else"}

    monkeypatch.setattr(opal_agent_fallback, "call_agent", fake_call_agent)
    result = opal_agent_fallback.launch(worktree_root=tmp_path, command="claude")
    assert result.get("failure_reason") == "launch_failed"
