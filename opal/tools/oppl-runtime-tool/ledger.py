"""
@header {
  "module": "ledger",
  "task": "131",
  "layer": "util",
  "domain": "opal-tools",
  "description": "oppl-runtime-tool의 설정 로더(D6)·운영 ledger 저장소(D4)·실패 지문(D9) 구현. 전역 $OPAL_HOME/setting.json을 base로 프로젝트 .opal/setting.local.json의 oppl.runtime 최상위 키를 통째로 교체하는 1단계 키 오버라이드(딥 머지 금지)를 수행하고, 필수 키·타입·유한 양수·등록 phase 검증에 실패하면 조용한 기본값 강등 없이 단일 코드 config_invalid로 거부한다. .oppl-run/runtime.json은 3-SSOT(backlog.json·state.json·test-scenario.json)와 분리된 런타임 가드 축이며 집계값만 보유한다 — attempt별 PID·PGID·heartbeat·terminal result 원문을 저장하지 않고 attempt_id와 attempt record 경로만 외래 참조로 갖는다. 모든 갱신은 fcntl 배타 락 안에서 revision 증가 → temp write → fsync → atomic replace로 직렬화한다(backlog_tool.py 선례). 동일 컨텍스트 resume 상한은 설정 키가 아니라 harness/guards.md §자동 루핑 제약의 고정값을 내부 상수로 쓴다.",
  "exports": [
    "ConfigError", "LedgerStore", "load_config", "find_project_root",
    "failure_fingerprint", "phase_record", "new_ledger", "reservation_token",
    "REGISTERED_PHASES", "REQUIRED_CONFIG_KEYS", "RESUME_LIMIT",
    "PHASE_STATUSES", "FAILURE_STATUSES", "T4B_BRANCHES"
  ]
}
"""

# 표준 라이브러리만 사용한다 (신규 의존성 도입 금지 — PLAN 131 §실행 capability)
import contextlib
import fcntl
import hashlib
import json
import math
import os
import pathlib
import secrets
import tempfile
from datetime import datetime, timedelta, timezone

# ─────────────────────────────────────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────────────────────────────────────

# PLAN §W-3 — 등록 phase 집합
REGISTERED_PHASES = ("t1", "t2", "g", "t3", "t4a", "t4b")

# 제안서 §6.1 — 필수 설정 키 9종
REQUIRED_CONFIG_KEYS = (
    "max_design_rounds",
    "max_project_dispatches",
    "max_task_attempts",
    "max_identical_failures",
    "max_wall_time_sec",
    "heartbeat_timeout_sec",
    "hard_timeout_sec_by_phase",
    "max_hard_timeout_sec",
    "terminate_grace_sec",
)

# 제안서 §6.1 — 선택 키이나 존재하면 유한 양수
OPTIONAL_CONFIG_KEYS = ("max_cost_usd",)

# 동일 컨텍스트 resume 상한. 설정 키가 아니다 —
# 수치의 SSOT는 opal/core/references/harness/guards.md §자동 루핑 제약이며
# 여기서는 그 고정값을 내부 상수로만 쓴다(config 출력에 노출하지 않는다).
RESUME_LIMIT = 1

# 제안서 §5 — 상태 7종
PHASE_STATUSES = ("pending", "running", "done", "failed", "error", "blocked", "timed_out")

# 실패 지문을 누적하는 terminal 상태
FAILURE_STATUSES = ("failed", "error", "timed_out")

# D9 / TASK C-12 / AC-14 — provider 장애는 무진전 신호가 아니므로
# no_progress 카운터를 건드리지 않는다.
NO_PROGRESS_EXEMPT_EXIT_CLASSES = ("api_error",)

# 제안서 §6.4 — T4b 3분기
T4B_BRANCHES = ("impl_defect", "contract_defect", "policy_conflict")

# budget_snapshot은 예산·상한 축만 담는다. heartbeat/timeout 계열은 attempt wrapper
# 소유 축이므로 ledger에 복제하지 않는다(D4).
BUDGET_SNAPSHOT_KEYS = (
    "max_design_rounds",
    "max_project_dispatches",
    "max_task_attempts",
    "max_identical_failures",
    "max_wall_time_sec",
    "max_cost_usd",
)

SCHEMA_VERSION = "1.0"
RUN_DIR_NAME = ".oppl-run"
LEDGER_NAME = "runtime.json"
LOCK_NAME = "runtime.lock"

RESERVATION_PREFIX = "resv-"


class ConfigError(Exception):
    """설정 로드·검증 실패. 원인 종류와 무관하게 단일 코드 config_invalid로 거부한다."""


