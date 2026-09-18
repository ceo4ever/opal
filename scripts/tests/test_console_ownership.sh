#!/usr/bin/env bash
# =============================================================================
# test_console_ownership.sh — opal-cli `console` PID 레코드 기반 소유권 판정 테스트
# 태스크: 127-T02 (Console 프로세스 소유권 — PID 레코드 identity로 pkill 전역 패턴 제거)
# 트랙: RED-first — 이 파일은 RED 단계(구현 전) 산출물. G ① fail 반영 재작성판.
#
# 시나리오 SSOT: tasks/127-260912-oppl-E2E-하네스-구현/tasks/T02-Console-프로세스-소유권/PLAN.md
#                §Test scenario design (S-1~S-14, 개정판), QA-SPEC.md(G ①)
#
# 실행 순서: (가) 정적 S-1,S-2,S-9,S-10,S-13 → (나) 레코드-only S-3,S-11,S-12,S-14
#           → (다) real-usage S-8(선두) → S-4,S-5,S-6,S-7
#
# 픽스처 수명주기 규약 [MUST] (F-1): real-usage 시나리오는 자기 서버를 자기가
# 기동·회수한다. 다른 시나리오의 pid를 skip 가드로 쓰지 않는다. 부수효과로 인한
# skip은 fail로 처리한다 — skip은 환경 부재(venv·소스·포트 취득 실패)에만 허용.
#
# RED 관측 규약 [MUST] (F-3·D-16): `console stop` 실호출은 console.sh에 전역
# pkill -f "dashboard.backend.main:app" 패턴이 남아있는 동안 절대 수행하지 않는다
# (C-2·RK-1 — 사용자의 실제 7823 Console을 죽인다). 대신:
#   (a) pgrep 집합 중첩 단언 — 읽기 전용, kill 0회, 항상 안전하게 실행
#   (b) pkill argv 스텁 — pkill을 argv 기록 함수로 오버라이드하고 console.sh를
#       source해 cmd_console stop을 호출. 실제로는 아무것도 죽이지 않는다.
# GREEN(전역 pkill 제거) 이후에만 실제 서브프로세스(run.sh) 경유 `console stop`을
# 호출해 종단 동작(P1 종료·레코드 삭제·stopped= 값)을 검증한다.
#
# bash 3.2 호환 — 연관배열(declare -A)·mapfile 미사용
#
# 변경이력:
#   v1.0 2026-09-13 신규 작성 — RED 단계 1회차 (opal-test-agent, mode: red) (127-T02)
#   v2.0 2026-09-13 G ① fail 반영 전면 재작성 — F-1~F-9,F-11 수정, S-10~S-14 신설,
#        픽스처 수명주기 규약·RED 관측 규약(pgrep 중첩+pkill 스텁) 도입 (127-T02)
#   v2.1 2026-09-14 [B-신규] S-14를 구현 후 회귀 가드로 재정의해 2케이스 신설 —
#        (a) 부팅-이후 started_at 왕복, (b) started_at 손상·공백 fail-open.
#        기존 20 케이스와 [B-신규] S-13은 문언·기대값 무변경 (127-W-2)
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RUN_SH="$REPO_ROOT/opal/tools/opal-cli/run.sh"
CONSOLE_SH="$REPO_ROOT/opal/tools/opal-cli/lib/console.sh"
INSTALL_MAC_SH="$REPO_ROOT/scripts/install-mac.sh"
TEST_TOOL_DIR="$REPO_ROOT/opal/tools/test-tool"
USER_HEALTH_URL="http://127.0.0.1:7823/health"
VENV_UVICORN="$HOME/.opal/.venv/bin/uvicorn"

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
    if [ -n "${2:-}" ]; then
        printf '       reason: %s\n' "$2"
    fi
}

# ---------------- scratch 준비 + 프로세스 정리 (격리 규약 [MUST]) ----------------
SCRATCH="$(mktemp -d)"
SERVER_PIDS=()

cleanup() {
    local pid
    for pid in "${SERVER_PIDS[@]:-}"; do
        [ -z "$pid" ] && continue
        kill -TERM "$pid" 2>/dev/null || true
    done
    sleep 1
    for pid in "${SERVER_PIDS[@]:-}"; do
        [ -z "$pid" ] && continue
        kill -0 "$pid" 2>/dev/null && kill -KILL "$pid" 2>/dev/null || true
    done
    rm -rf "$SCRATCH"
}
trap cleanup EXIT

# ---------------- 유틸: ephemeral 포트 취득 ----------------
get_ephemeral_port() {
    python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()'
}

# ---------------- 유틸: health 폴링 (최대 30초) ----------------
wait_for_health() {
    local url="$1"
    local i
    for i in $(seq 1 30); do
        if curl -s -o /dev/null --max-time 1 "$url" 2>/dev/null; then
            return 0
        fi
        sleep 1
    done
    return 1
}

# ---------------- 유틸: HTTP status 코드 취득 ----------------
http_code() {
    curl -s -o /dev/null -w '%{http_code}' --max-time 2 "$1" 2>/dev/null || echo "000"
}

# ---------------- 유틸: 실제 서버 기동 ----------------
# 주의: SERVER_PIDS 배열은 명령 치환(subshell)에서 갱신해도 부모 셸에 반영되지
# 않으므로, 반드시 이 함수를 subshell 없이 직접 호출하고 pid_out_file에서 값을
# 읽어 SERVER_PIDS에 append 한다.
start_server() {
    local app_dir="$1" port="$2" opal_home="$3" log_path="$4" pid_out_file="$5"
    OPAL_HOME="$opal_home" "$VENV_UVICORN" \
        --app-dir "$app_dir" \
        dashboard.backend.main:app \
        --host 127.0.0.1 \
        --port "$port" \
        >"$log_path" 2>&1 &
    local pid=$!
    printf '%s' "$pid" > "$pid_out_file"
    SERVER_PIDS+=("$pid")
}

# ---------------- console_stop_unsafe: console.sh에 전역 pkill 패턴 잔존 여부 ----------------
console_stop_unsafe() {
    grep -q 'pkill -f "dashboard.backend.main:app"' "$CONSOLE_SH" 2>/dev/null
}

# ---------------- 유틸: console.sh source용 최소 UI 함수 스텁 ----------------
# run.sh가 정의하는 info/success/warn/error를 재현한다(색상 생략, 토큰 검사에는 무관).
info()    { echo "[INFO] $1"; }
success() { echo "  OK  $1"; }
warn()    { echo "[WARN] $1"; }
error()   { echo "[ERROR] $1" >&2; }

# ---------------- D-17: 픽스처 정상 레코드의 단일 writer ----------------
# write_record <opal_home> <app_dir> <host> <port> <pid> — console_write_pid_record를
# source 호출한다. 반환값은 그 함수의 exit code(1회차 RED에서는 함수 부재로 127).
write_record() {
    local opal_home="$1" app_dir="$2" host="$3" port="$4" pid="$5"
    local rc
    if ( set +e
         source "$CONSOLE_SH" >/dev/null 2>&1
         console_write_pid_record "$opal_home" "$app_dir" "$host" "$port" "$pid"
       ); then
        rc=0
    else
        rc=$?
    fi
    return "$rc"
}

# ---------------- D-16(b): pkill argv 스텁 경유 cmd_console stop 호출 ----------------
# run_stop_stub <opal_home> — 결과를 STOP_STDOUT / STOP_PKILL_LOG 전역에 기록.
CURRENT_PKILL_LOG=""
STOP_STDOUT=""
STOP_PKILL_LOG=""
run_stop_stub() {
    local opal_home="$1"
    CURRENT_PKILL_LOG="$SCRATCH/pkill-$$-$RANDOM-$RANDOM.log"
    : > "$CURRENT_PKILL_LOG"
    STOP_STDOUT="$( (
        set +e
        pkill() { printf '%s\n' "$*" >> "$CURRENT_PKILL_LOG"; return 0; }
        OPAL_HOME="$opal_home"
        export OPAL_HOME
        source "$CONSOLE_SH" >/dev/null 2>&1
        cmd_console stop
        true
    ) 2>&1 )"
    STOP_PKILL_LOG="$CURRENT_PKILL_LOG"
}

# ---------------- 정적 분석 유틸: case 브랜치 추출 ----------------
extract_case_branch() {
    local file="$1" label="$2"
    awk -v label="$label" '
        BEGIN { found = 0 }
        $0 ~ "^[ \t]*" label "\\)" { found = 1 }
        found { print }
        found && $0 ~ /^[ \t]*;;[ \t]*$/ { exit }
    ' "$file" 2>/dev/null
}

