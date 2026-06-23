"""
@header {
  "module": "test_test_tool",
  "task": "039",
  "layer": "test",
  "domain": "opal-tools",
  "description": "test-tool 4서브명령(resolve/check/unit/integration) 행위 계약 RED-first 테스트. RED 상태(미구현) — 전부 FAIL 예상. GREEN 전환은 opal-be-agent(Step 3) 담당(작성자≠구현자).",
  "scenarios": "S-1~S-9",
  "track": "RED-first (red-first.md §1~§4)",
  "exports": [
    "TestResolve",
    "TestUnit",
    "TestCheck",
    "TestIntegrationCmuxFallback",
    "TestIntegrationCmuxEscalate",
    "TestIntegrationModeA",
    "TestErrorCodesInCatalog"
  ]
}

[T039] test-tool 4서브명령 행위 계약 — RED-first TDD
검증 대상: opal/tools/test-tool/run.sh 의 공개 인터페이스(exit code + stdout JSON)만 단언.
내부 구현/private 결합 금지(red-first.md §4).

cmux-tool 스텁 전략:
  - unittest.mock/MagicMock/patch 사용 금지 (state-tool mock 가드 오탐 회피 — tasks/033/034 교훈)
  - 결정론적 JSON을 반환하는 실제 stub 쉘 스크립트를 tmp_path에 생성
  - OPAL_CMUX_TOOL_CMD 환경변수로 stub 절대경로를 주입하여 test-tool이 stub을 호출하도록 격리
    (S-15 실검증 발견: cmux-tool은 PATH 명령이 아니라 ~/.opal/tools/cmux-tool/run.sh 경로 기반 호출이
     실제 OPAL 호출 계약임 — e2e_adapter가 OPAL_CMUX_TOOL_CMD env → 없으면 기본 경로로 호출해야 함)
  - PATH 주입(_env_with_stub_path) 방식은 S-1~S-5(cmux 무관) 헬퍼에서만 유지
"""

import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

# test-tool run.sh 위치 (산출 예정 — Step3 구현 전이므로 부재 상태)
_TOOL_DIR = pathlib.Path(__file__).parent.parent
_RUN_SH = _TOOL_DIR / "run.sh"

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
        cwd=cwd,
    )
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, data


