---
template: sdlc-v2
---
# PLAN: stockctl 버전 확인 옵션(`--version`) 추가

> 입력: [TASK.md](TASK.md)

## Approach
`stockctl/cli.py`의 `build_parser()`(`stockctl/cli.py:50-66`)에 최상위 옵션 `--version`을 argparse 표준 `action="version"`으로 추가한다. 이 action은 파싱 중 즉시 버전을 stdout에 쓰고 exit 0으로 종료하므로 필수 서브커맨드 검사(`stockctl/cli.py:53`)와 저장소 경로 해석·로드(`stockctl/cli.py:70-72`)에 도달하지 않는다. 버전 문자열은 `stockctl/__init__.py:10`의 `__version__`을 import해 사용한다. 공개 CLI 계약 변경이므로 RED-first를 적용해 테스트 에이전트가 먼저 `tests/test_version.py`로 실패를 관찰한 뒤 BE 워커가 구현하고 `docs/CLI.md`에 옵션을 추가한다.

현재 동작 근거: 구현 전 `python -m stockctl --version`은 `the following arguments are required: command`와 exit 2로 끝난다(2026-09-26 PM 실측). 기존 테스트 `tests/test_basic.py` 2건은 PASS(동일 실측).

## Findings

### 직접 변경
- `stockctl/cli.py` — `build_parser()`에 `--version` 옵션 추가, `__version__` import, @header description 갱신(→ W-2).
- `tests/test_version.py` — `--version` 출력·종료 코드·버전 단일 출처·저장소 비생성을 검증하는 신규 pytest(→ W-1).

### 회귀 확인
- `tests/test_basic.py` — add/list, remove 수량 부족(exit 2) 기존 회귀 테스트가 변경 없이 PASS해야 한다(C-3, AC-4).
- `stockctl/store.py` — `store_path`/`load`/`save`는 변경하지 않으며 `--version` 경로에서 호출되지 않아야 한다(C-2).
- `stockctl/__init__.py` — `__version__` 값의 단일 출처로 읽기만 하고 변경하지 않는다(C-1).

### 문서 갱신
- `docs/CLI.md` — 명령 표에 `stockctl --version` 행(출력 `stockctl <버전>`, 종료 코드 0, 서브커맨드 불필요·저장소 미접근) 추가(→ W-2, AC-5).

