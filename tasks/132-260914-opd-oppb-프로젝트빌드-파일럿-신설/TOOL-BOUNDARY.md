# TOOL-BOUNDARY — `oppl-runtime-tool` ↔ `oppb-runtime-tool` 경계 재확정 (W-38)

> 산출: W-38 / 소비: W-6 착수 입력
> 성격: 읽기 전용 실측 판정. 이 문서는 코드·PLAN·제안서·테스트를 변경하지 않는다.

## 0. 조사 기준

| 항목 | 값 |
|---|---|
| worktree | `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_132` |
| HEAD sha | `5288ffd66db4080c268f29a3bc0bed2e616ffb63` (`merge: main(131) 반영 — opal-agent 공용 runtime은 131 구현 채택`) |
| `oppl-runtime-tool` 상태 | HEAD 기준 **미변경** — `git status`에 없음. 이 문서의 `oppl-runtime-tool` 인용은 전부 HEAD와 동일 |
| `opal-agent` 상태 | **미커밋 작업본 존재** (W-1·W-39·W-2 진행 중). HEAD `opal_agent.py`는 1461줄, 작업본은 1935줄 |
| 기타 미커밋 | `opal-agent/tests/test_opal_agent_attempt.py`, `test_oppl_compat.py`, `PLAN.md`, `AGENTIC-LOG.md` |

[MUST] `opal_agent.py` 줄번호는 조사 중에도 이동했다. 이 문서는 **HEAD 부재/작업본 존재** 여부를 1급 사실로 쓰고, 작업본 줄번호는 조사 시점 값으로만 표기한다.

## 1. `oppl-runtime-tool` 공개 표면 전수 (코드 실측)

### 1.1 진입점

`opal/tools/oppl-runtime-tool/run.sh:12` — `$HOME/.opal/.venv/bin/python oppl_runtime_tool.py "$@"`. venv 부재 시 `{"ok":false,"error":"venv_missing"}` + exit 1 (`run.sh:8-9`).

### 1.2 CLI 서브커맨드 6종 (`oppl_runtime_tool.py:456-463`)

| 명령 | 필수 인자 | 선택 인자 | 성공 응답 키 | 거부 코드 |
|---|---|---|---|---|
| `config` | `--task-path` | — | `config` | `config_invalid` |
| `init` | `--task-path` `--run-id` | — | `run_id` `revision` `ledger_path` | `run_identity_missing` `config_invalid` |
| `admit` | `--task-path` `--scope` | `--task-id` `--phase`(scope=task-phase\|resume 시 필수) | `scope` `revision` + scope별(`design_round`\|`project_dispatch_count`\|`task_id`·`phase`·`attempt_count`·`resume_count`) + `reservation_id` | `active_attempt` `round_limit_exceeded` `attempt_limit_exceeded` `resume_limit_exceeded` `budget_exceeded` `no_progress` `decision_required` |
| `attempt-start` | `--task-path` `--task-id` `--phase` `--attempt-id` `--record-path` | — | `task_id` `phase` `attempt_id` `record_path` `revision` | `no_admission` `active_attempt` `ledger_missing` |
| `attempt-finish` | `--task-path` `--task-id` `--phase` `--attempt-id` `--status` | `--cost-usd` `--exit-class` `--verifier-id` `--command-id` `--failing-scenarios`(JSON 배열) `--error-code` `--contract-revision` `--t4b-branch` | `status` `revision` `cost_used` `project_dispatch_count` (+`failure_fingerprint` `identical_failure_count` `t4b_branch`) | `attempt_not_bound` `usage_error` |
| `show` | `--task-path` | — | `runtime`(ledger 전문) | `ledger_missing` |

- 인자 파서는 flag 화이트리스트 16종 고정(`:51-56`), `--k=v`/`--k v` 양식 모두 허용, 서브커맨드 위치 무관(`:86-111`).
- exit code: `0` 성공 / `1` 일반 오류 / `2` `config_invalid` / `3` admission 거부 (`:44-47`).
- 모든 출력은 단일 라인 JSON(`:68-71`). 예외 경로도 `internal_error`로 단일 라인 보장(`:480-481`).

### 1.3 파일 계약

