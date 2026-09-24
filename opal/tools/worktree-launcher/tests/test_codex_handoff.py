# @header {
#   "module": "worktree_launcher.tests.test_codex_handoff",
#   "layer": "test",
#   "domain": "opal-workspace",
#   "description": "명시 launcher owner의 실제 lease 이관 및 실패 취소 신원 고정 계약을 검증한다.",
#   "exports": [],
#   "depends": [
#     "worktree_launcher.launcher_core",
#     "ownership_tool.lease",
#     "conftest"
#   ]
# }
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ownership-tool'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ownership_tool import lease
from worktree_launcher import launcher_core
from conftest import build_launcher_hub, load_launcher_fixture, read_meta


def setup_hub(tmp_path):
    hub = build_launcher_hub(tmp_path, prior_state='hub_owned', prior_generation=0)
    task = hub.worktree_root / 'tasks/220-test'
    task.mkdir(parents=True)
    meta = read_meta(hub.meta_path)
    meta.update(task_folder=task.name, task_path=str(task))
    hub.meta_path.write_text(json.dumps(meta))
    assert lease.claim(task, session_id='hub-explicit', claim_source='state_transition')['ok']
    return hub, task


class Terminal:
    name = 'generic'

    def __init__(self, hub, task, monkeypatch, fail=False):
        self.hub, self.task, self.monkeypatch, self.fail = hub, task, monkeypatch, fail
        self.calls, self.closed, self.pending = [], [], None

    def launch(self, worktree_root, command):
        self.calls.append((worktree_root, command))
        self.pending = json.loads((self.task / 'run/.runtime/owner.json').read_text())
        report = load_launcher_fixture('fake_process-success.json', self.hub.hub, self.hub.wt_parent)
        if self.fail:
            self.monkeypatch.setenv('OPAL_SESSION_ID', 'ambient-changed-after-handoff')
            report['prompt_id'] = None
        return report

    def close(self, *, handle):
        self.closed.append(handle)
        return {'exit_code': 0}


def test_s3_explicit_owner_handoff_with_disagreeing_ambient(tmp_path, monkeypatch):
    hub, task = setup_hub(tmp_path)
    monkeypatch.setenv('OPAL_SESSION_ID', 'ambient-other')
    adapter = Terminal(hub, task, monkeypatch)
    result = launcher_core.run(adapter, hub_root=hub.hub, task=hub.task, worktree_root=hub.worktree_root, command='codex', owner_session_id='hub-explicit')
    assert result['ok'], result
    assert len(adapter.calls) == 1
    assert adapter.pending['handoff_from_session_id'] == 'hub-explicit'
    assert adapter.pending['owner_session_id'] is None
    assert adapter.pending['status'] == 'handoff_pending'


def test_s4_cancel_reuses_explicit_id_after_ambient_changes(tmp_path, monkeypatch):
    hub, task = setup_hub(tmp_path)
    monkeypatch.setenv('OPAL_SESSION_ID', 'hub-explicit')
    adapter = Terminal(hub, task, monkeypatch, fail=True)
    result = launcher_core.run(adapter, hub_root=hub.hub, task=hub.task, worktree_root=hub.worktree_root, command='codex', owner_session_id='hub-explicit')
    assert not result['ok']
    assert len(adapter.calls) == 1
    assert adapter.pending['handoff_from_session_id'] == 'hub-explicit'
    restored = json.loads((task / 'run/.runtime/owner.json').read_text())
    assert restored['status'] == 'active', result
    assert restored['owner_session_id'] == 'hub-explicit'
    assert 'handoff_from_session_id' not in restored
    assert result['lease_handoff_cancel']['ok']
    assert len(adapter.closed) == 1
    assert read_meta(hub.meta_path)['execution_ownership']['state'] == 'hub_owned'
