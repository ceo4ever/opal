---
template: sdlc-v2
---
# TEST-SCENARIO: run-log 계약 완성 — PM 활동 누락 판정과 payload 키 폐쇄

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: macOS · Python 3 · 워크트리 작업본 `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_137`. 모든 명령은 이 코드 루트에서 실행한다.
- 공통 데이터: 각 시나리오가 `tempfile.TemporaryDirectory()` 안에 자기 태스크 디렉터리와 run 조각을 만든다. 시나리오 간 상태를 공유하지 않는다.
- 대역 사용과 한계: 사용하지 않음. 판정은 `run.sh` subprocess 실호출 반환값과 디스크 조각·`state.json` 실제 바이트로만 한다(기존 `test_run_log_tool.py` 관례 — mock/patch/MagicMock 금지).
- 실행 조건: 자동 실행. 사용자 협업이 필요한 시나리오 없음.
- 기준선: 변경 전 3스위트 결과를 먼저 측정해 둔다 — `test_run_log_tool.py`, `test_state_tool_run_log.py`, `test_state_tool.py`. S-11의 "신규 실패 0건"은 이 기준선과의 차분으로 판정한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-2, C-1, C-2 | W-1 적용 후 `docs/run-log/CONTRACT.md`와 `opal/tools/state-tool/README.md` | (a) CONTRACT §2.5에서 `missing_pm_activity` 트리거 조문을 읽어 앵커 2종·대조 술어·대조 집합·범위 한정 3항·정렬·항목 형태 6요소가 모두 명시됐는지 확인한다. (b) 두 파일에서 유보 서술을 grep한다 — 패턴: `미집행 공백`, `항상 빈 배열`, `조건 확정은 후속`, `트리거 조건이 확정되지 않아` | (a) 6요소 전건 존재. (b) grep 히트 0건 | manual 문서 검토 + `grep -n` 결정론 검사 | 구현 후 |
| S-2 | AC-5, C-1 | W-1 적용 후 `docs/run-log/CONTRACT.md` §1.3 | (a) 범위 한정 문장을 grep한다 — 패턴: `이 표면을 거치지 않는 다른 생산 경로`, `이 폐쇄 검사를 받지 않는다`. (b) 같은 자리에 집행 지점이 `run_log_core.validate_event()`이고 `append()`를 통과하는 모든 A4 생산 경로에 적용된다는 조문이 있는지 읽는다 | (a) grep 히트 0건. (b) 새 조문 존재 | manual 문서 검토 + `grep -n` | 구현 후 |
| S-3 | AC-4, C-4 | 초기화된 run 1개. PM `activity` 사건(조합 A4: `actor.kind=PM`·`provenance.type=direct`·`recorded_by.kind=PM`), `data={"kind":"progress","x":1}` | `run_log_core.append()`를 인프로세스로 직접 호출한다(`state-tool log-event` CLI를 거치지 않는 경로). 호출 전후로 조각 파일 바이트를 읽는다 | `ok:false`이고 `error.code == "schema_invalid"`. 조각 파일 바이트가 호출 전과 동일(부분 쓰기 0). 코어가 `state.json`을 열지 않음 | unit — `run_log_core` 인프로세스 호출, `tempfile` 격리 | 구현 전 RED |
| S-4 | AC-4 | S-3과 동일 payload | `run-log-tool append` CLI(`run.sh`)로 같은 사건을 기록 시도한다 | exit≠0, 중첩 봉투 `{"ok":false,"error":{"code":"schema_invalid",...}}`. 조각 바이트 불변 | integration — `run.sh` subprocess 실호출 | 구현 전 RED |
| S-5 | AC-4, C-7 | (a) A8 import 조합(`provenance.type=import`·`recorded_by.kind=tool`)의 `activity`에 `data={"kind":"progress","x":1}`. (b) A2 worker 조합의 `activity`에 다중 키 `data`. (c) 변경 후 `run_log_core.py`·`state_tool.py` | (a)(b) 각각 `append()`로 기록한다. (c) `RUN_LOG_ERROR_CODES`·`RUN_LOG_STATE_ERROR_CODES`·`ERROR_CODES` 세 테이블의 키 집합을 변경 전과 비교한다 | (a)(b) 둘 다 `ok:true` — 폐쇄는 A4에만 적용되고 경계 밖으로 새지 않는다. (c) 세 테이블 키 집합 전건 동일(신설 0건), 세 테이블이 여전히 물리 분리 | unit — 인프로세스 호출 + 정적 비교 | 구현 후 |
| S-6 | AC-3, C-2, C-3 | `run_log` 블록 보유 태스크. `rows[]`에 `status="done"` ∧ `owner="auto"` ∧ `key` 보유 행이 1건 이상. 해당 `task_step`에 대응하는 PM `activity(data.kind=decision)` 사건 없음 | `state-tool verify <task> --run-log-completeness-check`를 호출한다. 호출 전후 `state.json` 바이트를 읽는다 | `missing_pm_activity`가 비어 있지 않고, 각 항목이 `row_id`·`row_key`·`stage`·`expected`·`anchor` 5키를 가지며 `anchor=="auto_approved_row"`. 항목 순서가 `row_id` 오름차순. exit 0. `state.json` 바이트 불변 | integration — `run.sh` subprocess 실호출 | 구현 전 RED |
| S-7 | AC-3, C-2, H-2 | S-6과 같은 fixture에서, 해당 행의 `key`와 같은 `task_step`을 실은 PM `activity(data.kind=decision)`를 `state-tool log-event`로 1건 기록한 상태 | 같은 완전성 진단을 호출한다 | `missing_pm_activity`가 빈 배열. 즉 기록하면 신호가 해소된다. exit 0 | integration — `run.sh` subprocess 실호출 | 구현 전 RED |
| S-8 | AC-3, C-2 | `run_log.status == "overridden"`이고 run 전역에 PM `activity(data.kind=decision)` 사건이 0건인 태스크 | 같은 완전성 진단을 호출한다 | `missing_pm_activity`에 `anchor=="override_bundle"` 항목이 정확히 1건이며 `row_id`·`row_key`·`stage`가 `null`. 앵커 ① 항목이 함께 있으면 override 항목이 배열 마지막 | integration — `run.sh` subprocess 실호출 | 구현 전 RED |
| S-9 | C-6 | `run_log` 블록이 없는 schema 1.0 / 1.1 태스크 | (a) 완전성 진단을 호출한다. (b) `advance`·`mark`를 각 1회 호출하고 응답 키 집합과 `state.json` 산출물을 변경 전 기준선과 비교한다 | (a) 모든 누락 목록이 비고 관측 3필드가 전부 `null`, exit 0. (b) 응답 키 집합과 `state.json` 바이트가 기준선과 동일 | integration — `run.sh` subprocess 실호출 + 바이트 비교 | 구현 후 |
| S-10 | C-5, H-3 | W-2가 S-16(`test_run_log_tool.py:906`)·S-17(`:940-963`) fixture를 정정한 뒤 | 두 시나리오를 단독 실행한다 | S-16: 세 variant(`diff_summary`·`diff_data`·`diff_stage`) 모두 `request_id_conflict`를 반환하고 조각 바이트 불변 — `diff_data`가 여전히 `data` 축의 차이로 충돌을 유발한다. S-17: 키 순서를 바꾼 재호출과 1.1초 후 재호출이 모두 `idempotent_hit:true`이고 `event_id`가 최초와 동일 — 다중 키 순열 축과 발급 필드 불변 축이 살아 있다 | unit — 단일 테스트 클래스 직접 실행 | 구현 후 |
| S-11 | AC-6, H-1 | 모든 Work item 적용 후 | Setup의 기준선과 같은 명령으로 3스위트를 전건 실행한다 — `python3 -m pytest opal/tools/run-log-tool/tests/test_run_log_tool.py opal/tools/state-tool/tests/test_state_tool_run_log.py opal/tools/state-tool/tests/test_state_tool.py -q` | 전건 통과. 기준선 대비 신규 실패 0건. 기준선에 없던 실패가 1건이라도 나오면 FAIL이며, 그것이 C-5 범위 밖 fixture 수정을 요구하면 진행하지 않고 블로커로 반환한다 | integration — pytest 전건 실행 | 구현 후 |
| S-12 | AC-7, C-3 | 모든 Work item 적용 후 | `~/.opal/tools/state-tool/run.sh validate <task-path>`를 호출한다 | `ok:true`, `violations` 0건 | integration — `run.sh` subprocess 실호출 | 구현 후 |
| S-13 | C-8 | 모든 Work item 적용 후 | `~/.opal/tools/run-log-tool/run_log_core.py`와 `~/.opal/tools/state-tool/state_tool.py`의 mtime·sha256을 태스크 시작 시점과 비교한다 | 두 배포본 파일 모두 무변경. 변경은 프로젝트 소스에만 적용되었다 | manual — `shasum` 비교 | 구현 후 |
