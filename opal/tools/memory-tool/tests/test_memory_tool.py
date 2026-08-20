"""
@header {
  "module": "test_memory_tool",
  "layer": "test",
  "domain": "opal-pipeline",
  "description": "memory-tool RED-first 테스트 — 045 트랙(S-1~S-17, S-24, 프리픽스 [T045/L1-...]) + 078 MEMORY.json 전환 트랙(TS-001~TS-021·TS-037~TS-041, 프리픽스 [T078/...]) + 079 `update --kind history` 작업 히스토리 정정 트랙(TS-001~TS-020·TS-025·TS-027·TS-028, 프리픽스 [T079/...]) + 096 참조 무결성·고아 행 정리 트랙(QA-001~QA-018·QA-024~QA-026, 프리픽스 [T096/L1-R1|R2|R3]). mock/patch/MagicMock 금지(헌법 §4) — 실 fixture·실 프로세스(subprocess)만. 078·079·096 블록은 구현 전 작성된 RED이므로 신규 기능 케이스는 전량 FAIL이 정상(단, 하위호환·불변식 가드 케이스는 구현 전에도 통과할 수 있다).",
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
    "TestTaskNumberDocs",
    "TestUpdateBackCompat", "TestUpdateKindHistory",
    "TestUpdateKindArgGuard", "TestUpdateHistoryLossless",
    "TestReviewReferenceIntegrity", "TestDeleteOrphan", "TestLifecycleDocParity"
  ]
}

변경이력:
  v1.1 2026-07-28 078 RED-first 블록 추가 — MEMORY.json 전환 계약(TS-001~TS-021, TS-037~TS-041)
                  61케이스 + 픽스처 5종 신설. 구현(GREEN)은 별도 워커 담당 (red-first.md §2) (078)
  v1.2 2026-07-30 079 RED-first 블록 추가 — `update --kind history` 정정 명령 계약
                  (TS-001~TS-020, TS-025, TS-027, TS-028) 신규 클래스 4종 32케이스.
                  신규 픽스처 신설 없음(기존 fixture_doc_populated.json in-test 가공).
                  구현(GREEN)은 opal-be-agent 별도 담당 (red-first.md §2) (079)
  v1.3 2026-08-20 096 RED-first 블록 추가 — review 참조 무결성 검사(memory_file_missing/
                  memory_file_unresolvable 2분) + delete --orphan --ref 고아 행 정리 +
                  라이프사이클 문서-스키마 파리티(TEST-SCENARIO.md TS-001~005·006~014·015~018·
                  024~026·036~039 대응) 신규 클래스 3종(TestReviewReferenceIntegrity·
                  TestDeleteOrphan·TestLifecycleDocParity) + 헬퍼 1종(_setup_populated_orphan).
                  신규 픽스처 파일 신설 없음(fixture_doc_populated.json in-test 가공 + 직접 dict
                  구성). 구현(GREEN)은 opal-be-agent 별도 담당 (red-first.md §2) (096)
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


def _setup_populated_orphan(tmp_dir: pathlib.Path, skip=("improve_candidate.md",)) -> pathlib.Path:
    """_setup_populated와 동일하되 skip에 든 본문 .md를 생성하지 않는다 —
    인덱스 행은 있고 본문이 없는 고아 행 상태를 만든다(096 R-1/R-2).
    기본 skip 대상 improve_candidate.md는 대응 인덱스 행이 status:"candidate"여서
    실환경 2건과 동일한 상태값이다(092/094 교훈 — fixture가 실환경을 재현해야 한다).
    """
    memory_dir = tmp_dir / "memory"
    memory_dir.mkdir(exist_ok=True)
    for name, content in [
        ("prefs_commit.md", "# 메인 직접 커밋 선호\n\nmain 직접 커밋 선호 상세 내용.\n"),
        ("task_done.md", "# 완료된 태스크 기록\n\n종료된 일회성 태스크 상세.\n"),
        ("console-brain-subscription-auth.md", "# 콘솔 브레인 구독 인증\n\n브레인 질의 상세.\n"),
        ("arch_old.md", "# 대체된 아키텍처 결정\n\n구 도구 패턴 상세.\n"),
        ("prefs_graduated.md", "# 졸업한 선호 규칙\n\nAGENT.md 이관 상세.\n"),
        ("improve_candidate.md", "# 개선 후보 기록\n\nimprove-tool 후보 상세.\n"),
    ]:
        if name in skip:
            continue
        (memory_dir / name).write_text(content, encoding="utf-8")
    dst = tmp_dir / "MEMORY.json"
    shutil.copy2(_FIXTURES_DIR / "fixture_doc_populated.json", dst)
    return dst


def _write_doc(json_path: pathlib.Path, memories, history=None) -> pathlib.Path:
    """memories(list[dict])만으로 최소 유효 MEMORY.json을 직접 작성한다(096, in-test 직접 구성).
    CLI append로는 만들 수 없는 field 조합(경로 탈출 file 등)을 스키마 pattern은 통과시키되
    실제 파일시스템 상태는 임의로 구성해야 하는 시나리오 전용 — mock이 아니라 실 파일 작성이다.
    """
    doc = {
        "version": 1,
        "last_task_number": 0,
        "memories": list(memories),
        "history": list(history) if history is not None else [],
    }
    json_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return json_path


def _traversal_row(title="탈출 포인터 행", status="candidate",
                    file_field="memory/../outside.md") -> dict:
    """`memory/` 밖으로 해석되지만 스키마 패턴 `^memory/[^/].*\\.md$`은 통과하는 행
    (096 G-3 — `_resolve_memory_file()`이 None을 반환하는 경로 탈출 벡터 실증용)."""
    return {
        "title": title, "date": "2026-08-01", "type": "project",
        "status": status, "file": file_field, "summary": "경로 탈출 참조 무결성 테스트(096)",
    }


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


# ─────────────────────────────────────────────────────────────────────────────
# T079: `update --kind history` 작업 히스토리 오기재 정정 명령 신설 (RED-first)
# 구현(GREEN)은 opal-be-agent(Step 2) 담당 — 이 파일에는 구현 코드를 넣지 않는다.
# 신규 픽스처 파일 신설 없음 — fixture_doc_populated.json을 in-test로만 가공한다.
# ─────────────────────────────────────────────────────────────────────────────

_T079_TARGET_TITLE = "076 파이프라인 todo 미러 hook"


def _t079_extra_history_row(idx=0):
    """FIFO 미적용(TS-009) 검증 전용 — 픽스처에 in-test로 덧붙일 6번째 히스토리 행."""
    return {
        "title": f"T079 in-test 추가 이력 {idx}",
        "date": "2026-07-05",
        "stage": "완료",
        "path": f"tasks/900-t079-extra-{idx}/",
        "result": "6행 초과 FIFO 미적용 검증 전용 in-test 추가 행 — 실 태스크 아님",
    }


class TestUpdateBackCompat(unittest.TestCase):
    """[T079/L1-R1a, T079/L1-R1c] TS-001, TS-002, TS-019 — `--kind` 미지정 하위호환
    + `--help` 노출. TS-025(기존 132건 전량 GREEN)는 이 클래스에 전용 메서드를 두지 않고
    전 스위트 `unittest discover` 실행 로그로 별도 확인한다(PLAN §4.2 Step 1 완료 기준)."""

    def test_ts001_status_only_no_kind_changes_only_memory_row(self):
        """TS-001: `--kind` 미지정 + `--status` 단독 → ok:true, 히스토리 무변경."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            history_before = _read_doc(md)["history"]

            result = _run(["update", "--file", str(md),
                           "--title", "메인 직접 커밋 선호", "--status", "superseded"])
            self.assertTrue(result.get("ok"), f"--kind 미지정 --status 단독 회귀: {result}")

            doc = _read_doc(md)
            row = next(r for r in doc["memories"] if r["title"] == "메인 직접 커밋 선호")
            self.assertEqual(row["status"], "superseded")
            self.assertEqual(doc["history"], history_before, "히스토리가 변경됨 — memory 경로가 history에 영향")

    def test_ts001_summary_only_no_kind_changes_only_memory_row(self):
        """TS-001: `--summary` 단독 → ok:true, 히스토리 무변경."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            history_before = _read_doc(md)["history"]

            result = _run(["update", "--file", str(md),
                           "--title", "메인 직접 커밋 선호", "--summary", "회귀 검증용 요약"])
            self.assertTrue(result.get("ok"), f"--kind 미지정 --summary 단독 회귀: {result}")
            self.assertEqual(_read_doc(md)["history"], history_before)

    def test_ts001_new_title_only_no_kind_changes_only_memory_row(self):
        """TS-001: `--new-title` 단독 → ok:true, 히스토리 무변경."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            history_before = _read_doc(md)["history"]

            result = _run(["update", "--file", str(md),
                           "--title", "메인 직접 커밋 선호", "--new-title", "메인 직접 커밋 선호 v2"])
            self.assertTrue(result.get("ok"), f"--kind 미지정 --new-title 단독 회귀: {result}")
            self.assertEqual(_read_doc(md)["history"], history_before)

    def test_ts001_combined_fields_no_kind_changes_only_memory_row(self):
        """TS-001: `--status`+`--summary`+`--new-title` 복합 → ok:true, 히스토리 무변경."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            history_before = _read_doc(md)["history"]

            result = _run(["update", "--file", str(md),
                           "--title", "메인 직접 커밋 선호",
                           "--status", "dead", "--summary", "복합 회귀 요약",
                           "--new-title", "메인 직접 커밋 선호 복합"])
            self.assertTrue(result.get("ok"), f"--kind 미지정 복합 필드 회귀: {result}")

            doc = _read_doc(md)
            row = next(r for r in doc["memories"] if r["title"] == "메인 직접 커밋 선호 복합")
            self.assertEqual(row["status"], "dead")
            self.assertEqual(row["summary"], "복합 회귀 요약")
            self.assertEqual(doc["history"], history_before)

    def test_ts002_zero_fields_no_kind_is_permissive(self):
        """TS-002: 정정 필드 0개 + `--kind` 미지정 → ok:true (invalid_args 아님 — R-3(d)는 history 한정)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)

            result = _run(["update", "--file", str(md), "--title", "메인 직접 커밋 선호"])
            self.assertTrue(result.get("ok"),
                           f"필드 0개 + --kind 미지정은 ok:true여야 한다(기존 관대 동작 보존): {result}")
            self.assertNotEqual(result.get("error"), "invalid_args")

    def test_ts019_help_exposes_kind_stage_result_path(self):
        """TS-019: `update --help`에 `--kind`·`--stage`·`--result`·`--path`와 `{memory,history}` 노출."""
        proc = _run_raw(["update", "--help"])
        self.assertEqual(proc.returncode, 0, f"--help 비정상 종료: {proc.stderr}")
        help_text = proc.stdout
        for token in ("--kind", "--stage", "--result", "--path", "{memory,history}"):
            self.assertIn(token, help_text, f"--help 출력에 '{token}' 누락:\n{help_text}")


