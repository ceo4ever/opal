# oppl-runtime-tool

> oppl 2-루프 실행의 유한 실행 계약(설정·ledger·lock·admission) 집행 CLI
> 소스: `opal/tools/oppl-runtime-tool/` | 배포: `~/.opal/tools/oppl-runtime-tool/`
> 설계 근거: `tasks/131-260914-opd-루프파일럿-실행안정화/PLAN.md` D2·D3·D4·D6·D8·D9 / W-3·W-6

## 개요

`oppl-runtime-tool`은 태스크 폴더의 `.oppl-run/runtime.json`을 운영 ledger로 소유하고, 설계 회전·프로젝트 dispatch·task attempt·resume·예산·무진전 상한을 도구 경계에서 집행한다. 에이전트가 자체 카운터로 상한을 우회하거나 receipt 없이 `done`을 기록하는 경로를 만들지 않는다.

- **축 분리(D3)**: `runtime.json`은 3-SSOT(`backlog.json`·`state.json`·`test-scenario.json`)와 별개인 **런타임 가드 축**이다. 업무·파이프라인·검증 상태를 복제하지 않는다.
- **소유권 분리(D4)**: ledger는 **집계값만** 보유한다. attempt별 PID·PGID·시작 fingerprint·heartbeat·terminal result 원문은 저장하지 않고 `attempt_id`와 attempt record **파일 경로만 외래 참조**로 갖는다.
- **run identity(D8)**: `run_id`는 `state-tool`이 발급한다. 이 도구는 발급하지 않고 외래 참조로만 복제한다.
- **출력 계약**: 모든 응답은 **단일 라인 JSON + exit code**(`opal/core/references/harness/tool-output-contract.md`).

## 호출 형식

```bash
~/.opal/tools/oppl-runtime-tool/run.sh <command> --task-path <task-path> [options]
```

> 개발 중에는 소스 경로로 직접 호출:
> `bash opal/tools/oppl-runtime-tool/run.sh <command> --task-path <task-path> [options]`

`--task-path`는 서브커맨드 앞·뒤 어느 위치에 와도 같게 해석된다.

## 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | 성공 |
| `1` | 인자 오류 / ledger 미초기화 / run identity 결손 / 상태 전이 거부 |
| `2` | `config_invalid` (설정 로드·검증 실패) |
| `3` | admission 거부 (거부 코드 8종) |

## 서브 명령 오너십 (D2)

| 명령 | 호출 주체 |
|------|-----------|
| `init` | PM 전용 |
| `admit` · `attempt-start` · `attempt-finish` | PM + `opal-loop-action-agent` |
| `config` · `show` | 읽기 전용 — 제한 없음 |

도구는 호출자를 구분하지 않는다. 이 경계는 `opal-pilot-project-loop/SKILL.md`와 `opal-loop-action-agent/AGENT.md`가 집행한다(W-7).

## 설정 SSOT (D6)

| 층 | 경로 |
|----|------|
| 전역 (base) | `$OPAL_HOME/setting.json` — 미설정 시 `~/.opal/setting.json` |
| 로컬 (override) | `<project-root>/.opal/setting.local.json` |

project root는 `--task-path`에서 위로 올라가며 `.opal/`을 가진 첫 조상이다. 두 파일의 `oppl.runtime` 블록을 **1단계 키 오버라이드**로 병합한다 — 로컬에 있는 최상위 키는 **통째로 교체**되며 **딥 머지를 하지 않는다**. `hard_timeout_sec_by_phase`도 dict 통째 교체이므로 phase 단위 부분 덮어쓰기는 불가능하다(부분 map은 등록 phase 결손으로 거부된다).

**필수 키 9종** — 모두 유한 양수:
`max_design_rounds`, `max_project_dispatches`, `max_task_attempts`, `max_identical_failures`, `max_wall_time_sec`, `heartbeat_timeout_sec`, `hard_timeout_sec_by_phase`, `max_hard_timeout_sec`, `terminate_grace_sec`

**선택 키**: `max_cost_usd` — 존재하면 유한 양수여야 한다.

**등록 phase 집합**: `t1`, `t2`, `g`, `t3`, `t4a`, `t4b`. `hard_timeout_sec_by_phase`는 이 전부를 유한 양수로 가져야 한다.

파싱 실패·타입 오류·필수 키 누락·등록 phase 누락·`0`·음수·비유한값·두 파일 모두 부재는 **전부 단일 코드 `config_invalid` + 비영 exit**로 거부한다. 조용한 기본값 강등을 하지 않는다.

