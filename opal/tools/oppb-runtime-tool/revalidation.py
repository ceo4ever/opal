"""
@header {
  "module": "revalidation",
  "task": "132",
  "layer": "util",
  "domain": "oppb-runtime",
  "description": "OPPB `needs_revalidation` 1-hop 전파기(W-26) — 외부 계약 revision이 바뀐 시점에 그 계약의 **직접 consumer만** `needs_revalidation`으로 전환하고, consumer의 수용 시나리오와 계약 테스트만 실제 자식 프로세스로 실행한다(제안서 §9.1). 통과하면 즉시 `accepted`로 되돌리고, 실패하면 그 consumer의 Repair attempt만 연다. 재검증 실패 그 자체로는 downstream을 전환하지 않는다 — Repair가 다시 출력 계약 revision을 바꾼 경우에만 그 계약을 대상으로 한 다음 `revalidate` 호출이 1-hop 더 전파한다. 무관하거나 아직 실행 전(`pending`/`ready`)인 태스크는 재검증 대상이 아니며 attempt를 만들지 않는다. 미니 태스크 배열은 동결 스키마의 `mini_tasks[]`를 읽고, 상태 어휘도 동결 `task_state` enum(controller.TASK_STATES)을 단일 출처로 쓴다 — 재선언하지 않는다. run root 문서 쓰기는 controller.py의 `workgraph_transaction`(배타 락 → revision 대조 → 원자 교체)으로만 수행하고 락 구현을 재구현하지 않는다. `compute_scope_hash`도 controller의 것을 호출만 한다. 표준 라이브러리와 실제 프로세스만 사용하고 플랫폼 분기를 두지 않는다.",
  "exports": [
    "ERROR_CODES", "RevalidationError",
    "REVALIDATABLE_STATES", "SCOPE_KINDS",
    "direct_consumers", "revalidation_scope", "revalidate_command"
  ],
  "depends": [
    "opal/tools/oppb-runtime-tool/controller.py",
    "opal/core/references/harness/tool-output-contract.md"
  ]
}
"""

# 표준 라이브러리만 사용한다 (신규 의존성 도입 금지)
from __future__ import annotations

import datetime
import json
import os
import pathlib
import shlex
import subprocess
import uuid

import controller

EXIT_ERROR = 1
EXIT_USAGE = 2

PACKET_FILENAME = "execution-packet.json"
RESULT_FILENAME = "result.json"

# 미니 태스크 상태 어휘는 동결 스키마 `task_state`(controller.TASK_STATES, 10종)가
# 단일 SSOT다. 제안서 §9.1의 `queued`는 추상 상태기계의 어휘이고, 구현은 이를
# `pending`/`ready`로 세분한 정련이다(`candidate_ready`·`failed`도 같은 정련의 산물).
# 이 모듈은 그 어휘를 재선언하지 않고 controller의 것을 그대로 참조한다.

# 재검증 대상이 될 수 있는 상태 — "이미 실행을 마치고 통과한" 상태 하나뿐이다.
# pending·ready(실행 전)·running·candidate_ready·verifying·repair·blocked·failed는
# 재검증하지 않는다(§9.1).
REVALIDATABLE_STATES = ("accepted",)

# 재검증 범위 — 수용 시나리오와 계약 테스트뿐이다. 전체 테스트·빌드는 범위가 아니다(§9.1).
SCOPE_KINDS = ("acceptance_scenario", "contract_test")

# 각 kind가 태스크 record에서 읽는 배열 필드.
SCOPE_FIELDS = (
    ("acceptance_scenario", "acceptance_scenarios"),
    ("contract_test", "contract_tests"),
)

MODE_REVALIDATION = "revalidation"
MODE_REPAIR = "repair"

# 재검증 명령 1건의 상한. 무한 대기가 run을 멈추지 않게 한다.
COMMAND_TIMEOUT_SECONDS = 600

ERROR_CODES = {
    "contract_missing": "--contract는 필수입니다.",
    "revision_missing": "--revision은 필수입니다.",
    "revision_invalid": "--revision은 0 이상의 정수여야 합니다.",
    "contract_not_found": "workgraph.json에 해당 계약이 없습니다.",
    "revalidation_graph_invalid": (
        "workgraph.json이 재검증 그래프 계약(mini_tasks[]·contracts[])을 만족하지 않습니다."
    ),
    "revalidation_command_invalid": "재검증 명령이 비어 있지 않은 문자열이 아닙니다.",
    "task_state_unknown": "동결 스키마 task_state enum에 없는 미니 태스크 상태입니다.",
}


