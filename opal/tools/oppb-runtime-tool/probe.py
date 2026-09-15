"""
@header {
  "module": "probe",
  "task": "132",
  "layer": "util",
  "domain": "oppb-runtime",
  "description": "OPPB Environment Probe Tool — 격리된 probe snapshot에서 bootstrap·build·test·검증 명령을 하나씩 단독 실행해 Git 미추적·ignored 생성·수정·삭제 경로, build cache·dependency 위치, port·DB·service 등 실행 자원, 환경변수로 재지정 가능한 출력과 고정 위치 출력을 관측한다. 관측 결과에 `shared_immutable`·`attempt_namespaced`·`exclusive` 정책과 adapter를 배정하고 `.opal/oppb-environment.json`에 command/config/lockfile/toolchain/bootstrap 입력 hash와 함께 원자 봉인한다(형태만 `oppl-runtime-tool/ledger.py:336-377` 복제 — 해당 도구를 import하지 않는다). 신선도 판정 입력은 repository tree 전체가 아니라 실행 command 정의·build/test config·lockfile·toolchain identity·bootstrap 정의 5종뿐이라 일반 source ACCEPT만으로 profile이 stale이 되지 않는다(제안서 §P2.2). Late environment discovery는 task contract revision당 첫 batch 하나만 run-local `environment-deltas/<fingerprint>.json`으로 무과금 회수하고, 같은 revision의 두 번째 미봉인 쓰기·probe 불일치·lease 교차·project 밖·민감 경로·정책 분류 불가는 `scope_violation`으로 승격해 그때부터 attempt·rework 예산을 차감한다. 이 profile은 Controller maintenance lane이 소유하며 capability Runner의 write lease로 주지 않는다. scope hash는 `controller.compute_scope_hash`·`controller.normalize_lease`를 호출하고 재구현하지 않는다. 표준 라이브러리와 git CLI만 사용하고 플랫폼 분기를 두지 않는다.",
  "exports": [
    "ERROR_CODES", "ProbeError", "EPHEMERAL_POLICIES",
    "PROFILE_RELPATH", "DELTA_DIRNAME", "DISCOVERY_FILENAME",
    "profile_path", "delta_dir", "discovery_path",
    "read_profile", "classify_path", "compute_input_hash",
    "cmd_seal", "cmd_status", "cmd_observe_write", "probe_command"
  ],
  "depends": [
    "git CLI 2.x",
    "opal/tools/oppb-runtime-tool/controller.py",
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
import shutil
import subprocess
import tarfile
import tempfile
import uuid

import controller

SCHEMA_VERSION = "1.0"

EXIT_ERROR = 1
EXIT_USAGE = 2

# `.opal/oppb-environment.json`은 Controller maintenance lane 소유다. Runner write lease로
# 주지 않는다(제안서 §P2.2). 이 상수를 lease 발급 경로에서 사용하지 않는다.
PROFILE_RELPATH = ".opal/oppb-environment.json"
PROFILE_OWNER = "controller_maintenance_lane"

DELTA_DIRNAME = "environment-deltas"
DISCOVERY_FILENAME = "environment-discovery.json"
DISCOVERY_LOCK_FILENAME = "environment-discovery.lock"
SNAPSHOT_DIRNAME = "probe-snapshots"

SUBCOMMANDS = ("seal", "status", "observe-write")

# 제안서 §P2.1 "Git 미추적·ignore 산출물 계약"의 3정책. 이 집합 밖 값을 만들지 않는다.
EPHEMERAL_POLICIES = ("shared_immutable", "attempt_namespaced", "exclusive")

# 신선도 판정 입력 5종 — repository tree 전체가 아니다(제안서 §P2.2).
INPUT_HASH_KEYS = ("commands", "config", "lockfile", "toolchain", "bootstrap")

COMMAND_TIMEOUT_SECONDS = 180

# 전역 git config에 의존하지 않도록 probe snapshot 조작에 항상 주입한다.
GIT_ISOLATION_ARGS = (
    "-c", "user.email=oppb-probe@opal.local",
    "-c", "user.name=OPPB Probe",
    "-c", "commit.gpgsign=false",
    "-c", "init.defaultBranch=main",
)

# dependency environment·download cache — P3 시작 전 1회 준비 후 Runner 쓰기 금지.
DEPENDENCY_ROOTS = (
    "node_modules", ".venv", "venv", "vendor", ".bundle", ".m2", ".gradle",
    ".cargo", ".pnpm-store", ".yarn", "site-packages", "dep-cache", ".deps",
)

# 도구가 출력 위치를 환경변수로 재지정할 수 있는 경로 → attempt별 경로로 namespacing한다.
REDIRECTABLE_ROOTS = {
    "__pycache__": ("PYTHONPYCACHEPREFIX", "python-bytecode"),
    ".pytest_cache": ("PYTEST_CACHE_DIR", "pytest-cache"),
    ".mypy_cache": ("MYPY_CACHE_DIR", "mypy-cache"),
    ".ruff_cache": ("RUFF_CACHE_DIR", "ruff-cache"),
    "target": ("CARGO_TARGET_DIR", "cargo-target"),
    ".next": ("NEXT_DIST_DIR", "next-dist"),
    ".turbo": ("TURBO_CACHE_DIR", "turbo-cache"),
    "coverage": ("COVERAGE_FILE", "coverage"),
    ".nyc_output": ("NYC_OUTPUT_DIR", "nyc-output"),
    ".cache": ("XDG_CACHE_HOME", "xdg-cache"),
    "tmp": ("TMPDIR", "tmpdir"),
}

# 자동 확장 대상이 아닌 민감 경로 — 첫 관측에서 바로 `scope_violation`이다(제안서 §P2.2).
SENSITIVE_ROOTS = (".git", ".opal", ".ssh", ".gnupg", ".aws", ".config")
SENSITIVE_NAMES = (".env", ".netrc", "credentials.json", "id_rsa", ".npmrc", ".pypirc")
SENSITIVE_SUFFIXES = (".pem", ".key", ".p12", ".keystore")

# 실행 자원 관측 대상 환경변수 — port·DB·service·queue·browser profile(제안서 §P2.2).
RUNTIME_RESOURCE_ENV_KEYS = (
    "PORT", "HTTP_PORT", "DATABASE_URL", "DB_URL", "POSTGRES_URL", "MYSQL_URL",
    "REDIS_URL", "AMQP_URL", "KAFKA_BROKERS", "BROWSER_PROFILE_DIR",
    "PLAYWRIGHT_BROWSERS_PATH", "SELENIUM_REMOTE_URL",
)

ERROR_CODES = {
    "probe_subcommand_unknown": "알 수 없는 probe 하위 명령입니다.",
    "commands_missing": "--commands는 필수입니다.",
    "commands_not_absolute": "--commands는 절대경로여야 합니다.",
    "commands_not_found": "--commands 경로가 존재하지 않습니다.",
    "commands_not_json": "--commands 파일이 유효한 JSON이 아닙니다.",
    "commands_invalid": "--commands 내용이 probe 명령 정의 계약을 만족하지 않습니다.",
    "observation_missing": "--observation은 필수입니다.",
    "observation_not_absolute": "--observation은 절대경로여야 합니다.",
    "observation_not_found": "--observation 경로가 존재하지 않습니다.",
    "observation_not_json": "--observation 파일이 유효한 JSON이 아닙니다.",
    "observation_invalid": "--observation 내용이 관측 계약을 만족하지 않습니다.",
    "probe_project_root_missing": "--project-root는 필수입니다.",
    "probe_project_root_invalid": "--project-root가 존재하는 절대경로가 아닙니다.",
    "probe_run_root_missing": "--run-root는 필수입니다.",
    "probe_run_root_invalid": "--run-root가 존재하는 절대경로가 아닙니다.",
    "project_root_not_a_git_repository": "--project-root가 git 저장소가 아닙니다.",
    "profile_missing": "`.opal/oppb-environment.json`이 아직 봉인되지 않았습니다.",
    "profile_corrupt": "`.opal/oppb-environment.json`을 읽을 수 없습니다.",
    "profile_untracked_guarantee_failed": (
        "`.opal/oppb-environment.json`의 미추적 보장을 확인하지 못했습니다."
    ),
    "probe_snapshot_failed": "격리된 probe snapshot 생성에 실패했습니다.",
    "probe_command_failed": "probe 단독 실행 명령이 실패했습니다.",
    "scope_violation": "봉인되지 않은 쓰기가 자동 확장 조건을 만족하지 못했습니다.",
}


class ProbeError(Exception):
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


def _canonical(payload):
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# 원자 쓰기와 락
#   ledger.py:336-377 패턴을 형태만 복제한다 — lock → 대상 디렉토리 mkstemp →
#   fsync → os.replace. oppl-runtime-tool은 import하지 않는다(TOOL-BOUNDARY §7-3).
# ─────────────────────────────────────────────────────────────────────────────


def _atomic_write_json(path, payload):
    """대상 디렉토리에 임시 파일을 만들고 fsync 후 교체한다(부분 쓰기 노출 0).

    임시 파일은 실패 경로에서도 반드시 제거한다 — `.opal/`에 partial 잔여물을
    남기지 않는 것이 봉인 원자성의 관측 가능한 조건이다.
    """
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".oppb-probe-", suffix=".tmp")
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
def _discovery_locked(run_root):
    """discovery epoch 장부 전용 배타 락 — Controller 트랜잭션과 축이 다르다."""
    path = pathlib.Path(run_root) / DISCOVERY_LOCK_FILENAME
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
# 경로
# ─────────────────────────────────────────────────────────────────────────────


def profile_path(project_root):
    return pathlib.Path(project_root) / PROFILE_RELPATH


def delta_dir(run_root):
    return pathlib.Path(run_root) / DELTA_DIRNAME


def discovery_path(run_root):
    return pathlib.Path(run_root) / DISCOVERY_FILENAME


def snapshot_root(run_root):
    return pathlib.Path(run_root) / SNAPSHOT_DIRNAME


# ─────────────────────────────────────────────────────────────────────────────
# git 호출 — 리스트 인자(shell=False)
# ─────────────────────────────────────────────────────────────────────────────


def _git(args, cwd):
    return subprocess.run(
        ["git", *GIT_ISOLATION_ARGS, *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def _require_git_repository(project_root):
    result = _git(["rev-parse", "--git-dir"], project_root)
    if result.returncode != 0:
        raise ProbeError(
            "project_root_not_a_git_repository",
            (result.stderr or result.stdout).strip(),
        )


def _ensure_profile_untracked(project_root):
    """profile을 project worktree의 추적 diff에 노출하지 않는다.

    profile은 Controller maintenance lane 소유이고 반영은 Checkpoint Tool이
    publication lock 안에서 수행한다. probe 자신이 Runner worktree를 dirty로
    만들면 Runner Git 상태 변경 0 계약(AC-6)을 probe가 먼저 깨뜨린다.
    이미 추적 중인 저장소에서는 exclude가 무효이므로 그 사실만 보고한다.
    """
    tracked = _git(["ls-files", "--error-unmatch", "--", PROFILE_RELPATH], project_root)
    if tracked.returncode == 0:
        return {"tracked": True, "exclude_entry_added": False}

    common = _git(["rev-parse", "--git-common-dir"], project_root)
    if common.returncode != 0:
        raise ProbeError(
            "profile_untracked_guarantee_failed",
            (common.stderr or common.stdout).strip(),
        )
    git_dir = pathlib.Path(common.stdout.strip())
    if not git_dir.is_absolute():
        git_dir = pathlib.Path(project_root) / git_dir
    exclude_file = git_dir / "info" / "exclude"

    entry = "/%s" % PROFILE_RELPATH
    added = False
    try:
        existing = exclude_file.read_text(encoding="utf-8") if exclude_file.is_file() else ""
        if entry not in {line.strip() for line in existing.splitlines()}:
            exclude_file.parent.mkdir(parents=True, exist_ok=True)
            prefix = "" if (existing == "" or existing.endswith("\n")) else "\n"
            with open(exclude_file, "a", encoding="utf-8") as handle:
                handle.write(prefix + entry + "\n")
            added = True
    except OSError as exc:
        raise ProbeError(
            "profile_untracked_guarantee_failed", "%s: %s" % (exclude_file, exc)
        ) from exc

    # 등록 문자열이 아니라 git의 실제 ignore 판정을 확인한다.
    check = _git(["check-ignore", "-q", "--", PROFILE_RELPATH], project_root)
    if check.returncode != 0:
        raise ProbeError(
            "profile_untracked_guarantee_failed",
            "check-ignore가 %s를 ignore로 판정하지 않았습니다." % PROFILE_RELPATH,
        )
    return {"tracked": False, "exclude_entry_added": added, "exclude_path": str(exclude_file)}


# ─────────────────────────────────────────────────────────────────────────────
# 격리된 probe snapshot
# ─────────────────────────────────────────────────────────────────────────────


def _make_snapshot(project_root, dest):
    """accepted head의 ref 미변경 snapshot을 만든다.

    `git archive HEAD`로 추적 tree만 복사하므로 프로젝트 worktree의 미추적·ignored
    상태가 섞이지 않는다. snapshot 자체를 독립 저장소로 초기화해 명령 실행 전후를
    git의 실제 ignore 판정으로 비교한다.
    """
    dest = pathlib.Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest.parent / ("%s.tar" % dest.name)
    result = _git(["archive", "--format=tar", "-o", str(archive), "HEAD"], project_root)
    if result.returncode != 0:
        raise ProbeError(
            "probe_snapshot_failed", (result.stderr or result.stdout).strip()
        )
    try:
        with tarfile.open(str(archive)) as handle:
            handle.extractall(str(dest), filter="data")
    except (OSError, tarfile.TarError) as exc:
        raise ProbeError("probe_snapshot_failed", "%s: %s" % (archive, exc)) from exc
    finally:
        with contextlib.suppress(OSError):
            archive.unlink()

    for args in (
        ["init", "-q", "-b", "main"],
        ["add", "-A"],
        ["commit", "-q", "-m", "probe snapshot baseline", "--allow-empty"],
    ):
        result = _git(args, dest)
        if result.returncode != 0:
            raise ProbeError(
                "probe_snapshot_failed",
                "git %s: %s" % (args[0], (result.stderr or result.stdout).strip()),
            )
    return dest


def _status_changes(snapshot):
    """snapshot의 미추적·ignored 생성과 추적 경로 수정·삭제를 git 판정으로 읽는다."""
    result = _git(
        [
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--ignored=matching",
        ],
        snapshot,
    )
    if result.returncode != 0:
        raise ProbeError(
            "probe_snapshot_failed", (result.stderr or result.stdout).strip()
        )
    tokens = [token for token in result.stdout.split("\0") if token]
    ephemeral = []
    tracked = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if len(token) < 4:
            continue
        code, path = token[:2], token[3:]
        if code[0] in ("R", "C"):
            index += 1  # rename/copy는 원본 경로 토큰이 하나 더 붙는다
        if code in ("??", "!!"):
            ephemeral.append({"path": path, "change": "created"})
        elif code.strip():
            change = "deleted" if "D" in code else "modified"
            tracked.append({"path": path, "change": change})
    return ephemeral, tracked


def _run_command(command, snapshot):
    """명령 하나를 snapshot에서 단독 실행한다(다른 명령과 섞지 않는다)."""
    argv = command["argv"]
    env = dict(os.environ)
    env["OPPB_PROBE"] = "1"
    started = datetime.datetime.now(datetime.timezone.utc)
    try:
        result = subprocess.run(
            argv,
            cwd=str(snapshot),
            capture_output=True,
            text=True,
            env=env,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ProbeError(
            "probe_command_failed", "%s: %s" % (command.get("id"), exc)
        ) from exc
    elapsed = (datetime.datetime.now(datetime.timezone.utc) - started).total_seconds()
    return result, env, round(elapsed * 1000)


def _observe_command(project_root, run_root, command, token):
    """명령 하나의 격리 단독 실행 관측 — snapshot은 관측 후 회수한다."""
    snapshot = snapshot_root(run_root) / token / str(command["id"])
    try:
        _make_snapshot(project_root, snapshot)
        result, env, elapsed_ms = _run_command(command, snapshot)
        if result.returncode != 0:
            raise ProbeError(
                "probe_command_failed",
                "%s exit=%d stderr=%s"
                % (command["id"], result.returncode, (result.stderr or "").strip()[:400]),
            )
        ephemeral, tracked = _status_changes(snapshot)
    finally:
        shutil.rmtree(str(snapshot), ignore_errors=True)
    return {
        "command_id": command["id"],
        "kind": command.get("kind", "build"),
        "exit_code": 0,
        "duration_ms": elapsed_ms,
        "ephemeral": ephemeral,
        "tracked": tracked,
        "runtime_resources": _runtime_resources(command, env),
    }


def _runtime_resources(command, env):
    """port·DB·service·queue·browser profile 등 실행 자원 관측.

    명령이 선언한 자원과, 실제 실행 환경에서 그 명령에 전달된 자원 지시 환경변수를
    합쳐 기록한다. 선언과 환경 어디에도 자원이 없으면 빈 목록이 정상이다.
    """
    observed = []
    for value in command.get("runtime_resources", []) or []:
        if isinstance(value, str) and value:
            observed.append({"resource": value, "source": "declared"})
    for key in RUNTIME_RESOURCE_ENV_KEYS:
        value = env.get(key)
        if value:
            observed.append({"resource": "%s=%s" % (key, value), "source": "environment"})
    return observed


# ─────────────────────────────────────────────────────────────────────────────
# 경로 안전성과 정책 분류
# ─────────────────────────────────────────────────────────────────────────────


def _relative_inside(project_root, raw):
    """project root 안의 상대 경로로 정규화한다. 밖이면 None."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    candidate = pathlib.Path(raw)
    if not candidate.is_absolute():
        candidate = pathlib.Path(project_root) / candidate
    try:
        resolved = candidate.resolve()
        base = pathlib.Path(project_root).resolve()
    except OSError:
        return None
    try:
        relative = resolved.relative_to(base)
    except ValueError:
        return None
    text = relative.as_posix()
    return text if text and text != "." else None


