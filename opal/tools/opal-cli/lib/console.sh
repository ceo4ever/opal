#!/usr/bin/env bash
#
# opal/tools/opal-cli/lib/console.sh — console 서브커맨드
#
# Usage:
#   opal-cli console start   — OPAL Console 대시보드 백그라운드 기동 (포트 7823)
#   opal-cli console stop    — 실행 중인 대시보드 데몬 종료
#   opal-cli console status  — /health 엔드포인트로 기동 상태 확인
#   opal-cli console open    — 브라우저에서 대시보드 열기
#
# 전제:
#   - ~/.opal/dashboard-server/dashboard/backend/ — install 후 BE 배포 경로 (패키지 구조)
#   - ~/.opal/dashboard-server/dashboard/__init__.py — 패키지 루트 마커
#   - ~/.opal/.venv/bin/uvicorn — OPAL 공유 venv (fastapi[standard] 포함)
#   - host: 127.0.0.1, port: 7823 — localhost 바인딩 (외부 노출 금지, H-7)
#   - uvicorn --app-dir ~/.opal/dashboard-server dashboard.backend.main:app
#     → 'from dashboard.backend.routers import ...' 절대 import 정상 동작
#
# 변경이력:
#   v1.0 2026-06-15 신규 구현 — console start/stop/status/open 서브커맨드 (021)
#   v1.1 2026-06-15 [fix] --app-dir 를 dashboard-server 로 변경 + app 경로 dashboard.backend.main:app (021)
#

# ─── console 서브커맨드 ───────────────────────────────────────

cmd_console() {
    local action="${1:-}"
    local opal_home="${OPAL_HOME:-$HOME/.opal}"
    local venv_uvicorn="$opal_home/.venv/bin/uvicorn"
    # 배포 구조: ~/.opal/dashboard-server/dashboard/backend/ (패키지 루트: dashboard-server/)
    local dashboard_server="$opal_home/dashboard-server"
    local dashboard_pkg="$dashboard_server/dashboard/backend"
    local host="127.0.0.1"
    local port="7823"
    local health_url="http://${host}:${port}/health"

    case "$action" in
        start)
            # 이미 기동 중인지 확인
            if curl -s --max-time 2 "$health_url" >/dev/null 2>&1; then
                warn "OPAL Console이 이미 ${host}:${port} 에서 실행 중입니다."
                return 0
            fi

            if [[ ! -f "$venv_uvicorn" ]]; then
                error "uvicorn을 찾을 수 없습니다: $venv_uvicorn"
                error "opal-cli install 을 먼저 실행하세요."
                exit 1
            fi

            if [[ ! -d "$dashboard_pkg" ]]; then
                error "dashboard-server/dashboard/backend 를 찾을 수 없습니다: $dashboard_pkg"
                error "opal-cli install 을 먼저 실행하세요."
                exit 1
            fi

            info "OPAL Console 기동 중 (${host}:${port})..."
            # 백그라운드 기동 — host=127.0.0.1 바인딩(H-7), nohup으로 터미널 종료 후에도 유지
            # --app-dir 는 패키지 루트(dashboard-server/)를 가리킴
            # → 'from dashboard.backend.routers import ...' 절대 import 정상 동작
            nohup "$venv_uvicorn" \
                --app-dir "$dashboard_server" \
                dashboard.backend.main:app \
                --host "$host" \
                --port "$port" \
                >/tmp/opal-console.log 2>&1 &
            success "OPAL Console 기동됨 (PID: $!, 로그: /tmp/opal-console.log)"
            info "상태 확인: opal-cli console status"
            info "브라우저 열기: opal-cli console open"
            ;;

        stop)
            if pkill -f "dashboard.backend.main:app" 2>/dev/null; then
                success "OPAL Console 데몬 종료됨."
            else
                warn "실행 중인 OPAL Console 데몬을 찾을 수 없습니다."
            fi
            ;;

        status)
            local response
            response="$(curl -s --max-time 5 "$health_url" 2>/dev/null)"
            if [[ $? -eq 0 && -n "$response" ]]; then
                success "OPAL Console 실행 중 (${health_url})"
                echo "$response"
            else
                warn "OPAL Console 응답 없음 (${health_url})"
                info "기동 방법: opal-cli console start"
                exit 1
            fi
            ;;

        open)
            local dashboard_url="http://${host}:${port}"
            # macOS: open, Linux: xdg-open (플랫폼 분기 — CONVENTIONS §플랫폼 분기 격리)
            if command -v open &>/dev/null; then
                open "$dashboard_url" 2>/dev/null && success "브라우저 열기: $dashboard_url"
            elif command -v xdg-open &>/dev/null; then
                xdg-open "$dashboard_url" 2>/dev/null && success "브라우저 열기: $dashboard_url"
            else
                info "브라우저에서 직접 여세요: $dashboard_url"
            fi
            ;;

        --help|-h|"")
            cat <<EOF
사용법: opal-cli console <action>

OPAL Console 대시보드 (포트 7823) 관리 명령어입니다.

액션:
  start    대시보드 백그라운드 기동
  stop     대시보드 데몬 종료
  status   기동 상태 확인 (/health)
  open     브라우저에서 대시보드 열기

예시:
  opal-cli console start
  opal-cli console status
  opal-cli console open
  opal-cli console stop

전제: opal-cli install 실행 후 사용 가능합니다.
EOF
            ;;

        *)
            error "알 수 없는 액션: $action"
            error "사용 가능한 액션: start | stop | status | open"
            exit 1
            ;;
    esac
}
