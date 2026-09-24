"""
@header {
  "module": "test_event_loader_design_event",
  "layer": "test",
  "domain": "opal-harness",
  "description": "events.json stage.design 이벤트 정적 계약(required_docs 5종·load)과 기존 stage.* 문서 목록 및 opwt·opp·opsdd SKILL.md 단계→이벤트 매핑의 main 대비 불변성.",
  "exports": [],
  "depends": ["event_loader"]
}
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
LOADER = REPO_ROOT / "opal" / "tools" / "event-loader" / "event_loader.py"

# DEC-13: stage.design required_docs id 목록
STAGE_DESIGN_EXPECTED_DOC_IDS = [
    "analysis-core",
    "citation-rules",
    "red-first",
    "scenario-gate",
    "design-gate",
]

# 기존 세 이벤트의 required_docs id 목록(불변 기대값) — events.json 실측
STAGE_ANALYSIS_EXPECTED_DOC_IDS = ["analysis-core", "citation-rules"]
STAGE_PLAN_EXPECTED_DOC_IDS = ["citation-rules", "pm-review-gate"]
STAGE_TEST_SCENARIO_EXPECTED_DOC_IDS = ["red-first", "scenario-gate"]

PILOT_SKILL_MDS = [
    REPO_ROOT / "opal" / "skills" / "opal-pilot-write-tech" / "SKILL.md",
    REPO_ROOT / "opal" / "skills" / "opal-pilot-project" / "SKILL.md",
    REPO_ROOT / "opal" / "skills" / "opal-pilot-sdd" / "SKILL.md",
]


def _run(*args: str) -> tuple[subprocess.CompletedProcess[str], dict]:
    completed = subprocess.run(
        [sys.executable, str(LOADER), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError):
        payload = {}
    return completed, payload


def _required_doc_ids(events_json: dict, event_id: str) -> list[str]:
    for event in events_json.get("events", []):
        if event.get("id") == event_id:
            return [doc.get("id") for doc in event.get("required_docs", [])]
    return []


class DesignEventCliContractTest(unittest.TestCase):
    def test_static_check_ok(self):
        completed, payload = _run("static-check", "--source-root", str(REPO_ROOT))
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        self.assertTrue(payload.get("ok"), payload)

    def test_stage_design_required_doc_ids(self):
        events_path = REPO_ROOT / "opal" / "core" / "references" / "events.json"
        events_json = json.loads(events_path.read_text(encoding="utf-8"))
        doc_ids = _required_doc_ids(events_json, "stage.design")
        self.assertEqual(doc_ids, STAGE_DESIGN_EXPECTED_DOC_IDS, events_json)

        # 기존 세 이벤트 목록 불변
        self.assertEqual(
            _required_doc_ids(events_json, "stage.analysis"),
            STAGE_ANALYSIS_EXPECTED_DOC_IDS,
        )
        self.assertEqual(
            _required_doc_ids(events_json, "stage.plan"),
            STAGE_PLAN_EXPECTED_DOC_IDS,
        )
        self.assertEqual(
            _required_doc_ids(events_json, "stage.test_scenario"),
            STAGE_TEST_SCENARIO_EXPECTED_DOC_IDS,
        )

    def test_stage_design_loads_via_public_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            deployed = Path(directory) / "deployed"
            deployed.mkdir()
            completed, payload = _run(
                "load", "--event", "stage.design",
                "--source-root", str(REPO_ROOT),
                "--deployed-root", str(deployed),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
            self.assertTrue(payload.get("ok"), payload)
            doc_ids = [doc.get("id") for doc in payload.get("documents", [])]
            self.assertEqual(doc_ids, STAGE_DESIGN_EXPECTED_DOC_IDS, payload)

    def test_pilot_skills_do_not_reference_stage_design(self):
        for skill_md in PILOT_SKILL_MDS:
            with self.subTest(skill_md=str(skill_md)):
                self.assertTrue(skill_md.exists(), skill_md)
                text = skill_md.read_text(encoding="utf-8")
                self.assertNotIn("stage.design", text, skill_md)

                rel_path = skill_md.relative_to(REPO_ROOT).as_posix()
                main_show = subprocess.run(
                    ["git", "show", f"main:{rel_path}"],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(main_show.returncode, 0, main_show.stderr)
                main_text = main_show.stdout

                current_tokens = sorted(set(re.findall(r"stage\.[a-z_]+", text)))
                main_tokens = sorted(set(re.findall(r"stage\.[a-z_]+", main_text)))
                self.assertEqual(
                    current_tokens, main_tokens,
                    f"{skill_md} 단계->이벤트 표의 stage.* 토큰 목록이 main과 다름",
                )


if __name__ == "__main__":
    unittest.main()
