"""
@header {
  "module": "routers.brain",
  "layer": "router",
  "domain": "console",
  "description": "대화별 session_id 격리: GET /api/brain/auth — shutil.which(claude) 경량 체크. GET /api/brain/status?project=<경로>&session_id=<id> — project·session_id 필수, BrainSessionRegistry.status(session_id) 반환. session_id 미등록 시 state=idle 응답(아직 프라임 안 된 대화). POST /api/brain/prime — project·session_id 필수, 빈값/무효→400, 그 session_id 세션만 콜드 프라임(다른 세션 불변), 백그라운드 스레드로 트리거(prime-on-intent). POST /api/brain/query — project·session_id 필수, 빈값/무효→400, BrainSessionRegistry.submit_job 호출 → job_id 즉시 반환(BrainJobSubmitResponse). 미등록 session_id로 query 오면 콜드 잡 자동 등록(robust). GET /api/brain/job/{job_id}?project=<>&session_id=<> — 잡 상태 폴링, BrainJobResponse(job_id,status,answer,citations,error_msg). 잡 소멸/미존재 시 graceful error 응답. [MUST] LLM 호출은 이 라우터에만 격리. project·session_id 빈값·무효 → 명시적 400 반환.",
  "exports": ["GET /api/brain/auth", "GET /api/brain/status", "POST /api/brain/prime", "POST /api/brain/query", "GET /api/brain/job/{job_id}"],
  "depends": ["adapters.brain_session", "adapters.opbr_adapter", "models", "scanner", "config"],
  "changelog": [
    "2026-06-23 Step3: POST /query → submit_job 비동기(BrainJobSubmitResponse), GET /api/brain/job/{job_id} 신설(PLAN §3.1.2)"
  ]
}
"""
from __future__ import annotations

import logging
import shutil
import threading

from fastapi import APIRouter, HTTPException, Query

from dashboard.backend.adapters.base import ToolError
from dashboard.backend.adapters.brain_session import brain_session_registry
from dashboard.backend.config import load_config
from dashboard.backend.models import (
    BrainAuthResponse,
    BrainJobResponse,
    BrainJobSubmitResponse,
    BrainPrimeResponse,
    BrainQueryRequest,
    BrainStatusResponse,
)
from dashboard.backend.scanner import scan_projects

router = APIRouter()

logger = logging.getLogger(__name__)


# ── project 경로 결정 헬퍼 ────────────────────────────────────────────────────────

def _resolve_project_path(project: str) -> str:
    """project 절대경로 검증 및 반환.

    project가 빈 값이거나 스캔된 프로젝트 목록에 존재하지 않으면 빈 문자열 반환.
    호출자가 빈 문자열 반환 시 HTTP 400을 발행한다.
    """
    if not project:
        return ""

    cfg = load_config()
    projects = scan_projects(cfg.scan_roots, cfg.scan_depth, cfg.exclude)

    for p in projects:
        if p.path == project:
            return p.path

    return ""


def _require_project_path(project: str) -> str:
    """project 검증 후 절대경로 반환. 실패 시 HTTPException(400) raise."""
    if not project:
        raise HTTPException(
            status_code=400,
            detail="project가 필수입니다. OPAL 프로젝트 절대경로를 지정하세요.",
        )

    resolved = _resolve_project_path(project)
    if not resolved:
        raise HTTPException(
            status_code=400,
            detail=f"프로젝트를 찾을 수 없습니다: {project!r}",
        )

    return resolved


def _require_session_id(session_id: str | None) -> str:
    """session_id 검증. 빈 값/None이면 HTTPException(400) raise."""
    if not session_id:
        raise HTTPException(
            status_code=400,
            detail="session_id가 필수입니다. FE가 생성한 대화 식별자(UUID)를 지정하세요.",
        )
    return session_id


# ── GET /api/brain/auth ──────────────────────────────────────────────────────────

@router.get("/api/brain/auth", response_model=BrainAuthResponse)
def get_brain_auth() -> BrainAuthResponse:
    """claude CLI 가용 여부 경량 체크.

    [MUST] 실 claude -p 서브프로세스 호출 0회 — shutil.which만 사용(H-8).
    """
    cli_path = shutil.which("claude")
    cli_available = cli_path is not None

    if not cli_available:
        return BrainAuthResponse(
            authenticated=False,
            cli_available=False,
            message=(
                "Claude Code CLI(claude)가 설치되어 있지 않거나 로그인되지 않았습니다. "
                "Claude Code를 설치하고 로그인하면 브레인 질의를 사용할 수 있습니다."
            ),
        )

    # 설치 확인됨 → 구독 유효성은 POST /api/brain/query의 is_error로 자연 검증
    return BrainAuthResponse(
        authenticated=True,
        cli_available=True,
        message="",
    )


# ── GET /api/brain/status ────────────────────────────────────────────────────────

@router.get("/api/brain/status", response_model=BrainStatusResponse)
def get_brain_status(
    project: str = Query(..., description="OPAL 프로젝트 절대경로 (필수)"),
    session_id: str = Query(..., description="대화 식별자 (필수)"),
) -> BrainStatusResponse:
    """대화별 BrainSession 연동 상태 조회.

    FE가 prime 트리거 후 폴링하여 ready 전환을 감지한다.
    session_id가 레지스트리에 없으면 state=idle 반환 (아직 프라임 안 된 대화).

    Args:
        project: OPAL 프로젝트 절대경로 (쿼리 파라미터, 필수)
        session_id: 대화 식별자 (쿼리 파라미터, 필수)

    Returns:
        {state, session_active, message, session_id}
        state: "idle"|"priming"|"ready"|"error"
        session_active: bool — claude session_id 보유 여부
        message: error 시 사유, 그 외 ""
        session_id: 에코

    Raises:
        HTTPException(400): project·session_id 빈 값 또는 project 미존재
    """
    _require_project_path(project)
    sid = _require_session_id(session_id)

    s = brain_session_registry.status(sid)
    return BrainStatusResponse(
        state=s["state"],
        session_active=s["session_active"],
        message=s["message"],
        session_id=sid,
    )


