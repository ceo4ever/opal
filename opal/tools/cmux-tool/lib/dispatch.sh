#!/usr/bin/env bash
#
# cmux-tool/lib/dispatch.sh — 서브명령 라우터 + cmux browser 명령 실행
#
# 역할: run.sh로부터 서브명령을 받아 해당 cmux browser 명령을 실행하고
#       공통 5필드 + 명령별 특화 필드를 JSON으로 stdout 출력한다.
#
# 공개 인터페이스:
#   dispatch <subcommand> [args...]
#
# 지원 서브명령 (12+1종):
#   필수 7종 (자동화 핵심): extract snapshot eval wait navigate click fill
#   선택 5종 (E2E 보조):   open open-split reload press get
#   레거시 1종 (호환):     extract (URL 단독 → 기존 흐름)
#
# [MUST] B/C 모드(사용자 surface 재사용)에서는 tab close 절대 금지.
#        tab close는 extract의 A) 케이스 내부에서만 호출된다.
#
# 흡수 출처: opal/tools/cmux-tool/run.sh (extract 흐름 이전)
#            PLAN §2.1 §2.2 §2.3 디스패처 설계
#            외부 SSOT: https://cmux.com/ko/docs/browser-automation (R-T1 검증 2026-05-22)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=json.sh
source "${SCRIPT_DIR}/json.sh"

