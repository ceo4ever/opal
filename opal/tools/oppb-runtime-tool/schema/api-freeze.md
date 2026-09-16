# OPPB Runtime Tool — G2 API 동결 기록

> PLAN **D3**이 정의한 G2 완료조건의 산출물이다. 이 문서와 같은 디렉토리의 스키마 4종이
> **G3 착수의 유일한 입력 계약**이다. G3 진행 중 이 계약을 바꾸려면 구현을 먼저 고치지 말고
> W-11로 돌아와 아래 §재동결 절차를 수행한다(PLAN §Risks **H-3**).

## 1. 동결 좌표

| 항목 | 값 |
|---|---|
| 동결 시각 (UTC) | `2026-09-15T12:06:50Z` (재동결 #4 — additive 확장 #2 + `profile` enum 정정) |
| 동결 기준 commit | `0862d1a14b4de867934d55c1d57e2e30aabb0d86` (`0862d1a`) — 확장 자체는 이 시점 미커밋이며 W-44 커밋에 들어간다 |
| 브랜치 / worktree | `.opal-worktrees/task_132` |
| 상류 main 대조 | `git log --oneline main ^HEAD` 결과 **7건** — 재동결 #3 이후 main이 앞서갔다. 7건 모두 `oppb-runtime-tool` 밖의 상류 작업이고, 이번 재동결은 병합하지 않은 이 브랜치 상태를 기준으로 한다. 병합 시 §2의 sha256을 재확인한다 |
| 동결 대상 구현 | `controller.py` · `supervisor.py` · `evidence.py` · `oppb_runtime_tool.py` (동결 시점 기준 아직 미커밋 — G2 체크포인트 커밋에 함께 들어간다) |

## 2. 파일별 sha256

| 파일 | sha256 | bytes |
|---|---|---|
| `oppb-state.schema.json` | `c0532009e4261a3101ce8ebef63271789ee03d2585018f337952169d6eab1b38` | 24319 |
| `oppb-event.schema.json` | `8a78a0c70f04dcea7334d42a20005f9e3ab547a8a4787ecc4c621af91e66fd98` | 5321 |
| `oppb-command.schema.json` | `f3fab919b75d3c8c57f474195433a340de13d03abee2874e00d4f5edad42b79e` | 12791 |
| `oppb-evidence.schema.json` | `2bc84ff52e1860fd917204538bf2243ae2c4ac76f0316eb7f965cfe671a91c22` | 5135 |

재확인 명령 (W-18이 이 값의 무변경을 재확인한다):

```bash
cd <repo-root>/opal/tools/oppb-runtime-tool/schema
shasum -a 256 oppb-state.schema.json oppb-event.schema.json \
              oppb-command.schema.json oppb-evidence.schema.json
```

## 3. 동결 범위

| 스키마 | 동결하는 계약 |
|---|---|
| `oppb-state.schema.json` | **G2가 소유하는 run root 문서** — `workgraph.json`(루트) + `acceptance.json` · `execution-packet.json` · `run.json` · `supervisor.json` · `attempt-spec.json` · `result.json`(`$defs`). 미니 태스크 상태 10종(최초 동결 8종 + 재검증 2종 — §9), dispatch 역할 3종, lease 4축, 예산 차감 축, revision lock 규율 |
| `oppb-event.schema.json` | `events.jsonl` 한 줄. 이벤트 이름 5종 폐쇄 집합과 이벤트별 필드 |
| `oppb-command.schema.json` | **G2가 소유하는** CLI 명령 7종 · 플래그 6종 · 서브커맨드 4종 · 오류 코드 52종 · 응답 봉투 · exit code 3종 · `workgraph load --spec` 입력 형식 |
| `oppb-evidence.schema.json` | `evidence/<scope>/<evidence_id>.json` 필수 필드·형식과 4단 거부 조건, `evidence submit`·`task accept` 응답 필드 |

**동결 범위 = G2 표면.** 이 동결이 거는 것은 Controller·Supervisor·Evidence의
state·event·command·evidence 계약뿐이다. **CLI 전체 표면이나 run root 전체 파일 목록이 아니다.**
G3·G4가 자기 서브커맨드·플래그·오류 코드·run root 문서를 추가하는 것은 **이 동결의 위반이 아니며
재동결 트리거도 아니다.** 스키마가 구현보다 좁은 상태는 의도된 것이다.

**동결 범위 밖 — 다른 그룹 소유**

| 표면 | 소유 W | 문서화 소유자 |
|---|---|---|
| `lease` 명령 + `--attempt`·`--candidate` 등 · `leases.json` | W-12 | `lease.py` @header + README |
| `probe` 명령 + `--commands`·`--observation` 등 · `environment-discovery.json` | W-13 | `probe.py` @header + README |
| `checkpoint` 명령 + `--task`·`--record-baseline` 등 · `checkpoint/` | W-14 | `checkpoint.py` @header + README |
| `cache` 명령 + `--dest`·`--regenerate` 등 · cache root 레이아웃 | W-15 | `cache.py` @header + README |
| `recover` 명령 + `--pid`·`--violation` 등 · `recovery/` | W-16 | `recovery.py` @header + README |

각 모듈의 @header가 이미 자기 표면을 기술한다. **이 문서와 스키마 4종은 그것을 중복 기술하지 않는다.**

**동결 범위 밖 — 의도적 제외**

- `attempts/<task>/<attempt>/attempt.attempt.json` (attempt record). 이 파일의 필드 집합은
  `opal-agent`의 `classify_attempt()` 입력 계약이고 소유자도 `opal-agent`다. OPPB Supervisor는
  같은 모양을 채워 넣을 뿐이므로 G2가 동결할 대상이 아니다.
- 내부 함수·클래스 시그니처. PLAN **H-6**에 따라 테스트도 스키마도 공개 CLI와 run root 파일
  계약 수준에서만 계약을 건다.

## 4. 이 스키마의 지위

- **문서이자 동결 대상이지 런타임 검증기가 아니다.** `oppb-runtime-tool`은 표준 라이브러리
  전용이고 `jsonschema`를 import하지 않는다. 실제 집행은 `evidence._validate_schema` 등
  구현 코드가 한다.
- 스키마는 **실측에서 뽑았다.** 아래 §5의 실행 결과가 근거이며, 현재 구현이 만들지 않는
  필드는 넣지 않았다. G3·G4가 추가할 필드를 미리 선언하지 않는다.
- 형식 준거는 `opal/tools/state-tool/schema/state.schema.json`(JSON Schema draft-07).

## 5. D3 완료조건 — 동결 시점 확인 결과

D3은 4항 전부 green일 때만 G2가 끝난 것으로 본다. 전부 이 문서 작성 시점에 재현했다.

| # | 조건 | 명령 | 결과 |
|---|---|---|---|
| 1 | 스키마 4종 존재 + sha256 고정 | 위 §2 | **충족** — 4파일 생성, sha256 기록 |
| 2 | `state.json`↔`workgraph.json` 상호 직접 쓰기 0 | `python3 -m pytest opal/tools/oppb-runtime-tool/tests/test_controller.py -q` | **5 passed** |
| 3 | 상한 포화 시 첫 slot을 Verifier에 배정 + 비정상 종료·재시작에서 재부착/수확 후 자동 tick 재개 | `python3 -m pytest opal/tools/oppb-runtime-tool/tests/test_supervisor.py -q` | **5 passed** |
| 4 | schema·code head·scope hash 불일치 evidence를 색인 전 거부 | `python3 -m pytest opal/tools/oppb-runtime-tool/tests/test_evidence.py -q` | **7 passed** |
| + | 진입 가드(run root·cache root 미추적 보장) | `python3 -m pytest opal/tools/oppb-runtime-tool/tests/test_oppb_init.py -q` | **18 passed** |
| + | **W-2 OPPL 회귀 — 기존 Pilot 무변경** | `python3 -m pytest opal/tools/opal-agent/tests/ opal/tools/state-tool/tests/ -q` | **546 passed, 3 skipped, 111 subtests passed** |

### 5.1 스키마 정합 검증

스키마가 구현·실산출물과 어긋나지 않음을 두 방향으로 확인했다.

1. **코드 대조** — 스키마의 폐쇄 집합을 구현 심볼에서 직접 읽어 비교했다. 전부 일치:
   `TASK_STATES`(8) · `ROLES`(3) · `LEASE_AXES`(4) · `COMMANDS`(7) · `DISPATCH` 키(7) ·
   `FLAGS`(6) · `ERROR_CODES`(52) · `evidence._REQUIRED_FIELD_TYPES`(8) ·
   `supervisor.append_event` 발행 이벤트 이름(5).
2. **실산출물 대조** — 격리된 임시 git 저장소에서 `init` → `workgraph load` → `start` →
   `evidence submit` → `task accept`를 실제로 완주시켜 나온 run root 산출물 전수를
   스키마로 검증했다. 4개 스키마 모두 draft-07 유효, 문서 **30건 전부 통과**
   (`workgraph.json` · `acceptance.json` · `run.json` · `supervisor.json` ·
   attempt 4건의 packet/spec/result 12개 · `events.jsonl` 11줄 · evidence 1건),
   명령 표면 8종 통과 + 음성 사례(필수 플래그 누락, 미지 명령) 거부 확인.

> 검증에 쓴 `jsonschema`는 OPAL `.venv`에 이미 있는 것을 **1회성 확인 용도로만** 썼다.
> 도구 런타임에 의존성을 추가하지 않았고 구현은 표준 라이브러리 전용 그대로다.

### 5.2 H-7 재실측 — `opal-agent` 공개 심볼

PLAN **H-7**이 W-11 시점에 요구한 재실측이다. 과거 실측치로 확정하지 않는다.

- `opal/tools/opal-agent/opal_agent.py` — **1935줄**, sha256
  `cedcfa5a0456784d935df615548ee609650586b95399da9a67467b45132753e7`
- `@header.exports` **17종**:
  `call_agent` · `resolve_session_event` · `analyze_stream` · `reconcile_attempts` ·
  `classify_attempt` · `load_attempt_record` · `AgentConfig` · `AgentResult` ·
  `StreamVerdict` · `PROVIDERS` · `EXIT_CLASSES` · `EPILOGUE_ALLOWLIST` ·
  `ATTEMPT_DISPOSITIONS` · `SUBCOMMANDS` · `OpalAgentError` · `ClaudeNotFoundError` ·
  `OpalAgentTimeout`
- **상류 변경 없음.** W-38 조사 중 관측된 1461줄 → 1935줄 이동은 이미 이 브랜치 HEAD에
  반영돼 있고, 동결 시점에 main이 앞서간 커밋은 0건이다.

## 6. 재동결 절차 (H-3 경로)

**재동결 트리거는 하나뿐이다 — Controller·Supervisor·Evidence의 state/event/command/evidence 계약
자체가 바뀔 때.** 구체적으로 `workgraph.json`·`acceptance.json`·`execution-packet.json`·
`result.json`·`run.json`·`supervisor.json`·`evidence/`의 필드·불변식이 바뀌거나, 이벤트 5종,
G2 명령 7종의 인자·응답·오류 계약이 바뀔 때다.

**트리거가 아닌 것:** 다른 그룹이 서브커맨드·플래그·오류 코드를 추가하는 것, run root에 그 그룹
소유 문서를 추가하는 것. 이 경우 스키마를 고치지 말고 해당 모듈 @header와 README에만 기술한다.

트리거에 해당하면 **G3에서 즉석으로 고치지 않는다.**

1. **중단** — 변경이 필요한 W를 중단하고 사유(어느 스키마의 어느 필드가, 왜 부족한지)를 기록한다.
2. **W-11 재진입** — PM에 W-11 재진입을 요청한다. 구현 변경이 선행하면 그 구현도 W-11 범위로 들어온다.
3. **실측 우선** — 스키마를 상상으로 고치지 않는다. 구현을 먼저 확정하고 §5.1의 두 방향
   대조(코드 심볼 · 실제 run 산출물)를 다시 통과시킨다.
4. **sha256 갱신** — 바뀐 스키마의 sha256을 §2 표에 갱신하고, §7 이력에 재동결 1행을 추가한다.
   동결 시각·기준 commit도 함께 갱신한다.
5. **D3 재확인** — §5의 테스트 4종 + W-2 OPPL 회귀를 다시 돌려 전부 green임을 기록한다.
6. **G3 재개** — 위가 끝난 뒤에만 중단했던 W를 재개한다. W-18은 **재동결 후의 sha256**을
   기준으로 무변경을 재확인한다.

구현이 스키마와 어긋난 경우의 기본 방향은 반대다 — **스키마를 실측에 맞춘다.** 구현이
틀렸다고 판단되면 임의로 고치지 말고 블로커로 올린다.

## 7. 동결 이력

| # | 시각 (UTC) | 기준 commit | 사유 |
|---|---|---|---|
| 1 | 2026-09-14T09:58:42Z | `612db93` | 최초 동결 — W-11 / PLAN D3 |
| 2 | 2026-09-15T01:38:25Z | `9d7dbc6` | **범위 한정 재동결** — W-11 재진입 / PLAN H-3. G3 워커 5명(W-12~W-16)이 동결된 `command_name` enum이 확장된 CLI 표면을 기술하지 못한다고 보고. enum 값을 늘리지 않고 `command_name`·`flag_name`·`error_code`·run root 문서 목록의 description을 **"G2가 소유하는 집합"**으로 한정했다. 최초 동결이 G2 시점 실측을 전체 표면으로 일반화한 오류를 정정한 것이다. 변경은 description 전용 — enum 값·필수 필드·구조 변경 0. |
| 3 | 2026-09-15T07:31:12Z | `0862d1a` | **additive 확장 재동결** — W-41 / H-3 예외. **소유자 명시 승인**으로 동결 이후 최초로 `oppb-state.schema.json`에 필드를 추가했다. 추가 2개뿐: `properties.execution_contract`(문자열, run root 상대 경로, 기본 `"INTENT.md"`) · `$defs.mini_task.properties.profile`(enum `fast`·`full`). 근거는 §8. 삭제·수정 0 — 기계 증명으로 확인했다. `oppb-event`·`oppb-command`·`oppb-evidence` 3종은 무변경이라 sha256이 그대로다. |
| 4 | 2026-09-15T12:06:50Z | `0862d1a` | **additive 확장 #2 + enum 정정 재동결** — W-44 / H-3 예외. **소유자 명시 승인**으로 재검증 그래프(제안서 §9.1)를 동결 스키마에 흡수했다. 추가 7개: 루트 `properties.contracts` · `$defs.mini_task.properties`의 `consumes_contracts`·`produces_contract`·`acceptance_scenarios`·`contract_tests` · `$defs.task_state` enum에 `needs_revalidation`·`repair`. 지원 `$defs` 4종(`contract_declaration`·`contract_ref`·`check_command`·`check_entry`) 신설. **정정 1건**: `profile` enum `["fast","full"]` → `["fast","standard","critical"]`(제안서 §8 실측). 근거는 §9. `oppb-event`·`oppb-command`·`oppb-evidence` 3종은 무변경이라 sha256이 그대로다. |

## 8. 재동결 #3 — additive 확장 근거 (H-3 예외)

### 8.1 왜 열었는가

동결 이후 표준 경로는 §6이고, 기본 방향은 "스키마를 고치지 말고 W-11로 돌아간다"였다.
이번은 그 경로를 **소유자 승인 아래 additive 확장으로 축약한 예외**다. 사유는 두 가지다.

1. **RED 계약이 요구하는 필드가 스키마에 없다.**
   `tests/test_product_flow.py::test_intent_md_is_the_single_execution_contract`는
   `workgraph.json`의 `execution_contract == "INTENT.md"`를 요구하고(수용기준 2),
   `test_fast_mini_task_artifacts_are_packet_result_evidence_only`는 미니 태스크의
   `profile == "fast"` 식별을 요구한다(수용기준 8).
2. **두 대상 모두 `additionalProperties: false`다.** 스키마 루트와 `$defs.mini_task`가
   닫힌 집합이라, 필드를 추가하지 않고는 RED 계약을 충족하는 문서가 스키마상 **유효할 수 없다.**
   우회로가 없다 — 이것이 §6이 정의한 "필드·불변식이 바뀔 때"의 재동결 트리거에 정확히 해당한다.

### 8.2 무엇을 추가했는가 — 이것뿐이다

| 위치 | 필드 | 형식 | required | 기본값 |
|---|---|---|---|---|
| 스키마 루트 `properties` | `execution_contract` | `string`, `minLength: 1` | **아니오**(optional) | `controller.DEFAULT_EXECUTION_CONTRACT` = `"INTENT.md"` |
| `$defs.mini_task.properties` | `profile` | `enum ["fast", "full"]` | **아니오**(optional) | `controller.DEFAULT_TASK_PROFILE` = `"full"` |

둘 다 **optional로 뒀다.** 기존 `required` 배열에 넣지 않았으므로 이 필드가 없는 기존
`workgraph.json`도 계속 유효하다 — 하위 호환이 깨지지 않는다.

### 8.3 additive임을 기계 증명했다

확장 전후 JSON을 로드해 전 노드를 경로로 평탄화하고 대조했다. 결과:

- 기존 노드 경로 **546개 전부 보존**, 삭제 0.
- 신규 경로 **11개**뿐 — `$.properties.execution_contract`(+하위 4) ·
  `$.$defs.mini_task.properties.profile`(+하위 4, enum 원소 2 포함).
- 기존 `dict` 키 집합은 전부 **부분집합으로 보존**. 키가 추가된 dict는 2곳뿐:
  `$.properties`(+`execution_contract`) · `$.$defs.mini_task.properties`(+`profile`).
- **기존 enum 값 16개 전부 생존**, 순서·내용 변경 0(after 18 = 16 + 신규 `fast`·`full`).
- **`required` 블록 16개 전부 유지**, 원소 축소 0.
- 기존 scalar(=모든 `description`·`type`·`const`·`pattern`) **변경 0건**.

### 8.4 scope hash 입력 불변

두 필드는 **scope hash 계산 입력이 아니다.** `controller.compute_scope_hash`는
`{"domain": SCOPE_HASH_DOMAIN, "lease": normalize_lease(lease)}`만 직렬화하고,
`normalize_lease`는 `LEASE_AXES` 4축만 읽는다. `profile`은 미니 태스크 최상위,
`execution_contract`는 workgraph 최상위라 어느 쪽도 `contract.lease` 안에 들어가지 않는다.
`SCOPE_HASH_DOMAIN`·`LEASE_AXES`·`normalize_lease`·`compute_scope_hash`의 **본문을 건드리지 않았다.**

확장 전 `controller.py`(`git show HEAD:`)와 확장 후를 동시에 로드해 대조한 결과,
lease 5종의 scope hash가 **전부 동일**했고, 같은 lease에 `profile`·`execution_contract`를
어떻게 바꿔 넣어도 `scope_hash`는 확장 전 값
`363320d0aa676395c1f856f74ebbc0595083735fa5d47d8d7e206f22d6037b5c`로 고정이었다.

### 8.5 §5 D3 완료조건 재확인

| 테스트 | 결과 |
|---|---|
| `tests/` 전체 | **83 passed** / 7 failed + 12 errors — 실패는 전부 `test_revalidation.py`(W-26) · `test_product_flow.py`(W-42)의 **기존 RED**다 |
| 확장 전 baseline 대조 | 같은 두 파일을 확장 전 코드로 돌린 결과도 **7 failed, 12 errors** — 실패 건수 증가 0 |
| `test_controller.py` · `test_lease.py` · `test_checkpoint.py` · `test_recovery.py` (scope hash 의존) | 전부 green |

### 8.6 이 예외의 범위

이번 확장이 연 것은 **이 두 필드뿐**이다. §6의 재동결 절차는 그대로 살아 있고,
`oppb-state.schema.json`의 나머지와 `oppb-event`·`oppb-command`·`oppb-evidence` 3종은
여전히 동결 상태다. 다음 변경도 소유자 승인 없이 곧바로 고치지 말고 §6을 따른다.

## 9. 재동결 #4 — additive 확장 #2 + `profile` enum 정정 근거 (H-3 예외)

### 9.1 왜 열었는가 — 한 경로에 두 문서 계약이 걸려 있었다

`<run_root>/workgraph.json` **하나에 호환되지 않는 두 계약**이 동시에 주장되고 있었다.

- 동결 스키마 · `controller.py` · `verifier_adapter.py` · `tests/test_product_flow.py` —
  최상위 `mini_tasks[]`, 미니 태스크 상태 8종.
- `tests/test_revalidation.py` — `{"contracts": [...], "tasks": [...]}`,
  `consumes_contracts` · `produces_contract`, 재검증 상태 어휘(`needs_revalidation` · `repair`).

실주행에서 `workgraph load`가 쓰는 것은 `mini_tasks`뿐이라, 이 상태로는 **수용기준 26(AC-12)의
재검증 경로가 실제 run root 문서 위에서 성립하지 않는다.** `checkpoint.py`도 같은 함정을 밟았다가
W-43에서 정정했다. **소유자가 "재검증 그래프를 동결 스키마에 흡수" 방향을 승인**했고, W-44는 그중
스키마·Controller 쪽을 수행한다.

### 9.2 무엇을 추가했는가 — 이것뿐이다 (전부 optional)

| 위치 | 필드 | 형식 | required |
|---|---|---|---|
| 스키마 루트 `properties` | `contracts` | `array<contract_declaration>` = `[{id, revision, owner}]` | **아니오** |
| `$defs.mini_task.properties` | `consumes_contracts` | `array<string>` — 소비 계약 id | **아니오** |
| `$defs.mini_task.properties` | `produces_contract` | `contract_ref`(`{id, revision}`) 또는 `null` | **아니오** |
| `$defs.mini_task.properties` | `acceptance_scenarios` | `array<check_entry>` = `[{id, command}]` | **아니오** |
| `$defs.mini_task.properties` | `contract_tests` | `array<check_entry>` | **아니오** |
| `$defs.task_state` enum | `needs_revalidation` · `repair` | enum 값 2개 추가 | — |

지원 `$defs` 4종을 신설했다: `contract_declaration` · `contract_ref` · `check_entry` ·
`check_command`. **`check_command`는 상상이 아니라 실측이다** — 정규형은 기존 `$defs.command`와
같은 argv 리스트지만, `revalidation._run_command`가 `shlex.split`으로 쪼개는 **단일 문자열** 형식도
실제로 받으므로(`tests/test_revalidation.py::_script_cmd`가 만드는 값이 그 형식이다) `oneOf`로 둘 다
허용한다. 두 형식 모두 shell을 거치지 않는다.

신규 필드는 **전부 optional이다.** 기존 `required` 배열에 원소를 넣지 않았으므로 이 필드가 하나도
없는 기존 `workgraph.json`도 계속 유효하다 — jsonschema 실측으로 확인했다(§9.5).

### 9.3 `profile` enum 정정 — 이건 추가가 아니라 값 교체다

W-41이 `profile` enum을 `["fast", "full"]`로 넣었다. **`"full"`은 설계에 없는 값이다.**
제안서 **§8 「미니 태스크 profile」**의 실측 표는 3종이다:

| Profile | RUN | PROVE | ACCEPT | 추가 에이전트 |
|---|---|---|---|---|
| Fast | 바로 구현 | 직접 테스트 | scope·기본 checkpoint 검증 | 없음이 기본 |
| Standard | capability micro design | 수직 수용·영향 테스트 | 외부 계약·컨벤션 | 필요 시 FE·BE·DB Executor |
| Critical | 보존할 설계 작성 | 심층 시나리오 | 독립 계약·보안·컨벤션 | Design Evaluator·Security Verifier |

즉 `"full"`은 제안서 어디에도 없고 테스트 작성자가 만든 값이다. 그래서
`["fast", "standard", "critical"]`로 정정하고 `controller.TASK_PROFILES` ·
`DEFAULT_TASK_PROFILE`(`"full"` → `"standard"`)을 함께 맞췄다.

**이것이 동결 위반이 아닌 근거:** `profile` 필드 자체가 **이번 태스크의 재동결 #3(W-41)이 처음
넣은 필드**다. 최초 동결본(재동결 #1·#2)의 `oppb-state.schema.json`에는 `profile`이 존재하지 않는다
(`git show HEAD:…/oppb-state.schema.json`에 `"profile"` **0건**). 따라서 **원래 동결본 기준으로는
이번 변경도 여전히 순수 추가**이며, 사라진 `"full"`은 동결 계약에 한 번도 들어간 적 없는 값이다.
제안서 §8을 어긴 미커밋 값을 커밋 전에 바로잡은 것이다.

### 9.4 additive임을 기계 증명했다

확장 전(W-41 상태) · 확장 후 JSON을 전 노드 경로로 평탄화해 5항목을 **각각 독립 검사**했다.

| # | 항목 | 결과 |
|---|---|---|
| (a) | 경로 삭제 | 확장 전 **557** → 확장 후 **643**, **삭제 0**, 신규 86 |
| (b) | 기존 dict 키집합 ⊆ 신규 | dict 노드 186개 검사, **부분집합 위반 0**. 키가 추가된 dict는 3곳뿐 — `$.properties`(+`contracts`) · `$.$defs`(+지원 `$defs` 4종) · `$.$defs.mini_task.properties`(+재검증 4필드) |
| (c) | 기존 enum 값 생존 | enum 블록 5개 중 4개는 값·순서 그대로. `task_state`는 8종 전부 보존 + 2종 추가(8→10). **유일 예외는 `profile`의 `"full"`** — §9.3의 승인된 정정 대상이다. profile 제외 시 사라진 값 **0** |
| (d) | required 축소 | `required` 블록 16개 **전부 유지, 원소 축소 0, 원소 증가 0**. 신규 블록 3개는 전부 신설 `$defs`(`contract_declaration`·`contract_ref`·`check_entry`) 소속 |
| (e) | 기존 scalar 변경 | scalar 노드 334개 중 변경 **3건, 전부 `profile` 정정분**(`enum[1]` · `description` · `default`). **정정 외 미승인 변경 0건** — 기존 `description` 한 줄도 건드리지 않았다(`task_state.description`은 확장 후에도 정확하므로 원문 그대로 뒀다) |

### 9.5 scope hash 입력 불변

신규 필드는 **전부 `contract.lease` 밖**이다 — `contracts`는 workgraph 최상위,
재검증 4필드는 미니 태스크 최상위다. `SCOPE_HASH_DOMAIN` · `LEASE_AXES` ·
`normalize_lease` · `compute_scope_hash`의 **본문을 건드리지 않았다**(확장 전후 상수 동일 실측).

확장 전 `controller.py`와 확장 후를 동시에 로드해 lease 5종(빈 lease · tracked만 · 4축 전부 ·
순서·중복 뒤섞음 · 계약축 다수)의 scope hash를 대조한 결과 **5종 전부 동일**했다. 같은 lease에
`profile`을 `fast`/`critical`로 바꾸거나 재검증 4필드를 전부 채워 넣어도 `scope_hash`는
`fb5b732f69abdafcf569dd73e339c1dc1d0d679333602b8016ffd1cd2af70bb6`로 고정이었다.

### 9.6 스키마 정합 — §5.1과 같은 두 방향

1. **코드 대조** — `controller.TASK_STATES`(10) · `TASK_PROFILES`(3, `DEFAULT="standard"`) ·
   `LEASE_AXES`(4, 무변경)를 구현 심볼에서 읽어 스키마 enum과 대조했고 전부 일치했다.
2. **실산출물 대조** — `build_workgraph`가 실제로 만든 문서를 `jsonschema` draft-07으로 검증했다.
   (ㄱ) 신규 필드를 전부 채운 문서 **통과**, (ㄴ) 신규 필드가 하나도 없는 동결 당시 모양 문서
   **통과**(하위 호환 확인), (ㄷ) 음성 사례 `profile: "full"` **거부**. 스키마 자체도 draft-07 유효.

> §5.1과 같이 `jsonschema`는 OPAL `.venv`의 것을 1회성 확인에만 썼다. 도구 런타임 의존성은
> 표준 라이브러리 전용 그대로다.

### 9.7 회귀 — baseline 대비

| 시점 | 결과 |
|---|---|
| W-44 착수 전 baseline | **1 failed, 116 passed** (유일 실패 `test_product_flow.py::test_fast_mini_task_artifacts_are_packet_result_evidence_only`, W-44 소유 아님) |
| W-44 확장 후 | **109 passed, 8 errors** — 8건 전부 `test_product_flow.py` 한 파일이고 **원인도 하나뿐**이다: 해당 픽스처가 아직 `"profile": "full"`(:398)을 선언해 `workgraph load`가 `spec_invalid`로 거부한다 |

즉 §9.3의 정정이 드러낸 **같은 결함의 잔여 지점 1곳**이며, 그 파일은 **W-45 소유**라 W-44가 고치지
않는다. W-45가 `"full"` → `"standard"`(또는 `"fast"`)로 맞추면 해소된다. `test_revalidation.py`를
포함한 나머지 스위트는 전부 green이고, scope hash 의존 스위트(`test_controller.py` ·
`test_lease.py` · `test_checkpoint.py` · `test_recovery.py`)도 전부 green이다.

### 9.8 이 예외의 범위

이번 확장이 연 것은 **§9.2의 7개 필드·enum 값과 §9.3의 `profile` 정정뿐**이다. §6의 재동결 절차는
그대로 살아 있고, `oppb-state.schema.json`의 나머지와 `oppb-event` · `oppb-command` ·
`oppb-evidence` 3종은 여전히 동결 상태다. 다음 변경도 소유자 승인 없이 곧바로 고치지 말고 §6을 따른다.
