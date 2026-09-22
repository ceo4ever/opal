#!/bin/bash
# state-tool 병렬 테스트 래퍼 — 각 test_*.py를 격리된 pytest 프로세스로 실행
# @header: shell script — 적용 대상 아님 (header-rules.md §적용 대상 확장자 참조)
set -eu

VENV_PYTHON="$HOME/.opal/.venv/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo 'OPAL .venv not found. Run install-mac.sh first.' >&2
  exit 1
fi

exec "$VENV_PYTHON" "$SCRIPT_DIR/tests/parallel_runner.py" "$@"
