---
template: sdlc-v2
---
# PLAN: stockctl 버전 확인 옵션

> 입력: [TASK.md](TASK.md)

## Approach

최상위 argparse 파서(`stockctl/cli.py:50-53`)에 표준 라이브러리 `argparse`의 `action="version"` 옵션을 추가하고, 버전 문자열은 패키지 `__version__`(`stockctl/__init__.py:10`)을 import해 조립한다. argparse의 version action은 인자 파싱 도중 메시지를 표준 출력에 쓰고 `SystemExit(0)`으로 끝나므로, 필수 서브커맨드 검사(`stockctl/cli.py:53` `required=True`)와 저장소 경로 해석(`stockctl/cli.py:71`) 이전에 종료되어 저장소에 접근하지 않는다. CLI 계약 문서(`docs/CLI.md`)에 옵션 행을 추가한다. RED-first 대상(CLI 공개 계약 추가)이므로 구현 전에 `opal-test-agent`가 공개 인터페이스(`python -m stockctl --version`) 기준 실패 테스트를 새 파일로 먼저 작성한다.

참조 문서:

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | cli.py | `stockctl/cli.py` | 파서 구성·main 흐름 |
| D-2 | 소스 | __init__.py | `stockctl/__init__.py` | `__version__` 단일 출처 |
| D-3 | 설계 | CLI 계약 | `docs/CLI.md` | 명령·종료 코드 계약 |
| D-4 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | 표준 라이브러리·@header·테스트 규칙 |
| D-5 | 소스 | 기존 테스트 | `tests/test_basic.py` | 회귀 기준 |
| D-6 | 외부 | Python argparse | [argparse — action='version'](https://docs.python.org/3/library/argparse.html#action) | version action 동작 |

## Findings

### 직접 변경
- `stockctl/cli.py`: `from . import __version__` 추가, `build_parser()`에서 `--version` 옵션 등록(→ D-1:50-53, D-2:10). 현재 `--version`은 미등록이라 `error: the following arguments are required: command`, exit 2로 실패한다(E1, `python3 -m stockctl --version`, worktree 루트, Python 3.14.3).
- `tests/test_version.py`: 신규 RED 테스트 파일. 기존 회귀 테스트의 subprocess 호출 방식(→ D-5:14-16)을 따른다.

### 회귀 확인
- `tests/test_basic.py`: 변경하지 않고 그대로 통과해야 한다. 기준선 2 passed(E1, `python3 -m pytest -q tests`, worktree 루트).
- `stockctl/store.py`: 변경 없음. `--version` 경로에서 `store_path`·`load`가 호출되지 않아야 한다.

### 문서 갱신
- `docs/CLI.md`: 명령 표에 `stockctl --version` 행(출력 `stockctl <버전>` 한 줄, 종료 코드 0, 저장소 미접근) 추가(→ D-3).

### 미확인 가정
없음.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| argparse `action="version"` 사용 | `p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")`; `prog="stockctl"`이므로 출력은 `stockctl 0.1.0\n`, 표준 출력, exit 0 | 표준 라이브러리만 사용(C-1, → D-4). version action은 stdout 출력 후 `parser.exit()`로 즉시 종료해 서브커맨드 필수 검사·`main()`의 저장소 해석보다 먼저 끝난다(→ D-6, D-1:69-72) |
| 버전 리터럴 중복 금지 | 버전 문자열은 `stockctl/__init__.py`의 `__version__` import로만 얻는다 | C-2 |
| 테스트는 신규 파일 | `tests/test_version.py`를 추가하고 `tests/test_basic.py`는 수정하지 않는다 | C-3 회귀 기준 보존, 기존 파일 @header가 add/remove/list 회귀 전용(→ D-5:6) |
| @header 갱신 | `stockctl/cli.py` @header `description`에 `--version` 언급 추가, 신규 테스트 파일에 @header 작성 | `docs/CONVENTIONS.md`: "모든 소스 파일 상단에 @header(module/layer/domain/description/exports)를 둔다." |

[MUST] `docs/CONVENTIONS.md`: "Python 3 표준 라이브러리만 사용한다."
[MUST] `docs/CONVENTIONS.md`: "테스트는 `tests/`에 pytest로 작성하고 CLI는 `python -m stockctl`로 호출한다."

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. RED 테스트 작성 | opal-test-agent (red mode) | `tests/test_version.py` | @header 포함 신규 pytest 파일. `python -m stockctl --version`을 subprocess로 실행해 stdout이 정확히 `f"stockctl {stockctl.__version__}\n"`, returncode 0, stderr 비어 있음을 검증. 빈 tmp 디렉토리에서 `--store` 미지정·`STOCKCTL_STORE` 미설정으로 실행해 파일이 생기지 않음, 그리고 파싱 불가 내용의 저장소 파일을 `--store`로 지정해도 exit 0이고 파일 내용·mtime이 바뀌지 않음을 검증 | 없음 | P1 | AC-1, C-2 |
| W-2. `--version` 옵션 구현 | opal-be-agent | `stockctl/cli.py` | `from . import __version__` 추가, `build_parser()`의 `--store` 옆에 `p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")` 추가, @header description 갱신. 다른 서브커맨드·`main()` 흐름은 변경하지 않음 | W-1 | P2 | AC-1, AC-2, C-1, C-2, C-3 |
| W-3. CLI 계약 문서 갱신 | opal-be-agent | `docs/CLI.md` | 명령 표에 `` `stockctl --version` `` 행 추가: 설명 "버전 출력(`stockctl <버전>` 한 줄, 저장소 미접근)", 종료 코드 0 | W-1 | P2 | AC-3 |

W-2·W-3은 같은 담당(opal-be-agent)이며 변경 파일이 겹치지 않으므로 P2에서 한 디스패치로 처리한다.

## Risks
추가 검증이 필요한 위험 없음.

## Release and recovery
- 적용 순서: P1(RED 테스트, 실패 관찰) → P2(구현·문서) → TEST 전체 회귀.
- 검증 범위: `python3 -m pytest -q tests` 전체(신규 + 기존 회귀)와 `python3 -m stockctl --version` 실행 관찰. 설치·배포 단계 없음.
- 실패 시: worktree 브랜치 `feat/OP-TASK-001`의 변경을 되돌리면 된다. 허브 `main`은 merge 전까지 영향 없음.
