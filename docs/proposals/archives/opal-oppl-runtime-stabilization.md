# OPPL 독립 Pilot 실행 안정화 제안서

> 상태: 적용완료
> 작성: 알투(PM)
> 작성일: 2026-09-13
> 목적: 수렴형 프로젝트에 사용하는 독립 Pilot인 OPPL의 장시간 실행, 반복 상한, 완료 판정을 도구로 집행한다.

---

## 1. 결론

OPPL은 목표·계약·백로그가 실행 증거에 따라 반복적으로 바뀌는 프로젝트를 위한 독립 Pilot로 유지한다.
확정된 실행 계약을 처리하는 다른 프로젝트 Pilot의 대체재나 후계 후보로 정의하지 않는다.

OPPL의 핵심은 무제한 반복이 아니라 **유한한 예산 안에서의 수렴**이다. 다음 질문에 `아니요`라면
OPPL 사용 대상이다.

> 한 번의 설계 승인 후 목표·계약·백로그를 잠그고, 이후 변경을 예외로 처리할 수 있는가?

- `예`: 고정된 실행 계약을 처리하는 프로젝트 실행 Pilot을 사용한다.
- `아니요`: OPPL로 설계와 실행을 반복하되 모든 회전은 도구가 집행하는 상한 안에서 수행한다.
- 단순 정보 결측이나 높은 기술 난이도만으로 OPPL을 선택하지 않는다.

OPPL은 다음 업무에 적합하다.

- 원인과 해법이 미확정인 안정성·성능 개선을 목표 수치까지 수렴시키는 작업
- 실험 결과에 따라 품질 기준·계약·백로그를 조정해야 하는 AI·추천·자동화 기능
- 구현 중 발견되는 현행 제약 때문에 설계와 작업 순서를 반복 재구성해야 하는 현대화 작업
- 사용자 검증 결과가 다음 기능 범위를 결정하는 탐색형 제품 개발

## 2. 범위와 비범위

### 2.1 포함

1. OPPL Loop 1·Loop 2·태스크 내부 반복의 유한 상한 집행
2. 장시간 워커의 process group·heartbeat·watchdog·자식 작업 회수
3. 결과 이벤트·프로세스 종료·자식 종료·exit code의 결합 판정
4. 동일 컨텍스트 재개 상한과 새 attempt 전환
5. 예산·무진전·T4b 실패 전이의 dispatch 차단
6. 기존 `opal-action-monitor` 상태 계약과의 호환
7. `BACKLOG.md` 파생 뷰의 갱신 시각 정합성

### 2.2 제외

- 다른 프로젝트 Pilot로의 기능 이관이나 OPPL 폐기
- 신규 프로젝트 스케줄러 또는 범용 Controller
- 검증 결과 캐시
- 잠긴 test-scenario spec 기준선의 사후 갱신
- `AGENTIC-LOG.md` 또는 차세대 run-log의 집계 설계
- OPPL과 무관한 전역 에이전트 실행 이력 표준화

잠금 기준선 변경은 RED-first 봉쇄의 별도 거버넌스 결정이고, 실행 로그 표준화는 해당 제안서가
소유한다. 이 문서에서 함께 구현하지 않는다.

## 3. 확인된 현행 결함

### 3.1 무출력 watchdog 부재

`opal-agent`의 stream 경로는 stdout 줄을 받은 뒤에만 deadline을 확인한다
(`opal/tools/opal-agent/opal_agent.py:694-721`). 출력이 없는 프로세스는 제한 시간을 지나도 종료되지
않는다. 동기 경로의 timeout도 직접 자식만 대상으로 하며 process group 생성·회수 계약이 없다.

### 3.2 결과 뒤 이벤트로 인한 정상 작업 오판

