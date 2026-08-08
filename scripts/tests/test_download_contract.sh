#!/usr/bin/env bash
# =============================================================================
# test_download_contract.sh — DL-CONTRACT (085) 다운로드·검증·추출 규약 테스트
# 태스크: 085 (릴리즈 체크섬 검증 경로 정합 — 다운로드 대상과 검증 대상 일치)
# 트랙: RED-first — 이 파일은 RED 단계(구현 전) 산출물이며, 구현(GREEN)은 별도 워커가 담당한다.
#        (가) 헬퍼 함수 계약 TC-A*  (S-1·S-2·S-6): RED 시점 FAIL — 헬퍼 4종이 아직 없다.
#        (나) 추출·체크섬 행위 TC-B* (S-13·S-5):   RED 시점 대부분 FAIL — 현행은 strip 고정 + 무음 통과.
#        (다) 정적 잔존 TC-C*        (S-3):        RED 시점 일부 FAIL — 교체 완결성 검사.
#
# 실행: bash scripts/tests/test_download_contract.sh
# 종료 코드: 0 = 전체 통과, 1 = 실패 있음
# bash 3.2 호환 — 연관배열(declare -A)·mapfile 미사용, case/awk 사용
#
# ── 헬퍼 로드 방식 근거 [MUST] ────────────────────────────────────────────────
# 대상 3파일은 실행 시 부수효과가 크다:
#   - scripts/install.sh          : 최상위에서 resolve_default_version() 즉시 실행(GitHub API 호출)
#                                   + 파일 말미 main "$@" 호출 → source 불가.
#   - opal/tools/opal-cli/lib/update.sh : cmd_update() 전 경로가 네트워크·~/.opal 파괴적 재설치.
#   - scripts/install.ps1         : pwsh 부재 환경 — 본 파일에서는 정적 검사만 수행(S-18은 별도).
# 따라서 파일에서 **해당 함수 정의 구간만 awk로 추출해 임시 하네스에 source**하는 방식을 택했다.
# 이 방식은 (a) 네트워크 0회 (b) 실사용 ~/.opal 미오염 (c) 함수의 공개 계약(반환값/exit code/표준출력)
# 만 검증한다는 red-first.md §4 요건을 동시에 만족한다. 내부 변수 상태에는 결합하지 않는다.
#
# ── 픽스처 정책 [MUST] ────────────────────────────────────────────────────────
# 네트워크 미사용. 아카이브는 `git archive`로 로컬 생성한다 (CI·오프라인 재현 가능).
#   A1 = prefix 없음  (발행 자산 등가) : git archive --format=tar.gz HEAD
#        → 실측 루트 직속 6·최상위 세그먼트 13 — TEST-SCENARIO.md §2.1 발행 자산 특성과 동일.
#   A2 = prefix 있음  (자동 아카이브 등가) : --prefix=opal-0.6.11/
#   A3 = prefix 있음  (main 아카이브 등가) : --prefix=opal-main/
#   A4 = 사후조건 위반(루트에 VERSION·opal/ 없음) — tar -czf로 직접 생성
# 대역 객체·모의 라이브러리·가짜 응답은 사용하지 않는다 (opal/core/PRINCIPLES.md §4).
#
# 시나리오 SSOT: tasks/085-260807-opds-릴리즈-체크섬-검증경로-정합/TEST-SCENARIO.md (S-1·S-2·S-3·S-5·S-6·S-13)
# 설계 SSOT:     tasks/085-260807-opds-릴리즈-체크섬-검증경로-정합/PLAN.md §3.0 DL-CONTRACT (D-B~D-F), §3.1.2, §3.2.2
#
# 변경이력:
#   v1.0 2026-08-07 신규 작성 — RED 단계 (opal-test-agent, mode: red) (085)
# =============================================================================

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
INSTALL_SH="$REPO_ROOT/scripts/install.sh"
INSTALL_PS1="$REPO_ROOT/scripts/install.ps1"
UPDATE_SH="$REPO_ROOT/opal/tools/opal-cli/lib/update.sh"
BASH_BIN="$(command -v bash)"

# ---------------- 유틸: pass/fail/skip 카운터 ----------------
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

