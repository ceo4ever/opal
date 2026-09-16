"""
@header {
  "module": "verifier_adapter",
  "task": "132",
  "layer": "util",
  "domain": "oppb-runtime",
  "description": "OPPB Verifier evidence adapter(W-24) — 제안서 §10 검증 시점표의 조건부 Verifier 호출 시점(ACCEPT·위험 ACCEPT·계약 폐쇄·PROJECT VERIFY)을 workgraph 사실만으로 판정하고, §4.2 매핑표의 기존 검증 자산(`opal-test-agent`의 e2e·be·fe mode, `op-gc-security`, `op-gc-convention`)을 **기존 입력 계약 그대로** 채운 dispatch payload를 만들며, 그 워커들이 낸 보고서를 Evidence schema 문서로 변환해 Evidence Tool(W-9)에 제출한다. 세 워커의 AGENT.md·SKILL.md는 이 모듈이 읽지도 고치지도 않는다(C-2) — 입력 키 집합만 코드 상수로 고정한다. scope_hash는 workgraph가 공표한 값을 복사하며, 직접 계산이 필요하면 `controller.compute_scope_hash`만 호출하고 재구현하지 않는다. verifier attempt id는 항상 해당 미니 태스크의 `runner_attempt_id`와 다르게 발급하고, 호출자가 같은 값을 명시하면 색인 이전에 `verifier_attempt_not_independent`로 거부한다(수용기준 9). `evidence/<scope>/<evidence-id>.json` 색인·schema·code head·scope hash 검사는 전적으로 evidence.py가 수행한다 — 이 모듈은 evidence.py의 공개 export(`evidence_command`)만 호출하고 색인 경로에 직접 쓰지 않는다. Git 쓰기를 하지 않는 read-only 경로다(`git rev-parse HEAD` 조회만 한다). 표준 라이브러리와 git CLI만 사용한다.",
  "exports": [
    "ERROR_CODES", "VerifierAdapterError",
    "VERIFIER_KINDS", "TRIGGERS", "RISK_SIGNALS", "VERIFIER_ASSETS",
    "decide_verifiers", "build_evidence_document", "verifier_command"
  ],
  "depends": [
    "git CLI 2.x",
    "opal/tools/oppb-runtime-tool/controller.py",
    "opal/tools/oppb-runtime-tool/evidence.py",
    "opal/core/references/harness/gc-finding-schema.md",
    "opal/core/references/harness/tool-output-contract.md"
  ]
}
"""

# 표준 라이브러리만 사용한다. oppl-runtime-tool은 import하지 않고 플랫폼 분기도 두지 않는다.
from __future__ import annotations

import contextlib
import datetime
import json
import os
import pathlib
import shlex
import subprocess
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import controller  # noqa: E402 — 동일 디렉토리 모듈, sys.path 보정 뒤 로드
import evidence  # noqa: E402 — 동일 디렉토리 모듈, sys.path 보정 뒤 로드

EXIT_ERROR = 1
EXIT_USAGE = 2

VERIFIER_SUBCOMMANDS = ("plan", "submit")

# §4.2 매핑표의 세 검증 자산. kind는 evidence 문서의 `verifier.kind`가 된다.
VERIFIER_KINDS = ("integration", "security", "convention")

# §10 검증 시점표의 호출 시점. `accept`는 신호에 따라 `risk_accept`로 승격될 수 있다.
TRIGGERS = ("accept", "risk_accept", "contract_closure", "project_verify")

# §10 "위험 ACCEPT" 행의 판정 신호 — 새 I/O·인증·권한·외부 입력·명령 실행.
RISK_SIGNALS = (
    "io",
    "auth",
    "authz",
    "external_input",
    "command_execution",
)

