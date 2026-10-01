---
template: sdlc-v2
---
# PLAN: stockctl 버전 확인 옵션

> 입력: [TASK.md](TASK.md)

## Approach
argparse 최상위 파서에 표준 `version` 액션 옵션 `--version`을 추가한다. 이 액션은 파싱 중 즉시 출력 후 종료하므로 서브커맨드 필수 검사(`stockctl/cli.py:53`)와 저장소 경로 해석·접근(`stockctl/cli.py:70-72`)에 도달하지 않는다. 버전 문자열은 `stockctl/__init__.py:10`의 `__version__`을 import해 단일 출처로 사용한다(C-2). 공개 CLI 계약 변경이므로 RED-first를 적용해 실패 테스트를 먼저 고정하고(`red-first` §1 "API 계약 … 적용"), `docs/CLI.md` 계약 표에 옵션을 추가한다.

code-scan 결과(워크트리 루트, `code-scan scan stockctl` / `depends cli` / `exports __version__`):

| 파일 | layer | domain | exports | depends |
|---|---|---|---|---|
| `stockctl/cli.py` | api | inventory | `main` | 의존·피의존 없음(`depends cli` → none) |
| `stockctl/__init__.py` | util | inventory | `__version__` | — |
| `stockctl/store.py` | data | inventory | `load`, `save`, `store_path` | — |

현재 동작(E1, 워크트리 루트에서 `python3 -m stockctl --version` 실행): `the following arguments are required: command` 오류와 exit 2 — 요구 동작이 미구현임을 확인했다. 기존 회귀 기준(E1, `python3 -m pytest -q tests`): 2 passed.

## Findings

### 직접 변경
- `stockctl/cli.py` — `build_parser()`(`stockctl/cli.py:50-66`)에 `--version` 옵션을 추가하고 `__version__`을 import한다.
- `tests/test_version.py` — `--version` 수용 동작을 고정하는 신규 테스트(RED 대상).

### 회귀 확인
- `tests/test_basic.py` — 기존 add/list/remove 회귀 테스트가 변경 없이 통과해야 한다(AC-2).
- `stockctl/store.py` — `--version` 경로에서 `store_path`/`load`/`save`가 호출되지 않아야 하며 이 파일은 변경하지 않는다(AC-1).
- `stockctl/__init__.py` — 버전 단일 출처로 읽기만 하며 변경하지 않는다(C-2).

### 문서 갱신
- `docs/CLI.md` — CLI 계약 표에 `stockctl --version` 행(출력 형식·저장소 미접근·종료 코드 0)을 추가한다(AC-3).

### 미확인 가정
없음.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| argparse 표준 `action="version"` 사용, `version="%(prog)s " + __version__` | `stockctl --version` → stdout `stockctl 0.1.0\n` 한 줄, exit 0. 서브커맨드 없이 단독 사용 가능 | 파서 `prog="stockctl"`(`stockctl/cli.py:51`)이므로 `%(prog)s`가 `stockctl`로 치환된다. version 액션은 파싱 즉시 `parser.exit()`하므로 필수 서브커맨드 검사(`stockctl/cli.py:53`)보다 먼저 끝난다. 표준 라이브러리만 사용(C-1) |
| 버전 값은 `from . import __version__`로 가져온다 | 버전 리터럴은 `stockctl/__init__.py:10` 한 곳에만 존재 | C-2 단일 출처 |
| 저장소 비접근은 별도 분기 없이 파싱 단계 종료로 보장 | `--version` 실행 시 `store.store_path`·`load`·`save` 미호출, 저장 파일 미생성 | `main()`은 `parse_args` 다음에야 `store.store_path`를 호출한다(`stockctl/cli.py:70-71`) |
| 신규 테스트는 별도 파일 `tests/test_version.py`로 둔다 | 기존 `tests/test_basic.py` 무변경 | 기존 회귀 테스트를 수정하지 않아 AC-2 회귀 판정이 오염되지 않는다. 테스트 형식은 `docs/CONVENTIONS.md`("CLI는 `python -m stockctl`로 호출", @header 필수)를 따른다 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. `--version` RED 테스트 작성 | opal-test-agent (red mode) | `tests/test_version.py` | @header 포함 pytest 파일 신규 작성(기존 `tests/test_basic.py`처럼 `sys.executable -m stockctl` 서브프로세스 호출). (a) 환경변수 `STOCKCTL_STORE`를 `tmp_path/s.json`으로 지정하고 `--version` 단독 실행 → stdout이 `f"stockctl {stockctl.__version__}\n"`과 정확히 일치, returncode 0, 실행 후 `tmp_path`가 비어 있음(파일 미생성). (b) `tmp_path/s.json`에 JSON이 아닌 내용을 미리 써 두고 같은 실행 → returncode 0·같은 stdout이고 파일 내용 불변(저장소 미읽기). 구현 전 실행해 실패를 관찰 | 없음 | P1 | AC-1, C-2 |
| W-2. `--version` 옵션 구현과 CLI 계약 문서 갱신 | opal-be-agent | `stockctl/cli.py`, `docs/CLI.md` | `stockctl/cli.py`: `from . import __version__, store`로 import 조정, `build_parser()`에 `p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")` 추가. 다른 서브커맨드·`main()` 흐름은 변경하지 않는다. `docs/CLI.md`: 계약 표에 `stockctl --version` 행(설명: `stockctl <버전>` 한 줄 출력, 서브커맨드 불필요, 저장소 미접근 / 종료 코드 0) 추가 | W-1 | P2 | AC-1, AC-2, AC-3, C-1, C-2 |

## Risks
추가 검증이 필요한 위험 없음.

## Release and recovery
- 적용 순서: P1(W-1 RED 고정·lock) → P2(W-2 GREEN 구현·문서) → TEST 전체 회귀.
- 검증 범위: 결정론 — `python3 -m pytest -q tests` 전체 통과와 `python -m stockctl --version` 실측 출력·exit·저장 파일 미생성 확인. 외부 연동·설치·배포 없음.
- 실패 시: worktree 브랜치 `feat/OP-TASK-001`에서만 변경하므로 해당 변경을 되돌리면 복구된다. 허브 `main`은 사용자 merge 전까지 영향 없음.