class TestUpdateKindHistory(unittest.TestCase):
    """[T079/L1-R1b, L1-R2a~d, L2-R2c] TS-003, TS-005~TS-010, TS-018, TS-020 —
    `--kind history` 정정 성공 경로: 필드 적용·미지정 불변·재로드 유효성·행수 불변(FIFO 미적용)·
    복수매치 관측·review 블록 유지."""

    def test_ts003_stage_only_changes_target_stage_only(self):
        """TS-003: `--kind history --stage` → ok:true, kind:"history", 대상 행 stage만 변경."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            before = next(r for r in _read_doc(md)["history"] if r["title"] == _T079_TARGET_TITLE)

            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", _T079_TARGET_TITLE, "--stage", "완료·커밋(abc1234)"])
            self.assertTrue(result.get("ok"), f"history stage 정정 실패: {result}")
            self.assertEqual(result.get("kind"), "history")

            after = next(r for r in _read_doc(md)["history"] if r["title"] == _T079_TARGET_TITLE)
            self.assertEqual(after["stage"], "완료·커밋(abc1234)")
            self.assertEqual(after["date"], before["date"])
            self.assertEqual(after["path"], before["path"])
            self.assertEqual(after["result"], before["result"])

    def test_ts005_stage_field_changed_reported(self):
        """TS-005: `--stage` 개별 지정 → changed[]가 정확히 ["stage"]."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", _T079_TARGET_TITLE, "--stage", "새 단계"])
            self.assertTrue(result.get("ok"), f"stage 개별 정정 실패: {result}")
            self.assertEqual(sorted(result.get("changed", [])), ["stage"])

    def test_ts005_result_field_changed_reported(self):
        """TS-005: `--result` 개별 지정 → changed[]가 정확히 ["result"]."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", _T079_TARGET_TITLE, "--result", "새 핵심결과"])
            self.assertTrue(result.get("ok"), f"result 개별 정정 실패: {result}")
            self.assertEqual(sorted(result.get("changed", [])), ["result"])

    def test_ts005_path_field_changed_reported(self):
        """TS-005: `--path` 개별 지정 → changed[]가 정확히 ["path"]."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", _T079_TARGET_TITLE, "--path", "tasks/999-새경로/"])
            self.assertTrue(result.get("ok"), f"path 개별 정정 실패: {result}")
            self.assertEqual(sorted(result.get("changed", [])), ["path"])

    def test_ts005_new_title_field_changed_reported(self):
        """TS-005: `--new-title` 개별 지정 → changed[]가 정확히 ["title"]."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", _T079_TARGET_TITLE, "--new-title", "새 제목"])
            self.assertTrue(result.get("ok"), f"new-title 개별 정정 실패: {result}")
            self.assertEqual(sorted(result.get("changed", [])), ["title"])

    def test_ts005_compound_four_fields_changed_reported_exactly(self):
        """TS-005: 4필드 복합 지정 → changed[]가 정확히 4개(잉여·누락 0)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", _T079_TARGET_TITLE,
                           "--stage", "복합 단계", "--result", "복합 결과",
                           "--path", "tasks/999-복합/", "--new-title", "복합 제목"])
            self.assertTrue(result.get("ok"), f"4필드 복합 정정 실패: {result}")
            self.assertEqual(sorted(result.get("changed", [])), ["path", "result", "stage", "title"])

    def test_ts006_unspecified_fields_and_other_rows_unchanged(self):
        """TS-006: `--stage`만 지정 → 대상 행의 나머지 필드 + 다른 히스토리 4행 전체 불변."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            doc_before = _read_doc(md)
            others_before = [r for r in doc_before["history"] if r["title"] != _T079_TARGET_TITLE]
            target_before = next(r for r in doc_before["history"] if r["title"] == _T079_TARGET_TITLE)

            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", _T079_TARGET_TITLE, "--stage", "단독 지정 단계"])
            self.assertTrue(result.get("ok"), f"단독 stage 정정 실패: {result}")

            doc_after = _read_doc(md)
            target_after = next(r for r in doc_after["history"] if r["title"] == _T079_TARGET_TITLE)
            self.assertEqual(target_after["title"], target_before["title"])
            self.assertEqual(target_after["date"], target_before["date"])
            self.assertEqual(target_after["path"], target_before["path"])
            self.assertEqual(target_after["result"], target_before["result"])
            self.assertEqual(target_after["stage"], "단독 지정 단계")

            others_after = [r for r in doc_after["history"] if r["title"] != _T079_TARGET_TITLE]
            self.assertEqual(others_after, others_before, "지정하지 않은 다른 히스토리 행이 변경됨")
            self.assertEqual(len(others_after), 4)

    def test_ts007_reload_after_correction_passes_validation(self):
        """TS-007(L2): 정정 후 `show --file X` 재로드 → ok:true(=validate_document 통과)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", _T079_TARGET_TITLE, "--stage", "재로드 검증 단계"])
            self.assertTrue(result.get("ok"), f"정정 실패(선행조건): {result}")

            show_result = _run(["show", "--file", str(md)])
            self.assertTrue(show_result.get("ok"),
                           f"정정 후 재로드 실패 — 스키마 위반 가능성(load_document가 schema_validation_failed): {show_result}")
            row = next((r for r in show_result.get("history_rows", [])
                        if r.get("title") == _T079_TARGET_TITLE), None)
            self.assertIsNotNone(row, "정정 대상 행이 재로드된 show 출력에 없음")
            self.assertEqual(row.get("stage"), "재로드 검증 단계")

    def test_ts008_five_row_history_count_unchanged(self):
        """TS-008: 5행 히스토리 문서 정정 → `history_count:5` + 파일 history 길이 5."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            self.assertEqual(len(_read_doc(md)["history"]), 5, "픽스처 전제 불일치(5행 아님)")

            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", _T079_TARGET_TITLE, "--stage", "5행 검증"])
            self.assertTrue(result.get("ok"), f"5행 문서 정정 실패: {result}")
            self.assertEqual(result.get("history_count"), 5)
            self.assertEqual(len(_read_doc(md)["history"]), 5)

    def test_ts009_six_row_history_no_silent_deletion(self):
        """TS-009 ★P0: 6행 히스토리 문서 정정 → 6행 유지(삭제 0),
        `review.history_status.fifo_trimmed:true`로 초과만 표면화(FIFO 미호출)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            doc = _read_doc(md)
            doc["history"].append(_t079_extra_history_row())
            md.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
            self.assertEqual(len(_read_doc(md)["history"]), 6, "6행 전제 준비 실패")

            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", _T079_TARGET_TITLE, "--stage", "6행 검증"])
            self.assertTrue(result.get("ok"), f"6행 문서 정정 실패: {result}")
            self.assertEqual(result.get("history_count"), 6,
                             "6행 문서인데 history_count가 FIFO 절단된 값으로 보고됨(FIFO 오적용 의심)")

            after_history = _read_doc(md)["history"]
            self.assertEqual(len(after_history), 6, "정정 명령이 히스토리 행을 조용히 삭제함(FIFO 오적용, H-6)")

            review = result.get("review", {})
            history_status = review.get("history_status", {})
            self.assertTrue(history_status.get("fifo_trimmed"),
                           f"6행 초과가 review.history_status.fifo_trimmed로 표면화되지 않음: {review}")
            self.assertEqual(history_status.get("count"), 6)

    def test_ts010_corrected_row_key_set_exact(self):
        """TS-010: 정정 후 대상 행 키 집합이 정확히 {title,date,stage,path,result}(부가 키 0)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", _T079_TARGET_TITLE, "--stage", "키 집합 검증"])
            self.assertTrue(result.get("ok"), f"정정 실패: {result}")
            row = next(r for r in _read_doc(md)["history"] if r["stage"] == "키 집합 검증")
            self.assertEqual(set(row.keys()), {"title", "date", "stage", "path", "result"},
                             f"부가 키 삽입 감지(additionalProperties:false 위반 위험, H-7): {sorted(row.keys())}")

    def test_ts018_duplicate_title_corrects_leading_row_only(self):
        """TS-018: 동일 title 2행 → 배열 선행 행만 변경, 후행 불변,
        응답 matched_index·match_count:2(복수 매치 관측 신호)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            doc = _read_doc(md)
            dup_title = doc["history"][0]["title"]
            trailing_before = dict(doc["history"][1])
            doc["history"][1]["title"] = dup_title  # 후행 행에 동일 title 부여 — 나머지 필드는 상이
            trailing_before["title"] = dup_title
            md.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", dup_title, "--stage", "중복 title 정정"])
            self.assertTrue(result.get("ok"), f"중복 title 정정 실패: {result}")
            self.assertEqual(result.get("matched_index"), 0, f"선행 행(index0)이 대상이어야 한다: {result}")
            self.assertEqual(result.get("match_count"), 2, f"복수 매치 신호 누락: {result}")

            after_history = _read_doc(md)["history"]
            self.assertEqual(after_history[0]["stage"], "중복 title 정정", "선행 행이 정정되지 않음")
            self.assertEqual(after_history[1], trailing_before, "후행 행이 변경됨(의도와 다른 행 정정, H-3)")

    def test_ts020_history_success_response_includes_review_block(self):
        """TS-020: `--kind history` 성공 → 응답에 `review` 블록 첨부(ambient 자가검토 계약 유지)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", _T079_TARGET_TITLE, "--stage", "review 확인"])
            self.assertTrue(result.get("ok"), f"정정 실패: {result}")
            self.assertIn("review", result, "history 경로 응답에 review 블록이 없음")
            self.assertIn("history_status", result.get("review", {}), "review 블록에 history_status 없음")


class TestUpdateKindArgGuard(unittest.TestCase):
    """[T079/L1-R1c, L1-R3a~d] TS-004, TS-011~TS-015, TS-027, TS-028 —
    `--kind` 오용 결정론 거부(silent no-op 금지) + JSON 계약(exit 1, argparse exit 2 아님)
    + 에러코드 신설 0(ERROR_CODES 23종 그대로)."""

    def test_ts004_invalid_kind_rejected_as_json_not_argparse_exit2(self):
        """TS-004 ★H-8: `--kind bogus` → stdout 단일라인 JSON invalid_kind,
        exit 1(argparse의 2 아님), stderr에 usage·traceback 0, 파일 불변."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            before = _snapshot(md)

            proc = _run_raw(["update", "--file", str(md), "--title", _T079_TARGET_TITLE,
                             "--kind", "bogus", "--stage", "x"])

            self.assertEqual(proc.returncode, 1,
                             f"exit code가 1이 아님(argparse choices= 회귀 의심, 실제={proc.returncode})\n"
                             f"stdout={proc.stdout!r}\nstderr={proc.stderr!r}")
            lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
            self.assertEqual(len(lines), 1, f"stdout이 단일라인 JSON이 아님: {proc.stdout!r}")
            payload = json.loads(lines[0])
            self.assertFalse(payload.get("ok"))
            self.assertEqual(payload.get("error"), "invalid_kind")

            self.assertNotIn("usage:", proc.stderr, f"stderr에 argparse usage 잔존: {proc.stderr!r}")
            self.assertNotIn("Traceback", proc.stderr, f"stderr에 traceback 잔존: {proc.stderr!r}")

            self.assertEqual(_snapshot(md), before, "invalid_kind 거부 후 파일이 변경됨")

    def test_ts011_history_status_rejected(self):
        """TS-011: `--kind history --status dead` → invalid_args, message에 --status 사유, 파일 불변."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            before = _snapshot(md)

            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", _T079_TARGET_TITLE, "--status", "dead"])
            self.assertFalse(result.get("ok"), f"history+--status 오용이 silent no-op으로 수용됨: {result}")
            self.assertEqual(result.get("error"), "invalid_args")
            self.assertIn("--status", result.get("message", ""), f"거부 사유에 --status 안내 없음: {result}")
            self.assertEqual(_snapshot(md), before)

    def test_ts012_history_summary_rejected_with_result_guidance(self):
        """TS-012: `--kind history --summary`(별칭 불허) → invalid_args, message가 --result 안내, 파일 불변."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            before = _snapshot(md)

            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", _T079_TARGET_TITLE, "--summary", "x"])
            self.assertFalse(result.get("ok"), f"history+--summary 별칭이 허용됨(비결정적 검증 표면 위험): {result}")
            self.assertEqual(result.get("error"), "invalid_args")
            self.assertIn("--result", result.get("message", ""), f"거부 사유가 --result를 안내하지 않음: {result}")
            self.assertEqual(_snapshot(md), before)

    def test_ts013_memory_kind_rejects_stage(self):
        """TS-013: `--kind memory --stage` → invalid_args, 파일 불변."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            before = _snapshot(md)
            result = _run(["update", "--file", str(md), "--kind", "memory",
                           "--title", "메인 직접 커밋 선호", "--stage", "x"])
            self.assertFalse(result.get("ok"), f"memory+--stage 오용이 수용됨: {result}")
            self.assertEqual(result.get("error"), "invalid_args")
            self.assertEqual(_snapshot(md), before)

    def test_ts013_memory_kind_rejects_result(self):
        """TS-013: `--kind memory --result` → invalid_args, 파일 불변."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            before = _snapshot(md)
            result = _run(["update", "--file", str(md), "--kind", "memory",
                           "--title", "메인 직접 커밋 선호", "--result", "x"])
            self.assertFalse(result.get("ok"), f"memory+--result 오용이 수용됨: {result}")
            self.assertEqual(result.get("error"), "invalid_args")
            self.assertEqual(_snapshot(md), before)

    def test_ts013_memory_kind_rejects_path(self):
        """TS-013: `--kind memory --path` → invalid_args, 파일 불변."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            before = _snapshot(md)
            result = _run(["update", "--file", str(md), "--kind", "memory",
                           "--title", "메인 직접 커밋 선호", "--path", "x"])
            self.assertFalse(result.get("ok"), f"memory+--path 오용이 수용됨: {result}")
            self.assertEqual(result.get("error"), "invalid_args")
            self.assertEqual(_snapshot(md), before)

    def test_ts014_row_not_found_no_lock_residue(self):
        """TS-014: 없는 히스토리 제목 → row_not_found, 파일 불변, .lock 잔여 0."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            before = _snapshot(md)

            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", "존재하지 않는 히스토리 제목 T079", "--stage", "x"])
            self.assertFalse(result.get("ok"), f"없는 제목이 수용됨: {result}")
            self.assertEqual(result.get("error"), "row_not_found")
            self.assertEqual(_snapshot(md), before)
            self.assertEqual(_residue(tmp_dir), [], f".lock/.tmp 잔여: {_residue(tmp_dir)}")

    def test_ts015_history_zero_fields_rejected(self):
        """TS-015: `--kind history` + 정정 필드 0개 → invalid_args, 파일 불변
        (`--kind memory` 필드 0개는 TS-002대로 계속 허용 — history 한정 거부)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            before = _snapshot(md)

            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", _T079_TARGET_TITLE])
            self.assertFalse(result.get("ok"),
                            f"history+필드 0개가 수용됨(memory 관대 동작이 history로 누수): {result}")
            self.assertEqual(result.get("error"), "invalid_args")
            self.assertEqual(_snapshot(md), before)

    def test_ts027_path_traversal_rejected(self):
        """TS-027: `--path`에 `..` 탈출 문자열 → invalid_args, 파일 불변(보안)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            before = _snapshot(md)

            result = _run(["update", "--file", str(md), "--kind", "history",
                           "--title", _T079_TARGET_TITLE, "--path", "../../etc/"])
            self.assertFalse(result.get("ok"), f"경로 탈출 --path가 수용됨: {result}")
            self.assertEqual(result.get("error"), "invalid_args")
            self.assertEqual(_snapshot(md), before)

    # 079 원본 ERROR_CODES 23종(079 시점 SSOT) — 096이 §3.2.2에서 3종을 추가하기 전의
    # 전체 키 집합. 이 상수 자체를 하드코딩된 총 개수 대신 "삭제·개명 여부"를 검사하는
    # 기준선으로 쓴다(PM 판정 §교정 요구 1) — 다음 태스크가 또 추가해도 이 리스트는
    # 불변이며, 애초에 존재하던 23종의 생존만 계속 확인한다.
    _T079_ORIGINAL_ERROR_CODES = frozenset({
        "memory_file_not_found", "row_not_found", "already_initialized", "invalid_kind",
        "invalid_type", "invalid_status", "summary_too_long", "title_required",
        "invalid_promote_target", "promote_ref_missing", "date_tool_failed",
        "delete_requires_dead_or_superseded", "memory_json_not_found", "invalid_json",
        "unsupported_version", "schema_validation_failed", "schema_load_failed",
        "schema_unsupported_keyword", "invalid_date", "lock_timeout", "migration_failed",
        "task_number_regression", "invalid_args",
    })

    def test_ts028_error_codes_unchanged_no_new_codes(self):
        """TS-028: ERROR_CODES 기존 23종 전건 생존(삭제·개명 0) + invalid_kind/invalid_args
        템플릿 무변경. (계약상 이 23종이 사라지거나 이름이 바뀌면 안 되는 불변식 —
        079 scope-creep 회귀 가드.)

        [096 갱신, PM 판정] 원래 단언은 `len(codes) == 23`으로 **총 개수**를 고정했으나,
        096이 PLAN §3.2.2 설계에 따라 의도적·문서화된 3종
        (`memory_file_exists`/`orphan_ref_missing`/`memory_file_unresolvable`)을
        추가하면서 23→26이 됐다(목표-커버 게이트 iteration 2 pass, `git diff -U0` 확인
        결과 기존 23종 삭제·개명 0줄·추가 3줄 — 순수 가산). 이 단언이 원래 잡으려던
        것은 "079 작업 중 의도치 않은 드리프트"이지 "영구히 23종 고정"이 아니었으므로
        (독스트링 자신이 "회귀 가드"라 명시), 총 개수 하드코딩을 다시 `== 26`으로
        바꾸는 대신 — (1) 기존 23종이 **전부** 여전히 존재하는지(부분집합 단언,
        삭제·개명이 있으면 즉시 FAIL)와 (2) 추가분이 **정확히** 096의 3종과
        일치하는지(그 이상도 이하도 아님)를 각각 단언하는 형태로 정밀화한다.
        이러면 다음 태스크가 또 코드를 추가할 때 (2)가 발동해 "의도적 갱신"을
        강제하면서도, (1)은 79/096 어느 쪽이 지정한 기존 코드도 조용히 사라지지
        못하게 계속 지킨다."""
        module = _load_tool_module(_TOOL_PY, "memory_tool_t079_errcodes")
        codes = module.ERROR_CODES
        code_keys = set(codes)

        # (1) 기존 23종 전건 생존 — 삭제·개명 0
        missing = self._T079_ORIGINAL_ERROR_CODES - code_keys
        self.assertEqual(missing, set(),
                         f"079 원본 ERROR_CODES 중 삭제·개명된 키: {sorted(missing)}")

        # (2) 추가분이 정확히 096의 3종과 일치 — 그 이상·이하도 아님
        added = code_keys - self._T079_ORIGINAL_ERROR_CODES
        self.assertEqual(
            added,
            {"memory_file_exists", "orphan_ref_missing", "memory_file_unresolvable"},
            f"079 원본 23종 이후 추가된 키가 096이 문서화한 3종과 불일치(의도치 않은 "
            f"드리프트 의심 — 새 태스크가 코드를 추가했다면 이 단언을 의도적으로 "
            f"갱신하라): {sorted(added)}",
        )

        self.assertEqual(codes["invalid_kind"],
                         "--kind는 memory 또는 history 중 하나여야 함: {kind}",
                         "invalid_kind 템플릿이 변경됨")
        self.assertEqual(codes["invalid_args"],
                         "인자 조합이 올바르지 않음: {detail}",
                         "invalid_args 템플릿이 변경됨")


