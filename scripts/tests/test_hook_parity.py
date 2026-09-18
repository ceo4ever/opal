#!/usr/bin/env python3
"""
@header {
  "module": "test_hook_parity",
  "layer": "test",
  "domain": "opal-install",
  "description": "소스 claude-hooks.json ↔ 설치 결과 settings.json parity 계약 테스트(W-10) — 이벤트 집합 일치·비OPAL(orca) hook 보존·N회 재배포 바이트 동일·project/worktree settings에 OPAL 항목 0건. 전 케이스를 임시 HOME 샌드박스에서 merge-hooks.py 서브프로세스로 실행하며 실제 ~/.claude/settings.json은 읽지도 쓰지도 않는다.",
  "exports": ["TestHookParity"],
  "depends": ["merge-hooks"]
}
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REPO_ROOT = os.path.dirname(_SCRIPTS_DIR)
MERGE_HOOKS = os.path.join(_SCRIPTS_DIR, "merge-hooks.py")
INSTALL_SH = os.path.join(_SCRIPTS_DIR, "install-mac.sh")
HOOKS_SRC = os.path.join(_REPO_ROOT, "opal", "core", "hooks", "claude-hooks.json")
RETIRED_SRC = os.path.join(_REPO_ROOT, "opal", "core", "hooks", "claude-hooks.retired.json")

MARKER = "_opal_managed"
ORCA_CMD = "orca-external-hook"

# 소스에 있어도 hook 항목이 아닌 메타 키는 이벤트로 세지 않는다.
_META_KEYS = {"_help"}

# W-19 — ownership-tool이 배포하는 hook 이벤트 5종과 담당 모듈(SSOT: claude-hooks.json).
OWNERSHIP_HOOKS = {
    "SessionStart": "session_start_hook.py",
    "PreToolUse": "pretooluse_guard_hook.py",
    "PostToolUse": "heartbeat_hook.py",
    "Stop": "stop_hook.py",
    "SessionEnd": "session_end_hook.py",
}


def _events(hooks_map):
    return {k for k, v in hooks_map.items() if k not in _META_KEYS and isinstance(v, list) and v}


class TestHookParity(unittest.TestCase):
    """install 결과 parity — 실제 HOME을 건드리지 않는 샌드박스 전용."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="opal-hook-parity-")
        self.addCleanup(shutil.rmtree, self._tmp, True)
        # 샌드박스 HOME: 실제 ~/.claude 와 완전히 분리된 경로
        self.home = os.path.join(self._tmp, "home")
        self.claude_dir = os.path.join(self.home, ".claude")
        os.makedirs(self.claude_dir)
        self.settings = os.path.join(self.claude_dir, "settings.json")
        with open(HOOKS_SRC, encoding="utf-8") as f:
            self.source_hooks = json.load(f)

    def _run_merge(self, target=None):
        """merge-hooks.py를 샌드박스 HOME 환경으로 1회 실행(= install의 merge_hooks_config seam)."""
        target = target or self.settings
        env = dict(os.environ, HOME=self.home)
        subprocess.run(
            [sys.executable, MERGE_HOOKS, target, HOOKS_SRC, RETIRED_SRC],
            check=True, env=env, cwd=self._tmp,
        )
        return target

    def _write(self, path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return path

    def _load(self, path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _opal_blocks(self, settings):
        return {
            event: [b for b in rules if b.get(MARKER) is True]
            for event, rules in settings.get("hooks", {}).items()
        }

    def _strip_markers(self, path):
        """Claude Code가 settings 저장 시 스키마 밖 키를 버리는 상황 재현."""
        data = self._load(path)
        for rules in data.get("hooks", {}).values():
            for block in rules:
                block.pop(MARKER, None)
        self._write(path, data)

    # ── 1. 이벤트 집합 parity ──────────────────────────────────────────────
    def test_installed_event_set_matches_source(self):
        """소스 claude-hooks.json의 이벤트 집합 == 설치 결과의 _opal_managed 이벤트 집합."""
        self._run_merge()
        installed = self._load(self.settings)
        owned = {e for e, blocks in self._opal_blocks(installed).items() if blocks}
        self.assertEqual(owned, _events(self.source_hooks))
        # 매처 블록 수까지 이벤트별로 일치해야 한다(누락·중복 0).
        for event, rules in self.source_hooks.items():
            self.assertEqual(len(self._opal_blocks(installed)[event]), len(rules), event)

    def test_source_declares_ownership_hook_events(self):
        """W-19 — ownership hook 5종 전건이 기존 항목을 대체하지 않고 소스에 배선돼 있다."""
        cmds = {
            e: [h["command"] for b in rules for h in b["hooks"]]
            for e, rules in self.source_hooks.items()
        }
        # 배포 이벤트 5종 확정 — 이벤트별로 담당 hook 모듈이 정확히 1건씩 배선된다.
        for event, module in OWNERSHIP_HOOKS.items():
            self.assertIn(event, self.source_hooks, event)
            self.assertEqual(
                sum(1 for c in cmds[event] if module in c), 1, "{}:{}".format(event, module)
            )
        # heartbeat는 matcher 없이 모든 PostToolUse에서 발화한다.
        hb = [b for b in self.source_hooks["PostToolUse"]
              if any("heartbeat_hook.py" in h["command"] for h in b["hooks"])]
        self.assertEqual([b["matcher"] for b in hb], [""])
        # PreToolUse guard는 D-6 폐쇄 목록이 닿는 도구에만 발화한다(전면 매칭 금지 — latency 방어).
        guard = [b for b in self.source_hooks["PreToolUse"]
                 if any("pretooluse_guard_hook.py" in h["command"] for h in b["hooks"])]
        self.assertEqual([b["matcher"] for b in guard], ["Edit|Write|NotebookEdit|Bash"])
        # 기존 todo_mirror / code-map 항목은 병존한다(제거·대체 금지).
        self.assertTrue(any("todo_mirror_hook.py" in c for c in cmds["PostToolUse"]))
        self.assertTrue(any("code-map-hook.js" in c for c in cmds["PostToolUse"]))

    def test_installed_ownership_hooks_are_opal_owned_on_all_five_events(self):
        """설치 결과에서도 5종 전건이 _opal_managed 소유로 정확히 1건씩 남는다."""
        self._run_merge()
        installed = self._load(self.settings)
        blocks = self._opal_blocks(installed)
        for event, module in OWNERSHIP_HOOKS.items():
            owned_cmds = [h["command"] for b in blocks.get(event, []) for h in b["hooks"]]
            self.assertEqual(
                sum(1 for c in owned_cmds if module in c), 1, "{}:{}".format(event, module)
            )

    def test_five_ownership_hook_modules_exist(self):
        """배선된 5종 hook 모듈 파일이 실재한다 — 죽은 command 배포 0건."""
        for event, module in OWNERSHIP_HOOKS.items():
            path = os.path.join(
                _REPO_ROOT, "opal", "tools", "ownership-tool", "ownership_tool", module
            )
            self.assertTrue(os.path.isfile(path), "{}:{}".format(event, path))

    # ── 2. 비OPAL hook 보존 ───────────────────────────────────────────────
    def test_non_opal_hooks_preserved(self):
        """외부 hook(orca)은 OPAL이 배선한 모든 이벤트에서 보존된다."""
        external = {
            event: [{"matcher": "", "hooks": [{"type": "command", "command": ORCA_CMD}]}]
            for event in _events(self.source_hooks)
        }
        self._write(self.settings, {"hooks": external, "model": "opus"})
        self._run_merge()
        installed = self._load(self.settings)
        for event in _events(self.source_hooks):
            cmds = [h["command"] for b in installed["hooks"][event] for h in b["hooks"]]
            self.assertEqual(cmds.count(ORCA_CMD), 1, event)
            orca = [b for b in installed["hooks"][event]
                    if any(h["command"] == ORCA_CMD for h in b["hooks"])]
            self.assertNotIn(MARKER, orca[0], event)  # 외부 소유를 가로채지 않는다
        self.assertEqual(installed["model"], "opus")  # hooks 밖 사용자 설정 보존

    # ── 3. N회 재배포 바이트 동일 ─────────────────────────────────────────
    def test_n_redeploys_byte_identical(self):
        """orca 동거 상태에서 재배포를 N회 반복해도 결과 바이트가 동일하다."""
        self._write(self.settings, {"hooks": {"PostToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": ORCA_CMD}]}
        ]}})
        self._run_merge()
        with open(self.settings, "rb") as f:
            first = f.read()
        for _ in range(3):
            self._run_merge()
            with open(self.settings, "rb") as f:
                self.assertEqual(f.read(), first)

    def test_n_redeploys_byte_identical_after_marker_loss(self):
        """마커가 지워진 뒤 재배포해도 바이트 동일 — OPAL 항목이 누적되지 않는다."""
        self._run_merge()
        with open(self.settings, "rb") as f:
            first = f.read()
        for _ in range(3):
            self._strip_markers(self.settings)
            self._run_merge()
            with open(self.settings, "rb") as f:
                self.assertEqual(f.read(), first)

    def test_retired_commands_are_reclaimed_not_reinserted(self):
        """retired 목록의 command는 회수되고 재삽입되지 않는다."""
        with open(RETIRED_SRC, encoding="utf-8") as f:
            retired = json.load(f)
        legacy = retired["Stop"]
        self.assertTrue(legacy)
        self._write(self.settings, {"hooks": {"Stop": [
            {"matcher": "", "hooks": [{"type": "command", "command": c}]} for c in legacy
        ] + [{"matcher": "", "hooks": [{"type": "command", "command": ORCA_CMD}]}]}})
        self._run_merge()
        cmds = [h["command"] for b in self._load(self.settings)["hooks"]["Stop"] for h in b["hooks"]]
        for c in legacy:
            self.assertNotIn(c, cmds)
        self.assertIn(ORCA_CMD, cmds)
        self.assertTrue(any("stop_hook.py" in c for c in cmds))

    # ── 4. project/worktree settings 오염 0건 ─────────────────────────────
    def test_project_and_worktree_settings_untouched(self):
        """install은 사용자 HOME settings만 쓴다 — project/worktree settings는 OPAL 항목 0건."""
        project = os.path.join(self._tmp, "proj")
        scopes = [
            os.path.join(project, ".claude", "settings.json"),
            os.path.join(project, ".claude", "settings.local.json"),
            os.path.join(project, ".opal-worktrees", "task_x", ".claude", "settings.json"),
        ]
        payload = {"hooks": {"PostToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": ORCA_CMD}]}
        ]}}
        before = {}
        for path in scopes:
            self._write(path, payload)
            with open(path, "rb") as f:
                before[path] = f.read()

        self._run_merge()  # HOME settings만 대상

        for path in scopes:
            with open(path, "rb") as f:
                self.assertEqual(f.read(), before[path], path)
            data = self._load(path)
            opal = [b for rules in data.get("hooks", {}).values()
                    for b in rules if b.get(MARKER)]
            self.assertEqual(opal, [], path)

    def test_installer_targets_home_settings_only(self):
        """install-mac.sh 배선 parity — 소스/퇴역 경로와 HOME settings 대상이 유지된다."""
        with open(INSTALL_SH, encoding="utf-8") as f:
            script = f.read()
        self.assertIn('opal/core/hooks/claude-hooks.json', script)
        self.assertIn('retired_json="${hooks_json%.json}.retired.json"', script)
        self.assertIn('merge_hooks_config "$settings" "$hooks_src"', script)
        self.assertIn('local settings="$USER_HOME/.claude/settings.json"', script)
        # retired 경로 파생이 실제 파일과 맞는지 확인
        self.assertEqual(HOOKS_SRC[: -len(".json")] + ".retired.json", RETIRED_SRC)
        self.assertTrue(os.path.isfile(RETIRED_SRC))


if __name__ == "__main__":
    unittest.main()
