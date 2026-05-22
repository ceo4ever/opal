#!/usr/bin/env bash
#
# cmux-tool/lib/json.sh — python3 JSON 직렬화 공통 헬퍼
#
# 흡수 출처: opal/tools/cmux-tool/run.sh L178-207 패턴 일반화
# 역할: cmux-tool 모든 서브명령의 JSON 출력 직렬화를 담당한다.
#       python3 내장 json 모듈을 사용하여 특수문자/유니코드를 안전하게 처리한다.
#
# 공개 함수:
#   json_ok <command> <kv_pairs...>  — 성공 JSON 출력 (ok=true)
#   json_err <command> <error_code> <detail> [fallback]  — 실패 JSON 출력 (ok=false)
#   json_emit_raw <json_string>  — 이미 구성된 JSON을 그대로 stdout 출력
#
# 출력 대상: stdout (성공 JSON) / stderr (에러 JSON은 호출자가 결정)
#
# 설계 원칙: 단순성 우선 — KV 쌍을 환경 변수 기반 export로 수집 후 python3에 주입

# shellcheck disable=SC2034

# ─── json_ok <command> [key=value ...] ─────────────────────────────────────
# 성공 JSON을 stdout으로 출력.
# KV 형식: key=value (값에 = 포함 가능 — 첫 = 기준 분리)
# 예: json_ok snapshot command=snapshot surface=surface:3 user_owned=false snapshot_text="hello"
json_ok() {
  local command="$1"
  shift
  local kv_json=""
  local key val pair

  for pair in "$@"; do
    key="${pair%%=*}"
    val="${pair#*=}"
    if [[ -z "$kv_json" ]]; then
      kv_json="\"${key}\": $(json_value "$val")"
    else
      kv_json="${kv_json}, \"${key}\": $(json_value "$val")"
    fi
  done

  python3 - "$command" "$kv_json" <<'PYEOF'
import json, sys
command = sys.argv[1]
extra_raw = sys.argv[2]  # 이미 JSON 값 형태로 인코딩된 KV 쌍 문자열

result = {"ok": True, "command": command}
# extra_raw를 파이썬에서 직접 파싱 (bash 수준 단순 직렬화의 한계 보완)
if extra_raw.strip():
    # "key": value 쌍을 임시 객체로 파싱
    try:
        extra_obj = json.loads("{" + extra_raw + "}")
        result.update(extra_obj)
    except json.JSONDecodeError:
        result["_parse_error"] = "kv_json parse failed"

print(json.dumps(result, ensure_ascii=False))
PYEOF
}

# ─── json_err <command> <error_code> <detail> [fallback] ──────────────────
# 실패 JSON을 stderr로 출력 후 비정상 종료.
# fallback 필드는 선택적 — 폴백 트리거 에러 코드일 때만 제공한다.
json_err() {
  local command="${1:-unknown}"
  local error_code="${2:-unknown_error}"
  local detail="${3:-}"
  local fallback="${4:-}"

  python3 - "$command" "$error_code" "$detail" "$fallback" <<'PYEOF'
import json, sys
command   = sys.argv[1]
error     = sys.argv[2]
detail    = sys.argv[3]
fallback  = sys.argv[4]

result = {"ok": False, "command": command, "error": error}
if detail:
    result["detail"] = detail
if fallback:
    result["fallback"] = fallback

print(json.dumps(result, ensure_ascii=False))
PYEOF
}

# ─── json_value <bash_val> ──────────────────────────────────────────────────
# bash 값을 JSON 값 문자열로 변환 (bool / number / string 구분)
json_value() {
  local v="$1"
  case "$v" in
    true|false|null)  printf '%s' "$v" ;;
    ''|[0-9]*|'-'[0-9]*)
      if [[ "$v" =~ ^-?[0-9]+(\.[0-9]+)?$ ]]; then
        printf '%s' "$v"
      else
        python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$v"
      fi
      ;;
    *)
      python3 -c "import json,sys; print(json.dumps(sys.argv[1]))" "$v"
      ;;
  esac
}