# ---------------- 유틸: 함수 정의 구간 추출 ----------------
# extract_func <file> <func_name>  → stdout에 함수 정의 텍스트(없으면 공백)
# 지원 형식: `name() {` / `name () {` / `function name {` / 한 줄 정의 `name() { ...; }`
extract_func() {
    awk -v fn="$2" '
        BEGIN { inf = 0 }
        !inf {
            if ($0 ~ "^" fn "[[:space:]]*\\([[:space:]]*\\)[[:space:]]*\\{" ||
                $0 ~ "^function[[:space:]]+" fn "([[:space:]]*\\([[:space:]]*\\))?[[:space:]]*\\{") {
                inf = 1
                print
                # 한 줄 정의: 시작 줄이 } 로 끝나면 즉시 종료
                if ($0 ~ /\}[[:space:]]*$/) { exit }
                next
            }
            next
        }
        { print }
        /^\}/ { exit }
    ' "$1"
}

has_func() {
    [ -n "$(extract_func "$1" "$2")" ]
}

# ---------------- 픽스처 준비 ----------------
FIX="$(mktemp -d)"
trap 'rm -rf "$FIX"' EXIT

A1="$FIX/archive-noprefix.tar.gz"      # 발행 자산 등가 (prefix 없음)   → strip 0
A2="$FIX/archive-tagprefix.tar.gz"     # 자동 아카이브 등가             → strip 1
A3="$FIX/archive-mainprefix.tar.gz"    # main 아카이브 등가             → strip 1
A4="$FIX/archive-badroot.tar.gz"       # 사후조건 위반(VERSION·opal/ 부재)

FIXTURE_READY=1
git -C "$REPO_ROOT" archive --format=tar.gz -o "$A1" HEAD 2>/dev/null || FIXTURE_READY=0
git -C "$REPO_ROOT" archive --prefix=opal-0.6.11/ --format=tar.gz -o "$A2" HEAD 2>/dev/null || FIXTURE_READY=0
git -C "$REPO_ROOT" archive --prefix=opal-main/ --format=tar.gz -o "$A3" HEAD 2>/dev/null || FIXTURE_READY=0

mkdir -p "$FIX/badsrc"
printf 'no VERSION, no opal/ here\n' > "$FIX/badsrc/README.md"
(cd "$FIX/badsrc" && COPYFILE_DISABLE=1 tar -czf "$A4" README.md) 2>/dev/null || FIXTURE_READY=0

if [ "$FIXTURE_READY" -ne 1 ]; then
    printf '[ABORT] 아카이브 픽스처 생성 실패 — git archive / tar 확인 필요\n' >&2
    exit 1
fi

# sha256sums.txt 픽스처 — 실제 릴리즈 자산 형식(`<64hex>  <파일명>`) 그대로
ASSET_NAME="opal-v0.6.11.tar.gz"
SHA_TMP="$FIX/shatmp"                 # OPAL_TMP 역할 — 검증 대상 tarball과 sha 파일이 함께 놓이는 디렉토리
mkdir -p "$SHA_TMP"
cp "$A1" "$SHA_TMP/$ASSET_NAME"
REF_SHA="$(shasum -a 256 "$SHA_TMP/$ASSET_NAME" 2>/dev/null | awk '{print $1}')"
if [ -z "$REF_SHA" ]; then
    REF_SHA="$(sha256sum "$SHA_TMP/$ASSET_NAME" 2>/dev/null | awk '{print $1}')"
fi
if [ -z "$REF_SHA" ]; then
    printf '[ABORT] 기준 해시 계산 실패 — shasum/sha256sum 부재\n' >&2
    exit 1
fi

SHA_OK="$SHA_TMP/sha256sums.txt"
SHA_BINMODE="$FIX/sha256sums-binmode.txt"
SHA_NOENTRY="$FIX/sha256sums-noentry.txt"
SHA_BLANKHASH="$FIX/sha256sums-blankhash.txt"

printf '%s  %s\n' "$REF_SHA" "$ASSET_NAME" > "$SHA_OK"
printf '%s *%s\n' "$REF_SHA" "$ASSET_NAME" > "$SHA_BINMODE"
printf '%s  %s\n' "$REF_SHA" "sha256sums-source-notes.md" > "$SHA_NOENTRY"
printf '  %s\n' "$ASSET_NAME" > "$SHA_BLANKHASH"

# 플랫폼 판정 — install.sh detect_platform과 동일 값 계약(macos|linux)
case "$(uname -s)" in
    Darwin) PLATFORM="macos" ;;
    *)      PLATFORM="linux" ;;
esac

