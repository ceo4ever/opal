"""
@header {
  "module": "test_improve_tool",
  "task": "058",
  "layer": "test",
  "domain": "opal-tools",
  "description": "improve-tool record 서브명령 행위 계약 RED-first 테스트 (058 TEST-SCENARIO.md S-1~S-5 대응). RED 상태(미구현, run.sh/improve_tool.py 부재) — 전부 FAIL 예상. GREEN 전환은 EXECUTE 구현 워커(op-dev-execute) 담당(작성자≠구현자, red-first.md §2).",
  "scenarios": ["S-1", "S-2", "S-3", "S-4", "S-5"],
  "exports": [
    "TestJsonContractThreePaths",
    "TestFwInboxSelfContainedEntry",
    "TestLocalScopeMemoryDelegation",
    "TestLocalScopeGracefulSkip",
    "TestRecordArgumentValidation"
  ]
}

[T058/L1] improve-tool `record` 서브명령 행위 계약 — RED-first TDD
검증 대상: opal/tools/improve-tool/run.sh 의 공개 인터페이스(exit code + stdout JSON)만 단언.
내부 함수/private 결합 금지(red-first.md §4) — subprocess 실호출만 사용, mock/patch/MagicMock 금지.
실 fixture만 사용: tmp 임시 프로젝트(.opal/MEMORY.md 유무) + 임시 fw-inbox 디렉토리.
실제 `~/.opal/fw-inbox`·소유자 프로젝트 MEMORY.md 오염 금지 — 모든 fw 경로 테스트는
환경변수 `IMPROVE_FW_INBOX` 로 임시 디렉토리를 주입한다(GREEN 구현이 이 env를 최우선
목적지로 사용해야 하는 계약 — 미설정 시에만 기본값 `~/.opal/fw-inbox` 사용).

PLAN.md §3.1.2 근거 (F-001 improve_tool.py 서브명령 스펙):
  - record --scope {local|fw}(req) --title(req) --body --situation --source-task --project-root
  - scope local: <project-root>/.opal/MEMORY.md 존재 시 memory-tool append 위임
    (--kind memory --type improvement --status candidate), 부재 시
    {"ok":true,"scope":"local","skipped":true,"reason":"no MEMORY.md"} no-op.
  - scope fw: ~/.opal/fw-inbox/{YYYYMMDD-HHmmss}-{host}-{slug}.md 결정론적 write.
    frontmatter 필수키(H-8): host/project/situation/created.
  - JSON 계약(H-4): 모든 경로 stdout에 "ok" 키 보장. 실패는 크래시/스택트레이스 없이
    {"ok":false,"error":"..."}.

주의(GREEN 구현자에게): PLAN이 지정한 memory-tool 위임 인자는 `--type improvement
--status candidate` 이나, 현재 opal/tools/memory-tool/memory_tool.py의
VALID_TYPES={project,architecture,feedback,preferences,issues,task} /
VALID_STATUSES={active,promoted,superseded,dead} 에는 improvement/candidate가
없다. GREEN은 memory_tool.py enum 확장 여부를 PM에 확인해야 할 수 있다(본 RED
테스트는 PLAN 명세를 있는 그대로 인코딩한다 — enum 불일치는 GREEN 단계 리스크로 별도 보고).
"""

import json
import os
import pathlib
import shutil
import socket
import subprocess
import tempfile
import unittest

# improve-tool run.sh 위치 (미구현 — RED 단계에서는 파일 자체가 부재)
_TOOL_DIR = pathlib.Path(__file__).resolve().parent.parent
_RUN_SH = _TOOL_DIR / "run.sh"

_VALID_MEMORY_MD = """# 테스트 프로젝트 Memory Index

> 최종 갱신: 2026-07-17
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
"""


# ─────────────────────────────────────────────────────────────────────────────
# 공통 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _run(args, fw_inbox_dir=None):
    """run.sh를 subprocess로 실행하여 (returncode, stdout_text, stderr_text, parsed_json) 반환.
    run.sh 부재 시 bash가 자체 오류를 내며 비정상 종료한다 — 이 역시 RED 증거다.
    fw_inbox_dir가 주어지면 IMPROVE_FW_INBOX 환경변수로 주입한다(실 ~/.opal/fw-inbox 오염 금지).
    """
    cmd = ["bash", str(_RUN_SH)] + args
    env = os.environ.copy()
    if fw_inbox_dir is not None:
        env["IMPROVE_FW_INBOX"] = str(fw_inbox_dir)
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, result.stderr, data


