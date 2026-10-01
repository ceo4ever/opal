#!/usr/bin/env bash
# =============================================================================
# test_console_open.sh — opal-cli `console open` 준비 확인·진입 token 계약 회귀 테스트
#
# `open`은 /health가 응답하고 `auth` 필드가 있는 경우에만, 1회용 진입 token을 URL
# fragment(#entry=<token>)로 실어 브라우저를 열어야 한다 (task 172 D-9·D-11·D-12).
# 실제 7823 포트를 사용하지 않고 curl·open·sleep만 스텁하며, 실제 console.sh와 실제
# entry_token CLI를 임시 OPAL_HOME에서 실행한다.
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

# ─── 새 진입 계약 (task 172, PLAN D-9·D-11·D-12) ─────────────────────────────
# 실제 console.sh + 실제 entry_token CLI(`python -m dashboard.backend.entry_token issue`)를 실행한다.
# 대체 대상은 curl(/health 응답)·open·sleep 뿐이다. 임시 HOME/OPAL_HOME만 사용하며
# 사용자 Console(7823)·사용자 ~/.opal·실제 브라우저는 건드리지 않는다.

WORK_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/opal-console-open.XXXXXX")"
trap 'rm -rf "$WORK_ROOT"' EXIT

HEALTH_NEW='{"status":"ok","version":"test","auth":"required"}'
HEALTH_OLD='{"status":"ok","version":"test"}'

# make_env <name> <server_link_target> — 임시 OPAL_HOME 구성: dashboard-server는 지정 경로의 심볼릭 링크
make_env() {
    local dir="$WORK_ROOT/$1"
    mkdir -p "$dir/opal_home" "$dir/home" "$dir/cwd"
    ln -s "$2" "$dir/opal_home/dashboard-server"
    : > "$dir/events"
    printf '%s' "$dir"
}

# run_open <env_dir> <health_body> <initially_up:0|1> — 서브셸에서 cmd_console open을 실행한다.
# 결과: <env_dir>/{stdout,stderr,rc,opened,events}
run_open() {
    local dir="$1" body="$2" up="$3"
    rm -f "$dir/up" "$dir/opened" "$dir/rc"
    [ "$up" = "1" ] && : > "$dir/up"
    (
        cd "$dir/cwd"
        export HOME="$dir/home" OPAL_HOME="$dir/opal_home"
        unset PYTHONPATH
        entry_count() { find "$OPAL_HOME/run/console-entry" -type f 2>/dev/null | wc -l | tr -d ' '; }
        curl() {
            printf 'health:%s\n' "$(entry_count)" >> "$dir/events"
            if [ -f "$dir/up" ]; then printf '%s' "$body"; return 0; fi
            return 22
        }
        sleep() { :; }
        open() { printf 'open:%s\n' "$(entry_count)" >> "$dir/events"; printf '%s' "$1" > "$dir/opened"; }
        xdg-open() { open "$@"; }
        info()    { echo "[INFO] $1"; }
        success() { echo "  ok $1"; }
        warn()    { echo "[WARN] $1"; }
        error()   { echo "[ERROR] $1" >&2; }
        source "$CONSOLE_SH"
        eval "$(declare -f cmd_console | sed '1s/^cmd_console/__orig_cmd_console/')"
        cmd_console() {
            if [ "${1:-}" = "start" ]; then
                printf 'start\n' >> "$dir/events"
                : > "$dir/up"
                return 0
            fi
            __orig_cmd_console "$@"
        }
        set +e
        cmd_console open > "$dir/stdout" 2> "$dir/stderr"
        echo $? > "$dir/rc"
    )
}

file_mode() { python3 -c 'import os,sys;print(format(os.stat(sys.argv[1]).st_mode & 0o777, "o"))' "$1"; }
sha256_hex() { python3 -c 'import hashlib,sys;print(hashlib.sha256(sys.argv[1].encode()).hexdigest())' "$1"; }

# ① 정상 데몬(/health에 auth 포함) — fragment URL로 열고 token은 어디에도 출력하지 않는다
E1="$(make_env normal "$REPO_ROOT")"
run_open "$E1" "$HEALTH_NEW" 1
opened1="$(cat "$E1/opened" 2>/dev/null || true)"
token1="${opened1#*#entry=}"
entry_dir="$E1/opal_home/run/console-entry"

