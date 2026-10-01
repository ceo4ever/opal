# Specification — OP-TASK-001 stockctl `--version`

## 요구사항과 사용자 흐름
흐름: 운영자 → `stockctl --version`(또는 `python -m stockctl --version`) → 표준 출력 `stockctl 0.1.0` → exit 0.

| 요구 | 연결 AC |
|---|---|
| R-1 최상위 파서에 `--version` 옵션을 추가하고 `stockctl <__version__>` 한 줄을 stdout에 출력 후 exit 0 | AC-0 |
| R-2 버전 문자열은 `stockctl.__version__`(`stockctl/__init__.py:10`)을 import해 사용 — 리터럴 중복 금지 | AC-1 |
| R-3 `--version`은 서브커맨드 검사·저장소 경로 해석·load/save 이전에 처리되어 단독 사용 가능, 저장소 파일 무접근 | AC-2 |
| R-4 add/remove/list 파서·핸들러는 변경하지 않는다 | AC-3 |
| R-5 `docs/CLI.md` 명령 표에 `stockctl --version` 행(출력 형식·종료 코드 0)을 추가 | AC-4 |

## 설계·정책·우려 사항
- 설계: `stockctl/cli.py:50-52` `build_parser()`에서 `--store` 옆에 `p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")`를 추가하고 `from . import __version__`으로 값을 가져온다. `prog="stockctl"`(`stockctl/cli.py:51`)이므로 출력은 `stockctl 0.1.0`.
- 근거: 표준 라이브러리 `argparse._VersionAction.__call__`은 버전 문자열을 `sys.stdout`으로 출력하고 `parser.exit()`(exit 0)를 호출한다(로컬 Python 실측 소스). 이 액션은 인자 파싱 도중 즉시 실행되므로 `add_subparsers(required=True)`(`stockctl/cli.py:53`)의 필수 검사 이전에 종료되고, `main()`의 `store.store_path`·핸들러(`stockctl/cli.py:69-72`)에 도달하지 않는다 → 저장소 무접근(R-3).
- 대안 기각: `main()`에서 `argv`를 수동 검사하는 방식은 argparse 관례와 중복되고 `--store X --version` 같은 조합을 별도 처리해야 해서 기각.
- 테스트: 신규 `tests/test_version.py`(pytest, `python -m stockctl` subprocess 호출 — `docs/CONVENTIONS.md`)로 AC-0~2를 검증, 기존 `tests/test_basic.py`는 수정하지 않고 회귀 확인(AC-3). 문서 AC-4는 결정론 검사(grep)로 확인.
- 정책: `.opal/AGENT.md` 금지사항(표준 라이브러리만, 승인 없는 수정 금지 — `//opd2` 지시로 승인), `docs/CONVENTIONS.md`(@header 유지·pytest·`python -m stockctl`). 위험도 normal.
- 우려: 없음. `--version`은 기존 옵션·서브커맨드 이름과 충돌하지 않는다(`stockctl/cli.py:52-65`).

## 미결 질문
없음.
