---
template: sdlc-v2
---
# CONTRACT: 태스크 실행 로그 표준화

> 1차 입력 SSOT: `docs/proposals/opal-task-run-log.md`
> 제약·수용 기준은 `TASK.md`, 무엇을 왜는 `PRD.md`, 기술 결정과 근거는 `TRD.md`가 소유한다.
> 이 문서는 **인터페이스 계약**(스키마·시그니처·경계)을 확정한다. 필드명·enum 값·명령명을 직접 쓰는 것이 이 문서의 정상 형태다.
> 기계검증절은 `surfaces.json`(같은 폴더)을 필수 구성요소로 포함한다.

---

## 1. 스키마 (Schema)

### 1.1 표준 사건 공통 필드

원천: 제안서 §5 payload 예시, §5.1 enum 표, §5.2 식별자·시간 규칙.

| 필드 | 타입 | 필수 | 값·제약 |
|---|---|---|---|
| `schema_version` | string | 필수 | 고정 `"1.0"` (사건 계약 버전. 상태 파일 `schema_version`과 별개) |
| `event_id` | string | 필수 | `evt_<UUIDv4>`. `run-log-core`가 발급 |
| `request_id` | string | 필수 | `req_<UUIDv4>` 또는 호출자가 재시도에도 유지하는 안정 문자열. `(run_id, request_id)`가 멱등 키 |
| `sequence` | integer | 필수 | run 전역 1부터 단조 증가. segment가 바뀌어도 리셋하지 않음 |
| `actor_sequence` | integer | 필수 | `actor.kind=worker`면 `worker_run_id` 범위, 그 외 `(actor.kind, actor.id)` 범위에서 1부터 단조 증가 |
| `timestamp` | string | 필수 | UTC RFC 3339 밀리초. 예 `2026-09-11T03:32:08.123Z`. 로컬 시각 저장 금지 |
| `task_id` | string | 필수 | 태스크 폴더명과 동일한 식별자 |
| `run_id` | string | 필수 | `run_<UUIDv4>`. `state-tool init` 또는 `restart-run`이 발급 |
| `parent_run_id` | string \| null | 필수(널 허용) | 동적 하위 태스크만 직계 상위 run을 가리킴. 그 외 `null` |
| `worker_run_id` | string \| null | 필수(널 허용) | `wrk_<UUIDv4>`. worker 계열 사건은 필수, 그 외 `null` |
| `caused_by_event_id` | string \| null | 필수(널 허용) | 직접적 원인 관계가 있을 때만 기록. 추정 금지 |
| `stage` | string \| null | 선택 | 파이프라인 단계 식별자 |
| `task_step` | string \| null | 선택 | `state.json`의 task step 키 |
| `work_item` | string \| null | 선택 | Work item 식별자 |
| `gate_id` | string \| null | 조건부 | `gate.requested`/`gate.resolved`에 필수, 그 외 `null` |
| `event` | string | 필수 | §1.2 사건 종류 12종 enum |
| `actor` | object | 필수 | §1.1.1 |
| `provenance` | object | 필수 | §1.1.2 |
| `summary` | string \| null | 조건부 | 사람이 읽는 1줄 요약. `activity`·terminal·gate 사건에 필수 |
| `reason` | string \| null | 조건부 | `worker.failed`/`worker.blocked`/`run.completed`에 필수 |
| `reason_code` | string \| null | 선택 | terminal 분류 코드. `pre_activity_failure` 포함 |
| `duration_ms` | integer \| null | 조건부 | terminal 사건에 필수(또는 `duration_unknown_reason`). 0 이상 |
| `duration_source` | string \| null | 조건부 | `adapter_monotonic` \| `worker_monotonic` \| `unknown` |
| `duration_unknown_reason` | string \| null | 조건부 | `duration_ms`가 `null`인 terminal에 필수 |
| `refs` | array\<string\> | 선택 | 프로젝트 상대 경로만. 절대 경로·원문 금지 |
| `data` | object | 조건부 | 사건별 추가 payload. §1.2 참조 |

- 직렬화 상한: UTF-8 **16 KiB**. 초과 시 `event_too_large`로 거부하며 자동 raw 저장이나 무음 절단을 하지 않는다(제안서 §8.2).
- 위에 정의되지 않은 최상위 키는 거부한다(폐쇄형 스키마).

#### 1.1.1 `actor`

| 필드 | 타입 | 필수 | 값 |
|---|---|---|---|
| `kind` | string | 필수 | `worker` \| `PM` \| `user` \| `auto` \| `tool` |
| `id` | string | 필수 | 에이전트명·도구명 등 안정 식별자 |
| `provider` | string \| null | 선택 | 플랫폼 제공자 식별자 |
| `session_id` | string \| null | 선택 | 채널 세션 식별자 |

adapter와 importer는 `actor`가 아니다. 사건을 **수행한 의미상 주체**만 `actor`다(제안서 §4.3).

#### 1.1.2 `provenance`

| 필드 | 타입 | 필수 | 값 |
|---|---|---|---|
| `type` | string | 필수 | `direct` \| `adapter` \| `import` |
| `recorded_by.kind` | string | 필수 | `worker` \| `PM` \| `adapter` \| `tool` |
| `recorded_by.id` | string | 필수 | 제출·변환 주체의 안정 식별자 |
| `worker_log_token_id` | string \| null | 조건부 | `type=direct` 이고 `actor.kind=worker`면 필수. **token 원문은 어떤 필드에도 넣지 않는다** |
| `source.kind` | string \| null | 조건부 | `worker_event` \| `process_start` \| `agent_handshake` \| `agent_message` \| `stream_event` \| `tool_result` \| `process_exit` \| `agent_error` \| `legacy_line` \| `oppl_event` |
| `source.id` | string \| null | 조건부 | `type=adapter`·`import`에 필수 |
| `source.sha256` | string \| null | 조건부 | `type=adapter`·`import`에 필수. 정규화 payload의 SHA-256 hex. **import 경로는 디스크에서 읽은 원본 바이트 그대로를 해싱한다** — 디코딩·치환·정규화 이전 값이다(PM 확정, T03 검사 의견) |
| `source.observed_at` | string \| null | 조건부 | `type=adapter`에 필수. UTC RFC 3339 밀리초 |
| `source.locator` | string \| null | 조건부 | `type=import`에 필수(원본 경로+행 번호 등) |
| `source.upstream_event_id` | string \| null | 선택 | 원본 사건 식별자. 있으면 import 멱등 키의 1순위 구성요소 |

#### 1.1.3 워커 쓰기 권한 식별자 3종의 관계

원천: 제안서 §5.2("비밀 token 원문은 로그에 넣지 않는다"), §6.4("원문이 아닌 SHA-256 hash·scope·만료만 기록하고 capability table에 투영한다. 비교는 constant-time").

| 이름 | 성격 | 어디에 존재하는가 | 로그에 남는가 |
|---|---|---|---|
| `worker_log_token` | **비밀 원문** | `run-log-tool begin-worker`의 stdout 1회, 그리고 워커 실행 컨텍스트의 메모리·인자 | **절대 남지 않는다.** 어떤 사건 필드·보관함·raw 경로에도 평문 금지 |
| `worker_log_token_id` | **식별자**(비밀 아님) | 사건의 `provenance.worker_log_token_id`, `worker.capability.revoked`의 `data.token_id`, 런타임 권한 테이블의 기본 키 | **남는다.** direct worker 사건의 필수 필드 |
| `data.token_sha256` | **검증자**(verifier) | `worker.capability.issued`의 `data` 안, 그리고 런타임 권한 테이블에 투영 | **남는다.** 원문을 복원할 수 없는 단방향 값 |

- 검증 절차: 호출자가 제시한 원문의 SHA-256을 `token_sha256`과 **constant-time** 비교한다. 원문을 저장하거나 다시 출력하지 않는다.
- 재구축: 런타임 권한 테이블은 `worker.capability.issued`의 `token_sha256`·`scope`·`expires_at`과 `revoked`·terminal·`run.completed`·만료를 함께 적용해 사건만으로 전량 재구축된다(§1.7, AC-9). 원문은 재구축에 필요하지 않다.
- `worker_log_token_id` 명명: `wlt_<UUIDv4>`.

### 1.2 사건 종류 12종과 추가 필수 조건

원천: 제안서 §4.1.

`mode`(`shadow` | `active`)는 기록할 사건 종류를 줄이지 않는다. 아래 12종 사건은 shadow·active 두 모드 모두 같은 표준 payload로 기록하며, mode에 따라 관측 가능한 사건 종류나 스키마가 달라지지 않는다. 두 모드의 차이는 §1.5가 정의하는 완료 게이트 기여 여부(active) 대 비차단 진단(shadow)뿐이다.

| `event` | 주체 | 유일성 | 추가 필수 조건 |
|---|---|---|---|
| `run.started` | `state-tool` | run마다 1건 | `actor.kind=tool`. `state-tool`이 outbox로 중개 |
| `state.changed` | `state-tool` | 상태 변경 성공마다 1건 | `actor.kind=tool`. `data.from`·`data.to`·`data.row_key` |
| `worker.started` | worker | `worker_run_id`마다 1건 | `actor.kind=worker`. active는 `source.kind ∈ {process_start, agent_handshake}` |
| `worker.capability.issued` | `run-log-tool` | 발급마다 1건 | `actor.kind=tool`, `recorded_by.kind=tool`. `data.token_sha256`·`data.scope`·`data.expires_at`. **token 원문 금지** |
| `worker.capability.revoked` | `run-log-tool` | terminal 전 조기 폐기 시 1건 | `actor.kind=tool`, `recorded_by.kind=tool`. `data.token_id`·`data.reason` |
| `activity` | worker / PM | 제한 없음 | `data.kind ∈ {progress, decision, validation, retry}`. `summary` 필수. active 강한 궤적 기여 조건은 §1.3·§1.5 |
| `worker.completed` | worker | `worker_run_id`마다 1건 | `actor.kind=worker`. terminal 공통 조건(아래) |
| `worker.failed` | worker | `worker_run_id`마다 1건 | `actor.kind=worker`. `reason` 필수. terminal 공통 조건 |
| `worker.blocked` | worker | `worker_run_id`마다 1건 | `actor.kind=worker`. `reason` 필수. terminal 공통 조건 |
| `gate.requested` | PM | `gate_id`마다 1건 | `actor.kind=PM`. `gate_id` 필수 |
| `gate.resolved` | PM / user / auto | `gate_id`마다 1건 | `actor.kind ∈ {PM, user, auto}`. `gate_id` 필수. 같은 `gate_id`의 `gate.requested` 선행 필수 |
| `run.completed` | `state-tool` | run 종료마다 1건 | `actor.kind=tool`. `reason` 필수(`close` \| `restart`) |

