#!/usr/bin/env bash
#
# opal/tools/doctor/run.sh — OPAL Doctor 진입점
#
# 4개 섹션을 순차 실행하여 OPAL 환경 상태를 진단한다:
#   1/4 Dependencies   — bash, git, node, python3, curl, playwright(옵션)
#   2/4 OPAL Paths     — ~/.opal/AGENT.md, identity.md, skills/, agents/, bin/opal-cli
#   3/4 MCP Registration — claude/cursor/gemini 플랫폼별 MCP 등록 상태
#   4/4 Bootstrappers  — CLAUDE.md/cursor rules/GEMINI.md 마커 확인
#
# Exit code:
#   0 — All Pass (Warn 포함 허용)
#   1 — Fail 1건 이상
#
# 변경이력:
#   v1.0 2026-05-08 KST 초기 구현 — 4섹션 순차 출력 + exit code 0/1 (139)
#

set -euo pipefail

# ─── 경로 ─────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"

# ─── checks.sh 로드 ──────────────────────────────────────────

if [[ ! -f "$LIB_DIR/checks.sh" ]]; then
    echo "  ✗ [ERROR] $LIB_DIR/checks.sh 파일을 찾을 수 없습니다." >&2
    exit 1
fi

# shellcheck source=lib/checks.sh
source "$LIB_DIR/checks.sh"

# ─── 카운터 초기화 ───────────────────────────────────────────

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

# ─── 배너 ─────────────────────────────────────────────────────

echo ""
echo "[OPAL Doctor]"
echo ""

# ─── 4 섹션 순차 실행 ────────────────────────────────────────

check_deps
check_paths
check_mcp
check_bootstrappers

# ─── 요약 ─────────────────────────────────────────────────────

TOTAL_CHECKS=$((PASS_COUNT + WARN_COUNT + FAIL_COUNT))

if [[ "$FAIL_COUNT" -eq 0 && "$WARN_COUNT" -eq 0 ]]; then
    VERDICT="All Pass"
elif [[ "$FAIL_COUNT" -eq 0 ]]; then
    VERDICT="Pass with warnings"
else
    VERDICT="Fail"
fi

echo "판정: ${VERDICT} (${PASS_COUNT} ✓, ${WARN_COUNT} ⚠, ${FAIL_COUNT} ✗ / 총 ${TOTAL_CHECKS}건)"
echo ""

# ─── Exit Code ───────────────────────────────────────────────
# Fail 1건 이상 → exit 1
# Pass/Warn only → exit 0

if [[ "$FAIL_COUNT" -gt 0 ]]; then
    exit 1
fi

exit 0
