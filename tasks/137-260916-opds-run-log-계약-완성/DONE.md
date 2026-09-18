# DONE: run-log 계약 완성 — PM 활동 누락 판정과 payload 키 폐쇄

## 결과

태스크 135가 "계약이 아직 정하지 않았다"며 남긴 빈 곳 2개가 집행 가능한 조문이 됐다. 둘 다 `docs/run-log/CONTRACT.md`가 먼저 조문을 확정하고 구현이 그것을 따랐으며, 그 순서를 PLAN `Work items`의 선행 작업 그래프(P1 계약 → P2 시나리오 → P3 구현 → P4 회귀)로 강제했다.

**달라진 것**

- **완전성 진단이 PM 활동 누락을 실제로 보고한다.** CONTRACT §2.5가 트리거 조건을 앵커 2종으로 정의했다 — ① `status=done` ∧ `owner=auto` ∧ `key` 보유 행에 `task_step` 일치 PM `activity(decision)`가 없으면 그 행마다 1건, ② `run_log.status=overridden`인데 run 전역에 그 사건이 0건이면 배열 마지막에 1건. 대조 집합(조각∪보관함), 정렬(`row_id` 오름차순 후 override 말미), 항목 형태(5키)까지 조문이 소유하고 `_run_log_completeness_check()`가 그대로 집행한다. AC-5의 누락 식별 4종이 전부 동작한다.
- **"판정하지 않음"과 "미구현"이 문장으로 구분된다.** 범위 한정 3항(`key` 없는 행 / `run_log` 블록 없는 태스크 / `--force` 통과)을 계약이 판정 대상에서 **정의상 제외**한다고 명시하고, 독해 규칙까지 덧붙였다 — 판정 대상 입력에서 목록이 비면 "누락 없음"이다. 빈 배열이 더 이상 모호하지 않다.
- **payload 키 폐쇄가 표면 1개에서 코어로 내려왔다.** 집행 지점이 `state-tool log-event` CLI 입력 검증에서 `run_log_core.validate_event()`로 이동해, `append()`를 통과하는 모든 A4 생산 경로(CLI·인프로세스)가 같은 판정을 받는다. `state-tool.log-event`의 `_build_pm_activity_data()`는 앞단 중복 방어로 남으며 두 지점의 판정이 항상 일치함을 계약이 못 박았다.
- **135가 막혔던 fixture 충돌이 축을 잃지 않고 풀렸다.** S-16은 `data` 축이 검증 lever 자체라 단일 키로 줄였고(기준 이벤트가 `data=None`이라 digest 차이 유지), S-17은 단일 키가 되면 "키 순서 불변" 축이 소멸하므로 조합 A7 `state.changed`(`from`/`to`/`row_key` 3키 필수)로 옮겨 순열을 보존했다.
- **기준선 선행 실패 4건이 해소됐다.** 원인은 하나가 아니라 둘이었다 — 3건은 "개정 전"을 움직이는 `HEAD` 참조로 대리해 커밋 `f8aba0a` 머지와 동시에 자기무효화됐고, 1건은 중첩 pytest를 `python3`로 하드코딩 기동해 커밋 `15fee62`의 인터프리터 게이트에 막혀 **스위트가 수집조차 되지 않던** 상태였다. 앞은 고정 커밋 상수로 핀, 뒤는 기동 인터프리터 교체로 처리했고 어느 쪽도 단언을 약화하지 않았다.

**유지된 것**

- `run_log_core`는 상태 원천 파일을 읽지 않는다. 새 폐쇄 분기는 순수 인메모리 판정이며 상태 대조는 `state-tool`이 전담한다(C-4 / TRD D-5).
- 새 오류 코드·표면 id 0건. `RUN_LOG_ERROR_CODES` 11종, `RUN_LOG_STATE_ERROR_CODES` 15종, `ERROR_CODES` 53종이 전부 불변이며 3종 물리 분리도 유지된다(C-7).
- 완전성 진단은 read-only·비차단이다. `state.json` 바이트 불변과 exit 0을 시나리오가 단언한다(C-3).
- 스키마 1.0/1.1과 `run_log` 블록 없는 태스크의 응답 키 집합·산출물이 종전과 동일하다(C-6).

**적용한 경계**

- 폐쇄 적용 조건을 조합 A4로 한정했다. A1(adapter)·A8(import)은 조합 자체가 조건을 만족하지 않아 자연 배제되며, 이는 집행의 빈틈이 아니라 적용 범위의 정의다.
- 배포(install)를 수행하지 않았다. 프로젝트 소스만 수정했고 배포본 2종의 sha256이 태스크 시작 시점과 바이트 일치한다(C-8).

## 변경 파일

- `docs/run-log/CONTRACT.md`
- `opal/tools/run-log-tool/run_log_core.py`
- `opal/tools/run-log-tool/tests/test_run_log_tool.py`
- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/tests/test_state_tool_run_log.py`
- `opal/tools/state-tool/README.md`

## 검증

- `python -m pytest opal/tools/run-log-tool/tests/test_run_log_tool.py -q` → 57 passed, 0 failed
- `python -m pytest opal/tools/state-tool/tests/test_state_tool_run_log.py -q` → 36 passed, 0 failed
- `python -m pytest opal/tools/state-tool/tests/test_state_tool.py -q` → 411 passed, 3 skipped
- 기준선 대조(`BASELINE.md`, EXECUTE 진입 전 캡처) → 4 failed / 489 passed → **0 failed / 504 passed**, 신규 실패 0건·기존 실패 4건 전건 해소
- `state-tool verify --plan-contract-check` / `--code-scan-citation-check` → 각 pass
- `state-tool validate` → violations 0
- `code-scan validate --changed <변경 6파일> --json` → `ok:true`, `newly_uncovered` 0 (`pre_existing` 1 = `CONTRACT.md`, 비차단)
- `op-gc-convention` 진단 → Critical/High 0건. Low 1건(PEP8 공백 3→2)은 정정 후 해당 스위트 36 passed 재확인
- 배포본 sha256 → `bcc6f6ca…845e4`(`run_log_core.py`) / `05d3a1ee…8386b`(`state_tool.py`), BASELINE.md와 바이트 일치
- 시나리오 판정 원본은 `test-scenario.json`이 소유한다 — `scenario-status`: locked true, total 13, passed 13, failed 0, red_confirmed_required 5/5, fidelity 전건 `real-usage`

## 회고적 학습 후보

없음

## 참고

**후속 권고 1건 — 이번 범위 밖**

- 인터프리터 게이트(`15fee62`)가 신설될 때 기존 하드코딩 호출부를 함께 개정하지 않으면 그 테스트가 **조용히 무력화된다.** 이번에 `TestExistingRegressionBaseline`이 그 사례였고, 리포 전역 점검에서 `opal/tools/event-loader/tests/test_event_loader_worktree_root.py:50`에 같은 패턴(`["python3", str(...)]`) 1건이 남아 있다. W-7 범위 밖이라 손대지 않았다.

**배포 필요**

- `state_tool.py`·`run_log_core.py`는 소스와 배포본이 갈라져 있다. 현재 `~/.opal` 경로로는 이번 개정분(`missing_pm_activity` 트리거, 코어 A4 폐쇄)을 호출할 수 없다. 배포는 별도 승인 경계라 이번 태스크에서 수행하지 않았다.