# ─────────────────────────────────────────────────────────────────────────────
# 시각
# ─────────────────────────────────────────────────────────────────────────────

def utc_now():
    return datetime.now(timezone.utc)


def to_iso(dt):
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def from_iso(text):
    return datetime.fromisoformat(text)


# ─────────────────────────────────────────────────────────────────────────────
# 설정 로더 (D6 — 1단계 키 오버라이드, 딥 머지 금지)
# ─────────────────────────────────────────────────────────────────────────────

def _reject_constant(name):
    # Infinity / -Infinity / NaN 은 JSON 확장 토큰이다. 유한 양수 계약 위반이므로
    # 파싱 단계에서 거부한다.
    raise ValueError("non-finite JSON constant: %s" % name)


def find_project_root(task_path):
    """task-path에서 위로 올라가며 `.opal/`을 가진 첫 조상을 project root로 본다."""
    current = pathlib.Path(task_path).resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / ".opal").is_dir():
            return candidate
    raise ConfigError("project root (.opal/) not found above %s" % task_path)


def opal_home():
    # state_tool.py:403 선례를 그대로 따른다.
    return pathlib.Path(os.environ.get("OPAL_HOME") or os.path.expanduser("~/.opal"))


def _read_runtime_block(path):
    """설정 파일 1건에서 oppl.runtime 블록을 꺼낸다. 부재 시 None."""
    if not path.is_file():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    except (ValueError, OSError) as exc:
        raise ConfigError("unparsable setting file %s: %s" % (path, exc))
    if not isinstance(doc, dict):
        raise ConfigError("setting file %s is not an object" % path)
    oppl = doc.get("oppl")
    if oppl is None:
        return None
    if not isinstance(oppl, dict):
        raise ConfigError("oppl block in %s is not an object" % path)
    runtime = oppl.get("runtime")
    if runtime is None:
        return None
    if not isinstance(runtime, dict):
        raise ConfigError("oppl.runtime in %s is not an object" % path)
    return runtime


def _positive_finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if not math.isfinite(float(value)):
        return False
    return float(value) > 0


def _validate(config):
    for key in REQUIRED_CONFIG_KEYS:
        if key not in config:
            raise ConfigError("required key missing: %s" % key)

    for key in REQUIRED_CONFIG_KEYS:
        if key == "hard_timeout_sec_by_phase":
            continue
        if not _positive_finite(config[key]):
            raise ConfigError("%s must be a finite positive number" % key)

    phase_map = config["hard_timeout_sec_by_phase"]
    if not isinstance(phase_map, dict):
        raise ConfigError("hard_timeout_sec_by_phase must be an object")
    for phase in REGISTERED_PHASES:
        if phase not in phase_map:
            # 딥 머지를 하지 않으므로 부분 map은 여기서 결손으로 드러난다(D6).
            raise ConfigError("hard_timeout_sec_by_phase missing registered phase: %s" % phase)
    for phase, value in phase_map.items():
        if not _positive_finite(value):
            raise ConfigError("hard_timeout_sec_by_phase[%s] must be a finite positive number" % phase)

    for key in OPTIONAL_CONFIG_KEYS:
        if key in config and not _positive_finite(config[key]):
            raise ConfigError("%s must be a finite positive number when present" % key)

    return config


def load_config(task_path):
    """전역 setting.json을 base로 로컬 setting.local.json의 최상위 키를 통째로 교체한다.

    딥 머지를 하지 않는다 — `hard_timeout_sec_by_phase`도 dict 통째 교체다(D6).
    두 파일 모두 부재하거나 검증에 실패하면 ConfigError를 올리며,
    호출자는 이를 단일 코드 config_invalid로 변환한다(조용한 기본값 강등 금지).
    """
    project_root = find_project_root(task_path)
    global_path = opal_home() / "setting.json"
    local_path = project_root / ".opal" / "setting.local.json"

    if not global_path.is_file() and not local_path.is_file():
        raise ConfigError("no setting file found (%s, %s)" % (global_path, local_path))

    merged = {}
    for path in (global_path, local_path):
        block = _read_runtime_block(path)
        if block is None:
            continue
        for key, value in block.items():
            merged[key] = value  # 1단계 키 오버라이드 — 하위 구조는 통째 교체

    return _validate(merged)


# ─────────────────────────────────────────────────────────────────────────────
# 실패 지문 (제안서 §6.3 / D9)
# ─────────────────────────────────────────────────────────────────────────────

