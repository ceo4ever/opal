"""
@header {
  "module": "test_event_loader_security",
  "layer": "test",
  "domain": "opal-tools",
  "description": "event-loader 보안 보강 계약(원장 override 게이트·무결성 기록, 기본 매니페스트 정규화, --role-doc 제한, verify --require-default-manifest)을 CLI 공개 출력으로 검증 (S-1~S-5, 정본 문서 루트 결속 GC-002 포함)",
  "exports": ["LedgerOverrideGateTest", "LedgerIntegrityTest", "ManifestPathNormalizationTest", "RoleDocRestrictionTest", "RequireDefaultManifestTest", "RequireDefaultManifestDocumentRootTest"],
  "depends": ["event_loader"]
}
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone


REPO_ROOT = Path(__file__).resolve().parents[4]
LOADER = REPO_ROOT / "opal" / "tools" / "event-loader" / "event_loader.py"
MANIFEST = REPO_ROOT / "opal" / "core" / "references" / "events.json"

AGENT = "opal-be-agent"
ROLE = "builder"
DISPATCH_ID = "dsp-0123456789"
FIXED_NOW = "2020-01-01T00:00:00Z"
ROLE_DOC_LIMIT = 1_048_576

# 테스트가 직접 제어하는 환경변수. 외부(conftest 포함)에서 새어 들어온 값은 항상 제거한다.
CONTROLLED_ENV = (
    "OPAL_EVENT_LOADER_TEST_MODE",
    "OPAL_EVENT_LOADER_LEDGER",
    "OPAL_EVENT_LOADER_NOW",
    "OPAL_DEPLOYED_ROOT",
    "OPAL_SOURCE_ROOT",
)


class Result:
    def __init__(self, completed: subprocess.CompletedProcess[str]):
        self.code = completed.returncode
        self.stdout = completed.stdout
        self.stderr = completed.stderr
        try:
            self.payload = json.loads(completed.stdout) if completed.stdout.strip() else {}
        except json.JSONDecodeError:
            self.payload = {}

    def __repr__(self) -> str:  # 실패 메시지에 원문을 그대로 남긴다.
        return f"Result(code={self.code}, stdout={self.stdout.strip()[:1500]!r}, stderr={self.stderr.strip()[:600]!r})"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def codes(payload: dict) -> list[str]:
    return [w.get("code") for w in payload.get("warnings", [])]


class SecurityBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.tmpdir = self.tmp / "tmpdir"
        self.tmpdir.mkdir()
        self.project = self.tmp / "project"
        self.project.mkdir()
        self.deployed = self.tmp / "deployed"
        self.deployed.mkdir()

    # ---- 실행 도우미 ------------------------------------------------------
    def env(self, *, test_mode=False, ledger=None, now=None, deployed_root_env=None) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if k not in CONTROLLED_ENV}
        env["HOME"] = str(self.home)
        env["TMPDIR"] = str(self.tmpdir)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        if test_mode:
            env["OPAL_EVENT_LOADER_TEST_MODE"] = "1"
        if ledger is not None:
            env["OPAL_EVENT_LOADER_LEDGER"] = str(ledger)
        if now is not None:
            env["OPAL_EVENT_LOADER_NOW"] = now
        if deployed_root_env is not None:
            env["OPAL_DEPLOYED_ROOT"] = str(deployed_root_env)
        return env

    def run_cli(self, args: list[str], env: dict[str, str], *, loader: Path = LOADER, timeout: int = 60, cwd: Path | None = None) -> Result:
        try:
            completed = subprocess.run(
                [sys.executable, str(loader), *args],
                capture_output=True,
                text=True,
                env=env,
                cwd=str(cwd or self.tmp),
                check=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            self.fail(f"event-loader가 {timeout}초 안에 반환하지 않았습니다(멈춤): {args}")
        return Result(completed)

    def source_args(self) -> list[str]:
        return ["--source-root", str(REPO_ROOT), "--project-root", str(self.project), "--deployed-root", str(self.deployed)]

    @staticmethod
    def contract_args(role_doc: Path | None = None, dispatch_id: str = DISPATCH_ID) -> list[str]:
        args = ["--contract-version", "2", "--agent", AGENT, "--role", ROLE, "--dispatch-id", dispatch_id]
        if role_doc is not None:
            args += ["--role-doc", str(role_doc)]
        return args

    def save(self, name: str, text: str) -> Path:
        path = self.tmp / name
        path.write_text(text, encoding="utf-8")
        return path

    @property
    def default_ledger(self) -> Path:
        return self.home / ".opal" / "state" / "event-loader" / "legacy-dispatch.jsonl"

    @property
    def default_integrity(self) -> Path:
        return self.home / ".opal" / "state" / "event-loader" / "legacy-dispatch.integrity.jsonl"

    @property
    def tmp_integrity(self) -> Path:
        return self.tmpdir / f"opal-event-loader-integrity-{os.getuid()}.jsonl"

    def legacy_load(self, env: dict[str, str], name: str = "legacy.json") -> tuple[Result, Path]:
        result = self.run_cli(["load", "--event", "worker.dispatch", *self.source_args()], env)
        self.assertEqual(result.code, 0, result)
        self.assertTrue(result.payload.get("ok"), result)
        return result, self.save(name, result.stdout)

    def legacy_verify(self, response: Path, env: dict[str, str]) -> Result:
        return self.run_cli(["verify", "--receipt", str(response), "--event", "worker.dispatch", *self.source_args()], env)

    # ---- 설치본 흉내 ---------------------------------------------------------
    def make_install(self, name: str, *, manifest: str = "file") -> Path:
        """`parents[2]`가 설치 루트가 되도록 loader를 사본으로 배치한 임시 설치 루트.

        manifest: "file"(일반 파일) | "symlink"(실제 파일로의 심볼릭 링크)
        """
        root = self.tmp / name
        loader_dir = root / "tools" / "event-loader"
        loader_dir.mkdir(parents=True)
        for module in LOADER.parent.glob("*.py"):
            shutil.copyfile(module, loader_dir / module.name)
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        event = next(e for e in data["events"] if e["id"] == "worker.dispatch")
        for doc in event["required_docs"] + event["optional_docs"]:
            if "deployed" not in doc:
                continue
            target = root / doc["deployed"].replace("{deployed_root}/", "")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / doc["source"].replace("{source_root}/", ""), target)
        agent = root / "agents" / AGENT / "AGENT.md"
        agent.parent.mkdir(parents=True)
        shutil.copyfile(REPO_ROOT / "opal" / "agents" / AGENT / "AGENT.md", agent)
        manifest_path = root / "references" / "events.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        if manifest == "symlink":
            real = self.tmp / f"{name}-real" / "events.json"
            real.parent.mkdir(parents=True)
            shutil.copyfile(MANIFEST, real)
            manifest_path.symlink_to(real)
        else:
            shutil.copyfile(MANIFEST, manifest_path)
        return root

    def make_reduced_copy(self, name: str, *, with_docs: bool) -> Path:
        """worker.dispatch 문서를 1건으로 줄인 사본 매니페스트(and 선택적으로 그 사본의 deployed 루트)."""
        root = self.tmp / name
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        event = next(e for e in data["events"] if e["id"] == "worker.dispatch")
        event.pop("selection", None)
        event["required_docs"] = event["required_docs"][:1]
        manifest_path = root / "references" / "events.json"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        if with_docs:
            doc = event["required_docs"][0]
            target = root / doc["deployed"].replace("{deployed_root}/", "")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / doc["source"].replace("{source_root}/", ""), target)
            agent = root / "agents" / AGENT / "AGENT.md"
            agent.parent.mkdir(parents=True)
            shutil.copyfile(REPO_ROOT / "opal" / "agents" / AGENT / "AGENT.md", agent)
        return manifest_path

    @staticmethod
    def installed_loader(root: Path) -> Path:
        return root / "tools" / "event-loader" / "event_loader.py"

    def assert_rejected(self, result: Result, error: str) -> dict:
        self.assertEqual(result.code, 1, result)
        self.assertFalse(result.payload.get("ok"), result)
        self.assertEqual(result.payload.get("error"), error, result)
        return result.payload


# =====================================================================
# S-1 원장 override는 테스트 모드에서만 (D-1, D-2)
# =====================================================================
class LedgerOverrideGateTest(SecurityBase):
    def setUp(self):
        super().setUp()
        self.override_dir = self.tmp / "override"
        self.override_ledger = self.override_dir / "legacy-dispatch.jsonl"
        self.decoy_ledger = self.deployed / "state" / "event-loader" / "legacy-dispatch.jsonl"

    def _assert_recent(self, stamp: str):
        self.assertNotEqual(stamp, FIXED_NOW)
        now = datetime.now(timezone.utc)
        self.assertLess(abs(now - parse_ts(stamp)), timedelta(minutes=5), stamp)

    def test_a_override_ignored_without_test_mode_on_load(self):
        for label, env in (
            ("ledger+now", self.env(ledger=self.override_ledger, now=FIXED_NOW, deployed_root_env=self.deployed)),
            ("ledger", self.env(ledger=self.override_ledger, deployed_root_env=self.deployed)),
            ("now", self.env(now=FIXED_NOW, deployed_root_env=self.deployed)),
        ):
            with self.subTest(label):
                for stale in (self.default_ledger, self.default_integrity):
                    if stale.exists():
                        stale.unlink()
                result = self.run_cli(["load", "--event", "worker.dispatch", *self.source_args()], env)
                self.assertEqual(result.code, 0, result)
                self.assertEqual(result.payload.get("contract"), "legacy", result)
                self.assertIn("legacy_dispatch_contract", codes(result.payload), result)
                self.assertIn("ledger_override_ignored", codes(result.payload), result)
                # 원장은 HOME 기반 기본 위치에만, 고정 시각 대신 실제 시각으로 기록된다.
                self.assertTrue(self.default_ledger.is_file(), "기본 원장 위치에 기록이 없습니다")
                rows = read_jsonl(self.default_ledger)
                self.assertEqual(len(rows), 1, rows)
                self.assertEqual((rows[0]["op"], rows[0]["event"]), ("load", "worker.dispatch"))
                self._assert_recent(rows[0]["ts"])
                self.assertFalse(self.override_ledger.exists(), "override 위치에 기록되면 안 됩니다")
                self.assertFalse(self.decoy_ledger.exists(), "--deployed-root·OPAL_DEPLOYED_ROOT로 원장이 옮겨지면 안 됩니다")
                # 무결성 기록 1줄
                self.assertTrue(self.default_integrity.is_file(), "무결성 기록이 없습니다")
                integrity = read_jsonl(self.default_integrity)
                self.assertEqual(len(integrity), 1, integrity)
                self.assertEqual(integrity[0]["kind"], "ledger_override_ignored")
                self.assertEqual((integrity[0]["op"], integrity[0]["event"]), ("load", "worker.dispatch"))
                self._assert_recent(integrity[0]["ts"])

    def test_a_override_ignored_without_test_mode_on_verify(self):
        env = self.env(ledger=self.override_ledger, now=FIXED_NOW)
        load, response = self.legacy_load(env)
        verify = self.legacy_verify(response, env)
        self.assertEqual(verify.code, 0, verify)
        self.assertEqual(verify.payload.get("contract"), "legacy", verify)
        self.assertTrue(verify.payload.get("legacy_verified"), verify)
        self.assertIn("legacy_dispatch_contract", codes(verify.payload), verify)
        self.assertIn("ledger_override_ignored", codes(verify.payload), verify)
        self.assertIn("ledger_override_ignored", codes(load.payload), load)
        rows = read_jsonl(self.default_ledger)
        self.assertEqual([r["op"] for r in rows], ["load", "verify"], rows)
        for row in rows:
            self._assert_recent(row["ts"])
        integrity = read_jsonl(self.default_integrity)
        self.assertEqual([(r["kind"], r["op"]) for r in integrity], [("ledger_override_ignored", "load"), ("ledger_override_ignored", "verify")], integrity)
        self.assertFalse(self.override_ledger.exists())

    def test_b_override_applied_in_test_mode(self):
        env = self.env(test_mode=True, ledger=self.override_ledger, now=FIXED_NOW)
        load, response = self.legacy_load(env)
        self.assertEqual(load.payload.get("contract"), "legacy", load)
        self.assertIn("legacy_dispatch_contract", codes(load.payload), load)
        self.assertIn("ledger_override_active", codes(load.payload), load)
        self.assertNotIn("ledger_override_ignored", codes(load.payload), load)
        verify = self.legacy_verify(response, env)
        self.assertEqual(verify.code, 0, verify)
        self.assertIn("ledger_override_active", codes(verify.payload), verify)
        rows = read_jsonl(self.override_ledger)
        self.assertEqual([(r["op"], r["ts"]) for r in rows], [("load", FIXED_NOW), ("verify", FIXED_NOW)], rows)
        self.assertFalse(self.default_ledger.exists(), "테스트 모드에서는 기본 원장을 건드리지 않습니다")
        # 무결성 기록은 (override가 가리키는) 원장 옆에 남고 실제 UTC 시각을 쓴다.
        adjacent = self.override_dir / "legacy-dispatch.integrity.jsonl"
        self.assertTrue(adjacent.is_file(), "원장 옆 무결성 기록이 없습니다")
        integrity = read_jsonl(adjacent)
        self.assertEqual([(r["kind"], r["op"], r["event"]) for r in integrity], [("ledger_override_active", "load", "worker.dispatch"), ("ledger_override_active", "verify", "worker.dispatch")], integrity)
        for row in integrity:
            self._assert_recent(row["ts"])

    def test_c_no_override_variables_records_default_location_without_warnings(self):
        env = self.env(deployed_root_env=self.deployed)
        result = self.run_cli(["load", "--event", "worker.dispatch", *self.source_args()], env)
        self.assertEqual(result.code, 0, result)
        self.assertEqual(codes(result.payload), ["legacy_dispatch_contract"], result)
        rows = read_jsonl(self.default_ledger)
        self.assertEqual(len(rows), 1, rows)
        self._assert_recent(rows[0]["ts"])
        self.assertFalse(self.default_integrity.exists(), "경고가 없으면 무결성 기록도 없어야 합니다")
        self.assertFalse(self.decoy_ledger.exists())

    def test_legacy_result_identical_across_modes(self):
        baseline = self.run_cli(["load", "--event", "worker.dispatch", *self.source_args()], self.env())
        ignored = self.run_cli(["load", "--event", "worker.dispatch", *self.source_args()], self.env(ledger=self.override_ledger, now=FIXED_NOW))
        active = self.run_cli(["load", "--event", "worker.dispatch", *self.source_args()], self.env(test_mode=True, ledger=self.override_ledger, now=FIXED_NOW))
        for other in (ignored, active):
            for key in ("contract", "payload_bytes", "document_count", "manifest_sha256"):
                self.assertEqual(other.payload.get(key), baseline.payload.get(key), key)
            self.assertEqual([d["id"] for d in other.payload["documents"]], [d["id"] for d in baseline.payload["documents"]])
            self.assertIn("legacy_dispatch_contract", codes(other.payload))


# =====================================================================
# S-2 원장 쓰기 실패와 무결성 기록·보고 (D-2)
# =====================================================================
class LedgerIntegrityTest(SecurityBase):
    def block_default_ledger_dir(self):
        """$HOME/.opal을 일반 파일로 만들어 기본 원장과 원장 옆 무결성 기록을 모두 쓸 수 없게 한다."""
        (self.home / ".opal").write_text("not a directory", encoding="utf-8")

    def test_blocked_ledger_does_not_block_call_and_falls_back_to_tmpdir(self):
        self.block_default_ledger_dir()
        result = self.run_cli(["load", "--event", "worker.dispatch", *self.source_args()], self.env())
        self.assertEqual(result.code, 0, result)
        self.assertTrue(result.payload.get("ok"), result)
        self.assertIn("ledger_write_failed", codes(result.payload), result)
        self.assertTrue(self.tmp_integrity.is_file(), f"TMPDIR 폴백 기록이 없습니다: {list(self.tmpdir.iterdir())}")
        self.assertEqual(stat.S_IMODE(self.tmp_integrity.stat().st_mode), 0o600)
        rows = read_jsonl(self.tmp_integrity)
        self.assertEqual(len(rows), 1, rows)
        self.assertEqual((rows[0]["kind"], rows[0]["op"], rows[0]["event"]), ("ledger_write_failed", "load", "worker.dispatch"))
        stamp = parse_ts(rows[0]["ts"])
        self.assertLess(abs(datetime.now(timezone.utc) - stamp), timedelta(minutes=5))

    def test_report_reads_tmpdir_fallback_and_is_unreliable(self):
        self.block_default_ledger_dir()
        self.run_cli(["load", "--event", "worker.dispatch", *self.source_args()], self.env())
        report = self.run_cli(["legacy-report", *self.source_args()], self.env())
        self.assertEqual(report.code, 0, report)
        integrity = report.payload.get("integrity")
        self.assertIsInstance(integrity, dict, report)
        self.assertGreaterEqual(integrity["write_failures"], 1, report)
        self.assertEqual(integrity["override_ignored"], 0, report)
        self.assertEqual(integrity["override_active"], 0, report)
        self.assertIs(report.payload.get("reliable"), False, report)
        self.assertEqual(report.payload.get("count"), 0, report)

    def test_adjacent_integrity_record_preferred_over_tmpdir(self):
        # 원장 파일 자리에 디렉터리를 두어 원장만 쓰기 실패시키고, 원장 옆 위치는 쓸 수 있게 둔다.
        ledger_dir = self.tmp / "led"
        ledger = ledger_dir / "legacy-dispatch.jsonl"
        ledger.mkdir(parents=True)
        env = self.env(test_mode=True, ledger=ledger, now=FIXED_NOW)
        result = self.run_cli(["load", "--event", "worker.dispatch", *self.source_args()], env)
        self.assertEqual(result.code, 0, result)
        self.assertIn("ledger_write_failed", codes(result.payload), result)
        adjacent = ledger_dir / "legacy-dispatch.integrity.jsonl"
        self.assertTrue(adjacent.is_file(), "원장 옆 무결성 기록이 없습니다")
        kinds = sorted(r["kind"] for r in read_jsonl(adjacent))
        self.assertEqual(kinds, ["ledger_override_active", "ledger_write_failed"], kinds)
        self.assertFalse(self.tmp_integrity.exists(), "원장 옆에 쓸 수 있으면 TMPDIR 폴백을 쓰면 안 됩니다")
        report = self.run_cli(["legacy-report", *self.source_args()], env)
        self.assertEqual(report.code, 0, report)
        self.assertGreaterEqual(report.payload["integrity"]["write_failures"], 1, report)
        self.assertGreaterEqual(report.payload["integrity"]["override_active"], 1, report)
        self.assertIs(report.payload.get("reliable"), False, report)

    def test_all_locations_blocked_writes_one_stderr_line_and_still_succeeds(self):
        self.block_default_ledger_dir()
        self.tmp_integrity.mkdir()  # 폴백 파일 자리에 디렉터리를 두어 쓰기를 막는다.
        result = self.run_cli(["load", "--event", "worker.dispatch", *self.source_args()], self.env())
        self.assertEqual(result.code, 0, result)
        self.assertTrue(result.payload.get("ok"), result)
        self.assertIn("ledger_write_failed", codes(result.payload), result)
        lines = [line for line in result.stderr.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, f"stderr 한 줄이어야 합니다: {result.stderr!r}")

    def _seed(self, path: Path, rows: list[tuple[str, str]]):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps({"ts": ts, "kind": kind, "op": "load", "event": "worker.dispatch"}) + "\n" for ts, kind in rows), encoding="utf-8")

    def _seed_windows(self):
        self._seed(self.default_integrity, [
            ("2026-10-01T00:00:00Z", "ledger_write_failed"),
            ("2026-10-03T00:00:00Z", "ledger_write_failed"),
            ("2026-10-03T12:00:00Z", "ledger_override_ignored"),
            ("2026-10-05T00:00:00Z", "ledger_write_failed"),
        ])
        self._seed(self.tmp_integrity, [
            ("2026-10-02T06:00:00Z", "ledger_write_failed"),
            ("2026-10-03T06:00:00Z", "ledger_override_active"),
            ("2026-10-06T00:00:00Z", "ledger_write_failed"),
        ])

    def test_report_counts_both_locations_and_applies_window(self):
        self._seed_windows()
        full = self.run_cli(["legacy-report", *self.source_args()], self.env())
        self.assertEqual(full.code, 0, full)
        self.assertEqual(full.payload["integrity"], {"write_failures": 5, "override_ignored": 1, "override_active": 1}, full)
        self.assertIs(full.payload["reliable"], False, full)
        windowed = self.run_cli(["legacy-report", "--since", "2026-10-02T00:00:00Z", "--until", "2026-10-04T00:00:00Z", *self.source_args()], self.env())
        self.assertEqual(windowed.payload["integrity"], {"write_failures": 2, "override_ignored": 1, "override_active": 1}, windowed)
        outside = self.run_cli(["legacy-report", "--since", "2026-11-01T00:00:00Z", "--until", "2026-11-02T00:00:00Z", *self.source_args()], self.env())
        self.assertEqual(outside.payload["integrity"], {"write_failures": 0, "override_ignored": 0, "override_active": 0}, outside)
        self.assertIs(outside.payload["reliable"], True, outside)

    def test_report_without_any_records_is_reliable(self):
        report = self.run_cli(["legacy-report", *self.source_args()], self.env())
        self.assertEqual(report.code, 0, report)
        self.assertEqual(report.payload.get("integrity"), {"write_failures": 0, "override_ignored": 0, "override_active": 0}, report)
        self.assertIs(report.payload.get("reliable"), True, report)

    def test_report_flags_override_variables_present_at_call_time(self):
        ledger = self.tmp / "ov" / "legacy-dispatch.jsonl"
        ignored = self.run_cli(["legacy-report", *self.source_args()], self.env(ledger=ledger))
        self.assertEqual(ignored.code, 0, ignored)
        self.assertIn("ledger_override_ignored", codes(ignored.payload), ignored)
        self.assertIs(ignored.payload.get("reliable"), False, ignored)
        active = self.run_cli(["legacy-report", *self.source_args()], self.env(test_mode=True, ledger=ledger))
        self.assertEqual(active.code, 0, active)
        self.assertIn("ledger_override_active", codes(active.payload), active)
        self.assertIs(active.payload.get("reliable"), False, active)


# =====================================================================
# S-3 기본 매니페스트 경로 정규화 (D-3)
# =====================================================================
class ManifestPathNormalizationTest(SecurityBase):
    def _dispatch_args(self, root: Path) -> list[str]:
        return ["--deployed-root", str(root), "--project-root", str(self.project), *self.contract_args()]

    def _load(self, root: Path, name: str) -> tuple[Result, Path]:
        result = self.run_cli(["load", "--event", "worker.dispatch", *self._dispatch_args(root)], self.env(), loader=self.installed_loader(root))
        self.assertEqual(result.code, 0, result)
        self.assertTrue(result.payload.get("ok"), result)
        return result, self.save(name, result.stdout)

    def _verify(self, root: Path, response: Path) -> Result:
        return self.run_cli(["verify", "--receipt", str(response), "--event", "worker.dispatch", *self._dispatch_args(root)], self.env(), loader=self.installed_loader(root))

    def test_a_symlinked_manifest_records_real_path(self):
        root = self.make_install("inst-link", manifest="symlink")
        real = (self.tmp / "inst-link-real" / "events.json").resolve()
        loaded, _ = self._load(root, "link.json")
        self.assertEqual(loaded.payload["manifest_path"], str(real), loaded)
        self.assertEqual(loaded.payload["receipt"]["manifest_path"], str(real), loaded)

    def test_a_symlinked_manifest_load_then_verify_passes(self):
        root = self.make_install("inst-link", manifest="symlink")
        real = (self.tmp / "inst-link-real" / "events.json").resolve()
        _, response = self._load(root, "link.json")
        verified = self._verify(root, response)
        self.assertEqual(verified.code, 0, verified)
        self.assertTrue(verified.payload.get("ok"), verified)
        self.assertEqual(verified.payload.get("manifest_path"), str(real), verified)

    def test_b_regular_file_manifest_unchanged(self):
        root = self.make_install("inst-file", manifest="file")
        expected = str((root / "references" / "events.json").resolve())
        loaded, response = self._load(root, "file.json")
        self.assertEqual(loaded.payload["manifest_path"], expected, loaded)
        verified = self._verify(root, response)
        self.assertEqual(verified.code, 0, verified)
        self.assertTrue(verified.payload.get("ok"), verified)
        self.assertEqual(verified.payload.get("manifest_path"), expected, verified)

    def test_c_receipt_pointing_to_other_real_manifest_is_stale(self):
        root = self.make_install("inst-file", manifest="file")
        _, response = self._load(root, "file.json")
        other = self.tmp / "other" / "events.json"
        other.parent.mkdir()
        shutil.copyfile(MANIFEST, other)
        data = json.loads(response.read_text(encoding="utf-8"))
        data["manifest_path"] = str(other)
        data["receipt"]["manifest_path"] = str(other)
        tampered = self.save("tampered.json", json.dumps(data, ensure_ascii=False))
        self.assert_rejected(self._verify(root, tampered), "stale_receipt")

    def test_d_receipt_from_copied_manifest_is_stale_against_canonical(self):
        root = self.make_install("inst-file", manifest="file")
        copy = self.make_reduced_copy("copy-d", with_docs=False)
        built = self.run_cli(
            ["load", "--event", "worker.dispatch", "--manifest", str(copy), *self._dispatch_args(root)],
            self.env(),
            loader=self.installed_loader(root),
        )
        self.assertEqual(built.code, 0, built)
        response = self.save("copy.json", built.stdout)
        self.assert_rejected(self._verify(root, response), "stale_receipt")


# =====================================================================
# S-4 --role-doc 제한 (D-4)
# =====================================================================
class RoleDocRestrictionTest(SecurityBase):
    def setUp(self):
        super().setUp()
        self.outside = self.tmp / "outside"
        self.outside.mkdir()
        # verify 판정 확인용 기준 receipt(역할 문서 없음)
        base = self.run_cli(["load", "--event", "worker.dispatch", *self.source_args(), *self.contract_args()], self.env())
        self.assertEqual(base.code, 0, base)
        self.base_response = self.save("base.json", base.stdout)

    def load(self, role_doc: Path) -> Result:
        return self.run_cli(["load", "--event", "worker.dispatch", *self.source_args(), *self.contract_args(role_doc)], self.env(), timeout=10)

    def verify(self, role_doc: Path, response: Path | None = None) -> Result:
        return self.run_cli(
            ["verify", "--receipt", str(response or self.base_response), "--event", "worker.dispatch", *self.source_args(), *self.contract_args(role_doc)],
            self.env(),
            timeout=10,
        )

    def assert_role_doc_rejected(self, result: Result, cause: str):
        payload = self.assert_rejected(result, "contract_arg_invalid")
        self.assertEqual(payload.get("argument"), "--role-doc", result)
        self.assertEqual(payload.get("cause"), cause, result)

    # ---- 허용 ----------------------------------------------------------
    def _allowed_candidates(self) -> list[tuple[str, Path]]:
        in_project = self.project / "role.md"
        in_project.write_text("project role doc\n", encoding="utf-8")
        in_deployed = self.deployed / "role.md"
        in_deployed.write_text("deployed role doc\n", encoding="utf-8")
        in_source = REPO_ROOT / "opal" / "agents" / AGENT / "AGENT.md"
        inner_link = self.project / "inner-link.md"
        inner_link.symlink_to(in_project)
        at_limit = self.project / "at-limit.md"
        at_limit.write_bytes(b"a" * ROLE_DOC_LIMIT)
        return [("project", in_project), ("deployed", in_deployed), ("source", in_source), ("inner-symlink", inner_link), ("exactly-limit", at_limit)]

    def test_allowed_candidates_load_and_record_path_and_hash(self):
        for label, path in self._allowed_candidates():
            with self.subTest(label):
                result = self.load(path)
                self.assertEqual(result.code, 0, result)
                self.assertTrue(result.payload.get("ok"), result)
                recorded = result.payload["receipt"]["role_doc"]
                self.assertEqual(recorded["path"], str(path.resolve()), result)
                self.assertEqual(recorded["sha256"], hashlib.sha256(path.read_bytes()).hexdigest(), result)

    def test_allowed_candidates_verify_with_same_role_doc(self):
        for label, path in self._allowed_candidates():
            with self.subTest(label):
                loaded = self.load(path)
                self.assertEqual(loaded.code, 0, loaded)
                response = self.save(f"rd-{label}.json", loaded.stdout)
                verified = self.verify(path, response)
                self.assertEqual(verified.code, 0, verified)
                self.assertTrue(verified.payload.get("ok"), verified)

    # ---- 거부 ----------------------------------------------------------
    def _rejected_candidates(self) -> list[tuple[str, Path, str]]:
        cases: list[tuple[str, Path, str]] = []
        outside_file = self.outside / "doc.md"
        outside_file.write_text("outside\n", encoding="utf-8")
        cases.append(("outside-root", outside_file, "outside_allowed_roots"))
        escape = self.project / "escape.md"
        escape.symlink_to(outside_file)
        cases.append(("symlink-escape", escape, "outside_allowed_roots"))
        fifo = self.project / "pipe.md"
        os.mkfifo(fifo)
        cases.append(("fifo", fifo, "not_regular_file"))
        directory = self.project / "adir"
        directory.mkdir()
        cases.append(("directory", directory, "not_regular_file"))
        big = self.project / "big.md"
        big.write_bytes(b"a" * (ROLE_DOC_LIMIT + 1))
        cases.append(("too-large", big, "too_large"))
        cases.append(("missing", self.project / "missing.md", "unreadable"))
        return cases

    def test_rejected_candidates_on_load(self):
        for label, path, cause in self._rejected_candidates():
            with self.subTest(label):
                self.assert_role_doc_rejected(self.load(path), cause)

    def test_rejected_candidates_on_verify(self):
        for label, path, cause in self._rejected_candidates():
            with self.subTest(label):
                self.assert_role_doc_rejected(self.verify(path), cause)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root는 권한 비트와 무관하게 읽을 수 있다")
    def test_unreadable_file_inside_root_is_rejected(self):
        locked = self.project / "locked.md"
        locked.write_text("secret\n", encoding="utf-8")
        locked.chmod(0o000)
        self.addCleanup(locked.chmod, 0o600)
        self.assert_role_doc_rejected(self.load(locked), "unreadable")
        self.assert_role_doc_rejected(self.verify(locked), "unreadable")


# =====================================================================
# S-5 verify --require-default-manifest (D-5)
# =====================================================================
FLAGLESS_VERIFY_KEYS = {
    "ok", "command", "event", "receipt_path", "manifest_path", "manifest_sha256", "verified_documents",
    "verified_document_count", "payload_bytes", "contract", "dispatch_id", "agent", "role", "load_id",
}


class RequireDefaultManifestTest(SecurityBase):
    FLAG = "--require-default-manifest"

    def installed(self) -> tuple[Path, Path]:
        root = self.make_install("inst", manifest="file")
        return root, self.installed_loader(root)

    def load_installed(self, loader: Path, root: Path, *extra: str, env: dict[str, str] | None = None, deployed: Path | None = None, name="resp.json") -> Path:
        args = ["load", "--event", "worker.dispatch", "--project-root", str(self.project), *self.contract_args()]
        if deployed is not None:
            args += ["--deployed-root", str(deployed)]
        result = self.run_cli([*args, *extra], env or self.env(), loader=loader)
        self.assertEqual(result.code, 0, result)
        return self.save(name, result.stdout)

    def verify_installed(self, loader: Path, response: Path, *extra: str, env: dict[str, str] | None = None, deployed: Path | None = None) -> Result:
        args = ["verify", "--receipt", str(response), "--event", "worker.dispatch", "--project-root", str(self.project), *self.contract_args()]
        if deployed is not None:
            args += ["--deployed-root", str(deployed)]
        return self.run_cli([*args, *extra], env or self.env(), loader=loader)

    # (a) 정상
    def test_a_installed_default_manifest_passes_and_reports_manifest_default(self):
        root, loader = self.installed()
        response = self.load_installed(loader, root, deployed=root)
        result = self.verify_installed(loader, response, self.FLAG, deployed=root)
        self.assertEqual(result.code, 0, result)
        self.assertTrue(result.payload.get("ok"), result)
        self.assertIs(result.payload.get("manifest_default"), True, result)
        self.assertEqual(result.payload.get("manifest_path"), str((root / "references" / "events.json").resolve()), result)

    def test_a_source_run_default_manifest_passes(self):
        loaded = self.run_cli(["load", "--event", "worker.dispatch", *self.source_args(), *self.contract_args()], self.env())
        self.assertEqual(loaded.code, 0, loaded)
        response = self.save("src.json", loaded.stdout)
        result = self.run_cli(["verify", "--receipt", str(response), "--event", "worker.dispatch", *self.source_args(), *self.contract_args(), self.FLAG], self.env())
        self.assertEqual(result.code, 0, result)
        self.assertIs(result.payload.get("manifest_default"), True, result)
        self.assertEqual(result.payload.get("manifest_path"), str(MANIFEST.resolve()), result)

    # (b) --manifest 사본
    def test_b_manifest_flag_copy_is_rejected(self):
        root, loader = self.installed()
        copy = self.make_reduced_copy("copy-b", with_docs=False)
        response = self.load_installed(loader, root, "--manifest", str(copy), deployed=root)
        payload = self.assert_rejected(self.verify_installed(loader, response, "--manifest", str(copy), self.FLAG, deployed=root), "manifest_not_default")
        self.assertEqual(payload.get("expected"), str((root / "references" / "events.json").resolve()), payload)
        self.assertEqual(payload.get("actual"), str(copy.resolve()), payload)

    def test_b_source_run_manifest_flag_copy_is_rejected(self):
        copy = self.make_reduced_copy("copy-bs", with_docs=False)
        loaded = self.run_cli(["load", "--event", "worker.dispatch", *self.source_args(), "--manifest", str(copy), *self.contract_args()], self.env())
        self.assertEqual(loaded.code, 0, loaded)
        response = self.save("srccopy.json", loaded.stdout)
        result = self.run_cli(["verify", "--receipt", str(response), "--event", "worker.dispatch", *self.source_args(), "--manifest", str(copy), *self.contract_args(), self.FLAG], self.env())
        payload = self.assert_rejected(result, "manifest_not_default")
        self.assertEqual(payload.get("expected"), str(MANIFEST.resolve()), payload)
        self.assertEqual(payload.get("actual"), str(copy.resolve()), payload)

    # (c) OPAL_DEPLOYED_ROOT 사본 루트
    def test_c_deployed_root_env_copy_is_rejected(self):
        root, loader = self.installed()
        copy_manifest = self.make_reduced_copy("copy-c", with_docs=True)
        copy_root = copy_manifest.parents[1]
        env = self.env(deployed_root_env=copy_root)
        response = self.load_installed(loader, root, env=env)
        payload = self.assert_rejected(self.verify_installed(loader, response, self.FLAG, env=env), "manifest_not_default")
        self.assertEqual(payload.get("expected"), str((root / "references" / "events.json").resolve()), payload)
        self.assertEqual(payload.get("actual"), str(copy_manifest.resolve()), payload)

    # (d) --deployed-root 사본 루트
    def test_d_deployed_root_flag_copy_is_rejected(self):
        root, loader = self.installed()
        copy_manifest = self.make_reduced_copy("copy-d2", with_docs=True)
        copy_root = copy_manifest.parents[1]
        response = self.load_installed(loader, root, deployed=copy_root)
        payload = self.assert_rejected(self.verify_installed(loader, response, self.FLAG, deployed=copy_root), "manifest_not_default")
        self.assertEqual(payload.get("expected"), str((root / "references" / "events.json").resolve()), payload)
        self.assertEqual(payload.get("actual"), str(copy_manifest.resolve()), payload)

    # (e) 플래그 없는 기존 verify는 불변
    def test_e_flagless_verify_unchanged_without_manifest_default_key(self):
        root, loader = self.installed()
        response = self.load_installed(loader, root, deployed=root)
        result = self.verify_installed(loader, response, deployed=root)
        self.assertEqual(result.code, 0, result)
        self.assertTrue(result.payload.get("ok"), result)
        self.assertNotIn("manifest_default", result.payload, result)
        self.assertEqual(set(result.payload), FLAGLESS_VERIFY_KEYS, result)

    def test_e_flagless_verify_with_copy_manifest_still_passes(self):
        root, loader = self.installed()
        copy = self.make_reduced_copy("copy-e", with_docs=False)
        response = self.load_installed(loader, root, "--manifest", str(copy), deployed=root)
        result = self.verify_installed(loader, response, "--manifest", str(copy), deployed=root)
        self.assertEqual(result.code, 0, result)
        self.assertNotIn("manifest_default", result.payload, result)


class RequireDefaultManifestDocumentRootTest(RequireDefaultManifestTest):
    """GC-002: 정본 --manifest를 주더라도 문서 루트가 정본 루트와 다르면 --require-default-manifest가 거부한다."""

    def evil_root(self, root: Path) -> Path:
        evil = self.tmp / "evil-root"
        shutil.copytree(root, evil)
        manifest = json.loads((root / "references" / "events.json").read_text(encoding="utf-8"))
        event = next(e for e in manifest["events"] if e["id"] == "worker.dispatch")
        doc = evil / event["required_docs"][0]["deployed"].replace("{deployed_root}/", "")
        doc.write_text(doc.read_text(encoding="utf-8") + "\n## INJECTED\n", encoding="utf-8")
        return evil

    def canonical_args(self, root: Path) -> list[str]:
        return ["--manifest", str((root / "references" / "events.json").resolve())]

    def test_canonical_manifest_with_evil_deployed_root_flag_rejected(self):
        root, loader = self.installed()
        evil = self.evil_root(root)
        response = self.load_installed(loader, root, *self.canonical_args(root), deployed=evil)
        payload = self.assert_rejected(self.verify_installed(loader, response, *self.canonical_args(root), self.FLAG, deployed=evil), "manifest_not_default")
        self.assertIn(str(root.resolve()), str(payload.get("expected")), payload)
        self.assertIn(str(evil.resolve()), str(payload.get("actual")), payload)

    def test_canonical_manifest_with_evil_deployed_root_env_rejected(self):
        root, loader = self.installed()
        evil = self.evil_root(root)
        env = self.env(deployed_root_env=evil)
        response = self.load_installed(loader, root, *self.canonical_args(root), env=env)
        self.assert_rejected(self.verify_installed(loader, response, *self.canonical_args(root), self.FLAG, env=env), "manifest_not_default")

    def test_canonical_manifest_and_root_pass(self):
        root, loader = self.installed()
        response = self.load_installed(loader, root, *self.canonical_args(root), deployed=root)
        result = self.verify_installed(loader, response, *self.canonical_args(root), self.FLAG, deployed=root)
        self.assertEqual(result.code, 0, result)
        self.assertIs(result.payload.get("manifest_default"), True, result)

    def test_flagless_verify_with_evil_root_unchanged(self):
        root, loader = self.installed()
        evil = self.evil_root(root)
        response = self.load_installed(loader, root, *self.canonical_args(root), deployed=evil)
        result = self.verify_installed(loader, response, *self.canonical_args(root), deployed=evil)
        self.assertEqual(result.code, 0, result)
        self.assertNotIn("manifest_default", result.payload, result)


if __name__ == "__main__":
    unittest.main()
