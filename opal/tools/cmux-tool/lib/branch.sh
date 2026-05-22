#!/usr/bin/env bash
#
# cmux-tool/lib/branch.sh — cmux 브라우저 A/B/C/D 분기 결정 헬퍼
#
# 흡수 출처: tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/scripts/test-browser.sh:65-100
# 역할: 현재 cmux 브라우저 상태를 탐지하여 A/B/C/D 분기를 결정한다.
#       MAMS 특화 변수(_config.sh 의존)를 제거하고 범용 함수 인터페이스로 일반화했다.
#
# 공개 함수:
#   decide_branch <target_url> [cmux_browser_decision]  → A|B|C|D 출력 (stdout)
#
# 분기 의미:
#   A — 동일 도메인 + 대기 상태  → 기존 탭에서 navigate
#   B — 브라우저 없음              → 새 브라우저 분할(open-split)
#   C — 동일 도메인 + 작업 중     → 별도 Surface 신규 생성
#   D — 다른 도메인                → 결정 불가, 오버라이드 필요
#
# 환경변수:
#   CMUX_BROWSER_DECISION=A|B|C   — 비대화 환경에서 분기 강제 지정 (오버라이드)
#
# cmux CLI 플래그는 버전에 따라 달라질 수 있음 — 'cmux browser --help'로 런타임 검증 권장

# ─── decide_branch <target_url> [forced_decision] ─────────────────────────
# stdout으로 A|B|C|D 중 하나를 출력.
# D가 반환되면 호출자가 CMUX_BROWSER_DECISION 또는 대화형 입력으로 처리해야 한다.
decide_branch() {
  local target_url="${1:-}"
  local forced="${2:-${CMUX_BROWSER_DECISION:-}}"

  if [ -z "${target_url}" ]; then
    echo "[ERROR] decide_branch: target_url 필요" >&2
    return 2
  fi

  # ─── Step 1: 강제 오버라이드 확인 ─────────────────────────────────────────
  if [ -n "${forced}" ]; then
    printf '%s' "${forced}"
    return 0
  fi

  # ─── Step 2: 현재 pane 목록 조회 ──────────────────────────────────────────
  local panes=""
  panes=$(cmux list-panes 2>/dev/null || echo "")

  # ─── Step 3: 브라우저 Surface 감지 ────────────────────────────────────────
  local browser_surface=""
  if echo "${panes}" | grep -qi "browser\|webview"; then
    browser_surface=$(echo "${panes}" | grep -i "browser\|webview" | head -1 | awk '{print $1}')
  fi

  # ─── Step 4: 브라우저 없음 → B안 ─────────────────────────────────────────
  if [ -z "${browser_surface}" ]; then
    printf '%s' "B"
    return 0
  fi

  # ─── Step 5: 현재 URL 조회 ────────────────────────────────────────────────
  local current_url=""
  current_url=$(cmux browser url 2>/dev/null || echo "")

  # ─── Step 6: 도메인 비교 ──────────────────────────────────────────────────
  local target_domain current_domain
  target_domain=$(echo "${target_url}"  | sed 's|^\(https\?://[^/]*\).*|\1|')
  current_domain=$(echo "${current_url}" | sed 's|^\(https\?://[^/]*\).*|\1|')

  if [ "${current_domain}" = "${target_domain}" ]; then
    # 동일 도메인 — snapshot으로 작업 중 여부 탐지
    local snapshot=""
    snapshot=$(cmux browser snapshot 2>/dev/null | head -50 || echo "")

    if echo "${snapshot}" | grep -qi "input\|modal\|dialog\|form"; then
      # 작업 중으로 추정 → C안
      printf '%s' "C"
    else
      # 대기 상태로 추정 → A안
      printf '%s' "A"
    fi
  else
    # 다른 도메인 → D (호출자가 처리)
    printf '%s' "D"
  fi
}
