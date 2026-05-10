#!/usr/bin/env bash
#
# opal/tools/opal-cli/lib/mcp.sh — mcp 서브커맨드
#
# Usage:
#   opal-cli mcp list                 등록된 MCP 서버 목록 출력
#   opal-cli mcp add <name>           MCP 서버 추가 (opal/core/mcps/ 에서 탐색)
#   opal-cli mcp remove <name>        MCP 서버 제거 (미구현 — 수동 제거 안내)
#   opal-cli mcp install-all          모든 MCP 서버 재설치 (install_mcp 재실행)
#   opal-cli mcp --help
#
# 동작:
#   opal/core/mcps/*.json 정의를 읽어 Claude/Cursor/Gemini/Antigravity에
#   MCP 서버를 등록한다. scripts/install-mac.sh:966-1056 install_mcp() 로직 래핑.
#
# 변경이력:
#   v1.0   2026-05-08 11:00 초기 구현 — install_mcp 로직 래핑 + list/add/install-all (139)
#   v1.0.1 2026-05-10 21:00 command 화이트리스트 검증 추가 — npx/npm/node/python3만 허용 (144)
#

# ─── mcp 서브커맨드 ───────────────────────────────────────────

cmd_mcp() {
    local subcmd="${1:-}"

    case "$subcmd" in
        list)
            shift
            _mcp_list "$@"
            ;;
        add)
            shift
            _mcp_add "$@"
            ;;
        remove)
            shift
            _mcp_remove "$@"
            ;;
        install-all)
            shift
            _mcp_install_all "$@"
            ;;
        --help|-h|help|"")
            _mcp_usage
            return 0
            ;;
        *)
            error "알 수 없는 mcp 서브커맨드: $subcmd"
            _mcp_usage
            return 1
            ;;
    esac
}

# ─── list ────────────────────────────────────────────────────

