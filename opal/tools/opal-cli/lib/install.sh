#!/usr/bin/env bash
#
# opal/tools/opal-cli/lib/install.sh — install 서브커맨드
#
# Usage: opal-cli install [--help]
#
# 동작:
#   scripts/install/macos.sh (또는 install-mac.sh fallback) 를 호출하여
#   OPAL 설치 또는 재설치를 수행한다.
#
# 변경이력:
#   v1.0 2026-05-08 11:00 초기 구현 — macos.sh wrapper 호출 (139)
#

# ─── install 서브커맨드 ───────────────────────────────────────

cmd_install() {
    local arg="${1:-}"

    if [[ "$arg" == "--help" || "$arg" == "-h" ]]; then
        cat <<EOF
사용법: opal-cli install [--help]

OPAL AI Framework 설치 또는 재설치를 수행합니다.
설치 스크립트(scripts/install/macos.sh 또는 install-mac.sh)를 찾아 실행합니다.

옵션:
  --help, -h    이 도움말 출력

예시:
  opal-cli install
EOF
        return 0
    fi

    # 설치 스크립트 경로 탐색
    # 1) OPAL 설치본의 tools 디렉토리로부터 소스 루트 추론
    # 2) FRAMEWORK_ROOT 환경변수 존재 시 우선 사용
    local installer=""

    if [[ -n "${FRAMEWORK_ROOT:-}" ]]; then
        if [[ -f "$FRAMEWORK_ROOT/scripts/install/macos.sh" ]]; then
            installer="$FRAMEWORK_ROOT/scripts/install/macos.sh"
        elif [[ -f "$FRAMEWORK_ROOT/scripts/install-mac.sh" ]]; then
            installer="$FRAMEWORK_ROOT/scripts/install-mac.sh"
        fi
    fi

    # FRAMEWORK_ROOT 미설정 시 opal-cli 위치에서 상대 경로로 추론
    # ~/.opal/tools/opal-cli/run.sh → ~/.opal가 배포 위치
    # 소스 레포는 별도이므로 여기서는 fallback 메시지만 제공
    if [[ -z "$installer" ]]; then
        error "설치 스크립트를 찾을 수 없습니다."
        info "FRAMEWORK_ROOT 환경변수를 설정하거나, 소스 레포에서 직접 실행하세요:"
        info "  git clone https://github.com/ceo4ever/opal && cd opal && ./scripts/install-mac.sh"
        return 1
    fi

    info "설치 스크립트 실행: $installer"
    bash "$installer" "$@"
}
