#!/bin/bash
# TS-022 픽스처: --help 호출 시 stdout은 비어있고 stderr로만 help 출력
# 일부 외부 CLI가 --help를 stderr로 출력하는 패턴 재현.
# tool-scan usage 구현은 stdout+stderr를 병합하여 usage_text를 채워야 함.
echo 'Usage: stub-cli [options]
  --option1   some option description
  --option2   another option
  --help      show this help text' >&2
exit 0
