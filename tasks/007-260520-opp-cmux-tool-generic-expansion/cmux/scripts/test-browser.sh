#!/usr/bin/env bash
set -euo pipefail
# Usage: test-browser.sh <URL> [--target <surface>]
#
# 기존 cmux 브라우저 상태를 탐지하여 A/B/C 분기로 브라우저 테스트를 수행한다.
# 탐지 순서: cmux list-panes → browser url 조회 → (필요 시) browser snapshot
#
# 분기:
#   A — 동일 도메인 + 대기 상태  → 기존 탭에서 navigate
#   B — 브라우저 없음              → 새 브라우저 분할(open-split)
#   C — 동일 도메인 + 작업 중     → 별도 test Surface 신규 생성
#   D — 다른 도메인                → 선택지 제시 (CMUX_BROWSER_DECISION=A|B|C 오버라이드)
#
# 환경변수:
#   CMUX_BROWSER_DECISION=A|B|C  — 비대화 환경에서 분기 강제 지정
#
# cmux CLI 플래그는 버전에 따라 달라질 수 있음
# 'cmux browser --help' / 'cmux list-panes --help'로 런타임 검증 권장

source "$(dirname "${BASH_SOURCE[0]:-$0}")/_config.sh"

TARGET_URL="${1:-}"
SURFACE_TARGET=""

if [ -z "${TARGET_URL}" ]; then
  echo "Usage: test-browser.sh <URL> [--target <surface>]"
  exit 2
fi

shift || true
while [ $# -gt 0 ]; do
  case "$1" in
    --target) SURFACE_TARGET="${2:-}"; shift 2 ;;
    *) echo "[WARN] Unknown arg: $1"; shift ;;
  esac
done

# ─── cmux 소켓 존재 여부 확인 ──────────────────────────────────────────────────
if [ ! -S "${CMUX_SOCKET}" ]; then
  echo "[WARN] cmux socket not found at ${CMUX_SOCKET} — cmux가 실행 중인지 확인하세요"
  echo "  힌트: CMUX_SOCKET_PATH 환경변수로 소켓 경로 오버라이드 가능"
  exit 0
fi

# ─── Step 1: 현재 pane 목록 조회 ──────────────────────────────────────────────
echo "[INFO] Checking existing panes..."
PANES=$(cmux list-panes 2>/dev/null || echo "")
# cmux list-panes --help 로 출력 형식 확인 권장

# ─── Step 2: 브라우저 Surface 감지 ────────────────────────────────────────────
BROWSER_SURFACE=""
if echo "${PANES}" | grep -qi "browser\|webview"; then
  BROWSER_SURFACE=$(echo "${PANES}" | grep -i "browser\|webview" | head -1 | awk '{print $1}')
  echo "[INFO] Browser surface detected: ${BROWSER_SURFACE}"
fi

# ─── Step 3: 현재 URL 조회 ────────────────────────────────────────────────────
CURRENT_URL=""
if [ -n "${BROWSER_SURFACE}" ]; then
  CURRENT_URL=$(cmux browser url 2>/dev/null || echo "")
  # cmux browser url --help 로 플래그 검증 권장
  echo "[INFO] Current browser URL: ${CURRENT_URL:-<empty>}"
fi

# ─── Step 4: 분기 결정 ────────────────────────────────────────────────────────
# 도메인 추출 (protocol + host + port)
TARGET_DOMAIN=$(echo "${TARGET_URL}" | sed 's|^\(https\?://[^/]*\).*|\1|')
CURRENT_DOMAIN=$(echo "${CURRENT_URL}" | sed 's|^\(https\?://[^/]*\).*|\1|')

DECISION="${CMUX_BROWSER_DECISION:-}"

if [ -z "${BROWSER_SURFACE}" ]; then
  # 브라우저 없음 → B안: open-split
  DECISION="${DECISION:-B}"
elif [ "${CURRENT_DOMAIN}" = "${TARGET_DOMAIN}" ]; then
  # 동일 도메인 — snapshot으로 작업 중 여부 추가 탐지
  SNAPSHOT=$(cmux browser snapshot 2>/dev/null | head -50 || echo "")
  if echo "${SNAPSHOT}" | grep -qi "input\|modal\|dialog\|form"; then
    # 작업 중으로 추정 → C안
    DECISION="${DECISION:-C}"
  else
    # 대기 상태로 추정 → A안
    DECISION="${DECISION:-A}"
  fi
else
  # 다른 도메인 → 선택지 제시
  if [ -z "${DECISION}" ]; then
    echo ""
    echo "현재 브라우저: ${CURRENT_URL}"
    echo "이동 대상:     ${TARGET_URL}"
    echo ""
    echo "A — 현재 탭에서 이동 (기존 작업 유실 위험)"
    echo "B — 새 탭에서 열기"
    echo "C — 별도 test Surface 신규 생성"
    printf "선택 [A/B/C]: "
    read -r DECISION
  fi
fi

echo "[INFO] Decision: ${DECISION}"

# ─── Step 5: 결정된 동작 실행 ──────────────────────────────────────────────────
case "${DECISION}" in
  A|a)
    echo "[INFO] A안: 기존 탭에서 navigate → ${TARGET_URL}"
    cmux browser navigate "${TARGET_URL}" \
      || echo "[ERROR] cmux browser navigate failed"
    # cmux browser navigate --help 로 플래그 검증 권장
    ;;
  B|b)
    echo "[INFO] B안: 새 브라우저 분할(open-split) → ${TARGET_URL}"
    cmux browser open-split "${TARGET_URL}" \
      || echo "[ERROR] cmux browser open-split failed"
    # cmux browser open-split --help 로 플래그 검증 권장
    ;;
  C|c)
    echo "[INFO] C안: 별도 test Surface 신규 생성 → ${TARGET_URL}"
    cmux new-surface --name "browser-test" \
      --command "cmux browser open-split '${TARGET_URL}'" \
      || echo "[ERROR] cmux new-surface for test browser failed"
    ;;
  *)
    echo "[WARN] 알 수 없는 선택: ${DECISION} — B안 기본값 적용"
    cmux browser open-split "${TARGET_URL}" \
      || echo "[ERROR] cmux browser open-split failed"
    ;;
esac

# ─── Step 6: snapshot 출력 (알투가 읽을 수 있도록) ─────────────────────────────
echo ""
echo "[INFO] Browser snapshot:"
cmux browser snapshot 2>/dev/null || echo "[WARN] snapshot failed — browser may not be ready yet"
