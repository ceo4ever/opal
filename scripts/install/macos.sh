#!/bin/bash
#
# scripts/install/macos.sh — macOS 설치 진입점 (install-mac.sh wrapper)
#
# 역할: install.sh 및 opal-cli 가 호출할 수 있는 macOS 전용 설치 진입점.
#       현행 scripts/install-mac.sh 를 exec 로 위임하여 동일 동작을 보장한다.
#       함수 그룹별 분해는 후속 리팩 태스크로 분리 예정 (PLAN §3.1.4).
#
# Usage:
#   bash scripts/install/macos.sh [args...]
#   bash scripts/install/macos.sh           # 대화형 메뉴 표시
#
# 근거:
#   tasks/139-260508-opp-distribute-and-getstarted/PLAN.md §4.2 Step 1
#   tasks/139-260508-opp-distribute-and-getstarted/PLAN.md §3.1.4 배치/마이그레이션
#   tasks/139-260508-opp-distribute-and-getstarted/ANALYSIS.md §1.3 install-mac.sh 핵심 호출 그래프
#
# 변경이력:
#   v1.0 2026-05-08 15:00: 신규 작성 — install-mac.sh wrapper 진입점 신설 (139)
#

set -euo pipefail

# ─── Resolve script location ──────────────────────────────
# exec 위임 전 scripts/install-mac.sh 의 절대 경로를 결정한다.
# 이 스크립트는 어느 cwd에서 호출되든 동작해야 한다.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
INSTALLER="${REPO_ROOT}/scripts/install-mac.sh"

if [[ ! -f "${INSTALLER}" ]]; then
    echo "[ERROR] install-mac.sh 를 찾을 수 없습니다: ${INSTALLER}" >&2
    echo "        프로젝트 루트에서 실행하거나 REPO_ROOT 환경변수를 설정하세요." >&2
    exit 1
fi

if [[ ! -x "${INSTALLER}" ]]; then
    chmod +x "${INSTALLER}"
fi

# install-mac.sh 에 모든 인자를 전달하여 exec 한다.
# exec 를 사용하므로 이 프로세스가 install-mac.sh 프로세스로 교체된다.
exec bash "${INSTALLER}" "$@"
