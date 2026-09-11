# OPAL 태스크 전체 여정 실행 로그 설계 제안서

> 상태: 3차 개정 제안
> 작성: 알투(PM)
> 작성일: 2026-09-10
> 개정 기준일: 2026-09-11
> 목적: 태스크 전체 실행 여정과 워커 작업 궤적을 중복 없이 보존하고, 도구로 검증 가능한 분석 원천을 마련한다.

---

## 1. 결론

OPAL은 태스크 실행 이력을 `tasks/{태스크 폴더}/run/run-log-{run_id}-{segment}.jsonl`의
순서 있는 표준 이벤트 segment로 기록한다. 이하 이 segment 집합을 `run-log`라고 부른다.
다만 첫 구현에서 모든 사건을 포괄하지 않는다. 현재 실제로 사용 중인 `AGENTIC-LOG.md`,
`state.json`, `.oppl-run/`을 먼저 정리하고, 워커 궤적과 상태 전이에 필요한 최소 계약만 도입한다.

1차 도입 원칙은 다음과 같다.

1. `run-log` segment 집합은 태스크 실행 이력의 유일한 표준 원천이다.
2. `state.json`은 현재 상태 SSOT이며 실행 이력의 활성화 여부와 현재 `run_id`를 소유한다.
3. `AGENTIC-LOG.md`의 판단·오류·수정·에스컬레이션 기록은 표준 이벤트로 흡수하고 신규 태스크에서 폐지한다.
4. `.oppl-run/`은 플랫폼 원본 증거로 유지하되 표준 로그로 단방향 변환한다.
5. 워커 완료는 신뢰 가능한 worker provenance를 가진 의미 있는 작업 사건이 있어야 인정한다.
6. 원본 출력은 기본 수집하지 않고 `run/raw/`만 git 추적에서 제외하며, 마스킹된 표준 로그는 태스크 증거로 추적한다.
7. 2단 상태 커밋, 일반화된 correction 체인, Console 분석 화면은 1차 범위에서 제외한다.
8. 상태 로그 장애는 현재 상태로 과거를 추정하지 않고 `state.json`의 bounded outbox를 재전송해 복구한다.
9. activity와 terminal은 서로 다른 시점에 관측된 증거여야 하며 하나의 완료 알림을 둘로 분해하지 않는다.
10. 전체 도입은 core shadow → 2개 pilot enforcement → 나머지 pilot 확산으로 나눈다.

---

## 2. 적용 범위

### 2.1 포함

태스크 폴더와 `state.json`을 생성하는 표준 pipeline 실행을 대상으로 한다.

- `opd`, `opds`, `opdw`, `opp`, `opwt`, `opgc`, `oppd`, `opsdd`, `oppl`, `opdd`
- 각 pipeline의 동적 하위 태스크와 워커 실행
- PM·사용자 게이트 및 `state-tool` 상태 변경

단계 목록은 각 pilot의 `pipeline.json`과 `state-tool` 스키마가 소유한다.

### 2.2 제외

다음 실행은 태스크 폴더가 없으므로 이 계약을 적용하지 않는다.

- L2 경량 트랙
- `opbr` 등 태스크 pipeline을 만들지 않는 operator
- PM의 읽기 전용 분석과 일반 비서 작업

이 실행들의 관측성이 필요하면 태스크 로그를 억지로 재사용하지 않고 별도의 session log 제안으로 다룬다.
`opgc`는 태스크 폴더와 `state.json`을 생성하므로 포함 대상이다.

---

## 3. 현행 자산과 전환 결정

### 3.1 자산 역할

| 자산 | 현행 역할 | 개정 후 역할 | 결정 |
|---|---|---|---|
| `state.json` | 행 상태·현재 상태·다음 액션·행별 시각/주체/워커 시간 | 현재 상태 SSOT + 로그 계약·현재 run·bounded outbox | 확장 |
| `STATE.md` | 의사결정·블로커 저널 | state·outbox의 사람이 읽는 파생 저널; 실행 사건 원천 아님 | 역할 축소 |
| `AGENTIC-LOG.md` | 게이트·오류·수정·판단·재시도·에스컬레이션 | 표준 `activity`·terminal 이벤트로 흡수 | 신규 생성 폐지 |
| `.oppl-run/` | oppl stdout·stderr·prompt·exitcode·journal 원본 | 채널 원본 증거 | 유지, 단방향 변환 |
| `run/run-log-{run_id}-{segment}.jsonl` | 없음 | 태스크 실행 이력의 순서 있는 segment 집합 SSOT | 신규 |
| `run/raw/` | 없음 | 명시적 opt-in 원본 | 신규, 기본 미생성 |

### 3.2 `state.json`의 정확한 한계

`state.json`에는 이미 다음 정보가 있다.

- 태스크 생성·갱신 시각
- 행별 `timestamp`, `owner`, `note`
- `worker_duration_minutes`, `worker_duration_unknown`

한계는 정보가 전혀 없다는 것이 아니라, 행당 `timestamp`가 하나뿐이고 `advance`, `mark`, `block` 때
덮어써져 전이 과정과 워커의 중간 판단·검증·재시도를 복원할 수 없다는 점이다.

검토한 대안은 다음과 같다.

| 대안 | 장점 | 기각 이유 |
|---|---|---|
| `state.json.rows[]` 필드만 확장 | 신규 파일·도구가 적음 | 현재 상태와 무제한 이력이 결합되고 동시 append가 어려움 |
| `state.json.events[]` 추가 | 단일 JSON에서 조회 가능 | 상태 갱신마다 전체 파일 rewrite, 손상·락 경합·크기 증가 |
| 별도 JSONL | append·스트리밍·부분 복구·도구 분석에 적합 | 자산 1개 증가 |

따라서 별도 JSONL을 채택하되, 중복 자산을 먼저 제거하고 1차 이벤트 수를 제한한다.

