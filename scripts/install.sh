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
#   v1.4 2026-05-20: Linux fallback 안내 블록 제거 — scripts/install/linux.sh 신설로 데드코드 (006)
#   v1.5 2026-06-29 15:24 KST: adopt_stamped_version 추가 — tarball 내 VERSION 각인값 우선 채택, API/main 폴백 강등 (048)
#   v1.6 2026-08-07 12:04 KST: DL-CONTRACT (085) 적용 — 다운로드 대상을 릴리즈 자산으로 전환, 로컬명=자산명,
#                          체크섬 3분기(verify/unverified/branch) 하드닝(고정문자열 매칭 + 항목 부재 하드 실패),
#                          추출 strip 자동 판정 + 사후조건 검사.
#                          정합 fix: sha 항목 선택을 파일명 컬럼 정확 일치로 교정(상위문자열 오채택 차단, D-2)
#                          + 체크섬 case에 `*)` 하드 실패 분기 추가(모드값 이상 fail-closed, D-6).
#                          TEST fix: DRY-RUN 조기 반환을 버전 종류로 분기(태그=릴리즈 자산 1순위 안내, 브랜치=아카이브)
#                          — 네트워크 0회 유지(RG-7, O-1) + strip 판정값 검증(빈 값·비수치 거부, 무음 강등 차단, O-5) (085)
#
# DL-CONTRACT (085): 릴리즈 태그는 릴리즈 자산 우선 + sha256sums.txt 부재 시 자동 아카이브 폴백(UNVERIFIED) + strip 자동 판정
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

# ─── 다운로드 계획 전역 (DL-CONTRACT 085) ────────────────────────────────────
# 값은 resolve_download_plan() / _dl_fallback() 이 설정한다 (§3.0 D-C).
#   TARBALL_URL         다운로드 URL
#   OPAL_TARBALL_NAME   로컬 저장 파일명 — [MUST] verify 모드에서는 발행 자산명과 동일
#   OPAL_CHECKSUM_MODE  verify | unverified | branch
#   OPAL_SHA_FILE       sha256sums.txt 로컬 경로 (verify 모드에서만 유효)
#   OPAL_TARBALL        ${OPAL_TMP}/${OPAL_TARBALL_NAME} (fetch_tarball이 설정)
TARBALL_URL=""
OPAL_TARBALL_NAME=""
OPAL_CHECKSUM_MODE=""
OPAL_SHA_FILE=""
OPAL_TARBALL=""

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

# ─── DL-CONTRACT (085) 공통 헬퍼 ──────────────────────────────
#
# [MUST] _dl_asset_name / _dl_detect_strip 의 본문은 `opal/tools/opal-cli/lib/update.sh` 와
#        **문자 단위로 동일**하게 유지한다 (PLAN §3.0 D-A 정합 수단 (a)). 한쪽만 수정하면 규약이 드리프트한다.
#        두 헬퍼는 외부 전역·로그 헬퍼에 의존하지 않는다 — tar / awk 만 사용한다.

# sha256sums.txt에서 첫 .tar.gz 파일명 컬럼을 파생 (binary mode '*' 접두 제거).
# 항목이 없으면 공백을 출력하고 exit 0 — 폴백 여부는 호출자가 판단한다.
_dl_asset_name() {
    awk '{ n = $2; sub(/^\*/, "", n); if (n ~ /\.tar\.gz$/) { print n; exit } }' "$1"
}

