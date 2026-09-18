"""
@header {
  "module": "orchestrator",
  "layer": "util",
  "domain": "opal-tools",
  "description": "T03 run 수명주기 — created→context_resolved→ports_leased→(sut_starting→sut_ready)→최종 상태→cleanup_* 상태 머신을 돌리고 run.json(§A.1)·journal.json(§A.2)·owned.json(§A.3)을 $OPAL_E2E_ARTIFACT_DIR에만 기록한다. 상태·exit·error 문자열은 전부 lib.e2e_contract의 상수·함수에서 끌어오며 리터럴로 만들지 않는다(CONTRACT.md 계약 규칙 C-125-1, TRD.md RK-8).",
  "exports": ["RUN_ID_PATTERN", "run_e2e"]
}

lib.e2e.orchestrator — 1회 실행이며 재시도 루프를 내장하지 않는다(CONTRACT.md §B.1.1
[MUST], test_tool.py 모듈 계약). 저장소에는 아무것도 쓰지 않는다(TASK.md C-5). 프로세스
회수는 lib/e2e/process.py의 pgid 단위 경로만 쓰고 이름 패턴 매칭을 쓰지 않는다(C-9, §C.1).
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib import e2e_contract
from lib.e2e import drivers as e2e_drivers
from lib.e2e import evidence as e2e_evidence
from lib.e2e import executors as e2e_executors
from lib.e2e import ports as e2e_ports
from lib.e2e import process as e2e_process
from lib.e2e import runtime as e2e_runtime
from lib.e2e import scenario_adapter as e2e_scenario_adapter
from lib.e2e import target as e2e_target

SCHEMA_VERSION = e2e_contract.E2E_CONTRACT_SCHEMA_VERSION

# CONTRACT.md §A.0 run_id 형식.
RUN_ID_PATTERN = re.compile(r"^e2e-\d{8}-\d{3}$")

# 계약 규칙 C-125-1 — 상태 문자열을 리터럴로 작성하지 않는다. e2e_contract가 소유한
# 튜플에서 조회해 가져오며, 계약에서 해당 상태가 사라지면 import 시점에 KeyError로
# 즉시 드러난다(조용한 문자열 드리프트를 막는 것이 이 조회의 목적이다).
_FINAL = {name: name for name in e2e_contract.FINAL_STATUSES}
_OPERATIONAL = {name: name for name in e2e_contract.OPERATIONAL_STATUSES}
STATUS_BLOCKED = _FINAL["blocked"]
STATUS_INFRA_ERROR = _FINAL["infra_error"]
STATUS_EXECUTOR_UNAVAILABLE = _FINAL["executor_unavailable"]

# CONTRACT.md §A.2.1 상태 enum. 이 값들은 e2e_contract가 소유한 status·exit·error가
# 아니라 하네스 내부 수명주기 상태이며, 본 모듈이 소유한다.
STATE_CREATED = "created"
STATE_CONTEXT_RESOLVED = "context_resolved"
STATE_PORTS_LEASED = "ports_leased"
STATE_SUT_STARTING = "sut_starting"
STATE_SUT_READY = "sut_ready"
STATE_PROFILE_RESOLVED = "profile_resolved"
STATE_EXECUTOR_READY = "executor_ready"
STATE_SCENARIO_RUNNING = "scenario_running"
STATE_EVIDENCE_CAPTURED = "evidence_captured"
STATE_CLEANUP_COMPLETE = "cleanup_complete"
STATE_CLEANUP_WARNING = "cleanup_warning"

# CONTRACT.md §A.1 cleanup enum.
CLEANUP_COMPLETE = "complete"
CLEANUP_WARNING = "warning"

# CONTRACT.md §A.1.2 candidates[].outcome enum.
_OUTCOME_SELECTED = "selected"
_OUTCOME_PROVIDER_UNAVAILABLE = "provider_unavailable"

_EXECUTOR_BROWSER = "browser"
_EXECUTOR_HUMAN = "human"

# §A.8 [MUST] probe는 **실행 근거로만** 가용성을 판정한다. `api` executor의 probe는 실제
# SUT의 `/health`를 호출하므로(`executors/api.py` `op_probe`) SUT가 먼저 떠 있어야 한다.
# `browser`·`human` probe는 SUT URL을 참조하지 않으므로(binary 해석·artifact 디렉터리만
# 본다) 기동 전에 판정할 수 있다. 이 목록이 "후보 해석을 SUT 앞에 둘 수 있는가"의 유일한
# 분기 근거이며, 두 경로가 섞이지 않게 여기 한 곳에서만 결정한다.
_SUT_DEPENDENT_EXECUTOR_TYPES = ("api",)

_ROLE_BACKEND = "backend"
_ROLE_FRONTEND = "frontend"
_DEFAULT_ARTIFACT_DIRNAME = "opal-e2e-runs"
_SCENARIO_FILENAME = "test-scenario.json"

# CONTRACT.md §A.1 `fidelity` enum. 값은 scenario.py의 FIDELITY_ORDER가 소유하며 여기서는
# **달성한** 충실도만 고른다 — 시나리오의 required_fidelity를 결과로 베껴 쓰지 않는다.
FIDELITY_MOCK = "mock"
FIDELITY_REAL_HTTP = "real-http"
FIDELITY_REAL_USAGE = "real-usage"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class _Journal:
    """§A.2 상태 전이 이력. 최초 전이의 `from`은 null이다."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.transitions: List[Dict[str, Any]] = []
        self._current: Optional[str] = None

    def to(self, state: str, detail: Optional[dict] = None) -> None:
        entry: Dict[str, Any] = {"from": self._current, "to": state, "at": _now_iso()}
        if detail:
            entry["detail"] = detail
        self.transitions.append(entry)
        self._current = state

    @property
    def state(self) -> str:
        return self._current or STATE_CREATED

    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "transitions": self.transitions,
            "resume": None,
        }


def _pid_run_id() -> str:
    return f"e2e-{datetime.now().strftime('%Y%m%d')}-{os.getpid() % 1000:03d}"


def _resolve_artifact_layout(
    *,
    artifact_root_arg: Optional[str],
    run_id_arg: Optional[str],
    project_id: str,
) -> tuple:
    """`(artifact_root, artifact_dir, run_id)`를 해석한다 (TRD.md TD-10).

    `$OPAL_E2E_ARTIFACT_DIR`가 주어지면 그것이 곧 run 디렉터리이며 lease 루트도 같은
    곳에 둔다 — 호출자가 격리 경로 하나만 넘겨도 산출물과 lease가 함께 격리된다.
    그렇지 않으면 `{artifact_root}/{project_id}/{run_id}/`를 만든다.
    """
    env_dir = os.environ.get("OPAL_E2E_ARTIFACT_DIR")
    env_root = os.environ.get("OPAL_E2E_ARTIFACT_ROOT")

    if env_dir:
        artifact_dir = os.path.abspath(env_dir)
        Path(artifact_dir).mkdir(parents=True, exist_ok=True)
        artifact_root = os.path.abspath(artifact_root_arg or env_root or artifact_dir)
        return (artifact_root, artifact_dir, run_id_arg or _pid_run_id())

    artifact_root = os.path.abspath(
        artifact_root_arg or env_root or str(e2e_process.temp_root() / _DEFAULT_ARTIFACT_DIRNAME)
    )
    base = Path(artifact_root) / project_id
    base.mkdir(parents=True, exist_ok=True)

    if run_id_arg:
        run_dir = base / run_id_arg
        run_dir.mkdir(parents=True, exist_ok=True)
        return (artifact_root, str(run_dir), run_id_arg)

    # 동시 run이 같은 run_id를 잡지 않도록 mkdir의 원자성으로 순번을 확정한다.
    stamp = datetime.now().strftime("%Y%m%d")
    for ordinal in range(1, 1000):
        candidate = f"e2e-{stamp}-{ordinal:03d}"
        run_dir = base / candidate
        try:
            run_dir.mkdir()
        except FileExistsError:
            continue
        return (artifact_root, str(run_dir), candidate)
    raise e2e_ports.PortLeaseError(
        "e2e_run_id_exhausted", "no free run_id ordinal remains for today under this project"
    )


def _metadata_names(required_evidence: List[str]) -> set:
    """`metadata` 증적을 시나리오가 쓴 표기로 되돌린다(§A.1 `observed_evidence`)."""
    names = {"metadata"}
    for item in required_evidence:
        if e2e_evidence.canonical_kind(item) == "metadata":
            names.add(str(item))
    return names


def _emit_server_log(writer: e2e_evidence.EvidenceWriter, handles: List[e2e_runtime.SutHandle]) -> None:
    """SUT stdout 로그를 마스킹본으로 봉인한다(§A.12 단일 관문).

    실행 중 프로세스의 stdout은 관문을 통과시킬 수 없으므로, 회수 직후 같은 경로를
    마스킹본으로 교체해 **디스크에 남는 증적**이 반드시 관문을 거치게 한다. SUT를 아예
    기동하지 않은 run은 서버 로그가 존재하지 않는다는 사실 자체를 기록하되 관측 증적으로
    올리지 않는다.
    """
    sealed = False
    for handle in handles:
        for path in (handle.log_paths or {}).values():
            if writer.seal_server_log(str(path)) is not None:
                sealed = True
    if sealed:
        return
    writer.write_text(
        e2e_evidence.EVIDENCE_PATHS["server_log"],
        "# no SUT server was started for this run — server log was not produced\n",
        kind="server_log",
        observed=False,
    )


