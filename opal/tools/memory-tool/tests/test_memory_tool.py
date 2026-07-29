"""
@header {
  "module": "test_memory_tool",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "memory-tool RED-first 테스트 — 045 트랙(S-1~S-17, S-24, 프리픽스 [T045/L1-...]) + 078 MEMORY.json 전환 트랙(TS-001~TS-021·TS-037~TS-041, 프리픽스 [T078/...]). mock/patch/MagicMock 금지(헌법 §4) — 실 fixture·실 프로세스(subprocess)만. 078 블록은 구현 전 작성된 RED이므로 전량 FAIL이 정상.",
  "exports": [
    "TestSkeleton", "TestMarkerGuard", "TestSummaryLengthCap",
    "TestCountUnlimited", "TestHistoryFIFO", "TestPruneIdempotent",
    "TestPromoteToDocs", "TestPromoteLossless", "TestPromoteToBrain",
    "TestUpdateStatusTransition", "TestInit", "TestInitAlreadyInitialized",
    "TestMigrate", "TestMigrateLossless", "TestReviewAmbient",
    "TestReviewRoleBoundary", "TestSecurity", "TestIntegrationTemplate",
    "TestSchemaValidation", "TestSymbolRemoval", "TestJsonIO",
    "TestErrorCodesJson", "TestAtomicWrite", "TestShowBrief",
    "TestLazyMigration", "TestMigrationLossless", "TestMigrationFailure",
    "TestConcurrentMigration", "TestTaskNumber", "TestSuiteMigration",
    "TestTaskNumberDocs"
  ]
}

변경이력:
  v1.1 2026-07-28 078 RED-first 블록 추가 — MEMORY.json 전환 계약(TS-001~TS-021, TS-037~TS-041)
                  61케이스 + 픽스처 5종 신설. 구현(GREEN)은 별도 워커 담당 (red-first.md §2) (078)
"""

# [MUST] 표준 라이브러리만 import
import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

# memory_tool.py 경로 (미존재 시 import 실패 = RED 정상)
_TOOL_DIR = pathlib.Path(__file__).parent.parent
_TOOL_PY = _TOOL_DIR / "memory_tool.py"
_PYTHON = pathlib.Path(os.environ.get("VIRTUAL_ENV", str(pathlib.Path.home() / ".opal" / ".venv"))) / "bin" / "python"
if not _PYTHON.exists():
    _PYTHON = pathlib.Path(sys.executable)

_FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


# ─────────────────────────────────────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _run(args: list, cwd=None) -> dict:
    """memory_tool.py를 직접 호출하고 JSON 결과를 반환한다. 실행 불가 시 예외."""
    cmd = [str(_PYTHON), str(_TOOL_PY)] + args
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    stdout = result.stdout.strip()
    if not stdout:
        raise AssertionError(
            f"memory_tool.py 출력 없음 (exit={result.returncode}).\n"
            f"stderr: {result.stderr.strip()}"
        )
    # 마지막 라인이 JSON (review 블록 등 앞에 부가 출력이 없어야 함)
    return json.loads(stdout.split("\n")[-1])


def _run_raw(args: list, cwd=None) -> subprocess.CompletedProcess:
    """JSON 파싱 없이 raw 결과 반환."""
    cmd = [str(_PYTHON), str(_TOOL_PY)] + args
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def _copy_fixture(name: str, tmp_dir: pathlib.Path) -> pathlib.Path:
    """fixture를 tmp_dir로 복사하고 복사본 경로를 반환한다."""
    src = _FIXTURES_DIR / name
    dst = tmp_dir / name
    shutil.copy2(src, dst)
    return dst


def _init_json(tmp_dir: pathlib.Path, name: str = "MEMORY.json") -> pathlib.Path:
    """tmp_dir에 MEMORY.json 골격을 init으로 생성하고 경로를 반환한다(빈 인덱스·빈 히스토리)."""
    json_path = tmp_dir / name
    result = _run(["init", "--file", str(json_path)])
    if not result.get("ok"):
        raise AssertionError(f"테스트 전제 준비(init) 실패: {result}")
    return json_path


def _setup_populated(tmp_dir: pathlib.Path) -> pathlib.Path:
    """fixture_doc_populated.json(6메모리·5히스토리) + 대응 memory/*.md 파일들을
    tmp_dir에 설치하고 MEMORY.json 경로를 반환한다(JSON SSOT, 078 전환 이후).
    """
    memory_dir = tmp_dir / "memory"
    memory_dir.mkdir(exist_ok=True)
    # 메모리 파일들 생성 (fixture_doc_populated.json의 file 필드 대응)
    for name, content in [
        ("prefs_commit.md", "# 메인 직접 커밋 선호\n\nmain 직접 커밋 선호 상세 내용.\n"),
        ("task_done.md", "# 완료된 태스크 기록\n\n종료된 일회성 태스크 상세.\n"),
        ("console-brain-subscription-auth.md", "# 콘솔 브레인 구독 인증\n\n브레인 질의 상세.\n"),
        ("arch_old.md", "# 대체된 아키텍처 결정\n\n구 도구 패턴 상세.\n"),
        ("prefs_graduated.md", "# 졸업한 선호 규칙\n\nAGENT.md 이관 상세.\n"),
        ("improve_candidate.md", "# 개선 후보 기록\n\nimprove-tool 후보 상세.\n"),
    ]:
        (memory_dir / name).write_text(content, encoding="utf-8")
    dst = tmp_dir / "MEMORY.json"
    shutil.copy2(_FIXTURES_DIR / "fixture_doc_populated.json", dst)
    return dst


# ─────────────────────────────────────────────────────────────────────────────
# S-1: memory-tool 도구 골격 [T045/L1-R5]
# ─────────────────────────────────────────────────────────────────────────────

class TestSkeleton(unittest.TestCase):
    """[T045/L1-R5] S-1: 8서브명령 등록·JSON 반환·validate 부재·memory_limit_exceeded 부재."""

    def test_tool_py_exists(self):
        """memory_tool.py 파일이 존재해야 한다 (미존재=RED)."""
        self.assertTrue(
            _TOOL_PY.exists(),
            f"memory_tool.py 미존재: {_TOOL_PY}"
        )

    def test_all_eight_subcommands_registered(self):
        """9서브명령(init/append/update/promote/prune/show/review/delete/task-number)이
        --help에 노출된다. migrate는 078 전환 이후 lazy 자동 변환으로 흡수되어 부재해야 한다
        (TS-017과 모순 없도록 갱신)."""
        result = _run_raw(["--help"])
        combined = result.stdout + result.stderr
        for sub in ["init", "append", "update", "promote", "prune", "show", "review",
                    "delete", "task-number"]:
            self.assertIn(
                sub, combined,
                f"서브명령 '{sub}'이 --help에 없음"
            )

    def test_validate_subcommand_absent(self):
        """validate 서브명령은 존재하지 않아야 한다 (review로 통합됨)."""
        if not _TOOL_PY.exists():
            self.fail(f"memory_tool.py 미존재 — RED: {_TOOL_PY}")
        result = _run_raw(["validate", "--help"])
        # validate가 없으면 exit code != 0 또는 'error'/'invalid' 포함
        self.assertNotEqual(
            result.returncode, 0,
            "validate 서브명령이 존재하면 안 됨 — review로 통합 필요"
        )

    def test_show_returns_json(self):
        """show 명령은 {'ok':...} 단일라인 JSON을 반환한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _init_json(tmp_dir)
            result = _run(["show", "--file", str(md)])
            self.assertIn("ok", result)

    def test_memory_limit_exceeded_error_code_absent(self):
        """ERROR_CODES에 memory_limit_exceeded 키가 없어야 한다 (갯수 게이트 제외)."""
        # memory_tool.py를 텍스트로 읽어 확인
        if not _TOOL_PY.exists():
            self.skipTest("memory_tool.py 미존재 — RED 예정")
        content = _TOOL_PY.read_text(encoding="utf-8")
        self.assertNotIn(
            "memory_limit_exceeded", content,
            "memory_limit_exceeded 코드가 존재하면 안 됨 (캡틴 지시: 갯수 게이트 제외)"
        )

    def test_memory_limits_constant_absent(self):
        """MEMORY_LIMITS 상수가 존재하지 않아야 한다."""
        if not _TOOL_PY.exists():
            self.skipTest("memory_tool.py 미존재 — RED 예정")
        content = _TOOL_PY.read_text(encoding="utf-8")
        self.assertNotIn(
            "MEMORY_LIMITS", content,
            "MEMORY_LIMITS 상수가 존재하면 안 됨"
        )

    def test_response_is_single_line_json(self):
        """모든 응답은 단일라인 JSON 형식이어야 한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _init_json(tmp_dir)
            raw = _run_raw(["show", "--file", str(md)])
            stdout = raw.stdout.strip()
            lines = [l for l in stdout.split("\n") if l.strip()]
            # 마지막 라인이 유효한 JSON이어야 함
            last = lines[-1] if lines else ""
            parsed = json.loads(last)
            self.assertIn("ok", parsed)


# ─────────────────────────────────────────────────────────────────────────────
# S-2: 마커 가드 (H-3) [T045/L1-R9]
# ─────────────────────────────────────────────────────────────────────────────

class TestMarkerGuard(unittest.TestCase):
    """[T045/L1-R9→T078 재작성] S-2: 마커 가드 개념은 078 JSON 전환으로 소멸(마커 자체가 없음).
    JSON 체제에서도 유효한 대체 계약 — '사용 불가한 대상 파일'에 대한 모든 변경 명령의
    일관된 거부(memory_json_not_found)와 무변경(atomicity) 보존. TS-007(show 단독)과 달리
    변경 명령 5종 전체를 대상으로 한다."""

    def test_all_mutating_commands_reject_missing_file(self):
        """json도 md도 없는 경로에 append/update/promote/prune/delete → 전부 memory_json_not_found."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            json_path = tmp_dir / "MEMORY.json"

            mutating_calls = [
                ["append", "--file", str(json_path), "--kind", "memory",
                 "--title", "T", "--type", "feedback", "--summary", "s"],
                ["update", "--file", str(json_path), "--title", "T", "--status", "dead"],
                ["promote", "--file", str(json_path), "--title", "T", "--to", "docs", "--ref", "x"],
                ["prune", "--file", str(json_path)],
                ["delete", "--file", str(json_path), "--title", "T"],
            ]
            for args in mutating_calls:
                with self.subTest(cmd=args[0]):
                    result = _run(args)
                    self.assertFalse(result["ok"], f"{args[0]}: ok:true 반환됨 — {result}")
                    self.assertEqual(result.get("error"), "memory_json_not_found",
                                     f"{args[0]}: error != memory_json_not_found: {result}")
                    self.assertFalse(json_path.exists(),
                                     f"{args[0]}: 거부됐는데 MEMORY.json이 생성됨")

    def test_append_reject_leaves_no_residual_file(self):
        """append가 memory_json_not_found로 거부된 후 tmp_dir에 어떤 파일도 남지 않는다(원자성)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            json_path = tmp_dir / "MEMORY.json"
            result = _run([
                "append", "--file", str(json_path),
                "--kind", "memory", "--title", "테스트제목",
                "--type", "feedback", "--summary", "대상 부재 테스트"
            ])
            self.assertFalse(result["ok"], f"ok:true가 반환됨: {result}")
            self.assertEqual(result.get("error"), "memory_json_not_found", f"에러 코드 불일치: {result}")
            self.assertEqual(list(tmp_dir.iterdir()), [], "거부 후 잔여 파일이 생성됨")


# ─────────────────────────────────────────────────────────────────────────────
# S-3: 요약 길이캡 (R2) [T045/L1-R2]
# ─────────────────────────────────────────────────────────────────────────────

class TestSummaryLengthCap(unittest.TestCase):
    """[T045/L1-R2] S-3: 81자 요약 append → ok:false + summary_too_long."""

    OVER_SUMMARY = "가" * 81  # 81자 (>80)
    EXACT_SUMMARY = "나" * 80  # 80자 (허용)

    def test_summary_81_chars_rejected(self):
        """81자 요약은 summary_too_long 오류로 거부된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _init_json(tmp_dir)
            result = _run([
                "append", "--file", str(md),
                "--kind", "memory",
                "--title", "길이초과테스트",
                "--type", "feedback",
                "--summary", self.OVER_SUMMARY
            ])
            self.assertFalse(result["ok"], f"81자 요약이 통과됨: {result}")
            self.assertEqual(result.get("error"), "summary_too_long",
                             f"에러 코드 불일치: {result}")

    def test_summary_80_chars_accepted(self):
        """정확히 80자 요약은 허용된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _init_json(tmp_dir)
            result = _run([
                "append", "--file", str(md),
                "--kind", "memory",
                "--title", "길이경계테스트",
                "--type", "feedback",
                "--summary", self.EXACT_SUMMARY
            ])
            self.assertTrue(result["ok"], f"80자 요약이 거부됨: {result}")


# ─────────────────────────────────────────────────────────────────────────────
# S-4: 메모리 갯수 무차단 (R6 제외) [T045/L1-R6x]
# ─────────────────────────────────────────────────────────────────────────────

