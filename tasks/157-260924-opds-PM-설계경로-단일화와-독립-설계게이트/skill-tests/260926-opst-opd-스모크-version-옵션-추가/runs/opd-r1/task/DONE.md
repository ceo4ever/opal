# DONE: stockctl 버전 확인 옵션

## 결과

`stockctl --version`을 추가했다. 서브커맨드 없이 단독으로 실행하면 표준 출력에 `stockctl 0.1.0` 한 줄을 쓰고 종료 코드 0으로 끝난다. 버전 문자열은 `stockctl/__init__.py`의 `__version__`에서만 가져오며, `cli.py`에 버전 리터럴은 없다. `--version`은 argparse 파싱 단계에서 끝나므로 저장소 파일을 만들거나 읽지 않는다. 손상된 JSON 저장소를 `--store`로 지정해도 정상 종료하고, 파일 내용과 mtime은 바뀌지 않는다.

유지한 동작: add/remove/list, 인자 없이 실행할 때의 사용법 에러(exit 2), 저장소 로직(`stockctl/store.py`), 기존 테스트(`tests/test_basic.py`)는 수정하지 않았다. `-V` 짧은 옵션은 요구 범위 밖이라 추가하지 않았다.

## 변경 파일

- `stockctl/cli.py` — `from . import __version__`, `--version` 인자 1줄 추가, @header description 갱신
- `docs/CLI.md` — 명령 표에 `stockctl --version` 행 추가
- `tests/test_version.py` — 신규. RED-first로 작성해 구현 전 실패 4건을 확인하고 lock한 뒤 GREEN으로 전환

## 검증

- `python3 -m pytest -q -p no:cacheprovider` → `6 passed`(신규 4 + 기존 2)
- `python3 -m stockctl --version` → `stockctl 0.1.0\n`, exit 0
- `python3 -m stockctl` → exit 2, 사용법 에러 유지
- `__version__`을 `9.9.9`로 바꾼 임시 사본에서 `--version` → `stockctl 9.9.9`(AC-4, 워크트리는 수정하지 않음)
- `git diff main -- tests/test_basic.py stockctl/store.py` → 0줄
- `test-scenario.json`: S-1~S-8 모두 pass(real-usage). S-1~S-4는 RED 확인 후 lock
- 설계 게이트 i1 pass(evaluator 설계 4축 PASS, 시나리오 3축 2/2/2)
- 컨벤션 진단 `GC-CONVENTION-2026-09-26T14-07-24.md`: Critical/High 0, Low 1

## 회고적 학습 후보

없음

## 참고

- 컨벤션 Low(권고): `tests/test_version.py:10`에 사용하지 않는 `import json`이 있다. lock된 RED 테스트라 이번 태스크에서는 수정하지 않았다. 필요하면 후속으로 1줄 삭제한다.
- worktree-tool 경고: `.opal/code-scan.json`의 exclude에 `.opal-worktrees`가 없다. 이번 범위 밖이며, 워크트리 사본이 code-scan 커버리지 지표에 섞일 수 있다.
- 커밋은 하지 않았다. 워크트리 브랜치 `feat/OP-TASK-001`의 변경은 미커밋 상태이며, 커밋과 main merge는 사용자 승인 사항이다.
