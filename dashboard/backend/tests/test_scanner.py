"""
@header {
  "module": "test_scanner",
  "layer": "test",
  "domain": "console",
  "description": "프로젝트 스캐너 RED-first 테스트 — S-1 시나리오 (L2/M1)",
  "exports": ["[T021/L2-R1] test_scan_finds_opal_projects", "[T021/L2-R1] test_scan_excludes_node_modules", "[T021/L2-R1] test_scan_depth_guard", "[T021/L2-R1] test_scan_marks_non_opal", "[T021/L2-R1][109] test_scan_task_count_two_tier_enumeration"],
  "depends": ["scanner", "config"]
}
"""
import os
import pytest
from pathlib import Path


# ─── Fixtures ─────────────────────────────────────────────────
@pytest.fixture
def opal_workspace(tmp_path: Path) -> Path:
    """fx-opal-a, fx-opal-b(blocked), fx-plain + node_modules 대형 트리 생성"""
    # fx-opal-a: OPAL 적용, tasks 2건
    fx_opal_a = tmp_path / "fx-opal-a"
    (fx_opal_a / ".opal").mkdir(parents=True)
    (fx_opal_a / ".opal" / "AGENT.md").write_text("# AGENT")
    (fx_opal_a / "tasks" / "001-task").mkdir(parents=True)
    (fx_opal_a / "tasks" / "002-task").mkdir(parents=True)

    # fx-opal-b: OPAL 적용, blocked state
    fx_opal_b = tmp_path / "fx-opal-b"
    (fx_opal_b / ".opal").mkdir(parents=True)
    (fx_opal_b / ".opal" / "AGENT.md").write_text("# AGENT blocked project")
    (fx_opal_b / "tasks" / "001-blocked").mkdir(parents=True)

    # fx-plain: 마커 없음
    fx_plain = tmp_path / "fx-plain"
    fx_plain.mkdir()
    (fx_plain / "package.json").write_text('{"name":"plain"}')

    # node_modules 대형 트리 모사 (fx-opal-a 하위)
    nm = fx_opal_a / "node_modules" / "some-pkg" / "lib"
    nm.mkdir(parents=True)
    # node_modules 안에 .opal/AGENT.md가 있어도 무시되어야 함
    (fx_opal_a / "node_modules" / "some-pkg" / ".opal").mkdir()
    (fx_opal_a / "node_modules" / "some-pkg" / ".opal" / "AGENT.md").write_text("# fake")

    return tmp_path


# ─── Tests ────────────────────────────────────────────────────
def test_scan_finds_opal_projects(opal_workspace: Path) -> None:
    """[T021/L2-R1] OPAL 2개(is_opal=true)+plain 1개(is_opal=false) 반환"""
    from dashboard.backend.scanner import scan_projects

    results = scan_projects(
        roots=[str(opal_workspace)],
        depth=2,
        exclude=["node_modules", ".git", ".venv", "__pycache__"],
    )

    names = {r.name: r for r in results}
    assert "fx-opal-a" in names, "fx-opal-a 발견 실패"
    assert "fx-opal-b" in names, "fx-opal-b 발견 실패"
    assert "fx-plain" in names, "fx-plain 발견 실패"

    assert names["fx-opal-a"].is_opal is True
    assert names["fx-opal-b"].is_opal is True
    assert names["fx-plain"].is_opal is False


def test_scan_task_count_accurate(opal_workspace: Path) -> None:
    """[T021/L2-R1] task_count가 실제 tasks/ 하위 디렉토리 수와 일치"""
    from dashboard.backend.scanner import scan_projects

    results = scan_projects(
        roots=[str(opal_workspace)],
        depth=2,
        exclude=["node_modules", ".git", ".venv", "__pycache__"],
    )
    names = {r.name: r for r in results}
    assert names["fx-opal-a"].task_count == 2, f"task_count 불일치: {names['fx-opal-a'].task_count}"
    assert names["fx-plain"].task_count == 0


def test_scan_excludes_node_modules(opal_workspace: Path) -> None:
    """[T021/L2-R1] node_modules 내부 .opal/AGENT.md를 프로젝트로 오인 금지"""
    from dashboard.backend.scanner import scan_projects

    results = scan_projects(
        roots=[str(opal_workspace)],
        depth=2,
        exclude=["node_modules", ".git", ".venv", "__pycache__"],
    )
    names = {r.name for r in results}
    # node_modules 하위 "some-pkg"가 프로젝트로 잡히면 안 됨
    assert "some-pkg" not in names, "node_modules 내 가짜 AGENT.md가 프로젝트로 오인됨"


def test_scan_depth_guard(tmp_path: Path) -> None:
    """[T021/L2-R1] depth 초과 디렉토리는 탐색하지 않음 (maxdepth 가드)"""
    from dashboard.backend.scanner import scan_projects

    # depth=2 이면 root/level1/level2 까지만 탐색
    # depth=2 이면 root/level1/level2/.opal/AGENT.md 는 발견해야 함
    # depth=2 이면 root/level1/level2/level3/.opal/AGENT.md 는 발견 안 해야 함
    deep = tmp_path / "level1" / "level2" / "level3"
    (deep / ".opal").mkdir(parents=True)
    (deep / ".opal" / "AGENT.md").write_text("# too deep")

    shallow = tmp_path / "level1" / "level2"
    (shallow / ".opal").mkdir(parents=True, exist_ok=True)
    (shallow / ".opal" / "AGENT.md").write_text("# shallow ok")

    results = scan_projects(roots=[str(tmp_path)], depth=2, exclude=[])
    names = {r.name for r in results}

    assert "level2" in names, "depth=2 허용 범위 프로젝트 미발견"
    assert "level3" not in names, "depth 초과 프로젝트가 잡힘 (maxdepth 가드 실패)"


