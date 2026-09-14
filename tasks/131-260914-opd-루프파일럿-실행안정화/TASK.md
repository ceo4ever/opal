---
template: sdlc-v2
---
# TASK: OPPL 실행 안정화 — 상한·완료판정 도구 집행

## Problem

OPPL의 장시간 실행·반복 상한·완료 판정이 문서 규칙으로만 존재하고 이를 집행하는 도구가 없다. 그 결과 실제 실행에서 다음 손상이 관측됐다.

- `opal-agent` stream 경로의 deadline 검사가 stdout 줄 도착 시에만 동작해(`opal/tools/opal-agent/opal_agent.py:694-721`), 무출력 프로세스가 제한 시간을 넘겨도 종료되지 않는다. 동기 경로의 timeout도 직접 자식만 대상으로 하며 process group 회수 계약이 없다.
- 파서가 stream의 마지막 비어 있지 않은 줄만 읽고 `type:result`가 아니면 실패한다(`opal/tools/opal-agent/opal_agent.py:538-558`). 태스크 123 실행 증거에서 성공 `result` 뒤에 `background_tasks_changed`·`task_updated`·`task_notification`이 기록돼 정상 완료 작업이 exit 2로 판정됐다(`.opal-worktrees/task_123/.../T01-채널-관측-능력-실측/.oppl-run/t1.events.jsonl`, `T03-기록코어-스키마-멱등-순번/.oppl-run/t3.events.jsonl`, `t3.a3.events.jsonl`).
- 동일 컨텍스트 재개 1회 상한(`opal/core/references/harness/guards.md` §자동 루핑 제약)과 Loop 1·Loop 2 회전 수, task attempt, 비용, 벽시계 상한을 기록하고 다음 dispatch를 거부하는 도구가 없다.
- `opal-action-monitor`는 `pending/running/done/failed/error/blocked` 6상태를 쓰는데 상태기계 정의가 이와 어긋나고, monitor와 `opal-agent`가 서로 다른 result 탐색 규칙을 쓴다.
- T4b 규칙검사는 실패 원인별 복귀 지점과 총 attempt 상한이 정의되지 않았다.
- `backlog-tool`이 `BACKLOG.md` 마커 영역만 교체해 머리말 `최종 갱신` 시각이 init 값으로 남는다(`opal/tools/backlog-tool/backlog_tool.py:252-267`).

집행 주체가 없는 상태에서 OPPL을 장시간 무인 실행하면 정상 작업이 실패로, 미완료 작업이 완료로 기록되고 상한을 넘긴 반복이 예산을 소진한다.

## Proposed outcome

OPPL 실행의 상한·완료 판정·프로세스 수명주기를 도구가 집행한다. 완료 후 다음을 관찰할 수 있다.

- 무출력 워커가 phase별 제한 시간 안에 process group째 종료되고 `timed_out`으로 기록된다.
- 성공 result 뒤에 자식 종료 알림이 출력돼도 정상 완료로 판정되고, result 뒤에 미종료 자식이나 알 수 없는 이벤트가 있으면 완료로 판정되지 않는다.
- 회전·dispatch·attempt·재개·비용·벽시계·동일 실패 반복이 각각 상한에 도달하면 신규 실행이 도구 수준에서 거부된다.
- `opal-action-monitor`가 7상태와 남은 상한을 읽기 전용으로 표시한다.
- `BACKLOG.md` 머리말 갱신 시각이 `backlog.json.updated_at`과 일치한다.
- 위 동작이 설치본(`~/.opal/`)에 배포되어 실제 OPPL 실행에서 사용된다.

## Affected users and systems

