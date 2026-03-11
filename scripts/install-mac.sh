#!/bin/bash
#
# install-mac.sh — AI Development Framework Installer (macOS)
#
# Usage: ./scripts/install-mac.sh
#

set -euo pipefail

# ─── Colors ───────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ─── OPAL Markers (R2 하위 호환 포함) ─────────────────────

OPAL_START="# === OPAL START ==="
OPAL_END="# === OPAL END ==="
R2_START="# === R2 START ==="
R2_END="# === R2 END ==="

# ─── Logging ─────────────────────────────────────────────

info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}  ✓${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# ─── Core Functions ──────────────────────────────────────

print_banner() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  ${BOLD}AI Development Framework Installer${NC}  (macOS)        ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  Claude Code · Cursor · Antigravity · OPAL          ${CYAN}║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
}

detect_framework_root() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    FRAMEWORK_ROOT="$(dirname "$script_dir")"

    if [[ ! -d "$FRAMEWORK_ROOT/claude" ]] || [[ ! -d "$FRAMEWORK_ROOT/antigravity" ]]; then
        error "프레임워크 루트를 찾을 수 없습니다: $FRAMEWORK_ROOT"
        error "이 스크립트는 ai-framework/scripts/ 에서 실행해야 합니다."
        exit 1
    fi

    info "프레임워크 루트: ${BOLD}$FRAMEWORK_ROOT${NC}"
}

detect_user() {
    local current_user
    current_user="$(whoami)"
    USER_HOME="$HOME"

    echo ""
    info "현재 사용자: ${BOLD}$current_user${NC}"
    info "홈 디렉토리: ${BOLD}$USER_HOME${NC}"
    echo ""

    local confirm
    read -rp "이 계정에 설치하시겠습니까? (Y/n): " confirm
    confirm="$(echo "$confirm" | tr '[:upper:]' '[:lower:]')"

    if [[ "$confirm" == "n" ]]; then
        read -rp "설치할 사용자의 홈 디렉토리: " USER_HOME
        if [[ ! -d "$USER_HOME" ]]; then
            error "디렉토리가 존재하지 않습니다: $USER_HOME"
            exit 1
        fi
    fi
}

show_menu() {
    echo ""
    echo -e "${BOLD}설치 대상을 선택하세요:${NC}"
    echo ""
    echo "  [1] Claude Code    (skills + agents → ~/.claude/)"
    echo "  [2] Cursor         (skills + agents → ~/.cursor/)"
    echo "  [3] Antigravity    (skills → ~/.gemini/antigravity/)"
    echo "  [4] OPAL           (AI 에이전트 → ~/.opal/)"
    echo "  [5] 전체 설치"
    echo "  [0] 종료"
    echo ""
    read -rp "선택 (0-5): " MENU_CHOICE
}

# ─── Install Helpers ─────────────────────────────────────

install_dir() {
    local src="$1"
    local dst="$2"
    local label="$3"

    mkdir -p "$(dirname "$dst")"

    if [[ ! -d "$dst" ]]; then
        cp -r "$src" "$dst"
        success "$label → $dst (신규)"
    else
        cp -Rf "$src"/. "$dst"/
        success "$label → $dst (덮어쓰기)"
    fi
}

extract_bootstrap_content() {
    local file="$1"
    sed -n '/^```markdown$/,/^```$/p' "$file" | sed '1d;$d'
}

