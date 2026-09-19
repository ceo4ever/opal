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

# CLI 표면(--adapter 명시 선택)은 worktree_launcher.cli가 소유한다 — 이 래퍼는 가드 2종
# 뒤에서 인자를 그대로 넘기고 종료 코드를 그대로 돌려준다.
PYTHONPATH="$SCRIPT_DIR" "$VENV_PYTHON" -m worktree_launcher.cli "$@"
