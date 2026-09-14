"""
@header {
  "module": "test_run_identity",
  "task": "131",
  "layer": "test",
  "domain": "opal-tools",
  "description": "state-tool run identity(`run-start`) 계약 RED-first 테스트 — PLAN D8 / TEST-SCENARIO S-3. `run-start`가 `run-<UTC14>-<8hex>` id를 발급해 state.json.run_id에 기록하고 단일 라인 JSON으로 반환하며, 재호출 시 교체되고, `show --format json`에 통과하는지 검증한다. 하위호환 축: run_id 없는 기존 state.json이 validate를 계속 통과하고 required 8필드가 불변인지 고정한다. RED 상태(`run-start` 미구현) — 신규 계약 테스트는 FAIL 예상. GREEN 전환은 EXECUTE 구현 워커 담당(작성자!=구현자, red-first.md §2).",
  "scenarios": ["S-3"],
  "exports": ["TestT131RunStart", "TestT131RunIdBackwardCompat", "TestT131StateSchemaRunId"]
}

검증 대상: opal/tools/state-tool/run.sh 의 공개 인터페이스(exit code + stdout 단일 라인 JSON)와
실 파일 상태(state.json / schema/state.schema.json)만 단언한다.
내부 함수 mock/patch 금지(red-first.md §4) — subprocess 실호출만 사용한다.

[MUST] opal/core/references/harness/tool-output-contract.md: 모든 서브명령은 단일 라인 JSON + exit code.
[MUST] CONVENTIONS State 관리: state.json을 직접 편집하지 않는다 — 픽스처도 `state-tool init` 경유로만 만들고
       테스트는 읽기만 한다.
[MUST] TASK T-11(기존 규약 계승): 표준 라이브러리만 import.
"""

import datetime
import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
_RUN_SH = _TOOL_DIR / "run.sh"
_SCHEMA_PATH = _TOOL_DIR / "schema" / "state.schema.json"

# PLAN D8 — run_id 형식 계약
RUN_ID_PATTERN = re.compile(r"^run-[0-9]{14}-[0-9a-f]{8}$")

# PLAN D8 — required는 불변(run_id는 properties에만 추가)
REQUIRED_FIELDS_8 = [
    "task_id", "skill", "mode", "schema_version",
    "created_at", "updated_at", "current_status", "rows",
]


def _run(args):
    """run.sh subprocess 실호출 → (returncode, stdout_raw, parsed_json)."""
    proc = subprocess.run(
        ["bash", str(_RUN_SH)] + [str(a) for a in args],
        capture_output=True, text=True,
    )
    raw = proc.stdout
    stripped = raw.strip()
    try:
        data = json.loads(stripped) if stripped else {}
    except json.JSONDecodeError:
        data = {"_raw": stripped, "_stderr": proc.stderr}
    return proc.returncode, raw, data


