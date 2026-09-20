"""
@header {
  "module": "test_agent_tool_adapter",
  "layer": "test",
  "domain": "opal-tools",
  "description": "adapter.pm-agent-tool 변환기(agent_tool_adapter.py) 계약 테스트 — TASK-147 W-6·W-13 / AC-1·AC-7 / TEST-SCENARIO S-19(설치 후 실디스패치)의 조각 실검사 대응분과 S-4와 같은 방식의 평문 0건 바이트 검사. 판정은 전부 공개 인터페이스 실호출이다 — 어댑터를 실제 프로세스로 띄워 stdin에 PostToolUse(matcher Agent|Task) 봉투를 넣고, 어댑터가 run-log-tool append CLI를 통해 tmp 캡슐(state-tool init --run-log-mode shadow)의 기록 조각에 남긴 산출물을 디스크에서 다시 읽어 판정한다(mock/patch 없음). 검사 축 7개 — ① 실제형 Agent의 구조화 toolUseResult terminal과 legacy Task 호출자 전사 terminal이 같은 A1 3사건(worker.started/activity/terminal)을 방출하고 actor.kind=worker ∧ provenance.type=adapter ∧ recorded_by.kind=adapter·id=변환기 식별자 ∧ source.{kind,id,sha256,observed_at}를 충족, ② §1.3 완료 알림 분해 금지 불변식(activity와 terminal의 source.id·sha256 상이, observed_at·timestamp 순서), ③ append의 recorded_by.id는 인자 미지정 시 actor_id로, 지정 시 지정값으로 기록, ④ AC-7 — 비밀값 4종과 원본 프롬프트를 심은 관측 원본으로 돌린 뒤 조각·state.json·커서 파일을 바이트 검색해 평문 0건, ⑤ 재실행 멱등(조각 바이트 불변), ⑥ 전 실패 경로 무출력 exit 0(훅이 세션을 막지 않는다), ⑦ 배포 배선 — claude-hooks.json의 PostToolUse(matcher Agent|Task) 1건 등재와 scripts/merge-hooks.py 멱등 upsert 2회 실행 결과 동일, install-mac.sh의 배포 확인 블록 존재, 그리고 플랫폼 고유 봉투 키·경로 문법이 어댑터 파일 밖(run_log_core.py·run_log_tool.py)에 새지 않음. 관측 원본 fixture는 실제 하네스 산출물의 **형식만** 복제해 런타임에 생성하며(키셋·경로 패턴·종료 알림 문법), 실제 전사 본문은 저장소에 두지 않는다(TASK C-5).",
  "exports": ["TestAppendRecordedBy", "TestAdapterEmission", "TestAdapterRedaction", "TestAdapterFailSafe",
              "TestAdapterDeploymentWiring"],
  "depends": ["agent_tool_adapter", "run_log_tool", "merge-hooks"]
}
"""

import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile
import time
import unittest

_TOOL_DIR = pathlib.Path(__file__).resolve().parent.parent
_ADAPTER_SRC = _TOOL_DIR / "adapters" / "agent_tool_adapter.py"
_RUN_LOG_RUN_SH = _TOOL_DIR / "run.sh"
_STATE_RUN_SH = _TOOL_DIR.parent / "state-tool" / "run.sh"
_REPO_ROOT = _TOOL_DIR.parent.parent.parent
_HOOKS_JSON = _REPO_ROOT / "opal" / "core" / "hooks" / "claude-hooks.json"
_INSTALL_SH = _REPO_ROOT / "scripts" / "install-mac.sh"
_MERGE_HOOKS = _REPO_ROOT / "scripts" / "merge-hooks.py"

_VENV_PYTHON = pathlib.Path(os.path.expanduser("~/.opal/.venv/bin/python"))

# 앰비언트 세션 식별자 의존을 배제한다 — 이 테스트는 주입한 봉투 값만으로 판정한다.
_AMBIENT_SESSION_VARS = ("OPAL_SESSION_ID", "CLAUDE_CODE_SESSION_ID", "CLAUDE_SESSION_ID")

