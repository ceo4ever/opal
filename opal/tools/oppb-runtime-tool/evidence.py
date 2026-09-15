"""
@header {
  "module": "evidence",
  "task": "132",
  "layer": "util",
  "domain": "oppb-runtime",
  "description": "OPPB Evidence Tool — `evidence/<scope>/<evidence-id>.json`을 schema 검증 후 원자·불변 색인하고 content hash를 발급한다. schema 불일치·code head 불일치·scope hash 불일치 evidence를 색인 전에 거부한다(검사가 색인보다 먼저 끝난다). `task accept`는 색인된 독립 검증 증거(해당 태스크의 runner attempt 자신이 발행하지 않은 evidence)가 있을 때만 미니 태스크를 accepted로 전이한다(수용기준 9). `workgraph.json`·`acceptance.json`은 이 모듈이 직접 쓰지 않는다 — 그 문서의 유일한 writer는 controller.py(W-7)이므로, 읽기는 `controller.read_workgraph`/`find_task`로, task state 갱신은 `controller.workgraph_transaction`으로, 증거 역인덱스 갱신은 `controller.index_evidence`로 위임한다(진입점 모듈이 이미 같은 방식으로 controller를 가져오므로 순환 임포트가 아니다). 이 모듈은 controller.py·supervisor.py를 만들거나 고치지 않는다 — 공개 export만 소비한다. evidence 색인 자체(`evidence/<scope>/<id>.json`)는 이 모듈의 단독 소유 경로이므로 `os.link`(CREATE 전용, 대상 존재 시 원자적으로 실패)로 불변을 보장한다 — `opal/tools/oppl-runtime-tool/ledger.py:336-377` 패턴을 형태만 복제했다(그 도구는 import하지 않는다). `oppb_runtime_tool.py`가 `evidence_command`/`task_command`를 서브커맨드로 등록해서 호출하며, 성공 시 반환하는 dict를 진입점의 `ok()`로 출력한다 — 이 모듈 자체는 stdout에 쓰지 않는다. 표준 라이브러리(git CLI 포함)만 사용한다.",
  "exports": [
    "ERROR_CODES", "EvidenceError",
    "evidence_command", "task_command"
  ],
  "depends": [
    "git CLI 2.x",
    "opal/tools/oppb-runtime-tool/controller.py",
    "opal/core/references/harness/tool-output-contract.md"
  ]
}
"""

# 표준 라이브러리만 사용한다. oppl-runtime-tool은 import하지 않는다 — 원자 쓰기는
# 형태만 복제한다. controller.py는 workgraph.json/acceptance.json의 유일한
# writer라 그 공개 export(읽기·트랜잭션)만 가져다 쓰고 직접 쓰지 않는다.
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import controller  # noqa: E402 — 동일 디렉토리 모듈, sys.path 보정 뒤 로드

EXIT_ERROR = 1
EXIT_USAGE = 2

EVIDENCE_SUBCOMMANDS = ("submit",)
TASK_SUBCOMMANDS = ("accept",)

ERROR_CODES = {
    "run_root_missing": "--run-root는 필수입니다.",
    "run_root_not_absolute": "--run-root는 절대경로여야 합니다.",
    "run_root_not_found": "--run-root 경로가 존재하지 않습니다.",
    "run_manifest_missing": "run root에 run.json이 없습니다 — init을 먼저 실행하십시오.",
    "file_missing": "--file은 필수입니다.",
    "file_not_absolute": "--file은 절대경로여야 합니다.",
    "file_not_found": "--file 경로가 존재하지 않습니다.",
    "evidence_json_invalid": "evidence 파일이 유효한 JSON이 아닙니다.",
    "evidence_schema_mismatch": "evidence document가 schema 계약을 충족하지 않습니다.",
    "evidence_code_head_mismatch": (
        "evidence의 code_head가 allocator repo의 실제 HEAD와 일치하지 않습니다."
    ),
    "evidence_scope_hash_mismatch": (
        "evidence의 scope_hash가 workgraph가 공표한 scope_hash와 일치하지 않습니다."
    ),
    "evidence_not_independent": (
        "evidence가 해당 태스크의 runner attempt 자신이 발행한 것이라 "
        "독립 검증 증거로 인정하지 않습니다."
    ),
    "evidence_already_indexed": "같은 scope·evidence_id가 이미 불변 색인되어 있어 재작성할 수 없습니다.",
    "evidence_index_write_failed": "evidence 색인 저장에 실패했습니다.",
    "task_id_missing": "--task-id는 필수입니다.",
    "task_accept_no_independent_evidence": (
        "독립 검증 evidence가 색인되어 있지 않아 accepted로 전이할 수 없습니다."
    ),
    "git_command_failed": "git 명령이 실패했습니다.",
    "unknown_subcommand": "알 수 없는 하위 명령입니다.",
    "internal_error": "처리되지 않은 내부 오류입니다.",
}