def _load_scenario(task_path: str, scenario_id: str) -> tuple:
    """`(scenario, detail_code, detail, contract_check)` — 해석 실패 시 scenario가 None.

    두 인자는 §B.1.1의 필수 인자이므로 argparse가 이미 존재를 보장한다.

    §C.4 집행 1(실행 전 정적 거부)은 **spec 전체 검증보다 먼저** 대상 시나리오에만
    적용한다. 순서가 반대이면 executor contract mismatch가 spec 전체 무효화로 흡수돼
    (`scenario_contract_invalid` → `blocked`) "browser profile에 browser step이 없다"는
    구체적 거부 사유가 기록에서 사라진다 — S-12(b)가 요구하는 것은 바로 그 사유다.
    `contract_check`는 계약 함수가 돌려준 결과 객체 그대로이며 호출자가 `status`·`error`를
    거기서 꺼내 쓴다(C-125-1).
    """
    spec_path = Path(task_path) / _SCENARIO_FILENAME
    if not spec_path.is_file():
        return (None, "e2e_scenario_not_found", f"{_SCENARIO_FILENAME} not found under --task-path", None)
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (None, "e2e_scenario_not_found", f"cannot read {_SCENARIO_FILENAME}: {exc}", None)

    raw_scenarios = spec.get("scenarios")
    if isinstance(raw_scenarios, list):
        for item in raw_scenarios:
            if not isinstance(item, dict) or str(item.get("id")) != str(scenario_id):
                continue
            check = e2e_scenario_adapter.static_executor_contract_error(item)
            if check is not None:
                # 거부된 시나리오도 run.json에 profile·surface_kind·required_evidence를
                # 남긴다 — "무엇이 무엇과 어긋났는가"가 기록에 없으면 이 거부는 감사할
                # 수 없다. 실행은 하지 않으므로 증적은 전부 missing으로 남는다.
                return (
                    dict(item),
                    "e2e_executor_contract_mismatch",
                    f"{scenario_id}: {check.get('detail')}",
                    check,
                )
            break

    # C-125-2 — schema_version이 "2.0"이 아닌 spec은 실행 대상으로 받지 않는다.
    validated = e2e_contract.validate_scenario_contract(spec, legacy_defaults=False)
    if not validated["ok"]:
        return (None, "e2e_scenario_contract_invalid", str(validated.get("detail")), None)
    for item in validated["normalized"].get("scenarios") or []:
        if str(item.get("id")) == str(scenario_id):
            return (item, None, None, None)
    return (None, "e2e_scenario_not_found", f"scenario {scenario_id!r} is not in {_SCENARIO_FILENAME}", None)


def run_e2e(
    *,
    target: str,
    scenario_id: str,
    task_path: str,
    worktree_root: Optional[str] = None,
    opal_home: Optional[str] = None,
    artifact_root: Optional[str] = None,
    run_id: Optional[str] = None,
) -> dict:
    """`test-tool e2e run` 1회 실행. stdout에 실을 payload를 반환한다(§B.1.1).

    exit code는 payload["exit_code"]이며 `status_to_exit()` 결과 그대로다 — 이 모듈은
    exit 정수를 직접 배정하지 않는다.

    증적 마스킹·저장 실패(`EvidenceError`)와 산출물 경로 자체의 I/O 실패(`OSError`)는
    여기서 붙잡아 **원문·부분 증적을 지우고** `infra_error`로 끝낸다(TASK.md C-6,
    CONTRACT.md §A.12 [MUST]). 다음 후보로 전환하지 않는다(§C.7).
    """
    state: Dict[str, Any] = {"artifact_dir": "", "artifact_root": "", "run_id": "", "writer": None}
    try:
        return _run_e2e(
            state=state,
            target=target,
            scenario_id=scenario_id,
            task_path=task_path,
            worktree_root=worktree_root,
            opal_home=opal_home,
            artifact_root=artifact_root,
            run_id=run_id,
        )
    except (e2e_evidence.EvidenceError, OSError) as exc:
        return _evidence_failure_payload(state, scenario_id=scenario_id, exc=exc)


def _evidence_failure_payload(state: Dict[str, Any], *, scenario_id: Optional[str], exc: Exception) -> dict:
    """증적 저장 실패 경로의 최종 payload. 디스크에 아무것도 남기지 않는다.

    stdout 필드 집합은 정상 경로와 동일하게 유지한다 — §B.1.1 밖의 진단 키를 이 경로에만
    덧붙이면 소비자가 두 가지 stdout 모양을 다뤄야 한다. 원인은 stderr로 보내지 않고
    `error`/`status`로만 알린다(NR-1: 새 status·exit 값을 만들지 않는다).
    """
    writer = state.get("writer")
    if isinstance(writer, e2e_evidence.EvidenceWriter):
        writer.purge()
    status = STATUS_INFRA_ERROR
    return {
        "run_id": state.get("run_id") or "",
        "scenario_id": scenario_id,
        "profile": None,
        "status": status,
        "operational_status": _OPERATIONAL.get(status),
        "error": e2e_contract.status_to_error(status),
        "exit_code": e2e_contract.status_to_exit(status),
        # 증적을 남기지 못했으므로 run.json 경로를 약속하지 않는다.
        "run_json_path": None,
        "artifact_dir": state.get("artifact_dir") or "",
        "executed": False,
        "urls": {"frontend": None, "backend": None},
        "project_root": None,
        "lease_reclaimed": [],
        "candidates": [],
    }