# 비밀값 fixture 4종(S-4와 같은 구성) + 원본 프롬프트 본문 1종.
_SECRET_FIXTURES = {
    "env_var": "DB_PASSWORD=Sup3rSecretP@ssw0rd_9x!",
    "bearer": "Authorization: Bearer sk-live-ZZZTOPSECRETTOKEN0123456789",
    "api_key": "api_key=AKIAIOSFODNN7SECRETXX",
    "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEAsecret\n-----END RSA PRIVATE KEY-----",
}
_PROMPT_BODY = "[WORKER] W6-CANARY-PROMPT-BODY-DO-NOT-PERSIST 원본 프롬프트 본문"
_ASSISTANT_BODY = "W6-CANARY-ASSISTANT-OUTPUT-DO-NOT-PERSIST 어시스턴트 출력 본문"


def _clean_env():
    env = dict(os.environ)
    for name in _AMBIENT_SESSION_VARS:
        env.pop(name, None)
    return env


def _run_state_tool(args):
    return subprocess.run(["bash", str(_STATE_RUN_SH)] + args,
                          capture_output=True, text=True, env=_clean_env(), timeout=120)


def _run_run_log_tool(args):
    return subprocess.run(["bash", str(_RUN_LOG_RUN_SH)] + args,
                          capture_output=True, text=True, env=_clean_env(), timeout=120)


def _load_adapter():
    spec = importlib.util.spec_from_file_location("agent_tool_adapter_undertest", _ADAPTER_SRC)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_adapter(envelope):
    """어댑터를 실제 프로세스로 실행한다(훅과 같은 형태: stdin 봉투, 무인자)."""
    return subprocess.run([str(_VENV_PYTHON), str(_ADAPTER_SRC)],
                          input=json.dumps(envelope, ensure_ascii=False),
                          capture_output=True, text=True, env=_clean_env(), timeout=300)


def _segments(task_path):
    return sorted((pathlib.Path(task_path) / "run").glob("run-log-*-*.jsonl"))


def _records(task_path):
    out = []
    for seg in _segments(task_path):
        for line in seg.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(json.loads(line))
    return out


def _segment_bytes(task_path):
    return b"".join(seg.read_bytes() for seg in _segments(task_path))


