"""
@header {
  "module": "test_opal_agent_attempt",
  "layer": "test",
  "domain": "opal-tools",
  "description": "TASK 132 W-2 / S-2·S-3. opal-agent 공용 attempt runtime의 RED-first 스위트. S-2는 무출력 자식·손자 프로세스 트리로 process group 생성·독립 watchdog deadline 집행·PGID 전체 회수·고아 0·종료 사유 attempt record 기록을 실제 프로세스로 검증한다. S-3은 stream terminal framing(마지막 result 채택, epilogue allowlist 무해 처리, result 부재·미종료 잔존의 성공 오판 금지)을 공개 CLI 실행으로 검증한다. mock/patch 미사용.",
  "task": "132",
  "scenarios": ["S-2", "S-3"],
  "exports": [
    "TestS2ProcessGroupCreated", "TestS2SilentWatchdog",
    "TestS2PgidReclaimNoOrphans", "TestS2AttemptRecordExitReason",
    "TestS3TerminalFraming"
  ]
}

# 인용 규칙
# - TEST-SCENARIO.md(132) S-2·S-3 ↔ PLAN.md(132) §Work items W-1, §Decisions D6.
# - [MUST] harness/red-first.md §2 작성자≠구현자: opal-test-agent(RED)가 작성한다.
#   opal_agent.py(W-1)는 수정하지 않고, GREEN 구현 중 이 파일도 수정하지 않는다.
# - [MUST] harness/red-first.md §2 "테스트 substitute는 실제 integration 증거가 아니다"
#   + PLAN W-2 "mock 금지, 실제 프로세스만": unittest.mock을 import하지 않는다.
#   프로세스 생성·종료·PGID·고아 판정은 실제 프로세스 트리와 os.kill(pid, 0)로만 관측한다.
# - [MUST] PLAN H-6: 미확정 내부 함수·클래스를 import하지 않는다. 진입점은 공개 CLI
#   (`opal_agent.py <flags>`, run.sh가 exec하는 것과 동일 형태)이고, attempt record는
#   run root의 파일 계약으로만 접근한다.
# - 표준 라이브러리만 사용 (pytest는 러너로만 쓴다).

===============================================================================
확정 계약 (태스크 131 구현 — W-2가 정합한 기준)
===============================================================================
1. attempt 산출물 전달 채널 = CLI `--run-dir` + `--phase`(+ `--attempt`)
   = `call_agent`의 동명 kwonly 인자. 132가 RED 시점에 가정한 환경변수
   `OPAL_AGENT_RUN_ROOT` 채널은 **폐기됐다**. D6 (b)가 동결한 플래그 집합은
   "기존 플래그 무변경"이며 신규 플래그 추가를 금지하지 않는다.
2. attempt record 경로 = `<run_dir>/<phase>[.aN].attempt.json`.
   스키마는 README §attempt 산출물 소유가 SSOT다 — 132가 가정한
   `attempt_id`·`exit_reason` 4키는 폐기되고, 종료 사유는
   `status`·`exit_class`·`timeout_reason`(`None`|`hard`|`heartbeat`)가 담는다.
3. epilogue allowlist = `EPILOGUE_ALLOWLIST` — `type`이 아니라 **`subtype`** 기준의
   `background_tasks_changed` / `task_updated` / `task_notification`이다.
4. **stream framing 판정의 관측 채널은 프로세스 종료 코드가 아니라 attempt record다.**
   opal-agent의 종료 코드는 D6 (b)(c)가 동결했고(정상 0 / `is_error` 1 / 실행 오류 2),
   framing 판정은 `analyze_stream`의 `StreamVerdict`가 만들어 record의
   `status`·`exit_class`·`unterminated_children`으로 기록된다
   (README §stream terminal framing 5: "루트 exit 0 + PGID 소멸 + 최종 자식 terminal
   + result schema 성공이 모두 성립해야 `done`"). 소비할 result가 아예 없을 때만
   `_terminal_event`가 실행 오류(종료 코드 2)로 승격한다.

위 4항이 바뀌면 이 파일이 아니라 PLAN/계약을 먼저 고친다.

프로세스 관측 방법
-----------------
stub provider는 자기 `pid`/`pgid`/`ppid`를 JSON으로 파일에 쓰고 손자 프로세스를
하나 띄운 뒤 stdout에 한 글자도 쓰지 않고 장시간 sleep한다. opal-agent가 종료한
뒤 테스트가 그 파일을 읽어 `os.kill(pid, 0)`으로 자식·손자의 생존을 직접 확인한다.
손자는 stub이 죽으면 init에 재양육되므로 좀비가 아니라 진짜 고아로 남는다.
"""

