---
template: sdlc-v2
---
# TEST-SCENARIO: stockctl 버전 확인 옵션

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: worktree 루트(`.opal-worktrees/task_001`)에서 Python 3(`sys.executable`), pytest. CLI는 `python -m stockctl`로 호출한다.
- import 경로: 모든 subprocess는 `cwd=tmp_path`와 `env={**os.environ, "PYTHONPATH": <프로젝트 루트>}`로 실행한다. 프로젝트 루트는 테스트 파일 기준 `Path(__file__).resolve().parents[1]`이다. S-4만 `PYTHONPATH=tmp_path/pkg`로 대체한다. 따라서 RED 단계의 실패 사유는 `--version` 미지원에 따른 argparse 사용법 오류(exit 2, stderr `stockctl: error:`)여야 하며 `No module named stockctl`(exit 1)이면 환경 오류다.
- 공통 데이터: 시나리오마다 pytest `tmp_path` 빈 디렉토리를 cwd·저장소 위치로 사용한다. S-3의 손상 저장소는 `tmp_path/bad.json`에 `{not json` 문자열을 기록해 만든다.
- 대역 사용과 한계: 사용하지 않음. 모든 CLI 검증은 실제 서브프로세스 실행이다. S-4는 대역이 아니라 실제 패키지 사본을 `PYTHONPATH`로 실행한다.
- 실행 조건: 자동 실행. 자동 테스트는 W-1이 만드는 `tests/test_version.py`에 구현하고, S-5~S-7은 명령·정적 검사로 실행한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-2 | 서브커맨드·다른 인자 없음, cwd=`tmp_path` | `python -m stockctl --version` | exit 0, stdout이 정확히 `stockctl 0.1.0\n`, stderr가 빈 문자열(`usage:`·`required` 문구 없음) | unit(pytest subprocess) | 구현 전 RED |
| S-2 | C-4 | 인자 없음, cwd=`tmp_path` | `python -m stockctl` (인자 없이) | 기존처럼 서브커맨드 필수 오류로 exit 2, stderr에 `usage:` 포함 — `--version` 추가가 필수 서브커맨드 규칙을 약화시키지 않음 | unit(pytest subprocess) | 구현 후 |
| S-3 | AC-4, C-2 | cwd=`tmp_path`(빈 디렉토리), 환경변수 `STOCKCTL_STORE=tmp_path/env.json`; 별도로 `tmp_path/bad.json`에 손상 JSON 존재 | (a) `python -m stockctl --version` (b) `python -m stockctl --store tmp_path/x.json --version` (c) `python -m stockctl --store tmp_path/bad.json --version` | (a)(b)(c) 모두 exit 0·stdout `stockctl 0.1.0\n`; 실행 후 `tmp_path`에 `stock.json`·`env.json`·`x.json`·`*.tmp`가 생기지 않음; `bad.json` 내용이 실행 전과 바이트 동일하고 JSON 파싱 오류가 출력되지 않음 | unit(pytest subprocess) | 구현 전 RED |
| S-4 | AC-3, C-1 | `stockctl` 패키지 디렉토리를 `tmp_path/pkg/stockctl`로 복사하고 사본 `__init__.py`의 `__version__`을 `"9.9.9-test"`로 치환 | `PYTHONPATH=tmp_path/pkg`, cwd=`tmp_path`로 `python -m stockctl --version` | exit 0, stdout이 정확히 `stockctl 9.9.9-test\n` — 출력이 `__version__`을 따름 | unit(pytest subprocess, 실제 패키지 사본) | 구현 전 RED |
| S-5 | AC-5, C-4 | 구현 완료된 worktree | worktree 루트에서 `python -m pytest -q`; `git diff --stat main -- tests/test_basic.py stockctl/store.py stockctl/__init__.py stockctl/__main__.py` | pytest 전체 통과(실패·에러 0, 기존 `tests/test_basic.py` 2건 포함); git diff 출력이 비어 있음(기존 테스트·저장소·버전·진입점 무변경) | 회귀(pytest 전체 + git diff) | 구현 후 |
| S-6 | AC-6 | 구현 완료된 `docs/CLI.md` | `docs/CLI.md` Read 및 `grep -n -- '--version' docs/CLI.md` | 명령 표에 `stockctl --version` 행이 있고, 출력 `stockctl <버전>` 한 줄과 종료 코드 0이 기재됨 | 정적 문서 검사 | 구현 후 |
| S-7 | C-1, C-3, C-5 | 구현 완료된 worktree | `grep -n '0\.1\.0' stockctl/cli.py`; `git diff --name-only main`; 변경 `.py` 파일의 import 목록과 상단 docstring 확인 | `stockctl/cli.py`에 버전 리터럴 없음(C-1); 새 의존성 파일(requirements·pyproject·setup) 추가 없음, 변경 파일 import가 표준 라이브러리·`stockctl`·`pytest`뿐(C-3); `stockctl/cli.py`·`tests/test_version.py` 상단에 module/layer/domain/description/exports @header 존재, 테스트가 `python -m stockctl`로 호출(C-5) | 정적 검사 | 구현 후 |
