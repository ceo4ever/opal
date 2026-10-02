---
template: sdlc-v2
---
# TEST-SCENARIO: stockctl 버전 확인 옵션

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 워크트리 루트(`.opal-worktrees/task_001`)에서 로컬 Python 3(실측 3.14.3)과 pytest 실행. 외부 서비스 없음.
- 공통 데이터: pytest `tmp_path` 임시 디렉터리. 저장소 경로는 `--store` 또는 환경변수 `STOCKCTL_STORE`로 `tmp_path` 아래를 가리킨다.
- 대역 사용과 한계: 사용하지 않음. 모든 시나리오는 실제 `python -m stockctl` 프로세스를 subprocess로 실행한다.
- 실행 조건: 자동 실행. 자동 테스트 명령은 `python3 -m pytest -q -p no:cacheprovider`.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-2, AC-3 | 서브커맨드 없음, 저장소 옵션 없음 | `python -m stockctl --version` 실행 | stdout이 정확히 `stockctl 0.1.0\n`, stderr 빈 문자열, 종료 코드 0(사용법 에러 exit 2 아님) | integration — `tests/test_version.py` subprocess | 구현 전 RED |
| S-2 | AC-4, C-1 | 실행 중인 패키지의 `stockctl.__version__` 값을 import로 읽음 | `python -m stockctl --version` 실행 후 stdout을 `f"stockctl {stockctl.__version__}\n"`과 비교하고, `stockctl/cli.py`에 리터럴 `"0.1.0"`이 없는지 확인 | 두 값이 일치하고 `stockctl/cli.py` 안에 버전 리터럴 `0.1.0`이 0건 | integration — `tests/test_version.py` + 소스 grep | 구현 전 RED |
| S-3 | AC-5, C-2 | cwd=`tmp_path`, `STOCKCTL_STORE=tmp_path/s.json`, 해당 파일 없음 | `python -m stockctl --version` 실행 | 종료 코드 0이고 실행 후 `tmp_path/s.json`과 기본 경로 `tmp_path/stock.json` 모두 존재하지 않음 | integration — `tests/test_version.py` subprocess | 구현 전 RED |
| S-4 | AC-5, C-2 | `tmp_path/bad.json`에 유효하지 않은 JSON(`{not json`)을 기록하고 mtime을 기록 | `python -m stockctl --store tmp_path/bad.json --version` 실행 | 종료 코드 0, stdout `stockctl 0.1.0\n`(읽었다면 JSON 파싱 오류로 실패), 파일 내용과 mtime 불변 | integration — `tests/test_version.py` subprocess | 구현 전 RED |
| S-5 | AC-6, C-3 | 구현 완료 상태, `tests/test_basic.py` 무수정 | 전체 pytest 실행 및 `git diff main -- tests/test_basic.py stockctl/store.py` 확인 | 모든 테스트 PASS(기존 2건 포함), 두 파일 diff 0줄 | integration — pytest + git diff | 구현 후 |
| S-6 | AC-3 | `--version`을 서브커맨드와 섞지 않은 부정 경계: 옵션도 서브커맨드도 없음 | `python -m stockctl` 실행 | 기존대로 종료 코드 2와 stderr 사용법 에러 유지(필수 서브커맨드 계약 회귀 없음) | integration — subprocess | 구현 후 |
| S-7 | C-4, C-5 | 구현 완료 상태 | `stockctl/cli.py`·`tests/test_version.py`의 import 목록 검사와 파일 상단 @header 확인, `~/.opal/tools/code-scan/run.sh scan` 실행 | import가 표준 라이브러리와 패키지 내부(`stockctl`)뿐이고 두 파일 모두 @header(module/layer/domain/description/exports) 보유, code-scan이 `test_version.py`를 인식 | 정적 검사 — grep + code-scan | 구현 후 |
| S-8 | AC-7 | 구현 완료 상태 | `docs/CLI.md` 확인 | 명령 표에 `stockctl --version` 행이 있고 출력 형식 `stockctl <버전>` 한 줄과 종료 코드 0이 기재됨 | 문서 검사 — grep | 구현 후 |
