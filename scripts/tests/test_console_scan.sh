#!/usr/bin/env bash
# =============================================================================
# test_console_scan.sh — opal-cli `console scan` (console.config.json 자동 생성·머지) 테스트
# 태스크: 057 (opal-cli console scan — console.config.json 자동 생성·머지)
# 트랙: RED-first — 이 파일은 RED 단계(구현 전) 산출물.
#        (가) 기능 계약 TC-S1~S5,S7,S9,S10 (TS-001~TS-010 중 기능): RED 시점에 FAIL —
#             `console scan` action이 아직 console.sh case에 없어 실행 자체가 실패한다.
#        (나) 정적/구조 TC-S6,S8,S11,S12,S13 (TS-005,011~014): RED 시점에 FAIL —
#             대상 코드(scan 브랜치, install 연동, docstring, windows.ps1)가 아직 삽입되지 않음.
#        (다) 회귀 TC-S14: RED 시점에도 PASS — test_version_stamp.sh는 본 태스크와 무관.
#
# 실행: bash scripts/tests/test_console_scan.sh
# 종료 코드: 0 = 전체 통과, 1 = 실패 있음
# bash 3.2 호환 — 연관배열(declare -A)·mapfile 미사용. JSON 파싱/조회는 python3에 위임
#   (PLAN.md §2.2.2: python3은 OPAL 전 구간 필수 의존 — bash 자체 JSON 파서 미신뢰).
#
# 격리 [MUST]: 실 ~/.opal/console.config.json을 절대 읽거나 쓰지 않는다.
#   SCRATCH=$(mktemp -d) + OPAL_HOME=$SCRATCH/.../.opal 오버라이드로 매 케이스 독립 픽스처를 사용하고,
#   trap으로 스크립트 종료 시 SCRATCH 전체를 정리한다.
#
# 시나리오 SSOT: tasks/057-260710-opds-콘솔스캔-설정자동생성/TEST-SCENARIO.md (S-1~S-14, TS-001~TS-014)
# 설계 근거: tasks/057-260710-opds-콘솔스캔-설정자동생성/PLAN.md §3.1.2(출력 계약)·§3.2.2(머지 알고리즘)
#
# 변경이력:
#   v1.0 2026-07-10 신규 작성 — RED 단계 (opal-test-agent, mode: red) (057)
# =============================================================================

set -euo pipefail
# REPO_ROOT: 이 스크립트 위치에서 두 단계 위(= ai-framework 저장소 루트)
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RUN_SH="$REPO_ROOT/opal/tools/opal-cli/run.sh"
CONSOLE_SH="$REPO_ROOT/opal/tools/opal-cli/lib/console.sh"
INSTALL_MAC_SH="$REPO_ROOT/scripts/install-mac.sh"
WINDOWS_PS1="$REPO_ROOT/scripts/install/windows.ps1"
CONFIG_PY="$REPO_ROOT/dashboard/backend/config.py"
VERSION_STAMP_TEST="$REPO_ROOT/scripts/tests/test_version_stamp.sh"

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

# ---------------- scratch 준비 (§2 격리 규칙) ----------------
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT

# 픽스처 트리 생성 (TEST-SCENARIO §2 Scratch 픽스처)
#   $base/ws/proj-a/.opal/AGENT.md       — 유효 프로젝트
#   $base/ws/group/proj-b/.opal/AGENT.md — 중첩 유효 프로젝트
#   $base/ws/node_modules/x/.opal/AGENT.md — exclude 대상
#   $base/.opal/AGENT.md                 — OPAL 홈 마커 (OPAL_HOME=$base/.opal일 때 제외 대상, H-2)
build_fixture() {
    local base="$1"
    mkdir -p "$base/ws/proj-a/.opal"
    printf '# marker: proj-a\n' > "$base/ws/proj-a/.opal/AGENT.md"
    mkdir -p "$base/ws/group/proj-b/.opal"
    printf '# marker: proj-b\n' > "$base/ws/group/proj-b/.opal/AGENT.md"
    mkdir -p "$base/ws/node_modules/x/.opal"
    printf '# marker: node_modules/x (excluded)\n' > "$base/ws/node_modules/x/.opal/AGENT.md"
    mkdir -p "$base/.opal"
    printf '# opal home marker\n' > "$base/.opal/AGENT.md"
}