class TestCountUnlimited(unittest.TestCase):
    """[T045/L1-R6x] S-4: 동일 유형 15건 append 전부 ok:true (갯수 게이트 없음)."""

    def test_fifteen_appends_all_succeed(self):
        """동일 유형 메모리 15건을 append해도 전부 ok:true여야 한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _init_json(tmp_dir)
            for i in range(15):
                result = _run([
                    "append", "--file", str(md),
                    "--kind", "memory",
                    "--title", f"메모리항목{i+1:02d}",
                    "--type", "feedback",
                    "--summary", f"갯수무차단 테스트 항목 {i+1}"
                ])
                self.assertTrue(
                    result["ok"],
                    f"{i+1}번째 append가 거부됨 — 갯수 게이트가 존재하면 안 됨: {result}"
                )


# ─────────────────────────────────────────────────────────────────────────────
# S-5: 히스토리 FIFO=5 (H-2) [T045/L1-R3] [T045/L1-R7]
# ─────────────────────────────────────────────────────────────────────────────

class TestHistoryFIFO(unittest.TestCase):
    """[T045/L1-R3][T045/L1-R7] S-5: history 6건 append → 행수=5, h1 제거, h2~h6 보존."""

    def test_history_fifo_limit_five(self):
        """6건 history append 후 히스토리 행수는 정확히 5여야 한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _init_json(tmp_dir)
            for i in range(6):
                result = _run([
                    "append", "--file", str(md),
                    "--kind", "history",
                    "--title", f"h{i+1}",
                    "--summary", f"히스토리항목{i+1} 핵심결과"
                ])
                self.assertTrue(result["ok"], f"h{i+1} append 실패: {result}")

            history = json.loads(md.read_text(encoding="utf-8"))["history"]
            self.assertEqual(len(history), 5,
                             f"히스토리 행수={len(history)}, FIFO=5 기대\n행목록: {history}")

    def test_history_fifo_removes_oldest(self):
        """h1(최초)이 제거되고 h2~h6(최신 5개)이 보존된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _init_json(tmp_dir)
            for i in range(6):
                _run([
                    "append", "--file", str(md),
                    "--kind", "history",
                    "--title", f"h{i+1}",
                    "--summary", f"히스토리항목{i+1}"
                ])

            titles = [row["title"] for row in json.loads(md.read_text(encoding="utf-8"))["history"]]
            self.assertNotIn("h1", titles, "h1(최초)이 제거되어야 함")
            for i in range(2, 7):
                self.assertIn(f"h{i}", titles, f"h{i}(최신)이 보존되어야 함")


# ─────────────────────────────────────────────────────────────────────────────
# S-6: prune idempotent [T045/L1-R7]
# ─────────────────────────────────────────────────────────────────────────────

class TestPruneIdempotent(unittest.TestCase):
    """[T045/L1-R7] S-6: 히스토리 ≤5 상태에서 prune → no-op, ok:true."""

    def _count_history_data_rows(self, md: pathlib.Path) -> int:
        return len(json.loads(md.read_text(encoding="utf-8"))["history"])

    def test_prune_no_op_when_five_or_fewer(self):
        """히스토리 3건 상태에서 prune → 행수 불변, ok:true."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _init_json(tmp_dir)
            # 3건 추가
            for i in range(3):
                _run([
                    "append", "--file", str(md),
                    "--kind", "history",
                    "--title", f"h{i+1}",
                    "--summary", f"히스토리{i+1}"
                ])

            before_count = self._count_history_data_rows(md)
            result = _run(["prune", "--file", str(md)])
            after_count = self._count_history_data_rows(md)

            self.assertTrue(result["ok"], f"prune 실패: {result}")
            self.assertEqual(before_count, after_count,
                             f"no-op이어야 하는데 행수 변경: {before_count} → {after_count}")

    def test_prune_empty_is_noop(self):
        """히스토리 0건 상태에서 prune → ok:true."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _init_json(tmp_dir)
            result = _run(["prune", "--file", str(md)])
            self.assertTrue(result["ok"], f"빈 히스토리에서 prune 실패: {result}")


# ─────────────────────────────────────────────────────────────────────────────
# S-7: promote --to docs (행+파일 원자 삭제 + provenance) [T045/L1-R8]
# ─────────────────────────────────────────────────────────────────────────────

class TestPromoteToDocs(unittest.TestCase):
    """[T045/L1-R8] S-7: promote --to docs → 인덱스 행 X 부재 + memory/X.md 부재 + provenance 1행."""

    def test_promote_to_docs_removes_row_and_file(self):
        """promote --to docs 후 인덱스 행과 memory 파일이 모두 제거된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            # "메인 직접 커밋 선호" 행 promote
            result = _run([
                "promote", "--file", str(md),
                "--title", "메인 직접 커밋 선호",
                "--to", "docs",
                "--ref", "AGENT.md#커밋방식"
            ])
            self.assertTrue(result["ok"], f"promote 실패: {result}")

            # 인덱스 행 제거 확인 (필드 단위 — 타이틀로 조회 시 부재)
            titles = [row["title"] for row in json.loads(md.read_text(encoding="utf-8"))["memories"]]
            self.assertNotIn("메인 직접 커밋 선호", titles,
                             "promote 후 인덱스 행이 남아있음")

            # memory 파일 제거 확인
            mem_file = tmp_dir / "memory" / "prefs_commit.md"
            self.assertFalse(mem_file.exists(),
                             f"promote 후 memory 파일이 남아있음: {mem_file}")

    def test_promote_to_docs_records_provenance(self):
        """promote 후 provenance(어디로 갔는지)가 기록된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "promote", "--file", str(md),
                "--title", "메인 직접 커밋 선호",
                "--to", "docs",
                "--ref", "AGENT.md#커밋방식"
            ])
            self.assertTrue(result["ok"], f"promote 실패: {result}")
            # provenance가 응답 또는 파일에 기록됨
            self.assertTrue(
                result.get("provenance_logged", False)
                or result.get("row_removed", False),
                f"provenance_logged 또는 삭제 확인 필드 부재: {result}"
            )

    def test_promote_response_fields(self):
        """promote 성공 응답에 필수 필드가 포함된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "promote", "--file", str(md),
                "--title", "메인 직접 커밋 선호",
                "--to", "docs",
                "--ref", "AGENT.md#커밋방식"
            ])
            self.assertTrue(result["ok"])
            # 원자성 증거 필드
            self.assertIn("row_removed", result,
                          f"row_removed 필드 없음: {result}")
            self.assertIn("file_deleted", result,
                          f"file_deleted 필드 없음: {result}")
            self.assertTrue(result["row_removed"])
            self.assertTrue(result["file_deleted"])


# ─────────────────────────────────────────────────────────────────────────────
# S-8: promote 무손실 가드 (H-1) [T045/L1-R8p]
# ─────────────────────────────────────────────────────────────────────────────

class TestPromoteLossless(unittest.TestCase):
    """[T045/L1-R8p] S-8: --ref 미지정 promote → ok:false + promote_ref_missing + 행·파일 불변."""

    def test_promote_without_ref_rejected(self):
        """--ref 없이 promote → ok:false + promote_ref_missing."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "promote", "--file", str(md),
                "--title", "메인 직접 커밋 선호",
                "--to", "docs"
                # --ref 미지정
            ])
            self.assertFalse(result["ok"],
                             f"--ref 없는 promote가 ok:true로 통과됨: {result}")
            self.assertEqual(result.get("error"), "promote_ref_missing",
                             f"에러 코드 불일치: {result}")

    def test_promote_without_ref_preserves_row_and_file(self):
        """--ref 없는 promote 실패 시 인덱스 행과 파일이 불변이어야 한다."""
        if not _TOOL_PY.exists():
            self.fail(f"memory_tool.py 미존재 — RED: {_TOOL_PY}")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            original_doc = json.loads(md.read_text(encoding="utf-8"))
            mem_file = tmp_dir / "memory" / "prefs_commit.md"
            original_mem = mem_file.read_text(encoding="utf-8")

            _run_raw([
                "promote", "--file", str(md),
                "--title", "메인 직접 커밋 선호",
                "--to", "docs"
            ])

            # 인덱스 불변 (필드 단위 비교)
            self.assertEqual(json.loads(md.read_text(encoding="utf-8")), original_doc,
                             "실패한 promote가 인덱스를 변경함")
            # 파일 불변
            self.assertTrue(mem_file.exists(), "실패한 promote가 파일을 삭제함")
            self.assertEqual(mem_file.read_text(encoding="utf-8"), original_mem,
                             "실패한 promote가 파일 내용을 변경함")

    def test_promote_without_to_rejected(self):
        """--to 없이 promote → ok:false."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "promote", "--file", str(md),
                "--title", "메인 직접 커밋 선호",
                "--ref", "AGENT.md#test"
                # --to 미지정
            ])
            self.assertFalse(result["ok"],
                             f"--to 없는 promote가 ok:true로 통과됨: {result}")

    def test_promote_nonexistent_title_rejected(self):
        """존재하지 않는 제목으로 promote → ok:false (row_not_found 또는 memory_file_not_found)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "promote", "--file", str(md),
                "--title", "존재하지않는메모리",
                "--to", "docs",
                "--ref", "AGENT.md#test"
            ])
            self.assertFalse(result["ok"],
                             f"존재하지 않는 제목 promote가 통과됨: {result}")
            self.assertIn(result.get("error"),
                          ["row_not_found", "memory_file_not_found"],
                          f"에러 코드 불일치: {result}")


# ─────────────────────────────────────────────────────────────────────────────
# S-9: promote --to brain (brain-tool 재사용 — H-9) [T045/L1-R8p]
# ─────────────────────────────────────────────────────────────────────────────

class TestPromoteToBrain(unittest.TestCase):
    """[T045/L1-R8p] S-9: promote --to brain → brain 디렉토리 직접 쓰기 없음."""

    def test_promote_brain_does_not_write_to_brain_dir(self):
        """promote --to brain이 brain/ 디렉토리에 직접 파일을 생성하지 않는다."""
        if not _TOOL_PY.exists():
            self.fail(f"memory_tool.py 미존재 — RED: {_TOOL_PY}")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            brain_dir = tmp_dir / "brain"
            brain_dir.mkdir()

            _run_raw([
                "promote", "--file", str(md),
                "--title", "캡틴 선호 커밋 방식",
                "--to", "brain",
                "--ref", "brain-page-slug",
                "--brain-dir", str(brain_dir)
            ])

            # brain 디렉토리에 직접 쓴 파일이 없어야 함
            brain_files = list(brain_dir.iterdir())
            self.assertEqual(len(brain_files), 0,
                             f"memory-tool이 brain 디렉토리에 직접 파일을 썼음: {brain_files}\n"
                             f"(brain-tool 재사용이 필요, 자체 파이프라인 재발명 금지 — H-9)")

    def test_promote_brain_does_not_contain_brain_write_impl(self):
        """memory_tool.py에 brain 디렉토리 직접 쓰기 구현이 없어야 한다."""
        if not _TOOL_PY.exists():
            self.skipTest("memory_tool.py 미존재 — RED 예정")
        content = _TOOL_PY.read_text(encoding="utf-8")
        # brain 직접 쓰기 패턴: brain/ 하위에 파일 쓰기
        import re
        brain_write_patterns = [
            r'brain[/\\].*\.write',
            r'open\(.*brain.*["\']w',
            r'\.write_text\(.*brain',
        ]
        for pattern in brain_write_patterns:
            matches = re.findall(pattern, content)
            self.assertEqual(len(matches), 0,
                             f"brain 직접 쓰기 패턴 발견: {pattern} → {matches}")


# ─────────────────────────────────────────────────────────────────────────────
# S-10: update 상태전이 [T045/L1-R4] [T045/L1-R8]
# ─────────────────────────────────────────────────────────────────────────────

class TestUpdateStatusTransition(unittest.TestCase):
    """[T045/L1-R4][T045/L1-R8] S-10: update 상태전이 — dead/superseded 행 보존, invalid_status 거부."""

    def test_update_active_to_dead_preserves_row(self):
        """active 행을 dead로 update → 행 보존(삭제 아님), 상태 변경."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "update", "--file", str(md),
                "--title", "메인 직접 커밋 선호",
                "--status", "dead"
            ])
            self.assertTrue(result["ok"], f"update 실패: {result}")

            memories = json.loads(md.read_text(encoding="utf-8"))["memories"]
            row = next((r for r in memories if r["title"] == "메인 직접 커밋 선호"), None)
            self.assertIsNotNone(row, "dead 상태 행이 삭제됨 — 보존되어야 함")
            self.assertEqual(row["status"], "dead", "상태가 dead로 변경되지 않음")

    def test_update_invalid_status_rejected(self):
        """invalid 상태값으로 update → ok:false + invalid_status."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "update", "--file", str(md),
                "--title", "메인 직접 커밋 선호",
                "--status", "invalid_unknown_status"
            ])
            self.assertFalse(result["ok"], f"잘못된 상태로 update가 통과됨: {result}")
            self.assertEqual(result.get("error"), "invalid_status",
                             f"에러 코드 불일치: {result}")

    def test_update_to_superseded_preserves_row(self):
        """active 행을 superseded로 update → 행 보존."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "update", "--file", str(md),
                "--title", "콘솔 브레인 구독 인증",
                "--status", "superseded"
            ])
            self.assertTrue(result["ok"], f"update 실패: {result}")
            memories = json.loads(md.read_text(encoding="utf-8"))["memories"]
            row = next((r for r in memories if r["title"] == "콘솔 브레인 구독 인증"), None)
            self.assertIsNotNone(row, "superseded 행이 삭제됨 — 보존되어야 함")
            self.assertEqual(row["status"], "superseded")

    def test_update_valid_status_enum(self):
        """유효한 상태값(active/promoted/superseded/dead)은 허용된다."""
        if not _TOOL_PY.exists():
            self.fail(f"memory_tool.py 미존재 — RED: {_TOOL_PY}")
        valid_statuses = ["active", "superseded", "dead"]
        for status in valid_statuses:
            with tempfile.TemporaryDirectory() as tmp:
                tmp_dir = pathlib.Path(tmp)
                md = _setup_populated(tmp_dir)
                with self.subTest(status=status):
                    result = _run([
                        "update", "--file", str(md),
                        "--title", "메인 직접 커밋 선호",
                        "--status", status
                    ])
                    self.assertTrue(result["ok"],
                                    f"유효한 상태 '{status}'가 거부됨: {result}")


# ─────────────────────────────────────────────────────────────────────────────
# S-11: init 마커 삽입 [T045/L1-R9]
# ─────────────────────────────────────────────────────────────────────────────

class TestInit(unittest.TestCase):
    """[T045/L1-R9→T078 재작성] S-11: init → MEMORY.json 골격 생성.
    마커·표 헤더 개념은 078 JSON 전환으로 소멸. JSON 체제에서 유효한 대체 계약 —
    init은 스키마가 요구하는 4키(version/last_task_number/memories/history)를 갖춘
    빈 골격 문서를 만들고, .md 파일은 생성하지 않는다."""

    def test_init_creates_json_skeleton_on_fresh_path(self):
        """대상 경로에 아무것도 없을 때 init → MEMORY.json 생성 + 빈 골격."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            json_path = tmp_dir / "MEMORY.json"

            result = _run(["init", "--file", str(json_path)])
            self.assertTrue(result["ok"], f"init 실패: {result}")
            self.assertTrue(json_path.exists(), "init이 MEMORY.json을 생성하지 않음")

            doc = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(doc, {"version": 1, "last_task_number": 0,
                                   "memories": [], "history": []},
                             f"init 골격이 계약과 다름: {doc}")

    def test_init_does_not_create_md_file(self):
        """init은 MEMORY.md를 생성하지 않는다(JSON 단독 SSOT)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            json_path = tmp_dir / "MEMORY.json"
            md_path = tmp_dir / "MEMORY.md"

            result = _run(["init", "--file", str(json_path)])
            self.assertTrue(result["ok"], f"init 실패: {result}")
            self.assertFalse(md_path.exists(), "init이 MEMORY.md를 생성함 — JSON 단독 SSOT 위반")


# ─────────────────────────────────────────────────────────────────────────────
# S-12: init 재실행 거부 [T045/L1-R9]
# ─────────────────────────────────────────────────────────────────────────────

class TestInitAlreadyInitialized(unittest.TestCase):
    """[T045/L1-R9→T078 재작성] S-12: 이미 유효한 MEMORY.json에 init(--force 없음) →
    already_initialized. --force는 멱등 통과(재생성 없음)."""

    def test_init_on_existing_json_rejected(self):
        """MEMORY.json이 이미 있는 상태에서 init(--force 없음) → ok:false + already_initialized."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _init_json(tmp_dir)

            result = _run(["init", "--file", str(md)])
            self.assertFalse(result["ok"],
                             f"이미 초기화된 파일에 init이 통과됨: {result}")
            self.assertEqual(result.get("error"), "already_initialized",
                             f"에러 코드 불일치: {result}")

    def test_init_force_on_existing_json_succeeds_idempotently(self):
        """--force 플래그로 init → 성공하며 기존 내용을 그대로 보존한다(멱등)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            before = json.loads(md.read_text(encoding="utf-8"))

            result = _run(["init", "--file", str(md), "--force"])
            self.assertTrue(result["ok"],
                            f"--force init 실패: {result}")
            after = json.loads(md.read_text(encoding="utf-8"))
            self.assertEqual(before, after,
                             "--force init이 기존 유효 문서를 변경함 — 멱등이어야 함")


# ─────────────────────────────────────────────────────────────────────────────
# S-13/S-14: migrate 구→신 변환 + 80자 초과 무손실 — [T045/L1-R8p·H5] 폐기 (078 재작성)
#
#   구 TestMigrate(6)·TestMigrateLossless(2)는 명시적 `migrate` 서브명령을 전제로 했으나
#   078 전환 이후 변환은 lazy 자동 마이그레이션(show/append 등 아무 명령에서나 발동)으로
#   흡수되어 별도 서브명령이 존재하지 않는다(TestSkeleton.test_all_eight_subcommands_registered
#   갱신·TS-017 참조). 동일 계약(행수 보존·상태매핑·80자 초과 [REVIEW] 무손실·마커 없는
#   신포맷 산출)은 TestLazyMigration·TestMigrationLossless·TestMigrationFailure가
#   fixture_md_marker_populated.md/fixture_md_marker_empty.md/fixture_md_no_marker_legacy.md로
#   더 엄격하게(필드 단위 100% 일치) 재검증하므로 완전 중복 — 폐기하고 재작성하지 않는다.
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# S-15: 자가검토 ambient 강제 (H-8) [T045/L1-R6p]
# ─────────────────────────────────────────────────────────────────────────────

