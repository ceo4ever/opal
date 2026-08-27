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
#   v1.0.2 2026-05-09 21:05 KST: 로컬/리모트 버전 비교 + --force 옵션 — ~/.opal/VERSION 읽어 같은 release tag(v*)면 "이미 최신" 안내 후 종료. main/SHA/미기록은 항상 진행 (139 추가작업)
#   v1.0.3 2026-05-09 22:00 KST: /releases/latest 실패 시 /tags?per_page=1 폴백 + tarball URL을 archive/refs/tags로 변경 (install.sh v1.2와 정합, release 자산 미생성 케이스 호환) (139 추가작업)
#   v1.0.4 2026-05-10 21:00 KST: verify_checksum 강화 — release tag + sha256sums.txt 부재 시 prompt/거부 + main UNVERIFIED banner (GC-001, R-2) (144)
#   v1.0.5 2026-06-29 15:24 KST: 추출 후 extract_dir/VERSION 각인값으로 version override — tarball VERSION 우선, API/main 폴백 강등 (048)
#   v1.0.6 2026-07-10 KST: 미설치 감지 시 안내를 신규 설치 원라이너로 교체 — install 서브커맨드 제거에 따른 순환 안내 방지 (055)
#   v1.0.7 2026-08-27 09:20 KST: 업데이트 성공 직후 릴리즈 노트 링크 안내 — version이 릴리즈 태그(v*)면 releases/tag/<version>, main/SHA면 releases 목록으로 분기(태그 페이지 404 방지). 출력 1블록 추가, 로직 무변경 (103 후속)
#   v1.1 2026-08-07 12:04 KST: DL-CONTRACT (085) 적용 — 다운로드 대상을 릴리즈 자산으로 전환, 체크섬 3분기(verify/unverified/branch) 하드닝(무음 통과·해시 도구 하드의존 제거), 추출 strip 자동 판정 + 사후조건 검사. 정합 fix: sha 항목 선택을 파일명 컬럼 정확 일치로 교정(상위문자열 오채택 차단, D-2) + 체크섬 case에 `*)` 하드 실패 분기 추가(모드값 이상 fail-closed, D-6). TEST fix: strip 판정값 검증 추가 — 빈 값·비수치 값을 그 지점에서 하드 실패로 거부(무음 강등 차단, O-5) (085)
#   v1.2 2026-08-08 21:52 KST: 체크섬 불일치 오류에 탈출 경로 안내 추가 — 우회 옵션은 제공하지 않되(무결성 유지), 원라이너 재설치·이슈 등록 경로를 출력하여 사용자가 막다른 길에 서지 않게 한다. 로컬 구버전 update.sh 결함으로 자가 갱신이 불가한 사용자(v0.6.0~v0.6.11)의 실제 이탈 사례 반영. 출력만 변경 — 검증·다운로드·추출 로직 무변경 (L2 경량)
#
# DL-CONTRACT (085): 릴리즈 태그는 릴리즈 자산 우선 + sha256sums.txt 부재 시 자동 아카이브 폴백(UNVERIFIED) + strip 자동 판정
#

# ─── DL-CONTRACT (085) 공통 헬퍼 ──────────────────────────────
#
# [MUST] _dl_asset_name / _dl_detect_strip 의 본문은 `scripts/install.sh` 와 **문자 단위로 동일**하게
#        유지한다 (PLAN §3.0 D-A 정합 수단 (a)). 한쪽만 수정하면 규약이 드리프트한다.
#        두 헬퍼는 외부 전역·로그 헬퍼에 의존하지 않는다 — tar / awk 만 사용한다.

# 다운로드 계획 전역 (_dl_resolve_plan / _dl_fallback 이 설정)
_DL_URL=""
_DL_NAME=""
_DL_MODE=""
_DL_SHA_FILE=""

# sha256 해시 계산 — 도구 이식성 흡수 (H-6). 둘 다 없으면 exit≠0 + 표준출력 공백.
_dl_sha256() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | awk '{print $1}'
    else
        return 1
    fi
}

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

