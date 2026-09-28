"""
@header {
  "module": "ownership_core",
  "layer": "util",
  "domain": "opal-pipeline",
  "description": "ownership-tool 런타임 저장소 코어. D-5의 3개 저장소 경로 계산(session_registry_path·hub_lease_path·stop_receipt_path)과 스키마 dataclass(SessionRecord·LeaseRecord·StopReceipt), D-7의 저장소별 lock(<path>.lock, O_CREAT+O_RDWR+O_NOFOLLOW·0o600·LOCK_EX+LOCK_NB 재시도, 상한 2000ms) + temp→os.replace 원자 교체 헬퍼(write_json_atomic·read_json), .opal-worktrees/.meta/task_<NNN>.json 읽기 전용 어댑터(read_registry_meta), 세션 ID 해석 2종(일반 CLI용 resolve_session_id — env OPAL_SESSION_ID → 플랫폼 env → 봉투 순, 훅 이벤트용 hook_session_id — 봉투 session_id만 읽고 env로 대체하지 않는다), 실행 루트 해석(resolve_roots — <cwd>/.opal-worktrees/.meta/ 존재 시 허브, 부재 시 worktree-tool이 내려보낸 <cwd>/.opal/task-ownership.json 발급값 사본에서 allocator_root·task_path를 읽고, 둘 다 없으면 roots_unresolved 진단만 남긴다 — 어느 분기에서도 cwd 문자열 자르기·부모 순회·.opal-worktrees 문자열 탐색으로 추론하지 않는다), 프로젝트 루트(task_root 축) 해석 단일 진입점(resolve_project_root — D-30b의 ① 명시 오버라이드 OPAL_PROJECT_ROOT → ② 봉투 cwd부터 조상으로 올라가며 .opal/MEMORY.json 또는 .opal/AGENT.md를 파일로 가진 첫 디렉토리 채택 → ③ None 3단계, 어댑터 5종이 공유하는 유일한 루트 채택 지점이며 플랫폼 환경변수를 읽지 않는다)을 제공한다. 실패는 예외가 아니라 ok/error 구조화 dict 또는 None으로 반환하며 플랫폼 고유 환경변수는 Claude/Codex adapter가 소유한다. 일반 신원 우선순위는 OPAL→Claude→Codex→payload이며 available_session_sources는 값 없이 source 이름만 보고하고 session_launch_env는 adapter 선언 부모 신원을 제거한다.",
  "exports": [
    "DEFAULT_LOCK_TIMEOUT_MS",
    "RUNTIME_DIR_MODE",
    "RUNTIME_FILE_MODE",
    "session_registry_path",
    "hub_lease_path",
    "stop_receipt_path",
    "registry_meta_path",
    "SessionRecord",
    "LeaseRecord",
    "StopReceipt",
    "write_json_atomic",
    "read_json",
    "read_registry_meta",
    "resolve_session_id",
    "hook_session_id",
    "task_ownership_copy_path",
    "resolve_roots",
    "resolve_project_root",
    "available_session_sources",
    "session_launch_env"
  ],
  "depends": [
    "claude_adapter",
    "codex_adapter"
  ]
}
"""
from __future__ import annotations

import errno
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
    pending_decisions: list = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return _from_dict(cls, data)


# ─────────────────────────────────────────────────────────────────────────────
# D-7 lock + atomic replace
# ─────────────────────────────────────────────────────────────────────────────

_LOCK_PERMISSION_ERRNOS = frozenset((errno.EACCES, errno.EPERM, errno.EROFS))


class _LockPermissionDenied(OSError):
    """A lock path cannot be opened or locked because this process cannot write it."""


def _is_lock_permission_error(exc):
    return isinstance(exc, OSError) and exc.errno in _LOCK_PERMISSION_ERRNOS

def _acquire_lock(lock_path, timeout_ms):
    """LOCK_EX|LOCK_NB 재시도 루프(run_log_core._acquire_lock 패턴). 성공 시 fd, 상한 초과 시 None."""
    lock_path = pathlib.Path(lock_path)
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True, mode=RUNTIME_DIR_MODE)
    except OSError as exc:
        if _is_lock_permission_error(exc):
            raise _LockPermissionDenied(exc.errno, str(exc), str(lock_path)) from exc
        raise
    deadline = time.monotonic() + (timeout_ms / 1000.0)
    while True:
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, RUNTIME_FILE_MODE)
        except OSError as exc:
            if _is_lock_permission_error(exc):
                raise _LockPermissionDenied(exc.errno, str(exc), str(lock_path)) from exc
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
        except OSError as exc:
            os.close(fd)
            if _is_lock_permission_error(exc):
                raise _LockPermissionDenied(exc.errno, str(exc), str(lock_path)) from exc
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
    try:
        lock_fd = _acquire_lock(str(target) + ".lock", timeout_ms)
    except _LockPermissionDenied as exc:
        return {"ok": False, "error": "registry_write_denied", "path": str(target),
                "detail": str(exc)}
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
    (harness/worktree.md §task root와 allocator root 계약). 이 금지는
    tests/test_root_resolution.py의 test_s9_resolve_roots_three_branches_preserved가
    수행하는 AST 검사가 집행한다.

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

    플랫폼 고유 변수명은 claude_adapter·codex_adapter가 소유하며 이 모듈에는 두지 않는다. 없으면 None.
    """
    env = env or {}
    value = env.get("OPAL_SESSION_ID")
    if isinstance(value, str) and value.strip():
        return value.strip()

    value = claude_adapter.session_id_from_env(env)
    if value:
        return value

    from . import codex_adapter
    value = codex_adapter.session_id_from_env(env)
    if value:
        return value

    if isinstance(payload, dict):
        value = payload.get("session_id")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def available_session_sources(env):
    """Return available source names only; never expose identity values in diagnostics."""
    from . import codex_adapter
    keys = ("OPAL_SESSION_ID", claude_adapter.SESSION_ID_ENV, codex_adapter.SESSION_ID_ENV)
    return [key for key in keys if isinstance(env.get(key), str) and env[key].strip()]


def session_launch_env(env):
    """Isolate a new runtime from its parent's ownership and platform identities."""
    from . import codex_adapter
    cleaned = dict(env)
    for key in ("OPAL_SESSION_ID",) + claude_adapter.INHERITED_IDENTITY_KEYS + codex_adapter.INHERITED_IDENTITY_KEYS:
        cleaned.pop(key, None)
    return cleaned


