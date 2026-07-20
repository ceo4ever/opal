"""
@header {
  "module": "test_backlog_tool",
  "task": "056",
  "layer": "test",
  "domain": "opal-tools",
  "description": "backlog-tool 6서브명령(init/add-task/select-next/mark/done-check/show) 행위 계약 RED-first 테스트. RED 상태(미구현, run.sh/backlog_tool.py 부재) — 전부 FAIL 예상. GREEN 전환은 EXECUTE 구현 워커 담당(작성자≠구현자, red-first.md §2).",
  "scenarios": ["S-001", "S-002", "S-003", "S-004", "S-007", "S-006", "S-001b", "T069/S-1", "T069/S-2", "T069/S-3", "T069/S-4"],
  "exports": [
    "TestInit",
    "TestSelectNext",
    "TestMarkTransition",
    "TestDoneCheck",
    "TestResultContract",
    "TestBacklogMdMirror",
    "TestConcurrentMark",
    "TestUpdateTask",
    "TestCoverageCheckUncovered",
    "TestCoverageCheckIntegrationMissing",
    "TestCoverageCheckAllCovered",
    "TestCoversFieldRecordRenderCompat"
  ]
}

[T069] 069 태스크 추가분: covers 필드(add-task/update-task) + coverage-check 신규 서브명령
RED-first 테스트. `--covers`/`coverage-check`는 backlog_tool.py에 미구현 — 자연 RED 예상.
GREEN 전환은 EXECUTE 구현 워커 담당(작성자≠구현자, red-first.md §2). 기존 클래스는 불변.

[T056] backlog-tool 6서브명령 행위 계약 — RED-first TDD
검증 대상: opal/tools/backlog-tool/run.sh 의 공개 인터페이스(exit code + stdout JSON)만 단언.
내부 함수/private 결합 금지(red-first.md §4) — subprocess 실호출만 사용, mock/patch/MagicMock 금지.

PLAN.md §3.1 근거:
  - 6서브명령: init/add-task/select-next/mark/done-check/show
  - 에러코드: already_initialized/backlog_not_initialized/task_id_exists/task_not_found/
    invalid_status_transition/dependency_not_found/acceptance_invalid_json/date_tool_failed/
    task_path_not_found. exit 0=성공/1=검증위반/2=내부오류.
  - backlog.json: schema_version/project_title/mode/created_at/updated_at/goal/tasks[]
    tasks[]: id/title/slice/acceptance_criteria[]/area/priority/depends[]/status/
    parallel_group/created_at/done_at
"""

import json
import pathlib
import subprocess
import tempfile
import shutil
import unittest

# backlog-tool run.sh 위치 (미구현 — RED 단계에서는 파일 자체가 부재)
_TOOL_DIR = pathlib.Path(__file__).parent.parent
_RUN_SH = _TOOL_DIR / "run.sh"


# ─────────────────────────────────────────────────────────────────────────────
# 공통 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _run(args, cwd=None):
    """run.sh를 subprocess로 실행하여 (returncode, stdout_text, parsed_json) 반환.
    run.sh 부재 시 bash가 자체 오류를 내며 비정상 종료한다 — 이 역시 RED 증거다.
    """
    cmd = ["bash", str(_RUN_SH)] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, data


def _init(task_path, project_title="056 드라이런", mode="semi-agentic", goal="테스트 목표", extra=None):
    args = ["init", str(task_path), "--project-title", project_title, "--mode", mode, "--goal", goal]
    if extra:
        args += extra
    return _run(args)


def _add_task(task_path, task_id, title, slice_desc, acceptance, area, priority, depends=None):
    args = [
        "add-task", str(task_path),
        "--id", task_id,
        "--title", title,
        "--slice", slice_desc,
        "--acceptance", json.dumps(acceptance, ensure_ascii=False),
        "--area", area,
        "--priority", priority,
    ]
    if depends:
        args += ["--depends", ",".join(depends)]
    return _run(args)


def _mark(task_path, task_id, status, note=None):
    args = ["mark", str(task_path), "--id", task_id, "--status", status]
    if note:
        args += ["--note", note]
    return _run(args)