# ---------------- 유틸: 하네스 실행 ----------------
# run_harness <src_file> <call_snippet> <func...>  → HARNESS_OUT / HARNESS_RC 설정
HARNESS_OUT=""
HARNESS_RC=0
HARNESS_MISSING=""
run_harness() {
    local src="$1"; shift
    local snippet="$1"; shift
    local h="$FIX/harness.$$.sh"
    HARNESS_MISSING=""
    {
        printf '#!/usr/bin/env bash\n'
        printf 'set -euo pipefail\n'
        local fn
        for fn in "$@"; do
            if has_func "$src" "$fn"; then
                extract_func "$src" "$fn"
                printf '\n'
            else
                HARNESS_MISSING="$HARNESS_MISSING $fn"
            fi
        done
        printf '%s\n' "$snippet"
    } > "$h"
    HARNESS_RC=0
    HARNESS_OUT="$("$BASH_BIN" "$h" 2>&1)" || HARNESS_RC=$?
    rm -f "$h"
}

# =============================================================================
# (가) 헬퍼 함수 계약 — S-1 / S-2 / S-6
# =============================================================================
printf '\n== (가) 헬퍼 함수 계약 (TC-A*, S-1·S-2·S-6) — RED 시점 FAIL 예상 ==\n\n'

# ---- TC-A1: 헬퍼 정의 존재 (DL-CONTRACT 4종) ----
TC="TC-A1 (S-1/S-2/S-6): DL-CONTRACT 헬퍼 정의 존재 (update.sh 4종 / install.sh 2종+계획함수)"
missing=""
for fn in _dl_sha256 _dl_asset_name _dl_detect_strip _dl_resolve_plan; do
    has_func "$UPDATE_SH" "$fn" || missing="$missing update.sh:$fn"
done
for fn in _dl_asset_name _dl_detect_strip resolve_download_plan; do
    has_func "$INSTALL_SH" "$fn" || missing="$missing install.sh:$fn"
done
if [ -z "$missing" ]; then
    pass "$TC"
else
    fail "$TC" "미정의:$missing"
fi

# ---- TC-A2: update.sh _dl_detect_strip 3형식 판정 = 0 / 1 / 1 ----
TC="TC-A2 (S-1): update.sh _dl_detect_strip 3형식 판정 = 0 / 1 / 1"
if ! has_func "$UPDATE_SH" "_dl_detect_strip"; then
    fail "$TC" "update.sh에 _dl_detect_strip 정의 없음"
else
    run_harness "$UPDATE_SH" \
        "printf '%s %s %s\n' \"\$(_dl_detect_strip '$A1')\" \"\$(_dl_detect_strip '$A2')\" \"\$(_dl_detect_strip '$A3')\"" \
        _dl_detect_strip
    if [ "$HARNESS_RC" -ne 0 ]; then
        fail "$TC" "harness exit=$HARNESS_RC out='$HARNESS_OUT'"
    elif [ "$HARNESS_OUT" = "0 1 1" ]; then
        pass "$TC"
    else
        fail "$TC" "got: '$HARNESS_OUT'  (expected: '0 1 1')"
    fi
fi

# ---- TC-A3: install.sh _dl_detect_strip 3형식 판정 = 0 / 1 / 1 ----
TC="TC-A3 (S-1): install.sh _dl_detect_strip 3형식 판정 = 0 / 1 / 1"
if ! has_func "$INSTALL_SH" "_dl_detect_strip"; then
    fail "$TC" "install.sh에 _dl_detect_strip 정의 없음"
else
    run_harness "$INSTALL_SH" \
        "printf '%s %s %s\n' \"\$(_dl_detect_strip '$A1')\" \"\$(_dl_detect_strip '$A2')\" \"\$(_dl_detect_strip '$A3')\"" \
        _dl_detect_strip
    if [ "$HARNESS_RC" -ne 0 ]; then
        fail "$TC" "harness exit=$HARNESS_RC out='$HARNESS_OUT'"
    elif [ "$HARNESS_OUT" = "0 1 1" ]; then
        pass "$TC"
    else
        fail "$TC" "got: '$HARNESS_OUT'  (expected: '0 1 1')"
    fi
fi

# ---- TC-A4: 두 bash 파일의 _dl_detect_strip 본문 동일 (드리프트 차단, PLAN §3.0 D-A(a)) ----
TC="TC-A4 (S-1/D-A): install.sh·update.sh의 _dl_detect_strip 본문 동일"
body_u="$(extract_func "$UPDATE_SH" "_dl_detect_strip" | sed 's/[[:space:]]*$//')"
body_i="$(extract_func "$INSTALL_SH" "_dl_detect_strip" | sed 's/[[:space:]]*$//')"
if [ -z "$body_u" ] || [ -z "$body_i" ]; then
    fail "$TC" "한쪽 이상 미정의 (update.sh:$([ -n "$body_u" ] && echo O || echo X) install.sh:$([ -n "$body_i" ] && echo O || echo X))"