import json
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import time
import unittest

_TESTS_DIR = pathlib.Path(__file__).resolve().parent
_TOOL_DIR = _TESTS_DIR.parent
_AGENT_PY = _TOOL_DIR / "opal_agent.py"

_PROBE_ENV = "OPAL_TEST_PROBE_FILE"
_STREAM_FIXTURE_ENV = "OPAL_TEST_STREAM_FIXTURE"

# attempt 산출물 계약(131). `--run-dir`+`--phase`가 함께 주어질 때만 opal-agent가
# 산출물 writer가 되고, record는 `<run_dir>/<phase>[.aN].attempt.json`에 기록된다.
_ATTEMPT_PHASE = "probe"

# 131 attempt record 스키마 — README §attempt 산출물 소유.
_ATTEMPT_RECORD_KEYS = (
    "phase", "attempt", "mode", "provider", "status", "exit_class",
    "pid", "pgid", "pgid_reclaimed", "exit_code", "timeout_reason",
    "started_at", "ended_at", "duration_ms", "fingerprint", "heartbeat",
    "terminal", "cost_used", "unterminated_children", "origin",
)

_AGENT_TIMEOUT = 2          # opal-agent에 주는 --timeout (초)
_GUARD = 20                 # 테스트가 opal-agent를 기다리는 상한 (초)
_REAP_GRACE = 3.0           # deadline 집행 후 PGID 회수를 기다리는 여유 (초)

# ─── stub provider: 무출력 + 손자 프로세스 ───────────────────────────────────

_STUB_SILENT_TREE = """#!/usr/bin/env python3
# 인자를 전부 무시하고, stdout/stderr에 아무것도 쓰지 않는다.
import json, os, subprocess, sys, time

grandchild = subprocess.Popen(
    [sys.executable, "-c", "import time; time.sleep(600)"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
probe = os.environ["OPAL_TEST_PROBE_FILE"]
tmp = probe + ".tmp"
with open(tmp, "w", encoding="utf-8") as fh:
    json.dump({
        "child_pid": os.getpid(),
        "child_pgid": os.getpgid(0),
        "child_ppid": os.getppid(),
        "child_sid": os.getsid(0),
        "grandchild_pid": grandchild.pid,
    }, fh)
os.replace(tmp, probe)
time.sleep(600)
"""

# stream fixture를 그대로 흘려보내는 stub. 줄 단위 flush로 passthrough를 재현한다.
_STUB_STREAM_REPLAY = """#!/usr/bin/env python3
import os, sys
with open(os.environ["OPAL_TEST_STREAM_FIXTURE"], "r", encoding="utf-8") as fh:
    for line in fh:
        sys.stdout.write(line)
        sys.stdout.flush()
sys.exit(0)
"""

# ─── S-3 stream fixture ─────────────────────────────────────────────────────

_EV_INIT = '{"type":"system","subtype":"init","session_id":"00000000-0000-4000-8000-0000000000aa"}'
_EV_ASSISTANT = '{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"working"}]}}'


def _result_event(is_error: bool, text: str) -> str:
    return json.dumps({
        "type": "result",
        "subtype": "error" if is_error else "success",
        "is_error": is_error,
        "result": text,
        "session_id": "00000000-0000-4000-8000-0000000000aa",
        "total_cost_usd": 0.01,
        "duration_ms": 1000,
    }, ensure_ascii=False)