# ---------------- 유틸: console scan 실행 캡처 ----------------
# 사용법: run_scan_capture <OPAL_HOME 디렉토리> <scan 인자...>
# 결과는 전역 변수 SCAN_STDOUT / SCAN_EXIT 에 기록 (set -e 하에서 안전한 if 패턴)
SCAN_STDOUT=""
SCAN_EXIT=0
run_scan_capture() {
    local home_dir="$1"
    shift
    if SCAN_STDOUT="$(OPAL_HOME="$home_dir" bash "$RUN_SH" console scan "$@" 2>/dev/null)"; then
        SCAN_EXIT=0
    else
        SCAN_EXIT=$?
    fi
}

# ---------------- 유틸: JSON 필드 조회 (stdout 문자열 대상) ----------------
# json_field <json문자열> <필드명> — 존재하면 값 출력(list는 개행 join), 파싱 실패/부재 시 "__ERR__"
json_field() {
    local json_str="$1" field="$2"
    python3 -c '
import json, sys
try:
    d = json.loads(sys.argv[1])
    if sys.argv[2] not in d:
        print("__ERR__")
        sys.exit(0)
    v = d[sys.argv[2]]
except Exception:
    print("__ERR__")
    sys.exit(0)
if isinstance(v, list):
    print("\n".join(str(x) for x in v))
else:
    print(v)
' "$json_str" "$field" 2>/dev/null || echo "__ERR__"
}

# json_has_keys <json문자열> <키1> <키2> ... — 모든 키 존재 시 "OK", 아니면 "MISSING"
json_has_keys() {
    local json_str="$1"
    shift
    python3 -c '
import json, sys
try:
    d = json.loads(sys.argv[1])
except Exception:
    print("MISSING")
    sys.exit(0)
for k in sys.argv[2:]:
    if k not in d:
        print("MISSING")
        sys.exit(0)
print("OK")
' "$json_str" "$@" 2>/dev/null || echo "MISSING"
}

# json_list_has_dup <json문자열> <필드명> — 리스트에 중복 존재하면 "DUP", 아니면 "NODUP"(파싱 실패도 NODUP)
json_list_has_dup() {
    local json_str="$1" field="$2"
    python3 -c '
import json, sys
try:
    d = json.loads(sys.argv[1])
    v = d.get(sys.argv[2], [])
    if len(v) != len(set(v)):
        print("DUP")
    else:
        print("NODUP")
except Exception:
    print("NODUP")
' "$json_str" "$field" 2>/dev/null || echo "NODUP"
}

# ---------------- 유틸: config 파일 필드 조회 (파일 대상) ----------------
# read_config_list <경로> <필드명> — 리스트를 개행 join으로 출력, 실패 시 "__ERR__"
read_config_list() {
    local path="$1" field="$2"
    if [ ! -f "$path" ]; then
        echo "__ERR__"
        return 0
    fi
    python3 -c '
import json, sys
try:
    with open(sys.argv[1], encoding="utf-8") as f:
        d = json.load(f)
    v = d.get(sys.argv[2], [])
    print("\n".join(str(x) for x in v))
except Exception:
    print("__ERR__")
' "$path" "$field" 2>/dev/null || echo "__ERR__"
}