현재 파서는 stream의 마지막 비어 있지 않은 줄만 읽고 `type:result`가 아니면 실패한다
(`opal/tools/opal-agent/opal_agent.py:538-558`). 실제 task 123 실행 증거에서는 성공 `result` 뒤에
`background_tasks_changed`, `task_updated`, `task_notification`이 기록됐고 opal-agent가 exit 2를
반환했다.

반대로 stream 어디에든 `result`가 있으면 성공으로 처리해서도 안 된다. result 뒤에 미종료 작업이나
알 수 없는 이벤트가 있을 수 있기 때문이다.

### 3.3 상한이 문서에만 존재

동일 컨텍스트 재개 1회와 검증 재시도 상한은 Guards에 정의되어 있지만 실행 시도 수를 기록하고 다음
dispatch를 거부하는 도구가 없다. Loop 1·Loop 2의 회전 수, task attempt, 비용, 벽시계 시간도 같은
문제를 가진다.

### 3.4 상태·실패 전이 불일치

- `opal-action-monitor`는 `pending/running/done/failed/error/blocked`를 표시한다.
- 기존 제안 상태는 `completed`를 사용하고 `error/blocked`를 빠뜨렸다.
- T4b는 검사 단계만 있고 실패 원인별 T2·T3 복귀와 총 attempt 상한이 정의되지 않았다.
- monitor와 opal-agent가 서로 다른 result 탐색 규칙을 사용한다.

### 3.5 파생 뷰 시각 불일치

`backlog-tool`은 JSON의 `updated_at`을 갱신하지만 기존 `BACKLOG.md`에서는 마커 영역만 교체해
머리말의 `최종 갱신` 시각이 init 값으로 남았다(`_rerender_backlog_md`
`opal/tools/backlog-tool/backlog_tool.py:268-283`, 신규 템플릿은 `_build_new_backlog_md` `:246-257`,
머리말 라인 `:250`). 현재는 `_sync_backlog_header` `:260-265`가 재렌더 경로에서 같은 `updated_at`으로
머리말을 치환하며, 머리말 라인이 없는 기존 파일에는 삽입하지 않아 하위호환을 유지한다.

## 4. 집행 구조

문서는 정책을 설명하고 도구가 정책을 집행한다. 에이전트가 횟수·시간·비용을 기억해서 차단하는
방식은 허용하지 않는다.

| 구성요소 | 책임 | 금지 책임 |
|---|---|---|
| OPPL skill·loop-control·Guards | 상태 의미·상한 종류·에스컬레이션 정책 | 횟수 기억·프로세스 감시·dispatch 허가 판정 |
| `oppl-runtime-tool` | round·attempt·resume·예산 ledger, admission, 무진전 판정, 상태 전이 | 자연어 설계·코드 구현 |
| `opal-agent` attempt wrapper | process group 시작·heartbeat·phase timeout·출력 경로·stream framing·종료 수확 | 프로젝트 우선순위·다음 태스크 선택 |
| `opal-loop-action-agent` | T1~T5+G 작업 조율, 도구 결정 소비 | 자체 카운터로 상한 우회·직접 성공 판정 |
| `opal-action-monitor` | runtime ledger와 실행 증거의 읽기 전용 표시 | 상태·예산·attempt 변경, 신규 dispatch 차단 |
| `backlog-tool` | 업무 백로그와 `BACKLOG.md` 파생 뷰 | 프로세스 수명주기·attempt ledger |

### 4.1 운영 ledger

`oppl-runtime-tool`은 태스크 폴더의 `.oppl-run/runtime.json`을 현재 실행 상태의 운영 SSOT로 관리한다.
모든 갱신은 lock 안에서 revision 확인 후 temp write·fsync·atomic replace로 수행한다.

ledger 최상위 필드는 `schema_version`, `run_id`, `revision`, `status`, `started_at`, `deadline_at`,
`design_round`, `project_dispatch_count`, `cost_used`, `wall_time_used`, `budget_snapshot`, `counters`
12종이다. phase 레코드는 `counters.<task_id>.phases.<phase>` 경로에 있고 `attempt_count`,
`resume_count`, `active_attempt_id`, `status`, `record_path`, `last_failure_fingerprint`,
`identical_failure_count` 7종을 갖는다.