| 경로 | 소유 | 근거 |
|---|---|---|
| `<task-path>/.oppl-run/runtime.json` | ledger 본문 | `ledger.py:82-83`, `LedgerStore.__init__ :324-328` |
| `<task-path>/.oppl-run/runtime.lock` | fcntl 배타 락 | `ledger.py:84`, `locked() :336-351` |
| `<task-path>/state.json` | **읽기만** — `run_id` 외래 참조 대조 | `oppl_runtime_tool.py:155-168` |
| `$OPAL_HOME/setting.json` → `<project-root>/.opal/setting.local.json` | `oppl.runtime` 블록 1단계 키 오버라이드 | `ledger.py:193-215`, `_read_runtime_block :133-153` |
| attempt record | **경로 외래 참조만** (`record_path`) — 내용을 읽지 않음 | `oppl_runtime_tool.py:339` |

`runtime.json` 최상위 12필드: `schema_version` `run_id` `revision` `status` `started_at` `deadline_at` `design_round` `project_dispatch_count` `cost_used` `wall_time_used` `budget_snapshot` `counters` (`ledger.py:266-281`).
`counters.<task_id>.phases.<phase>` 7필드: `attempt_count` `resume_count` `active_attempt_id` `status` `record_path` `last_failure_fingerprint` `identical_failure_count` (`ledger.py:301-309`).

### 1.4 공개 Python 심볼 (`ledger.py` @header `exports` + 실제 import)

`ConfigError` `LedgerStore` `load_config` `find_project_root` `failure_fingerprint` `phase_record` `new_ledger` `reservation_token` `REGISTERED_PHASES` `REQUIRED_CONFIG_KEYS` `RESUME_LIMIT` `PHASE_STATUSES` `FAILURE_STATUSES` `T4B_BRANCHES`

고정 enum·상수 실측:
- `REGISTERED_PHASES = ("t1","t2","g","t3","t4a","t4b")` (`ledger.py:34`) — **OPPL 파이프라인 전용 하드코딩**
- `REQUIRED_CONFIG_KEYS` 9종 (`:37-47`), `OPTIONAL_CONFIG_KEYS = ("max_cost_usd",)` (`:50`)
- `RESUME_LIMIT = 1` (`:55`) — 설정 키 아님
- `PHASE_STATUSES` 7종 (`:58`), `FAILURE_STATUSES` 3종 (`:61`), `NO_PROGRESS_EXEMPT_EXIT_CLASSES = ("api_error",)` (`:65`), `T4B_BRANCHES` 3종 (`:68`)
- `BUDGET_SNAPSHOT_KEYS` 6종 (`:72-79`), `SCHEMA_VERSION = "1.0"` (`:81`)

### 1.5 문서 ↔ 코드 충돌 (판정하지 않고 근거만 기록)

| # | 충돌 | 문서 측 | 코드 측 |
|---|---|---|---|
| X-1 | `ledger.py` @header `exports`가 실제 sibling import 심볼 4종을 누락 | `ledger.py:8-13` exports 목록 | `oppl_runtime_tool.py:22-38`이 `NO_PROGRESS_EXEMPT_EXIT_CLASSES`·`elapsed_seconds`·`is_reservation`·`normalize_error_code`를 import |
| X-2 | `admit` 검사 **순서**가 README 번호와 다름 | `README.md` §admit 1→6 순서(active → 상한 → resume → 예산 → 무진전 → decision) | `_check_admission`은 decision(`:200-201`) → active(`:206-209`) → 예산(`:211-222`) → 상한·resume·무진전(`:224-250`). 예산과 상한이 동시 초과면 코드는 `budget_exceeded`를 반환 |

X-1·X-2 모두 어느 쪽이 낡았는지 이 문서에서 정하지 않는다 — 131 소유 판단 사항이다. **W-38의 판정은 코드 실측 기준이므로 두 건 다 판정 결론을 바꾸지 않는다.**

### 1.6 실측 관찰 — OPPB가 복제하면 안 되는 동작

`cmd_init`은 기존 ledger 존재를 확인하지 않고 `new_ledger()`를 `expected_revision` 없이 write한다(`oppl_runtime_tool.py:170-173` + `ledger.py:356-362`). 즉 **재실행하면 모든 카운터가 0으로 초기화된다.** OPPB `init`은 재시작 가능성이 설계 전제(제안서 `§4.5:269-272`, `§4.6:395-401`)이므로 이 동작을 복제하면 안 된다.