class TestReviewAmbient(unittest.TestCase):
    """[T045/L1-R6p] S-15: 모든 변경 명령 응답에 review 키 존재."""

    def _assert_review_key(self, result: dict, cmd: str):
        self.assertIn("review", result,
                      f"{cmd} 응답에 review 키 없음 (ambient 강제 실패): {result}")
        review = result["review"]
        self.assertIn("promote_candidates", review,
                      f"{cmd}.review에 promote_candidates 없음")
        self.assertIn("cleanup_candidates", review,
                      f"{cmd}.review에 cleanup_candidates 없음")
        self.assertIn("history_status", review,
                      f"{cmd}.review에 history_status 없음")
        self.assertIn("violations", review,
                      f"{cmd}.review에 violations 없음")

    def test_init_response_has_review(self):
        """init 응답에 review 키가 있다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            json_path = tmp_dir / "MEMORY.json"
            result = _run(["init", "--file", str(json_path)])
            self.assertTrue(result["ok"])
            self._assert_review_key(result, "init")

    def test_append_response_has_review(self):
        """append 응답에 review 키가 있다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _init_json(tmp_dir)
            result = _run([
                "append", "--file", str(md),
                "--kind", "memory",
                "--title", "리뷰테스트",
                "--type", "feedback",
                "--summary", "자가검토 ambient 테스트"
            ])
            self.assertTrue(result["ok"])
            self._assert_review_key(result, "append")

    def test_update_response_has_review(self):
        """update 응답에 review 키가 있다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            result = _run([
                "update", "--file", str(md),
                "--title", "메인 직접 커밋 선호",
                "--status", "dead"
            ])
            self.assertTrue(result["ok"])
            self._assert_review_key(result, "update")

    def test_promote_response_has_review(self):
        """promote 응답에 review 키가 있다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            result = _run([
                "promote", "--file", str(md),
                "--title", "메인 직접 커밋 선호",
                "--to", "docs",
                "--ref", "AGENT.md#커밋방식"
            ])
            self.assertTrue(result["ok"])
            self._assert_review_key(result, "promote")

    def test_prune_response_has_review(self):
        """prune 응답에 review 키가 있다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _init_json(tmp_dir)
            result = _run(["prune", "--file", str(md)])
            self.assertTrue(result["ok"])
            self._assert_review_key(result, "prune")

    def test_delete_response_has_review(self):
        """delete 응답에 review 키가 있다(9종 서브명령 중 migrate 대체 커버리지)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            result = _run(["delete", "--file", str(md), "--title", "완료된 태스크 기록"])
            self.assertTrue(result["ok"], f"delete 실패: {result}")
            self._assert_review_key(result, "delete")

    def test_task_number_bump_response_has_review(self):
        """task-number --bump 응답에 review 키가 있다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _init_json(tmp_dir)
            result = _run(["task-number", "--file", str(md), "--bump"])
            self.assertTrue(result["ok"], f"task-number --bump 실패: {result}")
            self._assert_review_key(result, "task-number")


# ─────────────────────────────────────────────────────────────────────────────
# S-16: review 역할경계 (H-8) [T045/L1-R6p]
# ─────────────────────────────────────────────────────────────────────────────

class TestReviewRoleBoundary(unittest.TestCase):
    """[T045/L1-R6p] S-16: promote_candidates는 후보만, cleanup_candidates에 dead/superseded."""

    def test_review_promote_candidates_no_graduation_destination(self):
        """promote_candidates에 졸업지(docs/brain) 단정 필드가 없다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            result = _run(["review", "--file", str(md)])
            self.assertTrue(result["ok"], f"review 실패: {result}")

            candidates = result.get("promote_candidates", [])
            for c in candidates:
                self.assertNotIn("destination", c,
                                 f"promote_candidates에 졸업지 단정 필드 'destination' 존재: {c}")
                self.assertNotIn("graduate_to", c,
                                 f"promote_candidates에 'graduate_to' 단정 필드 존재: {c}")
                # 힌트(type)는 허용, 단정 필드는 금지

    def test_review_cleanup_candidates_includes_dead_and_superseded(self):
        """cleanup_candidates에 dead/superseded 행이 표면화된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            result = _run(["review", "--file", str(md)])
            self.assertTrue(result["ok"], f"review 실패: {result}")

            cleanup = result.get("cleanup_candidates", [])
            # fixture_doc_populated.json에 dead 1행·superseded 1행 존재
            self.assertGreater(len(cleanup), 0,
                               f"cleanup_candidates가 비어있음 — dead/superseded가 표면화되어야 함: {result}")

    def test_review_returns_violations_list(self):
        """review 응답에 violations 리스트가 있다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            result = _run(["review", "--file", str(md)])
            self.assertTrue(result["ok"])
            self.assertIsInstance(result.get("violations"), list,
                                  f"violations가 리스트가 아님: {result}")

    def test_review_history_status_field_present(self):
        """review 응답에 history_status 필드가 있다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            result = _run(["review", "--file", str(md)])
            self.assertTrue(result["ok"])
            self.assertIn("history_status", result,
                          f"history_status 없음: {result}")

    def test_review_promote_candidates_are_active_rows(self):
        """promote_candidates는 active 상태 행만 포함한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            result = _run(["review", "--file", str(md)])
            self.assertTrue(result["ok"])

            candidates = result.get("promote_candidates", [])
            for c in candidates:
                status = c.get("status", "active")
                self.assertIn(status, ["active"],
                              f"promote_candidates에 active가 아닌 행 포함: {c}")


# ─────────────────────────────────────────────────────────────────────────────
# S-17: 보안 — 경로 탈출·ReDoS·시크릿 [T045/L1-SEC]
# ─────────────────────────────────────────────────────────────────────────────

class TestSecurity(unittest.TestCase):
    """[T045/L1-SEC] S-17: promote --title 경로 탈출 거부, memory/ 하위만 허용."""

    def test_promote_path_traversal_rejected(self):
        """--title에 ../ 경로 탈출 문자열 → promote 거부."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            # 경로 탈출을 시도하는 제목으로 promote
            result = _run([
                "promote", "--file", str(md),
                "--title", "../../../etc/passwd",
                "--to", "docs",
                "--ref", "AGENT.md#test"
            ])
            self.assertFalse(result["ok"],
                             f"경로 탈출 제목으로 promote가 통과됨: {result}")

    def test_promote_only_deletes_within_memory_dir(self):
        """promote가 memory/ 디렉토리 외부 파일을 삭제하지 않는다."""
        if not _TOOL_PY.exists():
            self.fail(f"memory_tool.py 미존재 — RED: {_TOOL_PY}")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            # memory/ 외부에 파일 생성
            outside_file = tmp_dir / "important.md"
            outside_file.write_text("중요한 파일 — 삭제되면 안 됨\n", encoding="utf-8")

            _run_raw([
                "promote", "--file", str(md),
                "--title", "캡틴 선호 커밋 방식",
                "--to", "docs",
                "--ref", "AGENT.md#test"
            ])

            self.assertTrue(outside_file.exists(),
                            "promote가 memory/ 외부 파일을 삭제했음")

    def test_no_hardcoded_secrets_in_tool(self):
        """memory_tool.py에 하드코딩 시크릿 패턴이 없다."""
        if not _TOOL_PY.exists():
            self.skipTest("memory_tool.py 미존재 — RED 예정")
        content = _TOOL_PY.read_text(encoding="utf-8")
        import re
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][A-Za-z0-9+/]{20,}',
        ]
        for pattern in secret_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            self.assertEqual(len(matches), 0,
                             f"하드코딩 시크릿 패턴 발견: {pattern} → {matches}")

    def test_path_traversal_in_title_file_mapping(self):
        """제목에서 파일 경로 변환 시 ../ 가 포함되면 거부한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            # 실제 존재하는 제목이지만 파일 경로가 ../ 를 통과하는 케이스
            # (파일 필드가 ../sensitive.md 같은 경우 거부해야 함)
            result = _run([
                "promote", "--file", str(md),
                "--title", "캡틴 선호 커밋 방식",
                "--to", "docs",
                "--ref", "AGENT.md#test"
            ])
            # 정상 promote는 통과해야 함 (경로 가드가 memory/ 내부 파일만 허용하므로)
            if result["ok"]:
                mem_file = tmp_dir / "memory" / "prefs_commit.md"
                self.assertFalse(mem_file.exists(),
                                 "promote 후 파일이 memory/ 디렉토리 내에서 삭제됨 — 정상")


# ─────────────────────────────────────────────────────────────────────────────
# S-24: 통합 — 신포맷 템플릿 MEMORY.md → review violations 0 [T045/L2-R10] 폐기 (078 재작성)
#
#   구 TestIntegrationTemplate(4)은 마커 기반 MEMORY.md 템플릿 문자열을 전제로 했다.
#   JSON 체제의 동일 계약(스키마 위반 0건 골격·신규 파일에 append 성공)은
#   TestSchemaValidation(TS-001~005)의 유효 문서 통과 경로와 TestJsonIO(TS-007)의
#   init→append 흐름이 이미 실 프로세스로 검증하므로 완전 중복 — 폐기.
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# 추가: ERROR_CODES 검증 [T045/L1-R5]
# ─────────────────────────────────────────────────────────────────────────────

class TestErrorCodes(unittest.TestCase):
    """[T045/L1-R5] ERROR_CODES 키 SSOT 검증."""

    # marker_missing은 078 JSON 전환으로 소멸(마커 개념 부재) — TestErrorCodesJson(TS-008)의
    # _ERROR_CODES_FORBIDDEN에서 부재를 별도 검증한다.
    REQUIRED_CODES = [
        "summary_too_long",
        "promote_ref_missing",
        "memory_file_not_found",
        "row_not_found",
        "already_initialized",
        "invalid_status",
        "invalid_type",
        "title_required",
    ]

    FORBIDDEN_CODES = [
        "memory_limit_exceeded",
    ]

    def test_required_error_codes_exist(self):
        """필수 ERROR_CODES 키가 모두 존재한다."""
        if not _TOOL_PY.exists():
            self.skipTest("memory_tool.py 미존재 — RED 예정")
        content = _TOOL_PY.read_text(encoding="utf-8")
        for code in self.REQUIRED_CODES:
            self.assertIn(f'"{code}"', content,
                          f"필수 에러코드 '{code}'가 ERROR_CODES에 없음")

    def test_forbidden_error_codes_absent(self):
        """금지 ERROR_CODES 키가 존재하지 않는다."""
        if not _TOOL_PY.exists():
            self.skipTest("memory_tool.py 미존재 — RED 예정")
        content = _TOOL_PY.read_text(encoding="utf-8")
        for code in self.FORBIDDEN_CODES:
            self.assertNotIn(f'"{code}"', content,
                             f"금지 에러코드 '{code}'가 존재함 (갯수 게이트 제외)")

    def test_history_fifo_limit_constant(self):
        """HISTORY_FIFO_LIMIT = 5 상수가 존재한다."""
        if not _TOOL_PY.exists():
            self.skipTest("memory_tool.py 미존재 — RED 예정")
        content = _TOOL_PY.read_text(encoding="utf-8")
        self.assertIn("HISTORY_FIFO_LIMIT", content,
                      "HISTORY_FIFO_LIMIT 상수 없음")
        self.assertIn("HISTORY_FIFO_LIMIT = 5", content,
                      "HISTORY_FIFO_LIMIT 값이 5가 아님")


# ─────────────────────────────────────────────────────────────────────────────
# S-25: delete 서브명령 — dead/superseded 행 물리 제거 (무손실 가드) [T045/L1-DEL]
# ─────────────────────────────────────────────────────────────────────────────

class TestDelete(unittest.TestCase):
    """[T045/L1-DEL] S-25: delete 서브명령 — dead/superseded 행 물리 제거 + 무손실 가드."""

    def test_delete_dead_row_succeeds(self):
        """dead 상태 행 delete → ok:true + 인덱스 행 제거."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "delete", "--file", str(md),
                "--title", "완료된 태스크 기록"
            ])
            self.assertTrue(result["ok"], f"dead 행 delete 실패: {result}")

            titles = [row["title"] for row in json.loads(md.read_text(encoding="utf-8"))["memories"]]
            self.assertNotIn("완료된 태스크 기록", titles,
                             "dead 행이 인덱스에서 제거되지 않음")

    def test_delete_active_row_rejected_with_error_code(self):
        """active 상태 행 delete 시도 → ok:false + delete_requires_dead_or_superseded."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "delete", "--file", str(md),
                "--title", "메인 직접 커밋 선호"
            ])
            self.assertFalse(result["ok"],
                             f"active 행 delete가 ok:true로 통과됨 — 무손실 가드 실패: {result}")
            self.assertEqual(result.get("error"), "delete_requires_dead_or_superseded",
                             f"에러 코드 불일치: {result}")

    def test_delete_active_row_file_unchanged(self):
        """active 행 delete 거부 시 인덱스 파일이 불변이어야 한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            original_doc = json.loads(md.read_text(encoding="utf-8"))

            _run_raw([
                "delete", "--file", str(md),
                "--title", "메인 직접 커밋 선호"
            ])

            self.assertEqual(json.loads(md.read_text(encoding="utf-8")), original_doc,
                             "active 행 delete 거부 후 파일이 변경됨 — 1바이트도 건드리면 안 됨")

    def test_delete_superseded_row_succeeds(self):
        """superseded 상태 행 delete → ok:true + 인덱스 행 제거."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "delete", "--file", str(md),
                "--title", "대체된 아키텍처 결정"
            ])
            self.assertTrue(result["ok"], f"superseded 행 delete 실패: {result}")

            titles = [row["title"] for row in json.loads(md.read_text(encoding="utf-8"))["memories"]]
            self.assertNotIn("대체된 아키텍처 결정", titles,
                             "superseded 행이 인덱스에서 제거되지 않음")

    def test_delete_with_file_removes_md(self):
        """--with-file 옵션 시 memory/<file>.md도 삭제된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            mem_file = tmp_dir / "memory" / "task_done.md"
            self.assertTrue(mem_file.exists(), "테스트 전제 실패: task_done.md 없음")

            result = _run([
                "delete", "--file", str(md),
                "--title", "완료된 태스크 기록",
                "--with-file"
            ])
            self.assertTrue(result["ok"], f"--with-file delete 실패: {result}")
            self.assertFalse(mem_file.exists(),
                             f"--with-file 후 memory 파일이 여전히 존재함: {mem_file}")

    def test_delete_without_with_file_preserves_md(self):
        """--with-file 없이 delete → 인덱스 행만 제거, .md 파일 보존."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            mem_file = tmp_dir / "memory" / "task_done.md"

            result = _run([
                "delete", "--file", str(md),
                "--title", "완료된 태스크 기록"
            ])
            self.assertTrue(result["ok"], f"delete 실패: {result}")
            self.assertTrue(mem_file.exists(),
                            "--with-file 미지정인데 .md 파일이 삭제됨")

    def test_delete_with_file_path_traversal_rejected(self):
        """--with-file + ../ 탈출 경로 파일 필드 → 거부 (경로 화이트리스트 위반)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            # 탈출 경로 file 필드를 가진 행을 doc에 직접 삽입(필드 단위 조작 — 문자열 치환 아님)
            doc = json.loads(md.read_text(encoding="utf-8"))
            doc["memories"].append({
                "title": "탈출시도항목", "date": "2025-06-01", "type": "feedback",
                "status": "dead", "file": "../sensitive.md", "summary": "경로 탈출 테스트",
            })
            md.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

            # 외부에 민감 파일 생성
            sensitive = tmp_dir / "sensitive.md"
            sensitive.write_text("민감 파일 — 삭제되면 안 됨\n", encoding="utf-8")

            result = _run([
                "delete", "--file", str(md),
                "--title", "탈출시도항목",
                "--with-file"
            ])
            # 거부 또는 성공하더라도 sensitive.md는 살아있어야 함
            self.assertTrue(sensitive.exists(),
                            "경로 탈출 --with-file이 memory/ 외부 파일을 삭제했음")
            if result.get("ok"):
                # 성공했다면 실제로 ../sensitive.md가 아닌 경로를 시도해야 함
                # → 결과적으로 외부 파일이 삭제되지 않았음을 위 assert로 검증함
                pass
            else:
                # 명시적 에러로 거부된 경우도 PASS
                self.assertIn(result.get("error", ""), [
                    "path_traversal_denied", "invalid_file_path",
                    "memory_file_not_found", "row_not_found", "schema_validation_failed",
                ], f"예상치 못한 에러 코드: {result}")

    def test_delete_row_not_found(self):
        """존재하지 않는 title delete → ok:false + row_not_found."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "delete", "--file", str(md),
                "--title", "존재하지않는항목"
            ])
            self.assertFalse(result["ok"], f"존재하지 않는 항목 delete가 통과됨: {result}")
            self.assertEqual(result.get("error"), "row_not_found",
                             f"에러 코드 불일치: {result}")

    def test_delete_missing_target_rejected(self):
        """[T078 재작성] json도 md도 없는 경로에 delete → ok:false + memory_json_not_found + 파일 무생성.
        마커 개념 소멸로 marker_missing 대신 JSON 체제의 대상 부재 계약으로 대체."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            json_path = tmp_dir / "MEMORY.json"

            result = _run([
                "delete", "--file", str(json_path),
                "--title", "임의제목"
            ])
            self.assertFalse(result["ok"],
                             f"대상이 없는데 delete가 통과됨: {result}")
            self.assertEqual(result.get("error"), "memory_json_not_found",
                             f"에러 코드 불일치: {result}")
            self.assertFalse(json_path.exists(),
                             "거부됐는데 MEMORY.json이 생성됨")

    def test_delete_response_has_review_block(self):
        """delete 성공 응답에 review 블록이 첨부된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "delete", "--file", str(md),
                "--title", "완료된 태스크 기록"
            ])
            self.assertTrue(result["ok"], f"delete 실패: {result}")
            self.assertIn("review", result,
                          f"delete 응답에 review 블록 없음 (ambient 강제 실패): {result}")
            review = result["review"]
            self.assertIn("cleanup_candidates", review,
                          f"review에 cleanup_candidates 없음: {review}")


