#!/usr/bin/env bash
#
# opal/tools/opal-cli/lib/update.sh — update 서브커맨드
#
# Usage: opal-cli update [--to vX.Y] [--help]
#
# 동작:
#   GitHub Releases에서 release tarball을 재다운로드하여 OPAL을 업데이트한다.
#   사용자 데이터(identity.md, projects/)는 보존한다.
#
# 사용자 데이터 보존 정책 (PLAN §3.1.2 update 정책):
#   보존: ~/.opal/identity.md, ~/.opal/projects/, ~/.opal/community-skills/
#         ~/.opal/.venv/ (requirements.txt 재적용)
#   클린 후 재배포: ~/.opal/skills/, ~/.opal/agents/, ~/.opal/tools/
#   symlink 재생성: ~/.opal/bin/opal-cli
#
# 변경이력:
#   v1.0 2026-05-08 11:00 초기 구현 — tarball 재다운로드 + 사용자 데이터 보존 + --to 핀 옵션 (139)
#   v1.0.1 2026-05-09 18:00 KST: install-mac.sh 호출 시 OPAL_AUTO_INSTALL=1 명시 — tty 환경에서 비대화형 분기 강제 발동, ~/.opal/tools/ 갱신 결함 fix (139 추가작업)
#

# ─── update 서브커맨드 ────────────────────────────────────────

