"""
@header {
  "module": "test_lifecycle",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "opal-pilot-dev2/scripts/lifecycle.py의 Store 상태기계와 CLI(main) 전이 계약을 실제 형제 FW 도구 state-tool(state_tool.py) 마킹과 함께 검증한다 — 원장 전이가 진짜 state.json 행과 동기화되는지, opd2 pipeline.json 기반 초기화가 올바른지 확인한다.",
  "exports": ["LifecycleTests"],
  "depends": ["opal-pilot-dev2/scripts/lifecycle", "state_tool"]
}
"""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/lifecycle.py'
spec = importlib.util.spec_from_file_location('lifecycle', SCRIPT)
lc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lc)

# 168 W-9 — 원장(opd2-ledger.json) 커밋이 매 전이마다 형제 FW 도구 state-tool의
# `mark --task-step <key> --done`을 호출하므로(lifecycle.py Store.save(), H-1), 이
# 테스트가 검증하는 전이가 실제로 성공하려면 그 호출이 성공할 대상(진짜
# state-tool `state.json`)이 먼저 존재해야 한다. SKILL_ROOT는 lifecycle.py 자신의
# ROOT(parents[1])와 동일한 opd2 스킬 루트 — references/pipeline.json 경로 판정에 쓴다.
SKILL_ROOT = Path(__file__).resolve().parents[1]
OPAL_ROOT = SKILL_ROOT.parents[1]
STATE_TOOL_PY = OPAL_ROOT / 'tools' / 'state-tool' / 'state_tool.py'
PIPELINE_JSON = SKILL_ROOT / 'references' / 'pipeline.json'


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='opd2-lifecycle-')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        self.task = self.repo / 'tasks/change'
        self.task.mkdir(parents=True)
        (self.repo / 'app.py').write_text('value = 1\n')
        self.store = lc.Store(self.task)

    def call(self, command, *args, ok=True):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = lc.main([command, str(self.task), *map(str, args)])
        result = json.loads(out.getvalue())
        self.assertEqual(code == 0, ok, result)
        return result

    def state_tool_mark(self, key, *extra_args):
        """168 W-9 — Coordinator가 semi-agentic에서 명시 완료하는
        task.user_confirm/design.user_confirm/plan.user_confirm 행을 이 테스트가
        직접 재현할 때 쓰는 실제 state-tool 호출(PLAN Decisions "lifecycle.py 전이
        ↔ state.json 행 매핑")."""
        result = subprocess.run(
            [sys.executable, str(STATE_TOOL_PY), 'mark', str(self.task),
             '--task-step', key, '--done', *extra_args],
            capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def init(self, mode='agentic', delivery='build'):
        # 168 W-9 — lifecycle.py init(원장 생성) 전에 진짜 state-tool 태스크를
        # 먼저 만든다. opd2는 ACTOR_SKILLS가 아니라 resolve-start init_args에
        # --rows-from이 실리지 않으므로 opd2 pipeline.json을 직접 넘긴다.
        result = subprocess.run(
            [sys.executable, str(STATE_TOOL_PY), 'init', str(self.task),
             '--skill', 'opd2', '--mode', mode, '--workspace', 'hub',
             '--rows-from', str(PIPELINE_JSON)],
            capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.call('init', '--repo', self.repo, '--change-id', 'C1', '--workspace', 'hub',
                  '--mode', mode, '--delivery', delivery)

    def artifact(self, name, **extra):
        value = {'change_id': 'C1', 'risk': 'normal', 'open_questions': []}
        if name == 'intent':
            value.update(problem='Bug adds one', outcome='Correct sum', acceptance=['1+1 is 2'],
                         non_goals=[], constraints=['No new dependencies'])
        elif name == 'spec':
            value.update(source_sha256=self.store.artifact('intent')[1], requirements=['Correct arithmetic'],
                         design='Remove offset', policy_versions=['local test policy v1'])
        elif name == 'plan':
            value.update(source_sha256=self.store.artifact('spec')[1], files=['app.py'], builder='b1', verifier='v1',
                         reviewer='r1', checks=[[sys.executable, '-c', 'assert 1+1 == 2']], rollback='Restore prior source')
        value.update(extra)
        (self.task / f'{name}.md').write_text(f'# {name}\n\nConcrete user contract for arithmetic behavior.\n')
        (self.task / f'{name}.json').write_text(json.dumps(value))

    def plan_ready(self, **plan):
        for name in ('intent', 'spec', 'plan'):
            self.artifact(name, **(plan if name == 'plan' else {}))
            self.call('transition')

    def evidence(self, role, ok=True):
        plan = self.store.artifact('plan')[0]
        return self.call('collect-evidence', '--role', role, '--actor', plan.get(role, 'operator'),
                         '--argv', json.dumps(plan['checks'][0]), ok=ok)

    def declare_worker_durations_unknown(self):
        """168 W-9 — state-tool의 103 강제 2단 CLOSE 진입 게이트는 DESIGN/PLAN/EXECUTE
        stage의 '작업' 행(design.spec_md·plan.plan_md·execute.implement)에 워커 소요
        기록 또는 `--worker-duration-unknown` 선언이 없으면 close.done_md mark를
        차단한다(worker_duration_undeclared). lifecycle.py의 `_mark_state_tool()`은
        `--done`만 넘기므로, opd2 자체 게이트(RED-first·evidence·역할 분리)와는 무관한
        이 FW 공통 게이트를 이 테스트가 대신 충족시킨다 — 이미 done인 행을 같은 키로
        다시 mark해도 상태·타임스탬프는 바뀌지 않고 선언 필드만 추가된다."""
        for key in ('design.spec_md', 'plan.plan_md', 'execute.implement'):
            self.state_tool_mark(key, '--worker-duration-unknown')

    def reviewed(self, delivery='build'):
        self.init(delivery=delivery)
        self.plan_ready()
        (self.repo / 'app.py').write_text('value = 2\n')
        self.evidence('builder')
        self.call('transition')
        self.evidence('verifier')
        self.call('transition')
        self.call('review', '--actor', 'r1', '--verdict', 'pass', '--reason', 'Independent behavior and contract checked')
        (self.task / 'DONE.md').write_text('# Done\nActual evidence linked.\n')
        self.declare_worker_durations_unknown()

    def test_full_build_and_resume(self):
        self.reviewed()
        self.call('transition')
        state = self.call('status')['result']
        self.assertEqual((state['stage'], state['outcome']), ('CLOSED', 'ready_for_merge'))
        self.assertEqual(len(state['evidence']), 2)
        self.assertGreater(len(self.store.events()), 8)

    def test_semi_requires_three_real_approval_records(self):
        """168 W-9 — opd2 게이트 전이(intent/spec/plan)는 lifecycle.py의 자체
        승인(approve)만으로 진행되지만, state-tool 쪽 task.user_confirm·
        design.user_confirm 행은 semi-agentic에서 자동 승인되지 않는 TASK/DESIGN
        MODE_BOUNDARY_STAGES라 다음 stage의 opd2 게이트 행을 mark하기 전에
        Coordinator가 명시로 완료해야 한다(PLAN Decisions 매핑표)."""
        self.init('semi-agentic')
        for stage, name in lc.ARTIFACTS.items():
            self.artifact(name)
            self.assertIn('await_user', self.call('transition', ok=False)['error'])
            self.call('approve', '--gate', stage, '--actor', 'captain', '--reference', f'user-message-{stage}')
            if stage == 'DESIGN':
                self.state_tool_mark('task.user_confirm', '--owner', 'user')
            elif stage == 'PLAN':
                self.state_tool_mark('design.user_confirm', '--owner', 'user')
            self.call('transition')
        self.assertEqual(self.store.state()['stage'], 'BUILD')

    def test_high_risk_and_downgrade(self):
        self.init()
        self.artifact('intent', risk='high')
        self.call('transition', ok=False)
        self.call('approve', '--gate', 'INTENT', '--actor', 'captain', '--reference', 'approved-high')
        self.call('transition')
        self.artifact('spec')
        self.assertIn('risk downgrade', self.call('transition', ok=False)['error'])

    def test_missing_evidence_and_same_actor(self):
        self.init()
        self.plan_ready()
        self.call('transition', ok=False)
        self.call('collect-evidence', '--role', 'verifier', '--actor', 'b1', '--argv', '["true"]', ok=False)

    def test_scope_includes_untracked_files(self):
        self.init()
        self.plan_ready()
        (self.repo / 'unexpected.txt').write_text('outside approved scope')
        self.assertIn('scope violation', self.call('verify-scope', ok=False)['error'])
        self.evidence('builder', ok=False)

    def test_stale_artifact(self):
        self.init()
        self.plan_ready()
        (self.task / 'intent.md').write_text('Changed intent that invalidates previous approval')
        self.assertIn('stale artifact', self.call('transition', ok=False)['error'])

    def test_stale_code_evidence(self):
        self.init()
        self.plan_ready()
        self.evidence('builder')
        (self.repo / 'app.py').write_text('value = 3\n')
        self.assertIn('missing successful', self.call('transition', ok=False)['error'])

    def test_failed_command_cannot_advance(self):
        self.init()
        self.plan_ready(checks=[[sys.executable, '-c', 'raise SystemExit(1)']])
        self.evidence('builder')
        self.assertIn('latest builder check failed', self.call('transition', ok=False)['error'])

    def test_logs_cannot_be_changed(self):
        self.init()
        self.plan_ready()
        self.evidence('builder')
        (self.store.ledger_dir / 'opd2-evidence-1.log').write_text('forged pass')
        self.assertIn('log changed', self.call('transition', ok=False)['error'])

    def test_latest_review_fail_wins(self):
        self.reviewed()
        self.call('review', '--actor', 'r1', '--verdict', 'fail', '--reason', 'Found regression')
        self.call('transition', ok=False)

    def test_rewind_invalidates_and_is_bounded(self):
        self.init()
        self.plan_ready()
        for _ in range(3):
            self.call('rewind', '--gate', 'BUILD', '--reason', 'repair failed behavior')
        self.call('rewind', '--gate', 'BUILD', '--reason', 'fourth repair', ok=False)
        self.assertEqual(self.store.state()['retries'], 3)

    def test_journal_integrity(self):
        """168 W-9 — 원장은 단일 파일(<task>/run/opd2-ledger.json)이라 별도
        projection 캐시가 더 이상 없다(AC-2, C-3). 해시 체인 위변조는 여전히
        integrity 오류로 거부된다는 기존 기계 게이트만 유지한다."""
        self.init()
        self.assertEqual(self.call('status')['result']['stage'], 'INTENT')
        journal = self.store.ledger_path
        journal.write_text(journal.read_text().replace('INTENT', 'CLOSED'))
        self.assertIn('integrity', self.call('status', ok=False)['error'])

    def test_unknown_schema_keyword_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unsupported schema'):
            lc.validate('a', {'type': 'string', 'pattern': '^b$'})

    def test_source_hash_mismatch(self):
        self.init()
        self.artifact('intent')
        self.call('transition')
        self.artifact('spec', source_sha256='wrong')
        self.call('transition', ok=False)

    def test_independence_gate(self):
        self.init()
        for name in ('intent', 'spec'):
            self.artifact(name)
            self.call('transition')
        self.artifact('plan', reviewer='b1')
        self.call('transition', ok=False)

    def test_release_requires_approval_and_real_commands(self):
        self.reviewed(delivery='release')
        self.call('transition', ok=False)
        self.call('approve', '--gate', 'RELEASE', '--actor', 'release-manager', '--reference', 'approved-test-release')
        self.call('transition')
        self.call('transition', ok=False)
        self.evidence('deployment')
        self.call('transition')
        self.evidence('observation', ok=False)
        self.call('approve', '--gate', 'OBSERVE', '--actor', 'service-owner', '--reference', 'approved-test-observation')
        self.evidence('observation')
        self.call('transition')
        self.assertEqual(self.store.state()['outcome'], 'observed')

    def test_worktree_no_hub_fallback(self):
        self.call('init', '--repo', self.repo, '--change-id', 'C1', ok=False)
        self.assertFalse(self.store.events())

    def test_red_before_green_and_test_lock(self):
        self.init()
        for name in ('intent', 'spec'):
            self.artifact(name)
            self.call('transition')
        (self.repo / 'test_app.py').write_text('assert False\n')
        self.artifact('plan', files=['app.py', 'test_app.py'], protected_tests=['test_app.py'],
                      red_checks=[{'argv': [sys.executable, 'test_app.py'], 'exit_code': 1,
                                   'reason': 'Known arithmetic reproduction'}])
        self.call('transition', ok=False)
        self.call('collect-evidence', '--role', 'red', '--actor', 'v1',
                  '--argv', json.dumps([sys.executable, 'test_app.py']))
        self.call('transition')
        (self.repo / 'test_app.py').write_text('assert True\n')
        self.assertIn('protected test changed', self.call('verify-scope', ok=False)['error'])

    def test_source_mutating_check_not_pass_evidence(self):
        self.init()
        command = [sys.executable, '-c', 'from pathlib import Path; Path("app.py").write_text("changed")']
        self.plan_ready(checks=[command])
        self.evidence('builder')
        self.assertFalse(self.store.state()['evidence'][-1]['stable'])
        self.call('transition', ok=False)

    def test_block_and_explicit_mode_change(self):
        self.init()
        self.artifact('intent')
        self.call('block', '--reason', 'external contract unresolved')
        self.call('transition', ok=False)
        self.call('unblock', '--reason', 'resolved', ok=False)
        self.call('unblock', '--reason', 'resolved', '--reference', 'user-decision-7')
        self.call('set-mode', '--mode', 'semi-agentic', '--reason', 'user requested', ok=False)
        self.call('set-mode', '--mode', 'semi-agentic', '--reason', 'user requested', '--reference', 'message-8')
        self.call('transition', ok=False)

    def test_actual_bug_red_fix_green_review_close(self):
        (self.repo / 'app.py').write_text('def add(a, b):\n    return a + b + 1\n')
        self.init()
        for name in ('intent', 'spec'):
            self.artifact(name)
            self.call('transition')
        (self.repo / 'test_app.py').write_text('from app import add\nassert add(2, 3) == 5\nassert add(-1, 1) == 0\n')
        check = [sys.executable, '-B', 'test_app.py']
        self.artifact('plan', files=['app.py', 'test_app.py'], checks=[check], protected_tests=['test_app.py'],
                      red_checks=[{'argv': check, 'exit_code': 1, 'reason': 'Addition has an extra offset'}])
        self.call('collect-evidence', '--role', 'red', '--actor', 'v1', '--argv', json.dumps(check))
        self.assertIn('AssertionError', (self.store.ledger_dir / 'opd2-evidence-1.log').read_text())
        self.call('transition')
        protected_before = (self.repo / 'test_app.py').read_bytes()
        (self.repo / 'app.py').write_text('def add(a, b):\n    return a + b\n')
        self.evidence('builder')
        self.call('transition')
        self.evidence('verifier')
        self.call('transition')
        self.call('review', '--actor', 'r1', '--verdict', 'pass', '--reason', 'Both arithmetic cases pass; tests unchanged')
        (self.task / 'DONE.md').write_text('# Done\nReal RED and GREEN subprocess logs retained.\n')
        self.declare_worker_durations_unknown()
        self.call('transition')
        self.assertEqual(self.store.state()['outcome'], 'ready_for_merge')
        self.assertEqual((self.repo / 'test_app.py').read_bytes(), protected_before)
        # 168 W-9 — lifecycle.py는 더 이상 STATE.md/AGENTIC-LOG.md를 직접 쓰지 않는다
        # (AC-2, PLAN Decisions "상태 SSOT는 state-tool"). state-tool init/mark가
        # 소유하는 FW STATE.md만 존재를 확인한다(AGENTIC-LOG.md는 Coordinator가
        # 별도로 관리하는 태스크 문서라 lifecycle.py·state-tool 어느 쪽도 만들지 않는다).
        self.assertTrue((self.task / 'STATE.md').is_file())


if __name__ == '__main__':
    unittest.main()
