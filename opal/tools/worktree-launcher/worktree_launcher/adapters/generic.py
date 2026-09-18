"""
@header {
  "module": "worktree_launcher.adapters.generic",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "설정으로 주입된 terminal launcher 명령 템플릿 하나만 실행하는 범용 adapter. `render_template(template, cwd=…, command=…)`이 `{cwd}`·`{command}` 두 플레이스홀더만 치환하고, `launch(worktree_root, command, template=…)`이 그 결과를 argv로 쪼개 `worktree_root`를 subprocess cwd로 1회 실행한 뒤 launcher_core가 기대하는 단일 보고 dict를 돌려준다. 터미널 종류·OS를 판별하는 분기를 두지 않는다 — 어떤 터미널을 어떻게 띄울지는 전적으로 호출자가 설정에 선언한 템플릿이 정한다(`sys.platform`·`os.name` 조회 0건). launcher 명령이 `--json`류로 돌려준 응답에 담긴 handle·cwd·prompt 식별자만 receipt 원천으로 승격하며 경로·신원을 문자열이나 mtime으로 추론하지 않는다. 템플릿 미구성(`template=None`)은 실패 보고로 돌려줄 뿐 다른 adapter를 자동 호출하지 않는다 — 폴백 선택은 호출자 몫이다(orca와 동일한 무자동폴백 규약). 지속형 TUI를 띄우므로 `launch_mode`는 항상 persistent TUI 토큰이다.",
  "exports": [
    "ADAPTER_NAME", "LAUNCH_MODE", "FAILURE_LAUNCHER_NOT_CONFIGURED",
    "render_template", "parse_response", "launch"
  ],
  "depends": ["worktree_launcher.launcher_core(보고 dict 소비자)"]
}
"""

from __future__ import annotations

import datetime
import json
import shlex
import subprocess

ADAPTER_NAME = "generic"

# 지속형 TUI 기동 — one-shot/resume(`opal-agent -p`)과 구분해 receipt에 남긴다.
LAUNCH_MODE = "persistent_tui"

FAILURE_LAUNCHER_NOT_CONFIGURED = "launcher_not_configured"

# 템플릿이 인정하는 플레이스홀더는 이 둘뿐이다.
PLACEHOLDER_CWD = "{cwd}"
PLACEHOLDER_COMMAND = "{command}"

LAUNCH_TIMEOUT_SEC = 60


def _run_subprocess(args, **kwargs):
    """subprocess 경계 seam — 테스트가 여기만 대체한다."""
    return subprocess.run(args, capture_output=True, text=True, **kwargs)


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def render_template(template: str, *, cwd: str, command: str) -> str:
    """`{cwd}`·`{command}`만 치환한다. str.format을 쓰지 않으므로 템플릿에 들어 있는
    다른 중괄호는 그대로 보존되고, 이 둘 밖의 이름은 치환 대상이 아니다."""
    return template.replace(PLACEHOLDER_CWD, cwd).replace(PLACEHOLDER_COMMAND, command)


def parse_response(response: dict) -> dict:
    """launcher 명령의 응답에서 receipt 원천 필드만 뽑는다. 없는 필드는 만들어내지 않는다
    — 비어 있으면 launcher_core가 receipt 미성립으로 판정한다."""
    terminal = response.get("terminal") or {}
    return {
        "adapter": ADAPTER_NAME,
        "launch_mode": LAUNCH_MODE,
        "adapter_handle": terminal.get("handle"),
        "reported_cwd": terminal.get("cwd"),
        "launched_at": terminal.get("launched_at") or _now(),
        "prompt_id": terminal.get("prompt_id"),
        "submitted_at": terminal.get("submitted_at"),
    }


def launch(worktree_root, command, *, template=None) -> dict:
    """설정 템플릿을 1회 실행하고 launcher_core가 소비할 보고 dict를 돌려준다.

    `worktree_root`는 인자로 받은 값만 쓴다(경로 추론 없음). `template`이 없으면
    launcher 미구성이므로 실패를 보고할 뿐 다른 adapter를 부르지 않는다.
    """
    base = {"adapter": ADAPTER_NAME, "launch_mode": LAUNCH_MODE, "fallback_attempted": False}

    if not template:
        return {**base, "exit_code": 1, "failure_reason": FAILURE_LAUNCHER_NOT_CONFIGURED}

    rendered = render_template(template, cwd=str(worktree_root), command=command)
    try:
        completed = _run_subprocess(
            shlex.split(rendered), cwd=str(worktree_root), timeout=LAUNCH_TIMEOUT_SEC
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {**base, "exit_code": 1, "error": f"{type(exc).__name__}: {exc}"}

    if completed.returncode != 0:
        return {**base, "exit_code": completed.returncode, "stderr": completed.stderr}

    try:
        response = json.loads(completed.stdout)
    except (TypeError, ValueError):
        # 응답을 읽지 못하면 handle·cwd를 지어내지 않는다 — receipt 미성립으로 넘긴다.
        return {**base, "exit_code": 0}

    return {**base, "exit_code": 0, **parse_response(response)}
