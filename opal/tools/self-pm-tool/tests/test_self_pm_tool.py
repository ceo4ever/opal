"""
@header {
  "module": "test_self_pm_tool",
  "task": "122",
  "layer": "test",
  "domain": "opal-tools",
  "description": "self-pm-tool(신설 예정) init/update/show 3서브명령 행위 계약 테스트 — TEST-SCENARIO.md S-5~S-8. 대상 모듈(opal/tools/self-pm-tool/self_pm_tool.py, run.sh)은 아직 존재하지 않으며, run.sh 부재로 인한 실패 자체가 RED 증거다(red-first.md, 작성자(opal-test-agent mode:red) != 구현자).",
  "scenarios": ["S-5", "S-6", "S-7", "S-8"],
  "exports": [
    "TestInitCreatesEightFieldSkeleton",
    "TestRejectionPaths",
    "TestNoSsotSideEffects"
  ]
}

[T122/mode:red] self-pm-tool `init`/`update`/`show` 서브명령 행위 계약
검증 대상: opal/tools/self-pm-tool/run.sh 의 공개 인터페이스(exit code + stdout JSON)만 단언.
내부 함수/private 결합 금지(red-first.md §2/§4) — subprocess 실호출만 사용, mock/patch/MagicMock 금지.
실 fixture(tempfile.mkdtemp() 임시 task_root)만 사용 — 실 저장소·배포본(~/.opal) 오염 금지.

PLAN.md D-8/W-3 근거 계약 (본 테스트가 확정하는 공개 인터페이스 — GREEN 구현은 이 계약을
그대로 만족해야 한다):
  - 공통: `--task-root <path>`(필수) — 모든 산출물은 `{task-root}/.opal/self-pm/` 밑에만 쓴다.
  - init  : `--task-root <path> --objective <text> [--run-id <id>]`
            → `{task-root}/.opal/self-pm/{run_id}.json`(run_id 미지정 시 도구가 생성) 신설.
            8필드(objective/status/decisions/open_questions/approved_scope/changed_files/
            validation/knowledge_impact) 스켈레톤을 모두 채우고 stdout에 최소
            `{"ok":true,"run_id":...}`를 보장한다.
  - update: `--task-root <path> --run-id <id> --status <value> [--run-dir <path>]`
            → status는 폐쇄 집합(discovering/awaiting_approval/executing/
            awaiting_confirmation/done) 값만 허용 — 그 외 값은 `{"ok":false,...}` + exit != 0.
  - show  : `--task-root <path> --run-id <id> [--run-dir <path>]`
            → 8필드 중 하나라도 결손된 파일이면 `{"ok":false,...}` + exit != 0.
  - `--run-dir <path>`(공용, 선택) — run 파일이 위치한 디렉토리를 직접 지정하는 저수준
    override(기본값은 `{task-root}/.opal/self-pm`). 해석된 경로가 `{task-root}` 밖이면
    `{"ok":false,...}` + exit != 0으로 거부해야 한다(경로 이탈 차단, S-6(c)).
  - 8필드 누락·미지 status·경로 이탈 모두 traceback 없이 JSON 에러로 거부한다.
  - `state.json`/`test-scenario.json`/`backlog.json` 경로를 읽지도 쓰지도 않는다(S-7).
"""

import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

# self-pm-tool 위치 — run.sh/self_pm_tool.py 모두 미구현(RED 단계에서는 파일 자체가 부재)
_TOOL_DIR = pathlib.Path(__file__).resolve().parent.parent
_RUN_SH = _TOOL_DIR / "run.sh"
_SELF_PM_TOOL_PY = _TOOL_DIR / "self_pm_tool.py"

REQUIRED_FIELDS = [
    "objective", "status", "decisions", "open_questions",
    "approved_scope", "changed_files", "validation", "knowledge_impact",
]

CLOSED_STATUS_SET = {
    "discovering", "awaiting_approval", "executing",
    "awaiting_confirmation", "done",
}

_SSOT_FILENAMES = ("state.json", "test-scenario.json", "backlog.json")


# ─────────────────────────────────────────────────────────────────────────────
# 공통 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _run(args):
    """run.sh를 subprocess로 실행하여 (returncode, stdout_text, stderr_text, parsed_json) 반환.
    run.sh 부재 시 bash가 자체 오류를 내며 비정상 종료한다(stdout 공백) — 이후 모든
    `assertIn("ok", data)` 단언이 그 자리에서 깨끗하게 실패하는 것이 RED 증거다."""
    cmd = ["bash", str(_RUN_SH)] + args
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, result.stderr, data


def _init(task_root, objective, run_id=None):
    args = ["init", "--task-root", str(task_root), "--objective", objective]
    if run_id is not None:
        args += ["--run-id", run_id]
    return _run(args)


def _update(task_root, run_id, status, run_dir=None):
    args = ["update", "--task-root", str(task_root), "--run-id", run_id, "--status", status]
    if run_dir is not None:
        args += ["--run-dir", str(run_dir)]
    return _run(args)


