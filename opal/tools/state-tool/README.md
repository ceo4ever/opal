# state-tool

> OPAL 파이프라인 현황판 JSON SSOT 관리 CLI
> 소스: `opal/tools/state-tool/` | 배포: `~/.opal/tools/state-tool/`
> 설계 근거: `tasks/134-260501-opp-pipeline-state-tool/PLAN.md` §2.1~§2.20

## 개요

`state-tool`은 STATE.md의 파이프라인 현황판 표를 `state.json`(단일 진실 공급원)으로 분리하고, 10개 서브 명령으로만 갱신 가능하게 만들어 LLM의 절차 우회/오갱신을 차단한다.

> **070: task-step 키 주소 체계**. 행 주소를 불안정한 순번(`--row N`)이 아니라 `references/pipeline.json`에 선언된 task-step key(`plan.pm_gate` 형식)로 지정할 수 있다. `advance`/`mark`/`block`/`add-row`는 `--task-step <key>` / `--task-step-id <n>` / `--row <n>`(deprecated 별칭, 하위호환) 중 정확히 하나를 받는다. 미지정 시 `task_step_addr_required`, 2개 이상 동시 지정 시 `task_step_addr_conflict`, key 미매칭 시 `task_step_not_found`(candidates 포함).

- STATE.md는 **의사결정 로그·블로커·자유 기재를 담는 저널**이다. 파이프라인 현황(행 상태·진행·다음 액션)의 SSOT는 `state.json`이며, 조회는 `state-tool show`로 한다.
- **출력 형식**: 모든 응답은 단일 라인 JSON

## 호출 형식

```bash
~/.opal/tools/state-tool/run.sh <command> <task-path> [options]
```

> 개발 중에는 소스 경로로 직접 호출:
> `bash opal/tools/state-tool/run.sh <command> <task-path> [options]`

## 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | 성공 |
| `1` | 위반 / 스코프 오류 / 검증 실패 |
| `2` | 내부 오류 (subprocess 실패 / 미구현 기능) |

> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` T-3

## 10개 서브 명령

### 1. `init` — state.json + STATE.md 생성

```bash
~/.opal/tools/state-tool/run.sh init <task-path> \
  --skill <opp|opd|opds|opdw|opwt|opgc|oppd|opsdd|oppl|opdd> \
  --mode <interactive|semi-agentic|agentic> \
  [--task-title <text>] \
  [--next-action <text>] \
  [--rows-spec <inline-json>] \
  [--rows-from <path-to-pipeline.json-or-skill.md>] \
  [--rows-acts <inline-json>]          # 시그니처만, 미구현 (R-13) \
  [--force]                            # 멱등성 우회 (--note 필수) \
  [--note <text>]
```

- `--rows-spec`과 `--rows-from`은 배타적 (동시 사용 불가 — `rows_input_conflict`)
- `--rows-from`은 확장자로 분기한다(070 R-2): `.json`이면 `pipeline.json` 스펙 검증 후 로딩(rows에 task-step `key` 영속, `conditional` 메타데이터 저장), `.md`이면 기존 SKILL.md 표 파싱(레거시) + stderr에 deprecation 경고 1줄 출력. 두 경로 모두 stdout 응답 계약은 동일.
- `--next-action`: `state.json` `next_action` 필드로 영속화된다(기본값 `"PLAN 단계 진입"`). 이후 `advance`/`mark` 시 파이프라인 프론티어(첫 미완료 행)에서 자동 파생·갱신된다(072) — PM 수동 갱신 불필요. **094부터 이를 렌더하는 STATE.md 전용 섹션은 없다**(저널화로 `## 다음 액션` 자동 파생 섹션 삭제) — 현재 값은 `show`(md의 `- 다음 액션:` 줄 또는 json의 `next_action` 필드)로 조회한다
- `--force` 사용 시 `--note` 필수 (`note_required_for_force`)
- 구 STATE.md 표 흡수 옵션(`import`+`existing` 합성명, 094 이전 사용): **094(STATE.md 저널화)에서 제거됨** — 호출 시 rows 파싱 없이 항상 `import_existing_removed`로 거부된다(exit 1). 파싱 대상이던 파이프라인 표 자체가 STATE.md에서 소멸했기 때문이다. 행 구성은 `--rows-from <pipeline.json>` 또는 `--rows-spec`을 사용한다. (해당 인자는 argparse에 `help=argparse.SUPPRESS`로만 존치 — 완전히 삭제하면 미인식 인자로 exit 2 비-JSON 출력이 발생해 stdout 계약이 깨지므로, 인자는 받되 즉시 거부하는 방식을 택했다. 이 문서는 SUPPRESS 취지에 따라 정확한 플래그 철자를 의도적으로 노출하지 않는다)
- agentic 모드에서 CLOSE 단계가 아닌 사용자 확인 행은 자동으로 `na`(-) 처리 (`.json`/`.md`/`--rows-spec` 공통)
- `--note`(`--force` 시 기재)에 `{owner_name}` 플레이스홀더를 쓰면 `~/.opal/identity.md`의 `owner_name`으로 write-time 치환된다. identity.md 부재/`owner_name` 공란/파싱 실패 시 원문(`{owner_name}`) 그대로 유지(fail-safe) — 054

**성공 응답 예시**:
```json
{"ok": true, "command": "init", "task_path": "/path/to/task", "task_id": "134-...", "rows_count": 20, "created_at": "2026-05-01 17:58", "import_existing": false}
```

---

### 2. `show` — 파이프라인 현황 조회 (094 R-5: 표준 경로)

```bash
~/.opal/tools/state-tool/run.sh show <task-path> [--format md|json|full]
```

| `--format` | 출력 내용 |
|-----------|----------|
| `md` (기본) | `state.json.rows[]`에서 파생 렌더한 파이프라인 표 + `## 현재 상태` 3줄(모드/상태/다음 액션) |
| `json` | state.json raw (`marker_present` 필드 포함) |
| `full` | STATE.md 전체 본문 |

