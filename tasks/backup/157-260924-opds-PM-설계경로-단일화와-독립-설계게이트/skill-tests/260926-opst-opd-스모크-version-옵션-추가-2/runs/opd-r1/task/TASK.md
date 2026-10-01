---
template: sdlc-v2
---
# TASK: stockctl 버전 확인 옵션

## Problem
운영자가 설치된 stockctl의 버전을 확인할 방법이 없다. 배포·장애 대응 시 어떤 버전이 동작 중인지 판단할 수 없다.

## Proposed outcome
운영자가 `stockctl --version`을 실행하면 서브커맨드 없이 설치된 버전(`stockctl 0.1.0`)을 한 줄로 확인할 수 있고, 기존 add/remove/list 사용법은 그대로다.

## Affected users and systems
- 사용자: stockctl을 운영하는 운영자
- 포함: `stockctl/cli.py`의 인자 파싱, `docs/CLI.md` CLI 계약, `tests/`의 pytest
- 제외: 저장소 형식(`stockctl/store.py`), 기존 서브커맨드 동작 변경, 패키징·배포

## Constraints
- C-1: 버전 문자열은 `stockctl/__init__.py`의 `__version__` 값을 사용하며 다른 곳에 버전 리터럴을 중복 정의하지 않는다.
- C-2: `--version` 실행은 저장소 파일을 만들거나 읽지 않는다.
- C-3: Python 3 표준 라이브러리만 사용한다(외부 패키지 추가 금지).
- C-4: 기존 명령(add/remove/list)의 동작·출력·종료 코드와 기존 테스트를 변경 없이 유지한다.
- C-5: `docs/CONVENTIONS.md`(소스 @header, pytest, `python -m stockctl` 호출)를 준수한다.

## Acceptance criteria
- AC-1: `python -m stockctl --version`은 표준 출력에 정확히 `stockctl 0.1.0` 한 줄을 출력하고 종료 코드 0으로 끝난다.
- AC-2: `--version`은 서브커맨드 없이 단독으로 실행되며 오류(usage 메시지·비0 종료)를 내지 않는다.
- AC-3: 출력되는 버전이 `stockctl.__version__`에서 온다 — `__version__` 값을 바꾸면 출력이 그 값을 따른다.
- AC-4: `--version` 실행 전후로 저장소 파일(`--store`/`STOCKCTL_STORE`/`stock.json` 경로)이 생성되지 않고, 존재하지 않는 저장소 경로를 지정해도 성공한다.
- AC-5: 기존 테스트(`tests/test_basic.py`)를 포함한 전체 pytest가 통과한다.
- AC-6: `docs/CLI.md`에 `stockctl --version` 옵션의 출력과 종료 코드가 기재된다.
