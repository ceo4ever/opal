"""
@header {
  "module": "test_event_loader_agent_sections",
  "layer": "test",
  "domain": "opal-tools",
  "description": "agent_sections 절 파서·에이전트 항목 선별의 코드 펜스 경계와 실제 agents.md 선별 계약 (S-3, S-2 선별 부분)",
  "exports": [],
  "depends": ["agent_sections"]
}
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import unittest


REPO_ROOT = Path(__file__).resolve().parents[4]
MODULE_PATH = REPO_ROOT / "opal" / "tools" / "event-loader" / "agent_sections.py"
MANIFEST = REPO_ROOT / "opal" / "core" / "references" / "events.json"
AGENTS_MD = REPO_ROOT / "opal" / "core" / "references" / "agents.md"
AGENT_HEADING = re.compile(r"^### (\S+)", re.MULTILINE)


def _load_module():
    # 모듈 부재를 import 시점이 아니라 케이스 단위 실패로 만들기 위해 지연 import한다.
    if not MODULE_PATH.exists():
        raise ModuleNotFoundError(f"agent_sections.py 미구현: {MODULE_PATH}")
    spec = importlib.util.spec_from_file_location("agent_sections", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _selection() -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    event = next(item for item in manifest["events"] if item["id"] == "worker.dispatch")
    selection = event.get("selection")
    if not isinstance(selection, dict):
        raise AssertionError("events.json worker.dispatch.selection 선언이 없습니다 (D-6)")
    return selection


def _field(section, name):
    if isinstance(section, dict):
        return section[name]
    return getattr(section, name)


def _titles(sections) -> list[str]:
    return [str(_field(section, "title")).strip() for section in sections]


def _content(result) -> str:
    return result["content"] if isinstance(result, dict) else result.content


SYNTHETIC = """# 문서

머리말

## 프로젝트 전문

### opal-be-agent

BE 본문

### opal-fe-agent

FE 본문

## 에이전트 추가 가이드

### 프레임워크 에이전트 추가

가이드 본문

## 프로젝트 예시

```markdown
## 프레임워크 에이전트 로드
### 확정 기준
### opal-be-agent
- BaseRepository
```

뒷 본문

## 향후 추가 에이전트