class _Capsule:
    """tmp 태스크 캡슐 + 하네스 서브에이전트 실행 파일 3원천 fixture.

    경로 패턴·키셋·종료 알림 문법은 실제 하네스 산출물에서 관측한 형식을 복제한다
    (`{transcript}.jsonl`의 형제 `{transcript}/subagents/agent-<id>.meta.json`·`.jsonl`,
    호출자 전사의 `<task-notification>` 블록). 본문은 테스트 fixture 문자열이다.
    """

    def __init__(self, root, *, agent_id="atestagent0001", status="completed",
                 with_secrets=False, session_id="sess-adapter-0001"):
        self.root = pathlib.Path(root)
        self.agent_id = agent_id
        self.session_id = session_id
        self.task_path = self.root / "capsule"
        self.cwd = self.root / "worktree"
        self.task_path.mkdir(parents=True, exist_ok=True)
        (self.cwd / ".opal").mkdir(parents=True, exist_ok=True)

        result = _run_state_tool([
            "init", str(self.task_path), "--skill", "oppl", "--mode", "agentic",
            "--rows-spec", json.dumps([{"stage": "EXECUTE", "item": "W-6 adapter"}],
                                      ensure_ascii=False),
            "--run-log-mode", "shadow",
        ])
        if result.returncode != 0:
            raise AssertionError(f"tmp 캡슐 init 실패 — {result.stdout!r} {result.stderr!r}")

        # 발급값 사본(추론 금지 경로) — 어댑터는 여기서만 task_path를 읽는다.
        (self.cwd / ".opal" / "task-ownership.json").write_text(
            json.dumps({"task_path": str(self.task_path)}), encoding="utf-8")

        body = ""
        if with_secrets:
            body = " ".join([_PROMPT_BODY, _ASSISTANT_BODY, *_SECRET_FIXTURES.values()])

        proj = self.root / "projects"
        sub = proj / session_id / "subagents"
        sub.mkdir(parents=True, exist_ok=True)
        self.meta_path = sub / f"agent-{agent_id}.meta.json"
        self.log_path = sub / f"agent-{agent_id}.jsonl"
        self.transcript = proj / f"{session_id}.jsonl"

        self.meta_path.write_text(json.dumps({
            "agentType": "opal-be-agent",
            "description": "W-6 adapter fixture" + (" " + body if with_secrets else ""),
            "toolUseId": "toolu_adaptertest0001",
            "parentAgentId": None,
            "spawnDepth": 1,
            "requestShape": "background",
            "requestNonInteractive": True,
        }, ensure_ascii=False), encoding="utf-8")

        self.log_path.write_text("\n".join(
            json.dumps({
                "parentUuid": None if i == 0 else f"u{i}",
                "isSidechain": True,
                "agentId": agent_id,
                "type": "user" if i == 0 else "assistant",
                "message": {"role": "user" if i == 0 else "assistant",
                            "content": f"line {i} {body}"},
                "uuid": f"u{i + 1}",
                "timestamp": f"2026-09-19T14:0{i}:00.000Z",
            }, ensure_ascii=False) for i in range(3)) + "\n", encoding="utf-8")

        self.notification = (
            "<task-notification>\n"
            f"<task-id>{agent_id}</task-id>\n"
            "<tool-use-id>toolu_adaptertest0001</tool-use-id>\n"
            f"<output-file>{self.root}/out/{agent_id}.output</output-file>\n"
            f"<status>{status}</status>\n"
            f"<summary>Agent \"W-6 adapter fixture\" finished</summary>\n"
            f"<result>{body}</result>\n"
            "</task-notification>"
        )
        self.transcript.write_text(json.dumps(
            {"type": "user", "message": {"role": "user", "content": self.notification}},
            ensure_ascii=False) + "\n", encoding="utf-8")

        now = time.time()
        os.utime(self.meta_path, (now - 300, now - 300))
        os.utime(self.log_path, (now - 120, now - 120))

    def envelope(self, **overrides):
        payload = {
            "session_id": self.session_id,
            "transcript_path": str(self.transcript),
            "cwd": str(self.cwd),
            "hook_event_name": "PostToolUse",
            "tool_name": "Task",
            "tool_input": {"description": "W-6 adapter fixture",
                           "prompt": _PROMPT_BODY, "subagent_type": "opal-be-agent"},
            "tool_response": {"agentId": self.agent_id, "isAsync": True,
                              "status": "async_launched", "prompt": _PROMPT_BODY,
                              "description": "W-6 adapter fixture",
                              "outputFile": f"{self.root}/out/{self.agent_id}.output",
                              "resolvedModel": "opus", "canReadOutputFile": True},
        }
        payload.update(overrides)
        return payload

    def cursor_bytes(self):
        cursor_dir = self.cwd / ".opal" / "run" / ".runtime" / "agent-tool-adapter"
        if not cursor_dir.is_dir():
            return b""
        return b"".join(p.read_bytes() for p in sorted(cursor_dir.glob("*.json")))


