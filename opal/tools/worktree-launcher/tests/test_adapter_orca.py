# @header
# module: worktree_launcher.tests.test_adapter_orca
# layer: test
# domain: worktree-launcher
# description: worktree_launcher.adapters.orca의 3동사(launch·read·close) 공개 계약 검증. S-1은 W-1이 캡처한 실물 `create` 봉투(`result.terminal`)에서 `adapter_handle`·`reported_cwd`가 둘 다 채워지는지와 변형 3종(`result` 부재 / `worktreeId`에 `::` 없음 / 뒤쪽 비절대)에서 값을 지어내지 않고 None을 돌려주는지를 본다. S-2는 prompt receipt 원천이 `launch_argv`이고 `prompt_id`가 전송 명령 sha256 앞 16자임을 보고 dict와 `launcher_core.build_prompt_receipt()`로 확인하며, 구형 토큰 잔존 0건을 패키지 전체 grep으로 정적 검사한다. S-13은 `close`의 2스코프 argv 배타성과 인자 4조합을 본다. S-10은 이 모듈에서 유일하게 실제 orca를 호출하는 live 대조 1건이다 — `orca`가 PATH에 있고 `OPAL_LIVE_ORCA=1`일 때만 돌고(그 외 skip) 대상 워크트리는 `OPAL_LIVE_ORCA_WORKTREE` 또는 `orca worktree list --json`에서 레포 루트와 일치하는 항목으로만 정하며 워크트리를 새로 만들지 않는다. 나머지 전건은 실제 orca를 호출하지 않는다 — `_run_subprocess` seam만 대체하고 응답은 ownership-tool fixtures/launcher 실측 3종을 `{WT}` 치환해 쓴다.
# exports: (none — pytest module)
# depends: worktree_launcher.adapters.orca, worktree_launcher.launcher_core, ownership-tool fixtures/launcher, tests/conftest.load_launcher_fixture, orca CLI(live 대조 S-10 한정)
"""orca adapter 단위 테스트 — fixture 기반. 실 CLI 호출은 opt-in live 대조 1건(S-10)뿐이다."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess

import pytest

from conftest import load_launcher_fixture

CREATE_FIXTURE = "orca-json-response.json"
READ_FIXTURE = "orca-terminal-read-response.json"
CLOSE_FIXTURE = "orca-terminal-close-response.json"

PACKAGE_ROOT = (
    pathlib.Path(__file__).resolve().parent.parent / "worktree_launcher"
)


def _worktree_root(tmp_path: pathlib.Path) -> pathlib.Path:
    root = tmp_path / "hub" / ".opal-worktrees" / "task_145"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _fixture(name: str, tmp_path: pathlib.Path, worktree_root: pathlib.Path) -> dict:
    """fixtures/README.md 계약대로 `{WT}`를 실제 워크트리 경로로 치환해 읽는다."""
    return load_launcher_fixture(name, hub=tmp_path, wt_parent=worktree_root)


def _stub_run(recorded: dict, response, returncode: int = 0):
    def fake_run(argv, **kwargs):
        recorded.setdefault("calls", []).append(list(argv))
        recorded["args"] = list(argv)

        class _P:
            pass

        _P.returncode = returncode
        _P.stdout = response if isinstance(response, str) else json.dumps(response)
        _P.stderr = ""
        return _P()

    return fake_run


# ─────────────────────────────────────────────────────────────────────────────
# S-1 — 실물 `result.terminal` 봉투 파싱과 변형 3종의 값 지어내기 금지
# ─────────────────────────────────────────────────────────────────────────────


def test_parse_response_reads_real_result_terminal_envelope(tmp_path):
    """실물 fixture에서 `adapter_handle`이 `term_` 핸들로, `reported_cwd`가 워크트리
    절대경로로 **둘 다** 채워진다(S-1)."""
    from worktree_launcher.adapters import orca

    worktree_root = _worktree_root(tmp_path)
    response = _fixture(CREATE_FIXTURE, tmp_path, worktree_root)

    report = orca.parse_response(response)

    assert report["adapter_handle"] == response["result"]["terminal"]["handle"]
    assert report["adapter_handle"].startswith("term_")
    assert report["reported_cwd"] == str(worktree_root)
    assert pathlib.PurePath(report["reported_cwd"]).is_absolute()


def test_parse_response_missing_result_key_invents_nothing(tmp_path):
    """`result` 키가 없으면 handle·cwd 둘 다 None(S-1 변형 1)."""
    from worktree_launcher.adapters import orca

    report = orca.parse_response({"ok": True, "id": "x", "_meta": {}})

    assert report["adapter_handle"] is None
    assert report["reported_cwd"] is None


def test_parse_response_worktree_id_without_separator_yields_none(tmp_path):
    """`worktreeId`에 `::`가 없으면 경로를 지어내지 않고 `reported_cwd=None`(S-1 변형 2)."""
    from worktree_launcher.adapters import orca

    worktree_root = _worktree_root(tmp_path)
    response = _fixture(CREATE_FIXTURE, tmp_path, worktree_root)
    response["result"]["terminal"]["worktreeId"] = str(worktree_root)

    report = orca.parse_response(response)

    assert report["adapter_handle"] is not None
    assert report["reported_cwd"] is None


def test_parse_response_non_absolute_tail_yields_none(tmp_path):
    """첫 `::` 뒤쪽이 절대경로가 아니면 `reported_cwd=None`(S-1 변형 3)."""
    from worktree_launcher.adapters import orca

    worktree_root = _worktree_root(tmp_path)
    response = _fixture(CREATE_FIXTURE, tmp_path, worktree_root)
    response["result"]["terminal"]["worktreeId"] = "ce5d0068::relative/path"

    report = orca.parse_response(response)

    assert report["reported_cwd"] is None


def test_parse_response_splits_worktree_id_only_once(tmp_path):
    """분리는 **첫** `::` 1회다 — 뒤쪽에 `::`가 더 있어도 경로 성분으로 보존된다(D-D)."""
    from worktree_launcher.adapters import orca

    worktree_root = _worktree_root(tmp_path)
    response = _fixture(CREATE_FIXTURE, tmp_path, worktree_root)
    response["result"]["terminal"]["worktreeId"] = f"repo-id::{worktree_root}::extra"

    report = orca.parse_response(response)

    assert report["reported_cwd"] == f"{worktree_root}::extra"


def test_task163_s4_status_requires_stale_show_and_empty_list_for_absence(monkeypatch, tmp_path):
    """S-4: Orca only reports absent after both stale-handle and empty-worktree observations."""
    from worktree_launcher.adapters import orca

    root = _worktree_root(tmp_path)
    monkeypatch.setattr(orca, "_run_subprocess", _stub_run({}, {"ok": False, "error": "stale"}, returncode=1))
    report = orca.status_worktree(root)
    assert report["status"] == "unknown"


def test_task163_s4_status_non_object_json_is_unknown(monkeypatch, tmp_path):
    """A syntactically valid JSON scalar or list cannot prove terminal state."""
    from worktree_launcher.adapters import orca

    root = _worktree_root(tmp_path)
    monkeypatch.setattr(orca, "_run_subprocess", _stub_run({}, []))
    report = orca.status("term-unknown", worktree_root=root)
    assert report["status"] == "unknown"
    assert report["reason"] == "response_invalid"


def test_status_closed_orphan_requires_list_to_lack_handle_and_pty(monkeypatch, tmp_path):
    from worktree_launcher.adapters import orca

    root = _worktree_root(tmp_path)
    responses = iter([
        {"ok": True, "result": {"terminal": {
            "handle": "term-closed", "ptyId": "pty-closed", "orphaned": True,
            "connected": False, "exitCause": {"kind": "operator_close"},
        }}},
        {"ok": True, "result": {"terminals": []}},
    ])
    monkeypatch.setattr(orca, "_run_subprocess", lambda _argv: type("P", (), {
        "returncode": 0, "stdout": json.dumps(next(responses)), "stderr": "",
    })())
    assert orca.status("term-closed", worktree_root=root)["status"] == "absent"


def test_status_closed_orphan_with_listed_same_pty_is_unknown(monkeypatch, tmp_path):
    from worktree_launcher.adapters import orca

    root = _worktree_root(tmp_path)
    responses = iter([
        {"ok": True, "result": {"terminal": {
            "handle": "term-closed", "ptyId": "pty-closed", "orphaned": True,
            "connected": False, "exitCause": {"kind": "operator_close"},
        }}},
        {"ok": True, "result": {"terminals": [{"handle": "other", "ptyId": "pty-closed"}]}},
    ])
    monkeypatch.setattr(orca, "_run_subprocess", lambda _argv: type("P", (), {
        "returncode": 0, "stdout": json.dumps(next(responses)), "stderr": "",
    })())
    assert orca.status("term-closed", worktree_root=root)["status"] == "unknown"


def test_status_closed_orphan_list_error_is_unknown(monkeypatch, tmp_path):
    from worktree_launcher.adapters import orca

    root = _worktree_root(tmp_path)
    calls = 0
    def fake_run(_argv):
        nonlocal calls
        calls += 1
        payload = {"ok": True, "result": {"terminal": {
            "handle": "term-closed", "ptyId": "pty-closed", "orphaned": True,
            "connected": False, "exitCause": {"kind": "operator_close"},
        }}} if calls == 1 else {"ok": False, "error": {"code": "runtime_failed"}}
        return type("P", (), {"returncode": 0 if calls == 1 else 1,
                                "stdout": json.dumps(payload), "stderr": "failed"})()
    monkeypatch.setattr(orca, "_run_subprocess", fake_run)
    assert orca.status("term-closed", worktree_root=root)["status"] == "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# S-2 — prompt receipt 원천은 launch argv이고 구형 토큰은 0건이다
# ─────────────────────────────────────────────────────────────────────────────


def test_launch_prompt_receipt_source_is_launch_argv(monkeypatch, tmp_path):
    """`prompt_receipt_source == "launch_argv"`, `prompt_id`는 전송 명령 sha256 앞
    16자, `submitted_at`은 채워진다(S-2)."""
    from worktree_launcher.adapters import orca

    worktree_root = _worktree_root(tmp_path)
    response = _fixture(CREATE_FIXTURE, tmp_path, worktree_root)
    command = 'claude "tasks/145-260919 이어서 수행"'
    recorded: dict = {}
    monkeypatch.setattr(orca, "_run_subprocess", _stub_run(recorded, response))

    report = orca.launch(worktree_root=worktree_root, command=command)

    expected = hashlib.sha256(command.encode("utf-8")).hexdigest()[:16]
    assert report["prompt_receipt_source"] == "launch_argv"
    assert report["prompt_id"] == expected
    assert report["submitted_at"]
    # 전송한 argv에 그 명령 문자열이 실제로 실려 있다 — 해시의 대상이 관측 가능해야 한다.
    assert command in recorded["args"]


def test_launch_report_satisfies_both_launcher_core_receipts(monkeypatch, tmp_path):
    """보고 dict가 `build_launch_receipt()`·`build_prompt_receipt()` 둘 다 non-None을
    만족한다(S-2 — 원자 복귀로 떨어지지 않는다)."""
    from worktree_launcher import launcher_core
    from worktree_launcher.adapters import orca

    worktree_root = _worktree_root(tmp_path)
    response = _fixture(CREATE_FIXTURE, tmp_path, worktree_root)
    recorded: dict = {}
    monkeypatch.setattr(orca, "_run_subprocess", _stub_run(recorded, response))

    report = orca.launch(worktree_root=worktree_root, command="claude")

    assert launcher_core.build_launch_receipt(report) is not None
    assert launcher_core.build_prompt_receipt(report) is not None


def test_legacy_sessionstart_claim_tokens_are_absent_from_package():
    """구형 토큰 `PROMPT_SOURCE_SESSIONSTART_CLAIM`·`sessionstart_claim_observation`
    잔존 0건(S-2 — `worktree_launcher` 패키지 전체 정적 검사)."""
    offenders = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        for token in ("PROMPT_SOURCE_SESSIONSTART_CLAIM", "sessionstart_claim_observation"):
            if token in text:
                offenders.append(f"{path}:{token}")
    assert offenders == []


# ─────────────────────────────────────────────────────────────────────────────
# S-13 — close 2스코프 argv 배타성 (인자 4조합)
# ─────────────────────────────────────────────────────────────────────────────


def test_close_handle_scope_builds_terminal_argv(monkeypatch, tmp_path):
    """`handle`만 → `terminal close --terminal <handle>`. `--worktree`·`--all`을 만들지
    않는다(S-13)."""
    from worktree_launcher.adapters import orca

    worktree_root = _worktree_root(tmp_path)
    response = _fixture(CLOSE_FIXTURE, tmp_path, worktree_root)
    handle = response["result"]["close"]["handle"]
    recorded: dict = {}
    monkeypatch.setattr(orca, "_run_subprocess", _stub_run(recorded, response))

    report = orca.close(handle=handle)

    args = recorded["args"]
    assert args[:3] == [orca.ORCA_BIN, "terminal", "close"]
    assert "--terminal" in args and args[args.index("--terminal") + 1] == handle
    assert "--worktree" not in args
    assert "--all" not in args
    assert "--json" in args
    assert report["exit_code"] == 0
    assert report["scope"] == "terminal"
    assert handle in report["closed"]
    assert report["fallback_attempted"] is False


def test_close_worktree_scope_builds_worktree_all_argv(monkeypatch, tmp_path):
    """`worktree_root`+`all` → `terminal close --worktree path:<root> --all`.
    `--terminal`을 만들지 않는다(S-13)."""
    from worktree_launcher.adapters import orca

    worktree_root = _worktree_root(tmp_path)
    response = _fixture(CLOSE_FIXTURE, tmp_path, worktree_root)
    recorded: dict = {}
    monkeypatch.setattr(orca, "_run_subprocess", _stub_run(recorded, response))

    report = orca.close(worktree_root=worktree_root, all=True)

    args = recorded["args"]
    assert args[:3] == [orca.ORCA_BIN, "terminal", "close"]
    assert "--worktree" in args
    assert args[args.index("--worktree") + 1] == f"path:{worktree_root}"
    assert "--all" in args
    assert "--terminal" not in args
    assert report["exit_code"] == 0
    assert report["scope"] == "worktree_all"


def test_close_both_selectors_fails_without_invoking_orca(monkeypatch, tmp_path):
    """`handle`과 `worktree_root`를 둘 다 주면 예외가 아니라 `exit_code != 0` 실패
    dict이며 orca를 호출하지 않는다(S-13)."""
    from worktree_launcher.adapters import orca

    worktree_root = _worktree_root(tmp_path)
    recorded: dict = {}
    monkeypatch.setattr(orca, "_run_subprocess", _stub_run(recorded, {}))

    report = orca.close(handle="term_x", worktree_root=worktree_root, all=True)

    assert report["exit_code"] != 0
    assert report["failure_reason"]
    assert report["fallback_attempted"] is False
    assert "calls" not in recorded


def test_close_no_selector_fails_without_invoking_orca(monkeypatch, tmp_path):
    """둘 다 주지 않아도 같은 실패 dict다(S-13)."""
    from worktree_launcher.adapters import orca

    recorded: dict = {}
    monkeypatch.setattr(orca, "_run_subprocess", _stub_run(recorded, {}))

    report = orca.close()

    assert report["exit_code"] != 0
    assert report["failure_reason"]
    assert "calls" not in recorded


# ─────────────────────────────────────────────────────────────────────────────
# launch argv 형태와 무자동폴백 (기존 계약 보존)
# ─────────────────────────────────────────────────────────────────────────────


def test_launch_argv_shape_creates_no_worktree(monkeypatch, tmp_path):
    """`terminal create --worktree path:<root> --command … --json`이고 worktree·checkout
    생성 서브명령 0건이다(C-4)."""
    from worktree_launcher.adapters import orca

    worktree_root = _worktree_root(tmp_path)
    response = _fixture(CREATE_FIXTURE, tmp_path, worktree_root)
    recorded: dict = {}
    monkeypatch.setattr(orca, "_run_subprocess", _stub_run(recorded, response))

    report = orca.launch(worktree_root=worktree_root, command="claude")

    args = recorded["args"]
    assert args[:3] == [orca.ORCA_BIN, "terminal", "create"]
    assert args[args.index("--worktree") + 1] == f"path:{worktree_root}"
    assert "--json" in args
    joined = " ".join(args)
    assert "worktree add" not in joined
    assert "checkout -b" not in joined
    assert "worktree create" not in joined
    assert report["adapter_handle"] == response["result"]["terminal"]["handle"]


def test_orca_absent_returns_failure_without_fallback(monkeypatch, tmp_path):
    """orca 부재 → adapter 실패 dict 반환, 자동 폴백 없음."""
    from worktree_launcher.adapters import orca

    def fake_run(argv, **kwargs):
        raise FileNotFoundError("orca not found")

    monkeypatch.setattr(orca, "_run_subprocess", fake_run)

    report = orca.launch(worktree_root=tmp_path, command="claude")

    assert report["exit_code"] != 0
    assert report["fallback_attempted"] is False
    assert report["adapter"] == "orca"


# ─────────────────────────────────────────────────────────────────────────────
# read — D-J 보고 스키마
# ─────────────────────────────────────────────────────────────────────────────


def test_read_builds_terminal_read_argv_and_reports_schema(monkeypatch, tmp_path):
    """`terminal read --terminal <handle> --json`이고 보고 dict는 D-J의 `handle`·
    `content`·`next_cursor`·`source`를 담는다."""
    from worktree_launcher.adapters import orca

    worktree_root = _worktree_root(tmp_path)
    response = _fixture(READ_FIXTURE, tmp_path, worktree_root)
    terminal = response["result"]["terminal"]
    recorded: dict = {}
    monkeypatch.setattr(orca, "_run_subprocess", _stub_run(recorded, response))

    report = orca.read(terminal["handle"])

    args = recorded["args"]
    assert args[:3] == [orca.ORCA_BIN, "terminal", "read"]
    assert args[args.index("--terminal") + 1] == terminal["handle"]
    assert "--json" in args
    assert report["exit_code"] == 0
    assert report["handle"] == terminal["handle"]
    assert report["next_cursor"] == terminal["nextCursor"]
    assert report["source"] == terminal["source"]
    assert "OPAL-FIXTURE-CAPTURE" in report["content"]
    assert report["fallback_attempted"] is False


def test_read_passes_cursor_limit_and_screen_flags(monkeypatch, tmp_path):
    """옵션 3종이 실측 플래그(`--cursor`·`--limit`·`--screen`)로 전달된다."""
    from worktree_launcher.adapters import orca

    worktree_root = _worktree_root(tmp_path)
    response = _fixture(READ_FIXTURE, tmp_path, worktree_root)
    recorded: dict = {}
    monkeypatch.setattr(orca, "_run_subprocess", _stub_run(recorded, response))

    orca.read("term_x", cursor=42, limit=1000)
    args = recorded["args"]
    assert args[args.index("--cursor") + 1] == "42"
    assert args[args.index("--limit") + 1] == "1000"
    assert "--screen" not in args

    orca.read("term_x", screen=True)
    args = recorded["args"]
    assert "--screen" in args
    assert "--cursor" not in args


# ─────────────────────────────────────────────────────────────────────────────
# S-10 — live 대조 (opt-in). 실제 orca를 호출하는 이 모듈의 유일한 테스트다.
#   목킹은 캡처 시점 봉투만 고정하므로 버전 드리프트(H-2)를 잡지 못한다 —
#   [MUST] TASK §Constraints C-7: "적합성 테스트에 실물 CLI 대조 1건을 포함한다."
# ─────────────────────────────────────────────────────────────────────────────

LIVE_ENV = "OPAL_LIVE_ORCA"
LIVE_WORKTREE_ENV = "OPAL_LIVE_ORCA_WORKTREE"
# live 터미널이 실행할 무해한 명령 — 에이전트를 띄우지 않고 한 줄만 찍고 끝난다.
LIVE_COMMAND = "printf 'OPAL-LIVE-ORCA-S10\\n'"
LIVE_TIMEOUT_SEC = 60

live_orca = pytest.mark.skipif(
    os.environ.get(LIVE_ENV) != "1" or shutil.which("orca") is None,
    reason=f"live 대조는 {LIVE_ENV}=1이고 orca가 PATH에 있을 때만 실행한다(S-10 실행 조건)",
)


def _repo_root() -> str:
    """이 테스트 파일이 속한 체크아웃의 루트 — 경로를 문자열로 추론하지 않고 git에 묻는다."""
    completed = subprocess.run(
        ["git", "-C", str(pathlib.Path(__file__).resolve().parent), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        timeout=LIVE_TIMEOUT_SEC,
    )
    if completed.returncode != 0:
        pytest.skip(f"git rev-parse 실패: {completed.stderr.strip()}")
    return os.path.realpath(completed.stdout.strip())


def _resolve_live_worktree() -> str:
    """대상 워크트리를 **조회로만** 결정한다 — 워크트리를 새로 만들지 않는다(C-4).

    1순위는 `OPAL_LIVE_ORCA_WORKTREE`, 2순위는 `orca worktree list --json`에서 `path`가
    이 체크아웃 루트와 같은 항목이다. 둘 다 실패하면 경로를 지어내지 않고 skip한다.
    """
    explicit = os.environ.get(LIVE_WORKTREE_ENV)
    if explicit:
        if not os.path.isdir(explicit):
            pytest.skip(f"{LIVE_WORKTREE_ENV}가 가리키는 디렉터리가 없다: {explicit}")
        return os.path.realpath(explicit)

    completed = subprocess.run(
        ["orca", "worktree", "list", "--json"],
        capture_output=True,
        text=True,
        timeout=LIVE_TIMEOUT_SEC,
    )
    if completed.returncode != 0:
        pytest.skip(f"orca worktree list 실패(exit {completed.returncode})")
    try:
        listing = json.loads(completed.stdout)
    except json.JSONDecodeError:
        pytest.skip("orca worktree list --json 응답이 JSON이 아니다")

    repo_root = _repo_root()
    worktrees = (listing.get("result") or {}).get("worktrees")
    for entry in worktrees if isinstance(worktrees, list) else []:
        path = entry.get("path") if isinstance(entry, dict) else None
        if isinstance(path, str) and path and os.path.realpath(path) == repo_root:
            return os.path.realpath(path)
    pytest.skip(f"orca에 등록된 워크트리 중 이 체크아웃({repo_root})과 일치하는 항목이 없다")


@live_orca
def test_live_orca_create_fills_handle_and_cwd_and_is_closed(tmp_path):
    """실 `orca terminal create` stdout이 `parse_response()`에서 `adapter_handle`·
    `reported_cwd`를 **둘 다** 채우고, 만든 터미널 1개를 정밀 close로 남김없이 회수한다(S-10).

    teardown은 단언 실패·예외 경로에서도 반드시 돌아야 하므로 `finally`에 둔다. close 결과
    단언은 원래 예외를 가리지 않도록 `finally` **밖**에서 수행한다.
    """
    from worktree_launcher.adapters import orca

    worktree_root = _resolve_live_worktree()
    handle = None
    close_report = None
    try:
        completed = subprocess.run(
            orca.build_argv(worktree_root, LIVE_COMMAND),
            capture_output=True,
            text=True,
            timeout=LIVE_TIMEOUT_SEC,
        )
        assert completed.returncode == 0, (
            f"orca terminal create 실패(exit {completed.returncode}): {completed.stderr.strip()}"
        )
        response = json.loads(completed.stdout)
        # 실 stdout을 그대로 통과시킨다 — 이 한 줄이 fixture가 대체하지 못하는 관문이다.
        report = orca.parse_response(response, command=LIVE_COMMAND)
        handle = report["adapter_handle"]

        assert isinstance(handle, str) and handle, f"실 응답에서 handle이 비었다: {completed.stdout}"
        reported_cwd = report["reported_cwd"]
        assert isinstance(reported_cwd, str) and reported_cwd, (
            f"실 응답에서 reported_cwd가 비었다(H-2 봉투 드리프트 의심): {completed.stdout}"
        )
        assert os.path.isabs(reported_cwd)
        assert os.path.realpath(reported_cwd) == worktree_root
        assert report["prompt_receipt_source"] == "launch_argv"
    finally:
        if handle is not None:
            # 정밀 `--terminal <handle>`만 쓴다 — `--worktree … --all` 스윕은 사용자의 다른
            # 탭까지 닫으므로 이 테스트에서 금지다.
            close_report = orca.close(handle=handle)

    assert close_report is not None, "handle을 얻지 못해 회수 대상이 없다"
    assert close_report["exit_code"] == 0, f"터미널 회수 실패: {close_report}"
    assert close_report["scope"] == "terminal"
    closed = close_report["closed"]
    assert handle in closed
    # 우리가 만든 1개 말고는 아무것도 닫지 않았다 — 잔존 0개이자 부수 효과 0건이다.
    assert [h for h in closed if h != handle] == []
