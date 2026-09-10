# OPAL 태스크 전체 여정 실행 로그 설계 제안서

> 상태: 제안
> 작성: 알투(PM)
> 작성일: 2026-09-10
> 목적: 태스크 전체 실행 여정과 워커 진행 기록을 보존하여 사후 분석 가능성을 확보

---

## 1. 목적과 범위

OPAL 태스크가 시작된 시점부터 종료될 때까지 발생한 실행 사건을 태스크 폴더 안에 보존한다.

기록 대상은 다음 파이프라인 전체다.

```text
TASK → ANALYSIS → PLAN → TEST-SCENARIO → EXECUTE → TEST → CLOSE
```

태스크 유형에 따라 `SPEC`, `REVIEW`, `DESIGN`, `WBS`, `WIREFRAME`, `DICT`, `MODEL`, `DDL/MIGRATION`,
`SCAN`, `CHECK`, `REPORT` 등 추가 단계를 포함한다. 단계 목록의 기준은 각 pilot의 `pipeline.json`과
`state-tool` 스키마가 소유한다.

기본 저장 구조는 다음과 같다.

```text
tasks/{태스크 폴더}/
└── run/
    ├── run-log.jsonl       # 표준 실행 이벤트, append-only
    ├── run-manifest.json    # 로그 계약 활성화·스키마 버전
    └── raw/                # 긴 출력·프롬프트·플랫폼 원본 스트림
```

`run-manifest.json`이 있는 태스크는 표준 실행 로그 계약을 사용한다. manifest가 없는 기존 태스크는
legacy 모드로 판정하여 `run-log` 부재만으로 기존 `state-tool` 상태 전이를 차단하지 않는다.
로그 파일의 일시적 부재를 legacy 판정 근거로 사용하지 않으며, 새 태스크는 `state-tool init` 시
manifest를 먼저 생성한다.

---

## 2. 핵심 요구사항

### 2.1 전체 여정 복원

태스크의 현재 상태만이 아니라 다음 질문에 답할 수 있어야 한다.

- 어느 단계에서 언제 시작하고 끝났는가?
- 어떤 워커가 어떤 Work item을 담당했는가?
- 워커가 어느 시점에 무엇을 진행했는가?
- 어떤 판단을 했고 근거는 무엇인가?
- 어떤 파일을 만들거나 수정했는가?
- 어떤 검증을 실행했고 결과는 무엇인가?
- 왜 재시도하거나 중단했는가?
- PM 또는 사용자의 확인을 얼마나 기다렸는가?

### 2.2 워커 진행 기록 우선

핵심 기록 대상은 `EXECUTE 완료` 같은 최종 상태가 아니라 워커의 작업 궤적이다.

워커는 최소한 작업 시작, 의미 있는 진행, 판단, 검증, 재시도·블로커, 종료 사건을 남긴다.

### 2.3 분석 가능한 구조

로그는 사람이 읽을 수 있어야 하지만, 주요 필드는 기계적으로 집계할 수 있어야 한다.
자유 문장은 `summary`와 `reason`으로 제한하고, 단계·워커·작업 항목·상태·시각·소요 시간은
구조화된 필드로 둔다.

---

## 3. 현행 구조와 한계

### 3.1 `state.json`

`state.json`은 현재 파이프라인 상태의 SSOT다. 행 상태, 현재 상태, 다음 액션을 조회하는 데 적합하지만,
각 상태가 어떻게 변화했는지에 대한 append-only 사건 이력은 아니다.

근거: `opal/core/references/harness/state.md` §STATE.md 기본 구조.

### 3.2 워커 소요 시간

현재 워커 시간은 완료 시 반환되는 `duration_ms`를 PM이 분 단위로 환산하여
`rows[].worker_duration_minutes`에 기록하는 구조다. 따라서 워커 전체 소요는 남지만 작업 중간의
진행·판단·검증 순서는 남지 않는다.

근거: `opal/tools/state-tool/schema/state.schema.json` `worker_duration_minutes` 필드.

### 3.3 Project Loop의 부분 선례

