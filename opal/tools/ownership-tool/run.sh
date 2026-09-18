#!/bin/bash
# ownership-tool 래퍼 — OPAL .venv python 호출 (run-log-tool run.sh 패턴 복제)
# @header: shell script — 적용 대상 아님 (header-rules.md §적용 대상 확장자 참조)
VENV_PYTHON="$HOME/.opal/.venv/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo '{"ok":false,"command":"ownership-tool","error":"venv_missing","message":"OPAL .venv not found. Run install-mac.sh first."}' >&2
  exit 1
fi

# CLI 표면(ownership_tool/cli.py)은 아직 없다. 현재는 패키지 import 가능 여부만 확인한다.
if ! PYTHONPATH="$SCRIPT_DIR" "$VENV_PYTHON" -c 'import ownership_tool' >/dev/null 2>&1; then
  echo '{"ok":false,"command":"ownership-tool","error":"package_import_failed"}' >&2
  exit 1
fi

echo '{"ok":false,"command":"ownership-tool","error":"not_implemented"}' >&2
exit 1
