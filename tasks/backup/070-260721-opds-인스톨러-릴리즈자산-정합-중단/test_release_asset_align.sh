#!/usr/bin/env bash
# =============================================================================
# test_release_asset_align.sh — 인스톨러 3종 릴리즈-자산 다운로드 정합 테스트
# 태스크: 070 (인스톨러 릴리즈자산 정합)
# 트랙: RED-first — 이 파일은 RED 단계(구현 전) 산출물.
#        (가) 저장소 계약 검증 TC-A*: RED 시점에 TC-A1·A3·A4 FAIL — 구현 후 GREEN.
#             TC-A2·A5·A6·A7은 현행 코드에서 이미 성립(회귀 방지 목적)하므로 RED 시점에도 PASS 예상.
#        (나) 메커니즘 검증 TC-B*:  RED 시점에도 PASS — tar 네이티브 동작 증명(네트워크 미의존).
#
# 검증 대상 소스 3종:
#   - opal/tools/opal-cli/lib/update.sh  (opal-cli update 서브커맨드)
#   - scripts/install.sh                 (macOS/Linux one-liner)
#   - scripts/install.ps1                (Windows one-liner)
#
# 실행: bash scripts/tests/test_release_asset_align.sh
# 종료 코드: 0 = 전체 통과, 1 = 실패 있음
# bash 3.2 호환 — 연관배열·mapfile 미사용, case 패턴 사용
# =============================================================================

set -euo pipefail
# REPO_ROOT: 이 스크립트 위치에서 두 단계 위(= opal 저장소 루트)
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

UPDATE_SH="$REPO_ROOT/opal/tools/opal-cli/lib/update.sh"
INSTALL_SH="$REPO_ROOT/scripts/install.sh"
INSTALL_PS1="$REPO_ROOT/scripts/install.ps1"
SELF_TEST="$REPO_ROOT/scripts/tests/test_release_asset_align.sh"

# ---------------- 유틸 ----------------
PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

pass() {
    PASS_COUNT=$((PASS_COUNT + 1))
    printf '[PASS] %s\n' "$1"
}

fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf '[FAIL] %s\n' "$1"
    if [ -n "${2:-}" ]; then
        printf '       detail: %s\n' "$2"
    fi
}

skip() {
    SKIP_COUNT=$((SKIP_COUNT + 1))
    printf '[SKIP] %s\n' "$1"
}

# ---------------- scratch 준비 (네트워크 미의존 — tarball fixture) ----------------
SCRATCH_DIR="$(mktemp -d)"
trap 'rm -rf "$SCRATCH_DIR"' EXIT

setup_scratch_tarballs() {
    # (a) flat tarball — 릴리즈 자산 모사: 최상위 prefix 없음
    local flat_src="$SCRATCH_DIR/flat_src"
    mkdir -p "$flat_src/subdir"
    printf 'v9.9.9-asset\n' > "$flat_src/VERSION"
    printf 'content\n' > "$flat_src/subdir/file.txt"
    # 명시적 엔트리 나열로 './' 접두 방지 (strip-components 시연을 정확히 하기 위함)
    tar -czf "$SCRATCH_DIR/flat.tar.gz" -C "$flat_src" VERSION subdir

    # (b) prefixed tarball — GitHub 소스아카이브 모사: 최상위 opal-9.9.9/ prefix 있음
    local prefixed_src="$SCRATCH_DIR/prefixed_src"
    mkdir -p "$prefixed_src/opal-9.9.9/subdir"
    printf 'v9.9.9-archive\n' > "$prefixed_src/opal-9.9.9/VERSION"
    printf 'content\n' > "$prefixed_src/opal-9.9.9/subdir/file.txt"
    tar -czf "$SCRATCH_DIR/prefixed.tar.gz" -C "$prefixed_src" opal-9.9.9
}

setup_scratch_tarballs

sha256_of() {
    if command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | awk '{print $1}'
    else
        sha256sum "$1" | awk '{print $1}'
    fi
}

