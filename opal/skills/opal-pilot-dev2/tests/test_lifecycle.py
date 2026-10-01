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
                         reviewer='r1', checks=[[sys.executable, '-c', 'assert 1+1 == 2']], rollback='Restore prior source',
                         ac_coverage=[[0]])
        value.update(extra)
        (self.task / f'{name}.md').write_text(f'# {name}\n\nConcrete user contract for arithmetic behavior.\n')
        (self.task / f'{name}.json').write_text(json.dumps(value))

    def plan_reviewed(self, reason='Independent PLAN pre-review: acceptance coverage and scope verified'):
        """168 ADD-1 — PLAN 사전심사 Layer 2(추론). reviewer가 서로 다른 --call(A/B)로
        독립 심사 pass를 현재 fingerprint에서 기록해야 PLAN→BUILD 전이가 허용된다."""
        plan = self.store.artifact('plan')[0]
        for call in ('A', 'B'):
            self.call('review', '--actor', plan['reviewer'], '--verdict', 'pass', '--reason', reason, '--call', call)

    def plan_ready(self, **plan):
        for name in ('intent', 'spec', 'plan'):
            self.artifact(name, **(plan if name == 'plan' else {}))
            if name == 'plan':
                self.plan_reviewed()
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
            if stage == 'PLAN':
                self.plan_reviewed()
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

    def test_ac_coverage_gate_blocks_uncovered_acceptance(self):
        """168 ADD-1 — plan['ac_coverage']가 intent['acceptance']의 모든 인덱스를
        커버하지 못하면 PLAN→BUILD 전이가 기계적으로(Layer 1) 거부된다."""
        self.init()
        self.artifact('intent', acceptance=['1+1 is 2', 'no regression elsewhere'])
        self.call('transition')
        self.artifact('spec')
        self.call('transition')
        # ac_coverage covers only acceptance index 0; index 1 is left uncovered.
        self.artifact('plan', ac_coverage=[[0]])
        self.assertIn('uncovered acceptance criteria', self.call('transition', ok=False)['error'])

    def test_plan_review_call_b_missing_blocks_transition(self):
        """168 ADD-1 — call A만 기록되고 call B가 없으면 PLAN→BUILD 전이가 거부된다."""
        self.init()
        for name in ('intent', 'spec'):
            self.artifact(name)
            self.call('transition')
        self.artifact('plan')
        plan = self.store.artifact('plan')[0]
        self.call('review', '--actor', plan['reviewer'], '--verdict', 'pass',
                  '--reason', 'Call A only', '--call', 'A')
        self.assertIn('plan review call B must pass', self.call('transition', ok=False)['error'])
        self.call('review', '--actor', plan['reviewer'], '--verdict', 'pass',
                  '--reason', 'Call B recorded', '--call', 'B')
        self.call('transition')
        self.assertEqual(self.store.state()['stage'], 'BUILD')

    def test_plan_review_call_a_missing_blocks_transition(self):
        """168 ADD-1 — 반대 방향: call B만 기록되고 call A가 없으면 전이가 거부된다."""
        self.init()
        for name in ('intent', 'spec'):
            self.artifact(name)
            self.call('transition')
        self.artifact('plan')
        plan = self.store.artifact('plan')[0]
        self.call('review', '--actor', plan['reviewer'], '--verdict', 'pass',
                  '--reason', 'Call B only', '--call', 'B')
        self.assertIn('plan review call A must pass', self.call('transition', ok=False)['error'])

    def test_plan_review_wrong_actor_rejected(self):
        """168 ADD-1 — plan.reviewer가 아닌 actor로 --call 리뷰를 기록하려 하면
        신원 불일치로 즉시 거부된다(기록 시점에 거부되므로 전이까지 갈 필요 없음)."""
        self.init()
        for name in ('intent', 'spec'):
            self.artifact(name)
            self.call('transition')
        self.artifact('plan')
        self.assertIn('reviewer identity mismatch',
                      self.call('review', '--actor', 'not-the-reviewer', '--verdict', 'pass',
                               '--reason', 'impersonation attempt', '--call', 'A', ok=False)['error'])

    def test_rewind_clears_plan_reviews(self):
        """168 ADD-1 — rewind는 plan_reviews를 초기화하므로, PLAN으로 되돌아가면
        이전 fingerprint에서 기록된 call A/B pass는 더 이상 유효하지 않다."""
        self.init()
        self.plan_ready()
        self.assertEqual(self.store.state()['stage'], 'BUILD')
        self.assertTrue(self.store.state()['plan_reviews'])
        self.call('rewind', '--gate', 'PLAN', '--reason', 'need re-review of the plan')
        self.assertEqual(self.store.state()['plan_reviews'], [])
        self.assertEqual(self.store.state()['stage'], 'PLAN')
        # Re-entering BUILD now requires fresh call A/B reviews at the current fingerprint.
        self.assertIn('plan review call A must pass', self.call('transition', ok=False)['error'])

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
        self.plan_reviewed()
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
        self.plan_reviewed()
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


    # ------------------------------------------------------------------
    # 173 — opd2 PLAN 사전심사: 재검증 절차 정합·회차 상한·지적 해소 추적 (RED-first)
    # ------------------------------------------------------------------
    HOLD = 'await_user: PLAN pre-review fail limit (3) reached; user release required'

    def plan_stage(self):
        """PLAN 단계까지 INTENT·DESIGN을 통과하고 plan 산출물이 있는 임시 태스크."""
        self.init()
        self.artifact('intent', acceptance=['1+1 is 2', 'no regression elsewhere'])
        self.call('transition')
        self.artifact('spec')
        self.call('transition')
        self.artifact('plan', ac_coverage=[[0, 1]])

    @staticmethod
    def finding(fid, location='plan.json files', choice='app.py 외 테스트 파일 포함 여부'):
        return {'id': fid, 'location': location, 'remaining_choice': choice}

    @staticmethod
    def resolution(rid, status='resolved', evidence='plan.json files 수정으로 해소'):
        return {'id': rid, 'status': status, 'evidence': evidence}

    def review_plan(self, call, verdict, findings=None, resolutions=None, ok=True, actor='r1',
                    reason='Independent PLAN pre-review of acceptance coverage and scope'):
        args = ['--actor', actor, '--verdict', verdict, '--reason', reason, '--call', call]
        if findings is not None:
            args += ['--findings', json.dumps(findings)]
        if resolutions is not None:
            args += ['--resolutions', json.dumps(resolutions)]
        return self.call('review', *args, ok=ok)

    def count(self):
        return len(self.store.events())

    def raw(self, *argv):
        """task 위치 인자 없이 CLI를 호출한다(verify-mark 전용). (exit code, 응답 JSON)."""
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = lc.main(list(map(str, argv)))
        return code, json.loads(out.getvalue())

    def hold_state(self):
        """fail 2건(A-1, B-1) 뒤 3번째 fail(A, A-1 해소 보고 + 새 지적 A-2)로 상한 대기에 진입한다."""
        self.plan_stage()
        self.review_plan('A', 'fail', findings=[self.finding('A-1')], resolutions=[])
        self.review_plan('B', 'fail', findings=[self.finding('B-1')], resolutions=[])
        return self.review_plan('A', 'fail', findings=[self.finding('A-2')],
                                resolutions=[self.resolution('A-1')])

    def assert_held(self, result, before):
        self.assertEqual(result['transition_action'], 'await_user', result)
        self.assertTrue(result['error'].startswith(self.HOLD), result)
        self.assertEqual(self.count(), before)

    def test_s1_replan_requires_rerecording_call_a(self):
        """173 S-1 — B fail 지적 반영으로 plan을 고치면 통과했던 A 기록이 무효가 되어
        B만 다시 pass해도 전이가 거부되고, A까지 다시 pass해야 BUILD가 된다."""
        self.plan_stage()
        self.review_plan('A', 'pass')
        self.review_plan('B', 'fail', findings=[self.finding('B-1')])
        self.artifact('plan', ac_coverage=[[0, 1]], rollback='Restore prior source after fixing B-1')
        self.review_plan('B', 'pass', findings=[], resolutions=[self.resolution('B-1')])
        self.assertIn('plan review call A must pass at current fingerprint',
                      self.call('transition', ok=False)['error'])
        self.review_plan('A', 'pass')
        self.call('transition')
        self.assertEqual(self.store.state()['stage'], 'BUILD')

    def test_s3_third_fail_holds_and_blocks_everything(self):
        """173 S-3(a)~(g) — 3번째 fail은 저장되며 blocked/decision_request가 되고, 이후
        pass·fail·transition·verify-mark·rewind·unblock은 await_user로 거부된다."""
        third = self.hold_state()
        self.assertEqual(third['transition_action'], 'blocked')
        self.assertEqual(third['report_type'], 'decision_request')
        self.assertEqual(self.store.state()['blocked'], self.HOLD)
        before = self.count()
        self.assert_held(self.review_plan('A', 'pass', findings=[], resolutions=[self.resolution('A-2')],
                                          ok=False), before)
        self.assert_held(self.review_plan('A', 'fail', findings=[self.finding('A-3')],
                                          resolutions=[self.resolution('A-2')], ok=False), before)
        self.assert_held(self.call('transition', ok=False), before)
        code, result = self.raw('verify-mark', '--task', self.task, '--key', 'plan.plan_md')
        self.assertEqual(code, 2, result)
        self.assert_held(result, before)
        self.assert_held(self.call('rewind', '--gate', 'DESIGN', '--reason', 'try to bypass', ok=False), before)
        self.assert_held(self.call('unblock', '--reason', 'r', '--reference', 'r', ok=False), before)
        status = self.call('status')
        self.assertEqual(status['result']['blocked'], self.HOLD)
        self.assertEqual(status['transition_action'], 'blocked')

    def test_s3_other_block_reason_is_not_overwritten(self):
        """173 S-3(h) — 다른 사유의 blocked가 먼저 있어도 상한 대기 시 그 값은 덮어쓰이지 않고
        transition 오류는 같은 await_user 문구로 시작한다."""
        self.plan_stage()
        self.call('block', '--reason', 'other')
        self.review_plan('A', 'fail', findings=[self.finding('A-1')], resolutions=[])
        self.review_plan('B', 'fail', findings=[self.finding('B-1')], resolutions=[])
        self.review_plan('A', 'fail', findings=[self.finding('A-2')], resolutions=[self.resolution('A-1')])
        self.assertEqual(self.store.state()['blocked'], 'other')
        self.assert_held(self.call('transition', ok=False), self.count())

    def test_s4_reset_rejections_and_release(self):
        """173 S-4(a)(b)(d) — 해제는 실명 actor+reference만 허용하고 이력을 보존하며,
        이후 fail은 새 기준(floor)부터 3건까지 허용된다."""
        self.hold_state()
        before = self.count()
        self.call('plan-review-reset', '--actor', 'coordinator', '--reference', 'user message 1',
                  '--reason', 'release', ok=False)
        self.assertEqual(self.count(), before)
        self.call('plan-review-reset', '--actor', 'captain', '--reason', 'release', ok=False)
        self.assertEqual(self.count(), before)
        history = list(self.store.state()['plan_reviews'])
        self.call('plan-review-reset', '--actor', 'captain', '--reference', '사용자 승인 메시지',
                  '--reason', 'user approved another attempt')
        state = self.store.state()
        self.assertIsNone(state['blocked'])
        self.assertEqual(self.store.events()[-1]['kind'], 'plan_review_reset')
        self.assertEqual(state['plan_reviews'], history)
        self.assertEqual(state['plan_review_floor'], len(history))
        # 해제 뒤 fail 2건은 허용되고 아직 상한 대기가 아니다.
        self.review_plan('A', 'fail', findings=[self.finding('A-3')], resolutions=[self.resolution('A-2')])
        self.review_plan('B', 'fail', findings=[self.finding('B-2')], resolutions=[self.resolution('B-1')])
        self.assertIsNone(self.store.state()['blocked'])
        # rewind는 plan_reviews와 floor를 함께 초기화한다(상한 우회 없음).
        self.call('rewind', '--gate', 'DESIGN', '--reason', 'rework design')
        state = self.store.state()
        self.assertEqual(state['plan_reviews'], [])
        self.assertEqual(state.get('plan_review_floor'), 0)
        self.artifact('spec')
        self.call('transition')
        self.artifact('plan', ac_coverage=[[0, 1]])
        self.review_plan('A', 'fail', findings=[self.finding('A-1')], resolutions=[])
        self.review_plan('B', 'fail', findings=[self.finding('B-1')], resolutions=[])
        self.assertIsNone(self.store.state()['blocked'])
        self.review_plan('A', 'fail', findings=[self.finding('A-2')], resolutions=[self.resolution('A-1')])
        self.assertEqual(self.store.state()['blocked'], self.HOLD)

    def test_s4_reset_rejected_without_hold(self):
        """173 S-4(c) — 상한 대기가 아니면 plan-review-reset은 거부되고 원장이 바뀌지 않는다."""
        self.plan_stage()
        before = self.count()
        result = self.call('plan-review-reset', '--actor', 'captain', '--reference', '사용자 승인 메시지',
                           '--reason', 'no hold', ok=False)
        self.assertIn('no plan review hold to reset', result['error'])
        self.assertEqual(self.count(), before)

    def test_s5_first_round_format_rejections(self):
        """173 S-5(a)~(g) — 첫 회차 fail/pass의 findings 형식 위반은 모두 거부되고 원장·fail 수에
        반영되지 않으며, 올바른 fail은 findings/resolutions/open_findings를 남긴다."""
        self.plan_stage()
        before = self.count()
        good = self.finding('A-1')
        bad = [
            ('A', 'fail', None),                                              # (a) findings 없음
            ('A', 'fail', [{'id': 'A-1', 'remaining_choice': 'x'}]),          # (b) location 누락
            ('A', 'fail', [{'id': 'A-1', 'location': 'x'}]),                  # (b) remaining_choice 누락
            ('A', 'fail', [self.finding('A-1', location='  ')]),              # (b) 공백 location
            ('A', 'fail', [self.finding('A-1', choice='')]),                  # (b) 공백 remaining_choice
            ('A', 'fail', [self.finding('B-1')]),                             # (c) Call A에 B-1
            ('A', 'fail', [self.finding('A-01')]),                            # (d) 앞자리 0
            ('A', 'fail', [self.finding('A-x')]),                             # (d) 숫자 아님
            ('A', 'fail', [self.finding('A-1'), self.finding('A-1')]),        # (e) 중복
            ('A', 'pass', [good]),                                            # (f) pass에 findings
        ]
        for call, verdict, findings in bad:
            result = self.review_plan(call, verdict, findings=findings, ok=False)
            self.assertTrue(result['error'], (call, verdict, findings))
            self.assertEqual(self.count(), before, (call, verdict, findings))
            self.assertEqual(self.store.state()['plan_reviews'], [])
        self.review_plan('A', 'fail', findings=[good])
        record = self.store.state()['plan_reviews'][-1]
        self.assertEqual(record['findings'], [good])
        self.assertEqual(record['resolutions'], [])
        self.assertEqual(record['open_findings'], [good])

    def test_s6_resolution_reports_and_call_independence(self):
        """173 S-6(a)~(k) — 해소 보고는 이전 지적 id 집합과 정확히 일치해야 하고, 위반은 거부되며,
        미해소 지적은 open_findings로 이월된다. Call B는 Call A와 독립이다."""
        self.plan_stage()
        a1, a2 = self.finding('A-1'), self.finding('A-2', location='plan.json checks')
        self.review_plan('A', 'fail', findings=[a1, a2])
        # Call B 첫 기록은 Call A 지적과 무관하게 --resolutions 없이 성공한다.
        self.review_plan('B', 'pass')
        before = self.count()
        cover = 'resolutions must cover exactly the previous findings [A-1, A-2]'
        r1, r2 = self.resolution('A-1'), self.resolution('A-2')
        new3 = [self.finding('A-3')]
        for resolutions in (None, [r1], [r1, r2, self.resolution('A-9')], [r1, r1, r2]):   # (a)~(d)
            result = self.review_plan('A', 'fail', findings=new3, resolutions=resolutions, ok=False)
            self.assertIn(cover, result['error'])
            self.assertEqual(self.count(), before)
        rejects = [
            ('fail', new3, [r1, dict(r2, status='done')]),                        # (e)
            ('fail', new3, [r1, dict(r2, evidence='  ')]),                        # (f)
            ('pass', [], [r1, self.resolution('A-2', status='unresolved')]),      # (g)
            ('fail', [], [r1, r2]),                                               # (h)
            ('fail', [self.finding('A-1')], [r1, r2]),                            # (i)
        ]
        for verdict, findings, resolutions in rejects:
            result = self.review_plan('A', verdict, findings=findings, resolutions=resolutions, ok=False)
            self.assertTrue(result['error'])
            self.assertEqual(self.count(), before)
        unresolved = self.resolution('A-2', status='unresolved', evidence='아직 남은 선택이 있음')
        self.review_plan('A', 'fail', findings=new3, resolutions=[r1, unresolved])           # (j)
        record = self.store.state()['plan_reviews'][-1]
        self.assertEqual([f['id'] for f in record['open_findings']], ['A-2', 'A-3'])
        self.review_plan('A', 'pass', findings=[],
                         resolutions=[r2, self.resolution('A-3')])                          # (k)
        self.assertEqual(self.store.state()['plan_reviews'][-1]['verdict'], 'pass')

    def legacy_fixture(self, fails, passes=()):
        """변경 전 형식 원장 — findings/resolutions 키가 없는 사전심사 기록을 Store.save로 직접 심는다."""
        self.plan_stage()
        state = self.store.state()
        fingerprint = self.store.fingerprint(state)
        for call, verdict in [*fails, *passes]:
            report = {'call': call, 'actor': 'r1', 'verdict': verdict, 'reason': 'legacy record',
                      'fingerprint': fingerprint}
            state['plan_reviews'].append(report)
            self.store.save(state, 'plan_review', report)

    def test_s7_legacy_ledger_status_and_transition(self):
        """173 S-7(a)(b) — 변경 전 형식 fail 3건과 현재 지문의 A·B pass가 있는 원장은 조회되고
        전이도 변경 전 pass 기록으로 성공한다."""
        self.legacy_fixture([('A', 'fail'), ('B', 'fail'), ('A', 'fail')], [('A', 'pass'), ('B', 'pass')])
        self.assertEqual(self.call('status')['result']['stage'], 'PLAN')
        self.call('transition')
        self.assertEqual(self.store.state()['stage'], 'BUILD')

    def test_s7_legacy_fails_not_counted_nor_previous_findings(self):
        """173 S-7(c)(d) — 변경 전 fail은 상한 수·이전 지적에 들어가지 않으므로 새 형식 fail이
        --resolutions 없이 저장되고 상한 대기가 되지 않는다."""
        self.legacy_fixture([('A', 'fail')])
        self.review_plan('A', 'fail', findings=[self.finding('A-1')])
        self.assertIsNone(self.store.state()['blocked'])

    def test_s7_legacy_three_fails_then_new_fail(self):
        """173 S-7(d) — 변경 전 fail 3건 뒤 새 형식 fail 기록도 상한 대기를 만들지 않는다."""
        self.legacy_fixture([('A', 'fail'), ('B', 'fail'), ('A', 'fail')])
        self.review_plan('A', 'fail', findings=[self.finding('A-1')])
        self.review_plan('B', 'fail', findings=[self.finding('B-1')])
        self.assertIsNone(self.store.state()['blocked'])
        self.assertIsNone(self.store.state().get('plan_review_floor'))


if __name__ == '__main__':
    unittest.main()
