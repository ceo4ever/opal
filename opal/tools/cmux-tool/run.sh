#!/usr/bin/env bash
#
# cmux-tool/run.sh — cmux browser 자동화 래퍼
#
# 역할: cmux browser 호출을 캡슐화한 bash 래퍼.
#       URL 모드(A) + 사용자 surface 모드(B/C) 통합, JSON 출력, B/C 모드 cleanup 가드.
#
# 사용법:
#   run.sh <url> [--mode <full|clean|wireframe>] [--wait <ms>]
#   run.sh --surface <handle> [<url>] [--mode <full|clean|wireframe>] [--wait <ms>]
#
# 모드:
#   A: URL만 지정 → 신규 surface 열기 → 추출 후 tab close
#   B: --surface <handle> 단독 → 현재 페이지 추출 (cleanup 절대 금지)
#   C: --surface <handle> <url> → surface 재사용 + navigate (cleanup 절대 금지)
#
# 출처: PLAN §2 N-1 + TASK §R-6 + cmux 공식 문서 https://cmux.com/ko/docs/browser-automation

set -uo pipefail

# ─── 기본값 ───────────────────────────────────────────────
URL=""
SURFACE_HANDLE=""
MODE="full"
WAIT_MS=2000
MODE_TYPE=""  # A, B, C

# ─── 인자 파싱 ────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --surface)
      SURFACE_HANDLE="${2:-}"
      if [[ -z "$SURFACE_HANDLE" ]]; then
        echo '{"ok":false,"error":"usage","detail":"--surface 다음에 핸들을 지정하세요 (예: surface:3)","fallback":"phase3"}' >&2
        exit 1
      fi
      shift 2
      ;;
    --mode)
      MODE="${2:-full}"
      shift 2
      ;;
    --wait)
      WAIT_MS="${2:-2000}"
      shift 2
      ;;
    --help|-h)
      echo '{"ok":false,"error":"usage","usage":"run.sh <url> [--mode <full|clean|wireframe>] [--wait <ms>] | run.sh --surface <handle> [<url>] [--mode m] [--wait ms]","modes":{"A":"URL만 지정 (신규 surface)","B":"--surface 단독 (현재 페이지)","C":"--surface + URL (navigate)"}}'
      exit 0
      ;;
    http://*|https://*)
      URL="$1"
      shift
      ;;
    *)
      printf '{"ok":false,"error":"usage","detail":"알 수 없는 인자: %s","fallback":"phase3"}\n' "$1" >&2
      exit 1
      ;;
  esac
done

# ─── 인자 없음 → 사용법 안내 ─────────────────────────────
if [[ -z "$URL" && -z "$SURFACE_HANDLE" ]]; then
  echo '{"ok":false,"error":"usage","usage":"run.sh <url> [--mode <full|clean|wireframe>] [--wait <ms>] | run.sh --surface <handle> [<url>] [--mode m] [--wait ms]","modes":{"A":"URL만 지정","B":"--surface 단독","C":"--surface + URL"}}'
  exit 1
fi

# ─── 모드 결정 ────────────────────────────────────────────
if [[ -n "$SURFACE_HANDLE" && -n "$URL" ]]; then
  MODE_TYPE="C"
elif [[ -n "$SURFACE_HANDLE" && -z "$URL" ]]; then
  MODE_TYPE="B"
else
  MODE_TYPE="A"
fi

# ─── 환경 감지: CMUX_SURFACE_ID 가드 ─────────────────────
if [[ -z "${CMUX_SURFACE_ID:-}" ]]; then
  echo '{"ok":false,"error":"not_in_cmux","detail":"CMUX_SURFACE_ID 환경 변수가 설정되지 않았습니다. cmux 터미널 내에서 실행하세요.","fallback":"phase3"}' >&2
  exit 2
fi

# ─── 환경 감지: cmux 설치 가드 ───────────────────────────
if ! command -v cmux >/dev/null 2>&1; then
  cat >&2 <<'EOF'
{"ok":false,"error":"cmux_not_installed","detail":"cmux 명령을 찾을 수 없습니다. cmux 0.64.3 이상을 설치하세요.","install_url":"https://cmux.com/","github":"https://github.com/manaflow-ai/cmux","fallback":"phase3"}
EOF
  exit 3
fi

