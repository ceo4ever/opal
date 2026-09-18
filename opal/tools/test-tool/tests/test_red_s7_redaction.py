"""
@header {
  "module": "test_red_s7_redaction",
  "task": "127-260912-oppl-E2E-하네스-구현",
  "layer": "test",
  "domain": "opal-tools",
  "description": "S-7: (a) Authorization/Cookie/Set-Cookie 헤더 + query secret을 포함한 실패 run의 증적 디렉터리 전체를 문자열 검색해도 원문 비밀값이 없어야 한다. (b) redaction 단계 자체가 실패하도록 주입하면 원문/부분 증적이 디스크에 남지 않고 run이 infra_error로 판정돼야 한다. (c) lib/e2e/redaction.py·lib/e2e/evidence.py가 CONTRACT.md §A.12대로 존재하고, 증적 쓰기가 이 관문을 우회 없이 거치는지 공개 인터페이스로 검증한다.",
  "scenarios": ["S-7"],
  "exports": ["TestRedactionModulesExist", "TestRedactionOnFailedRun", "TestRedactionFailureInfraError"]
}

W-3가 CONTRACT.md §A.12("모든 증적 쓰기는 lib/e2e/evidence.py를 거치고, evidence.py는
저장 직전 반드시 lib/e2e/redaction.py를 통과시킨다")에 따라 lib/e2e/redaction.py·
lib/e2e/evidence.py를 신설했다. 두 모듈의 존재 자체가 계약이므로(§A.12), 이 파일은
더 이상 "모듈 부재"를 단언하지 않는다 — 대신 (1) 모듈이 실제로 import되고, (2)
`EvidenceWriter`의 공개 쓰기 메서드(write_json/write_jsonl/write_text/seal_server_log)
전부가 저장 직전 redaction을 거쳐 원문 비밀값을 남기지 않으며, (3) redaction을
우회해 원문을 그대로 저장하는 별도의 공개 경로가 없음을 검증한다.

이전에 이 파일에 `sys.path.insert`가 없어(s5·s6에는 있었다) 단독 실행 시 `lib`
패키지를 import할 수 없었고, 그 결과 "모듈이 없다"가 아니라 "import 경로가 없다"를
증명하고 있었다. 아래에서 s5·s6과 동일하게 `_TOOL_DIR`을 `sys.path`에 추가해
실행 순서·단독 실행 여부에 좌우되지 않게 고쳤다.
"""
from __future__ import annotations

import importlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
_TEST_TOOL_PY = _TOOL_DIR / "test_tool.py"
_SOURCE_ROOT = _TOOL_DIR.parent.parent.parent
_TASK_PATH = _SOURCE_ROOT / "tasks" / "127-260912-oppl-E2E-하네스-구현"
_SCENARIO_ID = "S-7"
_PYTHON = sys.executable
sys.path.insert(0, str(_TOOL_DIR))

_SECRET_HEADER_VALUE = "Bearer sk-super-secret-token-ABC123"
_SECRET_COOKIE_VALUE = "session=sekrit-cookie-value-XYZ789"
_SECRET_QUERY_VALUE = "api_key=leak-me-not-QWERTY99"

# CONTRACT.md §A.1/§A.2/§A.4/§A.5/§A.6이 공통 필수로 요구하는 증적 5종의 산출 파일.
# "증적이 없어서 유출도 없음"으로 통과할 수 없도록, 먼저 이 5종이 실제로 존재함을
# 단언한 뒤에만 마스킹 검사로 넘어간다. 하나라도 없으면 즉시 실패한다.
_REQUIRED_EVIDENCE_FILES = (
    "run.json",          # metadata
    "server/backend.log",  # server_log (frontend/backend 로그 중 backend를 대표로 확인)
    "actions.jsonl",     # action_log
    "assertions.json",   # assertion evidence (expected/actual)
    "cleanup.json",      # cleanup
)


def _assert_required_evidence_present(testcase, artifact_root: pathlib.Path):
    missing = [name for name in _REQUIRED_EVIDENCE_FILES if not (artifact_root / name).is_file()]
    testcase.assertEqual(
        missing, [],
        f"required evidence files missing under {artifact_root} — an empty/partial evidence "
        f"directory must not be treated as 'no leak' (RED target for S-7): {missing}",
    )