def _select_next(task_path):
    return _run(["select-next", str(task_path)])


def _done_check(task_path):
    return _run(["done-check", str(task_path)])


def _show(task_path, fmt=None):
    args = ["show", str(task_path)]
    if fmt:
        args += ["--format", fmt]
    return _run(args)


def _update_task(task_path, task_id, title=None, slice_desc=None, acceptance=None,
                  area=None, priority=None, depends=None, parallel_group=None):
    """update-task 호출 헬퍼 [T056/ADD3] — 지정된 필드만 CLI 인자로 전달."""
    args = ["update-task", str(task_path), "--id", task_id]
    if title is not None:
        args += ["--title", title]
    if slice_desc is not None:
        args += ["--slice", slice_desc]
    if acceptance is not None:
        args += ["--acceptance", json.dumps(acceptance, ensure_ascii=False)]
    if area is not None:
        args += ["--area", area]
    if priority is not None:
        args += ["--priority", priority]
    if depends is not None:
        args += ["--depends", ",".join(depends)]
    if parallel_group is not None:
        args += ["--parallel-group", parallel_group]
    return _run(args)


def _seed_two_tasks(task_path):
    """T01(P0, depends=[])·T02(P1, depends=[T01]) fixture 생성 (§2.2 S-002/S-003/S-004 공용)."""
    _init(task_path)
    _add_task(task_path, "T01", "T01 제목", "T01 슬라이스", ["AC1"], "be", "P0")
    _add_task(task_path, "T02", "T02 제목", "T02 슬라이스", ["AC2"], "be", "P1", depends=["T01"])


class BaseBacklogTestCase(unittest.TestCase):
    """임시 태스크 폴더 공통 베이스. 실 파일 생성·재읽기 — mock 금지(red-first.md §4)."""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.task_path = self.tmpdir / "056-dryrun"
        self.task_path.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _backlog_json(self):
        with open(self.task_path / "backlog.json", encoding="utf-8") as f:
            return json.load(f)


# ─────────────────────────────────────────────────────────────────────────────
# S-001: backlog-tool init 멱등·생성 계약 [T056/L1-F001]
# ─────────────────────────────────────────────────────────────────────────────

class TestInit(BaseBacklogTestCase):
    """[T056/L1-F001] backlog-tool init 멱등·생성 계약 — S-001 (H-5, H-6 연계)"""

    def test_init_creates_backlog_json_and_md(self):
        """Given: 빈 임시 태스크 폴더. When: init 1회차.
        Then: backlog.json + BACKLOG.md 생성, exit 0, ok true."""
        code, stdout, data = _init(self.task_path)
        self.assertEqual(code, 0)
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("command"), "init")
        self.assertTrue((self.task_path / "backlog.json").exists())
        self.assertTrue((self.task_path / "BACKLOG.md").exists())
        backlog = self._backlog_json()
        self.assertEqual(backlog.get("tasks"), [])
        self.assertIn("schema_version", backlog)
        self.assertIn("project_title", backlog)
        self.assertIn("mode", backlog)
        self.assertIn("goal", backlog)

    def test_init_twice_rejects_with_already_initialized(self):
        """When: init 2회차(동일 경로). Then: already_initialized exit 1."""
        first_code, _, _ = _init(self.task_path)
        self.assertEqual(first_code, 0)
        code, stdout, data = _init(self.task_path)
        self.assertEqual(code, 1)
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "already_initialized")

    def test_init_stdout_is_single_line(self):
        """stdout은 단일라인 JSON이어야 한다 (H-5)."""
        _, stdout, _ = _init(self.task_path)
        self.assertEqual(len(stdout.splitlines()), 1)


# ─────────────────────────────────────────────────────────────────────────────
# S-002: select-next 의존·우선순위 규칙 [T056/L1-F001]
# ─────────────────────────────────────────────────────────────────────────────