# ─── 공통: surface 핸들 검증 ─────────────────────────────────────────────────
_validate_surface_handle() {
  local handle="$1"
  local cmd="$2"
  if [[ ! "$handle" =~ ^surface:[0-9]+$ ]] && \
     [[ ! "$handle" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
    json_err "$cmd" "invalid_surface" \
      "핸들 형식이 잘못되었습니다: ${handle} (허용: surface:N 또는 UUID)" \
      "phase2" >&2
    return 4
  fi
}

# ─── 공통: cmux 설치·환경 가드 ──────────────────────────────────────────────
_guard_cmux_env() {
  local cmd="$1"
  if [[ -z "${CMUX_SURFACE_ID:-}" ]]; then
    json_err "$cmd" "not_in_cmux" \
      "CMUX_SURFACE_ID 환경 변수가 설정되지 않았습니다. cmux 터미널 내에서 실행하세요." \
      "phase2" >&2
    return 2
  fi
  if ! command -v cmux >/dev/null 2>&1; then
    python3 - "$cmd" >&2 <<'PYEOF'
import json, sys
print(json.dumps({"ok":False,"command":sys.argv[1],"error":"cmux_not_installed",
  "detail":"cmux 명령을 찾을 수 없습니다. cmux 0.64.3 이상을 설치하세요.",
  "install_url":"https://cmux.com/","github":"https://github.com/manaflow-ai/cmux",
  "fallback":"phase2"}, ensure_ascii=False))
PYEOF
    return 3
  fi
}

# ─── dispatch 메인 ───────────────────────────────────────────────────────────
dispatch() {
  local subcommand="${1:-}"
  shift || true

  case "$subcommand" in

    # ── extract: 기존 run.sh 전체 흐름 (A/B/C 모드) ──────────────────────────
    extract)
      _dispatch_extract "$@"
      ;;

    # ── snapshot ──────────────────────────────────────────────────────────────
    snapshot)
      local surface="" compact="" interactive=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --surface) surface="${2:-}"; shift 2 ;;
          --compact) compact="--compact"; shift ;;
          --interactive) interactive="--interactive"; shift ;;
          *) shift ;;
        esac
      done
      _guard_cmux_env "snapshot" || exit $?
      [[ -n "$surface" ]] && _validate_surface_handle "$surface" "snapshot" || true
      local surface_arg=""
      [[ -n "$surface" ]] && surface_arg="--surface ${surface}"
      local result user_owned="false"
      [[ -n "$surface" ]] && user_owned="true"
      # shellcheck disable=SC2086
      result=$(cmux browser ${surface_arg} snapshot ${compact} ${interactive} 2>/dev/null) || {
        json_err "snapshot" "eval_failed" "cmux browser snapshot 실패" >&2
        exit 8
      }
      local length=${#result}
      python3 - "snapshot" "${surface:-null}" "$user_owned" "$result" "$length" <<'PYEOF'
import json, sys
cmd, surface, user_owned, snap_text, length = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
print(json.dumps({"ok":True,"command":cmd,"surface":None if surface=="null" else surface,
  "user_owned":user_owned=="true","snapshot_text":snap_text,"length":length}, ensure_ascii=False))
PYEOF
      ;;

    # ── eval ──────────────────────────────────────────────────────────────────
    eval)
      local surface="" script=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --surface) surface="${2:-}"; shift 2 ;;
          --script)  script="${2:-}"; shift 2 ;;
          *)         [[ -z "$script" ]] && script="$1"; shift ;;
        esac
      done
      _guard_cmux_env "eval" || exit $?
      if [[ -z "$script" ]]; then
        json_err "eval" "usage" "--script <js> 또는 위치 인수로 JS를 지정하세요" >&2; exit 1
      fi
      local surface_arg=""
      [[ -n "$surface" ]] && surface_arg="--surface ${surface}"
      local user_owned="false"
      [[ -n "$surface" ]] && user_owned="true"
      local result
      # shellcheck disable=SC2086
      result=$(cmux browser ${surface_arg} eval --script "${script}" 2>/dev/null) || {
        json_err "eval" "eval_failed" "cmux browser eval 실패" >&2; exit 8
      }
      local script_len=${#script}
      python3 - "$surface" "$user_owned" "$result" "$script_len" <<'PYEOF'
import json, sys
surface, user_owned, result, script_len = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
print(json.dumps({"ok":True,"command":"eval","surface":None if surface=="" else surface,
  "user_owned":user_owned=="true","result":result,"script_len":script_len}, ensure_ascii=False))
PYEOF
      ;;

    # ── wait ──────────────────────────────────────────────────────────────────
    wait)
      local surface="" selector="" load_state="" timeout_ms="" text="" url_frag="" func=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --surface)      surface="${2:-}"; shift 2 ;;
          --selector)     selector="${2:-}"; shift 2 ;;
          --load-state)   load_state="${2:-}"; shift 2 ;;
          --timeout-ms)   timeout_ms="${2:-}"; shift 2 ;;
          --text)         text="${2:-}"; shift 2 ;;
          --url-contains) url_frag="${2:-}"; shift 2 ;;
          --function)     func="${2:-}"; shift 2 ;;
          *)              [[ -z "$selector" ]] && selector="$1"; shift ;;
        esac
      done
      _guard_cmux_env "wait" || exit $?
      local surface_arg="" timeout_arg=""
      [[ -n "$surface" ]]     && surface_arg="--surface ${surface}"
      [[ -n "$timeout_ms" ]]  && timeout_arg="--timeout-ms ${timeout_ms}"
      local wait_args=""
      if [[ -n "$load_state" ]]; then
        wait_args="--load-state ${load_state}"
      elif [[ -n "$selector" ]]; then
        wait_args="--selector ${selector}"
      elif [[ -n "$text" ]]; then
        wait_args="--text ${text}"
      elif [[ -n "$url_frag" ]]; then
        wait_args="--url-contains ${url_frag}"
      elif [[ -n "$func" ]]; then
        wait_args="--function ${func}"
      fi
      local start_ms end_ms elapsed_ms matched=false
      start_ms=$(python3 -c "import time; print(int(time.time()*1000))")
      # shellcheck disable=SC2086
      cmux browser ${surface_arg} wait ${wait_args} ${timeout_arg} 2>/dev/null && matched=true || true
      end_ms=$(python3 -c "import time; print(int(time.time()*1000))")
      elapsed_ms=$((end_ms - start_ms))
      local user_owned="false"
      [[ -n "$surface" ]] && user_owned="true"
      python3 - "${surface:-}" "$user_owned" "${selector:-${load_state:-}}" "$elapsed_ms" "$matched" <<'PYEOF'
