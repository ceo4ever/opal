"""
@header {
  "module": "settings",
  "layer": "util",
  "domain": "opal-workspace",
  "description": "launcher 설정 2-레이어 로더. `load_launcher_settings(project_root=None)`이 코드 상수 → 전역 `~/.opal/setting.json`(`GLOBAL_SETTING_PATH`) → `{project_root}/.opal/setting.local.json` 순으로 `launcher` 블록을 머지해 `{default, agents, utterance_template}` 3키 dict를 돌려준다. 머지 입도는 D-E — `agents.<name>`은 이름 단위 통째 교체(엔트리 내부를 깊게 합치지 않는다), 그 위 키는 키 단위 덮어쓰기다. 파일 부재·JSON 파싱 실패·타입 불일치는 전건 그 레이어만 무시하고 아래 레이어 값을 유지하며 예외를 전파하지 않는다(D-F — `models` 미설정은 중단이지만 launcher 미설정은 기본값이다. 블록을 쓴 적 없는 전 사용자의 `--wt`가 깨지면 안 된다). `resolve_command(settings, agent=None, task_path=…, meta_dir=…)`은 `agent` 인자 > `default` 순으로 이름을 정하고 `utterance_template`·`argv_template`을 렌더링해 실행 명령 문자열 하나를 만든다. 치환 토큰은 `{utterance}`·`{task_path}`·`{meta_dir}` 3종뿐이며 리터럴 치환이라 그 외 중괄호는 손대지 않는다(포맷 예외 없음). `{meta_dir}`은 태스크 전용 메타 폴더 절대경로를 받아 Codex 기본 argv_template에 `--add-dir` 쓰기 권한 토큰으로 쓰인다. `resolve_argv_template(settings, agent=None)`은 치환 전 원본 `argv_template` 문자열을 공개해 CLI의 기동 전 점검(`cli._grant_option_preflight`)이 `{meta_dir}` 사용 여부·직전 옵션 토큰을 판정하게 한다. `launcher`는 `adapter`를 소유하지 않는다 — 어댑터 선택은 CLI `--adapter` 인자가 단독 소유한다. 이 모듈은 설정 파일을 읽기만 하고 쓰지 않는다.",
  "exports": [
    "GLOBAL_SETTING_PATH", "LOCAL_SETTING_RELPATH", "LAUNCHER_BLOCK_KEY",
    "DEFAULT_AGENT", "DEFAULT_AGENTS", "DEFAULT_UTTERANCE_TEMPLATE",
    "load_launcher_settings", "resolve_command", "resolve_argv_template",
    "resolve_agent_name", "load_model_mapping", "resolve_builder_model",
    "MODEL_INJECTION", "BUILDER_MODEL_LEVEL",
    "resolve_builder_effort", "EFFORT_INJECTION", "BUILDER_EFFORT_KEY",
    "resolve_agent_provider"
  ],
  "depends": ["opal/core/setting.default.json(launcher 블록 기본값 SSOT)"]
}
"""

from __future__ import annotations

import copy
import json
import os
import pathlib
import re
import shlex

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
    "codex": {"argv_template": 'codex --dangerously-bypass-approvals-and-sandbox --no-daemon --add-dir "{meta_dir}" "{utterance}"'},
}
DEFAULT_UTTERANCE_TEMPLATE = "{task_path} 이어서 수행"
# Bounded child-lease observation limit.  Configuration uses the public camel
# case key so the JSON setting stays consistent with the other launcher keys.
DEFAULT_LEASE_POLL_TIMEOUT_SEC = 30

# 치환 토큰은 이 3종뿐이다(`{meta_dir}`는 태스크 전용 메타 폴더 쓰기 경로 부여용으로 추가됐다).
PLACEHOLDER_UTTERANCE = "{utterance}"
PLACEHOLDER_TASK_PATH = "{task_path}"
PLACEHOLDER_META_DIR = "{meta_dir}"