# ---------------- 공통 픽스처: 콘솔역(P1)+E2E역(P2) 서버 쌍 기동 ----------------
# boot_pair <prefix> — 결과는 BOOT_PAIR_OK/BOOT_PAIR_DETAIL, 성공 시 BP_* 전역에 기록.
BOOT_PAIR_OK=0
BOOT_PAIR_DETAIL=""
BP_CONSOLE_HOME=""; BP_E2E_HOME=""; BP_CONSOLE_APP_DIR=""
BP_P1_PORT=""; BP_P2_PORT=""; BP_P1_PID=""; BP_P2_PID=""
BP_P1_HEALTH=""; BP_P2_HEALTH=""
boot_pair() {
    local prefix="$1"
    local console_home="$SCRATCH/$prefix/console-home/.opal"
    local e2e_home="$SCRATCH/$prefix/e2e-home/.opal"
    local console_app_dir="$console_home/dashboard-server"
    mkdir -p "$console_app_dir" "$e2e_home"
    ln -s "$REPO_ROOT/dashboard" "$console_app_dir/dashboard"

    local p1_port p2_port
    p1_port="$(get_ephemeral_port)"
    p2_port="$(get_ephemeral_port)"
    if [ "$p1_port" = "7823" ] || [ "$p2_port" = "7823" ]; then
        BOOT_PAIR_OK=0
        BOOT_PAIR_DETAIL="ephemeral 포트가 7823과 충돌 p1=$p1_port p2=$p2_port"
        return 0
    fi

    local p1_log="$SCRATCH/$prefix-p1.log"
    local p2_log="$SCRATCH/$prefix-p2.log"
    start_server "$console_app_dir" "$p1_port" "$console_home" "$p1_log" "$SCRATCH/$prefix-p1.pid"
    local p1_pid; p1_pid="$(cat "$SCRATCH/$prefix-p1.pid")"
    start_server "$REPO_ROOT" "$p2_port" "$e2e_home" "$p2_log" "$SCRATCH/$prefix-p2.pid"
    local p2_pid; p2_pid="$(cat "$SCRATCH/$prefix-p2.pid")"
    local p1_health="http://127.0.0.1:$p1_port/health"
    local p2_health="http://127.0.0.1:$p2_port/health"

    local p1_ready=0 p2_ready=0
    wait_for_health "$p1_health" && p1_ready=1
    wait_for_health "$p2_health" && p2_ready=1
    if [ "$p1_ready" -ne 1 ] || [ "$p2_ready" -ne 1 ]; then
        BOOT_PAIR_OK=0
        BOOT_PAIR_DETAIL="health 30초 대기 초과 p1_ready=$p1_ready p2_ready=$p2_ready — 환경 사유"
        return 0
    fi

    BOOT_PAIR_OK=1
    BP_CONSOLE_HOME="$console_home"
    BP_E2E_HOME="$e2e_home"
    BP_CONSOLE_APP_DIR="$console_app_dir"
    BP_P1_PORT="$p1_port"; BP_P2_PORT="$p2_port"
    BP_P1_PID="$p1_pid"; BP_P2_PID="$p2_pid"
    BP_P1_HEALTH="$p1_health"; BP_P2_HEALTH="$p2_health"
}

teardown_pair() {
    kill -TERM "$BP_P1_PID" "$BP_P2_PID" 2>/dev/null || true
    sleep 1
    kill -0 "$BP_P1_PID" 2>/dev/null && kill -KILL "$BP_P1_PID" 2>/dev/null || true
    kill -0 "$BP_P2_PID" 2>/dev/null && kill -KILL "$BP_P2_PID" 2>/dev/null || true
}

# ---------------- C-2 가드: 사용자 7823 health 스위트 시작 시점 기록 ----------------
USER_HEALTH_BEFORE="$(http_code "$USER_HEALTH_URL")"
printf '사용자 127.0.0.1:7823 health (시작): %s\n' "$USER_HEALTH_BEFORE"

if [ ! -x "$VENV_UVICORN" ]; then
    echo "치명적: $VENV_UVICORN 없음 — (다) 그룹 전부 skip 처리" >&2
fi

# =============================================================================
# (가) 정적 계약 — S-1, S-2, S-9, S-10, S-13
# =============================================================================
printf '\n== (가) 정적 계약 (S-1, S-2, S-9, S-10, S-13) ==\n\n'

# --- S-1 (acceptance 3, red_required: true) ---
TC="S-1: console.sh·install-mac.sh 양쪽 pkill -f \"dashboard.backend.main:app\" 0건, pkill/pgrep/killall 0건, bash -n exit 0 (MV-21)"
s1_pkill_pattern_console="$(grep -c 'pkill -f "dashboard.backend.main:app"' "$CONSOLE_SH" 2>/dev/null || true)"
s1_pkill_pattern_install="$(grep -c 'pkill -f "dashboard.backend.main:app"' "$INSTALL_MAC_SH" 2>/dev/null || true)"
s1_names_console="$(grep -Ec '\b(pkill|pgrep|killall)\b' "$CONSOLE_SH" 2>/dev/null || true)"
s1_names_install="$(grep -Ec '\b(pkill|pgrep|killall)\b' "$INSTALL_MAC_SH" 2>/dev/null || true)"
: "${s1_pkill_pattern_console:=0}"; : "${s1_pkill_pattern_install:=0}"
: "${s1_names_console:=0}"; : "${s1_names_install:=0}"
s1_bash_n_ok=1
bash -n "$CONSOLE_SH" 2>/dev/null || s1_bash_n_ok=0
bash -n "$INSTALL_MAC_SH" 2>/dev/null || s1_bash_n_ok=0
if [ "$s1_pkill_pattern_console" -eq 0 ] && [ "$s1_pkill_pattern_install" -eq 0 ] \
    && [ "$s1_names_console" -eq 0 ] && [ "$s1_names_install" -eq 0 ] \
    && [ "$s1_bash_n_ok" -eq 1 ]; then
    pass "$TC"
else
    fail "$TC" "console.sh: pkill_pattern=$s1_pkill_pattern_console names=$s1_names_console | install-mac.sh: pkill_pattern=$s1_pkill_pattern_install names=$s1_names_install | bash_n_ok=$s1_bash_n_ok"
fi

# --- S-2 (MV-22 회귀 감시, red_required: false — RED 시점 PASS가 정상. 조작 금지) ---
# 감시 대상은 **구현**이다. `tests/` 아래에는 "clean은 console.pid를 보지 않는다"를
# 단언하는 경계 테스트가 그 문자열을 인용으로 들고 있으므로(예:
# tests/test_e2e_status_clean.py), 문자열 출현만 보는 감시는 그 테스트를 위반으로
# 오판정한다. 금지 대상과 금지를 단언하는 테스트를 같은 칸에 넣지 않는다.
# 감시 대상은 **실행 코드**다. 제외 대상 셋 모두 "읽지 않는다"를 문자로 적을 뿐 읽지
# 않는다 — tests/(금지를 단언하는 경계 테스트), __pycache__(파생물), *.md(그 금지를
# 서술하는 README). 금지 대상과 금지를 기술한 문서를 같은 칸에 넣지 않는다.
TC="S-2: grep -rc 'console\\.pid' opal/tools/test-tool/ (tests·문서 제외) == 0 (MV-22 경계 회귀 감시)"
if grep -rq --exclude-dir=tests --exclude-dir=__pycache__ --exclude='*.md' 'console\.pid' "$TEST_TOOL_DIR" 2>/dev/null; then
    fail "$TC" "$(grep -rn --exclude-dir=tests --exclude-dir=__pycache__ --exclude='*.md' 'console\.pid' "$TEST_TOOL_DIR" 2>/dev/null | head -5)"
else
    pass "$TC (RED 시점에도 PASS — 회귀 감시용, 통과시키려 조작하지 않음)"
fi