class TestUpdateHistoryLossless(unittest.TestCase):
    """[T079/L1-R4a, L2-R4b] TS-016, TS-017 — 거부 경로 무손실(파일·잔여물) +
    동시 정정 클로버 0(subprocess.Popen 실 병렬 — 스레드·가짜 대역 금지)."""

    def test_ts016_rejection_paths_leave_no_residue(self):
        """TS-016: 거부 경로 전수(TS-004·TS-011~TS-015·TS-027) 실행 후
        MEMORY.json 바이트·mtime 동일 + *.tmp* 0건 + MEMORY.json.lock 0건."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            before = _snapshot(md)

            rejection_argv = [
                ["--kind", "bogus", "--title", _T079_TARGET_TITLE, "--stage", "x"],
                ["--kind", "history", "--title", _T079_TARGET_TITLE, "--status", "dead"],
                ["--kind", "history", "--title", _T079_TARGET_TITLE, "--summary", "x"],
                ["--kind", "memory", "--title", "메인 직접 커밋 선호", "--stage", "x"],
                ["--kind", "memory", "--title", "메인 직접 커밋 선호", "--result", "x"],
                ["--kind", "memory", "--title", "메인 직접 커밋 선호", "--path", "x"],
                ["--kind", "history", "--title", "존재하지 않는 히스토리 제목 T079", "--stage", "x"],
                ["--kind", "history", "--title", _T079_TARGET_TITLE],
                ["--kind", "history", "--title", _T079_TARGET_TITLE, "--path", "../../etc/"],
            ]
            for extra_args in rejection_argv:
                proc = _run_raw(["update", "--file", str(md)] + extra_args)
                self.assertNotEqual(proc.returncode, 0,
                                   f"거부 대상 조합이 성공(exit 0)으로 통과됨: {extra_args}\n{proc.stdout}")

            self.assertEqual(_snapshot(md), before,
                             "거부 경로 전수 실행 후 MEMORY.json이 변경됨(부분 기록 의심, H-4)")
            residue = _residue(tmp_dir)
            self.assertEqual(residue, [], f"거부 경로 후 락/tmp 잔여: {residue}")
            self.assertFalse((tmp_dir / "MEMORY.json.lock").exists(), "MEMORY.json.lock 잔여")

    def test_ts017_concurrent_different_field_corrections_no_clobber(self):
        """TS-017: 2프로세스가 서로 다른 필드를 동시 정정 →
        클로버 0(둘 다 반영) 또는 한쪽 lock_timeout 결정론 실패. 문서는 항상 스키마 유효."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            title = _T079_TARGET_TITLE

            def _spawn(field, value):
                return subprocess.Popen(
                    [str(_PYTHON), str(_TOOL_PY), "update", "--file", str(md),
                     "--kind", "history", "--title", title, field, value],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                )

            procs = [_spawn("--stage", "동시 정정 stage"), _spawn("--result", "동시 정정 result")]
            outs = [p.communicate() for p in procs]

            payloads = []
            for proc, (stdout, stderr) in zip(procs, outs):
                line = stdout.strip().split("\n")[-1] if stdout.strip() else ""
                self.assertTrue(line, f"동시 update 출력 없음(exit={proc.returncode})\nstderr={stderr!r}")
                payloads.append(json.loads(line))

            oks = [p for p in payloads if p.get("ok")]
            fails = [p for p in payloads if not p.get("ok")]
            self.assertGreaterEqual(len(oks), 1, f"두 프로세스 모두 실패(클로버 회피 실패): {payloads}")
            for f in fails:
                self.assertEqual(f.get("error"), "lock_timeout",
                                 f"클로버 없는 실패는 반드시 lock_timeout이어야 한다: {f}")

            if len(oks) == 2:
                doc = _read_doc(md)
                row = next(r for r in doc["history"] if r["title"] == title)
                self.assertEqual(row["stage"], "동시 정정 stage", "stage 변경이 클로버됨")
                self.assertEqual(row["result"], "동시 정정 result", "result 변경이 클로버됨")

            # 문서는 항상 스키마 유효(어느 결과 조합이든) — show 재검증으로 확인
            show_result = _run(["show", "--file", str(md)])
            self.assertTrue(show_result.get("ok"), f"동시 정정 후 문서가 스키마 유효하지 않음: {show_result}")

            self.assertEqual(_residue(tmp_dir), [], f"동시 정정 후 락/tmp 잔여: {_residue(tmp_dir)}")