# 자동 아카이브 폴백으로 강등 — $1=repo $2=version $3=사유
# [MUST] 폴백 경로에서는 sha256sums.txt를 어떤 경우에도 비교에 사용하지 않는다 (H-3).
_dl_fallback() {
    if [[ -n "${_DL_SHA_FILE:-}" ]]; then
        rm -f "$_DL_SHA_FILE" 2>/dev/null || true
    fi
    _DL_SHA_FILE=""
    _DL_URL="https://github.com/${1}/archive/refs/tags/${2}.tar.gz"
    _DL_NAME="opal-${2}-archive.tar.gz"
    _DL_MODE="unverified"
    warn "릴리즈 자산 미사용 폴백: ${3}"
}

# 다운로드 계획 수립 — $1=repo $2=version $3=tmp_dir (§3.0 D-C)
# 산출 전역: _DL_URL / _DL_NAME / _DL_MODE(verify|unverified|branch) / _DL_SHA_FILE
_dl_resolve_plan() {
    local repo="$1" version="$2" tmp_dir="$3"
    _DL_SHA_FILE=""

    if [[ "$version" != v* ]]; then
        _DL_URL="https://github.com/${repo}/archive/refs/heads/${version}.tar.gz"
        _DL_NAME="opal-${version}.tar.gz"
        _DL_MODE="branch"
        return 0
    fi

    # 릴리즈 자산 존재 판정: sha256sums.txt 다운로드 성공 여부가 단일 신호 (§3.0 D-B)
    local sha_url="https://github.com/${repo}/releases/download/${version}/sha256sums.txt"
    _DL_SHA_FILE="$tmp_dir/sha256sums.txt"
    if ! curl -fsSL --proto '=https' --tlsv1.2 -o "$_DL_SHA_FILE" "$sha_url" 2>/dev/null; then
        _dl_fallback "$repo" "$version" "릴리즈 자산 없음 (sha256sums.txt 조회 실패)"
        return 0
    fi

    # [MUST] 자산명은 하드코딩하지 않고 검증 대상 목록에서 파생한다 — 다운로드 대상 = 검증 대상
    local asset
    asset="$(_dl_asset_name "$_DL_SHA_FILE")"
    if [[ -z "$asset" ]]; then
        _dl_fallback "$repo" "$version" "sha256sums.txt 형식 이상 (.tar.gz 항목 없음)"
        return 0
    fi

    _DL_URL="https://github.com/${repo}/releases/download/${version}/${asset}"
    _DL_NAME="$asset"
    _DL_MODE="verify"
    return 0
}

# ─── update 서브커맨드 ────────────────────────────────────────

