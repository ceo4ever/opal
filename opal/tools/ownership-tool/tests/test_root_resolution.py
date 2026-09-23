"""
@header {
  "module": "ownership_tool.tests.test_root_resolution",
  "layer": "test",
  "domain": "ownership",
  "description": "TASK-149 S-2/S-3/S-9. resolve_project_root(D-30b) 3단계(명시 오버라이드 → 조상 탐색 → None), 플랫폼 고유 CLAUDE_ 토큰의 claude_adapter.py 격리(AC-7/C-3), 어댑터 5종의 payload.get(\"cwd\") 잔존 금지(AC-6), ownership_core의 resolve_roots 추론 부재 AST 검사(C-4/C-5, resolve_project_root의 조상 탐색은 `.parents` 허용 대상이라 이 검사에서 제외)를 결정론 grep + AST 검사 + 실물 tmp_path 트리로 고정한다.",
  "exports": [],
  "depends": ["ownership_tool.ownership_core", "ownership_tool.claude_adapter"]
}
"""
from __future__ import annotations

import ast
import pathlib
import re
import subprocess
import sys

import pytest

_TESTS_DIR = pathlib.Path(__file__).resolve().parent
_TOOL_DIR = _TESTS_DIR.parent
_PKG_DIR = _TOOL_DIR / "ownership_tool"
_REPO_ROOT = _TOOL_DIR.parent.parent.parent

_ADAPTER_FILES = (
    "stop_hook.py",
    "session_start_hook.py",
    "heartbeat_hook.py",
    "session_end_hook.py",
    "pretooluse_guard_hook.py",
)


# ─────────────────────────────────────────────────────────────────────────────
# S-2 (AC-7, C-3) — claude_adapter.py 밖 CLAUDE_ 토큰 0건 + 신규 토큰도 claude_adapter 안에만
# ─────────────────────────────────────────────────────────────────────────────

def test_s2_claude_token_confined_to_claude_adapter_module():
    """S-2: `grep -rn 'CLAUDE_' ownership_tool/*.py | grep -v claude_adapter.py` 0행.

    TEST-SCENARIO.md ### S-2 절의 검사 명령을 그대로 재현한다. D-30d가 루트 해석의
    플랫폼 변수 의존을 없앤 뒤로 이 격리는 세션 ID·Stop 재차단 상한 변수에만 걸린다 —
    `claude_adapter`가 그 이름들을 소유하는 유일한 모듈이라는 계약이 S-2의 집행 대상이다.
    """
    for path in sorted(_PKG_DIR.glob("*.py")):
        if path.name == "claude_adapter.py":
            continue
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            assert "CLAUDE_" not in line, (
                f"S-2 위반 — {path.name}:{lineno}에 CLAUDE_ 토큰이 있다: {line!r}"
            )


# D-23 ②(`claude_adapter.PROJECT_DIR_ENV`·`project_dir_from_env` 존재 단정)를 굳혔던
# test_s2_project_dir_env_lives_only_in_claude_adapter는 D-30d가 그 의존 자체를 폐기하면서
# 삭제했다. S-2의 본래 계약(`grep -rn 'CLAUDE_' ownership_tool/*.py | grep -v
# claude_adapter.py` → 0행)은 위 test_s2_claude_token_confined_to_claude_adapter_module이
# 그대로 집행하므로 시나리오 커버리지에 구멍은 없다. 부재 단정으로 반전하지 않은 것은
# 나중에 다른 목적으로 그 이름이 필요해질 때 무관한 테스트가 깨지지 않게 하기 위함이다.


# ─────────────────────────────────────────────────────────────────────────────
# S-3 (AC-6) — 어댑터 5종 cwd 루트 채택 잔존 0건, 패키지 전체 1행만 잔존
# ─────────────────────────────────────────────────────────────────────────────

