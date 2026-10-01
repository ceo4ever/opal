---
template: sdlc-v2
---
# TASK: stockctl 버전 확인 옵션

## Problem
운영자가 설치된 stockctl 버전을 확인할 방법이 없다(요구서 `/tmp/opal-skill-tester/smoke-version-flag-20261001-094401/opd-r2/REQUEST.md`). 현재 CLI는 add/remove/list 서브커맨드만 제공하며 서브커맨드 없이 실행하면 오류가 난다(`stockctl/cli.py:53` `required=True`).

## Proposed outcome
- `stockctl --version`은 표준 출력에 `stockctl 0.1.0` 한 줄을 출력하고 exit 0으로 끝난다. 버전 문자열은 `stockctl/__init__.py`의 `__version__` 값을 사용한다.
- `--version`은 서브커맨드 없이 단독으로 쓸 수 있으며, 저장소 파일을 만들거나 읽지 않는다.
- 기존 명령(add/remove/list)과 기존 테스트는 그대로 동작한다.
- `docs/CLI.md`에 `--version` 옵션이 기재된다.

## Affected users and systems
- 사용자: stockctl을 운영하는 운영자.
- 시스템: stockctl CLI(`stockctl/`), 테스트(`tests/`), CLI 계약 문서(`docs/CLI.md`).
- 제외: 저장소 형식(`stockctl/store.py`의 저장 구조), 버전 값 자체의 변경.

## Constraints
- C-1: 프로젝트 강제 계약(`.opal/AGENT.md` §금지사항 — 표준 라이브러리만 사용, `docs/CONVENTIONS.md`)을 준수한다.
- C-2: 버전 문자열은 `stockctl/__init__.py`의 `__version__` 단일 출처에서 가져오며, 다른 위치에 버전 리터럴을 중복 기재하지 않는다.

## Acceptance criteria
- AC-1: 서브커맨드 없이 `stockctl --version`을 실행하면 표준 출력이 정확히 `stockctl <__version__>` 한 줄(현재 `stockctl 0.1.0`)이고 종료 코드가 0이며, 실행 전후로 저장소 파일이 생성되거나 읽히지 않는다.
- AC-2: 기존 add/remove/list 명령의 출력·종료 코드가 변경 전과 동일하고 기존 테스트가 모두 통과한다.
- AC-3: `docs/CLI.md`의 CLI 계약에 `--version` 옵션의 사용법·출력·종료 코드가 기재된다.