class EvidenceError(Exception):
    """폐쇄 집합 `ERROR_CODES`의 코드 하나로 실패를 표현한다.

    진입점 모듈(`oppb_runtime_tool.py`)의 `ToolError`로 어댑트되어 단일 라인
    JSON 출력 계약을 그대로 따른다(controller.py의 `ControllerError`와 같은 모양).
    """

    def __init__(self, code, message="", exit_code=EXIT_ERROR, **extra):
        super().__init__(message or code)
        self.code = code
        self.message = message
        self.exit_code = exit_code
        self.extra = extra


# ─────────────────────────────────────────────────────────────────────────────
# 인자 검증 — 부작용보다 먼저 끝낸다
# ─────────────────────────────────────────────────────────────────────────────


def _require_run_root(opts):
    raw = opts.get("run_root")
    if not raw:
        raise EvidenceError("run_root_missing")
    if not os.path.isabs(raw):
        raise EvidenceError("run_root_not_absolute", "받은 값: %s" % raw)
    path = pathlib.Path(raw)
    if not path.is_dir():
        raise EvidenceError("run_root_not_found", "받은 값: %s" % raw)
    return path


def _require_file(opts):
    raw = opts.get("file")
    if not raw:
        raise EvidenceError("file_missing")
    if not os.path.isabs(raw):
        raise EvidenceError("file_not_absolute", "받은 값: %s" % raw)
    path = pathlib.Path(raw)
    if not path.is_file():
        raise EvidenceError("file_not_found", "받은 값: %s" % raw)
    return path


def _require_task_id(opts):
    task_id = opts.get("task_id")
    if not task_id:
        raise EvidenceError("task_id_missing")
    return task_id


# ─────────────────────────────────────────────────────────────────────────────
# run root 파일 계약 읽기 — run.json은 oppb_runtime_tool.cmd_init이 쓴 것을 읽기만
# 한다. workgraph.json은 controller.py가 유일한 writer이므로 읽기·갱신 모두
# controller의 공개 export를 통해서만 접근한다.
# ─────────────────────────────────────────────────────────────────────────────