### 3.3 `AGENTIC-LOG.md` 전환

신규 로그 계약이 활성화된 태스크에서는 `AGENTIC-LOG.md`를 만들지 않는다.

| 기존 태그 | 표준 매핑 |
|---|---|
| `GATE` | `activity`, `data.kind=decision` 또는 `state.changed` |
| `ERROR` | `activity`, `data.kind=validation` 또는 `worker.failed` |
| `FIX` | `activity`, `data.kind=retry` |
| `DECISION`, `IMPROVE` | `activity`, `data.kind=decision` |
| `ESCALATION` | `worker.blocked` 또는 `activity`, `data.kind=decision` |

기존 태스크의 파일은 역사 증거로 보존하며 일괄 변환하지 않는다. 필요 시 별도 import 명령으로만
변환하고, 공통 `provenance.source`에 원본 경로·행 번호·hash를 남겨 중복을 식별한다.

### 3.4 Project Loop 전환

`.oppl-run/`은 raw source이고 `run-log` segment 집합이 표준 실행 이력 SSOT다.

- 변환 방향: `.oppl-run/` → `run-log` 단방향
- 역변환: 금지
- 멱등 키: `provenance.source.id + upstream_event_id`; 원본 ID가 없으면 `source.id + locator + sha256`
- `journal.md`의 start/end/gate-verdict/retry/blocked도 같은 변환기를 사용한다.
- 원본과 표준 이벤트가 함께 있어도 집계기는 표준 이벤트만 집계한다.

---

## 4. 1차 표준 이벤트

### 4.1 이벤트 집합

| 이벤트 | 주체 | 필수 조건 | 의미 |
|---|---|---|---|
| `run.started` | `state-tool` | run마다 1건 | 실행 시작과 식별자 확정 |
| `state.changed` | `state-tool` | 상태 변경 성공 시 | 커밋된 현재 상태의 관측 사건 |
| `worker.started` | worker | 워커마다 1건 | 실제 워커 실행 시작 |
| `activity` | worker/PM | 정상 완료 워커마다 신뢰 가능한 worker 사건 1건 이상 | 의미 있는 진행·판단·검증·재시도 |
| `worker.completed` | worker | 성공 종료 시 1건 | 정상 종료·결과·실행 시간 |
| `worker.failed` | worker | 실패 종료 시 1건 | 실패 종료·원인 |
| `worker.blocked` | worker | 외부 조건 필요 시 1건 | 차단 종료·필요 조건 |
| `gate.requested` | PM | 모든 PM·사용자 gate 요청 시 1건 | 요청 시각·대상·요청 주체 |
| `gate.resolved` | PM/user/auto | 요청된 gate 해결 시 1건 | 판정·판정 주체·해결 시각 |
| `run.completed` | `state-tool` | CLOSE 또는 명시적 restart로 run 종료 시 1건 | 실행 종료와 종료 사유 |

`activity.data.kind`는 1차에서 `progress | decision | validation | retry`만 허용한다.
heartbeat, artifact별 변경 이벤트, requested/committed 2단 이벤트, correction 이벤트는 1차에 넣지 않는다.

### 4.2 워커 완료 게이트

워커 완료로 인정하려면 같은 `worker_run_id`에 다음이 모두 있어야 한다.

1. `worker.started` 1건
2. 정상 완료면 §4.3의 trusted worker `activity` 1건 이상
3. `worker.completed | worker.failed | worker.blocked` 중 정확히 1건
4. terminal 이벤트의 결과 또는 원인
5. `duration_ms` 또는 `duration_unknown_reason`

`activity`는 단순 heartbeat가 아니라 결과에 영향을 준 작업 경계를 기록한다. 짧은 작업도
“대상 확인 → 변경 또는 판정 완료”를 1건으로 남긴다. 이 조건은 프롬프트 권고가 아니라
`run-log-tool validate-worker`와 `state-tool mark`의 완료 게이트로 집행한다.

### 4.3 기록 주체와 증거 신뢰

`actor`는 사건을 수행한 의미상 주체이고 `recorded_by`는 파일에 기록한 주체다. 둘을 섞지 않는다.

| 경로 | actor | provenance.type / recorded_by | 필수 provenance | 워커 완료 게이트 기여 |
|---|---|---|---|---|
| 워커 직접 기록 | `worker` | `direct / worker` | `worker_log_token_id` + 서로 다른 호출의 source ID/hash/observed_at | 가능 |
| adapter가 워커 중간 메시지를 변환 | `worker` | `adapter / adapter` | `source.kind/id/sha256/observed_at` | 가능 |
| legacy·oppl import | 원본 의미 주체 | `import / tool` | `source.id/locator/sha256` | 불가 |
| PM이 자기 판단 기록 | `PM` | `direct / PM|tool` | 호출 event ID | 불가 |
| PM이 워커 대신 작성 | `worker` | `direct / PM` | 허용하지 않음 | 불가·스키마 거부 |

trusted worker event는 `actor.kind=worker`, `provenance.type=direct|adapter`, 그리고
`provenance.recorded_by.kind=worker|adapter`를 모두 만족한 사건이다. adapter 경로는 원본
메시지·프로세스 결과의 ID, hash, 관측 시각이 검증돼야 한다. `provenance.type=import`는 actor가
worker여도 현재 워커 완료 게이트에 기여하지 않는다. PM의 자유 문장으로 worker actor를 지정한
사건은 append 단계에서 거부한다.

같은 `worker_run_id`에서 정상 완료를 충족하는 activity와 terminal은 다음 불변식을 지킨다.

- activity와 terminal의 `provenance.source.id`는 서로 달라야 한다.
- activity와 terminal의 `provenance.source.sha256`도 서로 달라야 한다.
- activity의 `provenance.source.observed_at`과 이벤트 timestamp가 terminal보다 앞서야 한다.
- 하나의 완료 메시지·완료 알림을 locator, offset, part로 분할해 activity와 terminal을 함께 만들 수 없다.
- adapter activity는 완료 알림 이전에 실제 수신된 중간 메시지나 stream 사건에서만 생성한다.
- 중간 메시지가 없는 Agent 채널은 워커 직접 activity가 없으면 정상 완료 게이트를 통과하지 못한다.