# ─────────────────────────────────────────────────────────────────────────────
# ① A1 3사건 방출 + ② 완료 알림 분해 금지 불변식
# ─────────────────────────────────────────────────────────────────────────────
class TestAppendRecordedBy(unittest.TestCase):

    def test_default_and_explicit_recorded_by_id_are_persisted(self):
        """W-13/D-15 — CLI 기본값 보존과 명시적 제출 주체 식별자를 조각으로 판정한다."""
        with tempfile.TemporaryDirectory() as tmp:
            task_path = pathlib.Path(tmp) / "task"
            run_id = "run_recordedby"
            init = _run_run_log_tool([
                "init", "--task", str(task_path), "--run-id", run_id, "--format", "json",
            ])
            self.assertEqual(init.returncode, 0, init.stderr)

            common = [
                "append", "--task", str(task_path), "--run-id", run_id,
                "--event", "activity", "--actor-kind", "PM", "--actor-id", "pm-legacy",
                "--provenance-type", "direct", "--recorded-by-kind", "PM",
                "--summary", "recorded-by fixture", "--data", '{"kind":"progress"}',
                "--format", "json",
            ]
            default = _run_run_log_tool(common[:5] + ["--request-id", "req-default"] + common[5:])
            self.assertEqual(default.returncode, 0, default.stderr)
            explicit = _run_run_log_tool(
                common[:5] + ["--request-id", "req-explicit"] + common[5:]
                + ["--recorded-by-id", "recording-adapter"])
            self.assertEqual(explicit.returncode, 0, explicit.stderr)

            records = [record for record in _records(task_path) if record["event"] == "activity"]
            self.assertEqual([record["provenance"]["recorded_by"]["id"] for record in records],
                             ["pm-legacy", "recording-adapter"])