if [[ "$opened1" =~ ^http://127\.0\.0\.1:7823/#entry=[A-Za-z0-9_-]{20,}$ ]] && [ "$(cat "$E1/rc")" = "0" ]; then
    pass '① 열기 URL은 http://127.0.0.1:7823/#entry=<token> 형식이고 종료 코드는 0이다'
else
    fail "① 열기 URL은 http://127.0.0.1:7823/#entry=<token> 형식이고 종료 코드는 0이다 (opened='$opened1', rc=$(cat "$E1/rc" 2>/dev/null))"
fi

if [ -n "$token1" ] && [ "$token1" != "$opened1" ] \
    && ! grep -qF "$token1" "$E1/stdout" "$E1/stderr" \
    && ! grep -qF '#entry' "$E1/stdout" "$E1/stderr"; then
    pass '① token·fragment는 stdout/stderr에 나오지 않는다'
else
    fail '① token·fragment는 stdout/stderr에 나오지 않는다'
fi

files1=("$entry_dir"/*)
if [ -d "$entry_dir" ] && [ "$(file_mode "$entry_dir")" = "700" ] \
    && [ "${#files1[@]}" -eq 1 ] && [ -f "${files1[0]}" ] \
    && [ "$(file_mode "${files1[0]}")" = "600" ] \
    && [ -n "$token1" ] && [ "$(basename "${files1[0]}")" = "$(sha256_hex "$token1")" ] \
    && ! grep -qF "$token1" "${files1[0]}"; then
    pass '① 발급 파일: console-entry 0700, <sha256> 이름 0600, 내용에 token 없음'
else
    fail '① 발급 파일: console-entry 0700, <sha256> 이름 0600, 내용에 token 없음'
fi

if [ "$(uniq "$E1/events")" = "$(printf 'health:0\nopen:1')" ]; then
    pass '① 순서: health 확인 → 발급 → 열기'
else
    fail "① 순서: health 확인 → 발급 → 열기 (events=$(tr '\n' ',' < "$E1/events"))"
fi

# ② 데몬 미기동 → start → 재확인 — 기존 순서 보존
E2="$(make_env restart "$REPO_ROOT")"
run_open "$E2" "$HEALTH_NEW" 0
if [ "$(uniq "$E2/events")" = "$(printf 'health:0\nstart\nhealth:0\nopen:1')" ] \
    && [[ "$(cat "$E2/opened" 2>/dev/null)" =~ ^http://127\.0\.0\.1:7823/#entry= ]]; then
    pass '② 순서: health 확인 → 기동 → 재확인 → 발급 → 열기'
else
    fail "② 순서: health 확인 → 기동 → 재확인 → 발급 → 열기 (events=$(tr '\n' ',' < "$E2/events"))"
fi

# ③ /health에 auth가 없는 구버전 — 열지 않고 비0, 재기동 안내
E3="$(make_env legacy "$REPO_ROOT")"
run_open "$E3" "$HEALTH_OLD" 1
if [ ! -e "$E3/opened" ] && [ "$(cat "$E3/rc")" != "0" ] \
    && grep -q '재기동' "$E3/stdout" "$E3/stderr" \
    && [ -z "$(find "$E3/opal_home/run/console-entry" -type f 2>/dev/null)" ]; then
    pass '③ 구버전 /health(auth 없음)는 브라우저를 열지 않고 비0 종료하며 재기동을 안내한다'
else
    fail "③ 구버전 /health(auth 없음)는 브라우저를 열지 않고 비0 종료하며 재기동을 안내한다 (opened='$(cat "$E3/opened" 2>/dev/null)', rc=$(cat "$E3/rc" 2>/dev/null))"
fi

# ④ token 발급 실패 주입 — dashboard-server가 빈 디렉터리를 가리켜 entry_token 모듈을 찾지 못한다
EMPTY_SERVER="$WORK_ROOT/empty-server"
mkdir -p "$EMPTY_SERVER"
E4="$(make_env issuefail "$EMPTY_SERVER")"
run_open "$E4" "$HEALTH_NEW" 1
if [ ! -e "$E4/opened" ] && [ "$(cat "$E4/rc")" != "0" ] \
    && grep -q 'ERROR' "$E4/stderr" "$E4/stdout"; then
    pass '④ 발급 실패 시 브라우저를 열지 않고 오류를 출력하며 비0 종료한다'
else
    fail "④ 발급 실패 시 브라우저를 열지 않고 오류를 출력하며 비0 종료한다 (opened='$(cat "$E4/opened" 2>/dev/null)', rc=$(cat "$E4/rc" 2>/dev/null))"
fi

printf '\n결과: PASS=%s FAIL=%s\n' "$PASS_COUNT" "$FAIL_COUNT"
[ "$FAIL_COUNT" -eq 0 ]
