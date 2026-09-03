#!/usr/bin/env bash
# =============================================================================
# test_agent_adapter_fields.sh — 플랫폼 어댑터 확장 필드 통로 회귀/기능 테스트
# 근거: tasks/105-260902-opds-어댑터-확장필드-통로/PLAN.md §3.5, §4.2 Step 1
#
# 배경:
#   scripts/install-mac.sh 의 emit_platform_agent_adapter()/install_codex_agents()
#   는 name/description/model 3필드를 하드코딩 재조립한다. 105 태스크는 이를
#   OPAL_ADAPTER_FIELD_SPEC(JSON) 순회 통로로 바꾸고 effort를 첫 확장 필드로
#   태운다. 본 테스트는 그 전환의 회귀(바이트 동일성) + 신규 동작(effort)을
#   모두 검증하는 유일한 자산이다(F-005).
#
# RED-first (opal/core/references/harness/red-first.md):
#   코드 변경(Step 3·4) 이전 상태에서 실행하면 TS-001·TS-002·TS-006·TS-010·TS-014는
#   PASS(기존 동작이 이미 만족)하고, TS-003~005·007·008·011·018~021은 FAIL로
#   리포트되어야 한다(RED 확인). Step 3~4·2 완료 후 재실행하면 전건 PASS(GREEN)해야 한다.
#
# 실행: bash scripts/tests/test_agent_adapter_fields.sh
# 종료 코드: 0 = FAIL 없음(SKIP 허용), 1 = FAIL 1건 이상
# bash 3.2 호환 — 연관배열·mapfile 미사용
# 네트워크 미사용 — git show(로컬 이력) + mktemp 스크래치만 사용
# 관용 근거: scripts/tests/test_archive_contents.sh (카운터·scratch·trap·bash 3.2 호환)
# =============================================================================

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MAC_SCRIPT="$REPO_ROOT/scripts/install-mac.sh"
WIN_SCRIPT="$REPO_ROOT/scripts/install/windows.ps1"

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf '[PASS] %s\n' "$1"; }
fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf '[FAIL] %s\n' "$1"
    [ -n "${2:-}" ] && printf '       detail: %s\n' "$2"
    return 0
}
skip() {
    SKIP_COUNT=$((SKIP_COUNT + 1))
    printf '[SKIP] %s\n' "$1"
    [ -n "${2:-}" ] && printf '       reason: %s\n' "$2"
}

SCRATCH_DIR="$(mktemp -d)"
trap 'rm -rf "$SCRATCH_DIR"' EXIT

cd "$REPO_ROOT"

# ─── 환경 의존 가드 ──────────────────────────────────────────────────────────
# codex CLI 부재 시 codex 런타임 검증(TS-009/TS-022, 본 스크립트 범위 밖 — Step
# 4/8에서 추가)은 SKIP 처리한다. 본 스크립트는 그 가드를 재사용 가능한 형태로
# 여기 둔다.
CODEX_BIN="$(command -v codex || true)"
codex_available() { [ -n "$CODEX_BIN" ]; }

PY_BIN="/usr/bin/python3"
if [ ! -x "$PY_BIN" ]; then
    PY_BIN="$(command -v python3)"
fi

# ─── seam: 함수 구간 추출 ────────────────────────────────────────────────────
# install-mac.sh:2098 이 가드 없는 `main "$@"` 이므로 source 불가 (§3.5.2).
# 단순 `/^fn() {/,/^}/` sed 범위 추출은 emit_platform_agent_adapter/install_codex_agents
# 내부 heredoc(Python)이 컬럼 0에 `mapping = {`...`}` 딕셔너리 리터럴을 갖고 있어
# 그 안의 "}"에서 조기 매치되어 함수 경계가 깨진다(실측 확인) — heredoc 구간은
# 통째로 opaque 텍스트로 건너뛰고, heredoc 밖에서만 중괄호 깊이를 세는 파서가 필요하다.
# bash 3.2 자체 문법으로 짜기보다 python3(이미 필수 의존성)로 정확히 구현한다.
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
        capturing = False
        break
sys.stdout.write(''.join(out))
PYEXTRACT
}

# 추출된 함수가 참조하는 로깅 헬퍼(warn/info/success) 스텁 — 원본은 색상 코드
# 변수(BLUE/YELLOW/GREEN/NC)와 OPAL_VERBOSE를 참조하므로 `set -u` 스크래치
# 실행 환경에서도 안전하도록 값을 채워 정의한다.
cat > "$SCRATCH_DIR/stubs.sh" <<'EOF'
OPAL_VERBOSE="${OPAL_VERBOSE:-0}"
BLUE=""; YELLOW=""; GREEN=""; NC=""
info()    { [ "$OPAL_VERBOSE" = "1" ] && echo "[INFO] $1" || true; }
success() { [ "$OPAL_VERBOSE" = "1" ] && echo "[OK] $1" || true; }
warn()    { echo "[WARN] $1" >&2; }
EOF

