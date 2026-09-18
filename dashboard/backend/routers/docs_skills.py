"""
@header {
  "module": "routers.docs_skills",
  "layer": "router",
  "domain": "console",
  "description": "GET /api/docs/skills · GET /api/docs/skills/{skill_id} — Docs 스킬 문서 화면 공개 표면(PLAN DEC-6). GET 2개만 등록하고 SPA fallback보다 앞에 둔다. corpus_root는 get_skill_docs_corpus_root 의존성으로만 주입되며(운영: ~/.opal, 테스트: dependency_overrides로 fixture root) 요청 파라미터로 지정할 수 없다. 매 요청 build_skill_docs_corpus()를 재구성한다(캐시 없음, DEC-4). adapter의 SkillDocsCorpusError 계층(code 속성)을 HTTP 상태로 매핑한다: skill_not_found→404, registry_unavailable/parse_error→500, 그 외 도메인 에러→500. 오류 응답은 stack trace·내부 경로 없이 error envelope({error:{code,message}})만 반환한다. trigger 정규식·pipeline 실행 없음, 읽기 전용.",
  "exports": ["router", "get_skill_docs_corpus_root"],
  "depends": ["adapters.skill_docs_adapter", "models"]
}
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from dashboard.backend.adapters.skill_docs_adapter import (
    SkillDocsCorpusError,
    build_skill_docs_corpus,
)
from dashboard.backend.models import (
    ErrorDetail,
    ErrorEnvelope,
    SkillCatalogListResponse,
    SkillDetailResponse,
)

router = APIRouter(prefix="/api/docs/skills", tags=["docs-skills"])


def get_skill_docs_corpus_root() -> Path:
    """운영 기본 corpus root — DI 지점.

    테스트는 FastAPI `app.dependency_overrides[get_skill_docs_corpus_root]`로
    fixture 디렉토리를 주입한다(PLAN DEC-6: 호출자가 경로를 지정할 수 없음).
    """
    return Path.home() / ".opal"


def _error_status(exc: SkillDocsCorpusError) -> int:
    if exc.code == "skill_not_found":
        return 404
    return 500


def _error_response(exc: SkillDocsCorpusError) -> JSONResponse:
    envelope = ErrorEnvelope(error=ErrorDetail(code=exc.code, message=exc.message))
    return JSONResponse(
        status_code=_error_status(exc),
        content=envelope.model_dump(),
    )


@router.get("", response_model=None)
def list_skills(
    q: str | None = Query(default=None),
    group: str | None = Query(default=None),
    domain: str | None = Query(default=None),
    corpus_root: Path = Depends(get_skill_docs_corpus_root),
) -> SkillCatalogListResponse | JSONResponse:
    try:
        corpus = build_skill_docs_corpus(corpus_root)
        items, extra = corpus.list_items(q=q, group=group, domain=domain)
    except SkillDocsCorpusError as exc:
        return _error_response(exc)
    return SkillCatalogListResponse(
        items=items,
        facets=extra["facets"],
        meta=extra["meta"],
    )


@router.get("/{skill_id}", response_model=None)
def get_skill_detail(
    skill_id: str,
    corpus_root: Path = Depends(get_skill_docs_corpus_root),
) -> SkillDetailResponse | JSONResponse:
    try:
        corpus = build_skill_docs_corpus(corpus_root)
        detail = corpus.get_detail(skill_id)
    except SkillDocsCorpusError as exc:
        return _error_response(exc)
    return SkillDetailResponse(**detail)
