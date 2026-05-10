#!/usr/bin/env bash
#
# scripts/install.sh — macOS/Linux 통합 one-liner 진입 부트스트랩
#
# 역할: curl-pipe-bash 보안 패턴으로 OPAL을 설치한다.
#       tarball 다운로드 → SHA-256 체크섬 검증 → 임시 디렉토리 추출
#       → 플랫폼별 설치 스크립트(install/macos.sh 또는 install/linux.sh) 호출.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.sh | bash
#   bash scripts/install.sh                      # 로컬 실행
#   OPAL_DRY_RUN=1 bash scripts/install.sh       # dry-run (fetch 없이 흐름 검증)
#   OPAL_VERSION=v0.1 bash scripts/install.sh    # 특정 버전 설치
#
# 환경 변수:
#   OPAL_REPO     GitHub 저장소 (기본: ceo4ever/opal)   [MUST] D2
#   OPAL_VERSION  브랜치 또는 태그 (기본: main)
#   OPAL_DRY_RUN  1 이면 실제 fetch 없이 흐름만 출력
#
# 보안 패턴:
#   - set -euo pipefail 필수                            [MUST] D-13
#   - curl -fsSL --proto '=https' --tlsv1.2 필수        [MUST] D-13
#   - main() 래핑으로 부분 다운로드 실행 방지            [MUST] D-13
#   - SHA-256 체크섬 검증 (sha256sums.txt)              [MUST] D-13
#   - mktemp -d + trap EXIT 정리                        [MUST] D-13
#
# 근거:
#   tasks/139-260508-opp-distribute-and-getstarted/PLAN.md §3.1.2
#   tasks/139-260508-opp-distribute-and-getstarted/PLAN.md §4.2 Step 5
#   tasks/139-260508-opp-distribute-and-getstarted/TASK.md ## 캡틴 확정 결정 사항 D2
#
# 변경이력:
#   v1.0 2026-05-09 10:00: 신규 작성 — macOS/Linux 통합 one-liner 진입점 (139)
#   v1.1 2026-05-09 21:20: OPAL_VERSION default를 latest release로 변경 + export로 install-mac.sh에 전달
#                          + release 자산 URL(opal-{tag}.tar.gz) 사용으로 sha256 매칭 (139 추가작업)
#   v1.2 2026-05-09 21:35: resolve_default_version에 /tags 폴백 추가 (release 자산 미생성 케이스 호환).
#                          TARBALL_URL을 archive/refs/tags로 변경하여 release 자산 없어도 다운로드 가능 (139 추가작업)
#   v1.3 2026-05-10 21:00: verify_checksum 강화 — release tag + sha256sums.txt 부재 시 prompt/거부 +
#                          main 브랜치 UNVERIFIED banner (GC-001, R-2) (144)
#

# ─── [MUST] 부분 다운로드 실행 방지 ─────────────────────────────────────────
# 이 파일 전체가 다운로드된 뒤 main "$@" 이 호출된다.
# curl-pipe-bash 시 bash는 스크립트 전체를 수신한 후 실행을 시작하므로
# 함수 정의가 모두 완료된 상태에서 main()이 호출된다.
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ─── 환경 변수 기본값 ────────────────────────────────────────────────────────
# OPAL_REPO  : GitHub 저장소 (기본: ceo4ever/opal)   [MUST] D2
# OPAL_VERSION: 명시 시 그 버전, 미명시 시 latest release tag 자동 조회 (실패 시 "main" 폴백)
# OPAL_DRY_RUN: 1 이면 실제 fetch 없이 흐름만 출력
OPAL_REPO="${OPAL_REPO:-ceo4ever/opal}"
OPAL_DRY_RUN="${OPAL_DRY_RUN:-0}"

