"""
@header {
  "module": "test_oppl_compat",
  "layer": "test",
  "domain": "opal-tools",
  "description": "TASK 132 W-2 / S-1. OPPL 하위 호환 회귀 스위트. PLAN §Decisions D6의 (a) 공개 시그니처 무변경, (b) CLI 플래그 집합 무변경, (c) 동일 입력에서 .result.json/.events.jsonl/.err.log/.exitcode 4종 바이트 동일, (d) 응답 5필드 의미·타입 무변경을 golden 비교로 고정한다. mock/patch 미사용 — opal_agent.py를 실제 subprocess로 실행하고 provider CLI만 결정론 stub 프로세스로 대체한다.",
  "task": "132",
  "scenarios": ["S-1"],
  "exports": [
    "TestD6aPublicSignatures", "TestD6bCliFlagSet", "TestD6cGoldenBytes",
    "TestD6dResponseFields", "TestAttemptRecordIsAdditive"
  ]
}

# 인용 규칙
# - TEST-SCENARIO.md(132) S-1 ↔ PLAN.md(132) §Decisions and contracts D6, §Risks H-1.
# - [MUST] harness/red-first.md §2 작성자≠구현자: 이 파일은 opal-test-agent(RED)가 작성한다.
#   opal_agent.py(W-1)는 절대 수정하지 않으며, GREEN 구현 중 이 파일도 수정하지 않는다.
# - [MUST] PLAN H-6: 공개 CLI 계약과 파일 계약 수준에서만 검증한다. 미확정 내부 함수는 import하지 않는다.
#   (D6 (a)가 명시적으로 동결한 4개 공개 심볼만 예외적으로 introspection 대상이다.)
# - [MUST] PLAN W-2 "mock 금지, 실제 프로세스만": unittest.mock을 import하지 않는다.
# - 표준 라이브러리만 사용 (pytest는 러너로만 쓴다).

===============================================================================
golden 수집 방법 (재현 절차) — S-1 "변경 전 HEAD에서 먼저 수집" 요건
===============================================================================

golden 4종은 W-1이 opal_agent.py에 손대기 전 HEAD에서 수집했고
`tests/golden/oppl_compat/` 아래에 커밋되어 있다. 재수집은 아래로 한다:

    python3 opal/tools/opal-agent/tests/test_oppl_compat.py --regen-golden

실제 외부 모델 호출을 하지 않고 재현하기 위해, provider CLI 자리에
**고정 출력 stub 프로세스**를 `--bin <stub>` 공개 플래그로 주입한다.
`--bin`은 D6 (b)가 동결한 플래그 집합 밖의 기존 공개 플래그이며,
`shutil.which(<절대경로>)`가 그대로 해석하므로 opal_agent.py의 실행 경로
(build_invocation → subprocess.run / Popen → parse_result → main의 stdout dump)
전체가 실제로 동작한다. 대체되는 것은 모델 호출 한 지점뿐이다.

stub 본문은 이 파일 안의 `_STUB_SUCCESS_JSON` / `_STUB_SUCCESS_STREAM` /
`_STUB_SILENT_HANG` 상수가 SSOT다. golden은 이 상수와 `_INVOCATIONS`의
플래그 조합에 1:1로 대응하므로, 상수를 바꾸면 golden도 함께 재수집해야 한다.

수집 축 (OPPL AGENT.md §결과 파일 규약의 동기 축·비동기 축을 그대로 재현):
  - sync_json_success  : `--json`  정상 종료 → .result.json  / .err.log / .exitcode
  - stream_success     : `--stream` 정상 종료 → .events.jsonl / .err.log / .exitcode
  - sync_json_timeout  : `--json`  timeout   → .result.json  / .err.log / .exitcode

바이트 비교 제외 목록과 이유
---------------------------
1. 제외 필드: **없음**. `duration_ms`·`total_cost_usd`·`session_id`는 실제
   provider 호출에서는 비결정적이지만, stub이 고정 리터럴을 내보내므로 이
   스위트 안에서는 완전히 결정론적이다. 따라서 세 필드를 포함한 전 바이트를
   비교한다 — H-1(watchdog이 출력·종료코드를 흔드는 회귀)은 바로 이
   전(全)바이트 비교로만 잡힌다.
2. 제외 **축**: stream 경로의 timeout golden은 수집하지 않는다. 현행
   `_run_stream`은 deadline을 stdout 줄 수신 루프 안에서만 확인하므로
   (opal_agent.py:694-732) timeout이 발화하려면 줄이 계속 흘러야 하고,
   그 경우 `.events.jsonl`의 줄 수가 타이밍 의존이라 바이트 고정이 불가능하다.
   이 축의 회귀는 S-2(`test_opal_agent_attempt.py`)가 줄 수가 아니라
   deadline 집행·PGID 회수·종료 사유로 판정한다.
3. `--cwd`로 넘기는 임시 디렉토리 경로는 출력 4종 어디에도 나타나지 않으므로
   경로 정규화가 필요 없다. (stub이 인자를 무시하기 때문)

RED / 회귀 baseline 구분
-----------------------
- `TestD6aPublicSignatures` / `TestD6bCliFlagSet` / `TestD6cGoldenBytes` /
  `TestD6dResponseFields` 는 **회귀 baseline**이다. 변경 전 HEAD에서 이미
  green이며, W-1 이후에도 green이어야 한다(H-1 게이트).
- `TestAttemptRecordIsAdditive` 는 **RED**다. D6이 "attempt record는 4종을
  대체하지 않고 run root에 추가로 원자 저장하는 신규 파일"이라고 규정했으나
  현행 opal_agent.py에는 attempt record writer가 존재하지 않는다
  (ANALYSIS Q1 실측). W-1 구현 후에만 green이 된다.
"""

