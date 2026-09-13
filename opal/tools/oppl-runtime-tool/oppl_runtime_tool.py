"""
@header {
  "module": "oppl_runtime_tool",
  "task": "131",
  "layer": "util",
  "domain": "opal-tools",
  "description": "oppl 2-루프 실행의 유한 실행 계약을 집행하는 CLI — 6개 서브 명령(config/init/admit/attempt-start/attempt-finish/show). 출력은 단일 라인 JSON + exit code만이며(docs/CONVENTIONS.md §도구 출력 계약), 성공은 ok:true·exit 0, 거부는 ok:false·비영 exit이다. init은 state.json.run_id가 없으면 run_identity_missing으로 거부하고 run_id를 발급하지 않는다(D8/C-5). admit은 같은 lock 안에서 제안서 §6.2의 6개 검사를 수행하고 허가된 경우에만 카운터를 증가시키며 active attempt를 예약한다 — 거부 코드는 active_attempt·round_limit_exceeded·attempt_limit_exceeded·resume_limit_exceeded·budget_exceeded·timeout_limit_exceeded·no_progress·decision_required 폐쇄 집합이고, dispatch 상한 초과는 전용 코드가 없으므로 attempt_limit_exceeded에 scope 필드를 동반해 구분한다. attempt-start는 예약 토큰을 실제 attempt-id·attempt record 경로로 바인딩하고, attempt-finish만이 phase 상태 7종을 확정하는 receipt 경로다 — receipt 없는 done 기록 경로를 만들지 않는다(AC-12). T4b 3분기는 어느 경로든 task attempt와 project dispatch를 함께 차감한다(제안서 §6.4). cost_used는 terminal candidate 값을 그대로 누적하며 stream의 result 개수로 배수되지 않는다(C-10).",
  "exports": [
    "cmd_config", "cmd_init", "cmd_admit",
    "cmd_attempt_start", "cmd_attempt_finish", "cmd_show", "main"
  ]
}
"""

# 표준 라이브러리만 사용한다 (신규 의존성 도입 금지)
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from ledger import (  # noqa: E402
    FAILURE_STATUSES,
    NO_PROGRESS_EXEMPT_EXIT_CLASSES,
    PHASE_STATUSES,
    RESUME_LIMIT,
    T4B_BRANCHES,
    ConfigError,
    LedgerStore,
    elapsed_seconds,
    failure_fingerprint,
    is_reservation,
    load_config,
    new_ledger,
    normalize_error_code,
    phase_record,
    reservation_token,
)

# ─────────────────────────────────────────────────────────────────────────────
# 출력 계약 — 단일 라인 JSON + exit code
# ─────────────────────────────────────────────────────────────────────────────

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_CONFIG_INVALID = 2
EXIT_REJECTED = 3

ADMIT_SCOPES = ("round", "dispatch", "task-phase", "resume")

FLAGS = (
    "--task-path", "--run-id", "--scope", "--task-id", "--phase",
    "--attempt-id", "--record-path", "--status", "--cost-usd",
    "--exit-class", "--verifier-id", "--command-id", "--failing-scenarios",
    "--error-code", "--contract-revision", "--t4b-branch",
)


class ToolError(Exception):
    def __init__(self, code, message="", exit_code=EXIT_ERROR, **extra):
        super().__init__(message or code)
        self.code = code
        self.message = message
        self.exit_code = exit_code
        self.extra = extra


def emit(payload, exit_code=EXIT_OK):
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()
    return exit_code


def fail(command, error, message="", exit_code=EXIT_ERROR, **extra):
    payload = {"ok": False, "command": command, "error": error}
    payload.update(extra)
    if message:
        payload["message"] = message
    return emit(payload, exit_code)


# ─────────────────────────────────────────────────────────────────────────────
# 인자 파싱
# ─────────────────────────────────────────────────────────────────────────────

def parse_argv(argv):
    """`--task-path`가 서브커맨드 앞·뒤 어디에 와도 같게 해석한다."""
    command = None
    opts = {}
    index = 0
    while index < len(argv):
        token = argv[index]
        if token.startswith("--"):
            if "=" in token:
                name, value = token.split("=", 1)
                index += 1
            else:
                name = token
                if index + 1 >= len(argv):
                    raise ToolError("usage_error", "option %s requires a value" % name)
                value = argv[index + 1]
                index += 2
            if name not in FLAGS:
                raise ToolError("usage_error", "unknown option %s" % name)
            opts[name[2:].replace("-", "_")] = value
        else:
            if command is not None:
                raise ToolError("usage_error", "unexpected argument %s" % token)
            command = token
            index += 1
    return command, opts


def require(opts, key, command):
    value = opts.get(key)
    if not value:
        raise ToolError("usage_error", "--%s is required for %s" % (key.replace("_", "-"), command))
    return value


