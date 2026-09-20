"""
@header {
  "module": "agent_tool_adapter",
  "layer": "util",
  "domain": "opal-tools",
  "description": "adapter.pm-agent-tool 채널 변환기(CONTRACT.md §1.3 A1 / surfaces.json adapter.pm-agent-tool). PostToolUse(matcher Agent|Task) 훅 봉투를 stdin으로 받아 현재 Agent와 legacy Task를 같은 정규화 경로로 처리한다. 하네스가 남긴 서브에이전트 실행 파일 3원천 — 시작 메타(agent-<id>.meta.json), 증분 전사(agent-<id>.jsonl), terminal 원천(Agent의 구조화 toolUseResult 또는 legacy Task 호출자 전사의 <task-notification>) — 을 관측해 worker.started 1건 / activity 1건 이상 / terminal 1건을 방출한다. Agent terminal source.sha256은 구조화 결과의 canonical JSON 바이트 해시만 쓰며 본문은 어느 필드에도 옮기지 않는다. 모든 emit은 A1 조합(actor.kind=worker ∧ provenance.type=adapter ∧ recorded_by.kind=adapter)이고 source.{kind,id,sha256,observed_at}를 채우며 source.kind는 agent_handshake|agent_message|tool_result 중 하나다. 방출은 run-log-tool append CLI 서브프로세스 호출로만 하고 run_log_core를 import하지 않는다(§3.1 채널 변환기 금지사항 — 코어 직접 링크·상태 전이·기록 조각 직접 읽기·자기 등급 선언·마스킹 자체 구현 없음). run_id는 state-tool show --format json의 run_log.active_run_id에서만 얻고, task_path는 <cwd>/.opal/task-ownership.json 발급 사본에서만 읽는다(경로·식별자 추론 금지). summary·reason은 실제 입력 도구명·상태·건수만 담는 고정 템플릿이며 전사 본문·프롬프트·어시스턴트 출력·비밀값을 어떤 필드에도 옮기지 않는다(§1.3, TASK C-5/AC-7) — 원본은 sha256 해시로만 참조한다. 플랫폼 고유 봉투 키·파일 경로 패턴·종료 알림 문법은 이 파일의 _PLATFORM_* 상수 구역 한 곳에만 둔다(PRINCIPLES §Core Stance 플랫폼 독립성, TASK C-6). 중복 방출 억제는 <cwd>/.opal/run/.runtime/agent-tool-adapter/ 커서 파일의 순수 성능 최적화이며 정확성은 append의 (run_id, request_id) 멱등이 소유한다. 훅으로 등록되므로 전 경로 fail-safe — 어떤 실패에서도 무출력 exit 0이다.",
  "exports": ["main", "handle", "collect_emissions", "terminal_event_for_status",
              "worker_run_id_for", "request_id_for", "rfc3339_ms", "sha256_file",
              "resolve_task_path", "resolve_active_run_id", "ADAPTER_ID", "CHANNEL_ID"],
  "depends": []
}
"""
from __future__ import annotations