def _run_e2e(
    *,
    state: Dict[str, Any],
    target: str,
    scenario_id: str,
    task_path: str,
    worktree_root: Optional[str] = None,
    opal_home: Optional[str] = None,
    artifact_root: Optional[str] = None,
    run_id: Optional[str] = None,
) -> dict:
    started_at = _now_iso()
    detail_code: Optional[str] = None
    detail: Optional[str] = None
    status = STATUS_BLOCKED

    # ── created ──────────────────────────────────────────────────────────────
    context: Optional[e2e_target.TargetContext] = None
    try:
        context = e2e_target.resolve_target(
            target,
            worktree_root=worktree_root,
            opal_home=opal_home,
        )
        project_id = e2e_target.project_id_for(context.project_root)
    except e2e_target.TargetResolutionError as exc:
        detail_code, detail = exc.detail_code, exc.detail
        project_id = "unresolved"

    resolved_root, artifact_dir, resolved_run_id = _resolve_artifact_layout(
        artifact_root_arg=artifact_root,
        run_id_arg=run_id,
        project_id=project_id,
    )
    # 증적 단일 관문(§A.12). 이 시점 이후의 모든 파일 쓰기는 writer를 통과한다.
    writer = e2e_evidence.EvidenceWriter(artifact_dir, resolved_run_id)
    state["artifact_dir"] = artifact_dir
    state["artifact_root"] = resolved_root
    state["run_id"] = resolved_run_id
    state["writer"] = writer

    journal = _Journal(resolved_run_id)
    journal.to(STATE_CREATED)

    if context is None:
        # 대상 소스를 해석하지 못하면 포트를 임대하지 않는다 — 입력 오류로 차단한다.
        return _finalize(
            status=STATUS_BLOCKED,
            journal=journal,
            writer=writer,
            context=None,
            leases=[],
            reclaimed=[],
            handles=[],
            artifact_root=resolved_root,
            artifact_dir=artifact_dir,
            run_id=resolved_run_id,
            scenario_id=scenario_id,
            started_at=started_at,
            detail_code=detail_code,
            detail=detail,
        )

    journal.to(STATE_CONTEXT_RESOLVED, {"target": context.target, "commit": context.commit})

    # ── ports_leased ─────────────────────────────────────────────────────────
    leases: List[e2e_ports.LeaseRecord] = []
    reclaimed: List[str] = []
    try:
        leases, reclaimed = e2e_ports.lease_ports(
            artifact_root=resolved_root,
            run_id=resolved_run_id,
            roles=(_ROLE_BACKEND, _ROLE_FRONTEND),
        )
    except e2e_ports.PortLeaseError as exc:
        journal.to(STATUS_INFRA_ERROR, {"detail_code": exc.detail_code})
        return _finalize(
            status=STATUS_INFRA_ERROR,
            journal=journal,
            writer=writer,
            context=context,
            leases=[],
            reclaimed=reclaimed,
            handles=[],
            artifact_root=resolved_root,
            artifact_dir=artifact_dir,
            run_id=resolved_run_id,
            scenario_id=scenario_id,
            started_at=started_at,
            detail_code=exc.detail_code,
            detail=exc.detail,
        )

    journal.to(
        STATE_PORTS_LEASED,
        {"leases": [rec.lease_id for rec in leases], "reclaimed": reclaimed},
    )

    # ── 시나리오 해석 ────────────────────────────────────────────────────────
    scenario, detail_code, detail, contract_check = _load_scenario(task_path, scenario_id)
    if contract_check is not None:
        # §C.4 집행 1 — 실행 전 정적 거부. SUT를 기동하지 않고 끝내며 `executed=false`로
        # "실행 중 실패가 아니라 실행 자체를 하지 않았다"를 기록에 남긴다(S-12(b), TD-17).
        # status·error는 계약 함수가 돌려준 값 그대로다(C-125-1).
        journal.to(str(contract_check.get("status")), {"detail_code": detail_code})
        return _finalize(
            status=str(contract_check.get("status")),
            error_override=contract_check.get("error"),
            executed=False,
            journal=journal,
            writer=writer,
            context=context,
            leases=leases,
            reclaimed=reclaimed,
            handles=[],
            artifact_root=resolved_root,
            artifact_dir=artifact_dir,
            run_id=resolved_run_id,
            scenario_id=scenario_id,
            scenario=scenario,
            started_at=started_at,
            detail_code=detail_code,
            detail=detail,
        )
    if scenario is None:
        # 시나리오를 읽지 못하면 외부 조건 차단으로 끝낸다. 인자 누락 자체는 여기까지
        # 오지 않는다 — --scenario·--task-path는 argparse 층에서 필수다(§B.1.1).
        journal.to(STATUS_BLOCKED, {"detail_code": detail_code})
        return _finalize(
            status=STATUS_BLOCKED,
            journal=journal,
            writer=writer,
            context=context,
            leases=leases,
            reclaimed=reclaimed,
            handles=[],
            artifact_root=resolved_root,
            artifact_dir=artifact_dir,
            run_id=resolved_run_id,
            scenario_id=scenario_id,
            started_at=started_at,
            detail_code=detail_code,
            detail=detail,
        )

    # ── executor 후보 해석 ───────────────────────────────────────────────────
    # 후보 해석을 SUT 기동 **앞**에 둘 수 있는지는 probe가 SUT를 필요로 하는지에 달렸다
    # (`_SUT_DEPENDENT_EXECUTOR_TYPES`). 앞에 둘 수 있으면 아무도 구동하지 않을
    # uvicorn·vite를 띄우지 않는다 — §A.1.2 [MUST]가 "`selected`가 0개이면
    # `executor_unavailable`"로 결론을 이미 고정하므로 기동 전에 판정이 끝난다(C-5:
    # 기동은 순수 부수효과). 앞에 둘 수 없으면(§A.8이 실행 근거를 요구하므로) 기동 후에
    # 해석하고, 그때도 §A.2.1 전이 순서는 그대로 지킨다.
    required_types = _required_executor_types(scenario)
    needs_sut_for_probe = any(item in _SUT_DEPENDENT_EXECUTOR_TYPES for item in required_types)

    candidates: List[Dict[str, Any]] = []
    probes: List[Dict[str, Any]] = []
    handles: List[e2e_runtime.SutHandle] = []
    # 후보 해석이 만든 driver 인스턴스를 step 실행까지 이어 쓴다 — 재생성은 같은 연산의
    # 두 번째 호출이 되고, 그것은 §C.7·S-27이 금지하는 재시도다.
    driver_cache = _DriverCache()
    # §A.4 `actions.jsonl`은 run 전체가 하나의 로그를 공유한다 — driver와 api executor가
    # 각자 적어도 `seq`가 한 줄기로 이어져야 §A.11 상호참조가 성립한다.
    action_log = e2e_executors.ActionLog()

    if not needs_sut_for_probe:
        candidates, probes = _resolve_executor_candidates(
            scenario,
            runtime_context=_executor_runtime_context(
                artifact_dir, task_path, writer,
                action_log=action_log, run_id=resolved_run_id,
            ),
            driver_cache=driver_cache,
        )
        # §A.8 [MUST] — 가용성 판정 근거는 probe 결과뿐이다. 후보별 결과를 probe.json에 남긴다.
        e2e_drivers.write_probe_json(writer, probes)
        gate = _candidate_gate(candidates, required_types)
        if gate is not None:
            # SUT 미기동 단축 — 이 경로는 SUT 없이 전 후보를 판정할 수 있을 때뿐이다.
            gate_status, gate_detail_code, gate_detail = gate
            journal.to(STATE_PROFILE_RESOLVED, {"profile": scenario.get("profile")})
            journal.to(gate_status, {"candidates": len(candidates)})
            return _finalize(
                status=gate_status,
                journal=journal,
                writer=writer,
                context=context,
                leases=leases,
                reclaimed=reclaimed,
                handles=[],
                candidates=candidates,
                artifact_root=resolved_root,
                artifact_dir=artifact_dir,
                run_id=resolved_run_id,
                scenario_id=scenario_id,
                scenario=scenario,
                started_at=started_at,
                detail_code=gate_detail_code,
                detail=gate_detail,
            )

    # ── sut_starting → sut_ready ─────────────────────────────────────────────
    journal.to(STATE_SUT_STARTING)
    try:
        handles = _start_sut(
            context=context,
            leases=leases,
            artifact_dir=artifact_dir,
            artifact_root=resolved_root,
        )
    except e2e_runtime.SutStartupError as exc:
        journal.to(STATUS_INFRA_ERROR, {"reason": exc.reason})
        return _finalize(
            status=STATUS_INFRA_ERROR,
            journal=journal,
            writer=writer,
            context=context,
            leases=leases,
            reclaimed=reclaimed,
            handles=handles,
            candidates=candidates,
            artifact_root=resolved_root,
            artifact_dir=artifact_dir,
            run_id=resolved_run_id,
            scenario_id=scenario_id,
            scenario=scenario,
            started_at=started_at,
            detail_code="e2e_sut_startup_failed",
            detail=exc.reason,
        )

    journal.to(STATE_SUT_READY, {"urls": _urls(leases)})

    if needs_sut_for_probe:
        # §A.8 [MUST] — api probe는 실제 SUT `/health`를 호출해야 가용성을 확정한다.
        # 설정값 존재로 추정하지 않으므로 여기서야 후보를 해석할 수 있다(NR-7).
        candidates, probes = _resolve_executor_candidates(
            scenario,
            runtime_context=_executor_runtime_context(
                artifact_dir, task_path, writer,
                backend_url=_urls(leases)[_ROLE_BACKEND],
                action_log=action_log, run_id=resolved_run_id,
            ),
            driver_cache=driver_cache,
        )
        e2e_drivers.write_probe_json(writer, probes)

    # §A.2.1 — SUT가 준비된 뒤에 profile 확정을 발행한다. 전이는 계약이 정한 순서대로
    # 남아야 재개·감사가 성립한다.
    journal.to(STATE_PROFILE_RESOLVED, {"profile": scenario.get("profile")})

    selected = [item for item in candidates if item.get("outcome") == _OUTCOME_SELECTED]
    gate = _candidate_gate(candidates, required_types)
    if gate is not None:
        gate_status, gate_detail_code, gate_detail = gate
        journal.to(gate_status, {"candidates": len(candidates)})
        return _finalize(
            status=gate_status,
            journal=journal,
            writer=writer,
            context=context,
            leases=leases,
            reclaimed=reclaimed,
            handles=handles,
            candidates=candidates,
            artifact_root=resolved_root,
            artifact_dir=artifact_dir,
            run_id=resolved_run_id,
            scenario_id=scenario_id,
            scenario=scenario,
            started_at=started_at,
            detail_code=gate_detail_code,
            detail=gate_detail,
        )

    journal.to(
        STATE_EXECUTOR_READY,
        {
            "executors": [
                {"type": item.get("type"), "driver": item.get("driver"), "session_mode": item.get("session_mode")}
                for item in selected
            ]
        },
    )

    # ── scenario_running → evidence_captured ─────────────────────────────────
    outcome = _run_scenario_steps(
        scenario=scenario,
        selected=selected,
        journal=journal,
        writer=writer,
        run_id=resolved_run_id,
        runtime_context=_executor_runtime_context(
            artifact_dir, task_path, writer,
            backend_url=_urls(leases)[_ROLE_BACKEND],
            action_log=action_log, run_id=resolved_run_id,
        ),
        action_log=action_log,
        urls=_urls(leases),
        target=context.target,
        driver_cache=driver_cache,
    )
    return _finalize(
        status=outcome["status"],
        operational_status=outcome.get("operational_status"),
        executed=outcome["executed"],
        assertion_results=outcome["assertion_results"],
        observed_executor_types=outcome["observed_executor_types"],
        fidelity_ceiling=outcome["fidelity_ceiling"],
        owned_browser=outcome["owned_browser"],
        journal=journal,
        writer=writer,
        context=context,
        leases=leases,
        reclaimed=reclaimed,
        handles=handles,
        candidates=candidates,
        artifact_root=resolved_root,
        artifact_dir=artifact_dir,
        run_id=resolved_run_id,
        scenario_id=scenario_id,
        scenario=scenario,
        started_at=started_at,
        detail_code=outcome["detail_code"],
        detail=outcome["detail"],
    )


# §A.4 step_role 실행 순서. 시나리오가 선언한 원소 순서는 그룹 **안에서** 그대로
# 유지하고, 그룹 사이의 순서만 이 튜플이 정한다 — hybrid의 "API setup → 핵심 UI 행동 →
# API/state verifier" 연결이 성립하려면 setup이 검증보다 먼저 끝나 있어야 한다.
_STEP_ROLE_ORDER = (
    e2e_executors.STEP_ROLE_SETUP,
    e2e_executors.STEP_ROLE_VERIFY,
    e2e_executors.STEP_ROLE_CLEANUP,
)


def _ordered_plan(plan: List[Any]) -> List[Any]:
    return sorted(plan, key=lambda step: _STEP_ROLE_ORDER.index(step.step_role))


# 후보가 **실행에 실패한 것**과 후보에 **연산 자체가 없는 것**은 다른 분류다.
# `dispatch()`가 연산을 찾지 못해 올리는 오류(`*_operation_unimplemented`,
# `*_unknown_operation`)는 driver·executor가 아직 아무 일도 하기 전에 나온다 — 하네스가
# 그 표면을 실행할 수단을 갖고 있지 않다는 뜻이며, §C.7이 `infra_error`로 규정한
# "driver 실행 오류"(실제로 돌다가 깨진 경우)가 아니다. 이 구분이 없으면 미구현 연산이
# 서버·포트 장애와 같은 칸에 기록돼, 무엇을 고쳐야 하는지가 기록에서 사라진다.
# 어느 쪽이든 다음 후보로 전환하지 않는 것은 같다(TASK.md C-3, §C.7).
_CAPABILITY_GAP_DETAIL_CODES = frozenset({
    "driver_operation_unimplemented",
    "driver_unknown_operation",
    "executor_operation_unimplemented",
    "executor_unknown_operation",
})


def _failure_status(detail_code: Optional[str]) -> str:
    return STATUS_BLOCKED if detail_code in _CAPABILITY_GAP_DETAIL_CODES else STATUS_INFRA_ERROR


