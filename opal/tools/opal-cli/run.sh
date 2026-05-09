#!/usr/bin/env bash
#
# opal/tools/opal-cli/run.sh — opal-cli 진입점 디스패처
#
# Usage:
#   opal-cli <subcommand> [args...]
#   opal-cli --version
#   opal-cli --help
#
# Subcommands: install | update | doctor | uninstall | mcp
#
# 변경이력:
#   v1.0 2026-05-08 11:00 초기 구현 — install/update/doctor/uninstall/mcp 디스패처 (139)
#   v1.0.1 2026-05-09 14:15 KST: BASH_SOURCE symlink chain 해석 보강 — ~/.opal/bin/opal-cli symlink 호출 시 lib/ 검색 실패 fix (139 추가작업)
#   v1.0.2 2026-05-09 17:45 KST: 색상 변수 $'...' 패턴 적용 — cat heredoc usage()/lib에서 \033[1m 리터럴 노출 fix (139 추가작업)
#

set -euo pipefail

# ─── 버전 ────────────────────────────────────────────────────
OPAL_CLI_VERSION="1.0.2"

# ─── 경로 ────────────────────────────────────────────────────
# BASH_SOURCE의 symlink chain을 따라 실제 위치 탐색
# (~/.opal/bin/opal-cli symlink로 호출되어도 lib/ 디렉토리를 정확히 찾기 위함, BSD readlink 호환)
SOURCE="${BASH_SOURCE[0]}"
while [ -L "$SOURCE" ]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ "$SOURCE" != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" >/dev/null && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"

# ─── Colors ──────────────────────────────────────────────────
# bash $'...' 패턴 — escape sequence를 ANSI 문자로 해석하여 변수에 저장.
# cat <<EOF heredoc 출력에서도 정상 동작 (cat은 escape 미해석 → 변수에 이미 ANSI 들어가 있어야 함).
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
BOLD=$'\033[1m'
NC=$'\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}  ✓${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# ─── Help ────────────────────────────────────────────────────

usage() {
    cat <<EOF
${BOLD}opal-cli${NC} — OPAL AI Framework CLI

${BOLD}사용법:${NC}
  opal-cli <subcommand> [options]
  opal-cli --version
  opal-cli --help

${BOLD}서브커맨드:${NC}
  install               OPAL 설치 (one-liner 외 수동 진입점)
  update [--to vX.Y]    업데이트 (사용자 데이터 보존)
  doctor                환경 진단 (의존성·경로·MCP·부트스트래퍼)
  uninstall             OPAL 제거 (~/.opal + 부트스트래퍼 마커)
  mcp [add|list|remove] [name]  MCP 관리

${BOLD}옵션:${NC}
  --version             버전 출력
  --help, -h            이 도움말 출력

${BOLD}예시:${NC}
  opal-cli install
  opal-cli update
  opal-cli update --to v0.2
  opal-cli doctor
  opal-cli uninstall
  opal-cli mcp list
  opal-cli mcp add context7

${BOLD}설치 경로:${NC}
  ~/.opal/bin/opal-cli  →  ~/.opal/tools/opal-cli/run.sh (symlink)

더 자세한 정보: ~/.opal/tools/opal-cli/README.md
EOF
}

# ─── 서브커맨드 디스패처 ──────────────────────────────────────

dispatch() {
    local subcommand="${1:-}"

    case "$subcommand" in
        --version|-v)
            echo "opal-cli $OPAL_CLI_VERSION"
            exit 0
            ;;
        --help|-h|help)
            usage
            exit 0
            ;;
        install|update|doctor|uninstall|mcp)
            local lib_file="$LIB_DIR/${subcommand}.sh"
            if [[ ! -f "$lib_file" ]]; then
                error "lib/${subcommand}.sh 파일을 찾을 수 없습니다: $lib_file"
                exit 1
            fi
            shift
            # shellcheck source=/dev/null
            source "$lib_file"
            "cmd_${subcommand}" "$@"
            ;;
        "")
            error "서브커맨드를 입력하세요."
            echo ""
            usage
            exit 1
            ;;
        *)
            error "알 수 없는 서브커맨드: $subcommand"
            echo ""
            usage
            exit 1
            ;;
    esac
}

dispatch "$@"
