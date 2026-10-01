"""
@header {
  "module": "routers.auth",
  "layer": "router",
  "domain": "console",
  "description": "Console 인증 엔드포인트 2종. POST /api/auth/exchange는 본문 {\"token\"}의 진입 token을 entry_token.consume으로 1회 소비하고 성공 시 200 {\"authenticated\": true, \"csrf_token\"}와 세션 쿠키(HttpOnly; SameSite=Strict; Path=/; Max-Age=43200, Secure 없음)를 발급하며 실패(만료·재사용·위조·본문 오류 모두)는 사유를 구별하지 않는 401 entry_token_invalid다. GET /api/auth/session은 항상 200으로 {\"authenticated\": false} 또는 {\"authenticated\": true, \"csrf_token\"}만 돌려주고 프로젝트·설정·계정 정보를 싣지 않는다. 두 경로는 AuthMiddleware의 default-deny 예외 2종이며 Origin 검사는 미들웨어가 한다. token·세션·csrf 값은 로그에 남기지 않는다.",
  "exports": ["router"],
  "depends": ["auth", "entry_token"],
  "task": "172-261001-opd-콘솔-POST-인증-게이트"
}
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from dashboard.backend import auth, entry_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

_MAX_BODY_BYTES = 4096


@router.post("/exchange")
async def exchange(request: Request) -> JSONResponse:
    """진입 token을 세션으로 교환한다."""
    invalid = auth.error_response(401, "entry_token_invalid", "진입 token이 유효하지 않습니다.")
    try:
        raw = await request.body()
        if len(raw) > _MAX_BODY_BYTES:
            return invalid
        body = await request.json()
        token = body.get("token") if isinstance(body, dict) else None
    except (ValueError, UnicodeDecodeError):
        return invalid
    if not await run_in_threadpool(entry_token.consume, token):
        return invalid

    cookie_value, csrf = auth.session_store.create()
    response = JSONResponse({"authenticated": True, "csrf_token": csrf})
    response.set_cookie(
        auth.SESSION_COOKIE,
        cookie_value,
        max_age=auth.SESSION_MAX_AGE,
        path="/",
        httponly=True,
        samesite="strict",
    )
    return response


@router.get("/session")
def session(request: Request) -> dict:
    """현재 세션 상태. 계정·설정 정보는 싣지 않는다."""
    current = auth.session_for_scope(request.scope)
    if current is None:
        return {"authenticated": False}
    return {"authenticated": True, "csrf_token": current.csrf_token}
