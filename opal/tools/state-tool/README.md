# state-tool

> OPAL 파이프라인 현황판 JSON SSOT 관리 CLI
> 소스: `opal/tools/state-tool/` | 배포: `~/.opal/tools/state-tool/`
> 설계 근거: `tasks/134-260501-opp-pipeline-state-tool/PLAN.md` §2.1~§2.20

## 개요

`state-tool`은 STATE.md의 파이프라인 현황판 표를 `state.json`(단일 진실 공급원)으로 분리하고, 10개 서브 명령으로만 갱신 가능하게 만들어 LLM의 절차 우회/오갱신을 차단한다.

> **070: task-step 키 주소 체계**. 행 주소를 불안정한 순번(`--row N`)이 아니라 `references/pipeline.json`에 선언된 task-step key(`plan.pm_gate` 형식)로 지정할 수 있다. `advance`/`mark`/`block`/`add-row`는 `--task-step <key>` / `--task-step-id <n>` / `--row <n>`(deprecated 별칭, 하위호환) 중 정확히 하나를 받는다. 미지정 시 `task_step_addr_required`, 2개 이상 동시 지정 시 `task_step_addr_conflict`, key 미매칭 시 `task_step_not_found`(candidates 포함).

- **SSOT**: `state.json` (마크다운 표는 도구가 자동 렌더한 미러)
- **마커**: `<!-- pipeline:start -->` ~ `<!-- pipeline:end -->` (STATE.md 내 파이프라인 영역 경계)
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
  [--note <text>] \
  [--import-existing]                  # 기존 STATE.md 흡수
```

- `--rows-spec`과 `--rows-from`은 배타적 (동시 사용 불가 — `rows_input_conflict`)
- `--rows-from`은 확장자로 분기한다(070 R-2): `.json`이면 `pipeline.json` 스펙 검증 후 로딩(rows에 task-step `key` 영속, `conditional` 메타데이터 저장), `.md`이면 기존 SKILL.md 표 파싱(레거시) + stderr에 deprecation 경고 1줄 출력. 두 경로 모두 stdout 응답 계약은 동일.
- `--force` 사용 시 `--note` 필수 (`note_required_for_force`)
- `--import-existing`: 기존 STATE.md 마크다운 표를 파싱하여 rows 초기화 + 자유 텍스트 영역 보존
- agentic 모드에서 CLOSE 단계가 아닌 사용자 확인 행은 자동으로 `na`(-) 처리 (`.json`/`.md`/`--rows-spec` 공통)
- `--note`(`--force` 시 기재)에 `{owner_name}` 플레이스홀더를 쓰면 `~/.opal/identity.md`의 `owner_name`으로 write-time 치환된다. identity.md 부재/`owner_name` 공란/파싱 실패 시 원문(`{owner_name}`) 그대로 유지(fail-safe) — 054

**성공 응답 예시**:
```json
{"ok": true, "command": "init", "task_path": "/path/to/task", "task_id": "134-...", "rows_count": 20, "created_at": "2026-05-01 17:58", "import_existing": false}
```

---

### 2. `show` — 파이프라인 현황판 출력

```bash
~/.opal/tools/state-tool/run.sh show <task-path> [--format md|json|full]
```

| `--format` | 출력 내용 |
|-----------|----------|
| `md` (기본) | 파이프라인 현황판 마크다운 표 + `## 현재 상태` 4줄 |
| `json` | state.json raw (`marker_present` 필드 포함) |
| `full` | STATE.md 전체 본문 |

- 마커 누락 시 `md`/`full`은 fallback 출력 (exit 0 + stderr warning)
- state.json 미존재 시: `state_not_initialized` + exit 1

---

### 3. `advance` — ⬜→🔄 전환

```bash
~/.opal/tools/state-tool/run.sh advance <task-path> \
  (--task-step <key> | --task-step-id <n> | --row <n>) \
  [--note <text>]
```

- 행 주소는 `--task-step`(key) / `--task-step-id`(숫자) / `--row`(숫자, deprecated 별칭) 중 정확히 하나 (070 R-4)
- `pending` 상태인 행만 `in_progress`로 전환 (T-7)
- CLOSE 단계 첫 행이면 직전 사용자 확인 게이트 자동 검증 (§2.16 G-13)
- `## 현재 상태` 섹션 `- 진행:` 라인 자동 갱신
- `--note`의 `{owner_name}` 플레이스홀더는 identity.md `owner_name`으로 write-time 치환된다. 부재/공란/파싱 실패 시 원문 유지(fail-safe) — 054

