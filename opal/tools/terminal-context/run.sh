#!/usr/bin/env bash
# terminal-context wrapper — Python standard-library detector
# @header: shell script — code-scan 적용 대상 아님
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/terminal_context.py"