class TestSelectNext(BaseBacklogTestCase):
    """[T056/L1-F001] select-next 의존·우선순위 규칙 — S-002 (H-5)"""

    def test_returns_highest_priority_pending_with_depends_met(self):
        """Given: T01(P0,depends=[])·T02(P1,depends=[T01]).
        When: select-next. Then: T01 반환 (T02는 depends 미충족 → 스킵)."""
        _seed_two_tasks(self.task_path)
        code, stdout, data = _select_next(self.task_path)
        self.assertEqual(code, 0)
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("next_task_id"), "T01")

    def test_returns_dependent_task_after_dependency_done(self):
        """When: T01 done 처리 후 재호출. Then: T02 반환 (depends 충족)."""
        _seed_two_tasks(self.task_path)
        mcode, _, _ = _mark(self.task_path, "T01", "in_progress")
        self.assertEqual(mcode, 0)
        mcode, _, _ = _mark(self.task_path, "T01", "done")
        self.assertEqual(mcode, 0)
        code, stdout, data = _select_next(self.task_path)
        self.assertEqual(code, 0)
        self.assertEqual(data.get("next_task_id"), "T02")

    def test_returns_null_when_exhausted(self):
        """When: 전 태스크 done 후 재호출. Then: next_task_id null."""
        _seed_two_tasks(self.task_path)
        for tid in ("T01", "T02"):
            _mark(self.task_path, tid, "in_progress")
            _mark(self.task_path, tid, "done")
        code, stdout, data = _select_next(self.task_path)
        self.assertEqual(code, 0)
        self.assertIsNone(data.get("next_task_id"))


# ─────────────────────────────────────────────────────────────────────────────
# S-003: mark 상태 전이 가드 [T056/L1-F001]
# ─────────────────────────────────────────────────────────────────────────────

class TestMarkTransition(BaseBacklogTestCase):
    """[T056/L1-F001] mark 상태 전이 가드 — S-003 (H-5)"""

    def setUp(self):
        super().setUp()
        _init(self.task_path)
        _add_task(self.task_path, "T01", "T01 제목", "T01 슬라이스", ["AC1"], "be", "P0")

    def test_valid_transition_pending_to_in_progress_to_done(self):
        """유효 전이: pending→in_progress→done. done 시 done_at 기록."""
        code, _, data = _mark(self.task_path, "T01", "in_progress")
        self.assertEqual(code, 0)
        self.assertEqual(data.get("status"), "in_progress")

        code, _, data = _mark(self.task_path, "T01", "done")
        self.assertEqual(code, 0)
        self.assertEqual(data.get("status"), "done")

        backlog = self._backlog_json()
        task = next(t for t in backlog["tasks"] if t["id"] == "T01")
        self.assertEqual(task["status"], "done")
        self.assertIsNotNone(task.get("done_at"))

    def test_invalid_transition_done_to_pending_rejected(self):
        """무효 전이: done→pending. Then: invalid_status_transition exit 1."""
        _mark(self.task_path, "T01", "in_progress")
        _mark(self.task_path, "T01", "done")
        code, stdout, data = _mark(self.task_path, "T01", "pending")
        self.assertEqual(code, 1)
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "invalid_status_transition")


# ─────────────────────────────────────────────────────────────────────────────
# S-004: done-check 종료 판정 [T056/L1-F001]
# ─────────────────────────────────────────────────────────────────────────────

class TestDoneCheck(BaseBacklogTestCase):
    """[T056/L1-F001] done-check 종료 판정 — S-004 (H-5, H-7 종료 판정 입력)"""

    def test_all_done_false_with_remaining(self):
        """Given: T01 done·T02 pending. When: done-check.
        Then: all_done:false, remaining=[T02]."""
        _seed_two_tasks(self.task_path)
        _mark(self.task_path, "T01", "in_progress")
        _mark(self.task_path, "T01", "done")

        code, stdout, data = _done_check(self.task_path)
        self.assertEqual(code, 0)
        self.assertFalse(data.get("all_done"))
        self.assertIn("T02", data.get("remaining", []))

    def test_all_done_true_when_all_tasks_done(self):
        """When: T02도 done 처리 후 재호출. Then: all_done:true."""
        _seed_two_tasks(self.task_path)
        for tid in ("T01", "T02"):
            _mark(self.task_path, tid, "in_progress")
            _mark(self.task_path, tid, "done")

        code, stdout, data = _done_check(self.task_path)
        self.assertEqual(code, 0)
        self.assertTrue(data.get("all_done"))
        self.assertEqual(data.get("remaining", []), [])