작업 활동 전 즉시 실패·차단만 terminal의 `reason_code=pre_activity_failure`로 activity 부재를
대체할 수 있다. 이 terminal은 `provenance.recorded_by.kind=adapter`이고 `provenance.source.kind`가
`process_exit | agent_error`이며 exitcode 또는 오류 envelope hash가 있을 때만 유효하다.

### 4.4 게이트 대기 계약

- gate 요청 전에 `gate.requested`를 기록하고 고유 `gate_id`를 발급한다.
- 해결 시 같은 `gate_id`로 `gate.resolved`를 기록한다.
- 두 사건은 `state-tool gate-request/gate-resolve`를 통해 outbox와 run-log에 기록한다.
- 사용자 응답, PM 판정, 자동 승인 여부는 `actor.kind`로 구분한다.
- 대기 시간은 같은 `gate_id`의 requested·resolved UTC timestamp 차이로만 계산한다.
- resolved만 있거나 중복 resolved가 있으면 `run_log_inconsistent`다.
- Phase 2 분석은 Phase 1에서 쌓인 두 사건만 소비하며 과거 요청 시점을 추정하지 않는다.

---

## 5. 공통 이벤트 계약

```json
{
  "schema_version": "1.0",
  "event_id": "evt_550e8400-e29b-41d4-a716-446655440000",
  "sequence": 42,
  "actor_sequence": 7,
  "timestamp": "2026-09-11T03:32:08.123Z",
  "task_id": "116-260911-opds-부트-행동-필요-브리핑",
  "run_id": "run_550e8400-e29b-41d4-a716-446655440000",
  "parent_run_id": null,
  "worker_run_id": "wrk_550e8400-e29b-41d4-a716-446655440000",
  "caused_by_event_id": null,
  "stage": "EXECUTE",
  "task_step": "execute.implement",
  "work_item": "F-003",
  "gate_id": null,
  "event": "activity",
  "actor": {
    "kind": "worker",
    "id": "opal-task-agent",
    "provider": "codex",
    "session_id": "..."
  },
  "provenance": {
    "type": "adapter",
    "recorded_by": {
      "kind": "adapter",
      "id": "agent-tool-adapter"
    },
    "worker_log_token_id": null,
    "source": {
      "kind": "agent_message",
      "id": "msg_...",
      "sha256": "...",
      "observed_at": "2026-09-11T03:31:42.041Z",
      "locator": null,
      "upstream_event_id": null
    }
  },
  "summary": "state-tool 기록 경로 구현 완료",
  "reason": null,
  "duration_ms": null,
  "duration_unknown_reason": null,
  "refs": ["opal/tools/state-tool/state_tool.py"],
  "data": {"kind": "progress"}
}
```

### 5.1 주체와 provenance enum

| 필드 | 허용값 | 제약 |
|---|---|---|
| `actor.kind` | `worker | PM | user | auto | tool` | 의미상 사건 수행자. adapter와 importer는 actor가 아님 |
| `provenance.type` | `direct | adapter | import` | 수집 경로 |
| `provenance.recorded_by.kind` | `worker | PM | adapter | tool` | 사건을 제출·변환한 주체 |
| `source.kind` | `worker_event | agent_message | stream_event | process_exit | agent_error | legacy_line | oppl_event` | type별 허용 조합을 schema `if/then`으로 검사 |

- worker lifecycle 사건의 `actor.kind`는 `worker`만 허용한다.
- PM activity와 `gate.requested`는 `PM`, `gate.resolved`는 `PM | user | auto`만 허용한다.
- `run.started/completed`, `state.changed`의 actor는 `tool`만 허용한다.
- `provenance.type=direct` worker 사건은 token ID가 필수다.
- direct worker source ID·관측 시각은 run-log-tool이 append 호출마다 발급하고, SHA-256은 정규화한 제출 payload로 계산한다.
- `provenance.type=adapter`는 source ID·SHA-256·`observed_at`, import는 source ID·SHA-256·`locator`가 필수다.
- import는 `recorded_by.kind=tool`만 허용하고 trusted worker 판정에서 항상 제외한다.

### 5.2 식별자와 시간

- `run_id`: `state-tool init`이 `run_<UUIDv4>`로 발급한다.
- `event_id`: `run-log-tool append`가 `evt_<UUIDv4>`로 발급한다.
- `worker_run_id`: 디스패치마다 PM 또는 adapter가 `wrk_<UUIDv4>`로 발급한다.
- `worker_log_token_id`: 디스패치가 해당 `worker_run_id`에 묶어 발급한 쓰기 capability의 식별자다. 비밀 token 원문은 로그에 넣지 않는다.
- 최초 실행은 `state-tool init` 시 새 run이다.
- 프로세스·세션 재접속과 동일 워커 resume는 기존 run과 `worker_run_id`를 유지한다.
- 명시적 재실행은 `state-tool restart-run --reason`만 새 run을 발급한다.
- 동적 하위 태스크는 별도 run을 만들고 `parent_run_id`로 직계 상위 run을 가리킨다.
- timestamp는 UTC RFC 3339 밀리초 형식만 저장한다. KST 등 로컬 시간은 표시 계층에서 변환한다.
- `duration_ms`는 monotonic clock으로 측정하고 timestamp 차분으로 만들지 않는다.

현행 `state.json`의 timezone 없는 시각은 `Asia/Seoul`로 해석한 뒤 UTC로 변환한다. 이 규칙은
legacy import에만 사용하며 신규 이벤트 시각을 state timestamp에서 역산하지 않는다. Console의
`quietHours`에는 `timeZone`을 추가하고, 미설정 시 기존 동작과 같은 `Asia/Seoul`을 사용한다.
Phase 2에서 UTC 이벤트를 집계할 때도 quietHours 구간을 이 timezone으로 변환한 뒤 겹침을 계산한다.

