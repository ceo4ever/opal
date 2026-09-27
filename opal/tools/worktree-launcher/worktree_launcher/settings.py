"""
@header {
  "module": "settings",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "launcher 설정 2-레이어 로더. `load_launcher_settings(project_root=None)`이 코드 상수 → 전역 `~/.opal/setting.json`(`GLOBAL_SETTING_PATH`) → `{project_root}/.opal/setting.local.json` 순으로 `launcher` 블록을 머지해 `{default, agents, utterance_template}` 3키 dict를 돌려준다. 머지 입도는 D-E — `agents.<name>`은 이름 단위 통째 교체(엔트리 내부를 깊게 합치지 않는다), 그 위 키는 키 단위 덮어쓰기다. 파일 부재·JSON 파싱 실패·타입 불일치는 전건 그 레이어만 무시하고 아래 레이어 값을 유지하며 예외를 전파하지 않는다(D-F — `models` 미설정은 중단이지만 launcher 미설정은 기본값이다. 블록을 쓴 적 없는 전 사용자의 `--wt`가 깨지면 안 된다). `resolve_command(settings, agent=None, task_path=…)`은 `agent` 인자 > `default` 순으로 이름을 정하고 `utterance_template`·`argv_template`을 렌더링해 실행 명령 문자열 하나를 만든다. 치환 토큰은 `{utterance}`·`{task_path}` 2종뿐이며 리터럴 치환이라 그 외 중괄호는 손대지 않는다(포맷 예외 없음). `launcher`는 `adapter`를 소유하지 않는다 — 어댑터 선택은 CLI `--adapter` 인자가 단독 소유한다. 이 모듈은 설정 파일을 읽기만 하고 쓰지 않는다.",
  "exports": [
    "GLOBAL_SETTING_PATH", "LOCAL_SETTING_RELPATH", "LAUNCHER_BLOCK_KEY",
    "DEFAULT_AGENT", "DEFAULT_AGENTS", "DEFAULT_UTTERANCE_TEMPLATE",
    "load_launcher_settings", "resolve_command"
  ],
  "depends": ["opal/core/setting.default.json(launcher 블록 기본값 SSOT)"]
}
"""

from __future__ import annotations

import copy
import json
import pathlib

# 전역 base 레이어. 테스트는 이 모듈 속성을 교체해 tmp 경로로 돌린다 —
# 실제 `~/.opal/`을 읽기 외로 건드리지 않는다.
GLOBAL_SETTING_PATH = pathlib.Path.home() / ".opal" / "setting.json"

# 프로젝트 오버라이드 레이어의 상대 경로(D-9 §5.1과 같은 위치 규약).
LOCAL_SETTING_RELPATH = pathlib.Path(".opal") / "setting.local.json"

LAUNCHER_BLOCK_KEY = "launcher"

# ─────────────────────────────────────────────────────────────────────────────
# D-F 기본 상수 — `opal/core/setting.default.json`의 `launcher` 블록과 같은 값이다.
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_AGENT = "claude"
DEFAULT_AGENTS = {
    "claude": {"argv_template": 'claude "{utterance}"'},
    "codex": {"argv_template": 'codex --no-daemon "{utterance}"'},
}
DEFAULT_UTTERANCE_TEMPLATE = "{task_path} 이어서 수행"
# Bounded child-lease observation limit.  Configuration uses the public camel
# case key so the JSON setting stays consistent with the other launcher keys.
DEFAULT_LEASE_POLL_TIMEOUT_SEC = 30

# 치환 토큰은 이 2종뿐이다(D-E).
PLACEHOLDER_UTTERANCE = "{utterance}"
PLACEHOLDER_TASK_PATH = "{task_path}"


# ─────────────────────────────────────────────────────────────────────────────
# 레이어 읽기 — 어떤 실패도 예외로 올리지 않는다
# ─────────────────────────────────────────────────────────────────────────────


def _read_json_object(path) -> dict:
    """설정 파일 하나를 dict로 읽는다. 부재·파싱 실패·최상위 비-dict는 모두 `{}`다."""
    if path is None:
        return {}
    try:
        text = pathlib.Path(path).read_text(encoding="utf-8")
    except (OSError, ValueError):
        return {}
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def _launcher_block(document: dict) -> dict:
    """문서에서 `launcher` 블록만 꺼낸다. 부재·비-dict는 `{}`(그 레이어 무시)."""
    block = document.get(LAUNCHER_BLOCK_KEY)
    return block if isinstance(block, dict) else {}


# ─────────────────────────────────────────────────────────────────────────────
# 머지 — D-E 입도
# ─────────────────────────────────────────────────────────────────────────────


