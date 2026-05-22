#!/usr/bin/env bash
#
# cmux-tool/examples/e2e-form-fill.sh — click + fill + wait + snapshot 조합 E2E 레시피
#
# 흡수 출처:
#   - tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/docs/CMUX.md §7-A (L301-356) 흡수
#   - tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/scripts/test-browser.sh (부분)
#
# 역할: cmux-tool 디스패처를 통해 "폼 입력 → 제출 → 결과 확인" E2E 자동화를 수행한다.
#       알투/워커가 E2E 자동화 레시피로 참조하거나 직접 실행할 수 있다.
#
# 사용법:
#   e2e-form-fill.sh <url> --email <email> --password <pw> [--surface <handle>]
#   e2e-form-fill.sh https://example.com/login --email user@example.com --password secret
#
# 환경변수:
#   CMUX_TOOL_PATH — cmux-tool run.sh 경로 (기본: ~/.opal/tools/cmux-tool/run.sh)
#
# 주의: 이 스크립트는 예시 레시피다. 실제 사용 시 selector와 URL을 대상 서비스에 맞게 수정한다.

set -uo pipefail

CMUX_TOOL="${CMUX_TOOL_PATH:-$HOME/.opal/tools/cmux-tool/run.sh}"

# ─── 인자 파싱 ───────────────────────────────────────────────────────────────
URL="${1:-}"
EMAIL=""
PASSWORD=""
SURFACE=""

shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --email)    EMAIL="${2:-}"; shift 2 ;;
    --password) PASSWORD="${2:-}"; shift 2 ;;
    --surface)  SURFACE="${2:-}"; shift 2 ;;
    *) echo "[WARN] 알 수 없는 인자: $1" >&2; shift ;;
  esac
done

if [[ -z "$URL" ]]; then
  echo "사용법: e2e-form-fill.sh <url> --email <email> --password <pw> [--surface <handle>]" >&2
  exit 2
fi

# ─── cmux-tool 확인 ───────────────────────────────────────────────────────────
if [[ ! -f "$CMUX_TOOL" ]]; then
  echo "[ERROR] cmux-tool을 찾을 수 없습니다: ${CMUX_TOOL}" >&2
  echo "  설치: scripts/install-mac.sh (OPAL 설치 옵션)" >&2
  exit 1
fi

# ─── surface 인자 처리 ────────────────────────────────────────────────────────
SURFACE_ARG=""
[[ -n "$SURFACE" ]] && SURFACE_ARG="--surface ${SURFACE}"

echo "[INFO] E2E 폼 채우기 시작: ${URL}"

# ─── Step 1: 페이지 오픈 / navigate ──────────────────────────────────────────
if [[ -n "$SURFACE" ]]; then
  echo "[INFO] Step 1: surface ${SURFACE}로 navigate → ${URL}"
  result=$(bash "$CMUX_TOOL" navigate "${URL}" ${SURFACE_ARG})
else
  echo "[INFO] Step 1: 신규 surface 오픈 → ${URL}"
  result=$(bash "$CMUX_TOOL" extract "${URL}" --wait 2000)
  # extract는 전체 HTML을 반환하므로 여기서는 오픈 확인만
  ok=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin).get('ok',''))" 2>/dev/null)
  if [[ "$ok" != "True" ]]; then
    echo "[ERROR] 페이지 오픈 실패: ${result}" >&2
    exit 1
  fi
  # extract로 오픈된 surface를 이후 단계에서 재사용 (B 모드)
  SURFACE=$(echo "$result" | python3 -c "import json,sys; print(json.load(sys.stdin).get('surface',''))" 2>/dev/null)
  SURFACE_ARG="--surface ${SURFACE}"
  echo "[INFO] 오픈된 surface: ${SURFACE}"
fi

# ─── Step 2: 로드 대기 ────────────────────────────────────────────────────────
echo "[INFO] Step 2: 페이지 로드 완료 대기"
bash "$CMUX_TOOL" wait --load-state complete ${SURFACE_ARG} --timeout-ms 10000 >/dev/null

# ─── Step 3: 이메일 필드 입력 ─────────────────────────────────────────────────
if [[ -n "$EMAIL" ]]; then
  echo "[INFO] Step 3: 이메일 입력 (#email 또는 [type=email])"
  bash "$CMUX_TOOL" fill "#email" --text "${EMAIL}" ${SURFACE_ARG} >/dev/null \
    || bash "$CMUX_TOOL" fill "[type=email]" --text "${EMAIL}" ${SURFACE_ARG} >/dev/null \
    || echo "[WARN] 이메일 필드를 찾지 못했습니다 — selector를 수정하세요" >&2
fi

# ─── Step 4: 비밀번호 필드 입력 ───────────────────────────────────────────────
if [[ -n "$PASSWORD" ]]; then
  echo "[INFO] Step 4: 비밀번호 입력 (#password 또는 [type=password])"
  bash "$CMUX_TOOL" fill "#password" --text "${PASSWORD}" ${SURFACE_ARG} >/dev/null \
    || bash "$CMUX_TOOL" fill "[type=password]" --text "${PASSWORD}" ${SURFACE_ARG} >/dev/null \
    || echo "[WARN] 비밀번호 필드를 찾지 못했습니다 — selector를 수정하세요" >&2
fi

# ─── Step 5: 제출 버튼 클릭 ───────────────────────────────────────────────────
echo "[INFO] Step 5: 제출 버튼 클릭 ([type=submit] 또는 #submit)"
bash "$CMUX_TOOL" click "[type=submit]" ${SURFACE_ARG} >/dev/null \
  || bash "$CMUX_TOOL" click "#submit" ${SURFACE_ARG} >/dev/null \
  || bash "$CMUX_TOOL" press "Enter" ${SURFACE_ARG} >/dev/null \
  || echo "[WARN] 제출 버튼을 찾지 못했습니다" >&2

# ─── Step 6: 제출 후 로드 대기 ────────────────────────────────────────────────
echo "[INFO] Step 6: 제출 후 로드 완료 대기"
bash "$CMUX_TOOL" wait --load-state complete ${SURFACE_ARG} --timeout-ms 10000 >/dev/null

# ─── Step 7: 결과 스냅샷 출력 ─────────────────────────────────────────────────
echo "[INFO] Step 7: 결과 스냅샷"
snapshot_result=$(bash "$CMUX_TOOL" snapshot ${SURFACE_ARG} --compact)
echo "$snapshot_result" | python3 -c "
import json, sys
d = json.load(sys.stdin)
if d.get('ok'):
    text = d.get('snapshot_text','')
    print('[SNAPSHOT]', text[:500], '...' if len(text) > 500 else '')
else:
    print('[ERROR] 스냅샷 실패:', d.get('error',''))
" 2>/dev/null || echo "[WARN] 스냅샷 파싱 실패"

echo "[INFO] E2E 폼 채우기 완료"
