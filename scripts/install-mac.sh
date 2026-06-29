#!/bin/bash
#
# install-mac.sh — OPAL AI Framework Installer (macOS)
#
# Usage: ./scripts/install-mac.sh
#
# 변경이력:
#   v1.1 2026-04-30: 플랫폼 sub-agent 어댑터 자동 생성 추가 (Claude/Cursor/Gemini, Antigravity 미지원) — task 133
#   v1.2 2026-04-30: emit_platform_agent_adapter description 평탄화 — Claude Code 파서 호환 (133)
#   v1.3 2026-04-30: AUTO-GENERATED 헤더 검사를 전체 파일로 확장 — head 3 라인 한정 시 frontmatter만 봐서 오탐지하던 결함 수정 (133)
#   v1.4 2026-05-08 KST: install_opal_bin/register_path_in_shell_rc 신설 + tools/ strip 호출 추가 (D 영역 PATH 등록) (139)
#   v1.5 2026-05-09 14:20 KST: install_opal_bin에 PATH 사용 방법 안내 추가 — source/exec/새 터미널 옵션 + 절대 경로 폴백 명시 (139 추가작업)
#   v1.6 2026-05-09 15:00 KST: 비대화형 모드 추가 — OPAL_AUTO_INSTALL=1 또는 stdin이 tty가 아닐 때(pipe) detect_user 자동 통과 + 메뉴 [3] 전체 설치 자동 실행. one-liner `curl | bash` 호환 결함 fix (139 추가작업, P0)
#   v1.7 2026-05-09 17:30 KST: install_opal_venv pip 호출에 --no-cache-dir 추가 — "Cache entry deserialization failed" 경고 차단 (139 추가작업)
#   v1.8 2026-05-09 21:00 KST: install_opal() 끝에 ~/.opal/VERSION 기록 추가 — opal-cli update의 로컬/리모트 버전 비교 기반 (139 추가작업)
#   v1.9 2026-05-09 21:15 KST: 출력 quiet 모드 default — info/success 침묵, OPAL_VERBOSE=1 시 자세히. step() 신규로 단계 진행 표시. main() 비대화형 분기 정제 (139 추가작업)
#   v2.0 2026-05-10 17:00 KST: community-skills 번들 → fetch 방식 전환 — install_opal_community_skills 함수 제거 + clean_dirs에서 community-skills 제거 (사용자 데이터 보존, D-4) + 종료 안내 추가 (142)
#   v2.1 2026-05-10 21:00 KST: command 화이트리스트 + fork repo banner + OPAL_HOME 가드 + playwright cache 디렉토리 생성 (144)
#   v2.2 2026-05-12 21:35 KST: cmux-tool 등록 + opal-wtm-agent 자동 어댑터 — install_opal()의 tools/ 처리 직후 cmux-tool/run.sh chmod +x 추가 (002)
#   v2.3 2026-05-20: install_opal_venv Playwright 캐시 경로 OS 분기 — Linux는 ~/.cache/ms-playwright (XDG 표준). Linux one-liner 진입점 신설 동반 수정 (006)
#   v2.4 2026-05-22 10:00 KST: cmux-tool lib/*.sh + examples/*.sh chmod +x 추가. 안내 메시지 "Phase 2(cmux)" → "cmux-tool" (007)
#   v2.5 2026-05-23 18:57 KST: detect_framework_root 검사 기준을 agents/ → opal/agents/ 로 갱신 — 태스크 002에서 wtm-agent를 opal/agents/로 이동하면서 루트 agents/ 폴더가 소멸했으나 사전 점검만 옛 구조를 검증해 즉시 차단되던 결함 fix (hotfix, "그냥 해")
#   v2.6 2026-05-24: Codex CLI 통합 — install_codex_agents 신설 + install_opal/install_mcp/show_menu/print_summary codex 분기 + emit_platform_agent_adapter codex 모델 매핑 (009)
#   v2.6.1 2026-05-24: install_codex_agents Python heredoc toml_escape docstring을 raw string(r""")으로 정정 — Python 3.12+ "\ → \\" docstring이 invalid escape sequence SyntaxWarning 13회 발생하던 결함 fix (009 EXECUTE 정정)
#   v2.6.2 2026-05-24: print_summary에 ~/.codex/AGENTS.md OPAL 부트스트래퍼 행 추가 — 다른 플랫폼(Claude/Cursor/Gemini) 부트스트래퍼 행과 일관성 결손 결함 fix (009 EXECUTE 정정 #2 — PLAN §3.3 U-1 (7) 설계 누락)
#   v2.7 2026-06-02 20:16 KST: 모델 매핑 최신화 — emit_platform_agent_adapter gemini(gemini-3.1-flash-lite/gemini-flash-latest/gemini-pro-latest) + codex(gpt-5.4-mini/gpt-5.5/gpt-5.3-codex) dict + codex_model_map + 기본값 gpt-5.5 (011)
#   v2.7 2026-06-02 20:16 KST: 모델 매핑 최신화 — Gemini 부동 별칭 전환 + Codex 최신 ID 갱신 (011)
#   v2.8 2026-06-07: OPAL 헌법(PRINCIPLES.md) 배포 추가 — strip_deploy_md로 opal/core/PRINCIPLES.md → ~/.opal/PRINCIPLES.md (always-on) (012)
#   v2.9 2026-06-15: OPAL Console 설치 추가 — install_dashboard() 신설 (FE npm 빌드·BE 복사·dashboard-server 배포) + clean_dirs에 dashboard-server 추가 (021)
#   v3.0 2026-06-15: 메뉴 [5] OPAL Console 추가 — install_dashboard 단독 + 자동 재시작(stop→start) + /health 확인 (021 후속)
#   v3.1 2026-06-17 10:24: install_opal()에 git core.quotepath=false 전역 설정 추가 — 한글 태스크 폴더명 허용에 따른 git 경로 표시 개선 (026 L2: 한글 폴더명 허용)
#   v3.2 2026-06-17: Codex 어댑터 정합 — install_codex_config 신설(config.toml [agents] 멱등 작성, max_threads=6/max_depth=1/job_max_runtime_seconds=1800) + 호출부 연결 + emit_platform_agent_adapter·codex_model_map stale Codex 매핑(standard=gpt-5.5/advanced=gpt-5.3-codex) → SSOT v1.4 정정(standard=gpt-5.4/advanced=gpt-5.5) (028)
#   v3.3 2026-06-21 16:18 KST: emit_platform_agent_adapter 본문 model 레벨 치환 추가 — f.write(body) 직전 _LEVEL_RE(`[,(]\s*model:\s*(light|standard|advanced)\b`)+_sub_body_model로 본문 인라인 sub-dispatch 토큰을 mapping[platform] 실모델명으로 변환(cursor=inherit→토큰 제거+빈괄호 정리). 액션 에이전트 sub-dispatch model 레벨명이 Agent 도구 model enum 위반하던 버그 fix. frontmatter 변환·prose 자기참조 불변 (032)
#   v3.4 2026-06-24: OPAL_TEST_TOOLS_GLOBAL shell rc 자동 등록 추가 — register_test_tools_global_in_shell_rc 신설 + install_opal_bin 연결 (041)
#   v3.5 2026-06-24: install_claude_permissions perm_entries에 'Bash(echo $OPAL_BOOTSTRAP)' 추가 — 부트스트랩 스킵 게이트 환경변수 점검 명령을 매 세션 무프롬프트 허용
#   v3.6 2026-06-24 17:26 KST: install_opal_setting 신규 + perm_entries echo 권한 제거(v3.5 reconcile) — OPAL_BOOTSTRAP 환경변수 게이트를 setting.json Read 게이트로 전환 (043)
#   v3.7 2026-06-29 15:24 KST: record_installed_version 함수 분리 + VERSION 기록 우선순위 재배치 — FRAMEWORK_ROOT/VERSION 각인값 최우선, API/main 폴백 강등 (048)
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
HARDENING_START="# === GEMINI HARDENING START ==="
HARDENING_END="# === GEMINI HARDENING END ==="

# ─── Logging ─────────────────────────────────────────────
# OPAL_VERBOSE=1 시 info/success 자세한 출력. default(미설정/0)는 quiet — 단계 진행만 표시.

OPAL_VERBOSE="${OPAL_VERBOSE:-0}"

info()    { [[ "$OPAL_VERBOSE" == "1" ]] && echo -e "${BLUE}[INFO]${NC} $1" || true; }
success() { [[ "$OPAL_VERBOSE" == "1" ]] && echo -e "${GREEN}  ✓${NC} $1" || true; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; }
step()    { echo -e "${BLUE}▸${NC} $1"; }

# ─── Core Functions ──────────────────────────────────────

print_banner() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC}  ${BOLD}OPAL AI Framework Installer${NC}  (macOS)               ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}  통합 배포: ~/.opal/ (skills + agents)                ${CYAN}║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""
}