# tar 최상위 구조 판정 → 0(루트 직속 항목 있음) | 1(단일 prefix 디렉토리) (§3.0 D-D).
# 목록 1회 스캔, awk 단일 패스.
_dl_detect_strip() {
    tar -tzf "$1" | awk -F/ '
        NF == 0 { next }
        { if ($0 !~ /\//) root++; tops[$1] = 1 }
        END { n = 0; for (t in tops) n++; print (root == 0 && n == 1) ? 1 : 0 }
    '
}

# 자동 아카이브 폴백으로 강등 — $1=사유
# [MUST] 폴백 경로에서는 sha256sums.txt를 어떤 경우에도 비교에 사용하지 않는다 (H-3).
_dl_fallback() {
    if [[ -n "${OPAL_SHA_FILE}" ]]; then
        rm -f "${OPAL_SHA_FILE}" 2>/dev/null || true
    fi
    OPAL_SHA_FILE=""
    TARBALL_URL="https://github.com/${OPAL_REPO}/archive/refs/tags/${OPAL_VERSION}.tar.gz"
    OPAL_TARBALL_NAME="opal-${OPAL_VERSION}-archive.tar.gz"
    OPAL_CHECKSUM_MODE="unverified"
    warn "릴리즈 자산 미사용 폴백: $1"
}

# ─── prepare_tmp ─────────────────────────────────────────────────────────────
# [MUST] PLAN §3.1.2: "임시 디렉토리는 mktemp -d로 생성, trap EXIT로 정리"
# sha256sums.txt를 tarball보다 먼저 받아야 하므로 생성 시점을 fetch_tarball보다 앞에 둔다 (§2.2.3).
prepare_tmp() {
    OPAL_TMP="$(mktemp -d)"
}

# ─── resolve_download_plan ───────────────────────────────────────────────────
# 다운로드 소스를 확정한다 (§3.0 D-B·D-C).
#   릴리즈 태그(v*) : sha256sums.txt 선조회 성공 = 릴리즈 자산 존재 → 자산명 파생 후 verify
#                     조회 실패/형식 이상 → 자동 아카이브 폴백(unverified)
#   브랜치          : archive/refs/heads (기존 URL 무변경, RG-1)
# [MUST] RG-7: OPAL_DRY_RUN=1 이면 네트워크에 접근하지 않고 조기 반환한다.
#              조기 반환도 버전 종류(태그/브랜치)로 분기해 실제 1순위 경로를 안내한다 — 조회는 하지 않는다.
resolve_download_plan() {
    OPAL_SHA_FILE=""

    if [[ "${OPAL_DRY_RUN}" == "1" ]]; then
        warn "[DRY-RUN] resolve_download_plan 생략 — 네트워크 조회 없음"
        if [[ "${OPAL_VERSION}" == v* ]]; then
            # 릴리즈 태그: 릴리즈 자산이 1순위 경로다. 자산명은 sha256sums.txt 조회로만 확정되므로
            # (자산명 하드코딩 금지, §3.0 D-B) DRY-RUN에서는 자리표시자로 안내한다.
            TARBALL_URL="https://github.com/${OPAL_REPO}/releases/download/${OPAL_VERSION}/<sha256sums.txt 파생 자산명>"
            OPAL_TARBALL_NAME="opal-${OPAL_VERSION}-dryrun.tar.gz"
            OPAL_CHECKSUM_MODE="verify"
            info "[DRY-RUN] 1순위: 릴리즈 자산 — 자산명은 sha256sums.txt 조회로만 확정된다 (조회 생략)"
            info "[DRY-RUN] 자산 부재 시: 자동 아카이브 폴백 (UNVERIFIED)"
        else
            TARBALL_URL="https://github.com/${OPAL_REPO}/archive/refs/heads/${OPAL_VERSION}.tar.gz"
            OPAL_TARBALL_NAME="opal-${OPAL_VERSION}.tar.gz"
            OPAL_CHECKSUM_MODE="branch"
            info "[DRY-RUN] 브랜치 아카이브 — SHA-256 무결성 검증 대상 아님 (UNVERIFIED)"
        fi
        return 0
    fi

    if [[ "${OPAL_VERSION}" != v* ]]; then
        TARBALL_URL="https://github.com/${OPAL_REPO}/archive/refs/heads/${OPAL_VERSION}.tar.gz"
        OPAL_TARBALL_NAME="opal-${OPAL_VERSION}.tar.gz"
        OPAL_CHECKSUM_MODE="branch"
        return 0
    fi

    # 릴리즈 자산 존재 판정: sha256sums.txt 다운로드 성공 여부가 단일 신호 (§3.0 D-B)
    local sha_url="https://github.com/${OPAL_REPO}/releases/download/${OPAL_VERSION}/sha256sums.txt"
    OPAL_SHA_FILE="${OPAL_TMP}/sha256sums.txt"
    info "체크섬 파일 확인 중: ${sha_url}"
    # HTTP 404 시 --fail에 의해 curl이 실패한다 — 자산 부재로 판정하고 폴백한다.
    if ! curl \
            --fail \
            --silent \
            --show-error \
            --location \
            --proto '=https' \
            --tlsv1.2 \
            --output "${OPAL_SHA_FILE}" \
            "${sha_url}" 2>/dev/null; then
        _dl_fallback "릴리즈 자산 없음 (sha256sums.txt 조회 실패)"
        return 0
    fi

    # [MUST] 자산명은 하드코딩하지 않고 검증 대상 목록에서 파생한다 — 다운로드 대상 = 검증 대상
    local asset
    asset="$(_dl_asset_name "${OPAL_SHA_FILE}")"
    if [[ -z "${asset}" ]]; then
        _dl_fallback "sha256sums.txt 형식 이상 (.tar.gz 항목 없음)"
        return 0
    fi

    TARBALL_URL="https://github.com/${OPAL_REPO}/releases/download/${OPAL_VERSION}/${asset}"
    OPAL_TARBALL_NAME="${asset}"
    OPAL_CHECKSUM_MODE="verify"
    return 0
}

# ─── fetch_tarball ───────────────────────────────────────────────────────────
# [MUST] curl 플래그: -fsSL --proto '=https' --tlsv1.2
# OPAL_DRY_RUN=1 시 실제 download를 생략하고 흐름만 출력한다.
# 릴리즈 자산 다운로드 실패 시 자동 아카이브로 1회 강등 후 재시도한다 (§3.0 D-C).
fetch_tarball() {
    OPAL_TARBALL="${OPAL_TMP}/${OPAL_TARBALL_NAME}"

    info "tarball URL: ${TARBALL_URL}"

    if [[ "${OPAL_DRY_RUN}" == "1" ]]; then
        warn "[DRY-RUN] fetch_tarball 생략 — 실제 다운로드 없음"
        # dry-run 에서도 이후 단계가 흐름 검증 가능하도록 빈 파일 생성
        touch "${OPAL_TARBALL}"
        return 0
    fi

    info "tarball 다운로드 중..."
    # [MUST] PLAN §3.1.2: "curl 플래그 -fsSL --proto '=https' --tlsv1.2"
    if ! curl \
            --fail \
            --silent \
            --show-error \
            --location \
            --proto '=https' \
            --tlsv1.2 \
            --output "${OPAL_TARBALL}" \
            "${TARBALL_URL}"; then
        if [[ "${OPAL_CHECKSUM_MODE}" != "verify" ]]; then
            error "tarball 다운로드 실패: ${TARBALL_URL}"
        fi
        # 릴리즈 자산 다운로드 실패 — 폴백 1회 강등 후 재시도
        _dl_fallback "릴리즈 자산 다운로드 실패"
        OPAL_TARBALL="${OPAL_TMP}/${OPAL_TARBALL_NAME}"
        info "폴백 tarball URL: ${TARBALL_URL}"
        curl \
            --fail \
            --silent \
            --show-error \
            --location \
            --proto '=https' \
            --tlsv1.2 \
            --output "${OPAL_TARBALL}" \
            "${TARBALL_URL}" || error "tarball 다운로드 실패: ${TARBALL_URL}"
    fi

    success "tarball 다운로드 완료: ${OPAL_TARBALL}"
}

# ─── verify_checksum ─────────────────────────────────────────────────────────
# resolve_download_plan이 확정한 OPAL_CHECKSUM_MODE에 따라 무결성을 판정한다 (§3.0 D-C).
#   verify     : sha256sums.txt 항목과 대조 — 무음 스킵 금지, 어긋나면 전부 하드 실패
#   unverified : 릴리즈 자산 미사용 — 옵트인 / 비대화형 거부 / 프롬프트 3분기 (R-2, GC-001, RG-4)
#   branch     : 브랜치 설치 — 배너는 main()에서 이미 출력 (RG-3)
# [MUST] PLAN §3.1.2: "shasum -a 256 -c (mac) / sha256sum -c (linux) 분기"
# 이 함수는 네트워크에 접근하지 않는다 — 다운로드는 resolve_download_plan / fetch_tarball의 책임이다.
verify_checksum() {
    if [[ "${OPAL_DRY_RUN}" == "1" ]]; then
        warn "[DRY-RUN] verify_checksum 생략"
        return 0
    fi

    case "${OPAL_CHECKSUM_MODE}" in
        verify)
            local sha_entry expected_hash
            # [MUST] 고정 문자열 매칭 — 파일명의 '.'이 정규식 와일드카드로 해석되는 오매칭 차단 (H-9)
            # [MUST] grep -F 는 부분문자열 매칭이므로 전(前)필터로만 쓰고, 파일명 컬럼($2, binary mode '*' 제거)
            #        정확 일치로 항목을 확정한다 — 상위문자열 항목(예: {자산}.tar.gz.sig)이 먼저 와도
            #        그 행을 채택하지 않는다 (D-2). install.ps1 의 컬럼 정확 일치와 동형.
            sha_entry="$(grep -F -- "${OPAL_TARBALL_NAME}" "${OPAL_SHA_FILE}" \
                | awk -v want="${OPAL_TARBALL_NAME}" '{ n = $2; sub(/^\*/, "", n); if (n == want) { print; exit } }' || true)"
            # [MUST] 항목 부재는 무음 스킵이 아니라 규약 위반이다 — 설치를 거부한다
            if [[ -z "${sha_entry}" ]]; then
                error "sha256sums.txt에 ${OPAL_TARBALL_NAME} 항목 없음 — DL-CONTRACT 위반. 설치를 중단합니다."
            fi
            # [MUST] 기대값 파싱 실패도 무음 통과가 아니라 하드 실패다 (H-10)
            expected_hash="$(printf '%s\n' "${sha_entry}" | awk 'NF >= 2 { print $1; exit }')"
            if [[ -z "${expected_hash}" ]]; then
                error "체크섬 기대값 파싱 실패 — sha256sums.txt 형식 이상. 설치를 중단합니다."
            fi

            info "SHA-256 검증 중..."
            # 플랫폼별 체크섬 명령 분기 (detect_platform 선행 전제)
            # 실패 사유를 사용자에게 보여야 하므로 stderr를 억제하지 않는다.
            if [[ "${OPAL_PLATFORM}" == "macos" ]]; then
                if ! (cd "${OPAL_TMP}" && shasum -a 256 -c "${OPAL_SHA_FILE}" --ignore-missing); then
                    error "SHA-256 체크섬 검증 실패 — 다운로드가 손상되었을 수 있습니다."
                fi
            else
                if ! (cd "${OPAL_TMP}" && sha256sum -c "${OPAL_SHA_FILE}" --ignore-missing); then
                    error "SHA-256 체크섬 검증 실패 — 다운로드가 손상되었을 수 있습니다."
                fi
            fi

            success "SHA-256 체크섬 검증 완료"
            ;;
        unverified)
            # 릴리즈 자산 미사용 — 무결성 검증 불가 (R-2, GC-001, RG-4)
            if [[ "${OPAL_ALLOW_UNVERIFIED:-}" == "1" ]]; then
                warn "[UNVERIFIED] 릴리즈 자산 없음 — OPAL_ALLOW_UNVERIFIED=1로 무결성 검증 없이 진행"
                return 0
            fi
            # 비대화형 모드 (stdin pipe 또는 OPAL_AUTO_INSTALL=1): 기본 거부
            if [[ ! -t 0 ]] || [[ "${OPAL_AUTO_INSTALL:-}" == "1" ]]; then
                error "릴리즈 자산 없음 — 비대화형 모드에서 무결성 검증 없는 설치를 거부합니다. 옵트인: OPAL_ALLOW_UNVERIFIED=1"
            fi
            # 대화형 모드: prompt (디폴트 N)
            read -r -p "릴리즈 자산 없음 — 무결성 검증 없이 진행하시겠습니까? [y/N] " unverified_confirm
            if [[ "$unverified_confirm" != "y" && "$unverified_confirm" != "Y" ]]; then
                error "사용자가 취소했습니다. 옵트인: OPAL_ALLOW_UNVERIFIED=1"
            fi
            warn "[UNVERIFIED] 사용자 동의로 무결성 검증 없이 진행"
            ;;
        branch)
            # 브랜치 설치 — UNVERIFIED 배너는 main()에서 이미 출력했다 (RG-3). 중복 출력하지 않는다.
            info "브랜치 설치 — SHA-256 무결성 검증 대상 아님"
            ;;
        *)
            # [MUST] 계약 3종(verify/unverified/branch) 밖의 값은 무음 통과가 아니라 하드 실패다 (D-6, fail-closed)
            error "체크섬 모드 값 이상: '${OPAL_CHECKSUM_MODE}' — DL-CONTRACT 위반. 설치를 중단합니다."
            ;;
    esac
}

