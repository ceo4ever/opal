"""
@header {
  "module": "test_oppl_runtime_config",
  "task": "131",
  "layer": "test",
  "domain": "opal-tools",
  "description": "oppl-runtime-tool 설정 로더(D6)와 run identity 게이트(D8/C-5)의 행위 계약 RED-first 테스트. S-1(필수 키 13종 fail-closed 거부), S-2(1단계 키 오버라이드 — 딥 머지 금지), S-4(run_identity_missing)를 담당한다. 검증 대상은 run.sh의 공개 인터페이스(stdout 단일 라인 JSON + exit code)뿐이며 내부 함수 결합·mock/patch를 쓰지 않는다(red-first.md §4). RED 상태 — oppl-runtime-tool 미구현이므로 전부 FAIL 예상. GREEN 전환은 EXECUTE 구현 워커 담당(작성자≠구현자, red-first.md §2).",
  "scenarios": ["S-1", "S-2", "S-4"],
  "exports": ["TestConfigInvalid", "TestConfigKeyOverride", "TestInitRunIdentity"]
}

고정하는 공개 인터페이스
------------------------
  bash opal/tools/oppl-runtime-tool/run.sh config --task-path <t>
  bash opal/tools/oppl-runtime-tool/run.sh init   --task-path <t> --run-id <id>

  성공: {"ok":true,"command":"<sub>", ...}      exit 0
  실패: {"ok":false,"command":"<sub>","error":"<코드>", ...}  exit != 0
  (opal/core/references/harness/tool-output-contract.md — 단일 라인 JSON + exit code만)

설정 주입 경로 (테스트가 고정한다)
  전역: $OPAL_HOME/setting.json   — OPAL_HOME 미설정 시 ~/.opal.
        기존 선례 state_tool.py:403 `os.environ.get("OPAL_HOME") or ~/.opal`를 따르며
        신규 추상화를 만들지 않는다(PRINCIPLES §2).
  로컬: <project-root>/.opal/setting.local.json
        project root는 --task-path에서 위로 올라가며 `.opal/`을 가진 첫 조상이다.

근거
  PLAN.md D6 (1단계 키 오버라이드, 딥 머지 금지, config_invalid 단일 코드)
  PLAN.md D8 / TASK C-5 (run_id는 state-tool이 발급, oppl-runtime-tool은 외래 참조만)
  제안서 §6.1 (필수 키 9종 유한 양수, max_cost_usd 선택 키)
  PLAN.md W-3 (등록 phase 집합 t1,t2,g,t3,t4a,t4b)
"""

import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

_RUN_SH = pathlib.Path(__file__).resolve().parent.parent / "run.sh"

# PLAN.md W-3 — 등록 phase 집합 상수
REGISTERED_PHASES = ["t1", "t2", "g", "t3", "t4a", "t4b"]

# 제안서 §6.1 — 필수 키 9종
REQUIRED_KEYS = [
    "max_design_rounds",
    "max_project_dispatches",
    "max_task_attempts",
    "max_identical_failures",
    "max_wall_time_sec",
    "heartbeat_timeout_sec",
    "hard_timeout_sec_by_phase",
    "max_hard_timeout_sec",
    "terminate_grace_sec",
]


def valid_runtime(**overrides):
    base = {
        "max_design_rounds": 5,
        "max_project_dispatches": 20,
        "max_task_attempts": 4,
        "max_identical_failures": 3,
        "max_wall_time_sec": 3600,
        "heartbeat_timeout_sec": 120,
        "hard_timeout_sec_by_phase": {p: 600 for p in REGISTERED_PHASES},
        "max_hard_timeout_sec": 1800,
        "terminate_grace_sec": 5,
    }
    base.update(overrides)
    return base


class Workspace:
    """임시 프로젝트 루트 + 태스크 폴더 + 전역/로컬 설정 쌍 (실제 파일)."""

    def __init__(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="oppl-rt-cfg-"))
        self.opal_home = self.tmp / "opal-home"
        self.opal_home.mkdir(parents=True)
        self.project_root = self.tmp / "project"
        (self.project_root / ".opal").mkdir(parents=True)
        self.task_path = self.project_root / "tasks" / "T-001-fixture"
        self.task_path.mkdir(parents=True)

    def cleanup(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, path, runtime, raw):
        if raw is not None:
            path.write_text(raw, encoding="utf-8")
        elif runtime is None:
            if path.exists():
                path.unlink()
        else:
            path.write_text(
                json.dumps({"oppl": {"runtime": runtime}}, ensure_ascii=False),
                encoding="utf-8",
            )
        return path

    def write_global(self, runtime=None, raw=None):
        return self._write(self.opal_home / "setting.json", runtime, raw)

    def write_local(self, runtime=None, raw=None):
        return self._write(self.project_root / ".opal" / "setting.local.json", runtime, raw)

    def write_state(self, run_id=None):
        doc = {
            "task_id": "131",
            "skill": "opal-pilot-project-loop",
            "mode": "agentic",
            "schema_version": "2.0",
            "created_at": "2026-09-14 00:00",
            "updated_at": "2026-09-14 00:00",
            "current_status": "in_progress",
            "rows": [],
        }
        if run_id is not None:
            doc["run_id"] = run_id
        p = self.task_path / "state.json"
        p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        return p

    @property
    def run_dir(self):
        return self.task_path / ".oppl-run"

    def env(self):
        e = dict(os.environ)
        e["OPAL_HOME"] = str(self.opal_home)
        return e


