#!/usr/bin/env bash
set -euo pipefail
# Usage: analyze-log.sh <surface> [--minutes <N>]
#
# 지정 Surface의 최신 로그 파일에서 최근 N분 내 에러·Traceback·structlog 이벤트를 추출한다.
# 인자:
#   <surface>      — be | fe | fe-wire | fe-test | batch
#   --minutes <N>  — 최근 N분 내 라인 분석 (기본 5). 복잡한 날짜 연산 회피를 위해 tail -N 방식 사용.
#
# 출력 섹션:
#   == Recent ERRORs ==         ERROR / CRITICAL 레벨 라인
#   == Tracebacks ==            Traceback / Exception 포함 라인
#   == Structlog events ==      FastAPI structlog JSON 라인의 event 필드만 추출

source "$(dirname "${BASH_SOURCE[0]:-$0}")/_config.sh"

SURFACE="${1:-}"
MINUTES=5

if [ -z "${SURFACE}" ]; then
  echo "Usage: analyze-log.sh <surface> [--minutes <N>]"
  echo "  surface: be | fe | fe-wire | fe-test | batch"
  exit 2
fi

shift || true
while [ $# -gt 0 ]; do
  case "$1" in
    --minutes) MINUTES="${2:-5}"; shift 2 ;;
    *) echo "[WARN] Unknown arg: $1"; shift ;;
  esac
done

# ─── 최신 로그 파일 선택 ─────────────────────────────────────────────────────
LOG_FILE=$(ls -t "${LOG_DIR}/${SURFACE}-"*.log 2>/dev/null | head -1 || echo "")

if [ -z "${LOG_FILE}" ]; then
  echo "[ERROR] No log file found for surface '${SURFACE}' in ${LOG_DIR}"
  echo "  힌트: start-all.sh 또는 open-dev.sh 로 서버를 먼저 기동하세요"
  exit 1
fi

echo "[INFO] Analyzing log: ${LOG_FILE}"
echo "[INFO] Scope: last 500 lines (approximately ${MINUTES} min)"
echo ""

# ─── tail 전략: macOS 호환 (date 연산 회피) ──────────────────────────────────
# N분 분량 추정이 어려우므로 tail -500으로 폴백 — 상황에 따라 --minutes 값 조정
LINES=500

# ─── == Recent ERRORs == ────────────────────────────────────────────────────
echo "== Recent ERRORs =="
tail -n "${LINES}" "${LOG_FILE}" | grep -E "(ERROR|CRITICAL)" || echo "  (없음)"
echo ""

# ─── == Tracebacks == ───────────────────────────────────────────────────────
echo "== Tracebacks =="
tail -n "${LINES}" "${LOG_FILE}" | grep -E "(Traceback|Exception)" || echo "  (없음)"
echo ""

# ─── == Structlog events == ─────────────────────────────────────────────────
echo "== Structlog events =="
# FastAPI structlog JSON 라인: '{' 로 시작하는 줄에서 'event' 필드 추출
tail -n "${LINES}" "${LOG_FILE}" | python3 -c "
import json, sys
events = []
for line in sys.stdin:
    line = line.strip()
    if line.startswith('{'):
        try:
            obj = json.loads(line)
            event = obj.get('event', '')
            level = obj.get('level', '')
            ts = obj.get('timestamp', obj.get('ts', ''))
            if event:
                events.append(f'[{level}] {ts} {event}')
        except (json.JSONDecodeError, ValueError):
            pass
if events:
    for e in events:
        print(e)
else:
    print('  (JSON structlog 라인 없음)')
" || echo "  (python3 파싱 오류)"