# Marker-based OPAL section management (R2 하위 호환)
# - Recognizes both OPAL and legacy R2 markers
# - Always writes with OPAL markers
install_opal_section() {
    local snippet="$1"
    local target="$2"
    local label="$3"

    local content
    content="$(extract_bootstrap_content "$snippet")"

    if [[ -z "$content" ]]; then
        error "OPAL 부트스트래퍼 내용을 추출할 수 없습니다: $snippet"
        return 1
    fi

    mkdir -p "$(dirname "$target")"

    if [[ ! -f "$target" ]]; then
        {
            echo "$OPAL_START"
            echo "$content"
            echo "$OPAL_END"
        } > "$target"
        success "$label OPAL 설치 (새 파일): $target"

    elif grep -qF "$OPAL_START" "$target"; then
        local tmp
        tmp="$(mktemp)"
        local in_section=0

        while IFS= read -r line || [[ -n "$line" ]]; do
            if [[ "$line" == "$OPAL_START" ]]; then
                in_section=1
                echo "$OPAL_START"
                echo "$content"
                echo "$OPAL_END"
            elif [[ "$line" == "$OPAL_END" ]]; then
                in_section=0
            elif [[ $in_section -eq 0 ]]; then
                echo "$line"
            fi
        done < "$target" > "$tmp"

        mv "$tmp" "$target"
        success "$label OPAL 업데이트 (마커 교체): $target"

    elif grep -qF "$R2_START" "$target"; then
        local tmp
        tmp="$(mktemp)"
        local in_section=0

        while IFS= read -r line || [[ -n "$line" ]]; do
            if [[ "$line" == "$R2_START" ]]; then
                in_section=1
                echo "$OPAL_START"
                echo "$content"
                echo "$OPAL_END"
            elif [[ "$line" == "$R2_END" ]]; then
                in_section=0
            elif [[ $in_section -eq 0 ]]; then
                echo "$line"
            fi
        done < "$target" > "$tmp"

        mv "$tmp" "$target"
        success "$label R2→OPAL 전환 (마커 교체): $target"

    else
        {
            echo ""
            echo "$OPAL_START"
            echo "$content"
            echo "$OPAL_END"
        } >> "$target"
        success "$label OPAL 추가 (기존 내용 보존): $target"
    fi
}

# ─── Platform Installers ─────────────────────────────────

install_claude() {
    echo ""
    info "Claude Code 설치..."
    local base="$USER_HOME/.claude"

    install_dir "$FRAMEWORK_ROOT/claude/skills" "$base/skills" "Claude skills (6개)"
    install_dir "$FRAMEWORK_ROOT/claude/agents" "$base/agents" "Claude agents (3개)"
}

install_cursor() {
    echo ""
    info "Cursor 설치..."
    local base="$USER_HOME/.cursor"

    install_dir "$FRAMEWORK_ROOT/cursor/skills" "$base/skills" "Cursor skills (6개)"
    install_dir "$FRAMEWORK_ROOT/cursor/agents" "$base/agents" "Cursor agents (3개)"
}

install_antigravity() {
    echo ""
    info "Antigravity 설치..."
    local base="$USER_HOME/.gemini/antigravity"

    install_dir "$FRAMEWORK_ROOT/antigravity/skills" "$base/skills" "Antigravity skills (9개)"
}

install_opal() {
    echo ""
    info "OPAL AI 에이전트 설치..."
    local opal_dir="$FRAMEWORK_ROOT/templates/opal"
    local opal_home="$USER_HOME/.opal"

    # ~/.opal/ 에이전트 홈 설치
    mkdir -p "$opal_home"

    cp "$opal_dir/core/AGENT.md" "$opal_home/AGENT.md"
    success "OPAL AGENT.md → $opal_home/AGENT.md"

    install_dir "$opal_dir/skills" "$opal_home/skills" "OPAL skills (3개)"
    install_dir "$opal_dir/templates" "$opal_home/templates" "OPAL templates"

    cp "$opal_dir/core/identity-template.md" "$opal_home/templates/identity-template.md"
    success "identity-template.md → $opal_home/templates/"

    # 부트스트래퍼 설치
    echo ""
    info "OPAL 부트스트래퍼 설치..."

    install_opal_section "$opal_dir/bootstrapper/claude-bootstrap.md" \
        "$USER_HOME/.claude/CLAUDE.md" "Claude"

    mkdir -p "$USER_HOME/.cursor/rules"
    cp "$opal_dir/bootstrapper/cursor-bootstrap.mdc" "$USER_HOME/.cursor/rules/000-opal-agent.mdc"
    success "Cursor OPAL → $USER_HOME/.cursor/rules/000-opal-agent.mdc"

    # Cursor: 기존 R2 규칙 파일 제거
    if [[ -f "$USER_HOME/.cursor/rules/000-r2-persona.mdc" ]]; then
        rm "$USER_HOME/.cursor/rules/000-r2-persona.mdc"
        success "Cursor 기존 R2 규칙 제거: 000-r2-persona.mdc"
    fi

    install_opal_section "$opal_dir/bootstrapper/gemini-bootstrap.md" \
        "$USER_HOME/.gemini/GEMINI.md" "Antigravity"
}

