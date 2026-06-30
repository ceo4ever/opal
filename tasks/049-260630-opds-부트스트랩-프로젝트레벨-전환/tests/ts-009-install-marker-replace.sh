#!/usr/bin/env bash
# TS-009: install 마커 교체 계약 — 회귀 가드
#
# 검증 목표:
#   scripts/install-mac.sh의 install_opal_section 함수를
#   임시 HOME에서 호출.
#
#   선배치: "사용자머리\n# === OPAL START ===\n구마커\n# === OPAL END ===\n사용자꼬리"
#   bootstrapper 스니펫으로 1회 호출 →
#     START~END 구간이 신 콘텐츠로 치환
#     + 마커 밖 "사용자머리"/"사용자꼬리" 보존
#   2회 호출 → 결과 동일(멱등, diff 0)
#   exit 0
#
# 현재 상태 = 회귀 가드:
#   install_opal_section은 이미 이 동작을 지원한다고 예상.
#   GREEN이면 GREEN으로 정직히 기록한다 (red-first.md §3 회귀 가드).
#
# 실배포 경계:
#   임시 HOME에서만 실행. ~/.opal, ~/.claude 등 실배포 경로 변경 금지.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
INSTALL_SH="$FRAMEWORK_ROOT/scripts/install-mac.sh"

PASS=0
FAIL=0
ERRORS=()

log()  { echo "[TS-009] $*"; }
ok()   { PASS=$((PASS + 1)); echo "  PASS: $*"; }
fail() { FAIL=$((FAIL + 1)); ERRORS+=("$*"); echo "  FAIL: $*"; }

# ── 사전 조건 ─────────────────────────────────────────────

log "사전 조건 확인"
if [[ ! -f "$INSTALL_SH" ]]; then
    echo "ERROR: install-mac.sh 없음: $INSTALL_SH" >&2
    exit 2
fi

# bash -n 구문 검사
if bash -n "$INSTALL_SH" 2>&1; then
    ok "bash -n 구문 무결 (exit 0)"
else
    fail "bash -n 구문 오류"
fi

# ── 임시 환경 격리 ─────────────────────────────────────────

TMP_HOME="$(mktemp -d)"
TMP_SNIPPET_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_HOME" "$TMP_SNIPPET_DIR"' EXIT

TARGET_FILE="$TMP_HOME/CLAUDE.md"
SNIPPET_FILE="$TMP_SNIPPET_DIR/bootstrap-snippet.md"
OPAL_MARKER="# === OPAL START ==="

# ── 테스트 스니펫 생성 (extract_bootstrap_content가 파싱하는 형식) ──

cat > "$SNIPPET_FILE" << 'SNIPPET_EOF'
# 테스트 스니펫

```markdown
신 부트스트래퍼 내용 (치환 결과)
```
SNIPPET_EOF

log "스니펫 파일: $SNIPPET_FILE"

# ── 대상 파일 선배치 ─────────────────────────────────────

cat > "$TARGET_FILE" << 'PREEXISTING'
사용자머리

# === OPAL START ===
구마커 (교체 대상)
# === OPAL END ===

사용자꼬리
PREEXISTING

log "선배치 대상 파일: $TARGET_FILE"
log "내용:"
cat "$TARGET_FILE"
log ""

# ── install_opal_section 함수 추출 + 호출 ──────────────────
# install-mac.sh의 필요 함수만 sourcing 한다.
# set -euo pipefail 및 전역 변수가 있으므로
# 서브셸에서 함수만 source하는 방식으로 격리 실행.