detect_framework_root() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    FRAMEWORK_ROOT="$(dirname "$script_dir")"

    if [[ ! -d "$FRAMEWORK_ROOT/skills" ]] || [[ ! -d "$FRAMEWORK_ROOT/opal/agents" ]]; then
        error "프레임워크 루트를 찾을 수 없습니다: $FRAMEWORK_ROOT"
        error "이 스크립트는 opal/scripts/ 에서 실행해야 합니다."
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

    # 비대화형 모드 (one-liner curl | bash 호환):
    #   - OPAL_AUTO_INSTALL=1 명시적 설정
    #   - 또는 stdin이 tty가 아님 (pipe로 호출됨)
    if [[ "${OPAL_AUTO_INSTALL:-0}" == "1" ]] || [[ ! -t 0 ]]; then
        info "비대화형 모드 — 현재 사용자에 자동 설치"
        return 0
    fi

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
    echo "  [1] OPAL 설치      (skills + agents + 부트스트래퍼 + OPAL Console → ~/.opal/, 서버 자동 기동)"
    echo "  [2] MCP 서버 설정   (MCP 설정 → claude, cursor, gemini, antigravity, codex)"
    echo "  [3] 전체 설치       (OPAL + MCP 서버)"
    echo "  [4] Python 패키지   (requirements.txt → ~/.opal/.venv/ 업데이트)"
    echo "  [5] OPAL Console   (dashboard 빌드+배포 → ~/.opal/dashboard-server/ + 서버 자동 기동)"
    echo "  [0] 종료"
    echo ""
    read -rp "선택 (0-5): " MENU_CHOICE
}

# ─── Install Helpers ─────────────────────────────────────