- `md`/`full` 모두 **마커 유무와 무관하게** `state.json`에서 렌더한다(094 R-5/D-4 — SSOT는 `state.json` 단일이며, 레거시 STATE.md의 마커·표 잔존 여부는 렌더 소스에 영향을 주지 않는다)
- 레거시(001~093) STATE.md에 파이프라인 마커가 잔존해 `marker_present:true`이면 `md`/`full` 응답 상단에 배너 1줄이 prepend된다: "[레거시] 이 태스크의 STATE.md에는 파이프라인 표가 남아 있으나 더 이상 갱신되지 않는 동결 텍스트입니다. 현황의 SSOT는 state.json이며 아래 렌더가 최신입니다."
- `marker_present`(`json` 포맷 필드): 094 저널화 이후 이 값이 `true`인 것은 **레거시 동결 표 잔존**을 뜻한다(현재 갱신되는 미러가 아니다) — 키·타입은 하위호환으로 존치
- state.json 미존재 시: `state_not_initialized` + exit 1

---

### 3. `advance` — ⬜→🔄 전환

```bash
~/.opal/tools/state-tool/run.sh advance <task-path> \
  (--task-step <key> | --task-step-id <n> | --row <n>) \
  [--note <text>] \
  [--next-action <text>]                    # per-transition 오버라이드, 비지속 (072)
```

- 행 주소는 `--task-step`(key) / `--task-step-id`(숫자) / `--row`(숫자, deprecated 별칭) 중 정확히 하나 (070 R-4)
- `pending` 상태인 행만 `in_progress`로 전환 (T-7)
- CLOSE 단계 첫 행이면 직전 사용자 확인 게이트 자동 검증 (§2.16 G-13)
- `state.json` `next_action`이 파이프라인 프론티어(첫 미완료 행)에서 자동 파생·갱신된다. `--next-action <text>` 지정 시 해당 값이 파생값보다 우선하며, 이 오버라이드는 **해당 전이 1회에만** 적용된다 — 다음 전이가 `--next-action` 없이 실행되면 자동 파생으로 복귀한다(072). **094부터 STATE.md에 이를 렌더하는 `## 현재 상태`/`## 다음 액션` 섹션은 없다** — 현재 상태 조회는 `show`로 한다
- STATE.md는 `> 최종 갱신:` 헤더 타임스탬프만 갱신된다(저널 후처리, 094)
- `--note`의 `{owner_name}` 플레이스홀더는 identity.md `owner_name`으로 write-time 치환된다. 부재/공란/파싱 실패 시 원문 유지(fail-safe) — 054

---

### 4. `mark` — ⬜/🔄→✅ 전환

```bash
~/.opal/tools/state-tool/run.sh mark <task-path> \
  (--task-step <key> | --task-step-id <n> | --row <n>) --done \
  [--note <text>] \
  [--as-worker --worker-stage <stage>] \   # 워커 권한 게이트 (T-10)
  [--step <N/M> | --action-step <N/M>] \    # EXECUTE Step 진행 표기 (동일 dest, 070 R-5)
  [--worker-duration-minutes <minutes>] \   # 워커 실제 실행 시간(분) 기록 (103 R-15)
  [--worker-duration-unknown] \             # 소요 미상 명시 — 누락 경고 억제 (103 R-21)
  [--owner <PM|worker|user|auto>] \
  [--auto-pass] \                           # agentic 자율 통과 (T-9)
  [--force] \                               # --note 필수
  [--next-action <text>]                    # per-transition 오버라이드, 비지속 (072)
```

- 행 주소는 `--task-step`(key) / `--task-step-id`(숫자) / `--row`(숫자, deprecated 별칭) 중 정확히 하나 (070 R-4). 미지정 시 `task_step_addr_required`, 2개 이상 지정 시 `task_step_addr_conflict`, key 미매칭 시 `task_step_not_found`(응답에 `candidates` 후보 목록 포함)
- `--action-step`은 `--step`의 신규 별칭(동일 동작, 070 R-5) — 기존 `--step`도 그대로 동작
- `--owner`와 `--auto-pass`는 배타적
- `--as-worker` 사용 시 `--worker-stage` 필수
- `--worker-duration-minutes <n>`(103 R-15)은 그 행에서 **워커(서브에이전트)가 실제 실행한 시간을 분 단위 0 이상 정수**로 `rows[].worker_duration_minutes`에 기록한다. 원천은 워커 완료 시 하네스가 반환하는 `duration_ms`이며, PM이 분으로 환산해 전달한다(집계 기준 16-b)
  - **지정 시에만 기록된다** — 미지정 호출은 필드를 만들지 않으며 `state.json`·응답 키 집합이 종전과 완전히 동일하다(기존 태스크 무영향)
  - 미기록 행의 소요는 집계에서 `PM` 계열로 전액 귀속된다(축퇴 규칙, 집계 기준 16-a) — 따라서 기록이 없는 과거 태스크는 종전 2계열 수치와 항등이다
  - `0`은 유효값이다(측정했으나 1분 미만). "측정하지 않음"은 인자 미지정으로 표현한다
  - 음수·소수·비수치는 **argparse 파싱 시점에 거부**된다(exit 2, `--owner` choices 위반과 동일 계열) — 전용 에러 코드는 신설하지 않았다
  - `--auto-pass` 재호출 멱등 no-op(093 F-005)은 이 인자가 실린 호출에는 적용되지 않는다 — 기록할 값이 조용히 버려지지 않게 하기 위함이며, 인자 없는 기존 호출의 no-op 조건은 불변이다
  - 기록에 성공하면 `mark` 응답 JSON에도 `worker_duration_minutes` 키가 실린다(지정하지 않으면 키 없음)
- **소요 누락 경고**(103 R-21) — `--as-worker` 또는 `--worker-stage`가 실린 `mark`가 그 행을 실제로 `done`으로 닫는데 `--worker-duration-minutes`가 없으면, 응답 JSON에 `warnings` 배열이 조건부로 실린다(`[{"code": "worker_duration_missing", "message": ...}]`)
  - **경고이지 차단이 아니다** — exit code는 `0`을 유지하고 상태 전이도 정상 수행되며, `state.json`·`STATE.md` 산출물은 경고 유무와 무관하게 동일하다. 경고는 stdout JSON에만 실린다
  - 경고가 없으면 `warnings` 키 자체를 만들지 않는다 — 기존 호출의 응답 키 집합은 종전과 완전히 동일하다
  - 이 경고가 필요한 이유: 워커 완료 알림의 `duration_ms`는 세션과 함께 사라지고 행에는 완료 시각만 남아 시작 시각을 되살릴 수 없다. 그 자리에서 적지 않으면 소요는 **영구히 소실**되고 통계에서 PM 몫으로 잘못 귀속된다(소급 복구 경로 없음)
  - 오탐을 막는 4관문: ① 값이 이미 실림 ② `--worker-duration-unknown` 억제 ③ 워커 신호 부재(PM 직접 수행 행) ④ `--action-step N/M`에서 `N<M`(행이 `in_progress`로 남는 중간 진행 보고). 추가로 `owner = "user"`인 사용자 확인 행과 `--auto-pass` 재호출 멱등 no-op(093 F-005) 경로도 제외된다
  - 경고 코드는 `ERROR_CODES`가 아니라 별도 사전 `WARNING_CODES`에 산다 — 경고는 에러가 아니며, **103은 에러 코드를 늘리지 않았다**(103 시점 45종 유지. 이후 106 F-004가 `code_scan_citation_unmet` 1종을 등재해 현재 실측은 **46종**이며, 경고/에러 사전 분리 자체는 불변이다)
