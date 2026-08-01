#!/bin/bash
# code-scan 래퍼 — Node.js 호출
# @header: shell script — 적용 대상 아님 (header-rules.md §적용 대상 확장자 참조)
NODE_BIN="${OPAL_NODE_BIN:-node}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v "$NODE_BIN" >/dev/null 2>&1; then
  echo '{"ok":false,"error":"node_missing","detail":"Node.js not found. Install Node 18+."}'
  exit 1
fi

exec "$NODE_BIN" "$SCRIPT_DIR/code-scan.js" "$@"