import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

_TESTS_DIR = pathlib.Path(__file__).resolve().parent
_TOOL_DIR = _TESTS_DIR.parent
_AGENT_PY = _TOOL_DIR / "opal_agent.py"
_GOLDEN_DIR = _TESTS_DIR / "golden" / "oppl_compat"

sys.path.insert(0, str(_TOOL_DIR))
import opal_agent as OA  # noqa: E402

# run root 파일 계약 (PLAN W-1 "attempt record를 run root에 원자 저장").
# run root는 `<allocator_root>/.opal-runs/<run_id>/`이며 opal-agent는 CLI 플래그
# 집합을 바꾸지 않고(D6 b) 이 경로를 전달받아야 하므로, 환경변수 채널을 계약으로 둔다.
_RUN_ROOT_ENV = "OPAL_AGENT_RUN_ROOT"

# ─── 결정론 stub provider ────────────────────────────────────────────────────
# 모든 stub은 인자를 전부 무시하고 고정 바이트만 내보낸다.

_STUB_SUCCESS_JSON = """#!/usr/bin/env python3
import sys
sys.stdout.write(
    '{"type":"result","subtype":"success","is_error":false,'
    '"result":"OPPL compat golden fixture.",'
    '"session_id":"00000000-0000-4000-8000-000000000001",'
    '"total_cost_usd":0.0123,"duration_ms":4242,"num_turns":1}'
)
sys.exit(0)
"""

_STUB_SUCCESS_STREAM = """#!/usr/bin/env python3
import sys
for line in (
    '{"type":"system","subtype":"init","session_id":"00000000-0000-4000-8000-000000000001"}',
    '{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"hi"}]}}',
    '{"type":"result","subtype":"success","is_error":false,'
    '"result":"OPPL compat golden fixture.",'
    '"session_id":"00000000-0000-4000-8000-000000000001",'
    '"total_cost_usd":0.0123,"duration_ms":4242,"num_turns":1}',
):
    sys.stdout.write(line + "\\n")
    sys.stdout.flush()
sys.exit(0)
"""