def _record(scope=None, title=None, body=None, situation=None, source_task=None,
            project_root=None, fw_inbox_dir=None):
    args = ["record"]
    if scope is not None:
        args += ["--scope", scope]
    if title is not None:
        args += ["--title", title]
    if body is not None:
        args += ["--body", body]
    if situation is not None:
        args += ["--situation", situation]
    if source_task is not None:
        args += ["--source-task", source_task]
    if project_root is not None:
        args += ["--project-root", str(project_root)]
    return _run(args, fw_inbox_dir=fw_inbox_dir)


def _make_project_with_memory(root: pathlib.Path) -> pathlib.Path:
    """proj-A 유형 — .opal/MEMORY.md가 유효 마커를 갖춘 상태로 존재."""
    opal_dir = root / ".opal"
    opal_dir.mkdir(parents=True, exist_ok=True)
    memory_md = opal_dir / "MEMORY.md"
    memory_md.write_text(_VALID_MEMORY_MD, encoding="utf-8")
    return memory_md


def _make_project_without_memory(root: pathlib.Path) -> pathlib.Path:
    """proj-B 유형 — 빈 디렉토리, .opal/MEMORY.md 부재."""
    root.mkdir(parents=True, exist_ok=True)
    return root


def _parse_frontmatter(text: str) -> dict:
    """파일 상단 --- ... --- 블록을 단순 key: value 딕셔너리로 파싱(자기완결 md 스키마 검증용)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fm = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


class BaseImproveTestCase(unittest.TestCase):
    """임시 프로젝트(proj-A/proj-B)·임시 fw-inbox 공통 베이스.
    실 파일 생성·재읽기 — mock 금지(red-first.md §4)."""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.fw_inbox = self.tmpdir / "fw-inbox"
        self.fw_inbox.mkdir()
        self.proj_a = self.tmpdir / "proj-A"
        _make_project_with_memory(self.proj_a)
        self.proj_b = self.tmpdir / "proj-B"
        _make_project_without_memory(self.proj_b)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _memory_md_text(self) -> str:
        return (self.proj_a / ".opal" / "MEMORY.md").read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# S-1: improve-tool record 3경로(성공/실패/no-op) JSON "ok" 계약 [T058/L1-R3]
# ─────────────────────────────────────────────────────────────────────────────

class TestJsonContractThreePaths(BaseImproveTestCase):
    """[T058/L1-R3] improve-tool record 3경로 JSON "ok" 계약 — S-1 (H-4)"""

    def test_record_fw_success_has_ok_true(self):
        """성공 경로: record --scope fw. Then: stdout JSON 파싱 성공 + "ok":true."""
        code, stdout, stderr, data = _record(
            scope="fw", title="FW 개선 제안 테스트", situation="retrospective",
            project_root=self.proj_a, fw_inbox_dir=self.fw_inbox,
        )
        self.assertNotIn("_raw", data, f"stdout이 유효 JSON이 아님: {stdout!r}")
        self.assertIn("ok", data)
        self.assertTrue(data.get("ok"))
        self.assertEqual(code, 0)

    def test_record_invalid_scope_has_ok_false(self):
        """실패 경로: record --scope wrong. Then: stdout JSON 파싱 성공 + "ok":false."""
        code, stdout, stderr, data = _record(
            scope="wrong", title="T", fw_inbox_dir=self.fw_inbox,
        )
        self.assertNotIn("_raw", data, f"stdout이 유효 JSON이 아님: {stdout!r}")
        self.assertIn("ok", data)
        self.assertFalse(data.get("ok"))

    def test_record_local_noop_has_ok_true_and_skipped(self):
        """no-op 경로: record --scope local (proj-B, MEMORY.md 부재).
        Then: stdout JSON 파싱 성공 + "ok":true + "skipped":true."""
        code, stdout, stderr, data = _record(
            scope="local", title="T", project_root=self.proj_b, fw_inbox_dir=self.fw_inbox,
        )
        self.assertNotIn("_raw", data, f"stdout이 유효 JSON이 아님: {stdout!r}")
        self.assertIn("ok", data)
        self.assertTrue(data.get("ok"))
        self.assertTrue(data.get("skipped"))
        self.assertEqual(code, 0)


# ─────────────────────────────────────────────────────────────────────────────
# S-2: record --scope fw → fw-inbox 자기완결 항목 생성 [T058/L1-R4]
# ─────────────────────────────────────────────────────────────────────────────

class TestFwInboxSelfContainedEntry(BaseImproveTestCase):
    """[T058/L1-R4] record --scope fw → fw-inbox 자기완결 항목 생성 — S-2 (H-8)"""

    def test_record_fw_creates_exactly_one_md_file(self):
        """Given: fw-inbox(임시) 비어있음. When: record --scope fw 1회.
        Then: *.md 정확히 1건 신규 생성."""
        before = list(self.fw_inbox.glob("*.md"))
        self.assertEqual(len(before), 0)

        code, stdout, stderr, data = _record(
            scope="fw", title="FW 개선 제안", body="본문 요약",
            situation="retrospective", project_root=self.proj_a,
            fw_inbox_dir=self.fw_inbox,
        )
        self.assertEqual(code, 0, f"stderr={stderr}")

        after = list(self.fw_inbox.glob("*.md"))
        self.assertEqual(len(after), 1, "fw-inbox에 정확히 1건의 *.md가 생성되어야 한다")

    def test_fw_entry_frontmatter_has_required_keys(self):
        """Then: frontmatter에 host·project·situation·created 4키 전부 존재(H-8 자기완결성)."""
        code, stdout, stderr, data = _record(
            scope="fw", title="FW 개선 제안", situation="retrospective",
            project_root=self.proj_a, fw_inbox_dir=self.fw_inbox,
        )
        self.assertEqual(code, 0, f"stderr={stderr}")

        entries = list(self.fw_inbox.glob("*.md"))
        self.assertEqual(len(entries), 1)
        fm = _parse_frontmatter(entries[0].read_text(encoding="utf-8"))
        for key in ("host", "project", "situation", "created"):
            self.assertIn(key, fm, f"frontmatter에 {key} 키 누락")
            self.assertTrue(fm[key], f"frontmatter {key} 값이 비어있음")
        self.assertEqual(fm.get("host"), socket.gethostname())
        self.assertEqual(fm.get("situation"), "retrospective")

    def test_record_fw_json_contract_has_scope_and_path(self):
        """Then: {"ok":true,"scope":"fw","path":...} 반환, path는 생성된 파일을 가리킴."""
        code, stdout, stderr, data = _record(
            scope="fw", title="FW 개선 제안", situation="retrospective",
            project_root=self.proj_a, fw_inbox_dir=self.fw_inbox,
        )
        self.assertEqual(code, 0, f"stderr={stderr}")
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("scope"), "fw")
        self.assertIn("path", data)

        entries = list(self.fw_inbox.glob("*.md"))
        self.assertEqual(len(entries), 1)
        # 심볼릭 링크(tmp 경로 별칭) 이슈 회피 — 파일명·실존 여부로만 대조
        returned_path = pathlib.Path(data["path"])
        self.assertTrue(returned_path.exists(), f"반환된 path가 실존하지 않음: {returned_path}")
        self.assertEqual(returned_path.name, entries[0].name)


# ─────────────────────────────────────────────────────────────────────────────
# S-3: record --scope local → memory-tool 위임 (MEMORY.md 존재) [T058/L1-R3b]
# ─────────────────────────────────────────────────────────────────────────────

class TestLocalScopeMemoryDelegation(BaseImproveTestCase):
    """[T058/L1-R3b] record --scope local → memory-tool 위임 (MEMORY.md 존재) — S-3 (H-2)"""

    def test_record_local_appends_improvement_candidate_row(self):
        """Given: proj-A/.opal/MEMORY.md 존재. When: record --scope local.
        Then: MEMORY.md에 type=improvement,status=candidate 항목 1건 append(실 memory-tool 위임)."""
        before = self._memory_md_text()
        self.assertNotIn("improvement", before)

        code, stdout, stderr, data = _record(
            scope="local", title="로컬 개선 후보 T", body="80자 이내 요약 텍스트",
            project_root=self.proj_a, fw_inbox_dir=self.fw_inbox,
        )
        self.assertEqual(code, 0, f"stderr={stderr}")
        self.assertTrue(data.get("ok"))

        after = self._memory_md_text()
        self.assertIn("로컬 개선 후보 T", after, "MEMORY.md에 제목 행이 append되어야 한다")
        self.assertIn("improvement", after, "type=improvement 컬럼 값이 존재해야 한다")
        self.assertIn("candidate", after, "status=candidate 컬럼 값이 존재해야 한다")

    def test_record_local_ok_contract_scope_local(self):
        """Then: {"ok":true,"scope":"local"} 반환."""
        code, stdout, stderr, data = _record(
            scope="local", title="T", project_root=self.proj_a, fw_inbox_dir=self.fw_inbox,
        )
        self.assertEqual(code, 0, f"stderr={stderr}")
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("scope"), "local")

    def test_record_local_does_not_write_fw_inbox(self):
        """분기 격리(H-2) — local scope 호출은 fw-inbox에 write가 없어야 한다.
        (호출 자체가 성공해야 검증 의미가 있다 — 미구현 상태에서 공허하게 통과하지 않도록
        code==0 선행 검증으로 RED 증거를 확보한다.)"""
        before = list(self.fw_inbox.glob("*.md"))
        self.assertEqual(len(before), 0)

        code, stdout, stderr, data = _record(
            scope="local", title="T", project_root=self.proj_a, fw_inbox_dir=self.fw_inbox,
        )
        self.assertEqual(code, 0, f"local record 호출 자체가 성공해야 분기 격리 검증이 의미있다. stderr={stderr}")

        after = list(self.fw_inbox.glob("*.md"))
        self.assertEqual(len(after), 0, "local scope 호출이 fw-inbox에 파일을 생성해서는 안 된다(scope 오분류 방지)")


# ─────────────────────────────────────────────────────────────────────────────
# S-4: record --scope local graceful skip (MEMORY.md 부재) [T058/L1-R4b]
# ─────────────────────────────────────────────────────────────────────────────

class TestLocalScopeGracefulSkip(BaseImproveTestCase):
    """[T058/L1-R4b] record --scope local graceful skip (MEMORY.md 부재) — S-4 (H-6)"""

    def test_record_local_skip_when_memory_md_absent(self):
        """Given: proj-B(.opal/MEMORY.md 부재). When: record --scope local.
        Then: 예외 전파 없이 {"ok":true,"scope":"local","skipped":true,"reason":"no MEMORY.md"}."""
        self.assertFalse((self.proj_b / ".opal" / "MEMORY.md").exists())

        code, stdout, stderr, data = _record(
            scope="local", title="T", project_root=self.proj_b, fw_inbox_dir=self.fw_inbox,
        )
        self.assertEqual(code, 0, f"no-op은 예외 전파 없이 exit 0이어야 한다. stderr={stderr}")
        self.assertNotIn("Traceback", stderr, "no-op 경로에서 스택트레이스가 노출되면 안 된다")
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("scope"), "local")
        self.assertTrue(data.get("skipped"))
        self.assertEqual(data.get("reason"), "no MEMORY.md")

    def test_record_local_skip_writes_zero_files(self):
        """Then: write 0건 — MEMORY.md 신규 생성 없음 + fw-inbox write 없음.
        (no-op 호출 자체가 ok:true로 성공 응답해야 검증 의미가 있다 — 미구현 상태에서
        공허하게 통과하지 않도록 ok==True 선행 검증으로 RED 증거를 확보한다.)"""
        code, stdout, stderr, data = _record(
            scope="local", title="T", project_root=self.proj_b, fw_inbox_dir=self.fw_inbox,
        )
        self.assertEqual(code, 0, f"no-op 호출 자체가 성공(exit 0)해야 한다. stderr={stderr}")
        self.assertTrue(data.get("ok"), f"no-op 호출은 ok:true여야 한다. data={data}")

        self.assertFalse(
            (self.proj_b / ".opal" / "MEMORY.md").exists(),
            "no-op 경로는 MEMORY.md를 새로 생성해서는 안 된다",
        )
        self.assertEqual(len(list(self.fw_inbox.glob("*.md"))), 0)


# ─────────────────────────────────────────────────────────────────────────────
# S-5: record 인자 오류 경계 (잘못된 scope / 필수 인자 누락) [T058/L1-R3]
# ─────────────────────────────────────────────────────────────────────────────

class TestRecordArgumentValidation(BaseImproveTestCase):
    """[T058/L1-R3] record 인자 오류 경계 — S-5 (H-4)"""

    def _assert_graceful_error(self, code, stdout, stderr, data):
        self.assertNotIn("_raw", data, f"stdout이 유효 JSON이 아님(파싱 실패): stdout={stdout!r}")
        self.assertIn("ok", data)
        self.assertFalse(data.get("ok"))
        self.assertIn("error", data)
        self.assertNotIn("Traceback", stderr, "파이썬 스택트레이스가 stderr에 노출되면 안 된다(크래시 금지)")
        self.assertNotEqual(code, 0, "인자 오류는 비정상 종료가 아닌 명시적 실패 exit code를 반환해야 한다")

    def test_wrong_scope_value_returns_graceful_error(self):
        """When: record --scope wrong --title T. Then: {"ok":false,"error":...} (크래시 아님)."""
        code, stdout, stderr, data = _run(
            ["record", "--scope", "wrong", "--title", "T"], fw_inbox_dir=self.fw_inbox,
        )
        self._assert_graceful_error(code, stdout, stderr, data)

    def test_missing_scope_returns_graceful_error(self):
        """When: record --title T (--scope 누락). Then: {"ok":false,"error":...} (argparse 크래시 아님)."""
        code, stdout, stderr, data = _run(
            ["record", "--title", "T"], fw_inbox_dir=self.fw_inbox,
        )
        self._assert_graceful_error(code, stdout, stderr, data)

    def test_missing_title_returns_graceful_error(self):
        """When: record --scope fw (--title 누락). Then: {"ok":false,"error":...} (argparse 크래시 아님)."""
        code, stdout, stderr, data = _run(
            ["record", "--scope", "fw"], fw_inbox_dir=self.fw_inbox,
        )
        self._assert_graceful_error(code, stdout, stderr, data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
