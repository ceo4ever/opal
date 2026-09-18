"""
@header {
  "module": "process",
  "layer": "util",
  "domain": "opal-tools",
  "description": "T01 lib/e2e OS 분기 유일 지점(TRD.md TD-16). 프로세스 그룹 기동(spawn_process_group)·생존 판정(pid_alive)·그룹 구성원 재열거(process_group_members)·그룹 단위 회수(terminate_process_group)·임시 디렉터리 해석(temp_root)을 제공한다. 이름 패턴 매칭이 아니라 pgid 범위로만 열거·회수한다(CONTRACT.md §C.1·§C.3).",
  "exports": ["SpawnedProcess", "TerminationResult", "spawn_process_group", "pid_alive", "process_group_members", "terminate_process_group", "temp_root"]
}

lib.e2e.process — OS·실행기 분기의 단일 어댑터 모듈(TRD.md TD-16, CONTRACT.md §C.2 [MUST]).
그 외 lib/e2e/* 모듈은 sys.platform·os.name·platform.system() 분기를 갖지 않는다(D-9, MV-20).

현 범위는 POSIX(새 세션/프로세스 그룹, os.killpg, ps -g 열거)만 구현한다. 비-POSIX는
명시적 NotImplementedError로 남긴다 — 분기 지점은 이 모듈에 고정되며 Windows 실제 구현은
이 태스크 범위 밖이다(§모듈 분해 T03 정지선 표 비고).
"""

from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SpawnedProcess:
    pid: int
    pgid: int
    popen: subprocess.Popen
    stdout_path: str
    stderr_path: str


@dataclass
class TerminationResult:
    released: bool
    method: str
    leaked: list[int]


def _require_posix() -> None:
    if os.name != "posix":
        raise NotImplementedError(
            "lib.e2e.process는 현재 POSIX만 구현한다 — Windows 분기는 T03+ 범위다 (TRD.md TD-16)."
        )


def spawn_process_group(
    argv: list[str],
    *,
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
    stdout_path: str,
    stderr_path: str,
) -> SpawnedProcess:
    """새 세션/프로세스 그룹으로 child를 기동한다.

    POSIX에서는 start_new_session=True로 기동해, child의 pgid가 child 자신의 pid와
    같아지도록 만든다(부모 세션과 분리). 이렇게 해야 종료 시 pgid 단위 SIGTERM/SIGKILL로
    child가 남긴 손자 프로세스(예: vite의 esbuild)까지 함께 회수할 수 있다(D-10, TD-5).
    """
    _require_posix()

    stdout_f = open(stdout_path, "wb")
    stderr_f = open(stderr_path, "wb")
    try:
        popen = subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            stdout=stdout_f,
            stderr=stderr_f,
            start_new_session=True,
        )
    finally:
        stdout_f.close()
        stderr_f.close()

    pgid = os.getpgid(popen.pid)
    return SpawnedProcess(
        pid=popen.pid,
        pgid=pgid,
        popen=popen,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
    )


def pid_alive(pid: int) -> bool:
    """pid(또는 pgid)가 아직 살아 있는지 판정한다."""
    _require_posix()
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # 권한이 있는 다른 사용자 프로세스로 pid가 재사용된 경우 — 생존으로 간주(보수적)
        return True
    return True


def process_group_members(pgid: int) -> list[int]:
    """pgid에 속한 프로세스 pid 전건을 그룹 범위로 열거한다.

    이름 패턴 매칭이 아니라 `ps -o pid= -g <pgid>`로 pgid 범위만 조회한다
    (CONTRACT.md §C.1·§C.3 — 패턴 매칭·전역 스캔 금지).
    """
    _require_posix()
    try:
        result = subprocess.run(
            ["ps", "-o", "pid=", "-g", str(pgid)],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []
    members: list[int] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            members.append(int(line))
        except ValueError:
            continue
    return members


def terminate_process_group(
    pgid: int,
    *,
    grace_seconds: float = 5.0,
    popen: Optional[subprocess.Popen] = None,
) -> TerminationResult:
    """pgid 단위로 SIGTERM → grace 대기 → SIGKILL 후, 잔존 구성원을 재열거해 집계한다.

    D-10: leaked는 그룹 리더 pid의 생존 여부가 아니라 SIGKILL 이후 process_group_members를
    재호출해 얻은 잔존 구성원 pid 전건이다. start_new_session=True에서는 pgid == 리더 pid이므로
    리더 pid 1건만 보는 검사는 vite 손자(esbuild) 누출을 전혀 검출하지 못한다(A-4).

    `popen`이 주어지면(호출자가 그룹 리더 자신을 spawn한 Popen을 넘기면) 대기 루프 중 이를
    `poll()`해 우리 자신의 자식을 즉시 reap한다 — reap하지 않으면 리더가 종료돼도 zombie로
    남아 `process_group_members`에 계속 잡히고, 그 상태로 grace를 소진해 버린다. 이 reap은
    또한 이후 SIGKILL 호출이 이미 죽은 zombie 대신 (드물게) 재사용된 pgid의 무관한 프로세스를
    잘못 겨냥해 `PermissionError`가 나는 상황을 줄인다 — 그런 재사용 레이스가 남아도 아래에서
    `PermissionError`를 `ProcessLookupError`와 동일하게 처리해 죽지 않는다.
    """
    _require_posix()

    method = "noop"
    try:
        os.killpg(pgid, signal.SIGTERM)
        method = "sigterm"
    except (ProcessLookupError, PermissionError):
        return TerminationResult(released=True, method="already_gone", leaked=[])

    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        if popen is not None:
            popen.poll()  # 우리 자신의 리더가 종료했으면 zombie를 reap해 그룹에서 제거한다
        if not process_group_members(pgid):
            return TerminationResult(released=True, method=method, leaked=[])
        time.sleep(0.1)

    try:
        os.killpg(pgid, signal.SIGKILL)
        method = "sigkill"
    except (ProcessLookupError, PermissionError):
        return TerminationResult(released=True, method=method, leaked=[])

    # SIGKILL 직후 짧게 대기한 뒤 잔존 구성원을 재열거한다.
    if popen is not None:
        popen.poll()
    time.sleep(0.2)
    leaked = process_group_members(pgid)
    return TerminationResult(released=(leaked == []), method=method, leaked=leaked)


def temp_root() -> Path:
    """TMPDIR(또는 플랫폼 기본 임시 루트)를 해석한다."""
    return Path(tempfile.gettempdir())