Project Loop는 비동기 워커의 원본 스트림을 `.events.jsonl`에, 게이트 판단·재시도·블로커를
`journal.md`에 기록한다. 다만 특정 액션 에이전트와 Claude 원본 스트림에 결합된 구현이므로
모든 pilot의 공통 로그 계약으로 바로 사용할 수는 없다.

근거: `opal/agents/opal-loop-action-agent/AGENT.md` §결과 파일 규약 및 §운행 일지.

### 3.4 디스패치 채널별 보장 범위

현재 워커 실행은 하나의 수집 경로가 아니다.

| 채널 | 현재 확인되는 수집 방식 | run-log에 보장할 수 있는 범위 |
|---|---|---|
| `opal-agent` CLI 채널 | 실행 래퍼가 stdout·stderr·종료 코드·원본 스트림을 파일로 캡처 | 디스패치·시작·종료·소요 시간·원본 출력 자동 기록 |
| Agent 도구 채널 | PM이 Agent 도구를 호출하고 완료 알림을 받음 | 디스패치·완료 알림·`duration_ms`·워커가 명시적으로 보낸 이벤트 |

Agent 도구 내부가 어떤 프로세스 구조로 실행되는지는 PM이 관측하거나 외부 래핑할 수 있는 계약이 아니다.
따라서 일반 Agent 채널에 CLI 스트림 자동 캡처를 전제하지 않는다.

### 3.5 현행 결론

현재 기록은 `현재 상태`, `일부 총소요`, `특정 루프의 원본 실행 증거`로 나뉘어 있다.
일반 태스크와 일반 워커의 전체 실행 여정을 하나의 표준 이벤트 흐름으로 복원하는 공통 계층은 없다.

---

## 4. 기록 자산의 역할 분리

| 자산 | 역할 | SSOT 성격 |
|---|---|---|
| `state.json` | 현재 파이프라인 상태와 유효한 행 상태 | 현재 상태 SSOT |
| `STATE.md` | 사람이 읽는 의사결정·블로커·자유 기재 저널 | 서술 저널 |
| `run/run-log.jsonl` | 태스크 전체 실행 사건과 분석용 이력 | 실행 이력 원천 |
| `run/run-manifest.json` | 표준 로그 계약 활성화 여부·스키마 버전·적용 모드 선언 | 실행 로그 계약 메타데이터 |
| `run/raw/` | 긴 출력·프롬프트·플랫폼별 원본 | 원본 증거 |
| `.events.jsonl` 등 기존 파일 | 특정 실행 채널의 원본 증거 | 호환·참조 자산 |

`run-log.jsonl`은 `state.json`을 대체하지 않는다. 현재 상태 조회는 계속 `state-tool`을 사용하고,
전체 이력 분석은 `run-log.jsonl`을 사용한다.

`run-log.jsonl`을 tool-gated 실행 이력 SSOT로 채택하면 `docs/PROJECT.md`의 3-SSOT 목록에
네 번째 축으로 등록하고, 기존 `backlog.json`·`state.json`·`test-scenario.json`과의 소유권을
분리해 명시해야 한다.

---

## 5. 표준 이벤트 종류

### 5.1 태스크·단계 이벤트

| 이벤트 | 기록 내용 |
|---|---|
| `task.created` | 태스크 ID, 스킬, 모드, 목표, run ID |
| `stage.started` | 단계명, 시작 시각, 담당 주체, 산출물 |
| `stage.completed` | 종료 시각, 결과, 산출물, 총 소요 |
| `state.transition.requested` | 상태 전이 의도, 대상 행, 요청 시각 |
| `state.transition.committed` | 실제 상태 커밋, 대상 행, 커밋 시각 |
| `task.completed` | 전체 종료, 최종 결과, 미해결 이슈 |

### 5.2 워커 이벤트

