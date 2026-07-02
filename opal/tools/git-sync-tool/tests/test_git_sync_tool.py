"""
@header {
  "module": "test_git_sync_tool",
  "layer": "test",
  "domain": "opal-workspace",
  "description": "git-sync-tool RED-first 테스트 (052 TEST-SCENARIO.md S-1~S-10,S-16~S-18 대응). 구현(git_sync_tool.py) 부재 상태에서 작성 — CLI(subprocess) 공개 인터페이스로만 검증, mock/patch 금지, 실 git 저장소 fixture(conftest.py) 사용. RED 증거: git_sync_tool.py 미존재로 전 테스트 실패해야 한다.",
  "exports": [],
  "depends": ["conftest.py", "git_sync_tool.py(미구현)"]
}
"""

from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

from conftest import GitFixtureWorkspace, run_git, run_sync_cli

REQUIRED_TOP_FIELDS = {"ok", "command", "workspace", "repositories", "summary", "error"}
REQUIRED_REPO_FIELDS = {
    "name",
    "branch",
    "upstream",
    "status",
    "reason",
    "ahead",
    "behind",
    "prev_head",
    "new_head",
    "pulled_commits",
}
REQUIRED_SUMMARY_FIELDS = {"total", "updated", "skipped", "failed"}
VALID_STATUS = {"updated", "skipped", "failed", "already-current"}
VALID_REASON = {"dirty", "diverged", "detached", "no-upstream", "fetch-failed", None}


def _parse_json_stdout(result: subprocess.CompletedProcess) -> dict:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(
            "sync 결과 stdout이 유효 JSON이 아님 (H-6 JSON 계약 위반). "
            f"exit={result.returncode}\nstdout={result.stdout!r}\nstderr={result.stderr!r}\n"
            f"원인: {exc}"
        )


def _find_repo(payload: dict, name: str) -> dict:
    for repo in payload["repositories"]:
        if repo.get("name") == name:
            return repo
    pytest.fail(f"repositories에서 '{name}' 항목을 찾지 못함. payload={payload}")


def _assert_top_schema(payload: dict) -> None:
    missing = REQUIRED_TOP_FIELDS - payload.keys()
    assert not missing, f"최상위 JSON 필드 누락: {missing} (H-6)"
    assert payload["command"] == "sync"
    assert isinstance(payload["repositories"], list)
    summary_missing = REQUIRED_SUMMARY_FIELDS - payload["summary"].keys()
    assert not summary_missing, f"summary 필드 누락: {summary_missing} (H-6)"


def _assert_repo_schema(repo: dict) -> None:
    missing = REQUIRED_REPO_FIELDS - repo.keys()
    assert not missing, f"repository 객체 필드 누락: {missing} (H-6) repo={repo}"
    assert repo["status"] in VALID_STATUS, f"status enum 위반: {repo['status']!r}"
    assert repo["reason"] in VALID_REASON, f"reason enum 위반: {repo['reason']!r}"


