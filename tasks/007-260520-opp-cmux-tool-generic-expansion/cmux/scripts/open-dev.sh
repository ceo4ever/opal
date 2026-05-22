#!/usr/bin/env bash
set -euo pipefail
# Usage: open-dev.sh <be|fe|fe-wire|fe-test|batch>
#
# 단일 Surface를 cmux에 생성·기동하고 준비 완료 검증 후 종료한다.
# 인자:
#   be       — FastAPI 백엔드 서버
#   fe       — Next.js 프론트엔드 (본)
#   fe-wire  — Next.js 프론트엔드 (와이어프레임 참조용)
#   fe-test  — Next.js 프론트엔드 (API 테스트용)
#   batch    — Airflow Docker Compose (배치)

HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
source "${HERE}/_config.sh"
source "${HERE}/_lib.sh"

TARGET="${1:-}"
if [ -z "${TARGET}" ]; then
  echo "Usage: open-dev.sh <be|fe|fe-wire|fe-test|batch>"
  exit 2
fi

mkdir -p "${LOG_DIR}"
TS=$(date +%Y%m%d-%H%M)
LOG="${LOG_DIR}/${TARGET}-${TS}.log"

case "${TARGET}" in
  be)      CWD="${BE_CWD}";      CMD="${BE_CMD}" ;;
  fe)      CWD="${FE_CWD}";      CMD="${FE_CMD}" ;;
  fe-wire) CWD="${FE_WIRE_CWD}"; CMD="${FE_WIRE_CMD}" ;;
  fe-test) CWD="${FE_TEST_CWD}"; CMD="${FE_TEST_CMD}" ;;
  batch)
    CWD="${BATCH_CWD}"
    CMD="docker compose -f \"${BATCH_COMPOSE}\" up -d && docker compose -f \"${BATCH_COMPOSE}\" logs -f ${BATCH_SERVICE}"
    ;;
  *)
    echo "Usage: open-dev.sh <be|fe|fe-wire|fe-test|batch>"
    echo "Unknown target: ${TARGET}"
    exit 2
    ;;
esac

echo "[INFO] ${TARGET} surface 기동 중 ..."
if ! SURFACE=$(start_surface "${TARGET}" "${CWD}" "${CMD}" "${LOG}"); then
  echo "[ERROR] ${TARGET} 기동 실패"
  exit 1
fi

PATTERN="$(ready_pattern_for "${TARGET}")"
if ! verify_surface "${TARGET}" "${SURFACE}" "${LOG}" "${PATTERN}" 60; then
  echo "[ERROR] ${TARGET} 준비 완료 검증 실패"
  exit 1
fi

echo "[OK] ${TARGET} 기동 완료 → ${SURFACE} (log: ${LOG})"
