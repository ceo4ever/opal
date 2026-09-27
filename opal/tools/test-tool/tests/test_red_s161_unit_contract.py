"""
@header {
  "module": "test_red_s161_unit_contract",
  "task": "161",
  "layer": "test",
  "domain": "opal-tools",
  "description": "RED-first public CLI contract tests for task 161 unit execution accuracy recovery (D-1~D-10). Verifies run/check separation, stop-on-fail not_run marking, file scope, required vs optional layers, and resolve source_path via `bash opal/tools/test-tool/run.sh` subprocess stdout JSON + exit only.",
  "scenarios": ["S-1", "S-2", "S-3", "S-4", "S-5", "S-6", "S-7", "S-8"],
  "exports": [
    "TestS1RunMissingNotConfigured",
    "TestS2CheckVsRunSeparation",
    "TestS3StopOnFailNotRun",
    "TestS4EmptyLayersAndNoMatchingFiles",
    "TestS5FileScope",
    "TestS6EvidenceFields",
    "TestS7RequiredOptionalLayers",
    "TestS8TemplateAndInferenceCommands"
  ]
}

[T161] test-tool unit 실행 정확성 복구 — 구현 전 RED 계약 테스트.
검증 대상: opal/tools/test-tool/run.sh 의 공개 인터페이스(exit code + stdout JSON)만 단언.
내부 구현/private 결합 금지(red-first.md §2, §4).

PLAN.md Decisions and contracts D-1~D-10을 원문 그대로 단언한다:
- D-2: run 없으면 not_configured(run_missing), check 실패는 tool_unavailable(install_check_failed).
- D-4: 계층 status ∈ {pass, fail, tool_unavailable, not_configured, not_applicable, not_run}.
        전체 status ∈ {pass, fail, incomplete}.
- D-3: scope {kind, requested, checked, excluded:[{path, reason}], reason}.
- D-5: required: false 계층의 tool_unavailable/not_configured는 전체를 incomplete로 만들지 않는다.
- D-6: pass→exit 0, fail→exit 5/layer_failed, incomplete→exit 21/unit_incomplete.
- D-7: 최상위 cwd(절대경로), config{source,path}, requested_files, layers, stopped_at.
       계층 name, tool, required, status, reason, check{cmd,exit,status}, cmd, exit, stdout, scope.
       resolve 응답에 source_path.
- D-10: 전역 템플릿/추론 명령이 ruff check .·mypy .·pytest·npx eslint .·npx tsc --noEmit·npx vitest run이다.

GREEN 구현은 이 파일을 수정하지 않고 통과시킨다(구현 워커는 계약을 약화·삭제하지 않는다).
"""

import json
import os
import pathlib
import stat
import subprocess
import tempfile
import unittest

_TOOL_DIR = pathlib.Path(__file__).parent.parent
_RUN_SH = _TOOL_DIR / "run.sh"
_REPO_ROOT = _TOOL_DIR.parent.parent.parent  # opal/tools/test-tool -> repo root
_GLOBAL_TEMPLATE = _REPO_ROOT / "opal" / "templates" / "test-tools.yaml"


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


def _isolated_env(extra=None):
    """OPAL_TEST_TOOLS_GLOBAL을 제거한 격리 환경(전역 템플릿 개입 차단)."""
    env = os.environ.copy()
    env.pop("OPAL_TEST_TOOLS_GLOBAL", None)
    if extra:
        env.update(extra)
    return env


