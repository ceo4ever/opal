"""
@header {
  "module": "oppb_runtime_tool",
  "task": "132",
  "layer": "util",
  "domain": "oppb-runtime",
  "description": "OPPB(프로젝트 빌드 파일럿) 실행 런타임 CLI 진입점 — 현재 `init`과 `start` 진입 가드를 소유한다. `init`은 allocator Git repository 루트에 run root(`.opal-runs/<run_id>/`)와 cache root(`.opal-cache/oppb/`)를 만들고, `.git/info/exclude`에 두 경로를 멱등 등록한 뒤 `git check-ignore`로 실제 ignore 판정을 확인하며, 확인에 실패하면 run 시작을 거부한다. allocator_root·project_root는 절대경로 명시 인자로만 받고 cwd·경로 세그먼트로 추론하지 않는다(harness/worktree.md §task root와 allocator root 계약 [MUST]). run identity는 `init`이 매 호출 새로 발급하며 기존 run root를 덮어쓰거나 초기화하지 않는다 — OPPB run root는 허브 소유라 태스크보다 오래 살아남는 것이 설계 요구다(제안서 §4.5). 출력은 단일 라인 JSON + exit code 계약을 따른다(harness/tool-output-contract.md). 표준 라이브러리와 git CLI만 사용하고 플랫폼 분기를 두지 않는다.",
  "exports": [
    "ERROR_CODES", "ok", "err", "parse_argv",
    "cmd_init", "cmd_start", "cmd_workgraph", "cmd_evidence", "cmd_task", "cmd_lease",
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

import datetime
import json
import os
import pathlib
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

RUN_ROOT_DIRNAME = ".opal-runs"
CACHE_ROOT_SEGMENTS = (".opal-cache", "oppb")

# `.git/info/exclude`에 등록하는 문자열 — run root·cache root 2종 고정
EXCLUDE_ENTRIES = (".opal-runs/", ".opal-cache/oppb/")

# ignore 판정 확인용 probe 상대경로. 등록 문자열 존재가 아니라 git의 실제 판정을 본다.
IGNORE_PROBES = (".opal-runs/.oppb-ignore-probe", ".opal-cache/oppb/.oppb-ignore-probe")

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
    "run_root_missing": "--run-root는 필수입니다.",
    "run_root_not_absolute": "--run-root는 절대경로여야 합니다.",
    "run_root_not_found": "--run-root 경로가 존재하지 않습니다.",
    "run_root_invalid": "--run-root가 <allocator_root>/.opal-runs/<run_id> 형태가 아닙니다.",
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
    "--allocator-root", "--project-root", "--run-root", "--spec",
    "--file", "--task-id", "--attempt", "--candidate",
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
    "init", "start", "status", "resume", "workgraph", "evidence", "task", "lease",
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


def repository_toplevel(root):
    """allocator_root가 git 저장소의 최상위인지 확인하고 그 경로를 돌려준다.

    최상위가 아니면 `.git/info/exclude`의 상대 패턴이 run root·cache root를 가리키지
    못하므로 등록과 ignore 판정 확인이 성립하지 않는다.
    """
    result = _git(["rev-parse", "--show-toplevel"], cwd=root)
    if result.returncode != 0:
        raise ToolError(
            "allocator_root_not_a_git_repository",
            (result.stderr or result.stdout).strip(),
        )
    toplevel = pathlib.Path(result.stdout.strip())
    if os.path.realpath(toplevel) != os.path.realpath(root):
        raise ToolError(
            "allocator_root_not_repository_root",
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


def register_exclude_entries(root):
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
        missing = [entry for entry in EXCLUDE_ENTRIES if entry not in present]
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


def verify_ignore_decisions(root):
    """등록 문자열이 아니라 git의 실제 ignore 판정을 확인한다.

    `.gitignore`의 부정 패턴이 `.git/info/exclude`보다 우선하는 경우처럼, 문자열
    확인만으로는 통과하지만 실제로는 추적 대상인 상태를 여기서 잡는다.
    """
    unignored = []
    for relpath in IGNORE_PROBES:
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

    OPPL은 `state.json.run_id`를 SSOT로 삼지만(D8) OPPB run root는 허브
    `<allocator_root>/.opal-runs/<run_id>/`에 있고 태스크 회수 뒤에도 남아야 한다
    (제안서 §4.5). 태스크 상태에 묶으면 그 요구가 깨지므로 여기서 발급한다.
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


def run_root_for(allocator_root, run_id):
    return allocator_root / RUN_ROOT_DIRNAME / run_id


def cache_root_for(allocator_root):
    return allocator_root.joinpath(*CACHE_ROOT_SEGMENTS)


def allocator_root_of(run_root):
    """run root 경로 계약에서 allocator_root를 되읽는다 — cwd 추론을 쓰지 않는다."""
    if run_root.parent.name != RUN_ROOT_DIRNAME:
        raise ToolError("run_root_invalid", "받은 값: %s" % run_root)
    return run_root.parent.parent


# ─────────────────────────────────────────────────────────────────────────────
# 서브 명령
# ─────────────────────────────────────────────────────────────────────────────


def cmd_init(opts):
    """run root·cache root를 만들고 미추적 보장을 확인한다.

    검사는 부작용보다 먼저 끝낸다 — 인자·저장소 검증, exclude 등록, ignore 판정
    확인을 모두 통과한 뒤에만 디렉토리를 만든다. 거부된 호출이 `.opal-runs/`나
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

    repository_toplevel(allocator_root)
    exclude_path, added = register_exclude_entries(allocator_root)
    verify_ignore_decisions(allocator_root)

    run_id = new_run_id()
    run_root = run_root_for(allocator_root, run_id)
    cache_root = cache_root_for(allocator_root)
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
        exclude_path=str(exclude_path),
        exclude_entries_added=added,
    )


def guarded_run_root(opts):
    """run을 가리키는 인자를 검증하고 §4.5 미추적 가드를 통과시킨다.

    ignore 판정 확인에 실패하면 run을 시작하지 않는다(제안서 §4.5).
    """
    raw = opts.get("run_root")
    if not raw:
        raise ToolError("run_root_missing")
    if not os.path.isabs(raw):
        raise ToolError("run_root_not_absolute", "받은 값: %s" % raw)
    run_root = pathlib.Path(raw)
    if not run_root.is_dir():
        raise ToolError("run_root_not_found", "받은 값: %s" % raw)

    allocator_root = allocator_root_of(run_root)
    repository_toplevel(allocator_root)
    verify_ignore_decisions(allocator_root)
    return run_root


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
    run_root = guarded_run_root(opts)
    try:
        return ok("status", **supervisor.read_status(run_root))
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
