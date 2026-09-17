"""
@header {
  "module": "test_git_sync_tool",
  "layer": "test",
  "domain": "opal-workspace",
  "description": "git-sync-tool RED-first 테스트. 052 블록(S-1~S-10,S-16~S-18 + S-19~S-22 root 저장소)과 139 블록(opws 워크스페이스 선언 — 선언 로더·org/repo 정규화·3진 대조·6상태·init/clone)을 담는다. CLI(subprocess) 공개 인터페이스로만 검증하고 mock/patch를 쓰지 않으며 실 git 저장소 fixture(conftest.py)를 사용한다. 139 S-1~S-7은 구현 전 RED로 작성해 14건 실패를 확인한 뒤 GREEN으로 전환했고(선언 로더·정규화 부재가 유일한 실패 사유), 원격 좌표와 fetch 도달성을 동시에 요구하는 시나리오는 url.<base>.insteadOf 재작성으로 구성한다 — 도구는 config 원문을 읽으므로 재작성이 판정에 새지 않는다.",
  "exports": [],
  "depends": ["conftest.py", "git_sync_tool.py"]
}
"""

from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

from conftest import (
    GitFixtureWorkspace,
    GitProjectRootFixture,
    run_git,
    run_sync_cli,
    run_tool_cli,
    write_workspace_config,
)

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


# ---------------------------------------------------------------------------
# S-19: --root 전달 시 순회 대상 밖의 root 저장소도 pull된다 (Golden Path)
# ---------------------------------------------------------------------------
def test_s19_root_repo_is_pulled_with_root_option(
    project_root_with_workspace: GitProjectRootFixture,
) -> None:
    fx = project_root_with_workspace
    result = run_sync_cli(fx.workspace, "--root", str(fx.project))
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    assert payload["root"] == str(fx.project), (
        f"root 필드가 전달한 root 경로와 다름: {payload['root']!r}"
    )

    all_names = {r["name"] for r in payload["repositories"]}
    assert "project" in all_names, (
        f"--root로 전달한 root 저장소가 순회 대상에 없음: {all_names}"
    )
    assert "repo_child" in all_names, (
        f"workspace 직속 자식 저장소가 누락됨(기존 동작 회귀): {all_names}"
    )

    root_repo = _find_repo(payload, "project")
    _assert_repo_schema(root_repo)
    assert root_repo["status"] == "updated", (
        f"behind 상태 root 저장소가 최신화되지 않음: {root_repo}"
    )
    assert root_repo["pulled_commits"] == fx.behind_n, (
        f"root 저장소 pulled_commits가 behind 수({fx.behind_n})와 다름: {root_repo}"
    )
    assert payload["summary"]["total"] == len(payload["repositories"])