def require_config(task_path):
    try:
        return load_config(task_path)
    except ConfigError as exc:
        raise ToolError("config_invalid", str(exc), EXIT_CONFIG_INVALID)


def require_store(task_path):
    store = LedgerStore(task_path)
    if not store.exists():
        raise ToolError("ledger_missing", "runtime ledger not initialized: %s" % store.path)
    return store


# ─────────────────────────────────────────────────────────────────────────────
# config
# ─────────────────────────────────────────────────────────────────────────────

def cmd_config(opts):
    task_path = require(opts, "task_path", "config")
    config = require_config(task_path)
    # 재개 상한은 설정 키가 아니므로 여기에 노출하지 않는다(guards.md §자동 루핑 제약).
    return emit({"ok": True, "command": "config", "config": config})


# ─────────────────────────────────────────────────────────────────────────────
# init — run identity 게이트 (D8 / TASK C-5)
# ─────────────────────────────────────────────────────────────────────────────

def cmd_init(opts):
    task_path = require(opts, "task_path", "init")
    config = require_config(task_path)

    run_id = opts.get("run_id")
    state_path = pathlib.Path(task_path) / "state.json"
    state_run_id = None
    if state_path.is_file():
        try:
            state_run_id = json.loads(state_path.read_text(encoding="utf-8")).get("run_id")
        except (ValueError, OSError):
            state_run_id = None

    # run_id는 state-tool이 발급한다. 이 도구는 발급하지 않고 외래 참조로만 저장한다.
    if not run_id or not state_run_id or run_id != state_run_id:
        raise ToolError(
            "run_identity_missing",
            "state.json must carry the current run_id and it must match --run-id",
        )

    store = LedgerStore(task_path)
    with store.locked():
        ledger = new_ledger(run_id, config)
        store.write(ledger)

    return emit({
        "ok": True,
        "command": "init",
        "run_id": run_id,
        "revision": ledger["revision"],
        "ledger_path": str(store.path),
    })


# ─────────────────────────────────────────────────────────────────────────────
# admit — 제안서 §6.2 6개 검사
# ─────────────────────────────────────────────────────────────────────────────

class Rejected(Exception):
    def __init__(self, code, scope, block=True, **extra):
        super().__init__(code)
        self.code = code
        self.scope = scope
        self.block = block
        self.extra = extra


def _check_admission(ledger, config, scope, task_id, phase):
    """허가 가능하면 None, 아니면 Rejected를 올린다. 어떤 카운터도 건드리지 않는다."""
    # 검사 6 — 사용자 결정이나 비가역 행동 대기 상태가 아닌가
    if ledger.get("status") == "blocked":
        raise Rejected("decision_required", scope, block=False)

    record = None
    if scope in ("task-phase", "resume"):
        record = phase_record(ledger, task_id, phase)
        # 검사 1 — 같은 범위에 active attempt가 없는가
        if record is not None and record.get("active_attempt_id"):
            raise Rejected("active_attempt", scope, block=False,
                           active_attempt_id=record["active_attempt_id"])

    # 검사 4 — 비용·벽시계 시간이 남아 있는가
    max_wall = float(config["max_wall_time_sec"])
    used_wall = elapsed_seconds(ledger)
    if used_wall >= max_wall:
        raise Rejected("budget_exceeded", scope, budget="wall_time",
                       limit=max_wall, used=round(used_wall, 3))
    if "max_cost_usd" in config:
        max_cost = float(config["max_cost_usd"])
        used_cost = float(ledger.get("cost_used") or 0.0)
        if used_cost >= max_cost:
            raise Rejected("budget_exceeded", scope, budget="cost",
                           limit=max_cost, used=used_cost)

    # 검사 2 — 설계 회전·프로젝트 dispatch·task attempt 상한이 남아 있는가
    if scope == "round":
        limit = config["max_design_rounds"]
        if ledger["design_round"] >= limit:
            raise Rejected("round_limit_exceeded", scope, limit=limit,
                           used=ledger["design_round"])
    elif scope == "dispatch":
        # 거부 코드 8종은 폐쇄 집합이고 dispatch 전용 코드가 없다.
        # scope 필드로 task attempt 상한과 구분한다.
        limit = config["max_project_dispatches"]
        if ledger["project_dispatch_count"] >= limit:
            raise Rejected("attempt_limit_exceeded", scope, limit=limit,
                           used=ledger["project_dispatch_count"])
    elif scope == "task-phase":
        used = record["attempt_count"] if record else 0
        limit = config["max_task_attempts"]
        if used >= limit:
            raise Rejected("attempt_limit_exceeded", scope, limit=limit, used=used)
        # 검사 5 — 동일 실패 지문 반복이 무진전 기준 미만인가
        repeats = record["identical_failure_count"] if record else 0
        fail_limit = config["max_identical_failures"]
        if repeats >= fail_limit:
            raise Rejected("no_progress", scope, limit=fail_limit, used=repeats)
    else:  # resume — 검사 3
        used = record["resume_count"] if record else 0
        if used >= RESUME_LIMIT:
            raise Rejected("resume_limit_exceeded", scope, limit=RESUME_LIMIT, used=used)

    return record