def _is_sensitive(relpath):
    segments = relpath.split("/")
    if segments[0] in SENSITIVE_ROOTS:
        return True
    name = segments[-1]
    return name in SENSITIVE_NAMES or name.endswith(SENSITIVE_SUFFIXES)


def classify_path(relpath, kind="build"):
    """관측 경로에 3정책 중 하나와 adapter를 결정론적으로 배정한다.

    - bootstrap 명령의 산출물과 dependency environment는 `shared_immutable` —
      P3 전에 한 번 준비하고 그 뒤 Runner 쓰기를 금지한다.
    - 출력 위치를 환경변수로 재지정할 수 있는 경로는 `attempt_namespaced` —
      run root의 attempt별 경로로 돌린다.
    - 위치를 바꿀 수단이 없는 고정 위치 출력은 `exclusive` — 배타 lease를 잡고
      병렬 실행을 금지한다.

    분류할 수 없으면 None을 돌려준다(호출자가 `scope_violation`으로 승격한다).
    """
    if not relpath or _is_sensitive(relpath):
        return None
    root = relpath.split("/")[0]
    if kind == "bootstrap" or root in DEPENDENCY_ROOTS:
        return {
            "policy": "shared_immutable",
            "adapter": "dependency-environment",
            "redirect_env": None,
        }
    if root in REDIRECTABLE_ROOTS:
        env_key, adapter = REDIRECTABLE_ROOTS[root]
        return {
            "policy": "attempt_namespaced",
            "adapter": adapter,
            "redirect_env": env_key,
        }
    return {
        "policy": "exclusive",
        "adapter": "fixed-location-output",
        "redirect_env": None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 한정 입력 hash — repository tree 전체가 아니다 (제안서 §P2.2)
# ─────────────────────────────────────────────────────────────────────────────


def _digest_files(project_root, relpaths):
    """선언된 파일 내용만 hash한다. 부재 파일도 결정론적으로 표현한다."""
    digest = hashlib.sha256()
    for relpath in sorted(set(relpaths or [])):
        digest.update(relpath.encode("utf-8"))
        digest.update(b"\0")
        path = pathlib.Path(project_root) / relpath
        if path.is_file():
            try:
                digest.update(path.read_bytes())
            except OSError:
                digest.update(b"<unreadable>")
        else:
            digest.update(b"<absent>")
        digest.update(b"\0")
    return digest.hexdigest()


def _command_identity(commands):
    return [
        {
            "id": command["id"],
            "kind": command.get("kind", "build"),
            "argv": list(command["argv"]),
        }
        for command in sorted(commands, key=lambda item: item["id"])
    ]


def compute_input_hash(project_root, inputs):
    """신선도 판정 입력 hash 5종.

    실행 command 정의·build/test config·lockfile·toolchain identity·bootstrap 정의만
    포함한다. repository tree 전체를 넣으면 일반 source ACCEPT마다 profile이 stale이
    되어 병렬 dispatch가 매번 닫힌다(제안서 §P2.2).
    """
    commands = inputs.get("commands", [])
    bootstrap = [
        command for command in commands if command.get("kind", "build") == "bootstrap"
    ]
    return {
        "commands": _sha256_text(_canonical(_command_identity(commands))),
        "bootstrap": _sha256_text(_canonical(_command_identity(bootstrap))),
        "config": _digest_files(project_root, inputs.get("config", [])),
        "lockfile": _digest_files(project_root, inputs.get("lockfile", [])),
        "toolchain": _sha256_text(_canonical(inputs.get("toolchain", {}) or {})),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 입력 검증
# ─────────────────────────────────────────────────────────────────────────────


def _require_dir(opts, key, missing_code, invalid_code):
    raw = opts.get(key)
    if not raw:
        raise ProbeError(missing_code, exit_code=EXIT_USAGE)
    if not os.path.isabs(raw):
        raise ProbeError(invalid_code, "받은 값: %s" % raw, EXIT_USAGE)
    path = pathlib.Path(raw)
    if not path.is_dir():
        raise ProbeError(invalid_code, "받은 값: %s" % raw)
    return path


def _load_json_argument(opts, key, codes):
    missing, not_absolute, not_found, not_json = codes
    raw = opts.get(key)
    if not raw:
        raise ProbeError(missing, exit_code=EXIT_USAGE)
    if not os.path.isabs(raw):
        raise ProbeError(not_absolute, "받은 값: %s" % raw, EXIT_USAGE)
    path = pathlib.Path(raw)
    if not path.is_file():
        raise ProbeError(not_found, "받은 값: %s" % raw)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProbeError(not_json, "%s: %s" % (path, exc)) from exc


def _validate_commands(raw):
    if not isinstance(raw, dict):
        raise ProbeError("commands_invalid", "최상위는 object여야 합니다.")
    commands = raw.get("commands")
    if not isinstance(commands, list) or not commands:
        raise ProbeError("commands_invalid", "commands는 비어 있지 않은 배열이어야 합니다.")
    normalized = []
    for index, entry in enumerate(commands):
        if not isinstance(entry, dict):
            raise ProbeError("commands_invalid", "commands[%d]는 object여야 합니다." % index)
        command_id = entry.get("id")
        argv = entry.get("argv")
        if not isinstance(command_id, str) or not command_id.strip():
            raise ProbeError("commands_invalid", "commands[%d].id가 없습니다." % index)
        if (
            not isinstance(argv, list)
            or not argv
            or not all(isinstance(token, str) for token in argv)
        ):
            raise ProbeError(
                "commands_invalid", "commands[%d].argv는 문자열 배열이어야 합니다." % index
            )
        normalized.append(
            {
                "id": command_id,
                "kind": entry.get("kind", "build"),
                "argv": list(argv),
                "runtime_resources": list(entry.get("runtime_resources", []) or []),
            }
        )
    def _string_list(key):
        values = raw.get(key, []) or []
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            raise ProbeError("commands_invalid", "%s는 문자열 배열이어야 합니다." % key)
        return list(values)

    toolchain = raw.get("toolchain", {}) or {}
    if not isinstance(toolchain, dict):
        raise ProbeError("commands_invalid", "toolchain은 object여야 합니다.")
    return {
        "commands": normalized,
        "config": _string_list("config"),
        "lockfile": _string_list("lockfile"),
        "toolchain": toolchain,
    }


def _validate_observation(raw):
    if not isinstance(raw, dict):
        raise ProbeError("observation_invalid", "최상위는 object여야 합니다.")
    task_id = raw.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        raise ProbeError("observation_invalid", "task_id가 없습니다.")
    revision = raw.get("contract_revision")
    if not isinstance(revision, int) or isinstance(revision, bool):
        raise ProbeError("observation_invalid", "contract_revision은 정수여야 합니다.")
    command = raw.get("command")
    if not isinstance(command, dict) or not isinstance(command.get("id"), str):
        raise ProbeError("observation_invalid", "command.id가 없습니다.")
    argv = command.get("argv")
    if (
        not isinstance(argv, list)
        or not argv
        or not all(isinstance(token, str) for token in argv)
    ):
        raise ProbeError("observation_invalid", "command.argv는 문자열 배열이어야 합니다.")
    paths = raw.get("observed_paths")
    if not isinstance(paths, list) or not paths or not all(isinstance(p, str) for p in paths):
        raise ProbeError("observation_invalid", "observed_paths는 문자열 배열이어야 합니다.")
    return {
        "task_id": task_id,
        "attempt_id": raw.get("attempt_id") or "unknown",
        "contract_revision": revision,
        "command": {
            "id": command["id"],
            "kind": command.get("kind", "build"),
            "argv": list(argv),
            "runtime_resources": list(command.get("runtime_resources", []) or []),
        },
        "observed_paths": list(paths),
    }


# ─────────────────────────────────────────────────────────────────────────────
# profile 읽기
# ─────────────────────────────────────────────────────────────────────────────


def read_profile(project_root, required=True):
    path = profile_path(project_root)
    if not path.is_file():
        if required:
            raise ProbeError("profile_missing", "받은 값: %s" % path)
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProbeError("profile_corrupt", "%s: %s" % (path, exc)) from exc


def _sealed_paths(profile):
    return {entry["path"] for entry in profile.get("ephemeral_write_set", []) if entry.get("path")}


def _covered(relpath, sealed):
    for sealed_path in sealed:
        if relpath == sealed_path or relpath.startswith(sealed_path.rstrip("/") + "/"):
            return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# lease 교차 판정
#   lease store는 Scope Lease Tool(W-12) 소유다. probe는 읽기만 하고 그 모듈이
#   아직 없으면 run root의 공개 파일 계약(`{"leases": [...]}`)으로 폴백한다.
# ─────────────────────────────────────────────────────────────────────────────


def _lease_documents(run_root):
    run_root = pathlib.Path(run_root)
    candidates = list(run_root.glob("*lease*.json"))
    candidates.extend(sorted((run_root / "leases").glob("*.json")))
    documents = []
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and isinstance(data.get("leases"), list):
            documents.extend(data["leases"])
        elif isinstance(data, list):
            documents.extend(item for item in data if isinstance(item, dict))
        elif isinstance(data, dict) and data.get("task_id"):
            documents.append(data)
    return documents


# 쓰기 소유권 경로를 담는 축 이름. Scope Lease Tool은 record 최상위·`lease`(정규형)·
# `ownership`(공개형) 어디에든 이 축을 둘 수 있으므로 세 위치를 모두 훑는다.
LEASE_PATH_KEYS = (
    "ephemeral_write_set", "ephemeral_writes", "ephemeral_write",
    "tracked_write_set", "tracked_writes", "tracked_write",
)


def _lease_paths(lease):
    paths = []
    scopes = [lease]
    for nested in ("lease", "ownership"):
        value = lease.get(nested)
        if isinstance(value, dict):
            scopes.append(value)
    for scope in scopes:
        for key in LEASE_PATH_KEYS:
            for entry in scope.get(key, []) or []:
                if isinstance(entry, str):
                    paths.append(entry)
                elif isinstance(entry, dict) and isinstance(entry.get("path"), str):
                    paths.append(entry["path"])
    return paths


def _crossing_lease(run_root, task_id, relpaths):
    """다른 미니 태스크가 보유한 lease 경로와 교차하는지 본다.

    교차는 첫 관측이라도 자동 확장 조건("기존 lease와 교차하지 않으며")을 만족하지
    못하므로 late discovery 대상이 아니다(제안서 §P2.2).
    """
    for lease in _lease_documents(run_root):
        if not isinstance(lease, dict):
            continue
        if lease.get("state") not in (None, "active"):
            continue
        if lease.get("task_id") == task_id:
            continue
        held = _lease_paths(lease)
        for relpath in relpaths:
            for owned in held:
                normalized = owned.strip("/")
                if not normalized:
                    continue
                if relpath == normalized or relpath.startswith(normalized + "/"):
                    return {
                        "task_id": lease.get("task_id"),
                        "path": normalized,
                        "observed_path": relpath,
                    }
    return None


# ─────────────────────────────────────────────────────────────────────────────
# discovery epoch 장부 — contract revision당 1 batch
# ─────────────────────────────────────────────────────────────────────────────


def _read_discovery(run_root):
    path = discovery_path(run_root)
    if not path.is_file():
        return {"schema_version": SCHEMA_VERSION, "epochs": {}, "charges": []}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": SCHEMA_VERSION, "epochs": {}, "charges": []}
    document.setdefault("epochs", {})
    document.setdefault("charges", [])
    return document


def _epoch_key(task_id, revision):
    return "%s|%d" % (task_id, revision)


def _fingerprint(observation, relpaths):
    """task contract revision·새 command hash·관측 경로 집합 하나의 지문."""
    return _sha256_text(
        _canonical(
            {
                "task_id": observation["task_id"],
                "contract_revision": observation["contract_revision"],
                "command": {
                    "id": observation["command"]["id"],
                    "argv": observation["command"]["argv"],
                },
                "paths": sorted(relpaths),
            }
        )
    )


def _charge(run_root, observation, reason, fingerprint=None):
    """승격 시점부터 attempt·rework 예산을 차감한다.

    `workgraph.json`의 role 예산(runner·executor·verifier)과 축이 다른 별도 장부다.
    Controller 문서를 probe가 직접 쓰지 않는다 — workgraph 갱신은 Controller
    트랜잭션 API의 소유다.
    """
    charged = ["task_attempt", "project_rework"]
    with _discovery_locked(run_root):
        document = _read_discovery(run_root)
        document["charges"].append(
            {
                "task_id": observation["task_id"],
                "attempt_id": observation["attempt_id"],
                "contract_revision": observation["contract_revision"],
                "command_id": observation["command"]["id"],
                "reason": reason,
                "fingerprint": fingerprint,
                "charged_budgets": charged,
                "charged_at": _now(),
            }
        )
        _atomic_write_json(discovery_path(run_root), document)
    return charged


def _escalate(run_root, observation, reason, **detail):
    charged = _charge(run_root, observation, reason)
    raise ProbeError(
        "scope_violation",
        "미봉인 쓰기가 자동 확장 조건을 만족하지 못했습니다: %s" % reason,
        reason=reason,
        budget_charged=True,
        charged_budgets=charged,
        task_id=observation["task_id"],
        contract_revision=observation["contract_revision"],
        **detail,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 서브 명령 — `probe seal` / `probe status` / `probe observe-write`
# ─────────────────────────────────────────────────────────────────────────────


def _roots(opts):
    run_root = _require_dir(
        opts, "run_root", "probe_run_root_missing", "probe_run_root_invalid"
    )
    project_root = _require_dir(
        opts, "project_root", "probe_project_root_missing", "probe_project_root_invalid"
    )
    return run_root, project_root


def cmd_seal(opts):
    """명령을 하나씩 단독 실행해 관측하고 profile을 원자 봉인한다."""
    run_root, project_root = _roots(opts)
    _require_git_repository(project_root)
    inputs = _validate_commands(
        _load_json_argument(
            opts,
            "commands",
            ("commands_missing", "commands_not_absolute", "commands_not_found", "commands_not_json"),
        )
    )

    token = uuid.uuid4().hex[:12]
    observations = []
    for command in inputs["commands"]:
        observations.append(_observe_command(project_root, run_root, command, token))
    shutil.rmtree(str(snapshot_root(run_root) / token), ignore_errors=True)

    ephemeral = []
    rejected = []
    tracked = []
    resources = []
    seen = set()
    for observation in observations:
        for entry in observation["ephemeral"]:
            relpath = _relative_inside(project_root, entry["path"])
            if relpath is None:
                rejected.append({**entry, "reason": "outside_project_root"})
                continue
            policy = classify_path(relpath, observation["kind"])
            if policy is None:
                rejected.append({**entry, "path": relpath, "reason": "sensitive_path"})
                continue
            key = (relpath, observation["command_id"])
            if key in seen:
                continue
            seen.add(key)
            ephemeral.append(
                {
                    "path": relpath,
                    "change": entry["change"],
                    "command_id": observation["command_id"],
                    "command_kind": observation["kind"],
                    **policy,
                }
            )
        for entry in observation["tracked"]:
            tracked.append({**entry, "command_id": observation["command_id"]})
        for entry in observation["runtime_resources"]:
            if entry not in resources:
                resources.append({**entry, "command_id": observation["command_id"]})

    ephemeral.sort(key=lambda item: (item["path"], item["command_id"]))
    lease = controller.normalize_lease(
        {"ephemeral_writes": [entry["path"] for entry in ephemeral]}
    )
    profile = {
        "schema_version": SCHEMA_VERSION,
        "owner": PROFILE_OWNER,
        "sealed_at": _now(),
        "run_root": str(run_root),
        "project_root": str(project_root),
        "inputs": inputs,
        "input_hash": compute_input_hash(project_root, inputs),
        "ephemeral_write_set": ephemeral,
        "tracked_write_observations": tracked,
        "runtime_resources": resources,
        "rejected_paths": rejected,
        "scope_hash": controller.compute_scope_hash(lease),
        "probe_runs": [
            {
                "command_id": observation["command_id"],
                "kind": observation["kind"],
                "exit_code": observation["exit_code"],
                "duration_ms": observation["duration_ms"],
            }
            for observation in observations
        ],
    }

    untracked = _ensure_profile_untracked(project_root)
    _atomic_write_json(profile_path(project_root), profile)

    return {
        "subcommand": "seal",
        "project_root": str(project_root),
        "run_root": str(run_root),
        "profile_path": str(profile_path(project_root)),
        "input_hash": profile["input_hash"],
        "ephemeral_write_set": ephemeral,
        "runtime_resources": resources,
        "rejected_paths": rejected,
        "scope_hash": profile["scope_hash"],
        "untracked_guarantee": untracked,
    }


def cmd_status(opts):
    """profile 신선도 관측 — 부작용이 없고 봉인을 갱신하지 않는다."""
    run_root, project_root = _roots(opts)
    profile = read_profile(project_root, required=False)
    if profile is None:
        return {
            "subcommand": "status",
            "project_root": str(project_root),
            "run_root": str(run_root),
            "sealed": False,
            "fresh": False,
            "parallel_dispatch_allowed": False,
            "stale_inputs": list(INPUT_HASH_KEYS),
            "reason": "profile_missing",
        }

    sealed_hash = profile.get("input_hash", {})
    current_hash = compute_input_hash(project_root, profile.get("inputs", {}))
    stale = [key for key in INPUT_HASH_KEYS if sealed_hash.get(key) != current_hash.get(key)]
    fresh = not stale
    return {
        "subcommand": "status",
        "project_root": str(project_root),
        "run_root": str(run_root),
        "sealed": True,
        "fresh": fresh,
        # Controller는 profile이 없거나 한정 입력 hash가 다르면 병렬 dispatch를 거부한다.
        "parallel_dispatch_allowed": fresh,
        "sealed_input_hash": sealed_hash,
        "current_input_hash": current_hash,
        "stale_inputs": stale,
        "freshness_input_scope": list(INPUT_HASH_KEYS),
        "ephemeral_write_set_size": len(profile.get("ephemeral_write_set", [])),
    }


def cmd_observe_write(opts):
    """미봉인 ignored 쓰기 1건을 판정한다 — late discovery 회수 또는 승격."""
    run_root, project_root = _roots(opts)
    _require_git_repository(project_root)
    observation = _validate_observation(
        _load_json_argument(
            opts,
            "observation",
            (
                "observation_missing",
                "observation_not_absolute",
                "observation_not_found",
                "observation_not_json",
            ),
        )
    )
    profile = read_profile(project_root)

    # 1. 경로 안전성 — project/run root 밖과 민감 경로는 자동 확장 대상이 아니다.
    declared = []
    for raw in observation["observed_paths"]:
        relpath = _relative_inside(project_root, raw)
        if relpath is None:
            _escalate(run_root, observation, "outside_project_root", offending_path=raw)
        if _is_sensitive(relpath):
            _escalate(run_root, observation, "sensitive_path", offending_path=relpath)
        declared.append(relpath)

    # 2. 이미 봉인된 경로만이면 discovery가 아니다.
    sealed = _sealed_paths(profile)
    if all(_covered(relpath, sealed) for relpath in declared):
        return {
            "subcommand": "observe-write",
            "action": "already_sealed",
            "budget_charged": False,
            "rerun_requested": False,
            "task_id": observation["task_id"],
            "contract_revision": observation["contract_revision"],
            "paths": declared,
        }

    # 3. lease 교차 — 첫 관측이라도 자동 확장 조건을 만족하지 못한다.
    crossing = _crossing_lease(run_root, observation["task_id"], declared)
    if crossing is not None:
        _escalate(run_root, observation, "lease_crossing", crossing_lease=crossing)

    # 4. contract revision당 첫 batch만 무과금이다.
    key = _epoch_key(observation["task_id"], observation["contract_revision"])
    with _discovery_locked(run_root):
        document = _read_discovery(run_root)
        if key in document["epochs"]:
            consumed = document["epochs"][key]
        else:
            consumed = None
    if consumed is not None:
        _escalate(
            run_root,
            observation,
            "second_discovery_in_revision",
            previous_fingerprint=consumed.get("fingerprint"),
        )

    # 5. 후보 snapshot에서 명령을 단독 delta probe하고 결과를 대조한다.
    probe_result = _observe_command(
        project_root, run_root, observation["command"], "delta-%s" % uuid.uuid4().hex[:8]
    )
    probe_paths = []
    for entry in probe_result["ephemeral"]:
        relpath = _relative_inside(project_root, entry["path"])
        if relpath is None or _is_sensitive(relpath):
            _escalate(
                run_root, observation, "probe_mismatch", offending_path=entry["path"]
            )
        probe_paths.append(relpath)

    batch = sorted(set(declared) | set(probe_paths))
    crossing = _crossing_lease(run_root, observation["task_id"], batch)
    if crossing is not None:
        _escalate(run_root, observation, "lease_crossing", crossing_lease=crossing)

    # 6. 정책을 결정론적으로 배정할 수 없으면 승격한다.
    entries = []
    for relpath in batch:
        policy = classify_path(relpath, observation["command"].get("kind", "build"))
        if policy is None:
            _escalate(
                run_root, observation, "policy_unclassifiable", offending_path=relpath
            )
        entries.append({"path": relpath, "change": "created", **policy})

    # 7. run-local delta를 봉인하고 임시 ephemeral lease를 확장한다.
    fingerprint = _fingerprint(observation, batch)
    lease = controller.normalize_lease({"ephemeral_writes": batch})
    delta = {
        "schema_version": SCHEMA_VERSION,
        "owner": PROFILE_OWNER,
        "sealed_at": _now(),
        "fingerprint": fingerprint,
        "task_id": observation["task_id"],
        "attempt_id": observation["attempt_id"],
        "contract_revision": observation["contract_revision"],
        "command": observation["command"],
        "declared_paths": sorted(declared),
        "probe_paths": sorted(set(probe_paths)),
        "ephemeral_write_set": entries,
        "lease_extension": lease,
        "scope_hash": controller.compute_scope_hash(lease),
        "budget_charged": False,
        "parent_profile_scope_hash": profile.get("scope_hash"),
    }
    delta_file = delta_dir(run_root) / ("%s.json" % fingerprint)
    _atomic_write_json(delta_file, delta)

    with _discovery_locked(run_root):
        document = _read_discovery(run_root)
        document["epochs"][key] = {
            "fingerprint": fingerprint,
            "task_id": observation["task_id"],
            "contract_revision": observation["contract_revision"],
            "consumed_at": _now(),
            "delta_path": str(delta_file),
        }
        _atomic_write_json(discovery_path(run_root), document)

    return {
        "subcommand": "observe-write",
        "action": "delta_probe",
        "budget_charged": False,
        "rerun_requested": True,
        "rerun_task_id": observation["task_id"],
        "lease_extended": batch,
        "lease_extension": lease,
        "scope_hash": delta["scope_hash"],
        "fingerprint": fingerprint,
        "delta_path": str(delta_file),
        "ephemeral_write_set": entries,
        "contract_revision": observation["contract_revision"],
    }


SUBCOMMAND_DISPATCH = {
    "seal": cmd_seal,
    "status": cmd_status,
    "observe-write": cmd_observe_write,
}


def probe_command(opts):
    """`probe <subcommand>` 진입점. 진입점 모듈이 이 함수만 호출한다."""
    subcommand = opts.get("subcommand")
    handler = SUBCOMMAND_DISPATCH.get(subcommand)
    if handler is None:
        raise ProbeError(
            "probe_subcommand_unknown",
            "지원 하위 명령: %s (받은 값: %r)" % (", ".join(SUBCOMMANDS), subcommand),
            EXIT_USAGE,
        )
    return handler(opts)
