# DONE: stockctl 버전 확인 옵션

## 결과

- `stockctl --version`이 서브커맨드 없이 단독으로 동작하며, 표준 출력에 `stockctl 0.1.0` 한 줄을 출력하고 exit 0으로 끝난다. 버전 문자열은 `stockctl/__init__.py`의 `__version__`을 그대로 사용한다(argparse `action="version"`).
- `--version`은 파싱 단계에서 종료되므로 저장소 파일을 만들거나 읽지 않는다. JSON이 아닌 저장 파일이 이미 있어도 성공하고 그 파일은 바이트 단위로 그대로다.
- 기존 add/remove/list 명령의 출력과 종료 코드(0/1/2)는 허브 `main`과 명령 단위로 동일하며, 기존 테스트도 통과한다.
- `docs/CLI.md` CLI 계약 표에 `stockctl --version` 행을 추가했다.

## 변경 파일

- `stockctl/cli.py`
- `docs/CLI.md`
- `tests/test_version.py` (신규)

## 검증

- `python3 -m pytest -q tests` → 4 passed (기존 `tests/test_basic.py` 2건 + 신규 `tests/test_version.py` 2건)
- `python3 -m stockctl --version` → `stockctl 0.1.0`, exit 0
- RED-first: 구현 전 `tests/test_version.py` 2 failed(stdout 비어 있음 / exit 2) 관측 → `scenario-red` S-1·S-2 기록 → lock → GREEN 후 통과
- TEST-SCENARIO S-1~S-6 전부 PASS (`test-scenario.json`, opal-test-agent 독립 실행). S-3: 허브 `main`과 worktree의 add/add/remove/remove(미등록)/remove(부족)/list stdout·stderr·exit 일치
- 설계 게이트 i1 pass(opal-evaluator-agent design-rubric), 컨벤션 최종 검사 0건(`GC-CONVENTION-2026-10-01T09-54-59.md`), 보안 검사 통과

## 회고적 학습 후보

없음

## 참고

- 변경은 worktree 브랜치 `feat/OP-TASK-001`의 작업 트리에 **미커밋** 상태다. 전용 터미널 기동 실패로 registry가 `recovery_required`라 체크포인트 커밋이 `checkpoint_ownership_denied`로 거부되었다. 커밋·merge는 사용자 승인 사항이다.