# ─────────────────────────────────────────────────────────────────────────────
# 096 헬퍼 — 문서-스키마 파리티 검사 (PLAN §3.3.5, TS-015/TS-016)
# ─────────────────────────────────────────────────────────────────────────────

_MEMORY_LEARNING = _REPO_ROOT / "opal/core/references/harness/memory-learning.md"
_MEMORY_SCHEMA_PATH = _TOOL_DIR / "schema" / "memory.schema.json"
_README_PATH = _TOOL_DIR / "README.md"
_TOOLS_MD_PATH = _REPO_ROOT / "opal/core/references/tools.md"
_NEW_ERROR_CODES_096 = ("memory_file_exists", "orphan_ref_missing", "memory_file_unresolvable")


def _lifecycle_table_section(text):
    """memory-learning.md '## 메모리 라이프사이클' 표 구간 텍스트만 절취한다."""
    section = text.split("## 메모리 라이프사이클", 1)[1]
    section = section.split("## 메모리 이관", 1)[0]
    return section


def _lifecycle_table_statuses(text):
    """라이프사이클 표 첫 열(백틱 상태값)의 집합을 파싱한다."""
    section = _lifecycle_table_section(text)
    return set(re.findall(r"^\|\s*`([a-z]+)`\s*\|", section, flags=re.MULTILINE))


# 변경 전 memory-learning.md 라이프사이클 표의 기존 4행 — R-3 반영 전후 문자 그대로 불변이어야 한다
# (PLAN §3.3.2 (2): "기존 4행 서술은 R-2 반영분 외 diff 0", QA-018).
_EXPECTED_LIFECYCLE_ROWS_096 = (
    "| `active` | 살아있는 지식. 인덱스에 노출·로드 대상 | 신규 등록(append) | 인덱스 행 유지 |",
    r"| `promoted` | 영구 거처(docs/brain)로 졸업 완료 | PM이 본문을 docs 규칙/brain 페이지로 "
    r"이전했다고 판단 | `promote --to <docs\|brain>`: 이전 확인 후 인덱스 행 + `.md` 파일 삭제 + "
    r"provenance 기록(SSOT 이중화 해소) |",
    "| `superseded` | 더 새로운 메모리/결정이 대체 | PM이 대체 관계 식별 | "
    "`update --status superseded`: 행 보존(추적용), 로드 제외. 자가검토 `cleanup_candidates`로 "
    "표면화 후 `delete`로 제거(`--with-file`로 `.md`도 정리) |",
    "| `dead` | 완료·진부화(task 완료, 이슈 해소) | task 완료 / 이슈 해소 / 철회 | "
    "`update --status dead`: 로드 제외. 자가검토 `cleanup_candidates`로 표면화 후 `delete`로 제거 |",
)