_EV_EPILOGUE_BG = '{"type":"background_tasks_changed","tasks":[]}'
_EV_EPILOGUE_TASK = '{"type":"task_updated","task_id":"t-1","state":"done"}'
# 131 EPILOGUE_ALLOWLIST의 실제 판정 형태 — `type`이 아니라 `subtype` 기준이다.
_EV_EPILOGUE_SYS_BG = '{"type":"system","subtype":"background_tasks_changed","tasks":[]}'
# allowlist 밖 — result 이후에도 끝나지 않은 작업이 남아 있음을 알리는 이벤트
_EV_UNFINISHED = '{"type":"background_task_started","task_id":"t-2","state":"running"}'

_FIXTURES = {
    # (a) 성공 result 뒤에 allowlist epilogue가 붙은 stream
    "epilogue_after_result": [
        _EV_INIT, _EV_ASSISTANT, _result_event(False, "done"),
        _EV_EPILOGUE_BG, _EV_EPILOGUE_TASK,
    ],
    # (a') 같은 형태이되 채택될 result가 is_error=true — 채택 여부를 exit code로 관측
    "epilogue_after_error_result": [
        _EV_INIT, _EV_ASSISTANT, _result_event(True, "failed"),
        _EV_EPILOGUE_BG, _EV_EPILOGUE_TASK,
    ],
    # (a'') result가 두 번 — "마지막 result 채택"을 관측
    "two_results_last_wins": [
        _EV_INIT, _result_event(True, "first"), _EV_ASSISTANT,
        _result_event(False, "second"), _EV_EPILOGUE_TASK,
    ],
    # (b) result가 전혀 없는 stream
    "no_result": [_EV_INIT, _EV_ASSISTANT, _EV_EPILOGUE_BG],
    # (c) result 뒤 미종료 작업이 남은 stream
    "unfinished_after_result": [
        _EV_INIT, _EV_ASSISTANT, _result_event(False, "done"), _EV_UNFINISHED,
    ],
    # (c') (c)의 대조군 — 131 형태의 allowlist epilogue만 뒤따르는 정상 framing.
    #      (c)의 단언이 "무조건 error"가 아님을 같은 실행 경로로 증명한다.
    "clean_framing_after_result": [
        _EV_INIT, _EV_ASSISTANT, _result_event(False, "done"), _EV_EPILOGUE_SYS_BG,
    ],
}


# ─── 공통 실행 헬퍼 ─────────────────────────────────────────────────────────

def _write_stub(directory: pathlib.Path, source: str, name: str) -> pathlib.Path:
    path = directory / name
    path.write_text(source, encoding="utf-8")
    path.chmod(0o755)
    return path


class _AgentRun:
    """opal-agent 1회 실행 결과 (OPPL §결과 파일 규약 3-분리 캡처)."""

    def __init__(self, exitcode, stdout, stderr, wall_s, timed_out_by_guard):
        self.exitcode = exitcode
        self.stdout = stdout
        self.stderr = stderr
        self.wall_s = wall_s
        self.timed_out_by_guard = timed_out_by_guard


def _run_agent(stub: pathlib.Path, display: str, workdir: pathlib.Path,
               env_extra: dict, timeout: int = _AGENT_TIMEOUT,
               extra_args=None) -> _AgentRun:
    cmd = [
        sys.executable, str(_AGENT_PY),
        "--provider", "claude",
        "--opal-bootstrap", "off",
        "--timeout", str(timeout),
        "--cwd", str(workdir),
        "--bin", str(stub),
        *(extra_args or []),
        display,
        "[WORKER] attempt runtime probe",
    ]
    env = {k: v for k, v in os.environ.items()
           if k not in (_PROBE_ENV, _STREAM_FIXTURE_ENV)}
    env.update(env_extra)

    started = time.monotonic()
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=str(workdir), env=env, start_new_session=True,
    )
    guard_hit = False
    try:
        out, err = proc.communicate(timeout=_GUARD)
    except subprocess.TimeoutExpired:
        guard_hit = True
        # opal-agent가 deadline을 집행하지 못했다 — 테스트 하네스가 정리한다.
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            proc.kill()
        out, err = proc.communicate()
    return _AgentRun(
        exitcode=proc.returncode,
        stdout=(out or b"").decode("utf-8", "replace"),
        stderr=(err or b"").decode("utf-8", "replace"),
        wall_s=time.monotonic() - started,
        timed_out_by_guard=guard_hit,
    )