**terminal 공통 조건** (`worker.completed`/`failed`/`blocked`): 같은 `worker_run_id`에 정확히 1건. `duration_ms`+`duration_source` 또는 `duration_unknown_reason` 중 정확히 하나. active 모드는 `duration_source=adapter_monotonic`만 허용한다. `data.duration_spans[]`는 `{source_id, duration_ms}` 배열이며 `duration_ms`는 span 합과 같아야 하고 같은 `source_id` 중복은 거부한다(제안서 §5.2).

`activity.data.kind`는 1차에서 4종만 허용한다. heartbeat, artifact별 사건, requested/committed 2단 사건, correction 사건은 이 계약에 없다(제안서 §4.1 말미).

### 1.3 `actor.kind` × `provenance.type` × `recorded_by.kind` × `source.kind` 허용 조합

원천: 제안서 §4.3 기록 주체 표, §5.1 enum 제약. **아래 표에 없는 조합은 append 단계에서 거부한다**(AC-6).

| # | `actor.kind` | `provenance.type` | `recorded_by.kind` | 허용 `source.kind` | 필수 추가 증거 | 완료 게이트 기여 |
|---|---|---|---|---|---|---|
| A1 | `worker` | `adapter` | `adapter` | `process_start` \| `agent_handshake` \| `agent_message` \| `stream_event` \| `tool_result` \| `process_exit` \| `agent_error` | `source.id` + `source.sha256` + `source.observed_at` | **가능** (trusted adapter event) |
| A2 | `worker` | `direct` | `worker` | `worker_event` | `worker_log_token_id` + 안정 `request_id` | 불가 (보조 궤적) |
| A3 | `worker` | `import` | `tool` | `legacy_line` \| `oppl_event` | `source.id` + `source.sha256` + `source.locator` | 불가 |
| A4 | `PM` | `direct` | `PM` \| `tool` | `null` | 호출 event ID | 불가 |
| A5 | `user` | `direct` | `PM` \| `tool` | `null` | 호출 event ID | 불가 |
| A6 | `auto` | `direct` | `tool` | `null` | 호출 event ID | 불가 |
| A7 | `tool` | `direct` | `tool` | `null` | 사전 확정 event ID(= `request_id`) | 해당 없음 |
| A8 | `PM` \| `user` \| `auto` \| `tool` | `import` | `tool` | `legacy_line` \| `oppl_event` | `source.id` + `source.sha256` + `source.locator` | 불가 |

**PM `activity`의 사건 고유 payload 축 폐쇄 목록**: `actor.kind=PM` ∧ `provenance.type=direct`인 `activity` 사건에서, §1.1 공통 필드(`schema_version`·`event_id`·`timestamp`·`run_id`·`sequence`·`event`·`actor`·`provenance`·`caused_by_event_id`·`worker_run_id`·`stage`·`task_step`·`work_item` 등)는 §1.1 계약 그대로 적용되며 이 조문이 제한하지 않는다. 이 조문이 폐쇄하는 것은 사건 고유 의미 payload 두 축뿐이다: (a) `data` 객체 — `kind` 1개 키만 허용하고 값은 `{decision, validation, retry, progress}` 4종 enum, (b) 사람이 읽는 서술 축 — `summary`·`reason`·`refs` 외의 자유 서술 필드를 새로 만들지 않는다. 원본 프롬프트, chain-of-thought(내부 사고 과정), 비밀값은 `summary`·`reason`·`refs`·`data`를 포함한 어떤 필드에도 저장하지 않는다. `data`에 `kind` 외의 키가 있거나 `kind` 값이 4종 enum 밖이면 `state-tool.log-event`의 입력 검증(`_build_pm_activity_data()`)이 `schema_invalid`로 거부한다. 이 집행 지점은 `state-tool.log-event` CLI를 거치는 PM `activity` 생산 경로에만 적용되며, 이 표면을 거치지 않는 다른 생산 경로(adapter·importer 등)는 이 폐쇄 검사를 받지 않는다. 최상위 키 폐쇄 판정은 §1.1이 소유하므로 여기서 재서술하지 않는다.

**명시적 거부 조합**

- `actor.kind=worker` + `recorded_by.kind=PM` — PM 대필. 스키마 단계에서 거부한다(제안서 §4.3 표 5행).
- `actor.kind=worker` + `provenance.type=direct` + `worker_log_token_id` 부재.
- `provenance.type=adapter` + `recorded_by.kind ≠ adapter`.
- `provenance.type=import` + `recorded_by.kind ≠ tool`.
- 사건 종류별 actor 제약 위반: `worker.*`는 `worker`만, `worker.capability.*`는 actor·recorded_by 모두 `tool`만, `run.started`/`run.completed`/`state.changed`는 `tool`만, `gate.requested`는 `PM`만, `gate.resolved`는 `PM|user|auto`만(제안서 §5.1).
- active 모드의 사건별 source 제약 위반: `worker.started`는 `process_start|agent_handshake`, `activity`는 `agent_message|stream_event|tool_result`, terminal은 `process_exit|agent_error`만(제안서 §5.1 말미).

**trusted adapter event 정의**: `actor.kind=worker` ∧ `provenance.type=adapter` ∧ `provenance.recorded_by.kind=adapter`를 모두 만족하는 사건. 조합 A1만 해당한다.

**완료 알림 분해 금지 불변식** (같은 `worker_run_id`에서 완료 게이트에 기여하는 activity와 terminal 사이, 제안서 §4.3):

1. `activity.provenance.source.id ≠ terminal.provenance.source.id`
2. `activity.provenance.source.sha256 ≠ terminal.provenance.source.sha256`
3. `activity.provenance.source.observed_at < terminal.provenance.source.observed_at` **이며** `activity.timestamp < terminal.timestamp`
4. 하나의 완료 메시지를 `locator`·offset·part로 분할해 둘을 만들 수 없다
5. 위 1~4 중 하나라도 위반하면 완료를 거부한다

### 1.4 상태 원천의 로그 계약 블록과 미전송 사건 보관함

원천: 제안서 §6.1. 상태 파일 `schema_version` `"1.2"`의 **필수 블록**이다. 별도 매니페스트 파일을 만들지 않는다.

```json
{
  "schema_version": "1.2",
  "run_log": {
    "contract_version": "1.0",
    "mode": "active",
    "completion_profile": "observed_trajectory",
    "completion_profile_receipt": {
      "channel_id": "pm-agent-tool",
      "adapter_id": "agent-tool-adapter",
      "adapter_sha256": "<hex>",
      "receipt_sha256": "<hex>"
    },
    "active_run_id": "run_...",
    "status": "active",
    "pending_events": []
  }
}
```

| 필드 | 타입 | 필수 | 값·제약 |
|---|---|---|---|
| `contract_version` | string | 필수 | 사건 계약 버전. 현재 `"1.0"` |
| `mode` | string | 필수 | `shadow` \| `active` |
| `completion_profile` | string | 필수 | §1.5 enum 3종 |
| `completion_profile_receipt` | object \| null | 조건부 | `mode=active`에 필수. `channel_id`·`adapter_id`·`adapter_sha256`·`receipt_sha256` |
| `active_run_id` | string | 필수 | 현재 run |
| `status` | string | 필수 | `active` \| `pending` \| `overridden`. outbox와 전이 규칙으로만 변경 |
| `pending_events` | array | 필수 | 미전송 사건 보관함. 아래 상한 |

> 위 예시의 `channel_id`·`completion_profile`·`adapter_id` 값은 **형태를 보이기 위한 예시이며 계약이 아니다.** 실제 채널별 등급 배정은 Phase 0 산출 `profiles.json`이 소유한다(§1.6, TRD D-8).

**보관함 항목 구조와 상한**

- 항목은 §1.1 공통 필드를 그대로 갖는 **compact 표준 payload**다(별도 축약 형식을 만들지 않는다).
- 항목당 상한: **UTF-8 4 KiB**. 초과하는 PM 설명·증거는 먼저 별도 파일에 원자 저장하고 항목에는 상대 경로와 SHA-256만 넣는다. 증거 파일 생성 실패 시 상태 전이를 시작하지 않는다.
- 전체 건수 상한: `TOTAL_LIMIT = 128`. 전체 payload 최악 크기 = 512 KiB.
- 일반 admission 한도 = `TOTAL_LIMIT − (보관함에 있는 override 사건 수)`. 별도 예약 슬롯 자료구조를 두지 않는다.
- override bundle은 `activity(data.kind=decision)` 1건 + 강제 `state.changed` 1건의 **정확히 2건**이며, 일반 admission 한도와 무관하게 **정확히 한 번만** 적재된다.
- 보관함에 적재 대상인 사건: `state.changed`, `run.started`, `run.completed`, `gate.requested`, `gate.resolved`, PM `activity`. 워커 직접·adapter 사건은 보관함을 쓰지 않고 `run-log-tool`이 직접 append한다(제안서 §6.2 말미).

**계약 무결성**: `run_log` 블록을 손편집으로 제거하면 스키마 검증 실패다. active 태스크에서 outbox 복구 근거 없이 기록이 사라지면 legacy로 강등하지 않고 `run_log_missing`으로 진단한다. 반대로 보관함에 `run.started`가 남아 있으면 `run_log_missing`이 아니라 **복구 가능 초기화**다(제안서 §6.1).

### 1.5 완료 판정 등급 enum과 self-test receipt

