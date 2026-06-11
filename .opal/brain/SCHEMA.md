# Project Brain SCHEMA

> brain의 "헌법" — 모든 페이지가 따르는 규약. `//opbr init` 시 프로젝트별로 복사 생성된다.
> 근거: `docs/proposals/opal-brain-design.md` §5, PLAN 결정7

본 SCHEMA는 Karpathy llm-wiki 사상("영속·복리 지식 아티팩트")을 OPAL 네이티브로 구현한 위키 규약이다.
페이지 본문은 LLM이 작성하되, `index.md`·`log.md`·인덱싱·frontmatter 검증은 **brain-tool이 집행**한다 (enforce, don't advise).

---

## 1. 디렉토리 구조

```
.opal/brain/
  SCHEMA.md            # 본 규약 (페이지 포맷·네이밍·링크 규칙)
  index.md             # 카테고리별 카탈로그 (도메인/개념/엔티티/흐름/합성)
  log.md               # append-only ingest 연대기
  pages/
    entity/            # 코드 엔티티 페이지 (모듈·서비스·도구·스킬)
    concept/           # 개념·아키텍처 결정 페이지 (왜 이렇게 설계했나)
    flow/              # 비즈니스·데이터·파이프라인 흐름 페이지
    synthesis/         # 질의에서 파생된 분석·비교 페이지 (복리 누적)
  sources/             # 외부 소스 원본 보관 (웹·PDF·이미지·제공 자료)
    <source-id>/
      raw.md           # 변환된 원본 (web-to-markdown/xlsx-tool 산출)
      meta.yaml        # 출처 URL·수집일·라이선스
```

> 내부 코드/문서는 `sources/`에 넣지 않는다 — git + code-scan이 SSOT. brain 페이지가 `file_path:line`으로 참조한다.

---

## 2. 페이지 frontmatter 표준

모든 페이지는 YAML frontmatter로 시작한다.

### 2.1 필수 키 (모든 페이지)

| 키 | 타입 | 설명 |
|----|------|------|
| `type` | enum | 페이지 타입 — `entity` \| `concept` \| `flow` \| `synthesis` |
| `title` | string | 페이지 제목 (한국어 가능) |
| `created` | date | 생성일 `YYYY-MM-DD` |
| `updated` | date | 최종 갱신일 `YYYY-MM-DD` |
| `status` | enum | 페이지 상태 — `active` \| `stale` \| `draft` |

### 2.2 선택 키 (모든 페이지)

| 키 | 타입 | 설명 |
|----|------|------|
| `tags` | string[] | 분류 태그 (예: `[tool, pipeline]`) |
| `sources` | string[] | 근거 출처 (예: `[code:opal/tools/state-tool/, task:013]`) |
| `related` | string[] | 교차참조 페이지 파일명 (예: `[opal-harness, pipeline-state]`) |

### 2.3 entity 추가 키 (@header 시드)

entity 페이지는 빈 페이지로 시작하지 않는다. `code-scan.json`이 파싱한 **@header 메타블록을 frontmatter 시드로 흡수**한다.
단방향 동기화: 코드 @header가 SSOT, brain은 스냅샷 + 누적 지식. brain→코드 역방향 갱신은 금지한다.

| 키 | 타입 | 설명 |
|----|------|------|
| `module` | string | @header `module` 시드 |
| `layer` | string | @header `layer` 시드 |
| `domain` | string | @header `domain` 시드 |
| `exports` | string[] | @header `exports` 시드 |
| `source_ref` | string | 코드 파일 경로 (예: `opal/tools/state-tool/state_tool.py`) |
| `header_synced` | date | 마지막 @header 동기화 시각 `YYYY-MM-DD` |

### 2.4 예시 (entity)

```yaml
---
type: entity
title: state-tool
module: state_tool
layer: util
domain: opal-pipeline
exports: [cmd_init, cmd_mark, cmd_advance]
source_ref: opal/tools/state-tool/state_tool.py
header_synced: 2026-06-10
tags: [tool, pipeline]
sources: [code:opal/tools/state-tool/, task:013, task:014]
related: [opal-harness]
created: 2026-06-10
updated: 2026-06-10
status: active
---
```

> `@header` = 구조(WHAT), brain 본문 = 이유·관계·결정(WHY/HOW). 코드 본문은 복제하지 않고 `source_ref`로 참조한다.

---

## 3. 네이밍 규칙

- 파일명: `kebab-case.md` (예: `state-tool-design.md`)
- 페이지명 = frontmatter `title`, 링크는 **파일명 기준** `[[state-tool-design]]`
- 타입별 디렉토리 강제: `pages/{type}/` (`type` ∈ entity/concept/flow/synthesis)
- 언어: 문서 본문=한국어, frontmatter 키·코드 식별자=English

---

## 4. 링크 규칙 (3종)

| 종류 | 형식 | 용도 |
|------|------|------|
| 교차참조 | `[[페이지파일명]]` | brain 페이지 간 연결 (Obsidian 호환) |
| 코드참조 | `` `file_path:line` `` | 코드 SSOT 참조 (OPAL 클릭 가능 형식) |
| 외부소스참조 | `[[source:source-id]]` | `sources/<id>/` 외부 원본 참조 |

---

## 5. index.md 구조

`index.md`는 brain-tool이 `pages/`를 스캔해 자동 재생성한다 (LLM 직접 편집 금지).
카테고리: **도메인 / 개념 / 엔티티 / 흐름 / 합성**.

```markdown
# Project Brain Index
> 갱신: <brain-tool 자동>

## 도메인
- [[domain-pipeline]] — 파이프라인 오케스트레이션

## 개념
- [[state-tool-design]] — STATE 결정론적 집행 #tool #pipeline

## 엔티티
- [[opal-pilot-project]] — 범용 오케스트레이터

## 흐름
- [[close-ingest-flow]] — CLOSE 자동 ingest 흐름

## 합성
- [[interactive-vs-agentic]] — 모드 비교 분석 (질의 2026-06-08 파생)
```

---

## 6. log.md 구조 (append-only)

`log.md`는 brain-tool `log`가 타임스탬프와 함께 append한다 (LLM 직접 편집 금지).

```markdown
## [2026-06-10] ingest | 태스크 015 CLOSE — opal-brain 신설
- 신규: [[opal-brain-skill]], [[brain-tool]]
- 갱신: [[index]], [[opal-harness]]
- 출처: task:015
```

---

## 7. 집행 규칙 (brain-tool)

- `index.md` / `log.md`는 **brain-tool로만** 갱신한다 (LLM 마크다운 직접 편집 금지).
- 페이지 본문은 LLM 작성, 메타데이터·인덱싱은 도구가 집행한다.
- 출력은 JSON (`"ok": true/false`), 에러는 ERROR_CODES 카탈로그 키만 사용한다.
- `sync-header`는 단방향(code-scan @header → brain entity frontmatter)만 수행한다 — 역방향 금지.
