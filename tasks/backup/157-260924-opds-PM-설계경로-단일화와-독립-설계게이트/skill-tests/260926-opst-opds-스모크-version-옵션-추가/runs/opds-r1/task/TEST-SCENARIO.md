---
template: sdlc-v2
---
# TEST-SCENARIO: stockctl 버전 확인 옵션(`--version`) 추가

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: worktree 루트(`.opal-worktrees/task_001`)에서 로컬 Python 3 + pytest. CLI는 `python -m stockctl`로 subprocess 호출한다.
- 공통 데이터: 각 시나리오는 pytest `tmp_path` 빈 디렉토리를 사용한다. 저장소 파일은 사전에 만들지 않는다.
- 대역 사용과 한계: 사용하지 않음. S-2는 원본 대신 `tmp_path`에 복사한 실제 `stockctl` 패키지를 `PYTHONPATH`로 실행하며, 복사본은 원본과 동일 코드이고 `__version__` 값만 다르다.
- 실행 조건: 자동 실행.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-2, C-4 | 원본 `stockctl` 패키지(`__version__ = "0.1.0"`), 서브커맨드·`--store` 없음 | `python -m stockctl --version`을 subprocess로 실행하는 `tests/test_version.py`의 출력 테스트 | stdout이 정확히 `stockctl 0.1.0\n`, stderr 빈 문자열, 종료 코드 0 | unit(pytest subprocess), 로컬 | 구현 전 RED |
| S-2 | AC-2, C-1 | `tmp_path/pkg`에 `stockctl` 패키지를 복사하고 복사본 `__version__`을 `"9.9.9"`로 변경 | `cwd=<tmp_path/pkg>`, `PYTHONPATH=<tmp_path/pkg>`로 `python -m stockctl --version` 실행하는 pytest | stdout이 정확히 `stockctl 9.9.9\n`, 종료 코드 0 (출력이 `__version__`을 따르고 CLI에 리터럴이 없음) | unit(pytest subprocess), 로컬 | 구현 전 RED |
| S-3 | AC-3, C-2 | 빈 `tmp_path/work`를 cwd로, `--store <tmp_path/work>/s.json` 지정, 환경변수 `STOCKCTL_STORE=<tmp_path/work>/env.json`, `PYTHONPATH=<코드 루트>` | `python -m stockctl --store <tmp_path/work>/s.json --version` 실행하는 pytest | 종료 코드 0이고 실행 후 `tmp_path/work`가 비어 있음(`s.json`·`env.json`·`stock.json`·`*.tmp` 없음) | unit(pytest subprocess), 로컬 | 구현 전 RED |
| S-4 | AC-4, C-3 | 구현 완료 후 `tests/test_basic.py` 무수정 | `python -m pytest tests/test_basic.py` | 2건 모두 PASS(add/list 출력 `A1\tApple\tMAIN\t5`, remove 수량 부족 exit 2) | unit(pytest), 로컬 | 구현 후 |
| S-5 | C-3 | 구현 완료 후, 서브커맨드 없이 `--version`도 없음 | `python -m stockctl` 실행 | 종료 코드 2, stderr에 `the following arguments are required: command` 포함(서브커맨드 필수 계약 유지) | 수동 명령 실행(자동 셸), 로컬 | 구현 후 |
| S-6 | AC-5 | 구현 완료 후 `docs/CLI.md` | `grep -n -- "--version" docs/CLI.md` 및 해당 행 확인 | 명령 표에 `stockctl --version` 행이 있고 출력 형식 `stockctl <버전>`과 종료 코드 `0`이 기재됨 | 결정론 문서 검사(grep), 로컬 | 구현 후 |
| S-7 | AC-1, AC-4, C-4 | 구현 완료 후 전체 테스트 스위트 | `python -m pytest` | 전체 테스트 PASS(신규 `tests/test_version.py` + 기존 `tests/test_basic.py`), 외부 패키지 추가 없음 | unit(pytest), 로컬 | 구현 후 |
