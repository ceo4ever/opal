#!/usr/bin/env bash
# =============================================================================
# test_version_stamp.sh — 버전 아카이브 각인(export-subst) 회귀 테스트
# 태스크: 048 (버전을 릴리스 아카이브에 각인)
# 트랙: RED-first — 이 파일은 RED 단계(구현 전) 산출물.
#        (가) 저장소 계약 검증 TC-A*: RED 시점에 FAIL — 구현 후 GREEN.
#        (나) 메커니즘 검증 TC-B*:  RED 시점에도 PASS — git 네이티브 동작 증명.
#
# 실행: bash scripts/tests/test_version_stamp.sh
# 종료 코드: 0 = 전체 통과, 1 = 실패 있음
# bash 3.2 호환 — 연관배열·mapfile 미사용, case 패턴 사용
# =============================================================================

set -euo pipefail
# REPO_ROOT: 이 스크립트 위치에서 두 단계 위(= ai-framework 저장소 루트)
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

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

# ---------------- scratch repo 준비 ----------------
SCRATCH_DIR="$(mktemp -d)"
trap 'rm -rf "$SCRATCH_DIR"' EXIT

setup_scratch_repo() {
    # scratch git repo 초기화 (TC-B*)
    local repo="$SCRATCH_DIR/repo"
    mkdir -p "$repo"
    git -C "$repo" init -q
    git -C "$repo" config user.email "test@example.com"
    git -C "$repo" config user.name "Test"

    # VERSION 파일 (export-subst placeholder)
    printf '$Format:%%(describe:tags)$' > "$repo/VERSION"

    # .gitattributes (export-subst 설정)
    printf 'VERSION export-subst\n' > "$repo/.gitattributes"

    # 초기 커밋 + 태그
    git -C "$repo" add VERSION .gitattributes
    git -C "$repo" commit -q -m "init"
    git -C "$repo" tag v9.9.9

    echo "$repo"
}

SCRATCH_REPO="$(setup_scratch_repo)"

# =============================================================================
# (가) 저장소 계약 검증 — RED 시점 FAIL 대상
# =============================================================================
printf '\n== (가) 저장소 계약 검증 (TC-A*) — RED 시점 FAIL 예상 ==\n\n'

# TC-A1 (S-2): .gitattributes에 VERSION export-subst 설정 존재 확인
TC="TC-A1 (S-2): git check-attr export-subst VERSION = set"
actual_subst="$(git -C "$REPO_ROOT" check-attr export-subst -- VERSION 2>/dev/null || true)"
case "$actual_subst" in
    *": set")
        pass "$TC"
        ;;
    *)
        fail "$TC" "got: $actual_subst  (expected: '...VERSION: export-subst: set')"
        ;;
esac

# TC-A2 (S-2): export-ignore는 unspecified이어야 함 (VERSION이 archive에 포함)
TC="TC-A2 (S-2): git check-attr export-ignore VERSION = unspecified"
actual_ignore="$(git -C "$REPO_ROOT" check-attr export-ignore -- VERSION 2>/dev/null || true)"
case "$actual_ignore" in
    *": unspecified")
        pass "$TC"
        ;;
    *)
        fail "$TC" "got: $actual_ignore  (expected: '...VERSION: export-ignore: unspecified')"
        ;;
esac

# TC-A3 (S-1): 루트 VERSION 파일 존재 + 내용 = $Format:%(describe:tags)$
TC="TC-A3 (S-1): 루트 VERSION 파일 존재 및 placeholder 내용 확인"
VERSION_FILE="$REPO_ROOT/VERSION"
if [ ! -f "$VERSION_FILE" ]; then
    fail "$TC" "VERSION file does not exist at $VERSION_FILE"
else
    version_content="$(tr -d '[:space:]' < "$VERSION_FILE" 2>/dev/null || true)"
    # bash 3.2 호환: case로 문자열 비교
    case "$version_content" in
        '$Format:%(describe:tags)$')
            pass "$TC"
            ;;
        *)
            fail "$TC" "content: '$version_content'  (expected: '\$Format:%(describe:tags)\$')"
            ;;
    esac
fi

