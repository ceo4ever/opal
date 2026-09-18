"""
@header {
  "module": "ports",
  "layer": "util",
  "domain": "opal-tools",
  "description": "포트 확보의 유일한 진입점. T01의 find_free_port(bind(0) 1건 확보)를 그대로 두고, 그 곁에 T03 allocator를 추가한다 — O_CREAT|O_EXCL allocator lockfile(C-LEASE-1), {artifact_root}/.leases/{lease_id}.json lease record(§A.7), owner_pid 생존 판정 기반 stale 회수(C-LEASE-2), 사용자 소유 포트 제외(TASK.md C-2). lib.e2e.runtime은 이 모듈을 호출하지 않는다(D-11 — 포트 확보 책임은 호출자에게 있다).",
  "exports": ["MAX_PORT_ATTEMPTS", "EXCLUDED_PORTS", "LEASE_SCHEMA_VERSION", "LeaseRecord", "PortLeaseError", "find_free_port", "lease_dir_for", "allocator_lock", "reclaim_stale_leases", "read_leases", "lease_ports", "confirm_lease", "release_lease", "release_leases"]
}
"""

from __future__ import annotations

import socket

MAX_PORT_ATTEMPTS = 5


def find_free_port(host: str = "127.0.0.1") -> int:
    """host에 bind 가능한 임시 포트 1건을 확보해 반환한다.

    확보 이후 실제 기동 전까지 다른 프로세스가 같은 포트를 선점할 수 있는 TOCTOU 창은
    닫지 않는다(H-5) — strict-port 기동 실패를 신호로 호출자가 MAX_PORT_ATTEMPTS회까지
    재확보하는 것으로 완화한다. 창을 닫는 allocator lock은 T03 소유다.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]


# ─────────────────────────────────────────────────────────────────────────────
# T03 allocator — lease record · allocator lock · stale 회수 (CONTRACT.md §A.7)
#
# 위의 find_free_port는 치환하지 않는다. allocator는 그 함수를 후보 생성기로 쓰고,
# 살아 있는 lease가 점유한 포트와 사용자 소유 포트를 걸러내는 층을 그 위에 얹는다.
# ─────────────────────────────────────────────────────────────────────────────

import errno
import json
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from lib.e2e import process as e2e_process
from lib.e2e_contract import E2E_CONTRACT_SCHEMA_VERSION

LEASE_SCHEMA_VERSION = E2E_CONTRACT_SCHEMA_VERSION

# TASK.md C-2 — 사용자 소유 자원. Console daemon이 127.0.0.1:7823에서 상시 가동 중이므로
# 임대 후보에서 제외한다. 종료·재시작은 하지 않는다.
EXCLUDED_PORTS = (7823,)

_LEASE_DIR_NAME = ".leases"
_LOCK_NAME = ".lock"
_LOCK_TIMEOUT_S = 15.0
_LOCK_POLL_S = 0.02
# 소유 프로세스가 사라진 lock 파일을 이 시간 뒤에는 깨뜨린다(교착 방지).
_LOCK_STALE_S = 60.0
# 한 번의 lease_ports 호출에서 허용하는 후보 bind 시도 수. MAX_PORT_ATTEMPTS는
# 기동 실패(EADDRINUSE) 후 재임대 상한(§A.7 attempt)이고, 이것은 그와 별개로 한 번의
# 할당 안에서 이미 점유된 후보를 건너뛰기 위한 상한이다.
_CANDIDATE_ATTEMPTS = 64

_LEASE_STATE_RESERVED = "reserved"
_LEASE_STATE_CONFIRMED = "confirmed"
_LEASE_STATE_RELEASED = "released"


class PortLeaseError(Exception):
    """포트 임대 실패. 상태·exit 문자열은 만들지 않는다(계약 규칙 C-125-1).

    detail_code는 test_tool.ERROR_CODES의 키이며 최종 판정은 호출자가 수행한다.
    """

    def __init__(self, detail_code: str, detail: str = ""):
        self.detail_code = detail_code
        self.detail = detail
        super().__init__(f"{detail_code}: {detail}" if detail else detail_code)


@dataclass
class LeaseRecord:
    schema_version: str
    lease_id: str
    run_id: str
    owner_pid: int
    port: int
    role: str
    state: str
    created_at: str
    confirmed_at: Optional[str]
    attempt: int

    def to_dict(self) -> dict:
        return asdict(self)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def lease_dir_for(artifact_root: str) -> Path:
    """CONTRACT.md §A.7 — lease record 루트 `{artifact_root}/.leases/`."""
    path = Path(artifact_root) / _LEASE_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def allocator_lock(lease_dir: Path, *, timeout_s: float = _LOCK_TIMEOUT_S):
    """allocator lock. 계약 규칙 C-LEASE-1 — O_CREAT|O_EXCL만 쓰고 fcntl.flock은 쓰지 않는다.

    lock 파일에는 소유 pid를 기록한다. 소유 pid가 죽었거나 파일이 _LOCK_STALE_S보다
    오래됐으면 깨뜨린다 — 소유자가 비정상 종료해도 다음 run이 영구 대기하지 않는다.
    PID 생존 판정은 lib/e2e/process.py 단일 어댑터로만 한다(C-LEASE-2, TD-16).
    """
    lock_path = lease_dir / _LOCK_NAME
    deadline = time.monotonic() + timeout_s
    acquired = False
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(fd, str(os.getpid()).encode("utf-8"))
            os.close(fd)
            acquired = True
            break
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise PortLeaseError("e2e_port_lease_failed", f"allocator lock error: {exc}")
            if _lock_is_stale(lock_path):
                _break_lock(lock_path)
                continue
            if time.monotonic() >= deadline:
                raise PortLeaseError(
                    "e2e_port_lease_failed",
                    "allocator lock is held by another run and did not release in time",
                )
            time.sleep(_LOCK_POLL_S)
    try:
        yield lease_dir
    finally:
        if acquired:
            _break_lock(lock_path)


def _lock_is_stale(lock_path: Path) -> bool:
    try:
        owner = int(lock_path.read_text(encoding="utf-8").strip() or "0")
    except (OSError, ValueError):
        owner = 0
    if owner and not e2e_process.pid_alive(owner):
        return True
    try:
        age = time.time() - lock_path.stat().st_mtime
    except OSError:
        return False
    return age > _LOCK_STALE_S


def _break_lock(lock_path: Path) -> None:
    try:
        lock_path.unlink()
    except OSError:
        pass


def read_leases(lease_dir: Path) -> list:
    """lease 디렉터리의 record 전건을 읽는다. 손상된 파일은 건너뛴다."""
    records = []
    for path in sorted(lease_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("lease_id"):
            records.append((path, data))
    return records


def reclaim_stale_leases(lease_dir: Path) -> list:
    """계약 규칙 C-LEASE-2 — owner_pid가 살아 있지 않은 record를 회수한다.

    회수한 lease_id 목록을 반환한다. 호출자는 이를 run 산출물에 기록한다(S-2).
    이름 패턴으로 프로세스를 찾지 않으며 어떤 프로세스도 종료하지 않는다 —
    회수 대상은 record 파일뿐이다(TASK.md C-9, CONTRACT.md §C.1).
    """
    reclaimed = []
    for path, data in read_leases(lease_dir):
        if data.get("state") == _LEASE_STATE_RELEASED:
            _unlink(path)
            continue
        owner = data.get("owner_pid")
        if not isinstance(owner, int) or owner <= 0:
            reclaimed.append(str(data.get("lease_id")))
            _unlink(path)
            continue
        if not e2e_process.pid_alive(owner):
            reclaimed.append(str(data.get("lease_id")))
            _unlink(path)
    return reclaimed


def _unlink(path: Path) -> None:
    try:
        path.unlink()
    except OSError:
        pass


def _held_ports(lease_dir: Path) -> set:
    held = set()
    for _, data in read_leases(lease_dir):
        if data.get("state") == _LEASE_STATE_RELEASED:
            continue
        port = data.get("port")
        if isinstance(port, int):
            held.add(port)
    return held


def lease_ports(
    *,
    artifact_root: str,
    run_id: str,
    roles: Iterable[str],
    host: str = "127.0.0.1",
    attempt: int = 1,
    excluded_ports: Iterable[int] = EXCLUDED_PORTS,
) -> tuple:
    """roles 각각에 포트를 임대하고 `(leases, reclaimed_lease_ids)`를 반환한다.

    allocator lock 아래에서 (1) stale record 회수 → (2) 살아 있는 record가 점유한 포트와
    사용자 소유 포트를 제외한 후보 확보 → (3) record 기록을 원자적으로 수행한다. 후보 socket은
    세 role의 포트가 모두 정해질 때까지 열어 두었다가 한꺼번에 닫는다 — 먼저 닫으면 OS가
    같은 포트를 바로 다음 후보로 되돌려 줄 수 있다(H-5 TOCTOU 창 축소).
    """
    lease_dir = lease_dir_for(artifact_root)
    excluded = set(excluded_ports)
    leases = []
    with allocator_lock(lease_dir):
        reclaimed = reclaim_stale_leases(lease_dir)
        blocked = _held_ports(lease_dir) | excluded
        open_sockets = []
        try:
            for role in roles:
                port = _pick_port(host, blocked, open_sockets)
                blocked.add(port)
                record = LeaseRecord(
                    schema_version=LEASE_SCHEMA_VERSION,
                    lease_id=f"{run_id}-{role}",
                    run_id=run_id,
                    owner_pid=os.getpid(),
                    port=port,
                    role=role,
                    state=_LEASE_STATE_RESERVED,
                    created_at=_now_iso(),
                    confirmed_at=None,
                    attempt=attempt,
                )
                _write_lease(lease_dir, record)
                leases.append(record)
        finally:
            for sock in open_sockets:
                sock.close()
    return (leases, reclaimed)


def _pick_port(host: str, blocked: set, open_sockets: list) -> int:
    for _ in range(_CANDIDATE_ATTEMPTS):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((host, 0))
        except OSError:
            sock.close()
            continue
        port = sock.getsockname()[1]
        open_sockets.append(sock)
        if port not in blocked:
            return port
    raise PortLeaseError(
        "e2e_port_lease_failed",
        "no free port outside the set already leased or reserved by the user",
    )


def _write_lease(lease_dir: Path, record: LeaseRecord) -> Path:
    path = lease_dir / f"{record.lease_id}.json"
    path.write_text(json.dumps(record.to_dict(), ensure_ascii=False), encoding="utf-8")
    return path


def confirm_lease(artifact_root: str, record: LeaseRecord) -> LeaseRecord:
    """health 통과 시각을 기록해 record를 confirmed로 올린다(§A.7)."""
    record.state = _LEASE_STATE_CONFIRMED
    record.confirmed_at = _now_iso()
    _write_lease(lease_dir_for(artifact_root), record)
    return record


def release_lease(artifact_root: str, lease_id: str) -> None:
    """자기 run이 만든 record만 제거한다."""
    _unlink(lease_dir_for(artifact_root) / f"{lease_id}.json")


def release_leases(artifact_root: str, records: Iterable[LeaseRecord]) -> list:
    released = []
    for record in records:
        release_lease(artifact_root, record.lease_id)
        record.state = _LEASE_STATE_RELEASED
        released.append(record.lease_id)
    return released
