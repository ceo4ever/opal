# backlog-tool

> oppl 2-루프 오케스트레이터의 백로그(backlog.json) SSOT 관리 CLI
> 소스: `opal/tools/backlog-tool/` | 배포: `~/.opal/tools/backlog-tool/`
> 설계 근거: `tasks/056-260710-opd-oppl-루프-오케스트레이터/PLAN.md` §3.1

## 개요

`backlog-tool`은 oppl(설계 루프 → 실행 루프) 오케스트레이터가 태스크 백로그를 `backlog.json`(단일 진실 공급원)으로 관리하고, 7개 서브 명령으로만 갱신 가능하게 만들어 LLM의 절차 우회/오갱신을 차단한다. `state-tool`과 동일한 아키텍처 패턴(래퍼 → venv python → ok/err 단일라인 JSON → date.js KST 시점 → 마크다운 마커 렌더)을 복제한다.

- **SSOT**: `backlog.json` (마크다운 표는 도구가 자동 렌더한 미러)
- **마커**: `<!-- backlog:start -->` ~ `<!-- backlog:end -->` (BACKLOG.md 내 백로그 표 영역 경계)
- **출력 형식**: 모든 응답은 단일 라인 JSON
- **축 분리**: `state.json`(파이프라인 현황판) / `test-scenario.json`(테스트 시나리오)과 상호 참조하지 않는다

## 호출 형식

```bash
~/.opal/tools/backlog-tool/run.sh <command> <task-path> [options]
```

> 개발 중에는 소스 경로로 직접 호출:
> `bash opal/tools/backlog-tool/run.sh <command> <task-path> [options]`

## 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | 성공 |
| `1` | 검증 위반 / not_found / 상태 전이 위반 |
| `2` | 내부 오류 (date.js subprocess 실패) |

## 7개 서브 명령

### 1. `init` — backlog.json + BACKLOG.md 생성

```bash
~/.opal/tools/backlog-tool/run.sh init <task-path> \
  --project-title <text> \
  --mode <interactive|semi-agentic|agentic> \
  [--goal <text>] \
  [--force]
```

- 멱등 검증: 이미 존재하면 `already_initialized` + exit 1 (`--force`로 우회, 기존 `created_at`/`tasks` 보존)
- `tasks: []`로 빈 백로그 생성

**성공 응답 예시**:
```json
{"ok": true, "command": "init", "task_path": "/path/to/task", "created_at": "2026-07-10 16:34"}
```

---

### 2. `add-task` — tasks[] 추가 + BACKLOG.md 재렌더

```bash
~/.opal/tools/backlog-tool/run.sh add-task <task-path> \
  --id <T01> \
  --title <text> \
  --slice <text> \
  --acceptance '["AC1", "AC2"]' \
  --area <fe|be|db|공통|통합> \
  --priority <P0|P1|P2> \
  [--depends <T01,T02>] \
  [--parallel-group <group-id>]
```

- `--acceptance`는 JSON 배열 문자열 — 파싱 실패 시 `acceptance_invalid_json`
- 중복 `--id` → `task_id_exists`
- `--depends`에 존재하지 않는 task id → `dependency_not_found`
- 신규 태스크는 `status: "pending"`, `done_at: null`로 생성

**성공 응답**:
```json
{"ok": true, "command": "add-task", "task_id": "T01", "tasks_count": 1}
```

---

### 3. `select-next` — 의존 충족 + 우선순위 최상위 pending 태스크 반환

```bash
~/.opal/tools/backlog-tool/run.sh select-next <task-path>
```

- `depends[]`의 모든 항목이 `done` 상태인 `pending` 태스크 중 `priority`(P0 > P1 > P2) 최상위 반환
- 조건을 만족하는 태스크가 없으면 `next_task_id: null`

**성공 응답**:
```json
{"ok": true, "command": "select-next", "next_task_id": "T01", "task": {"id": "T01", "...": "..."}}
```

---

### 4. `mark` — 상태 전이

```bash
~/.opal/tools/backlog-tool/run.sh mark <task-path> \
  --id <T01> \
  --status <pending|in_progress|done|blocked> \
  [--note <text>]
```

허용 전이 그래프:
- `pending` → `in_progress` / `blocked`
- `in_progress` → `done` / `blocked` / `pending`
- `blocked` → `pending` / `in_progress`
- `done` → (없음 — 종결 상태. 재작업이 필요하면 신규 `add-task`로 새 슬라이스 생성)

위 그래프 외 전이 시도: `invalid_status_transition` + exit 1. 존재하지 않는 `--id` → `task_not_found`.
`status: "done"` 전환 시 `done_at`에 KST 시점 기록. `fcntl` 배타 락으로 read-modify-write를 직렬화해 동시 `mark` 호출 시 backlog.json 무손상을 보장한다 (H-3).

**성공 응답**:
```json
{"ok": true, "command": "mark", "task_id": "T01", "status": "done"}
```

---

### 5. `update-task` — 지정 필드만 tool-gated 수정 (056 ADD-3)

```bash
~/.opal/tools/backlog-tool/run.sh update-task <task-path> \
  --id <T01> \
  [--title <text>] \
  [--slice <text>] \
  [--acceptance '["AC1", "AC2"]'] \
  [--area <fe|be|db|공통|통합>] \
  [--priority <P0|P1|P2>] \
  [--depends <T01,T02>] \
  [--parallel-group <group-id>]
```

