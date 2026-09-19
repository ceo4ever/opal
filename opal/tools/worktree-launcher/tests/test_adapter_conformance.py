# @header
# module: worktree_launcher.tests.test_adapter_conformance
# layer: test
# domain: worktree-launcher
# description: 터미널 adapter 공통 적합성 스위트(S-3). D-J가 고정한 3동사(launch·read·close) 보고 스키마를 어댑터 모듈 파라미터화로 집행한다 — 검사 7항목은 (1) 3동사 존재·호출 가능 (2) 보고 dict 공통 필수 키·타입 (3) 실패가 예외가 아니라 `exit_code != 0` dict (4) `fallback_attempted` 항상 False (5) `launch` argv에 worktree/checkout 생성 서브명령 0건 (6) 성공 launch 보고가 `launcher_core.build_launch_receipt()`·`build_prompt_receipt()` 둘 다 non-None (7) `close` 인자 배타성이다. 대상 어댑터는 `CONFORMANCE_ADAPTERS` 1개 상수가 소유하고 fixture 매핑은 `ADAPTER_FIXTURES`가 소유한다 — 새 어댑터의 추가 비용은 이 두 상단 상수에 자기 이름과 fixture를 등록해 전건 통과시키는 것이 전부다(AC-8). 이번 범위의 대상은 `orca` 하나이며 `generic`·`opal_agent_fallback`은 3동사를 갖추지 않아 대상이 아니다(C-1). 더해 S-14의 정적 검사(C-1 어댑터 모듈 집합 고정·C-2 상속 계층 0건·C-4 worktree/checkout 생성 문자열 0건·C-5 registry 메타 직접 쓰기 0건 + `ownership-set` 단일 경유)를 grep이 아닌 AST로 이 파일이 소유한다. 실 CLI는 한 번도 호출하지 않는다 — 어댑터의 subprocess seam만 대체하고 응답은 ownership-tool fixtures/launcher 실측 3종을 `{WT}` 치환해 쓴다.
# exports: (none — pytest module)
# depends: worktree_launcher.adapters.*, worktree_launcher.launcher_core, ownership-tool fixtures/launcher, tests/conftest.load_launcher_fixture
"""어댑터 적합성 스위트 — 새 어댑터가 통과해야 할 계약을 이 파일이 정의한다.

이 스위트는 **목킹 기반**이다. 어댑터가 실물 orca CLI의 현재 응답 모양과 여전히
맞는지(버전 드리프트)는 이 스위트가 잡지 않는다 — 그것은 `OPAL_LIVE_ORCA=1`일 때만
도는 live 테스트(`test_adapter_orca.py`, W-8 소유)가 잡는다. 여기서 쓰는 fixture는
실측 캡처본이므로 "구현이 가정한 모양"을 스스로 넣어 파싱하는 순환은 없지만,
캡처 시점 이후의 드리프트는 live 대조만이 관측할 수 있다.
"""
from __future__ import annotations

import ast
import importlib
import json
import pathlib
import subprocess

import pytest

from conftest import FIXTURES_ROOT, load_launcher_fixture

# ─────────────────────────────────────────────────────────────────────────────
# 새 어댑터의 추가 비용은 아래 두 상수뿐이다
# ─────────────────────────────────────────────────────────────────────────────

#: 적합성 계약을 집행할 어댑터 모듈명. 새 어댑터는 여기에 1줄을 더한다.
CONFORMANCE_ADAPTERS = [
    "orca",
]

