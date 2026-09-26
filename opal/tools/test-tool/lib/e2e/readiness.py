"""
@header {
  "module": "readiness",
  "layer": "util",
  "domain": "opal-tools",
  "description": "`test-tool e2e env-check`의 준비 검증 판정. 유효한 환경 설정을 받아 표면별 check를 정해진 순서로 실제 수행하고(서비스 기동·health·실행기 / URL 도달·응답·실행기 / human 실행기 / 데스크톱 플랫폼·앱 존재·실행기), 처음 실패한 check의 cause(닫힌 11종)와 조치 문장을 남긴다. 최상위 secrets는 환경 변수 존재만 보고 값을 싣지 않는다. 포트 임대·서비스 기동·회수는 ports·runtime·environment를, 실행기 확인은 drivers.resolve_candidates와 executors 레지스트리를 재사용하며, 여러 표면이 공유하는 서비스는 1회만 띄우고 판정 뒤 모든 서비스와 임대를 회수한다. 기동 로그는 redaction.redact_text 패턴과 from_env·최상위 secrets 값 마스킹을 거친 사본만 남기고 원문은 지운다.",
  "exports": ["CAUSE_CODES", "check_readiness"],
  "depends": ["environment", "ports", "runtime", "process", "redaction", "drivers", "executors"]
}

lib.e2e.readiness — 설정 파일 존재나 진술만으로 ready를 주지 않는다. 각 check는 실제
프로세스·실제 HTTP·실제 후보 해석 결과로만 통과한다. 기동 로그는
`<artifact-root>/readiness/<run>/<service-id>.log`에 마스킹 사본으로 모으고 check detail에 그 경로를 쓴다.
OS 판정은 process.host_platform()만 사용한다.
"""

from __future__ import annotations

import os
import shutil
import socket
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

from lib.e2e import environment as e2e_environment
from lib.e2e import ports as e2e_ports
from lib.e2e import process as e2e_process
from lib.e2e import redaction as e2e_redaction
from lib.e2e import runtime as e2e_runtime

CAUSE_CODES = (
    "service_start_failed",
    "dependency_failed",
    "health_timeout",
    "health_bad_response",
    "driver_unavailable",
    "api_executor_unavailable",
    "url_unreachable",
    "human_executor_unavailable",
    "platform_mismatch",
    "app_not_found",
    "desktop_executor_absent",
)

_REMEDIATION = {
    "service_start_failed": "서비스 command·cwd·의존성을 점검하고 check detail의 기동 로그를 확인한 뒤 다시 실행한다.",
    "dependency_failed": "먼저 실패한 의존 서비스를 고친 뒤 다시 실행한다.",
    "health_timeout": "서비스 command가 {port} 치환 토큰으로 임대 포트에 바인딩하는지와 startup_timeout_s가 충분한지 확인한다.",
    "health_bad_response": "health 경로·기대 상태·json_field 선언이 실제 응답과 맞는지 확인한다.",
    "driver_unavailable": "브라우저 driver(agent-browser 등)를 설치하거나 .opal/e2e/order.json 후보 순서를 확인한다.",
    "api_executor_unavailable": "표면 URL과 health_path가 응답하는지 확인한다.",
    "url_unreachable": "표면 url의 서버를 먼저 띄우거나 url 값을 고친다.",
    "human_executor_unavailable": "artifact-root에 쓸 수 있는지 확인한다.",
    "platform_mismatch": "이 표면은 선언된 플랫폼의 호스트에서만 검증할 수 있다.",
    "app_not_found": "app.path 또는 app.launch가 가리키는 앱을 설치하거나 경로를 고친다.",
    "desktop_executor_absent": "데스크톱 앱 실행기가 아직 없어 이 표면은 자동 검증할 수 없다. 사람 확인 표면으로 대체한다.",
}

_DESKTOP_PLATFORM = {"macos-app": "macos", "windows-app": "windows", "linux-app": "linux"}
_URL_TIMEOUT_S = 3.0
_SKIPPED = "skipped"