attempt 1건의 PID·PGID·시작 fingerprint·heartbeat·terminal result·exit code 원문은 ledger가 아니라
`opal-agent`가 `<run-dir>/<phase>[.aN].attempt.json`에 원자 기록한다. ledger는 `attempt_id`와 그
파일 경로(`active_attempt_id`, `record_path`)만 외래 참조로 갖고 원문을 중복 저장하지 않는다. OPPD
Controller도 같은 attempt record를 소비하므로 원문 owner는 공용 쪽에 둔다
(`docs/proposals/opal-oppd-v3-lean-project-execution.md:344-345`).

`cost_used`는 terminal candidate의 `total_cost_usd` 값을 그대로 쓰고 stream 안 result마다 합산하지
않는다. 같은 stream의 복수 result가 싣는 비용은 누적값이라 합산하면 이중 계상된다.

`run_id`는 `state-tool`이 발급해 `state.json`의 현재 run으로 저장한다. `oppl-runtime-tool`은 이 값을
외래 참조로 복제할 뿐 새 ID를 발급하거나 현재 run을 바꾸지 않는다. `state.json`에 현재 run이 없으면
runtime 초기화를 거부하며, run-log 활성화 전이라면 state-tool의 run identity 계약을 먼저 구현한다.

이 ledger는 `backlog.json`, `state.json`, `test-scenario.json`의 업무·파이프라인·검증 상태를 복제하지
않는다. 삭제 가능한 로그가 아니라 다음 실행의 admission을 결정하는 운영 SSOT다.

## 5. 상태기계

기존 monitor 호환을 위해 상태는 다음 7개로 고정한다.

| 상태 | 의미 | 허용 전이 |
|---|---|---|
| `pending` | 실행 등록 전 또는 자원 대기 | `running`, `blocked`, `error` |
| `running` | 루트 프로세스나 등록 자식 실행 중 | `done`, `failed`, `error`, `blocked`, `timed_out` |
| `done` | 완료조건과 결과 계약 모두 성공 | 종료 |
| `failed` | 실행 또는 검증이 정상적으로 실패 | 새 attempt, `blocked` |
| `error` | 실행기·schema·알 수 없는 terminal framing 오류 | 새 attempt, `blocked` |
| `blocked` | 계약·승인·예산·무진전으로 자동 진행 불가 | 사용자 또는 PM 결정 뒤 새 attempt |
| `timed_out` | watchdog이 process group을 종료 | 새 attempt, `blocked` |

`running`은 실패가 아니다. active attempt가 있으면 같은 task·phase의 신규 dispatch를 도구가 거부한다.

## 6. 유한 실행 계약

### 6.1 설정 SSOT

상한 값은 effective setting의 `oppl.runtime`에서 읽고 프로젝트
`.opal/setting.local.json`이 전역 값을 덮는다. 다음 값은 모두 유한한 양수여야 한다.

- `max_design_rounds`
- `max_project_dispatches`
- `max_task_attempts`
- `max_identical_failures`
- `max_wall_time_sec`
- `heartbeat_timeout_sec` (stream mode 전용)
- `hard_timeout_sec_by_phase`
- `max_hard_timeout_sec`
- `terminate_grace_sec`

`heartbeat_timeout_sec`는 stream mode에만 적용한다. sync mode는 출력을 줄 단위로 관측하지 않으므로
hard timeout만 적용하고 heartbeat 부재를 `timed_out` 사유로 쓰지 않는다. hard timeout과 PGID 회수는
두 mode에 동일하게 적용한다.