elif [ "$body_u" = "$body_i" ]; then
    pass "$TC"
else
    fail "$TC" "본문 불일치 — 두 파일의 _dl_detect_strip이 드리프트했습니다"
fi

# ---- TC-A5: update.sh _dl_asset_name 정상 sha256sums.txt → 자산명 파생 ----
TC="TC-A5 (S-2): update.sh _dl_asset_name(정상 sha256sums.txt) = $ASSET_NAME"
if ! has_func "$UPDATE_SH" "_dl_asset_name"; then
    fail "$TC" "update.sh에 _dl_asset_name 정의 없음"
else
    run_harness "$UPDATE_SH" "_dl_asset_name '$SHA_OK'" _dl_asset_name
    if [ "$HARNESS_RC" -eq 0 ] && [ "$HARNESS_OUT" = "$ASSET_NAME" ]; then
        pass "$TC"
    else
        fail "$TC" "exit=$HARNESS_RC got: '$HARNESS_OUT'  (expected: '$ASSET_NAME')"
    fi
fi

# ---- TC-A6: binary mode('*' 접두) 형식에서도 동일 파생 ----
TC="TC-A6 (S-2): update.sh _dl_asset_name(binary mode '*' 접두) = $ASSET_NAME"
if ! has_func "$UPDATE_SH" "_dl_asset_name"; then
    fail "$TC" "update.sh에 _dl_asset_name 정의 없음"
else
    run_harness "$UPDATE_SH" "_dl_asset_name '$SHA_BINMODE'" _dl_asset_name
    if [ "$HARNESS_RC" -eq 0 ] && [ "$HARNESS_OUT" = "$ASSET_NAME" ]; then
        pass "$TC"
    else
        fail "$TC" "exit=$HARNESS_RC got: '$HARNESS_OUT'  (expected: '$ASSET_NAME')"
    fi
fi

# ---- TC-A7: .tar.gz 항목 없는 파일 → 공백 반환 (호출자가 폴백 판단) ----
TC="TC-A7 (S-2): update.sh _dl_asset_name(.tar.gz 항목 없음) = 공백"
if ! has_func "$UPDATE_SH" "_dl_asset_name"; then
    fail "$TC" "update.sh에 _dl_asset_name 정의 없음"
else
    run_harness "$UPDATE_SH" "out=\"\$(_dl_asset_name '$SHA_NOENTRY')\"; printf '[%s]\n' \"\$out\"" _dl_asset_name
    if [ "$HARNESS_RC" -eq 0 ] && [ "$HARNESS_OUT" = "[]" ]; then
        pass "$TC"
    else
        fail "$TC" "exit=$HARNESS_RC got: '$HARNESS_OUT'  (expected: '[]')"
    fi
fi

# ---- TC-A8: install.sh _dl_asset_name 동일 3판정 ----
TC="TC-A8 (S-2): install.sh _dl_asset_name 3입력 판정 (정상/binmode/항목없음)"
if ! has_func "$INSTALL_SH" "_dl_asset_name"; then
    fail "$TC" "install.sh에 _dl_asset_name 정의 없음"
else
    run_harness "$INSTALL_SH" \
        "printf '%s|%s|[%s]\n' \"\$(_dl_asset_name '$SHA_OK')\" \"\$(_dl_asset_name '$SHA_BINMODE')\" \"\$(_dl_asset_name '$SHA_NOENTRY')\"" \
        _dl_asset_name
    if [ "$HARNESS_RC" -eq 0 ] && [ "$HARNESS_OUT" = "$ASSET_NAME|$ASSET_NAME|[]" ]; then
        pass "$TC"
    else
        fail "$TC" "exit=$HARNESS_RC got: '$HARNESS_OUT'  (expected: '$ASSET_NAME|$ASSET_NAME|[]')"
    fi
fi

# ---- TC-A9: 두 bash 파일의 _dl_asset_name 본문 동일 ----
TC="TC-A9 (S-2/D-A): install.sh·update.sh의 _dl_asset_name 본문 동일"
an_u="$(extract_func "$UPDATE_SH" "_dl_asset_name" | sed 's/[[:space:]]*$//')"
an_i="$(extract_func "$INSTALL_SH" "_dl_asset_name" | sed 's/[[:space:]]*$//')"
if [ -z "$an_u" ] || [ -z "$an_i" ]; then
    fail "$TC" "한쪽 이상 미정의 (update.sh:$([ -n "$an_u" ] && echo O || echo X) install.sh:$([ -n "$an_i" ] && echo O || echo X))"
elif [ "$an_u" = "$an_i" ]; then
    pass "$TC"