# 세 워커의 **기존** 입력 계약. 이 집합을 늘리거나 줄이면 스킬·에이전트를 고쳐야 하므로
# 여기서 고정하고, 값만 workgraph·run.json 사실로 채운다(D2·C-2).
VERIFIER_ASSETS = {
    "integration": {
        "agent": "opal-test-agent",
        "skill": None,
        "input_keys": ("mode", "test_mode", "changed_files", "project_root"),
    },
    "security": {
        "agent": "opal-security-checker",
        "skill": "op-gc-security",
        "input_keys": ("project_root", "target_files", "output_dir", "timestamp"),
    },
    "convention": {
        "agent": "opal-convention-checker",
        "skill": "op-gc-convention",
        "input_keys": ("project_root", "target_files", "output_dir", "timestamp"),
    },
}

# `opal-test-agent`의 test_mode 허용값(AGENT.md 입력 파라미터표). red는 RED-first 전용이라
# Verifier 경로에서는 부르지 않는다.
TEST_MODES = ("e2e", "be", "fe")
DEFAULT_TEST_MODE = "e2e"
DEFAULT_TEST_DEPTH = "full-simple"

ERROR_CODES = {
    "run_root_missing": "--run-root는 필수입니다.",
    "run_root_not_absolute": "--run-root는 절대경로여야 합니다.",
    "run_root_not_found": "--run-root 경로가 존재하지 않습니다.",
    "run_manifest_missing": "run root에 run.json이 없습니다 — init을 먼저 실행하십시오.",
    "task_id_missing": "--task-id는 필수입니다.",
    "verifier_trigger_missing": "--trigger는 필수입니다.",
    "verifier_trigger_unknown": "알 수 없는 검증 시점입니다.",
    "verifier_kind_missing": "--kind는 필수입니다.",
    "verifier_kind_unknown": "알 수 없는 Verifier 종류입니다.",
    "verifier_test_mode_unknown": "--test-mode가 opal-test-agent의 허용값 밖입니다.",
    "verifier_report_missing": "--report는 필수입니다.",
    "verifier_report_not_absolute": "--report는 절대경로여야 합니다.",
    "verifier_report_not_found": "--report 경로가 존재하지 않습니다.",
    "verifier_report_invalid": "Verifier 보고서가 유효한 JSON object가 아닙니다.",
    "verifier_report_commands_invalid": "보고서의 commands가 argv 리스트 또는 명령 문자열이 아닙니다.",
    "verifier_attempt_not_independent": (
        "verifier attempt id가 해당 미니 태스크의 runner attempt id와 같아 "
        "독립 검증 증거가 될 수 없습니다."
    ),
    "verifier_scope_hash_missing": "workgraph가 해당 미니 태스크의 scope_hash를 공표하지 않았습니다.",
    "git_command_failed": "git 명령이 실패했습니다.",
    "unknown_subcommand": "알 수 없는 하위 명령입니다.",
}


class VerifierAdapterError(Exception):
    """폐쇄 집합 `ERROR_CODES`의 코드 하나로 실패를 표현한다.

    진입점 모듈(`oppb_runtime_tool.py`)의 `ToolError`로 어댑트되어 단일 라인 JSON
    출력 계약을 그대로 따른다(evidence.py의 `EvidenceError`와 같은 모양).
    """

    def __init__(self, code, message="", exit_code=EXIT_ERROR, **extra):
        super().__init__(message or code)
        self.code = code
        self.message = message
        self.exit_code = exit_code
        self.extra = extra


# ─────────────────────────────────────────────────────────────────────────────
# 인자·run root 읽기 — 부작용보다 먼저 끝낸다. run.json·workgraph.json은 읽기만 한다.
# ─────────────────────────────────────────────────────────────────────────────


def _require_run_root(opts):
    raw = opts.get("run_root")
    if not raw:
        raise VerifierAdapterError("run_root_missing")
    if not os.path.isabs(raw):
        raise VerifierAdapterError("run_root_not_absolute", "받은 값: %s" % raw)
    path = pathlib.Path(raw)
    if not path.is_dir():
        raise VerifierAdapterError("run_root_not_found", "받은 값: %s" % raw)
    return path


def _require_task_id(opts):
    task_id = opts.get("task_id")
    if not task_id:
        raise VerifierAdapterError("task_id_missing")
    return task_id


