"""
@header {
  "module": "oppb_runtime_tool",
  "task": "132",
  "layer": "util",
  "domain": "oppb-runtime",
  "description": "OPPB(프로젝트 빌드 파일럿) 실행 런타임 CLI 진입점. `init`은 신규 run root를 명시 OPPB task root의 `.oppb-run/<run_id>/`에 만들고 공유 cache만 allocator의 `.opal-cache/oppb/`에 둔다. `finalize-run`은 성공 실행의 로그·결과·증거·최종 상태를 canonical 태스크 폴더에 미추적 보존하면서 lock·Supervisor identity·임시 index·검증 sandbox를 제거한다. 기존 allocator `.opal-runs/<run_id>/`는 status/resume 호환으로만 수용한다. 모든 루트는 절대경로 명시 인자로 받고 cwd·경로 세그먼트로 추론하지 않으며, Git ignore 실효 판정을 통과하지 못하면 실행을 거부한다. 출력은 단일 라인 JSON + exit code 계약을 따른다.",
  "exports": [
    "ERROR_CODES", "ok", "err", "parse_argv",
    "cmd_init", "cmd_start", "cmd_finalize_run", "cmd_workgraph", "cmd_evidence", "cmd_task", "cmd_lease",
    "cmd_verifier", "cmd_revalidate",
    "main"
  ],
  "depends": [
    "git CLI 2.x",
    "opal/core/references/harness/tool-output-contract.md",
    "opal/tools/oppb-runtime-tool/evidence.py",
    "opal/tools/oppb-runtime-tool/cache.py",
    "opal/tools/oppb-runtime-tool/verifier_adapter.py",
    "opal/tools/oppb-runtime-tool/revalidation.py"
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
import stat
import subprocess
import sys
import tempfile
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import supervisor  # noqa: E402 — 동일 디렉토리 모듈(supervisor는 이 모듈을 import하지 않는다)
import controller  # noqa: E402 — 동일 디렉토리 모듈, sys.path 보정 뒤 로드
import evidence  # noqa: E402 — 동일 디렉토리 모듈, sys.path 보정 뒤 로드
import cache  # noqa: E402 — 동일 디렉토리 모듈(W-15), sys.path 보정 뒤 로드
import lease  # noqa: E402 — 동일 디렉토리 모듈, sys.path 보정 뒤 로드
import checkpoint  # noqa: E402 — 동일 디렉토리 모듈(W-14), sys.path 보정 뒤 로드
import probe  # noqa: E402 — 동일 디렉토리 모듈, sys.path 보정 뒤 로드
import recovery  # noqa: E402 — 동일 디렉토리 모듈(W-16), sys.path 보정 뒤 로드
import verifier_adapter  # noqa: E402 — 동일 디렉토리 모듈(W-24), sys.path 보정 뒤 로드
import revalidation  # noqa: E402 — 동일 디렉토리 모듈(W-26), sys.path 보정 뒤 로드

# ─────────────────────────────────────────────────────────────────────────────
# 출력 계약 — 단일 라인 JSON + exit code
# ─────────────────────────────────────────────────────────────────────────────

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2

SCHEMA_VERSION = "1.0"

RUN_ROOT_DIRNAME = ".oppb-run"
LEGACY_RUN_ROOT_DIRNAME = ".opal-runs"
CACHE_ROOT_SEGMENTS = (".opal-cache", "oppb")
RUN_CLOSED_NAME = "run.closed.json"

# `.git/info/exclude`에 등록하는 문자열 — run root·cache root 2종 고정
EXCLUDE_ENTRIES = (".oppb-run/", ".opal-cache/oppb/")
LEGACY_RUN_ROOT_ENTRY = ".opal-runs/"

# ignore 판정 확인용 probe 상대경로. 등록 문자열 존재가 아니라 git의 실제 판정을 본다.
CACHE_IGNORE_PROBE = ".opal-cache/oppb/.oppb-ignore-probe"

ERROR_CODES = {
    "usage_error": "명령 인자가 올바르지 않습니다.",
    "unknown_command": "알 수 없는 서브 명령입니다.",
    "allocator_root_missing": "--allocator-root는 필수입니다 — cwd로 추론하지 않습니다.",
    "allocator_root_not_absolute": "--allocator-root는 절대경로여야 합니다.",
    "allocator_root_not_found": "--allocator-root 경로가 존재하지 않습니다.",
    "allocator_root_not_a_git_repository": "--allocator-root가 git 저장소가 아닙니다.",
    "allocator_root_not_repository_root": "--allocator-root가 git 저장소의 최상위가 아닙니다.",
    "project_root_missing": "--project-root는 필수입니다.",
    "project_root_not_absolute": "--project-root는 절대경로여야 합니다.",
    "project_root_not_found": "--project-root 경로가 존재하지 않습니다.",
    "project_root_not_a_git_repository": "--project-root가 git 저장소가 아닙니다.",
    "project_root_not_repository_root": "--project-root가 git 저장소의 최상위가 아닙니다.",
    "task_root_missing": "--task-root는 필수입니다 — project_root에서 추론하지 않습니다.",
    "task_root_not_absolute": "--task-root는 절대경로여야 합니다.",
    "task_root_not_found": "--task-root 경로가 존재하지 않습니다.",
    "task_root_outside_project": "--task-root는 --project-root 하위여야 합니다.",
    "run_root_missing": "--run-root는 필수입니다.",
    "run_root_not_absolute": "--run-root는 절대경로여야 합니다.",
    "run_root_not_found": "--run-root 경로가 존재하지 않습니다.",
    "run_root_invalid": "--run-root가 <task_root>/.oppb-run/<run_id> 또는 legacy <allocator_root>/.opal-runs/<run_id> 형태가 아닙니다.",
    "run_manifest_invalid": "run.json이 없거나 run root 계약과 일치하지 않습니다.",
    "run_closed": "종료 보존된 run은 start/resume할 수 없습니다.",
    "archive_task_path_invalid": "--task-path가 canonical OPPB 태스크 보존 경로가 아닙니다.",
    "archive_destination_exists": "보존 대상 run root가 이미 존재하지만 완료 보존본이 아닙니다.",
    "run_not_finalizable": "성공 완료가 확인되지 않은 run은 보존 종료할 수 없습니다.",
    "archive_symlink_forbidden": "run root 안의 심볼릭 링크는 보존 묶음으로 복사하지 않습니다.",
    "archive_failed": "run 보존 묶음 생성에 실패했습니다.",
    "archive_integrity_failed": "기존 종료 보존본의 내용 hash가 marker와 일치하지 않습니다.",
    "git_command_failed": "git 명령이 실패했습니다.",
    "exclude_registration_failed": "`.git/info/exclude` 등록에 실패했습니다.",
    "ignore_verification_failed": (
        "run root·cache root의 실제 ignore 판정 확인에 실패했습니다 — run 시작을 거부합니다."
    ),
    "run_root_create_failed": "run root 또는 cache root 생성에 실패했습니다.",
    "supervisor_not_implemented": "Supervisor 본체는 아직 구현되지 않았습니다.",
    "internal_error": "처리되지 않은 내부 오류입니다.",
}

# Controller(W-7)·Evidence(W-9) 고유 오류 코드를 폐쇄 집합에 병합한다.
ERROR_CODES.update(controller.ERROR_CODES)
ERROR_CODES.update(supervisor.SUPERVISOR_ERROR_CODES)
ERROR_CODES.update(evidence.ERROR_CODES)
ERROR_CODES.update(cache.ERROR_CODES)
ERROR_CODES.update(lease.ERROR_CODES)
ERROR_CODES.update(probe.ERROR_CODES)
ERROR_CODES.update(checkpoint.ERROR_CODES)
ERROR_CODES.update(recovery.ERROR_CODES)
ERROR_CODES.update(verifier_adapter.ERROR_CODES)
ERROR_CODES.update(revalidation.ERROR_CODES)


class ToolError(Exception):
    """폐쇄 집합 `ERROR_CODES`의 코드 하나로 실패를 표현한다."""

    def __init__(self, code, message="", exit_code=EXIT_ERROR, **extra):
        super().__init__(message or code)
        self.code = code
        self.message = message
        self.exit_code = exit_code
        self.extra = extra


def _emit(payload, exit_code):
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
    sys.stdout.flush()
    return exit_code


def ok(command, **fields):
    return _emit({"ok": True, "command": command, **fields}, EXIT_OK)


def err(command, code, message="", exit_code=EXIT_ERROR, **fields):
    payload = {
        "ok": False,
        "command": command,
        "error": code,
        "message": message or ERROR_CODES.get(code, code),
    }
    payload.update(fields)
    return _emit(payload, exit_code)


# ─────────────────────────────────────────────────────────────────────────────
# 인자 파싱 — flag 화이트리스트, `--k=v`/`--k v` 양식 허용
# ─────────────────────────────────────────────────────────────────────────────

FLAGS = (
    "--allocator-root", "--project-root", "--task-root", "--run-root", "--spec",
    "--file", "--task-id", "--task-path", "--attempt", "--candidate",
    "--commands", "--observation",
    # recover 서브 명령 전용 플래그(W-16) — 본체는 recovery.py가 소유한다.
    "--task", "--pid", "--violation",
    # cache 서브 명령 전용 플래그(W-15) — 본체는 cache.py가 소유한다.
    "--cache-root", "--adapter", "--command", "--parent",
    "--source-root", "--verification", "--new-head", "--policy",
    # checkpoint 서브 명령 전용 플래그(W-14) — 본체는 checkpoint.py가 소유한다.
    "--dest",
    "--node", "--state", "--last-access", "--size-bytes",
    # verifier 서브 명령 전용 플래그(W-24) — 본체는 verifier_adapter.py가 소유한다.
    "--kind", "--trigger", "--signals", "--report", "--output-dir", "--timestamp",
    "--test-mode", "--mode",
    # revalidate 서브 명령 전용 플래그(W-26) — 본체는 revalidation.py가 소유한다.
    "--contract", "--revision",
)

COMMANDS = (
    "init", "start", "status", "resume", "finalize-run", "workgraph", "evidence", "task", "lease",
    "probe",
    "cache",
    "recover",
    "checkpoint",
    "verifier",
    "revalidate",
)


# 값을 받지 않는 플래그 — 존재만으로 True다. 기존 값 플래그 처리와 분리한다.
BOOL_FLAGS = ("--record-baseline", "--regenerate")


def parse_argv(argv):
    command = None
    opts = {}
    index = 0
    while index < len(argv):
        token = argv[index]
        if token.startswith("--"):
            if token in BOOL_FLAGS:
                opts[token[2:].replace("-", "_")] = True
                index += 1
                continue
            if "=" in token:
                name, value = token.split("=", 1)
                index += 1
            else:
                name = token
                if index + 1 >= len(argv):
                    raise ToolError(
                        "usage_error",
                        "%s 옵션에 값이 없습니다." % name,
                        EXIT_USAGE,
                    )
                value = argv[index + 1]
                index += 2
            if name not in FLAGS:
                raise ToolError(
                    "usage_error", "알 수 없는 옵션 %s" % name, EXIT_USAGE
                )
            key = name[2:].replace("-", "_")
            opts[key] = value
            opts.setdefault("_values", {}).setdefault(key, []).append(value)
        else:
            if command is None:
                command = token
            elif "subcommand" not in opts:
                opts["subcommand"] = token
            else:
                raise ToolError(
                    "usage_error", "예상치 못한 인자 %s" % token, EXIT_USAGE
                )
            index += 1
    return command, opts


def require_absolute_dir(opts, key, missing_code, not_absolute_code, not_found_code):
    """경로 인자를 명시 인자로만 받는다 — 미지정·상대경로를 cwd 기준으로 해석하지 않는다."""
    raw = opts.get(key)
    if not raw:
        raise ToolError(missing_code)
    if not os.path.isabs(raw):
        raise ToolError(not_absolute_code, "받은 값: %s" % raw)
    path = pathlib.Path(raw)
    if not path.is_dir():
        raise ToolError(not_found_code, "받은 값: %s" % raw)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# git 호출 — 리스트 인자(shell=False), 공통 수단만 사용한다
# ─────────────────────────────────────────────────────────────────────────────


def _git(args, cwd):
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def repository_toplevel(root, kind="allocator"):
    """명시 root가 git 저장소의 최상위인지 확인하고 그 경로를 돌려준다.

    최상위가 아니면 `.git/info/exclude`의 상대 패턴이 run root·cache root를 가리키지
    못하므로 등록과 ignore 판정 확인이 성립하지 않는다.
    """
    result = _git(["rev-parse", "--show-toplevel"], cwd=root)
    if result.returncode != 0:
        raise ToolError(
            "%s_root_not_a_git_repository" % kind,
            (result.stderr or result.stdout).strip(),
        )
    toplevel = pathlib.Path(result.stdout.strip())
    if os.path.realpath(toplevel) != os.path.realpath(root):
        raise ToolError(
            "%s_root_not_repository_root" % kind,
            "저장소 최상위=%s, 받은 값=%s" % (toplevel, root),
        )
    return toplevel


def exclude_file_path(root):
    """`.git/info/exclude`의 실제 경로. worktree에서도 공용 git dir를 가리킨다."""
    result = _git(["rev-parse", "--git-common-dir"], cwd=root)
    if result.returncode != 0:
        raise ToolError(
            "git_command_failed", (result.stderr or result.stdout).strip()
        )
    common = pathlib.Path(result.stdout.strip())
    if not common.is_absolute():
        common = pathlib.Path(root) / common
    return common / "info" / "exclude"


def register_exclude_entries(root, entries=EXCLUDE_ENTRIES):
    """run root·cache root를 `.git/info/exclude`에 멱등 등록한다.

    이미 있는 줄은 다시 쓰지 않는다 — 재호출로 중복 줄이 늘지 않는다.
    """
    path = exclude_file_path(root)
    try:
        if path.exists():
            existing = path.read_text(encoding="utf-8")
        else:
            existing = ""
        present = {line.strip() for line in existing.splitlines()}
        missing = [entry for entry in entries if entry not in present]
        if not missing:
            return path, []
        path.parent.mkdir(parents=True, exist_ok=True)
        prefix = "" if (existing == "" or existing.endswith("\n")) else "\n"
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(prefix + "".join("%s\n" % entry for entry in missing))
    except OSError as exc:
        raise ToolError(
            "exclude_registration_failed", "%s: %s" % (path, exc)
        ) from exc
    return path, missing


def verify_ignore_decisions(root, probes):
    """등록 문자열이 아니라 git의 실제 ignore 판정을 확인한다.

    `.gitignore`의 부정 패턴이 `.git/info/exclude`보다 우선하는 경우처럼, 문자열
    확인만으로는 통과하지만 실제로는 추적 대상인 상태를 여기서 잡는다.
    """
    unignored = []
    for relpath in probes:
        result = _git(["check-ignore", "-q", "--", relpath], cwd=root)
        if result.returncode == 1:
            unignored.append(relpath)
        elif result.returncode != 0:
            raise ToolError(
                "git_command_failed",
                "check-ignore %s: %s" % (relpath, (result.stderr or "").strip()),
            )
    if unignored:
        raise ToolError("ignore_verification_failed", unignored_paths=unignored)


# ─────────────────────────────────────────────────────────────────────────────
# run identity·run root
# ─────────────────────────────────────────────────────────────────────────────


def new_run_id():
    """`init`이 자체 발급하는 run identity.

    OPPL은 `state.json.run_id`를 SSOT로 삼지만(D8), OPPB는 한 태스크 아래에서도
    재실행을 구분하고 기존 run을 덮어쓰지 않기 위해 런타임이 새 ID를 발급한다.
    """
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return "%s-%s" % (stamp, uuid.uuid4().hex[:8])


def atomic_write_json(path, payload):
    """대상 디렉토리에 임시 파일을 만들고 fsync 후 교체한다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def run_root_for(task_root, run_id):
    return task_root / RUN_ROOT_DIRNAME / run_id