def _make_stub_script(stub_dir, name, json_output, exit_code=0):
    """결정론적 JSON을 반환하는 stub 쉘 스크립트를 stub_dir/<name>으로 생성."""
    stub_path = stub_dir / name
    # $@ 인자를 무시하고 지정 JSON을 출력한 뒤 종료
    script = f"""#!/bin/bash
echo '{json.dumps(json_output, ensure_ascii=False)}'
exit {exit_code}
"""
    stub_path.write_text(script)
    stub_path.chmod(stub_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return stub_path


def _env_with_stub_path(stub_dir):
    """현재 환경을 복사하고 stub_dir를 PATH 선두에 추가한 환경 dict 반환.
    cmux 무관 테스트(S-1~S-5)의 헬퍼 stub(eslint/tsc/vitest 등) 주입 전용.
    cmux-tool 주입에는 _env_with_cmux_cmd()를 사용한다.
    """
    env = os.environ.copy()
    env["PATH"] = str(stub_dir) + os.pathsep + env.get("PATH", "")
    return env


def _env_with_cmux_cmd(stub_path, base_env=None):
    """OPAL_CMUX_TOOL_CMD 환경변수로 cmux-tool stub 절대경로를 주입한 환경 dict 반환.
    S-15 실검증 발견: OPAL cmux-tool은 PATH 명령이 아니라 절대 경로로 호출해야 하는
    실제 호출 계약을 반영한다. e2e_adapter는 OPAL_CMUX_TOOL_CMD env를 우선 사용하고,
    없으면 ~/.opal/tools/cmux-tool/run.sh를 기본값으로 사용한다(구현자 담당).
    """
    env = (base_env or os.environ).copy()
    env["OPAL_CMUX_TOOL_CMD"] = str(stub_path)
    return env


# ─────────────────────────────────────────────────────────────────────────────
# S-1, S-2: resolve 서브명령
# ─────────────────────────────────────────────────────────────────────────────

class TestResolve(unittest.TestCase):
    """[T039/L1-resolve] test-tool resolve 행위 계약 — S-1, S-2"""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        # v2.0 tiers 구조의 project test-tools.yaml fixture 생성
        self.project_root = self.tmpdir / "project"
        self.project_root.mkdir()
        opal_dir = self.project_root / ".opal"
        opal_dir.mkdir()
        project_yaml = opal_dir / "test-tools.yaml"
        project_yaml.write_text(
            """
version: "2.0"
source_label: project
stack: {language: ts, framework: nextjs, runtime: node}
tiers:
  unit:
    fe:
      lint:
        - name: eslint
          check: npx eslint .
          required: true
      typecheck:
        - name: tsc
          check: npx tsc --noEmit
          required: true
      unit:
        - name: vitest
          check: npx vitest run
    be:
      lint:
        - name: eslint
          check: npx eslint .
          required: true
      unit:
        - name: vitest
          check: npx vitest run
  integration:
    e2e:
      - name: cmux
        priority: 1
        via: cmux-tool
      - name: playwright
        priority: 2
        fallback: true
"""
        )
        # global template fixture
        self.global_dir = self.tmpdir / "global"
        self.global_dir.mkdir()
        global_yaml = self.global_dir / "test-tools.yaml"
        global_yaml.write_text(
            """
version: "2.0"
source_label: global
tiers:
  unit:
    fe:
      unit:
        - name: jest
    be:
      unit:
        - name: pytest
  integration:
    e2e:
      - name: playwright
        priority: 1
"""
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_resolve_returns_tier_toolset_json(self):
        """[T039/L1-resolve] S-1 H-1: resolve가 exit 0 + tiers.unit.fe/be + tiers.integration.e2e 키를 포함한 JSON 반환"""
        code, stdout, data = _run(
            ["resolve", "--project-root", str(self.project_root)]
        )
        self.assertEqual(code, 0, f"exit should be 0, got {code}. stdout={stdout}")
        self.assertTrue(data.get("ok"), f"ok should be true. data={data}")
        # tiers 최상위 키 존재
        tiers = data.get("tiers", {})
        self.assertIn("unit", tiers, f"tiers.unit 키 없음. data={data}")
        self.assertIn("be", tiers.get("unit", {}), f"tiers.unit.be 키 없음. data={data}")
        self.assertIn("fe", tiers.get("unit", {}), f"tiers.unit.fe 키 없음. data={data}")
        integration = tiers.get("integration", {})
        self.assertIn("e2e", integration, f"tiers.integration.e2e 키 없음. data={data}")

    def test_resolve_order_project_over_global(self):
        """[T039/L1-resolve] S-2 H-1: project yaml fixture가 global보다 우선 — source=project"""
        # OPAL_GLOBAL_DIR 환경변수로 global template 디렉토리 주입
        env = os.environ.copy()
        env["OPAL_TEST_TOOLS_GLOBAL"] = str(self.global_dir / "test-tools.yaml")
        code, stdout, data = _run(
            ["resolve", "--project-root", str(self.project_root)],
            env=env,
        )
        self.assertEqual(code, 0, f"exit 0 expected. stdout={stdout}")
        self.assertEqual(
            data.get("source"), "project",
            f"source should be 'project'. data={data}"
        )
        # project fixture에는 eslint가 있고 global fixture에는 없음 — 값이 project 기반임을 확인
        unit_fe = data.get("tiers", {}).get("unit", {}).get("fe", {})
        lint_tools = unit_fe.get("lint", [])
        names = [t.get("name") for t in lint_tools]
        self.assertIn("eslint", names, f"project lint 값(eslint) 미채택. data={data}")

    def test_resolve_infer_fallback_when_no_yaml(self):
        """[T039/L1-resolve] S-2 H-1/H-8: yaml 부재 + package.json 존재 시 source=infer 추론 폴백"""
        # yaml 없는 프로젝트 루트(package.json만 존재)
        no_yaml_root = self.tmpdir / "no_yaml_project"
        no_yaml_root.mkdir()
        (no_yaml_root / "package.json").write_text(
            '{"name": "test-app", "devDependencies": {"vitest": "^1.0.0", "eslint": "^8.0.0"}}'
        )
        code, stdout, data = _run(
            ["resolve", "--project-root", str(no_yaml_root)]
        )
        self.assertEqual(code, 0, f"infer fallback should exit 0. stdout={stdout}")
        self.assertEqual(
            data.get("source"), "infer",
            f"source should be 'infer'. data={data}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# S-3, S-4: unit 서브명령
# ─────────────────────────────────────────────────────────────────────────────

class TestUnit(unittest.TestCase):
    """[T039/L1-unit] test-tool unit 행위 계약 — S-3, S-4"""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.project_root = self.tmpdir / "project"
        self.project_root.mkdir()
        opal_dir = self.project_root / ".opal"
        opal_dir.mkdir()
        # lint 실패를 주입하는 stub 환경을 위해 stub_dir 준비
        self.stub_dir = self.tmpdir / "stubs"
        self.stub_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_lint_fail_yaml(self):
        """eslint가 exit 1을 반환하도록 설정된 yaml fixture 생성."""
        yaml_path = self.project_root / ".opal" / "test-tools.yaml"
        # stub eslint 생성: 항상 lint 오류로 exit 1
        stub_eslint = self.stub_dir / "eslint"
        stub_eslint.write_text(
            '#!/bin/bash\n'
            'echo \'{"lintErrors": 1, "detail": "intentional lint failure"}\'\n'
            'exit 1\n'
        )
        stub_eslint.chmod(stub_eslint.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        yaml_path.write_text(
            """
version: "2.0"
tiers:
  unit:
    be:
      lint:
        - name: eslint
          check: eslint .
          required: true
      typecheck:
        - name: tsc
          check: tsc --noEmit
          required: true
      unit:
        - name: vitest
          check: vitest run
"""
        )
        return yaml_path

    def _make_normal_yaml(self):
        """정상 통과 fixture — stub으로 모든 계층 exit 0."""
        yaml_path = self.project_root / ".opal" / "test-tools.yaml"
        for tool in ["eslint", "tsc", "vitest"]:
            stub = self.stub_dir / tool
            stub.write_text(
                '#!/bin/bash\n'
                'echo \'{"ok": true}\'\n'
                'exit 0\n'
            )
            stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        yaml_path.write_text(
            """
version: "2.0"
tiers:
  unit:
    be:
      lint:
        - name: eslint
          check: eslint .
          required: true
      typecheck:
        - name: tsc
          check: tsc --noEmit
          required: true
      unit:
        - name: vitest
          check: vitest run
"""
        )
        return yaml_path

    def test_unit_stop_on_fail_lint_blocks_build(self):
        """[T039/L1-unit] S-3 H-2: lint 실패 시 build/unit 미실행 + stopped_at=lint + exit≠0"""
        self._make_lint_fail_yaml()
        env = _env_with_stub_path(self.stub_dir)
        code, stdout, data = _run(
            ["unit", "--scope", "be", "--project-root", str(self.project_root)],
            env=env,
        )
        # exit code 는 0이어서는 안 됨
        self.assertNotEqual(code, 0, f"lint fail 시 exit≠0 expected. stdout={stdout}")
        layers = data.get("layers", [])
        # lint 계층은 fail
        lint_layers = [l for l in layers if l.get("name") == "lint"]
        self.assertTrue(len(lint_layers) > 0, f"layers에 lint 항목 없음. data={data}")
        self.assertEqual(
            lint_layers[0].get("status"), "fail",
            f"layers[lint].status should be fail. data={data}"
        )
        # build/unit은 실행되지 않아야 함(skip 또는 부재)
        build_layers = [l for l in layers if l.get("name") in ("build", "typecheck")]
        for bl in build_layers:
            self.assertNotEqual(
                bl.get("status"), "pass",
                f"build/typecheck 계층이 lint 실패 후 pass여서는 안 됨. data={data}"
            )
        unit_layers = [l for l in layers if l.get("name") == "unit"]
        for ul in unit_layers:
            self.assertNotEqual(
                ul.get("status"), "pass",
                f"unit 계층이 lint 실패 후 pass여서는 안 됨. data={data}"
            )
        # stopped_at 필드
        self.assertEqual(
            data.get("stopped_at"), "lint",
            f"stopped_at should be 'lint'. data={data}"
        )

    def test_unit_layer_order_lint_build_unit(self):
        """[T039/L1-unit] S-4 H-2: JSON layers 순서가 lint→build/typecheck→unit"""
        self._make_normal_yaml()
        env = _env_with_stub_path(self.stub_dir)
        code, stdout, data = _run(
            ["unit", "--scope", "be", "--project-root", str(self.project_root)],
            env=env,
        )
        layers = data.get("layers", [])
        self.assertTrue(len(layers) >= 2, f"layers가 2개 이상이어야 함. data={data}")
        names = [l.get("name") for l in layers]
        # lint가 첫 번째
        self.assertEqual(names[0], "lint", f"첫 번째 layer는 lint이어야 함. names={names}")
        # unit이 마지막 (typecheck/build보다 후)
        if "unit" in names:
            lint_idx = names.index("lint")
            unit_idx = names.index("unit")
            self.assertLess(lint_idx, unit_idx, f"lint가 unit보다 앞에 있어야 함. names={names}")

    def test_unit_no_watch_mode(self):
        """[T039/L1-unit] S-4 H-2: 실행 명령 문자열에 watch 플래그(--watch/-w) 없음(단발)
        RED 조건: run.sh 미구현 → exit 127 + layers=[] → 선행 단언(exit 0 및 layers 존재)에서 FAIL.
        GREEN 조건: unit 명령이 JSON layers를 반환하고 각 명령에 watch 플래그 없음.
        """
        self._make_normal_yaml()
        env = _env_with_stub_path(self.stub_dir)
        code, stdout, data = _run(
            ["unit", "--scope", "be", "--project-root", str(self.project_root)],
            env=env,
        )
        # 선행 단언: run.sh가 존재하고 정상 응답을 반환해야 함
        self.assertEqual(
            code, 0,
            f"unit(정상 fixture) exit 0 expected. stdout={stdout}"
        )
        layers = data.get("layers", [])
        self.assertTrue(
            len(layers) >= 1,
            f"layers가 1개 이상이어야 함(단발 실행 증거). data={data}"
        )
        # watch 플래그 부재 검증
        for layer in layers:
            cmd_str = layer.get("cmd", layer.get("command", ""))
            self.assertNotIn(
                "--watch", str(cmd_str),
                f"layer '{layer.get('name')}' cmd에 --watch 플래그 존재. data={data}"
            )
            self.assertNotRegex(
                str(cmd_str),
                r"\s-w\b",
                f"layer '{layer.get('name')}' cmd에 -w 플래그 존재. data={data}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# S-5: check 서브명령
# ─────────────────────────────────────────────────────────────────────────────

class TestCheck(unittest.TestCase):
    """[T039/L1-check] test-tool check 행위 계약 — S-5"""

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.project_root = self.tmpdir / "project"
        self.project_root.mkdir()
        opal_dir = self.project_root / ".opal"
        opal_dir.mkdir()
        self.stub_dir = self.tmpdir / "stubs"
        self.stub_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_check_yaml(self, required_tool, optional_tool):
        """required/optional 도구가 지정된 yaml fixture 생성."""
        yaml_path = self.project_root / ".opal" / "test-tools.yaml"
        yaml_path.write_text(
            f"""
version: "2.0"
tiers:
  unit:
    be:
      lint:
        - name: {required_tool}
          check: {required_tool} .
          required: true
      unit:
        - name: {optional_tool}
          check: {optional_tool} run
          required: false
"""
        )
        return yaml_path

    def test_check_required_blocks_optional_skips(self):
        """[T039/L1-check] S-5 H-5: required 미설치=blocked=true exit≠0 / optional 미설치=skip exit 0"""
        # required_tool: PATH에 존재하지 않는 임의 이름
        required_tool = "nonexistent_required_tool_039"
        # optional_tool: 마찬가지로 없는 도구
        optional_tool = "nonexistent_optional_tool_039"
        self._make_check_yaml(required_tool, optional_tool)

        # 1) required 미설치 → blocked=true exit≠0
        code_req, stdout_req, data_req = _run(
            ["check", "--tier", "unit", "--project-root", str(self.project_root)]
        )
        self.assertNotEqual(
            code_req, 0,
            f"required 미설치 시 exit≠0 expected. stdout={stdout_req}"
        )
        self.assertTrue(
            data_req.get("blocked"),
            f"blocked=true expected. data={data_req}"
        )

        # required_tool만 PATH에 설치된 stub 추가(optional은 여전히 없음)
        stub_req = self.stub_dir / required_tool
        stub_req.write_text("#!/bin/bash\nexit 0\n")
        stub_req.chmod(stub_req.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        env_with_req = _env_with_stub_path(self.stub_dir)

        # 2) optional만 미설치(required 설치됨) → exit 0
        code_opt, stdout_opt, data_opt = _run(
            ["check", "--tier", "unit", "--project-root", str(self.project_root)],
            env=env_with_req,
        )
        self.assertEqual(
            code_opt, 0,
            f"optional 미설치 시 exit 0 expected. stdout={stdout_opt}"
        )
        self.assertFalse(
            data_opt.get("blocked"),
            f"blocked=false expected. data={data_opt}"
        )
        # optional 도구의 results에 installed=false
        results = data_opt.get("results", [])
        optional_results = [r for r in results if r.get("name") == optional_tool]
        if optional_results:
            self.assertFalse(
                optional_results[0].get("installed"),
                f"optional tool installed should be false. data={data_opt}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# S-6: integration cmux 폴백 4종
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegrationCmuxFallback(unittest.TestCase):
    """[T039/L1-integration] test-tool integration cmux 폴백 4종 — S-6

    교정(S-15 실검증): cmux-tool 스텁 주입을 PATH 주입에서 OPAL_CMUX_TOOL_CMD 환경변수로 변경.
    e2e_adapter가 OPAL_CMUX_TOOL_CMD(env) → ~/.opal/tools/cmux-tool/run.sh(기본) 순으로
    cmux-tool을 호출해야 하는 실제 OPAL 호출 계약을 반영한다.
    기대 결과(driver=playwright on fallback)는 변경 없음 — 호출 메커니즘만 수정.
    """

    # cmux-tool 스텁이 반환할 폴백 트리거 에러코드 4종
    FALLBACK_CODES = [
        "not_in_cmux",
        "cmux_not_installed",
        "surface_parse_failed",
        "open_failed",
    ]

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.project_root = self.tmpdir / "project"
        self.project_root.mkdir()
        opal_dir = self.project_root / ".opal"
        opal_dir.mkdir()
        (opal_dir / "test-tools.yaml").write_text(
            """
version: "2.0"
tiers:
  integration:
    e2e:
      - name: cmux
        priority: 1
        via: cmux-tool
      - name: playwright
        priority: 2
        fallback: true
"""
        )
        self.stub_dir = self.tmpdir / "stubs"
        self.stub_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_cmux_tool_stub(self, error_code):
        """지정 error_code를 반환하는 cmux-tool stub 생성.
        스텁은 PATH 이름이 아닌 절대 경로(stub_dir/cmux-tool-stub)에 위치 —
        OPAL_CMUX_TOOL_CMD 환경변수로 주입.
        """
        stub_json = {"ok": False, "command": "open", "error": error_code}
        return _make_stub_script(self.stub_dir, "cmux-tool-stub", stub_json, exit_code=1)

    def _assert_playwright_fallback(self, error_code):
        stub_path = self._make_cmux_tool_stub(error_code)
        # PATH 주입 대신 OPAL_CMUX_TOOL_CMD로 stub 절대경로 주입
        env = _env_with_cmux_cmd(stub_path)
        code, stdout, data = _run(
            ["integration", "--url", "http://localhost:3000",
             "--project-root", str(self.project_root)],
            env=env,
        )
        e2e = data.get("e2e", {})
        self.assertEqual(
            e2e.get("driver"), "playwright",
            f"error_code={error_code}: e2e.driver should be playwright. data={data}"
        )
        self.assertIn(
            "fallback_reason", e2e,
            f"error_code={error_code}: fallback_reason 필드 없음. data={data}"
        )
        # fallback_reason에 에러 코드가 기록되어야 함
        self.assertIn(
            error_code, str(e2e.get("fallback_reason", "")),
            f"fallback_reason에 {error_code} 미포함. data={data}"
        )

    def test_integration_cmux_fallback_4codes(self):
        """[T039/L1-integration] S-6 H-3: cmux-tool stub이 폴백 4종 반환 시 e2e.driver=playwright
        OPAL_CMUX_TOOL_CMD 환경변수 경유로 stub 주입 (실제 OPAL 호출 계약 반영).
        subTest 외에 실패 카운트를 추적하여 메인 테스트도 FAIL 처리.
        """
        failures = []
        for error_code in self.FALLBACK_CODES:
            with self.subTest(error_code=error_code):
                try:
                    self._assert_playwright_fallback(error_code)
                except AssertionError as e:
                    failures.append(f"{error_code}: {e}")
        if failures:
            self.fail(
                f"폴백 4종 중 {len(failures)}건 실패:\n" + "\n".join(failures)
            )


# ─────────────────────────────────────────────────────────────────────────────
# S-7: integration cmux 에스컬레이션 5종
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegrationCmuxEscalate(unittest.TestCase):
    """[T039/L1-integration] test-tool integration cmux 에스컬레이션 5종 — S-7

    교정(S-15 실검증): cmux-tool 스텁 주입을 PATH 주입에서 OPAL_CMUX_TOOL_CMD 환경변수로 변경.
    기대 결과(escalate=true, playwright 폴백 금지, exit=7)는 변경 없음 — 호출 메커니즘만 수정.
    """

    ESCALATE_CODES = [
        "usage",
        "invalid_surface",
        "goto_failed",
        "wait_failed",
        "eval_failed",
    ]

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.project_root = self.tmpdir / "project"
        self.project_root.mkdir()
        opal_dir = self.project_root / ".opal"
        opal_dir.mkdir()
        (opal_dir / "test-tools.yaml").write_text(
            """
version: "2.0"
tiers:
  integration:
    e2e:
      - name: cmux
        priority: 1
        via: cmux-tool
      - name: playwright
        priority: 2
        fallback: true
"""
        )
        self.stub_dir = self.tmpdir / "stubs"
        self.stub_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_cmux_tool_stub(self, error_code):
        """지정 error_code를 반환하는 cmux-tool stub 생성.
        스텁은 PATH 이름이 아닌 절대 경로(stub_dir/cmux-tool-stub)에 위치 —
        OPAL_CMUX_TOOL_CMD 환경변수로 주입.
        """
        stub_json = {"ok": False, "command": "open", "error": error_code}
        return _make_stub_script(self.stub_dir, "cmux-tool-stub", stub_json, exit_code=1)

    def _assert_escalate(self, error_code):
        stub_path = self._make_cmux_tool_stub(error_code)
        # PATH 주입 대신 OPAL_CMUX_TOOL_CMD로 stub 절대경로 주입
        env = _env_with_cmux_cmd(stub_path)
        code, stdout, data = _run(
            ["integration", "--url", "http://localhost:3000",
             "--project-root", str(self.project_root)],
            env=env,
        )
        # exit code는 escalation(7)
        self.assertEqual(
            code, 7,
            f"error_code={error_code}: exit should be 7(escalation). got={code}. stdout={stdout}"
        )
        # escalate=true
        self.assertTrue(
            data.get("escalate"),
            f"error_code={error_code}: escalate should be true. data={data}"
        )
        # e2e.driver는 playwright여서는 안 됨(폴백 금지)
        e2e = data.get("e2e", {})
        self.assertNotEqual(
            e2e.get("driver"), "playwright",
            f"error_code={error_code}: 에스컬레이션 코드에 playwright 폴백 발생(헌법 위반). data={data}"
        )

    def test_integration_cmux_escalate_5codes(self):
        """[T039/L1-integration] S-7 H-3: 에스컬레이션 5종 → escalate=true + playwright 폴백 금지 + exit=7
        OPAL_CMUX_TOOL_CMD 환경변수 경유로 stub 주입 (실제 OPAL 호출 계약 반영).
        subTest 외에 실패 카운트를 추적하여 메인 테스트도 FAIL 처리.
        """
        failures = []
        for error_code in self.ESCALATE_CODES:
            with self.subTest(error_code=error_code):
                try:
                    self._assert_escalate(error_code)
                except AssertionError as e:
                    failures.append(f"{error_code}: {e}")
        if failures:
            self.fail(
                f"에스컬레이션 5종 중 {len(failures)}건 실패:\n" + "\n".join(failures)
            )


# ─────────────────────────────────────────────────────────────────────────────
# S-8: integration mode A open→navigate→close 시퀀스
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegrationModeA(unittest.TestCase):
    """[T039/L1-modeA] test-tool integration mode A 격리 시퀀스 — S-8

    교정(S-15 실검증): cmux-tool 스텁 주입을 PATH 주입에서 OPAL_CMUX_TOOL_CMD 환경변수로 변경.
    스텁은 여전히 호출 인자를 로그 파일에 기록하여 open→navigate→close 시퀀스 및
    --surface 미전달을 검증한다 — 검증 방식 유지, 호출 메커니즘만 수정.
    """

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.project_root = self.tmpdir / "project"
        self.project_root.mkdir()
        opal_dir = self.project_root / ".opal"
        opal_dir.mkdir()
        (opal_dir / "test-tools.yaml").write_text(
            """
version: "2.0"
tiers:
  integration:
    e2e:
      - name: cmux
        priority: 1
        via: cmux-tool
      - name: playwright
        priority: 2
        fallback: true
"""
        )
        self.stub_dir = self.tmpdir / "stubs"
        self.stub_dir.mkdir()
        # 호출 시퀀스 기록용 로그 파일
        self.call_log = self.tmpdir / "cmux_calls.log"

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_recording_cmux_tool_stub(self):
        """호출 인자를 로그 파일에 기록하고 성공 JSON을 반환하는 stub.
        스텁은 PATH 이름이 아닌 절대 경로(stub_dir/cmux-tool-stub)에 위치 —
        OPAL_CMUX_TOOL_CMD 환경변수로 주입.
        """
        call_log = str(self.call_log)
        # open 서브명령: surface 핸들 반환
        # navigate 서브명령: ok 반환
        # close 서브명령: ok 반환
        stub_path = self.stub_dir / "cmux-tool-stub"
        stub_path.write_text(
            f"""#!/bin/bash
# 모든 인자를 로그에 기록
echo "$@" >> "{call_log}"
SUBCMD="${{1:-}}"
case "$SUBCMD" in
  open)
    echo '{{"ok":true,"command":"open","surface":"mock-surface-123"}}'
    exit 0
    ;;
  navigate|goto)
    echo '{{"ok":true,"command":"navigate"}}'
    exit 0
    ;;
  close|tab-close)
    echo '{{"ok":true,"command":"close"}}'
    exit 0
    ;;
  *)
    echo '{{"ok":true,"command":"'$SUBCMD'"}}'
    exit 0
    ;;
esac
"""
        )
        stub_path.chmod(stub_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        return stub_path

    def test_integration_mode_a_open_close(self):
        """[T039/L1-modeA] S-8 H-4: cmux-tool 호출 시퀀스에 open→navigate→close 포함 + --surface 미전달
        OPAL_CMUX_TOOL_CMD 환경변수 경유로 stub 주입 (실제 OPAL 호출 계약 반영).
        """
        stub_path = self._make_recording_cmux_tool_stub()
        # PATH 주입 대신 OPAL_CMUX_TOOL_CMD로 stub 절대경로 주입
        env = _env_with_cmux_cmd(stub_path)
        code, stdout, data = _run(
            ["integration", "--url", "http://localhost:3000",
             "--project-root", str(self.project_root)],
            env=env,
        )
        # exit code는 0 또는 e2e_failed(6) — stub은 정상 응답
        self.assertIn(
            code, [0, 6],
            f"mode A 실행 후 exit 0 또는 6 expected. got={code}. stdout={stdout}"
        )

        # 로그 파일로 호출 시퀀스 검증
        if not self.call_log.exists():
            self.fail(
                f"cmux-tool이 호출되지 않았음(call_log 미생성). data={data}"
            )
        calls = self.call_log.read_text().strip().splitlines()

        subcmds = []
        for call in calls:
            parts = call.strip().split()
            if parts:
                subcmds.append(parts[0])

        # open이 호출되어야 함
        self.assertIn(
            "open", subcmds,
            f"cmux-tool open 호출 없음. subcmds={subcmds}"
        )

        # close가 open 이후에 호출되어야 함(mode A 격리)
        close_variants = {"close", "tab-close"}
        has_close = bool(close_variants & set(subcmds))
        self.assertTrue(
            has_close,
            f"cmux-tool close 호출 없음(mode A 격리 위반). subcmds={subcmds}"
        )

        open_idx = subcmds.index("open")
        close_idx = next(
            (i for i, s in enumerate(subcmds) if s in close_variants), None
        )
        self.assertGreater(
            close_idx, open_idx,
            f"close가 open보다 먼저 호출됨. subcmds={subcmds}"
        )

        # --surface 인자가 cmux-tool open 호출에 전달되지 않아야 함(신규 surface 강제)
        for call in calls:
            if call.strip().startswith("open"):
                self.assertNotIn(
                    "--surface", call,
                    f"mode A에서 --surface가 전달됨(사용자 surface 재사용 위반). call={call}"
                )


# ─────────────────────────────────────────────────────────────────────────────
# S-9: 모든 에러 응답의 error 값이 ERROR_CODES 카탈로그 키와 일치
# ─────────────────────────────────────────────────────────────────────────────

class TestErrorCodesInCatalog(unittest.TestCase):
    """[T039/L1-check][T039/L1-integration] S-9 H-3/H-5: error 값이 ERROR_CODES 카탈로그 키"""

    # PLAN §3.3.2 서브명령 계약에 명시된 에러 코드 카탈로그
    # 구현 후 test_tool.py의 ERROR_CODES dict 키와 일치해야 함
    EXPECTED_ERROR_CATALOG = {
        "venv_missing",      # run.sh venv 가드
        "yaml_parse_failed", # resolve: yaml 파싱 실패
        "no_runner",         # resolve: 러너 없음
        "required_missing",  # check: required 미설치
        "layer_failed",      # unit: 계층 실패
        "e2e_failed",        # integration: e2e 실패
        "escalation",        # integration: 에스컬레이션
    }

    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.project_root = self.tmpdir / "project"
        self.project_root.mkdir()
        opal_dir = self.project_root / ".opal"
        opal_dir.mkdir()
        self.stub_dir = self.tmpdir / "stubs"
        self.stub_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _collect_error_code(self, args, env=None):
        """서브명령을 실행하여 반환된 JSON의 error 값을 수집. None이면 에러 없음."""
        code, stdout, data = _run(args, env=env)
        if code != 0:
            return data.get("error")
        return None

    def test_error_codes_in_catalog(self):
        """[T039/L1-check][T039/L1-integration] S-9: 에러 경로에서 반환된 error 값이 카탈로그 키에 포함
        RED 조건: run.sh 미구현 → exit 127 + error=None → assertIsNotNone에서 FAIL.
        GREEN 조건: 각 에러 경로가 카탈로그 키 중 하나를 error 필드로 반환.
        """
        # 1) resolve: yaml 파싱 실패 유도 (깨진 yaml)
        broken_yaml_root = self.tmpdir / "broken"
        broken_yaml_root.mkdir()
        (broken_yaml_root / ".opal").mkdir()
        (broken_yaml_root / ".opal" / "test-tools.yaml").write_text(
            "version: 2.0\ntiers: [invalid: yaml: structure"
        )
        error_resolve = self._collect_error_code(
            ["resolve", "--project-root", str(broken_yaml_root)]
        )
        # 에러 경로이므로 error 필드가 반드시 존재해야 함
        self.assertIsNotNone(
            error_resolve,
            "resolve 깨진 yaml → error 필드 없음. run.sh가 구현되지 않았거나 에러 코드를 반환하지 않음"
        )
        self.assertIn(
            error_resolve, self.EXPECTED_ERROR_CATALOG,
            f"resolve 에러 코드 '{error_resolve}'가 카탈로그에 없음. catalog={self.EXPECTED_ERROR_CATALOG}"
        )

        # 2) check: required 미설치 유도
        (self.project_root / ".opal" / "test-tools.yaml").write_text(
            """
version: "2.0"
tiers:
  unit:
    be:
      lint:
        - name: nonexistent_required_039
          check: nonexistent_required_039 .
          required: true
"""
        )
        error_check = self._collect_error_code(
            ["check", "--tier", "unit", "--project-root", str(self.project_root)]
        )
        self.assertIsNotNone(
            error_check,
            "check required 미설치 → error 필드 없음. run.sh가 구현되지 않았거나 에러 코드를 반환하지 않음"
        )
        self.assertIn(
            error_check, self.EXPECTED_ERROR_CATALOG,
            f"check 에러 코드 '{error_check}'가 카탈로그에 없음. catalog={self.EXPECTED_ERROR_CATALOG}"
        )

        # 3) integration: 에스컬레이션 에러코드 유도 (goto_failed)
        #    교정(S-15 실검증): OPAL_CMUX_TOOL_CMD 환경변수로 stub 절대경로 주입
        (self.project_root / ".opal" / "test-tools.yaml").write_text(
            """
version: "2.0"
tiers:
  integration:
    e2e:
      - name: cmux
        priority: 1
        via: cmux-tool
"""
        )
        stub_json = {"ok": False, "command": "open", "error": "goto_failed"}
        stub_path_s9 = _make_stub_script(self.stub_dir, "cmux-tool-stub", stub_json, exit_code=1)
        env = _env_with_cmux_cmd(stub_path_s9)
        error_integration = self._collect_error_code(
            ["integration", "--url", "http://localhost:3000",
             "--project-root", str(self.project_root)],
            env=env,
        )
        self.assertIsNotNone(
            error_integration,
            "integration goto_failed → error 필드 없음. run.sh가 구현되지 않았거나 에러 코드를 반환하지 않음"
        )
        self.assertIn(
            error_integration, self.EXPECTED_ERROR_CATALOG,
            f"integration 에러 코드 '{error_integration}'가 카탈로그에 없음. catalog={self.EXPECTED_ERROR_CATALOG}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
