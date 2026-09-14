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
#   v1.5 2026-09-13 Console 프로세스 소유권을 PID 레코드(identity) 기반으로 전환 — start가 $OPAL_HOME/run/console.pid에
#     6필드 JSON을 기록하고, stop의 전역 프로세스 이름 패턴 종료(ASGI 경로 문자열 기준 광역 종료, RK-1)를 제거해
#     레코드 identity(app_dir 일치 + kill -0 생존) 검증 후에만 종료. status에 소유권(pid/app_dir 등) 노출 추가.
#     E2E backend와 사용자 Console이 동일 ASGI 경로 문자열로 뜰 때 서로를 오탐 종료하던 결함 제거
#     (TASK.md AC-3, CONTRACT.md §A.13·§B.4, PLAN.md D-1~D-18, MV-21) (127-T02)
#

# ─── PID 레코드 헬퍼 (§A.13, D-2·D-12) ─────────────────────────
# 이 함수들은 opal-cli console 서브커맨드와 독립적으로 source·호출 가능해야 한다
# (test-tool은 이 파일 포맷만 문서 계약으로 공유하며 런타임 의존은 0이다 — CONTRACT §C.1).

# console_record_path <opal_home> — PID 레코드 경로를 stdout으로 출력한다.
console_record_path() {
    printf '%s/run/console.pid' "$1"
}

# _console_pid_value_unsafe <value> — D-2: "·\·제어문자(개행·탭·CR·ESC 등 전체)가 있으면 참(0)을 반환한다.
# 순수 셸 파서가 이스케이프를 하지 않으므로(F-9(1)), 이 문자들을 포함한 값은 기록 자체를 거부한다.
# [[ =~ ]]는 파이프를 거치지 않고 전체 문자열을 그대로 정규식과 비교하므로(외부 grep의 줄 단위 소비 문제가 없다),
# 개행뿐 아니라 ESC 등 모든 제어문자를 [[:cntrl:]] 한 클래스로 검출한다(T4b m-8: 레코드 출력 인젝션 방지 재사용).
_console_pid_value_unsafe() {
    local value="$1"
    case "$value" in
        *'"'*|*'\'*) return 0 ;;
    esac
    if [[ "$value" =~ [[:cntrl:]] ]]; then
        return 0
    fi
    return 1
}

# _console_pid_sane <value> — T4b B-1: kill(1) 대상으로 안전한 pid인지 검증한다.
# POSIX kill(1)에서 pid 0은 호출자의 프로세스 그룹 전체, 음수는 그 절대값의 프로세스 그룹 전체를 가리키고
# pid 1은 init이다. 레코드 identity 판정·종료 대상은 반드시 실제 단일 사용자 프로세스(pid>=2)여야 한다.
_console_pid_sane() {
    case "$1" in ''|*[!0-9]*) return 1 ;; esac
    [ "$1" -ge 2 ] 2>/dev/null
}

# console_write_pid_record <opal_home> <app_dir> <host> <port> <pid>
# D-12: 값 제약 위반(따옴표·역슬래시·제어문자) 또는 쓰기 실패 시 return 1 — 파일을 만들지 않는다(D-2·fail-safe).
# T4b m-5·m-6: run/ 디렉터리 0700 생성 + 심볼릭 링크 대상 거부 + tmp 파일 경유 원자적 교체 + 레코드 파일 0600.
console_write_pid_record() {
    local opal_home="$1" app_dir="$2" host="$3" port="$4" pid="$5"

    if _console_pid_value_unsafe "$opal_home" || _console_pid_value_unsafe "$app_dir" \
        || _console_pid_value_unsafe "$host"; then
        return 1
    fi
    _console_pid_sane "$pid" || return 1
    case "$port" in
        ''|*[!0-9]*) return 1 ;;
    esac

    local run_dir="$opal_home/run"
    mkdir -p -m 700 "$run_dir" 2>/dev/null || return 1

    local record_path tmp_path started_at
    record_path="$(console_record_path "$opal_home")"
    # 레코드 경로가 심볼릭 링크면(예: /tmp 경쟁으로 다른 경로를 가리키도록 선점) 쓰지 않는다.
    [[ -L "$record_path" ]] && return 1
    tmp_path="${record_path}.tmp.$$"
    started_at="$(date +%Y-%m-%dT%H:%M:%S%z)"

    printf '{"pid": %s, "opal_home": "%s", "app_dir": "%s", "host": "%s", "port": %s, "started_at": "%s"}\n' \
        "$pid" "$opal_home" "$app_dir" "$host" "$port" "$started_at" \
        > "$tmp_path" 2>/dev/null || { rm -f "$tmp_path" 2>/dev/null; return 1; }
    chmod 600 "$tmp_path" 2>/dev/null
    mv -f "$tmp_path" "$record_path" 2>/dev/null || { rm -f "$tmp_path" 2>/dev/null; return 1; }
    return 0
}

