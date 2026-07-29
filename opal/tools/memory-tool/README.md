# memory-tool

OPAL 프로젝트 메모리 인덱스·히스토리 결정론적 집행 CLI.
`MEMORY.json` 단독 SSOT (v2.0, 078) — 9서브명령 `init/append/update/promote/prune/show/review/delete/task-number`.

> **원칙**: 메모리는 임시 보관소. 성숙한 지식은 `promote`로 영구 거처(`docs`/`brain`)로 졸업한다.
> **참조**: `opal/core/references/harness/memory-learning.md` — 형식·라이프사이클 SSOT

---

## 사용법

```bash
~/.opal/tools/memory-tool/run.sh <서브명령> [옵션]
# 또는 직접:
~/.opal/.venv/bin/python opal/tools/memory-tool/memory_tool.py <서브명령> [옵션]
```

모든 응답은 `{"ok": true|false, "command": "...", ...}` 단일라인 JSON.
`--file`은 **`MEMORY.json` 경로**를 가리킨다 (구 마커 포맷의 `MEMORY.md`가 아님 — 아래 [lazy 마이그레이션](#lazy-마이그레이션-md--json) 참조).

---

## MEMORY.json 스키마 요약

SSOT: `schema/memory.schema.json` (draft-07). 런타임에 `memory_tool.py`가 이 파일을 로드해 enum·제약을 파생한다.

```json
{
  "version": 1,
  "last_task_number": 78,
  "memories": [
    {"title": "...", "date": "YYYY-MM-DD", "type": "feedback", "status": "active", "file": "memory/<name>.md", "summary": "..."}
  ],
  "history": [
    {"title": "...", "date": "YYYY-MM-DD", "stage": "완료", "path": "tasks/.../", "result": "핵심결과"}
  ]
}
```

- `version`: 문서 스키마 버전(현재 `1`, 상한 초과 시 `unsupported_version`)
- `last_task_number`: 마지막 발급 태스크 번호 — `task-number` 서브명령 전용 필드
- `memories[]`: 메모리 인덱스 행. `type` enum: `project/architecture/feedback/preferences/issues/task/improvement`. `status` enum: `active/promoted/superseded/dead/candidate`. `summary` ≤80자 [MUST]
- `history[]`: 작업 히스토리 행(FIFO=5, 맨 앞=최신)
- `additionalProperties: false` — 스키마 외 키 삽입은 `schema_validation_failed`로 거부

---

## 서브명령

### `init` — MEMORY.json 생성

파일이 없으면 빈 문서(`version/last_task_number=0/memories=[]/history=[]`)로 생성. 이미 있으면 `--force` 없이는 거부.

```bash
run.sh init --file MEMORY.json [--force]
```

- `--force`: 이미 존재해도 재호출 허용 — 유효 JSON이면 재생성 없이 멱등 통과, 손상 JSON이면 `invalid_json`

에러: `already_initialized` | `invalid_json`

---

### `append` — 행 추가

메모리 인덱스 또는 히스토리에 행을 추가한다.

```bash
# 메모리 추가
run.sh append --file MEMORY.json --kind memory \
  --title "제목(≤30자 권고)" \
  --type feedback \
  --summary "요약(≤80자)" \
  [--status active]

# 히스토리 추가 (FIFO=5 자동 집행)
run.sh append --file MEMORY.json --kind history \
  --title "078 메모리 JSON 전환" \
  --summary "핵심결과" \
  [--stage "완료"] [--path "tasks/078-.../"]
```

에러: `title_required` | `invalid_kind` | `invalid_type` | `invalid_status` | `summary_too_long` | `schema_validation_failed`
갯수 제한: 없음 (캡틴 지시 2026-06-26 — R6 제외)

---

### `update` — 상태/요약 수정

```bash
run.sh update --file MEMORY.json --title "제목" \
  [--status dead|superseded|active|promoted|candidate] \
  [--summary "새 요약(≤80자)"] \
  [--new-title "새 제목"]
```

에러: `title_required` | `row_not_found` | `invalid_status` | `summary_too_long` | `schema_validation_failed`
dead/superseded 전이: 행 보존(삭제 아님), `show`(비-brief) 로드에는 포함되지만 `--brief`는 active만 반환.

---

### `promote` — 영구 거처 졸업 ★1순위

메모리를 `docs` 또는 `brain` 영구 거처로 이전 확인 후 인덱스 행 + `memory/<file>.md` 삭제.

```bash
run.sh promote --file MEMORY.json \
  --title "제목" \
  --to docs \
  --ref "AGENT.md#금지사항"
```

- `--to`: `docs` 또는 `brain`
- `--ref`: 영구 거처 위치 (필수 — 이전 미확인 시 거부, 무손실)

**brain 이관**: memory-tool은 brain에 직접 쓰지 않는다.
PM이 먼저 `//opbr ingest` / `brain-tool add-page`로 brain 페이지를 만든 후, `--to brain --ref <brain-page-slug>`로 호출.

에러: `invalid_promote_target` | `promote_ref_missing` | `title_required` | `row_not_found` | `memory_file_not_found` | `schema_validation_failed`
성공 응답: `{"ok": true, "row_removed": true, "file_deleted": true, "provenance_logged": true, ...}` (`.memory_provenance.log`에 추가 기록, 실패는 비치명적)

---

### `prune` — 히스토리 정리

히스토리를 FIFO=5로 정리한다. 이미 ≤5면 no-op.

```bash
run.sh prune --file MEMORY.json
```

---

### `show` — 현황 조회 (read-only)

```bash
run.sh show --file MEMORY.json
run.sh show --file MEMORY.json --brief
run.sh show --file MEMORY.json --history 5
```

- (인자 없음): `index_rows`(전체 memories) + `history_rows`(전체 history) + `version`/`last_task_number` 반환
- `--brief`: `status=="active"` 메모리만 5필드(`title/date/type/file/summary`)로 축약 반환(날짜 내림차순), 히스토리는 기본 최신 3건으로 절단
- `--history N`: 히스토리 반환 건수를 N으로 재정의(단독 지정도 가능, `--brief` 없이도 동작). 절단 발생 시 `history_truncated: true`

공통 응답 키(하위호환 유지, H-4): `index_rows`/`history_rows`/`active_count`/`total_count`/`history_count`/`migration`

---

### `review` — 자가검토

현황 분석 + 후보 표면화. 매 변경 명령(append/update/promote/prune/delete/task-number --bump|--set) 응답에도 자동 첨부.

```bash
run.sh review --file MEMORY.json
```

응답 구조:
```json
{
  "ok": true,
  "promote_candidates": [{"title": "...", "type": "...", "date": "..."}],
  "cleanup_candidates": [{"title": "...", "status": "dead"}],
  "history_status": {"fifo_trimmed": false, "count": 2},
  "violations": []
}
```

- `promote_candidates`: 오래된 active 행(≥30일) — 졸업 후보 (졸업지 단정 없음, PM 판단)
- `cleanup_candidates`: dead/superseded 행 — 정리 후보
- `violations`: 스키마 위반(요약 길이>80·enum 위반 등)

---

### `delete` — dead/superseded 행 물리 제거 (무손실 가드)

```bash
run.sh delete --file MEMORY.json --title "제목" [--with-file]
```

- `--with-file`: `memory/<file>.md`도 함께 삭제(경로 화이트리스트 검증 재사용)
- **무손실 가드 [MUST]**: `status`가 `dead`/`superseded`가 아닌 행(active/promoted)은 `delete_requires_dead_or_superseded`로 거부, 행 불변

에러: `title_required` | `row_not_found` | `delete_requires_dead_or_superseded` | `schema_validation_failed`

---

### `task-number` — last_task_number 조회·원자적 채번

`--file`은 MEMORY.json 경로. 태스크 번호 발급 SSOT.

```bash
run.sh task-number --file MEMORY.json            # 조회(파일 무변경)
run.sh task-number --file MEMORY.json --bump      # 원자적 +1
run.sh task-number --file MEMORY.json --set 80    # 복구·보정 (역행 거부)
```

- 인자 없음: 현재값 반환, 파일 락 없이 read-only
- `--bump`: 현재값+1로 원자적 갱신, `previous`/`bumped: true` 포함
- `--set N`: 지정값으로 강제 설정 — 현재값보다 작으면 `task_number_regression`으로 거부(무손실)
- `--bump`와 `--set` 동시 지정: `invalid_args`

에러: `invalid_args` | `task_number_regression` | `schema_validation_failed`

---

## lazy 마이그레이션 (md → json)

`load_document()`가 매 명령 진입 시 아래 조건에서 **자동 발동**한다 (별도 `migrate` 서브명령 없음 — v1.x의 `migrate`는 소멸).

**발동 조건**: `<file>.json`이 부재 **AND** 동일 이름 `.md`(`json_path.with_suffix(".md")`)가 존재.
둘 다 부재하면 `memory_json_not_found`로 거부(먼저 `init` 필요).

**절차**:
1. 구 마커 표(`memory:index:*`, `memory:history:*`)를 파싱해 `memories[]`/`history[]`로 변환(무손실 — truncate 금지, 초과분은 `[REVIEW]` 플래그)
2. 상태 매핑: `완료/~~완료~~` → `dead` | `폐기 기록/폐기` → `superseded` | `대기/유지` → `active` (매핑 실패 값은 `unmapped_statuses`에 원문 보존)
3. `last_task_number`를 `MEMORY.md`/프로젝트 근거에서 해석 — 해석 실패 시 `0`으로 폴백(`last_task_number_source`에 해석 출처 또는 폴백 사유 기록)
4. 조립한 문서를 `validate_document()`로 검증 → 위반 시 `migration_failed`(원본 `.md` **무변경**, `.json` 미생성)
5. 통과 시 `atomic_write_json()`으로 `.json` 생성 → 원본 `.md`를 `.md.bak`으로 이동(**`.bak` 보존** — 이미 `.bak`이 있으면 타임스탬프 suffix로 충돌 회피, 손실 없음)
6. 락(`memory_lock`) 보유 상태에서 실행되므로 동시 호출 경쟁 없음

**실패 시 원본 무변경 [MUST]**: 표 파싱 행수 불일치·스키마 위반 등 어떤 이유로든 실패하면 `.md`는 그대로, `.json`은 생성되지 않는다 (부분 변환 금지).

**리포트 필드** (성공 시 응답의 `migration` 키에 포함, 마이그레이션 미발동 시 `migration: null`):

| 필드 | 의미 |
|------|------|
| `performed` | 이번 호출에서 마이그레이션이 실행됐는지 |
| `source` / `backup` | 원본 `.md` 경로 / `.bak` 이동 경로(`backup_failed`면 `null`) |
| `memories` / `history` | 변환된 행 수 |
| `review_flagged` | `[REVIEW]` 플래그가 붙은 행 수(길이 초과 등) |
| `unmapped_statuses` | 상태 매핑표에 없는 원문 상태값 목록(무손실 보존) |
| `last_task_number` / `last_task_number_source` | 해석된 번호 / 해석 근거(또는 폴백 사유) |
| `empty_source_regions` | 원본에 표가 없어 빈 배열로 처리된 영역(`memories`/`history`) |
| `dropped_history` | FIFO=5 절단으로 제외된 히스토리 제목 목록 |
| `backup_failed` | `.bak` 이동 실패 여부(비치명적 — `.json`은 이미 기록됨) |

---

## 라이프사이클

| 상태 | 의미 | 전환 방법 |
|------|------|----------|
| `active` | 살아있는 지식 | `append` 시 기본값 |
| `candidate` | 승격 검토 대기(improve-tool 위임 등) | `append --status candidate` |
| `promoted` | 영구 거처로 졸업 완료 | `promote --to docs\|brain` |
| `superseded` | 새 결정/메모리로 대체 | `update --status superseded` |
| `dead` | 완료·진부화 | `update --status dead` |

---

## 에러 코드

전체 SSOT는 `memory_tool.py`의 `ERROR_CODES` 딕셔너리.

| 코드 | 의미 |
|------|------|
| `memory_file_not_found` | `--file`에 해당하는 `memory/<file>.md`가 없음 (promote/delete --with-file) |
| `memory_json_not_found` | `MEMORY.json`도 `MEMORY.md`도 없음 — `init` 먼저 실행 |
| `invalid_json` | `MEMORY.json` 파싱 실패(손상된 JSON) |
| `unsupported_version` | 문서 `version`이 지원 상한을 초과 |
| `schema_validation_failed` | 문서가 스키마를 위반(파일 변경 없음, `violations[]` 참조) |
| `schema_load_failed` | 스키마 파일(`schema/memory.schema.json`) 로드 실패 — CLI 기동 자체 중단 |
| `schema_unsupported_keyword` | 검증기가 지원하지 않는 스키마 키워드 사용 |
| `migration_failed` | md→json 변환 실패(원본 `.md` 무변경, `.json` 미생성) |
| `lock_timeout` | 메모리 락 획득 시간 초과(다른 프로세스 점유 중) |
| `row_not_found` | `--title`에 해당하는 인덱스 행이 없음 |
| `already_initialized` | `MEMORY.json`이 이미 존재(`--force` 없이 `init`) |
| `invalid_kind` | `--kind`가 `memory`/`history` 외 값 |
| `invalid_type` | `--type`이 유형 enum에 없음 |
| `invalid_status` | `--status`가 라이프사이클 enum에 없음 |
| `invalid_date` | 날짜 형식이 `YYYY-MM-DD`가 아님 |
| `summary_too_long` | 요약 80자 초과(R2) — 상세는 개별 `.md` 본문으로 |
| `title_required` | `--title`이 필수 비공백 문자열 |
| `invalid_promote_target` | `--to`가 `docs`/`brain` 외 값 |
| `promote_ref_missing` | `--ref`(영구 거처 위치) 필수 — 이전 미확인 promote 거부(무손실, H-1) |
| `delete_requires_dead_or_superseded` | `delete`는 `dead`/`superseded` 행만 허용(무손실 가드) |
| `task_number_regression` | `--set`이 현재값보다 작음 — 채번 역행 거부(무손실) |
| `invalid_args` | 인자 조합이 올바르지 않음(예: `--bump`와 `--set` 동시 지정) |
| `date_tool_failed` | `node ~/.opal/tools/date/date.js` 호출 실패 |

---

## 변경이력

| 버전 | 태스크 | 내용 |
|------|--------|------|
| v1.0 | 045 | memory-tool 신설 — 8서브명령, 마커 가드, FIFO=5, promote 무손실+provenance, 자가검토 |
| v1.1 | 058 | VALID_TYPES에 `improvement`, VALID_STATUSES에 `candidate` 추가(additive) |
| v2.0 | 078 | MEMORY.json 단독 SSOT 전환 — 구 마커·표 파싱 계층 및 `migrate` 서브명령 소멸, lazy 자동 마이그레이션(md→json, `.bak` 보존) 신설, `task-number` 서브명령 신설, `show --brief`/`--history N` 추가, 스키마 런타임 검증(`schema/memory.schema.json`)·파일 락 기반 원자적 쓰기 도입 |