## 2. `oppb-runtime-tool`이 만들려는 것

### 2.1 RED가 고정한 CLI 표면 (`opal/tools/oppb-runtime-tool/tests/`, 11파일 5,415줄)

테스트는 `run.sh` 서브프로세스와 run root 파일만으로 검증한다(`test_oppb_init.py:86-97`, PLAN H-6). 내부 심볼 import 0건.

| 명령 | 인자 | 소유 W |
|---|---|---|
| `init` | `--allocator-root` `--project-root` | W-6 |
| `start` / `resume` / `status` | `--run-root` | W-8 |
| `workgraph load` | `--run-root` `--spec` | W-7 |
| `task accept` | `--run-root` | W-7 |
| `evidence submit` | `--run-root` | W-9 |
| `lease acquire` / `verifier-acquire` / `check-parallel` / `list` | `--run-root` `--attempt` `--candidate` `--spec` | W-12 |
| `probe observe-write` / `seal` / `status` | `--run-root` `--project-root` `--commands` `--observation` | W-13 |
| `checkpoint candidate` / `guard` / `publish` | `--run-root` `--project-root` `--task` `--attempt` `--candidate` `--verification` `--record-baseline` | W-14 |
| `cache lookup` / `put-node` / `list-nodes` / `head-set` / `set-policy` / `overlay-fork` / `seal` / `reseed` / `gc` / `conformance` / `plan-execution` / `record-publication` | `--cache-root` `--source-root` `--node` `--parent` `--candidate` `--adapter` `--policy` `--state` `--command` `--verification` `--size-bytes` `--last-access` `--new-head` | W-15 |
| `recover register-attempt` / `prove-failure` / `scope-violation` / `seal-preimage` | `--run-root` `--project-root` `--task` `--attempt` `--candidate` `--pid` `--violation` | W-16 |

run root 파일 계약(테스트가 직접 읽는 것): `workgraph.json`(19회), `events.jsonl`, `attempts/<task>/<attempt>/{execution-packet.json,result.json}`, `evidence/`, `acceptance.json`, `gate-approvals.json`, `knowledge-receipt.json`, `INTENT.md`. 응답 키: `init` → `run_id`·`run_root`·`cache_root`(`test_oppb_init.py:101-104`), `start`/`resume` → `supervisor_pid`(`test_supervisor.py:260`), `status` → `attempts[].{attempt_id,pid,status}`(`test_supervisor.py:218-219, 272-296`).

경로 계약: `run_root == <allocator_root>/.opal-runs/<run_id>`(`test_oppb_init.py:137`), `cache_root == <allocator_root>/.opal-cache/oppb`(`:141`) — 둘 다 절대경로, `.git/info/exclude` 등록 + `git check-ignore` 실제 판정 확인.

### 2.2 제안서가 정한 책임

- `§4:107-109` — Controller Tool(DAG·Ready queue·예산·상태·dispatch·Repair·deadlock), Runtime Supervisor(`opal-agent` attempt 시작·heartbeat·timeout·수확·tick), `opal-agent`(process group·watchdog·framing·자식 종료·exit code·attempt record)
- `§4.5:245-263` — 산출물·단일 writer 표. `§4.5:265-267` — Controller는 `state.json`을 쓰지 않는다
- `§4.6:377-381` — **소유 경계 원칙**: OPPL=round·resume·수렴 상한, OPPB=DAG·lease·Repair·프로젝트 예산. "양쪽은 공용 attempt API와 schema를 소비하되 상대 Pilot의 상위 상태기계를 복제하거나 호출하지 않는다"
- `§4.6:395-401` — Supervisor event loop, 재기동 시 재부착·수확·고아 판정 선행, 동일 run 두 번째 Supervisor는 `flock` 거부
- `§9.1:783-801` / `§9.2:803-817` / `§9.3:819-836` — 미니 태스크·프로젝트 상태기계, 동시성 예산 3종
- 아카이브 OPPL `§2.2:46-47` — **"신규 프로젝트 스케줄러 또는 범용 Controller"와 "검증 결과 캐시"는 OPPL 비범위**. 아카이브 `§4:102-103` — `oppl-runtime-tool`=round·resume·예산 집계·admission·무진전·상태 전이·attempt ID 색인 / `opal-agent`=attempt 1건 원시 기능