# --- S-9 (acceptance 3, red_required: true) ---
TC="S-9: install-mac.sh console_autostart 종료 블록이 D-13 3분기(FRAMEWORK_ROOT/opal/tools/opal-cli/run.sh 위임, || true) + bash -n"
autostart_body="$(awk '
    /^console_autostart\(\)[ \t]*\{/ { found = 1; print; next }
    found && /^[A-Za-z_][A-Za-z0-9_]*\(\)[ \t]*\{/ { exit }
    found { print }
' "$INSTALL_MAC_SH" 2>/dev/null)"
s9_bash_n_ok=1
bash -n "$INSTALL_MAC_SH" 2>/dev/null || s9_bash_n_ok=0
if [ -z "$autostart_body" ]; then
    fail "$TC" "install-mac.sh에 console_autostart 함수가 없음"
elif echo "$autostart_body" | grep -q 'opal-cli/run.sh console stop' \
    && echo "$autostart_body" | grep -q 'FRAMEWORK_ROOT' \
    && echo "$autostart_body" | grep -q 'elif' \
    && echo "$autostart_body" | grep -q '|| true' \
    && [ "$s9_bash_n_ok" -eq 1 ]; then
    pass "$TC"
else
    fail "$TC" "위임 문자열·elif 3분기·|| true 중 일부 미발견 (GREEN 이전 정상) bash_n_ok=$s9_bash_n_ok"
fi

# --- S-10 (F-7, red_required: true): start 통합 정적 ---
TC="S-10: start 블록 — nohup 직후 local pid=\$!, writer 5인자 호출, 이후 \$! 미사용, nohup 이전 값 제약(D-12) 사전 검증"
start_branch="$(extract_case_branch "$CONSOLE_SH" start)"
s10_ok=1; s10_detail=""
if [ -z "$start_branch" ]; then
    s10_ok=0; s10_detail="start 브랜치 없음"
else
    if ! printf '%s\n' "$start_branch" | grep -q 'nohup'; then
        s10_ok=0; s10_detail="nohup 백그라운드 기동 라인 없음"
        nohup_line=""
    else
        # nohup ... & 는 백슬래시로 개행된 다중행 명령이므로, 배경 실행 연산자(&)가
        # 실제로 종료되는 마지막 행(예: '>"$log_file" 2>&1 &')을 nohup_line으로 삼는다.
        nohup_line="$(printf '%s\n' "$start_branch" | grep -nE ' &[[:space:]]*$' | head -1 | cut -d: -f1 || true)"
    fi
    if [ -z "$nohup_line" ]; then
        s10_ok=0; s10_detail="nohup 배경 실행(&) 종료 라인을 찾을 수 없음"
    else
        pid_capture_line="$(printf '%s\n' "$start_branch" | grep -n 'local pid=\$!' | head -1 | cut -d: -f1 || true)"
        writer_line="$(printf '%s\n' "$start_branch" | grep -n 'console_write_pid_record "\$opal_home" "\$dashboard_server" "\$host" "\$port" "\$pid"' | head -1 | cut -d: -f1 || true)"
        if [ -z "$pid_capture_line" ] || [ "$pid_capture_line" -ne $((nohup_line + 1)) ]; then
            s10_ok=0; s10_detail="local pid=\$! 이 nohup 직후 줄에 없음 (nohup=$nohup_line pid_capture=${pid_capture_line:-none})"
        elif [ -z "$writer_line" ] || [ "$writer_line" -le "$pid_capture_line" ]; then
            s10_ok=0; s10_detail="console_write_pid_record 5인자 호출 없음 또는 pid 캡처보다 앞 (writer=${writer_line:-none})"
        else
            tail_after_writer="$(printf '%s\n' "$start_branch" | tail -n +$((writer_line + 1)))"
            if printf '%s\n' "$tail_after_writer" | grep -qF '$!'; then
                s10_ok=0; s10_detail="writer 호출 이후에도 \$! 인라인 사용 잔존(console.sh:81 미교체)"
            else
                pre_nohup="$(printf '%s\n' "$start_branch" | head -n $((nohup_line - 1)))"
                if ! printf '%s\n' "$pre_nohup" | grep -Eq '^[ \t]*case[ \t]+"?\$(opal_home|dashboard_server)"?[ \t]+in' \
                    && ! printf '%s\n' "$pre_nohup" | grep -Eq '\[\[[^]]*(\$opal_home|\$dashboard_server)[^]]*==[^]]*\*'"'"'"'"'"'[^]]*\]\]'; then
                    s10_ok=0; s10_detail="nohup 이전 값 제약(D-12 가) 구조 단언 실패 — opal_home/dashboard_server 피연산자 case 또는 [[ ... == *'\"'* ]] 미발견"
                fi
            fi
        fi
    fi
fi
if [ "$s10_ok" -eq 1 ]; then pass "$TC"; else fail "$TC" "$s10_detail"; fi

# --- S-13 (F-6, red_required: true): start 3분기 정적 ---
TC="S-13: start 3분기 — ①이미실행중 return0 ②레코드없이 health응답시 writer미호출+lsof토큰+return0 ③그외만 기동"
s13_ok=1; s13_detail=""
if [ -z "$start_branch" ]; then
    s13_ok=0; s13_detail="start 브랜치 없음"
else
    branch1_ok=0
    if printf '%s\n' "$start_branch" | grep -q '이미 실행 중' \
        && printf '%s\n' "$start_branch" | grep -q 'return 0' \
        && printf '%s\n' "$start_branch" | grep -Eq 'kill -0[[:space:]]+"?\$pid"?' \
        && printf '%s\n' "$start_branch" | grep -Eq '\$app_dir'; then
        branch1_ok=1
    fi
    branch2_ok=0
    if printf '%s\n' "$start_branch" | grep -qF 'lsof -ti tcp:7823'; then
        branch2_section="$(printf '%s\n' "$start_branch" | awk '/lsof -ti tcp:7823/{f=1} f{print} f && /return 0/{exit}')"
        if ! printf '%s\n' "$branch2_section" | grep -q 'console_write_pid_record'; then
            branch2_ok=1
        fi
    fi
    branch3_ok=0
    if printf '%s\n' "$start_branch" | grep -q 'nohup' && printf '%s\n' "$start_branch" | grep -q 'console_write_pid_record'; then
        branch3_ok=1
    fi
    if [ "$branch1_ok" -ne 1 ] || [ "$branch2_ok" -ne 1 ] || [ "$branch3_ok" -ne 1 ]; then
        s13_ok=0
        s13_detail="branch1(이미실행중)=$branch1_ok branch2(레코드없이health응답)=$branch2_ok branch3(정상기동)=$branch3_ok"
    fi
fi
if [ "$s13_ok" -eq 1 ]; then pass "$TC"; else fail "$TC" "$s13_detail"; fi

# =============================================================================
# (나) 레코드-only — S-3, S-11, S-12, S-14 (mock, 서버 기동 없음)
# =============================================================================
printf '\n== (나) 레코드-only (S-3, S-11, S-12, S-14) ==\n\n'

# --- S-3 (MV-23, red_required: true): console_write_pid_record 단위 + D-12 값 제약 ---
TC="S-3: console_write_pid_record 호출 → \$OPAL_HOME/run/console.pid 6필드 JSON 생성 (MV-23)"
S3_OPAL_HOME="$SCRATCH/s3/console-home/.opal"
S3_APP_DIR="$S3_OPAL_HOME/dashboard-server"
S3_PORT="$(get_ephemeral_port)"
mkdir -p "$S3_OPAL_HOME"
S3_RECORD_PATH="$S3_OPAL_HOME/run/console.pid"

write_record "$S3_OPAL_HOME" "$S3_APP_DIR" 127.0.0.1 "$S3_PORT" "$$" || true

if [ ! -f "$S3_RECORD_PATH" ]; then
    fail "$TC" "레코드 파일 없음: $S3_RECORD_PATH (console_write_pid_record 미신설 — RED 정상)"
else
    s3_json_valid=0
    python3 -m json.tool "$S3_RECORD_PATH" >/dev/null 2>&1 && s3_json_valid=1
    s3_keys="$(python3 -c '
import json, sys
try:
    with open(sys.argv[1], encoding="utf-8") as f:
        d = json.load(f)
    print(",".join(sorted(d.keys())))
except Exception:
    print("__ERR__")
' "$S3_RECORD_PATH" 2>/dev/null)"
    expected_keys="app_dir,host,opal_home,pid,port,started_at"
    s3_types_ok=0
    if python3 -c '
import json, sys
try:
    with open(sys.argv[1], encoding="utf-8") as f:
        d = json.load(f)
    assert isinstance(d.get("pid"), int)
    assert isinstance(d.get("port"), int)
    assert d.get("app_dir") == sys.argv[2] + "/dashboard-server"
    from datetime import datetime
    datetime.fromisoformat(d.get("started_at").replace("Z", "+00:00"))
    sys.exit(0)
except Exception:
    sys.exit(1)
' "$S3_RECORD_PATH" "$S3_OPAL_HOME" 2>/dev/null; then
        s3_types_ok=1
    fi
    if [ "$s3_json_valid" -eq 1 ] && [ "$s3_keys" = "$expected_keys" ] && [ "$s3_types_ok" -eq 1 ]; then
        pass "$TC"
    else
        fail "$TC" "json_valid=$s3_json_valid keys='$s3_keys' (expected='$expected_keys') types_ok=$s3_types_ok"
    fi
fi

TC="S-3b: 값 제약 위반(D-2·D-12) — \"·개행 포함 경로 인자 호출 시 return 1 + 파일 미생성"
S3B_OPAL_HOME="$SCRATCH/s3b/console-home/.opal"
mkdir -p "$S3B_OPAL_HOME"
S3B_BAD_APP_DIR="$S3B_OPAL_HOME/dash\"board-server"
S3B_RECORD_PATH="$S3B_OPAL_HOME/run/console.pid"
s3b_exit=0
if write_record "$S3B_OPAL_HOME" "$S3B_BAD_APP_DIR" 127.0.0.1 12345 12345; then
    s3b_exit=0
else
    s3b_exit=$?
fi
if [ "$s3b_exit" -eq 1 ] && [ ! -f "$S3B_RECORD_PATH" ]; then
    pass "$TC"
else
    fail "$TC" "exit=$s3b_exit (expected 1) record_exists=$([ -f "$S3B_RECORD_PATH" ] && echo yes || echo no)"
fi

TC="S-3b(역슬래시): 값 제약 위반(D-2) — 역슬래시 포함 경로 인자 호출 시 return 1 + 파일 미생성"
S3B2_OPAL_HOME="$SCRATCH/s3b2/console-home/.opal"
mkdir -p "$S3B2_OPAL_HOME"
S3B2_BAD_APP_DIR="$S3B2_OPAL_HOME/dash\\board-server"
S3B2_RECORD_PATH="$S3B2_OPAL_HOME/run/console.pid"
s3b2_exit=0
if write_record "$S3B2_OPAL_HOME" "$S3B2_BAD_APP_DIR" 127.0.0.1 12345 12345; then
    s3b2_exit=0
else
    s3b2_exit=$?
fi
if [ "$s3b2_exit" -eq 1 ] && [ ! -f "$S3B2_RECORD_PATH" ]; then
    pass "$TC"
else
    fail "$TC" "exit=$s3b2_exit (expected 1) record_exists=$([ -f "$S3B2_RECORD_PATH" ] && echo yes || echo no)"
fi

TC="S-3b(개행): 값 제약 위반(D-2) — 개행 포함 경로 인자 호출 시 return 1 + 파일 미생성"
S3B3_OPAL_HOME="$SCRATCH/s3b3/console-home/.opal"
mkdir -p "$S3B3_OPAL_HOME"
S3B3_BAD_APP_DIR="$(printf '%s\ndash-server' "$S3B3_OPAL_HOME")"
S3B3_RECORD_PATH="$S3B3_OPAL_HOME/run/console.pid"
s3b3_exit=0
if write_record "$S3B3_OPAL_HOME" "$S3B3_BAD_APP_DIR" 127.0.0.1 12345 12345; then
    s3b3_exit=0
else
    s3b3_exit=$?
fi
if [ "$s3b3_exit" -eq 1 ] && [ ! -f "$S3B3_RECORD_PATH" ]; then
    pass "$TC"
else
    fail "$TC" "exit=$s3b3_exit (expected 1) record_exists=$([ -f "$S3B3_RECORD_PATH" ] && echo yes || echo no)"
fi

# --- S-11 (판정표 #2, red_required: true, D-17 예외: printf 직접 오염) ---
TC="S-11: 판정표 #2 unreadable_record — pid 비정수 오염 레코드 → stopped=false pid=- reason=unreadable_record, 레코드 잔존, kill 0회"
S11_HOME="$SCRATCH/s11-home/.opal"
mkdir -p "$S11_HOME/run"
S11_RECORD="$S11_HOME/run/console.pid"
printf '{"pid": "abc", "opal_home": "%s", "app_dir": "%s/dashboard-server", "host": "127.0.0.1", "port": 9999, "started_at": "2026-09-13T00:00:00+0000"}' \
    "$S11_HOME" "$S11_HOME" > "$S11_RECORD"
run_stop_stub "$S11_HOME"
if echo "$STOP_STDOUT" | grep -q 'stopped=false' \
    && echo "$STOP_STDOUT" | grep -q 'pid=-' \
    && echo "$STOP_STDOUT" | grep -q 'reason=unreadable_record' \
    && [ -f "$S11_RECORD" ] \
    && [ ! -s "$STOP_PKILL_LOG" ]; then
    pass "$TC"
else
    fail "$TC" "stdout='$STOP_STDOUT' record_exists=$([ -f "$S11_RECORD" ] && echo yes || echo no) pkill_log='$(cat "$STOP_PKILL_LOG" 2>/dev/null)'"
fi

# --- S-12 (판정표 #4, red_required: true, D-17 writer 사용) ---
TC="S-12: 판정표 #4 stale_record — 확실히 죽은 pid로 identity 일치 레코드 → stopped=false pid=<N> reason=stale_record + 레코드 삭제"
S12_HOME="$SCRATCH/s12-home/.opal"
S12_APP_DIR="$S12_HOME/dashboard-server"
mkdir -p "$S12_APP_DIR"
( exec true ) &
S12_DEAD_PID=$!
wait "$S12_DEAD_PID" 2>/dev/null || true
write_record "$S12_HOME" "$S12_APP_DIR" 127.0.0.1 9998 "$S12_DEAD_PID" || true
S12_RECORD="$S12_HOME/run/console.pid"
if [ ! -f "$S12_RECORD" ]; then
    fail "$TC" "픽스처 레코드 생성 실패(console_write_pid_record 미신설 — RED 정상)"
else
    run_stop_stub "$S12_HOME"
    if echo "$STOP_STDOUT" | grep -q 'stopped=false' \
        && echo "$STOP_STDOUT" | grep -q "pid=$S12_DEAD_PID" \
        && echo "$STOP_STDOUT" | grep -q 'reason=stale_record' \
        && [ ! -f "$S12_RECORD" ]; then
        pass "$TC"
    else
        fail "$TC" "stdout='$STOP_STDOUT' record_exists=$([ -f "$S12_RECORD" ] && echo yes || echo no)"
    fi
fi

# --- S-14 (판정표 #6, red_required: true, D-17 writer 사용) ---
TC="S-14: 판정표 #6 terminate_timeout — SIGTERM 무시 프로세스 → 5초 후 stopped=false pid=<N> reason=terminate_timeout, 프로세스 생존"
S14_HOME="$SCRATCH/s14-home/.opal"
S14_APP_DIR="$S14_HOME/dashboard-server"
mkdir -p "$S14_APP_DIR"
bash -c 'trap "" TERM; while :; do sleep 1; done' &
S14_PID=$!
SERVER_PIDS+=("$S14_PID")
sleep 0.3
write_record "$S14_HOME" "$S14_APP_DIR" 127.0.0.1 9997 "$S14_PID" || true
S14_RECORD="$S14_HOME/run/console.pid"
if [ ! -f "$S14_RECORD" ]; then
    fail "$TC" "픽스처 레코드 생성 실패(console_write_pid_record 미신설 — RED 정상)"
else
    S14_START="$(date +%s)"
    run_stop_stub "$S14_HOME"
    S14_ELAPSED=$(( $(date +%s) - S14_START ))
    s14_alive=0; kill -0 "$S14_PID" 2>/dev/null && s14_alive=1
    if echo "$STOP_STDOUT" | grep -q 'stopped=false' \
        && echo "$STOP_STDOUT" | grep -q "pid=$S14_PID" \
        && echo "$STOP_STDOUT" | grep -q 'reason=terminate_timeout' \
        && [ "$s14_alive" -eq 1 ] \
        && [ "$S14_ELAPSED" -ge 4 ]; then
        pass "$TC"
    else
        fail "$TC" "stdout='$STOP_STDOUT' alive=$s14_alive elapsed=${S14_ELAPSED}s (D-6 5초 상한 관측 목적, 케이스 예산 10초)"
    fi
fi
kill -9 "$S14_PID" 2>/dev/null || true

# =============================================================================
# (다) real-usage — S-8(선두) → S-4, S-5, S-6, S-7
# =============================================================================
printf '\n== (다) real-usage (S-8 → S-4, S-5, S-6, S-7) ==\n\n'

# --- S-8 (acceptance 5, red_required: false — status는 stop 미호출, 안전) ---
TC="S-8: console status — pid=/app_dir=/opal_home=/host=/port=/started_at= 값 일치 + health 원문이 레코드 줄보다 앞 + health 성패 양분기 레코드 출력"
if [ ! -x "$VENV_UVICORN" ]; then
    skip "$TC" "venv uvicorn 없음: $VENV_UVICORN"
else
    S8_HOME="$SCRATCH/s8-home/.opal"
    S8_APP_DIR="$S8_HOME/dashboard-server"
    mkdir -p "$S8_APP_DIR"
    ln -s "$REPO_ROOT/dashboard" "$S8_APP_DIR/dashboard"
    S8_PORT="$(get_ephemeral_port)"
    if [ "$S8_PORT" = "7823" ]; then
        fail "$TC" "S-8 전용 ephemeral 포트가 7823과 충돌"
    else
        S8_LOG="$SCRATCH/s8.log"
        start_server "$S8_APP_DIR" "$S8_PORT" "$S8_HOME" "$S8_LOG" "$SCRATCH/s8.pid"
        S8_PID="$(cat "$SCRATCH/s8.pid")"
        S8_HEALTH="http://127.0.0.1:$S8_PORT/health"
        if ! wait_for_health "$S8_HEALTH"; then
            skip "$TC" "S-8 전용 서버 health 30초 대기 초과 — 환경 사유"
        else
            write_record "$S8_HOME" "$S8_APP_DIR" 127.0.0.1 "$S8_PORT" "$S8_PID" || true
            S8_RECORD="$S8_HOME/run/console.pid"
            if [ ! -f "$S8_RECORD" ]; then
                fail "$TC" "픽스처 레코드 생성 실패(console_write_pid_record 미신설 — RED 정상)"
            else
                s8_health_code="$(http_code "$USER_HEALTH_URL")"
                s8_output="$(OPAL_HOME="$S8_HOME" bash "$RUN_SH" console status 2>&1 || true)"
                s8_exit=0
                OPAL_HOME="$S8_HOME" bash "$RUN_SH" console status >/dev/null 2>&1 || s8_exit=$?

                s8_pid_ok=0; echo "$s8_output" | grep -Eq "(^|[^0-9])pid=${S8_PID}([^0-9]|$)" && s8_pid_ok=1
                s8_appdir_ok=0; echo "$s8_output" | grep -qF "app_dir=$S8_APP_DIR" && s8_appdir_ok=1
                s8_opalhome_ok=0; echo "$s8_output" | grep -qF "opal_home=$S8_HOME" && s8_opalhome_ok=1
                s8_host_ok=0; echo "$s8_output" | grep -q 'host=127\.0\.0\.1' && s8_host_ok=1
                s8_port_ok=0; echo "$s8_output" | grep -qF "port=$S8_PORT" && s8_port_ok=1
                s8_started_ok=0; echo "$s8_output" | grep -q 'started_at=' && s8_started_ok=1
                s8_record_present=$(( s8_pid_ok & s8_appdir_ok & s8_opalhome_ok & s8_host_ok & s8_port_ok & s8_started_ok ))

                s8_order_ok=1
                if [ "$s8_health_code" = "200" ]; then
                    health_line="$(echo "$s8_output" | grep -n '"status"' | head -1 | cut -d: -f1 || true)"
                    record_line="$(echo "$s8_output" | grep -n "pid=$S8_PID" | head -1 | cut -d: -f1 || true)"
                    if [ -z "$health_line" ] || [ -z "$record_line" ] || [ "$health_line" -ge "$record_line" ]; then
                        s8_order_ok=0
                    fi
                fi

                s8_exit_ok=0
                if [ "$s8_health_code" = "200" ] && [ "$s8_exit" -eq 0 ]; then s8_exit_ok=1; fi
                if [ "$s8_health_code" != "200" ] && [ "$s8_exit" -ne 0 ]; then s8_exit_ok=1; fi

                if [ "$s8_record_present" -eq 1 ] && [ "$s8_order_ok" -eq 1 ] && [ "$s8_exit_ok" -eq 1 ]; then
                    pass "$TC"
                else
                    fail "$TC" "record(pid=$s8_pid_ok,app_dir=$s8_appdir_ok,opal_home=$s8_opalhome_ok,host=$s8_host_ok,port=$s8_port_ok,started_at=$s8_started_ok) order_ok=$s8_order_ok exit_ok=$s8_exit_ok(health=$s8_health_code,exit=$s8_exit) output='$s8_output'"
                fi
                rm -f "$S8_RECORD"
            fi
        fi
        kill -TERM "$S8_PID" 2>/dev/null || true
        sleep 1
        kill -0 "$S8_PID" 2>/dev/null && kill -KILL "$S8_PID" 2>/dev/null || true
    fi
fi

# --- S-4 (판정표 #1, red_required: true, D-16 (a)+(b)) ---
TC="S-4: 레코드 부재 — no_record + D-9 lsof 토큰 + 두 서버 생존"
if [ ! -x "$VENV_UVICORN" ]; then
    skip "$TC" "venv uvicorn 없음: $VENV_UVICORN"
else
    boot_pair s4
    if [ "$BOOT_PAIR_OK" -ne 1 ]; then
        skip "$TC" "$BOOT_PAIR_DETAIL"
    else
        s4_user_pid="$(lsof -ti tcp:7823 2>/dev/null | head -1 || true)"
        s4_pgrep_set="$(pgrep -f "dashboard.backend.main:app" 2>/dev/null || true)"
        s4_pgrep_ok=1
        echo "$s4_pgrep_set" | grep -qx "$BP_P1_PID" || s4_pgrep_ok=0
        echo "$s4_pgrep_set" | grep -qx "$BP_P2_PID" || s4_pgrep_ok=0
        if [ -n "$s4_user_pid" ]; then
            echo "$s4_pgrep_set" | grep -qx "$s4_user_pid" || s4_pgrep_ok=0
        fi
        if [ "$s4_pgrep_ok" -eq 1 ]; then
            pass "S-4(a): pgrep -f dashboard.backend.main:app 매치 집합이 P1·P2·사용자7823 pid 모두 포함 (RK-1 사전 실패 증명)"
        else
            fail "S-4(a): pgrep 집합 중첩 미확인" "pgrep_set='$s4_pgrep_set' p1=$BP_P1_PID p2=$BP_P2_PID user=$s4_user_pid"
        fi

        run_stop_stub "$BP_CONSOLE_HOME"
        s4_p1_alive=0; kill -0 "$BP_P1_PID" 2>/dev/null && s4_p1_alive=1
        s4_p2_alive=0; kill -0 "$BP_P2_PID" 2>/dev/null && s4_p2_alive=1
        if [ "$s4_p1_alive" -eq 1 ] && [ "$s4_p2_alive" -eq 1 ] \
            && echo "$STOP_STDOUT" | grep -q 'stopped=false' \
            && echo "$STOP_STDOUT" | grep -q 'pid=-' \
            && echo "$STOP_STDOUT" | grep -q 'reason=no_record' \
            && echo "$STOP_STDOUT" | grep -qF 'lsof -ti tcp:7823' \
            && [ ! -s "$STOP_PKILL_LOG" ]; then
            pass "$TC"
        else
            fail "$TC" "p1_alive=$s4_p1_alive p2_alive=$s4_p2_alive stdout='$STOP_STDOUT' pkill_log='$(cat "$STOP_PKILL_LOG" 2>/dev/null)'"
        fi
        teardown_pair
    fi
fi

# --- S-5 (판정표 #3, red_required: true, D-16 (b)) ---
TC="S-5: identity 불일치 — 레코드 app_dir 타 홈 → 두 서버 생존 + reason=identity_mismatch + 레코드 잔존"
if [ ! -x "$VENV_UVICORN" ]; then
    skip "$TC" "venv uvicorn 없음: $VENV_UVICORN"
else
    boot_pair s5
    if [ "$BOOT_PAIR_OK" -ne 1 ]; then
        skip "$TC" "$BOOT_PAIR_DETAIL"
    else
        s5_other_app_dir="$SCRATCH/s5/other-home/.opal/dashboard-server"
        write_record "$BP_CONSOLE_HOME" "$s5_other_app_dir" 127.0.0.1 "$BP_P1_PORT" "$BP_P1_PID" || true
        s5_record="$BP_CONSOLE_HOME/run/console.pid"
        if [ ! -f "$s5_record" ]; then
            fail "$TC" "픽스처 레코드 생성 실패(console_write_pid_record 미신설 — RED 정상)"
        else
            run_stop_stub "$BP_CONSOLE_HOME"
            s5_p1_alive=0; kill -0 "$BP_P1_PID" 2>/dev/null && s5_p1_alive=1
            s5_p2_alive=0; kill -0 "$BP_P2_PID" 2>/dev/null && s5_p2_alive=1
            if [ "$s5_p1_alive" -eq 1 ] && [ "$s5_p2_alive" -eq 1 ] \
                && echo "$STOP_STDOUT" | grep -q 'reason=identity_mismatch' \
                && [ -f "$s5_record" ] \
                && [ ! -s "$STOP_PKILL_LOG" ]; then
                pass "$TC"
            else
                fail "$TC" "p1_alive=$s5_p1_alive p2_alive=$s5_p2_alive record_exists=$([ -f "$s5_record" ] && echo yes || echo no) stdout='$STOP_STDOUT'"
            fi
        fi
        teardown_pair
    fi
fi

# --- S-6 (판정표 #5, F-8, red_required: true, D-16 (a)+(b)) ---
TC="S-6: AC-3 정방향(MV-37) — console stop이 P1만 종료, P2 생존, stopped=true, 사용자 7823 불변"
if [ ! -x "$VENV_UVICORN" ]; then
    skip "$TC" "venv uvicorn 없음: $VENV_UVICORN"
else
    boot_pair s6
    if [ "$BOOT_PAIR_OK" -ne 1 ]; then
        skip "$TC" "$BOOT_PAIR_DETAIL"
    else
        write_record "$BP_CONSOLE_HOME" "$BP_CONSOLE_APP_DIR" 127.0.0.1 "$BP_P1_PORT" "$BP_P1_PID" || true
        s6_record="$BP_CONSOLE_HOME/run/console.pid"
        if [ ! -f "$s6_record" ]; then
            fail "$TC" "픽스처 레코드 생성 실패(console_write_pid_record 미신설 — RED 정상)"
        else
            s6_user_pid="$(lsof -ti tcp:7823 2>/dev/null | head -1 || true)"
            s6_pgrep_set="$(pgrep -f "dashboard.backend.main:app" 2>/dev/null || true)"
            s6_pgrep_ok=1
            echo "$s6_pgrep_set" | grep -qx "$BP_P1_PID" || s6_pgrep_ok=0
            echo "$s6_pgrep_set" | grep -qx "$BP_P2_PID" || s6_pgrep_ok=0
            if [ -n "$s6_user_pid" ]; then
                echo "$s6_pgrep_set" | grep -qx "$s6_user_pid" || s6_pgrep_ok=0
            fi
            if [ "$s6_pgrep_ok" -eq 1 ]; then
                pass "S-6(a): pgrep 매치 집합이 P1·P2·사용자7823 pid 모두 포함"
            else
                fail "S-6(a): pgrep 집합 중첩 미확인" "pgrep_set='$s6_pgrep_set' p1=$BP_P1_PID p2=$BP_P2_PID user=$s6_user_pid"
            fi

            # S-6(b)는 RED 전용 단언이다 (D-16). GREEN(전역 pkill 제거)에서는 스텁을 거치지
            # 않고 cmd_console stop이 실서버를 실제로 종료하므로, 스텁 경로에서 P1 생존을
            # 확인하는 이 단언은 무의미해질 뿐 아니라 아래 S-6(functional)의 전제(레코드
            # 잔존)를 자기 자신이 깨뜨린다. gating 밖(=GREEN)에서는 집계하지 않는다 —
            # 그 역할은 S-6(functional)이 대체한다.
            if console_stop_unsafe; then
                run_stop_stub "$BP_CONSOLE_HOME"
                s6_stub_p1_alive=0; kill -0 "$BP_P1_PID" 2>/dev/null && s6_stub_p1_alive=1
                if [ "$s6_stub_p1_alive" -eq 1 ] && [ ! -s "$STOP_PKILL_LOG" ]; then
                    pass "S-6(b): pkill 스텁 로그 비어있음(전역 패턴 미호출) + 스텁 경로에서 P1 생존"
                else
                    fail "S-6(b): pkill 스텁 로그가 비어있지 않음(전역 패턴 잔존) 또는 P1 생존 실패" "p1_alive=$s6_stub_p1_alive pkill_log='$(cat "$STOP_PKILL_LOG" 2>/dev/null)'"
                fi
            fi

            if console_stop_unsafe; then
                skip "S-6(functional): 실제 console stop 서브프로세스 호출" "console.sh에 전역 pkill 패턴이 남아있어 실호출은 사용자 7823을 위협한다(C-2) — GREEN 이후 해제"
            else
                s6_user_before="$(http_code "$USER_HEALTH_URL")"
                s6_output="$(OPAL_HOME="$BP_CONSOLE_HOME" bash "$RUN_SH" console stop 2>&1 || true)"
                sleep 1
                s6_p1_alive=0; kill -0 "$BP_P1_PID" 2>/dev/null && s6_p1_alive=1
                s6_p2_alive=0; kill -0 "$BP_P2_PID" 2>/dev/null && s6_p2_alive=1
                s6_p2_health="$(http_code "$BP_P2_HEALTH")"
                s6_user_after="$(http_code "$USER_HEALTH_URL")"
                if [ "$s6_p1_alive" -eq 0 ] && [ "$s6_p2_alive" -eq 1 ] && [ "$s6_p2_health" = "200" ] \
                    && [ ! -f "$s6_record" ] \
                    && echo "$s6_output" | grep -q "stopped=true" \
                    && echo "$s6_output" | grep -q "pid=$BP_P1_PID" \
                    && [ "$s6_user_before" = "$s6_user_after" ]; then
                    pass "S-6(functional): P1 종료 + P2 생존 + 레코드 삭제 + stopped=true pid=<P1> + 사용자 7823 불변"
                else
                    fail "S-6(functional)" "p1_alive=$s6_p1_alive(expect0) p2_alive=$s6_p2_alive(expect1) p2_health=$s6_p2_health record_exists=$([ -f "$s6_record" ] && echo yes || echo no) output='$s6_output' user_before=$s6_user_before user_after=$s6_user_after"
                fi
            fi
            rm -f "$s6_record"
        fi
        teardown_pair
    fi
fi

# --- S-7 (D-18, F-2, red_required: false — PLAN 근거, 기동 부분은 T02 무관 OS 동작) ---
TC="S-7: AC-3 역방향(D-18) — E2E역 프로세스그룹 종료 시 P1 생존+health200+레코드 잔존+사용자7823 생존, 이후 stop 성공(stopped=true)"
if [ ! -x "$VENV_UVICORN" ]; then
    skip "$TC" "venv uvicorn 없음: $VENV_UVICORN"
else
    S7_CONSOLE_HOME="$SCRATCH/s7/console-home/.opal"
    S7_E2E_HOME="$SCRATCH/s7/e2e-home/.opal"
    S7_CONSOLE_APP_DIR="$S7_CONSOLE_HOME/dashboard-server"
    mkdir -p "$S7_CONSOLE_APP_DIR" "$S7_E2E_HOME"
    ln -s "$REPO_ROOT/dashboard" "$S7_CONSOLE_APP_DIR/dashboard"
    S7_P1_PORT="$(get_ephemeral_port)"
    S7_P2_PORT="$(get_ephemeral_port)"
    if [ "$S7_P1_PORT" = "7823" ] || [ "$S7_P2_PORT" = "7823" ]; then
        fail "$TC" "ephemeral 포트가 7823과 충돌 p1=$S7_P1_PORT p2=$S7_P2_PORT"
    else
        start_server "$S7_CONSOLE_APP_DIR" "$S7_P1_PORT" "$S7_CONSOLE_HOME" "$SCRATCH/s7-p1.log" "$SCRATCH/s7-p1.pid"
        S7_P1_PID="$(cat "$SCRATCH/s7-p1.pid")"
        S7_P1_HEALTH="http://127.0.0.1:$S7_P1_PORT/health"

        # E2E역(P2)은 set -m 구간에서 자기 프로세스 그룹으로 기동 (D-18 — 하네스 process.py 미import)
        set -m
        OPAL_HOME="$S7_E2E_HOME" "$VENV_UVICORN" --app-dir "$REPO_ROOT" dashboard.backend.main:app \
            --host 127.0.0.1 --port "$S7_P2_PORT" >"$SCRATCH/s7-p2.log" 2>&1 &
        S7_P2_PID=$!
        set +m
        SERVER_PIDS+=("$S7_P2_PID")
        S7_P2_HEALTH="http://127.0.0.1:$S7_P2_PORT/health"

        s7_p1_ready=0; wait_for_health "$S7_P1_HEALTH" && s7_p1_ready=1
        s7_p2_ready=0; wait_for_health "$S7_P2_HEALTH" && s7_p2_ready=1
        if [ "$s7_p1_ready" -ne 1 ] || [ "$s7_p2_ready" -ne 1 ]; then
            skip "$TC" "health 30초 대기 초과 p1_ready=$s7_p1_ready p2_ready=$s7_p2_ready — 환경 사유"
        else
            S7_P2_PGID="$(ps -o pgid= -p "$S7_P2_PID" 2>/dev/null | tr -d ' ' || true)"
            if [ "$S7_P2_PGID" != "$S7_P2_PID" ]; then
                fail "$TC (H-5: set -m 효과 미확인)" "P2_PID=$S7_P2_PID P2_PGID=$S7_P2_PGID — pgid==pid 기대"
            else
                write_record "$S7_CONSOLE_HOME" "$S7_CONSOLE_APP_DIR" 127.0.0.1 "$S7_P1_PORT" "$S7_P1_PID" || true
                s7_record="$S7_CONSOLE_HOME/run/console.pid"
                s7_user_before="$(http_code "$USER_HEALTH_URL")"

                kill -- "-$S7_P2_PGID" 2>/dev/null || true
                sleep 1
                s7_p2_alive=0; kill -0 "$S7_P2_PID" 2>/dev/null && s7_p2_alive=1
                s7_p1_alive=0; kill -0 "$S7_P1_PID" 2>/dev/null && s7_p1_alive=1
                s7_p1_health="$(http_code "$S7_P1_HEALTH")"
                s7_user_after="$(http_code "$USER_HEALTH_URL")"

                s7_user_assert_skip=0
                if [ "$s7_user_before" = "000" ]; then
                    s7_user_assert_skip=1
                fi
                s7_group_ok=1
                [ "$s7_p2_alive" -eq 0 ] || s7_group_ok=0
                [ "$s7_p1_alive" -eq 1 ] || s7_group_ok=0
                [ "$s7_p1_health" = "200" ] || s7_group_ok=0
                [ -f "$s7_record" ] || s7_group_ok=0
                if [ "$s7_user_assert_skip" -eq 0 ]; then
                    [ "$s7_user_before" = "$s7_user_after" ] || s7_group_ok=0
                fi
                if [ "$s7_group_ok" -eq 1 ]; then
                    pass "S-7①②③: kill -- -$S7_P2_PGID 그룹 종료 → P2(그룹) 종료 + P1 생존/health200 + 레코드 잔존$([ "$s7_user_assert_skip" -eq 1 ] && echo ' (사용자7823 부재로 그 단언은 skip)' || echo ' + 사용자7823 생존 단언')"
                else
                    fail "S-7①②③" "p2_alive=$s7_p2_alive(expect0) p1_alive=$s7_p1_alive(expect1) p1_health=$s7_p1_health record_exists=$([ -f "$s7_record" ] && echo yes || echo no) user_before=$s7_user_before user_after=$s7_user_after"
                fi

                if console_stop_unsafe; then
                    skip "S-7④: 그룹 회수 후 console stop 성공 관측(stopped=true)" "console.sh에 전역 pkill 패턴 잔존 — 실호출은 C-2 위험. RED에서는 S-6의 (a)+(b)가 동일 경로의 사전 실패 증명을 이미 제공(F-2 근거)"
                else
                    s7_stop_output="$(OPAL_HOME="$S7_CONSOLE_HOME" bash "$RUN_SH" console stop 2>&1 || true)"
                    if echo "$s7_stop_output" | grep -q "stopped=true" && echo "$s7_stop_output" | grep -q "pid=$S7_P1_PID"; then
                        pass "S-7④: 그룹 회수가 레코드·identity를 훼손하지 않음 — stop 성공(stopped=true pid=<P1>)"
                    else
                        fail "S-7④" "output='$s7_stop_output'"
                    fi
                fi
                rm -f "$s7_record"
            fi
        fi
        kill -TERM "$S7_P1_PID" 2>/dev/null || true
        sleep 1
        kill -0 "$S7_P1_PID" 2>/dev/null && kill -KILL "$S7_P1_PID" 2>/dev/null || true
        kill -0 "$S7_P2_PID" 2>/dev/null && kill -- "-$S7_P2_PGID" 2>/dev/null || true
        sleep 1
        kill -0 "$S7_P2_PID" 2>/dev/null && kill -KILL "$S7_P2_PID" 2>/dev/null || true
    fi
fi

# =============================================================================
# 배치 B 신규 — task-127 배치 B (test-scenario.json S-13/S-14/S-16, AC-15/AC-16)
# 주의: 위 (가)(나)(다) 그룹의 S-13/S-14 라벨은 T02 구scenario 트랙(PLAN.md 개정판)
# 소속이며, 아래 섹션은 별도 SSOT(현재 태스크 test-scenario.json)의 동명 ID다.
# 혼동 방지를 위해 아래 TC 문자열에 "[B-신규]"와 AC 번호를 명시한다.
# =============================================================================
printf '\n== [B-신규] AC-15/AC-16 (test-scenario.json S-13, S-14, S-16) ==\n\n'

# --- [B-신규] S-13 (AC-15, C-2, H-1, 구현 전 RED) ---
# 격리 OPAL_HOME에 started_at을 과거(부팅 이전이 확실한 값)로 둔 identity-일치
# 생존 센티넬 레코드를 만들고 console stop을 호출한다. 기대(GREEN): 센티넬 생존,
# stopped=false pid=<pid> reason=stale_record. 현재(RED): console.sh stop 분기가
# started_at을 전혀 읽지 않으므로(console.sh:234-236) identity 일치+kill -0 생존
# 판정표 #5/#6으로 빠져 센티넬을 실제로 SIGTERM한다 — stopped=true가 나와야 정상
# RED로 관측된다.
TC="[B-신규] S-13(AC-15): 부팅-이전 started_at + 생존 센티넬 → console stop 실행 시 센티넬 생존 유지 + stopped=false pid=<pid> reason=stale_record 기대"
B13_USER_HEALTH_BEFORE="$(http_code "$USER_HEALTH_URL")"
B13_HOME="$SCRATCH/b13-home/.opal"
B13_APP_DIR="$B13_HOME/dashboard-server"
mkdir -p -m 700 "$B13_HOME/run" "$B13_APP_DIR"
bash -c 'while :; do sleep 1; done' &
B13_SENTINEL_PID=$!
SERVER_PIDS+=("$B13_SENTINEL_PID")
sleep 0.3
B13_RECORD="$B13_HOME/run/console.pid"
# started_at은 console.sh의 실제 기록 포맷(date +%Y-%m-%dT%H:%M:%S%z)을 그대로 따르되
# 값 자체는 시스템 부팅 시각보다 확실히 이른 과거로 둔다(부팅 시각 파싱 로직 부재
# 하에서도 레코드 자체는 identity 판정에 유효해야 하므로 pid/app_dir/host/port는
# 정상 값으로 채운다).
printf '{"pid": %s, "opal_home": "%s", "app_dir": "%s", "host": "127.0.0.1", "port": 9990, "started_at": "2000-01-01T00:00:00+0000"}' \
    "$B13_SENTINEL_PID" "$B13_HOME" "$B13_APP_DIR" > "$B13_RECORD"
chmod 600 "$B13_RECORD"
run_stop_stub "$B13_HOME"
b13_alive=0
kill -0 "$B13_SENTINEL_PID" 2>/dev/null && b13_alive=1
B13_USER_HEALTH_AFTER="$(http_code "$USER_HEALTH_URL")"
if [ "$b13_alive" -eq 1 ] \
    && echo "$STOP_STDOUT" | grep -q 'stopped=false' \
    && echo "$STOP_STDOUT" | grep -q "pid=$B13_SENTINEL_PID" \
    && echo "$STOP_STDOUT" | grep -q 'reason=stale_record' \
    && [ "$B13_USER_HEALTH_BEFORE" = "$B13_USER_HEALTH_AFTER" ]; then
    pass "$TC"
else
    fail "$TC" "sentinel_alive=$b13_alive stdout='$STOP_STDOUT' user_health_before=$B13_USER_HEALTH_BEFORE user_health_after=$B13_USER_HEALTH_AFTER (RED 정상: started_at 부팅비교 미구현 — 센티넬이 실제 종료됨)"
fi
kill -9 "$B13_SENTINEL_PID" 2>/dev/null || true

# --- [B-신규] S-14 (AC-15, H-1) — 구현 후 회귀 가드 ---
# RED 단계에서는 "started_at을 해석하는 공개 인터페이스 부재로 실패를 관측할 수
# 없다"는 사유로 BLOCKED 반환되었다. PM이 S-14를 RED 대상에서 제외하고 구현 후
# 회귀 가드로 재정의함에 따라, 부팅-이전 판정이 구현된 지금 아래 2케이스로
# 되살린다. 단언은 전적으로 `console stop`의 stdout key=value와 프로세스 생존
# 으로만 한다 — 비공개 헬퍼명(_console_boot_epoch 등)에 의존하지 않는다.

# (a) 왕복: console.sh 자신의 writer가 기록한 started_at(= 부팅 이후)은 stale로
#     오판정되지 않고 기존 판정 #5로 내려가 실제 종료에 도달해야 한다.
TC="[B-신규] S-14(a): writer가 기록한 부팅-이후 started_at 레코드 + 생존 센티넬 → stopped=true + 센티넬 종료 (기록 포맷 왕복, 부팅-이후 오판정 없음)"
B14A_HOME="$SCRATCH/b14a-home/.opal"
B14A_APP_DIR="$B14A_HOME/dashboard-server"
mkdir -p "$B14A_APP_DIR"
bash -c 'while :; do sleep 1; done' &
B14A_PID=$!
SERVER_PIDS+=("$B14A_PID")
sleep 0.3
write_record "$B14A_HOME" "$B14A_APP_DIR" 127.0.0.1 9989 "$B14A_PID" || true
B14A_RECORD="$B14A_HOME/run/console.pid"
if [ ! -f "$B14A_RECORD" ]; then
    fail "$TC" "픽스처 레코드 생성 실패: $B14A_RECORD"
else
    run_stop_stub "$B14A_HOME"
    sleep 1
    b14a_alive=0; kill -0 "$B14A_PID" 2>/dev/null && b14a_alive=1
    # 신규 reason 토큰 0건: stopped=true 경로는 reason= 를 출력하지 않으며,
    # console.sh 전체의 reason 토큰 집합도 기존 5종을 벗어나지 않아야 한다.
    b14a_reason_tokens="$(grep -o 'reason=[a-z_]*' "$CONSOLE_SH" | sort -u | tr '\n' ',' || true)"
    b14a_expected_tokens="reason=identity_mismatch,reason=no_record,reason=stale_record,reason=terminate_timeout,reason=unreadable_record,"
    if [ "$b14a_alive" -eq 0 ] \
        && echo "$STOP_STDOUT" | grep -q 'stopped=true' \
        && echo "$STOP_STDOUT" | grep -q "pid=$B14A_PID" \
        && ! echo "$STOP_STDOUT" | grep -q 'reason=' \
        && [ ! -f "$B14A_RECORD" ] \
        && [ "$b14a_reason_tokens" = "$b14a_expected_tokens" ]; then
        pass "$TC"
    else
        fail "$TC" "sentinel_alive=$b14a_alive(expect0) stdout='$STOP_STDOUT' record_exists=$([ -f "$B14A_RECORD" ] && echo yes || echo no) reason_tokens='$b14a_reason_tokens' (expected='$b14a_expected_tokens')"
    fi
fi
kill -9 "$B14A_PID" 2>/dev/null || true

# (b) fail-open: started_at이 손상되었거나 공백이면 부팅-이전 판정을 내리지 못하므로
#     stale로 오판정하지 않고 기존 판정 경로(#5)를 그대로 유지해야 한다(D-8).
TC="[B-신규] S-14(b): started_at 손상·공백 레코드 + 생존 센티넬 → 파싱 실패 fail-open으로 기존 판정 유지 → stopped=true (stale 오판정 없음)"
b14b_all_ok=1
b14b_detail=""
for b14b_case in corrupt blank; do
    b14b_home="$SCRATCH/b14b-$b14b_case-home/.opal"
    b14b_app_dir="$b14b_home/dashboard-server"
    mkdir -p -m 700 "$b14b_home/run" "$b14b_app_dir"
    bash -c 'while :; do sleep 1; done' &
    b14b_pid=$!
    SERVER_PIDS+=("$b14b_pid")
    sleep 0.3
    if [ "$b14b_case" = "corrupt" ]; then
        b14b_started="not-a-timestamp"
    else
        b14b_started="   "
    fi
    b14b_record="$b14b_home/run/console.pid"
    printf '{"pid": %s, "opal_home": "%s", "app_dir": "%s", "host": "127.0.0.1", "port": 9988, "started_at": "%s"}' \
        "$b14b_pid" "$b14b_home" "$b14b_app_dir" "$b14b_started" > "$b14b_record"
    chmod 600 "$b14b_record"
    run_stop_stub "$b14b_home"
    sleep 1
    b14b_alive=0; kill -0 "$b14b_pid" 2>/dev/null && b14b_alive=1
    if [ "$b14b_alive" -eq 0 ] \
        && echo "$STOP_STDOUT" | grep -q 'stopped=true' \
        && echo "$STOP_STDOUT" | grep -q "pid=$b14b_pid" \
        && ! echo "$STOP_STDOUT" | grep -q 'reason=stale_record'; then
        :
    else
        b14b_all_ok=0
        b14b_detail="$b14b_detail [$b14b_case] alive=$b14b_alive(expect0) stdout='$STOP_STDOUT';"
    fi
    kill -9 "$b14b_pid" 2>/dev/null || true
done
if [ "$b14b_all_ok" -eq 1 ]; then
    pass "$TC"
else
    fail "$TC" "$b14b_detail"
fi

# --- [B-신규] S-16 (AC-16, C-7 — 전제 불일치, RED 아님) ---
# 근거: 현재 .gitignore(REPO_ROOT/.gitignore)에 이미 `.oppl-run/` 항목이 존재한다
# (커밋 710800d "feat(126): OPAL WorkStudio 독립 앱 구축"에서 도입, 이 태스크
# 범위 밖). 디스패치 지시가 금지한 .gitignore 수정 없이 실측한 결과, 신규
# .oppl-run/ 산출물을 만들어도 git status --porcelain에 나타나지 않아 AC-16이
# 이미 충족된 상태다 — RED(실패)를 관측할 수 없다(전제 불일치). 아래는 그 실측
# 재현 절차이며 결과를 PASS로 기록하지 않고 시나리오 전제 불일치로 PM에 보고한다.
TC="[B-신규] S-16(AC-16, 전제불일치): .oppl-run/ 산출물이 git status --porcelain에 나타나지 않음 — 이미 충족, RED 관측 불가"
B16_TESTDIR="$REPO_ROOT/.oppl-run/batchB-probe-$$"
mkdir -p "$B16_TESTDIR"
echo probe > "$B16_TESTDIR/file.txt"
B16_STATUS_OUT="$(cd "$REPO_ROOT" && git status --porcelain | grep -c 'oppl-run' || true)"
rm -rf "$B16_TESTDIR"
echo "[BLOCKED-전제불일치] $TC — git status --porcelain 매치 수: $B16_STATUS_OUT (0이면 이미 충족)"

# ---------------- C-2 가드: 사용자 7823 health 스위트 종료 시점 기록 ----------------
USER_HEALTH_AFTER="$(http_code "$USER_HEALTH_URL")"
printf '\n사용자 127.0.0.1:7823 health (종료): %s (시작 대비 %s)\n' "$USER_HEALTH_AFTER" "$([ "$USER_HEALTH_BEFORE" = "$USER_HEALTH_AFTER" ] && echo 동일 || echo 상이)"
if [ "$USER_HEALTH_BEFORE" != "$USER_HEALTH_AFTER" ]; then
    fail "C-2 가드: 사용자 7823 health 코드가 스위트 전후 상이함" "before=$USER_HEALTH_BEFORE after=$USER_HEALTH_AFTER"
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
