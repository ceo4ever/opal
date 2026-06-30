#!/usr/bin/env bash
# TS-013: apply.js 4파일 생성 — Codex AGENTS.md 포함
#
# 검증 목표:
#   빈 임시 프로젝트에서 node apply.js --project-root {tmp} 실행 →
#   CLAUDE.md · GEMINI.md · .cursorrules · AGENTS.md 4개 생성 +
#   각 파일에 "# === OPAL START ===" 포함.
#
# 현재 상태 = RED:
#   apply.js PLATFORM_FILES 배열에 AGENTS.md 항목이 없어 3파일만 생성됨.
#   AGENTS.md 부재 → FAIL.
#
# RED-first 규칙 (red-first.md §3):
#   이 테스트는 GREEN 루핑 중 수정 금지 — 구현(apply.js)이 변경되어야 한다.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
APPLY_JS="$FRAMEWORK_ROOT/opal/skills/opal-project-init/scripts/apply.js"

PASS=0
FAIL=0
ERRORS=()

log()  { echo "[TS-013] $*"; }
ok()   { PASS=$((PASS + 1)); echo "  PASS: $*"; }
fail() { FAIL=$((FAIL + 1)); ERRORS+=("$*"); echo "  FAIL: $*"; }

# ── 사전 조건 ─────────────────────────────────────────────

log "사전 조건 확인"
if [[ ! -f "$APPLY_JS" ]]; then
    echo "ERROR: apply.js 없음: $APPLY_JS" >&2
    exit 2
fi

# ── 임시 프로젝트 격리 ─────────────────────────────────────

TMP_PROJECT="$(mktemp -d)"
trap 'rm -rf "$TMP_PROJECT"' EXIT

log "임시 프로젝트 생성: $TMP_PROJECT"
log "apply.js 실행 중..."

# ── apply.js 실행 ─────────────────────────────────────────

node "$APPLY_JS" --project-root "$TMP_PROJECT"
EXIT_CODE=$?

log "exit code: $EXIT_CODE"
if [[ "$EXIT_CODE" -eq 0 ]]; then
    ok "exit 0"
else
    fail "exit code != 0 (got $EXIT_CODE)"
fi

# ── 파일 존재 검사 ─────────────────────────────────────────

OPAL_MARKER="# === OPAL START ==="

for dest in "CLAUDE.md" "GEMINI.md" ".cursorrules" "AGENTS.md"; do
    fpath="$TMP_PROJECT/$dest"
    if [[ -f "$fpath" ]]; then
        ok "파일 존재: $dest"
        # OPAL 마커 포함 확인
        if grep -qF "$OPAL_MARKER" "$fpath"; then
            ok "OPAL 마커 포함: $dest"
        else
            fail "OPAL 마커 없음: $dest"
        fi
    else
        fail "파일 없음: $dest"
    fi
done

# ── 최종 판정 ─────────────────────────────────────────────

log ""
log "=== TS-013 결과: PASS=$PASS FAIL=$FAIL ==="
if [[ "$FAIL" -gt 0 ]]; then
    log "FAIL 항목:"
    for e in "${ERRORS[@]}"; do
        log "  - $e"
    done
    log "STATUS: FAIL (RED 확인됨)"
    exit 1
else
    log "STATUS: PASS"
    exit 0
fi