## 3. 겹침 판정표

분류: **중복**(OPPL이 이미 제공 + OPPB가 재구현 예정) / **고유**(OPPB 전용) / **공용**(둘 다 필요).

| # | 기능 축 | OPPL 실측 | OPPB 계획 | 분류 | 권고 | 근거 |
|---|---|---|---|---|---|---|
| B-1 | attempt 재부착·수확·고아 3분류 | 없음(자체 미구현) — `opal-agent`에 위임. HEAD `opal_agent.py`에 `classify_attempt` **부재**, W-1 미커밋 작업본이 `:1529`에 신설 중(`reconcile_attempts :1654`, `load_attempt_record :1501`, `ATTEMPT_DISPOSITIONS :1379`, `_probe_identity :1446`, `_pid_elapsed_sec :1409`) | W-8 "W-1의 attempt record를 읽어 재부착 또는 수확"(PLAN:53). `test_supervisor.py:272-296`이 pid 동일성까지 단언 | **공용 — 이미 opal-agent 소유** | **`opal-agent` 그대로 재사용** | 제안서 `§4.6:373-374`가 "재시작 시 살아 있는 process 재부착 또는 고아 정리 판정"을 `opal-agent` 원시 기능으로 명시. PID 생존·PGID·`ps -o etime` 오차 허용 판정은 ~200줄의 미묘한 로직이고 양 Pilot 요구가 동일하다. **W-8이 이를 재구현하면 W-1 사고의 정확한 반복이다** |
| B-2 | attempt 기동(process group·watchdog·timeout·terminal framing·record 기록) | `opal-agent` 위임 — `oppl-runtime-tool`은 `record_path` 문자열만 보관(`oppl_runtime_tool.py:339`) | W-8 Supervisor가 attempt 시작 | **공용 — 이미 opal-agent 소유** | **`opal-agent` 그대로 재사용** | 제안서 `§4:109`. `call_agent(run_dir=, phase=, attempt=)`가 단일 writer 계약(`opal_agent.py` `_AttemptSink`, HEAD `:920`). W-8 설명에 "`opal-agent`로 기동"이 명시돼 있지 않아 자체 spawn 위험이 있다 |
| B-3 | 원자 파일 쓰기 + revision 낙관적 잠금 | `LedgerStore.write` — lock → revision 대조 → `mkstemp`(대상 dir) → `fsync` → `os.replace` (`ledger.py:356-377`) | W-7 `workgraph.json` revision lock, W-13 probe seal 원자 봉인(`test_probe.py:293`), W-9 evidence 불변 색인, W-15 cache CAS | **중복** | **`oppb-runtime-tool`이 따로 구현** (단, `ledger.py:336-377` 패턴을 형태 그대로 복제) | PRINCIPLES §2·§3. 동일 패턴이 이미 `state_tool`·`backlog_tool`·`ledger.py`·`opal_agent._atomic_write`(HEAD `:944`) 4벌 공존한다. 5번째 추출은 4개 green 도구를 동시에 건드리는 변경이고, H-7(상류 main 병렬 변경)이 활성 위험인 지금 비용이 중복 비용보다 크다. 약 55줄 표준 라이브러리 코드다. 도구 간 Python import 선례도 없다(`oppl-runtime-tool`은 `opal-agent`를 import하지 않고 서브프로세스로만 쓴다 — `tests/test_ac_integration.py:53`) |
| B-4 | 파일 락(단일 writer 직렬화) | `fcntl.flock` 배타 락, `.oppl-run/runtime.lock` (`ledger.py:336-351`) | Supervisor 단일 인스턴스 `flock`(제안서 `§4.6:401`), publication 짧은 전역 lock(`§4.5:280-284`) | **중복(얕음)** | **`oppb-runtime-tool`이 따로 구현** | 표준 라이브러리 3줄 호출. 용도가 다르다 — OPPL은 read-modify-write 직렬화, OPPB는 상주 프로세스 단일성 + ref 전진 구간 직렬화. 공용화 대상 없음 |
| B-5 | 상한 카운터·admission 판정 | `admit` 4 scope + 8종 폐쇄 거부 코드(`oppl_runtime_tool.py:49, 197-312`). 축: design_round·project_dispatch·task attempt·resume·cost·wall_time·동일실패 | W-8은 **process 동시 실행 상한**(`max_active_runners=2`·`max_active_executors=2`·`max_total_agent_processes=4`, 제안서 `§9.3:825-827`, `test_supervisor.py:245`). W-12 `lease check-parallel`은 **경로·계약 교집합 admission**(`test_lease.py:184, 236-244`) | **고유 (이름만 같음)** | **`oppb-runtime-tool`이 따로 구현** | OPPL admission은 "누적 횟수/예산이 남았는가"이고 OPPB admission은 "지금 동시에 몇 개가 도는가"와 "이 둘이 같은 자원을 건드리는가"다. 공유 가능한 술어가 0이다. OPPL은 동시 프로세스 수 개념 자체가 없다(`_check_admission`에 프로세스 카운트 없음) |
| B-6 | attempt ledger·집계 저장소 | `.oppl-run/runtime.json`, key=(task_id, phase∈`REGISTERED_PHASES` t1/t2/g/t3/t4a/t4b `ledger.py:34`) | `workgraph.json`(P3 DAG·미니 태스크·계약·예산·상태) + `attempts/<task>/<attempt>/` | **고유** | **`oppb-runtime-tool`이 따로 구현** | OPPL ledger의 phase enum이 OPPL 파이프라인에 하드코딩돼 있다. OPPB는 M1/M2/M3 + DAG 의존이라 enum이 맞지 않고, 재사용하려면 `REGISTERED_PHASES`·`REQUIRED_CONFIG_KEYS`·`hard_timeout_sec_by_phase` 검증(`ledger.py:164-190`)을 전부 파라미터화해야 한다 — 131 계약 파괴. 제안서 `§4.6:378-379`의 소유 경계 원칙 그대로 |
| B-7 | 상태 전이 enum·receipt 경로 | `PHASE_STATUSES` 7종(`ledger.py:58`), `attempt-finish`가 유일한 확정 경로(`oppl_runtime_tool.py:394-399`, AC-12) | 미니 태스크 `queued/running/verifying/accepted/repair/needs_revalidation/blocked`(`§9.1:783-801`), 프로젝트 P0~P5는 **state-tool 소유**(`§4.5:265-267`) | **고유** | **`oppb-runtime-tool`이 따로 구현** | enum 교집합이 `running`·`blocked` 2개뿐이고 의미가 다르다(OPPL=attempt 1건, OPPB=미니 태스크). "receipt 없는 done 금지" 원칙만 계승할 가치가 있고 그것은 코드가 아니라 설계 규약이다 |
| B-8 | run root 디렉토리 구조 | `<task-path>/.oppl-run/` — 태스크 폴더 하위, 2파일(`ledger.py:82-84`) | `<allocator_root>/.opal-runs/<run_id>/` — 허브 루트 미추적 + `.git/info/exclude` 멱등 등록 + `check-ignore` 실제 판정(`test_oppb_init.py:137-141`, 제안서 `§4.5:253, 270-272`) | **고유** | **`oppb-runtime-tool`이 따로 구현** | 위치·수명·Git 가시성·writer가 전부 다르다. 공유 코드 없음 |
| B-9 | run identity(run_id) 발급 정책 | **발급하지 않는다.** `state.json.run_id`와 `--run-id`가 일치할 때만 진행, 불일치·부재는 `run_identity_missing`(`oppl_runtime_tool.py:154-168`, D8) | **`init`이 자체 발급한다.** `--run-id` 인자 없음, 응답 `run_id`로 run root 경로가 결정됨(`test_oppb_init.py:101-104, 137`) | **정책 충돌(공용 후보)** | **PM 판단 — 현 RED 표면 유지 시 `oppb`가 따로 구현** | 두 Pilot의 run identity 정책이 정면으로 다르다. OPPL은 state-tool을 SSOT로 두고 OPPB는 도구가 발급한다. 아카이브 `§4:102`가 "attempt ID 색인"만 `oppl-runtime-tool` 책임으로 두고 run_id 발급은 빼놓은 것과 일관되지만, OPPB init은 `--project-root`(태스크 캡슐)를 이미 받으면서 그 `state.json.run_id`를 보지 않는다. **§5·§6 참조 — 이 항목만 RED 표면 변경을 유발할 수 있다** |
| B-10 | 설정 SSOT 로더 | `$OPAL_HOME/setting.json` + `.opal/setting.local.json`의 `oppl.runtime` 1단계 키 오버라이드, 필수 9키 검증(`ledger.py:193-215`) | 설정 파일 경로 없음. budget은 `workgraph load --spec <file>`의 `budget` 블록(`test_controller.py:189-193`), cache 정책은 `--policy <file>` / `.opal/oppb-environment.json.cache_policy`(`§4.5:298`) | **고유** | **`oppb-runtime-tool`이 따로 구현 — 단, 설정 파일 층을 새로 만들지 않는다** | RED가 `--spec`/`--policy` 파일 주입으로 계약을 고정했다. `setting.json`에 `oppb.runtime` 블록을 추가하면 RED와 어긋나고 층이 2개가 된다. `find_project_root`(`ledger.py:119-125`)만 형태상 유사하나 OPPB는 `--allocator-root`·`--project-root`를 **명시 인자로만** 받고 추론을 금지한다(`test_oppb_init.py:195-201`, PLAN H-2) |
| B-11 | 무진전 판정(실패 지문·연속 카운터) | `failure_fingerprint()` SHA-256 8필드(`ledger.py:222-240`), `identical_failure_count`, `api_error` 면제(`:65`), `no_progress` 거부 | **현 범위에 없다.** W-6~W-16 어디에도 Repair 반복 상한·무진전 판정이 없고, RED 11파일 전체에 `no_progress`·`identical`·`fingerprint`(실패 지문 의미) 단언 0건 | **공용 후보 — 현 시점 OPPB 미필요** | **지금은 어느 쪽도 옮기지 않는다.** 트리거 발생 시 `opal-agent`로 승격 | PRINCIPLES §2. 소비자가 1개인 추상화를 미리 만들지 않는다. 지문 payload 8필드 중 `exit_class`는 이미 `opal-agent`의 `EXIT_CLASSES`(HEAD `opal_agent.py:161`)이고 나머지도 attempt 단위라 승격 자체는 자연스럽다. **트리거**: 제안서 `§11:857` "예산 초과·반복 무진전" 게이트를 OPPB가 실제로 집행하는 Work item이 생기는 시점. 그때 `ledger.failure_fingerprint`를 `opal-agent`로 올리고 `oppl-runtime-tool`이 그것을 소비하도록 바꾼다 |
| B-12 | 비용·벽시계 예산 | `max_cost_usd`·`max_wall_time_sec`, `cost_used` 누적(비배수, C-10), `deadline_at`(`ledger.py:266-281`, `oppl_runtime_tool.py:404-406`) | **현 범위에 없다.** 제안서 `§4:107`이 Controller 책임에 "예산"을 넣었으나 `§9.3`의 예산은 동시성뿐이고, RED에 cost/wall 단언 0건 | **공용 후보 — 현 시점 OPPB 미필요** | **B-11과 동일. 지금 만들지 않는다** | 위와 같음. `§11:857` 게이트 4가 미충족 상태로 남는 것은 **범위 결손**이며 §5에서 PLAN 영향으로 보고한다(추정 아님 — RED·Work item 양쪽에서 부재를 실측) |
| B-13 | 출력 계약(단일 라인 JSON + exit code) | `emit`/`fail`(`oppl_runtime_tool.py:68-79`), `harness/tool-output-contract.md` | 동일 계약(`parse_json_stdout`, `test_oppb_init.py:90-97`) | **공용 — 규약** | **코드 공유 없이 규약만 따른다** | 21개 기존 도구가 각자 `ok`/`err` 헬퍼를 갖는 것이 현행 관례(PLAN §Approach 3). 20줄 헬퍼를 공용화할 이유가 없다 |

