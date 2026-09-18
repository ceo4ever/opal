"""
@header {
  "module": "cmux",
  "layer": "util",
  "domain": "opal-tools",
  "description": "T08 cmux driver — e2e_adapter가 들고 있던 cmux-tool 호출 로직을 §B.2 8연산 계약으로 이관한다. mode A(--surface 미전달, 신규 surface 강제)를 구조로 강제하고, cmux-tool이 user_owned=true로 표시한 surface는 정리 대장에 올리지 않는다(C-DRV-5, TASK.md C-2). 미지원 capability는 probed=true·available=false로 명시해 해당 증적을 요구하는 시나리오를 실행 전에 거른다. cmux-tool 자체는 변경하지 않으며 에러코드 어휘를 소비만 한다(TRD.md §8).",
  "exports": [
    "DRIVER_NAME", "SESSION_MODE_OWNED_SURFACE", "FALLBACK_CODES", "ESCALATE_CODES",
    "ENV_CMUX_TOOL_CMD", "CMUX_TOOL_DEFAULT_PATH", "SUPPORTED_CAPABILITIES",
    "UNSUPPORTED_CAPABILITIES", "CmuxToolError", "CmuxDriver",
    "resolve_cmux_tool_cmd", "call_cmux_tool", "register"
  ]
}

lib.e2e.drivers.cmux — `drivers/__init__.py`가 소유한 §B.2 8연산 배선을 상속해 cmux
후보(`session_mode="owned-surface"`) 하나를 구현한다. 이 모듈이 집행하는 규칙.

- C-DRV-5 [MUST]: **mode A 강제.** 어떤 연산도 cmux-tool에 `--surface`를 전달하지 않는다.
  `open`은 항상 신규 surface를 만들고, B/C 모드(사용자 surface 재사용)로 내려가는 경로를
  아예 두지 않는다 — 호출자가 surface를 지정하면 실행 없이 거부한다.
- TASK.md C-2 [MUST]: cmux-tool이 `user_owned=true`로 표시한 surface는 `_user_owned`에만
  담고 `_owned_surfaces`에는 절대 올리지 않는다. `op_close`의 정리 대상은 `_owned_surfaces`
  뿐이므로 사용자 surface는 정리 경로에서 **구조적으로** 닿을 수 없다.
- C-DRV-2 [MUST]: 가용성은 `op_probe`가 실제로 실행한 cmux-tool 결과로만 판정한다.
  `uname`·`cmux --version` 파싱·바이너리 존재로 추정하지 않는다(NR-7). 판정 근거는
  cmux-tool이 발행한 error code 원문이며 하네스가 재작문하지 않는다.
- C-DRV-4 [MUST]: `open`·`navigate`만 수행한 결과는 `pass`가 될 수 없다. 이 모듈은
  `assertion_results()`에 **실제 `assert` 연산 결과만** 쌓고, 호출자는 그것을
  `build_verdict`에 그대로 넘긴다. assertion이 없으면 비어 있고 그대로 `fail`이 된다.
- §A.8 [MUST]: cmux-tool이 제공하지 않는 capability(`screenshot`·`console`·`errors`·
  `network_har`·`isolated_profile`)는 "미확인"이 아니라 **없음**이다. `probed=true`와
  `available=false`를 함께 실어 `resolve_candidates()`의 `capability_missing` 게이트가
  그 증적을 요구하는 시나리오를 **실행 전에** 이 후보에서 걷어내게 한다.
  `route`는 §A.8.1 enum(`native`|`exec`)이 확정하므로 `exec`를 유지한다 — 없음은 route가
  아니라 `available`로 표현한다(CONTRACT.md는 소비만 하며 변경하지 않는다, C-8).
- TRD.md §8 [MUST]: `~/.opal/tools/cmux-tool/`은 배포 트리이며 이 태스크는 **cmux-tool을
  변경하지 않는다**. 아래 `FALLBACK_CODES`·`ESCALATE_CODES`가 `lib/dispatch.sh`의 발행
  어휘와 **문자 그대로** 일치해야 그 계약이 성립한다.
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any, Dict, List, Mapping, Optional, Sequence

from lib.e2e import drivers as e2e_drivers
from lib.e2e import evidence as e2e_evidence

DRIVER_NAME = "cmux"
SESSION_MODE_OWNED_SURFACE = "owned-surface"


# ─── legacy cmux-tool raw error buckets (input normalization only) ───────────
# [MUST] 아래 두 집합은 `~/.opal/tools/cmux-tool/lib/dispatch.sh`가 실제로 발행하는 이름
# 이다(`not_in_cmux`·`cmux_not_installed`는 `:46,54`의 `_guard_cmux_env`). 어휘가 한 글자
# 라도 어긋나면 cmux-tool을 고쳐야 계약이 성립하게 되는데, 이 태스크의 제약은 정확히 그
# 반대다(cmux-tool 변경 0). 이름을 바꾸지 않는다.
FALLBACK_CODES = {
    "not_in_cmux",          # provider_unavailable candidate result
    "cmux_not_installed",   # provider_unavailable candidate result
    "surface_parse_failed", # infra_error via common contract
    "open_failed",          # infra_error via common contract
}

ESCALATE_CODES = {
    "usage",            # infra_error via common contract
    "invalid_surface",  # infra_error via common contract
    "goto_failed",      # infra_error via common contract
    "wait_failed",      # infra_error or fail with wait_kind=assertion_condition
    "eval_failed",      # infra_error via common contract
}

# cmux-tool 기본 실행 경로 — OPAL 설치 기준 절대 경로
# OPAL_CMUX_TOOL_CMD 환경변수가 있으면 그 값을 우선 사용 (테스트 스텁 주입 + 오버라이드용)
ENV_CMUX_TOOL_CMD = "OPAL_CMUX_TOOL_CMD"
CMUX_TOOL_DEFAULT_PATH = os.path.expanduser("~/.opal/tools/cmux-tool/run.sh")

RESOLUTION_ENV_OVERRIDE = "env-override"
RESOLUTION_OPAL_INSTALL = "opal-install"

# cmux-tool `lib/dispatch.sh`가 제공하는 서브명령으로 실제 수집 가능한 capability.
SUPPORTED_CAPABILITIES = ("snapshot",)
# 제공 서브명령이 존재하지 않는 capability — "미확인"이 아니라 "없음"이다(§A.8).
UNSUPPORTED_CAPABILITIES = (
    "screenshot",
    "console",
    "errors",
    "network_har",
    "isolated_profile",
)

# §A.8 capability ↔ artifact 고정 매핑 중 이 driver가 채울 수 있는 것.
SNAPSHOT_ARTIFACTS = {
    "before": "browser/before.snapshot",
    "after": "browser/after.snapshot",
}

# §B.2 `act`의 action.kind → cmux-tool 서브명령. 여기 없는 kind는 실행하지 않는다.
_ACT_SUBCOMMANDS = {
    "navigate": "navigate",
    "click": "click",
    "fill": "fill",
    "press": "press",
    "reload": "reload",
}

# §B.2 `assert`의 verifier → 관측 경로. 자유 형식 판정을 만들지 않는다(C-HUM-1의 취지).
VERIFIER_DOM_TEXT = "dom_text"
VERIFIER_DOM_ATTRIBUTE = "dom_attribute"
VERIFIER_EVAL = "eval"
VERIFIERS = (VERIFIER_DOM_TEXT, VERIFIER_DOM_ATTRIBUTE, VERIFIER_EVAL)

MATCH_EQUALS = "equals"
MATCH_CONTAINS = "contains"
MATCHERS = (MATCH_EQUALS, MATCH_CONTAINS)


class CmuxToolError(e2e_drivers.DriverError):
    """cmux-tool이 error code를 돌려준 경우. 원문 결과를 `raw`로 함께 싣는다.

    `detail_code`가 cmux-tool 원문 code이므로 호출자는 `FALLBACK_CODES`/`ESCALATE_CODES`
    소속만 보고 공통 계약으로 정규화할 수 있다 — 하네스가 사유를 재작문하지 않는다(NR-7).
    """

    def __init__(self, detail_code: str, detail: str = "", raw: Optional[Mapping[str, Any]] = None):
        super().__init__(detail_code, detail)
        self.raw: Dict[str, Any] = dict(raw or {})


# ─── cmux-tool 호출 ──────────────────────────────────────────────────────────
def resolve_cmux_tool_cmd(env=None) -> str:
    """
    cmux-tool 실행 경로 결정.
    1. OPAL_CMUX_TOOL_CMD 환경변수 (env dict 또는 현재 프로세스 환경)
    2. 없으면 ~/.opal/tools/cmux-tool/run.sh 기본 경로
    """
    # env dict가 전달된 경우 우선 참조, 없으면 현재 프로세스 환경 확인
    if env is not None:
        cmd = env.get(ENV_CMUX_TOOL_CMD)
    else:
        cmd = os.environ.get(ENV_CMUX_TOOL_CMD)
    return cmd if cmd else CMUX_TOOL_DEFAULT_PATH


def call_cmux_tool(args: List[str], env=None) -> Dict[str, Any]:
    """
    cmux-tool을 subprocess로 호출하고 stdout JSON 파싱하여 반환.
    호출 실패(파일 없음 등) 시 {"ok": False, "error": "cmux_not_installed"} 반환.

    cmux-tool 경로 해석 순서:
    1. env["OPAL_CMUX_TOOL_CMD"] (테스트 스텁 주입 / 오버라이드)
    2. os.environ["OPAL_CMUX_TOOL_CMD"]
    3. ~/.opal/tools/cmux-tool/run.sh (기본 경로)

    `dispatch.sh`의 `json_err`는 오류 JSON을 **stderr**로 낸다(`:46,54` 등). stdout이 비면
    stderr의 JSON을 먼저 읽는 이유가 이것이다 — 그래야 `not_in_cmux` 같은 실제 발행 어휘가
    소비되고, 모든 실패가 `cmux_not_installed` 한 코드로 뭉개지지 않는다.
    """
    cmux_tool_cmd = resolve_cmux_tool_cmd(env)
    try:
        result = subprocess.run(
            ["bash", cmux_tool_cmd] + args,
            capture_output=True,
            text=True,
            env=env,
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        if not stdout:
            parsed_stderr = _loads_or_none(stderr)
            if isinstance(parsed_stderr, dict) and parsed_stderr.get("error"):
                return parsed_stderr
            # cmux-tool이 설치되지 않았거나 실패한 경우 stderr 확인
            return {
                "ok": False,
                "error": "cmux_not_installed",
                "detail": stderr or "cmux-tool returned empty output",
            }
        parsed = _loads_or_none(stdout)
        if parsed is None:
            return {
                "ok": False,
                "error": "surface_parse_failed",
                "detail": f"Failed to parse cmux-tool JSON output: {stdout}",
            }
        return parsed
    except FileNotFoundError:
        return {
            "ok": False,
            "error": "cmux_not_installed",
            "detail": f"{cmux_tool_cmd} not found",
        }


def _loads_or_none(text: str) -> Optional[Dict[str, Any]]:
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    return data if isinstance(data, dict) else None


# ─── driver ──────────────────────────────────────────────────────────────────
class CmuxDriver(e2e_drivers.BrowserDriver):
    """cmux `owned-surface` 후보의 §B.2 8연산 구현.

    소유권 대장이 두 개인 것이 이 driver의 핵심이다. `_owned_surfaces`는 **이 run이 연**
    surface만, `_user_owned`는 cmux-tool이 `user_owned=true`로 표시한 surface만 담는다.
    정리는 앞의 것만 대상으로 하므로 사용자 surface를 닫는 경로가 존재하지 않는다(C-2).
    """

    name = DRIVER_NAME
    session_mode = SESSION_MODE_OWNED_SURFACE

    def __init__(
        self,
        *,
        runtime_context: Optional[Mapping[str, Any]] = None,
        env: Optional[Mapping[str, str]] = None,
    ):
        self.runtime_context: Dict[str, Any] = dict(runtime_context or {})
        self._env: Optional[Dict[str, str]] = dict(env) if env is not None else None

        self.binary_path = resolve_cmux_tool_cmd(self._env)
        self.resolution_source = (
            RESOLUTION_ENV_OVERRIDE
            if (self._env or os.environ).get(ENV_CMUX_TOOL_CMD)
            else RESOLUTION_OPAL_INSTALL
        )
        # cmux-tool은 버전을 발행하지 않는다. 없는 값을 지어내면 §A.15 게이트가 거짓
        # 근거로 후보를 거르게 되므로 None으로 둔다(manifest의 cmux minimum은 0.0.0).
        self.declared_version: Optional[str] = None

        self._owned_surfaces: List[str] = []   # 이 run이 연 surface — 정리 대상
        self._user_owned: List[str] = []       # 사용자 surface — 정리 금지(C-2)
        self._assertion_results: List[Dict[str, Any]] = []
        self._action_log: List[Dict[str, Any]] = []
        self._snapshots: Dict[str, str] = {}
        self._cleanup_record: Dict[str, Any] = {}
        # 증적 관문을 실제로 통과한 종류만 쌓인다 — `observed_evidence()`의 유일한 근거다.
        self._captured_kinds: List[str] = []

    # ── 내부 공통 ────────────────────────────────────────────────────────────
    def _call(self, args: Sequence[str]) -> Dict[str, Any]:
        """cmux-tool 한 번 호출. mode A 위반 인자는 여기서 최종 차단한다(C-DRV-5)."""
        argv = [str(item) for item in args]
        if "--surface" in argv:
            raise e2e_drivers.DriverError(
                "cmux_mode_a_violation",
                "mode A forbids --surface: this driver never reuses an existing surface",
            )
        result = call_cmux_tool(argv, env=self._env)
        self._record_surface_ownership(result)
        return result

    def _record_surface_ownership(self, result: Mapping[str, Any]) -> None:
        """cmux-tool이 알려준 surface 소유권을 대장에 반영한다.

        `user_owned=true`면 사용자 것이다 — 정리 대장이 아니라 보존 대장으로 간다. 이
        분기 하나가 C-2를 코드 구조로 만든다.
        """
        surface = result.get("surface") or result.get("new_surface")
        if not surface:
            return
        surface = str(surface)
        if result.get("user_owned"):
            if surface not in self._user_owned:
                self._user_owned.append(surface)
            return
        if surface not in self._owned_surfaces:
            self._owned_surfaces.append(surface)

    @staticmethod
    def _raise_if_error(result: Mapping[str, Any], *, operation: str) -> None:
        error_code = result.get("error")
        if not result.get("ok") and error_code:
            raise CmuxToolError(
                str(error_code),
                str(result.get("detail") or f"cmux-tool {operation} failed: {error_code}"),
                raw=result,
            )

    def _log_action(self, kind: str, payload: Mapping[str, Any]) -> None:
        self._action_log.append({"action": kind, **dict(payload)})

    # ── §B.2 probe ───────────────────────────────────────────────────────────
    def op_probe(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """§A.8 probe 결과를 **실행 결과로만** 만든다(C-DRV-2 [MUST]).

        판정 수단은 비파괴 읽기인 `snapshot`이다. 이 한 번의 실행이 (1) cmux 설치와
        cmux 터미널 여부(`_guard_cmux_env` → `not_in_cmux`·`cmux_not_installed`)와
        (2) `snapshot` capability를 동시에 확인한다 — 둘을 각각 추정으로 채우지 않는다.
        읽어 온 snapshot 본문은 여기서 버린다(probe는 증적을 남기지 않는다).
        """
        capabilities = e2e_drivers.default_capabilities()
        # 미지원은 "없음"이며 그 사실 자체는 확정돼 있다 — probed=true로 못 박아 이 후보를
        # 요구 시나리오에서 실행 전에 걸러지게 한다(§A.8).
        for key in UNSUPPORTED_CAPABILITIES:
            capabilities[key] = {"available": False, "route": "exec", "probed": True}

        result = self._call(["snapshot", "--compact"])
        error_code = result.get("error")
        if not result.get("ok") and error_code:
            return {
                "available": False,
                "version": None,
                # cmux-tool 원문 code를 그대로 싣는다(NR-7).
                "unavailable_reason": str(error_code),
                "capabilities": capabilities,
            }

        capabilities["snapshot"] = {"available": True, "route": "exec", "probed": True}
        return {"available": True, "version": None, "capabilities": capabilities}

    # ── §B.2 open / close — 소유권이 갈리는 두 연산 ──────────────────────────
    def op_open(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{url, isolation_key}` → `{handle, owned, current_url}`.

        [MUST] mode A — `--surface`를 전달하지 않아 cmux-tool이 **신규** surface를 만든다.
        호출자가 재사용할 surface를 지정하면 B/C 모드가 되므로 실행 없이 거부한다.
        """
        if request.get("surface") or request.get("reuse_surface"):
            raise e2e_drivers.DriverError(
                "cmux_mode_a_violation",
                "mode A forbids reusing a surface: open always creates a new one",
            )
        url = request.get("url")

        args = ["open"]
        if url:
            args.append(str(url))
        result = self._call(args)
        self._raise_if_error(result, operation="open")

        surface = result.get("surface") or result.get("new_surface")
        handle = str(surface) if surface else str(request.get("isolation_key") or "cmux-surface")
        self._log_action("open", {"url": url, "surface": surface})
        return {
            "handle": handle,
            # 우리가 연 신규 surface만 owned다. 사용자 surface는 여기에 올라오지 않는다.
            "owned": bool(surface) and str(surface) in self._owned_surfaces,
            "current_url": url,
        }

    def op_close(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{handle}` → `{closed, released[], leaked[], skipped_user_owned[]}`.

        [MUST] 정리 대상은 `_owned_surfaces`뿐이다. 사용자 surface는 `skipped_user_owned`로
        **기록만** 하고 손대지 않는다(C-DRV-5, C-2). 대장에 없는 handle은 거부한다 — 남의
        자원을 우리 것으로 착각해 닫는 경로를 열지 않기 위해서다.
        """
        handle = request.get("handle")
        if handle is not None and str(handle) in self._user_owned:
            raise e2e_drivers.DriverError(
                "cmux_close_user_owned_surface",
                f"{handle!r} is a user-owned surface — refusing to close it",
            )
        if handle is not None and str(handle) not in self._owned_surfaces:
            raise e2e_drivers.DriverError(
                "driver_close_unowned_handle",
                f"{handle!r} was not opened by this run — refusing to close a resource we do not own",
            )

        targets = [str(handle)] if handle is not None else list(self._owned_surfaces)
        released: List[str] = []
        leaked: List[str] = []
        for item in targets:
            # mode A 신규 surface 정리 — cmux-tool에 --surface를 주지 않으므로 이 run이
            # 연 surface에만 작용한다(사용자 surface 미훼손).
            result = self._call(["close"])
            if result.get("error"):
                leaked.append(item)
                continue
            released.append(item)
            if item in self._owned_surfaces:
                self._owned_surfaces.remove(item)

        self._log_action("close", {"released": list(released), "leaked": list(leaked)})
        self._cleanup_record = {
            "released": list(released),
            "leaked": list(leaked),
            "skipped_user_owned": list(self._user_owned),
        }
        return {
            "closed": not leaked,
            "released": released,
            "leaked": leaked,
            "skipped_user_owned": list(self._user_owned),
        }

    # ── §B.2 snapshot / act / wait ───────────────────────────────────────────
    def op_snapshot(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{handle, label}` → `{snapshot, current_url, artifact_path}`."""
        result = self._call(["snapshot", "--compact"])
        self._raise_if_error(result, operation="snapshot")

        label = str(request.get("label") or "after")
        text = str(result.get("snapshot_text") or "")
        self._snapshots[label] = text
        artifact_path = SNAPSHOT_ARTIFACTS.get(label, f"browser/{label}.snapshot")
        writer = self._writer(request)
        written = (
            writer.write_text(artifact_path, text, kind="snapshot", observed=True)
            if writer is not None
            else None
        )
        self._log_action("snapshot", {"label": label, "length": result.get("length")})
        return {"snapshot": text, "current_url": request.get("current_url"), "artifact_path": written or artifact_path}

    def op_act(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{handle, action:{kind, target, value?}}` → `{ok, action_result, current_url}`."""
        action = request.get("action") or {}
        if not isinstance(action, Mapping):
            raise e2e_drivers.DriverError("driver_act_action_required", "act requires an action object")
        kind = str(action.get("kind") or "")
        subcommand = _ACT_SUBCOMMANDS.get(kind)
        if subcommand is None:
            raise e2e_drivers.DriverError(
                "cmux_unsupported_action",
                f"{kind!r} is not one of {sorted(_ACT_SUBCOMMANDS)}",
            )

        args: List[str] = [subcommand]
        target = action.get("target")
        if target is not None:
            args.append(str(target))
        if kind == "fill" and action.get("value") is not None:
            args += ["--value", str(action.get("value"))]

        result = self._call(args)
        self._raise_if_error(result, operation=kind)
        self._log_action(kind, {"target": target, "value": action.get("value")})
        return {
            "ok": bool(result.get("ok")),
            "action_result": result,
            "current_url": result.get("to_url") or result.get("after_url") or target,
        }

    def op_wait(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{handle, condition, wait_kind, timeout_ms}` → `{satisfied, wait_kind, elapsed_ms}`.

        `wait_kind` 필수 검증은 기반 클래스 `dispatch()`가 이미 집행한다(C-DRV-1). 여기서
        다시 판정하지 않고, 대신 그 값을 결과에 그대로 실어 호출자가 `fail`/`infra_error`를
        가를 수 있게 한다.
        """
        condition = request.get("condition") or {}
        args: List[str] = ["wait"]
        if isinstance(condition, Mapping):
            for key, flag in (
                ("selector", "--selector"),
                ("text", "--text"),
                ("url_contains", "--url-contains"),
                ("load_state", "--load-state"),
                ("function", "--function"),
            ):
                if condition.get(key) is not None:
                    args += [flag, str(condition.get(key))]
                    break
        elif condition:
            args.append(str(condition))
        if request.get("timeout_ms") is not None:
            args += ["--timeout-ms", str(request.get("timeout_ms"))]

        result = self._call(args)
        self._raise_if_error(result, operation="wait")
        self._log_action("wait", {"condition": condition, "wait_kind": request.get("wait_kind")})
        return {
            "satisfied": bool(result.get("matched")),
            "wait_kind": request.get("wait_kind"),
            "elapsed_ms": result.get("elapsed_ms"),
        }

    # ── §B.2 assert — C-DRV-4의 본질 ─────────────────────────────────────────
    def op_assert(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{handle, assertion:{id, verifier, expected}}` → `{id, expected, actual, passed}`.

        [MUST] 여기서 만든 결과만 `assertion_results()`에 쌓인다. `open`·`navigate`는
        아무 것도 쌓지 않으므로 그것만 수행한 run은 `assertion_results`가 비고,
        `validate_pass_requirements`가 `assertion_required`로 `fail`을 낸다(C-DRV-4).
        """
        assertion = request.get("assertion") or {}
        if not isinstance(assertion, Mapping) or assertion.get("id") is None:
            raise e2e_drivers.DriverError("driver_assert_id_required", "assert requires assertion.id")
        verifier = str(assertion.get("verifier") or "")
        if verifier not in VERIFIERS:
            raise e2e_drivers.DriverError(
                "cmux_unsupported_verifier",
                f"{verifier!r} is not one of {VERIFIERS}",
            )
        match = str(assertion.get("match") or MATCH_EQUALS)
        if match not in MATCHERS:
            raise e2e_drivers.DriverError("cmux_unsupported_matcher", f"{match!r} is not one of {MATCHERS}")

        if verifier == VERIFIER_EVAL:
            args = ["eval", "--script", str(assertion.get("script") or assertion.get("target") or "")]
            key = "result"
        else:
            args = ["get", str(assertion.get("target") or "")]
            if verifier == VERIFIER_DOM_ATTRIBUTE:
                args += ["--attr", str(assertion.get("attribute") or "")]
            key = "value"

        result = self._call(args)
        self._raise_if_error(result, operation="assert")

        actual = result.get(key)
        expected = assertion.get("expected")
        passed = (
            str(expected) in str(actual)
            if match == MATCH_CONTAINS
            else str(actual) == str(expected)
        )
        record = {
            "id": str(assertion.get("id")),
            "expected": expected,
            "actual": actual,
            "passed": bool(passed),
            "verifier": verifier,
            "match": match,
        }
        self._assertion_results.append(record)
        self._log_action("assert", {"id": record["id"], "passed": record["passed"]})
        return dict(record)

    # ── §B.2 capture ─────────────────────────────────────────────────────────
    def op_capture(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{handle, evidence_spec[]}` → `{artifacts:{name→path}, redacted, redaction_failed}`.

        [MUST] 파일을 직접 쓰지 않는다 — 호출자가 넘긴 `EvidenceWriter` 관문을 통과시킨다
        (§C.2, redaction 우회 경로 금지). writer가 없으면 아무 것도 쓰지 않고 요청분을
        `unsupported`로 돌려준다 — 쓰지 않은 것을 썼다고 보고하지 않는다.
        """
        writer = self._writer(request)
        specs = [str(item) for item in (request.get("evidence_spec") or [])]
        artifacts: Dict[str, str] = {}
        unsupported: List[str] = []

        for spec in specs:
            kind = e2e_evidence.canonical_kind(spec)
            if kind in UNSUPPORTED_CAPABILITIES:
                # 없는 수단으로 만든 증적은 없다. 조용히 빈 파일을 남기지 않는다.
                unsupported.append(spec)
                continue
            if writer is None:
                unsupported.append(spec)
                continue
            if kind == "action_log":
                artifacts[kind] = writer.write_jsonl(
                    e2e_evidence.EVIDENCE_PATHS["action_log"], list(self._action_log), kind="action_log"
                )
            elif kind == "assertion_evidence":
                artifacts[kind] = writer.write_json(
                    e2e_evidence.EVIDENCE_PATHS["assertion_evidence"],
                    {"assertions": list(self._assertion_results)},
                    kind="assertion_evidence",
                )
            elif kind == "cleanup":
                artifacts[kind] = writer.write_json(
                    e2e_evidence.EVIDENCE_PATHS["cleanup"], dict(self._cleanup_record), kind="cleanup"
                )
            elif kind == "snapshot":
                for label, text in self._snapshots.items():
                    artifacts[f"snapshot:{label}"] = writer.write_text(
                        SNAPSHOT_ARTIFACTS.get(label, f"browser/{label}.snapshot"), text, kind="snapshot"
                    )
            else:
                unsupported.append(spec)

        for kind in artifacts:
            base = kind.split(":", 1)[0]
            if base not in self._captured_kinds:
                self._captured_kinds.append(base)

        records = writer.redaction_records() if writer is not None else []
        return {
            "artifacts": artifacts,
            "unsupported": unsupported,
            "redacted": bool(records),
            "redaction_failed": any(item.get("failed") for item in records),
        }

    def _writer(self, request: Mapping[str, Any]):
        return request.get("evidence_writer") or self.runtime_context.get("evidence_writer")

    # ── 소유·관측 대장 ───────────────────────────────────────────────────────
    def assertion_results(self) -> List[Dict[str, Any]]:
        """실제 `assert` 연산이 만든 결과만 돌려준다. 비어 있음은 그 자체로 정보다."""
        return [dict(item) for item in self._assertion_results]

    def action_log(self) -> List[Dict[str, Any]]:
        return [dict(item) for item in self._action_log]

    def observed_evidence(self) -> List[str]:
        """증적 관문을 **실제로 통과해 기록된** 종류만 돌려준다.

        메모리에 로그를 모았다는 사실은 증적이 아니다 — artifact로 남지 않은 것을
        관측분으로 세면 결손이 판정에 도달하지 못한다(S-5). 그래서 근거는 `op_capture`가
        writer로 커밋한 목록 하나뿐이다.
        """
        return list(self._captured_kinds)

    def owned_resources(self) -> Dict[str, List[str]]:
        """`owned.json` 기록 근거. 사용자 surface는 소유 자원이 아니라 보존 대상이다."""
        return {
            "browser_pages": list(self._owned_surfaces),
            "skipped_user_owned": list(self._user_owned),
        }


# ─── 레지스트리 등록 ─────────────────────────────────────────────────────────
def _factory(*, runtime_context: Optional[Mapping[str, Any]] = None, **_kwargs) -> CmuxDriver:
    return CmuxDriver(runtime_context=runtime_context)


def register() -> None:
    """후보 레지스트리에 cmux/owned-surface를 등록한다(후보 순서는 `drivers/__init__` 소유)."""
    e2e_drivers.register_driver(DRIVER_NAME, SESSION_MODE_OWNED_SURFACE, _factory)


register()