def run_tool(ws, args, timeout=60):
    """run.sh 실호출 → (returncode, stdout, parsed). run.sh 부재도 정상 RED 증거다."""
    proc = subprocess.run(
        ["bash", str(_RUN_SH), *args],
        capture_output=True,
        text=True,
        env=ws.env(),
        cwd=str(ws.project_root),
        timeout=timeout,
    )
    stdout = proc.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return proc.returncode, stdout, data


class _Base(unittest.TestCase):
    def setUp(self):
        self.ws = Workspace()
        self.addCleanup(self.ws.cleanup)

    def assert_single_line_json(self, stdout):
        self.assertTrue(stdout, "stdout이 비어 있다 — 단일 라인 JSON 계약 위반")
        self.assertNotIn("\n", stdout, f"stdout이 다중 라인이다 — 계약 위반: {stdout!r}")
        return json.loads(stdout)

    def assert_config_invalid(self, label):
        """config와 admit 두 진입점 모두 config_invalid + 비영 exit로 거부되어야 한다.

        subTest를 쓰지 않는다 — pytest가 subTest 실패를 SUBFAILED로 내면서 테스트
        자체는 PASSED로 집계해 거짓 GREEN이 만들어진다.
        """
        for sub_args in (
            ["config", "--task-path", str(self.ws.task_path)],
            ["admit", "--task-path", str(self.ws.task_path), "--scope", "round"],
        ):
            rc, stdout, _ = run_tool(self.ws, sub_args)
            tag = f"{label}/{sub_args[0]}"
            data = self.assert_single_line_json(stdout)
            self.assertFalse(data.get("ok"), f"[{tag}] 조용한 기본값 강등 발생")
            self.assertEqual(
                data.get("error"), "config_invalid",
                f"[{tag}] 단일 오류 코드 config_invalid가 아니다: {data!r}",
            )
            self.assertNotEqual(rc, 0, f"[{tag}] exit code가 0이다 (fail-closed 위반)")
        # 프로세스 생성 0건 — 거부 경로에서 런타임 ledger를 만들지 않는다
        self.assertFalse(
            self.ws.run_dir.exists(),
            f"[{label}] 거부 경로인데 .oppl-run이 생성됐다",
        )