def _require_kind(opts):
    kind = opts.get("kind")
    if not kind:
        raise VerifierAdapterError("verifier_kind_missing")
    if kind not in VERIFIER_KINDS:
        raise VerifierAdapterError(
            "verifier_kind_unknown",
            "지원 종류: %s (받은 값: %r)" % (", ".join(VERIFIER_KINDS), kind),
            EXIT_USAGE,
        )
    return kind


def _load_run_manifest(run_root):
    path = run_root / "run.json"
    if not path.is_file():
        raise VerifierAdapterError("run_manifest_missing", "경로: %s" % path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VerifierAdapterError(
            "run_manifest_missing", "run.json 파싱 실패: %s" % exc
        ) from exc


def _code_head(allocator_root):
    """allocator repo의 현재 HEAD를 읽는다 — 조회 전용이며 Git 상태를 바꾸지 않는다.

    evidence.py가 제출된 code_head를 이 값과 대조해 거부하므로, adapter는 같은
    관측값을 그대로 싣는다(재구현이 아니라 동일한 read-only 조회다).
    """
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(allocator_root),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise VerifierAdapterError(
            "git_command_failed", (result.stderr or result.stdout).strip()
        )
    return result.stdout.strip()


def _task_of(run_root, task_id):
    """workgraph.json은 controller.py가 유일한 writer이므로 읽기 export로만 접근한다."""
    workgraph = controller.read_workgraph(run_root)
    return workgraph, controller.find_task(workgraph, task_id)


def _lease_of(task):
    return (task.get("contract") or {}).get("lease") or {}


# ─────────────────────────────────────────────────────────────────────────────
# 조건부 Verifier 호출 시점 판정 — workgraph 사실과 명시 신호만 본다(추론 없음)
# ─────────────────────────────────────────────────────────────────────────────


def _risk_signals(task, declared):
    """§10 "위험 ACCEPT" 신호 집합.

    호출자가 명시한 신호(`--signals`)와 workgraph가 공표한 사실 하나를 합친다 —
    `lease.runtime_resources` 선언은 그 자체가 새 I/O 축 점유 선언이므로 위험
    신호로 센다. 그 외에는 코드가 무엇을 바꿨는지 추측하지 않는다.
    """
    signals = []
    for raw in declared:
        token = raw.strip()
        if token and token not in signals:
            signals.append(token)
    if _lease_of(task).get("runtime_resources") and "io" not in signals:
        signals.append("io")
    return signals


def closed_contracts(workgraph, task):
    """§10 "계약 폐쇄" 판정 — producer-consumer가 모두 run을 마친 계약만 돌려준다.

    이 태스크가 선언한 각 contract에 대해, 같은 contract를 선언한 다른 미니
    태스크(peer)가 하나 이상 있고 자신과 모든 peer가 `POST_RUN_STATES`이면 그
    계약은 폐쇄된 것으로 본다. peer가 없으면 통합할 상대가 없으므로 폐쇄가 아니다.
    """
    contracts = _lease_of(task).get("contracts") or []
    if task.get("state") not in controller.POST_RUN_STATES:
        return []
    tasks = workgraph.get("mini_tasks") or []
    closed = []
    for contract in contracts:
        peers = [
            other
            for other in tasks
            if other.get("id") != task.get("id")
            and contract in (_lease_of(other).get("contracts") or [])
        ]
        if not peers:
            continue
        if all(peer.get("state") in controller.POST_RUN_STATES for peer in peers):
            closed.append(contract)
    return closed


def decide_verifiers(trigger, risk_signals, closed):
    """(resolved_trigger, kinds) — §10 검증 시점표를 그대로 옮긴 판정.

    | 시점 | 호출 Verifier |
    |---|---|
    | ACCEPT | 경량 Convention + 조건부 Integration(계약 폐쇄 시) |
    | 위험 ACCEPT | ACCEPT + Security |
    | 계약 폐쇄 | Integration |
    | PROJECT VERIFY | 세 Verifier 전부 |
    """
    if trigger == "project_verify":
        return trigger, ["convention", "integration", "security"]
    if trigger == "contract_closure":
        return trigger, ["integration"]

    # accept / risk_accept — 신호가 있으면 accept를 risk_accept로 승격한다.
    resolved = "risk_accept" if (trigger == "risk_accept" or risk_signals) else "accept"
    kinds = ["convention"]
    if resolved == "risk_accept":
        kinds.append("security")
    if closed:
        kinds.append("integration")
    return resolved, kinds


# ─────────────────────────────────────────────────────────────────────────────
# dispatch payload — 세 워커의 기존 입력 계약만 채운다(키 추가·제거 없음)
# ─────────────────────────────────────────────────────────────────────────────


def _timestamp(opts):
    raw = opts.get("timestamp")
    if raw:
        return raw
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")


def _output_dir(opts, run_root, task_id):
    raw = opts.get("output_dir")
    path = pathlib.Path(raw) if raw else run_root / "verify" / task_id
    # Verifier 보고서 산출 위치는 run root 안이며 Git 추적 대상이 아니다(init이
    # `.opal-runs/`를 exclude에 등록한다). 워커가 바로 쓸 수 있게 미리 만든다.
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def dispatch_input(kind, opts, run_root, manifest, task):
    """해당 Verifier 워커의 기존 입력 계약을 그대로 채운 payload."""
    project_root = opts.get("project_root") or manifest.get("project_root") or manifest["allocator_root"]
    files = list(_lease_of(task).get("tracked_writes") or [])
    if kind == "integration":
        test_mode = opts.get("test_mode") or DEFAULT_TEST_MODE
        if test_mode not in TEST_MODES:
            raise VerifierAdapterError(
                "verifier_test_mode_unknown",
                "지원 값: %s (받은 값: %r)" % (", ".join(TEST_MODES), test_mode),
                EXIT_USAGE,
            )
        return {
            "mode": opts.get("mode") or DEFAULT_TEST_DEPTH,
            "test_mode": test_mode,
            "changed_files": files,
            "project_root": project_root,
        }
    return {
        "project_root": project_root,
        "target_files": files,
        "output_dir": _output_dir(opts, run_root, task["id"]),
        "timestamp": _timestamp(opts),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 보고서 → Evidence schema 변환
# ─────────────────────────────────────────────────────────────────────────────


def _load_report(opts):
    raw = opts.get("report")
    if not raw:
        raise VerifierAdapterError("verifier_report_missing")
    if not os.path.isabs(raw):
        raise VerifierAdapterError("verifier_report_not_absolute", "받은 값: %s" % raw)
    path = pathlib.Path(raw)
    if not path.is_file():
        raise VerifierAdapterError("verifier_report_not_found", "받은 값: %s" % raw)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VerifierAdapterError("verifier_report_invalid", str(exc)) from exc
    if not isinstance(document, dict):
        raise VerifierAdapterError(
            "verifier_report_invalid", "최상위가 object가 아닙니다: %s" % type(document).__name__
        )
    return path, document


def _normalize_commands(report):
    """보고서가 남긴 실행 명령을 evidence의 `commands`(argv 리스트의 리스트)로 정규화한다.

    gc 스킬은 argv 리스트를, `opal-test-agent`는 명령 문자열을 남기는 경우가 있어
    둘 다 받아 하나의 형태로 만든다. 그 외 형태는 추측하지 않고 거부한다.
    """
    raw = report.get("commands")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise VerifierAdapterError("verifier_report_commands_invalid", "commands가 리스트가 아닙니다.")
    commands = []
    for item in raw:
        if isinstance(item, str):
            argv = shlex.split(item)
            if not argv:
                raise VerifierAdapterError(
                    "verifier_report_commands_invalid", "빈 명령 문자열: %r" % item
                )
            commands.append(argv)
        elif isinstance(item, list) and item and all(isinstance(part, str) for part in item):
            commands.append(list(item))
        else:
            raise VerifierAdapterError(
                "verifier_report_commands_invalid", "지원하지 않는 원소: %r" % (item,)
            )
    return commands


def _blocking_findings(report):
    findings = report.get("findings")
    if not isinstance(findings, list):
        return 0
    return sum(
        1
        for finding in findings
        if isinstance(finding, dict) and finding.get("disposition") == "blocking"
    )


_TEST_VERDICT_RESULTS = {
    "all pass": "pass",
    "partial fail": "fail",
    "critical fail": "fail",
}


def _result_of(kind, report, blocking):
    """검증 결과를 `pass`·`fail`·`incomplete` 셋으로 정규화한다.

    gc-finding-schema.md §6이 이미 정한 규칙을 그대로 따른다 — `missing_capabilities`가
    비어 있지 않거나 검사 실행 status가 pass가 아니면 PASS 계열을 만들지 않고,
    blocking finding이 1건 이상이면 fail이다. 통합 검증은 `opal-test-agent`의
    verdict 3값을 같은 축으로 옮긴다.
    """
    if report.get("missing_capabilities"):
        return "incomplete"
    if kind == "integration":
        status = str(report.get("status") or "").strip().lower()
        if status and status != "completed":
            return "incomplete"
        verdict = str(report.get("verdict") or "").strip().lower()
        if verdict in _TEST_VERDICT_RESULTS:
            return _TEST_VERDICT_RESULTS[verdict]
        if report.get("fail_count"):
            return "fail"
        return "incomplete" if verdict == "" and not report.get("pass_count") else "pass"
    status = str(report.get("status") or "").strip().lower()
    if status and status != "pass":
        return "incomplete" if status != "fail" else "fail"
    return "fail" if blocking else "pass"


def build_evidence_document(run_root, task_id, kind, report, report_path, attempt_id=None):
    """보고서를 Evidence schema 문서로 변환한다.

    - `scope_hash`는 workgraph가 공표한 값을 **복사**한다(자체 계산 없음).
    - `code_head`는 run.json의 allocator_root에서 읽은 현재 HEAD다.
    - `verifier.attempt_id`는 항상 runner attempt id와 다르다 — 호출자가 같은 값을
      명시하면 여기서 거부하므로 색인 경로에 도달하지 않는다(수용기준 9).
    - `changes`·`proof`·`knowledge`는 `attempt_result`(additionalProperties: false)가
      아니라 이 문서의 `runner_result`에 안착한다 — evidence schema는 최상위
      additionalProperties: true이므로 동결 스키마 변경 없이 표현된다.
    """
    _workgraph, task = _task_of(run_root, task_id)
    scope_hash = task.get("scope_hash")
    if not scope_hash:
        raise VerifierAdapterError("verifier_scope_hash_missing", "task_id=%s" % task_id)

    runner_attempt_id = task.get("runner_attempt_id")
    if attempt_id:
        if runner_attempt_id and attempt_id == runner_attempt_id:
            raise VerifierAdapterError(
                "verifier_attempt_not_independent",
                "runner_attempt_id=%s" % runner_attempt_id,
            )
        verifier_attempt_id = attempt_id
    else:
        verifier_attempt_id = "%s-verifier-%s-%s" % (task_id, kind, uuid.uuid4().hex[:8])

    manifest = _load_run_manifest(run_root)
    blocking = _blocking_findings(report)
    document = {
        "schema_version": 1,  # evidence schema는 정수다(workgraph의 문자열 "1.0"과 다르다).
        "evidence_id": "%s-%s" % (kind, verifier_attempt_id),
        "scope": task_id,
        "code_head": _code_head(pathlib.Path(manifest["allocator_root"])),
        "scope_hash": scope_hash,
        "verifier": {
            "kind": kind,
            "attempt_id": verifier_attempt_id,
            "agent": VERIFIER_ASSETS[kind]["agent"],
            "skill": VERIFIER_ASSETS[kind]["skill"],
        },
        "result": _result_of(kind, report, blocking),
        "commands": _normalize_commands(report),
        "blocking_findings": blocking,
        "source_report": str(report_path),
    }
    for key in ("report_path", "findings_path", "verdict", "summary"):
        if report.get(key) is not None:
            document.setdefault("report", {})[key] = report[key]

    runner_result = {
        key: report[key]
        for key in ("changes", "proof", "knowledge")
        if report.get(key) is not None
    }
    if runner_result:
        document["runner_result"] = runner_result
    return document


# ─────────────────────────────────────────────────────────────────────────────
# 서브 명령 본체
# ─────────────────────────────────────────────────────────────────────────────


def cmd_verifier_plan(opts):
    """조건부 Verifier 호출 시점을 판정하고 각 워커의 dispatch payload를 만든다."""
    run_root = _require_run_root(opts)
    task_id = _require_task_id(opts)
    trigger = opts.get("trigger")
    if not trigger:
        raise VerifierAdapterError("verifier_trigger_missing")
    if trigger not in TRIGGERS:
        raise VerifierAdapterError(
            "verifier_trigger_unknown",
            "지원 시점: %s (받은 값: %r)" % (", ".join(TRIGGERS), trigger),
            EXIT_USAGE,
        )

    manifest = _load_run_manifest(run_root)
    workgraph, task = _task_of(run_root, task_id)

    declared = [token for token in (opts.get("signals") or "").split(",") if token.strip()]
    signals = _risk_signals(task, declared)
    closed = closed_contracts(workgraph, task)
    resolved, kinds = decide_verifiers(trigger, signals, closed)

    verifiers = []
    for kind in kinds:
        asset = VERIFIER_ASSETS[kind]
        payload = dispatch_input(kind, opts, run_root, manifest, task)
        # 기존 입력 계약을 벗어난 키를 만들지 않는다 — 키 집합은 상수로 고정돼 있다.
        assert set(payload) == set(asset["input_keys"])
        verifiers.append(
            {
                "kind": kind,
                "agent": asset["agent"],
                "skill": asset["skill"],
                "input": payload,
            }
        )

    return {
        "task_id": task_id,
        "trigger": trigger,
        "resolved_trigger": resolved,
        "risk_signals": signals,
        "contract_closure": bool(closed),
        "closed_contracts": closed,
        "verifiers": verifiers,
    }


def cmd_verifier_submit(opts):
    """Verifier 보고서를 Evidence 문서로 변환해 Evidence Tool에 제출한다.

    색인·schema·code head·scope hash 검사는 전적으로 evidence.py의 것이다 — 이
    모듈은 변환 결과를 임시 파일에 쓰고 `evidence submit` 계약으로 넘길 뿐,
    `evidence/` 색인 경로에 직접 쓰지 않는다.
    """
    run_root = _require_run_root(opts)
    task_id = _require_task_id(opts)
    kind = _require_kind(opts)
    report_path, report = _load_report(opts)

    document = build_evidence_document(
        run_root, task_id, kind, report, report_path, opts.get("attempt")
    )

    handle, staged = tempfile.mkstemp(prefix="oppb-evidence-", suffix=".json")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(document, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        submitted = evidence.evidence_command(
            {"subcommand": "submit", "run_root": str(run_root), "file": staged}
        )
    finally:
        with contextlib.suppress(OSError):
            os.unlink(staged)

    submitted = dict(submitted)
    submitted["kind"] = kind
    submitted["result"] = document["result"]
    submitted["verifier_attempt_id"] = document["verifier"]["attempt_id"]
    return submitted


# ─────────────────────────────────────────────────────────────────────────────
# 진입점 — `oppb_runtime_tool.py`가 `verifier` 서브 명령으로 등록한다.
# ─────────────────────────────────────────────────────────────────────────────


def verifier_command(opts):
    """`verifier <subcommand>` 진입점. 진입점 모듈이 이 함수만 호출한다."""
    subcommand = opts.get("subcommand")
    if subcommand == "plan":
        return cmd_verifier_plan(opts)
    if subcommand == "submit":
        return cmd_verifier_submit(opts)
    raise VerifierAdapterError(
        "unknown_subcommand",
        "지원 하위 명령: %s (받은 값: %r)" % (", ".join(VERIFIER_SUBCOMMANDS), subcommand),
        EXIT_USAGE,
    )