class TestRedactionModulesExist(unittest.TestCase):
    """S-7 전제조건(CONTRACT.md §A.12): redaction/evidence 모듈이 실제로 존재하고,
    증적 쓰기가 그 관문을 우회 없이 거쳐야 한다."""

    def test_redaction_module_importable(self):
        module = importlib.import_module("lib.e2e.redaction")
        self.assertTrue(
            hasattr(module, "redact_text") and hasattr(module, "redact_value"),
            "lib.e2e.redaction must expose the §A.12 masking entry points",
        )

    def test_evidence_module_importable(self):
        module = importlib.import_module("lib.e2e.evidence")
        self.assertTrue(
            hasattr(module, "EvidenceWriter"),
            "lib.e2e.evidence must expose the §A.12 single evidence-writing gate",
        )

    def test_evidence_writer_has_no_public_write_path_bypassing_redaction(self):
        """공개 쓰기 API 전부가 redaction을 거치는지 — 우회 경로가 없는지 검증한다.

        `EvidenceWriter`의 공개 쓰기 메서드는 write_json/write_jsonl/write_text/
        seal_server_log 4개뿐이어야 한다. 그 이상의 공개 쓰기 메서드가 있다면 그중
        일부가 §A.12 관문(redaction)을 거치지 않을 위험 표면이 생긴다.
        """
        evidence = importlib.import_module("lib.e2e.evidence")
        writer_cls = evidence.EvidenceWriter
        public_write_methods = {
            name
            for name in dir(writer_cls)
            if not name.startswith("_")
            and (name.startswith("write") or name.startswith("seal"))
            and callable(getattr(writer_cls, name))
        }
        self.assertEqual(
            public_write_methods,
            {"write_json", "write_jsonl", "write_text", "seal_server_log"},
            "EvidenceWriter must expose exactly the known §A.12-gated write methods — "
            "any additional public write method is a potential redaction bypass",
        )

    def test_evidence_writer_masks_secrets_through_the_single_gate(self):
        """§A.12 관문 동작 자체를 공개 인터페이스(write_json/write_text)로 검증한다.

        원문 비밀값을 담은 payload를 각 공개 쓰기 메서드로 저장했을 때, 디스크에 남는
        파일에는 원문이 전혀 없고 마스킹 표기만 남아야 한다 — evidence.py가 저장 직전
        반드시 redaction.py를 통과시킨다는 §A.12를 우회 없이 만족함을 증명한다.
        """
        evidence = importlib.import_module("lib.e2e.evidence")
        with tempfile.TemporaryDirectory() as artifact_dir:
            writer = evidence.EvidenceWriter(artifact_dir, run_id="s7-gate-check")

            writer.write_json(
                "gate-check.json",
                {
                    "headers": {"Authorization": _SECRET_HEADER_VALUE, "Cookie": _SECRET_COOKIE_VALUE},
                    "url": f"http://x?{_SECRET_QUERY_VALUE}",
                },
                kind="assertion_evidence",
            )
            writer.write_jsonl(
                "gate-check.jsonl",
                [{"headers": {"Set-Cookie": _SECRET_COOKIE_VALUE}}],
                kind="action_log",
            )
            writer.write_text(
                "gate-check.log",
                f"Authorization: {_SECRET_HEADER_VALUE}\nurl=http://x?{_SECRET_QUERY_VALUE}",
                kind="server_log",
            )

            artifact_root = pathlib.Path(artifact_dir)
            joined = "\n".join(
                path.read_text(encoding="utf-8", errors="ignore")
                for path in artifact_root.rglob("*")
                if path.is_file()
            )
            self.assertNotIn(_SECRET_HEADER_VALUE, joined, "Authorization value must never reach disk unmasked")
            self.assertNotIn(_SECRET_COOKIE_VALUE, joined, "Cookie/Set-Cookie value must never reach disk unmasked")
            self.assertNotIn("leak-me-not-QWERTY99", joined, "query secret value must never reach disk unmasked")
            redaction_module = importlib.import_module("lib.e2e.redaction")
            self.assertIn(
                redaction_module.MASK,
                joined,
                "masked marker must be present where secrets were redacted",
            )


