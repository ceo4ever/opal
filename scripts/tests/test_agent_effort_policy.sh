#!/usr/bin/env bash
# =============================================================================
# test_agent_effort_policy.sh — 에이전트 effort 선언 정책 회귀 시험
# 정책: opal/core/references/agents.md 의 "effort 선언 정책"
#   (a) opal/agents/*/AGENT.md 의 effort 선언값은 허용 집합
#       low·medium·high·xhigh·max·minimal 에 속해야 한다 (default 등 불가).
#   (b) 선언된 에이전트의 Claude 어댑터 출력(effort:)과 Codex 어댑터 출력
#       (model_reasoning_effort)에 해당 키가 실제로 나타나야 한다.
#   선언 에이전트가 없어도 통과한다.
# 방식: test_agent_adapter_fields.sh 와 같이 install-mac.sh 의 어댑터 함수를
#       추출해 임시 디렉토리에서 실행한다. 실제 opal/agents/ 는 수정하지 않는다.
# 실행: bash scripts/tests/test_agent_effort_policy.sh  (0=PASS, 1=FAIL)
# bash 3.2 호환, 네트워크 미사용
# =============================================================================
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MAC_SCRIPT="$REPO_ROOT/scripts/install-mac.sh"

PASS_COUNT=0
FAIL_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf '[PASS] %s\n' "$1"; }
fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf '[FAIL] %s\n' "$1"
    [ -n "${2:-}" ] && printf '       detail: %s\n' "$2"
    return 0
}

SCRATCH_DIR="$(mktemp -d)"
trap 'rm -rf "$SCRATCH_DIR"' EXIT

PY_BIN="/usr/bin/python3"
[ -x "$PY_BIN" ] || PY_BIN="$(command -v python3)"

