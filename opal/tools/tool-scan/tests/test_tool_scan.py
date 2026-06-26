"""
@header {
  "module": "test_tool_scan",
  "task": "044",
  "layer": "test",
  "domain": "opal-tools",
  "description": "tool-scan 5서브명령(list/which/usage/resolve/check) + federation(mcps/skills-registry) + 산출물 grep 행위 계약 RED-first 테스트. RED 상태(미구현) — 전부 FAIL 예상. GREEN 전환은 opal-be-agent(Step 3~5) 담당(작성자≠구현자).",
  "scenarios": "TS-001~003, TS-010~012, TS-020~023, TS-030~035, TS-040~041, TS-050~051, TS-060",
  "track": "RED-first (red-first.md §1~§4)",
  "exports": [
    "TestSubcommandsJson",
    "TestManifest",
    "TestUsage",
    "TestResolveAndFederation",
    "TestOutputArtifacts"
  ]
}

[T044] tool-scan 5서브명령 + federation + 산출물 행위 계약 — RED-first TDD
검증 대상: opal/tools/tool-scan/run.sh 의 공개 인터페이스(exit code + stdout JSON)만 단언.
내부 구현/private 결합 금지(red-first.md §4).

stub 전략:
  - unittest.mock/MagicMock/patch 사용 금지 (state-tool/test-tool mock 가드 교훈 — tasks/033/034)
  - 실제 stub 쉘 스크립트 파일을 tests/fixtures/ 또는 tmpdir에 생성
  - 환경변수로 manifest 경로·federation 경로를 주입하여 격리
    TOOL_SCAN_MANIFEST_PATH: 대체 manifest.json 절대 경로 (구현자가 지원해야 함)
    TOOL_SCAN_MCPS_PATH: 대체 mcps.md 절대 경로
    TOOL_SCAN_SKILLS_REGISTRY_PATH: 대체 skills-registry.json 절대 경로
    TOOL_SCAN_HELP_CMD: usage self-help에서 호출할 stub run.sh 절대 경로
    TOOL_SCAN_HELP_VERSION: help_mutable.sh 출력 변경용

TS-033(불파괴): resolve 실행 전후 skills-registry.json byte 해시 동일 단언.
TS-040~060(산출물): 구현 후 AGENT.md/tools.md/harness.md/install-mac.sh 검사 — 현재 RED.
"""

import hashlib
import json
import os
import pathlib
import shutil
import stat
import subprocess
import tempfile
import unittest

# tool-scan run.sh 위치 (산출 예정 — Step 3 구현 전이므로 부재 상태)
_TOOL_DIR = pathlib.Path(__file__).parent.parent
_RUN_SH = _TOOL_DIR / "run.sh"

# 프로젝트 루트 (opal/tools/tool-scan 의 두 상위)
_PROJECT_ROOT = _TOOL_DIR.parent.parent.parent

# 실 federation 소스 경로
_REAL_SKILLS_REGISTRY = _PROJECT_ROOT / "opal" / "core" / "references" / "opal-skills-registry.json"
_REAL_MCPS_MD = _PROJECT_ROOT / "opal" / "core" / "references" / "mcps.md"

# 산출물 경로 (F-005/006/007)
_AGENT_MD = _PROJECT_ROOT / "opal" / "core" / "AGENT.md"
_TOOLS_MD = _PROJECT_ROOT / "opal" / "core" / "references" / "tools.md"
_HARNESS_MD = _PROJECT_ROOT / "opal" / "core" / "references" / "opal-harness.md"
_INSTALL_SH = _PROJECT_ROOT / "scripts" / "install-mac.sh"

# fixture 디렉토리
_FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


# ─────────────────────────────────────────────────────────────────────────────
# 공통 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def _run(args, env=None, cwd=None):
    """run.sh를 subprocess로 실행하여 (returncode, stdout_text, parsed_json) 반환."""
    cmd = ["bash", str(_RUN_SH)] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd) if cwd else None,
    )
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, data


def _env_with_stub_manifest(manifest_path, base_env=None):
    """TOOL_SCAN_MANIFEST_PATH 환경변수로 stub manifest 절대경로를 주입한 env dict 반환."""
    env = (base_env or os.environ).copy()
    env["TOOL_SCAN_MANIFEST_PATH"] = str(manifest_path)
    return env


def _env_with_federation(manifest_path=None, mcps_path=None, skills_path=None, base_env=None):
    """federation 경로 환경변수를 주입한 env dict 반환."""
    env = (base_env or os.environ).copy()
    if manifest_path:
        env["TOOL_SCAN_MANIFEST_PATH"] = str(manifest_path)
    if mcps_path:
        env["TOOL_SCAN_MCPS_PATH"] = str(mcps_path)
    if skills_path:
        env["TOOL_SCAN_SKILLS_REGISTRY_PATH"] = str(skills_path)
    return env


def _env_with_help_cmd(help_script_path, base_env=None):
    """TOOL_SCAN_HELP_CMD 환경변수로 stub --help 스크립트 절대경로를 주입한 env dict 반환."""
    env = (base_env or os.environ).copy()
    env["TOOL_SCAN_HELP_CMD"] = str(help_script_path)
    return env