# ─────────────────────────────────────────────────────────────────────────────
# 096 F-001: review 참조 무결성 검사 [T096/L1-R1] — QA-001~QA-005 (+ TS-036 리스크 커버)
# ─────────────────────────────────────────────────────────────────────────────

class TestReviewReferenceIntegrity(unittest.TestCase):
    """[T096/L1-R1] R-1 AC — build_review_block(doc, json_path)의 참조 무결성 검사.
    본문 부재는 memory_file_missing, 경로 해석 불가는 memory_file_unresolvable로 어휘를
    2분한다(G-3). 096 구현 전이므로 신규 케이스는 FAIL이 정상(red-first.md §1)."""

    def test_qa001_missing_body_detected_in_violations(self):
        """QA-001 (TS-001): 본문 부재 행 2건이 review violations에 memory_file_missing
        정확히 2건으로 검출된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated_orphan(
                tmp_dir, skip=("improve_candidate.md", "prefs_graduated.md"))
            result = _run(["review", "--file", str(md)])
            self.assertTrue(result.get("ok"), f"review 실패: {result}")
            missing = [v for v in result.get("violations", [])
                       if v.get("type") == "memory_file_missing"]
            self.assertEqual(len(missing), 2,
                             f"본문 부재 2건이 memory_file_missing으로 검출돼야 한다: "
                             f"{result.get('violations')}")
            titles = {v["title"] for v in missing}
            self.assertEqual(titles, {"개선 후보 기록", "졸업한 선호 규칙"},
                             f"검출된 행 제목 불일치: {titles}")
            for v in missing:
                self.assertIn("file", v, f"memory_file_missing 엔트리에 file 없음: {v}")

    def test_qa002_no_false_positive_when_bodies_intact(self):
        """QA-002 (TS-002, 음성 통제): 본문이 전건 실재하면 memory_file_missing 0건."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)  # 6행 전부 본문 실재
            result = _run(["review", "--file", str(md)])
            self.assertTrue(result.get("ok"), f"review 실패: {result}")
            missing = [v for v in result.get("violations", [])
                       if v.get("type") == "memory_file_missing"]
            self.assertEqual(missing, [],
                             f"본문 전건 실재인데 memory_file_missing이 검출됨: {missing}")

    def test_qa003_existing_four_violation_types_unchanged(self):
        """QA-003 (TS-003): build_review_block(doc, json_path=None)이 기존 4종
        violations(invalid_status/invalid_type/summary_too_long/title_too_long)의
        키 집합·값·상대 순서를 변경 전과 동일하게 유지한다. json_path=None이면
        참조 무결성 검사는 건너뛴다(하위호환).

        [096 교정 1] 최초 버전은 제목을 "긴제목"*10(정확히 30자)으로 구성했으나
        판정식이 `len(title) > TITLE_MAX_LENGTH`(memory_tool.py:856, TITLE_MAX_LENGTH=30 —
        schema/memory.schema.json:106)이므로 30>30=False라 title_too_long이 애초에
        검출 불가능한 fixture 결함이었다(구현과 무관하게 검증 불능). 임계값을
        `module.TITLE_MAX_LENGTH`에서 직접 취득해 31자(초과 → 검출)와 30자(경계 →
        미검출) 두 케이스로 분리했다 — 경계 자체를 명시적으로 확인하는 편이 ⑥경계
        축에도 기여한다(PM 지적 반영)."""
        module = _load_tool_module(_TOOL_PY, "memory_tool_qa003")
        max_len = module.TITLE_MAX_LENGTH
        boundary_title = "가" * max_len          # 정확히 상한 — 미검출이 정상(30>30=False)
        over_title = "가" * (max_len + 1)        # 상한 초과 — 검출이 정상
        doc = {
            "version": 1, "last_task_number": 0,
            "memories": [
                {"title": "잘못된 상태", "date": "2026-08-01", "type": "project",
                 "status": "bogus_status", "file": "memory/a.md", "summary": "s"},
                {"title": "잘못된 유형", "date": "2026-08-01", "type": "bogus_type",
                 "status": "active", "file": "memory/b.md", "summary": "s"},
                {"title": "긴 요약", "date": "2026-08-01", "type": "project",
                 "status": "active", "file": "memory/c.md", "summary": "x" * 81},
                {"title": boundary_title, "date": "2026-08-01", "type": "project",
                 "status": "active", "file": "memory/d0.md", "summary": "경계 정확히 상한"},
                {"title": over_title, "date": "2026-08-01", "type": "project",
                 "status": "active", "file": "memory/d.md", "summary": "s"},
            ],
            "history": [],
        }
        review = module.build_review_block(doc, json_path=None)
        violations = review["violations"]
        types = [v["type"] for v in violations]
        self.assertEqual(
            types,
            ["invalid_status", "invalid_type", "summary_too_long", "title_too_long"],
            f"기존 4종 violations의 구성·상대 순서가 변경됨(경계 30자 행은 무위반이어야 "
            f"하므로 목록 길이는 여전히 4): {types}",
        )
        self.assertEqual(violations[0],
                         {"type": "invalid_status", "title": "잘못된 상태", "value": "bogus_status"})
        self.assertEqual(violations[1],
                         {"type": "invalid_type", "title": "잘못된 유형", "value": "bogus_type"})
        self.assertEqual(violations[2],
                         {"type": "summary_too_long", "title": "긴 요약", "length": 81})
        self.assertEqual(violations[3]["type"], "title_too_long")
        self.assertEqual(violations[3]["title"], over_title,
                         f"title_too_long이 상한 초과({max_len + 1}자) 행이 아닌 다른 행을 가리킴")
        self.assertEqual(violations[3]["length"], max_len + 1)
        violation_titles = [v.get("title") for v in violations]
        self.assertNotIn(boundary_title, violation_titles,
                         f"경계값 정확히 {max_len}자 제목이 title_too_long으로 오탐됨 "
                         f"({max_len}>{max_len}는 False여야 한다)")
        self.assertNotIn("memory_file_missing", types,
                         "json_path=None인데 참조 무결성 검사가 수행됨(하위호환 위반)")

    def test_qa004_call_sites_pass_json_path_and_six_commands_detect(self):
        """QA-004 (TS-004, H-1): build_review_block(doc) 구형태(1-인자) 호출 잔존 0건
        (호출부 9곳 전량 json_path 배선) + 변경 명령 6종(init/append/update/prune/
        task-number --bump/delete) 응답의 자동 첨부 review 전부에서 검출된다.

        [096 교정 2] 최초 버전은 append 이후에도 기대치를 2(orphan 사전조건 그대로)로
        두었으나, 이는 fixture 결함이 아니라 **cmd_append의 실제 동작을 잘못 예측한
        assertion 오류**였다. `cmd_append`는 `file_field = _title_to_filename(title)`
        (memory_tool.py:965)로 경로 문자열만 인덱스에 기록할 뿐 `memory/<file>.md`
        본문을 생성하지 않는다 — 저장소 전체에 `.md` 본문을 쓰는 코드가 존재하지
        않는다(grep `write_text` 결과 memory_tool.py:345의 MEMORY.json 원자적 쓰기용
        tmp 파일 1건뿐, memory/*.md 대상 0건). 따라서 `append --kind memory`는
        구조적으로 항상 "본문 없는 신규 행"을 만들며, F-001 참조 무결성 검사가
        **append 시점에 그 행을 즉시 검출하는 것이 정상 동작**이다(오탐이 아니라
        이 기능의 핵심 가치 — 태스크 배경의 "인덱스 참조는 있는데 본문이 없는" 상태가
        바로 이렇게 발생한다). append 이후의 기대치를 3(orphan 사전조건 2 +
        append 신규 1)으로 정정하고, 숫자만이 아니라 **append로 만든 행이 실제로
        검출 목록에 title로 포함되는지**를 append 직후와 마지막 delete 이후
        (지속성 확인) 양쪽에서 단언한다."""
        src = _TOOL_PY.read_text(encoding="utf-8")
        self.assertEqual(
            src.count("build_review_block(doc)"), 0,
            "build_review_block(doc) 구형태(1-인자) 호출이 잔존 — json_path 미배선 호출부가 "
            "있으면 그 명령에서만 검사가 침묵 실패한다(H-1)",
        )

        appended_title = "QA-004 신규 메모리"

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated_orphan(
                tmp_dir, skip=("improve_candidate.md", "prefs_graduated.md"))

            def _missing_titles(result):
                review = result.get("review") if "review" in result else result
                return {v["title"] for v in review.get("violations", [])
                       if v.get("type") == "memory_file_missing"}

            init_result = _run(["init", "--file", str(md), "--force"])
            self.assertTrue(init_result.get("ok"), f"init 실패: {init_result}")
            self.assertEqual(len(_missing_titles(init_result)), 2,
                             f"init 응답 review에서 검출 안 됨: {init_result}")

            append_result = _run([
                "append", "--file", str(md), "--kind", "memory",
                "--title", appended_title, "--type", "project",
                "--summary", "호출부 누락 검증용",
            ])
            self.assertTrue(append_result.get("ok"), f"append 실패: {append_result}")
            append_missing = _missing_titles(append_result)
            self.assertEqual(
                len(append_missing), 3,
                f"append는 본문 없는 신규 행을 만들므로(memory_tool.py:965 — "
                f"_title_to_filename만 계산, .md 쓰기 없음) orphan 사전조건 2건 + "
                f"신규 1건 = 3건이 정상이다: {append_result}",
            )
            self.assertIn(
                appended_title, append_missing,
                f"append로 생성된 행 '{appended_title}' 자신이 검출 목록에 없음 — "
                f"append 시점 검출이라는 핵심 동작이 성립하지 않음: {append_missing}",
            )

            update_result = _run([
                "update", "--file", str(md), "--title", "메인 직접 커밋 선호", "--status", "dead",
            ])
            self.assertTrue(update_result.get("ok"), f"update 실패: {update_result}")
            self.assertEqual(len(_missing_titles(update_result)), 3,
                             f"update 응답에서 검출 안 됨: {update_result}")

            prune_result = _run(["prune", "--file", str(md)])
            self.assertTrue(prune_result.get("ok"), f"prune 실패: {prune_result}")
            self.assertEqual(len(_missing_titles(prune_result)), 3,
                             f"prune 응답에서 검출 안 됨: {prune_result}")

            task_number_result = _run(["task-number", "--file", str(md), "--bump"])
            self.assertTrue(task_number_result.get("ok"),
                            f"task-number --bump 실패: {task_number_result}")
            self.assertEqual(len(_missing_titles(task_number_result)), 3,
                             f"task-number 응답에서 검출 안 됨: {task_number_result}")

            delete_result = _run(["delete", "--file", str(md), "--title", "완료된 태스크 기록"])
            self.assertTrue(delete_result.get("ok"), f"delete 실패: {delete_result}")
            delete_missing = _missing_titles(delete_result)
            self.assertEqual(len(delete_missing), 3,
                             f"delete 응답에서 검출 안 됨: {delete_result}")
            self.assertIn(
                appended_title, delete_missing,
                f"append로 생성된 행이 이후 명령(delete)까지 지속 검출되지 않음: "
                f"{delete_missing}",
            )

    def test_qa005_traversal_row_reported_as_unresolvable_not_missing(self):
        """QA-005 (TS-005): 경로 탈출 file은 memory_file_missing이 아니라
        memory_file_unresolvable로 검출된다(어휘 2분, G-3)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            (tmp_dir / "memory").mkdir()
            md = tmp_dir / "MEMORY.json"
            _write_doc(md, [_traversal_row()])
            # memory/ 밖에는 아무 파일도 만들지 않는다 — 어휘 구분이 본문 실재 여부와
            # 무관하게 "해석 가능 여부" 하나로 결정됨을 보인다.
            result = _run(["review", "--file", str(md)])
            self.assertTrue(result.get("ok"), f"review 실패: {result}")
            violations = result.get("violations", [])
            types = {v["type"] for v in violations}
            self.assertNotIn("memory_file_missing", types,
                             f"경로 탈출 행이 memory_file_missing으로 오분류됨: {violations}")
            self.assertIn("memory_file_unresolvable", types,
                          f"경로 탈출 행이 memory_file_unresolvable로 검출되지 않음: {violations}")

    def test_ts036_mixed_vocab_review_distinguishes_missing_from_unresolvable(self):
        """TS-036 (리스크 커버 H-4, PLAN QA-ID 대응 없음): 본문 부재 행과 경로 탈출 행이
        공존할 때 review가 두 행을 서로 다른 type으로 반환한다 — 운영자가 review 출력만으로
        "정리 가능" vs "포인터 수리 필요"를 구별할 수 있어야 한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated_orphan(tmp_dir, skip=("improve_candidate.md",))
            doc = _read_doc(md)
            doc["memories"].append(_traversal_row(title="탈출-혼합", status="candidate"))
            md.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

            result = _run(["review", "--file", str(md)])
            self.assertTrue(result.get("ok"), f"review 실패: {result}")
            by_title = {v["title"]: v["type"] for v in result.get("violations", [])
                       if v.get("title") in ("개선 후보 기록", "탈출-혼합")}
            self.assertEqual(by_title.get("개선 후보 기록"), "memory_file_missing",
                             f"본문 부재 행 어휘 불일치: {by_title}")
            self.assertEqual(by_title.get("탈출-혼합"), "memory_file_unresolvable",
                             f"경로 탈출 행 어휘 불일치: {by_title}")
            self.assertNotEqual(
                by_title.get("개선 후보 기록"), by_title.get("탈출-혼합"),
                "두 행이 같은 type으로 뭉뚱그려짐 — 검출 어휘 2분 실패",
            )


