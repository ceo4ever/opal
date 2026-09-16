"""
@header {
  "module": "controller",
  "task": "132",
  "layer": "util",
  "domain": "oppb-runtime",
  "description": "OPPB Controller — run root의 `workgraph.json`(미니 태스크 DAG·계약·예산·상태 SSOT)과 `acceptance.json`(완료조건·기여 태스크·증거 역인덱스)의 유일한 writer다. 모든 갱신은 `workgraph.lock` 배타 락 아래에서 revision 대조 후 대상 디렉토리 `mkstemp` → `fsync` → `os.replace`로 원자 교체한다(형태만 `oppl-runtime-tool/ledger.py:336-377` 복제 — 해당 도구를 import하지 않는다). dispatch 시점 가변 입력인 `attempts/<task>/<attempt>/execution-packet.json`을 생성하고 같은 트랜잭션에서 프로젝트 예산을 차감한다. 프로젝트 태스크 `state.json`은 읽지도 쓰지도 않는다 — P0~P5 전이는 Product Flow가 `state-tool`로만 수행한다(제안서 §4.5 산출물 소유권·수용기준 25). 표준 라이브러리만 사용하고 플랫폼 분기를 두지 않는다.",
  "exports": [
    "ERROR_CODES", "ControllerError", "TASK_STATES",
    "workgraph_path", "acceptance_path", "attempt_dir", "compute_scope_hash",
    "read_workgraph", "read_acceptance",
    "workgraph_transaction", "acceptance_transaction",
    "set_task_state", "create_execution_packet", "debit_budget", "POST_RUN_STATES",
    "index_evidence", "workgraph_command",
    "TASK_PROFILES", "DEFAULT_TASK_PROFILE", "DEFAULT_EXECUTION_CONTRACT"
  ],
  "depends": ["opal/core/references/harness/tool-output-contract.md"]
}
"""

# 표준 라이브러리만 사용한다 (신규 의존성 도입 금지)
from __future__ import annotations

import contextlib
import datetime
import fcntl
import hashlib
import json
import os
import pathlib
import tempfile

SCHEMA_VERSION = "1.0"

WORKGRAPH_FILENAME = "workgraph.json"
ACCEPTANCE_FILENAME = "acceptance.json"
LOCK_FILENAME = "workgraph.lock"
ATTEMPTS_DIRNAME = "attempts"
PACKET_FILENAME = "execution-packet.json"

EXIT_ERROR = 1
EXIT_USAGE = 2

# 미니 태스크 상태 — P0~P5 프로젝트 단계와 어휘를 공유하지 않는다(§4.5 소유권 경계).
TASK_STATES = (
    "pending",
    "ready",
    "running",
    "candidate_ready",
    "verifying",
    "accepted",
    "blocked",
    "failed",
    # 재검증 어휘(제안서 §9.1) — 소비 계약 revision 변경으로 재검증이 필요한 accepted 태스크와
    # 그 재검증이 실패해 복구가 열린 태스크. 기존 8종은 값·순서 그대로 보존한다.
    "needs_revalidation",
    "repair",
)

# dispatch 역할 — 예산 차감 축과 1:1 대응한다(§9.3).
ROLES = ("runner", "executor", "verifier")

# 미니 태스크 실행 프로파일 — 제안서 §8의 Fast · Standard · Critical 3종. 단계 수는 같고 깊이만 다르다.
# fast는 상시 산출물을 packet·result·evidence로 한정한다(수용기준 8).
# scope hash 입력이 아니다: compute_scope_hash는 lease 4축만 읽는다.
TASK_PROFILES = ("fast", "standard", "critical")
DEFAULT_TASK_PROFILE = "standard"

# 이 run의 유일한 실행 계약 문서(run root 상대 경로). OPPB는 INTENT.md 하나로 확정한다(수용기준 2).
# scope hash 입력이 아니다.
DEFAULT_EXECUTION_CONTRACT = "INTENT.md"

# runner attempt가 이미 끝났음을 함의하는 상태 — candidate가 존재해야만 도달한다.
# 이 상태로 선언된 태스크에만 runner attempt identity를 공표한다. pending·ready는
# runner가 아직 없고, running은 dispatch가 실제 attempt_id를 발급하며, blocked·failed는
# 귀속할 candidate가 없다.
POST_RUN_STATES = ("candidate_ready", "verifying", "accepted")

SUBCOMMANDS = ("load", "show")