| `completion_profile` | 기계 관측 범위 | active 정상 완료 게이트 | 허용 `mode` |
|---|---|---|---|
| `observed_trajectory` | start + 중간 message/stream/tool + terminal | trusted started 1건 + **trusted activity 1건 이상** + terminal 정확히 1건 + §1.3 분해 금지 불변식 | `shadow`, `active` |
| `observed_terminal` | start + terminal만 | trusted started 1건 + terminal 정확히 1건 + 기존 `task_steps[].gate.artifacts` 검사와 PM Gate | `shadow`, `active` |
| `cooperative` | 기계 증거 없음 | 완료 차단에 관여하지 않음 | `shadow`만 |

- 두 active 등급의 공통 조건: 같은 `worker_run_id`의 started 1건, terminal 정확히 1건, terminal의 결과 또는 `reason`, `duration_ms` + `duration_source=adapter_monotonic`.
- `shadow`는 `duration_source ∈ {worker_monotonic, unknown}`과 `duration_unknown_reason`을 허용한다.
- `observed_terminal`의 artifact 검사는 `--force + --note`로 우회 가능하며 그 사실이 decision 로그에 `gate_artifact_force`로 남는다. 따라서 이 등급의 **무조건적 기계 강제 범위는 trusted started + terminal까지**다.
- `activity` 부재를 대체할 수 있는 유일한 예외: terminal의 `reason_code=pre_activity_failure`. 이때 `recorded_by.kind=adapter` ∧ `source.kind ∈ {process_exit, agent_error}` ∧ (exitcode 또는 오류 envelope hash) 가 모두 참이어야 한다(제안서 §4.3 말미).
- `mode=active` + `completion_profile=cooperative` 조합은 `cooperative_active_rejected`로 거부한다.

**self-test receipt 구조** (변환기가 자기 채널의 관측 능력을 기계적으로 입증하는 산출):

| 필드 | 타입 | 필수 | 값 |
|---|---|---|---|
| `receipt_version` | string | 필수 | `"1.0"` |
| `channel_id` | string | 필수 | §1.6 명명 규칙 |
| `adapter_id` | string | 필수 | 변환기 식별자 |
| `adapter_sha256` | string | 필수 | 변환기 구현체의 SHA-256 hex |
| `observed` | object | 필수 | `{start: bool, intermediate: bool, terminal: bool, monotonic_span: bool}` |
| `claimed_profile` | string | 필수 | §1.5 enum |
| `evidence` | array\<string\> | 필수 | 원본 증거 파일의 **상대 경로** 목록. 1건 이상 |
| `produced_at` | string | 필수 | UTC RFC 3339 밀리초 |

`claimed_profile`은 `observed`에서 결정론적으로 파생되어야 한다: 셋 다 참이면 `observed_trajectory`, start·terminal만 참이면 `observed_terminal`, 그 외 `cooperative`. 파생과 불일치하는 receipt는 거부한다.

### 1.6 `profiles.json` 구조

원천: 제안서 §4.2.1. **계약(등급 메커니즘)은 이 문서가, 배정값은 이 파일이 소유한다**(TASK.md C-9).

```json
{
  "schema_version": "1.0",
  "produced_by": "<Phase 0 태스크 id>",
  "channels": [
    {
      "channel_id": "pm-agent-tool",
      "completion_profile": "observed_trajectory",
      "adapter_id": "agent-tool-adapter",
      "adapter_sha256": "<hex>",
      "receipt_sha256": "<hex>",
      "evidence_paths": ["evidence/pm-agent-tool/start.json", "evidence/pm-agent-tool/terminal.json"]
    }
  ]
}
```

| 필드 | 타입 | 필수 | 제약 |
|---|---|---|---|
| `schema_version` | string | 필수 | `"1.0"` |
| `produced_by` | string | 필수 | 배정을 산출한 Phase 0 태스크 식별자 |
| `channels[].channel_id` | string | 필수 | 파일 내 유일. 명명 규칙 아래 |
| `channels[].completion_profile` | string | 필수 | §1.5 enum 3종 |
| `channels[].adapter_id` | string | 필수 | `cooperative`면 `null` 허용 |
| `channels[].adapter_sha256` | string \| null | 조건부 | `completion_profile ≠ cooperative`면 필수 |
| `channels[].receipt_sha256` | string \| null | 조건부 | `completion_profile ≠ cooperative`면 필수 |
| `channels[].evidence_paths` | array\<string\> | 필수 | **상대 경로**만. 1건 이상 |
| `channels[].observation_preconditions` | array\<object\> | 조건부 | 등급이 특정 호출 조건에서만 성립할 때 **필수**. 각 항목은 `condition`(관측을 성립시킨 호출 조건), `evidence_path`(그 조건에서의 관측 증거), `invalidated_if`(이 조건이 깨지면 배정이 무효가 되는 서술)를 갖는다 |

> 위 예시에 적힌 `completion_profile` 값은 **형태 예시이며 배정이 아니다.** 어느 채널이 어느 등급인지는 이 계약이 정하지 않으며 Phase 0 실측이 산출한다(TASK.md C-9, TRD D-8). 아래 명명 규칙 표는 채널 식별자와 표면 id의 대응만 확정하고 등급은 확정하지 않는다.

**채널 식별자 명명 규칙** (PM 판정 M-3): `{호출 주체}-{채널 종류}` 형태의 소문자 kebab 안정 문자열이며, `surfaces.json`의 변환기 표면 id 뒷부분과 **같은 값**을 쓴다. Phase 0 판정 대상 2축의 확정값은 다음과 같다.

| `channel_id` | 축 | 대응 표면 id |
|---|---|---|
| `pm-agent-tool` | PM이 외부 에이전트 도구를 호출하는 축 | `adapter.pm-agent-tool` |
| `oppl-headless-cli` | Project Loop 내부 헤드리스 CLI(`opal-agent`) 축 | `adapter.oppl-headless-cli` |

**등급의 호출 조건 종속 (Phase 0 실측 반영)**

등급은 채널 그 자체가 아니라 **채널을 어떤 호출 조건으로 부르는지**에 종속될 수 있다. Phase 0 실측이
이 축을 드러냈으므로 계약에 가산 반영한다.

- 배정이 특정 호출 조건에서만 성립하면 `observation_preconditions`를 채운다. 비우고 등급만 적으면
  조건이 소실되어, 조건을 만족하지 않는 변환기가 같은 등급을 주장할 수 있다.
- **변환기가 선언된 호출 조건을 바꾸면 그 채널의 배정은 무효다.** 재스파이크로 재발급해야 하며,
  이는 계약 개정이 아니라 배정값 갱신이다(TASK.md C-9).
- `state-tool init --run-log-mode active`는 이 필드가 조건부 필수인데 비어 있으면 active 초기화를
  거부한다(`profile_not_found`와 같은 계열로 다룬다).
- 기계검증: 이 조건은 MV-31이 판정한다.

`state-tool init --run-log-mode active`는 이 파일에서 `--channel-id` 항목을 찾아 `adapter_sha256`·`receipt_sha256`을 검증하고 `completion_profile_receipt`에 고정한다. **항목이 없으면 active 초기화를 거부한다**(`profile_not_found`). 배정값 변경은 계약 개정이 아니라 재스파이크이며 계약 재확정 절차를 발동하지 않는다.

### 1.7 워커 쓰기 권한의 범위(`scope`)와 유효기간

원천: 제안서 §6.4(scope·만료·폐기 검증, terminal과 `run.completed(reason=restart)`가 즉시 폐기 원천), §5.2(token 원문 비기록), AC-9.

#### 1.7.1 `worker.capability.issued`의 `data` 구조

| 필드 | 타입 | 필수 | 값·제약 |
|---|---|---|---|
| `token_id` | string | 필수 | `wlt_<UUIDv4>`. §1.1.3의 식별자 |
| `token_sha256` | string | 필수 | 원문의 SHA-256 hex. §1.1.3의 검증자 |
| `scope` | object | 필수 | 아래 §1.7.2 |
| `expires_at` | string | 필수 | UTC RFC 3339 밀리초 |

#### 1.7.2 `scope` 허용 값 집합

권한은 **1회 디스패치 범위**로만 발급된다. 세 축 전부를 만족해야 append가 통과하며, 하나라도 어긋나면 `worker_token_invalid`다.

| `scope` 필드 | 타입 | 필수 | 허용 값 | 의미 |
|---|---|---|---|---|
| `run_id` | string | 필수 | 발급 시점의 `active_run_id` **정확히 하나** | 다른 run에 쓸 수 없다. run이 바뀌면(`restart-run`) 즉시 무효 |
| `worker_run_id` | string | 필수 | 발급 대상 `worker_run_id` **정확히 하나** | 다른 워커 실행의 사건을 쓸 수 없다(R-20: 위조 방지) |
| `events` | array\<string\> | 필수 | `worker.started`, `activity`, `worker.completed`, `worker.failed`, `worker.blocked` 중 1건 이상. **기본값은 이 5종 전부** | 워커가 직접 쓸 수 있는 사건 종류의 폐쇄 집합 |
| `provenance_types` | array\<string\> | 필수 | 고정 `["direct"]` | 권한은 direct 경로만 인가한다. adapter·import 경로는 워커 token을 쓰지 않으며 §1.3의 A1·A3 조건으로 별도 검증된다 |

**`events`에 넣을 수 없는 값**(요청 시 발급 자체를 거부): `run.started`, `run.completed`, `state.changed`, `gate.requested`, `gate.resolved`, `worker.capability.issued`, `worker.capability.revoked`. 이들은 도구·PM 소유 사건이며 `actor.kind=tool|PM`만 허용되므로(§1.2·§1.3) 워커 권한의 대상이 아니다.

**게이트 기여와의 관계**: 이 권한으로 쓴 사건은 전부 조합 A2(`direct`/`worker`)이므로 완료 게이트에 기여하지 않고 보조 궤적으로만 보존된다(§1.3). 권한의 존재는 "쓸 수 있다"이지 "완료 근거가 된다"가 아니다.

#### 1.7.3 유효기간 기본값과 상한

락 대기 정책(§2.7)과 같은 형태 — **기본값 존재 + 설정 조정 가능 + 절대 상한**.

