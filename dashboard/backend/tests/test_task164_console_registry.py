# @header
# module: tests.test_task164_console_registry
# layer: test
# domain: console
# description: RED-first(task_164) S-2 — Console `_active_worktree_task_roots`가
#   새 구조(`.opal-worktrees/.meta/task_{NNN}/meta.json`)만 이름순으로 읽고,
#   구 구조 평면 파일(`.meta/task_{NNN}.json`)은 무시·바이트 불변이어야 한다(D-3).
# exports:
#   - TestTask164ConsoleActiveWorktreeTaskRoots
# depends: dashboard.backend.routers.tasks
"""RED 테스트 — task_164 S-2 (Console 부분, W-3)."""
from __future__ import annotations

import json
import os

from dashboard.backend.routers.tasks import _active_worktree_task_roots


def _write_meta(meta_dir: str, task_path: str) -> None:
    os.makedirs(meta_dir, exist_ok=True)
    meta = {
        "allocator_root": os.path.dirname(os.path.dirname(meta_dir)),
        "task_home": os.path.dirname(task_path),
        "task_folder": os.path.basename(task_path),
        "task_path": task_path,
        "artifact_repo": ".",
        "task_ownership_version": 2,
    }
    with open(os.path.join(meta_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


class TestTask164ConsoleActiveWorktreeTaskRoots:
    def test_reads_new_structure_only_ignores_old_flat_file(self, tmp_path):
        """새 구조 2건(task_101, task_102) + 구 구조 평면 파일 task_900.json 1건.

        결과는 새 구조 2건의 tasks root만 담아야 하고, task_900.json은 읽지도
        않고 바이트도 바뀌지 않아야 한다(D-3)."""
        hub = tmp_path / "hub"
        registry_dir = hub / ".opal-worktrees" / ".meta"

        home_101 = hub / ".opal-worktrees" / "task_101"
        task_path_101 = home_101 / "tasks" / "task164-101"
        os.makedirs(task_path_101, exist_ok=True)
        _write_meta(str(registry_dir / "task_101"), str(task_path_101))

        home_102 = hub / ".opal-worktrees" / "task_102"
        task_path_102 = home_102 / "tasks" / "task164-102"
        os.makedirs(task_path_102, exist_ok=True)
        _write_meta(str(registry_dir / "task_102"), str(task_path_102))

        old_flat = registry_dir / "task_900.json"
        os.makedirs(registry_dir, exist_ok=True)
        old_body = json.dumps({"task": "900", "legacy": True}, ensure_ascii=False, indent=2)
        old_flat.write_text(old_body, encoding="utf-8")
        before = old_flat.read_bytes()

        roots = _active_worktree_task_roots(str(hub))

        expected = {
            os.path.realpath(str(task_path_101.parent)),
            os.path.realpath(str(task_path_102.parent)),
        }
        assert set(roots) == expected, (
            f"Task164 S-2(Console): 새 구조 2건만 반영해야 한다 — {roots}"
        )
        assert old_flat.read_bytes() == before, (
            "Task164 S-2(Console): 구 구조 평면 파일 바이트가 조회 후 바뀌었다"
        )

    def test_missing_registry_dir_returns_empty(self, tmp_path):
        assert _active_worktree_task_roots(str(tmp_path / "no-hub")) == []

    def test_slot_without_meta_json_is_skipped(self, tmp_path):
        """폴더는 있으나 `meta.json`이 없는 슬롯은 무시한다."""
        hub = tmp_path / "hub"
        empty_slot = hub / ".opal-worktrees" / ".meta" / "task_999"
        os.makedirs(empty_slot, exist_ok=True)

        assert _active_worktree_task_roots(str(hub)) == []