**집계** — 중복 2건(B-3, B-4), 고유 6건(B-5~B-8, B-10 + B-13 규약), 공용 4건(B-1, B-2, B-11, B-12), 정책 충돌 1건(B-9).

**가장 비싼 것 1건: B-1** — attempt 재부착·수확·고아 3분류. 재구현 시 PID 생존 판정·PGID 확인·`ps -o etime` 기반 identity 대조·미종료 자식 회수 판정을 OPPB가 독자적으로 다시 쓰게 되고(작업본 `opal_agent.py:1379-1720` ≈ 340줄), W-1 산출물과 정확히 같은 로직이 두 벌 남는다. 게다가 두 구현이 갈라지면 "고아 0" 수용기준(AC-11)이 Pilot마다 다르게 집행된다. **B-2와 함께 W-8 하나에 걸려 있다.**

## 4. 소유 경계 원칙 재확인 결과

제안서 `§4.6:377-381`의 분리선은 **현행 코드에서 그대로 성립한다.**

| 층 | 소유 | 실측 확인 |
|---|---|---|
| attempt 1건 실행 primitive | `opal-agent` | `oppl-runtime-tool`이 attempt 원문을 저장하지 않고 `record_path` 문자열만 보관(`oppl_runtime_tool.py:339`). ledger 12필드에 PID·PGID·heartbeat 없음(`ledger.py:266-281`) |
| OPPL 상위 상태기계 | `oppl-runtime-tool` | round·resume·수렴 상한 전용. 프로세스 동시성·DAG·lease·cache 개념 0 |
| OPPB 상위 상태기계 | `oppb-runtime-tool` | 아카이브 `§2.2:46-47`이 "신규 프로젝트 스케줄러 또는 범용 Controller"·"검증 결과 캐시"를 OPPL 비범위로 명시 |

