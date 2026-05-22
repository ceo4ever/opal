#!/usr/bin/env bash
#
# cmux-tool/examples/e2e-branch-auto.sh — A/B/C 분기 자동 결정 E2E 레시피
#
# 흡수 출처: tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/scripts/test-browser.sh:1-133
#            (원형 보존판 — cmux-tool/lib/branch.sh 함수를 source해서 호출하는 형태로 일반화)
#
# 역할: 현재 cmux 브라우저 상태를 탐지하여 A/B/C 분기로 브라우저 자동화를 수행한다.
#       탐지 순서: cmux list-panes → browser url 조회 → (필요 시) browser snapshot
#
# 분기:
#   A — 동일 도메인 + 대기 상태  → 기존 탭에서 navigate
#   B — 브라우저 없음              → 새 브라우저 분할(open-split)
#   C — 동일 도메인 + 작업 중     → 별도 Surface 신규 생성 후 open-split
#   D — 다른 도메인                → CMUX_BROWSER_DECISION 오버라이드 필요
#
# 사용법:
#   e2e-branch-auto.sh <URL> [--target <surface>]
#
# 환경변수:
#   CMUX_BROWSER_DECISION=A|B|C  — 비대화 환경에서 분기 강제 지정
#   CMUX_TOOL_PATH — cmux-tool run.sh 경로 (기본: ~/.opal/tools/cmux-tool/run.sh)
#
# cmux CLI 플래그는 버전에 따라 달라질 수 있음 — 'cmux browser --help'로 런타임 검증 권장

set -uo pipefail

LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../lib" && pwd)"
CMUX_TOOL="${CMUX_TOOL_PATH:-$HOME/.opal/tools/cmux-tool/run.sh}"

# lib/branch.sh에서 decide_branch 함수 로드
# shellcheck source=../lib/branch.sh
source "${LIB_DIR}/branch.sh"

# ─── 인자 파싱 ───────────────────────────────────────────────────────────────
TARGET_URL="${1:-}"
SURFACE_TARGET=""

if [[ -z "${TARGET_URL}" ]]; then
  echo "사용법: e2e-branch-auto.sh <URL> [--target <surface>]" >&2
  exit 2
fi

shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) SURFACE_TARGET="${2:-}"; shift 2 ;;
    *) echo "[WARN] 알 수 없는 인자: $1" >&2; shift ;;
  esac
done

# ─── cmux 소켓 존재 여부 확인 ────────────────────────────────────────────────
CMUX_SOCKET="${CMUX_SOCKET_PATH:-/tmp/cmux.sock}"
if [[ ! -S "${CMUX_SOCKET}" ]]; then
  echo "[WARN] cmux socket not found at ${CMUX_SOCKET} — cmux가 실행 중인지 확인하세요" >&2
  echo "  힌트: CMUX_SOCKET_PATH 환경변수로 소켓 경로 오버라이드 가능" >&2
  exit 0
fi

# ─── cmux 설치 확인 ───────────────────────────────────────────────────────────
if ! command -v cmux >/dev/null 2>&1; then
  echo "[ERROR] cmux 명령을 찾을 수 없습니다. https://cmux.com/ 에서 설치하세요" >&2
  exit 1
fi

echo "[INFO] 브라우저 분기 결정 중: ${TARGET_URL}"

# ─── 분기 결정 (lib/branch.sh 함수 사용) ────────────────────────────────────
DECISION=$(decide_branch "${TARGET_URL}" "${CMUX_BROWSER_DECISION:-}")
echo "[INFO] Decision: ${DECISION}"

# ─── 분기별 동작 실행 ────────────────────────────────────────────────────────
case "${DECISION}" in
  A|a)
    echo "[INFO] A안: 기존 탭에서 navigate → ${TARGET_URL}"
    SURFACE_ARG=""
    [[ -n "${SURFACE_TARGET}" ]] && SURFACE_ARG="--surface ${SURFACE_TARGET}"
    bash "$CMUX_TOOL" navigate "${TARGET_URL}" ${SURFACE_ARG} \
      || echo "[ERROR] navigate 실패" >&2
    ;;
  B|b)
    echo "[INFO] B안: 새 브라우저 분할(open-split) → ${TARGET_URL}"
    bash "$CMUX_TOOL" open-split "${TARGET_URL}" \
      || echo "[ERROR] open-split 실패" >&2
    ;;
  C|c)
    echo "[INFO] C안: 별도 Surface 신규 생성 → ${TARGET_URL}"
    # 새 Surface를 열고 open-split으로 브라우저 분할
    if cmux new-surface --type terminal >/dev/null 2>&1; then
      bash "$CMUX_TOOL" open-split "${TARGET_URL}" \
        || echo "[ERROR] open-split 실패" >&2
    else
      echo "[ERROR] new-surface 실패" >&2
    fi
    ;;
  D|d)
    echo "[WARN] D: 다른 도메인 감지 — CMUX_BROWSER_DECISION=A|B|C 환경변수로 오버라이드 후 재실행" >&2
    echo "  현재 브라우저와 다른 도메인 접근. 어떤 분기를 원하시나요?" >&2
    echo "  A — 현재 탭에서 이동  B — 새 탭  C — 별도 Surface" >&2
    exit 1
    ;;
  *)
    echo "[WARN] 알 수 없는 결정: ${DECISION} — B안 기본값 적용" >&2
    bash "$CMUX_TOOL" open-split "${TARGET_URL}" \
      || echo "[ERROR] open-split 실패" >&2
    ;;
esac

# ─── 결과 스냅샷 출력 ────────────────────────────────────────────────────────
echo ""
echo "[INFO] 분기 완료. 브라우저 스냅샷 확인:"
bash "$CMUX_TOOL" snapshot --compact 2>/dev/null \
  | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    if d.get('ok'):
        t = d.get('snapshot_text','')
        print(t[:800], '...' if len(t) > 800 else '')
    else:
        print('[WARN] snapshot 실패:', d.get('error',''))
except: print('[WARN] snapshot 파싱 실패')
" 2>/dev/null || echo "[WARN] snapshot 실패 — 브라우저가 아직 준비되지 않았을 수 있습니다"
