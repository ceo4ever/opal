#!/usr/bin/env bash
# =============================================================================
# test_archive_contents.sh — 릴리스 아카이브 내용물 회귀 테스트
# 근거: .gitattributes export-ignore 앵커 결함 (2026-08-08 L2 수정)
#
# 배경:
#   gitattributes 패턴은 선행 슬래시가 없으면 **모든 depth의 동명 디렉토리**에 매칭된다.
#   `tasks/ export-ignore` 가 dashboard/frontend/src/pages/tasks/ 까지 지워
#   릴리스 tarball 설치 시 Console FE 빌드가 실패했다(2026-05-09 도입 이후 계속 발현).
#   이 테스트는 그 회귀를 다시 잡는다.
#
# 실행: bash scripts/tests/test_archive_contents.sh
# 종료 코드: 0 = 전체 통과, 1 = 실패 있음
# bash 3.2 호환 — 연관배열·mapfile 미사용
# 네트워크 미사용 — git archive 로 로컬 생성
# =============================================================================

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

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

cd "$REPO_ROOT"

# 워킹트리의 .gitattributes 를 적용해 아카이브를 만든다(--worktree-attributes).
# 커밋 전 수정도 검증 대상에 포함시키기 위함이다.
ARCHIVE="$SCRATCH_DIR/archive.tar.gz"
if ! git archive --format=tar.gz --worktree-attributes -o "$ARCHIVE" HEAD 2>"$SCRATCH_DIR/archive.err"; then
    printf '[FAIL] git archive 생성 실패\n       detail: %s\n' "$(head -1 "$SCRATCH_DIR/archive.err")"
    exit 1
fi

LIST="$SCRATCH_DIR/list.txt"
tar -tzf "$ARCHIVE" | sed 's|/$||' | sort > "$LIST"

in_archive() { grep -qx -- "$1" "$LIST"; }
count_prefix() { grep -c "^$1" "$LIST" || true; }

# ---------------- TC-A: 중첩된 동명 디렉토리는 포함되어야 한다 ----------------
# 앵커가 풀리면 이 3건이 가장 먼저 사라진다.

if in_archive "dashboard/frontend/src/pages/tasks/TasksPage.tsx"; then
    pass "TC-A1: dashboard/frontend/src/pages/tasks/ 포함 (Console FE 빌드 전제)"
else
    fail "TC-A1: dashboard/frontend/src/pages/tasks/TasksPage.tsx 누락" \
         ".gitattributes 의 tasks/ 패턴이 루트 고정(/tasks/)인지 확인"
fi

if in_archive "opal/tools/cmux-tool/docs/CMUX-REFERENCE.md"; then
    pass "TC-A2: opal/tools/cmux-tool/docs/ 포함"
else
    fail "TC-A2: opal/tools/cmux-tool/docs/CMUX-REFERENCE.md 누락" \
         ".gitattributes 의 docs/ 패턴이 루트 고정(/docs/)인지 확인"
fi

FIXTURE_OPAL="$(grep -c "tests/fixtures/.*\.opal/" "$LIST" || true)"
if [ "$FIXTURE_OPAL" -gt 0 ]; then
    pass "TC-A3: code-scan 테스트 픽스처의 중첩 .opal/ 포함 (${FIXTURE_OPAL}건)"
else
    fail "TC-A3: tests/fixtures/**/.opal/ 전량 누락" \
         ".gitattributes 의 .opal/ 패턴이 루트 고정(/.opal/)인지 확인"
fi

# ---------------- TC-B: 루트 제외는 유지되어야 한다 ----------------
# 앵커를 걸면서 제외 자체가 풀리면 배포 자산이 오염된다.

for d in "tasks/" "docs/" ".opal/" ".github/"; do
    c="$(count_prefix "$d")"
    if [ "$c" -eq 0 ]; then
        pass "TC-B: 루트 ${d} 제외 유지"
    else
        fail "TC-B: 루트 ${d} 가 아카이브에 포함됨 (${c}건)" "export-ignore 가 풀렸다"
    fi
done

for f in ".gitignore" ".gitattributes"; do
    if in_archive "$f"; then
        fail "TC-B: 루트 ${f} 가 아카이브에 포함됨" "export-ignore 가 풀렸다"
    else
        pass "TC-B: 루트 ${f} 제외 유지"
    fi
done

# ---------------- TC-C: 추적 파일 중 의도 밖 누락이 없어야 한다 ----------------
# 개별 파일을 열거하는 대신, git 추적 목록에서 "의도된 제외"를 뺀 나머지가
# 전부 아카이브에 있는지 본다 — 새로 추가되는 과잉 패턴도 여기서 잡힌다.

TRACKED="$SCRATCH_DIR/tracked.txt"
git ls-files | sort > "$TRACKED"

MISSING="$SCRATCH_DIR/missing.txt"
comm -23 "$TRACKED" "$LIST" \
    | grep -vE '^(tasks/|docs/|\.opal/|\.github/|\.gitignore$|\.gitattributes$)' \
    | grep -vE '(^|/)backup/' \
    > "$MISSING" || true

MISSING_COUNT="$(wc -l < "$MISSING" | tr -d ' ')"
if [ "$MISSING_COUNT" -eq 0 ]; then
    pass "TC-C: 의도된 제외 외 누락 0건 (추적 $(wc -l < "$TRACKED" | tr -d ' ')건 대조)"
else
    fail "TC-C: 의도 밖 누락 ${MISSING_COUNT}건" "$(head -5 "$MISSING" | tr '\n' ' ')"
fi

# ---------------- TC-D: VERSION export-subst 는 유지되어야 한다 ----------------
# 각인이 깨지면 opal-cli update 의 버전 비교 전제가 무너진다 (task 048).

if in_archive "VERSION"; then
    STAMP="$(tar -xzOf "$ARCHIVE" VERSION 2>/dev/null | tr -d '[:space:]')"
    case "$STAMP" in
        *'$Format:'*|"")
            fail "TC-D: VERSION 각인 미치환" "값: '${STAMP}'" ;;
        *)
            pass "TC-D: VERSION export-subst 치환 확인 (값: ${STAMP})" ;;
    esac
else
    fail "TC-D: VERSION 이 아카이브에 없음" "export-ignore 과잉 매칭 의심"
fi

# ---------------- 집계 ----------------
printf '\n========================================================\n'
printf 'PASS: %d | FAIL: %d\n' "$PASS_COUNT" "$FAIL_COUNT"
printf '========================================================\n'

if [ "$FAIL_COUNT" -gt 0 ]; then
    printf 'verdict: FAIL (%d failures)\n' "$FAIL_COUNT"
    exit 1
fi
printf 'verdict: ALL PASS\n'
exit 0
