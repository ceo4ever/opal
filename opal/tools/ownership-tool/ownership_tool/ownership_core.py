"""
@header {
  "module": "ownership_core",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "ownership-tool 런타임 저장소 코어. D-5의 3개 저장소 경로 계산(session_registry_path·hub_lease_path·stop_receipt_path)과 스키마 dataclass(SessionRecord·LeaseRecord·StopReceipt), D-7의 저장소별 lock(<path>.lock, O_CREAT+O_RDWR+O_NOFOLLOW·0o600·LOCK_EX+LOCK_NB 재시도, 상한 2000ms) + temp→os.replace 원자 교체 헬퍼(write_json_atomic·read_json), .opal-worktrees/.meta/task_<NNN>.json 읽기 전용 어댑터(read_registry_meta), 세션 ID 해석(resolve_session_id), 실행 루트 해석(resolve_roots — <cwd>/.opal-worktrees/.meta/ 존재 시 허브, 부재 시 worktree-tool이 내려보낸 <cwd>/.opal/task-ownership.json 발급값 사본에서 allocator_root·task_path를 읽고, 둘 다 없으면 roots_unresolved 진단만 남긴다 — 어느 분기에서도 cwd 문자열 자르기·부모 순회·.opal-worktrees 문자열 탐색으로 추론하지 않는다)을 제공한다. 실패는 예외가 아니라 ok/error 구조화 dict로 반환하며 플랫폼 고유 환경변수는 claude_adapter에만 둔다.",
  "exports": [
    "DEFAULT_LOCK_TIMEOUT_MS", "RUNTIME_DIR_MODE", "RUNTIME_FILE_MODE",
    "session_registry_path", "hub_lease_path", "stop_receipt_path", "registry_meta_path",
    "SessionRecord", "LeaseRecord", "StopReceipt",
    "write_json_atomic", "read_json", "read_registry_meta", "resolve_session_id",
    "task_ownership_copy_path", "resolve_roots"
  ],
  "depends": ["claude_adapter"]
}
"""
from __future__ import annotations

import fcntl
import json
import os
import pathlib
import time
from dataclasses import asdict, dataclass

from . import claude_adapter

# D-7 — 재시도 상한 2000ms (run-log/state-tool 공용 .opal-task.lock의 30s와 분리)
DEFAULT_LOCK_TIMEOUT_MS = 2000
_LOCK_POLL_INTERVAL_SEC = 0.01

RUNTIME_DIR_MODE = 0o700
RUNTIME_FILE_MODE = 0o600


# ─────────────────────────────────────────────────────────────────────────────
# D-5 저장소 경로
# ─────────────────────────────────────────────────────────────────────────────

def session_registry_path(project_root, session_id):
    """<project_root>/.opal/run/.runtime/sessions/<session_id>.json"""
    return pathlib.Path(project_root) / ".opal" / "run" / ".runtime" / "sessions" / f"{session_id}.json"


def hub_lease_path(canonical_task_path):
    """<canonical_task_path>/run/.runtime/owner.json"""
    return pathlib.Path(canonical_task_path) / "run" / ".runtime" / "owner.json"


def stop_receipt_path(project_root, session_id):
    """<project_root>/.opal/run/.runtime/stop-guard/<session_id>.json"""
    return pathlib.Path(project_root) / ".opal" / "run" / ".runtime" / "stop-guard" / f"{session_id}.json"


def registry_meta_path(hub_root, task_number):
    """<hub_root>/.opal-worktrees/.meta/task_<NNN>.json"""
    return pathlib.Path(hub_root) / ".opal-worktrees" / ".meta" / f"task_{task_number}.json"


# ─────────────────────────────────────────────────────────────────────────────
# D-5 스키마
# ─────────────────────────────────────────────────────────────────────────────

def _from_dict(cls, data):
    if not isinstance(data, dict):
        raise TypeError("record must be a dict")
    fields = cls.__dataclass_fields__
    return cls(**{k: data.get(k) for k in fields})


@dataclass
class SessionRecord:
    """세션 registry 레코드 — sessions/<session_id>.json"""

    session_id: str = None
    cwd: str = None
    started_at: str = None
    heartbeat_at: str = None
    expires_at: str = None
    status: str = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return _from_dict(cls, data)


@dataclass
class LeaseRecord:
    """hub task lease 레코드 — <canonical_task>/run/.runtime/owner.json"""

    task_path: str = None
    owner_session_id: str = None
    generation: int = None
    claimed_at: str = None
    heartbeat_at: str = None
    lease_expires_at: str = None
    status: str = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return _from_dict(cls, data)


