---
template: sdlc-v2
---
# TEST-SCENARIO: stockctl 버전 확인 옵션

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: worktree 루트(`.opal-worktrees/task_001`)에서 로컬 Python 3(`python3`)와 pytest. 외부 서비스 없음.
- 공통 데이터: 각 테스트는 pytest `tmp_path`를 작업 디렉토리 또는 저장소 경로로 사용한다. CLI는 `python -m stockctl`로 subprocess 호출한다(`docs/CONVENTIONS.md`).
- 대역 사용과 한계: 사용하지 않음. 실제 CLI 프로세스를 실행한다.
- 실행 조건: 자동 실행. 사람 협업 없음.

## Scenarios

| ID | 유형 | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|---|
| S-1 | contract | AC-1, C-2 | 빈 `tmp_path`를 cwd로 사용, 환경변수 `STOCKCTL_STORE` 제거, `--store` 미지정 | `python -m stockctl --version` 실행(서브커맨드 없음) | returncode 0; stdout이 정확히 `f"stockctl {stockctl.__version__}\n"`(현재 `stockctl 0.1.0\n`)이며 줄 수 1; stderr 비어 있음; 실행 후 `tmp_path`에 새 파일(`stock.json` 포함)이 생기지 않음 | pytest subprocess, `tests/test_version.py` | 구현 전 RED |
| S-2 | contract | AC-1 | `tmp_path/s.json`에 JSON 파싱 불가 내용(`not json`)을 기록하고 내용·mtime 기록, `STOCKCTL_STORE`도 같은 경로로 설정 | `python -m stockctl --store <tmp_path/s.json> --version` 실행 | returncode 0; stdout이 S-1과 동일한 한 줄; stderr 비어 있음(저장소를 읽었다면 JSON 오류로 실패); 파일 내용과 mtime 불변; `s.json.tmp` 미생성 | pytest subprocess, `tests/test_version.py` | 구현 전 RED |
| S-3 | check | C-1, C-2 | 구현 완료된 worktree | `stockctl/` 아래에서 버전 리터럴 `0.1.0` 검색, `stockctl/cli.py`의 import 목록 확인 | `0.1.0`은 `stockctl/__init__.py`에만 존재; `stockctl/cli.py`는 표준 라이브러리와 패키지 내부(`from . import ...`)만 import | grep / 소스 확인 | 구현 후 |
| S-4 | check | AC-2, C-3 | 구현 완료된 worktree | `git diff main -- tests/test_basic.py` 확인 후 `python3 -m pytest -q tests/test_basic.py` 실행 | diff 없음; 기존 2개 테스트(add/list, remove 수량 부족 exit 2) 모두 PASS | git + pytest, worktree 루트 | 구현 후 |
| S-5 | check | AC-3 | 구현 완료된 worktree | `docs/CLI.md` 명령 표 확인 | `stockctl --version` 행이 존재하고 출력 형식 `stockctl <버전>` 한 줄, 저장소 미접근, 종료 코드 0이 기재됨; 기존 add/remove/list 행 불변 | 문서 확인 | 구현 후 |