~~~markdown
### {agent-name}
~~~
"""


class ParseSectionsFenceTest(unittest.TestCase):
    def setUp(self):
        self.mod = _load_module()

    def test_backtick_fence_headings_are_not_sections(self):
        sections = self.mod.parse_sections(SYNTHETIC)
        titles = _titles(sections)
        self.assertIn("프로젝트 예시", titles)
        for leaked in ("프레임워크 에이전트 로드", "확정 기준"):
            self.assertNotIn(leaked, titles)
        holder = next(s for s in sections if _titles([s])[0] == "프로젝트 예시")
        self.assertIn("## 프레임워크 에이전트 로드", _field(holder, "body"))
        self.assertIn("### 확정 기준", _field(holder, "body"))

    def test_tilde_fence_headings_are_body(self):
        titles = _titles(self.mod.parse_sections(SYNTHETIC))
        self.assertNotIn("{agent-name}", titles)
        self.assertEqual(titles.count("opal-be-agent"), 1)

    def test_four_backtick_fence_contains_inner_triple_backtick(self):
        text = "## A\n\n````md\n```\n## 안쪽\n```\n### 또 안쪽\n````\n\n## B\n"
        titles = _titles(self.mod.parse_sections(text))
        self.assertEqual(titles, ["A", "B"])

    def test_unclosed_fence_runs_to_end_of_document(self):
        text = "## A\n\n```md\n## 안 닫힘\n### 계속\n본문 끝\n"
        sections = self.mod.parse_sections(text)
        self.assertEqual(_titles(sections), ["A"])
        self.assertIn("## 안 닫힘", _field(sections[0], "body"))
        self.assertIn("본문 끝", _field(sections[0], "body"))

    def test_shorter_closing_fence_does_not_close(self):
        text = "## A\n\n````md\n```\n## 안쪽 헤딩\n````\n## B\n"
        self.assertEqual(_titles(self.mod.parse_sections(text)), ["A", "B"])


class SelectAgentEntriesTest(unittest.TestCase):
    def setUp(self):
        self.mod = _load_module()
        self.selection = _selection()

    def test_general_target_keeps_only_target_entry(self):
        out = _content(self.mod.select_agent_entries(SYNTHETIC, self.selection, "opal-be-agent"))
        self.assertIn("BE 본문", out)
        self.assertNotIn("FE 본문", out)
        self.assertNotIn("### opal-fe-agent", out)

    def test_excluded_sections_removed_with_children(self):
        out = _content(self.mod.select_agent_entries(SYNTHETIC, self.selection, "opal-be-agent"))
        for removed in ("에이전트 추가 가이드", "프레임워크 에이전트 추가", "가이드 본문", "향후 추가 에이전트", "{agent-name}"):
            self.assertNotIn(removed, out)

    def test_fenced_example_stays_inside_its_own_section(self):
        out = _content(self.mod.select_agent_entries(SYNTHETIC, self.selection, "opal-fe-agent"))
        self.assertIn("## 프로젝트 예시", out)
        self.assertIn("뒷 본문", out)
        self.assertIn("```markdown\n## 프레임워크 에이전트 로드", out)
        self.assertNotIn("BE 본문", out)

    def test_full_entry_agent_keeps_every_entry(self):
        out = _content(self.mod.select_agent_entries(SYNTHETIC, self.selection, "opal-plan-agent"))
        self.assertIn("BE 본문", out)
        self.assertIn("FE 본문", out)
        self.assertNotIn("가이드 본문", out)

    def test_target_absent_yields_zero_entries_without_error(self):
        result = self.mod.select_agent_entries(SYNTHETIC, self.selection, "opal-project-only-agent")
        out = _content(result)
        self.assertNotIn("BE 본문", out)
        self.assertNotIn("FE 본문", out)
        self.assertIn("absent", json.dumps(result, ensure_ascii=False, default=str))


class RealAgentsMdSelectionTest(unittest.TestCase):
    def setUp(self):
        self.mod = _load_module()
        self.selection = _selection()
        self.full = AGENTS_MD.read_text(encoding="utf-8")

    def test_real_agents_md_example_blocks_do_not_leak(self):
        for agent in ("opal-be-agent", "opal-test-agent", "opal-security-checker"):
            with self.subTest(agent=agent):
                out = _content(self.mod.select_agent_entries(self.full, self.selection, agent))
                self.assertLess(len(out.encode("utf-8")), len(self.full.encode("utf-8")))
                self.assertNotIn("BaseRepository", out)
                self.assertNotIn("## 프레임워크 에이전트 로드", out)
                self.assertNotIn("### 확정 기준", out)
                self.assertNotIn("### {agent-name}", out)
                self.assertNotIn("## 에이전트 추가 가이드", out)
                self.assertNotIn("## 향후 추가 에이전트", out)
                self.assertEqual(len(re.findall(rf"^### {re.escape(agent)}\b", out, re.MULTILINE)), 1)

    def test_real_agents_md_parse_does_not_surface_fenced_headings(self):
        titles = _titles(self.mod.parse_sections(self.full))
        for leaked in ("프레임워크 에이전트 로드", "확정 기준", "{agent-name}"):
            self.assertNotIn(leaked, titles)
        self.assertIn("에이전트 추가 가이드", titles)
        self.assertIn("향후 추가 에이전트", titles)

    def test_real_agents_md_full_entry_agent_keeps_all_entries(self):
        out = _content(self.mod.select_agent_entries(self.full, self.selection, "opal-plan-agent"))
        kept = set(re.findall(r"^### (opal-[a-z0-9-]+-(?:agent|checker))", out, re.MULTILINE))
        expected = {
            name for name in re.findall(r"^### (opal-[a-z0-9-]+-(?:agent|checker))", self.full, re.MULTILINE)
        }
        self.assertEqual(kept, expected)
        self.assertNotIn("BaseRepository", out)


if __name__ == "__main__":
    unittest.main()