@dataclass
class StopReceipt:
    """stop-guard receipt — stop-guard/<session_id>.json"""

    session_id: str = None
    fingerprint: str = None
    decision_kind: str = None
    decided_at: str = None
    block_count: int = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return _from_dict(cls, data)


# ─────────────────────────────────────────────────────────────────────────────
# D-7 lock + atomic replace
# ─────────────────────────────────────────────────────────────────────────────

def _acquire_lock(lock_path, timeout_ms):
    """LOCK_EX|LOCK_NB 재시도 루프(run_log_core._acquire_lock 패턴). 성공 시 fd, 상한 초과 시 None."""
    lock_path = pathlib.Path(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True, mode=RUNTIME_DIR_MODE)
    deadline = time.monotonic() + (timeout_ms / 1000.0)
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, RUNTIME_FILE_MODE)
        except OSError:
            if time.monotonic() >= deadline:
                return None
            time.sleep(_LOCK_POLL_INTERVAL_SEC)
            continue

        try:
            os.fchmod(fd, RUNTIME_FILE_MODE)
        except OSError:
            pass

        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except OSError:
            os.close(fd)
            if time.monotonic() >= deadline:
                return None
            time.sleep(_LOCK_POLL_INTERVAL_SEC)


def _release_lock(fd):
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass
    os.close(fd)


def write_json_atomic(path, obj, *, timeout_ms=DEFAULT_LOCK_TIMEOUT_MS):
    """<path>.lock 배타 락 아래 temp→os.replace로 JSON을 원자 교체한다.

    성공 {"ok": True, "path": str}, 락 상한 초과 {"ok": False, "error": "lock_timeout", ...},
    쓰기 실패 {"ok": False, "error": "write_failed", ...}. 예외를 던지지 않는다.
    """
    target = pathlib.Path(path)
    if hasattr(obj, "to_dict"):
        obj = obj.to_dict()
    lock_fd = _acquire_lock(str(target) + ".lock", timeout_ms)
    if lock_fd is None:
        return {"ok": False, "error": "lock_timeout", "path": str(target), "timeout_ms": timeout_ms}
    tmp_path = target.with_name(target.name + f".tmp.{os.getpid()}")
    try:
        target.parent.mkdir(parents=True, exist_ok=True, mode=RUNTIME_DIR_MODE)
        fd = os.open(str(tmp_path), os.O_CREAT | os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW, RUNTIME_FILE_MODE)
        try:
            os.write(fd, (json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)
        os.chmod(str(tmp_path), RUNTIME_FILE_MODE)
        os.replace(str(tmp_path), str(target))
        return {"ok": True, "path": str(target)}
    except OSError as exc:
        try:
            os.unlink(str(tmp_path))
        except OSError:
            pass
        return {"ok": False, "error": "write_failed", "path": str(target), "detail": str(exc)}
    finally:
        _release_lock(lock_fd)


def read_json(path):
    """JSON 파일을 읽는다. {"ok": True, "data": ...} 또는 not_found/invalid_json/read_failed 구조화 반환."""
    target = pathlib.Path(path)
    try:
        raw = target.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"ok": False, "error": "not_found", "path": str(target)}
    except OSError as exc:
        return {"ok": False, "error": "read_failed", "path": str(target), "detail": str(exc)}
    try:
        return {"ok": True, "path": str(target), "data": json.loads(raw)}
    except ValueError as exc:
        return {"ok": False, "error": "invalid_json", "path": str(target), "detail": str(exc)}


# ─────────────────────────────────────────────────────────────────────────────
# registry meta 읽기 전용 어댑터
# ─────────────────────────────────────────────────────────────────────────────

_REGISTRY_REQUIRED_KEYS = ("allocator_root", "task_home", "task_folder", "task_path", "artifact_repo")


