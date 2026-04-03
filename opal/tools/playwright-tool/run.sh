#!/bin/bash
# playwright-tool 래퍼 — OPAL .venv python 호출
VENV_PYTHON="$HOME/.opal/.venv/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. venv 존재 확인
if [[ ! -x "$VENV_PYTHON" ]]; then
  echo '{"ok":false,"error":"OPAL .venv not found. Run install-mac.sh first."}' >&2
  exit 1
fi

# 2. playwright 패키지 설치 확인 (import 가능 여부)
if ! "$VENV_PYTHON" -c "import playwright" 2>/dev/null; then
  echo '{"ok":false,"error":"playwright not installed in .venv. Run: ~/.opal/.venv/bin/pip install playwright"}' >&2
  exit 1
fi

exec "$VENV_PYTHON" "$SCRIPT_DIR/main.py" "$@"