def _valid_agent_entry(entry):
    """에이전트 엔트리는 문자열 `argv_template`을 가진 dict여야 한다."""
    if not isinstance(entry, dict):
        return None
    template = entry.get("argv_template")
    if not isinstance(template, str) or not template:
        return None
    return copy.deepcopy(entry)


def _apply_layer(resolved: dict, block: dict) -> None:
    """한 레이어를 아래 레이어 결과 위에 덮는다.

    - `default`·`utterance_template`: 키 단위 덮어쓰기(문자열일 때만).
    - `agents`: 이름 단위 통째 교체 — 이 레이어가 언급한 이름만 바꾸고,
      그 이름의 엔트리는 깊게 합치지 않고 통째로 갈아끼운다.
    """
    default = block.get("default")
    if isinstance(default, str) and default:
        resolved["default"] = default

    utterance_template = block.get("utterance_template")
    if isinstance(utterance_template, str) and utterance_template:
        resolved["utterance_template"] = utterance_template

    lease_poll_timeout = block.get("leasePollTimeoutSec")
    if isinstance(lease_poll_timeout, (int, float)) and not isinstance(lease_poll_timeout, bool) and lease_poll_timeout > 0:
        resolved["leasePollTimeoutSec"] = lease_poll_timeout

    agents = block.get("agents")
    if isinstance(agents, dict):
        for name, entry in agents.items():
            if not isinstance(name, str):
                continue
            valid = _valid_agent_entry(entry)
            if valid is not None:
                resolved["agents"][name] = valid


def load_launcher_settings(project_root=None) -> dict:
    """effective launcher 설정을 만든다.

    레이어는 코드 상수 → 전역 `GLOBAL_SETTING_PATH` → `{project_root}/.opal/setting.local.json`
    순이며, `project_root`가 없으면 로컬 레이어를 보지 않는다. 어떤 레이어가 없거나
    깨졌거나 타입이 다르면 그 레이어만 조용히 건너뛴다(D-F).
    """
    resolved = {
        "default": DEFAULT_AGENT,
        "agents": copy.deepcopy(DEFAULT_AGENTS),
        "utterance_template": DEFAULT_UTTERANCE_TEMPLATE,
        "leasePollTimeoutSec": DEFAULT_LEASE_POLL_TIMEOUT_SEC,
    }

    _apply_layer(resolved, _launcher_block(_read_json_object(GLOBAL_SETTING_PATH)))

    if project_root is not None:
        local_path = pathlib.Path(project_root) / LOCAL_SETTING_RELPATH
        _apply_layer(resolved, _launcher_block(_read_json_object(local_path)))

    return resolved


# ─────────────────────────────────────────────────────────────────────────────
# 명령 결정
# ─────────────────────────────────────────────────────────────────────────────


def _render(template: str, utterance: str, task_path: str) -> str:
    """플레이스홀더 2종만 리터럴 치환한다 — `str.format`을 쓰지 않으므로
    템플릿에 다른 중괄호가 있어도 예외가 나지 않고 그대로 남는다."""
    return template.replace(PLACEHOLDER_TASK_PATH, task_path).replace(
        PLACEHOLDER_UTTERANCE, utterance
    )


def _argv_template(settings: dict, agent) -> str:
    """이름 → `argv_template`. 요청 이름이 없으면 `default`, 그래도 없으면 기본 상수."""
    agents = settings.get("agents")
    agents = agents if isinstance(agents, dict) else {}

    for candidate in (agent, settings.get("default"), DEFAULT_AGENT):
        if not isinstance(candidate, str) or not candidate:
            continue
        entry = _valid_agent_entry(agents.get(candidate))
        if entry is not None:
            return entry["argv_template"]
        fallback = DEFAULT_AGENTS.get(candidate)
        if fallback is not None:
            return fallback["argv_template"]

    return DEFAULT_AGENTS[DEFAULT_AGENT]["argv_template"]


def resolve_command(settings: dict, agent=None, task_path: str = "") -> str:
    """실행 명령 문자열 하나를 만든다.

    `agent` 인자가 `default`를 이긴다. 발화는 `utterance_template`에 `{task_path}`를
    넣어 만들고, 그 결과를 `argv_template`의 `{utterance}`에 넣는다.
    """
    settings = settings if isinstance(settings, dict) else {}
    task_path = task_path if isinstance(task_path, str) else str(task_path)

    utterance_template = settings.get("utterance_template")
    if not isinstance(utterance_template, str) or not utterance_template:
        utterance_template = DEFAULT_UTTERANCE_TEMPLATE

    # 발화 템플릿이 받는 토큰은 `{task_path}` 하나다.
    utterance = utterance_template.replace(PLACEHOLDER_TASK_PATH, task_path)
    return _render(_argv_template(settings, agent), utterance=utterance, task_path=task_path)
