"""
@header {
  "module": "runtime",
  "layer": "util",
  "domain": "opal-tools",
  "description": "설정 기반 SUT 기동 — start_service가 lib/e2e/environment.render_service로 확정된 서비스 1건(argv·cwd·env·health)을 호출자가 넘긴 포트로 프로세스 그룹 기동하고, health 선언에 따라 wait_http_health(경로·기대 상태·json_field) 또는 포트 오픈 대기로 기동 완료를 판정한다. 실패하면 그 그룹을 회수한 뒤 SutStartupError(reason 3종)를 올린다. stop_all은 그룹 단위 회수 결과(CleanupReport)를 집계한다. 상태·exit 문자열·포트 확보는 다루지 않는다.",
  "exports": ["SutHandle", "CleanupReport", "SutStartupError", "start_service", "wait_http_health", "stop_all"],
  "depends": ["process"]
}

lib.e2e.runtime — 포트는 이 모듈이 확보하지 않는다(호출자가 임대해 넘긴다). 무엇을 어떻게
띄울지는 프로젝트 설정(`.opal/e2e/environment.json`)이 소유하며 이 모듈은 특정 제품의 경로·
명령을 알지 않는다. OS 조건문은 두지 않으며 프로세스 기동·회수는 lib.e2e.process에 위임한다.
"""

from __future__ import annotations

import json
import os
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from lib.e2e import process as e2e_process

# reason 코드 집합 — e2e_contract의 FINAL_STATUSES/OPERATIONAL_STATUSES/PROFILES 값과
# 교집합 0(C-125-1, MV-19(a)). 상태 매핑은 T04 orchestrator가 e2e_contract 함수로만 수행한다.
#
# 오너십 (A-7): "process_exited_early"·"health_timeout"·"health_bad_response"는 이 모듈이
# 단일 시도의 실패로 직접 raise한다. "port_bind_exhausted"는 이 모듈이 raise하지 않는다 —
# MAX_PORT_ATTEMPTS회 재확보 루프는 호출자 책임(D-11·D-13·H-5)이므로, 소진 판정과 그 reason의
# raise도 호출자(재시도 루프를 도는 쪽)가 수행한다.
_REASON_PROCESS_EXITED_EARLY = "process_exited_early"
_REASON_HEALTH_TIMEOUT = "health_timeout"
_REASON_HEALTH_BAD_RESPONSE = "health_bad_response"


class SutStartupError(Exception):
    def __init__(self, reason: str, detail: str = ""):
        self.reason = reason
        self.detail = detail
        super().__init__(f"{reason}: {detail}" if detail else reason)


@dataclass
class SutHandle:
    role: str  # 설정 서비스 id
    port: int
    url: str
    spawned: e2e_process.SpawnedProcess
    log_paths: dict = field(default_factory=dict)


@dataclass
class CleanupReport:
    released: list
    leaked: list[int]


def _log_paths(artifact_dir: str, role: str) -> dict:
    server_dir = Path(artifact_dir) / "server"
    server_dir.mkdir(parents=True, exist_ok=True)
    return {
        "stdout": str(server_dir / f"{role}.log"),
        "stderr": str(server_dir / f"{role}.err.log"),
    }


# 기동 직후 조기 종료(strict-port 충돌·import 실패 등)를 잡기 위한 짧은 관찰 구간.
_EARLY_EXIT_GRACE_S = 0.3


def start_service(rendered: dict, *, role: str, port: int, artifact_dir: str) -> SutHandle:
    """render_service 결과 1건을 기동하고 health를 통과시킨 handle을 돌려준다.

    - `rendered`: `lib.e2e.environment.render_service` 반환값(argv·cwd·env·health·
      startup_timeout_s·host·url). env는 부모 환경 위에 덮어쓴다.
    - port는 호출자가 임대해 넘긴다. 명령이 그 포트로 strict 바인딩하는지는 설정이 책임진다.
    - health `http`: `url + path`가 expect_status를 돌려주고(json_field가 있으면 그 키가
      JSON 본문에 있어야) 통과. `port`: host:port가 열리면 통과. 제한 시간은 startup_timeout_s.
    - 실패하면 이 함수가 띄운 그룹을 회수한 뒤 SutStartupError를 올린다(누수 방지).
    """
    env = dict(os.environ)
    env.update(rendered.get("env") or {})
    host = rendered.get("host") or "127.0.0.1"
    url = rendered.get("url") or f"http://{host}:{port}"
    timeout_s = float(rendered.get("startup_timeout_s") or 60.0)
    health = rendered.get("health") or {"type": "port"}

    log_paths = _log_paths(artifact_dir, role)
    try:
        spawned = e2e_process.spawn_process_group(
            list(rendered["argv"]),
            cwd=rendered.get("cwd"),
            env=env,
            stdout_path=log_paths["stdout"],
            stderr_path=log_paths["stderr"],
        )
    except OSError as exc:
        raise SutStartupError(
            _REASON_PROCESS_EXITED_EARLY,
            f"{role} process could not be spawned ({type(exc).__name__}: {exc}); log={log_paths['stderr']}",
        ) from exc

    handle = SutHandle(role=role, port=port, url=url, spawned=spawned, log_paths=log_paths)
    try:
        time.sleep(_EARLY_EXIT_GRACE_S)
        _raise_if_exited(handle)
        if health.get("type") == "http":
            wait_http_health(
                url,
                health.get("path") or "/",
                health.get("expect_status") or 200,
                health.get("json_field"),
                timeout_s,
                spawned=spawned,
            )
        else:
            _wait_port_open(host, port, spawned=spawned, timeout_s=timeout_s)
    except SutStartupError as exc:
        e2e_process.terminate_process_group(spawned.pgid, popen=spawned.popen)
        raise SutStartupError(exc.reason, f"{role}: {exc.detail}; log={log_paths['stderr']}") from exc
    return handle


