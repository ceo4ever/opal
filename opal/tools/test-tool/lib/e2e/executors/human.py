"""
@header {
  "module": "human",
  "layer": "util",
  "domain": "opal-tools",
  "description": "T10 Human handoff executor — CONTRACT.md §B.3 handoff·resume 2연산. 발행 시점에 server_policy를 §A.9 enum(keep|terminate)으로 정규화하고(MV-17) 선언 원문·정규화 사실을 함께 보존한다. collaborative/manual 시나리오를 awaiting_human(exit 20)으로 일시 정지하며 §A.9 handoff 8필드와 §A.2.3 journal resume를 보존하고, 동일 run-id + resume token 재개의 판정은 새 경로를 만들지 않고 lib/scenario.py:482-528의 기존 resume 검증을 호출한다(TRD.md TD-18). timeout은 fail이 아니라 blocked(exit 19)로 끝내고 토큰 만료를 기록한다(C-HUM-2).",
  "exports": [
    "HumanExecutor", "SERVER_POLICY_KEEP", "SERVER_POLICY_TERMINATE",
    "HUMAN_DIR", "HANDOFF_PATH", "RESUME_INDEX_PATH", "DEFAULT_SUBMISSION_PATH",
    "build_handoff", "build_resume_state", "server_action", "normalize_server_policy", "is_expired",
    "mark_awaiting_human", "invoke_scenario_resume", "run_resume", "register"
  ]
}

lib.e2e.executors.human — 이 모듈은 판정을 만들지 않는다. `pass`/`fail`/`blocked`는
`e2e_contract`와 `scenario.py`의 기존 함수가 돌려준 값을 그대로 옮기며, 재개 검증은
`scenario.py`의 `cmd_scenario_mark` resume 분기(:482-528)를 **직접 호출**한다 —
`scenario.py`는 변경 0이고 새 resume 판정 경로도 만들지 않는다(§C.2 [MUST], TASK.md C-1).

집행 규칙:
- C-HUM-1 [MUST]: `manual`도 자유 형식 응답을 받지 않는다. §A.9 8필드가 전건 채워지지
  않으면 handoff를 발행하지 않는다 — 필수 필드 목록은 `e2e_contract.HANDOFF_REQUIRED_FIELDS`
  단일 SSOT에서 읽고 여기서 복제하지 않는다.
- C-HUM-2 [MUST]: timeout 경과는 자동 `fail`이 아니라 `blocked`이며 만료 여부를
  §A.2.3 `journal.json.resume.expired`에 기록한다.
- §A.9 enum 집행 [MUST]: 발행하는 `server_policy`는 반드시 `keep`|`terminate`다
  (MV-17, §A.2.3 `CONTRACT.md:187`). enum 밖 선언값은 보수적으로 `keep`으로 정규화해
  발행하되(TASK.md C-2), 선언 원문(`server_policy_declared`)과 정규화 사실
  (`server_policy_normalized`)을 함께 남긴다 — 조용한 대체를 만들지 않는다.
  세 키의 의미는 `handoff.json`·`journal.json.resume`·`human/resume.json`에서 동일하다:
  `server_policy`는 어디서나 **발행값**이고 원문은 어디서나 `server_policy_declared`다.
- R-13 [MUST]: 사람의 `completed: true`는 pass 선언이 아니다. 재개 후
  `validate_pass_requirements`를 다시 통과해야 pass가 된다(§A.10).
- §C.3: 이 executor의 소유물은 handoff/submission artifact뿐이다. 사람의 브라우저
  세션·인증 상태는 소유하지도 정리하지도 않는다.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import pathlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Mapping, Optional, Tuple

from lib import e2e_contract
from lib.e2e import executors as e2e_executors

SCHEMA_VERSION = e2e_executors.SCHEMA_VERSION

EXECUTOR_TYPE = "human"
ACTOR_HUMAN = "human"

# §A.9 `server_policy` enum. 이 계약이 확정한 두 값이며 여기서 확장하지 않는다.
SERVER_POLICY_KEEP = "keep"
SERVER_POLICY_TERMINATE = "terminate"
SERVER_POLICIES: Tuple[str, ...] = (SERVER_POLICY_KEEP, SERVER_POLICY_TERMINATE)

# §A.9·§A.10 경로. artifact 디렉터리 하위에만 쓴다(TASK.md C-5, §C.6).
HUMAN_DIR = "human"
HANDOFF_PATH = f"{HUMAN_DIR}/handoff.json"
DEFAULT_SUBMISSION_PATH = f"{HUMAN_DIR}/submission.json"
# executor 내부 재개 색인. §A.9/§A.2.3의 필드 집합을 바꾸지 않으려고 별도 파일에 둔다 —
# `e2e resume`는 §B.1.2가 확정한 3인자만 받으므로 task_path·scenario_id를 run 쪽에
# 남겨 두지 않으면 재개 시 시나리오를 찾을 방법이 없다.
RESUME_INDEX_PATH = f"{HUMAN_DIR}/resume.json"

# §A.1 status / §A.2.1 상태. 리터럴로 만들지 않고 계약 소유 튜플에서 조회한다(C-125-1).
_FINAL = {name: name for name in e2e_contract.FINAL_STATUSES}
_OPERATIONAL = {name: name for name in e2e_contract.OPERATIONAL_STATUSES}
STATUS_BLOCKED = _FINAL["blocked"]
STATUS_PASS = _FINAL["pass"]
STATUS_FAIL = _FINAL["fail"]
STATUS_AWAITING_HUMAN = _OPERATIONAL["awaiting_human"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def _parse_iso(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def server_action(server_policy: Any) -> str:
    """§A.9 — `terminate`만 정리 후 넘기고 그 밖의 값은 보수적으로 `keep`이다.

    시나리오 spec은 동결돼 있어 계약 enum 밖의 값이 들어올 수 있다(`test-scenario.json`
    locked). 알 수 없는 정책에서 프로세스를 죽이는 쪽으로 기울면 사용자 자원을 건드릴
    위험이 생기므로, 판단 불가는 **아무것도 종료하지 않는 쪽**으로 떨어뜨린다(TASK.md C-2).
    """
    return SERVER_POLICY_TERMINATE if server_policy == SERVER_POLICY_TERMINATE else SERVER_POLICY_KEEP


def normalize_server_policy(declared: Any) -> Tuple[str, bool]:
    """발행값 정규화 — `(emitted, normalized)`.

    §A.9가 `server_policy` enum을 `keep`|`terminate`로 확정하고 MV-17이 **발행된
    `handoff.json`의 값**을 검사한다. 동결 시나리오가 enum 밖 값을 들고 있어도 산출물에
    그대로 흘려보내면 MV-17이 깨지므로, 발행 시점에 enum 안으로 정규화한다.

    [MUST] 정규화 기본값은 `keep`이다 — 판단 불가에서 프로세스를 종료하는 쪽으로 기울면
    사용자 소유 자원을 건드릴 수 있다(TASK.md C-2).
    [MUST] 조용히 바꾸지 않는다. 선언 원문과 정규화 사실은 handoff와 §A.2.3 journal
    resume 양쪽에 함께 남아 추적 가능하다.
    """
    emitted = server_action(declared)
    return emitted, declared not in SERVER_POLICIES


# ─── §A.9 handoff ────────────────────────────────────────────────────────────
def build_handoff(
    *,
    run_id: str,
    scenario_id: str,
    step_id: str,
    handoff_spec: Optional[Mapping[str, Any]],
    artifact_dir: Optional[str] = None,
    issued_at: Optional[str] = None,
) -> Dict[str, Any]:
    """§A.9 `handoff.json` 본문을 만든다. 8필드가 전건 채워지지 않으면 발행하지 않는다.

    필수 8필드 목록은 `e2e_contract.HANDOFF_REQUIRED_FIELDS`가 소유한다(§A.9 표 각주) —
    이 함수는 그 튜플을 순회할 뿐 자기 목록을 갖지 않는다.
    """
    spec: Mapping[str, Any] = handoff_spec or {}
    merged: Dict[str, Any] = {key: spec.get(key) for key in e2e_contract.HANDOFF_REQUIRED_FIELDS}
    if not merged.get("submission_path") and artifact_dir:
        merged["submission_path"] = str(pathlib.Path(artifact_dir) / DEFAULT_SUBMISSION_PATH)
    if isinstance(merged.get("timeout_seconds"), str):
        with contextlib.suppress(ValueError):
            merged["timeout_seconds"] = int(merged["timeout_seconds"])

    missing = [
        field
        for field in e2e_contract.HANDOFF_REQUIRED_FIELDS
        if merged.get(field) in (None, "", [], {})
    ]
    if missing:
        raise e2e_executors.ExecutorError(
            "handoff_contract_incomplete",
            f"handoff is missing required fields {missing} (§A.9, C-HUM-1)",
        )
    if not isinstance(merged["timeout_seconds"], int) or merged["timeout_seconds"] <= 0:
        raise e2e_executors.ExecutorError(
            "handoff_timeout_invalid", "timeout_seconds must be a positive integer (§A.9)"
        )

    # §A.9 enum 집행은 **발행 시점**이다. 선언 원문은 버리지 않고 나란히 남긴다 —
    # MV-17은 `server_policy`를, 추적은 `server_policy_declared`를 본다.
    declared_policy = merged["server_policy"]
    emitted_policy, policy_normalized = normalize_server_policy(declared_policy)
    merged["server_policy"] = emitted_policy
    merged["server_policy_declared"] = declared_policy
    merged["server_policy_normalized"] = policy_normalized

    merged["actor"] = ACTOR_HUMAN
    merged["run_id"] = str(run_id)
    merged["scenario_id"] = str(scenario_id)
    merged["step_id"] = str(step_id)
    merged["issued_at"] = issued_at or _iso(_now())
    return merged


def build_resume_state(handoff: Mapping[str, Any], *, resumed_at: Optional[str] = None,
                       expired: bool = False) -> Dict[str, Any]:
    """§A.2.3 `journal.json.resume` 객체. `expires_at = issued_at + timeout_seconds`.

    키 의미는 `handoff.json`과 **동일하다**. `server_policy`는 어느 산출물에서나
    **발행값**(§A.2.3 `CONTRACT.md:187`·§A.9 enum 안)이고, 선언 원문은 언제나
    `server_policy_declared`다 — 같은 키 이름이 산출물마다 다른 것을 가리키면 읽는
    쪽이 틀린다.

    정규화 전/후 세 정보는 그대로 유지한다: 발행값·선언 원문·대체 발생 여부.
    """
    issued = _parse_iso(handoff.get("issued_at")) or _now()
    expires = issued + timedelta(seconds=int(handoff.get("timeout_seconds") or 0))
    emitted = handoff.get("server_policy")
    declared = handoff.get("server_policy_declared", emitted)
    return {
        "resume_token": handoff.get("resume_token"),
        "issued_at": _iso(issued),
        "expires_at": _iso(expires),
        "expired": bool(expired),
        # §A.2.3 [MUST] — enum 안의 발행값이다. handoff.json의 같은 키와 같은 값이다.
        "server_policy": emitted,
        # 선언 원문. 하네스가 추적 정보를 재작문하지 않는다(NR-7).
        "server_policy_declared": declared,
        "server_policy_normalized": bool(
            handoff.get("server_policy_normalized", declared != emitted)
        ),
        "resumed_at": resumed_at,
    }


def is_expired(resume_state: Mapping[str, Any], *, at: Optional[datetime] = None) -> bool:
    """§A.2.3 — `expires_at` 경과 여부. 해석 불가한 값은 만료로 보지 않는다."""
    expires = _parse_iso(resume_state.get("expires_at"))
    if expires is None:
        return False
    return (at or _now()) >= expires


# ─── §B.3 human executor ─────────────────────────────────────────────────────
class HumanExecutor(e2e_executors.Executor):
    """§B.3 Human handoff executor. 증적은 생성자로 받은 관문으로만 발행한다(C-EXE-3)."""

    executor_type = EXECUTOR_TYPE
    operations = e2e_executors.HUMAN_OPERATIONS
    capability_keys = e2e_executors.HUMAN_CAPABILITY_KEYS

    def __init__(
        self,
        *,
        runtime_context: Optional[Mapping[str, Any]] = None,
        writer: Any = None,
        action_log: Optional[e2e_executors.ActionLog] = None,
    ):
        context = dict(runtime_context or {})
        self.runtime_context = context
        self.binary_path = None
        self.resolution_source = e2e_executors.RESOLUTION_SOURCE_INPROCESS
        self.declared_version = None
        self.artifact_dir = context.get("artifact_dir")
        self.task_path = context.get("task_path")
        self._writer = writer if writer is not None else context.get("writer")
        self._log = action_log or context.get("action_log") or e2e_executors.ActionLog()
        self.resume_state: Optional[Dict[str, Any]] = None

    @property
    def action_log(self) -> e2e_executors.ActionLog:
        return self._log

    def executor_record(self) -> Dict[str, Any]:
        """§A.1.1 `executors[]` 원소."""
        return {
            "type": EXECUTOR_TYPE,
            "driver": None,
            "session_mode": None,
            "driver_version": None,
            "client": None,
        }

    def op_probe(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """사람 인계는 artifact 디렉터리에 쓸 수 있는지로만 가용성이 결정된다.

        가용성 근거를 실제로 확인한 것만 `probed=true`로 올린다(C-EXE-1) — 사람이
        존재한다는 가정은 probe의 근거가 아니다.
        """
        writable = bool(self.artifact_dir) and pathlib.Path(str(self.artifact_dir)).is_dir()
        return {
            "executor": EXECUTOR_TYPE,
            "available": writable,
            "version": None,
            "unavailable_reason": None if writable else "human_artifact_dir_absent",
            "capabilities": {
                key: {"available": writable, "route": "native", "probed": True}
                for key in self.capability_keys
            },
        }

    def op_handoff(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{run_id, scenario_id, step_id, handoff_spec}` → §A.9 `handoff.json` 전체.

        발행 후 run은 `awaiting_human`으로 정지하고 exit 20으로 제어를 넘긴다 — 상태와
        exit은 호출자가 `e2e_contract`에서 조회한다(이 모듈은 값을 만들지 않는다).
        """
        handoff = build_handoff(
            run_id=str(request.get("run_id") or ""),
            scenario_id=str(request.get("scenario_id") or ""),
            step_id=str(request.get("step_id") or "handoff"),
            handoff_spec=request.get("handoff_spec"),
            artifact_dir=self.artifact_dir,
        )
        self.resume_state = build_resume_state(handoff)

        writer = self._require_writer()
        writer.write_json(HANDOFF_PATH, handoff, kind=None, observed=False)
        writer.write_json(
            RESUME_INDEX_PATH,
            {
                "schema_version": SCHEMA_VERSION,
                "run_id": handoff["run_id"],
                "scenario_id": handoff["scenario_id"],
                "task_path": str(self.task_path) if self.task_path else None,
                "artifact_dir": str(self.artifact_dir) if self.artifact_dir else None,
                "handoff_id": handoff["handoff_id"],
                "submission_path": handoff["submission_path"],
                "resume": self.resume_state,
            },
            kind=None,
            observed=False,
        )
        self._log.record(
            step_id=handoff["step_id"],
            executor=EXECUTOR_TYPE,
            action="handoff",
            step_role=e2e_executors.STEP_ROLE_VERIFY,
            result="ok",
            elapsed_ms=0,
        )
        return handoff

    def op_resume(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """`{run_id, resume_token, submission_path}` → `{accepted, status, error, verifier_results[]}`.

        판정은 이 함수가 내리지 않는다. `scenario.py`의 기존 resume 분기를 호출하고 그
        결과를 옮긴다(TD-18).
        """
        outcome = run_resume(
            run_id=str(request.get("run_id") or ""),
            token=str(request.get("resume_token") or ""),
            submission=str(request.get("submission_path") or ""),
            artifact_dir=self.artifact_dir,
            task_path=request.get("task_path") or self.task_path,
            scenario_id=request.get("scenario_id"),
        )
        self._log.record(
            step_id=str(request.get("step_id") or "resume"),
            executor=EXECUTOR_TYPE,
            action="resume",
            step_role=e2e_executors.STEP_ROLE_VERIFY,
            result="ok" if outcome["status"] == STATUS_PASS else "error",
            elapsed_ms=0,
            error_code=outcome.get("error"),
        )
        return {
            "accepted": outcome["status"] == STATUS_PASS,
            "status": outcome["status"],
            "error": outcome["error"],
            "verifier_results": outcome["verifier_results"],
        }

    def _require_writer(self) -> Any:
        if self._writer is None:
            raise e2e_executors.ExecutorError(
                "human_evidence_writer_absent",
                "handoff requires an EvidenceWriter — executors never write files directly (§C.2)",
            )
        return self._writer


# ─── scenario.py 기존 경로 호출 (TD-18) ──────────────────────────────────────
def _call_scenario_mark(namespace: argparse.Namespace) -> Tuple[int, Dict[str, Any]]:
    """`scenario.py`의 `cmd_scenario_mark`를 그대로 호출하고 결과를 돌려준다.

    `cmd_scenario_mark`는 CLI 핸들러라 stdout에 JSON을 쓰고 `sys.exit`로 끝난다. 그
    계약을 바꾸지 않고 쓰기 위해 stdout을 붙잡고 `SystemExit`를 받아낸다 — 판정 로직을
    복제하거나 우회하는 분기를 만들지 않는 유일한 방법이다(§C.2 "새 resume 판정 경로
    신설" 금지, CONTRACT.md §B.1.2).
    """
    from lib import scenario as scenario_module

    buffer = io.StringIO()
    exit_code = 0
    try:
        with contextlib.redirect_stdout(buffer):
            scenario_module.cmd_scenario_mark(namespace)
    except SystemExit as exc:
        exit_code = int(exc.code or 0)
    raw = buffer.getvalue().strip()
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {"ok": False, "error": "resume_verification_failed", "detail": raw}
    return exit_code, payload


def _mark_namespace(task_path: str, scenario_id: str, **overrides: Any) -> argparse.Namespace:
    """`scenario-mark` 서브파서가 만들어 주는 Namespace와 같은 형태를 만든다."""
    values: Dict[str, Any] = {
        "task_path": str(task_path),
        "id": str(scenario_id),
        "result": None,
        "evidence": None,
        "fidelity": None,
        "verdict_json": None,
        "resume_run_id": None,
        "resume_token": None,
        "submission": None,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def mark_awaiting_human(
    *,
    task_path: str,
    scenario_id: str,
    run_id: str,
    handoff: Mapping[str, Any],
    verdict_path: str,
) -> Tuple[int, Dict[str, Any]]:
    """`awaiting_human`을 시나리오 result존에 기록한다(`scenario.py:456-466` 기존 분기).

    이 기록이 있어야 나중의 `e2e resume`가 같은 run_id·token을 대조할 수 있다. 기록
    경로는 기존 `--verdict-json` 분기이며 새 분기를 만들지 않는다.
    """
    payload = {
        "status": STATUS_AWAITING_HUMAN,
        "run_id": str(run_id),
        "profile": None,
        "handoff_state": dict(handoff),
    }
    path = pathlib.Path(verdict_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return _call_scenario_mark(
        _mark_namespace(task_path, scenario_id, verdict_json=str(path))
    )


def invoke_scenario_resume(
    *,
    task_path: str,
    scenario_id: str,
    run_id: str,
    token: str,
    submission: str,
) -> Tuple[int, Dict[str, Any]]:
    """`scenario.py:482-528` resume 분기를 그대로 호출한다(§B.1.2, TD-18).

    [MUST] 사람의 제출만으로는 pass가 되지 않는다 — 저 분기가 `validate_pass_requirements`를
    다시 통과시킨 뒤에야 `pass`를 돌려준다(R-13, §A.10).
    """
    return _call_scenario_mark(
        _mark_namespace(
            task_path,
            scenario_id,
            resume_run_id=str(run_id),
            resume_token=str(token),
            submission=str(submission),
        )
    )


# ─── §B.1.2 `test-tool e2e resume` ───────────────────────────────────────────
def load_resume_index(
    *,
    run_id: str,
    artifact_dir: Optional[str] = None,
    artifact_root: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """handoff가 남긴 재개 색인을 찾는다. 없으면 None."""
    for candidate in _resume_index_candidates(run_id, artifact_dir, artifact_root):
        if candidate.is_file():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return None
    return None


def _resume_index_candidates(
    run_id: str, artifact_dir: Optional[str], artifact_root: Optional[str]
) -> List[pathlib.Path]:
    paths: List[pathlib.Path] = []
    if artifact_dir:
        paths.append(pathlib.Path(artifact_dir) / RESUME_INDEX_PATH)
    if artifact_root:
        root = pathlib.Path(artifact_root)
        paths.append(root / RESUME_INDEX_PATH)
        paths.append(root / run_id / RESUME_INDEX_PATH)
        with contextlib.suppress(OSError):
            for project_dir in sorted(root.iterdir()):
                if project_dir.is_dir():
                    paths.append(project_dir / run_id / RESUME_INDEX_PATH)
    return paths


def run_resume(
    *,
    run_id: str,
    token: str,
    submission: str,
    artifact_root: Optional[str] = None,
    artifact_dir: Optional[str] = None,
    task_path: Optional[str] = None,
    scenario_id: Optional[str] = None,
    at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """`test-tool e2e resume`의 본체. §B.1.2 stdout payload를 돌려준다.

    순서가 계약이다.
    1. 재개 색인을 찾지 못하면 `blocked` — 판정할 시나리오를 모르면 fail이 아니다.
    2. token 만료는 `blocked`(exit 19)이며 `journal.resume.expired=true`를 남긴다(C-HUM-2).
    3. 그 밖에는 `scenario.py`의 기존 resume 검증에 전적으로 위임한다(TD-18).
    """
    index = load_resume_index(
        run_id=run_id, artifact_dir=artifact_dir, artifact_root=artifact_root
    )
    resolved_task_path = task_path or (index or {}).get("task_path")
    resolved_scenario = scenario_id or (index or {}).get("scenario_id")
    resolved_artifact_dir = artifact_dir or (index or {}).get("artifact_dir") or ""

    if not resolved_task_path or not resolved_scenario:
        return _payload(
            run_id=run_id,
            scenario_id=resolved_scenario,
            status=STATUS_BLOCKED,
            artifact_dir=resolved_artifact_dir,
            detail_code="e2e_resume_state_not_found",
            verifier_results=[],
        )

    resume_state = dict((index or {}).get("resume") or {})
    if resume_state and is_expired(resume_state, at=at):
        # C-HUM-2 [MUST] — timeout은 fail이 아니라 blocked다. 만료 사실을 남긴다.
        resume_state["expired"] = True
        _record_expiry(resolved_artifact_dir, run_id, resume_state)
        return _payload(
            run_id=run_id,
            scenario_id=resolved_scenario,
            status=STATUS_BLOCKED,
            artifact_dir=resolved_artifact_dir,
            detail_code="e2e_resume_token_expired",
            verifier_results=[],
        )

    exit_code, mark_payload = invoke_scenario_resume(
        task_path=str(resolved_task_path),
        scenario_id=str(resolved_scenario),
        run_id=run_id,
        token=token,
        submission=submission,
    )
    status = mark_payload.get("status") or (STATUS_PASS if exit_code == 0 else STATUS_FAIL)
    verifier_results = _verifier_results(submission, mark_payload)
    payload = _payload(
        run_id=run_id,
        scenario_id=resolved_scenario,
        status=str(status),
        artifact_dir=resolved_artifact_dir,
        detail_code=mark_payload.get("error"),
        verifier_results=verifier_results,
    )
    payload["profile"] = mark_payload.get("profile") or payload["profile"]
    return payload


def _verifier_results(submission: str, mark_payload: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """§B.1.2 `verifier_results[]` — 제출물의 assertion 결과를 그대로 옮긴다.

    사람이 보낸 값을 하네스가 판정으로 승격하지 않는다. `passed`는 `scenario.py`가
    통과시킨 뒤에만 의미를 갖는다(R-13).
    """
    try:
        payload = json.loads(pathlib.Path(submission).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    accepted = mark_payload.get("ok") is True
    results: List[Dict[str, Any]] = []
    for item in payload.get("assertion_results") or []:
        if not isinstance(item, Mapping):
            continue
        results.append(
            {
                "id": item.get("id"),
                "verifier": item.get("verifier") or "human",
                "expected": item.get("expected"),
                "actual": item.get("actual"),
                "passed": bool(item.get("passed")) and accepted,
            }
        )
    return results


def _record_expiry(artifact_dir: str, run_id: str, resume_state: Mapping[str, Any]) -> None:
    """§A.2.3 — 만료를 `journal.json.resume`에 남긴다. 실패해도 판정을 바꾸지 않는다.

    이 시점에는 run이 이미 끝나 증적 관문(writer)이 살아 있지 않다. journal은 하네스가
    만든 구조화 JSON이고 사람 제출물·헤더를 담지 않으므로 비밀값이 새로 들어올 표면이
    아니다 — 그래서 관문 없이 기존 파일의 `resume` 키만 갱신한다.
    """
    if not artifact_dir:
        return
    path = pathlib.Path(artifact_dir) / "journal.json"
    try:
        journal = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        journal = {"schema_version": SCHEMA_VERSION, "run_id": run_id, "transitions": []}
    journal["resume"] = dict(resume_state)
    with contextlib.suppress(OSError, TypeError, ValueError):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(journal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _payload(
    *,
    run_id: str,
    scenario_id: Optional[str],
    status: str,
    artifact_dir: str,
    detail_code: Optional[str],
    verifier_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """§B.1.2 stdout — `e2e run`과 같은 형태 + `verifier_results`.

    status·error·exit은 전부 `e2e_contract` 함수 반환값이며 여기서 값을 만들지 않는다.
    """
    operational = _OPERATIONAL.get(status)
    run_json = str(pathlib.Path(artifact_dir) / "run.json") if artifact_dir else None
    return {
        "run_id": run_id,
        "scenario_id": scenario_id,
        "profile": None,
        "status": None if operational else status,
        "operational_status": operational,
        "error": e2e_contract.status_to_error(status),
        "exit_code": e2e_contract.status_to_exit(status),
        "run_json_path": run_json,
        "artifact_dir": artifact_dir,
        "detail_code": detail_code,
        "verifier_results": verifier_results,
    }


def register() -> None:
    """레지스트리에 `human` executor를 등록한다(import 부작용으로 자동 등록하지 않는다)."""
    e2e_executors.register_executor(
        EXECUTOR_TYPE, lambda **kwargs: HumanExecutor(**kwargs)
    )