# ── POST /api/brain/prime ────────────────────────────────────────────────────────

@router.post("/api/brain/prime", response_model=BrainPrimeResponse)
def post_brain_prime(body: dict | None = None) -> BrainPrimeResponse:
    """prime-on-intent: session_id 세션만 콜드 프라임을 백그라운드 스레드로 트리거, 즉시 반환.

    다른 session_id 세션은 완전히 독립 — 영향 없음.
    이미 웜이면 no-op (ConversationBrainSession.prime 내부에서 guard).
    진행 중(_priming=True)이면 no-op.

    Args:
        body: {
            "project": "<절대경로>",    — 필수. 빈 값이면 400.
            "session_id": "<UUID>",    — 필수. 빈 값이면 400.
        }

    Returns:
        {"priming": true} — 백그라운드 프라임 시작됨 또는 이미 웜

    Raises:
        HTTPException(400): project·session_id 빈 값 또는 project 미존재
    """
    project = ""
    session_id = ""
    if body and isinstance(body, dict):
        project = body.get("project", "")
        session_id = body.get("session_id", "")

    project_path = _require_project_path(project)
    sid = _require_session_id(session_id)

    logger.info("[brain] POST /prime 접수 session=%s project=%s", sid[:8], project_path)

    # 백그라운드 스레드로 prime 트리거 (즉시 반환)
    t = threading.Thread(
        target=_prime_background,
        args=(sid, project_path),
        daemon=True,
    )
    t.start()

    return BrainPrimeResponse(priming=True)


def _prime_background(session_id: str, project_path: str) -> None:
    """백그라운드 스레드에서 BrainSessionRegistry.prime 실행. 실패는 조용히 무시."""
    try:
        brain_session_registry.prime(session_id, project_path)
    except Exception:
        pass  # 백그라운드 프라임 실패는 다음 ask에서 콜드로 재시도


# ── POST /api/brain/query ────────────────────────────────────────────────────────

@router.post("/api/brain/query", response_model=BrainJobSubmitResponse)
def post_brain_query(body: BrainQueryRequest) -> BrainJobSubmitResponse:
    """opbr 질의 — 비동기 잡 제출. job_id를 즉시 반환하고 백그라운드에서 ask를 실행한다.

    session_id가 레지스트리에 없으면 (서버재시작 후 등) 콜드 잡으로 자동 등록(robust).
    잡 결과는 GET /api/brain/job/{job_id}?project=<>&session_id=<> 폴링으로 수신.

    Args:
        body: {question, project, session_id, new_conversation?}
            project: 필수. 빈 값이면 400.
            session_id: 필수. 빈 값이면 400.
            new_conversation: 호환 목적으로 수신하되 reset 트리거하지 않음(폐기).

    Returns:
        {job_id}: 즉시 반환 — 블로킹 없음

    Raises:
        HTTPException(400): project·session_id 빈 값 또는 project 미존재
    """
    project_path = _require_project_path(body.project)
    sid = _require_session_id(body.session_id)

    logger.info(
        "[brain] POST /query 접수 session=%s project=%s q=%r",
        sid[:8], project_path, (body.question or "")[:60],
    )

    # [NOTE] new_conversation에 의한 reset은 query에서 수행하지 않는다(폐기).
    # 대화별 session_id 설계에서 새 대화는 FE가 새 session_id를 생성·전달하는 것으로 처리.

    try:
        job_id = brain_session_registry.submit_job(
            session_id=sid,
            question=body.question,
            project_path=project_path,
        )
    except ToolError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                f"브레인 도구 초기화에 실패했습니다. "
                f"OPAL 프로젝트가 설정되어 있는지 확인해주세요. ({exc})"
            ),
        ) from exc
    except RuntimeError as exc:
        # 어댑터 즉시 실패(인증 오류 등) → 502
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return BrainJobSubmitResponse(job_id=job_id)


# ── GET /api/brain/job/{job_id} ──────────────────────────────────────────────────

@router.get("/api/brain/job/{job_id}", response_model=BrainJobResponse)
def get_brain_job(
    job_id: str,
    project: str = Query(..., description="OPAL 프로젝트 절대경로 (필수)"),
    session_id: str = Query(..., description="대화 식별자 (필수)"),
) -> BrainJobResponse:
    """비동기 잡 상태 폴링. job_id·project·session_id 필수.

    잡이 소멸됐거나 job_id가 불일치하면 graceful error 응답(500 아님).

    Args:
        job_id: 조회할 잡의 식별자 (path parameter)
        project: OPAL 프로젝트 절대경로 (query parameter, 필수)
        session_id: 대화 식별자 (query parameter, 필수)

    Returns:
        BrainJobResponse: {job_id, status, answer, citations, error_msg}
            status: "pending" | "done" | "error"

    Raises:
        HTTPException(400): project·session_id 빈 값 또는 project 미존재
    """
    _require_project_path(project)
    sid = _require_session_id(session_id)

    job = brain_session_registry.get_job(sid, job_id)
    if job is None:
        # 잡 소멸(TTL) 또는 session_id/job_id 불일치 — graceful 반환
        return BrainJobResponse(
            job_id=job_id,
            status="error",
            error_msg="잡을 찾을 수 없습니다(세션이 재시작되었을 수 있습니다)",
        )

    return BrainJobResponse(**job)
