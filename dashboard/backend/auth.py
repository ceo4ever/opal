"""
@header {
  "module": "auth",
  "layer": "service",
  "domain": "console",
  "description": "Console 인증 경계. 순수 ASGI 미들웨어 AuthMiddleware가 http·websocket scope를 라우팅 전에 Host → Origin → 세션 → CSRF 순으로 검사해 요청 본문을 읽기 전에 거절한다. Host는 모든 경로에서 호스트명(포트 제외)이 127.0.0.1·localhost·[::1] 또는 OPAL_CONSOLE_ALLOWED_HOSTS(쉼표 구분, 형식 불일치 항목은 경고 후 제외)에 있어야 하고 위반은 403 host_not_allowed. /api/ 경로는 Origin이 있으면 요청 Host 기준 동일 출처 또는 생성자에 전달된 CORS origin과 정확히 일치해야 하며(403 origin_not_allowed) POST·PUT·PATCH·DELETE 등 상태 변경 메서드는 Origin이 없어도 거절한다(403 origin_required). /api/ 하위는 세션 쿠키 opal_console_session 필수(401 auth_required)이며 예외는 POST /api/auth/exchange와 GET /api/auth/session 2종뿐이다. 상태 변경 메서드는 X-CSRF-Token이 세션의 csrf 값과 compare_digest로 일치해야 한다(403 csrf_invalid). WebSocket은 Host·Origin(필수)·세션을 검사하고 실패하면 accept 전에 close 1008을 보낸다. SPA 정적 경로와 /health는 Host 검사만 받는다. SessionStore는 SHA-256 해시 키 인메모리 세션(12시간 절대 만료, 재시작 시 소멸)과 세션별 csrf 값을 보관한다. 세션·csrf·token 값은 로그·예외·URL에 남기지 않고 인증 우회 스위치는 없다. 오류 본문은 {\"error\":{\"code\",\"message\"}} 형식이다.",
  "exports": ["AuthMiddleware", "SessionStore", "Session", "session_store", "SESSION_COOKIE", "SESSION_MAX_AGE", "error_response", "session_for_scope"],
  "depends": [],
  "task": "175-261001-opd-콘솔-POST-인증-게이트"
}
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import secrets
import threading
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

SESSION_COOKIE = "opal_console_session"
SESSION_MAX_AGE = 43200  # 12시간 절대 만료
_MAX_SESSIONS = 256

_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "[::1]"})
_HOST_ENTRY_RE = re.compile(r"^[A-Za-z0-9.\-\[\]:]+$")
_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

_EXCHANGE = ("POST", "/api/auth/exchange")
_SESSION_PROBE = ("GET", "/api/auth/session")

_MESSAGES = {
    "host_not_allowed": "허용되지 않은 Host입니다.",
    "origin_required": "Origin 헤더가 필요합니다.",
    "origin_not_allowed": "허용되지 않은 Origin입니다.",
    "auth_required": "인증이 필요합니다. 터미널에서 `opal-cli console open`으로 다시 여세요.",
    "csrf_invalid": "CSRF 검증에 실패했습니다.",
}
_STATUS = {
    "host_not_allowed": 403,
    "origin_required": 403,
    "origin_not_allowed": 403,
    "auth_required": 401,
    "csrf_invalid": 403,
}


def error_response(status: int, code: str, message: str) -> JSONResponse:
    """공통 오류 envelope. 자격 증명 값을 싣지 않는다."""
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


# ── 세션 저장소 ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Session:
    csrf_token: str
    expires_at: float


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class SessionStore:
    """인메모리 세션 저장소. 키는 세션 값의 SHA-256 해시이며 원문은 저장하지 않는다."""

    def __init__(self, max_age: int = SESSION_MAX_AGE, clock=time.time) -> None:
        self._max_age = max_age
        self._clock = clock
        self._lock = threading.Lock()
        self._sessions: dict[str, Session] = {}

    def create(self) -> tuple[str, str]:
        """새 세션을 만들고 (쿠키 값, csrf 값)을 돌려준다."""
        value = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(32)
        now = self._clock()
        with self._lock:
            self._prune(now)
            self._sessions[_digest(value)] = Session(csrf, now + self._max_age)
        return value, csrf

    def get(self, value: str | None) -> Session | None:
        if not value:
            return None
        key = _digest(value)
        with self._lock:
            session = self._sessions.get(key)
            if session is None:
                return None
            if session.expires_at <= self._clock():
                del self._sessions[key]
                return None
            return session

    def _prune(self, now: float) -> None:
        for key in [k for k, s in self._sessions.items() if s.expires_at <= now]:
            del self._sessions[key]
        while len(self._sessions) >= _MAX_SESSIONS:
            oldest = min(self._sessions, key=lambda k: self._sessions[k].expires_at)
            del self._sessions[oldest]


session_store = SessionStore()


# ── 요청 해석 ────────────────────────────────────────────────────────────────

def _header_map(scope) -> tuple[dict[str, str], list[str]]:
    """첫 값 기준 헤더 맵과 모든 Cookie 헤더 값 목록."""
    headers: dict[str, str] = {}
    cookies: list[str] = []
    for raw_name, raw_value in scope.get("headers", []):
        name = raw_name.decode("latin-1").lower()
        value = raw_value.decode("latin-1")
        if name == "cookie":
            cookies.append(value)
        headers.setdefault(name, value)
    return headers, cookies


def _cookie_value(cookie_headers: Iterable[str], name: str) -> str | None:
    for header in cookie_headers:
        for part in header.split(";"):
            key, sep, val = part.strip().partition("=")
            if sep and key == name:
                return val
    return None


def session_for_scope(scope, store: SessionStore | None = None) -> Session | None:
    """scope의 쿠키로 유효 세션을 찾는다. 없거나 만료면 None."""
    _headers, cookies = _header_map(scope)
    return (store or session_store).get(_cookie_value(cookies, SESSION_COOKIE))


def _hostname(host_header: str) -> str | None:
    """Host 헤더에서 포트를 뗀 호스트명을 돌려준다. 형식이 이상하면 None."""
    host = host_header.strip().lower()
    if not host or not _HOST_ENTRY_RE.match(host):
        return None
    if host.startswith("["):
        end = host.find("]")
        return host[: end + 1] if end != -1 else None
    return host.rsplit(":", 1)[0] if host.count(":") == 1 else host


@lru_cache(maxsize=8)
def _extra_hosts(raw: str) -> frozenset[str]:
    hosts: set[str] = set()
    for candidate in raw.split(","):
        entry = candidate.strip()
        if not entry:
            continue
        name = _hostname(entry) if _HOST_ENTRY_RE.match(entry) else None
        if name is None:
            logger.warning("[auth] OPAL_CONSOLE_ALLOWED_HOSTS 무효 항목 제외: %r", entry)
            continue
        hosts.add(name)
    return frozenset(hosts)


def _host_allowed(headers: dict[str, str]) -> bool:
    name = _hostname(headers.get("host", ""))
    if name is None:
        return False
    return name in _LOOPBACK_HOSTS or name in _extra_hosts(os.environ.get("OPAL_CONSOLE_ALLOWED_HOSTS", ""))


def _origin_allowed(origin: str, headers: dict[str, str], cors_origins: frozenset[str]) -> bool:
    if origin in cors_origins:
        return True
    return origin.lower() == f"http://{headers.get('host', '').strip().lower()}"


# ── 미들웨어 ─────────────────────────────────────────────────────────────────

class AuthMiddleware:
    """Host → Origin → 세션 → CSRF 순으로 거절하는 순수 ASGI 미들웨어."""

    def __init__(self, app, cors_origins: Iterable[str] = (), store: SessionStore | None = None) -> None:
        self.app = app
        self._cors_origins = frozenset(cors_origins)
        self._store = store or session_store

    async def __call__(self, scope, receive, send) -> None:
        kind = scope["type"]
        if kind not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        denial = self._check(scope, kind)
        if denial is None:
            await self.app(scope, receive, send)
            return
        if kind == "websocket":
            await receive()  # websocket.connect 소비 후 accept 없이 거절
            await send({"type": "websocket.close", "code": 1008})
            return
        await error_response(_STATUS[denial], denial, _MESSAGES[denial])(scope, receive, send)

    def _check(self, scope, kind: str) -> str | None:
        """거절 코드 또는 통과(None). 본문은 읽지 않는다."""
        headers, cookies = _header_map(scope)
        if not _host_allowed(headers):
            return "host_not_allowed"

        path = scope.get("path", "")
        is_api = path == "/api" or path.startswith("/api/")
        method = scope.get("method", "GET").upper() if kind == "http" else "GET"
        mutating = kind == "http" and method not in _SAFE_METHODS

        if not is_api and kind == "http":
            return None  # /health·SPA 정적 경로는 Host만 검사

        origin = headers.get("origin")
        if origin is None:
            if kind == "websocket" or mutating:
                return "origin_required"
        elif not _origin_allowed(origin, headers, self._cors_origins):
            return "origin_not_allowed"

        if kind == "http" and (method, path) in (_EXCHANGE, _SESSION_PROBE):
            return None  # default-deny 예외 2종

        session = self._store.get(_cookie_value(cookies, SESSION_COOKIE))
        if session is None:
            return "auth_required"

        if mutating:
            supplied = headers.get("x-csrf-token", "")
            if not supplied or not hmac.compare_digest(
                supplied.encode("utf-8"), session.csrf_token.encode("utf-8")
            ):
                return "csrf_invalid"
        return None
