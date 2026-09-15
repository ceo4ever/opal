"""
@header {
  "module": "checkpoint",
  "task": "132",
  "layer": "util",
  "domain": "oppb-runtime",
  "description": "OPPB Checkpoint Tool — 프로젝트 worktree의 유일한 Git writer다. candidate 생성은 `GIT_INDEX_FILE` 임시 index + `write-tree` + `commit-tree`로 수행해 project branch·HEAD·공유 index를 전혀 건드리지 않고 병렬로 돌아간다. project branch를 전진시키는 publication 구간만 run root의 짧은 전역 lock으로 직렬화하고, 검증 통과 candidate만 expected parent 비교 뒤 `update-ref <ref> <new> <old>` compare-and-swap으로 fast-forward한다. parent가 이미 전진한 candidate는 `STALE_PARENT`로 거부하고 반영하지 않는다. Runner의 Git 상태 변경은 HEAD sha·HEAD symbolic ref·공유 index 지문·HEAD reflog 지문 4축 baseline 대조로 감지하며, lease 밖 tracked 쓰기와 공유 지식(MEMORY·brain) 쓰기도 checkpoint 거부 사유다. 검증 snapshot은 `git archive <candidate_commit>`으로 만든다. 실패·거부 경로는 candidate를 폐기할 뿐 branch·HEAD·공유 index를 되돌리지 않으며 `reset --hard`·worktree 전체 restore·`clean`·`worktree remove`를 호출하지 않는다(제안서 §4.5 [MUST]). 복구는 path-scoped 수단만 쓴다. `worktree-tool finalize` 전 사전 검사(active lease 0·미처리 result 0·checkpoint 밖 dirty source 0·MEMORY/brain diff 0)는 `pre-finalize`가 외부에서 수행하며 `worktree_tool.py`를 수정하지 않는다. scope hash·lease 정규화는 controller를 호출하고 재구현하지 않는다. 원자 쓰기는 `ledger.py:336-377` 형태만 복제한다(oppl-runtime-tool import 금지). 표준 라이브러리와 git CLI만 사용하고 플랫폼 분기를 두지 않는다.",
  "exports": [
    "ERROR_CODES", "CheckpointError", "SUBCOMMANDS",
    "checkpoint_dir", "candidate_receipt_path", "baseline_path", "publication_lock_path",
    "git_state_fingerprint", "read_baseline", "record_baseline",
    "load_active_leases", "dirty_paths", "classify_writes",
    "create_candidate", "publish_candidate", "archive_candidate",
    "pre_finalize_check", "checkpoint_command"
  ],
  "depends": [
    "git CLI 2.x",
    "opal/tools/oppb-runtime-tool/controller.py",
    "opal/tools/oppb-runtime-tool/lease.py",
    "opal/core/references/harness/tool-output-contract.md"
  ]
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
import subprocess
import tempfile
import uuid

import controller
import lease

SCHEMA_VERSION = "1.0"

EXIT_ERROR = 1
EXIT_USAGE = 2

CHECKPOINT_DIRNAME = "checkpoint"
CANDIDATES_DIRNAME = "candidates"
BASELINE_FILENAME = "git-baseline.json"
PUBLICATION_LOCK_FILENAME = "publication.lock"
TMP_INDEX_DIRNAME = "tmp-index"

# lease store(`leases.json`)의 유일한 writer는 W-12 `lease.py`다. checkpoint는
# 그 모듈의 공개 reader(`read_leases`·`active_leases`)만 호출하고 위치·표기를
# 재구현하지 않는다.

# lease 기록에서 tracked write 축을 읽을 때 허용하는 키 이름.
# spec 표기(`tracked_write_set`)와 controller 정규형(`tracked_writes`)을 모두 받는다.
TRACKED_KEYS = ("tracked_writes", "tracked_write_set", "tracked")
EPHEMERAL_KEYS = ("ephemeral_writes", "ephemeral_write_set")
CONTRACT_KEYS = ("contracts",)
RESOURCE_KEYS = ("runtime_resources",)

# 공유 지식 — Runner가 쓸 권한이 없는 경로. 접두 또는 파일명으로 판정한다.
SHARED_KNOWLEDGE_BASENAMES = ("MEMORY.md", "MEMORY.json")
SHARED_KNOWLEDGE_PREFIXES = ("brain/", ".opal/brain/", "docs/brain/")

VERIFICATION_VALUES = ("pass", "fail")

SUBCOMMANDS = ("candidate", "publish", "guard", "snapshot", "pre-finalize")

ERROR_CODES = {
    # 공개 응답에 그대로 노출되는 판정 코드 (대문자) — S-12·S-13 계약
    "CHECKPOINT_REJECTED": "checkpoint가 거부되었습니다 — 이탈 쓰기 또는 Git 상태 변경.",
    "CANDIDATE_DISCARDED": "검증에 실패한 candidate를 폐기했습니다 — branch는 전진하지 않습니다.",
    "STALE_PARENT": "candidate의 parent가 더 이상 branch head가 아닙니다 — 반영하지 않습니다.",
    "PRE_FINALIZE_BLOCKED": "finalize 사전 검사가 통과하지 못했습니다.",
    # 입력·환경 오류 (소문자 snake — 기존 도구 관례)
    "checkpoint_usage": "checkpoint 서브 명령 인자가 올바르지 않습니다.",
    "checkpoint_task_missing": "--task는 필수입니다.",
    "checkpoint_attempt_missing": "--attempt는 필수입니다.",
    "checkpoint_candidate_missing": "--candidate는 필수입니다.",
    "checkpoint_verification_invalid": "--verification은 pass 또는 fail이어야 합니다.",
    "checkpoint_candidate_not_found": "candidate 영수증을 찾을 수 없습니다.",
    "checkpoint_candidate_already_published": "이미 publication된 candidate입니다.",
    "checkpoint_lease_store_unavailable": (
        "run root에서 lease 기록을 찾을 수 없습니다 — `lease acquire`가 선행해야 합니다."
    ),
    "checkpoint_lease_not_found": "요청한 task/attempt의 active lease가 없습니다.",
    "checkpoint_git_failed": "git 명령이 실패했습니다.",
    "checkpoint_detached_head": "프로젝트 worktree의 HEAD가 branch를 가리키지 않습니다.",
    "checkpoint_dest_missing": "--dest는 필수입니다.",
}


class CheckpointError(Exception):
    """폐쇄 집합 `ERROR_CODES`의 코드 하나로 실패를 표현한다."""

    def __init__(self, code, message="", exit_code=EXIT_ERROR, **extra):
        super().__init__(message or code)
        self.code = code
        self.message = message
        self.exit_code = exit_code
        self.extra = extra


def _now():
    return (
        datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    )


# ─────────────────────────────────────────────────────────────────────────────
# run root 경로
# ─────────────────────────────────────────────────────────────────────────────


def checkpoint_dir(run_root):
    return pathlib.Path(run_root) / CHECKPOINT_DIRNAME


def candidates_dir(run_root):
    return checkpoint_dir(run_root) / CANDIDATES_DIRNAME


def candidate_receipt_path(run_root, candidate_id):
    return candidates_dir(run_root) / ("%s.json" % candidate_id)


def baseline_path(run_root):
    return checkpoint_dir(run_root) / BASELINE_FILENAME


def publication_lock_path(run_root):
    return checkpoint_dir(run_root) / PUBLICATION_LOCK_FILENAME


# ─────────────────────────────────────────────────────────────────────────────
# 원자 쓰기 — ledger.py:336-377 패턴을 형태만 복제한다(TOOL-BOUNDARY §7-3).
# oppl-runtime-tool을 import하지 않고, 공용 추출도 이 태스크에서 시도하지 않는다.
# ─────────────────────────────────────────────────────────────────────────────


def _atomic_write_json(path, payload):
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


def _read_json(path):
    path = pathlib.Path(path)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


@contextlib.contextmanager
def _publication_lock(run_root):
    """publication 구간 전용 전역 lock.

    candidate 생성은 이 lock을 잡지 않는다 — ref를 건드리지 않으므로 직렬화할
    이유가 없다(제안서 §4.5 "publication 구간만 짧은 전역 lock"). branch를
    전진시키는 구간만 여기서 직렬화된다.
    """
    path = publication_lock_path(run_root)
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


# ─────────────────────────────────────────────────────────────────────────────
# git 호출
#   - 항상 PATH의 `git`을 리스트 인자(shell=False)로 부른다. 절대경로로 우회하면
#     감사(audit) 채널이 끊기므로 금지다.
#   - 파괴적 명령(`reset --hard` · 전체 `restore`/`checkout -- .` · `clean -fd` ·
#     `worktree remove`)은 이 모듈 어디에서도 호출하지 않는다(제안서 §4.5 [MUST]).
# ─────────────────────────────────────────────────────────────────────────────

# commit-tree는 identity를 요구한다. 전역 git config에 의존하지 않도록 주입한다.
_IDENTITY_ENV = {
    "GIT_AUTHOR_NAME": "OPAL OPPB Checkpoint",
    "GIT_AUTHOR_EMAIL": "oppb-checkpoint@opal.local",
    "GIT_COMMITTER_NAME": "OPAL OPPB Checkpoint",
    "GIT_COMMITTER_EMAIL": "oppb-checkpoint@opal.local",
}


def _git(args, cwd, env_overrides=None, check=True):
    env = os.environ.copy()
    env.update(_IDENTITY_ENV)
    if env_overrides:
        env.update(env_overrides)
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=env,
    )
    if check and result.returncode != 0:
        raise CheckpointError(
            "checkpoint_git_failed",
            "git %s: %s" % (" ".join(args), (result.stderr or result.stdout).strip()),
        )
    return result


def _git_out(args, cwd, env_overrides=None):
    return _git(args, cwd, env_overrides).stdout.strip()


def _digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Runner Git 상태 변경 감지 — 4축 지문
# ─────────────────────────────────────────────────────────────────────────────


def git_state_fingerprint(project_root):
    """프로젝트 worktree의 Git 상태 지문.

    네 축을 함께 본다. 어느 하나만으로는 Runner의 commit·checkout·reset을 모두
    잡지 못한다 — 실측 결과 `reset --soft HEAD~0`은 branch reflog를 남기지 않고
    **HEAD reflog**만 늘리며, `checkout -b`는 sha를 바꾸지 않고 symbolic ref만
    바꾼다. 읽기 전용 명령만 사용한다(`ls-files`/`reflog`는 index를 쓰지 않는다).
    """
    head_ref = _git(["symbolic-ref", "-q", "HEAD"], cwd=project_root, check=False)
    return {
        "head_sha": _git_out(["rev-parse", "HEAD"], cwd=project_root),
        "head_ref": head_ref.stdout.strip(),
        "index_digest": _digest(_git(["ls-files", "-s"], cwd=project_root).stdout),
        "head_reflog_digest": _digest(
            _git(["reflog", "show", "HEAD"], cwd=project_root, check=False).stdout
        ),
    }


def read_baseline(run_root):
    document = _read_json(baseline_path(run_root))
    if isinstance(document, dict):
        return document.get("fingerprint")
    return None


def record_baseline(run_root, project_root, actor=None):
    """checkpoint가 소유하는 Git 상태 기록을 현재 값으로 갱신한다.

    checkpoint 자신이 branch를 전진시킨 직후에도 호출한다 — 그래야 다음 호출이
    "checkpoint가 만든 변화"를 Runner 위반으로 오판하지 않는다.
    """
    fingerprint = git_state_fingerprint(project_root)
    _atomic_write_json(
        baseline_path(run_root),
        {
            "schema_version": SCHEMA_VERSION,
            "recorded_at": _now(),
            "actor": actor,
            "project_root": str(project_root),
            "fingerprint": fingerprint,
        },
    )
    return fingerprint


def diff_fingerprint(before, after):
    if not before:
        return []
    return sorted(key for key in after if before.get(key) != after.get(key))


# ─────────────────────────────────────────────────────────────────────────────
# lease view — W-12 lease store를 읽기 전용으로 관측한다
# ─────────────────────────────────────────────────────────────────────────────


def _first_list(record, keys):
    for key in keys:
        value = record.get(key)
        if isinstance(value, list):
            return value
    return []


def _as_paths(values):
    """tracked/ephemeral 축은 문자열 또는 `{"path": ...}` 표기를 모두 받는다."""
    paths = []
    for value in values:
        if isinstance(value, str):
            paths.append(value)
        elif isinstance(value, dict) and isinstance(value.get("path"), str):
            paths.append(value["path"])
    return paths


def _normalize_lease_record(record):
    if not isinstance(record, dict):
        return None
    inner = record
    for key in ("lease", "spec", "scope"):
        nested = record.get(key)
        if isinstance(nested, dict):
            inner = {**nested, **{k: v for k, v in record.items() if k != key}}
            break
    task_id = inner.get("task_id") or inner.get("task")
    if not task_id:
        return None
    lease_axes = {
        "tracked_writes": _as_paths(_first_list(inner, TRACKED_KEYS)),
        "ephemeral_writes": _as_paths(_first_list(inner, EPHEMERAL_KEYS)),
        "contracts": [v for v in _first_list(inner, CONTRACT_KEYS) if isinstance(v, str)],
        "runtime_resources": [
            v for v in _first_list(inner, RESOURCE_KEYS) if isinstance(v, str)
        ],
    }
    return {
        "task_id": str(task_id),
        "attempt_id": str(inner.get("attempt_id") or inner.get("attempt") or ""),
        "role": inner.get("role") or "runner",
        "state": inner.get("state") or "active",
        # scope hash·정규화는 controller가 소유한다 — 여기서 재구현하지 않는다.
        "lease": controller.normalize_lease(lease_axes),
        "scope_hash": controller.compute_scope_hash(lease_axes),
    }


def load_active_leases(run_root):
    """run root의 lease 기록에서 active lease 목록을 읽는다.

    lease store는 W-12(`lease.py`)가 소유한다. checkpoint는 위치와 표기 차이를
    흡수하는 읽기 전용 view만 갖고, 쓰기·회수는 하지 않는다.
    """
    run_root = pathlib.Path(run_root)
    if not lease.leases_path(run_root).exists():
        raise CheckpointError("checkpoint_lease_store_unavailable", "run_root=%s" % run_root)

    document = lease.read_leases(run_root)
    leases = []
    for record in lease.active_leases(document):
        normalized = _normalize_lease_record(record)
        if normalized:
            leases.append(normalized)
    return leases


def find_lease(leases, task_id, attempt_id):
    for held in leases:
        if held["task_id"] != str(task_id):
            continue
        if attempt_id and held["attempt_id"] and held["attempt_id"] != str(attempt_id):
            continue
        return held
    raise CheckpointError(
        "checkpoint_lease_not_found", "task=%s attempt=%s" % (task_id, attempt_id)
    )


# ─────────────────────────────────────────────────────────────────────────────
# 작업 트리 관측과 쓰기 귀속(attribution)
# ─────────────────────────────────────────────────────────────────────────────


def _zsplit(text):
    return [token for token in text.split("\0") if token]


def dirty_paths(project_root):
    """HEAD 대비 변경된 tracked 경로 + 미추적 경로를 mtime과 함께 돌려준다.

    반환: {relpath: mtime_ns}. 삭제된 경로는 mtime 0으로 남긴다.
    """
    modified = _zsplit(
        _git(["diff", "--name-only", "-z", "HEAD"], cwd=project_root).stdout
    )
    untracked = _zsplit(
        _git(
            ["ls-files", "--others", "--exclude-standard", "-z"], cwd=project_root
        ).stdout
    )
    staged = _zsplit(
        _git(["diff", "--name-only", "-z", "--cached", "HEAD"], cwd=project_root).stdout
    )
    observed = {}
    for relpath in list(modified) + list(untracked) + list(staged):
        full = pathlib.Path(project_root) / relpath
        try:
            observed[relpath] = full.stat().st_mtime_ns
        except OSError:
            observed[relpath] = 0
    return observed


def is_shared_knowledge(relpath):
    name = relpath.rsplit("/", 1)[-1]
    if name in SHARED_KNOWLEDGE_BASENAMES:
        return True
    return any(relpath.startswith(prefix) for prefix in SHARED_KNOWLEDGE_PREFIXES)


def classify_writes(observed, lease_paths):
    """dirty 경로를 호출 attempt 기준으로 분류한다.

    귀속 규칙(제안서 §4.5 "귀속 불가는 연결 성분만 중단", TEST-SCENARIO S-12):
    checkpoint를 호출하는 attempt는 **자기 lease 경로에 대한 쓰기를 이미 끝낸**
    상태다. 따라서 자기 lease 경로의 마지막 쓰기 시점(`own_marker`)보다 **나중에**
    바뀐 lease 밖 경로는 그 attempt가 자기 구간을 벗어나 쓴 것으로 귀속된다.
    `own_marker`보다 앞선 변경은 그 시점에 함께 달리고 있던 다른 Runner의
    미완료 작업이므로 이 attempt의 위반이 아니다 — 그 변경은 소유 lease의
    candidate로 따로 들어간다. 동시각(tie)은 귀속 불가로 보고 보수적으로
    거부한다.
    """
    lease_set = set(lease_paths)
    own = {p: m for p, m in observed.items() if p in lease_set}
    foreign = {p: m for p, m in observed.items() if p not in lease_set}

    own_marker = max(own.values()) if own else None

    attributed = []
    if own_marker is not None:
        attributed = sorted(p for p, m in foreign.items() if m >= own_marker)

    shared = [p for p in attributed if is_shared_knowledge(p)]
    out_of_lease = [p for p in attributed if not is_shared_knowledge(p)]
    return {
        "own_paths": sorted(own),
        "own_marker_ns": own_marker,
        "out_of_lease": out_of_lease,
        "shared_knowledge": sorted(shared),
        "unattributed": sorted(set(foreign) - set(attributed)),
    }


def path_hashes(project_root, relpaths):
    hashes = {}
    for relpath in sorted(relpaths):
        full = pathlib.Path(project_root) / relpath
        if full.is_file():
            hashes[relpath] = hashlib.sha256(full.read_bytes()).hexdigest()
        else:
            hashes[relpath] = "<absent>"
    return hashes


# ─────────────────────────────────────────────────────────────────────────────
# candidate 생성 — ref를 바꾸지 않는 임시 index + commit-tree
# ─────────────────────────────────────────────────────────────────────────────


def _next_candidate_id(run_root, task_id, attempt_id):
    directory = candidates_dir(run_root)
    directory.mkdir(parents=True, exist_ok=True)
    prefix = "cand-%s-%s-" % (task_id, attempt_id)
    existing = [p.stem for p in directory.glob("%s*.json" % prefix)]
    sequence = len(existing) + 1
    while True:
        candidate_id = "%s%04d" % (prefix, sequence)
        if not candidate_receipt_path(run_root, candidate_id).exists():
            return candidate_id
        sequence += 1


def create_candidate(run_root, project_root, task_id, attempt_id, regenerate=False):
    run_root = pathlib.Path(run_root)
    project_root = pathlib.Path(project_root)

    leases = load_active_leases(run_root)
    lease = find_lease(leases, task_id, attempt_id)
    lease_paths = lease["lease"]["tracked_writes"]

    reasons = []
    detail = {}

    # ① Runner의 Git 상태 변경 — baseline 대조
    fingerprint = git_state_fingerprint(project_root)
    baseline = read_baseline(run_root)
    changed_axes = diff_fingerprint(baseline, fingerprint)
    if changed_axes:
        reasons.append("git_state_changed")
        detail["changed_git_axes"] = changed_axes
        detail["baseline_fingerprint"] = baseline
        detail["observed_fingerprint"] = fingerprint

    # ② lease 밖 tracked 쓰기 / ③ 공유 지식 쓰기
    observed = dirty_paths(project_root)
    classified = classify_writes(observed, lease_paths)
    if classified["out_of_lease"]:
        reasons.append("out_of_lease_write")
    if classified["shared_knowledge"]:
        reasons.append("shared_knowledge_write")

    if reasons:
        # 거부 경로는 **아무것도 되돌리지 않는다.** candidate를 만들지 않을 뿐
        # branch·HEAD·공유 index·다른 Runner의 파일에 손대지 않는다(§4.5 [MUST]).
        raise CheckpointError(
            "CHECKPOINT_REJECTED",
            "checkpoint 거부: %s" % ", ".join(reasons),
            reasons=reasons,
            violating_paths=sorted(
                classified["out_of_lease"] + classified["shared_knowledge"]
            ),
            task=str(task_id),
            attempt=str(attempt_id),
            **detail,
        )

    if baseline is None:
        # 최초 관측 — 이후 호출이 대조할 기준을 남긴다.
        record_baseline(run_root, project_root, actor="candidate:bootstrap")

    parent = fingerprint["head_sha"]
    tmp_dir = checkpoint_dir(run_root) / TMP_INDEX_DIRNAME
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_index = tmp_dir / ("%s.index" % uuid.uuid4().hex)
    index_env = {"GIT_INDEX_FILE": str(tmp_index)}
    try:
        # 공유 index는 건드리지 않는다 — 임시 index에 HEAD tree를 읽어 온다.
        _git(["read-tree", parent], cwd=project_root, env_overrides=index_env)
        staged = [p for p in classified["own_paths"]]
        for relpath in staged:
            _git(
                ["update-index", "--add", "--remove", "--", relpath],
                cwd=project_root,
                env_overrides=index_env,
            )
        tree = _git_out(["write-tree"], cwd=project_root, env_overrides=index_env)
    finally:
        with contextlib.suppress(OSError):
            tmp_index.unlink()

    message = "oppb candidate %s/%s\n\ntask: %s\nattempt: %s\n" % (
        task_id,
        attempt_id,
        task_id,
        attempt_id,
    )
    candidate_commit = _git_out(
        ["commit-tree", tree, "-p", parent, "-m", message], cwd=project_root
    )

    candidate_id = _next_candidate_id(run_root, task_id, attempt_id)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "candidate_id": candidate_id,
        "task_id": str(task_id),
        "attempt_id": str(attempt_id),
        "state": "pending",
        "parent": parent,
        "tree": tree,
        "candidate_commit": candidate_commit,
        "changed_paths": staged,
        "lease_paths": lease_paths,
        "lease_path_hashes": path_hashes(project_root, lease_paths),
        "scope_hash": lease["scope_hash"],
        "project_root": str(project_root),
        "created_at": _now(),
        "regenerated": bool(regenerate),
    }
    receipt_path = candidate_receipt_path(run_root, candidate_id)
    _atomic_write_json(receipt_path, receipt)

    if regenerate:
        _supersede_previous(run_root, task_id, attempt_id, candidate_id)

    return {
        "subcommand": "candidate",
        "candidate_id": candidate_id,
        "candidate_commit": candidate_commit,
        "parent": parent,
        "tree": tree,
        "receipt_path": str(receipt_path),
        "changed_paths": staged,
        "lease_path_hashes": receipt["lease_path_hashes"],
        "scope_hash": lease["scope_hash"],
    }


def _supersede_previous(run_root, task_id, attempt_id, keep_id):
    """재생성 시 같은 attempt의 이전 pending candidate를 superseded로 표시한다.

    표시만 한다 — Git object는 unreachable로 남겨 둘 뿐 파괴적 명령으로 지우지
    않는다(`gc`·`worktree prune` 호출 금지).
    """
    for path in sorted(candidates_dir(run_root).glob("cand-%s-%s-*.json" % (task_id, attempt_id))):
        receipt = _read_json(path)
        if not receipt or receipt.get("candidate_id") == keep_id:
            continue
        if receipt.get("state") == "pending":
            receipt["state"] = "superseded"
            receipt["superseded_by"] = keep_id
            receipt["superseded_at"] = _now()
            _atomic_write_json(path, receipt)


# ─────────────────────────────────────────────────────────────────────────────
# publication — 짧은 전역 lock 구간에서만 branch를 전진시킨다
# ─────────────────────────────────────────────────────────────────────────────


def _load_receipt(run_root, candidate_id):
    receipt = _read_json(candidate_receipt_path(run_root, candidate_id))
    if not receipt:
        raise CheckpointError("checkpoint_candidate_not_found", "candidate=%s" % candidate_id)
    return receipt


def _head_ref(project_root):
    result = _git(["symbolic-ref", "-q", "HEAD"], cwd=project_root, check=False)
    ref = result.stdout.strip()
    if not ref:
        raise CheckpointError("checkpoint_detached_head", "project_root=%s" % project_root)
    return ref


def _align_index(project_root, parent, commit, changed_paths):
    """publication된 lease 경로만 공유 index에 정합시킨다.

    경로를 지정한 `update-index`만 쓴다 — worktree 전체를 되돌리는 수단
    (`reset --hard` · `checkout -- .` · `restore`)은 쓰지 않는다(§4.5 [MUST]).
    다른 Runner의 미완료 변경은 index·worktree 모두에서 그대로 남는다.
    """
    status = _zsplit(
        _git(
            ["diff-tree", "-r", "-z", "--name-status", "--no-commit-id", parent, commit],
            cwd=project_root,
        ).stdout
    )
    # `-z`는 status와 path를 NUL로 번갈아 내보낸다.
    pairs = [
        (status[index], status[index + 1])
        for index in range(0, len(status) - 1, 2)
    ]

    for code, relpath in pairs:
        if code.startswith("D"):
            _git(["update-index", "--force-remove", "--", relpath], cwd=project_root)
            continue
        entry = _git_out(["ls-tree", commit, "--", relpath], cwd=project_root)
        if not entry:
            continue
        meta = entry.split("\t", 1)[0].split()
        if len(meta) < 3:
            continue
        mode, _kind, blob = meta[0], meta[1], meta[2]
        _git(
            ["update-index", "--add", "--cacheinfo", "%s,%s,%s" % (mode, blob, relpath)],
            cwd=project_root,
        )
    # stat 캐시만 새로 고친다. 실제로 수정된 파일이 있으면 non-zero로 끝나므로
    # 결과를 강제하지 않는다(파괴적 동작 없음).
    _git(["update-index", "-q", "--refresh"], cwd=project_root, check=False)
    return [relpath for _code, relpath in pairs]


def publish_candidate(run_root, project_root, candidate_id, verification):
    run_root = pathlib.Path(run_root)
    project_root = pathlib.Path(project_root)

    if verification not in VERIFICATION_VALUES:
        raise CheckpointError(
            "checkpoint_verification_invalid", "받은 값: %r" % verification, EXIT_USAGE
        )

    with _publication_lock(run_root):
        receipt = _load_receipt(run_root, candidate_id)
        if receipt.get("state") == "published":
            raise CheckpointError(
                "checkpoint_candidate_already_published", "candidate=%s" % candidate_id
            )

        expected_parent = receipt["parent"]

        if verification != "pass":
            # 폐기만 한다 — branch·HEAD·공유 index를 되돌리지 않는다(§4.5 [MUST]).
            receipt["state"] = "discarded"
            receipt["discarded_at"] = _now()
            receipt["verification"] = verification
            _atomic_write_json(candidate_receipt_path(run_root, candidate_id), receipt)
            raise CheckpointError(
                "CANDIDATE_DISCARDED",
                "검증 실패로 candidate를 폐기했습니다.",
                candidate_id=candidate_id,
                branch_advanced=False,
                applied=False,
                expected_parent=expected_parent,
                verification=verification,
            )

        ref = _head_ref(project_root)
        actual_parent = _git_out(["rev-parse", ref], cwd=project_root)
        if actual_parent != expected_parent:
            receipt["state"] = "stale"
            receipt["stale_at"] = _now()
            receipt["actual_parent"] = actual_parent
            _atomic_write_json(candidate_receipt_path(run_root, candidate_id), receipt)
            raise CheckpointError(
                "STALE_PARENT",
                "parent가 전진했습니다 — 새 parent에서 재생성해야 합니다.",
                candidate_id=candidate_id,
                applied=False,
                branch_advanced=False,
                expected_parent=expected_parent,
                actual_parent=actual_parent,
            )

        commit = receipt["candidate_commit"]
        # compare-and-swap — <newvalue> <oldvalue>. 경쟁 갱신이 있으면 실패한다.
        _git(["update-ref", ref, commit, expected_parent], cwd=project_root)
        aligned = _align_index(project_root, expected_parent, commit, receipt.get("changed_paths"))

        receipt["state"] = "published"
        receipt["published_at"] = _now()
        receipt["verification"] = verification
        receipt["new_head"] = commit
        _atomic_write_json(candidate_receipt_path(run_root, candidate_id), receipt)

        # checkpoint 자신이 만든 변화를 기준으로 삼는다 — 다음 호출이 이를
        # Runner 위반으로 오판하지 않게 한다.
        record_baseline(run_root, project_root, actor="publish:%s" % candidate_id)

        return {
            "subcommand": "publish",
            "candidate_id": candidate_id,
            "fast_forward": True,
            "branch_advanced": True,
            "applied": True,
            "ref": ref,
            "expected_parent": expected_parent,
            "new_head": commit,
            "aligned_paths": aligned,
        }


# ─────────────────────────────────────────────────────────────────────────────
# 검증 snapshot — git archive
# ─────────────────────────────────────────────────────────────────────────────


def archive_candidate(run_root, project_root, candidate_id, dest):
    """candidate commit에서 검증용 snapshot을 만든다.

    worktree를 재사용하거나 되돌리지 않는다 — `git archive <candidate_commit>`은
    작업 트리와 ref를 전혀 건드리지 않는 읽기 전용 수단이다(§4.5).
    """
    receipt = _load_receipt(run_root, candidate_id)
    commit = receipt["candidate_commit"]
    dest = pathlib.Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    tarball = dest / ("%s.tar" % candidate_id)
    result = _git(
        ["archive", "--format=tar", "-o", str(tarball), commit], cwd=project_root
    )
    del result
    return {
        "subcommand": "snapshot",
        "candidate_id": candidate_id,
        "candidate_commit": commit,
        "snapshot_path": str(tarball),
        "bytes": tarball.stat().st_size,
    }


# ─────────────────────────────────────────────────────────────────────────────
# finalize 사전 검사 — worktree_tool.py를 수정하지 않고 외부에서 얹는다
# ─────────────────────────────────────────────────────────────────────────────


def _unprocessed_results(run_root):
    """`attempts/<task>/<attempt>/result.json` 중 아직 소비되지 않은 것.

    Controller가 결과를 색인하면 receipt에 소비 표식이 남는다. 표식이 없고
    미니 태스크가 종료 상태도 아니면 미처리로 센다.
    """
    attempts = pathlib.Path(run_root) / "attempts"
    if not attempts.is_dir():
        return []
    terminal = set()
    document = _read_json(controller.workgraph_path(run_root)) or {}
    for task in document.get("tasks") or []:
        if task.get("state") in ("accepted", "failed", "blocked"):
            terminal.add(str(task.get("task_id") or task.get("id")))
    pending = []
    for result_path in sorted(attempts.glob("*/*/result.json")):
        task_id = result_path.parent.parent.name
        payload = _read_json(result_path) or {}
        if payload.get("processed") is True or payload.get("indexed") is True:
            continue
        if task_id in terminal:
            continue
        pending.append(str(result_path.relative_to(run_root)))
    return pending


def pre_finalize_check(run_root, project_root):
    """`worktree-tool finalize` **호출 전에** 네 항목을 외부에서 확인한다.

    `worktree_tool.py`는 수정하지 않는다(ANALYSIS Q4). finalize의 자체
    `check_guards`는 그대로 두고, OPPB가 추가로 요구하는 네 항목만 이 명령이
    선행 검사로 확인한 뒤 호출자가 finalize를 부르는 구조다.
    """
    run_root = pathlib.Path(run_root)
    project_root = pathlib.Path(project_root)

    try:
        leases = load_active_leases(run_root)
    except CheckpointError as exc:
        if exc.code != "checkpoint_lease_store_unavailable":
            raise
        leases = []
    active = [
        {"task_id": held["task_id"], "attempt_id": held["attempt_id"], "role": held["role"]}
        for held in leases
    ]

    pending_results = _unprocessed_results(run_root)

    observed = dirty_paths(project_root)
    shared_diff = sorted(p for p in observed if is_shared_knowledge(p))
    dirty_source = sorted(p for p in observed if not is_shared_knowledge(p))

    checks = {
        "active_leases": active,
        "unprocessed_results": pending_results,
        "dirty_sources_outside_checkpoint": dirty_source,
        "shared_knowledge_diff": shared_diff,
    }
    blocking = sorted(name for name, value in checks.items() if value)

    if blocking:
        raise CheckpointError(
            "PRE_FINALIZE_BLOCKED",
            "finalize 사전 검사 미통과: %s" % ", ".join(blocking),
            finalize_allowed=False,
            blocking=blocking,
            **checks,
        )
    return {
        "subcommand": "pre-finalize",
        "finalize_allowed": True,
        "blocking": [],
        **checks,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLI 진입 — oppb_runtime_tool.cmd_checkpoint가 호출한다
# ─────────────────────────────────────────────────────────────────────────────


def _require(opts, key, code):
    value = opts.get(key)
    if not value:
        raise CheckpointError(code, exit_code=EXIT_USAGE)
    return value


def _roots(opts):
    run_root = _require(opts, "run_root", "checkpoint_usage")
    project_root = _require(opts, "project_root", "checkpoint_usage")
    return pathlib.Path(run_root), pathlib.Path(project_root)


def _sub_candidate(opts):
    run_root, project_root = _roots(opts)
    return create_candidate(
        run_root,
        project_root,
        _require(opts, "task", "checkpoint_task_missing"),
        _require(opts, "attempt", "checkpoint_attempt_missing"),
        regenerate=bool(opts.get("regenerate")),
    )


def _sub_publish(opts):
    run_root, project_root = _roots(opts)
    return publish_candidate(
        run_root,
        project_root,
        _require(opts, "candidate", "checkpoint_candidate_missing"),
        opts.get("verification"),
    )


def _sub_guard(opts):
    """Runner 구간 진입 전 Git 상태 지문을 기록하거나 현재 지문을 보고한다."""
    run_root, project_root = _roots(opts)
    task = opts.get("task")
    attempt = opts.get("attempt")
    if opts.get("record_baseline"):
        fingerprint = record_baseline(
            run_root, project_root, actor="guard:%s/%s" % (task, attempt)
        )
        return {
            "subcommand": "guard",
            "recorded": True,
            "task": task,
            "attempt": attempt,
            "fingerprint": fingerprint,
        }
    fingerprint = git_state_fingerprint(project_root)
    baseline = read_baseline(run_root)
    return {
        "subcommand": "guard",
        "recorded": False,
        "task": task,
        "attempt": attempt,
        "fingerprint": fingerprint,
        "baseline": baseline,
        "changed_git_axes": diff_fingerprint(baseline, fingerprint),
    }


def _sub_snapshot(opts):
    run_root, project_root = _roots(opts)
    return archive_candidate(
        run_root,
        project_root,
        _require(opts, "candidate", "checkpoint_candidate_missing"),
        _require(opts, "dest", "checkpoint_dest_missing"),
    )


def _sub_pre_finalize(opts):
    run_root, project_root = _roots(opts)
    return pre_finalize_check(run_root, project_root)


SUBCOMMAND_DISPATCH = {
    "candidate": _sub_candidate,
    "publish": _sub_publish,
    "guard": _sub_guard,
    "snapshot": _sub_snapshot,
    "pre-finalize": _sub_pre_finalize,
}


def checkpoint_command(opts):
    subcommand = opts.get("subcommand")
    handler = SUBCOMMAND_DISPATCH.get(subcommand)
    if handler is None:
        raise CheckpointError(
            "checkpoint_usage",
            "지원 서브 명령: %s" % ", ".join(SUBCOMMANDS),
            EXIT_USAGE,
        )
    return handler(opts)
