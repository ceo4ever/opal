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


if __name__ == "__main__":
    unittest.main()