def _make_stub_manifest_with_tool(tmpdir, tool_name, help_script_path=None):
    """단일 도구 엔트리를 가진 stub manifest.json을 tmpdir에 생성하여 경로 반환."""
    exec_path = str(help_script_path) if help_script_path else "run.sh --help"
    manifest = {
        "$schema": "tool-scan-manifest-v1",
        "version": "1.0.0",
        "updated_at": "2026-06-26",
        "tools": [
            {
                "name": tool_name,
                "kind": "tool",
                "purpose": f"stub tool for testing: {tool_name}",
                "when": [tool_name, "test"],
                "exec": exec_path,
                "usage_source": {
                    "type": "self-help",
                    "exec": exec_path,
                    "ref": None,
                    "text": None,
                    "freshness": None,
                },
                "fallback": None,
            }
        ],
    }
    manifest_path = pathlib.Path(tmpdir) / "manifest.stub.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest_path


def _make_no_exec_venv():
    """존재하지 않는 venv python 경로를 담은 env dict 반환 (venv 부재 시뮬레이션)."""
    env = os.environ.copy()
    env["OPAL_VENV_PYTHON"] = "/nonexistent_path_venv/bin/python"
    return env


def _file_sha256(path):
    """파일의 SHA-256 hex digest 반환."""
    h = hashlib.sha256()
    h.update(pathlib.Path(path).read_bytes())
    return h.hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# TS-001 ~ TS-003: 5서브명령 JSON 계약, venv 부재, 잘못된 호출
# ─────────────────────────────────────────────────────────────────────────────

