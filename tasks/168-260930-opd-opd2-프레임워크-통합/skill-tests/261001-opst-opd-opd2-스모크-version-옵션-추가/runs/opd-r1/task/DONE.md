# DONE: stockctl 버전 확인 옵션

## 결과

`stockctl --version`을 서브커맨드 없이 실행하면 표준 출력에 `stockctl 0.1.0` 한 줄을 출력하고 종료 코드 0으로 끝난다. 버전 문자열은 `stockctl/__init__.py`의 `__version__`을 import해 쓰며 다른 곳에 버전 리터럴을 두지 않았다. argparse `action="version"`으로 구현해 서브커맨드 필수 검사와 저장소 경로 해석보다 먼저 종료하므로, 저장소 파일을 만들거나 읽지 않는다(파싱 불가 저장소를 지정해도 exit 0, 파일 불변). 기존 add/remove/list 동작과 기존 테스트는 바뀌지 않았고 `docs/CLI.md`에 옵션 행을 추가했다. 표준 라이브러리만 사용했다.

## 변경 파일

- `stockctl/cli.py`
- `docs/CLI.md`
- `tests/test_version.py` (신규)

## 검증

- RED: 구현 전 `python3 -m pytest -q tests/test_version.py` → 2 failed (`assert 2 == 0`), S-1·S-2 `scenario-red` 기록 후 `scenario-lock`
- `python3 -m pytest -q tests` (worktree 루트, Python 3.14.3, HEAD `76ae603`) → 4 passed
- `python3 -m stockctl --version` → `stockctl 0.1.0`, exit 0
- TEST(opal-test-agent): S-1~S-5 전건 PASS (`test-scenario.json`), 전체 회귀 4 passed, 보안 스캔 이상 없음
- 설계 게이트(opal-evaluator-agent design-rubric) i1 pass — 설계 4축 PASS, 시나리오 2/2/2
- 컨벤션 진단(opal-convention-checker): Critical/High 0 (Low 2, Info 2 advisory) — `GC-CONVENTION-2026-10-01T09-58-00.md`

## 회고적 학습 후보

없음

## 참고

- 컨벤션 advisory(비차단): `tests/test_version.py`의 미사용 `monkeypatch` 인자 2건, `cli.py` 함수 docstring 부재·서브파서 변수명 한 글자(기존 코드). 프로젝트 CONVENTIONS에 명시 규칙이 없어 이번 범위에서 수정하지 않음.
- merge는 사용자 승인 사항: 허브에서 `git merge --ff-only feat/OP-TASK-001` 후 귀속 절차 진행.