> 동일 컨텍스트 resume 상한은 **설정 키가 아니다**. 수치의 SSOT는 `opal/core/references/harness/guards.md` §자동 루핑 제약이며, 도구는 그 고정값을 내부 상수로만 쓰고 `config` 출력에 노출하지 않는다.

## 서브 명령

### `config` — effective 설정 조회

```bash
run.sh config --task-path <t>
```

```json
{"ok":true,"command":"config","config":{"max_design_rounds":5,"...":"..."}}
```

### `init` — ledger 생성 (PM 전용)

```bash
run.sh init --task-path <t> --run-id <run-id>
```

`state.json`이 없거나 `state.json.run_id`가 없거나 `--run-id`와 불일치하면 `run_identity_missing` + 비영 exit으로 거부하고 `runtime.json`을 만들지 않는다.

### `admit` — 허가 판정 (제안서 §6.2)

```bash
run.sh admit --task-path <t> --scope round|dispatch|task-phase|resume \
  [--task-id <id> --phase <p>]
```

`--task-id`/`--phase`는 `task-phase`·`resume` scope에서 필수다. 같은 lock 안에서 6개 검사를 수행하고 **허가된 경우에만** 카운터를 증가시키며 active attempt를 예약한다.

1. 같은 범위에 active attempt가 없는가 → `active_attempt`
2. 설계 회전·프로젝트 dispatch·task attempt 상한 → `round_limit_exceeded` / `attempt_limit_exceeded`
3. 동일 컨텍스트 resume 상한 → `resume_limit_exceeded` (응답에 `limit` 동반)
4. 비용·벽시계 예산 → `budget_exceeded`
5. 동일 실패 지문 반복 → `no_progress`
6. 사용자 결정 대기 상태 → `decision_required`

거부 코드 8종은 **폐쇄 집합**이다: `active_attempt`, `round_limit_exceeded`, `attempt_limit_exceeded`, `resume_limit_exceeded`, `budget_exceeded`, `timeout_limit_exceeded`, `no_progress`, `decision_required`. 에이전트는 이를 재해석해 우회하지 않고 그대로 `blocked` 반환 사유로 쓴다.

> `max_project_dispatches` 전용 코드는 폐쇄 집합에 없다. dispatch 상한 초과는 `attempt_limit_exceeded`를 쓰되, 모든 거부 응답에 **`scope` 필드가 필수로 동반**되어 task attempt 상한과 구분된다.
>
> `timeout_limit_exceeded`는 attempt wrapper(`opal-agent`, W-5)가 요청 timeout을 phase 상한·`max_hard_timeout_sec`와 대조해 판정하는 코드이며 이 도구가 반환하지 않는다.

상한·무진전 도달 거부는 ledger `status`를 `blocked`로 전이시킨다. `active_attempt`와 `decision_required`는 ledger를 쓰지 않는다.

### `attempt-start` — 예약 토큰 바인딩

```bash
run.sh attempt-start --task-path <t> --task-id <id> --phase <p> \
  --attempt-id <aid> --record-path <path>
```

`admit`이 예약한 토큰을 실제 `attempt_id`와 attempt record 경로로 바인딩하고 phase 상태를 `running`으로 둔다. 선행 `admit`이 없으면 `no_admission`으로 거부한다.

### `attempt-finish` — phase 상태를 확정하는 유일한 receipt 경로

```bash
run.sh attempt-finish --task-path <t> --task-id <id> --phase <p> --attempt-id <aid> \
  --status pending|running|done|failed|error|blocked|timed_out \
  [--cost-usd <float>] [--exit-class <c>] [--verifier-id <v>] [--command-id <c>] \
  [--failing-scenarios '<json array>'] [--error-code <c>] [--contract-revision <r>] \
  [--t4b-branch impl_defect|contract_defect|policy_conflict]
```

- `--attempt-id`가 현재 바인딩된 active attempt가 아니면 `attempt_not_bound`로 거부한다. **`attempt-start` 없이 `done`을 기록할 경로가 존재하지 않는다**(AC-12).
- `--cost-usd`는 adapter가 고른 **terminal candidate의 `total_cost_usd` 값 하나**다. 도구는 이 값을 run 누적에 1회 더할 뿐 stream 안의 result 개수로 배수하거나 재합산하지 않는다(C-10).
- `--t4b-branch`가 주어지면 **3분기 어느 경로든** task attempt(admit 시점 차감)와 project dispatch가 **함께** 1씩 증가한다(제안서 §6.4).