_mcp_list() {
    local opal_home="${OPAL_HOME:-$HOME/.opal}"
    local mcp_src="${FRAMEWORK_ROOT:-$opal_home}/opal/core/mcps"

    # 배포된 mcps는 opal_home 기준
    if [[ ! -d "$mcp_src" ]]; then
        mcp_src="$opal_home/tools/mcp"  # 혹시 별도 배포 경로가 있을 경우
    fi

    echo ""
    echo "[OPAL MCP 서버 목록]"
    echo ""

    # opal/core/mcps/*.json에서 이름·플랫폼 읽기
    local found=0
    if [[ -d "$mcp_src" ]]; then
        for mcp_file in "$mcp_src"/*.json; do
            [[ -f "$mcp_file" ]] || continue
            found=1
            if command -v python3 &>/dev/null; then
                local name platforms
                name=$(python3 -c "import json; d=json.load(open('$mcp_file')); print(d.get('name','?'))" 2>/dev/null) || name="(파싱 실패)"
                platforms=$(python3 -c "import json; d=json.load(open('$mcp_file')); print(' '.join(d.get('platforms',[])))" 2>/dev/null) || platforms="?"
                echo "  - $name  (플랫폼: $platforms)"
            else
                echo "  - $(basename "$mcp_file" .json)"
            fi
        done
    fi

    if [[ "$found" -eq 0 ]]; then
        info "등록된 MCP 정의 파일이 없습니다: $mcp_src/*.json"
    fi

    echo ""
    info "현재 Claude 등록 MCP:"
    if command -v claude &>/dev/null; then
        claude mcp list 2>/dev/null || info "  (claude CLI 없음 또는 mcp list 미지원)"
    else
        info "  claude CLI를 찾을 수 없습니다"
    fi
}

# ─── add ─────────────────────────────────────────────────────

_mcp_add() {
    local name="${1:-}"

    if [[ -z "$name" ]]; then
        error "MCP 서버 이름을 지정하세요."
        info "  opal-cli mcp add <name>"
        info "  opal-cli mcp list 로 사용 가능한 서버를 확인하세요."
        return 1
    fi

    local opal_home="${OPAL_HOME:-$HOME/.opal}"
    local mcp_src="${FRAMEWORK_ROOT:-$opal_home}/opal/core/mcps"

    if [[ ! -d "$mcp_src" ]]; then
        error "MCP 정의 디렉토리를 찾을 수 없습니다: $mcp_src"
        return 1
    fi

    local mcp_file="$mcp_src/${name}.json"
    if [[ ! -f "$mcp_file" ]]; then
        error "MCP 정의 파일을 찾을 수 없습니다: $mcp_file"
        info "사용 가능한 MCP 목록: opal-cli mcp list"
        return 1
    fi

    if ! command -v python3 &>/dev/null; then
        error "python3가 필요합니다. python3를 설치 후 다시 시도하세요."
        return 1
    fi

    info "MCP 서버 추가 중: $name"

    local install_type platforms command args_json
    install_type=$(python3 -c "import json; print(json.load(open('$mcp_file'))['install_type'])" 2>/dev/null) || install_type=""
    platforms=$(python3 -c "import json; print(' '.join(json.load(open('$mcp_file'))['platforms']))" 2>/dev/null) || platforms=""
    command=$(python3 -c "import json; print(json.load(open('$mcp_file'))['config'].get('command',''))" 2>/dev/null) || command=""
    args_json=$(python3 -c "import json; print('\n'.join(json.load(open('$mcp_file'))['config'].get('args',[])))" 2>/dev/null) || args_json=""

    if [[ "$install_type" != "config_merge" ]]; then
        warn "$name: $install_type 타입은 수동 설치가 필요합니다."
        info "MCP 서버 설정 방법: https://modelcontextprotocol.io/quickstart"
        return 1
    fi

    # command 화이트리스트 검증 (GC-002, R-4) — npx/npm/node/python3만 허용
    local cmd_basename
    cmd_basename="$(basename "$command")"
    case "$cmd_basename" in
        npx|npm|node|python3|python) ;;
        *) error "MCP command '$command' 화이트리스트 미통과 — npx/npm/node/python3만 허용"; return 1 ;;
    esac

    # args_json → args_array
    local args_array=()
    while IFS= read -r arg; do
        [[ -n "$arg" ]] && args_array+=("$arg")
    done <<< "$args_json"

    # 플랫폼별 등록
    local installed_count=0
    for platform in $platforms; do
        case "$platform" in
            claude)
                if command -v claude &>/dev/null; then
                    if claude mcp add --scope user "$name" -- "$command" "${args_array[@]}" &>/dev/null; then
                        success "claude: $name 등록 완료"
                        ((installed_count++))
                    else
                        warn "claude: $name 등록 실패 (이미 등록됨 or 오류)"
                    fi
                else
                    warn "claude CLI 없음 — 수동 등록: claude mcp add $name -- $command ${args_array[*]:-}"
                fi
                ;;
            gemini)
                if command -v gemini &>/dev/null; then
                    if gemini mcp add -s user "$name" -- "$command" "${args_array[@]}" &>/dev/null; then
                        success "gemini: $name 등록 완료"
                        ((installed_count++))
                    else
                        warn "gemini: $name 등록 실패"
                    fi
                else
                    warn "gemini CLI 없음 — config 병합 폴백"
                    local config
                    config=$(python3 -c "import json; print(json.dumps(json.load(open('$mcp_file'))['config']))" 2>/dev/null)
                    _merge_mcp_config "$HOME/.gemini/settings.json" "$name" "$config"
                    ((installed_count++))
                fi
                ;;
            cursor)
                local config
                config=$(python3 -c "import json; print(json.dumps(json.load(open('$mcp_file'))['config']))" 2>/dev/null)
                _merge_mcp_config "$HOME/.cursor/mcp.json" "$name" "$config"
                success "cursor: $name 등록 완료"
                ((installed_count++))
                ;;
            antigravity)
                local config
                config=$(python3 -c "import json; print(json.dumps(json.load(open('$mcp_file'))['config']))" 2>/dev/null)
                _merge_mcp_config "$HOME/.gemini/antigravity/mcp_config.json" "$name" "$config"
                success "antigravity: $name 등록 완료"
                ((installed_count++))
                ;;
        esac
    done

    if [[ "$installed_count" -gt 0 ]]; then
        success "$name MCP 등록 완료 ($installed_count 플랫폼)"
    else
        error "$name MCP 등록 실패"
        return 1
    fi
}

# ─── remove ──────────────────────────────────────────────────

_mcp_remove() {
    local name="${1:-}"

    if [[ -z "$name" ]]; then
        error "제거할 MCP 서버 이름을 지정하세요."
        info "  opal-cli mcp remove <name>"
        return 1
    fi

    info "MCP 서버 제거는 현재 플랫폼 CLI를 통해 직접 수행하세요:"
    info "  Claude:  claude mcp remove $name"
    info "  Gemini:  gemini mcp remove -s user $name"
    info "  Cursor:  ~/.cursor/mcp.json에서 $name 항목 수동 삭제"
}

# ─── install-all ─────────────────────────────────────────────

_mcp_install_all() {
    local opal_home="${OPAL_HOME:-$HOME/.opal}"
    local mcp_src="${FRAMEWORK_ROOT:-$opal_home}/opal/core/mcps"

    if [[ ! -d "$mcp_src" ]]; then
        error "MCP 정의 디렉토리를 찾을 수 없습니다: $mcp_src"
        return 1
    fi

    if ! command -v python3 &>/dev/null; then
        error "python3가 필요합니다."
        return 1
    fi

    info "모든 MCP 서버 설치 중..."
    local count=0
    for mcp_file in "$mcp_src"/*.json; do
        [[ -f "$mcp_file" ]] || continue
        local name
        name=$(python3 -c "import json; print(json.load(open('$mcp_file'))['name'])" 2>/dev/null) || continue
        _mcp_add "$name" && ((count++)) || true
    done

    if [[ "$count" -eq 0 ]]; then
        info "설치된 MCP 서버가 없습니다."
    else
        success "총 ${count}개 MCP 서버 설치 완료"
    fi
}

# ─── 헬퍼: MCP config JSON 병합 ──────────────────────────────

_merge_mcp_config() {
    local target="$1"
    local name="$2"
    local config="$3"

    mkdir -p "$(dirname "$target")"

    if [[ -f "$target" ]]; then
        python3 - "$target" "$name" "$config" <<'PYEOF'
import json, sys
target, name, config_str = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    with open(target) as f:
        data = json.load(f)
except Exception:
    data = {}
if "mcpServers" not in data:
    data["mcpServers"] = {}
data["mcpServers"][name] = json.loads(config_str)
with open(target, "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")
PYEOF
    else
        python3 - "$target" "$name" "$config" <<'PYEOF'
import json, sys
target, name, config_str = sys.argv[1], sys.argv[2], sys.argv[3]
data = {"mcpServers": {name: json.loads(config_str)}}
with open(target, "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")
PYEOF
    fi
}

_mcp_usage() {
    cat <<EOF
사용법: opal-cli mcp <subcommand> [options]

OPAL MCP 서버를 관리합니다.

서브커맨드:
  list                   등록 가능한 MCP 서버 목록 출력
  add <name>             MCP 서버 추가 (Claude/Cursor/Gemini/Antigravity)
  remove <name>          MCP 서버 제거 안내 (플랫폼 CLI 직접 사용)
  install-all            모든 MCP 서버 재설치

옵션:
  --help, -h    이 도움말 출력

예시:
  opal-cli mcp list
  opal-cli mcp add context7
  opal-cli mcp add playwright
  opal-cli mcp install-all
  opal-cli mcp remove context7
EOF
}