# startup 실패 reason(runtime.SutStartupError) → 실패한 check와 cause.
_STARTUP_REASON = {
    "process_exited_early": ("service_start", "service_start_failed"),
    "health_timeout": ("health", "health_timeout"),
    "health_bad_response": ("health", "health_bad_response"),
}


def check_readiness(
    config: Mapping[str, Any],
    *,
    project_root: str,
    artifact_root: Optional[str] = None,
    driver_registry: Optional[Mapping[Any, Callable[..., Any]]] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """정규화된 설정(environment.load의 config)으로 D-8 판정을 만든다.

    `driver_registry`는 브라우저 후보 해석에 넘길 레지스트리다(기본: 등록된 driver와
    프로젝트 선언 driver). 반환 `{ready, secrets, surfaces, run_dir}`.
    """
    root = str(Path(project_root).resolve())
    artifact_root = os.path.abspath(artifact_root or os.path.join(root, ".e2e", "artifacts"))
    run = run_id or f"readiness-{datetime.now().strftime('%Y%m%dT%H%M%S')}-{os.getpid()}"
    run_dir = Path(artifact_root) / "readiness" / run
    run_dir.mkdir(parents=True, exist_ok=True)

    secrets = [_secret_status(item) for item in config.get("secrets", [])]
    surfaces_cfg = [s for s in config.get("surfaces", []) if isinstance(s, dict)]

    services = _ServiceRunner(config, root=root, artifact_root=artifact_root, run=run, run_dir=run_dir)
    try:
        needed = [s["service"] for s in surfaces_cfg if s.get("kind") in ("web", "api") and "service" in s]
        services.start(needed)
        surfaces = [
            _judge_surface(surface, services=services, root=root, run_dir=run_dir, driver_registry=driver_registry)
            for surface in surfaces_cfg
        ]
    finally:
        services.stop()

    ready = all(s["status"] == "ready" for s in surfaces) and all(s["ok"] for s in secrets)
    return {"ready": ready, "secrets": secrets, "surfaces": surfaces, "run_dir": str(run_dir)}


# ── 비밀 ─────────────────────────────────────────────────────────────────────

def _secret_status(item: Mapping[str, Any]) -> Dict[str, Any]:
    name = str(item.get("name"))
    present = name in os.environ
    return {
        "name": name,
        "ok": present,
        "remediation": None if present else f"export {name}=... 로 환경 변수를 설정한 뒤 다시 실행한다.",
    }


# ── 서비스 기동 ──────────────────────────────────────────────────────────────

class _ServiceRunner:
    """필요한 서비스만 의존 순서로 1회씩 띄우고 결과를 서비스 id별로 기억한다."""

    def __init__(self, config: Mapping[str, Any], *, root: str, artifact_root: str, run: str, run_dir: Path):
        self.config = config
        self.root = root
        self.artifact_root = artifact_root
        self.run = run
        self.run_dir = run_dir
        self.by_id = {s["id"]: s for s in config.get("services", []) if isinstance(s, dict)}
        self.results: Dict[str, Dict[str, Any]] = {}
        self.handles: List[e2e_runtime.SutHandle] = []
        self.leases: List[e2e_ports.LeaseRecord] = []
        self.started_ids: List[str] = []
        # 로그에서 가릴 비밀 원문 — 최상위 secrets와 서비스 env의 from_env 해석값.
        self.secret_values: set = {
            os.environ[str(item.get("name"))]
            for item in config.get("secrets", [])
            if isinstance(item, dict) and os.environ.get(str(item.get("name")))
        }

    def log_path(self, service_id: str) -> str:
        return str(self.run_dir / f"{service_id}.log")

    def _closure(self, ids: List[str]) -> List[str]:
        wanted: List[str] = []
        stack = list(ids)
        while stack:
            ident = stack.pop()
            if ident in wanted or ident not in self.by_id:
                continue
            wanted.append(ident)
            stack.extend(self.by_id[ident].get("depends_on", []))
        return [i for i in e2e_environment.service_order(self.config) if i in wanted]

    def start(self, ids: List[str]) -> None:
        order = self._closure(ids)
        if not order:
            return
        try:
            self.leases, _ = e2e_ports.lease_ports(artifact_root=self.artifact_root, run_id=self.run, roles=order)
        except e2e_ports.PortLeaseError as exc:
            for ident in order:
                self.results[ident] = _failed("service_start", "service_start_failed", f"{exc.detail_code}: {exc.detail}")
            return
        ports_by_id = {lease.role: lease.port for lease in self.leases}
        for ident in order:
            self.results[ident] = self._start_one(ident, ports_by_id)

    def _start_one(self, ident: str, ports_by_id: Mapping[str, int]) -> Dict[str, Any]:
        log = self.log_path(ident)
        service = self.by_id[ident]
        failed_dep = next(
            (dep for dep in service.get("depends_on", []) if not self.results.get(dep, {}).get("ok")),
            None,
        )
        if failed_dep is not None:
            return _failed("service_start", "dependency_failed", f"dependency service '{failed_dep}' is not ready")
        port = ports_by_id[ident]
        try:
            rendered = e2e_environment.render_service(
                service, port=port, ports_by_id=ports_by_id, project_root=self.root
            )
        except ValueError as exc:
            return _failed("service_start", "service_start_failed", f"{exc}; log={log}")
        for name, value in (service.get("env") or {}).items():
            if isinstance(value, dict) and rendered["env"].get(name):
                self.secret_values.add(rendered["env"][name])
        self.started_ids.append(ident)
        try:
            handle = e2e_runtime.start_service(rendered, role=ident, port=port, artifact_dir=str(self.run_dir))
        except e2e_runtime.SutStartupError as exc:
            check, cause = _STARTUP_REASON.get(exc.reason, ("service_start", "service_start_failed"))
            detail = f"{exc.detail.split('; log=')[0]}; log={log}"
            result = _failed(check, cause, detail)
            result["start_detail"] = f"started pid group; log={log}" if check == "health" else detail
            result["port"] = port
            return result
        self.handles.append(handle)
        lease = next((item for item in self.leases if item.role == ident), None)
        if lease is not None:
            e2e_ports.confirm_lease(self.artifact_root, lease)
        health = rendered.get("health") or {}
        if health.get("type") == "http":
            health_detail = f"GET {rendered['url']}{health.get('path')} -> {health.get('expect_status', 200)}"
        else:
            health_detail = f"port {rendered['host']}:{port} open"
        return {
            "ok": True,
            "failed_check": None,
            "cause": None,
            "detail": None,
            "start_detail": f"started on {rendered['url']}; log={log}",
            "health_detail": health_detail,
            "url": rendered["url"],
            "port": port,
        }

    def stop(self) -> None:
        try:
            e2e_runtime.stop_all(self.handles)
        finally:
            e2e_ports.release_leases(self.artifact_root, self.leases)
            for ident in self.started_ids:
                _merge_logs(self.run_dir, ident, self.secret_values)


def _failed(check: str, cause: str, detail: str) -> Dict[str, Any]:
    return {"ok": False, "failed_check": check, "cause": cause, "detail": detail}


def _merge_logs(run_dir: Path, ident: str, secret_values=()) -> None:
    """runtime이 남긴 `server/<id>.log`·`.err.log`를 마스킹해 `<run>/<id>.log` 하나로 모은다.

    e2e run의 서버 로그 봉인과 같게 redaction.redact_text 패턴을 적용하고, 그 패턴이 모르는
    비밀 원문(from_env·최상위 secrets 값)은 값 자체를 MASK로 바꾼다. 원문 파일은 지운다.
    """
    server_dir = run_dir / "server"
    target = run_dir / f"{ident}.log"
    parts = []
    for name, label in ((f"{ident}.log", "stdout"), (f"{ident}.err.log", "stderr")):
        source = server_dir / name
        if source.is_file():
            parts.append(f"--- {label} ---\n" + source.read_text(encoding="utf-8", errors="replace"))
            source.unlink()
    target.write_text(_redact_log("\n".join(parts) if parts else "", secret_values), encoding="utf-8")
    try:
        server_dir.rmdir()
    except OSError:
        pass


def _redact_log(text: str, secret_values=()) -> str:
    # 긴 값부터 바꿔 한 비밀이 다른 비밀의 일부일 때 조각이 남지 않게 한다.
    for value in sorted({v for v in secret_values if v}, key=len, reverse=True):
        text = text.replace(value, e2e_redaction.MASK)
    return e2e_redaction.redact_text(text, path="readiness_log")[0]


# ── 표면 판정 ────────────────────────────────────────────────────────────────

def _judge_surface(surface, *, services: _ServiceRunner, root: str, run_dir: Path, driver_registry) -> Dict[str, Any]:
    kind = surface["kind"]
    if kind in ("web", "api") and "service" in surface:
        steps = _service_surface_steps(surface, services, root, driver_registry)
        return _sequence(surface, steps)
    if kind in ("web", "api"):
        steps = _url_surface_steps(surface, root, driver_registry)
        return _sequence(surface, steps)
    if kind == "human":
        return _sequence(surface, [("executor", lambda: _human_executor(run_dir))])
    return _desktop_surface(surface)


def _sequence(surface, steps) -> Dict[str, Any]:
    """steps를 차례로 수행하고 첫 실패 뒤는 `skipped`로 남긴다."""
    checks: List[Dict[str, Any]] = []
    cause: Optional[str] = None
    for name, run in steps:
        if cause is not None:
            checks.append({"name": name, "ok": False, "detail": _SKIPPED})
            continue
        ok, detail, failure = run()
        checks.append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            cause = failure
    return _surface_result(surface, checks, cause)


def _surface_result(surface, checks, cause) -> Dict[str, Any]:
    return {
        "id": surface["id"],
        "kind": surface["kind"],
        "status": "ready" if cause is None else "not_ready",
        "checks": checks,
        "cause": cause,
        "remediation": None if cause is None else _REMEDIATION[cause],
    }


def _service_surface_steps(surface, services: _ServiceRunner, root, driver_registry):
    ident = surface["service"]
    result = services.results.get(ident) or _failed("service_start", "service_start_failed", "service was not started")

    def start():
        if result["ok"]:
            return True, result["start_detail"], None
        if result["failed_check"] == "service_start":
            return False, result["detail"], result["cause"]
        return True, result.get("start_detail") or "started", None

    def health():
        if result["ok"]:
            return True, result["health_detail"], None
        return False, result["detail"], result["cause"]

    def executor():
        return _executor_check(surface, result.get("url"), root, driver_registry)

    return [("service_start", start), ("health", health), ("executor", executor)]


def _url_surface_steps(surface, root, driver_registry):
    url = surface["url"].rstrip("/")
    kind = surface["kind"]

    def reachable():
        parsed = urllib.parse.urlsplit(url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        try:
            with socket.create_connection((host, port), timeout=_URL_TIMEOUT_S):
                pass
        except OSError as exc:
            return False, f"connect {host}:{port} failed: {type(exc).__name__}", "url_unreachable"
        return True, f"connect {host}:{port} ok", None

    def response():
        path = surface.get("path", "/") if kind == "web" else surface.get("health_path", "/health")
        target = f"{url}{path}"
        status = _http_status(target)
        if status is None:
            return False, f"GET {target} got no response", "url_unreachable"
        passed = status < 500 if kind == "web" else status == 200
        detail = f"GET {target} -> {status}"
        return (True, detail, None) if passed else (False, detail, "health_bad_response")

    def executor():
        return _executor_check(surface, url, root, driver_registry)

    return [("reachable", reachable), ("response", response), ("executor", executor)]


def _http_status(target: str) -> Optional[int]:
    try:
        with urllib.request.urlopen(target, timeout=_URL_TIMEOUT_S) as resp:
            return int(resp.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except (urllib.error.URLError, ConnectionError, OSError, ValueError):
        return None


# ── 실행기 확인 ──────────────────────────────────────────────────────────────

def _executor_check(surface, base_url: Optional[str], root: str, driver_registry) -> Tuple[bool, str, Optional[str]]:
    if surface["kind"] == "web":
        return _browser_executor(root, driver_registry)
    return _api_executor(base_url, surface.get("health_path", "/health"))


def _browser_executor(root: str, driver_registry) -> Tuple[bool, str, Optional[str]]:
    from lib.e2e import drivers as e2e_drivers

    try:
        candidates, _ = e2e_drivers.resolve_candidates(
            runtime_context={"project_root": root, "profile": "browser", "surface_kind": "web"},
            registry=driver_registry,
            candidate_order=e2e_drivers.load_candidate_order(root),
        )
    except Exception as exc:  # noqa: BLE001 — 후보 해석 오류는 실행기 미가용으로 닫는다.
        code = getattr(exc, "detail_code", type(exc).__name__)
        return False, f"driver candidate resolution failed: {code}", "driver_unavailable"
    selected = [c for c in candidates if c.get("outcome") == "selected"]
    if selected:
        pick = selected[0]
        return True, f"selected {pick['driver']}/{pick['session_mode']}", None
    summary = ", ".join(f"{c['driver']}/{c['session_mode']}:{c.get('reason')}" for c in candidates) or "no candidates"
    return False, f"no browser driver selected ({summary})", "driver_unavailable"


def _api_executor(base_url: Optional[str], health_path: str) -> Tuple[bool, str, Optional[str]]:
    from lib.e2e import executors as e2e_executors
    from lib.e2e.executors import api as e2e_api

    if not base_url:
        return False, "no base url to probe", "api_executor_unavailable"
    e2e_api.register()
    candidates, _ = e2e_executors.resolve_executor_candidates(
        ["api"], runtime_context={"base_url": base_url, "health_path": health_path}
    )
    selected = [c for c in candidates if c.get("outcome") == "selected"]
    if selected:
        return True, f"api probe {base_url}{health_path} ok", None
    reason = candidates[0].get("reason") if candidates else "no_candidate"
    return False, f"api probe {base_url}{health_path} failed: {reason}", "api_executor_unavailable"


def _human_executor(run_dir: Path) -> Tuple[bool, str, Optional[str]]:
    from lib.e2e import executors as e2e_executors
    from lib.e2e.executors import human as e2e_human

    e2e_human.register()
    candidates, _ = e2e_executors.resolve_executor_candidates(
        ["human"], runtime_context={"artifact_dir": str(run_dir)}
    )
    if any(c.get("outcome") == "selected" for c in candidates):
        return True, "human executor registered", None
    reason = candidates[0].get("reason") if candidates else "no_candidate"
    return False, f"human executor unavailable: {reason}", "human_executor_unavailable"


# ── 데스크톱 ─────────────────────────────────────────────────────────────────

def _desktop_surface(surface) -> Dict[str, Any]:
    """데스크톱은 3항목을 모두 기록하고 실행기가 없으므로 언제나 not_ready다."""
    kind = surface["kind"]
    app = surface.get("app") or {}
    expected = _DESKTOP_PLATFORM[kind]
    host = e2e_process.host_platform()

    def platform():
        detail = f"host {host}, surface needs {expected}"
        return (True, detail, None) if host == expected else (False, detail, "platform_mismatch")

    def app_present():
        if app.get("path"):
            path = os.path.expanduser(str(app["path"]))
            return (True, f"{path} exists", None) if os.path.exists(path) else (False, f"{path} not found", "app_not_found")
        launch = app.get("launch") or []
        head = str(launch[0]) if launch else ""
        found = shutil.which(head) if head else None
        return (True, f"{found} found", None) if found else (False, f"{head!r} not found on PATH", "app_not_found")

    def executor():
        return False, f"no desktop executor exists for {kind}", "desktop_executor_absent"

    return _sequence(surface, [("platform", platform), ("app_present", app_present), ("executor", executor)])