class TestRedactionOnFailedRun(unittest.TestCase):
    """S-7(a): 실패 run의 증적 디렉터리 전체에 원문 비밀값이 없어야 한다."""

    def test_no_raw_secret_in_evidence_directory(self):
        with tempfile.TemporaryDirectory() as artifact_dir:
            import os
            env = os.environ.copy()
            env["OPAL_E2E_ARTIFACT_DIR"] = artifact_dir
            # 시나리오가 비밀 헤더/쿼리를 포함한 요청을 발생시키도록 의도된 인자 —
            # 실제로는 'e2e run' 서브명령이 없어 이 지점에서 RED로 실패한다.
            proc = subprocess.run(
                [
                    _PYTHON, str(_TEST_TOOL_PY),
                    "e2e", "run",
                    "--scenario", _SCENARIO_ID,
                    "--task-path", str(_TASK_PATH),
                    "--target", "source-worktree",
                    "--worktree-root", str(_SOURCE_ROOT),
                ],
                capture_output=True,
                text=True,
                env=env,
                timeout=60,
            )
            self.assertNotEqual(
                proc.returncode, 2,
                f"'e2e run' subcommand missing (RED target): {proc.stderr!r}",
            )

            artifact_root = pathlib.Path(artifact_dir)
            # 강화: "아무 증적도 없어서 유출도 없음"은 통과가 아니다. 공통 필수 증적
            # 5종이 실제로 존재함을 먼저 단언한다 — 비어 있으면 여기서 실패한다.
            _assert_required_evidence_present(self, artifact_root)

            all_text = []
            for path in artifact_root.rglob("*"):
                if path.is_file():
                    try:
                        all_text.append(path.read_text(encoding="utf-8", errors="ignore"))
                    except OSError:
                        pass
            joined = "\n".join(all_text)
            self.assertNotIn(_SECRET_HEADER_VALUE, joined, "raw Authorization value leaked into evidence")
            self.assertNotIn(_SECRET_COOKIE_VALUE, joined, "raw Cookie/Set-Cookie value leaked into evidence")
            self.assertNotIn(_SECRET_QUERY_VALUE, joined, "raw query secret leaked into evidence")


class TestRedactionFailureInfraError(unittest.TestCase):
    """S-7(b): redaction 단계 실패 주입 시 원문/부분 증적이 남지 않고 infra_error가 된다."""

    def test_redaction_failure_leaves_no_partial_evidence_and_is_infra_error(self):
        with tempfile.TemporaryDirectory() as artifact_dir:
            import os
            env = os.environ.copy()
            env["OPAL_E2E_ARTIFACT_DIR"] = artifact_dir
            # 증적 경로 쓰기 권한을 박탈해 redaction/evidence 저장 단계를 실패시킨다.
            artifact_root = pathlib.Path(artifact_dir)
            artifact_root.chmod(0o500)
            try:
                proc = subprocess.run(
                    [
                        _PYTHON, str(_TEST_TOOL_PY),
                        "e2e", "run",
                        "--scenario", _SCENARIO_ID,
                        "--task-path", str(_TASK_PATH),
                        "--target", "source-worktree",
                        "--worktree-root", str(_SOURCE_ROOT),
                    ],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=60,
                )
            finally:
                artifact_root.chmod(0o700)

            self.assertNotEqual(
                proc.returncode, 2,
                f"'e2e run' subcommand missing (RED target): {proc.stderr!r}",
            )
            data = json.loads(proc.stdout)
            self.assertEqual(
                data.get("status"), "infra_error",
                f"redaction failure must yield infra_error: {data}",
            )
            leftover_files = [p for p in artifact_root.rglob("*") if p.is_file()]
            self.assertEqual(
                leftover_files, [],
                f"no partial/raw evidence file may remain on disk after redaction failure: {leftover_files}",
            )


if __name__ == "__main__":
    unittest.main()