동일 컨텍스트 resume 상한은 설정값이 아니라 Guards의 고정값 `1`을 사용한다. provider가 비용을
신뢰성 있게 보고할 때는 `max_cost_usd` 또는 동등 비용 단위를 추가로 설정하며 이 값도 유한한 양수여야
한다. 비용 측정이 불가능한 provider에서도 dispatch 횟수와 벽시계 상한은 필수다. 필수 설정이 없거나
0, 음수, 무한대이면 OPPL 시작과 신규 dispatch를 fail-closed로 거부한다.

`hard_timeout_sec_by_phase`는 등록된 phase마다 서로 다른 유한 상한을 가진다. attempt가 timeout을
별도로 요청하지 않으면 해당 phase 상한을 사용하고, 요청값이 phase 상한이나
`max_hard_timeout_sec`를 넘으면 admission이 `timeout_limit_exceeded`로 거부한다. 에이전트가 실패 후
명령행 숫자만 높여 상한을 우회하는 경로는 없다.

현재 Python 도구 계층에는 이 병합 계약을 제공하는 공용 로더가 없다. `oppl-runtime-tool`은 전역
`~/.opal/setting.json`과 프로젝트 `.opal/setting.local.json`에서 `oppl.runtime`만 읽어 키 단위로
병합하는 read-only loader를 소유한다. 파일 파싱 실패·타입 오류·필수 phase 누락은 조용히 기본값으로
내리지 않고 설정 오류로 거부한다.

### 6.2 admission

Loop 1 회전, Loop 2 task 선택, 태스크 내부 phase 시작과 resume 직전에 반드시
`oppl-runtime-tool admit`을 호출한다. 도구는 같은 lock 안에서 다음을 검사하고 허가된 경우에만 카운터를
증가시킨다.

호출 주체는 범위별로 갈린다. PM은 `state-tool run-start` → `oppl-runtime-tool init --run-id`로 run을
초기화하고 Loop 1 회전과 Loop 2 task 선택 경계에서 `admit`을 호출한다. 태스크 내부 phase 시작과
resume 경계에서는 `opal-loop-action-agent`가 `admit` → `attempt-start` → 실행 → `attempt-finish`를
직접 호출한다. phase 전환 시점과 상한 판정 시점을 분리할 수 없고, PM만 호출하게 하면 phase마다 왕복이
생겨 태스크당 PM 개입 1회 구조가 무너지기 때문이다.

이 허용은 업무 SSOT 경계를 넓히지 않는다. `runtime.json`은 `backlog.json`·`state.json`·
`test-scenario.json` 3축과 별개의 런타임 가드 축이며, `opal-loop-action-agent`의 `backlog-tool`·
`state-tool`·`oppl-runtime-tool init` 호출 금지는 그대로다.

1. 같은 범위에 active attempt가 없는가
2. 설계 회전·프로젝트 dispatch·task attempt 상한이 남아 있는가
3. 동일 컨텍스트 resume 상한이 남아 있는가
4. 비용·벽시계 시간이 남아 있는가
5. 동일 실패 지문 반복이 무진전 기준 미만인가
6. 사용자 결정이나 비가역 행동 대기 상태가 아닌가

거부 응답은 단일 JSON과 비영(非零) exit code로 `active_attempt`, `round_limit_exceeded`,
`attempt_limit_exceeded`, `resume_limit_exceeded`, `budget_exceeded`, `timeout_limit_exceeded`,
`no_progress`, `decision_required` 중 하나를 반환한다. 이 8종은 폐쇄 집합이고
`max_project_dispatches` 전용 코드는 없다. 모든 거부 응답은 어느 범위에서 걸렸는지를 나타내는
`scope` 필드를 동반하며, dispatch 상한 초과는 `attempt_limit_exceeded` + `scope: "dispatch"`로
구분한다. `timeout_limit_exceeded`는 집합에 있으나 `oppl-runtime-tool`이 아니라 attempt wrapper가
요청 timeout을 phase 상한·`max_hard_timeout_sec`와 대조해 반환한다. 에이전트는 이를 재해석해
우회하지 않는다.

