---
template: sdlc-v2
---
# PLAN: T02 — 워킹 스켈레톤 (CLI 관통 1건)

> 입력: [TASK.md](../../TASK.md), [CONTRACT.md](../../../../docs/run-log/CONTRACT.md), [TRD.md](../../../../docs/run-log/TRD.md), [surfaces.json](../../../../docs/run-log/surfaces.json)
> 상위 태스크: `tasks/123-260912-oppl-태스크-실행로그-표준화`

## Approach

끝에서 끝까지 **관통 경로 1건**만 만든다 — `state-tool init --run-log-mode shadow`가 스키마 1.2 `state.json`과
첫 기록 조각을 만들고, `run-log-tool append` 1건이 붙고, `run-log-tool validate-run`이 그 경로를 통과한다(AC-2).

관통에 필요한 최소만 구현하고, 각 최소 구현 옆에 완성 소유 태스크를 명시한다. 목·스텁으로 대체하지 않는다 —
모든 시나리오는 실제 셸에서 `run.sh`를 호출하고 디스크 산출물을 검사하는 `real-usage` 충실도로 판정한다.

세 갈래의 설계 압력이 이 계획의 형태를 결정했다.

1. **기존 회귀가 동결 단언으로 지켜진다.** `state_tool.ERROR_CODES`와 `state.schema.json`은 각각 4건·1건의
   동결 단언에 묶여 있어(아래 Decisions D-A·D-B), 그 자산을 건드리는 순간 C-2가 깨진다. 따라서 신규 계약은
   전부 **기존 자산 바깥의 새 자산**에 둔다.
2. **D-5 단방향 의존이 검증 전략 그 자체다.** `run_log_core`·`run-log-tool`은 `state.json`을 읽지 않으며,
   그 사실을 기록 도구 테스트가 state fixture 없이 통과한다는 실측으로 판정한다(AC-19 / MV-24).
3. **경로 계약 §3.2가 추론을 금지한다.** 기록 자산 위치는 전달받은 절대 task path로만 해석한다.

