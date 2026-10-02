"""
@header {
  "module": "console_session",
  "layer": "util",
  "domain": "opal-tools",
  "task": "175-261001-opd-콘솔-POST-인증-게이트",
  "description": "E2E 하네스 세션 부트스트랩 명령(`.opal/e2e/environment.json`의 session_bootstrap). 기동된 SUT가 상속한 OPAL_HOME에 dashboard.backend.entry_token.issue()로 진입 token 2개를 발급하고, 하나는 --base-url 백엔드의 POST /api/auth/exchange(Origin=base-url)에 직접 교환해 세션 쿠키·CSRF를 얻으며, 다른 하나는 브라우저 진입 fragment로 돌려준다. stdout에는 {headers: {Cookie, X-CSRF-Token, Origin}, browser_entry_fragment: entry=<token>} 한 줄 JSON만 쓰고, token·쿠키·CSRF 값은 stderr·로그에 쓰지 않는다. 실패는 값 없는 한 줄 사유를 stderr에 쓰고 비0으로 끝난다. 표준 라이브러리와 entry_token만 사용한다.",
  "exports": ["main"],
  "depends": ["entry_token"]
}
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from http.cookies import SimpleCookie

from dashboard.backend import entry_token

_SESSION_COOKIE = "opal_console_session"
_EXCHANGE_TIMEOUT_S = 10


def _fail(reason: str) -> int:
    sys.stderr.write(f"console_session: {reason}\n")
    return 1


def _exchange(base_url: str, token: str) -> tuple[str, str]:
    """진입 token을 세션으로 교환해 (쿠키 값, csrf 값)을 돌려준다. 실패는 ValueError(값 없음)."""
    request = urllib.request.Request(
        base_url + "/api/auth/exchange",
        data=json.dumps({"token": token}).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "Origin": base_url},
    )
    try:
        with urllib.request.urlopen(request, timeout=_EXCHANGE_TIMEOUT_S) as response:
            body = json.loads(response.read().decode("utf-8"))
            set_cookies = response.headers.get_all("Set-Cookie") or []
    except (urllib.error.URLError, OSError, ValueError):
        raise ValueError("exchange request failed") from None
    cookie_value = None
    for raw in set_cookies:
        parsed = SimpleCookie()
        try:
            parsed.load(raw)
        except Exception:  # noqa: BLE001 — 형식 오류 쿠키는 건너뛴다.
            continue
        if _SESSION_COOKIE in parsed:
            cookie_value = parsed[_SESSION_COOKIE].value
            break
    csrf = body.get("csrf_token") if isinstance(body, dict) else None
    if not cookie_value or not isinstance(csrf, str) or not csrf:
        raise ValueError("exchange response incomplete")
    return cookie_value, csrf


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="E2E console session bootstrap")
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args(argv)
    base_url = args.base_url.rstrip("/")
    try:
        exchange_token = entry_token.issue()
        browser_token = entry_token.issue()
    except Exception:  # noqa: BLE001 — 예외 문구에 경로·값이 섞이지 않게 사유만 남긴다.
        return _fail("entry token issue failed")
    try:
        cookie_value, csrf = _exchange(base_url, exchange_token)
    except ValueError as exc:
        return _fail(str(exc))
    payload = {
        "headers": {
            "Cookie": f"{_SESSION_COOKIE}={cookie_value}",
            "X-CSRF-Token": csrf,
            "Origin": base_url,
        },
        "browser_entry_fragment": f"entry={browser_token}",
    }
    sys.stdout.write(json.dumps(payload) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
