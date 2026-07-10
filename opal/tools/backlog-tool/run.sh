#!/bin/bash
# backlog-tool 래퍼 — OPAL .venv python 호출 (state-tool run.sh 패턴 복제 → PLAN §3.1.2)
# @header: shell script — 적용 대상 아님 (header-rules.md §적용 대상 확장자 참조)
VENV_PYTHON="$HOME/.opal/.venv/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo '{"ok":false,"error":"venv_missing","message":"OPAL .venv not found. Run install-mac.sh first."}' >&2
  exit 1
fi

exec "$VENV_PYTHON" "$SCRIPT_DIR/backlog_tool.py" "$@"