def _run_scenario_steps(
    *,
    scenario: dict,
    selected: List[Dict[str, Any]],
    journal: _Journal,
    writer: e2e_evidence.EvidenceWriter,
    run_id: str,
    runtime_context: Dict[str, Any],
    urls: Dict[str, Optional[str]],
    target: Optional[str],
    action_log: Optional[e2e_executors.ActionLog] = None,
    driver_cache: Optional["_DriverCache"] = None,
) -> Dict[str, Any]:
    """§A.2.1 `scenario_running` → `evidence_captured`. step 실행·assertion·증적 수집.

    후보 **선택**은 이미 끝났다(§A.1.2). 이 함수는 선택된 후보를 실제 executor 인스턴스로
    열어 시나리오 step을 돌린다. 실행 중 오류는 `infra_error`이며 **다음 후보로 넘어가지
    않는다**(TASK.md C-3, §C.7 "예외 목록 없음"). 증적은 전부 `writer` 관문을 거친다
    (§A.12, C-EXE-3).

    판정은 만들지 않는다 — assertion `passed` 집계로 `status` 후보만 정하고, `pass` 승격은
    호출자가 `build_verdict`에 맡긴다(§C.2 [MUST]).
    """
    blank: Dict[str, Any] = {
        "executed": False,
        "status": STATUS_BLOCKED,
        "assertion_results": [],
        "observed_executor_types": [],
        "fidelity_ceiling": None,
        "operational_status": None,
        "detail_code": None,
        "detail": None,
        # §A.3 — driver가 연 page·profile. 정리는 이 대장에 오른 것만 대상으로 한다(C-2).
        "owned_browser": {"browser_pages": [], "browser_profiles": []},
    }

    try:
        plan = e2e_scenario_adapter.build_execution_plan(scenario)
    except e2e_executors.ExecutorError as exc:
        blank.update(detail_code=exc.detail_code, detail=exc.detail)
        return blank

    journal.to(STATE_SCENARIO_RUNNING, {"steps": len(plan)})

    log = action_log or runtime_context.get("action_log") or e2e_executors.ActionLog()
    # handoff 사양은 시나리오가 소유한다(§A.9). human executor가 이를 받지 못하면
    # `handoff_contract_incomplete`로 `infra_error`가 되어 `awaiting_human`에 도달하지
    # 못한다(AC-9).
    context = dict(
        runtime_context,
        action_log=log,
        urls=urls,
        target=target,
        run_id=run_id,
        scenario_id=scenario.get("id"),
        handoff=scenario.get("handoff"),
    )

    try:
        instances = _open_executors(selected, context, driver_cache=driver_cache)
    except (e2e_executors.ExecutorError, e2e_drivers.DriverError) as exc:
        failed = _failure_status(exc.detail_code)
        journal.to(failed, {"detail_code": exc.detail_code})
        blank.update(status=failed, detail_code=exc.detail_code, detail=exc.detail)
        return blank

    executed_ids: List[str] = []
    assertion_results: List[Dict[str, Any]] = []
    try:
        for step in _ordered_plan(plan):
            instance = instances.get(step.executor)
            if instance is None:
                # 선택된 후보에 없는 executor를 시나리오가 요구한다 — 계약 위반이며
                # 대체 executor로 돌리지 않는다(§C.4 "API가 UI를 대체할 수 없다").
                raise e2e_executors.ExecutorError(
                    "e2e_step_executor_not_selected",
                    f"step {step.id!r} requires executor {step.executor!r} which is not selected",
                )
            outcome = instance["run_step"](step)
            executed_ids.append(step.id)
            if isinstance(outcome, dict) and outcome.get("awaiting_human"):
                # §A.9·§B.1.2 — handoff 발행 시점에 run은 정지하고 제어를 사람에게
                # 넘긴다. 뒤 step·assertion을 계속 돌리면 사람이 아직 하지 않은 일을
                # 실패로 기록하게 되고, 재개 경로가 판정할 것이 남지 않는다(R-13).
                blank.update(
                    executed=True,
                    status=None,
                    operational_status="awaiting_human",
                    observed_executor_types=sorted({s.executor for s in _ordered_plan(plan)}),
                    handoff=outcome.get("handoff"),
                )
                journal.to("awaiting_human", {"handoff_id": (outcome.get("handoff") or {}).get("handoff_id")})
                return blank
        assertion_results = _run_assertions(scenario, plan, instances, executed_ids)
        for instance in instances.values():
            instance["capture"]()
    except (e2e_executors.ExecutorError, e2e_drivers.DriverError) as exc:
        failed = _failure_status(exc.detail_code)
        journal.to(failed, {"detail_code": exc.detail_code})
        blank.update(
            executed=bool(executed_ids),
            status=failed,
            detail_code=exc.detail_code,
            detail=exc.detail,
            observed_executor_types=e2e_scenario_adapter.observed_executors(plan, executed_ids),
            owned_browser=_collect_browser_ledger(instances),
        )
        return blank
    finally:
        for instance in instances.values():
            instance["close"]()

    owned_browser = _collect_browser_ledger(instances)
    journal.to(STATE_EVIDENCE_CAPTURED, {"assertions": len(assertion_results)})

    # §C.4 집행 2 — 핵심 UI assertion이 verify API step만으로 충족됐으면 `real-usage`
    # 승격을 막는다. setup·cleanup API는 후보에 들어오지 않으므로 우회로 판정되지 않는다.
    substituted = e2e_scenario_adapter.api_substituted_core_ui_assertions(
        scenario, plan, assertion_results
    )
    missing = e2e_scenario_adapter.missing_assertion_results(scenario, assertion_results)
    all_passed = bool(assertion_results) and not missing and all(
        item.get("passed") is True for item in assertion_results
    )
    return {
        "executed": True,
        "status": _FINAL["pass"] if all_passed else _FINAL["fail"],
        "assertion_results": assertion_results,
        "observed_executor_types": e2e_scenario_adapter.observed_executors(plan, executed_ids),
        "owned_browser": owned_browser,
        "fidelity_ceiling": FIDELITY_REAL_HTTP if substituted else None,
        "detail_code": "e2e_core_ui_behavior_substituted_by_api" if substituted else None,
        "detail": (
            f"core UI assertions satisfied only by step_role=verify api steps: {substituted}"
            if substituted
            else None
        ),
    }


def _open_executors(
    selected: List[Dict[str, Any]],
    context: Dict[str, Any],
    *,
    driver_cache: Optional["_DriverCache"] = None,
) -> Dict[str, Dict[str, Any]]:
    """선택된 후보마다 실행 인스턴스를 열고 `{run_step, assert, capture, close}`로 감싼다.

    두 레지스트리(driver·executor)의 호출 규약이 §B.2/§B.3으로 서로 다르므로, 호출 형태의
    차이는 여기서 흡수하고 step 루프는 하나의 모양만 다룬다.
    """
    opened: Dict[str, Dict[str, Any]] = {}
    for record in selected:
        executor_type = str(record.get("type"))
        if executor_type == _EXECUTOR_BROWSER:
            opened[executor_type] = _open_browser(record, context, driver_cache=driver_cache)
        else:
            opened[executor_type] = _open_executor(executor_type, context)
    return opened


def _wrap_human_executor(executor: Any, context: Dict[str, Any]) -> Dict[str, Any]:
    """human executor를 step 루프가 다루는 하나의 모양으로 감싼다.

    `run_step`은 `handoff`를 발행하고, 발행 시점에 run은 `awaiting_human`으로 정지한다
    (§A.9·§B.1.2). `assert`·`capture`는 사람 제출이 도착한 뒤 `resume` 경로에서 판정되므로
    여기서는 관측을 만들지 않는다 — 만들면 사람 제출만으로 `pass`가 서는 우회가 된다(R-13).
    """

    def run_step(step: Any) -> Dict[str, Any]:
        raw = getattr(step, "raw", None) or {}
        handoff = executor.dispatch(
            "handoff",
            {
                "run_id": context.get("run_id"),
                "scenario_id": context.get("scenario_id"),
                "step_id": step.id,
                "handoff_spec": raw.get("handoff") or context.get("handoff"),
            },
        )
        # 호출자가 이 신호를 보고 정지한다. 상태·exit 값은 여기서 만들지 않는다 —
        # `e2e_contract`가 소유한다(C-1).
        return {"awaiting_human": True, "handoff": handoff}

    def run_assert(assertion: Dict[str, Any]) -> Dict[str, Any]:
        # 판정은 `resume` 뒤 `validate_pass_requirements`가 내린다(C-1).
        return {
            "id": assertion.get("id"),
            "expected": assertion.get("expected"),
            "actual": None,
            "passed": False,
            "pending_human": True,
        }

    def capture() -> None:
        return None

    def close() -> None:
        return None

    return {
        "run_step": run_step,
        "assert": run_assert,
        "capture": capture,
        "close": close,
        "instance": executor,
    }