- `--worker-duration-unknown`(103 R-21)은 그 행의 워커 소요를 **알 수 없음을 명시**한다(중단된 워커·PM 직접 수행·소급 불가 과거 데이터). 경고를 억제하며 행에는 필드를 만들지 않는다 — 기록 결과는 인자 미지정과 완전히 동형이므로 "미측정"이 `0`("측정했으나 1분 미만")으로 오독되지 않는다
  - `--worker-duration-minutes`와 **배타적**이다(값과 미상 선언은 동시에 성립할 수 없음). 둘 다 지정하면 argparse가 exit 2로 거부한다 — `--owner`/`--auto-pass` 배타와 동일 계열이므로 전용 에러 코드는 신설하지 않았다
- `--auto-pass` 사용 시 `owner = "auto"`, note에 "agentic auto-pass" 자동 기재
- CLOSE 첫 행 + agentic/semi-agentic 모드 + `--auto-pass` 조합 거부 (`agentic_close_gate_requires_user`)
- `--force` 사용 시 `--note` 필수 + 의사결정 로그 자동 기재
- `state.json` `next_action`이 파이프라인 프론티어(첫 미완료 행)에서 자동 파생·갱신된다. `--next-action <text>` 지정 시 해당 값이 파생값보다 우선하며, 이 오버라이드는 **해당 전이 1회에만** 적용된다 — 다음 전이가 `--next-action` 없이 실행되면 자동 파생으로 복귀한다(072). **094부터 STATE.md에 이를 렌더하는 `## 다음 액션` 섹션은 없다** — 현재 상태 조회는 `show`로 한다
- STATE.md는 `> 최종 갱신:` 헤더 타임스탬프 갱신 + (의사결정 있을 시) `## 의사결정 로그` 표에 1행 자동 추가(저널 후처리, 094)
- `--note`의 `{owner_name}` 플레이스홀더는 identity.md `owner_name`으로 write-time 치환된다(`--auto-pass` 접두 "agentic auto-pass: " 뒤에도 적용). 부재/공란/파싱 실패 시 원문 유지(fail-safe) — 054

---

### 5. `block` — any→❌ + current_status=blocked

```bash
~/.opal/tools/state-tool/run.sh block <task-path> \
  (--task-step <key> | --task-step-id <n> | --row <n>) \
  --reason <text>
```

- 행 주소는 `--task-step`(key) / `--task-step-id`(숫자) / `--row`(숫자, deprecated 별칭) 중 정확히 하나 (070 R-4)
- 행 상태 `failed`(❌) + `current_status` → `blocked` 자동 전환(`state.json`)
- STATE.md는 `> 최종 갱신:` 헤더 타임스탬프만 갱신된다 — **094부터 `- 상태:` 자동 렌더 섹션은 없다**, 현재 상태 조회는 `show`로 한다
- 의사결정 로그 자동 기재 안 함 (`## 블로커` 자유 기재 섹션은 PM이 직접 작성)
- `--reason`의 `{owner_name}` 플레이스홀더는 identity.md `owner_name`으로 write-time 치환된다(`note`는 `"block: {치환결과}"`). 부재/공란/파싱 실패 시 원문 유지(fail-safe) — 054

---

### 6. `validate` — 정합성 검증

```bash
~/.opal/tools/state-tool/run.sh validate <task-path>
```

검증 항목:
- 스키마 필수 필드 존재 여부
- 사용자 확인 행 `owner` 정합성
- interactive 모드에서 `owner=auto` 사용 여부
- semi-agentic 모드에서 EXECUTE-equivalent 이전 행 `owner=auto` 사용 여부 (`semi_agentic_pre_execute_auto_pass_denied`)

> 094: STATE.md 마커 존재 여부 검사는 저널화로 제거되었다 — `validate`는 더 이상 마커 유무를 판정하지 않는다(`marker_missing` 소멸).

**응답 예시**:
```json
{"ok": true, "command": "validate", "violations": [], "violations_count": 0}
```
```json
{"ok": false, "command": "validate", "violations": [{"code": "user_confirmation_owner_mismatch", "row_id": 12, "detail": "owner=None"}], "violations_count": 1}
```

---

### 7. `add-row` — 추가작업 행 삽입

```bash
~/.opal/tools/state-tool/run.sh add-row <task-path> \
  (--after-task-step <key> | --after-task-step-id <n> | --after <n>) \
  --stage <stage> \
  --item <항목명> \
  [--key <key>] \                           # 070 R-9: 명시 지정 (미지정 시 자동 생성)
  [--note <text>]
```