class TestAdapterEmission(unittest.TestCase):

    def test_emits_a1_started_activity_terminal(self):
        with tempfile.TemporaryDirectory() as tmp:
            capsule = _Capsule(tmp)
            proc = _run_adapter(capsule.envelope())
            self.assertEqual(proc.returncode, 0, f"어댑터 비정상 종료 — {proc.stderr!r}")

            records = [r for r in _records(capsule.task_path) if r["event"] != "run.started"]
            by_event = {}
            for rec in records:
                by_event.setdefault(rec["event"], []).append(rec)

            self.assertEqual(len(by_event.get("worker.started", [])), 1,
                             f"worker.started 1건이 아님 — {sorted(by_event)}")
            self.assertGreaterEqual(len(by_event.get("activity", [])), 1,
                                    f"activity 1건 이상이 아님 — {sorted(by_event)}")
            terminals = [r for r in records
                         if r["event"] in ("worker.completed", "worker.failed", "worker.blocked")]
            self.assertEqual(len(terminals), 1, f"terminal 1건이 아님 — {sorted(by_event)}")

            allowed_source_kinds = {"agent_handshake", "agent_message", "tool_result",
                                    "process_exit"}
            for rec in records:
                with self.subTest(event=rec["event"]):
                    self.assertEqual(rec["actor"]["kind"], "worker")
                    self.assertEqual(rec["provenance"]["type"], "adapter")
                    self.assertEqual(rec["provenance"]["recorded_by"]["kind"], "adapter")
                    self.assertEqual(rec["provenance"]["recorded_by"]["id"],
                                     _load_adapter().ADAPTER_ID)
                    source = rec["provenance"]["source"]
                    self.assertIn(source["kind"], allowed_source_kinds)
                    for field in ("id", "sha256", "observed_at"):
                        self.assertTrue(source.get(field),
                                        f"A1 필수 증거 source.{field} 결측 — {source}")
                    self.assertRegex(source["sha256"], r"^[0-9a-f]{64}$")
                    self.assertRegex(source["observed_at"],
                                     r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
                    self.assertTrue(rec["worker_run_id"])

            # worker.started의 source는 시작 메타 원본 해시 그대로여야 한다.
            self.assertEqual(
                by_event["worker.started"][0]["provenance"]["source"]["sha256"],
                hashlib.sha256(capsule.meta_path.read_bytes()).hexdigest())

    def test_agent_envelope_uses_the_same_a1_path_as_legacy_task(self):
        """S-19 회귀 — Claude Code 2.1.278 실측형 Agent 봉투도 A1 세 사건을 남긴다."""
        with tempfile.TemporaryDirectory() as tmp:
            capsule = _Capsule(tmp)
            capsule.transcript.write_text("", encoding="utf-8")
            structured_result = {
                "agentId": capsule.agent_id,
                "status": "completed",
                "prompt": _PROMPT_BODY,
                "content": " ".join([_ASSISTANT_BODY, *_SECRET_FIXTURES.values()]),
            }
            proc = _run_adapter(capsule.envelope(
                tool_name="Agent", tool_response=None,
                toolUseResult=structured_result,
            ))
            self.assertEqual(proc.returncode, 0, proc.stderr)

            records = [r for r in _records(capsule.task_path) if r["event"] != "run.started"]
            events = {r["event"] for r in records}
            self.assertIn("worker.started", events)
            self.assertIn("activity", events)
            terminals = [r for r in records if r["event"] in {
                "worker.completed", "worker.failed", "worker.blocked",
            }]
            self.assertEqual(len(terminals), 1)
            for record in records:
                with self.subTest(event=record["event"]):
                    self.assertEqual(record["actor"]["kind"], "worker")
                    self.assertEqual(record["provenance"]["type"], "adapter")
                    self.assertEqual(record["provenance"]["recorded_by"],
                                     {"kind": "adapter", "id": _load_adapter().ADAPTER_ID})
                    self.assertTrue(record["summary"].startswith("Agent adapter: "))
            terminal = terminals[0]
            expected_sha = hashlib.sha256(json.dumps(
                structured_result, ensure_ascii=False, sort_keys=True,
                separators=(",", ":")).encode("utf-8")).hexdigest()
            self.assertEqual(terminal["provenance"]["source"]["kind"], "tool_result")
            self.assertEqual(terminal["provenance"]["source"]["id"],
                             f"agent-tool-result:{capsule.agent_id}")
            self.assertEqual(terminal["provenance"]["source"]["sha256"], expected_sha)
            for blob in (_segment_bytes(capsule.task_path), capsule.cursor_bytes(),
                         (capsule.task_path / "state.json").read_bytes()):
                for needle in [*_SECRET_FIXTURES.values(), _PROMPT_BODY, _ASSISTANT_BODY]:
                    self.assertNotIn(needle.encode("utf-8"), blob)

    def test_agent_unknown_structured_status_does_not_create_a_terminal(self):
        with tempfile.TemporaryDirectory() as tmp:
            capsule = _Capsule(tmp)
            capsule.transcript.write_text("", encoding="utf-8")
            proc = _run_adapter(capsule.envelope(
                tool_name="Agent", tool_response=None,
                toolUseResult={"agentId": capsule.agent_id, "status": "future_status"},
            ))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            events = [r["event"] for r in _records(capsule.task_path)]
            self.assertIn("worker.started", events)
            self.assertIn("activity", events)
            self.assertFalse(set(events) & {"worker.completed", "worker.failed", "worker.blocked"})

    def test_activity_and_terminal_are_not_one_message_split(self):
        """§1.3 완료 알림 분해 금지 불변식 1~3."""
        with tempfile.TemporaryDirectory() as tmp:
            capsule = _Capsule(tmp)
            self.assertEqual(_run_adapter(capsule.envelope()).returncode, 0)
            records = _records(capsule.task_path)
            activity = [r for r in records if r["event"] == "activity"][-1]
            terminal = [r for r in records if r["event"].startswith("worker.")
                        and r["event"] != "worker.started"][0]

            a_src = activity["provenance"]["source"]
            t_src = terminal["provenance"]["source"]
            self.assertNotEqual(a_src["id"], t_src["id"])
            self.assertNotEqual(a_src["sha256"], t_src["sha256"])
            self.assertLess(a_src["observed_at"], t_src["observed_at"])
            self.assertLess(activity["timestamp"], terminal["timestamp"])
            self.assertEqual(activity["worker_run_id"], terminal["worker_run_id"])

    def test_terminal_status_maps_without_guessing(self):
        adapter = _load_adapter()
        self.assertEqual(adapter.terminal_event_for_status("completed"), "worker.completed")
        self.assertEqual(adapter.terminal_event_for_status("failed"), "worker.failed")
        self.assertEqual(adapter.terminal_event_for_status("cancelled"), "worker.blocked")
        self.assertIsNone(adapter.terminal_event_for_status("async_launched"))
        self.assertIsNone(adapter.terminal_event_for_status("some-future-status"))
        self.assertIsNone(adapter.terminal_event_for_status(None))

    def test_blocked_terminal_carries_template_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            capsule = _Capsule(tmp, status="cancelled")
            self.assertEqual(_run_adapter(capsule.envelope()).returncode, 0)
            terminal = [r for r in _records(capsule.task_path)
                        if r["event"] == "worker.blocked"]
            self.assertEqual(len(terminal), 1)
            self.assertEqual(terminal[0]["reason"],
                             "Task adapter: worker.blocked status=cancelled")

    def test_rerun_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            capsule = _Capsule(tmp)
            self.assertEqual(_run_adapter(capsule.envelope()).returncode, 0)
            first = _segment_bytes(capsule.task_path)
            self.assertEqual(_run_adapter(capsule.envelope()).returncode, 0)
            self.assertEqual(_segment_bytes(capsule.task_path), first,
                             "재실행이 조각 바이트를 바꿨다(멱등 위반)")

    def test_non_task_tool_and_missing_issued_copy_are_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            capsule = _Capsule(tmp)
            before = _segment_bytes(capsule.task_path)

            self.assertEqual(set(_load_adapter()._PLATFORM_TOOL_NAMES), {"Agent", "Task"})

            proc = _run_adapter(capsule.envelope(tool_name="Bash"))
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout, "")
            self.assertEqual(_segment_bytes(capsule.task_path), before)

            (capsule.cwd / ".opal" / "task-ownership.json").unlink()
            proc = _run_adapter(capsule.envelope())
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout, "")
            self.assertEqual(_segment_bytes(capsule.task_path), before)