# ─── surface 핸들 유효성 검증 (B/C 모드) ─────────────────
if [[ "$MODE_TYPE" == "B" || "$MODE_TYPE" == "C" ]]; then
  if [[ ! "$SURFACE_HANDLE" =~ ^surface:[0-9]+$ ]] && \
     [[ ! "$SURFACE_HANDLE" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
    printf '{"ok":false,"error":"invalid_surface","detail":"핸들 형식이 잘못되었습니다: %s (허용: surface:N 또는 UUID)","fallback":"phase3"}\n' \
      "$SURFACE_HANDLE" >&2
    exit 4
  fi
fi

# ─── SURFACE 변수 설정 ────────────────────────────────────
SURFACE=""

# ─── 모드 A: 신규 surface 열기 ───────────────────────────
if [[ "$MODE_TYPE" == "A" ]]; then
  OPEN_OUT=$(cmux browser open "$URL" --workspace "${CMUX_WORKSPACE_ID:-}" --focus false 2>&1) || {
    printf '{"ok":false,"error":"open_failed","detail":"cmux browser open 실패","fallback":"phase3"}\n' >&2
    exit 5
  }
  SURFACE=$(printf '%s\n' "$OPEN_OUT" | grep -oE 'surface:[0-9]+' | head -1)
  if [[ -z "$SURFACE" ]]; then
    printf '{"ok":false,"error":"surface_parse_failed","detail":"cmux browser open 출력에서 surface 핸들을 파싱할 수 없습니다","fallback":"phase3"}\n' >&2
    exit 5
  fi
fi

# ─── 모드 B: 사용자 surface 그대로 사용 ──────────────────
if [[ "$MODE_TYPE" == "B" ]]; then
  SURFACE="$SURFACE_HANDLE"
fi

# ─── 모드 C: 사용자 surface + navigate ───────────────────
if [[ "$MODE_TYPE" == "C" ]]; then
  SURFACE="$SURFACE_HANDLE"
  cmux browser "$SURFACE" goto "$URL" 2>/dev/null || {
    printf '{"ok":false,"error":"goto_failed","detail":"cmux browser goto 실패","fallback":"phase3"}\n' >&2
    exit 6
  }
fi

# ─── 로드 완료 대기 ───────────────────────────────────────
cmux browser "$SURFACE" wait --load-state complete --timeout-ms 15000 2>/dev/null || {
  printf '{"ok":false,"error":"wait_failed","detail":"페이지 로드 대기 타임아웃","fallback":"phase3"}\n' >&2
  # A 모드에서만 cleanup
  case "$MODE_TYPE" in
    A) cmux browser "$SURFACE" tab close 2>/dev/null || true ;;
    B|C) ;;  # cleanup 금지 — 사용자 소유 surface
  esac
  exit 7
}

# ─── 추가 대기 (--wait 옵션) ─────────────────────────────
if [[ "$WAIT_MS" -gt 0 ]]; then
  WAIT_S=$(awk "BEGIN {printf \"%.3f\", $WAIT_MS/1000}")
  sleep "$WAIT_S"
fi

# ─── 페이지 정보 추출 ─────────────────────────────────────
TITLE=$(cmux browser "$SURFACE" get title 2>/dev/null) || TITLE=""
FINAL_URL=$(cmux browser "$SURFACE" get url 2>/dev/null) || FINAL_URL="${URL:-}"
HTML_FILE=$(mktemp /tmp/cmux-tool-html.XXXXXX)
cmux browser "$SURFACE" eval --script "document.documentElement.outerHTML" > "$HTML_FILE" 2>/dev/null || {
  printf '{"ok":false,"error":"eval_failed","detail":"HTML 추출 실패","fallback":"phase3"}\n' >&2
  rm -f "$HTML_FILE"
  # A 모드에서만 cleanup
  case "$MODE_TYPE" in
    A) cmux browser "$SURFACE" tab close 2>/dev/null || true ;;
    B|C) ;;  # cleanup 금지 — 사용자 소유 surface
  esac
  exit 8
}

# ─── A 모드에서만 tab close (B/C는 절대 금지) ────────────
case "$MODE_TYPE" in
  A) cmux browser "$SURFACE" tab close 2>/dev/null || true ;;
  B|C) ;;  # cleanup 금지 — 사용자 소유 surface
esac

# ─── user_owned 결정 (안전 가드 1차 시그널) ──────────────
# B/C 모드: user_owned=true → opal-wtm-agent가 민감 정보 경고 부착 (2차)
# A 모드:   user_owned=false
case "$MODE_TYPE" in
  A)   USER_OWNED="false" ;;
  B|C) USER_OWNED="true"  ;;
esac

# ─── JSON 출력 (stdout) — python3으로 안전 직렬화 ─────────
python3 - "$SURFACE" "$USER_OWNED" "$MODE_TYPE" "$TITLE" "$FINAL_URL" \
  "$WAIT_MS" "$HTML_FILE" <<'PYEOF'
import json, sys, os

surface    = sys.argv[1]
user_owned = sys.argv[2] == "true"
mode       = sys.argv[3]
title      = sys.argv[4]
final_url  = sys.argv[5]
wait_ms    = int(sys.argv[6])
html_file  = sys.argv[7]

with open(html_file, "r", encoding="utf-8", errors="replace") as f:
    content = f.read()
os.unlink(html_file)

result = {
    "ok": True,
    "method": "cmux",
    "mode": mode,
    "surface": surface,
    "user_owned": user_owned,
    "title": title,
    "final_url": final_url,
    "content": content,
    "bytes": len(content.encode("utf-8")),
    "wait_ms": wait_ms
}
print(json.dumps(result, ensure_ascii=False))
PYEOF

rm -f "$HTML_FILE" 2>/dev/null || true