### 5.3 순서와 인과관계

`sequence`는 파일 잠금을 획득해 append된 run 전체 저장 순서일 뿐 인과 순서가 아니다.

- `sequence`는 run 전체에서 1부터 단조 증가하며 segment가 바뀌어도 리셋하지 않는다.
- `actor_sequence`는 worker면 `worker_run_id`, 그 외에는 `(actor.kind, actor.id)` 범위에서 1부터 단조 증가한다.
- 두 순번은 task transaction lock 안에서 마지막 segment와 필요한 이전 actor 사건을 확인한 뒤 발급한다.
- segment 정렬은 번호, 사건 정렬은 run-global `sequence`를 사용한다.
- 직접적인 원인 관계가 있을 때만 `caused_by_event_id`를 기록한다.
- 워커 내부 궤적은 `worker_run_id + actor_sequence`로 복원한다.
- 서로 다른 병렬 워커 사이에 원인 링크가 없으면 동시 실행으로 취급하며 전체 인과 순서를 추정하지 않는다.
- 분석기는 `sequence`만으로 PLAN 병렬 그룹의 선후관계를 만들지 않는다.

---

## 6. 활성화와 장애 계약

### 6.1 활성화 SSOT

`run-manifest.json`은 만들지 않는다. 삭제 가능한 별도 파일을 기능 스위치로 쓰지 않기 위해
`state.json` 스키마 1.2의 필수 블록이 로그 계약을 활성화한다.

```json
{
  "schema_version": "1.2",
  "run_log": {
    "contract_version": "1.0",
    "mode": "active",
    "active_run_id": "run_...",
    "status": "active",
    "pending_events": []
  }
}
```

- 신규 태스크: `state-tool init --run-log-mode shadow|active`가 스키마 1.2와 `run_log`를 함께 생성한다.
- init의 첫 원자 쓰기는 `status=pending`과 compact `run.started` outbox 사건을 함께 저장한다. 이후 첫 segment 생성·멱등 append·outbox 제거가 성공해야 `status=active`가 된다.
- init 중단으로 run 디렉터리나 첫 segment가 없어도 pending `run.started`가 있으면 `run_log_missing`이 아니라 복구 가능 초기화로 판정한다.
- 이 상태의 `reconcile`은 run 디렉터리와 `0001` segment를 생성한 뒤 outbox를 재전송할 수 있다.
- legacy: 스키마 1.0/1.1이며 `run_log`가 없는 태스크만 해당한다.
- 1.2 active에서 outbox 복구 근거 없이 `run/`이나 로그가 사라지면 legacy로 강등하지 않고 `run_log_missing`으로 진단한다.
- `state.json` 손편집으로 계약을 제거하면 스키마 검증 실패다.
- `pending_events`는 사건당 UTF-8 4 KiB 이하의 compact 표준 payload를 최대 128건 보관하는 bounded outbox다. 일반 사건은 126건까지이며 마지막 2칸은 사용자 override 결정과 강제 `state.changed` 전용이다.
- 4 KiB를 넘는 PM 설명·증거는 먼저 별도 파일에 원자 저장하고 outbox에는 상대 경로와 SHA-256만 넣는다. 증거 파일 생성 실패 시 상태 전이를 시작하지 않는다.
- `mode`는 `shadow | active`다. shadow는 Phase 1A의 비교 기록으로 완료 게이트에 관여하지 않고, active만 표준 실행 이력 SSOT·완료 게이트로 사용한다.
- `status`는 `active | pending | overridden`이며 outbox와 상태 전이 규칙으로만 바뀐다.

이는 §3.2에서 기각한 무제한 `state.json.events[]`와 다르다. 정상 이력은 run-log에만 있고 outbox는
장애·중단 사이의 미전송 사건만 일시 보유한다. 최악 크기는 payload 기준 512 KiB이며 정상 호출은
같은 task transaction lock 안에서 즉시 비운다. 이 임시 rewrite 비용을 상태·사건 원자성의 비용으로 수용한다.

### 6.2 상태 변경과 로그 실패

1차에서는 requested/committed 사건 쌍을 도입하지 않고 transactional outbox를 사용한다.

1. `state-tool`이 상태 변경 결과와 compact `state.changed` 이벤트를 함께 구성하고 event ID·UTC 시각을 확정한다.
2. 상태 변경과 이벤트의 `pending_events` 추가를 한 번의 `state.json` 원자 쓰기로 커밋한다.
3. 커밋 뒤 `run-log-core`가 같은 event ID를 표준 로그에 멱등 append한다.
4. append 성공 시 두 번째 원자 쓰기로 outbox 사건을 제거하고, 실패·프로세스 중단 시 그대로 둔다. 2~4는 같은 공개 호출과 task transaction lock 안에서 동기 실행한다.
5. `pending_events`가 비어 있지 않으면 `run_log.status=pending`이며 워커 완료 mark와 CLOSE를 차단한다.
6. `reconcile`은 outbox의 완전한 사건만 재전송하고 현재 행 timestamp나 stdout에서 과거 사건을 합성하지 않는다.
7. append 성공 후 outbox 제거 전에 중단돼도 같은 event ID의 멱등 append 후 안전하게 제거한다.
8. 일반 사건 126건 도달 시 추가 상태 전이는 차단하고 reconcile 또는 예약된 2칸의 사용자 override만 허용한다.

outbox는 `state.changed`, `run.started/completed`, `gate.requested/resolved`, PM의 `activity`처럼
state-tool이 소유하거나 중개하는 사건에 적용한다. 워커 직접·adapter 사건은 `run-log-tool`이
표준 로그에 직접 append하며, 실패하면 terminal 검증이 성립하지 않아 완료가 차단된다.

