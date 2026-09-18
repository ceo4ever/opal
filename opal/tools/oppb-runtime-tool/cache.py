"""
@header {
  "module": "cache",
  "task": "132",
  "layer": "util",
  "domain": "oppb-runtime",
  "description": "OPPB cache root(`<allocator_root>/.opal-cache/oppb/`)의 유일한 writer. source base·dependency environment·build cache 3계층을 content-addressed immutable node로 봉인하고 mutable 작업은 candidate별 overlay에서만 수행한다(제안서 §4.5). source base는 최초·복구 시 `git archive`, 이후 parent→accepted `diff-tree`의 변경·삭제·mode만 새 generation에 적용하며 materialize 결과 manifest가 candidate tree와 다르면 generation을 폐기하고 전체 archive로 복구한다. 같은 parent에서 fork한 병렬 candidate는 승자 하나만 남기지 않고 각 overlay를 별도 CAS node로 모두 봉인하며, accepted head는 단일 build-cache 파일 대신 재사용 가능한 cache DAG head set을 기록한다. stale sibling은 input 일치가 가장 크고 Git delta가 가장 작은 seed를 결정론적으로 고른 뒤 intervening accepted source delta를 replay한다 — cache 파일끼리 byte merge하지 않는다. conformance 미통과 adapter는 `non_reusable`로 강등되어 그 명령만 cold 실행한다. 용량은 soft cap과 최소 여유 공간으로 집행하고 active run·실행 중 candidate·publication 대기 node만 pin하며 closed node는 warm retention 경과 후 last-access LRU로 회수한다. 공간을 확보하지 못하면 cacheless 강등 또는 `disk_budget_exceeded`다. evidence·DONE·source code는 GC 대상이 아니다. 모든 갱신은 cache root 배타 락 아래 `mkstemp`→`fsync`→`os.replace`로 원자 교체한다(형태만 `oppl-runtime-tool/ledger.py:336-377` 복제 — 해당 도구를 import하지 않는다). 표준 라이브러리와 git CLI만 사용하고 플랫폼 분기를 두지 않는다.",
  "exports": [
    "ERROR_CODES", "CacheError", "NODE_STATES", "PINNED_STATES",
    "DEFAULT_POLICY", "read_policy", "cache_command"
  ],
  "depends": [
    "git CLI 2.x",
    "opal/tools/oppb-runtime-tool/cache_adapter_conformance.py",
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
import io
import json
import os
import pathlib
import shutil
import subprocess
import tarfile
import tempfile

import cache_adapter_conformance as conformance

SCHEMA_VERSION = "1.0"

EXIT_ERROR = 1
EXIT_USAGE = 2

LOCK_FILENAME = "cache.lock"
POLICY_FILENAME = "policy.json"
STATE_FILENAME = "cache-state.json"
PUBLICATIONS_FILENAME = "publications.json"
NODES_DIRNAME = "nodes"
OVERLAYS_DIRNAME = "overlays"
SOURCE_BASE_DIRNAME = "source-base"
PLANS_DIRNAME = "plans"
NODE_MANIFEST = "node.json"
NODE_PAYLOAD = "payload"
CANDIDATE_MANIFEST = "candidate.json"
GENERATION_MANIFEST = "generation.json"

# 제안서 §4.5 — lease로 pin되는 node 상태 3종. GC 삭제 대상이 아니다.
PINNED_STATES = ("active_run", "running_candidate", "publication_pending")
NODE_STATES = PINNED_STATES + ("closed",)

# key 도메인 분리 — 축이 다르면 절대 같은 hash가 나오지 않게 한다.
SOURCE_KEY_DOMAIN = "oppb-cache-source/v1"
SOURCE_LINE_DOMAIN = "oppb-source-line/v1"
DEPENDENCY_KEY_DOMAIN = "oppb-cache-dependency/v1"
BUILD_KEY_DOMAIN = "oppb-cache-build/v1"
NODE_ID_DOMAIN = "oppb-cache-node/v1"

GIB = 1 << 30

# 제안서 §4.5 기본값 — allocator별 soft cap 10 GiB, 최소 여유 max(5 GiB, filesystem 10%),
# closed node warm retention 7일. `cache set-policy`로 더 작게 제한하거나 확대한다.
DEFAULT_POLICY = {
    "soft_cap_bytes": 10 * GIB,
    "min_free_bytes": None,  # None이면 max(5 GiB, filesystem 10%)로 해석한다
    "min_free_floor_bytes": 5 * GIB,
    "min_free_filesystem_ratio": 0.10,
    "warm_retention_days": 7,
    # pin되지 않은 node를 모두 비워도 최소 여유를 못 채울 때, warm cache를 끈 격리
    # 실행이라도 하려면 최소한 이만큼은 있어야 한다. 이보다 적으면 구조화 blocked다.
    "isolated_run_reserve_bytes": 256 * (1 << 20),
}

# 의존성 환경 key의 lockfile 축 — 존재하는 것만 hash에 들어간다.
LOCKFILE_NAMES = (
    "Cargo.lock",
    "Gemfile.lock",
    "go.sum",
    "lockfile.lock",
    "package-lock.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "requirements.txt",
    "uv.lock",
    "yarn.lock",
)

# build cache key의 config 축 — 존재하는 것만 hash에 들어간다.
CONFIG_NAMES = (
    "build.config",
    "pyproject.toml",
    "tsconfig.json",
    "vite.config.js",
    "vite.config.ts",
)

ENVIRONMENT_PROFILE = (".opal", "oppb-environment.json")

SUBCOMMANDS = (
    "conformance",
    "plan-execution",
    "overlay-fork",
    "seal",
    "record-publication",
    "list-nodes",
    "head-set",
    "reseed",
    "lookup",
    "set-policy",
    "put-node",
    "gc",
)

ERROR_CODES = {
    "cache_root_missing": "--cache-root는 필수입니다 — cwd로 추론하지 않습니다.",
    "cache_root_not_absolute": "--cache-root는 절대경로여야 합니다.",
    "cache_root_not_found": "--cache-root 경로가 존재하지 않습니다.",
    "unknown_cache_subcommand": "알 수 없는 cache 하위 명령입니다.",
    "adapter_missing": "--adapter는 필수입니다.",
    "adapter_not_found": "--adapter 경로가 존재하지 않습니다.",
    "adapter_not_executable": "--adapter를 실행할 수 없습니다.",
    "adapter_failed": "cache adapter 실행이 실패했습니다.",
    "adapter_timeout": "cache adapter가 제한 시간 안에 끝나지 않았습니다.",
    "adapter_output_invalid": "cache adapter 출력이 계약을 만족하지 않습니다.",
    "source_root_missing": "--source-root는 필수입니다.",
    "source_root_not_found": "--source-root 경로가 존재하지 않습니다.",
    "candidate_missing": "--candidate는 필수입니다.",
    "candidate_not_found": "해당 candidate overlay가 없습니다.",
    "parent_missing": "--parent는 필수입니다.",
    "commit_not_found": "git 저장소에서 해당 commit을 찾을 수 없습니다.",
    "git_command_failed": "git 명령이 실패했습니다.",
    "command_missing": "--command는 필수입니다.",
    "node_missing": "--node는 필수입니다.",
    "node_not_found": "해당 cache node가 없습니다.",
    "node_state_invalid": "허용되지 않은 cache node 상태입니다.",
    "last_access_invalid": "--last-access가 ISO-8601 UTC 시각이 아닙니다.",
    "size_bytes_invalid": "--size-bytes가 음이 아닌 정수가 아닙니다.",
    "policy_missing": "--policy는 필수입니다.",
    "policy_not_found": "--policy 경로가 존재하지 않습니다.",
    "policy_invalid": "--policy 내용이 cache 정책 계약을 만족하지 않습니다.",
    "verification_invalid": "--verification은 pass 또는 fail이어야 합니다.",
    "new_head_missing": "--new-head는 필수입니다.",
    "seed_not_available": "재사용 가능한 cache DAG seed가 없습니다.",
    "cache_corrupt": "cache root 파일을 읽을 수 없습니다.",
    "disk_budget_exceeded": (
        "pin되지 않은 node를 모두 회수해도 최소 여유 공간을 확보하지 못했습니다."
    ),
}


class CacheError(Exception):
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


def _parse_time(raw, code="last_access_invalid"):
    if not isinstance(raw, str) or not raw:
        raise CacheError(code, "받은 값: %r" % raw)
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        moment = datetime.datetime.fromisoformat(text)
    except ValueError as exc:
        raise CacheError(code, "받은 값: %r (%s)" % (raw, exc)) from exc
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=datetime.timezone.utc)
    return moment.astimezone(datetime.timezone.utc)


def _sha256(*parts):
    digest = hashlib.sha256()
    for part in parts:
        digest.update(b"\x00")
        digest.update(part if isinstance(part, bytes) else str(part).encode("utf-8"))
    return digest.hexdigest()


def _canonical(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


# ─────────────────────────────────────────────────────────────────────────────
# 원자 쓰기·락 — 형태만 `oppl-runtime-tool/ledger.py:336-377` 복제
# ─────────────────────────────────────────────────────────────────────────────


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


@contextlib.contextmanager
def _locked(cache_root):
    """cache root 단위 배타 락 — 다중 프로세스의 read-modify-write를 직렬화한다."""
    path = pathlib.Path(cache_root) / LOCK_FILENAME
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


def _read_json(path, default=None):
    path = pathlib.Path(path)
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CacheError("cache_corrupt", "%s: %s" % (path, exc)) from exc


def _replace_tree(source, target):
    """target을 source의 복사본으로 교체한다.

    copy-on-write를 지원하지 않는 플랫폼도 동일 manifest를 보존하도록 hardlink를
    쓰지 않고 파일을 복사한다. 어느 경우에도 두 candidate가 하나의 mutable build
    cache를 공유하지 않는다.
    """
    target = pathlib.Path(target)
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(str(source), str(target), symlinks=True)
    return target


def _dir_size(path):
    total = 0
    for root, _dirs, files in os.walk(str(path)):
        for name in files:
            with contextlib.suppress(OSError):
                total += os.lstat(os.path.join(root, name)).st_size
    return total


# ─────────────────────────────────────────────────────────────────────────────
# git — 리스트 인자(shell=False)
# ─────────────────────────────────────────────────────────────────────────────


def _git(args, cwd, binary=False):
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=not binary,
    )


def _git_text(args, cwd):
    result = _git(args, cwd)
    if result.returncode != 0:
        raise CacheError(
            "git_command_failed",
            "git %s: %s" % (" ".join(args), (result.stderr or result.stdout).strip()),
        )
    return result.stdout.strip()


def _resolve_commit(source_root, rev):
    result = _git(["rev-parse", "--verify", "%s^{commit}" % rev], cwd=source_root)
    if result.returncode != 0:
        raise CacheError("commit_not_found", "%s in %s" % (rev, source_root))
    return result.stdout.strip()


def _tree_of(source_root, commit):
    return _git_text(["rev-parse", "%s^{tree}" % commit], cwd=source_root)


def _source_line_id(source_root):
    """경로가 아니라 저장소 identity로 source base 계보를 식별한다(lineage 축)."""
    result = _git(["rev-list", "--max-parents=0", "HEAD"], cwd=source_root)
    if result.returncode == 0 and result.stdout.strip():
        root_commit = result.stdout.strip().splitlines()[-1].strip()
        return _sha256(SOURCE_LINE_DOMAIN, root_commit)
    return _sha256(SOURCE_LINE_DOMAIN, os.path.realpath(str(source_root)))


def _ls_tree(source_root, tree):
    """(mode, blob_sha, relpath) 목록 — materialize 검증의 기준 manifest."""
    raw = _git_text(["ls-tree", "-r", "-z", tree], cwd=source_root)
    entries = []
    for record in raw.split("\0"):
        if not record:
            continue
        meta, relpath = record.split("\t", 1)
        mode, kind, sha = meta.split()
        if kind != "blob":
            continue
        entries.append((mode, sha, relpath))
    return sorted(entries, key=lambda item: item[2])


def _diff_tree(source_root, old_tree, new_tree):
    """parent→accepted 변경·삭제·mode 목록. 전체 archive를 반복하지 않기 위한 입력이다."""
    raw = _git_text(["diff-tree", "-r", "-z", "--no-commit-id", old_tree, new_tree], cwd=source_root)
    fields = [field for field in raw.split("\0") if field]
    changes = []
    index = 0
    while index + 1 < len(fields):
        meta = fields[index]
        relpath = fields[index + 1]
        index += 2
        if not meta.startswith(":"):
            continue
        parts = meta[1:].split()
        if len(parts) < 5:
            continue
        old_mode, new_mode, _old_sha, new_sha, status = parts[:5]
        changes.append(
            {
                "status": status[:1],
                "path": relpath,
                "old_mode": old_mode,
                "new_mode": new_mode,
                "blob": new_sha,
            }
        )
    return sorted(changes, key=lambda item: item["path"])


def _git_blob_sha(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()  # noqa: S324


def _object_format_is_sha1(source_root):
    result = _git(["rev-parse", "--show-object-format"], cwd=source_root)
    return result.returncode != 0 or result.stdout.strip() in ("", "sha1")


# ─────────────────────────────────────────────────────────────────────────────
# source base — generation 전진과 복구
# ─────────────────────────────────────────────────────────────────────────────


def _source_base_dir(cache_root, line_id):
    return pathlib.Path(cache_root) / SOURCE_BASE_DIRNAME / line_id


def _extract_archive(source_root, commit, target):
    """`git archive`로 전체 snapshot을 만든다 — 최초 generation과 복구 경로."""
    result = _git(["archive", "--format=tar", commit], cwd=source_root, binary=True)
    if result.returncode != 0:
        raise CacheError("git_command_failed", "git archive %s 실패" % commit)
    target = pathlib.Path(target)
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r|") as archive:
        archive.extractall(str(target))  # noqa: S202 — git archive 산출물만 다룬다
    return target


def _apply_delta(source_root, target, changes):
    """변경·삭제·mode만 직전 generation에 증분 반영한다."""
    target = pathlib.Path(target)
    for change in changes:
        path = target / change["path"]
        if change["status"] == "D":
            with contextlib.suppress(OSError):
                path.unlink()
            continue
        blob = _git(["cat-file", "blob", change["blob"]], cwd=source_root, binary=True)
        if blob.returncode != 0:
            raise CacheError("git_command_failed", "cat-file %s 실패" % change["blob"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob.stdout)
        with contextlib.suppress(OSError):
            path.chmod(0o755 if change["new_mode"].endswith("755") else 0o644)


def _materialized_matches(source_root, target, tree):
    """결과 manifest의 Git tree entries가 candidate tree와 같은지 확인한다."""
    if not _object_format_is_sha1(source_root):
        return True
    target = pathlib.Path(target)
    expected = {relpath: sha for _mode, sha, relpath in _ls_tree(source_root, tree)}
    actual = {}
    for root, _dirs, files in os.walk(str(target)):
        for name in files:
            full = pathlib.Path(root) / name
            relpath = str(full.relative_to(target))
            try:
                actual[relpath] = _git_blob_sha(full.read_bytes())
            except OSError:
                return False
    return expected == actual


def materialize_source_base(cache_root, source_root, commit):
    """source base를 최신 generation으로 만들고 receipt를 갱신한다.

    직전 generation이 있으면 `diff-tree`의 변경·삭제·mode만 반영해 generation을
    전진시킨다. 반영 결과가 candidate tree와 다르면 그 generation을 폐기하고 전체
    `git archive`로 복구한다.
    """
    line_id = _source_line_id(source_root)
    tree = _tree_of(source_root, commit)
    base_dir = _source_base_dir(cache_root, line_id)
    tree_dir = base_dir / "tree"
    receipt_path = base_dir / GENERATION_MANIFEST
    receipt = _read_json(receipt_path)

    method = "archive"
    generation = 1
    if receipt and tree_dir.is_dir() and receipt.get("tree") == tree:
        method = "reuse"
        generation = int(receipt.get("generation", 1))
    elif receipt and tree_dir.is_dir() and receipt.get("tree"):
        changes = _diff_tree(source_root, receipt["tree"], tree)
        _apply_delta(source_root, tree_dir, changes)
        generation = int(receipt.get("generation", 1)) + 1
        method = "incremental"
        if not _materialized_matches(source_root, tree_dir, tree):
            _extract_archive(source_root, commit, tree_dir)
            generation += 1
            method = "archive_recovered"
    else:
        _extract_archive(source_root, commit, tree_dir)

    entries = _ls_tree(source_root, tree)
    manifest_hash = _sha256(
        SOURCE_KEY_DOMAIN,
        _canonical([{"mode": mode, "blob": sha, "path": rel} for mode, sha, rel in entries]),
    )
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "line_id": line_id,
        "tree": tree,
        "commit": commit,
        "generation": generation,
        "method": method,
        "source_key": _sha256(SOURCE_KEY_DOMAIN, tree),
        "manifest_hash": manifest_hash,
        "updated_at": _now(),
    }
    _atomic_write_json(receipt_path, receipt)
    receipt["tree_path"] = str(tree_dir)
    receipt["inputs"] = [rel for _mode, _sha, rel in entries]
    return receipt


# ─────────────────────────────────────────────────────────────────────────────
# 3계층 key
# ─────────────────────────────────────────────────────────────────────────────


def _hash_named_files(root, names):
    root = pathlib.Path(root)
    found = {}
    for name in names:
        path = root / name
        if path.is_file():
            found[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def _toolchain_contract(source_root):
    """봉인된 실행 profile의 toolchain·bootstrap 계약. 없으면 빈 계약이다."""
    path = pathlib.Path(source_root).joinpath(*ENVIRONMENT_PROFILE)
    profile = _read_json(path, default={}) or {}
    return {
        "toolchain": profile.get("toolchain", {}),
        "bootstrap": profile.get("bootstrap_command", profile.get("bootstrap", [])),
    }


def dependency_key(source_root):
    """lockfile + toolchain + bootstrap command hash — 환경 계약이 바뀔 때만 움직인다."""
    contract = _toolchain_contract(source_root)
    return _sha256(
        DEPENDENCY_KEY_DOMAIN,
        _canonical(
            {
                "lockfiles": _hash_named_files(source_root, LOCKFILE_NAMES),
                "toolchain": contract["toolchain"],
                "bootstrap": contract["bootstrap"],
            }
        ),
    )


def build_key(adapter_hash, config_hashes, dependency, source_manifest_hash, lineage_id):
    """build tool/version + config + dependency key + source input manifest + lineage."""
    return _sha256(
        BUILD_KEY_DOMAIN,
        _canonical(
            {
                "adapter": adapter_hash,
                "config": config_hashes,
                "dependency": dependency,
                "source_manifest": source_manifest_hash,
                "lineage": lineage_id,
            }
        ),
    )


def compute_keys(cache_root, source_root, commit, adapter):
    """3계층 key와 materialize된 source base를 함께 돌려준다."""
    base = materialize_source_base(cache_root, source_root, commit)
    adapter_hash = conformance.adapter_identity(adapter)
    config_hashes = _hash_named_files(base["tree_path"], CONFIG_NAMES)
    dependency = dependency_key(source_root)
    return {
        "source_base": base,
        "source_key": base["source_key"],
        "source_manifest_hash": base["manifest_hash"],
        "source_generation": base["generation"],
        "dependency_key": dependency,
        "adapter_hash": adapter_hash,
        "config_hashes": config_hashes,
        "lineage_id": base["line_id"],
        "build_key": build_key(
            adapter_hash, config_hashes, dependency, base["manifest_hash"], base["line_id"]
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# node 저장소
# ─────────────────────────────────────────────────────────────────────────────


def _nodes_dir(cache_root):
    return pathlib.Path(cache_root) / NODES_DIRNAME


def load_nodes(cache_root):
    nodes = []
    root = _nodes_dir(cache_root)
    if not root.is_dir():
        return nodes
    for entry in sorted(root.iterdir()):
        manifest = _read_json(entry / NODE_MANIFEST)
        if manifest:
            nodes.append(manifest)
    return nodes


def _write_node(cache_root, manifest, payload_source=None, payload_bytes=None):
    node_dir = _nodes_dir(cache_root) / manifest["node_id"]
    payload_dir = node_dir / NODE_PAYLOAD
    if payload_source is not None:
        _replace_tree(payload_source, payload_dir)
    else:
        if payload_dir.exists():
            shutil.rmtree(payload_dir)
        payload_dir.mkdir(parents=True, exist_ok=True)
        if payload_bytes:
            (payload_dir / "object.bin").write_bytes(b"\0" * int(payload_bytes))
    manifest["size_bytes"] = _dir_size(payload_dir)
    _atomic_write_json(node_dir / NODE_MANIFEST, manifest)
    return manifest


def _find_node(cache_root, node_id):
    manifest = _read_json(_nodes_dir(cache_root) / node_id / NODE_MANIFEST)
    if manifest is None:
        raise CacheError("node_not_found", "받은 값: %s" % node_id)
    return manifest


def _nodes_for_candidate(cache_root, candidate):
    return [node for node in load_nodes(cache_root) if node.get("candidate") == candidate]


def _touch(cache_root, node):
    """last-access receipt 갱신 — LRU 회수 순서의 유일한 근거다."""
    node["last_access"] = _now()
    _atomic_write_json(_nodes_dir(cache_root) / node["node_id"] / NODE_MANIFEST, node)
    return node


# ─────────────────────────────────────────────────────────────────────────────
# 정책과 용량 관리
# ─────────────────────────────────────────────────────────────────────────────


def read_policy(cache_root):
    policy = dict(DEFAULT_POLICY)
    stored = _read_json(pathlib.Path(cache_root) / POLICY_FILENAME)
    if isinstance(stored, dict):
        policy.update(stored)
    return policy


def _effective_min_free(cache_root, policy):
    if policy.get("min_free_bytes") is not None:
        return int(policy["min_free_bytes"])
    usage = shutil.disk_usage(str(cache_root))
    ratio = float(policy.get("min_free_filesystem_ratio", 0.10))
    return max(int(policy.get("min_free_floor_bytes", 5 * GIB)), int(usage.total * ratio))


def _free_bytes(cache_root):
    return shutil.disk_usage(str(cache_root)).free


def _evictable(nodes, policy, now):
    """closed node만, warm retention 경과 뒤에, last-access LRU 순서로."""
    retention = datetime.timedelta(days=float(policy.get("warm_retention_days", 7)))
    ready = []
    for node in nodes:
        if node.get("state") in PINNED_STATES:
            continue
        if node.get("state") != "closed":
            continue
        last_access = _parse_time(node.get("last_access") or "1970-01-01T00:00:00Z")
        if now - last_access < retention:
            continue
        ready.append((last_access, node["node_id"], node))
    ready.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in ready]


def collect_garbage(cache_root, policy, enforce):
    """pin되지 않고 retention이 지난 closed node만 LRU로 회수한다.

    evidence·DONE·source code는 대상이 아니다 — cache root의 node payload만 만진다.
    `enforce`가 참이면 공간을 못 채웠을 때 cacheless 강등 또는 구조화 blocked까지 간다.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    nodes = load_nodes(cache_root)
    total = sum(int(node.get("size_bytes", 0)) for node in nodes)
    soft_cap = int(policy.get("soft_cap_bytes", DEFAULT_POLICY["soft_cap_bytes"]))
    min_free = _effective_min_free(cache_root, policy)

    evicted = []
    for node in _evictable(nodes, policy, now):
        if total <= soft_cap and _free_bytes(cache_root) >= min_free:
            break
        shutil.rmtree(_nodes_dir(cache_root) / node["node_id"], ignore_errors=True)
        total -= int(node.get("size_bytes", 0))
        evicted.append(node["node_id"])

    free = _free_bytes(cache_root)
    result = {
        "evicted": evicted,
        "total_bytes": total,
        "free_bytes": free,
        "soft_cap_bytes": soft_cap,
        "min_free_bytes": min_free,
        "pinned": [node["node_id"] for node in load_nodes(cache_root) if node.get("state") in PINNED_STATES],
    }
    if free >= min_free:
        _set_cacheless(cache_root, False)
        result["degraded"] = None
        return result
    if not enforce:
        result["degraded"] = None
        return result

    reserve = int(policy.get("isolated_run_reserve_bytes", DEFAULT_POLICY["isolated_run_reserve_bytes"]))
    if free >= reserve:
        _set_cacheless(cache_root, True)
        result["degraded"] = "cacheless"
        return result
    raise CacheError(
        "disk_budget_exceeded",
        "free=%s, min_free=%s, reserve=%s" % (free, min_free, reserve),
        blocked=True,
        evicted=evicted,
        free_bytes=free,
        min_free_bytes=min_free,
    )


