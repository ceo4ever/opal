#!/usr/bin/env bash
# =============================================================================
# test-install-skill-cleanup.sh — 설치/업데이트 후 legacy skill 경로 정리 계약
# 태스크: 112, S-6 (RED-first)
#
# 실제 사용자 홈은 건드리지 않는다. install-mac.sh를 main 호출만 제거한 하네스로
# 로드하고, 스킬 배포를 담당하는 공개 install_opal 경로를 임시 HOME에서 실행한다.
# update.sh도 같은 installer를 호출하는 계약을 먼저 확인한다. venv/dashboard/플랫폼
# 어댑터처럼 스킬 트리와 무관한 부수효과만 격리하고 install_dir·strip 처리는 실제로
# 수행한다.
#
# 실행: bash scripts/tests/test-install-skill-cleanup.sh
# 종료 코드: 0 = 계약 충족, 1 = stale/missing skill 경로 존재
# =============================================================================

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
INSTALLER="$REPO_ROOT/scripts/install-mac.sh"
UPDATE_LIB="$REPO_ROOT/opal/tools/opal-cli/lib/update.sh"
SCRATCH_DIR="$(mktemp -d)"
trap 'rm -rf "$SCRATCH_DIR"' EXIT

PASS_COUNT=0
FAIL_COUNT=0

pass() {
    PASS_COUNT=$((PASS_COUNT + 1))
    printf '[PASS] %s\n' "$1"
}

fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf '[FAIL] %s\n' "$1"
    [ -n "${2:-}" ] && printf '       detail: %s\n' "$2"
}

# update 공개 경로가 install-mac.sh의 동일 배포 계약을 소비하는지 확인한다.
if grep -q 'OPAL_AUTO_INSTALL=1.*bash "$installer"' "$UPDATE_LIB"; then
    pass "update.sh는 install-mac.sh 공개 배포 경로를 호출"
else
    fail "update.sh installer 위임 계약 누락" "$UPDATE_LIB"
fi

TASK112_TEST_HOME="$SCRATCH_DIR/home"
TASK112_TEST_OPAL_HOME="$TASK112_TEST_HOME/.opal"
mkdir -p "$TASK112_TEST_OPAL_HOME/skills"

LEGACY_SKILLS="opal-pilot-dev-short op-sdd-spec op-sdd-plan op-sdd-action-plan op-sdd-verify"
for skill in $LEGACY_SKILLS; do
    mkdir -p "$TASK112_TEST_OPAL_HOME/skills/$skill"
    printf 'seeded legacy path\n' > "$TASK112_TEST_OPAL_HOME/skills/$skill/.legacy-seed"
done

# main "$@"만 제거하여 실제 함수 본문을 그대로 사용한다.
HARNESS="$SCRATCH_DIR/install-mac-functions.sh"
sed '/^main "$@"$/d' "$INSTALLER" > "$HARNESS"

USER_HOME="$TASK112_TEST_HOME"
export FRAMEWORK_ROOT="$REPO_ROOT"
export OPAL_HOME="$TASK112_TEST_OPAL_HOME"
export OPAL_HOME_OVERRIDE=1
export OPAL_VERBOSE=0

# shellcheck source=/dev/null
source "$HARNESS"

# S-6의 스킬 트리와 관계없는 설치 부수효과만 격리한다.
install_opal_venv() { :; }
merge_hooks_config() { :; }
install_claude_permissions() { :; }
install_claude_agents() { :; }
install_cursor_agents() { :; }
install_gemini_agents() { :; }
install_codex_agents() { :; }
install_codex_config() { :; }
install_gemini_config() { :; }
install_opal_bin() { :; }
install_dashboard() { :; }
console_autostart() { :; }
git() {
    if [ "${1:-}" = "config" ] && [ "${2:-}" = "--global" ]; then
        return 0
    fi
    command git "$@"
}

INSTALL_RC=0
install_opal > "$SCRATCH_DIR/install.out" 2>&1 || INSTALL_RC=$?
if [ "$INSTALL_RC" -eq 0 ]; then
    pass "격리 HOME에서 install_opal 실행 성공"
else
    fail "격리 HOME install_opal 실행 실패" "exit=$INSTALL_RC output=$(tail -5 "$SCRATCH_DIR/install.out" | tr '\n' ' ')"
fi

for skill in $LEGACY_SKILLS; do
    if [ -e "$TASK112_TEST_OPAL_HOME/skills/$skill" ]; then
        fail "legacy top-level skill 제거: $skill" "설치 후에도 $TASK112_TEST_OPAL_HOME/skills/$skill 존재"
    else
        pass "legacy top-level skill 제거: $skill"
    fi
done

REQUIRED_SKILLS="opal-pilot-dev opal-pilot-sdd/internal-skills/op-sdd-spec opal-pilot-sdd/internal-skills/op-sdd-plan opal-pilot-sdd/internal-skills/op-sdd-action-plan"
for skill in $REQUIRED_SKILLS; do
    if [ -d "$TASK112_TEST_OPAL_HOME/skills/$skill" ]; then
        pass "canonical/nested skill 배포: $skill"
    else
        fail "canonical/nested skill 배포: $skill" "설치 결과에 디렉토리 없음"
    fi
done

printf '\n========================================================\n'
printf 'PASS: %d | FAIL: %d\n' "$PASS_COUNT" "$FAIL_COUNT"
printf '========================================================\n'

if [ "$FAIL_COUNT" -gt 0 ]; then
    printf 'verdict: FAIL (%d failures)\n' "$FAIL_COUNT"
    exit 1
fi

printf 'verdict: ALL PASS\n'
exit 0