class RevalidationError(Exception):
    """폐쇄 집합 `ERROR_CODES`의 코드 하나로 실패를 표현한다.

    진입점 모듈(`oppb_runtime_tool.py`)의 `ToolError`로 어댑트되어 단일 라인 JSON
    출력 계약을 그대로 따른다(verifier_adapter.py의 `VerifierAdapterError`와 같은 모양).
    """

    def __init__(self, code, message="", exit_code=EXIT_ERROR, **extra):
        super().__init__(message or code)
        self.code = code
        self.message = message
        self.exit_code = exit_code
        self.extra = extra


def _now():
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


# ─────────────────────────────────────────────────────────────────────────────
# 인자 읽기 — 부작용보다 먼저 끝낸다
# ─────────────────────────────────────────────────────────────────────────────


def _require_run_root(opts):
    raw = opts.get("run_root")
    if not raw:
        raise RevalidationError("run_root_missing")
    if not os.path.isabs(raw):
        raise RevalidationError("run_root_not_absolute", "받은 값: %s" % raw)
    path = pathlib.Path(raw)
    if not path.is_dir():
        raise RevalidationError("run_root_not_found", "받은 값: %s" % raw)
    return path


def _require_contract_id(opts):
    contract_id = opts.get("contract")
    if not contract_id:
        raise RevalidationError("contract_missing")
    return contract_id


def _require_revision(opts):
    raw = opts.get("revision")
    if raw is None or raw == "":
        raise RevalidationError("revision_missing")
    try:
        revision = int(str(raw), 10)
    except (TypeError, ValueError):
        raise RevalidationError(
            "revision_invalid", "받은 값: %r" % raw, EXIT_USAGE
        ) from None
    if revision < 0:
        raise RevalidationError("revision_invalid", "받은 값: %r" % raw, EXIT_USAGE)
    return revision


# ─────────────────────────────────────────────────────────────────────────────
# 재검증 그래프 읽기
#   workgraph.json은 controller.py가 유일한 writer이므로 읽기 export로만 접근하고,
#   쓰기는 controller.workgraph_transaction 안에서만 한다.
# ─────────────────────────────────────────────────────────────────────────────


def _tasks_of(document):
    tasks = document.get("mini_tasks")
    if not isinstance(tasks, list):
        raise RevalidationError(
            "revalidation_graph_invalid",
            "workgraph.json 최상위에 mini_tasks 배열이 없습니다.",
        )
    for task in tasks:
        if not isinstance(task, dict) or not task.get("id"):
            raise RevalidationError(
                "revalidation_graph_invalid", "mini_tasks[] 항목에 id가 없습니다."
            )
        state = task.get("state")
        if state not in controller.TASK_STATES:
            raise RevalidationError(
                "task_state_unknown",
                "%s의 상태=%r (허용: %s)"
                % (task["id"], state, ", ".join(controller.TASK_STATES)),
            )
    return tasks


def _contracts_of(document):
    contracts = document.get("contracts")
    if not isinstance(contracts, list):
        raise RevalidationError(
            "revalidation_graph_invalid",
            "workgraph.json 최상위에 contracts 배열이 없습니다.",
        )
    return contracts


def _find_contract(document, contract_id):
    for contract in _contracts_of(document):
        if isinstance(contract, dict) and contract.get("id") == contract_id:
            return contract
    raise RevalidationError("contract_not_found", "받은 값: %s" % contract_id)


def _find_task(tasks, task_id):
    for task in tasks:
        if task.get("id") == task_id:
            return task
    return None


def direct_consumers(tasks, contract_id):
    """해당 계약을 **직접** 소비하는 태스크 id — 1-hop만이다(§9.1).

    `consumes_contracts`에 이 계약을 직접 적은 태스크만 센다. 그 태스크의 출력
    계약을 소비하는 2-hop consumer는 여기서 세지 않는다 — 출력 계약 revision이
    실제로 바뀐 뒤 그 계약을 대상으로 한 다음 호출이 전파한다.
    소유자(`produces_contract`)는 소비자가 아니므로 대상이 아니다.
    """
    hits = []
    for task in tasks:
        consumes = task.get("consumes_contracts") or []
        if not isinstance(consumes, list):
            raise RevalidationError(
                "revalidation_graph_invalid",
                "%s.consumes_contracts가 리스트가 아닙니다." % task.get("id"),
            )
        if contract_id in consumes:
            hits.append(task["id"])
    return hits