_STUB_SILENT_HANG = """#!/usr/bin/env python3
import time
time.sleep(120)
"""

_GOLDEN_PROMPT = "[GOLDEN] opal-agent OPPL compat fixture prompt."

# 축 이름 -> (stub 소스, 추가 플래그, stdout 파일명)
_INVOCATIONS = {
    "sync_json_success": (_STUB_SUCCESS_JSON, ["--json", "--timeout", "300"], "result.json"),
    "stream_success": (_STUB_SUCCESS_STREAM, ["--stream", "--timeout", "300"], "events.jsonl"),
    "sync_json_timeout": (_STUB_SILENT_HANG, ["--json", "--timeout", "1"], "result.json"),
}


def _write_stub(directory: pathlib.Path, source: str) -> pathlib.Path:
    path = directory / "stub_provider.py"
    path.write_text(source, encoding="utf-8")
    path.chmod(0o755)
    return path


def _run_axis(axis: str, workdir: pathlib.Path, extra_env=None) -> dict[str, bytes]:
    """OPPL AGENT.md §결과 파일 규약과 동일한 3-분리 캡처로 한 축을 실행한다.

    `run.sh`가 하는 일은 `exec <python> opal_agent.py "$@"` 뿐이므로
    (opal/tools/opal-agent/run.sh), 워크트리 소스를 같은 형태로 실행한다.
    호출측 셸의 `> f 2> g; echo $? > h` 리다이렉트를 파일 핸들로 재현한다.
    """
    stub_src, flags, stdout_name = _INVOCATIONS[axis]
    stub = _write_stub(workdir, stub_src)
    cwd = workdir / "cwd"
    cwd.mkdir(exist_ok=True)

    out_path = workdir / stdout_name
    err_path = workdir / "err.log"
    code_path = workdir / "exitcode"

    cmd = [
        sys.executable, str(_AGENT_PY),
        "--provider", "claude",
        "--opal-bootstrap", "off",
        "--model", "golden-fixed-model",
        "--allowed-tools", "Read,Bash",
        "--cwd", str(cwd),
        "--bin", str(stub),
        *flags,
        _GOLDEN_PROMPT,
    ]
    env = {k: v for k, v in os.environ.items() if k != _RUN_ROOT_ENV}
    if extra_env:
        env.update(extra_env)

    with out_path.open("wb") as fout, err_path.open("wb") as ferr:
        code = subprocess.call(cmd, stdout=fout, stderr=ferr, cwd=str(cwd), env=env)
    code_path.write_bytes(f"{code}\n".encode("utf-8"))

    return {
        stdout_name: out_path.read_bytes(),
        "err.log": err_path.read_bytes(),
        "exitcode": code_path.read_bytes(),
    }


def _regen_golden() -> None:
    for axis in _INVOCATIONS:
        target = _GOLDEN_DIR / axis
        target.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            captured = _run_axis(axis, pathlib.Path(tmp))
        for name, data in captured.items():
            (target / name).write_bytes(data)
        print(f"[golden] {axis}: {', '.join(sorted(captured))}")


# ─── D6 (a) 공개 시그니처 무변경 ─────────────────────────────────────────────