else
    fail "$TC" "본문 불일치 — 두 파일의 _dl_asset_name이 드리프트했습니다"
fi

# ---- S-6: _dl_sha256 도구 이식성 — PATH 제한 실행 ----
# 스텁 PATH 구성: awk(필수 의존) + 대상 해시 도구만 심볼릭 링크로 노출
SHA256SUM_BIN="$(command -v sha256sum || true)"
SHASUM_BIN="$(command -v shasum || true)"
AWK_BIN="$(command -v awk || true)"

mk_stub_path() {  # $1=dir 이름, $2.. = 노출할 실행파일 절대경로
    local d="$FIX/$1"; shift
    mkdir -p "$d"
    local b
    for b in "$@"; do
        [ -n "$b" ] && ln -sf "$b" "$d/$(basename "$b")"
    done
    printf '%s' "$d"
}

TC="TC-A10 (S-6): _dl_sha256 — sha256sum만 있는 PATH에서 기준 해시 반환"
if ! has_func "$UPDATE_SH" "_dl_sha256"; then
    fail "$TC" "update.sh에 _dl_sha256 정의 없음"
elif [ -z "$SHA256SUM_BIN" ]; then
    skip "$TC (이 환경에 sha256sum 미탑재)"
else
    STUB_A="$(mk_stub_path stub-sha256sum "$AWK_BIN" "$SHA256SUM_BIN")"
    h="$FIX/h_sha_a.sh"
    { printf '#!/usr/bin/env bash\nset -uo pipefail\n'; extract_func "$UPDATE_SH" _dl_sha256; printf '\n_dl_sha256 "%s"\n' "$SHA_TMP/$ASSET_NAME"; } > "$h"
    rc=0
    out="$(PATH="$STUB_A" "$BASH_BIN" "$h" 2>&1)" || rc=$?
    if [ "$rc" -eq 0 ] && [ "$out" = "$REF_SHA" ]; then
        pass "$TC"
    else
        fail "$TC" "exit=$rc got: '$out'  (expected: '$REF_SHA')"
    fi
fi

TC="TC-A11 (S-6): _dl_sha256 — shasum만 있는 PATH에서 동일 해시 반환"
if ! has_func "$UPDATE_SH" "_dl_sha256"; then
    fail "$TC" "update.sh에 _dl_sha256 정의 없음"
elif [ -z "$SHASUM_BIN" ]; then
    skip "$TC (이 환경에 shasum 미탑재)"
else
    STUB_B="$(mk_stub_path stub-shasum "$AWK_BIN" "$SHASUM_BIN")"
    h="$FIX/h_sha_b.sh"
    { printf '#!/usr/bin/env bash\nset -uo pipefail\n'; extract_func "$UPDATE_SH" _dl_sha256; printf '\n_dl_sha256 "%s"\n' "$SHA_TMP/$ASSET_NAME"; } > "$h"
    rc=0
    out="$(PATH="$STUB_B" "$BASH_BIN" "$h" 2>&1)" || rc=$?
    if [ "$rc" -eq 0 ] && [ "$out" = "$REF_SHA" ]; then
        pass "$TC"
    else
        fail "$TC" "exit=$rc got: '$out'  (expected: '$REF_SHA')"
    fi
fi

TC="TC-A12 (S-6): _dl_sha256 — 해시 도구 둘 다 없는 PATH에서 실패 반환(exit≠0, stdout 공백)"
if ! has_func "$UPDATE_SH" "_dl_sha256"; then
    fail "$TC" "update.sh에 _dl_sha256 정의 없음"
else
    STUB_C="$(mk_stub_path stub-none "$AWK_BIN")"
    h="$FIX/h_sha_c.sh"
    { printf '#!/usr/bin/env bash\nset -uo pipefail\n'; extract_func "$UPDATE_SH" _dl_sha256; printf '\n_dl_sha256 "%s"\n' "$SHA_TMP/$ASSET_NAME"; } > "$h"
    rc=0
    out="$(PATH="$STUB_C" "$BASH_BIN" "$h" 2>/dev/null)" || rc=$?
    if [ "$rc" -ne 0 ] && [ -z "$out" ]; then
        pass "$TC"
    else
        fail "$TC" "exit=$rc stdout='$out'  (expected: exit≠0 + 공백 stdout — 무음 통과 금지)"
    fi
fi

# =============================================================================
# (나) 추출 사후조건 · 체크섬 하드 실패 — S-13 / S-5
# =============================================================================
printf '\n== (나) 추출·체크섬 행위 (TC-B*, S-13·S-5) — RED 시점 FAIL 예상 ==\n\n'

