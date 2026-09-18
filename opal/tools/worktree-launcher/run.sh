#!/bin/bash
# worktree-launcher 래퍼 — OPAL .venv python 호출 (ownership-tool run.sh 패턴 복제)
# @header: shell script — 적용 대상 아님 (header-rules.md §적용 대상 확장자 참조)
VENV_PYTHON="$HOME/.opal/.venv/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo '{"ok":false,"command":"worktree-launcher","error":"venv_missing","message":"OPAL .venv not found. Run install-mac.sh first."}' >&2
  exit 1
fi

if ! PYTHONPATH="$SCRIPT_DIR" "$VENV_PYTHON" -c 'from worktree_launcher import launcher_core' >/dev/null 2>&1; then
  echo '{"ok":false,"command":"worktree-launcher","error":"package_import_failed"}' >&2
  exit 1
fi

# CLI 표면(--adapter 명시 선택)은 adapter 2종(orca·generic)이 들어오는 후속 Work item이
# 채운다. 현재는 lifecycle 코어만 있으므로 라이브러리 호출로만 사용한다.
echo '{"ok":false,"command":"worktree-launcher","error":"not_implemented"}' >&2
exit 1
