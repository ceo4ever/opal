"""
@header {
  "module": "test_ego_browser_tool",
  "task": "129",
  "layer": "test",
  "domain": "opal-tools",
  "description": "ego-browser-tool public CLI contract tests for install handoff, verified installation gates, and sentinel-based smoke assertions.",
  "scenarios": ["S-2", "S-4", "S-5"],
  "exports": ["TestEgoBrowserToolContract"]
}

Tests use only the run.sh CLI, process environment, exit code, and stdout JSON.
The environment variables are explicit command/path seams for deterministic tests;
they do not bypass the observable verification sequence.
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


_TOOL_DIR = pathlib.Path(__file__).parent.parent
_RUN_SH = _TOOL_DIR / "run.sh"


def _run(args, env=None):
    result = subprocess.run(
        ["bash", str(_RUN_SH), *args],
        capture_output=True,
        text=True,
        env=env,
    )
    stdout = result.stdout.strip()
    try:
        data = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError:
        data = {"_raw": stdout}
    return result.returncode, stdout, data


def _write_script(path, body):
    path.write_text("#!/bin/bash\nset -eu\n" + body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return path


class TestEgoBrowserToolContract(unittest.TestCase):
    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_missing_cli_returns_structured_resumable_install_choice(self):
        env = os.environ.copy()
        env["OPAL_EGO_PLATFORM"] = "darwin"
        env["OPAL_EGO_ARCH"] = "arm64"
        env["OPAL_EGO_CLI_CMD"] = str(self.tmpdir / "missing-ego-browser")

        code, stdout, data = _run(
            ["smoke", "https://example.com", "--expect-text", "Example Domain"],
            env=env,
        )

        self.assertEqual(code, 20, stdout)
        self.assertEqual(data.get("status"), "awaiting_human", data)
        self.assertEqual(data.get("operational_status"), "awaiting_human", data)
        handoff = data.get("handoff", {})
        self.assertEqual(handoff.get("choices"), ["manual", "r2", "cancel"], data)
        resume = handoff.get("resume", {})
        self.assertEqual(resume.get("url"), "https://example.com", data)
        self.assertEqual(resume.get("expect_text"), "Example Domain", data)
        self.assertIn("resume_token", handoff, data)

    def _installer_env(self, *, verify_exit=0, codesign_exit=0, spctl_exit=0, good_hash=True):
        fixture = self.tmpdir / "ego-lite.dmg"
        fixture.write_bytes(b"verified ego fixture")
        digest = hashlib.sha256(fixture.read_bytes()).hexdigest()
        if not good_hash:
            digest = "0" * 64

        mount = self.tmpdir / "mount"
        app = mount / "ego lite.app"
        app.mkdir(parents=True)
        (app / "fixture.txt").write_text("signed", encoding="utf-8")
        install_root = self.tmpdir / "Applications"
        command_log = self.tmpdir / "install-commands.log"
        hdiutil = _write_script(
            self.tmpdir / "hdiutil-stub",
            f'''echo "$*" >> "{command_log}"
if [ "$1" = "verify" ]; then exit {verify_exit}; fi
if [ "$1" = "attach" ]; then printf '%s\\n' "{mount}"; exit 0; fi
exit 0
''',
        )
        codesign = _write_script(
            self.tmpdir / "codesign-stub",
            f'''echo "codesign $*" >> "{command_log}"
exit {codesign_exit}
''',
        )
        spctl = _write_script(
            self.tmpdir / "spctl-stub",
            f'''echo "spctl $*" >> "{command_log}"
exit {spctl_exit}
''',
        )
        manifest = self.tmpdir / "manifest.json"
        manifest.write_text(
            json.dumps({
                "version": "0.4.5.9",
                "platforms": {
                    "darwin-arm64": {
                        "url": "https://example.invalid/ego-lite.dmg",
                        "sha256": digest,
                    }
                },
            }),
            encoding="utf-8",
        )
        env = os.environ.copy()
        env.update({
            "OPAL_EGO_PLATFORM": "darwin",
            "OPAL_EGO_ARCH": "arm64",
            "OPAL_EGO_DMG_PATH": str(fixture),
            "OPAL_EGO_MANIFEST_PATH": str(manifest),
            "OPAL_EGO_HDIUTIL_CMD": str(hdiutil),
            "OPAL_EGO_CODESIGN_CMD": str(codesign),
            "OPAL_EGO_SPCTL_CMD": str(spctl),
            "OPAL_EGO_INSTALL_ROOT": str(install_root),
        })
        return env, command_log, install_root

    def test_install_rejects_unsupported_platform_and_every_verification_failure(self):
        unsupported = os.environ.copy()
        unsupported["OPAL_EGO_PLATFORM"] = "linux"
        unsupported["OPAL_EGO_ARCH"] = "x86_64"
        code, stdout, data = _run(["install"], env=unsupported)
        self.assertEqual(code, 18, stdout)
        self.assertEqual(data.get("status"), "provider_unavailable", data)

        cases = [
            ("hash", {"good_hash": False}),
            ("hdiutil", {"verify_exit": 1}),
            ("codesign", {"codesign_exit": 1}),
            ("spctl", {"spctl_exit": 1}),
        ]
        for name, kwargs in cases:
            with self.subTest(gate=name):
                case_dir = self.tmpdir / name
                case_dir.mkdir()
                original = self.tmpdir
                self.tmpdir = case_dir
                try:
                    env, _log, install_root = self._installer_env(**kwargs)
                    code, stdout, data = _run(["install"], env=env)
                    self.assertNotEqual(code, 0, stdout)
                    self.assertIn(data.get("status"), {"blocked", "infra_error"}, data)
                    self.assertFalse((install_root / "ego lite.app").exists(), data)
                finally:
                    self.tmpdir = original

    def test_install_copies_only_after_verify_hash_signature_and_notarization(self):
        env, command_log, install_root = self._installer_env()
        code, stdout, data = _run(["install"], env=env)

        self.assertEqual(code, 20, stdout)
        self.assertEqual(data.get("status"), "awaiting_human", data)
        self.assertEqual(data.get("version"), "0.4.5.9", data)
        self.assertTrue((install_root / "ego lite.app").is_dir(), data)
        commands = command_log.read_text(encoding="utf-8")
        self.assertIn("verify", commands)
        self.assertIn("codesign --verify --deep --strict", commands)
        self.assertIn("spctl --assess", commands)
        self.assertNotIn("xattr", commands)

    def test_smoke_normalizes_sentinel_assertions_and_rejects_malformed_output(self):
        cases = [
            (
                "pass",
                '__OPAL_EGO_RESULT__={"status":"pass","space_id":"space-1","actual":"Example Domain"}',
                False,
                0,
                "pass",
            ),
            (
                "pass-stderr",
                '__OPAL_EGO_RESULT__={"status":"pass","space_id":"space-stderr","actual":"Example Domain"}',
                True,
                0,
                "pass",
            ),
            (
                "assertion-fail",
                '__OPAL_EGO_RESULT__={"status":"pass","space_id":"space-2","actual":"Different"}',
                False,
                6,
                "fail",
            ),
            ("missing-sentinel", "ordinary ego log", False, 7, "infra_error"),
            (
                "duplicate-sentinel",
                '__OPAL_EGO_RESULT__={"status":"pass","space_id":"a","actual":"Example Domain"}\n'
                '__OPAL_EGO_RESULT__={"status":"pass","space_id":"b","actual":"Example Domain"}',
                False,
                7,
                "infra_error",
            ),
        ]
        for name, output, to_stderr, expected_exit, expected_status in cases:
            with self.subTest(case=name):
                redirect = " >&2" if to_stderr else ""
                stub = _write_script(
                    self.tmpdir / f"ego-{name}",
                    "printf '%s\\n' " + json.dumps(output) + redirect + "\n",
                )
                env = os.environ.copy()
                env["OPAL_EGO_PLATFORM"] = "darwin"
                env["OPAL_EGO_ARCH"] = "arm64"
                env["OPAL_EGO_CLI_CMD"] = str(stub)
                code, stdout, data = _run(
                    ["smoke", "https://example.com", "--expect-text", "Example Domain"],
                    env=env,
                )
                self.assertEqual(code, expected_exit, stdout)
                self.assertEqual(data.get("status"), expected_status, data)
                serialized = json.dumps(data, ensure_ascii=False).lower()
                self.assertNotIn("cookie", serialized)
                self.assertNotIn("token-value", serialized)
                if expected_status in {"pass", "fail"}:
                    self.assertEqual(data.get("expected"), "Example Domain", data)
                    self.assertIn("actual", data)
                    self.assertIn("space_id", data)


if __name__ == "__main__":
    unittest.main()