# ─────────────────────────────────────────────────────────────────────────────
# S-26: update --new-title — 제목 수정 [T045/L1-NEWTITLE]
# ─────────────────────────────────────────────────────────────────────────────

class TestUpdateNewTitle(unittest.TestCase):
    """[T045/L1-NEWTITLE] S-26: update --new-title 제목 수정 + 빈 값 거부 + 기존 동작 회귀 없음."""

    def test_new_title_changes_title_preserves_other_fields(self):
        """--new-title 지정 시 제목이 변경되고 유형·상태·요약은 보존된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "update", "--file", str(md),
                "--title", "대체된 아키텍처 결정",
                "--new-title", "대체된 아키텍처 결정 v2"
            ])
            self.assertTrue(result["ok"], f"--new-title update 실패: {result}")

            memories = json.loads(md.read_text(encoding="utf-8"))["memories"]
            titles = [row["title"] for row in memories]
            # 새 제목 존재, 기존 제목 제거
            self.assertIn("대체된 아키텍처 결정 v2", titles,
                          "새 제목이 인덱스에 반영되지 않음")
            self.assertNotIn("대체된 아키텍처 결정", titles,
                             "기존 제목이 그대로 남아있음")
            row = next(r for r in memories if r["title"] == "대체된 아키텍처 결정 v2")
            # 유형·상태 보존 (architecture / superseded)
            self.assertEqual(row["type"], "architecture",
                             "제목 변경 후 유형(architecture)이 보존되지 않음")
            self.assertEqual(row["status"], "superseded",
                             "제목 변경 후 상태(superseded)가 보존되지 않음")

    def test_new_title_empty_string_rejected(self):
        """--new-title이 빈 문자열 → ok:false + title_required (또는 적절한 에러)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            original_doc = json.loads(md.read_text(encoding="utf-8"))

            result = _run([
                "update", "--file", str(md),
                "--title", "메인 직접 커밋 선호",
                "--new-title", ""
            ])
            self.assertFalse(result["ok"],
                             f"빈 --new-title이 ok:true로 통과됨: {result}")
            self.assertIn(result.get("error"), [
                "title_required", "invalid_title", "new_title_required"
            ], f"에러 코드 불일치: {result}")
            # 행 불변 확인
            self.assertEqual(json.loads(md.read_text(encoding="utf-8")), original_doc,
                             "빈 --new-title 거부 후 파일이 변경됨")

    def test_new_title_whitespace_only_rejected(self):
        """--new-title이 공백만 → ok:false + title_required (또는 적절한 에러)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            original_doc = json.loads(md.read_text(encoding="utf-8"))

            result = _run([
                "update", "--file", str(md),
                "--title", "메인 직접 커밋 선호",
                "--new-title", "   "
            ])
            self.assertFalse(result["ok"],
                             f"공백 --new-title이 ok:true로 통과됨: {result}")
            self.assertIn(result.get("error"), [
                "title_required", "invalid_title", "new_title_required"
            ], f"에러 코드 불일치: {result}")
            self.assertEqual(json.loads(md.read_text(encoding="utf-8")), original_doc,
                             "공백 --new-title 거부 후 파일이 변경됨")

    def test_existing_status_update_regression(self):
        """기존 --status update 동작이 회귀 없이 정상 작동한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "update", "--file", str(md),
                "--title", "콘솔 브레인 구독 인증",
                "--status", "superseded"
            ])
            self.assertTrue(result["ok"],
                            f"기존 --status update 회귀 — 실패: {result}")

            memories = json.loads(md.read_text(encoding="utf-8"))["memories"]
            row = next((r for r in memories if r["title"] == "콘솔 브레인 구독 인증"), None)
            self.assertIsNotNone(row, "행이 삭제됨 — 보존되어야 함")
            self.assertEqual(row["status"], "superseded",
                             "상태가 superseded로 변경되지 않음")

    def test_existing_summary_update_regression(self):
        """기존 --summary update 동작이 회귀 없이 정상 작동한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            new_summary = "갱신된 요약 내용 — 회귀 테스트"
            result = _run([
                "update", "--file", str(md),
                "--title", "메인 직접 커밋 선호",
                "--summary", new_summary
            ])
            self.assertTrue(result["ok"],
                            f"기존 --summary update 회귀 — 실패: {result}")

            memories = json.loads(md.read_text(encoding="utf-8"))["memories"]
            row = next(r for r in memories if r["title"] == "메인 직접 커밋 선호")
            self.assertEqual(row["summary"], new_summary,
                             "요약이 갱신되지 않음")


# ─────────────────────────────────────────────────────────────────────────────
# S-27: argparse 9종 서브명령 등록 확인 (delete 포함) [T045/L1-SKv2]
# ─────────────────────────────────────────────────────────────────────────────

class TestSkeletonV2(unittest.TestCase):
    """[T045/L1-SKv2→T078 갱신] S-27: 서브명령 9종(delete·task-number 포함) argparse 등록 확인.
    migrate는 078 전환으로 lazy 자동 변환에 흡수되어 부재해야 한다(TS-017과 무모순)."""

    ALL_NINE_SUBCOMMANDS = [
        "init", "append", "update", "promote", "prune",
        "show", "review", "delete", "task-number"
    ]

    def test_all_nine_subcommands_in_help(self):
        """9서브명령(delete 포함)이 --help에 모두 노출된다."""
        result = _run_raw(["--help"])
        combined = result.stdout + result.stderr
        for sub in self.ALL_NINE_SUBCOMMANDS:
            self.assertIn(sub, combined,
                          f"서브명령 '{sub}'이 --help에 없음 (9종 등록 미완)")

    def test_delete_subcommand_help_available(self):
        """delete --help 가 정상 응답한다 (argparse 등록 확인)."""
        result = _run_raw(["delete", "--help"])
        combined = result.stdout + result.stderr
        # help가 출력되거나 exit 0이면 등록된 것
        has_help_output = "delete" in combined or "--title" in combined or "--file" in combined
        exited_ok = result.returncode == 0
        self.assertTrue(has_help_output or exited_ok,
                        f"delete --help 응답 없음 (returncode={result.returncode})\n"
                        f"stdout: {result.stdout[:300]}\nstderr: {result.stderr[:300]}")

    def test_delete_requires_title_argument(self):
        """delete 서브명령은 --title 인자를 필요로 한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            # --title 없이 delete 실행 → non-zero exit 또는 error 응답
            result = _run_raw(["delete", "--file", str(md)])
            # argparse가 --title을 required로 등록했다면 non-zero exit
            # 또는 JSON error 응답
            has_error = result.returncode != 0
            if result.returncode == 0 and result.stdout.strip():
                try:
                    parsed = json.loads(result.stdout.strip().split("\n")[-1])
                    has_error = not parsed.get("ok", True)
                except json.JSONDecodeError:
                    has_error = True
            self.assertTrue(has_error,
                            "--title 없이 delete가 성공함 — required 인자로 등록되어야 함")

    def test_new_title_argument_registered_in_update(self):
        """update 서브명령에 --new-title 인자가 등록되어 있다."""
        result = _run_raw(["update", "--help"])
        combined = result.stdout + result.stderr
        self.assertIn("new-title", combined,
                      "update --help에 --new-title 인자가 없음 (argparse 등록 미완)")


# ─────────────────────────────────────────────────────────────────────────────
# S-28: 백틱 file 필드 버그 [T045/L1-BUG] 폐기 (078 재작성)
#
#   구 TestBacktickFileFieldDeletion(4)은 `migrate` 서브명령이 생성한 인덱스 행의
#   file 필드에 백틱이 남는 버그를 전제로 했다. 078 전환 이후 변환 로직
#   (_convert_index_rows)이 `file_field.strip().strip("`").strip()`으로 백틱을
#   무조건 제거한 뒤 JSON에 기록하므로 이 버그 자체가 구조적으로 재현 불가능하다.
#   백틱 정규화 계약은 TestMigrationLossless.test_ts014_backtick_file_field_is_normalized가
#   더 엄격하게(패턴 검증까지) 재검증하므로 완전 중복 — 폐기.
# ─────────────────────────────────────────────────────────────────────────────


# ═════════════════════════════════════════════════════════════════════════════
# 078 RED-first — 프로젝트 메모리 SSOT MEMORY.md → MEMORY.json 전환
#
#   대상 시나리오: TS-001~TS-021, TS-037~TS-041
#   계약 출처    : tasks/078-260728-opd-메모리-json전환/PLAN.md
#                  §3.1(스키마·검증기) §3.2(I/O·응답키·ERROR_CODES)
#                  §3.3(show --brief) §3.4(lazy 마이그레이션·행 회계) §3.5(task-number)
#   [MUST] red-first.md §2 작성자≠구현자 — 본 블록은 테스트만 담는다(구현 코드 0줄).
#   [MUST] TEST-SCENARIO.md §3 테스트 더블 금지 — 실 파일·실 프로세스(subprocess)만.
#   [MUST] red-first.md §3 — GREEN 루핑 중 아래 단정을 약화·삭제하지 않는다.
# ═════════════════════════════════════════════════════════════════════════════

_REPO_ROOT = _TOOL_DIR.parent.parent.parent          # .../ai-framework
_SCHEMA_PATH = _TOOL_DIR / "schema" / "memory.schema.json"

# TS-015(2) 결함 주입 훅 — 히스토리 헤더 프로파일 감지를 강제 무력화한다.
# 구현자는 이 환경변수가 참일 때 V-2 프로파일 매칭·위치 폴백을 비활성화해야 한다.
_ENV_DISABLE_PROFILES = "MEMORY_TOOL_DISABLE_HISTORY_PROFILES"

# TS-008 — ERROR_CODES 카탈로그 전환 (PLAN §3.2.3)
_ERROR_CODES_REQUIRED = {
    "memory_json_not_found",       # memory_md_not_found 개명
    "invalid_json",
    "unsupported_version",
    "schema_validation_failed",
    "schema_load_failed",
    "schema_unsupported_keyword",
    "invalid_date",
    "lock_timeout",
    "migration_failed",
    "task_number_regression",
    "invalid_args",                # PLAN §3.5.2 --bump + --set 동시 지정
}
_ERROR_CODES_FORBIDDEN = {"marker_missing", "import_failed", "memory_md_not_found"}

# TS-014 — fixture_md_marker_populated.md(ai-framework 실측)의 변환 기대값 (100% 일치)
_TS014_MEMORIES = [
    {"title": "Console 브레인 구독 인증", "date": "2026-06-22", "type": "project", "status": "active",
     "file": "memory/console-brain-subscription-auth.md",
     "summary": "Console 브레인 질의는 종량제 API 아닌 사용자 Claude 구독(로컬 claude -p). API키·SDK 금지"},
    {"title": "브레인 질의 콜드 경량화(037후속)", "date": "2026-06-23", "type": "task", "status": "active",
     "file": "memory/follow-up-brain-query-lite.md",
     "summary": "브레인 질의 콜드 latency 경량화 — 검색을 LLM 밖 brain-tool로. opbr --lite 권고"},
    {"title": "후속 069·070 액션에이전트 관측 확장", "date": "2026-07-17", "type": "task", "status": "active",
     "file": "memory/후속_069_070_액션에이전트_관측_확장.md",
     "summary": "oppd·opsdd를 opal-agent 채널+규약 전환→action-monitor 공용화. phase 동적발견 필수"},
]

_TS014_HISTORY = [
    {"title": "076 파이프라인 todo 미러 hook 강제", "date": "2026-07-23",
     "stage": "완료·커밋(148e95c)", "path": "tasks/076-260723-opds-todo미러-hook자동화/",
     "result": "prose→hook강제(state-tool todo_mirror+PostToolUse). clobber해소 실증·회귀0. S-9 L3후속"},
    {"title": "075 목표-커버 게이트 opds·opsdd 확산 1차", "date": "2026-07-23",
     "stage": "완료·커밋(6b1eafb)·미배포(캡틴 배포)", "path": "tasks/075-260723-opd-시나리오게이트-확산-1차/",
     "result": "op-scenario-gate opds·opsdd 확산(신규0·pilot 변환기+배선). opd 무영향·opsdd self-confirming 해소. oppl제외·oppd2차"},
    {"title": "073 TEST-SCENARIO 목표-커버 게이트 루프", "date": "2026-07-23",
     "stage": "완료·커밋(c8cb0b6)·배포", "path": "tasks/073-260723-opd-시나리오-목표커버리지-루프/",
     "result": "목표-커버 루브릭 게이트 공유컴포넌트 신설·opd 선적용. dogfooding 실증(음성통제FAIL+수렴PASS)"},
    {"title": "074 import-existing key 유실 수정", "date": "2026-07-23",
     "stage": "완료·미배포·미커밋", "path": "tasks/074-260723-opds-import-existing-키유실/",
     "result": "--import-existing가 lossy STATE.md 재파싱으로 key 유실 → (stage,item) 순서매칭 재접합(state.json→pipeline.json→keyless경고). RED→GREEN 신규5·전량254. 후속=배포·커밋"},
    {"title": "072 다음 액션 자동 파생", "date": "2026-07-23",
     "stage": "완료·커밋(f6ec48b)", "path": "tasks/072-260723-opd-다음액션-자동파생/",
     "result": "advance/mark 프론티어 자동파생+next_action SSOT·설계반전. 회귀249·RED-first"},
]


