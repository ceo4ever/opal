#!/usr/bin/env bash
# CONTRACT.md 기계검증절(MV-1/MV-2) + PLAN.md TS-3(경계) 실행 스크립트
# 재사용: RED 관찰(test-agent) 및 GREEN 검증(T4a) 양쪽에서 동일 스크립트 사용

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

pass_count=0
fail_count=0

echo "== verify.sh: T01-정상슬라이스 =="
echo "task_folder: $SCRIPT_DIR"
echo

# --- S-1 (MV-1): 파일 존재 ---
echo "[S-1/MV-1] test -f out/status.md"
if test -f out/status.md; then
  echo "  결과: PASS (exit 0)"
  pass_count=$((pass_count + 1))
else
  echo "  결과: FAIL (exit $? — out/status.md 부재)"
  fail_count=$((fail_count + 1))
fi
echo

# --- S-2 (MV-2): H1 존재 (>=1) ---
echo "[S-2/MV-2] grep -c '^# ' out/status.md (기대: >=1)"
if [ -f out/status.md ]; then
  h1_count=$(grep -c '^# ' out/status.md)
  if [ "$h1_count" -ge 1 ]; then
    echo "  결과: PASS (H1 개수=$h1_count)"
    pass_count=$((pass_count + 1))
  else
    echo "  결과: FAIL (H1 개수=$h1_count, 기대 >=1)"
    fail_count=$((fail_count + 1))
  fi
else
  echo "  결과: FAIL (out/status.md 부재로 grep 실행 불가)"
  fail_count=$((fail_count + 1))
fi
echo

# --- S-3 (경계): 생성 파일이 전부 samples/T01-정상슬라이스/ 하위인지 ---
echo "[S-3/경계] out/ 하위 생성 파일 경로가 task_scope(samples/T01-정상슬라이스/) 하위인지 확인"
violations=0
if [ -d out ]; then
  while IFS= read -r -d '' f; do
    real_f="$(cd "$(dirname "$f")" && pwd)/$(basename "$f")"
    case "$real_f" in
      "$SCRIPT_DIR"/*) ;;
      *)
        echo "  위반: $f -> $real_f (task_scope 밖)"
        violations=$((violations + 1))
        ;;
    esac
  done < <(find out -type f -print0)
else
  echo "  (out/ 디렉토리 부재 — 생성된 파일 없음)"
fi

if [ "$violations" -eq 0 ]; then
  echo "  결과: PASS (경계 위반 0건)"
  pass_count=$((pass_count + 1))
else
  echo "  결과: FAIL (경계 위반 ${violations}건)"
  fail_count=$((fail_count + 1))
fi
echo

echo "== 요약: pass=$pass_count fail=$fail_count =="

if [ "$fail_count" -gt 0 ]; then
  exit 1
fi
exit 0
