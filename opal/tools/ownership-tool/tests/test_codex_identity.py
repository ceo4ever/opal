# @header {
#   "module": "ownership_tool.tests.test_codex_identity",
#   "layer": "test",
#   "domain": "opal-pipeline",
#   "description": "Codex 신원 해석과 공개 시작 CLI의 부모 신원 격리 계약을 검증한다.",
#   "exports": [],
#   "depends": [
#     "ownership_tool.ownership_core",
#     "ownership_tool.lease",
#     "ownership_tool.cli"
#   ]
# }
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

import pytest

TOOL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL))
from ownership_tool import ownership_core as core, lease

IDENTITY_KEYS = ('OPAL_SESSION_ID', 'CODEX_SESSION_ID', 'CODEX_THREAD_ID', 'CLAUDE_CODE_SESSION_ID', 'ORCA_SESSION_ID')
CHILD = '11111111-1111-4111-8111-111111111111'


def cli(*args, extra_env=None):
    env = {k: v for k, v in os.environ.items() if k not in IDENTITY_KEYS and k not in ('OPAL_PROJECT_ROOT', 'CLAUDE_ENV_FILE')}
    env['PYTHONPATH'] = str(TOOL)
    env.update(extra_env or {})
    return subprocess.run([sys.executable, '-m', 'ownership_tool.cli', *map(str, args)], env=env, text=True, capture_output=True, timeout=20)


def test_s1_codex_only_identity_and_public_status(tmp_path):
    assert core.resolve_session_id({'CODEX_SESSION_ID': CHILD}, {}) == CHILD
    assert lease.claim(tmp_path, session_id=CHILD, claim_source='state_transition')['ok']
    result = cli('status', '--task-path', tmp_path, extra_env={'CODEX_SESSION_ID': CHILD})
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(result.stdout)
    assert data['session_id'] == CHILD
    assert data['classification'] == 'current_session_owned'


@pytest.mark.parametrize('value', ['', '  ', None, 123])
def test_s1_invalid_native_id_does_not_use_thread(value):
    assert core.resolve_session_id({'CODEX_SESSION_ID': value, 'CODEX_THREAD_ID': CHILD}, {}) is None


def test_s2_neutral_claude_and_payload_priority():
    env = {'OPAL_SESSION_ID': 'neutral', 'CLAUDE_CODE_SESSION_ID': 'claude', 'CODEX_SESSION_ID': CHILD}
    assert core.resolve_session_id(env, {'session_id': 'payload'}) == 'neutral'
    del env['OPAL_SESSION_ID']
    assert core.resolve_session_id(env, {'session_id': 'payload'}) == 'claude'
    assert core.resolve_session_id({}, {'session_id': 'payload'}) == 'payload'
    assert core.hook_session_id({}) is None


def test_s9_session_launch_strips_parent_identity_preserves_command(tmp_path):
    output = tmp_path / 'child-env.json'
    script = 'import os,json,pathlib; pathlib.Path(' + repr(str(output)) + ').write_text(json.dumps(dict(os.environ)))'
    command = shlex.join([sys.executable, '-c', script])
    result = cli('session-launch', '--command', command, extra_env={**dict.fromkeys(IDENTITY_KEYS, 'parent'), 'KEEP_TASK_VALUE': 'literal value'})
    assert result.returncode == 0, result.stdout + result.stderr
    actual = json.loads(output.read_text())
    assert not (set(IDENTITY_KEYS) & actual.keys())
    assert actual['KEEP_TASK_VALUE'] == 'literal value'


def test_s9_codex_start_claims_native_id_and_rejects_inherited_parent(tmp_path):
    root = tmp_path / 'worktree'
    task = root / 'tasks' / '220-test'
    task.mkdir(parents=True)
    (root / '.opal').mkdir()
    (root / '.opal/AGENT.md').write_text('# fixture')
    (root / '.opal/task-ownership.json').write_text(json.dumps({'allocator_root': str(tmp_path), 'task_home': str(root), 'task_folder': task.name, 'task_path': str(task), 'artifact_repo': '.', 'task_ownership_version': 2}))
    assert lease.claim(task, session_id='parent', claim_source='state_transition')['ok']
    assert lease.handoff(task, session_id='parent', to_worktree_root=root)['ok']
    owner = task / 'run/.runtime/owner.json'
    before = owner.read_bytes()
    conflict = cli('codex-start', '--cwd', root, extra_env={'CODEX_SESSION_ID': CHILD, 'OPAL_SESSION_ID': 'parent'})
    assert conflict.returncode != 0
    assert owner.read_bytes() == before
    result = cli('codex-start', '--cwd', root, extra_env={'CODEX_SESSION_ID': CHILD})
    assert result.returncode == 0, result.stdout + result.stderr
    record = json.loads(owner.read_text())
    assert record['owner_session_id'] == CHILD
    assert record['status'] == 'active'
    assert record['generation'] == 2
    session = core.read_json(core.session_registry_path(root, CHILD))
    assert session['ok'] and session['data']['session_id'] == CHILD
    assert session['data']['cwd'] == str(root)
    heartbeat_before = record['heartbeat_at']
    repeated = cli('codex-start', '--cwd', root, extra_env={'CODEX_SESSION_ID': CHILD})
    assert repeated.returncode == 0, repeated.stdout + repeated.stderr
    assert json.loads(owner.read_text())['heartbeat_at'] >= heartbeat_before


def test_task163_s6_codex_start_defers_only_registry_write_denied(tmp_path, monkeypatch):
    """S-6: an EPERM-style registry failure keeps the native lease and asks the hub to finalize ownership."""
    from ownership_tool import codex_adapter, heartbeat_hook, session_start_hook

    root = tmp_path / "root"
    (root / ".opal").mkdir(parents=True)
    (root / ".opal" / "AGENT.md").write_text("fixture")
    monkeypatch.setattr(session_start_hook, "handle", lambda *a, **k: {"registered": False, "task_path": str(root / "tasks" / "x"), "lease_claimed": True, "classification": "unowned", "diagnostics": ["registry_write_denied"]})
    monkeypatch.setattr(heartbeat_hook, "handle", lambda *a, **k: {"ok": True})
    result = codex_adapter.start(root, {"CODEX_SESSION_ID": CHILD})
    assert result["ok"] is True
    assert result["diagnostic"] == "registry_owner_deferred_to_hub"
