#!/usr/bin/env bash
#
# opal/tools/opal-cli/lib/doctor.sh — doctor 서브커맨드
#
# Usage: opal-cli doctor [--help]
#
# 동작:
#   ~/.opal/tools/doctor/run.sh 에 위임한다.
#   doctor 도구가 설치되지 않은 경우 오류 메시지를 출력한다.
#
# 변경이력:
#   v1.0 2026-05-08 11:00 초기 구현 — doctor/run.sh 위임 (139)
#   v1.1 2026-07-10 doctor 도구 누락 안내를 opal-cli update(재배포)로 교체 — install 서브커맨드 제거에 정합 (055)
#

# ─── doctor 서브커맨드 ────────────────────────────────────────

cmd_doctor() {
    local arg="${1:-}"

    if [[ "$arg" == "--help" || "$arg" == "-h" ]]; then
        cat <<EOF
사용법: opal-cli doctor [--help]

OPAL 환경을 진단합니다.
의존성, 경로, MCP 등록, 부트스트래퍼 정합성을 점검합니다.

출력 섹션:
  [1/4] Dependencies    bash, git, Node.js, Python 버전 확인
  [2/4] OPAL Paths      ~/.opal/ 하위 필수 경로 존재 여부
  [3/4] MCP Registration Claude/Cursor/Gemini MCP 등록 상태
  [4/4] Bootstrappers   CLAUDE.md/GEMINI.md OPAL 마커 존재 여부

종료 코드:
  0   All Pass (경고·오류 없음)
  1   Fail 또는 Warn 발생

옵션:
  --help, -h    이 도움말 출력

예시:
  opal-cli doctor
EOF
        return 0
    fi

    local opal_home="${OPAL_HOME:-$HOME/.opal}"
    local doctor_run="$opal_home/tools/doctor/run.sh"

    if [[ ! -f "$doctor_run" ]]; then
        error "doctor 도구를 찾을 수 없습니다: $doctor_run"
        info "OPAL을 최신 배포본으로 갱신하면 doctor 도구가 포함됩니다:"
        info "  opal-cli update"
        return 1
    fi

    if [[ ! -x "$doctor_run" ]]; then
        chmod +x "$doctor_run"
    fi

    exec bash "$doctor_run" "$@"
}