동일 컨텍스트 resume은 Guards 계약대로 최대 1회다. 그 뒤에는 남은 예산 안에서 압축 실행 입력을 받은
새 attempt만 허용한다. 새 attempt도 전체 task·project 상한을 우회하지 못한다.

### 6.3 실패 지문

무진전 판정용 실패 지문은 다음 정규화 payload의 SHA-256이다.

```text
{task_id, phase, verifier_id, command_id, exit_class,
 sorted(failing_scenario_ids), normalized_error_code, contract_revision}
```

자유 텍스트, timestamp, 임시 경로, PID, 토큰 수는 지문에서 제외한다. 같은 지문이
`max_identical_failures`에 도달하면 추가 dispatch를 거부하고 `blocked/no_progress`로 전이한다.

`exit_class`는 provider adapter가 terminal candidate의 `terminal_reason`과 `api_error_status`를 읽어
`ok`, `impl_failure`, `api_error`, `timed_out`, `output_format_invalid`, `framing_error` 중 하나로
분류한 값이다. 지문 payload의 1급 필드이므로 provider API 오류 반복은 구현 실패(`impl_failure`)
지문과 섞이지 않는다.

`api_error`로 끝난 attempt는 무진전 카운터를 증가시키지도 초기화하지도 않는다. provider rate limit
재시도는 시간 경과만으로 해소될 수 있어 "같은 시도가 목표에 가까워지지 않음"과 성격이 다르기
때문이다. 따라서 provider 장애는 `no_progress`가 아니라 attempt·dispatch·비용·벽시계 상한으로만
제한된다.

### 6.4 T4b 실패 전이

- 제품 코드·설정·방어 구현 결함: T3 새 attempt
- 테스트 시나리오·검증 계약 결함: 계약 변경 승인을 받은 뒤 T2 새 attempt
- 보안·컨벤션 정책 자체의 충돌 또는 귀속 불가: 즉시 `blocked`
- 어느 분기든 task attempt와 project dispatch 상한을 함께 차감

## 7. 프로세스·완료 판정

### 7.1 watchdog과 자식 회수

attempt wrapper는 루트 프로세스를 별도 process group으로 시작하고 PID·PGID·시작 fingerprint를
attempt record에 기록한다(ledger가 아니다 — §4.1). watchdog은 stdout read loop와 독립된 monotonic
timer로 동작한다.

heartbeat timeout은 stream mode에만 적용한다. sync mode는 hard timeout만 적용하며 heartbeat 부재를
`timed_out` 사유로 쓰지 않는다.

hard timeout 또는 heartbeat timeout이면 process group 전체에 TERM을 보내고 `terminate_grace_sec` 뒤
남은 프로세스에 KILL을 보낸다. PGID 소멸을 확인하기 전에는 `timed_out` terminal 기록과 다음 attempt
허가를 완료하지 않는다.

### 7.2 stream terminal framing

provider adapter가 전체 stream을 분류한다.

1. stream의 마지막 유효한 result를 현재 attempt의 terminal candidate로 선택한다.
2. 그 앞 result는 같은 `session_id`이고 `result_index`가 단조 증가할 때만 선행 turn으로 인정하며
   현재 결과로 소비하지 않는다. 둘 중 하나라도 깨진 복수 result는 `error`다. 선행 result는 이전
   결과의 재생이 아니라 백그라운드 작업 알림 등이 유발한 별도 turn이다 — 태스크 123 실측에서 선행
   result는 `origin.kind = task-notification`·`num_turns 0`·`total_cost_usd 0`이었고, 본 작업 result
   뒤에 같은 origin으로 15 turn짜리 후속 작업이 이어진 사례도 있다.