# ─────────────────────────────────────────────────────────────────────────────
# ③ AC-7 — 조각·state.json·커서 평문 0건
# ─────────────────────────────────────────────────────────────────────────────
class TestAdapterRedaction(unittest.TestCase):

    def test_no_plaintext_secret_or_prompt_in_any_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            capsule = _Capsule(tmp, with_secrets=True)
            self.assertEqual(_run_adapter(capsule.envelope()).returncode, 0)

            records = _records(capsule.task_path)
            self.assertTrue(any(r["event"] == "worker.started" for r in records),
                            "비밀값 fixture 경로에서 사건이 하나도 방출되지 않았다")

            haystacks = {
                "segment": _segment_bytes(capsule.task_path),
                "state.json": (capsule.task_path / "state.json").read_bytes(),
                "cursor": capsule.cursor_bytes(),
            }
            needles = dict(_SECRET_FIXTURES)
            needles["prompt_body"] = _PROMPT_BODY
            needles["assistant_body"] = _ASSISTANT_BODY

            for where, blob in haystacks.items():
                for kind, secret in needles.items():
                    with self.subTest(where=where, kind=kind):
                        self.assertNotIn(
                            secret.encode("utf-8"), blob,
                            f"AC-7 위반 — {where}에 {kind} 평문이 남아있다")

    def test_summary_is_fixed_template_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            capsule = _Capsule(tmp, with_secrets=True)
            self.assertEqual(_run_adapter(capsule.envelope()).returncode, 0)
            for rec in _records(capsule.task_path):
                if rec["event"] == "run.started":
                    continue
                with self.subTest(event=rec["event"]):
                    self.assertRegex(
                        rec["summary"],
                        r"^(?:Agent|Task) adapter: [a-z.]+ status=[A-Za-z_]+ records=\d+$",
                        f"summary가 고정 템플릿 밖이다 — {rec['summary']!r}")
                    self.assertIsNone(rec.get("refs"),
                                      "refs에 플랫폼 절대 경로를 실으면 안 된다")
                    data = rec.get("data")
                    if data is not None:
                        self.assertEqual(set(data), {"kind"})