| 항목 | 값 | 근거 |
|---|---|---|
| 기본 유효기간 | **86,400초(24시간)** | 1회 디스패치는 통상 분~시간 단위이며, 하루를 넘겨 유효한 쓰기 권한은 디스패치 범위를 벗어난다. **제안서에 값이 없으므로 PM 판정 위임 범위 내 설계 결정이다** |
| 절대 상한 | **604,800초(7일)** | 원본 보존 기본 상한 7일(제안서 §8.3)과 같은 축에 값을 맞춘다 — 권한이 증거 보존 창보다 오래 살아남지 않게 한다. **PM 판정 위임 범위 내 설계 결정** |
| 설정 조정 | effective setting으로 기본 유효기간을 조정할 수 있되 **절대 상한을 넘길 수 없고 0 이하일 수 없다** | §2.7과 동일한 형태 |
| 초과·부적격 요청 | `--expires-in`이 절대 상한 초과 또는 0 이하이면 **발급을 거부**한다 → `capability_expiry_invalid` | 상한을 조용히 잘라내면 호출자가 받은 값과 실제 값이 달라진다 |

#### 1.7.4 폐기 원천

| 원천 | 별도 사건 필요 | 근거 |
|---|---|---|
| terminal(`worker.completed`/`failed`/`blocked`) | 불필요 — 그 자체가 즉시 폐기 원천 | §6.4 |
| `run.completed(reason=restart)` | 불필요 — 그 자체가 즉시 폐기 원천 | §6.4 |
| `expires_at` 경과 | 불필요 — 시각 비교로 판정 | §6.4 |
| terminal 이전의 명시적 조기 폐기 | **필요** — `worker.capability.revoked` 1건 | §6.4 |

만료·폐기된 권한의 재사용은 `worker_token_invalid`로 거부한다. 런타임 권한 테이블은 위 4종 원천을 함께 적용해 사건만으로 전량 재구축된다(§1.1.3, MV-11).

---

## 2. 시그니처 (Signature)

### 2.1 공통 응답 봉투

**기존 도구의 평면 봉투와 의도적으로 다르다.** 기존 22종(`state-tool`·`backlog-tool` 등)은 payload 키를
봉투 키와 같은 층에 펼친다(예: `{"ok": true, "command": "coverage-check", "all_covered": true}`). run-log
계열은 payload를 `data`로, 오류를 `error.code`/`error.message`/`error.detail`로 분리한다.

분리하는 이유는 이 계열이 **기계 소비 우선**이기 때문이다. 평면 봉투에서는 새 payload 키가 봉투 키와
이름이 겹칠 수 있고, 소비자가 "어디까지가 봉투이고 어디부터가 결과인지"를 키 이름으로 추측해야 한다.
`§2.2.1`의 오류 코드↔표면 대응과 `MV-30` 같은 기계 검사가 이 경계를 전제한다.

기존 도구는 이 형태로 이전하지 않는다 — 이전 비용이 이득보다 크고 `TASK.md` C-2가 기존 동작 보존을
요구한다. 따라서 OPAL에는 두 봉투가 공존하며, 그 경계는 "run-log 계열인가"다.

```json
{"ok": true,  "data": { ... }}
{"ok": false, "error": {"code": "<ERROR_CODE>", "message": "<사람이 읽는 문장>", "detail": { ... }}}
```

- 모든 명령은 `--format json`을 지원하며, 미지정 시 사람이 읽는 텍스트를 낸다.
- `ok:false`의 프로세스 종료 코드는 0이 아니다.
- 오류 코드 문자열은 단일 SSOT 상수 테이블(`ERROR_CODES`)이 소유한다.

### 2.2 오류 코드

제안서 §6.3의 5종 + 본 계약이 확정하는 추가 코드.

| 코드 | 조건 | 처리 | 원천 |
|---|---|---|---|
| `run_log_write_failed` | 필수 워커 사건 append 실패 | 워커 완료 mark 차단 | §6.3 |
| `run_log_missing` | 활성 계약인데 로그 또는 필수 사건 부재 | 워커 완료·CLOSE 차단. **legacy 강등 금지** | §6.3 |
| `run_log_pending` | 보관함 사건이 표준 로그에 미반영 | 한도 내 일반 진행 허용, 완료·CLOSE 차단 | §6.3 |
| `run_log_outbox_full` | 일반 보관함이 `TOTAL_LIMIT − override 사건 수`에 도달 | reconcile·1회 override bundle 외 전이 차단 | §6.3 |
| `run_log_inconsistent` | reconcile로 자동 확정 불가 | 사용자 override 또는 수동 복구 | §6.3 |
| `request_id_conflict` | 같은 `(run_id, request_id)`에 다른 payload 재사용 | 거부. 동일 payload는 기존 event 반환 | §5.1 |
| `event_too_large` | 직렬화 16 KiB 초과 | 거부. 자동 raw 저장·무음 절단 금지 | §8.2 |
| `schema_invalid` | 폐쇄형 스키마 위반(미정의 키·타입·enum) | 거부 | §5.1 |
| `provenance_invalid` | §1.3 허용 조합 표 밖의 조합, 필수 증거 부재, 분해 금지 불변식 위반 | 거부 | §4.3 |
| `worker_token_invalid` | 만료·폐기·scope 불일치 token 사용 | 거부 | §6.4 / 본 계약 §1.7.2 |
| **`capability_expiry_invalid`** | 권한 발급 요청의 유효기간이 절대 상한 초과 또는 0 이하 | **발급 거부**(조용한 절단 금지) | **본 계약 §1.7.3** |
| **`capability_scope_invalid`** | 권한 발급 요청의 `events`에 도구·PM 소유 사건이 포함, 또는 `run_id`/`worker_run_id`가 단일 값이 아님 | **발급 거부** | **본 계약 §1.7.2** |
| `completion_evidence_missing` | 등급이 요구하는 증거(started/activity/terminal) 부족 | 완료 차단 | §4.2 |
| `worker_duration_conflict` | 1.2 태스크의 수동 분 값이 파생값과 불일치 | 거부 | §7 |
| `gate_not_requested` | 선행 `gate.requested` 없는 `gate.resolved` | 거부 | §4.4 |
| `gate_duplicate` | 같은 `gate_id`의 중복 requested 또는 중복 resolved | 거부 | §4.4 |
| `profile_not_found` | `--run-log-mode active`인데 `profiles.json`에 채널 항목 없음 | active 초기화 거부 | §4.2.1 |
| `profile_receipt_mismatch` | `adapter_sha256`·`receipt_sha256` 불일치 | active 초기화 거부 | §6.1 |
| `cooperative_active_rejected` | `cooperative` 채널에 active 설정 시도 | 거부 | §4.2 |
| `actor_not_allowed` | 명령이 허용하지 않는 actor(예: `log-event`에 worker actor) | 거부 | §9 |
| `refs_invalid` | `refs`에 프로젝트 상대 경로가 아닌 값(절대 경로 등)이 있음 | 거부 | §1.1 |
| `redaction_failed` | 마스킹 불가로 판정된 원본 | 저장 거부, 메타데이터 사건만 기록 | §8.3 |
| `task_path_not_absolute` | 전달된 task path가 절대 경로가 아님 | 거부 | §3.2 (M-2) |
| **`task_lock_timeout`** | 배타 락 대기가 상한을 초과 | **오류 반환**(자동 재시도 금지) | **본 계약 §2.7 (M-4)** |

#**사건 종류별 actor 제약 위반의 코드** (PM 확정, F-3): §1.2가 사건마다 정한 `actor.kind` 제약을
어긴 사건(예: `gate.requested`에 `actor.kind=user`)은 `provenance_invalid`로 거부한다.
`schema_invalid`가 아니다 — 이 위반은 값이 enum 밖이어서가 아니라 **사건과 주체의 조합이
인가되지 않아서** 거부되며, 그 판정 축은 §1.3 조합 검증과 같다. `schema_invalid`는 §1.1 폐쇄형
최상위 키와 개별 필드 enum 위반에만 쓴다.

**`source.sha256`의 해싱 대상** (PM 확정, T03 검사 의견): 이 해시의 용도는 **원본 증거를 유일하게
식별하고 감사자가 대조할 수 있게** 하는 것이다. 따라서 import 경로는 파일에서 읽은 **원본 바이트**를
해싱한다. 비-UTF-8 바이트를 치환한 뒤 그 결과를 해싱하면, 같은 해시가 서로 다른 원본에서 나올 수
있고 원본과 대조해도 일치하지 않아 식별자로서의 성질을 잃는다. 디코딩 실패는 해시 대상을 바꾸는
사유가 아니라 별도 신호로 보고할 사유다.

**읽었으나 버린 행의 보고** (PM 확정, T03 검사 의견): import 응답의 읽은 행 수를 버린 행만큼
줄여서 보고하지 않는다. 버린 행은 별도 필드로 **명시적으로 드러낸다**. 이 프로젝트가 없애려는
실패 모드가 "조용한 누락"인데, 집계에서 소리 없이 빼면 같은 실패 모드를 도구가 재생산한다.

### 2.2.1 오류 코드 ↔ 발생 표면 대응

위 표의 각 코드가 어느 표면에서 발생하는지의 **계약상 원천**이다. `surfaces.json` 각 표면의 `response_shape.err` 집합은 이 대응과 **양방향으로 일치**해야 한다 — 여기에 있는데 표면에 없거나, 표면에 있는데 여기에 없으면 계약 위반이다(판정: MV-30).