# ─────────────────────────────────────────────────────────────────────────────
# S-007 (backlog 몫): 도구 결과 계약 — 단일라인 JSON + exit code [T056/L1-F001]
# ─────────────────────────────────────────────────────────────────────────────

class TestResultContract(BaseBacklogTestCase):
    """[T056/L1-F001] backlog-tool 6서브명령 결과 계약 — S-007 (H-5)"""

    def _assert_single_line_json(self, stdout, data):
        self.assertEqual(len(stdout.splitlines()), 1, "stdout은 단일라인이어야 한다")
        self.assertNotIn("_raw", data, "stdout이 유효 JSON으로 파싱되지 않음")

    def test_init_success_and_error_contract(self):
        code, stdout, data = _init(self.task_path)
        self._assert_single_line_json(stdout, data)
        self.assertEqual(code, 0)
        self.assertIs(data.get("ok"), True)

        code, stdout, data = _init(self.task_path)  # 2회차 → 오류
        self._assert_single_line_json(stdout, data)
        self.assertEqual(code, 1)
        self.assertIs(data.get("ok"), False)
        self.assertIn("error", data)

    def test_add_task_success_and_error_contract(self):
        _init(self.task_path)
        code, stdout, data = _add_task(
            self.task_path, "T01", "제목", "슬라이스", ["AC1"], "be", "P0"
        )
        self._assert_single_line_json(stdout, data)
        self.assertEqual(code, 0)

        code, stdout, data = _add_task(
            self.task_path, "T01", "중복", "슬라이스", ["AC1"], "be", "P0"
        )  # 중복 id → task_id_exists
        self._assert_single_line_json(stdout, data)
        self.assertEqual(code, 1)
        self.assertEqual(data.get("error"), "task_id_exists")

    def test_select_next_success_and_notfound_contract(self):
        code, stdout, data = _select_next(self.task_path)  # backlog 미초기화
        self._assert_single_line_json(stdout, data)
        self.assertEqual(code, 1)
        self.assertEqual(data.get("error"), "backlog_not_initialized")

        _init(self.task_path)
        code, stdout, data = _select_next(self.task_path)
        self._assert_single_line_json(stdout, data)
        self.assertEqual(code, 0)

    def test_mark_success_and_error_contract(self):
        _init(self.task_path)
        _add_task(self.task_path, "T01", "제목", "슬라이스", ["AC1"], "be", "P0")

        code, stdout, data = _mark(self.task_path, "T99", "in_progress")  # 없는 id
        self._assert_single_line_json(stdout, data)
        self.assertEqual(code, 1)
        self.assertEqual(data.get("error"), "task_not_found")

        code, stdout, data = _mark(self.task_path, "T01", "in_progress")
        self._assert_single_line_json(stdout, data)
        self.assertEqual(code, 0)

    def test_done_check_contract(self):
        _init(self.task_path)
        code, stdout, data = _done_check(self.task_path)
        self._assert_single_line_json(stdout, data)
        self.assertEqual(code, 0)
        self.assertIn("all_done", data)
        self.assertIn("remaining", data)

    def test_show_contract(self):
        _init(self.task_path)
        code, stdout, data = _show(self.task_path, fmt="json")
        self.assertEqual(code, 0)
        self.assertIs(data.get("ok"), True)


# ─────────────────────────────────────────────────────────────────────────────
# S-006: BACKLOG.md 미러 ↔ backlog.json 정합 [T056/L2-F001]
# ─────────────────────────────────────────────────────────────────────────────