def _set_cacheless(cache_root, value):
    path = pathlib.Path(cache_root) / STATE_FILENAME
    state = _read_json(path, default={}) or {}
    if bool(state.get("degraded_cacheless")) == bool(value):
        return state
    state["degraded_cacheless"] = bool(value)
    state["updated_at"] = _now()
    return _atomic_write_json(path, state)


def _is_cacheless(cache_root):
    state = _read_json(pathlib.Path(cache_root) / STATE_FILENAME, default={}) or {}
    return bool(state.get("degraded_cacheless"))


def _auto_gc(cache_root):
    """새 cache object를 쓰기 전 자동 회수. 절대 실패로 번지지 않는다."""
    with contextlib.suppress(CacheError, OSError):
        collect_garbage(cache_root, read_policy(cache_root), enforce=False)


# ─────────────────────────────────────────────────────────────────────────────
# overlay와 CAS node
# ─────────────────────────────────────────────────────────────────────────────


def _overlay_dir(cache_root, candidate):
    return pathlib.Path(cache_root) / OVERLAYS_DIRNAME / candidate


def _candidate_manifest(cache_root, candidate):
    manifest = _read_json(_overlay_dir(cache_root, candidate) / CANDIDATE_MANIFEST)
    if manifest is None:
        raise CacheError("candidate_not_found", "받은 값: %s" % candidate)
    return manifest


