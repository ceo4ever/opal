"""
@header {
  "module": "task134_mode_persistence_contract",
  "layer": "test",
  "domain": "opal-harness",
  "description": "Task 134 nested Pilot and track mode inheritance RED contract",
  "exports": [],
  "depends": []
}
"""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
DEV = ROOT / "opal/skills/opal-pilot-dev/SKILL.md"
PROJECT_DEV = ROOT / "opal/skills/opal-pilot-project-dev/SKILL.md"
ROUTING = ROOT / "opal/skills/opal-pilot-dev/references/track-routing.md"
ESCALATION = ROOT / "opal/skills/opal-pilot-dev/references/track-escalation.md"
TARGETS = (DEV, PROJECT_DEV, ROUTING, ESCALATION)


class Task134ModePersistenceContractTest(unittest.TestCase):
    def _text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def test_s7_existing_task_reentry_resolves_before_mode_harness_load(self):
        text = self._text(DEV)
        resolve_at = text.find("resolve-mode")
        harness_at = text.find("서브 하네스")
        self.assertGreaterEqual(resolve_at, 0, "existing/new task mode resolver contract missing")
        self.assertGreater(harness_at, resolve_at,
                           "effective mode must be resolved before the mode harness is loaded")
        self.assertTrue("--new-task" in text, "new-task resolver branch missing")
        self.assertTrue(
            re.search(r"명시[^\n]*>[^\n]*state|explicit[^\n]*>[^\n]*state", text),
            "explicit > stored state precedence missing",
        )

    def test_s7_oppd_to_opwt_passes_parent_effective_mode(self):
        text = self._text(PROJECT_DEV)
        opwt_positions = [match.start() for match in re.finditer(r"opwt", text)]
        self.assertTrue(opwt_positions, "oppd must contain its opwt delegation")
        self.assertTrue("effective mode" in text, "oppd parent effective mode missing")
        self.assertTrue(
            re.search(r"opwt[^\n]*(--interactive|--semi-agentic|--agentic)", text),
            "opwt invocation does not carry an explicit effective-mode flag",
        )

    def test_s7_bidirectional_track_transitions_inherit_effective_mode(self):
        routing = self._text(ROUTING)
        escalation = self._text(ESCALATION)
        for label, text in (("opd->opds", routing), ("opds->opd", escalation)):
            with self.subTest(direction=label):
                self.assertTrue("effective mode" in text,
                                f"{label} effective mode inheritance missing")
                self.assertTrue(re.search(r"--interactive|--semi-agentic|--agentic", text),
                                f"{label} explicit mode flag missing")
                self.assertNotIn("--force init", text)

    def test_s7_user_sovereignty_gates_are_preserved(self):
        dev = self._text(DEV)
        project_dev = self._text(PROJECT_DEV)
        routing = self._text(ROUTING)
        escalation = self._text(ESCALATION)
        self.assertIn("CLOSE 진입", dev)
        self.assertIn("owner=user", dev)
        self.assertIn("PRD/TRD", project_dev)
        self.assertRegex(project_dev, r"사용자[^\n]*(소유|확인|승인)")
        self.assertRegex(routing, r"사용자[^\n]*(수락|승인|확인)")
        self.assertRegex(escalation, r"사용자[^\n]*(수락|승인|확인)")

    def test_s7_mode_contract_remains_platform_neutral(self):
        branch = re.compile(r"\b(?:if|when)\b[^\n]*(?:Claude|Cursor|Gemini|Antigravity)", re.I)
        hits = []
        for path in TARGETS:
            for number, line in enumerate(self._text(path).splitlines(), 1):
                if branch.search(line):
                    hits.append(f"{path.relative_to(ROOT)}:{number}:{line}")
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
