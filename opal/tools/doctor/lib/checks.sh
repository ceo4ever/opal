#!/usr/bin/env bash
#
# opal/tools/doctor/lib/checks.sh — OPAL Doctor 체크 함수 모음
#
# check_deps        : 의존성 도구 버전 확인 (bash, git, node, python3, curl, playwright)
# check_paths       : OPAL 핵심 경로 존재 확인 (~/.opal/AGENT.md 등)
# check_mcp         : MCP 등록 상태 확인 (claude/cursor/gemini)
# check_bootstrappers: 부트스트래퍼 마커 확인 (CLAUDE.md/cursor rules/GEMINI.md)
#
# 변경이력:
#   v1.0 2026-05-08 KST 초기 구현 — 4개 체크 함수 신설 (139)
#   v1.1 2026-05-10 10:35 KST: check_deps set -e 안전화 + python Microsoft Store stub 회피.
#                              모든 grep|head 라인에 || true 추가 — 매치 0건 + pipefail 로 인한 abort 결함 fix.
#                              _resolve_python3 신규 — python3 → python → py 폴백 + ^3\.X\.Y 검증으로
#                              Windows 의 python3.exe Microsoft Store stub 으로 인한 doctor abort 결함 fix (140 추가작업, v0.3.9)
#

# ─── 공통 상수 ──────────────────────────────────────────────

OPAL_HOME="${OPAL_HOME:-$HOME/.opal}"

# ─── 카운터 (run.sh에서 초기화) ─────────────────────────────
# PASS_COUNT, WARN_COUNT, FAIL_COUNT 는 run.sh에서 선언하여 공유

# ─── 심볼 ────────────────────────────────────────────────────

SYM_PASS="  ✓"
SYM_WARN="  ⚠"
SYM_FAIL="  ✗"

# ─── 출력 헬퍼 ──────────────────────────────────────────────

_pass() { echo "${SYM_PASS} $1"; ((PASS_COUNT++)) || true; }
_warn() { echo "${SYM_WARN} $1"; ((WARN_COUNT++)) || true; }
_fail() { echo "${SYM_FAIL} $1"; ((FAIL_COUNT++)) || true; }

# ─── check_deps ─────────────────────────────────────────────
# 의존성 도구 확인:
#   ✓ / ✗ 필수 — bash, git, node, python3, curl
#   ⚠       옵션 — playwright (npx @playwright/mcp@latest)
# ─────────────────────────────────────────────────────────────

# Python 인터프리터 해석 — Microsoft Store stub 회피.
# python3 → python → py 순으로 시도하여 --version 출력이 Python 3.X.Y 인 첫 후보를 채택한다.
# 매치 실패 시 1 반환 (set -e 미발동).
# 출력: "<cmd>|<version>" (성공 시), 실패 시 빈 문자열.
_resolve_python3() {
    local cmd raw ver
    for cmd in python3 python py; do
        if command -v "$cmd" &>/dev/null; then
            raw=$("$cmd" --version 2>&1 || true)
            ver=$(echo "$raw" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)
            if [[ "$ver" =~ ^3\.[0-9]+\.[0-9]+$ ]]; then
                echo "${cmd}|${ver}"
                return 0
            fi
        fi
    done
    return 1
}

check_deps() {
    echo "[1/4] Dependencies"

    # bash (필수)
    if command -v bash &>/dev/null; then
        local bver
        bver=$(bash --version 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)
        _pass "bash ${bver:-?}"
    else
        _fail "bash — 미설치 (필수)"
    fi

    # git (필수)
    if command -v git &>/dev/null; then
        local gver
        gver=$(git --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)
        _pass "git ${gver:-?}"
    else
        _fail "git — 미설치 (필수)"
    fi

    # node (필수 v18+)
    if command -v node &>/dev/null; then
        local nver nmaj
        nver=$(node --version 2>/dev/null || true)
        nmaj=$(echo "${nver:-}" | grep -oE '[0-9]+' | head -1 || true)
        if [[ "${nmaj:-0}" -ge 18 ]]; then
            _pass "Node.js ${nver:-?}"
        else
            _fail "Node.js ${nver:-?} — v18+ 필요"
        fi
    else
        _fail "node — 미설치 (필수, v18+)"
    fi

    # python (필수, 3.x) — Windows Microsoft Store stub 자동 회피, python3/python/py 순 폴백
    local py_info py_cmd py_ver
    if py_info=$(_resolve_python3); then
        py_cmd="${py_info%|*}"
        py_ver="${py_info#*|}"
        _pass "${py_cmd} ${py_ver}"
    else
        _fail "python3 — 미설치 또는 Microsoft Store stub (실제 Python 3 필요)"
    fi

    # curl (필수)
    if command -v curl &>/dev/null; then
        local cver
        cver=$(curl --version 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)
        _pass "curl ${cver:-?}"
    else
        _fail "curl — 미설치 (필수)"
    fi

    # playwright (옵션)
    if command -v npx &>/dev/null && npx --yes @playwright/mcp@latest --version &>/dev/null 2>&1; then
        _pass "playwright (npx @playwright/mcp)"
    else
        _warn "playwright — 옵션, 미설치 (npx @playwright/mcp@latest)"
    fi

    echo ""
}