| 코드 | 발생 표면 |
|---|---|
| `task_path_not_absolute` | **전 CLI 표면 17종** (§3.2 경로 계약) |
| `task_lock_timeout` | **전 CLI 표면 17종** (§2.7 락 대기 정책) |
| `run_log_write_failed` | `run-log-tool.init`, `.begin-worker`, `.append`, `.reconcile`, `.import-agentic`, `.import-oppl`, `state-tool.restart-run`, `.log-event`, `.gate-request`, `.gate-resolve`, `.init.run-log-mode`, `.mark.completion-gate` |
| `run_log_missing` | `run-log-tool.begin-worker`, `.append`, `.validate-worker`, `.validate-run`, `.reconcile-duration`, `.import-agentic`, `.import-oppl`, `.show`, `.export`, `state-tool.mark.completion-gate` |
| `run_log_pending` | `state-tool.restart-run`, `.log-event`, `.mark.completion-gate` |
| `run_log_outbox_full` | `state-tool.restart-run`, `.log-event`, `.gate-request`, `.gate-resolve`, `.mark.completion-gate` |
| `run_log_inconsistent` | `run-log-tool.validate-worker`, `.validate-run`, `.reconcile`, `state-tool.mark.completion-gate` |
| `request_id_conflict` | `run-log-tool.append` |
| `event_too_large` | `run-log-tool.append`, `.import-agentic`, `.import-oppl` |
| `schema_invalid` | `run-log-tool.append`, `.import-agentic`, `.import-oppl`, `state-tool.log-event` |
| `provenance_invalid` | `run-log-tool.append` |
| `worker_token_invalid` | `run-log-tool.append` |
| `capability_expiry_invalid` | `run-log-tool.begin-worker` |
| `capability_scope_invalid` | `run-log-tool.begin-worker` |
| `completion_evidence_missing` | `state-tool.mark.completion-gate` |
| `worker_duration_conflict` | `run-log-tool.reconcile-duration`, `state-tool.mark.completion-gate` |
| `gate_not_requested` | `state-tool.gate-resolve` |
| `gate_duplicate` | `state-tool.gate-request`, `.gate-resolve` |
| `profile_not_found` | `state-tool.init.run-log-mode` |
| `profile_receipt_mismatch` | `state-tool.init.run-log-mode` |
| `cooperative_active_rejected` | `state-tool.init.run-log-mode` |
| `actor_not_allowed` | `state-tool.log-event` |
| `refs_invalid` | `state-tool.log-event` |
| `redaction_failed` | `run-log-tool.append`, `.import-agentic`, `.import-oppl`, `.export` |

- **변환기 표면 2종(`adapter.*`)은 이 대응의 대상이 아니다.** CLI가 아니므로 오류 봉투를 직접 반환하지 않고, 변환기가 관측한 실패는 자기가 호출한 `run-log-tool.append` 표면의 오류로 드러난다. MV-30의 양방향 검사는 `kind=cli`인 17개 표면만 대상으로 한다.
- 이 대응을 바꿀 때는 §2.2 표·§2.2.1 대응·`surfaces.json` 세 곳을 **같은 변경 단위**로 갱신한다.

### 2.3 `run-log-tool` 11개 서브명령

호출 형태·인자·응답 필드는 `surfaces.json`의 `run-log-tool.*` 표면 11개가 기계가독 원천이다. 아래는 계약상 의미와 불변식만 확정한다.

| 표면 id | 의미 | 계약 불변식 |
|---|---|---|
| `run-log-tool.init` | 실행 디렉터리와 첫 segment 생성 | 멱등. 이미 있으면 `created:false`로 성공 |
| `run-log-tool.begin-worker` | `worker_run_id`와 1회 디스패치 범위 쓰기 capability 발급 | `worker.capability.issued`와 runtime 투영만 만들고 **`worker.started`를 만들지 않는다**. token 원문은 stdout 1회로만 전달하고 로그에는 `worker_log_token_id`만 남긴다. `--scope` 미지정 시 §1.7.2의 기본 `events` 5종, `--expires-in` 미지정 시 §1.7.3의 기본 86,400초를 적용하며 상한 초과·부적격 요청은 `capability_expiry_invalid`·`capability_scope_invalid`로 거부한다 |
| `run-log-tool.append` | 표준 사건 1건 기록 | §1.1~§1.3 전건 검증. `(run_id, request_id)` 멱등 |
| `run-log-tool.validate-worker` | 워커 단위 완료 증거 검증 | 등급별 게이트 조건과 분해 금지 불변식 판정. **활성 여부는 판정하지 않는다** |
| `run-log-tool.validate-run` | run 단위 무결성·누적 용량 검증 | 순번 중복·누락, segment 정렬, 총 bytes 보고 |
| `run-log-tool.reconcile` | 보관함 사건 재전송 | **완전한 사건만** 재전송. 현재 timestamp·stdout에서 사건 합성 금지 |
| `run-log-tool.reconcile-duration` | 시간 파생 일치 검증 | `floor(duration_ms / 60000)` 불일치 시 `worker_duration_conflict` |
| `run-log-tool.import-agentic` | legacy 실행 일지 단방향 가져오기 | 멱등. `recorded_by.kind=tool`. 완료 게이트 불기여 |
| `run-log-tool.import-oppl` | Project Loop 원본 단방향 가져오기 | 멱등. 역변환 금지. 완료 게이트 불기여 |
| `run-log-tool.show` | 사건 조회 | 읽기 전용 |
| `run-log-tool.export` | 정제본 산출 | `--sanitize` 필수. 마스킹 경로 통과 |

### 2.4 `state-tool` 신규 4개 서브명령

| 표면 id | 계약 불변식 |
|---|---|
| `state-tool.restart-run` | 기존 run을 `run.completed(reason=restart)`로 닫고 새 `run_id` 발급. 두 사건을 한 번의 상태 원자 쓰기로 커밋. **호출 전에 존재한 미해소 보관함이 있으면 거부**하며, restart 자체가 커밋하는 2건은 이 사전검사 대상이 아니다 |
| `state-tool.log-event` | PM actor 사건만 수용. `actor.kind=worker` 지정은 `actor_not_allowed`로 거부 |
| `state-tool.gate-request` | 고유 `gate_id` 유일성 검사. 보관함 중개 |
| `state-tool.gate-resolve` | 같은 `gate_id`의 선행 requested 필수. 중복 resolved 거부. 대기 시간은 두 사건의 UTC 차분으로만 계산 |

### 2.5 `state-tool` 개정 2개 표면

| 표면 id | 개정 내용 |
|---|---|
| `state-tool.init.run-log-mode` | `--run-log-mode <off\|shadow\|active>` 추가. **기본값은 `shadow`** — 플래그를 생략하면 `shadow`로 초기화되며, 개정 전과 동일하게 run-log 계약을 비활성화하려면 `off`를 명시해야 한다(`off`는 개정 전 "미지정" 경로와 산출물·응답 키 집합이 바이트 동일). active는 `--channel-id` 필수이며 배포된 `profiles.json` 항목과 hash를 검증해 `completion_profile_receipt`에 고정한다. 첫 원자 쓰기는 `status=pending` + `run.started` 보관함 적재, 이후 segment 생성·멱등 append·보관함 제거가 성공해야 `status=active` |
| `state-tool.mark.completion-gate` | 완료 표시 시 채널 등급·provenance·시간 증거를 함께 검사. `--run-log-override`는 `--owner user` + `--note` 동시 필수이며 override bundle 2건을 한 번만 적재하고 `status=overridden`으로 둔다. 이후 해당 전이 1건 뒤에는 reconcile 외 추가 전이를 허용하지 않는다. `--worker-duration-minutes`는 1.0/1.1에서 현행 수용, 1.2에서 파생값 일치 시 수용+deprecated 경고, 불일치 시 `worker_duration_conflict` |

**`state-tool verify --run-log-completeness-check`** (D-6, AC-7·AC-8): 기존 `verify` 명령의 7번째 상호 배타 검사 라우트다. `state.json` 현재 행과 조각(committed)·보관함(pending) 사건을 대조해 자동 승인을 포함한 누락을 진단한다. read-only·비차단(exit 0)이며, `run-log-tool validate-run`의 조각 자체 순번·스키마·provenance 검증과 별개 축이다 — `run-log-core`가 상태 파일을 읽지 않는 단방향 의존(§3.1) 때문에 상태 대조는 `state-tool`만 수행할 수 있다. 반환은 누락 목록 4종(`missing_state_changed`·`missing_pm_activity`·`missing_gate_event`·`unobserved_worker_boundary`)과 관측 지점 3필드(`last_observed_decision`·`last_observed_state_change`·`last_observed_boundary`, 각 `{event_id, ts, ref}` 또는 `null`)이며, 3필드는 누락 목록과 무관하게 항상 반환한다. 이 라우트는 기존 `state-tool.verify` CLI 표면의 플래그 확장이며 `surfaces.json`에 별도 표면 id를 신설하지 않는다(D-7, PLAN 범위 제약 — 신규 id 필요 여부는 PM 판단 대상으로 남긴다).

`missing_pm_activity`는 현재 이 검사가 값을 채우는 조건을 결정론적으로 정의하지 않아 항상 빈 배열을 반환하는 미집행 공백이다. 트리거 조건을 이 계약이 아직 확정하지 않았으므로 임의로 지어내지 않는다 — 조건 확정은 후속 W의 몫이다.

### 2.6 기록 코어의 인프로세스 호출 형태

TRD D-5에 따라 `state-tool`은 기록 CLI를 하위 프로세스로 부르지 않고 **같은 프로세스의 기록 코어**를 호출한다.

```python
run_log_core.append(
    task_path: str,          # 절대 경로. 호출자가 전달 (§3.2)
    run_id: str,
    event: dict,             # §1.1 공통 필드를 갖춘 완성 payload
    *,
    lock_held: bool = False, # True면 코어는 배타 락을 재획득하지 않는다
    lock_timeout_ms: int = 30000,
    mode: str | None = None, # "active" | "shadow" | None. 호출자가 넘긴다 (PM 판정 ②)
) -> dict                     # §2.1 응답 봉투와 동일 구조
```

- `lock_held=True`는 **호출자가 같은 프로세스에서 이미 `.opal-task.lock`을 보유한다는 선언**이다. 코어는 이를 신뢰하고 재획득하지 않는다. 거짓 선언은 계약 위반이며 코어가 검출할 책임을 지지 않는다.
- 코어는 `state.json`을 읽지 않는다. `task_path`·`run_id`·`event`·`mode`만 소비한다.
- **`mode`는 코어가 판정하지 않고 호출자가 넘기는 값이다** (PM 판정 ②). 모드를 소유하는 것은
  상태 원천이고(§1.4 `run_log.mode`), 그 값을 아는 상태 도구가 인자로 전달한다. 코어는 이 값을
  어디서도 조회하지 않으므로 D-5 단방향이 보존된다.
