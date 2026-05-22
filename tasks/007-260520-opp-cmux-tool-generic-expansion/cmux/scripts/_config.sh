#!/usr/bin/env bash
set -euo pipefail
# Usage: source "$(dirname "${BASH_SOURCE[0]}")/_config.sh"
#
# 프로젝트 승격 시 이 파일만 교체하세요 — 다른 스크립트는 변수 이름만 사용합니다
# When upgrading to OPAL framework (~/.opal/cmux/), only replace this file.
#
# 설치된 cmux 버전에 따라 CMUX_SOCKET_PATH 환경변수를 설정하세요:
#   stable:  /tmp/cmux.sock  (기본값)
#   nightly: /tmp/cmux-nightly.sock
# cmux --version 으로 버전 확인 권장

# ─── 프로젝트 루트 (스크립트 위치 기반 자동 해석) ─────────────────────────────
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../../.." && pwd)"

# ─── 백엔드 (FastAPI + uvicorn) ───────────────────────────────────────────────
BE_CWD="${PROJECT_ROOT}/workspace/backend"
BE_PORT=8000
BE_CMD="uv run uvicorn app.mams.main:mams_app --reload --port ${BE_PORT}"

# ─── 프론트엔드 (본, Next.js) ──────────────────────────────────────────────────
FE_CWD="${PROJECT_ROOT}/workspace/frontend"
FE_PORT=3000
FE_CMD="pnpm dev"

# ─── 프론트엔드 와이어프레임 ────────────────────────────────────────────────────
FE_WIRE_CWD="${PROJECT_ROOT}/workspace/frontend_wireframe"
FE_WIRE_PORT=3001
FE_WIRE_CMD="pnpm dev --port ${FE_WIRE_PORT}"

# ─── 프론트엔드 테스트 ──────────────────────────────────────────────────────────
FE_TEST_CWD="${PROJECT_ROOT}/workspace/frontend_test"
FE_TEST_PORT=3002
FE_TEST_CMD="pnpm dev --port ${FE_TEST_PORT}"

# ─── 배치 (Airflow Docker Compose) ────────────────────────────────────────────
BATCH_CWD="${PROJECT_ROOT}/workspace/backend"
BATCH_COMPOSE="docker-compose.airflow.yml"
BATCH_PORT=8080
BATCH_SERVICE="airflow-apiserver"

# ─── 로그 디렉토리 ────────────────────────────────────────────────────────────
LOG_DIR="${PROJECT_ROOT}/.opal/cmux/logs"

# ─── cmux 소켓 경로 (환경변수 오버라이드 지원) ──────────────────────────────────
CMUX_SOCKET="${CMUX_SOCKET_PATH:-/tmp/cmux.sock}"
