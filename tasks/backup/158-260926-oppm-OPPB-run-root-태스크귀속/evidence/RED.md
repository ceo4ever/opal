<!--
@header {
  "module": "oppm-158-red-evidence",
  "layer": "test",
  "domain": "oppb-runtime",
  "description": "OPPB run root 태스크 귀속 공개 CLI 계약의 구현 전 RED 실행 결과와 실패 의미를 보존한다.",
  "exports": []
}
-->

# RED evidence

- 명령: `$HOME/.opal/.venv/bin/python -m pytest opal/tools/oppb-runtime-tool/tests/test_oppb_init.py -q`
- 최초 결과: `9 failed, 12 passed in 2.36s`
- 실패 이유: 공개 CLI가 `--task-root`와 `finalize-run`을 아직 지원하지 않았고 신규 실행도 허브 `.opal-runs/`에 생성했다.
- 의미: 구현 전에 신규 태스크 귀속·legacy 호환·종료 보존 계약이 기존 코드에서 충족되지 않음을 확인했다.
