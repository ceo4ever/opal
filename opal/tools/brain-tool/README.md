# brain-tool

> OPAL Project Brain 지식 위키 결정론적 집행 CLI
> 소스: `opal/tools/brain-tool/` | 배포: `~/.opal/tools/brain-tool/`
> 설계 근거: `docs/proposals/opal-brain-design.md` §5·§7, `tasks/015-260610-opp-opal-brain/PLAN.md` 결정3·결정7

## 개요

`brain-tool`은 `.opal/brain/` 지식 위키의 `index.md`·`log.md`·링크 무결성·frontmatter 표준을 **결정론적으로 집행**한다 (enforce, don't advise). 페이지 본문은 LLM이 작성하되, 인덱싱·log append·frontmatter 검증은 도구가 전담해 절차 우회·오갱신을 차단한다 (state-tool 동형 철학).

- **SSOT**: `pages/` 하위 .md 파일 (index.md는 도구가 자동 렌더한 카탈로그)
- **출력 형식**: 모든 응답은 단일 라인 JSON (`"ok": true/false`)
- **frontmatter 파싱**: PyYAML (venv)
- **KST 타임스탬프**: `node ~/.opal/tools/date/date.js datetime` subprocess
- **단방향 동기화**: `sync-header`는 code-scan @header → brain entity frontmatter 방향만 (역방향 금지)

## 호출 형식

```bash
~/.opal/tools/brain-tool/run.sh <command> [options]
```

> 개발 중에는 소스 경로로 직접 호출:
> `bash opal/tools/brain-tool/run.sh <command> [options]`

## 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | 성공 |
| `1` | 위반 / 검증 실패 / 에러 |
| `2` | 내부 오류 (subprocess 실패 / 템플릿 부재) |

## 8개 서브 명령

### 1. `init` — brain 골격 생성

```bash
run.sh init <brain-path> [--force]
```

`.opal/brain/` 골격(pages/{entity,concept,flow,synthesis}, sources/) + SCHEMA.md·index.md·log.md를 생성한다.
이미 초기화된 경우 `brain_already_initialized`로 거부하며 `--force`로만 재초기화한다.

- `<brain-path>`: 프로젝트 디렉토리(자동으로 `.opal/brain` 부착) 또는 brain 루트 경로 직접 지정.
- 출력: `{ok, command:"init", created:[dirs], schema_written:true}`

### 2. `add-page` — 페이지 생성 + index 등록

```bash
run.sh add-page <path> --type <entity|concept|flow|synthesis> --title <..> [--tags a,b] [--sources x,y] [--brain-path .]
```

타입별 템플릿을 기반으로 페이지를 `pages/{type}/<name>.md`에 생성하고, frontmatter를 검증한 뒤 index.md를 재생성한다.

- 출력: `{ok, page, type, title, indexed:true}`
- 에러: `invalid_page_type`, `frontmatter_invalid`, `duplicate_page`

### 3. `index` — index.md 재생성

```bash
run.sh index [--brain-path .]
```

`pages/`를 스캔해 index.md를 카테고리(도메인/개념/엔티티/흐름/합성)별로 재생성한다.

- 출력: `{ok, pages_scanned:N, index_written:true, categories:{}}`

### 4. `log` — log.md append

```bash
run.sh log --op <ingest|init|lint|query> --summary <..> [--new a,b] [--updated x,y] [--sources s] [--brain-path .]
```

append-only log.md에 `## [날짜] op | 요약` 엔트리를 추가한다.

- 출력: `{ok, logged:true, timestamp:"<KST>"}`

### 5. `search` — 페이지 검색

```bash
run.sh search <query> [--type T] [--tag X] [--limit N] [--brain-path .]
```

frontmatter title·tags·본문을 검색해 점수순 관련 페이지를 반환한다 (PM 참조용).

- 출력: `{ok, matches:[{page, title, type, score, snippet}]}`
- 에러: `query_empty`

### 6. `sync-header` — @header 단방향 동기화

```bash
run.sh sync-header [--scope X] [--page P] [--brain-path .]
```

`.opal/code-scan.json` 기반으로 code-scan을 실행해 @header를 얻고, entity 페이지 frontmatter(module/layer/domain/exports)와 비교해 drift 시 **단방향**(코드→brain)으로 갱신한다. 코드가 사라진 entity는 stale 표시한다.

- 출력: `{ok, synced:[], drift:[{page, field, old, new}], stale_marked:[]}`
- 에러: `code_scan_json_missing`, `header_parse_failed`

### 7. `lint` — 무결성 점검

```bash
run.sh lint [--brain-path .]
```

고아·stale·끊어진 링크·누락 링크·근거 없는 페이지를 탐지한다.

- 출력: `{ok, issues:[{kind, page, detail}]}` (kind ∈ orphan/stale/broken_link/missing_link/unsourced/contradiction)

### 8. `validate` — 표준 검증

```bash
run.sh validate [--brain-path .]
```

brain 구조(필수 파일·디렉토리)와 페이지 frontmatter 표준 준수를 검증한다.

- 출력: `{ok, valid:bool, violations:[{page, rule, detail}]}`

## 집행 경계

- `index.md` / `log.md`는 **brain-tool로만** 갱신한다 (LLM 직접 편집 금지).
- 페이지 본문은 LLM 작성, 메타데이터·인덱싱은 도구 집행.
- `sync-header`는 단방향(code-scan @header → brain frontmatter)만 — 역방향 금지.

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-06-10 | 초기 구현 — 8 서브 명령(init/add-page/index/log/search/sync-header/lint/validate) (015) |