3. terminal candidate 뒤에는 adapter가 명시한 terminal epilogue allowlist만 허용한다. allowlist는
   `type`이 아니라 `subtype` 기준이다 — 실측 형태는
   `{"type":"system","subtype":"background_tasks_changed"|"task_updated"|"task_notification"}`이며,
   판정은 `type == "system"`이고 `subtype`이 allowlist에 있을 때만 통과한다.
4. epilogue를 순서대로 reduce한 **stream 종료 시점**에 등록된 모든 자식 작업이 terminal이어야 한다.
   중간 이벤트에 실행 중 task가 있어도 뒤 사건에서 `killed/completed/stopped` 또는 빈 task 집합으로
   닫히면 허용한다.
5. 알 수 없는 이벤트, epilogue 안의 신규 작업 시작, 종료 시점의 미종료 자식은 성공으로 판정하지
   않는다.
6. 루트 프로세스 exit 0, PGID 소멸, 최종 자식 terminal, 마지막 result schema 성공이 모두 성립해야
   `done`이다.

`origin`은 어떤 판정 분기에도 쓰지 않는다. attempt record에 진단 정보로만 싣고 `origin` 부재는
오류로 다루지 않는다.

따라서 마지막 줄만 보는 규칙과 “어디든 result가 있으면 성공” 규칙을 모두 폐기한다.
`opal-agent`와 monitor는 동일 adapter의 terminal 판정 결과만 소비한다.

### 7.3 출력 경로와 직렬화

호출 에이전트는 shell redirect로 결과 파일 이름과 형식을 결정하지 않는다. `opal-agent`가
`--run-dir <dir> --phase <name> [--attempt aN]`을 받으면 attempt 산출물의 단일 writer가 되어 호출
mode에 따라 경로를 만들고 닫는다. 세 인자가 모두 없으면 기존 stdout passthrough 동작이 그대로다.

- stream mode: `<phase>[.aN].events.jsonl` — UTF-8 compact JSON 객체 1행 1건
- sync mode: `<phase>[.aN].result.json` — UTF-8 단일 JSON 객체
- 공통: `<phase>[.aN].err.log`, `<phase>[.aN].exitcode`, `<phase>[.aN].attempt.json`

stream 파일은 줄 단위 append 후 flush로 쓴다 — 실행 중 증분 관측을 유지해야 monitor가 진행 상황을
읽을 수 있기 때문이다. sync `result.json`, `.exitcode`, `.err.log`는 temp write·fsync·atomic
rename으로 확정한다. 확장자와 실제 직렬화가 다르거나 JSONL 한 사건이 여러 물리 행에 걸치면
`output_format_invalid`로 처리하며 `done`을 기록하지 않는다.

watchdog 조절은 `--heartbeat-timeout-sec`(stream mode 전용), `--terminate-grace-sec`(기본 5초 —
기본값이 있는 것은 유예 시간뿐이다), `--max-timeout-sec`, `--phase-timeout-limit-sec` 네 인자로
받는다. `--phase-timeout-limit-sec`는 호출자가 계산해 넘기는 값이고 `opal-agent`는 phase별 상한 표를
갖지 않는다 — phase 의미론과 상한 표는 공용 owner인 `oppl-runtime-tool` 설정 계약에 있다. `--timeout`이
전달된 상한을 넘으면 프로세스를 만들지 않고 거부한다. 네 인자를 모두 생략하면 기존 동작이 그대로다.

## 8. 파생 뷰와 검증 경계

- monitor는 7상태와 ledger의 남은 상한을 표시하되 어떤 파일도 수정하지 않는다.
- `BACKLOG.md` 재렌더는 표뿐 아니라 머리말 `최종 갱신`을 `backlog.json.updated_at`과 함께 갱신한다.
- 변경 중에는 formatter·lint·직접 관련 테스트만 실행한다.
- task 완료 후보에서는 수용·영향·규칙 검사를 실행한다.
- 프로젝트 완료 후보에서는 전체 회귀·통합 보안·신규 컨벤션 위반을 검사한다.
- 검증 캐시는 도입하지 않는다. 실행 횟수 감소는 경계 분리로만 달성한다.
- 잠긴 test-scenario spec은 이 제안으로 수정하지 않는다.
- 실행 일지 집계와 `AGENTIC-LOG.md` 폐지는 run-log 설계가 소유한다.

