"""
@header {
  "module": "main",
  "layer": "router",
  "domain": "console",
  "description": "FastAPI app 진입점. uvicorn host=127.0.0.1:7823(외부 노출 금지, H-7/S-5). CORS dev=localhost:5173 / prod=동일 오리진. /health. 6개 라우터 등록(5개 read-only + brain POST). StaticFiles SPA 서빙(dist 존재 시): 알 수 없는 경로 → index.html fallback. [T060 F-3] lifespan asynccontextmanager 신설 — 기동 시 load_config().prewarm_projects를 순회하며 brain_session_registry.prewarm(project_path)를 호출(비블로킹, daemon 스레드 내부 분리 — lifespan 본문은 즉시 yield). prewarm_projects 미지정 시 생략 로그만 남긴다.",
  "exports": ["app"],
  "depends": ["routers.dashboard", "routers.projects", "routers.tasks", "routers.memory", "routers.doctor", "routers.brain", "config", "adapters.brain_session"],
  "task": "060",
  "changelog": [
    "2026-07-14 T060 Step4: lifespan asynccontextmanager 신설 — 기동 선프라임 훅 연결 (F-3)"
  ]
}
"""
from __future__ import annotations

import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from dashboard.backend.adapters.brain_session import brain_session_registry
from dashboard.backend.config import load_config
from dashboard.backend.routers import brain, dashboard, doctor, memory, projects, tasks

# 앱 로거 INFO를 로그 파일(/tmp/opal-console.log)로 내보낸다.
# uvicorn은 root 로거에 핸들러를 두지 않아, basicConfig 없이는 앱 logger.info가 유실된다.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── lifespan: 기동 선프라임 (T060 F-3) ────────────────────────────────────────

def _prewarm_targets(targets: list[str]) -> None:
    """지정된 프로젝트 목록을 순서대로 prewarm 호출 (daemon 스레드에서 실행)."""
    for project_path in targets:
        brain_session_registry.prewarm(project_path)   # 각 호출 자체도 내부에서 비블로킹


@asynccontextmanager
async def lifespan(app: FastAPI):
    """기동 시 prewarm_projects 지정 프로젝트를 백그라운드 선프라임한다.

    [MUST] 프라임은 블로킹 호출 금지 — prewarm 호출 루프 자체를 daemon 스레드로 분리하여
    (brain_session_registry.prewarm() 내부 구현과 무관하게 이중으로 방어) 이 본문은
    즉시 yield한다(R2/H-6).
    """
    cfg = load_config()
    targets = cfg.prewarm_projects            # F-1 필드
    if targets:
        logger.info("[brain] 기동 선프라임 대상 %d개: %s", len(targets), targets)
        threading.Thread(target=_prewarm_targets, args=(targets,), daemon=True).start()
    else:
        logger.info("[brain] prewarm_projects 미지정 — 선프라임 생략")
    yield
    # shutdown: 인메모리 풀은 프로세스 종료와 함께 소멸(무상태 원칙) — 별도 정리 불요


# ── FastAPI 앱 생성 ──────────────────────────────────────────────────────────

app = FastAPI(
    title="OPAL Console API",
    description="OPAL 로컬 프로젝트 통합 관리 대시보드 — read-only API",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS 설정 ────────────────────────────────────────────────────────────────
# dev 모드: Vite 개발 서버(localhost:5173) 허용
# prod 모드: 동일 오리진(정적 서빙)이므로 CORS 불요 — allow_origins=[""] 로 제한
CORS_ORIGINS = [
    "http://localhost:5173",   # Vite dev server
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],  # brain 라우터 POST 격리 허용 (기존 5라우터는 POST 핸들러 미등록 → 405 유지)
    allow_headers=["*"],
)

# ── 라우터 등록 ───────────────────────────────────────────────────────────────

app.include_router(dashboard.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(memory.router)
app.include_router(doctor.router)
app.include_router(brain.router)  # Phase 1 스파이크 — POST /api/brain/query + GET /api/brain/auth


# ── /health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    """/health — 데몬 상태 확인 엔드포인트."""
    return {"status": "ok", "version": "0.1.0"}


# ── 정적 파일 서빙 + SPA fallback ─────────────────────────────────────────────
# dist 경로: __file__(배포 시 dashboard/backend/main.py) 기준 상위 두 단계 → dist/
# 소스 개발(dashboard/backend/)에서는 dist가 없을 수 있음 → graceful: dist 미존재 시 API만.
# 배포 구조: ~/.opal/dashboard-server/
#   ├── dashboard/backend/main.py  ← __file__
#   └── dist/                      ← 정적 산출물 (SPA)
# → __file__ 기준 ../../dist

_here = Path(__file__).parent          # dashboard/backend/
_dist_dir = (_here / ".." / ".." / "dist").resolve()  # dashboard-server/dist/

if _dist_dir.is_dir():
    logger.info("StaticFiles SPA 서빙 활성화: %s", _dist_dir)

    # /assets, /favicon.ico 등 실제 파일은 StaticFiles가 서빙
    app.mount("/assets", StaticFiles(directory=str(_dist_dir / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(request: Request, full_path: str) -> FileResponse:
        """SPA fallback — 알 수 없는 경로(React Router 경로 등)는 index.html 반환."""
        # /api/* 는 라우터가 먼저 처리하므로 여기까지 도달하지 않음
        index_file = _dist_dir / "index.html"
        if index_file.is_file():
            return FileResponse(str(index_file))
        return FileResponse(str(_dist_dir / "index.html"))
else:
    logger.info("dist/ 미존재 (%s) — API 전용 모드로 기동", _dist_dir)


# ── 엔트리포인트 ──────────────────────────────────────────────────────────────
# [MUST] host=127.0.0.1 — 외부 노출 금지 (H-7, S-5, TASK §제약)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "dashboard.backend.main:app",
        host="127.0.0.1",   # localhost 바인딩 — 0.0.0.0 금지
        port=7823,
        reload=False,
    )