# TC-A4 (S-1): VERSION이 git에 tracked(index 또는 HEAD에 존재) 되어 있는지 확인
# 설계 근거: export-subst 메커니즘 증명은 TC-B1(scratch repo)이 담당한다.
#   - TC-A1: export-subst attr 설정 확인
#   - TC-B1: scratch repo에서 태그 archive → 치환 증명
#   - TC-A4(여기): VERSION이 tracked 상태임을 확인
#   → 세 조건 합산으로 "장차 태그 archive에서 반드시 치환됨"이 보장된다.
# 메커니즘 증명은 TC-B1(scratch), 여기선 tracked+attr만 확인 —
# 실저장소 커밋 비강요(task 048 가드 준수)
TC="TC-A4 (S-1): VERSION이 git index에 tracked 되어 있음 (커밋 비강요)"
tracked="$(git -C "$REPO_ROOT" ls-files VERSION 2>/dev/null || true)"
if [ -n "$tracked" ]; then
    pass "$TC"
else
    fail "$TC" "VERSION is not tracked in git index (git ls-files VERSION returned empty)"
fi

# TC-A5 (S-5/S-7): install.sh에 adopt_stamped_version 함수 정의 + $Format: 판별 분기 존재
TC="TC-A5 (S-5/S-7): install.sh adopt_stamped_version 함수 및 Format: 판별 분기 존재"
INSTALL_SH="$REPO_ROOT/scripts/install.sh"
if [ ! -f "$INSTALL_SH" ]; then
    skip "$TC (install.sh 미존재)"
else
    found_func=0
    found_branch=0
    if grep -q "adopt_stamped_version" "$INSTALL_SH" 2>/dev/null; then
        found_func=1
    fi
    # $Format: 판별 — bash case 또는 grep 분기 (리터럴 $ 이스케이프 무관하게 탐색)
    if grep -q 'Format:' "$INSTALL_SH" 2>/dev/null; then
        found_branch=1
    fi
    if [ "$found_func" -eq 1 ] && [ "$found_branch" -eq 1 ]; then
        pass "$TC"
    elif [ "$found_func" -eq 0 ]; then
        fail "$TC" "adopt_stamped_version function not found in install.sh"
    else
        fail "$TC" "adopt_stamped_version exists but \$Format: detection branch not found"
    fi
fi

# TC-A6 (S-6): install-mac.sh에 record_installed_version 함수 또는 FRAMEWORK_ROOT/VERSION 최상위 단계 존재
TC="TC-A6 (S-6): install-mac.sh VERSION 기록 우선순위 재배치 (각인값 최우선)"
INSTALL_MAC="$REPO_ROOT/scripts/install-mac.sh"
if [ ! -f "$INSTALL_MAC" ]; then
    skip "$TC (install-mac.sh 미존재)"
else
    found_record_func=0
    found_framework_version=0
    if grep -q "record_installed_version" "$INSTALL_MAC" 2>/dev/null; then
        found_record_func=1
    fi
    # FRAMEWORK_ROOT/VERSION 참조 + placeholder 판별 분기
    if grep -q "FRAMEWORK_ROOT/VERSION\|FRAMEWORK_ROOT.*VERSION" "$INSTALL_MAC" 2>/dev/null; then
        found_framework_version=1
    fi
    # Format: 판별 분기도 있어야 함
    found_format_branch=0
    if grep -q 'Format:' "$INSTALL_MAC" 2>/dev/null; then
        found_format_branch=1
    fi

    if [ "$found_record_func" -eq 1 ] || { [ "$found_framework_version" -eq 1 ] && [ "$found_format_branch" -eq 1 ]; }; then
        pass "$TC"
    else
        fail "$TC" "record_installed_version not found AND FRAMEWORK_ROOT/VERSION+Format: branch not found in install-mac.sh (VERSION 기록 우선순위 미전환)"
    fi
fi

# TC-A7 (S-9): install.ps1에 추출 후 VERSION 읽기 + -notlike '*$Format:*' 판별 분기 존재
TC="TC-A7 (S-9): install.ps1 추출 후 VERSION 읽기 및 -notlike Format: 판별 분기 존재"
INSTALL_PS1="$REPO_ROOT/scripts/install.ps1"
if [ ! -f "$INSTALL_PS1" ]; then
    skip "$TC (install.ps1 미존재)"