class TestBacklogMdMirror(BaseBacklogTestCase):
    """[T056/L2-F001] BACKLOG.md 미러 ↔ backlog.json 정합 — S-006 (H-6)"""

    def test_md_reflects_json_after_cud_chain(self):
        """Given: init→add-task→mark 연쇄. Then: 매 CUD 후 BACKLOG.md 표가
        backlog.json과 정합(태스크 수·상태 일치), 마커 구간 외 본문 보존."""
        _init(self.task_path)

        md_path = self.task_path / "BACKLOG.md"
        original_md = md_path.read_text(encoding="utf-8")
        # 마커 구간 외 커스텀 본문을 주입해 보존 여부를 검증
        custom_note = "\n\n## 커스텀 메모\n\n이 구간은 도구가 건드리지 않아야 한다.\n"
        md_path.write_text(original_md + custom_note, encoding="utf-8")

        _add_task(self.task_path, "T01", "T01 제목", "T01 슬라이스", ["AC1"], "be", "P0")
        md_after_add = md_path.read_text(encoding="utf-8")
        self.assertIn("커스텀 메모", md_after_add, "마커 구간 외 본문이 보존되어야 한다")
        self.assertIn("T01", md_after_add)

        _mark(self.task_path, "T01", "in_progress")
        _mark(self.task_path, "T01", "done")
        md_after_mark = md_path.read_text(encoding="utf-8")
        self.assertIn("커스텀 메모", md_after_mark, "mark 이후에도 커스텀 본문 보존")

        backlog = self._backlog_json()
        task_count_json = len(backlog["tasks"])
        done_count_json = sum(1 for t in backlog["tasks"] if t["status"] == "done")

        # BACKLOG.md 렌더 표가 json과 태스크 수·상태 정합
        code, stdout, show_data = _show(self.task_path, fmt="md")
        self.assertEqual(code, 0)
        self.assertEqual(task_count_json, 1)
        self.assertEqual(done_count_json, 1)


# ─────────────────────────────────────────────────────────────────────────────
# S-001b: backlog.json 동시 쓰기 무손상 [T056/L2-F001]
# ─────────────────────────────────────────────────────────────────────────────