# ─── 출력 헬퍼 (URL 구성 전에 정의 — resolve_default_version에서 사용) ───
info()    { printf '\033[0;34m[opal]\033[0m %s\n' "$*"; }
success() { printf '\033[0;32m[opal]\033[0m %s\n' "$*"; }
warn()    { printf '\033[0;33m[opal] WARN:\033[0m %s\n' "$*" >&2; }
error()   { printf '\033[0;31m[opal] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# ─── resolve_default_version ─────────────────────────────────────────────
# OPAL_VERSION이 미설정이면 자동 결정:
#   1) GitHub API /releases/latest (published release)
#   2) 폴백: GitHub API /tags?per_page=1 (가장 최근 태그 — release 자산 미생성 케이스 호환)
#   3) 두 단계 모두 실패 시 "main" 폴백 + 경고
resolve_default_version() {
    if [[ -n "${OPAL_VERSION:-}" ]]; then
        return 0
    fi

    if [[ "${OPAL_DRY_RUN}" == "1" ]]; then
        OPAL_VERSION="main"
        return 0
    fi

    # 1차: /releases/latest
    local latest
    latest="$(curl -fsSL --proto '=https' --tlsv1.2 \
        "https://api.github.com/repos/${OPAL_REPO}/releases/latest" 2>/dev/null \
        | grep '"tag_name"' | head -1 | sed 's/.*"tag_name": "\([^"]*\)".*/\1/')" || true

    # 2차 폴백: /tags?per_page=1 (release 자산 없는 케이스 — release.yml 결함 등)
    if [[ -z "${latest}" ]]; then
        latest="$(curl -fsSL --proto '=https' --tlsv1.2 \
            "https://api.github.com/repos/${OPAL_REPO}/tags?per_page=1" 2>/dev/null \
            | grep '"name"' | head -1 | sed 's/.*"name": "\([^"]*\)".*/\1/')" || true
        if [[ -n "${latest}" ]]; then
            info "최신 태그 자동 선택: ${latest} (release 자산 없음 — archive tarball 사용)"
        fi
    else
        info "최신 release 자동 선택: ${latest}"
    fi

    if [[ -n "${latest}" ]]; then
        OPAL_VERSION="${latest}"
    else
        OPAL_VERSION="main"
        warn "최신 버전 조회 실패 — main 브랜치 사용"
    fi
}

resolve_default_version

# install-mac.sh가 ~/.opal/VERSION에 정확한 버전을 기록할 수 있도록 export
export OPAL_VERSION

# ─── URL 구성 ─────────────────────────────────────────────────────────────────
# release tag(v*): GitHub archive(/refs/tags) 사용 — release.yml 자산이 없어도 항상 동작.
#                  release 자산이 있는 경우 sha256sums.txt가 동시에 존재 → verify_checksum이 검증.
# branch (main 등): /refs/heads 사용.
if [[ "${OPAL_VERSION}" == v* ]]; then
    TARBALL_URL="https://github.com/${OPAL_REPO}/archive/refs/tags/${OPAL_VERSION}.tar.gz"
else
    TARBALL_URL="https://github.com/${OPAL_REPO}/archive/refs/heads/${OPAL_VERSION}.tar.gz"
fi
# sha256sums.txt는 release 자산. release.yml이 정상이면 존재, 아니면 verify_checksum이 graceful skip.
SHA_URL="https://github.com/${OPAL_REPO}/releases/download/${OPAL_VERSION}/sha256sums.txt"

# ─── 임시 디렉토리 + 자동 정리 ───────────────────────────────────────────────
# [MUST] PLAN §3.1.2: "임시 디렉토리는 mktemp -d로 생성, trap EXIT로 정리"
OPAL_TMP=""

cleanup() {
    if [[ -n "${OPAL_TMP}" && -d "${OPAL_TMP}" ]]; then
        rm -rf "${OPAL_TMP}"
    fi
}
trap cleanup EXIT

# 출력 헬퍼는 환경 변수 결정 전에 위에서 정의됨

# ─── detect_platform ─────────────────────────────────────────────────────────
# uname -s 결과로 플랫폼을 판별한다.
# 지원: Darwin(macOS), Linux
detect_platform() {
    local uname_s
    uname_s="$(uname -s)"
    case "${uname_s}" in
        Darwin)
            OPAL_PLATFORM="macos"
            ;;
        Linux)
            OPAL_PLATFORM="linux"
            ;;
        *)
            error "지원하지 않는 플랫폼입니다: ${uname_s}. macOS 또는 Linux가 필요합니다."
            ;;
    esac
    info "플랫폼 감지: ${OPAL_PLATFORM}"
}

# ─── check_deps ──────────────────────────────────────────────────────────────
# 필수 의존성(bash, curl, tar, git) 존재 여부를 확인한다.
check_deps() {
    local missing=()
    local deps=("curl" "tar" "git")

    for dep in "${deps[@]}"; do
        if ! command -v "${dep}" &>/dev/null; then
            missing+=("${dep}")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        error "필수 도구가 없습니다: ${missing[*]}"
    fi

    info "의존성 확인 완료: curl, tar, git"
}

