#!/bin/bash
# TS-020 함정 픽스처: --help 호출 시 stdout에 {"ok":false,...} JSON + exit 0
# OPAL 래퍼(cmux-tool)가 --help에 ok:false + exit 0을 반환하는 패턴 재현.
# tool-scan usage 구현은 exit_code(==0)로 성공 판정해야 함 (ok 필드 기준 금지).
echo '{"ok":false,"command":"usage","error":"usage","detail":"cmux-tool help text here","version":"1.0.0"}'
exit 0