import json, sys
surface, user_owned, sel, elapsed, matched = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
print(json.dumps({"ok":True,"command":"wait","surface":None if surface=="" else surface,
  "user_owned":user_owned=="true","selector":sel,"elapsed_ms":elapsed,
  "matched":matched=="true"}, ensure_ascii=False))
PYEOF
      ;;

    # ── navigate ──────────────────────────────────────────────────────────────
    navigate)
      local url="" surface=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --surface) surface="${2:-}"; shift 2 ;;
          http://*|https://*) url="$1"; shift ;;
          *) url="$1"; shift ;;
        esac
      done
      _guard_cmux_env "navigate" || exit $?
      if [[ -z "$url" ]]; then
        json_err "navigate" "usage" "URL을 지정하세요" >&2; exit 1
      fi
      local surface_arg=""
      [[ -n "$surface" ]] && surface_arg="--surface ${surface}"
      local from_url=""
      # shellcheck disable=SC2086
      from_url=$(cmux browser ${surface_arg} url 2>/dev/null || echo "")
      # shellcheck disable=SC2086
      cmux browser ${surface_arg} navigate "${url}" 2>/dev/null || {
        json_err "navigate" "goto_failed" "cmux browser navigate 실패" >&2; exit 6
      }
      local user_owned="false"
      [[ -n "$surface" ]] && user_owned="true"
      python3 - "${surface:-}" "$user_owned" "$from_url" "$url" <<'PYEOF'
import json, sys
surface, user_owned, from_url, to_url = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
print(json.dumps({"ok":True,"command":"navigate","surface":None if surface=="" else surface,
  "user_owned":user_owned=="true","from_url":from_url,"to_url":to_url}, ensure_ascii=False))
PYEOF
      ;;

    # ── click ─────────────────────────────────────────────────────────────────
    click)
      local selector="" surface=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --surface) surface="${2:-}"; shift 2 ;;
          *)         [[ -z "$selector" ]] && selector="$1"; shift ;;
        esac
      done
      _guard_cmux_env "click" || exit $?
      if [[ -z "$selector" ]]; then
        json_err "click" "usage" "CSS selector를 지정하세요" >&2; exit 1
      fi
      local surface_arg=""
      [[ -n "$surface" ]] && surface_arg="--surface ${surface}"
      local user_owned="false"
      [[ -n "$surface" ]] && user_owned="true"
      # shellcheck disable=SC2086
      cmux browser ${surface_arg} click "${selector}" 2>/dev/null || {
        json_err "click" "eval_failed" "cmux browser click 실패: ${selector}" >&2; exit 8
      }
      python3 - "${surface:-}" "$user_owned" "$selector" <<'PYEOF'
import json, sys
surface, user_owned, selector = sys.argv[1], sys.argv[2], sys.argv[3]
print(json.dumps({"ok":True,"command":"click","surface":None if surface=="" else surface,
  "user_owned":user_owned=="true","selector":selector}, ensure_ascii=False))
PYEOF
      ;;

    # ── fill ──────────────────────────────────────────────────────────────────
    # 외부 SSOT R-T1 검증: fill <selector> --text <value> (--text 플래그 사용)
    fill)
      local selector="" value="" surface=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --surface) surface="${2:-}"; shift 2 ;;
          --text)    value="${2:-}"; shift 2 ;;
          *)         [[ -z "$selector" ]] && selector="$1" || value="$1"; shift ;;
        esac
      done
      _guard_cmux_env "fill" || exit $?
      if [[ -z "$selector" ]]; then
        json_err "fill" "usage" "CSS selector를 지정하세요" >&2; exit 1
      fi
      local surface_arg=""
      [[ -n "$surface" ]] && surface_arg="--surface ${surface}"
      local user_owned="false"
      [[ -n "$surface" ]] && user_owned="true"
      # shellcheck disable=SC2086
      cmux browser ${surface_arg} fill "${selector}" --text "${value}" 2>/dev/null || {
        json_err "fill" "eval_failed" "cmux browser fill 실패: ${selector}" >&2; exit 8
      }
      python3 - "${surface:-}" "$user_owned" "$selector" "$value" <<'PYEOF'