# ─── seam: 전역 상수 센티넬 블록 추출 (105 fix — readonly 충돌 회귀 방지) ───
# emit_platform_agent_adapter/install_codex_agents는 함수 스코프 안에서
# `OPAL_ADAPTER_FIELD_SPEC="$spec_json" "$py" ...` 커맨드 prefix-assignment를
# 수행한다. 과거 하네스는 함수 본문만 추출해 스크립트 전역
# `readonly OPAL_ADAPTER_FIELD_SPEC` 선언 없이 그 함수를 실행했기 때문에,
# 전역 상수와 이름이 충돌해도 통과했다(실제 install-mac.sh 실행 시에만
# "readonly variable" 로 즉시 실패 — 105 fix 블로커). 센티넬 마커 사이
# 텍스트(전역 readonly 선언)를 함수보다 먼저 source해 프로덕션과 동일한
# 초기화 순서를 재현한다. 마커가 없는 소스(예: 이 필드 도입 이전 HEAD)에서는
# 빈 출력 — 정상.
extract_sentinel() {
    local file="$1"
    "$PY_BIN" - "$file" <<'PYSENTINEL'
import re, sys
path = sys.argv[1]
with open(path, encoding='utf-8') as f:
    text = f.read()
m = re.search(
    r"# >>> OPAL_ADAPTER_FIELD_SPEC >>>\n(.*?)# <<< OPAL_ADAPTER_FIELD_SPEC <<<\n",
    text, re.DOTALL)
if m:
    sys.stdout.write(m.group(1))
PYSENTINEL
}

# old(HEAD)/new(워킹트리) 각각에서 어댑터 함수 3종을 추출해 소스 가능한 파일로 구성.
# 전역 센티넬 블록을 함수보다 먼저 넣어 프로덕션 초기화 순서를 재현한다(위 설명).
build_functions_file() {
    local src_mac="$1" out="$2"
    {
        cat "$SCRATCH_DIR/stubs.sh"
        echo
        extract_sentinel "$src_mac" || true
        echo
        extract_fn "$src_mac" "emit_platform_agent_adapter"
        echo
        extract_fn "$src_mac" "install_codex_agents"
        echo
        extract_fn "$src_mac" "install_codex_config"
    } > "$out"
}

OLD_MAC_SRC="$SCRATCH_DIR/old_install-mac.sh"
if ! git show HEAD:scripts/install-mac.sh > "$OLD_MAC_SRC" 2>"$SCRATCH_DIR/git.err"; then
    fail "seam: git show HEAD:scripts/install-mac.sh 실패" "$(cat "$SCRATCH_DIR/git.err")"
    OLD_MAC_SRC="$MAC_SCRIPT"  # 폴백 — 최소한 스위트 자체는 끝까지 실행
fi

# 워킹트리가 이미 dirty하면(R-7) baseline=HEAD 사실을 명시한다.
if ! git diff --quiet -- scripts/install-mac.sh 2>/dev/null; then
    printf '[NOTE] scripts/install-mac.sh 가 HEAD 대비 dirty — baseline=HEAD로 차등 골든을 계산한다 (R-7)\n'
fi

OLD_FUNCS="$SCRATCH_DIR/old_functions.sh"
NEW_FUNCS="$SCRATCH_DIR/new_functions.sh"
build_functions_file "$OLD_MAC_SRC" "$OLD_FUNCS"
build_functions_file "$MAC_SCRIPT" "$NEW_FUNCS"