def _alive(pid) -> bool:
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _kill_tree(probe: dict) -> None:
    for key in ("grandchild_pid", "child_pid"):
        pid = probe.get(key)
        if pid and _alive(pid):
            try:
                os.kill(int(pid), signal.SIGKILL)
            except OSError:
                pass


def _wait_probe(path: pathlib.Path, limit: float = 10.0) -> dict:
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        time.sleep(0.05)
    raise AssertionError(f"stub probe 파일이 생성되지 않았다: {path}")


def _sink_args(run_dir: pathlib.Path, attempt: str | None = None) -> list[str]:
    """attempt 산출물 writer 소유권을 넘기는 CLI 인자(131 계약)."""
    args = ["--run-dir", str(run_dir), "--phase", _ATTEMPT_PHASE]
    if attempt:
        args += ["--attempt", attempt]
    return args


def _record_path(run_dir: pathlib.Path, attempt: str | None = None) -> pathlib.Path:
    stem = f"{_ATTEMPT_PHASE}.{attempt}" if attempt else _ATTEMPT_PHASE
    return run_dir / f"{stem}.attempt.json"


def _read_record(case: unittest.TestCase, run_dir: pathlib.Path,
                 attempt: str | None = None) -> dict:
    path = _record_path(run_dir, attempt)
    case.assertTrue(
        path.is_file(),
        f"attempt record가 계약 경로에 없다: {path} "
        f"(실제: {sorted(p.name for p in run_dir.rglob('*'))})",
    )
    record = json.loads(path.read_text(encoding="utf-8"))
    for key in _ATTEMPT_RECORD_KEYS:
        case.assertIn(key, record, f"attempt record에 {key}가 없다")
    return record


class _SilentTreeCase(unittest.TestCase):
    """무출력 자식·손자 트리를 띄우는 S-2 공통 셋업."""

    display = "--json"
    sink = False        # True면 opal-agent가 attempt 산출물 writer가 된다

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.work = pathlib.Path(self._tmp.name)
        self.run_dir = self.work / ".opal-runs" / "run-s2"
        self.run_dir.mkdir(parents=True)
        self.probe_path = self.work / "probe.json"
        self.stub = _write_stub(self.work, _STUB_SILENT_TREE, "stub_silent_tree.py")
        self.probe = None

    def tearDown(self):
        if self.probe:
            _kill_tree(self.probe)
        self._tmp.cleanup()

    def execute(self):
        run = _run_agent(
            self.stub, self.display, self.work,
            {_PROBE_ENV: str(self.probe_path)},
            extra_args=_sink_args(self.run_dir) if self.sink else None,
        )
        self.probe = _wait_probe(self.probe_path)
        return run


# ─── S-2 ────────────────────────────────────────────────────────────────────

class TestS2ProcessGroupCreated(_SilentTreeCase):
    """S-2 RED. sync·stream 두 경로 모두 자식을 새 process group의 리더로 띄운다.

    현행 구현은 `start_new_session`/`preexec_fn` 없이 subprocess.run / Popen을 쓰므로
    자식이 opal-agent와 같은 PGID를 상속한다 (opal_agent.py:665-691, 694-732).
    """

    def _assert_new_group(self):
        self.execute()
        self.assertEqual(
            self.probe["child_pgid"], self.probe["child_pid"],
            "provider 자식이 새 process group의 리더가 아니다 — "
            f"pgid={self.probe['child_pgid']} pid={self.probe['child_pid']} "
            "(start_new_session 미적용)",
        )
        self.assertEqual(
            self.probe["child_sid"], self.probe["child_pid"],
            "provider 자식이 새 session leader가 아니다",
        )

    def test_sync_path_creates_new_process_group(self):
        self.display = "--json"
        self._assert_new_group()

    def test_stream_path_creates_new_process_group(self):
        self.display = "--stream"
        self._assert_new_group()