merge_mcp_config() {
    local target="$1"
    local name="$2"
    local config="$3"

    /usr/bin/python3 -c "
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

merge_hooks_config() {
    local target="$1"
    local hooks_json="$2"

    /usr/bin/python3 -c "
import json, os, sys

target = sys.argv[1]
hooks_file = sys.argv[2]

with open(hooks_file) as f:
    source_hooks = json.load(f)

if os.path.exists(target):
    with open(target) as f:
        content = f.read().strip()
    data = json.loads(content) if content else {}
else:
    data = {}

data.setdefault('hooks', {})
for event, rules in source_hooks.items():
    data['hooks'][event] = rules

with open(target, 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
" "$target" "$hooks_json"
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

# 배포용 .md 파일에서 "## 변경이력" 섹션부터 파일 끝까지 제거
# 사용: strip_deploy_md <source_path> <destination_path>
strip_deploy_md() {
    local src="$1"
    local dst="$2"
    /usr/bin/awk 'BEGIN{keep=1} /^## 변경이력$/{keep=0} keep==1{print}' "$src" > "$dst"
}

# 디렉토리 하위 모든 .md 파일에서 "## 변경이력" 섹션 제거 (in-place)
# 사용: strip_deploy_md_recursive <directory>
strip_deploy_md_recursive() {
    local root="$1"
    /usr/bin/find "$root" -type f -name "*.md" -print0 | while IFS= read -r -d '' file; do
        if /usr/bin/grep -q '^## 변경이력$' "$file"; then
            /usr/bin/awk 'BEGIN{keep=1} /^## 변경이력$/{keep=0} keep==1{print}' "$file" > "${file}.tmp" && /bin/mv "${file}.tmp" "$file"
        fi
    done
}

extract_bootstrap_content() {
    local file="$1"
    # 4-backtick 외부 블록 우선 (내부에 ``` 포함 가능), 없으면 3-backtick 블록 사용
    if grep -q '^````markdown$' "$file"; then
        sed -n '/^````markdown$/,/^````$/p' "$file" | sed '1d;$d'
    else
        sed -n '/^```markdown$/,/^```$/p' "$file" | sed '1d;$d'
    fi
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

install_gemini_hardening() {
    local snippet="$1"
    local target="$2"
    local label="$3"

    local content
    content="$(extract_bootstrap_content "$snippet")"

    if [[ -z "$content" ]]; then
        error "HARDENING 부트스트래퍼 내용을 추출할 수 없습니다: $snippet"
        return 1
    fi

    mkdir -p "$(dirname "$target")"

    if [[ ! -f "$target" ]]; then
        {
            echo "$HARDENING_START"
            echo "$content"
            echo "$HARDENING_END"
        } > "$target"
        success "$label HARDENING 설치 (새 파일): $target"

    elif grep -qF "$HARDENING_START" "$target"; then
        local tmp
        tmp="$(mktemp)"
        local in_section=0

        while IFS= read -r line || [[ -n "$line" ]]; do
            if [[ "$line" == "$HARDENING_START" ]]; then
                in_section=1
                echo "$HARDENING_START"
                echo "$content"
                echo "$HARDENING_END"
            elif [[ "$line" == "$HARDENING_END" ]]; then
                in_section=0
            elif [[ $in_section -eq 0 ]]; then
                echo "$line"
            fi
        done < "$target" > "$tmp"

        mv "$tmp" "$target"
        success "$label HARDENING 업데이트 (마커 교체): $target"

    else
        {
            echo ""
            echo "$HARDENING_START"
            echo "$content"
            echo "$HARDENING_END"
        } >> "$target"
        success "$label HARDENING 추가 (기존 내용 보존): $target"
    fi
}

# ─── Claude Permissions ─────────────────────────────────

install_claude_permissions() {
    local settings="$USER_HOME/.claude/settings.json"

    mkdir -p "$(dirname "$settings")"

    /usr/bin/python3 -c "
import json, os, sys

settings_path = sys.argv[1]
opal_home = sys.argv[2]

# 절대 경로와 틸다 경로 모두 등록 (Claude Code가 두 형태를 별도로 매칭)
perm_entries = [f'Read({opal_home}/**)', 'Read(~/.opal/**)']

if os.path.exists(settings_path):
    with open(settings_path) as f:
        content = f.read().strip()
    data = json.loads(content) if content else {}
else:
    data = {}

perms = data.setdefault('permissions', {})
allow = perms.setdefault('allow', [])

changed = False
for perm_entry in perm_entries:
    if perm_entry not in allow:
        allow.append(perm_entry)
        changed = True

if changed:
    with open(settings_path, 'w') as f:
        json.dump(data, f, indent=2)
        f.write('\n')
" "$settings" "$USER_HOME/.opal"

    success "Claude Code ~/.opal 읽기 권한 → $settings"
}

# ─── Gemini Config ──────────────────────────────────────

install_gemini_config() {
    local config="$USER_HOME/.gemini/settings.json"
    local include_dirs=("~/.opal/" "~/.gemini/")

    mkdir -p "$(dirname "$config")"

    /usr/bin/python3 -c "
import json, os, sys

config_path = sys.argv[1]
new_dirs = sys.argv[2:]

if os.path.exists(config_path):
    with open(config_path) as f:
        content = f.read().strip()
    data = json.loads(content) if content else {}
else:
    data = {}

ctx = data.setdefault('context', {})
existing = set(ctx.get('includeDirectories', []))
for d in new_dirs:
    existing.add(d)
ctx['includeDirectories'] = sorted(existing)

with open(config_path, 'w') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
" "$config" "${include_dirs[@]}"

    success "Gemini 외부 경로 접근 설정 → $config"
}

# ─── 플랫폼 sub-agent 어댑터 ────────────────────────────
#
# OPAL 에이전트(`~/.opal/agents/{name}/AGENT.md`)를 각 플랫폼 sub-agent 형식으로 변환하여
# 사용자 등록 경로(`~/.claude/agents/`, `~/.cursor/agents/`, `~/.gemini/agents/`)에 배포한다.
# 변환 규칙 SSOT: opal/core/references/agents.md §플랫폼 sub-agent 어댑터 변환 규칙
# Antigravity는 custom sub-agent 미지원 (2026-04 기준):
#   https://discuss.ai.google.dev/t/antigravity-sub-agents/114381

emit_platform_agent_adapter() {
    local src_dir="$1"
    local dst_file="$2"
    local platform="$3"

    local agent_md="$src_dir/AGENT.md"
    [[ -f "$agent_md" ]] || return 0

    # Python 인터프리터 결정: venv 우선 + 시스템 폴백 (W-3)
    local py
    if [[ -x "$USER_HOME/.opal/.venv/bin/python3" ]]; then
        py="$USER_HOME/.opal/.venv/bin/python3"
    else
        py="/usr/bin/python3"
    fi

    "$py" - "$agent_md" "$dst_file" "$platform" <<'PYEOF'
import os, re, sys

src, dst, platform = sys.argv[1], sys.argv[2], sys.argv[3]

def _flatten_description(s):
    """multiline description을 single-line으로 평탄화 (Claude Code 파서 호환)."""
    if not s:
        return ''
    # 모든 whitespace(개행 포함)를 단일 공백으로
    return re.sub(r'\s+', ' ', s).strip()

# PyYAML 폴백 (W-1): venv에 PyYAML이 있으면 사용, 없으면 stdlib 정규식 파서로 폴백
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

with open(src, 'r', encoding='utf-8') as f:
    text = f.read()

m = re.match(r'^---\n(.*?)\n---\n?(.*)$', text, re.DOTALL)
if not m:
    sys.exit(0)  # frontmatter 없는 파일은 스킵

fm_raw = m.group(1)
body = m.group(2)

# frontmatter 파싱
if HAS_YAML:
    try:
        fm = yaml.safe_load(fm_raw) or {}
    except Exception as e:
        sys.stderr.write(f"warn: YAML parse failed for {src} ({e}) — fallback parser used\n")
        HAS_YAML = False

if not HAS_YAML:
    # stdlib 정규식 폴백: name/description/model 만 추출
    sys.stderr.write(f"warn: PyYAML missing — fallback parser used for {os.path.basename(os.path.dirname(src))}\n")
    fm = {}
    lines = fm_raw.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        # 단일 라인 key: value
        sm = re.match(r'^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$', line)
        if sm:
            key = sm.group(1)
            val = sm.group(2).strip()
            # `|` 또는 `>` 블록 스타일 — 들여쓰기 라인 모두 수집 후 평탄화
            if val in ('|', '>', '|-', '>-', '|+', '>+'):
                block_lines = []
                j = i + 1
                while j < len(lines):
                    nxt = lines[j]
                    if re.match(r'^\s+\S', nxt) or nxt.strip() == '':
                        block_lines.append(nxt.strip())
                        j += 1
                    else:
                        break
                fm[key] = _flatten_description(' '.join(block_lines))
                i = j
                continue
            else:
                # 따옴표 제거
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                # 단일 라인 description도 평탄화 (이미 single-line이라 영향 없음)
                fm[key] = _flatten_description(val)
        i += 1

# 필수 필드: name (없으면 디렉토리 이름으로 폴백)
agent_name = fm.get('name')
if not agent_name:
    agent_name = os.path.basename(os.path.dirname(src))
    sys.stderr.write(f"warn: name missing — using dir name '{agent_name}'\n")

description = _flatten_description(fm.get('description') or '')
opal_model = fm.get('model', 'standard')

# 플랫폼별 모델 매핑 (agents.md §변환 규칙 표와 동기)
mapping = {
    'claude': {'light': 'haiku', 'standard': 'sonnet', 'advanced': 'opus'},
    'cursor': {'light': 'inherit', 'standard': 'inherit', 'advanced': 'inherit'},
    'gemini': {'light': 'gemini-3.1-flash-lite', 'standard': 'gemini-flash-latest', 'advanced': 'gemini-pro-latest'},
    'codex': {'light': 'gpt-5.4-mini', 'standard': 'gpt-5.4', 'advanced': 'gpt-5.5'},
}
model_value = mapping.get(platform, {}).get(opal_model, 'inherit')

# 사용자 파일 충돌 가드 (W-2 R-T4) — 어댑터의 AUTO-GENERATED 헤더는 frontmatter 뒤(line 9 이후)에 위치하므로 전체 파일을 검사한다
if os.path.isfile(dst):
    with open(dst, 'r', encoding='utf-8') as f:
        head = f.read()
    if 'AUTO-GENERATED by install-mac.sh' not in head:
        sys.stderr.write(f"warn: user-managed file detected (no AUTO-GENERATED header) — skipping: {dst}\n")
        sys.exit(0)

# 출력 frontmatter 직렬화 (3필드만)
def yaml_escape(v):
    if v is None:
        return ''
    s = str(v)
    if any(ch in s for ch in [':', '#', '\n', '\'', '"', '[', ']', '{', '}', '&', '*', '!', '|', '>', '%', '@', '`']):
        return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return s

out_lines = []
out_lines.append(f"name: {yaml_escape(agent_name)}")
if description:
    out_lines.append(f"description: {yaml_escape(description)}")
out_lines.append(f"model: {yaml_escape(model_value)}")

header = (
    f"<!-- AUTO-GENERATED by install-mac.sh from ~/.opal/agents/{agent_name}/AGENT.md. DO NOT EDIT. -->\n"
    f"<!-- SSOT: opal/agents/{agent_name}/AGENT.md (project), ~/.opal/agents/{agent_name}/AGENT.md (deploy). -->\n\n"
)

# 본문(body) 인라인 model 레벨 sub-dispatch 토큰 치환 (032 — F-001 + F-002)
# 앵커 `[,(]\s*` = sub-dispatch 토큰 한정(괄호 내 ", model: <레벨>" 또는 "(model: <레벨>").
#   - 바레-paren:  "(op-dev-plan, model: advanced)" → lead=", " (선행 콤마)
#   - 백틱-skill paren: "`op-dev-plan` (model: advanced)" → lead="(" (여는 괄호)
#   - prose 자기참조("frontmatter의 `model: standard`를 따른다")는 선행이 백틱이라 미매칭 → 오염 차단.
# `\b` 단어 경계로 레벨명 부분 매칭 차단. mapping[platform]는 frontmatter 변환(:559-565)과 동일 dict 재사용.
# 정규식은 frontmatter가 아닌 `body` 문자열에만 적용된다(:504에서 분리 보유 — frontmatter 변환과 독립).
_LEVEL_RE = re.compile(r'(?P<lead>[,(]\s*)model:\s*(?P<lvl>light|standard|advanced)\b')
# cursor inherit 제거 시 백틱-skill paren 잔여 빈 괄호만 정리하기 위한 sentinel (정상 괄호 미오염).
_INHERIT_OPEN = '\x00OPAL_INHERIT_OPEN\x00'

def _sub_body_model(m):
    lvl = m.group('lvl')
    repl = mapping.get(platform, {}).get(lvl)
    if repl is None:
        return m.group(0)            # 매핑 부재(오타·미지원 플랫폼) → 원문 유지 (H-2 방어)
    if repl == 'inherit':
        # F-002 cursor: Agent 도구 model 파라미터 오인 차단을 위해 오버라이드 토큰 제거.
        # ", model: <레벨>" → "" (선행 콤마+공백 제거, 괄호 내용 보존)
        # "(model: <레벨>"  → sentinel (여는 괄호 보존 — 뒤따르는 ")"와 함께 빈 괄호 정리)
        lead = m.group('lead')
        return _INHERIT_OPEN if lead.lstrip().startswith('(') else ''
    return f"{m.group('lead')}model: {repl}"

body = _LEVEL_RE.sub(_sub_body_model, body)
# cursor 빈 괄호 2차 정리: sub-dispatch 유래 "(  )" 만 제거(sentinel-anchored — 정상 괄호 불간섭).
body = re.sub(re.escape(_INHERIT_OPEN) + r'\s*\)', '', body)
body = body.replace(_INHERIT_OPEN, '(')   # 잔여 sentinel 복구(이론상 미도달 — 방어)

os.makedirs(os.path.dirname(dst), exist_ok=True)
with open(dst, 'w', encoding='utf-8') as f:
    f.write('---\n')
    f.write('\n'.join(out_lines) + '\n')
    f.write('---\n\n')
    f.write(header)
    f.write(body)
PYEOF
}

install_claude_agents() {
    local agents_src="$USER_HOME/.opal/agents"
    local agents_dst="$USER_HOME/.claude/agents"

    if [[ ! -d "$agents_src" ]]; then
        warn "~/.opal/agents 부재 — Claude 어댑터 스킵"
        return
    fi
    mkdir -p "$agents_dst"

    local count=0
    for agent_dir in "$agents_src"/*/; do
        [[ -d "$agent_dir" ]] || continue
        local agent_name
        agent_name="$(basename "$agent_dir")"
        emit_platform_agent_adapter "$agent_dir" "$agents_dst/$agent_name.md" "claude"
        ((count++))
    done

    success "Claude Code 어댑터 ${count}개 → $agents_dst/"
}

install_cursor_agents() {
    local agents_src="$USER_HOME/.opal/agents"
    local agents_dst="$USER_HOME/.cursor/agents"

    if [[ ! -d "$agents_src" ]]; then
        warn "~/.opal/agents 부재 — Cursor 어댑터 스킵"
        return
    fi
    mkdir -p "$agents_dst"

    local count=0
    for agent_dir in "$agents_src"/*/; do
        [[ -d "$agent_dir" ]] || continue
        local agent_name
        agent_name="$(basename "$agent_dir")"
        emit_platform_agent_adapter "$agent_dir" "$agents_dst/$agent_name.md" "cursor"
        ((count++))
    done

    success "Cursor 어댑터 ${count}개 → $agents_dst/"
}

install_gemini_agents() {
    local agents_src="$USER_HOME/.opal/agents"
    local agents_dst="$USER_HOME/.gemini/agents"

    if [[ ! -d "$agents_src" ]]; then
        warn "~/.opal/agents 부재 — Gemini 어댑터 스킵"
        return
    fi
    mkdir -p "$agents_dst"

    local count=0
    for agent_dir in "$agents_src"/*/; do
        [[ -d "$agent_dir" ]] || continue
        local agent_name
        agent_name="$(basename "$agent_dir")"
        emit_platform_agent_adapter "$agent_dir" "$agents_dst/$agent_name.md" "gemini"
        ((count++))
    done

    success "Gemini CLI 어댑터 ${count}개 → $agents_dst/"
}

install_codex_agents() {
    local agents_src="$USER_HOME/.opal/agents"
    local agents_dst="$USER_HOME/.codex/agents"

    if [[ ! -d "$agents_src" ]]; then
        warn "~/.opal/agents 부재 — Codex 어댑터 스킵"
        return
    fi
    mkdir -p "$agents_dst"

    # Python 인터프리터 결정: venv 우선 + 시스템 폴백
    local py
    if [[ -x "$USER_HOME/.opal/.venv/bin/python3" ]]; then
        py="$USER_HOME/.opal/.venv/bin/python3"
    else
        py="/usr/bin/python3"
    fi

    local count=0
    for agent_dir in "$agents_src"/*/; do
        [[ -d "$agent_dir" ]] || continue
        local agent_name
        agent_name="$(basename "$agent_dir")"
        local agent_md="$agent_dir/AGENT.md"
        [[ -f "$agent_md" ]] || continue

        local dst_file="$agents_dst/$agent_name.toml"

        "$py" - "$agent_md" "$dst_file" <<'PYEOF'
import os, re, sys

src, dst = sys.argv[1], sys.argv[2]

# Codex sub-agent 모델 매핑 (opal-model-mapping.md §2 Codex 컬럼과 동기)
codex_model_map = {
    'light': 'gpt-5.4-mini',
    'standard': 'gpt-5.4',
    'advanced': 'gpt-5.5',
}

def _flatten_description(s):
    if not s:
        return ''
    return re.sub(r'\s+', ' ', s).strip()

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

with open(src, 'r', encoding='utf-8') as f:
    text = f.read()

m = re.match(r'^---\n(.*?)\n---\n?(.*)$', text, re.DOTALL)
if not m:
    sys.exit(0)

fm_raw = m.group(1)
body = m.group(2)

if HAS_YAML:
    try:
        fm = yaml.safe_load(fm_raw) or {}
    except Exception:
        HAS_YAML = False

if not HAS_YAML:
    fm = {}
    for line in fm_raw.split('\n'):
        kv = re.match(r'^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$', line)
        if kv:
            fm[kv.group(1)] = kv.group(2).strip().strip('"\'')

agent_name = fm.get('name', '').strip()
if not agent_name:
    agent_name = os.path.basename(os.path.dirname(src))

description = _flatten_description(fm.get('description') or '')
opal_model = fm.get('model', 'standard')
model_value = codex_model_map.get(opal_model, 'gpt-5.5')

# 사용자 파일 충돌 가드 (AUTO-GENERATED 헤더 없으면 스킵)
if os.path.isfile(dst):
    with open(dst, 'r', encoding='utf-8') as f:
        head = f.read()
    if 'AUTO-GENERATED by install-mac.sh' not in head:
        sys.stderr.write(f"warn: user-managed file detected (no AUTO-GENERATED header) — skipping: {dst}\n")
        sys.exit(0)

def toml_escape(s):
    r"""TOML triple-quoted basic string 내부 escape: \ → \\, " → \" """
    return s.replace('\\', '\\\\').replace('"', '\\"')

os.makedirs(os.path.dirname(dst), exist_ok=True)
with open(dst, 'w', encoding='utf-8') as f:
    f.write(f'# AUTO-GENERATED by install-mac.sh from ~/.opal/agents/{agent_name}/AGENT.md. DO NOT EDIT.\n')
    f.write(f'# SSOT: opal/agents/{agent_name}/AGENT.md (project), ~/.opal/agents/{agent_name}/AGENT.md (deploy).\n\n')
    f.write(f'name = "{toml_escape(agent_name)}"\n')
    if description:
        f.write(f'description = "{toml_escape(description)}"\n')
    f.write(f'model = "{model_value}"\n')
    f.write(f'developer_instructions = """\n{toml_escape(body)}\n"""\n')
PYEOF

        ((count++))
    done

    success "Codex 어댑터 ${count}개 → $agents_dst/"
}

# Codex config.toml [agents] 글로벌 설정 멱등 작성
# 키/기본값 출처: https://developers.openai.com/codex/config-reference (2026-06-17 확인)
#   max_threads=6, max_depth=1, job_max_runtime_seconds=1800
# 멱등성: [agents] 헤더가 이미 존재하면 중복 추가 생략.
# 기존 [mcp_servers] 등 다른 블록은 훼손하지 않는다.
# 사용: install_codex_config
install_codex_config() {
    local config_file="$USER_HOME/.codex/config.toml"
    mkdir -p "$(dirname "$config_file")"

    # 멱등성: [agents] 헤더가 이미 있으면 스킵
    if [[ -f "$config_file" ]] && grep -q '^\[agents\]' "$config_file"; then
        info "Codex config.toml — [agents] 블록 이미 존재, 스킵"
        return
    fi

    # [agents] 블록 append (기존 블록 보존)
    {
        echo ""
        echo "# AUTO-GENERATED by install-mac.sh — OPAL Codex 글로벌 에이전트 한계치"
        echo "# 출처: https://developers.openai.com/codex/config-reference"
        echo "[agents]"
        echo "max_threads = 6"
        echo "max_depth = 1"
        echo "job_max_runtime_seconds = 1800"
    } >> "$config_file"

    success "Codex config.toml — [agents] 블록 추가 → $config_file"
}

# ─── OPAL bin PATH 등록 (D 영역) ────────────────────────

# ~/.opal/bin/opal-cli symlink 생성 후 셸 rc 파일에 PATH 등록
# 사용: install_opal_bin
install_opal_bin() {
    local bin_dir="$USER_HOME/.opal/bin"
    local cli_target="$USER_HOME/.opal/tools/opal-cli/run.sh"

    if [[ ! -f "$cli_target" ]]; then
        warn "opal-cli/run.sh 부재 — bin 생성 스킵 (Step 3 이후 동작)"
        return
    fi
    chmod +x "$cli_target"
    mkdir -p "$bin_dir"
    ln -sfn "$cli_target" "$bin_dir/opal-cli"
    success "opal-cli 심볼릭 링크 → $bin_dir/opal-cli"

    register_path_in_shell_rc "$bin_dir"
    register_test_tools_global_in_shell_rc

    # 자세한 PATH 사용 안내는 OPAL_VERBOSE=1 때만. quiet 모드는 main()의 마무리 echo에 통합됨.
    if [[ "$OPAL_VERBOSE" == "1" ]]; then
        echo ""
        info "opal-cli 사용 방법:"
        echo -e "    ${BOLD}1) 현재 셸에 즉시 적용${NC} — 다음 중 하나 실행:"
        echo    "         source ~/.zshrc      (zsh 사용자)"
        echo    "         source ~/.bashrc     (bash 사용자)"
        echo    "         exec \$SHELL          (현재 셸 재시작)"
        echo -e "    ${BOLD}2) 또는 새 터미널 열기${NC} — PATH 자동 적용"
        echo ""
        echo -e "    ${BOLD}검증:${NC}"
        echo    "         opal-cli --version    # 버전 출력"
        echo    "         opal-cli doctor       # 환경 진단 (4섹션)"
        echo ""
        echo -e "    ${BOLD}PATH 미적용 시 절대 경로 호출도 가능:${NC}"
        echo    "         ~/.opal/bin/opal-cli doctor"
        echo ""
    fi
}

# 셸 rc 파일(zsh/bash/profile)에 OPAL PATH 마커 1회만 추가 (idempotent)
# fish 사용자는 별도 안내
# 사용: register_path_in_shell_rc <bin_dir>
register_path_in_shell_rc() {
    local bin_dir="$1"
    local marker="# === OPAL PATH ==="
    local marker_end="# === OPAL PATH END ==="
    local rc_files=("$USER_HOME/.zshrc" "$USER_HOME/.bashrc" "$USER_HOME/.profile")
    local export_line='export PATH="$HOME/.opal/bin:$PATH"'

    for rc in "${rc_files[@]}"; do
        [[ -f "$rc" ]] || continue
        if grep -qF "$marker" "$rc"; then
            success "PATH 이미 등록됨: $rc"
            continue
        fi
        printf '\n%s\n%s\n%s\n' "$marker" "$export_line" "$marker_end" >> "$rc"
        success "PATH 등록 → $rc"
    done

    # fish는 config.fish 구조가 달라 별도 안내
    if command -v fish &>/dev/null; then
        info "fish 사용자: ~/.config/fish/config.fish 에 다음 줄을 추가하세요:"
        info "  set -gx PATH \$HOME/.opal/bin \$PATH"
    fi
}

# 셸 rc 파일에 OPAL_TEST_TOOLS_GLOBAL 환경변수를 1회만 등록 (idempotent)
# 기존 register_path_in_shell_rc 멱등 마커 패턴을 동일하게 적용.
register_test_tools_global_in_shell_rc() {
    local marker="# === OPAL TEST_TOOLS_GLOBAL ==="
    local marker_end="# === OPAL TEST_TOOLS_GLOBAL END ==="
    local rc_files=("$USER_HOME/.zshrc" "$USER_HOME/.bashrc" "$USER_HOME/.profile")
    local export_line='export OPAL_TEST_TOOLS_GLOBAL="$HOME/.opal/templates/test-tools.yaml"'

    for rc in "${rc_files[@]}"; do
        [[ -f "$rc" ]] || continue
        if grep -qF "$marker" "$rc"; then
            success "OPAL_TEST_TOOLS_GLOBAL 이미 등록됨: $rc"
            continue
        fi
        printf '\n%s\n%s\n%s\n' "$marker" "$export_line" "$marker_end" >> "$rc"
        success "OPAL_TEST_TOOLS_GLOBAL 등록 → $rc"
    done
}

# ─── OPAL Setting (create-if-absent) ────────────────────

install_opal_setting() {
    local src="$FRAMEWORK_ROOT/opal/core/setting.default.json"
    local dst="$USER_HOME/.opal/setting.json"
    if [[ -f "$dst" ]]; then
        # 파일이 존재하는 경우: models 키가 없으면 scaffold 병합 (멱등) — H-1
        python3 - "$src" "$dst" <<'PYEOF' || warn "setting.json models 병합 실패 — 기존 파일 유지"
import json, sys

src_path, dst_path = sys.argv[1], sys.argv[2]

try:
    with open(src_path, 'r', encoding='utf-8') as f:
        default = json.load(f)
    with open(dst_path, 'r', encoding='utf-8') as f:
        existing = json.load(f)
except Exception as e:
    sys.stderr.write(f"warn: setting.json 로드 실패 — {e}\n")
    sys.exit(1)

if 'models' in existing:
    sys.stderr.write("info: setting.json에 models 키 존재 — 무변 (멱등)\n")
    sys.exit(0)

existing['models'] = default['models']

with open(dst_path, 'w', encoding='utf-8') as f:
    json.dump(existing, f, ensure_ascii=False, indent=2)
    f.write('\n')

sys.stderr.write("info: setting.json에 models scaffold 병합 완료\n")
PYEOF
        return 0
    fi
    cp "$src" "$dst"
    success "OPAL setting.json (기본값) → $dst"
}

# ─── record_installed_version ────────────────────────────────────────────────
# ~/.opal/VERSION 기록 함수 (테스트 용이성 — 단위 테스트에서 직접 호출 가능).
# 우선순위:
#   1) FRAMEWORK_ROOT/VERSION 각인값 (tarball 설치 — 최우선, placeholder면 스킵)
#   2) $OPAL_VERSION (one-liner installer가 전달)
#   3) git describe (개발자 git clone 경로, .git 존재 시)
#   4) "main" 폴백
# bash 3.2 호환: case 패턴 사용, 연관배열 미사용.
record_installed_version() {
    local opal_home="${1:-${OPAL_HOME:-$HOME/.opal}}"
    local framework_root="${2:-${FRAMEWORK_ROOT:-}}"
    local installed_version="${OPAL_VERSION:-}"
    local _stamped=""

    # 1) 추출된 소스 루트의 각인 VERSION (tarball 설치 경로 — 최우선)
    if [[ -n "$framework_root" && -f "$framework_root/VERSION" ]]; then
        _stamped="$(tr -d '[:space:]' < "$framework_root/VERSION" 2>/dev/null || true)"
        case "$_stamped" in
            ''|*'$Format:'*) : ;;              # 미치환/부재 → 다음 폴백
            *) installed_version="$_stamped" ;; # 각인값 채택
        esac
    fi

    # 2) $OPAL_VERSION (one-liner installer가 전달; 위에서 미채택 시)
    # installed_version="${OPAL_VERSION:-}" 로 이미 초기화됨

    # 3) git describe (개발자 git clone 경로)
    if [[ -z "$installed_version" ]] && command -v git &>/dev/null && [[ -n "$framework_root" ]] && [[ -d "$framework_root/.git" ]]; then
        installed_version="$(cd "$framework_root" && git describe --tags --always 2>/dev/null || echo "main")"
    fi

    # 4) main 폴백
    installed_version="${installed_version:-main}"

    echo "$installed_version" > "$opal_home/VERSION"
    success "버전 기록 → $opal_home/VERSION ($installed_version)"
}

# ─── OPAL Installer ─────────────────────────────────────

install_opal() {
    echo ""
    info "OPAL AI 프레임워크 설치..."
    local opal_dir="$FRAMEWORK_ROOT/opal"
    local opal_home="$USER_HOME/.opal"

    mkdir -p "$opal_home"

    # OPAL_HOME 가드 — 비표준 경로 거부 (GC-010, R-8)
    local opal_home_canon
    opal_home_canon="$(cd "$opal_home" 2>/dev/null && pwd -P || echo "$opal_home")"
    local default_opal_canon
    default_opal_canon="$(cd "$USER_HOME/.opal" 2>/dev/null && pwd -P || echo "$USER_HOME/.opal")"
    if [[ "$opal_home_canon" != "$default_opal_canon" ]] && [[ "${OPAL_HOME_OVERRIDE:-}" != "1" ]]; then
        error "비표준 OPAL_HOME 거부: $opal_home (예상: $USER_HOME/.opal). 옵트인: OPAL_HOME_OVERRIDE=1 명시"
        return 1
    fi

    # ── 프레임워크 디렉토리 클린 삭제 (사용자 데이터 보존) ──
    info "기존 프레임워크 파일 정리 (사용자 데이터 보존)..."
    # 사용자 데이터 보존: ~/.opal/community-skills/는 install이 절대 건드리지 않음 (TASK 142 D-4)
    local clean_dirs=("skills" "agents" "references" "templates" "tools" "dashboard-server")
    for dir in "${clean_dirs[@]}"; do
        if [[ -d "$opal_home/$dir" ]]; then
            rm -rf "$opal_home/$dir"
            success "삭제: $opal_home/$dir/"
        fi
    done
    # 보존: identity.md, AGENT.md, projects/ (사용자 데이터)

    # ── OPAL 코어 ──
    strip_deploy_md "$opal_dir/core/AGENT.md" "$opal_home/AGENT.md"
    success "OPAL AGENT.md → $opal_home/AGENT.md"

    # ── OPAL 헌법 (행동 원칙 SSOT, always-on) ──
    strip_deploy_md "$opal_dir/core/PRINCIPLES.md" "$opal_home/PRINCIPLES.md"
    success "OPAL PRINCIPLES.md (헌법) → $opal_home/PRINCIPLES.md"

    # ── OPAL 기본 설정 (create-if-absent — 사용자 토글 보존) ──
    install_opal_setting

    # ── 독립 스킬 (skills/ → ~/.opal/skills/) ──
    local fw_skill_count
    fw_skill_count=$(find "$FRAMEWORK_ROOT/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
    install_dir "$FRAMEWORK_ROOT/skills" "$opal_home/skills" "독립 스킬 (${fw_skill_count}개)"

    # ── OPAL 스킬 (opal/skills/ → ~/.opal/skills/) ──
    local opal_skill_count
    opal_skill_count=$(find "$opal_dir/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
    for skill_dir in "$opal_dir/skills"/*/; do
        if [[ -d "$skill_dir" ]]; then
            local skill_name
            skill_name="$(basename "$skill_dir")"
            install_dir "$skill_dir" "$opal_home/skills/$skill_name" "OPAL 스킬: $skill_name"
        fi
    done
    strip_deploy_md_recursive "$opal_home/skills"
    success "OPAL 스킬 ${opal_skill_count}개 → $opal_home/skills/"

    # ── 에이전트 (opal/agents/ + agents/ → ~/.opal/agents/) ──
    local agent_count=0
    mkdir -p "$opal_home/agents"

    # OPAL 전용 에이전트 (opal/agents/)
    if [[ -d "$opal_dir/agents" ]]; then
        for agent_dir in "$opal_dir/agents"/*/; do
            if [[ -d "$agent_dir" ]]; then
                local agent_name
                agent_name="$(basename "$agent_dir")"
                install_dir "$agent_dir" "$opal_home/agents/$agent_name" "에이전트: $agent_name"
                ((agent_count++))
            fi
        done
    fi

    # 범용 에이전트 (agents/ — OPAL 무관)
    for agent_dir in "$FRAMEWORK_ROOT/agents"/*/; do
        if [[ -d "$agent_dir" ]]; then
            local agent_name
            agent_name="$(basename "$agent_dir")"
            # 레거시 claude 디렉토리는 스킵
            [[ "$agent_name" == "claude" ]] && continue
            [[ "$agent_name" == "cursor" ]] && continue
            [[ "$agent_name" == "antigravity" ]] && continue
            install_dir "$agent_dir" "$opal_home/agents/$agent_name" "에이전트: $agent_name"
            ((agent_count++))
        fi
    done
    strip_deploy_md_recursive "$opal_home/agents"
    success "에이전트 ${agent_count}개 → $opal_home/agents/"

    # ── 템플릿 ──
    install_dir "$opal_dir/templates" "$opal_home/templates" "OPAL templates"

    cp "$opal_dir/core/identity-template.md" "$opal_home/templates/identity-template.md"
    success "identity-template.md → $opal_home/templates/"

    # ── 도구 (opal/tools/ → ~/.opal/tools/) ──
    if [[ -d "$opal_dir/tools" ]]; then
        install_dir "$opal_dir/tools" "$opal_home/tools" "OPAL 도구"
        strip_deploy_md_recursive "$opal_home/tools"

        # ── playwright-tool 실행 권한 ──
        local playwright_run="$opal_home/tools/playwright-tool/run.sh"
        if [[ -f "$playwright_run" ]]; then
            chmod +x "$playwright_run"
            success "playwright-tool run.sh 실행 권한 설정"
        fi

        # ── state-tool 실행 권한 (TASK F-20 / PLAN §1.5 M-41 / §1 D-16 / §3 Step 15) ──
        local state_run="$opal_home/tools/state-tool/run.sh"
        if [[ -f "$state_run" ]]; then
            chmod +x "$state_run"
            success "state-tool run.sh 실행 권한 설정"
        fi

        # ── brain-tool 실행 권한 (015 / PLAN §2.0 결정8 / §3 Step 9) ──
        local brain_run="$opal_home/tools/brain-tool/run.sh"
        if [[ -f "$brain_run" ]]; then
            chmod +x "$brain_run"
            success "brain-tool run.sh 실행 권한 설정"
        fi

        # ── cmux-tool 실행 권한 ──
        local cmux_run="$opal_home/tools/cmux-tool/run.sh"
        if [[ -f "$cmux_run" ]]; then
            chmod +x "$cmux_run"
            success "cmux-tool run.sh 실행 권한 설정"
        fi

        # ── cmux-tool lib/ 및 examples/ 실행 권한 ──
        local cmux_lib_dir="$opal_home/tools/cmux-tool/lib"
        local cmux_examples_dir="$opal_home/tools/cmux-tool/examples"
        for sh_file in "$cmux_lib_dir"/*.sh "$cmux_examples_dir"/*.sh; do
            [[ -f "$sh_file" ]] && chmod +x "$sh_file"
        done
        if [[ -d "$cmux_lib_dir" || -d "$cmux_examples_dir" ]]; then
            success "cmux-tool lib/, examples/ 실행 권한 설정"
        fi

        # ── tool-scan 실행 권한 (044) ──
        local tool_scan_run="$opal_home/tools/tool-scan/run.sh"
        if [[ -f "$tool_scan_run" ]]; then
            chmod +x "$tool_scan_run"
            success "tool-scan run.sh 실행 권한 설정"
        fi

        # ── memory-tool 실행 권한 (045) ──
        local memory_run="$opal_home/tools/memory-tool/run.sh"
        if [[ -f "$memory_run" ]]; then
            chmod +x "$memory_run"
            success "memory-tool run.sh 실행 권한 설정"
        fi

        # cmux 의존성 안내 (정보성 — 설치 강제 없음, silent fallback 정책)
        if ! command -v cmux &>/dev/null; then
            info "cmux 미감지 — cmux-tool 사용 시 https://cmux.com/ 또는 https://github.com/manaflow-ai/cmux 에서 설치 필요"
        fi

        # Node.js 환경 체크
        if command -v node &>/dev/null; then
            local node_check
            node_check="$(node "$opal_home/tools/check-env.js" 2>/dev/null)" || true
            if node -e "const d=$node_check; process.exit(d.node?0:1)" 2>/dev/null; then
                success "Node.js 환경 확인: $(node --version)"
            else
                warn "Node.js 버전이 낮습니다. v18 이상 권장"
            fi
        else
            warn "Node.js가 설치되어 있지 않습니다. opal/tools/ 기능이 제한됩니다"
            info "  설치: https://nodejs.org/ 또는 brew install node"
        fi
    fi

    # ── Python venv ──
    install_opal_venv

    # ── 참조 레지스트리 ──
    install_opal_references

    # 커뮤니티 스킬은 번들로 배포하지 않음. 사용자가 //skill-manager로 검색·설치 (TASK 142)

    # ── Claude Code hooks ──
    local hooks_src="$FRAMEWORK_ROOT/opal/core/hooks/claude-hooks.json"
    if [[ -f "$hooks_src" ]] && [[ -x /usr/bin/python3 ]]; then
        local settings="$USER_HOME/.claude/settings.json"
        mkdir -p "$(dirname "$settings")"
        merge_hooks_config "$settings" "$hooks_src"
        success "Claude Code hooks → $settings"
    fi

    # ── 부트스트래퍼 설치 ──
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
        "$USER_HOME/.gemini/GEMINI.md" "Gemini"

    install_gemini_hardening "$opal_dir/bootstrapper/gemini-hardening.md" \
        "$USER_HOME/.gemini/GEMINI.md" "Gemini"

    install_opal_section "$opal_dir/bootstrapper/codex-bootstrap.md" \
        "$USER_HOME/.codex/AGENTS.md" "Codex"

    # ── Claude Code ~/.opal 읽기 권한 ──
    install_claude_permissions

    # ── 플랫폼 sub-agent 어댑터 ──
    install_claude_agents
    install_cursor_agents
    install_gemini_agents
    install_codex_agents
    install_codex_config
    # Antigravity는 custom sub-agent 미지원
    # 출처: https://discuss.ai.google.dev/t/antigravity-sub-agents/114381

    # ── Gemini CLI 외부 경로 접근 설정 ──
    install_gemini_config

    # ── opal-cli bin symlink + PATH 등록 ──
    install_opal_bin

    # ── OPAL Console 대시보드 배포 + 서버 자동 기동 ──
    install_dashboard
    console_autostart

    # ── git 한글 경로 표시 (core.quotepath=false) ──
    # OPAL 태스크 폴더명은 한글/혼용을 허용한다(op-task SKILL.md §저장 경로).
    # git 기본값(quotepath=true)은 한글 경로를 \355.. octal 이스케이프로 표시하므로,
    # 사용자 git 전역 설정에 quotepath=false를 적용해 status/log에서 한글이 그대로 보이도록 한다.
    if command -v git &>/dev/null; then
        if git config --global core.quotepath false 2>/dev/null; then
            success "git core.quotepath=false 설정 (한글 경로 표시)"
        else
            info "git core.quotepath 설정 실패 — 한글 경로가 octal로 표시될 수 있습니다"
        fi
    fi

    # ── 설치 버전 기록 (~/.opal/VERSION) ──
    # 우선순위: FRAMEWORK_ROOT/VERSION 각인값(tarball 최우선) → $OPAL_VERSION → git describe → "main" 폴백
    # opal-cli update가 이 파일을 읽어 리모트 latest tag와 비교, 동일하면 갱신 스킵.
    # record_installed_version 함수 분리 — 단위 테스트에서 직접 호출 가능 (048 D-피2).
    record_installed_version "$opal_home" "${FRAMEWORK_ROOT:-}"

    # ── 레거시 정리 안내 ──
    # print_cleanup_notice

    echo ""
    info "커뮤니티 스킬은 //skill-manager로 검색·설치하세요 (예: //skill-manager pdf)"
}

install_opal_venv() {
    local venv_dir="$USER_HOME/.opal/.venv"
    local req_src="$FRAMEWORK_ROOT/opal/tools/requirements.txt"

    if [[ ! -f "$req_src" ]]; then
        warn "opal/tools/requirements.txt 없음 — Python venv 스킵"
        return
    fi

    echo ""
    info "Python 가상환경 설정..."

    if [[ ! -d "$venv_dir" ]]; then
        python3 -m venv "$venv_dir"
        success "venv 생성: $venv_dir"
    else
        success "venv 기존 사용: $venv_dir"
    fi

    # --no-cache-dir: pip HTTP 캐시 deserialization 경고(다양한 pip 버전 간 캐시 포맷 비호환) 차단
    "$venv_dir/bin/pip" install --quiet --no-cache-dir --upgrade pip
    "$venv_dir/bin/pip" install --quiet --no-cache-dir -r "$req_src"
    success "Python 패키지 설치 완료 (requirements.txt)"

    # playwright 브라우저 확인 및 설치
    # Playwright 캐시 경로: macOS ~/Library/Caches, Linux ~/.cache (XDG 표준)
    # 출처: https://playwright.dev/docs/browsers#managing-browser-binaries
    local pw_cache
    if [[ "$(uname -s)" == "Linux" ]]; then
        pw_cache="$USER_HOME/.cache/ms-playwright"
    else
        pw_cache="$USER_HOME/Library/Caches/ms-playwright"
    fi
    local missing_browsers=()

    if [[ -d "$pw_cache" ]] && [[ -n "$(ls -A "$pw_cache" 2>/dev/null)" ]]; then
        success "Playwright 브라우저 이미 설치됨 (스킵)"
        echo -e "  ${CYAN}설치된 브라우저:${NC} $(ls "$pw_cache" | tr '\n' ' ')"

        ls "$pw_cache" | grep -q "^chromium"  || missing_browsers+=("chromium")
        ls "$pw_cache" | grep -q "^firefox"   || missing_browsers+=("firefox")
        ls "$pw_cache" | grep -q "^webkit"    || missing_browsers+=("webkit")
    else
        info "Playwright 브라우저 설치 (기본: Chromium)..."
        if "$venv_dir/bin/playwright" install chromium 2>/dev/null; then
            success "Chromium 설치 완료"
        else
            warn "Chromium 설치 실패 — 수동 실행: ~/.opal/.venv/bin/playwright install chromium"
        fi
        missing_browsers+=("firefox" "webkit")
    fi

    if [[ ${#missing_browsers[@]} -gt 0 ]]; then
        echo ""
        echo -e "  ${CYAN}미설치 브라우저 설치 명령어:${NC}"
        for browser in "${missing_browsers[@]}"; do
            echo "    ~/.opal/.venv/bin/playwright install $browser"
        done
    fi
    echo ""
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
    # 배포된 모든 .md 파일에서 변경이력 섹션 제거
    strip_deploy_md_recursive "$ref_dst"
    success "참조 레지스트리 → $ref_dst/"
}

# ─── OPAL Console Dashboard Installer ───────────────────

install_dashboard() {
    local src="$FRAMEWORK_ROOT/dashboard"
    local dst="$USER_HOME/.opal/dashboard-server"

    # dashboard/ 소스가 없으면 graceful skip (미빌드 환경 대응)
    if [[ ! -d "$src" ]]; then
        info "dashboard/ 소스 미존재 — OPAL Console 설치 스킵"
        return
    fi

    echo ""
    info "OPAL Console 설치 중..."

    # ── FE 빌드 (Node 필요) ──
    if command -v node &>/dev/null && [[ -d "$src/frontend" ]]; then
        info "Node $(node --version) 발견 — FE 빌드 시작..."
        if (cd "$src/frontend" && npm install --silent && npm run build); then
            # dist/ → ~/.opal/dashboard-server/dist/
            install_dir "$src/frontend/dist" "$dst/dist" "Console FE dist"
        else
            warn "FE 빌드 실패 — dashboard/frontend npm build 오류. Console FE 배포 스킵."
        fi
    else
        warn "Node 미설치 또는 dashboard/frontend 없음 — FE 빌드 스킵 (node 설치 후 재실행 권장)"
    fi

    # ── BE 복사 (패키지 구조 유지: dashboard/backend/) ──
    # main.py의 'from dashboard.backend.routers import ...' 절대 import가 동작하려면
    # --app-dir ~/.opal/dashboard-server 기준으로 dashboard/ 패키지가 존재해야 함.
    # → BE를 dashboard/backend/로 복사하고 dashboard/__init__.py 생성.
    if [[ -d "$src/backend" ]]; then
        install_dir "$src/backend" "$dst/dashboard/backend" "Console BE"
        # dashboard 패키지 루트 __init__.py 생성 (없으면)
        touch "$dst/dashboard/__init__.py"
        success "Console BE 패키지 구조 생성 → $dst/dashboard/__init__.py"
    else
        warn "dashboard/backend 없음 — BE 배포 스킵"
    fi

    echo ""
    info "OPAL Console 설치 완료 → $dst"
    info "기동: opal-cli console start"
}

# ─── OPAL Console 자동 재시작 ────────────────────────────
#
# install_dashboard 후 호출. 기존 데몬을 종료하고 신규 기동한다.
# opal-cli 가 존재하면 console stop/start 위임, 미존재 시 uvicorn 직접 폴백.
# 기동 후 /health 확인 + 접속 안내 출력.

console_autostart() {
    local opal_home="$USER_HOME/.opal"
    local venv_uvicorn="$opal_home/.venv/bin/uvicorn"
    local dashboard_server="$opal_home/dashboard-server"
    local dashboard_pkg="$dashboard_server/dashboard/backend"
    local opal_cli="$opal_home/bin/opal-cli"
    local host="127.0.0.1"
    local port="7823"
    local health_url="http://${host}:${port}/health"

    echo ""
    step "OPAL Console 자동 재시작 중..."

    # ── 전제 점검 ──
    if [[ ! -d "$dashboard_pkg" ]]; then
        warn "dashboard-server/dashboard/backend 없음 — 서버 기동 스킵"
        info "install_dashboard 가 정상 완료되었는지 확인하세요."
        return
    fi

    if [[ ! -f "$venv_uvicorn" ]]; then
        warn "uvicorn 미설치: $venv_uvicorn"
        info "메뉴 [4] Python 패키지 업데이트 후 재시도하세요."
        return
    fi

    # ── 기존 데몬 종료 ──
    # opal-cli console stop 우선, 미존재 시 pkill 폴백
    if [[ -x "$opal_cli" ]]; then
        "$opal_cli" console stop 2>/dev/null || true
    else
        pkill -f "dashboard.backend.main:app" 2>/dev/null || true
    fi
    # 프로세스 종료 대기 (최대 3초)
    local waited=0
    while curl -s --max-time 1 "$health_url" >/dev/null 2>&1; do
        sleep 1
        ((waited++))
        [[ $waited -ge 3 ]] && break
    done

    # ── 신규 기동 ──
    if [[ -x "$opal_cli" ]]; then
        # opal-cli console start 위임
        "$opal_cli" console start 2>/dev/null &
    else
        # 직접 uvicorn 기동 (opal-cli 미배포 폴백)
        nohup "$venv_uvicorn" \
            --app-dir "$dashboard_server" \
            dashboard.backend.main:app \
            --host "$host" \
            --port "$port" \
            >/tmp/opal-console.log 2>&1 &
        local pid=$!
        success "OPAL Console 기동됨 (PID: $pid, 로그: /tmp/opal-console.log)"
    fi

    # ── /health 확인 (최대 10초 대기) ──
    local ok=0
    for i in $(seq 1 10); do
        sleep 1
        if curl -s --max-time 2 "$health_url" >/dev/null 2>&1; then
            ok=1
            break
        fi
    done

    if [[ $ok -eq 1 ]]; then
        local health_response
        health_response="$(curl -s --max-time 3 "$health_url" 2>/dev/null)"
        echo ""
        echo -e "${GREEN}✓${NC} OPAL Console 기동 완료"
        echo -e "  ${CYAN}접속:${NC} http://${host}:${port}"
        echo -e "  ${CYAN}/health:${NC} $health_response"
    else
        warn "OPAL Console /health 응답 없음 (10초 초과)"
        info "로그 확인: cat /tmp/opal-console.log"
        info "수동 기동: opal-cli console start"
    fi
}

# ─── Legacy Cleanup Notice ───────────────────────────────

print_cleanup_notice() {
    local legacy_paths=()

    [[ -d "$USER_HOME/.claude/skills" ]] && legacy_paths+=("~/.claude/skills/")
    [[ -d "$USER_HOME/.claude/agents" ]] && legacy_paths+=("~/.claude/agents/")
    [[ -d "$USER_HOME/.cursor/skills" ]] && legacy_paths+=("~/.cursor/skills/")
    [[ -d "$USER_HOME/.cursor/agents" ]] && legacy_paths+=("~/.cursor/agents/")
    [[ -d "$USER_HOME/.gemini/antigravity/skills" ]] && legacy_paths+=("~/.gemini/antigravity/skills/")
    [[ -d "$USER_HOME/.gemini/agents" ]] && legacy_paths+=("~/.gemini/agents/")

    if [[ ${#legacy_paths[@]} -gt 0 ]]; then
        echo ""
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}  레거시 배포 경로 감지${NC}"
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo "  스킬/에이전트가 이제 ~/.opal/ 단일 경로로 배포됩니다."
        echo "  아래 레거시 경로는 더 이상 사용되지 않으므로 수동 삭제를 권장합니다:"
        echo ""
        for path in "${legacy_paths[@]}"; do
            echo -e "    ${RED}rm -rf $path${NC}"
        done
        echo ""
        echo "  * MCP 설정 파일(mcp.json, settings.json)과 부트스트래퍼는 그대로 유지하세요."
        echo ""
    fi
}

# ─── MCP Installer ───────────────────────────────────────

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

    # command 화이트리스트 검증 (GC-002, R-4)
    local cmd_basename
    cmd_basename="$(basename "$cmd")"
    case "$cmd_basename" in
        npx|npm|node|python3|python) ;;
        *) error "MCP command '$cmd' 화이트리스트 미통과 — npx/npm/node/python3만 허용"; return 1 ;;
    esac

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

    if [[ ! -x /usr/bin/python3 ]]; then
        warn "python3이 없어 MCP 설정을 자동 머지할 수 없습니다"
        info "수동 설정: https://modelcontextprotocol.io/quickstart"
        return
    fi

    # fork repo banner — OPAL_REPO != ceo4ever/opal 시 경고 (GC-002, R-4)
    local opal_repo="${OPAL_REPO:-ceo4ever/opal}"
    if [[ "$opal_repo" != "ceo4ever/opal" ]]; then
        echo ""
        echo "════════════════════════════════════════════════════════"
        echo "  [FORK INSTALL] OPAL_REPO=$opal_repo"
        echo "  이 설치본은 OPAL 공식 저장소(ceo4ever/opal)가 아닙니다."
        echo "  MCP 서버 등록 항목을 직접 검토하세요."
        echo "════════════════════════════════════════════════════════"
        echo ""
        # 비대화형 모드: OPAL_ALLOW_FORK=1 옵트인 없으면 거부
        if [[ "${OPAL_AUTO_INSTALL:-0}" == "1" ]] || [[ ! -t 0 ]]; then
            if [[ "${OPAL_ALLOW_FORK:-}" != "1" ]]; then
                error "fork repo 비대화형 설치 거부. 옵트인: OPAL_ALLOW_FORK=1 명시"
                return 1
            fi
        else
            read -r -p "계속하시겠습니까? [y/N] " fork_confirm
            if [[ "$fork_confirm" != "y" && "$fork_confirm" != "Y" ]]; then
                info "MCP 설치를 건너뜁니다."
                return 0
            fi
        fi
    fi

    # playwright cache 디렉토리 사전 생성 (args의 ~/.opal/cache/playwright-mcp 경로 보장)
    mkdir -p "$USER_HOME/.opal/cache/playwright-mcp"
    chmod 700 "$USER_HOME/.opal/cache"

    local count=0
    for mcp_file in "$mcp_src"/*.json; do
        [[ -f "$mcp_file" ]] || continue

        local name config install_type platforms command args_json
        name=$(/usr/bin/python3 -c "import json; print(json.load(open('$mcp_file'))['name'])")
        config=$(/usr/bin/python3 -c "import json; print(json.dumps(json.load(open('$mcp_file'))['config']))")
        install_type=$(/usr/bin/python3 -c "import json; print(json.load(open('$mcp_file'))['install_type'])")
        platforms=$(/usr/bin/python3 -c "import json; print(' '.join(json.load(open('$mcp_file'))['platforms']))")
        command=$(/usr/bin/python3 -c "import json; print(json.load(open('$mcp_file'))['config'].get('command',''))")
        args_json=$(/usr/bin/python3 -c "import json; print('\n'.join(json.load(open('$mcp_file'))['config'].get('args',[])))")

        if [[ "$install_type" != "config_merge" ]]; then
            info "  $name: $install_type 타입 — 수동 설치 필요"
            continue
        fi

        # command 화이트리스트 검증 (GC-002, R-4)
        local cmd_basename
        cmd_basename="$(basename "$command")"
        case "$cmd_basename" in
            npx|npm|node|python3|python) ;;
            *)
                warn "$name: command '$command' 화이트리스트 미통과 — 건너뜀"
                continue
                ;;
        esac

        # args_json → args_array 변환
        local args_array=()
        while IFS= read -r arg; do
            # ~/... → ${HOME}/... expand (MCP 클라이언트 ~ 미전개 방어)
            [[ -n "$arg" ]] && args_array+=("${arg/#\~/$USER_HOME}")
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
                codex)
                    local bin
                    if bin=$(find_cli_bin codex "$USER_HOME/.nvm/versions/node/*/bin/codex" "/opt/homebrew/bin/codex" "/usr/local/bin/codex"); then
                        if install_mcp_cli "$bin" "" "$name" "$command" "${args_array[@]}"; then
                            installed_platforms+=("codex")
                        fi
                    else
                        warn "codex CLI 없음 — 수동 등록: codex mcp add $name -- $command ${args_array[*]}"
                    fi
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

    local opal_home="$USER_HOME/.opal"

    [[ -d "$opal_home/skills" ]] && \
        echo "    ~/.opal/skills/              $(count_items "$opal_home/skills" "*") skills"
    [[ -d "$opal_home/agents" ]] && \
        echo "    ~/.opal/agents/              $(count_items "$opal_home/agents" "*") agents"
    [[ -d "$opal_home/community-skills" ]] && \
        echo "    ~/.opal/community-skills/    커뮤니티 스킬"
    [[ -d "$opal_home/references" ]] && \
        echo "    ~/.opal/references/          참조 레지스트리"
    [[ -d "$opal_home/tools" ]] && \
        echo "    ~/.opal/tools/               파싱 도구 (Node.js)"
    [[ -d "$opal_home/.venv" ]] && \
        echo "    ~/.opal/.venv/                Python 가상환경"
    [[ -d "$opal_home/templates" ]] && \
        echo "    ~/.opal/templates/           프로젝트 템플릿"
    [[ -d "$opal_home/dashboard-server" ]] && \
        echo "    ~/.opal/dashboard-server/    OPAL Console (http://127.0.0.1:7823)"

    [[ -f "$USER_HOME/.claude/CLAUDE.md" ]] && grep -qF "$OPAL_START" "$USER_HOME/.claude/CLAUDE.md" && \
        echo "    ~/.claude/CLAUDE.md          OPAL 부트스트래퍼"
    [[ -f "$USER_HOME/.cursor/rules/000-opal-agent.mdc" ]] && \
        echo "    ~/.cursor/rules/             OPAL 부트스트래퍼"
    [[ -f "$USER_HOME/.gemini/GEMINI.md" ]] && grep -qF "$OPAL_START" "$USER_HOME/.gemini/GEMINI.md" && \
        echo "    ~/.gemini/GEMINI.md          OPAL 부트스트래퍼"
    [[ -f "$USER_HOME/.gemini/GEMINI.md" ]] && grep -qF "$HARDENING_START" "$USER_HOME/.gemini/GEMINI.md" && \
        echo "    ~/.gemini/GEMINI.md          GEMINI HARDENING"
    [[ -f "$USER_HOME/.codex/AGENTS.md" ]] && grep -qF "$OPAL_START" "$USER_HOME/.codex/AGENTS.md" && \
        echo "    ~/.codex/AGENTS.md           OPAL 부트스트래퍼"

    echo "    Claude MCP                   claude mcp add (CLI 등록)"
    echo "    Gemini MCP                   gemini mcp add (CLI 등록)"
    echo "    Codex MCP                    codex mcp add (CLI 등록)"
    [[ -f "$USER_HOME/.cursor/mcp.json" ]] && \
        echo "    ~/.cursor/mcp.json           MCP 설정 (config_merge)"
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

    # 비대화형 모드 (one-liner curl | bash 호환): 메뉴 [3] 전체 설치 자동 실행
    if [[ "${OPAL_AUTO_INSTALL:-0}" == "1" ]] || [[ ! -t 0 ]]; then
        echo ""
        step "OPAL 자산 배포 중..."
        install_opal
        step "MCP 서버 설정 중..."
        install_mcp

        # 자세한 요약은 verbose 모드에서만 표시
        if [[ "$OPAL_VERBOSE" == "1" ]]; then
            installed+=("OPAL (skills + agents + 부트스트래퍼)" "MCP 서버")
            print_summary "${installed[@]}"
        fi

        # 마무리 (quiet/verbose 공통)
        local final_version="${OPAL_VERSION:-main}"
        [[ -f "$USER_HOME/.opal/VERSION" ]] && final_version="$(tr -d '[:space:]' < "$USER_HOME/.opal/VERSION")"
        echo ""
        echo -e "${GREEN}✓${NC} OPAL 설치 완료 (${final_version})"
        echo ""
        echo "  • ~/.opal/                  스킬·에이전트·도구"
        echo "  • ~/.opal/bin/opal-cli      CLI 진입점 (PATH 등록됨)"
        echo ""
        echo "다음 단계:"
        echo "  새 터미널 열기 또는  source ~/.zshrc"
        echo "  opal-cli doctor      # 환경 진단"
        echo ""
        exit 0
    fi

    while true; do
        show_menu

        case "$MENU_CHOICE" in
            1)
                install_opal
                installed+=("OPAL (skills + agents + 부트스트래퍼)")
                print_summary "${installed[@]}"
                ;;
            2)
                echo ""
                info "MCP 서버 설정..."
                install_mcp
                installed+=("MCP 서버 설정")
                print_summary "${installed[@]}"
                ;;
            3)
                install_opal
                echo ""
                info "MCP 서버 설정..."
                install_mcp
                installed+=("OPAL (skills + agents + 부트스트래퍼)" "MCP 서버")
                print_summary "${installed[@]}"
                ;;
            4)
                echo ""
                info "Python 패키지 업데이트..."
                install_opal_venv
                installed+=("Python 패키지 (.venv)")
                print_summary "${installed[@]}"
                ;;
            5)
                install_dashboard
                console_autostart
                installed+=("OPAL Console (dashboard-server + 서버 기동)")
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