**어느 방향으로도 상대 Pilot 호출·복제 요구가 발견되지 않았다.** 두 Pilot이 공유하는 것은 `opal-agent` 하나뿐이며, 그 접점은 B-1·B-2 두 건이다.

## 5. PLAN 영향 (PM 반영 대상 — 이 문서는 PLAN을 고치지 않는다)

| # | 대상 | 변경 방향 | 내용 |
|---|---|---|---|
| P-1 | **W-8** (PLAN:53) | **범위 축소 + 제약 추가** | "attempt 재부착/수확/고아 3분류를 `opal-agent`의 `classify_attempt`·`reconcile_attempts`·`load_attempt_record` **호출로만** 수행하고 판정 로직을 재구현하지 않는다"를 명시. 현 문구 "W-1의 attempt record를 읽어"는 *파일*을 읽으라는 뜻으로도 읽혀 B-1 재구현 위험이 있다 |
| P-2 | **W-8** (PLAN:53) | **제약 추가** | "attempt 기동은 `opal-agent`(`call_agent(run_dir=, phase=, attempt=)`)를 경유하고 Supervisor가 직접 `subprocess`로 provider CLI를 띄우지 않는다" 명시(B-2) |
| P-3 | **W-8** (PLAN:53) | **선행 작업 보강** | 현재 선행이 `W-6`뿐. `W-1`(재부착 진입점)·`W-39`(시작 시점 record) 추가. P4/P5 순서상 이미 뒤이나 의존이 문서에 없다 |
| P-4 | **W-6** (PLAN:51) | **제약 추가** | (a) `init` 재실행이 기존 run 상태를 초기화하지 않는다 — `oppl` `cmd_init`의 무조건 덮어쓰기(§1.6)를 복제 금지. (b) `setting.json`에 `oppb.runtime` 설정 층을 만들지 않는다 — 예산·정책은 `--spec`·`--policy` 파일 주입이 RED 계약(B-10) |
| P-5 | **W-6** (PLAN:51) | **결정 필요** | run identity 정책(B-9). 현 RED는 `init`이 run_id를 자체 발급한다. OPPL D8(state-tool 발급)과 정렬할지 PM 판단. **정렬을 택하면 RED 표면 변경이 필요하다(§6)** |
| P-6 | **W-7** (PLAN:52) | **구현 지침** | `workgraph.json` revision lock 원자 쓰기를 `ledger.py:336-377` 패턴(lock → revision 대조 → 대상 dir `mkstemp` → `fsync` → `os.replace`)으로 형태 복제. `oppl-runtime-tool`을 import하지 않는다(B-3) |
| P-7 | **W-9·W-12~W-16** | **변경 없음** | Evidence·Lease·Probe·Checkpoint·Cache·Recovery는 OPPL과 겹치는 축이 0이다. 아카이브 `§2.2:46-47`이 cache·Controller를 OPPL 비범위로 명시 |
| P-8 | **PLAN §Risks** | **항목 추가 권고** | 제안서 `§11:857` 게이트 4(예산 초과·반복 무진전)를 집행하는 Work item이 G2~G5 어디에도 없다(B-11·B-12 실측). 현 태스크 범위 유지 여부를 PM이 판정해야 한다. 유지한다면 "OPPB v1은 동시성 예산만 집행하고 비용·무진전 예산은 후속"임을 PLAN에 명시 |
| P-9 | **PLAN H-7** (PLAN:143) | **사실 갱신** | W-38 실행 시점에 `opal_agent.py`가 미커밋 작업본으로 변동 중이었다(HEAD 1461줄 → 작업본 1935줄). W-38 결론은 `oppl-runtime-tool`(HEAD 무변경) 기준이므로 영향 없으나, W-11 G2 동결 시 `opal-agent` 공개 심볼을 다시 실측해야 한다 |