# 함수·센티넬 추출 (test_agent_adapter_fields.sh 와 동일 방식)
extract_fn() {
    local file="$1" fn="$2"
    "$PY_BIN" - "$file" "$fn" <<'PYEXTRACT'
import sys, re
path, fn = sys.argv[1], sys.argv[2]
with open(path, encoding='utf-8') as f:
    lines = f.readlines()
out = []
capturing = False
depth = 0
heredoc = False
marker = None
start_re = re.compile(r'^' + re.escape(fn) + r'\(\)\s*\{')
heredoc_re = re.compile(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?")
for line in lines:
    if not capturing:
        if start_re.match(line):
            capturing = True
            depth = 1
            out.append(line)
        continue
    if heredoc:
        out.append(line)
        if line.rstrip('\n') == marker:
            heredoc = False
        continue
    m = heredoc_re.search(line)
    if m:
        marker = m.group(1)
        heredoc = True
        out.append(line)
        continue
    depth += line.count('{') - line.count('}')
    out.append(line)
    if depth <= 0:
        break
sys.stdout.write(''.join(out))
PYEXTRACT
}

extract_sentinel() {
    "$PY_BIN" - "$1" <<'PYSENTINEL'
import re, sys
text = open(sys.argv[1], encoding='utf-8').read()
m = re.search(r"# >>> OPAL_ADAPTER_FIELD_SPEC >>>\n(.*?)# <<< OPAL_ADAPTER_FIELD_SPEC <<<\n", text, re.DOTALL)
if m:
    sys.stdout.write(m.group(1))
PYSENTINEL
}

FUNCS="$SCRATCH_DIR/functions.sh"
{
    cat <<'STUBS'
OPAL_VERBOSE="${OPAL_VERBOSE:-0}"
BLUE=""; YELLOW=""; GREEN=""; NC=""
info()    { :; }
success() { :; }
warn()    { echo "[WARN] $1" >&2; }
STUBS
    extract_sentinel "$MAC_SCRIPT"
    extract_fn "$MAC_SCRIPT" "emit_platform_agent_adapter"
    extract_fn "$MAC_SCRIPT" "install_codex_agents"
} > "$FUNCS"

ALLOWED=" low medium high xhigh max minimal "

# frontmatter 의 effort 값을 출력 (미선언이면 빈 문자열)
read_effort() {
    awk 'NR==1 && $0!="---"{exit} NR>1 && $0=="---"{exit} /^effort:/{sub(/^effort:[ \t]*/,""); gsub(/["\047 \t\r]+$/,""); gsub(/^["\047]/,""); print; exit}' "$1"
}

# check_agents_dir <agents_dir> <label>
# 정책 위반이 있으면 사유를 stdout 에 출력하고 1 을 반환한다.
check_agents_dir() {
    local dir="$1" violations=0 agent_dir name eff work out
    work="$(mktemp -d "$SCRATCH_DIR/check.XXXXXX")"
    mkdir -p "$work/home/.opal/agents"
    for agent_dir in "$dir"/*/; do
        [ -f "$agent_dir/AGENT.md" ] || continue
        name="$(basename "$agent_dir")"
        eff="$(read_effort "$agent_dir/AGENT.md")"
        [ -n "$eff" ] || continue
        case "$ALLOWED" in
            *" $eff "*) ;;
            *) echo "$name: effort '$eff' 는 허용 집합 밖"; violations=$((violations + 1)); continue ;;
        esac
        cp -R "$agent_dir" "$work/home/.opal/agents/$name"
        out="$work/$name.claude.md"
        ( USER_HOME="$work/home"; source "$FUNCS"
          emit_platform_agent_adapter "$agent_dir" "$out" claude ) 2>/dev/null || true
        if ! grep -q "^effort: $eff\$" "$out" 2>/dev/null; then
            echo "$name: Claude 출력에 'effort: $eff' 없음"; violations=$((violations + 1))
        fi
    done
    if ls "$work/home/.opal/agents" 2>/dev/null | grep -q .; then
        ( USER_HOME="$work/home"; source "$FUNCS"; install_codex_agents ) >/dev/null 2>&1 || true
        for agent_dir in "$work/home/.opal/agents"/*/; do
            name="$(basename "$agent_dir")"
            eff="$(read_effort "$agent_dir/AGENT.md")"
            [ "$eff" = "minimal" ] && eff="none"
            if ! grep -q "^model_reasoning_effort = \"$eff\"" "$work/home/.codex/agents/$name.toml" 2>/dev/null; then
                echo "$name: Codex 출력에 model_reasoning_effort '$eff' 없음"; violations=$((violations + 1))
            fi
        done
    fi
    [ "$violations" -eq 0 ]
}

make_fixture() { # <root> <name> <effort-line or empty>
    mkdir -p "$1/$2"
    {
        echo "---"
        echo "name: $2"
        echo "description: effort 정책 시험용 임시 에이전트"
        echo "model: standard"
        [ -n "$3" ] && echo "$3"
        echo "---"
        echo "본문"
    } > "$1/$2/AGENT.md"
}

# TS-1: 실제 소스 검사
if msg="$(check_agents_dir "$REPO_ROOT/opal/agents")"; then
    pass "opal/agents 의 effort 선언이 정책(허용 집합·어댑터 출력)을 만족"
else
    fail "opal/agents 의 effort 선언이 정책 위반" "$msg"
fi

# TS-2: 양성 — 유효 선언은 통과하고 Claude·Codex 출력에 나타난다
POS="$SCRATCH_DIR/pos"; make_fixture "$POS" fx-valid "effort: high"; make_fixture "$POS" fx-none ""
if msg="$(check_agents_dir "$POS")"; then
    pass "양성: effort: high 임시 에이전트가 정책을 통과 (미선언 에이전트 포함)"
else
    fail "양성: 유효 선언이 위반으로 판정됨" "$msg"
fi

# TS-3: 음성 — effort: default 는 실패로 판정되어야 한다
NEG="$SCRATCH_DIR/neg"; make_fixture "$NEG" fx-default "effort: default"
if check_agents_dir "$NEG" >/dev/null; then
    fail "음성: effort: default 임시 에이전트를 시험이 통과시킴"
else
    pass "음성: effort: default 임시 에이전트를 시험이 실패로 판정"
fi

# TS-4: 음성 — 허용 집합 밖 임의 값
NEG2="$SCRATCH_DIR/neg2"; make_fixture "$NEG2" fx-bogus "effort: turbo"
if check_agents_dir "$NEG2" >/dev/null; then
    fail "음성: effort: turbo 임시 에이전트를 시험이 통과시킴"
else
    pass "음성: 허용 집합 밖 값(turbo)을 시험이 실패로 판정"
fi

printf '\nPASS=%d FAIL=%d\n' "$PASS_COUNT" "$FAIL_COUNT"
[ "$FAIL_COUNT" -eq 0 ]
