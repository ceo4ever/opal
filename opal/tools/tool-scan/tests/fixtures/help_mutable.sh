#!/bin/bash
# TS-021 픽스처: 환경변수로 --help 출력 변경 가능
# TOOL_SCAN_HELP_VERSION 환경변수를 읽어 출력을 다르게 반환.
# tool-scan usage가 정적 캐시를 사용하지 않음을 증명: 두 번 호출 시 환경변수 변경이 반영되어야 함.
VERSION="${TOOL_SCAN_HELP_VERSION:-v1}"
echo "Usage: mutable-tool [options] (${VERSION})"
echo "  This is help text for version: ${VERSION}"
exit 0