def cache_root_for(allocator_root):
    return allocator_root.joinpath(*CACHE_ROOT_SEGMENTS)


def _is_within(child, parent):
    try:
        return os.path.commonpath((os.path.realpath(child), os.path.realpath(parent))) == os.path.realpath(parent)
    except ValueError:
        return False


def _relative_posix(child, parent):
    try:
        return pathlib.Path(os.path.realpath(child)).relative_to(
            pathlib.Path(os.path.realpath(parent))
        ).as_posix()
    except ValueError as exc:
        raise ToolError("task_root_outside_project", "task_root=%s project_root=%s" % (child, parent)) from exc


def _read_run_manifest(run_root):
    path = pathlib.Path(run_root) / "run.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolError("run_manifest_invalid", "%s: %s" % (path, exc)) from exc
    if not isinstance(document, dict) or document.get("run_id") != pathlib.Path(run_root).name:
        raise ToolError("run_manifest_invalid", "run_id 불일치: %s" % path)
    return document


# ─────────────────────────────────────────────────────────────────────────────
# 서브 명령
# ─────────────────────────────────────────────────────────────────────────────


def cmd_init(opts):
    """태스크 귀속 run root·공유 cache root를 만들고 미추적 보장을 확인한다.

    검사는 부작용보다 먼저 끝낸다 — 인자·저장소 검증, exclude 등록, ignore 판정
    확인을 모두 통과한 뒤에만 디렉토리를 만든다. 거부된 호출이 `.oppb-run/`이나
    `.opal-cache/`를 남기지 않는다.

    멱등 계약: 재호출은 기존 run root를 건드리지 않는다. run identity를 매번 새로
    발급하므로 이전 run의 상태·카운터를 덮어쓰거나 0으로 되돌리는 경로가 없다.
    이미 존재하는 run root의 `run.json`도 다시 쓰지 않는다.
    """
    allocator_root = require_absolute_dir(
        opts,
        "allocator_root",
        "allocator_root_missing",
        "allocator_root_not_absolute",
        "allocator_root_not_found",
    )
    project_root = require_absolute_dir(
        opts,
        "project_root",
        "project_root_missing",
        "project_root_not_absolute",
        "project_root_not_found",
    )
    task_root = require_absolute_dir(
        opts,
        "task_root",
        "task_root_missing",
        "task_root_not_absolute",
        "task_root_not_found",
    )

    repository_toplevel(allocator_root)
    repository_toplevel(project_root, kind="project")
    task_rel = _relative_posix(task_root, project_root)
    exclude_path, run_added = register_exclude_entries(
        project_root,
        ("%s/" % RUN_ROOT_DIRNAME,),
    )
    cache_exclude_path, cache_added = register_exclude_entries(
        allocator_root,
        ("/".join(CACHE_ROOT_SEGMENTS) + "/",),
    )
    verify_ignore_decisions(project_root, ("%s/%s/.oppb-ignore-probe" % (task_rel, RUN_ROOT_DIRNAME),))
    verify_ignore_decisions(allocator_root, (CACHE_IGNORE_PROBE,))

    run_id = new_run_id()
    run_root = run_root_for(task_root, run_id)
    cache_root = cache_root_for(allocator_root)
    if task_root.is_symlink() or run_root.parent.is_symlink():
        raise ToolError("run_root_create_failed", "symlink 경로=%s" % run_root.parent)
    if cache_root.is_symlink() or cache_root.parent.is_symlink():
        raise ToolError("run_root_create_failed", "symlink 경로=%s" % cache_root)
    try:
        run_root.mkdir(parents=True, exist_ok=True)
        cache_root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ToolError("run_root_create_failed", str(exc)) from exc

    manifest = run_root / "run.json"
    if not manifest.exists():
        atomic_write_json(
            manifest,
            {
                "schema_version": SCHEMA_VERSION,
                "run_id": run_id,
                "allocator_root": str(allocator_root),
                "project_root": str(project_root),
                "cache_root": str(cache_root),
                "created_at": datetime.datetime.now(datetime.timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
            },
        )

    return ok(
        "init",
        run_id=run_id,
        run_root=str(run_root),
        cache_root=str(cache_root),
        allocator_root=str(allocator_root),
        project_root=str(project_root),
        task_root=str(task_root),
        exclude_path=str(exclude_path),
        cache_exclude_path=str(cache_exclude_path),
        exclude_entries_added=run_added + cache_added,
    )


def guarded_run_root(opts, allow_closed=False):
    """신규 task run root와 legacy hub run root를 manifest 기반으로 검증한다.

    신규 위치는 task/project 경계를, legacy 위치는 allocator 경계를 확인한다. 어느
    경우에도 cwd나 `.opal-worktrees` 문자열로 상위 경로를 추론하지 않는다.
    """
    raw = opts.get("run_root")
    if not raw:
        raise ToolError("run_root_missing")
    if not os.path.isabs(raw):
        raise ToolError("run_root_not_absolute", "받은 값: %s" % raw)
    run_root = pathlib.Path(raw)
    if (
        run_root.is_symlink()
        or run_root.parent.is_symlink()
        or run_root.parent.parent.is_symlink()
    ):
        raise ToolError("run_root_invalid", "symlink 경로=%s" % run_root)
    if not run_root.is_dir():
        raise ToolError("run_root_not_found", "받은 값: %s" % raw)
    closed = (run_root / RUN_CLOSED_NAME).is_file()
    if closed and not allow_closed:
        raise ToolError("run_closed", "run_root=%s" % run_root)

    manifest = _read_run_manifest(run_root)
    allocator_root = pathlib.Path(manifest.get("allocator_root") or "")
    project_root = pathlib.Path(manifest.get("project_root") or "")
    if not allocator_root.is_absolute() or not project_root.is_absolute():
        raise ToolError("run_manifest_invalid", "root 필드가 절대경로가 아님")

    if run_root.parent.name == RUN_ROOT_DIRNAME:
        task_root = run_root.parent.parent
        if closed:
            canonical_tasks = allocator_root / "tasks"
            if os.path.realpath(task_root.parent) != os.path.realpath(canonical_tasks):
                raise ToolError(
                    "run_root_invalid",
                    "종료 보존본이 canonical tasks 밖에 있음: %s" % task_root,
                )
        else:
            if not _is_within(task_root, project_root):
                raise ToolError(
                    "run_root_invalid",
                    "task_root=%s project_root=%s" % (task_root, project_root),
                )
            repository_toplevel(project_root, kind="project")
            task_rel = _relative_posix(task_root, project_root)
            verify_ignore_decisions(
                project_root,
                ("%s/%s/.oppb-ignore-probe" % (task_rel, RUN_ROOT_DIRNAME),),
            )
            repository_toplevel(allocator_root)
            verify_ignore_decisions(allocator_root, (CACHE_IGNORE_PROBE,))
    elif run_root.parent.name == LEGACY_RUN_ROOT_DIRNAME:
        if os.path.realpath(run_root.parent.parent) != os.path.realpath(allocator_root):
            raise ToolError("run_root_invalid", "legacy allocator_root 불일치")
        repository_toplevel(allocator_root)
        verify_ignore_decisions(
            allocator_root,
            (
                "%s/.oppb-ignore-probe" % LEGACY_RUN_ROOT_DIRNAME,
                CACHE_IGNORE_PROBE,
            ),
        )
    else:
        raise ToolError("run_root_invalid", "받은 값: %s" % run_root)
    return run_root


def _assert_no_symlinks(root):
    for path in pathlib.Path(root).rglob("*"):
        if path.is_symlink():
            raise ToolError("archive_symlink_forbidden", "경로=%s" % path)


@contextlib.contextmanager
def _hold_archive_locks(run_fd):
    """Supervisor 종료와 workgraph 정지를 같은 snapshot 구간에서 고정한다."""
    handles = []
    try:
        for name in ("supervisor.lock", "workgraph.lock"):
            try:
                fd = os.open(
                    name,
                    os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=run_fd,
                )
            except OSError as exc:
                raise ToolError(
                    "archive_symlink_forbidden",
                    "archive lock 경로를 열 수 없음: %s" % name,
                ) from exc
            handle = os.fdopen(fd, "a+")
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                handle.close()
                raise ToolError(
                    "run_not_finalizable",
                    "archive lock을 획득할 수 없음: %s" % name,
                ) from exc
            handles.append(handle)
        yield
    finally:
        for handle in reversed(handles):
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()


def _read_text_at(root_fd, name):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=root_fd)
    with os.fdopen(fd, "r", encoding="utf-8") as handle:
        return handle.read()


