---
template: sdlc-v2
---
# TASK: stockctl 버전 확인 옵션

## Problem
운영자가 설치된 stockctl의 버전을 확인할 방법이 없다. 현재 CLI는 add/remove/list 서브커맨드만 제공하며(`stockctl/cli.py:50-66`), 패키지에 정의된 버전 문자열(`stockctl/__init__.py:10`)을 사용자에게 노출하는 경로가 없다. 요구서: `/tmp/opal-skill-tester/smoke-version-flag-20261001-094401/opd-r1/REQUEST.md`.

## Proposed outcome
운영자가 `stockctl --version`을 서브커맨드 없이 단독 실행하면 표준 출력에 `stockctl 0.1.0` 한 줄이 출력되고 종료 코드 0으로 끝난다. 출력되는 버전은 패키지의 `__version__` 값과 항상 일치하며, 이 실행은 재고 저장소 파일을 만들거나 읽지 않는다. CLI 계약 문서에 이 옵션이 기재된다. 기존 add/remove/list 동작은 바뀌지 않는다.

## Affected users and systems
- 사용자: stockctl을 운영하는 운영자
- 시스템: stockctl CLI(`stockctl/`), CLI 계약 문서(`docs/CLI.md`), 회귀 테스트(`tests/`)
- 제외: 저장소 포맷(`stockctl/store.py`), 패키징·배포 설정, 버전 번호 변경

## Constraints
- C-1: 외부 패키지를 추가하지 않고 Python 3 표준 라이브러리만 사용한다(`.opal/AGENT.md` §금지사항, `docs/CONVENTIONS.md`).
- C-2: 버전 문자열은 `stockctl/__init__.py`의 `__version__` 값을 단일 출처로 사용하며 다른 위치에 버전 리터럴을 중복 정의하지 않는다(요구서).
- C-3: 기존 add/remove/list 명령의 인자·출력·종료 코드와 기존 테스트(`tests/test_basic.py`)는 변경 없이 그대로 통과해야 한다(요구서, `.opal/AGENT.md` §PM 검토 기준).

## Acceptance criteria
- AC-1: 서브커맨드 없이 `stockctl --version`을 실행하면 표준 출력에 정확히 `stockctl <__version__>`(현재 `stockctl 0.1.0`) 한 줄이 출력되고 종료 코드가 0이며, 이 실행 전후로 재고 저장소 파일이 새로 생기지 않고 기존 저장소 파일도 읽히거나 변경되지 않는다.
- AC-2: 기존 add/remove/list 명령이 이전과 동일한 출력과 종료 코드로 동작하며 기존 테스트가 모두 통과한다.
- AC-3: `docs/CLI.md`에 `--version` 옵션의 사용법·출력 형식·종료 코드가 기재된다.