자동 복구가 불가능하고 로그 장애가 지속되면 다음 break-glass만 허용한다.

```text
state-tool mark ... --run-log-override --owner user --note "사유"
```

- 사용자 명시 승인과 사유가 모두 있어야 한다.
- override는 승인된 상태 변경, `activity(kind=decision)`, 강제 `state.changed`를 같은 원자 쓰기로 커밋하고 두 사건을 예약 슬롯에 기록한다.
- 이때 `run_log.status=overridden`으로 두며 해당 전이 1건 뒤에는 reconcile 외 추가 전이를 허용하지 않는다.
- `STATE.md`에는 이 사건의 `event_id`와 복구 필요 상태만 파생 표시하고 별도 decision 원문을 만들지 않는다.
- 로그가 복구되면 `reconcile`이 두 outbox 사건을 그대로 이관하고 outbox를 비운 뒤 `status=active`로 복귀한다.
- manifest 삭제나 PM의 임의 판단으로는 override할 수 없다.

### 6.3 오류 코드

| 오류 코드 | 조건 | 처리 |
|---|---|---|
| `run_log_write_failed` | 필수 워커 사건 append 실패 | 워커 완료 mark 차단 |
| `run_log_missing` | 활성 계약인데 로그 또는 필수 사건 부재 | 워커 완료·CLOSE 차단 |
| `run_log_pending` | outbox 사건이 표준 로그에 아직 반영되지 않음 | 한도 내 일반 진행 허용, 완료·CLOSE 차단 |
| `run_log_outbox_full` | 일반 outbox 126건 도달 | reconcile·예약 슬롯의 사용자 override 외 상태 전이 차단 |
| `run_log_inconsistent` | reconcile로 자동 확정 불가 | 사용자 override 또는 수동 복구 필요 |

### 6.4 도구 의존 방향

```text
run-log-core  ←  run-log-tool CLI
      ↑
  state-tool
```

- `run-log-core`는 명시적으로 받은 task path, run ID, event payload만 소비하며 `state.json`을 읽지 않는다.
- `state-tool`이 로그 활성화·현재 run·outbox를 소유하고 `run-log-core`를 호출한다.
- 워커는 디스패치 때 받은 run ID, worker run ID, worker log token으로 `run-log-tool append`를 호출한다.
- `run-log-tool validate-*`는 표준 로그와 명시 인자만 읽으며 state 활성 여부를 판정하지 않는다.
- legacy/active 판정과 완료 게이트의 조합은 상위 `state-tool`만 소유한다.
- 배포 순서는 `run-log-core/tool` 설치·검증 후 `state-tool` 1.2 활성화 순서다.

### 6.5 동시성·락 범위

- 태스크별 공용 배타 락은 `<task-path>/.opal-task.lock` 하나이며 gitignore 대상이다.
- 모든 state-tool 변경 명령과 run-log append/import/reconcile/segment roll은 이 락을 사용한다.
- state-tool 호출은 상태+outbox 원자 쓰기부터 segment 선택·sequence 발급·append·fsync·outbox 제거까지 락을 유지한다.
- 외부 run-log-tool CLI는 스스로 락을 획득한다. 락을 이미 가진 state-tool은 같은 프로세스의 `run-log-core(..., lock_held=true)`를 호출해 재획득하지 않는다.
- segment 상한 검사, 다음 번호 선택, 파일 생성은 같은 락 안에서 수행하므로 경계 roll은 정확히 한 프로세스만 실행한다.
- 다른 프로세스의 mark는 앞 호출이 append·outbox 제거를 마치거나 실패 상태로 락을 놓을 때까지 기다린다. 따라서 정상 호출의 일시적 pending을 관측해 오탐 차단하지 않는다.
- 별도 state lock이나 segment별 lock을 추가하지 않아 lock ordering과 교착을 만들지 않는다.

동시성 수용 테스트는 여러 프로세스를 segment 경계 직전에 barrier로 대기시킨다. 해제 후 새 segment
1개, run-global sequence 중복·누락 0건, actor sequence 단조성, JSON 행 개수, 정상 mark 오탐 0건을 함께 판정한다.

---

## 7. 시간 원천과 Console 정합성

워커 실행 시간의 원천은 terminal 이벤트의 `duration_ms` 하나다.

- `state.json.rows[].worker_duration_minutes`는 호환용 파생 투영이다.
- 변환식은 `floor(duration_ms / 60000)`이며 1분 미만은 `0`이다.
- `state-tool mark`가 terminal 이벤트를 읽어 자동 기록하며 PM이 별도 값을 입력하지 않는다.
- `duration_unknown_reason`이 있으면 `worker_duration_unknown=true`로 투영한다.
- `run-log-tool reconcile-duration`은 두 값이 변환식과 다르면 오류로 진단한다.

혼재 기간의 기존 CLI 계약은 다음처럼 전환한다.

| 대상 state | `--worker-duration-minutes` 처리 | `worker_duration_missing` 처리 |
|---|---|---|
| 1.0/1.1 | 현행 그대로 수용 | 현행 경고·CLOSE 계약 유지 |
| 1.2 | terminal 파생값과 같으면 수용 + deprecated 경고, 다르면 `worker_duration_conflict` | terminal/unknown 사건 부재를 기준으로 판정 |

Phase 1에서 모든 pilot 문서와 호출부를 자동 파생 방식으로 바꾸고, 호환 인자는 1.0/1.1 태스크
지원을 위해 유지한다. 실제 제거는 legacy 지원 종료 제안에서 별도 결정한다.

Console 1차는 기존 `state.json` 통계를 유지하되 이 파생 규칙을 검증한다. Console이
run-log segment를 직접 읽는 타임라인·재시도·병목 분석은 2차 범위다.

---

## 8. 보안·보존 정책

### 8.1 기본값