# 표준 라이브러리만 import한다(run-log-tool 관례). run_log_core를 import하지 않는다(§3.1).
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────────────────────
# _PLATFORM_* — 플랫폼 고유 봉투 키·경로·문법. **이 구역 밖에 두지 않는다**(C-6).
# ─────────────────────────────────────────────────────────────────────────────
_PLATFORM_TOOL_NAMES = ("Agent", "Task")
_PLATFORM_ENVELOPE_TOOL_NAME_KEY = "tool_name"
_PLATFORM_ENVELOPE_CWD_KEY = "cwd"
_PLATFORM_ENVELOPE_TRANSCRIPT_KEY = "transcript_path"
_PLATFORM_ENVELOPE_SESSION_KEY = "session_id"
_PLATFORM_ENVELOPE_TOOL_RESPONSE_KEYS = ("toolUseResult", "tool_response")
_PLATFORM_TOOL_RESPONSE_AGENT_ID_KEY = "agentId"
_PLATFORM_SUBAGENT_DIR_NAME = "subagents"
_PLATFORM_AGENT_FILE_PREFIX = "agent-"
_PLATFORM_AGENT_META_SUFFIX = ".meta.json"
_PLATFORM_AGENT_LOG_SUFFIX = ".jsonl"
_PLATFORM_META_AGENT_TYPE_KEY = "agentType"
_PLATFORM_TASK_NOTIFICATION_RE = re.compile(
    r"<task-notification>(?:(?!</task-notification>).)*?"
    r"<task-id>(?P<agent_id>[A-Za-z0-9_-]{1,64})</task-id>"
    r"(?:(?!</task-notification>).)*?"
    r"<status>(?P<status>[A-Za-z0-9_-]{1,32})</status>"
    r"(?:(?!</task-notification>).)*?</task-notification>",
    re.S,
)
# 하네스 종료 알림 <status> → 표준 terminal 사건. 표에 없는 값은 추정하지 않고 건너뛴다.
_PLATFORM_TERMINAL_EVENT_BY_STATUS = {
    "completed": "worker.completed",
    "success": "worker.completed",
    "failed": "worker.failed",
    "error": "worker.failed",
    "timeout": "worker.failed",
    "blocked": "worker.blocked",
    "cancelled": "worker.blocked",
    "canceled": "worker.blocked",
}

# ─────────────────────────────────────────────────────────────────────────────
# 채널·변환기 식별자와 고정 템플릿
# ─────────────────────────────────────────────────────────────────────────────
ADAPTER_ID = "agent-tool-adapter"
CHANNEL_ID = "pm-agent-tool"

# 발급 식별자 파생용 고정 네임스페이스(UUIDv5). 같은 입력이면 항상 같은 값이다.
_ID_NAMESPACE = uuid.UUID("0f3a8b1e-6f2c-5a47-9c1d-7b5e2a904c31")

# [MUST] CONTRACT §1.3 — 원본 프롬프트·chain-of-thought·비밀값을 어떤 필드에도 넣지 않는다.
# summary/reason은 도구명·상태·건수만 담는 이 고정 템플릿 2개가 전부다.
_SUMMARY_TEMPLATE = "{tool} adapter: {event} status={status} records={records}"
_REASON_TEMPLATE = "{tool} adapter: {event} status={status}"

_DURATION_UNKNOWN_REASON = "adapter_post_hoc_observation_no_monotonic_span"
_ACTIVITY_DATA = {"kind": "progress"}

# 발급값 사본(추론 금지) — <cwd>/.opal/task-ownership.json
_OWNERSHIP_COPY_REL = (".opal", "task-ownership.json")
_OWNERSHIP_TASK_PATH_KEY = "task_path"
# 커서(순수 최적화) — <cwd>/.opal/run/.runtime/agent-tool-adapter/<key>.json
_CURSOR_REL = (".opal", "run", ".runtime", "agent-tool-adapter")
_CURSOR_MAX_ENTRIES = 600

_MAX_AGENTS_PER_INVOCATION = 12
_SUBPROCESS_TIMEOUT_S = 45
_MAX_TRANSCRIPT_BYTES = 64 * 1024 * 1024