import json, sys
surface, user_owned, selector, value = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
print(json.dumps({"ok":True,"command":"fill","surface":None if surface=="" else surface,
  "user_owned":user_owned=="true","selector":selector,"value":value}, ensure_ascii=False))
PYEOF
      ;;

    # ── open ──────────────────────────────────────────────────────────────────
    open)
      local url=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          http://*|https://*) url="$1"; shift ;;
          *)                  url="$1"; shift ;;
        esac
      done
      _guard_cmux_env "open" || exit $?
      if [[ -z "$url" ]]; then
        json_err "open" "usage" "URL을 지정하세요" >&2; exit 1
      fi
      local open_out
      open_out=$(cmux browser open "${url}" --workspace "${CMUX_WORKSPACE_ID:-}" --focus false 2>&1) || {
        json_err "open" "open_failed" "cmux browser open 실패" "phase2" >&2; exit 5
      }
      local new_surface
      new_surface=$(printf '%s\n' "$open_out" | grep -oE 'surface:[0-9]+' | head -1)
      if [[ -z "$new_surface" ]]; then
        json_err "open" "surface_parse_failed" "cmux browser open 출력에서 surface 파싱 실패" "phase2" >&2; exit 5
      fi
      python3 - "$new_surface" "$url" <<'PYEOF'
import json, sys
new_surface, url = sys.argv[1], sys.argv[2]
print(json.dumps({"ok":True,"command":"open","surface":new_surface,"user_owned":False,
  "new_surface":new_surface,"to_url":url}, ensure_ascii=False))
PYEOF
      ;;

    # ── open-split ────────────────────────────────────────────────────────────
    open-split)
      local url=""
      while [[ $# -gt 0 ]]; do
        url="$1"; shift
      done
      _guard_cmux_env "open-split" || exit $?
      if [[ -z "$url" ]]; then
        json_err "open-split" "usage" "URL을 지정하세요" >&2; exit 1
      fi
      cmux browser open-split "${url}" 2>/dev/null || {
        json_err "open-split" "open_failed" "cmux browser open-split 실패" "phase2" >&2; exit 5
      }
      python3 - "$url" <<'PYEOF'
import json, sys
url = sys.argv[1]
print(json.dumps({"ok":True,"command":"open-split","surface":None,"user_owned":False,
  "new_surface":None,"to_url":url}, ensure_ascii=False))
PYEOF
      ;;

    # ── reload ────────────────────────────────────────────────────────────────
    reload)
      local surface=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --surface) surface="${2:-}"; shift 2 ;;
          *) shift ;;
        esac
      done
      _guard_cmux_env "reload" || exit $?
      local surface_arg=""
      [[ -n "$surface" ]] && surface_arg="--surface ${surface}"
      local user_owned="false"
      [[ -n "$surface" ]] && user_owned="true"
      local before_url=""
      # shellcheck disable=SC2086
      before_url=$(cmux browser ${surface_arg} url 2>/dev/null || echo "")
      # shellcheck disable=SC2086
      cmux browser ${surface_arg} reload 2>/dev/null || {
        json_err "reload" "eval_failed" "cmux browser reload 실패" >&2; exit 8
      }
      local after_url=""
      # shellcheck disable=SC2086
      after_url=$(cmux browser ${surface_arg} url 2>/dev/null || echo "")
      python3 - "${surface:-}" "$user_owned" "$before_url" "$after_url" <<'PYEOF'
import json, sys
surface, user_owned, before_url, after_url = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
print(json.dumps({"ok":True,"command":"reload","surface":None if surface=="" else surface,
  "user_owned":user_owned=="true","before_url":before_url,"after_url":after_url}, ensure_ascii=False))
PYEOF
      ;;

    # ── press ─────────────────────────────────────────────────────────────────
    press)
      local key="" surface=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --surface) surface="${2:-}"; shift 2 ;;
          *)         [[ -z "$key" ]] && key="$1"; shift ;;
        esac
      done
      _guard_cmux_env "press" || exit $?
      if [[ -z "$key" ]]; then
        json_err "press" "usage" "키 이름을 지정하세요 (예: Enter, Tab, Escape)" >&2; exit 1
      fi
      local surface_arg=""
      [[ -n "$surface" ]] && surface_arg="--surface ${surface}"
      local user_owned="false"
      [[ -n "$surface" ]] && user_owned="true"
      # shellcheck disable=SC2086
      cmux browser ${surface_arg} press "${key}" 2>/dev/null || {
        json_err "press" "eval_failed" "cmux browser press 실패: ${key}" >&2; exit 8
      }
      python3 - "${surface:-}" "$user_owned" "$key" <<'PYEOF'