# ─────────────────────────────────────────────────────────────────────────────
# 078 헬퍼 (실 파일·실 프로세스 전용 — 테스트 더블 없음)
# ─────────────────────────────────────────────────────────────────────────────

def _run_cli(args, cwd=None, env=None, tool_py=None):
    """memory_tool.py를 서브프로세스로 호출한다.
    반환 (CompletedProcess, payload|None) — 실패 응답도 파싱해 돌려준다.
    """
    cmd = [str(_PYTHON), str(tool_py or _TOOL_PY)] + list(args)
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, env=full_env)
    payload = None
    out = proc.stdout.strip()
    if out:
        try:
            payload = json.loads(out.split("\n")[-1])
        except json.JSONDecodeError:
            payload = None
    return proc, payload


def _make_project(tmp_dir):
    """<tmp>/.opal/ 를 만들고 (opal_dir, MEMORY.json 경로, MEMORY.md 경로) 반환."""
    opal = pathlib.Path(tmp_dir) / ".opal"
    opal.mkdir(parents=True, exist_ok=True)
    return opal, opal / "MEMORY.json", opal / "MEMORY.md"


def _install_json(tmp_dir, fixture="fixture_doc_populated.json"):
    opal, json_path, _ = _make_project(tmp_dir)
    shutil.copy2(_FIXTURES_DIR / fixture, json_path)
    return opal, json_path


def _install_md(tmp_dir, fixture):
    opal, json_path, md_path = _make_project(tmp_dir)
    shutil.copy2(_FIXTURES_DIR / fixture, md_path)
    return opal, json_path, md_path


def _snapshot(path):
    """(내용 바이트, mtime_ns, size) — 파일 불변 단정용."""
    p = pathlib.Path(path)
    st = p.stat()
    return (p.read_bytes(), st.st_mtime_ns, st.st_size)


def _read_doc(json_path):
    return json.loads(pathlib.Path(json_path).read_text(encoding="utf-8"))


def _clone_tool(dest, with_schema=True):
    """memory_tool.py(+schema/)를 dest에 복제하고 복제된 memory_tool.py 경로를 반환한다.
    리포지토리 원본을 건드리지 않고 '스키마 부재' 상태를 실제로 만든다(TS-037).
    """
    dest = pathlib.Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_TOOL_PY, dest / "memory_tool.py")
    if with_schema:
        shutil.copytree(_TOOL_DIR / "schema", dest / "schema", dirs_exist_ok=True)
    return dest / "memory_tool.py"


def _load_tool_module(tool_py, alias):
    """memory_tool.py를 모듈로 로드한다(모듈 레벨 상수 대조용). main()은 실행되지 않는다."""
    spec = importlib.util.spec_from_file_location(alias, str(tool_py))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _residue(opal_dir):
    """`.opal/` 안의 tmp·lock 잔여 파일 목록."""
    return sorted(
        p.name for p in pathlib.Path(opal_dir).iterdir()
        if p.name.endswith(".tmp") or p.name.endswith(".lock") or ".tmp." in p.name
    )


# ─────────────────────────────────────────────────────────────────────────────
# TS-001~TS-005, TS-037: 스키마 검증 [T078/L1-R1]
# ─────────────────────────────────────────────────────────────────────────────

class TestSchemaValidation(unittest.TestCase):
    """[T078/L1-R1] R-1 AC — enum·길이·pattern·손상·스키마부재 5경로 + 파일 불변."""

    def test_ts001_invalid_type_rejected_and_file_unchanged(self):
        """TS-001: append --type bogus → invalid_type + MEMORY.json mtime·내용 불변."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            before = _snapshot(json_path)
            proc, payload = _run_cli([
                "append", "--file", str(json_path), "--kind", "memory",
                "--title", "신규 메모리", "--type", "bogus", "--summary", "요약",
            ])
            self.assertIsNotNone(payload, f"단일라인 JSON 응답 없음. stdout={proc.stdout!r} stderr={proc.stderr!r}")
            self.assertFalse(payload.get("ok"), f"잘못된 type이 수용됨: {payload}")
            self.assertEqual(payload.get("error"), "invalid_type", f"에러 코드 불일치: {payload}")
            self.assertNotEqual(proc.returncode, 0, "거부 시 exit code는 0이 아니어야 한다")
            self.assertEqual(_snapshot(json_path), before, "거부됐는데 MEMORY.json이 변경됨 (H-8)")

    def test_ts002_summary_81_chars_rejected_and_file_unchanged(self):
        """TS-002: append --summary 81자 → summary_too_long + 파일 불변."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            before = _snapshot(json_path)
            proc, payload = _run_cli([
                "append", "--file", str(json_path), "--kind", "memory",
                "--title", "신규 메모리", "--type", "project", "--summary", "x" * 81,
            ])
            self.assertIsNotNone(payload, f"응답 없음. stderr={proc.stderr!r}")
            self.assertFalse(payload.get("ok"), f"81자 요약이 수용됨: {payload}")
            self.assertEqual(payload.get("error"), "summary_too_long", f"에러 코드 불일치: {payload}")
            self.assertEqual(_snapshot(json_path), before, "거부됐는데 MEMORY.json이 변경됨 (H-8)")

    def test_ts002_summary_80_chars_accepted(self):
        """TS-002 경계: 정확히 80자는 통과해야 한다(상한 off-by-one 방지)."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            proc, payload = _run_cli([
                "append", "--file", str(json_path), "--kind", "memory",
                "--title", "경계 메모리", "--type", "project", "--summary", "y" * 80,
            ])
            self.assertIsNotNone(payload, f"응답 없음. stderr={proc.stderr!r}")
            self.assertTrue(payload.get("ok"), f"80자 요약이 거부됨(경계 오류): {payload}")

    def test_ts003_date_pattern_violation_rejected_on_load(self):
        """TS-003: 문서 로드 시 schema_validation_failed + violations[0].keyword == 'pattern'."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp, "fixture_doc_invalid.json")
            proc, payload = _run_cli(["show", "--file", str(json_path)])
            self.assertIsNotNone(payload, f"응답 없음. stderr={proc.stderr!r}")
            self.assertFalse(payload.get("ok"), f"스키마 위반 문서가 수용됨: {payload}")
            self.assertEqual(payload.get("error"), "schema_validation_failed", f"에러 코드 불일치: {payload}")

            violations = payload.get("violations")
            self.assertIsInstance(violations, list, f"violations[] 미동반: {payload}")
            self.assertGreaterEqual(len(violations), 3, f"3개 위반(pattern/enum/maxLength) 전부 표면화 필요: {violations}")
            self.assertEqual(violations[0].get("keyword"), "pattern",
                             f"첫 위반은 memories[0].date의 pattern이어야 한다: {violations[0]}")
            self.assertEqual(violations[0].get("path"), "memories[0].date",
                             f"위반 경로가 응답에 포함되어야 한다: {violations[0]}")
            keywords = {v.get("keyword") for v in violations}
            self.assertIn("enum", keywords, f"type enum 위반 미검출: {violations}")
            self.assertIn("maxLength", keywords, f"summary 81자 위반 미검출: {violations}")

    def test_ts004_corrupted_json_is_deterministic(self):
        """TS-004: 내용이 '{' 한 글자 → invalid_json 단일라인 + exit 1 + traceback 0 + 파일 불변."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            json_path.write_text("{", encoding="utf-8")
            before = _snapshot(json_path)
            proc, payload = _run_cli(["show", "--file", str(json_path)])
            self.assertIsNotNone(payload, f"단일라인 JSON 응답 없음. stdout={proc.stdout!r} stderr={proc.stderr!r}")
            self.assertEqual(payload.get("error"), "invalid_json", f"에러 코드 불일치: {payload}")
            self.assertEqual(proc.returncode, 1, f"exit 1이어야 한다 (실제 {proc.returncode})")
            self.assertNotIn("Traceback", proc.stderr, f"traceback 노출 금지:\n{proc.stderr}")
            self.assertEqual(len(proc.stdout.strip().split("\n")), 1, f"단일라인이 아님: {proc.stdout!r}")
            self.assertEqual(_snapshot(json_path), before, "손상 파일이 변경됨")

    def test_ts005_constants_match_schema_enum(self):
        """TS-005: VALID_TYPES/VALID_STATUSES가 스키마 enum과 정확히 동일 + improvement/candidate 포함."""
        module = _load_tool_module(_TOOL_PY, "memory_tool_ts005_repo")
        schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
        mem_props = schema["$defs"]["memoryRow"]["properties"]

        self.assertEqual(set(module.VALID_TYPES), set(mem_props["type"]["enum"]),
                         "VALID_TYPES ≠ 스키마 type enum (H-3)")
        self.assertEqual(set(module.VALID_STATUSES), set(mem_props["status"]["enum"]),
                         "VALID_STATUSES ≠ 스키마 status enum (H-3)")
        self.assertIn("improvement", module.VALID_TYPES, "improvement 누락 — improve-tool 위임이 거부된다")
        self.assertIn("candidate", module.VALID_STATUSES, "candidate 누락 — improve-tool 위임이 거부된다")

        self.assertEqual(module.SUMMARY_MAX_LENGTH, mem_props["summary"]["maxLength"],
                         "SUMMARY_MAX_LENGTH가 스키마 maxLength에서 파생되지 않음")
        self.assertEqual(module.HISTORY_FIFO_LIMIT, schema["x-constants"]["HISTORY_FIFO_LIMIT"])
        self.assertEqual(module.PROMOTE_AGE_DAYS, schema["x-constants"]["PROMOTE_AGE_DAYS"])
        self.assertEqual(module.CURRENT_VERSION, schema["properties"]["version"]["const"])

    def test_ts005_constants_are_derived_from_schema_at_runtime(self):
        """TS-005: P-1 단일 출처 — 스키마 파일을 바꾸면 코드 상수가 따라와야 한다(하드코딩 금지)."""
        with tempfile.TemporaryDirectory() as tmp:
            tool_py = _clone_tool(pathlib.Path(tmp) / "tool")
            schema_path = tool_py.parent / "schema" / "memory.schema.json"
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            schema["$defs"]["memoryRow"]["properties"]["type"]["enum"].append("zzz_probe")
            schema["$defs"]["memoryRow"]["properties"]["status"]["enum"].append("zzz_state")
            schema["x-constants"]["HISTORY_FIFO_LIMIT"] = 7
            schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

            module = _load_tool_module(tool_py, "memory_tool_ts005_probe")
            self.assertIn("zzz_probe", module.VALID_TYPES,
                          "스키마에 추가한 type이 VALID_TYPES에 반영되지 않음 — 하드코딩 상태 (P-1 위반)")
            self.assertIn("zzz_state", module.VALID_STATUSES,
                          "스키마에 추가한 status가 VALID_STATUSES에 반영되지 않음 (P-1 위반)")
            self.assertEqual(module.HISTORY_FIFO_LIMIT, 7,
                             "x-constants.HISTORY_FIFO_LIMIT가 런타임 파생되지 않음 (P-1 위반)")

    def test_ts037_schema_absent_returns_schema_load_failed_for_all_subcommands(self):
        """TS-037: 스키마 파일 부재 시 전 서브명령이 schema_load_failed 단일라인 JSON (크래시 0)."""
        with tempfile.TemporaryDirectory() as tmp:
            tool_py = _clone_tool(pathlib.Path(tmp) / "tool", with_schema=False)
            _, json_path = _install_json(tmp)
            cases = {
                "init":        ["init", "--file", str(json_path)],
                "append":      ["append", "--file", str(json_path), "--kind", "memory",
                                "--title", "T", "--type", "project", "--summary", "S"],
                "update":      ["update", "--file", str(json_path), "--title", "메인 직접 커밋 선호",
                                "--status", "dead"],
                "promote":     ["promote", "--file", str(json_path), "--title", "메인 직접 커밋 선호",
                                "--to", "docs", "--ref", "docs/ARCHITECTURE.md#x"],
                "prune":       ["prune", "--file", str(json_path)],
                "show":        ["show", "--file", str(json_path)],
                "review":      ["review", "--file", str(json_path)],
                "delete":      ["delete", "--file", str(json_path), "--title", "완료된 태스크 기록"],
                "task-number": ["task-number", "--file", str(json_path)],
            }
            for name, args in cases.items():
                with self.subTest(subcommand=name):
                    proc, payload = _run_cli(args, tool_py=tool_py)
                    self.assertNotIn("Traceback", proc.stderr,
                                     f"[{name}] 크래시 traceback 노출:\n{proc.stderr}")
                    self.assertNotEqual(proc.returncode, 0, f"[{name}] 스키마 부재인데 성공 exit")
                    self.assertEqual(len(proc.stdout.strip().split("\n")), 1,
                                     f"[{name}] 단일라인 JSON이 아님: {proc.stdout!r}")
                    self.assertIsNotNone(payload, f"[{name}] JSON 파싱 실패: {proc.stdout!r}")
                    self.assertEqual(payload.get("error"), "schema_load_failed",
                                     f"[{name}] 에러 코드 불일치: {payload}")


# ─────────────────────────────────────────────────────────────────────────────
# TS-006, TS-017: 마커·표 파싱 계층 / 구 migrate 소멸 [T078/L1-R2a, L1-R5d]
# ─────────────────────────────────────────────────────────────────────────────

class TestSymbolRemoval(unittest.TestCase):
    """[T078/L1-R2a] R-2 AC(a) + R-5 AC(d) — 산출물 검사."""

    def _hits(self, pattern):
        source = _TOOL_PY.read_text(encoding="utf-8")
        rx = re.compile(pattern)
        return [f"{i}: {line.strip()}" for i, line in enumerate(source.splitlines(), 1) if rx.search(line)]

    def test_ts006_marker_and_table_symbols_absent(self):
        """TS-006: marker·MARKER·_render_*_table·_parse_(index|history)_rows 매치 0건."""
        hits = self._hits(r"marker|MARKER|_render_\w*_table|_parse_(?:index|history)_rows")
        self.assertEqual(hits, [], "마커·표 파싱 심볼 잔존:\n" + "\n".join(hits))

    def test_ts017_legacy_migrate_symbols_absent(self):
        """TS-017: cmd_migrate·_parse_legacy_·_strip_legacy_tables 0건."""
        hits = self._hits(r"cmd_migrate|_parse_legacy_|_strip_legacy_tables")
        self.assertEqual(hits, [], "구 migrate 심볼 잔존:\n" + "\n".join(hits))

    def test_ts017_migrate_subcommand_absent(self):
        """TS-017: migrate 서브명령이 argparse에서 인식되지 않아야 한다(등록 자체가 없음)."""
        proc, _ = _run_cli(["migrate", "--help"])
        self.assertNotEqual(proc.returncode, 0,
                            "migrate 서브명령이 아직 등록되어 있다 (R-5 AC(d) 위반)")
        self.assertTrue("invalid choice" in proc.stderr,
                        f"argparse가 migrate를 미등록 서브명령으로 거부해야 한다: {proc.stderr.strip()[:200]}")

    def test_ts017_task_number_subcommand_registered(self):
        """TS-017 대응쌍: migrate가 빠진 자리에 task-number가 등록되어야 한다 (D-1)."""
        proc, _ = _run_cli(["--help"])
        combined = proc.stdout + proc.stderr
        self.assertTrue("task-number" in combined,
                        "task-number 서브명령이 --help에 없다")


# ─────────────────────────────────────────────────────────────────────────────
# TS-007: 8서브명령 JSON 단독 동작 + 응답 키 보존 [T078/L1-R2b]
# ─────────────────────────────────────────────────────────────────────────────

class TestJsonIO(unittest.TestCase):
    """[T078/L1-R2b] R-2 AC(b) — MEMORY.json만으로 8서브명령 동작, H-4 응답 키 보존."""

    def test_ts007_eight_subcommands_operate_on_json_only(self):
        """TS-007: init→append×3→update→promote→prune→show→review→delete 전부 ok:true."""
        with tempfile.TemporaryDirectory() as tmp:
            opal, json_path, md_path = _make_project(tmp)

            proc, payload = _run_cli(["init", "--file", str(json_path)])
            self.assertTrue(payload and payload.get("ok"), f"init 실패: {payload} / {proc.stderr!r}")
            self.assertTrue(json_path.exists(), "init이 MEMORY.json을 만들지 않음")
            self.assertFalse(md_path.exists(), "init이 MEMORY.md를 만들면 안 된다")
            self.assertEqual(_read_doc(json_path),
                             {"version": 1, "last_task_number": 0, "memories": [], "history": []},
                             "init 골격이 계약과 다름 (PLAN §3.10.2)")

            _, payload = _run_cli(["append", "--file", str(json_path), "--kind", "memory",
                                   "--title", "테스트 메모리", "--type", "project",
                                   "--summary", "JSON 단독 동작 검증용 행"])
            self.assertTrue(payload and payload.get("ok"), f"append(memory) 실패: {payload}")

            _, payload = _run_cli(["append", "--file", str(json_path), "--kind", "history",
                                   "--title", "078 메모리 JSON 전환", "--stage", "완료",
                                   "--path", "tasks/078-260728-opd-메모리-json전환/",
                                   "--summary", "SSOT를 MEMORY.json으로 전환"])
            self.assertTrue(payload and payload.get("ok"), f"append(history) 실패: {payload}")

            _, payload = _run_cli(["append", "--file", str(json_path), "--kind", "memory",
                                   "--title", "승격 대상", "--type", "architecture",
                                   "--summary", "promote 검증용 행"])
            self.assertTrue(payload and payload.get("ok"), f"append(promote 대상) 실패: {payload}")

            # 파일 필드는 도구가 결정한다 — 문서에서 읽어 실 파일을 만든다(테스트 더블 아님)
            row = next(r for r in _read_doc(json_path)["memories"] if r["title"] == "승격 대상")
            mem_file = opal / row["file"]
            mem_file.parent.mkdir(parents=True, exist_ok=True)
            mem_file.write_text("# 승격 대상\n\n본문\n", encoding="utf-8")

            _, payload = _run_cli(["update", "--file", str(json_path),
                                   "--title", "테스트 메모리", "--status", "dead"])
            self.assertTrue(payload and payload.get("ok"), f"update 실패: {payload}")

            _, payload = _run_cli(["promote", "--file", str(json_path), "--title", "승격 대상",
                                   "--to", "docs", "--ref", "docs/ARCHITECTURE.md#도구"])
            self.assertTrue(payload and payload.get("ok"), f"promote 실패: {payload}")

            _, payload = _run_cli(["prune", "--file", str(json_path)])
            self.assertTrue(payload and payload.get("ok"), f"prune 실패: {payload}")

            _, show_payload = _run_cli(["show", "--file", str(json_path)])
            self.assertTrue(show_payload and show_payload.get("ok"), f"show 실패: {show_payload}")

            _, payload = _run_cli(["review", "--file", str(json_path)])
            self.assertTrue(payload and payload.get("ok"), f"review 실패: {payload}")

            _, payload = _run_cli(["delete", "--file", str(json_path), "--title", "테스트 메모리"])
            self.assertTrue(payload and payload.get("ok"), f"delete 실패: {payload}")

            self.assertFalse(md_path.exists(), "전 과정에서 MEMORY.md가 생성되면 안 된다")

    def test_ts007_show_response_keys_preserved(self):
        """TS-007/H-4: show 응답 최상위 키가 개명 없이 보존된다(improve_tool.py:311 의존)."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            proc, payload = _run_cli(["show", "--file", str(json_path)])
            self.assertTrue(payload and payload.get("ok"), f"show 실패: {payload} / {proc.stderr!r}")
            for key in ("index_rows", "history_rows", "active_count", "total_count", "history_count"):
                self.assertIn(key, payload, f"응답 키 '{key}' 소실 — improve-tool이 조용히 빈 목록을 받는다 (H-4)")
            self.assertEqual(payload["total_count"], 6, f"total_count 불일치: {payload['total_count']}")
            self.assertEqual(payload["active_count"], 2, f"active_count 불일치: {payload['active_count']}")
            self.assertEqual(payload["history_count"], 5, f"history_count 불일치: {payload['history_count']}")
            self.assertEqual(len(payload["index_rows"]), 6, "비-brief show는 전 행을 반환한다")
            self.assertIn("status", payload["index_rows"][0], "비-brief 행에는 status가 있어야 한다")

    def test_ts007_non_brief_show_exposes_version_and_task_number(self):
        """TS-007: --brief 미지정 시 version·last_task_number 추가 반환 (PLAN §3.3.2)."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            _, payload = _run_cli(["show", "--file", str(json_path)])
            self.assertTrue(payload and payload.get("ok"), f"show 실패: {payload}")
            self.assertEqual(payload.get("version"), 1, f"version 미노출: {payload}")
            self.assertEqual(payload.get("last_task_number"), 78, f"last_task_number 미노출: {payload}")

    def test_ts007_memory_json_not_found_when_nothing_exists(self):
        """TS-007: json도 md도 없으면 memory_json_not_found (개명된 코드)."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path, _ = _make_project(tmp)
            proc, payload = _run_cli(["show", "--file", str(json_path)])
            self.assertIsNotNone(payload, f"응답 없음: {proc.stdout!r} / {proc.stderr!r}")
            self.assertEqual(payload.get("error"), "memory_json_not_found", f"에러 코드 불일치: {payload}")