def _show(task_root, run_id, run_dir=None):
    args = ["show", "--task-root", str(task_root), "--run-id", run_id]
    if run_dir is not None:
        args += ["--run-dir", str(run_dir)]
    return _run(args)


def _valid_skeleton_doc(objective="테스트 목표"):
    return {
        "objective": objective,
        "status": "discovering",
        "decisions": [],
        "open_questions": [],
        "approved_scope": [],
        "changed_files": [],
        "validation": [],
        "knowledge_impact": [],
    }


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BaseSelfPmTestCase(unittest.TestCase):
    """임시 task_root 공통 베이스. 실 파일 생성·재읽기 — mock 금지(red-first.md §2/§4)."""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _new_task_root(self, name):
        p = self.tmpdir / name
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _write_run_file(self, task_root, run_id, doc):
        run_dir = task_root / ".opal" / "self-pm"
        run_dir.mkdir(parents=True, exist_ok=True)
        run_file = run_dir / f"{run_id}.json"
        run_file.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        return run_file


# ─────────────────────────────────────────────────────────────────────────────
# S-5: init --objective → show 8필드 스켈레톤 생성 확인 (AC-10)
# ─────────────────────────────────────────────────────────────────────────────

class TestInitCreatesEightFieldSkeleton(BaseSelfPmTestCase):
    """[T122/S-5] `init --objective` → `{task_root}/.opal/self-pm/{run_id}.json` 신설,
    8필드 전부 존재 + status 초기값이 폐쇄 집합 안."""

    def test_init_creates_run_file_with_eight_fields_and_valid_status(self):
        task_root = self._new_task_root("s5_init")
        code, stdout, stderr, data = _init(task_root, objective="PM 직접 수행 모델 self-pm 기록 검증")

        self.assertIn(
            "ok", data,
            f"stdout이 JSON 'ok' 계약을 지키지 않음(run.sh/self_pm_tool.py 미구현): "
            f"stdout={stdout!r} stderr={stderr!r}",
        )
        self.assertTrue(data.get("ok"), f"init 실패: {data!r}")
        self.assertEqual(code, 0, f"init은 exit 0이어야 한다: {data!r}")

        run_id = data.get("run_id")
        self.assertTrue(run_id, f"init 응답에 run_id가 없음: {data!r}")

        run_file = task_root / ".opal" / "self-pm" / f"{run_id}.json"
        self.assertTrue(run_file.exists(), f"{run_file} 가 생성되지 않음")

        doc = json.loads(run_file.read_text(encoding="utf-8"))
        for field in REQUIRED_FIELDS:
            self.assertIn(field, doc, f"필수 8필드 중 '{field}' 누락: {doc!r}")

        self.assertIn(
            doc.get("status"), CLOSED_STATUS_SET,
            f"status 초기값이 폐쇄 집합 밖: {doc.get('status')!r}",
        )


# ─────────────────────────────────────────────────────────────────────────────
# S-6: 3가지 거부 경로 — (a) 미지 status (b) 8필드 결손 파일 (c) task_root 밖 경로
# ─────────────────────────────────────────────────────────────────────────────

class TestRejectionPaths(BaseSelfPmTestCase):
    """[T122/S-6] 세 거부 경로 모두 `ok:false` JSON + exit != 0 + traceback 미출력."""

    def test_update_unknown_status_rejected(self):
        """(a) `update --status 존재하지않는값` → ok:false + exit != 0."""
        task_root = self._new_task_root("s6a")
        self._write_run_file(task_root, "fixture-run", _valid_skeleton_doc())

        code, stdout, stderr, data = _update(task_root, "fixture-run", status="존재하지않는상태값")

        self.assertIn(
            "ok", data,
            f"stdout이 JSON 'ok' 계약을 지키지 않음(미구현 가능성): stdout={stdout!r} stderr={stderr!r}",
        )
        self.assertFalse(data.get("ok"), f"미지 status 값이 거부되지 않음: {data!r}")
        self.assertNotEqual(code, 0, "미지 status는 exit 0이면 안 된다")
        self.assertNotIn("Traceback", stderr, f"traceback이 출력됨: {stderr!r}")

    def test_show_file_missing_one_of_eight_fields_rejected(self):
        """(b) 8필드 중 1개(knowledge_impact) 제거된 파일에 `show` → ok:false + exit != 0."""
        task_root = self._new_task_root("s6b")
        broken_doc = _valid_skeleton_doc()
        del broken_doc["knowledge_impact"]
        self._write_run_file(task_root, "broken-run", broken_doc)

        code, stdout, stderr, data = _show(task_root, "broken-run")

        self.assertIn(
            "ok", data,
            f"stdout이 JSON 'ok' 계약을 지키지 않음(미구현 가능성): stdout={stdout!r} stderr={stderr!r}",
        )
        self.assertFalse(data.get("ok"), f"8필드 결손 파일이 거부되지 않음: {data!r}")
        self.assertNotEqual(code, 0, "8필드 결손 파일은 exit 0이면 안 된다")
        self.assertNotIn("Traceback", stderr, f"traceback이 출력됨: {stderr!r}")

    def test_run_dir_outside_task_root_rejected(self):
        """(c) `--run-dir`가 `{task_root}` 밖 경로를 가리키면 ok:false + exit != 0
        (경로 이탈 차단 — 유효한 8필드 파일이 실존해도 거부되어야 한다)."""
        task_root = self._new_task_root("s6c_inside")
        outside_dir = self.tmpdir / "s6c_outside_escape"
        outside_dir.mkdir(parents=True, exist_ok=True)
        run_file = outside_dir / "escape-run.json"
        run_file.write_text(
            json.dumps(_valid_skeleton_doc(), ensure_ascii=False, indent=2), encoding="utf-8"
        )

        code, stdout, stderr, data = _show(task_root, "escape-run", run_dir=outside_dir)

        self.assertIn(
            "ok", data,
            f"stdout이 JSON 'ok' 계약을 지키지 않음(미구현 가능성): stdout={stdout!r} stderr={stderr!r}",
        )
        self.assertFalse(
            data.get("ok"),
            f"{{task_root}} 밖 --run-dir가 거부되지 않음(경로 이탈 허용 — 위반): {data!r}",
        )
        self.assertNotEqual(code, 0, "task_root 밖 --run-dir는 exit 0이면 안 된다")
        self.assertNotIn("Traceback", stderr, f"traceback이 출력됨: {stderr!r}")


