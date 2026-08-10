#!/bin/bash
#
# scripts/install/linux.sh — Linux 설치 진입점 (install-mac.sh wrapper)
#
# 역할: install.sh 및 opal-cli 가 호출할 수 있는 Linux 전용 설치 진입점.
#       현행 scripts/install-mac.sh 를 exec 로 위임한다.
#       install-mac.sh 내부는 OS 감지를 통해 Linux 호환 분기(Playwright 캐시 경로)를
#       처리하므로 동일 스크립트를 안전하게 재사용 가능하다.
#       Python 하한 게이트는 위임 대상 install-mac.sh 의 ensure_python() 에 있다.
#       Linux는 자동 설치를 수행하지 않고 안내만 출력한다(install_platform_python() Linux 분기).
#       후속: install-core.sh로 리네이밍 검토 (v0.6 로드맵).
#
# Usage:
#   bash scripts/install/linux.sh [args...]
#
# 근거:
#   tasks/006-260520-opp-install-linux/PLAN.md §의사결정 M-1 (전략 A — 단순 위임)
#   tasks/006-260520-opp-install-linux/PLAN.md §1 install-mac.sh 함수별 호환성 분석
#
# 변경이력:
#   v1.0 2026-05-20: 신규 작성 — Linux one-liner 진입점 (006)
#   v1.1 2026-05-24: Codex CLI 통합은 install-mac.sh 위임 경로로 자동 상속 (별도 코드 변경 없음) (009)
#   v1.2 2026-08-10: Python 하한 게이트 소재 명시 주석 추가 — 게이트는 위임 대상 install-mac.sh 의 ensure_python() 에 있으며 Linux는 자동 설치 없이 안내만 수행(동작 무변경, 주석 전용) (087)
#

set -euo pipefail

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

exec bash "${INSTALLER}" "$@"