def failure_fingerprint(task_id, phase, verifier_id, command_id, exit_class,
                        failing_scenario_ids, normalized_error_code, contract_revision):
    """정규화 payload의 SHA-256.

    자유 텍스트·timestamp·임시 경로·PID·토큰 수는 payload에 들어가지 않는다.
    exit_class는 1급 필드이므로 api_error 종료는 impl_failure와 다른 지문이 된다(D9).
    """
    payload = {
        "task_id": task_id,
        "phase": phase,
        "verifier_id": verifier_id,
        "command_id": command_id,
        "exit_class": exit_class,
        "failing_scenario_ids": sorted(failing_scenario_ids or []),
        "normalized_error_code": normalized_error_code,
        "contract_revision": contract_revision,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalize_error_code(value):
    if value is None:
        return None
    return str(value).strip().lower() or None


# ─────────────────────────────────────────────────────────────────────────────
# ledger 문서 (D4 — 집계값만)
# ─────────────────────────────────────────────────────────────────────────────

def reservation_token():
    """admit이 예약하는 active attempt 토큰. attempt-start가 실제 attempt-id로 바꾼다."""
    return RESERVATION_PREFIX + secrets.token_hex(6)


def is_reservation(value):
    return isinstance(value, str) and value.startswith(RESERVATION_PREFIX)


def budget_snapshot(config):
    return {k: config[k] for k in BUDGET_SNAPSHOT_KEYS if k in config}


def new_ledger(run_id, config):
    started = utc_now()
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,                 # state-tool이 발급한 값의 외래 참조 (D8/C-5)
        "revision": 0,
        "status": "running",
        "started_at": to_iso(started),
        "deadline_at": to_iso(started + timedelta(seconds=float(config["max_wall_time_sec"]))),
        "design_round": 0,
        "project_dispatch_count": 0,
        "cost_used": 0.0,
        "wall_time_used": 0.0,
        "budget_snapshot": budget_snapshot(config),
        "counters": {},
    }


def phase_record(ledger, task_id, phase, create=False):
    """task·phase 단위 집계 레코드를 반환한다. create=False면 부재 시 None."""
    counters = ledger.get("counters")
    if counters is None:
        if not create:
            return None
        counters = ledger["counters"] = {}
    task_node = counters.get(task_id)
    if task_node is None:
        if not create:
            return None
        task_node = counters[task_id] = {"phases": {}}
    phases = task_node.setdefault("phases", {})
    record = phases.get(phase)
    if record is None:
        if not create:
            return None
        record = phases[phase] = {
            "attempt_count": 0,
            "resume_count": 0,
            "active_attempt_id": None,
            "status": "pending",
            "record_path": None,
            "last_failure_fingerprint": None,
            "identical_failure_count": 0,
        }
    return record


def elapsed_seconds(ledger, now=None):
    now = now or utc_now()
    return max(0.0, (now - from_iso(ledger["started_at"])).total_seconds())


# ─────────────────────────────────────────────────────────────────────────────
# 저장소 — lock → revision 확인 → temp write → fsync → atomic replace
# ─────────────────────────────────────────────────────────────────────────────

class LedgerStore:

    def __init__(self, task_path):
        self.task_path = pathlib.Path(task_path)
        self.run_dir = self.task_path / RUN_DIR_NAME
        self.path = self.run_dir / LEDGER_NAME
        self.lock_path = self.run_dir / LOCK_NAME

    def exists(self):
        return self.path.is_file()

    def ensure_run_dir(self):
        self.run_dir.mkdir(parents=True, exist_ok=True)

    @contextlib.contextmanager
    def locked(self):
        """fcntl 배타 락 — 다중 프로세스의 read-modify-write를 직렬화한다.

        backlog_tool.py의 배타 락 선례를 따른다(그 파일은 읽기만 하고 수정하지 않았다).
        """
        self.ensure_run_dir()
        handle = open(self.lock_path, "a+")
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            finally:
                handle.close()

    def read(self):
        return json.loads(self.path.read_text(encoding="utf-8"))

    def write(self, ledger, expected_revision=None):
        """revision 확인 후 원자적으로 교체한다. 반드시 locked() 안에서 호출한다."""
        if expected_revision is not None and self.exists():
            current = self.read().get("revision")
            if current != expected_revision:
                raise ConfigError("ledger revision conflict: %r != %r" % (current, expected_revision))
        ledger["revision"] = int(ledger.get("revision", 0)) + 1
        ledger["wall_time_used"] = round(elapsed_seconds(ledger), 3)

        self.ensure_run_dir()
        fd, tmp_name = tempfile.mkstemp(dir=str(self.run_dir), prefix=".runtime-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(ledger, handle, ensure_ascii=False, separators=(",", ":"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, str(self.path))
        except BaseException:
            with contextlib.suppress(OSError):
                os.unlink(tmp_name)
            raise
        return ledger