# ─────────────────────────────────────────────────────────────────────────────
# S-7: SSOT 무접촉 — state.json/test-scenario.json/backlog.json grep 0건 +
#      init/update 실행 전후 세 SSOT 파일 해시 불변
# ─────────────────────────────────────────────────────────────────────────────

class TestNoSsotSideEffects(BaseSelfPmTestCase):
    """[T122/S-7] self-pm-tool은 state.json/test-scenario.json/backlog.json을
    읽지도 쓰지도 않는다 — 소스 grep 0건 + 실행 전후 SSOT 3파일 해시 불변."""

    def test_source_has_no_ssot_filename_references(self):
        """소스(self_pm_tool.py) 전체에서 세 SSOT 파일명이 0건 등장해야 한다.
        파일 자체가 아직 없으므로(RED-first, 구현자=EXECUTE 워커 담당) 이 단언은
        지금 실행하면 실패한다 — 이것이 S-7의 RED 증거다."""
        self.assertTrue(
            _SELF_PM_TOOL_PY.exists(),
            f"self_pm_tool.py가 아직 존재하지 않음(GREEN 이전 정상): {_SELF_PM_TOOL_PY}",
        )
        source = _SELF_PM_TOOL_PY.read_text(encoding="utf-8")
        hits = [name for name in _SSOT_FILENAMES if name in source]
        self.assertEqual(
            hits, [],
            f"self_pm_tool.py 소스에 SSOT 파일명 참조가 존재함(AC-10 위반): {hits!r}",
        )

    def test_init_and_update_leave_ssot_files_byte_identical(self):
        """task_root에 세 SSOT 파일을 실제로 배치한 뒤 init/update를 실행하고,
        실행 전후 해시가 완전히 동일해야 한다(읽기·쓰기 모두 없음)."""
        task_root = self._new_task_root("s7_ssot_untouched")
        ssot_paths = {}
        for name in _SSOT_FILENAMES:
            p = task_root / name
            p.write_text(f'{{"marker": "{name} 원본 — 절대 변경되면 안 됨"}}', encoding="utf-8")
            ssot_paths[name] = p

        before_hashes = {name: _sha256(p) for name, p in ssot_paths.items()}

        init_code, init_stdout, init_stderr, init_data = _init(
            task_root, objective="SSOT 무접촉 검증용 objective"
        )
        run_id = init_data.get("run_id") or "s7-fallback-run"
        if not init_data.get("ok"):
            # GREEN 이전에는 init 자체가 실패할 수 있다 — update 호출을 위해 run 파일을
            # 직접 마련해 두 명령(init 실패/성공 무관) 이후에도 SSOT 무접촉을 계속 확인한다.
            self._write_run_file(task_root, run_id, _valid_skeleton_doc())
        _update(task_root, run_id, status="executing")

        after_hashes = {name: _sha256(p) for name, p in ssot_paths.items()}

        self.assertEqual(
            before_hashes, after_hashes,
            "init/update 실행 전후 SSOT 3파일 해시가 달라짐(state.json/test-scenario.json/"
            "backlog.json에 손을 댔다는 뜻 — AC-10 위반)",
        )

        # 소스 자체 존재 + grep 0건은 test_source_has_no_ssot_filename_references가 담당한다.
        # 이 테스트는 지금(파일 부재) 시점에는 위 해시 불변 단언이 자명하게 참일 수 있으나,
        # test_source_has_no_ssot_filename_references가 같은 S-7 안에서 이미 RED를 보장한다.
        self.assertTrue(
            _SELF_PM_TOOL_PY.exists(),
            f"self_pm_tool.py가 아직 존재하지 않음(GREEN 이전 정상 — S-7 RED 증거 재확인): "
            f"{_SELF_PM_TOOL_PY}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