- OPPL(`opal-pilot-project-loop`)로 프로젝트를 실행하는 소유자와 PM.
- 변경 대상: `opal/tools/opal-agent/`, 신규 `opal/tools/oppl-runtime-tool/`, `opal/tools/state-tool/`, `opal/tools/opal-action-monitor/`, `opal/tools/backlog-tool/`, `opal/skills/opal-pilot-project-loop/`, `opal/agents/opal-loop-action-agent/`, `opal/core/references/harness/`, `scripts/`, `docs/proposals/opal-oppl-runtime-stabilization.md`, `docs/PROJECT.md`.
- 소비 영향: `opal-agent`를 공용 실행 원시 기능으로 쓰는 다른 호출자(OPPD v3 제안서 §공용 attempt runtime).
- 제외: 다른 Pilot로의 기능 이관·OPPL 폐기, 신규 프로젝트 스케줄러·범용 Controller, 검증 결과 캐시, 잠긴 test-scenario spec 기준선의 사후 갱신, `AGENTIC-LOG.md`·run-log 집계 설계, OPPL과 무관한 전역 실행 이력 표준화.

## Constraints

- C-1: 입력 명세는 `docs/proposals/opal-oppl-runtime-stabilization.md`다. 제안서 §2.2 비범위 항목을 구현하지 않는다.
- C-2: 상한·횟수·비용 판정을 에이전트 기억이나 산문 판단으로 수행하지 않는다. 도구 호출 결과(단일 JSON + exit code)만 근거로 삼는다.
- C-3: `opal-action-monitor`는 읽기 전용을 유지한다. 어떤 파일도 수정하지 않으며 상태·예산·attempt를 바꾸지 않는다.
- C-4: 3-SSOT 축 분리를 유지한다. `runtime.json`은 `backlog.json`·`state.json`·`test-scenario.json`의 업무·파이프라인·검증 상태를 복제하지 않는다.
- C-5: `run_id`는 `state-tool`이 발급하고 `state.json`이 현재 run을 소유한다. `oppl-runtime-tool`은 외래 참조로만 복제하며 새 ID를 발급하지 않는다.
- C-6: `~/.opal/` 배포본을 직접 편집하지 않는다. 프로젝트 소스를 수정한 뒤 install로 재배포한다.
- C-7: `--dangerously-skip-permissions`를 어떤 축의 명령에도 추가하지 않는다. 자동 실행 제어는 `--allowed-tools` allowlist로만 수행한다.
- C-8: 기존 `--json`·`--text` 호출 경로의 관측 가능한 동작을 바꾸지 않는다. 비-OPPL 호출자가 회귀를 겪지 않아야 한다.
- C-9: terminal candidate 판정은 마지막 유효 result를 기준으로 하며, 그 앞의 result는 같은 `session_id`와 단조 증가 `result_index`로만 선행 turn임을 인정한다. "이전 결과 재생(replay)"을 전제로 서술하거나 판정하지 않는다. 근거: 태스크 123 실측에서 선행 result는 `origin.kind = task-notification`·`num_turns 0`·`total_cost_usd 0`이고, 본 작업 result 뒤에 같은 origin으로 15 turn짜리 후속 작업이 이어진 사례가 있다(`T03-기록코어-스키마-멱등-순번/.oppl-run/t3.events.jsonl`).
- C-10: 같은 stream 안 복수 result의 `total_cost_usd`는 누적값이다. ledger `cost_used`는 terminal candidate의 값을 그대로 쓰고 result마다 합산하지 않는다.
- C-11: `heartbeat_timeout_sec`의 적용 범위를 호출 mode별로 명시한다. 출력 이벤트가 없는 sync mode에 stdout 기반 heartbeat를 적용하지 않는다.
- C-12: API 오류 종료를 구현 결함과 같은 실패 class로 집계하지 않는다. adapter가 `terminal_reason`·`api_error_status`를 읽어 별도 `exit_class`로 분류한다. 근거: 태스크 123 `T02-워킹-스켈레톤-CLI-관통/.oppl-run/t3.a2.events.jsonl`은 `is_error true`·`terminal_reason api_error`·HTTP 429로 종료됐다.
- C-13: 커밋은 소유자가 명시 요청할 때만 수행한다.

## Acceptance criteria