### `show` — ledger 조회 (읽기 전용)

```bash
run.sh show --task-path <t>
```

```json
{"ok":true,"command":"show","runtime":{"...":"..."}}
```

## 실패 지문 (제안서 §6.3 / D9)

무진전 판정용 지문은 다음 정규화 payload의 SHA-256이다.

```text
{task_id, phase, verifier_id, command_id, exit_class,
 sorted(failing_scenario_ids), normalized_error_code, contract_revision}
```

자유 텍스트·timestamp·임시 경로·PID·토큰 수는 제외한다. 지문이 바뀌면 연속 카운터가 1로 초기화되고, 같은 지문이 `max_identical_failures`에 도달하면 다음 `admit`이 `no_progress`로 거부하며 `blocked`로 전이한다.

`exit_class`는 지문의 **1급 필드**다. provider 장애로 분류된 `api_error` 종료는 구현 결함(`impl_failure`) 지문과 다른 지문이며, 무진전 카운터를 증가시키지 않는다 — 같은 API 오류가 반복돼도 `no_progress`를 트리거하지 않는다(TASK C-12, AC-14).

## `runtime.json` 스키마

최상위 필드는 D4가 정의한 집계값으로 닫혀 있다.

| 필드 | 타입 | 의미 |
|------|------|------|
| `schema_version` | string | ledger 스키마 버전 |
| `run_id` | string | `state.json.run_id`의 외래 참조 (도구가 발급하지 않는다) |
| `revision` | int | 갱신마다 1씩 증가 — 원자적 교체의 낙관적 확인용 |
| `status` | string | run 상태 (`running` / `blocked`) |
| `started_at` | string | ISO-8601 UTC |
| `deadline_at` | string | `started_at + max_wall_time_sec` |
| `design_round` | int | Loop 1 설계 회전 누계 |
| `project_dispatch_count` | int | 프로젝트 dispatch 누계 (T4b 전이 포함) |
| `cost_used` | number | terminal candidate 비용의 run 누계 |
| `wall_time_used` | number | 갱신 시점의 경과 초 |
| `budget_snapshot` | object | 예산·상한 축 설정 스냅샷 |
| `counters` | object | task·phase별 집계 컨테이너 |

`counters.<task_id>.phases.<phase>`:

| 필드 | 타입 | 의미 |
|------|------|------|
| `attempt_count` | int | 허가된 task attempt 누계 |
| `resume_count` | int | 허가된 resume 누계 |
| `active_attempt_id` | string \| null | 예약 토큰 또는 바인딩된 `attempt_id`. terminal 확정 시 `null` |
| `status` | string | phase 상태 7종 (제안서 §5) |
| `record_path` | string \| null | attempt record 파일 경로 **외래 참조** |
| `last_failure_fingerprint` | string \| null | 최근 실패 지문 (SHA-256 hex) |
| `identical_failure_count` | int | 같은 지문의 연속 발생 횟수 |

`budget_snapshot`은 `max_design_rounds`·`max_project_dispatches`·`max_task_attempts`·`max_identical_failures`·`max_wall_time_sec`와 (존재 시) `max_cost_usd`만 담는다. heartbeat·timeout 계열은 attempt wrapper 소유 축이므로 ledger에 복제하지 않는다.

## 동시성

모든 갱신은 `.oppl-run/runtime.lock`의 `fcntl` 배타 락 안에서 **revision 확인 → temp write → fsync → atomic replace** 순서로 수행한다(`backlog-tool`의 배타 락 선례). 같은 task·phase에 여러 프로세스가 동시에 `admit`해도 정확히 1건만 허가되고 나머지는 `active_attempt`로 거부되며, 카운터는 1회만 증가한다.

## 테스트

```bash
python3 -m pytest opal/tools/oppl-runtime-tool/tests/ -q
```

`tests/test_oppl_runtime_config.py`(S-1·S-2·S-4)와 `tests/test_oppl_runtime_admission.py`(S-11·S-15~S-19·S-26·S-34)가 공개 인터페이스(단일 라인 JSON + exit code, `runtime.json` 저장값)만으로 계약을 고정한다. mock·patch를 쓰지 않고 실제 파일·실제 프로세스로 검증한다.
