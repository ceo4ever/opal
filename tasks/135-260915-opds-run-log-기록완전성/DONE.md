# DONE: run-log 기록 완전성

## 결과

`shadow`와 `active`가 같은 표준 사건 집합을 기록하고, 두 모드의 차이가 "기록 범위"가 아니라 "기록 증거가 완료 판정을 차단하는지"로 좁혀졌다.

**달라진 것**

- **복합 상태 전이가 각각 관측된다.** `run_log_commit()`이 단일 event와 event list를 모두 받고, `advance`/`mark`가 자동 승인한 각 사용자 확인 행과 대상 행 전이를 독립 `state.changed`로 남긴다. admission은 전부-아니면-전무이며, 여러 사건이 한 pending_events 묶음으로 커밋된 뒤 기존 drain을 멱등 재사용한다.
- **PM 의사결정과 게이트 생명주기가 표준 사건으로 남는다.** `state-tool log-event`·`gate-request`·`gate-resolve` 3종을 신규 구현했다. `surfaces.json`에 선언만 있고 구현이 없던 표면이며, 세 명령 모두 별도 기록 경로 없이 `run_log_commit()`의 같은 outbox/admission/drain을 재사용한다.
- **관측 중단 지점을 기계로 판정할 수 있다.** `state-tool verify --run-log-completeness-check`(7번째 상호 배타 라우트)가 `state.json`과 JSONL을 대조해 누락 목록 4종과 관측 지점 3필드(`last_observed_decision`·`last_observed_state_change`·`last_observed_boundary`)를 반환한다. 3필드는 누락 목록과 무관하게 항상 반환되어, 마지막 의사결정·마지막 상태 전이·관측 중단 지점을 사람 판독 없이 구분한다.
- **active 완료 게이트가 동작한다.** 호출자가 명시 전달한 `profiles.json`에 항목이 있는 channel만 active로 수용하고, 완료 전이 시 trusted 증거가 부족하면 `completion_evidence_missing`으로 거부한다.
- **계약이 구현과 일치한다.** CONTRACT §1.2에 모드별 인벤토리 동일성, §1.3에 PM `activity` 페이로드 폐쇄 목록을 확정했고, `refs_invalid` 신설과 `schema_invalid`의 `state-tool.log-event` 대응을 등재했다.

**유지된 것**

- shadow는 기록 실패·관측 불가에도 상태 전이를 완료하고 exit 0을 유지한다(C-1).
- 미승인 channel의 active 초기화는 기존대로 `profile_not_found`로 거부된다. `profiles.json`을 새로 만들거나 channel을 자동 승격하지 않았다(C-2, H-4).
- schema 1.0/1.1과 run_log 블록 없는 태스크의 `advance`/`mark`/`validate`는 응답 키 집합과 산출물이 종전과 동일하다(C-6).
- append-only·순번 연속성·멱등성·배타 락·마스킹·경로 방어 계약이 그대로 통과한다(C-5).
- 기존 22종 도구의 평면 오류 봉투는 오염되지 않았다. 중첩 봉투(`error.code`/`message`/`detail`)는 CONTRACT §2.1이 run-log 계열 전용으로 확정한 형태이며 신규 3종 표면에만 적용했고, `RUN_LOG_STATE_ERROR_CODES`는 `ERROR_CODES`와 물리 분리된 별도 테이블이다.
- `run_log_core`는 상태 원천 파일을 읽지 않는다(TRD D-5 단방향 의존). state/log 대조는 `state-tool`이 전담한다.

**적용한 경계**

- `docs/run-log/surfaces.json`에 신규 표면 `id`를 추가하지 않았다. `verify` 라우트는 7개 전부가 이 인벤토리 밖에 있어, 7번째만 등재하면 형제 6개가 빠진 비대칭 인벤토리가 된다.
- `run_log_core.append()`에는 `data` 키 집합 폐쇄 검사를 넣지 않았다. 사유는 §참고.
- 배포(install)를 수행하지 않았다. 프로젝트 소스만 수정했다.

## 변경 파일

- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/tests/test_state_tool_run_log.py`
- `opal/tools/state-tool/README.md`
- `docs/run-log/CONTRACT.md`
- `docs/run-log/TRD.md`
- `docs/run-log/surfaces.json`

## 검증

- `python3 -m pytest opal/tools/state-tool/tests/test_state_tool_run_log.py -q` → 29 passed, 0 failed
- `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q` → 411 passed, 3 skipped, 116 subtests passed
- `python3 -m pytest opal/tools/run-log-tool/tests/test_run_log_tool.py -q` → 53 passed, 4 subtests passed
- 추가 탐색 스위트(`test_run_identity.py`·`test_mode_resolution.py`·`test_mode_transition_contract.py`·`test_todo_mirror_hook.py`·`test_event_verify.py`) → 47 passed, 71 subtests passed
- `scripts/tests/` 파이썬 계약 테스트 3종 → 전건 OK
- `state-tool verify --plan-contract-check` / `--code-scan-citation-check` → 각 pass
- `state-tool validate` → violations 0
- `python3 -m json.tool docs/run-log/surfaces.json` → OK
- 마스킹 실증: `log-event --summary "api_key=... Bearer ..."` 기록 후 JSONL byte 검색 → `[REDACTED]` 치환 확인, 원문 미검출
- 경로 방어 실증: 상대 task-path → `task_path_not_absolute`, `--refs /etc/passwd` → `refs_invalid`
- 시나리오 판정 원본은 `test-scenario.json`이 소유한다 — `scenario-status`: locked=true, total 11, passed 11, failed 0, red_confirmed_required 9/9

## 회고적 학습 후보

없음

## 참고

**미완 2건 — 후속 태스크에서 계약부터 정해야 한다**

1. **`data` 키 집합 폐쇄가 `state-tool log-event` 표면 하나에만 걸린다.** CONTRACT §1.3의 집행 지점을 "append 단계"에서 실제 지점으로 정정했다. 코어 집행을 시도했으나 기존 `test_run_log_tool.py:906`(digest 차이 검증)과 `:951`~`:963`(멱등 정규화 검증) fixture가 임의 `data` 키를 전제로 설계되어 있어 회귀 없이 넣을 수 없었다. adapter·importer 등 `log-event`를 거치지 않는 생산 경로는 이 폐쇄 검사를 받지 않으므로, C-3의 보장 범위가 그만큼 좁다. 이 한계는 §1.3에 명시했다.
2. **`missing_pm_activity`가 항상 빈 배열이다.** "PM activity가 언제 누락으로 판정되는가"의 결정론적 트리거가 계약에 없다. 구현자가 조건을 만들면 그 조건이 사실상 계약이 되는 역전이 생기므로 발명하지 않고 공백을 CONTRACT에 명시했다. AC-5의 누락 식별 4종 중 1종이 미집행이다.

**배포 필요**

- `state_tool.py`는 소스와 배포본이 갈라져 있다. 현재 `~/.opal/tools/state-tool/run.sh`로는 신규 3종 CLI와 `--run-log-completeness-check`를 호출할 수 없다. 배포는 별도 승인 경계라 이번 태스크에서 수행하지 않았다.

**범위 밖으로 남긴 것**

- `state-tool.restart-run`이 CONTRACT §2.4와 `surfaces.json`에 선언돼 있으나 구현이 없다(`add_parser` 0건). 이번 TASK 범위가 기록 완전성이고 PLAN Work items에 없어 건드리지 않았다.