# ─── Summary ─────────────────────────────────────────────

count_items() {
    local dir="$1"
    local pattern="$2"

    if [[ -d "$dir" ]]; then
        # shellcheck disable=SC2086
        ls -1d $dir/$pattern 2>/dev/null | wc -l | tr -d ' '
    else
        echo "0"
    fi
}

print_summary() {
    echo ""
    echo -e "${CYAN}══════════════════════════════════════════════════════${NC}"
    echo -e "  ${BOLD}설치 완료${NC}"
    echo -e "${CYAN}══════════════════════════════════════════════════════${NC}"
    echo ""

    for item in "$@"; do
        echo -e "  ${GREEN}✓${NC} $item"
    done

    echo ""
    echo -e "  ${BOLD}설치 경로:${NC}"

    local claude_base="$USER_HOME/.claude"
    local cursor_base="$USER_HOME/.cursor"
    local ag_base="$USER_HOME/.gemini/antigravity"
    local opal_home="$USER_HOME/.opal"

    [[ -d "$claude_base/skills" ]] && \
        echo "    ~/.claude/skills/              $(count_items "$claude_base/skills" "*") skills"
    [[ -d "$claude_base/agents" ]] && \
        echo "    ~/.claude/agents/              $(count_items "$claude_base/agents" "*") agents"
    [[ -f "$claude_base/CLAUDE.md" ]] && grep -qF "$OPAL_START" "$claude_base/CLAUDE.md" && \
        echo "    ~/.claude/CLAUDE.md            OPAL 포함"

    [[ -d "$cursor_base/skills" ]] && \
        echo "    ~/.cursor/skills/              $(count_items "$cursor_base/skills" "*") skills"
    [[ -d "$cursor_base/agents" ]] && \
        echo "    ~/.cursor/agents/              $(count_items "$cursor_base/agents" "*.md") agents"
    [[ -f "$cursor_base/rules/000-opal-agent.mdc" ]] && \
        echo "    ~/.cursor/rules/               OPAL 포함"

    [[ -d "$ag_base/skills" ]] && \
        echo "    ~/.gemini/antigravity/skills/   $(count_items "$ag_base/skills" "*") skills"
    [[ -f "$USER_HOME/.gemini/GEMINI.md" ]] && grep -qF "$OPAL_START" "$USER_HOME/.gemini/GEMINI.md" && \
        echo "    ~/.gemini/GEMINI.md            OPAL 포함"

    [[ -d "$opal_home" ]] && \
        echo "    ~/.opal/                       OPAL 에이전트 홈"

    echo ""
}

# ─── Main ────────────────────────────────────────────────

main() {
    print_banner
    detect_framework_root
    detect_user

    local installed=()

    while true; do
        show_menu

        case "$MENU_CHOICE" in
            1)
                install_claude
                installed+=("Claude Code (skills + agents)")
                print_summary "${installed[@]}"
                ;;
            2)
                install_cursor
                installed+=("Cursor (skills + agents)")
                print_summary "${installed[@]}"
                ;;
            3)
                install_antigravity
                installed+=("Antigravity (skills)")
                print_summary "${installed[@]}"
                ;;
            4)
                install_opal
                installed+=("OPAL (AI 에이전트)")
                print_summary "${installed[@]}"
                ;;
            5)
                install_claude
                install_cursor
                install_antigravity
                install_opal
                installed+=("Claude Code" "Cursor" "Antigravity" "OPAL")
                print_summary "${installed[@]}"
                ;;
            0)
                info "종료합니다."
                exit 0
                ;;
            *)
                warn "잘못된 선택입니다. 다시 선택해주세요."
                ;;
        esac
    done
}

main "$@"
