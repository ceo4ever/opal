---
template: sdlc-v2
---
# PLAN: stockctl 버전 확인 옵션

> 입력: [TASK.md](TASK.md)

## 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | cli.py | `stockctl/cli.py` | 파서 구성과 `main` 흐름 |
| D-2 | 소스 | __init__.py | `stockctl/__init__.py` | `__version__` 정의 |
| D-3 | 설계 | CLI.md | `docs/CLI.md` | CLI 명령 계약 |
| D-4 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 표준 라이브러리·@header·pytest 규칙 |
| D-5 | 소스 | test_basic.py | `tests/test_basic.py` | 기존 회귀 테스트와 호출 방식 |
| D-6 | 외부 | Python argparse | [argparse — action='version'](https://docs.python.org/3/library/argparse.html#action) | `version` 액션 동작 |

## code-scan 결과

`~/.opal/tools/code-scan/run.sh scan`·`exports "version|main"`·`depends cli` 실행 결과(2026-09-26, 워크트리 기준).

| 파일 | domain | layer | exports | depends |
|---|---|---|---|---|
| `stockctl/cli.py` | inventory | api | `main` | (none — @header에 선언 없음) |
| `stockctl/__init__.py` | inventory | util | `__version__` | (none) |
| `stockctl/__main__.py` | inventory | api | (없음) | (none) |
| `stockctl/store.py` | inventory | data | `load`, `save`, `store_path` | (none) |
| `tests/test_basic.py` | inventory | test | (없음) | (none) |

변경 대상 `stockctl/cli.py`(layer api, exports `main`)는 `__version__`(layer util)을 새로 import한다. exports 목록은 바뀌지 않는다.

## Approach
표준 라이브러리 `argparse`의 `action="version"`으로 최상위 파서에 `--version`을 추가한다. 버전 문자열은 `stockctl/__init__.py`의 `__version__`을 import해 `f"stockctl {__version__}"`으로 만든다(→ D-2:10). argparse는 `--version`을 파싱하는 즉시 문자열을 표준 출력에 쓰고 `parser.exit()`(종료 코드 0)를 호출하므로, 필수 서브커맨드 검사(→ D-1:53)와 `store.store_path` 호출(→ D-1:70-72) 이전에 끝난다. 따라서 저장소 파일을 만들거나 읽지 않는다. 기존 add/remove/list 코드는 건드리지 않는다. 공개 CLI 계약 변경이므로 RED-first를 적용해 테스트를 먼저 고정한다.

## Findings

### 직접 변경
- `stockctl/cli.py`: `build_parser()`(→ D-1:50-66)에 `--version` 인자를 추가하고, `from . import __version__` import를 더한다. @header `description`에 `--version` 옵션을 반영한다(→ D-4:4).
- `tests/test_version.py`: `--version` 계약(AC-1~AC-5)을 검증하는 신규 pytest 파일. 기존 회귀 테스트(D-5)와 같은 `python -m stockctl` subprocess 호출 방식을 따른다(→ D-5:14-16, D-4:7).

### 회귀 확인
- `tests/test_basic.py`: add/list, remove 수량 부족(exit 2) 기존 테스트가 변경 없이 통과해야 한다(C-3). 기준선: 변경 전 `python3 -m pytest -q` → `2 passed`(PM 실측, 2026-09-26 13:55).
- `stockctl/store.py`: 저장소 로드·저장 로직은 변경하지 않는다. `--version` 경로가 `store.load`/`store.save`를 호출하지 않는지만 확인한다.
- `stockctl/__init__.py`: `__version__` 정의만 읽으며 변경하지 않는다(C-1).

### 문서 갱신
- `docs/CLI.md`: 명령 표에 `stockctl --version` 행을 추가한다(출력 `stockctl <__version__>` 한 줄, 종료 코드 0, 저장소 미접근).

### 미확인 가정
없음.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| argparse `action="version"` 사용 | `stockctl --version` → stdout `stockctl 0.1.0\n`, exit 0. 서브커맨드 없이 단독 허용 | Python 3.4+에서 version 액션은 stdout으로 출력 후 즉시 종료(→ D-6). 현재 런타임 Python 3.14.3에서 서브커맨드 `required=True`와 함께 exit 0 실측. 외부 패키지 불필요(C-4, → D-4:3) |
| 버전 문자열 출처 | `f"stockctl {__version__}"` — `stockctl/__init__.py`의 `__version__` 단일 출처 | C-1. 하드코딩 중복 제거 |
| 저장소 미접근 | `--version`은 `parse_args` 단계에서 종료하므로 `store.store_path`/`load`/`save`에 도달하지 않음 | `main`은 `parse_args` 이후에만 저장소 경로를 해석(→ D-1:69-72). C-2 |
| 테스트 파일 분리 | 신규 `tests/test_version.py`, `tests/test_basic.py`는 수정하지 않음 | C-3 기존 테스트 불변 |
| 짧은 옵션 `-V` 미추가 | `--version`만 제공 | 요구서가 `--version`만 요구. 범위 최소화(PRINCIPLES §2) |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. `--version` RED 테스트 작성 | opal-test-agent (red mode, 파일 소유) | `tests/test_version.py` | @header를 가진 pytest 파일 생성. subprocess로 `sys.executable -m stockctl --version` 실행: (a) stdout == `"stockctl 0.1.0\n"`, stderr 비어 있음, (b) returncode 0, (c) 출력이 `stockctl.__version__`과 일치(`f"stockctl {stockctl.__version__}\n"`), (d) `tmp_path`를 cwd로 하고 `STOCKCTL_STORE`를 `tmp_path/s.json`으로 지정했을 때 실행 후 파일 미생성, (e) 손상된 JSON이 담긴 저장소 파일을 `--store`로 지정해도 exit 0이며 파일 내용·mtime 불변(읽기 없음 증거). 구현 전 실행 시 실패(RED) 확인 | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, AC-5, C-2, C-5 |
| W-2. `--version` 옵션 구현 | opal-be-agent (파일 소유) | `stockctl/cli.py` | `from . import __version__` 추가. `build_parser()`에서 `p.add_argument("--store", ...)` 다음 줄에 `p.add_argument("--version", action="version", version=f"stockctl {__version__}")` 추가. @header `description`을 "stockctl 명령행 인터페이스. add/remove/list 서브커맨드로 단일 위치 재고를 관리하고 --version으로 버전을 출력한다."로 갱신. 그 외 함수 변경 금지 | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-6, C-1, C-3, C-4, C-5 |
| W-3. CLI 계약 문서 갱신 | opal-be-agent (파일 소유) | `docs/CLI.md` | 명령 표 첫 행 앞에 `stockctl --version` 행 추가: 설명 "버전 출력 (`stockctl <__version__>` 한 줄, 저장소 미접근)", 종료 코드 `0`. 기존 행·저장소 경로 문장은 유지 | W-1 | P2 | AC-7 |

## Risks
추가 검증이 필요한 위험 없음.

## Release and recovery
- 적용 순서: P1(W-1 RED 테스트 작성·실패 관찰·lock) → P2(W-2·W-3, 동일 워커가 파일 겹침 없이 수행) → TEST 단계 전체 pytest.
- 검증 범위: 결정론 — `python3 -m pytest -q`(신규 `tests/test_version.py` + 기존 `tests/test_basic.py`), `python3 -m stockctl --version` 실측 출력·exit. 외부 연동·설치·배포 없음.
- 실패 시: 배포가 없으므로 worktree 브랜치 `feat/OP-TASK-001`에서 보정 커밋으로 복구한다. main 반영은 사용자 merge 승인 뒤에만.