def revalidation_scope(task):
    """재검증 범위 — 이 태스크의 수용 시나리오·계약 테스트 명령뿐이다(§9.1).

    `{"kinds": [...], "commands": [...], "entries": [...]}`를 돌려준다. kinds는
    실제로 명령이 하나 이상 있는 종류만 담으며 SCOPE_KINDS 순서로 정렬된다.
    다른 태스크의 명령이나 전체 테스트 스위트는 이 범위에 들어올 수 없다 —
    입력이 이 태스크 record의 두 필드로 닫혀 있다.
    """
    entries = []
    kinds = []
    for kind, field in SCOPE_FIELDS:
        items = task.get(field) or []
        if not isinstance(items, list):
            raise RevalidationError(
                "revalidation_graph_invalid",
                "%s.%s가 리스트가 아닙니다." % (task.get("id"), field),
            )
        for item in items:
            command = (item or {}).get("command")
            if not isinstance(command, str) or not command.strip():
                raise RevalidationError(
                    "revalidation_command_invalid",
                    "%s.%s의 command=%r" % (task.get("id"), field, command),
                )
            entries.append({"kind": kind, "id": item.get("id"), "command": command})
            if kind not in kinds:
                kinds.append(kind)
    return {
        "kinds": sorted(kinds),
        "commands": [entry["command"] for entry in entries],
        "entries": entries,
    }


# ─────────────────────────────────────────────────────────────────────────────
# attempt 산출물 — `attempts/<task>/<attempt>/execution-packet.json`(§4.5)
# ─────────────────────────────────────────────────────────────────────────────


def _new_attempt_id(prefix):
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return "%s-%s-%s" % (prefix, stamp, uuid.uuid4().hex[:8])


def _write_json(path, payload):
    controller._atomic_write_json(path, payload)  # noqa: SLF001 — 원자 쓰기 수단 재사용
    return payload


def _write_packet(run_root, task_id, attempt_id, payload):
    directory = controller.attempt_dir(run_root, task_id, attempt_id)
    directory.mkdir(parents=True, exist_ok=True)
    return _write_json(directory / PACKET_FILENAME, payload)


def _write_result(run_root, task_id, attempt_id, payload):
    directory = controller.attempt_dir(run_root, task_id, attempt_id)
    directory.mkdir(parents=True, exist_ok=True)
    return _write_json(directory / RESULT_FILENAME, payload)


def _run_command(command):
    """재검증 명령 1건을 실제 자식 프로세스로 실행한다 — shell=False, mock 없음."""
    argv = shlex.split(command)
    if not argv:
        raise RevalidationError("revalidation_command_invalid", "받은 값: %r" % command)
    try:
        completed = subprocess.run(
            argv, capture_output=True, text=True, timeout=COMMAND_TIMEOUT_SECONDS
        )
    except subprocess.TimeoutExpired:
        return {"command": command, "exit_code": None, "passed": False, "timeout": True}
    except OSError as exc:
        return {
            "command": command,
            "exit_code": None,
            "passed": False,
            "error": str(exc),
        }
    return {
        "command": command,
        "exit_code": completed.returncode,
        "passed": completed.returncode == 0,
        "stderr_tail": (completed.stderr or "")[-2000:],
    }


# ─────────────────────────────────────────────────────────────────────────────
# revalidate — 계약 revision 변경 1건에 대한 1-hop 재검증
# ─────────────────────────────────────────────────────────────────────────────