def _raise_if_exited(handle: SutHandle) -> None:
    popen = handle.spawned.popen
    if popen.poll() is not None:
        raise SutStartupError(
            _REASON_PROCESS_EXITED_EARLY,
            f"process exited early (returncode={popen.returncode})",
        )


def _wait_port_open(
    host: str, port: int, *, spawned: e2e_process.SpawnedProcess, timeout_s: float
) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if spawned.popen.poll() is not None:
            raise SutStartupError(
                _REASON_PROCESS_EXITED_EARLY,
                f"process exited early (returncode={spawned.popen.returncode})",
            )
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.3)
            try:
                sock.connect((host, port))
                return
            except OSError:
                pass
        time.sleep(0.3)
    raise SutStartupError(_REASON_HEALTH_TIMEOUT, f"port {host}:{port} did not open in {timeout_s:g}s")


def wait_http_health(
    url: str,
    path: str,
    expect_status: int,
    json_field: Optional[str],
    timeout_s: float,
    *,
    spawned: Optional[e2e_process.SpawnedProcess] = None,
    interval_s: float = 0.3,
) -> dict:
    """GET {url}{path}를 폴링해 expect_status(+json_field 존재)를 확인한다.

    - 연결이 한 번도 성립하지 않고 시간이 다 되면 `health_timeout`.
    - 응답은 오지만 상태가 끝까지 다르면 `health_bad_response`.
    - 기대 상태의 응답에 json_field가 없거나 본문이 JSON이 아니면 즉시 `health_bad_response`.
    - `spawned`가 주어지면 대기 중 프로세스 종료를 `process_exited_early`로 올린다.
    반환: json_field 검사를 했으면 파싱된 본문, 아니면 `{}`.
    """
    target = f"{url.rstrip('/')}{path}"
    deadline = time.monotonic() + timeout_s
    last_error = ""
    last_status: Optional[int] = None
    while time.monotonic() < deadline:
        if spawned is not None and spawned.popen.poll() is not None:
            raise SutStartupError(
                _REASON_PROCESS_EXITED_EARLY,
                f"process exited early (returncode={spawned.popen.returncode})",
            )
        status: Optional[int] = None
        raw = b""
        try:
            with urllib.request.urlopen(target, timeout=2) as resp:
                status = resp.status
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            status = exc.code
            try:
                raw = exc.read()
            except OSError:
                raw = b""
        except (urllib.error.URLError, ConnectionError, OSError) as exc:
            last_error = str(exc)
        if status is not None:
            last_status = status
            if status == expect_status:
                if not json_field:
                    return {}
                try:
                    body = json.loads(raw)
                except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
                    raise SutStartupError(_REASON_HEALTH_BAD_RESPONSE, f"health response from {target} is not JSON")
                if not isinstance(body, dict) or json_field not in body:
                    raise SutStartupError(
                        _REASON_HEALTH_BAD_RESPONSE,
                        f"health response missing '{json_field}' field",
                    )
                return body
            last_error = f"unexpected status {status}"
        time.sleep(interval_s)
    if last_status is not None:
        raise SutStartupError(
            _REASON_HEALTH_BAD_RESPONSE,
            f"health {target} returned {last_status}, expected {expect_status}",
        )
    raise SutStartupError(_REASON_HEALTH_TIMEOUT, f"health check {target} timed out: {last_error}")


def stop_all(handles: list[SutHandle]) -> CleanupReport:
    """모든 handle을 그룹 단위로 회수하고 잔존 구성원을 집계한다 (D-10)."""
    released: list = []
    leaked: list[int] = []
    for handle in handles:
        result = e2e_process.terminate_process_group(
            handle.spawned.pgid, popen=handle.spawned.popen
        )
        if result.released:
            released.append({"role": handle.role, "pgid": handle.spawned.pgid})
        leaked.extend(result.leaked)
    return CleanupReport(released=released, leaked=leaked)