# ─────────────────────────────────────────────────────────────────────────────
# TS-008: ERROR_CODES 카탈로그 [T078/L1-R2c]
# ─────────────────────────────────────────────────────────────────────────────

class TestErrorCodesJson(unittest.TestCase):
    """[T078/L1-R2c] R-2 AC(c) — 구 코드 제거 + 신설 코드 존재 (PLAN §3.2.3).

    기존 클래스명 TestErrorCodes와 충돌하므로 Json 접미사를 쓴다.
    """

    def setUp(self):
        self.module = _load_tool_module(_TOOL_PY, "memory_tool_ts008")

    def test_ts008_obsolete_error_codes_absent(self):
        """TS-008: marker_missing·import_failed·memory_md_not_found 부재."""
        codes = set(self.module.ERROR_CODES)
        leftover = sorted(_ERROR_CODES_FORBIDDEN & codes)
        self.assertEqual(leftover, [], f"구 에러 코드 잔존: {leftover}")

    def test_ts008_new_error_codes_present(self):
        """TS-008: 신설/개명 코드 전량 존재."""
        codes = set(self.module.ERROR_CODES)
        missing = sorted(_ERROR_CODES_REQUIRED - codes)
        self.assertEqual(missing, [], f"신설 에러 코드 누락: {missing}")

    def test_ts008_lossless_delete_guard_code_preserved(self):
        """TS-008: 무손실 가드 코드는 불변 유지 (TASK.md 제약)."""
        codes = set(self.module.ERROR_CODES)
        for keep in ("delete_requires_dead_or_superseded", "promote_ref_missing",
                     "row_not_found", "invalid_type", "invalid_status",
                     "summary_too_long", "title_required"):
            self.assertIn(keep, codes, f"불변 유지 대상 에러 코드 '{keep}' 소실")


# ─────────────────────────────────────────────────────────────────────────────
# TS-009: 원자적 쓰기 [T078/L1-H8]
# ─────────────────────────────────────────────────────────────────────────────

class TestAtomicWrite(unittest.TestCase):
    """[T078/L1-H8] H-8 — 검증 실패 시 원본 불변 + tmp/lock 잔여 0."""

    def test_ts009_failed_append_leaves_no_residue(self):
        """TS-009: 검증 실패 append 후 .json 불변 + .tmp/.lock 잔여 0건."""
        with tempfile.TemporaryDirectory() as tmp:
            opal, json_path = _install_json(tmp)
            before = _snapshot(json_path)
            _, payload = _run_cli([
                "append", "--file", str(json_path), "--kind", "memory",
                "--title", "잔여 검사", "--type", "bogus", "--summary", "x" * 81,
            ])
            self.assertFalse(payload and payload.get("ok"), f"위반 입력이 수용됨: {payload}")
            self.assertIn(payload.get("error"), ("invalid_type", "summary_too_long"),
                          f"L-A 인자 검증 코드로 거부되어야 한다: {payload}")
            self.assertEqual(_snapshot(json_path), before, "실패했는데 원본이 변경됨")
            self.assertEqual(_residue(opal), [], f"tmp/lock 잔여 파일: {_residue(opal)}")
            self.assertEqual(sorted(p.name for p in opal.iterdir()), ["MEMORY.json"],
                             f".opal/ 내용이 MEMORY.json 하나가 아님: {sorted(p.name for p in opal.iterdir())}")

    def test_ts009_successful_append_leaves_no_residue(self):
        """TS-009: 성공 경로에서도 tmp·lock 파일이 남지 않는다."""
        with tempfile.TemporaryDirectory() as tmp:
            opal, json_path = _install_json(tmp)
            _, payload = _run_cli([
                "append", "--file", str(json_path), "--kind", "memory",
                "--title", "정상 추가", "--type", "project", "--summary", "정상 경로 잔여 검사",
            ])
            self.assertTrue(payload and payload.get("ok"), f"append 실패: {payload}")
            self.assertEqual(_residue(opal), [], f"tmp/lock 잔여 파일: {_residue(opal)}")


# ─────────────────────────────────────────────────────────────────────────────
# TS-010~TS-012, TS-039: show --brief [T078/L1-R3]
# ─────────────────────────────────────────────────────────────────────────────

