#!/usr/bin/env bash
set -euo pipefail
# Usage: start-all.sh [--with-wire] [--with-test] [--no-batch]
#
# BE / FE / Batch Surface를 cmux에 생성·기동하고 각 로그 파일을 tee로 기록한다.
# 기동 후 준비 완료 패턴을 검증하여 한 개라도 실패하면 비-0 종료한다.
#
# 옵션:
#   --with-wire   FE 와이어프레임(fe-wire) Surface도 추가로 기동
#   --with-test   FE 테스트(fe-test) Surface도 추가로 기동
#   --no-batch    Airflow Batch Surface를 건너뜀

HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
source "${HERE}/_config.sh"
source "${HERE}/_lib.sh"

WITH_WIRE=false
WITH_TEST=false
NO_BATCH=false

for arg in "$@"; do
  case "$arg" in
    --with-wire) WITH_WIRE=true ;;
    --with-test) WITH_TEST=true ;;
    --no-batch)  NO_BATCH=true  ;;
    *) echo "[WARN] Unknown flag: $arg" ;;
  esac
done

mkdir -p "${LOG_DIR}"
TS=$(date +%Y%m%d-%H%M)
echo "[INFO] Starting MAMS surfaces (ts=${TS}) ..."

declare -a NAMES=()
declare -a SURFACES=()
declare -a LOGS=()

start_one() {
  local name="$1" cwd="$2" cmd="$3"
  local log="${LOG_DIR}/${name}-${TS}.log"
  local surface
  if ! surface=$(start_surface "${name}" "${cwd}" "${cmd}" "${log}"); then
    echo "[ERROR] ${name} 기동 실패 — 계속 진행"
    return 1
  fi
  NAMES+=("${name}")
  SURFACES+=("${surface}")
  LOGS+=("${log}")
}

start_one be      "${BE_CWD}" "${BE_CMD}"
start_one fe      "${FE_CWD}" "${FE_CMD}"
[ "${WITH_WIRE}" = "true" ] && start_one fe-wire "${FE_WIRE_CWD}" "${FE_WIRE_CMD}"
[ "${WITH_TEST}" = "true" ] && start_one fe-test "${FE_TEST_CWD}" "${FE_TEST_CMD}"

if [ "${NO_BATCH}" = "false" ]; then
  BATCH_RUN="docker compose -f \"${BATCH_COMPOSE}\" up -d && docker compose -f \"${BATCH_COMPOSE}\" logs -f ${BATCH_SERVICE}"
  start_one batch "${BATCH_CWD}" "${BATCH_RUN}"
fi

echo "[INFO] 기동 요청 완료. 준비 완료 검증 시작 ..."
FAIL=0
for i in "${!NAMES[@]}"; do
  name="${NAMES[$i]}"
  surface="${SURFACES[$i]}"
  log="${LOGS[$i]}"
  pattern="$(ready_pattern_for "${name}")"
  if ! verify_surface "${name}" "${surface}" "${log}" "${pattern}" 60; then
    FAIL=$((FAIL + 1))
  fi
done

echo "[INFO] 현재 pane 상태:"
cmux list-panes || echo "[WARN] cmux list-panes 실패"

if [ "${FAIL}" -gt 0 ]; then
  echo "[ERROR] ${FAIL}개 surface 검증 실패"
  exit 1
fi
echo "[OK] 모든 surface 기동 완료"