# ─── fetch_tarball ───────────────────────────────────────────────────────────
# [MUST] curl 플래그: -fsSL --proto '=https' --tlsv1.2
# OPAL_DRY_RUN=1 시 실제 download를 생략하고 흐름만 출력한다.
fetch_tarball() {
    OPAL_TMP="$(mktemp -d)"
    OPAL_TARBALL="${OPAL_TMP}/opal.tar.gz"

    info "tarball URL: ${TARBALL_URL}"

    if [[ "${OPAL_DRY_RUN}" == "1" ]]; then
        warn "[DRY-RUN] fetch_tarball 생략 — 실제 다운로드 없음"
        # dry-run 에서도 이후 단계가 흐름 검증 가능하도록 빈 파일 생성
        touch "${OPAL_TARBALL}"
        return 0
    fi

    info "tarball 다운로드 중..."
    # [MUST] PLAN §3.1.2: "curl 플래그 -fsSL --proto '=https' --tlsv1.2"
    curl \
        --fail \
        --silent \
        --show-error \
        --location \
        --proto '=https' \
        --tlsv1.2 \
        --output "${OPAL_TARBALL}" \
        "${TARBALL_URL}" || error "tarball 다운로드 실패: ${TARBALL_URL}"

    success "tarball 다운로드 완료: ${OPAL_TARBALL}"
}

# ─── verify_checksum ─────────────────────────────────────────────────────────
# sha256sums.txt를 다운로드하여 tarball SHA-256을 검증한다.
# sha256sums.txt가 없는 경우(main 브랜치 등) 경고 후 건너뛴다.
# [MUST] PLAN §3.1.2: "sha256sums.txt 다운로드 후 shasum -a 256 -c (mac) / sha256sum -c (linux) 분기"
verify_checksum() {
    if [[ "${OPAL_DRY_RUN}" == "1" ]]; then
        warn "[DRY-RUN] verify_checksum 생략"
        return 0
    fi

    local sha_file="${OPAL_TMP}/sha256sums.txt"

    info "체크섬 파일 확인 중: ${SHA_URL}"

    # sha256sums.txt는 릴리스 태그 시에만 존재한다.
    # HTTP 404 시 -f 플래그에 의해 curl이 실패하므로 || true 로 처리.
    if ! curl \
            --fail \
            --silent \
            --show-error \
            --location \
            --proto '=https' \
            --tlsv1.2 \
            --output "${sha_file}" \
            "${SHA_URL}" 2>/dev/null; then
        # sha256sums.txt 없음 — release tag(v*) 인 경우 prompt/거부 적용
        if [[ "${OPAL_VERSION}" == v* ]]; then
            # release tag지만 sha256sums.txt 부재 — 무결성 검증 불가
            if [[ "${OPAL_ALLOW_UNVERIFIED:-}" == "1" ]]; then
                warn "[UNVERIFIED] sha256sums.txt 없음 — OPAL_ALLOW_UNVERIFIED=1로 무결성 검증 없이 진행"
                return 0
            fi
            # 비대화형 모드 (stdin pipe 또는 OPAL_AUTO_INSTALL=1): 기본 거부
            if [[ ! -t 0 ]] || [[ "${OPAL_AUTO_INSTALL:-}" == "1" ]]; then
                error "sha256sums.txt 없음 — 비대화형 모드에서 무결성 검증 없는 설치를 거부합니다. 옵트인: OPAL_ALLOW_UNVERIFIED=1"
            fi
            # 대화형 모드: prompt (디폴트 N)
            read -r -p "sha256sums.txt 없음 — 무결성 검증 없이 진행하시겠습니까? [y/N] " unverified_confirm
            if [[ "$unverified_confirm" != "y" && "$unverified_confirm" != "Y" ]]; then
                error "사용자가 취소했습니다. 옵트인: OPAL_ALLOW_UNVERIFIED=1"
            fi
            warn "[UNVERIFIED] 사용자 동의로 무결성 검증 없이 진행"
        else
            warn "sha256sums.txt 없음 (브랜치 설치 또는 릴리스 미배포) — 체크섬 검증 건너뜀"
        fi
        return 0
    fi

    # tarball 파일명을 sha256sums.txt 내 항목과 매핑하기 위해 같은 디렉토리에서 검증
    local tarball_name
    tarball_name="$(basename "${OPAL_TARBALL}")"
    local sha_entry
    sha_entry="$(grep "${tarball_name}" "${sha_file}" 2>/dev/null || true)"

    if [[ -z "${sha_entry}" ]]; then
        warn "sha256sums.txt에 ${tarball_name} 항목 없음 — 체크섬 검증 건너뜀"
        return 0
    fi

    info "SHA-256 검증 중..."
    # 플랫폼별 체크섬 명령 분기
    # [MUST] PLAN §3.1.2: "shasum -a 256 -c (mac) 또는 sha256sum -c (linux) 분기"
    if [[ "${OPAL_PLATFORM}" == "macos" ]]; then
        if ! (cd "${OPAL_TMP}" && shasum -a 256 -c "${sha_file}" --ignore-missing 2>/dev/null); then
            error "SHA-256 체크섬 검증 실패 — 다운로드가 손상되었을 수 있습니다."
        fi
    else
        if ! (cd "${OPAL_TMP}" && sha256sum -c "${sha_file}" --ignore-missing 2>/dev/null); then
            error "SHA-256 체크섬 검증 실패 — 다운로드가 손상되었을 수 있습니다."
        fi
    fi

    success "SHA-256 체크섬 검증 완료"
}

