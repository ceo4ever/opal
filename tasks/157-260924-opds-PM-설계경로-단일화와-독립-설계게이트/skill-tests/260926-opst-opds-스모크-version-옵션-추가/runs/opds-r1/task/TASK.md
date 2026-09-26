---
template: sdlc-v2
---
# TASK: stockctl 버전 확인 옵션(`--version`) 추가

## Problem
운영자가 설치된 stockctl 버전을 확인할 방법이 없다. 버전 문자열은 `stockctl/__init__.py:10`의 `__version__ = "0.1.0"`에만 있고, CLI 파서(`stockctl/cli.py:50-66`)는 서브커맨드를 필수(`required=True`, `stockctl/cli.py:53`)로 요구하며 버전 출력 옵션이 없다. CLI 계약 문서(`docs/CLI.md:3-7`)에도 버전 확인 방법이 없다.

## Proposed outcome
운영자가 `stockctl --version`을 서브커맨드 없이 실행하면 표준 출력에 `stockctl 0.1.0` 한 줄이 나오고 exit 0으로 끝난다. 출력 버전은 `stockctl/__init__.py`의 `__version__`을 따른다. `docs/CLI.md`에서 이 옵션을 확인할 수 있다.

## Affected users and systems
- 사용자: stockctl을 운영하는 운영자.
- 시스템: `stockctl` CLI 진입점(`stockctl/cli.py`), CLI 계약 문서(`docs/CLI.md`), 회귀 테스트(`tests/`).
- 제외: 저장소 형식(`stockctl/store.py`)과 add/remove/list의 동작·출력·종료 코드 변경.

## Constraints
- C-1: 버전 문자열은 `stockctl/__init__.py`의 `__version__` 값을 사용하며 CLI 코드에 버전 리터럴을 중복 기재하지 않는다.
- C-2: `--version` 실행은 저장소 파일을 만들거나 읽지 않는다.
- C-3: 기존 명령(add/remove/list)과 기존 테스트(`tests/test_basic.py`)는 그대로 동작해야 한다.
- C-4: `docs/CONVENTIONS.md`를 준수한다 — Python 3 표준 라이브러리만 사용하고, 테스트는 `tests/`에 pytest로 작성하며 CLI는 `python -m stockctl`로 호출한다.

## Acceptance criteria
- AC-1: `python -m stockctl --version`의 stdout이 정확히 `stockctl 0.1.0\n` 한 줄이고 종료 코드가 0이다.
- AC-2: `--version`은 서브커맨드 없이 단독으로 실행되며 `stockctl/__init__.py`의 `__version__` 값을 바꾸면 출력도 그 값으로 바뀐다.
- AC-3: 빈 디렉토리에서 `--store` 경로를 지정해 `--version`을 실행한 뒤 해당 저장소 파일이 생성되지 않는다.
- AC-4: 기존 add/remove/list 회귀 테스트(`tests/test_basic.py`)가 모두 통과한다.
- AC-5: `docs/CLI.md`에 `stockctl --version` 옵션과 출력 형식(`stockctl <버전>`)·종료 코드 0이 기재되어 있다.