# ─────────────────────────────────────────────────────────────────────────────
# builder 모델 기동 시점 주입 — 워크트리 세션(PM·builder)은 `models.<provider>.standard`로
# 뜬다. 검증기는 각 에이전트 frontmatter 레벨(advanced 등)을 그대로 따르므로 여기서 다루지
# 않는다. 모델 값은 `models` 매핑(전역+로컬 셀 단위 머지)만 원천으로 쓴다 — 하드코딩 없음.
# ─────────────────────────────────────────────────────────────────────────────

MODELS_BLOCK_KEY = "models"
BUILDER_MODEL_LEVEL = "standard"
# 에이전트 이름 → (models provider, 주입 옵션, 이미 지정된 것으로 볼 옵션들).
# 목록 밖 에이전트(gemini·cursor-agent 등)는 주입하지 않는다.
MODEL_INJECTION = {
    "claude": ("claude", "--model", ("--model",)),
    "codex": ("codex", "-m", ("-m", "--model")),
}
# 이 값이면 IDE/CLI 자체 설정에 위임한 것으로 보고 주입하지 않는다.
MODEL_INHERIT = "inherit"

# builder effort 주입 — `launcher.builderEffort.<에이전트>`(전역→로컬 에이전트 키 단위 덮어쓰기).
# 모델과 달리 선택값이다: 미설정·`inherit`이면 주입하지 않고 각 CLI의 기본 effort로 폴백한다.
# 에이전트 이름 → (주입 인자 생성기, 이미 지정된 것으로 볼 토큰 조각).
BUILDER_EFFORT_KEY = "builderEffort"
EFFORT_INJECTION = {
    "claude": (lambda value: ["--effort", value], ("--effort",)),
    "codex": (lambda value: ["-c", f'model_reasoning_effort="{value}"'], ("model_reasoning_effort",)),
}


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

    builder_effort = block.get(BUILDER_EFFORT_KEY)
    if isinstance(builder_effort, dict):
        for name, value in builder_effort.items():
            if isinstance(name, str) and isinstance(value, str) and value:
                resolved[BUILDER_EFFORT_KEY][name] = value

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
        BUILDER_EFFORT_KEY: {},
    }

    _apply_layer(resolved, _launcher_block(_read_json_object(GLOBAL_SETTING_PATH)))

    if project_root is not None:
        local_path = pathlib.Path(project_root) / LOCAL_SETTING_RELPATH
        _apply_layer(resolved, _launcher_block(_read_json_object(local_path)))

    return resolved


# ─────────────────────────────────────────────────────────────────────────────
# 명령 결정
# ─────────────────────────────────────────────────────────────────────────────


def _render(template: str, utterance: str, task_path: str, meta_dir: str = "") -> str:
    """플레이스홀더 3종만 리터럴 치환한다 — `str.format`을 쓰지 않으므로
    템플릿에 다른 중괄호가 있어도 예외가 나지 않고 그대로 남는다."""
    return (
        template.replace(PLACEHOLDER_TASK_PATH, task_path)
        .replace(PLACEHOLDER_META_DIR, meta_dir)
        .replace(PLACEHOLDER_UTTERANCE, utterance)
    )


def _agent_entry(settings: dict, agent) -> tuple:
    """이름 → `(실제로 쓰인 에이전트 이름, 엔트리 dict)`.
    요청 이름이 없으면 `default`, 그래도 없으면 기본 상수."""
    agents = settings.get("agents")
    agents = agents if isinstance(agents, dict) else {}

    for candidate in (agent, settings.get("default"), DEFAULT_AGENT):
        if not isinstance(candidate, str) or not candidate:
            continue
        entry = _valid_agent_entry(agents.get(candidate))
        if entry is not None:
            return candidate, entry
        fallback = DEFAULT_AGENTS.get(candidate)
        if fallback is not None:
            return candidate, copy.deepcopy(fallback)

    return DEFAULT_AGENT, copy.deepcopy(DEFAULT_AGENTS[DEFAULT_AGENT])


def _agent_and_template(settings: dict, agent) -> tuple:
    name, entry = _agent_entry(settings, agent)
    return name, entry["argv_template"]


def _argv_template(settings: dict, agent) -> str:
    return _agent_and_template(settings, agent)[1]