| 이벤트 | 기록 내용 |
|---|---|
| `worker.dispatched` | 에이전트, 모델, 단계, Work item, 세션, 프롬프트 경로 |
| `worker.started` | 실제 작업 시작 시각과 목표 |
| `progress` | 완료 항목, 남은 항목, 현재 활동, 다음 활동, 진행률 |
| `worker.completed` | 결과, 변경 파일, 검증 결과, `duration_ms` |
| `worker.failed` | 실패 유형, 오류 요약, 원본 오류 경로 |
| `worker.lost` | 종료 이벤트 미수신, 타임아웃 또는 프로세스 단절 |

### 5.3 판단·산출물·검증 이벤트

| 이벤트 | 기록 내용 |
|---|---|
| `decision` | 결정 요약, 이유, 대안, 근거, 사용자 결정 필요 여부 |
| `artifact.changed` | 파일 경로, 생성·수정·삭제, 변경 요약 |
| `validation.started` | 검증 종류, 실행 명령, 시작 시각 |
| `validation.completed` | 종료 코드, 결과, 소요 시간, 출력 경로 |
| `correction` | 정정 대상 이벤트 ID, 정정 이유, 교정 필드·값 |

### 5.4 예외·대기 이벤트

| 이벤트 | 기록 내용 |
|---|---|
| `retry` | 회차, 대상, 원인, 이전 시도 ID |
| `blocked` | 차단 단계, 원인, 필요한 조건, 에스컬레이션 여부 |
| `gate.requested` | PM Gate 또는 사용자 확인 요청 |
| `gate.resolved` | 판정, 판정 주체, 근거, 대기 시간 |

---

## 6. 이벤트 공통 스키마

```json
{
  "schema_version": "1.0",
  "event_id": "evt_01...",
  "sequence": 42,
  "timestamp": "2026-09-10T14:32:08+09:00",
  "task_id": "111-260909-opd-SDLC-템플릿-하네스개편",
  "run_id": "run_01...",
  "parent_run_id": null,
  "stage": "EXECUTE",
  "task_step": "execute.implement",
  "work_item": "F-003",
  "event": "progress",
  "actor": {
    "kind": "worker",
    "id": "opal-task-agent",
    "provider": "codex",
    "session_id": "..."
  },
  "summary": "state-tool 기록 경로 구현 완료",
  "reason": null,
  "duration_ms": null,
  "refs": ["opal/tools/state-tool/state_tool.py"],
  "data": {}
}
```

필수 식별자는 `event_id`, `sequence`, `timestamp`, `task_id`, `run_id`, `stage`, `event`, `actor`다.
`sequence`는 동시 기록 상황에서도 태스크별 사건 순서를 검증하기 위한 값이다.

`parent_run_id`는 중첩 실행을 연결하는 선택 필드다. 일반 태스크에서는 생략하거나 `null`로 두며,
`oppl`의 Loop 1·Loop 2와 동적 하위 태스크에서는 상위 실행의 `run_id`를 가리키는 값으로 필수화한다.

`correction`은 기존 이벤트를 수정·삭제하지 않고 잘못된 이벤트의 `event_id`를 가리키는 추가 사건이다.
정정 이벤트 자체도 원본과 동일한 append-only 검증을 받는다.
분석기는 `state.transition.committed`만 실제 상태 전이로 집계하며, `requested`만 존재하는 사건은
미적용 요청으로 분류한다.

---

## 7. 워커 기록 계약

모든 워커 디스패치 프롬프트에는 다음 기록 계약을 주입한다.

```text
worker.started
progress                 의미 있는 작업 경계마다
decision                 판단이 발생한 경우
validation               검증을 수행한 경우
retry                    재시도한 경우
blocked                  진행을 중단한 경우
worker.completed|failed  종료 시 반드시 1건
```

워커 완료를 인정하기 위한 최소 조건은 다음과 같다.

- `worker.started`가 존재함
- `worker.completed` 또는 `worker.failed`가 존재함
- 종료 이벤트에 결과 요약이 있음
- 실행 시간 또는 미측정 사유가 있음
- 실패·블로커인 경우 원인이 있음

종료 이벤트가 없으면 PM은 정상 완료가 아니라 `worker.lost` 또는 `blocked`로 처리한다.