# console_read_pid_field <content> <field> — 레코드 파일을 1회 읽은 $content 문자열에서 필드값을 추출해
# stdout으로 출력한다. 미발견 시 return 1. T4b M-1: 호출자가 파일을 1회만 읽어 스냅샷으로 넘기게 해
# 여러 필드를 각각 재오픈하며 발생하던 TOCTOU(레코드가 그 사이 교체되는) 창을 닫는다.
# T4b m-4: field는 명시 allowlist만 허용 — sed 스크립트에 임의 문자열이 보간되지 않는다.
# writer가 이스케이프를 하지 않으므로(D-2) 이 reader도 언이스케이프를 하지 않는다 — 바이트 대칭.
console_read_pid_field() {
    local content="$1" field="$2" val
    case "$field" in
        pid|port)
            val="$(printf '%s\n' "$content" | sed -n "s/.*\"$field\"[[:space:]]*:[[:space:]]*\([0-9][0-9]*\).*/\\1/p" 2>/dev/null | head -1)"
            ;;
        opal_home|app_dir|host|started_at)
            val="$(printf '%s\n' "$content" | sed -n "s/.*\"$field\"[[:space:]]*:[[:space:]]*\"\\([^\"]*\\)\".*/\\1/p" 2>/dev/null | head -1)"
            ;;
        *)
            return 1
            ;;
    esac
    [[ -n "$val" ]] || return 1
    printf '%s' "$val"
    return 0
}

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

            # D-8: 3분기 — ① 레코드 기반 "이미 실행 중" ② 레코드 없이 응답(구버전 daemon) ③ 정상 기동
            local record_path
            record_path="$(console_record_path "$opal_home")"
            local pid=""
            local app_dir=""
            if [[ -f "$record_path" ]]; then
                local record_content
                record_content="$(cat "$record_path" 2>/dev/null)"
                pid="$(console_read_pid_field "$record_content" pid)" || pid=""
                app_dir="$(console_read_pid_field "$record_content" app_dir)" || app_dir=""
            fi

            # ① 레코드 존재 + 생존 + app_dir 일치 → 이미 실행 중 (T4b B-1: pid 0/1은 kill -0 대상에서 배제)
            if [[ -n "$pid" && -n "$app_dir" ]] \
                && _console_pid_sane "$pid" \
                && [[ "$app_dir" == "$dashboard_server" ]] \
                && kill -0 "$pid" 2>/dev/null; then
                warn "OPAL Console이 이미 실행 중입니다 (PID: $pid)."
                return 0
            fi

            # ② 레코드 없음·stale·불일치인데 health가 응답 — 구버전 daemon(TRD.md:235, H-1)
            if curl -s --max-time 2 "$health_url" >/dev/null 2>&1; then
                warn "PID 레코드 없이 ${host}:${port}가 응답 중입니다 — 이 프로세스는 opal-cli가 소유하지 않습니다."
                info "이 버전은 PID 레코드로 소유 프로세스만 종료합니다. 이전 버전에서 기동한 데몬은 레코드가 없어 종료되지 않습니다 — 'lsof -ti tcp:7823' 로 확인 후 수동 종료하고 'opal-cli console start' 로 재기동하세요."
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

            # ③ 정상 기동 — D-12(가): nohup 이전에 레코드 값 제약(D-2)을 사전 검증한다.
            # 위반 시 기동하지 않는다 — 레코드 없이 데몬만 뜨면 이후 stop이 영구 stale 경로로 밀린다.
            # T4b M-3: writer(console_write_pid_record)가 실제로 쓰는 판정(_console_pid_value_unsafe, 제어문자 포함)과
            # 반드시 같은 기준을 여기서도 적용한다 — 사전검사가 더 느슨하면 그 틈으로 뜬 데몬이 레코드 없이 고아가 된다.
            if [[ "$opal_home" == *'"'* || "$dashboard_server" == *'"'* ]] \
                || _console_pid_value_unsafe "$opal_home" || _console_pid_value_unsafe "$dashboard_server"; then
                error "OPAL_HOME 또는 dashboard-server 경로에 허용되지 않는 문자(\"·\\·제어문자)가 포함되어 있습니다: $opal_home / $dashboard_server"
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
            local pid=$!
            if ! console_write_pid_record "$opal_home" "$dashboard_server" "$host" "$port" "$pid"; then
                warn "PID 레코드를 기록하지 못했습니다 — 이 데몬은 'opal-cli console stop'으로 종료되지 않습니다."
                info "이 버전은 PID 레코드로 소유 프로세스만 종료합니다. 이전 버전에서 기동한 데몬은 레코드가 없어 종료되지 않습니다 — 'lsof -ti tcp:7823' 로 확인 후 수동 종료하고 'opal-cli console start' 로 재기동하세요."
            fi
            success "OPAL Console 기동됨 (PID: $pid, 로그: $log_file)"
            info "pid_record_path=$record_path"
            info "pid=$pid host=$host port=$port log_file=$log_file"
            info "상태 확인: opal-cli console status"
            info "로그 팔로우: opal-cli console log"
            info "브라우저 열기: opal-cli console open"
            ;;

        stop)
            # D-11/§변경 후 stop 판정표(PLAN.md) — 전역 이름 패턴 종료 제거, 레코드 identity 기반 종료
            local record_path
            record_path="$(console_record_path "$opal_home")"

            if [[ ! -f "$record_path" ]]; then
                # 판정표 #1
                warn "실행 중인 OPAL Console 데몬 레코드를 찾을 수 없습니다: $record_path"
                info "이 버전은 PID 레코드로 소유 프로세스만 종료합니다. 이전 버전에서 기동한 데몬은 레코드가 없어 종료되지 않습니다 — 'lsof -ti tcp:7823' 로 확인 후 수동 종료하고 'opal-cli console start' 로 재기동하세요."
                echo "stopped=false pid=- reason=no_record"
                return 0
            fi

            local record_content
            record_content="$(cat "$record_path" 2>/dev/null)"
            local rec_pid rec_app_dir
            rec_pid="$(console_read_pid_field "$record_content" pid)" || rec_pid=""
            rec_app_dir="$(console_read_pid_field "$record_content" app_dir)" || rec_app_dir=""

            # 판정표 #2 — 파싱 실패 또는 pid가 kill(1) 대상으로 안전하지 않음(T4b B-1: 0/1/음수/비정수는
            # unreadable_record로 합류시킨다 — 새 분기를 만들지 않는다): 레코드 보존, kill 0회
            if [[ -z "$rec_pid" || -z "$rec_app_dir" ]] || ! _console_pid_sane "$rec_pid"; then
                warn "PID 레코드를 해석할 수 없습니다: $record_path"
                echo "stopped=false pid=- reason=unreadable_record"
                return 0
            fi

            if [[ "$rec_app_dir" != "$dashboard_server" ]]; then
                # 판정표 #3 — identity 불일치: 레코드 보존, kill 0회
                warn "레코드의 app_dir가 현재 OPAL_HOME과 일치하지 않습니다: $rec_app_dir (기대: $dashboard_server)"
                echo "stopped=false pid=- reason=identity_mismatch"
                return 0
            fi

            if ! kill -0 "$rec_pid" 2>/dev/null; then
                # 판정표 #4 — stale: 레코드 삭제, kill 0회
                warn "레코드의 프로세스가 이미 종료되어 있습니다 (PID: $rec_pid) — stale 레코드를 정리합니다."
                rm -f "$record_path"
                echo "stopped=false pid=$rec_pid reason=stale_record"
                return 0
            fi

            # 판정표 #5/#6 — identity 일치 + 생존: SIGTERM 후 최대 5초 폴링(D-6)
            kill "$rec_pid" 2>/dev/null || true
            local waited=0
            while kill -0 "$rec_pid" 2>/dev/null; do
                if [[ "$waited" -ge 5 ]]; then
                    warn "종료 신호를 보냈으나 아직 실행 중입니다 (PID: $rec_pid)"
                    echo "stopped=false pid=$rec_pid reason=terminate_timeout"
                    return 0
                fi
                sleep 1
                waited=$((waited + 1))
            done

            rm -f "$record_path"
            success "OPAL Console 데몬 종료됨 (PID: $rec_pid)."
            echo "stopped=true pid=$rec_pid"
            ;;

        status)
            local record_path
            record_path="$(console_record_path "$opal_home")"
            local response curl_rc health_ok=1
            response="$(curl -s --max-time 5 "$health_url" 2>/dev/null)"
            curl_rc=$?
            if [[ "$curl_rc" -eq 0 && -n "$response" ]]; then
                success "OPAL Console 실행 중 (${health_url})"
                echo "$response"
            else
                warn "OPAL Console 응답 없음 (${health_url})"
                info "기동 방법: opal-cli console start"
                health_ok=0
            fi

            # D-10: health 성공·실패 양 분기 모두 소유권 레코드 줄을 출력한다. exit code만 health가 결정한다.
            if [[ -f "$record_path" ]]; then
                local record_content
                record_content="$(cat "$record_path" 2>/dev/null)"
                local rec_pid rec_app_dir rec_opal_home rec_host rec_port rec_started_at
                rec_pid="$(console_read_pid_field "$record_content" pid)" || rec_pid=""
                rec_app_dir="$(console_read_pid_field "$record_content" app_dir)" || rec_app_dir=""
                rec_opal_home="$(console_read_pid_field "$record_content" opal_home)" || rec_opal_home=""
                rec_host="$(console_read_pid_field "$record_content" host)" || rec_host=""
                rec_port="$(console_read_pid_field "$record_content" port)" || rec_port=""
                rec_started_at="$(console_read_pid_field "$record_content" started_at)" || rec_started_at=""

                # T4b B-1: pid 0/1/음수/비정수는 생존 판정에서 제외. T4b m-8: 출력 대상 문자열 필드를
                # 표시 직전 재검증해 수기 편집된 레코드의 제어문자(터미널 출력 인젝션)가 그대로 echo되지 않게 한다.
                if [[ -n "$rec_pid" && -n "$rec_app_dir" ]] \
                    && _console_pid_sane "$rec_pid" \
                    && ! _console_pid_value_unsafe "$rec_app_dir" \
                    && ! _console_pid_value_unsafe "$rec_opal_home" \
                    && ! _console_pid_value_unsafe "$rec_host" \
                    && ! _console_pid_value_unsafe "$rec_started_at" \
                    && kill -0 "$rec_pid" 2>/dev/null; then
                    info "소유 프로세스: pid=$rec_pid app_dir=$rec_app_dir"
                    info "opal_home=$rec_opal_home host=$rec_host port=$rec_port started_at=$rec_started_at"
                else
                    warn "stale 레코드: pid=${rec_pid:--} (종료됨이거나 값이 유효하지 않음)"
                fi
            else
                warn "PID 레코드 없음: $record_path — 이 Console은 opal-cli가 소유하지 않습니다"
            fi

            if [[ "$health_ok" -eq 0 ]]; then
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