- `tasks/**/run/raw/`은 `.gitignore`에 등록한다.
- `<task-path>/.opal-task.lock`도 runtime 파일이므로 `.gitignore`에 등록한다.
- 마스킹과 스키마 검증을 통과한 `run/run-log-{run_id}-{segment}.jsonl`은 `state.json`과 함께 추적한다.
- run-log에는 구조화 요약과 상대 경로만 저장한다.
- stdout, stderr, 프롬프트 원문은 기본 수집하지 않는다.
- `run/raw/`은 사용자가 명시적으로 활성화한 실행에서만 생성한다.
- 공유가 필요하면 `run-log-tool export --sanitize`로 별도 정제본을 만든다.

### 8.2 표준 로그 segment와 보존

- 파일명: `run-log-{run_id}-{segment:04d}.jsonl`
- 이벤트 직렬화 상한: UTF-8 16 KiB. 초과 사건은 `event_too_large`로 거부하고 자동 raw 저장이나 무음 절단을 하지 않는다.
- segment 상한: 4 MiB. 다음 append가 상한을 넘으면 새 번호 segment를 원자 생성한다.
- 정렬: 같은 run은 segment 번호 오름차순, segment 내부는 `sequence` 오름차순이다.
- 닫힌 segment는 다시 수정하지 않으며 현재 마지막 segment만 append한다.
- 표준 사건은 태스크 감사 증거이므로 개별 삭제·TTL을 적용하지 않고 태스크와 같은 기간 보존한다.
- 누적 용량은 `run-log-tool validate-run`이 보고한다. 완료 태스크의 외부 이전은 Phase 2에서 태스크 폴더 전체를 단위로 수행하며 로그만 떼어내지 않는다.

이 정책은 전체 증거가 태스크 수에 따라 증가한다는 비용을 의도적으로 수용한다. 고정 크기 segment로
활성 파일의 diff와 손상 반경을 제한하며, 보존 비용이 허용되지 않는 프로젝트는 도입 전에
프로젝트 전체의 로그 추적 정책을 별도 승인해야 한다.

### 8.3 디스크 기록 전 마스킹

모든 adapter와 raw writer는 파일 쓰기 전에 공통 redactor를 통과한다.

- 환경변수형 secret, bearer/token, API key, private key 블록을 마스킹한다.
- 프로젝트 `docs/SECURITY.md`의 추가 패턴을 병합한다.
- 마스킹 불가로 판정된 원본은 저장을 거부하고 메타데이터 사건만 남긴다.
- raw 기본 상한은 파일당 10 MiB·run당 100 MiB·7일이며, effective setting으로 더 작게만 조정할 수 있다.
- raw writer는 상한 초과 시 저장을 중단하고 `raw_capture_limited` 메타 사건만 남긴다.
- raw 파일 기본 권한은 소유자 읽기·쓰기 전용이다.
- 보안 테스트는 “로그에 넣지 않는다”는 문구가 아니라 실제 fixture secret이 디스크에 남지 않는지 판정한다.

Phase 1은 `.oppl-run/` writer도 디스크 기록 전에 같은 redactor를 통과하도록 변경한다.
그 전까지 생성된 legacy 원본은 기존처럼 gitignore 상태를 유지하고, 표준 로그로 가져올 때 다시 마스킹한다.

---

## 9. `run-log-tool` 1차 인터페이스

```text
run-log-tool init               --task <task-path> --run-id <id>
run-log-tool begin-worker       --task <task-path> --run-id <id> --actor-id <id>
run-log-tool append             --task <task-path> --run-id <id> --event <type> ...
run-log-tool validate-worker    --task <task-path> --worker-run-id <id>
run-log-tool validate-run       --task <task-path> --run-id <id>
run-log-tool reconcile          --task <task-path>
run-log-tool reconcile-duration --task <task-path>
run-log-tool import-agentic     --task <legacy-task-path>
run-log-tool import-oppl        --task <task-path>
run-log-tool show               --task <task-path> [--run-id <id>]
run-log-tool export             --task <task-path> --sanitize

state-tool restart-run          <task-path> --reason <text>
state-tool log-event            <task-path> --event activity ...
state-tool gate-request         <task-path> --gate-id <id> ...
state-tool gate-resolve         <task-path> --gate-id <id> ...
```

`begin-worker`는 `worker_run_id`와 1회 디스패치 범위의 worker log token을 발급한다. token 원문은
worker 실행 컨텍스트에만 전달하고 로그에는 token ID만 남긴다. `restart-run`은 기존 run을
`run.completed(reason=restart)`로 닫은 뒤 새 run ID를 발급하며, 미해소 outbox가 있으면 거부한다.
`log-event`는 PM actor 사건만 받으며 worker actor를 거부한다. gate 두 명령은 요청·해결 사건을
outbox로 중개하고 같은 gate ID의 유일성과 순서를 검사한다.

도구가 소유하는 공통 기능은 다음과 같다.

- JSON Schema 검증
- 파일 잠금과 한 줄 단위 append
- 4 MiB segment 원자 roll과 닫힌 segment 불변성
- `sequence`·`actor_sequence` 발급 및 역행 진단
- 이벤트·worker terminal 유일성 검증
- worker token·adapter source provenance 검증
- import 멱등성 검증
- 디스크 기록 전 redaction
- run별 집계

legacy/active 판정, 현재 run 선택, restart 허용 여부는 `state-tool`만 소유한다.

---

## 10. 단계별 도입

### Phase 1A — foundation + shadow pilot

단일 기반 태스크로 다음만 구현한다.

1. 폐쇄 enum·공통 provenance·서로 다른 시점 증거를 검증하는 `run-log-core/tool`
2. task transaction lock, run-global sequence, 동시 segment roll
3. `state.json` 1.2 compact outbox와 중단 가능한 init/reconcile
4. redactor·raw 상한·gitignore·UTC/KST 변환
5. `opds`(일반 Agent 채널)와 `oppl`(CLI/raw 채널) 두 pilot adapter

