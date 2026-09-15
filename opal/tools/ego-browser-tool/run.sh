#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${OPAL_EGO_PYTHON_CMD:-python3}"

exec "$PYTHON_BIN" "$SCRIPT_DIR/main.py" "$@"