def _require_successful_run(run_fd):
    try:
        workgraph = json.loads(_read_text_at(run_fd, "workgraph.json"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolError("run_not_finalizable", "workgraph.json: %s" % exc) from exc
    incomplete = [
        str(item.get("id") or "<unknown>")
        for item in workgraph.get("mini_tasks") or []
        if item.get("state") != "accepted"
    ]
    try:
        events = _read_text_at(run_fd, "events.jsonl").splitlines()
        completed = any(
            json.loads(line).get("event") == "run_completed"
            for line in events
            if line.strip()
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolError("run_not_finalizable", "events.jsonl: %s" % exc) from exc
    if incomplete or not completed:
        raise ToolError(
            "run_not_finalizable",
            "미수락 task=%s, run_completed=%s" % (incomplete, completed),
        )


def _new_tree_digest():
    digest = hashlib.sha256()
    digest.update(b"OPPB-ARCHIVE-TREE-V1\0")
    return digest


def _hash_entry_header(digest, entry_type, relpath, size):
    relpath_bytes = relpath.encode("utf-8")
    digest.update(entry_type)
    digest.update(len(relpath_bytes).to_bytes(8, "big"))
    digest.update(relpath_bytes)
    digest.update(size.to_bytes(8, "big"))


def _hash_file(digest, relpath, source_fd, size):
    _hash_entry_header(digest, b"F", relpath, size)
    observed_size = 0
    while True:
        block = os.read(source_fd, 1024 * 1024)
        if not block:
            break
        observed_size += len(block)
        digest.update(block)
        yield block
    if observed_size != size:
        raise ToolError(
            "archive_integrity_failed",
            "복사 중 파일 크기 변경: %s" % relpath,
        )


def _copy_retained_tree(source_fd, destination_fd, digest, prefix="", removed=None):
    removed = [] if removed is None else removed
    for name in sorted(os.listdir(source_fd)):
        relpath = "%s/%s" % (prefix, name) if prefix else name
        info = os.stat(name, dir_fd=source_fd, follow_symlinks=False)
        if stat.S_ISLNK(info.st_mode):
            raise ToolError("archive_symlink_forbidden", "경로=%s" % relpath)
        if stat.S_ISDIR(info.st_mode):
            if relpath in ("verify-sandboxes", "checkpoint/tmp-index"):
                removed.append(relpath)
                continue
            _hash_entry_header(digest, b"D", relpath, 0)
            os.mkdir(name, info.st_mode & 0o777, dir_fd=destination_fd)
            source_child = os.open(
                name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=source_fd,
            )
            destination_child = os.open(
                name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=destination_fd,
            )
            try:
                _copy_retained_tree(
                    source_child,
                    destination_child,
                    digest,
                    relpath,
                    removed,
                )
            finally:
                os.close(destination_child)
                os.close(source_child)
            continue
        if not stat.S_ISREG(info.st_mode):
            raise ToolError("archive_symlink_forbidden", "특수 파일=%s" % relpath)
        if (
            name.endswith(".lock")
            or name.startswith(".supervisor-handshake-")
            or name == "supervisor.json"
        ):
            removed.append(relpath)
            continue
        source_file = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=source_fd)
        destination_file = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            info.st_mode & 0o777,
            dir_fd=destination_fd,
        )
        try:
            for block in _hash_file(digest, relpath, source_file, info.st_size):
                view = memoryview(block)
                while view:
                    view = view[os.write(destination_file, view):]
            os.fsync(destination_file)
        finally:
            os.close(destination_file)
            os.close(source_file)
    return sorted(removed)


def _tree_sha256_at(root_fd, prefix="", digest=None):
    digest = _new_tree_digest() if digest is None else digest
    for name in sorted(os.listdir(root_fd)):
        relpath = "%s/%s" % (prefix, name) if prefix else name
        info = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
        if stat.S_ISLNK(info.st_mode):
            raise ToolError("archive_integrity_failed", "symlink=%s" % relpath)
        if stat.S_ISDIR(info.st_mode):
            _hash_entry_header(digest, b"D", relpath, 0)
            child = os.open(
                name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=root_fd,
            )
            try:
                _tree_sha256_at(child, relpath, digest)
            finally:
                os.close(child)
        elif stat.S_ISREG(info.st_mode) and relpath != RUN_CLOSED_NAME:
            source = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=root_fd)
            try:
                for _block in _hash_file(digest, relpath, source, info.st_size):
                    pass
            finally:
                os.close(source)
        elif not stat.S_ISREG(info.st_mode):
            raise ToolError("archive_integrity_failed", "특수 파일=%s" % relpath)
    return digest.hexdigest()


