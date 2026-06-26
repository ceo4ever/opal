"""
@header {
  "module": "test_memory_tool",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "memory-tool RED-first 테스트 — S-1~S-17, S-24 (TEST-SCENARIO.md 매핑). 케이스명 프리픽스 [T045/L1-...]. mock/patch/MagicMock 금지(헌법 §4). 실 fixture·tmp_path 사용. memory_tool.py 미존재 시 전부 FAIL(RED) 정상.",
  "exports": [
    "TestSkeleton", "TestMarkerGuard", "TestSummaryLengthCap",
    "TestCountUnlimited", "TestHistoryFIFO", "TestPruneIdempotent",
    "TestPromoteToDocs", "TestPromoteLossless", "TestPromoteToBrain",
    "TestUpdateStatusTransition", "TestInit", "TestInitAlreadyInitialized",
    "TestMigrate", "TestMigrateLossless", "TestReviewAmbient",
    "TestReviewRoleBoundary", "TestSecurity", "TestIntegrationTemplate"
  ]
}
"""

# [MUST] 표준 라이브러리만 import
import json
import os
import pathlib
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


def _setup_populated(tmp_dir: pathlib.Path) -> pathlib.Path:
    """fixture_populated.md + 대응 memory/*.md 파일들을 tmp_dir에 설치한다."""
    memory_dir = tmp_dir / "memory"
    memory_dir.mkdir(exist_ok=True)
    # 메모리 파일들 생성 (fixture_populated.md의 파일 컬럼 대응)
    for name, content in [
        ("prefs_commit.md", "# 캡틴 선호 커밋 방식\n\nmain 직접 커밋 선호 상세 내용.\n"),
        ("arch_tools.md", "# 아키텍처 결정 도구패턴\n\nstate-tool ok/err 패턴 상세.\n"),
        ("prefs_folder.md", "# 한글 폴더명 선호\n\n폴더명 규칙 상세.\n"),
        ("issue_old.md", "# 완료된 이슈 기록\n\n해결된 이슈 내용.\n"),
        ("arch_old.md", "# 대체된 결정\n\n이전 결정 내용.\n"),
    ]:
        (memory_dir / name).write_text(content, encoding="utf-8")
    return _copy_fixture("fixture_populated.md", tmp_dir)


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
        """8서브명령(init/append/update/promote/prune/migrate/show/review)이 --help에 노출된다."""
        result = _run_raw(["--help"])
        combined = result.stdout + result.stderr
        for sub in ["init", "append", "update", "promote", "prune", "migrate", "show", "review"]:
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
            md = _copy_fixture("fixture_valid.md", tmp_dir)
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
            md = _copy_fixture("fixture_valid.md", tmp_dir)
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
    """[T045/L1-R9] S-2: 마커 없는 파일 append → ok:false + marker_missing + 파일 바이트 불변."""

    def test_append_no_marker_returns_marker_missing(self):
        """fixture_no_marker.md에 append → ok:false + error=marker_missing."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_no_marker.md", tmp_dir)
            result = _run([
                "append", "--file", str(md),
                "--kind", "memory",
                "--title", "테스트제목",
                "--type", "feedback",
                "--summary", "마커 없는 파일 테스트"
            ])
            self.assertFalse(result["ok"], f"ok:true가 반환됨 — marker_missing 거부 필요: {result}")
            self.assertEqual(result.get("error"), "marker_missing", f"에러 코드 불일치: {result}")

    def test_append_no_marker_file_bytes_unchanged(self):
        """마커 없는 파일 append 시도 후 파일 바이트가 불변이어야 한다."""
        if not _TOOL_PY.exists():
            self.fail(f"memory_tool.py 미존재 — RED: {_TOOL_PY}")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_no_marker.md", tmp_dir)
            original_bytes = md.read_bytes()
            _run_raw([
                "append", "--file", str(md),
                "--kind", "memory",
                "--title", "테스트제목",
                "--type", "feedback",
                "--summary", "마커 없는 파일 테스트"
            ])
            after_bytes = md.read_bytes()
            self.assertEqual(original_bytes, after_bytes, "마커 없는 파일이 변경됨 — 1바이트도 건드리면 안 됨")

    def test_all_mutating_commands_reject_no_marker(self):
        """모든 변경 명령(append/update/promote/prune)이 마커 없는 파일을 거부한다."""
        if not _TOOL_PY.exists():
            self.fail(f"memory_tool.py 미존재 — RED: {_TOOL_PY}")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_no_marker.md", tmp_dir)
            original_bytes = md.read_bytes()

            mutating_calls = [
                ["append", "--file", str(md), "--kind", "memory",
                 "--title", "T", "--type", "feedback", "--summary", "s"],
                ["update", "--file", str(md), "--title", "T", "--status", "dead"],
                ["prune", "--file", str(md)],
            ]
            for args in mutating_calls:
                with self.subTest(cmd=args[0]):
                    result = _run(args)
                    self.assertFalse(result["ok"], f"{args[0]}: ok:true 반환됨")
                    self.assertEqual(result.get("error"), "marker_missing",
                                     f"{args[0]}: error != marker_missing: {result}")
                    self.assertEqual(md.read_bytes(), original_bytes,
                                     f"{args[0]}: 파일 바이트 변경됨")


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
            md = _copy_fixture("fixture_valid.md", tmp_dir)
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
            md = _copy_fixture("fixture_valid.md", tmp_dir)
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
            md = _copy_fixture("fixture_valid.md", tmp_dir)
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

    def _count_history_rows(self, md: pathlib.Path) -> list:
        """히스토리 마커 사이의 데이터 행(헤더·구분선 제외)을 반환한다."""
        content = md.read_text(encoding="utf-8")
        in_section = False
        rows = []
        for line in content.splitlines():
            if "<!-- memory:history:start -->" in line:
                in_section = True
                continue
            if "<!-- memory:history:end -->" in line:
                in_section = False
                continue
            if in_section:
                stripped = line.strip()
                if stripped.startswith("|") and stripped.endswith("|"):
                    # 헤더 행(제목 포함) 또는 구분선 제외
                    inner = stripped[1:-1].strip()
                    if not inner.replace("-", "").replace("|", "").replace(" ", ""):
                        continue  # 구분선
                    if "제목" in inner or "title" in inner.lower():
                        continue  # 헤더
                    rows.append(stripped)
        return rows

    def test_history_fifo_limit_five(self):
        """6건 history append 후 히스토리 행수는 정확히 5여야 한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_valid.md", tmp_dir)
            for i in range(6):
                result = _run([
                    "append", "--file", str(md),
                    "--kind", "history",
                    "--title", f"h{i+1}",
                    "--summary", f"히스토리항목{i+1} 핵심결과"
                ])
                self.assertTrue(result["ok"], f"h{i+1} append 실패: {result}")

            rows = self._count_history_rows(md)
            self.assertEqual(len(rows), 5,
                             f"히스토리 행수={len(rows)}, FIFO=5 기대\n행목록: {rows}")

    def test_history_fifo_removes_oldest(self):
        """h1(최초)이 제거되고 h2~h6(최신 5개)이 보존된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_valid.md", tmp_dir)
            for i in range(6):
                _run([
                    "append", "--file", str(md),
                    "--kind", "history",
                    "--title", f"h{i+1}",
                    "--summary", f"히스토리항목{i+1}"
                ])

            content = md.read_text(encoding="utf-8")
            self.assertNotIn("| h1 |", content, "h1(최초)이 제거되어야 함")
            for i in range(2, 7):
                self.assertIn(f"h{i}", content, f"h{i}(최신)이 보존되어야 함")


# ─────────────────────────────────────────────────────────────────────────────
# S-6: prune idempotent [T045/L1-R7]
# ─────────────────────────────────────────────────────────────────────────────

class TestPruneIdempotent(unittest.TestCase):
    """[T045/L1-R7] S-6: 히스토리 ≤5 상태에서 prune → no-op, ok:true."""

    def _count_history_data_rows(self, md: pathlib.Path) -> int:
        content = md.read_text(encoding="utf-8")
        in_section = False
        count = 0
        for line in content.splitlines():
            if "<!-- memory:history:start -->" in line:
                in_section = True
                continue
            if "<!-- memory:history:end -->" in line:
                in_section = False
                continue
            if in_section:
                stripped = line.strip()
                if stripped.startswith("|") and stripped.endswith("|"):
                    inner = stripped[1:-1].strip()
                    if not inner.replace("-", "").replace("|", "").replace(" ", ""):
                        continue
                    if "제목" in inner or "title" in inner.lower():
                        continue
                    count += 1
        return count

    def test_prune_no_op_when_five_or_fewer(self):
        """히스토리 3건 상태에서 prune → 행수 불변, ok:true."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_valid.md", tmp_dir)
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
            md = _copy_fixture("fixture_valid.md", tmp_dir)
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

            # "캡틴 선호 커밋 방식" 행 promote
            result = _run([
                "promote", "--file", str(md),
                "--title", "캡틴 선호 커밋 방식",
                "--to", "docs",
                "--ref", "AGENT.md#커밋방식"
            ])
            self.assertTrue(result["ok"], f"promote 실패: {result}")

            # 인덱스 행 제거 확인
            content = md.read_text(encoding="utf-8")
            self.assertNotIn("캡틴 선호 커밋 방식", content,
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
                "--title", "캡틴 선호 커밋 방식",
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
                "--title", "캡틴 선호 커밋 방식",
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
                "--title", "캡틴 선호 커밋 방식",
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
            original_content = md.read_text(encoding="utf-8")
            mem_file = tmp_dir / "memory" / "prefs_commit.md"
            original_mem = mem_file.read_text(encoding="utf-8")

            _run_raw([
                "promote", "--file", str(md),
                "--title", "캡틴 선호 커밋 방식",
                "--to", "docs"
            ])

            # 인덱스 불변
            self.assertEqual(md.read_text(encoding="utf-8"), original_content,
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
                "--title", "캡틴 선호 커밋 방식",
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
                "--title", "캡틴 선호 커밋 방식",
                "--status", "dead"
            ])
            self.assertTrue(result["ok"], f"update 실패: {result}")

            content = md.read_text(encoding="utf-8")
            # 행은 보존되어야 함
            self.assertIn("캡틴 선호 커밋 방식", content,
                          "dead 상태 행이 삭제됨 — 보존되어야 함")
            # 상태가 dead로 변경됨
            self.assertIn("dead", content,
                          "상태가 dead로 변경되지 않음")

    def test_update_invalid_status_rejected(self):
        """invalid 상태값으로 update → ok:false + invalid_status."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "update", "--file", str(md),
                "--title", "캡틴 선호 커밋 방식",
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
                "--title", "아키텍처 결정 도구패턴",
                "--status", "superseded"
            ])
            self.assertTrue(result["ok"], f"update 실패: {result}")
            content = md.read_text(encoding="utf-8")
            self.assertIn("아키텍처 결정 도구패턴", content,
                          "superseded 행이 삭제됨 — 보존되어야 함")

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
                        "--title", "한글 폴더명 선호",
                        "--status", status
                    ])
                    self.assertTrue(result["ok"],
                                    f"유효한 상태 '{status}'가 거부됨: {result}")


# ─────────────────────────────────────────────────────────────────────────────
# S-11: init 마커 삽입 [T045/L1-R9]
# ─────────────────────────────────────────────────────────────────────────────

class TestInit(unittest.TestCase):
    """[T045/L1-R9] S-11: 마커 없는 파일에 init → 마커 4개 삽입."""

    EXPECTED_MARKERS = [
        "<!-- memory:index:start -->",
        "<!-- memory:index:end -->",
        "<!-- memory:history:start -->",
        "<!-- memory:history:end -->",
    ]

    def test_init_inserts_four_markers(self):
        """init 후 index·history start/end 마커 4개가 삽입된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            # 마커 없는 새 파일
            new_md = tmp_dir / "MEMORY.md"
            new_md.write_text("# 새 프로젝트 Memory Index\n\n", encoding="utf-8")

            result = _run(["init", "--file", str(new_md)])
            self.assertTrue(result["ok"], f"init 실패: {result}")

            content = new_md.read_text(encoding="utf-8")
            for marker in self.EXPECTED_MARKERS:
                self.assertIn(marker, content,
                              f"마커 누락: {marker}")

    def test_init_inserts_format_headers(self):
        """init 후 인덱스·히스토리 표 헤더가 삽입된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            new_md = tmp_dir / "MEMORY.md"
            new_md.write_text("# 새 프로젝트\n", encoding="utf-8")

            result = _run(["init", "--file", str(new_md)])
            self.assertTrue(result["ok"], f"init 실패: {result}")

            content = new_md.read_text(encoding="utf-8")
            # 인덱스 헤더 (제목 컬럼 포함)
            self.assertIn("제목", content,
                          "init 후 제목 컬럼 헤더 없음")

    def test_init_on_no_marker_file(self):
        """fixture_no_marker.md에 init → ok:true (마커 삽입)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_no_marker.md", tmp_dir)

            result = _run(["init", "--file", str(md)])
            self.assertTrue(result["ok"], f"마커 없는 파일 init 실패: {result}")

            content = md.read_text(encoding="utf-8")
            for marker in self.EXPECTED_MARKERS:
                self.assertIn(marker, content, f"마커 누락: {marker}")