# =============================================================================
# (가) 저장소 계약 검증 — RED 시점 TC-A1·A3·A4 FAIL 예상
# =============================================================================
printf '\n== (가) 저장소 계약 검증 (TC-A*) — RED 시점 TC-A1/A3/A4 FAIL 예상 ==\n\n'

# TC-A1 (S-1, H-1): 3종 소스에 릴리즈 자산 URL(releases/download/.../opal-*.tar.gz) 존재
TC="TC-A1 (S-1): 3종에 릴리즈 자산 URL(releases/download/.../opal-*.tar.gz) 존재"
missing=""
for f in "$UPDATE_SH" "$INSTALL_SH" "$INSTALL_PS1"; do
    if [ ! -f "$f" ]; then
        missing="$missing $f(미존재)"
        continue
    fi
    if ! grep -Eq 'releases/download/.*opal-.*\.tar\.gz' "$f" 2>/dev/null; then
        missing="$missing $(basename "$f")"
    fi
done
if [ -z "$missing" ]; then
    pass "$TC"
else
    fail "$TC" "자산 URL 패턴 미발견:$missing"
fi

# TC-A2 (S-1, H-1): 3종에 아카이브 폴백(archive/refs/tags) 잔존
TC="TC-A2 (S-1): 3종에 아카이브 폴백(archive/refs/tags) 잔존"
missing=""
for f in "$UPDATE_SH" "$INSTALL_SH" "$INSTALL_PS1"; do
    if [ ! -f "$f" ]; then
        missing="$missing $f(미존재)"
        continue
    fi
    if ! grep -Eq 'archive/refs/tags' "$f" 2>/dev/null; then
        missing="$missing $(basename "$f")"
    fi
done
if [ -z "$missing" ]; then
    pass "$TC"
else
    fail "$TC" "아카이브 폴백 패턴 미발견:$missing"
fi

# TC-A3 (S-3, H-2): 3종에 소스 기반 strip 분기 존재
# strip-components 사용 근방(최대 10줄 이전)에 'asset' 마커가 존재해야
# "무조건 strip"이 아닌 "소스 판정 기반 조건부 strip"으로 간주한다.
TC="TC-A3 (S-3): 3종에 소스 기반 strip 분기(asset=no-strip / archive=strip) 존재"
missing=""
for f in "$UPDATE_SH" "$INSTALL_SH" "$INSTALL_PS1"; do
    if [ ! -f "$f" ]; then
        missing="$missing $f(미존재)"
        continue
    fi
    if ! grep -q 'strip-components' "$f" 2>/dev/null; then
        missing="$missing $(basename "$f")(strip-components 없음)"
        continue
    fi
    context="$(grep -n -B10 'strip-components' "$f" 2>/dev/null || true)"
    if ! printf '%s' "$context" | grep -qi 'asset'; then
        missing="$missing $(basename "$f")(asset 조건부 분기 미발견 — 무조건 strip으로 추정)"
    fi
done
if [ -z "$missing" ]; then
    pass "$TC"
else
    fail "$TC" "$missing"
fi

# TC-A4 (S-4, H-3): 로컬 tarball 파일명 / 검증 token 정합
TC="TC-A4 (S-4): install.sh 로컬명 opal-\${OPAL_VERSION}.tar.gz / update.sh 검증 token opal-\${version}.tar.gz / ps1 로컬명 opal-\$OpalVersion.tar.gz"
missing=""
if [ ! -f "$INSTALL_SH" ]; then
    missing="$missing install.sh(미존재)"
elif ! grep -Eq 'opal-\$\{?OPAL_VERSION\}?\.tar\.gz' "$INSTALL_SH" 2>/dev/null; then
    missing="$missing install.sh(opal-\${OPAL_VERSION}.tar.gz 패턴 없음 — 로컬 tarball명 미정합)"
fi
if [ ! -f "$UPDATE_SH" ]; then
    missing="$missing update.sh(미존재)"