def _run_build(adapter, source, overlay, inputs):
    try:
        return conformance.run_adapter(adapter, source, overlay, inputs)
    except conformance.ConformanceError as exc:
        raise CacheError(exc.code, exc.message, exc.exit_code, **exc.extra) from exc


def _classification(cache_root, adapter):
    try:
        return conformance.classification_of(cache_root, adapter)
    except conformance.ConformanceError as exc:
        raise CacheError(exc.code, exc.message, exc.exit_code, **exc.extra) from exc


# ─────────────────────────────────────────────────────────────────────────────
# 인자
# ─────────────────────────────────────────────────────────────────────────────


def _require_cache_root(opts):
    raw = opts.get("cache_root")
    if not raw:
        raise CacheError("cache_root_missing")
    if not os.path.isabs(raw):
        raise CacheError("cache_root_not_absolute", "받은 값: %s" % raw)
    path = pathlib.Path(raw)
    if not path.is_dir():
        raise CacheError("cache_root_not_found", "받은 값: %s" % raw)
    return path


def _require_adapter(opts):
    raw = opts.get("adapter")
    if not raw:
        raise CacheError("adapter_missing")
    path = pathlib.Path(raw)
    if not path.is_file():
        raise CacheError("adapter_not_found", "받은 값: %s" % raw)
    return path