이 중 `worker.started`, 종료 이벤트, 필수 상태 전이 이벤트는 **필수 이벤트**다. 필수 이벤트 기록이
실패하면 정상 완료를 허용하지 않고 `run_log_write_failed` 또는 `run_log_missing`으로 차단한다.
`progress`, heartbeat, 상세 원본 참조는 **선택 이벤트**로 두며 기록 실패 시 경고만 남길 수 있다.

단순 산문 지시만으로 끝내지 않기 위해 채널별 수집 경로와 완료 게이트를 조합한다.

- `opal-agent` CLI 채널: `run-log-tool` + CLI 실행 래퍼 + 완료 게이트
- 일반 Agent 채널: `run-log-tool` + 완료 게이트

---

## 8. 기록 수집 방식

### 8.1 `run-log-tool`

태스크별 로그에 이벤트를 추가하고 조회·검증·요약하는 결정론적 도구를 둔다.

```text
run-log-tool append \
  --task <task-path> \
  --event progress \
  --stage EXECUTE \
  --summary "..."
```

도구는 append-only, 파일 잠금, 단조 `sequence`, JSON 스키마 검증, 손상 행 진단을 담당한다.
필수 이벤트 쓰기 실패는 예외를 흡수하지 않고 호출자에게 실패를 반환한다. 선택 이벤트 쓰기 실패는
경고로 반환할 수 있다.

### 8.1.1 로그 오류 계약

아래 코드는 이 제안서의 실행 로그 오류 계약 초안이다. 구현 시 최종 SSOT는 `run-log-tool`의
오류 코드 문서로 승격한다.

| 오류 코드 | 발생 조건 | 처리 |
|---|---|---|
| `run_log_write_failed` | 필수 이벤트를 파일에 기록하지 못함 | 상태 변경·정상 완료 차단 |
| `run_log_missing` | 필수 종료 이벤트 또는 필수 상태 전이 이벤트가 없음 | `mark`·CLOSE 진입 차단 |
| `run_log_inconsistent` | state와 `requested/committed` 로그를 자동 정합화할 수 없음 | 복구 전 진행 차단 |

### 8.2 `state-tool` 연동

`state-tool`의 `init`, `advance`, `mark`, `block`, `add-row`, `status` 호출은 대응 이벤트를 자동으로 남긴다.
표준 로그 계약이 활성화된 태스크에서는 `state.transition.requested` 기록 후 상태를 커밋하고,
성공 직후 `state.transition.committed`를 기록한다. 필수 이벤트 기록 실패는 예외를 흡수하지 않고
`run_log_write_failed`로 반환하며 상태 변경 또는 정상 완료를 fail-open으로 통과시키지 않는다.

두 파일의 완전한 원자적 커밋은 보장 대상이 아니므로 부분 실패를 명시적으로 복구한다.

- `requested`만 남음: 상태 미적용 요청으로 유지
- 상태 커밋 후 `committed` 누락: `run-log-tool reconcile`이 state와 로그를 대조하여 보정
- 대조 결과를 자동 확정할 수 없음: `run_log_inconsistent`로 차단
- 잘못된 이벤트를 무효화할 때: `correction`에 대상 이벤트와 정정 이유를 기록

manifest가 없는 legacy 태스크에는 위 fail-closed 계약을 적용하지 않고 기존 상태 전이를 유지한다.

### 8.3 채널별 수집

`opal-agent` CLI 채널에서만 실행 래퍼가 디스패치·시작·종료 코드·종료 시각·벽시계 소요 시간과
stdout·stderr·프롬프트 원문을 자동 기록한다. 원문은 `run/raw/`에 두고 표준 로그에서는 경로만 참조한다.

일반 Agent 도구 채널은 PM이 외부 프로세스로 감쌀 수 없으므로 자동 stdout 캡처를 보장하지 않는다.
이 채널에서는 완료 알림의 `duration_ms`와 워커가 `run-log-tool`로 명시한 이벤트를 수집한다.

### 8.4 채널·플랫폼 어댑터

