---
template: sdlc-v2
---
# TEST-SCENARIO: run-log 기록 완전성

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: 임시 태스크 폴더와 실제 `state-tool`/`run-log-tool` CLI, 실제 `state.json` 및 분할 JSONL 파일을 사용한다. shadow와 검증용 active state/profile fixture를 같은 사건 입력으로 구성한다.
- 공통 데이터: user confirmation 2건과 다음 단계 행 1건, PM activity 4종, worker 시작·중간·종료, gate 요청·해결, 정상/기록 실패/구조적으로만 유효한 누락 run fixture를 사용한다. opal-studio 원본은 읽기 전용 원인 근거로만 사용하고 내부 fixture로 재현한다.
- 대역 사용과 한계: mock/patch/MagicMock/가짜 파일시스템은 사용하지 않는다. active 채널은 승인된 배포를 가정하지 않고 검증 fixture와 현재 `profile_not_found` 경계를 각각 검증한다.
- 실행 조건: RED 작성 전에 W-0이 D-1·D-2 의미 계약 조문을 `docs/run-log/CONTRACT.md`에 확정해야 한다 — RED가 고정하는 기대값의 판정 원천이다. RED 행은 구현자와 다른 `opal-test-agent` red mode가 먼저 실패를 고정하며, 각 RED 케이스는 GREEN 담당 work item 번호(W-2/W-3/W-4)를 태깅한다. 구현 후 동일 공개 명령과 전체 회귀 스위트를 새 프로세스에서 실행한다. 외부 네트워크나 사용자 수동 조작은 필요하지 않다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, C-1, C-2, C-4 | 동일한 실행·상태·PM·worker·gate 입력을 갖는 shadow와 검증용 active run | 각 run에 표준 표면으로 사건을 기록하고 event 종류·payload 의미·provenance와 완료 판정을 비교 | 두 모드의 관측 가능 event 인벤토리와 표준 payload 의미가 동일하고, 차이는 provenance 신뢰도와 completion enforcement에만 있음 | CLI integration, 실제 JSONL 집합 비교 | 구현 전 RED |
| S-2 | AC-2, C-3, C-5, H-2 | run-log가 활성화된 shadow/active fixture와 상대경로 정규화 가능한 refs | 신규 구현되는 `state-tool log-event`(surfaces.json 선언·현재 미구현)로 PM progress·decision·validation·retry를 summary·reason·refs와 함께 기록하고 조회 | 두 모드 모두 `activity` 4종이 남고 decision·validation·retry의 판단 요약·사유·근거 참조를 복원할 수 있음 | CLI integration, 실제 JSONL 역직렬화 | 구현 전 RED |
| S-3 | C-3, C-5, H-2 | W-0이 CONTRACT에 확정한 허용 필드 화이트리스트 밖의 키, 외부 절대경로 refs, 비밀값을 포함한 PM activity 입력 | 신규 `state-tool log-event`와 디스크 직렬화 경로를 실행 | 화이트리스트 밖 키는 구조화 오류로 거부되고, 절대경로 refs는 거부 또는 프로젝트 상대 참조로 정규화되며, 비밀값은 공통 redact 경로를 통과해 원문이 JSONL에 없음. "내부 사고 과정 금지"는 문자열 탐지가 아니라 이 화이트리스트로만 판정한다 | CLI security integration, 파일 byte 검색 | 구현 전 RED |
| S-4 | AC-3, AC-8, C-1, C-4, C-5, C-6, H-1 | 미완료 user confirmation 2건 뒤에 진입 대상 행이 있는 agentic schema 1.2 태스크 | `state-tool advance`/`mark`로 복합 전이를 1회 실행하고 state·pending_events·JSONL을 비교 | 자동 승인 2건과 대상 행 1건이 각각 독립 `state.changed`로 남고 순서·from/to·row key가 `state.json`과 일치하며, 일부 admission만 되는 상태가 없음 | subprocess integration, 실제 state/JSONL/outbox 검사 | 구현 전 RED |
| S-5 | AC-4, C-4, C-5 | shadow/active 각각에 동일 worker run과 gate id를 준비 | worker started→activity→completed와 신규 구현되는 `gate-request`→`gate-resolve`(surfaces.json 선언·현재 미구현)를 실행하고, 요청 없는 resolve·중복 resolve도 시도 | 정상 순서는 두 모드에서 같은 worker/gate 사건으로 남고, 선행 요청 없음·중복 해결은 무변경 구조화 오류로 거부됨 | CLI integration, 실제 JSONL·exit code | 구현 전 RED |
| S-6 | AC-5, C-1, C-5, H-1 | 쓰기 불가 조각 또는 관측 불가 worker boundary를 갖는 shadow run | 상태 전이와 완전성 검사를 실행하고 반환 warning·pending outbox·missing 분류를 조회 | 상태 전이는 완료되고 exit 0을 유지하며, 누락 범위와 원인이 `run_log_pending`/recoverable 여부 또는 표준 missing 진단으로 식별됨 | failure-injection integration, 실제 권한·파일 I/O | 구현 전 RED |
| S-7 | AC-6, C-2, H-4 | completion profile이 요구하는 trusted worker/gate/state 증거가 누락되거나 모순된 active fixture와 profiles.json에 없는 channel | active 완료 전이와 미승인 channel의 active init을 각각 시도 | 증거 부족·모순은 기존 completion gate가 완료를 거부하고, 미승인 channel은 `profile_not_found`로 거부되며 임의 profile 승격이 없음 | CLI integration, active contract fixture | 구현 전 RED |
| S-8 | AC-7, AC-8, C-3 | TASK 완료 보고 직후 모델 턴이 종료된 opal-studio 재현형 fixture | `state-tool verify --run-log-completeness-check`를 실행해 반환 payload의 `last_observed_decision`·`last_observed_state_change`·`last_observed_boundary` 3필드와 missing 진단을 조회 | 대화 원문이나 `AGENTIC-LOG.md` 없이 세 필드가 서로 다른 `event_id`/`ts`로 채워져 세 지점이 구분되고, 다음 stage 진입 행이 `missing_state_changed`에 실려 관측 중단 사실이 복원됨. 사람 판독이 아니라 3필드 값 일치로 판정한다 | CLI integration, 반환 JSON 필드 단언 + 내부 재현 fixture | 구현 전 RED |
| S-9 | AC-8, C-4, C-5, H-3 | 순번·스키마·provenance는 유효하지만 자동 승인 `state.changed` 1건을 뺀 JSONL | `run-log-tool validate-run`과 `state-tool verify --run-log-completeness-check`를 순서대로 실행 | 전자는 조각 구조만 유효하므로 통과하고, 후자는 빠진 row/event를 정확히 누락으로 보고하며 run-log-core가 state.json을 읽지 않는 의존 방향이 유지됨 | CLI integration + 정적 import/헤더 검사 | 구현 전 RED |
| S-10 | AC-8, C-5, C-6, H-1 | schema 1.0/1.1, run_log 블록 부재, 중복 request_id, 조각 경계, 동시 append, symlink/경로 이탈, secret 입력 fixture | 기존 state-tool/run-log-tool 회귀 스위트와 신규 시나리오를 전건 실행 | legacy 상태·통계·완료 동작의 바이트/응답 계약이 유지되고 append-only·멱등·순번·락·마스킹·경로 방어 회귀가 모두 통과함 | subprocess regression/security suite | 구현 후 |
| S-11 | AC-1, AC-2, AC-4, AC-5, AC-8, C-7, H-5 | 구현된 CLI·진단 표면과 개정된 PRD/TRD/CONTRACT/surfaces/README | 문서별 책임 경계, surfaces request/response/error 집합, 실제 `--help`와 오류 코드를 결정론적으로 대조 | PRD는 목표, TRD는 흐름/책임, CONTRACT는 필드·인터페이스, surfaces는 선언 시점부터 보유한 `log-event`/`gate-request`/`gate-resolve` 공개 표면만 소유하며(신규 표면 추가 0건) 중복 규범 정의와 구현 드리프트가 없음 | static contract test + 실제 CLI 표면 대조 | 구현 후 |