**범위가 늘어나는 Work item: 없음.** 축소 1건(W-8, B-1·B-2 재구현 제거), 제약 추가 3건(W-6·W-7·W-8), 결정 요청 2건(P-5·P-8).

## 6. RED 테스트 표면과의 충돌

| 권고 | 충돌 여부 |
|---|---|
| P-1·P-2·P-3 (W-8이 `opal-agent` 재사용) | **충돌 없음.** `test_supervisor.py`는 `status` 응답의 `attempts[].{attempt_id,pid,status}`와 pid 동일성만 단언한다(`:272-296`). 내부 구현 무관 |
| P-4 (a) init 멱등 | **충돌 없음.** `test_oppb_init.py`에 init 재실행 단언 없음 |
| P-4 (b) 설정 층 미신설 | **충돌 없음** — RED 계약과 일치 |
| P-6 (원자 쓰기 자체 구현) | **충돌 없음.** `test_controller.py:273-283`은 `workgraph.json`의 `revision` 전진만 본다 |
| **P-5 (run identity를 OPPL D8로 정렬)** | **충돌한다.** 정렬하면 `init`이 `--run-id`를 요구하거나 `--project-root/state.json.run_id`를 게이트로 써야 하는데, RED는 `init --allocator-root --project-root` 2인자만으로 성공하고 응답 `run_id`로 run root 경로를 구성한다(`test_oppb_init.py:101-104, 137`). 최소 `init_hub` 헬퍼와 S-7 4개 테스트가 바뀐다 |