Claude·Cursor·Gemini·Codex의 원본 출력 형식을 공통 로그의 SSOT로 삼지 않는다.
각 플랫폼·실행 채널 어댑터가 확보 가능한 원본과 완료 알림을 표준 이벤트로 변환한다.

실시간 스트림이 없는 채널에서는 시작·완료·실패·총 소요와 워커가 명시적으로 보낸 진행 이벤트까지만 보장한다.

---

## 9. 분석 가능 범위

### 9.1 시간

- 단계별·워커별 실행 시간
- PM 대기와 사용자 확인 대기
- 검증에 소비된 시간
- 재시도로 추가된 시간
- 병렬 처리와 직렬 처리의 차이

### 9.2 품질

- 실패가 집중되는 단계
- 반복되는 블로커
- 재시도가 많은 Work item
- 검증 실패 유형
- 결정이 나중에 번복되는 빈도

`run-log.jsonl`은 위 품질 신호의 사실 원천이고, `improve-tool`은 이를 개선 후보로 분류·기록하는
후속 집행 도구다. `run-log`가 개선 판단을 대신하거나 `.opal/MEMORY.json`을 직접 갱신하지 않는다.

### 9.3 운영

- 에이전트·모델별 처리량과 소요 시간
- 태스크 유형별 리드타임
- 사용자 개입 횟수
- 워커 완료 누락률
- 단계별 병목과 무진전 구간

### 9.4 Console 연계

기존 Console 통계는 `state.json` 기반 계산을 유지할 수 있다.
이후 `run-log-tool summary`를 통해 워커 진행률, 재시도율, 블로커 원인, 결정 지연과 같은 이력 기반 지표를 추가한다.

기존 `opal-action-monitor`는 `.oppl-run/` 전용 읽기 도구로 유지하되, 표준 로그를 소비하는
공통 타임라인·현황 렌더러로 확장하거나 별도 `run-log-monitor`를 둔다. 기존 모니터의
`.oppl-run/` 판독 계약과 `run-log.jsonl`의 표준 이벤트 계약은 상호 변환 계층으로 연결한다.

---

## 10. 보존·안전 원칙

- `run-log.jsonl`은 append-only로 운영한다.
- 정정이 필요하면 기존 이벤트를 수정하지 않고 정정 이벤트를 추가한다.
- 로그에 비밀값·인증 토큰·불필요한 사용자 개인정보를 넣지 않는다.
- 숨은 내부 사고 전문은 기록하지 않고, 검증 가능한 결정 요약과 근거만 기록한다.
- 원본 출력은 표준 로그와 분리하여 크기 증가와 분석 비용을 통제한다.
- `run-log.jsonl`은 사용자 데이터이므로 git 추적 여부와 보존 기간을 별도 정책으로 결정한다.

---

## 11. 구현 단위

1. `run-log-tool` 신규 도구와 이벤트 스키마
2. append-only·동시 기록·순번 보장
3. `state-tool` 이벤트 연동
4. `opal-agent` CLI 채널 전용 실행 래퍼 연동
5. 전체 워커용 채널별 기록 계약 주입
6. `state-tool mark`와 CLOSE 진입 시 `worker.completed` 누락 검증 게이트 (`run_log_missing`)
7. Agent 채널의 완료 알림·워커 자발 이벤트 수집 경로
8. Project Loop 기존 `.events.jsonl`·`journal.md`와 표준 이벤트 연결
9. `docs/PROJECT.md` 3-SSOT 목록과 실행 이력 SSOT 등록·소유권 경계 갱신
10. `improve-tool`·`pm-improvement-loop.md`와 실행 사실/개선 판단 경계 연결
11. `opal-action-monitor`의 `.oppl-run/` 소비와 표준 로그 타임라인 연결
12. 로그 조회·검증·요약 명령
13. Console 분석 API·화면 확장
14. `run-manifest.json` 생성과 legacy 태스크 하위호환 판정
15. `state.transition.requested/committed` 2단 기록과 `run-log-tool reconcile`
16. 필수 이벤트 쓰기 실패·선택 이벤트 실패·정정 이벤트 검증
17. 단위·통합·실행 흐름 테스트