---

### 4. `mark` — ⬜/🔄→✅ 전환

```bash
~/.opal/tools/state-tool/run.sh mark <task-path> \
  (--task-step <key> | --task-step-id <n> | --row <n>) --done \
  [--note <text>] \
  [--as-worker --worker-stage <stage>] \   # 워커 권한 게이트 (T-10)
  [--step <N/M> | --action-step <N/M>] \    # EXECUTE Step 진행 표기 (동일 dest, 070 R-5)
  [--owner <PM|worker|user|auto>] \
  [--auto-pass] \                           # agentic 자율 통과 (T-9)
  [--force]                                 # --note 필수
```

- 행 주소는 `--task-step`(key) / `--task-step-id`(숫자) / `--row`(숫자, deprecated 별칭) 중 정확히 하나 (070 R-4). 미지정 시 `task_step_addr_required`, 2개 이상 지정 시 `task_step_addr_conflict`, key 미매칭 시 `task_step_not_found`(응답에 `candidates` 후보 목록 포함)
- `--action-step`은 `--step`의 신규 별칭(동일 동작, 070 R-5) — 기존 `--step`도 그대로 동작
- `--owner`와 `--auto-pass`는 배타적
- `--as-worker` 사용 시 `--worker-stage` 필수
- `--auto-pass` 사용 시 `owner = "auto"`, note에 "agentic auto-pass" 자동 기재
- CLOSE 첫 행 + agentic/semi-agentic 모드 + `--auto-pass` 조합 거부 (`agentic_close_gate_requires_user`)
- `--force` 사용 시 `--note` 필수 + 의사결정 로그 자동 기재
- `--note`의 `{owner_name}` 플레이스홀더는 identity.md `owner_name`으로 write-time 치환된다(`--auto-pass` 접두 "agentic auto-pass: " 뒤에도 적용). 부재/공란/파싱 실패 시 원문 유지(fail-safe) — 054

---

### 5. `block` — any→❌ + current_status=blocked

```bash
~/.opal/tools/state-tool/run.sh block <task-path> \
  (--task-step <key> | --task-step-id <n> | --row <n>) \
  --reason <text>
```

- 행 주소는 `--task-step`(key) / `--task-step-id`(숫자) / `--row`(숫자, deprecated 별칭) 중 정확히 하나 (070 R-4)
- 행 상태 `failed`(❌) + `current_status` → `blocked` 자동 전환
- `STATE.md` `- 상태: 블로커` 자동 갱신
- 의사결정 로그 자동 기재 안 함 (블로커 섹션은 PM 별도 작성)
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
- STATE.md 마커 존재 여부

