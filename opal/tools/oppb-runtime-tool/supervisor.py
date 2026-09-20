"""
@header {
  "module": "supervisor",
  "task": "132",
  "layer": "util",
  "domain": "oppb-runtime",
  "description": "OPPB Runtime Supervisor — 동시성 상한 집행·Verifier 우선 배정·비정상 종료 복구를 소유한다. `max_active_runners`·`max_active_executors`·`max_total_agent_processes` 3종 상한을 집행하고, 선언된 Executor가 pool 상한보다 많으면 같은 runner 세대 안에서 빈 slot만큼 배치하며, 상한이 포화된 뒤 반환되는 첫 slot은 신규 Runner보다 준비된 candidate의 Verifier에 우선 배정한다(제안서 §9.3, 수용기준 10). run_command가 null인 capability는 구현 생략으로 처리하지 않고 `opal-agent` Runner로 기동하며, effective setting의 `models.platform` 또는 auto 세션 표식으로 provider를 명시해 `opal-agent` 기본 Claude로 잘못 강등되지 않게 한다. 비정상 종료·재시작 복구는 판정 로직을 재구현하지 않는다 — `opal-agent`의 `reconcile-attempts` CLI를 호출해 받은 reattach/harvest/orphan 3분류와 `reclaim_required`를 소비만 하며, attempt record를 직접 파싱하거나 PID 생존·PGID·경과시간 identity 판정을 자체 구현하지 않는다(PLAN W-8 / W-38 B-1). 복구 후에는 사람 개입 없이 tick을 자동 재개한다 — PM tick·수동 재촉·강제 resume 경로를 만들지 않는다(제안서 §4.1, 수용기준 10). `workgraph.json`·`acceptance.json`·`execution-packet.json`은 쓰지 않고 `controller.py`의 revision lock API로만 전진시킨다(§4.5 writer 소유권). run 1개당 Supervisor 1개는 `supervisor.lock` flock으로 강제한다(§4.6). 표준 라이브러리 전용.",
  "exports": [
    "SUPERVISOR_ERROR_CODES", "SupervisorError", "Supervisor",
    "start_supervisor", "read_status", "main"
  ],
  "depends": [
    "opal/tools/oppb-runtime-tool/controller.py",
    "opal/tools/opal-agent/run.sh",
    "opal/core/references/harness/tool-output-contract.md"
  ]
}
"""

# 표준 라이브러리만 사용한다 (신규 의존성 도입 금지)
from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import time
import uuid

import controller
import lease

SCHEMA_VERSION = "1.0"

# run root 안의 Supervisor 소유 경로 — workgraph·acceptance·packet은 Controller 소유다.
LOCK_NAME = "supervisor.lock"
SUPERVISOR_STATE_NAME = "supervisor.json"
EVENTS_NAME = "events.jsonl"
DAEMON_LOG_NAME = "supervisor.log"

# attempt 디렉토리 안의 파일 이름. `attempt.attempt.json`은 opal-agent의 sink stem
# 규약(`<stem>.attempt.json`)을 그대로 따른다 — `reconcile-attempts`가 이것을 읽는다.
ATTEMPT_RECORD_STEM = "attempt"
ATTEMPT_RESULT_NAME = "result.json"
ATTEMPT_SPEC_NAME = "attempt-spec.json"
ATTEMPT_RUNNER_LOG_NAME = "attempt-runner.log"
CAPABILITY_STDOUT_NAME = "capability.out"
CAPABILITY_STDERR_NAME = "capability.err"
AGENT_RUN_DIRNAME = "agent"

ROLE_RUNNER = "runner"
ROLE_EXECUTOR = "executor"
ROLE_VERIFIER = "verifier"

# 미니 태스크 상태 어휘는 controller.TASK_STATES가 SSOT다.
STATE_PENDING = "pending"
STATE_RUNNING = "running"
STATE_CANDIDATE_READY = "candidate_ready"
STATE_VERIFYING = "verifying"
STATE_ACCEPTED = "accepted"
STATE_FAILED = "failed"
TERMINAL_TASK_STATES = (STATE_ACCEPTED, STATE_FAILED, "blocked")

# §9.3 동시성 예산. workgraph의 budget.limits가 선언하면 그 값이 우선한다.
DEFAULT_LIMITS = {
    "max_active_runners": 2,
    "max_active_executors": 2,
    "max_total_agent_processes": 4,
}
DEFAULT_MAX_ATTEMPTS = 2

TICK_INTERVAL_SEC = 0.1
# 결과 파일이 아직 running으로 보일 때 `reconcile-attempts`로 재확인하는 주기.
RECONCILE_INTERVAL_SEC = 2.0
HANDSHAKE_TIMEOUT_SEC = 60.0
PGID_REAP_TIMEOUT_SEC = 10.0
LAUNCH_PID_WAIT_SEC = 15.0
# Capability 단위는 구현과 프로젝트 전체 회귀를 한 attempt 안에서 수행한다. opal-agent의
# 기본 300초는 실제 T01/T03에서 정상 작업 중 hard timeout을 냈으므로 OPPB는 15분을 명시한다.
CAPABILITY_AGENT_TIMEOUT_SEC = 900