def _write_json_at(root_fd, name, payload):
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    fd = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=root_fd,
    )
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)


def _remove_tree_at(parent_fd, name):
    child_fd = os.open(
        name,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
        dir_fd=parent_fd,
    )
    try:
        for child in os.listdir(child_fd):
            info = os.stat(child, dir_fd=child_fd, follow_symlinks=False)
            if stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode):
                _remove_tree_at(child_fd, child)
            else:
                os.unlink(child, dir_fd=child_fd)
    finally:
        os.close(child_fd)
    os.rmdir(name, dir_fd=parent_fd)


@contextlib.contextmanager
def _open_archive_parent(allocator_root, task_name):
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    handles = []
    try:
        allocator_fd = os.open(allocator_root, flags)
        handles.append(allocator_fd)
        tasks_fd = os.open("tasks", flags, dir_fd=allocator_fd)
        handles.append(tasks_fd)
        task_fd = os.open(task_name, flags, dir_fd=tasks_fd)
        handles.append(task_fd)
        try:
            os.mkdir(RUN_ROOT_DIRNAME, 0o700, dir_fd=task_fd)
        except FileExistsError:
            pass
        archive_fd = os.open(RUN_ROOT_DIRNAME, flags, dir_fd=task_fd)
        handles.append(archive_fd)
        yield archive_fd
    except OSError as exc:
        raise ToolError("archive_task_path_invalid", str(exc)) from exc
    finally:
        for handle in reversed(handles):
            os.close(handle)