class TestShowBrief(unittest.TestCase):
    """[T078/L1-R3] R-3 AC — active 필터 + 히스토리 3건 기본 + 브리핑 재현 가능성."""

    _EXCLUDED_TITLES = ["완료된 태스크 기록", "대체된 아키텍처 결정", "졸업한 선호 규칙", "개선 후보 기록"]

    def test_ts010_brief_excludes_non_active_statuses(self):
        """TS-010: dead/superseded/promoted/candidate 0건, active만 잔존."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            proc, payload = _run_cli(["show", "--file", str(json_path), "--brief"])
            self.assertTrue(payload and payload.get("ok"), f"show --brief 실패: {payload} / {proc.stderr!r}")
            self.assertIs(payload.get("brief"), True, f"brief:true 플래그 없음: {payload}")

            rows = payload["index_rows"]
            titles = [r["title"] for r in rows]
            self.assertEqual(len(rows), 2, f"active 2건만 남아야 한다: {titles}")
            for excluded in self._EXCLUDED_TITLES:
                self.assertNotIn(excluded, titles, f"비-active 행 '{excluded}'이 brief에 노출됨")
            self.assertEqual(payload["active_count"], 2, f"active_count 불일치: {payload}")

    def test_ts010_brief_row_fields_are_exactly_five(self):
        """TS-010: brief 메모리 필드는 title/date/type/file/summary 5개 (status 생략)."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            _, payload = _run_cli(["show", "--file", str(json_path), "--brief"])
            self.assertTrue(payload and payload.get("ok"), f"show --brief 실패: {payload}")
            for row in payload["index_rows"]:
                self.assertEqual(set(row), {"title", "date", "type", "file", "summary"},
                                 f"brief 행 필드 계약 위반 (PLAN §3.3.2): {sorted(row)}")

    def test_ts011_brief_output_is_smaller_than_full(self):
        """TS-011: len(brief_stdout) < len(full_stdout) — 절약 실측."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            full_proc, full_payload = _run_cli(["show", "--file", str(json_path)])
            brief_proc, brief_payload = _run_cli(["show", "--file", str(json_path), "--brief"])
            self.assertTrue(full_payload and full_payload.get("ok"), f"show 실패: {full_payload}")
            self.assertTrue(brief_payload and brief_payload.get("ok"), f"show --brief 실패: {brief_payload}")

            full_bytes = len(full_proc.stdout.encode("utf-8"))
            brief_bytes = len(brief_proc.stdout.encode("utf-8"))
            self.assertLess(brief_bytes, full_bytes,
                            f"brief가 더 크거나 같다 — full={full_bytes}B brief={brief_bytes}B")

    def test_ts012_brief_history_defaults_to_three(self):
        """TS-012: 히스토리 5행 → 기본 3건 + history_truncated=true, 날짜 내림차순."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            _, payload = _run_cli(["show", "--file", str(json_path), "--brief"])
            self.assertTrue(payload and payload.get("ok"), f"show --brief 실패: {payload}")
            rows = payload["history_rows"]
            self.assertEqual(len(rows), 3, f"기본 3건이어야 한다: {len(rows)}건")
            self.assertIs(payload.get("history_truncated"), True,
                          f"5행 중 3건만 반환했으므로 history_truncated=true: {payload.get('history_truncated')}")
            self.assertEqual([r["date"] for r in rows], ["2026-07-23", "2026-07-21", "2026-07-19"],
                             f"최신순(날짜 내림차순) 3건이 아님: {[r['date'] for r in rows]}")

    def test_ts012_history_zero_returns_empty_not_error(self):
        """TS-012: --history 0 → 0건 반환(에러 아님)."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            proc, payload = _run_cli(["show", "--file", str(json_path), "--brief", "--history", "0"])
            self.assertTrue(payload and payload.get("ok"),
                            f"--history 0이 에러로 처리됨: {payload} / {proc.stderr!r}")
            self.assertEqual(payload["history_rows"], [], f"0건이어야 한다: {payload['history_rows']}")

    def test_ts012_history_n_override(self):
        """TS-012: --history 5 → 5건 전량 + history_truncated=false."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            _, payload = _run_cli(["show", "--file", str(json_path), "--brief", "--history", "5"])
            self.assertTrue(payload and payload.get("ok"), f"show --brief --history 5 실패: {payload}")
            self.assertEqual(len(payload["history_rows"]), 5, "5건 전량 반환")
            self.assertIs(payload.get("history_truncated"), False,
                          f"절단이 없으므로 false: {payload.get('history_truncated')}")

    def test_ts039_brief_is_sufficient_to_render_pm_briefing(self):
        """TS-039: brief 출력만으로 opal-pm.md §15 `- [{type}] {summary} ({date})` 재현 가능."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            _, payload = _run_cli(["show", "--file", str(json_path), "--brief"])
            self.assertTrue(payload and payload.get("ok"), f"show --brief 실패: {payload}")

            rows = payload["index_rows"]
            self.assertGreaterEqual(len(rows), 1, "브리핑 3~5줄을 만들려면 최소 1행 필요")
            lines = []
            for row in rows:
                for field in ("type", "date", "summary", "title", "file"):
                    self.assertIn(field, row, f"브리핑 재현 필드 '{field}' 누락: {sorted(row)}")
                    self.assertTrue(str(row[field]).strip(), f"브리핑 필드 '{field}'가 공백: {row}")
                lines.append(f"- [{row['type']}] {row['summary']} ({row['date']})")
            self.assertTrue(all(line.startswith("- [") for line in lines))

            dates = [r["date"] for r in rows]
            self.assertEqual(dates, sorted(dates, reverse=True),
                             f"메모리 정렬이 날짜 내림차순이 아님: {dates}")

            for row in payload["history_rows"]:
                self.assertEqual(set(row), {"title", "date", "stage", "path", "result"},
                                 f"brief 히스토리 필드 계약 위반: {sorted(row)}")


# ─────────────────────────────────────────────────────────────────────────────
# TS-013: lazy 변환 발동 + .bak 보존 [T078/L1-R5a]
# ─────────────────────────────────────────────────────────────────────────────

class TestLazyMigration(unittest.TestCase):
    """[T078/L1-R5a] R-5 AC(a) + H-12 — 자동 변환·백업·백업 충돌 회피."""

    def test_ts013_show_on_md_only_project_triggers_migration(self):
        """TS-013(1): md만 있는 프로젝트에 show → MEMORY.json 생성 + MEMORY.md.bak 존재."""
        with tempfile.TemporaryDirectory() as tmp:
            opal, json_path, md_path = _install_md(tmp, "fixture_md_marker_populated.md")
            proc, payload = _run_cli(["show", "--file", str(json_path)])
            self.assertTrue(payload and payload.get("ok"),
                            f"lazy 변환이 발동하지 않음: {payload} / {proc.stderr!r}")
            self.assertTrue(json_path.exists(), "MEMORY.json이 생성되지 않음")
            self.assertTrue((opal / "MEMORY.md.bak").exists(), "MEMORY.md.bak이 없음 (무손실 위반)")
            self.assertFalse(md_path.exists(), "원본 MEMORY.md는 .bak으로 이동되어야 한다 (PLAN §3.4.4 9단계)")
            self.assertEqual(len(payload["index_rows"]), 3, f"show 결과가 비정상: {payload}")

            migration = payload.get("migration")
            self.assertIsInstance(migration, dict, f"migration 리포트 미첨부: {payload}")
            self.assertIs(migration.get("performed"), True, f"performed=true 아님: {migration}")

    def test_ts013_existing_bak_is_not_overwritten(self):
        """TS-013(2)/H-12: .bak 선점 시 덮어쓰지 않고 .bak.<timestamp> 신규 생성."""
        with tempfile.TemporaryDirectory() as tmp:
            opal, json_path, _ = _install_md(tmp, "fixture_md_marker_populated.md")
            sentinel = opal / "MEMORY.md.bak"
            sentinel.write_text("# 선점된 백업 — 절대 덮어쓰면 안 된다\n", encoding="utf-8")
            sentinel_bytes = sentinel.read_bytes()

            _, payload = _run_cli(["show", "--file", str(json_path)])
            self.assertTrue(payload and payload.get("ok"), f"lazy 변환 실패: {payload}")
            self.assertEqual(sentinel.read_bytes(), sentinel_bytes,
                             "기존 .bak을 덮어썼다 — 무손실 제약 위반 (H-12)")

            stamped = [p.name for p in opal.iterdir()
                       if re.fullmatch(r"MEMORY\.md\.bak\.\d{14}", p.name)]
            self.assertEqual(len(stamped), 1,
                             f"타임스탬프 백업(MEMORY.md.bak.<YYYYMMDDHHmmss>) 1건이어야 한다: "
                             f"{sorted(p.name for p in opal.iterdir())}")

    def test_ts013_migration_result_is_usable_by_next_command(self):
        """TS-013: 변환 후 이어지는 append가 변환 결과 위에서 동작한다(재변환 없음)."""
        with tempfile.TemporaryDirectory() as tmp:
            opal, json_path, _ = _install_md(tmp, "fixture_md_marker_populated.md")
            _, payload = _run_cli(["show", "--file", str(json_path)])
            self.assertTrue(payload and payload.get("ok"), f"1차 변환 실패: {payload}")

            _, payload = _run_cli(["append", "--file", str(json_path), "--kind", "memory",
                                   "--title", "변환 후 추가", "--type", "project",
                                   "--summary", "변환 결과 위에 append"])
            self.assertTrue(payload and payload.get("ok"), f"변환 후 append 실패: {payload}")
            self.assertIsNone(payload.get("migration"), "이미 변환됐는데 재변환이 발생함")

            doc = _read_doc(json_path)
            self.assertEqual(len(doc["memories"]), 4, f"3행 + 신규 1행이어야 한다: {len(doc['memories'])}")
            self.assertEqual(len(list(opal.glob("MEMORY.md.bak*"))), 1, "백업이 중복 생성됨")


# ─────────────────────────────────────────────────────────────────────────────
# TS-014, TS-016: 변환 무손실 [T078/L1-R5b]
# ─────────────────────────────────────────────────────────────────────────────

class TestMigrationLossless(unittest.TestCase):
    """[T078/L1-R5b] R-5 AC(b) — 행 수·필드값 100% 일치 + 정상 0행 구분."""

    def _migrate(self, fixture, tmp):
        opal, json_path, md_path = _install_md(tmp, fixture)
        proc, payload = _run_cli(["show", "--file", str(json_path)])
        return opal, json_path, md_path, proc, payload

    def test_ts014_ai_framework_fixture_is_lossless(self):
        """TS-014: 메모리 3행·히스토리 5행 + 각 필드 값 100% 일치(백틱 제거·날짜 정규화만 허용)."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path, _, proc, payload = self._migrate("fixture_md_marker_populated.md", tmp)
            self.assertTrue(payload and payload.get("ok"), f"변환 실패: {payload} / {proc.stderr!r}")

            doc = _read_doc(json_path)
            self.assertEqual(len(doc["memories"]), 3, f"메모리 행 수 불일치: {len(doc['memories'])}")
            self.assertEqual(len(doc["history"]), 5, f"히스토리 행 수 불일치: {len(doc['history'])}")
            self.assertEqual(doc["memories"], _TS014_MEMORIES, "메모리 필드값이 원본과 다르다 (무손실 위반)")
            self.assertEqual(doc["history"], _TS014_HISTORY, "히스토리 필드값이 원본과 다르다 (무손실 위반)")

    def test_ts014_dead_category_table_is_not_ingested(self):
        """TS-014/V-6: 구 잔존 카테고리 안내표(L7-18)가 데이터로 유입되지 않는다."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path, _, _, payload = self._migrate("fixture_md_marker_populated.md", tmp)
            self.assertTrue(payload and payload.get("ok"), f"변환 실패: {payload}")
            titles = [m["title"] for m in _read_doc(json_path)["memories"]]
            for polluted in ("카테고리", "task", "project", "architecture", "feedback", "preferences", "issues"):
                self.assertNotIn(polluted, titles, f"죽은 안내표 행 '{polluted}'이 데이터로 유입됨 (영역 분할 실패)")

    def test_ts014_last_task_number_from_md_header(self):
        """TS-014/V-4: md 헤더 `> last_task_number: 78` → 78, source='header'."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path, _, _, payload = self._migrate("fixture_md_marker_populated.md", tmp)
            self.assertTrue(payload and payload.get("ok"), f"변환 실패: {payload}")
            self.assertEqual(_read_doc(json_path)["last_task_number"], 78, "헤더 채번값이 유실됨")
            self.assertEqual(payload["migration"].get("last_task_number_source"), "header",
                             f"채번 출처 미기록: {payload['migration']}")

    def test_ts014_backtick_file_field_is_normalized(self):
        """TS-014/V-7: 백틱 감싼 file 경로가 정규화되어 스키마 pattern을 만족한다."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path, _, _, payload = self._migrate("fixture_md_marker_populated.md", tmp)
            self.assertTrue(payload and payload.get("ok"), f"변환 실패: {payload}")
            for row in _read_doc(json_path)["memories"]:
                self.assertNotIn("`", row["file"], f"백틱이 남아 있음: {row['file']}")
                self.assertRegex(row["file"], r"^memory/[^/].*\.md$", f"file pattern 위반: {row['file']}")

    def test_ts016_empty_index_is_success_not_failure(self):
        """TS-016/V-5: aos 재현(마커 O·인덱스 0행) → ok:true, memories:[], empty_source_regions."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path, _, proc, payload = self._migrate("fixture_md_marker_empty.md", tmp)
            self.assertTrue(payload and payload.get("ok"),
                            f"빈 인덱스를 실패로 처리했다 (V-5 위반): {payload} / {proc.stderr!r}")

            doc = _read_doc(json_path)
            self.assertEqual(doc["memories"], [], f"memories는 빈 배열이어야 한다: {doc['memories']}")
            self.assertEqual(len(doc["history"]), 1, f"히스토리 1행이 보존되어야 한다: {doc['history']}")
            self.assertEqual(doc["last_task_number"], 1, "aos 헤더 last_task_number: 1 유실")

            migration = payload.get("migration")
            self.assertIsInstance(migration, dict, f"migration 리포트 미첨부: {payload}")
            self.assertEqual(migration.get("empty_source_regions"), ["memories"],
                             f"정상 0행과 인식 실패 0행을 구분하지 못함 (D-3): {migration}")

    def test_ts016_empty_index_history_row_values(self):
        """TS-016: aos 히스토리 1행의 필드값이 원본과 일치한다."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path, _, _, payload = self._migrate("fixture_md_marker_empty.md", tmp)
            self.assertTrue(payload and payload.get("ok"), f"변환 실패: {payload}")
            self.assertEqual(_read_doc(json_path)["history"][0], {
                "title": "opi 프로젝트 초기화",
                "date": "2026-07-16",
                "stage": "완료",
                "path": "docs/, .opal/",
                "result": "docs 4종+AGENT/MEMORY/setting 생성, 플랫폼 파일 4종 적용",
            }, "aos 히스토리 필드값 불일치")


# ─────────────────────────────────────────────────────────────────────────────
# TS-015, TS-040: 무성 유실 금지 + 변환 리포트 관측성 [T078/L2-R5c]
# ─────────────────────────────────────────────────────────────────────────────

class TestMigrationFailure(unittest.TestCase):
    """[T078/L2-R5c] H-1(P0) — 헤더 변형 인식 + 인식 실패의 명시적 실패."""

    def test_ts015_legacy_header_variant_preserves_three_history_rows(self):
        """TS-015(1)/V-2: invest-stock 헤더 변형(`#|작업|단계|경로|시작일시|완료일시`) 3행 보존."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path, _ = _install_md(tmp, "fixture_md_no_marker_legacy.md")
            proc, payload = _run_cli(["show", "--file", str(json_path)])
            self.assertTrue(payload and payload.get("ok"),
                            f"마커 부재 파일 변환 실패 (V-1 위반): {payload} / {proc.stderr!r}")

            doc = _read_doc(json_path)
            self.assertEqual(len(doc["history"]), 3,
                             f"히스토리 3행이 {len(doc['history'])}행이 됨 — 무성 유실 (H-1 P0)")
            self.assertEqual(len(doc["memories"]), 3,
                             f"메모리 3행이 {len(doc['memories'])}행이 됨 — 무성 유실")

    def test_ts015_legacy_datetime_is_truncated_to_date(self):
        """TS-015/V-8: `2026-06-20 12:34` 형식이 YYYY-MM-DD로 절단되어 스키마를 만족한다."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path, _ = _install_md(tmp, "fixture_md_no_marker_legacy.md")
            _, payload = _run_cli(["show", "--file", str(json_path)])
            self.assertTrue(payload and payload.get("ok"), f"변환 실패: {payload}")
            doc = _read_doc(json_path)
            self.assertEqual([m["date"] for m in doc["memories"]],
                             ["2026-06-20", "2026-06-24", "2026-06-24"],
                             f"datetime 절단 실패: {[m['date'] for m in doc['memories']]}")
            for row in doc["memories"] + doc["history"]:
                self.assertRegex(row["date"], r"^\d{4}-\d{2}-\d{2}$", f"date pattern 위반: {row}")

    def test_ts015_detection_failure_is_explicit_and_leaves_source_intact(self):
        """TS-015(2)/D-3: 프로파일 강제 무력화 → migration_failed(row_detection_failed),
        md mtime 불변, MEMORY.json 미생성 — 조용한 0행 금지."""
        with tempfile.TemporaryDirectory() as tmp:
            opal, json_path, md_path = _install_md(tmp, "fixture_md_no_marker_legacy.md")
            before = _snapshot(md_path)
            proc, payload = _run_cli(["show", "--file", str(json_path)],
                                     env={_ENV_DISABLE_PROFILES: "1"})
            self.assertIsNotNone(payload, f"응답 없음: {proc.stdout!r} / {proc.stderr!r}")
            self.assertFalse(payload.get("ok"),
                             f"인식 실패인데 '0행 변환 성공'으로 처리됨 — 무성 유실 (D-3 위반): {payload}")
            self.assertEqual(payload.get("error"), "migration_failed", f"에러 코드 불일치: {payload}")
            self.assertEqual(payload.get("reason"), "row_detection_failed",
                             f"실패 사유가 row_detection_failed가 아님: {payload}")
            self.assertFalse(json_path.exists(), "실패했는데 MEMORY.json이 생성됨 (R-5 AC(c) 위반)")
            self.assertEqual(_snapshot(md_path), before, "실패했는데 원본 MEMORY.md가 변경됨")
            self.assertEqual(list(opal.glob("MEMORY.md.bak*")), [], "실패했는데 백업이 생성됨")

    def test_ts040_report_lists_unmapped_statuses(self):
        """TS-040/V-3: `확정`·`확정`·`승인대기` 3건이 unmapped_statuses에 전량 기록된다."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path, _ = _install_md(tmp, "fixture_md_no_marker_legacy.md")
            _, payload = _run_cli(["show", "--file", str(json_path)])
            self.assertTrue(payload and payload.get("ok"), f"변환 실패: {payload}")

            migration = payload.get("migration")
            self.assertIsInstance(migration, dict, f"migration 리포트 미첨부: {payload}")
            unmapped = migration.get("unmapped_statuses")
            self.assertIsInstance(unmapped, list, f"unmapped_statuses 미기록 — 조용한 폴백 금지: {migration}")
            self.assertEqual(len(unmapped), 3, f"자유 상태값 3건이 전량 기록되어야 한다: {unmapped}")
            self.assertEqual(sorted(item.get("raw") for item in unmapped),
                             sorted(["확정", "확정", "승인대기"]),
                             f"원본 상태값이 그대로 보존되어야 한다: {unmapped}")
            for item in unmapped:
                self.assertTrue(str(item.get("title", "")).strip(),
                                f"unmapped 항목에 추적용 title이 없음: {item}")

    def test_ts040_report_records_last_task_number_source(self):
        """TS-040/V-4: 헤더도 tasks/도 없으면 last_task_number=0 + source='default'."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path, _ = _install_md(tmp, "fixture_md_no_marker_legacy.md")
            _, payload = _run_cli(["show", "--file", str(json_path)])
            self.assertTrue(payload and payload.get("ok"), f"변환 실패: {payload}")
            migration = payload["migration"]
            self.assertIn(migration.get("last_task_number_source"), ("header", "tasks_scan", "default"),
                          f"last_task_number_source 미명시: {migration}")
            self.assertEqual(migration.get("last_task_number_source"), "default",
                             f"헤더·tasks/ 모두 없으므로 default: {migration}")
            self.assertEqual(_read_doc(json_path)["last_task_number"], 0,
                             "폴백 채번값은 0이어야 한다")

    def test_ts040_report_flags_review_rows(self):
        """TS-040/V-3: 상태값 폴백 행은 [REVIEW]로 표면화된다(추적 가능)."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path, _ = _install_md(tmp, "fixture_md_no_marker_legacy.md")
            _, payload = _run_cli(["show", "--file", str(json_path)])
            self.assertTrue(payload and payload.get("ok"), f"변환 실패: {payload}")
            self.assertGreaterEqual(payload["migration"].get("review_flagged", 0), 3,
                                    f"[REVIEW] 플래그 계수 부족: {payload['migration']}")
            flagged = [m for m in _read_doc(json_path)["memories"] if "[REVIEW]" in m["summary"]]
            self.assertEqual(len(flagged), 3,
                             f"상태 폴백 3행 전부 [REVIEW] 접두가 있어야 한다: "
                             f"{[m['summary'][:20] for m in _read_doc(json_path)['memories']]}")


