#!/usr/bin/env bash
# event-loader wrapper — Python 표준 라이브러리 CLI
# @header: shell script — 적용 대상 아님
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/event_loader.py" "$@"