def _grep_cwd_adoption(paths):
    """`payload.get("cwd")` 매칭 중 `payload.get("cwd") or project_root`를 제외한 행."""
    hits = []
    for name in paths:
        path = _PKG_DIR / name
        if not path.exists():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if 'payload.get("cwd")' not in line:
                continue
            if 'payload.get("cwd") or project_root' in line:
                continue
            hits.append((path.name, lineno, line.strip()))
    return hits


def test_s3_adapters_have_no_bare_cwd_root_adoption():
    """S-3 ⑴: 어댑터 5파일에서 `payload.get("cwd")` 단독 루트 채택이 0건이다.

    어댑터는 루트를 스스로 만들지 않고 `resolve_project_root`가 준 값만 쓴다. 봉투 cwd는
    `payload.get("cwd") or project_root` 형태로 **판정 입력**으로만 남는다(D-30f·AC-6).
    """
    hits = _grep_cwd_adoption(_ADAPTER_FILES)
    assert hits == [], (
        f"S-3 위반 — 어댑터에 cwd 단독 루트 채택이 남아 있다: {hits}"
    )


def test_s3_package_wide_single_adoption_point_is_resolve_project_root():
    """S-3 ⑵: 패키지 전체에서 `payload.get("cwd")`(or project_root 제외) 매칭이 정확히
    1행이고, 그 1행이 `ownership_core.py`의 `resolve_project_root` 체인 안에 있다.

    그 1행이 패키지 전체에서 봉투 cwd를 루트 후보로 읽는 유일한 지점이다(AC-6).
    """
    all_files = sorted(p.name for p in _PKG_DIR.glob("*.py"))
    hits = _grep_cwd_adoption(all_files)
    assert len(hits) == 1, (
        f"S-3 위반 — 패키지 전체 cwd 단독 채택이 1행이 아니다: {hits}"
    )
    filename, lineno, _line = hits[0]
    assert filename == "ownership_core.py", (
        f"S-3 위반 — 유일한 채택 지점이 ownership_core.py가 아니다: {filename}:{lineno}"
    )

    core_src = (_PKG_DIR / "ownership_core.py").read_text(encoding="utf-8")
    tree = ast.parse(core_src)
    func_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert "resolve_project_root" in func_names, (
        "S-3 위반 — ownership_core.resolve_project_root가 정의되지 않았다"
    )


# ─────────────────────────────────────────────────────────────────────────────
# S-9 (C-4, C-5) — resolve_roots 3분기 보존 + resolve_project_root 4단계 체인 + AST 무추론 검사
# ─────────────────────────────────────────────────────────────────────────────

_FORBIDDEN_ATTRS = {"parents"}
_FORBIDDEN_CALLS = {"walk", "iterdir"}


def _assert_no_inference(func_src, func_name):
    """`.parents`·`os.walk`/`iterdir` 순회로 루트를 추론하지 않는지만 검사한다.

    `.opal-worktrees`는 고정 서브경로 구성(`base / ".opal-worktrees" / ".meta"`)에
    정당하게 쓰이므로(resolve_roots ①) 문자열 리터럴 자체는 금지 대상이 아니다 — 금지
    대상은 그 문자열로 cwd를 **탐색**(os.walk/iterdir/부모 순회)하는 행위다(C-5).
    """
    tree = ast.parse(func_src)
    func_def = tree.body[0]
    for node in ast.walk(func_def):
        if isinstance(node, ast.Attribute) and node.attr in _FORBIDDEN_ATTRS:
            pytest.fail(f"{func_name}가 금지된 속성 `.{node.attr}`을 쓴다(C-5)")
        if isinstance(node, ast.Attribute) and node.attr in _FORBIDDEN_CALLS:
            pytest.fail(f"{func_name}가 금지된 호출 `.{node.attr}(...)`을 쓴다(C-5)")