import json, sys
surface, user_owned, key = sys.argv[1], sys.argv[2], sys.argv[3]
print(json.dumps({"ok":True,"command":"press","surface":None if surface=="" else surface,
  "user_owned":user_owned=="true","key":key}, ensure_ascii=False))
PYEOF
      ;;

    # ── get ───────────────────────────────────────────────────────────────────
    get)
      local selector="" surface="" attr_name=""
      while [[ $# -gt 0 ]]; do
        case "$1" in
          --surface) surface="${2:-}"; shift 2 ;;
          --attr)    attr_name="${2:-}"; shift 2 ;;
          *)         [[ -z "$selector" ]] && selector="$1"; shift ;;
        esac
      done
      _guard_cmux_env "get" || exit $?
      local surface_arg=""
      [[ -n "$surface" ]] && surface_arg="--surface ${surface}"
      local user_owned="false"
      [[ -n "$surface" ]] && user_owned="true"
      local value=""
      if [[ -n "$attr_name" ]]; then
        # shellcheck disable=SC2086
        value=$(cmux browser ${surface_arg} get attr "${selector}" --attr "${attr_name}" 2>/dev/null || echo "")
      else
        # shellcheck disable=SC2086
        value=$(cmux browser ${surface_arg} get "${selector}" 2>/dev/null || echo "")
      fi
      python3 - "${surface:-}" "$user_owned" "${selector:-}" "$value" <<'PYEOF'
import json, sys
surface, user_owned, selector, value = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
print(json.dumps({"ok":True,"command":"get","surface":None if surface=="" else surface,
  "user_owned":user_owned=="true","selector":selector,"value":value}, ensure_ascii=False))
PYEOF
      ;;

    # ── 알 수 없는 서브명령 ─────────────────────────────────────────────────────
    *)
      json_err "unknown" "usage" "알 수 없는 서브명령: ${subcommand}. run.sh --help로 목록 확인" >&2
      exit 1
      ;;
  esac
}