범위는 **shadow 초기화 관통 1건**이다. `--run-log-mode active`는 배정 파일(`profiles.json`)이 아직 배포되지
않았으므로 계약상 정확한 `profile_not_found`로 거부하고, active 3종 분기 전건은 소유 태스크 확정이 필요하다
(아래 Risks H-4 — PM 판단 필요).

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| **D-A. run-log 오류 코드는 `run_log_core`가 자기 테이블로 소유하고, `state_tool.ERROR_CODES` 딕셔너리 리터럴은 한 글자도 건드리지 않는다** | `run_log_core.RUN_LOG_ERROR_CODES`가 run-log 계열 코드의 SSOT다. `state_tool.err()`는 템플릿 조회만 `_error_template(code)` 헬퍼로 바꿔 `ERROR_CODES` → `RUN_LOG_ERROR_CODES` 순으로 **조회만** 합친다. `ERROR_CODES` 키 집합·종수·README 헤더 수치는 불변 | 동결 단언 4건이 전부 `ERROR_CODES` **키 집합/종수**만 본다 — `err()` 본문이나 별도 테이블은 보지 않는다: `test_error_codes_count`(`len(ST.ERROR_CODES)==51`, `tests/test_state_tool.py:2582-2583`), `test_all_28_codes_registered`(`EXPECTED_CODES` 건수 일치, 같은 파일 2585-2591), `test_s7_error_catalog_marker_import_realignment`(README 「에러 코드 카탈로그 (N종」 헤더 == 실측 == 51, 2622-2638), S-40 `error_codes_key_set_untouched`(HEAD의 `state_tool.py`를 AST 파싱해 키 집합 대조, 삭제 0건·추가는 선언 목록 한정, 9125-9159). 도구마다 자기 오류 테이블을 갖는 것은 신설 관례가 아니라 **기존 관례**다 — `opal/tools/backlog-tool/backlog_tool.py:6` @header "state-tool 패턴(ok/err 헬퍼, … ERROR_CODES SSOT)을 복제한다", 그리고 `state_tool.py:218-223`의 `WARNING_CODES` 물리 분리 주석이 "ERROR_CODES 키 집합은 회귀 테스트가 HEAD와 대조해 고정하고 있어 종수를 늘리면 계약이 깨진다"를 이미 같은 이유로 선언한다. 본 결정은 그 관례의 3번째 적용이며 **기존 테스트 수정 0건** |
| **D-B. T02는 `opal/tools/state-tool/schema/state.schema.json`을 건드리지 않는다** | 런타임은 `schema_version:"1.2"`와 `run_log` 블록을 내지만, 정적 스키마 자산의 1.2 반영은 T05(상태 1.2 블록 소유)가 같은 변경 단위로 수행한다. T02 산출물에 이 파일은 없다 | `cmd_validate`는 `state.schema.json`을 **참조하지 않는다** — 필수 필드 목록이 함수 안에 하드코딩돼 있다(`state_tool.py:2077-2082`), 테스트 주석도 같은 사실을 명시한다(`tests/test_state_tool.py:5485`). 따라서 관통(AC-2)은 스키마 파일 갱신 없이 성립한다. 반대로 갱신하면 `test_schema_version_enum_allows_1_0_and_1_1`이 `set(enum)=={"1.0","1.1"}`을 단언하므로(`tests/test_state_tool.py:5461-5466) 즉시 FAIL하고, root `additionalProperties:false`(`schema/state.schema.json:16`) 때문에 `run_log` 속성 등재도 함께 필요해진다. 워킹 스켈레톤에 동결 단언 갱신을 끼워 넣지 않는다 → **H-1 / PM 판단 필요** |
| **D-C. `run-log-tool`은 `opal/tools/run-log-tool/`에 신설하고, `state_tool`은 형제 경로 우선 해석으로 `run_log_core`를 같은 프로세스에서 import한다** | `_run_log_core_dir()`는 형제 `<state_tool 디렉터리>/../run-log-tool`이 있으면 그 경로, 없으면 `~/.opal/tools/run-log-tool`을 반환하고, 그 경로를 `sys.path`에 삽입한 뒤 `import run_log_core`한다. 하위 프로세스 호출 금지 | `state_tool.py:293-306` `_date_js_path()`가 이미 "형제 배치 우선, 없으면 배포본" 관례를 확립하고 그 이유를 적어 두었다 — "배포 레이아웃에서는 형제 경로가 곧 `~/.opal/tools/...`라 종전과 동일하게 해석되고, 레포 소스에서 직접 실행할 때만 레포 쪽을 쓰게 되어 배포 전 검증이 가능하다". 디렉터리명에 하이픈이 있어 패키지 import가 불가능하므로 `sys.path` 경유가 유일한 수단이다. 하위 프로세스 호출은 락 재획득으로 D-4와 충돌한다(TRD D-5 대안 (b)) |
| **D-D. 기록 코어는 `state.json`을 읽지 않고, 소스에 `state_tool` import가 0건이다** | `run_log_core.py`·`run_log_tool.py`는 `task_path`·`run_id`·`event` dict만 소비한다. 역방향 import 없음. 기록 도구 테스트는 state fixture를 만들지 않는다 | TRD D-5, TASK C-4, CONTRACT §2.6·§3.1. 이 성질이 곧 AC-19/MV-24의 판정 대상이며, 깨지면 기록 도구 검증 전체가 상태 자산에 결합된다 |
| **D-E. shadow 초기화도 outbox 2단 커밋을 그대로 밟는다** | ① 배타 락 획득 → ② 1차 원자 쓰기(`status=pending` + `run.started` compact payload를 `pending_events`에 적재) → ③ `run/` 디렉터리·첫 조각 생성 + 같은 `event_id`로 append + fsync → ④ 2차 원자 쓰기(보관함 비우고 `status=active`) → ⑤ 락 해제 | CONTRACT §2.5, TRD 데이터 흐름 (a). 관통에서 2단 커밋을 생략하면 T05의 복구 경로가 설 자리가 없어진다. **상한·admission·override·중단 복구 reconcile은 T05가 완성한다** |
| **D-F. 상태 원자 쓰기는 run-log 경로 전용 헬퍼로 도입하고 `save_state_json()`은 손대지 않는다** | 신규 `_atomic_write_state_json(task_path, state)`(tmp → fsync → `os.replace`)를 **run-log init 경로의 2회 쓰기에서만** 호출한다. 기존 경로는 `save_state_json()`(`state_tool.py:363-368`) 그대로 | 원자성은 D-2가 요구하지만, 기존 전 경로를 바꾸면 회귀 표면이 불필요하게 넓어진다. 원자 쓰기 구현은 `opal/tools/memory-tool/memory_tool.py:358-377` `atomic_write_json()` 선례를 복제한다. **상태 전이 전반으로의 확장은 T05가 완성한다** |
| **D-G. 사건 `timestamp`는 Python 표준 라이브러리의 UTC를 쓰고 `date.js`를 타지 않는다** | `run_log_core`는 `datetime.now(timezone.utc)`로 RFC 3339 밀리초 `...Z`를 만든다. `state.json`의 `created_at`/`updated_at`은 기존대로 `get_kst_datetime()`(`state_tool.py:308-336`)을 쓴다 | CONTRACT §1.1은 사건 시각을 UTC 밀리초로 못 박고 로컬 시각 저장을 금지한다. 기록 코어가 node 바이너리에 의존하면 D-5의 "명시 인자만 소비" 성질이 외부 프로세스 의존으로 흐려진다. TRD 시간 모델 §두 시간계 — 두 계는 병존하며 어느 쪽도 다른 쪽에서 역산하지 않는다 |
| **D-H. 조각 파일명 segment는 4자리 0패딩(`0001`)** | 첫 조각은 `<task-path>/run/run-log-{run_id}-0001.jsonl` | D-1이 정한 경로 패턴의 `{segment}` 자리를 결정론화한다. **4 MiB 경계 전환과 다음 번호 승계는 T04가 완성한다** |
| **D-I. 순번은 조각 전량 스캔으로 발급한다(색인 없음)** | `sequence`는 run 전역 최대+1, `actor_sequence`는 `(actor.kind, actor.id)` 범위 최대+1을 매 append마다 조각을 읽어 계산한다 | D-3은 `run/.runtime/` 색인을 **파생 인덱스**로 규정하고 "부재·손상 시 1회 스캔 재구축"을 정상 경로의 한 분기로 둔다. 즉 전량 스캔은 색인 없는 상태의 **정의된 동작**이지 임시방편이 아니다. **색인 도입과 재구축 동일성은 T04가 완성한다** |
| **D-J. 배타 락은 최소 형태로 지금 넣는다** | `<task-path>/.opal-task.lock`에 `fcntl.flock(LOCK_EX|LOCK_NB)` 재시도 + 기본 30,000 ms 상한, 초과 시 `task_lock_timeout` 반환(자동 재시도 없음). `lock_held=True`면 코어는 재획득하지 않는다 | CONTRACT §2.6 시그니처가 `lock_held`를 요구하므로 락은 관통의 일부다. 락 구현은 `backlog_tool.py:167-197`의 `fcntl` 배타 락 read-modify-write 선례를 따른다. **경합 실증·설정 조정·재구축 중 fail-closed 대기는 T04가 완성한다** |
| **D-K. shadow 기본 `completion_profile`은 `cooperative`, `completion_profile_receipt`는 `null`** | `--run-log-mode shadow`가 `--channel-id` 없이 호출되면 `run_log.completion_profile="cooperative"`, `completion_profile_receipt=null` | CONTRACT §1.4는 `completion_profile`을 필수로, receipt를 `mode=active`에만 조건부 필수로 둔다. §1.5는 `cooperative`를 "기계 증거 없음 / shadow 전용"으로 정의한다 — adapter 증거가 아직 없는 스켈레톤에 정직하게 대응하는 유일한 값이다 |
| **D-L. `--run-log-mode` 미지정 init은 개정 전과 바이트 동일한 `state.json`을 낸다** | 인자 미지정 시 `schema_version` 판정(`state_tool.py:1405`)·`state` dict 구성(1411-1421)·`save_state_json()` 경로가 전부 종전과 같고, `run_log` 키를 만들지 않으며 `run/` 디렉터리도 만들지 않는다 | TASK C-3. 판정은 육안이 아니라 HEAD 대조 바이트 비교로 한다(시나리오 S-2) — `state_tool.py:1423-1425` `--worktree` 조건부 영속화가 "미지정 시 키 자체를 생성하지 않는다 — 기존 state.json과 스키마·바이트 동일"로 같은 계약을 이미 집행한 선례다 |

### 사건 필수 필드 — 스켈레톤이 발급하는 것과 넘기는 것 (설계 쟁점 2 결론)

`run.started` 1건은 CONTRACT §1.1 필수 필드를 **전건 채워서** 기록한다. 필드를 비우고 넘기면 `validate-run`이
검증할 대상 자체가 없어져 관통이 성립하지 않는다.

| 필드 | T02가 실제로 발급하는 값 | 완성 소유 |
|---|---|---|
| `schema_version` | 고정 `"1.0"`(사건 계약 버전. 상태 파일 버전과 별개) | — |
| `event_id` | `evt_<uuid4>` — `run_log_core`가 발급 | — |
| `request_id` | `req_<uuid4>` — `state-tool`이 1차 원자 쓰기 **이전에 확정**해 보관함 payload와 append에 같은 값을 쓴다(§1.3 A7 "사전 확정 event ID(= `request_id`)") | 동일 키 재호출의 `idempotent_hit`/`request_id_conflict` 판정은 **T03** |
| `sequence` | run 전역 최대+1 (조각 전량 스캔, D-I) | 색인 기반 발급·재구축 동일성은 **T04** |
| `actor_sequence` | `(actor.kind, actor.id)` 범위 최대+1 (같은 스캔) | `worker_run_id` 범위 발급은 **T04**(`begin-worker` 소유) |
| `timestamp` | `datetime.now(timezone.utc)` RFC 3339 밀리초 (D-G) | 시간계 2계 정합·날짜 경계는 **T06** |
| `task_id` | 전달받은 task path의 마지막 디렉터리명 | — |
| `run_id` | `run_<uuid4>` — `state-tool init`이 발급 | `restart-run` 재발급은 **T10** |
| `parent_run_id` / `worker_run_id` / `caused_by_event_id` | 전부 `null`(널 허용 필수 필드로 명시 기록) | worker 계열 채움은 **T04·T07** |
| `event` | `"run.started"` | 12종 어휘 전수는 **T03** |
| `actor` | `{"kind":"tool","id":"state-tool","provider":null,"session_id":null}` | actor enum 전수 집행은 **T03** |
| `provenance` | `{"type":"direct","recorded_by":{"kind":"tool","id":"state-tool"},"worker_log_token_id":null,"source":null}` | §1.3 허용 조합표 전수 집행은 **T03** |
| `summary` | 1줄 요약(예: `"run started (shadow)"`) | — |
| `reason`/`reason_code`/`duration_*`/`refs`/`data` | `run.started`에 필수가 아니므로 미기록 | terminal 조건부 필수 집행은 **T08·T09** |

T02의 `append` 검증은 **폐쇄형 최상위 키 검사 1건**만 집행한다 — §1.1에 정의되지 않은 최상위 키와 §1.2 밖의
`event` 값을 `schema_invalid`로 거부한다. §1.3 조합표 전수, 16 KiB 상한, provenance 증거 검증, 멱등 충돌 판정은
**T03이 완성한다**.

### 신설 오류 코드 테이블 (`run_log_core.RUN_LOG_ERROR_CODES`)

T02가 등재하는 최소 집합. 나머지 run-log 계열 코드는 각 소유 태스크가 같은 테이블에 가산한다.

| 코드 | T02에서의 발생 조건 | 계약 |
|---|---|---|
| `task_path_not_absolute` | `--task`/`task_path`가 절대 경로가 아님 | §2.2 / §3.2 |
| `task_lock_timeout` | 배타 락 대기 30,000 ms 초과 | §2.2 / §2.7 |
| `run_log_write_failed` | 조각 생성·append·fsync 실패 | §2.2 |
| `run_log_missing` | `append`/`validate-run` 대상 실행 디렉터리·조각 부재 | §2.2 |
| `schema_invalid` | 폐쇄형 최상위 키 위반, `event` enum 밖 값 | §2.2 |
| `profile_not_found` | `--run-log-mode active` 호출(배정 파일 미배포) | §2.2 — H-4 참조 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 기록 코어 신설 | opal-be-agent | `opal/tools/run-log-tool/run_log_core.py` | 신규 파일. @header 블록(module/layer=util/domain=opal-tools/description/exports) 작성. `RUN_LOG_ERROR_CODES` 테이블(위 6종), `ok()`/`err()` 봉투 헬퍼(`state_tool.py:264-288` 패턴 복제, `{"ok":true,"data":{...}}` / `{"ok":false,"error":{"code","message","detail"}}`, `ok:false`는 exit≠0), `task_lock(task_path, *, timeout_ms=30000)` 컨텍스트매니저(`<task-path>/.opal-task.lock`에 `fcntl.flock(LOCK_EX + LOCK_NB)` 재시도 — `backlog_tool.py:167-197` 선례, 상한 초과 시 `task_lock_timeout`), `require_absolute(task_path)`(§3.2 — cwd·워크트리 문자열 추론 금지, 위반 시 `task_path_not_absolute`), `new_event_id()`/`new_run_id()`/`utc_now_ms()`(D-G), `segment_path(task_path, run_id, n)`(D-H), `scan_sequences(task_path, run_id)`(조각 전량 스캔 → run 전역 max·주체별 max, D-I), `validate_event(event)`(폐쇄형 최상위 키 + `event` enum 검사 → `schema_invalid`), `init(task_path, run_id, *, lock_held=False, lock_timeout_ms=30000)`(§2.6 시그니처. `run/` 디렉터리 + 첫 조각 생성, 이미 있으면 `created:false` 멱등), `append(task_path, run_id, event, *, lock_held=False, lock_timeout_ms=30000)`(순번 채움 → 줄 직렬화 → `O_APPEND` 쓰기 → `fsync` → `{event_id, sequence, actor_sequence, segment, idempotent_hit:false}`), `validate_run(task_path, run_id, *, lock_held=False, lock_timeout_ms=30000)`(조각 정렬·줄 파싱·순번 중복/누락 수집 → `{run_id, verdict, segment_count, event_count, total_bytes, sequence_gaps, violations}`). Python 3 표준 라이브러리만. **`state.json`·`state_tool` 문자열 0건**(D-D) | 없음 | P1 | AC-2, C-4 |
| W-2. 기록 CLI와 래퍼 신설 | opal-be-agent | `opal/tools/run-log-tool/run_log_tool.py`, `opal/tools/run-log-tool/run.sh`, `opal/tools/run-log-tool/README.md` | `run_log_tool.py`: @header 작성. `argparse` 서브파서 3종 — `init`(`--task`/`--run-id` 필수, `--format json`), `append`(`surfaces.json` `run-log-tool.append` 표면의 required 8종 + optional 중 T02 관통에 필요한 `--summary`/`--data`/`--worker-run-id`/`--gate-id`/`--stage`/`--task-step`/`--work-item`/`--refs`/`--caused-by-event-id`/`--format json`), `validate-run`(`--task`/`--run-id` 필수, `--format json`). CLI는 인자를 §1.1 payload dict로 조립해 `run_log_core`만 호출한다 — 자체 락 획득(`lock_held=False`). `--format json` 미지정 시 사람이 읽는 텍스트. `run.sh`: `opal/tools/backlog-tool/run.sh`를 그대로 복제해 대상만 `run_log_tool.py`로 바꾼다(`$HOME/.opal/.venv/bin/python`, venv 부재 시 `{"ok":false,"error":"venv_missing",...}` + exit 1, shell script이므로 @header 적용 대상 아님). `README.md`: 3서브명령 사용례 + `RUN_LOG_ERROR_CODES` 카탈로그 | W-1 | P2 | AC-2, C-4 |
| W-3. 상태 도구 개정 — `--run-log-mode` shadow 관통 | opal-be-agent | `opal/tools/state-tool/state_tool.py` | (a) `_run_log_core_dir()` + `_import_run_log_core()` 신설 — 형제 `../run-log-tool` 우선, 없으면 `~/.opal/tools/run-log-tool`을 `sys.path`에 삽입 후 `import run_log_core`(D-C, `_date_js_path()` 293-306 관례 복제). (b) `err()`(268-288)의 템플릿 조회를 `_error_template(code)` 헬퍼로 교체 — `ERROR_CODES` → `run_log_core.RUN_LOG_ERROR_CODES` 순 조회. **`ERROR_CODES` 딕셔너리 리터럴(135-217)은 접촉 금지**(D-A). (c) `_atomic_write_state_json()` 신설(D-F, `memory_tool.py:358-377` 복제) — run-log 경로 전용. (d) `build_parser()`의 `p_init`(3969-3991)에 `--run-log-mode {shadow,active}`·`--channel-id`·`--profiles` 추가. (e) `cmd_init()`(1338-1455)에 run-log 분기 추가 — **미지정이면 기존 경로를 한 줄도 우회하지 않는다**(D-L). 지정 시: `run_log_core.require_absolute()` → `task_lock()` 획득 → `run_id`/`request_id`/`event_id`/`timestamp` 사전 확정 → `schema_version="1.2"` + `run_log` 블록(§1.4 7필드, D-K) `status="pending"` + `pending_events=[compact run.started]`로 **1차 원자 쓰기** → `run_log_core.init(..., lock_held=True)` + `run_log_core.append(..., lock_held=True)` → `pending_events=[]` + `status="active"`로 **2차 원자 쓰기** → 락 해제. 응답에 `run_id`·`run_log`·`status` 추가. `--run-log-mode active`는 `profile_not_found`로 거부(H-4) | W-1 | P2 | AC-2, C-2, C-3, C-4 |
| W-4. 기록 도구 테스트 신설 (state 자산 0건) | opal-be-agent | `opal/tools/run-log-tool/tests/test_run_log_tool.py` | 신규 파일. @header 블록(layer=test, scenarios 배열에 S-3~S-8 기재). `run.sh` subprocess 실호출만 사용 — mock/patch/MagicMock 금지(`opal/tools/backlog-tool/tests/test_backlog_tool.py:29-31` 관례). 표준 라이브러리만. `tempfile` 절대경로 태스크 폴더에서 S-3(init 멱등)·S-4(append)·S-5(validate-run)·S-6(`task_path_not_absolute`)·S-7(`schema_invalid`)·S-8(state 자산 미생성·미참조)을 판정. **테스트 소스와 실행 결과 어디에도 `state.json`을 만들거나 읽지 않는다**(AC-19 / MV-24) | W-2 | P3 | AC-2, C-4 |
| W-5. 상태 도구 관통 테스트 신설 (기존 파일 무접촉) | opal-be-agent | `opal/tools/state-tool/tests/test_state_tool_run_log.py` | 신규 파일. @header 작성. `run.sh`/`cmd_init` 실호출로 S-1(shadow init 관통 — `state.json` 1.2 + `run_log` 7필드 + `status=active` + `pending_events==[]` + 첫 조각에 `run.started` 1줄)과 S-2(`--run-log-mode` 미지정 바이트 동일성 — `git show HEAD:./state_tool.py`를 tmp에 풀어 개정 전/후 산출물을 같은 고정 시각으로 생성해 바이트 비교, `run_log` 키 부재, `run/` 미생성)를 판정. S-9(관통 후 `validate-run` pass)도 여기서 닫는다. **`tests/test_state_tool.py`는 한 줄도 수정하지 않는다** — 동결 단언 보전(D-A·D-B) | W-3 | P3 | AC-2, C-2, C-3 |
| W-6. 배포 배선 | opal-be-agent | `scripts/install-mac.sh` | `install_opal()`의 도구 설치 블록에서 `backlog-tool run.sh 실행 권한` 블록(1349-1354) 바로 뒤에 `run-log-tool` chmod 블록을 같은 형태로 추가한다 — `local run_log_run="$opal_home/tools/run-log-tool/run.sh"; if [[ -f ... ]]; then chmod +x ...; success ...; fi`. `opal/tools/` 디렉터리 복사는 `install_dir`(1285)가 이미 전량 처리하므로 별도 등록은 불필요하다. **install 실행 자체는 하지 않는다 — PM 승인 필요**(TASK C-1, TRD §배포 순서) | W-2 | P3 | C-1 |
| W-7. 문서 동기화 | opal-be-agent | `docs/CONVENTIONS.md`, `docs/PROJECT.md` | `docs/CONVENTIONS.md` §도구 우선 원칙(249-252)의 도구 종수와 전체 목록에 `run-log-tool`을 가산한다(20종 → 21종). `docs/PROJECT.md` §폴더 구조맵의 `opal/tools/` 행 도구 종수(20종 → 21종)를 같은 값으로 맞춘다. 두 곳이 같은 수치를 서로 다르게 말하지 않게 **같은 변경 단위**로 처리한다 | W-2 | P3 | C-1 |
| W-8. 회귀 확인 | opal-be-agent | `opal/tools/state-tool/tests/`, `opal/tools/run-log-tool/tests/` | `python3 -m pytest opal/tools/state-tool/tests/ -q`가 **425 passed, 3 skipped, 111 subtests passed**(2026-09-12 실측 기준선)를 그대로 재현하는지 확인하고, `python3 -m pytest opal/tools/run-log-tool/tests/ -q`가 전건 통과하는지 확인한다. 기존 테스트 파일 수정 0건을 `git diff --stat`으로 함께 보고한다 | W-4, W-5, W-6, W-7 | P4 | C-2, AC-2 |

## 테스트 시나리오 초안 (T2가 RED-first로 작성)

요구 충실도 문턱은 **`real-http` 이상**이며, 전 시나리오를 그보다 강한 **`real-usage`** — 실제 셸에서 `run.sh`
또는 `python3 <tool>.py`를 실행하고 디스크 산출물을 검사 — 로 작성한다. 목·스텁으로 대체하지 않는다.

| id | 설명 | 대상 표면(surface_ref) | required_fidelity | 기대 결과 | RED에서 실제로 무엇이 실패하는가 |
|---|---|---|---|---|---|
| S-1 | shadow 초기화가 상태 1.2와 첫 조각을 함께 만든다 | `state-tool.init.run-log-mode` | real-usage | `state-tool init <abs> --skill oppl --mode agentic --run-log-mode shadow` exit 0. `state.json`의 `schema_version=="1.2"`, `run_log`가 §1.4 7필드(`contract_version=="1.0"`, `mode=="shadow"`, `completion_profile=="cooperative"`, `completion_profile_receipt is None`, `active_run_id` = `run_` 접두, `status=="active"`, `pending_events==[]`)를 갖는다. `run/run-log-{run_id}-0001.jsonl`이 존재하고 정확히 1줄이며, 그 줄이 `event=="run.started"`·`sequence==1`·`actor_sequence==1`·`actor.kind=="tool"`·`provenance.type=="direct"`·`timestamp`가 `Z`로 끝나는 RFC 3339 밀리초다 | `--run-log-mode`가 argparse에 없어 `unrecognized arguments`로 exit 2. 인자 등록만 된 중간 상태에서는 `schema_version`이 `"1.0"`/`"1.1"`로 남고 `run/` 디렉터리가 없어 `assertTrue(segment.exists())`에서 실패한다 |
| S-2 | `--run-log-mode` 미지정 init이 개정 전과 **바이트 동일**하다 (C-3) | `state-tool.init.run-log-mode` | real-usage | 같은 인자·같은 고정 시각으로 (a) `git show HEAD:./state_tool.py`를 tmp에 풀어 실행한 산출물과 (b) 개정본 산출물의 `state.json` **바이트가 동일**하다. 개정본 산출물에 `run_log` 키가 없고 `run/` 디렉터리가 생성되지 않는다 | 분기를 조건부로 두지 않고 `state` dict 구성이나 `schema_version` 판정을 공통 경로에서 바꾸면 바이트 비교가 어긋나 실패한다. 이 시나리오가 없으면 C-3 위반이 조용히 통과한다 |
| S-3 | 실행 디렉터리 초기화가 멱등이다 | `run-log-tool.init` | real-usage | `run.sh init --task <abs> --run-id run_x --format json`을 2회 호출. 1회차 `ok:true`·`created:true`, 2회차 `ok:true`·`created:false`. 조각 파일은 1개이고 2회차 전후 내용이 바이트 동일하다 | `run_log_tool.py`·`run.sh` 부재로 exit 127 또는 `venv_missing`. 구현 중간 상태에서는 2회차가 조각을 덮어써 내용 비교가 실패한다 |
| S-4 | 표준 사건 1건이 append된다 | `run-log-tool.append` | real-usage | S-3 뒤 `append --task <abs> --run-id run_x --request-id req_y --event activity --actor-kind PM --actor-id pm --provenance-type direct --recorded-by-kind PM --summary "..." --format json` exit 0. 응답이 `event_id`(`evt_` 접두)·`sequence`·`actor_sequence`·`segment`·`idempotent_hit:false`를 갖는다. 조각 줄 수가 1 증가하고 **선행 줄이 바이트 불변**(append 전용)이며, 새 줄이 단독 JSON으로 파싱된다 | 서브명령 미구현으로 `invalid choice: 'append'` exit 2. 순번 스캔 미구현이면 `sequence`가 `None`/`1`로 나와 단조 단언에서 실패한다 |
| S-5 | 실행 검증이 관통 경로를 통과한다 (AC-2의 종결 지점) | `run-log-tool.validate-run` | real-usage | S-1의 태스크 폴더에 S-4 방식으로 사건 1건을 더 붙인 뒤 `validate-run --task <abs> --run-id <run_id> --format json` exit 0. `verdict=="pass"`, `segment_count==1`, `event_count==2`, `sequence_gaps==[]`, `violations==[]`, `total_bytes>0` | 서브명령 미구현으로 exit 2. 스캔이 조각을 못 찾으면 `run_log_missing`으로 exit 1, 순번 발급이 틀리면 `sequence_gaps`가 비지 않아 `verdict=="fail"` |
| S-6 | 상대 경로 task path를 추론 없이 거부한다 (§3.2 / MV-27 부분) | `run-log-tool.init`, `.append`, `.validate-run` | real-usage | 세 서브명령 각각에 `--task ./relative`를 주면 `ok:false`·`error.code=="task_path_not_absolute"`·exit≠0. cwd를 바꿔도 결과가 같다 | `require_absolute()` 부재 시 상대 경로가 cwd 기준으로 해석되어 exit 0으로 통과한다 — 정확히 §3.2가 금지하는 동작 |
| S-7 | 폐쇄형 스키마가 정의되지 않은 값을 거부한다 | `run-log-tool.append` | real-usage | (a) `--event not_a_real_event` → `ok:false`·`schema_invalid`, (b) `--data '{"kind":"progress"}'`는 통과하되 §1.1 밖 최상위 키를 만드는 입력은 `schema_invalid`. 두 경우 모두 조각 줄 수가 **증가하지 않는다**(거부 후 부분 쓰기 없음) | `validate_event()` 부재 시 임의 `event` 값이 그대로 기록되어 줄 수가 증가하고 거부 단언이 실패한다 |
| S-8 | 기록 도구 테스트가 상태 자산 없이 통과한다 (AC-19 / MV-24 / D-5) | `run-log-tool.*` 전 표면 | real-usage | (a) `opal/tools/run-log-tool/tests/` 전체 실행 후 tmpdir 어디에도 `state.json`이 생성되지 않는다. (b) `run_log_core.py`·`run_log_tool.py` 소스에 `state_tool` import와 `state.json` 문자열이 0건이다(정적 판정). (c) `state.json`이 없는 빈 절대경로 폴더에서 `init`→`append`→`validate-run` 3연속이 전건 exit 0 | 코어가 `state.json`에서 `active_run_id`를 읽는 구현(TRD D-5 대안 (a))이면 (c)에서 `run_log_missing`/`FileNotFoundError`로 실패한다 |
| S-9 | 기존 state-tool 회귀 0건 (C-2) | — | real-usage | `python3 -m pytest opal/tools/state-tool/tests/ -q`가 **425 passed, 3 skipped, 111 subtests passed**를 재현한다. `git diff --stat`에 `tests/test_state_tool.py`와 `schema/state.schema.json`이 나타나지 않는다 | `ERROR_CODES`에 코드를 직접 등재하면 `test_error_codes_count`·`test_all_28_codes_registered`·`test_s7_...`·S-40 4건이 동시 FAIL. `state.schema.json`에 `"1.2"`를 넣으면 `test_schema_version_enum_allows_1_0_and_1_1`이 FAIL |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. `state.schema.json`의 1.2 미반영이 정적 드리프트로 남는다 | `schema/state.schema.json`의 `schema_version` enum이 `{"1.0","1.1"}`이고 root가 `additionalProperties:false`인 채로 런타임은 1.2 + `run_log`를 낸다 | 정적 자산과 런타임이 어긋난 상태가 T05까지 존속한다. 다만 `cmd_validate`가 이 파일을 참조하지 않으므로(`state_tool.py:2077-2082`) 런타임 판정에는 영향이 없다 | D-B — T02는 파일을 건드리지 않고 드리프트 해소를 **T05로 명시 이관**한다. T05는 `schema_version` enum에 `"1.2"`를, `properties`에 `run_log`를 등재하면서 `test_schema_version_enum_allows_1_0_and_1_1`(`tests/test_state_tool.py:5461-5466`)의 기대 집합도 같은 변경 단위로 옮겨야 한다. 이는 테스트 약화가 아니라 070·106·111·118이 반복한 "등재 태스크가 기대값을 함께 옮긴다" 관례의 재적용이다 — **PM 판단 필요** |
| H-2. `ERROR_CODES` 동결 단언 4건이 신규 코드 등재를 차단한다 | `len(ST.ERROR_CODES)==51`·`EXPECTED_CODES` 일치·README 헤더 수치·S-40 HEAD AST 키 대조 | run-log 오류 코드를 `state_tool.ERROR_CODES`에 넣는 순간 C-2가 즉시 깨진다 | D-A — 별도 테이블 소유 + `err()` 조회만 합성. 구현자가 무심코 `ERROR_CODES`에 한 줄 추가하는 것이 이 태스크의 가장 현실적인 실패 경로이므로, W-3 (b)에 **"딕셔너리 리터럴 접촉 금지"**를 명시하고 S-9가 `git diff --stat`으로 함께 잡는다 |
| H-3. `sys.path` 삽입 import가 배포 레이아웃에서 성립하지 않으면 D-5 인프로세스 호출이 실패한다 | `state-tool init --run-log-mode shadow`가 배포본에서 `ModuleNotFoundError`로 죽는다 | 레포에서는 통과하는데 배포 후 관통이 깨져, 스켈레톤이 있다고 믿는 후속 태스크 전체가 잘못된 전제 위에 선다 | D-C의 형제 우선 해석은 배포 레이아웃(`~/.opal/tools/state-tool/` ↔ `~/.opal/tools/run-log-tool/`)과 레포 레이아웃(`opal/tools/state-tool/` ↔ `opal/tools/run-log-tool/`) 양쪽에서 **같은 상대 관계**로 성립한다 — `_date_js_path()`가 이미 검증한 성질이다. 다만 배포본 실증은 install 실행이 필요하므로 TRD §배포 순서 2항대로 **PM이 install 후 배포본에서 `run-log-tool` 검증 경로를 확인**한다(워커는 install을 수행하지 않는다) |
| H-4. active 초기화(MV-23 / AC-18)의 소유 태스크가 백로그에 없다 | `state-tool.init.run-log-mode`의 `profile_not_found`·`profile_receipt_mismatch`·`cooperative_active_rejected` 3종 분기 | T02가 shadow만 구현하면 이 표면의 active 절반이 미소유로 남는다. 백로그상 이 표면을 `covers`로 선언한 태스크는 T02뿐이며, T07은 그림자 통합, T08은 완료 게이트다 | T02는 `--run-log-mode active`를 **계약상 정확한 `profile_not_found`로 거부**한다(배정 파일이 실제로 배포돼 있지 않으므로 참인 응답이다). active 3종 분기의 소유 태스크 배정은 **PM 판단 필요** — 권고는 T07(그림자 통합 시점에 승격 게이트가 실제로 필요해진다)에 편입하거나 T07·T08 사이에 별도 태스크를 추가하는 것이다 |

## Release and recovery

- **적용 순서**: TRD §배포 순서가 요구하는 "기록 코어·기록 CLI 설치·검증 후 상태 도구 활성화"를 실행 그룹으로
  옮긴 것이 P1→P4다. P1(W-1 코어) → P2(W-2 CLI·래퍼, W-3 상태 도구 개정 — 변경 대상이 겹치지 않아 병렬) →
  P3(W-4·W-5 테스트, W-6 배포 배선, W-7 문서) → P4(W-8 회귀 확인).
- **설치·배포**: `./scripts/install-mac.sh` 실행은 **PM 승인 필요**이며 워커가 스스로 수행하지 않는다(TASK C-1).
  배포 후 확인 항목은 두 가지다 — (a) `~/.opal/tools/run-log-tool/run.sh`가 실행 가능하고 `init`이 응답한다,
  (b) 배포본 `state-tool init --run-log-mode shadow`가 `ModuleNotFoundError` 없이 관통한다(H-3).
- **검증 범위**: 결정론 — S-1~S-8(신규 계약, 전건 `real-usage`). 회귀 — S-9(기존 state-tool 425/3/111 기준선,
  기존 테스트 파일 수정 0건). 실제 연동 — 배포본 관통은 install 이후 PM이 확인한다.
- **실측 경계**: 없음. 이 태스크에 시간·품질 수치 목표가 없다.
- **실패 시**: P1~P3은 전부 신규 파일 추가이거나(W-1·W-2·W-4·W-5) 조건부 분기 추가이므로(W-3),
  되돌림은 신규 파일 삭제 + `state_tool.py` revert 1건이다. `--run-log-mode` 미지정 경로를 건드리지 않았으므로
  (D-L / S-2) 되돌리지 않은 채로도 기존 태스크는 영향을 받지 않는다. 배포 후 실패면 install 재실행으로
  이전 소스 상태를 다시 배포한다.

## 근거 인용

이 PLAN의 모든 비자명 조항이 실제로 읽은 파일의 행 번호 또는 `문서 §절`을 근거로 갖는다. 아래는 코드 근거 목록이며,
계약 근거는 각 결정 행에 인라인으로 달았다. 프로젝트 구조 파악에는 `docs/PROJECT.md` §폴더 구조맵과
`docs/CONVENTIONS.md` §도구 우선 원칙(code-scan 대상 목록과 같은 축의 도구 인벤토리)을 사용했다.

| 근거 | 이 PLAN에서의 쓰임 |
|---|---|
| `opal/tools/state-tool/state_tool.py:135-217` (`ERROR_CODES`) | D-A — 접촉 금지 대상의 물리적 경계 |
| `opal/tools/state-tool/state_tool.py:218-223` (`WARNING_CODES` 분리 주석) | D-A — 같은 이유의 선행 분리 선례 |
| `opal/tools/state-tool/state_tool.py:264-288` (`ok`/`err`) | D-A, W-1 — 응답 봉투 패턴과 `_error_template` 교체 지점 |
| `opal/tools/state-tool/state_tool.py:293-306` (`_date_js_path`) | D-C — 형제 배치 우선 경로 해석 관례 |
| `opal/tools/state-tool/state_tool.py:308-336` (`get_kst_datetime`) | D-G — 상태 파일 시각은 종전 경로 유지 |
| `opal/tools/state-tool/state_tool.py:363-368` (`save_state_json`) | D-F — 비원자 쓰기, run-log 경로에서만 우회 |
| `opal/tools/state-tool/state_tool.py:1338-1455` (`cmd_init`) | W-3 (e) — 분기 삽입 지점 |
| `opal/tools/state-tool/state_tool.py:1402-1405` (schema_version 판정) | D-L — 미지정 경로 불변성의 실제 지점 |
| `opal/tools/state-tool/state_tool.py:1423-1425` (`--worktree` 조건부 영속화) | D-L — "미지정 시 키 자체를 만들지 않는다" 선례 |
| `opal/tools/state-tool/state_tool.py:2068-2082` (`cmd_validate`) | D-B — 런타임이 `state.schema.json`을 참조하지 않는다는 근거 |
| `opal/tools/state-tool/state_tool.py:3969-3991` (`p_init` 파서) | W-3 (d) — 인자 등록 지점 |
| `opal/tools/state-tool/schema/state.schema.json:16`, `:47-52` | D-B, H-1 — `additionalProperties:false`와 `schema_version` enum |
| `opal/tools/state-tool/tests/test_state_tool.py:2582-2591`, `:2622-2638`, `:5461-5466`, `:9125-9159` | D-A, D-B, H-1, H-2 — 동결 단언 4+1건의 정확한 위치 |
| `opal/tools/backlog-tool/backlog_tool.py:6` (@header) | D-A — "state-tool 패턴 복제, ERROR_CODES SSOT" 관례 선언 |
| `opal/tools/backlog-tool/backlog_tool.py:167-197` (fcntl 락) | D-J, W-1 — 배타 락 선례 |
| `opal/tools/backlog-tool/run.sh:1-12` | W-2 — `run.sh` 래퍼 패턴 |
| `opal/tools/backlog-tool/tests/test_backlog_tool.py:29-31` | W-4 — subprocess 실호출·mock 금지 테스트 관례 |
| `opal/tools/memory-tool/memory_tool.py:358-377` (`atomic_write_json`) | D-F, W-3 (c) — tmp→fsync→`os.replace` 원자 쓰기 선례 |
| `scripts/install-mac.sh:1284-1285`, `:1349-1354` | W-6 — `install_dir` 전량 복사와 chmod 블록 삽입 지점 |
| `docs/CONVENTIONS.md:249-252` (도구 우선 원칙), `:219-225` (@header 규칙) | W-7, W-1/W-2 — 도구 인벤토리 갱신과 @header 의무 |
| `docs/PROJECT.md` §폴더 구조맵 `opal/tools/` 행 | W-7 — 같은 수치를 갖는 두 번째 지점 |
| 실측 기준선 (2026-09-12, `python3 -m pytest opal/tools/state-tool/tests/ -q`) | S-9, W-8 — 425 passed, 3 skipped, 111 subtests passed |