else
    found_version_read=0
    found_notlike=0
    # $extractDir/VERSION 또는 extractDir.*VERSION 패턴
    if grep -q 'extractDir.*VERSION\|VERSION.*extractDir\|extractDir/VERSION' "$INSTALL_PS1" 2>/dev/null; then
        found_version_read=1
    fi
    # -notlike '*$Format:*' 판별
    if grep -q 'notlike.*Format:\|Format:.*notlike' "$INSTALL_PS1" 2>/dev/null; then
        found_notlike=1
    fi
    if [ "$found_version_read" -eq 1 ] && [ "$found_notlike" -eq 1 ]; then
        pass "$TC"
    elif [ "$found_version_read" -eq 0 ]; then
        fail "$TC" "extractDir/VERSION read not found in install.ps1"
    else
        fail "$TC" "-notlike '*\$Format:*' detection branch not found in install.ps1"
    fi
fi

# TC-A8 (S-10): 변경 대상 파일에 시크릿 패턴 없음 (보안 스캔)
TC="TC-A8 (S-10): 변경 대상 파일에 시크릿 패턴 없음"
SECRET_PATTERN='ghp_[0-9A-Za-z]\{36\}\|AKIA[0-9A-Z]\{16\}\|-----BEGIN [A-Z ]*PRIVATE KEY\|password=[^$][^{]'
SCAN_FILES=""
for f in "$REPO_ROOT/VERSION" \
         "$REPO_ROOT/.gitattributes" \
         "$REPO_ROOT/scripts/install.sh" \
         "$REPO_ROOT/scripts/install-mac.sh" \
         "$REPO_ROOT/scripts/install.ps1" \
         "$REPO_ROOT/opal/tools/opal-cli/lib/update.sh"; do
    if [ -f "$f" ]; then
        SCAN_FILES="$SCAN_FILES $f"
    fi
done
if [ -z "$SCAN_FILES" ]; then
    skip "$TC (스캔 대상 파일 없음)"
else
    # word split 의도적 사용 (파일 목록)
    # shellcheck disable=SC2086
    secret_hits="$(grep -n "$SECRET_PATTERN" $SCAN_FILES 2>/dev/null || true)"
    if [ -z "$secret_hits" ]; then
        pass "$TC"
    else
        fail "$TC" "시크릿 패턴 발견:\n$secret_hits"
    fi
fi

# =============================================================================
# (나) 메커니즘 검증 (scratch repo) — RED 시점에도 PASS, git 네이티브 동작 증명
# =============================================================================
printf '\n== (나) 메커니즘 검증 (TC-B*, scratch repo) — RED 시점에도 PASS 예상 ==\n\n'

# TC-B1 (S-1): 태그 archive → 실태그 각인 확인
TC="TC-B1 (S-1): scratch repo 태그 archive에서 VERSION = v9.9.9"
b1_out="$(git -C "$SCRATCH_REPO" archive --format=tar v9.9.9 | tar -xO VERSION 2>/dev/null || true)"
case "$b1_out" in
    "v9.9.9")
        pass "$TC"
        ;;
    *)
        fail "$TC" "got: '$b1_out'  (expected: 'v9.9.9')"
        ;;
esac

# TC-B2 (S-3): 태그 후 커밋 1개 추가 → HEAD archive = v9.9.9-1-g<sha> 형식
TC="TC-B2 (S-3): 태그 후 커밋 추가 시 HEAD archive VERSION = v9.9.9-N-g<sha>"
# 커밋 추가
printf 'extra\n' > "$SCRATCH_REPO/extra.txt"
git -C "$SCRATCH_REPO" add extra.txt
git -C "$SCRATCH_REPO" commit -q -m "extra commit"

b2_out="$(git -C "$SCRATCH_REPO" archive --format=tar HEAD | tar -xO VERSION 2>/dev/null || true)"
# v9.9.9-N-gSHA 형식 검증 (정규식: bash 3.2에서는 grep 사용)
if printf '%s' "$b2_out" | grep -qE '^v9\.9\.9-[0-9]+-g[0-9a-f]+$' 2>/dev/null; then
    pass "$TC"
else
    fail "$TC" "got: '$b2_out'  (expected pattern: v9.9.9-N-g<sha>)"
fi

# TC-B3 (S-4): scratch 작업트리 cat VERSION = placeholder (미치환)
TC="TC-B3 (S-4): scratch 작업트리 cat VERSION = placeholder 미치환"
wt_content="$(cat "$SCRATCH_REPO/VERSION" 2>/dev/null || true)"
case "$wt_content" in
    *'$Format:'*)
        pass "$TC"
        ;;
    *)
        fail "$TC" "got: '$wt_content'  (expected placeholder '\$Format:...')"
        ;;
esac

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