def test_scan_task_count_two_tier_enumeration(tmp_path: Path) -> None:
    """[T021/L2-R1][109] task_count는 `tasks/` 1-depth + `tasks/backup/` 1-depth
    2단 열거를 합산한다. `backup` 폴더 자체는 태스크로 세지 않고, 그 하위 폴더만 센다.
    Step 8의 단일 열거 함수(iter_task_dirs/resolve_task_dir) 도입 전이므로 RED가 정상."""
    from dashboard.backend.scanner import scan_projects

    fx = tmp_path / "fx-opal-c"
    (fx / ".opal").mkdir(parents=True)
    (fx / ".opal" / "AGENT.md").write_text("# AGENT")
    (fx / "tasks" / "001-task").mkdir(parents=True)
    (fx / "tasks" / "002-task").mkdir(parents=True)
    (fx / "tasks" / "backup" / "003-task").mkdir(parents=True)
    (fx / "tasks" / "backup" / "004-task").mkdir(parents=True)

    results = scan_projects(
        roots=[str(tmp_path)],
        depth=2,
        exclude=["node_modules", ".git", ".venv", "__pycache__"],
    )
    names = {r.name: r for r in results}
    assert "fx-opal-c" in names, "fx-opal-c 발견 실패"
    # tasks/ 직속 2건 + tasks/backup/ 하위 2건 = 4건. backup 폴더 자체는 세지 않는다.
    assert names["fx-opal-c"].task_count == 4, (
        f"2단 열거(tasks/ + tasks/backup/) 합산 불일치: {names['fx-opal-c'].task_count}"
    )


def test_scan_marks_non_opal(opal_workspace: Path) -> None:
    """[T021/L2-R1] 비OPAL 디렉토리는 is_opal=false"""
    from dashboard.backend.scanner import scan_projects

    results = scan_projects(
        roots=[str(opal_workspace)],
        depth=2,
        exclude=["node_modules", ".git", ".venv", "__pycache__"],
    )
    plain = next((r for r in results if r.name == "fx-plain"), None)
    assert plain is not None
    assert plain.is_opal is False
    assert plain.task_count == 0


# ─────────────────────────────────────────────────────────────────────────────
# [RED-118][S-16] resolve_task_dir 다중 허용 루트 (D-5, task 118)
#
# S-16(a) — 회귀 보호: `extra_task_roots` 미지정 호출은 현행과 완전히 동일해야 한다.
#   구현 전에도 통과해야 정상이다 (TASK.md C-1).
# S-16(b) — RED: `extra_task_roots`로 넘긴 realpath 화이트리스트 안의 태스크는
#   찾아야 하고 화이트리스트 밖은 거부해야 한다. 현재 `resolve_task_dir(project_path,
#   task_id)`는 `extra_task_roots` 키워드 인자 자체를 받지 않으므로(D-5 keyword-only
#   계약 미구현) TypeError로 실패하는 것이 RED 정상 상태다.
# ─────────────────────────────────────────────────────────────────────────────

def test_resolve_task_dir_without_extra_roots_unchanged(tmp_path: Path) -> None:
    """[RED-118][S-16a] 회귀 보호 — `extra_task_roots` 미지정 호출은 현행과 동일하다.
    구현 전에도 통과해야 정상(회귀 가드)."""
    from dashboard.backend.scanner import resolve_task_dir

    project = tmp_path / "fx-project"
    (project / "tasks" / "001-task").mkdir(parents=True)

    resolved = resolve_task_dir(str(project), "001-task")
    assert resolved == os.path.realpath(str(project / "tasks" / "001-task")), (
        "extra_task_roots 미지정 호출이 현행과 달라졌다"
    )

    # 경로 이탈 입력은 extra_task_roots 유무와 무관하게 현행처럼 거부된다.
    assert resolve_task_dir(str(project), "../etc") is None
    assert resolve_task_dir(str(project), "nonexistent-task") is None


def test_resolve_task_dir_extra_task_roots_whitelists_worktree_task(tmp_path: Path) -> None:
    """[RED-118][S-16b] D-5 keyword-only `extra_task_roots`— 화이트리스트 안의
    워크트리 태스크(registry active worktree `task_path`에서 파생한 루트)는 찾고,
    화이트리스트 밖 경로는 거부한다.

    RED 기대: 현재 `resolve_task_dir` 시그니처에는 `extra_task_roots`가 없으므로
    이 호출 자체가 TypeError(unexpected keyword argument)로 실패한다."""
    from dashboard.backend.scanner import resolve_task_dir

    project = tmp_path / "fx-project"
    (project / "tasks").mkdir(parents=True)

    worktree_tasks_root = tmp_path / "fx-worktree" / "tasks"
    worktree_tasks_root.mkdir(parents=True)
    (worktree_tasks_root / "118-worktree-task").mkdir(parents=True)

    outside_tasks_root = tmp_path / "fx-outside-not-whitelisted"
    (outside_tasks_root / "999-outside-task").mkdir(parents=True)

    whitelist = [os.path.realpath(str(worktree_tasks_root))]

    resolved = resolve_task_dir(
        str(project), "118-worktree-task", extra_task_roots=whitelist,
    )
    assert resolved == os.path.realpath(str(worktree_tasks_root / "118-worktree-task")), (
        "화이트리스트 안의 워크트리 태스크를 찾지 못했다"
    )

    rejected = resolve_task_dir(
        str(project), "999-outside-task", extra_task_roots=whitelist,
    )
    assert rejected is None, "화이트리스트 밖 경로가 거부되지 않았다"
