# memory-tool

OPAL 프로젝트 메모리 인덱스·히스토리 결정론적 집행 CLI.  
8서브명령 `init/append/update/promote/prune/migrate/show/review`.

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

---

## 서브명령

### `init` — 마커 삽입

MEMORY.md에 신포맷 마커·헤더·빈 표를 삽입한다. 파일이 없으면 생성.

```bash
run.sh init --file MEMORY.md [--force]
```

- `--force`: 마커가 이미 있어도 재삽입

에러: `already_initialized` (마커 존재 + --force 없음)

---

### `append` — 행 추가

메모리 인덱스 또는 히스토리에 행을 추가한다.

```bash
# 메모리 추가
run.sh append --file MEMORY.md --kind memory \
  --title "제목(≤30자)" \
  --type feedback \
  --summary "요약(≤80자)" \
  [--status active]

# 히스토리 추가 (FIFO=5 자동 집행)
run.sh append --file MEMORY.md --kind history \
  --title "045 메모리 관리 개선" \
  --summary "핵심결과" \
  [--stage "완료"] [--path "tasks/045-.../"]
```

에러: `marker_missing` | `summary_too_long` | `invalid_type` | `invalid_status`  
갯수 제한: 없음 (캡틴 지시 2026-06-26 — R6 제외)

---

### `update` — 상태/요약 수정

```bash
run.sh update --file MEMORY.md --title "제목" \
  [--status dead|superseded|active|promoted] \
  [--summary "새 요약(≤80자)"]
```

에러: `row_not_found` | `invalid_status` | `summary_too_long`  
dead/superseded 전이: 행 보존(삭제 아님), 로드 제외.

---

### `promote` — 영구 거처 졸업 ★1순위

메모리를 `docs` 또는 `brain` 영구 거처로 이전 확인 후 삭제.

```bash
run.sh promote --file MEMORY.md \
  --title "제목" \
  --to docs \
  --ref "AGENT.md#금지사항"
```

- `--to`: `docs` 또는 `brain`
- `--ref`: 영구 거처 위치 (필수 — 이전 미확인 시 거부, 무손실)

**brain 이관**: memory-tool은 brain에 직접 쓰지 않는다.  
PM이 먼저 `//opbr ingest` / `brain-tool add-page`로 brain 페이지를 만든 후, `--to brain --ref <brain-page-slug>`로 호출.

에러: `promote_ref_missing` | `memory_file_not_found` | `row_not_found`  
성공 응답: `{"ok": true, "row_removed": true, "file_deleted": true, "provenance_logged": true, ...}`

---

### `prune` — 히스토리 정리

히스토리를 FIFO=5로 정리한다. 이미 ≤5면 no-op.

```bash
run.sh prune --file MEMORY.md
```

---

### `migrate` — 구포맷 변환

구포맷(`| 등록일시 | 카테고리 | 상태 | 파일 | 설명 |`) → 신포맷 변환.

```bash
run.sh migrate --file MEMORY.md
```

- 제목 자동 추출 (첫 문장/30자) + `[REVIEW]` 플래그
- 상태 매핑: `완료/~~완료~~` → `dead` | `폐기 기록/폐기` → `superseded` | `대기/유지` → `active`
- truncate 금지 — 길이 초과는 `[REVIEW]` 플래그 (무손실, H-5)
- FIFO=5 적용

에러: `import_failed` (구포맷 표 파싱 0건)

---

### `show` — 현황 조회 (read-only)

```bash
run.sh show --file MEMORY.md
```

---

### `review` — 자가검토

현황 분석 + 후보 표면화. 매 변경 명령 응답에도 자동 첨부.

```bash
run.sh review --file MEMORY.md
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
- `violations`: 마커 누락·요약 길이>80·enum 위반

---

## 마커 규약

```markdown
## 메모리
<!-- memory:index:start -->
| 제목 | 등록일 | 유형 | 상태 | 파일 | 요약 |
|------|--------|------|------|------|------|
<!-- memory:index:end -->

## 작업 히스토리 (최대 5개, FIFO)
<!-- memory:history:start -->
| 제목 | 등록일 | 단계 | 경로 | 핵심결과 |
|------|--------|------|------|----------|
<!-- memory:history:end -->
```

**[MUST]** 마커 부재 시 모든 변경 명령(`append`/`update`/`promote`/`prune`)은 `marker_missing`으로 거부한다.  
MEMORY.md 직접 편집 금지 — memory-tool로만 수정.

---

## 라이프사이클

| 상태 | 의미 | 전환 방법 |
|------|------|----------|
| `active` | 살아있는 지식 | `append` 시 기본값 |
| `promoted` | 영구 거처로 졸업 완료 | `promote --to docs\|brain` |
| `superseded` | 새 결정/메모리로 대체 | `update --status superseded` |
| `dead` | 완료·진부화 | `update --status dead` |

---

## 변경이력

| 버전 | 태스크 | 내용 |
|------|--------|------|
| v1.0 | 045 | memory-tool 신설 — 8서브명령, 마커 가드, FIFO=5, promote 무손실+provenance, 자가검토 |
