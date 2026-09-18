"""
@header {
  "module": "worktree_launcher.adapters.opal_agent_fallback",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "terminal launcher가 구성돼 있지 않을 때 호출자가 명시 선택하는 폴백 adapter. 지속형 TUI를 띄우는 대신 opal-agent의 공개 API를 one-shot(`-p`)으로 1회 호출해 같은 보고 dict 형태로 돌려주므로 launcher_core의 seam(`launch(worktree_root, command)`)이 그대로 성립한다. `AgentConfig`는 opal-agent가 실재로 선언한 필드(prompt·provider·cwd·output_format·session_id)만 채우고 새 인자를 만들지 않는다 — opal-agent 모듈은 하이픈 디렉터리라 파일 경로로 지연 로드한다. 반환된 세션 식별자를 `adapter_handle`로 승격해 이후 같은 값을 `session_id`로 넘기면 resume이 성립하며, 그때 `launch_mode`가 one-shot에서 resume 토큰으로 바뀌어 receipt에 남는다. `cwd`는 인자로 받은 `worktree_root`만 쓰고(경로 추론 없음), 에이전트가 다른 cwd를 보고하면 `failure_reason=launch_failed`로 보고해 launcher_core의 원자 복귀 경로로 넘긴다. 다른 adapter를 자동으로 되부르지 않는다.",
  "exports": [
    "ADAPTER_NAME", "PROVIDER", "OUTPUT_FORMAT",
    "LAUNCH_MODE_ONE_SHOT", "LAUNCH_MODE_RESUME", "call_agent", "launch"
  ],
  "depends": ["opal/tools/opal-agent/opal_agent.py(AgentConfig·call_agent 공개 API)", "worktree_launcher.launcher_core(FAILURE_REASON_LAUNCH_FAILED)"]
}
"""

from __future__ import annotations

import datetime
import importlib.util
import os
import pathlib
import sys

from ..launcher_core import FAILURE_REASON_LAUNCH_FAILED

ADAPTER_NAME = "opal_agent_fallback"

# opal-agent가 지원하는 provider 토큰(AgentConfig.provider의 기본값과 같은 값).
PROVIDER = "claude"
OUTPUT_FORMAT = "json"

# 지속형 TUI(generic/orca)와 구분되는 one-shot/resume 실행 모드 — receipt에 남는다.
LAUNCH_MODE_ONE_SHOT = "one_shot"
LAUNCH_MODE_RESUME = "resume"

OPAL_AGENT_MODULE = "opal_agent"
OPAL_AGENT_PATH = (
    pathlib.Path(__file__).resolve().parents[3] / "opal-agent" / "opal_agent.py"
)

_opal_agent = None


def _load_opal_agent():
    """`opal-agent`는 하이픈 디렉터리라 일반 import 경로가 없다 — 파일 경로로 1회 로드해
    캐시한다. 로드 대상은 위 상수 1경로뿐이며 탐색·추론을 하지 않는다. dataclass의 지연
    annotation 해석이 `sys.modules[__module__]`을 요구하므로 exec 전에 등록한다."""
    global _opal_agent
    if _opal_agent is None:
        spec = importlib.util.spec_from_file_location(OPAL_AGENT_MODULE, OPAL_AGENT_PATH)
        module = importlib.util.module_from_spec(spec)
        sys.modules.setdefault(OPAL_AGENT_MODULE, module)
        spec.loader.exec_module(module)
        _opal_agent = module
    return _opal_agent


def call_agent(config):
    """opal-agent 호출 경계 seam — 테스트가 여기만 대체한다. `AgentConfig`가 이미 담고 있는
    필드를 그대로 공개 API의 키워드로 펼칠 뿐 새 인자를 만들지 않는다."""
    return _load_opal_agent().call_agent(
        config.prompt,
        provider=config.provider,
        cwd=config.cwd,
        output_format=config.output_format,
        session_id=config.session_id,
    )


def _field(result, name):
    """결과에서 필드 하나를 읽는다 — `AgentResult` 데이터클래스와 dict 응답 둘 다 받는다."""
    if isinstance(result, dict):
        return result.get(name)
    return getattr(result, name, None)


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def launch(worktree_root, command, *, prompt=None, session_id=None) -> dict:
    """opal-agent를 one-shot(또는 `session_id`가 있으면 resume)으로 1회 호출한다.

    `prompt`를 따로 주지 않으면 `command`를 그대로 지시문으로 쓴다. 반환 dict는
    launcher_core가 launch·prompt receipt를 조립할 원천 필드를 담는다.
    """
    agent = _load_opal_agent()
    config = agent.AgentConfig(
        prompt=command if prompt is None else prompt,
        provider=PROVIDER,
        cwd=str(worktree_root),
        output_format=OUTPUT_FORMAT,
        session_id=session_id,
    )

    result = call_agent(config)

    handle = _field(result, "session_id")
    # 에이전트가 cwd를 따로 보고하면 그 값을, 아니면 우리가 subprocess에 강제한 cwd를 쓴다.
    reported_cwd = _field(result, "reported_cwd") or config.cwd
    report = {
        "adapter": ADAPTER_NAME,
        "launch_mode": LAUNCH_MODE_RESUME if session_id else LAUNCH_MODE_ONE_SHOT,
        "fallback_attempted": False,
        "exit_code": 0,
        "adapter_handle": handle,
        "reported_cwd": reported_cwd,
        "launched_at": _now(),
        "prompt_id": handle,
        "submitted_at": _now(),
    }

    if os.path.realpath(reported_cwd) != os.path.realpath(str(worktree_root)):
        report["exit_code"] = 1
        report["failure_reason"] = FAILURE_REASON_LAUNCH_FAILED
    return report