# ─── _dispatch_extract: 기존 run.sh extract 흐름 전체 ─────────────────────────
# [MUST] B/C 모드에서 tab close 절대 금지 — A) 케이스 내부에서만 호출.
_dispatch_extract() {
  local url="" surface_handle="" mode="full" wait_ms=2000
  local mode_type=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --surface)
        surface_handle="${2:-}"
        if [[ -z "$surface_handle" ]]; then
          json_err "extract" "usage" "--surface 다음에 핸들을 지정하세요 (예: surface:3)" "phase2" >&2
          exit 1
        fi
        shift 2 ;;
      --mode)    mode="${2:-full}"; shift 2 ;;
      --wait)    wait_ms="${2:-2000}"; shift 2 ;;
      http://*|https://*) url="$1"; shift ;;
      *)
        printf '{"ok":false,"command":"extract","error":"usage","detail":"알 수 없는 인자: %s","fallback":"phase2"}\n' "$1" >&2
        exit 1 ;;
    esac
  done

  # 인자 없음 시 사용법 오류
  if [[ -z "$url" && -z "$surface_handle" ]]; then
    json_err "extract" "usage" \
      "run.sh extract <url> 또는 run.sh extract --surface <handle> [url]" "phase2" >&2
    exit 1
  fi

  # 모드 결정
  if [[ -n "$surface_handle" && -n "$url" ]]; then
    mode_type="C"
  elif [[ -n "$surface_handle" && -z "$url" ]]; then
    mode_type="B"
  else
    mode_type="A"
  fi

  # 환경 가드
  _guard_cmux_env "extract" || exit $?

  # B/C 모드 핸들 검증
  if [[ "$mode_type" == "B" || "$mode_type" == "C" ]]; then
    _validate_surface_handle "$surface_handle" "extract" || exit 4
  fi

  local surface=""

  # ── 모드 A: 신규 surface 열기 ─────────────────────────────────────────────
  if [[ "$mode_type" == "A" ]]; then
    local open_out
    open_out=$(cmux browser open "$url" --workspace "${CMUX_WORKSPACE_ID:-}" --focus false 2>&1) || {
      json_err "extract" "open_failed" "cmux browser open 실패" "phase2" >&2; exit 5
    }
    surface=$(printf '%s\n' "$open_out" | grep -oE 'surface:[0-9]+' | head -1)
    if [[ -z "$surface" ]]; then
      json_err "extract" "surface_parse_failed" \
        "cmux browser open 출력에서 surface 핸들을 파싱할 수 없습니다" "phase2" >&2
      exit 5
    fi
  fi

  # ── 모드 B: 사용자 surface 그대로 사용 ────────────────────────────────────
  if [[ "$mode_type" == "B" ]]; then
    surface="$surface_handle"
  fi

  # ── 모드 C: 사용자 surface + navigate ─────────────────────────────────────
  if [[ "$mode_type" == "C" ]]; then
    surface="$surface_handle"
    cmux browser "$surface" goto "$url" 2>/dev/null || {
      json_err "extract" "goto_failed" "cmux browser goto 실패" "phase2" >&2; exit 6
    }
  fi

  # ── 로드 완료 대기 ─────────────────────────────────────────────────────────
  cmux browser "$surface" wait --load-state complete --timeout-ms 15000 2>/dev/null || {
    json_err "extract" "wait_failed" "페이지 로드 대기 타임아웃" "phase2" >&2
    # A 모드에서만 cleanup
    case "$mode_type" in
      A) cmux browser "$surface" tab close 2>/dev/null || true ;;
      B|C) ;;  # cleanup 금지 — 사용자 소유 surface
    esac
    exit 7
  }

  # ── 추가 대기 ──────────────────────────────────────────────────────────────
  if [[ "$wait_ms" -gt 0 ]]; then
    local wait_s
    wait_s=$(awk "BEGIN {printf \"%.3f\", $wait_ms/1000}")
    sleep "$wait_s"
  fi

  # ── 페이지 정보 추출 ────────────────────────────────────────────────────────
  local title final_url html_file
  title=$(cmux browser "$surface" get title 2>/dev/null) || title=""
  final_url=$(cmux browser "$surface" get url 2>/dev/null) || final_url="${url:-}"
  html_file=$(mktemp /tmp/cmux-tool-html.XXXXXX)
  cmux browser "$surface" eval --script "document.documentElement.outerHTML" > "$html_file" 2>/dev/null || {
    json_err "extract" "eval_failed" "HTML 추출 실패" "phase2" >&2
    rm -f "$html_file"
    # A 모드에서만 cleanup
    case "$mode_type" in
      A) cmux browser "$surface" tab close 2>/dev/null || true ;;
      B|C) ;;  # cleanup 금지 — 사용자 소유 surface
    esac
    exit 8
  }

  # ── A 모드에서만 tab close ([MUST] B/C 절대 금지) ──────────────────────────
  case "$mode_type" in
    A) cmux browser "$surface" tab close 2>/dev/null || true ;;
    B|C) ;;  # cleanup 금지 — 사용자 소유 surface
  esac

  # ── user_owned 결정 ────────────────────────────────────────────────────────
  local user_owned
  case "$mode_type" in
    A)   user_owned="false" ;;
    B|C) user_owned="true"  ;;
  esac

  # ── JSON 출력 (기존 8필드 + command 필드 추가 — R-2 호환) ──────────────────
  python3 - "$surface" "$user_owned" "$mode_type" "$title" "$final_url" \
    "$wait_ms" "$html_file" <<'PYEOF'
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
    "command": "extract",
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

  rm -f "$html_file" 2>/dev/null || true
}

# ─── 직접 실행 시 dispatch 호출 ─────────────────────────────────────────────
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  dispatch "$@"
fi
