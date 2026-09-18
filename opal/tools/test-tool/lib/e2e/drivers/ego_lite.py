"""
@header {
  "module": "ego_lite",
  "layer": "util",
  "domain": "opal-tools",
  "description": "ADD-1 Ego Lite driver — 태스크 129가 e2e_adapter에 직접 넣었던 Ego Lite 우선 통합을 §B.2 driver 계약으로 흡수한다. ego-browser-tool의 `smoke`는 open+텍스트 assert가 융합된 단일 연산이므로 그 둘만 구현하고, 분리 실행이 불가능한 나머지 연산(snapshot·act·wait·capture)은 probed=true·available=false로 명시해 해당 증적을 요구하는 시나리오를 실행 전에 거른다. ego-browser-tool 자체는 변경하지 않으며 JSON 출력 계약을 소비만 한다.",
  "exports": [
    "DRIVER_NAME", "SESSION_MODE_STANDALONE", "ENV_EGO_TOOL_CMD", "EGO_TOOL_DEFAULT_PATH",
    "SUPPORTED_CAPABILITIES", "UNSUPPORTED_CAPABILITIES", "EgoLiteDriver", "register"
  ]
}

lib.e2e.drivers.ego_lite — Ego Lite 후보(`session_mode="standalone"`) 하나를 구현한다.

이 driver가 집행하는 규칙.

- **[MUST] 융합 연산을 쪼갠 척하지 않는다.** `ego-browser-tool`이 제공하는 것은
  `smoke <url> --expect-text <text>` 하나이며 여기에는 open과 텍스트 assert가 붙어 있다.
  `op_open`은 대상 URL을 **기록만** 하고 실제 호출은 `op_assert`에서 한 번 일어난다.
  open만 수행한 결과는 assertion을 만들지 않으므로 `pass`가 될 수 없다(C-DRV-4).
- **§A.8 [MUST]**: `snapshot`·`act`·`wait`·`capture`는 "미확인"이 아니라 **없음**이다.
  `probed=true`·`available=false`를 실어 `resolve_candidates()`의 `capability_missing`
  게이트가 그 연산을 요구하는 시나리오를 **실행 전에** 이 후보에서 걷어내게 한다.
  UI 조작(`act`)이 필요한 여정은 이 후보로 내려오지 않고 agent-browser로 간다.
- **C-DRV-2 [MUST]**: 가용성은 `op_probe`가 실제 실행한 `run.sh status` 결과로만 판정한다.
  바이너리 존재·플랫폼 추정으로 승격하지 않는다(NR-7).
- **C-3 [MUST]**: `ego-browser-tool`이 돌려주는 `provider_unavailable`(명시 `cancel`과
  비지원 플랫폼)일 때만 다음 후보로 전환된다. 미설치 상태의 `awaiting_human`은 전환
  사유가 아니다 — 사람의 설치 선택을 기다리는 상태이며 그대로 상위로 올린다.
- **TASK.md C-2 [MUST]**: 사용자 자원을 정리하지 않는다. 이 driver는 surface·profile을
  소유하지 않으므로(`smoke`가 자기 수명을 관리한다) `owned_resources()`가 항상 비어 있다.
- **배포 경계**: `~/.opal/tools/ego-browser-tool/`은 배포 트리이며 이 작업은 그것을
  변경하지 않는다. 아래 서브명령 이름과 인자는 그 도구의 README 계약 그대로다.
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any, Dict, List, Mapping, Optional, Sequence

from lib.e2e import drivers as e2e_drivers

DRIVER_NAME = "ego-lite"
SESSION_MODE_STANDALONE = "standalone"

ENV_EGO_TOOL_CMD = "OPAL_EGO_BROWSER_TOOL_CMD"
EGO_TOOL_DEFAULT_PATH = os.path.expanduser("~/.opal/tools/ego-browser-tool/run.sh")

# `smoke`가 텍스트 일치를 직접 수행하므로 dom_text만 관측할 수 있다. url·title·
# dom_attribute·eval은 도구가 노출하지 않으므로 선언하지 않는다 — 선언하면 그 verifier를
# 쓰는 시나리오가 이 후보로 내려와 실행 시점에 깨진다.
SUPPORTED_VERIFIERS = ("dom_text",)

SUPPORTED_CAPABILITIES: Sequence[str] = ()
# §A.8.1 6키 중 이 도구가 제공하지 않는 것. "없음"을 route가 아니라 available로 표현한다.
UNSUPPORTED_CAPABILITIES = (
    "screenshot", "console", "errors", "network_har", "isolated_profile", "semantic_assertion",
)


class EgoLiteToolError(e2e_drivers.DriverError):
    """ego-browser-tool 호출 자체가 깨진 경우. 제품 실패와 구분한다."""


def resolve_ego_tool_cmd(env: Optional[Mapping[str, str]] = None) -> List[str]:
    src = env if env is not None else os.environ
    override = src.get(ENV_EGO_TOOL_CMD)
    if override:
        return override.split()
    return [EGO_TOOL_DEFAULT_PATH]


def call_ego_tool(
    args: Sequence[str], *, env: Optional[Mapping[str, str]] = None, timeout: int = 120
) -> Dict[str, Any]:
    """도구를 실행하고 JSON 한 줄을 돌려준다. 파싱 실패는 제품 실패가 아니라 도구 오류다."""
    cmd = [*resolve_ego_tool_cmd(env), *args]
    try:
        completed = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            env=dict(env) if env is not None else None,
        )
    except FileNotFoundError as exc:
        raise EgoLiteToolError("ego_browser_tool_not_found", str(exc)) from exc
    except subprocess.TimeoutExpired as exc:
        raise EgoLiteToolError("ego_browser_tool_timeout", str(exc)) from exc
    text = (completed.stdout or "").strip()
    if not text:
        raise EgoLiteToolError(
            "ego_browser_tool_empty_output",
            (completed.stderr or "").strip()[:400] or f"exit={completed.returncode}",
        )
    try:
        return json.loads(text.splitlines()[-1])
    except json.JSONDecodeError as exc:
        raise EgoLiteToolError("ego_browser_tool_bad_json", text[:400]) from exc


class EgoLiteDriver(e2e_drivers.BrowserDriver):
    """Ego Lite 후보의 §B.2 부분 구현.

    구현: `probe`·`open`(기록)·`assert`(smoke 실행)·`close`(no-op).
    미구현으로 **선언**: `snapshot`·`act`·`wait`·`capture` — 도구가 분리 실행을 제공하지
    않는다. 기반 클래스의 `driver_operation_unimplemented`가 그대로 올라가며, 그 전에
    capability 게이트가 이 후보를 걸러내는 것이 정상 경로다.
    """

    name = DRIVER_NAME
    session_mode = SESSION_MODE_STANDALONE

    def __init__(self, *, runtime_context: Optional[Mapping[str, Any]] = None, **_kwargs) -> None:
        self.runtime_context: Dict[str, Any] = dict(runtime_context or {})
        self._env: Optional[Mapping[str, str]] = self.runtime_context.get("env")
        self._pending_url: Optional[str] = None
        self._assertion_results: List[Dict[str, Any]] = []
        self._op_calls: Dict[str, int] = {}
        self._version: Optional[str] = None
        # ego-browser-tool 원본 응답. 미설치 `awaiting_human`·`cancel`
        # `provider_unavailable`처럼 **도구가 소유한 status**를 호출자가 그대로
        # 읽어야 하므로 버리지 않는다(README 계약).
        self.last_raw: Dict[str, Any] = {}

    # ── 연산 ────────────────────────────────────────────────────────────────
    def op_probe(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`run.sh status`를 **실제 실행**해 가용성을 판정한다(C-DRV-2)."""
        self._count("probe")
        try:
            raw = call_ego_tool(["status"], env=self._env)
        except EgoLiteToolError as exc:
            return {
                "available": False, "probed": True,
                "reason": exc.detail_code, "version": None,
                "capabilities": self._capability_table(),
            }
        installed = bool(raw.get("installed"))
        self._version = raw.get("version")
        return {
            "available": installed,
            "probed": True,
            "version": self._version,
            "binary_path": raw.get("app_path"),
            "resolution_source": "installed" if installed else None,
            # 미설치는 `provider_unavailable`이 아니다 — 도구가 사람의 설치 선택을
            # 기다리는 상태를 별도로 돌려준다(C-3: 전환 사유는 cancel·비지원 플랫폼뿐).
            "reason": None if installed else (raw.get("error") or "ego_lite_not_installed"),
            "capabilities": self._capability_table(),
        }

    def op_open(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """대상 URL을 기록만 한다 — 실제 호출은 `assert`에서 한 번 일어난다.

        [MUST] 여기서 `smoke`를 부르면 같은 연산이 run 안에서 두 번 실행되어 재시도로
        관측된다(동결 RED S-27 (d-1)). 융합 연산은 융합된 지점에서 한 번만 부른다.
        """
        self._count("open")
        url = request.get("url") or request.get("value")
        if not url:
            raise e2e_drivers.DriverError("ego_lite_url_required", "open requires a url")
        self._pending_url = str(url)
        return {"opened": True, "url": self._pending_url, "deferred": True}

    def op_assert(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`smoke <url> --expect-text <expected>` 한 번으로 open+텍스트 일치를 수행한다."""
        self._count("assert")
        assertion = dict(request.get("assertion") or {})
        verifier = assertion.get("verifier")
        expected = assertion.get("expected")
        if verifier not in SUPPORTED_VERIFIERS:
            # 모르는 verifier를 대충 통과시키지 않는다. 관측 근거가 없으면 실패다.
            record = {
                "id": assertion.get("id"), "expected": expected, "actual": None,
                "passed": False, "verifier": verifier, "match": assertion.get("match"),
                "reason": "ego_lite_verifier_unsupported",
            }
            self._assertion_results.append(record)
            return record
        url = self._pending_url or request.get("url")
        if not url:
            raise e2e_drivers.DriverError("ego_lite_url_required", "assert requires a prior open")
        args = ["smoke", str(url), "--expect-text", str(expected)]
        choice = self.runtime_context.get("ego_install_choice")
        if choice:
            args += ["--install-choice", str(choice)]
        raw = call_ego_tool(args, env=self._env)
        self.last_raw = raw
        actual = raw.get("actual_text") if "actual_text" in raw else raw.get("actual")
        record = {
            "id": assertion.get("id"),
            "expected": expected,
            "actual": actual,
            "passed": bool(raw.get("ok")) and actual == expected,
            "verifier": verifier,
            "match": assertion.get("match") or "equals",
            "space_id": raw.get("space_id"),
        }
        self._assertion_results.append(record)
        return record

    def op_close(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """소유 자원이 없다 — `smoke`가 자기 수명을 관리한다(C-2)."""
        self._count("close")
        self._pending_url = None
        return {"closed": True, "released": [], "leaked": []}

    # ── 대장·관측 ───────────────────────────────────────────────────────────
    def assertion_results(self) -> List[Dict[str, Any]]:
        return list(self._assertion_results)

    def owned_resources(self) -> Dict[str, List[str]]:
        # 이 driver는 page·profile을 소유하지 않는다. 정리 대상이 구조적으로 없다.
        return {"browser_pages": [], "browser_profiles": []}

    def operation_calls(self) -> Dict[str, int]:
        return dict(self._op_calls)

    # ── 내부 ────────────────────────────────────────────────────────────────
    def _count(self, operation: str) -> None:
        self._op_calls[operation] = self._op_calls.get(operation, 0) + 1

    def _capability_table(self) -> Dict[str, Dict[str, Any]]:
        table = e2e_drivers.default_capabilities()
        for key in table:
            # 도구가 제공하지 않음을 **실행으로 확인한 사실**로 못 박는다(§A.8).
            table[key] = {"available": False, "route": "exec", "probed": True}
        return table


def _factory(*, runtime_context: Optional[Mapping[str, Any]] = None, **kwargs) -> EgoLiteDriver:
    return EgoLiteDriver(runtime_context=runtime_context, **kwargs)


def register() -> None:
    """후보 레지스트리에 ego-lite/standalone을 등록한다(순서는 `drivers/__init__` 소유)."""
    e2e_drivers.register_driver(DRIVER_NAME, SESSION_MODE_STANDALONE, _factory)


register()