- **배경**: Evaluator(명세 심판)가 구현 전 태스크 속성(수용기준 등)에 지적을 남겼을 때, 기존에는 `backlog.json`을 직접 손편집하거나 `add-task`로 재등록하는 수밖에 없었다. `update-task`는 tool-gated로 지정 필드만 안전하게 수정하는 경로를 제공한다.
- 지정한 필드만 갱신(나머지는 불변) + `updated_at` 갱신 + `BACKLOG.md` 마커 영역 재렌더
- **가드**:
  - 최소 1개 필드 지정 필수 — 없으면 `no_fields_to_update`
  - `status`는 인자 자체가 없음 — 상태 전이는 `mark` 전용(명령 설계상 우회 불가)
  - 대상 태스크가 이미 `done` 상태면 수정 거부 — `task_already_done` (재작업이 필요하면 `add-task`로 새 슬라이스 생성)
  - `--id`에 해당하는 태스크가 없으면 `task_not_found`
  - `--acceptance` JSON 파싱 실패 시 `acceptance_invalid_json`
  - `--depends`에 존재하지 않는 태스크 id → `dependency_not_found` (add-task와 동일 에러코드 재사용)
  - `mark`와 동일하게 `fcntl` 배타 락으로 read-modify-write 직렬화(H-3)

**성공 응답**:
```json
{"ok": true, "command": "update-task", "task_id": "T01", "updated_fields": ["acceptance", "title"]}
```

---

### 6. `done-check` — 종료 판정

```bash
~/.opal/tools/backlog-tool/run.sh done-check <task-path>
```

- 전체 태스크 중 `done`이 아닌 항목을 `remaining[]`으로 반환
- `all_done`: 모든 태스크가 `done`이면 `true`

**성공 응답**:
```json
{"ok": true, "command": "done-check", "all_done": false, "remaining": ["T02"], "done_count": 1, "total": 2}
```

---

### 7. `show` — BACKLOG.md 렌더 또는 backlog.json raw 출력

```bash
~/.opal/tools/backlog-tool/run.sh show <task-path> [--format md|json]
```

| `--format` | 출력 내용 |
|-----------|----------|
| `md` (기본) | BACKLOG.md 마커 영역(백로그 표) |
| `json` | backlog.json raw |

- BACKLOG.md 마커 누락 시 backlog.json에서 표를 재구성해 fallback 출력 (`marker_present: false`)

---

## BACKLOG.md — 손편집 금지 미러

`BACKLOG.md`는 `backlog.json`을 도구가 렌더한 미러다. `<!-- backlog:start -->` ~ `<!-- backlog:end -->` 마커 구간만 `add-task`/`mark`/`update-task` 실행 시 재렌더되며, 마커 구간 밖의 자유 텍스트(메모, 설명 등)는 보존된다. 마커 구간 내부를 손으로 편집하면 다음 CUD 명령 실행 시 덮어써진다.

## 에러 코드 표 (ERROR_CODES SSOT)

| 코드 | 발생 명령 | 의미 |
|------|----------|------|
| `already_initialized` | init | backlog.json이 이미 존재(--force로 우회) |
| `backlog_not_initialized` | add-task/select-next/mark/update-task/done-check/show | backlog.json이 존재하지 않음(init 선행 필요) |
| `task_id_exists` | add-task | 이미 존재하는 task id |
| `task_not_found` | mark/update-task | `--id`에 해당하는 태스크가 없음 |
| `invalid_status_transition` | mark | status 전이 그래프 위반 |
| `dependency_not_found` | add-task/update-task | `--depends`에 지정된 태스크가 존재하지 않음 |
| `acceptance_invalid_json` | add-task/update-task | `--acceptance`가 유효한 JSON 배열이 아님 |
| `date_tool_failed` | 전체(시점 필요 명령) | date.js subprocess 호출 실패(원자성 — 파일 변경 없음) |
| `task_path_not_found` | 전체 | `<task-path>` 디렉토리가 존재하지 않음 |
| `no_fields_to_update` | update-task | 갱신할 필드를 1개도 지정하지 않음(056 ADD-3 신규) |
| `task_already_done` | update-task | 대상 태스크가 이미 `done` — 수정 거부(056 ADD-3 신규, 재작업은 add-task로) |

## 의존성

- `~/.opal/.venv/bin/python` — 표준 라이브러리만 사용 (`json`, `argparse`, `pathlib`, `subprocess`, `sys`, `os`, `fcntl`)
- `~/.opal/tools/date/date.js` — KST 시점 취득 (node.js)
- `opal/tools/backlog-tool/schema/backlog.schema.json` — JSON Schema Draft-07 참조용

## 관련 문서

| 문서 | 경로 | 참조 이유 |
|------|------|---------|
| PLAN.md | `tasks/056-260710-opd-oppl-루프-오케스트레이터/PLAN.md` | §3.1 전체 설계 SSOT |
| backlog.schema.json | `opal/tools/backlog-tool/schema/backlog.schema.json` | JSON Schema Draft-07 |
| state-tool README.md | `opal/tools/state-tool/README.md` | 아키텍처 패턴 원본 |

## 변경이력

| 버전 | 일시 (KST) | 태스크 | 변경 내용 |
|------|-----------|--------|---------|
| v1.0 | 2026-07-10 16:34 | (056) | 최초 작성 — 6서브명령(init/add-task/select-next/mark/done-check/show), state-tool 패턴 복제 |
| v1.1 | 2026-07-10 18:34 | (056 ADD-3) | `update-task` 서브명령 신설(7서브명령 체제) — Evaluator 지적 반영 시 손편집 없이 tool-gated로 태스크 속성 수정. 신규 에러코드 `no_fields_to_update`/`task_already_done` 추가. status는 인자 자체를 두지 않아 mark 전용 상태 전이 원칙 유지. 에러 코드 표 신설 |