# ─── TS-001 / TS-010: 차등 골든 (구판 vs 신판, 15 에이전트 × 4플랫폼) ─────────
run_emit_all() {
    # $1 = functions file, $2 = output root dir
    local funcs="$1" outroot="$2"
    local fake_home="$SCRATCH_DIR/home_$(basename "$outroot")"
    mkdir -p "$fake_home"  # venv 없음 → PY_BIN(시스템 python3) 폴백 결정론화

    for agent_dir in "$REPO_ROOT"/opal/agents/*/; do
        [ -d "$agent_dir" ] || continue
        local agent_name
        agent_name="$(basename "$agent_dir")"
        for platform in claude cursor gemini; do
            mkdir -p "$outroot/$platform"
            (
                # shellcheck disable=SC1090
                USER_HOME="$fake_home"
                source "$funcs"
                emit_platform_agent_adapter "$agent_dir" "$outroot/$platform/$agent_name.md" "$platform"
            ) 2>>"$outroot/stderr.log" || true
        done
    done

    # codex 경로: install_codex_agents는 자체 루프이므로 $USER_HOME/.opal/agents 를 구성
    local codex_home="$fake_home/codex_run"
    mkdir -p "$codex_home/.opal/agents"
    cp -R "$REPO_ROOT"/opal/agents/*/ "$codex_home/.opal/agents/" 2>/dev/null || true
    (
        USER_HOME="$codex_home"
        source "$funcs"
        install_codex_agents
    ) >>"$outroot/stdout.log" 2>>"$outroot/stderr.log" || true
    mkdir -p "$outroot/codex"
    if [ -d "$codex_home/.codex/agents" ]; then
        cp "$codex_home"/.codex/agents/*.toml "$outroot/codex/" 2>/dev/null || true
    fi
}

OLD_OUT="$SCRATCH_DIR/old_out"
NEW_OUT="$SCRATCH_DIR/new_out"
mkdir -p "$OLD_OUT" "$NEW_OUT"
run_emit_all "$OLD_FUNCS" "$OLD_OUT"
run_emit_all "$NEW_FUNCS" "$NEW_OUT"

DIFF_OUT="$SCRATCH_DIR/golden.diff"
if diff -r "$OLD_OUT/claude" "$NEW_OUT/claude" > "$DIFF_OUT" 2>&1 \
    && diff -r "$OLD_OUT/cursor" "$NEW_OUT/cursor" >> "$DIFF_OUT" 2>&1 \
    && diff -r "$OLD_OUT/gemini" "$NEW_OUT/gemini" >> "$DIFF_OUT" 2>&1 \
    && diff -r "$OLD_OUT/codex" "$NEW_OUT/codex" >> "$DIFF_OUT" 2>&1; then
    pass "TS-001/TS-010: 구판 vs 신판 emitter 산출물 diff 공집합 (15 에이전트 × 4플랫폼, body 포함)"
else
    fail "TS-001/TS-010: 구판 vs 신판 emitter 산출물 diff 비공집합" "$(head -c 2000 "$DIFF_OUT")"
fi

# ─── TS-002: 플랫폼명 조건 분기 신규 등장 스캔 ─────────────────────────────
# 스펙 조회(.get(platform), spec[...][platform])는 허용 — 플랫폼명 "리터럴 비교"만 금지.
scan_platform_literal_branch() {
    local funcs="$1"
    grep -nE "platform[[:space:]]*==[[:space:]]*['\"](claude|cursor|gemini|codex)['\"]|platform[[:space:]]+in[[:space:]]*\(" "$funcs" || true
}
HITS_OLD="$(scan_platform_literal_branch "$OLD_FUNCS")"
HITS_NEW="$(scan_platform_literal_branch "$NEW_FUNCS")"
if [ -z "$HITS_NEW" ]; then
    pass "TS-002: emit_platform_agent_adapter/install_codex_agents 본문에 플랫폼명 리터럴 비교 0건"
else
    fail "TS-002: 플랫폼명 리터럴 비교 발견" "$HITS_NEW"
fi

# ─── 배치 모드 4형태 + 값 도메인 (TS-003~008) 픽스처 ────────────────────────
# effort 필드를 선언한 에이전트 픽스처 — 실제 opal/agents/ 는 건드리지 않는다(금지사항 1).
make_probe_agent() {
    # $1 = dir, $2 = effort value(빈 문자열이면 미선언)
    local dir="$1" effort_val="$2"
    mkdir -p "$dir"
    {
        echo "---"
        echo "name: adapter-field-probe-105"
        echo "description: 어댑터 확장 필드 테스트용 임시 프로브"
        echo "model: standard"
        [ -n "$effort_val" ] && echo "effort: $effort_val"
        echo "---"
        echo ""
        echo "프로브 본문 (더미)."
    } > "$dir/AGENT.md"
}

emit_one() {
    # $1 = functions file, $2 = agent_dir, $3 = dst_file, $4 = platform, $5 = stderr capture file
    local funcs="$1" agent_dir="$2" dst="$3" platform="$4" errfile="$5"
    local fake_home="$SCRATCH_DIR/home_probe"
    mkdir -p "$fake_home"
    (
        USER_HOME="$fake_home"
        source "$funcs"
        emit_platform_agent_adapter "$agent_dir" "$dst" "$platform"
    ) 2>"$errfile" || true
}

emit_one_codex() {
    # $1 = functions file, $2 = agent_dir(단일 에이전트 폴더), $3 = dst toml 경로, $4 = stderr capture
    local funcs="$1" agent_dir="$2" dst="$3" errfile="$4"
    local fake_home
    fake_home="$(mktemp -d "$SCRATCH_DIR/codex_probe_XXXX")"
    local agent_name
    agent_name="$(basename "$agent_dir")"
    mkdir -p "$fake_home/.opal/agents/$agent_name"
    cp "$agent_dir/AGENT.md" "$fake_home/.opal/agents/$agent_name/AGENT.md"
    (
        USER_HOME="$fake_home"
        source "$funcs"
        install_codex_agents
    ) >/dev/null 2>"$errfile" || true
    if [ -f "$fake_home/.codex/agents/$agent_name.toml" ]; then
        cp "$fake_home/.codex/agents/$agent_name.toml" "$dst"
    fi
}

PROBE_HIGH="$SCRATCH_DIR/probe_high"
make_probe_agent "$PROBE_HIGH" "high"
PROBE_MAX="$SCRATCH_DIR/probe_max"
make_probe_agent "$PROBE_MAX" "max"
PROBE_TYPO="$SCRATCH_DIR/probe_typo"
make_probe_agent "$PROBE_TYPO" "hihg"
PROBE_NONE="$SCRATCH_DIR/probe_none"
make_probe_agent "$PROBE_NONE" ""

# TS-003 (① 독립 키, Claude) — effort: high 선언 → Claude md에 `effort: high` 존재
DST="$SCRATCH_DIR/ts003_claude.md"
emit_one "$NEW_FUNCS" "$PROBE_HIGH" "$DST" "claude" "$SCRATCH_DIR/ts003.err"
if [ -f "$DST" ] && grep -qE '^effort:[[:space:]]*high$' "$DST"; then
    pass "TS-003: Claude md frontmatter에 effort: high 존재 (①독립 키)"
else
    fail "TS-003: Claude md에 effort: high 미검출 (스펙 미도입 — RED 예상)" "$(cat "$DST" 2>/dev/null | head -10)"
fi

# TS-004 (② 이름 다른 독립 키, Codex) — 동일 입력 → model_reasoning_effort = "high"
DST="$SCRATCH_DIR/ts004_codex.toml"
emit_one_codex "$NEW_FUNCS" "$PROBE_HIGH" "$DST" "$SCRATCH_DIR/ts004.err"
if [ -f "$DST" ] && grep -qE '^model_reasoning_effort[[:space:]]*=[[:space:]]*"high"$' "$DST"; then
    pass "TS-004: Codex toml에 model_reasoning_effort = \"high\" 존재 (②이름 다른 독립 키)"
else
    fail "TS-004: Codex toml에 model_reasoning_effort 미검출 (스펙 미도입 — RED 예상)" "$(cat "$DST" 2>/dev/null | head -10)"
fi

# TS-005 (③ model 값 내 합성) — mode:"model_param" 활성 경로 실행 가능성 확인.
# 배경(PM 지시, TEST-SCENARIO.md §3 S-3): 스펙상 effort는 Claude/Codex=mode:"key",
# Cursor/Gemini=mode:"omit" 이므로, 정상 스펙으로 생성된 산출물에는 "[effort="가
# 원천적으로 나타날 수 없다 — 이전 구현(ts00*.* 산출물 스캔)은 TS-003/004/006이
# 정상 통과하는 한 항상 실패하는 죽은 경로였다. mode:"model_param" 경로는 현재
# 활성 플랫폼이 없으므로(Cursor는 예약) "임시 스펙 주입"으로 그 경로를 실제
# 실행시켜 검증한다(dead code 방지).
extract_spec_json() {
    # $1 = mac 스크립트 경로 -> stdout: OPAL_ADAPTER_FIELD_SPEC 리터럴의 JSON 원문
    "$PY_BIN" - "$1" <<'PYSPECEXTRACT'
import re, sys
path = sys.argv[1]
with open(path, encoding='utf-8') as f:
    text = f.read()
m = re.search(r"readonly OPAL_ADAPTER_FIELD_SPEC='(.*?)'\n", text)
if not m:
    sys.exit(1)
sys.stdout.write(m.group(1))
PYSPECEXTRACT
}

make_model_param_spec() {
    # $1 = 캐노니컬 스펙 JSON -> stdout: cursor.effort만 mode:"model_param"(to:"effort")로
    # 바꾼 변형 스펙 JSON. 그 외 필드/플랫폼은 원본과 동일 — 순수 임시 주입용.
    "$PY_BIN" - "$1" <<'PYMODPARAM'
import json, sys
spec = json.loads(sys.argv[1])
for field in spec['fields']:
    if field['opal'] == 'effort':
        field['platforms']['cursor'] = {"mode": "model_param", "to": "effort"}
sys.stdout.write(json.dumps(spec))
PYMODPARAM
}

emit_one_with_spec() {
    # $1 = 함수 소스 스크립트(mac 원본 경로), $2 = agent_dir, $3 = dst_file, $4 = platform,
    # $5 = 대체 스펙으로 주입할 JSON, $6 = stderr capture file
    #
    # 주의(105 fix 이후): funcs 파일에는 전역 센티넬 `readonly
    # OPAL_ADAPTER_FIELD_SPEC='...'` 이 이미 포함돼 있다(위 build_functions_file
    # seam). 이 함수를 source하기 *전에* OPAL_ADAPTER_FIELD_SPEC을 env로
    # 선주입해도, source 시점의 readonly 선언이 캐노니컬 값으로 되돌려버려
    # 대체 스펙이 무시된다. 그래서 대체 스펙 자체를 센티넬 자리에 심은
    # 전용 functions 파일을 새로 빌드해 source한다.
    local src_mac="$1" agent_dir="$2" dst="$3" platform="$4" spec_json="$5" errfile="$6"
    local fake_home="$SCRATCH_DIR/home_probe_spec"
    mkdir -p "$fake_home"
    local spec_funcs="$SCRATCH_DIR/spec_functions.sh"
    {
        cat "$SCRATCH_DIR/stubs.sh"
        echo
        printf "readonly OPAL_ADAPTER_FIELD_SPEC='%s'\n" "$spec_json"
        echo
        extract_fn "$src_mac" "emit_platform_agent_adapter"
    } > "$spec_funcs"
    (
        USER_HOME="$fake_home"
        source "$spec_funcs"
        emit_platform_agent_adapter "$agent_dir" "$dst" "$platform"
    ) 2>"$errfile" || true
}

BASE_SPEC_JSON="$(extract_spec_json "$MAC_SCRIPT" 2>/dev/null || true)"
MODEL_PARAM_SPEC=""
if [ -n "$BASE_SPEC_JSON" ]; then
    MODEL_PARAM_SPEC="$(make_model_param_spec "$BASE_SPEC_JSON" 2>/dev/null || true)"
fi

DST_MP="$SCRATCH_DIR/ts005_cursor_modelparam.md"
if [ -n "$MODEL_PARAM_SPEC" ]; then
    emit_one_with_spec "$MAC_SCRIPT" "$PROBE_HIGH" "$DST_MP" "cursor" "$MODEL_PARAM_SPEC" "$SCRATCH_DIR/ts005.err"
fi
if [ -f "$DST_MP" ] && grep -qE '^model:[[:space:]]*"?inherit\[effort=high\]"?[[:space:]]*$' "$DST_MP"; then
    pass "TS-005: model_param 합성(base[effort=...]) 경로 확인 — cursor.effort→model_param 임시 주입 시 model: \"inherit[effort=high]\" 합성"
else
    fail "TS-005: model_param 합성 경로 미검출 — cursor.effort→model_param 임시 스펙 주입 후에도 model 값에 [effort=high] 합성이 나타나지 않음 (build_pairs의 model_param 경로 결함 가능성)" "$(cat "$DST_MP" 2>/dev/null | head -10)$( [ -s "$SCRATCH_DIR/ts005.err" ] && printf '\nstderr: %s' "$(cat "$SCRATCH_DIR/ts005.err")")"
fi

# TS-006 (④ 미지원 생략) — Gemini/Cursor 산출물에 effort 문자열 0건
DST_G="$SCRATCH_DIR/ts006_gemini.md"
DST_C="$SCRATCH_DIR/ts006_cursor.md"
emit_one "$NEW_FUNCS" "$PROBE_HIGH" "$DST_G" "gemini" "$SCRATCH_DIR/ts006g.err"
emit_one "$NEW_FUNCS" "$PROBE_HIGH" "$DST_C" "cursor" "$SCRATCH_DIR/ts006c.err"
# 주의: 픽스처 에이전트명(adapter-field-probe-105)에는 'effort' 부분 문자열이
# 없으므로 단순 substring grep으로도 오탐(name/SSOT 경로 매치) 없이 안전하다.
# 그래도 의도를 명확히 하기 위해 frontmatter 키·model_param 합성 패턴에 한정한다.
if ! grep -qE '^effort:|effort_reasoning|model_reasoning_effort' "$DST_G" 2>/dev/null \
    && ! grep -qE '^effort:|effort_reasoning|model_reasoning_effort' "$DST_C" 2>/dev/null \
    && ! grep -q '\[effort=' "$DST_C" 2>/dev/null; then
    pass "TS-006: Gemini/Cursor 산출물에 effort 키/[effort= 0건 (④미지원 생략)"
else
    fail "TS-006: Gemini/Cursor 산출물에 effort 관련 문자열 검출"
fi

# TS-007 (값 축약) — effort: max → Claude는 max 그대로, Codex는 xhigh로 축약
DST_CL="$SCRATCH_DIR/ts007_claude.md"
DST_CX="$SCRATCH_DIR/ts007_codex.toml"
emit_one "$NEW_FUNCS" "$PROBE_MAX" "$DST_CL" "claude" "$SCRATCH_DIR/ts007cl.err"
emit_one_codex "$NEW_FUNCS" "$PROBE_MAX" "$DST_CX" "$SCRATCH_DIR/ts007cx.err"
if grep -qE '^effort:[[:space:]]*max$' "$DST_CL" 2>/dev/null \
    && grep -qE '^model_reasoning_effort[[:space:]]*=[[:space:]]*"xhigh"$' "$DST_CX" 2>/dev/null; then
    pass "TS-007: effort:max → Claude=max / Codex=xhigh 축약 확인"
else
    fail "TS-007: 값 축약(max→xhigh) 미검출 (스펙 미도입 — RED 예상)"
fi

# TS-008 (미정의 값 방어) — effort: hihg(오타) → stderr 경고 1행 + 산출물에 effort 키 부재
#                          + 종료코드 0(emit_one 내부에서 이미 || true로 흡수) + name/description/model 정상
DST_TYPO="$SCRATCH_DIR/ts008_claude.md"
emit_one "$NEW_FUNCS" "$PROBE_TYPO" "$DST_TYPO" "claude" "$SCRATCH_DIR/ts008.err"
WARN_HIT="$(grep -c 'unsupported effort' "$SCRATCH_DIR/ts008.err" 2>/dev/null || true)"
if [ -f "$DST_TYPO" ] && [ "${WARN_HIT:-0}" -ge 1 ] \
    && ! grep -q '^effort:' "$DST_TYPO" \
    && grep -q '^name:' "$DST_TYPO" && grep -q '^model:' "$DST_TYPO"; then
    pass "TS-008: 미정의 effort 값 → stderr 경고 + 필드 생략 + 나머지 필드 정상 + install 계속"
else
    fail "TS-008: 미정의 값 방어 로직 미검출 (스펙/resolve_value 미도입 — RED 예상)" "$(cat "$SCRATCH_DIR/ts008.err" 2>/dev/null)"
fi

# ─── TS-011: 스펙 미러 diff (4곳 전수 검증 — 센티넬 2 + 폴백 2) ──────────────
# 배경(PM 지시 보강): 센티넬 마커(mac #1·windows #4)만 비교하면
# emit_platform_agent_adapter()/install_codex_agents() 내부의 자기완결 폴백
# 리터럴(#2·#3, install-mac.sh 상단 주석 "폴백은 위 OPAL_ADAPTER_FIELD_SPEC
# 캐노니컬 값과 반드시 바이트 동일하게 유지한다" 규약으로만 보호됨)이 캐노니컬과
# 벌어져도 검출되지 않는다. 앵커는 행 번호가 아니라 "spec_json='...'" 단일행
# 대입 패턴(두 폴백 함수가 공유하는 선언 관용구)이다 — 파일이 바뀌어도 stale해지지
# 않는다. 4곳 중 하나라도 못 찾거나(예: 3곳만 추출) 바이트가 어긋나면 FAIL.
extract_all_spec_literals() {
    # $1 = mac 스크립트 경로, $2 = windows 스크립트 경로
    # stdout 1행 = PASS|FAIL, 2행 = 상세(검출 개수/라벨 또는 불일치 라벨)
    "$PY_BIN" - "$1" "$2" <<'PYALLSPEC'
import re, sys
mac_path, win_path = sys.argv[1], sys.argv[2]
with open(mac_path, encoding='utf-8') as f:
    mac_text = f.read()
with open(win_path, encoding='utf-8') as f:
    win_text = f.read()

literals = []
m = re.search(r"readonly OPAL_ADAPTER_FIELD_SPEC='(.*?)'\n", mac_text)
if m:
    literals.append(("mac_sentinel", m.group(1)))
for fm in re.finditer(r"^[ \t]*spec_json='(.*)'[ \t]*$", mac_text, re.MULTILINE):
    literals.append(("mac_fallback", fm.group(1)))
wm = re.search(r"readonly OPAL_ADAPTER_FIELD_SPEC='(.*?)'\n", win_text)
if wm:
    literals.append(("win_mirror", wm.group(1)))

count = len(literals)
if count != 4:
    print("FAIL")
    print("count=%d/4 labels=%s" % (count, ",".join(l for l, _ in literals)))
    sys.exit(0)

canon = literals[0][1]
mismatches = [label for label, j in literals if j != canon]
if mismatches:
    print("FAIL")
    print("count=4/4 mismatch=%s" % ",".join(mismatches))
else:
    print("PASS")
    print("count=4/4 all bytes identical (mac_sentinel, mac_fallback x2, win_mirror)")
PYALLSPEC
}

TS011_RESULT="$(extract_all_spec_literals "$MAC_SCRIPT" "$WIN_SCRIPT")"
TS011_STATUS="$(printf '%s\n' "$TS011_RESULT" | sed -n '1p')"
TS011_DETAIL="$(printf '%s\n' "$TS011_RESULT" | sed -n '2p')"
if [ "$TS011_STATUS" = "PASS" ]; then
    pass "TS-011: 스펙 JSON 리터럴 4곳(mac 센티넬·mac 폴백×2·windows 미러) 전수 바이트 동일 ($TS011_DETAIL)"
else
    fail "TS-011: 스펙 JSON 리터럴 4곳 전수 검증 실패 (Step 3·5 미완 또는 폴백 드리프트 — RED 예상)" "$TS011_DETAIL"
fi

# ─── TS-014: PowerShell 7 전용 구문 스캔 (PS 5.1 호환) ─────────────────────
PS7_HITS="$(grep -nE -- '-AsHashtable|\?\?|\?\.|\\u\{' "$WIN_SCRIPT" || true)"
if [ -z "$PS7_HITS" ]; then
    pass "TS-014: windows.ps1에 PS7 전용 구문(-AsHashtable/??/?./\\u{}) 0건"
else
    fail "TS-014: PS7 전용 구문 검출" "$PS7_HITS"
fi

# ─── TS-018~021: Codex max_threads legacy alias 교체 + 마이그레이션 ────────
# R-6 AC 재정의(캡틴 승인, TASK.md `[결정]` 참조): 판정 대상은 install이 기록한
# config.toml 결과 파일이다. scripts/ 소스 텍스트 스캔은 legacy 키 탐지·치환
# 로직 자체가 그 리터럴을 품어야 동작하는 구조적 필연이라 원리적으로 0건이
# 될 수 없으므로 폐기한다 — 탐지·치환 정규식/주석/변경이력/성공 메시지/본
# 테스트 픽스처의 max_threads 리터럴은 판정 대상에서 명시 제외한다.

run_install_codex_config() {
    # $1 = functions file, $2 = fake USER_HOME(이미 .codex/config.toml 세팅 완료 가정)
    local funcs="$1" home="$2"
    (
        USER_HOME="$home"
        source "$funcs"
        install_codex_config
    ) >/dev/null 2>"$SCRATCH_DIR/codex_config_run.err" || true
}

# TS-018: 기존 머신 케이스② — config.toml 존재하나 [agents] 없음(타 블록만 보유) → append, 타 블록 무손상
TS018_HOME="$SCRATCH_DIR/ts018_home"
mkdir -p "$TS018_HOME/.codex"
TS018_FILE="$TS018_HOME/.codex/config.toml"
cat > "$TS018_FILE" <<'EOF'
[mcp_servers.example]
command = "example-mcp"
args = ["--flag"]
EOF
run_install_codex_config "$NEW_FUNCS" "$TS018_HOME"
if [ -f "$TS018_FILE" ] \
    && ! grep -q 'max_threads' "$TS018_FILE" \
    && grep -qE '^\[agents\]$' "$TS018_FILE" \
    && grep -qE '^max_concurrent_threads_per_session[[:space:]]*=[[:space:]]*6$' "$TS018_FILE" \
    && grep -q '\[mcp_servers.example\]' "$TS018_FILE" \
    && grep -q 'command = "example-mcp"' "$TS018_FILE"; then
    pass "TS-018: 기존 머신([agents] 없음) — legacy 0건 + [agents] 신설(정식 키) + [mcp_servers] 무손상"
else
    fail "TS-018: [agents] 없는 기존 머신 append 미동작 (3분기 미구현 — RED 예상)" "$(cat "$TS018_FILE" 2>/dev/null)"
fi

# TS-019: 신규 머신(파일 부재) → 정식 키로 append
TS019_HOME="$SCRATCH_DIR/ts019_home"
mkdir -p "$TS019_HOME"
run_install_codex_config "$NEW_FUNCS" "$TS019_HOME"
TS019_FILE="$TS019_HOME/.codex/config.toml"
if [ -f "$TS019_FILE" ] && grep -qE '^\[agents\]$' "$TS019_FILE" \
    && grep -qE '^max_concurrent_threads_per_session[[:space:]]*=[[:space:]]*6$' "$TS019_FILE" \
    && grep -qE '^max_depth[[:space:]]*=[[:space:]]*1$' "$TS019_FILE" \
    && grep -qE '^job_max_runtime_seconds[[:space:]]*=[[:space:]]*1800$' "$TS019_FILE"; then
    pass "TS-019: 신규 머신 — [agents] + max_concurrent_threads_per_session=6 등 정식 키 3종 존재"
else
    fail "TS-019: 신규 머신 산출물에 정식 키 미검출 (Step 2 미완 — RED 예상)" "$(cat "$TS019_FILE" 2>/dev/null)"
fi

# TS-020: 기존 머신(legacy 키 + [mcp_servers] 등 타 블록 보유) → in-place 치환, 값 보존, 타 블록 무손상
TS020_HOME="$SCRATCH_DIR/ts020_home"
mkdir -p "$TS020_HOME/.codex"
TS020_FILE="$TS020_HOME/.codex/config.toml"
cat > "$TS020_FILE" <<'EOF'
[mcp_servers.example]
command = "example-mcp"
args = ["--flag"]

# AUTO-GENERATED by install-mac.sh — OPAL Codex 글로벌 에이전트 한계치
# 출처: https://developers.openai.com/codex/config-reference
[agents]
max_threads = 9
max_depth = 1
job_max_runtime_seconds = 1800
EOF
cp "$TS020_FILE" "$SCRATCH_DIR/ts020_before.toml"
run_install_codex_config "$NEW_FUNCS" "$TS020_HOME"
if [ -f "$TS020_FILE" ] \
    && ! grep -q 'max_threads' "$TS020_FILE" \
    && grep -qE '^max_concurrent_threads_per_session[[:space:]]*=[[:space:]]*9$' "$TS020_FILE" \
    && grep -q '\[mcp_servers.example\]' "$TS020_FILE" \
    && grep -q 'command = "example-mcp"' "$TS020_FILE"; then
    pass "TS-020: 기존 머신 legacy 키 in-place 치환 (값 9 보존) + [mcp_servers] 무손상"
else
    fail "TS-020: legacy 키 마이그레이션 미동작 (3분기 미구현 — RED 예상)" "$(cat "$TS020_FILE" 2>/dev/null)"
fi

# TS-021: 멱등 — TS-020 결과에 2회차 실행 시 바이트 무변화
if [ -f "$TS020_FILE" ]; then
    cp "$TS020_FILE" "$SCRATCH_DIR/ts021_after1.toml"
    run_install_codex_config "$NEW_FUNCS" "$TS020_HOME"
    if diff -q "$SCRATCH_DIR/ts021_after1.toml" "$TS020_FILE" >/dev/null 2>&1; then
        pass "TS-021: 2회차 실행 후 파일 바이트 무변화 (멱등)"
    else
        fail "TS-021: 2회차 실행 후 파일 변화 감지 (RED 예상 — TS-020 선행 실패 시 연쇄)"
    fi
else
    fail "TS-021: TS-020 산출물 부재로 검증 불가"
fi

# ─── TS-024: install-mac.sh 실제 기동 가능성 (readonly 충돌류 치명 오류 부재) ──
# 배경(105 fix 블로커): `./scripts/install-mac.sh` 실행이 line 498
# "OPAL_ADAPTER_FIELD_SPEC: readonly variable" 로 즉시 실패했다. 위 seam
# 개선(전역 센티넬 선행 source)만으로도 TS-001 등 기존 케이스가 간접적으로
# 이 결함을 잡지만, 여기서는 프로덕션과 동일하게 `set -euo pipefail` 하에서
# 함수를 1회 실행해 "치명 오류 없이 기동 가능"함을 직접 단정한다. 전체
# install은 돌리지 않고, USER_HOME/HOME을 스크래치로 격리해 실사용자 홈이나
# 배포 디렉토리에 쓰지 않는다.
# RED-first: (A) 적용 전 상태에서는 FAIL해야 한다.
build_strict_functions_file() {
    local src_mac="$1" out="$2"
    {
        cat "$SCRATCH_DIR/stubs.sh"
        echo 'set -euo pipefail'
        echo
        extract_sentinel "$src_mac" || true
        echo
        extract_fn "$src_mac" "emit_platform_agent_adapter"
    } > "$out"
}

STRICT_FUNCS="$SCRATCH_DIR/strict_functions.sh"
build_strict_functions_file "$MAC_SCRIPT" "$STRICT_FUNCS"

TS024_HOME="$SCRATCH_DIR/ts024_home"
mkdir -p "$TS024_HOME"
TS024_DST="$SCRATCH_DIR/ts024_out.md"
TS024_ERR="$SCRATCH_DIR/ts024.err"

set +e
(
    HOME="$TS024_HOME"
    USER_HOME="$TS024_HOME"
    source "$STRICT_FUNCS"
    emit_platform_agent_adapter "$REPO_ROOT/opal/agents/opal-task-agent" "$TS024_DST" "claude"
) 2>"$TS024_ERR"
TS024_EXIT=$?
set -e

if [ "$TS024_EXIT" -eq 0 ] && [ -f "$TS024_DST" ] && grep -q '^name:' "$TS024_DST" \
    && ! grep -q 'readonly variable' "$TS024_ERR"; then
    pass "TS-024: install-mac.sh strict(set -euo pipefail) 기동 — 전역 센티넬 로드 상태에서 emit_platform_agent_adapter 1회 실행, readonly 충돌류 치명 오류 없이 산출물 생성"
else
    fail "TS-024: install-mac.sh strict 기동 실패 (exit=$TS024_EXIT)" "$(cat "$TS024_ERR" 2>/dev/null)"
fi

# ─── 요약 ────────────────────────────────────────────────────────────────
echo ""
echo "=============================================="
printf 'PASS=%d FAIL=%d SKIP=%d\n' "$PASS_COUNT" "$FAIL_COUNT" "$SKIP_COUNT"
echo "=============================================="

if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
fi
exit 0