# ─────────────────────────────────────────────────────────────────────────────
# ⑤ 전 실패 경로 무출력 exit 0
# ─────────────────────────────────────────────────────────────────────────────
class TestAdapterFailSafe(unittest.TestCase):

    def _assert_silent_ok(self, stdin_text, label):
        proc = subprocess.run([str(_VENV_PYTHON), str(_ADAPTER_SRC)], input=stdin_text,
                              capture_output=True, text=True, env=_clean_env(), timeout=120)
        self.assertEqual(proc.returncode, 0, f"{label}: exit 0이 아니다 — {proc.stderr!r}")
        self.assertEqual(proc.stdout, "", f"{label}: stdout이 비어있지 않다 — {proc.stdout!r}")

    def test_all_failure_paths_are_silent_exit_zero(self):
        cases = {
            "empty_stdin": "",
            "not_json": "not json at all",
            "json_array": "[1, 2, 3]",
            "json_string": '"hello"',
            "missing_keys": "{}",
            "task_without_cwd": json.dumps({"tool_name": "Task"}),
            "nonexistent_paths": json.dumps({
                "tool_name": "Task", "cwd": "/nonexistent/w6",
                "transcript_path": "/nonexistent/w6/sess.jsonl",
                "session_id": "sess-x"}),
            "wrong_types": json.dumps({"tool_name": "Task", "cwd": 5,
                                       "transcript_path": ["x"], "tool_response": "y"}),
        }
        for label, payload in cases.items():
            with self.subTest(case=label):
                self._assert_silent_ok(payload, label)

    def test_broken_observation_sources_are_silent_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            capsule = _Capsule(tmp)
            capsule.meta_path.write_text("{ not json", encoding="utf-8")
            capsule.transcript.write_text("<task-notification>truncated",
                                          encoding="utf-8")
            proc = _run_adapter(capsule.envelope())
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stdout, "")
            self.assertEqual(
                [r["event"] for r in _records(capsule.task_path)], ["run.started"],
                "손상 원본에서 사건을 지어내면 안 된다")

    def test_unreachable_run_log_tool_is_silent_ok(self):
        """append 표면이 실패해도 훅은 세션을 막지 않는다."""
        adapter = _load_adapter()
        with tempfile.TemporaryDirectory() as tmp:
            capsule = _Capsule(tmp)
            emitted = adapter.handle(capsule.envelope(),
                                     run_log_run_sh=str(pathlib.Path(tmp) / "no-such-run.sh"))
            self.assertEqual(emitted, 0)
            self.assertEqual([r["event"] for r in _records(capsule.task_path)],
                             ["run.started"])