변경 범위가 여러 도구·에이전트·파이프라인에 걸리고 동작 검증이 필요하므로 정식 `//opd` 태스크로 다루는 것이 적합하다.

---

## 12. 수용 기준 초안

- 모든 표준 skill 식별자(`opd`, `opds`, `opdw`, `opp`, `opwt`, `opgc`, `oppd`, `opsdd`, `oppl`, `opdd`)가 태스크 시작부터 종료까지 최소 실행 이벤트를 남긴다.
- `opds`는 `opd`의 Short profile alias로 기록되며, 로그 계약은 `opd`와 동일하게 적용된다.
- `oppl`의 Loop 1·Loop 2와 동적 하위 태스크는 `stage`, `task_step`, `parent_run_id`로 표준 로그에 매핑된다.
- 새 태스크는 `run-manifest.json`으로 표준 로그 계약을 활성화한다.
- manifest가 없는 기존 태스크는 legacy 모드로 종전 `state-tool` 상태 전이를 유지한다.
- 모든 워커가 시작·종료 이벤트를 남기며, 누락 시 정상 완료로 판정되지 않는다.
- 필수 이벤트 쓰기 실패가 `run_log_write_failed`로 반환되고, 상태 변경 또는 정상 완료가 fail-open으로 통과하지 않는다.
- `state.transition.requested`만 존재하는 사건은 완료 전이로 집계되지 않는다.
- 상태 커밋 후 `committed` 이벤트가 누락되면 `reconcile` 또는 `run_log_inconsistent` 경로로 처리된다.
- 워커 담당 행의 `state-tool mark`와 CLOSE 진입에서 종료 이벤트 누락이 `run_log_missing`으로 차단된다.
- 워커가 명시적으로 보낸 진행·판단·검증 이벤트가 태스크별 `run-log.jsonl`에 보존된다.
- 동일 태스크의 여러 프로세스가 동시에 기록해도 JSONL이 손상되지 않는다.
- 기존 `state.json` 조회·상태 전이·통계 동작이 회귀하지 않는다.
- 재시도·블로커·게이트·사용자 확인 대기 시간을 로그에서 재구성할 수 있다.
- 로그 검증 도구가 순번 역행, 필수 필드 누락, 잘못된 이벤트 유형을 진단한다.
- 플랫폼별 원본 형식이 달라도 표준 이벤트 스키마로 분석할 수 있다.
- `backlog.json`·`state.json`·`test-scenario.json`·`run-log.jsonl`의 소유권과 상호 참조 경계가 문서에 등록된다.
- `improve-tool`이 실행 로그를 개선 후보로 분류하고, 실행 로그 자체와 역할이 중복되지 않는다.
- 기존 `opal-action-monitor`가 표준 로그 또는 변환 계층을 통해 태스크 타임라인을 조회할 수 있다.

---

## 13. 결정이 필요한 항목

| 항목 | 선택지 |
|---|---|
| 로그 보존 | 태스크 폴더와 함께 영구 보존 / 별도 아카이브 |
| git 추적 | 로그를 git에 포함 / 기본 제외하고 필요 시 첨부 |
| legacy 전환 | manifest 없는 기존 태스크는 legacy 유지 / 일괄 migration |
| 명칭 호환 | 표준 로그는 `run/`, 기존 oppl 원본은 `.oppl-run/` 유지 |
| Console 1차 범위 | 워커 타임라인 / 병목·재시도 분석 / 둘 다 |

---

## 14. 최종 방향

OPAL의 기록 구조는 다음처럼 분리하는 것이 가장 안정적이다.

```text
모든 파이프라인 단계
        ↓
워커·PM·도구의 표준 이벤트 생성
        ↓
태스크별 run/run-log.jsonl
        ↓
조회·검증·통계·병목 분석
```

핵심은 `run-log.jsonl`을 단순 출력 파일이 아니라 **태스크 전체 여정을 재구성할 수 있는 표준 실행 이벤트 원천**으로 정의하는 것이다.
