"""
@header {
  "module": "task136_mode_transition_contract",
  "layer": "test",
  "domain": "opal-harness",
  "description": "Task 136 cross-Pilot transition prose and pipeline fixture contract",
  "exports": [],
  "depends": []
}
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
VOCABULARY = {"continue", "await_user", "blocked", "complete"}
COMMON_CONTRACTS = (
    ROOT / "opal/core/references/harness/modes.md",
    ROOT / "opal/core/references/harness/state.md",
    ROOT / "opal/core/references/harness/task-process.md",
    ROOT / "opal/core/references/opal-harness-interactive.md",
    ROOT / "opal/core/references/opal-harness-semi-agentic.md",
    ROOT / "opal/core/references/opal-harness-agentic.md",
)
PILOT_SKILLS = (
    ROOT / "opal/skills/opal-pilot-dev/SKILL.md",
    ROOT / "opal/skills/opal-pilot-dev-short/SKILL.md",
    ROOT / "opal/skills/opal-pilot-dev-wireframe/SKILL.md",
    ROOT / "opal/skills/opal-pilot-project/SKILL.md",
    ROOT / "opal/skills/opal-pilot-write-tech/SKILL.md",
    ROOT / "opal/skills/opal-pilot-data-design/SKILL.md",
    ROOT / "opal/skills/opal-pilot-gc/SKILL.md",
    ROOT / "opal/skills/opal-pilot-sdd/SKILL.md",
    ROOT / "opal/skills/opal-pilot-project-dev/SKILL.md",
    ROOT / "opal/skills/opal-pilot-project-loop/SKILL.md",
)
PIPELINES = (
    ROOT / "opal/skills/opal-pilot-data-design/references/pipeline.json",
    ROOT / "opal/skills/opal-pilot-dev-wireframe/references/pipeline.json",
    ROOT / "opal/skills/opal-pilot-dev/references/pipeline-short.json",
    ROOT / "opal/skills/opal-pilot-dev/references/pipeline.json",
    ROOT / "opal/skills/opal-pilot-gc/references/pipeline.json",
    ROOT / "opal/skills/opal-pilot-project-dev/references/pipeline.json",
    ROOT / "opal/skills/opal-pilot-project-loop/references/pipeline.json",
    ROOT / "opal/skills/opal-pilot-project/references/pipeline.json",
    ROOT / "opal/skills/opal-pilot-sdd/references/pipeline.json",
    ROOT / "opal/skills/opal-pilot-write-tech/references/pipeline.json",
)
CLOSE_KEYS = (
    "close.done_md",
    "close.docs_sync",
    "close.brain_ingest",
    "close.retrospective",
    "close.worktree_finalize",
    "close.final",
)


class Task136TransitionDocumentationContractTest(unittest.TestCase):
    def _text(self, path: Path) -> str:
        self.assertTrue(path.is_file(), f"missing contract source: {path}")
        return path.read_text(encoding="utf-8")

    def test_s2_common_and_pilot_prose_use_structured_reports(self):
        missing: list[str] = []
        for path in (*COMMON_CONTRACTS, *PILOT_SKILLS):
            text = self._text(path)
            for token in ("transition_action", "progress_report", "decision_request"):
                if token not in text:
                    missing.append(f"{path.relative_to(ROOT)}: missing {token}")
        self.assertEqual(missing, [])

        task_process = self._text(ROOT / "opal/core/references/harness/task-process.md")
        self.assertNotIn("사용자에게 보고하고 다음 단계 승인을 받는다", task_process)
        self.assertIsNone(
            re.search(r"다음 단계\([^\n]+\)로 넘어갈까요\?", task_process),
            "TASK completion report must consume transition_action, not always ask approval",
        )

    def test_s2_track_change_is_nonblocking_while_selected_track_is_viable(self):
        for relative in (
            "opal/skills/opal-pilot-dev/references/track-routing.md",
            "opal/skills/opal-pilot-dev/references/track-escalation.md",
        ):
            path = ROOT / relative
            text = self._text(path)
            self.assertIn("progress_report", text, path)
            self.assertIn("현재 트랙", text, path)
            self.assertRegex(text, r"실행 불가|불가능", path)
            self.assertNotRegex(
                text,
                r"사용자(?:가|의)?\s*(?:수락|승인|확인)[^\n]*(?:후|해야|필수)",
                f"track suggestion still blocks: {path}",
            )


class Task136PipelineConformanceTest(unittest.TestCase):
    def test_s5_all_pilots_publish_one_transition_contract_and_close_final(self):
        self.assertEqual(len(PIPELINES), 10)
        failures: list[str] = []
        for path in PIPELINES:
            data = json.loads(path.read_text(encoding="utf-8"))
            steps = data.get("task_steps", [])
            keys = [row.get("key") for row in steps]
            contract = data.get("transition_contract")
            label = str(path.relative_to(ROOT))

            if not isinstance(contract, dict):
                failures.append(f"{label}: transition_contract missing")
                continue
            if set(contract.get("vocabulary", [])) != VOCABULARY:
                failures.append(f"{label}: transition vocabulary mismatch")
            boundary = contract.get("semi_agentic_boundary")
            if not isinstance(boundary, str) or boundary not in keys:
                failures.append(f"{label}: invalid semi_agentic_boundary={boundary!r}")
            if contract.get("close_final_key") != "close.final":
                failures.append(f"{label}: close_final_key must be close.final")

            close_steps = [row for row in steps if row.get("stage") == "CLOSE"]
            close_keys = tuple(row.get("key") for row in close_steps)
            if close_keys != CLOSE_KEYS:
                failures.append(f"{label}: CLOSE tail {close_keys!r}")
            if not steps or steps[-1].get("key") != "close.final":
                failures.append(f"{label}: close.final is not the pipeline final row")
            ids = [row.get("id") for row in steps]
            if ids != list(range(1, len(steps) + 1)):
                failures.append(f"{label}: row ids are not contiguous")

        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
