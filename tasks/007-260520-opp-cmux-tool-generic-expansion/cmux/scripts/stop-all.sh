#!/usr/bin/env bash
set -euo pipefail
# Usage: stop-all.sh [--keep-batch]
#
# be / fe / fe-wire / fe-test / batch Surface를 순차 종료한다.
# 옵션:
#   --keep-batch  Airflow Batch는 종료하지 않음
#
# cmux CLI 플래그는 버전에 따라 달라질 수 있음
# 'cmux send-key --help' / 'cmux close-surface --help'로 런타임 검증 권장

source "$(dirname "${BASH_SOURCE[0]:-$0}")/_config.sh"

KEEP_BATCH=false

for arg in "$@"; do
  case "$arg" in
    --keep-batch) KEEP_BATCH=true ;;
    *) echo "[WARN] Unknown flag: $arg" ;;
  esac
done

SURFACES="be fe fe-wire fe-test"

echo "[INFO] Stopping MAMS surfaces..."

# ─── Surface별 Ctrl+C 전송 → close ───────────────────────────────────────────
for surface in ${SURFACES}; do
  # cmux list-panes 로 해당 Surface 존재 여부 확인
  if cmux list-panes 2>/dev/null | grep -q "${surface}"; then
    echo "[INFO] Stopping surface: ${surface}"
    cmux send-key --surface "${surface}" 'Ctrl+C' 2>/dev/null \
      || echo "[WARN] send-key failed for ${surface} — skipping"
    sleep 1
    cmux close-surface "${surface}" 2>/dev/null \
      || echo "[WARN] close-surface failed for ${surface} — skipping"
  else
    echo "[INFO] Surface '${surface}' not found — skipping"
  fi
done

# ─── Batch (Airflow) 종료 ─────────────────────────────────────────────────────
if [ "${KEEP_BATCH}" = "false" ]; then
  if cmux list-panes 2>/dev/null | grep -q "batch"; then
    echo "[INFO] Stopping batch surface..."
    cmux send-key --surface batch 'Ctrl+C' 2>/dev/null \
      || echo "[WARN] send-key failed for batch — skipping"
    sleep 1
    cmux close-surface batch 2>/dev/null \
      || echo "[WARN] close-surface failed for batch — skipping"
  fi
  echo "[INFO] Running docker compose down for Airflow..."
  cd "${BATCH_CWD}" && docker compose -f "${BATCH_COMPOSE}" down \
    || echo "[ERROR] docker compose down failed — check Docker status"
fi

echo "[INFO] Stop sequence complete."
cmux list-panes 2>/dev/null || echo "[WARN] cmux list-panes failed"