# ─── extract_to_tmp ──────────────────────────────────────────────────────────
# tarball을 임시 디렉토리에 추출한다.
# 상위 디렉토리(prefix) 유무를 판정하여 strip을 적용한다 (§3.0 D-D) —
# 발행 자산은 prefix 없음(strip 0), 자동/브랜치 아카이브는 prefix 있음(strip 1).
extract_to_tmp() {
    OPAL_EXTRACT_DIR="${OPAL_TMP}/opal-extracted"
    mkdir -p "${OPAL_EXTRACT_DIR}"

    if [[ "${OPAL_DRY_RUN}" == "1" ]]; then
        warn "[DRY-RUN] extract_to_tmp 생략"
        return 0
    fi

    # [MUST] 목록 조회 가능 여부를 먼저 확정한다 (§3.0 D-D, O-5).
    #        _dl_detect_strip은 조회 실패 시에도 '0'을 출력하므로(입력 0줄 → root=0·tops=0 → 0),
    #        판정값만으로는 "prefix 없는 정상 자산"과 "손상 tarball"을 구분할 수 없다.
    #        선검사 없이는 손상 tarball이 무음으로 strip=0 경로를 타고, 뒤이은 사후조건 오류가 진짜 원인을 가린다.
    if ! tar -tzf "${OPAL_TARBALL}" >/dev/null 2>&1; then
        error "tarball 목록 조회 실패 — 손상되었거나 tar.gz 형식이 아닙니다: ${OPAL_TARBALL}"
    fi

    local strip_n
    strip_n="$(_dl_detect_strip "${OPAL_TARBALL}" || true)"
    # 판정값 자체도 검증한다 — awk 산출이 비거나 예상 밖 값이면 하드 실패 (무음 강등 차단).
    case "${strip_n}" in
        0|1) ;;
        *) error "tarball 구조 판정 실패 (strip 판정값: '${strip_n}') — 설치를 중단합니다." ;;
    esac
    info "tarball 추출 중... (strip-components=${strip_n})"

    if [[ "${strip_n}" -eq 1 ]]; then
        tar -xzf "${OPAL_TARBALL}" -C "${OPAL_EXTRACT_DIR}" --strip-components=1 \
            || error "tarball 추출 실패"
    else
        tar -xzf "${OPAL_TARBALL}" -C "${OPAL_EXTRACT_DIR}" \
            || error "tarball 추출 실패"
    fi

    # [MUST] 추출 사후조건 — 조용한 진행 금지 (§3.0 D-D)
    if [[ ! -f "${OPAL_EXTRACT_DIR}/VERSION" || ! -d "${OPAL_EXTRACT_DIR}/opal" ]]; then
        error "추출 결과 구조 이상 — VERSION 또는 opal/ 이 루트에 없습니다 (strip=${strip_n})"
    fi

    success "추출 완료: ${OPAL_EXTRACT_DIR}"
}