def _open_executor(executor_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
    factory = e2e_executors.registered_executors().get(executor_type)
    if factory is None:
        raise e2e_executors.ExecutorError(
            "e2e_no_executor_registered", f"{executor_type} executor is no longer registered"
        )
    executor = factory(runtime_context=dict(context))
    operations = tuple(getattr(executor, "operations", ()) or ())
    if executor_type == _EXECUTOR_HUMAN:
        # human executor는 `probe`·`handoff`·`resume`만 가진다(§B.3,
        # `executors/__init__.py` HUMAN_OPERATIONS). `prepare`를 내려보내면
        # collaborative·manual profile이 실행 전에 거부되어 `awaiting_human`에
        # 도달하지 못한다(AC-9). 연산 집합이 다른 executor를 하나의 호출 모양으로
        # 밀어 넣지 않는다 — 여기서 갈라 흡수하는 것이 이 함수의 역할이다.
        return _wrap_human_executor(executor, context)
    if "prepare" in operations:
        prepared = executor.dispatch(
            "prepare",
            {
                "run_id": context.get("run_id"),
                "target": context.get("target"),
                "base_url": context.get("backend_url"),
                "isolation_key": context.get("run_id"),
            },
        )
        handle = prepared.get("handle")
    else:
        handle = context.get("run_id")

    def run_step(step: Any) -> Dict[str, Any]:
        return executor.dispatch(
            "act", {"handle": handle, "step_id": step.id, "action": step.as_action()}
        )

    def run_assert(assertion: Dict[str, Any]) -> Dict[str, Any]:
        return executor.dispatch("assert", {"handle": handle, "assertion": dict(assertion)})

    def capture() -> None:
        executor.dispatch("capture", {"handle": handle, "evidence_spec": []})

    def close() -> None:
        try:
            executor.dispatch("cleanup", {"handle": handle})
        except e2e_executors.ExecutorError:
            # 정리 실패로 이미 확정된 판정을 덮지 않는다. 누출은 cleanup.json과
            # §A.6.1 승격 경로가 별도로 기록한다.
            pass

    return {
        "run_step": run_step,
        "assert": run_assert,
        "capture": capture,
        "close": close,
        "instance": executor,
    }


def _open_browser(
    record: Dict[str, Any],
    context: Dict[str, Any],
    *,
    driver_cache: Optional["_DriverCache"] = None,
) -> Dict[str, Any]:
    key = (record.get("driver"), record.get("session_mode"))
    # 후보 해석 때 만들어 probe까지 끝낸 인스턴스를 그대로 이어받는다. 새로 만들면
    # 생성자의 binary 해석(`--version`)이 한 번 더 일어나고, 같은 연산의 두 번째 호출은
    # 재시도로 관측된다(S-27 (d-1), §C.7).
    driver = driver_cache.get(key) if driver_cache is not None else None
    if driver is None:
        factory = e2e_drivers.registered_drivers().get(key)
        if factory is None:
            raise e2e_drivers.DriverError(
                "e2e_no_executor_registered", f"browser driver {key} is no longer registered"
            )
        driver = factory(runtime_context=dict(context))
    url = (context.get("urls") or {}).get(_ROLE_FRONTEND)
    if not url:
        raise e2e_drivers.DriverError(
            "driver_open_url_required", "browser step execution requires a leased frontend url"
        )
    # `isolation_key`가 driver가 대장에 올리는 page handle이 된다(§A.3 `browser_pages`).
    # run_id로 이름을 잡아야 정리가 **이 run이 연 page**만 겨냥한다(C-2) — 기본값인
    # 세션 이름을 쓰면 사용자 `default` 세션과 구분되지 않는다.
    session = driver.dispatch("open", {"url": url, "isolation_key": context.get("run_id")})
    page_id = session.get("page_id") or session.get("handle")

    def run_step(step: Any) -> Dict[str, Any]:
        return driver.dispatch(
            "act", {"page_id": page_id, "step_id": step.id, "action": step.as_action()}
        )

    def run_assert(assertion: Dict[str, Any]) -> Dict[str, Any]:
        return driver.dispatch(
            "assert",
            {"page_id": page_id, "step_id": assertion.get("id"), "assertion": dict(assertion)},
        )

    def capture() -> None:
        # 증적 관문을 요청에도 싣는다 — driver는 request → runtime_context 순으로 찾는다.
        driver.dispatch(
            "capture",
            {"page_id": page_id, "evidence_spec": [], "writer": context.get("writer")},
        )

    def close() -> None:
        try:
            driver.dispatch("close", {"page_id": page_id})
        except e2e_drivers.DriverError:
            pass

    return {
        "run_step": run_step,
        "assert": run_assert,
        "capture": capture,
        "close": close,
        "instance": driver,
    }


def _collect_browser_ledger(instances: Dict[str, Dict[str, Any]]) -> Dict[str, List[Any]]:
    """driver가 스스로 신고한 소유 자원만 모은다(§A.3 `browser_pages`·`browser_profiles`).

    [MUST] 하네스가 브라우저를 훑어 목록을 만들지 않는다 — 우리가 연 것만 driver의
    `owned_resources()`에 오르고, 그 밖의 탭·profile은 사용자 소유다(TASK.md C-2,
    §C.3 "Browser driver 비소유: 사용자 브라우저 탭·user_owned surface").
    """
    pages: List[Any] = []
    profiles: List[Any] = []
    for executor_type, instance in instances.items():
        driver = instance.get("instance")
        reader = getattr(driver, "owned_resources", None)
        if reader is None:
            continue
        ledger = reader() or {}
        for page_id in ledger.get("browser_pages") or []:
            pages.append(
                {
                    "page_id": str(page_id),
                    "driver": getattr(driver, "name", executor_type),
                    "session_mode": getattr(driver, "session_mode", None),
                    "user_owned": False,
                }
            )
        profiles.extend(str(item) for item in (ledger.get("profiles") or []))
    return {"browser_pages": pages, "browser_profiles": profiles}


def _run_assertions(
    scenario: dict,
    plan: List[Any],
    instances: Dict[str, Dict[str, Any]],
    executed_ids: List[str],
) -> List[Dict[str, Any]]:
    """시나리오 assertion을 **검증 대상 step을 실행한 executor**로 판정한다.

    어느 executor가 판정했는지를 `executor`·`observed_via_step`으로 결과에 남긴다 —
    §C.4 집행 2가 "핵심 UI assertion을 무엇이 충족했는가"를 이 두 필드로 읽는다.
    """
    grouped = e2e_scenario_adapter.verify_step_ids_by_executor(plan)
    results: List[Dict[str, Any]] = []
    for assertion in scenario.get("assertions") or []:
        if not isinstance(assertion, dict):
            continue
        executor_type = str(assertion.get("executor") or "")
        if executor_type not in instances:
            # 시나리오가 지정하지 않으면 verify step을 가진 executor 중 browser를
            # 우선한다 — UI 검증을 API로 흘려보내지 않기 위한 기본값이다(§C.4).
            for candidate in (_EXECUTOR_BROWSER, "api", "human"):
                if grouped.get(candidate) and candidate in instances:
                    executor_type = candidate
                    break
        instance = instances.get(executor_type)
        if instance is None:
            continue
        outcome = dict(instance["assert"](assertion))
        outcome.setdefault("executor", executor_type)
        verify_ids = [item for item in grouped.get(executor_type, ()) if item in executed_ids]
        outcome.setdefault("observed_via_step", verify_ids[-1] if verify_ids else None)
        results.append(outcome)
    return results


def _required_browser_capabilities(scenario: dict) -> List[str]:
    """시나리오 `required_evidence`에서 §A.8 capability 요구를 읽는다.

    capability 요구는 별도 `requires` 필드를 만들지 않고 `required_evidence` 원소로
    표현한다(TRD.md TD-12 결정 3).
    """
    declared = [str(item) for item in (scenario.get("required_evidence") or [])]
    return [item for item in declared if item in e2e_drivers.CAPABILITY_KEYS]


def _required_executor_types(scenario: dict) -> tuple:
    """profile이 요구하는 executor 종류(§1 `EXECUTOR_MATRIX`). 미지의 profile이면 빈 튜플.

    계약을 소비만 한다 — `profile`이 `None`이거나 matrix에 없는 값이면 요구 집합을
    지어내지 않고 빈 튜플로 둔다(C-8: 계약에 없는 경로를 만들지 않는다).
    """
    try:
        return tuple(e2e_contract.executor_contract(str(scenario.get("profile") or ""))["required"])
    except KeyError:
        return ()


def _candidate_gate(candidates: List[Dict[str, Any]], required_types: tuple) -> Optional[tuple]:
    """후보 기록만으로 run을 끝내야 하는가. 끝내야 하면 `(status, detail_code, detail)`.

    [MUST] 후보 시도 중 하나라도 `outcome=infra_error`이면 run은 `infra_error`로 확정된다
    (§C.7 "infra_error에서 다음 후보로의 전환은 전면 금지 — 예외 목록 없음", MV-38).
    `selected`가 0건이라는 이유로 `executor_unavailable`로 덮으면 인프라 실패가 후보 소진으로
    둔갑해, 전환 금지 계약이 기록 위에서 사라진다. 그래서 infra_error를 **먼저** 본다.
    """
    failed = [
        item for item in candidates if item.get("outcome") == e2e_drivers.OUTCOME_INFRA_ERROR
    ]
    if failed:
        return (
            STATUS_INFRA_ERROR,
            "e2e_candidate_infra_error",
            # 후보가 반환한 error code 원문을 그대로 싣는다(NR-7).
            str(failed[0].get("reason") or "candidate attempt failed with infra_error"),
        )
    if not _all_required_selected(candidates, required_types):
        return (
            STATUS_EXECUTOR_UNAVAILABLE,
            "e2e_no_executor_registered",
            "no executor candidate satisfies the profile contract",
        )
    return None


def _all_required_selected(candidates: List[Dict[str, Any]], required_types: tuple) -> bool:
    """profile이 요구하는 executor 종류마다 `selected` 후보가 있는가(§A.1.2).

    요구 종류가 없으면(미지의 profile) 진행 근거가 없으므로 False다 — "요구가 없으니
    전부 만족"으로 읽으면 profile 없는 run이 SUT를 띄우게 된다.
    """
    if not required_types:
        return False
    chosen = {
        item.get("type") for item in candidates if item.get("outcome") == _OUTCOME_SELECTED
    }
    return all(item in chosen for item in required_types)


def _executor_runtime_context(
    artifact_dir: str,
    task_path: str,
    writer: e2e_evidence.EvidenceWriter,
    *,
    backend_url: Optional[str] = None,
    action_log: Optional[e2e_executors.ActionLog] = None,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """executor·driver가 소비하는 runtime context(§B.3 `probe` 입력, §B.2 동일).

    `backend_url`은 SUT가 실제로 기동된 뒤에만 채운다 — 값이 있다는 것 자체가
    "health를 물어볼 대상이 존재한다"는 뜻이어야 하기 때문이다(§A.8, NR-7).

    `writer`·`action_log`는 **후보 해석 시점부터** 실린다. driver는 이 둘을 생성자가 받은
    `runtime_context`에서 lazy하게 읽고(§A.4 행 적재·§A.12 증적 관문), 후보 해석이 만든
    인스턴스를 step 실행이 그대로 이어받기 때문이다 — 나중에 끼워 넣으면 그 사이에 적힌
    행동 기록이 갈 곳을 잃는다.
    """
    return {
        "backend_url": backend_url,
        "artifact_dir": artifact_dir,
        "task_path": task_path,
        "writer": writer,
        "action_log": action_log,
        "run_id": run_id,
    }


def _register_executors() -> None:
    """`api`·`human` executor를 레지스트리에 등록한다.

    등록 호출 지점을 orchestrator가 소유한다. executor 모듈은 import 부작용으로 자동
    등록하지 않으며(`executors/api.py` `register()` 주석), 그래야 후보 목록이 언제
    열리는지를 이 모듈이 통제해 §A.2.1 순서(기동 → 후보 해석)를 지킬 수 있다. driver
    쪽의 `_BUILTIN_DRIVER_MODULES` 자동 등록과 의도적으로 다른 구조다.
    """
    from lib.e2e.executors import api as e2e_api
    from lib.e2e.executors import human as e2e_human

    e2e_api.register()
    e2e_human.register()


class _DriverCache:
    """후보 해석이 만든 driver 인스턴스를 붙잡아 step 실행에서 재사용한다.

    `drivers.resolve_candidates()`는 후보를 만들고 probe한 뒤 인스턴스를 버린다(반환값은
    §A.1.2 기록뿐이다). step 실행에서 같은 driver를 다시 생성하면 **생성자가 하는
    `--version` 해석이 한 번 더 일어난다** — 같은 연산의 두 번째 호출은 재시도이며
    동결 RED S-27 (d-1)이 정확히 그것을 금지한다. drivers 패키지는 이 태스크에서
    변경 0이므로(W-5 소유), 대신 레지스트리 factory를 감싸 **첫 생성 결과를 기억**시켜
    같은 인스턴스가 probe와 실행에 함께 쓰이게 한다.
    """

    def __init__(self) -> None:
        self._instances: Dict[tuple, Any] = {}

    def registry(self) -> Dict[tuple, Any]:
        """`resolve_candidates(registry=...)`에 넘길 메모이즈 레지스트리."""
        return {
            key: self._memoized(key, factory)
            for key, factory in e2e_drivers.registered_drivers().items()
        }

    def _memoized(self, key: tuple, factory: Any) -> Any:
        def make(**kwargs):
            if key not in self._instances:
                self._instances[key] = factory(**kwargs)
            return self._instances[key]

        return make

    def get(self, key: tuple) -> Optional[Any]:
        return self._instances.get(key)


def _resolve_executor_candidates(
    scenario: dict,
    *,
    runtime_context: Optional[Dict[str, Any]] = None,
    driver_cache: Optional[_DriverCache] = None,
) -> tuple:
    """profile이 요구하는 executor 후보를 §A.1.2 원소로 열거한다.

    반환: `(candidates, probes)`. browser 후보의 순서·manifest 게이트·probe는
    `lib/e2e/drivers`가(§B.2 C-DRV-2·C-DRV-3), `api`·`human` 후보는
    `lib/e2e/executors`가 소유한다(§B.3 C-EXE-1). 이 함수는 `EXECUTOR_MATRIX`가 요구하는
    종류를 두 레지스트리에 나눠 묻고 `order`를 1부터 연속으로 잇는 일만 한다.

    `driver_cache`가 주어지면 여기서 만든 browser driver 인스턴스가 그 안에 남아 step
    실행이 재생성 없이 이어받는다.
    """
    profile = str(scenario.get("profile") or "")
    required = _required_executor_types(scenario)
    if not required:
        return ([], [])

    candidates: List[Dict[str, Any]] = []
    probes: List[Dict[str, Any]] = []

    # browser 후보가 먼저다 — C-DRV-3 후보 순서가 배열 앞쪽을 차지해야 §A.1.2 `order`가
    # 실제 시도 순서와 일치한다.
    if _EXECUTOR_BROWSER in required:
        browser_candidates, browser_probes = e2e_drivers.resolve_candidates(
            required_capabilities=_required_browser_capabilities(scenario),
            # driver 인스턴스가 여기서 만들어져 step 실행까지 재사용되므로(§C.7·S-27),
            # 증적 관문과 행동 로그를 생성 시점에 함께 넘긴다.
            runtime_context=dict(
                runtime_context or {},
                profile=profile,
                surface_kind=scenario.get("surface_kind"),
            ),
            registry=driver_cache.registry() if driver_cache is not None else None,
        )
        probes.extend(browser_probes)
        for item in browser_candidates:
            item["order"] = len(candidates) + 1
            candidates.append(item)

    non_browser = [item for item in required if item != _EXECUTOR_BROWSER]
    if non_browser:
        _register_executors()
        executor_candidates, executor_probes = e2e_executors.resolve_executor_candidates(
            non_browser,
            runtime_context=runtime_context or {},
            start_order=len(candidates),
        )
        candidates.extend(executor_candidates)
        probes.extend(executor_probes)

    return (candidates, probes)


def _start_sut(
    *,
    context: e2e_target.TargetContext,
    leases: List[e2e_ports.LeaseRecord],
    artifact_dir: str,
    artifact_root: str,
) -> List[e2e_runtime.SutHandle]:
    """임대 포트 위에 backend·frontend를 strict-port로 기동하고 health를 통과시킨다.

    기동·회수 자체는 T01 lib/e2e/runtime.py가 소유하며(D-11) 이 함수는 순서와 lease
    confirm만 맡는다. health를 통과한 포트만 §A.7 `confirmed`로 올린다.
    """
    port_of = {record.role: record.port for record in leases}
    handles: List[e2e_runtime.SutHandle] = []

    backend = e2e_runtime.start_backend(
        source_root=context.project_root,
        artifact_dir=artifact_dir,
        port=port_of[_ROLE_BACKEND],
    )
    handles.append(backend)
    e2e_runtime.wait_healthy(backend.url)
    e2e_ports.confirm_lease(artifact_root, _lease_of(leases, _ROLE_BACKEND))

    frontend = e2e_runtime.start_frontend(
        source_root=context.project_root,
        artifact_dir=artifact_dir,
        port=port_of[_ROLE_FRONTEND],
        backend_url=backend.url,
    )
    handles.append(frontend)
    e2e_ports.confirm_lease(artifact_root, _lease_of(leases, _ROLE_FRONTEND))
    return handles


def _lease_of(leases: List[e2e_ports.LeaseRecord], role: str) -> e2e_ports.LeaseRecord:
    for record in leases:
        if record.role == role:
            return record
    raise KeyError(role)


def _urls(leases: List[e2e_ports.LeaseRecord]) -> dict:
    urls: Dict[str, Optional[str]] = {"frontend": None, "backend": None}
    for record in leases:
        if record.role in urls:
            urls[record.role] = f"http://127.0.0.1:{record.port}"
    return urls


def _achieved_fidelity(
    *,
    evidence_complete: bool,
    candidates: List[Dict[str, Any]],
    handles: List[e2e_runtime.SutHandle],
    ceiling: Optional[str] = None,
) -> str:
    """이 run이 **실제로 달성한** 충실도(§A.1 `fidelity`).

    [MUST] 증적이 불완전한 run은 `real-usage`로 기록하지 않는다(AC-6, S-6). 시나리오의
    `required_fidelity`를 결과로 베껴 쓰지 않는다 — 요구치와 달성치를 구분하는 것이
    이 필드의 존재 이유다.

    `ceiling`은 §C.4 집행 2가 내리는 상한이다. browser executor가 selected라는 사실만으로
    `real-usage`를 주는 것은 "browser가 무언가는 했다"만 보는 판정이고, §C.4가 금지하는
    것은 "핵심 UI 행동의 **검증**을 verify API step으로 대체"하는 일이다. 그런 대체가
    관측되면 상한이 `real-http`로 내려와 승격이 막힌다(R-12, AC-8).
    """
    if not evidence_complete:
        return FIDELITY_MOCK
    selected = [item for item in candidates if item.get("outcome") == _OUTCOME_SELECTED]
    if any(item.get("type") == _EXECUTOR_BROWSER for item in selected):
        achieved = FIDELITY_REAL_USAGE
    elif selected and handles:
        achieved = FIDELITY_REAL_HTTP
    else:
        achieved = FIDELITY_MOCK
    if ceiling is None:
        return achieved
    order = (FIDELITY_MOCK, FIDELITY_REAL_HTTP, FIDELITY_REAL_USAGE)
    if ceiling not in order:
        return achieved
    return achieved if order.index(achieved) <= order.index(ceiling) else ceiling


def _finalize(
    *,
    status: str,
    journal: _Journal,
    writer: e2e_evidence.EvidenceWriter,
    context: Optional[e2e_target.TargetContext],
    leases: List[e2e_ports.LeaseRecord],
    reclaimed: List[str],
    handles: List[e2e_runtime.SutHandle],
    candidates: Optional[List[Dict[str, Any]]] = None,
    artifact_root: str,
    artifact_dir: str,
    run_id: str,
    scenario_id: Optional[str],
    started_at: str,
    detail_code: Optional[str] = None,
    detail: Optional[str] = None,
    scenario: Optional[dict] = None,
    executed: bool = False,
    error_override: Optional[str] = None,
    assertion_results: Optional[List[Dict[str, Any]]] = None,
    observed_executor_types: Optional[List[str]] = None,
    fidelity_ceiling: Optional[str] = None,
    owned_browser: Optional[Dict[str, List[Any]]] = None,
    operational_status: Optional[str] = None,
) -> dict:
    """SUT 회수 → lease 해제 → 산출물 기록 → stdout payload 조립.

    verdict는 직접 조립하지 않고 `build_verdict()`에 위임한다(CONTRACT.md §1 표).
    exit은 `status_to_exit()` 결과로만 결정한다.

    `error_override`는 계약 함수가 **이미 돌려준** error 문자열을 그대로 싣기 위한
    통로다(§C.4 정적 거부의 `surface_profile_mismatch`). 이 모듈이 error 문자열을
    새로 만들지는 않는다(C-125-1) — 받은 값을 통과시킬 뿐이다.
    """
    cleanup_report = e2e_runtime.stop_all(handles) if handles else e2e_runtime.CleanupReport([], [])
    leaked = list(cleanup_report.leaked)
    released_lease_ids = e2e_ports.release_leases(artifact_root, leases)
    cleanup = CLEANUP_COMPLETE if not leaked else CLEANUP_WARNING
    final_state = journal.state

    # ── 공통 필수 증적 5종을 증적 관문으로 발행한다(§A.1/§A.4/§A.5/§A.6, §A.12) ──
    required_evidence = [str(item) for item in ((scenario or {}).get("required_evidence") or [])]
    _emit_server_log(writer, handles)
    # 행동·assertion은 step runner가 소유한다. runner가 돌지 않았거나 결과가 비면 파일은
    # 관문을 통해 발행하되 관측 증적으로 올리지 않는다 — 빈 파일로 pass 게이트를
    # 통과시키지 않는다. runner가 이미 `actions.jsonl`을 발행했으면 여기서 덮어쓰지
    # 않는다(그랬다면 방금 기록한 행동이 사라진다).
    results = list(assertion_results or [])
    if not executed:
        writer.write_jsonl(
            e2e_evidence.EVIDENCE_PATHS["action_log"], [], kind="action_log", observed=False
        )
    writer.write_json(
        e2e_evidence.EVIDENCE_PATHS["assertion_evidence"],
        {"schema_version": SCHEMA_VERSION, "run_id": run_id, "results": results},
        kind="assertion_evidence",
        observed=bool(results),
    )
    cleanup_json = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "result": cleanup,
        "released": (
            [{"kind": "process_group", "id": str(item)} for item in cleanup_report.released]
            + [{"kind": "lease", "id": str(item)} for item in released_lease_ids]
        ),
        "leaked": [{"kind": "process_group", "id": str(item)} for item in leaked],
        # C-2 집행 증적 — 사용자 소유 자원은 애초에 소유 대장에 오르지 않는다.
        "skipped_user_owned": [],
        "escalated_to_infra_error": bool(leaked),
    }
    writer.write_json(
        e2e_evidence.EVIDENCE_PATHS["cleanup"], cleanup_json, kind="cleanup", observed=True
    )

    # §A.6.1 승격 — process_group·lease 누출은 다음 실행을 오염시키므로 infra_error다.
    if leaked:
        status = STATUS_INFRA_ERROR

    verdict_input: Optional[Dict[str, Any]] = None
    # `awaiting_human`은 아직 끝나지 않은 run이다. 증적·assertion 완결성을 요구하는
    # 일반 경로로 보내면 사람이 아직 하지 않은 일이 결손으로 계산되어 `infra_error`가
    # 된다 — §B.1.2대로 `status`는 null·exit 20으로 정지하고, 판정은 `e2e resume`
    # 뒤의 `validate_pass_requirements`가 내린다(R-13).
    if operational_status == "awaiting_human":
        verdict = e2e_contract.build_verdict({"status": "awaiting_human"})
        resolved_status = None
    # step runner가 돌았으면 시나리오·결과 전체를 verdict 입력으로 넘긴다 — pass 승격
    # 여부는 `build_verdict` → `validate_pass_requirements`가 결정하고 이 모듈은
    # 자체 pass 판정을 하지 않는다(§C.2 [MUST]).
    elif executed and scenario:
        verdict_input = e2e_scenario_adapter.build_verdict_input(
            scenario,
            status=status,
            run_id=run_id,
            assertion_results=results,
            observed_executor_types=list(observed_executor_types or []),
            observed_evidence=sorted(
                set(writer.observed(required_evidence)) | _metadata_names(required_evidence)
            ),
        )
    if operational_status != "awaiting_human":
        verdict = e2e_contract.build_verdict(
            dict(verdict_input) if verdict_input else {"status": status}
        )
        resolved_status = verdict.get("status") or status
    # 기본 경로의 `error`는 status에서만 나온다(§B.1.1 — 값은 STATUS_ERROR_CODES 안). 더
    # 세분한 계약 error는 verdict에 남고 run.json의 `verdict_error`로 기록한다.
    # `awaiting_human`은 `status`가 null인 채로 exit·error·operational_status를 갖는
    # 유일한 상태다(§B.1.1 stdout 표·§A.2.1). 값은 전부 계약 함수에서 나온다(C-125-1).
    exit_key = "awaiting_human" if operational_status == "awaiting_human" else resolved_status
    error = error_override or e2e_contract.status_to_error(exit_key)
    exit_code = e2e_contract.status_to_exit(exit_key)

    # §A.2.1 — 최종 상태는 cleanup_* **앞**에 기록된다. 조기 반환 경로들은 자기 사유와
    # 함께 이미 전이를 남겼으므로 중복해서 쌓지 않는다. [MUST] §A.2.2가 "중간 상태를
    # 건너뛴 pass"를 금지하므로, 이 전이가 빠지면 `evidence_captured` 바로 뒤에
    # `cleanup_complete`가 붙어 최종 판정이 이력에서 사라진다(MV-06 검증 대상).
    if operational_status != "awaiting_human" and journal.state != resolved_status:
        journal.to(resolved_status)
    journal.to(STATE_CLEANUP_COMPLETE if cleanup == CLEANUP_COMPLETE else STATE_CLEANUP_WARNING)

    # metadata(run.json)는 이 함수가 지금 발행하므로 관측 증적에 포함한다. 나머지는
    # 관문이 실제로 내용을 채운 종류만 돌려준다.
    observed_evidence = sorted(set(writer.observed(required_evidence)) | _metadata_names(required_evidence))
    missing_evidence = [
        item for item in required_evidence if item not in observed_evidence
    ]
    evidence_complete = not missing_evidence
    fidelity = _achieved_fidelity(
        evidence_complete=evidence_complete,
        candidates=list(candidates or []),
        handles=handles,
        ceiling=fidelity_ceiling,
    )

    urls = _urls(leases)
    target_fields = (
        context.as_run_json_fields()
        if context
        else {
            "target": None,
            "project_root": None,
            "worktree_root": None,
            "opal_home": None,
            "commit": "",
            "dirty": False,
            "dirty_files": [],
        }
    )

    run_json: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "scenario_id": scenario_id,
        "profile": (scenario or {}).get("profile"),
        "actors": list((scenario or {}).get("actors") or []),
        "surface_kind": (scenario or {}).get("surface_kind"),
        **target_fields,
        "urls": urls,
        # §A.1.1 `executors[]` — 후보 배열이 아니라 **실제로 선택된** 실행 수단이다.
        # 둘을 같은 배열로 묶으면 "무엇을 시도했는가"와 "무엇으로 실행했는가"가 섞인다.
        "executors": [
            {
                "type": item.get("type"),
                "driver": item.get("driver"),
                "session_mode": item.get("session_mode"),
                "driver_version": item.get("version"),
                "resolution_source": item.get("resolution_source"),
            }
            for item in (candidates or [])
            if item.get("outcome") == _OUTCOME_SELECTED
        ],
        "candidates": list(candidates or []),
        "driver_version": next(
            (
                item.get("version")
                for item in (candidates or [])
                if item.get("outcome") == _OUTCOME_SELECTED
                and item.get("type") == _EXECUTOR_BROWSER
            ),
            None,
        ),
        "state": final_state,
        "status": resolved_status,
        "operational_status": operational_status or _OPERATIONAL.get(resolved_status),
        "error": error,
        "exit_code": exit_code,
        "assertion_summary": (
            e2e_scenario_adapter.assertion_summary(scenario, results)
            if scenario
            else {"passed": 0, "failed": 0, "missing": 0}
        ),
        "assertion_results": results,
        "observed_executors": list(observed_executor_types or []),
        # `executed`는 "step runner가 실제로 돌았는가"다. 정적 거부(§C.4 집행 1)와
        # 실행 중 실패를 기록 위에서 구분하는 유일한 필드다.
        "executed": bool(executed),
        "verdict_error": verdict.get("error"),
        "required_evidence": list(required_evidence),
        "observed_evidence": list(observed_evidence),
        "missing_evidence": list(missing_evidence),
        "evidence_complete": evidence_complete,
        "fidelity": fidelity,
        "cleanup": cleanup,
        "artifact_dir": artifact_dir,
        "artifact_root": artifact_root,
        "lease_reclaimed": list(reclaimed),
        "lease_released": released_lease_ids,
        "started_at": started_at,
        "ended_at": _now_iso(),
        "detail_code": detail_code,
        "detail": detail,
    }
    writer.write_json(
        e2e_evidence.EVIDENCE_PATHS["journal"], journal.to_dict(), kind="journal", observed=False
    )
    writer.write_json(
        e2e_evidence.EVIDENCE_PATHS["owned"],
        {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "process_groups": [
                {"pgid": handle.spawned.pgid, "role": handle.role, "started_at": started_at}
                for handle in handles
            ],
            "leases": [
                {"lease_id": rec.lease_id, "port": rec.port, "role": rec.role} for rec in leases
            ],
            # §A.3 필수 배열. `e2e clean`이 이 대장만 보고 정리하므로(TD-15) 키는 항상
            # 존재해야 한다 — 없는 키는 "정리 대상 없음"이 아니라 대장 파손이다.
            # browser 자원은 driver가 스스로 신고한 것만 오른다(C-2).
            "browser_pages": list((owned_browser or {}).get("browser_pages") or []),
            "browser_profiles": list((owned_browser or {}).get("browser_profiles") or []),
            "cmux_surfaces": [],
            "api_fixtures": [],
            "leaked": leaked,
        },
        kind="owned",
        observed=False,
    )
    run_json_path = writer.write_json(
        e2e_evidence.EVIDENCE_PATHS["metadata"], run_json, kind="metadata", observed=True
    )
    # §A.12 redaction 결과 — 관문이 저장한 모든 artifact의 마스킹 기록.
    writer.write_json(
        e2e_evidence.EVIDENCE_PATHS["redaction"],
        {"schema_version": SCHEMA_VERSION, "run_id": run_id, "records": writer.redaction_records()},
        kind="redaction",
        observed=False,
    )

    return {
        # CONTRACT.md §B.1.1 규정 필드.
        "run_id": run_id,
        "scenario_id": scenario_id,
        "profile": run_json["profile"],
        "status": resolved_status,
        "operational_status": run_json["operational_status"],
        "error": error,
        "exit_code": exit_code,
        "run_json_path": run_json_path,
        "artifact_dir": artifact_dir,
        # 달성 충실도(`fidelity`)·`evidence_complete`·`missing_evidence`는 stdout에 얹지
        # 않는다 — §B.1.1 stdout 필드 집합은 동결돼 있고(test_e2e_runtime.py), 세 값은
        # §A.1 run.json이 소유한다. 소비자는 `run_json_path`로 읽는다.
        # 아래 5개는 §B.1.1 규정 밖이지만 동결된 RED가 stdout에서 직접 읽는다:
        # S-1이 urls·project_root를, S-2가 lease_reclaimed·candidates를,
        # S-12(b)가 executed를 소비한다. `executed`는 정적 거부를 실행 중 실패와
        # 구분하는 값이라 경로마다 모양이 달라지지 않게 **모든 run**에 싣는다.
        "executed": bool(executed),
        "urls": urls,
        "project_root": run_json["project_root"],
        "lease_reclaimed": list(reclaimed),
        "candidates": list(candidates or []),
    }