# read_config_field <경로> <필드명> — 스칼라 값 출력, 실패 시 "__ERR__"
read_config_field() {
    local path="$1" field="$2"
    if [ ! -f "$path" ]; then
        echo "__ERR__"
        return 0
    fi
    python3 -c '
import json, sys
try:
    with open(sys.argv[1], encoding="utf-8") as f:
        d = json.load(f)
    if sys.argv[2] not in d:
        print("__ERR__")
        sys.exit(0)
    print(d[sys.argv[2]])
except Exception:
    print("__ERR__")
' "$path" "$field" 2>/dev/null || echo "__ERR__"
}

# list_contains <개행구분목록> <값> — grep -qxF 래퍼 (bash 3.2 호환)
list_contains() {
    printf '%s\n' "$1" | grep -qxF "$2"
}

# ---------------- 유틸: bash case 브랜치 추출 (정적 TC용) ----------------
# extract_branch <파일> <라벨(괄호 앞)> — "라벨)"부터 그 뒤 첫 ";;" 단독 줄까지 출력
extract_branch() {
    local file="$1" label="$2"
    awk -v label="$label" '
        BEGIN { found = 0 }
        $0 ~ "^[ \t]*" label "\\)" { found = 1 }
        found { print }
        found && $0 ~ /^[ \t]*;;[ \t]*$/ { exit }
    ' "$file" 2>/dev/null
}