두 pilot은 `run_log.mode=shadow`로 실행한다. 이 기간에는 기존 AGENTIC-LOG가 현행 기록 원천이고
run-log는 비교 후보이므로 완료를 차단하지 않는다. shadow→active 승격에는 각 채널의 정상 완료,
중간 activity 없는 완료, 즉시 실패, 로그 쓰기 실패, 동시 roll 실증이 모두 필요하다.

### Phase 1B — 2개 pilot enforcement

1. `opds`·`oppl`만 `run_log.mode=active`로 승격
2. trusted worker 완료 게이트와 `gate.requested/resolved`
3. outbox reconcile·사용자 override·`restart-run`
4. duration 자동 투영과 1.0/1.1 CLI 호환
5. shared owner·state 문서를 `active면 run-log / legacy·shadow면 AGENTIC-LOG` 조건부 계약으로 개정
6. 두 pilot에서 active conformance와 기존 state/Console 회귀 검증

### Phase 1C — 나머지 pilot 확산

- 나머지 8개 pilot은 태스크당 최대 2개씩 배치해 adapter·SKILL·pipeline 계약을 확산한다.
- 각 배치는 자기 pilot conformance와 전체 state 회귀를 통과한 뒤 다음 배치로 진행한다.
- 마지막 배치에서 `task-process.md`, `parallel-execution.md`, 모든 pilot SKILL의 AGENTIC 무조건 기록 지시를 제거하고 기존 1.0/1.1 태스크의 계속 실행과 import를 위한 legacy 조건만 남긴다.
- R-11은 마지막 배치까지 10개 pilot 전부 통과해야 완료다.

Phase 1A·1B·1C는 각각 독립 승인·태스크·완료 기준을 가진다. 한 구현 태스크로 합치지 않는다.

### Phase 2 — 분석 소비

- Console 워커 타임라인
- 재시도·블로커·게이트 대기 분석
- `opal-action-monitor`의 표준 로그 reader 또는 별도 monitor
- 완료 태스크 폴더 전체의 외부 archive 연계; 표준 로그만 분리 삭제하지 않음

### Phase 3 — 필요성이 실증된 확장

- artifact 단위 이벤트
- correction 또는 invalidation 의미론
- session log와 L2 관측성
- 플랫폼별 raw capture 확장

Phase 2·3은 Phase 1C 실제 로그 표본으로 필요성과 비용을 검증한 뒤 별도 승인한다.

---

## 11. 요구사항·구현·검증 추적표

| ID | 요구사항 | 도입 단계 | 판정 방법 |
|---|---|---|---|
| R-1 | 신규 태스크는 삭제로 우회할 수 없는 로그 계약을 갖는다 | 1A state schema 1.2 + init | 중단 init은 pending outbox로 복구되고 active 로그 삭제는 `run_log_missing` |
| R-2 | 워커의 의미 있는 궤적을 남긴다 | 1A provenance, 1B gate | PM 대필·import·terminal과 같은 source는 기여하지 않고 앞선 별도 source만 인정 |
| R-3 | 워커 terminal은 정확히 하나다 | validate-worker | completed+failed 중복 거부 |
| R-4 | 병렬 기록이 손상되거나 정상 pending을 오탐하지 않는다 | 1A task transaction lock | 경계 동시 roll 1개·순번 중복 0·정상 mark 오탐 0 |
| R-5 | 저장 순서와 인과 순서를 혼동하지 않는다 | actor_sequence + caused_by | 병렬 fixture가 허위 선후관계를 만들지 않음 |
| R-6 | 상태 로그 장애가 state 전체를 교착시키거나 이력을 잃지 않는다 | 1A compact outbox, 1B override | 사건당 4 KiB·총 512 KiB 상한과 다중 누락 전이 멱등 복구 |
| R-7 | 워커 시간 원천이 하나다 | duration projection | ms→분 변환 및 불일치 진단 |
| R-8 | secret이 디스크에 남지 않는다 | redactor | token/private-key fixture 전 경로 0건 |
| R-9 | 기존 자산과 실행 사건을 이중 소유하지 않는다 | 1A import, 1B/1C 전환 | import는 멱등이고 완료 게이트에 불기여, STATE는 같은 event ID 포인터만 보유 |
| R-10 | 기존 state 동작이 회귀하지 않는다 | additive schema/adapter | 기존 state-tool 전체 테스트와 Console stats golden fixture 통과 |
| R-11 | 표준 pipeline 전부가 같은 계약을 지킨다 | 1B 2종, 1C 8종 확산 | 10개 skill별 init→worker→CLOSE conformance fixture 통과 |
| R-12 | 플랫폼 원본 형식과 표준 스키마가 분리된다 | 1A adapter contract | provider fixture별 동일 canonical event와 폐쇄 enum assertion |
| R-13 | PM·사용자 gate 대기 시간을 복원한다 | gate requested/resolved | 동일 gate ID 두 사건으로 대기 시간 재현, 요청 없는 resolved 거부 |
| R-14 | 도구 의존이 순환하지 않는다 | state-tool → run-log-core 단방향 | run-log-core/tool 테스트가 state fixture 없이 통과 |
| R-15 | AGENTIC 기록 계약을 이중 소유하지 않는다 | owner·harness·pilot 문서 동시 개정 | 무조건 생성 지시 0건, 남은 언급은 legacy·shadow·import 조건으로만 존재 |
| R-16 | 명시적 재실행만 새 run을 만든다 | restart-run | resume는 ID 유지, restart는 이전 run 종료·새 ID 발급 |
| R-17 | 추적 로그의 단일 파일 무한 증가를 막는다 | 4 MiB immutable segment | 경계 append에서 다음 segment 생성·순서 보존 |
| R-18 | 두 시간계를 일관되게 해석한다 | UTC event + Asia/Seoul legacy/quietHours | 날짜 경계·quietHours fixture 결과가 기존 Console과 일치 |