def resolve_agent_name(settings: dict, agent=None) -> str:
    """`resolve_command`가 실제로 고르는 에이전트 이름을 공개한다."""
    settings = settings if isinstance(settings, dict) else {}
    return _agent_and_template(settings, agent)[0]


def _entry_provider(name: str, entry: dict) -> str:
    """주입 규칙을 고를 provider. 엔트리 `provider` → 에이전트 이름(주입 표에 있으면)
    → 실행 파일 basename 순이다. 같은 CLI의 다른 계정 엔트리가 이름과 무관하게
    같은 주입 규칙을 받게 한다."""
    provider = entry.get("provider")
    if isinstance(provider, str) and provider:
        return provider
    if name in MODEL_INJECTION:
        return name
    tokens = entry["argv_template"].split()
    return os.path.basename(tokens[0]) if tokens else name


def resolve_agent_provider(settings: dict, agent=None) -> str:
    settings = settings if isinstance(settings, dict) else {}
    name, entry = _agent_entry(settings, agent)
    return _entry_provider(name, entry)


_ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _env_prefix(entry: dict) -> str:
    """엔트리 `env`(이름→값)를 셸 대입 접두사로 만든다. 값의 `~`는 홈으로 펼친다.
    이름이 셸 변수 규칙을 벗어나거나 값이 문자열이 아니면 그 항목만 건너뛴다."""
    env = entry.get("env")
    if not isinstance(env, dict):
        return ""
    parts = [
        f"{key}={shlex.quote(os.path.expanduser(value))}"
        for key, value in sorted(env.items())
        if isinstance(key, str) and _ENV_NAME_RE.match(key) and isinstance(value, str)
    ]
    return " ".join(parts) + " " if parts else ""


def _models_block(document: dict) -> dict:
    block = document.get(MODELS_BLOCK_KEY)
    return block if isinstance(block, dict) else {}


def load_model_mapping(project_root=None) -> dict:
    """`models` 블록을 전역 → 로컬 순으로 provider×level 셀 단위 머지한다
    (`opal-model-mapping.md` §5.1과 같은 입도). 표 폴백·기본 상수는 없다."""
    merged: dict = {}
    layers = [_read_json_object(GLOBAL_SETTING_PATH)]
    if project_root is not None:
        layers.append(_read_json_object(pathlib.Path(project_root) / LOCAL_SETTING_RELPATH))
    for document in layers:
        for provider, cells in _models_block(document).items():
            if not isinstance(provider, str) or not isinstance(cells, dict):
                continue
            target = merged.setdefault(provider, {})
            for level, value in cells.items():
                if isinstance(level, str) and isinstance(value, str) and value:
                    target[level] = value
    return merged


def _template_has_model_flag(template: str, flags) -> bool:
    for token in template.split():
        for flag in flags:
            if token == flag or token.startswith(flag + "="):
                return True
    return False


def resolve_builder_effort(settings: dict, agent=None):
    """주입할 builder effort를 돌려준다. 주입하지 않으면 `None` — CLI 기본값 폴백.

    미설정·`inherit`·주입 표 밖 에이전트·템플릿에 이미 effort 지정이 있는 경우는
    모두 `None`이다. 값의 유효성은 각 CLI가 판정한다(여기서 목록을 복제하지 않는다).
    """
    settings = settings if isinstance(settings, dict) else {}
    name, entry = _agent_entry(settings, agent)
    provider = _entry_provider(name, entry)
    injection = EFFORT_INJECTION.get(provider)
    if injection is None:
        return None
    if any(marker in entry["argv_template"] for marker in injection[1]):
        return None
    efforts = settings.get(BUILDER_EFFORT_KEY)
    efforts = efforts if isinstance(efforts, dict) else {}
    # 에이전트 이름 키가 provider 키를 이긴다 — 다른 계정 엔트리는 따로 적지 않으면 provider 값을 따른다.
    value = efforts.get(name) or efforts.get(provider)
    if not isinstance(value, str) or not value or value == MODEL_INHERIT:
        return None
    return value