def cmd_finalize_run(opts):
    """성공 실행의 보존 가치가 있는 기록을 canonical 태스크 폴더에 게시한다."""
    run_root = guarded_run_root(opts)
    if run_root.parent.name != RUN_ROOT_DIRNAME:
        raise ToolError("run_root_invalid", "legacy run은 finalize-run 대상이 아님")
    allocator_root = require_absolute_dir(
        opts,
        "allocator_root",
        "allocator_root_missing",
        "allocator_root_not_absolute",
        "allocator_root_not_found",
    )
    repository_toplevel(allocator_root)
    destination_task = require_absolute_dir(
        opts,
        "task_path",
        "archive_task_path_invalid",
        "archive_task_path_invalid",
        "archive_task_path_invalid",
    )
    if destination_task.is_symlink():
        raise ToolError("archive_symlink_forbidden", "경로=%s" % destination_task)
    manifest = _read_run_manifest(run_root)
    if os.path.realpath(manifest["allocator_root"]) != os.path.realpath(allocator_root):
        raise ToolError(
            "archive_task_path_invalid",
            "명시 allocator와 run manifest가 다름",
        )
    source_task = run_root.parent.parent
    canonical_tasks = allocator_root / "tasks"
    if (
        destination_task.name != source_task.name
        or os.path.realpath(destination_task.parent) != os.path.realpath(canonical_tasks)
        or not _is_within(destination_task, canonical_tasks)
    ):
        raise ToolError(
            "archive_task_path_invalid",
            "source=%s destination=%s allocator=%s" % (
                source_task, destination_task, allocator_root,
            ),
        )

    archive_parent = destination_task / RUN_ROOT_DIRNAME
    if archive_parent.is_symlink():
        raise ToolError("archive_symlink_forbidden", "경로=%s" % archive_parent)
    if archive_parent.exists() and not archive_parent.is_dir():
        raise ToolError("archive_task_path_invalid", "경로=%s" % archive_parent)
    archived_root = archive_parent / run_root.name
    if os.path.realpath(archived_root) == os.path.realpath(run_root):
        raise ToolError("archive_task_path_invalid", "source와 destination이 같습니다")

    _assert_no_symlinks(run_root)
    source_fd = os.open(
        run_root,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
    )
    try:
        with _open_archive_parent(allocator_root, destination_task.name) as archive_fd:
            with _hold_archive_locks(source_fd):
                _require_successful_run(source_fd)
                flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                try:
                    archived_fd = os.open(run_root.name, flags, dir_fd=archive_fd)
                except FileNotFoundError:
                    archived_fd = None
                if archived_fd is not None:
                    try:
                        try:
                            document = json.loads(
                                _read_text_at(archived_fd, RUN_CLOSED_NAME)
                            )
                        except (OSError, json.JSONDecodeError) as exc:
                            raise ToolError(
                                "archive_integrity_failed",
                                "marker=%s" % exc,
                            ) from exc
                        observed_hash = _tree_sha256_at(archived_fd)
                    finally:
                        os.close(archived_fd)
                    if (
                        document.get("run_id") != run_root.name
                        or document.get("content_sha256") != observed_hash
                    ):
                        raise ToolError(
                            "archive_integrity_failed",
                            "경로=%s" % archived_root,
                        )
                    return ok(
                        "finalize-run",
                        run_root=str(run_root),
                        archived_run_root=str(archived_root),
                        content_sha256=observed_hash,
                        removed=document.get("removed") or [],
                        idempotent=True,
                    )

                tmp_name = ".tmp-%s-%s" % (run_root.name, uuid.uuid4().hex[:8])
                os.mkdir(tmp_name, 0o700, dir_fd=archive_fd)
                tmp_fd = os.open(tmp_name, flags, dir_fd=archive_fd)
                published = False
                try:
                    digest = _new_tree_digest()
                    removed = _copy_retained_tree(source_fd, tmp_fd, digest)
                    content_sha256 = digest.hexdigest()
                    closed_document = {
                        "schema_version": SCHEMA_VERSION,
                        "run_id": run_root.name,
                        "archived_at": datetime.datetime.now(datetime.timezone.utc)
                        .isoformat()
                        .replace("+00:00", "Z"),
                        "source_run_root": str(run_root),
                        "content_sha256": content_sha256,
                        "removed": removed,
                    }
                    _write_json_at(tmp_fd, RUN_CLOSED_NAME, closed_document)
                    os.fsync(tmp_fd)
                    os.close(tmp_fd)
                    tmp_fd = None
                    os.rename(
                        tmp_name,
                        run_root.name,
                        src_dir_fd=archive_fd,
                        dst_dir_fd=archive_fd,
                    )
                    os.fsync(archive_fd)
                    published = True
                except ToolError:
                    raise
                except OSError as exc:
                    raise ToolError("archive_failed", str(exc)) from exc
                finally:
                    if tmp_fd is not None:
                        os.close(tmp_fd)
                    if not published:
                        try:
                            _remove_tree_at(archive_fd, tmp_name)
                        except OSError:
                            pass

                return ok(
                    "finalize-run",
                    run_root=str(run_root),
                    archived_run_root=str(archived_root),
                    content_sha256=content_sha256,
                    removed=removed,
                    idempotent=False,
                )
    finally:
        os.close(source_fd)


