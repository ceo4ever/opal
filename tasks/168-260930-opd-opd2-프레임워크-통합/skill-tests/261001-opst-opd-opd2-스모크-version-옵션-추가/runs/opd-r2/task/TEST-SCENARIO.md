---
template: sdlc-v2
---
# TEST-SCENARIO: stockctl 버전 확인 옵션

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 워크트리 루트(`.opal-worktrees/task_001`)를 cwd로 하는 로컬 Python 3(표준 라이브러리) + pytest. CLI는 `python3 -m stockctl`로 호출한다(`docs/CONVENTIONS.md`).
- 공통 데이터: 각 시나리오는 pytest `tmp_path` 또는 `mktemp -d` 임시 디렉터리를 저장소 위치로 쓰며, 기본 저장 파일(`stock.json`)이 cwd에 생기지 않도록 `--store` 또는 `STOCKCTL_STORE`를 임시 디렉터리 안으로 지정한다.
- 대역 사용과 한계: 사용하지 않음. 모든 행동 시나리오는 실제 CLI 서브프로세스를 실행한다.
- 실행 조건: 자동 실행. 사람 협업 없음.

## Scenarios

| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | contract | AC-1, C-2 | 빈 임시 디렉터리 D, 환경변수 `STOCKCTL_STORE=D/s.json` | 서브커맨드 없이 `python3 -m stockctl --version` 실행 | stdout이 정확히 `stockctl ` + `stockctl.__version__` + 개행 한 줄(현재 `stockctl 0.1.0`), stderr 비어 있음, exit 0, 실행 후 D에 파일 0개 | `tests/test_version.py` pytest(서브프로세스) | 구현 전 RED |
| S-2 | contract | AC-1 | 임시 디렉터리 D에 JSON이 아닌 내용(`not-json`)을 담은 `D/s.json`이 이미 존재, `STOCKCTL_STORE=D/s.json` | `python3 -m stockctl --version` 실행 | exit 0, stdout은 S-1과 동일한 한 줄, `D/s.json` 내용이 실행 전과 바이트 동일(저장소를 읽거나 쓰지 않음 — 읽었다면 JSON 파싱 오류로 비정상 종료) | `tests/test_version.py` pytest(서브프로세스) | 구현 전 RED |
| S-3 | regression | AC-2 | 임시 저장소 `D/s.json`(빈 상태), 허브 `main` 체크아웃과 워크트리 각각에서 동일 명령열 준비 | 두 체크아웃에서 각각 `add A1 --qty 5 --name Apple` → `add B2 --qty 1 --location R1` → `remove A1 --qty 2` → `remove ZZ --qty 1` → `remove B2 --qty 9` → `list`를 `--store D/s.json`로 실행하고 명령별 stdout·stderr·exit를 수집 | 두 체크아웃의 명령별 stdout·stderr·exit가 전부 일치(기대 exit: 0,0,0,1,2,0) | 셸 스크립트로 `python3 -m stockctl` 실행 결과 diff | 구현 후 |
| S-4 | check | AC-2, C-1 | 구현 완료 상태의 워크트리 | `python3 -m pytest -q tests` 실행 | 기존 `tests/test_basic.py` 2건을 포함한 전 테스트 통과, 실패 0 | pytest | 구현 후 |
| S-5 | check | C-1, C-2 | 구현 완료 상태의 워크트리 | `stockctl/cli.py`의 import 문과 @header 확인, `stockctl/`·`docs/`·`tests/`에서 버전 리터럴 `0.1.0` 검색 | `stockctl/cli.py` import가 표준 라이브러리와 패키지 내부(`.`)뿐이고 @header 블록 유지. `0.1.0` 리터럴은 `stockctl/__init__.py`에만 존재(`docs/CLI.md`도 버전 값을 `<버전>` 같은 일반 표기로 적는다) | grep 정적 검사 | 구현 후 |
| S-6 | check | AC-3 | 구현 완료 상태의 워크트리 | `docs/CLI.md` 계약 표 확인 | `stockctl --version` 행이 있고 출력 형식(`stockctl <버전>` 한 줄), 서브커맨드 없이 단독 사용·저장소 미접근, 종료 코드 0이 기재됨 | 문서 정적 검사 | 구현 후 |