#: 어댑터별 실측 응답 fixture와 subprocess seam 이름.
ADAPTER_FIXTURES = {
    "orca": {
        "subprocess_seam": "_run_subprocess",
        "launch": "orca-json-response.json",
        "read": "orca-terminal-read-response.json",
        "close": "orca-terminal-close-response.json",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# D-J 보고 스키마
# ─────────────────────────────────────────────────────────────────────────────

COMMON_REPORT_TYPES = {"adapter": str, "exit_code": int, "fallback_attempted": bool}

VERB_REPORT_KEYS = {
    "launch": (
        "adapter_handle",
        "reported_cwd",
        "launched_at",
        "prompt_id",
        "submitted_at",
        "prompt_receipt_source",
        "launch_mode",
    ),
    "read": ("handle", "content", "next_cursor", "source"),
    "close": ("scope", "closed"),
}

VERBS = ("launch", "read", "close")

CLOSE_SCOPES = ("terminal", "worktree_all")

#: C-4 — worktree·checkout을 새로 만드는 서브명령. argv에도 소스 문자열에도 0건이어야 한다.
FORBIDDEN_ARGV_PAIRS = (("worktree", "add"), ("worktree", "create"), ("checkout", "-b"))
FORBIDDEN_SOURCE_STRINGS = ("worktree add", "worktree create", "checkout -b")

#: C-1 — `adapters/`의 허용 모듈 집합. 신규 모듈 0건·`cmux.py` 부재를 이 집합이 집행한다.
ALLOWED_ADAPTER_MODULES = {
    "__init__.py",
    "generic.py",
    "opal_agent_fallback.py",
    "orca.py",
}
#: C-1 — 이번 태스크에서 손대지 않기로 한 어댑터 모듈(범위 밖).
UNTOUCHED_ADAPTER_MODULES = ("generic.py", "opal_agent_fallback.py")

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent.parent / "worktree_launcher"
ADAPTERS_DIR = PACKAGE_ROOT / "adapters"

HANDLE_FOR_TESTS = "term_6281f52a-c804-4fca-8aea-347a2b1f6203"


# ─────────────────────────────────────────────────────────────────────────────
# 헬퍼 — 실 CLI는 호출하지 않는다
# ─────────────────────────────────────────────────────────────────────────────


def _import_adapter(name: str):
    return importlib.import_module(f"worktree_launcher.adapters.{name}")


def _worktree_root(tmp_path: pathlib.Path) -> pathlib.Path:
    root = tmp_path / "hub" / ".opal-worktrees" / "task_145"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _fixture(adapter: str, verb: str, tmp_path, worktree_root) -> dict:
    """fixtures/README.md 계약대로 `{WT}`를 실제 워크트리 경로로 치환해 읽는다."""
    return load_launcher_fixture(
        ADAPTER_FIXTURES[adapter][verb], hub=tmp_path, wt_parent=worktree_root
    )


class _Completed:
    """`subprocess.run` 반환값 중 어댑터가 읽는 3필드만 가진 대역."""

    def __init__(self, returncode, stdout, stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _install_seam(monkeypatch, module, response, *, returncode=0, stderr=""):
    """어댑터의 subprocess seam을 대체하고 관측된 argv 목록을 돌려준다."""
    seam = ADAPTER_FIXTURES[module.ADAPTER_NAME]["subprocess_seam"]
    calls: list[list[str]] = []

    def fake_run(argv, **kwargs):
        calls.append([str(token) for token in argv])
        stdout = response if isinstance(response, str) else json.dumps(response)
        return _Completed(returncode, stdout, stderr)

    monkeypatch.setattr(module, seam, fake_run)
    return calls


def _invoke_verb(module, verb, *, tmp_path, worktree_root):
    """D-J가 고정한 시그니처로 동사 1개를 호출한다 — 어댑터별 분기를 두지 않는다."""
    if verb == "launch":
        return module.launch(str(worktree_root), "claude \"이어서 수행\"")
    if verb == "read":
        return module.read(HANDLE_FOR_TESTS, limit=10)
    return module.close(handle=HANDLE_FOR_TESTS)


def _success_report(module, verb, monkeypatch, tmp_path):
    worktree_root = _worktree_root(tmp_path)
    response = _fixture(module.ADAPTER_NAME, verb, tmp_path, worktree_root)
    calls = _install_seam(monkeypatch, module, response)
    report = _invoke_verb(module, verb, tmp_path=tmp_path, worktree_root=worktree_root)
    return report, calls


# ─────────────────────────────────────────────────────────────────────────────
# 검사 1 — 3동사 존재·호출 가능
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("adapter", CONFORMANCE_ADAPTERS)
def test_adapter_exposes_three_verbs(adapter):
    module = _import_adapter(adapter)

    assert module.ADAPTER_NAME == adapter
    for verb in VERBS:
        assert callable(getattr(module, verb, None)), f"{adapter}.{verb} 미노출"


@pytest.mark.parametrize("adapter", CONFORMANCE_ADAPTERS)
def test_adapter_registers_its_own_fixtures(adapter):
    """어댑터 등록은 상단 2상수로 끝난다 — 스위트 본문에 어댑터 고유 분기가 없다."""
    entry = ADAPTER_FIXTURES[adapter]

    assert set(entry) == {"subprocess_seam", *VERBS}
    for verb in VERBS:
        fixture_path = FIXTURES_ROOT / entry[verb]
        assert fixture_path.is_file(), f"{adapter}.{verb} fixture 부재: {entry[verb]}"


# ─────────────────────────────────────────────────────────────────────────────
# 검사 2 + 4 — 보고 dict 공통 필수 키·타입, 동사별 추가 키, fallback_attempted False
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("adapter", CONFORMANCE_ADAPTERS)
@pytest.mark.parametrize("verb", VERBS)
def test_success_report_schema(adapter, verb, monkeypatch, tmp_path):
    module = _import_adapter(adapter)

    report, _calls = _success_report(module, verb, monkeypatch, tmp_path)

    assert isinstance(report, dict)
    for key, expected_type in COMMON_REPORT_TYPES.items():
        assert key in report, f"{adapter}.{verb} 보고에 공통 키 {key} 부재"
        # bool은 int의 서브클래스다 — exit_code가 True/False로 오는 것을 통과시키지 않는다.
        assert isinstance(report[key], expected_type)
        if expected_type is int:
            assert not isinstance(report[key], bool)
    assert report["adapter"] == adapter
    assert report["exit_code"] == 0
    for key in VERB_REPORT_KEYS[verb]:
        assert key in report, f"{adapter}.{verb} 보고에 동사 키 {key} 부재"

    if verb == "close":
        assert report["scope"] in CLOSE_SCOPES
        assert isinstance(report["closed"], list)


@pytest.mark.parametrize("adapter", CONFORMANCE_ADAPTERS)
@pytest.mark.parametrize("verb", VERBS)
def test_fallback_attempted_is_always_false(adapter, verb, monkeypatch, tmp_path):
    """폴백 선택은 호출자 책임이다 — 어댑터는 성공에서도 실패에서도 시도하지 않는다."""
    module = _import_adapter(adapter)

    success, _calls = _success_report(module, verb, monkeypatch, tmp_path)
    assert success["fallback_attempted"] is False

    worktree_root = _worktree_root(tmp_path)
    _install_seam(monkeypatch, module, "", returncode=1, stderr="boom")
    failure = _invoke_verb(
        module, verb, tmp_path=tmp_path, worktree_root=worktree_root
    )
    assert failure["fallback_attempted"] is False


# ─────────────────────────────────────────────────────────────────────────────
# 검사 3 — 실패는 예외가 아니라 exit_code != 0 dict다
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("adapter", CONFORMANCE_ADAPTERS)
@pytest.mark.parametrize("verb", VERBS)
@pytest.mark.parametrize("mode", ["nonzero_exit", "unparsable_stdout", "cli_missing"])
def test_failure_is_a_report_not_an_exception(
    adapter, verb, mode, monkeypatch, tmp_path
):
    module = _import_adapter(adapter)
    worktree_root = _worktree_root(tmp_path)

    if mode == "cli_missing":
        seam = ADAPTER_FIXTURES[adapter]["subprocess_seam"]

        def raise_oserror(argv, **kwargs):
            raise OSError(2, "No such file or directory")

        monkeypatch.setattr(module, seam, raise_oserror)
    elif mode == "nonzero_exit":
        _install_seam(monkeypatch, module, "", returncode=1, stderr="orca failed")
    else:
        _install_seam(monkeypatch, module, "not json at all", returncode=0)

    report = _invoke_verb(module, verb, tmp_path=tmp_path, worktree_root=worktree_root)

    assert isinstance(report, dict), f"{adapter}.{verb}가 dict 대신 {type(report)} 반환"
    assert report["exit_code"] != 0
    assert isinstance(report["exit_code"], int)
    assert report["adapter"] == adapter
    assert report["failure_reason"]
    assert report["detail"]
    assert report["fallback_attempted"] is False


# ─────────────────────────────────────────────────────────────────────────────
# 검사 5 — launch argv에 worktree/checkout 생성 서브명령 0건
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("adapter", CONFORMANCE_ADAPTERS)
def test_launch_argv_never_creates_a_worktree(adapter, monkeypatch, tmp_path):
    """워크트리·브랜치 생성의 단일 소유자는 worktree-tool이다(C-4)."""
    module = _import_adapter(adapter)

    _report, calls = _success_report(module, "launch", monkeypatch, tmp_path)

    assert calls, "launch가 subprocess seam을 한 번도 호출하지 않았다"
    for argv in calls:
        normalized = [token.lstrip("-") for token in argv]
        pairs = set(zip(normalized, normalized[1:]))
        for forbidden in FORBIDDEN_ARGV_PAIRS:
            assert forbidden not in pairs, f"{adapter} launch argv에 {forbidden}: {argv}"


# ─────────────────────────────────────────────────────────────────────────────
# 검사 6 — 성공 launch 보고가 receipt 2종을 둘 다 만든다
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("adapter", CONFORMANCE_ADAPTERS)
def test_success_launch_builds_both_receipts(adapter, monkeypatch, tmp_path):
    from worktree_launcher import launcher_core

    module = _import_adapter(adapter)

    report, _calls = _success_report(module, "launch", monkeypatch, tmp_path)

    assert launcher_core.build_launch_receipt(report) is not None
    assert launcher_core.build_prompt_receipt(report) is not None


# ─────────────────────────────────────────────────────────────────────────────
# 검사 7 — close 인자 배타성
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("adapter", CONFORMANCE_ADAPTERS)
@pytest.mark.parametrize(
    "kwargs, expected_scope",
    [
        ({"handle": HANDLE_FOR_TESTS}, "terminal"),
        ({"worktree_root": "{WT}", "all": True}, "worktree_all"),
    ],
)
def test_close_accepts_exactly_one_scope(
    adapter, kwargs, expected_scope, monkeypatch, tmp_path
):
    module = _import_adapter(adapter)
    worktree_root = _worktree_root(tmp_path)
    response = _fixture(adapter, "close", tmp_path, worktree_root)
    _install_seam(monkeypatch, module, response)

    call_kwargs = {
        key: (str(worktree_root) if value == "{WT}" else value)
        for key, value in kwargs.items()
    }
    report = module.close(**call_kwargs)

    assert report["exit_code"] == 0
    assert report["scope"] == expected_scope


@pytest.mark.parametrize("adapter", CONFORMANCE_ADAPTERS)
@pytest.mark.parametrize("kwargs", [{"both": True}, {}])
def test_close_rejects_ambiguous_scope(adapter, kwargs, monkeypatch, tmp_path):
    """둘 다 주거나 둘 다 주지 않으면 대상을 고를 수 없다 — 예외가 아니라 실패 dict다."""
    module = _import_adapter(adapter)
    worktree_root = _worktree_root(tmp_path)
    calls = _install_seam(monkeypatch, module, {"ok": True, "result": {"close": {}}})

    if kwargs.get("both"):
        report = module.close(handle=HANDLE_FOR_TESTS, worktree_root=str(worktree_root))
    else:
        report = module.close()

    assert isinstance(report, dict)
    assert report["exit_code"] != 0
    assert report["failure_reason"]
    assert report["detail"]
    assert report["fallback_attempted"] is False
    assert calls == [], "인자 위반인데 CLI를 호출했다"


# ─────────────────────────────────────────────────────────────────────────────
# S-14 — 정적 검사(C-1·C-2·C-4·C-5). grep이 아니라 AST로 본다.
# ─────────────────────────────────────────────────────────────────────────────


def _package_sources() -> list[pathlib.Path]:
    return sorted(
        path
        for path in PACKAGE_ROOT.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def _parse(path: pathlib.Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _docstring_nodes(tree: ast.Module) -> set[int]:
    """docstring으로 쓰인 문자열 상수의 id 집합 — @header 서술은 코드가 아니다."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            body = getattr(node, "body", None)
            if not body:
                continue
            first = body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                if isinstance(first.value.value, str):
                    ids.add(id(first.value))
    return ids


def _code_strings(tree: ast.Module) -> list[str]:
    """docstring을 뺀 문자열 상수 — 실제 실행에 쓰이는 리터럴만 남는다."""
    skip = _docstring_nodes(tree)
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in skip
    ]


def test_c1_adapter_module_set_is_frozen():
    """신규 어댑터 모듈 0건이고 `cmux.py`는 존재하지 않는다."""
    present = {
        path.name for path in ADAPTERS_DIR.glob("*.py") if path.name != "__pycache__"
    }

    assert present == ALLOWED_ADAPTER_MODULES
    assert not (ADAPTERS_DIR / "cmux.py").exists()


def test_c1_out_of_scope_adapters_are_untouched():
    """`generic.py`·`opal_agent_fallback.py`는 이번 태스크의 변경 대상이 아니다."""
    try:
        repo_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(PACKAGE_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except OSError:  # git 부재 환경
        pytest.skip("git을 실행할 수 없는 환경")
    if repo_root.returncode != 0:
        pytest.skip("git 저장소가 아니다")

    paths = [str(ADAPTERS_DIR / name) for name in UNTOUCHED_ADAPTER_MODULES]
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=repo_root.stdout.strip(),
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert status.returncode == 0
    assert status.stdout.strip() == "", f"범위 밖 어댑터가 변경됐다: {status.stdout}"


def test_c2_adapters_declare_no_class_or_inheritance():
    """모듈 함수 seam을 유지한다 — 상속 계층을 만들지 않는다(C-2)."""
    for path in sorted(ADAPTERS_DIR.glob("*.py")):
        tree = _parse(path)
        classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        assert classes == [], f"{path.name}에 class 선언: {[c.name for c in classes]}"
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.module != "abc", f"{path.name}가 abc를 import한다"
            if isinstance(node, ast.Import):
                assert all(
                    alias.name != "abc" for alias in node.names
                ), f"{path.name}가 abc를 import한다"
            if isinstance(node, ast.Name):
                assert node.id not in ("ABC", "ABCMeta"), f"{path.name}에 {node.id}"


def test_c4_package_never_creates_worktrees_or_branches():
    """worktree·브랜치 생성은 worktree-tool의 소유다 — launcher 실행 문자열 0건(C-4)."""
    for path in _package_sources():
        for literal in _code_strings(_parse(path)):
            for forbidden in FORBIDDEN_SOURCE_STRINGS:
                assert forbidden not in literal, f"{path.name}: {literal!r}"


def test_c5_package_has_no_private_registry_writer():
    """registry 메타 직접 쓰기 0건 — 상태 전이는 `ownership-set` 경유가 유일하다(C-5)."""
    for path in _package_sources():
        tree = _parse(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id != "write_meta_atomic", f"{path.name}: write_meta_atomic"
                if func.id == "open":
                    modes = [
                        arg.value
                        for arg in list(node.args[1:2])
                        + [kw.value for kw in node.keywords if kw.arg == "mode"]
                        if isinstance(arg, ast.Constant)
                        and isinstance(arg.value, str)
                    ]
                    assert all(
                        "w" not in mode and "a" not in mode and "+" not in mode
                        for mode in modes
                    ), f"{path.name}: 쓰기 모드 open()"
            if isinstance(func, ast.Attribute):
                assert func.attr not in (
                    "write_text",
                    "write_bytes",
                    "write_meta_atomic",
                ), f"{path.name}: {func.attr}()"


def test_c5_state_transition_goes_through_ownership_set():
    """positive 대조 — 상태 전이 subprocess argv에 `ownership-set`이 실제로 실린다."""
    core = PACKAGE_ROOT / "launcher_core.py"

    literals = _code_strings(_parse(core))

    assert "ownership-set" in literals
