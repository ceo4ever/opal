# DONE: stockctl 버전 확인 옵션

## 결과

`stockctl --version`이 서브커맨드 없이 단독으로 동작한다. 표준 출력에 `stockctl 0.1.0` 한 줄을 출력하고 exit 0으로 끝난다. 버전 문자열은 `stockctl/__init__.py`의 `__version__`에서만 가져오며, `stockctl/cli.py`에는 버전 리터럴이 없다. argparse `action="version"`이 인자 파싱 중에 종료하므로 저장소 경로 해석·파일 생성·읽기가 일어나지 않는다. `--store`나 `STOCKCTL_STORE`가 가리키는 파일이 없거나 손상되어도 성공한다.

유지한 것: add/remove/list 동작·출력·종료 코드, 인자 없이 실행하면 서브커맨드 필수 오류(exit 2)가 나는 규칙, 기존 테스트 `tests/test_basic.py`, 저장소·버전·진입점 모듈(`stockctl/store.py`, `stockctl/__init__.py`, `stockctl/__main__.py`) 무변경. 외부 패키지는 추가하지 않았다.

## 변경 파일

- `stockctl/cli.py` — `--version` 옵션 추가, @header description 갱신
- `docs/CLI.md` — 명령 표에 `stockctl --version` 행, 저장소 미접근 문장 추가
- `tests/test_version.py` — 신규 pytest 4건(S-1~S-4)

## 검증

- `python3 -m stockctl --version` → stdout `stockctl 0.1.0`, exit 0
- `python3 -m pytest -q`(worktree 루트, 전체) → 6 passed (기존 2 + 신규 4)
- RED 선확인: 구현 전 `tests/test_version.py`의 S-1/S-3/S-4가 argparse 사용법 오류(exit 2)로 실패 → `scenario-red` 3건, `scenario-lock`
- `test-tool scenario-status` → total 7, pass 7, fail/blocked 0 (S-5 git diff 무변경, S-6 CLI.md 기재, S-7 버전 리터럴·의존성·@header 정적 검사 포함)
- 설계 게이트: i1 rewrite(테스트 import 경로 미결정) → 보완 → i3 pass (설계 4축 PASS, 시나리오 2/2/2)
- 컨벤션 자동 진단 `GC-CONVENTION-2026-09-26T15-19.md` → pass, Critical/High 0 (low 1: import 정렬 — isort 기본 규칙상 조치 불요, info 1: 범위 밖 기존 `cmd_add`)

## 회고적 학습 후보

없음

## 참고

- worktree 생성 시 경고: `.opal/code-scan.json` exclude에 `.opal-worktrees`가 없어 code-scan이 worktree 사본까지 스캔할 수 있다. 범위 밖이라 수정하지 않았다.
- 체크포인트: `0ea07c0`(명세), `2b1c359`(구현·테스트) — 브랜치 `feat/OP-TASK-001`. main merge는 사용자 승인 사항이다.
- 회고 개선 후보: FW 3건은 `~/.opal/fw-inbox/`에 기록했다(RED 실패 사유 선측정·duration 기록 유도 / improve-tool worktree `--task-path` 미전달 / finalize의 본문 없는 memory 요청 무반영 applied 처리). 로컬 2건(code-scan exclude 보강, CLI subprocess 테스트 PYTHONPATH 고정)은 memory index 요청으로 남겼지만, finalize 뒤에도 허브 MEMORY.json에 반영되지 않았다. 필요하면 허브에서 별도로 기록해야 한다.