# extract_to_tmp 하네스 실행기 — OPAL_EXTRACT_DIR을 표준출력으로 회수(공개 산출값)
run_extract() {  # $1 = tarball 경로 → HARNESS_OUT / HARNESS_RC / EXTRACT_DIR
    local tarball="$1"
    local tmp; tmp="$(mktemp -d "$FIX/ex.XXXXXX")"
    run_harness "$INSTALL_SH" \
        "OPAL_DRY_RUN=0
OPAL_TMP='$tmp'
OPAL_TARBALL='$tarball'
extract_to_tmp
printf 'EXTRACT_DIR=%s\n' \"\${OPAL_EXTRACT_DIR}\"" \
        info success warn error _dl_detect_strip extract_to_tmp
    EXTRACT_DIR="$(printf '%s\n' "$HARNESS_OUT" | sed -n 's/^EXTRACT_DIR=//p' | tail -1)"
}

# 하네스 자체 오류(미정의 변수/명령/구문)로 인한 우연한 exit≠0을 "의도된 하드 실패" 증거로
# 오인하지 않기 위한 가드. 하드 실패는 스크립트의 명시적 거부여야 하며 계약 밖 오류여서는 안 된다.
harness_error() {
    case "$HARNESS_OUT" in
        *"unbound variable"*|*"command not found"*|*"syntax error"*) return 0 ;;
        *) return 1 ;;
    esac
}

TC="TC-B1 (S-13): extract_to_tmp(prefix 없는 아카이브) → 루트에 VERSION·opal/ 존재"
if ! has_func "$INSTALL_SH" "extract_to_tmp"; then
    fail "$TC" "install.sh에 extract_to_tmp 정의 없음"
else
    run_extract "$A1"
    if [ "$HARNESS_RC" -ne 0 ]; then
        fail "$TC" "exit=$HARNESS_RC out='$HARNESS_OUT'"
    elif [ -n "$EXTRACT_DIR" ] && [ -f "$EXTRACT_DIR/VERSION" ] && [ -d "$EXTRACT_DIR/opal" ]; then
        pass "$TC"
    else
        fail "$TC" "extract_dir='$EXTRACT_DIR' VERSION=$([ -f "$EXTRACT_DIR/VERSION" ] && echo O || echo X) opal/=$([ -d "$EXTRACT_DIR/opal" ] && echo O || echo X) | out='$HARNESS_OUT'"
    fi
fi

TC="TC-B2 (S-13): extract_to_tmp(prefix 있는 자동 아카이브) → 루트에 VERSION·opal/ 존재"
if ! has_func "$INSTALL_SH" "extract_to_tmp"; then
    fail "$TC" "install.sh에 extract_to_tmp 정의 없음"
else
    run_extract "$A2"
    if [ "$HARNESS_RC" -ne 0 ]; then
        fail "$TC" "exit=$HARNESS_RC out='$HARNESS_OUT'"
    elif [ -n "$EXTRACT_DIR" ] && [ -f "$EXTRACT_DIR/VERSION" ] && [ -d "$EXTRACT_DIR/opal" ]; then
        pass "$TC"
    else
        fail "$TC" "extract_dir='$EXTRACT_DIR' VERSION=$([ -f "$EXTRACT_DIR/VERSION" ] && echo O || echo X) opal/=$([ -d "$EXTRACT_DIR/opal" ] && echo O || echo X) | out='$HARNESS_OUT'"
    fi
fi

TC="TC-B3 (S-13): extract_to_tmp(구조 위반 아카이브) → 하드 실패(exit≠0), 조용한 진행 금지"
if ! has_func "$INSTALL_SH" "extract_to_tmp"; then
    fail "$TC" "install.sh에 extract_to_tmp 정의 없음"
else
    run_extract "$A4"
    if harness_error; then
        fail "$TC" "계약 밖 하네스 오류로 종료 — 의도된 거부가 아님 | out='$HARNESS_OUT'"
    elif [ "$HARNESS_RC" -ne 0 ]; then
        pass "$TC"
    else
        fail "$TC" "exit=0 — VERSION·opal/ 부재에도 통과했습니다 (사후조건 검사 부재) | out='$HARNESS_OUT'"
    fi
fi

