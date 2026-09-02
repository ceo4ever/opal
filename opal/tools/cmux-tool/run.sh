#!/usr/bin/env bash
#
# cmux-tool/run.sh — cmux browser 자동화 래퍼 (디스패처)
#
# 역할: 서브명령 디스패처 진입점.
#       첫 인자가 URL이면 extract로 자동 라우팅 (레거시 호환 — TASK §R-2).
#       서브명령은 lib/dispatch.sh로 위임한다.
#
# 사용법:
#   run.sh <url> [--mode <full|clean|wireframe>] [--wait <ms>]
#   run.sh --surface <handle> [<url>] [--mode m] [--wait ms]
#   run.sh <subcommand> [args...]
#   run.sh --help | -h
#
# 서브명령 (12+1종):
#   필수 7종: extract  snapshot  eval  wait  navigate  click  fill
#   선택 5종: open  open-split  reload  press  get
#   레거시 1종: (URL 단독 → extract 자동 라우팅)
#
# 모드 (extract 전용):
#   A: URL만 지정 → 신규 surface 열기 → 추출 후 tab close
#   B: --surface <handle> 단독 → 현재 페이지 추출 (cleanup 절대 금지)
#   C: --surface <handle> <url> → surface 재사용 + navigate (cleanup 절대 금지)
#
# [MUST] B/C 모드에서 tab close 절대 금지 — dispatch.sh extract A) 케이스 내부에서만 호출.
#
# 단독 호출 경계 (PLAN §2.5):
#   PM/워커가 cmux-tool을 단독 호출 시 이 도구는 단일 책임(cmux browser 래퍼)만 수행한다.
#   cmux 미설치 시 에러 JSON 반환 ({"ok":false,"error":"cmux_not_installed"}).
#   fallback 로직은 도구 내부에 없다 — 호출자(wtm-agent 등)가 판단한다.
#
# 출처: PLAN §2.1 §2.2 §2.3 §2.5 / 흡수: 기존 run.sh 재설계 (007)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─── 알려진 서브명령 목록 ────────────────────────────────────────────────────
KNOWN_SUBCOMMANDS=(
  extract snapshot eval wait navigate click fill
  open open-split reload press get
)

_is_known_subcommand() {
  local cmd="$1"
  local sc
  for sc in "${KNOWN_SUBCOMMANDS[@]}"; do
    [[ "$sc" == "$cmd" ]] && return 0
  done
  return 1
}

# ─── --help / -h ─────────────────────────────────────────────────────────────
_show_help() {
  python3 - <<'PYEOF'
import json
result = {
  "ok": False,
  "error": "usage",
  "usage": "run.sh <url|subcommand> [args...]",
  "subcommands": {
    "extract":   "URL → HTML 추출 (모드 A/B/C). 레거시 호환: run.sh <url>",
    "snapshot":  "Accessibility tree 스냅샷 (--surface <h> [--compact] [--interactive])",
    "eval":      "JavaScript 실행 (--script '<js>' [--surface <h>])",
    "wait":      "요소/로드 대기 (--selector|--load-state|--text|--timeout-ms)",
    "navigate":  "URL 이동 (<url> [--surface <h>])",
    "click":     "요소 클릭 (<selector> [--surface <h>])",
    "fill":      "입력 채우기 (<selector> --text <value> [--surface <h>])",
    "open":      "브라우저 신규 오픈 (<url>)",
    "open-split":"브라우저 분할 오픈 (<url>)",
    "reload":    "새로고침 ([--surface <h>])",
    "press":     "키 누르기 (<key> [--surface <h>])",
    "get":       "요소 텍스트/속성 조회 (<selector> [--attr <name>] [--surface <h>])"
  },
  "common_output_fields": {
    "ok": "bool — 성공 여부",
    "command": "string — 실행된 서브명령",
    "surface": "string|null — 사용된 surface 핸들",
    "user_owned": "bool — B/C 모드 시 true",
    "error": "string|null — 실패 시 에러 코드"
  }
}
print(json.dumps(result, ensure_ascii=False, indent=2))
PYEOF
}

# ─── 메인 라우팅 ─────────────────────────────────────────────────────────────
if [[ $# -eq 0 ]]; then
  _show_help
  exit 1
fi

first="$1"

case "$first" in
  --help|-h)
    _show_help
    exit 0
    ;;
  http://*|https://*)
    # 레거시 호환: 첫 인자가 URL → extract 자동 라우팅 (TASK §R-2)
    exec "${SCRIPT_DIR}/lib/dispatch.sh" extract "$@"
    ;;
  --surface)
    # --surface 단독 시작 → extract B/C 모드 (레거시 호환)
    exec "${SCRIPT_DIR}/lib/dispatch.sh" extract "$@"
    ;;
  *)
    if _is_known_subcommand "$first"; then
      # 알려진 서브명령 → lib/dispatch.sh 위임
      shift
      exec "${SCRIPT_DIR}/lib/dispatch.sh" "$first" "$@"
    else
      # 알 수 없는 인자
      python3 - "$first" <<'PYEOF'
import json, sys
arg = sys.argv[1]
print(json.dumps({"ok":False,"error":"usage",
  "detail":f"알 수 없는 서브명령 또는 인자: {arg}. run.sh --help 로 목록 확인",
  "fallback":"phase2"}, ensure_ascii=False))
PYEOF
      exit 1
    fi
    ;;
esac
