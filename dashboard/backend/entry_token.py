"""
@header {
  "module": "entry_token",
  "layer": "service",
  "domain": "console",
  "description": "Console 1회성 진입 token 채널. <OPAL_HOME>/run/console-entry/(OPAL_HOME 환경 변수는 호출 시점에 읽고 없으면 ~/.opal)를 0700으로 만들고, 소유자 uid·권한(그룹/타인 비트 없음)·symlink 여부를 확인하지 못하면 발급·소비를 거부한다. issue(ttl)는 secrets.token_urlsafe(32) token을 만들어 token 전체 SHA-256 16진 64자를 이름으로 하는 0600 파일(O_CREAT|O_EXCL)에 {\"expires_at\": epoch초}만 쓰고(기본 TTL 60초, 상한 300초) 발급 때 만료 파일을 청소하며 token 원문은 디스크·로그에 남기지 않는다. consume(token)은 파일을 고유 이름으로 os.rename해 원자적으로 1회만 성공시키고 만료·TTL 상한 초과·부재·위조·디렉터리 위조를 구별하지 않는 False로 돌려준다. CLI: python -m dashboard.backend.entry_token issue [--ttl N]은 stdout에 token 한 줄만 출력하고 실패 시 stdout 없이 비0 종료한다. 표준 라이브러리만 사용한다.",
  "exports": ["issue", "consume", "entry_dir", "EntryChannelError", "DEFAULT_TTL_SECONDS", "MAX_TTL_SECONDS"],
  "depends": [],
  "task": "172-261001-opd-콘솔-POST-인증-게이트"
}
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import stat
import sys
import time
import uuid
from pathlib import Path

DEFAULT_TTL_SECONDS = 60
MAX_TTL_SECONDS = 300

_NAME_RE = re.compile(r"^[0-9a-f]{64}$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{16,256}$")
_CONSUMING_PREFIX = ".consuming-"
_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)


class EntryChannelError(RuntimeError):
    """진입 token 채널을 안전하게 쓸 수 없을 때(디렉터리 위조 등). 메시지에 token을 싣지 않는다."""


def _opal_home() -> Path:
    raw = os.environ.get("OPAL_HOME")
    return Path(raw) if raw else Path.home() / ".opal"


def entry_dir() -> Path:
    """진입 token 디렉터리 경로(호출 시점의 OPAL_HOME 기준)."""
    return _opal_home() / "run" / "console-entry"


def _verify_dir(path: Path) -> None:
    """디렉터리가 symlink가 아니고 현재 사용자 소유이며 그룹/타인 권한이 없음을 확인한다."""
    try:
        st = os.lstat(path)
    except OSError as exc:
        raise EntryChannelError("entry directory unavailable") from exc
    if not stat.S_ISDIR(st.st_mode):  # symlink는 lstat에서 S_ISLNK이므로 여기서 걸러진다
        raise EntryChannelError("entry directory is not a plain directory")
    if hasattr(os, "geteuid") and st.st_uid != os.geteuid():
        raise EntryChannelError("entry directory has a foreign owner")
    if stat.S_IMODE(st.st_mode) & 0o077:
        raise EntryChannelError("entry directory is not owner-only")


def _ensure_dir() -> Path:
    path = entry_dir()
    if not os.path.lexists(path):
        for parent in (path.parent.parent, path.parent):
            try:
                os.mkdir(parent, 0o700)
            except FileExistsError:
                pass
        try:
            os.mkdir(path, 0o700)
        except FileExistsError:
            pass
        else:
            os.chmod(path, 0o700)  # umask 영향 제거
    _verify_dir(path)
    return path


def _read_expiry(path: Path) -> float | None:
    """일반 파일·소유자·0600 조건을 만족하는 항목의 expires_at을 읽는다. 아니면 None."""
    try:
        st = os.lstat(path)
        if not stat.S_ISREG(st.st_mode):
            return None
        if hasattr(os, "geteuid") and st.st_uid != os.geteuid():
            return None
        if stat.S_IMODE(st.st_mode) & 0o077:
            return None
        fd = os.open(path, os.O_RDONLY | _NOFOLLOW)
        try:
            raw = os.read(fd, 4096)
        finally:
            os.close(fd)
        value = json.loads(raw.decode("utf-8")).get("expires_at")
    except (OSError, ValueError, AttributeError):
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _sweep(directory: Path, now: float) -> None:
    try:
        names = os.listdir(directory)
    except OSError:
        return
    for name in names:
        if not _NAME_RE.match(name):
            continue
        entry = directory / name
        expiry = _read_expiry(entry)
        if expiry is None or expiry <= now:
            try:
                os.unlink(entry)
            except OSError:
                pass


def issue(ttl: int | float = DEFAULT_TTL_SECONDS) -> str:
    """진입 token을 발급해 돌려준다. 디렉터리가 안전하지 않으면 EntryChannelError."""
    if isinstance(ttl, bool) or not isinstance(ttl, (int, float)) or ttl <= 0:
        raise ValueError("ttl must be a positive number")
    ttl = min(float(ttl), float(MAX_TTL_SECONDS))
    directory = _ensure_dir()
    now = time.time()
    _sweep(directory, now)
    token = secrets.token_urlsafe(32)
    name = hashlib.sha256(token.encode("utf-8")).hexdigest()
    payload = json.dumps({"expires_at": now + ttl}).encode("utf-8")
    fd = os.open(directory / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | _NOFOLLOW, 0o600)
    try:
        os.fchmod(fd, 0o600) if hasattr(os, "fchmod") else None
        os.write(fd, payload)
    finally:
        os.close(fd)
    return token


def consume(token: object) -> bool:
    """token을 1회 소비한다. 성공만 True, 그 밖의 모든 사유는 구별 없이 False."""
    if not isinstance(token, str) or not _TOKEN_RE.match(token):
        return False
    try:
        directory = entry_dir()
        _verify_dir(directory)
    except EntryChannelError:
        return False
    name = hashlib.sha256(token.encode("utf-8")).hexdigest()
    claimed = directory / f"{_CONSUMING_PREFIX}{uuid.uuid4().hex}"
    try:
        os.rename(directory / name, claimed)  # 원자적: 동시 소비 중 하나만 성공
    except OSError:
        return False
    try:
        expiry = _read_expiry(claimed)
        now = time.time()
        return expiry is not None and now < expiry <= now + MAX_TTL_SECONDS
    finally:
        try:
            os.unlink(claimed)
        except OSError:
            pass


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m dashboard.backend.entry_token")
    sub = parser.add_subparsers(dest="command", required=True)
    issue_parser = sub.add_parser("issue", help="진입 token을 발급해 stdout에 출력한다")
    issue_parser.add_argument("--ttl", type=int, default=DEFAULT_TTL_SECONDS)
    args = parser.parse_args(argv)
    try:
        token = issue(ttl=args.ttl)
    except (EntryChannelError, OSError, ValueError) as exc:
        print(f"entry token issue failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    sys.stdout.write(token + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
