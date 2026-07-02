#!/bin/bash
# git-sync-tool 래퍼 — OPAL .venv python 호출
# @header: shell script — 적용 대상 아님
VENV_PYTHON="$HOME/.opal/.venv/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -x "$VENV_PYTHON" ]]; then
  echo '{"ok":false,"error":"OPAL .venv not found. Run install-mac.sh first."}' >&2
  exit 1
fi
exec "$VENV_PYTHON" "$SCRIPT_DIR/git_sync_tool.py" "$@"