- `mode="active"`일 때만 §1.3의 **active 전용 source 제약**(`worker.started`는 `process_start`·
  `agent_handshake`, `activity`는 `agent_message`·`stream_event`·`tool_result`, terminal은
  `process_exit`·`agent_error`)을 집행한다. **`None`이면 이 제약을 적용하지 않는다** — 모르는 것을
  추측해 차단하지 않는다.
- 이 인자가 집행하는 범위는 **append 시점의 구조 제약까지**다. 완료 게이트의 최종 조합 판정은
  상위 상태 도구가 소유한다(§3.1).
- 같은 시그니처 규약을 `init`·`reconcile`·`validate_*`·`import_*`에도 적용한다.

### 2.7 배타 락 대기 정책 (PM 판정 M-4)

- 배타 락은 `<task-path>/.opal-task.lock` 하나이며 **무한 대기를 금지한다**.
- 기본 대기 상한: **30,000 ms**.
- 초과 시 `task_lock_timeout` 오류를 반환한다. **도구가 자동 재시도하지 않는다** — 재시도 여부는 호출자의 결정이다.
- effective setting으로 조정 가능하되 **기본값이 항상 존재**하며, 설정 부재 시 위 기본값이 적용된다. 설정이 상한을 0 또는 음수로 지정하면 거부하고 기본값을 쓴다.
- 근거: fail-closed는 "잘못 진행하지 않는다"는 뜻이지 "영원히 기다린다"가 아니다. 무한 대기는 관측 도구가 실행을 멈추는 결과가 되어 제안서 §11 R-6("기록 계층 장애가 상태를 교착시키지 않는다")과 충돌한다.

### 2.8 조용시간 설정 로더·캐시 토큰의 개정 후 시그니처

§3.5가 정한 변경의 **개정 후 입출력 형태**다. 현재 형태의 원천은 `dashboard/backend/config.py`의 `load_quiet_hours`(160행)·`quiet_hours_token`(196행)과 그 반환식(204행)이다.

**개정 전**

```python
DEFAULT_QUIET_HOURS = {"enabled": True, "start": "00:00", "end": "09:00"}

def load_quiet_hours(project_path: str | None = None) -> tuple[int, int] | None
    # (시작 분, 끝 분) 또는 None

def quiet_hours_token(quiet_hours: tuple[int, int] | None) -> str
    # None → "off",  그 외 → f"{start}-{end}"
```

**개정 후**

```python
DEFAULT_QUIET_HOURS = {
    "enabled": True, "start": "00:00", "end": "09:00",
    "timeZone": "Asia/Seoul",          # 신설. 미설정 시 기존 동작과 동일
}

class QuietHours(NamedTuple):
    start_minute: int
    end_minute: int
    time_zone: str                      # IANA 시간대 이름

def load_quiet_hours(project_path: str | None = None) -> QuietHours | None
    # 2층 머지(전역 → 프로젝트 로컬, 하위 키 단위)는 그대로.
    # timeZone도 같은 머지의 하위 키로 해석한다.
    # enabled != True 또는 start == end면 None(보정 끔) — 기존과 동일.
    # timeZone 값이 유효한 IANA 이름이 아니면 DEFAULT의 "Asia/Seoul"로 폴백하고
    # 예외를 밖으로 던지지 않는다 — 기존 로더의 폴백 성격을 유지한다.

def quiet_hours_token(quiet_hours: QuietHours | None) -> str
    # None → "off" (기존과 동일)
    # 그 외 → f"{start_minute}-{end_minute}@{time_zone}"
```

계약 조항:

1. `timeZone`은 **2층 머지의 하위 키**다. 전역 `~/.opal/setting.json`의 `quietHours` 위에 프로젝트 `.opal/setting.local.json`의 `quietHours`를 하위 키 단위로 덮어쓰는 기존 구조를 그대로 쓰며 별도 로딩 경로를 만들지 않는다.
2. 어느 층에도 `timeZone`이 없으면 `Asia/Seoul`을 적용하고 **기존 설정 파일을 다시 쓰지 않는다**(제안서 §5.2).
3. `quiet_hours_token`은 `time_zone`을 서명에 **포함한다**. `timeZone`만 다르고 시작·끝이 같은 두 설정은 반드시 서로 다른 토큰을 만든다(MV-26).
4. `"off"` 반환 형태는 바뀌지 않는다. 보정이 꺼진 상태는 시간대와 무관하기 때문이다.
5. 토큰 문자열 형식 변경으로 기존 캐시 키는 1회 전부 갱신된다. 캐시는 파생물이므로 이는 손실이 아니다.
6. `stats` 모듈에 대한 주입 계약은 유지된다 — `stats.py`는 설정을 읽지 않으며 라우터가 필요한 값을 인자로 주입한다.

#### 2.8.1 계층 경계 — 시간대 해석은 통계 계층 앞에서 끝난다

`QuietHours` 3필드 구조는 **설정·라우터 계층 안에서만 존재한다.** 통계 계층의 기존 입력 형태는 바꾸지 않는다.

근거: `dashboard/backend/config.py` @header가 이미 경계를 선언한다 — "반환값 (시작 분, 끝 분)은 라우터가 `stats.py`에 인자로 주입한다 — **`stats.py`는 설정을 읽지 않는다**". 시간대는 설정이다. 따라서 시간대를 해석해 분 구간을 확정하는 일은 설정·라우터 계층의 책임이고, 통계 계층은 **확정된 분 구간만** 받는다.

| # | 조항 |
|---|---|
| B-1 | **유효 범위**: `QuietHours`(3필드)는 `config` 모듈과 라우터 계층 내부에서만 흐른다. 이 타입이 `stats` 모듈의 어떤 공개 함수 인자에도 나타나지 않는다 |
| B-2 | **통계 계층 주입 형태**: `stats`에 주입되는 값은 **기존과 동일한 `tuple[int, int] | None`(시작 분, 끝 분)**이다. `format_quiet_hours`·`quiet_overlap_minutes`·`row_durations`·`task_static_stats`·`task_live_stats`·`workflow_stats`의 `quiet_hours` 인자 형태는 개정하지 않는다 |
| B-3 | **해석 시점**: 시간대 해석은 **통계 호출 이전**, 라우터가 `load_quiet_hours()` 결과에서 분 구간을 좁혀 넘기는 지점에서 끝난다. 라우터는 3필드 값을 `quiet_hours_token()`에만 그대로 넘기고, `stats` 호출에는 `(start_minute, end_minute)`로 좁혀 넘긴다 |
| B-4 | **동결 표본 보존**: B-1~B-3을 지키면 `TASK.md` C-2가 동결한 Console 표본이 닿는 `stats` 공개 함수의 시그니처가 하나도 바뀌지 않으므로, `STATS-BASELINE.md` 기준값과 `dashboard/backend/tests/fixtures/t103_states/` 동결 fixture가 **시그니처 변경 없이 그대로 통과**한다. 판정은 MV-25·MV-26 |

Phase 2에서 UTC 사건을 집계하며 시간대별 겹침을 계산할 때도 이 경계를 유지한다 — 시간대를 소비해 분 구간을 만드는 일은 호출 계층이 하고, 통계 계층은 구간만 받는다.

---

## 3. 경계 (Boundary)

### 3.1 소유·금지 계약

TRD `## 구성요소와 책임 경계`를 계약 문장으로 확정한다.

| 주체 | 쓸 수 있는 것 | 쓸 수 없는 것 |
|---|---|---|
| `run-log-core` | 기록 segment(append 전용), `run/.runtime/` 파생 색인 | `state.json`을 **읽지도 쓰지도 않는다**. 계약 활성 여부·현재 run·재실행 허용을 판정하지 않는다. 채널 분기를 갖지 않는다 |
| `run-log-tool` | 기록 CLI 표면, 자체 락 획득 | 완료 게이트 최종 판정, legacy/active 판정, 현재 run 선택 |
| `state-tool` | `state.json`(계약 블록·보관함·현재 run), 배타 락, 완료 게이트 조합 판정 | 기록 segment에 **직접 파일 쓰기 금지**. 순번 자체 발급 금지. 현재 상태에서 과거 사건 합성 금지 |
| 채널 변환기 | `run-log-tool.append` 표면 호출 | `run-log-core` 직접 링크 금지. 상태 전이 수행 금지. 자기 등급 선언 금지(배정값은 `profiles.json`이 소유). 마스킹 자체 구현 금지 |
| Console (`dashboard/backend`) | `state-tool show --format json` read-only 호출 | 기록 segment 직접 읽기 금지(Phase 2 범위). 상태 도구 쓰기 커맨드 호출 금지 — `dashboard/backend/adapters/state_adapter.py` @header가 "쓰기 커맨드(init/advance/mark 등) 금지"로 이미 선언한 경계를 그대로 유지한다 |
| `STATE.md` | 사건 식별자 포인터와 복구 필요 상태 표시 | 사건 원문·decision 원문 복제 금지 |

**플랫폼 분기 금지**: 채널·플랫폼 차이는 변환기 계층과 install·plugin 어댑터에만 존재한다. `run-log-core`·`run-log-tool`·`state-tool` 어디에도 플랫폼 분기를 넣지 않는다(`.opal/AGENT.md` §금지사항, `docs/PROJECT.md` §프로젝트 원칙 플랫폼 독립성).

**`origins` 미선언**: 이 프로젝트는 웹 클라이언트를 갖지 않으므로 `surfaces.json`에 `origins`를 선언하지 않는다(제안서 §9.1).

### 3.2 경로 계약 (PM 판정 M-2)

기록 segment(`run/run-log-*.jsonl`), 런타임 색인(`run/.runtime/`), 배타 락(`.opal-task.lock`)은 **전부 `task_root`가 소유하는 태스크 캡슐 자산**이다.

- 근거: `opal/core/references/harness/worktree.md:29` — "태스크 문서·`.opal` 설정·branch source는 `task_root`가, 허브 `.opal/MEMORY.json`은 `allocator_root`가 소유한다."
- `memory-tool`의 `WORKTREE_WRITE_REJECTED`(`opal/tools/memory-tool/memory_tool.py:169`)는 **허브 자산 쓰기**를 막는 규칙이다. 기록은 태스크 캡슐 안이므로 두 규칙은 만나지 않는다. 충돌이 아니다.

계약 조항:

1. **기록 경로는 호출자가 전달한 task path 기준으로만 해석한다.** 모든 기록 자산의 위치는 `<task-path>/run/…`과 `<task-path>/.opal-task.lock`으로 고정하며, task path는 절대 경로여야 한다(아니면 `task_path_not_absolute`).
2. **도구는 cwd나 워크트리 디렉터리 문자열로 task path를 추론하지 않는다.** `allocator_root`를 cwd·task path 조상·`.opal-worktrees` 문자열로 추론하지 않는다는 계약과 같은 원칙이다(`opal/core/references/harness/worktree.md:41`, §canonical path 발급 계약). canonical task path는 `worktree-tool create` 성공 응답과 registry meta가 소유하며(같은 문서 57행), 도구는 그 값을 인자로 받는다.

### 3.3 `profiles.json` 2단 소유와 승격 절차 (PM 판정 M-3)

1. **산출 시점**: Phase 0 태스크 폴더 안에서 원본 증거와 함께 생성된다. `evidence_paths`는 그 폴더 기준 상대 경로다.
2. **승격**: 사람 승인 게이트(제안서 §10 Phase 0 말미) 통과 후 프로젝트 소스 `opal/core/` 아래로 승격하고, install이 배포본에 내린다.
3. **읽기**: `state-tool init --run-log-mode active`는 **배포된 위치**에서 읽는다.
4. **금지**: 배포본(`~/.opal/`)을 직접 편집해 배정값을 바꾸지 않는다(`.opal/AGENT.md` §금지사항, `TASK.md` C-1). 배정값 변경은 프로젝트 소스 수정 후 재배포로만 이뤄진다.

### 3.4 식별자 계약과 집계 주체 (PM 판정 M-5)

- 기록 계층은 사건에 `parent_run_id`를 담는 것까지만 소유한다. **두 태스크 폴더를 가로질러 하나의 실행으로 읽는 주체는 이 계약이 정하지 않는다.**
- 교차 읽기는 Phase 2 분석 소비(렌더러 층)의 소유다. 관측이 데이터 규약·렌더러·발동층 3층으로 분리돼 있고 교차 읽기는 렌더러 층의 일이기 때문이다(프로젝트 지식 `.opal/brain/pages/concept/observability-3layer-protocol-renderer-trigger-separation.md`).
- **이 문단은 후속 단계가 같은 질문을 다시 올리지 않도록 하는 종결 조항이다.** Phase 1 범위에서 교차 집계 주체를 정하지 않는 것이 결정이다.

### 3.5 조용시간 설정 키 계약 (PM 판정 M-1)

- `quietHours`에 `timeZone` 키를 추가한다. 미설정 시 기존 동작과 같은 `Asia/Seoul`을 적용하며, 기존 전역 설정 파일에 키가 없어도 **파일을 다시 쓰지 않고** 폴백한다(제안서 §5.2).
- `timeZone`은 기존 2층 머지의 **하위 키**로 들어간다 — 전역 `~/.opal/setting.json`의 `quietHours` 위에 프로젝트 `.opal/setting.local.json`의 `quietHours`를 하위 키 단위로 덮어쓰는 구조를 그대로 쓴다(`dashboard/backend/config.py`의 `load_quiet_hours`, 160행). 별도 로딩 경로를 만들지 않는다.
- **`quiet_hours_token` 캐시 키 서명에 `timeZone`을 Phase 1A에서 함께 포함한다.** 설정 키 추가와 서명 포함은 **한 단위**의 변경이다. 근거: 서명의 존재 이유가 "설정 변경 시 보정 전후 값이 같은 캐시 키를 공유하지 않게 한다"(`dashboard/backend/config.py` @header)인데 `timeZone`은 보정 결과를 바꾸는 설정이고, 현재 서명은 시작·끝 분만 담는다(같은 파일 204행). 서명에서 빼면 시간대만 바꾼 설정이 낡은 캐시를 반환한다. 겹침 계산의 실제 소비가 Phase 2인 것과 무관하다.
- 시드 원본 `opal/core/setting.default.json`과 `scripts/install-mac.sh`의 `SEED_KEYS` 배선을 함께 개정하되, 배포본을 직접 편집하지 않는다.

---

## 4. 기계검증절 (Machine-Verifiable Section)

아래는 결정론적으로 참·거짓이 갈리는 항목만 모은다. 각 항목은 고정 입력과 고정 판정을 갖는다.

**[MUST] 이 절은 같은 폴더의 `surfaces.json`을 필수 구성요소로 포함한다.** 표면 id는 백로그 태스크가 `--covers`로 가리키는 유일한 키이며, 모든 구현 태스크는 자기가 커버하는 표면 id를 선언해야 설계 루프의 커버리지 게이트를 통과한다(제안서 §9.1).

| MV-ID | 검증 대상 | 고정 입력 | 판정 | 대응 표면 | 근거 |
|---|---|---|---|---|---|
| MV-1 | 폐쇄형 스키마 | §1.1 밖의 최상위 키를 가진 payload | `schema_invalid` 거부 | `run-log-tool.append` | §5.1 / AC-6 |
| MV-2 | enum 조합 거부 | §1.3 표 밖의 actor×type×recorded_by×source 조합 전수 | 전건 `provenance_invalid` 거부 | `run-log-tool.append` | §4.3 / AC-6 |
| MV-3 | PM 대필 거부 | `actor.kind=worker` + `recorded_by.kind=PM` | 거부 | `run-log-tool.append` | §4.3 / AC-6 |
| MV-4 | terminal 유일성 | 같은 `worker_run_id`에 `worker.completed` + `worker.failed` | 두 번째 거부 | `run-log-tool.validate-worker` | §11 R-3 |
| MV-5 | 요청 식별자 멱등 | 같은 `(run_id, request_id)` 동일 payload 재호출 / 다른 payload 재호출 | 전자는 기존 event 반환(`idempotent_hit:true`), 후자는 `request_id_conflict` | `run-log-tool.append` | §5.1 / AC-7 |
| MV-6 | 출처 검증 | adapter 사건에서 `source.id`/`sha256`/`observed_at` 각각 결측 | 전건 거부 | `run-log-tool.append` | §5.1 |
| MV-7 | 완료 알림 분해 거부 | 같은 source ID인 activity+terminal / 같은 SHA-256인 쌍 / activity `observed_at`이 terminal보다 늦은 쌍 | 3건 모두 완료 거부 | `run-log-tool.validate-worker`, `state-tool.mark.completion-gate` | §4.3 / AC-5 |
| MV-8 | 강한 궤적 게이트 | `observed_trajectory` 채널에서 activity 없는 정상 완료 / `reason_code=pre_activity_failure` + adapter 기계 증거 있는 terminal | 전자 차단, 후자 통과 | `state-tool.mark.completion-gate` | §4.2·§4.3 / AC-4 |
| MV-9 | 게이트 기여 배제 | worker direct activity·import activity·PM activity만 있는 완료 | 완료 차단(`completion_evidence_missing`) | `state-tool.mark.completion-gate` | §4.3 / AC-6 |
| MV-10 | 순번 단조성 | 순차 append N건 | `sequence` 1..N 중복·누락 0, `actor_sequence` 주체별 단조 | `run-log-tool.validate-run` | §5.3 |
| MV-11 | 색인 재구축 동일성 | `run/.runtime/` 삭제 후 append / 손상 후 append | 재구축 뒤 동일 순번을 이어감. capability registry가 issued/revoked/terminal/expiry에서 전량 재구축 | `run-log-tool.append` | §5.3 / AC-9 |
| MV-12 | 조각 경계 전환 단일성 | 여러 프로세스를 4 MiB 경계 직전 barrier에 대기시킨 뒤 동시 해제 | 새 segment 정확히 1개, run-global sequence 중복·누락 0, 정상 mark 오탐 0. **barrier 대기 시간은 §2.7 락 상한(기본 30,000 ms)보다 충분히 짧게 잡는다** — 그렇지 않으면 판정이 `task_lock_timeout`과 뒤섞인다 | `run-log-tool.append` | §6.5 / AC-8 |
| MV-13 | 락 타임아웃 | 락을 보유한 프로세스를 상한 초과까지 유지한 뒤 두 번째 호출 | `task_lock_timeout` 반환, 자동 재시도 없음, 프로세스 종료 코드 ≠ 0 | 전 CLI 표면 | 본 계약 §2.7 (M-4) |
| MV-14 | 시간 변환식 | terminal `duration_ms` 표본 | `state.json` 분 투영 = `floor(duration_ms / 60000)`, 1분 미만 0 | `run-log-tool.reconcile-duration` | §7 / AC-12 |
| MV-15 | resume span 합산 | 같은 `worker_run_id`의 다중 process span / 같은 `source_id` 중복 span | 전자는 중복 없이 합산되고 terminal `duration_ms` = span 합, 후자는 거부 | `run-log-tool.validate-worker` | §5.2 / AC-12 |
| MV-16 | 1.2 수동 시간 거부 | 1.2 태스크에 파생값과 다른 `--worker-duration-minutes` | `worker_duration_conflict` | `state-tool.mark.completion-gate` | §7 / AC-12 |
| MV-17 | 마스킹 | secret fixture(환경변수형·bearer·API key·private key 블록)를 표준 로그·raw·import 3경로에 투입 | 3경로 디스크 산출물 어디에도 평문 0건. **문구 검사가 아니라 실제 파일 검사** | 전 writer 경로 | §8.3 / AC-13 |
| MV-18 | 추적/비추적 경계 | 태스크 실행 후 git 추적 목록 | `tasks/**/run/raw/`·`tasks/**/run/.runtime/`·`.opal-task.lock` 제외, 마스킹된 segment 추적. opt-in 없이 stdout·stderr·prompt 미저장 | — | §8.1 / AC-14 |
| MV-19 | 가져오기 멱등 | 같은 `.oppl-run/` 원본으로 import 2회 | 2회차 `imported:0`, `skipped_idempotent`가 1회차 수와 동일. import 사건은 완료 게이트 불기여 | `run-log-tool.import-oppl` | §3.4 / AC-15 |
| MV-20 | 계약 삭제 저항 | active 태스크의 기록 파일 삭제 / init 중단으로 첫 segment 부재 | 전자 `run_log_missing`(legacy 강등 없음), 후자는 pending `run.started` reconcile로 active 복구 | `state-tool.mark.completion-gate`, `run-log-tool.reconcile` | §6.1 / AC-3 |
| MV-21 | 보관함 상한·복구 | 연속 기록 실패 N건 | 전건 보존(사건당 4 KiB·전체 512 KiB 상한), reconcile 또는 사용자 override 1회로 해소. **reconcile이 현재 timestamp·stdout에서 사건을 합성하지 않음** | `run-log-tool.reconcile` | §6.2 / AC-10 |
| MV-22 | 게이트 쌍 | 모든 PM·사용자 gate / requested 없는 resolved / 중복 resolved | 전자는 같은 `gate_id` 쌍으로 대기 시간 재구성, 후 2건은 거부 | `state-tool.gate-request`, `state-tool.gate-resolve` | §4.4 / AC-11 |
| MV-23 | active 초기화 게이트 | `profiles.json`에 없는 채널로 active init / hash 불일치 / `cooperative` 채널 active | 각각 `profile_not_found`·`profile_receipt_mismatch`·`cooperative_active_rejected` | `state-tool.init.run-log-mode` | §4.2.1 / AC-18 |
| MV-24 | 단방향 의존 | 기록 도구 테스트 스위트 실행 | `state.json`·state fixture 없이 전건 통과 | `run-log-tool.*` 전 표면 | §6.4 / AC-19 / TRD D-5 |
| MV-25 | 기존 회귀 | `opal/tools/state-tool/tests/` 전체, `tasks/103-260825-opd-태스크-진행통계/STATS-BASELINE.md` 기준값, `dashboard/backend/tests/fixtures/t103_states/` 동결 fixture | 전건 통과. 기존 fixture 변경 금지. **추가 판정: `stats` 공개 함수의 `quiet_hours` 인자가 여전히 `tuple[int, int] | None`이고, `QuietHours` 3필드 타입이 `stats` 모듈 어느 공개 시그니처에도 나타나지 않는다**(§2.8.1 B-1·B-2) | — | TASK.md C-2 / AC-20 / 본 계약 §2.8.1 |
| MV-26 | 시간계 경계 | 날짜 경계 fixture(legacy KST·event UTC·quietHours `timeZone`) | 세 변환이 일치. `timeZone`만 다른 두 설정이 서로 다른 `quiet_hours_token`을 만든다. **추가 판정: 시간대 해석이 통계 호출 이전에 끝나 `stats`에는 확정된 분 구간만 전달된다**(§2.8.1 B-3) | — | §5.2 / AC-20 / 본 계약 §3.5·§2.8.1 |
| MV-27 | 경로 추론 금지 | 상대 경로 task path / cwd만 바꾼 호출 | 전자 `task_path_not_absolute`, 후자는 cwd와 무관하게 동일 결과 | 전 CLI 표면 | 본 계약 §3.2 (M-2) |
| MV-28 | shadow 비차단 | `run_log.mode=shadow` 태스크 | `AGENTIC-LOG.md` 유지, 완료 미차단. active 태스크에서는 `AGENTIC-LOG.md` 미생성 | `state-tool.mark.completion-gate` | §10 / AC-16 |
| MV-29 | 채널 원본 → 표준 사건 정규화 동일성 | 두 축 각각의 원본 fixture 쌍: (a) 같은 의미의 중간 진행 1건, (b) 같은 의미의 정상 종료 1건. 외부 에이전트 도구 축은 `agent_message`/`process_exit` 계열, 내부 헤드리스 CLI 축은 결과 파일 캡처/`process_exit` 계열 | 두 축의 변환 결과가 `event`, `actor.kind`, `provenance.type`, `provenance.recorded_by.kind`, `data.kind`(진행 사건) 또는 `reason_code` 분류(종료 사건)에서 **동일**하고, 폐쇄 enum 밖 값 0건이다. 축 간 차이는 `provenance.source.*`와 실행마다 달라지는 식별자·timestamp 필드에만 존재해야 하며, 그 외 필드에 축별 분기가 나타나면 실패다 | `adapter.pm-agent-tool`, `adapter.oppl-headless-cli` | §11 R-12 / §5.1 / TRD D-6 |