# ─── exec_platform_installer ─────────────────────────────────────────────────
# 플랫폼별 설치 스크립트를 실행한다.
# macOS: scripts/install/macos.sh
# Linux: scripts/install/linux.sh
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
        error "플랫폼 설치 스크립트를 찾을 수 없습니다: ${installer_path}"
    fi

    chmod +x "${installer_path}"

    info "${OPAL_PLATFORM} 설치 스크립트 실행 중..."
    # 추출된 소스 디렉토리를 REPO_ROOT로 전달하여 설치 스크립트가
    # 올바른 소스 경로를 참조할 수 있게 한다.
    export OPAL_SOURCE_DIR="${OPAL_EXTRACT_DIR}"
    exec bash "${installer_path}" "$@"
}

# ─── adopt_stamped_version ───────────────────────────────────────────────────
# 추출된 tarball의 VERSION이 치환되어 있으면(=$Format: 잔존 아님) 그 값을 채택.
# 미치환/부재면 기존 OPAL_VERSION(resolve_default_version 결과) 유지 → 폴백.
# bash 3.2 호환: case 패턴 사용, 연관배열 미사용.
# DRY-RUN 시 OPAL_EXTRACT_DIR는 빈 디렉토리 → [[ -f ]] false → no-op (안전).
adopt_stamped_version() {
    local vf="${OPAL_EXTRACT_DIR}/VERSION"
    [[ -f "$vf" ]] || return 0
    local stamped
    stamped="$(tr -d '[:space:]' < "$vf" 2>/dev/null || true)"
    [[ -z "$stamped" ]] && return 0
    case "$stamped" in
        *'$Format:'*) return 0 ;;   # 미치환 placeholder → 폴백 유지
    esac
    OPAL_VERSION="$stamped"
    export OPAL_VERSION
    info "tarball VERSION 각인값 채택: ${OPAL_VERSION} (API 미사용)"
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

    # detect_platform은 verify_checksum의 shasum/sha256sum 분기 전제 — 순서 유지 (§3.2.2)
    detect_platform
    check_deps
    prepare_tmp
    resolve_download_plan
    fetch_tarball
    verify_checksum
    extract_to_tmp
    adopt_stamped_version
    exec_platform_installer "$@"
}

main "$@"
