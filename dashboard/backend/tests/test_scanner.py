"""
@header {
  "module": "test_scanner",
  "layer": "test",
  "domain": "console",
  "description": "프로젝트 스캐너 RED-first 테스트 — S-1 시나리오 (L2/M1)",
  "exports": ["[T021/L2-R1] test_scan_finds_opal_projects", "[T021/L2-R1] test_scan_excludes_node_modules", "[T021/L2-R1] test_scan_depth_guard", "[T021/L2-R1] test_scan_marks_non_opal"],
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