class TestConcurrentMark(BaseBacklogTestCase):
    """[T056/L2-F001] backlog.json 동시 쓰기 무손상 — S-001b (H-3)"""

    def test_parallel_mark_no_silent_corruption(self):
        """Given: T01·T02 pending. When: mark 2건 동시(&) 실행.
        Then: backlog.json 유효 JSON 유지 + 두 상태 모두 반영(또는 명시적 락 에러 — 유실 없음)."""
        _seed_two_tasks(self.task_path)

        proc1 = subprocess.Popen(
            ["bash", str(_RUN_SH), "mark", str(self.task_path), "--id", "T01", "--status", "in_progress"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        proc2 = subprocess.Popen(
            ["bash", str(_RUN_SH), "mark", str(self.task_path), "--id", "T02", "--status", "in_progress"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        out1, _ = proc1.communicate(timeout=30)
        out2, _ = proc2.communicate(timeout=30)

        # backlog.json이 여전히 유효 JSON이어야 한다 (silent 손상 금지)
        backlog_path = self.task_path / "backlog.json"
        self.assertTrue(backlog_path.exists())
        with open(backlog_path, encoding="utf-8") as f:
            backlog = json.load(f)  # JSONDecodeError 시 손상 — RED/실패 증거

        statuses = {t["id"]: t["status"] for t in backlog["tasks"]}
        # 양쪽 반영(둘 다 in_progress) 또는 최소 하나는 명시적 락 에러(exit!=0)로 처리되어야 하며
        # pending 상태로 되돌아간(유실) 경우는 없어야 한다.
        for tid in ("T01", "T02"):
            self.assertNotEqual(statuses.get(tid), None, f"{tid} 상태가 backlog.json에서 사라짐(유실)")

        json1 = json.loads(out1.strip()) if out1.strip() else {}
        json2 = json.loads(out2.strip()) if out2.strip() else {}
        # 두 프로세스 모두 성공(0) 이거나, 실패한 쪽은 명시적 에러코드를 반환해야 한다(silent 실패 금지)
        for jd in (json1, json2):
            self.assertIn("ok", jd)


# ─────────────────────────────────────────────────────────────────────────────
# ADD-3: update-task — tool-gated 태스크 속성 수정 [T056/ADD3]
# ─────────────────────────────────────────────────────────────────────────────

class TestUpdateTask(BaseBacklogTestCase):
    """[T056/ADD3] update-task 신규 서브명령 — Evaluator 지적 반영 경로(손편집 금지 대체).
    배경: 056 드라이런 QA-SPEC.md에서 evaluator가 T01 acceptance 경로 불일치를 지적했으나
    backlog-tool에 수정 명령이 없어 재등록 외 방법이 없었다. tool-gated 수정 경로를 신설한다."""

    def setUp(self):
        super().setUp()
        _init(self.task_path)
        _add_task(self.task_path, "T01", "T01 원래 제목", "T01 원래 슬라이스", ["bash src/hello.sh World"], "be", "P0")
        _add_task(self.task_path, "T02", "T02 제목", "T02 슬라이스", ["AC2"], "be", "P1")

    def test_update_task_applies_fields_and_rerenders_backlog_md(self):
        """Given: T01 존재. When: --title/--acceptance 갱신.
        Then: backlog.json 반영 + updated_at 갱신 + BACKLOG.md 마커 영역 재렌더."""
        before = self._backlog_json()
        before_updated_at = before["updated_at"]

        code, stdout, data = _update_task(
            self.task_path, "T01",
            title="T01 수정된 제목",
            acceptance=["bash dryrun/src/hello.sh World"],
        )
        self.assertEqual(code, 0)
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("command"), "update-task")
        self.assertEqual(data.get("task_id"), "T01")

        after = self._backlog_json()
        task = next(t for t in after["tasks"] if t["id"] == "T01")
        self.assertEqual(task["title"], "T01 수정된 제목")
        self.assertEqual(task["acceptance_criteria"], ["bash dryrun/src/hello.sh World"])
        # 미지정 필드는 불변
        self.assertEqual(task["slice"], "T01 원래 슬라이스")
        self.assertEqual(task["area"], "be")
        self.assertEqual(task["priority"], "P0")
        self.assertIsNotNone(after["updated_at"])

        md = (self.task_path / "BACKLOG.md").read_text(encoding="utf-8")
        self.assertIn("T01 수정된 제목", md)
        self.assertNotIn("T01 원래 제목", md)

    def test_update_task_rejects_when_no_fields_given(self):
        """When: 갱신 필드 없이 --id만 호출. Then: no_fields_to_update exit 1."""
        code, stdout, data = _update_task(self.task_path, "T01")
        self.assertEqual(code, 1)
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "no_fields_to_update")

        # 원본 불변
        task = next(t for t in self._backlog_json()["tasks"] if t["id"] == "T01")
        self.assertEqual(task["title"], "T01 원래 제목")

    def test_update_task_rejects_when_task_already_done(self):
        """Given: T01 done 상태. When: update-task 시도. Then: task_already_done exit 1."""
        _mark(self.task_path, "T01", "in_progress")
        mcode, _, _ = _mark(self.task_path, "T01", "done")
        self.assertEqual(mcode, 0)

        code, stdout, data = _update_task(self.task_path, "T01", title="새 제목 시도")
        self.assertEqual(code, 1)
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "task_already_done")

        task = next(t for t in self._backlog_json()["tasks"] if t["id"] == "T01")
        self.assertEqual(task["title"], "T01 원래 제목")

    def test_update_task_rejects_unknown_depends_target(self):
        """When: --depends에 존재하지 않는 id 지정. Then: dependency_not_found exit 1(기존 에러코드 재사용)."""
        code, stdout, data = _update_task(self.task_path, "T02", depends=["T99"])
        self.assertEqual(code, 1)
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "dependency_not_found")

        task = next(t for t in self._backlog_json()["tasks"] if t["id"] == "T02")
        self.assertEqual(task.get("depends") or [], [])



# ─────────────────────────────────────────────────────────────────────────────
# [T069] covers 필드 + coverage-check 게이트 신규 서브명령 RED-first 테스트
# 검증 대상: opal/tools/backlog-tool/run.sh 공개 인터페이스(exit code + stdout JSON)만
# 단언 — 내부 함수 직접 import 금지(red-first.md §4). PLAN.md §3.3.2/§3.4.2 근거.
# `--covers`/`coverage-check`는 현재 backlog_tool.py에 미구현 — 자연 RED 예상.
# 기존 클래스(TestInit~TestUpdateTask)는 수정하지 않았다 — 아래 클래스만 신규 추가.
# ─────────────────────────────────────────────────────────────────────────────

