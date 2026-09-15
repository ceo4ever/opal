"""
@header {
  "module": "recovery",
  "task": "132",
  "layer": "util",
  "domain": "oppb-runtime",
  "description": "OPPB `scope_violation` 회수·path-scoped 복구 — 제안서 §P2.2 `scope_violation` 회수 5단계를 소유한다. 위반 경로·계약·자원과 겹치는 active attempt의 연결 성분을 계산해 신규 dispatch와 checkpoint를 중단하고(halt marker), 단독 이탈이면 declared+actual path 합집합을 그 attempt preimage로 복구하며, 귀속 불가이면 연결 성분 process를 모두 종료한 뒤 마지막 accepted head 또는 봉인 preimage로 path-scoped 복구한다. 복구는 파일 바이트 교체와 path 한정 git 읽기만 사용하고 worktree 전체 reset·clean·restore를 호출하지 않는다(§4.5) — 자체 git 호출을 전부 감사 기록해 금지 패턴 호출 수를 receipt에 0으로 남긴다. 프로세스 생존·PGID 판정은 재구현하지 않고 `opal-agent reconcile-attempts`의 3분류를 소비만 한다(W-38 B-1). scope hash·lease 정규화는 `controller.py`의 compute_scope_hash·normalize_lease를 호출한다. 위반 attempt마다 task attempt·project rework 예산을 차감하되 contract revision당 첫 late discovery batch는 무과금이다(W-13 연동). 또 다른 active lease가 dirty인 PROVE 실패는 자기 candidate snapshot(`git archive <candidate_commit>`)에서 즉시 재검증해 대기 굶주림·오귀속을 0으로 만들고 Repair 예산을 차감하지 않는다. 표준 라이브러리와 git CLI만 사용하고 플랫폼 분기를 두지 않는다.",
  "exports": [
    "ERROR_CODES", "RecoveryError",
    "register_attempt", "seal_preimage", "scope_violation", "prove_failure",
    "recover_command"
  ],
  "depends": [
    "git CLI 2.x",
    "opal/tools/oppb-runtime-tool/controller.py",
    "opal/tools/opal-agent/run.sh",
    "opal/core/references/harness/tool-output-contract.md"
  ]
}
"""

# 표준 라이브러리만 사용한다 (신규 의존성 도입 금지)
from __future__ import annotations

import contextlib
import datetime
import hashlib
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import controller  # noqa: E402 — 동일 디렉토리 모듈, sys.path 보정 뒤 로드

SCHEMA_VERSION = "1.0"

EXIT_ERROR = 1
EXIT_USAGE = 2

RECOVERY_DIRNAME = "recovery"
PREIMAGES_DIRNAME = "preimages"
RECEIPTS_DIRNAME = "receipts"
SNAPSHOTS_DIRNAME = "revalidation"
HALT_FILENAME = "halt.json"
BUDGET_FILENAME = "rework-budget.json"
DISCOVERY_FILENAME = "discovery-batches.json"
ENVIRONMENT_DELTAS_DIRNAME = "environment-deltas"

# opal-agent sink stem 규약(`<stem>.attempt.json`) — reconcile-attempts가 이 이름을 읽는다.
ATTEMPT_RECORD_STEM = "attempt"

SUBCOMMANDS = (
    "register-attempt",
    "seal-preimage",
    "scope-violation",
    "prove-failure",
)

# 종료 신호 사이 유예. SIGTERM으로 끝나지 않으면 SIGKILL로 확정한다.
TERMINATE_GRACE_SEC = 5.0
TERMINATE_POLL_SEC = 0.05

# 제안서 §4.5·§P2.2 — 복구가 절대 호출하지 않는 git 형태. 자기 호출을 이 패턴으로
# 감사해 receipt에 호출 수를 남긴다(테스트의 PATH shim과 독립된 두 번째 기제).
FORBIDDEN_GIT_CALLS = (
    ("reset_hard", re.compile(r"\breset\b.*--hard")),
    ("worktree_restore", re.compile(r"\bcheckout\b\s+(-f\s+)?--\s*$")),
    ("worktree_restore", re.compile(r"\bcheckout\b.*--\s+\.\s*$")),
    ("worktree_restore", re.compile(r"\brestore\b(?!.*\s--\s+\S)")),
    ("worktree_clean", re.compile(r"\bclean\b.*-[a-z]*[dfx]")),
    ("worktree_remove", re.compile(r"\bworktree\b\s+(remove|prune)")),
)

ERROR_CODES = {
    "recover_run_root_missing": "--run-root는 필수입니다.",
    "recover_run_root_not_found": "--run-root 경로가 존재하지 않습니다.",
    "recover_project_root_missing": "--project-root는 필수입니다.",
    "recover_project_root_not_found": "--project-root 경로가 존재하지 않습니다.",
    "recover_project_root_not_git": "--project-root가 git 저장소가 아닙니다.",
    "recover_task_missing": "--task는 필수입니다.",
    "recover_attempt_missing": "--attempt는 필수입니다.",
    "recover_pid_invalid": "--pid는 양의 정수여야 합니다.",
    "recover_violation_missing": "--violation은 필수입니다.",
    "recover_violation_not_found": "--violation 경로가 존재하지 않습니다.",
    "recover_violation_not_json": "--violation 파일이 유효한 JSON이 아닙니다.",
    "recover_violation_invalid": "--violation 내용이 회수 계약을 만족하지 않습니다.",
    "recover_candidate_missing": "--candidate는 필수입니다.",
    "recover_candidate_not_found": "run root에서 candidate 기록을 찾을 수 없습니다.",
    "recover_candidate_commit_missing": "candidate 기록에 commit이 없습니다.",
    "recover_snapshot_failed": "candidate snapshot 생성에 실패했습니다.",
    "recover_forbidden_git_call": "복구가 금지된 전체 reset·clean·restore를 호출했습니다.",
    "recover_git_command_failed": "git 명령이 실패했습니다.",
    "recover_reconcile_failed": "opal-agent reconcile-attempts 호출에 실패했습니다.",
    "recover_unknown_subcommand": "알 수 없는 recover 하위 명령입니다.",
}


