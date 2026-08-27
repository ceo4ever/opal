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
run.sh add-page <path> --type <entity|concept|flow|synthesis> --title <..> [--tags a,b] [--sources x,y] [--related a,b] [--body-file <file>] [--force] [--note <사유>] [--brain-path .]
```

타입별 템플릿을 기반으로 페이지를 `pages/{type}/<name>.md`에 생성하고, frontmatter를 검증한 뒤 index.md를 재생성한다.

- `--body-file <file>`: 지정 시 템플릿 본문 대신 이 파일의 본문으로 페이지를 생성한다 — 미실체 게이트가 실제 본문(제목 + `#` 섹션 헤딩)을 스캔하는 대상이 된다. 미지정 시 기존 템플릿 본문 경로 그대로(하위호환).
- **미실체 지식 거부 게이트**: 본문(제목 + `#` 헤딩)에 미실체 마커(`미착수`·`미확정`·`향후계획`·`개선사항`·`todo` 등 — 아직 실재하지 않는 지식 신호)가 감지되면 등록을 거부한다(`speculative_content`). 산문은 스캔하지 않아 오검출을 최소화한다.
- `--force`: 미실체 거부를 우회한다. **`--note <사유>` 없이는 우회 불가**(백도어 차단) — `--force --note`를 함께 지정해야 통과한다.
- `--force --note` 통과 시: frontmatter에 `speculative_override: true`·`override_note: <사유>`를 영속 기재하고, 응답에 `warning:"speculative_content_overridden"`·`speculative_markers`·`override_note`를 포함한다.
- 출력: `{ok, page, type, title, indexed:true}` (override 통과 시 `warning`·`speculative_markers`·`override_note` 추가)
- 에러: `invalid_page_type`, `frontmatter_invalid`, `duplicate_page`, `speculative_content`

### 2b. `update-page` — 기존 페이지 갱신

```bash
run.sh update-page <path> [--title ..] [--tags a,b] [--sources x,y] [--related a,b] [--status ..] [--body-file <file>] [--force] [--note <사유>] [--brain-path .]
```

`add-page`가 `duplicate_page`로 거부하는 **기존 페이지 갱신의 유일한 도구 경로**다. 이 경로가 없으면 갱신 지시를 받은 LLM이 `.md`를 직접 편집하게 되고, 손으로 쓴 frontmatter가 `related` 중첩 리스트로 붕괴한다.

- 대상 탐색: 슬러그(`my-page`) 또는 `pages/<type>/<name>.md` 어느 쪽으로도 지목 가능. 타입 디렉토리를 순회해 찾는다.
- **부분 갱신**: 지정한 필드만 바뀐다. 미지정 필드는 그대로 둔다.
- `created`는 보존하고 `updated`만 오늘(KST)로 갱신한다.
- `add-page`와 동일한 frontmatter 계약을 집행한다 — `related`에 `[[ ]]`·`.md`·중첩 리스트가 있으면 `frontmatter_invalid`로 거부한다.
- `--body-file` 지정 시에만 미실체 게이트를 재판정한다(본문이 바뀐 경우에만).
- title 변경은 index.md에 반영된다(갱신 후 index 자동 재생성).
- 출력: `{ok, page, type, title, updated_fields:[...], indexed:true}`
- 에러: `page_not_found`, `no_update_fields`, `frontmatter_invalid`, `speculative_content`

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

- **공백 무시 매칭**: 한국어 복합명사의 띄어쓰기 편차를 흡수하기 위해 검색 시점에 쿼리·대상(title·파일명·tags·본문) 양쪽의 공백을 제거한 휘발성 사본으로 비교한다. `"자동 취소"`와 `"자동취소"`가 동일하게 매칭된다. 저장 문서는 변형하지 않으며, 스니펫은 원문(공백 포함) 그대로 노출한다. 부분문자열 포함 방향은 유지되어 짧은 쿼리는 넓게, 긴 쿼리는 좁게 잡힌다.
- 출력: `{ok, matches:[{page, title, type, score, snippet}]}`
- 에러: `query_empty`

### 6. `sync-header` — @header 단방향 동기화

```bash
run.sh sync-header [--scope X] [--page P] [--brain-path .]
```

`.opal/code-scan.json` 기반으로 code-scan을 실행해 @header를 얻고, entity 페이지 frontmatter(module/layer/domain/exports)와 비교해 drift 시 **단방향**(코드→brain)으로 갱신한다. 코드가 사라진 entity는 stale 표시한다.

이때 참조하는 "code-scan @header"는 이제 소스 파일 인라인 주석과 `.opal/code-map/` 외부 매니페스트 2소스를 함께 의미한다.

- 출력: `{ok, synced:[], drift:[{page, field, old, new}], stale_marked:[]}`
- 에러: `code_scan_json_missing`, `header_parse_failed`

### 7. `lint` — 무결성 점검

```bash
run.sh lint [--brain-path .]
```

고아·stale·끊어진 링크·누락 링크·근거 없는 페이지·미실체 지식을 탐지한다.

- 출력: `{ok, issues:[{kind, page, detail}]}` (kind ∈ orphan/stale/broken_link/missing_link/unsourced/contradiction/speculative)
- `speculative`: 미실체 마커(섹션 헤딩) 소급 검출 — `add-page` 경로와 무관하게 이미 등록된 페이지의 본문을 스캔한다. 검출까지만 수행하며 자동 삭제·수정은 하지 않는다(`speculative_override` 기재 페이지도 계속 리포트).

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
| v1.13 | 2026-08-27 | `update-page` 신설 + `lint` frontmatter 검사 편입 — (1) 기존 페이지 갱신 도구 경로 부재가 LLM 직접 편집을 강제했고 그때 `related`가 중첩 리스트로 붕괴했다(9페이지 실측). `update-page`가 부분 갱신·`created` 보존·`updated` 자동 갱신을 집행하며 `add-page`와 동일한 frontmatter·미실체 계약을 적용한다. 에러 2종 신설(`page_not_found`·`no_update_fields`). (2) `cmd_lint`가 `validate_frontmatter`를 호출해 `frontmatter_invalid` kind를 표면화한다 — 종전에는 붕괴된 `related`가 `missing_link`라는 다른 이름으로 뭉개져 원인이 3회차 정비까지 가려졌다. `related` 붕괴 페이지의 `missing_link` 중복 보고는 억제한다. 테스트 127→142 |
| v1.0 | 2026-06-10 | 초기 구현 — 8 서브 명령(init/add-page/index/log/search/sync-header/lint/validate) (015) |
| v1.1 | 2026-06-16 18:15 | search 공백 무시 매칭 — 한국어 복합명사 띄어쓰기 편차 흡수(검색 시점 정규화, 저장 문서 불변, 스니펫 원문 노출) (025) |
| v1.2 | 2026-07-23 10:15 | 미실체 지식 등록 차단 게이트 — add-page에 `--body-file`(실제 본문 스캔)·`--force`·`--note`(우회, note 필수) 추가 + `speculative_content` 에러(거부/우회 시 frontmatter `speculative_override`·`override_note` 기재) + lint에 `speculative` kind 추가(소급 검출, 비파괴) (071) |
| v1.3 | 2026-07-28 23:28 | `sync-header` 절에 "code-scan @header"가 인라인 주석 + `.opal/code-map/` 외부 매니페스트 2소스를 함께 의미한다는 1문장 추가. 단방향 동기화 계약 문언은 불변 (077) |