def _supervise(command, opts):
    """진입 가드 통과 후 Supervisor를 기동한다(`start`·`resume` 공통 경로).

    재기동은 자동 복구다 — 강제 resume이나 수동 tick 경로를 따로 만들지 않는다.
    """
    run_root = guarded_run_root(opts)
    try:
        payload = supervisor.start_supervisor(run_root)
    except (supervisor.SupervisorError, controller.ControllerError) as exc:
        raise ToolError(exc.code, exc.message, exc.exit_code, **exc.extra) from exc
    return ok(
        command,
        run_root=str(run_root),
        supervisor_pid=payload["supervisor_pid"],
        recovery=payload.get("recovery"),
        reclaimed=payload.get("reclaimed"),
    )


def cmd_start(opts):
    """Supervisor 기동 — 상한 집행·Verifier 우선 배정·복구는 supervisor.py(W-8) 소유."""
    return _supervise("start", opts)


def cmd_resume(opts):
    """비정상 종료 뒤 재기동 — 재부착·수확 후 자동으로 tick을 재개한다."""
    return _supervise("resume", opts)


def cmd_status(opts):
    """run의 현재 관측값. 부작용이 없고 Supervisor를 기동하지 않는다."""
    run_root = guarded_run_root(opts, allow_closed=True)
    try:
        payload = supervisor.read_status(run_root)
        closed_path = run_root / RUN_CLOSED_NAME
        if closed_path.is_file():
            closed = json.loads(closed_path.read_text(encoding="utf-8"))
            archive_fd = os.open(
                run_root,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            )
            try:
                observed_hash = _tree_sha256_at(archive_fd)
            finally:
                os.close(archive_fd)
            if closed.get("content_sha256") != observed_hash:
                raise ToolError(
                    "archive_integrity_failed",
                    "경로=%s" % run_root,
                )
            payload.update(
                archived=True,
                archived_at=closed.get("archived_at"),
                content_sha256=observed_hash,
                supervisor_pid=None,
            )
        else:
            payload["archived"] = False
        return ok("status", **payload)
    except (supervisor.SupervisorError, controller.ControllerError) as exc:
        raise ToolError(exc.code, exc.message, exc.exit_code, **exc.extra) from exc


