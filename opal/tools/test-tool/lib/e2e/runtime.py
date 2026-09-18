"""
@header {
  "module": "runtime",
  "layer": "util",
  "domain": "opal-tools",
  "description": "T01 최소 SUT 기동 골격 — start_backend/start_frontend(포트는 호출자가 확보해 필수 인자로 전달, D-11)로 소스 트리 backend/frontend를 strict-port로 기동하고, wait_healthy로 backend /health를 폴링하며, stop_all로 그룹 단위 회수 결과(CleanupReport)를 집계한다. 상태·exit 문자열은 다루지 않고 실패는 SutStartupError(reason=...) 예외로만 올린다(D-8) — run 상태 머신·CLI·verdict·OPAL_E2E_* 전량 주입은 T04 소유다.",
  "exports": ["SutHandle", "CleanupReport", "SutStartupError", "start_backend", "start_frontend", "wait_healthy", "stop_all"]
}

lib.e2e.runtime — 포트는 이 모듈이 확보하지 않는다(D-11). OS 조건문은 두지 않으며
(sys.platform·os.name·platform.system() 0건, D-9) 프로세스 기동·회수는 lib.e2e.process에 위임한다.
"""

from __future__ import annotations

import json
import os
import shutil
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
    role: str  # "backend" | "frontend"
    port: int
    url: str
    spawned: e2e_process.SpawnedProcess
    log_paths: dict = field(default_factory=dict)


@dataclass
class CleanupReport:
    released: list
    leaked: list[int]


def _resolve_python() -> str:
    """venv python을 우선 해석하고 없으면 sys.executable로 폴백한다.

    opal/tools/test-tool/run.sh:4가 도구 인터프리터로 선언하는 venv(fastapi·uvicorn 설치본)를
    하드코딩된 절대경로가 아니라 존재 탐색으로 해석한다 — 다른 머신에서 이 venv가 없는 경우에도
    sys.executable로 이식성을 유지한다.
    """
    import sys

    candidate = Path.home() / ".opal" / ".venv" / "bin" / "python"
    if candidate.is_file():
        return str(candidate)
    return sys.executable


def _log_paths(artifact_dir: str, role: str) -> dict:
    server_dir = Path(artifact_dir) / "server"
    server_dir.mkdir(parents=True, exist_ok=True)
    return {
        "stdout": str(server_dir / f"{role}.log"),
        "stderr": str(server_dir / f"{role}.err.log"),
    }


def start_backend(
    *,
    source_root: str,
    artifact_dir: str,
    port: int,
    env_extra: Optional[dict] = None,
) -> SutHandle:
    """backend를 strict-port로 기동한다 (D-13).

    port는 호출자가 find_free_port()로 확보해 넘긴다 — 이 함수는 포트를 자체 확보하지
    않는다(D-11). uvicorn은 지정 포트가 점유돼 있으면 스스로 기동에 실패하므로, 그것이
    strict-port 보증의 근거다.
    """
    python_bin = _resolve_python()
    argv = [
        python_bin,
        "-m",
        "uvicorn",
        "dashboard.backend.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]

    env = dict(os.environ)
    env.update(env_extra or {})

    log_paths = _log_paths(artifact_dir, "backend")
    spawned = e2e_process.spawn_process_group(
        argv,
        cwd=source_root,
        env=env,
        stdout_path=log_paths["stdout"],
        stderr_path=log_paths["stderr"],
    )

    # strict-port 기동이 즉시 실패하는 경우(EADDRINUSE 등)를 조기 검출한다.
    time.sleep(0.3)
    if spawned.popen.poll() is not None:
        raise SutStartupError(
            _REASON_PROCESS_EXITED_EARLY,
            f"backend process exited early (returncode={spawned.popen.returncode})",
        )

    return SutHandle(
        role="backend",
        port=port,
        url=f"http://127.0.0.1:{port}",
        spawned=spawned,
        log_paths=log_paths,
    )


def start_frontend(
    *,
    source_root: str,
    artifact_dir: str,
    port: int,
    backend_url: str,
    env_extra: Optional[dict] = None,
) -> SutHandle:
    """frontend(vite dev)를 strict-port로 기동하고 backend_url을 가리키게 한다 (D-12·D-13).

    port는 호출자가 find_free_port()로 확보해 넘긴다 — 이 함수는 포트를 자체 확보하지
    않는다(D-11). vite는 --strictPort로 기동해 지정 포트가 점유돼 있으면 자동으로 다른
    포트로 넘어가는 대신 기동에 실패한다.
    """
    frontend_root = str(Path(source_root) / "dashboard" / "frontend")
    npm_bin = shutil.which("npm") or "npm"
    argv = [
        npm_bin,
        "run",
        "dev",
        "--",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--strictPort",
    ]

    env = dict(os.environ)
    env["VITE_API_BASE_URL"] = backend_url
    env.update(env_extra or {})

    log_paths = _log_paths(artifact_dir, "frontend")
    spawned = e2e_process.spawn_process_group(
        argv,
        cwd=frontend_root,
        env=env,
        stdout_path=log_paths["stdout"],
        stderr_path=log_paths["stderr"],
    )

    handle = SutHandle(
        role="frontend",
        port=port,
        url=f"http://127.0.0.1:{port}",
        spawned=spawned,
        log_paths=log_paths,
    )

    # vite dev ready 타임아웃 90s (PLAN.md §Release and recovery 실측 경계) — 조기 프로세스
    # 종료(strict-port 충돌 등)와 포트 오픈 대기를 함께 다룬다.
    _wait_port_open(port, spawned=spawned, timeout_s=90.0)

    return handle


def _wait_port_open(port: int, *, spawned: e2e_process.SpawnedProcess, timeout_s: float) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if spawned.popen.poll() is not None:
            raise SutStartupError(
                _REASON_PROCESS_EXITED_EARLY,
                f"frontend process exited early (returncode={spawned.popen.returncode})",
            )
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.3)
            try:
                sock.connect(("127.0.0.1", port))
                return
            except OSError:
                pass
        time.sleep(0.3)
    raise SutStartupError(_REASON_HEALTH_TIMEOUT, f"frontend port {port} did not open in time")


def wait_healthy(base_url: str, *, timeout_s: float = 60.0, interval_s: float = 0.3) -> dict:
    """GET {base_url}/health를 폴링해 200 + JSON status 키를 확인한다 (D-14, CONTRACT.md §B.5)."""
    deadline = time.monotonic() + timeout_s
    last_error: str = ""
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=2) as resp:
                if resp.status != 200:
                    last_error = f"unexpected status {resp.status}"
                else:
                    body = json.loads(resp.read())
                    if "status" not in body:
                        raise SutStartupError(
                            _REASON_HEALTH_BAD_RESPONSE,
                            "health response missing 'status' field",
                        )
                    return body
        except SutStartupError:
            raise
        except (urllib.error.URLError, ConnectionError, OSError, json.JSONDecodeError) as exc:
            last_error = str(exc)
        time.sleep(interval_s)
    raise SutStartupError(_REASON_HEALTH_TIMEOUT, f"health check timed out: {last_error}")


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
