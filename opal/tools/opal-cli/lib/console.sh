#!/usr/bin/env bash
#
# opal/tools/opal-cli/lib/console.sh — console 서브커맨드
#
# Usage:
#   opal-cli console start   — OPAL Console 대시보드 백그라운드 기동 (포트 7823)
#   opal-cli console stop    — 실행 중인 대시보드 데몬 종료
#   opal-cli console status  — /health 엔드포인트로 기동 상태 확인
#   opal-cli console open    — 브라우저에서 대시보드 열기
#   opal-cli console scan [기준경로...] [--prune] [--depth N]
#                             — console.config.json 자동 생성·머지 (기본 base=$HOME, depth=3)
#   opal-cli console log [-n N] — 로그 실시간 팔로우 (기본 최근 50줄부터, Ctrl+C 종료)
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
#   v1.2 2026-07-10 컴포넌트 누락·전제 안내를 opal-cli update(재배포)로 교체 — install 서브커맨드 제거에 정합 (055)
#   v1.3 2026-07-10 18:07 scan 서브명령 신설 — console.config.json 자동 생성/머지 + start 가드 안내 (057)
#   v1.4 2026-07-13 17:43 log 서브명령 신설 — tail -F 실시간 팔로우(-n N) + 로그 경로 변수 추출 (L2)
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
    local log_file="/tmp/opal-console.log"

    case "$action" in
        start)
            # console.config.json 부재 안내 (F-004) — 기동은 계속 진행(중단 금지)
            local console_config_path="$opal_home/console.config.json"
            if [[ ! -f "$console_config_path" ]]; then
                warn "console.config.json이 없습니다 — 대시보드에 프로젝트가 안 보일 수 있습니다."
                info "먼저 스캔을 실행하세요: opal-cli console scan <프로젝트-기준경로>"
            fi

            # 이미 기동 중인지 확인
            if curl -s --max-time 2 "$health_url" >/dev/null 2>&1; then
                warn "OPAL Console이 이미 ${host}:${port} 에서 실행 중입니다."
                return 0
            fi

            if [[ ! -f "$venv_uvicorn" ]]; then
                error "uvicorn을 찾을 수 없습니다: $venv_uvicorn"
                error "opal-cli update 로 최신 배포본을 재배포하세요."
                exit 1
            fi

            if [[ ! -d "$dashboard_pkg" ]]; then
                error "dashboard-server/dashboard/backend 를 찾을 수 없습니다: $dashboard_pkg"
                error "opal-cli update 로 최신 배포본을 재배포하세요."
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
                >"$log_file" 2>&1 &
            success "OPAL Console 기동됨 (PID: $!, 로그: $log_file)"
            info "상태 확인: opal-cli console status"
            info "로그 팔로우: opal-cli console log"
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

        scan)
            # console.config.json 자동 생성/머지 (F-001, F-002) — .opal/AGENT.md 마커 탐색 → scan_root 도출
            shift
            local prune_flag=0
            local depth=3
            local -a bases=()
            while [[ $# -gt 0 ]]; do
                if [[ "$1" == "--prune" ]]; then
                    prune_flag=1
                    shift
                elif [[ "$1" == "--depth" ]]; then
                    depth="${2:-3}"
                    shift 2
                else
                    bases+=("$1")
                    shift
                fi
            done

            if [[ ${#bases[@]} -eq 0 ]]; then
                bases=("$HOME")
                info "기준경로 미지정 — 기본값 \$HOME(${HOME})에서 탐색합니다." >&2
                info "프로젝트가 안 보이면 기준경로를 명시하세요: opal-cli console scan <기준경로>" >&2
            fi

            local maxdepth=$((depth + 2))
            local projects_found=0
            local -a discovered_roots=()
            local scan_base hit project_dir scan_root

            for scan_base in "${bases[@]}"; do
                if [[ ! -d "$scan_base" ]]; then
                    warn "기준경로가 존재하지 않습니다: $scan_base" >&2
                    continue
                fi
                while IFS= read -r hit; do
                    [[ -z "$hit" ]] && continue
                    project_dir="${hit%/.opal/AGENT.md}"
                    # $OPAL_HOME 자체가 마커로 잡히면 discovery에서 제외 (H-2)
                    if [[ "$project_dir/.opal" == "$opal_home" ]]; then
                        continue
                    fi
                    projects_found=$((projects_found + 1))
                    scan_root="$(dirname "$project_dir")"
                    discovered_roots+=("$scan_root")
                done < <(find "$scan_base" -maxdepth "$maxdepth" \
                    -type d \( -name node_modules -o -name .git -o -name .venv -o -name __pycache__ -o -name .DS_Store \) -prune -o \
                    -type f -path '*/.opal/AGENT.md' -print 2>/dev/null)
            done

            local scan_config_path="$opal_home/console.config.json"
            local prune_arg="0"
            [[ "$prune_flag" -eq 1 ]] && prune_arg="1"

            set -- "$scan_config_path" "$prune_arg" "$projects_found"
            if [[ ${#discovered_roots[@]} -gt 0 ]]; then
                set -- "$@" "${discovered_roots[@]}"
            fi

            local merge_output
            local merge_exit
            if merge_output="$(python3 - "$@" <<'PYEOF'
import json
import os
import sys

config_path = sys.argv[1]
prune = sys.argv[2] == "1"
projects_found = int(sys.argv[3])
discovered = sys.argv[4:]

# 순서 보존 dedup (discovered)
disc_dedup = []
seen = set()
for r in discovered:
    if r not in seen:
        disc_dedup.append(r)
        seen.add(r)

existed = os.path.exists(config_path)
data = {}
if existed:
    try:
        with open(config_path, encoding="utf-8") as f:
            content = f.read()
        data = json.loads(content) if content.strip() else {}
    except (json.JSONDecodeError, OSError) as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        sys.exit(1)

existing = list(data.get("scan_roots", []))

if prune:
    # --prune: scan이 못 찾은 기존 root 제거 (C-3)
    merged = list(disc_dedup)
else:
    # 기본: 기존 roots 보존 + 신규 추가
    merged = list(existing)
    for r in disc_dedup:
        if r not in merged:
            merged.append(r)

# 순서 보존 dedup (merged)
final = []
seen2 = set()
for r in merged:
    if r not in seen2:
        final.append(r)
        seen2.add(r)

data["scan_roots"] = final

if not existed:
    # 신규 생성 시에만 기본값 기록 (config.py DEFAULT_SCAN_DEPTH/DEFAULT_EXCLUDE와 동일)
    data.setdefault("scan_depth", 2)
    data.setdefault("exclude", ["node_modules", ".git", ".venv", "__pycache__", ".DS_Store"])

added = [r for r in final if r not in existing]

os.makedirs(os.path.dirname(config_path), exist_ok=True)
with open(config_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(json.dumps({
    "ok": True,
    "created": not existed,
    "added_roots": added,
    "projects_found": projects_found,
}))
PYEOF
)"; then
                merge_exit=0
            else
                merge_exit=$?
            fi

            # 출력 계약 (C-6): stdout에 JSON 1줄만. 사람용 로그는 전부 stderr.
            echo "$merge_output"

            if [[ "$merge_exit" -ne 0 ]]; then
                error "console.config.json 갱신 실패 — 위 오류를 확인하세요."
                exit 1
            fi

            success "console.config.json 갱신 완료: $scan_config_path" >&2
            ;;

        log)
            # 실시간 로그 팔로우 — tail -F: start가 >(truncate)로 재기동해도 이름 기준 재추적
            shift
            local tail_lines=50
            while [[ $# -gt 0 ]]; do
                if [[ "$1" == "-n" ]]; then
                    tail_lines="${2:-50}"
                    shift 2
                else
                    warn "알 수 없는 옵션 무시: $1"
                    shift
                fi
            done

            if [[ ! -f "$log_file" ]]; then
                error "로그 파일이 없습니다: $log_file"
                info "먼저 기동하세요: opal-cli console start"
                exit 1
            fi

            info "로그 팔로우 시작 — 최근 ${tail_lines}줄부터 (Ctrl+C 종료): $log_file"
            tail -n "$tail_lines" -F "$log_file"
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
  scan     console.config.json 자동 생성/머지 (기준경로 탐색)
  log      로그 실시간 팔로우 (기본 최근 50줄부터, -n N 으로 조정, Ctrl+C 종료)

예시:
  opal-cli console start
  opal-cli console status
  opal-cli console open
  opal-cli console stop
  opal-cli console scan
  opal-cli console scan /Volumes/Data/workspace --depth 3
  opal-cli console scan --prune /Volumes/Data/workspace
  opal-cli console log
  opal-cli console log -n 200

전제: opal-cli update 로 대시보드 배포본(dashboard-server·venv) 반영 후 사용 가능합니다.
EOF
            ;;

        *)
            error "알 수 없는 액션: $action"
            error "사용 가능한 액션: start | stop | status | open | scan | log"
            exit 1
            ;;
    esac
}
