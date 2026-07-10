# state-tool

> OPAL 파이프라인 현황판 JSON SSOT 관리 CLI
> 소스: `opal/tools/state-tool/` | 배포: `~/.opal/tools/state-tool/`
> 설계 근거: `tasks/134-260501-opp-pipeline-state-tool/PLAN.md` §2.1~§2.20

## 개요

`state-tool`은 STATE.md의 파이프라인 현황판 표를 `state.json`(단일 진실 공급원)으로 분리하고, 9개 서브 명령으로만 갱신 가능하게 만들어 LLM의 절차 우회/오갱신을 차단한다.

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

## 9개 서브 명령

### 1. `init` — state.json + STATE.md 생성

```bash
~/.opal/tools/state-tool/run.sh init <task-path> \
  --skill <opp|opd|opds|opdw|opwt|opgc|oppd|opsdd> \
  --mode <interactive|semi-agentic|agentic> \
  [--task-title <text>] \
  [--next-action <text>] \
  [--rows-spec <inline-json>] \
  [--rows-from <path-to-skill.md>] \
  [--rows-acts <inline-json>]          # 시그니처만, 미구현 (R-13) \
  [--force]                            # 멱등성 우회 (--note 필수) \
  [--note <text>] \
  [--import-existing]                  # 기존 STATE.md 흡수
```

- `--rows-spec`과 `--rows-from`은 배타적 (동시 사용 불가 — `rows_input_conflict`)
- `--force` 사용 시 `--note` 필수 (`note_required_for_force`)
- `--import-existing`: 기존 STATE.md 마크다운 표를 파싱하여 rows 초기화 + 자유 텍스트 영역 보존
- agentic 모드에서 CLOSE 단계가 아닌 사용자 확인 행은 자동으로 `na`(-) 처리
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
~/.opal/tools/state-tool/run.sh advance <task-path> --row <N> [--note <text>]
```

- `pending` 상태인 행만 `in_progress`로 전환 (T-7)
- CLOSE 단계 첫 행이면 직전 사용자 확인 게이트 자동 검증 (§2.16 G-13)
- `## 현재 상태` 섹션 `- 진행:` 라인 자동 갱신
- `--note`의 `{owner_name}` 플레이스홀더는 identity.md `owner_name`으로 write-time 치환된다. 부재/공란/파싱 실패 시 원문 유지(fail-safe) — 054

---

### 4. `mark` — ⬜/🔄→✅ 전환

```bash
~/.opal/tools/state-tool/run.sh mark <task-path> \
  --row <N> --done \
  [--note <text>] \
  [--as-worker --worker-stage <stage>] \   # 워커 권한 게이트 (T-10)
  [--step <N/M>] \                          # EXECUTE Step 진행 표기
  [--owner <PM|worker|user|auto>] \
  [--auto-pass] \                           # agentic 자율 통과 (T-9)
  [--force]                                 # --note 필수
```

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
  --row <N> \
  --reason <text>
```

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
  --after <N> \
  --stage <stage> \
  --item <항목명> \
  [--note <text>]
```

- 행 N 직후에 새 행 삽입 (row_id 전체 재정렬)
- `current_status == "done"` → `additional_work` 자동 전환
- `current_status == "additional_work_done"` → `additional_work` 자동 회귀
- 의사결정 로그 자동 기재 (§2.17 트리거 #5)
- `--note`의 `{owner_name}` 플레이스홀더는 identity.md `owner_name`으로 write-time 치환된다. 부재/공란/파싱 실패 시 원문 유지(fail-safe) — 054

**성공 응답**:
```json
{"ok": true, "command": "add-row", "row_id": 11, "rows_count": 21, "current_status": "additional_work"}
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

## 에러 코드 카탈로그 (23종 SSOT — PLAN §2.18 E-1)

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

---

## 의존성

- `~/.opal/.venv/bin/python` — 표준 라이브러리만 사용 (`json`, `argparse`, `pathlib`, `subprocess`, `re`, `sys`, `datetime`, `os`)
- `~/.opal/tools/date/date.js` — KST 시점 취득 (node.js)
- `opal/tools/state-tool/schema/state.schema.json` — JSON Schema Draft-07 참조용

## 관련 문서

| 문서 | 경로 | 참조 이유 |
|------|------|---------|
| PLAN.md | `tasks/134-260501-opp-pipeline-state-tool/PLAN.md` | §2.1~§2.20 전체 설계 SSOT |
| TASK.md | `tasks/134-260501-opp-pipeline-state-tool/TASK.md` | T-1~T-13 기술 결정 |
| state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | JSON Schema Draft-07 |

## 변경이력

| 버전 | 일시 (KST) | 태스크 | 변경 내용 |
|------|-----------|--------|---------|
| v1.0 | 2026-05-01 | (134) | 최초 작성 |
| v1.1 | 2026-05-09 11:22 | (140) | 3-way 모드 지원: init --mode semi-agentic 추가, mark/validate semi-agentic 경계 게이트 문서화, 오류 #24/#25 추가 |
| v1.2 | 2026-07-10 13:15 | (054) | `resolve_owner_placeholder()` 신설 — note/reason의 `{owner_name}` 플레이스홀더를 identity.md `owner_name`으로 write-time 치환(fail-safe: 부재/공란/파싱실패 시 원문 유지). init/advance/mark/block/add-row/status 6경로 적용 |
| xlsx-tool 패턴 | `opal/tools/xlsx-tool/run.sh:1-12` | OPAL Tools 래퍼 패턴 |