elif ! grep -Eq 'opal-\$\{?version\}?\.tar\.gz' "$UPDATE_SH" 2>/dev/null; then
    missing="$missing update.sh(opal-\${version}.tar.gz 검증 token 없음)"
fi
if [ ! -f "$INSTALL_PS1" ]; then
    missing="$missing install.ps1(미존재)"
elif ! grep -Eq 'opal-\$OpalVersion\.tar\.gz' "$INSTALL_PS1" 2>/dev/null; then
    missing="$missing install.ps1(opal-\$OpalVersion.tar.gz 패턴 없음)"
fi
if [ -z "$missing" ]; then
    pass "$TC"
else
    fail "$TC" "$missing"
fi

# TC-A5 (S-2, H-4): 3종에 UNVERIFIED 배너 + OPAL_ALLOW_UNVERIFIED + 비대화형 거부 존재
TC="TC-A5 (S-2): 3종에 UNVERIFIED 배너 + OPAL_ALLOW_UNVERIFIED + 비대화형 거부 존재"
missing=""
for f in "$UPDATE_SH" "$INSTALL_SH" "$INSTALL_PS1"; do
    if [ ! -f "$f" ]; then
        missing="$missing $f(미존재)"
        continue
    fi
    found_banner=0
    found_optin=0
    found_reject=0
    if grep -qi 'UNVERIFIED' "$f" 2>/dev/null; then
        found_banner=1
    fi
    if grep -q 'OPAL_ALLOW_UNVERIFIED' "$f" 2>/dev/null; then
        found_optin=1
    fi
    if grep -q 'OPAL_AUTO_INSTALL' "$f" 2>/dev/null; then
        found_reject=1
    fi
    if [ "$found_banner" -eq 0 ] || [ "$found_optin" -eq 0 ] || [ "$found_reject" -eq 0 ]; then
        missing="$missing $(basename "$f")(banner=$found_banner optin=$found_optin reject=$found_reject)"
    fi
done
if [ -z "$missing" ]; then
    pass "$TC"
else
    fail "$TC" "$missing"
fi

# TC-A6 (S-5, H-5): 비-v* 경로 archive/refs/heads 잔존 (회귀)
TC="TC-A6 (S-5): 비-v* 경로 archive/refs/heads 잔존(회귀)"
missing=""
for f in "$UPDATE_SH" "$INSTALL_SH" "$INSTALL_PS1"; do
    if [ ! -f "$f" ]; then
        missing="$missing $f(미존재)"
        continue
    fi
    if ! grep -Eq 'archive/refs/heads' "$f" 2>/dev/null; then
        missing="$missing $(basename "$f")"
    fi
done
if [ -z "$missing" ]; then
    pass "$TC"
else
    fail "$TC" "$missing"
fi

# TC-A7 (S-6, H-7): 변경 대상 3종 + 신규 테스트 파일 시크릿 패턴 스캔
# (test_version_stamp.sh 시크릿 스캔 블록 패턴 재사용)
TC="TC-A7 (S-6): 변경 대상 3종 + 신규 테스트에 시크릿 패턴 없음"
SECRET_PATTERN='ghp_[0-9A-Za-z]\{36\}\|AKIA[0-9A-Z]\{16\}\|-----BEGIN [A-Z ]*PRIVATE KEY\|password=[^$][^{]'
SCAN_FILES=""
for f in "$UPDATE_SH" "$INSTALL_SH" "$INSTALL_PS1" "$SELF_TEST"; do
    if [ -f "$f" ]; then
        SCAN_FILES="$SCAN_FILES $f"
    fi
done
if [ -z "$SCAN_FILES" ]; then
    skip "$TC (스캔 대상 파일 없음)"
else
    # word split 의도적 사용 (파일 목록)
    # shellcheck disable=SC2086
    # SECRET_PATTERN= 정의 라인 자체(자기참조 오탐)는 스캔 결과에서 제외한다.
    secret_hits="$(grep -n "$SECRET_PATTERN" $SCAN_FILES 2>/dev/null | grep -v 'SECRET_PATTERN=' || true)"
    if [ -z "$secret_hits" ]; then
        pass "$TC"
    else
        fail "$TC" "시크릿 패턴 발견:\n$secret_hits"
    fi