# ─────────────────────────────────────────────────────────────────────────────
# §B.1.3 `e2e status` · §B.1.4 `e2e clean`
#
# [MUST] 두 명령 모두 프로세스 이름 패턴 매칭 도구를 쓰지 않고 opal-cli의 console PID
# 파일을 보지 않는다(§C.1, TASK.md C-9). 조회는 산출물
# 디렉터리와 `.leases/` record만, 회수는 `owned.json` 대장(§A.3)에 오른 pgid·lease만
# 대상으로 한다(TD-15). 사용자 소유 자원은 애초에 대장에 오르지 않으며, 그럼에도 대장에
# `user_owned=true`로 표시된 원소가 있으면 `skipped[]`로 빼고 손대지 않는다(C-2, R-8).
# ─────────────────────────────────────────────────────────────────────────────

_JOURNAL_TAIL = 10
ERROR_RUN_NOT_FOUND = "run_not_found"

EVIDENCE_RUN_JSON = e2e_evidence.EVIDENCE_PATHS["metadata"]
EVIDENCE_OWNED_JSON = e2e_evidence.EVIDENCE_PATHS["owned"]
EVIDENCE_JOURNAL_JSON = e2e_evidence.EVIDENCE_PATHS["journal"]


def default_artifact_root() -> str:
    """`${OPAL_E2E_ARTIFACT_ROOT:-${TMPDIR}/opal-e2e-runs}`(§B.1.1 표·§C.6)."""
    return os.path.abspath(
        os.environ.get("OPAL_E2E_ARTIFACT_ROOT")
        or str(e2e_process.temp_root() / _DEFAULT_ARTIFACT_DIRNAME)
    )