# ─────────────────────────────────────────────────────────────────────────────
# ⑥ 배포 배선 + 플랫폼 분기 격리
# ─────────────────────────────────────────────────────────────────────────────
class TestAdapterDeploymentWiring(unittest.TestCase):

    _ADAPTER_COMMAND = ('"$HOME/.opal/.venv/bin/python" '
                        '"$HOME/.opal/tools/run-log-tool/adapters/agent_tool_adapter.py"')

    def test_posttooluse_agent_or_task_hook_registered_once(self):
        hooks = json.loads(_HOOKS_JSON.read_text(encoding="utf-8"))
        blocks = [b for b in hooks.get("PostToolUse", []) if b.get("matcher") == "Agent|Task"]
        self.assertEqual(len(blocks), 1, "PostToolUse(matcher Agent|Task) 블록이 정확히 1건이 아니다")
        commands = [h.get("command") for h in blocks[0].get("hooks", [])]
        self.assertEqual(commands, [self._ADAPTER_COMMAND])

    def test_merge_hooks_upsert_is_idempotent(self):
        """scripts/merge-hooks.py 멱등 upsert 관례 — 2회 실행 결과가 바이트 동일."""
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / "settings.json"
            target.write_text(json.dumps({"hooks": {"PostToolUse": [
                {"matcher": "", "hooks": [{"type": "command", "command": "external-orca-hook"}]},
                {"matcher": "Task", "hooks": [{"type": "command",
                                                    "command": self._ADAPTER_COMMAND}]}
            ]}}), encoding="utf-8")
            for _ in range(2):
                proc = subprocess.run(["/usr/bin/python3", str(_MERGE_HOOKS),
                                       str(target), str(_HOOKS_JSON)],
                                      capture_output=True, text=True, env=_clean_env())
                self.assertEqual(proc.returncode, 0, proc.stderr)
                if _ == 0:
                    first = target.read_bytes()
            self.assertEqual(target.read_bytes(), first, "merge-hooks 재실행이 멱등이 아니다")

            merged = json.loads(target.read_text(encoding="utf-8"))
            post = merged["hooks"]["PostToolUse"]
            agent_task_blocks = [b for b in post if b.get("matcher") == "Agent|Task"]
            self.assertEqual(len(agent_task_blocks), 1, "Agent|Task 블록이 누적되거나 사라졌다")
            self.assertTrue(agent_task_blocks[0].get("_opal_managed"))
            self.assertFalse([b for b in post if b.get("matcher") == "Task"],
                             "기존 Task 단일 matcher가 Agent|Task 전환 뒤에도 남았다")
            self.assertTrue(any(h.get("command") == "external-orca-hook"
                                for b in post for h in b.get("hooks", [])),
                            "외부 hook이 보존되지 않았다")

    def test_install_script_reflects_adapter_deployment(self):
        text = _INSTALL_SH.read_text(encoding="utf-8")
        self.assertIn("tools/run-log-tool/adapters/agent_tool_adapter.py", text,
                      ".opal/AGENT.md 배포 반영 계약 — install-mac.sh가 변환기 경로를 다루지 않는다")

    def test_platform_envelope_keys_stay_inside_the_adapter(self):
        """[MUST] 플랫폼 고유 봉투 키·경로 문법은 이 어댑터 파일 한 곳에만 둔다."""
        adapter_text = _ADAPTER_SRC.read_text(encoding="utf-8")
        tokens = ("subagents", "agentId", "task-notification", "transcript_path",
                  "agentType", "toolUseResult", "tool_response")
        for token in tokens:
            with self.subTest(token=token):
                self.assertIn(token, adapter_text)
        for other in ((_TOOL_DIR / "run_log_core.py"), (_TOOL_DIR / "run_log_tool.py")):
            other_text = other.read_text(encoding="utf-8")
            for token in tokens:
                with self.subTest(file=other.name, token=token):
                    self.assertNotIn(token, other_text,
                                     f"{other.name}에 플랫폼 고유 토큰 {token!r}이 샜다")

    def test_adapter_does_not_link_run_log_core(self):
        """[MUST] CONTRACT §3.1 — 채널 변환기는 run-log-core를 직접 링크하지 않는다."""
        text = _ADAPTER_SRC.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import ", "from ")):
                self.assertNotIn("run_log_core", stripped,
                                 f"기록 코어를 직접 import했다 — {stripped!r}")
                self.assertNotIn("state_tool", stripped,
                                 f"상태 도구를 직접 import했다 — {stripped!r}")
        self.assertIn("run-log-tool", text)

    def test_run_id_comes_only_from_state_tool_show(self):
        with tempfile.TemporaryDirectory() as tmp:
            capsule = _Capsule(tmp)
            adapter = _load_adapter()
            run_id = adapter.resolve_active_run_id(capsule.task_path)
            state = json.loads((capsule.task_path / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(run_id, state["run_log"]["active_run_id"])
            for rec in _records(capsule.task_path):
                self.assertEqual(rec["run_id"], run_id)


if __name__ == "__main__":
    unittest.main()