fi

# =============================================================================
# (나) 메커니즘 검증 (scratch tarball) — RED 시점에도 PASS 예상
# =============================================================================
printf '\n== (나) 메커니즘 검증 (TC-B*, scratch tarball) — RED 시점에도 PASS 예상 ==\n\n'

# TC-B1 (S-3, H-2): flat tarball(자산 모사)을 --strip-components=1로 풀면 최상위 파일 유실 / no-strip이면 온전
TC="TC-B1 (S-3): flat tarball --strip-components=1 시 최상위 파일 유실, no-strip 시 온전"
STRIP_DIR="$SCRATCH_DIR/flat_stripped"
NOSTRIP_DIR="$SCRATCH_DIR/flat_nostripped"
mkdir -p "$STRIP_DIR" "$NOSTRIP_DIR"
tar -xzf "$SCRATCH_DIR/flat.tar.gz" -C "$STRIP_DIR" --strip-components=1 2>/dev/null || true
tar -xzf "$SCRATCH_DIR/flat.tar.gz" -C "$NOSTRIP_DIR" 2>/dev/null || true
if [ ! -f "$STRIP_DIR/VERSION" ] && [ -f "$NOSTRIP_DIR/VERSION" ]; then
    pass "$TC"
else
    fail "$TC" "strip 유무 결과 예상과 다름 — strip 후 VERSION 존재: $([ -f "$STRIP_DIR/VERSION" ] && echo yes || echo no), no-strip 후 VERSION 존재: $([ -f "$NOSTRIP_DIR/VERSION" ] && echo yes || echo no)"
fi

# TC-B2 (S-3, H-2): prefixed tarball(아카이브 모사)을 --strip-components=1로 풀면 최상위 파일 온전 배치
TC="TC-B2 (S-3): prefixed tarball --strip-components=1 시 최상위 파일 온전 배치"
PREFIXED_STRIP_DIR="$SCRATCH_DIR/prefixed_stripped"
mkdir -p "$PREFIXED_STRIP_DIR"
tar -xzf "$SCRATCH_DIR/prefixed.tar.gz" -C "$PREFIXED_STRIP_DIR" --strip-components=1 2>/dev/null || true
if [ -f "$PREFIXED_STRIP_DIR/VERSION" ] && [ -f "$PREFIXED_STRIP_DIR/subdir/file.txt" ]; then
    pass "$TC"
else
    fail "$TC" "strip 후 최상위 파일 미배치 — VERSION 존재: $([ -f "$PREFIXED_STRIP_DIR/VERSION" ] && echo yes || echo no)"
fi

# TC-B3 (S-4, H-3): flat tarball과 prefixed tarball의 sha256이 서로 다름 (근본 원인 재현)
TC="TC-B3 (S-4): flat/prefixed tarball sha256 불일치 실증"
flat_sha="$(sha256_of "$SCRATCH_DIR/flat.tar.gz")"
prefixed_sha="$(sha256_of "$SCRATCH_DIR/prefixed.tar.gz")"
if [ -n "$flat_sha" ] && [ -n "$prefixed_sha" ] && [ "$flat_sha" != "$prefixed_sha" ]; then
    pass "$TC"
else
    fail "$TC" "flat=$flat_sha prefixed=$prefixed_sha (동일하면 실증 실패)"
fi

# =============================================================================
# 최종 요약
# =============================================================================
printf '\n========================================================\n'
printf 'PASS: %d | FAIL: %d | SKIP: %d\n' "$PASS_COUNT" "$FAIL_COUNT" "$SKIP_COUNT"
printf '========================================================\n'

if [ "$FAIL_COUNT" -gt 0 ]; then
    printf 'verdict: FAIL (%d failures)\n' "$FAIL_COUNT"
    exit 1
else
    printf 'verdict: ALL PASS\n'
    exit 0
fi
