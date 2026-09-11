"""
@header {
  "module": "test_boot_brief",
  "layer": "test",
  "domain": "opal-tools",
  "description": "project-aware assistant용 memory boot brief의 3건·1024 bytes·history 0 상한을 고정하는 RED-first 테스트",
  "task": "113",
  "scenarios": ["S-2"],
  "exports": ["TestBootBrief"]
}

TASK 113 RED-first 테스트.
memory-tool 공개 CLI의 stdout bytes와 JSON 필드만 검증한다.
"""

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


_TOOL_DIR = pathlib.Path(__file__).parent.parent
_TOOL_PY = _TOOL_DIR / "memory_tool.py"


def _memory_document():
    memories = []
    for index in range(8):
        memories.append(
            {
                "title": f"활성 메모리 {index}",
                "date": f"2026-09-{index + 1:02d}",
                "type": "project",
                "status": "active",
                "file": f"memory/active-{index}.md",
                "summary": (f"부트 요약 {index} " + "가" * 48)[:80],
            }
        )
    history = [
        {
            "title": f"과거 작업 {index}",
            "date": f"2026-08-{index + 1:02d}",
            "stage": "완료",
            "path": f"tasks/{index:03d}-fixture/",
            "result": "부트에서는 제외되어야 하는 긴 작업 결과 " + "나" * 120,
        }
        for index in range(5)
    ]
    return {
        "version": 1,
        "last_task_number": 113,
        "memories": memories,
        "history": history,
    }


class TestBootBrief(unittest.TestCase):
    """S-2: 전용 boot brief는 hard cap을 넘지 않고 history를 싣지 않는다."""

    def test_boot_brief_enforces_count_and_byte_caps(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = pathlib.Path(tmp) / "MEMORY.json"
            memory_path.write_text(
                json.dumps(_memory_document(), ensure_ascii=False),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(_TOOL_PY),
                    "show",
                    "--file",
                    str(memory_path),
                    "--boot-brief",
                    "--max-bytes",
                    "1024",
                    "--memories",
                    "3",
                    "--history",
                    "0",
                ],
                capture_output=True,
                text=True,
            )

        self.assertEqual(
            result.returncode,
            0,
            f"boot brief CLI 실패: stdout={result.stdout!r} stderr={result.stderr!r}",
        )
        self.assertLessEqual(len(result.stdout.encode("utf-8")), 1024, result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload.get("ok"), payload)
        rows = payload.get("memories", payload.get("index_rows"))
        self.assertIsInstance(rows, list, payload)
        self.assertLessEqual(len(rows), 3, rows)
        self.assertEqual(payload.get("history_rows", []), [], payload)
        self.assertNotIn("긴 작업 결과", result.stdout)

    def _run_boot(self, memories, max_bytes=1024):
        document = {"version": 1, "last_task_number": 116,
                    "memories": memories, "history": []}
        with tempfile.TemporaryDirectory() as tmp:
            memory_path = pathlib.Path(tmp) / "MEMORY.json"
            memory_path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(_TOOL_PY), "show", "--file", str(memory_path),
                 "--boot-brief", "--max-bytes", str(max_bytes), "--memories", "3", "--history", "0"],
                capture_output=True, text=True,
            )

    @staticmethod
    def _row(title, date, row_type="project", status="active", summary="요약"):
        return {"title": title, "date": date, "type": row_type, "status": status,
                "file": "memory/%s.md" % title, "summary": summary}

    def test_review_rows_prioritize_candidate_then_actionable_types(self):
        result = self._run_boot([
            self._row("일반 최신", "2026-09-11"),
            self._row("개선", "2026-09-11", "improvement"),
            self._row("이슈", "2026-09-12", "issues"),
            self._row("후보", "2026-09-01", "project", "candidate"),
            self._row("피드백", "2026-09-13", "feedback"),
            self._row("죽은 후보", "2026-09-20", "feedback", "dead"),
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        review = payload["review_rows"]
        self.assertEqual([row["title"] for row in review], ["후보", "피드백"])
        self.assertEqual(payload["history_rows"], [])
        self.assertIn("index_rows", payload)

    def test_review_rows_equal_dates_are_stable_and_empty_when_no_candidates(self):
        result = self._run_boot([
            self._row("첫 이슈", "2026-09-10", "issues"),
            self._row("둘 이슈", "2026-09-10", "issues"),
            self._row("일반", "2026-09-12", "preferences"),
        ])
        payload = json.loads(result.stdout)
        self.assertEqual([row["title"] for row in payload["review_rows"]], ["첫 이슈", "둘 이슈"])
        result = self._run_boot([self._row("일반", "2026-09-12")])
        self.assertEqual(json.loads(result.stdout)["review_rows"], [])

    def test_long_review_data_still_respects_byte_cap(self):
        result = self._run_boot([
            self._row("후보1", "2026-09-11", status="candidate", summary="가" * 80),
            self._row("후보2", "2026-09-10", status="candidate", summary="나" * 80),
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLessEqual(len(result.stdout.encode("utf-8")), 1024)
        payload = json.loads(result.stdout)
        self.assertIn("review_rows", payload)


if __name__ == "__main__":
    unittest.main()