### 검증 주체

- `run-log-tool` 단위·동시성·redaction 테스트: 도구 테스트 스위트
- `state-tool` 회귀: 기존 전체 테스트 + 스키마 1.0/1.1 호환 fixture
- Console 회귀: 기존 stats golden fixture
- pipeline conformance: pilot별 통합 테스트
- 플랫폼 변환: 각 adapter가 소유한 canonical event fixture
- 최종 판정: `TEST-SCENARIO.md`의 R-1~R-18 매핑과 독립 test-agent 실행 결과

“기존 동작 회귀 없음”은 위 기준선이 모두 통과한다는 뜻이며, 단순 육안 확인으로 판정하지 않는다.

---

## 12. 수용 기준

- [ ] 신규 태스크의 `state.json` 1.2가 로그 계약과 현재 run을 가진다.
- [ ] init 중단으로 첫 segment가 없어도 pending `run.started`를 reconcile해 active로 복구한다.
- [ ] 활성 로그 파일을 삭제해도 legacy로 강등되지 않는다.
- [ ] 모든 포함 대상 skill의 정상 완료 워커가 trusted started + activity + terminal 계약을 통과한다.
- [ ] PM 대필 activity를 스키마가 거부하고 검증된 adapter source만 worker 증거로 인정한다.
- [ ] activity와 terminal의 source ID 또는 SHA-256 중 하나라도 같거나 activity 관측 시각이 늦으면 완료를 거부한다.
- [ ] 하나의 완료 알림을 locator·offset·part로 분해한 activity를 거부한다.
- [ ] `provenance.type=import` 사건은 actor가 worker여도 완료 게이트에 기여하지 않는다.
- [ ] 정의되지 않은 actor·recorded_by·source enum 조합을 스키마가 거부한다.
- [ ] activity가 없는 정상 완료를 차단하고 adapter 기계 증거가 있는 `pre_activity_failure`만 허용한다.
- [ ] 모든 PM·사용자 gate가 requested/resolved 쌍을 남기며 대기 시간을 재구성할 수 있다.
- [ ] segment 경계 동시 append에서 새 segment가 정확히 하나 생기고 run·actor 순번 중복과 누락이 없다.
- [ ] 정상 state 호출 중 다른 mark가 일시적 pending을 관측하지 않고 락 해제 뒤 올바른 결과를 받는다.
- [ ] `sequence`만으로 병렬 워커의 인과 순서를 만들지 않는다.
- [ ] 연속된 상태 로그 실패가 outbox에 전건 보존되고 reconcile 또는 사용자 override로 해소된다.
- [ ] outbox 사건은 각각 4 KiB, 전체 payload는 최대 512 KiB이며 초과 설명은 hash·경로만 저장한다.
- [ ] reconcile이 현재 state timestamp나 stdout에서 누락 사건을 합성하지 않는다.
- [ ] override 결정은 outbox가 소유하고 STATE.md에는 같은 event ID의 파생 표시만 남는다.
- [ ] `duration_ms`와 state 분 투영이 정의된 변환식과 일치한다.
- [ ] state 1.0/1.1 duration 인자는 유지되고 1.2의 불일치 수동 값은 거부된다.
- [ ] legacy KST·event UTC·quietHours timezone 변환이 날짜 경계에서도 일치한다.
- [ ] `run_log.mode=shadow`는 AGENTIC을 유지하고 완료를 차단하지 않으며, active 태스크만 AGENTIC을 생성하지 않는다.
- [ ] owner·harness·pilot 규범의 AGENTIC 무조건 생성 지시가 제거되고 남은 언급은 legacy·shadow·import로 한정된다.
- [ ] `.oppl-run/` import가 단방향·멱등이며 표준 로그만 집계된다.
- [ ] stdout·stderr·prompt는 opt-in 없이는 저장되지 않는다.
- [ ] secret fixture가 표준·raw·import 경로 어디에도 평문으로 남지 않는다.
- [ ] 마스킹된 run-log segment는 추적되고 `tasks/**/run/raw/`만 기본 git 추적 대상에서 제외된다.
- [ ] 4 MiB 경계에서 immutable segment가 순서대로 생성되고 기존 segment는 변경되지 않는다.
- [ ] resume는 run ID를 유지하고 `restart-run --reason`만 새 run을 발급한다.
- [ ] 기존 state-tool·Console 통계 기준선이 모두 통과한다.
- [ ] provider별 원본 fixture가 동일한 canonical schema로 변환된다.
- [ ] run-log-core/tool 테스트가 state.json이나 state fixture 없이 통과하여 R-14 단방향 의존을 입증한다.
- [ ] Phase 1A·1B와 1C의 pilot별 확산 배치가 각각 독립 태스크와 검증 결과를 가진다.

---

## 13. 최종 구조

```text
state-tool init
    ├── state.json 1.2: status=pending + run.started outbox
    ├── run/run-log-{run_id}-0001.jsonl 멱등 생성·append
    └── outbox 제거 + status=active

worker dispatch
    └── trusted worker.started → trusted activity 1건 이상 → terminal 1건

PM·사용자 gate
    └── gate.requested(gate_id) → gate.resolved(같은 gate_id)

state-tool transition
    └── 상태 + outbox 원자 커밋 → run-log 멱등 append → outbox 제거
                                  └── 실패: pending → reconcile | 사용자 override

legacy AGENTIC-LOG ──선택 import──┐
.oppl-run 원본 ─────단방향 import──┴→ run-log segment 집합
```

이 설계의 핵심은 로그 양을 늘리는 것이 아니다. 이미 존재하는 중복 기록을 하나의 표준 사건으로
흡수하고, OPAL이 중요하다고 선언한 워커 작업 궤적을 실제 완료 게이트로 집행하는 것이다.
