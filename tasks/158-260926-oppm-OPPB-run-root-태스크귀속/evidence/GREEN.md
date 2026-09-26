<!--
@header {
  "module": "oppm-158-green-evidence",
  "layer": "test",
  "domain": "oppb-runtime",
  "description": "OPPB run root 태스크 귀속 구현의 최종 공개 CLI 및 전체 runtime 회귀 결과를 보존한다.",
  "exports": []
}
-->

# GREEN evidence

## 신규 경로·종료·보안 경계

- 명령: `$HOME/.opal/.venv/bin/python -m pytest opal/tools/oppb-runtime-tool/tests/test_oppb_init.py -q`
- 결과: `30 passed in 10.80s`
- 범위: task-local init, hub 신규 미생성, legacy status/resume, cleaned archive, 중단 run 유지,
  symlink 거부, archive lock, 기존 보존본 hash 재검증.

## OPPB runtime 전체 회귀

- 명령: `$HOME/.opal/.venv/bin/python -m pytest opal/tools/oppb-runtime-tool/tests/ -q`
- 결과: `154 passed, 13 subtests passed in 220.45s`

## 비영향 경계

- 명령: `$HOME/.opal/.venv/bin/python -m pytest opal/tools/opal-agent/tests/test_oppl_compat.py -q`
- 결과: `18 passed in 3.90s`