def cmd_admit(opts):
    task_path = require(opts, "task_path", "admit")
    config = require_config(task_path)

    scope = require(opts, "scope", "admit")
    if scope not in ADMIT_SCOPES:
        raise ToolError("usage_error", "--scope must be one of %s" % ", ".join(ADMIT_SCOPES))
    task_id = phase = None
    if scope in ("task-phase", "resume"):
        task_id = require(opts, "task_id", "admit --scope %s" % scope)
        phase = require(opts, "phase", "admit --scope %s" % scope)

    store = require_store(task_path)
    with store.locked():
        ledger = store.read()
        revision = ledger["revision"]
        try:
            _check_admission(ledger, config, scope, task_id, phase)
        except Rejected as rejection:
            if rejection.block and ledger.get("status") != "blocked":
                # 상한·무진전 도달은 blocked 전이다(제안서 §5 · §6.3).
                ledger["status"] = "blocked"
                store.write(ledger, expected_revision=revision)
            payload = {"ok": False, "command": "admit",
                       "error": rejection.code, "scope": rejection.scope}
            payload.update(rejection.extra)
            return emit(payload, EXIT_REJECTED)

        # 허가된 경우에만 카운터를 증가시킨다(제안서 §6.2).
        token = None
        if scope == "round":
            ledger["design_round"] += 1
            granted = {"design_round": ledger["design_round"]}
        elif scope == "dispatch":
            ledger["project_dispatch_count"] += 1
            granted = {"project_dispatch_count": ledger["project_dispatch_count"]}
        else:
            record = phase_record(ledger, task_id, phase, create=True)
            if scope == "task-phase":
                record["attempt_count"] += 1
            else:
                record["resume_count"] += 1
            token = reservation_token()
            record["active_attempt_id"] = token
            record["status"] = "pending"
            granted = {
                "task_id": task_id,
                "phase": phase,
                "attempt_count": record["attempt_count"],
                "resume_count": record["resume_count"],
            }
        store.write(ledger, expected_revision=revision)

    payload = {"ok": True, "command": "admit", "scope": scope, "revision": ledger["revision"]}
    payload.update(granted)
    if token:
        payload["reservation_id"] = token
    return emit(payload)


# ─────────────────────────────────────────────────────────────────────────────
# attempt-start — 예약 토큰을 attempt-id·record 경로로 바인딩
# ─────────────────────────────────────────────────────────────────────────────

def cmd_attempt_start(opts):
    task_path = require(opts, "task_path", "attempt-start")
    require_config(task_path)
    task_id = require(opts, "task_id", "attempt-start")
    phase = require(opts, "phase", "attempt-start")
    attempt_id = require(opts, "attempt_id", "attempt-start")
    record_path = require(opts, "record_path", "attempt-start")

    store = require_store(task_path)
    with store.locked():
        ledger = store.read()
        revision = ledger["revision"]
        record = phase_record(ledger, task_id, phase)
        if record is None or not record.get("active_attempt_id"):
            raise ToolError("no_admission",
                            "attempt-start requires a prior admit for %s/%s" % (task_id, phase))
        if not is_reservation(record["active_attempt_id"]):
            raise ToolError("active_attempt",
                            "attempt %s is already started" % record["active_attempt_id"])
        record["active_attempt_id"] = attempt_id
        record["record_path"] = record_path   # attempt record는 경로 외래 참조로만 갖는다(D4)
        record["status"] = "running"
        store.write(ledger, expected_revision=revision)

    return emit({
        "ok": True, "command": "attempt-start", "task_id": task_id, "phase": phase,
        "attempt_id": attempt_id, "record_path": record_path, "revision": ledger["revision"],
    })


# ─────────────────────────────────────────────────────────────────────────────
# attempt-finish — phase 상태를 확정하는 유일한 receipt 경로 (AC-12)
# ─────────────────────────────────────────────────────────────────────────────

def _parse_failing_scenarios(raw):
    if raw is None:
        return []
    try:
        value = json.loads(raw)
    except ValueError:
        raise ToolError("usage_error", "--failing-scenarios must be a JSON array")
    if not isinstance(value, list):
        raise ToolError("usage_error", "--failing-scenarios must be a JSON array")
    return [str(item) for item in value]


