"""OPPB Controller DONE renderer 공개 CLI 계약."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess


RUN_SH = pathlib.Path(__file__).resolve().parents[1] / "run.sh"


def test_render_done_uses_acceptance_and_evidence_hashes(tmp_path):
    run_root = tmp_path / "run"
    task_path = tmp_path / "tasks" / "142-sample"
    evidence = run_root / "evidence" / "T01" / "ev-1.json"
    evidence.parent.mkdir(parents=True)
    task_path.mkdir(parents=True)
    evidence.write_text('{"result":"pass"}\n', encoding="utf-8")
    (run_root / "workgraph.json").write_text(
        json.dumps({
            "mini_tasks": [{
                "id": "T01", "capability": "sample", "profile": "standard",
                "state": "accepted", "runner_attempt_id": "T01.runner.1",
            }]
        }),
        encoding="utf-8",
    )
    (run_root / "acceptance.json").write_text(
        json.dumps({
            "created_at": "2026-09-20T00:00:00Z",
            "criteria": [{
                "id": "AC-1", "description": "sample", "satisfied": True,
                "evidence": ["ev-1"],
            }],
            "evidence_index": {"ev-1": {"task_id": "T01", "criteria": ["AC-1"]}},
        }),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "bash", str(RUN_SH), "workgraph", "render-done",
            "--run-root", str(run_root), "--task-path", str(task_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    done = (task_path / "DONE.md").read_text(encoding="utf-8")
    assert payload["criteria"] == 1
    assert payload["accepted_tasks"] == 1
    assert hashlib.sha256(evidence.read_bytes()).hexdigest() in done
    assert "## 회고적 학습 후보" in done
    assert "`.opal/MEMORY.json`" in done