# ─────────────────────────────────────────────────────────────────────────────
# S-1 — 필수 키 결손·비유한값 fail-closed 거부 (AC-5, C-2)
# ─────────────────────────────────────────────────────────────────────────────
class TestConfigInvalid(_Base):

    def test_s1_both_setting_files_absent_rejected(self):
        """전역·로컬 양쪽 부재 1종 → config_invalid."""
        self.ws.write_global(None)
        self.ws.write_local(None)
        self.ws.write_state(run_id="run-20260914000000-deadbeef")
        self.assert_config_invalid("both-absent")

    def test_s1_each_required_key_missing_rejected(self):
        """필수 키 9종 각각 누락 → config_invalid (조용한 기본값 강등 0건)."""
        self.ws.write_state(run_id="run-20260914000000-deadbeef")
        for key in REQUIRED_KEYS:
            rt = valid_runtime()
            rt.pop(key)
            self.ws.write_global(rt)
            self.ws.write_local(None)
            self.assert_config_invalid(f"missing:{key}")

    def test_s1_zero_negative_string_infinity_rejected(self):
        """0 · 음수 · 문자열 · Infinity 4종 변형 → config_invalid."""
        self.ws.write_state(run_id="run-20260914000000-deadbeef")
        scalar_keys = [k for k in REQUIRED_KEYS if k != "hard_timeout_sec_by_phase"]
        for key in scalar_keys:
            for label, value in (("zero", 0), ("negative", -1), ("string", "600")):
                rt = valid_runtime(**{key: value})
                self.ws.write_global(rt)
                self.ws.write_local(None)
                self.assert_config_invalid(f"{label}:{key}")

        # Infinity — JSON 확장 토큰을 실제 파일 텍스트로 주입한다
        rt = valid_runtime()
        rt.pop("max_wall_time_sec")
        raw = json.dumps({"oppl": {"runtime": rt}})
        raw = raw.replace('{"max_design_rounds"', '{"max_wall_time_sec": Infinity, "max_design_rounds"')
        self.ws.write_global(raw=raw)
        self.ws.write_local(None)
        self.assert_config_invalid("infinity:max_wall_time_sec")

    def test_s1_hard_timeout_map_variants_rejected(self):
        """hard_timeout_sec_by_phase: 등록 phase 누락 · 0 · 음수 · 문자열 → config_invalid."""
        self.ws.write_state(run_id="run-20260914000000-deadbeef")
        variants = {
            "phase-missing": {p: 600 for p in REGISTERED_PHASES if p != "t4b"},
            "phase-zero": {**{p: 600 for p in REGISTERED_PHASES}, "g": 0},
            "phase-negative": {**{p: 600 for p in REGISTERED_PHASES}, "g": -5},
            "phase-string": {**{p: 600 for p in REGISTERED_PHASES}, "g": "600"},
            "not-a-map": 600,
        }
        for label, value in variants.items():
            self.ws.write_global(valid_runtime(hard_timeout_sec_by_phase=value))
            self.ws.write_local(None)
            self.assert_config_invalid(f"hard_timeout:{label}")

    def test_s1_unparsable_setting_file_rejected(self):
        """파싱 실패 → 기본값 강등 없이 config_invalid."""
        self.ws.write_state(run_id="run-20260914000000-deadbeef")
        self.ws.write_global(raw='{"oppl": {"runtime": {')
        self.ws.write_local(None)
        self.assert_config_invalid("unparsable-global")

    def test_s1_optional_max_cost_usd_must_be_finite_positive(self):
        """max_cost_usd는 선택 키이나 존재하면 유한 양수여야 한다."""
        self.ws.write_state(run_id="run-20260914000000-deadbeef")
        for label, value in (("zero", 0), ("negative", -1.0), ("string", "1.0")):
            self.ws.write_global(valid_runtime(max_cost_usd=value))
            self.ws.write_local(None)
            self.assert_config_invalid(f"max_cost_usd:{label}")

    def test_s1_valid_config_is_accepted(self):
        """대조군 — 유효 설정은 ok:true로 통과해야 한다(항진 거부 방지)."""
        self.ws.write_global(valid_runtime())
        self.ws.write_local(None)
        self.ws.write_state(run_id="run-20260914000000-deadbeef")
        rc, stdout, data = run_tool(self.ws, ["config", "--task-path", str(self.ws.task_path)])
        self.assert_single_line_json(stdout)
        self.assertTrue(data.get("ok"), f"유효 설정이 거부됐다: {data!r}")
        self.assertEqual(rc, 0)


# ─────────────────────────────────────────────────────────────────────────────
# S-2 — 1단계 키 오버라이드 (딥 머지 금지) (AC-5, C-2)
# ─────────────────────────────────────────────────────────────────────────────
class TestConfigKeyOverride(_Base):

    def _effective(self, data):
        """config 응답에서 effective 설정 블록을 꺼낸다."""
        self.assertIn("config", data, f"config 응답에 effective 설정 블록이 없다: {data!r}")
        return data["config"]

    def test_s2_local_keys_replace_global_wholesale(self):
        """로컬에 있는 2개 키만 통째 교체되고 나머지는 전역 값."""
        self.ws.write_state(run_id="run-20260914000000-deadbeef")
        self.ws.write_global(valid_runtime())
        local_map = {p: 111 for p in REGISTERED_PHASES}
        self.ws.write_local({
            "max_task_attempts": 9,
            "hard_timeout_sec_by_phase": local_map,
        })

        rc, stdout, data = run_tool(self.ws, ["config", "--task-path", str(self.ws.task_path)])
        self.assert_single_line_json(stdout)
        self.assertTrue(data.get("ok"), f"유효한 병합인데 거부됐다: {data!r}")
        self.assertEqual(rc, 0)

        eff = self._effective(data)
        self.assertEqual(eff.get("max_task_attempts"), 9, "로컬 키가 반영되지 않았다")
        self.assertEqual(
            eff.get("hard_timeout_sec_by_phase"), local_map,
            "hard_timeout_sec_by_phase가 통째 교체되지 않았다",
        )
        # 나머지 7개 키는 전역 값 그대로
        g = valid_runtime()
        for key in REQUIRED_KEYS:
            if key in ("max_task_attempts", "hard_timeout_sec_by_phase"):
                continue
            self.assertEqual(eff.get(key), g[key], f"{key}가 전역 값이 아니다")

    def test_s2_partial_phase_map_is_not_deep_merged(self):
        """로컬 map에 일부 phase만 있으면 딥 머지 없이 config_invalid로 거부된다."""
        self.ws.write_state(run_id="run-20260914000000-deadbeef")
        self.ws.write_global(valid_runtime())
        self.ws.write_local({
            "max_task_attempts": 9,
            "hard_timeout_sec_by_phase": {"t1": 111, "t3": 222},
        })
        self.assert_config_invalid("local-partial-phase-map")

    def test_s2_resume_limit_is_not_a_config_key(self):
        """재개 상한은 설정 키가 아니다 — config 출력에 노출되지 않는다(S-15와 공유 계약)."""
        self.ws.write_state(run_id="run-20260914000000-deadbeef")
        self.ws.write_global(valid_runtime())
        self.ws.write_local(None)
        _, stdout, data = run_tool(self.ws, ["config", "--task-path", str(self.ws.task_path)])
        self.assert_single_line_json(stdout)
        eff = self._effective(data)
        leaked = [k for k in eff if "resume" in k.lower()]
        self.assertEqual(leaked, [], f"재개 상한이 설정 키로 노출됐다: {leaked}")


