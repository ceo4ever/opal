# run-log-tool

태스크 실행 로그 기록 CLI. `run_log_core.py`(기록 코어)를 감싸는 외부 호출 표면이며, 표준
사건을 append 전용 줄 단위 기록 조각(`run/run-log-{run_id}-{segment}.jsonl`)에 기록한다.
전문은 `docs/run-log/CONTRACT.md`·`docs/run-log/TRD.md`가 소유하며, 이 README는 설치된
5서브명령의 사용례와 오류 코드 카탈로그만 다룬다.

## 서브명령 (5종)

```bash
run-log-tool init --task <절대경로> --run-id <run_id> [--format json]

run-log-tool append --task <절대경로> --run-id <run_id> --request-id <id> \
  --event <event_type> --actor-kind <kind> --actor-id <id> \
  --provenance-type <type> --recorded-by-kind <kind> \
  [--summary <text>] [--data <json>] [--worker-run-id <id>] [--gate-id <id>] \
  [--stage <id>] [--task-step <id>] [--work-item <id>] [--refs <path>...] \
  [--source-kind <kind>] [--source-id <id>] [--source-sha256 <hex64>] \
  [--source-observed-at <rfc3339ms>] [--source-locator <text>] \
  [--upstream-event-id <id>] [--caused-by-event-id <id>] \
  [--reason <text>] [--reason-code <code>] \
  [--duration-ms <int>] [--duration-source <source>] [--duration-unknown-reason <text>] \
  [--mode <shadow|active>] [--format json]

run-log-tool validate-run --task <절대경로> --run-id <run_id> [--format json]

run-log-tool import-agentic --task <절대경로> [--run-id <run_id>] [--dry-run] [--format json]

run-log-tool import-oppl --task <절대경로> [--run-id <run_id>] [--dry-run] [--format json]
```

- `append`의 `--mode`(선택, `shadow`/`active`)는 §1.3 말미의 active 전용 source 제약을
  게이트한다. 미지정 시 그 제약을 적용하지 않는다 — 도구는 이 값을 어디서도 읽지 않고
  호출자가 전달한 값만 소비한다(D-5 단방향 의존 유지).
- `import-agentic`은 `<task-path>/AGENTIC-LOG.md`(legacy 실행 일지)를, `import-oppl`은
  `<task-path>/.oppl-run/`(Project Loop 원본)을 단방향·멱등으로 표준 사건(조합 A8,
  `event=activity`)으로 정규화해 append한다. 둘 다 완료 게이트에 기여하지 않으며 역변환하지
  않는다. `--run-id` 생략 시 `run/` 조각 파일명에서 유일한 run_id를 찾고, 0개면
  `run_log_missing`, 2개 이상이면 `schema_invalid`로 거부한다.
  응답 필드: `scanned`(인식한 원본 항목 수) / `imported`(신규 적재) /
  `skipped_idempotent`(기존 사건과 동일해 건너뜀) — 항상 `scanned == imported +
  skipped_idempotent`. `import-oppl`은 추가로 `sources`(소비한 원본 파일별
  `path`/`sha256`/`scanned`) 배열을 낸다. `--dry-run`은 append를 호출하지 않고 같은 수치를
  계산만 한다.

## 응답 봉투 — 두 계열이 병존한다 (F-1)

`run-log-tool`(이 도구)과 `run_log_core`는 CONTRACT §2.1이 정한 **중첩 봉투**를 쓴다:

```json
{"ok": true,  "data": {"...": "..."}}
{"ok": false, "error": {"code": "<ERROR_CODE>", "message": "...", "detail": {"...": "..."}}}
```

`ok:false`의 프로세스 종료 코드는 0이 아니다.