| MV-30 | 오류 코드 ↔ 표면 양방향 일치 | 두 자산: `CONTRACT.md` §2.2 오류 코드 표와 §2.2.1 대응, 그리고 `surfaces.json` | (a) §2.2 표의 모든 코드가 §2.2.1에 발생 표면을 갖는다, (b) §2.2.1이 지정한 표면의 `response_shape.err`에 그 코드가 있다, (c) `surfaces.json`의 모든 `err` 값이 §2.2 표에 존재한다, (d) `kind=cli` 17개 표면 전부가 `task_path_not_absolute`·`task_lock_timeout`을 갖는다. 4항 중 하나라도 어긋나면 실패. 검사 대상은 `kind=cli` 표면만이며 `adapter.*` 2종은 제외한다 | 전 CLI 표면 17종 | 본 계약 §2.2.1 / §9.1 |
| MV-31 | 등급의 호출 조건 종속 | `profiles.json`의 각 채널 항목과 해당 변환기의 실제 호출 조건 | `observation_preconditions`가 비어 있지 않은 채널에서, 변환기가 실제로 사용하는 호출 조건이 `condition`과 일치한다. 불일치하면 실패이며 배정을 무효로 판정한다. 필드 자체가 조건부 필수인데 비어 있어도 실패 | `adapter.pm-agent-tool`, `adapter.oppl-headless-cli` | 본 계약 §1.6 / Phase 0 실측 |

**변환기 표면 수에 관한 조항**: 변환기 표면의 최종 개수는 Phase 0 `profiles.json`의 active 채널 수로 확정된다(제안서 §9.1). 이 계약 시점에는 판정 대상 2축(`adapter.pm-agent-tool`, `adapter.oppl-headless-cli`)을 각각 1개 표면으로 등재하며, Phase 0 결과에 따라 `cooperative`로 판정된 축은 변환기를 만들지 않고 표면이 비활성으로 남는다.

---

## 5. 루브릭절 (Rubric Section)

이 절은 **이후 모든 명세 리뷰의 판정 기준 원천**이다. 기계로 판정할 수 없는 품질만 다루며, 기계 판정 가능한 항목은 §4로 보낸다.

척도는 Likert 1–5이고 1·3·5 지점에 관찰 가능한 앵커를 단다. 2·4는 인접 앵커 사이의 중간값으로 읽는다.

### RB-1 계약 완전성

호출자가 이 문서만 읽고 구현·검증을 시작할 수 있는가.

| 점수 | 앵커 |
|---|---|
| 1 | 필수 필드·enum·오류 코드 중 다수가 "추후 정의"로 남아 있어 구현 착수가 불가능하다 |
| 3 | 주요 표면은 정의됐으나 일부 필드의 필수/선택 구분이나 조건부 필수 조건이 비어 있어 구현자가 임의로 메워야 한다 |
| 5 | 모든 표면의 인자·응답·오류가 정의되고, 모든 필드에 타입·필수 여부·제약이 있으며, 조건부 필수는 조건이 명시돼 있다 |

### RB-2 계약 일관성

문서 내부에서 같은 대상을 두 번 다르게 말하지 않는가.

| 점수 | 앵커 |
|---|---|
| 1 | 같은 enum·상한·오류 코드가 절마다 다른 값으로 나타난다 |
| 3 | 값은 일치하지만 한 곳에만 있는 제약이 있어 다른 절을 읽은 구현자가 놓칠 수 있다 |
| 5 | 모든 값이 단일 정의 지점을 갖고 나머지는 그곳을 참조하며, 스키마·시그니처·경계·기계검증이 서로 모순 없이 교차 참조된다 |

### RB-3 설계 정합 (TRD 결정과의 일치)

계약이 TRD D-1~D-9의 결정을 그대로 구현 가능한 형태로 옮겼는가.

| 점수 | 앵커 |
|---|---|
| 1 | 계약 조항이 TRD 결정과 충돌한다(예: 기록 코어가 상태 파일을 읽는 시그니처) |
| 3 | 충돌은 없으나 일부 결정이 계약에 반영되지 않아 구현이 결정을 우회할 여지가 있다 |
| 5 | D-1~D-9 각각이 최소 1개 계약 조항 또는 기계검증 항목으로 집행되며, 결정을 우회하는 합법적 호출 경로가 없다 |

### RB-4 범위 준수 (Phase 경계·비목표)

PRD 비목표와 Phase 경계를 침범하지 않는가.

| 점수 | 앵커 |
|---|---|
| 1 | 비목표(2단 커밋, correction 체인, Console 분석 화면, Phase 2·3 항목)가 계약에 들어와 있다 |
| 3 | 명시적 침범은 없으나 Phase 2 소관 항목의 소유 주체가 모호해 다음 단계가 다시 물어야 한다 |
| 5 | 비목표가 계약에 없고, Phase 2·3으로 미룬 항목은 "이 계약이 정하지 않는다"는 종결 조항으로 명시돼 재질의가 발생하지 않는다 |

### RB-5 근거 인용 충실도

각 계약 조항이 제안서·프로젝트 규범의 어느 지점에서 왔는지 추적 가능한가.

| 점수 | 앵커 |
|---|---|
| 1 | 제안서에 없는 계약이 근거 없이 들어와 있다 |
| 3 | 대부분 인용이 있으나 절 단위로만 가리켜 어떤 문장이 근거인지 확인하려면 제안서 전체를 다시 읽어야 한다 |
| 5 | 모든 비자명 조항이 `문서 §절` 또는 `경로:줄번호`로 근거를 달고, 제안서에 없는 조항은 PM 판정임을 명시하고 판단 근거를 함께 적는다 |

### 통과선

- **전 축 4점 이상**이면 통과한다.
- 어느 한 축이라도 **2점 이하**이면 점수 합과 무관하게 즉시 반려한다.
- RB-3(설계 정합)과 RB-4(범위 준수)는 **3점 이하이면 반려**한다. 두 축의 실패는 이후 구현 태스크 전체가 잘못된 전제 위에 서게 만들기 때문이다.
