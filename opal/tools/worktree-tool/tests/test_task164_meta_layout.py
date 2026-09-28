# @header
# module: worktree_tool.tests.test_task164_meta_layout
# layer: test
# domain: worktree-tool
# description: RED-first(task_164) — registry 메타의 태스크별 폴더 분리 계약(S-1, S-3)을
#   공개 CLI(create/ownership-set/remove)로만 검증한다. 구현 전 현재 코드는 `.meta/task_{NNN}.json`
#   평면 파일 구조라서 이 테스트는 실제로 실패해야 한다(assertion 실패, import/문법 오류 아님).
# exports: (none — pytest module)
# depends: opal/tools/worktree-tool/worktree_tool.py, tests/conftest.py(project_b, run_worktree_cli)
"""RED 테스트 — task_164 S-1, S-3 (구현 전)."""
from __future__ import annotations

import json
import os
import pathlib

from conftest import ProjectB, parse_json_stdout, run_worktree_cli


def _create(project_b: ProjectB, task: str, folder: str) -> dict:
    result = run_worktree_cli(
        [
            "create",
            "--project-root",
            str(project_b.root),
            "--task",
            task,
            "--task-folder",
            folder,
        ]
    )
    payload = parse_json_stdout(result, f"create({task})")
    assert payload.get("ok") is True, f"Task164 setup 실패: {payload}"
    return payload


def _meta_dir(project_b: ProjectB, task: str) -> pathlib.Path:
    return project_b.root / ".opal-worktrees" / ".meta" / f"task_{task}"


class TestTask164MetaFolderLayout:
    """S-1 (AC-1, C-3) — 메타·lock·임시 파일이 태스크 전용 폴더 안에만 있어야 한다."""

    def test_meta_lives_under_task_folder_not_flat_file(self, project_b: ProjectB):
        task = "9011"
        _create(project_b, task, "task164-9011")

        meta_dir = _meta_dir(project_b, task)
        new_meta_path = meta_dir / "meta.json"
        old_flat_path = project_b.root / ".opal-worktrees" / ".meta" / f"task_{task}.json"

        assert new_meta_path.is_file(), (
            f"Task164 S-1: 새 구조 메타 파일이 없다 — {new_meta_path} "
            f"(구 구조 잔존: {old_flat_path.exists()})"
        )
        assert not old_flat_path.exists(), (
            f"Task164 S-1: 구 구조 평면 파일이 그대로 만들어졌다 — {old_flat_path}"
        )

    def test_ownership_set_writes_lock_and_tmp_only_inside_task_folder(
        self, project_b: ProjectB
    ):
        task = "9012"
        _create(project_b, task, "task164-9012")

        result = run_worktree_cli(
            [
                "ownership-set",
                "--project-root",
                str(project_b.root),
                "--task",
                task,
                "--execution-ownership",
                "session_launching",
                "--attribution-state",
                "active",
            ]
        )
        payload = parse_json_stdout(result, "ownership-set(9012)")
        assert payload.get("ok") is True, f"Task164 S-1 ownership-set 실패: {payload}"

        meta_root = project_b.root / ".opal-worktrees" / ".meta"
        task_dir = meta_root / f"task_{task}"

        # 새 구조: lock·임시 파일은 태스크 폴더 안에만 존재해야 한다.
        assert (task_dir / "meta.json").is_file(), (
            f"Task164 S-1: {task_dir}/meta.json이 없다"
        )
        assert (task_dir / "meta.json.lock").exists(), (
            f"Task164 S-1: lock 파일이 태스크 폴더 안에 없다 — {task_dir}"
        )
        tmp_leftovers_in_task_dir = list(task_dir.glob("meta.json.tmp.*"))
        # 임시 파일은 os.replace로 정리되므로 남아있지 않아야 하지만, 남더라도 태스크 폴더
        # 안에만 있어야 한다(허용). 핵심 위반은 `.meta/` 루트에 남는 것이다.
        stray_in_meta_root = [
            p
            for p in meta_root.iterdir()
            if p.is_file()
            and (
                p.name == f"task_{task}.json"
                or p.name == f"task_{task}.json.lock"
                or p.name.startswith(f"task_{task}.json.tmp.")
            )
        ]
        assert not stray_in_meta_root, (
            f"Task164 S-1: `.meta/` 루트에 태스크 전용 파일이 새어나왔다 — {stray_in_meta_root} "
            f"(임시 파일은 태스크 폴더 안에만 허용: {tmp_leftovers_in_task_dir})"
        )

    def test_meta_root_has_no_files_other_than_task_folders(self, project_b: ProjectB):
        task = "9013"
        _create(project_b, task, "task164-9013")
        run_worktree_cli(
            [
                "ownership-set",
                "--project-root",
                str(project_b.root),
                "--task",
                task,
                "--execution-ownership",
                "session_launching",
                "--attribution-state",
                "active",
            ]
        )

        meta_root = project_b.root / ".opal-worktrees" / ".meta"
        top_level_files = [p for p in meta_root.iterdir() if p.is_file()]
        assert top_level_files == [], (
            f"Task164 S-1: `.meta/` 바로 아래에 파일이 있으면 안 된다(폴더만 허용) — "
            f"{top_level_files}"
        )

    def test_issued_ownership_invariants_unchanged_under_new_layout(
        self, project_b: ProjectB
    ):
        """새 메타 위치로 바뀌어도 발급 6종 필드와
        `task_path == realpath(task_home/tasks/task_folder)` 불변식은 그대로다."""
        task = "9014"
        payload = _create(project_b, task, "task164-9014")

        required_fields = (
            "allocator_root",
            "task_home",
            "task_folder",
            "task_path",
            "artifact_repo",
            "task_ownership_version",
        )
        for field in required_fields:
            assert field in payload, f"Task164 S-1: 응답에 {field} 누락: {payload}"

        meta_path = _meta_dir(project_b, task) / "meta.json"
        assert meta_path.is_file(), f"Task164 S-1: 새 구조 메타 부재 — {meta_path}"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        for field in required_fields:
            assert field in meta, f"Task164 S-1: 메타에 {field} 누락: {meta}"

        expected_task_path = os.path.realpath(
            os.path.join(str(meta["task_home"]), "tasks", str(meta["task_folder"]))
        )
        assert os.path.realpath(str(meta["task_path"])) == expected_task_path, (
            f"Task164 S-1: task_path 불변식 위반: {meta}"
        )