# ---------------------------------------------------------------------------
# S-20: --root 미전달 시 현행 동작 100% 유지 (root 저장소 미포함)
# ---------------------------------------------------------------------------
def test_s20_root_repo_absent_without_root_option(
    project_root_with_workspace: GitProjectRootFixture,
) -> None:
    fx = project_root_with_workspace
    result = run_sync_cli(fx.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    all_names = {r["name"] for r in payload["repositories"]}
    assert "project" not in all_names, (
        f"--root 미전달인데 root 저장소가 순회됨(현행 동작 변경): {all_names}"
    )
    assert all_names == {"repo_child"}, f"대상이 workspace 직속 자식뿐이 아님: {all_names}"
    assert payload["root"] is None, f"--root 미전달인데 root 필드가 null이 아님: {payload['root']!r}"


# ---------------------------------------------------------------------------
# S-21: .git 없는 --root는 제외된다 (발생 낮음 / 영향 높음 — 상위 저장소 오조작 방지)
#       .git 없는 경로에서 git을 실행하면 상위 디렉토리의 저장소로 올라가 엉뚱한 저장소를 조작한다.
# ---------------------------------------------------------------------------
def test_s21_non_repo_root_is_excluded(
    project_root_with_workspace: GitProjectRootFixture,
) -> None:
    fx = project_root_with_workspace
    # workspace 자체는 git 저장소가 아니지만, 상위 project는 저장소다 (오조작 유발 조건).
    result = run_sync_cli(fx.workspace, "--root", str(fx.workspace))
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    assert payload["root"] is None, (
        f".git 없는 root가 제외되지 않음: {payload['root']!r}"
    )
    all_names = {r["name"] for r in payload["repositories"]}
    assert all_names == {"repo_child"}, (
        f".git 없는 root가 대상에 포함됨(상위 저장소 오조작 위험): {all_names}"
    )
    assert result.returncode == 0, f"제외는 에러가 아니어야 함: exit={result.returncode}"


# ---------------------------------------------------------------------------
# S-22: --root가 이미 발견된 대상과 같으면 중복 계상하지 않는다
#       (발생 낮음 / 영향 높음 — 같은 저장소 2회 pull + summary 이중 계상)
# ---------------------------------------------------------------------------
def test_s22_root_duplicate_is_not_counted_twice(
    project_root_with_workspace: GitProjectRootFixture,
) -> None:
    fx = project_root_with_workspace
    # project 자체를 순회 경로로 주면 단일 git 루트로 발견된다 → --root와 중복.
    result = run_sync_cli(fx.project, "--root", str(fx.project))
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    assert len(payload["repositories"]) == 1, (
        f"root 중복이 제거되지 않음: {payload['repositories']}"
    )
    assert payload["repositories"][0]["name"] == "project"
    assert payload["summary"]["total"] == 1, f"summary 이중 계상: {payload['summary']}"


# ═══════════════════════════════════════════════════════════════════════════
# 139(opws) 워크스페이스 선언 기반 확장 — RED-first M1 시나리오 S-1~S-7
#
# 이 블록은 아직 존재하지 않는 계약(workspace.json 선언 로더, org/repo 정규화,
# 3진 대조 match/mismatch/unknown, 스키마 검증)을 CLI subprocess 공개 인터페이스로만
# 관찰한다. 현재 git_sync_tool.py는 workspace.json을 전혀 읽지 않으므로 아래 테스트는
# 전부 실패해야 정상이다(RED). 내부 함수 import 금지 — normalize_repo_coord/
# compare_repo_coord/load_workspace_config를 직접 import하지 않는다.
#
# 판정값이 노출되는 정확한 필드명(reason="mismatch"/"unknown" 등)은 PLAN.md의
# 문장 표현이 완전히 확정하지 않으므로, 이 테스트 블록이 그 표면 계약을 최초로
# 고정한다 — GREEN 구현은 여기 단언과 합치해야 한다.
# ═══════════════════════════════════════════════════════════════════════════


def _ws_declare(dir_name: str, repo: str, state: str = "active",
                org: str = "storelink-io", host: str = "github.com") -> dict:
    return {
        "schema_version": 1,
        "host": host,
        "org": org,
        "repos": [{"dir": dir_name, "repo": repo, "state": state}],
    }


# ---------------------------------------------------------------------------
# S-1: 선언 storelink-io/blend, 실제 origin이 storelink-io/blend-admin → mismatch,
#      해당 저장소는 pull되지 않는다(HEAD 불변, pulled_commits==0)
# ---------------------------------------------------------------------------
def test_ws_s1_mismatch_different_repo_name_blocks_pull(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    run_git(
        ["remote", "set-url", "origin", "https://github.com/storelink-io/blend-admin.git"],
        cwd=fx.repo_behind,
    )
    write_workspace_config(fx.root, _ws_declare("repo_behind", "blend"))

    prev_head = run_git(["rev-parse", "HEAD"], cwd=fx.repo_behind).stdout.strip()

    result = run_sync_cli(fx.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    repo = _find_repo(payload, "repo_behind")
    assert repo.get("reason") == "mismatch", (
        f"선언과 다른 org/repo인데 mismatch로 판정되지 않음: {repo}"
    )
    assert repo.get("status") != "updated", (
        f"mismatch 저장소가 pull되어 updated로 보고됨(fail-closed 위반): {repo}"
    )
    assert not repo.get("pulled_commits"), (
        f"mismatch 저장소인데 pulled_commits가 발생함: {repo}"
    )

    new_head = run_git(["rev-parse", "HEAD"], cwd=fx.repo_behind).stdout.strip()
    assert new_head == prev_head, (
        "mismatch 저장소인데 HEAD가 전진함 — pull이 실제로 수행됨(fail-closed 집행 실패)"
    )


# ---------------------------------------------------------------------------
# S-2: 선언 storelink-io/blend, 실제 origin이 other-org/blend (org만 다름) → mismatch
# ---------------------------------------------------------------------------
def test_ws_s2_mismatch_different_org_blocks_pull(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    run_git(
        ["remote", "set-url", "origin", "https://github.com/other-org/blend.git"],
        cwd=fx.repo_behind,
    )
    write_workspace_config(fx.root, _ws_declare("repo_behind", "blend"))

    prev_head = run_git(["rev-parse", "HEAD"], cwd=fx.repo_behind).stdout.strip()

    result = run_sync_cli(fx.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    repo = _find_repo(payload, "repo_behind")
    assert repo.get("reason") == "mismatch", f"org만 다른데 mismatch가 아님: {repo}"
    assert repo.get("status") != "updated", f"mismatch인데 pull됨: {repo}"

    new_head = run_git(["rev-parse", "HEAD"], cwd=fx.repo_behind).stdout.strip()
    assert new_head == prev_head, "org만 다른 mismatch 저장소인데 HEAD가 전진함"


# ---------------------------------------------------------------------------
# S-3: 선언 storelink-io/blend, 실제 origin이 storelink-io/blend2 (접두 유사) → mismatch.
#      접두 일치를 동일로 보지 않는다.
# ---------------------------------------------------------------------------
def test_ws_s3_mismatch_prefix_similar_repo_blocks_pull(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    run_git(
        ["remote", "set-url", "origin", "https://github.com/storelink-io/blend2.git"],
        cwd=fx.repo_behind,
    )
    write_workspace_config(fx.root, _ws_declare("repo_behind", "blend"))

    prev_head = run_git(["rev-parse", "HEAD"], cwd=fx.repo_behind).stdout.strip()

    result = run_sync_cli(fx.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    repo = _find_repo(payload, "repo_behind")
    assert repo.get("reason") == "mismatch", (
        f"접두 유사(blend vs blend2)를 동일로 오판정함: {repo}"
    )
    assert repo.get("status") != "updated", f"접두 유사 mismatch인데 pull됨: {repo}"

    new_head = run_git(["rev-parse", "HEAD"], cwd=fx.repo_behind).stdout.strip()
    assert new_head == prev_head, "접두 유사 mismatch 저장소인데 HEAD가 전진함"


# ---------------------------------------------------------------------------
# S-4: 같은 레포를 4형식(별칭 SSH·SSH·HTTPS+.git·ssh://)으로 각각 설정해도
#      선언 org/repo와 대조 시 전부 match — host·프로토콜이 판정을 바꾸지 않는다.
#
#      PM Gate 수정: 이 4형식은 의도적으로 도달 불가한 host(github.com 등 실호출 금지
#      제약 하의 문자열)이므로 "정상 fetch/pull 성공"을 단언 대상으로 삼지 않는다
#      (그건 결함 RED다 — 구현으로도 GREEN이 될 수 없다). 대신 정규화 결과 자체를
#      직접 관찰한다: repositories[]의 정규화 키 `repo` 필드(PLAN W-4 "정규화 키 repo
#      필드를 추가한다")가 4형식 모두 동일한 `org/repo`로 환원되는지, 그리고 그 판정이
#      `mismatch`/`unknown`으로 오판정되지 않는지만 확인한다. fetch 성공 여부(도달성)는
#      이 시나리오의 검증 대상이 아니다.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "origin_url",
    [
        "git@github-alias:storelink-io/blend",
        "git@github.com:storelink-io/blend",
        "https://github.com/storelink-io/blend.git",
        "ssh://git@github.com/storelink-io/blend",
    ],
    ids=["ssh-alias", "ssh-canonical", "https-dotgit", "ssh-url-scheme"],
)
def test_ws_s4_equivalent_url_formats_all_match(
    git_workspace: GitFixtureWorkspace, origin_url: str
) -> None:
    fx = git_workspace
    run_git(["remote", "set-url", "origin", origin_url], cwd=fx.repo_behind)
    write_workspace_config(fx.root, _ws_declare("repo_behind", "blend"))

    result = run_sync_cli(fx.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    repo = _find_repo(payload, "repo_behind")
    assert repo.get("reason") != "mismatch", (
        f"동일 레포의 형식 차이({origin_url})를 mismatch로 오판정함: {repo}"
    )
    assert repo.get("reason") != "unknown", (
        f"동일 레포의 형식 차이({origin_url})를 unknown으로 오판정함: {repo}"
    )
    assert repo.get("repo") == "storelink-io/blend", (
        f"동일 레포의 형식 차이({origin_url})가 같은 정규화 키(org/repo)로 환원되지 않음: {repo}"
    )


# ---------------------------------------------------------------------------
# S-5: 한 워크스페이스에 .git 접미사가 있는 origin과 없는 origin이 공존 → 둘 다 match.
#      접미사 유무가 판정을 바꾸지 않는다.
#
#      PM Gate 재수정: 로컬 파일시스템 경로를 org/repo로 환원하는 축은 PLAN 계약 밖이며
#      (정규화 대상은 git@host:org/repo·ssh://·https:// 3형식뿐), 임의 경로의 마지막
#      2세그먼트를 org/repo로 읽으면 서로 무관한 경로가 같은 키로 충돌하는 새 미탐(H-1)을
#      만든다. S-4와 동일한 방식으로 되돌린다 — 원격 URL 형식(도달 불가)으로 .git 접미사
#      유무만 축으로 삼고, 검증은 `repo` 정규화 키와 mismatch/unknown 오판정 여부만 본다.
#      "match 판정 이후 실제 sync 정상 수행"은 S-8(선언 부재 회귀)·S-9(6상태 중 active·
#      있음→sync)가 이미 소유하므로 이 시나리오가 pull 성공까지 떠안지 않는다. 심링크·
#      로컬 bare 재사용도 제거한다.
# ---------------------------------------------------------------------------
def test_ws_s5_dotgit_suffix_presence_does_not_affect_match(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    run_git(
        ["remote", "set-url", "origin", "https://github.com/storelink-io/blend.git"],
        cwd=fx.repo_behind,
    )
    run_git(
        ["remote", "set-url", "origin", "git@github.com:storelink-io/blend-current"],
        cwd=fx.repo_current,
    )
    write_workspace_config(
        fx.root,
        {
            "schema_version": 1,
            "host": "github.com",
            "org": "storelink-io",
            "repos": [
                {"dir": "repo_behind", "repo": "blend", "state": "active"},
                {"dir": "repo_current", "repo": "blend-current", "state": "active"},
            ],
        },
    )

    result = run_sync_cli(fx.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    repo_with_suffix = _find_repo(payload, "repo_behind")
    repo_without_suffix = _find_repo(payload, "repo_current")

    for repo in (repo_with_suffix, repo_without_suffix):
        assert repo.get("reason") not in ("mismatch", "unknown"), (
            f".git 접미사 유무로 오판정됨: {repo}"
        )

    assert repo_with_suffix.get("repo") == "storelink-io/blend", (
        f".git 접미사 있는 origin의 정규화 키가 기대와 다름: {repo_with_suffix}"
    )
    assert repo_without_suffix.get("repo") == "storelink-io/blend-current", (
        f".git 접미사 없는 origin의 정규화 키가 기대와 다름: {repo_without_suffix}"
    )


# ---------------------------------------------------------------------------
# S-6: 자식 저장소에 origin이 없거나 파싱 불가한 remote 문자열이 설정됨 → unknown으로
#      보고되고 pull되지 않는다(match로 간주되지 않는다, fail-closed).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "setup_origin",
    [
        lambda repo_path: run_git(["remote", "remove", "origin"], cwd=repo_path),
        lambda repo_path: run_git(
            ["remote", "set-url", "origin", "not-a-valid-remote-string"], cwd=repo_path
        ),
    ],
    ids=["origin-absent", "origin-unparseable"],
)
def test_ws_s6_missing_or_unparseable_origin_is_unknown_and_not_pulled(
    git_workspace: GitFixtureWorkspace, setup_origin
) -> None:
    fx = git_workspace
    setup_origin(fx.repo_behind)
    write_workspace_config(fx.root, _ws_declare("repo_behind", "blend"))

    prev_head = run_git(["rev-parse", "HEAD"], cwd=fx.repo_behind).stdout.strip()

    result = run_sync_cli(fx.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    repo = _find_repo(payload, "repo_behind")
    assert repo.get("reason") == "unknown", (
        f"origin 부재/파싱불가가 unknown으로 보고되지 않음: {repo}"
    )
    assert repo.get("reason") != "match", repo
    assert repo.get("status") != "updated", f"unknown 저장소인데 pull됨: {repo}"

    new_head = run_git(["rev-parse", "HEAD"], cwd=fx.repo_behind).stdout.strip()
    assert new_head == prev_head, "unknown 저장소인데 HEAD가 전진함(pull 집행됨)"


# ---------------------------------------------------------------------------
# S-7: workspace.json 스키마 위반 4건 — 각각 WORKSPACE_CONFIG_INVALID로 거부되고
#      순회를 시작하지 않는다(repositories/summary 키가 응답에 없음).
# ---------------------------------------------------------------------------
def _base_valid_repos() -> list:
    return [
        {"dir": "child-a", "repo": "blend", "state": "active"},
        {"dir": "child-b", "repo": "other", "state": "active"},
    ]


@pytest.mark.parametrize(
    "bad_config",
    [
        pytest.param(
            {
                "schema_version": 1,
                "host": "github.com",
                "org": "storelink-io",
                "repos": [{"dir": "child-a", "repo": "blend", "state": "actve"}],
            },
            id="state-typo",
        ),
        pytest.param(
            {
                "schema_version": 1,
                "host": "github.com",
                "org": "storelink-io",
                "repos": [{"dir": "../x", "repo": "blend", "state": "active"}],
            },
            id="dir-path-traversal",
        ),
        pytest.param(
            {
                "schema_version": 1,
                "host": "github.com",
                "org": "storelink-io",
                "repos": [
                    {"dir": "child-a", "repo": "blend", "state": "active"},
                    {"dir": "child-a", "repo": "other", "state": "active"},
                ],
            },
            id="dir-duplicate",
        ),
        pytest.param(
            {
                "schema_version": 1,
                "host": "github.com",
                "org": "storelink-io",
                "repos": [
                    {"dir": "child-a", "repo": "blend", "state": "active"},
                    {"dir": "child-b", "repo": "blend", "state": "active"},
                ],
            },
            id="repo-duplicate",
        ),
    ],
)
def test_ws_s7_schema_violation_rejected_before_traversal(
    tmp_path: pathlib.Path, bad_config: dict
) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    write_workspace_config(tmp_path, bad_config)

    result = run_sync_cli(workspace_dir)
    payload = _parse_json_stdout(result)

    assert payload.get("ok") is False, (
        f"스키마 위반 workspace.json이 거부되지 않음: {payload}"
    )
    assert payload.get("error") == "WORKSPACE_CONFIG_INVALID", (
        f"스키마 위반 에러 코드가 WORKSPACE_CONFIG_INVALID가 아님: {payload}"
    )
    assert "repositories" not in payload, (
        f"스키마 위반인데 순회가 시작됨(repositories 키 존재): {payload}"
    )
    assert "summary" not in payload, (
        f"스키마 위반인데 summary가 생성됨(순회 실행 증거): {payload}"
    )


# ═══════════════════════════════════════════════════════════════════════════
# 139(opws) 구현 후 시나리오 S-8~S-17
#
# S-1~S-7이 고정한 표면 계약 위에서 나머지 수용 기준을 관찰한다. 동일 규율 —
# CLI subprocess 공개 인터페이스만 사용하고 내부 함수를 import하지 않는다.
#
# 원격 좌표(org/repo)와 실제 fetch 도달성을 동시에 만족시켜야 하는 시나리오는
# git의 `url.<base>.insteadOf` 재작성을 쓴다. `git remote get-url`은 재작성 전
# 원문을 돌려주므로 도구는 원격 좌표를 보고, fetch는 로컬 bare로 연결된다.
# ═══════════════════════════════════════════════════════════════════════════

WS_TOP_FIELDS_NO_CONFIG = {
    "ok", "error", "command", "workspace", "root", "repositories", "summary",
}


def _bare_of(fx: GitFixtureWorkspace, name: str) -> pathlib.Path:
    return fx.root / "_remotes" / f"{name}.git"


def _point_at_remote_coord(
    repo_path: pathlib.Path, bare_path: pathlib.Path, coord_url: str
) -> None:
    """origin을 원격 좌표 문자열로 바꾸되, fetch는 로컬 bare로 가도록 재작성을 건다."""
    run_git(["config", f'url.{bare_path}.insteadOf', coord_url], cwd=repo_path)
    run_git(["remote", "set-url", "origin", coord_url], cwd=repo_path)


# ---------------------------------------------------------------------------
# S-8: 선언 파일이 없으면 응답 키 집합이 도입 전과 동일하다 (AC-4, C-1, H-3)
# ---------------------------------------------------------------------------
def test_ws_s8_no_declaration_keeps_response_shape(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    assert not (fx.root / ".opal" / "workspace.json").exists()

    result = run_sync_cli(fx.workspace)
    payload = _parse_json_stdout(result)

    assert set(payload.keys()) == WS_TOP_FIELDS_NO_CONFIG, (
        f"선언 부재인데 최상위 키 집합이 달라짐: {sorted(payload.keys())}"
    )
    for repo in payload["repositories"]:
        assert set(repo.keys()) == REQUIRED_REPO_FIELDS, (
            f"선언 부재인데 repository 키 집합이 달라짐: {sorted(repo.keys())}"
        )
        _assert_repo_schema(repo)
        assert repo["reason"] not in (
            "mismatch", "unknown", "not-cloned", "undeclared", "undeclared-active",
        ), f"선언 부재인데 선언 대조 판정이 발생함: {repo}"


# ---------------------------------------------------------------------------
# S-9: 선언 × 디스크 6상태가 각각 판정된다 (AC-5)
# ---------------------------------------------------------------------------
def test_ws_s9_six_states_are_each_judged(git_workspace: GitFixtureWorkspace) -> None:
    fx = git_workspace

    # (1) active·있음·좌표 일치 → sync 수행
    _point_at_remote_coord(
        fx.repo_behind, _bare_of(fx, "behind"),
        "https://github.com/storelink-io/blend.git",
    )
    # (4) deferred·있음 → sync + 선언 어긋남 보고
    _point_at_remote_coord(
        fx.repo_current, _bare_of(fx, "current"),
        "https://github.com/storelink-io/blend-current.git",
    )
    # (6) 환원 불가 → unknown (origin이 로컬 경로 그대로)

    write_workspace_config(
        fx.root,
        {
            "schema_version": 1,
            "host": "github.com",
            "org": "storelink-io",
            "repos": [
                {"dir": "repo_behind", "repo": "blend", "state": "active"},
                {"dir": "repo_absent", "repo": "blend-absent", "state": "active"},
                {"dir": "repo_deferred_absent", "repo": "blend-later", "state": "deferred"},
                {"dir": "repo_current", "repo": "blend-current", "state": "deferred"},
                {"dir": "repo_noupstream", "repo": "blend-noupstream", "state": "active"},
            ],
        },
    )

    result = run_sync_cli(fx.workspace)
    payload = _parse_json_stdout(result)
    _assert_top_schema(payload)

    # (1) active·있음 → sync 수행
    behind = _find_repo(payload, "repo_behind")
    assert behind["declaration"] == "match", behind
    assert behind["status"] == "updated", f"active·있음·일치인데 sync되지 않음: {behind}"
    assert behind["repo"] == "storelink-io/blend", behind

    # (2) active·없음 → not-cloned
    absent = _find_repo(payload, "repo_absent")
    assert absent["reason"] == "not-cloned", absent
    assert absent["status"] == "skipped", absent

    # (3) deferred·없음 → 조치 없는 정상 상태지만 **보고에는 남는다** (ADD-1)
    #     경고를 내지 않는 것과 출력에서 지우는 것은 다르다. 지우면 선언해 둔 레포가
    #     어디에도 나타나지 않아 "선언은 했는데 아무도 안 본다"가 된다.
    deferred_absent = _find_repo(payload, "repo_deferred_absent")
    assert deferred_absent["reason"] == "deferred", deferred_absent
    assert deferred_absent["declaration"] == "deferred", deferred_absent
    assert deferred_absent["status"] == "skipped", deferred_absent
    assert deferred_absent["repo"] == "storelink-io/blend-later", deferred_absent

    # (4) deferred·있음 → sync + 선언 어긋남 보고
    deferred_present = _find_repo(payload, "repo_current")
    assert deferred_present["declaration"] == "undeclared-active", deferred_present
    assert deferred_present["status"] in ("updated", "already-current"), (
        f"deferred·있음은 sync 대상이다: {deferred_present}"
    )

    # (5) 미선언·있음 → undeclared
    undeclared = _find_repo(payload, "repo_dirty")
    assert undeclared["reason"] == "undeclared", undeclared

    # (6) 환원 불가 → unknown
    unknown = _find_repo(payload, "repo_noupstream")
    assert unknown["reason"] == "unknown", unknown
    assert unknown["status"] == "skipped", unknown


# ---------------------------------------------------------------------------
# S-10: 어느 응답에도 원격 URL 원문이 등장하지 않는다 (AC-7, C-3)
# ---------------------------------------------------------------------------
def test_ws_s10_no_raw_remote_url_in_any_response(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    raw_url = "git@github-iskang:storelink-io/blend"
    run_git(["remote", "set-url", "origin", raw_url], cwd=fx.repo_behind)
    write_workspace_config(fx.root, _ws_declare("repo_behind", "blend"))

    sync_out = run_sync_cli(fx.workspace).stdout
    init_out = run_tool_cli("init", str(fx.workspace), "--dry-run").stdout
    clone_out = run_tool_cli(
        "clone", str(fx.workspace), "--dir", "repo_cloned",
        "--url", str(_bare_of(fx, "behind")),
    ).stdout

    for label, out in (("sync", sync_out), ("init", init_out), ("clone", clone_out)):
        assert "github-iskang" not in out, f"{label} 응답에 원격 host 별칭이 노출됨: {out}"
        assert raw_url not in out, f"{label} 응답에 원격 URL 원문이 노출됨: {out}"
        assert str(_bare_of(fx, "behind")) not in out, (
            f"{label} 응답에 clone URL 원문이 노출됨: {out}"
        )

    repo = _find_repo(json.loads(sync_out), "repo_behind")
    assert repo["repo"] == "storelink-io/blend", repo


# ---------------------------------------------------------------------------
# S-11: init 4케이스 — 생성 / CONFIG_EXISTS 거부 / --force 덮어씀 / --dry-run 미생성
# ---------------------------------------------------------------------------
def test_ws_s11_init_draft_contract(git_workspace: GitFixtureWorkspace) -> None:
    fx = git_workspace
    _point_at_remote_coord(
        fx.repo_behind, _bare_of(fx, "behind"),
        "https://github.com/storelink-io/blend.git",
    )
    config_path = fx.root / ".opal" / "workspace.json"

    # (d) --dry-run — 파일을 쓰지 않고 draft만 반환
    dry = _parse_json_stdout(run_tool_cli("init", str(fx.workspace), "--dry-run"))
    assert dry["ok"] is True, dry
    assert "draft" in dry, f"--dry-run 응답에 draft 키가 없음: {dry}"
    assert dry["written"] is False, dry
    assert not config_path.exists(), "--dry-run이 파일을 생성함"

    # (a) 부재 → 생성
    created = _parse_json_stdout(run_tool_cli("init", str(fx.workspace)))
    assert created["ok"] is True and created["written"] is True, created
    assert config_path.exists(), "init이 선언 파일을 생성하지 않음"
    written = json.loads(config_path.read_text(encoding="utf-8"))
    assert written["schema_version"] == 1
    assert written["org"] == "storelink-io", written
    assert {r["dir"] for r in written["repos"]} == {"repo_behind"}, written
    assert all(r["state"] == "active" for r in written["repos"]), (
        f"init이 deferred를 추측함: {written}"
    )

    # (b) 존재 + --force 없음 → CONFIG_EXISTS 거부, 기존 파일 무변경
    before = config_path.read_text(encoding="utf-8")
    rejected = _parse_json_stdout(run_tool_cli("init", str(fx.workspace)))
    assert rejected["ok"] is False, rejected
    assert rejected["error"] == "CONFIG_EXISTS", rejected
    assert config_path.read_text(encoding="utf-8") == before, "거부했는데 파일이 변경됨"

    # (b-2) 존재 + --dry-run → 거부하지 않는다. 쓰지 않는 경로이므로 충돌이 없고,
    #       선언이 이미 있을 때 디스크와의 차이를 보려면 이 경로가 열려 있어야 한다.
    dry_with_existing = _parse_json_stdout(
        run_tool_cli("init", str(fx.workspace), "--dry-run")
    )
    assert dry_with_existing["ok"] is True, (
        f"--dry-run이 기존 파일 존재로 거부됨(쓰지 않는데 막혔다): {dry_with_existing}"
    )
    assert dry_with_existing["written"] is False, dry_with_existing
    assert config_path.read_text(encoding="utf-8") == before, "--dry-run이 파일을 변경함"

    # (c) 존재 + --force → 덮어씀
    config_path.write_text('{"schema_version": 1, "host": "x", "org": "y", "repos": []}',
                           encoding="utf-8")
    forced = _parse_json_stdout(run_tool_cli("init", str(fx.workspace), "--force"))
    assert forced["ok"] is True and forced["written"] is True, forced
    assert json.loads(config_path.read_text(encoding="utf-8"))["org"] == "storelink-io"


# ---------------------------------------------------------------------------
# S-12: not-cloned는 보고만 되고 승인 없이 clone되지 않는다 (AC-8, C-5)
# ---------------------------------------------------------------------------
def test_ws_s12_not_cloned_is_reported_without_cloning(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    write_workspace_config(
        fx.root,
        {
            "schema_version": 1,
            "host": "github.com",
            "org": "storelink-io",
            "repos": [{"dir": "repo_missing", "repo": "blend-missing", "state": "active"}],
        },
    )
    before = {child.name for child in fx.workspace.iterdir()}

    payload = _parse_json_stdout(run_sync_cli(fx.workspace))
    _assert_top_schema(payload)

    missing = _find_repo(payload, "repo_missing")
    assert missing["reason"] == "not-cloned", missing
    assert missing["repo"] == "storelink-io/blend-missing", missing

    after = {child.name for child in fx.workspace.iterdir()}
    assert after == before, f"sync가 승인 없이 디렉토리를 생성함: {after - before}"


# ---------------------------------------------------------------------------
# S-14: host는 비교에 쓰지 않는다 — 수용한 트레이드오프이며 문서에 명시돼 있다 (H-2)
# ---------------------------------------------------------------------------
def test_ws_s14_host_is_not_compared_and_is_documented(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    run_git(
        ["remote", "set-url", "origin", "https://github.com/storelink-io/blend"],
        cwd=fx.repo_behind,
    )
    run_git(
        ["remote", "set-url", "origin", "https://gitlab.com/storelink-io/blend-current"],
        cwd=fx.repo_current,
    )
    write_workspace_config(
        fx.root,
        {
            "schema_version": 1,
            "host": "github.com",
            "org": "storelink-io",
            "repos": [
                {"dir": "repo_behind", "repo": "blend", "state": "active"},
                {"dir": "repo_current", "repo": "blend-current", "state": "active"},
            ],
        },
    )

    payload = _parse_json_stdout(run_sync_cli(fx.workspace))
    for name in ("repo_behind", "repo_current"):
        repo = _find_repo(payload, name)
        assert repo["declaration"] == "match", (
            f"host가 달라 판정이 갈렸다 — host는 비교 축이 아니다: {repo}"
        )

    tool_dir = pathlib.Path(__file__).resolve().parents[1]
    readme = (tool_dir / "README.md").read_text(encoding="utf-8")
    schema = (tool_dir / "schema" / "workspace.schema.json").read_text(encoding="utf-8")
    assert "host" in readme and "비교" in readme, "README에 host 미비교가 기술되지 않음"
    assert "host는 비교에 사용하지 않는다" in schema, (
        "스키마 _help에 host 미비교가 기술되지 않음"
    )


# ---------------------------------------------------------------------------
# S-15: 점유된 디렉토리로의 clone은 거부되고 기존 내용이 보존된다 (AC-8, C-5)
# ---------------------------------------------------------------------------
def test_ws_s15_clone_into_occupied_dir_is_rejected(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    occupied = fx.workspace / "repo_occupied"
    occupied.mkdir()
    (occupied / "keep.txt").write_text("사람이 둔 내용\n", encoding="utf-8")

    payload = _parse_json_stdout(run_tool_cli(
        "clone", str(fx.workspace), "--dir", "repo_occupied",
        "--url", str(_bare_of(fx, "behind")),
    ))
    assert payload["ok"] is False, payload
    assert payload["error"] == "DIR_EXISTS", payload
    assert (occupied / "keep.txt").read_text(encoding="utf-8") == "사람이 둔 내용\n", (
        "거부했는데 기존 디렉토리 내용이 변경됨"
    )
    assert not (occupied / ".git").exists(), "거부했는데 저장소가 생성됨"


# ---------------------------------------------------------------------------
# S-16: org/repo 비교는 대소문자를 구분하지 않는다 (AC-2, C-2)
# ---------------------------------------------------------------------------
def test_ws_s16_coord_comparison_is_case_insensitive(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    run_git(
        ["remote", "set-url", "origin", "git@github.com:storelink-io/blend"],
        cwd=fx.repo_behind,
    )
    write_workspace_config(
        fx.root,
        {
            "schema_version": 1,
            "host": "github.com",
            "org": "Storelink-IO",
            "repos": [{"dir": "repo_behind", "repo": "Blend", "state": "active"}],
        },
    )

    payload = _parse_json_stdout(run_sync_cli(fx.workspace))
    repo = _find_repo(payload, "repo_behind")
    assert repo["declaration"] == "match", (
        f"대소문자 차이가 mismatch 오탐을 만들었다: {repo}"
    )


# ---------------------------------------------------------------------------
# S-17: 승인 후 clone하면 저장소가 생성되고 이후 sync가 match로 판정한다 (AC-8)
# ---------------------------------------------------------------------------
def test_ws_s17_clone_then_sync_reports_match(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    bare = _bare_of(fx, "behind")

    payload = _parse_json_stdout(run_tool_cli(
        "clone", str(fx.workspace), "--dir", "repo_new", "--url", str(bare),
    ))
    assert payload["ok"] is True and payload["created"] is True, payload
    assert (fx.workspace / "repo_new" / ".git").exists(), "clone이 저장소를 만들지 않음"

    new_repo = fx.workspace / "repo_new"
    _point_at_remote_coord(new_repo, bare, "https://github.com/storelink-io/blend.git")
    write_workspace_config(fx.root, _ws_declare("repo_new", "blend"))

    sync_payload = _parse_json_stdout(run_sync_cli(fx.workspace))
    repo = _find_repo(sync_payload, "repo_new")
    assert repo["declaration"] == "match", f"clone된 저장소가 match로 판정되지 않음: {repo}"
    assert repo["reason"] not in ("mismatch", "unknown", "not-cloned"), repo


# ---------------------------------------------------------------------------
# S-7b: 사람이 손으로 쓴 선언 파일 형태를 거부하지 않는다 (AC-10 경계)
#
# 실환경 선언 파일은 `schema_version`을 문자열 "1.0"으로 쓰고 `_help`·`clone_branch`
# 같은 사람용 필드를 담고 있었다. 이 표기 차이는 판정을 바꾸지 않으므로 거부 사유가
# 아니다 — 거부는 판정을 바꾸는 위반(state enum·dir basename·중복)에만 쓴다.
# ---------------------------------------------------------------------------
def test_ws_s7b_human_authored_declaration_shape_is_accepted(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    run_git(
        ["remote", "set-url", "origin", "git@github-alias:storelink-io/blend"],
        cwd=fx.repo_behind,
    )
    write_workspace_config(
        fx.root,
        {
            "schema_version": "1.0",
            "_help": "사람이 읽는 설명 — 판정에 영향을 주지 않는다",
            "host": "github.com",
            "org": "storelink-io",
            "repos": [
                {
                    "dir": "repo_behind",
                    "repo": "blend",
                    "state": "active",
                    "clone_branch": "main",
                    "note": "보류 사유 메모",
                }
            ],
        },
    )

    payload = _parse_json_stdout(run_sync_cli(fx.workspace))
    assert payload["ok"] is True, f"사람이 쓴 선언 형태가 거부됨: {payload}"
    repo = _find_repo(payload, "repo_behind")
    assert repo["declaration"] == "match", repo


# ---------------------------------------------------------------------------
# S-7c: 알려지지 않은 키는 여전히 거부한다 — 오타(`stat`)가 조용히 통과하면
#       state 판정이 사라진 줄 모른 채 동작한다.
# ---------------------------------------------------------------------------
def test_ws_s7c_unknown_key_is_still_rejected(tmp_path: pathlib.Path) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    write_workspace_config(
        tmp_path,
        {
            "schema_version": 1,
            "host": "github.com",
            "org": "storelink-io",
            "repos": [{"dir": "child-a", "repo": "blend", "stat": "active"}],
        },
    )

    payload = _parse_json_stdout(run_sync_cli(workspace_dir))
    assert payload["ok"] is False, payload
    assert payload["error"] == "WORKSPACE_CONFIG_INVALID", payload


# ---------------------------------------------------------------------------
# S-3b: 계층이 깊은 좌표(GitLab subgroup류)에서 상위 조직이 소실되지 않는다 (H-1)
#
# 독립 검증에서 발견된 미탐이다. 경로의 마지막 2세그먼트만 취하면
# `orgA/team/repo`와 `orgB/team/repo`가 둘 다 `team/repo`가 되어 서로 다른 조직의
# 저장소를 같다고 판정하고, 그대로 pull 경로에 진입한다 — TASK H-1이 막으려던
# 바로 그 손상이다. 좌표는 host를 뺀 경로 전체여야 한다.
# ---------------------------------------------------------------------------
def test_ws_s3b_subgroup_path_does_not_collapse_to_last_two_segments(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    run_git(
        ["remote", "set-url", "origin", "https://gitlab.com/orgB/team/repo.git"],
        cwd=fx.repo_behind,
    )
    write_workspace_config(
        fx.root,
        {
            "schema_version": 1,
            "host": "gitlab.com",
            "org": "orgA",
            "repos": [{"dir": "repo_behind", "repo": "team/repo", "state": "active"}],
        },
    )

    prev_head = run_git(["rev-parse", "HEAD"], cwd=fx.repo_behind).stdout.strip()

    payload = _parse_json_stdout(run_sync_cli(fx.workspace))
    _assert_top_schema(payload)

    repo = _find_repo(payload, "repo_behind")
    assert repo.get("reason") == "mismatch", (
        f"상위 조직이 다른데(orgA vs orgB) 같은 저장소로 판정됨 — H-1 미탐: {repo}"
    )
    assert repo.get("repo") == "orgB/team/repo", (
        f"좌표에서 상위 조직이 소실됨: {repo}"
    )
    assert repo.get("status") != "updated", repo

    new_head = run_git(["rev-parse", "HEAD"], cwd=fx.repo_behind).stdout.strip()
    assert new_head == prev_head, "미탐으로 엉뚱한 저장소가 pull됨"


# ---------------------------------------------------------------------------
# S-3c: 같은 계층 좌표는 URL 형식이 달라도 여전히 match다 (S-3b의 반대 축)
# ---------------------------------------------------------------------------
def test_ws_s3c_same_subgroup_path_still_matches_across_formats(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    run_git(
        ["remote", "set-url", "origin", "git@gitlab-alias:orgA/team/repo"],
        cwd=fx.repo_behind,
    )
    write_workspace_config(
        fx.root,
        {
            "schema_version": 1,
            "host": "gitlab.com",
            "org": "orgA",
            "repos": [{"dir": "repo_behind", "repo": "team/repo", "state": "active"}],
        },
    )

    payload = _parse_json_stdout(run_sync_cli(fx.workspace))
    repo = _find_repo(payload, "repo_behind")
    assert repo.get("declaration") == "match", (
        f"같은 계층 좌표인데 형식 차이로 판정이 갈렸다: {repo}"
    )
    assert repo.get("repo") == "orgA/team/repo", repo


# ---------------------------------------------------------------------------
# S-11b: init 초안은 다수 org와 다른 자식을 억지로 끼워넣지 않는다
#
# 선언의 `repo`는 항상 org 아래 경로이므로, 다른 org의 좌표를 그대로 넣으면
# `org/다른org/repo`로 읽혀 사람이 보는 의미와 판정이 어긋난다. 초안에서 빼고
# `other_org`로 보고해 사람이 결정하게 한다.
# ---------------------------------------------------------------------------
def test_ws_s11b_init_reports_foreign_org_children_separately(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    for repo_path, url in (
        (fx.repo_behind, "https://github.com/storelink-io/blend.git"),
        (fx.repo_current, "https://github.com/storelink-io/blend-current.git"),
        (fx.repo_dirty, "https://github.com/other-org/outsider.git"),
    ):
        run_git(["remote", "set-url", "origin", url], cwd=repo_path)

    payload = _parse_json_stdout(run_tool_cli("init", str(fx.workspace), "--dry-run"))
    assert payload["ok"] is True, payload

    draft = payload["draft"]
    assert draft["org"] == "storelink-io", draft
    dirs = {r["dir"] for r in draft["repos"]}
    assert "repo_dirty" not in dirs, (
        f"다른 org의 자식이 초안에 끼워넣어짐: {draft}"
    )
    assert {"repo_behind", "repo_current"} <= dirs, draft
    assert {entry["dir"] for entry in payload["other_org"]} == {"repo_dirty"}, payload
    assert payload["other_org"][0]["repo"] == "other-org/outsider", payload


# ═══════════════════════════════════════════════════════════════════════════
# ADD-1 — 선언 파일 위치 판정 · init 컨테이너 가드 · deferred 가시화
#
# 실사용(blend 워크스페이스) 검증에서 드러난 3건. 스킬 경유(`sync <프로젝트>/workspace`)
# 로는 어긋나지 않았지만 사람이 프로젝트 경로를 직접 치는 순간 선언 파일이 레포 밖으로
# 잡혔고, 의도적으로 보류한 레포가 출력에서 사라졌다.
# ═══════════════════════════════════════════════════════════════════════════


# ---------------------------------------------------------------------------
# A-1: 순회 경로 자체에 `.opal/`이 있으면 그 경로가 프로젝트 루트다
#      (프로젝트 경로를 직접 준 경우 — 선언 파일이 레포 밖으로 새지 않는다)
# ---------------------------------------------------------------------------
def test_add1_project_root_is_the_path_itself_when_it_has_opal(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    run_git(
        ["remote", "set-url", "origin", "https://github.com/storelink-io/blend.git"],
        cwd=fx.repo_behind,
    )
    # 컨테이너 자신이 프로젝트 루트인 배치 — workspace/.opal/workspace.json
    write_workspace_config(fx.workspace, _ws_declare("repo_behind", "blend"))

    payload = _parse_json_stdout(run_sync_cli(fx.workspace))
    _assert_top_schema(payload)

    assert payload["workspace_config"] == str(
        fx.workspace / ".opal" / "workspace.json"
    ), f"순회 경로 자신의 .opal을 두고 부모를 봤다: {payload['workspace_config']}"
    repo = _find_repo(payload, "repo_behind")
    assert repo["declaration"] == "match", repo


# ---------------------------------------------------------------------------
# A-2: `.opal/`이 없으면 종전대로 부모를 프로젝트 루트로 본다 (회귀 방지)
# ---------------------------------------------------------------------------
def test_add1_project_root_falls_back_to_parent_without_opal(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    assert not (fx.workspace / ".opal").exists()
    write_workspace_config(fx.root, _ws_declare("repo_behind", "blend"))

    payload = _parse_json_stdout(run_sync_cli(fx.workspace))
    assert payload["workspace_config"] == str(
        fx.root / ".opal" / "workspace.json"
    ), payload["workspace_config"]


# ---------------------------------------------------------------------------
# A-3: init이 저장소 자체를 받으면 거부한다
#      (자기 자신을 유일한 자식으로 선언하는 초안은 의미가 없다)
# ---------------------------------------------------------------------------
def test_add1_init_rejects_a_repository_path(single_repo_root: pathlib.Path) -> None:
    payload = _parse_json_stdout(run_tool_cli("init", str(single_repo_root), "--dry-run"))

    assert payload["ok"] is False, f"저장소 경로를 init이 받아들였다: {payload}"
    assert payload["error"] == "NOT_A_WORKSPACE_CONTAINER", payload
    assert "draft" not in payload, payload


# ---------------------------------------------------------------------------
# A-4: init은 컨테이너 자신의 `.opal/`에 쓴다 (레포 밖으로 새지 않는다)
# ---------------------------------------------------------------------------
def test_add1_init_writes_into_the_container_own_opal(
    git_workspace: GitFixtureWorkspace,
) -> None:
    fx = git_workspace
    run_git(
        ["remote", "set-url", "origin", "https://github.com/storelink-io/blend.git"],
        cwd=fx.repo_behind,
    )
    (fx.workspace / ".opal").mkdir()

    payload = _parse_json_stdout(run_tool_cli("init", str(fx.workspace), "--dry-run"))
    assert payload["ok"] is True, payload
    assert payload["config_path"] == str(fx.workspace / ".opal" / "workspace.json"), (
        f"초안 기록 위치가 컨테이너 밖으로 잡혔다: {payload['config_path']}"
    )