def _add_task_covers(task_path, task_id, title, slice_desc, acceptance, area, priority,
                      covers=None, depends=None, parallel_group=None):
    """add-task 호출 헬퍼(covers 포함) [T069] — 기존 `_add_task`는 불변, 신규 헬퍼로 분리."""
    args = [
        "add-task", str(task_path),
        "--id", task_id,
        "--title", title,
        "--slice", slice_desc,
        "--acceptance", json.dumps(acceptance, ensure_ascii=False),
        "--area", area,
        "--priority", priority,
    ]
    if covers is not None:
        args += ["--covers", covers if isinstance(covers, str) else json.dumps(covers, ensure_ascii=False)]
    if depends:
        args += ["--depends", ",".join(depends)]
    if parallel_group:
        args += ["--parallel-group", parallel_group]
    return _run(args)


def _update_task_covers(task_path, task_id, covers):
    """update-task 호출 헬퍼(covers 갱신) [T069]."""
    args = [
        "update-task", str(task_path), "--id", task_id,
        "--covers", covers if isinstance(covers, str) else json.dumps(covers, ensure_ascii=False),
    ]
    return _run(args)


def _coverage_check(task_path, surfaces_path):
    """coverage-check 신규 서브명령 호출 헬퍼 [T069] (PLAN §3.4.2)."""
    return _run(["coverage-check", str(task_path), "--surfaces", str(surfaces_path)])


def _write_surfaces_fixture(dest_dir):
    """fixture-A: 표면 3종(auth-login:auth none, agents/budgets:auth required) +
    origins.dev 선언 — TEST-SCENARIO.md §2.1 fixture-A 재현."""
    surfaces = {
        "origins": ["https://app.dev"],
        "surfaces": [
            {"id": "auth-login", "auth": "none"},
            {"id": "agents", "auth": "required"},
            {"id": "budgets", "auth": "required"},
        ],
    }
    path = pathlib.Path(dest_dir) / "surfaces.json"
    path.write_text(json.dumps(surfaces, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


class TestCoverageCheckUncovered(BaseBacklogTestCase):
    """[T069/S-1] coverage-check 미커버 표면 거부 (H-1). fixture-A + fixture-B1
    (T01만 auth-login 커버, agents·budgets 미커버)."""

    def test_coverage_check_rejects_uncovered_surfaces(self):
        surfaces_path = _write_surfaces_fixture(self.tmpdir)
        _init(self.task_path)
        code, _, _ = _add_task_covers(
            self.task_path, "T01", "T01 제목", "T01 슬라이스", ["AC1"], "be", "P0",
            covers=["auth-login"],
        )
        self.assertEqual(code, 0, "fixture-B1 준비 단계(add-task --covers)부터 실패 — RED 증거")

        code, stdout, data = _coverage_check(self.task_path, surfaces_path)
        self.assertEqual(code, 1)
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "surface_uncovered")
        self.assertEqual(sorted(data.get("uncovered", [])), ["agents", "budgets"])


class TestCoverageCheckIntegrationMissing(BaseBacklogTestCase):
    """[T069/S-2] coverage-check 통합 태스크 부재 거부 (H-2). fixture-B2:
    T01~T03(covers 전수)+parallel_group=g1, area=통합 태스크 부재."""

    def test_coverage_check_rejects_missing_integration_task(self):
        surfaces_path = _write_surfaces_fixture(self.tmpdir)
        _init(self.task_path)
        _add_task_covers(self.task_path, "T01", "T01", "S1", ["AC1"], "be", "P0",
                          covers=["auth-login"], parallel_group="g1")
        _add_task_covers(self.task_path, "T02", "T02", "S2", ["AC2"], "be", "P1",
                          covers=["agents"], parallel_group="g1")
        _add_task_covers(self.task_path, "T03", "T03", "S3", ["AC3"], "be", "P1",
                          covers=["budgets"], parallel_group="g1")

        code, stdout, data = _coverage_check(self.task_path, surfaces_path)
        self.assertEqual(code, 1)
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "integration_task_missing")