def read_registry_meta(hub_root, task_number):
    """<hub_root>/.opal-worktrees/.meta/task_<NNN>.json을 읽기 전용으로 해석한다.

    성공 시 allocator_root·task_home·task_folder·task_path·artifact_repo·task_ownership_version·
    attribution_state·execution_ownership·legacy를 반환한다. task_ownership_version 부재는
    legacy=True로만 표시한다. 파일 부재·손상 JSON·필수 키 누락은 예외가 아니라
    {"ok": False, "diagnostic": "invalid_registry", "detail": ...}로 반환한다.
    경로는 발급값을 읽기만 하며 추측·보정하지 않는다.
    """
    meta_path = registry_meta_path(hub_root, task_number)
    read = read_json(meta_path)
    if not read["ok"]:
        return {
            "ok": False,
            "diagnostic": "invalid_registry",
            "path": str(meta_path),
            "detail": read["error"],
        }
    data = read["data"]
    if not isinstance(data, dict):
        return {
            "ok": False,
            "diagnostic": "invalid_registry",
            "path": str(meta_path),
            "detail": "meta_not_object",
        }
    missing = [k for k in _REGISTRY_REQUIRED_KEYS if not data.get(k)]
    if missing:
        return {
            "ok": False,
            "diagnostic": "invalid_registry",
            "path": str(meta_path),
            "detail": "missing_keys",
            "missing_keys": missing,
        }
    ownership_version = data.get("task_ownership_version")
    return {
        "ok": True,
        "path": str(meta_path),
        "allocator_root": data.get("allocator_root"),
        "task_home": data.get("task_home"),
        "task_folder": data.get("task_folder"),
        "task_path": data.get("task_path"),
        "artifact_repo": data.get("artifact_repo"),
        "task_ownership_version": ownership_version,
        "attribution_state": data.get("attribution_state"),
        "execution_ownership": data.get("execution_ownership"),
        "legacy": ownership_version is None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 실행 루트 해석 — 허브 세션 / 워크트리 세션 공용
# ─────────────────────────────────────────────────────────────────────────────

TASK_OWNERSHIP_COPY_NAME = "task-ownership.json"


def task_ownership_copy_path(worktree_root):
    """<worktree_root>/.opal/task-ownership.json — worktree-tool이 내려보낸 발급값 사본."""
    return pathlib.Path(worktree_root) / ".opal" / TASK_OWNERSHIP_COPY_NAME


def resolve_roots(cwd):
    """cwd가 허브인지 워크트리인지 판정하고 allocator_root/task_path를 돌려준다.

    분기는 정확히 3개이며 그 밖의 경로는 없다.

    ① <cwd>/.opal-worktrees/.meta/ 가 있으면 허브 세션이다 — allocator_root는 cwd 자신이다.
    ② 없으면 <cwd>/.opal/task-ownership.json 사본에서 allocator_root·task_path를 **읽는다**.
    ③ 둘 다 없으면 roots_unresolved 진단만 남기고 루트를 None으로 둔다.

    [MUST] 어느 분기에서도 추론하지 않는다 — cwd 문자열 자르기·부모 디렉터리 순회
    (`.parents`)·`.opal-worktrees` 문자열 탐색(`os.walk`/`iterdir`)을 쓰지 않는다
    (harness/worktree.md §task root와 allocator root 계약). 이 금지는 test_resolve_roots의
    AST 검사가 집행한다.

    ②의 사본은 **읽기 snapshot**이다(harness/worktree.md §cone 확장 계약) — allocator_root는
    사본이 적어준 값을 그대로 돌려주며, 사본이 있다고 워크트리를 허브로 승격시키지 않는다
    (kind는 "worktree"로 남는다).
    """
    base = pathlib.Path(cwd)

    meta_dir = base / ".opal-worktrees" / ".meta"
    if meta_dir.is_dir():
        return {
            "ok": True,
            "kind": "hub",
            "source": "hub_registry",
            "path": str(meta_dir),
            "allocator_root": str(base),
            "task_path": None,
        }

    copy_path = task_ownership_copy_path(base)
    read = read_json(copy_path)
    if read["ok"] and isinstance(read["data"], dict):
        data = read["data"]
        allocator_root = data.get("allocator_root")
        if isinstance(allocator_root, str) and allocator_root:
            return {
                "ok": True,
                "kind": "worktree",
                "source": "issued_copy",
                "path": str(copy_path),
                "allocator_root": allocator_root,
                "task_path": data.get("task_path"),
                "task_home": data.get("task_home"),
                "task_folder": data.get("task_folder"),
            }

    return {
        "ok": False,
        "diagnostic": "roots_unresolved",
        "kind": None,
        "allocator_root": None,
        "task_path": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 세션 ID 해석 (D-18)
# ─────────────────────────────────────────────────────────────────────────────

def resolve_session_id(env, payload=None):
    """① env OPAL_SESSION_ID ② 플랫폼 어댑터 ③ hook 봉투 session_id 순으로 해석한다.

    플랫폼 고유 변수명은 claude_adapter가 소유하며 이 모듈에는 두지 않는다. 없으면 None.
    """
    env = env or {}
    value = env.get("OPAL_SESSION_ID")
    if isinstance(value, str) and value.strip():
        return value.strip()

    value = claude_adapter.session_id_from_env(env)
    if value:
        return value

    if isinstance(payload, dict):
        value = payload.get("session_id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