SUPERVISOR_ERROR_CODES = {
    "run_lock_held": "이 run에는 이미 살아 있는 Supervisor가 있습니다 — run lock을 얻지 못했습니다.",
    "supervisor_spawn_failed": "Supervisor 프로세스를 기동하지 못했습니다.",
    "supervisor_handshake_timeout": "Supervisor 기동 확인(handshake)이 시간 안에 오지 않았습니다.",
    "reconcile_failed": "opal-agent reconcile-attempts 호출에 실패했습니다.",
}


class SupervisorError(Exception):
    """폐쇄 집합 `SUPERVISOR_ERROR_CODES`의 코드 하나로 실패를 표현한다."""

    def __init__(self, code, message="", **extra):
        super().__init__(message or code)
        self.code = code
        self.message = message
        self.exit_code = controller.EXIT_ERROR
        self.extra = extra


def _atomic_write_json(path, payload):
    """대상 디렉토리 임시 파일 → fsync → `os.replace`.

    `oppl-runtime-tool/ledger.py:336-377`의 **형태만** 복제한다 — 그 도구를
    import하지 않으며 공용 추출도 하지 않는다(W-38 B-3).
    """
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".oppb-sv-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, str(path))
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def _read_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def limits_of(document):
    limits = dict(DEFAULT_LIMITS)
    declared = (document.get("budget") or {}).get("limits") or {}
    for key in DEFAULT_LIMITS:
        if isinstance(declared.get(key), int) and not isinstance(declared.get(key), bool):
            limits[key] = declared[key]
    raw_attempts = declared.get("max_attempts_per_task")
    limits["max_attempts_per_task"] = (
        raw_attempts if isinstance(raw_attempts, int) and raw_attempts > 0
        else DEFAULT_MAX_ATTEMPTS
    )
    return limits


# ─────────────────────────────────────────────────────────────────────────────
# events.jsonl — Supervisor 단일 writer, 한 줄당 JSON object 1개
# ─────────────────────────────────────────────────────────────────────────────


def append_event(run_root, event, **fields):
    path = pathlib.Path(run_root) / EVENTS_NAME
    payload = {"ts": time.time(), "event": event}
    payload.update(fields)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


# ─────────────────────────────────────────────────────────────────────────────
# attempt 디렉토리
# ─────────────────────────────────────────────────────────────────────────────


def iter_attempt_dirs(run_root):
    root = pathlib.Path(run_root) / controller.ATTEMPTS_DIRNAME
    if not root.is_dir():
        return []
    return sorted(p for p in root.glob("*/*") if p.is_dir())


