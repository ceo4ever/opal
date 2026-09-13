"""
@header {
  "module": "test_backlog_header_sync",
  "task": "131",
  "layer": "test",
  "domain": "opal-tools",
  "description": "BACKLOG.md 머리말 `최종 갱신` 동기화 계약 RED-first 테스트 — PLAN W-4 / TEST-SCENARIO S-22. `_rerender_backlog_md` 경로(add-task / mark / update-task)가 마커 영역 교체와 함께 머리말 라인도 backlog.json.updated_at으로 치환하는지, 머리말 라인이 없는 기존 파일은 삽입 없이 무변경 통과하는지, `--force` 재생성 경로의 머리말 처리가 무엇인지 고정한다. RED 상태(재렌더가 마커 영역만 교체) — 동기화 테스트는 FAIL 예상. GREEN 전환은 EXECUTE 구현 워커 담당(작성자!=구현자, red-first.md §2).",
  "scenarios": ["S-22"],
  "exports": ["TestT131HeaderSyncOnRerender", "TestT131HeaderAbsentBackwardCompat", "TestT131ForceRegenerationHeader"]
}

검증 대상: opal/tools/backlog-tool/run.sh 의 공개 인터페이스(exit code + stdout JSON)와
실 파일 상태(BACKLOG.md / backlog.json)만 단언한다.
내부 함수 mock/patch 금지(red-first.md §4) — subprocess 실호출만 사용한다.

머리말 포맷 SSOT: `_build_new_backlog_md`가 내는 `> 최종 갱신: {updated_at}` 한 줄.
재렌더 경로가 같은 포맷을 재사용하는지를 "바이트 동일" 단언으로 고정한다 —
포맷 문자열이 두 번째로 복제되면 이 단언이 드리프트를 잡는다.

[MUST] BACKLOG.md는 backlog.json의 파생 뷰다. 픽스처에서만 "기존 파일" 상황을 만들기 위해
       머리말 타임스탬프를 낡은 값으로 되돌려 쓴다. backlog.json은 도구 경유로만 조작한다.
[MUST] 표준 라이브러리만 import.
"""

import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
_RUN_SH = _TOOL_DIR / "run.sh"

HEADER_PREFIX = "> 최종 갱신: "
STALE_STAMP = "2000-01-01 00:00"
MARKER_START = "<!-- backlog:start -->"
MARKER_END = "<!-- backlog:end -->"

# 마커 밖 자유 서술 — 재렌더 경로가 보존해야 하는 사용자 텍스트
FREE_TEXT = "## 운영 메모\n사람이 직접 쓴 보존 대상 텍스트\n"


def _run(args):
    """run.sh subprocess 실호출 → (returncode, parsed_json)."""
    proc = subprocess.run(
        ["bash", str(_RUN_SH)] + [str(a) for a in args],
        capture_output=True, text=True,
    )
    stripped = proc.stdout.strip()
    try:
        data = json.loads(stripped) if stripped else {}
    except json.JSONDecodeError:
        data = {"_raw": stripped, "_stderr": proc.stderr}
    return proc.returncode, data