- AC-1: phase 상한이 서로 다른 무출력 프로세스 둘을 실행하면 각 phase deadline에 PGID 전체가 소멸하고 `timed_out`으로 기록되며, phase 상한이나 `max_hard_timeout_sec`를 넘는 timeout 요청은 프로세스를 만들지 않고 `timeout_limit_exceeded`로 거부된다.
- AC-2: 선행 turn result가 앞에 있고 terminal candidate 뒤에 허용된 자식 종료 epilogue가 출력된 stream에서, 마지막 result만 소비하고 종료 시점 미종료 자식 0으로 exit 0·`done`이 된다.
- AC-3: terminal candidate 뒤에 알 수 없는 이벤트가 있거나 epilogue 종료 시점까지 실행 중 자식이 남은 stream은 `done`으로 판정되지 않고 `running` 또는 `error`가 된다.
- AC-4: 같은 컨텍스트를 두 번 resume하면 첫 번째만 허가되고 두 번째는 `resume_limit_exceeded`로 거부된다.
- AC-5: 필수 상한이 누락·0·음수·무한대인 설정에서 OPPL 시작과 신규 dispatch가 거부된다.
- AC-6: 회전·dispatch·attempt·벽시계·비용 상한이 각각 도달한 뒤 신규 실행이 0건이고 대응 구조화 오류와 `blocked` 전이가 관찰된다.
- AC-7: 동일 정규화 실패 지문이 `max_identical_failures`에 도달하면 다음 admission이 `no_progress`를 반환하고 신규 프로세스가 0건이다.
- AC-8: T4b에 구현 결함·테스트계약 결함·정책충돌 fixture를 각각 주입하면 각각 T3 새 attempt, 승인 후 T2 새 attempt, 즉시 `blocked`로만 전이한다.
- AC-9: `opal-action-monitor` 실행 전후 `.oppl-run` 파일 hash가 동일하고, 출력 상태값이 7종 enum을 벗어나지 않는다.
- AC-10: `backlog-tool`의 add-task·mark·update-task 실행 후 `BACKLOG.md` 머리말 `최종 갱신`과 `backlog.json.updated_at`이 일치한다.
- AC-11: 같은 task·phase에 active attempt가 있는 상태에서 재호출하면 `active_attempt`로 거부되고 중복 프로세스가 0건이다.
- AC-12: `oppl-runtime-tool`을 우회해 phase 결과를 직접 완료 처리하려 하면 상태 전이가 거부되고, tool receipt 없는 `done` 기록이 0건이다.
- AC-13: sync·stream wrapper를 각각 실행하면 sync 산출물은 단일 JSON, stream 산출물은 1행 1객체 JSONL이며 확장자와 실제 직렬화가 불일치한 산출물이 0건이다.
- AC-14: API 오류로 종료된 실행이 구현 결함과 다른 `exit_class`로 분류되어, 같은 API 오류가 `max_identical_failures`만큼 반복돼도 구현 결함 지문으로 `no_progress` 판정되지 않는다.
- AC-15: 같은 stream에 복수 result가 있을 때 ledger `cost_used`가 terminal candidate의 `total_cost_usd`와 같고 합산값이 아니다.
- AC-16: `heartbeat_timeout_sec` 적용 범위가 호출 mode별로 문서와 구현에서 일치하며, sync mode 실행이 heartbeat 부재만을 이유로 `timed_out`이 되지 않는다.
- AC-17: `--json`·`--text` 기존 호출 경로의 회귀 테스트가 전건 통과한다.
- AC-18: `docs/proposals/opal-oppl-runtime-stabilization.md`가 구현 결과와 일치하도록 갱신되고, C-9~C-12가 반영되며, 잘못된 인용 행번호(`backlog_tool.py:251-265`)가 실제 위치로 정정된다.
- AC-19: 변경된 도구·스킬·에이전트가 install 경로로 `~/.opal/`에 배포되고, 배포본에서 `oppl-runtime-tool`과 `opal-agent` attempt wrapper가 실제로 호출된다.
- AC-20: 수용기준 검증이 실제 subprocess·process group·파일 lock 기반 통합 테스트로 수행되고, mock만으로 통과 선언한 항목이 0건이다.