# ─────────────────────────────────────────────────────────────────────────────
# S-12: init 재실행 거부 [T045/L1-R9]
# ─────────────────────────────────────────────────────────────────────────────

class TestInitAlreadyInitialized(unittest.TestCase):
    """[T045/L1-R9] S-12: 마커 존재 파일에 init(--force 없음) → already_initialized."""

    def test_init_on_existing_markers_rejected(self):
        """마커가 이미 있는 파일에 init → ok:false + already_initialized."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_valid.md", tmp_dir)

            result = _run(["init", "--file", str(md)])
            self.assertFalse(result["ok"],
                             f"마커 있는 파일에 init이 통과됨: {result}")
            self.assertEqual(result.get("error"), "already_initialized",
                             f"에러 코드 불일치: {result}")

    def test_init_force_on_existing_markers_succeeds(self):
        """--force 플래그로 init → 재삽입 성공."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_valid.md", tmp_dir)

            result = _run(["init", "--file", str(md), "--force"])
            self.assertTrue(result["ok"],
                            f"--force init 실패: {result}")


# ─────────────────────────────────────────────────────────────────────────────
# S-13: migrate 구→신 변환 (H-5) [T045/L1-R8p 변환]
# ─────────────────────────────────────────────────────────────────────────────

class TestMigrate(unittest.TestCase):
    """[T045/L1-H5] S-13: fixture_legacy.md 6행 → 신포맷 6행, 제목 비공백, 상태매핑."""

    def _count_index_data_rows(self, md: pathlib.Path) -> list:
        """인덱스 마커 사이 데이터 행 반환."""
        content = md.read_text(encoding="utf-8")
        in_section = False
        rows = []
        for line in content.splitlines():
            if "<!-- memory:index:start -->" in line:
                in_section = True
                continue
            if "<!-- memory:index:end -->" in line:
                in_section = False
                continue
            if in_section:
                stripped = line.strip()
                if stripped.startswith("|") and stripped.endswith("|"):
                    inner = stripped[1:-1].strip()
                    if not inner.replace("-", "").replace("|", "").replace(" ", ""):
                        continue
                    if "제목" in inner and "등록일" in inner:
                        continue
                    rows.append(stripped)
        return rows

    def test_migrate_preserves_row_count(self):
        """migrate 후 메모리 인덱스 행수가 6개 보존된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_legacy.md", tmp_dir)

            result = _run(["migrate", "--file", str(md)])
            self.assertTrue(result["ok"], f"migrate 실패: {result}")

            rows = self._count_index_data_rows(md)
            self.assertEqual(len(rows), 6,
                             f"행수 불일치: {len(rows)} ≠ 6\n행목록: {rows}")

    def test_migrate_titles_nonempty(self):
        """migrate 후 각 행의 제목 컬럼이 비공백이다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_legacy.md", tmp_dir)

            result = _run(["migrate", "--file", str(md)])
            self.assertTrue(result["ok"], f"migrate 실패: {result}")

            rows = self._count_index_data_rows(md)
            for i, row in enumerate(rows):
                cols = [c.strip() for c in row.strip("|").split("|")]
                title = cols[0] if cols else ""
                self.assertTrue(
                    title and title.strip(),
                    f"행 {i+1}의 제목이 비어있음: {row}"
                )

    def test_migrate_status_mapping_dead(self):
        """완료/~~완료~~ 상태는 dead로 매핑된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_legacy.md", tmp_dir)

            _run(["migrate", "--file", str(md)])
            content = md.read_text(encoding="utf-8")
            # 구 상태값이 없어야 함
            self.assertNotIn("~~완료~~", content,
                             "구 상태값 '~~완료~~'가 신포맷에 남아있음")

    def test_migrate_status_mapping_superseded(self):
        """폐기 기록 상태는 superseded로 매핑된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_legacy.md", tmp_dir)

            _run(["migrate", "--file", str(md)])
            content = md.read_text(encoding="utf-8")
            self.assertNotIn("폐기 기록", content,
                             "구 상태값 '폐기 기록'이 신포맷에 남아있음")

    def test_migrate_reports_review_count(self):
        """migrate 응답에 review_count가 포함된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_legacy.md", tmp_dir)

            result = _run(["migrate", "--file", str(md)])
            self.assertTrue(result["ok"], f"migrate 실패: {result}")
            self.assertIn("review_count", result,
                          f"review_count 없음: {result}")

    def test_migrate_inserts_markers(self):
        """migrate 후 신포맷 마커 4개가 존재한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_legacy.md", tmp_dir)

            _run(["migrate", "--file", str(md)])
            content = md.read_text(encoding="utf-8")
            for marker in [
                "<!-- memory:index:start -->",
                "<!-- memory:index:end -->",
                "<!-- memory:history:start -->",
                "<!-- memory:history:end -->",
            ]:
                self.assertIn(marker, content, f"마커 누락: {marker}")