class TestS2SilentWatchdog(_SilentTreeCase):
    """S-2 RED. stdout을 한 줄도 내지 않아도 deadline이 집행된다.

    현행 `_run_stream`은 deadline을 stdout 줄 수신 루프 안에서만 확인하므로
    (opal_agent.py:709-721) 무출력 자식에서는 영원히 발화하지 않는다.
    """

    def _assert_deadline_enforced(self):
        run = self.execute()
        self.assertFalse(
            run.timed_out_by_guard,
            f"--timeout {_AGENT_TIMEOUT}초가 집행되지 않아 하네스가 {_GUARD}초 뒤 "
            f"강제 종료했다 (display={self.display}) — 독립 watchdog 부재",
        )
        self.assertLess(
            run.wall_s, _AGENT_TIMEOUT + _REAP_GRACE + 2,
            f"deadline 집행이 지연됐다: {run.wall_s:.1f}s",
        )
        self.assertEqual(run.stdout, "", "무출력 경로인데 stdout이 비어 있지 않다")
        self.assertNotEqual(run.exitcode, 0, "timeout인데 성공 종료했다")
        self.assertIn("초과", run.stderr, f"timeout 사유가 stderr에 없다: {run.stderr!r}")

    def test_sync_path_enforces_deadline_without_any_output(self):
        self.display = "--json"
        self._assert_deadline_enforced()

    def test_stream_path_enforces_deadline_without_any_output(self):
        self.display = "--stream"
        self._assert_deadline_enforced()


class TestS2PgidReclaimNoOrphans(_SilentTreeCase):
    """S-2 RED. deadline 집행 시 PGID 전체가 회수되어 고아 프로세스가 0이다.

    현행 sync 경로는 subprocess.run의 timeout 처리로 직계 자식 1개만 kill하므로
    손자가 init에 재양육되어 고아로 남는다.
    """

    def _assert_no_orphans(self):
        run = self.execute()
        # 하네스가 killpg로 정리해 버리면 "고아 0"이 거짓 green이 된다 —
        # 회수 주체가 opal-agent였음을 먼저 못박는다.
        self.assertFalse(
            run.timed_out_by_guard,
            f"opal-agent가 deadline을 집행하지 못해 테스트 하네스가 PGID를 회수했다 "
            f"(display={self.display}) — 회수 주체가 opal-agent가 아니다",
        )
        deadline = time.monotonic() + _REAP_GRACE
        while time.monotonic() < deadline:
            if not _alive(self.probe["child_pid"]) and not _alive(self.probe["grandchild_pid"]):
                break
            time.sleep(0.1)
        survivors = {
            name: pid for name, pid in (
                ("child", self.probe["child_pid"]),
                ("grandchild", self.probe["grandchild_pid"]),
            ) if _alive(pid)
        }
        self.assertEqual(
            survivors, {},
            f"PGID 회수 실패 — 고아 프로세스 잔존 {survivors} (display={self.display})",
        )

    def test_sync_path_reclaims_whole_process_group(self):
        self.display = "--json"
        self._assert_no_orphans()

    def test_stream_path_reclaims_whole_process_group(self):
        self.display = "--stream"
        self._assert_no_orphans()