def _make_stub(stub_dir, name, exit_code=0, marker_name=None):
    """호출되면 marker 파일을 생성하고 argv를 marker에 기록한 뒤 exit_code로 끝나는 stub."""
    stub_path = stub_dir / name
    marker = stub_dir / (marker_name or f"{name}.marker")
    script = f"""#!/bin/bash
echo "$@" > "{marker}"
exit {exit_code}
"""
    stub_path.write_text(script)
    stub_path.chmod(stub_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return stub_path, marker


def _write_project_yaml(project_root, tiers_yaml_body):
    opal_dir = project_root / ".opal"
    opal_dir.mkdir(parents=True, exist_ok=True)
    (opal_dir / "test-tools.yaml").write_text(
        "version: \"2.0\"\n" + tiers_yaml_body, encoding="utf-8"
    )


# ─────────────────────────────────────────────────────────────────────────────
# S-1: run 없는 구형 설정 — not_configured/run_missing, check 미실행, run 대체 미실행
# ─────────────────────────────────────────────────────────────────────────────

class TestS1RunMissingNotConfigured(unittest.TestCase):
    def test_s1_legacy_check_only_config_is_not_configured_and_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            stub_path, marker = _make_stub(project_root, "lint_stub.sh", exit_code=0)
            _write_project_yaml(
                project_root,
                f"""tiers:
  unit:
    be:
      lint:
        - name: legacy-lint
          check: "{stub_path} ."
          required: true
""",
            )
            returncode, stdout, data = _run(
                ["unit", "--scope", "be", "--project-root", str(project_root)],
                env=_isolated_env(),
            )

            self.assertEqual(returncode, 21, msg=f"stdout={stdout}")
            self.assertFalse(data.get("ok"))
            self.assertEqual(data.get("status"), "incomplete")
            self.assertEqual(data.get("error"), "unit_incomplete")

            layers = data.get("layers", [])
            lint_layer = next((layer for layer in layers if layer.get("name") == "lint"), None)
            self.assertIsNotNone(lint_layer, msg=f"layers={layers}")
            self.assertEqual(lint_layer.get("status"), "not_configured")
            self.assertEqual(lint_layer.get("reason"), "run_missing")
            self.assertIsNone(lint_layer.get("cmd"))
            self.assertIn("hint", lint_layer)

            self.assertFalse(marker.exists(), msg="check를 실행하지도, run으로 대체 실행하지도 않아야 한다")


# ─────────────────────────────────────────────────────────────────────────────
# S-2: 이관된 설정 — check(설치 확인)와 run(실제 검사) 분리 실행
# ─────────────────────────────────────────────────────────────────────────────

class TestS2CheckVsRunSeparation(unittest.TestCase):
    def test_s2a_check_pass_run_pass_yields_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            check_stub, check_marker = _make_stub(project_root, "check_ok.sh", exit_code=0)
            run_stub, run_marker = _make_stub(project_root, "run_ok.sh", exit_code=0)
            _write_project_yaml(
                project_root,
                f"""tiers:
  unit:
    be:
      lint:
        - name: migrated-lint
          check: "{check_stub}"
          run: "{run_stub}"
          required: true
""",
            )
            returncode, stdout, data = _run(
                ["unit", "--scope", "be", "--project-root", str(project_root)],
                env=_isolated_env(),
            )

            self.assertEqual(returncode, 0, msg=f"stdout={stdout}")
            self.assertEqual(data.get("status"), "pass")
            lint_layer = next(layer for layer in data.get("layers", []) if layer.get("name") == "lint")
            self.assertEqual(lint_layer.get("status"), "pass")
            self.assertEqual(lint_layer.get("check", {}).get("exit"), 0)
            self.assertEqual(lint_layer.get("cmd"), str(run_stub))
            self.assertTrue(check_marker.exists())
            self.assertTrue(run_marker.exists())

    def test_s2b_check_fail_yields_tool_unavailable_without_running_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            check_stub, check_marker = _make_stub(project_root, "check_fail.sh", exit_code=1)
            run_stub, run_marker = _make_stub(project_root, "run_marker.sh", exit_code=0)
            _write_project_yaml(
                project_root,
                f"""tiers:
  unit:
    be:
      lint:
        - name: migrated-lint
          check: "{check_stub}"
          run: "{run_stub}"
          required: true
""",
            )
            returncode, stdout, data = _run(
                ["unit", "--scope", "be", "--project-root", str(project_root)],
                env=_isolated_env(),
            )

            self.assertEqual(returncode, 21, msg=f"stdout={stdout}")
            lint_layer = next(layer for layer in data.get("layers", []) if layer.get("name") == "lint")
            self.assertEqual(lint_layer.get("status"), "tool_unavailable")
            self.assertEqual(lint_layer.get("reason"), "install_check_failed")
            self.assertEqual(lint_layer.get("check", {}).get("exit"), 1)
            self.assertFalse(run_marker.exists(), msg="check 실패 시 run은 실행되지 않아야 한다")
            # S-3(검사 실패, exit 5/fail)와 상태·exit가 달라야 한다
            self.assertNotEqual(returncode, 5)
            self.assertNotEqual(data.get("status"), "fail")


# ─────────────────────────────────────────────────────────────────────────────
# S-3: stop-on-fail — 실패 후 계층은 not_run/stopped_after_failure로 남고 미실행
# ─────────────────────────────────────────────────────────────────────────────

class TestS3StopOnFailNotRun(unittest.TestCase):
    def test_s3_lint_fail_stops_remaining_layers_as_not_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            lint_run, _ = _make_stub(project_root, "lint_run.sh", exit_code=1)
            typecheck_run, typecheck_marker = _make_stub(project_root, "typecheck_run.sh", exit_code=0)
            unit_run, unit_marker = _make_stub(project_root, "unit_run.sh", exit_code=0)
            _write_project_yaml(
                project_root,
                f"""tiers:
  unit:
    be:
      lint:
        - name: lint-tool
          run: "{lint_run}"
          required: true
      typecheck:
        - name: typecheck-tool
          run: "{typecheck_run}"
          required: true
      unit:
        - name: unit-tool
          run: "{unit_run}"
          required: true
""",
            )
            returncode, stdout, data = _run(
                ["unit", "--scope", "be", "--project-root", str(project_root)],
                env=_isolated_env(),
            )

            self.assertEqual(returncode, 5, msg=f"stdout={stdout}")
            self.assertEqual(data.get("status"), "fail")
            self.assertEqual(data.get("error"), "layer_failed")
            self.assertEqual(data.get("stopped_at"), "lint")

            layers = {layer["name"]: layer for layer in data.get("layers", [])}
            self.assertIn("typecheck", layers)
            self.assertIn("unit", layers)
            self.assertEqual(layers["typecheck"].get("status"), "not_run")
            self.assertEqual(layers["typecheck"].get("reason"), "stopped_after_failure")
            self.assertIsNone(layers["typecheck"].get("cmd"))
            self.assertEqual(layers["unit"].get("status"), "not_run")
            self.assertEqual(layers["unit"].get("reason"), "stopped_after_failure")
            self.assertIsNone(layers["unit"].get("cmd"))

            self.assertFalse(typecheck_marker.exists())
            self.assertFalse(unit_marker.exists())


# ─────────────────────────────────────────────────────────────────────────────
# S-4: 빈 계층 선언과 매칭 파일 없음 — incomplete
# ─────────────────────────────────────────────────────────────────────────────

class TestS4EmptyLayersAndNoMatchingFiles(unittest.TestCase):
    def test_s4a_empty_fe_tiers_is_incomplete_no_layers_declared(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            _write_project_yaml(
                project_root,
                """tiers:
  unit:
    fe: {}
""",
            )
            returncode, stdout, data = _run(
                ["unit", "--scope", "fe", "--project-root", str(project_root)],
                env=_isolated_env(),
            )

            self.assertEqual(returncode, 21, msg=f"stdout={stdout}")
            self.assertEqual(data.get("status"), "incomplete")
            self.assertEqual(data.get("reason"), "no_layers_declared")

    def test_s4b_changed_files_matching_no_glob_yields_not_applicable(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            lint_run, marker = _make_stub(project_root, "lint_run_files.sh", exit_code=0)
            (project_root / "README.md").write_text("x", encoding="utf-8")
            _write_project_yaml(
                project_root,
                f"""tiers:
  unit:
    be:
      lint:
        - name: lint-tool
          run: "{lint_run}"
          run_files: "{lint_run} {{files}}"
          file_globs: ["*.py"]
          required: true
""",
            )
            returncode, stdout, data = _run(
                [
                    "unit", "--scope", "be",
                    "--project-root", str(project_root),
                    "--changed-files", "README.md",
                ],
                env=_isolated_env(),
            )

            self.assertEqual(returncode, 21, msg=f"stdout={stdout}")
            layers = data.get("layers", [])
            for layer in layers:
                self.assertEqual(layer.get("status"), "not_applicable")
                self.assertEqual(layer.get("reason"), "no_matching_files")
            self.assertEqual(data.get("reason"), "no_check_executed")
            self.assertFalse(marker.exists(), msg="어떤 stub도 호출되지 않아야 한다")


# ─────────────────────────────────────────────────────────────────────────────
# S-5: 파일 범위 — run_files/file_globs 지원 계층과 미지원 계층 분기
# ─────────────────────────────────────────────────────────────────────────────

class TestS5FileScope(unittest.TestCase):
    def test_s5_file_scope_excludes_and_checked_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            lint_run, _ = _make_stub(project_root, "lint_project.sh", exit_code=0)
            lint_run_files, lint_marker = _make_stub(project_root, "lint_files.sh", exit_code=0)
            typecheck_run, typecheck_marker = _make_stub(project_root, "typecheck_project.sh", exit_code=0)
            (project_root / "a.py").write_text("x = 1\n", encoding="utf-8")
            (project_root / "b.md").write_text("doc\n", encoding="utf-8")
            _write_project_yaml(
                project_root,
                f"""tiers:
  unit:
    be:
      lint:
        - name: lint-tool
          run: "{lint_run}"
          run_files: "{lint_run_files} {{files}}"
          file_globs: ["*.py"]
          required: true
      typecheck:
        - name: typecheck-tool
          run: "{typecheck_run}"
          required: true
""",
            )
            returncode, stdout, data = _run(
                [
                    "unit", "--scope", "be",
                    "--project-root", str(project_root),
                    "--changed-files", "a.py", "b.md", "gone.py", "../outside.py",
                ],
                env=_isolated_env(),
            )

            self.assertEqual(data.get("requested_files"), ["a.py", "b.md", "gone.py", "../outside.py"])

            layers = {layer["name"]: layer for layer in data.get("layers", [])}
            lint_scope = layers["lint"].get("scope", {})
            self.assertEqual(lint_scope.get("kind"), "files")
            self.assertEqual(sorted(lint_scope.get("requested", [])), sorted(["a.py", "b.md", "gone.py", "../outside.py"]))
            self.assertEqual(lint_scope.get("checked"), ["a.py"])
            excluded = {e["path"]: e["reason"] for e in lint_scope.get("excluded", [])}
            self.assertEqual(excluded.get("b.md"), "pattern_mismatch")
            self.assertEqual(excluded.get("gone.py"), "missing")
            self.assertEqual(excluded.get("../outside.py"), "outside_project")

            self.assertTrue(lint_marker.exists())
            lint_argv = lint_marker.read_text(encoding="utf-8").strip()
            self.assertIn("a.py", lint_argv)
            self.assertNotIn("b.md", lint_argv)
            self.assertNotIn("gone.py", lint_argv)

            typecheck_scope = layers["typecheck"].get("scope", {})
            self.assertEqual(typecheck_scope.get("kind"), "project")
            self.assertEqual(typecheck_scope.get("reason"), "file_scope_unsupported")
            self.assertTrue(typecheck_marker.exists())
            typecheck_argv = typecheck_marker.read_text(encoding="utf-8").strip()
            self.assertEqual(typecheck_argv, "", msg="typecheck stub에는 파일 인자가 없어야 한다")


# ─────────────────────────────────────────────────────────────────────────────
# S-6: 증거 필드 — cwd, config{source,path}, 계층 필드, resolve source_path
# ─────────────────────────────────────────────────────────────────────────────

class TestS6EvidenceFields(unittest.TestCase):
    def test_s6_project_source_unit_evidence_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            lint_run, _ = _make_stub(project_root, "lint_run.sh", exit_code=0)
            _write_project_yaml(
                project_root,
                f"""tiers:
  unit:
    be:
      lint:
        - name: lint-tool
          run: "{lint_run}"
          required: true
""",
            )
            returncode, stdout, data = _run(
                ["unit", "--scope", "be", "--project-root", str(project_root)],
                env=_isolated_env(),
            )
            self.assertEqual(returncode, 0, msg=f"stdout={stdout}")
            self.assertEqual(data.get("cwd"), str(project_root))
            self.assertEqual(data.get("config", {}).get("source"), "project")
            self.assertEqual(
                data.get("config", {}).get("path"),
                str(project_root / ".opal" / "test-tools.yaml"),
            )
            lint_layer = next(layer for layer in data.get("layers", []) if layer.get("name") == "lint")
            for field in ("name", "tool", "required", "status", "cmd", "exit", "stdout", "scope"):
                self.assertIn(field, lint_layer, msg=f"missing field {field} in {lint_layer}")

    def test_s6_resolve_source_path_for_project_global_infer(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)

            # project 출처
            _write_project_yaml(
                project_root,
                """tiers:
  unit:
    be:
      lint:
        - name: lint-tool
          run: "true"
          required: true
""",
            )
            returncode, stdout, data = _run(
                ["resolve", "--project-root", str(project_root)],
                env=_isolated_env(),
            )
            self.assertEqual(returncode, 0, msg=f"stdout={stdout}")
            self.assertEqual(data.get("source"), "project")
            self.assertEqual(data.get("source_path"), str(project_root / ".opal" / "test-tools.yaml"))

        with tempfile.TemporaryDirectory() as tmp2:
            project_root2 = pathlib.Path(tmp2)
            returncode, stdout, data = _run(
                ["resolve", "--project-root", str(project_root2)],
                env=_isolated_env({"OPAL_TEST_TOOLS_GLOBAL": str(_GLOBAL_TEMPLATE)}),
            )
            self.assertEqual(returncode, 0, msg=f"stdout={stdout}")
            self.assertEqual(data.get("source"), "global")
            self.assertEqual(data.get("source_path"), str(_GLOBAL_TEMPLATE))

        with tempfile.TemporaryDirectory() as tmp3:
            project_root3 = pathlib.Path(tmp3)
            (project_root3 / "pyproject.toml").write_text("[project]\nname = \"x\"\n", encoding="utf-8")
            returncode, stdout, data = _run(
                ["resolve", "--project-root", str(project_root3)],
                env=_isolated_env(),
            )
            self.assertEqual(returncode, 0, msg=f"stdout={stdout}")
            self.assertEqual(data.get("source"), "infer")
            self.assertEqual(data.get("source_path"), str(project_root3 / "pyproject.toml"))


# ─────────────────────────────────────────────────────────────────────────────
# S-7: required 여부 — optional 계층 미설정은 incomplete로 만들지 않는다
# ─────────────────────────────────────────────────────────────────────────────

class TestS7RequiredOptionalLayers(unittest.TestCase):
    def test_s7a_optional_a11y_not_configured_does_not_block_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            lint_run, _ = _make_stub(project_root, "lint_run.sh", exit_code=0)
            _write_project_yaml(
                project_root,
                f"""tiers:
  unit:
    fe:
      lint:
        - name: lint-tool
          run: "{lint_run}"
          required: true
      a11y:
        - name: a11y-tool
          required: false
""",
            )
            returncode, stdout, data = _run(
                ["unit", "--scope", "fe", "--project-root", str(project_root)],
                env=_isolated_env(),
            )
            self.assertEqual(returncode, 0, msg=f"stdout={stdout}")
            self.assertEqual(data.get("status"), "pass")
            a11y_layer = next(layer for layer in data.get("layers", []) if layer.get("name") == "a11y")
            self.assertEqual(a11y_layer.get("status"), "not_configured")

    def test_s7b_required_a11y_not_configured_makes_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            lint_run, _ = _make_stub(project_root, "lint_run.sh", exit_code=0)
            _write_project_yaml(
                project_root,
                f"""tiers:
  unit:
    fe:
      lint:
        - name: lint-tool
          run: "{lint_run}"
          required: true
      a11y:
        - name: a11y-tool
          required: true
""",
            )
            returncode, stdout, data = _run(
                ["unit", "--scope", "fe", "--project-root", str(project_root)],
                env=_isolated_env(),
            )
            self.assertEqual(returncode, 21, msg=f"stdout={stdout}")
            self.assertEqual(data.get("status"), "incomplete")
            self.assertEqual(data.get("reason"), "required_layer_unverified")


# ─────────────────────────────────────────────────────────────────────────────
# S-8: 전역 템플릿·추론 명령 — D-10 실제 검사 명령
# ─────────────────────────────────────────────────────────────────────────────

class TestS8TemplateAndInferenceCommands(unittest.TestCase):
    def test_s8a_global_template_has_run_distinct_from_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            returncode, stdout, data = _run(
                ["resolve", "--project-root", str(project_root)],
                env=_isolated_env({"OPAL_TEST_TOOLS_GLOBAL": str(_GLOBAL_TEMPLATE)}),
            )
            self.assertEqual(returncode, 0, msg=f"stdout={stdout}")
            unit_tiers = data.get("tiers", {}).get("unit", {})
            ruff_found = False
            for scope_val in unit_tiers.values():
                if not isinstance(scope_val, dict):
                    continue
                for tool_list in scope_val.values():
                    if not isinstance(tool_list, list):
                        continue
                    for tool in tool_list:
                        if not isinstance(tool, dict):
                            continue
                        if tool.get("required") is not False:
                            self.assertIn(
                                "run", tool,
                                msg=f"required tool missing run: {tool}",
                            )
                            if "check" in tool:
                                self.assertNotEqual(tool.get("check"), tool.get("run"))
                        if tool.get("name") == "ruff":
                            ruff_found = True
                            self.assertEqual(tool.get("run"), "ruff check .")
            self.assertTrue(ruff_found, msg="global template must declare ruff tool")

            integration = data.get("tiers", {}).get("integration", {})
            api_db = integration.get("be", {}).get("api_db", [])
            pytest_tool = next((t for t in api_db if t.get("name") == "pytest"), None)
            self.assertIsNotNone(pytest_tool, msg=f"api_db={api_db}")
            self.assertEqual(pytest_tool.get("run"), "pytest")

            self.assertNotIn("ruff .", stdout)

    def test_s8b_pyproject_inference_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            (project_root / "pyproject.toml").write_text("[project]\nname = \"x\"\n", encoding="utf-8")
            returncode, stdout, data = _run(
                ["resolve", "--project-root", str(project_root)],
                env=_isolated_env(),
            )
            self.assertEqual(returncode, 0, msg=f"stdout={stdout}")
            be = data.get("tiers", {}).get("unit", {}).get("be", {})
            lint_tool = be.get("lint", [{}])[0]
            typecheck_tool = be.get("typecheck", [{}])[0]
            unit_tool = be.get("unit", [{}])[0]
            self.assertEqual(lint_tool.get("run"), "ruff check .")
            self.assertIn("{files}", lint_tool.get("run_files", ""))
            self.assertEqual(typecheck_tool.get("run"), "mypy .")
            self.assertEqual(unit_tool.get("run"), "pytest")
            self.assertNotIn("ruff .", stdout)

    def test_s8c_package_json_inference_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_root = pathlib.Path(tmp)
            pkg = {
                "name": "x",
                "devDependencies": {
                    "eslint": "^9.0.0",
                    "typescript": "^5.0.0",
                    "vitest": "^2.0.0",
                },
            }
            (project_root / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
            returncode, stdout, data = _run(
                ["resolve", "--project-root", str(project_root)],
                env=_isolated_env(),
            )
            self.assertEqual(returncode, 0, msg=f"stdout={stdout}")
            fe = data.get("tiers", {}).get("unit", {}).get("fe", {})
            eslint_tool = fe.get("lint", [{}])[0]
            tsc_tool = fe.get("typecheck", [{}])[0]
            vitest_tool = fe.get("unit", [{}])[0]
            self.assertEqual(eslint_tool.get("run"), "npx eslint .")
            self.assertEqual(tsc_tool.get("run"), "npx tsc --noEmit")
            self.assertEqual(vitest_tool.get("run"), "npx vitest run")
            self.assertNotIn("ruff .", stdout)


if __name__ == "__main__":
    unittest.main()