### 미확인 가정
없음.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| argparse `action="version"` 사용 | `stockctl --version` → stdout `stockctl 0.1.0\n`, exit 0. 서브커맨드 없이 동작하고 다른 인자 검사보다 먼저 종료 | 표준 라이브러리만 사용(→ `docs/CONVENTIONS.md` §1행). version action은 파싱 중 즉시 `parser.exit()`하므로 `required=True` 서브파서 검사(`stockctl/cli.py:53`)와 `store.store_path` 호출(`stockctl/cli.py:71`)에 도달하지 않음(C-2) |
| 버전 문자열 형식 `f"%(prog)s {__version__}"` | `prog="stockctl"`(`stockctl/cli.py:51`)이므로 출력은 `stockctl <__version__>` | 요구 출력 `stockctl 0.1.0`과 일치하고 버전 리터럴을 CLI에 중복 기재하지 않음(C-1) |
| `__version__`은 `from . import __version__`로 import | 버전 단일 출처는 `stockctl/__init__.py`의 `__version__` | 기존 import 관례 `from . import store`(`stockctl/cli.py:13`)와 동일 |
| 테스트는 subprocess로 `python -m stockctl` 호출 | 신규 테스트도 기존 `run()` 헬퍼 방식(`tests/test_basic.py:14-16`)과 같은 subprocess 호출 | [MUST] `docs/CONVENTIONS.md`: "테스트는 `tests/`에 pytest로 작성하고 CLI는 `python -m stockctl`로 호출한다." |
| AC-2(버전 단일 출처) 검증은 임시 복사본 패키지로 수행 | 테스트가 `tmp_path/"pkg"`에 `stockctl` 패키지를 복사하고 복사본의 `__version__`만 바꿔 `cwd`와 `PYTHONPATH`를 모두 복사본 부모로 두고 실행, 원본 파일은 수정하지 않음 | 저장소 원본 변경 없이 "값을 바꾸면 출력이 바뀐다"를 관찰 가능하게 검증. `python -m`은 cwd를 `sys.path[0]`에 넣어 `PYTHONPATH`보다 우선하므로 cwd 고정이 필수(design-gate i1 evaluator 실측) |
| subprocess의 import 경로는 cwd·`PYTHONPATH`로 명시 | 원본 패키지를 쓰는 테스트가 cwd를 코드 루트 밖으로 옮기면 `PYTHONPATH=<코드 루트>`를 지정 | cwd가 코드 루트가 아니면 `python -m stockctl`이 패키지를 찾지 못함(기존 `tests/test_basic.py:14-16`은 cwd를 바꾸지 않아 해당 없음) |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. `--version` RED 테스트 작성 | opal-test-agent (red mode) | `tests/test_version.py` | 파일 상단 @header(module/layer=test/domain/description/exports) 추가. pytest 테스트 3개 작성: (a) `python -m stockctl --version` stdout == `stockctl 0.1.0\n`, stderr 빈 문자열, returncode 0 — 기대 버전은 `stockctl.__version__`에서 읽어 비교하고 `"0.1.0"` 고정 기대도 함께 단언; (b) `tmp_path / "pkg"`에 `stockctl` 패키지를 `shutil.copytree`로 복사(`ignore=shutil.ignore_patterns("__pycache__")`)하고 복사본 `__init__.py`의 `__version__`을 `"9.9.9"`로 바꾼 뒤 `subprocess.run([sys.executable, "-m", "stockctl", "--version"], cwd=tmp_path / "pkg", env={**os.environ, "PYTHONPATH": str(tmp_path / "pkg")})`로 실행 → stdout == `stockctl 9.9.9\n`, returncode 0 (`cwd`를 복사본 부모로 고정해야 `python -m`이 `sys.path[0]`에 넣는 cwd가 원본 패키지를 가리지 않는다); (c) 빈 `tmp_path / "work"`를 `cwd`로, `--store tmp_path/"work"/"s.json"`, 환경변수 `STOCKCTL_STORE=tmp_path/"work"/"env.json"`, `PYTHONPATH=<코드 루트>`(= `Path(__file__).resolve().parents[1]`, 원본 패키지 import용)로 `python -m stockctl --store ... --version` 실행 → returncode 0이고 실행 후 `tmp_path/"work"` 디렉토리가 비어 있음(`s.json`·`env.json`·`stock.json`·`*.tmp` 모두 없음). 구현 전 실행 시 실패(exit 2)를 관찰해 RED 증거 기록 | 없음 | P1 | AC-1, AC-2, AC-3, C-2, C-4 |
| W-2. `--version` 구현 및 CLI 문서 갱신 | opal-be-agent | `stockctl/cli.py`, `docs/CLI.md` | `stockctl/cli.py`: `from . import __version__` 추가, `build_parser()`에서 `p = argparse.ArgumentParser(prog="stockctl")` 직후 `p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")` 추가, @header description에 `--version` 옵션 언급 추가(exports 불변). add/remove/list 코드와 `main()`은 변경하지 않음. `docs/CLI.md`: 명령 표에 `stockctl --version` 행 추가 — 설명 "설치된 버전을 `stockctl <버전>` 한 줄로 stdout 출력(서브커맨드 불필요, 저장소 미접근)", 종료 코드 `0` | W-1 | P2 | AC-1, AC-2, AC-3, AC-4, AC-5, C-1, C-2, C-3, C-4 |

## Risks
추가 검증이 필요한 위험 없음.

## Release and recovery
- 적용 순서: P1(W-1 RED 테스트, 실패 관찰) → P2(W-2 구현·문서) → 전체 `python -m pytest` 회귀.
- 검증 범위: 결정론 CLI 검증(subprocess pytest)과 기존 회귀 테스트. 외부 연동·설치·배포 없음.
- 실패 시: 변경은 `feat/OP-TASK-001` worktree 브랜치에만 존재하므로 main merge 전 브랜치 폐기로 복구한다.