# verify_checksum 하네스 실행기 — DL-CONTRACT 전역 계약으로 픽스처 주입 (네트워크 0회)
run_verify() {  # $1 = 주입할 sha 파일
    local shafile="$1"
    run_harness "$INSTALL_SH" \
        "OPAL_DRY_RUN=0
OPAL_PLATFORM='$PLATFORM'
OPAL_TMP='$SHA_TMP'
OPAL_TARBALL='$SHA_TMP/$ASSET_NAME'
OPAL_TARBALL_NAME='$ASSET_NAME'
OPAL_SHA_FILE='$shafile'
OPAL_CHECKSUM_MODE='verify'
verify_checksum" \
        info success warn error _dl_sha256 _dl_asset_name verify_checksum
}

TC="TC-B4 (S-5, 양성대조): verify_checksum(정상 sha256sums.txt 주입) → exit 0 + 검증 완료 출력"
if ! has_func "$INSTALL_SH" "verify_checksum"; then
    fail "$TC" "install.sh에 verify_checksum 정의 없음"
else
    run_verify "$SHA_OK"
    case "$HARNESS_OUT" in
        *"체크섬 검증 완료"*) ok_msg=1 ;;
        *) ok_msg=0 ;;
    esac
    if [ "$HARNESS_RC" -eq 0 ] && [ "$ok_msg" -eq 1 ]; then
        pass "$TC"
    else
        fail "$TC" "exit=$HARNESS_RC msg=$ok_msg out='$HARNESS_OUT' (verify_checksum이 OPAL_CHECKSUM_MODE/OPAL_SHA_FILE/OPAL_TARBALL_NAME 계약으로 구동되어야 함)"
    fi
fi

TC="TC-B5 (S-5): verify_checksum(항목 부재 sha256sums.txt) → 하드 실패(exit≠0)"
if ! has_func "$INSTALL_SH" "verify_checksum"; then
    fail "$TC" "install.sh에 verify_checksum 정의 없음"
else
    run_verify "$SHA_NOENTRY"
    if harness_error; then
        fail "$TC" "계약 밖 하네스 오류로 종료 — 의도된 거부가 아님 | out='$HARNESS_OUT'"
    elif [ "$HARNESS_RC" -ne 0 ]; then
        pass "$TC"
    else
        fail "$TC" "exit=0 — 항목 부재인데 통과했습니다 (무음 스킵 잔존) | out='$HARNESS_OUT'"
    fi
fi

TC="TC-B6 (S-5): verify_checksum(빈 해시 sha256sums.txt) → 하드 실패(exit≠0)"
if ! has_func "$INSTALL_SH" "verify_checksum"; then
    fail "$TC" "install.sh에 verify_checksum 정의 없음"
else
    run_verify "$SHA_BLANKHASH"
    if harness_error; then
        fail "$TC" "계약 밖 하네스 오류로 종료 — 의도된 거부가 아님 | out='$HARNESS_OUT'"
    elif [ "$HARNESS_RC" -ne 0 ]; then
        pass "$TC"
    else
        fail "$TC" "exit=0 — 기대값이 공백인데 통과했습니다 (H-10 무음 통과 잔존) | out='$HARNESS_OUT'"
    fi
fi

TC="TC-B7 (S-5): install.sh verify_checksum 본문에 네트워크 호출·경고후통과 경로 부재"
vbody="$(extract_func "$INSTALL_SH" "verify_checksum")"
if [ -z "$vbody" ]; then
    fail "$TC" "install.sh에 verify_checksum 정의 없음"
else
    net_hits="$(printf '%s\n' "$vbody" | grep -c 'curl' || true)"
    # 항목 부재를 warn 후 통과시키는 경로: '항목 없음' 계열 경고 + return 0 조합
    warnskip_hits="$(printf '%s\n' "$vbody" | grep -c '검증 건너뜀\|검증을 건너' || true)"
    if [ "$net_hits" -eq 0 ] && [ "$warnskip_hits" -eq 0 ]; then
        pass "$TC"
    else
        fail "$TC" "curl 호출 ${net_hits}건(다운로드는 resolve_download_plan 책임) / '검증 건너뜀' 경로 ${warnskip_hits}건"
    fi
fi

TC="TC-B8 (S-5): update.sh 체크섬 분기 — 빈 기대값 무음 통과 패턴 0건 + 고정문자열 매칭"
silent_hits="$(grep -c -- '-n "\$expected_sha"' "$UPDATE_SH" || true)"
fixed_hits="$(grep -c -- 'grep -F' "$UPDATE_SH" || true)"
if [ "$silent_hits" -eq 0 ] && [ "$fixed_hits" -ge 1 ]; then
    pass "$TC"
else
    fail "$TC" "무음통과 조건('-n \$expected_sha') ${silent_hits}건(기대 0) / 'grep -F' ${fixed_hits}건(기대 ≥1)"
fi