def revalidate_command(opts):
    """`revalidate --run-root <R> --contract <id> --revision <n>`.

    절차는 §9.1 그대로다.

    1. 계약 revision을 선언값으로 올린다(이미 같으면 전환 대상 0건).
    2. 그 계약의 **직접 consumer** 중 `accepted`인 것만 `needs_revalidation`으로
       전환한다 — 무관 태스크·`pending`/`ready`(실행 전) consumer·계약 소유자는
       건드리지 않고 attempt도 만들지 않는다.
    3. 전환된 consumer마다 자신의 수용 시나리오·계약 테스트만 실제로 실행한다.
    4. 전부 통과하면 즉시 `accepted`로 복귀하고, 하나라도 실패하면 그 consumer만
       `repair`로 두고 Repair attempt를 연다.
    5. downstream 전파는 여기서 하지 않는다. Repair가 출력 계약 revision을 실제로
       바꿨을 때 그 계약을 인자로 이 명령을 다시 부르는 것이 유일한 전파 경로다 —
       "Repair가 다시 출력 계약을 바꾼 경우에만" 조건을 코드가 아니라 사실로 건다.

    상태 쓰기는 `controller.workgraph_transaction`(배타 락 → revision 대조 →
    원자 교체) 두 번으로만 한다. 명령 실행은 락 밖에서 한다.
    """
    run_root = _require_run_root(opts)
    contract_id = _require_contract_id(opts)
    revision = _require_revision(opts)
    started_at = _now()

    # ── 1·2단계: 계약 revision 갱신과 직접 consumer 전환을 한 트랜잭션에서 한다.
    selected = []
    scopes = {}
    skipped = []
    previous_revision = None
    with controller.workgraph_transaction(run_root) as document:
        tasks = _tasks_of(document)
        contract = _find_contract(document, contract_id)
        previous_revision = contract.get("revision")
        contract["revision"] = revision

        changed = previous_revision != revision
        consumer_ids = direct_consumers(tasks, contract_id) if changed else []

        for task in tasks:
            task_id = task["id"]
            if task_id in consumer_ids and task.get("state") in REVALIDATABLE_STATES:
                task["state"] = "needs_revalidation"
                task["revalidation"] = {
                    "contract": contract_id,
                    "from_revision": previous_revision,
                    "to_revision": revision,
                    "started_at": started_at,
                }
                selected.append(task_id)
                scopes[task_id] = revalidation_scope(task)
            else:
                # 무관·실행 전·이미 재검증 중인 태스크 — 상태도 attempt도 건드리지 않는다.
                skipped.append(task_id)

    # ── 3단계: 락 밖에서 consumer의 수용 시나리오·계약 테스트만 실제로 실행한다.
    outcomes = {}
    for task_id in selected:
        scope = scopes[task_id]
        attempt_id = _new_attempt_id("reval")
        _write_packet(
            run_root,
            task_id,
            attempt_id,
            {
                "schema_version": controller.SCHEMA_VERSION,
                "task_id": task_id,
                "attempt_id": attempt_id,
                "mode": MODE_REVALIDATION,
                "created_at": _now(),
                "contract": {
                    "id": contract_id,
                    "from_revision": previous_revision,
                    "to_revision": revision,
                },
                "revalidation_scope": {
                    "kinds": scope["kinds"],
                    "commands": scope["commands"],
                    "entries": scope["entries"],
                },
            },
        )
        checks = [_run_command(entry["command"]) for entry in scope["entries"]]
        passed = all(check["passed"] for check in checks)
        _write_result(
            run_root,
            task_id,
            attempt_id,
            {
                "schema_version": controller.SCHEMA_VERSION,
                "task_id": task_id,
                "attempt_id": attempt_id,
                "mode": MODE_REVALIDATION,
                "passed": passed,
                "checks": checks,
                "finished_at": _now(),
            },
        )
        outcomes[task_id] = {
            "attempt_id": attempt_id,
            "passed": passed,
            "checks": checks,
        }

    # ── 4단계: 통과 → 즉시 accepted 복귀, 실패 → 그 consumer만 repair.
    accepted = []
    repair_opened = []
    with controller.workgraph_transaction(run_root) as document:
        tasks = _tasks_of(document)
        for task_id in selected:
            task = _find_task(tasks, task_id)
            if task is None:  # 트랜잭션 사이에 사라진 태스크 — 전이할 대상이 없다.
                continue
            outcome = outcomes[task_id]
            if outcome["passed"]:
                task["state"] = "accepted"
                task.pop("revalidation", None)
                accepted.append(task_id)
            else:
                task["state"] = "repair"
                task["revalidation"] = {
                    "contract": contract_id,
                    "from_revision": previous_revision,
                    "to_revision": revision,
                    "failed_attempt_id": outcome["attempt_id"],
                    "failed_at": _now(),
                }
                repair_opened.append(task_id)

    # Repair attempt는 상태 전이가 확정된 뒤에 연다 — 실패한 consumer 하나당 1건이다.
    for task_id in repair_opened:
        outcome = outcomes[task_id]
        repair_attempt_id = _new_attempt_id("repair")
        _write_packet(
            run_root,
            task_id,
            repair_attempt_id,
            {
                "schema_version": controller.SCHEMA_VERSION,
                "task_id": task_id,
                "attempt_id": repair_attempt_id,
                "mode": MODE_REPAIR,
                "created_at": _now(),
                "contract": {
                    "id": contract_id,
                    "from_revision": previous_revision,
                    "to_revision": revision,
                },
                "opened_by": {
                    "reason": "revalidation_failed",
                    "attempt_id": outcome["attempt_id"],
                    "failed_commands": [
                        check["command"] for check in outcome["checks"]
                        if not check["passed"]
                    ],
                },
            },
        )

    return {
        "run_root": str(run_root),
        "contract": contract_id,
        "from_revision": previous_revision,
        "revision": revision,
        "needs_revalidation": sorted(selected),
        "accepted": sorted(accepted),
        "repair_opened": sorted(repair_opened),
        "skipped": sorted(skipped),
        # downstream 전파는 이 호출의 산출물이 아니다 — 출력 계약이 실제로 바뀐 뒤의
        # 다음 revalidate 호출만이 1-hop 더 나아간다(§9.1).
        "propagated": [],
    }


def _parse_json_document(path):  # pragma: no cover - 진단 편의용
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