# ─── check_paths ─────────────────────────────────────────────
# OPAL 핵심 경로 확인:
#   ✓ / ✗ 필수 — AGENT.md, identity.md, skills/, agents/
#   ✓ / ⚠ 권고 — bin/opal-cli (symlink)
# ─────────────────────────────────────────────────────────────

check_paths() {
    echo "[2/4] OPAL Paths"

    # ~/.opal/AGENT.md (필수)
    if [[ -f "$OPAL_HOME/AGENT.md" ]]; then
        _pass "${HOME}/.opal/AGENT.md"
    else
        _fail "${HOME}/.opal/AGENT.md — 미존재 (필수)"
    fi

    # ~/.opal/identity.md (필수)
    if [[ -f "$OPAL_HOME/identity.md" ]]; then
        _pass "${HOME}/.opal/identity.md"
    else
        _fail "${HOME}/.opal/identity.md — 미존재 (설치 후 opal-onboarding으로 생성)"
    fi

    # ~/.opal/skills/ (필수)
    if [[ -d "$OPAL_HOME/skills" ]]; then
        local skill_count
        skill_count=$(find "$OPAL_HOME/skills" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
        _pass "${HOME}/.opal/skills/ (${skill_count} skills)"
    else
        _fail "${HOME}/.opal/skills/ — 디렉토리 미존재 (필수)"
    fi

    # ~/.opal/agents/ (필수)
    if [[ -d "$OPAL_HOME/agents" ]]; then
        local agent_count
        agent_count=$(find "$OPAL_HOME/agents" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
        _pass "${HOME}/.opal/agents/ (${agent_count} agents)"
    else
        _fail "${HOME}/.opal/agents/ — 디렉토리 미존재 (필수)"
    fi

    # ~/.opal/bin/opal-cli (권고 — Step 2 PATH 등록 후 생성됨)
    if [[ -L "$OPAL_HOME/bin/opal-cli" ]]; then
        local link_target
        link_target=$(readlink "$OPAL_HOME/bin/opal-cli" 2>/dev/null || echo "?")
        _pass "${HOME}/.opal/bin/opal-cli  →  $link_target"
    elif [[ -f "$OPAL_HOME/bin/opal-cli" ]]; then
        _pass "${HOME}/.opal/bin/opal-cli (파일)"
    else
        _warn "${HOME}/.opal/bin/opal-cli — 미존재 (install_opal_bin 재실행 권장)"
    fi

    echo ""
}

# ─── check_mcp ───────────────────────────────────────────────
# MCP 등록 상태 확인 (claude CLI / cursor mcp.json / gemini settings.json 및 antigravity):
#   OPAL 공식 MCP: context7, playwright, shadcn, sequential-thinking
#   플랫폼별 등록 여부를 확인하고, 누락 시 ⚠ (옵션 항목)
# ─────────────────────────────────────────────────────────────

_read_json_keys() {
    # $1 = json file path, $2 = jq-like python path (mcpServers)
    local file="$1"
    if [[ -f "$file" ]] && command -v python3 &>/dev/null; then
        python3 -c "
import json, sys
try:
    d = json.load(open('$file'))
    keys = list(d.get('mcpServers', {}).keys())
    print(' '.join(keys))
except Exception:
    print('')
" 2>/dev/null || echo ""
    else
        echo ""
    fi
}

_check_mcp_entry() {
    local platform="$1"   # claude / cursor / gemini
    local keys="$2"       # 공백 구분 등록 키 목록
    local mcp_names=("context7" "playwright" "shadcn" "sequential-thinking")

    local registered=()
    local missing=()

    for name in "${mcp_names[@]}"; do
        if echo "$keys" | grep -qw "$name" 2>/dev/null; then
            registered+=("$name")
        else
            missing+=("$name")
        fi
    done

    if [[ ${#missing[@]} -eq 0 ]]; then
        _pass "${platform}: $(IFS=', '; echo "${registered[*]}")"
    elif [[ ${#registered[@]} -gt 0 ]]; then
        _warn "${platform}: $(IFS=', '; echo "${registered[*]}") 등록됨, 미등록: $(IFS=', '; echo "${missing[*]}")"
    else
        _warn "${platform}: MCP 미등록 (또는 설정 파일 없음)"
    fi
}

check_mcp() {
    echo "[3/4] MCP Registration"

    # Claude CLI — `claude mcp list` 파싱
    local claude_keys=""
    if command -v claude &>/dev/null; then
        # claude mcp list 출력에서 서버 이름 추출 (": " 앞 부분)
        claude_keys=$(claude mcp list 2>/dev/null | grep -E '^\S+:' | awk -F: '{print $1}' | tr '\n' ' ' || echo "")
    fi
    _check_mcp_entry "Claude" "$claude_keys"

    # Cursor — ~/.cursor/mcp.json
    local cursor_keys
    cursor_keys=$(_read_json_keys "$HOME/.cursor/mcp.json")
    _check_mcp_entry "Cursor" "$cursor_keys"

    # Gemini — ~/.gemini/settings.json 및 ~/.gemini/antigravity/mcp_config.json 합산
    local gemini_keys=""
    local gs_keys ac_keys
    gs_keys=$(_read_json_keys "$HOME/.gemini/settings.json")
    ac_keys=$(_read_json_keys "$HOME/.gemini/antigravity/mcp_config.json")
    gemini_keys="$gs_keys $ac_keys"
    _check_mcp_entry "Gemini" "$gemini_keys"

    echo ""
}

# ─── check_bootstrappers ────────────────────────────────────
# 부트스트래퍼 마커 확인:
#   ✓ / ✗ 필수 — ~/.claude/CLAUDE.md (OPAL 마커)
#   ✓ / ⚠ 권고 — ~/.cursor/rules/000-opal-agent.mdc
#   ✓ / ⚠ 권고 — ~/.gemini/GEMINI.md (OPAL + HARDENING 마커)
# ─────────────────────────────────────────────────────────────

check_bootstrappers() {
    echo "[4/4] Bootstrappers"

    # ~/.claude/CLAUDE.md — OPAL START 마커 확인 (필수)
    local claude_md="$HOME/.claude/CLAUDE.md"
    if [[ -f "$claude_md" ]]; then
        if grep -qF "=== OPAL START ===" "$claude_md" 2>/dev/null; then
            _pass "${HOME}/.claude/CLAUDE.md (OPAL marker)"
        else
            _fail "${HOME}/.claude/CLAUDE.md — OPAL 마커 없음 (opal-onboarding 또는 install 재실행)"
        fi
    else
        _fail "${HOME}/.claude/CLAUDE.md — 파일 미존재 (Claude Code 미설치 또는 부트스트래퍼 미삽입)"
    fi

    # ~/.cursor/rules/000-opal-agent.mdc (권고)
    local cursor_rule="$HOME/.cursor/rules/000-opal-agent.mdc"
    if [[ -f "$cursor_rule" ]]; then
        _pass "${HOME}/.cursor/rules/000-opal-agent.mdc"
    else
        _warn "${HOME}/.cursor/rules/000-opal-agent.mdc — 미존재 (Cursor 미사용 시 무시 가능)"
    fi

    # ~/.gemini/GEMINI.md — OPAL + HARDENING 마커 확인 (권고)
    local gemini_md="$HOME/.gemini/GEMINI.md"
    if [[ -f "$gemini_md" ]]; then
        local opal_ok hardening_ok
        opal_ok=$(grep -cF "=== OPAL START ===" "$gemini_md" 2>/dev/null || echo "0")
        hardening_ok=$(grep -cF "=== GEMINI HARDENING START ===" "$gemini_md" 2>/dev/null || echo "0")

        if [[ "$opal_ok" -gt 0 && "$hardening_ok" -gt 0 ]]; then
            _pass "${HOME}/.gemini/GEMINI.md (OPAL + HARDENING markers)"
        elif [[ "$opal_ok" -gt 0 ]]; then
            _warn "${HOME}/.gemini/GEMINI.md — OPAL 마커 있음, HARDENING 마커 없음"
        else
            _warn "${HOME}/.gemini/GEMINI.md — OPAL 마커 없음 (Gemini 미사용 시 무시 가능)"
        fi
    else
        _warn "${HOME}/.gemini/GEMINI.md — 미존재 (Gemini 미사용 시 무시 가능)"
    fi

    echo ""
}