## 9. 기계 판정 수용기준

| ID | 검증 시나리오 | 통과 증거 |
|---|---|---|
| AC-01 | phase 상한이 서로 다른 무출력 process 둘과 상한 초과 요청 실행 | 각 phase deadline에 PGID 소멸·`timed_out`; 초과 요청은 process 0·`timeout_limit_exceeded` |
| AC-02 | terminal candidate 앞에 같은 `session_id`·단조 증가 `result_index`의 선행 turn result가 있고, 뒤에 허용된 자식 종료 epilogue가 붙은 stream | 마지막 result만 소비, 종료 시점 자식 0, exit 0·`done` |
| AC-03 | result 뒤 알 수 없는 이벤트 또는 epilogue 종료 시점까지 실행 중 자식 유지 | `done` 거부, `running` 또는 `error` |
| AC-04 | 같은 context를 두 번 resume | 첫 resume만 허가, 두 번째 `resume_limit_exceeded` |
| AC-05 | 필수 상한 누락·0·음수·무한대 설정 | OPPL 시작 전 설정 오류로 거부 |
| AC-06 | 각 round·dispatch·attempt·벽시계·비용 상한 도달 | 이후 신규 실행 0, 대응 구조화 오류와 `blocked` |
| AC-07 | 같은 정규화 실패를 설정 횟수만큼 반복 | 다음 admission `no_progress`, 신규 process 0 |
| AC-08 | T4b에 구현·테스트계약·정책충돌 fixture 각각 주입 | 각각 T3·승인 후 T2·blocked로만 전이 |
| AC-09 | monitor 실행 전후 `.oppl-run` hash 비교 | 변경 0, 상태 enum 7종 외 출력 0 |
| AC-10 | backlog add·mark·update 실행 | `BACKLOG.md` 최종 갱신과 JSON `updated_at` 일치 |
| AC-11 | active attempt 중 같은 task·phase 재호출 | `active_attempt`, 중복 process 0 |
| AC-12 | runtime tool을 우회해 직접 phase 결과를 완료 처리 | state 전이 거부, tool receipt 없는 `done` 0 |
| AC-13 | sync·stream wrapper를 각각 실행하고 산출물 직렬화 검사 | sync 단일 JSON·stream 1행 1객체, 경로/형식 불일치 0 |

수용기준은 실제 subprocess·process group·파일 lock 기반 통합 테스트로 검증한다. mock만으로 P0 완료를
선언하지 않는다.

## 10. 구현 순서

1. task 123의 복수 result turn·result 후속 이벤트·잘못된 JSONL 사례를 비식별 회귀 fixture로 고정
2. state-tool run identity 계약과 `oppl.runtime` effective-setting loader 구현
3. `opal-agent` process group·독립 watchdog·phase timeout·terminal adapter·출력 writer 구현
4. `oppl-runtime-tool` ledger·lock·admission·실패 지문 구현
5. OPPL Loop 1·Loop 2·loop-action-agent의 모든 실행 진입을 admission에 연결
6. T4b 전이와 monitor 7상태 호환 구현
7. `BACKLOG.md` 머리말 갱신 수정
8. AC-01~AC-13 실제 통합 검증
9. 설치 스크립트와 배포본 반영

1~5가 구현되고 AC-01~AC-08·AC-11~AC-13이 통과하기 전에는 OPPL을 장시간 무인 자율 실행에 사용하지
않는다. 문서 규칙만 추가된 상태를 안정화 완료로 판정하지 않는다.
