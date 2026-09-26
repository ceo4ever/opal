# DONE: stockctl 버전 확인 옵션(--version) 추가

## 결과

`stockctl --version`을 서브커맨드 없이 실행하면 stdout에 `stockctl 0.1.0` 한 줄을 출력하고 exit 0으로 끝난다. 버전 문자열은 `stockctl/__init__.py`의 `__version__`을 import해 argparse `action="version"`(`%(prog)s {__version__}`)으로 출력하므로 CLI에 버전 리터럴이 없다. version action은 파싱 중 즉시 종료하므로 저장소 경로 해석·파일 읽기/쓰기에 도달하지 않는다. `docs/CLI.md` 명령 표에 옵션을 추가했다.

유지된 동작: add/remove/list의 출력·종료 코드, 서브커맨드 필수 계약(`python -m stockctl` 단독 실행 시 exit 2), 저장소 형식(`stockctl/store.py` 무변경).

## 변경 파일

- `stockctl/cli.py`
- `docs/CLI.md`
- `tests/test_version.py` (신규)

## 검증

- RED: 구현 전 `python3 -m pytest tests/test_version.py` → 3 failed (모두 exit 2, `the following arguments are required: command`) — S-1~S-3 red_confirmed, scenario locked
- `python3 -m stockctl --version` → exit 0, stdout `stockctl 0.1.0\n`, stderr 없음 (S-1)
- `tests/test_version.py` 3 passed — 출력·버전 단일 출처(복사본 `9.9.9` 반영)·저장소 파일 비생성 (S-1~S-3)
- `python3 -m pytest tests/test_basic.py` → 2 passed (S-4)
- `python3 -m stockctl` → exit 2 유지 (S-5)
- `docs/CLI.md` 8행 `stockctl --version` 행 확인 (S-6)
- `python3 -m pytest` → 5 passed (S-7)
- 컨벤션 진단 `GC-CONVENTION-2026-09-26T09-28-29.md`: Critical/High/Medium/Low 0, Info 1(AC-1 요구에 따른 고정 리터럴 단언 — 의도적 유지)

## 회고적 학습 후보

없음

## 참고

- worktree-tool create 경고: `.opal/code-scan.json` exclude에 `.opal-worktrees`가 없어 code-scan 커버리지가 왜곡될 수 있다(범위 밖, 미조치).
- 실행 환경 PATH에 `python`이 없고 `python3`만 있다. 검증은 `python3`로 수행했다.
- main 머지는 사용자 승인 대상이다(아래 CLOSE 안내 참조).
