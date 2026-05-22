#!/usr/bin/env bash
# shellcheck disable=SC2155
# Usage: source "$(dirname "${BASH_SOURCE[0]}")/_lib.sh"
#
# cmux 0.60+ 호환 공통 함수 모음.
# cmux CLI 변경 이력(2026-04-18 069 태스크 기준):
#   - new-surface 는 --name/--cwd/--command 플래그를 더 이상 지원하지 않는다
#   - 따라서 "new-surface 생성 → rename-tab → send(명령 텍스트) → send-key Enter → 검증"
#     순서로 surface를 기동해야 한다 (이전 스크립트가 빈 surface만 만들고
#     기동에 실패했던 회귀 방지용)

# ─── Surface 기동 ────────────────────────────────────────────────────────────
# start_surface <name> <cwd> <cmd> <log>
# 성공 시 surface ref(예: "surface:15")를 stdout으로 출력, 실패 시 비-0 반환.
start_surface() {
  local name="$1"
  local cwd="$2"
  local cmd="$3"
  local log="$4"

  if [ -z "${name}" ] || [ -z "${cwd}" ] || [ -z "${cmd}" ] || [ -z "${log}" ]; then
    echo "[ERROR] start_surface: name/cwd/cmd/log 모두 필요" >&2
    return 2
  fi

  local out
  if ! out=$(cmux new-surface --type terminal 2>&1); then
    echo "[ERROR] cmux new-surface 실패: ${out}" >&2
    return 1
  fi

  local surface
  surface=$(printf '%s' "${out}" | grep -oE 'surface:[0-9]+' | head -1)
  if [ -z "${surface}" ]; then
    echo "[ERROR] surface ref 파싱 실패 (응답: ${out})" >&2
    return 1
  fi

  cmux rename-tab --surface "${surface}" "${name}" >/dev/null 2>&1 || true

  local full="cd \"${cwd}\" && ${cmd} 2>&1 | tee \"${log}\""
  if ! cmux send --surface "${surface}" "${full}" >/dev/null; then
    echo "[ERROR] cmux send 실패 (${surface})" >&2
    return 1
  fi
  if ! cmux send-key --surface "${surface}" Enter >/dev/null; then
    echo "[ERROR] cmux send-key Enter 실패 (${surface})" >&2
    return 1
  fi

  echo "[INFO] ${name} → ${surface} (log: ${log})" >&2
  printf '%s' "${surface}"
}

# ─── Surface 기동 검증 ───────────────────────────────────────────────────────
# verify_surface <name> <surface> <log> <ready_pattern> [timeout_sec]
# 준비 완료 패턴을 로그 또는 read-screen에서 감지하면 0 반환, 시간 초과 시 비-0.
verify_surface() {
  local name="$1"
  local surface="$2"
  local log="$3"
  local pattern="$4"
  local timeout="${5:-60}"

  if [ -z "${name}" ] || [ -z "${surface}" ] || [ -z "${log}" ] || [ -z "${pattern}" ]; then
    echo "[ERROR] verify_surface: name/surface/log/pattern 필요" >&2
    return 2
  fi

  local elapsed=0
  while [ "${elapsed}" -lt "${timeout}" ]; do
    if [ -f "${log}" ] && grep -qE "${pattern}" "${log}" 2>/dev/null; then
      echo "[OK] ${name} ready — log 매칭 (\"${pattern}\")" >&2
      return 0
    fi
    if cmux read-screen --surface "${surface}" --lines 60 2>/dev/null | grep -qE "${pattern}"; then
      echo "[OK] ${name} ready — screen 매칭 (\"${pattern}\")" >&2
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done

  echo "[ERROR] ${name} 기동 확인 실패 — ${timeout}s 내 \"${pattern}\" 미감지" >&2
  echo "--- ${log} (tail 20) ---" >&2
  tail -20 "${log}" 2>/dev/null || echo "(로그 파일 없음)" >&2
  echo "--- read-screen (last 30) ---" >&2
  cmux read-screen --surface "${surface}" --lines 30 2>/dev/null || true
  return 1
}

# ─── 대상별 준비 패턴 ────────────────────────────────────────────────────────
# 대상 이름을 받아 해당 서버의 "기동 완료" 패턴을 반환한다.
ready_pattern_for() {
  case "$1" in
    be)       printf '%s' 'Application startup complete|Uvicorn running on' ;;
    fe)       printf '%s' 'Ready in|started server on' ;;
    fe-wire)  printf '%s' 'Ready in|started server on' ;;
    fe-test)  printf '%s' 'Ready in|started server on' ;;
    batch)    printf '%s' 'Listening at|Running on|airflow-apiserver.*healthy' ;;
    *)        printf '%s' 'Ready|started|listening' ;;
  esac
}
