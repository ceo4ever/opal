"""
@header {
  "module": "test_worktree_tool",
  "layer": "test",
  "domain": "opal-workspace",
  "description": "worktree-tool 공개 인터페이스 회귀 테스트. 092 TEST-SCENARIO.md S-4~S-17,S-21~S-28과 112 TEST-SCENARIO.md S-8 hub-fixed worktree 계약을 검증한다. S-1/S-2는 state-tool 측 전용이라 test_state_tool.py에 있다. S-3/S-15는 각각 git working-tree diff의 일관성/~/.opal 배포본 변경 금지 때문에 이 파일에서 제외했다(092/112 번호 체계). CLI(subprocess) 공개 인터페이스로만 검증하고, mock/patch 없이 실 git 저장소 fixture(conftest.py)를 사용한다. 118 TEST-SCENARIO.md S-3~S-8,S-11,S-15(taskCapsuleCone·canonical metadata 6필드·TASK_PATH_AMBIGUOUS·finalize 재진입 path-scoped 판정·memory-index-request 가드)를 RED-first로 추가한다 — S-3만 구현 전에도 PASS해야 하는 회귀 보호 케이스이고 나머지는 구현 전 FAIL이 정상이다.",
  "exports": [],
  "depends": ["conftest.py", "worktree_tool.py", "opal/tools/state-tool/state_tool.py"]
}
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

import pytest

from conftest import (
    OPAL_DIR,
    WORKTREE_TOOL_PATH,
    ProjectA,
    ProjectB,
    add_worktree,
    build_guard_repo,
    clone_repo,
    make_bare_remote,
    make_monorepo_bare_remote,
    parse_json_stdout,
    run_git,
    run_state_cli,
    run_worktree_cli,
    write_json,
    write_meta,
)


def _minimal_project(tmp_path: pathlib.Path, config: dict, name: str) -> pathlib.Path:
    """레포·워크트리 없이 `.opal/worktree.json`만 있는 프로젝트 — list의 config 검증만
    타는 S-14 ①②③④ 케이스용(pre-flight 파일시스템 검사는 create에서만 발생한다)."""
    root = tmp_path / name
    root.mkdir()
    write_json(root / ".opal" / "worktree.json", config)
    return root


def _build_independent_repo(
    remotes_dir: pathlib.Path,
    project_root: pathlib.Path,
    workspace_subdir: str,
    repo_name: str,
    extra_files: dict | None = None,
) -> pathlib.Path:
    """S-30(`init` 탐지) 전용 — `<project_root>/<workspace_subdir>/<repo_name>`에 독립
    bare remote의 clone(자체 `.git` 보유)을 만든다. `extra_files`(상대경로→내용)는 워킹
    트리에만 기록한다 — 탐지는 파일시스템 스캔이므로 커밋이 필요 없다."""
    origin = make_bare_remote(remotes_dir, f"origin_{repo_name}")
    dest = clone_repo(origin, project_root / workspace_subdir, repo_name)
    for relpath, content in (extra_files or {}).items():
        target = dest / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return dest


# ═════════════════════════════════════════════════════════════════════════════
# S-14: validate_worktree_config() — 부적합 6종 + 템플릿 2종 (H-9, F-1 AC)
# ═════════════════════════════════════════════════════════════════════════════


def test_s14_1_missing_layout_key_gives_config_missing_key(tmp_path):
    """[T092/L1-F1] S-14 ① `layout` 키 누락 → CONFIG_MISSING_KEY (list 경로)."""
    root = _minimal_project(tmp_path, {"repos": ["workspace/a"]}, "proj_cfg1")
    result = run_worktree_cli(["list", "--project-root", str(root)])
    payload = parse_json_stdout(result, "list(S-14①)")
    assert payload.get("ok") is False
    assert payload.get("error") == "CONFIG_MISSING_KEY"


def test_s14_2_invalid_layout_value_gives_config_invalid_layout(tmp_path):
    """[T092/L1-F1] S-14 ② `layout: "unknown"` → CONFIG_INVALID_LAYOUT (①과 다른 코드)."""
    root = _minimal_project(
        tmp_path, {"layout": "unknown", "repos": ["workspace/a"]}, "proj_cfg2"
    )
    result = run_worktree_cli(["list", "--project-root", str(root)])
    payload = parse_json_stdout(result, "list(S-14②)")
    assert payload.get("ok") is False
    assert payload.get("error") == "CONFIG_INVALID_LAYOUT"


def test_s14_3_repos_path_escape_gives_config_path_escape(tmp_path):
    """[T092/L1-F1] S-14 ③ `repos: ["../escape"]` → CONFIG_PATH_ESCAPE (①②와 다른 코드)."""
    root = _minimal_project(
        tmp_path,
        {"layout": "multi-repo", "repos": ["../escape"]},
        "proj_cfg3",
    )
    result = run_worktree_cli(["list", "--project-root", str(root)])
    payload = parse_json_stdout(result, "list(S-14③)")
    assert payload.get("ok") is False
    assert payload.get("error") == "CONFIG_PATH_ESCAPE"


def test_s14_4_empty_repos_array_gives_config_invalid_type(tmp_path):
    """[T092/L1-F1] S-14 ④ `repos: []`(빈 배열) → CONFIG_INVALID_TYPE."""
    root = _minimal_project(
        tmp_path, {"layout": "multi-repo", "repos": []}, "proj_cfg4"
    )
    result = run_worktree_cli(["list", "--project-root", str(root)])
    payload = parse_json_stdout(result, "list(S-14④)")
    assert payload.get("ok") is False
    assert payload.get("error") == "CONFIG_INVALID_TYPE"


def test_s14_error_codes_are_all_distinct(tmp_path):
    """[T092/L1-F1] S-14 — ①②③이 서로 모두 다른 코드인지 교차 확인."""
    codes = set()
    variants = [
        {"repos": ["workspace/a"]},
        {"layout": "unknown", "repos": ["workspace/a"]},
        {"layout": "multi-repo", "repos": ["../escape"]},
    ]
    for i, cfg in enumerate(variants):
        root = _minimal_project(tmp_path, cfg, f"proj_distinct_{i}")
        result = run_worktree_cli(["list", "--project-root", str(root)])
        payload = parse_json_stdout(result, f"list(S-14 distinct #{i})")
        codes.add(payload.get("error"))
    assert len(codes) == 3, f"①②③의 에러 코드가 서로 달라야 한다: {codes}"


def test_s14_5_non_git_repo_dir_rejected_pre_flight_with_zero_side_effect(tmp_path):
    """[T092/L1-F1] S-14 ⑤ `repos[1]`이 `.git` 없는 일반 디렉토리 → pre-flight
    NOT_A_GIT_REPO로 거부, worktree 0개·브랜치 0개 (S-12 롤백 경로와 별개 계약)."""
    root = tmp_path / "proj_cfg5"
    root.mkdir()
    remotes = tmp_path / "_remotes5"
    remotes.mkdir()
    origin = make_bare_remote(remotes, "origin_a5")
    repo_a = clone_repo(origin, root / "workspace", "a")
    plain_dir = root / "workspace" / "plain"
    plain_dir.mkdir(parents=True)
    write_json(
        root / ".opal" / "worktree.json",
        {
            "layout": "multi-repo",
            "repos": ["workspace/a", "workspace/plain"],
            "branchTemplate": "feat/OP-TASK-{NNN}",
            "copy": [],
            "setup": [],
            "portOffset": 0,
        },
    )
    result = run_worktree_cli(["create", "--project-root", str(root), "--task", "092"])
    payload = parse_json_stdout(result, "create(S-14⑤)")
    assert payload.get("ok") is False
    assert payload.get("error") == "NOT_A_GIT_REPO"

    wt_list = run_git(["worktree", "list", "--porcelain"], cwd=repo_a).stdout
    assert "task_092" not in wt_list, "pre-flight 실패인데 worktree가 생성됨"
    branch_list = run_git(["branch", "--list", "feat/OP-TASK-092"], cwd=repo_a).stdout
    assert branch_list.strip() == "", "pre-flight 실패인데 브랜치가 생성됨"


def test_s14_6_symlink_repo_path_is_not_resolved_and_passes(tmp_path):
    """[T092/L1-F1] S-14 ⑥ `repos[0]`이 프로젝트 밖을 가리키는 심볼릭 링크 →
    PLAN §3.1.3 `_is_inside()`가 심볼릭 링크를 해석하지 않으므로 통과(ok:true)를 기대한다.
    구현자가 `resolve()`로 바꾸면 이 케이스가 깨져 설계 결정을 고정한다."""
    root = tmp_path / "proj_cfg6"
    root.mkdir()
    remotes = tmp_path / "_remotes6"
    remotes.mkdir()
    origin = make_bare_remote(remotes, "origin_ext6")
    external_repo = clone_repo(origin, tmp_path / "_external6", "ext_repo")
    (root / "workspace").mkdir()
    link_path = root / "workspace" / "linked"
    link_path.symlink_to(external_repo, target_is_directory=True)
    write_json(
        root / ".opal" / "worktree.json",
        {
            "layout": "multi-repo",
            "repos": ["workspace/linked"],
            "branchTemplate": "feat/OP-TASK-{NNN}",
            "copy": [],
            "setup": [],
            "portOffset": 0,
        },
    )
    result = run_worktree_cli(["create", "--project-root", str(root), "--task", "092"])
    payload = parse_json_stdout(result, "create(S-14⑥)")
    assert payload.get("error") != "CONFIG_PATH_ESCAPE", (
        f"심볼릭 링크는 경로 이탈로 거부되면 안 된다(설계 결정 위반): {payload}"
    )
    assert payload.get("ok") is True, f"심볼릭 링크 경로는 통과(ok:true)를 기대: {payload}"


def test_s14_multi_repo_template_passes_validation(project_a: ProjectA):
    """[T092/L1-F1] S-14 — 유형 A 템플릿이 검증을 통과한다."""
    result = run_worktree_cli(["list", "--project-root", str(project_a.root)])
    payload = parse_json_stdout(result, "list(S-14 유형A 템플릿)")
    assert payload.get("ok") is True, f"유형 A 템플릿이 검증에 실패함: {payload}"


def test_s14_monorepo_template_passes_validation(project_b: ProjectB):
    """[T092/L1-F1] S-14 — 유형 B 템플릿이 검증을 통과한다."""
    result = run_worktree_cli(["list", "--project-root", str(project_b.root)])
    payload = parse_json_stdout(result, "list(S-14 유형B 템플릿)")
    assert payload.get("ok") is True, f"유형 B 템플릿이 검증에 실패함: {payload}"


# ═════════════════════════════════════════════════════════════════════════════
# S-4 / S-5: create — 유형 A(multi-repo) / 유형 B(monorepo) (H-3, H-4)
# ═════════════════════════════════════════════════════════════════════════════


def test_s4_multi_repo_create_creates_worktree_per_repo(project_a: ProjectA):
    """[T092/L2-F2a] S-4 — 코드 레포 2곳에 각각 worktree 생성, 경로·브랜치명·메타 확인."""
    result = run_worktree_cli(
        ["create", "--project-root", str(project_a.root), "--task", "092"]
    )
    payload = parse_json_stdout(result, "create(S-4)")
    assert payload.get("ok") is True, f"S-4 create 실패: {payload}"
    assert payload.get("branch") == "feat/OP-TASK-092"

    wt_root = project_a.root / ".opal-worktrees" / "task_092"
    assert payload.get("worktree_root") == str(wt_root)

    for repo, name in ((project_a.backend, "backend"), (project_a.frontend, "frontend")):
        wt_list = run_git(["worktree", "list", "--porcelain"], cwd=repo).stdout
        expected_path = str(wt_root / "workspace" / name)
        assert expected_path in wt_list, f"{name} worktree 미생성: {wt_list}"

    meta_path = project_a.root / ".opal-worktrees" / ".meta" / "task_092.json"
    assert meta_path.exists(), "메타 파일 미생성"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert len(meta["entries"]) == 2
    for entry in meta["entries"]:
        assert entry.get("base_ref"), f"entries[].base_ref 기록 누락(DEC-3): {entry}"


def test_s5_monorepo_create_checks_out_workspace_only(project_b: ProjectB):
    """[T092/L2-F2b] S-5 — sparse worktree에 workspace/만 존재, tasks/·.opal/ 부재."""
    result = run_worktree_cli(
        ["create", "--project-root", str(project_b.root), "--task", "092"]
    )
    payload = parse_json_stdout(result, "create(S-5)")
    assert payload.get("ok") is True, f"S-5 create 실패: {payload}"
    assert payload.get("branch") == "feat/OP-TASK-092"

    wt_root = project_b.root / ".opal-worktrees" / "task_092"
    assert (wt_root / "workspace").exists(), "workspace/ 미체크아웃"
    assert not (wt_root / "tasks").exists(), "tasks/가 체크아웃됨(H-4 위반)"
    assert not (wt_root / ".opal").exists(), ".opal/이 체크아웃됨(H-4 위반)"


def test_s8_hub_fixed_paths_are_not_in_opal_monorepo_sparse_set(tmp_path):
    """[T112/L2-S8] OPAL형 monorepo 설정은 source repos만 sparse checkout하고,
    hub-fixed `.opal/`·`tasks/`와 삭제된 stale `memory` repo를 worktree에 포함하지 않는다."""
    remotes_dir = tmp_path / "_remotes_112_s8"
    remotes_dir.mkdir()
    origin = make_bare_remote(remotes_dir, "origin_112_s8")
    project_root = clone_repo(origin, tmp_path, "proj_112_s8")

    source_repos = ["cursor-rules", "dashboard", "docs", "opal", "scripts", "skills"]
    for rel in source_repos:
        path = project_root / rel / "README.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {rel}\n", encoding="utf-8")
    for rel in ("tasks/README.md", ".opal/README.md", "memory/README.md"):
        path = project_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {path.parent.name}\n", encoding="utf-8")

    run_git(["add", "-A"], cwd=project_root)
    run_git(["commit", "-m", "seed opal monorepo"], cwd=project_root)
    run_git(["push", "origin", "main"], cwd=project_root)

    write_json(
        project_root / ".opal" / "worktree.json",
        {
            "layout": "monorepo",
            "repos": source_repos,
            "branchTemplate": "feat/OP-TASK-{NNN}",
            "copy": [],
            "setup": [],
            "portOffset": 0,
        },
    )

    result = run_worktree_cli(
        ["create", "--project-root", str(project_root), "--task", "112"]
    )
    payload = parse_json_stdout(result, "create(T112/S-8)")
    assert payload.get("ok") is True, f"OPAL형 monorepo create 실패: {payload}"

    wt_root = project_root / ".opal-worktrees" / "task_112"
    for rel in source_repos:
        assert (wt_root / rel).exists(), f"source repo가 sparse checkout되지 않음: {rel}"
    assert not (wt_root / ".opal").exists(), ".opal/이 체크아웃됨(hub-fixed 계약 위반)"
    assert not (wt_root / "tasks").exists(), "tasks/가 체크아웃됨(hub-fixed 계약 위반)"
    assert not (wt_root / "memory").exists(), "stale memory repo가 체크아웃됨"


# ═════════════════════════════════════════════════════════════════════════════
# S-6~S-10, S-13: remove 3중 가드 + --force + base-ref 동결 (H-5, H-8)
# ═════════════════════════════════════════════════════════════════════════════


def test_s6_remove_rejects_dirty_worktree(tmp_path):
    """[T092/L2-F8a] S-6 — dirty 작업본은 GUARD_DIRTY로 거부, 디렉토리·브랜치 잔존."""
    g = build_guard_repo(tmp_path, "dirty")
    result = run_worktree_cli(
        ["remove", "--project-root", str(g.project_root), "--task", g.task]
    )
    payload = parse_json_stdout(result, "remove(S-6)")
    assert payload.get("ok") is False
    assert payload.get("error") == "GUARD_DIRTY"
    assert g.wt_path.exists(), "dirty 거부 시 worktree 디렉토리가 잔존해야 한다"
    branch_list = run_git(["branch", "--list", g.branch], cwd=g.repo).stdout
    assert g.branch in branch_list, "dirty 거부 시 브랜치가 잔존해야 한다"


def test_s7_remove_rejects_unpushed_commit(tmp_path):
    """[T092/L2-F8b] S-7 — clean이지만 unpushed 커밋 존재 → GUARD_UNPUSHED (S-6과 다른 코드)."""
    g = build_guard_repo(tmp_path, "unpushed")
    result = run_worktree_cli(
        ["remove", "--project-root", str(g.project_root), "--task", g.task]
    )
    payload = parse_json_stdout(result, "remove(S-7)")
    assert payload.get("ok") is False
    assert payload.get("error") == "GUARD_UNPUSHED"
    assert payload.get("error") != "GUARD_DIRTY"


def test_s8_remove_rejects_unmerged_branch(tmp_path):
    """[T092/L2-F8c] S-8 — clean+push완료지만 base에 미머지 → GUARD_UNMERGED (S-6·S-7과 다른 코드)."""
    g = build_guard_repo(tmp_path, "unmerged")
    result = run_worktree_cli(
        ["remove", "--project-root", str(g.project_root), "--task", g.task]
    )
    payload = parse_json_stdout(result, "remove(S-8)")
    assert payload.get("ok") is False
    assert payload.get("error") == "GUARD_UNMERGED"
    assert payload.get("error") not in ("GUARD_DIRTY", "GUARD_UNPUSHED")


def test_s9_remove_succeeds_when_all_guards_clear_and_keeps_branch(tmp_path):
    """[T092/L2-F8d] S-9 — 3조건 모두 해소 시 성공, worktree 제거되지만 브랜치는 잔존."""
    g = build_guard_repo(tmp_path, "clean")
    result = run_worktree_cli(
        ["remove", "--project-root", str(g.project_root), "--task", g.task]
    )
    payload = parse_json_stdout(result, "remove(S-9)")
    assert payload.get("ok") is True, f"3조건 해소 시 성공 기대: {payload}"
    assert not g.wt_path.exists(), "성공 시 worktree 디렉토리가 제거돼야 한다"
    branch_list = run_git(["branch", "--list", g.branch], cwd=g.repo).stdout
    assert g.branch in branch_list, "remove는 브랜치를 삭제하면 안 된다(user sovereignty)"


def test_s10_remove_force_bypasses_guard_and_records_it(tmp_path):
    """[T092/L2-F8e] S-10 — `--force`가 dirty 가드를 우회하되 stdout에 우회 사실을 기록."""
    g = build_guard_repo(tmp_path, "dirty")
    result = run_worktree_cli(
        ["remove", "--project-root", str(g.project_root), "--task", g.task, "--force"]
    )
    payload = parse_json_stdout(result, "remove(S-10)")
    assert payload.get("ok") is True, f"--force는 성공해야 한다: {payload}"
    assert payload.get("forced") is True
    bypassed = payload.get("bypassed_guards") or []
    assert "GUARD_DIRTY" in bypassed, f"우회된 가드가 stdout에 기록돼야 한다: {payload}"


def test_s13_remove_uses_frozen_base_ref_not_live_origin_head(tmp_path):
    """[T092/L2-F8f] S-13 — H-8/DEC-3: origin의 기본 브랜치 포인터가 create 이후 바뀌어도
    remove 판정은 메타에 동결된 base_ref(main)를 그대로 쓴다. develop을 branch와 동일
    커밋으로 만든 뒤 로컬 origin/HEAD 캐시를 develop으로 바꾸면, 매 호출마다 base를
    재조회하는 (틀린) 구현은 '병합됨'으로 오판해 가드를 통과시키지만, 동결(올바른) 구현은
    여전히 main 기준 GUARD_UNMERGED를 반환해야 한다."""
    g = build_guard_repo(tmp_path, "unmerged")
    run_git(["push", "origin", "HEAD:refs/heads/develop"], cwd=g.wt_path)
    run_git(["fetch", "origin"], cwd=g.repo)
    run_git(["remote", "set-head", "origin", "develop"], cwd=g.repo)

    result = run_worktree_cli(
        ["remove", "--project-root", str(g.project_root), "--task", g.task]
    )
    payload = parse_json_stdout(result, "remove(S-13)")
    assert payload.get("ok") is False
    assert payload.get("error") == "GUARD_UNMERGED", (
        "origin의 기본 브랜치가 바뀌어도 remove는 메타 동결값(main) 기준으로 판정해야 한다 — "
        f"재조회했다면 오판으로 통과했을 것이다: {payload}"
    )


# ═════════════════════════════════════════════════════════════════════════════
# S-11: .gitignore 멱등 (H-6)
# ═════════════════════════════════════════════════════════════════════════════


def test_s11_gitignore_entry_idempotent_and_byte_unchanged(project_a: ProjectA):
    """[T092/L2-F7] S-11 — 3회 연속 create 후 `.opal-worktrees/` 행 수 1 + 이미 있으면
    바이트 무변경(sha256 동일 — write 자체를 하지 않아야 함)."""
    gitignore_path = project_a.root / ".gitignore"

    r1 = run_worktree_cli(
        ["create", "--project-root", str(project_a.root), "--task", "092"]
    )
    p1 = parse_json_stdout(r1, "create(S-11 1회차)")
    assert p1.get("ok") is True, f"S-11 1회차 create 실패: {p1}"
    content_1 = gitignore_path.read_text(encoding="utf-8")
    lines_1 = [
        line for line in content_1.splitlines() if line.strip() in (".opal-worktrees", ".opal-worktrees/")
    ]
    assert len(lines_1) == 1, f".opal-worktrees 행 수가 1이 아님: {lines_1}"
    sha_before_2 = hashlib.sha256(gitignore_path.read_bytes()).hexdigest()

    r2 = run_worktree_cli(
        ["create", "--project-root", str(project_a.root), "--task", "093"]
    )
    p2 = parse_json_stdout(r2, "create(S-11 2회차)")
    assert p2.get("ok") is True, f"S-11 2회차 create 실패: {p2}"
    sha_after_2 = hashlib.sha256(gitignore_path.read_bytes()).hexdigest()
    assert sha_before_2 == sha_after_2, "이미 항목이 있으면 .gitignore를 재기록하면 안 된다(바이트 무변경)"

    r3 = run_worktree_cli(
        ["create", "--project-root", str(project_a.root), "--task", "094"]
    )
    p3 = parse_json_stdout(r3, "create(S-11 3회차)")
    assert p3.get("ok") is True, f"S-11 3회차 create 실패: {p3}"
    content_3 = gitignore_path.read_text(encoding="utf-8")
    lines_3 = [
        line for line in content_3.splitlines() if line.strip() in (".opal-worktrees", ".opal-worktrees/")
    ]
    assert len(lines_3) == 1, f"3회차 이후에도 행 수가 1이어야 한다: {lines_3}"


# ═════════════════════════════════════════════════════════════════════════════
# S-12: 중간 실패 시 자기 생성물 전량 회수 (H-7, DEC-2)
# ═════════════════════════════════════════════════════════════════════════════


def test_s12_partial_failure_rolls_back_all_created_entries(project_a: ProjectA):
    """[T092/L2-F2c] S-12 — repos[1](frontend)의 `.git`을 쓰기 불가로 만들어 pre-flight는
    통과하되(디렉토리·`.git` 존재, 브랜치 미존재) 실제 `worktree add` 단계에서 실패하도록
    조작한다(DEC-2 "N번째 실패"). repos[0](backend)에 이미 만들어진 worktree·브랜치가
    남으면 안 되고, 조작을 되돌리면 재실행이 막히지 않아야 한다."""
    git_dir = project_a.frontend / ".git"
    original_mode = git_dir.stat().st_mode
    git_dir.chmod(0o555)
    try:
        result = run_worktree_cli(
            ["create", "--project-root", str(project_a.root), "--task", "092"]
        )
    finally:
        git_dir.chmod(original_mode)

    payload = parse_json_stdout(result, "create(S-12)")
    assert payload.get("ok") is False, f"쓰기 불가 repo인데 성공함: {payload}"

    branch = "feat/OP-TASK-092"
    wt_list_be = run_git(["worktree", "list", "--porcelain"], cwd=project_a.backend).stdout
    assert "task_092" not in wt_list_be, "1번째(backend) worktree가 롤백되지 않음"
    branch_list_be = run_git(["branch", "--list", branch], cwd=project_a.backend).stdout
    assert branch_list_be.strip() == "", "1번째(backend) 브랜치가 롤백되지 않음"

    result2 = run_worktree_cli(
        ["create", "--project-root", str(project_a.root), "--task", "092"]
    )
    payload2 = parse_json_stdout(result2, "create(S-12 재실행)")
    assert payload2.get("ok") is True, f"롤백 후 재실행이 막히면 안 된다: {payload2}"


# ═════════════════════════════════════════════════════════════════════════════
# S-16: 캐시 볼륨 진단 — 경고만, 차단 금지 (H-12)
# ═════════════════════════════════════════════════════════════════════════════


def test_s16_cache_volume_mismatch_warns_but_never_blocks(project_a: ProjectA):
    """[T092/L1-F9b] S-16 — `UV_CACHE_DIR`이 프로젝트와 다른 볼륨이면 경고만 하고
    차단하지 않는다. mock 금지 원칙에 따라 실제 두 경로의 st_dev를 비교해, 실제로
    다른 볼륨일 때만 '경고 비어있지 않음'을 강하게 단언한다(환경에 따라 두 경로가
    우연히 같은 볼륨이면 차단 금지 불변만 확인— 실제 자원 기반 판정이므로 결정론을
    강제할 수 없는 부분은 약화시킨다)."""
    candidate_cache_dir = pathlib.Path(tempfile.gettempdir()) / "opal_wt_uv_cache_probe_092"
    candidate_cache_dir.mkdir(parents=True, exist_ok=True)
    same_device = os.stat(candidate_cache_dir).st_dev == os.stat(project_a.root).st_dev

    env = dict(os.environ)
    env["UV_CACHE_DIR"] = str(candidate_cache_dir)
    result = subprocess.run(
        [
            sys.executable,
            str(WORKTREE_TOOL_PATH),
            "create",
            "--project-root",
            str(project_a.root),
            "--task",
            "092",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    payload = parse_json_stdout(result, "create(S-16)")
    assert payload.get("ok") is True, f"볼륨 진단은 절대 create를 차단하면 안 된다: {payload}"
    warnings = payload.get("warnings")
    assert isinstance(warnings, list), "warnings는 항상 리스트여야 한다(예외 없이)"
    if not same_device:
        assert len(warnings) >= 1, f"실제 볼륨 불일치인데 경고가 비어있음: {payload}"


# ═════════════════════════════════════════════════════════════════════════════
# S-17: opal-harness.md 전역 §N 인용에 dangling 없음 + 기존 절 번호 불변 (H-13)
# ═════════════════════════════════════════════════════════════════════════════


def test_s17_harness_citations_resolve_and_existing_sections_are_stable():
    """[T092/L1-F3 → T118/AC-12] S-17 — `opal-harness.md §N` 형태의 전역 인용이 전부 실존
    절을 가리켜야 하며(dangling 0건), 기존 §3·§4·§9 번호는 불변이어야 한다.

    [T118 변경] 원래 이 테스트는 `## 2.5` 절의 **존재**도 함께 단언했으나(태스크 092 Step 9의
    RED 증거), 태스크 118 AC-12가 그 §2.5 포인터를 제거하기로 확정하면서 존재 단언이 계약과
    정면 충돌하게 됐다. 존재 단언만 제거하고, 실제 가드로 유용한 dangling 인용 검사와 기존
    절 번호 불변 단언은 그대로 보존한다 — §2.5를 가리키던 인용이 남아 있으면 dangling 검사가
    잡아낸다."""
    harness_path = OPAL_DIR / "core" / "references" / "opal-harness.md"
    harness_md = harness_path.read_text(encoding="utf-8")

    cited_numbers = set()
    for md_path in OPAL_DIR.rglob("*.md"):
        text = md_path.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"opal-harness\.md\s*§(\d+(?:\.\d+)?)", text):
            cited_numbers.add(m.group(1))

    # 해소 가능한 번호 = 이 파일에 실존하는 `## N` 절 ∪ `## 구형 절 참조 호환 매핑` 표가
    # 새 SSOT로 안내하는 구형 번호. opal-harness.md는 번호 절을 owner 문서로 분해하고 그
    # 호환 매핑 표만 남기는 구조로 이미 전환됐으므로(허브·워크트리 동일), 인용 해소 대상은
    # 두 출처의 합집합이다. 표에서 행이 사라진 번호를 누군가 계속 인용하면 여기서 걸린다.
    existing_headings = set(re.findall(r"^##\s+(\d+(?:\.\d+)?)", harness_md, flags=re.MULTILINE))
    mapping_section = harness_md.split("## 구형 절 참조 호환 매핑", 1)[-1]
    mapped_numbers = set(
        re.findall(r"opal-harness\.md\s*§(\d+(?:\.\d+)?)", mapping_section)
    )
    resolvable = existing_headings | mapped_numbers

    dangling = cited_numbers - resolvable
    assert not dangling, f"dangling §번호 인용 발견(절도 호환 매핑도 없음): {dangling}"
    for must_have in ("3", "4", "9"):
        assert must_have in resolvable, (
            f"기존 §{must_have} 번호가 절에서도 호환 매핑에서도 사라짐(H-13 위반)"
        )


# ═════════════════════════════════════════════════════════════════════════════
# S-21: lazy setup — 실행하지 않고 열거만 (H-15, C-7)
# ═════════════════════════════════════════════════════════════════════════════


def test_s21_setup_commands_are_not_executed_but_enumerated(tmp_path):
    """[T092/L2-F2d] S-21 — `setup[]`에 sentinel 생성 명령을 넣어도 create는 실행하지
    않고 `pending_setup[]`에 열거만 한다."""
    remotes_dir = tmp_path / "_remotes21"
    remotes_dir.mkdir()
    project_root = tmp_path / "proj_lazy"
    project_root.mkdir()
    origin = make_bare_remote(remotes_dir, "origin_lazy")
    clone_repo(origin, project_root / "workspace", "app")

    sentinel = project_root / "SENTINEL_SHOULD_NOT_EXIST"
    write_json(
        project_root / ".opal" / "worktree.json",
        {
            "layout": "multi-repo",
            "repos": ["workspace/app"],
            "branchTemplate": "feat/OP-TASK-{NNN}",
            "copy": [],
            "setup": [{"cwd": ".", "run": f"touch {sentinel}"}],
            "portOffset": 0,
        },
    )
    result = run_worktree_cli(
        ["create", "--project-root", str(project_root), "--task", "092"]
    )
    payload = parse_json_stdout(result, "create(S-21)")
    assert payload.get("ok") is True, f"S-21 create 실패: {payload}"
    assert not sentinel.exists(), "setup[]은 실행되면 안 된다(lazy setup, C-7)"
    pending = payload.get("pending_setup") or []
    assert len(pending) == 1, f"pending_setup[]에 setup 항목이 열거돼야 한다: {payload}"
    assert pending[0].get("run") == f"touch {sentinel}"


# ═════════════════════════════════════════════════════════════════════════════
# S-22: 동시 슬롯 2개째부터 경고, 차단 없음 (H-16, DEC-6)
# ═════════════════════════════════════════════════════════════════════════════


def test_s22_concurrent_slot_warning_appears_from_second_slot_only(project_a: ProjectA):
    """[T092/L2-F2e] S-22 — 1회차는 동시 슬롯 경고 부재, 2회차는 출현. 양쪽 모두 ok:true."""
    r1 = run_worktree_cli(
        ["create", "--project-root", str(project_a.root), "--task", "092"]
    )
    p1 = parse_json_stdout(r1, "create(S-22 1회차)")
    assert p1.get("ok") is True
    warnings1 = p1.get("warnings") or []
    assert not any("슬롯" in w for w in warnings1), f"1회차는 동시 슬롯 경고가 없어야 한다: {warnings1}"

    r2 = run_worktree_cli(
        ["create", "--project-root", str(project_a.root), "--task", "093"]
    )
    p2 = parse_json_stdout(r2, "create(S-22 2회차)")
    assert p2.get("ok") is True, "2회차도 차단 없이 성공해야 한다"
    warnings2 = p2.get("warnings") or []
    assert any("슬롯" in w for w in warnings2), f"2회차는 동시 슬롯 경고가 출현해야 한다: {warnings2}"


# ═════════════════════════════════════════════════════════════════════════════
# S-23: 두 슬롯이 서로 간섭 없이 독립 작업 (목표달성 시나리오)
# ═════════════════════════════════════════════════════════════════════════════


def test_s23_two_slots_are_isolated_from_each_other(project_a: ProjectA):
    """[T092/L2-목표] S-23 — 슬롯 092에서 커밋해도 슬롯 093·메인 작업본이 영향받지 않는다."""
    r1 = run_worktree_cli(
        ["create", "--project-root", str(project_a.root), "--task", "092"]
    )
    p1 = parse_json_stdout(r1, "create(S-23 슬롯092)")
    assert p1.get("ok") is True
    r2 = run_worktree_cli(
        ["create", "--project-root", str(project_a.root), "--task", "093"]
    )
    p2 = parse_json_stdout(r2, "create(S-23 슬롯093)")
    assert p2.get("ok") is True

    wt092_backend = project_a.root / ".opal-worktrees" / "task_092" / "workspace" / "backend"
    wt093_backend = project_a.root / ".opal-worktrees" / "task_093" / "workspace" / "backend"

    (wt092_backend / "slot092.txt").write_text("slot 092 change\n", encoding="utf-8")
    run_git(["add", "slot092.txt"], cwd=wt092_backend)
    run_git(["commit", "-m", "slot 092 change"], cwd=wt092_backend)

    status_093 = run_git(["status", "--porcelain"], cwd=wt093_backend).stdout
    assert status_093 == "", f"슬롯 093이 슬롯 092의 변경에 영향받음: {status_093!r}"
    assert (
        run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=wt093_backend).stdout.strip()
        == "feat/OP-TASK-093"
    )
    assert (
        run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=wt092_backend).stdout.strip()
        == "feat/OP-TASK-092"
    )

    main_status = run_git(["status", "--porcelain"], cwd=project_a.backend).stdout
    assert main_status == "", f"메인 작업본이 슬롯 변경에 영향받음: {main_status!r}"
    assert (
        run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=project_a.backend).stdout.strip()
        == "main"
    )


# ═════════════════════════════════════════════════════════════════════════════
# S-24: 파이프라인 관통 — create → state init --worktree → show (H-17, 목표달성)
# ═════════════════════════════════════════════════════════════════════════════


def test_s24_pipeline_flag_flows_from_create_into_state(project_a: ProjectA, tmp_path):
    """[T092/L2-F4b] S-24 — ⓐ create의 worktree_root ⓑ state show json의 data.worktree가
    문자열 동일 ⓒ create 실패 시 --worktree 미전달 + state init 자체는 성공(비차단)
    ⓓ 문서 3종에 축 문안이 실제로 존재(grep). ⓓ는 Step 9~17 GREEN 이전이므로 RED가 정상."""
    r = run_worktree_cli(
        ["create", "--project-root", str(project_a.root), "--task", "092"]
    )
    p = parse_json_stdout(r, "create(S-24)")
    assert p.get("ok") is True, f"S-24 create 실패: {p}"
    worktree_root = p.get("worktree_root")
    assert worktree_root, "worktree_root 필드 누락"

    task_folder = tmp_path / "s24_task_ok"
    task_folder.mkdir()
    r_init = run_state_cli(
        [
            "init",
            str(task_folder),
            "--skill",
            "opd",
            "--mode",
            "interactive",
            "--worktree",
            worktree_root,
        ]
    )
    assert r_init.returncode == 0, f"state init 실패: stdout={r_init.stdout!r} stderr={r_init.stderr!r}"
    init_payload = json.loads(r_init.stdout)
    assert init_payload.get("ok") is True

    r_show = run_state_cli(["show", str(task_folder), "--format", "json"])
    assert r_show.returncode == 0
    show_payload = json.loads(r_show.stdout)
    assert show_payload["data"]["worktree"] == worktree_root, (
        f"data.worktree가 create의 worktree_root와 문자열 동일해야 한다: {show_payload}"
    )

    # ⓒ 실패 경로 — config 부재 프로젝트에서는 --worktree가 전달되지 않고, state init 자체는 성공
    proj_no_config = tmp_path / "s24_no_config"
    proj_no_config.mkdir()
    r_fail = run_worktree_cli(
        ["create", "--project-root", str(proj_no_config), "--task", "092"]
    )
    p_fail = parse_json_stdout(r_fail, "create(S-24 실패경로)")
    assert p_fail.get("ok") is False
    assert p_fail.get("error") == "CONFIG_NOT_FOUND"

    task_folder2 = tmp_path / "s24_task_fail"
    task_folder2.mkdir()
    r_init2 = run_state_cli(
        ["init", str(task_folder2), "--skill", "opd", "--mode", "interactive"]
    )
    assert r_init2.returncode == 0, "create 실패해도 state init 자체는 성공해야 한다(DEC-2 비차단)"
    state2 = json.loads((task_folder2 / "state.json").read_text(encoding="utf-8"))
    assert "worktree" not in state2, "create 실패 시 --worktree 미전달 → 키가 생성되면 안 된다"

    # ⓓ 문서 3종 문안 grep — Step 9~17 GREEN 이전이므로 실패가 RED 증거다
    task_process_md = (
        OPAL_DIR / "core" / "references" / "harness" / "task-process.md"
    ).read_text(encoding="utf-8")
    assert "4.5" in task_process_md, "harness/task-process.md에 스텝 4.5가 있어야 한다"
    assert "worktree-tool create" in task_process_md, "스텝 4.5에 worktree-tool create 호출 문안이 있어야 한다"
    assert "--worktree" in task_process_md, "스텝 4.5~5에 --worktree 전달 문안이 있어야 한다"

    dispatch_md = (
        OPAL_DIR / "core" / "references" / "pm" / "dispatch-process.md"
    ).read_text(encoding="utf-8")
    assert "## 작업 경로" in dispatch_md, "pm/dispatch-process.md에 '## 작업 경로' 블록이 있어야 한다"
    assert "절대경로" in dispatch_md, "pm/dispatch-process.md에 '절대경로' 문구가 있어야 한다"

    harness_md = (OPAL_DIR / "core" / "references" / "opal-harness.md").read_text(encoding="utf-8")
    assert "§2.5" in harness_md or "## 2.5" in harness_md, "opal-harness.md에 §2.5 절이 있어야 한다"


# ═════════════════════════════════════════════════════════════════════════════
# S-25: status가 remove와 동일 판정을 보고하되 거부하지 않음 (H-18)
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("state", ["dirty", "unpushed", "unmerged", "clean"])
def test_s25_status_reports_same_judgment_as_remove_without_rejecting(tmp_path, state):
    """[T092/L2-F2f] S-25 — 4상태 모두 status는 ok:true(거부하지 않음)이고, 보고된
    가드 판정이 같은 상태에서의 remove 판정과 일치한다."""
    g = build_guard_repo(tmp_path, state, name_suffix=f"_s25_{state}")

    status_result = run_worktree_cli(
        ["status", "--project-root", str(g.project_root), "--task", g.task]
    )
    status_payload = parse_json_stdout(status_result, f"status(S-25 {state})")
    assert status_payload.get("ok") is True, f"status는 거부하지 않아야 한다({state}): {status_payload}"

    remove_result = run_worktree_cli(
        ["remove", "--project-root", str(g.project_root), "--task", g.task]
    )
    remove_payload = parse_json_stdout(remove_result, f"remove(S-25 {state})")

    entries = status_payload.get("entries")
    entry = entries[0] if entries else status_payload

    if state == "clean":
        assert remove_payload.get("ok") is True, f"clean 상태는 remove가 성공해야 한다: {remove_payload}"
        assert entry.get("dirty") is False
        assert entry.get("merged") is True
    else:
        assert remove_payload.get("ok") is False, f"{state} 상태는 remove가 거부해야 한다: {remove_payload}"
        if state == "dirty":
            assert entry.get("dirty") is True
            assert remove_payload.get("error") == "GUARD_DIRTY"
        elif state == "unpushed":
            assert entry.get("dirty") is False
            assert (entry.get("unpushed") or 0) > 0
            assert remove_payload.get("error") == "GUARD_UNPUSHED"
        elif state == "unmerged":
            assert entry.get("dirty") is False
            assert entry.get("merged") is False
            assert remove_payload.get("error") == "GUARD_UNMERGED"


def test_s25_close_guidance_references_status_output():
    """[T092/L2-F2f] S-25 — `opal-pilot-dev/SKILL.md` STEP 6 안내가 `status` 출력을
    근거로 삼도록 기술돼 있어야 한다(Step 12 GREEN 이전이므로 실패가 RED 증거)."""
    skill_md = (OPAL_DIR / "skills" / "opal-pilot-dev" / "SKILL.md").read_text(encoding="utf-8")
    assert "worktree-tool" in skill_md, "opal-pilot-dev/SKILL.md에 worktree-tool 언급이 있어야 한다"
    assert "status" in skill_md, "opal-pilot-dev/SKILL.md STEP 6이 status 조회를 근거로 해야 한다"
    assert "머지 대기" in skill_md, "opal-pilot-dev/SKILL.md에 '머지 대기' 안내 문구가 있어야 한다"


# ═════════════════════════════════════════════════════════════════════════════
# S-26: config 부재·무효 시 부수효과 없이 거부 (H-19)
# ═════════════════════════════════════════════════════════════════════════════


def test_s26_missing_config_rejected_without_side_effects(tmp_path):
    """[T092/L2-F3b] S-26 ① — `.opal/worktree.json` 부재 → CONFIG_NOT_FOUND +
    `.gitignore` sha256 불변 + `.opal-worktrees/` 미생성."""
    root = tmp_path / "proj_no_cfg"
    root.mkdir()
    (root / ".gitignore").write_text("*.pyc\n", encoding="utf-8")
    sha_before = hashlib.sha256((root / ".gitignore").read_bytes()).hexdigest()

    result = run_worktree_cli(["create", "--project-root", str(root), "--task", "092"])
    payload = parse_json_stdout(result, "create(S-26①)")
    assert payload.get("ok") is False
    assert payload.get("error") == "CONFIG_NOT_FOUND"

    sha_after = hashlib.sha256((root / ".gitignore").read_bytes()).hexdigest()
    assert sha_before == sha_after, ".gitignore가 변경되면 안 된다(부수효과 0)"
    assert not (root / ".opal-worktrees").exists(), ".opal-worktrees/가 생성되면 안 된다"


def test_s26_broken_json_config_rejected_without_side_effects(tmp_path):
    """[T092/L2-F3b] S-26 ② — 깨진 JSON → CONFIG_INVALID_JSON + 부수효과 0."""
    root = tmp_path / "proj_broken_cfg"
    root.mkdir()
    (root / ".gitignore").write_text("*.pyc\n", encoding="utf-8")
    config_path = root / ".opal" / "worktree.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("{not valid json", encoding="utf-8")
    sha_before = hashlib.sha256((root / ".gitignore").read_bytes()).hexdigest()

    result = run_worktree_cli(["create", "--project-root", str(root), "--task", "092"])
    payload = parse_json_stdout(result, "create(S-26②)")
    assert payload.get("ok") is False
    assert payload.get("error") == "CONFIG_INVALID_JSON"

    sha_after = hashlib.sha256((root / ".gitignore").read_bytes()).hexdigest()
    assert sha_before == sha_after, ".gitignore가 변경되면 안 된다(부수효과 0)"
    assert not (root / ".opal-worktrees").exists(), ".opal-worktrees/가 생성되면 안 된다"


# ═════════════════════════════════════════════════════════════════════════════
# S-27: 살아 있는 슬롯에 동일 번호 재생성 거부 + 무손상 (H-20)
# ═════════════════════════════════════════════════════════════════════════════


def test_s27_duplicate_create_rejected_and_existing_slot_untouched(project_a: ProjectA):
    """[T092/L2-F2e] S-27 — 살아 있는 슬롯에 동일 태스크 번호로 재실행 시 거부되고,
    기존 worktree·브랜치·메타가 무손상이어야 한다(H-7의 반대 방향)."""
    r1 = run_worktree_cli(
        ["create", "--project-root", str(project_a.root), "--task", "092"]
    )
    p1 = parse_json_stdout(r1, "create(S-27 1회차)")
    assert p1.get("ok") is True

    meta_path = project_a.root / ".opal-worktrees" / ".meta" / "task_092.json"
    sha_before = hashlib.sha256(meta_path.read_bytes()).hexdigest()

    r2 = run_worktree_cli(
        ["create", "--project-root", str(project_a.root), "--task", "092"]
    )
    p2 = parse_json_stdout(r2, "create(S-27 재실행)")
    assert p2.get("ok") is False
    assert p2.get("error") in ("WORKTREE_EXISTS", "BRANCH_EXISTS")

    sha_after = hashlib.sha256(meta_path.read_bytes()).hexdigest()
    assert sha_before == sha_after, "재실행 거부 시 기존 메타가 무손상이어야 한다"
    wt_root = project_a.root / ".opal-worktrees" / "task_092"
    assert (wt_root / "workspace" / "backend").exists(), "기존 worktree가 훼손됨"
    branch_list = run_git(["branch", "--list", "feat/OP-TASK-092"], cwd=project_a.backend).stdout
    assert "feat/OP-TASK-092" in branch_list, "기존 브랜치가 훼손됨"


# ═════════════════════════════════════════════════════════════════════════════
# S-28: 슬롯 없이 remove/status 호출 시 예외로 죽지 않음 (H-21)
# ═════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("command", ["remove", "status"])
def test_s28_remove_and_status_without_meta_report_meta_not_found(project_a: ProjectA, command):
    """[T092/L2-F2f] S-28 ① — 슬롯을 만든 적 없는 프로젝트에서 remove/status 호출 시
    META_NOT_FOUND로 명확히 보고하고 예외(트레이스백)로 죽지 않는다."""
    result = run_worktree_cli(
        [command, "--project-root", str(project_a.root), "--task", "999"]
    )
    payload = parse_json_stdout(result, f"{command}(S-28①)")
    assert payload.get("ok") is False
    assert payload.get("error") == "META_NOT_FOUND"
    assert "Traceback" not in result.stderr, f"{command}가 예외로 죽음: {result.stderr}"


def test_s28_remove_twice_is_reported_cleanly_after_success(tmp_path):
    """[T092/L2-F2f] S-28 ② — `remove` 성공 직후 같은 명령을 재실행해도 META_NOT_FOUND로
    명확히 보고하고 죽지 않는다(CLOSE 경로에서 no-op 비차단과 동일 패턴)."""
    g = build_guard_repo(tmp_path, "clean", name_suffix="_s28")
    r1 = run_worktree_cli(
        ["remove", "--project-root", str(g.project_root), "--task", g.task]
    )
    p1 = parse_json_stdout(r1, "remove(S-28② 1회차)")
    assert p1.get("ok") is True

    r2 = run_worktree_cli(
        ["remove", "--project-root", str(g.project_root), "--task", g.task]
    )
    p2 = parse_json_stdout(r2, "remove(S-28② 2회차)")
    assert p2.get("ok") is False
    assert p2.get("error") == "META_NOT_FOUND"
    assert "Traceback" not in r2.stderr, f"2회차 remove가 예외로 죽음: {r2.stderr}"


# ═════════════════════════════════════════════════════════════════════════════
# S-29: remove 후 빈 슬롯 껍데기가 재생성을 영구 차단한다 (H-22, 회귀 — revup 실측)
#
# PM이 revup 실환경에서 실측한 결함: `remove` 성공 후 `.opal-worktrees/task_{NNN}/`
# 슬롯 루트(레포별 worktree 디렉토리의 상위 디렉토리)가 회수되지 않고 빈 껍데기로
# 남는다. `list`는 `.meta/task_{NNN}.json`이 삭제되었으므로 슬롯이 없다고 답하지만,
# `create`의 pre-flight는 `wt_root.exists()`만 보므로 빈 껍데기를 "이미 존재"로 오판해
# `WORKTREE_EXISTS`로 거부한다 — `list`와 `create`의 슬롯 존재 판정이 어긋난다.
#
# 기존 S-9(`test_s9_remove_succeeds_when_all_guards_clear_and_keeps_branch`)는
# 레포별 경로(`g.wt_path`)만 보고 슬롯 루트(`task_{NNN}/`)는 보지 않아 이 결함을
# 놓쳤다. 기존 S-27(`test_s27_duplicate_create_rejected_and_existing_slot_untouched`)는
# 살아 있는 슬롯으로만 시험해 "제거된 슬롯 재생성" 경로를 밟지 않았다.
# ═════════════════════════════════════════════════════════════════════════════


def test_s29_1a_remove_clears_slot_root_for_single_repo(tmp_path):
    """[T092/L2-F8g] S-29 계약1 — 레포 1개(단일 entry) clean 상태에서 remove 성공 후,
    레포별 worktree 경로뿐 아니라 슬롯 루트(`.opal-worktrees/task_{NNN}/`) 자체가
    남지 않아야 한다."""
    g = build_guard_repo(tmp_path, "clean", name_suffix="_s29_1a")
    result = run_worktree_cli(
        ["remove", "--project-root", str(g.project_root), "--task", g.task]
    )
    payload = parse_json_stdout(result, "remove(S-29 계약1a)")
    assert payload.get("ok") is True, f"remove 실패: {payload}"
    assert not g.wt_path.exists(), "레포별 worktree 경로가 잔존"

    slot_root = g.project_root / ".opal-worktrees" / f"task_{g.task}"
    assert not slot_root.exists(), (
        f"remove 성공 후 슬롯 루트({slot_root})가 잔존한다 — 빈 껍데기 결함(H-22): "
        f"{list(slot_root.rglob('*')) if slot_root.exists() else []}"
    )


def test_s29_1b_remove_clears_slot_root_for_multi_repo(project_a: ProjectA):
    """[T092/L2-F8g] S-29 계약1 — 유형 A(레포 2개) 전부 회수한 뒤에도 슬롯 루트가
    남지 않아야 한다(H-5 3중 가드를 모두 해소한 정상 경로)."""
    r = run_worktree_cli(
        ["create", "--project-root", str(project_a.root), "--task", "092"]
    )
    p = parse_json_stdout(r, "create(S-29 계약1b)")
    assert p.get("ok") is True, f"create 실패: {p}"

    wt_root = project_a.root / ".opal-worktrees" / "task_092"
    branch = "feat/OP-TASK-092"
    for repo, name in ((project_a.backend, "backend"), (project_a.frontend, "frontend")):
        wt_path = wt_root / "workspace" / name
        run_git(["push", "-u", "origin", branch], cwd=wt_path)
        run_git(["merge", branch], cwd=repo)

    result = run_worktree_cli(
        ["remove", "--project-root", str(project_a.root), "--task", "092"]
    )
    payload = parse_json_stdout(result, "remove(S-29 계약1b)")
    assert payload.get("ok") is True, f"remove 실패: {payload}"

    assert not wt_root.exists(), (
        f"레포 2개 전부 회수 후에도 슬롯 루트({wt_root})가 잔존한다 — 빈 껍데기 결함(H-22): "
        f"{list(wt_root.rglob('*')) if wt_root.exists() else []}"
    )


def test_s29_2_recreate_after_remove_succeeds(tmp_path):
    """[T092/L2-F8g] S-29 계약2 — clean 상태에서 remove 성공 후, 동일 태스크 번호로
    create를 재실행하면 성공해야 한다(WORKTREE_EXISTS/BRANCH_EXISTS로 막히면 안 된다).

    [설계 공백 — 임의로 정하지 않음] `remove`는 브랜치를 삭제하지 않는다(S-9, user
    sovereignty 결정). 따라서 재생성 시 "같은 브랜치를 재사용할지" 정책이 PLAN/TASK
    어디에도 명시돼 있지 않다. 이 테스트가 실패하면 원인이 (a) 슬롯 루트 잔존으로 인한
    WORKTREE_EXISTS인지 (b) 잔존 브랜치로 인한 BRANCH_EXISTS인지 구분해서 보고해야 한다
    — (a)는 이번 계약 위반(H-22)이고 (b)는 별도의 설계 결정이 필요한 블로커다."""
    g = build_guard_repo(tmp_path, "clean", name_suffix="_s29_2")
    r_remove = run_worktree_cli(
        ["remove", "--project-root", str(g.project_root), "--task", g.task]
    )
    p_remove = parse_json_stdout(r_remove, "remove(S-29 계약2)")
    assert p_remove.get("ok") is True, f"remove 실패: {p_remove}"

    r_recreate = run_worktree_cli(
        ["create", "--project-root", str(g.project_root), "--task", g.task]
    )
    p_recreate = parse_json_stdout(r_recreate, "create(S-29 계약2 재생성)")
    assert p_recreate.get("ok") is True, (
        f"remove 후 같은 번호로 재생성이 실패한다(H-22 결함 또는 브랜치 재사용 설계 공백): "
        f"{p_recreate}"
    )
    assert p_recreate.get("error") not in ("WORKTREE_EXISTS", "BRANCH_EXISTS"), (
        f"재생성이 WORKTREE_EXISTS/BRANCH_EXISTS로 막힌다: {p_recreate}"
    )


def test_s29_3_list_and_create_agree_on_slot_existence(project_a: ProjectA):
    """[T092/L2-F8g] S-29 계약3 — `list`가 해당 태스크 슬롯을 반환하지 않는 상태에서
    `create`가 `WORKTREE_EXISTS`를 반환해서는 안 된다. `list`는 `.meta/*.json` 존재
    여부로, `create`의 pre-flight는 `wt_root.exists()`로 슬롯 유무를 각각 독립적으로
    판정하고 있어 remove 이후 두 판정이 어긋난다(H-22)."""
    r_create = run_worktree_cli(
        ["create", "--project-root", str(project_a.root), "--task", "092"]
    )
    p_create = parse_json_stdout(r_create, "create(S-29 계약3 최초생성)")
    assert p_create.get("ok") is True, f"최초 create 실패: {p_create}"

    branch = "feat/OP-TASK-092"
    for repo, name in ((project_a.backend, "backend"), (project_a.frontend, "frontend")):
        wt_path = project_a.root / ".opal-worktrees" / "task_092" / "workspace" / name
        run_git(["push", "-u", "origin", branch], cwd=wt_path)
        run_git(["merge", branch], cwd=repo)

    r_remove = run_worktree_cli(
        ["remove", "--project-root", str(project_a.root), "--task", "092"]
    )
    p_remove = parse_json_stdout(r_remove, "remove(S-29 계약3)")
    assert p_remove.get("ok") is True, f"remove 실패: {p_remove}"

    r_list = run_worktree_cli(["list", "--project-root", str(project_a.root)])
    p_list = parse_json_stdout(r_list, "list(S-29 계약3)")
    assert p_list.get("ok") is True, f"list 실패: {p_list}"
    task_092_entries = [e for e in p_list.get("entries", []) if e.get("task") == "092"]
    assert task_092_entries == [], f"remove 후에도 list가 슬롯을 반환한다: {p_list}"

    r_recreate = run_worktree_cli(
        ["create", "--project-root", str(project_a.root), "--task", "092"]
    )
    p_recreate = parse_json_stdout(r_recreate, "create(S-29 계약3 재생성)")
    assert p_recreate.get("error") != "WORKTREE_EXISTS", (
        f"list는 슬롯 없음(entries=[])이라 답하는데 create는 WORKTREE_EXISTS로 거부한다 — "
        f"list/create 판정 불일치(H-22): {p_recreate}"
    )


def test_s29_4_empty_shell_slot_root_does_not_permanently_block_recreate(project_a: ProjectA):
    """[T092/L2-F8g] S-29 계약4 — 슬롯 루트에 빈 디렉토리만 남아 있는 상태(부분 잔여 —
    메타 파일은 삭제됐지만 디렉토리 트리는 남은 remove 이후 상태를 fixture로 직접
    조성)에서 create를 호출하면, 성공하거나 최소한 `WORKTREE_EXISTS`가 아닌 진단
    가능한 다른 코드를 반환해야 한다. 어느 쪽(성공/특정 코드)이 맞는지는 설계 판단이
    필요하므로, 이 테스트는 "빈 껍데기가 재생성을 영구 차단하지 않는다"만 단언한다."""
    slot_root = project_a.root / ".opal-worktrees" / "task_092"
    (slot_root / "workspace" / "backend").mkdir(parents=True)
    (slot_root / "workspace" / "frontend").mkdir(parents=True)
    # 메타 파일(.opal-worktrees/.meta/task_092.json)은 의도적으로 만들지 않는다 —
    # remove가 메타는 지웠지만 슬롯 루트 디렉토리 트리는 못 지운 실측 잔여 상태를 재현.

    result = run_worktree_cli(
        ["create", "--project-root", str(project_a.root), "--task", "092"]
    )
    payload = parse_json_stdout(result, "create(S-29 계약4)")
    assert payload.get("error") != "WORKTREE_EXISTS", (
        f"빈 껍데기 슬롯 루트가 WORKTREE_EXISTS로 영구 차단한다 — 진단 불가능한 결함(H-22): "
        f"{payload}"
    )


# ═════════════════════════════════════════════════════════════════════════════
# S-30: `worktree-tool init` 신설 — 탐지 기반 초안 생성 (H-23, DEC-8, ADD-1)
#
# 미구현이므로(RED 규율) 전부 실패가 정상이다. init은 `code-scan init`처럼 비대화형
# 탐지 초안 생성이며, 자동 생성이 아니다 — 규칙은 DEC-8 "탐지 규칙"·"setup[] 탐지"·
# "추측하지 않는 것"·"멱등·안전" 4절에 전부 있다(PLAN.md §1.4 DEC-8).
# ═════════════════════════════════════════════════════════════════════════════


def test_s30_1_multi_repo_layout_detected_with_sorted_repos(tmp_path):
    """[T092/L2-ADD1] S-30 계약1 — 유형 A: `workspace/` 하위 독립 `.git` 2개(backend,
    frontend)가 있으면 init은 `layout: "multi-repo"` + `repos`에 발견된 2경로를 프로젝트
    루트 상대·정렬된 형태로 채운다(DEC-8 탐지 규칙 2~3단계, revup 실측과 동형 — revup
    root 자체도 `.git`을 갖는 컨테이너 레포다: PLAN D-5 `.gitignore:2 workspace/`)."""
    remotes_dir = tmp_path / "_remotes_s30_1"
    remotes_dir.mkdir()
    project_root = tmp_path / "proj_s30_1"
    project_root.mkdir()
    run_git(["init", "-b", "main"], cwd=project_root)
    # 정렬 검증을 위해 알파벳 역순으로 생성한다(zzz 먼저, aaa 나중).
    _build_independent_repo(remotes_dir, project_root, "workspace", "zzz_frontend")
    _build_independent_repo(remotes_dir, project_root, "workspace", "aaa_backend")

    result = run_worktree_cli(["init", "--project-root", str(project_root)])
    payload = parse_json_stdout(result, "init(S-30 계약1)")
    assert payload.get("ok") is True, f"multi-repo 탐지 init 실패: {payload}"

    config_path = project_root / ".opal" / "worktree.json"
    assert config_path.exists(), "init이 .opal/worktree.json을 생성하지 않음"
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    assert cfg.get("layout") == "multi-repo"
    assert cfg.get("repos") == ["workspace/aaa_backend", "workspace/zzz_frontend"], (
        f"repos가 프로젝트 루트 상대·정렬된 2경로여야 한다: {cfg.get('repos')}"
    )


def test_s30_2_monorepo_layout_detected_with_top_level_manifest_dir(tmp_path):
    """[T092/L2-ADD1] S-30 계약2 — 유형 B: 독립 `.git` 0개 + 루트 레포가 `workspace/**`를
    추적하고 `workspace/backend/pyproject.toml`이 존재하면 init은 `layout: "monorepo"` +
    `repos == ["workspace"]`를 반환한다(DEC-8 탐지 규칙 4단계, mams 실측과 동형 — `tasks/`·
    `.opal/`은 manifest가 없어 후보에서 자연 배제된다)."""
    remotes_dir = tmp_path / "_remotes_s30_2"
    remotes_dir.mkdir()
    origin = make_monorepo_bare_remote(remotes_dir, "origin_s30_2")
    project_root = clone_repo(origin, tmp_path, "proj_s30_2")
    (project_root / "workspace" / "backend" / "pyproject.toml").write_text(
        '[project]\nname = "mams-backend"\n', encoding="utf-8"
    )

    result = run_worktree_cli(["init", "--project-root", str(project_root)])
    payload = parse_json_stdout(result, "init(S-30 계약2)")
    assert payload.get("ok") is True, f"monorepo 탐지 init 실패: {payload}"

    cfg = json.loads((project_root / ".opal" / "worktree.json").read_text(encoding="utf-8"))
    assert cfg.get("layout") == "monorepo"
    assert cfg.get("repos") == ["workspace"], (
        f"mams 실측과 동형으로 최상위 단일 dir이어야 한다: {cfg.get('repos')}"
    )


def test_s30_3_setup_lock_file_mapping_and_gradle_maven_excluded(tmp_path):
    """[T092/L2-ADD1] S-30 계약3 — lock 파일 기반 `setup[]` 매핑: `uv.lock`→`uv sync`,
    `pnpm-lock.yaml`→`pnpm install`, `bun.lock`→`bun install`이 각각 해당 `cwd`와 함께
    생성되고, `build.gradle`만 있는 디렉토리는 setup 항목이 생성되지 않는다(DEC-8
    `setup[]` 탐지표)."""
    remotes_dir = tmp_path / "_remotes_s30_3"
    remotes_dir.mkdir()
    project_root = tmp_path / "proj_s30_3"
    project_root.mkdir()
    run_git(["init", "-b", "main"], cwd=project_root)

    _build_independent_repo(remotes_dir, project_root, "workspace", "svc_uv", {"uv.lock": ""})
    _build_independent_repo(
        remotes_dir, project_root, "workspace", "svc_pnpm", {"pnpm-lock.yaml": ""}
    )
    _build_independent_repo(remotes_dir, project_root, "workspace", "svc_bun", {"bun.lock": ""})
    _build_independent_repo(
        remotes_dir, project_root, "workspace", "svc_gradle", {"build.gradle": ""}
    )

    result = run_worktree_cli(["init", "--project-root", str(project_root)])
    payload = parse_json_stdout(result, "init(S-30 계약3)")
    assert payload.get("ok") is True, f"init 실패: {payload}"

    cfg = json.loads((project_root / ".opal" / "worktree.json").read_text(encoding="utf-8"))
    setup = cfg.get("setup", [])
    by_cwd = {item.get("cwd"): item.get("run") for item in setup}

    assert by_cwd.get("workspace/svc_uv") == "uv sync", f"uv.lock 매핑 불일치: {setup}"
    assert by_cwd.get("workspace/svc_pnpm") == "pnpm install", f"pnpm-lock.yaml 매핑 불일치: {setup}"
    assert by_cwd.get("workspace/svc_bun") == "bun install", f"bun.lock 매핑 불일치: {setup}"
    assert "workspace/svc_gradle" not in by_cwd, (
        f"gradle만 있는 디렉토리는 setup 항목을 생성하면 안 된다(빌드 시 자동 해석): {setup}"
    )


def test_s30_4_generated_draft_never_guesses_copy_port_offset_branch_template(tmp_path):
    """[T092/L2-ADD1] S-30 계약4 — 생성물의 `copy`는 빈 배열, `portOffset`은 `0`,
    `branchTemplate`은 `"feat/OP-TASK-{NNN}"`이어야 한다(DEC-8 "추측하지 않는 것" —
    로컬 설정·포트 실태·브랜치 규칙을 도구가 임의로 채우지 않는다)."""
    remotes_dir = tmp_path / "_remotes_s30_4"
    remotes_dir.mkdir()
    project_root = tmp_path / "proj_s30_4"
    project_root.mkdir()
    run_git(["init", "-b", "main"], cwd=project_root)
    _build_independent_repo(remotes_dir, project_root, "workspace", "backend")
    _build_independent_repo(remotes_dir, project_root, "workspace", "frontend")

    result = run_worktree_cli(["init", "--project-root", str(project_root)])
    payload = parse_json_stdout(result, "init(S-30 계약4)")
    assert payload.get("ok") is True, f"init 실패: {payload}"

    cfg = json.loads((project_root / ".opal" / "worktree.json").read_text(encoding="utf-8"))
    assert cfg.get("copy") == [], f"copy는 추측 금지 — 빈 배열이어야 한다: {cfg.get('copy')}"
    assert cfg.get("portOffset") == 0, f"portOffset은 추측 금지 — 0이어야 한다: {cfg.get('portOffset')}"
    assert cfg.get("branchTemplate") == "feat/OP-TASK-{NNN}", (
        f"branchTemplate 기본값이 DEC-1(C-4)과 달라야 한다: {cfg.get('branchTemplate')}"
    )


def test_s30_5_existing_config_rejected_with_config_exists_and_file_untouched(project_a: ProjectA):
    """[T092/L2-ADD1] S-30 계약5a — 이미 `.opal/worktree.json`이 있으면(project_a fixture가
    사전 생성) `--force` 없이 init을 실행하면 `CONFIG_EXISTS`로 거부하고 파일 내용은
    sha256 기준으로 완전히 불변이어야 한다(DEC-8 "멱등·안전")."""
    before_sha = hashlib.sha256(project_a.config_path.read_bytes()).hexdigest()

    result = run_worktree_cli(["init", "--project-root", str(project_a.root)])
    payload = parse_json_stdout(result, "init(S-30 계약5a CONFIG_EXISTS)")
    assert payload.get("ok") is False
    assert payload.get("error") == "CONFIG_EXISTS"

    after_sha = hashlib.sha256(project_a.config_path.read_bytes()).hexdigest()
    assert before_sha == after_sha, "CONFIG_EXISTS 거부 시 기존 파일 내용이 바뀌면 안 된다"


def test_s30_6_force_flag_overwrites_existing_config(project_a: ProjectA):
    """[T092/L2-ADD1] S-30 계약5b — `--force`를 주면 기존 설정을 실제로 덮어써야 한다.
    우연한 내용 일치로 거짓 통과하지 않도록, fixture 기본값과 다른 내용(bogus monorepo)을
    먼저 덮어써 둔 뒤 `--force` init을 실행해 실제 탐지 결과(multi-repo)로 갱신됨을
    확인한다."""
    write_json(project_a.config_path, {"layout": "monorepo", "repos": ["bogus"]})
    stale_sha = hashlib.sha256(project_a.config_path.read_bytes()).hexdigest()

    result = run_worktree_cli(
        ["init", "--project-root", str(project_a.root), "--force"]
    )
    payload = parse_json_stdout(result, "init(S-30 계약5b --force)")
    assert payload.get("ok") is True, f"--force는 성공해야 한다: {payload}"

    after_sha = hashlib.sha256(project_a.config_path.read_bytes()).hexdigest()
    assert after_sha != stale_sha, "--force는 파일을 실제로 덮어써야 한다"

    cfg = json.loads(project_a.config_path.read_text(encoding="utf-8"))
    assert cfg.get("layout") == "multi-repo", (
        f"--force 이후에는 bogus 값이 아니라 실제 탐지 결과(multi-repo)로 갱신돼야 한다: {cfg}"
    )


def test_s30_7_dry_run_does_not_write_file_but_returns_draft_json(tmp_path):
    """[T092/L2-ADD1] S-30 계약6 — `--dry-run`은 파일을 쓰지 않고(`.opal/worktree.json`
    미생성) 초안을 stdout JSON으로만 반환해야 한다(DEC-8 "멱등·안전").

    [설계 공백 — 임의로 정하지 않음] DEC-8은 dry-run 응답의 정확한 JSON 키 이름까지는
    규정하지 않는다. 이 테스트는 응답이 최상위이든 `draft` 키 아래든 탐지된 layout/repos를
    포함하기만 하면 통과하도록 관대하게 작성했다 — 구현이 키 이름을 다르게 고르면 이
    지점만 조정하면 된다."""
    remotes_dir = tmp_path / "_remotes_s30_7"
    remotes_dir.mkdir()
    project_root = tmp_path / "proj_s30_7"
    project_root.mkdir()
    run_git(["init", "-b", "main"], cwd=project_root)
    _build_independent_repo(remotes_dir, project_root, "workspace", "backend")
    _build_independent_repo(remotes_dir, project_root, "workspace", "frontend")

    config_path = project_root / ".opal" / "worktree.json"
    result = run_worktree_cli(
        ["init", "--project-root", str(project_root), "--dry-run"]
    )
    payload = parse_json_stdout(result, "init(S-30 계약6 --dry-run)")
    assert payload.get("ok") is True, f"--dry-run도 성공 응답이어야 한다: {payload}"
    assert not config_path.exists(), "--dry-run은 .opal/worktree.json을 쓰면 안 된다"

    draft = payload.get("draft")
    draft = draft if isinstance(draft, dict) else payload
    assert draft.get("layout") == "multi-repo", (
        f"--dry-run 응답에 탐지된 초안(layout 포함)이 있어야 한다: {payload}"
    )
    assert draft.get("repos") == ["workspace/backend", "workspace/frontend"], (
        f"--dry-run 응답의 repos가 탐지 결과와 일치해야 한다: {payload}"
    )


def test_s30_8_non_git_root_rejected_with_not_a_git_repo(tmp_path):
    """[T092/L2-ADD1] S-30 계약7a — 프로젝트 루트가 git 레포가 아니면(어디에도 `.git`
    없음) `NOT_A_GIT_REPO`로 거부하고 파일을 생성하지 않는다(DEC-8 탐지 규칙 1단계)."""
    project_root = tmp_path / "proj_s30_8_not_git"
    project_root.mkdir()

    result = run_worktree_cli(["init", "--project-root", str(project_root)])
    payload = parse_json_stdout(result, "init(S-30 계약7a NOT_A_GIT_REPO)")
    assert payload.get("ok") is False
    assert payload.get("error") == "NOT_A_GIT_REPO"
    assert not (project_root / ".opal" / "worktree.json").exists(), (
        "거부 시 파일을 생성하면 안 된다"
    )


def test_s30_9_monorepo_without_manifest_rejected_with_layout_undetermined(tmp_path):
    """[T092/L2-ADD1] S-30 계약7b — 독립 `.git`이 0개(monorepo 후보)인데 어떤 최상위
    디렉토리도 코드 manifest를 갖지 않으면 `LAYOUT_UNDETERMINED`로 거부하고 추측 생성하지
    않는다(DEC-8 탐지 규칙 5단계 "추측 금지"). `workspace/backend`·`workspace/frontend`에
    `app.py`/`app.js`만 있고 manifest 파일(`package.json`/`pyproject.toml`/... )은 없다."""
    remotes_dir = tmp_path / "_remotes_s30_9"
    remotes_dir.mkdir()
    origin = make_monorepo_bare_remote(remotes_dir, "origin_s30_9")
    project_root = clone_repo(origin, tmp_path, "proj_s30_9")

    result = run_worktree_cli(["init", "--project-root", str(project_root)])
    payload = parse_json_stdout(result, "init(S-30 계약7b LAYOUT_UNDETERMINED)")
    assert payload.get("ok") is False
    assert payload.get("error") == "LAYOUT_UNDETERMINED", (
        f"manifest 없는 monorepo 후보는 추측 생성 없이 거부해야 한다: {payload}"
    )
    assert not (project_root / ".opal" / "worktree.json").exists(), (
        "LAYOUT_UNDETERMINED 거부 시 파일을 생성하면 안 된다"
    )


def test_s30_10_generated_config_passes_validation_and_create_succeeds(tmp_path):
    """[T092/L2-ADD1] S-30 계약8 — 관통 검증: init으로 만든 파일이 기존
    `validate_worktree_config()`(list 경로로 확인)를 통과하고, 이어서 `create`가 성공해야
    한다. 초안이 문법만 맞고 실제로 못 쓰면 의미가 없다(DEC-8 결론부)."""
    remotes_dir = tmp_path / "_remotes_s30_10"
    remotes_dir.mkdir()
    project_root = tmp_path / "proj_s30_10"
    project_root.mkdir()
    run_git(["init", "-b", "main"], cwd=project_root)
    _build_independent_repo(remotes_dir, project_root, "workspace", "backend")
    _build_independent_repo(remotes_dir, project_root, "workspace", "frontend")

    r_init = run_worktree_cli(["init", "--project-root", str(project_root)])
    p_init = parse_json_stdout(r_init, "init(S-30 계약8)")
    assert p_init.get("ok") is True, f"init 실패: {p_init}"

    r_list = run_worktree_cli(["list", "--project-root", str(project_root)])
    p_list = parse_json_stdout(r_list, "list(S-30 계약8 검증관통)")
    assert p_list.get("ok") is True, (
        f"init 생성물이 validate_worktree_config()를 통과해야 한다(list 경로로 확인): {p_list}"
    )

    r_create = run_worktree_cli(
        ["create", "--project-root", str(project_root), "--task", "092"]
    )
    p_create = parse_json_stdout(r_create, "create(S-30 계약8 검증관통)")
    assert p_create.get("ok") is True, (
        f"init 생성물로 곧바로 create가 성공해야 한다(관통 검증 — 초안이 문법만 맞고 "
        f"실제로 못 쓰면 의미 없다): {p_create}"
    )


# ═════════════════════════════════════════════════════════════════════════════
# S-31: `worktree-tool init`의 `setup[]`/`_copy_candidates` 탐지가 monorepo에서
# repos 바로 아래(depth 1)만 보는 결함 (H-24, mams 실환경 실측)
#
# mams(monorepo, repos=["workspace"])는 workspace/backend/uv.lock,
# workspace/frontend/pnpm-lock.yaml처럼 repos 경로보다 한 단계 더 깊은 곳에 lock
# 파일이 있다. 현재 `_detect_setup()`(worktree_tool.py:472-481)과
# `_detect_copy_candidates()`(:484-)는 `repo_dir / lock_name`만 검사(비재귀)하므로
# 전부 놓친다 — setup: [] 로 생성돼 lazy setup(C-7)이 무의미해진다.
# RED 규율(작성자≠구현자) — worktree_tool.py를 고치지 않는다. 아래는 전부 실패가
# 정상이다(현재 구현이 depth 1만 보므로).
# ═════════════════════════════════════════════════════════════════════════════


def test_s31_1_monorepo_deep_lock_files_detected_at_actual_directories(tmp_path):
    """[T092/L2-ADD1b] S-31 계약1 — mams 실측 구조 재현: `layout: "monorepo"` +
    `repos == ["workspace"]`인 프로젝트에서 `workspace/backend/uv.lock`,
    `workspace/frontend/pnpm-lock.yaml`처럼 repos 자신보다 한 단계 더 깊은 lock
    파일도 `setup[]`에 반영돼야 하고, 각 항목의 `cwd`는 lock 파일이 실제로 있는
    디렉토리(`workspace/backend`, `workspace/frontend`)여야 한다 — `workspace`
    자신이 아니다(현재 구현은 repos 최상위만 보므로 RED 예상)."""
    remotes_dir = tmp_path / "_remotes_s31_1"
    remotes_dir.mkdir()
    origin = make_monorepo_bare_remote(remotes_dir, "origin_s31_1")
    project_root = clone_repo(origin, tmp_path, "proj_s31_1")
    (project_root / "workspace" / "backend" / "pyproject.toml").write_text(
        '[project]\nname = "mams-backend"\n', encoding="utf-8"
    )
    (project_root / "workspace" / "backend" / "uv.lock").write_text("", encoding="utf-8")
    (project_root / "workspace" / "frontend" / "package.json").write_text(
        '{"name": "mams-frontend"}\n', encoding="utf-8"
    )
    (project_root / "workspace" / "frontend" / "pnpm-lock.yaml").write_text(
        "", encoding="utf-8"
    )

    result = run_worktree_cli(["init", "--project-root", str(project_root)])
    payload = parse_json_stdout(result, "init(S-31 계약1)")
    assert payload.get("ok") is True, f"init 실패: {payload}"

    cfg = json.loads((project_root / ".opal" / "worktree.json").read_text(encoding="utf-8"))
    assert cfg.get("layout") == "monorepo"
    assert cfg.get("repos") == ["workspace"]

    setup = cfg.get("setup", [])
    by_cwd = {item.get("cwd"): item.get("run") for item in setup}
    assert by_cwd.get("workspace/backend") == "uv sync", (
        f"repos(['workspace']) 바로 아래가 아니라 한 단계 더 깊은 workspace/backend의 "
        f"uv.lock도 탐지돼야 한다(mams 실측 결함): {setup}"
    )
    assert by_cwd.get("workspace/frontend") == "pnpm install", (
        f"workspace/frontend의 pnpm-lock.yaml도 탐지돼야 한다: {setup}"
    )
    assert "workspace" not in by_cwd, (
        f"cwd는 lock 파일이 실제 있는 디렉토리여야 한다 — repos 자체(workspace)가 "
        f"아니다: {setup}"
    )


def test_s31_2_multi_repo_shallow_lock_detection_unchanged(tmp_path):
    """[T092/L2-ADD1b] S-31 계약2 — 회귀 불변: repos 바로 아래(depth 0, 기존 동작)에
    lock 파일이 있는 multi-repo 기존 케이스는 깊은 탐지가 추가돼도 그대로 동작해야
    한다 — `cwd`는 여전히 repos 경로 자신(`workspace/svc_uv`)이다(test_s30_3과
    동형이나 S-31 회귀 계약으로 명시)."""
    remotes_dir = tmp_path / "_remotes_s31_2"
    remotes_dir.mkdir()
    project_root = tmp_path / "proj_s31_2"
    project_root.mkdir()
    run_git(["init", "-b", "main"], cwd=project_root)

    _build_independent_repo(
        remotes_dir, project_root, "workspace", "svc_uv", {"uv.lock": ""}
    )
    _build_independent_repo(
        remotes_dir, project_root, "workspace", "svc_pnpm", {"pnpm-lock.yaml": ""}
    )

    result = run_worktree_cli(["init", "--project-root", str(project_root)])
    payload = parse_json_stdout(result, "init(S-31 계약2)")
    assert payload.get("ok") is True, f"init 실패: {payload}"

    cfg = json.loads((project_root / ".opal" / "worktree.json").read_text(encoding="utf-8"))
    setup = cfg.get("setup", [])
    by_cwd = {item.get("cwd"): item.get("run") for item in setup}
    assert by_cwd.get("workspace/svc_uv") == "uv sync", (
        f"repos 바로 아래 lock 탐지(기존 동작)가 회귀되면 안 된다: {setup}"
    )
    assert by_cwd.get("workspace/svc_pnpm") == "pnpm install", (
        f"repos 바로 아래 lock 탐지(기존 동작)가 회귀되면 안 된다: {setup}"
    )


def test_s31_3_deep_search_excludes_build_artifact_directories(tmp_path):
    """[T092/L2-ADD1b] S-31 계약3 — 깊이 경계: monorepo 깊은 탐지는 무한 재귀를 해서는
    안 되고, `node_modules` 같은 빌드 산출물 디렉토리 안의 lock 파일을 주워오면 안
    된다. `workspace/frontend/pnpm-lock.yaml`(정상 2단계)은 탐지되어야 하지만,
    `workspace/frontend/node_modules/some-pkg/package-lock.json`(빌드 산출물 내부)은
    탐지되면 안 된다."""
    remotes_dir = tmp_path / "_remotes_s31_3"
    remotes_dir.mkdir()
    origin = make_monorepo_bare_remote(remotes_dir, "origin_s31_3")
    project_root = clone_repo(origin, tmp_path, "proj_s31_3")
    (project_root / "workspace" / "backend" / "pyproject.toml").write_text(
        '[project]\nname = "mams-backend"\n', encoding="utf-8"
    )
    (project_root / "workspace" / "frontend" / "package.json").write_text(
        '{"name": "mams-frontend"}\n', encoding="utf-8"
    )
    (project_root / "workspace" / "frontend" / "pnpm-lock.yaml").write_text(
        "", encoding="utf-8"
    )
    nested_pkg = (
        project_root
        / "workspace"
        / "frontend"
        / "node_modules"
        / "some-pkg"
        / "package-lock.json"
    )
    nested_pkg.parent.mkdir(parents=True, exist_ok=True)
    nested_pkg.write_text("{}", encoding="utf-8")

    result = run_worktree_cli(["init", "--project-root", str(project_root)])
    payload = parse_json_stdout(result, "init(S-31 계약3)")
    assert payload.get("ok") is True, f"init 실패: {payload}"

    cfg = json.loads((project_root / ".opal" / "worktree.json").read_text(encoding="utf-8"))
    setup = cfg.get("setup", [])
    by_cwd = {item.get("cwd"): item.get("run") for item in setup}
    assert by_cwd.get("workspace/frontend") == "pnpm install", (
        f"정상 2단계 깊이의 pnpm-lock.yaml은 탐지되어야 한다: {setup}"
    )
    assert not any(
        "node_modules" in (item.get("cwd") or "") for item in setup
    ), f"node_modules 같은 빌드 산출물 디렉토리 내부 lock을 주워오면 안 된다: {setup}"


def test_s31_4_duplicate_lock_kinds_in_same_dir_yield_single_entry(tmp_path):
    """[T092/L2-ADD1b] S-31 계약4 — 중복 방지: 같은 디렉토리(`workspace/backend`)에
    `uv.lock`과 `package-lock.json`이 둘 다 있으면 setup 항목은 우선순위 첫 매칭
    (`_LOCK_FILE_SETUP_MAP` 순서상 `uv.lock`→`uv sync`) 1건만 생성돼야 한다. 서로
    다른 디렉토리(`workspace/frontend`)는 별개로 1건 생성된다."""
    remotes_dir = tmp_path / "_remotes_s31_4"
    remotes_dir.mkdir()
    origin = make_monorepo_bare_remote(remotes_dir, "origin_s31_4")
    project_root = clone_repo(origin, tmp_path, "proj_s31_4")
    (project_root / "workspace" / "backend" / "pyproject.toml").write_text(
        '[project]\nname = "mams-backend"\n', encoding="utf-8"
    )
    (project_root / "workspace" / "backend" / "uv.lock").write_text("", encoding="utf-8")
    (project_root / "workspace" / "backend" / "package-lock.json").write_text(
        "{}", encoding="utf-8"
    )
    (project_root / "workspace" / "frontend" / "package.json").write_text(
        '{"name": "mams-frontend"}\n', encoding="utf-8"
    )
    (project_root / "workspace" / "frontend" / "pnpm-lock.yaml").write_text(
        "", encoding="utf-8"
    )

    result = run_worktree_cli(["init", "--project-root", str(project_root)])
    payload = parse_json_stdout(result, "init(S-31 계약4)")
    assert payload.get("ok") is True, f"init 실패: {payload}"

    cfg = json.loads((project_root / ".opal" / "worktree.json").read_text(encoding="utf-8"))
    setup = cfg.get("setup", [])
    backend_entries = [item for item in setup if item.get("cwd") == "workspace/backend"]
    assert len(backend_entries) == 1, (
        f"같은 디렉토리에 lock 2종이 있어도 setup 항목은 1건이어야 한다: {setup}"
    )
    assert backend_entries[0].get("run") == "uv sync", (
        f"우선순위 첫 매칭(uv.lock→uv sync)이 채택돼야 한다: {setup}"
    )
    frontend_entries = [
        item for item in setup if item.get("cwd") == "workspace/frontend"
    ]
    assert len(frontend_entries) == 1, (
        f"다른 디렉토리는 별개로 1건씩 생성돼야 한다: {setup}"
    )
    assert frontend_entries[0].get("run") == "pnpm install"


def test_s31_5_copy_candidates_detected_at_same_deeper_level(tmp_path):
    """[T092/L2-ADD1b] S-31 계약5 — `_copy_candidates`도 `setup[]`과 동일한 깊이까지
    탐지해야 한다: `workspace/backend/settings.local.yaml`처럼 repos 자신보다 한 단계
    더 깊은 후보도 참고용 목록에 제시돼야 한다(copy[]에는 여전히 자동 반영되지
    않는다 — DEC-8 '추측하지 않는 것')."""
    remotes_dir = tmp_path / "_remotes_s31_5"
    remotes_dir.mkdir()
    origin = make_monorepo_bare_remote(remotes_dir, "origin_s31_5")
    project_root = clone_repo(origin, tmp_path, "proj_s31_5")
    (project_root / "workspace" / "backend" / "pyproject.toml").write_text(
        '[project]\nname = "mams-backend"\n', encoding="utf-8"
    )
    (project_root / "workspace" / "backend" / "settings.local.yaml").write_text(
        "db: local\n", encoding="utf-8"
    )

    result = run_worktree_cli(["init", "--project-root", str(project_root)])
    payload = parse_json_stdout(result, "init(S-31 계약5)")
    assert payload.get("ok") is True, f"init 실패: {payload}"

    cfg = json.loads((project_root / ".opal" / "worktree.json").read_text(encoding="utf-8"))
    candidates = cfg.get("_copy_candidates", [])
    assert "workspace/backend/settings.local.yaml" in candidates, (
        f"repos 자신보다 한 단계 더 깊은 로컬 설정 후보도 제시돼야 한다: {candidates}"
    )
    assert cfg.get("copy") == [], (
        "깊은 탐지가 추가돼도 copy[]는 여전히 추측 없이 빈 배열이어야 한다(DEC-8)"
    )


# ═════════════════════════════════════════════════════════════════════════════
# 118 TEST-SCENARIO.md S-3~S-8, S-11, S-15 — taskCapsuleCone·canonical metadata·
# TASK_PATH_AMBIGUOUS·finalize 재진입 path-scoped 판정·memory-index-request 가드
# (PLAN D-1/D-2/D-2b/D-3b, ANALYSIS Q2/Q6/Q7). RED-first — S-3만 구현 전에도 PASS
# 해야 하는 회귀 보호 케이스이고, 나머지는 구현 전 FAIL이 정상이다(TASK.md C-1).
# ═════════════════════════════════════════════════════════════════════════════


def _write_repo_file(repo: pathlib.Path, relpath: str, content: str) -> None:
    """S-11 fixture 전용 — conftest.py를 건드리지 않기 위해 이 파일 안에 로컬 복제한다."""
    path = repo / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _payload_mentions(payload: dict, needle: str) -> bool:
    """응답 JSON 어디든(키 이름을 가정하지 않고) needle 문자열이 나타나는지 확인한다."""
    return needle in json.dumps(payload, ensure_ascii=False)


def test_t118_s3_missing_task_capsule_cone_key_is_byte_identical_regression(
    project_b: ProjectB,
):
    """[T118/S-3] `taskCapsuleCone` 키 미지정 시 `sparse-checkout set` 인자가 현행(`repos`만)과
    바이트 동일함을 고정하는 회귀 테스트(AC-6, C-1, PLAN D-1).

    [MUST] TASK.md C-1 — 이 케이스는 구현 전에도 PASS해야 정상이다: 현재 monorepo 분기
    (`worktree_tool.py:814`)가 이미 `sparse-checkout set *cfg["repos"]`만 실행하며
    `taskCapsuleCone`을 전혀 읽지 않기 때문이다. 키 미지정 no-op이 구현 후에도 보전돼야
    하므로(C-1) 회귀 가드로 유지한다.
    """
    result = run_worktree_cli(
        ["create", "--project-root", str(project_b.root), "--task", "118"]
    )
    payload = parse_json_stdout(result, "create(S-3)")
    assert payload.get("ok") is True, f"S-3 create 실패: {payload}"

    config = json.loads(project_b.config_path.read_text(encoding="utf-8"))
    assert "taskCapsuleCone" not in config, "S-3 전제 위반: fixture 설정에 키가 있으면 안 됨"

    wt_root = project_b.root / ".opal-worktrees" / "task_118"
    list_result = run_git(["sparse-checkout", "list"], cwd=wt_root)
    cone_lines = [line for line in list_result.stdout.splitlines() if line.strip()]
    assert cone_lines == config["repos"], (
        f"S-3: taskCapsuleCone 키 미지정 시 cone이 repos({config['repos']})와 바이트 동일해야 "
        f"함(C-1 회귀): {cone_lines}"
    )


def test_t118_s4_task_capsule_cone_adds_tasks_and_opal_to_monorepo_cone(
    project_b: ProjectB,
):
    """[T118/S-4] 구현 전 RED — `taskCapsuleCone: ["tasks", ".opal"]` 지정 시 cone에 두 항목이
    추가되고 실체화된다(AC-6, PLAN D-1). project_b의 origin_mono는 `tasks/README.md`,
    `.opal/README.md`를 이미 커밋하고 있어 실체화를 직접 관측할 수 있다.
    """
    config = json.loads(project_b.config_path.read_text(encoding="utf-8"))
    config["taskCapsuleCone"] = ["tasks", ".opal"]
    write_json(project_b.config_path, config)

    result = run_worktree_cli(
        ["create", "--project-root", str(project_b.root), "--task", "118"]
    )
    payload = parse_json_stdout(result, "create(S-4)")
    assert payload.get("ok") is True, f"S-4 create 실패: {payload}"

    wt_root = project_b.root / ".opal-worktrees" / "task_118"
    list_result = run_git(["sparse-checkout", "list"], cwd=wt_root)
    cone_lines = {line.strip() for line in list_result.stdout.splitlines() if line.strip()}
    assert {"workspace", "tasks", ".opal"} <= cone_lines, (
        f"S-4: cone에 tasks/.opal이 추가되지 않음(taskCapsuleCone 미적용): {cone_lines}"
    )
    assert (wt_root / "tasks" / "README.md").exists(), "S-4: tasks/가 실체화되지 않음"
    assert (wt_root / ".opal" / "README.md").exists(), "S-4: .opal/이 실체화되지 않음"


def test_t118_s5_multi_repo_layout_ignores_task_capsule_cone(project_a: ProjectA):
    """[T118/S-5] 구현 전 RED — `layout: multi-repo`에서는 `taskCapsuleCone`이 적용되지 않고
    `repos`의 독립 저장소 의미가 보존된다(AC-6, C-6, PLAN D-1 — multi-repo 분기 `:773-792`
    무변경).

    [주의] project_a의 backend/frontend 레포 자체에는 애초에 `tasks/`·`.opal/`이 존재하지
    않으므로(별개 독립 저장소), 이 조건에서는 "cone 미적용"과 "현재 코드가 이 키를 아예
    모르는 것"이 관측상 구분되지 않는다 — 즉 이 케이스는 구현 전에도 이미 PASS할 수 있다
    (S-3과 동형의 회귀 보호 성격). 그래도 PLAN AC-6·C-6이 명시한 계약이므로 고정한다.
    """
    config = json.loads(project_a.config_path.read_text(encoding="utf-8"))
    config["taskCapsuleCone"] = ["tasks", ".opal"]
    write_json(project_a.config_path, config)

    result = run_worktree_cli(
        ["create", "--project-root", str(project_a.root), "--task", "118"]
    )
    payload = parse_json_stdout(result, "create(S-5)")
    assert payload.get("ok") is True, f"S-5 create 실패: {payload}"

    wt_root = project_a.root / ".opal-worktrees" / "task_118"
    for name in ("backend", "frontend"):
        repo_wt = wt_root / "workspace" / name
        assert not (repo_wt / "tasks").exists(), f"S-5: {name}에 tasks/가 나타남(cone 오적용)"
        assert not (repo_wt / ".opal").exists(), f"S-5: {name}에 .opal/이 나타남(cone 오적용)"


def test_t118_s6a_task_capsule_cone_non_string_element_gives_config_invalid_type(
    tmp_path,
):
    """[T118/S-6] 구현 전 RED — `taskCapsuleCone`에 비문자열 원소가 있으면
    `CONFIG_INVALID_TYPE(key="taskCapsuleCone")`로 거부된다(AC-6, PLAN D-1 — 신규 에러
    코드를 만들지 않는다)."""
    root = _minimal_project(
        tmp_path,
        {
            "layout": "monorepo",
            "repos": ["workspace"],
            "taskCapsuleCone": ["tasks", 123],
        },
        "proj_t118_s6a",
    )
    result = run_worktree_cli(["list", "--project-root", str(root)])
    payload = parse_json_stdout(result, "list(S-6a)")
    assert payload.get("ok") is False, f"S-6a: 비문자열 원소가 통과함: {payload}"
    assert payload.get("error") == "CONFIG_INVALID_TYPE", f"S-6a 에러 코드 불일치: {payload}"
    assert payload.get("key") == "taskCapsuleCone", (
        f"S-6a: 에러의 key가 taskCapsuleCone이어야 함: {payload}"
    )


def test_t118_s6b_task_capsule_cone_path_escape_gives_config_path_escape(tmp_path):
    """[T118/S-6] 구현 전 RED — `taskCapsuleCone`에 상위 이탈 경로(`../x`)가 있으면
    `CONFIG_PATH_ESCAPE`로 거부된다(AC-6, PLAN D-1 — 신규 에러 코드를 만들지 않는다)."""
    root = _minimal_project(
        tmp_path,
        {
            "layout": "monorepo",
            "repos": ["workspace"],
            "taskCapsuleCone": ["../escape"],
        },
        "proj_t118_s6b",
    )
    result = run_worktree_cli(["list", "--project-root", str(root)])
    payload = parse_json_stdout(result, "list(S-6b)")
    assert payload.get("ok") is False, f"S-6b: 상위 이탈 경로가 통과함: {payload}"
    assert payload.get("error") == "CONFIG_PATH_ESCAPE", f"S-6b 에러 코드 불일치: {payload}"


def test_t118_s6_error_codes_stay_within_existing_set(tmp_path):
    """[T118/S-6] 신규 에러 코드가 추가되지 않았는지 교차 확인 — S-6a/S-6b가 각각
    기존에도 존재하던 `CONFIG_INVALID_TYPE`/`CONFIG_PATH_ESCAPE`만 반환해야 한다."""
    for cfg, expected in (
        (
            {
                "layout": "monorepo",
                "repos": ["workspace"],
                "taskCapsuleCone": [None],
            },
            "CONFIG_INVALID_TYPE",
        ),
        (
            {
                "layout": "monorepo",
                "repos": ["workspace"],
                "taskCapsuleCone": ["..", "nested/../../escape"],
            },
            "CONFIG_PATH_ESCAPE",
        ),
    ):
        root = _minimal_project(tmp_path, cfg, f"proj_t118_s6_{expected.lower()}")
        result = run_worktree_cli(["list", "--project-root", str(root)])
        payload = parse_json_stdout(result, f"list(S-6 {expected})")
        assert payload.get("error") == expected, f"S-6 교차확인 실패: {payload}"


def test_t118_s7_create_response_and_meta_have_task_ownership_fields(
    project_b: ProjectB,
):
    """[T118/S-7] 구현 전 RED — `create` 성공 응답과
    `.opal-worktrees/.meta/task_<NNN>.json`이 `allocator_root`·`task_home`·`task_folder`·
    `task_path`·`artifact_repo`·`task_ownership_version` 6필드를 갖고
    `realpath(task_path) == realpath(task_home/tasks/task_folder)`가 성립한다
    (AC-5, PLAN D-1 §5.1, 제안서 §5.1).

    [설계 가정] `task_folder`는 PM/allocator가 이미 확정한 태스크 문서 폴더명을 `create`에
    `--task-folder`로 명시 전달한다고 가정한다(제안서 §6.1 생성 순서: task folder 이름을
    worktree 생성 전에 메모리에서 확정). GREEN 구현이 다른 인자명을 택하면 이 테스트의
    CLI 인자 이름만 맞춰 조정하면 된다 — 응답·메타 필드 계약(6필드, realpath 동치)은
    제안서 §5.1 원문 그대로다.
    """
    result = run_worktree_cli(
        [
            "create",
            "--project-root",
            str(project_b.root),
            "--task",
            "118",
            "--task-folder",
            "118-260912-opd-fixture",
        ]
    )
    payload = parse_json_stdout(result, "create(S-7)")
    assert payload.get("ok") is True, f"S-7 create 실패: {payload}"

    required_fields = (
        "allocator_root",
        "task_home",
        "task_folder",
        "task_path",
        "artifact_repo",
        "task_ownership_version",
    )
    for field in required_fields:
        assert field in payload, f"S-7: 응답에 {field} 필드 누락: {payload}"

    meta_path = project_b.root / ".opal-worktrees" / ".meta" / "task_118.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    for field in required_fields:
        assert field in meta, f"S-7: 메타 파일에 {field} 필드 누락: {meta}"

    expected_task_path = os.path.realpath(
        os.path.join(str(meta["task_home"]), "tasks", str(meta["task_folder"]))
    )
    assert os.path.realpath(str(meta["task_path"])) == expected_task_path, (
        f"S-7: realpath(task_path) != realpath(task_home/tasks/task_folder): {meta}"
    )


@pytest.mark.parametrize(
    "bad_task_folder",
    ["sub/dir", "..", "../escape", "a/../../b", "nul\x00byte"],
)
def test_t118_s7_create_rejects_unsafe_task_folder(
    project_b: ProjectB, bad_task_folder: str
):
    """[T118/S-7] 구현 전 RED — `task_folder`에 `/`·`..`·NUL이 포함되면 basename만 허용하는
    계약에 따라 거부된다(AC-5, 제안서 §5.1 "task_folder는 basename만 허용").

    [NUL 케이스의 관측 지점] NUL 바이트는 `execve(2)` 인자 경계에서 이미 거부되므로 CLI
    프로세스에 도달할 수 없다(`subprocess`가 `ValueError: embedded null byte`를 올린다).
    거부 계약 자체는 보전되며 관측 지점만 OS 경계로 내려간다 — 어느 쪽이든 "NUL이 포함된
    task_folder로는 create가 성사되지 않는다"가 증명된다. GREEN 구현도 `_validate_task_folder`
    에서 NUL을 독립적으로 거부한다(방어적 이중화).
    """
    try:
        result = run_worktree_cli(
            [
                "create",
                "--project-root",
                str(project_b.root),
                "--task",
                "118",
                "--task-folder",
                bad_task_folder,
            ]
        )
    except ValueError:
        assert "\x00" in bad_task_folder, (
            f"ValueError는 NUL 케이스에서만 허용된다: {bad_task_folder!r}"
        )
        assert not (project_b.root / ".opal-worktrees" / "task_118").exists(), (
            "NUL task_folder로 create가 성사되어서는 안 된다"
        )
        return
    payload = parse_json_stdout(result, f"create(S-7 unsafe={bad_task_folder!r})")
    assert payload.get("ok") is False, (
        f"S-7: 안전하지 않은 task_folder({bad_task_folder!r})가 통과함: {payload}"
    )


def test_t118_s8_status_blocks_when_hub_task_folder_collides_with_worktree_task(
    project_b: ProjectB,
):
    """[T118/S-8] 구현 전 RED — 등록된 worktree 태스크와 같은 `task_folder`가 허브
    `tasks/`에도 존재하면 canonical task path 해석이 자동 선택 없이 `TASK_PATH_AMBIGUOUS`로
    차단된다(AC-7, 제안서 §5.1 "동시에 있으면 ... task_path_ambiguous로 차단").

    [설계 가정] canonical task path를 해석하는 진입점을 `status`로 가정한다(등록된 태스크의
    현재 위치를 조회하는 기존 서브커맨드). GREEN 구현이 별도 진입점(예: `resolve`)을 새로
    만들면 이 테스트의 서브커맨드만 조정하면 된다 — 판정 자체(`TASK_PATH_AMBIGUOUS`, 자동
    선택 금지)는 AC-7 원문 그대로다.
    """
    create_result = run_worktree_cli(
        [
            "create",
            "--project-root",
            str(project_b.root),
            "--task",
            "118",
            "--task-folder",
            "118-260912-opd-fixture",
        ]
    )
    create_payload = parse_json_stdout(create_result, "create(S-8 setup)")
    assert create_payload.get("ok") is True, f"S-8 사전 create 실패: {create_payload}"

    hub_dup = project_b.root / "tasks" / "118-260912-opd-fixture"
    hub_dup.mkdir(parents=True, exist_ok=True)
    (hub_dup / "TASK.md").write_text("# 허브 쪽 중복 폴더\n", encoding="utf-8")

    result = run_worktree_cli(
        ["status", "--project-root", str(project_b.root), "--task", "118"]
    )
    payload = parse_json_stdout(result, "status(S-8)")
    assert payload.get("ok") is False, (
        f"S-8: 허브·워크트리 양쪽에 같은 task_folder가 있는데 자동 선택으로 통과함: {payload}"
    )
    assert payload.get("error") == "TASK_PATH_AMBIGUOUS", f"S-8 에러 코드 불일치: {payload}"


def _build_finalize_fixture(tmp_path: pathlib.Path, name: str):
    """S-11 전용 — 허브(project_root)와 task_118 worktree(브랜치 체크아웃에 `.opal/brain`,
    `tasks/{task_folder}/DONE.md` 포함)를 raw git으로 구성한다. `finalize` 서브커맨드가
    아직 없으므로(RED) `create`를 거치지 않고 `add_worktree`/`write_meta`(conftest 기존
    헬퍼, S-092 트랙에서 이미 같은 목적으로 쓰던 패턴)로 선행 상태를 직접 조립한다.
    반환: (project_root, wt_root, task_path, task_folder)"""
    remotes_dir = tmp_path / f"_remotes_{name}"
    remotes_dir.mkdir()
    origin = make_bare_remote(remotes_dir, f"origin_{name}")
    project_root = clone_repo(origin, tmp_path, f"hub_{name}")

    task_folder = "118-260912-opd-fixture"
    branch = "feat/OP-TASK-118"
    wt_root = project_root / ".opal-worktrees" / "task_118"
    add_worktree(project_root, branch, wt_root, base="main")

    _write_repo_file(wt_root, ".opal/brain/index.md", "# index\n")
    _write_repo_file(wt_root, ".opal/brain/log.md", "# log\n")
    _write_repo_file(
        wt_root,
        ".opal/MEMORY.json",
        json.dumps({"last_task_number": 118, "history": [], "memories": []}),
    )
    _write_repo_file(
        wt_root,
        f"tasks/{task_folder}/DONE.md",
        "## 회고적 학습 후보\n- .opal/brain/pages/concept/declared-page.md\n",
    )
    _write_repo_file(wt_root, ".opal/brain/pages/concept/declared-page.md", "# declared\n")
    _write_repo_file(
        wt_root, ".opal/brain/pages/concept/undeclared-page.md", "# undeclared\n"
    )
    run_git(["add", "-A"], cwd=wt_root)
    run_git(["commit", "-m", "seed S-11 finalize fixture"], cwd=wt_root)

    task_path = wt_root / "tasks" / task_folder
    write_meta(
        project_root,
        "118",
        layout="monorepo",
        branch=branch,
        entries=[
            {
                "repo": str(project_root),
                "path": str(wt_root),
                "branch": branch,
                "base_ref": "main",
            }
        ],
        worktree_root=wt_root,
    )
    meta_path = project_root / ".opal-worktrees" / ".meta" / "task_118.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta.update(
        {
            "allocator_root": str(project_root),
            "task_home": str(wt_root),
            "task_folder": task_folder,
            "task_path": str(task_path),
            "artifact_repo": ".",
            "task_ownership_version": 2,
        }
    )
    write_json(meta_path, meta)

    return project_root, wt_root, task_path, task_folder


def test_t118_s11_finalize_reentry_allowed_when_dirty_is_subset_of_declared(tmp_path):
    """[T118/S-11] 구현 전 RED — 양방향 케이스 (1/2, 허용): 1차 실행이 DONE.md에 선언된
    brain page(`declared-page.md`)를 미커밋 상태로 남긴 채 중단된 뒤 재실행하면, 관측
    집합이 선언 집합의 부분집합(`S ⊆ D`)이므로 재개가 허용된다(AC-10, PLAN D-3b).

    [설계 가정] `finalize` 서브커맨드가 `--project-root`/`--task`로 meta를 읽어 task_path의
    DONE.md와 worktree_root의 `git status --porcelain`을 대조한다고 가정한다."""
    project_root, wt_root, task_path, _task_folder = _build_finalize_fixture(
        tmp_path, "s11_allow"
    )

    # 1차 실행 중단 재현 — 선언된 brain page만 미커밋 상태로 남긴다.
    _write_repo_file(
        wt_root, ".opal/brain/pages/concept/declared-page.md", "# declared (수정됨)\n"
    )

    result = run_worktree_cli(
        ["finalize", "--project-root", str(project_root), "--task", "118"]
    )
    payload = parse_json_stdout(result, "finalize(S-11 allow)")
    assert payload.get("error") != "ATTRIBUTION_COMMIT_BLOCKED", (
        f"S-11: 선언된 page만 dirty인데 차단됨(S⊆D 위반): {payload}"
    )
    assert payload.get("ok") is True, f"S-11: 선언 집합 부분집합인데 재개가 허용되지 않음: {payload}"


def test_t118_s11_finalize_reentry_blocked_when_undeclared_page_is_dirty(tmp_path):
    """[T118/S-11] 구현 전 RED — 양방향 케이스 (2/2, 차단): DONE.md에 선언되지 않은
    brain page(`undeclared-page.md`)가 미커밋 상태이면, 관측 집합이 선언 집합을 벗어나므로
    (`S ⊄ D`) `ATTRIBUTION_COMMIT_BLOCKED`가 위반 경로 목록과 함께 반환된다(AC-10, PLAN
    D-3b)."""
    project_root, wt_root, task_path, _task_folder = _build_finalize_fixture(
        tmp_path, "s11_block"
    )

    # 선언되지 않은 page를 미커밋 상태로 남긴다(declared-page.md는 건드리지 않는다).
    _write_repo_file(
        wt_root, ".opal/brain/pages/concept/undeclared-page.md", "# undeclared (수정됨)\n"
    )

    result = run_worktree_cli(
        ["finalize", "--project-root", str(project_root), "--task", "118"]
    )
    payload = parse_json_stdout(result, "finalize(S-11 block)")
    assert payload.get("ok") is False, (
        f"S-11: 선언되지 않은 page가 dirty인데 차단되지 않음(S⊆D 오판정): {payload}"
    )
    assert payload.get("error") == "ATTRIBUTION_COMMIT_BLOCKED", f"S-11 에러 코드 불일치: {payload}"
    assert _payload_mentions(payload, "undeclared-page.md"), (
        f"S-11: 위반 경로 목록에 undeclared-page.md가 동봉돼야 함: {payload}"
    )


def test_t118_s15_remove_blocked_by_pending_memory_index_request(tmp_path):
    """[T118/S-15] 구현 전 RED — 미처리 memory-index-request가 있으면 `remove`가
    `MEMORY_INDEX_REQUEST_PENDING`으로 거부된다(AC-11, PLAN D-2b). 3중 가드는 모두
    clean(`build_guard_repo(..., "clean")`)이므로 이 거부는 신규 memory-index 가드만의
    효과다."""
    g = build_guard_repo(tmp_path, "clean", name_suffix="_s15pending")
    task_path = g.project_root / "tasks" / "118-260912-opd-fixture"
    task_path.mkdir(parents=True)
    write_json(
        task_path / "memory-index-request.json",
        {
            "schema_version": 1,
            "requests": [
                {
                    "task_id": g.task,
                    "title": "예시 학습 후보",
                    "type": "concept",
                    "status": "pending",
                    "file": ".opal/brain/pages/concept/example.md",
                    "summary": "예시 요약",
                    "body_sha256": "a" * 64,
                    "requested_at": "2026-09-12 00:00",
                }
            ],
        },
    )
    meta_path = g.project_root / ".opal-worktrees" / ".meta" / f"task_{g.task}.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["task_path"] = str(task_path)
    meta["memory_index_requests_resolved"] = []
    write_json(meta_path, meta)

    result = run_worktree_cli(
        ["remove", "--project-root", str(g.project_root), "--task", g.task]
    )
    payload = parse_json_stdout(result, "remove(S-15 pending)")
    assert payload.get("ok") is False, f"S-15: 미처리 요청이 있는데 remove가 통과함: {payload}"
    assert payload.get("error") == "MEMORY_INDEX_REQUEST_PENDING", (
        f"S-15 에러 코드 불일치: {payload}"
    )


def test_t118_s15_remove_allowed_when_all_requests_applied(tmp_path):
    """[T118/S-15] 전부 `applied` 처리된 경우 기존 dirty·unpushed·unmerged 3중 가드만
    적용되고(clean 상태이므로) `remove`가 성공한다(AC-11, PLAN D-2b).

    [MUST] 이 케이스는 신규 memory-index 가드가 없어도(현재 코드) clean 상태이므로 이미
    PASS한다 — S-3/S-5와 동형인 회귀 보호 성격이며 순수 RED는 아니다. 그래도 계약을
    고정하기 위해 유지한다."""
    g = build_guard_repo(tmp_path, "clean", name_suffix="_s15applied")
    task_path = g.project_root / "tasks" / "118-260912-opd-fixture"
    task_path.mkdir(parents=True)
    body_sha = "b" * 64
    write_json(
        task_path / "memory-index-request.json",
        {
            "schema_version": 1,
            "requests": [
                {
                    "task_id": g.task,
                    "title": "예시 학습 후보",
                    "type": "concept",
                    "status": "applied",
                    "file": ".opal/brain/pages/concept/example.md",
                    "summary": "예시 요약",
                    "body_sha256": body_sha,
                    "requested_at": "2026-09-12 00:00",
                }
            ],
        },
    )
    meta_path = g.project_root / ".opal-worktrees" / ".meta" / f"task_{g.task}.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["task_path"] = str(task_path)
    meta["memory_index_requests_resolved"] = [body_sha]
    write_json(meta_path, meta)

    result = run_worktree_cli(
        ["remove", "--project-root", str(g.project_root), "--task", g.task]
    )
    payload = parse_json_stdout(result, "remove(S-15 applied)")
    assert payload.get("ok") is True, f"S-15: 전부 applied인데 remove가 거부됨: {payload}"


def test_t118_s15_remove_no_capsule_file_is_noop_pass(tmp_path):
    """[T118/S-15] 캡슐 파일(`memory-index-request.json`) 자체가 없으면 no-op으로
    통과하고 기존 가드만 적용된다(AC-11, PLAN D-2b).

    [MUST] 이 케이스도 현재 코드에서 이미 PASS한다(신규 가드 부재 + clean 상태) — S-15의
    "applied" 케이스와 동형인 회귀 보호 성격이며 순수 RED는 아니다."""
    g = build_guard_repo(tmp_path, "clean", name_suffix="_s15nocaps")
    meta_path = g.project_root / ".opal-worktrees" / ".meta" / f"task_{g.task}.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["task_path"] = str(g.project_root / "tasks" / "118-260912-opd-nofixture")
    meta["memory_index_requests_resolved"] = []
    write_json(meta_path, meta)

    result = run_worktree_cli(
        ["remove", "--project-root", str(g.project_root), "--task", g.task]
    )
    payload = parse_json_stdout(result, "remove(S-15 no-capsule)")
    assert payload.get("ok") is True, f"S-15: 캡슐 파일 부재인데 거부됨: {payload}"