ERROR_CODES = {
    "spec_missing": "--spec는 필수입니다.",
    "spec_not_absolute": "--spec는 절대경로여야 합니다.",
    "spec_not_found": "--spec 경로가 존재하지 않습니다.",
    "spec_not_json": "--spec 파일이 유효한 JSON이 아닙니다.",
    "spec_invalid": "--spec 내용이 workgraph 계약을 만족하지 않습니다.",
    "workgraph_missing": "run root에 workgraph.json이 없습니다.",
    "workgraph_exists": "이미 workgraph.json이 있습니다 — load는 덮어쓰지 않습니다.",
    "workgraph_corrupt": "workgraph.json을 읽을 수 없습니다.",
    "workgraph_revision_conflict": "workgraph.json revision이 기대값과 다릅니다.",
    "acceptance_corrupt": "acceptance.json을 읽을 수 없습니다.",
    "task_not_found": "workgraph.json에 해당 미니 태스크가 없습니다.",
    "task_state_invalid": "허용되지 않은 미니 태스크 상태입니다.",
    "role_invalid": "허용되지 않은 dispatch 역할입니다.",
    "budget_exhausted": "프로젝트 예산이 소진되어 dispatch를 거부합니다.",
    "unknown_subcommand": "알 수 없는 workgraph 하위 명령입니다.",
}


class ControllerError(Exception):
    """폐쇄 집합 `ERROR_CODES`의 코드 하나로 실패를 표현한다.

    진입점 모듈의 `ToolError`로 어댑트되어 단일 라인 JSON 출력 계약을 그대로 따른다.
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
# 경로
# ─────────────────────────────────────────────────────────────────────────────


def workgraph_path(run_root):
    return pathlib.Path(run_root) / WORKGRAPH_FILENAME


def acceptance_path(run_root):
    return pathlib.Path(run_root) / ACCEPTANCE_FILENAME


def lock_path(run_root):
    return pathlib.Path(run_root) / LOCK_FILENAME


def attempt_dir(run_root, task_id, attempt_id):
    """`attempts/<task>/<attempt>/` — dispatch 산출물의 유일한 위치(§4.5)."""
    return pathlib.Path(run_root) / ATTEMPTS_DIRNAME / str(task_id) / str(attempt_id)


# ─────────────────────────────────────────────────────────────────────────────
# 원자 쓰기와 revision lock
#   ledger.py:336-377 패턴을 형태만 복제한다 — lock → revision 대조 →
#   대상 디렉토리 mkstemp → fsync → os.replace. oppl-runtime-tool은 import하지 않는다.
# ─────────────────────────────────────────────────────────────────────────────


@contextlib.contextmanager
def _locked(run_root):
    """run root 단위 배타 락 — 다중 프로세스의 read-modify-write를 직렬화한다."""
    path = lock_path(run_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(path, "a+")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def _atomic_write_json(path, payload):
    """대상 디렉토리에 임시 파일을 만들고 fsync 후 교체한다(부분 쓰기 노출 0)."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".oppb-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, str(path))
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise
    return payload