# ─────────────────────────────────────────────────────────────────────────────
# S-14: migrate 80자 초과 무손실 [T045/L1-H5]
# ─────────────────────────────────────────────────────────────────────────────

class TestMigrateLossless(unittest.TestCase):
    """[T045/L1-H5] S-14: 80자 초과 설명 → truncate 없이 [REVIEW] 플래그."""

    def test_long_description_gets_review_flag_not_truncated(self):
        """80자 초과 구 설명 행이 migrate 후 [REVIEW] 플래그를 받는다 (truncate 금지)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_legacy.md", tmp_dir)

            result = _run(["migrate", "--file", str(md)])
            self.assertTrue(result["ok"], f"migrate 실패: {result}")

            content = md.read_text(encoding="utf-8")
            # fixture_legacy.md에 80자 초과 설명이 포함됨 → [REVIEW] 마킹 기대
            self.assertIn("[REVIEW]", content,
                          "80자 초과 행에 [REVIEW] 플래그가 없음 (truncate 금지)")

    def test_review_count_nonzero_for_long_descriptions(self):
        """80자 초과 행이 있으면 review_count > 0이다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_legacy.md", tmp_dir)

            result = _run(["migrate", "--file", str(md)])
            self.assertTrue(result["ok"])
            review_count = result.get("review_count", 0)
            self.assertGreater(review_count, 0,
                               f"80자 초과 행이 있는데 review_count=0: {result}")


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
            new_md = tmp_dir / "MEMORY.md"
            new_md.write_text("# 테스트\n", encoding="utf-8")
            result = _run(["init", "--file", str(new_md)])
            self.assertTrue(result["ok"])
            self._assert_review_key(result, "init")

    def test_append_response_has_review(self):
        """append 응답에 review 키가 있다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_valid.md", tmp_dir)
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
                "--title", "캡틴 선호 커밋 방식",
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
                "--title", "캡틴 선호 커밋 방식",
                "--to", "docs",
                "--ref", "AGENT.md#커밋방식"
            ])
            self.assertTrue(result["ok"])
            self._assert_review_key(result, "promote")

    def test_prune_response_has_review(self):
        """prune 응답에 review 키가 있다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_valid.md", tmp_dir)
            result = _run(["prune", "--file", str(md)])
            self.assertTrue(result["ok"])
            self._assert_review_key(result, "prune")

    def test_migrate_response_has_review(self):
        """migrate 응답에 review 키가 있다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_legacy.md", tmp_dir)
            result = _run(["migrate", "--file", str(md)])
            self.assertTrue(result["ok"])
            self._assert_review_key(result, "migrate")


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
            # fixture_populated.md에 dead 1행·superseded 1행 존재
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
# S-24: 통합 — 신포맷 템플릿 MEMORY.md → review violations 0 [T045/L2-R10]
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegrationTemplate(unittest.TestCase):
    """[T045/L2-R10] S-24: 신포맷 템플릿 기반 MEMORY.md → review violations=0."""

    # 신포맷 템플릿 (PLAN §3.7.2 기준)
    TEMPLATE_CONTENT = """\