class TestS2AttemptRecordExitReason(_SilentTreeCase):
    """S-2. deadline 집행 사유·PID·PGID가 attempt record에 기록된다(131 스키마).

    132 RED가 가정한 `exit_reason` 단일 키는 폐기됐다 — 131은 같은 사실을
    `status`·`exit_class`·`timeout_reason`로 나눠 기록한다. 검증 의도(무엇이
    프로세스를 죽였는지와 무엇을 죽였는지가 record에 남는다)는 그대로다.
    """

    sink = True

    def test_timeout_reason_is_recorded_with_pid_and_pgid(self):
        self.display = "--json"
        run = self.execute()
        self.assertFalse(
            run.timed_out_by_guard,
            "opal-agent가 deadline을 집행하지 못해 하네스가 정리했다 — record 판정 불가",
        )
        record = _read_record(self, self.run_dir)

        # (1) 종료 사유 — watchdog hard deadline이 집행했다.
        self.assertEqual(
            record["status"], "timed_out",
            f"종료 상태가 timed_out이 아니다: {record['status']!r}",
        )
        self.assertEqual(
            record["exit_class"], "timed_out",
            f"exit_class가 timed_out이 아니다: {record['exit_class']!r}",
        )
        self.assertEqual(
            record["timeout_reason"], "hard",
            f"hard deadline 집행이 timeout_reason에 남지 않았다: "
            f"{record['timeout_reason']!r}",
        )
        self.assertIs(
            record["heartbeat"]["expired"], False,
            "sync 경로인데 heartbeat 만료로 기록됐다",
        )
        self.assertNotEqual(
            record["exit_code"], 0, "timeout 회수인데 exit_code가 0이다",
        )

        # (2) 무엇을 죽였는지 — 실제 자식 프로세스의 PID·PGID가 기록된다.
        self.assertEqual(
            record["pid"], self.probe["child_pid"],
            "record의 pid가 실제 provider 자식 pid와 다르다",
        )
        self.assertEqual(
            record["pgid"], self.probe["child_pgid"],
            "record의 pgid가 실제 provider 자식 pgid와 다르다",
        )
        self.assertIs(
            record["pgid_reclaimed"], True,
            "PGID 회수 완료가 record에 기록되지 않았다 — 고아 잔존 가능",
        )

        # (3) timeout이므로 소비 가능한 terminal result가 없다.
        self.assertIsNone(record["terminal"])
        self.assertEqual(record["unterminated_children"], [])

    def test_no_partial_attempt_record_after_timeout(self):
        """원자 저장 — timeout 회수 중에도 중간 산출물(.tmp/.partial)이 남지 않는다."""
        self.display = "--json"
        self.execute()
        leftovers = sorted(
            p.name for p in self.run_dir.rglob("*")
            if p.is_file() and (p.suffix in (".tmp", ".partial")
                                or p.name.startswith("."))
        )
        self.assertEqual(leftovers, [], f"원자 저장 잔여 파일: {leftovers}")
        # 완결된 JSON만 남는다 — 부분 기록이면 여기서 깨진다.
        _read_record(self, self.run_dir)


# ─── S-3 ────────────────────────────────────────────────────────────────────