class TestTask164ListIgnoresOldStructure:
    """S-2 (AC-1, AC-2, C-3) — 새 구조 2건만 보고하고 구 구조 파일은 무시·바이트 불변."""

    def test_list_reports_new_structure_only_and_old_file_untouched(
        self, project_b: ProjectB
    ):
        _create(project_b, "9031", "task164-9031-a")
        _create(project_b, "9032", "task164-9032-b")

        meta_root = project_b.root / ".opal-worktrees" / ".meta"
        old_flat = meta_root / "task_900.json"
        old_flat.parent.mkdir(parents=True, exist_ok=True)
        old_body = json.dumps({"task": "900", "legacy": True}, ensure_ascii=False, indent=2)
        old_flat.write_text(old_body, encoding="utf-8")
        old_bytes_before = old_flat.read_bytes()

        result = run_worktree_cli(["list", "--project-root", str(project_b.root)])
        payload = parse_json_stdout(result, "list(S-2)")
        assert payload.get("ok") is True, f"Task164 S-2 list 실패: {payload}"

        tasks_reported = {entry.get("task") for entry in payload.get("entries", [])}
        assert tasks_reported == {"9031", "9032"}, (
            f"Task164 S-2: list가 새 구조 2건만 보고해야 한다 — {tasks_reported}"
        )
        assert old_flat.read_bytes() == old_bytes_before, (
            "Task164 S-2: 구 구조 파일 바이트가 list 실행 후 바뀌었다"
        )


class TestTask164RemoveRecoversTaskFolder:
    """S-3 (AC-1, C-3) — remove 성공 시 태스크 폴더 전체 삭제, 실패 시 보존."""

    def test_remove_success_deletes_whole_task_folder_including_lock(
        self, project_b: ProjectB
    ):
        task = "9021"
        _create(project_b, task, "task164-9021")
        task_dir = _meta_dir(project_b, task)
        assert task_dir.exists(), "Task164 S-3 setup: 태스크 폴더가 만들어지지 않았다"

        result = run_worktree_cli(
            ["remove", "--project-root", str(project_b.root), "--task", task, "--force"]
        )
        payload = parse_json_stdout(result, "remove(9021)")
        assert payload.get("ok") is True, f"Task164 S-3 remove 실패: {payload}"

        assert not task_dir.exists(), (
            f"Task164 S-3: remove 성공 후에도 태스크 폴더가 남아있다 — {task_dir}"
        )
        meta_root = project_b.root / ".opal-worktrees" / ".meta"
        assert meta_root.is_dir(), "Task164 S-3: `.meta/` 자체는 남아야 한다"

    def test_remove_failure_preserves_task_folder_and_meta(self, project_b: ProjectB):
        """가드 위반(unmerged 등)으로 remove가 실패하면 메타·lock·태스크 폴더가 보존된다."""
        task = "9022"
        _create(project_b, task, "task164-9022")

        # 실제 워크트리 디렉토리를 지워 가드가 WORKTREE_NOT_FOUND로 실패하게 만든다
        # (force 없이 호출) — 실패 시 메타 폴더 보존을 관찰하는 목적에는 원인 불문이다.
        created_meta_path = _meta_dir(project_b, task) / "meta.json"
        meta_before = None
        if created_meta_path.is_file():
            meta_before = created_meta_path.read_bytes()

        wt_root = project_b.root / ".opal-worktrees" / f"task_{task}"
        import shutil

        if wt_root.exists():
            shutil.rmtree(wt_root)

        result = run_worktree_cli(
            ["remove", "--project-root", str(project_b.root), "--task", task]
        )
        payload = parse_json_stdout(result, "remove(9022 failing)")
        assert payload.get("ok") is False, (
            f"Task164 S-3 setup 가정 실패: 실패가 관측되지 않았다 — {payload}"
        )

        task_dir = _meta_dir(project_b, task)
        assert task_dir.exists(), (
            f"Task164 S-3: 실패한 remove가 태스크 폴더를 지웠다 — {task_dir}"
        )
        assert created_meta_path.is_file(), (
            f"Task164 S-3: 실패한 remove가 메타 파일을 지웠다 — {created_meta_path}"
        )
        if meta_before is not None:
            assert created_meta_path.read_bytes() == meta_before, (
                "Task164 S-3: 실패한 remove가 메타 바이트를 바꿨다"
            )