def _require_source_root(opts):
    raw = opts.get("source_root")
    if not raw:
        raise CacheError("source_root_missing")
    path = pathlib.Path(raw)
    if not path.is_dir():
        raise CacheError("source_root_not_found", "받은 값: %s" % raw)
    return path


def _require(opts, key, code):
    value = opts.get(key)
    if not value:
        raise CacheError(code)
    return value


# ─────────────────────────────────────────────────────────────────────────────
# 하위 명령
# ─────────────────────────────────────────────────────────────────────────────


def cmd_conformance(opts):
    """adapter conformance suite 실행과 분류 receipt 발행."""
    cache_root = _require_cache_root(opts)
    adapter = _require_adapter(opts)
    try:
        receipt = conformance.run_conformance(cache_root, adapter)
    except conformance.ConformanceError as exc:
        raise CacheError(exc.code, exc.message, exc.exit_code, **exc.extra) from exc
    return {
        "adapter": str(adapter),
        "classification": receipt["classification"],
        "cases": receipt["cases"],
        "evidence_path": str(conformance.receipt_path(cache_root, receipt["adapter_hash"])),
    }


def cmd_plan_execution(opts):
    """명령 단위 실행 계획. `non_reusable` 강등은 해당 명령만 cold로 내린다."""
    cache_root = _require_cache_root(opts)
    adapter = _require_adapter(opts)
    command = _require(opts, "command", "command_missing")
    classification, _receipt = _classification(cache_root, adapter)

    if classification == "non_reusable":
        execution, reason = "cold", "non_reusable"
    elif _is_cacheless(cache_root):
        execution, reason = "cold", "cacheless_degraded"
    else:
        execution, reason = "warm_eligible", "conformant_adapter"

    plan = {
        "schema_version": SCHEMA_VERSION,
        "command": command,
        "adapter_hash": conformance.adapter_identity(adapter),
        "classification": classification,
        "execution": execution,
        "reason": reason,
        "planned_at": _now(),
    }
    _atomic_write_json(
        pathlib.Path(cache_root) / PLANS_DIRNAME / ("%s.json" % _sha256(command)[:32]), plan
    )
    return {
        "target_command": command,
        "execution": execution,
        "reason": reason,
        "classification": classification,
    }


