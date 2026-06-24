#!/usr/bin/env bash
# RED-first 테스트: install_opal_setting 함수 계약 검증
# TS-002: 멱등(존재 시 불변) | TS-003: 생성(부재 시 생성)
# red-first.md §1: 구현 전 실패(exit≠0) 증거 확보 필수
# red-first.md §4: 공개 인터페이스(파일 내용·exit code)로만 검증
#
# 실행: bash tasks/043-260624-opds-부트스트랩-게이트-설정파일-전환/tests/test_install_opal_setting.sh

set -euo pipefail

# ─── 헬퍼 ────────────────────────────────────────────────────────────────────
PASS=0
FAIL=0
ERRORS=()

pass() { echo "[PASS] $1"; PASS=$((PASS+1)); }
fail() { echo "[FAIL] $1"; FAIL=$((FAIL+1)); ERRORS+=("$1"); }

# ─── 소스 로드: 함수만 추출 ──────────────────────────────────────────────────
# install-mac.sh 전체를 직접 source하면 인스톨러 본문(main)이 실행될 수 있어
# sed로 install_opal_setting() 함수 정의 블록만 추출해 로드한다.
# 함수가 아직 없으면 추출 결과가 비어 호출 시 "command not found"(exit≠0) → 자연 RED.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_SH="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")/scripts/install-mac.sh"

if [[ ! -f "$INSTALL_SH" ]]; then
    echo "[ERROR] install-mac.sh 를 찾을 수 없습니다: $INSTALL_SH"
    exit 1
fi

# install_opal_setting 함수 블록 추출 (없으면 빈 파일 → 함수 미등록 → 자연 RED)
# bash 3.2(/bin/bash on macOS)에서 프로세스 치환 source <(...) 은 현재 셸에
# 함수를 등록하지 못하는 silent no-op이 발생하므로 named 임시 파일에 먼저 쓴다.
_fn_tmp="$(mktemp)"
trap 'rm -f "$_fn_tmp"' EXIT
sed -n '/^install_opal_setting()/,/^}/p' "$INSTALL_SH" > "$_fn_tmp"

# 추출 결과가 비어 있으면(함수 미구현) 명시 실패로 즉시 종료 → RED 보장
if [[ ! -s "$_fn_tmp" ]]; then
    echo "[FAIL] install_opal_setting 함수가 $INSTALL_SH 에 없음 — 함수 미구현"
    echo ""
    echo "=== 결과 ==="
    echo "PASS: 0 / FAIL: 2"
    echo ""
    echo "EXIT 1 — RED 확인됨 (구현 전 실패 증거)"
    exit 1
fi

# 함수 정의만 포함된 파일을 source → bash 3.2 호환
source "$_fn_tmp"

# ─── no-op 헬퍼 스텁 ──────────────────────────────────────────────────────────
# install-mac.sh의 info/success/warn 함수가 없으면 no-op으로 정의
info()    { true; }
success() { true; }
warn()    { true; }
error()   { true; }

# ─── TS-002: 멱등 — 존재 시 불변 ─────────────────────────────────────────────
# PLAN §3.1.2: "[[ -f "$dst" ]] early-return — 사용자 토글 보존"
run_ts002() {
    local tmp_home
    tmp_home="$(mktemp -d)"
    trap 'rm -rf "$tmp_home"' RETURN

    # 임시 소스(실제 소스 파일 부재 시 대체)
    local tmp_src="$tmp_home/setting.default.json"
    echo '{"bootstrap":"on"}' > "$tmp_src"

    # ~/.opal/setting.json 선배치 — {"bootstrap":"off"}
    mkdir -p "$tmp_home/.opal"
    local expected='{"bootstrap":"off"}'
    echo "$expected" > "$tmp_home/.opal/setting.json"
    local before
    before="$(cat "$tmp_home/.opal/setting.json")"

    # 함수 호출에 필요한 변수 환경 설정
    local FRAMEWORK_ROOT
    FRAMEWORK_ROOT="$(dirname "$tmp_src")"          # tmp_src 위치를 FRAMEWORK_ROOT로
    USER_HOME="$tmp_home"

    # install_opal_setting이 src로 사용하는 실제 경로에 소스 파일 배치
    mkdir -p "$FRAMEWORK_ROOT/opal/core"
    cp "$tmp_src" "$FRAMEWORK_ROOT/opal/core/setting.default.json"

    # 함수 호출
    if ! install_opal_setting 2>/dev/null; then
        fail "TS-002: install_opal_setting 호출 실패 (exit≠0) — 함수 미구현 또는 오류"
        return
    fi

    local after
    after="$(cat "$tmp_home/.opal/setting.json")"

    if [[ "$before" == "$after" ]]; then
        pass "TS-002: 존재 시 불변 — setting.json 내용 변경 없음 (off 보존)"
    else
        fail "TS-002: 존재 시 덮어씌워짐 — before='$before' after='$after'"
    fi
}

# ─── TS-003: 생성 — 부재 시 생성 ──────────────────────────────────────────────
# PLAN §3.1.2: "부재 시 cp src dst — 유효 JSON + bootstrap 키"
run_ts003() {
    local tmp_home
    tmp_home="$(mktemp -d)"
    trap 'rm -rf "$tmp_home"' RETURN

    # ~/.opal 디렉토리만 생성, setting.json은 없음
    mkdir -p "$tmp_home/.opal"

    # 임시 소스 파일 생성 (실제 opal/core/setting.default.json 역할)
    local tmp_fw="$tmp_home/_framework"
    mkdir -p "$tmp_fw/opal/core"
    echo '{"bootstrap":"on"}' > "$tmp_fw/opal/core/setting.default.json"

    # 함수 호출에 필요한 변수 설정
    FRAMEWORK_ROOT="$tmp_fw"
    USER_HOME="$tmp_home"

    # 함수 호출
    if ! install_opal_setting 2>/dev/null; then
        fail "TS-003: install_opal_setting 호출 실패 (exit≠0) — 함수 미구현 또는 오류"
        return
    fi

    local dst="$tmp_home/.opal/setting.json"

    # 파일 생성 여부 확인
    if [[ ! -f "$dst" ]]; then
        fail "TS-003: setting.json 미생성 — 파일이 존재하지 않음"
        return
    fi

    # bootstrap 키 포함 여부 확인
    if python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert 'bootstrap' in d" "$dst" 2>/dev/null; then
        pass "TS-003: 부재 시 생성 — setting.json 생성 + bootstrap 키 확인"
    else
        fail "TS-003: setting.json 생성됐으나 bootstrap 키 없음 또는 유효하지 않은 JSON"
    fi
}

# ─── 테스트 실행 ──────────────────────────────────────────────────────────────
echo "=== RED-first 테스트: install_opal_setting ==="
echo "스크립트: $INSTALL_SH"
echo ""

run_ts002
run_ts003

# ─── 결과 보고 ────────────────────────────────────────────────────────────────
echo ""
echo "=== 결과 ==="
echo "PASS: $PASS / FAIL: $FAIL"

if [[ ${#ERRORS[@]} -gt 0 ]]; then
    echo ""
    echo "실패한 시나리오:"
    for e in "${ERRORS[@]}"; do
        echo "  - $e"
    done
fi

if [[ $FAIL -gt 0 ]]; then
    echo ""
    echo "EXIT 1 — RED 확인됨 (구현 전 실패 증거)"
    exit 1
fi

echo ""
echo "EXIT 0 — 모두 통과 (GREEN)"
exit 0