def _read_json(path: Path) -> Optional[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _looks_like_run_dir(path: Path) -> bool:
    return (path / EVIDENCE_RUN_JSON).is_file() or (path / EVIDENCE_OWNED_JSON).is_file()


def _resolve_run_dir(
    *, run_id: Optional[str], artifact_dir: Optional[str], artifact_root: Optional[str]
) -> Optional[Path]:
    """run 디렉터리를 찾는다. `$OPAL_E2E_ARTIFACT_DIR` → 명시 경로 → root 하위 탐색 순.

    탐색은 `{artifact_root}/{project_id}/{run_id}` 한 단계 깊이로 제한한다 — 전역 스캔을
    하지 않는 것이 §C.1의 취지다.
    """
    if artifact_dir:
        path = Path(os.path.abspath(artifact_dir))
        return path if _looks_like_run_dir(path) else None

    env_dir = os.environ.get("OPAL_E2E_ARTIFACT_DIR")
    if env_dir:
        path = Path(os.path.abspath(env_dir))
        if _looks_like_run_dir(path):
            if not run_id:
                return path
            found = _read_json(path / EVIDENCE_RUN_JSON) or _read_json(path / EVIDENCE_OWNED_JSON)
            if found and str(found.get("run_id")) == str(run_id):
                return path

    if not run_id:
        return None
    root = Path(artifact_root or default_artifact_root())
    if not root.is_dir():
        return None
    for project_dir in sorted(root.iterdir()):
        if not project_dir.is_dir() or project_dir.name.startswith("."):
            continue
        candidate = project_dir / str(run_id)
        if candidate.is_dir() and _looks_like_run_dir(candidate):
            return candidate
    return None


def run_status(
    *,
    run_id: Optional[str] = None,
    artifact_dir: Optional[str] = None,
    artifact_root: Optional[str] = None,
) -> dict:
    """§B.1.3 — 지정 run의 상태·증적 경로를 조회한다. 아무것도 변경하지 않는다.

    전이 이력은 `journal.json`의 마지막 `_JOURNAL_TAIL`건만 싣는다(`journal_tail`).
    """
    run_dir = _resolve_run_dir(
        run_id=run_id, artifact_dir=artifact_dir, artifact_root=artifact_root
    )
    if run_dir is None:
        return {"error": ERROR_RUN_NOT_FOUND, "run_id": run_id, "artifact_dir": artifact_dir}

    run_json = _read_json(run_dir / EVIDENCE_RUN_JSON) or {}
    journal = _read_json(run_dir / EVIDENCE_JOURNAL_JSON) or {}
    transitions = journal.get("transitions")
    tail = list(transitions)[-_JOURNAL_TAIL:] if isinstance(transitions, list) else []
    owned = _read_json(run_dir / EVIDENCE_OWNED_JSON) or {}

    return {
        # §B.1.3 stdout 필드.
        "run_id": run_json.get("run_id") or owned.get("run_id") or run_id,
        "scenario_id": run_json.get("scenario_id"),
        "profile": run_json.get("profile"),
        "target": run_json.get("target"),
        "state": run_json.get("state"),
        "status": run_json.get("status"),
        "operational_status": run_json.get("operational_status"),
        "urls": run_json.get("urls") or {"frontend": None, "backend": None},
        "artifact_dir": str(run_dir),
        "journal_tail": tail,
        # 소유 자원 요약 — `e2e clean`이 무엇을 회수하게 되는지 미리 보여준다(§A.3).
        "owned": {
            "process_groups": list(owned.get("process_groups") or []),
            "leases": list(owned.get("leases") or []),
            "browser_pages": list(owned.get("browser_pages") or []),
            "cmux_surfaces": list(owned.get("cmux_surfaces") or []),
            "api_fixtures": list(owned.get("api_fixtures") or []),
        },
        "run_json_path": str(run_dir / EVIDENCE_RUN_JSON),
    }


def _skip_record(kind: str, item: dict, reason: str) -> dict:
    return {
        "kind": kind,
        "id": str(
            item.get("pgid")
            or item.get("lease_id")
            or item.get("page_id")
            or item.get("surface_handle")
            or item.get("fixture_id")
            or ""
        ),
        "reason": reason,
    }


_SKIP_USER_OWNED = "user_owned"

# `user_owned=true` 표시를 가질 수 있는 §A.3 배열. 프로세스 그룹과 lease는 하네스가
# 스스로 만든 것만 대장에 오르므로 여기 없다.
_USER_OWNABLE_ARRAYS = (
    ("browser_page", "browser_pages"),
    ("cmux_surface", "cmux_surfaces"),
    ("api_fixture", "api_fixtures"),
)


def _clean_one_run(run_dir: Path, *, artifact_root: str, dry_run: bool) -> dict:
    """run 1건의 `owned.json` 대장에 오른 자원만 회수한다(§B.1.4·TD-15)."""
    owned = _read_json(run_dir / EVIDENCE_OWNED_JSON) or {}
    terminated: List[dict] = []
    reclaimed: List[str] = []
    skipped: List[dict] = []
    leaked: List[dict] = []

    for entry in owned.get("process_groups") or []:
        if not isinstance(entry, dict):
            continue
        if entry.get("user_owned") is True:
            skipped.append(_skip_record("process_group", entry, _SKIP_USER_OWNED))
            continue
        pgid = entry.get("pgid")
        if not isinstance(pgid, int):
            continue
        if not e2e_process.pid_alive(pgid):
            terminated.append({"pgid": pgid, "role": entry.get("role"), "method": "already_gone"})
            continue
        if dry_run:
            terminated.append({"pgid": pgid, "role": entry.get("role"), "method": "dry_run"})
            continue
        # pgid 단위 회수만 쓴다 — 이름 패턴으로 프로세스를 찾지 않는다(§C.1).
        result = e2e_process.terminate_process_group(pgid)
        terminated.append({"pgid": pgid, "role": entry.get("role"), "method": result.method})
        if result.leaked:
            leaked.append({"kind": "process_group", "id": str(pgid), "members": result.leaked})

    for entry in owned.get("leases") or []:
        if not isinstance(entry, dict):
            continue
        if entry.get("user_owned") is True:
            skipped.append(_skip_record("lease", entry, _SKIP_USER_OWNED))
            continue
        lease_id = entry.get("lease_id")
        if not lease_id:
            continue
        if not dry_run:
            e2e_ports.release_lease(artifact_root, str(lease_id))
        reclaimed.append(str(lease_id))

    for kind, key in _USER_OWNABLE_ARRAYS:
        for entry in owned.get(key) or []:
            if isinstance(entry, dict) and entry.get("user_owned") is True:
                skipped.append(_skip_record(kind, entry, _SKIP_USER_OWNED))

    return {
        "run_id": owned.get("run_id"),
        "terminated_process_groups": terminated,
        "reclaimed_leases": reclaimed,
        "skipped": skipped,
        "leaked": leaked,
    }


def _remove_tree(path: Path, *, artifact_root: str) -> bool:
    """artifact root **안쪽** 경로만 지운다(§C.6, TASK.md C-2·C-5).

    `$OPAL_E2E_ARTIFACT_DIR`가 root 밖을 가리키고 있어도 회수가 그쪽으로 새지 않게
    삭제 직전에 봉쇄한다 — run 디렉터리처럼 보인다는 것만으로는 삭제 근거가 되지 않는다.
    """
    import shutil

    try:
        resolved = path.resolve()
        root = Path(artifact_root).resolve()
        resolved.relative_to(root)
    except (OSError, ValueError):
        return False
    try:
        shutil.rmtree(str(resolved))
    except OSError:
        return False
    return True


def run_clean(
    *,
    run_id: Optional[str] = None,
    stale: bool = False,
    artifact_root: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """§B.1.4 — `owned.json` 대장에 오른 자원만 회수한다. exit은 호출자가 항상 0으로 준다.

    [MUST] `user_owned=true`인 원소는 `skipped[]`로 빠지고 손대지 않는다(C-2, R-8).
    [MUST] 회수 후에도 프로세스 그룹이 남으면(`leaked`) cleanup 결과를 `infra_error`로
    승격한다 — 누출은 다음 실행을 오염시키므로 "정리했다"로 기록할 수 없다(§A.6.1).
    승격은 payload의 `status`로 알리고 exit 값을 새로 배정하지 않는다(§B.1.4 exit=0).
    """
    root = os.path.abspath(artifact_root or default_artifact_root())
    reclaimed_leases: List[str] = []
    terminated: List[dict] = []
    removed_dirs: List[str] = []
    skipped: List[dict] = []
    leaked: List[dict] = []

    targets: List[Path] = []
    if run_id:
        run_dir = _resolve_run_dir(run_id=run_id, artifact_dir=None, artifact_root=root)
        if run_dir is None:
            return {
                "error": ERROR_RUN_NOT_FOUND,
                "run_id": run_id,
                "reclaimed_leases": [],
                "terminated_process_groups": [],
                "removed_artifact_dirs": [],
                "skipped": [],
                "status": STATUS_BLOCKED,
            }
        targets.append(run_dir)

    if stale:
        # C-LEASE-2 — owner_pid가 살아 있지 않은 record가 대상이다. 어떤 run의 것인지
        # record가 스스로 말하므로(§A.7 `run_id`) 전역 스캔 없이 run 디렉터리를 찾는다.
        lease_dir = e2e_ports.lease_dir_for(root)
        stale_run_ids = {
            str(data.get("run_id"))
            for _, data in e2e_ports.read_leases(lease_dir)
            if isinstance(data.get("owner_pid"), int)
            and not e2e_process.pid_alive(int(data["owner_pid"]))
        }
        for stale_run_id in sorted(stale_run_ids):
            found = _resolve_run_dir(run_id=stale_run_id, artifact_dir=None, artifact_root=root)
            if found is not None and found not in targets:
                targets.append(found)
        if not dry_run:
            reclaimed_leases.extend(e2e_ports.reclaim_stale_leases(lease_dir))

    for target in targets:
        report = _clean_one_run(target, artifact_root=root, dry_run=dry_run)
        terminated.extend(report["terminated_process_groups"])
        reclaimed_leases.extend(
            item for item in report["reclaimed_leases"] if item not in reclaimed_leases
        )
        skipped.extend(report["skipped"])
        leaked.extend(report["leaked"])
        if report["leaked"]:
            # 누출된 프로세스가 남은 run의 산출물은 지우지 않는다 — 원인을 남긴다.
            continue
        if dry_run or _remove_tree(target, artifact_root=root):
            removed_dirs.append(str(target))

    status = STATUS_INFRA_ERROR if leaked else None
    return {
        # §B.1.4 stdout 필드.
        "reclaimed_leases": reclaimed_leases,
        "terminated_process_groups": terminated,
        "removed_artifact_dirs": removed_dirs,
        "skipped": skipped,
        # 승격 기록. exit은 §B.1.4대로 0이며 새 exit 값을 만들지 않는다.
        "leaked": leaked,
        "escalated_to_infra_error": bool(leaked),
        "status": status,
        "error": e2e_contract.status_to_error(status) if status else None,
        "dry_run": bool(dry_run),
        "artifact_root": root,
    }