class TestSubcommandsJson(unittest.TestCase):
    """[T044/L1-subcmds] 5서브명령 기본 JSON 계약 — TS-001, TS-002, TS-003"""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        # 기본 stub manifest 복사
        shutil.copy(_FIXTURES_DIR / "manifest.stub.json", self.tmpdir / "manifest.stub.json")
        self.manifest_path = self.tmpdir / "manifest.stub.json"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_subcommands_json(self):
        """[T044/TS-001] 5서브명령 전부 {"ok":true,"command":"<subcmd>",...} + exit 0.
        RED 조건: run.sh 미구현 → 비0 exit + JSON 없음 → 단언 실패.
        """
        env = _env_with_stub_manifest(self.manifest_path)
        for subcmd in ["list", "which", "usage", "resolve", "check"]:
            with self.subTest(subcmd=subcmd):
                # which/usage/resolve/check는 필수 인자가 있으므로 더미 인자를 줌
                extra = []
                if subcmd in ("which", "resolve"):
                    extra = ["test situation"]
                elif subcmd in ("usage",):
                    extra = ["tool-scan"]
                elif subcmd in ("check",):
                    extra = ["tool-scan"]
                code, stdout, data = _run([subcmd] + extra, env=env)
                self.assertEqual(
                    code, 0,
                    f"[TS-001] {subcmd}: exit 0 expected. got={code}. stdout={stdout}"
                )
                self.assertTrue(
                    data.get("ok"),
                    f"[TS-001] {subcmd}: ok should be true. data={data}"
                )
                self.assertEqual(
                    data.get("command"), subcmd,
                    f"[TS-001] {subcmd}: command field mismatch. data={data}"
                )

    def test_venv_missing(self):
        """[T044/TS-002] venv 부재 시 {"ok":false,"error":"venv_missing","detail":..} + exit 1.
        RED 조건: run.sh 미구현 → exit 127 → exit code 단언 실패.
        """
        env = _make_no_exec_venv()
        code, stdout, data = _run(["list"], env=env)
        self.assertEqual(
            code, 1,
            f"[TS-002] venv 부재: exit 1 expected. got={code}. stdout={stdout}"
        )
        self.assertFalse(
            data.get("ok"),
            f"[TS-002] ok should be false. data={data}"
        )
        self.assertEqual(
            data.get("error"), "venv_missing",
            f"[TS-002] error key should be 'venv_missing'. data={data}"
        )
        self.assertIn(
            "detail", data,
            f"[TS-002] detail field 부재. data={data}"
        )

    def test_bad_invocation(self):
        """[T044/TS-003] 알 수 없는 서브명령/필수 인자 누락 → {"ok":false,..,"error":..} + 비0 exit.
        RED 조건: run.sh 미구현 → exit 127이지만 JSON 응답 없음 + ok=false 단언으로 RED 확보.
        구현 시: exit≠0 + ok=false + error 필드를 포함한 JSON 응답 단언.
        """
        env = _env_with_stub_manifest(self.manifest_path)

        # 알 수 없는 서브명령
        code_bad, stdout_bad, data_bad = _run(["badcmdxyz123"], env=env)
        self.assertNotEqual(
            code_bad, 0,
            f"[TS-003] 알 수 없는 서브명령: 비0 exit expected. got={code_bad}. stdout={stdout_bad}"
        )
        # run.sh 구현 시 반드시 JSON ok=false + error 필드 반환 (exit 127은 구현 부재 신호)
        self.assertNotEqual(
            code_bad, 127,
            f"[TS-003] run.sh 미구현(exit 127). 구현자가 run.sh를 생성해야 이 단언이 통과함. stdout={stdout_bad}"
        )
        self.assertFalse(
            data_bad.get("ok"),
            f"[TS-003] ok=false expected. data={data_bad}"
        )
        self.assertIn(
            "error", data_bad,
            f"[TS-003] error 필드 없음. data={data_bad}"
        )

        # 필수 인자 누락 (which는 <상황> 인자 필요)
        code_miss, stdout_miss, data_miss = _run(["which"], env=env)
        self.assertNotEqual(
            code_miss, 0,
            f"[TS-003] which 인자 누락: 비0 exit expected. got={code_miss}. stdout={stdout_miss}"
        )
        # exit 127은 구현 부재 — 구현 시에는 1 또는 2 기대
        self.assertNotEqual(
            code_miss, 127,
            f"[TS-003] which 인자 누락: run.sh 미구현(exit 127). stdout={stdout_miss}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TS-010 ~ TS-012: manifest.json 구조 검증
# ─────────────────────────────────────────────────────────────────────────────

class TestManifest(unittest.TestCase):
    """[T044/L1-manifest] manifest.json 구조·drift 방어 — TS-010, TS-011, TS-012"""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        shutil.copy(_FIXTURES_DIR / "manifest.stub.json", self.tmpdir / "manifest.stub.json")
        self.manifest_path = self.tmpdir / "manifest.stub.json"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_manifest_no_usage_text(self):
        """[T044/TS-010] manifest grep 시 --help 본문 텍스트 부재, usage_source.text=null(inline 외).
        drift 방어: self-help 엔트리는 포인터만 보유해야 함 (R-3, H-9).
        이 테스트는 실제 manifest.json(F-002 산출물)에 적용됨 — stub은 이미 규칙을 따름.
        """
        real_manifest = _TOOL_DIR / "manifest.json"
        # 실제 manifest가 없으면(RED) 이 테스트는 FileNotFoundError로 FAIL
        self.assertTrue(
            real_manifest.exists(),
            f"[TS-010] manifest.json 부재 — F-002 미구현(RED). path={real_manifest}"
        )
        manifest_text = real_manifest.read_text()
        manifest_data = json.loads(manifest_text)

        for entry in manifest_data.get("tools", []):
            name = entry.get("name", "?")
            usage_source = entry.get("usage_source", {})
            # inline 타입이 아닌 엔트리는 text가 null이어야 함
            if usage_source.get("type") != "inline":
                self.assertIsNone(
                    usage_source.get("text"),
                    f"[TS-010] 엔트리 '{name}': text가 null이 아님(drift 위반). usage_source={usage_source}"
                )
            # --help 본문 텍스트가 manifest에 저장되면 안 됨 (긴 텍스트 검사)
            text_val = usage_source.get("text")
            if text_val is not None:
                self.assertLess(
                    len(str(text_val)), 50,
                    f"[TS-010] 엔트리 '{name}': text 필드에 긴 usage 텍스트 저장(drift 위반). len={len(str(text_val))}"
                )

    def test_manifest_entries(self):
        """[T044/TS-011] 6 OPAL(xlsx/state/code-scan/cmux/test/brain)+tool-scan 7엔트리, 각 usage_source.type 지정.
        이 테스트는 실제 manifest.json(F-002 산출물)에 적용됨.
        """
        real_manifest = _TOOL_DIR / "manifest.json"
        self.assertTrue(
            real_manifest.exists(),
            f"[TS-011] manifest.json 부재 — F-002 미구현(RED). path={real_manifest}"
        )
        manifest_data = json.loads(real_manifest.read_text())
        tools = manifest_data.get("tools", [])
        names = {t.get("name") for t in tools}

        expected_names = {
            "tool-scan", "xlsx-tool", "state-tool",
            "code-scan", "cmux-tool", "test-tool", "brain-tool"
        }
        self.assertEqual(
            len(tools), 7,
            f"[TS-011] 7 엔트리 expected, got={len(tools)}. names={names}"
        )
        self.assertEqual(
            names, expected_names,
            f"[TS-011] 엔트리 집합 불일치. got={names}, expected={expected_names}"
        )

        # 각 엔트리에 usage_source.type 존재 및 허용된 값인지 확인
        allowed_types = {"self-help", "context7", "url", "inline", "doc"}
        for entry in tools:
            name = entry.get("name", "?")
            usage_source = entry.get("usage_source", {})
            self.assertIn(
                "type", usage_source,
                f"[TS-011] 엔트리 '{name}': usage_source.type 필드 없음"
            )
            self.assertIn(
                usage_source["type"], allowed_types,
                f"[TS-011] 엔트리 '{name}': usage_source.type='{usage_source['type']}' 허용값 아님"
            )

    def test_list_purpose_only(self):
        """[T044/TS-012] list 서브명령: stub manifest 7엔트리, purpose 1줄씩만 반환, 전체 usage 본문 미포함.
        RED 조건: run.sh 미구현 → 비0 exit → 단언 실패.
        """
        env = _env_with_stub_manifest(self.manifest_path)
        code, stdout, data = _run(["list"], env=env)
        self.assertEqual(
            code, 0,
            f"[TS-012] list: exit 0 expected. got={code}. stdout={stdout}"
        )
        self.assertTrue(
            data.get("ok"),
            f"[TS-012] list: ok=true expected. data={data}"
        )
        capabilities = data.get("capabilities", [])
        self.assertEqual(
            len(capabilities), 7,
            f"[TS-012] list: 7개 capability expected. got={len(capabilities)}. data={data}"
        )
        for cap in capabilities:
            # purpose 필드 존재
            self.assertIn(
                "purpose", cap,
                f"[TS-012] capability에 purpose 필드 없음. cap={cap}"
            )
            # usage 본문이 포함되면 안 됨: usage_text / usage_json 필드 없음
            self.assertNotIn(
                "usage_text", cap,
                f"[TS-012] list 응답에 usage_text가 포함됨(2단 토큰 위반). cap={cap}"
            )
            self.assertNotIn(
                "usage_json", cap,
                f"[TS-012] list 응답에 usage_json이 포함됨(2단 토큰 위반). cap={cap}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# TS-020 ~ TS-023: usage live --help 추출
# ─────────────────────────────────────────────────────────────────────────────

class TestUsage(unittest.TestCase):
    """[T044/L1-usage] usage live --help 추출 — TS-020, TS-021, TS-022, TS-023"""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        # fixture 쉘 스크립트를 실행 가능하게 복사
        for fname in ("help_exit0_ok_false.sh", "help_stderr_only.sh", "help_mutable.sh"):
            dst = self.tmpdir / fname
            shutil.copy(_FIXTURES_DIR / fname, dst)
            dst.chmod(dst.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_usage_exit0_okfalse(self):
        """[T044/TS-020] OPAL 래퍼 stub: --help → stdout {"ok":false} + exit 0 함정.
        기대: exit_code 기준 성공 판정(ok:false 무관), live:true, usage 반환 성공.
        RED 조건: run.sh 미구현 → 비0 exit → 단언 실패.
        """
        help_script = self.tmpdir / "help_exit0_ok_false.sh"
        stub_manifest = _make_stub_manifest_with_tool(
            self.tmpdir, "stub-opal-tool", help_script
        )
        env = _env_with_stub_manifest(stub_manifest)
        env = _env_with_help_cmd(help_script, env)
        code, stdout, data = _run(["usage", "stub-opal-tool"], env=env)
        self.assertEqual(
            code, 0,
            f"[TS-020] exit0+ok:false stub: usage exit 0 expected. got={code}. stdout={stdout}"
        )
        self.assertTrue(
            data.get("ok"),
            f"[TS-020] usage ok=true expected (exit code 기준 판정). data={data}"
        )
        self.assertTrue(
            data.get("live"),
            f"[TS-020] live=true expected. data={data}"
        )
        self.assertEqual(
            data.get("exit_code"), 0,
            f"[TS-020] exit_code=0 expected. data={data}"
        )
        # usage_json 또는 usage_text 중 하나는 있어야 함
        has_usage = ("usage_json" in data and data["usage_json"] is not None) or \
                    ("usage_text" in data and data["usage_text"])
        self.assertTrue(
            has_usage,
            f"[TS-020] usage_json 또는 usage_text 없음. data={data}"
        )

    def test_usage_live_nocache(self):
        """[T044/TS-021] 정적 캐시 금지 — stub 출력 A→B 변경 시 2회 usage 호출이 변경 반영.
        RED 조건: run.sh 미구현 → 비0 exit → 단언 실패.
        """
        help_script = self.tmpdir / "help_mutable.sh"
        stub_manifest = _make_stub_manifest_with_tool(
            self.tmpdir, "stub-mutable-tool", help_script
        )

        # 1회: TOOL_SCAN_HELP_VERSION=v1
        env_v1 = _env_with_stub_manifest(stub_manifest)
        env_v1 = _env_with_help_cmd(help_script, env_v1)
        env_v1["TOOL_SCAN_HELP_VERSION"] = "v1"
        code1, _, data1 = _run(["usage", "stub-mutable-tool"], env=env_v1)
        self.assertEqual(
            code1, 0,
            f"[TS-021] 1회 호출 exit 0 expected. got={code1}"
        )

        # 2회: TOOL_SCAN_HELP_VERSION=v2
        env_v2 = _env_with_stub_manifest(stub_manifest)
        env_v2 = _env_with_help_cmd(help_script, env_v2)
        env_v2["TOOL_SCAN_HELP_VERSION"] = "v2"
        code2, _, data2 = _run(["usage", "stub-mutable-tool"], env=env_v2)
        self.assertEqual(
            code2, 0,
            f"[TS-021] 2회 호출 exit 0 expected. got={code2}"
        )

        # 두 응답의 usage 텍스트가 달라야 함 (정적 캐시 미사용 증명)
        text1 = data1.get("usage_text", "") or str(data1.get("usage_json", ""))
        text2 = data2.get("usage_text", "") or str(data2.get("usage_json", ""))
        self.assertNotEqual(
            text1, text2,
            f"[TS-021] 정적 캐시 의심: 두 usage 출력이 동일함. text1={text1!r}, text2={text2!r}"
        )
        # v1/v2 문자열이 각 응답에 포함되어야 함
        self.assertIn(
            "v1", text1,
            f"[TS-021] 1회 응답에 'v1' 없음. text1={text1!r}"
        )
        self.assertIn(
            "v2", text2,
            f"[TS-021] 2회 응답에 'v2' 없음. text2={text2!r}"
        )

    def test_usage_stderr_merge(self):
        """[T044/TS-022] 외부 CLI stub: --help→ stderr로만 출력, stdout 비어있음.
        기대: stdout+stderr 병합 → usage_text 비어있지 않음.
        RED 조건: run.sh 미구현 → 비0 exit → 단언 실패.
        """
        help_script = self.tmpdir / "help_stderr_only.sh"
        stub_manifest = _make_stub_manifest_with_tool(
            self.tmpdir, "stub-stderr-tool", help_script
        )
        env = _env_with_stub_manifest(stub_manifest)
        env = _env_with_help_cmd(help_script, env)
        code, stdout, data = _run(["usage", "stub-stderr-tool"], env=env)
        self.assertEqual(
            code, 0,
            f"[TS-022] stderr-only stub: usage exit 0 expected. got={code}. stdout={stdout}"
        )
        usage_text = data.get("usage_text", "")
        self.assertTrue(
            usage_text and len(usage_text.strip()) > 0,
            f"[TS-022] stdout+stderr 병합 실패 — usage_text 비어있음. data={data}"
        )
        # stderr의 "Usage:" 문자열이 포함되어야 함
        self.assertIn(
            "Usage", usage_text,
            f"[TS-022] usage_text에 'Usage:' 없음 (stderr 병합 미적용). data={data}"
        )

    def test_usage_tool_not_found(self):
        """[T044/TS-023] 미등록 도구 → {"ok":false,"error":"tool_not_found"}.
        RED 조건: run.sh 미구현 → exit 127 → assertNotEqual(code, 127)로 RED 확보.
        구현 시: exit≠0 + ok=false + error='tool_not_found' JSON 단언.
        """
        shutil.copy(_FIXTURES_DIR / "manifest.stub.json", self.tmpdir / "manifest.stub.json")
        env = _env_with_stub_manifest(self.tmpdir / "manifest.stub.json")
        code, stdout, data = _run(["usage", "nonexistent_tool_xyz_044"], env=env)
        # 비0 exit 기대
        self.assertNotEqual(
            code, 0,
            f"[TS-023] 미등록 도구: 비0 exit expected. got={code}. stdout={stdout}"
        )
        # exit 127은 run.sh 부재 증거 — 구현 시 통과되지 않아야 함
        self.assertNotEqual(
            code, 127,
            f"[TS-023] run.sh 미구현(exit 127). 구현자가 run.sh를 생성해야 이 단언이 통과함."
        )
        # 구현 시 error=tool_not_found
        self.assertFalse(
            data.get("ok"),
            f"[TS-023] ok=false expected. data={data}"
        )
        self.assertEqual(
            data.get("error"), "tool_not_found",
            f"[TS-023] error='tool_not_found' expected. data={data}"
        )


    def test_usage_real_target_path_resolution(self):
        """[T044/TS-024] TOOL_SCAN_HELP_CMD 미주입 — 실 manifest로 usage state-tool 호출 시
        대상 도구(state-tool)의 사용법이 반환되어야 함.

        버그 설명 (tool_scan.py:275):
          _TOOL_DIR = tool-scan 자기 디렉토리
          tool_run_sh = _TOOL_DIR / "run.sh"  ← 대상 도구 run.sh가 아니라 tool-scan 자신의 run.sh
          → usage_text가 tool-scan 자기 --help가 됨.

        RED 조건 (현재 버그 상태):
          usage_text에 "tool-scan [-h] {list,which,usage,resolve,check}" 포함
          → assertNotIn 단언 실패 → FAIL(RED).

        GREEN 조건 (수정 후):
          usage_text에 state-tool 서브명령 토큰(init/show/advance/mark 중 하나 이상) 포함,
          tool-scan 고유 시그니처 미포함.
        """
        # TOOL_SCAN_HELP_CMD 미주입: 실제 manifest→대상 도구 경로 해석 코드패스를 타야 함
        env = os.environ.copy()
        # TOOL_SCAN_HELP_CMD가 환경에 있다면 제거 (stub 우회 차단)
        env.pop("TOOL_SCAN_HELP_CMD", None)

        code, stdout, data = _run(["usage", "state-tool"], env=env)

        # 1) exit 0 + ok=true (기본 응답 계약)
        self.assertEqual(
            code, 0,
            f"[TS-024] usage state-tool: exit 0 expected. got={code}. stdout={stdout}"
        )
        self.assertTrue(
            data.get("ok"),
            f"[TS-024] ok=true expected. data={data}"
        )

        usage_str = data.get("usage_text", "") or str(data.get("usage_json", ""))

        # 2) tool-scan 자기 시그니처가 포함되면 안 됨 (버그 증거)
        self.assertNotIn(
            "tool-scan [-h] {list,which,usage,resolve,check}",
            usage_str,
            f"[TS-024] usage state-tool이 tool-scan 자기 --help를 반환함 (버그: _TOOL_DIR 경로 오류). "
            f"usage_str={usage_str!r}"
        )

        # 3) state-tool 서브명령 토큰이 포함되어야 함
        state_tool_tokens = ["init", "show", "advance", "mark"]
        has_state_token = any(tok in usage_str for tok in state_tool_tokens)
        self.assertTrue(
            has_state_token,
            f"[TS-024] usage_text에 state-tool 서브명령 토큰({state_tool_tokens}) 없음. "
            f"usage_str={usage_str!r}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TS-030 ~ TS-035: resolve + federation + 결정론 + 불파괴
# ─────────────────────────────────────────────────────────────────────────────

class TestResolveAndFederation(unittest.TestCase):
    """[T044/L1-resolve] resolve/which + federation + 결정론 + 불파괴 — TS-030~035"""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        shutil.copy(_FIXTURES_DIR / "manifest.stub.json", self.tmpdir / "manifest.stub.json")
        self.manifest_path = self.tmpdir / "manifest.stub.json"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_resolve_tool(self):
        """[T044/TS-030] resolve "browser check localhost" → cmux-tool(kind=tool, invoke=shell, fallback 동봉).
        실 manifest + federation 사용.
        RED 조건: run.sh 미구현 → 비0 exit → 단언 실패.
        """
        env = _env_with_stub_manifest(self.manifest_path)
        env = _env_with_federation(
            manifest_path=self.manifest_path,
            mcps_path=_REAL_MCPS_MD,
            skills_path=_REAL_SKILLS_REGISTRY,
            base_env=env,
        )
        code, stdout, data = _run(["resolve", "browser check localhost"], env=env)
        self.assertEqual(
            code, 0,
            f"[TS-030] resolve: exit 0 expected. got={code}. stdout={stdout}"
        )
        self.assertTrue(
            data.get("ok"),
            f"[TS-030] ok=true expected. data={data}"
        )
        resolved = data.get("resolved", {})
        self.assertEqual(
            resolved.get("name"), "cmux-tool",
            f"[TS-030] resolved.name should be 'cmux-tool'. data={data}"
        )
        self.assertEqual(
            resolved.get("kind"), "tool",
            f"[TS-030] resolved.kind should be 'tool'. data={data}"
        )
        self.assertEqual(
            resolved.get("invoke"), "shell",
            f"[TS-030] resolved.invoke should be 'shell'. data={data}"
        )
        # fallback 계약 동봉
        self.assertIn(
            "fallback", resolved,
            f"[TS-030] fallback 필드 없음. data={data}"
        )
        # error_contract 또는 fallback이 cmux 에러 계약을 포함해야 함
        has_error_contract = "error_contract" in resolved or resolved.get("fallback") is not None
        self.assertTrue(
            has_error_contract,
            f"[TS-030] error_contract 또는 fallback 부재. data={data}"
        )

    def test_resolve_mcp_pointer(self):
        """[T044/TS-031] resolve "library docs" → context7(kind=mcp, invoke=ToolSearch 포인터, 스키마 미반환).
        실 mcps.md 사용. H-3: mcp-schema live 부재 → ToolSearch 포인터만.
        RED 조건: run.sh 미구현 → 비0 exit → 단언 실패.
        """
        env = _env_with_stub_manifest(self.manifest_path)
        env = _env_with_federation(
            manifest_path=self.manifest_path,
            mcps_path=_REAL_MCPS_MD,
            skills_path=_REAL_SKILLS_REGISTRY,
            base_env=env,
        )
        code, stdout, data = _run(["resolve", "library docs"], env=env)
        self.assertEqual(
            code, 0,
            f"[TS-031] resolve mcp: exit 0 expected. got={code}. stdout={stdout}"
        )
        resolved = data.get("resolved", {})
        self.assertEqual(
            resolved.get("kind"), "mcp",
            f"[TS-031] resolved.kind should be 'mcp'. data={data}"
        )
        self.assertEqual(
            resolved.get("invoke"), "ToolSearch",
            f"[TS-031] resolved.invoke should be 'ToolSearch'. data={data}"
        )
        # 파라미터 스키마는 반환하지 않음 (H-3)
        self.assertNotIn(
            "parameters", resolved,
            f"[TS-031] resolved에 parameters 포함(MCP 스키마 미반환 계약 위반). data={data}"
        )

    def test_resolve_opskill(self):
        """[T044/TS-032] resolve "데이터 모델" → op-data-model(kind=op-skill, dispatched_by 포함).
        실 skills-registry.json 사용.
        RED 조건: run.sh 미구현 → 비0 exit → 단언 실패.
        """
        env = _env_with_stub_manifest(self.manifest_path)
        env = _env_with_federation(
            manifest_path=self.manifest_path,
            mcps_path=_REAL_MCPS_MD,
            skills_path=_REAL_SKILLS_REGISTRY,
            base_env=env,
        )
        code, stdout, data = _run(["resolve", "데이터 모델"], env=env)
        self.assertEqual(
            code, 0,
            f"[TS-032] resolve op-skill: exit 0 expected. got={code}. stdout={stdout}"
        )
        resolved = data.get("resolved", {})
        self.assertEqual(
            resolved.get("kind"), "op-skill",
            f"[TS-032] resolved.kind should be 'op-skill'. data={data}"
        )
        self.assertEqual(
            resolved.get("name"), "op-data-model",
            f"[TS-032] resolved.name should be 'op-data-model'. data={data}"
        )
        self.assertEqual(
            resolved.get("invoke"), "dispatch",
            f"[TS-032] resolved.invoke should be 'dispatch'. data={data}"
        )
        # dispatched_by 포함
        self.assertIn(
            "dispatched_by", resolved,
            f"[TS-032] dispatched_by 필드 없음. data={data}"
        )
        self.assertTrue(
            len(resolved.get("dispatched_by", [])) > 0,
            f"[TS-032] dispatched_by 비어있음. data={data}"
        )

    def test_registry_unchanged(self):
        """[T044/TS-033] federation 불파괴: resolve 실행 전후 skills-registry.json byte 동일.
        H-1: skills-registry.json은 읽기 전용 — 원본 무변경 단언.
        RED 조건: run.sh 미구현 → exit 127 → resolve_code == 127 단언으로 RED 확보.
        구현 시: resolve가 exit 0으로 실행되고 파일 해시가 동일해야 함.
        """
        self.assertTrue(
            _REAL_SKILLS_REGISTRY.exists(),
            f"[TS-033] skills-registry.json 없음. path={_REAL_SKILLS_REGISTRY}"
        )
        hash_before = _file_sha256(_REAL_SKILLS_REGISTRY)

        # resolve 실행
        env = _env_with_stub_manifest(self.manifest_path)
        env = _env_with_federation(
            manifest_path=self.manifest_path,
            mcps_path=_REAL_MCPS_MD,
            skills_path=_REAL_SKILLS_REGISTRY,
            base_env=env,
        )
        resolve_code, resolve_stdout, resolve_data = _run(["resolve", "데이터 모델"], env=env)

        # run.sh 미구현 시 exit 127 → 이 단언으로 RED 확보
        self.assertNotEqual(
            resolve_code, 127,
            f"[TS-033] run.sh 미구현(exit 127). 구현자가 run.sh를 생성해야 이 단언이 통과함."
        )

        # 파일 해시 비교 (불파괴 검증)
        hash_after = _file_sha256(_REAL_SKILLS_REGISTRY)
        self.assertEqual(
            hash_before, hash_after,
            f"[TS-033] skills-registry.json이 resolve 실행 후 변경됨(불파괴 위반)! "
            f"before={hash_before[:16]}, after={hash_after[:16]}"
        )

    def test_resolve_deterministic(self):
        """[T044/TS-034] 동일 상황 입력 2회 → 동일 정렬 후보(결정론).
        H-10: 라우팅 안정 정렬 (-score, kind 우선순위, name 알파벳).
        RED 조건: run.sh 미구현 → 두 호출 모두 빈/에러 → 우연 PASS 가능이지만
                  ok=true 단언이 추가로 있으므로 실제 구현 전엔 FAIL.
        """
        env = _env_with_stub_manifest(self.manifest_path)
        env = _env_with_federation(
            manifest_path=self.manifest_path,
            mcps_path=_REAL_MCPS_MD,
            skills_path=_REAL_SKILLS_REGISTRY,
            base_env=env,
        )

        code1, stdout1, data1 = _run(["resolve", "browser check localhost"], env=env)
        code2, stdout2, data2 = _run(["resolve", "browser check localhost"], env=env)

        self.assertEqual(
            code1, 0,
            f"[TS-034] 1회 resolve exit 0 expected. got={code1}"
        )
        self.assertEqual(
            code2, 0,
            f"[TS-034] 2회 resolve exit 0 expected. got={code2}"
        )
        # 두 출력이 동일해야 함 (결정론)
        self.assertEqual(
            stdout1, stdout2,
            f"[TS-034] 결정론 실패: 동일 입력에 다른 출력. stdout1={stdout1!r}, stdout2={stdout2!r}"
        )

    def test_which_no_match(self):
        """[T044/TS-035] 매칭 없는 입력 → {"ok":false,"error":"no_match"}.
        RED 조건: run.sh 미구현 → exit 127 → assertNotEqual(code, 127)로 RED 확보.
        구현 시: exit≠0 + ok=false + error='no_match' JSON 단언.
        """
        env = _env_with_stub_manifest(self.manifest_path)
        env = _env_with_federation(
            manifest_path=self.manifest_path,
            mcps_path=_REAL_MCPS_MD,
            skills_path=_REAL_SKILLS_REGISTRY,
            base_env=env,
        )
        code, stdout, data = _run(["which", "zzz없는것zzz_044_no_match_ever"], env=env)
        self.assertNotEqual(
            code, 0,
            f"[TS-035] no_match: 비0 exit expected. got={code}. stdout={stdout}"
        )
        # exit 127은 run.sh 부재 — 구현 시에는 통과되지 않아야 함
        self.assertNotEqual(
            code, 127,
            f"[TS-035] run.sh 미구현(exit 127). 구현자가 run.sh를 생성해야 이 단언이 통과함."
        )
        self.assertFalse(
            data.get("ok"),
            f"[TS-035] ok=false expected. data={data}"
        )
        self.assertEqual(
            data.get("error"), "no_match",
            f"[TS-035] error='no_match' expected. data={data}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TS-040 ~ TS-060: 산출물 grep 테스트 (F-005/006/007 구현 후 GREEN)
# ─────────────────────────────────────────────────────────────────────────────

class TestOutputArtifacts(unittest.TestCase):
    """[T044/L1-artifacts] 산출물 grep 테스트 — TS-040, TS-041, TS-050, TS-051, TS-060.
    현재는 F-005/006/007 미구현이므로 모두 RED(FAIL)이 정상.
    """

    def test_agentmd_cmux_routing(self):
        """[T044/TS-040] F-005 구현 후: AGENT.md 인지맵에 cmux-tool 행 존재,
        localhost 행이 cmux-tool 1순위/playwright 폴백 명시.
        RED 조건: AGENT.md에 cmux-tool 인지맵 행 없음 → FAIL.
        """
        self.assertTrue(
            _AGENT_MD.exists(),
            f"[TS-040] AGENT.md 파일 없음. path={_AGENT_MD}"
        )
        content = _AGENT_MD.read_text()

        # cmux-tool 행이 인지맵 표에 있어야 함
        self.assertIn(
            "cmux-tool",
            content,
            f"[TS-040] AGENT.md 인지맵에 'cmux-tool' 없음. path={_AGENT_MD}"
        )

        # localhost 상황에서 cmux-tool이 1순위로 명시되어야 함
        # 예: "localhost | cmux-tool" 또는 "cmux-tool 우선 / playwright ... 폴백"
        import re
        localhost_cmux_pattern = re.search(
            r"localhost.*cmux.?tool|cmux.?tool.*localhost",
            content,
            re.IGNORECASE,
        )
        self.assertIsNotNone(
            localhost_cmux_pattern,
            f"[TS-040] AGENT.md에 'localhost + cmux-tool' 연관 행 없음(1순위 미명시). path={_AGENT_MD}"
        )

        # playwright 폴백 명시
        playwright_fallback_pattern = re.search(
            r"playwright.*fallback|fallback.*playwright|playwright.*폴백|폴백.*playwright",
            content,
            re.IGNORECASE,
        )
        self.assertIsNotNone(
            playwright_fallback_pattern,
            f"[TS-040] AGENT.md에 playwright 폴백 명시 없음. path={_AGENT_MD}"
        )

    def test_agentmd_usage_discipline(self):
        """[T044/TS-041] F-005 구현 후: AGENT.md에 "사용법 선확인" + "에러 종류 진단후 폴백" 규율 문단.
        RED 조건: 해당 규율 문단 없음 → FAIL.
        """
        self.assertTrue(
            _AGENT_MD.exists(),
            f"[TS-041] AGENT.md 파일 없음. path={_AGENT_MD}"
        )
        content = _AGENT_MD.read_text()

        # "사용법 선확인" 문구
        self.assertIn(
            "사용법 선확인",
            content,
            f"[TS-041] AGENT.md에 '사용법 선확인' 문구 없음. path={_AGENT_MD}"
        )

        # 에러 종류 진단후 폴백(usage=수정/cmux_not_installed=폴백) 내용
        self.assertIn(
            "cmux_not_installed",
            content,
            f"[TS-041] AGENT.md에 'cmux_not_installed' 폴백 규율 없음. path={_AGENT_MD}"
        )

    def test_registry_parity(self):
        """[T044/TS-050] F-006 구현 후: tools.md 섹션 집합 == harness §9 표 도구 집합 (둘 다 7도구).
        H-5: drift 정합. 두 표 도구 집합이 동일해야 함.
        RED 조건: brain-tool/code-scan/cmux-tool/tool-scan 미추가 → 집합 불일치 → FAIL.
        """
        self.assertTrue(
            _TOOLS_MD.exists(),
            f"[TS-050] tools.md 파일 없음. path={_TOOLS_MD}"
        )
        self.assertTrue(
            _HARNESS_MD.exists(),
            f"[TS-050] opal-harness.md 파일 없음. path={_HARNESS_MD}"
        )

        tools_content = _TOOLS_MD.read_text()
        harness_content = _HARNESS_MD.read_text()

        expected_tools = {
            "xlsx-tool", "xlsx", "state-tool", "state",
            "code-scan", "cmux-tool", "cmux",
            "test-tool", "test", "brain-tool", "brain", "tool-scan"
        }

        # tools.md에서 7도구 섹션 헤더 추출
        # "## brain-tool" 또는 "## brain" 패턴으로 섹션 확인
        tools_found = set()
        for tool_name in ["xlsx", "state", "code-scan", "cmux", "test", "brain", "tool-scan"]:
            import re
            if re.search(rf"#+\s+{re.escape(tool_name)}", tools_content, re.IGNORECASE):
                tools_found.add(tool_name)

        self.assertEqual(
            len(tools_found), 7,
            f"[TS-050] tools.md에서 7도구 섹션 미확인. found={tools_found}"
        )

        # harness §9 표에서 도구 행 추출
        harness_tools_found = set()
        for tool_name in ["xlsx", "state", "code-scan", "cmux", "test", "brain", "tool-scan"]:
            import re
            if re.search(rf"\|\s*{re.escape(tool_name)}", harness_content, re.IGNORECASE):
                harness_tools_found.add(tool_name)

        self.assertEqual(
            len(harness_tools_found), 7,
            f"[TS-050] harness §9 표에서 7도구 행 미확인. found={harness_tools_found}"
        )

        # 두 집합 동일
        self.assertEqual(
            tools_found, harness_tools_found,
            f"[TS-050] tools.md 집합과 harness §9 집합 불일치. tools={tools_found}, harness={harness_tools_found}"
        )

    def test_drift_entries(self):
        """[T044/TS-051] F-006 구현 후: tools.md에 brain-tool 섹션, harness §9에 code-scan·cmux-tool 행.
        RED 조건: brain-tool/code-scan/cmux-tool 미추가 → FAIL.
        """
        self.assertTrue(
            _TOOLS_MD.exists(),
            f"[TS-051] tools.md 파일 없음. path={_TOOLS_MD}"
        )
        self.assertTrue(
            _HARNESS_MD.exists(),
            f"[TS-051] opal-harness.md 파일 없음. path={_HARNESS_MD}"
        )

        tools_content = _TOOLS_MD.read_text()
        harness_content = _HARNESS_MD.read_text()

        # tools.md에 brain-tool 섹션
        import re
        brain_section = re.search(r"#+\s+brain.?tool", tools_content, re.IGNORECASE)
        self.assertIsNotNone(
            brain_section,
            f"[TS-051] tools.md에 brain-tool 섹션 없음. path={_TOOLS_MD}"
        )

        # harness §9에 code-scan 행
        code_scan_row = re.search(r"\|\s*code.?scan", harness_content, re.IGNORECASE)
        self.assertIsNotNone(
            code_scan_row,
            f"[TS-051] harness §9에 code-scan 행 없음. path={_HARNESS_MD}"
        )

        # harness §9에 cmux-tool 행
        cmux_row = re.search(r"\|\s*cmux.?tool", harness_content, re.IGNORECASE)
        self.assertIsNotNone(
            cmux_row,
            f"[TS-051] harness §9에 cmux-tool 행 없음. path={_HARNESS_MD}"
        )

    def test_install_chmod_line(self):
        """[T044/TS-060] F-007 구현 후: install-mac.sh에 tool-scan/run.sh chmod 라인 존재.
        H-6: install 스크립트에 tool-scan 실행권한 설정 라인 필요.
        RED 조건: install-mac.sh에 tool-scan chmod 라인 없음 → FAIL.
        """
        self.assertTrue(
            _INSTALL_SH.exists(),
            f"[TS-060] install-mac.sh 파일 없음. path={_INSTALL_SH}"
        )
        content = _INSTALL_SH.read_text()

        # "tool-scan" + "chmod" 또는 "tool-scan/run.sh" 라인 존재
        import re
        chmod_line = re.search(r"tool.?scan.*chmod|chmod.*tool.?scan", content, re.IGNORECASE)
        self.assertIsNotNone(
            chmod_line,
            f"[TS-060] install-mac.sh에 tool-scan chmod 라인 없음. path={_INSTALL_SH}"
        )

        # tool-scan/run.sh 참조 라인 존재
        run_sh_line = re.search(r"tool.?scan/run\.sh", content, re.IGNORECASE)
        self.assertIsNotNone(
            run_sh_line,
            f"[TS-060] install-mac.sh에 'tool-scan/run.sh' 참조 없음. path={_INSTALL_SH}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