def cmd_workgraph(opts):
    """Controller 서브 명령 — 본체와 파일 계약은 controller.py(W-7)가 소유한다."""
    try:
        return ok("workgraph", **controller.workgraph_command(opts))
    except controller.ControllerError as exc:
        raise ToolError(exc.code, exc.message, exc.exit_code, **exc.extra) from exc


def cmd_evidence(opts):
    """Evidence 서브 명령 — 본체와 파일 계약은 evidence.py(W-9)가 소유한다."""
    try:
        return ok("evidence", **evidence.evidence_command(opts))
    except (evidence.EvidenceError, controller.ControllerError) as exc:
        raise ToolError(exc.code, exc.message, exc.exit_code, **exc.extra) from exc


def cmd_task(opts):
    """Task 서브 명령 — 본체와 파일 계약은 evidence.py(W-9)가 소유한다."""
    try:
        return ok("task", **evidence.task_command(opts))
    except (evidence.EvidenceError, controller.ControllerError) as exc:
        raise ToolError(exc.code, exc.message, exc.exit_code, **exc.extra) from exc


def cmd_lease(opts):
    """Lease 서브 명령 — 본체와 파일 계약은 lease.py(W-12)가 소유한다."""
    try:
        return ok("lease", **lease.lease_command(opts))
    except controller.ControllerError as exc:
        raise ToolError(exc.code, exc.message, exc.exit_code, **exc.extra) from exc