run_install_opal_section() {
    local snippet="$1"
    local target="$2"

    # install-mac.sh에서 필요한 함수와 변수만 추출·정의하여 실행
    # 전체 스크립트 source 시 detect_framework_root가 exit 1을 낼 수 있으므로
    # 함수 정의만 grep으로 추출하여 eval한다.
    bash << BASH_EOF
set -euo pipefail

# 마커 상수 (install-mac.sh와 동일)
OPAL_START="# === OPAL START ==="
OPAL_END="# === OPAL END ==="
R2_START="# === R2 START ==="
R2_END="# === R2 END ==="
OPAL_VERBOSE="0"

# 로깅 함수 (install-mac.sh와 동일)
info()    { true; }
success() { echo "  [success] \$1"; }
error()   { echo "[ERROR] \$1" >&2; }

# extract_bootstrap_content 함수 (install-mac.sh 원문 그대로)
extract_bootstrap_content() {
    local file="\$1"
    if grep -q '^'\'''\'''\'''\''markdown\$' "\$file"; then
        sed -n '/^'\'''\'''\'''\''markdown\$/,/^'\'''\'''\'''\''$/p' "\$file" | sed '1d;\$d'
    else
        sed -n '/^\`\`\`markdown\$/,/^\`\`\`\$/p' "\$file" | sed '1d;\$d'
    fi
}

# install_opal_section 함수 (install-mac.sh 원문 그대로)
install_opal_section() {
    local snippet="\$1"
    local target="\$2"
    local label="\$3"

    local content
    content="\$(extract_bootstrap_content "\$snippet")"

    if [[ -z "\$content" ]]; then
        error "OPAL 부트스트래퍼 내용을 추출할 수 없습니다: \$snippet"
        return 1
    fi

    mkdir -p "\$(dirname "\$target")"

    if [[ ! -f "\$target" ]]; then
        {
            echo "\$OPAL_START"
            echo "\$content"
            echo "\$OPAL_END"
        } > "\$target"
        success "\$label OPAL 설치 (새 파일): \$target"

    elif grep -qF "\$OPAL_START" "\$target"; then
        local tmp
        tmp="\$(mktemp)"
        local in_section=0

        while IFS= read -r line || [[ -n "\$line" ]]; do
            if [[ "\$line" == "\$OPAL_START" ]]; then
                in_section=1
                echo "\$OPAL_START"
                echo "\$content"
                echo "\$OPAL_END"
            elif [[ "\$line" == "\$OPAL_END" ]]; then
                in_section=0
            elif [[ \$in_section -eq 0 ]]; then
                echo "\$line"
            fi
        done < "\$target" > "\$tmp"

        mv "\$tmp" "\$target"
        success "\$label OPAL 업데이트 (마커 교체): \$target"

    elif grep -qF "\$R2_START" "\$target"; then
        local tmp
        tmp="\$(mktemp)"
        local in_section=0

        while IFS= read -r line || [[ -n "\$line" ]]; do
            if [[ "\$line" == "\$R2_START" ]]; then
                in_section=1
                echo "\$OPAL_START"
                echo "\$content"
                echo "\$OPAL_END"
            elif [[ "\$line" == "\$R2_END" ]]; then
                in_section=0
            elif [[ \$in_section -eq 0 ]]; then
                echo "\$line"
            fi
        done < "\$target" > "\$tmp"

        mv "\$tmp" "\$target"
        success "\$label R2→OPAL 전환 (마커 교체): \$target"

    else
        {
            echo ""
            echo "\$OPAL_START"
            echo "\$content"
            echo "\$OPAL_END"
        } >> "\$target"
        success "\$label OPAL 추가 (기존 내용 보존): \$target"
    fi
}

install_opal_section "$snippet" "$target" "테스트"
BASH_EOF
}

# ── 1회 호출 ─────────────────────────────────────────────

log "install_opal_section 1회 호출..."
run_install_opal_section "$SNIPPET_FILE" "$TARGET_FILE"
EXIT1=$?

log "1회 exit code: $EXIT1"
if [[ "$EXIT1" -eq 0 ]]; then
    ok "1회 exit 0"
else
    fail "1회 exit code != 0 (got $EXIT1)"
fi

log "1회 결과 CLAUDE.md:"
cat "$TARGET_FILE"
log ""

# 마커 START~END 구간이 신 콘텐츠로 치환됐는지 확인
if grep -qF "신 부트스트래퍼 내용 (치환 결과)" "$TARGET_FILE"; then
    ok "1회 후 신 콘텐츠로 치환됨"
else
    fail "1회 후 신 콘텐츠 없음 (치환 실패)"
fi

# 구 내용이 사라졌는지 확인
if grep -qF "구마커 (교체 대상)" "$TARGET_FILE"; then
    fail "1회 후 구 마커 내용이 그대로 남아 있음"
else
    ok "1회 후 구 마커 내용 제거됨"
fi

# 마커 밖 "사용자머리" 보존 확인
if grep -qF "사용자머리" "$TARGET_FILE"; then
    ok "1회 후 '사용자머리' 보존"
else
    fail "1회 후 '사용자머리' 소실"
fi

# 마커 밖 "사용자꼬리" 보존 확인
if grep -qF "사용자꼬리" "$TARGET_FILE"; then
    ok "1회 후 '사용자꼬리' 보존"
else
    fail "1회 후 '사용자꼬리' 소실"
fi

# OPAL 마커 포함 확인
if grep -qF "$OPAL_MARKER" "$TARGET_FILE"; then
    ok "1회 후 OPAL 마커 존재"
else
    fail "1회 후 OPAL 마커 없음"
fi

# ── 1회 결과 스냅샷 저장 ─────────────────────────────────

SNAPSHOT_AFTER_1="$(cat "$TARGET_FILE")"

# ── 2회 호출 (멱등 검증) ─────────────────────────────────

log "install_opal_section 2회 호출 (멱등 검증)..."
run_install_opal_section "$SNIPPET_FILE" "$TARGET_FILE"
EXIT2=$?

log "2회 exit code: $EXIT2"
if [[ "$EXIT2" -eq 0 ]]; then
    ok "2회 exit 0"
else
    fail "2회 exit code != 0 (got $EXIT2)"
fi

SNAPSHOT_AFTER_2="$(cat "$TARGET_FILE")"

if [[ "$SNAPSHOT_AFTER_1" == "$SNAPSHOT_AFTER_2" ]]; then
    ok "멱등: 2회차 결과가 1회차와 동일 (diff 0)"
else
    fail "멱등 실패: 2회차 결과가 1회차와 다름"
    log "--- diff ---"
    diff <(echo "$SNAPSHOT_AFTER_1") <(echo "$SNAPSHOT_AFTER_2") || true
fi

# ── 최종 판정 ─────────────────────────────────────────────

log ""
log "=== TS-009 결과: PASS=$PASS FAIL=$FAIL ==="
if [[ "$FAIL" -gt 0 ]]; then
    log "FAIL 항목:"
    for e in "${ERRORS[@]}"; do
        log "  - $e"
    done
    log "STATUS: FAIL"
    exit 1
else
    log "STATUS: PASS (회귀 가드 통과)"
    exit 0
fi
