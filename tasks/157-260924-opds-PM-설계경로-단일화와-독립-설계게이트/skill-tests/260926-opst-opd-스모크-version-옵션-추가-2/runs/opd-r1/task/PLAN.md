---
template: sdlc-v2
---
# PLAN: stockctl 버전 확인 옵션

> 입력: [TASK.md](TASK.md)

## 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | cli.py | `stockctl/cli.py` | 인자 파서 구성과 main 흐름 |
| D-2 | 소스 | __init__.py | `stockctl/__init__.py` | 버전 문자열 SSOT |
| D-3 | 소스 | store.py | `stockctl/store.py` | 저장소 경로·읽기 경계 |
| D-4 | 설계 | CLI.md | `docs/CLI.md` | CLI 명령 계약 |
| D-5 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 헤더·테스트·표준 라이브러리 규칙 |
| D-6 | 소스 | test_basic.py | `tests/test_basic.py` | 기존 회귀 테스트 |
| D-7 | 외부 | Python argparse | [argparse — action='version'](https://docs.python.org/3/library/argparse.html#action) | version action 동작 |

## Approach

최상위 파서에 `--version` 옵션을 추가해 서브커맨드 없이 버전을 출력하고 종료하게 한다. 파서는 `build_parser()`에서 만들어지고(→ D-1:50-66), `main()`은 `parse_args` 뒤에야 `store.store_path`를 호출하고 서브커맨드 함수를 실행한다(→ D-1:69-72). 따라서 파싱 도중 종료하는 argparse `version` action을 쓰면 저장소 경로 해석·로드가 일어나지 않는다. 버전 문자열은 `stockctl/__init__.py`의 `__version__`(→ D-2:10)을 import해 조립한다.

실측(E1, 스코프: 격리된 argparse 파서, 명령 `python3 -c` 로 `--version` 액션 + `required=True` 서브파서 구성 후 `parse_args(["--version"])`): stdout `x 1\n`, exit 0, 서브커맨드 required 오류 없음. 즉 version action은 required 서브커맨드 검사보다 먼저 종료한다.

범위: 인자 파서, CLI 계약 문서, 신규 테스트. 저장소 모듈·기존 서브커맨드·기존 테스트는 바꾸지 않는다.

## Findings

### 직접 변경
- `stockctl/cli.py`: `build_parser()`에 `--version`(argparse `action="version"`, `version=f"stockctl {__version__}"`)을 추가하고 `from . import __version__`로 버전을 가져온다. @header `description`에 `--version` 옵션을 반영한다(→ D-1:1-9, D-5).
- `tests/test_version.py`: 신규 pytest. `python -m stockctl --version`의 출력·종료 코드·저장소 무접근·버전 출처를 공개 인터페이스(subprocess)로 검증한다(→ D-5).

### 회귀 확인
- `tests/test_basic.py`: add/list·remove 부족 수량 동작을 그대로 통과해야 한다(→ D-6).
- `stockctl/store.py`: 변경하지 않으며 `--version` 경로에서 호출되지 않아야 한다(→ D-3:15-23).
- `stockctl/__init__.py`: 읽기 전용 버전 출처. 값·형식을 바꾸지 않는다(→ D-2:10).
- `stockctl/__main__.py`: `sys.exit(main())` 진입점이 argparse의 SystemExit(0)을 그대로 종료 코드로 전달한다.

### 문서 갱신
- `docs/CLI.md`: 명령 표에 `stockctl --version` 행(출력 `stockctl <버전>` 한 줄, 종료 코드 0, 서브커맨드 불필요, 저장소 미접근)을 추가한다(→ D-4).

### 미확인 가정
없음.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| argparse 내장 `action="version"` 사용 | `stockctl --version` → stdout `stockctl 0.1.0\n`, exit 0, stderr 없음 | 파싱 중 stdout 출력 후 exit 0으로 끝나며 required 서브커맨드 검사 전에 종료함을 실측(Approach E1). 표준 라이브러리만 사용(→ D-5). design-decision detail 기록 |
| 버전 문자열은 `__version__` import로만 조립 | `stockctl/cli.py`에 버전 리터럴 없음. `__version__` 변경 시 출력이 따라 바뀜 | TASK C-1, AC-3. 버전 SSOT는 `__version__`(→ D-2:10) |
| 저장소 무접근 | `--version`은 `--store`·`STOCKCTL_STORE`·`stock.json`을 생성·읽지 않음 | `store_path`·`load`는 `parse_args` 이후에만 호출됨(→ D-1:69-72). TASK C-2 |
| 테스트 subprocess의 import 경로 고정 | `tests/test_version.py`는 프로젝트 루트를 `Path(__file__).resolve().parents[1]`로 구하고, 모든 subprocess를 `env={**os.environ, "PYTHONPATH": <프로젝트 루트>}`로 실행한다(cwd는 `tmp_path`). S-4만 `PYTHONPATH=<tmp_path/pkg>`로 대체한다. 절대경로를 하드코딩하지 않는다 | cwd가 `tmp_path`이면 `python -m stockctl`이 패키지를 찾지 못함을 실측(E1, 스코프: `/tmp` cwd, 명령 `python3 -m stockctl --version` → `No module named stockctl`, exit 1). 경로를 고정해야 RED 실패 사유가 `--version` 부재로 한정되고, 저장소 무접근 검증용 빈 cwd를 유지할 수 있다. 설계 게이트 i1 지적 반영 |
| 신규 테스트는 별도 파일 | `tests/test_basic.py` 무변경, `tests/test_version.py` 신설 | TASK C-4(기존 테스트 변경 금지). [MUST] `docs/CONVENTIONS.md`: "테스트는 `tests/`에 pytest로 작성하고 CLI는 `python -m stockctl`로 호출한다." |
| 신규 소스에도 @header | `tests/test_version.py` 상단에 module/layer/domain/description/exports | [MUST] `docs/CONVENTIONS.md`: "모든 소스 파일 상단에 @header(module/layer/domain/description/exports)를 둔다." |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. RED 테스트 작성 | opal-test-agent (red mode) | `tests/test_version.py` | @header 포함 신규 pytest. TEST-SCENARIO S-1~S-4를 subprocess(`[sys.executable, "-m", "stockctl", ...]`, `cwd=tmp_path`, `env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}` — S-4만 `PYTHONPATH=str(tmp_path/"pkg")`)로 구현: 정확한 stdout·exit 0·stderr 비어 있음, 서브커맨드 없는 단독 실행, 저장소 파일 미생성·손상 JSON 저장소 미읽기, 패키지 사본의 `__version__` 변경 시 출력 추종. 구현 전 실패를 관찰해 RED 증거로 기록 — RED 실패 사유가 argparse 사용법 오류(exit 2, stderr `stockctl: error: the following arguments are required: command` — 구현 전 실측)이고 `No module named stockctl`(exit 1)이 아님을 확인 | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, C-1, C-2, C-5 |
| W-2. `--version` 구현과 CLI 계약 갱신 | opal-be-agent | `stockctl/cli.py`, `docs/CLI.md` | `cli.py`: `from . import __version__` 추가, `build_parser()`의 `p = argparse.ArgumentParser(prog="stockctl")` 직후 `p.add_argument("--version", action="version", version=f"stockctl {__version__}")` 추가, @header description에 `--version` 반영. 서브커맨드·`main()`·`--store` 로직은 변경하지 않음. `CLI.md`: 명령 표에 `stockctl --version` 행 추가(출력 `stockctl <__version__>` 한 줄, 종료 코드 0), 저장소 미접근 한 줄 명시. W-1 테스트는 수정하지 않음 | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, C-1, C-2, C-3, C-4, C-5 |

## Risks

추가 검증이 필요한 위험 없음.

## Release and recovery

- 적용 순서: P1 W-1(RED 테스트, 실패 관찰) → scenario-lock → P2 W-2(GREEN 구현·문서) → TEST 전체 pytest.
- 검증 범위: 결정론 — `python -m pytest -q` 전체(신규 + 기존 회귀), `python -m stockctl --version` 실제 실행 출력. 실제 연동·배포 대상 없음.
- 실측 경계: 해당 없음(시간·품질 수치 목표 없음).
- 실패 시: 패키징·배포가 없는 로컬 CLI 변경이므로 worktree 브랜치 `feat/OP-TASK-001`의 해당 커밋을 되돌리면 복구된다. main 반영은 사용자 merge 승인 이후다.