class TestCoverageCheckAllCovered(BaseBacklogTestCase):
    """[T069/S-3] coverage-check 전 표면 커버 + 통합 태스크 존재 → 통과 (H-1 통과 경로).
    fixture-B3: fixture-B2 + T04(area:통합)."""

    def test_coverage_check_passes_when_all_covered_and_integration_present(self):
        surfaces_path = _write_surfaces_fixture(self.tmpdir)
        _init(self.task_path)
        _add_task_covers(self.task_path, "T01", "T01", "S1", ["AC1"], "be", "P0",
                          covers=["auth-login"], parallel_group="g1")
        _add_task_covers(self.task_path, "T02", "T02", "S2", ["AC2"], "be", "P1",
                          covers=["agents"], parallel_group="g1")
        _add_task_covers(self.task_path, "T03", "T03", "S3", ["AC3"], "be", "P1",
                          covers=["budgets"], parallel_group="g1")
        _add_task_covers(self.task_path, "T04", "T04 통합", "통합 슬라이스", ["AC4"], "통합", "P1")

        code, stdout, data = _coverage_check(self.task_path, surfaces_path)
        self.assertEqual(code, 0)
        self.assertTrue(data.get("ok"))
        self.assertTrue(data.get("all_covered"))
        self.assertEqual(data.get("surface_count"), 3)


class TestCoversFieldRecordRenderCompat(BaseBacklogTestCase):
    """[T069/S-4] covers 필드 기록·BACKLOG.md 렌더·update-task 갱신·하위 호환(H-5)."""

    def test_add_task_covers_recorded_and_rendered(self):
        """① add-task --covers 기록 → backlog.json covers[] + BACKLOG.md 렌더."""
        _init(self.task_path)
        code, stdout, data = _add_task_covers(
            self.task_path, "T01", "T01 제목", "T01 슬라이스", ["AC1"], "be", "P0",
            covers=["auth-login"],
        )
        self.assertEqual(code, 0)
        self.assertTrue(data.get("ok"))

        backlog = self._backlog_json()
        task = next(t for t in backlog["tasks"] if t["id"] == "T01")
        self.assertEqual(task.get("covers"), ["auth-login"])

        md = (self.task_path / "BACKLOG.md").read_text(encoding="utf-8")
        self.assertIn("auth-login", md)

    def test_add_task_without_covers_defaults_empty_list(self):
        """② --covers 미지정 시 covers==[] 정상 동작(하위 호환, H-5)."""
        _init(self.task_path)
        code, stdout, data = _add_task_covers(
            self.task_path, "T02", "T02 제목", "T02 슬라이스", ["AC2"], "be", "P1",
        )
        self.assertEqual(code, 0)
        self.assertTrue(data.get("ok"))

        backlog = self._backlog_json()
        task = next(t for t in backlog["tasks"] if t["id"] == "T02")
        self.assertEqual(task.get("covers"), [])

    def test_update_task_covers_updates_existing(self):
        """③ update-task --covers로 covers 갱신."""
        _init(self.task_path)
        _add_task_covers(self.task_path, "T03", "T03 제목", "T03 슬라이스", ["AC3"], "be", "P1",
                          covers=["auth-login"])

        code, stdout, data = _update_task_covers(self.task_path, "T03", ["agents", "budgets"])
        self.assertEqual(code, 0)
        self.assertTrue(data.get("ok"))

        backlog = self._backlog_json()
        task = next(t for t in backlog["tasks"] if t["id"] == "T03")
        self.assertEqual(sorted(task.get("covers", [])), ["agents", "budgets"])

    def test_add_task_covers_invalid_json_rejected(self):
        """④ covers 잘못된 JSON → covers_invalid_json exit 1."""
        _init(self.task_path)
        code, stdout, data = _add_task_covers(
            self.task_path, "T04", "T04 제목", "T04 슬라이스", ["AC4"], "be", "P1",
            covers="{not-valid-json",
        )
        self.assertEqual(code, 1)
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "covers_invalid_json")


if __name__ == "__main__":
    unittest.main(verbosity=2)
