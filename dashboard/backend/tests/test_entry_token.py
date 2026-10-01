"""
@header {
  "module": "tests.test_entry_token",
  "layer": "test",
  "domain": "console",
  "description": "진입 token 발급 채널 공개 계약 RED-first 테스트(S-5 발급 측). 임시 OPAL_HOME에서 dashboard.backend.entry_token.issue()가 만드는 디렉터리(0700)·파일(0600)·파일명(token의 SHA-256 16진)·내용(만료 시각만, token 없음)·기본 TTL(60초, 상한 300초), 발급 때의 만료 파일 청소, token 유일성, 로그 비노출, 디렉터리가 symlink이거나 그룹/타인 권한이 열려 있으면 발급 거부, CLI(python -m dashboard.backend.entry_token issue [--ttl N])가 stdout에 token 한 줄만 쓰는지를 검증한다. 소비 측 계약(1회성·만료·위조)은 test_auth_gate.py가 POST /api/auth/exchange로 검증한다. 사용자 ~/.opal은 건드리지 않는다(항상 임시 OPAL_HOME).",
  "task": "172-261001-opd-콘솔-POST-인증-게이트",
  "scenarios": ["S-5"],
  "exports": [],
  "depends": ["entry_token"]
}
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def home(monkeypatch, tmp_path) -> Path:
    opal_home = tmp_path / ".opal"
    opal_home.mkdir()
    monkeypatch.setenv("OPAL_HOME", str(opal_home))
    return opal_home


def _entry_dir(home: Path) -> Path:
    return home / "run" / "console-entry"


def _issue(**kwargs) -> str:
    from dashboard.backend import entry_token

    return entry_token.issue(**kwargs)


def _mode(path: Path) -> int:
    return stat.S_IMODE(os.stat(path).st_mode)


def test_issue_creates_private_dir_and_hashed_file(home):
    token = _issue()

    entry_dir = _entry_dir(home)
    assert entry_dir.is_dir() and not entry_dir.is_symlink()
    assert _mode(entry_dir) == 0o700
    files = list(entry_dir.iterdir())
    assert len(files) == 1
    entry = files[0]
    assert _mode(entry) == 0o600
    assert entry.name == hashlib.sha256(token.encode()).hexdigest()
    assert token not in entry.name
    content = entry.read_text(encoding="utf-8")
    assert token not in content
    assert set(json.loads(content).keys()) == {"expires_at"}


def test_issue_token_is_url_safe_and_unique(home):
    tokens = {_issue() for _ in range(20)}

    assert len(tokens) == 20
    assert all(re.fullmatch(r"[A-Za-z0-9_-]{32,}", t) for t in tokens)
    assert len(list(_entry_dir(home).iterdir())) == 20


def test_issue_default_ttl_is_60_seconds(home):
    before = time.time()
    token = _issue()
    after = time.time()

    entry = _entry_dir(home) / hashlib.sha256(token.encode()).hexdigest()
    expires_at = json.loads(entry.read_text(encoding="utf-8"))["expires_at"]
    assert before + 59 <= expires_at <= after + 61


def test_issue_sweeps_expired_files(home):
    _issue()
    entry_dir = _entry_dir(home)
    stale = entry_dir / ("a" * 64)
    stale.write_text(json.dumps({"expires_at": time.time() - 100}), encoding="utf-8")
    stale.chmod(0o600)

    fresh = _issue()

    names = {p.name for p in entry_dir.iterdir()}
    assert stale.name not in names
    assert hashlib.sha256(fresh.encode()).hexdigest() in names


def test_issue_does_not_log_the_token(home, caplog):
    caplog.set_level(logging.DEBUG)

    token = _issue()

    assert token not in caplog.text


@pytest.mark.parametrize("tamper", ["symlink_dir", "mode_0755", "mode_0770"])
def test_issue_refuses_tampered_directory(home, tamper):
    _issue()
    entry_dir = _entry_dir(home)
    if tamper == "symlink_dir":
        real = entry_dir.with_name("console-entry-real")
        entry_dir.rename(real)
        entry_dir.symlink_to(real, target_is_directory=True)
    else:
        entry_dir.chmod(0o755 if tamper == "mode_0755" else 0o770)

    try:
        token = _issue()
    except Exception:
        token = None

    assert not token, "issue must refuse an entry directory that is a symlink or not owner-only"


def _run_cli(home: Path, *args: str) -> subprocess.CompletedProcess:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(home.parent),
        "OPAL_HOME": str(home),
        "PYTHONPATH": str(REPO_ROOT),
    }
    return subprocess.run(
        [sys.executable, "-m", "dashboard.backend.entry_token", *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(home.parent),
        timeout=30,
    )


def test_cli_issue_prints_only_the_token(home):
    proc = _run_cli(home, "issue")

    assert proc.returncode == 0, proc.stderr
    token = proc.stdout.strip()
    assert re.fullmatch(r"[A-Za-z0-9_-]{32,}", token), proc.stdout
    assert proc.stdout.count("\n") <= 1
    assert token not in proc.stderr
    entry = _entry_dir(home) / hashlib.sha256(token.encode()).hexdigest()
    assert entry.is_file() and _mode(entry) == 0o600


def test_cli_issue_honors_ttl(home):
    before = time.time()
    proc = _run_cli(home, "issue", "--ttl", "30")

    assert proc.returncode == 0, proc.stderr
    token = proc.stdout.strip()
    entry = _entry_dir(home) / hashlib.sha256(token.encode()).hexdigest()
    expires_at = json.loads(entry.read_text(encoding="utf-8"))["expires_at"]
    assert before + 28 <= expires_at <= time.time() + 31


def test_cli_issue_fails_without_leaking_when_directory_tampered(home):
    first = _run_cli(home, "issue")
    assert first.returncode == 0
    _entry_dir(home).chmod(0o755)

    proc = _run_cli(home, "issue")

    assert proc.returncode != 0
    assert proc.stdout.strip() == ""
