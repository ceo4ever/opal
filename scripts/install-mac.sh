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

    if [[ ! -d "$FRAMEWORK_ROOT/skills" ]] || [[ ! -d "$FRAMEWORK_ROOT/agents" ]]; then
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
    echo "  [5] MCP 서버       (MCP 설정 → claude, cursor, gemini, antigravity)"
    echo "  [6] 전체 설치"
    echo "  [0] 종료"
    echo ""
    read -rp "선택 (0-6): " MENU_CHOICE
}

# ─── Install Helpers ─────────────────────────────────────

merge_mcp_config() {
    local target="$1"
    local name="$2"
    local config="$3"

    python3 -c "
import json, os, sys

target = sys.argv[1]
name = sys.argv[2]
config = json.loads(sys.argv[3])

if os.path.exists(target):
    with open(target) as f:
        content = f.read().strip()
    data = json.loads(content) if content else {}
else:
    data = {}

data.setdefault('mcpServers', {})

if name in data['mcpServers']:
    sys.exit(0)

data['mcpServers'][name] = config

with open(target, 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
" "$target" "$name" "$config"
}

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

    local skill_count=$(find "$FRAMEWORK_ROOT/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
    local claude_agent_count=$(find "$FRAMEWORK_ROOT/agents/claude" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
    install_dir "$FRAMEWORK_ROOT/skills" "$base/skills" "스킬 (${skill_count}개)"
    install_dir "$FRAMEWORK_ROOT/agents/claude" "$base/agents" "Claude 에이전트 (${claude_agent_count}개)"
}

install_cursor() {
    echo ""
    info "Cursor 설치..."
    local base="$USER_HOME/.cursor"

    local skill_count=$(find "$FRAMEWORK_ROOT/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
    local cursor_agent_count=$(find "$FRAMEWORK_ROOT/agents/cursor" -mindepth 1 -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')
    install_dir "$FRAMEWORK_ROOT/skills" "$base/skills" "스킬 (${skill_count}개)"
    install_dir "$FRAMEWORK_ROOT/agents/cursor" "$base/agents" "Cursor 에이전트 (${cursor_agent_count}개)"
}

install_antigravity() {
    echo ""
    info "Antigravity 설치..."
    local base="$USER_HOME/.gemini/antigravity"

    local skill_count=$(find "$FRAMEWORK_ROOT/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
    install_dir "$FRAMEWORK_ROOT/skills" "$base/skills" "스킬 (${skill_count}개)"

    for agent_dir in "$FRAMEWORK_ROOT/agents/antigravity"/*/; do
        if [[ -d "$agent_dir" ]]; then
            local agent_name
            agent_name="$(basename "$agent_dir")"
            install_dir "$agent_dir" "$base/skills/$agent_name" "에이전트→스킬: $agent_name"
        fi
    done

    # Gemini CLI agents 배포: Cursor 에이전트 파일을 ~/.gemini/agents/에 복사
    local gemini_agents="$USER_HOME/.gemini/agents"
    mkdir -p "$gemini_agents"
    for agent_file in "$FRAMEWORK_ROOT/agents/cursor"/*.md; do
        if [[ -f "$agent_file" ]]; then
            cp "$agent_file" "$gemini_agents/"
        fi
    done
    success "Gemini CLI agents → $gemini_agents/"
}

find_cli_bin() {
    local cli_name="$1"
    shift
    local fallback_paths=("$@")

    if command -v "$cli_name" &>/dev/null; then
        command -v "$cli_name"
        return 0
    fi

    for path in "${fallback_paths[@]}"; do
        if [[ -x "$path" ]]; then
            echo "$path"
            return 0
        fi
    done

    return 1
}

install_mcp_cli() {
    local cli_bin="$1"
    local scope_flag="$2"
    local name="$3"
    local cmd="$4"
    shift 4
    local args=("$@")

    # 이미 등록되어 있으면 스킵
    if "$cli_bin" mcp get "$name" &>/dev/null; then
        return 0
    fi

    "$cli_bin" mcp add $scope_flag "$name" -- "$cmd" "${args[@]}" &>/dev/null
}

install_mcp() {
    local mcp_src="$FRAMEWORK_ROOT/opal/core/mcps"

    if [[ ! -d "$mcp_src" ]]; then
        warn "opal/core/mcps/ 디렉토리가 없습니다 (스킵)"
        return
    fi

    if ! command -v python3 &>/dev/null; then
        warn "python3이 없어 MCP 설정을 자동 머지할 수 없습니다"
        info "수동 설정: https://modelcontextprotocol.io/quickstart"
        return
    fi

    local count=0
    for mcp_file in "$mcp_src"/*.json; do
        [[ -f "$mcp_file" ]] || continue

        local name config install_type platforms command args_json
        name=$(python3 -c "import json; print(json.load(open('$mcp_file'))['name'])")
        config=$(python3 -c "import json; print(json.dumps(json.load(open('$mcp_file'))['config']))")
        install_type=$(python3 -c "import json; print(json.load(open('$mcp_file'))['install_type'])")
        platforms=$(python3 -c "import json; print(' '.join(json.load(open('$mcp_file'))['platforms']))")
        command=$(python3 -c "import json; print(json.load(open('$mcp_file'))['config'].get('command',''))")
        args_json=$(python3 -c "import json; print('\n'.join(json.load(open('$mcp_file'))['config'].get('args',[])))")

        if [[ "$install_type" != "config_merge" ]]; then
            info "  $name: $install_type 타입 — 수동 설치 필요"
            continue
        fi

        # args_json → args_array 변환
        local args_array=()
        while IFS= read -r arg; do
            [[ -n "$arg" ]] && args_array+=("$arg")
        done <<< "$args_json"

        local installed_platforms=()
        for platform in $platforms; do
            case "$platform" in
                claude)
                    local bin
                    if bin=$(find_cli_bin claude "$USER_HOME/.local/bin/claude"); then
                        if install_mcp_cli "$bin" "--scope user" "$name" "$command" "${args_array[@]}"; then
                            installed_platforms+=("claude")
                        fi
                    else
                        warn "claude CLI 없음 — 수동 등록: claude mcp add $name -- $command ${args_array[*]}"
                    fi
                    ;;
                gemini)
                    local bin
                    if bin=$(find_cli_bin gemini /opt/homebrew/bin/gemini /usr/local/bin/gemini); then
                        if install_mcp_cli "$bin" "-s user" "$name" "$command" "${args_array[@]}"; then
                            installed_platforms+=("gemini")
                        fi
                    else
                        warn "gemini CLI 없음 — config_merge 폴백"
                        local target="$USER_HOME/.gemini/settings.json"
                        mkdir -p "$(dirname "$target")"
                        merge_mcp_config "$target" "$name" "$config"
                        installed_platforms+=("gemini")
                    fi
                    ;;
                cursor)
                    local target="$USER_HOME/.cursor/mcp.json"
                    mkdir -p "$(dirname "$target")"
                    merge_mcp_config "$target" "$name" "$config"
                    installed_platforms+=("cursor")
                    ;;
                antigravity)
                    local target="$USER_HOME/.gemini/antigravity/mcp_config.json"
                    mkdir -p "$(dirname "$target")"
                    merge_mcp_config "$target" "$name" "$config"
                    installed_platforms+=("antigravity")
                    ;;
            esac
        done

        if [[ ${#installed_platforms[@]} -gt 0 ]]; then
            success "$name MCP → ${installed_platforms[*]}"
            ((count++))
        fi
    done

    if [[ $count -eq 0 ]]; then
        info "머지할 MCP 서버가 없습니다"
    else
        success "MCP 서버 ${count}건 설정 완료"
    fi
}

install_opal_community_skills() {
    local cs_src="$FRAMEWORK_ROOT/community-skills"
    local cs_dst="$USER_HOME/.opal/community-skills"

    if [[ ! -d "$cs_src" ]]; then
        warn "community-skills/ 디렉토리가 없습니다 (스킵)"
        return
    fi

    mkdir -p "$cs_dst"

    for vendor_dir in "$cs_src"/*/; do
        if [[ -d "$vendor_dir" ]]; then
            cp -Rf "$vendor_dir" "$cs_dst/"
        fi
    done

    local cs_count
    cs_count="$(find "$cs_src" -mindepth 2 -maxdepth 2 -type d | wc -l | tr -d ' ')"
    success "커뮤니티 스킬 ${cs_count}개 → $cs_dst/"
}

install_opal_references() {
    local ref_src="$FRAMEWORK_ROOT/opal/core/references"
    local ref_dst="$USER_HOME/.opal/references"

    if [[ ! -d "$ref_src" ]]; then
        warn "opal/core/references/ 디렉토리가 없습니다 (스킵)"
        return
    fi

    mkdir -p "$ref_dst"
    cp -Rf "$ref_src"/. "$ref_dst"/
    success "참조 레지스트리 → $ref_dst/"
}

install_opal() {
    echo ""
    info "OPAL AI 에이전트 설치..."
    local opal_dir="$FRAMEWORK_ROOT/opal"
    local opal_home="$USER_HOME/.opal"

    mkdir -p "$opal_home"

    cp "$opal_dir/core/AGENT.md" "$opal_home/AGENT.md"
    success "OPAL AGENT.md → $opal_home/AGENT.md"

    local opal_skill_count=$(find "$opal_dir/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
    install_dir "$opal_dir/skills" "$opal_home/skills" "OPAL 스킬 (${opal_skill_count}개)"
    install_dir "$opal_dir/templates" "$opal_home/templates" "OPAL templates"

    cp "$opal_dir/core/identity-template.md" "$opal_home/templates/identity-template.md"
    success "identity-template.md → $opal_home/templates/"

    # 참조 레지스트리 복사
    install_opal_references

    # 커뮤니티 스킬 복사
    install_opal_community_skills

    # 부트스트래퍼 설치
    echo ""
    info "OPAL 부트스트래퍼 설치..."

    install_opal_section "$opal_dir/bootstrapper/claude-bootstrap.md" \
        "$USER_HOME/.claude/CLAUDE.md" "Claude"

    mkdir -p "$USER_HOME/.cursor/rules"
    cp "$opal_dir/bootstrapper/cursor-bootstrap.mdc" "$USER_HOME/.cursor/rules/000-opal-agent.mdc"
    success "Cursor OPAL → $USER_HOME/.cursor/rules/000-opal-agent.mdc"

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

    echo "    Claude MCP                     claude mcp add (CLI 등록)"
    echo "    Gemini MCP                     gemini mcp add (CLI 등록)"
    [[ -f "$cursor_base/mcp.json" ]] && \
        echo "    ~/.cursor/mcp.json             MCP 설정 (config_merge)"
    [[ -f "$USER_HOME/.gemini/antigravity/mcp_config.json" ]] && \
        echo "    ~/.gemini/antigravity/mcp_config.json  MCP 설정 (config_merge)"

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
                echo ""
                info "MCP 서버 설정..."
                install_mcp
                installed+=("MCP 서버 설정")
                print_summary "${installed[@]}"
                ;;
            6)
                install_claude
                install_cursor
                install_antigravity
                install_opal
                echo ""
                info "MCP 서버 설정..."
                install_mcp
                installed+=("Claude Code" "Cursor" "Antigravity" "OPAL" "MCP 서버")
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
