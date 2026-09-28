# @header
# module: ownership_tool.tests.test_task164_registry_layout
# layer: test
# domain: ownership
# description: RED-first(task_164) S-2 — ownership_tool.ownership_core.read_registry_meta가
#   새 구조(`<hub>/.opal-worktrees/.meta/task_{NNN}/meta.json`)만 읽고 구 구조 평면 파일은
#   무시·바이트 불변이어야 한다. 공개 함수(read_registry_meta)로만 검증한다(private 미사용).
# exports: (none — pytest module)
# depends: ownership_tool.ownership_core
"""RED 테스트 — task_164 S-2 (구현 전)."""
from __future__ import annotations

import json
import pathlib
import sys

TESTS_DIR = pathlib.Path(__file__).resolve().parent
TOOL_DIR = TESTS_DIR.parent
sys.path.insert(0, str(TOOL_DIR))

from ownership_tool import ownership_core  # noqa: E402


def _issued_meta(task: str, hub: pathlib.Path) -> dict:
    task_home = hub / ".opal-worktrees" / f"task_{task}"
    task_folder = f"task164-{task}"
    return {
        "allocator_root": str(hub),
        "task_home": str(task_home),
        "task_folder": task_folder,
        "task_path": str(task_home / "tasks" / task_folder),
        "artifact_repo": ".",
        "task_ownership_version": 2,
    }


class TestTask164OwnershipCoreReadsNewLayout:
    def test_read_registry_meta_finds_task_folder_json(self, tmp_path):
        task = "9041"
        hub = tmp_path / "hub"
        meta_dir = hub / ".opal-worktrees" / ".meta" / f"task_{task}"
        meta_dir.mkdir(parents=True)
        meta = _issued_meta(task, hub)
        (meta_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        result = ownership_core.read_registry_meta(str(hub), task)
        assert result.get("ok") is True, (
            f"Task164 S-2: 새 구조 메타를 읽지 못했다(구 구조 경로만 보는 중일 가능성) — {result}"
        )
        assert result.get("task_folder") == meta["task_folder"]

    def test_old_flat_file_is_ignored_and_untouched(self, tmp_path):
        """구 구조 `.meta/task_{NNN}.json`이 남아 있어도 소비자는 이를 읽지 않고,
        새 구조 조회 시도로 인해 구 파일 바이트가 바뀌지 않는다."""
        task = "9042"
        hub = tmp_path / "hub"
        old_flat = hub / ".opal-worktrees" / ".meta" / f"task_{task}.json"
        old_flat.parent.mkdir(parents=True, exist_ok=True)
        old_body = json.dumps({"task": task, "legacy": True}, ensure_ascii=False, indent=2)
        old_flat.write_text(old_body, encoding="utf-8")
        before = old_flat.read_bytes()

        result = ownership_core.read_registry_meta(str(hub), task)

        # 새 구조 폴더가 없으므로 조회는 실패(invalid_registry)여야 한다 — 구 구조로
        # 폴백해 성공하면 안 된다(D-3 "읽지도 옮기지도 않는다").
        assert result.get("ok") is False, (
            f"Task164 S-2: 구 구조 평면 파일로 폴백해 성공했다 — {result}"
        )
        assert old_flat.read_bytes() == before, (
            "Task164 S-2: 구 구조 파일 바이트가 조회 후 바뀌었다"
        )

    def test_registry_meta_entries_returns_empty_on_iterdir_permission_error(
        self, tmp_path, monkeypatch
    ):
        """`.meta/` 열람이 PermissionError(OSError)를 던져도 registry_meta_entries는
        예외로 새지 않고 빈 목록을 돌려준다(훅 3종이 기대하는 fail-safe)."""
        hub = tmp_path / "hub"
        meta_root = hub / ".opal-worktrees" / ".meta"
        meta_root.mkdir(parents=True)

        real_iterdir = pathlib.Path.iterdir

        def _raise_permission_error(self):
            if self == meta_root:
                raise PermissionError("denied")
            return real_iterdir(self)

        monkeypatch.setattr(pathlib.Path, "iterdir", _raise_permission_error)

        assert ownership_core.list_task_meta_dirs(str(hub)) == []
        assert ownership_core.registry_meta_entries(str(hub)) == []