def cmd_probe(opts):
    """Probe 서브 명령 — 본체와 파일 계약은 probe.py(W-13)가 소유한다."""
    try:
        return ok("probe", **probe.probe_command(opts))
    except (probe.ProbeError, controller.ControllerError) as exc:
        raise ToolError(exc.code, exc.message, exc.exit_code, **exc.extra) from exc


def cmd_cache(opts):
    """Cache 서브 명령 — 본체와 cache root 파일 계약은 cache.py(W-15)가 소유한다."""
    try:
        return ok("cache", **cache.cache_command(opts))
    except cache.CacheError as exc:
        raise ToolError(exc.code, exc.message, exc.exit_code, **exc.extra) from exc


def cmd_checkpoint(opts):
    """Checkpoint 서브 명령 — 본체와 파일 계약은 checkpoint.py(W-14)가 소유한다."""
    try:
        return ok("checkpoint", **checkpoint.checkpoint_command(opts))
    except (checkpoint.CheckpointError, controller.ControllerError) as exc:
        raise ToolError(exc.code, exc.message, exc.exit_code, **exc.extra) from exc


def cmd_recover(opts):
    """Recovery 서브 명령 — 본체와 파일 계약은 recovery.py(W-16)가 소유한다."""
    try:
        return ok("recover", **recovery.recover_command(opts))
    except (recovery.RecoveryError, controller.ControllerError) as exc:
        raise ToolError(exc.code, exc.message, exc.exit_code, **exc.extra) from exc


def cmd_verifier(opts):
    """Verifier adapter 서브 명령 — 본체와 변환 계약은 verifier_adapter.py(W-24)가 소유한다."""
    try:
        return ok("verifier", **verifier_adapter.verifier_command(opts))
    except (
        verifier_adapter.VerifierAdapterError,
        evidence.EvidenceError,
        controller.ControllerError,
    ) as exc:
        raise ToolError(exc.code, exc.message, exc.exit_code, **exc.extra) from exc


def cmd_revalidate(opts):
    """Revalidation 서브 명령 — 본체와 전파 규칙은 revalidation.py(W-26)가 소유한다."""
    try:
        return ok("revalidate", **revalidation.revalidate_command(opts))
    except (revalidation.RevalidationError, controller.ControllerError) as exc:
        raise ToolError(exc.code, exc.message, exc.exit_code, **exc.extra) from exc


DISPATCH = {
    "init": cmd_init,
    "start": cmd_start,
    "resume": cmd_resume,
    "status": cmd_status,
    "finalize-run": cmd_finalize_run,
    "workgraph": cmd_workgraph,
    "evidence": cmd_evidence,
    "task": cmd_task,
    "lease": cmd_lease,
    "probe": cmd_probe,
    "cache": cmd_cache,
    "recover": cmd_recover,
    "checkpoint": cmd_checkpoint,
    "verifier": cmd_verifier,
    "revalidate": cmd_revalidate,
}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    command = None
    try:
        command, opts = parse_argv(argv)
        if command is None:
            raise ToolError(
                "usage_error",
                "서브 명령이 필요합니다: %s" % ", ".join(COMMANDS),
                EXIT_USAGE,
            )
        handler = DISPATCH.get(command)
        if handler is None:
            raise ToolError(
                "unknown_command",
                "지원 명령: %s" % ", ".join(COMMANDS),
                EXIT_USAGE,
            )
        return handler(opts)
    except ToolError as exc:
        return err(
            command or "oppb",
            exc.code,
            exc.message,
            exc.exit_code,
            **exc.extra,
        )
    except Exception as exc:  # 예외 경로에서도 단일 라인 JSON을 보장한다
        return err(command or "oppb", "internal_error", repr(exc))


if __name__ == "__main__":
    sys.exit(main())