class _TaskFolderCase(unittest.TestCase):
    """`state-tool init`으로만 state.json을 만드는 공통 픽스처."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="t131-runid-")
        self.task_path = pathlib.Path(self.tmp) / "001-260914-oppl-runid"
        self.task_path.mkdir(parents=True)
        rc, _, data = _run([
            "init", self.task_path,
            "--skill", "oppl", "--mode", "agentic",
            "--rows-spec", json.dumps([{"stage": "PLAN", "item": "작업"}]),
        ])
        self.assertEqual(rc, 0, f"픽스처 init 실패: {data}")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _state(self):
        return json.loads((self.task_path / "state.json").read_text(encoding="utf-8"))


class TestT131RunStart(_TaskFolderCase):
    """S-3 / PLAN D8 — `state-tool run-start <task-path>` 발급 계약."""

    def test_run_start_returns_single_line_json_ok(self):
        """run-start는 exit 0 + 단일 라인 JSON으로 run_id를 반환한다 (harness/tool-output-contract.md)."""
        rc, raw, data = _run(["run-start", self.task_path])
        self.assertEqual(rc, 0, f"run-start가 실패했다: {data}")
        self.assertEqual(
            raw.strip().count("\n"), 0,
            f"stdout이 단일 라인 JSON이 아니다: {raw!r}",
        )
        self.assertTrue(data.get("ok"), f"ok:true가 아니다: {data}")
        self.assertEqual(data.get("command"), "run-start")
        self.assertIn("run_id", data, f"반환 JSON에 run_id가 없다: {data}")

    def test_run_start_run_id_matches_contract_pattern(self):
        """run_id 형식은 `run-<UTC YYYYMMDDHHMMSS>-<8자리 hex>` (PLAN D8)."""
        _, _, data = _run(["run-start", self.task_path])
        run_id = data.get("run_id")
        self.assertIsInstance(run_id, str, f"run_id가 문자열이 아니다: {data}")
        self.assertRegex(run_id, RUN_ID_PATTERN)

    def test_run_start_timestamp_is_utc_now(self):
        """run_id의 14자리는 UTC 현재 시각이다 — 로컬 타임존 발급을 배제한다."""
        _, _, data = _run(["run-start", self.task_path])
        run_id = data.get("run_id", "")
        self.assertRegex(run_id, RUN_ID_PATTERN)
        stamp = datetime.datetime.strptime(run_id[4:18], "%Y%m%d%H%M%S").replace(
            tzinfo=datetime.timezone.utc
        )
        now = datetime.datetime.now(datetime.timezone.utc)
        self.assertLess(
            abs((now - stamp).total_seconds()), 300,
            f"run_id 타임스탬프가 UTC 현재 시각이 아니다: {run_id} vs {now}",
        )

    def test_run_start_persists_run_id_into_state_json(self):
        """발급된 run_id가 state.json.run_id에 기록된다."""
        _, _, data = _run(["run-start", self.task_path])
        state = self._state()
        self.assertIn("run_id", state, f"state.json에 run_id가 없다: {sorted(state)}")
        self.assertEqual(state["run_id"], data.get("run_id"))

    def test_run_start_replaces_previous_run_id(self):
        """재호출하면 새 id로 교체한다 — 현재 run은 항상 1개 (PLAN D8)."""
        _, _, first = _run(["run-start", self.task_path])
        first_id = first.get("run_id")
        _, _, second = _run(["run-start", self.task_path])
        second_id = second.get("run_id")

        self.assertRegex(str(first_id), RUN_ID_PATTERN)
        self.assertRegex(str(second_id), RUN_ID_PATTERN)
        self.assertNotEqual(first_id, second_id, "재호출인데 run_id가 교체되지 않았다")

        state = self._state()
        self.assertEqual(state.get("run_id"), second_id, "state.json이 최신 run_id로 교체되지 않았다")
        self.assertNotIn("run_ids", state, "현재 run은 1개여야 하는데 누적 목록이 생겼다")
        self.assertNotIn("runs", state, "현재 run은 1개여야 하는데 누적 목록이 생겼다")

    def test_show_json_passes_run_id_through(self):
        """`show --format json` 출력에 run_id가 통과한다 (S-3)."""
        _, _, started = _run(["run-start", self.task_path])
        self.assertRegex(
            str(started.get("run_id")), RUN_ID_PATTERN,
            f"전제 불충족 — run-start가 run_id를 발급하지 못했다: {started}",
        )
        rc, _, shown = _run(["show", self.task_path, "--format", "json"])
        self.assertEqual(rc, 0, f"show 실패: {shown}")
        self.assertTrue(shown.get("ok"), f"show ok:true가 아니다: {shown}")
        self.assertEqual(
            shown.get("data", {}).get("run_id"), started.get("run_id"),
            f"show 출력에 run_id가 통과하지 않았다: {shown.get('data', {}).keys()}",
        )

    def test_validate_ok_after_run_start(self):
        """run_id 기록 후에도 validate가 ok:true + violations 0이다 (additionalProperties 회귀 방어)."""
        _, _, started = _run(["run-start", self.task_path])
        self.assertRegex(
            str(started.get("run_id")), RUN_ID_PATTERN,
            f"전제 불충족 — run-start가 run_id를 발급하지 못했다: {started}",
        )
        self.assertIn("run_id", self._state(), "전제 불충족 — state.json에 run_id가 기록되지 않았다")
        rc, _, data = _run(["validate", self.task_path])
        self.assertEqual(rc, 0, f"run_id 기록 후 validate가 실패했다: {data}")
        self.assertTrue(data.get("ok"), f"ok:true가 아니다: {data}")
        self.assertEqual(
            data.get("violations"), [],
            f"run_id 때문에 violation이 생겼다: {data.get('violations')}",
        )


class TestT131RunIdBackwardCompat(_TaskFolderCase):
    """S-3 하위호환 축 — run_id 없는 기존 state.json은 계속 통과해야 한다."""

    def test_validate_ok_without_run_id(self):
        """run_id 없는 state.json이 validate를 계속 통과한다 (C-8 하위호환)."""
        state = self._state()
        self.assertNotIn("run_id", state, "픽스처 전제 위반: init이 run_id를 만들면 안 된다")
        rc, _, data = _run(["validate", self.task_path])
        self.assertEqual(rc, 0, f"run_id 없는 state.json validate 실패: {data}")
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("violations"), [])

    def test_show_ok_without_run_id(self):
        """run_id 없는 state.json도 show가 정상 렌더한다."""
        rc, _, data = _run(["show", self.task_path, "--format", "json"])
        self.assertEqual(rc, 0, f"show 실패: {data}")
        self.assertTrue(data.get("ok"))
        self.assertNotIn("run_id", data.get("data", {}))


class TestT131StateSchemaRunId(unittest.TestCase):
    """S-3 / PLAN D8 — state.schema.json 계약: properties 추가, required 불변."""

    def setUp(self):
        self.schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_schema_declares_run_id_property(self):
        """run_id가 properties에 선언된다 — root additionalProperties:false 하에서 필수."""
        self.assertIn(
            "run_id", self.schema.get("properties", {}),
            f"schema properties에 run_id가 없다: {sorted(self.schema.get('properties', {}))}",
        )

    def test_schema_run_id_is_pattern_constrained_string(self):
        """run_id property는 계약 정규식으로 구속된 string이다."""
        prop = self.schema.get("properties", {}).get("run_id", {})
        self.assertEqual(prop.get("type"), "string", f"run_id property 정의: {prop}")
        self.assertEqual(
            prop.get("pattern"), r"^run-[0-9]{14}-[0-9a-f]{8}$",
            f"run_id pattern이 D8 계약과 다르다: {prop.get('pattern')!r}",
        )

    def test_schema_required_stays_eight_fields(self):
        """required에는 run_id를 넣지 않는다 — 8필드 불변 (하위호환)."""
        self.assertEqual(self.schema.get("required"), REQUIRED_FIELDS_8)
        self.assertNotIn("run_id", self.schema.get("required", []))

    def test_schema_root_additional_properties_stays_false(self):
        """root additionalProperties:false는 유지된다 — 스키마 완화로 우회하지 않는다."""
        self.assertIs(self.schema.get("additionalProperties"), False)


if __name__ == "__main__":
    unittest.main()
