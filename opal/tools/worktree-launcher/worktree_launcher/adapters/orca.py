"""
@header {
  "module": "worktree_launcher.adapters.orca",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "Orca 터미널 adapter — `launch`·`read`·`close` 3동사를 D-J 보고 스키마로 노출한다. `launch`는 `orca terminal create --worktree path:<worktree_root> --command <command> --json` 단일 호출로 **이미 존재하는** OPAL worktree에 터미널 1개를 붙이고, `read`는 `orca terminal read --terminal <handle> [--cursor <n>] [--limit <n>] [--screen] --json`으로 유계 출력을, `close`는 `--terminal <handle>`(정밀 1개) 또는 `--worktree path:<root> --all`(워크스페이스 스윕) 2스코프로 회수를 수행한다. worktree·checkout을 새로 만드는 서브명령(`worktree add`·`checkout -b`·`orca worktree create` 등)은 어떤 argv에도 넣지 않는다 — 워크트리 생성은 worktree-tool의 소유다. 응답 봉투는 `{\"ok\":…,\"result\":{…},\"_meta\":…}`이며 터미널 필드는 `result.terminal`에서만 읽는다. `reported_cwd`는 `result.terminal.worktreeId`(`<repoId>::<path>`)를 첫 `::` 1회 분리해 뒤쪽을 취하고, 분리 실패·비절대 경로는 값을 지어내지 않고 None을 돌려 launcher_core가 launch 실패로 판정하게 둔다. handoff prompt는 별도 seam 없이 `--command`로 띄운 TUI에 함께 제출되므로 prompt receipt의 원천은 기동 argv 하나뿐이다 — `prompt_receipt_source`는 항상 `launch_argv`, `prompt_id`는 실제로 실어 보낸 명령 문자열의 sha256 앞 16자, `submitted_at`은 exit 0을 관측한 시각이다. orca 미설치·비-0 종료·응답 파싱 실패·`close` 스코프 인자 위반은 전부 예외가 아니라 `exit_code != 0` + `failure_reason`·`detail` 보고이며 다른 adapter로 자동 폴백하지 않는다(폴백 선택은 호출자 책임, `fallback_attempted`는 항상 False). worktree_root·handle은 호출 인자로만 받고 basename·경로 접두·mtime으로 신원을 추론하지 않는다. 플랫폼 고유 env 변수명은 이 모듈에 두지 않는다(C-15).",
  "exports": [
    "ADAPTER_NAME", "ORCA_BIN", "LAUNCH_MODE_TERMINAL_CREATE",
    "PROMPT_SOURCE_LAUNCH_ARGV", "CLOSE_SCOPE_TERMINAL", "CLOSE_SCOPE_WORKTREE_ALL",
    "prompt_id_for_command", "build_argv", "build_read_argv", "build_close_argv",
    "parse_response", "launch", "read", "close"
  ],
  "depends": ["orca CLI(terminal create/read/close)"]
}
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import subprocess

ADAPTER_NAME = "orca"
# `launcher_core`가 `getattr(adapter, "name", None)`로 읽는 선택 seam(README §adapter seam).
# 보고 dict의 `adapter` 키가 정상 경로의 이름을 채우지만, 보고가 dict가 아닌
# `adapter_report_invalid` 복귀에서는 그 키에 도달하지 못해 실패 귀속에 이름이 비어버린다 —
# 어댑터가 망가졌을 때 정확히 어느 어댑터인지 잃는 자리라 이름을 모듈에 노출한다.
name = ADAPTER_NAME
ORCA_BIN = "orca"

# `--worktree` selector 스킴 — 이미 존재하는 worktree를 경로로 지목하는 유일한 형식.
WORKTREE_SELECTOR_SCHEME = "path:"
# `result.terminal.worktreeId`의 선언된 형식은 `<repoId>::<path>`다(D-D).
WORKTREE_ID_SEPARATOR = "::"

LAUNCH_MODE_TERMINAL_CREATE = "orca_terminal_create"

# prompt receipt의 유일한 원천 — `--command`를 실은 기동 argv 그 자체다(D-A).
PROMPT_SOURCE_LAUNCH_ARGV = "launch_argv"
PROMPT_ID_HASH_PREFIX_LEN = 16

CLOSE_SCOPE_TERMINAL = "terminal"
CLOSE_SCOPE_WORKTREE_ALL = "worktree_all"

FAILURE_REASON_LAUNCH_FAILED = "launch_failed"
FAILURE_REASON_READ_FAILED = "read_failed"
FAILURE_REASON_CLOSE_FAILED = "close_failed"
# `handle`·`worktree_root` 중 정확히 하나가 아닐 때의 호출자 인자 위반(D-C).
FAILURE_REASON_CLOSE_SCOPE_INVALID = "close_scope_invalid"

# orca 실행 파일 자체가 없을 때의 종료코드(POSIX `command not found` 관례).
EXIT_ORCA_UNAVAILABLE = 127
# 종료코드 0인데 stdout이 JSON이 아닐 때 쓰는 adapter 고유 실패 코드.
EXIT_RESPONSE_UNPARSABLE = 65
# 호출자 인자 자체가 잘못돼 orca를 부르지도 않은 경우(POSIX `usage error` 관례).
EXIT_INVALID_ARGUMENTS = 64

ORCA_TIMEOUT_SEC = 120


def _run_subprocess(argv, **kwargs):
    """실제 프로세스 실행 seam. 테스트는 이 이름을 monkeypatch해 orca를 한 번도 띄우지
    않고 argv와 응답을 관측한다."""
    return subprocess.run(
        argv, capture_output=True, text=True, timeout=ORCA_TIMEOUT_SEC, **kwargs
    )


def _observed_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# argv 조립 — 이 세 목록이 orca 경로가 만들 수 있는 부수효과의 전부다
# ─────────────────────────────────────────────────────────────────────────────


def build_argv(worktree_root, command):
    """`orca terminal create` argv. worktree 생성 서브명령은 넣지 않는다."""
    return [
        ORCA_BIN,
        "terminal",
        "create",
        "--worktree",
        f"{WORKTREE_SELECTOR_SCHEME}{worktree_root}",
        "--command",
        str(command),
        "--json",
    ]


def build_read_argv(handle, *, cursor=None, limit=None, screen=False):
    """`orca terminal read` argv. 옵션 3종은 값이 주어졌을 때만 실린다 — `--screen`과
    `--cursor`는 orca가 상호 배타로 선언했으므로 `screen=True`면 cursor를 싣지 않는다."""
    argv = [ORCA_BIN, "terminal", "read", "--terminal", str(handle)]
    if screen:
        argv.append("--screen")
    elif cursor is not None:
        argv += ["--cursor", str(cursor)]
    if limit is not None:
        argv += ["--limit", str(limit)]
    argv.append("--json")
    return argv


def build_close_argv(*, handle=None, worktree_root=None, all=False):
    """`orca terminal close` argv. 두 스코프는 서로의 플래그를 만들지 않는다(D-C) —
    `handle` 스코프는 `--terminal`만, worktree 스코프는 `--worktree … --all`만 싣는다."""
    argv = [ORCA_BIN, "terminal", "close"]
    if handle is not None:
        argv += ["--terminal", str(handle)]
    else:
        argv += ["--worktree", f"{WORKTREE_SELECTOR_SCHEME}{worktree_root}"]
        if all:
            argv.append("--all")
    argv.append("--json")
    return argv


# ─────────────────────────────────────────────────────────────────────────────
# 응답 파싱 — 실물 봉투(`result.<node>`)에서만 읽고 없는 값은 만들어내지 않는다
# ─────────────────────────────────────────────────────────────────────────────


def _result_node(response, node: str) -> dict:
    """`response["result"][node]`를 dict로 꺼낸다. 봉투가 다르면 빈 dict다 —
    None·비-dict를 흘려보내 호출부에서 AttributeError로 터지게 두지 않는다."""
    if not isinstance(response, dict):
        return {}
    result = response.get("result")
    if not isinstance(result, dict):
        return {}
    value = result.get(node)
    return value if isinstance(value, dict) else {}


def _reported_cwd(terminal: dict):
    """`worktreeId`(`<repoId>::<path>`)를 **첫 `::` 1회** 분리해 뒤쪽을 취한다(D-D).

    실물 응답에 `cwd`·`worktree_selector` 키는 없으므로 기대하지 않는다. 분리에 실패하거나
    뒤쪽이 절대경로가 아니면 값을 지어내지 않고 None을 돌려 launcher_core가 launch 실패로
    판정하게 둔다.
    """
    worktree_id = terminal.get("worktreeId")
    if not isinstance(worktree_id, str):
        return None
    _repo_id, separator, path = worktree_id.partition(WORKTREE_ID_SEPARATOR)
    if not separator or not path or not os.path.isabs(path):
        return None
    return path


def prompt_id_for_command(command) -> str:
    """전송한 명령 문자열의 sha256 앞 16자 — prompt receipt의 식별자다(D-A). 대상이
    argv에 실려 나간 그 문자열이므로 receipt가 가리키는 사실이 관측 가능하다."""
    return hashlib.sha256(str(command).encode("utf-8")).hexdigest()[
        :PROMPT_ID_HASH_PREFIX_LEN
    ]


def parse_response(response: dict, *, command=None, observed_at=None) -> dict:
    """`orca terminal create --json` 응답을 launcher_core의 보고 dict로 옮긴다.

    prompt receipt 2필드는 응답이 아니라 **기동 argv**에서 나온다 — `command`가 주어지면
    그 sha256 앞 16자를 `prompt_id`로, `observed_at`(exit 0 관측 시각)을 `submitted_at`으로
    싣는다. 원천 토큰은 이 adapter에 하나뿐이므로 항상 `launch_argv`다.
    """
    terminal = _result_node(response, "terminal")
    observed_at = observed_at or _observed_now()
    return {
        "adapter": ADAPTER_NAME,
        "adapter_handle": terminal.get("handle"),
        "reported_cwd": _reported_cwd(terminal),
        "launched_at": observed_at,
        "launch_mode": LAUNCH_MODE_TERMINAL_CREATE,
        "prompt_id": prompt_id_for_command(command) if command is not None else None,
        "submitted_at": observed_at if command is not None else None,
        "prompt_receipt_source": PROMPT_SOURCE_LAUNCH_ARGV,
    }


def _failure(exit_code: int, detail: str, failure_reason: str, **extra) -> dict:
    """실패는 예외가 아니라 성공과 같은 모양의 dict다(D-J)."""
    return {
        "adapter": ADAPTER_NAME,
        "exit_code": exit_code,
        "failure_reason": failure_reason,
        "detail": detail,
        # 다른 adapter로 넘어갈지는 호출자가 정한다 — 이 모듈은 시도조차 하지 않는다.
        "fallback_attempted": False,
        **extra,
    }


def _invoke(argv, failure_reason: str, **failure_extra):
    """orca 1회 호출 → (response, failure). 성공이면 failure가 None이고, 실패면 response가
    None이다. 세 동사가 같은 실패 표면을 공유한다."""
    try:
        completed = _run_subprocess(argv)
    except OSError as exc:  # orca 미설치 포함
        return None, _failure(
            EXIT_ORCA_UNAVAILABLE,
            f"orca_unavailable: {exc}",
            failure_reason,
            **failure_extra,
        )

    if completed.returncode != 0:
        return None, _failure(
            completed.returncode,
            (completed.stderr or "").strip() or "orca_nonzero_exit",
            failure_reason,
            **failure_extra,
        )

    try:
        return json.loads(completed.stdout), None
    except (TypeError, ValueError) as exc:
        return None, _failure(
            EXIT_RESPONSE_UNPARSABLE,
            f"orca_response_unparsable: {exc}",
            failure_reason,
            **failure_extra,
        )


# ─────────────────────────────────────────────────────────────────────────────
# 3동사
# ─────────────────────────────────────────────────────────────────────────────


def launch(worktree_root, command) -> dict:
    """orca 터미널 1개를 기존 worktree에 붙이고 launch·prompt receipt 원천을 반환한다."""
    argv = build_argv(worktree_root, command)
    response, failure = _invoke(
        argv, FAILURE_REASON_LAUNCH_FAILED, launch_mode=LAUNCH_MODE_TERMINAL_CREATE
    )
    if failure is not None:
        return failure

    # exit 0으로 돌아온 이 시점이 "그 argv가 셸에 전달됐다"의 관측 시각이다(D-A).
    report = parse_response(response, command=command, observed_at=_observed_now())
    report["exit_code"] = 0
    report["fallback_attempted"] = False
    return report


def _read_content(terminal: dict):
    """`tail`은 줄 목록이다 — 줄바꿈으로 이어 붙여 하나의 본문으로 돌려준다. 목록도
    문자열도 아니면 내용이 없는 것이므로 만들어내지 않는다."""
    tail = terminal.get("tail")
    if isinstance(tail, list):
        return "\n".join(str(line) for line in tail)
    if isinstance(tail, str):
        return tail
    return None


def read(handle, *, cursor=None, limit=None, screen=False) -> dict:
    """터미널 1개의 유계 출력을 읽는다(D-J `read` 스키마)."""
    argv = build_read_argv(handle, cursor=cursor, limit=limit, screen=screen)
    response, failure = _invoke(argv, FAILURE_REASON_READ_FAILED, handle=handle)
    if failure is not None:
        return failure

    terminal = _result_node(response, "terminal")
    return {
        "adapter": ADAPTER_NAME,
        "exit_code": 0,
        "fallback_attempted": False,
        "handle": terminal.get("handle") or handle,
        "content": _read_content(terminal),
        "next_cursor": terminal.get("nextCursor"),
        "source": terminal.get("source"),
    }


def _closed_handles(response, fallback_handle=None) -> list:
    """응답이 보고한 handle만 모은다. 스윕 응답이 목록을 주면 그 목록을, 단건이면 그
    handle 하나를 담는다 — 닫혔을 것이라고 추측해 채우지 않는다."""
    close_node = _result_node(response, "close")
    closed = close_node.get("closed") or close_node.get("terminals")
    if isinstance(closed, list):
        handles = [
            item.get("handle") if isinstance(item, dict) else item for item in closed
        ]
        return [h for h in handles if h]
    handle = close_node.get("handle") or fallback_handle
    return [handle] if handle else []


def close(*, handle=None, worktree_root=None, all=False) -> dict:
    """터미널을 회수한다. 스코프는 정확히 둘이며 **배타**다(D-C).

    - `close(handle=…)` → `terminal close --terminal <handle>` (정밀 1개, 원자 복귀용)
    - `close(worktree_root=…, all=True)` → `terminal close --worktree path:<root> --all`
      (워크스페이스 스윕, 회수용)

    `handle`·`worktree_root`를 둘 다 주거나 둘 다 주지 않으면 대상을 고를 수 없다 —
    예외가 아니라 `exit_code != 0` 실패 dict로 돌려주고 orca를 호출하지 않는다.
    """
    if (handle is None) == (worktree_root is None):
        return _failure(
            EXIT_INVALID_ARGUMENTS,
            "close_requires_exactly_one_of: handle | worktree_root",
            FAILURE_REASON_CLOSE_SCOPE_INVALID,
            scope=None,
            closed=[],
        )

    if handle is not None:
        scope = CLOSE_SCOPE_TERMINAL
        if all:
            # `--all`은 worktree 스코프 전용 플래그다 — handle과 섞이면 어느 대상을
            # 닫으라는 것인지 호출자 의도가 갈린다.
            return _failure(
                EXIT_INVALID_ARGUMENTS,
                "close_all_applies_to_worktree_scope_only",
                FAILURE_REASON_CLOSE_SCOPE_INVALID,
                scope=scope,
                closed=[],
            )
    else:
        scope = CLOSE_SCOPE_WORKTREE_ALL
        if not all:
            # orca는 `--worktree <selector> --all`만 받는다 — `--all` 없는 worktree
            # 스코프 argv를 만들지 않는다.
            return _failure(
                EXIT_INVALID_ARGUMENTS,
                "close_worktree_scope_requires_all",
                FAILURE_REASON_CLOSE_SCOPE_INVALID,
                scope=scope,
                closed=[],
            )

    argv = build_close_argv(handle=handle, worktree_root=worktree_root, all=all)
    response, failure = _invoke(
        argv, FAILURE_REASON_CLOSE_FAILED, scope=scope, closed=[]
    )
    if failure is not None:
        return failure

    return {
        "adapter": ADAPTER_NAME,
        "exit_code": 0,
        "fallback_attempted": False,
        "scope": scope,
        "closed": _closed_handles(response, handle),
    }
