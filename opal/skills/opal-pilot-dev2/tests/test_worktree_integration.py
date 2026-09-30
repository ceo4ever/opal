import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


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
            # Entire fixture, including Git common dir and worktree, lives in this temporary directory.


if __name__ == '__main__':
    unittest.main()
