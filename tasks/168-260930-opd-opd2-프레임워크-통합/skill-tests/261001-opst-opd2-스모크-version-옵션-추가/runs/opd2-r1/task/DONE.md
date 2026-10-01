# DONE: stockctl --version 옵션 (OP-TASK-001)

> 완료: 2026-10-01 11:42 KST | opd2 agentic · worktree `feat/OP-TASK-001` | delivery=build → CLOSED/ready_for_merge

## 결과

`stockctl --version`(및 `python -m stockctl --version`)이 표준 출력에 `stockctl 0.1.0` 한 줄을 출력하고 exit 0으로 끝난다. 버전은 `stockctl/__init__.py`의 `__version__`을 import해 argparse `action="version"`으로 출력하므로 리터럴 중복이 없다. 파싱 도중 종료되어 서브커맨드 없이 단독으로 동작하고 저장소 파일을 만들거나 읽지 않는다. add/remove/list 파서·핸들러와 인자 없음(exit 2)·`-h` 동작은 그대로다. `docs/CLI.md`에 `--version` 행을 추가했다.

## 변경 파일

- `stockctl/cli.py` — `from . import __version__`, `--version` 옵션 1행, @header description 갱신
- `tests/test_version.py` — 신규(6 테스트: 정확한 출력·`__version__` 일치·하드코딩 차단(`__version__`=9.9.9 추종)·`--store`/`STOCKCTL_STORE` 미생성·손상 저장소 미읽기)
- `docs/CLI.md` — 명령 표에 `stockctl --version` 행 추가

## 검증

- RED(구현 전, Verifier `verifier-001`): `python3 -m pytest -q tests/test_version.py` → exit 1, 6 failed(required 서브커맨드 오류 exit 2) — `run/opd2-evidence-2.log`
- Builder(`builder-001`): checks 3건 exit 0·stable — `run/opd2-evidence-3..5.log` (test_version 6 passed, tests 8 passed, docs grep 일치)
- 독립 Verifier(`verifier-001`, 별도 세션): 같은 checks 3건 exit 0·stable — `run/opd2-evidence-6..8.log`. 직접 관찰: 출력 15바이트 1줄·stderr 0바이트, 저장소 미생성, remove 성공(0)·미등록 SKU(1)·수량 부족(2)·list 형식·인자 없음(2)·`-h`(0) 회귀 없음 → AC-0~4 pass
- PLAN 사전심사: Call A 1차 fail(AC-1 하드코딩 미검증) → 테스트 보강 후 Call A·B 현재 fingerprint pass
- 최종 독립 Reviewer(`reviewer-001`): pass, 차단 finding 0
- 컨벤션 자동 진단: Critical/High 0, Low 2 — `GC-CONVENTION-2026-10-01T11-40-00.md`
- `code-scan validate --changed`: newly_uncovered 0 / `state-tool validate`: violations 0

## 회고적 학습 후보

없음

## 참고

- 미머지: `feat/OP-TASK-001`는 main에 merge·push하지 않았다(사용자 승인 사항). merge 후 `finalize-attribution`으로 MEMORY 히스토리가 귀속된다.
- 비차단 advisory: (1) `stockctl/cli.py:66` 변수명 `l`(PEP 8 E741, 기존 코드) (2) 하드코딩 차단 테스트만 `python -c`로 `main`을 호출(`__version__` 런타임 치환 목적의 의도적 예외) (3) `--version`은 최상위 전용 — `stockctl list --version`은 exit 2(서브커맨드별 버전은 비목표) (4) 버전 값 변경 시 `tests/test_version.py` EXPECTED와 docs grep 기준도 함께 갱신 필요.
- 진행 판단: 워크트리 전용 터미널(Orca) 기동은 하지 않고 lease를 보유한 허브 세션이 발급 작업본에서 수행했다. 서브에이전트 디스패치 중 OPAL 훅 커서 파일(`.opal/run/.runtime/agent-tool-adapter/*.json`, 도구 문서상 순수 성능 최적화)이 작업본에 생겨 범위 검사에 걸려 1회 제거했다.