cmd_update() {
    local version=""
    local dry_run="${OPAL_DRY_RUN:-}"

    # 인자 파싱
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --to)
                if [[ -z "${2:-}" ]]; then
                    error "--to 옵션에 버전을 지정하세요 (예: --to v0.2)"
                    return 1
                fi
                version="$2"
                shift 2
                ;;
            --dry-run)
                dry_run=1
                shift
                ;;
            --help|-h)
                _update_usage
                return 0
                ;;
            *)
                error "알 수 없는 옵션: $1"
                _update_usage
                return 1
                ;;
        esac
    done

    local opal_home="${OPAL_HOME:-$HOME/.opal}"
    local opal_repo="${OPAL_REPO:-ceo4ever/opal}"

    # 버전 미지정 시 latest release 확인
    if [[ -z "$version" ]]; then
        info "최신 버전 확인 중..."
        if command -v curl &>/dev/null; then
            local latest
            latest=$(curl -fsSL --proto '=https' --tlsv1.2 \
                "https://api.github.com/repos/${opal_repo}/releases/latest" \
                2>/dev/null | grep '"tag_name"' | head -1 | sed 's/.*"tag_name": "\(.*\)".*/\1/') || true
            if [[ -n "$latest" ]]; then
                version="$latest"
                info "최신 버전: $version"
            else
                # API 실패 시 main 브랜치 tarball 사용
                version="main"
                warn "최신 버전 확인 실패 — main 브랜치 tarball 사용"
            fi
        else
            error "curl을 찾을 수 없습니다. curl을 설치 후 다시 시도하세요."
            return 1
        fi
    fi

    # Tarball URL 결정
    local tarball_url
    if [[ "$version" == "main" ]]; then
        tarball_url="https://github.com/${opal_repo}/archive/refs/heads/main.tar.gz"
    else
        tarball_url="https://github.com/${opal_repo}/releases/download/${version}/opal-${version}.tar.gz"
    fi

    info "업데이트 버전: $version"
    info "다운로드 URL: $tarball_url"

    if [[ -n "$dry_run" ]]; then
        info "[dry-run] 실제 다운로드 및 설치를 수행하지 않습니다."
        info "[dry-run] 보존 대상: identity.md, projects/, community-skills/, .venv/"
        info "[dry-run] 클린 대상: skills/, agents/, tools/"
        return 0
    fi

    # 사전 점검
    if [[ ! -d "$opal_home" ]]; then
        error "OPAL이 설치되어 있지 않습니다: $opal_home"
        info "먼저 opal-cli install 을 실행하세요."
        return 1
    fi

    # 임시 디렉토리 생성
    local tmp_dir
    tmp_dir=$(mktemp -d)
    # shellcheck disable=SC2064
    trap "rm -rf '$tmp_dir'" EXIT

    info "tarball 다운로드 중..."
    local tarball_path="$tmp_dir/opal.tar.gz"
    if ! curl -fsSL --proto '=https' --tlsv1.2 -o "$tarball_path" "$tarball_url"; then
        error "tarball 다운로드 실패: $tarball_url"
        return 1
    fi
    success "다운로드 완료"

    # 체크섬 검증 (release tarball인 경우)
    if [[ "$version" != "main" ]]; then
        local sha_url="https://github.com/${opal_repo}/releases/download/${version}/sha256sums.txt"
        local sha_file="$tmp_dir/sha256sums.txt"
        if curl -fsSL --proto '=https' --tlsv1.2 -o "$sha_file" "$sha_url" 2>/dev/null; then
            info "체크섬 검증 중..."
            local actual_sha
            actual_sha=$(sha256sum "$tarball_path" | awk '{print $1}')
            local expected_sha
            expected_sha=$(grep "opal-${version}.tar.gz" "$sha_file" 2>/dev/null | awk '{print $1}') || true
            if [[ -n "$expected_sha" && "$actual_sha" != "$expected_sha" ]]; then
                error "체크섬 불일치! 다운로드가 손상되었을 수 있습니다."
                error "  기대값: $expected_sha"
                error "  실제값: $actual_sha"
                return 1
            fi
            success "체크섬 검증 완료"
        else
            warn "sha256sums.txt 다운로드 실패 — 체크섬 검증 생략"
        fi
    fi

    # tarball 압축 해제
    local extract_dir="$tmp_dir/opal-src"
    mkdir -p "$extract_dir"
    info "압축 해제 중..."
    tar -xzf "$tarball_path" -C "$extract_dir" --strip-components=1 2>/dev/null || \
        tar -xzf "$tarball_path" -C "$extract_dir"
    success "압축 해제 완료"

    # 설치 스크립트 실행
    local installer=""
    if [[ -f "$extract_dir/scripts/install/macos.sh" ]]; then
        installer="$extract_dir/scripts/install/macos.sh"
    elif [[ -f "$extract_dir/scripts/install-mac.sh" ]]; then
        installer="$extract_dir/scripts/install-mac.sh"
    fi

    if [[ -z "$installer" ]]; then
        error "압축 해제된 패키지에서 설치 스크립트를 찾을 수 없습니다."
        return 1
    fi

    info "업데이트 설치 중... (사용자 데이터 보존)"
    warn "업데이트 주의: 사용자 커스텀 스킬(skills/)은 클린 후 재배포됩니다."
    warn "커스텀 스킬이 있으면 ~/.opal/skills.user/에 백업해두세요 (후속 태스크에서 자동화 예정)."
    # OPAL_AUTO_INSTALL=1 — install-mac.sh의 비대화형 분기 강제 발동 (tty 환경에서도 자동 [3] 전체 설치).
    # update.sh가 사용자 tty에서 호출되면 stdin이 tty → install-mac.sh의 [[ ! -t 0 ]] 조건이 false →
    # 메뉴 read -rp가 사용자 입력 대기 또는 잘못 처리되어 install_opal() 미호출 결함 회피.
    OPAL_AUTO_INSTALL=1 FRAMEWORK_ROOT="$extract_dir" bash "$installer"
    success "업데이트 완료 ($version)"
}

_update_usage() {
    cat <<EOF
사용법: opal-cli update [--to vX.Y] [--dry-run] [--help]

GitHub Releases에서 최신 OPAL을 다운로드하여 업데이트합니다.
사용자 데이터(identity.md, projects/, community-skills/)는 보존됩니다.

옵션:
  --to vX.Y     특정 버전으로 핀 (예: --to v0.2)
  --dry-run     실제 다운로드 없이 동작 확인
  --help, -h    이 도움말 출력

보존 항목:
  ~/.opal/identity.md        사용자 정체성 (덮어쓰기 금지)
  ~/.opal/projects/          프로젝트 메모리
  ~/.opal/community-skills/  vendor 스킬 (추가 디렉토리 보존)
  ~/.opal/.venv/             Python 가상환경

클린 후 재배포 항목:
  ~/.opal/skills/            프레임워크 스킬
  ~/.opal/agents/            에이전트 정의
  ~/.opal/tools/             도구 모음

예시:
  opal-cli update
  opal-cli update --to v0.2
  opal-cli update --dry-run
EOF
}