# ---------------------------------------------------------------------------
# S-1: repo_behind → status=updated, pulled_commits=N, HEAD 전진, behind=N/ahead=0
# ---------------------------------------------------------------------------
def test_s1_behind_only_updates_via_ff_pull(git_workspace: GitFixtureWorkspace) -> None:
    prev_head = run_git(["rev-parse", "HEAD"], cwd=git_workspace.repo_behind).stdout.strip()

    result = run_sync_cli(git_workspace.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    repo = _find_repo(payload, "repo_behind")
    _assert_repo_schema(repo)

    assert repo["status"] == "updated", f"behind-only 저장소가 updated가 아님: {repo}"
    assert repo["reason"] is None
    assert repo["pulled_commits"] == git_workspace.behind_n, (
        f"pulled_commits 불일치: 기대={git_workspace.behind_n}, 실제={repo['pulled_commits']}"
    )
    assert repo["behind"] == git_workspace.behind_n
    assert repo["ahead"] == 0

    new_head = run_git(["rev-parse", "HEAD"], cwd=git_workspace.repo_behind).stdout.strip()
    assert new_head != prev_head, "HEAD가 전진하지 않음 (ff-pull 미실행 의심)"
    assert repo["prev_head"] is not None and repo["new_head"] is not None


# ---------------------------------------------------------------------------
# S-2: repo_dirty → status=skipped, reason=dirty
# ---------------------------------------------------------------------------
def test_s2_dirty_is_skipped(git_workspace: GitFixtureWorkspace) -> None:
    result = run_sync_cli(git_workspace.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    repo = _find_repo(payload, "repo_dirty")
    _assert_repo_schema(repo)

    assert repo["status"] == "skipped"
    assert repo["reason"] == "dirty"


# ---------------------------------------------------------------------------
# S-3: repo_diverged → status=skipped, reason=diverged (ahead>0 AND behind>0)
# ---------------------------------------------------------------------------
def test_s3_diverged_is_skipped(git_workspace: GitFixtureWorkspace) -> None:
    result = run_sync_cli(git_workspace.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    repo = _find_repo(payload, "repo_diverged")
    _assert_repo_schema(repo)

    assert repo["status"] == "skipped"
    assert repo["reason"] == "diverged"
    assert repo["ahead"] is not None and repo["ahead"] > 0, f"ahead>0 기대: {repo}"
    assert repo["behind"] is not None and repo["behind"] > 0, f"behind>0 기대: {repo}"


# ---------------------------------------------------------------------------
# S-4: repo_detached → status=skipped, reason=detached
# ---------------------------------------------------------------------------
def test_s4_detached_head_is_skipped(git_workspace: GitFixtureWorkspace) -> None:
    result = run_sync_cli(git_workspace.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    repo = _find_repo(payload, "repo_detached")
    _assert_repo_schema(repo)

    assert repo["status"] == "skipped"
    assert repo["reason"] == "detached"


# ---------------------------------------------------------------------------
# S-5: repo_noupstream → status=skipped, reason=no-upstream, upstream=null
# ---------------------------------------------------------------------------
def test_s5_no_upstream_is_skipped_without_exception(git_workspace: GitFixtureWorkspace) -> None:
    result = run_sync_cli(git_workspace.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    repo = _find_repo(payload, "repo_noupstream")
    _assert_repo_schema(repo)

    assert repo["status"] == "skipped"
    assert repo["reason"] == "no-upstream"
    assert repo["upstream"] is None


# ---------------------------------------------------------------------------
# S-6: repo_fetchfail → status=failed, reason=fetch-failed, 크래시 없이 순회 지속
# ---------------------------------------------------------------------------
def test_s6_fetch_failure_reported_without_crash(git_workspace: GitFixtureWorkspace) -> None:
    result = run_sync_cli(git_workspace.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    repo = _find_repo(payload, "repo_fetchfail")
    _assert_repo_schema(repo)

    assert repo["status"] == "failed"
    assert repo["reason"] == "fetch-failed"

    # 크래시 없이 나머지 저장소도 순회를 계속했는지 확인 (전체 8종이 모두 결과에 존재)
    all_names = {r["name"] for r in payload["repositories"]}
    expected_names = {
        "repo_behind",
        "repo_current",
        "repo_dirty",
        "repo_diverged",
        "repo_detached",
        "repo_noupstream",
        "repo_fetchfail",
    }
    missing = expected_names - all_names
    assert not missing, f"fetch 실패 이후 순회가 중단되어 누락된 저장소: {missing}"


# ---------------------------------------------------------------------------
# S-7: JSON 출력 계약 검증 — 유효 JSON + 필수 필드 존재 (전체 실행)
# ---------------------------------------------------------------------------
def test_s7_json_output_contract(git_workspace: GitFixtureWorkspace) -> None:
    result = run_sync_cli(git_workspace.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    assert isinstance(payload["ok"], bool)
    assert isinstance(payload["workspace"], str)

    assert len(payload["repositories"]) >= 1, "repositories가 비어있음"
    for repo in payload["repositories"]:
        _assert_repo_schema(repo)


# ---------------------------------------------------------------------------
# S-8: repo_current → status=already-current, pulled_commits=0, HEAD 불변
# ---------------------------------------------------------------------------
def test_s8_already_current_skips_pull(git_workspace: GitFixtureWorkspace) -> None:
    prev_head = run_git(["rev-parse", "HEAD"], cwd=git_workspace.repo_current).stdout.strip()

    result = run_sync_cli(git_workspace.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    repo = _find_repo(payload, "repo_current")
    _assert_repo_schema(repo)

    assert repo["status"] == "already-current"
    assert repo["pulled_commits"] == 0

    new_head = run_git(["rev-parse", "HEAD"], cwd=git_workspace.repo_current).stdout.strip()
    assert new_head == prev_head, "already-current 저장소의 HEAD가 변경됨"


# ---------------------------------------------------------------------------
# S-9: 대상 결정 — workspace 직속 자식 중 .git 보유 저장소 전부 순회, 1단계만
# ---------------------------------------------------------------------------
def test_s9_target_discovery_covers_all_direct_children_only(
    git_workspace: GitFixtureWorkspace,
) -> None:
    # 중첩 검증용: workspace 자식 저장소 내부에 또 다른 git 저장소를 중첩 배치 -
    # 순회 대상에 포함되면 안 된다 (1단계만, 재귀 금지).
    nested_bare_dir = git_workspace.root / "_remotes"
    from conftest import clone_repo, make_bare_remote  # 동일 컨벤션 재사용

    nested_bare = make_bare_remote(nested_bare_dir, "nested")
    clone_repo(nested_bare, git_workspace.repo_current, "nested_should_not_appear")

    result = run_sync_cli(git_workspace.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    all_names = {r["name"] for r in payload["repositories"]}
    expected_direct_children = {
        "repo_behind",
        "repo_current",
        "repo_dirty",
        "repo_diverged",
        "repo_detached",
        "repo_noupstream",
        "repo_fetchfail",
    }
    missing = expected_direct_children - all_names
    assert not missing, f"직속 자식 저장소 누락: {missing}"
    assert "nested_should_not_appear" not in all_names, (
        "중첩된 하위 git 저장소가 순회 대상에 포함됨 (재귀 금지 위반, H-7)"
    )


# ---------------------------------------------------------------------------
# S-10: 단일 git 루트 경로 전달 시 repositories 길이 1
# ---------------------------------------------------------------------------
def test_s10_single_git_root_path_yields_one_repository(single_repo_root: pathlib.Path) -> None:
    result = run_sync_cli(single_repo_root)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    assert len(payload["repositories"]) == 1, (
        f"단일 git 루트 전달 시 repositories 길이가 1이 아님: {payload['repositories']}"
    )
    _assert_repo_schema(payload["repositories"][0])
    assert payload["repositories"][0]["name"] == single_repo_root.name


# ---------------------------------------------------------------------------
# S-16: repo_dirty 무손실 (P0) — 실행 전후 HEAD·porcelain 완전 불변
# ---------------------------------------------------------------------------
def test_s16_dirty_repo_is_never_mutated(git_workspace: GitFixtureWorkspace) -> None:
    repo = git_workspace.repo_dirty
    prev_head = run_git(["rev-parse", "HEAD"], cwd=repo).stdout.strip()
    prev_porcelain = run_git(["status", "--porcelain"], cwd=repo).stdout

    result = run_sync_cli(git_workspace.workspace)
    _parse_json_stdout(result)  # 계약 파싱 가능 여부만 확인, 본 시나리오 핵심은 아래 불변성

    new_head = run_git(["rev-parse", "HEAD"], cwd=repo).stdout.strip()
    new_porcelain = run_git(["status", "--porcelain"], cwd=repo).stdout

    assert new_head == prev_head, "dirty 저장소의 HEAD가 sync 실행으로 변경됨 (P0 무손실 위반, H-1)"
    assert new_porcelain == prev_porcelain, (
        "dirty 저장소의 작업트리 상태가 sync 실행으로 변경됨 (P0 무손실 위반, H-1)\n"
        f"before={prev_porcelain!r}\nafter={new_porcelain!r}"
    )


# ---------------------------------------------------------------------------
# S-17: repo_diverged 무손실 (P0) — 실행 전후 HEAD 불변, 머지커밋 미생성, 커밋 수 불변
# ---------------------------------------------------------------------------
def test_s17_diverged_repo_head_and_commit_count_unchanged(
    git_workspace: GitFixtureWorkspace,
) -> None:
    repo = git_workspace.repo_diverged
    prev_head = run_git(["rev-parse", "HEAD"], cwd=repo).stdout.strip()
    prev_commit_count = run_git(
        ["rev-list", "--count", "HEAD"], cwd=repo
    ).stdout.strip()

    result = run_sync_cli(git_workspace.workspace)
    _parse_json_stdout(result)

    new_head = run_git(["rev-parse", "HEAD"], cwd=repo).stdout.strip()
    new_commit_count = run_git(["rev-list", "--count", "HEAD"], cwd=repo).stdout.strip()

    assert new_head == prev_head, "diverged 저장소의 HEAD가 sync 실행으로 이동함 (P0 무손실 위반, H-2)"
    assert new_commit_count == prev_commit_count, (
        "diverged 저장소의 HEAD 커밋 수가 변경됨 — 머지/병합 커밋 생성 의심 (P0 무손실 위반, H-2)\n"
        f"before={prev_commit_count} after={new_commit_count}"
    )

    # HEAD의 부모 수가 1개인지 확인 (2개 이상이면 머지커밋 = 병합 발생)
    parent_count_output = run_git(
        ["cat-file", "-p", "HEAD"], cwd=repo
    ).stdout
    parent_lines = [line for line in parent_count_output.splitlines() if line.startswith("parent ")]
    assert len(parent_lines) <= 1, f"HEAD가 머지커밋으로 보임(parent {len(parent_lines)}개): H-2 위반"


# ---------------------------------------------------------------------------
# S-18: repo_diverged — pull 미실행(ff-only가 diverged 병합 안 함) → skipped 확인
# ---------------------------------------------------------------------------
def test_s18_diverged_repo_pull_never_attempted(git_workspace: GitFixtureWorkspace) -> None:
    result = run_sync_cli(git_workspace.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    repo = _find_repo(payload, "repo_diverged")
    _assert_repo_schema(repo)

    assert repo["status"] == "skipped", (
        f"diverged 저장소가 skipped가 아님 (ff-only가 시도됐을 가능성, H-2/H-5): {repo}"
    )
    assert repo["reason"] == "diverged"
    assert repo["pulled_commits"] in (0, None), (
        f"diverged 저장소인데 pulled_commits가 0이 아님(pull 실행 흔적): {repo}"
    )

    # 도구가 크래시 없이 정상 종료했는지 (non-ff 예외로 전체 프로세스가 죽지 않아야 함)
    assert result.returncode in (0, 1), f"예상치 못한 exit code: {result.returncode}, stderr={result.stderr}"