def read_attempt_result(directory):
    path = pathlib.Path(directory) / ATTEMPT_RESULT_NAME
    if not path.is_file():
        return None
    try:
        return _read_json(path)
    except (OSError, json.JSONDecodeError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# opal-agent 경유 — 재부착·수확·고아 3분류는 여기서 **소비만** 한다.
# ─────────────────────────────────────────────────────────────────────────────


def opal_agent_entrypoint():
    """`opal-agent`의 공개 CLI. run.sh가 있으면 그것을 쓴다."""
    agent_dir = pathlib.Path(__file__).resolve().parents[1] / "opal-agent"
    run_sh = agent_dir / "run.sh"
    if run_sh.is_file():
        return ["bash", str(run_sh)]
    return [sys.executable, str(agent_dir / "opal_agent.py")]


def agent_provider(project_root):
    """effective `models.platform`을 provider로 해석한다.

    `auto`는 Supervisor를 기동한 현재 하네스의 환경 표식을 사용한다. 아무 표식도
    없는 기존 호출은 opal-agent의 종전 기본값인 Claude를 유지한다.
    """
    platform = "auto"
    opal_home = pathlib.Path(os.environ.get("OPAL_HOME") or pathlib.Path.home() / ".opal")
    paths = [opal_home / "setting.json"]
    if project_root:
        paths.append(pathlib.Path(project_root) / ".opal" / "setting.local.json")
    for path in paths:
        try:
            document = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        declared = (document.get("models") or {}).get("platform")
        if isinstance(declared, str) and declared:
            platform = declared

    if platform != "auto":
        return "codex" if platform == "openai" else platform
    if os.environ.get("CODEX_SESSION_ID") or os.environ.get("CODEX_THREAD_ID"):
        return "codex"
    if os.environ.get("CLAUDE_CODE_SESSION_ID") or os.environ.get("CLAUDECODE"):
        return "claude"
    if os.environ.get("GEMINI_CLI"):
        return "gemini"
    if os.environ.get("CURSOR_AGENT"):
        return "cursor"
    return "claude"


def reconcile_attempt_dir(directory):
    """`opal-agent reconcile-attempts <dir>` 응답을 그대로 돌려준다.

    reattach/harvest/orphan 판정과 `reclaim_required`는 전적으로 `opal-agent`가
    소유한다. 이 함수는 호출하고 응답을 읽을 뿐, attempt record를 직접 파싱하거나
    PID·PGID·경과시간으로 identity를 판정하지 않는다(W-38 B-1).
    """
    cmd = [*opal_agent_entrypoint(), "reconcile-attempts", str(directory)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise SupervisorError("reconcile_failed", "%s: %s" % (" ".join(cmd), exc)) from exc
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SupervisorError(
            "reconcile_failed",
            "stdout이 JSON이 아님(exit=%s): %r / %s" % (proc.returncode, proc.stdout, exc),
        ) from exc
    if not report.get("ok"):
        raise SupervisorError("reconcile_failed", json.dumps(report, ensure_ascii=False))
    return report


def reclaim_process_group(pgid):
    """`reclaim_required`로 지시된 잔여 process group을 회수한다.

    회수 **여부의 판정**은 `opal-agent`가 내리고 여기서는 집행만 한다.
    """
    if not isinstance(pgid, int) or pgid <= 0:
        return False
    with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
        os.killpg(pgid, signal.SIGKILL)
    deadline = time.monotonic() + PGID_REAP_TIMEOUT_SEC
    while time.monotonic() < deadline:
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return True
        except (PermissionError, OSError):
            return False
        time.sleep(0.05)
    return False


# ═════════════════════════════════════════════════════════════════════════════
# attempt 실행기 (`__attempt__` 모드)
#
# Supervisor와 분리된 프로세스 세션에서 capability 1건을 실행하고, 개시·종료 시점에
# opal-agent 규약의 attempt record와 OPPB attempt result를 원자 기록한다. Supervisor가
# 비정상 종료해도 이 실행기는 살아남으므로, 재기동한 Supervisor가 `reconcile-attempts`로
# `reattach`(살아 있음) 또는 `harvest`(결과 확정)를 실제로 관측할 수 있다.
# ═════════════════════════════════════════════════════════════════════════════


def _record_skeleton(spec, pid, pgid, started_at):
    """opal-agent `_attempt_start_record()`와 같은 필드 집합을 만든다.

    `classify_attempt()`가 읽는 필드(pid·pgid·started_at·status·terminal·exit_code·
    heartbeat.expired·unterminated_children·pgid_reclaimed·outputs)를 채운다.
    판정은 하지 않는다 — 판정은 `reconcile-attempts`가 한다.
    """
    return {
        "phase": spec["task_id"],
        "attempt": spec["attempt_id"],
        "mode": "sync",
        "provider": spec.get("provider") or "command",
        "status": "running",
        "exit_class": None,
        "pid": pid,
        "pgid": pgid,
        "pgid_reclaimed": False,
        "exit_code": None,
        "timeout_reason": None,
        "started_at": started_at,
        "ended_at": None,
        "duration_ms": None,
        "fingerprint": {"role": spec["role"], "command": spec["command"]},
        "heartbeat": {"timeout_sec": None, "count": 0, "last_at": None, "expired": False},
        "terminal": None,
        "cost_used": None,
        "unterminated_children": [],
        "origin": "oppb-supervisor",
    }


def _result_payload(spec, status, pid, exit_code, started_at, ended_at):
    return {
        "schema_version": SCHEMA_VERSION,
        "attempt_id": spec["attempt_id"],
        "task_id": spec["task_id"],
        "role": spec["role"],
        "executor_id": spec.get("executor_id"),
        "status": status,
        "pid": pid,
        "exit_code": exit_code,
        "started_at": started_at,
        "ended_at": ended_at,
        "command": spec["command"],
    }


def run_attempt(spec_path):
    """`__attempt__` 모드 본체. 이 프로세스는 자기 세션의 리더다."""
    spec = _read_json(spec_path)
    directory = pathlib.Path(spec["attempt_dir"])
    record_path = directory / ("%s.attempt.json" % ATTEMPT_RECORD_STEM)

    out = open(directory / CAPABILITY_STDOUT_NAME, "wb")
    errf = open(directory / CAPABILITY_STDERR_NAME, "wb")
    started_at = time.time()
    started_mono = time.monotonic()
    try:
        proc = subprocess.Popen(
            spec["command"],
            cwd=spec.get("cwd") or None,
            stdout=out,
            stderr=errf,
            stdin=subprocess.DEVNULL,
            # capability에 자기 process group을 준다 — 회수 단위가 명확해지고,
            # group 소멸이 곧 capability 종료를 뜻하게 된다.
            start_new_session=True,
        )
    except OSError as exc:
        out.close()
        errf.close()
        failure = _record_skeleton(spec, -1, -1, started_at)
        failure.update(
            {
                "status": "failed",
                "exit_class": "spawn_error",
                "exit_code": 127,
                "ended_at": time.time(),
                "duration_ms": 0,
                "pgid_reclaimed": True,
                "terminal": "spawn_error",
                "outputs": {"err": str(directory / CAPABILITY_STDERR_NAME)},
            }
        )
        _atomic_write_json(record_path, failure)
        _atomic_write_json(
            directory / ATTEMPT_RESULT_NAME,
            _result_payload(spec, "failed", -1, 127, started_at, time.time()),
        )
        raise SystemExit("capability spawn 실패: %s" % exc)

    try:
        pgid = os.getpgid(proc.pid)
    except OSError:
        pgid = proc.pid

    _atomic_write_json(record_path, _record_skeleton(spec, proc.pid, pgid, started_at))
    _atomic_write_json(
        directory / ATTEMPT_RESULT_NAME,
        _result_payload(spec, "running", proc.pid, None, started_at, None),
    )

    exit_code = proc.wait()
    out.close()
    errf.close()

    # capability process group을 회수한 뒤에만 종료를 확정한다 — 남은 자식이 고아로
    # 남지 않게 하고, 뒤이은 판정이 `pgid_residue`로 흔들리지 않게 한다.
    reclaimed = reclaim_process_group(pgid)
    ended_at = time.time()
    status = "succeeded" if exit_code == 0 else "failed"
    record = _record_skeleton(spec, proc.pid, pgid, started_at)
    record.update(
        {
            "status": status,
            "exit_class": "ok" if exit_code == 0 else "nonzero_exit",
            "exit_code": exit_code,
            "ended_at": ended_at,
            "duration_ms": int((time.monotonic() - started_mono) * 1000),
            "pgid_reclaimed": reclaimed,
            "terminal": status,
            "outputs": {
                "out": str(directory / CAPABILITY_STDOUT_NAME),
                "err": str(directory / CAPABILITY_STDERR_NAME),
            },
        }
    )
    _atomic_write_json(record_path, record)
    _atomic_write_json(
        directory / ATTEMPT_RESULT_NAME,
        _result_payload(spec, status, proc.pid, exit_code, started_at, ended_at),
    )
    return 0


# ═════════════════════════════════════════════════════════════════════════════
# Supervisor 본체 (`__daemon__` 모드)
# ═════════════════════════════════════════════════════════════════════════════


class Supervisor:
    """run 1개의 tick loop. 사람이 tick을 돌리는 경로는 만들지 않는다."""

    def __init__(self, run_root):
        self.run_root = pathlib.Path(run_root)
        self.document = controller.read_workgraph(self.run_root)
        self.limits = limits_of(self.document)
        # attempt_id -> {task_id, role, executor_id, dir, pid, last_reconcile}
        self.live = {}
        # 상한이 한 번이라도 포화된 뒤부터 Verifier 우선 배정이 활성화된다(§9.3).
        self.saturated = False
        self.project_root = self._project_root()

    # ── 읽기 ──────────────────────────────────────────────────────────────
    def _project_root(self):
        manifest = self.run_root / "run.json"
        if manifest.is_file():
            with contextlib.suppress(OSError, json.JSONDecodeError):
                return _read_json(manifest).get("project_root")
        return None

    def refresh(self):
        self.document = controller.read_workgraph(self.run_root)
        return self.document

    def tasks(self):
        return self.document.get("mini_tasks") or []

    def task(self, task_id):
        for item in self.tasks():
            if item.get("id") == task_id:
                return item
        return None

    @staticmethod
    def contract(task):
        return task.get("contract") or {}

    def set_state(self, task_id, state, **fields):
        """Controller의 revision lock API로만 상태를 전진시킨다(§4.5 writer 소유권)."""
        controller.set_task_state(self.run_root, task_id, state, **fields)
        self.refresh()

    # ── 복구 ──────────────────────────────────────────────────────────────
    def recover(self):
        """`reconcile-attempts` 3분류를 소비해 재부착 또는 수확한다.

        판정은 전부 `opal-agent`가 한다. 여기서 하는 일은 그 결과에 따라
        (a) 살아 있는 attempt를 live로 되돌리거나(reattach),
        (b) 끝난 attempt의 결과를 미니 태스크 상태에 반영하거나(harvest),
        (c) `reclaim_required` 잔재를 회수한 뒤 실패로 확정하는(orphan) 것뿐이다.
        """
        summary = {"reattach": 0, "harvest": 0, "orphan": 0, "reclaimed": []}
        for directory in iter_attempt_dirs(self.run_root):
            result = read_attempt_result(directory)
            if result is None or not list(directory.glob("*.attempt.json")):
                continue
            task = self.task(result.get("task_id"))
            if task is not None and task.get("state") in TERMINAL_TASK_STATES:
                continue
            report = reconcile_attempt_dir(directory)
            for item in report.get("attempts") or []:
                disposition = item.get("disposition")
                summary[disposition] = summary.get(disposition, 0) + 1
                if disposition == "reattach":
                    self.live[result["attempt_id"]] = {
                        "task_id": result["task_id"],
                        "role": result["role"],
                        "executor_id": result.get("executor_id"),
                        "dir": directory,
                        "pid": result.get("pid"),
                        "last_reconcile": time.monotonic(),
                    }
                    continue
                if item.get("reclaim_required") and reclaim_process_group(item.get("pgid")):
                    summary["reclaimed"].append(result["attempt_id"])
                self.settle(result["attempt_id"], directory, disposition=disposition)
        append_event(
            self.run_root,
            "recovery_completed",
            counts={key: summary[key] for key in ("reattach", "harvest", "orphan")},
            reclaimed=summary["reclaimed"],
        )
        return summary

    # ── attempt 종료 처리 ─────────────────────────────────────────────────
    def settle(self, attempt_id, directory, disposition=None):
        result = read_attempt_result(directory) or {}
        status = result.get("status")
        if disposition == "orphan" or status not in ("succeeded", "failed"):
            status = "failed"
        entry = self.live.pop(attempt_id, None)
        task_id = result.get("task_id") or (entry or {}).get("task_id")
        role = result.get("role") or (entry or {}).get("role")
        append_event(
            self.run_root,
            "attempt_exited",
            attempt_id=attempt_id,
            task_id=task_id,
            role=role,
            status=status,
            exit_code=result.get("exit_code"),
            disposition=disposition,
        )
        self._apply_outcome(
            task_id,
            role,
            status == "succeeded",
            executor_id=result.get("executor_id") or (entry or {}).get("executor_id"),
        )

    def _apply_outcome(self, task_id, role, succeeded, executor_id=None):
        task = self.task(task_id)
        if task is None or task.get("state") in TERMINAL_TASK_STATES:
            return
        if role == ROLE_VERIFIER:
            if succeeded:
                self.set_state(task_id, STATE_ACCEPTED)
            else:
                self._retry_or_fail(task, STATE_CANDIDATE_READY, "verify_attempts")
            return

        # runner / executor — 같은 세대의 attempt가 모두 끝나야 태스크가 전진한다.
        outcomes = dict(task.get("generation_outcomes") or {})
        # Executor별 결과를 분리해 배치 사이에도 완료 여부를 보존한다.
        key = (
            ROLE_RUNNER
            if role == ROLE_RUNNER
            else "%s:%s" % (ROLE_EXECUTOR, executor_id)
        )
        outcomes[key] = (
            bool(succeeded) if key not in outcomes
            else bool(outcomes[key]) and bool(succeeded)
        )
        if any(entry["task_id"] == task_id for entry in self.live.values()):
            self.set_state(task_id, STATE_RUNNING, generation_outcomes=outcomes)
            return

        self.refresh()
        task = self.task(task_id)
        if any(value is False for value in outcomes.values()):
            self._release_runner_lease(task_id)
            self._retry_or_fail(task, STATE_PENDING, "runner_attempts")
            return
        if self._pending_executors(task):
            self.set_state(task_id, STATE_RUNNING, generation_outcomes=outcomes)
            return
        if all(outcomes.get(key, False) for key in (ROLE_RUNNER, *self._executor_keys(task))):
            self._release_runner_lease(task_id)
            if self.contract(task).get("verify_command"):
                self.set_state(task_id, STATE_CANDIDATE_READY, generation_outcomes={})
            else:
                self.set_state(task_id, STATE_ACCEPTED, generation_outcomes={})
        else:
            self._release_runner_lease(task_id)
            self._retry_or_fail(task, STATE_PENDING, "runner_attempts")

    def _executor_keys(self, task):
        return [
            "%s:%s" % (ROLE_EXECUTOR, item.get("id"))
            for item in self.contract(task).get("executors") or []
            if item.get("run_command") is not None
        ]

    def _pending_executors(self, task):
        """현재 runner 세대에서 아직 dispatch하지 않은 Executor만 반환한다."""
        generation = int(task.get("runner_attempts") or 0)
        launched = {
            item.get("attempt_id")
            for item in task.get("attempts") or []
        }
        return [
            executor
            for executor in self.contract(task).get("executors") or []
            if executor.get("run_command") is not None
            if "%s.%s.%d" % (task["id"], executor.get("id"), generation)
            not in launched
        ]

    def _acquire_runner_lease(self, task, attempt_id):
        """capability owner의 task lease를 발급하고 packet에 실을 receipt를 돌려준다."""
        declared = self.contract(task).get("lease") or {}
        payload = {
            "task_id": task.get("id"),
            "capability_id": task.get("id"),
            "tracked_write_set": list(declared.get("tracked_writes") or []),
            "ephemeral_write_set": list(declared.get("ephemeral_writes") or []),
            "contracts": list(declared.get("contracts") or []),
            "business_rules": [],
            "acceptance_ids": [],
            "runtime_resources": list(declared.get("runtime_resources") or []),
            "global_outputs": [],
        }
        fd, path = tempfile.mkstemp(prefix="oppb-lease-", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False)
            return lease.cmd_acquire(
                {
                    "run_root": str(self.run_root),
                    "attempt": attempt_id,
                    "spec": path,
                    "_values": {"spec": [path]},
                }
            )
        finally:
            with contextlib.suppress(OSError):
                os.unlink(path)

    def _release_runner_lease(self, task_id):
        store = lease.read_leases(self.run_root)
        if not any(
            item.get("state") == "active" and item.get("task_id") == task_id
            for item in store.get("leases") or []
        ):
            return
        lease.cmd_release({"run_root": str(self.run_root), "task_id": task_id})

    def _retry_or_fail(self, task, retry_state, counter_key):
        """실패한 attempt를 재시도하거나 태스크를 실패로 확정한다.

        재시도는 자동 tick의 일부다 — 사람이 재촉하는 경로를 만들지 않는다.
        """
        used = int(task.get(counter_key) or 0)
        if used < int(self.limits["max_attempts_per_task"]):
            self.set_state(task["id"], retry_state, generation_outcomes={})
        else:
            self.set_state(task["id"], STATE_FAILED, generation_outcomes={})

    # ── 관측 ──────────────────────────────────────────────────────────────
    def poll_live(self):
        now = time.monotonic()
        for attempt_id in list(self.live):
            entry = self.live.get(attempt_id)
            if entry is None:
                continue
            result = read_attempt_result(entry["dir"]) or {}
            if result.get("status") in ("succeeded", "failed"):
                self.settle(attempt_id, entry["dir"])
                continue
            if now - entry["last_reconcile"] < RECONCILE_INTERVAL_SEC:
                continue
            entry["last_reconcile"] = now
            # 실행기까지 강제 종료돼 result.json이 running으로 굳은 경우를 잡는다 —
            # 생존 판정은 하지 않고 `reconcile-attempts`에 위임한다.
            for item in reconcile_attempt_dir(entry["dir"]).get("attempts") or []:
                if item.get("disposition") == "reattach":
                    continue
                if item.get("reclaim_required"):
                    reclaim_process_group(item.get("pgid"))
                self.settle(attempt_id, entry["dir"], disposition=item.get("disposition"))

    def counts(self):
        runners = sum(1 for e in self.live.values() if e["role"] == ROLE_RUNNER)
        executors = sum(1 for e in self.live.values() if e["role"] == ROLE_EXECUTOR)
        return runners, executors, len(self.live)

    # ── 배정 ──────────────────────────────────────────────────────────────
    def _deps_accepted(self, task):
        for dependency in task.get("depends_on") or []:
            other = self.task(dependency)
            if other is None or other.get("state") != STATE_ACCEPTED:
                return False
        return True

    def schedule(self):
        """동시성 상한 3종을 집행하며 배정한다.

        상한이 한 번 포화된 뒤에는(`self.saturated`) 반환되는 slot을 신규 Runner보다
        준비된 candidate의 Verifier에 먼저 준다(제안서 §9.3, 수용기준 10). 포화 전에는
        workgraph 선언 순서대로 채운다 — 아직 아무것도 돌지 않는 시점에 Verifier를
        앞세우면 검증할 대상이 생기기도 전에 slot을 점유해 처리량이 무너진다.
        """
        verifiable = [
            task for task in self.tasks()
            if task.get("state") == STATE_CANDIDATE_READY
            and self.contract(task).get("verify_command")
        ]
        runnable = [
            task for task in self.tasks()
            if task.get("state") in (STATE_PENDING, None) and self._deps_accepted(task)
        ]
        continuable = [
            task for task in self.tasks()
            if task.get("state") == STATE_RUNNING
            and not any(
                value is False
                for value in (task.get("generation_outcomes") or {}).values()
            )
            and self._pending_executors(task)
        ]
        if self.saturated:
            order = [(ROLE_VERIFIER, t) for t in verifiable]
            order += [(ROLE_EXECUTOR, t) for t in continuable]
            order += [(ROLE_RUNNER, t) for t in runnable]
        else:
            order = []
            verifiable_ids = {t["id"] for t in verifiable}
            continuable_ids = {t["id"] for t in continuable}
            runnable_ids = {t["id"] for t in runnable}
            for task in self.tasks():
                if task["id"] in verifiable_ids:
                    order.append((ROLE_VERIFIER, task))
                elif task["id"] in continuable_ids:
                    order.append((ROLE_EXECUTOR, task))
                elif task["id"] in runnable_ids:
                    order.append((ROLE_RUNNER, task))

        for kind, task in order:
            if kind == ROLE_VERIFIER:
                self._admit_verifier(task)
            elif kind == ROLE_EXECUTOR:
                self._admit_executors(task)
            else:
                self._admit_task(task)

        if self.counts()[2] >= int(self.limits["max_total_agent_processes"]):
            self.saturated = True

    def _admit_verifier(self, task):
        if self.counts()[2] >= int(self.limits["max_total_agent_processes"]):
            return
        used = int(task.get("verify_attempts") or 0) + 1
        self.set_state(task["id"], STATE_VERIFYING, verify_attempts=used)
        self.launch(task["id"], ROLE_VERIFIER, used)

    def _admit_task(self, task):
        """Runner와 그 Executor를 하나의 admission 단위로 승인한다.

        Executor는 이미 승인된 작업의 일부지만 pool 상한보다 많을 수 있다. Runner를 먼저
        승인하고 빈 slot만큼 배치하며, 다음 tick이 같은 세대의 잔여 Executor를 이어서 넣는다.
        """
        runners, _, total = self.counts()
        if runners + 1 > int(self.limits["max_active_runners"]):
            return
        if total + 1 > int(self.limits["max_total_agent_processes"]):
            return

        used = int(task.get("runner_attempts") or 0) + 1
        self.set_state(
            task["id"], STATE_RUNNING, runner_attempts=used, generation_outcomes={}
        )
        self.launch(task["id"], ROLE_RUNNER, used)
        self.refresh()
        self._admit_executors(self.task(task["id"]))

    def _admit_executors(self, task):
        """현재 세대의 미실행 Executor를 전역 pool의 빈 slot만큼 배치한다."""
        if task is None:
            return
        generation = int(task.get("runner_attempts") or 0)
        for executor in self._pending_executors(task):
            _, running_executors, total = self.counts()
            if running_executors >= int(self.limits["max_active_executors"]):
                return
            if total >= int(self.limits["max_total_agent_processes"]):
                return
            self.launch(
                task["id"], ROLE_EXECUTOR, generation, executor_id=executor.get("id")
            )
            self.refresh()
            task = self.task(task["id"])

    def launch(self, task_id, role, generation, executor_id=None):
        """execution-packet을 Controller에 요청하고 attempt 실행기를 기동한다."""
        attempt_id = "%s.%s.%d" % (task_id, executor_id or role, generation)
        task = self.task(task_id) or {}
        fallback_runner = (
            role == ROLE_RUNNER and self.contract(task).get("run_command") is None
        )
        receipt = self._acquire_runner_lease(task, attempt_id) if fallback_runner else None
        try:
            packet_path, packet = controller.create_execution_packet(
                self.run_root,
                task_id,
                attempt_id,
                role=role,
                executor_id=executor_id,
                **({"lease_receipt": receipt} if receipt else {}),
            )
            self.refresh()
            directory = controller.attempt_dir(self.run_root, task_id, attempt_id)
            directory.mkdir(parents=True, exist_ok=True)
            (directory / AGENT_RUN_DIRNAME).mkdir(exist_ok=True)

            command = packet.get("command") or self._agent_command(
                task_id, role, directory, packet_path
            )
            spec = {
                "attempt_id": attempt_id,
                "task_id": task_id,
                "role": role,
                "executor_id": executor_id,
                "command": command,
                "cwd": self.project_root,
                "attempt_dir": str(directory),
                "provider": "command" if packet.get("command") else "opal-agent",
            }
            spec_path = directory / ATTEMPT_SPEC_NAME
            _atomic_write_json(spec_path, spec)

            log = open(directory / ATTEMPT_RUNNER_LOG_NAME, "ab")
            try:
                proc = subprocess.Popen(
                    [sys.executable, str(pathlib.Path(__file__).resolve()),
                     "__attempt__", "--spec", str(spec_path)],
                    stdout=log,
                    stderr=log,
                    stdin=subprocess.DEVNULL,
                    # Supervisor가 죽어도 attempt는 살아남아야 재부착을 관측할 수 있다.
                    start_new_session=True,
                )
            finally:
                log.close()
        except BaseException:
            if fallback_runner:
                self._release_runner_lease(task_id)
            raise

        pid = None
        deadline = time.monotonic() + LAUNCH_PID_WAIT_SEC
        while time.monotonic() < deadline:
            result = read_attempt_result(directory)
            if result and result.get("pid"):
                pid = result["pid"]
                break
            if proc.poll() is not None and result is not None:
                break
            time.sleep(0.02)

        self.live[attempt_id] = {
            "task_id": task_id,
            "role": role,
            "executor_id": executor_id,
            "dir": directory,
            "pid": pid,
            "last_reconcile": time.monotonic(),
        }
        append_event(
            self.run_root,
            "attempt_launched",
            attempt_id=attempt_id,
            task_id=task_id,
            role=role,
            executor_id=executor_id,
            pid=pid,
        )

    def _agent_command(self, task_id, role, directory, packet_path):
        """실행 명령이 계약에 없으면 `opal-agent` CLI로 기동한다.

        provider CLI를 Supervisor가 직접 spawn하지 않는다 — 기동도 `opal-agent`를
        경유한다(W-38 B-2). 산출물이 섞이지 않게 opal-agent에는 전용 하위 run-dir을 준다.
        """
        task = self.task(task_id) or {}
        prompt = (
            "[WORKER]\n"
            "You are the OPPB opal-capability-agent for role %s. "
            "Read and follow ~/.opal/agents/opal-capability-agent/AGENT.md first. "
            "Then read the execution packet at %s and perform only that packet's "
            "task, role, lease, contract, and budget. Return the required structured JSON."
            % (role, packet_path)
        )
        return [
            *opal_agent_entrypoint(),
            prompt,
            "--provider", agent_provider(self.project_root),
            "--timeout", str(CAPABILITY_AGENT_TIMEOUT_SEC),
            "--run-dir", str(directory / AGENT_RUN_DIRNAME),
            "--phase", str(task_id),
            "--attempt", role,
        ]

    # ── loop ──────────────────────────────────────────────────────────────
    def finished(self):
        if self.live:
            return False
        return all(task.get("state") in TERMINAL_TASK_STATES for task in self.tasks())

    def loop(self):
        while True:
            self.refresh()
            self.poll_live()
            self.refresh()
            self.schedule()
            if self.finished():
                append_event(self.run_root, "run_completed")
                return
            time.sleep(TICK_INTERVAL_SEC)


def run_daemon(run_root, handshake_path):
    run_root = pathlib.Path(run_root)
    lock_handle = open(run_root / LOCK_NAME, "a+")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        _atomic_write_json(
            handshake_path,
            {"ok": False, "error": "run_lock_held", "run_root": str(run_root)},
        )
        return 1

    try:
        supervisor = Supervisor(run_root)
        _atomic_write_json(
            run_root / SUPERVISOR_STATE_NAME,
            {
                "schema_version": SCHEMA_VERSION,
                "supervisor_pid": os.getpid(),
                "started_at": time.time(),
            },
        )
        append_event(run_root, "supervisor_started", supervisor_pid=os.getpid())
        recovery = supervisor.recover()
    except (SupervisorError, controller.ControllerError) as exc:
        _atomic_write_json(
            handshake_path, {"ok": False, "error": exc.code, "message": exc.message}
        )
        return 1

    # 복구가 끝난 뒤에만 기동 성공을 알린다 — 호출자가 응답을 받은 시점에는 재부착·수확이
    # 이미 반영돼 있고, tick은 사람 개입 없이 그대로 이어진다.
    _atomic_write_json(
        handshake_path,
        {
            "ok": True,
            "supervisor_pid": os.getpid(),
            "run_root": str(run_root),
            "recovery": {key: recovery[key] for key in ("reattach", "harvest", "orphan")},
            "reclaimed": recovery["reclaimed"],
        },
    )

    try:
        supervisor.loop()
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        lock_handle.close()
    return 0


# ═════════════════════════════════════════════════════════════════════════════
# CLI가 호출하는 공개 진입점
# ═════════════════════════════════════════════════════════════════════════════


def start_supervisor(run_root):
    """Supervisor를 기동하고 복구 완료까지 기다린 뒤 결과를 돌려준다.

    `start`와 `resume`이 같은 경로를 쓴다 — 비정상 종료 뒤 재기동은 자동 복구이지
    상태를 건너뛰는 강제 resume이 아니다(제안서 §4.1).
    """
    run_root = pathlib.Path(run_root)
    controller.read_workgraph(run_root)  # 선행 조건 — 없으면 여기서 거부한다.

    handshake = run_root / (".supervisor-handshake-%s.json" % uuid.uuid4().hex[:8])
    log = open(run_root / DAEMON_LOG_NAME, "ab")
    try:
        subprocess.Popen(
            [sys.executable, str(pathlib.Path(__file__).resolve()),
             "__daemon__", "--run-root", str(run_root), "--handshake", str(handshake)],
            stdout=log,
            stderr=log,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        raise SupervisorError("supervisor_spawn_failed", str(exc)) from exc
    finally:
        log.close()

    deadline = time.monotonic() + HANDSHAKE_TIMEOUT_SEC
    payload = None
    while time.monotonic() < deadline:
        if handshake.is_file():
            with contextlib.suppress(OSError, json.JSONDecodeError):
                payload = _read_json(handshake)
            if payload is not None:
                break
        time.sleep(0.05)
    with contextlib.suppress(OSError):
        handshake.unlink()

    if payload is None:
        raise SupervisorError("supervisor_handshake_timeout", "run_root=%s" % run_root)
    if not payload.get("ok"):
        raise SupervisorError(
            payload.get("error") or "supervisor_spawn_failed", payload.get("message") or ""
        )
    return payload


def read_status(run_root):
    """run의 현재 관측값. 부작용이 없고 Supervisor를 기동하지 않는다."""
    run_root = pathlib.Path(run_root)
    document = controller.read_workgraph(run_root)
    attempts = []
    for directory in iter_attempt_dirs(run_root):
        result = read_attempt_result(directory)
        if result is None:
            continue
        attempts.append(
            {
                "attempt_id": result.get("attempt_id"),
                "task_id": result.get("task_id"),
                "role": result.get("role"),
                "executor_id": result.get("executor_id"),
                "status": result.get("status"),
                "pid": result.get("pid"),
                "exit_code": result.get("exit_code"),
            }
        )
    running = [item for item in attempts if item["status"] == "running"]
    supervisor_pid = None
    state_path = run_root / SUPERVISOR_STATE_NAME
    if state_path.is_file():
        with contextlib.suppress(OSError, json.JSONDecodeError):
            supervisor_pid = _read_json(state_path).get("supervisor_pid")
    return {
        "run_root": str(run_root),
        "supervisor_pid": supervisor_pid,
        "revision": document.get("revision"),
        "limits": limits_of(document),
        "active_agent_processes": len(running),
        "active_runners": sum(1 for item in running if item["role"] == ROLE_RUNNER),
        "active_executors": sum(1 for item in running if item["role"] == ROLE_EXECUTOR),
        "attempts": attempts,
        "mini_tasks": [
            {"id": task.get("id"), "state": task.get("state")}
            for task in document.get("mini_tasks") or []
        ],
    }


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(prog="oppb-supervisor")
    sub = parser.add_subparsers(dest="mode", required=True)

    daemon = sub.add_parser("__daemon__")
    daemon.add_argument("--run-root", required=True)
    daemon.add_argument("--handshake", required=True)

    attempt = sub.add_parser("__attempt__")
    attempt.add_argument("--spec", required=True)

    args = parser.parse_args(argv)
    if args.mode == "__daemon__":
        return run_daemon(args.run_root, pathlib.Path(args.handshake))
    return run_attempt(args.spec)


if __name__ == "__main__":
    sys.exit(main())
