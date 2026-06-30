#!/usr/bin/env bash
# TS-015: apply.js AGENTS.md 멱등 병합 — 사용자 내용 보존
#
# 검증 목표:
#   임시 프로젝트에 기존 AGENTS.md 선배치 (사용자내용 + OPAL 마커 구간) →
#   apply.js 1회 실행 → 마커 구간만 교체 + "사용자내용" 보존 + .bak 생성.
#   2회 실행 → 결과 동일(멱등, diff 0).
#
# 현재 상태 = RED:
#   apply.js PLATFORM_FILES 배열에 AGENTS.md 미포함 → mergeOther 미호출.
#   AGENTS.md 처리 없음 → 사용자 내용 보존 및 .bak 생성 모두 FAIL.
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

log()  { echo "[TS-015] $*"; }
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

AGENTS_FILE="$TMP_PROJECT/AGENTS.md"
OPAL_MARKER="# === OPAL START ==="

# ── AGENTS.md 선배치 ─────────────────────────────────────

cat > "$AGENTS_FILE" << 'PREEXISTING'
사용자내용

# === OPAL START ===
구 부트스트래퍼 내용 (교체 대상)
# === OPAL END ===
PREEXISTING

log "선배치 AGENTS.md 작성 완료"
log "내용:"
cat "$AGENTS_FILE"
log ""

# ── 1회 실행 ─────────────────────────────────────────────

log "apply.js 1회 실행..."
node "$APPLY_JS" --project-root "$TMP_PROJECT"
EXIT1=$?

log "1회 exit code: $EXIT1"
if [[ "$EXIT1" -eq 0 ]]; then
    ok "1회 exit 0"
else
    fail "1회 exit code != 0 (got $EXIT1)"
fi

log "1회 결과 AGENTS.md:"
cat "$AGENTS_FILE" 2>/dev/null || log "(파일 없음)"
log ""

# 파일 존재 확인
if [[ -f "$AGENTS_FILE" ]]; then
    ok "1회 후 AGENTS.md 존재"
else
    fail "1회 후 AGENTS.md 없음"
fi

# 사용자 내용 보존 확인
if grep -qF "사용자내용" "$AGENTS_FILE" 2>/dev/null; then
    ok "1회 후 '사용자내용' 보존"
else
    fail "1회 후 '사용자내용' 소실"
fi

# OPAL 마커 포함 확인
if grep -qF "$OPAL_MARKER" "$AGENTS_FILE" 2>/dev/null; then
    ok "1회 후 OPAL 마커 존재"
else
    fail "1회 후 OPAL 마커 없음"
fi

# 구 내용 교체 확인 (구 부트스트래퍼가 사라져야 함)
if grep -qF "구 부트스트래퍼 내용 (교체 대상)" "$AGENTS_FILE" 2>/dev/null; then
    fail "1회 후 구 내용이 그대로 남아 있음 (교체 안 됨)"
else
    ok "1회 후 구 내용 교체됨"
fi

# .bak 생성 확인
if [[ -f "${AGENTS_FILE}.bak" ]]; then
    ok ".bak 백업 파일 생성됨"
else
    fail ".bak 백업 파일 없음"
fi

# ── 1회 결과 스냅샷 저장 ─────────────────────────────────

SNAPSHOT_AFTER_1="$(cat "$AGENTS_FILE" 2>/dev/null || echo '')"

# ── 2회 실행 (멱등 검증) ──────────────────────────────────

log "apply.js 2회 실행 (멱등 검증)..."
node "$APPLY_JS" --project-root "$TMP_PROJECT"
EXIT2=$?

log "2회 exit code: $EXIT2"
if [[ "$EXIT2" -eq 0 ]]; then
    ok "2회 exit 0"
else
    fail "2회 exit code != 0 (got $EXIT2)"
fi

SNAPSHOT_AFTER_2="$(cat "$AGENTS_FILE" 2>/dev/null || echo '')"

if [[ "$SNAPSHOT_AFTER_1" == "$SNAPSHOT_AFTER_2" ]]; then
    ok "멱등: 2회차 결과가 1회차와 동일 (diff 0)"
else
    fail "멱등 실패: 2회차 결과가 1회차와 다름"
    log "--- 1회차 ---"
    echo "$SNAPSHOT_AFTER_1"
    log "--- 2회차 ---"
    echo "$SNAPSHOT_AFTER_2"
fi

# ── 최종 판정 ─────────────────────────────────────────────

log ""
log "=== TS-015 결과: PASS=$PASS FAIL=$FAIL ==="
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