# =============================================================================
# (다) 구형 경로 잔존 0건 — S-3
# =============================================================================
printf '\n== (다) 구형 잔존 정적 검사 (TC-C*, S-3) ==\n\n'

# 코드 라인(주석 제외) 한정 검색기
code_grep_count() {  # $1=file $2=fixed string
    grep -F -- "$2" "$1" 2>/dev/null | grep -vc '^[[:space:]]*#' || true
}

TC="TC-C1 (S-3①): install.sh에 'opal.tar.gz' 리터럴 0건"
c1="$(grep -c -F 'opal.tar.gz' "$INSTALL_SH" || true)"
if [ "$c1" -eq 0 ]; then
    pass "$TC"
else
    fail "$TC" "${c1}건 잔존 — 로컬 저장명이 발행 자산명으로 전환되지 않았습니다: $(grep -n -F 'opal.tar.gz' "$INSTALL_SH" | tr '\n' ' ')"
fi

TC="TC-C2 (S-3②): 2개 bash 파일에 비고정문자열 grep 매칭(변수 보간 + -F 부재) 0건"
c2_hits=""
for f in "$INSTALL_SH" "$UPDATE_SH"; do
    hit="$(grep -n 'grep ' "$f" | grep '\$' | grep -v -- '-F' || true)"
    [ -n "$hit" ] && c2_hits="$c2_hits
$(basename "$f"): $hit"
done
if [ -z "$c2_hits" ]; then
    pass "$TC"
else
    fail "$TC" "잔존:$c2_hits"
fi

TC="TC-C3 (S-3③): 3파일 각각 코드 라인의 'archive/refs/tags' 정확히 1회(폴백 분기 전용)"
c3_bad=""
for f in "$INSTALL_SH" "$INSTALL_PS1" "$UPDATE_SH"; do
    n="$(code_grep_count "$f" 'archive/refs/tags')"
    [ "$n" -eq 1 ] || c3_bad="$c3_bad $(basename "$f")=$n"
done
if [ -z "$c3_bad" ]; then
    pass "$TC"
else
    fail "$TC" "기대 1회, 실제:$c3_bad"
fi

TC="TC-C4 (S-3, 신형 채택): 3파일 각각 릴리즈 자산 tarball URL(releases/download, sha256sums.txt 아님) 구성 라인 ≥1"
c4_bad=""
for f in "$INSTALL_SH" "$INSTALL_PS1" "$UPDATE_SH"; do
    n="$(grep -F 'releases/download' "$f" 2>/dev/null | grep -v '^[[:space:]]*#' | grep -vc 'sha256sums.txt' || true)"
    [ "$n" -ge 1 ] || c4_bad="$c4_bad $(basename "$f")=$n"
done
if [ -z "$c4_bad" ]; then
    pass "$TC"
else
    fail "$TC" "기대 ≥1, 실제:$c4_bad — 릴리즈 자산이 다운로드 대상으로 채택되지 않았습니다"
fi

TC="TC-C5 (S-3④): 3파일에 무조건 고정 '--strip-components' 0건 (판정값 참조가 12줄 이내 선행해야 함)"
c5_bad=""
for f in "$INSTALL_SH" "$INSTALL_PS1" "$UPDATE_SH"; do
    bad="$(awk '
        { for (i = 12; i >= 1; i--) prev[i+1] = prev[i]; prev[1] = last; last = $0 }
        /--strip-components/ {
            ctx = $0
            gsub(/--strip-components/, "", ctx)
            for (i = 1; i <= 12; i++) ctx = ctx "\n" prev[i]
            if (ctx !~ /_dl_detect_strip|Get-DlStripComponents|strip_n|\$strip|\$Strip/) print NR
        }
    ' "$f")"
    [ -n "$bad" ] && c5_bad="$c5_bad $(basename "$f"):line($(printf '%s' "$bad" | tr '\n' ','))"
done
if [ -z "$c5_bad" ]; then
    pass "$TC"
else
    fail "$TC" "판정값 미참조(고정) 잔존:$c5_bad"
fi

TC="TC-C6 (S-3⑤): 3파일 헤더(첫 70줄)에 'DL-CONTRACT (085)' 각인 존재"
c6_bad=""
for f in "$INSTALL_SH" "$INSTALL_PS1" "$UPDATE_SH"; do
    if ! head -70 "$f" | grep -qE 'DL-CONTRACT \((task )?085\)'; then
        c6_bad="$c6_bad $(basename "$f")"
    fi
done
if [ -z "$c6_bad" ]; then
    pass "$TC"
else
    fail "$TC" "각인 누락:$c6_bad"
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