def cmd_overlay_fork(opts):
    """parent에서 candidate-private overlay를 fork한다 — mutable 작업은 여기서만."""
    cache_root = _require_cache_root(opts)
    adapter = _require_adapter(opts)
    source_root = _require_source_root(opts)
    candidate = _require(opts, "candidate", "candidate_missing")
    parent = _require(opts, "parent", "parent_missing")

    with _locked(cache_root):
        _auto_gc(cache_root)
        commit = _resolve_commit(source_root, parent)
        keys = compute_keys(cache_root, source_root, commit, adapter)

        overlay_root = _overlay_dir(cache_root, candidate)
        candidate_source = overlay_root / "source"
        overlay = overlay_root / "overlay"
        # candidate마다 source 복사본과 overlay를 따로 둔다 — 여러 candidate가 하나의
        # mutable build cache를 동시에 쓰지 않는다.
        _replace_tree(keys["source_base"]["tree_path"], candidate_source)
        if overlay.exists():
            shutil.rmtree(overlay)
        overlay.mkdir(parents=True, exist_ok=True)

        inputs = keys["source_base"]["inputs"]
        build = _run_build(adapter, candidate_source, overlay, inputs)

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "candidate": candidate,
            "parent_commit": commit,
            "source_key": keys["source_key"],
            "source_manifest_hash": keys["source_manifest_hash"],
            "source_generation": keys["source_generation"],
            "dependency_key": keys["dependency_key"],
            "build_key": keys["build_key"],
            "adapter_hash": keys["adapter_hash"],
            "lineage_id": keys["lineage_id"],
            "inputs": inputs,
            "output_manifest": build.get("output_manifest"),
            "overlay_path": str(overlay),
            "source_path": str(candidate_source),
            "source_root": str(source_root),
            "forked_at": _now(),
        }
        _atomic_write_json(overlay_root / CANDIDATE_MANIFEST, manifest)

    return {
        "candidate": candidate,
        "overlay_path": str(overlay),
        "parent_commit": commit,
        "source_key": keys["source_key"],
        "dependency_key": keys["dependency_key"],
        "build_key": keys["build_key"],
        "source_generation": keys["source_generation"],
    }


