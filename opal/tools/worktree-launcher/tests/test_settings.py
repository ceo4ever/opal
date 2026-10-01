# @header
# module: worktree_launcher.tests.test_settings
# layer: test
# domain: worktree-launcher
# description: RED-first — launcher 설정 2-레이어 머지 로더(`load_launcher_settings`)와 명령 결정(`resolve_command`)의 공개 계약 검증 (S-6). 6조합(블록 전체 부재 / 전역만 / 로컬이 default만 덮어씀 / 로컬이 agents.codex만 교체 / JSON 파싱 실패 / agents 타입 불일치) 전건에서 예외 없이 기본값 폴백함을, 그리고 `agents.<name>` 이름 단위 통째 교체·그 위 키 단위 덮어쓰기 입도를 고정한다. 전역 경로는 `settings.GLOBAL_SETTING_PATH`를 monkeypatch해 tmp로 돌린다 — 실제 `~/.opal/setting.json`은 읽지도 쓰지도 않는다. `setting.default.json`의 `launcher._help` 비대칭 근거 문장 존재도 문자열로 검사한다.
# exports: (none — pytest module)
# depends: worktree_launcher.settings, opal/core/setting.default.json
"""RED 테스트 — 구현 전(S-6)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
SETTING_DEFAULT = REPO_ROOT / "opal" / "core" / "setting.default.json"

TASK_PATH = "/hub/tasks/145-demo"


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def layers(tmp_path, monkeypatch):
    """전역·로컬 두 레이어를 tmp에 두고 전역 경로를 monkeypatch한다."""
    from worktree_launcher import settings  # RED

    global_path = tmp_path / "opal_home" / "setting.json"
    project_root = tmp_path / "project"
    local_path = project_root / ".opal" / "setting.local.json"
    monkeypatch.setattr(settings, "GLOBAL_SETTING_PATH", global_path)

    class Layers:
        def __init__(self):
            self.global_path = global_path
            self.local_path = local_path
            self.project_root = project_root

        def write_global(self, payload):
            _write_json(global_path, payload)

        def write_local(self, payload):
            _write_json(local_path, payload)

        def load(self):
            return settings.load_launcher_settings(project_root=project_root)

    project_root.mkdir(parents=True, exist_ok=True)
    return Layers()


# ─────────────────────────────────────────────────────────────────────────────
# S-6 조합 1 — 블록 전체 부재(두 파일 모두 없음)
# ─────────────────────────────────────────────────────────────────────────────


def test_missing_both_files_falls_back_to_defaults(layers):
    from worktree_launcher import settings  # RED

    resolved = layers.load()

    assert resolved["default"] == "claude"
    assert resolved["agents"]["claude"]["argv_template"] == 'claude "{utterance}"'
    assert "codex" in resolved["agents"]
    assert resolved["utterance_template"] == "{task_path} 이어서 수행"
    assert resolved["default"] == settings.DEFAULT_AGENT


def test_missing_launcher_block_in_present_files_falls_back_to_defaults(layers):
    """파일은 있으나 `launcher` 블록이 없는 경우도 기본값이다."""
    layers.write_global({"bootstrap": "on", "models": {"platform": "auto"}})
    layers.write_local({"models": {"platform": "claude"}})

    resolved = layers.load()

    assert resolved["default"] == "claude"
    assert resolved["utterance_template"] == "{task_path} 이어서 수행"


def test_defaults_resolve_to_claude_command(layers):
    from worktree_launcher import settings  # RED

    command = settings.resolve_command(layers.load(), task_path=TASK_PATH)

    assert command == f'claude "{TASK_PATH} 이어서 수행"'


# ─────────────────────────────────────────────────────────────────────────────
# S-6 조합 2 — 전역만 존재
# ─────────────────────────────────────────────────────────────────────────────


def test_global_only_block_is_applied(layers):
    from worktree_launcher import settings  # RED

    layers.write_global(
        {
            "launcher": {
                "default": "codex",
                "agents": {"codex": {"argv_template": 'codex exec "{utterance}"'}},
                "utterance_template": "{task_path} 계속",
            }
        }
    )

    resolved = layers.load()

    assert resolved["default"] == "codex"
    assert resolved["utterance_template"] == "{task_path} 계속"
    # 전역이 재정의하지 않은 이름(claude)은 기본 상수로 남는다.
    assert resolved["agents"]["claude"]["argv_template"] == 'claude "{utterance}"'
    assert settings.resolve_command(resolved, task_path=TASK_PATH) == (
        f'codex exec "{TASK_PATH} 계속"'
    )


# ─────────────────────────────────────────────────────────────────────────────
# S-6 조합 3 — 로컬이 `default`만 덮어씀 (키 단위 덮어쓰기)
# ─────────────────────────────────────────────────────────────────────────────


def test_local_overrides_default_key_only(layers):
    from worktree_launcher import settings  # RED

    layers.write_global(
        {
            "launcher": {
                "default": "claude",
                "agents": {
                    "claude": {"argv_template": 'claude --global "{utterance}"'},
                    "codex": {"argv_template": 'codex --global "{utterance}"'},
                },
                "utterance_template": "{task_path} 전역문구",
            }
        }
    )
    layers.write_local({"launcher": {"default": "codex"}})

    resolved = layers.load()

    # 바뀐 셀만 로컬, 나머지 키는 전역 유지.
    assert resolved["default"] == "codex"
    assert resolved["utterance_template"] == "{task_path} 전역문구"
    assert resolved["agents"]["claude"]["argv_template"] == 'claude --global "{utterance}"'
    assert resolved["agents"]["codex"]["argv_template"] == 'codex --global "{utterance}"'

    # default를 codex로 바꾸면 결정 명령이 codex argv로 바뀐다.
    assert settings.resolve_command(resolved, task_path=TASK_PATH) == (
        f'codex --global "{TASK_PATH} 전역문구"'
    )


# ─────────────────────────────────────────────────────────────────────────────
# S-6 조합 4 — 로컬이 `agents.codex`만 교체 (이름 단위 통째 교체)
# ─────────────────────────────────────────────────────────────────────────────


def test_local_replaces_one_agent_by_name_wholesale(layers):
    from worktree_launcher import settings  # RED

    layers.write_global(
        {
            "launcher": {
                "default": "claude",
                "agents": {
                    "claude": {"argv_template": 'claude --global "{utterance}"'},
                    "codex": {
                        "argv_template": 'codex --global "{utterance}"',
                        "legacy_key": "전역에만 있던 키",
                    },
                },
            }
        }
    )
    layers.write_local(
        {"launcher": {"agents": {"codex": {"argv_template": 'codex --local "{utterance}"'}}}}
    )

    resolved = layers.load()

    # 이름 단위 통째 교체 — 전역 codex 엔트리의 다른 키는 살아남지 않는다.
    assert resolved["agents"]["codex"]["argv_template"] == 'codex --local "{utterance}"'
    assert "legacy_key" not in resolved["agents"]["codex"]
    # 로컬이 언급하지 않은 이름은 전역 그대로.
    assert resolved["agents"]["claude"]["argv_template"] == 'claude --global "{utterance}"'
    # default는 전역 유지이므로 claude 명령이 결정된다.
    assert settings.resolve_command(resolved, task_path=TASK_PATH).startswith("claude --global")
    # 명시 agent 인자는 default를 이긴다.
    assert settings.resolve_command(
        resolved, agent="codex", task_path=TASK_PATH
    ).startswith("codex --local")


# ─────────────────────────────────────────────────────────────────────────────
# S-6 조합 5 — JSON 파싱 실패
# ─────────────────────────────────────────────────────────────────────────────


def test_broken_global_json_falls_back_without_exception(layers):
    layers.write_global("{ this is not json ")

    resolved = layers.load()

    assert resolved["default"] == "claude"
    assert resolved["agents"]["claude"]["argv_template"] == 'claude "{utterance}"'


def test_broken_local_json_keeps_global_layer_without_exception(layers):
    layers.write_global({"launcher": {"default": "codex"}})
    layers.write_local("}{ broken")

    resolved = layers.load()

    # 로컬 파손은 전역 레이어를 무너뜨리지 않는다.
    assert resolved["default"] == "codex"


# ─────────────────────────────────────────────────────────────────────────────
# S-6 조합 6 — `agents`가 문자열(타입 불일치)
# ─────────────────────────────────────────────────────────────────────────────


def test_agents_type_mismatch_falls_back_without_exception(layers):
    from worktree_launcher import settings  # RED

    layers.write_global({"launcher": {"default": "claude", "agents": "codex"}})

    resolved = layers.load()

    assert resolved["agents"]["claude"]["argv_template"] == 'claude "{utterance}"'
    assert settings.resolve_command(resolved, task_path=TASK_PATH) == (
        f'claude "{TASK_PATH} 이어서 수행"'
    )


@pytest.mark.parametrize(
    "block",
    [
        "launcher-as-string",
        ["launcher", "as", "list"],
        {"default": 7, "utterance_template": [], "agents": {"claude": "not-a-dict"}},
        {"agents": {"claude": {"argv_template": 123}}},
        None,
    ],
)
def test_arbitrary_type_mismatches_never_raise(layers, block):
    layers.write_global({"launcher": block})

    resolved = layers.load()

    assert resolved["default"] == "claude"
    assert resolved["agents"]["claude"]["argv_template"] == 'claude "{utterance}"'
    assert resolved["utterance_template"] == "{task_path} 이어서 수행"


def test_unknown_agent_name_does_not_raise(layers):
    from worktree_launcher import settings  # RED

    resolved = layers.load()

    command = settings.resolve_command(resolved, agent="nope", task_path=TASK_PATH)

    assert command == f'claude "{TASK_PATH} 이어서 수행"'


def test_project_root_none_reads_global_layer_only(layers):
    from worktree_launcher import settings  # RED

    layers.write_global({"launcher": {"default": "codex"}})
    layers.write_local({"launcher": {"default": "claude"}})

    resolved = settings.load_launcher_settings()

    assert resolved["default"] == "codex"


# ─────────────────────────────────────────────────────────────────────────────
# 플레이스홀더 2종 계약
# ─────────────────────────────────────────────────────────────────────────────


def test_only_two_placeholders_are_substituted(layers):
    from worktree_launcher import settings  # RED

    layers.write_global(
        {
            "launcher": {
                "default": "claude",
                "agents": {"claude": {"argv_template": 'run --at {task_path} -- "{utterance}"'}},
                "utterance_template": "{task_path} 이어서",
            }
        }
    )

    command = settings.resolve_command(layers.load(), task_path=TASK_PATH)

    assert command == f'run --at {TASK_PATH} -- "{TASK_PATH} 이어서"'
    assert "{task_path}" not in command and "{utterance}" not in command


def test_unknown_placeholder_is_left_untouched(layers):
    from worktree_launcher import settings  # RED

    layers.write_global(
        {
            "launcher": {
                "default": "claude",
                "agents": {"claude": {"argv_template": 'claude --x {nope} "{utterance}"'}},
            }
        }
    )

    command = settings.resolve_command(layers.load(), task_path=TASK_PATH)

    assert "{nope}" in command


# ─────────────────────────────────────────────────────────────────────────────
# setting.default.json — `launcher` 블록과 비대칭 근거 문장
# ─────────────────────────────────────────────────────────────────────────────


def test_setting_default_json_has_launcher_block():
    data = json.loads(SETTING_DEFAULT.read_text(encoding="utf-8"))

    block = data["launcher"]
    assert block["default"] == "claude"
    assert block["agents"]["claude"]["argv_template"] == 'claude "{utterance}"'
    assert isinstance(block["agents"]["codex"]["argv_template"], str)
    assert block["utterance_template"] == "{task_path} 이어서 수행"
    # `launcher`는 adapter를 소유하지 않는다 — CLI `--adapter`가 단독 소유(D-E).
    assert "adapter" not in block


def test_codex_default_uses_no_daemon(layers):
    """Codex 기본 argv_template은 `--no-daemon`에 더해 태스크 전용 메타 폴더 쓰기
    경로 토큰(`--add-dir "{meta_dir}"`)을 포함한다."""
    from worktree_launcher import settings

    resolved = layers.load()
    assert resolved["agents"]["codex"]["argv_template"] == (
        'codex --dangerously-bypass-approvals-and-sandbox --no-daemon --add-dir "{meta_dir}" "{utterance}"'
    )
    assert settings.resolve_command(
        resolved, agent="codex", task_path=TASK_PATH, meta_dir="/hub/.opal-worktrees/.meta/task_220"
    ) == (
        f'codex --dangerously-bypass-approvals-and-sandbox --no-daemon --add-dir "/hub/.opal-worktrees/.meta/task_220" "{TASK_PATH} 이어서 수행"'
    )


def test_setting_default_json_launcher_help_states_asymmetry_rationale():
    data = json.loads(SETTING_DEFAULT.read_text(encoding="utf-8"))

    help_text = data["launcher"]["_help"]
    assert "models" in help_text
    assert "중단" in help_text
    assert "기본값" in help_text


def test_default_constants_match_setting_default_json():
    from worktree_launcher import settings  # RED

    data = json.loads(SETTING_DEFAULT.read_text(encoding="utf-8"))
    block = data["launcher"]

    assert settings.DEFAULT_AGENT == block["default"]
    assert settings.DEFAULT_UTTERANCE_TEMPLATE == block["utterance_template"]
    for name, entry in settings.DEFAULT_AGENTS.items():
        assert entry["argv_template"] == block["agents"][name]["argv_template"]


# ─────────────────────────────────────────────────────────────────────────────
# builder 모델 기동 시점 주입 — `models.<provider>.standard`를 실행 파일 뒤에 넣는다
# ─────────────────────────────────────────────────────────────────────────────

MODELS = {"claude": {"standard": "sonnet"}, "codex": {"standard": "gpt-5.6-terra"}}


def _builder(layers, agent=None):
    from worktree_launcher import settings

    return settings.resolve_builder_model(layers.load(), agent=agent, project_root=layers.project_root)


def test_builder_model_injected_for_claude_and_codex(layers):
    from worktree_launcher import settings

    layers.write_global({"models": MODELS})
    loaded = layers.load()

    assert _builder(layers) == ("sonnet", None)
    assert settings.resolve_command(loaded, task_path=TASK_PATH, model="sonnet") == (
        f'claude --model sonnet "{TASK_PATH} 이어서 수행"'
    )
    assert _builder(layers, "codex") == ("gpt-5.6-terra", None)
    assert settings.resolve_command(
        loaded, agent="codex", task_path=TASK_PATH, meta_dir="/m", model="gpt-5.6-terra"
    ) == f'codex -m gpt-5.6-terra --dangerously-bypass-approvals-and-sandbox --no-daemon --add-dir "/m" "{TASK_PATH} 이어서 수행"'


def test_builder_model_local_cell_overrides_global(layers):
    layers.write_global({"models": MODELS})
    layers.write_local({"models": {"claude": {"standard": "haiku"}}})

    assert _builder(layers) == ("haiku", None)
    assert _builder(layers, "codex") == ("gpt-5.6-terra", None)


@pytest.mark.parametrize(
    "agent,template",
    [
        ("claude", 'claude --model opus "{utterance}"'),
        ("claude", 'claude --model=opus "{utterance}"'),
        ("codex", 'codex -m gpt-5.6-sol "{utterance}"'),
        ("codex", 'codex --model gpt-5.6-sol "{utterance}"'),
    ],
)
def test_builder_model_skipped_when_template_already_sets_model(layers, agent, template):
    layers.write_global({"models": MODELS, "launcher": {"agents": {agent: {"argv_template": template}}}})

    assert _builder(layers, agent) == (None, None)


def test_builder_model_skipped_for_inherit_and_unknown_agent(layers):
    layers.write_global({
        "models": {"claude": {"standard": "inherit"}},
        "launcher": {"agents": {"gemini": {"argv_template": 'gemini "{utterance}"'}}},
    })

    assert _builder(layers) == (None, None)
    assert _builder(layers, "gemini") == (None, None)


def test_builder_model_missing_cell_is_error_not_guess(layers):
    layers.write_global({"models": {"claude": {"advanced": "opus"}}})

    assert _builder(layers) == (None, "models.claude.standard")


# ─────────────────────────────────────────────────────────────────────────────
# builder effort 주입 — 선택값. 미설정이면 주입하지 않고 CLI 기본값으로 폴백한다
# ─────────────────────────────────────────────────────────────────────────────


def _effort(layers, agent=None):
    from worktree_launcher import settings

    return settings.resolve_builder_effort(layers.load(), agent=agent)


def test_builder_effort_unset_falls_back_to_cli_default(layers):
    from worktree_launcher import settings

    layers.write_global({"models": MODELS})

    assert _effort(layers) is None
    assert _effort(layers, "codex") is None
    assert settings.resolve_command(layers.load(), task_path=TASK_PATH, model="sonnet", effort=None) == (
        f'claude --model sonnet "{TASK_PATH} 이어서 수행"'
    )


def test_builder_effort_injected_after_model(layers):
    from worktree_launcher import settings

    layers.write_global({"launcher": {"builderEffort": {"claude": "high", "codex": "medium"}}})
    loaded = layers.load()

    assert _effort(layers) == "high"
    assert settings.resolve_command(loaded, task_path=TASK_PATH, model="sonnet", effort="high") == (
        f'claude --model sonnet --effort high "{TASK_PATH} 이어서 수행"'
    )
    assert _effort(layers, "codex") == "medium"
    assert settings.resolve_command(
        loaded, agent="codex", task_path=TASK_PATH, meta_dir="/m", model="gpt-5.6-terra", effort="medium"
    ) == (
        "codex -m gpt-5.6-terra -c 'model_reasoning_effort=\"medium\"' "
        f'--dangerously-bypass-approvals-and-sandbox --no-daemon --add-dir "/m" "{TASK_PATH} 이어서 수행"'
    )


def test_builder_effort_local_overrides_per_agent(layers):
    layers.write_global({"launcher": {"builderEffort": {"claude": "high", "codex": "medium"}}})
    layers.write_local({"launcher": {"builderEffort": {"claude": "max"}}})

    assert _effort(layers) == "max"
    assert _effort(layers, "codex") == "medium"


@pytest.mark.parametrize(
    "agent,template",
    [
        ("claude", 'claude --effort low "{utterance}"'),
        ("codex", "codex -c model_reasoning_effort=low \"{utterance}\""),
    ],
)
def test_builder_effort_skipped_when_template_already_sets_it(layers, agent, template):
    layers.write_global({"launcher": {
        "builderEffort": {agent: "high"},
        "agents": {agent: {"argv_template": template}},
    }})

    assert _effort(layers, agent) is None


def test_builder_effort_skipped_for_inherit_and_unknown_agent(layers):
    layers.write_global({"launcher": {
        "builderEffort": {"claude": "inherit", "gemini": "high"},
        "agents": {"gemini": {"argv_template": 'gemini "{utterance}"'}},
    }})

    assert _effort(layers) is None
    assert _effort(layers, "gemini") is None


# ─────────────────────────────────────────────────────────────────────────────
# 같은 CLI의 다른 계정 — 엔트리 `provider`로 주입 규칙을, `env`로 계정 홈을 정한다
# ─────────────────────────────────────────────────────────────────────────────

ACCT2_ENTRY = {
    "provider": "codex",
    "env": {"CODEX_HOME": "~/.codex_acct2"},
    "argv_template": 'codex --no-daemon --add-dir "{meta_dir}" "{utterance}"',
}


def test_second_account_agent_gets_provider_injection_and_env_prefix(layers):
    from worktree_launcher import settings

    layers.write_global({"models": MODELS, "launcher": {"agents": {"acct2": ACCT2_ENTRY}}})
    loaded = layers.load()

    assert settings.resolve_agent_provider(loaded, "acct2") == "codex"
    model, error = _builder(layers, "acct2")
    assert (model, error) == ("gpt-5.6-terra", None)
    home = str(Path("~/.codex_acct2").expanduser())
    assert settings.resolve_command(
        loaded, agent="acct2", task_path=TASK_PATH, meta_dir="/m", model=model
    ) == f'CODEX_HOME={home} codex -m gpt-5.6-terra --no-daemon --add-dir "/m" "{TASK_PATH} 이어서 수행"'
    # 기동 전 점검은 env 없는 원본 템플릿을 본다 — 실행 파일이 첫 토큰으로 남는다.
    assert settings.resolve_argv_template(loaded, "acct2").startswith("codex ")


def test_provider_falls_back_to_executable_basename(layers):
    from worktree_launcher import settings

    layers.write_global({"launcher": {"agents": {"acct2": {"argv_template": '/opt/bin/claude "{utterance}"'}}}})

    assert settings.resolve_agent_provider(layers.load(), "acct2") == "claude"


def test_second_account_effort_name_key_beats_provider_key(layers):
    layers.write_global({"launcher": {
        "agents": {"acct2": ACCT2_ENTRY},
        "builderEffort": {"codex": "medium"},
    }})
    assert _effort(layers, "acct2") == "medium"

    layers.write_local({"launcher": {"builderEffort": {"acct2": "high"}}})
    assert _effort(layers, "acct2") == "high"
    assert _effort(layers, "codex") == "medium"


def test_env_prefix_skips_invalid_names_and_quotes_values(layers):
    from worktree_launcher import settings

    layers.write_global({"launcher": {"agents": {"x": {
        "provider": "claude",
        "env": {"BAD-NAME": "1", "GOOD": "a b", "NUM": 3},
        "argv_template": 'claude "{utterance}"',
    }}}})

    assert settings.resolve_command(layers.load(), agent="x", task_path=TASK_PATH) == (
        f"GOOD='a b' claude \"{TASK_PATH} 이어서 수행\""
    )


# ─────────────────────────────────────────────────────────────────────────────
# TASK-176 S-6 (RED-first) — `launcher.builderModelLevel.<에이전트|provider>`로 주입 모델 레벨 선택
# ─────────────────────────────────────────────────────────────────────────────

LEVEL_MODELS = {
    "claude": {"light": "haiku", "standard": "sonnet", "advanced": "opus"},
    "codex": {"light": "gpt-5.6-luna", "standard": "gpt-5.6-terra", "advanced": "gpt-5.6-sol"},
}


def _level_launcher(level):
    return {"builderModelLevel": level}


def test_task176_builder_model_level_key_constant():
    from worktree_launcher import settings

    assert getattr(settings, "BUILDER_MODEL_LEVEL_KEY", None) == "builderModelLevel"


def test_task176_level_unset_and_bogus_use_standard_cell(layers):
    layers.write_global({"models": LEVEL_MODELS})
    assert _builder(layers) == ("sonnet", None)

    layers.write_global({"models": LEVEL_MODELS, "launcher": _level_launcher({"claude": "bogus"})})
    assert _builder(layers) == ("sonnet", None)


def test_task176_level_advanced_injects_advanced_cell_into_command(layers):
    from worktree_launcher import settings

    layers.write_global({"models": LEVEL_MODELS, "launcher": _level_launcher({"claude": "advanced"})})
    model, error = _builder(layers)

    assert (model, error) == ("opus", None)
    assert settings.resolve_command(layers.load(), task_path=TASK_PATH, model=model) == (
        f'claude --model opus "{TASK_PATH} 이어서 수행"'
    )
    # 다른 provider는 영향을 받지 않는다(standard).
    assert _builder(layers, "codex") == ("gpt-5.6-terra", None)


def test_task176_level_light_uses_light_cell(layers):
    layers.write_global({"models": LEVEL_MODELS, "launcher": _level_launcher({"claude": "light"})})

    assert _builder(layers) == ("haiku", None)


def test_task176_level_agent_key_beats_provider_key(layers):
    acct = {"provider": "codex", "argv_template": 'codex --no-daemon --add-dir "{meta_dir}" "{utterance}"'}
    layers.write_global({
        "models": LEVEL_MODELS,
        "launcher": {"agents": {"acct2": acct}, **_level_launcher({"codex": "light", "acct2": "advanced"})},
    })

    assert _builder(layers, "codex") == ("gpt-5.6-luna", None)
    assert _builder(layers, "acct2") == ("gpt-5.6-sol", None)


def test_task176_level_inherit_cell_injects_nothing(layers):
    models = {"claude": {"standard": "sonnet", "advanced": "inherit"}}
    layers.write_global({"models": models, "launcher": _level_launcher({"claude": "advanced"})})

    assert _builder(layers) == (None, None)


def test_task176_level_missing_cell_is_unresolved_error(layers):
    layers.write_global({
        "models": {"claude": {"standard": "sonnet"}},
        "launcher": _level_launcher({"claude": "advanced"}),
    })

    assert _builder(layers) == (None, "models.claude.advanced")


def test_task176_level_with_effort_orders_model_then_effort(layers):
    from worktree_launcher import settings

    layers.write_global({"models": LEVEL_MODELS, "launcher": {
        **_level_launcher({"claude": "advanced"}), "builderEffort": {"claude": "high"},
    }})
    loaded = layers.load()
    model, error = _builder(layers)
    effort = settings.resolve_builder_effort(loaded)

    assert (model, error, effort) == ("opus", None, "high")
    assert settings.resolve_command(loaded, task_path=TASK_PATH, model=model, effort=effort) == (
        f'claude --model opus --effort high "{TASK_PATH} 이어서 수행"'
    )


def test_task176_level_local_overrides_global_per_agent_key(layers):
    layers.write_global({
        "models": LEVEL_MODELS,
        "launcher": _level_launcher({"claude": "advanced", "codex": "light"}),
    })
    layers.write_local({"launcher": _level_launcher({"claude": "light"})})

    loaded = layers.load()
    assert loaded.get("builderModelLevel") == {"claude": "light", "codex": "light"}
    assert _builder(layers) == ("haiku", None)
    assert _builder(layers, "codex") == ("gpt-5.6-luna", None)
