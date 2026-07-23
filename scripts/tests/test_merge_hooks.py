#!/usr/bin/env python3
"""
@header {
  "module": "test_merge_hooks",
  "layer": "test",
  "domain": "opal-install",
  "description": "merge-hooks.py 멱등 upsert 단위 테스트 — 외부(orca) 보존·OPAL 스탬프 upsert·2회 멱등·유효 JSON/마커 위치 (TS-020~023)",
  "exports": ["TestMergeHooks"],
  "depends": ["merge-hooks"]
}
"""
import copy
import importlib.util
import json
import os
import sys
import tempfile
import unittest

# merge-hooks.py는 하이픈 파일명 → importlib로 파일 경로 로드
_MODULE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "merge-hooks.py")
_spec = importlib.util.spec_from_file_location("merge_hooks_mod", _MODULE_PATH)
merge_hooks_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(merge_hooks_mod)

merge_hooks = merge_hooks_mod.merge_hooks
MARKER = merge_hooks_mod.MARKER

# OPAL 소스 hooks (claude-hooks.json + PostToolUse 추가 형태)
SOURCE_HOOKS = {
    "SubagentStop": [
        {"matcher": "", "hooks": [{"type": "command", "command": "osascript -e 'subagent'"}]}
    ],
    "Stop": [
        {"matcher": "", "hooks": [{"type": "command", "command": "osascript -e 'stop'"}]}
    ],
    "PostToolUse": [
        {"matcher": "Bash", "hooks": [{"type": "command", "command": "python todo_mirror_hook.py"}]}
    ],
}

# 사용자의 기존 settings — orca PostToolUse hook 보유(외부, 마커 無)
ORCA_SETTINGS = {
    "hooks": {
        "PostToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": "orca-external-hook"}]}
        ]
    }
}


class TestMergeHooks(unittest.TestCase):
    def _iter_matcher_blocks(self, settings):
        for _event, rules in settings.get("hooks", {}).items():
            for block in rules:
                yield block

    def test_ts020_external_orca_preserved(self):
        """TS-020: 기존 orca PostToolUse가 merge 후에도 보존된다."""
        merged = merge_hooks(copy.deepcopy(ORCA_SETTINGS), copy.deepcopy(SOURCE_HOOKS))
        commands = [
            h["command"]
            for block in merged["hooks"]["PostToolUse"]
            for h in block["hooks"]
        ]
        self.assertIn("orca-external-hook", commands)
        # orca 블록은 마커가 없어야 한다(외부 소유)
        orca_blocks = [
            b for b in merged["hooks"]["PostToolUse"]
            if any(h["command"] == "orca-external-hook" for h in b["hooks"])
        ]
        self.assertEqual(len(orca_blocks), 1)
        self.assertNotIn(MARKER, orca_blocks[0])

    def test_ts021_opal_upsert_stamped(self):
        """TS-021: OPAL PostToolUse/SubagentStop/Stop 항목이 _opal_managed:true로 삽입된다."""
        merged = merge_hooks(copy.deepcopy(ORCA_SETTINGS), copy.deepcopy(SOURCE_HOOKS))
        for event in ("SubagentStop", "Stop", "PostToolUse"):
            self.assertIn(event, merged["hooks"])
        opal_blocks = [b for b in self._iter_matcher_blocks(merged) if b.get(MARKER) is True]
        opal_commands = [h["command"] for b in opal_blocks for h in b["hooks"]]
        self.assertIn("python todo_mirror_hook.py", opal_commands)
        self.assertIn("osascript -e 'subagent'", opal_commands)
        self.assertIn("osascript -e 'stop'", opal_commands)
        # PostToolUse에는 orca(외부) + OPAL 2블록 공존
        self.assertEqual(len(merged["hooks"]["PostToolUse"]), 2)

    def test_ts022_idempotent_byte_identical(self):
        """TS-022: main() 2회 연속 실행 → 결과 파일 바이트 동일(OPAL·orca 중복 0)."""
        with tempfile.TemporaryDirectory() as d:
            target = os.path.join(d, "settings.json")
            source = os.path.join(d, "hooks.json")
            with open(target, "w", encoding="utf-8") as f:
                json.dump(ORCA_SETTINGS, f)
            with open(source, "w", encoding="utf-8") as f:
                json.dump(SOURCE_HOOKS, f)

            saved_argv = sys.argv
            try:
                sys.argv = ["merge-hooks.py", target, source]
                merge_hooks_mod.main()
                with open(target, "rb") as f:
                    first = f.read()
                merge_hooks_mod.main()
                with open(target, "rb") as f:
                    second = f.read()
            finally:
                sys.argv = saved_argv

            self.assertEqual(first, second)
            # OPAL PostToolUse 항목이 중복 누적되지 않았는지(orca 1 + OPAL 1 = 2)
            data = json.loads(second)
            self.assertEqual(len(data["hooks"]["PostToolUse"]), 2)

    def test_ts023_valid_json_marker_only_on_matcher_blocks(self):
        """TS-023: 산출 settings가 유효 JSON이며 마커 키가 매처 블록에만 존재한다."""
        merged = merge_hooks(copy.deepcopy(ORCA_SETTINGS), copy.deepcopy(SOURCE_HOOKS))
        # 직렬화·역직렬화 가능(유효 JSON)
        reparsed = json.loads(json.dumps(merged, ensure_ascii=False))
        self.assertEqual(reparsed, merged)
        # 마커는 매처 블록 dict의 형제 키에만 — 내부 hooks 엔트리에는 없어야 한다
        for block in self._iter_matcher_blocks(merged):
            for hook_entry in block["hooks"]:
                self.assertNotIn(MARKER, hook_entry)

    def test_missing_target_creates_from_empty(self):
        """target 없음 → 빈 {}에서 OPAL upsert(회귀 안전, 신규 머신)."""
        merged = merge_hooks({}, copy.deepcopy(SOURCE_HOOKS))
        self.assertIn("PostToolUse", merged["hooks"])
        self.assertEqual(len(merged["hooks"]["PostToolUse"]), 1)


if __name__ == "__main__":
    unittest.main()
