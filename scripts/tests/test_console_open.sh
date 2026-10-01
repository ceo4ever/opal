#!/usr/bin/env bash
# =============================================================================
# test_console_open.sh — opal-cli `console open` 준비 확인 회귀 테스트
#
# `open`은 /health가 응답하는 경우에만 브라우저를 열어야 한다. 실제 7823 포트를
# 사용하지 않고 curl·sleep을 스텁하여 준비 대기 헬퍼를 검증한다.
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CONSOLE_SH="$REPO_ROOT/opal/tools/opal-cli/lib/console.sh"
PASS_COUNT=0
FAIL_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf '[PASS] %s\n' "$1"; }
fail() { FAIL_COUNT=$((FAIL_COUNT + 1)); printf '[FAIL] %s\n' "$1"; }

extract_case_branch() {
    awk -v label="$2" '
        $0 ~ "^[ \\t]*" label "\\)" { found = 1 }
        found { print }
        found && $0 ~ /^[ \\t]*;;[ \\t]*$/ { exit }
    ' "$1"
}

if bash -n "$CONSOLE_SH"; then
    pass 'console.sh Bash 구문 검사'
else
    fail 'console.sh Bash 구문 검사'
fi

if (
    curl_calls=0
    curl() { curl_calls=$((curl_calls + 1)); [ "$curl_calls" -ge 3 ]; }
    sleep() { :; }
    source "$CONSOLE_SH"
    _console_wait_for_health 'http://127.0.0.1:7823/health' 3
    [ "$curl_calls" -eq 3 ]
); then
    pass '준비 대기는 health 성공까지 재시도한다'
else
    fail '준비 대기는 health 성공까지 재시도한다'
fi

if (
    curl() { return 1; }
    sleep() { :; }
    source "$CONSOLE_SH"
    ! _console_wait_for_health 'http://127.0.0.1:7823/health' 2
); then
    pass '준비 대기는 제한 횟수 뒤 실패를 반환한다'
else
    fail '준비 대기는 제한 횟수 뒤 실패를 반환한다'
fi

if (
    opened_url=''
    curl() { return 0; }
    open() { opened_url="$1"; }
    success() { :; }
    source "$CONSOLE_SH"
    cmd_console open
    [ "$opened_url" = 'http://127.0.0.1:7823' ]
); then
    pass '준비된 Console만 브라우저 열기 명령을 받는다'
else
    fail '준비된 Console만 브라우저 열기 명령을 받는다'
fi

open_branch="$(extract_case_branch "$CONSOLE_SH" open)"
first_health_line="$(printf '%s\n' "$open_branch" | grep -nF '_console_wait_for_health "$health_url" 1' | head -1 | cut -d: -f1 || true)"
start_line="$(printf '%s\n' "$open_branch" | grep -nF 'cmd_console start' | head -1 | cut -d: -f1 || true)"
ready_line="$(printf '%s\n' "$open_branch" | grep -nF '_console_wait_for_health "$health_url" 10' | head -1 | cut -d: -f1 || true)"
browser_line="$(printf '%s\n' "$open_branch" | grep -nF 'open "$dashboard_url"' | head -1 | cut -d: -f1 || true)"

if [ -n "$first_health_line" ] && [ -n "$start_line" ] && [ -n "$ready_line" ] && [ -n "$browser_line" ] \
    && [ "$first_health_line" -lt "$start_line" ] && [ "$start_line" -lt "$ready_line" ] && [ "$ready_line" -lt "$browser_line" ]; then
    pass 'open은 준비 확인·기동·재확인 뒤 브라우저를 연다'
else
    fail 'open은 준비 확인·기동·재확인 뒤 브라우저를 연다'
fi

printf '\n결과: PASS=%s FAIL=%s\n' "$PASS_COUNT" "$FAIL_COUNT"
[ "$FAIL_COUNT" -eq 0 ]