def _load_run_manifest(run_root):
    path = run_root / "run.json"
    if not path.is_file():
        raise EvidenceError("run_manifest_missing", "경로: %s" % path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvidenceError("run_manifest_missing", "run.json 파싱 실패: %s" % exc) from exc


def _current_code_head(allocator_root):
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(allocator_root),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise EvidenceError(
            "git_command_failed", (result.stderr or result.stdout).strip()
        )
    return result.stdout.strip()


# ─────────────────────────────────────────────────────────────────────────────
# evidence schema — 색인 전 첫 관문. 표준 라이브러리만 사용한다(jsonschema 금지).
# ─────────────────────────────────────────────────────────────────────────────

_REQUIRED_FIELD_TYPES = {
    "schema_version": int,
    "evidence_id": str,
    "scope": str,
    "code_head": str,
    "scope_hash": str,
    "verifier": dict,
    "result": str,
    "commands": list,
}

_SHA1_HEX = re.compile(r"^[0-9a-f]{40}$")
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


def _validate_schema(document):
    if not isinstance(document, dict):
        raise EvidenceError("evidence_schema_mismatch", "evidence document가 JSON object가 아닙니다.")

    missing = [key for key in _REQUIRED_FIELD_TYPES if key not in document]
    if missing:
        raise EvidenceError(
            "evidence_schema_mismatch",
            "필수 필드 누락: %s" % ", ".join(sorted(missing)),
            missing_fields=sorted(missing),
        )

    for key, expected_type in _REQUIRED_FIELD_TYPES.items():
        value = document[key]
        # bool은 int의 서브클래스이므로 schema_version에서 별도로 걸러낸다.
        if expected_type is int and isinstance(value, bool):
            raise EvidenceError(
                "evidence_schema_mismatch", "%s 필드는 bool을 허용하지 않습니다." % key
            )
        if not isinstance(value, expected_type):
            raise EvidenceError(
                "evidence_schema_mismatch",
                "%s 필드 타입 불일치: %s 기대, %s 수신"
                % (key, expected_type.__name__, type(value).__name__),
                field=key,
            )

    if not document["evidence_id"].strip():
        raise EvidenceError("evidence_schema_mismatch", "evidence_id가 빈 문자열입니다.")
    if not document["scope"].strip():
        raise EvidenceError("evidence_schema_mismatch", "scope가 빈 문자열입니다.")
    if not _SHA1_HEX.match(document["code_head"]):
        raise EvidenceError("evidence_schema_mismatch", "code_head가 40자리 소문자 hex가 아닙니다.")
    if not _SHA256_HEX.match(document["scope_hash"]):
        raise EvidenceError("evidence_schema_mismatch", "scope_hash가 64자리 소문자 hex가 아닙니다.")

    verifier = document["verifier"]
    if not isinstance(verifier.get("kind"), str) or not verifier.get("kind", "").strip():
        raise EvidenceError("evidence_schema_mismatch", "verifier.kind가 없거나 문자열이 아닙니다.")
    if not isinstance(verifier.get("attempt_id"), str) or not verifier.get("attempt_id", "").strip():
        raise EvidenceError("evidence_schema_mismatch", "verifier.attempt_id가 없거나 문자열이 아닙니다.")

    for command in document["commands"]:
        if not isinstance(command, list) or not command or not all(
            isinstance(part, str) for part in command
        ):
            raise EvidenceError(
                "evidence_schema_mismatch", "commands의 각 원소는 비어있지 않은 문자열 리스트여야 합니다."
            )


# ─────────────────────────────────────────────────────────────────────────────
# evidence 색인 — 이 모듈의 단독 소유 경로. CREATE 전용 원자 쓰기로 불변을 보장한다.
# ─────────────────────────────────────────────────────────────────────────────


def _atomic_create_immutable(path, payload):
    """대상이 이미 있으면 원자적으로 실패한다(TOCTOU 없는 CREATE 전용 색인).

    tempfile에 쓰고 fsync한 뒤 `os.link`로 최종 경로에 연결한다. `os.link`는
    대상이 이미 존재하면 `FileExistsError`로 실패하는 원자 연산이라, 검사와
    쓰기 사이에 값을 몰래 바꿔치기 하는 race가 없다. 성공하든 실패하든 임시
    파일은 정리한다(`ledger.py:336-377`의 mkstemp→fsync→교체 형태를 CREATE 전용으로
    변형했다).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
    body = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(tmp, str(path))
    finally:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _indexed_evidence_count(run_root, task_id):
    evidence_dir = run_root / "evidence" / task_id
    if not evidence_dir.is_dir():
        return 0
    return sum(1 for p in evidence_dir.glob("*.json") if p.is_file())


# ─────────────────────────────────────────────────────────────────────────────
# 서브 명령 본체
# ─────────────────────────────────────────────────────────────────────────────


def cmd_evidence_submit(opts):
    """schema·code head·scope hash·독립성 검사를 색인 전에 전부 통과한 evidence만
    `evidence/<scope>/<evidence-id>.json`에 불변 색인한다.

    거부는 색인보다 앞선다 — 아래 검사 중 하나라도 실패하면 색인 디렉토리에
    파일을 하나도 남기지 않고 즉시 실패를 반환한다(S-9 ①).
    """
    run_root = _require_run_root(opts)
    file_path = _require_file(opts)

    try:
        raw = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise EvidenceError("file_not_found", str(exc)) from exc
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise EvidenceError("evidence_json_invalid", str(exc)) from exc

    # 1) schema — 필수 필드·타입이 전부 맞아야 다음 검사로 넘어간다.
    _validate_schema(document)

    # 2) code head — evidence가 주장하는 커밋이 allocator repo의 실제 HEAD와 같아야 한다.
    manifest = _load_run_manifest(run_root)
    allocator_root = pathlib.Path(manifest["allocator_root"])
    actual_head = _current_code_head(allocator_root)
    if document["code_head"] != actual_head:
        raise EvidenceError(
            "evidence_code_head_mismatch",
            "evidence=%s, 실제=%s" % (document["code_head"], actual_head),
        )

    # 3) scope hash — workgraph가 공표한 scope의 scope_hash와 같아야 한다.
    #    workgraph.json은 controller.py 소유이므로 읽기 전용 export로만 접근한다.
    workgraph = controller.read_workgraph(run_root)
    task = controller.find_task(workgraph, document["scope"])
    expected_scope_hash = task.get("scope_hash")
    if not expected_scope_hash or document["scope_hash"] != expected_scope_hash:
        raise EvidenceError(
            "evidence_scope_hash_mismatch",
            "evidence=%s, workgraph=%s" % (document["scope_hash"], expected_scope_hash),
        )

    # 4) 독립성 — 이 태스크를 실행한 runner attempt 자신이 발행한 evidence가 아니어야 한다.
    runner_attempt_id = task.get("runner_attempt_id")
    if runner_attempt_id and document["verifier"]["attempt_id"] == runner_attempt_id:
        raise EvidenceError(
            "evidence_not_independent", "runner_attempt_id=%s" % runner_attempt_id
        )

    # 5) 불변 색인 — 대상이 이미 있으면 `os.link`가 원자적으로 실패한다.
    target = run_root / "evidence" / document["scope"] / ("%s.json" % document["evidence_id"])
    if target.exists():
        raise EvidenceError("evidence_already_indexed", "경로: %s" % target)
    try:
        content_hash = _atomic_create_immutable(target, document)
    except FileExistsError as exc:
        raise EvidenceError("evidence_already_indexed", "경로: %s" % target) from exc
    except OSError as exc:
        raise EvidenceError("evidence_index_write_failed", str(exc)) from exc

    # 6) 증거 역인덱스 — acceptance.json은 controller.py 소유이므로 export로만 갱신한다.
    controller.index_evidence(
        run_root, document["evidence_id"], document["scope"], satisfied=True
    )

    return {
        "accepted": True,
        "evidence_id": document["evidence_id"],
        "scope": document["scope"],
        "path": str(target),
        "content_hash": content_hash,
    }


def cmd_task_accept(opts):
    """schema 검증을 통과해 색인된 독립 검증 증거가 있을 때만 미니 태스크를
    `accepted`로 전이한다(수용기준 9).

    workgraph.json 갱신은 `controller.workgraph_transaction`에 위임한다 —
    이 모듈은 그 문서를 직접 쓰지 않는다. 같은 락 안에서 증거 존재를 재확인해
    락 밖 선검사와 락 안 갱신 사이의 TOCTOU를 닫는다.
    """
    run_root = _require_run_root(opts)
    task_id = _require_task_id(opts)

    if _indexed_evidence_count(run_root, task_id) == 0:
        raise EvidenceError("task_accept_no_independent_evidence", "task_id=%s" % task_id)

    with controller.workgraph_transaction(run_root) as document:
        task = controller.find_task(document, task_id)
        evidence_count = _indexed_evidence_count(run_root, task_id)
        if evidence_count == 0:
            raise EvidenceError(
                "task_accept_no_independent_evidence", "task_id=%s" % task_id
            )
        task["state"] = "accepted"

    return {
        "accepted": True,
        "task_id": task_id,
        "state": "accepted",
        "evidence_count": evidence_count,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 진입점 — `oppb_runtime_tool.py`가 `evidence`/`task` 서브 명령으로 등록한다.
# ─────────────────────────────────────────────────────────────────────────────


def evidence_command(opts):
    """`evidence <subcommand>` 진입점. 진입점 모듈이 이 함수만 호출한다."""
    subcommand = opts.get("subcommand")
    if subcommand not in EVIDENCE_SUBCOMMANDS:
        raise EvidenceError(
            "unknown_subcommand",
            "지원 하위 명령: %s (받은 값: %r)" % (", ".join(EVIDENCE_SUBCOMMANDS), subcommand),
            EXIT_USAGE,
        )
    return cmd_evidence_submit(opts)


def task_command(opts):
    """`task <subcommand>` 진입점. 진입점 모듈이 이 함수만 호출한다."""
    subcommand = opts.get("subcommand")
    if subcommand not in TASK_SUBCOMMANDS:
        raise EvidenceError(
            "unknown_subcommand",
            "지원 하위 명령: %s (받은 값: %r)" % (", ".join(TASK_SUBCOMMANDS), subcommand),
            EXIT_USAGE,
        )
    return cmd_task_accept(opts)