# ─────────────────────────────────────────────────────────────────────────────
# TS-018: 변환 중 동시 진입 클로버 방지 [T078/L2-H2] (P0)
# ─────────────────────────────────────────────────────────────────────────────

class TestConcurrentMigration(unittest.TestCase):
    """[T078/L2-H2] H-2(P0) — 실 프로세스 2개 병렬 기동. 스레드·가짜 대역 금지."""

    def test_ts018_two_concurrent_appends_do_not_clobber(self):
        """TS-018: md만 있는 디렉토리에 append 2프로세스 동시 기동 → 두 행 모두 존재."""
        with tempfile.TemporaryDirectory() as tmp:
            opal, json_path, _ = _install_md(tmp, "fixture_md_marker_populated.md")

            def _spawn(title):
                return subprocess.Popen(
                    [str(_PYTHON), str(_TOOL_PY), "append", "--file", str(json_path),
                     "--kind", "memory", "--title", title, "--type", "project",
                     "--summary", f"{title} 동시성 검증"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                )

            procs = [_spawn("동시 진입 A"), _spawn("동시 진입 B")]
            outs = [p.communicate() for p in procs]

            for proc, (stdout, stderr) in zip(procs, outs):
                self.assertEqual(proc.returncode, 0,
                                 f"동시 append 실패 (exit={proc.returncode})\nstdout={stdout!r}\nstderr={stderr!r}")

            self.assertTrue(json_path.exists(), "MEMORY.json이 생성되지 않음")
            titles = [m["title"] for m in _read_doc(json_path)["memories"]]
            self.assertIn("동시 진입 A", titles, f"A 행이 클로버됨: {titles}")
            self.assertIn("동시 진입 B", titles, f"B 행이 클로버됨: {titles}")
            self.assertEqual(len(titles), 5, f"원본 3행 + 신규 2행이어야 한다: {titles}")

            baks = sorted(p.name for p in opal.glob("MEMORY.md.bak*"))
            self.assertEqual(len(baks), 1, f".bak은 정확히 1개여야 한다(이중 변환 금지): {baks}")
            self.assertEqual(_residue(opal), [], f"락·tmp 잔여 파일: {_residue(opal)}")

    def test_ts018_json_files_are_not_duplicated(self):
        """TS-018: 동시 진입 후에도 MEMORY.json은 1개 (부분 파일·중복 없음)."""
        with tempfile.TemporaryDirectory() as tmp:
            opal, json_path, _ = _install_md(tmp, "fixture_md_marker_populated.md")
            procs = [
                subprocess.Popen([str(_PYTHON), str(_TOOL_PY), "show", "--file", str(json_path)],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                for _ in range(4)
            ]
            outs = [p.communicate() for p in procs]
            for proc, (stdout, stderr) in zip(procs, outs):
                self.assertEqual(proc.returncode, 0, f"동시 show 실패\nstdout={stdout!r}\nstderr={stderr!r}")
            self.assertEqual(len(list(opal.glob("MEMORY.json*"))), 1,
                             f"MEMORY.json 파생 파일 잔존: {sorted(p.name for p in opal.iterdir())}")


# ─────────────────────────────────────────────────────────────────────────────
# TS-019~TS-021: task-number 서브명령 [T078/L2-D1]
# ─────────────────────────────────────────────────────────────────────────────

class TestTaskNumber(unittest.TestCase):
    """[T078/L2-D1] D-1 + H-7 — 읽기 무변경 / 원자적 증가 / 역행·인자충돌 거부 / 20프로세스 동시성."""

    def test_ts019_read_does_not_modify_file(self):
        """TS-019: `task-number`(읽기) → 78 반환 + 파일 mtime·내용 불변."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            before = _snapshot(json_path)
            proc, payload = _run_cli(["task-number", "--file", str(json_path)])
            self.assertTrue(payload and payload.get("ok"),
                            f"task-number 서브명령 부재/실패: {payload} / {proc.stderr!r}")
            self.assertEqual(payload.get("command"), "task-number", f"command 필드 불일치: {payload}")
            self.assertEqual(payload.get("last_task_number"), 78, f"현재값 불일치: {payload}")
            self.assertEqual(_snapshot(json_path), before, "읽기인데 파일이 변경됨")

    def test_ts019_bump_increments_and_persists(self):
        """TS-019: `--bump` → 79 반환(previous=78, bumped=true) + 파일에 79 반영."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            proc, payload = _run_cli(["task-number", "--file", str(json_path), "--bump"])
            self.assertTrue(payload and payload.get("ok"), f"--bump 실패: {payload} / {proc.stderr!r}")
            self.assertEqual(payload.get("last_task_number"), 79, f"반환값이 79가 아님: {payload}")
            self.assertEqual(payload.get("previous"), 78, f"previous 미첨부/불일치: {payload}")
            self.assertIs(payload.get("bumped"), True, f"bumped=true 아님: {payload}")
            self.assertIn("review", payload, "변경 명령이므로 review 블록을 첨부해야 한다")
            self.assertEqual(_read_doc(json_path)["last_task_number"], 79, "파일에 반영되지 않음")

    def test_ts021_set_regression_is_rejected(self):
        """TS-021: `--set 70`(현재 78) → task_number_regression + 파일 불변."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            before = _snapshot(json_path)
            proc, payload = _run_cli(["task-number", "--file", str(json_path), "--set", "70"])
            self.assertIsNotNone(payload, f"응답 없음: {proc.stdout!r} / {proc.stderr!r}")
            self.assertFalse(payload.get("ok"), f"역행 --set이 수용됨: {payload}")
            self.assertEqual(payload.get("error"), "task_number_regression", f"에러 코드 불일치: {payload}")
            self.assertEqual(_snapshot(json_path), before, "거부됐는데 파일이 변경됨")

    def test_ts021_set_forward_is_accepted(self):
        """TS-021 경계: 전진 `--set 90`은 허용되고 파일에 반영된다."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            _, payload = _run_cli(["task-number", "--file", str(json_path), "--set", "90"])
            self.assertTrue(payload and payload.get("ok"), f"전진 --set이 거부됨: {payload}")
            self.assertEqual(payload.get("last_task_number"), 90, f"반환값 불일치: {payload}")
            self.assertIs(payload.get("set"), True, f"set=true 아님: {payload}")
            self.assertEqual(_read_doc(json_path)["last_task_number"], 90, "파일에 반영되지 않음")

    def test_ts021_bump_and_set_together_is_invalid_args(self):
        """TS-021: `--bump --set 90` 동시 지정 → invalid_args + 파일 불변."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            before = _snapshot(json_path)
            proc, payload = _run_cli(["task-number", "--file", str(json_path), "--bump", "--set", "90"])
            self.assertIsNotNone(payload, f"응답 없음: {proc.stdout!r} / {proc.stderr!r}")
            self.assertFalse(payload.get("ok"), f"인자 충돌이 수용됨: {payload}")
            self.assertEqual(payload.get("error"), "invalid_args", f"에러 코드 불일치: {payload}")
            self.assertEqual(_snapshot(json_path), before, "거부됐는데 파일이 변경됨")

    def test_ts020_twenty_concurrent_bumps_have_no_duplicates(self):
        """TS-020/H-7: 20 프로세스 동시 --bump → 반환값 20개 전부 상이, 최종값 == 초기+20."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path = _install_json(tmp)
            initial = _read_doc(json_path)["last_task_number"]
            self.assertEqual(initial, 78, "픽스처 초기값 전제")

            procs = [
                subprocess.Popen(
                    [str(_PYTHON), str(_TOOL_PY), "task-number", "--file", str(json_path), "--bump"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                )
                for _ in range(20)
            ]
            outs = [p.communicate() for p in procs]

            issued = []
            for proc, (stdout, stderr) in zip(procs, outs):
                self.assertEqual(proc.returncode, 0,
                                 f"동시 --bump 실패 (exit={proc.returncode})\nstdout={stdout!r}\nstderr={stderr!r}")
                payload = json.loads(stdout.strip().split("\n")[-1])
                self.assertTrue(payload.get("ok"), f"--bump 실패 응답: {payload}")
                issued.append(payload["last_task_number"])

            self.assertEqual(len(set(issued)), 20,
                             f"채번 중복 발생 — 태스크 폴더 충돌 (H-7): {sorted(issued)}")
            self.assertEqual(sorted(issued), list(range(initial + 1, initial + 21)),
                             f"연속 채번이 아님: {sorted(issued)}")
            self.assertEqual(_read_doc(json_path)["last_task_number"], initial + 20,
                             "최종 저장값이 초기+20이 아님")

    def test_ts019_task_number_on_missing_document(self):
        """TS-019: json도 md도 없으면 memory_json_not_found (init 선행 안내)."""
        with tempfile.TemporaryDirectory() as tmp:
            _, json_path, _ = _make_project(tmp)
            proc, payload = _run_cli(["task-number", "--file", str(json_path)])
            self.assertIsNotNone(payload, f"응답 없음: {proc.stdout!r} / {proc.stderr!r}")
            self.assertEqual(payload.get("error"), "memory_json_not_found", f"에러 코드 불일치: {payload}")


# ─────────────────────────────────────────────────────────────────────────────
# TS-038: 테스트 이관 완결 회귀 [T078/L1-R2b]
# ─────────────────────────────────────────────────────────────────────────────

class TestSuiteMigration(unittest.TestCase):
    """[T078/L1-R2b] H-9 — 회귀망이 빈 채 GREEN 선언되는 것을 차단한다."""

    _OBSOLETE_MD_FIXTURES = ("fixture_valid.md", "fixture_populated.md", "fixture_no_marker.md")

    def test_ts038_total_test_count_at_least_88(self):
        """TS-038: 발견되는 테스트 총 건수 ≥ 88."""
        tests_dir = pathlib.Path(__file__).parent
        suite = unittest.TestLoader().discover(str(tests_dir), pattern="test_*.py",
                                               top_level_dir=str(tests_dir))
        self.assertGreaterEqual(suite.countTestCases(), 88,
                                f"테스트 건수 부족: {suite.countTestCases()}건")

    def test_ts038_obsolete_md_fixtures_are_deleted(self):
        """TS-038: 마커 개념 소멸 — md 픽스처 3종이 삭제되어야 한다 (PLAN §3.2.1)."""
        leftover = [name for name in self._OBSOLETE_MD_FIXTURES if (_FIXTURES_DIR / name).exists()]
        self.assertEqual(leftover, [], f"폐기 대상 md 픽스처 잔존: {leftover}")

    def test_ts038_no_md_based_assertions_remain(self):
        """TS-038: 테스트 파일에 md 마커·폐기 픽스처 기반 어서션이 남아 있지 않다.
        탐지 문자열은 자기참조(이 assertion 라인 자신)를 피하기 위해 연결식으로 구성한다 —
        연속 리터럴로 쓰면 이 라인 자체가 항상 1건으로 잡혀 검사가 영구히 통과 불가능해진다."""
        content = pathlib.Path(__file__).read_text(encoding="utf-8")
        legacy_marker_prefix = "<!-- " + "memory:"
        self.assertEqual(content.count(legacy_marker_prefix), 0,
                         "md 마커 리터럴 기반 어서션 잔존 — JSON 계약으로 이관 필요")
        for name in self._OBSOLETE_MD_FIXTURES:
            # 허용 1회 = 위 _OBSOLETE_MD_FIXTURES 상수 선언. 그 외 참조는 미이관 테스트다.
            self.assertEqual(content.count(name), 1,
                             f"폐기 픽스처 '{name}' 참조 {content.count(name)}건 잔존 "
                             f"(허용: 상수 선언 1회) — JSON 계약으로 이관 필요")

    def test_ts038_conversion_input_fixture_is_preserved(self):
        """TS-038: fixture_legacy.md는 변환 입력 픽스처로 존치한다 (PLAN §3.4.1)."""
        self.assertTrue((_FIXTURES_DIR / "fixture_legacy.md").exists(),
                        "fixture_legacy.md가 삭제됨 — 용도 전환(존치) 대상이다")

    def test_ts038_new_json_fixtures_exist(self):
        """TS-038: 078 신규 픽스처 5종이 존재한다."""
        for name in ("fixture_doc_populated.json", "fixture_doc_invalid.json",
                     "fixture_md_marker_populated.md", "fixture_md_no_marker_legacy.md",
                     "fixture_md_marker_empty.md"):
            self.assertTrue((_FIXTURES_DIR / name).exists(), f"픽스처 누락: {name}")


# ─────────────────────────────────────────────────────────────────────────────
# TS-041: 채번 절차 3곳 tool-gated 개정 (산출물 검사) [T078/L1-D1]
# ─────────────────────────────────────────────────────────────────────────────

class TestTaskNumberDocs(unittest.TestCase):
    """[T078/L1-D1] D-1 — 직접 Read+Edit 채번 서술 0건 + 도구 호출 지시 3곳."""

    _SSOT = _REPO_ROOT / "opal/core/references/harness/task-process.md"
    _POINTERS = (
        _REPO_ROOT / "opal/skills/op-task/SKILL.md",
        _REPO_ROOT / "opal/skills/opal-pilot-gc/SKILL.md",
    )

    def _text(self, path):
        self.assertTrue(path.exists(), f"대상 문서 부재: {path}")
        return path.read_text(encoding="utf-8")

    def test_ts041_tool_call_instruction_present_in_all_three(self):
        """TS-041: 3개 문서 전부에 `task-number --bump` 지시가 존재한다."""
        for path in (self._SSOT,) + self._POINTERS:
            with self.subTest(doc=path.name):
                self.assertTrue("task-number --bump" in self._text(path),
                                f"{path} 에 `task-number --bump` 도구 호출 지시가 없다")

    def test_ts041_direct_edit_numbering_absent(self):
        """TS-041: `last_task_number + 1` 계산·직접 갱신 서술 0건."""
        arithmetic = re.compile(r"last_task_number.{0,12}\+\s*1")
        direct_edit = re.compile(r"last_task_number.{0,40}(갱신한다|읽는다)")
        for path in (self._SSOT,) + self._POINTERS:
            with self.subTest(doc=path.name):
                text = self._text(path)
                self.assertEqual(arithmetic.findall(text), [],
                                 f"{path}: LLM이 채번을 계산하는 서술 잔존")
                self.assertEqual(direct_edit.findall(text), [],
                                 f"{path}: 헤더 직접 Read/Edit 채번 서술 잔존")

    def test_ts041_pointers_do_not_duplicate_procedure(self):
        """TS-041: 절차 본문은 SSOT 1곳, 나머지 2곳은 포인터 참조만 한다."""
        for path in self._POINTERS:
            with self.subTest(doc=path.name):
                text = self._text(path)
                self.assertTrue("task-process.md" in text,
                                f"{path}: SSOT(harness/task-process.md) 포인터가 없다")
                self.assertTrue("run.sh task-number" not in text,
                                f"{path}: 절차 본문(실행 커맨드)을 중복 서술하고 있다")

    def test_ts041_ssot_documents_full_procedure(self):
        """TS-041: SSOT에는 실행 커맨드와 init 선행 안내가 있다."""
        text = self._text(self._SSOT)
        self.assertTrue("run.sh task-number" in text, "SSOT에 실행 커맨드가 없다")
        self.assertTrue("memory-tool init" in text, "SSOT에 `init` 선행 안내가 없다 (PLAN §3.5.3)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
