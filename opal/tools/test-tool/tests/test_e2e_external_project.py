"""
@header {
  "module": "test_e2e_external_project",
  "task": "159-260926-opds-E2E-테스트환경-설정체계",
  "layer": "test",
  "domain": "opal-tools",
  "description": "W-6 (S-12) — 저장소 밖 임의 프로젝트를 관통하는 E2E 자동화. OS 임시 폴더에 git 초기화된 표본 프로젝트(실제 FastAPI 앱 + api profile test-scenario.json)를 만들고, CLI subprocess로 `env-inspect`(설정 부재·후보 제안) → `env-inspect`가 제시한 `suggested.command` 그대로 설정 작성 → `env-validate` → `env-check`(ready) → `e2e run`(pass, real-http) 순서로 관통해, '탐지된 앱 = 실제로 기동되는 앱'을 단언한다. 사용자 HOME·~/.opal·이 저장소 파일은 건드리지 않으며 임시 폴더는 종료 시 제거한다.",
  "scenarios": ["S-12"],
  "exports": ["TestExternalProjectWalkthrough"]
}
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
_TEST_TOOL_PY = _TOOL_DIR / "test_tool.py"
_PYTHON = sys.executable

sys.path.insert(0, str(_TOOL_DIR))

from lib import e2e_contract  # noqa: E402
from lib.e2e import orchestrator as e2e_orchestrator  # noqa: E402

# 실제 FastAPI 앱 — env-inspect의 python 후보 탐지 정규식(`app = FastAPI(`)이 찾는 대상과
# 실제로 기동되는 서비스가 같은 파일이다(대역 분기 없음). `/health` 문자열이 있어
# inspect가 http health 후보(`{"type":"http","path":"/health"}`)까지 제안한다.
_APP_SOURCE = """\
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/items")
def items():
    return ["alpha", "beta"]