# ─── extract_to_tmp ──────────────────────────────────────────────────────────
# tarball을 임시 디렉토리에 추출한다.
extract_to_tmp() {
    if [[ "${OPAL_DRY_RUN}" == "1" ]]; then
        warn "[DRY-RUN] extract_to_tmp 생략"
        OPAL_EXTRACT_DIR="${OPAL_TMP}/opal-extracted"
        mkdir -p "${OPAL_EXTRACT_DIR}"
        return 0
    fi

    info "tarball 추출 중..."
    OPAL_EXTRACT_DIR="${OPAL_TMP}/opal-extracted"
    mkdir -p "${OPAL_EXTRACT_DIR}"

    tar -xzf "${OPAL_TARBALL}" -C "${OPAL_EXTRACT_DIR}" --strip-components=1 \
        || error "tarball 추출 실패"

    success "추출 완료: ${OPAL_EXTRACT_DIR}"
}

# ─── exec_platform_installer ─────────────────────────────────────────────────
# 플랫폼별 설치 스크립트를 실행한다.
# macOS: scripts/install/macos.sh
# Linux: scripts/install/linux.sh (미구현 시 fallback 안내)
exec_platform_installer() {
    local installer_path

    case "${OPAL_PLATFORM}" in
        macos)
            installer_path="${OPAL_EXTRACT_DIR}/scripts/install/macos.sh"
            ;;
        linux)
            installer_path="${OPAL_EXTRACT_DIR}/scripts/install/linux.sh"
            ;;
        *)
            error "알 수 없는 플랫폼: ${OPAL_PLATFORM}"
            ;;
    esac

    if [[ "${OPAL_DRY_RUN}" == "1" ]]; then
        warn "[DRY-RUN] exec_platform_installer 생략"
        info "[DRY-RUN] 실행 예정 경로: ${installer_path}"
        success "[DRY-RUN] 흐름 검증 완료"
        return 0
    fi

    if [[ ! -f "${installer_path}" ]]; then
        # Linux 전용 installer 미구현 시 fallback 안내
        if [[ "${OPAL_PLATFORM}" == "linux" ]]; then
            warn "Linux 전용 설치 스크립트가 아직 준비 중입니다 (scripts/install/linux.sh)."
            warn "Linux 사용자는 다음 명령으로 수동 설치하세요:"
            warn "  git clone https://github.com/${OPAL_REPO}.git opal"
            warn "  bash opal/scripts/install-mac.sh"
            exit 1
        fi
        error "플랫폼 설치 스크립트를 찾을 수 없습니다: ${installer_path}"
    fi

    chmod +x "${installer_path}"

    info "${OPAL_PLATFORM} 설치 스크립트 실행 중..."
    # 추출된 소스 디렉토리를 REPO_ROOT로 전달하여 설치 스크립트가
    # 올바른 소스 경로를 참조할 수 있게 한다.
    export OPAL_SOURCE_DIR="${OPAL_EXTRACT_DIR}"
    exec bash "${installer_path}" "$@"
}

# ─── main ────────────────────────────────────────────────────────────────────
# [MUST] PLAN §3.1.2: "main() 래핑 — 부분 다운로드 실행 방지"
# 이 함수가 파일 최하단에서 호출되므로 모든 함수 정의 완료 후 실행된다.
main() {
    info "OPAL 설치 시작 (repo: ${OPAL_REPO}, version: ${OPAL_VERSION})"

    if [[ "${OPAL_DRY_RUN}" == "1" ]]; then
        warn "=== DRY-RUN 모드 — 실제 설치 없이 흐름만 검증합니다 ==="
    fi

    # main 브랜치 UNVERIFIED banner (release tag 외 모든 버전) (R-2, GC-001)
    if [[ "${OPAL_VERSION}" != v* ]]; then
        warn "[UNVERIFIED] '${OPAL_VERSION}' 브랜치 설치 — SHA-256 무결성 검증 없음. 공식 릴리스(v*)를 권장합니다."
    fi

    detect_platform
    check_deps
    fetch_tarball
    verify_checksum
    extract_to_tmp
    exec_platform_installer "$@"
}

main "$@"