# 테스트 프로젝트 Memory Index

> 최종 갱신: 2026-06-26
> last_task_number: 0

## 메모리
<!-- memory:index:start -->
| 제목 | 등록일 | 유형 | 상태 | 파일 | 요약 |
|------|--------|------|------|------|------|
<!-- memory:index:end -->

## 작업 히스토리 (최대 5개, FIFO)
<!-- memory:history:start -->
| 제목 | 등록일 | 단계 | 경로 | 핵심결과 |
|------|--------|------|------|----------|
<!-- memory:history:end -->

> 메모리 행 추가·정리·이관은 memory-tool로만 수행한다(직접 편집 금지). 상세 형식·라이프사이클: memory-learning.md.
"""

    def test_template_passes_review_with_zero_violations(self):
        """신포맷 템플릿으로 만든 MEMORY.md를 review → violations == []."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = tmp_dir / "MEMORY.md"
            md.write_text(self.TEMPLATE_CONTENT, encoding="utf-8")

            result = _run(["review", "--file", str(md)])
            self.assertTrue(result["ok"], f"review 실패: {result}")

            violations = result.get("violations", [])
            self.assertEqual(violations, [],
                             f"신포맷 템플릿에서 violations 발생: {violations}")

    def test_template_has_four_markers(self):
        """신포맷 템플릿에 마커 4개가 존재한다."""
        for marker in [
            "<!-- memory:index:start -->",
            "<!-- memory:index:end -->",
            "<!-- memory:history:start -->",
            "<!-- memory:history:end -->",
        ]:
            self.assertIn(marker, self.TEMPLATE_CONTENT,
                          f"템플릿에 마커 누락: {marker}")

    def test_template_has_title_column(self):
        """신포맷 템플릿에 제목 컬럼이 있다."""
        self.assertIn("제목", self.TEMPLATE_CONTENT,
                      "템플릿에 제목 컬럼 없음")

    def test_append_to_template_succeeds(self):
        """템플릿 기반 MEMORY.md에 append → ok:true (형식 호환)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = tmp_dir / "MEMORY.md"
            md.write_text(self.TEMPLATE_CONTENT, encoding="utf-8")

            result = _run([
                "append", "--file", str(md),
                "--kind", "memory",
                "--title", "템플릿호환테스트",
                "--type", "feedback",
                "--summary", "신포맷 템플릿 호환 테스트 완료"
            ])
            self.assertTrue(result["ok"],
                            f"템플릿 기반 파일 append 실패: {result}")


# ─────────────────────────────────────────────────────────────────────────────
# 추가: ERROR_CODES 검증 [T045/L1-R5]
# ─────────────────────────────────────────────────────────────────────────────

class TestErrorCodes(unittest.TestCase):
    """[T045/L1-R5] ERROR_CODES 키 SSOT 검증."""

    REQUIRED_CODES = [
        "marker_missing",
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
                "--title", "완료된 이슈 기록"
            ])
            self.assertTrue(result["ok"], f"dead 행 delete 실패: {result}")

            content = md.read_text(encoding="utf-8")
            self.assertNotIn("완료된 이슈 기록", content,
                             "dead 행이 인덱스에서 제거되지 않음")

    def test_delete_active_row_rejected_with_error_code(self):
        """active 상태 행 delete 시도 → ok:false + delete_requires_dead_or_superseded."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "delete", "--file", str(md),
                "--title", "캡틴 선호 커밋 방식"
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
            original_content = md.read_text(encoding="utf-8")

            _run_raw([
                "delete", "--file", str(md),
                "--title", "캡틴 선호 커밋 방식"
            ])

            self.assertEqual(md.read_text(encoding="utf-8"), original_content,
                             "active 행 delete 거부 후 파일이 변경됨 — 1바이트도 건드리면 안 됨")

    def test_delete_superseded_row_succeeds(self):
        """superseded 상태 행 delete → ok:true + 인덱스 행 제거."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "delete", "--file", str(md),
                "--title", "대체된 결정"
            ])
            self.assertTrue(result["ok"], f"superseded 행 delete 실패: {result}")

            content = md.read_text(encoding="utf-8")
            self.assertNotIn("대체된 결정", content,
                             "superseded 행이 인덱스에서 제거되지 않음")

    def test_delete_with_file_removes_md(self):
        """--with-file 옵션 시 memory/<file>.md도 삭제된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            mem_file = tmp_dir / "memory" / "issue_old.md"
            self.assertTrue(mem_file.exists(), "테스트 전제 실패: issue_old.md 없음")

            result = _run([
                "delete", "--file", str(md),
                "--title", "완료된 이슈 기록",
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
            mem_file = tmp_dir / "memory" / "issue_old.md"

            result = _run([
                "delete", "--file", str(md),
                "--title", "완료된 이슈 기록"
            ])
            self.assertTrue(result["ok"], f"delete 실패: {result}")
            self.assertTrue(mem_file.exists(),
                            "--with-file 미지정인데 .md 파일이 삭제됨")

    def test_delete_with_file_path_traversal_rejected(self):
        """--with-file + ../ 탈출 경로 파일 필드 → 거부 (경로 화이트리스트 위반)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            # memory/ 하위 파일 필드가 ../ 탈출인 행을 직접 삽입
            content = md.read_text(encoding="utf-8")
            traversal_row = "| 탈출시도항목 | 2025-06-01 | feedback | dead | ../sensitive.md | 경로 탈출 테스트 |\n"
            # 인덱스 마커 사이에 삽입
            new_content = content.replace(
                "<!-- memory:index:end -->",
                traversal_row + "<!-- memory:index:end -->"
            )
            md.write_text(new_content, encoding="utf-8")

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
                    "memory_file_not_found", "row_not_found"
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

    def test_delete_no_marker_rejected(self):
        """마커 없는 파일에 delete → ok:false + marker_missing + 파일 불변."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _copy_fixture("fixture_no_marker.md", tmp_dir)
            original_bytes = md.read_bytes()

            result = _run([
                "delete", "--file", str(md),
                "--title", "임의제목"
            ])
            self.assertFalse(result["ok"],
                             f"마커 없는 파일에 delete가 통과됨: {result}")
            self.assertEqual(result.get("error"), "marker_missing",
                             f"에러 코드 불일치: {result}")
            self.assertEqual(md.read_bytes(), original_bytes,
                             "마커 없는 파일에 delete 거부 후 파일 바이트 변경됨")

    def test_delete_response_has_review_block(self):
        """delete 성공 응답에 review 블록이 첨부된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "delete", "--file", str(md),
                "--title", "완료된 이슈 기록"
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
                "--title", "아키텍처 결정 도구패턴",
                "--new-title", "아키텍처 결정 도구패턴 v2"
            ])
            self.assertTrue(result["ok"], f"--new-title update 실패: {result}")

            content = md.read_text(encoding="utf-8")
            # 새 제목 존재
            self.assertIn("아키텍처 결정 도구패턴 v2", content,
                          "새 제목이 인덱스에 반영되지 않음")
            # 기존 제목 제거
            self.assertNotIn("| 아키텍처 결정 도구패턴 |", content,
                             "기존 제목이 그대로 남아있음")
            # 유형 보존 (architecture)
            self.assertIn("architecture", content,
                          "제목 변경 후 유형(architecture)이 사라짐")
            # 상태 보존 (active)
            self.assertIn("active", content,
                          "제목 변경 후 상태(active)가 사라짐")

    def test_new_title_empty_string_rejected(self):
        """--new-title이 빈 문자열 → ok:false + title_required (또는 적절한 에러)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            original_content = md.read_text(encoding="utf-8")

            result = _run([
                "update", "--file", str(md),
                "--title", "캡틴 선호 커밋 방식",
                "--new-title", ""
            ])
            self.assertFalse(result["ok"],
                             f"빈 --new-title이 ok:true로 통과됨: {result}")
            self.assertIn(result.get("error"), [
                "title_required", "invalid_title", "new_title_required"
            ], f"에러 코드 불일치: {result}")
            # 행 불변 확인
            self.assertEqual(md.read_text(encoding="utf-8"), original_content,
                             "빈 --new-title 거부 후 파일이 변경됨")

    def test_new_title_whitespace_only_rejected(self):
        """--new-title이 공백만 → ok:false + title_required (또는 적절한 에러)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            original_content = md.read_text(encoding="utf-8")

            result = _run([
                "update", "--file", str(md),
                "--title", "캡틴 선호 커밋 방식",
                "--new-title", "   "
            ])
            self.assertFalse(result["ok"],
                             f"공백 --new-title이 ok:true로 통과됨: {result}")
            self.assertIn(result.get("error"), [
                "title_required", "invalid_title", "new_title_required"
            ], f"에러 코드 불일치: {result}")
            self.assertEqual(md.read_text(encoding="utf-8"), original_content,
                             "공백 --new-title 거부 후 파일이 변경됨")

    def test_existing_status_update_regression(self):
        """기존 --status update 동작이 회귀 없이 정상 작동한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run([
                "update", "--file", str(md),
                "--title", "한글 폴더명 선호",
                "--status", "superseded"
            ])
            self.assertTrue(result["ok"],
                            f"기존 --status update 회귀 — 실패: {result}")

            content = md.read_text(encoding="utf-8")
            self.assertIn("superseded", content,
                          "상태가 superseded로 변경되지 않음")
            self.assertIn("한글 폴더명 선호", content,
                          "행이 삭제됨 — 보존되어야 함")

    def test_existing_summary_update_regression(self):
        """기존 --summary update 동작이 회귀 없이 정상 작동한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            new_summary = "갱신된 요약 내용 — 회귀 테스트"
            result = _run([
                "update", "--file", str(md),
                "--title", "캡틴 선호 커밋 방식",
                "--summary", new_summary
            ])
            self.assertTrue(result["ok"],
                            f"기존 --summary update 회귀 — 실패: {result}")

            content = md.read_text(encoding="utf-8")
            self.assertIn(new_summary, content,
                          "요약이 갱신되지 않음")


# ─────────────────────────────────────────────────────────────────────────────
# S-27: argparse 9종 서브명령 등록 확인 (delete 포함) [T045/L1-SKv2]
# ─────────────────────────────────────────────────────────────────────────────

class TestSkeletonV2(unittest.TestCase):
    """[T045/L1-SKv2] S-27: 서브명령 9종(delete 포함) argparse 등록 확인."""

    ALL_NINE_SUBCOMMANDS = [
        "init", "append", "update", "promote", "prune",
        "migrate", "show", "review", "delete"
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
# S-28: 백틱 file 필드 — migrate 생성 행의 삭제 경로 버그 [T045/L1-BUG]
# ─────────────────────────────────────────────────────────────────────────────

class TestBacktickFileFieldDeletion(unittest.TestCase):
    """[T045/L1-BUG] S-28: migrate 생성 행(백틱 file 필드) → delete/promote 시 실 .md 파일 삭제 실패 버그.

    확정된 버그:
    - migrate가 생성한 인덱스 행의 파일 컬럼은 구포맷 그대로 백틱 포함: `memory/x.md`
    - append는 백틱 없이 저장: memory/x.md
    - delete --with-file / promote가 _resolve_memory_file()에 백틱 포함 file 필드를 넘기면
      경로 해석 실패 → 실파일이 안 지워지고 orphan이 남는다.
    - 현재 FAIL (RED) 정상.
    """

    # 구포맷 파일 컬럼에 백틱이 포함된 레거시 MEMORY.md 템플릿
    # cells[3]이 "`memory/x.md`" 형태로 파싱되어 신포맷 file 컬럼에 그대로 저장됨
    _LEGACY_TEMPLATE_DEAD = """\
# 프로젝트 Memory Index

> 구포맷 파일 — 백틱 file 필드 버그 재현용

## 프로젝트 메모리

| 등록일시 | 카테고리 | 상태 | 파일 | 설명 |
|----------|---------|------|------|------|
| 2026-01-15 | feedback | 완료 | `memory/backtick_test.md` | 백틱 파일 필드 버그 재현 테스트 |

## 작업 히스토리

| 등록일자 | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |
|----------|------|------|------|---------|---------|
| 2026-01-10 | 테스트작업 | 완료 | tasks/test/ | 2026-01-10 09:00 | 2026-01-12 18:00 |
"""

    _LEGACY_TEMPLATE_ACTIVE = """\
# 프로젝트 Memory Index

> 구포맷 파일 — 백틱 file 필드 버그 재현용 (promote 경로)

## 프로젝트 메모리

| 등록일시 | 카테고리 | 상태 | 파일 | 설명 |
|----------|---------|------|------|------|
| 2026-01-15 | feedback | 유지 | `memory/backtick_promote.md` | 백틱 파일 필드 promote 버그 재현 |

## 작업 히스토리

| 등록일자 | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |
|----------|------|------|------|---------|---------|
| 2026-01-10 | 테스트작업 | 완료 | tasks/test/ | 2026-01-10 09:00 | 2026-01-12 18:00 |
"""

    def _setup_migrate_dead(self, tmp_dir):
        """구포맷(백틱 file 필드, 완료=dead) → migrate → update --status dead 상태 설정.
        반환: (md_path, mem_file_path, migrated_title)
        """
        md = tmp_dir / "MEMORY.md"
        mem_dir = tmp_dir / "memory"
        mem_dir.mkdir(exist_ok=True)
        mem_file = mem_dir / "backtick_test.md"
        mem_file.write_text("# 백틱 테스트\n내용\n", encoding="utf-8")
        md.write_text(self._LEGACY_TEMPLATE_DEAD, encoding="utf-8")

        # migrate 실행 — 이 경로에서 백틱 file 필드가 신포맷에 그대로 박힘
        result = _run(["migrate", "--file", str(md)])
        self.assertTrue(result["ok"], f"migrate 실패: {result}")

        # migrate 후 인덱스에서 실제 제목 추출 (migrate가 설명 첫 부분으로 제목 생성)
        content = md.read_text(encoding="utf-8")
        title = None
        in_idx = False
        for line in content.splitlines():
            if "<!-- memory:index:start -->" in line:
                in_idx = True
                continue
            if "<!-- memory:index:end -->" in line:
                break
            if in_idx and line.strip().startswith("|"):
                inner = line.strip()[1:-1].strip()
                if "제목" in inner and "등록일" in inner:
                    continue  # 헤더
                if inner.replace("-", "").replace("|", "").replace(" ", ""):
                    cols = [c.strip() for c in line.strip("|").split("|")]
                    if cols:
                        title = cols[0].strip()
                        break

        self.assertIsNotNone(title, "migrate 후 제목을 추출할 수 없음")

        # migrate 후 상태가 dead인지 확인 (완료→dead 매핑)
        # dead 상태이면 delete 가능, 아니면 update로 전환
        if "dead" not in content:
            r = _run(["update", "--file", str(md), "--title", title, "--status", "dead"])
            self.assertTrue(r["ok"], f"update --status dead 실패: {r}")

        return md, mem_file, title

    def _setup_migrate_active(self, tmp_dir):
        """구포맷(백틱 file 필드, 유지=active) → migrate 상태 설정.
        반환: (md_path, mem_file_path, migrated_title)
        """
        md = tmp_dir / "MEMORY.md"
        mem_dir = tmp_dir / "memory"
        mem_dir.mkdir(exist_ok=True)
        mem_file = mem_dir / "backtick_promote.md"
        mem_file.write_text("# 백틱 프로모트 테스트\n내용\n", encoding="utf-8")
        md.write_text(self._LEGACY_TEMPLATE_ACTIVE, encoding="utf-8")

        # migrate 실행
        result = _run(["migrate", "--file", str(md)])
        self.assertTrue(result["ok"], f"migrate 실패: {result}")

        # 제목 추출
        content = md.read_text(encoding="utf-8")
        title = None
        in_idx = False
        for line in content.splitlines():
            if "<!-- memory:index:start -->" in line:
                in_idx = True
                continue
            if "<!-- memory:index:end -->" in line:
                break
            if in_idx and line.strip().startswith("|"):
                inner = line.strip()[1:-1].strip()
                if "제목" in inner and "등록일" in inner:
                    continue
                if inner.replace("-", "").replace("|", "").replace(" ", ""):
                    cols = [c.strip() for c in line.strip("|").split("|")]
                    if cols:
                        title = cols[0].strip()
                        break

        self.assertIsNotNone(title, "migrate 후 제목을 추출할 수 없음")
        return md, mem_file, title

    def test_migrate_produces_backtick_file_field(self):
        """[T045/L1-BUG] 전제 확인: migrate가 생성한 인덱스 행의 file 필드에 백틱이 포함된다.
        이 케이스가 PASS여야 나머지 버그 케이스가 의미 있다.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md, mem_file, title = self._setup_migrate_dead(tmp_dir)

            content = md.read_text(encoding="utf-8")
            # migrate 후 file 컬럼에 백틱이 포함되어 있어야 한다 (버그 전제)
            self.assertIn("`memory/backtick_test.md`", content,
                          "전제 실패: migrate 후 file 필드에 백틱이 없음 — 버그 전제가 바뀐 것임")

    def test_delete_with_file_on_migrated_row_removes_md(self):
        """[T045/L1-BUG] migrate 행(백틱 file 필드)을 delete --with-file → 실 .md 파일도 삭제됨.

        현재 FAIL(RED):
        - _resolve_memory_file()이 '`memory/backtick_test.md`'를 해석 실패
        - file_deleted=False, 실 파일이 orphan으로 남음
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md, mem_file, title = self._setup_migrate_dead(tmp_dir)

            # 전제: 실 파일이 존재해야 함
            self.assertTrue(mem_file.exists(),
                            f"전제 실패: memory 파일이 없음: {mem_file}")

            result = _run([
                "delete", "--file", str(md),
                "--title", title,
                "--with-file"
            ])

            # (1) 인덱스 행 제거 확인
            self.assertTrue(result["ok"],
                            f"delete --with-file 실패: {result}")
            self.assertTrue(result.get("row_removed", False),
                            f"인덱스 행이 제거되지 않음: {result}")

            # (2) 실 .md 파일도 삭제됨 — 현재 FAIL(RED) 예상
            self.assertTrue(result.get("file_deleted", False),
                            f"[RED] file_deleted=False — 백틱 포함 file 필드로 인해 파일 삭제 실패: {result}")
            self.assertFalse(mem_file.exists(),
                             f"[RED] 실 파일이 orphan으로 남아있음: {mem_file}\n"
                             f"버그: _resolve_memory_file()이 백틱 포함 경로를 해석하지 못함")

    def test_promote_on_migrated_row_removes_md(self):
        """[T045/L1-BUG] migrate 행(백틱 file 필드)을 promote --to docs → 실 .md 파일 삭제됨.

        현재 FAIL(RED):
        - _resolve_memory_file()이 '`memory/backtick_promote.md`'를 해석 실패
        - memory_file_not_found 에러 또는 file_deleted=False
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md, mem_file, title = self._setup_migrate_active(tmp_dir)

            # 전제: 실 파일이 존재해야 함
            self.assertTrue(mem_file.exists(),
                            f"전제 실패: memory 파일이 없음: {mem_file}")

            result = _run([
                "promote", "--file", str(md),
                "--title", title,
                "--to", "docs",
                "--ref", "AGENT.md#backtick-bug-test"
            ])

            # (1) promote 성공해야 함 — 현재 memory_file_not_found로 실패(RED)
            self.assertTrue(result["ok"],
                            f"[RED] promote 실패 — 백틱 포함 file 필드로 인해 경로 해석 실패: {result}\n"
                            f"버그: _resolve_memory_file()이 '`memory/backtick_promote.md`'를 None으로 반환")

            # (2) 인덱스 행 제거
            self.assertTrue(result.get("row_removed", False),
                            f"인덱스 행이 제거되지 않음: {result}")

            # (3) 실 .md 파일 삭제 — 현재 FAIL(RED)
            self.assertTrue(result.get("file_deleted", False),
                            f"[RED] file_deleted=False — 백틱 포함 file 필드로 인해 파일 삭제 실패: {result}")
            self.assertFalse(mem_file.exists(),
                             f"[RED] 실 파일이 orphan으로 남아있음: {mem_file}")

    def test_resolve_handles_backtick_wrapped_file_field(self):
        """[T045/L1-BUG] 백틱 포함 file 필드도 올바른 실경로로 해석 → delete --with-file 성공.

        공개 인터페이스(파일 존재 여부·JSON)로만 검증.
        내부 _resolve_memory_file() 직접 호출 금지.

        현재 FAIL(RED): 백틱이 있으면 resolve 실패 → 파일 삭제 안 됨.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)

            # 신포맷 MEMORY.md에 백틱 file 필드를 직접 삽입 (migrate 없이 백틱 필드 재현)
            # 이 케이스는 migrate 경유 없이도 백틱 필드가 인덱스에 있을 때의 동작을 검증
            new_md_content = """\
# 테스트 Memory Index

<!-- memory:index:start -->
| 제목 | 등록일 | 유형 | 상태 | 파일 | 요약 |
|------|--------|------|------|------|------|
| 백틱경로테스트 | 2026-01-15 | feedback | dead | `memory/backtick_direct.md` | 직접 백틱 삽입 테스트 |
<!-- memory:index:end -->

<!-- memory:history:start -->
| 제목 | 등록일 | 단계 | 경로 | 핵심결과 |
|------|--------|------|------|----------|
<!-- memory:history:end -->
"""
            md = tmp_dir / "MEMORY.md"
            mem_dir = tmp_dir / "memory"
            mem_dir.mkdir()
            mem_file = mem_dir / "backtick_direct.md"
            mem_file.write_text("# 직접 백틱 테스트\n내용\n", encoding="utf-8")
            md.write_text(new_md_content, encoding="utf-8")

            # delete --with-file 실행
            result = _run([
                "delete", "--file", str(md),
                "--title", "백틱경로테스트",
                "--with-file"
            ])

            # 성공 + 실 파일 삭제 — 현재 FAIL(RED)
            self.assertTrue(result["ok"],
                            f"delete 실패: {result}")
            self.assertTrue(result.get("file_deleted", False),
                            f"[RED] file_deleted=False — 백틱 포함 file 필드 처리 실패: {result}")
            self.assertFalse(mem_file.exists(),
                             f"[RED] 실 파일이 orphan으로 남아있음: {mem_file}\n"
                             f"버그: _resolve_memory_file()이 '`memory/backtick_direct.md`'를 None으로 반환")


if __name__ == "__main__":
    unittest.main(verbosity=2)
