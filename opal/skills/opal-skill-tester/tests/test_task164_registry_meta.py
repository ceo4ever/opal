"""
@header {
  "module": "test_task164_registry_meta",
  "layer": "test",
  "domain": "opal-skill-tester",
  "description": "TASK-164 S-2 — skill_tester._registry_checkpoint_shas가 `.meta/task_*/meta.json` 새 구조만 읽고 구 구조 `.meta/task_{NNN}.json`은 읽지도 바꾸지도 않음을 검증한다.",
  "exports": []
}
"""
import importlib.util
import json
import pathlib


SKILL_DIR = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "skill_tester.py"
SPEC = importlib.util.spec_from_file_location("skill_tester", SCRIPT)
skill_tester = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(skill_tester)


def _write_meta(meta_dir, folder_name, worktree_root, checkpoint_shas):
    task_dir = meta_dir / folder_name
    task_dir.mkdir(parents=True)
    meta = {
        "worktree_root": str(worktree_root),
        "execution_ownership": {"checkpoint_shas": checkpoint_shas},
    }
    (task_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


def test_registry_checkpoint_shas_reads_new_layout_only(tmp_path):
    repo = tmp_path / "hub"
    meta_dir = repo / ".opal-worktrees" / ".meta"
    code = tmp_path / "issued" / "worktree-code"
    code.mkdir(parents=True)

    _write_meta(meta_dir, "task_161", code, ["abc111"])
    other_code = tmp_path / "issued" / "other-worktree-code"
    other_code.mkdir(parents=True)
    _write_meta(meta_dir, "task_162", other_code, ["zzz999"])

    legacy = meta_dir / "task_900.json"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text(json.dumps({
        "worktree_root": str(code),
        "execution_ownership": {"checkpoint_shas": ["legacy-should-not-be-returned"]},
    }), encoding="utf-8")
    before = legacy.read_bytes()

    result = skill_tester._registry_checkpoint_shas(repo, code)

    assert result == ["abc111"]
    assert legacy.read_bytes() == before


def test_registry_checkpoint_shas_ignores_legacy_only_row(tmp_path):
    repo = tmp_path / "hub"
    meta_dir = repo / ".opal-worktrees" / ".meta"
    code = tmp_path / "issued" / "worktree-code"
    code.mkdir(parents=True)

    legacy = meta_dir / "task_900.json"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text(json.dumps({
        "worktree_root": str(code),
        "execution_ownership": {"checkpoint_shas": ["legacy-sha"]},
    }), encoding="utf-8")
    before = legacy.read_bytes()

    result = skill_tester._registry_checkpoint_shas(repo, code)

    assert result == []
    assert legacy.read_bytes() == before
