#!/usr/bin/env bash
#
# opal/tools/opal-cli/lib/uninstall.sh — uninstall 서브커맨드
#
# Usage: opal-cli uninstall [--yes] [--help]
#
# 동작:
#   1. ~/.opal/ 디렉토리 제거
#   2. ~/.claude/CLAUDE.md, ~/.gemini/GEMINI.md 등의 부트스트래퍼 파일에서
#      OPAL/R2 마커 블록(# === OPAL START === ~ # === OPAL END ===)만 제거
#      (파일 자체는 보존)
#   3. ~/.opal/bin PATH 등록 마커(# === OPAL PATH ===)도 제거
#
# 마커 패턴 (scripts/install-mac.sh:25-32):
#   OPAL: # === OPAL START === ~ # === OPAL END ===
#   R2:   # === R2 START ===   ~ # === R2 END ===
#   HARDENING: # === GEMINI HARDENING START === ~ # === GEMINI HARDENING END ===
#   PATH: # === OPAL PATH ===  ~ # === OPAL PATH END ===
#
# 변경이력:
#   v1.0 2026-05-08 11:00 초기 구현 — ~/.opal 제거 + 부트스트래퍼 마커 블록 회수 (139)
#

# ─── uninstall 서브커맨드 ─────────────────────────────────────

cmd_uninstall() {
    local force=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --yes|-y)
                force=1
                shift
                ;;
            --help|-h)
                _uninstall_usage
                return 0
                ;;
            *)
                error "알 수 없는 옵션: $1"
                _uninstall_usage
                return 1
                ;;
        esac
    done

    local opal_home="${OPAL_HOME:-$HOME/.opal}"

    echo ""
    warn "OPAL을 완전히 제거합니다."
    warn "  - 제거 대상: $opal_home/"
    warn "  - 마커 제거: CLAUDE.md / GEMINI.md OPAL 블록"
    warn "  - PATH 마커 제거: ~/.zshrc / ~/.bashrc / ~/.profile"
    warn "  - 파일 자체(CLAUDE.md 등)는 보존됩니다."
    echo ""

    if [[ -z "$force" ]]; then
        read -r -p "계속하시겠습니까? [y/N] " confirm
        if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
            info "제거가 취소되었습니다."
            return 0
        fi
    fi

    # 1. ~/.opal/ 제거
    if [[ -d "$opal_home" ]]; then
        rm -rf "$opal_home"
        success "제거 완료: $opal_home/"
    else
        info "이미 제거되어 있습니다: $opal_home/"
    fi

    # 2. 부트스트래퍼 마커 블록 제거
    _remove_marker_blocks

    # 3. PATH 등록 마커 제거
    _remove_path_markers

    echo ""
    success "OPAL 제거 완료"
    info "AI 도구를 재시작하면 OPAL 부트스트랩이 더 이상 실행되지 않습니다."
}

# ─── 마커 블록 제거 (부트스트래퍼) ──────────────────────────────

_remove_marker_blocks() {
    local user_home="${HOME}"

    # 대상 파일 목록 (부트스트래퍼가 삽입될 수 있는 파일들)
    local target_files=(
        "$user_home/.claude/CLAUDE.md"
        "$user_home/CLAUDE.md"
        "$user_home/.gemini/GEMINI.md"
        "$user_home/GEMINI.md"
    )

    # 마커 쌍 배열: [시작마커, 종료마커]
    local marker_pairs=(
        "# === OPAL START ===:# === OPAL END ==="
        "# === R2 START ===:# === R2 END ==="
        "# === GEMINI HARDENING START ===:# === GEMINI HARDENING END ==="
    )

    for file in "${target_files[@]}"; do
        [[ -f "$file" ]] || continue

        local modified=0
        for pair in "${marker_pairs[@]}"; do
            local start_marker="${pair%%:*}"
            local end_marker="${pair##*:}"

            if grep -qF "$start_marker" "$file"; then
                _remove_block_from_file "$file" "$start_marker" "$end_marker"
                modified=1
            fi
        done

        if [[ "$modified" -eq 1 ]]; then
            success "마커 블록 제거: $file"
        fi
    done
}

# 파일에서 시작~종료 마커 사이 블록을 제거
_remove_block_from_file() {
    local file="$1"
    local start_marker="$2"
    local end_marker="$3"

    local tmp_file
    tmp_file=$(mktemp)

    local in_block=0
    while IFS= read -r line || [[ -n "$line" ]]; do
        if [[ "$line" == "$start_marker" ]]; then
            in_block=1
            continue
        fi
        if [[ "$line" == "$end_marker" ]]; then
            in_block=0
            continue
        fi
        if [[ "$in_block" -eq 0 ]]; then
            printf '%s\n' "$line" >> "$tmp_file"
        fi
    done < "$file"

    # 파일 끝의 빈 줄 정리 후 교체
    mv "$tmp_file" "$file"
}

# ─── PATH 등록 마커 제거 ──────────────────────────────────────

_remove_path_markers() {
    local user_home="${HOME}"
    local rc_files=(
        "$user_home/.zshrc"
        "$user_home/.bashrc"
        "$user_home/.profile"
    )

    local path_start="# === OPAL PATH ==="
    local path_end="# === OPAL PATH END ==="

    for rc in "${rc_files[@]}"; do
        [[ -f "$rc" ]] || continue
        if grep -qF "$path_start" "$rc"; then
            _remove_block_from_file "$rc" "$path_start" "$path_end"
            success "PATH 마커 제거: $rc"
        fi
    done
}

_uninstall_usage() {
    cat <<EOF
사용법: opal-cli uninstall [--yes] [--help]

OPAL AI Framework를 제거합니다.

제거 내용:
  - ~/.opal/ 디렉토리 전체 삭제
  - CLAUDE.md, GEMINI.md 등의 OPAL/R2 마커 블록 제거 (파일 자체는 보존)
  - ~/.zshrc, ~/.bashrc, ~/.profile 의 OPAL PATH 마커 제거

옵션:
  --yes, -y     확인 프롬프트 없이 즉시 제거
  --help, -h    이 도움말 출력

예시:
  opal-cli uninstall
  opal-cli uninstall --yes
EOF
}