- 앵커 행 주소는 `--after-task-step`(key) / `--after-task-step-id`(숫자) / `--after`(숫자, deprecated 별칭) 중 정확히 하나 (070 R-4) — 그 행 직후에 새 행 삽입 (row_id 전체 재정렬, 기존 행 key는 불변)
- 신규 행의 `key`는 `--key` 명시 지정(형식 위반 시 `task_step_key_invalid`, 기존 key와 중복 시 `task_step_key_duplicate`) 또는 미지정 시 `{stage_slug}.{item_slug}_{n}` 자동 생성(파일 내 유일성 보장, 070 R-9)
- `current_status == "done"` → `additional_work` 자동 전환
- `current_status == "additional_work_done"` → `additional_work` 자동 회귀
- 의사결정 로그 자동 기재 (§2.17 트리거 #5)
- `--note`의 `{owner_name}` 플레이스홀더는 identity.md `owner_name`으로 write-time 치환된다. 부재/공란/파싱 실패 시 원문 유지(fail-safe) — 054

**성공 응답**:
```json
{"ok": true, "command": "add-row", "row_id": 11, "key": "test.fix_1", "rows_count": 21, "current_status": "additional_work"}
```

---

### 8. `status` — current_status 명시 전환

```bash
~/.opal/tools/state-tool/run.sh status <task-path> \
  --set <in_progress|done|blocked|additional_work|additional_work_done> \
  [--note <text>]
```

허용 전이 그래프:
- `in_progress` → `done` / `blocked` / `additional_work`
- `done` → `additional_work` / `blocked`
- `blocked` → `in_progress` / `done`
- `additional_work` → `additional_work_done` / `blocked` / `in_progress`
- `additional_work_done` → `additional_work` / `blocked`

위 그래프 외 전이 시도: `invalid_status_transition` + exit 1

`--note`의 `{owner_name}` 플레이스홀더는 identity.md `owner_name`으로 write-time 치환된다(의사결정 로그 근거에 반영). 부재/공란/파싱 실패 시 원문 유지(fail-safe) — 054

---

### 9. `gate-pass` — Gate 4행 일괄 ✅ 처리

```bash
~/.opal/tools/state-tool/run.sh gate-pass <task-path> \
  --start <N> \
  [--note <text>]
```

- 행 N부터 4행이 `[QA Gate, State Gate, PM Gate, State Gate]` 패턴이어야 함
- 4행 모두 동일 stage여야 함
- 4행 모두 동일 timestamp로 ✅ 처리
- 의사결정 로그 자동 기재 (§2.17 트리거 #6)

**성공 응답**:
```json
{"ok": true, "command": "gate-pass", "rows_passed": [6, 7, 8, 9], "stage": "PLAN", "timestamp": "2026-05-01 18:00"}
```

---

### 10. `spec-validate` — pipeline.json 스펙 검증 (070 R-6)

```bash
~/.opal/tools/state-tool/run.sh spec-validate <pipeline.json 경로>
```

- task-path가 아닌 **pipeline.json 파일 경로**를 받는 유일한 서브 명령
- 검사 항목: 필수 필드(spec_version/skill/meta/task_steps) 존재, skill enum 정합, `task_steps[].stage` STAGE_ENUM 정합, key 형식(`^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*(_[0-9]+)?$`), key 유일성, id 1..N 순차, key의 stage_slug와 실제 stage 정합
- `init --rows-from <pipeline.json>`이 내부적으로 동일 검증을 재사용한다(공유 단일 검증 지점)

**성공 응답**:
```json
{"ok": true, "command": "spec-validate", "violations": [], "violations_count": 0}
```
**실패 응답**:
```json
{"ok": false, "command": "spec-validate", "violations": [{"code": "spec_key_duplicate", "id": 2, "key": "plan.pm_gate", "detail": "..."}], "violations_count": 1}
```

---

### `verify` — TEST-SCENARIO.md 검증 + TASK 게이트 (013/016/005/098/100)

`10개 서브 명령`과 별개로 동작하는 검증 전용 명령. task-path 하나에 여러 독립
분기(mock 패턴/증거 누락 검사, `--red-check`, `--fix-mode`, `--clarification-check`,
`--evidence-check`, `--code-scan-citation-check`)가 있으며 각 분기는 조기 반환한다 — 동시 지정 가능
조합은 플래그별 계약을 따른다(`--clarification-check`·`--evidence-check`·`--code-scan-citation-check`
3종은 서로 동시 지정 불가, 아래 참조).

```bash
~/.opal/tools/state-tool/run.sh verify <task-path> --evidence-check [--task-md <path>]
```

- `--evidence-check`: TASK.md의 **두 곳**을 근거 등급 4축(① 인용 존재 ② 인용
  유효(경로·줄 실존) ③ 등급 부여 ④ E5 단독 아님)으로 판정하여 항목별
  확정/미확정 + 사유를 반환하는 **라우터**다 — 미충족이어도 차단하지 않는다
  (exit code 항상 0). PM이 반환된 `unconfirmed`를 검토해 판단으로 확정 승격할
  수 있다(098, PLAN §3.3.2 / 100 §3.7.2).
  - **파싱 대상 ①** `## 명확화 결과` **표**의 `의존 사실` 열 → `source:
    "clarification"` (098부터).
  - **파싱 대상 ②** `## 확정된 설계 방향` 섹션의 **최상위 불릿** → `source:
    "confirmed_direction"` (100부터). 표가 아니라 불릿 리스트이므로 전용 파서로
    수집하며, 표의 열 구성에는 아무 영향이 없다. 중첩(들여쓴) 불릿은 항목으로
    수집하지 않고, `element`에는 불릿 본문 원문이 그대로 담긴다(어떤 항목이
    미확정인지 PM이 식별할 수 있어야 하므로 인덱스형 라벨을 쓰지 않는다).
- `items[]`의 `source` 필드가 두 출처를 구분한다(`"clarification"` |
  `"confirmed_direction"`). 두 소스는 하나의 `items[]`로 병합되지만 **비율
  분모는 공유하지 않는다** — 아래 `confirmed_ratio` / `direction_confirmed_ratio`
  참조.
- `--task-md <path>`: TASK.md 경로 명시(기본 `<task-path>/TASK.md`).
- `--clarification-check`와 동시 지정 시 `evidence_check_flag_conflict`로 거부(exit 1) — 같은 표를 서로 다른 반환 계약(차단형/라우터형)으로 동시에 소비할 수 없다.
- TASK.md 부재, `## 명확화 결과` 섹션/표 부재, `의존 사실` 열 부재는 모두 하위호환
  graceful skip(`evidence_check: "skipped"`, exit 0) — 레거시 TASK.md 회귀 없음.
  `## 확정된 설계 방향` 섹션 부재·항목 0건도 마찬가지로 조용히 건너뛴다
  (`direction_confirmed_ratio: null`, 분모 0 나눗셈 없음).
- 인용 형식 4종: `` `경로:N` ``/`` `경로:N-M` `` (등급 매핑 + 파일·줄 실존 검사) /
  `` `경로` §N `` (등급 매핑 + 경로 존재만) / `[사이트명](URL)` (네트워크 접근
  금지, `grade:"unknown"`) / `(→ D-N §N)` 단축 참조(테이블 역참조 미해석,
  `grade:"unknown"`). 디렉토리 없는 파일명 단독 토큰(`/` 없음)도 저장소 탐색 없이
  `grade:"unknown"`.
- 등급 패턴 기본 세트(1차): `.opal/brain/**`·`.opal/code-scan.json`·`*code-map*` →
  E5 / `docs/**`·`*.md` → E4 / `**/tests/**`·`test_*.py` 및 코드 확장자(`.py .ts
  .tsx .js .sh .json`) → E2 / 그 외 → `unknown`. E1(실행 관측)·E3(생성 코드)은
  경로 패턴으로 판별 불가하므로 자동 부여 대상이 아니다(항상 `unknown`).
- `unknown` 등급은 `confirmed_ratio` 계산에서 미확정으로 계상한다(분자 제외·
  분모 포함) — 근거 없음은 완료가 아니라는 원칙의 도구 집행이다.
- **verdict 3종**: `확정` / `승계` / `미확정`.
  - `확정` — `[결정]` 태그 보유(캡틴 결정은 근거 판정 면제) 또는 4축 통과.
  - `승계` — `[사실]` 태그 + 유효 인용(E2/E4 + 실존)으로 4축 통과. 상류에서 이미
    대조 확인된 사실을 승계했다는 표시이며(재확인 면제), **계수상 `확정`과
    동등하게 confirmed로 집계**된다(100).
  - `미확정` — 인용 부재/경로 부재/등급 unknown/E5 단독 등. `unconfirmed[]`에
    오르며, 두 출처의 미확정 항목이 함께 담긴다.

**성공 응답(라우터)**:
```json
{
  "ok": true, "command": "verify", "evidence_check": "routed",
  "items": [
    {"element": "목표", "verdict": "확정", "reasons": [],
     "citations": [{"raw": "`opal/tools/state-tool/state_tool.py:100`", "grade": "E2", "exists": true}],
     "source": "clarification"},
    {"element": "제약", "verdict": "미확정", "reasons": ["citation_missing"], "citations": [],
     "source": "clarification"},
    {"element": "`[사실]` evidence-check는 라우터다 (`opal/tools/state-tool/README.md:267`).",
     "verdict": "승계", "reasons": [],
     "citations": [{"raw": "`opal/tools/state-tool/README.md:267`", "grade": "E4", "exists": true}],
     "source": "confirmed_direction"}
  ],
  "confirmed_ratio": 0.5, "direction_confirmed_ratio": 1.0,
  "unconfirmed": ["제약", "완료기준"]
}
```
`evidence_check`는 `"pass"`(confirmed_ratio 1.0) / `"routed"`(일부 미확정) /
`"skipped"`(graceful skip) 중 하나이며, exit code는 항상 0이다.

**두 비율 키는 분모가 다르다**(100 PD-1 — 분리형):

| 키 | 분모 | 분자 |
|----|------|------|
| `confirmed_ratio` | `## 명확화 결과` 4요소 항목 수 **고정(불변)** | 그중 `확정`+`승계` |
| `direction_confirmed_ratio` | `## 확정된 설계 방향` 최상위 불릿 수 | 그중 `확정`+`승계` |

`confirmed_ratio`의 분모에 방향 항목이 섞이지 않는다 — 기존 소비자의 의미를
바꾸지 않기 위한 의도적 분리다. `direction_confirmed_ratio`는 섹션 부재 또는
항목 0건일 때 `null`이며, `evidence_check` 상태값(`pass`/`routed`) 판정에는
관여하지 않는다(기존 `confirmed_ratio` 단독 기준 유지).

**플래그 충돌 응답**:
```json
{"ok": false, "command": "verify", "error": "evidence_check_flag_conflict", "message": "..."}
```

---

#### `--code-scan-citation-check` — code-scan 결과 인용 게이트 (106)

```bash
~/.opal/tools/state-tool/run.sh verify <task-path> --code-scan-citation-check
```

- **판정 대상**: `<task-path>/PLAN.md` §4.2 실행 체크리스트 본문. 그 안에 code-scan 결과
  인용 토큰(`domain`/`layer`/`depends`/`exports` 및 `discover`/`scaffold`/`target`/`validate`/`feature`
  결과 필드)이 1건 이상 존재하는지 판정한다. 디스패치 프롬프트는 파일로 남지 않으므로,
  **파일로 영속되고 워커에 그대로 전달되는 PLAN.md Step 본문**을 증거로 삼는다.
- **반환** `code_scan_citation_check`: `pass` | `skipped` | `unmet` (도메인 3값으로 닫힘).
  `exit`: `pass`·`skipped` → 0 / `unmet` → 1 (`error: code_scan_citation_unmet`).
- **스킵 `reason` 3값** — **[MUST] 판정보다 앞에 평가한다.** 순서 자체가 계약이며, 아래로
  내리면 조용히 통과해야 할 태스크에서 거부가 발생한다:
  1. `code_scan_unavailable` — `.opal/code-scan.json` 부재 또는 `headerSource` ∉ {`inline`, `manifest`}
  2. `plan_md_absent` — PLAN.md 부재 (하위호환)
  3. `doc_only_task` — §4.2 대상 파일에 code-scan 적용 확장자 0건 (순수 문서 태스크)
- **집행 지점 2곳**: ① 위 라우터(PM 수동 호출) ② **EXECUTE 단계 첫 행 진입 시
  `advance`/`mark`의 자동 훅** — 동일 판정을 재실행해 진입 자체를 차단한다. 거부는
  `save_state_json()` **이전** 검증 구간이므로 `state.json`·`STATE.md`가 오염되지 않는다.
  우회는 `--force --note`만 가능하며(의사결정 로그에 남는다), `--auto-pass`로는 우회할 수 없다.
- `--clarification-check`·`--evidence-check`와 동시 지정 시 `evidence_check_flag_conflict`로 거부(exit 1).
- 신규 영속 필드 0건 — `state.json`·`STATE.md`·`schema/*.json`은 변경되지 않는다.
- 규정 SSOT: `opal/core/references/harness/pm-review-gate.md` §표준 검토 항목 14.

## `--rows-spec` 입력 형식

```bash
~/.opal/tools/state-tool/run.sh init <task-path> \
  --skill opp --mode interactive \
  --rows-spec '[
    {"stage": "TASK", "item": "작업"},
    {"stage": "TASK", "item": "사용자 확인"},
    {"stage": "PLAN", "item": "작업"},
    {"stage": "PLAN", "item": "PLAN.md 생성"},
    {"stage": "PLAN", "item": "QA Gate"},
    {"stage": "PLAN", "item": "QA-PLAN.md 생성"},
    {"stage": "PLAN", "item": "State Gate"},
    {"stage": "PLAN", "item": "PM Gate"},
    {"stage": "PLAN", "item": "State Gate"},
    {"stage": "PLAN", "item": "사용자 확인"},
    {"stage": "CLOSE", "item": "DONE.md 생성"},
    {"stage": "CLOSE", "item": "State Gate"}
  ]'
```

---

## 에러 코드 카탈로그 (46종 실측 SSOT — PLAN §2.18 E-1 + 070 R-1/R-4/R-9 + 091 F-004 R-10/R-11 + 093 F-004 R-4 + 094 R-3/R-4/R-9 + 098 F-003 R-4 + 106 F-004 R-4)

> 종수는 `len(ERROR_CODES)`(`state_tool.py`) 실측값이 기준이다 — 이 헤더 숫자를 리터럴로 신뢰하지 말고 코드 실측으로 재검증할 것(094 R-9 ①, S-7/S-15).

| # | 에러 코드 | 발생 명령 | 종료 코드 | 의미 |
|---|---------|---------|---------|------|
| 1 | `worker_scope_violation` | mark | 1 | 워커가 자기 단계 외 행 갱신 시도 |
| 2 | `already_initialized` | init | 1 | state.json 이미 존재 (`--force`로 우회) |
| 3 | `date_tool_failed` | 모든 갱신 명령 | 2 | date.js 호출 실패 |
| 4 | `import_existing_removed` | init(구 STATE.md 표 흡수 옵션 호출 시) | 1 | 해당 옵션 사용 시 항상 거부 — 파싱 대상이던 파이프라인 표가 STATE.md에서 소멸 (094 R-4/D-2) |
| 5 | `invalid_status_transition` | status | 1 | current_status 전이 그래프 위반 |
| 6 | `row_not_found` | mark/advance/block/add-row | 1 | --row N 행 미존재 |
| 7 | `invalid_stage_enum` | add-row | 1 | --stage 값이 16종 enum 외 |
| 8 | `gate_pattern_mismatch` | gate-pass | 1 | 4행 패턴 불일치 |
| 9 | `gate_stage_mixed` | gate-pass | 1 | 4행 stage 혼합 |
| 10 | `state_not_initialized` | show/advance/mark/block/validate/add-row/status/gate-pass | 1 | state.json 미존재 |
| 11 | `user_confirmation_owner_mismatch` | validate | 1 | 사용자 확인 행 owner 불일치 |
| 12 | `owner_flag_conflict` | mark | 1 | --owner와 --auto-pass 동시 사용 |
| 13 | `auto_pass_in_interactive_mode` | validate | 1 | interactive 모드에서 owner=auto |
| 14 | `close_gate_violation` | mark/advance | 1 | CLOSE 진입 게이트 위반 |
| 15 | `agentic_close_gate_requires_user` | mark | 1 | agentic/semi-agentic CLOSE 첫 행에 --auto-pass 거부 |
| 16 | `semi_agentic_pre_execute_auto_pass_denied` | mark / validate | 1 | semi-agentic 모드에서 EXECUTE 등가 단계 이전 행에 --auto-pass 사용 불가 |
| 17 | `mode_flag_conflict` | (state init 포함 -- 향후) | 1 | 다중 모드 플래그 동시 사용 불가 |
| 18 | `note_required_for_force` | init --force / mark --force | 1 | --force 시 --note 미제공 |
| 19 | `rows_spec_invalid_json` | init --rows-spec | 1 | --rows-spec JSON 배열 아님 |
| 20 | `skill_md_parse_error` | init --rows-from | 1 | SKILL.md 행 추출 실패 |
| 21 | `task_path_not_found` | 모든 명령 | 1 | task-path 디렉토리 미존재 |
| 22 | `worker_stage_required` | mark | 1 | --as-worker 시 --worker-stage 미지정 |
| 23 | `rows_input_conflict` | init | 1 | --rows-spec과 --rows-from 동시 사용 |
| 24 | `rows_acts_not_implemented` | init --rows-acts | 2 | opsdd ACT 동적 주입 미구현 |
| 25 | `mock_in_scenario` | mark(TEST stage done 훅) | 1 | TEST-SCENARIO.md에 mock 코드 패턴 발견 (013) |
| 26 | `evidence_missing` | mark(TEST stage done 훅) | 1 | TEST-SCENARIO.md Pass 시나리오에 실행 증거 누락 (013) |
| 27 | `stage_transition_violation` | advance/mark | 1 | 단계 건너뛰기 차단 — 앞 행 미완료 (014 §M-A) |
| 28 | `red_evidence_missing` | verify --red-check | 1 | RED 증거(실패 출력) 누락 (016) |
| 29 | `test_modified_in_fix` | verify --fix-mode | 1 | fix 루핑 중 RED 테스트 파일 수정 감지 (016) |
| 30 | `clarification_gate_unmet` | verify --clarification-check / advance / mark | 1 | TASK 4요소 미잠금 — 다음 단계 진입 거부 (005) |
| 31 | `spec_file_not_found` | spec-validate / init --rows-from(.json) | 1 | pipeline.json 스펙 파일 없음 (070) |
| 32 | `spec_invalid_json` | spec-validate / init --rows-from(.json) | 1 | pipeline.json JSON 파싱 실패 (070) |
| 33 | `spec_validation_failed` | init --rows-from(.json) | 1 | pipeline.json 스펙 검증 실패(violations[0] 포함) (070) |
| 34 | `task_step_addr_required` | advance/mark/block/add-row | 1 | 행 주소 플래그 0개 지정 (070) |
| 35 | `task_step_addr_conflict` | advance/mark/block/add-row | 1 | 행 주소 플래그 2개 이상 동시 지정 (070) |
| 36 | `task_step_not_found` | advance/mark/block/add-row | 1 | `--task-step <key>` 미매칭(candidates 후보 목록 포함) (070) |
| 37 | `task_step_key_invalid` | add-row --key | 1 | `--key` 형식 위반(KEY_PATTERN) (070) |
| 38 | `task_step_key_duplicate` | add-row --key | 1 | `--key`가 기존 행 key와 중복 (070) |
| 39 | `gate_artifact_missing` | mark | 1 | PM Gate 산출물(`gate.artifacts`) 미충족 — 게이트 아티팩트 부재(`--force`+`--note`로만 우회) (091) |
| 40 | `spec_gate_type_invalid` | spec-validate / init --rows-from(.json) | 1 | `task_steps[].gate`가 object가 아님 (091) |
| 41 | `spec_gate_missing_field` | spec-validate / init --rows-from(.json) | 1 | `task_steps[].gate` 필수 필드(`artifacts`/`checklist`) 누락 (091) |
| 42 | `spec_gate_field_type_invalid` | spec-validate / init --rows-from(.json) | 1 | `task_steps[].gate` 필드 타입 오류(문자열 배열 필요) (091) |
| 43 | `spec_gate_checklist_empty` | spec-validate / init --rows-from(.json) | 1 | `task_steps[].gate.checklist`가 비어 있음 (091) |
| 44 | `user_confirmation_required` | advance/mark | 1 | 자동 승인 불가 구간의 사용자 확인 행 — 캡틴 승인 필요 (093) |
| 45 | `evidence_check_flag_conflict` | verify --evidence-check | 1 | `--evidence-check`와 `--clarification-check` 동시 지정 — 두 게이트 계약 충돌 (098) |
| 46 | `code_scan_citation_unmet` | verify --code-scan-citation-check / advance·mark(EXECUTE 첫 행 자동 훅) | 1 | `PLAN.md` §4.2 대상 파일에 코드 확장자가 있는데 §4.2 본문에 code-scan 결과 인용 토큰이 0건 — 또는 EXECUTE 첫 행 진입에 `--auto-pass`가 실려 우회 시도 (106) |

> `spec-validate` 서브 명령 자체의 violations[] 내부 코드(`spec_missing_field`/`spec_skill_invalid`/`spec_stage_invalid`/`spec_key_format_invalid`/`spec_key_duplicate`/`spec_id_sequence_invalid`/`spec_key_stage_mismatch`)는 `cmd_validate`의 `schema_violation`처럼 인라인 문자열로 쓰이며 ERROR_CODES 템플릿을 거치지 않는다(070 §3.1.2). (`spec_gate_*` 4종은 동일하게 violations[]에 인라인 append되지만 ERROR_CODES에 등록되어 있어 위 카탈로그에 포함된다 — 091이 만든 예외.)

---

## 의존성

- `~/.opal/.venv/bin/python` — 표준 라이브러리만 사용 (`json`, `argparse`, `pathlib`, `subprocess`, `re`, `sys`, `datetime`, `os`)
- `~/.opal/tools/date/date.js` — KST 시점 취득 (node.js)
- `opal/tools/state-tool/schema/state.schema.json` — JSON Schema Draft-07 참조용 (1.0/1.1 병행)
- `opal/tools/state-tool/schema/pipeline-spec.schema.json` — pipeline.json 스펙 JSON Schema Draft-07 참조용 (070 신설)

## 관련 문서

| 문서 | 경로 | 참조 이유 |
|------|------|---------|
| PLAN.md | `tasks/134-260501-opp-pipeline-state-tool/PLAN.md` | §2.1~§2.20 전체 설계 SSOT |
| TASK.md | `tasks/134-260501-opp-pipeline-state-tool/TASK.md` | T-1~T-13 기술 결정 |
| state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | JSON Schema Draft-07 |
| xlsx-tool 패턴 | `opal/tools/xlsx-tool/run.sh:1-12` | OPAL Tools 래퍼 패턴 |

## 변경이력

| 버전 | 일시 (KST) | 태스크 | 변경 내용 |
|------|-----------|--------|---------|
| v1.0 | 2026-05-01 | (134) | 최초 작성 |
| v1.1 | 2026-05-09 11:22 | (140) | 3-way 모드 지원: init --mode semi-agentic 추가, mark/validate semi-agentic 경계 게이트 문서화, 오류 #24/#25 추가 |
| v1.2 | 2026-07-10 13:15 | (054) | `resolve_owner_placeholder()` 신설 — note/reason의 `{owner_name}` 플레이스홀더를 identity.md `owner_name`으로 write-time 치환(fail-safe: 부재/공란/파싱실패 시 원문 유지). init/advance/mark/block/add-row/status 6경로 적용 |
| v1.3 | 2026-07-10 16:33 | (056) | `init --skill` choices + state.schema.json `skill` enum에 `oppl` 추가 (opal-pilot-project-loop 등록, 스키마 신규 필드 없음) |
| v1.4 | 2026-07-10 | (056 ADD-2) | 드리프트 정정 — state.schema.json `mode` enum에 `semi-agentic` 추가 (CLI `--mode` choices와 정합). 신규 필드 없음, `schema_version` 유지("1.0") |
| v1.5 | 2026-07-20 15:45 | (070) | task-step 키 주소 체계 도입 1차 — `spec-validate` 서브명령 신설(10종), `pipeline-spec.schema.json` 신설, `init --rows-from` `.json`/`.md` 확장자 분기(json 스펙 로딩 시 rows[].key·conditional 영속, md는 deprecation 경고), `state.schema.json` 1.1 병행(rows[].key·conditional 선택 필드, schema_version enum), `--task-step`/`--task-step-id`/`--row`(deprecated)/`--action-step`(구 `--step` 별칭) 신설(advance/mark/block), `--after-task-step`/`--after-task-step-id`/`--key`(add-row), opdd skill·DICT/MODEL/DDL·MIGRATION stage enum 등록, ERROR_CODES 8종 추가(39종) |
| v1.6 | 2026-07-23 12:09 | (072) | STATE.md "다음 액션" 자동 파생 — `state.json` `next_action` 필드 신설(init 영속화, `state.schema.json` optional 등록), `advance`/`mark` 프론티어(첫 미완료 행) 자동 파생·`update_next_action_section`(첫 줄만 치환, 하위 자유기재 보존), `advance`/`mark` `--next-action` per-transition 오버라이드(비지속 — 다음 전이 자동 파생 복귀). `## 블로커`는 기존대로 PM 수동 갱신 |
| v1.7 | 2026-08-16 13:15 | (094) | STATE.md 저널화에 따른 문서 재정합(R-4 문서 + R-9 ①③) — 에러 카탈로그 재실측(`marker_missing`/`import_failed` 삭제, `import_existing_removed` 추가, 39종 표기 → **44종 실측값**으로 정정 및 091/093 누락 행(`gate_artifact_missing`/`spec_gate_*`/`user_confirmation_required`) 보강, 행 번호 전체 재부여); `init --import-existing` 사용 안내 제거 — 항상 `import_existing_removed`로 거부됨을 명시(인자는 `help=SUPPRESS`로 존치, 설계 의도 기술); `validate` 검증 항목·응답 예시에서 `marker_missing` 서술 제거; `show` 절을 `cmd_show` 재설계(R-5/D-4)에 맞춰 재작성 — `md`/`full` 모두 마커 유무와 무관하게 `state.json` 단일 파생 렌더, 레거시 마커 잔존 시 배너 1줄 prepend, `marker_present` 필드 의미 재해석(레거시 동결 표 잔존 신호) 1줄 추가 |
| v1.8 | 2026-08-21 18:04 | (098) | `verify --evidence-check` 신설(F-003, PLAN §3.3.2) — TASK.md `## 명확화 결과` 표의 `의존 사실` 셀을 근거 등급 4축으로 판정해 항목별 확정/미확정+사유를 반환하는 라우터(exit 0 유지, 미확정도 차단하지 않음) 신규 절 추가; 에러 코드 44→**45종**(`evidence_check_flag_conflict` — `--evidence-check`/`--clarification-check` 동시 지정 거부) 반영해 카탈로그 헤더·표 정정 |
| v1.9 | 2026-08-23 13:03 | (100) | `verify --evidence-check` 파싱 대상 확장(F-007, PLAN §3.7.2) — `## 명확화 결과` 표에 더해 `## 확정된 설계 방향` 섹션의 **최상위 불릿**을 전용 파서(`_locate_confirmed_direction_items`)로 수집해 하나의 `items[]`로 병합, 각 항목에 출처 구분 `source`(`clarification` \| `confirmed_direction`) 필드 신설; verdict에 `승계` 추가(`[사실]` 태그 + 유효 인용 → 상류 대조 확인 승계, 계수상 `확정`과 동등); 신규 반환 키 `direction_confirmed_ratio`(섹션 부재·항목 0건 시 `null`) 추가 — **기존 `confirmed_ratio`의 분모는 `## 명확화 결과` 항목 수로 불변**(PD-1 분리형, 소비자 계약 보호). 표 열 구성·플래그·에러 코드 45종·exit 0 3경로 전부 불변 |
| v1.10 | 2026-08-25 | (103 R-15) | 워커 소요 계측 필드 신설 — `state.schema.json` `rows[].worker_duration_minutes`(integer, `minimum: 0`) **선택** 등록(`required`·`additionalProperties: false` 불변, 기존 `state.json` 전건 유효), `mark --worker-duration-minutes <n>` 인자 추가(값 검증은 argparse `type` 파서가 파싱 시점에 수행 — 음수·소수·비수치 exit 2, **에러 코드 45종 불변**). 지정 시에만 행에 기록 + `mark` 응답에 동명 키 조건부 추가하며, **미지정 호출은 `state.json`·stdout 모두 종전과 바이트 동일**. 미기록 행은 집계에서 `PM` 계열로 전액 축퇴(집계 기준 16-a) |
| v1.11 | 2026-08-26 | (103 R-21) | 워커 소요 누락 경고 신설 — `mark`가 워커 디스패치 행(`--as-worker` 또는 `--worker-stage`)을 `done`으로 닫으면서 `--worker-duration-minutes`를 넘기지 않으면 응답 JSON에 `warnings` 배열(`worker_duration_missing`)을 조건부로 싣는다. **exit 0 유지·차단 없음**이며 `state.json`·`STATE.md` 산출물은 경고 유무와 무관하게 동일하다(경고는 stdout 전용). 오탐 차단 4관문(값 보유·억제 인자·워커 신호 부재·`--action-step N/M`의 `N<M`) + `owner="user"` 사용자 확인 행·093 재-auto-pass 멱등 no-op 제외. 억제 인자 `--worker-duration-unknown` 추가(`--worker-duration-minutes`와 argparse 배타, 지정 시 경고·필드 모두 미생성). 경고 카탈로그는 신규 `WARNING_CODES`로 분리 — **에러 코드 45종 불변** |
| v1.12 | 2026-08-26 | (103 강제 2단) | 워커 소요 기록 강제 — (1) 경고 판정을 인자 신호(`--as-worker`/`--worker-stage`) **또는 행 구조**(`stage`가 워커 디스패치 규범 단계 + `item`이 「작업」)로 확장해 PM의 자발적 표시에 의존하지 않게 했다. (2) `--worker-duration-unknown`이 행에 `worker_duration_unknown: true`를 영속화한다(스키마 선택 필드) — CLOSE 게이트가 「미측정 선언」과 「침묵」을 갈라야 하기 때문. (3) `mark`가 CLOSE 첫 행 진입 시 기록도 선언도 없는 워커 규범 행이 있으면 **차단**한다(`BLOCK_CODES.worker_duration_undeclared`, `ERROR_CODES` 45종 불변). 통과는 기록 또는 선언 둘뿐이고 `--force --note`가 최후 우회다. 계측 도입(`_WORKER_MEASUREMENT_EPOCH` 2026-08-26) 이전 `created_at` 태스크는 유예 — 「기록 0건이면 유예」로 두면 전건 미기록 신규 태스크가 통과해 강제가 무의미해진다 |
| v1.13 | 2026-09-04 22:52 | (106) | 에러 코드 45→**46종** 반영(F-004 R-4) — `code_scan_citation_unmet` 카탈로그 행 1건 추가(`verify --code-scan-citation-check` 및 `advance`/`mark`의 EXECUTE 첫 행 자동 훅, exit 1: `PLAN.md` §4.2 대상 파일에 코드 확장자가 있는데 §4.2 본문의 code-scan 결과 인용 토큰이 0건이거나, EXECUTE 첫 행 진입에 `--auto-pass`로 우회 시도) + 카탈로그 헤더 종수·근거 목록 정정. 103 R-21 절의 「에러 코드는 45종 그대로다」 문면을 「103이 늘리지 않았다(103 시점 45종) + 현재 실측 46종」으로 정정 — 경고/에러 사전 분리 계약 자체는 불변. 코드↔문서 정합(D-5 ①)은 `test_s7_error_catalog_marker_import_realignment`가 카탈로그 헤더 종수를 `len(ERROR_CODES)` 실측과 대조하므로 이 표기는 코드와 함께 움직여야 한다 |
| v1.14 | 2026-09-04 23:05 | (106) | `verify --code-scan-citation-check` 절 신설 — 판정 대상(PLAN.md §4.2 본문)·반환 3값·스킵 `reason` 3값과 순서 계약·집행 지점 2곳(라우터 + EXECUTE 첫 행 자동 훅)·플래그 상호배타·영속 무변경을 기재. 카탈로그 정정과 함께 신규 절을 추가한 098 v1.8 선례를 준용 |
