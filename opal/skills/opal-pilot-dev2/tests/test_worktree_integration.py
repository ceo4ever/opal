"""
@header {
  "module": "test_worktree_integration",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "opal-pilot-dev2/scripts/worktree.py create와 scripts/lifecycle.py init의 실제 연동을 검증한다 — worktree-tool이 발급한 워크트리 receipt로 lifecycle.py가 실제 워크트리 경로에 원장을 초기화하고 stage/mode/workspace가 기대값과 일치하는지, lifecycle stage↔worktree-tool checkpoint --stage 매핑 어휘가 깨지지 않았는지 확인한다.",
  "exports": ["WorktreeIntegrationTests"],
  "depends": ["opal-pilot-dev2/scripts/worktree", "opal-pilot-dev2/scripts/lifecycle"]
}
"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


# 168 W-9 — references/execution.md §체크포인트·마감의 opd2 lifecycle stage ↔
# worktree-tool checkpoint --stage 매핑(PLAN→PLAN, BUILD→EXECUTE, VERIFY/REVIEW→TEST,
# CLOSED→CLOSE). --stage는 worktree-tool 쪽에서 enum이 아닌 자유 문자열이라 잘못된
# 값이어도 "invalid stage" 같은 전용 오류가 없다 — 그래서 이 매핑이 실제로 그대로
# 전달되는지는 각 값이 checkpoint의 동일한 후속 검사(소유권 판정)까지 도달하는지로
# 확인한다(모두 같은 도메인 오류로 실패해야 한다 — 인자 파싱 단계에서 걸러지는
# 값이 하나라도 있으면 매핑 어휘가 깨진 것이다).
CHECKPOINT_STAGE_MAPPING = {
    'PLAN': 'PLAN', 'BUILD': 'EXECUTE', 'VERIFY': 'TEST', 'REVIEW': 'TEST', 'CLOSED': 'CLOSE',
}


class WorktreeIntegrationTests(unittest.TestCase):
    def test_real_opal_create_and_lifecycle_init(self):
        with tempfile.TemporaryDirectory(prefix='opd2-wt-') as temp:
            hub = Path(temp).resolve() / 'hub'
            hub.mkdir()
            subprocess.run(['git', 'init', '-q', '-b', 'main', str(hub)], check=True)
            for name, content in {
                'src/app.py': 'answer = 42\n',
                'tasks/.keep': '', '.opal/AGENT.md': '# Test project\n',
                '.opal/MEMORY.json': '{}',
                '.gitignore': '.opal-worktrees/\n',
                '.opal/worktree.json': json.dumps({'layout': 'monorepo', 'repos': ['src'],
                    'taskCapsuleCone': ['tasks', '.opal'], 'baseBranch': 'main', 'copy': [], 'setup': []})
            }.items():
                path = hub / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            subprocess.run(['git', '-C', str(hub), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(hub), '-c', 'user.name=OPD2 test', '-c',
                            'user.email=opd2@example.invalid', '-c', 'commit.gpgsign=false',
                            'commit', '-qm', 'seed'], check=True)
            run = subprocess.run([sys.executable, str(ROOT / 'scripts/worktree.py'), 'create',
                '--project-root', str(hub), '--task', '901', '--skill', 'opd2', '--task-folder', '901-opd2-test'],
                capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            receipt = json.loads(run.stdout)
            self.assertTrue(receipt['ok'])
            self.assertNotEqual(Path(receipt['worktree_root']), hub)
            self.assertTrue((Path(receipt['worktree_root']) / 'src/app.py').is_file())
            receipt_path = Path(temp) / 'receipt.json'
            receipt_path.write_text(run.stdout)
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/lifecycle.py'), 'init',
                receipt['task_path'], '--repo', receipt['worktree_root'], '--change-id', 'C901',
                '--mode', 'semi-agentic', '--worktree-receipt', str(receipt_path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            state = json.loads(result.stdout)['result']
            self.assertEqual((state['mode'], state['workspace'], state['stage']),
                             ('semi-agentic', 'worktree', 'INTENT'))
            status = subprocess.run([sys.executable, str(ROOT / 'scripts/worktree.py'), 'status',
                '--project-root', str(hub), '--task', '901'], capture_output=True, text=True)
            self.assertEqual(status.returncode, 0, status.stdout + status.stderr)

            # 168 W-9 — execution.md의 opd2 stage ↔ checkpoint --stage 매핑값이 그대로
            # 전달되는지 확인한다. 이 fixture는 소유권 registry lease를 발급받지 않으므로
            # 모든 값이 checkpoint_ownership_denied로 실패해야 한다 — 하나라도 다른 오류
            # (예: argparse 사용법 오류나 별도 invalid-stage 코드)로 갈리면 매핑 문자열이
            # worktree-tool까지 그대로 전달되지 않은 것이다.
            worktree_root = Path(receipt['worktree_root'])
            (worktree_root / 'src/app.py').write_text('answer = 43\n')
            subprocess.run(['git', '-C', str(worktree_root), 'add', '.'], check=True)
            for opd2_stage, mapped_stage in CHECKPOINT_STAGE_MAPPING.items():
                with self.subTest(opd2_stage=opd2_stage, mapped_stage=mapped_stage):
                    checkpoint = subprocess.run(
                        [sys.executable, str(ROOT / 'scripts/worktree.py'), 'checkpoint',
                         '--project-root', str(hub), '--task', '901', '--stage', mapped_stage,
                         '--mode', 'agentic'],
                        capture_output=True, text=True)
                    self.assertEqual(checkpoint.returncode, 1, checkpoint.stdout + checkpoint.stderr)
                    payload = json.loads(checkpoint.stdout)
                    self.assertEqual(payload.get('error'), 'checkpoint_ownership_denied', payload)
            # Entire fixture, including Git common dir and worktree, lives in this temporary directory.


if __name__ == '__main__':
    unittest.main()
