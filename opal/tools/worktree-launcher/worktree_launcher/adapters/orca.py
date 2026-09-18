"""
@header {
  "module": "worktree_launcher.adapters.orca",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "Orca 터미널 adapter. `orca terminal create --worktree path:<worktree_root> --command <command> --json` 단일 호출로 **이미 존재하는** OPAL worktree에 터미널을 붙이고, `--json` 응답의 terminal handle을 `adapter_handle`로 반환한다. worktree·checkout을 새로 만드는 서브명령(`worktree add`·`checkout -b` 등)은 argv에 넣지 않는다 — 워크트리 생성은 worktree-tool의 소유다. handoff prompt는 별도 seam 없이 `--command`로 띄운 Claude TUI에 함께 제출되며, 제출 receipt 원천(prompt_id·submitted_at)을 같은 보고 dict에 담아 launcher_core에 돌려준다. `--json`이 prompt receipt를 주지 않으면 값을 지어내지 않고 `prompt_receipt_source`를 SessionStart claim 관측 대체 경로로 표기한다. orca 미설치·비-0 종료·응답 파싱 실패는 전부 `exit_code != 0` 실패 보고이며 다른 adapter로 자동 폴백하지 않는다(폴백 선택은 호출자 책임, `fallback_attempted`는 항상 False). worktree_root는 호출 인자로만 받고 basename·경로 접두·mtime으로 신원을 추론하지 않는다. 플랫폼 고유 env 변수명은 이 모듈에 두지 않는다(C-15).",
  "exports": [
    "ADAPTER_NAME", "ORCA_BIN", "LAUNCH_MODE_TERMINAL_CREATE",
    "PROMPT_SOURCE_JSON", "PROMPT_SOURCE_SESSIONSTART_CLAIM",
    "build_argv", "parse_response", "launch"
  ],
  "depends": ["orca CLI(terminal create)"]
}
"""

from __future__ import annotations

import datetime
import json
import subprocess

ADAPTER_NAME = "orca"
ORCA_BIN = "orca"

# `--worktree` selector 스킴 — 이미 존재하는 worktree를 경로로 지목하는 유일한 형식.
WORKTREE_SELECTOR_SCHEME = "path:"

LAUNCH_MODE_TERMINAL_CREATE = "orca_terminal_create"
PROMPT_SOURCE_JSON = "orca_json"
PROMPT_SOURCE_SESSIONSTART_CLAIM = "sessionstart_claim_observation"

FAILURE_REASON_LAUNCH_FAILED = "launch_failed"

# orca 실행 파일 자체가 없을 때의 종료코드(POSIX `command not found` 관례).
EXIT_ORCA_UNAVAILABLE = 127
# 종료코드 0인데 stdout이 JSON이 아닐 때 쓰는 adapter 고유 실패 코드.
EXIT_RESPONSE_UNPARSABLE = 65

ORCA_TIMEOUT_SEC = 120


def _run_subprocess(argv, **kwargs):
    """실제 프로세스 실행 seam. 테스트는 이 이름을 monkeypatch해 orca를 한 번도 띄우지
    않고 argv와 응답을 관측한다."""
    return subprocess.run(
        argv, capture_output=True, text=True, timeout=ORCA_TIMEOUT_SEC, **kwargs
    )


def build_argv(worktree_root, command):
    """`orca terminal create` argv. worktree 생성 서브명령은 넣지 않는다 — 이 목록이
    orca 경로가 만들 수 있는 부수효과의 전부다."""
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


def _reported_cwd(terminal: dict):
    """orca가 보고한 값에서만 cwd를 읽는다. `cwd`가 없으면 orca가 되돌려준
    `worktree_selector`(우리가 넘긴 것과 같은 `path:` 스킴)를 디코드한다 — 경로 문자열로
    신원을 추론하는 것이 아니라 adapter 응답을 그 스킴대로 파싱하는 것이다. 둘 다 없으면
    None을 돌려 launcher_core가 launch 실패로 판정하게 둔다(값 지어내기 금지)."""
    cwd = terminal.get("cwd")
    if cwd:
        return cwd
    selector = terminal.get("worktree_selector")
    if isinstance(selector, str) and selector.startswith(WORKTREE_SELECTOR_SCHEME):
        return selector[len(WORKTREE_SELECTOR_SCHEME) :]
    return None


def _observed_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def parse_response(response: dict) -> dict:
    """`orca terminal create --json` 응답을 launcher_core의 보고 dict로 옮긴다.

    prompt receipt 2필드를 응답에서 얻지 못하면 `prompt_receipt_source`를 SessionStart
    claim 관측 대체 경로로 표기하고 값은 비운 채 둔다.
    """
    terminal = response.get("terminal") or {}
    prompt_id = terminal.get("prompt_id") or response.get("prompt_id")
    submitted_at = terminal.get("submitted_at") or response.get("submitted_at")
    from_json = bool(prompt_id and submitted_at)
    return {
        "adapter": ADAPTER_NAME,
        "adapter_handle": terminal.get("handle"),
        "reported_cwd": _reported_cwd(terminal),
        "launched_at": terminal.get("launched_at") or _observed_now(),
        "launch_mode": LAUNCH_MODE_TERMINAL_CREATE,
        "prompt_id": prompt_id,
        "submitted_at": submitted_at,
        "prompt_receipt_source": (
            PROMPT_SOURCE_JSON if from_json else PROMPT_SOURCE_SESSIONSTART_CLAIM
        ),
    }


def _failure(exit_code: int, detail: str) -> dict:
    return {
        "adapter": ADAPTER_NAME,
        "exit_code": exit_code,
        "failure_reason": FAILURE_REASON_LAUNCH_FAILED,
        "launch_mode": LAUNCH_MODE_TERMINAL_CREATE,
        "detail": detail,
        # 다른 adapter로 넘어갈지는 호출자가 정한다 — 이 모듈은 시도조차 하지 않는다.
        "fallback_attempted": False,
    }


def launch(worktree_root, command) -> dict:
    """orca 터미널 1개를 기존 worktree에 붙이고 launch·prompt receipt 원천을 반환한다."""
    argv = build_argv(worktree_root, command)
    try:
        completed = _run_subprocess(argv)
    except OSError as exc:  # orca 미설치 포함
        return _failure(EXIT_ORCA_UNAVAILABLE, f"orca_unavailable: {exc}")

    if completed.returncode != 0:
        return _failure(
            completed.returncode,
            (completed.stderr or "").strip() or "orca_nonzero_exit",
        )

    try:
        response = json.loads(completed.stdout)
    except (TypeError, ValueError) as exc:
        return _failure(EXIT_RESPONSE_UNPARSABLE, f"orca_response_unparsable: {exc}")

    report = parse_response(response)
    report["exit_code"] = 0
    report["fallback_attempted"] = False
    return report