**상태 도구(`state-tool`)의 신규 run-log 경로**(예: `init --run-log-mode`)는 이 봉투를 쓰지
않는다 — 상태 도구는 기존 `err()`의 **평면 봉투**(`{"ok":false,"command":...,"error":"<code>","message":...}`)를
그대로 유지한다. 두 도구가 서로 다른 봉투 계열을 쓰는 것은 결함이 아니라 각 도구의 기존
관례를 보전하기 위한 의도된 경계다 — 상태 도구 쪽 봉투를 바꾸면 그 도구의 동결 회귀
테스트가 깨진다. `CONTRACT.md §2.2.1`이 "전 CLI 표면 17종 공통"으로 선언한
`task_path_not_absolute`·`task_lock_timeout` 두 코드도 이 경계를 따라 `run-log-tool`에서는
중첩, `state-tool`에서는 평면으로 나온다. 계약 본문(§2.1) 자체의 정정은 이 도구의 소관이
아니며 PM이 판단한다.

## 오류 코드 카탈로그 (8종)

`run_log_core.RUN_LOG_ERROR_CODES`가 SSOT다 — `state_tool.ERROR_CODES`와 물리적으로
분리된 별도 테이블이며, 상태 도구의 동결 회귀 테스트를 건드리지 않는다(PLAN D-A).

| 코드 | 조건 |
|---|---|
| `task_path_not_absolute` | `--task`가 절대 경로가 아님 (§3.2) |
| `task_lock_timeout` | 배타 락 대기가 상한(기본 30,000ms)을 초과함 (§2.7) |
| `run_log_write_failed` | 조각 생성·append·fsync 실패, 또는 가져오기 원본이 심볼릭 링크·태스크 경계 밖 |
| `run_log_missing` | `append`/`validate-run` 대상 실행 디렉터리·조각 부재, 또는 가져오기 원본(`AGENTIC-LOG.md`/`.oppl-run/`) 부재 |
| `schema_invalid` | 폐쇄형 최상위 키·`event` enum·사건별 조건부 필수 필드 위반, 또는 `--run-id` 생략 시 조각의 run_id가 여럿이라 모호함 |
| `provenance_invalid` | §1.3 4축 허용 조합 표 밖, 사건별 actor 제약 위반, adapter/import 필수 증거 결측·형식 위반, active 모드 source 제약 위반 |
| `request_id_conflict` | 동일 `(run_id, request_id)`에 다른 payload를 재사용 |
| `event_too_large` | 직렬화(마스킹 후) 크기가 16 KiB를 초과 |

`profile_not_found`는 이 테이블에 없다 — 그 의미(`profiles.json` 배정값 판정)는 CONTRACT
§3.1이 `state-tool` 소유로 규정한 영역이므로, 상태 도구 쪽 `RUN_LOG_STATE_ERROR_CODES`
테이블이 발신한다.

## 단방향 의존 (D-5)

이 도구와 `run_log_core.py`는 상태 원천 파일을 읽지도 쓰지도 않으며, 상태 도구 모듈을
import하지 않는다. `opal/tools/run-log-tool/tests/`는 상태 자산 없이 전건 통과한다
(AC-19 / MV-24).

## 마스킹 초크포인트 (D-9)

`run_log_core.redact()`가 디스크 직렬화 직전 공통 마스킹 경로다. 현재는 pass-through이며
본문을 채우는 것은 이 도구가 다루지 않는 범위다 — writer별 개별 마스킹은 추가하지 않는다.
가져오기(`import-agentic`/`import-oppl`)가 만든 사건도 append() 내부에서 이 초크포인트를
그대로 통과하므로, 이 함수의 본문이 채워지면 가져오기 경로에도 자동 적용된다.

## 가져오기 읽기 경로의 방어

`import-agentic`/`import-oppl`이 읽는 원본(`AGENTIC-LOG.md`, `.oppl-run/journal.md`,
`.oppl-run/*.result.json`, `.oppl-run/*.events.jsonl`, `.oppl-run/*.exitcode`)은 조각 경로와
같은 방어를 거친다 — 파일 자신 또는 `.oppl-run/` 자체가 심볼릭 링크이거나 해석 결과가
태스크 경계 밖이면 거부하고(`_reject_symlink_or_escape`), 열기는 `O_NOFOLLOW`
(`_safe_read_bytes`)로 TOCTOU·링크 추종 간극을 없앤다. 신뢰 불가 원본의 디코딩 실패·JSON
타입 불일치·과도한 중첩·달력상 불가능한 시각은 예외를 밖으로 던지지 않고 해당 행·파일만
건너뛰며 배치 전체를 막지 않는다.