def _read_json(path, corrupt_code, missing_code=None):
    path = pathlib.Path(path)
    if not path.is_file():
        if missing_code is None:
            return None
        raise ControllerError(missing_code, "받은 값: %s" % path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ControllerError(corrupt_code, "%s: %s" % (path, exc)) from exc


def read_workgraph(run_root):
    """현재 `workgraph.json`. 부재는 오류다 — `workgraph load`가 선행해야 한다."""
    return _read_json(
        workgraph_path(run_root), "workgraph_corrupt", "workgraph_missing"
    )


def read_acceptance(run_root):
    """현재 `acceptance.json`. 부재면 None."""
    return _read_json(acceptance_path(run_root), "acceptance_corrupt")


def _write_document(path, document, expected_revision):
    """revision 대조 후 원자 교체한다. 반드시 `_locked()` 안에서 호출한다."""
    current = None
    if pathlib.Path(path).is_file():
        current = _read_json(path, "workgraph_corrupt").get("revision")
    if expected_revision is not None and current != expected_revision:
        raise ControllerError(
            "workgraph_revision_conflict",
            "현재=%r, 기대=%r" % (current, expected_revision),
        )
    document["revision"] = int(document.get("revision", 0)) + 1
    document["updated_at"] = _now()
    _atomic_write_json(path, document)
    return document


@contextlib.contextmanager
def workgraph_transaction(run_root):
    """`workgraph.json` read-modify-write 트랜잭션.

    락을 잡은 채 현재 문서를 읽어 yield하고, 블록이 정상 종료하면 읽은 시점의
    revision과 대조한 뒤 revision을 1 전진시켜 원자 교체한다. 블록에서 예외가
    나면 아무것도 쓰지 않는다.
    """
    with _locked(run_root):
        document = read_workgraph(run_root)
        expected = document.get("revision")
        yield document
        _write_document(workgraph_path(run_root), document, expected)


@contextlib.contextmanager
def acceptance_transaction(run_root):
    """`acceptance.json` read-modify-write 트랜잭션. workgraph와 같은 락을 쓴다."""
    with _locked(run_root):
        document = read_acceptance(run_root)
        if document is None:
            raise ControllerError("workgraph_missing", "acceptance.json 부재")
        expected = document.get("revision")
        yield document
        _write_document(acceptance_path(run_root), document, expected)


# ─────────────────────────────────────────────────────────────────────────────
# spec 검증과 문서 구성
# ─────────────────────────────────────────────────────────────────────────────


def _require(condition, detail):
    if not condition:
        raise ControllerError("spec_invalid", detail)


def _command(value, detail):
    if value is None:
        return None
    _require(
        isinstance(value, list)
        and value
        and all(isinstance(token, str) for token in value),
        "%s는 비어 있지 않은 문자열 리스트여야 합니다." % detail,
    )
    return list(value)


def _lease(raw, detail):
    raw = raw or {}
    _require(isinstance(raw, dict), "%s는 object여야 합니다." % detail)
    lease = {
        "tracked_writes": [],
        "ephemeral_writes": [],
        "contracts": [],
        "runtime_resources": [],
    }
    for key in lease:
        values = raw.get(key, [])
        _require(
            isinstance(values, list)
            and all(isinstance(item, str) for item in values),
            "%s.%s는 문자열 리스트여야 합니다." % (detail, key),
        )
        lease[key] = list(values)
    return lease


def _check_command(value, detail):
    """수용 시나리오·계약 테스트 1건의 실행 명령.

    정규형은 argv 리스트(`_command`)이고, 실측상 revalidation._run_command는
    비어 있지 않은 단일 문자열도 받아 shlex.split으로 argv로 쪼갠다. 두 형식
    모두 shell을 거치지 않으므로 둘 다 받아 원형 그대로 보존한다.
    """
    if isinstance(value, str):
        _require(value.strip(), "%s는 비어 있지 않은 문자열이어야 합니다." % detail)
        return value
    return _command(value, detail)


def _check_entries(raw, detail):
    """`[{id, command}]` 목록 정규화. 선언이 없으면 빈 목록이다."""
    raw = raw or []
    _require(isinstance(raw, list), "%s는 리스트여야 합니다." % detail)
    entries = []
    for position, item in enumerate(raw):
        _require(isinstance(item, dict), "%s[%d]는 object여야 합니다." % (detail, position))
        entry_id = item.get("id")
        _require(
            isinstance(entry_id, str) and entry_id.strip(),
            "%s[%d].id는 비어 있지 않은 문자열이어야 합니다." % (detail, position),
        )
        entries.append(
            {
                "id": entry_id,
                "command": _check_command(
                    item.get("command"), "%s[%s].command" % (detail, entry_id)
                ),
            }
        )
    return entries


def _contract_ref(raw, detail, with_owner=False):
    """계약 지목 `{id, revision}`(+ owner) 정규화."""
    _require(isinstance(raw, dict), "%s는 object여야 합니다." % detail)
    contract_id = raw.get("id")
    _require(
        isinstance(contract_id, str) and contract_id.strip(),
        "%s.id는 비어 있지 않은 문자열이어야 합니다." % detail,
    )
    revision = raw.get("revision")
    _require(
        isinstance(revision, int) and not isinstance(revision, bool) and revision >= 1,
        "%s.revision은 1 이상의 정수여야 합니다. 받은 값: %r" % (detail, revision),
    )
    ref = {"id": contract_id, "revision": revision}
    if with_owner:
        owner = raw.get("owner")
        _require(
            isinstance(owner, str) and owner.strip(),
            "%s.owner는 비어 있지 않은 문자열이어야 합니다." % detail,
        )
        ref["owner"] = owner
    return ref


def _contracts(raw):
    """workgraph 최상위 `contracts[]` 정규화. 선언이 없으면 빈 목록이다."""
    raw = raw or []
    _require(isinstance(raw, list), "spec.contracts는 리스트여야 합니다.")
    declared = []
    seen = set()
    for index, item in enumerate(raw):
        contract = _contract_ref(item, "contracts[%d]" % index, with_owner=True)
        _require(contract["id"] not in seen, "계약 id 중복: %s" % contract["id"])
        seen.add(contract["id"])
        declared.append(contract)
    return declared


SCOPE_HASH_DOMAIN = "oppb-scope/v1"

LEASE_AXES = ("tracked_writes", "ephemeral_writes", "contracts", "runtime_resources")


def normalize_lease(lease):
    """lease 선언을 정규형으로 만든다 — 축 순서 고정, 각 축은 중복 제거 후 정렬.

    선언 순서나 중복 기입 같은 표기 차이가 scope hash를 흔들지 않게 한다.
    """
    lease = lease or {}
    return {axis: sorted(set(lease.get(axis) or [])) for axis in LEASE_AXES}


def compute_scope_hash(lease):
    """미니 태스크 scope hash — lease 선언의 sha256 64자 hex.

    scope hash는 lease를 소유한 Controller만 계산할 수 있다(PLAN D2). Evidence
    Tool·Scope Lease Tool은 이 함수를 호출하고 자체 재구현하지 않는다.
    같은 lease 선언이면 항상 같은 값, 다르면 다른 값이 나온다.
    """
    payload = json.dumps(
        {"domain": SCOPE_HASH_DOMAIN, "lease": normalize_lease(lease)},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _budget(raw):
    raw = raw or {}
    _require(isinstance(raw, dict), "budget은 object여야 합니다.")
    limits = {}
    for key, value in raw.items():
        _require(
            isinstance(value, int) and not isinstance(value, bool) and value >= 0,
            "budget.%s는 0 이상의 정수여야 합니다." % key,
        )
        limits[key] = value
    return {
        "limits": limits,
        "debited": {"runner": 0, "executor": 0, "verifier": 0, "total": 0},
    }


def _mini_task(raw, index, known_ids):
    _require(isinstance(raw, dict), "mini_tasks[%d]는 object여야 합니다." % index)
    task_id = raw.get("id")
    _require(
        isinstance(task_id, str) and task_id.strip(),
        "mini_tasks[%d].id는 비어 있지 않은 문자열이어야 합니다." % index,
    )
    _require(task_id not in known_ids, "미니 태스크 id 중복: %s" % task_id)

    capability = raw.get("capability")
    _require(
        isinstance(capability, str) and capability.strip(),
        "%s.capability는 비어 있지 않은 문자열이어야 합니다." % task_id,
    )

    # 실행 프로파일 — 선언이 없으면 full. lease와 무관하므로 scope hash에 들어가지 않는다.
    profile = raw.get("profile", DEFAULT_TASK_PROFILE)
    _require(
        profile in TASK_PROFILES,
        "%s.profile은 %s 중 하나여야 합니다. 받은 값: %r"
        % (task_id, " · ".join(TASK_PROFILES), profile),
    )

    depends_on = raw.get("depends_on", [])
    _require(
        isinstance(depends_on, list)
        and all(isinstance(item, str) for item in depends_on),
        "%s.depends_on은 문자열 리스트여야 합니다." % task_id,
    )

    state = raw.get("pre_state", "pending")
    _require(
        state in TASK_STATES,
        "%s.pre_state가 허용 집합 밖입니다: %r" % (task_id, state),
    )

    declared_runner_attempt = raw.get("runner_attempt_id")
    if declared_runner_attempt is not None:
        _require(
            isinstance(declared_runner_attempt, str) and declared_runner_attempt.strip(),
            "%s.runner_attempt_id는 비어 있지 않은 문자열이어야 합니다." % task_id,
        )
        _require(
            state in POST_RUN_STATES,
            "%s.runner_attempt_id는 runner attempt가 끝난 상태(%s)에서만 선언할 수 "
            "있습니다. 받은 pre_state=%r" % (task_id, ", ".join(POST_RUN_STATES), state),
        )

    executors = raw.get("executors", [])
    _require(isinstance(executors, list), "%s.executors는 리스트여야 합니다." % task_id)
    normalized_executors = []
    for position, executor in enumerate(executors):
        _require(
            isinstance(executor, dict), "%s.executors[%d]는 object여야 합니다." % (task_id, position)
        )
        executor_id = executor.get("id")
        _require(
            isinstance(executor_id, str) and executor_id.strip(),
            "%s.executors[%d].id가 없습니다." % (task_id, position),
        )
        normalized_executors.append(
            {
                "id": executor_id,
                "run_command": _command(
                    executor.get("run_command"),
                    "%s.executors[%s].run_command" % (task_id, executor_id),
                ),
            }
        )

    lease = _lease(raw.get("lease"), "%s.lease" % task_id)

    # 재검증 축(제안서 §9.1) — 전부 optional이고 contract.lease 밖이라 scope hash 입력이 아니다.
    consumes_contracts = raw.get("consumes_contracts", [])
    _require(
        isinstance(consumes_contracts, list)
        and all(isinstance(item, str) and item.strip() for item in consumes_contracts),
        "%s.consumes_contracts는 비어 있지 않은 문자열의 리스트여야 합니다." % task_id,
    )
    produces_contract = raw.get("produces_contract")
    if produces_contract is not None:
        produces_contract = _contract_ref(
            produces_contract, "%s.produces_contract" % task_id
        )
    acceptance_scenarios = _check_entries(
        raw.get("acceptance_scenarios"), "%s.acceptance_scenarios" % task_id
    )
    contract_tests = _check_entries(
        raw.get("contract_tests"), "%s.contract_tests" % task_id
    )

    # pre_state가 candidate를 함의하면 그 candidate를 만든 runner attempt identity를
    # 공표한다 — 독립 검증(수용기준 9)은 verifier attempt가 이 값과 다름을 봐야 한다.
    runner_attempt_id = None
    attempts = []
    if state in POST_RUN_STATES:
        runner_attempt_id = declared_runner_attempt or "%s-runner-0" % task_id
        attempts.append(
            {
                "attempt_id": runner_attempt_id,
                "role": "runner",
                "executor_id": None,
                "created_at": None,
                "declared": True,
            }
        )

    return {
        "id": task_id,
        "capability": capability,
        # 실행 프로파일 — scope_hash 계산 입력이 아니다(아래 compute_scope_hash는 lease만 받는다).
        "profile": profile,
        "depends_on": list(depends_on),
        "state": state,
        # lease 선언에서 파생한 scope 식별자 — evidence 대조의 기준값이다.
        "scope_hash": compute_scope_hash(lease),
        # 이 태스크의 candidate를 만든 runner attempt. 선언되지 않은 상태면 None이고
        # 실제 dispatch 시점에 create_execution_packet()이 attempts[]를 채운다.
        "runner_attempt_id": runner_attempt_id,
        "contract": {
            "lease": lease,
            "run_command": _command(raw.get("run_command"), "%s.run_command" % task_id),
            "verify_command": _command(
                raw.get("verify_command"), "%s.verify_command" % task_id
            ),
            "executors": normalized_executors,
        },
        "attempts": attempts,
        "evidence": [],
        # 재검증 축 — scope_hash 계산 입력이 아니다(compute_scope_hash는 lease만 받는다).
        "consumes_contracts": list(consumes_contracts),
        "produces_contract": produces_contract,
        "acceptance_scenarios": acceptance_scenarios,
        "contract_tests": contract_tests,
    }


def _check_dependencies(mini_tasks):
    ids = {task["id"] for task in mini_tasks}
    for task in mini_tasks:
        for dependency in task["depends_on"]:
            _require(
                dependency in ids,
                "%s.depends_on의 %s가 미니 태스크 집합에 없습니다." % (task["id"], dependency),
            )
            _require(
                dependency != task["id"], "%s가 자기 자신에 의존합니다." % task["id"]
            )

    # DAG 확인 — 순환이 있으면 Supervisor가 영원히 ready를 못 만든다.
    pending = {task["id"]: set(task["depends_on"]) for task in mini_tasks}
    resolved = set()
    progressed = True
    while pending and progressed:
        progressed = False
        for task_id in list(pending):
            if pending[task_id] <= resolved:
                resolved.add(task_id)
                del pending[task_id]
                progressed = True
    _require(not pending, "의존 그래프에 순환이 있습니다: %s" % sorted(pending))


def build_workgraph(run_id, spec):
    """검증된 spec에서 `workgraph.json` 문서를 만든다(revision은 쓰기 시점에 1이 된다)."""
    mini_tasks = spec.get("mini_tasks")
    _require(
        isinstance(mini_tasks, list) and mini_tasks,
        "spec.mini_tasks는 비어 있지 않은 리스트여야 합니다.",
    )
    normalized = []
    known_ids = set()
    for index, raw in enumerate(mini_tasks):
        task = _mini_task(raw, index, known_ids)
        known_ids.add(task["id"])
        normalized.append(task)
    _check_dependencies(normalized)

    # 실행 계약 문서 지목 — run root 상대 경로 1개. 선언이 없으면 INTENT.md로 확정한다.
    # scope hash와 무관하다: compute_scope_hash는 lease 4축만 읽는다.
    execution_contract = spec.get("execution_contract", DEFAULT_EXECUTION_CONTRACT)
    _require(
        isinstance(execution_contract, str) and execution_contract.strip(),
        "spec.execution_contract는 비어 있지 않은 문자열이어야 합니다. 받은 값: %r"
        % (execution_contract,),
    )
    _require(
        not os.path.isabs(execution_contract),
        "spec.execution_contract는 run root 기준 상대 경로여야 합니다. 받은 값: %r"
        % (execution_contract,),
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "revision": 0,
        "run_id": run_id,
        "created_at": _now(),
        "updated_at": None,
        "budget": _budget(spec.get("budget")),
        "execution_contract": execution_contract,
        # 이 run이 추적하는 외부 계약 선언. 선언이 없으면 빈 배열이고 재검증 전파 대상이 없다.
        # scope hash와 무관하다: compute_scope_hash는 lease 4축만 읽는다.
        "contracts": _contracts(spec.get("contracts")),
        "mini_tasks": normalized,
    }


def build_acceptance(run_id, spec, mini_tasks):
    """완료조건·기여 태스크·증거 역인덱스 문서를 만든다.

    spec이 완료조건을 주지 않으면 미니 태스크 1개당 조건 1개로 유도한다 —
    "미니 태스크 accepted 전 독립 검증 증거 존재"(수용기준 9)를 걸 자리가 필요하다.
    """
    declared = spec.get("acceptance", [])
    _require(isinstance(declared, list), "spec.acceptance는 리스트여야 합니다.")
    known_ids = {task["id"] for task in mini_tasks}

    criteria = []
    if declared:
        for index, raw in enumerate(declared):
            _require(
                isinstance(raw, dict), "acceptance[%d]는 object여야 합니다." % index
            )
            criterion_id = raw.get("id")
            _require(
                isinstance(criterion_id, str) and criterion_id.strip(),
                "acceptance[%d].id가 없습니다." % index,
            )
            contributing = raw.get("contributing_tasks", raw.get("tasks", []))
            _require(
                isinstance(contributing, list)
                and all(item in known_ids for item in contributing),
                "acceptance[%s].contributing_tasks가 미니 태스크 집합 밖을 가리킵니다."
                % criterion_id,
            )
            criteria.append(
                {
                    "id": criterion_id,
                    "description": raw.get("description", ""),
                    "contributing_tasks": list(contributing),
                    "satisfied": False,
                    "evidence": [],
                }
            )
    else:
        for task in mini_tasks:
            criteria.append(
                {
                    "id": "ac-%s" % task["id"],
                    "description": "%s 미니 태스크 완료" % task["id"],
                    "contributing_tasks": [task["id"]],
                    "satisfied": False,
                    "evidence": [],
                }
            )

    return {
        "schema_version": SCHEMA_VERSION,
        "revision": 0,
        "run_id": run_id,
        "created_at": _now(),
        "updated_at": None,
        "criteria": criteria,
        # 증거 역인덱스: evidence_id → 기여한 완료조건·미니 태스크
        "evidence_index": {},
    }


# ─────────────────────────────────────────────────────────────────────────────
# Supervisor가 소비하는 공개 API
# ─────────────────────────────────────────────────────────────────────────────


def find_task(document, task_id):
    for task in document.get("mini_tasks", []):
        if task.get("id") == task_id:
            return task
    raise ControllerError("task_not_found", "받은 값: %s" % task_id)


def set_task_state(run_root, task_id, state, **fields):
    """미니 태스크 상태만 revision lock 아래 갱신한다.

    프로젝트 `state.json`은 건드리지 않는다 — P0~P5 전이는 Product Flow 소유다.
    """
    if state not in TASK_STATES:
        raise ControllerError("task_state_invalid", "받은 값: %r" % state)
    with workgraph_transaction(run_root) as document:
        task = find_task(document, task_id)
        task["state"] = state
        task.update(fields)
    return state


def debit_budget(run_root, role, amount=1):
    """프로젝트 예산을 차감한다. 한도가 선언돼 있으면 초과 시 거부한다."""
    if role not in ROLES:
        raise ControllerError("role_invalid", "받은 값: %r" % role)
    with workgraph_transaction(run_root) as document:
        _apply_debit(document, role, amount)
        return dict(document["budget"]["debited"])


def _apply_debit(document, role, amount):
    budget = document.setdefault(
        "budget",
        {"limits": {}, "debited": {"runner": 0, "executor": 0, "verifier": 0, "total": 0}},
    )
    limits = budget.get("limits", {})
    debited = budget.setdefault(
        "debited", {"runner": 0, "executor": 0, "verifier": 0, "total": 0}
    )
    projected_role = debited.get(role, 0) + amount
    projected_total = debited.get("total", 0) + amount

    role_cap = limits.get("max_%s_dispatches" % role)
    total_cap = limits.get("max_total_dispatches")
    if role_cap is not None and projected_role > role_cap:
        raise ControllerError(
            "budget_exhausted",
            "%s dispatch 예산 초과: %d > %d" % (role, projected_role, role_cap),
        )
    if total_cap is not None and projected_total > total_cap:
        raise ControllerError(
            "budget_exhausted",
            "전체 dispatch 예산 초과: %d > %d" % (projected_total, total_cap),
        )
    debited[role] = projected_role
    debited["total"] = projected_total
    return debited


def create_execution_packet(
    run_root, task_id, attempt_id, role="runner", executor_id=None, **extra
):
    """`attempts/<task>/<attempt>/execution-packet.json`을 쓰고 예산을 차감한다.

    workgraph의 불변 계약에서 dispatch 시점 가변 입력만 추려 packet으로 만든다.
    packet 생성과 예산 차감·attempt 기록은 하나의 revision lock 트랜잭션에서 끝난다.
    """
    if role not in ROLES:
        raise ControllerError("role_invalid", "받은 값: %r" % role)

    with workgraph_transaction(run_root) as document:
        task = find_task(document, task_id)
        contract = task.get("contract", {})
        if role == "verifier":
            command = contract.get("verify_command")
        elif role == "executor":
            command = next(
                (
                    executor.get("run_command")
                    for executor in contract.get("executors", [])
                    if executor.get("id") == executor_id
                ),
                None,
            )
        else:
            command = contract.get("run_command")

        _apply_debit(document, role, 1)

        packet = {
            "schema_version": SCHEMA_VERSION,
            "run_id": document.get("run_id"),
            "workgraph_revision": int(document.get("revision", 0)) + 1,
            "task_id": task_id,
            "attempt_id": attempt_id,
            "role": role,
            "executor_id": executor_id,
            "capability": task.get("capability"),
            "depends_on": list(task.get("depends_on", [])),
            "lease": contract.get("lease", {}),
            "command": command,
            "created_at": _now(),
        }
        packet.update(extra)

        if role == "runner":
            # 실제 dispatch도 같은 필드를 최신 runner attempt로 유지한다 —
            # load 시점 공표와 dispatch 시점 공표가 같은 의미를 갖게 한다.
            task["runner_attempt_id"] = attempt_id
        task.setdefault("attempts", []).append(
            {
                "attempt_id": attempt_id,
                "role": role,
                "executor_id": executor_id,
                "created_at": packet["created_at"],
            }
        )

        directory = attempt_dir(run_root, task_id, attempt_id)
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / PACKET_FILENAME
        _atomic_write_json(path, packet)

    return path, packet


def index_evidence(run_root, evidence_id, task_id, criteria=None, satisfied=False):
    """증거 역인덱스를 갱신한다 — evidence_id → 완료조건·기여 미니 태스크."""
    with acceptance_transaction(run_root) as document:
        targets = [
            criterion
            for criterion in document.get("criteria", [])
            if (criteria is None and task_id in criterion.get("contributing_tasks", []))
            or (criteria is not None and criterion.get("id") in criteria)
        ]
        for criterion in targets:
            if evidence_id not in criterion["evidence"]:
                criterion["evidence"].append(evidence_id)
            if satisfied:
                criterion["satisfied"] = True
        document.setdefault("evidence_index", {})[evidence_id] = {
            "task_id": task_id,
            "criteria": [criterion["id"] for criterion in targets],
        }
        return [criterion["id"] for criterion in targets]


# ─────────────────────────────────────────────────────────────────────────────
# 서브 명령 — `workgraph load` / `workgraph show`
# ─────────────────────────────────────────────────────────────────────────────


def _require_run_root(opts):
    raw = opts.get("run_root")
    if not raw:
        raise ControllerError("workgraph_missing", "--run-root는 필수입니다.", EXIT_USAGE)
    run_root = pathlib.Path(raw)
    if not run_root.is_dir():
        raise ControllerError("workgraph_missing", "run root 부재: %s" % raw)
    return run_root


def _load_spec(opts):
    raw = opts.get("spec")
    if not raw:
        raise ControllerError("spec_missing", exit_code=EXIT_USAGE)
    if not os.path.isabs(raw):
        raise ControllerError("spec_not_absolute", "받은 값: %s" % raw, EXIT_USAGE)
    path = pathlib.Path(raw)
    if not path.is_file():
        raise ControllerError("spec_not_found", "받은 값: %s" % raw)
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ControllerError("spec_not_json", "%s: %s" % (path, exc)) from exc
    if not isinstance(spec, dict):
        raise ControllerError("spec_invalid", "spec 최상위는 object여야 합니다.")
    return spec


def _run_id_of(run_root):
    """run root 경로 계약에서 run identity를 되읽는다(`run.json`이 있으면 그 값)."""
    manifest = pathlib.Path(run_root) / "run.json"
    if manifest.is_file():
        with contextlib.suppress(OSError, json.JSONDecodeError):
            return json.loads(manifest.read_text(encoding="utf-8")).get("run_id")
    return pathlib.Path(run_root).name


def cmd_load(opts):
    """spec에서 `workgraph.json`·`acceptance.json`을 초기 생성한다.

    이미 있는 run을 덮어쓰지 않는다 — OPPB run root는 재시작 가능성이 전제라
    load 재호출이 진행 중인 미니 태스크 상태를 0으로 되돌려서는 안 된다.
    """
    run_root = _require_run_root(opts)
    spec = _load_spec(opts)
    run_id = _run_id_of(run_root)

    document = build_workgraph(run_id, spec)
    acceptance = build_acceptance(run_id, spec, document["mini_tasks"])

    with _locked(run_root):
        if workgraph_path(run_root).is_file():
            raise ControllerError(
                "workgraph_exists", "받은 값: %s" % workgraph_path(run_root)
            )
        _write_document(workgraph_path(run_root), document, None)
        _write_document(acceptance_path(run_root), acceptance, None)

    return {
        "run_root": str(run_root),
        "run_id": run_id,
        "revision": document["revision"],
        "workgraph_path": str(workgraph_path(run_root)),
        "acceptance_path": str(acceptance_path(run_root)),
        "mini_task_count": len(document["mini_tasks"]),
        "mini_task_ids": [task["id"] for task in document["mini_tasks"]],
        "acceptance_criteria": len(acceptance["criteria"]),
        "budget": document["budget"],
    }


def cmd_show(opts):
    """현재 workgraph 요약 — 읽기 전용이며 revision을 전진시키지 않는다."""
    run_root = _require_run_root(opts)
    document = read_workgraph(run_root)
    return {
        "run_root": str(run_root),
        "run_id": document.get("run_id"),
        "revision": document.get("revision"),
        "budget": document.get("budget"),
        "mini_tasks": [
            {
                "id": task.get("id"),
                "state": task.get("state"),
                "depends_on": task.get("depends_on", []),
                "attempts": len(task.get("attempts", [])),
            }
            for task in document.get("mini_tasks", [])
        ],
    }


SUBCOMMAND_DISPATCH = {"load": cmd_load, "show": cmd_show}


def workgraph_command(opts):
    """`workgraph <subcommand>` 진입점. 진입점 모듈이 이 함수만 호출한다."""
    subcommand = opts.get("subcommand")
    handler = SUBCOMMAND_DISPATCH.get(subcommand)
    if handler is None:
        raise ControllerError(
            "unknown_subcommand",
            "지원 하위 명령: %s (받은 값: %r)" % (", ".join(SUBCOMMANDS), subcommand),
            EXIT_USAGE,
        )
    return handler(opts)