class TestD6aPublicSignatures(unittest.TestCase):
    """S-1 / D6 (a). 회귀 baseline — HEAD에서 green, W-1 이후에도 green이어야 한다."""

    def test_call_agent_signature_is_frozen(self):
        import inspect
        sig = inspect.signature(OA.call_agent)
        params = list(sig.parameters)
        self.assertEqual(params[0], "prompt")
        self.assertEqual(
            params[1:],
            [
                "provider", "system_prompt", "allowed_tools", "model", "effort",
                "cwd", "timeout", "session_id", "new_session_id", "output_format",
                "bin", "opal_bootstrap",
            ],
        )
        defaults = {
            name: p.default for name, p in sig.parameters.items()
            if p.default is not inspect.Parameter.empty
        }
        self.assertEqual(defaults["provider"], "claude")
        self.assertEqual(defaults["timeout"], 300)
        self.assertEqual(defaults["output_format"], "json")
        self.assertEqual(defaults["opal_bootstrap"], "on")
        for name in ("provider", "timeout", "output_format", "opal_bootstrap"):
            self.assertEqual(
                sig.parameters[name].kind, inspect.Parameter.KEYWORD_ONLY,
                f"{name}은 keyword-only 계약이다",
            )

    def test_agent_config_fields_are_frozen(self):
        import dataclasses
        names = [f.name for f in dataclasses.fields(OA.AgentConfig)]
        for required in (
            "prompt", "provider", "system_prompt", "allowed_tools", "model",
            "effort", "cwd", "timeout", "session_id", "new_session_id",
            "output_format", "bin", "opal_bootstrap",
        ):
            self.assertIn(required, names, f"AgentConfig.{required} 제거는 하위 호환 파괴다")

    def test_agent_result_fields_are_frozen(self):
        import dataclasses
        names = [f.name for f in dataclasses.fields(OA.AgentResult)]
        for required in (
            "text", "provider", "session_id", "is_error", "cost_usd",
            "duration_ms", "raw",
        ):
            self.assertIn(required, names, f"AgentResult.{required} 제거는 하위 호환 파괴다")

    def test_resolve_session_event_signature_is_frozen(self):
        import inspect
        sig = inspect.signature(OA.resolve_session_event)
        self.assertEqual(
            list(sig.parameters)[:3],
            ["prompt", "bootstrap_enabled", "project_detected"],
        )
        self.assertEqual(
            OA.resolve_session_event("[WORKER]\nx", bootstrap_enabled=True,
                                     project_detected=True),
            "session.worker",
        )


# ─── D6 (b) CLI 플래그 집합 무변경 ───────────────────────────────────────────