def cmd_seal(opts):
    """검증 통과한 overlay를 immutable CAS node로 봉인한다.

    같은 parent의 병렬 candidate여도 각각 별도 node로 남는다 — 승자 하나만 남기지
    않는다. node identity에는 candidate·parent·3계층 key·검증 receipt가 모두 들어간다.
    """
    cache_root = _require_cache_root(opts)
    candidate = _require(opts, "candidate", "candidate_missing")
    verification = opts.get("verification", "pass")
    if verification not in ("pass", "fail"):
        raise CacheError("verification_invalid", "받은 값: %s" % verification)

    with _locked(cache_root):
        manifest = _candidate_manifest(cache_root, candidate)
        if verification != "pass":
            # 검증 실패 overlay는 봉인하지 않고 폐기한다.
            shutil.rmtree(_overlay_dir(cache_root, candidate) / "overlay", ignore_errors=True)
            return {"candidate": candidate, "sealed": False, "verification": verification}

        _auto_gc(cache_root)
        node_id = _sha256(
            NODE_ID_DOMAIN,
            _canonical(
                {
                    "candidate": candidate,
                    "parent_commit": manifest["parent_commit"],
                    "source_key": manifest["source_key"],
                    "source_manifest_hash": manifest["source_manifest_hash"],
                    "dependency_key": manifest["dependency_key"],
                    "build_key": manifest["build_key"],
                    "output_manifest": manifest.get("output_manifest"),
                    "verification": verification,
                }
            ),
        )
        node = {
            "schema_version": SCHEMA_VERSION,
            "node_id": node_id,
            # 봉인 직후는 publication 대기다 — pin되어 GC 대상이 아니다.
            "state": "publication_pending",
            "candidate": candidate,
            "parent_commit": manifest["parent_commit"],
            "source_key": manifest["source_key"],
            "source_manifest_hash": manifest["source_manifest_hash"],
            "source_generation": manifest["source_generation"],
            "dependency_key": manifest["dependency_key"],
            "build_key": manifest["build_key"],
            "adapter_hash": manifest["adapter_hash"],
            "lineage_id": manifest["lineage_id"],
            "inputs": manifest.get("inputs", []),
            "output_manifest": manifest.get("output_manifest"),
            "verification": verification,
            "source_root": manifest.get("source_root"),
            "last_access": _now(),
            "sealed_at": _now(),
        }
        _write_node(cache_root, node, payload_source=manifest["overlay_path"])

    return {
        "candidate": candidate,
        "sealed": True,
        "node_id": node_id,
        "state": node["state"],
        "verification": verification,
    }


def cmd_record_publication(opts):
    """publication 기록. stale sibling overlay는 폐기하지 않고 seed 후보로 남긴다."""
    cache_root = _require_cache_root(opts)
    candidate = _require(opts, "candidate", "candidate_missing")

    with _locked(cache_root):
        nodes = _nodes_for_candidate(cache_root, candidate)
        if not nodes:
            raise CacheError("node_not_found", "candidate=%s" % candidate)
        node = sorted(nodes, key=lambda item: item.get("sealed_at", ""))[-1]
        node["state"] = "active_run"
        node["published_at"] = _now()
        node["last_access"] = node["published_at"]
        _atomic_write_json(_nodes_dir(cache_root) / node["node_id"] / NODE_MANIFEST, node)

        path = pathlib.Path(cache_root) / PUBLICATIONS_FILENAME
        document = _read_json(path, default={"schema_version": SCHEMA_VERSION, "entries": []})
        document["entries"].append(
            {
                "candidate": candidate,
                "node_id": node["node_id"],
                "parent_commit": node["parent_commit"],
                "published_at": node["published_at"],
            }
        )
        _atomic_write_json(path, document)

        siblings = [
            item["node_id"]
            for item in load_nodes(cache_root)
            if item.get("verification") == "pass" and item["node_id"] != node["node_id"]
        ]

    return {
        "candidate": candidate,
        "node_id": node["node_id"],
        "retained_siblings": sorted(siblings),
    }


