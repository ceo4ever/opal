---
template: sdlc-v2
---
# TASK: stockctl 버전 확인 옵션

## Problem
운영자가 설치된 stockctl 버전을 확인할 방법이 없다. 현재 CLI는 add/remove/list 서브커맨드만 제공하며(`stockctl/cli.py:50-66`), 패키지에 정의된 버전 문자열(`stockctl/__init__.py:10`)을 명령행에서 조회할 수단이 없다. CLI 계약 문서(`docs/CLI.md:3-7`)에도 버전 조회 옵션이 없다.

## Proposed outcome
운영자가 `stockctl --version`을 실행하면 서브커맨드 없이도 설치된 버전이 표준 출력에 `stockctl 0.1.0` 한 줄로 표시되고 명령이 정상 종료된다. 버전 조회는 재고 저장소 파일에 영향을 주지 않으며, `docs/CLI.md`에 이 옵션이 계약으로 기재된다.

## Affected users and systems
- 사용자: stockctl을 운영하는 운영자
- 시스템: `stockctl` CLI 패키지(`stockctl/`), CLI 계약 문서(`docs/CLI.md`), 테스트(`tests/`)
- 제외: 저장소 포맷(`stockctl/store.py`)과 add/remove/list 동작 변경

## Constraints
- C-1: 버전 문자열은 `stockctl/__init__.py`의 `__version__` 값을 사용한다(하드코딩 중복 금지).
- C-2: `--version` 실행은 저장소 파일을 만들거나 읽지 않는다.
- C-3: 기존 명령(add/remove/list)과 기존 테스트(`tests/test_basic.py`)는 변경 없이 그대로 통과해야 한다.
- C-4: 외부 패키지를 추가하지 않고 Python 3 표준 라이브러리만 사용한다(`docs/CONVENTIONS.md:3`, `.opal/AGENT.md` §금지사항).
- C-5: 신규·수정 소스 파일은 `docs/CONVENTIONS.md`를 따른다(@header 유지, pytest 테스트는 `tests/`에 두고 `python -m stockctl`로 호출).

## Acceptance criteria
- AC-1: `python -m stockctl --version`의 표준 출력이 정확히 `stockctl 0.1.0` 한 줄이다.
- AC-2: `python -m stockctl --version`의 종료 코드가 0이다.
- AC-3: `--version`은 서브커맨드 없이 단독으로 실행해도 오류(사용법 에러, 종료 코드 2)가 나지 않는다.
- AC-4: `__version__` 값을 바꾸면 `--version` 출력도 그 값을 따른다(출력 문자열이 `__version__`에서 유래).
- AC-5: 빈 디렉터리에서 `STOCKCTL_STORE`/`--store`가 가리키는 경로에 파일이 없는 상태로 `--version`을 실행한 뒤에도 저장소 파일이 생성되지 않고, 기존 저장소 파일이 있으면 내용·수정 시각이 바뀌지 않는다.
- AC-6: 기존 `tests/test_basic.py`를 포함한 전체 pytest가 통과한다.
- AC-7: `docs/CLI.md`에 `stockctl --version` 옵션과 출력 형식·종료 코드가 기재된다.