**응답 예시**:
```json
{"ok": true, "command": "validate", "violations": [], "violations_count": 0}
```
```json
{"ok": false, "command": "validate", "violations": [{"code": "marker_missing", "row_id": null, "detail": "..."}], "violations_count": 1}
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

## 에러 코드 카탈로그 (39종 SSOT — PLAN §2.18 E-1 + 070 R-1/R-4/R-9)

| # | 에러 코드 | 발생 명령 | 종료 코드 | 의미 |
|---|---------|---------|---------|------|
| 1 | `worker_scope_violation` | mark | 1 | 워커가 자기 단계 외 행 갱신 시도 |
| 2 | `marker_missing` | init(--import-existing 외)/advance/mark/block/add-row | 1 | STATE.md 마커 누락 |
| 3 | `already_initialized` | init | 1 | state.json 이미 존재 (`--force`로 우회) |
| 4 | `date_tool_failed` | 모든 갱신 명령 | 2 | date.js 호출 실패 |
| 5 | `import_failed` | init --import-existing | 1 | 기존 STATE.md 파싱 실패 |
| 6 | `invalid_status_transition` | status | 1 | current_status 전이 그래프 위반 |
| 7 | `row_not_found` | mark/advance/block/add-row | 1 | --row N 행 미존재 |
| 8 | `invalid_stage_enum` | add-row | 1 | --stage 값이 16종 enum 외 |
| 9 | `gate_pattern_mismatch` | gate-pass | 1 | 4행 패턴 불일치 |
| 10 | `gate_stage_mixed` | gate-pass | 1 | 4행 stage 혼합 |
| 11 | `state_not_initialized` | show/advance/mark/block/validate/add-row/status/gate-pass | 1 | state.json 미존재 |
| 12 | `user_confirmation_owner_mismatch` | validate | 1 | 사용자 확인 행 owner 불일치 |
| 13 | `owner_flag_conflict` | mark | 1 | --owner와 --auto-pass 동시 사용 |
| 14 | `auto_pass_in_interactive_mode` | validate | 1 | interactive 모드에서 owner=auto |
| 15 | `close_gate_violation` | mark/advance | 1 | CLOSE 진입 게이트 위반 |
| 16 | `agentic_close_gate_requires_user` | mark | 1 | agentic/semi-agentic CLOSE 첫 행에 --auto-pass 거부 |
| 17 | `note_required_for_force` | init --force / mark --force | 1 | --force 시 --note 미제공 |
| 18 | `rows_spec_invalid_json` | init --rows-spec | 1 | --rows-spec JSON 배열 아님 |
| 19 | `skill_md_parse_error` | init --rows-from | 1 | SKILL.md 행 추출 실패 |
| 20 | `task_path_not_found` | 모든 명령 | 1 | task-path 디렉토리 미존재 |
| 21 | `worker_stage_required` | mark | 1 | --as-worker 시 --worker-stage 미지정 |
| 22 | `rows_input_conflict` | init | 1 | --rows-spec과 --rows-from 동시 사용 |
| 23 | `rows_acts_not_implemented` | init --rows-acts | 2 | opsdd ACT 동적 주입 미구현 |
| 24 | `semi_agentic_pre_execute_auto_pass_denied` | mark / validate | 1 | semi-agentic 모드에서 EXECUTE 등가 단계 이전 행에 --auto-pass 사용 불가 |
| 25 | `mode_flag_conflict` | (state init 포함 -- 향후) | 1 | 다중 모드 플래그 동시 사용 불가 |
| 26 | `mock_in_scenario` | mark(TEST stage done 훅) | 1 | TEST-SCENARIO.md에 mock 코드 패턴 발견 (013) |
| 27 | `evidence_missing` | mark(TEST stage done 훅) | 1 | TEST-SCENARIO.md Pass 시나리오에 실행 증거 누락 (013) |
| 28 | `stage_transition_violation` | advance/mark | 1 | 단계 건너뛰기 차단 — 앞 행 미완료 (014 §M-A) |
| 29 | `red_evidence_missing` | verify --red-check | 1 | RED 증거(실패 출력) 누락 (016) |
| 30 | `test_modified_in_fix` | verify --fix-mode | 1 | fix 루핑 중 RED 테스트 파일 수정 감지 (016) |
| 31 | `clarification_gate_unmet` | verify --clarification-check / advance / mark | 1 | TASK 4요소 미잠금 — 다음 단계 진입 거부 (005) |
| 32 | `spec_file_not_found` | spec-validate / init --rows-from(.json) | 1 | pipeline.json 스펙 파일 없음 (070) |
| 33 | `spec_invalid_json` | spec-validate / init --rows-from(.json) | 1 | pipeline.json JSON 파싱 실패 (070) |
| 34 | `spec_validation_failed` | init --rows-from(.json) | 1 | pipeline.json 스펙 검증 실패(violations[0] 포함) (070) |
| 35 | `task_step_addr_required` | advance/mark/block/add-row | 1 | 행 주소 플래그 0개 지정 (070) |
| 36 | `task_step_addr_conflict` | advance/mark/block/add-row | 1 | 행 주소 플래그 2개 이상 동시 지정 (070) |
| 37 | `task_step_not_found` | advance/mark/block/add-row | 1 | `--task-step <key>` 미매칭(candidates 후보 목록 포함) (070) |
| 38 | `task_step_key_invalid` | add-row --key | 1 | `--key` 형식 위반(KEY_PATTERN) (070) |
| 39 | `task_step_key_duplicate` | add-row --key | 1 | `--key`가 기존 행 key와 중복 (070) |

> `spec-validate` 서브 명령 자체의 violations[] 내부 코드(`spec_missing_field`/`spec_skill_invalid`/`spec_stage_invalid`/`spec_key_format_invalid`/`spec_key_duplicate`/`spec_id_sequence_invalid`/`spec_key_stage_mismatch`)는 `cmd_validate`의 `schema_violation`처럼 인라인 문자열로 쓰이며 ERROR_CODES 템플릿을 거치지 않는다(070 §3.1.2).

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