class TestS3TerminalFraming(unittest.TestCase):
    """S-3. stream terminal framing — 마지막 result 채택 + epilogue allowlist.

    RED: `test_allowlisted_epilogue_after_result_is_not_a_failure`,
         `test_error_result_is_adopted_even_with_epilogue`,
         `test_last_result_wins_when_two_results_appear`.
         현행 `_last_stream_result`는 stdout의 **마지막 비어있지 않은 줄**만 보고
         `type == "result"`가 아니면 무조건 에러로 만든다 (opal_agent.py:538-558).
    회귀 guard(현재도 green, 구현 후에도 green이어야 함):
         `test_stream_without_result_is_never_success`,
         `test_unfinished_work_after_result_is_never_success`.
         allowlist를 과도하게 넓히면 이 둘이 깨진다.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.work = pathlib.Path(self._tmp.name)
        self.stub = _write_stub(self.work, _STUB_STREAM_REPLAY, "stub_stream.py")

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, fixture: str, run_dir: pathlib.Path | None = None) -> _AgentRun:
        """fixture를 stream으로 재생한다.

        run_dir을 주면 opal-agent가 attempt 산출물 writer가 되어 framing 판정이
        `<run_dir>/<phase>.attempt.json`에 기록된다(헤더 §확정 계약 1·4).
        주지 않으면 기존 passthrough 경로 그대로다(C-8).
        """
        path = self.work / f"{fixture}.jsonl"
        path.write_text("\n".join(_FIXTURES[fixture]) + "\n", encoding="utf-8")
        run = _run_agent(
            self.stub, "--stream", self.work,
            {_STREAM_FIXTURE_ENV: str(path)}, timeout=30,
            extra_args=_sink_args(run_dir) if run_dir else None,
        )
        self.assertFalse(run.timed_out_by_guard, "stream replay가 종료하지 않았다")
        return run

    def _passthrough_intact(self, run: _AgentRun, fixture: str):
        emitted = [ln for ln in run.stdout.splitlines() if ln.strip()]
        self.assertEqual(
            emitted, _FIXTURES[fixture],
            "stream passthrough가 원본 JSONL과 다르다 — OPPL .events.jsonl 계약 위반",
        )

    def test_allowlisted_epilogue_after_result_is_not_a_failure(self):
        run = self._run("epilogue_after_result")
        self._passthrough_intact(run, "epilogue_after_result")
        self.assertEqual(
            run.exitcode, 0,
            "성공 result 뒤 allowlist epilogue(background_tasks_changed·task_updated)를 "
            f"실패로 오판했다. stderr={run.stderr.strip()!r}",
        )

    def test_error_result_is_adopted_even_with_epilogue(self):
        run = self._run("epilogue_after_error_result")
        self.assertEqual(
            run.exitcode, 1,
            "is_error=true인 result가 채택되지 않았다 (epilogue에 가려짐). "
            f"exit={run.exitcode} stderr={run.stderr.strip()!r}",
        )

    def test_last_result_wins_when_two_results_appear(self):
        run = self._run("two_results_last_wins")
        self.assertEqual(
            run.exitcode, 0,
            "마지막 result(is_error=false)가 아니라 앞선 result가 채택됐다. "
            f"exit={run.exitcode} stderr={run.stderr.strip()!r}",
        )

    def test_stream_without_result_is_never_success(self):
        run = self._run("no_result")
        self.assertNotEqual(run.exitcode, 0, "result가 없는 stream을 성공으로 처리했다")
        self._passthrough_intact(run, "no_result")

    def test_unfinished_work_after_result_is_never_success(self):
        """result 뒤 미종료 작업이 남은 stream은 결코 성공으로 판정되지 않는다.

        [W-2 ③ 정합] 판정 채널은 프로세스 종료 코드가 아니라 attempt record다.
        131은 종료 코드를 D6 (b)(c)대로 동결하고(정상 0 / `is_error` 1 / 실행 오류 2),
        framing 판정은 `analyze_stream`의 `StreamVerdict`가 만들어 record의
        `status`·`exit_class`·`unterminated_children`으로 낸다
        (README §stream terminal framing 5). 따라서 "성공으로 처리하지 않는다"는
        record가 `done`/`ok`가 **아님**으로 단언한다 — 단언 강도는 낮추지 않는다.
        """
        run_dir = self.work / ".opal-runs" / "unfinished"
        run_dir.mkdir(parents=True)
        self._run("unfinished_after_result", run_dir=run_dir)
        record = _read_record(self, run_dir)

        self.assertNotEqual(
            record["status"], "done",
            "result 뒤 미종료 작업(background_task_started)이 남았는데 done으로 판정했다 "
            "— epilogue allowlist가 과도하게 넓다",
        )
        self.assertNotEqual(
            record["exit_class"], "ok",
            "미종료 작업이 남은 stream을 exit_class=ok로 판정했다",
        )
        self.assertEqual(
            record["exit_class"], "framing_error",
            f"framing 위반이 framing_error로 분류되지 않았다: {record['exit_class']!r}",
        )

        # 대조군 — 같은 실행 경로에서 정상 framing은 done/ok로 판정된다.
        # (이 단언이 없으면 위 단언은 "어떤 stream이든 error"로도 통과한다.)
        clean_dir = self.work / ".opal-runs" / "clean"
        clean_dir.mkdir(parents=True)
        self._run("clean_framing_after_result", run_dir=clean_dir)
        clean = _read_record(self, clean_dir)
        self.assertEqual(
            clean["status"], "done",
            f"정상 framing stream이 done으로 판정되지 않았다: {clean['status']!r}",
        )
        self.assertEqual(clean["exit_class"], "ok")


if __name__ == "__main__":
    unittest.main()
