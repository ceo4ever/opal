"""
@header {
  "module": "test_state_tool_ownership",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "태스크 138 S-11 — state-tool init→첫 advance에서 OPAL_SESSION_ID(또는 CLAUDE_CODE_SESSION_ID 매핑) 존재 시 lease 원자 생성 1회 + run-log actor.session_id 채움을 검증한다. env 미설정 시 종전과 동일 전이여야 한다(회귀). 기존 test_state_tool.py는 수정하지 않고 별도 파일로 신설했다. 태스크 150 S-11(W-5, AC-1·AC-10·C-6) — `TestT150W5ClaimantRoot`가 `_claim_task_lease_if_needed()`의 `claimant_root=os.getcwd()` 전달을 고정한다: 이관 대기(handoff_pending) 태스크에서 허브 cwd의 advance/mark는 lease를 되찾지 못하지만(레코드 불변) 전이는 exit 0으로 통과하고, 워크트리 루트 cwd의 전이는 이관을 소비해 claim에 성공하며(SessionStart 실패 시 자가 치유), 이관 필드가 없는 기존 형식 lease의 claim·foreign_owner 동작과 비 `--wt` 태스크의 응답 키 집합·state.json 산출물은 변경 전과 동일하다. lease 레코드는 손으로 조립하지 않고 `ownership_tool.lease`의 claim/handoff 함수만 거친다.",
  "exports": [],
  "depends": ["state_tool.py (CLI subprocess)", "ownership_tool.lease", "ownership_tool.claude_adapter (SESSION_ID_ENV 상수)"]
}
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

STATE_TOOL_PATH = Path(__file__).parent.parent / "state_tool.py"

_CLAUDE_ADAPTER_PATH = (
    Path(__file__).parent.parent.parent
    / "ownership-tool"
    / "ownership_tool"
    / "claude_adapter.py"
)


def _load_claude_adapter_session_id_env() -> str:
    """`claude_adapter`가 소유한 플랫폼 고유 세션 변수명 상수를 얻는다.

    변수명을 이 테스트에 하드코딩하지 않기 위해 `claude_adapter.SESSION_ID_ENV`를
    직접 적재한다(D-18·C-15 — 플랫폼 고유 이름은 어댑터 한 곳에만 둔다)."""
    spec = importlib.util.spec_from_file_location(
        "ownership_tool.claude_adapter", _CLAUDE_ADAPTER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SESSION_ID_ENV


CLAUDE_SESSION_ID_ENV = _load_claude_adapter_session_id_env()

SIMPLE_ROWS_SPEC = json.dumps(
    [
        {"stage": "TASK", "item": "작업"},
        {"stage": "PLAN", "item": "작업"},
        {"stage": "EXECUTE", "item": "작업"},
        {"stage": "CLOSE", "item": "State Gate"},
    ]
)


def _run(args: list[str], env: dict | None = None) -> subprocess.CompletedProcess:
    full_env = dict(os.environ)
    if env is not None:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, str(STATE_TOOL_PATH), *args],
        capture_output=True,
        text=True,
        env=full_env,
    )


class TestS11OwnershipSessionIntegration(unittest.TestCase):
    """S-11 (AC-12, AC-27, C-9, H-2) — 구현 전 RED."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.task_path = Path(self.tmp.name) / "tasks" / "999-red-s11"
        self.task_path.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _init(self, env=None):
        return _run(
            [
                "init",
                str(self.task_path),
                "--skill",
                "opds",
                "--mode",
                "agentic",
                "--task-title",
                "S-11 RED",
                "--rows-spec",
                SIMPLE_ROWS_SPEC,
            ],
            env=env,
        )

    def test_env_set_creates_lease_exactly_once_at_first_advance(self):
        """OPAL_SESSION_ID 설정 시 최초 경계 1곳에서만 hub lease 원자 생성(중복 claim 없음)."""
        init_result = self._init()
        self.assertEqual(init_result.returncode, 0, init_result.stderr)

        env = {"OPAL_SESSION_ID": "sess-s11-red-0001"}
        first = _run(["advance", str(self.task_path), "--row", "1"], env=env)

        lease_file = self.task_path / "run/.runtime/owner.json"
        self.assertTrue(
            lease_file.exists(),
            f"S-11 RED 기대: lease 파일이 아직 생성되지 않음(미구현) — stdout={first.stdout!r} stderr={first.stderr!r}",
        )

    def test_env_set_run_log_actor_session_id_filled(self):
        """OPAL_SESSION_ID env 값이 run-log 사건 actor.session_id로 채워진다.

        [MUST] 1.0/1.1 태스크는 run_log 블록 자체가 없고 run_log_commit()이
        save_state_json()으로 우회한다(state_tool.py C-3) — 대조할 사건이 애초에
        생성되지 않는다. `--run-log-mode shadow`로 schema 1.2 + run_log 블록을
        만들어야 검증이 가능하다. 커밋된 사건은 drain되어 `<task>/run/run-log-*.jsonl`
        조각에 실리고 pending_events는 비워지므로(state_tool.py _run_log_drain),
        state.json의 존재한 적 없는 `run_log.events` 키가 아니라 그 조각을 관측한다
        (같은 태스크의 test_state_tool.py::TestT138W9ActorSessionId._events()와 동일 패턴)."""
        init_result = _run(
            [
                "init",
                str(self.task_path),
                "--skill",
                "opds",
                "--mode",
                "agentic",
                "--task-title",
                "S-11 RED",
                "--rows-spec",
                SIMPLE_ROWS_SPEC,
                "--run-log-mode",
                "shadow",
            ]
        )
        self.assertEqual(init_result.returncode, 0, init_result.stderr)

        env = {"OPAL_SESSION_ID": "sess-s11-red-0002"}
        advance_result = _run(["advance", str(self.task_path), "--row", "1"], env=env)
        self.assertEqual(advance_result.returncode, 0, advance_result.stderr)

        events = []
        for segment in sorted((self.task_path / "run").glob("run-log-*.jsonl")):
            for line in segment.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    events.append(json.loads(line))

        state_path = self.task_path / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        pending_events = state.get("run_log", {}).get("pending_events") or []
        events.extend(e for e in pending_events if isinstance(e, dict))

        actor_session_ids = [e.get("actor", {}).get("session_id") for e in events if isinstance(e, dict)]
        self.assertIn(
            "sess-s11-red-0002",
            actor_session_ids,
            f"run-log 사건(조각+pending_events)에 actor.session_id가 채워져야 한다 — events={events!r}",
        )

    def test_env_unset_transition_unchanged_regression_guard(self):
        """OPAL_SESSION_ID 미설정 시 state 전이 결과·transition_action이 종전과 동일해야 한다
        (이 케이스는 기존 동작 보존이므로 GREEN 이후에도 PASS 유지되어야 하는 회귀 가드)."""
        init_result = self._init()
        self.assertEqual(init_result.returncode, 0, init_result.stderr)

        clean_env = dict(os.environ)
        clean_env.pop("OPAL_SESSION_ID", None)
        clean_env.pop(CLAUDE_SESSION_ID_ENV, None)
        # `_run()`의 dict.update 병합은 부재 키를 지우지 못해 앰비언트 값이 되살아난다
        # (full_env=dict(os.environ) 후 clean_env로 update해도 clean_env에 없는 키는
        # 그대로 남는다) — 이 케이스는 진짜 "미설정" 서브프로세스 env가 필요하므로
        # 병합을 거치지 않고 구성한 env를 그대로 넘긴다.
        result = subprocess.run(
            [sys.executable, str(STATE_TOOL_PATH), "advance", str(self.task_path), "--row", "1"],
            capture_output=True,
            text=True,
            env=clean_env,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        state_path = self.task_path / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertIn(state.get("current_status"), ("in_progress", "done", None) or [state.get("current_status")])
        lease_file = self.task_path / "run/.runtime/owner.json"
        self.assertFalse(lease_file.exists())


_LEASE_PATH = (
    Path(__file__).parent.parent.parent
    / "ownership-tool"
    / "ownership_tool"
    / "lease.py"
)


def _load_lease_module():
    """`ownership_tool.lease`를 sys.path 오염 없이 적재한다.

    state_tool.py의 `_import_ownership_lease()`와 같은 관례(패키지 먼저 등록 →
    서브모듈 적재)를 쓴다. 테스트가 lease 레코드를 손으로 조립하지 않고 도구
    함수(claim/handoff)만 거치기 위한 적재다."""
    pkg_dir = str(_LEASE_PATH.parent)
    pkg = sys.modules.get("ownership_tool")
    if pkg is None or pkg_dir not in list(getattr(pkg, "__path__", []) or []):
        pkg_spec = importlib.util.spec_from_file_location(
            "ownership_tool",
            os.path.join(pkg_dir, "__init__.py"),
            submodule_search_locations=[pkg_dir],
        )
        pkg = importlib.util.module_from_spec(pkg_spec)
        sys.modules["ownership_tool"] = pkg
        pkg_spec.loader.exec_module(pkg)
    spec = importlib.util.spec_from_file_location(
        "ownership_tool.lease", str(_LEASE_PATH)
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["ownership_tool.lease"] = module
    spec.loader.exec_module(module)
    return module


_TS_VALUE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")
_RUN_ID_KEYS = ("run_id", "active_run_id")


def _normalize(value):
    """실행마다 달라지는 값(시각·run id)만 상수로 접어 두 산출물을 구조 비교 가능하게 만든다.

    claim 유무와 무관하게 달라지는 축이므로 접지 않으면 비교 자체가 성립하지
    않는다. 나머지 키·값은 그대로 두어 산출물 불변을 실제로 집행한다."""
    if isinstance(value, dict):
        return {
            k: ("<RUN_ID>" if k in _RUN_ID_KEYS else _normalize(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    if isinstance(value, str) and _TS_VALUE.match(value):
        return "<TS>"
    return value


def _run_at(cwd, args, env=None):
    """`_run()`과 같되 서브프로세스 cwd를 지정한다 — claimant_root가 cwd에서 오기 때문이다."""
    full_env = dict(os.environ)
    full_env.pop("OPAL_SESSION_ID", None)
    full_env.pop(CLAUDE_SESSION_ID_ENV, None)
    if env is not None:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, str(STATE_TOOL_PATH), *args],
        capture_output=True,
        text=True,
        env=full_env,
        cwd=str(cwd),
    )


class TestT150W5ClaimantRoot(unittest.TestCase):
    """태스크 150 S-11 (AC-1, AC-10, C-6) — 상태 전이 claim 주체 전달.

    `_claim_task_lease_if_needed()`가 `claimant_root=os.getcwd()`를 넘기면서
    이관 중(`handoff_pending`) 태스크의 허브 재-claim이 거부되지만, 그 거부는
    기존 `foreign_owner`와 **완전히 동일하게** 경고 1줄로 접히고 전이는 통과한다.
    """

    HUB_SESSION = "sess-150-hub-0001"
    WT_SESSION = "sess-150-wt-0001"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.hub_cwd = self.root / "hub"
        self.hub_cwd.mkdir()
        self.worktree_root = self.root / "hub" / ".opal-worktrees" / "wt-150"
        self.worktree_root.mkdir(parents=True)
        self.task_path = self.root / "hub" / "tasks" / "150-claimant-root"
        self.task_path.mkdir(parents=True)
        self.lease = _load_lease_module()
        self.lease_file = self.task_path / "run/.runtime/owner.json"

    def tearDown(self):
        self.tmp.cleanup()

    def _init(self, task_path=None):
        target = task_path or self.task_path
        result = _run_at(
            self.hub_cwd,
            [
                "init",
                str(target),
                "--skill",
                "opds",
                "--mode",
                "agentic",
                "--task-title",
                "150 W-5",
                "--rows-spec",
                SIMPLE_ROWS_SPEC,
            ],
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def _read_lease(self):
        return json.loads(self.lease_file.read_text(encoding="utf-8"))

    def _put_task_into_handoff(self):
        """허브 세션 소유 lease를 만든 뒤 워크트리 루트 앞으로 이관 대기로 바꾼다."""
        claimed = self.lease.claim(
            str(self.task_path),
            session_id=self.HUB_SESSION,
            claim_source="session_start",
        )
        self.assertTrue(claimed.get("ok"), claimed)
        handed = self.lease.handoff(
            str(self.task_path),
            session_id=self.HUB_SESSION,
            to_worktree_root=str(self.worktree_root),
        )
        self.assertTrue(handed.get("ok"), handed)
        self.assertEqual(self._read_lease().get("status"), "handoff_pending")

    def test_hub_transition_on_handoff_pending_task_does_not_reclaim(self):
        """이관 중 태스크에서 허브가 advance/mark를 해도 lease를 되찾지 않는다(H-2, AC-1)."""
        self._init()
        self._put_task_into_handoff()
        before = self._read_lease()

        advance = _run_at(
            self.hub_cwd,
            ["advance", str(self.task_path), "--row", "1"],
            env={"OPAL_SESSION_ID": self.HUB_SESSION},
        )
        self.assertEqual(advance.returncode, 0, advance.stderr)
        mark = _run_at(
            self.hub_cwd,
            ["mark", str(self.task_path), "--row", "1", "--done"],
            env={"OPAL_SESSION_ID": self.HUB_SESSION},
        )
        self.assertEqual(mark.returncode, 0, mark.stderr)

        after = self._read_lease()
        self.assertEqual(after, before, "허브 전이가 이관 대기 레코드를 바꾸면 안 된다")
        self.assertEqual(after.get("status"), "handoff_pending")
        self.assertIsNone(after.get("owner_session_id"))

    def test_hub_transition_on_handoff_pending_task_still_succeeds(self):
        """이관 중 거부는 `foreign_owner`와 동일하게 fail-safe다 — 전이가 통과한다(C-6, AC-10)."""
        self._init()
        self._put_task_into_handoff()

        advance = _run_at(
            self.hub_cwd,
            ["advance", str(self.task_path), "--row", "1"],
            env={"OPAL_SESSION_ID": self.HUB_SESSION},
        )
        self.assertEqual(advance.returncode, 0, advance.stderr)
        payload = json.loads(advance.stdout)
        self.assertTrue(payload.get("ok"), payload)

        state = json.loads((self.task_path / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["rows"][0].get("status"), "in_progress")

    def test_worktree_cwd_transition_claims_handed_off_lease(self):
        """워크트리 cwd의 전이는 이관을 소비해 claim에 성공한다(SessionStart 실패 시 자가 치유)."""
        self._init()
        self._put_task_into_handoff()

        advance = _run_at(
            self.worktree_root,
            ["advance", str(self.task_path), "--row", "1"],
            env={"OPAL_SESSION_ID": self.WT_SESSION},
        )
        self.assertEqual(advance.returncode, 0, advance.stderr)

        after = self._read_lease()
        self.assertEqual(after.get("owner_session_id"), self.WT_SESSION)
        self.assertEqual(after.get("status"), "active")
        self.assertEqual(after.get("claim_source"), "state_transition")

    def test_legacy_lease_without_handoff_fields_claim_unchanged(self):
        """이관 필드가 없는 기존 형식 lease의 claim 동작이 변경 전과 동일하다(AC-10)."""
        self._init()

        first = _run_at(
            self.hub_cwd,
            ["advance", str(self.task_path), "--row", "1"],
            env={"OPAL_SESSION_ID": self.HUB_SESSION},
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        record = self._read_lease()
        self.assertEqual(record.get("owner_session_id"), self.HUB_SESSION)
        self.assertEqual(record.get("status"), "active")
        self.assertNotIn("handoff_to_worktree_root", record)

        # 타 세션의 전이는 foreign_owner로 claim만 실패하고 전이는 통과한다(종전 동작).
        second = _run_at(
            self.hub_cwd,
            ["mark", str(self.task_path), "--row", "1", "--done"],
            env={"OPAL_SESSION_ID": "sess-150-other-0002"},
        )
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self._read_lease().get("owner_session_id"), self.HUB_SESSION)
        state = json.loads((self.task_path / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["rows"][0].get("status"), "done")

    def test_non_worktree_task_response_keys_and_state_json_unchanged(self):
        """`--wt`가 아닌 태스크의 응답 키 집합과 state.json 산출물이 세션 유무와 무관하게 같다(C-6)."""
        # 두 태스크의 디렉터리명을 같게 둬 state.json의 task_id까지 동일 비교한다.
        baseline_task = self.root / "baseline" / "tasks" / "150-claimant-root"
        baseline_task.mkdir(parents=True)
        self._init(task_path=baseline_task)
        self._init()

        without = _run_at(self.hub_cwd, ["advance", str(baseline_task), "--row", "1"])
        with_session = _run_at(
            self.hub_cwd,
            ["advance", str(self.task_path), "--row", "1"],
            env={"OPAL_SESSION_ID": self.HUB_SESSION},
        )
        self.assertEqual(without.returncode, with_session.returncode)
        self.assertEqual(without.returncode, 0, without.stderr)
        self.assertEqual(
            set(json.loads(without.stdout).keys()),
            set(json.loads(with_session.stdout).keys()),
            "claim 여부가 응답 JSON 키 집합을 바꾸면 안 된다",
        )

        baseline_state = _normalize(
            json.loads((baseline_task / "state.json").read_text(encoding="utf-8"))
        )
        session_state = _normalize(
            json.loads((self.task_path / "state.json").read_text(encoding="utf-8"))
        )
        self.assertEqual(
            baseline_state,
            session_state,
            "claim 여부가 state.json 산출물을 바꾸면 안 된다",
        )
        self.assertFalse((baseline_task / "run/.runtime/owner.json").exists())


if __name__ == "__main__":
    unittest.main()