class _BacklogCase(unittest.TestCase):
    """init + add-task 1건으로 만든 공통 픽스처."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="t131-backlog-")
        self.task_path = pathlib.Path(self.tmp) / "002-260914-oppl-backlog"
        self.task_path.mkdir(parents=True)
        self.md_path = self.task_path / "BACKLOG.md"
        self.json_path = self.task_path / "backlog.json"

        rc, data = _run([
            "init", self.task_path,
            "--project-title", "파일럿", "--mode", "agentic", "--goal", "목표",
        ])
        self.assertEqual(rc, 0, f"픽스처 init 실패: {data}")

        rc, data = _run([
            "add-task", self.task_path,
            "--id", "T-1", "--title", "첫 태스크", "--slice", "슬라이스",
            "--acceptance", json.dumps(["AC-1"]),
            "--area", "be", "--priority", "P1",
        ])
        self.assertEqual(rc, 0, f"픽스처 add-task 실패: {data}")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ── 헬퍼 ─────────────────────────────────────────────────────────────
    def _md(self):
        return self.md_path.read_text(encoding="utf-8")

    def _backlog(self):
        return json.loads(self.json_path.read_text(encoding="utf-8"))

    def _header_lines(self, md=None):
        text = self._md() if md is None else md
        return [ln for ln in text.splitlines() if ln.startswith(HEADER_PREFIX)]

    def _make_header_stale(self):
        """머리말 타임스탬프만 낡은 값으로 되돌려 '기존 파일' 상황을 만든다."""
        md = self._md()
        stale = re.sub(
            rf"^{re.escape(HEADER_PREFIX)}.*$",
            f"{HEADER_PREFIX}{STALE_STAMP}",
            md, count=1, flags=re.MULTILINE,
        )
        self.assertNotEqual(stale, md, "픽스처 전제 위반: 머리말 라인을 찾지 못했다")
        self.md_path.write_text(stale, encoding="utf-8")
        self.assertEqual(self._header_lines(), [f"{HEADER_PREFIX}{STALE_STAMP}"])

    def _append_free_text(self):
        self.md_path.write_text(self._md().rstrip("\n") + "\n\n" + FREE_TEXT, encoding="utf-8")

    def _assert_header_matches_json(self):
        """머리말 라인이 backlog.json.updated_at과 정확히 일치하고, 포맷 SSOT와 바이트 동일하다."""
        updated_at = self._backlog()["updated_at"]
        lines = self._header_lines()
        self.assertEqual(len(lines), 1, f"머리말 라인이 1개가 아니다: {lines}")
        self.assertEqual(
            lines[0], f"{HEADER_PREFIX}{updated_at}",
            f"머리말이 backlog.json.updated_at({updated_at})과 다르다: {lines[0]!r}",
        )
        self.assertNotIn(STALE_STAMP, self._md(), "낡은 타임스탬프가 잔존한다")


class TestT131HeaderSyncOnRerender(_BacklogCase):
    """S-22 / PLAN W-4 — add-task·mark·update-task 세 경로 모두 머리말을 동기화한다."""

    def test_add_task_syncs_header(self):
        """add-task 재렌더가 머리말을 updated_at으로 치환한다."""
        self._make_header_stale()
        rc, data = _run([
            "add-task", self.task_path,
            "--id", "T-2", "--title", "둘째", "--slice", "슬라이스",
            "--acceptance", json.dumps(["AC-2"]),
            "--area", "fe", "--priority", "P2",
        ])
        self.assertEqual(rc, 0, f"add-task 실패: {data}")
        self._assert_header_matches_json()

    def test_mark_syncs_header(self):
        """mark 재렌더가 머리말을 updated_at으로 치환한다."""
        self._make_header_stale()
        rc, data = _run(["mark", self.task_path, "--id", "T-1", "--status", "in_progress"])
        self.assertEqual(rc, 0, f"mark 실패: {data}")
        self._assert_header_matches_json()

    def test_update_task_syncs_header(self):
        """update-task 재렌더가 머리말을 updated_at으로 치환한다."""
        self._make_header_stale()
        rc, data = _run(["update-task", self.task_path, "--id", "T-1", "--title", "제목 변경"])
        self.assertEqual(rc, 0, f"update-task 실패: {data}")
        self._assert_header_matches_json()

    def test_rerender_preserves_free_text_outside_markers(self):
        """머리말 치환이 마커 밖 자유 서술을 파괴하지 않는다 (재생성으로 우회 금지)."""
        self._append_free_text()
        self._make_header_stale()
        rc, data = _run(["mark", self.task_path, "--id", "T-1", "--status", "in_progress"])
        self.assertEqual(rc, 0, f"mark 실패: {data}")
        self._assert_header_matches_json()
        self.assertIn(
            FREE_TEXT.strip(), self._md(),
            "머리말 동기화가 마커 밖 자유 서술을 지웠다 — 재렌더가 아니라 재생성으로 구현됐다",
        )

    def test_rerender_does_not_duplicate_header_line(self):
        """동기화가 머리말 라인을 중복 삽입하지 않는다."""
        self._make_header_stale()
        for status in ("in_progress", "done"):
            rc, data = _run(["mark", self.task_path, "--id", "T-1", "--status", status])
            self.assertEqual(rc, 0, f"mark {status} 실패: {data}")
        self.assertEqual(len(self._header_lines()), 1, f"머리말 중복: {self._header_lines()}")


class TestT131HeaderAbsentBackwardCompat(_BacklogCase):
    """S-22 하위호환 축 — 머리말 라인이 없는 기존 파일은 삽입 없이 무변경 통과한다."""

    def _strip_header_line(self):
        md = self._md()
        kept = [ln for ln in md.splitlines() if not ln.startswith(HEADER_PREFIX)]
        self.md_path.write_text("\n".join(kept) + "\n", encoding="utf-8")
        self.assertEqual(self._header_lines(), [], "픽스처 전제 위반: 머리말이 남아있다")

    def test_add_task_does_not_insert_header(self):
        """머리말 없는 파일에 add-task — 머리말을 삽입하지 않는다."""
        self._strip_header_line()
        rc, data = _run([
            "add-task", self.task_path,
            "--id", "T-9", "--title", "추가", "--slice", "슬라이스",
            "--acceptance", json.dumps(["AC-9"]),
            "--area", "be", "--priority", "P2",
        ])
        self.assertEqual(rc, 0, f"add-task 실패: {data}")
        self.assertEqual(self._header_lines(), [], f"머리말이 삽입됐다: {self._header_lines()}")

    def test_mark_does_not_insert_header(self):
        """머리말 없는 파일에 mark — 머리말을 삽입하지 않는다."""
        self._strip_header_line()
        rc, data = _run(["mark", self.task_path, "--id", "T-1", "--status", "in_progress"])
        self.assertEqual(rc, 0, f"mark 실패: {data}")
        self.assertEqual(self._header_lines(), [], f"머리말이 삽입됐다: {self._header_lines()}")

    def test_update_task_does_not_insert_header(self):
        """머리말 없는 파일에 update-task — 머리말을 삽입하지 않는다."""
        self._strip_header_line()
        rc, data = _run(["update-task", self.task_path, "--id", "T-1", "--priority", "P2"])
        self.assertEqual(rc, 0, f"update-task 실패: {data}")
        self.assertEqual(self._header_lines(), [], f"머리말이 삽입됐다: {self._header_lines()}")

    def test_non_marker_region_unchanged_when_header_absent(self):
        """머리말 없는 파일에서 마커 밖 영역은 무변경이다."""
        self._append_free_text()
        self._strip_header_line()
        before = self._md()
        before_outside = before[:before.index(MARKER_START)] + before[before.index(MARKER_END):]

        rc, data = _run(["mark", self.task_path, "--id", "T-1", "--status", "in_progress"])
        self.assertEqual(rc, 0, f"mark 실패: {data}")

        after = self._md()
        after_outside = after[:after.index(MARKER_START)] + after[after.index(MARKER_END):]
        self.assertEqual(
            after_outside, before_outside,
            "머리말 없는 파일의 마커 밖 영역이 변경됐다 (하위호환 위반)",
        )


class TestT131ForceRegenerationHeader(_BacklogCase):
    """S-22 — `init --force` 재생성 경로의 머리말 처리 고정.

    현행 동작(코드 확인 결과, `backlog_tool.py` cmd_init):
      `--force`는 `_build_new_backlog_md`로 BACKLOG.md **전체를 재생성**한다.
      머리말은 now_str(= 새 backlog.json.updated_at)로 새로 쓰이고,
      tasks[]와 created_at은 보존되며, 마커 밖 자유 서술은 소실된다.
    이 계약을 회귀 가드로 고정한다 — W-4가 재렌더 경로를 고치면서 이 경로를 바꾸면 안 된다.
    """

    def test_force_header_matches_new_updated_at(self):
        """--force 재생성 후 머리말이 backlog.json.updated_at과 일치한다."""
        self._make_header_stale()
        rc, data = _run([
            "init", self.task_path,
            "--project-title", "파일럿2", "--mode", "agentic", "--goal", "목표2", "--force",
        ])
        self.assertEqual(rc, 0, f"init --force 실패: {data}")
        self._assert_header_matches_json()

    def test_force_preserves_tasks_and_created_at(self):
        """--force는 tasks[]와 created_at을 보존한다 (현행 계약)."""
        before = self._backlog()
        rc, data = _run([
            "init", self.task_path,
            "--project-title", "파일럿2", "--mode", "agentic", "--goal", "목표2", "--force",
        ])
        self.assertEqual(rc, 0, f"init --force 실패: {data}")
        after = self._backlog()
        self.assertEqual(after["created_at"], before["created_at"])
        self.assertEqual([t["id"] for t in after["tasks"]], [t["id"] for t in before["tasks"]])
        self.assertIn("| T-1 |", self._md(), "--force 재생성 표에 기존 태스크가 없다")

    def test_force_regenerates_whole_file_from_template(self):
        """--force는 전체 재생성이므로 마커 밖 자유 서술이 보존되지 않는다 (현행 동작 고정)."""
        self._append_free_text()
        rc, data = _run([
            "init", self.task_path,
            "--project-title", "파일럿2", "--mode", "agentic", "--goal", "목표2", "--force",
        ])
        self.assertEqual(rc, 0, f"init --force 실패: {data}")
        md = self._md()
        self.assertNotIn(FREE_TEXT.strip(), md, "--force 현행 동작(전체 재생성)이 바뀌었다")
        self.assertTrue(md.startswith("# BACKLOG: 파일럿2\n"), f"템플릿 머리부가 아니다: {md[:40]!r}")
        self.assertIn("> 목표: 목표2", md)


if __name__ == "__main__":
    unittest.main()