# ─────────────────────────────────────────────────────────────────────────────
# 순수 헬퍼
# ─────────────────────────────────────────────────────────────────────────────
def rfc3339_ms(epoch_seconds):
    """epoch 초를 CONTRACT §1.1의 UTC RFC 3339 밀리초 문자열로 바꾼다."""
    dt = datetime.fromtimestamp(float(epoch_seconds), tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def sha256_file(path):
    """파일 원본 바이트의 SHA-256 hex. 읽을 수 없으면 None."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def worker_run_id_for(scope, agent_id):
    """(세션 범위, 에이전트 id)에서 결정론적으로 파생한 worker_run_id."""
    return "wrk_" + str(uuid.uuid5(_ID_NAMESPACE, f"worker/{scope}/{agent_id}"))


def request_id_for(run_id, agent_id, label, digest):
    """(run, 에이전트, 사건 라벨, 원본 해시)에서 파생한 안정 request_id.

    원본 내용이 같으면 재실행해도 같은 값이라 append의 (run_id, request_id)
    멱등 판정이 그대로 걸린다(CONTRACT §1.1).
    """
    return "req_" + str(uuid.uuid5(_ID_NAMESPACE, f"{run_id}/{agent_id}/{label}/{digest}"))


def terminal_event_for_status(status):
    """종료 알림 status → terminal 사건 종류. 모르는 값은 None(추정 금지)."""
    if not isinstance(status, str):
        return None
    return _PLATFORM_TERMINAL_EVENT_BY_STATUS.get(status.strip().lower())


def _count_lines(path):
    n = 0
    with open(path, "rb") as fh:
        for _ in fh:
            n += 1
    return n


def _bump(observed_at_iso, previous_iso):
    """observed_at 단조성 보정 — §1.3 완료 알림 분해 금지 불변식 3번."""
    if previous_iso is None or observed_at_iso > previous_iso:
        return observed_at_iso
    epoch = datetime.strptime(previous_iso, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
        tzinfo=timezone.utc).timestamp()
    return rfc3339_ms(epoch + 0.001)


# ─────────────────────────────────────────────────────────────────────────────
# 발급값 조회 — 추론하지 않는다
# ─────────────────────────────────────────────────────────────────────────────
def resolve_task_path(cwd):
    """<cwd>/.opal/task-ownership.json 발급 사본의 task_path. 없으면 None."""
    copy_path = pathlib.Path(cwd).joinpath(*_OWNERSHIP_COPY_REL)
    try:
        with open(copy_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:  # noqa: BLE001 — 부재·손상은 방출 없음(fail-safe)
        return None
    value = data.get(_OWNERSHIP_TASK_PATH_KEY) if isinstance(data, dict) else None
    return value if isinstance(value, str) and os.path.isabs(value) else None


def _tool_run_sh(tool_name):
    """이 파일 위치 기준의 도구 래퍼 경로(워크트리 소스·배포본 모두 동일 상대 위치)."""
    return pathlib.Path(__file__).resolve().parent.parent.parent / tool_name / "run.sh"


def resolve_active_run_id(task_path, state_tool_run_sh=None):
    """state-tool show --format json의 run_log.active_run_id **에서만** run_id를 얻는다."""
    run_sh = pathlib.Path(state_tool_run_sh) if state_tool_run_sh else _tool_run_sh("state-tool")
    try:
        proc = subprocess.run([str(run_sh), "show", str(task_path), "--format", "json"],
                              capture_output=True, text=True, timeout=_SUBPROCESS_TIMEOUT_S)
        if proc.returncode != 0:
            return None
        payload = json.loads(proc.stdout)
    except Exception:  # noqa: BLE001 — 조회 실패는 방출 없음(fail-safe)
        return None
    data = payload.get("data") if isinstance(payload, dict) else None
    run_log = data.get("run_log") if isinstance(data, dict) else None
    value = run_log.get("active_run_id") if isinstance(run_log, dict) else None
    return value if isinstance(value, str) and value else None


# ─────────────────────────────────────────────────────────────────────────────
# 관측 → 방출 명세 조립 (순수 함수: 파일을 읽지만 아무것도 쓰지 않는다)
# ─────────────────────────────────────────────────────────────────────────────
def _terminal_index(transcript_path):
    """호출자 전사의 <task-notification>을 terminal 원천으로 모은다.

    블록 **본문은 반환하지 않는다** — 해시와 status 토큰만 남긴다(§1.3).
    """
    index = {}
    try:
        size = os.path.getsize(transcript_path)
    except OSError:
        return index
    if size > _MAX_TRANSCRIPT_BYTES:
        return index
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return index
    for match in _PLATFORM_TASK_NOTIFICATION_RE.finditer(text):
        block = match.group(0)
        index[match.group("agent_id")] = (
            match.group("status"),
            hashlib.sha256(block.encode("utf-8")).hexdigest(),
            f"task-notification:{match.group('agent_id')}",
        )
    return index


def _agent_structured_terminal(tool_result):
    """Agent toolUseResult의 알려진 status만 terminal 원천으로 정규화한다."""
    if not isinstance(tool_result, dict):
        return {}
    agent_id = tool_result.get(_PLATFORM_TOOL_RESPONSE_AGENT_ID_KEY)
    status = tool_result.get("status")
    if not isinstance(agent_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", agent_id):
        return {}
    if terminal_event_for_status(status) is None:
        return {}
    try:
        canonical = json.dumps(tool_result, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError):
        return {}
    return {
        agent_id: (
            status,
            hashlib.sha256(canonical).hexdigest(),
            f"agent-tool-result:{agent_id}",
        ),
    }


def _agent_ids(subagents_dir, focus_agent_id):
    """처리 대상 에이전트 id — 봉투가 지목한 것 + 최근 수정 순 상위 N개."""
    ordered = []
    try:
        entries = [p for p in subagents_dir.iterdir()
                   if p.name.startswith(_PLATFORM_AGENT_FILE_PREFIX)
                   and p.name.endswith(_PLATFORM_AGENT_META_SUFFIX)]
    except OSError:
        entries = []
    entries.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    for path in entries[:_MAX_AGENTS_PER_INVOCATION]:
        ordered.append(path.name[len(_PLATFORM_AGENT_FILE_PREFIX):
                                 -len(_PLATFORM_AGENT_META_SUFFIX)])
    if focus_agent_id and focus_agent_id not in ordered:
        ordered.insert(0, focus_agent_id)
    return ordered


def collect_emissions(subagents_dir, transcript_path, run_id, scope, focus_agent_id=None,
                      platform_tool_name="Task", structured_terminals=None):
    """관측 원본 3종에서 append 인자 dict 목록을 만든다(부수효과 없음).

    각 항목은 A1 조합과 source.{kind,id,sha256,observed_at}를 갖춘다.
    """
    subagents_dir = pathlib.Path(subagents_dir)
    terminals = _terminal_index(transcript_path) if transcript_path else {}
    if structured_terminals:
        terminals.update(structured_terminals)
    try:
        transcript_observed = rfc3339_ms(os.path.getmtime(transcript_path))
    except OSError:
        transcript_observed = None

    emissions = []
    for agent_id in _agent_ids(subagents_dir, focus_agent_id):
        meta_path = subagents_dir / (
            _PLATFORM_AGENT_FILE_PREFIX + agent_id + _PLATFORM_AGENT_META_SUFFIX)
        log_path = subagents_dir / (
            _PLATFORM_AGENT_FILE_PREFIX + agent_id + _PLATFORM_AGENT_LOG_SUFFIX)
        if not meta_path.is_file():
            continue
        try:
            meta_sha = sha256_file(meta_path)
            meta_observed = rfc3339_ms(meta_path.stat().st_mtime)
            with open(meta_path, encoding="utf-8") as fh:
                meta = json.load(fh)
        except Exception:  # noqa: BLE001 — 손상 원본은 그 에이전트만 건너뛴다
            continue
        agent_type = meta.get(_PLATFORM_META_AGENT_TYPE_KEY) if isinstance(meta, dict) else None
        actor_id = agent_type if isinstance(agent_type, str) and agent_type else f"agent:{agent_id}"
        worker_run_id = worker_run_id_for(scope, agent_id)

        emissions.append(_spec(
            run_id, agent_id, worker_run_id, actor_id, "worker.started",
            source_kind="agent_handshake",
            source_id=f"agent-meta:{agent_id}",
            source_sha256=meta_sha,
            observed_at=meta_observed,
            status="started", records=1,
            platform_tool_name=platform_tool_name,
        ))
        last_observed = meta_observed

        if log_path.is_file():
            log_sha = log_observed = None
            records = 0
            try:
                log_sha = sha256_file(log_path)
                log_observed = _bump(rfc3339_ms(log_path.stat().st_mtime), meta_observed)
                records = _count_lines(log_path)
            except OSError:
                log_sha = None
            if log_sha and records > 0:
                emissions.append(_spec(
                    run_id, agent_id, worker_run_id, actor_id, "activity",
                    source_kind="agent_message",
                    source_id=f"agent-log:{agent_id}:{log_sha[:12]}",
                    source_sha256=log_sha,
                    observed_at=log_observed,
                    status="running", records=records,
                    data=_ACTIVITY_DATA,
                    platform_tool_name=platform_tool_name,
                ))
                last_observed = log_observed

        status, block_sha, terminal_source_id = terminals.get(agent_id, (None, None, None))
        event = terminal_event_for_status(status)
        if event and block_sha:
            emissions.append(_spec(
                run_id, agent_id, worker_run_id, actor_id, event,
                source_kind="tool_result",
                source_id=terminal_source_id,
                source_sha256=block_sha,
                observed_at=_bump(transcript_observed or last_observed, last_observed),
                status=status, records=1,
                duration_unknown_reason=_DURATION_UNKNOWN_REASON,
                platform_tool_name=platform_tool_name,
            ))
    return emissions


def _spec(run_id, agent_id, worker_run_id, actor_id, event, *, source_kind, source_id,
          source_sha256, observed_at, status, records, data=None,
          duration_unknown_reason=None, platform_tool_name="Task"):
    summary = _SUMMARY_TEMPLATE.format(tool=platform_tool_name, event=event,
                                       status=status, records=records)
    spec = {
        "request_id": request_id_for(run_id, agent_id, event, source_sha256),
        "event": event,
        "actor_kind": "worker",
        "actor_id": actor_id,
        "provenance_type": "adapter",
        "recorded_by_kind": "adapter",
        "worker_run_id": worker_run_id,
        "source_kind": source_kind,
        "source_id": source_id,
        "source_sha256": source_sha256,
        "source_observed_at": observed_at,
        "summary": summary,
        "data": data,
        "duration_unknown_reason": duration_unknown_reason,
    }
    if event in ("worker.failed", "worker.blocked"):
        spec["reason"] = _REASON_TEMPLATE.format(tool=platform_tool_name,
                                                 event=event, status=status)
    return spec


# ─────────────────────────────────────────────────────────────────────────────
# 방출 — run-log-tool append CLI 표면만 호출한다(§3.1 코어 직접 링크 금지)
# ─────────────────────────────────────────────────────────────────────────────
def _append(task_path, run_id, spec, run_log_run_sh=None):
    run_sh = pathlib.Path(run_log_run_sh) if run_log_run_sh else _tool_run_sh("run-log-tool")
    argv = [str(run_sh), "append",
            "--task", str(task_path), "--run-id", run_id,
            "--request-id", spec["request_id"], "--event", spec["event"],
            "--actor-kind", spec["actor_kind"], "--actor-id", spec["actor_id"],
            "--provenance-type", spec["provenance_type"],
            "--recorded-by-kind", spec["recorded_by_kind"],
            "--recorded-by-id", ADAPTER_ID,
            "--worker-run-id", spec["worker_run_id"],
            "--source-kind", spec["source_kind"], "--source-id", spec["source_id"],
            "--source-sha256", spec["source_sha256"],
            "--source-observed-at", spec["source_observed_at"],
            "--summary", spec["summary"], "--format", "json"]
    if spec.get("reason"):
        argv += ["--reason", spec["reason"]]
    if spec.get("duration_unknown_reason"):
        argv += ["--duration-unknown-reason", spec["duration_unknown_reason"]]
    if spec.get("data") is not None:
        argv += ["--data", json.dumps(spec["data"], ensure_ascii=False)]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True,
                              timeout=_SUBPROCESS_TIMEOUT_S)
    except Exception:  # noqa: BLE001 — append 표면 실패는 이 사건 1건만 건너뛴다(fail-safe)
        return False
    return proc.returncode == 0


# ─────────────────────────────────────────────────────────────────────────────
# 커서 — 순수 성능 최적화(정확성은 append 멱등이 소유)
# ─────────────────────────────────────────────────────────────────────────────
def _cursor_path(cwd, scope):
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", str(scope))[:96] or "session"
    return pathlib.Path(cwd).joinpath(*_CURSOR_REL) / f"{safe}.json"


def _cursor_load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        emitted = data.get("emitted")
        return list(emitted) if isinstance(emitted, list) else []
    except Exception:  # noqa: BLE001 — 커서 부재·손상은 그냥 전량 재시도
        return []


def _cursor_save(path, emitted):
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        tmp = path.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"emitted": emitted[-_CURSOR_MAX_ENTRIES:]}, fh)
        os.replace(tmp, path)
    except Exception:  # noqa: BLE001 — 커서 쓰기 실패는 방출 결과에 영향이 없다
        pass


# ─────────────────────────────────────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────────────────────────────────────
def handle(payload, *, run_log_run_sh=None, state_tool_run_sh=None, use_cursor=True):
    """봉투 1건을 처리하고 방출 성공 건수를 돌려준다. 어떤 것도 stdout에 내지 않는다."""
    if not isinstance(payload, dict):
        return 0
    platform_tool_name = payload.get(_PLATFORM_ENVELOPE_TOOL_NAME_KEY)
    if platform_tool_name not in _PLATFORM_TOOL_NAMES:
        return 0
    cwd = payload.get(_PLATFORM_ENVELOPE_CWD_KEY)
    transcript_path = payload.get(_PLATFORM_ENVELOPE_TRANSCRIPT_KEY)
    if not cwd or not transcript_path:
        return 0

    task_path = resolve_task_path(cwd)
    if not task_path:
        return 0
    run_id = resolve_active_run_id(task_path, state_tool_run_sh)
    if not run_id:
        return 0

    transcript = pathlib.Path(transcript_path)
    subagents_dir = transcript.with_suffix("") / _PLATFORM_SUBAGENT_DIR_NAME
    scope = payload.get(_PLATFORM_ENVELOPE_SESSION_KEY) or transcript.stem

    tool_response = next((payload.get(key) for key in _PLATFORM_ENVELOPE_TOOL_RESPONSE_KEYS
                          if isinstance(payload.get(key), dict)), None)
    focus = None
    if isinstance(tool_response, dict):
        candidate = tool_response.get(_PLATFORM_TOOL_RESPONSE_AGENT_ID_KEY)
        if isinstance(candidate, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", candidate):
            focus = candidate

    structured_terminals = (_agent_structured_terminal(tool_response)
                            if platform_tool_name == "Agent" else None)
    specs = collect_emissions(subagents_dir, transcript, run_id, scope, focus,
                              platform_tool_name, structured_terminals)
    if not specs:
        return 0

    cursor_file = _cursor_path(cwd, scope) if use_cursor else None
    emitted = _cursor_load(cursor_file) if cursor_file else []
    seen = set(emitted)

    count = 0
    for spec in specs:
        if spec["request_id"] in seen:
            continue
        if _append(task_path, run_id, spec, run_log_run_sh):
            count += 1
            seen.add(spec["request_id"])
            emitted.append(spec["request_id"])
    if cursor_file:
        _cursor_save(cursor_file, emitted)
    return count


def main():
    """stdin PostToolUse(Agent|Task) 봉투 → 3종 사건 방출. 출력은 언제나 없다."""
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 — 봉투 파싱 실패는 무출력 통과(fail-safe)
        return
    handle(payload)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 — 전 경로 fail-safe: 어떤 예외에서도 세션을 막지 않는다.
        pass
    sys.exit(0)
