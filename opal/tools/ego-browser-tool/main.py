#!/usr/bin/env python3
"""
@header {
  "module": "ego_browser_tool",
  "layer": "util",
  "domain": "opal-tools",
  "description": "Ego Lite readiness, verified macOS installation, resumable handoff, and sentinel-based browser assertion adapter.",
  "exports": ["main"],
  "depends": ["ego-browser CLI", "macOS hdiutil/codesign/spctl"]
}

The public contract is JSON-only. Ego Lite remains an optional user-managed
provider; this tool never exports cookies, passwords, or session tokens.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from typing import Any, Dict, Iterable, Optional


TOOL_DIR = pathlib.Path(__file__).resolve().parent
DEFAULT_MANIFEST = TOOL_DIR / "installer-manifest.json"
APP_BUNDLE = "ego lite.app"
INSTALL_URL = "https://lite.ego.app/document/en/docs/quick-start"
SENTINEL = "__OPAL_EGO_RESULT__="
EXIT_CODES = {
    "pass": 0,
    "fail": 6,
    "infra_error": 7,
    "provider_unavailable": 18,
    "blocked": 19,
    "awaiting_human": 20,
}


def _emit(payload: Dict[str, Any]) -> None:
    status = str(payload.get("status") or ("pass" if payload.get("ok") else "infra_error"))
    payload.setdefault("ok", status == "pass")
    print(json.dumps(payload, ensure_ascii=False))
    raise SystemExit(EXIT_CODES.get(status, 7))


def _platform_key() -> Optional[str]:
    system = os.environ.get("OPAL_EGO_PLATFORM") or sys.platform
    machine = os.environ.get("OPAL_EGO_ARCH") or platform.machine()
    system = system.lower()
    machine = machine.lower()
    if system in {"darwin", "macos"}:
        system = "darwin"
    if machine in {"aarch64", "arm64"}:
        machine = "arm64"
    elif machine in {"amd64", "x64", "x86_64"}:
        machine = "x86_64"
    key = f"{system}-{machine}"
    return key if key in {"darwin-arm64", "darwin-x86_64"} else None


def _candidate_cli() -> Optional[str]:
    override = os.environ.get("OPAL_EGO_CLI_CMD")
    if override:
        return override if os.path.isfile(override) and os.access(override, os.X_OK) else None
    found = shutil.which("ego-browser")
    if found:
        return found
    local = pathlib.Path.home() / ".local" / "bin" / "ego-browser"
    return str(local) if local.is_file() and os.access(local, os.X_OK) else None


def _installed_app() -> Optional[pathlib.Path]:
    roots: Iterable[pathlib.Path]
    override = os.environ.get("OPAL_EGO_INSTALL_ROOT")
    if override:
        roots = (pathlib.Path(override),)
    else:
        roots = (pathlib.Path("/Applications"), pathlib.Path.home() / "Applications")
    for root in roots:
        candidate = root / APP_BUNDLE
        if candidate.is_dir():
            return candidate
    return None


def _resume_token(url: str, expected: Optional[str]) -> str:
    value = json.dumps({"url": url, "expect_text": expected}, sort_keys=True)
    return "ego-" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def _handoff(url: str, expected: Optional[str], *, choice: Optional[str] = None) -> Dict[str, Any]:
    instruction = "Ego Lite 설치 방식을 선택한 뒤 GUI 온보딩을 완료해 주세요."
    if choice == "manual":
        instruction = "공식 안내에서 Ego Lite를 설치하고 GUI 온보딩을 완료해 주세요."
    elif choice == "r2":
        instruction = "Ego Lite 앱 설치가 끝났습니다. 앱을 열어 GUI 온보딩을 완료해 주세요."
    return {
        "choices": ["manual", "r2", "cancel"],
        "selected": choice,
        "instruction": instruction,
        "install_url": INSTALL_URL,
        "resume_token": _resume_token(url, expected),
        "resume": {"url": url, "expect_text": expected},
    }


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def _command(env_name: str, default: str) -> list[str]:
    return shlex.split(os.environ.get(env_name, default))


def _verification_error(error: str, detail: str, status: str = "blocked") -> None:
    _emit({"ok": False, "command": "install", "status": status, "error": error, "detail": detail})


def _manifest_entry() -> tuple[Dict[str, Any], str]:
    key = _platform_key()
    if not key:
        _emit({
            "ok": False,
            "command": "install",
            "status": "provider_unavailable",
            "error": "unsupported_platform",
        })
    manifest_path = pathlib.Path(os.environ.get("OPAL_EGO_MANIFEST_PATH", str(DEFAULT_MANIFEST)))
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entry = manifest["platforms"][key]
        return {**entry, "version": manifest["version"]}, key
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        _verification_error("installer_manifest_invalid", str(exc), "infra_error")
        raise AssertionError("unreachable")


def _download(entry: Dict[str, Any], destination: pathlib.Path) -> None:
    request = urllib.request.Request(entry["url"], headers={"User-Agent": "OPAL ego-browser-tool/1"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as output:
            shutil.copyfileobj(response, output)
    except Exception as exc:
        _verification_error("artifact_download_failed", str(exc), "infra_error")


def cmd_status(_args: argparse.Namespace) -> None:
    key = _platform_key()
    cli = _candidate_cli()
    app = _installed_app()
    if not key:
        _emit({"ok": False, "command": "status", "status": "provider_unavailable", "error": "unsupported_platform"})
    if cli:
        _emit({"ok": True, "command": "status", "status": "pass", "cli": cli, "app": str(app) if app else None})
    _emit({
        "ok": False,
        "command": "status",
        "status": "awaiting_human",
        "operational_status": "awaiting_human",
        "app": str(app) if app else None,
        "detail": "Ego Lite GUI onboarding is required" if app else "Ego Lite is not installed",
    })


def cmd_install(_args: argparse.Namespace) -> None:
    entry, platform_key = _manifest_entry()
    resume_url = getattr(_args, "url", None) or "https://example.com"
    resume_expected = getattr(_args, "expect_text", None)
    existing = _installed_app()
    if existing:
        _emit({
            "ok": False,
            "command": "install",
            "status": "awaiting_human",
            "operational_status": "awaiting_human",
            "version": entry["version"],
            "app": str(existing),
            "detail": "Existing app preserved; complete GUI onboarding",
        })

    with tempfile.TemporaryDirectory(prefix="opal-ego-install-") as raw_temp:
        temp_dir = pathlib.Path(raw_temp)
        supplied_dmg = os.environ.get("OPAL_EGO_DMG_PATH")
        dmg_path = pathlib.Path(supplied_dmg) if supplied_dmg else temp_dir / "egolite.dmg"
        if not supplied_dmg:
            _download(entry, dmg_path)

        hdiutil = _command("OPAL_EGO_HDIUTIL_CMD", "hdiutil")
        verified = _run([*hdiutil, "verify", str(dmg_path)])
        if verified.returncode != 0:
            _verification_error("dmg_verify_failed", verified.stderr.strip() or verified.stdout.strip())

        actual_hash = hashlib.sha256(dmg_path.read_bytes()).hexdigest()
        if actual_hash != entry["sha256"]:
            _verification_error("artifact_hash_mismatch", f"expected={entry['sha256']} actual={actual_hash}")

        mountpoint = temp_dir / "mount"
        mountpoint.mkdir()
        attached = _run([*hdiutil, "attach", str(dmg_path), "-nobrowse", "-readonly", "-mountpoint", str(mountpoint)])
        if attached.returncode != 0:
            _verification_error("dmg_attach_failed", attached.stderr.strip() or attached.stdout.strip(), "infra_error")
        attach_lines = [line.strip() for line in attached.stdout.splitlines() if line.strip()]
        if attach_lines:
            possible = attach_lines[-1].split("\t")[-1]
            if pathlib.Path(possible).is_dir():
                mountpoint = pathlib.Path(possible)

        try:
            apps = list(mountpoint.glob(f"**/{APP_BUNDLE}"))
            if not apps:
                _verification_error("app_bundle_missing", f"{APP_BUNDLE} not found", "infra_error")
            source_app = apps[0]
            codesign = _run([*_command("OPAL_EGO_CODESIGN_CMD", "codesign"), "--verify", "--deep", "--strict", str(source_app)])
            if codesign.returncode != 0:
                _verification_error("codesign_verify_failed", codesign.stderr.strip() or codesign.stdout.strip())
            spctl = _run([*_command("OPAL_EGO_SPCTL_CMD", "spctl"), "--assess", "--type", "execute", str(source_app)])
            if spctl.returncode != 0:
                _verification_error("notarization_verify_failed", spctl.stderr.strip() or spctl.stdout.strip())

            install_root = pathlib.Path(os.environ.get("OPAL_EGO_INSTALL_ROOT", str(pathlib.Path.home() / "Applications")))
            install_root.mkdir(parents=True, exist_ok=True)
            target = install_root / APP_BUNDLE
            if target.exists():
                _verification_error("install_target_exists", f"preserved existing target: {target}")
            staged = install_root / f".{APP_BUNDLE}.opal-staging"
            if staged.exists():
                _verification_error("install_staging_exists", f"preserved unexpected staging path: {staged}")
            try:
                copied = _run([*_command("OPAL_EGO_DITTO_CMD", "/usr/bin/ditto"), str(source_app), str(staged)])
                if copied.returncode != 0:
                    _verification_error("app_copy_failed", copied.stderr.strip() or copied.stdout.strip(), "infra_error")
                staged_codesign = _run([*_command("OPAL_EGO_CODESIGN_CMD", "codesign"), "--verify", "--deep", "--strict", str(staged)])
                if staged_codesign.returncode != 0:
                    _verification_error("installed_codesign_verify_failed", staged_codesign.stderr.strip() or staged_codesign.stdout.strip())
                staged_spctl = _run([*_command("OPAL_EGO_SPCTL_CMD", "spctl"), "--assess", "--type", "execute", str(staged)])
                if staged_spctl.returncode != 0:
                    _verification_error("installed_notarization_verify_failed", staged_spctl.stderr.strip() or staged_spctl.stdout.strip())
                os.replace(staged, target)
            except Exception:
                if staged.exists():
                    shutil.rmtree(staged)
                raise
        finally:
            _run([*hdiutil, "detach", str(mountpoint), "-quiet"])

    _emit({
        "ok": False,
        "command": "install",
        "status": "awaiting_human",
        "operational_status": "awaiting_human",
        "version": entry["version"],
        "platform": platform_key,
        "sha256": entry["sha256"],
        "app": str(target),
        "verification": ["hdiutil", "sha256", "codesign", "spctl"],
        "handoff": _handoff(resume_url, resume_expected, choice="r2"),
    })


def _safe_actual(actual: Any, expected: str) -> str:
    text = str(actual or "")
    location = text.find(expected) if expected else -1
    if location >= 0:
        start = max(0, location - 120)
        return text[start : location + len(expected) + 120]
    return text[:500]


def cmd_smoke(args: argparse.Namespace) -> None:
    if not _platform_key():
        _emit({"ok": False, "command": "smoke", "status": "provider_unavailable", "error": "unsupported_platform"})
    cli = _candidate_cli()
    if not cli:
        if args.install_choice == "cancel":
            _emit({"ok": False, "command": "smoke", "status": "provider_unavailable", "error": "ego_not_selected"})
        if args.install_choice == "r2":
            cmd_install(args)
        _emit({
            "ok": False,
            "command": "smoke",
            "status": "awaiting_human",
            "operational_status": "awaiting_human",
            "handoff": _handoff(args.url, args.expect_text, choice=args.install_choice),
        })
    if not args.expect_text:
        _emit({"ok": False, "command": "smoke", "status": "fail", "error": "assertion_required"})

    js = f'''const task = await taskSpace("OPAL browser assertion");
const page = task.page("p1");
await page.goto({json.dumps(args.url)});
const actual = await page.evaluate(() => document.body ? document.body.innerText : "");
console.log({json.dumps(SENTINEL)} + JSON.stringify({{status:"pass", space_id:task.spaceId, actual}}));
await task.finish({{keep: []}});'''
    result = _run([cli, "nodejs", "-e", js])
    output_lines = [*result.stdout.splitlines(), *result.stderr.splitlines()]
    sentinels = [line[len(SENTINEL) :] for line in output_lines if line.startswith(SENTINEL)]
    if result.returncode != 0 or len(sentinels) != 1:
        _emit({
            "ok": False,
            "command": "smoke",
            "status": "infra_error",
            "error": "ego_result_invalid",
            "detail": "ego-browser did not return exactly one successful sentinel",
        })
    try:
        observed = json.loads(sentinels[0])
    except json.JSONDecodeError as exc:
        _emit({"ok": False, "command": "smoke", "status": "infra_error", "error": "ego_result_invalid", "detail": str(exc)})
    if observed.get("status") in {"blocked", "awaiting_human", "infra_error"}:
        _emit({"ok": False, "command": "smoke", "status": observed["status"], "space_id": observed.get("space_id")})
    actual = _safe_actual(observed.get("actual"), args.expect_text)
    status = "pass" if args.expect_text in str(observed.get("actual") or "") else "fail"
    _emit({
        "ok": status == "pass",
        "command": "smoke",
        "status": status,
        "driver": "ego-lite",
        "space_id": observed.get("space_id"),
        "url": args.url,
        "expected": args.expect_text,
        "actual": actual,
    })


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ego-browser-tool", description="Verified Ego Lite provider adapter")
    sub = parser.add_subparsers(dest="command", required=True)
    status = sub.add_parser("status", help="Inspect platform, app, and CLI readiness")
    status.set_defaults(handler=cmd_status)
    install = sub.add_parser("install", help="Install pinned Ego Lite after integrity and trust verification")
    install.set_defaults(handler=cmd_install)
    smoke = sub.add_parser("smoke", help="Run one public browser text assertion")
    smoke.add_argument("url")
    smoke.add_argument("--expect-text")
    smoke.add_argument("--install-choice", choices=["manual", "r2", "cancel"])
    smoke.set_defaults(handler=cmd_smoke)
    return parser


def main() -> None:
    args = _parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
