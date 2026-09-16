"""저장소 루트 pytest 게이트 — 잘못된 인터프리터 실행을 조기 차단한다.

OPAL 테스트는 `~/.opal/.venv`의 인터프리터를 전제한다. 시스템 `python3`로 돌리면
`jsonschema`·`yaml` 같은 의존성이 없어 개별 테스트가 `ModuleNotFoundError`로
실패하는데, 그 메시지는 "테스트가 깨졌다"로 오독되기 쉽다. 실제로 이 저장소에서
그 오독이 반복 발생했다(태스크 135 회고 — brain-tool·test-tool 두 번).

산문 규칙으로는 막히지 않아 도구 게이트로 집행한다(`PRINCIPLES.md` Core Stance:
"Enforce, don't just advise"). 수집 시작 전에 의존성을 확인하고, 없으면 올바른
실행 명령을 알려주며 즉시 중단한다.

우회: `OPAL_ALLOW_ANY_PYTHON=1`을 설정하면 이 게이트를 건너뛴다. 의존성이 필요
없는 일부 스위트만 시스템 인터프리터로 돌리는 경우를 위한 탈출구이며, 기본 경로는
아니다.
"""

import os
import shutil
import sys

import pytest

# 테스트가 요구하지만 시스템 인터프리터에는 보통 없는 모듈.
# 새 의존성이 생기면 여기에 더한다 — 목록이 곧 게이트의 판정 기준이다.
_REQUIRED_MODULES = ("jsonschema", "yaml")

_VENV_PYTHON = os.path.expanduser("~/.opal/.venv/bin/python")


def _missing_modules():
    import importlib.util

    return [m for m in _REQUIRED_MODULES if importlib.util.find_spec(m) is None]


def pytest_configure(config):
    if os.environ.get("OPAL_ALLOW_ANY_PYTHON"):
        return

    missing = _missing_modules()
    if not missing:
        return

    hint = _VENV_PYTHON if os.path.isfile(_VENV_PYTHON) else shutil.which("python3") or "python3"
    args = " ".join(sys.argv[1:]) or "<테스트 경로>"

    raise pytest.UsageError(
        "\n"
        f"OPAL 테스트 인터프리터가 아닙니다 — 누락 모듈: {', '.join(missing)}\n"
        f"현재 인터프리터: {sys.executable}\n"
        "\n"
        "이대로 실행하면 해당 의존성을 쓰는 테스트가 ModuleNotFoundError로 실패해\n"
        "제품 결함처럼 보입니다. 아래로 다시 실행하십시오.\n"
        "\n"
        f"    {hint} -m pytest {args}\n"
        "\n"
        "의존성 없이 일부 스위트만 돌려야 하면 OPAL_ALLOW_ANY_PYTHON=1 로 우회할 수\n"
        "있지만, 그 경우 실패는 인터프리터 문제일 수 있음을 전제하고 해석하십시오."
    )