def hook_session_id(payload):
    """훅 이벤트의 세션 ID — 봉투 ``session_id``만 읽는다. 없으면 None.

    훅은 이벤트를 일으킨 세션에만 작용해야 한다. 부모 세션의 env(``OPAL_SESSION_ID``·플랫폼
    변수)를 상속한 자식 프로세스의 이벤트를 부모 신원으로 판정하지 않도록 env를 받지 않는다.
    누락·공백·비문자는 None이며 호출자는 진단만 남기고 아무것도 쓰지 않는다.
    """
    if not isinstance(payload, dict):
        return None
    value = payload.get("session_id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 프로젝트 루트 해석 (D-30)
# ─────────────────────────────────────────────────────────────────────────────

# D-30c — 조상 탐색의 앵커는 **마커 파일**이다. `.opal/` 디렉토리 존재는 앵커가 아니다.
# 이번 결함이 하위에 남기는 오염은 `<하위>/.opal/run/.runtime/…`뿐이고 마커 파일을 만들지
# 않으므로, 파일 앵커만 인정하면 오염된 하위가 루트로 승격되는 자기증식이 차단된다.
_PROJECT_ROOT_MARKERS = (
    ("MEMORY.json",),
    ("AGENT.md",),
)


def resolve_project_root(payload, env=None):
    """hook 봉투와 env에서 프로젝트 루트를 해석하는 **단일 진입점**이다(D-30b).

    이 루트는 `allocator_root`가 아니라 **`task_root`** 축이다(D-30a) — 소비자가
    `session_registry_path`·`stop_receipt_path`·`lease.resolve_ttl_sec`로 전부 `.opal`
    설정·state다. 계약 원문은 `opal/core/references/harness/worktree.md`
    §task root와 allocator root 계약의 `task_root` 행이며, 그 정의가 "가장 가까운
    `.git`·`.opal` 작업본"이다.

    체인은 정확히 3단계이며 그 밖의 경로는 없다.

    ① env["OPAL_PROJECT_ROOT"] — 문자열이고 실제 디렉토리면 채택한다. 저장소에 이 변수를
       쓰는 주체는 없고 테스트·수동 **명시 오버라이드 전용**이다(D-30e).
    ② 봉투 cwd에서 시작하는 **조상 탐색** — cwd 자신부터 위로 올라가며
       `.opal/MEMORY.json` 또는 `.opal/AGENT.md`를 **파일로** 가진 첫 디렉토리를 채택한다
       (D-30c). 파일시스템 루트에서 멈춘다. "가장 가까운 조상" 규칙이므로 워크트리 안에서는
       허브가 아니라 워크트리 `.opal`이 먼저 잡힌다.
    ③ 그 외 None — 호출자는 None을 "루트 미해석"으로 보고 파일 I/O 이전에 종료한다(D-25).

    선례는 `state_tool.task_root()`이며 같은 `for cand in (p, *p.parents)` 패턴이다.
    다만 `task_root()`와 달리 **`.resolve()`를 걸지 않는다** — macOS에서 `/var` ↔
    `/private/var` 심볼릭 정규화가 일어나 봉투가 준 경로와 반환값의 문자열 동등이
    깨지고 tests/test_root_resolution.py의 S-9 ⑶이 실패한다. 이관 판정은
    `lease._root_accepts`가 양쪽에 realpath를 걸므로 영향받지 않는다(D-28).
    `resolve_roots`(allocator_root 축)는 호출하지 않는다 — 두 축은 독립이며
    `resolve_roots`의 시그니처·3분기·반환 키는 이 함수와 무관하게 무변경이다.

    [MUST] 예외를 던지지 않는다. 어떤 실패도 None으로 흡수한다(C-1 fail-safe).
    [MUST] 플랫폼 고유 환경변수를 읽지 않는다 — 조상 탐색이 전 플랫폼(claude·codex·
    cursor·gemini)에서 동일하게 성립하므로 루트 해석은 플랫폼 독립이다(D-30d).
    """
    env = env or {}

    value = env.get("OPAL_PROJECT_ROOT")
    if isinstance(value, str) and value.strip() and os.path.isdir(value.strip()):
        return value.strip()

    if isinstance(payload, dict):
        cwd = payload.get("cwd")
        if isinstance(cwd, str) and cwd.strip():
            try:
                start = pathlib.Path(cwd.strip())
                for cand in (start, *start.parents):
                    for marker in _PROJECT_ROOT_MARKERS:
                        if cand.joinpath(".opal", *marker).is_file():
                            return str(cand)
            except Exception:  # noqa: BLE001 — 조상 탐색 실패는 미해석(None)으로 흡수한다.
                return None
    return None
