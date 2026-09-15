"""
@header {
  "module": "lease",
  "task": "132",
  "layer": "util",
  "domain": "oppb-runtime",
  "description": "OPPB Scope Lease Tool — run root의 `leases.json`(소유권 lease 대장)의 유일한 writer다. 제안서 §P2.1 소유권 축 7종(tracked write·ephemeral write·contract·business rule·acceptance·runtime resource·global output)을 미니 태스크 spec에서 추출해 정규화하고, dispatch admission(`check-parallel`)에서 쌍별 교집합을 기계 판정해 하나라도 겹치면 dispatch **전에** 거부한다. `acquire`는 이미 active인 lease와의 교집합을 같은 판정으로 검사해 동일 대상의 동시 lease를 0으로 집행한다. `verifier-acquire`는 제안서 §4.5에 따라 candidate ID에 귀속된 검증 전용 runtime resource lease를 발급하며, 실행 중 Runner lease와 겹치는 자원이 하나라도 남으면 발급하지 않고 pending으로 둔다 — 겹친 채 검증을 시작하는 경로가 없다. scope hash와 lease 정규화는 재구현하지 않고 `controller.compute_scope_hash`·`controller.normalize_lease`를 호출한다(PLAN D2). `workgraph.json`·`acceptance.json`은 읽지도 쓰지도 않는다 — 단일 writer는 controller다. 원자 쓰기·파일 락도 controller가 이미 복제해 둔 형태(`ledger.py:336-377`)를 그대로 재사용한다. 표준 라이브러리만 사용하고 플랫폼 분기를 두지 않는다.",
  "exports": [
    "ERROR_CODES", "LeaseError", "OWNERSHIP_AXES", "SUBCOMMANDS",
    "leases_path", "read_leases", "extract_ownership", "lease_of_ownership",
    "conflict_axes", "unrepresented_global_outputs", "lease_command"
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
import socket
import uuid

import controller

SCHEMA_VERSION = "1.0"

LEASES_FILENAME = "leases.json"

EXIT_ERROR = 1
EXIT_USAGE = 2

SUBCOMMANDS = ("check-parallel", "acquire", "verifier-acquire", "release", "list")

# lease 상태 — active만 "점유 중"이다. pending은 자원 분리 실패로 시작하지 못한
# 검증 요청이고, released는 회수된 과거 기록이다.
LEASE_STATES = ("active", "pending", "released")

# 제안서 §P2.1 소유권 축. 이름은 단수형이며 `conflict_axes`·`checked_axes`
# 응답 필드가 이 어휘를 그대로 쓴다.
OWNERSHIP_AXES = (
    "tracked_write",
    "ephemeral_write",
    "contract",
    "business_rule",
    "acceptance",
    "runtime_resource",
    "global_output",
)

# 소유권 축 ← 미니 태스크 spec 필드 이름
SPEC_KEYS = {
    "tracked_write": "tracked_write_set",
    "ephemeral_write": "ephemeral_write_set",
    "contract": "contracts",
    "business_rule": "business_rules",
    "acceptance": "acceptance_ids",
    "runtime_resource": "runtime_resources",
    "global_output": "global_outputs",
}

# global output은 그 자체로 잠글 수 없다 — write set 또는 runtime resource로
# 반드시 다시 표현돼야 하며, 표현되지 않으면 dispatch 거부다(§P2.1).
GLOBAL_OUTPUT_CARRIER_AXES = ("tracked_write", "ephemeral_write", "runtime_resource")

# controller.LEASE_AXES(4축) ← 소유권 축. 기계적으로 lease를 발급하는 축만 대응한다.
LEASE_AXIS_OF = {
    "tracked_writes": "tracked_write",
    "ephemeral_writes": "ephemeral_write",
    "contracts": "contract",
    "runtime_resources": "runtime_resource",
}

# runtime resource 격리 정책. exclusive는 namespace로 쪼갤 수 없는 배타 자원이라
# Verifier 전용 사본을 만들 수 없다는 선언이다.
ISOLATION_NAMESPACED = "namespaced"
ISOLATION_EXCLUSIVE = "exclusive"

ERROR_CODES = {
    "LEASE_CONFLICT": "소유권 축 교집합이 있어 동시 lease를 발급하지 않습니다.",
    "RESOURCE_BUSY": (
        "실행 중 lease와 겹치지 않는 runtime resource를 확보할 수 없습니다."
    ),
    "OWNERSHIP_NOT_REPRESENTABLE": (
        "global output이 write set·runtime resource 어디에도 표현되지 않았습니다."
    ),
    "lease_spec_count": "--spec는 2개 이상 필요합니다.",
    "lease_store_corrupt": "leases.json을 읽을 수 없습니다.",
    "lease_not_found": "회수할 lease를 찾지 못했습니다.",
    "attempt_missing": "--attempt는 필수입니다.",
    "candidate_missing": "--candidate는 필수입니다.",
    "unknown_lease_subcommand": "알 수 없는 lease 하위 명령입니다.",
}


class LeaseError(controller.ControllerError):
    """lease 고유 실패. `ControllerError` 하위라 진입점의 단일 except로 잡힌다.

    `extra`는 응답 JSON에 그대로 병합된다 — admission 거부는 오류이면서 동시에
    판정 결과이므로 `conflict_axes` 같은 근거를 함께 싣는다.
    """


def _now():
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


# ─────────────────────────────────────────────────────────────────────────────
# leases.json — 이 모듈이 유일한 writer
#   락·원자 쓰기는 controller가 이미 복제해 둔 형태를 재사용한다. 같은 run root의
#   문서이므로 같은 락(`workgraph.lock`)으로 직렬화해 교차 갱신을 막는다.
# ─────────────────────────────────────────────────────────────────────────────


def leases_path(run_root):
    return pathlib.Path(run_root) / LEASES_FILENAME


def _empty_store(run_root):
    return {
        "schema_version": SCHEMA_VERSION,
        "run_root": str(run_root),
        "revision": 0,
        "leases": [],
    }


def read_leases(run_root):
    """현재 lease 대장. 부재는 오류가 아니라 빈 대장이다."""
    path = leases_path(run_root)
    if not path.is_file():
        return _empty_store(run_root)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LeaseError("lease_store_corrupt", "%s: %s" % (path, exc)) from exc
    if not isinstance(document, dict) or not isinstance(
        document.get("leases"), list
    ):
        raise LeaseError("lease_store_corrupt", "받은 값: %s" % path)
    return document


def _write_leases(run_root, document):
    document["revision"] = int(document.get("revision", 0)) + 1
    document["updated_at"] = _now()
    controller._atomic_write_json(leases_path(run_root), document)
    return document


def active_leases(document):
    return [
        lease for lease in document.get("leases", []) if lease.get("state") == "active"
    ]


# ─────────────────────────────────────────────────────────────────────────────
# 소유권 추출·정규화
# ─────────────────────────────────────────────────────────────────────────────


def _token(item):
    """소유권 원소를 비교 가능한 단일 문자열로 만든다.

    ephemeral write는 `{"path": ..., "policy": ...}` object로 선언되므로 경로만
    비교 대상이다 — 같은 경로를 서로 다른 policy로 선언해도 충돌은 충돌이다.
    """
    if isinstance(item, dict):
        for key in ("path", "id", "name", "resource"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return json.dumps(item, ensure_ascii=False, sort_keys=True)
    return str(item)


def extract_ownership(spec, label):
    """미니 태스크 spec에서 소유권 축 7종을 뽑아 정규형으로 만든다."""
    if not isinstance(spec, dict):
        raise controller.ControllerError(
            "spec_invalid", "%s: spec 최상위는 object여야 합니다." % label
        )
    ownership = {}
    for axis in OWNERSHIP_AXES:
        raw = spec.get(SPEC_KEYS[axis], [])
        if raw is None:
            raw = []
        if not isinstance(raw, list):
            raise controller.ControllerError(
                "spec_invalid",
                "%s.%s는 리스트여야 합니다." % (label, SPEC_KEYS[axis]),
            )
        ownership[axis] = sorted({_token(item) for item in raw})
    return ownership


def lease_of_ownership(ownership):
    """소유권 축 → `controller.LEASE_AXES` 4축 lease 선언.

    scope hash 계산 입력이다. 정규화·해시는 controller가 소유하므로 여기서
    다시 구현하지 않는다(PLAN D2).
    """
    return controller.normalize_lease(
        {
            lease_axis: ownership.get(axis, [])
            for lease_axis, axis in LEASE_AXIS_OF.items()
        }
    )


def unrepresented_global_outputs(ownership):
    """write set·runtime resource 어디에도 재표현되지 않은 global output."""
    carriers = set()
    for axis in GLOBAL_OUTPUT_CARRIER_AXES:
        carriers.update(ownership.get(axis, []))
    return [name for name in ownership.get("global_output", []) if name not in carriers]


def conflict_axes(left, right):
    """두 소유권 선언의 축별 교집합. 비어 있지 않은 축 이름을 순서대로 돌려준다.

    판정 알고리즘은 축별 집합 교집합 하나뿐이다 — 경로 접두사·정규식 같은
    추론을 넣지 않는다. 표현할 수 없는 소유권은 축에 올리지 못하므로 별도
    거부 경로(`OWNERSHIP_NOT_REPRESENTABLE`)로 빠진다(§P2.1).
    """
    axes = []
    for axis in OWNERSHIP_AXES:
        if set(left.get(axis, [])) & set(right.get(axis, [])):
            axes.append(axis)
    return axes


def _require_representable(ownership, task_id):
    unrepresented = unrepresented_global_outputs(ownership)
    if unrepresented:
        raise LeaseError(
            "OWNERSHIP_NOT_REPRESENTABLE",
            "%s의 global output이 재표현되지 않았습니다: %s"
            % (task_id, ", ".join(unrepresented)),
            EXIT_ERROR,
            parallel_eligible=False,
            task_id=task_id,
            unrepresented_global_outputs=unrepresented,
            checked_axes=list(OWNERSHIP_AXES),
            conflict_axes=[],
        )


# ─────────────────────────────────────────────────────────────────────────────
# runtime resource 격리 — Verifier 전용 lease (제안서 §4.5)
# ─────────────────────────────────────────────────────────────────────────────


def _free_port(excluded):
    """실제로 비어 있는 TCP 포트를 OS에서 받아온다 — 상상 값으로 쓰지 않는다."""
    for _ in range(64):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("127.0.0.1", 0))
            candidate = "port:%d" % probe.getsockname()[1]
        if candidate not in excluded:
            return candidate
    return None


def verifier_resources(ownership, isolation, candidate_id, held):
    """Runner와 겹치지 않는 검증 전용 runtime resource 집합.

    분리할 수 없으면 None을 돌려주고 호출자가 pending으로 둔다 — 겹친 채
    시작하는 경로는 없다(§4.5).
    """
    if isolation == ISOLATION_EXCLUSIVE:
        return None

    declared = ownership.get("runtime_resource", [])
    if not declared:
        # 선언된 자원이 없어도 Verifier는 자기 이름의 lease를 하나 쥔다 —
        # 검증 실행 자체가 run 안에서 식별 가능한 점유여야 한다.
        declared = ["verify"]

    allocated = []
    taken = set(held)
    for resource in declared:
        kind, sep, name = resource.partition(":")
        if sep and kind == "port":
            candidate = _free_port(taken)
        elif sep:
            candidate = "%s:%s@verify-%s" % (kind, name, candidate_id)
        else:
            candidate = "%s@verify-%s" % (resource, candidate_id)
        if candidate is None or candidate in taken:
            return None
        taken.add(candidate)
        allocated.append(candidate)
    return sorted(set(allocated))


# ─────────────────────────────────────────────────────────────────────────────
# 입력
# ─────────────────────────────────────────────────────────────────────────────


def _require_run_root(opts):
    raw = opts.get("run_root")
    if not raw:
        raise controller.ControllerError(
            "run_root_missing", "--run-root는 필수입니다.", EXIT_USAGE
        )
    if not os.path.isabs(raw):
        raise controller.ControllerError(
            "run_root_not_absolute", "받은 값: %s" % raw, EXIT_USAGE
        )
    run_root = pathlib.Path(raw)
    if not run_root.is_dir():
        raise controller.ControllerError("run_root_not_found", "받은 값: %s" % raw)
    return run_root


def _spec_paths(opts):
    """`--spec`는 반복 가능하다 — 진입점 파서가 모은 순서를 그대로 쓴다."""
    values = opts.get("_values", {}).get("spec")
    if values:
        return list(values)
    single = opts.get("spec")
    return [single] if single else []


def _read_spec(raw):
    if not raw:
        raise controller.ControllerError("spec_missing", exit_code=EXIT_USAGE)
    if not os.path.isabs(raw):
        raise controller.ControllerError(
            "spec_not_absolute", "받은 값: %s" % raw, EXIT_USAGE
        )
    path = pathlib.Path(raw)
    if not path.is_file():
        raise controller.ControllerError("spec_not_found", "받은 값: %s" % raw)
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise controller.ControllerError(
            "spec_not_json", "%s: %s" % (path, exc)
        ) from exc
    if not isinstance(spec, dict):
        raise controller.ControllerError(
            "spec_invalid", "%s: spec 최상위는 object여야 합니다." % path
        )
    return spec


def _task_id_of(spec, fallback):
    value = spec.get("task_id")
    return value if isinstance(value, str) and value.strip() else fallback


def _isolation_of(spec):
    value = spec.get("runtime_resource_isolation", ISOLATION_NAMESPACED)
    return value if value in (ISOLATION_NAMESPACED, ISOLATION_EXCLUSIVE) else (
        ISOLATION_NAMESPACED
    )


def _describe(spec, path):
    """spec 1개를 판정 입력으로 정규화한다."""
    task_id = _task_id_of(spec, pathlib.Path(path).stem)
    ownership = extract_ownership(spec, task_id)
    lease = lease_of_ownership(ownership)
    return {
        "task_id": task_id,
        "capability_id": spec.get("capability_id"),
        "spec_path": str(path),
        "ownership": ownership,
        "lease": lease,
        # scope hash는 lease를 소유한 Controller만 계산한다(PLAN D2).
        "scope_hash": controller.compute_scope_hash(lease),
        "isolation": _isolation_of(spec),
    }


def _ownership_public(ownership):
    return {axis: list(ownership.get(axis, [])) for axis in OWNERSHIP_AXES}


# ─────────────────────────────────────────────────────────────────────────────
# 서브 명령
# ─────────────────────────────────────────────────────────────────────────────


def cmd_check_parallel(opts):
    """dispatch admission — 쌍별 소유권 교집합을 dispatch **전에** 판정한다."""
    run_root = _require_run_root(opts)
    paths = _spec_paths(opts)
    if len(paths) < 2:
        raise LeaseError(
            "lease_spec_count", "받은 개수: %d" % len(paths), EXIT_USAGE
        )

    described = [_describe(_read_spec(path), path) for path in paths]
    for entry in described:
        _require_representable(entry["ownership"], entry["task_id"])

    for index, left in enumerate(described):
        for right in described[index + 1 :]:
            axes = conflict_axes(left["ownership"], right["ownership"])
            if axes:
                raise LeaseError(
                    "LEASE_CONFLICT",
                    "%s ↔ %s 소유권 교집합: %s"
                    % (left["task_id"], right["task_id"], ", ".join(axes)),
                    EXIT_ERROR,
                    parallel_eligible=False,
                    conflict_axes=axes,
                    checked_axes=list(OWNERSHIP_AXES),
                    conflicting_task_ids=[left["task_id"], right["task_id"]],
                )

    return {
        "run_root": str(run_root),
        "parallel_eligible": True,
        "conflict_axes": [],
        "checked_axes": list(OWNERSHIP_AXES),
        "task_ids": [entry["task_id"] for entry in described],
        "scope_hashes": {
            entry["task_id"]: entry["scope_hash"] for entry in described
        },
        "pairs_checked": len(described) * (len(described) - 1) // 2,
    }


def cmd_acquire(opts):
    """Runner lease 발급 — active lease와 한 축이라도 겹치면 발급하지 않는다."""
    run_root = _require_run_root(opts)
    paths = _spec_paths(opts)
    attempt_id = opts.get("attempt")
    if not attempt_id:
        raise LeaseError("attempt_missing", exit_code=EXIT_USAGE)

    entry = _describe(_read_spec(paths[0] if paths else None), paths[0] if paths else "")
    _require_representable(entry["ownership"], entry["task_id"])

    with controller._locked(run_root):
        document = read_leases(run_root)
        for held in active_leases(document):
            axes = conflict_axes(entry["ownership"], held.get("ownership", {}))
            if axes:
                raise LeaseError(
                    "LEASE_CONFLICT",
                    "%s는 active lease %s와 겹칩니다: %s"
                    % (entry["task_id"], held.get("lease_id"), ", ".join(axes)),
                    EXIT_ERROR,
                    conflict_axes=axes,
                    checked_axes=list(OWNERSHIP_AXES),
                    held_lease_id=held.get("lease_id"),
                    held_task_id=held.get("task_id"),
                )
        record = {
            "lease_id": "lease-%s" % uuid.uuid4().hex[:12],
            "run_root": str(run_root),
            "role": "runner",
            "state": "active",
            "task_id": entry["task_id"],
            "capability_id": entry["capability_id"],
            "attempt_id": attempt_id,
            "scope_hash": entry["scope_hash"],
            "lease": entry["lease"],
            "ownership": _ownership_public(entry["ownership"]),
            "runtime_resources": list(entry["ownership"]["runtime_resource"]),
            "isolation": entry["isolation"],
            "acquired_at": _now(),
        }
        document.setdefault("leases", []).append(record)
        _write_leases(run_root, document)

    return dict(record)


def cmd_verifier_acquire(opts):
    """Verifier 전용 runtime resource lease — candidate ID에 귀속된다(§4.5).

    실행 중 Runner lease와 겹치지 않는 자원을 확보하지 못하면 발급하지 않고
    pending으로 기록한다. 겹친 채 검증을 시작하는 경로는 없다.
    """
    run_root = _require_run_root(opts)
    paths = _spec_paths(opts)
    candidate_id = opts.get("candidate")
    if not candidate_id:
        raise LeaseError("candidate_missing", exit_code=EXIT_USAGE)

    entry = _describe(_read_spec(paths[0] if paths else None), paths[0] if paths else "")

    with controller._locked(run_root):
        document = read_leases(run_root)
        held = set()
        for lease in active_leases(document):
            held.update(lease.get("runtime_resources", []))

        allocated = verifier_resources(
            entry["ownership"], entry["isolation"], candidate_id, held
        )
        if allocated is None or set(allocated) & held:
            record = {
                "lease_id": "lease-%s" % uuid.uuid4().hex[:12],
                "run_root": str(run_root),
                "role": "verifier",
                "state": "pending",
                "task_id": entry["task_id"],
                "candidate_id": candidate_id,
                "runtime_resources": [],
                "requested_runtime_resources": list(
                    entry["ownership"]["runtime_resource"]
                ),
                "isolation": entry["isolation"],
                "requested_at": _now(),
            }
            document.setdefault("leases", []).append(record)
            _write_leases(run_root, document)
            raise LeaseError(
                "RESOURCE_BUSY",
                "candidate %s의 검증 전용 runtime resource를 분리할 수 없습니다."
                % candidate_id,
                EXIT_ERROR,
                state="pending",
                lease_id=record["lease_id"],
                role="verifier",
                candidate_id=candidate_id,
                task_id=entry["task_id"],
                blocked_by=sorted(held),
                isolation=entry["isolation"],
            )

        verifier_lease = controller.normalize_lease(
            {"runtime_resources": allocated}
        )
        record = {
            "lease_id": "lease-%s" % uuid.uuid4().hex[:12],
            "run_root": str(run_root),
            "role": "verifier",
            "state": "active",
            "task_id": entry["task_id"],
            "candidate_id": candidate_id,
            "scope_hash": controller.compute_scope_hash(verifier_lease),
            "lease": verifier_lease,
            "runtime_resources": allocated,
            "runner_runtime_resources": sorted(held),
            "isolation": entry["isolation"],
            "acquired_at": _now(),
        }
        document.setdefault("leases", []).append(record)
        _write_leases(run_root, document)

    return dict(record)


def cmd_release(opts):
    """lease 회수 — attempt·candidate·task 단위로 active lease를 released로 닫는다."""
    run_root = _require_run_root(opts)
    attempt_id = opts.get("attempt")
    candidate_id = opts.get("candidate")
    task_id = opts.get("task_id")
    if not (attempt_id or candidate_id or task_id):
        raise LeaseError(
            "lease_not_found",
            "--attempt·--candidate·--task-id 중 하나는 필요합니다.",
            EXIT_USAGE,
        )

    released = []
    with controller._locked(run_root):
        document = read_leases(run_root)
        for lease in document.get("leases", []):
            if lease.get("state") != "active":
                continue
            if attempt_id and lease.get("attempt_id") != attempt_id:
                continue
            if candidate_id and lease.get("candidate_id") != candidate_id:
                continue
            if task_id and lease.get("task_id") != task_id:
                continue
            lease["state"] = "released"
            lease["released_at"] = _now()
            released.append(lease.get("lease_id"))
        if not released:
            raise LeaseError(
                "lease_not_found",
                "attempt=%r candidate=%r task=%r" % (attempt_id, candidate_id, task_id),
            )
        _write_leases(run_root, document)

    return {
        "run_root": str(run_root),
        "released": released,
        "released_count": len(released),
    }


def cmd_list(opts):
    """lease 대장 관측 — 부작용이 없고 revision을 전진시키지 않는다."""
    run_root = _require_run_root(opts)
    document = read_leases(run_root)
    leases = document.get("leases", [])
    return {
        "run_root": str(run_root),
        "revision": document.get("revision"),
        "leases": leases,
        "active_count": len(active_leases(document)),
        "lease_count": len(leases),
    }


SUBCOMMAND_DISPATCH = {
    "check-parallel": cmd_check_parallel,
    "acquire": cmd_acquire,
    "verifier-acquire": cmd_verifier_acquire,
    "release": cmd_release,
    "list": cmd_list,
}


def lease_command(opts):
    """`lease <subcommand>` 진입점. 진입점 모듈이 이 함수만 호출한다."""
    subcommand = opts.get("subcommand")
    handler = SUBCOMMAND_DISPATCH.get(subcommand)
    if handler is None:
        raise LeaseError(
            "unknown_lease_subcommand",
            "지원 하위 명령: %s (받은 값: %r)" % (", ".join(SUBCOMMANDS), subcommand),
            EXIT_USAGE,
        )
    return handler(opts)