def cmd_list_nodes(opts):
    cache_root = _require_cache_root(opts)
    nodes = [
        {
            "node_id": node["node_id"],
            "state": node.get("state"),
            "candidate": node.get("candidate"),
            "last_access": node.get("last_access"),
            "size_bytes": node.get("size_bytes"),
            "source_key": node.get("source_key"),
            "dependency_key": node.get("dependency_key"),
            "build_key": node.get("build_key"),
            "verification": node.get("verification"),
        }
        for node in load_nodes(cache_root)
    ]
    return {"nodes": nodes, "count": len(nodes)}


def cmd_head_set(opts):
    """accepted head가 기록하는 재사용 가능한 cache DAG head set.

    단일 build-cache 파일을 소유하지 않는다 — 검증 통과한 모든 CAS node가 head set에
    남아 stale sibling replay의 seed 후보가 된다.
    """
    cache_root = _require_cache_root(opts)
    heads = sorted(
        node["node_id"] for node in load_nodes(cache_root) if node.get("verification") == "pass"
    )
    published = _read_json(
        pathlib.Path(cache_root) / PUBLICATIONS_FILENAME, default={"entries": []}
    )
    return {
        "head_set": heads,
        "count": len(heads),
        "published": [entry["node_id"] for entry in published.get("entries", [])],
    }


def _select_seed(cache_root, source_root, candidate, new_head_commit, new_manifest_paths):
    """input 일치가 가장 크고 적용할 Git delta가 가장 작은 seed를 결정론적으로 고른다.

    동점이면 node_id 사전순으로 끊는다 — 같은 입력이면 항상 같은 seed가 나온다.
    """
    scored = []
    for node in load_nodes(cache_root):
        if node.get("verification") != "pass":
            continue
        if node.get("lineage_id") is None:
            continue
        match = len(set(node.get("inputs", [])) & new_manifest_paths)
        try:
            delta = len(
                _diff_tree(
                    source_root,
                    _tree_of(source_root, node["parent_commit"]),
                    _tree_of(source_root, new_head_commit),
                )
            )
        except CacheError:
            continue
        scored.append(((-match, delta, node["node_id"]), node))
    if not scored:
        raise CacheError("seed_not_available", "candidate=%s" % candidate)
    scored.sort(key=lambda item: item[0])
    return scored[0][1]


def cmd_reseed(opts):
    """stale sibling을 새 head에 다시 올린다 — seed의 overlay에 delta를 replay한다.

    cache 파일끼리 byte merge하지 않는다. seed overlay를 candidate-private 복사본으로
    가져온 뒤 intervening accepted source delta를 source에 반영하고 build tool의 정상
    incremental 검사를 다시 실행한다. adapter가 `non_reusable`이면 cold로 내려간다.
    """
    cache_root = _require_cache_root(opts)
    adapter = _require_adapter(opts)
    source_root = _require_source_root(opts)
    candidate = _require(opts, "candidate", "candidate_missing")
    new_head = _require(opts, "new_head", "new_head_missing")

    with _locked(cache_root):
        manifest = _candidate_manifest(cache_root, candidate)
        new_head_commit = _resolve_commit(source_root, new_head)
        keys = compute_keys(cache_root, source_root, new_head_commit, adapter)
        new_paths = set(keys["source_base"]["inputs"])

        classification, _receipt = _classification(cache_root, adapter)
        overlay_root = _overlay_dir(cache_root, candidate)
        candidate_source = overlay_root / "source"
        overlay = overlay_root / "overlay"

        if classification == "non_reusable":
            # 재사용을 증명하지 못한 adapter는 이 명령만 cold로 실행한다.
            _replace_tree(keys["source_base"]["tree_path"], candidate_source)
            if overlay.exists():
                shutil.rmtree(overlay)
            overlay.mkdir(parents=True, exist_ok=True)
            build = _run_build(adapter, candidate_source, overlay, sorted(new_paths))
            replayed = []
            seed = None
            cold_fallback = True
        else:
            seed = _select_seed(cache_root, source_root, candidate, new_head_commit, new_paths)
            seed_payload = _nodes_dir(cache_root) / seed["node_id"] / NODE_PAYLOAD
            # seed의 candidate-private overlay 복사본에서 시작한다(공유 금지).
            _replace_tree(seed_payload, overlay)
            _replace_tree(
                _source_base_dir(cache_root, seed["lineage_id"]) / "tree", candidate_source
            )
            replayed = _diff_tree(
                source_root,
                _tree_of(source_root, seed["parent_commit"]),
                _tree_of(source_root, new_head_commit),
            )
            _apply_delta(source_root, candidate_source, replayed)
            build = _run_build(adapter, candidate_source, overlay, sorted(new_paths))
            cold_fallback = False
            _touch(cache_root, seed)

        manifest.update(
            {
                "parent_commit": new_head_commit,
                "source_key": keys["source_key"],
                "source_manifest_hash": keys["source_manifest_hash"],
                "source_generation": keys["source_generation"],
                "dependency_key": keys["dependency_key"],
                "build_key": keys["build_key"],
                "adapter_hash": keys["adapter_hash"],
                "lineage_id": keys["lineage_id"],
                "inputs": sorted(new_paths),
                "output_manifest": build.get("output_manifest"),
                "seed_node": seed["node_id"] if seed else None,
                "reseeded_at": _now(),
            }
        )
        _atomic_write_json(overlay_root / CANDIDATE_MANIFEST, manifest)

    return {
        "candidate": candidate,
        "seed_node": seed["node_id"] if seed else None,
        "cold_fallback": cold_fallback,
        "byte_merged": False,
        "replayed_delta": [
            {"status": change["status"], "path": change["path"]} for change in replayed
        ],
        "classification": classification,
        "overlay_path": str(overlay),
        "build_key": keys["build_key"],
    }