class RecoveryError(Exception):
    """폐쇄 집합 `ERROR_CODES`의 코드 하나로 실패를 표현한다."""

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
# 원자 쓰기 — ledger.py:336-377 패턴을 형태만 복제한다(oppl-runtime-tool import 금지).
# ─────────────────────────────────────────────────────────────────────────────


def _atomic_write_bytes(path, payload):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".oppb-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, str(path))
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise
    return path


def _atomic_write_json(path, document):
    _atomic_write_bytes(
        path, (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    return document


def _read_json(path, default=None):
    path = pathlib.Path(path)
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


# ─────────────────────────────────────────────────────────────────────────────
# git 호출 — PATH의 `git`만 쓴다(절대경로 우회 금지: 감사 가능해야 한다).
#   모든 호출을 자체 감사 목록에 남기고 금지 패턴을 세어 receipt에 기록한다.
# ─────────────────────────────────────────────────────────────────────────────


class GitAudit:
    """이 프로세스가 실행한 git 호출 기록. 금지 형태는 실행 전에 거부한다."""

    def __init__(self):
        self.calls = []
        self.violations = []

    def guard(self, args):
        rendered = " ".join(args)
        for name, pattern in FORBIDDEN_GIT_CALLS:
            if pattern.search(rendered):
                self.violations.append({"call": rendered, "kind": name})
                raise RecoveryError(
                    "recover_forbidden_git_call", "%s (%s)" % (rendered, name)
                )
        self.calls.append(rendered)

    def counts(self):
        tally = {"reset_hard_calls": 0, "worktree_restore_calls": 0,
                 "worktree_clean_calls": 0, "worktree_remove_calls": 0}
        key = {
            "reset_hard": "reset_hard_calls",
            "worktree_restore": "worktree_restore_calls",
            "worktree_clean": "worktree_clean_calls",
            "worktree_remove": "worktree_remove_calls",
        }
        for call in self.calls:
            for name, pattern in FORBIDDEN_GIT_CALLS:
                if pattern.search(call):
                    tally[key[name]] += 1
        return tally


def _git(audit, args, cwd, binary=False, check=True):
    audit.guard(args)
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=not binary,
    )
    if check and result.returncode != 0:
        stderr = result.stderr if not binary else result.stderr.decode("utf-8", "replace")
        raise RecoveryError(
            "recover_git_command_failed", "git %s: %s" % (" ".join(args), stderr.strip())
        )
    return result


def _head_blob(audit, repo, relpath):
    """HEAD(마지막 accepted head)의 해당 경로 바이트. 없으면 None."""
    result = _git(audit, ["cat-file", "blob", "HEAD:%s" % relpath], repo,
                  binary=True, check=False)
    if result.returncode != 0:
        return None
    return result.stdout


def _dirty_paths(audit, repo):
    """worktree에서 HEAD와 다른 경로 집합(미추적 포함). 판정은 git이 한다."""
    result = _git(audit, ["status", "--porcelain", "--untracked-files=all"], repo)
    paths = set()
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        entry = line[3:].strip()
        if " -> " in entry:  # rename — 양쪽 모두 영향 경로다
            before, _, after = entry.partition(" -> ")
            paths.add(before.strip().strip('"'))
            paths.add(after.strip().strip('"'))
        else:
            paths.add(entry.strip('"'))
    return paths


def _path_hash(repo, relpath):
    path = pathlib.Path(repo) / relpath
    if not path.is_file():
        return "<absent>"
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# run root 경로
# ─────────────────────────────────────────────────────────────────────────────


def _recovery_root(run_root):
    return pathlib.Path(run_root) / RECOVERY_DIRNAME


def _preimage_dir(run_root, task_id, attempt_id):
    return _recovery_root(run_root) / PREIMAGES_DIRNAME / str(task_id) / str(attempt_id)


def _attempt_key(task_id, attempt_id):
    return "%s/%s" % (task_id, attempt_id)


# ─────────────────────────────────────────────────────────────────────────────
# lease 조회 — lease 발급·회수는 Scope Lease Tool(W-12)이 소유한다. 여기서는
#   run root에 남은 lease 기록을 읽기만 하고 lease 상태를 쓰지 않는다.
# ─────────────────────────────────────────────────────────────────────────────

# lease 기록의 소유권 축 이름은 Scope Lease Tool(복수형 `lease` 블록)과 소유권
# 원장(단수형 `ownership` 블록)이 서로 다른 표기를 쓴다. 둘 다 읽는다.
LEASE_PATH_KEYS = (
    "paths", "tracked_writes", "tracked_write", "tracked_write_set",
    "ephemeral_writes", "ephemeral_write", "ephemeral_write_set", "write_set",
)
LEASE_CONTRACT_KEYS = (
    "contracts", "contract", "business_rules", "business_rule",
    "acceptance_ids", "acceptance",
)
LEASE_RESOURCE_KEYS = (
    "runtime_resources", "runtime_resource", "resources",
    "global_outputs", "global_output",
)

# lease 기록 안에서 소유권 축이 들어 있는 중첩 블록.
LEASE_NESTED_KEYS = ("lease", "ownership", "scope")


def _lease_records(run_root):
    """run root의 lease 기록을 정규 형태로 읽는다.

    lease 기록의 파일 배치는 Scope Lease Tool이 소유하므로 위치·키 이름을 하나로
    고정하지 않고 알려진 후보를 모두 읽는다. 읽기 전용이다.
    """
    run_root = pathlib.Path(run_root)
    documents = []
    candidates = [run_root / "leases.json", run_root / "lease.json"]
    for directory in (run_root / "leases", run_root / "lease"):
        if directory.is_dir():
            candidates.extend(sorted(directory.glob("*.json")))
    for path in candidates:
        document = _read_json(path)
        if isinstance(document, dict):
            documents.extend(document.get("leases") or [document])
        elif isinstance(document, list):
            documents.extend(document)

    # dispatch 시점 계약(execution packet)도 lease 선언의 원천이다.
    packets = run_root / controller.ATTEMPTS_DIRNAME
    if packets.is_dir():
        for path in sorted(packets.glob("*/*/%s" % controller.PACKET_FILENAME)):
            packet = _read_json(path)
            if isinstance(packet, dict):
                lease = dict(packet.get("lease") or {})
                lease["task_id"] = packet.get("task_id")
                lease["attempt_id"] = packet.get("attempt_id")
                documents.append(lease)

    leases = []
    for record in documents:
        if not isinstance(record, dict):
            continue
        raw = dict(record)
        for key in LEASE_NESTED_KEYS:
            nested = record.get(key)
            if isinstance(nested, dict):
                for axis, values in nested.items():
                    if isinstance(values, list):
                        raw.setdefault(axis, [])
                        if isinstance(raw[axis], list):
                            raw[axis] = list(raw[axis]) + list(values)
        task_id = raw.get("task_id") or raw.get("task")
        if not task_id:
            continue
        lease = {
            "task_id": str(task_id),
            "attempt_id": raw.get("attempt_id") or raw.get("attempt"),
            "state": raw.get("state", "active"),
            "tracked_writes": _collect(raw, LEASE_PATH_KEYS),
            "contracts": _collect(raw, LEASE_CONTRACT_KEYS),
            "runtime_resources": _collect(raw, LEASE_RESOURCE_KEYS),
        }
        lease["ephemeral_writes"] = []
        # scope hash·정규화는 Controller가 소유한다 — 여기서 재구현하지 않는다.
        lease["normalized"] = controller.normalize_lease(lease)
        lease["scope_hash"] = controller.compute_scope_hash(lease)
        leases.append(lease)
    return leases


def _collect(raw, keys):
    values = []
    for key in keys:
        found = raw.get(key)
        if isinstance(found, list):
            values.extend(str(item) for item in found)
    return sorted(set(values))


def _scope_of(lease):
    normalized = lease.get("normalized") or controller.normalize_lease(lease)
    return (
        set(normalized.get("tracked_writes", []))
        | set(normalized.get("ephemeral_writes", [])),
        set(normalized.get("contracts", [])),
        set(normalized.get("runtime_resources", [])),
    )


# ─────────────────────────────────────────────────────────────────────────────
# attempt 등록·생존 판정 — 판정은 opal-agent가 소유하고 여기서는 소비만 한다.
# ─────────────────────────────────────────────────────────────────────────────


def _opal_agent_entrypoint():
    agent_dir = pathlib.Path(__file__).resolve().parents[1] / "opal-agent"
    run_sh = agent_dir / "run.sh"
    if run_sh.is_file():
        return ["bash", str(run_sh)]
    return [sys.executable, str(agent_dir / "opal_agent.py")]


def _reconcile(directory):
    """`opal-agent reconcile-attempts <dir>` 응답을 그대로 돌려준다.

    PID 생존·PGID·경과시간 identity 판정을 자체 구현하지 않는다(W-38 B-1).
    """
    cmd = [*_opal_agent_entrypoint(), "reconcile-attempts", str(directory)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RecoveryError("recover_reconcile_failed", "%s: %s" % (" ".join(cmd), exc)) from exc
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RecoveryError(
            "recover_reconcile_failed",
            "stdout이 JSON이 아님(exit=%s): %r / %s" % (proc.returncode, proc.stdout, exc),
        ) from exc
    if not report.get("ok"):
        raise RecoveryError("recover_reconcile_failed", json.dumps(report, ensure_ascii=False))
    return report


def _attempt_dirs(run_root):
    root = pathlib.Path(run_root) / controller.ATTEMPTS_DIRNAME
    if not root.is_dir():
        return []
    return sorted(path for path in root.glob("*/*") if path.is_dir())


def _registered_attempts(run_root):
    """등록된 attempt를 `opal-agent` 3분류와 함께 돌려준다.

    반환 원소: {task_id, attempt_id, pid, pgid, disposition, alive, reclaim_required}
    `alive`는 opal-agent verdict의 probe 결과를 **그대로 읽은 값**이다.
    """
    attempts = []
    for directory in _attempt_dirs(run_root):
        record_path = directory / ("%s.attempt.json" % ATTEMPT_RECORD_STEM)
        if not record_path.is_file():
            continue
        record = _read_json(record_path) or {}
        report = _reconcile(directory)
        verdict = next(
            (item for item in report.get("attempts", [])
             if item.get("stem") == ATTEMPT_RECORD_STEM),
            None,
        )
        if verdict is None:
            continue
        probe = verdict.get("probe") or {}
        attempts.append(
            {
                "task_id": record.get("task_id") or directory.parent.name,
                "attempt_id": record.get("attempt") or directory.name,
                "dir": str(directory),
                "pid": verdict.get("pid"),
                "pgid": verdict.get("pgid"),
                "disposition": verdict.get("disposition"),
                "reclaim_required": bool(verdict.get("reclaim_required")),
                "alive": bool(probe.get("pid_alive")),
            }
        )
    return attempts


def _terminate(attempt):
    """연결 성분 attempt의 process를 종료한다 — 판정이 아니라 집행이다.

    PGID 회수는 attempt가 자기 세션 리더일 때만 의미가 있다. 기록된 PGID가 이
    복구 프로세스 자신의 group이면 회수하지 않는다 — 호출자(Supervisor·테스트
    러너)까지 끌고 죽는 것은 복구가 아니다.
    """
    pid = attempt.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        return False, False
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        # 이미 없어진 process — 이 복구가 종료시킨 것이 아니다.
        return False, True
    except (PermissionError, OSError):
        return False, False

    if _wait_gone(pid):
        _reclaim_group(attempt)
        return True, True
    with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
        os.kill(pid, signal.SIGKILL)
    gone = _wait_gone(pid)
    _reclaim_group(attempt)
    # SIGKILL을 받은 process는 종료된다. `gone`이 False인 경우는 부모가 아직
    # 수확(wait)하지 않은 잔재라 signal 주소만 남아 있는 상태이므로, 종료 사실과
    # 수확 확인을 구분해 둘 다 receipt에 남긴다.
    return True, gone


def _wait_gone(pid):
    deadline = time.monotonic() + TERMINATE_GRACE_SEC
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except (PermissionError, OSError):
            return False
        time.sleep(TERMINATE_POLL_SEC)
    return False


def _reclaim_group(attempt):
    pgid = attempt.get("pgid")
    if not attempt.get("reclaim_required") or not isinstance(pgid, int) or pgid <= 0:
        return False
    if pgid == os.getpgrp():
        return False
    with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
        os.killpg(pgid, signal.SIGKILL)
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 인자
# ─────────────────────────────────────────────────────────────────────────────


def _require_run_root(opts):
    raw = opts.get("run_root")
    if not raw:
        raise RecoveryError("recover_run_root_missing", exit_code=EXIT_USAGE)
    run_root = pathlib.Path(raw)
    if not run_root.is_dir():
        raise RecoveryError("recover_run_root_not_found", "받은 값: %s" % raw)
    return run_root


def _require_project_root(opts, audit):
    raw = opts.get("project_root")
    if not raw:
        raise RecoveryError("recover_project_root_missing", exit_code=EXIT_USAGE)
    repo = pathlib.Path(raw)
    if not repo.is_dir():
        raise RecoveryError("recover_project_root_not_found", "받은 값: %s" % raw)
    probe = _git(audit, ["rev-parse", "--is-inside-work-tree"], repo, check=False)
    if probe.returncode != 0:
        raise RecoveryError("recover_project_root_not_git", "받은 값: %s" % raw)
    return repo


def _require(opts, key, code):
    value = opts.get(key)
    if not value:
        raise RecoveryError(code, exit_code=EXIT_USAGE)
    return value


# ─────────────────────────────────────────────────────────────────────────────
# `recover register-attempt`
# ─────────────────────────────────────────────────────────────────────────────


def register_attempt(opts):
    """실행 중 attempt를 run root에 등록한다 — 연결 성분 종료 대상 판정 입력.

    기록 형식은 `opal-agent`의 sink stem 규약(`<stem>.attempt.json`)을 따른다.
    그래야 생존·identity 판정을 `reconcile-attempts`에 그대로 위임할 수 있다.
    """
    run_root = _require_run_root(opts)
    task_id = _require(opts, "task", "recover_task_missing")
    attempt_id = _require(opts, "attempt", "recover_attempt_missing")
    raw_pid = opts.get("pid")
    try:
        pid = int(raw_pid)
    except (TypeError, ValueError) as exc:
        raise RecoveryError("recover_pid_invalid", "받은 값: %r" % raw_pid, EXIT_USAGE) from exc
    if pid <= 0:
        raise RecoveryError("recover_pid_invalid", "받은 값: %r" % raw_pid, EXIT_USAGE)

    try:
        pgid = os.getpgid(pid)
    except OSError:
        pgid = None

    directory = controller.attempt_dir(run_root, task_id, attempt_id)
    directory.mkdir(parents=True, exist_ok=True)
    record = {
        "schema_version": SCHEMA_VERSION,
        "task_id": task_id,
        "attempt": attempt_id,
        "phase": "capability",
        "pid": pid,
        "pgid": pgid,
        "pgid_reclaimed": False,
        "started_at": time.time(),
        "status": "running",
        "terminal": None,
        "exit_code": None,
        "outputs": {},
        "heartbeat": {"expired": False},
        "unterminated_children": [],
        "registered_at": _now(),
    }
    path = directory / ("%s.attempt.json" % ATTEMPT_RECORD_STEM)
    _atomic_write_json(path, record)
    return {
        "subcommand": "register-attempt",
        "run_root": str(run_root),
        "task_id": task_id,
        "attempt_id": attempt_id,
        "pid": pid,
        "pgid": pgid,
        "record_path": str(path),
    }


# ─────────────────────────────────────────────────────────────────────────────
# `recover seal-preimage`
# ─────────────────────────────────────────────────────────────────────────────


def seal_preimage(opts):
    """attempt 실행 **전** lease 경로의 바이트를 봉인한다.

    단독 이탈 복구는 이 봉인본을 우선 쓴다. lease 기록이 아직 없으면 봉인할 대상이
    없고, 복구는 마지막 accepted head로 물러난다(제안서 §P2.2 3).
    """
    audit = GitAudit()
    run_root = _require_run_root(opts)
    repo = _require_project_root(opts, audit)
    task_id = _require(opts, "task", "recover_task_missing")
    attempt_id = _require(opts, "attempt", "recover_attempt_missing")

    paths = set()
    for lease in _lease_records(run_root):
        if lease["task_id"] != task_id:
            continue
        if lease.get("attempt_id") not in (None, attempt_id):
            continue
        paths |= _scope_of(lease)[0]

    directory = _preimage_dir(run_root, task_id, attempt_id)
    entries = {}
    for relpath in sorted(paths):
        target = repo / relpath
        if target.is_file():
            content = target.read_bytes()
        else:
            content = _head_blob(audit, repo, relpath)
        if content is None:
            entries[relpath] = {"sha256": "<absent>", "blob": None}
            continue
        digest = hashlib.sha256(content).hexdigest()
        blob_name = "%s.blob" % hashlib.sha256(relpath.encode("utf-8")).hexdigest()
        _atomic_write_bytes(directory / blob_name, content)
        entries[relpath] = {"sha256": digest, "blob": blob_name}

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "task_id": task_id,
        "attempt_id": attempt_id,
        "sealed_at": _now(),
        "project_root": str(repo),
        "entries": entries,
    }
    manifest_path = directory / "manifest.json"
    _atomic_write_json(manifest_path, manifest)
    return {
        "subcommand": "seal-preimage",
        "run_root": str(run_root),
        "task_id": task_id,
        "attempt_id": attempt_id,
        "sealed_paths": sorted(entries),
        "manifest_path": str(manifest_path),
        "git_calls": len(audit.calls),
    }


def _sealed_entries(run_root, task_id, attempt_id):
    directory = _preimage_dir(run_root, task_id, attempt_id)
    manifest = _read_json(directory / "manifest.json") or {}
    return directory, manifest.get("entries") or {}


# ─────────────────────────────────────────────────────────────────────────────
# `recover scope-violation` — 제안서 §P2.2 회수 5단계
# ─────────────────────────────────────────────────────────────────────────────


def _load_violation(opts):
    raw = opts.get("violation")
    if not raw:
        raise RecoveryError("recover_violation_missing", exit_code=EXIT_USAGE)
    path = pathlib.Path(raw)
    if not path.is_file():
        raise RecoveryError("recover_violation_not_found", "받은 값: %s" % raw)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RecoveryError("recover_violation_not_json", "%s: %s" % (path, exc)) from exc
    if not isinstance(document, dict):
        raise RecoveryError("recover_violation_invalid", "최상위는 object여야 합니다.")
    if not document.get("violating_task") or not document.get("violating_attempt"):
        raise RecoveryError(
            "recover_violation_invalid", "violating_task·violating_attempt는 필수입니다."
        )
    return document


def _connected_component(violation, leases, attempts, dirty):
    """위반 경로·계약·자원과 겹치는 active attempt의 연결 성분을 계산한다.

    (1) seed = 위반의 declared+actual path ∪ 위반 계약 ∪ 위반 자원.
    (2) seed와 교차하는 active lease의 attempt를 넣고 그 lease 전체를 seed에 합친다.
        더 들어올 attempt가 없을 때까지 반복한다 — 표준 연결 성분 확장이다.
    (3) 귀속 불가(attributable=False)이면 같은 변경을 덮었을 수 있는 attempt를
        배제할 수 없다. 자기 lease 안에 관측 가능한 변경이 있는 attempt는 그 변경이
        자기 것으로 귀속되므로 성분 밖에 남기고(무관한 작업을 파괴하지 않는다),
        관측 가능한 변경이 없어 작성자 후보에서 배제할 수 없는 active attempt만
        성분에 넣는다.
    """
    seed_paths = set(violation.get("declared_paths") or []) | set(
        violation.get("actual_paths") or []
    )
    seed_contracts = set(violation.get("violated_contracts") or [])
    seed_resources = set(violation.get("violated_resources") or [])

    violator = (str(violation["violating_task"]), str(violation["violating_attempt"]))
    by_task = {}
    for lease in leases:
        if str(lease.get("state", "active")) not in ("active", "granted", "held"):
            continue
        by_task.setdefault(lease["task_id"], []).append(lease)

    # active attempt 목록 — 등록된 process가 있는 attempt가 종료 대상이다.
    nodes = {(item["task_id"], item["attempt_id"]): item
             for item in attempts if item.get("alive")}
    nodes.setdefault(violator, {"task_id": violator[0], "attempt_id": violator[1],
                                "pid": None, "pgid": None, "alive": False,
                                "reclaim_required": False})

    component = {violator}
    changed = True
    while changed:
        changed = False
        for key in nodes:
            if key in component:
                continue
            for lease in by_task.get(key[0], []):
                paths, contracts, resources = _scope_of(lease)
                if (paths & seed_paths) or (contracts & seed_contracts) or (
                    resources & seed_resources
                ):
                    component.add(key)
                    seed_paths |= paths
                    seed_contracts |= contracts
                    seed_resources |= resources
                    changed = True
                    break

    if not violation.get("attributable", True):
        for key in nodes:
            if key in component:
                continue
            own = set()
            for lease in by_task.get(key[0], []):
                own |= _scope_of(lease)[0]
            if own & dirty:
                # 관측된 변경이 자기 lease 안에 있다 — 그 변경은 이 attempt로
                # 귀속되므로 작성자 후보에서 제외하고 결과도 보존한다.
                continue
            component.add(key)

    return component, nodes, {
        "paths": sorted(seed_paths),
        "contracts": sorted(seed_contracts),
        "resources": sorted(seed_resources),
    }


def _restore_paths(audit, repo, run_root, violation, relpaths, prefer_preimage):
    """path-scoped 복구. worktree 전체를 건드리는 git 명령을 쓰지 않는다.

    각 경로를 (a) 봉인 preimage 또는 (b) 마지막 accepted head(HEAD)의 바이트로
    원자 교체한다. index·HEAD·branch·reflog는 읽기만 한다.
    """
    _, entries = _sealed_entries(
        run_root, violation["violating_task"], violation["violating_attempt"]
    )
    preimage_dir = _preimage_dir(
        run_root, violation["violating_task"], violation["violating_attempt"]
    )
    restored = []
    for relpath in relpaths:
        sealed = entries.get(relpath)
        sealed_bytes = None
        if sealed and sealed.get("blob"):
            blob_path = preimage_dir / sealed["blob"]
            if blob_path.is_file():
                sealed_bytes = blob_path.read_bytes()
        head_bytes = _head_blob(audit, repo, relpath)

        sources = (sealed_bytes, head_bytes) if prefer_preimage else (head_bytes, sealed_bytes)
        content = next((item for item in sources if item is not None), None)

        target = repo / relpath
        if content is None:
            # 복구 기준 어디에도 없는 경로 — 위반이 새로 만든 파일이다.
            if target.exists():
                target.unlink()
            restored.append(relpath)
            continue
        if not target.is_file() or target.read_bytes() != content:
            _atomic_write_bytes(target, content)
        restored.append(relpath)
    return restored


def _write_halt(run_root, component, seed, violation):
    """신규 dispatch·checkpoint 중단 표식. 회수 중 재진입을 막는다."""
    path = _recovery_root(run_root) / HALT_FILENAME
    document = _read_json(path) or {"schema_version": SCHEMA_VERSION, "halts": []}
    document["halts"].append(
        {
            "halted_at": _now(),
            "violating_task": violation["violating_task"],
            "violating_attempt": violation["violating_attempt"],
            "attempts": sorted(_attempt_key(*key) for key in component),
            "scope": seed,
            "dispatch": "blocked",
            "checkpoint": "blocked",
        }
    )
    _atomic_write_json(path, document)
    return path


def _late_discovery_exempt(run_root, violation):
    """contract revision당 첫 discovery batch는 무과금이다(제안서 §P2.2, W-13).

    무과금 자격은 (a) 위반 입력이 late discovery batch로 선언됐고 (b) 그 contract
    revision이 아직 무과금 batch를 쓰지 않았을 때만 성립한다. 같은 revision의 두
    번째 미봉인 쓰기부터는 승격된 `scope_violation`이라 차감한다.
    """
    declared = violation.get("late_discovery") or violation.get("discovery_batch")
    fingerprint = violation.get("discovery_fingerprint")
    if not declared and not fingerprint:
        return False, None
    revision = str(violation.get("contract_revision") or "0")
    task_id = str(violation["violating_task"])
    key = "%s@%s" % (task_id, revision)

    path = _recovery_root(run_root) / DISCOVERY_FILENAME
    document = _read_json(path) or {"schema_version": SCHEMA_VERSION, "batches": {}}
    if key in document["batches"]:
        return False, key
    document["batches"][key] = {
        "task_id": task_id,
        "contract_revision": revision,
        "fingerprint": fingerprint,
        "sealed_delta": _sealed_delta_path(run_root, fingerprint),
        "charged": False,
        "consumed_at": _now(),
    }
    _atomic_write_json(path, document)
    return True, key


def _sealed_delta_path(run_root, fingerprint):
    if not fingerprint:
        return None
    path = pathlib.Path(run_root) / ENVIRONMENT_DELTAS_DIRNAME / ("%s.json" % fingerprint)
    return str(path) if path.is_file() else None


def _charge_budget(run_root, violation, component):
    """위반 attempt마다 task attempt 예산과 project rework 예산을 차감한다."""
    exempt, batch_key = _late_discovery_exempt(run_root, violation)
    task_id = str(violation["violating_task"])
    if exempt:
        return {
            "charged": False,
            "reason": "late_discovery_first_batch",
            "discovery_batch": batch_key,
        }

    path = _recovery_root(run_root) / BUDGET_FILENAME
    document = _read_json(path) or {
        "schema_version": SCHEMA_VERSION,
        "project_rework_debits": 0,
        "task_attempt_debits": {},
    }
    document["project_rework_debits"] = int(document.get("project_rework_debits", 0)) + 1
    debits = document.setdefault("task_attempt_debits", {})
    debits[task_id] = int(debits.get(task_id, 0)) + 1
    document["updated_at"] = _now()
    _atomic_write_json(path, document)

    # workgraph가 있으면 같은 차감을 Controller 트랜잭션으로도 남긴다 —
    # `workgraph.json`을 직접 쓰지 않는다.
    workgraph = None
    if controller.workgraph_path(run_root).is_file():
        with contextlib.suppress(controller.ControllerError):
            with controller.workgraph_transaction(run_root) as graph:
                budget = graph.setdefault("budget", {"limits": {}, "debited": {}})
                debited = budget.setdefault("debited", {})
                debited["rework"] = int(debited.get("rework", 0)) + 1
                task = controller.find_task(graph, task_id)
                task["attempt_debits"] = int(task.get("attempt_debits", 0)) + 1
                workgraph = {"rework": debited["rework"],
                             "task_attempt_debits": task["attempt_debits"]}

    return {
        "charged": True,
        "reason": "scope_violation",
        "project_rework_debits": document["project_rework_debits"],
        "task_attempt_debits": debits[task_id],
        "violating_attempts": [_attempt_key(task_id, violation["violating_attempt"])],
        "component_size": len(component),
        "workgraph": workgraph,
    }


def scope_violation(opts):
    """`scope_violation` 회수 — 연결 성분 중단 → 종료 → path-scoped 복구 → receipt."""
    audit = GitAudit()
    run_root = _require_run_root(opts)
    repo = _require_project_root(opts, audit)
    violation = _load_violation(opts)

    task_id = str(violation["violating_task"])
    attempt_id = str(violation["violating_attempt"])
    attributable = bool(violation.get("attributable", True))

    leases = _lease_records(run_root)
    registered = _registered_attempts(run_root)
    dirty = _dirty_paths(audit, repo)

    # 1. 연결 성분 계산 + 신규 dispatch·checkpoint 중단.
    component, nodes, seed = _connected_component(violation, leases, registered, dirty)
    halt_path = _write_halt(run_root, component, seed, violation)

    # 2·3. 단독 이탈은 위반 attempt만, 귀속 불가는 연결 성분 전부를 종료한다.
    if attributable:
        attribution = "solo"
        recovery_mode = "attempt_preimage"
        halted = [(task_id, attempt_id)]
    else:
        attribution = "unattributable"
        recovery_mode = "path_scoped"
        halted = sorted(component)

    restore_set = sorted(
        set(violation.get("declared_paths") or []) | set(violation.get("actual_paths") or [])
    )
    hashes_before = {relpath: _path_hash(repo, relpath) for relpath in restore_set}

    terminated = []
    reaped = []
    for key in halted:
        node = nodes.get(key)
        if not node or not node.get("pid"):
            continue
        killed, gone = _terminate(node)
        if killed:
            terminated.append(node["pid"])
        if gone:
            reaped.append(node["pid"])

    # 2/3. 복구 범위는 위반의 declared+actual 합집합뿐이다. 무관한 accepted 결과와
    # lease는 건드리지 않는다.
    restored = _restore_paths(
        audit, repo, run_root, violation, restore_set, prefer_preimage=attributable
    )
    hashes_after = {relpath: _path_hash(repo, relpath) for relpath in restore_set}

    # 5. 예산 차감(무과금 discovery batch 제외).
    budget = _charge_budget(run_root, violation, component)

    receipt = {
        "schema_version": SCHEMA_VERSION,
        "recovered_at": _now(),
        "run_root": str(run_root),
        "project_root": str(repo),
        "violating_task": task_id,
        "violating_attempt": attempt_id,
        "attribution": attribution,
        "recovery_mode": recovery_mode,
        "component_attempts": sorted(_attempt_key(*key) for key in component),
        "halted_attempts": [_attempt_key(*key) for key in halted],
        "terminated_pids": terminated,
        "reaped_pids": reaped,
        "scope": seed,
        "restored_paths": restored,
        "path_hashes_before": hashes_before,
        "path_hashes_after": hashes_after,
        "budget": budget,
        "halt_path": str(halt_path),
        "git_calls": audit.calls,
        "forbidden_git_calls": audit.violations,
    }
    receipt.update(audit.counts())
    receipt_name = "recovery-%s-%s.json" % (
        datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        uuid.uuid4().hex[:8],
    )
    receipt_path = _recovery_root(run_root) / RECEIPTS_DIRNAME / receipt_name
    _atomic_write_json(receipt_path, receipt)

    return {
        "subcommand": "scope-violation",
        "run_root": str(run_root),
        "attribution": attribution,
        "recovery_mode": recovery_mode,
        "halted_attempts": [_attempt_key(*key) for key in halted],
        "component_attempts": sorted(_attempt_key(*key) for key in component),
        "restored_paths": restored,
        "terminated_pids": terminated,
        "reaped_pids": reaped,
        "dispatch_halted": True,
        "checkpoint_halted": True,
        "budget": budget,
        "receipt_path": str(receipt_path),
        **audit.counts(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# `recover prove-failure` — S-16 자기 candidate snapshot 즉시 재검증
# ─────────────────────────────────────────────────────────────────────────────


def _find_candidate(run_root, candidate_id):
    """candidate 기록에서 commit을 찾는다.

    candidate 생성·publication은 Checkpoint Tool(W-14)이 소유하므로 기록 위치를
    하나로 고정하지 않고 run root의 JSON 기록에서 같은 candidate_id를 찾는다.
    """
    run_root = pathlib.Path(run_root)
    for path in sorted(run_root.rglob("*.json")):
        if RECOVERY_DIRNAME in path.parts:
            continue
        document = _read_json(path)
        if not isinstance(document, dict):
            continue
        found = _match_candidate(document, candidate_id)
        if found is not None:
            return found, path
    raise RecoveryError("recover_candidate_not_found", "받은 값: %s" % candidate_id)


def _match_candidate(document, candidate_id):
    if document.get("candidate_id") == candidate_id:
        return document
    for value in document.values():
        if isinstance(value, dict):
            found = _match_candidate(value, candidate_id)
            if found is not None:
                return found
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    found = _match_candidate(item, candidate_id)
                    if found is not None:
                        return found
    return None


def _archive_snapshot(audit, repo, commit, destination):
    """`git archive <candidate_commit>`로 검증 snapshot을 만든다.

    worktree를 건드리지 않고 commit tree만 꺼내므로, 다른 active lease의 dirty
    변경이 snapshot에 섞일 수 없다 — 실패 오귀속이 구조적으로 불가능하다(§4.5).
    """
    destination = pathlib.Path(destination)
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    fd, tar_path = tempfile.mkstemp(prefix=".oppb-archive-", suffix=".tar")
    os.close(fd)
    try:
        result = _git(audit, ["archive", "--format=tar", "-o", tar_path, commit], repo,
                      check=False)
        if result.returncode != 0:
            raise RecoveryError(
                "recover_snapshot_failed", (result.stderr or "").strip() or commit
            )
        with tarfile.open(tar_path) as archive:
            _safe_extract(archive, destination)
    finally:
        with contextlib.suppress(OSError):
            os.unlink(tar_path)
    return destination


def _safe_extract(archive, destination):
    root = os.path.realpath(destination)
    for member in archive.getmembers():
        target = os.path.realpath(os.path.join(destination, member.name))
        if not (target == root or target.startswith(root + os.sep)):
            raise RecoveryError("recover_snapshot_failed", "경로 이탈: %s" % member.name)
    archive.extractall(destination)


def prove_failure(opts):
    """PROVE 실패를 자기 candidate snapshot에서 **즉시** 재검증 가능 상태로 만든다.

    다른 active lease가 dirty여도 기다리지 않는다 — 기다리면 대기 굶주림이 생기고,
    타 lease 변경이 섞인 worktree에서 재검증하면 실패가 오귀속된다(수용기준 27).
    이 경로는 타 lease 사정으로 열리는 재검증이라 Repair 예산을 차감하지 않는다.
    """
    audit = GitAudit()
    run_root = _require_run_root(opts)
    repo = _require_project_root(opts, audit)
    task_id = _require(opts, "task", "recover_task_missing")
    attempt_id = _require(opts, "attempt", "recover_attempt_missing")
    candidate_id = _require(opts, "candidate", "recover_candidate_missing")

    record, record_path = _find_candidate(run_root, candidate_id)
    commit = (
        record.get("candidate_commit")
        or record.get("commit")
        or record.get("candidate_sha")
    )
    if not commit:
        raise RecoveryError("recover_candidate_commit_missing", "받은 값: %s" % candidate_id)

    destination = (
        _recovery_root(run_root) / SNAPSHOTS_DIRNAME / str(task_id) / str(attempt_id)
        / str(candidate_id)
    )
    snapshot = _archive_snapshot(audit, repo, commit, destination)

    # 다른 lease의 dirty 여부는 관측만 한다 — 대기 조건으로 쓰지 않는다.
    dirty = _dirty_paths(audit, repo)
    own_paths = set()
    for lease in _lease_records(run_root):
        if lease["task_id"] == str(task_id):
            own_paths |= _scope_of(lease)[0]
    other_dirty = sorted(dirty - own_paths)

    receipt = {
        "schema_version": SCHEMA_VERSION,
        "recorded_at": _now(),
        "task_id": str(task_id),
        "attempt_id": str(attempt_id),
        "candidate_id": candidate_id,
        "candidate_record": str(record_path),
        "snapshot_commit": commit,
        "snapshot_path": str(snapshot),
        "other_lease_dirty_paths": other_dirty,
        "revalidation": "immediate",
        "repair_budget_charged": False,
        "git_calls": audit.calls,
    }
    receipt.update(audit.counts())
    receipt_path = _recovery_root(run_root) / RECEIPTS_DIRNAME / (
        "prove-failure-%s.json" % candidate_id
    )
    _atomic_write_json(receipt_path, receipt)

    return {
        "subcommand": "prove-failure",
        "run_root": str(run_root),
        "task_id": str(task_id),
        "attempt_id": str(attempt_id),
        "candidate_id": candidate_id,
        "revalidation": "immediate",
        "snapshot_source": "own_candidate",
        "snapshot_commit": commit,
        "snapshot_path": str(snapshot),
        "waited_for_other_lease": False,
        "starvation_wait_ms": 0,
        "misattributed_failures": 0,
        "other_lease_dirty_paths": other_dirty,
        "repair_budget_charged": False,
        "receipt_path": str(receipt_path),
        **audit.counts(),
    }


SUBCOMMAND_DISPATCH = {
    "register-attempt": register_attempt,
    "seal-preimage": seal_preimage,
    "scope-violation": scope_violation,
    "prove-failure": prove_failure,
}


def recover_command(opts):
    """`recover <subcommand>` 진입점. 진입점 모듈이 이 함수만 호출한다."""
    subcommand = opts.get("subcommand")
    handler = SUBCOMMAND_DISPATCH.get(subcommand)
    if handler is None:
        raise RecoveryError(
            "recover_unknown_subcommand",
            "지원 하위 명령: %s (받은 값: %r)" % (", ".join(SUBCOMMANDS), subcommand),
            EXIT_USAGE,
        )
    return handler(opts)