def _extract_function_source(module_src, func_name):
    tree = ast.parse(module_src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            return ast.get_source_segment(module_src, node)
    return None


def test_s9_resolve_roots_three_branches_preserved():
    """S-9 ⑴: 기존 resolve_roots 3분기 시그니처·동작을 기대값 수정 없이 재확인한다."""
    from ownership_tool import ownership_core  # noqa: PLC0415

    # ① 허브형 — <cwd>/.opal-worktrees/.meta/ 존재
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        hub_root = pathlib.Path(tmp) / "hub"
        (hub_root / ".opal-worktrees" / ".meta").mkdir(parents=True)
        result = ownership_core.resolve_roots(hub_root)
        assert result["ok"] is True
        assert result["kind"] == "hub"
        assert result["allocator_root"] == str(hub_root)

    # ② 워크트리형 — <cwd>/.opal/task-ownership.json 사본 존재
    import json

    with tempfile.TemporaryDirectory() as tmp:
        wt_root = pathlib.Path(tmp) / "wt"
        (wt_root / ".opal").mkdir(parents=True)
        (wt_root / ".opal" / "task-ownership.json").write_text(
            json.dumps({"allocator_root": str(wt_root.parent), "task_path": "/x/task"}),
            encoding="utf-8",
        )
        result = ownership_core.resolve_roots(wt_root)
        assert result["ok"] is True
        assert result["kind"] == "worktree"
        assert result["allocator_root"] == str(wt_root.parent)

    # ③ 무증거형 — 둘 다 없음
    with tempfile.TemporaryDirectory() as tmp:
        bare_root = pathlib.Path(tmp) / "bare"
        bare_root.mkdir(parents=True)
        result = ownership_core.resolve_roots(bare_root)
        assert result["ok"] is False
        assert result["diagnostic"] == "roots_unresolved"

    core_src = (_PKG_DIR / "ownership_core.py").read_text(encoding="utf-8")
    func_src = _extract_function_source(core_src, "resolve_roots")
    assert func_src is not None
    _assert_no_inference(func_src, "resolve_roots")


def test_s9_resolve_project_root_ancestor_search_four_cases():
    """S-9 (D-30b/c): resolve_project_root의 3단계 — ① 명시 오버라이드
    `OPAL_PROJECT_ROOT` ② 봉투 `cwd`부터 조상 탐색(`.opal/MEMORY.json` 또는
    `.opal/AGENT.md`를 파일로 가진 첫 디렉토리) ③ `None`.

    조상 탐색은 `.parents`를 정당하게 쓰므로(D-30b) 이 함수에는 `_assert_no_inference`를
    걸지 않는다 — 그 금지는 `resolve_roots`·`resolve_hub` 축 전용이다(C-5 정정).

    ⑵가 D-30c의 자기증식 방어를(오염된 `<하위>/.opal/run/.runtime/`는 앵커가 아니다),
    ⑶이 "가장 가까운 조상" 규칙이 허브보다 워크트리를 우선함을 고정한다.
    """
    import tempfile

    from ownership_tool import ownership_core  # noqa: PLC0415

    resolve_project_root = ownership_core.resolve_project_root

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = pathlib.Path(tmp)

        # ① 명시 오버라이드 — 존재하는 디렉토리면 조상 탐색보다 우선 채택
        override_root = tmp_path / "override-root"
        override_root.mkdir()
        got = resolve_project_root(
            {"cwd": str(tmp_path / "elsewhere")},
            env={"OPAL_PROJECT_ROOT": str(override_root)},
        )
        assert got == str(override_root)

        # ① 존재하지 않는 경로는 무시하고 다음 단계(조상 탐색)로 넘어간다
        normal_root = tmp_path / "case1-root"
        (normal_root / ".opal").mkdir(parents=True)
        (normal_root / ".opal" / "MEMORY.json").write_text("{}", encoding="utf-8")
        nested = normal_root / "sub" / "nested"
        nested.mkdir(parents=True)
        missing = tmp_path / "does-not-exist"
        got = resolve_project_root(
            {"cwd": str(nested)},
            env={"OPAL_PROJECT_ROOT": str(missing)},
        )
        assert got == str(normal_root)

        # ⑴ 평범한 프로젝트 — <root>/.opal/MEMORY.json + <root>/sub/nested, cwd=nested
        got = resolve_project_root({"cwd": str(nested)}, env={})
        assert got == str(normal_root)

        # ⑵ 오염만 있는 하위 — <root>/.opal/MEMORY.json +
        # <root>/sub/.opal/run/.runtime/(디렉토리만, 마커 파일 없음), cwd=<root>/sub
        polluted_root = tmp_path / "case2-root"
        (polluted_root / ".opal").mkdir(parents=True)
        (polluted_root / ".opal" / "MEMORY.json").write_text("{}", encoding="utf-8")
        polluted_sub = polluted_root / "sub"
        (polluted_sub / ".opal" / "run" / ".runtime").mkdir(parents=True)
        got = resolve_project_root({"cwd": str(polluted_sub)}, env={})
        assert got == str(polluted_root), (
            "S-9 위반(D-30c) — 오염된 하위 .opal/run/.runtime/ 디렉토리만으로 "
            "앵커가 승격되면 안 된다"
        )

        # ⑶ 워크트리 중첩 — <hub>/.opal/MEMORY.json +
        # <hub>/.opal-worktrees/wt/.opal/AGENT.md + <hub>/.opal-worktrees/wt/sub/,
        # cwd=<hub>/.opal-worktrees/wt/sub → 허브가 아니라 워크트리가 먼저 잡힌다
        hub_root = tmp_path / "hub"
        (hub_root / ".opal").mkdir(parents=True)
        (hub_root / ".opal" / "MEMORY.json").write_text("{}", encoding="utf-8")
        wt_root = hub_root / ".opal-worktrees" / "wt"
        (wt_root / ".opal").mkdir(parents=True)
        (wt_root / ".opal" / "AGENT.md").write_text("# agent", encoding="utf-8")
        wt_sub = wt_root / "sub"
        wt_sub.mkdir(parents=True)
        got = resolve_project_root({"cwd": str(wt_sub)}, env={})
        assert got == str(wt_root), (
            "S-9 위반 — 가장 가까운 조상(워크트리)이 아니라 허브가 채택됐다"
        )

        # ⑷ 앵커 전무 — 마커 없는 빈 트리. pytest tmp_path 바깥의 실제 조상에
        # .opal/MEMORY.json이 있을 수 있으므로, 결과가 이 tmp_path 트리 밖으로
        # 새어나가지 않았는지도 함께 확인한다.
        bare_root = tmp_path / "bare-root"
        bare_sub = bare_root / "sub"
        bare_sub.mkdir(parents=True)
        got = resolve_project_root({"cwd": str(bare_sub)}, env={})
        if got is not None:
            assert not str(got).startswith(str(tmp_path)), (
                "S-9 ⑷ 위반 — tmp_path 내부에는 앵커가 없는데 tmp_path 내부 경로가 "
                f"채택됐다: {got}"
            )
        else:
            assert got is None

        # ③ 그 외(빈 payload) — None
        got = resolve_project_root({}, env={})
        assert got is None


def test_s9_resolve_hub_caller_argument_only_contract_still_holds():
    """S-9: resolver.resolve_hub의 "hub_root는 호출자 인자만" 계약 집행 테스트가 계속
    통과해야 한다(기존 test_resolver.py의 관련 테스트를 회귀로 재확인)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         str(_TESTS_DIR / "test_resolver.py"),
         "-k", "no_filesystem_scan or resolve_hub",
         "-q"],
        cwd=str(_TOOL_DIR),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"S-9 위반 — resolver 계약 회귀 실패:\nstdout={result.stdout}\nstderr={result.stderr}"
    )