def cmd_attempt_finish(opts):
    task_path = require(opts, "task_path", "attempt-finish")
    require_config(task_path)
    task_id = require(opts, "task_id", "attempt-finish")
    phase = require(opts, "phase", "attempt-finish")
    attempt_id = require(opts, "attempt_id", "attempt-finish")
    status = require(opts, "status", "attempt-finish")
    if status not in PHASE_STATUSES:
        raise ToolError("usage_error", "--status must be one of %s" % ", ".join(PHASE_STATUSES))

    branch = opts.get("t4b_branch")
    if branch is not None and branch not in T4B_BRANCHES:
        raise ToolError("usage_error", "--t4b-branch must be one of %s" % ", ".join(T4B_BRANCHES))

    cost_usd = None
    if opts.get("cost_usd") is not None:
        try:
            cost_usd = float(opts["cost_usd"])
        except ValueError:
            raise ToolError("usage_error", "--cost-usd must be a number")

    scenarios = _parse_failing_scenarios(opts.get("failing_scenarios"))
    exit_class = opts.get("exit_class")

    store = require_store(task_path)
    with store.locked():
        ledger = store.read()
        revision = ledger["revision"]
        record = phase_record(ledger, task_id, phase)
        if record is None or record.get("active_attempt_id") != attempt_id:
            # attempt-start가 바인딩하지 않은 attempt는 상태를 확정할 수 없다.
            raise ToolError(
                "attempt_not_bound",
                "attempt %s is not the bound active attempt for %s/%s" % (attempt_id, task_id, phase),
            )

        record["status"] = status
        record["active_attempt_id"] = None

        # C-10 — terminal candidate의 total_cost_usd를 그대로 반영한다(합산·배수 금지).
        if cost_usd is not None:
            ledger["cost_used"] = round(float(ledger.get("cost_used") or 0.0) + cost_usd, 10)

        fingerprint = None
        if status in FAILURE_STATUSES and exit_class not in NO_PROGRESS_EXEMPT_EXIT_CLASSES:
            fingerprint = failure_fingerprint(
                task_id=task_id,
                phase=phase,
                verifier_id=opts.get("verifier_id"),
                command_id=opts.get("command_id"),
                exit_class=exit_class,
                failing_scenario_ids=scenarios,
                normalized_error_code=normalize_error_code(opts.get("error_code")),
                contract_revision=opts.get("contract_revision"),
            )
            if fingerprint == record.get("last_failure_fingerprint"):
                record["identical_failure_count"] += 1
            else:
                record["last_failure_fingerprint"] = fingerprint
                record["identical_failure_count"] = 1

        # 제안서 §6.4 — T4b 3분기 어느 경로든 project dispatch를 함께 차감한다.
        if branch is not None:
            ledger["project_dispatch_count"] += 1

        store.write(ledger, expected_revision=revision)

    payload = {
        "ok": True, "command": "attempt-finish", "task_id": task_id, "phase": phase,
        "attempt_id": attempt_id, "status": status, "revision": ledger["revision"],
        "cost_used": ledger["cost_used"],
        "project_dispatch_count": ledger["project_dispatch_count"],
    }
    if fingerprint:
        payload["failure_fingerprint"] = fingerprint
        payload["identical_failure_count"] = record["identical_failure_count"]
    if branch is not None:
        payload["t4b_branch"] = branch
    return emit(payload)


# ─────────────────────────────────────────────────────────────────────────────
# show
# ─────────────────────────────────────────────────────────────────────────────

def cmd_show(opts):
    task_path = require(opts, "task_path", "show")
    store = require_store(task_path)
    return emit({"ok": True, "command": "show", "runtime": store.read()})


COMMANDS = {
    "config": cmd_config,
    "init": cmd_init,
    "admit": cmd_admit,
    "attempt-start": cmd_attempt_start,
    "attempt-finish": cmd_attempt_finish,
    "show": cmd_show,
}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    command = None
    try:
        command, opts = parse_argv(argv)
        if command is None:
            raise ToolError("usage_error", "a subcommand is required: %s" % ", ".join(COMMANDS))
        if command not in COMMANDS:
            raise ToolError("usage_error", "unknown subcommand %s" % command)
        return COMMANDS[command](opts)
    except ToolError as exc:
        return fail(command or "unknown", exc.code, exc.message, exc.exit_code, **exc.extra)
    except ConfigError as exc:
        return fail(command or "unknown", "config_invalid", str(exc), EXIT_CONFIG_INVALID)
    except Exception as exc:  # 어떤 경로에서도 다중 라인 출력이나 빈 stdout을 만들지 않는다
        return fail(command or "unknown", "internal_error", "%s: %s" % (type(exc).__name__, exc))


if __name__ == "__main__":
    sys.exit(main())