"""

_REQUIREMENTS = "fastapi\nuvicorn\n"


def _write_scenario(task_dir: pathlib.Path) -> None:
    scenario = {
        "id": "w6-external-items",
        "acceptance_ref": ["AC-S12"],
        "type": "integration",
        "expected": "GET /items가 200과 배열을 돌려준다",
        "red_required": False,
        "required_fidelity": e2e_orchestrator.FIDELITY_REAL_HTTP,
        "surface_ref": "svc-api",
        "surface_kind": "api",
        "profile": "api",
        "actors": ["service"],
        "steps": [
            {
                "id": "st-items",
                "executor": "api",
                "step_role": "verify",
                "method": "GET",
                "url": "/items",
                "timeout_ms": 30000,
            }
        ],
        "assertions": [
            {
                "id": "w6-a1",
                "verifier": "response",
                "match": "equals",
                "source_seq": 1,
                "field": "status",
                "expected": 200,
            },
            {
                "id": "w6-a2",
                "verifier": "response",
                "match": "equals",
                "source_seq": 1,
                "field": "0",
                "expected": "alpha",
            },
            {
                "id": "w6-a3",
                "verifier": "response",
                "match": "equals",
                "source_seq": 1,
                "field": "1",
                "expected": "beta",
            },
        ],
        "required_evidence": ["metadata", "server_log", "action_log", "assertions", "cleanup"],
    }
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "test-scenario.json").write_text(
        json.dumps(
            {
                "schema_version": "2.0",
                "task_id": task_dir.name,
                "locked": False,
                "scenarios": [scenario],
            }
        ),
        encoding="utf-8",
    )


class TestExternalProjectWalkthrough(unittest.TestCase):
    """[MUST] S-12 — 저장소 밖 표본 프로젝트를 `e2e` CLI만으로 관통한다."""

    def setUp(self):
        self.project_root = pathlib.Path(tempfile.mkdtemp(prefix="w6-external-project-"))
        self.artifact_root = pathlib.Path(tempfile.mkdtemp(prefix="w6-external-artifacts-"))
        self.addCleanup(shutil.rmtree, self.project_root, ignore_errors=True)
        self.addCleanup(shutil.rmtree, self.artifact_root, ignore_errors=True)

        subprocess.run(
            ["git", "init", "-q", str(self.project_root)],
            check=True,
            capture_output=True,
        )
        (self.project_root / "app.py").write_text(_APP_SOURCE, encoding="utf-8")
        (self.project_root / "requirements.txt").write_text(_REQUIREMENTS, encoding="utf-8")

        self.task_dir = self.project_root / "task"
        _write_scenario(self.task_dir)

    def _cli(self, *args: str, timeout: int = 60) -> subprocess.CompletedProcess:
        return subprocess.run(
            [_PYTHON, str(_TEST_TOOL_PY), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def _snapshot_tree(self) -> set:
        return {
            str(path.relative_to(self.project_root))
            for path in self.project_root.rglob("*")
            if ".git" not in path.parts
        }

    def test_walkthrough_env_inspect_then_setup_then_validate_check_run(self):
        # 1) env-inspect — 설정 부재, api 후보 존재(실제 FastAPI 앱을 근거로), 트리 미변경.
        before_tree = self._snapshot_tree()
        proc = self._cli("e2e", "env-inspect", "--project-root", str(self.project_root))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        inspected = json.loads(proc.stdout)
        self.assertTrue(inspected["ok"])
        self.assertFalse(inspected["config"]["present"])
        api_candidates = [c for c in inspected["surface_candidates"] if c.get("kind") == "api"]
        self.assertTrue(api_candidates, inspected["surface_candidates"])
        self.assertIn("app.py", api_candidates[0]["evidence"])
        self.assertEqual(before_tree, self._snapshot_tree(), "env-inspect가 트리를 바꿨다")

        # 제안 명령이 실제로 그 파일(app.py의 FastAPI 앱)을 가리키는지 — 탐지된 앱과
        # 기동될 앱이 같은 대상임을 명령 자체로 확인한다(대역 아님).
        suggested = api_candidates[0]["suggested"]
        self.assertIn("uvicorn", suggested["command"])
        self.assertIn("app:app", suggested["command"])
        self.assertEqual(suggested["health"], {"type": "http", "path": "/health", "expect_status": 200})

        # 2) 설정 작성 — env-inspect가 제시한 suggested.command를 그대로 서비스 command로
        #    쓴다(치환 토큰 {python}/{host}/{port}는 이미 그 형태). 표면은 api 하나만
        #    (web 표면 미포함).
        config = {
            "schema_version": "1.0",
            "services": [
                {
                    "id": "api",
                    "command": suggested["command"],
                    "cwd": suggested.get("cwd") or ".",
                    "health": suggested["health"],
                    "startup_timeout_s": 20,
                }
            ],
            "surfaces": [
                {"id": "svc-api", "kind": "api", "service": "api", "health_path": "/health"},
            ],
        }
        env_dir = self.project_root / ".opal" / "e2e"
        env_dir.mkdir(parents=True, exist_ok=True)
        (env_dir / "environment.json").write_text(json.dumps(config), encoding="utf-8")

        # 3) env-validate — exit 0.
        proc = self._cli("e2e", "env-validate", "--project-root", str(self.project_root))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        validated = json.loads(proc.stdout)
        self.assertTrue(validated["ok"])
        self.assertEqual(validated["summary"], {"services": 1, "surfaces": 1})

        # 4) env-check — exit 0, ready:true, 서버 프로세스·포트 잔존 없음.
        proc = self._cli(
            "e2e", "env-check",
            "--project-root", str(self.project_root),
            "--artifact-root", str(self.artifact_root),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        checked = json.loads(proc.stdout)
        self.assertTrue(checked["ready"], checked)
        self.assertTrue(all(item["ok"] for item in checked["secrets"]), checked["secrets"])
        self.assertTrue(
            all(s["status"] == "ready" for s in checked["surfaces"]), checked["surfaces"]
        )

        # 5) e2e run — pass, real-http, assertion expected/actual 기록. 기동된 서비스가
        #    바로 env-inspect가 가리킨 app.py의 FastAPI 앱이다.
        run_artifact_root = pathlib.Path(tempfile.mkdtemp(prefix="w6-external-run-"))
        self.addCleanup(shutil.rmtree, run_artifact_root, ignore_errors=True)
        proc = self._cli(
            "e2e", "run",
            "--scenario", "w6-external-items",
            "--task-path", str(self.task_dir),
            "--target", "source-worktree",
            "--worktree-root", str(self.project_root),
            "--artifact-root", str(run_artifact_root),
            timeout=120,
        )
        self.assertTrue(proc.stdout.strip(), proc.stderr[-2000:])
        run_payload = json.loads(proc.stdout)
        self.assertEqual(run_payload["status"], "pass", run_payload)
        self.assertEqual(proc.returncode, e2e_contract.status_to_exit("pass"))

        run_json_path = pathlib.Path(run_payload["run_json_path"])
        run_json = json.loads(run_json_path.read_text(encoding="utf-8"))
        self.assertEqual(run_json["fidelity"], e2e_orchestrator.FIDELITY_REAL_HTTP)

        assertions_path = run_json_path.parent / "assertions.json"
        assertions = json.loads(assertions_path.read_text(encoding="utf-8"))["results"]
        self.assertEqual(len(assertions), 3)
        for result in assertions:
            self.assertIn("expected", result)
            self.assertIn("actual", result)
            self.assertEqual(result["expected"], result["actual"], result)
            self.assertTrue(result["passed"], result)

        self.assertEqual(run_json["cleanup"], "complete")
        self.assertEqual(len(run_json["lease_released"]), 1)


if __name__ == "__main__":
    unittest.main()