def resolve_builder_model(settings: dict, agent=None, project_root=None) -> tuple:
    """주입할 builder 모델을 결정한다. `(model, error)`를 돌려준다.

    - 주입 대상이 아닌 에이전트, 템플릿에 이미 모델 옵션이 있는 경우, 매핑 값이
      `inherit`인 경우는 `(None, None)` — 주입하지 않는다(사용자 지정 우선).
    - 주입 대상인데 `models.<provider>.standard` 셀이 전역·로컬 둘 다 없으면
      `(None, "models.<provider>.standard")` — 추정·폴백하지 않는다.
    """
    settings = settings if isinstance(settings, dict) else {}
    name, entry = _agent_entry(settings, agent)
    injection = MODEL_INJECTION.get(_entry_provider(name, entry))
    if injection is None:
        return None, None
    provider, _flag, detect_flags = injection
    if _template_has_model_flag(entry["argv_template"], detect_flags):
        return None, None
    model = load_model_mapping(project_root).get(provider, {}).get(BUILDER_MODEL_LEVEL)
    if not model:
        return None, f"{MODELS_BLOCK_KEY}.{provider}.{BUILDER_MODEL_LEVEL}"
    if model == MODEL_INHERIT:
        return None, None
    return model, None


def _inject_options(template: str, provider: str, model, effort) -> str:
    """실행 파일 토큰 바로 뒤에 모델·effort 옵션을 넣는다(모델 → effort 순)."""
    injected: list = []
    model_injection = MODEL_INJECTION.get(provider)
    if model and model_injection is not None:
        injected += [model_injection[1], model]
    effort_injection = EFFORT_INJECTION.get(provider)
    if effort and effort_injection is not None:
        injected += effort_injection[0](effort)
    if not injected:
        return template
    executable, sep, rest = template.partition(" ")
    return f"{executable} {' '.join(shlex.quote(arg) for arg in injected)}{sep}{rest}"


def resolve_argv_template(settings: dict, agent=None) -> str:
    """치환 전 원본 `argv_template` 문자열을 공개한다(CLI의 기동 전 점검 전용).

    `resolve_command`가 내부적으로 쓰는 `_argv_template`과 같은 이름 해석 규칙을
    쓰되, 치환은 하지 않는다 — 호출자가 `{meta_dir}` 존재 여부·직전 옵션 토큰을
    직접 검사할 수 있게 한다."""
    settings = settings if isinstance(settings, dict) else {}
    return _argv_template(settings, agent)


def resolve_command(
    settings: dict, agent=None, task_path: str = "", meta_dir: str = "", model=None, effort=None
) -> str:
    """실행 명령 문자열 하나를 만든다.

    `agent` 인자가 `default`를 이긴다. 발화는 `utterance_template`에 `{task_path}`를
    넣어 만들고, 그 결과를 `argv_template`의 `{utterance}`에 넣는다. `{meta_dir}`는
    태스크 전용 메타 폴더 절대경로를 그대로 리터럴 치환한다. `model`이 주어지면
    (`resolve_builder_model` 결과) 실행 파일 바로 뒤에 에이전트별 모델 옵션을 넣고,
    `effort`(`resolve_builder_effort` 결과)가 있으면 그 뒤에 effort 옵션을 넣는다.
    """
    settings = settings if isinstance(settings, dict) else {}
    task_path = task_path if isinstance(task_path, str) else str(task_path)
    meta_dir = meta_dir if isinstance(meta_dir, str) else str(meta_dir)

    utterance_template = settings.get("utterance_template")
    if not isinstance(utterance_template, str) or not utterance_template:
        utterance_template = DEFAULT_UTTERANCE_TEMPLATE

    # 발화 템플릿이 받는 토큰은 `{task_path}` 하나다.
    utterance = utterance_template.replace(PLACEHOLDER_TASK_PATH, task_path)
    name, entry = _agent_entry(settings, agent)
    provider = _entry_provider(name, entry)
    return _env_prefix(entry) + _render(
        _inject_options(entry["argv_template"], provider, model, effort),
        utterance=utterance,
        task_path=task_path,
        meta_dir=meta_dir,
    )