cmd_update() {
    local version=""
    local dry_run="${OPAL_DRY_RUN:-}"
    local force=0

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
            --force|-f)
                force=1
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

    # 로컬 설치 버전 읽기
    local local_version=""
    if [[ -f "$opal_home/VERSION" ]]; then
        local_version="$(tr -d '[:space:]' < "$opal_home/VERSION" 2>/dev/null || true)"
    fi
    [[ -z "$local_version" ]] && local_version="(미기록)"
    info "로컬 버전: $local_version"

    # 버전 미지정 시 자동 결정 (install.sh v1.2 resolve_default_version과 정합)
    #   1) /releases/latest (published release)
    #   2) 폴백: /tags?per_page=1 (release 자산 미생성 케이스 호환)
    #   3) 두 단계 모두 실패 시 "main" 폴백
    if [[ -z "$version" ]]; then
        info "최신 버전 확인 중..."
        if ! command -v curl &>/dev/null; then
            error "curl을 찾을 수 없습니다. curl을 설치 후 다시 시도하세요."
            return 1
        fi

        # 1차: /releases/latest
        local latest
        latest=$(curl -fsSL --proto '=https' --tlsv1.2 \
            "https://api.github.com/repos/${opal_repo}/releases/latest" \
            2>/dev/null | grep '"tag_name"' | head -1 | sed 's/.*"tag_name": "\([^"]*\)".*/\1/') || true

        # 2차 폴백: /tags?per_page=1
        if [[ -z "$latest" ]]; then
            latest=$(curl -fsSL --proto '=https' --tlsv1.2 \
                "https://api.github.com/repos/${opal_repo}/tags?per_page=1" \
                2>/dev/null | grep '"name"' | head -1 | sed 's/.*"name": "\([^"]*\)".*/\1/') || true
            if [[ -n "$latest" ]]; then
                info "리모트 최신 태그: $latest"
            fi
        else
            info "리모트 최신 release: $latest"
        fi

        if [[ -n "$latest" ]]; then
            version="$latest"
        else
            version="main"
            warn "최신 버전 확인 실패 — main 브랜치 tarball 사용"
        fi
    fi

    # 버전 비교: 로컬과 리모트가 같은 release tag(v*)이면 갱신 스킵
    # main / commit SHA / 미기록은 항상 진행 (정확한 비교 불가)
    if [[ "$force" -eq 0 ]] \
       && [[ "$local_version" == "$version" ]] \
       && [[ "$local_version" == v* ]]; then
        success "이미 최신 버전입니다 ($local_version)"
        info "강제 재설치: opal-cli update --to $version --force"
        return 0
    fi

    if [[ "$local_version" != "(미기록)" && "$version" != "main" && "$local_version" != "$version" ]]; then
        info "업데이트: $local_version → $version"
    fi

    info "업데이트 버전: $version"

    # [MUST] dry-run은 네트워크에 접근하지 않는다 (RG-8) — 계획 수립(_dl_resolve_plan) 이전에 종료한다.
    if [[ -n "$dry_run" ]]; then
        if [[ "$version" == v* ]]; then
            info "[dry-run] 다운로드 소스: releases/download/${version}/<sha256sums.txt 파생 자산명> (자산 부재 시 자동 아카이브 폴백)"
        else
            info "[dry-run] 다운로드 소스: ${version} 브랜치 아카이브 (UNVERIFIED)"
        fi
        info "[dry-run] 실제 다운로드 및 설치를 수행하지 않습니다."
        info "[dry-run] 보존 대상: identity.md, projects/, community-skills/, .venv/"
        info "[dry-run] 클린 대상: skills/, agents/, tools/"
        return 0
    fi

    # 사전 점검
    if [[ ! -d "$opal_home" ]]; then
        error "OPAL이 설치되어 있지 않습니다: $opal_home"
        info "신규 설치: curl -fsSL https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.sh | bash"
        info "  (Windows PowerShell) iex (irm https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.ps1)"
        return 1
    fi

    # 임시 디렉토리 생성
    local tmp_dir
    tmp_dir=$(mktemp -d)
    # shellcheck disable=SC2064
    trap "rm -rf '$tmp_dir'" EXIT

    # 다운로드 계획 수립 (§3.0 D-C) — 릴리즈 자산 우선, 자산 부재 시 자동 아카이브 폴백
    _dl_resolve_plan "$opal_repo" "$version" "$tmp_dir"
    info "다운로드 URL: $_DL_URL"

    info "tarball 다운로드 중..."
    local tarball_path="$tmp_dir/$_DL_NAME"
    if ! curl -fsSL --proto '=https' --tlsv1.2 -o "$tarball_path" "$_DL_URL"; then
        if [[ "$_DL_MODE" == "verify" ]]; then
            # 릴리즈 자산 다운로드 실패 — 폴백 1회 강등 후 재시도
            _dl_fallback "$opal_repo" "$version" "릴리즈 자산 다운로드 실패"
            tarball_path="$tmp_dir/$_DL_NAME"
            info "폴백 다운로드 URL: $_DL_URL"
            if ! curl -fsSL --proto '=https' --tlsv1.2 -o "$tarball_path" "$_DL_URL"; then
                error "tarball 다운로드 실패: $_DL_URL"
                return 1
            fi
        else
            error "tarball 다운로드 실패: $_DL_URL"
            return 1
        fi
    fi
    success "다운로드 완료"

    # 체크섬 정책 (§3.0 D-C) — verify / unverified / branch 3분기
    case "$_DL_MODE" in
        branch)
            # main 브랜치 UNVERIFIED banner (release tag 외 모든 버전) (R-2, GC-001, RG-3)
            warn "[UNVERIFIED] '${version}' 브랜치 업데이트 — SHA-256 무결성 검증 없음. 공식 릴리스(v*)를 권장합니다."
            ;;
        verify)
            info "체크섬 검증 중..."
            # [MUST] 고정 문자열 매칭 — 파일명의 '.'이 정규식 와일드카드로 해석되는 오매칭 차단 (H-9)
            # [MUST] grep -F 는 부분문자열 매칭이므로 전(前)필터로만 쓰고, 파일명 컬럼($2, binary mode '*' 제거)
            #        정확 일치로 항목을 확정한다 — 상위문자열 항목(예: {자산}.tar.gz.sig)이 먼저 와도
            #        그 행을 채택하지 않는다 (D-2). install.sh·install.ps1 과 동형.
            local sha_entry expected_hash actual_hash
            sha_entry="$(grep -F -- "$_DL_NAME" "$_DL_SHA_FILE" \
                | awk -v want="$_DL_NAME" '{ n = $2; sub(/^\*/, "", n); if (n == want) { print; exit } }' || true)"
            if [[ -z "$sha_entry" ]]; then
                error "sha256sums.txt에 ${_DL_NAME} 항목 없음 — DL-CONTRACT 위반. 업데이트를 중단합니다."
                return 1
            fi
            expected_hash="$(printf '%s\n' "$sha_entry" | awk '{print $1}')"
            # [MUST] 기대값 공백은 무음 통과가 아니라 하드 실패다 (H-10)
            if [[ -z "$expected_hash" ]]; then
                error "체크섬 기대값 파싱 실패 — sha256sums.txt 형식 이상. 업데이트를 중단합니다."
                return 1
            fi
            actual_hash="$(_dl_sha256 "$tarball_path" || true)"
            if [[ -z "$actual_hash" ]]; then
                error "sha256 계산 도구(sha256sum/shasum)를 찾을 수 없습니다. 업데이트를 중단합니다."
                return 1
            fi
            if [[ "$actual_hash" != "$expected_hash" ]]; then
                error "체크섬 불일치! 다운로드가 손상되었을 수 있습니다."
                error "  기대값: $expected_hash"
                error "  실제값: $actual_hash"
                # 무결성 보호를 위해 우회 옵션은 제공하지 않는다. 대신 사용자가 막다른 길에
                # 서지 않도록 탈출 경로를 안내한다 — 원라이너는 main의 최신 인스톨러를 매번
                # 새로 받아 실행하므로, 로컬에 깔린 구버전 update.sh의 결함에 영향받지 않는다.
                info "다시 실행해도 같은 오류가 나면 최신 인스톨러로 재설치하십시오:"
                info "  curl -fsSL https://raw.githubusercontent.com/${opal_repo}/main/scripts/install.sh | bash"
                info "  (Windows PowerShell) iex (irm https://raw.githubusercontent.com/${opal_repo}/main/scripts/install.ps1)"
                info "해결되지 않으면 이슈로 알려주십시오: https://github.com/${opal_repo}/issues"
                return 1
            fi
            success "체크섬 검증 완료"
            ;;
        unverified)
            # 릴리즈 자산 미사용 — 무결성 검증 불가 (R-2, RG-4: 옵트인 / 비대화형 거부 / 프롬프트)
            if [[ "${OPAL_ALLOW_UNVERIFIED:-}" == "1" ]]; then
                warn "[UNVERIFIED] 릴리즈 자산 없음 — OPAL_ALLOW_UNVERIFIED=1로 무결성 검증 없이 진행"
            elif [[ ! -t 0 ]] || [[ "${OPAL_AUTO_INSTALL:-}" == "1" ]]; then
                error "릴리즈 자산 없음 — 비대화형 모드에서 무결성 검증 없는 업데이트를 거부합니다. 옵트인: OPAL_ALLOW_UNVERIFIED=1"
                return 1
            else
                read -r -p "릴리즈 자산 없음 — 무결성 검증 없이 진행하시겠습니까? [y/N] " unverified_confirm
                if [[ "$unverified_confirm" != "y" && "$unverified_confirm" != "Y" ]]; then
                    error "사용자가 취소했습니다. 옵트인: OPAL_ALLOW_UNVERIFIED=1"
                    return 1
                fi
                warn "[UNVERIFIED] 사용자 동의로 무결성 검증 없이 진행"
            fi
            ;;
        *)
            # [MUST] 계약 3종(verify/unverified/branch) 밖의 값은 무음 통과가 아니라 하드 실패다 (D-6, fail-closed)
            error "체크섬 모드 값 이상: '${_DL_MODE}' — DL-CONTRACT 위반. 업데이트를 중단합니다."
            return 1
            ;;
    esac

    # tarball 압축 해제 — 상위 디렉토리 유무를 판정하여 strip 적용 (§3.0 D-D)
    local extract_dir="$tmp_dir/opal-src"
    mkdir -p "$extract_dir"
    # [MUST] 목록 조회 가능 여부를 먼저 확정한다 (§3.0 D-D, O-5).
    #        _dl_detect_strip은 조회 실패 시에도 '0'을 출력하므로(입력 0줄 → root=0·tops=0 → 0),
    #        판정값만으로는 "prefix 없는 정상 자산"과 "손상 tarball"을 구분할 수 없다.
    #        선검사 없이는 손상 tarball이 무음으로 strip=0 경로를 타고, 뒤이은 사후조건 오류가 진짜 원인을 가린다.
    if ! tar -tzf "$tarball_path" >/dev/null 2>&1; then
        error "tarball 목록 조회 실패 — 손상되었거나 tar.gz 형식이 아닙니다: $tarball_path"
        return 1
    fi

    local strip_n
    strip_n="$(_dl_detect_strip "$tarball_path" || true)"
    # 판정값 자체도 검증한다 — awk 산출이 비거나 예상 밖 값이면 하드 실패 (무음 강등 차단).
    case "$strip_n" in
        0|1) ;;
        *)
            error "tarball 구조 판정 실패 (strip 판정값: '${strip_n}') — 업데이트를 중단합니다."
            return 1
            ;;
    esac
    info "압축 해제 중... (strip-components=${strip_n})"
    if [[ "$strip_n" -eq 1 ]]; then
        tar -xzf "$tarball_path" -C "$extract_dir" --strip-components=1 || {
            error "tarball 추출 실패: $tarball_path"
            return 1
        }
    else
        tar -xzf "$tarball_path" -C "$extract_dir" || {
            error "tarball 추출 실패: $tarball_path"
            return 1
        }
    fi
    # [MUST] 추출 사후조건 — 조용한 진행 금지 (§3.0 D-D)
    if [[ ! -f "$extract_dir/VERSION" || ! -d "$extract_dir/opal" ]]; then
        error "추출 결과 구조 이상 — VERSION 또는 opal/ 이 루트에 없습니다 (strip=${strip_n})"
        return 1
    fi
    success "압축 해제 완료"

    # 각인 VERSION 우선 — install.sh adopt_stamped_version과 동일 원칙 (048)
    # 추출된 tarball의 VERSION이 치환되어 있으면(=$Format: 잔존 아님) 그 값으로 version override.
    # bash 3.2 호환: case 패턴 사용.
    if [[ -f "$extract_dir/VERSION" ]]; then
        local _stamped
        _stamped="$(tr -d '[:space:]' < "$extract_dir/VERSION" 2>/dev/null || true)"
        case "$_stamped" in
            ''|*'$Format:'*) : ;;          # 부재/미치환 → version 유지(폴백)
            *) version="$_stamped"
               info "tarball VERSION 각인값 채택: ${version} (API 미사용)" ;;
        esac
    fi

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
    # OPAL_VERSION="$version" — install-mac.sh가 ~/.opal/VERSION에 기록하는 버전 (다음 update 비교 기준).
    OPAL_AUTO_INSTALL=1 OPAL_VERSION="$version" FRAMEWORK_ROOT="$extract_dir" bash "$installer"
    success "업데이트 완료 ($version)"

    # 릴리즈 노트 링크 — 무엇이 바뀌었는지 바로 확인할 수 있게 안내한다.
    # version이 릴리즈 태그(v*)면 해당 태그 페이지로, main/SHA 등 태그가 아니면
    # 릴리즈 목록으로 보낸다(태그 페이지가 404가 되지 않도록).
    if [[ "$version" == v* ]]; then
        info "릴리즈 노트: https://github.com/${opal_repo}/releases/tag/${version}"
    else
        info "릴리즈 노트: https://github.com/${opal_repo}/releases"
    fi
}

_update_usage() {
    cat <<EOF
사용법: opal-cli update [--to vX.Y] [--dry-run] [--force] [--help]

GitHub Releases에서 최신 OPAL을 다운로드하여 업데이트합니다.
사용자 데이터(identity.md, projects/, community-skills/)는 보존됩니다.

버전 비교:
  로컬 ~/.opal/VERSION 과 리모트 latest tag를 비교합니다.
  같은 release tag(v*)이면 "이미 최신" 안내 후 종료합니다.
  main / commit SHA / 미기록 상태는 항상 갱신을 진행합니다.

옵션:
  --to vX.Y     특정 버전으로 핀 (예: --to v0.2.1)
  --dry-run     실제 다운로드 없이 동작 확인
  --force, -f   같은 버전이라도 강제 재설치
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