class TestD6bCliFlagSet(unittest.TestCase):
    """S-1 / D6 (b). 회귀 baseline."""

    FROZEN_FLAGS = (
        "--provider", "--model", "--effort", "--timeout",
        "--resume", "--session-id", "--opal-bootstrap",
        "--json", "--text", "--stream",
    )

    def _help_text(self) -> str:
        proc = subprocess.run(
            [sys.executable, str(_AGENT_PY), "--help"],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout

    def test_frozen_flags_present_in_public_cli(self):
        help_text = self._help_text()
        for flag in self.FROZEN_FLAGS:
            self.assertRegex(
                help_text, re.escape(flag) + r"(?![\w-])",
                f"{flag}가 CLI에서 사라졌다 — OPPL 호출 형태가 깨진다",
            )

    def test_frozen_flag_destinations_and_defaults(self):
        parser = OA._build_parser()
        opts = {}
        for action in parser._actions:
            for s in action.option_strings:
                opts[s] = action
        for flag in self.FROZEN_FLAGS:
            self.assertIn(flag, opts, f"{flag} 미존재")
        self.assertEqual(opts["--resume"].dest, "session_id")
        self.assertEqual(opts["--session-id"].dest, "new_session_id")
        self.assertEqual(opts["--timeout"].default, 300)
        self.assertEqual(opts["--timeout"].type, int)
        for flag in ("--json", "--text", "--stream"):
            self.assertEqual(opts[flag].dest, "display")
        self.assertEqual(opts["--json"].const, "json")
        self.assertEqual(opts["--text"].const, "text")
        self.assertEqual(opts["--stream"].const, "stream")
        self.assertEqual(
            tuple(opts["--opal-bootstrap"].choices), ("on", "assistant", "off")
        )

    def test_resume_and_session_id_stay_mutually_exclusive(self):
        proc = subprocess.run(
            [sys.executable, str(_AGENT_PY), "--resume", "a", "--session-id", "b", "p"],
            capture_output=True, text=True, timeout=60,
        )
        self.assertNotEqual(proc.returncode, 0)


# ─── D6 (c) 4종 파일 바이트 동일성 ───────────────────────────────────────────

class _GoldenAxisMixin:
    axis = ""

    def _compare(self):
        golden_dir = _GOLDEN_DIR / self.axis
        self.assertTrue(
            golden_dir.is_dir(),
            f"golden 미수집: {golden_dir} — `python3 {__file__} --regen-golden`은 "
            f"W-1 변경 전 HEAD에서만 실행해야 한다",
        )
        with tempfile.TemporaryDirectory() as tmp:
            actual = _run_axis(self.axis, pathlib.Path(tmp))
        expected_names = sorted(p.name for p in golden_dir.iterdir())
        self.assertEqual(sorted(actual), expected_names)
        for name in expected_names:
            want = (golden_dir / name).read_bytes()
            got = actual[name]
            self.assertEqual(
                got, want,
                f"[{self.axis}] {name} 바이트 불일치 (H-1 회귀)\n"
                f"golden={want!r}\nactual={got!r}",
            )


class TestD6cGoldenBytes(unittest.TestCase):
    """S-1 / D6 (c). 회귀 baseline — 정상 종료 경로와 timeout 경로 양쪽."""

    def test_sync_json_success_bytes_identical(self):
        self.axis = "sync_json_success"
        _GoldenAxisMixin._compare(self)

    def test_stream_success_bytes_identical(self):
        self.axis = "stream_success"
        _GoldenAxisMixin._compare(self)

    def test_sync_json_timeout_bytes_identical(self):
        self.axis = "sync_json_timeout"
        _GoldenAxisMixin._compare(self)

    def test_timeout_axis_keeps_oppl_completion_marker_contract(self):
        """OPPL은 `.exitcode` 파일 존재로 완료를 판정한다 (AGENT.md §결과 파일 규약).

        timeout 경로에서 exit code가 2가 아니거나 stderr가 비면 OPPL 완료 판정이 깨진다.
        """
        golden = _GOLDEN_DIR / "sync_json_timeout"
        self.assertEqual(golden.joinpath("exitcode").read_bytes(), b"2\n")
        self.assertTrue(golden.joinpath("err.log").read_bytes().strip())
        self.assertEqual(golden.joinpath("result.json").read_bytes(), b"")


# ─── D6 (d) 응답 5필드 의미·타입 무변경 ──────────────────────────────────────

class TestD6dResponseFields(unittest.TestCase):
    """S-1 / D6 (d). 회귀 baseline."""

    FIELDS = ("result", "session_id", "is_error", "total_cost_usd", "duration_ms")

    def _payload(self, axis: str) -> dict:
        raw = (_GOLDEN_DIR / axis / ("events.jsonl" if "stream" in axis else "result.json"))
        data = raw.read_bytes().decode("utf-8")
        if "stream" in axis:
            data = [ln for ln in data.splitlines() if ln.strip()][-1]
        return json.loads(data)

    def test_json_axis_exposes_five_fields_with_frozen_types(self):
        payload = self._payload("sync_json_success")
        for field in self.FIELDS:
            self.assertIn(field, payload, f"OPPL 소비 필드 {field} 누락")
        self.assertIsInstance(payload["result"], str)
        self.assertIsInstance(payload["session_id"], str)
        self.assertIsInstance(payload["is_error"], bool)
        self.assertIsInstance(payload["total_cost_usd"], float)
        self.assertIsInstance(payload["duration_ms"], int)

    def test_stream_axis_last_line_exposes_same_five_fields(self):
        payload = self._payload("stream_success")
        for field in self.FIELDS:
            self.assertIn(field, payload)
        self.assertEqual(payload["type"], "result")

    def test_field_semantics_survive_round_trip_through_call_agent(self):
        """raw dict가 그대로 보존되고 AgentResult 매핑 의미가 유지된다."""
        with tempfile.TemporaryDirectory() as tmp:
            stub = _write_stub(pathlib.Path(tmp), _STUB_SUCCESS_JSON)
            result = OA.call_agent(
                _GOLDEN_PROMPT, provider="claude", bin=str(stub),
                cwd=tmp, timeout=60, opal_bootstrap="off",
            )
        self.assertEqual(result.text, "OPPL compat golden fixture.")
        self.assertEqual(result.session_id, "00000000-0000-4000-8000-000000000001")
        self.assertIs(result.is_error, False)
        self.assertEqual(result.cost_usd, 0.0123)
        self.assertEqual(result.duration_ms, 4242)
        for field in self.FIELDS:
            self.assertIn(field, result.raw)


# ─── attempt record 가산성 (RED) ─────────────────────────────────────────────

class TestAttemptRecordIsAdditive(unittest.TestCase):
    """S-1 RED. D6: attempt record는 4종 파일을 대체하지 않고 run root에 '추가로' 저장된다.

    현행 opal_agent.py에는 attempt record writer가 없어 실패한다(ANALYSIS Q1 실측).
    W-1 구현 후 green이 되어야 하며, 그때에도 4종 바이트는 golden과 동일해야 한다.
    """

    def _attempt_records(self, run_root: pathlib.Path) -> list[pathlib.Path]:
        return [p for p in run_root.rglob("*.json") if p.is_file()]

    def test_attempt_record_written_without_changing_the_four_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = pathlib.Path(tmp)
            run_root = work / ".opal-runs" / "run-golden"
            run_root.mkdir(parents=True)
            actual = _run_axis(
                "sync_json_success", work,
                extra_env={_RUN_ROOT_ENV: str(run_root)},
            )
            records = self._attempt_records(run_root)

            golden_dir = _GOLDEN_DIR / "sync_json_success"
            for name, got in actual.items():
                self.assertEqual(
                    got, (golden_dir / name).read_bytes(),
                    f"attempt record 도입이 {name} 바이트를 바꿨다 — D6 (c) 위반",
                )

            self.assertTrue(
                records,
                f"{_RUN_ROOT_ENV}가 지정됐는데 run root에 attempt record가 없다",
            )
            record = json.loads(records[0].read_text(encoding="utf-8"))
            for key in ("attempt_id", "pid", "pgid", "exit_reason"):
                self.assertIn(key, record, f"attempt record에 {key}가 없다")
            self.assertEqual(record["exit_reason"], "completed")

    def test_attempt_record_write_is_atomic_no_partial_files_left(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = pathlib.Path(tmp)
            run_root = work / ".opal-runs" / "run-golden"
            run_root.mkdir(parents=True)
            _run_axis("sync_json_success", work,
                      extra_env={_RUN_ROOT_ENV: str(run_root)})
            leftovers = [
                p.name for p in run_root.rglob("*")
                if p.is_file() and (p.name.endswith(".tmp")
                                    or p.name.startswith(".")
                                    or p.suffix == ".partial")
            ]
            self.assertEqual(leftovers, [], f"원자 저장 잔여 파일: {leftovers}")
            records = self._attempt_records(run_root)
            self.assertTrue(records, "attempt record 미생성")
            json.loads(records[0].read_text(encoding="utf-8"))

    def test_no_run_root_env_means_no_side_effect_for_oppl(self):
        """OPPL은 run root를 지정하지 않는다 — 미지정 시 아무 파일도 늘지 않아야 한다."""
        with tempfile.TemporaryDirectory() as tmp:
            work = pathlib.Path(tmp)
            before = {p.name for p in work.rglob("*")}
            _run_axis("sync_json_success", work)
            after = {p.name for p in work.rglob("*")}
            unexpected = after - before - {
                "stub_provider.py", "cwd", "result.json", "err.log", "exitcode",
                "__pycache__",
            }
            self.assertEqual(unexpected, set(), f"예상 밖 산출물: {unexpected}")


if __name__ == "__main__":
    if "--regen-golden" in sys.argv:
        _regen_golden()
    else:
        unittest.main()
