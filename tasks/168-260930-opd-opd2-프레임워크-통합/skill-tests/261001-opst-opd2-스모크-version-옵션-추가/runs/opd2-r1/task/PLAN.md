# Implementation plan — OP-TASK-001 stockctl `--version`

근거: spec.md(R-1~R-5), intent.md(AC-0~AC-4). 코드맵(`code-scan scan stockctl`): `stockctl/cli.py` module=cli, layer=api, domain=inventory, exports=[main]; `stockctl/__init__.py` module=stockctl, layer=util, exports=[__version__].

## 변경 파일·담당·순서

| W | 파일 | 담당 | 선행 | 완료 기준 |
|---|---|---|---|---|
| W-0 (RED) | `tests/test_version.py` (신규) | Verifier 역할 `verifier-001` — `opal-test-agent` red mode (구현자와 분리, `harness/red-first.md` §1.5) | 없음 | AC-0~2를 공개 CLI(`python -m stockctl`)로 검증하는 pytest가 구현 전 실패(exit 1)하고 role=red 증거가 기록됨 |
| W-1 | `stockctl/cli.py` | Builder `builder-001` — `opal-be-agent` (`docs/PROJECT.md` 프로젝트 구성: CLI `stockctl/`, `tests/` → opal-be-agent) | W-0 | `build_parser()`에 `--version`(argparse `action="version"`, `version=f"%(prog)s {__version__}"`, `from . import __version__`) 추가. @header의 description에 --version 반영. add/remove/list 무변경 |
| W-2 | `docs/CLI.md` | Builder `builder-001` (같은 워커, W-1과 순차) | W-1 | 명령 표에 `` | `stockctl --version` | 버전 출력 `stockctl <__version__>` 한 줄(예: `stockctl 0.1.0`), 저장소 미접근 | 0 | `` 행 추가 |

- W-1·W-2는 같은 Builder가 순차 수행한다. W-0 파일(`tests/test_version.py`)과 `tests/test_basic.py`는 PLAN 전이 시 보호 테스트로 고정되며 Builder는 수정하지 않는다.
- 테스트 설계(W-0): (a) stdout이 정확히 `"stockctl 0.1.0\n"`이고 returncode 0, stderr 비어 있음 — AC-0. (b) stdout이 `f"stockctl {stockctl.__version__}\n"`과 같음 — AC-1. (b') 하드코딩 차단(PLAN 사전심사 Call A F-A1 반영): 하위 프로세스에서 `stockctl.__version__`을 `"9.9.9"`로 바꾼 뒤 `stockctl.cli`를 import하고 `main(["--version"])`을 호출하면 stdout이 `stockctl 9.9.9`이고 exit 0 — 리터럴 `0.1.0`을 cli에 박으면 실패한다. (c) `STOCKCTL_STORE`/`--store`를 tmp의 없는 경로로 주면 실행 후에도 그 파일이 생성되지 않음, 그리고 손상된 JSON 저장소 파일을 `--store`로 줘도 exit 0 — AC-2(무생성·무읽기). 서브커맨드 없이 `--version`만 호출.

## 검증 시나리오

| AC | 명령(plan.json checks) | 기대 동작 |
|---|---|---|
| AC-0, AC-1, AC-2 | `python3 -m pytest -q tests/test_version.py` | 구현 전 exit 1(RED: argparse가 `--version`을 모르고 서브커맨드 필수로 exit 2 → assertion 실패), 구현 후 exit 0 |
| AC-0~AC-3 | `python3 -m pytest -q tests` | 신규 + 기존 `tests/test_basic.py`(add/list, remove 수량 부족 exit 2) 모두 통과 — 회귀 없음 |
| AC-4 | `grep -qE -e '^\| `stockctl --version` \|.*stockctl 0\.1\.0.*\| 0 \|$' docs/CLI.md` | 문서 표에 `--version` 행(출력 예시와 종료 코드 0)이 있으면 exit 0 |

- RED: `red_checks` = `python3 -m pytest -q tests/test_version.py` 기대 exit 1. PLAN 단계에서 Verifier가 `collect-evidence --role red`로 기록한다.
- 보호 테스트: `tests/test_version.py`, `tests/test_basic.py`.

## 위험·배포·복구
- 위험도 normal: 가역적 CLI 옵션 추가, 저장소·데이터 포맷 무변경, 외부 패키지 없음.
- 영향: `--version`은 파싱 중 즉시 종료하므로 기존 서브커맨드 경로에 영향 없음. 기존 옵션명과 충돌 없음(`stockctl/cli.py:52-65`).
- 복구: worktree 브랜치 `feat/OP-TASK-001`의 해당 커밋을 revert하거나 main에 merge하지 않는다. 배포 없음(delivery=build, merge는 사용자 승인 사항).
- 실행 권한: Builder는 W-1·W-2 파일만, Verifier는 W-0 테스트 파일만 쓴다. 상태 전이·승인은 Coordinator만.