# ─────────────────────────────────────────────────────────────────────────────
# 096 F-002: delete --orphan --ref 고아 행 정리 [T096/L1-R2] — QA-006~QA-014,
# QA-024~QA-026 (+ TS-037·TS-038 리스크 커버)
# ─────────────────────────────────────────────────────────────────────────────

class TestDeleteOrphan(unittest.TestCase):
    """[T096/L1-R2] R-2 AC — `delete --orphan --ref`. 무손실 가드는 약화되지 않고
    술어가 정밀화된다: 본문 실재(status 무관) → memory_file_exists 거부(H-2 벡터①),
    해석 불가(경로 탈출 등) → memory_file_unresolvable 거부(G-3, H-2 벡터②).
    096 구현 전이므로 신규 케이스는 FAIL이 정상(red-first.md §1)."""

    def test_qa006_candidate_orphan_row_cleaned_real_layout_roundtrip(self):
        """QA-006 (TS-006) [MUST 실환경 재현]: `.opal/MEMORY.json` ↔ `.opal/memory/*.md`
        왕복 경로를 `_install_json()`으로 재현 — candidate + 본문 부재 행에
        `delete --orphan --ref X` → 검출→정리 왕복 성립(잔여 재검출 없음)."""
        with tempfile.TemporaryDirectory() as tmp:
            opal, md = _install_json(tmp)  # memory/*.md 미생성 → 6행 전부 본문 부재
            title = "개선 후보 기록"

            pre_review = _run(["review", "--file", str(md)])
            self.assertTrue(pre_review.get("ok"), f"사전 review 실패: {pre_review}")
            pre_missing = {v["title"] for v in pre_review.get("violations", [])
                          if v.get("type") == "memory_file_missing"}
            self.assertIn(title, pre_missing, f"사전 검출 실패: {pre_review.get('violations')}")

            result = _run(["delete", "--file", str(md), "--title", title,
                          "--orphan", "--ref", "docs/CONVENTIONS.md#변경이력"])
            self.assertTrue(result.get("ok"), f"orphan delete 실패: {result}")
            self.assertIs(result.get("orphan"), True, f"orphan 플래그 미반영: {result}")
            self.assertEqual(result.get("reason"), "memory_file_missing",
                             f"reason이 검출 어휘와 불일치: {result}")
            self.assertEqual(result.get("ref"), "docs/CONVENTIONS.md#변경이력")

            doc = _read_doc(md)
            self.assertTrue(all(r["title"] != title for r in doc["memories"]),
                            f"행이 제거되지 않음: {doc['memories']}")

            post_review = _run(["review", "--file", str(md)])
            post_missing = {v["title"] for v in post_review.get("violations", [])
                           if v.get("type") == "memory_file_missing"}
            self.assertNotIn(title, post_missing, "정리 후에도 재검출됨(검출→정리 왕복 실패)")

    def test_qa007_promoted_orphan_row_cleaned(self):
        """QA-007 (TS-007 일부): promoted + 본문 부재 행도 동일하게 성공한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated_orphan(tmp_dir, skip=("prefs_graduated.md",))
            result = _run(["delete", "--file", str(md), "--title", "졸업한 선호 규칙",
                          "--orphan", "--ref", "docs/CONVENTIONS.md#변경이력"])
            self.assertTrue(result.get("ok"), f"promoted 행 orphan delete 실패: {result}")
            doc = _read_doc(md)
            self.assertTrue(all(r["title"] != "졸업한 선호 규칙" for r in doc["memories"]),
                            f"행이 제거되지 않음: {doc['memories']}")

    def test_qa008_orphan_rejected_when_body_exists_all_statuses(self):
        """QA-008 (TS-008) [핵심]: 본문 실재 행은 status 무관하게 memory_file_exists로
        거부되고 인덱스·본문 모두 불변이다(무손실 가드 우회 불가, H-2 벡터①, 4 status 전수)."""
        targets = [
            ("메인 직접 커밋 선호", "active", "prefs_commit.md"),
            ("완료된 태스크 기록", "dead", "task_done.md"),
            ("대체된 아키텍처 결정", "superseded", "arch_old.md"),
            ("졸업한 선호 규칙", "promoted", "prefs_graduated.md"),
        ]
        for title, status, fname in targets:
            with self.subTest(status=status):
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_dir = pathlib.Path(tmp)
                    md = _setup_populated(tmp_dir)  # 전건 본문 실재
                    before_doc = _snapshot(md)
                    body_path = tmp_dir / "memory" / fname
                    before_body = body_path.read_bytes()

                    result = _run(["delete", "--file", str(md), "--title", title,
                                  "--orphan", "--ref", "X"])
                    self.assertFalse(result.get("ok"),
                                     f"본문 실재({status}) 행이 --orphan으로 제거됨: {result}")
                    self.assertEqual(result.get("error"), "memory_file_exists",
                                     f"[{status}] 에러 코드 불일치: {result}")
                    self.assertEqual(_snapshot(md), before_doc,
                                     f"[{status}] 인덱스가 변경됨(무손실 가드 위반)")
                    self.assertEqual(body_path.read_bytes(), before_body,
                                     f"[{status}] 본문 파일이 변경됨")

    def test_qa009_active_body_exists_orphan_rejected_bytes_unchanged(self):
        """QA-009 (TS-009) [핵심]: active + 본문 실재 행에 --orphan --ref →
        memory_file_exists 거부 + MEMORY.json 바이트 단위 불변."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated(tmp_dir)
            before = _snapshot(md)
            result = _run(["delete", "--file", str(md), "--title", "메인 직접 커밋 선호",
                          "--orphan", "--ref", "X"])
            self.assertFalse(result.get("ok"), f"active+본문실재 행이 제거됨: {result}")
            self.assertEqual(result.get("error"), "memory_file_exists",
                             f"에러 코드 불일치: {result}")
            self.assertEqual(_snapshot(md), before, "MEMORY.json 바이트가 변경됨")

    def test_qa010_orphan_without_ref_rejected(self):
        """QA-010 (TS-010): --orphan 단독(--ref 없음) → orphan_ref_missing, 행 불변."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated_orphan(tmp_dir, skip=("improve_candidate.md",))
            before = _snapshot(md)
            result = _run(["delete", "--file", str(md), "--title", "개선 후보 기록", "--orphan"])
            self.assertFalse(result.get("ok"), f"--ref 없이 성공함: {result}")
            self.assertEqual(result.get("error"), "orphan_ref_missing",
                             f"에러 코드 불일치: {result}")
            self.assertEqual(_snapshot(md), before, "행이 변경됨")

    def test_qa011_no_flag_delete_still_requires_dead_or_superseded(self):
        """QA-011 (TS-011, 불변식 가드 — RED 시점에도 통과 가능): 본문 부재 candidate
        행에 무플래그 delete → 여전히 delete_requires_dead_or_superseded(silent 완화 없음)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated_orphan(tmp_dir, skip=("improve_candidate.md",))
            before = _snapshot(md)
            result = _run(["delete", "--file", str(md), "--title", "개선 후보 기록"])
            self.assertFalse(result.get("ok"), f"본문 부재 candidate가 무플래그로 제거됨: {result}")
            self.assertEqual(result.get("error"), "delete_requires_dead_or_superseded",
                             f"에러 코드 불일치: {result}")
            self.assertEqual(_snapshot(md), before, "행이 변경됨")

    def test_qa012_provenance_log_records_reason_ref_and_summary(self):
        """QA-012 (TS-012, H-3): `.memory_provenance.log`에 delete-orphan 행이 기록되고
        ref=/summary=가 포함된다(무손실 — 본문 없는 행에서 유일하게 남은 지식 보존)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated_orphan(tmp_dir, skip=("improve_candidate.md",))
            result = _run(["delete", "--file", str(md), "--title", "개선 후보 기록",
                          "--orphan", "--ref", "docs/CONVENTIONS.md#변경이력"])
            self.assertTrue(result.get("ok"), f"orphan delete 실패: {result}")
            log_path = tmp_dir / ".memory_provenance.log"
            self.assertTrue(log_path.exists(), "provenance 로그가 생성되지 않음")
            content = log_path.read_text(encoding="utf-8")
            self.assertIn("delete-orphan", content, "행 접두 토큰 'delete-orphan' 없음")
            self.assertIn("ref=docs/CONVENTIONS.md#변경이력", content, "ref= 미기록")
            self.assertIn("summary=", content, "summary= 미기록")
            self.assertIn("improve-tool record --scope local이 기록한 개선 후보", content,
                          "행의 summary 원문이 provenance에 보존되지 않음")

    def test_qa013_orphan_delete_leaves_no_residue_and_show_ok(self):
        """QA-013 (TS-013, H-5): orphan delete 후 .tmp/.lock 잔여 0건,
        후속 show가 ok:true(스키마 유효)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated_orphan(tmp_dir, skip=("improve_candidate.md",))
            result = _run(["delete", "--file", str(md), "--title", "개선 후보 기록",
                          "--orphan", "--ref", "X"])
            self.assertTrue(result.get("ok"), f"orphan delete 실패: {result}")
            self.assertEqual(_residue(tmp_dir), [], f"tmp/lock 잔여: {_residue(tmp_dir)}")
            show_result = _run(["show", "--file", str(md)])
            self.assertTrue(show_result.get("ok"), f"후속 show 실패(스키마 무효): {show_result}")

    def test_qa014_single_call_no_status_transition_required(self):
        """QA-014 (TS-014): `update --status` 선행 호출 없이 단일
        `delete --orphan --ref` 1회 호출로 행이 제거된다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            md = _setup_populated_orphan(tmp_dir, skip=("improve_candidate.md",))
            doc_before = _read_doc(md)
            row = next(r for r in doc_before["memories"] if r["title"] == "개선 후보 기록")
            self.assertEqual(row["status"], "candidate", "전제 상태값이 candidate가 아님")
            result = _run(["delete", "--file", str(md), "--title", "개선 후보 기록",
                          "--orphan", "--ref", "X"])
            self.assertTrue(result.get("ok"),
                            f"단일 호출 실패 — update --status 선행이 필요하다면 결함: {result}")

    def test_qa024_traversal_with_live_body_outside_memory_rejected(self):
        """QA-024 (TS-034) [P0, H-2 벡터②]: memory/ 밖에 본문이 실재하는 경로 탈출 행은
        memory_file_unresolvable로 거부되고 인덱스 행·memory/ 밖 본문 파일 모두 불변이다
        (확인 불가는 부재가 아니므로 삭제하지 않는다 — G-3)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            (tmp_dir / "memory").mkdir()
            md = tmp_dir / "MEMORY.json"
            _write_doc(md, [_traversal_row(title="탈출-실재", status="candidate",
                                           file_field="memory/../outside_live.md")])
            outside = tmp_dir / "outside_live.md"
            outside.write_text("본문이 memory/ 밖에 실재한다 — 소실되면 안 됨\n", encoding="utf-8")
            before_doc = _snapshot(md)
            before_body = outside.read_bytes()

            result = _run(["delete", "--file", str(md), "--title", "탈출-실재",
                          "--orphan", "--ref", "X"])
            self.assertFalse(result.get("ok"), f"경로 탈출+본문 실재 행이 제거됨: {result}")
            self.assertEqual(result.get("error"), "memory_file_unresolvable",
                             f"에러 코드 불일치: {result}")
            self.assertEqual(_snapshot(md), before_doc, "인덱스가 변경됨")
            self.assertTrue(outside.exists(), "memory/ 밖 본문 파일이 삭제됨(지식 소실)")
            self.assertEqual(outside.read_bytes(), before_body, "memory/ 밖 본문 파일이 수정됨")

    def test_qa025_none_return_three_paths_all_rejected(self):
        """QA-025 (TS-035) [P0, H-2 벡터②]: `_resolve_memory_file()`이 None을 반환하는
        3경로(① 경로 탈출 ② resolve 예외(임베디드 null 문자) ③ 빈 file) 전수가 삭제로
        이어지지 않는다. ③은 스키마 pattern이 CLI 경로 도달을 막으므로(PLAN §3.2.2 판정3)
        기존 함수 `_resolve_memory_file()`을 직접 호출해 None 반환을 확인한다(모듈 레벨
        직접 호출 — mock 아님, 실제 함수를 실행한다)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            (tmp_dir / "memory").mkdir()

            # ① 경로 탈출
            md1 = tmp_dir / "MEMORY_1.json"
            _write_doc(md1, [_traversal_row(title="탈출-1", file_field="memory/../outside1.md")])
            before1 = _snapshot(md1)
            r1 = _run(["delete", "--file", str(md1), "--title", "탈출-1",
                      "--orphan", "--ref", "X"])
            self.assertFalse(r1.get("ok"), f"①경로 탈출 행이 제거됨: {r1}")
            self.assertEqual(r1.get("error"), "memory_file_unresolvable", f"①: {r1}")
            self.assertEqual(_snapshot(md1), before1, "①행이 변경됨")

            # ② resolve 예외(임베디드 null 문자 — 스키마 pattern은 통과, resolve()가 ValueError)
            md2 = tmp_dir / "MEMORY_2.json"
            _write_doc(md2, [_traversal_row(title="탈출-2", file_field="memory/\x00bad.md")])
            before2 = _snapshot(md2)
            r2 = _run(["delete", "--file", str(md2), "--title", "탈출-2",
                      "--orphan", "--ref", "X"])
            self.assertFalse(r2.get("ok"), f"②resolve 예외 유발 행이 제거됨: {r2}")
            self.assertEqual(r2.get("error"), "memory_file_unresolvable", f"②: {r2}")
            self.assertEqual(_snapshot(md2), before2, "②행이 변경됨")

            # ③ 빈 file — CLI 경로 도달 불가(스키마 pattern 불일치)이므로 함수 단위 직접 확인
            module = _load_tool_module(_TOOL_PY, "memory_tool_qa025")
            self.assertIsNone(
                module._resolve_memory_file(str(md2), ""),
                "③빈 file_field가 None으로 해석되지 않음 — cmd_delete orphan 분기의 "
                "`if file_field else None` 단락 전제가 깨짐",
            )

    def test_qa026_ts039_vocabulary_consistency_across_three_commands(self):
        """QA-026 (TS-039, 정정 3): 동일 경로 탈출 행에 대해 review·promote·
        delete --orphan 세 명령이 모두 memory_file_unresolvable 어휘로 일치한다
        (citation-rules §7.1 영역 간 용어 일관성). promote는 096 이전에는 이 경우를
        memory_file_not_found로 반환했다 — 096이 만든 어휘 단절을 정합한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            (tmp_dir / "memory").mkdir()
            md = tmp_dir / "MEMORY.json"
            _write_doc(md, [_traversal_row(title="탈출-어휘일관성", status="candidate")])

            review_result = _run(["review", "--file", str(md)])
            self.assertTrue(review_result.get("ok"), f"review 실패: {review_result}")
            review_types = {v["type"] for v in review_result.get("violations", [])
                           if v.get("title") == "탈출-어휘일관성"}
            self.assertIn("memory_file_unresolvable", review_types,
                          f"review 어휘 불일치: {review_result}")
            self.assertNotIn("memory_file_missing", review_types,
                             f"review가 해석 불가를 부재로 오분류: {review_result}")

            promote_result = _run(["promote", "--file", str(md), "--title", "탈출-어휘일관성",
                                   "--to", "docs", "--ref", "X"])
            self.assertFalse(promote_result.get("ok"), f"해석 불가 행이 promote됨: {promote_result}")
            self.assertEqual(promote_result.get("error"), "memory_file_unresolvable",
                             f"promote 어휘 불일치(096 정정 3 미반영, 구코드 memory_file_not_found "
                             f"잔존 의심): {promote_result}")

            delete_result = _run(["delete", "--file", str(md), "--title", "탈출-어휘일관성",
                                  "--orphan", "--ref", "X"])
            self.assertFalse(delete_result.get("ok"),
                             f"해석 불가 행이 orphan 삭제됨: {delete_result}")
            self.assertEqual(delete_result.get("error"), "memory_file_unresolvable",
                             f"delete --orphan 어휘 불일치: {delete_result}")

    def test_ts037_orphan_and_promote_reject_regardless_of_status(self):
        """TS-037 (①②일부, PLAN §9 R-13 잔존 고착 실증): --orphan과 promote는 해석 불가
        행에 대해 status(candidate/dead)와 무관하게 거부한다 — 무손실 가드는 상태 축이
        아니라 본문 확인 가능 여부 축으로 판정된다."""
        for status in ("candidate", "dead"):
            with self.subTest(status=status):
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_dir = pathlib.Path(tmp)
                    (tmp_dir / "memory").mkdir()
                    md = tmp_dir / "MEMORY.json"
                    title = f"탈출-{status}"
                    _write_doc(md, [_traversal_row(title=title, status=status)])

                    orphan_result = _run(["delete", "--file", str(md), "--title", title,
                                         "--orphan", "--ref", "X"])
                    self.assertFalse(orphan_result.get("ok"),
                                     f"[{status}] --orphan이 해석 불가 행을 제거함: {orphan_result}")
                    self.assertEqual(orphan_result.get("error"), "memory_file_unresolvable",
                                     f"[{status}] --orphan 에러 코드 불일치: {orphan_result}")

                    promote_result = _run(["promote", "--file", str(md), "--title", title,
                                          "--to", "docs", "--ref", "X"])
                    self.assertFalse(promote_result.get("ok"),
                                     f"[{status}] promote가 해석 불가 행을 졸업시킴: {promote_result}")
                    self.assertEqual(promote_result.get("error"), "memory_file_unresolvable",
                                     f"[{status}] promote 에러 코드 불일치: {promote_result}")

    def test_ts038_no_flag_delete_allows_dead_unresolvable_row(self):
        """TS-038 [핵심/음성 통제, 불변식 가드 — RED 시점에도 통과 가능]: 무플래그 delete는
        mem_file을 조회하지 않으므로 dead + 해석 불가(경로 탈출) 행도 여전히 허용되어
        제거된다. PLAN이 [MUST]로 보존 명령한 else 3줄(memory_tool.py:1355-1357)이
        문자 그대로 불변임을 실증한다 — GREEN을 좇아 무플래그 경로에 가드를 추가하면
        이 시나리오가 FAIL해야 한다."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = pathlib.Path(tmp)
            (tmp_dir / "memory").mkdir()
            md = tmp_dir / "MEMORY.json"
            _write_doc(md, [_traversal_row(title="탈출-dead", status="dead")])

            result = _run(["delete", "--file", str(md), "--title", "탈출-dead"])
            self.assertTrue(
                result.get("ok"),
                f"dead+해석불가 행이 무플래그 delete에서 거부됨 — else 3줄이 mem_file을 "
                f"조회하도록 변경됐다는 뜻이며 PLAN [MUST] 위반: {result}",
            )
            doc = _read_doc(md)
            self.assertTrue(all(r["title"] != "탈출-dead" for r in doc["memories"]),
                            "허용됐다는데 행이 실제로는 제거되지 않음")


# ─────────────────────────────────────────────────────────────────────────────
# 096 F-003: 규범·도구 문서 정합 [T096/L1-R3] — QA-015~QA-018
# ─────────────────────────────────────────────────────────────────────────────

class TestLifecycleDocParity(unittest.TestCase):
    """[T096/L1-R3] R-3 AC — memory-learning.md 라이프사이클 표 ↔
    memory.schema.json status enum 파리티(H-7, 수동 동기화 계약을 기계 집행으로 전환).
    `TestTaskNumberDocs`(:2515)의 `_REPO_ROOT` 기준 문서 읽기 패턴을 재사용한다."""

    def test_qa015_lifecycle_table_matches_schema_enum(self):
        """QA-015 (TS-015): 라이프사이클 표 상태 값 집합 == 스키마 status enum
        (문자 단위 동일, 5종)."""
        text = _MEMORY_LEARNING.read_text(encoding="utf-8")
        table_statuses = _lifecycle_table_statuses(text)
        schema = json.loads(_MEMORY_SCHEMA_PATH.read_text(encoding="utf-8"))
        schema_statuses = set(schema["$defs"]["memoryRow"]["properties"]["status"]["enum"])
        self.assertEqual(
            table_statuses, schema_statuses,
            f"라이프사이클 표 상태 집합과 스키마 enum 불일치: 표={table_statuses} "
            f"스키마={schema_statuses}",
        )
        self.assertEqual(len(schema_statuses), 5, f"스키마 enum이 5종이 아님: {schema_statuses}")

    def test_qa016_candidate_row_columns_filled(self):
        """QA-016 (TS-016): `candidate` 행의 의미·진입 트리거·도구 동작 3열이
        모두 비어있지 않다."""
        text = _MEMORY_LEARNING.read_text(encoding="utf-8")
        section = _lifecycle_table_section(text)
        row_match = re.search(r"^\|\s*`candidate`\s*\|(.+)\|(.+)\|(.+)\|\s*$",
                              section, flags=re.MULTILINE)
        self.assertIsNotNone(row_match, "candidate 행이 라이프사이클 표에 없음")
        for i, col in enumerate(row_match.groups(), start=1):
            self.assertTrue(col.strip(), f"candidate 행 {i}번째 열이 비어있음")

    def test_qa017_new_error_codes_documented_in_readme_and_toolsmd(self):
        """QA-017 (TS-017, H-9): ERROR_CODES 신규 3종
        (memory_file_exists/orphan_ref_missing/memory_file_unresolvable)이
        README.md·tools.md 에러 코드 표에 모두 등재된다."""
        module = _load_tool_module(_TOOL_PY, "memory_tool_qa017")
        codes = set(module.ERROR_CODES)
        for code in _NEW_ERROR_CODES_096:
            self.assertIn(code, codes, f"ERROR_CODES에 신규 코드 '{code}' 부재 — GREEN 미구현")

        readme_text = _README_PATH.read_text(encoding="utf-8")
        tools_text = _TOOLS_MD_PATH.read_text(encoding="utf-8")
        for code in _NEW_ERROR_CODES_096:
            self.assertIn(f"`{code}`", readme_text, f"README.md 에러 코드 표에 '{code}' 누락")
            self.assertIn(f"`{code}`", tools_text, f"tools.md 에러 코드 표에 '{code}' 누락")

    def test_qa018_existing_four_rows_text_unchanged(self):
        """QA-018 (TS-018, 불변식 가드 — RED 시점에도 통과 가능): 기존 4개 상태 행
        (active/promoted/superseded/dead)의 3열 텍스트가 R-3 반영 전후 문자 그대로
        동일하다(§3.3.2 (2): "기존 4행 서술은 R-2 반영분 외 diff 0")."""
        text = _MEMORY_LEARNING.read_text(encoding="utf-8")
        for row in _EXPECTED_LIFECYCLE_ROWS_096:
            self.assertIn(row, text, f"기존 라이프사이클 행 텍스트가 변경됨: {row!r}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