def cmd_lookup(opts):
    """무실행 exact hit는 source·dependency·build manifest hash가 모두 일치할 때만."""
    cache_root = _require_cache_root(opts)
    adapter = _require_adapter(opts)
    source_root = _require_source_root(opts)
    head = opts.get("new_head") or "HEAD"

    with _locked(cache_root):
        commit = _resolve_commit(source_root, head)
        keys = compute_keys(cache_root, source_root, commit, adapter)
        exact = None
        seeds = []
        for node in load_nodes(cache_root):
            if node.get("verification") != "pass":
                continue
            if (
                node.get("source_manifest_hash") == keys["source_manifest_hash"]
                and node.get("dependency_key") == keys["dependency_key"]
                and node.get("build_key") == keys["build_key"]
            ):
                exact = node
                break
            if node.get("adapter_hash") == keys["adapter_hash"]:
                seeds.append(node["node_id"])
        if exact is not None:
            _touch(cache_root, exact)

    if exact is not None:
        return {
            "hit": "exact",
            "node_id": exact["node_id"],
            "source_key": keys["source_key"],
            "dependency_key": keys["dependency_key"],
            "build_key": keys["build_key"],
        }
    return {
        "hit": "replay" if seeds else "miss",
        "node_id": None,
        "seed_candidates": sorted(seeds),
        "source_key": keys["source_key"],
        "dependency_key": keys["dependency_key"],
        "build_key": keys["build_key"],
    }


def cmd_set_policy(opts):
    """cache 정책 주입 — 설정 층을 새로 만들지 않고 명시 인자 파일로만 받는다."""
    cache_root = _require_cache_root(opts)
    raw = _require(opts, "policy", "policy_missing")
    path = pathlib.Path(raw)
    if not path.is_file():
        raise CacheError("policy_not_found", "받은 값: %s" % raw)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CacheError("policy_invalid", "%s: %s" % (path, exc)) from exc
    if not isinstance(document, dict):
        raise CacheError("policy_invalid", "최상위가 object가 아닙니다: %s" % path)
    allowed = set(DEFAULT_POLICY)
    unknown = sorted(set(document) - allowed)
    if unknown:
        raise CacheError("policy_invalid", "알 수 없는 키: %s" % ", ".join(unknown))

    with _locked(cache_root):
        _atomic_write_json(pathlib.Path(cache_root) / POLICY_FILENAME, document)
        policy = read_policy(cache_root)
    return {
        "policy": document,
        "effective": {
            "soft_cap_bytes": policy["soft_cap_bytes"],
            "min_free_bytes": _effective_min_free(cache_root, policy),
            "warm_retention_days": policy["warm_retention_days"],
        },
    }


def cmd_put_node(opts):
    """cache node를 명시 상태·last-access·크기로 기록한다(운영·복구 경로).

    자동 GC를 걸지 않는다 — node 등록 자체가 회수 판단을 바꾸지 않게 한다.
    """
    cache_root = _require_cache_root(opts)
    name = _require(opts, "node", "node_missing")
    state = opts.get("state", "closed")
    if state not in NODE_STATES:
        raise CacheError("node_state_invalid", "받은 값: %s (허용: %s)" % (state, ", ".join(NODE_STATES)))
    last_access = opts.get("last_access") or _now()
    _parse_time(last_access)
    raw_size = opts.get("size_bytes", "0")
    try:
        size_bytes = int(raw_size)
    except (TypeError, ValueError) as exc:
        raise CacheError("size_bytes_invalid", "받은 값: %r" % raw_size) from exc
    if size_bytes < 0:
        raise CacheError("size_bytes_invalid", "받은 값: %r" % raw_size)

    with _locked(cache_root):
        node = {
            "schema_version": SCHEMA_VERSION,
            "node_id": _sha256(NODE_ID_DOMAIN, "put-node", name),
            "name": name,
            "state": state,
            "last_access": last_access,
            "created_at": _now(),
        }
        _write_node(cache_root, node, payload_bytes=size_bytes)
    return {"node_id": node["node_id"], "name": name, "state": state, "size_bytes": node["size_bytes"]}


def cmd_gc(opts):
    """명시 GC. pin된 node는 어떤 경로에서도 삭제하지 않는다."""
    cache_root = _require_cache_root(opts)
    with _locked(cache_root):
        result = collect_garbage(cache_root, read_policy(cache_root), enforce=True)
    return result


SUBCOMMAND_DISPATCH = {
    "conformance": cmd_conformance,
    "plan-execution": cmd_plan_execution,
    "overlay-fork": cmd_overlay_fork,
    "seal": cmd_seal,
    "record-publication": cmd_record_publication,
    "list-nodes": cmd_list_nodes,
    "head-set": cmd_head_set,
    "reseed": cmd_reseed,
    "lookup": cmd_lookup,
    "set-policy": cmd_set_policy,
    "put-node": cmd_put_node,
    "gc": cmd_gc,
}


def cache_command(opts):
    """`run.sh cache <subcommand>` 진입점 — 본체와 cache root 파일 계약을 소유한다."""
    subcommand = opts.get("subcommand")
    handler = SUBCOMMAND_DISPATCH.get(subcommand)
    if handler is None:
        raise CacheError(
            "unknown_cache_subcommand",
            "지원 하위 명령: %s" % ", ".join(SUBCOMMANDS),
            EXIT_USAGE,
        )
    return handler(opts)
