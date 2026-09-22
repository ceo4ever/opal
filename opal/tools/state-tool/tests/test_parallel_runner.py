"""
@header {
  "module": "test_parallel_runner",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "state-tool 파일 단위 병렬 pytest runner의 전건 실행·실패 전파 계약 테스트",
  "exports": ["TestParallelRunner"]
}
"""

import pathlib
import subprocess
import sys
import tempfile
import unittest


RUNNER = pathlib.Path(__file__).with_name("parallel_runner.py")


class TestParallelRunner(unittest.TestCase):
    def _run(self, files: dict[str, str]):
        with tempfile.TemporaryDirectory() as tmp:
            tests_dir = pathlib.Path(tmp)
            for name, source in files.items():
                (tests_dir / name).write_text(source, encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--jobs",
                    "2",
                    "--tests-dir",
                    str(tests_dir),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_all_files_pass_and_are_reported(self):
        result = self._run(
            {
                "test_alpha.py": "def test_alpha():\n    assert True\n",
                "test_beta.py": "def test_beta():\n    assert 2 + 2 == 4\n",
            }
        )

        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("PASS test_alpha.py", result.stdout)
        self.assertIn("PASS test_beta.py", result.stdout)
        self.assertIn("2/2 files passed", result.stdout)

    def test_failure_is_propagated_after_every_file_runs(self):
        result = self._run(
            {
                "test_fail.py": "def test_fail():\n    assert False\n",
                "test_pass.py": "def test_pass():\n    assert True\n",
            }
        )

        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertIn("FAIL test_fail.py", result.stdout)
        self.assertIn("PASS test_pass.py", result.stdout)
        self.assertIn("Failed files: test_fail.py", result.stdout)


if __name__ == "__main__":
    unittest.main()