# extract_bash_function <파일> <함수명> — "함수명() {"부터 다음 최상위 함수정의 직전까지 출력
extract_bash_function() {
    local file="$1" fname="$2"
    awk -v fname="$fname" '
        BEGIN { found = 0 }
        $0 ~ "^" fname "\\(\\)[ \t]*\\{" { found = 1; print; next }
        found && /^[A-Za-z_][A-Za-z0-9_]*\(\)[ \t]*\{/ { exit }
        found { print }
    ' "$file" 2>/dev/null
}

# extract_ps_function <파일> <함수명> — "function 함수명"부터 다음 최상위 function 직전까지 출력
extract_ps_function() {
    local file="$1" fname="$2"
    awk -v fname="$fname" '
        BEGIN { found = 0 }
        $0 ~ "^function[ \t]+" fname { found = 1; print; next }
        found && /^function[ \t]+[A-Za-z]/ { exit }
        found { print }
    ' "$file" 2>/dev/null
}

# =============================================================================
# (가) 기능 계약 TC — RED 시점 FAIL 예상 (scan action 미구현)
# =============================================================================
printf '\n== (가) 기능 계약 (TC-S1~S5,S7,S9,S10) — RED 시점 FAIL 예상 ==\n\n'

# --- TC-S1 (S-1, TS-001/TS-004): config 부재 상태 scan → 생성 ---
T1="$SCRATCH/case1"
mkdir -p "$T1"
build_fixture "$T1"
HOME1="$T1/.opal"
CONFIG1="$HOME1/console.config.json"

TC="TC-S1 (S-1, TS-001/004): config 부재 상태 scan → 파일 생성 + created:true"
run_scan_capture "$HOME1" "$T1/ws"
if [ -f "$CONFIG1" ] \
    && [ "$(json_field "$SCAN_STDOUT" ok)" = "True" ] \
    && [ "$(json_field "$SCAN_STDOUT" created)" = "True" ]; then
    pass "$TC"
else
    fail "$TC" "exit=$SCAN_EXIT stdout='$SCAN_STDOUT' config_exists=$([ -f "$CONFIG1" ] && echo yes || echo no)"
fi

# --- TC-S2 (S-2, TS-002): 마커 프로젝트의 부모가 scan_roots에 포함 ---
TC="TC-S2 (S-2, TS-002): 마커 프로젝트 부모 디렉토리가 scan_roots(added_roots)에 포함"
added_roots="$(json_field "$SCAN_STDOUT" added_roots)"
if list_contains "$added_roots" "$T1/ws" && list_contains "$added_roots" "$T1/ws/group"; then
    pass "$TC"
else
    fail "$TC" "added_roots='$added_roots' (expected에 $T1/ws, $T1/ws/group 포함)"
fi

# --- TC-S3a/S3b (S-3, TS-006/TS-008): 수기 root 보존 + --prune 대조 ---
T3="$SCRATCH/case3"
mkdir -p "$T3"
build_fixture "$T3"
HOME3="$T3/.opal"
CONFIG3="$HOME3/console.config.json"
MANUAL_ROOT="/manual/keep/root-057"
mkdir -p "$HOME3"
python3 -c '
import json, sys
data = {"scan_roots": [sys.argv[2]], "scan_depth": 2, "exclude": ["node_modules", ".git", ".venv", "__pycache__", ".DS_Store"]}
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(data, f)
' "$CONFIG3" "$MANUAL_ROOT"

TC="TC-S3a (S-3, TS-006): --prune 미지정 시 수기 root 보존 + 신규 root 추가"
run_scan_capture "$HOME3" "$T3/ws"
post_roots_a="$(read_config_list "$CONFIG3" scan_roots)"
if list_contains "$post_roots_a" "$MANUAL_ROOT" \
    && list_contains "$post_roots_a" "$T3/ws" \
    && list_contains "$post_roots_a" "$T3/ws/group"; then
    pass "$TC"
else
    fail "$TC" "exit=$SCAN_EXIT scan_roots='$post_roots_a'"
fi

TC="TC-S3b (S-3, TS-008): --prune 지정 시 미발견 수기 root 제거"
run_scan_capture "$HOME3" --prune "$T3/ws"
post_roots_b="$(read_config_list "$CONFIG3" scan_roots)"
if ! list_contains "$post_roots_b" "$MANUAL_ROOT" \
    && list_contains "$post_roots_b" "$T3/ws" \
    && list_contains "$post_roots_b" "$T3/ws/group"; then
    pass "$TC"
else
    fail "$TC" "exit=$SCAN_EXIT scan_roots='$post_roots_b' (MANUAL_ROOT이 제거되어야 함)"
fi

# --- TC-S4 (S-4, TS-004/TS-007): JSON 출력 계약 스키마 준수 + added_roots dedup ---
T4="$SCRATCH/case4"
mkdir -p "$T4"
build_fixture "$T4"
HOME4="$T4/.opal"

TC="TC-S4 (S-4, TS-004/007): stdout JSON이 ok/created/added_roots/projects_found 4키 준수 + added_roots 중복 없음"
run_scan_capture "$HOME4" "$T4/ws"
keys_ok="$(json_has_keys "$SCAN_STDOUT" ok created added_roots projects_found)"
dup_check="$(json_list_has_dup "$SCAN_STDOUT" added_roots)"
if [ "$keys_ok" = "OK" ] && [ "$dup_check" = "NODUP" ]; then
    pass "$TC"
else
    fail "$TC" "exit=$SCAN_EXIT stdout='$SCAN_STDOUT' keys=$keys_ok dup=$dup_check"
fi

# --- TC-S5 (S-5, TS-003): OPAL 홈 마커 제외 (H-2) ---
T5="$SCRATCH/case5"
mkdir -p "$T5"
build_fixture "$T5"
HOME5="$T5/.opal"
CONFIG5="$HOME5/console.config.json"

TC="TC-S5 (S-5, TS-003): base=\$SCRATCH scan 시 OPAL 홈(\$OPAL_HOME) 마커가 scan_root로 추가되지 않음"
run_scan_capture "$HOME5" "$T5"
projects_found5="$(json_field "$SCAN_STDOUT" projects_found)"
post_roots5="$(read_config_list "$CONFIG5" scan_roots)"
parent_of_t5="$(dirname "$T5")"
if [ "$projects_found5" = "2" ] && ! list_contains "$post_roots5" "$parent_of_t5"; then
    pass "$TC"
else
    fail "$TC" "exit=$SCAN_EXIT projects_found=$projects_found5 (expected 2) scan_roots='$post_roots5' (parent_of_t5=$parent_of_t5 이 없어야 함)"
fi

# --- TC-S7 (S-7, TS-010): 손상 config 비파괴 ---
T7="$SCRATCH/case7"
mkdir -p "$T7"
build_fixture "$T7"
HOME7="$T7/.opal"
CONFIG7="$HOME7/console.config.json"
mkdir -p "$HOME7"
printf '{ this is not valid json ' > "$CONFIG7"
checksum_before="$(cksum "$CONFIG7")"

TC="TC-S7 (S-7, TS-010): 손상된 기존 config에 scan 시 ok:false + 원본 바이트 불변"
run_scan_capture "$HOME7" "$T7/ws"
checksum_after="$(cksum "$CONFIG7")"
if [ "$(json_field "$SCAN_STDOUT" ok)" = "False" ] \
    && [ -n "$(json_field "$SCAN_STDOUT" error)" ] \
    && [ "$(json_field "$SCAN_STDOUT" error)" != "__ERR__" ] \
    && [ "$checksum_before" = "$checksum_after" ]; then
    pass "$TC"
else
    fail "$TC" "exit=$SCAN_EXIT stdout='$SCAN_STDOUT' checksum_before='$checksum_before' checksum_after='$checksum_after'"
fi

# --- TC-S9 (S-9, TS-009): 미지정 키 보존 ---
T9="$SCRATCH/case9"
mkdir -p "$T9"
build_fixture "$T9"
HOME9="$T9/.opal"
CONFIG9="$HOME9/console.config.json"
mkdir -p "$HOME9"
python3 -c '
import json, sys
data = {
    "scan_roots": [],
    "scan_depth": 5,
    "exclude": ["custom_exclude_dir"],
    "my_custom_key": "custom_value_057",
}
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(data, f)
' "$CONFIG9"

TC="TC-S9 (S-9, TS-009): 사용자 추가 키·scan_depth·exclude가 실제 머지 실행 후에도 보존"
run_scan_capture "$HOME9" "$T9/ws"
custom_key_after="$(read_config_field "$CONFIG9" my_custom_key)"
scan_depth_after="$(read_config_field "$CONFIG9" scan_depth)"
exclude_after="$(read_config_list "$CONFIG9" exclude)"
post_roots9="$(read_config_list "$CONFIG9" scan_roots)"
# [MUST] self-confirming 방지: scan이 실제로 실행되어 scan_roots를 갱신했다는 증거(exit=0 +
# 신규 발견 root 추가)가 없으면, "보존"이 단지 scan 미실행(파일 무변경) 때문일 수 있으므로 FAIL 처리한다.
if [ "$SCAN_EXIT" -eq 0 ] \
    && list_contains "$post_roots9" "$T9/ws" \
    && list_contains "$post_roots9" "$T9/ws/group" \
    && [ "$custom_key_after" = "custom_value_057" ] \
    && [ "$scan_depth_after" = "5" ] \
    && list_contains "$exclude_after" "custom_exclude_dir"; then
    pass "$TC"
else
    fail "$TC" "exit=$SCAN_EXIT my_custom_key='$custom_key_after' scan_depth='$scan_depth_after' exclude='$exclude_after' post_roots='$post_roots9' (scan_roots 갱신 증거 없이 보존만으로는 PASS 불인정)"
fi

# --- TC-S10 (S-10, TS-007): 중복 root dedup ---
T10="$SCRATCH/case10"
mkdir -p "$T10"
build_fixture "$T10"
HOME10="$T10/.opal"
CONFIG10="$HOME10/console.config.json"
mkdir -p "$HOME10"
python3 -c '
import json, sys
data = {"scan_roots": [sys.argv[2]], "scan_depth": 2, "exclude": ["node_modules", ".git", ".venv", "__pycache__", ".DS_Store"]}
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(data, f)
' "$CONFIG10" "$T10/ws"

TC="TC-S10 (S-10, TS-007): 이미 존재하는 root 재발견 시 dedup — added_roots에 기존 root 미포함"
run_scan_capture "$HOME10" "$T10/ws"
added_roots10="$(json_field "$SCAN_STDOUT" added_roots)"
post_roots10="$(read_config_list "$CONFIG10" scan_roots)"
occurrences10="$(printf '%s\n' "$post_roots10" | grep -cxF "$T10/ws" || true)"
if ! list_contains "$added_roots10" "$T10/ws" \
    && list_contains "$added_roots10" "$T10/ws/group" \
    && [ "$occurrences10" = "1" ]; then
    pass "$TC"
else
    fail "$TC" "exit=$SCAN_EXIT added_roots='$added_roots10' post_roots='$post_roots10' occurrences=$occurrences10"
fi

# =============================================================================
# (나) 정적/구조 TC — RED 시점 FAIL 예상 (대상 코드 미삽입)
# =============================================================================
printf '\n== (나) 정적/구조 (TC-S6,S8,S11,S12,S13) — RED 시점 FAIL 예상 ==\n\n'

# --- TC-S6 (S-6, TS-005): 전체 디스크 스캔 금지 (scan 브랜치 -maxdepth·-prune 존재) ---
TC="TC-S6 (S-6, TS-005): console.sh scan 브랜치에 -maxdepth·exclude -prune 존재"
scan_branch="$(extract_branch "$CONSOLE_SH" scan)"
if [ -z "$scan_branch" ]; then
    fail "$TC" "console.sh에 'scan)' 브랜치가 없음 (GREEN 이전 정상)"
elif echo "$scan_branch" | grep -q -- '-maxdepth' && echo "$scan_branch" | grep -q -- '-prune'; then
    pass "$TC"
else
    fail "$TC" "'scan)' 브랜치는 있으나 -maxdepth/-prune 미발견"
fi

# --- TC-S8 (S-8, TS-011): install 연동 존재 + 실패 격리 (정적) ---
TC="TC-S8 (S-8, TS-011): install-mac.sh install_dashboard에 console scan 호출 + 실패 격리(||) 존재"
install_dashboard_body="$(extract_bash_function "$INSTALL_MAC_SH" install_dashboard)"
if [ -z "$install_dashboard_body" ]; then
    fail "$TC" "install-mac.sh에 install_dashboard 함수가 없음"
elif echo "$install_dashboard_body" | grep -q 'console scan' && echo "$install_dashboard_body" | grep -q '||'; then
    pass "$TC"
else
    fail "$TC" "install_dashboard 함수는 있으나 'console scan' 호출 또는 '||' 실패 격리 미발견 (GREEN 이전 정상)"
fi

# --- TC-S11 (S-11, TS-012): start 가드 안내 (정적) ---
TC="TC-S11 (S-11, TS-012): console.sh start 브랜치에 config 부재 안내 + scan 안내 문구 존재"
start_branch="$(extract_branch "$CONSOLE_SH" start)"
if [ -z "$start_branch" ]; then
    fail "$TC" "console.sh에 'start)' 브랜치가 없음"
elif echo "$start_branch" | grep -q 'console.config.json' && echo "$start_branch" | grep -q 'console scan'; then
    pass "$TC"
else
    fail "$TC" "'start)' 브랜치는 있으나 config 부재 안내(console.config.json) 또는 scan 안내(console scan) 문구 미발견 (GREEN 이전 정상)"
fi

# --- TC-S12 (S-12, TS-013): config.py 독스트링 정정 + load_config 로직 불변 (정적) ---
TC="TC-S12 (S-12, TS-013): config.py load_config 독스트링이 'console scan' 서술 + 'install 단계에서 수행' 문구 제거"
if [ ! -f "$CONFIG_PY" ]; then
    fail "$TC" "config.py 파일 없음: $CONFIG_PY"
else
    has_console_scan_mention=0
    has_stale_phrase=0
    if grep -q 'console scan' "$CONFIG_PY" 2>/dev/null; then
        has_console_scan_mention=1
    fi
    if grep -q '설정 파일 생성은 install 단계에서 수행\|install 단계에서 수행' "$CONFIG_PY" 2>/dev/null; then
        has_stale_phrase=1
    fi
    if [ "$has_console_scan_mention" -eq 1 ] && [ "$has_stale_phrase" -eq 0 ]; then
        pass "$TC"
    else
        fail "$TC" "console_scan_mention=$has_console_scan_mention stale_phrase_present=$has_stale_phrase (GREEN 이전 정상: stale_phrase_present=1)"
    fi
fi

TC="TC-S12b (S-12, TS-013): config.py load_config 로직(핵심 라인) 불변 확인"
if [ ! -f "$CONFIG_PY" ]; then
    fail "$TC" "config.py 파일 없음: $CONFIG_PY"
else
    logic_intact=1
    for needle in \
        'if not CONFIG_PATH.exists():' \
        'return ConsoleConfig()' \
        'except (json.JSONDecodeError, OSError):' \
        'scan_roots=data.get("scan_roots", DEFAULT_SCAN_ROOTS)' \
        'scan_depth=int(data.get("scan_depth", DEFAULT_SCAN_DEPTH))' \
        'exclude=data.get("exclude", DEFAULT_EXCLUDE)'; do
        if ! grep -qF "$needle" "$CONFIG_PY" 2>/dev/null; then
            logic_intact=0
        fi
    done
    if [ "$logic_intact" -eq 1 ]; then
        pass "$TC"
    else
        fail "$TC" "load_config 핵심 로직 라인 중 일부가 변경/누락됨 (021 C-2 읽기 전용 유지 위반 가능성)"
    fi
fi

# --- TC-S13 (S-13, TS-014): windows.ps1 등가 로직 (정적) ---
TC="TC-S13 (S-13, TS-014): windows.ps1 Install-Dashboard에 마커 탐색+config 머지+실패 격리 등가 로직 존재"
if [ ! -f "$WINDOWS_PS1" ]; then
    fail "$TC" "windows.ps1 파일 없음: $WINDOWS_PS1"
else
    ps_body="$(extract_ps_function "$WINDOWS_PS1" Install-Dashboard)"
    if [ -z "$ps_body" ]; then
        fail "$TC" "windows.ps1에 Install-Dashboard 함수가 없음"
    else
        has_marker=0
        has_merge=0
        has_isolation=0
        if echo "$ps_body" | grep -q 'AGENT.md'; then
            has_marker=1
        fi
        if echo "$ps_body" | grep -q 'ConvertFrom-Json' && echo "$ps_body" | grep -q 'ConvertTo-Json'; then
            has_merge=1
        fi
        if echo "$ps_body" | grep -q 'try' && echo "$ps_body" | grep -q 'catch'; then
            has_isolation=1
        fi
        if [ "$has_marker" -eq 1 ] && [ "$has_merge" -eq 1 ] && [ "$has_isolation" -eq 1 ]; then
            pass "$TC"
        else
            fail "$TC" "marker=$has_marker merge=$has_merge isolation=$has_isolation (GREEN 이전 정상: 전부 0 또는 일부 0)"
        fi
    fi
fi

# =============================================================================
# (다) 회귀 — RED 시점에도 PASS 예상 (본 태스크와 무관)
# =============================================================================
printf '\n== (다) 회귀 (TC-S14) — RED 시점에도 PASS 예상 ==\n\n'

TC="TC-S14 (S-14): 회귀 — test_version_stamp.sh PASS"
if [ ! -f "$VERSION_STAMP_TEST" ]; then
    skip "$TC (test_version_stamp.sh 미존재)"
else
    if bash "$VERSION_STAMP_TEST" >/tmp/console_scan_regression_057.log 2>&1; then
        pass "$TC"
    else
        fail "$TC" "test_version_stamp.sh 실패 — 로그: /tmp/console_scan_regression_057.log"
    fi
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