# ─────────────────────────────────────────────────────────────────────────────
# S-4 — run identity 게이트 (C-5)
# ─────────────────────────────────────────────────────────────────────────────
class TestInitRunIdentity(_Base):

    def setUp(self):
        super().setUp()
        self.ws.write_global(valid_runtime())
        self.ws.write_local(None)

    def _assert_run_identity_missing(self, args, label):
        rc, stdout, data = run_tool(self.ws, args)
        self.assertTrue(stdout, f"[{label}] stdout이 비어 있다")
        self.assertNotIn("\n", stdout, f"[{label}] 단일 라인 JSON 계약 위반")
        payload = json.loads(stdout)
        self.assertFalse(payload.get("ok"), f"[{label}] 거부되지 않았다: {payload!r}")
        self.assertEqual(
            payload.get("error"), "run_identity_missing",
            f"[{label}] 오류 코드가 run_identity_missing이 아니다: {payload!r}",
        )
        self.assertNotEqual(rc, 0, f"[{label}] exit code가 0이다")
        self.assertFalse(
            (self.ws.task_path / ".oppl-run" / "runtime.json").exists(),
            f"[{label}] 거부됐는데 runtime.json이 생성됐다",
        )

    def test_s4_init_without_run_id_flag_rejected(self):
        """--run-id 인자 없이 init → run_identity_missing."""
        self.ws.write_state(run_id=None)
        self._assert_run_identity_missing(
            ["init", "--task-path", str(self.ws.task_path)],
            "no --run-id flag",
        )

    def test_s4_init_with_state_missing_run_id_rejected(self):
        """state.json에 run_id가 없으면 --run-id를 줘도 거부된다 (도구는 발급하지 않는다)."""
        self.ws.write_state(run_id=None)
        self._assert_run_identity_missing(
            ["init", "--task-path", str(self.ws.task_path),
             "--run-id", "run-20260914000000-deadbeef"],
            "state.json lacks run_id",
        )

    def test_s4_init_with_state_file_absent_rejected(self):
        """state.json 자체가 없으면 run identity를 확인할 수 없으므로 거부."""
        state = self.ws.task_path / "state.json"
        if state.exists():
            state.unlink()
        self._assert_run_identity_missing(
            ["init", "--task-path", str(self.ws.task_path),
             "--run-id", "run-20260914000000-deadbeef"],
            "state.json absent",
        )

    def test_s4_init_succeeds_when_state_run_id_matches(self):
        """대조군 — state.json.run_id와 --run-id가 일치하면 init 성공, 외래 참조로 저장."""
        run_id = "run-20260914000000-deadbeef"
        self.ws.write_state(run_id=run_id)
        rc, stdout, data = run_tool(
            self.ws,
            ["init", "--task-path", str(self.ws.task_path), "--run-id", run_id],
        )
        self.assert_single_line_json(stdout)
        self.assertTrue(data.get("ok"), f"정상 init이 거부됐다: {data!r}")
        self.assertEqual(rc, 0)
        ledger_path = self.ws.task_path / ".oppl-run" / "runtime.json"
        self.assertTrue(ledger_path.exists(), "runtime.json이 생성되지 않았다")
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        self.assertEqual(ledger.get("run_id"), run_id, "run_id가 외래 참조로 저장되지 않았다")


if __name__ == "__main__":
    unittest.main()