`scenario-lock`이 걸려 있어 시나리오는 변경 불가이고, 테스트 표면 변경은 PM 판단 사항이다. **이 문서는 P-5를 결정하지 않고 선택지와 비용만 제시한다.** 현 RED 표면을 유지하는 쪽(=OPPB init 자체 발급)이 기본값이며, 그 경우 P-5는 "PLAN·README에 두 Pilot의 run identity 정책이 의도적으로 다르다는 1행을 명시"로 축소된다.

## 7. W-6 착수 입력 요약

1. `opal-agent`를 서브프로세스·라이브러리로 **재사용**한다 — attempt 기동(B-2)과 재부착·수확·고아 판정(B-1). 두 기능을 `oppb-runtime-tool`에 다시 쓰지 않는다.
2. `oppl-runtime-tool`은 **import·호출하지 않는다.** 재사용할 코드가 없고, 원칙상 상대 Pilot의 상위 상태기계다.
3. 원자 쓰기·파일 락은 `ledger.py:336-377` 패턴을 **형태만 복제**한다. 공용 추출을 이 태스크에서 시도하지 않는다.
4. `init`은 멱등이어야 하고 재실행이 run 상태를 초기화하지 않는다.
5. 설정 층을 새로 만들지 않는다 — 예산·정책은 명시 인자 파일 주입.
