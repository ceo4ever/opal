# brain-schema — OPAL Project Brain SCHEMA 규약 요약

> 원본 SSOT: `opal/tools/brain-tool/templates/schema-template.md` (brain-tool init 시 `.opal/brain/SCHEMA.md`로 복사)
> 이 문서는 opal-brain 스킬 운용자를 위한 사람용 요약본이다.
> 설계 근거: `docs/proposals/opal-brain-design.md` §5, `tasks/015-260610-opp-opal-brain/PLAN.md` 결정7

---

## 1. 페이지 타입 (4종)

| type | 용도 | 저장 경로 |
|------|------|----------|
| `entity` | 코드 모듈·도구·스킬 등 구체적 구성요소 | `pages/entity/` |
| `concept` | 아키텍처 결정·설계 사상·WHY/HOW | `pages/concept/` |
| `flow` | 비즈니스·데이터·파이프라인 흐름 | `pages/flow/` |
| `synthesis` | 질의에서 파생된 분석·비교 페이지 (복리 누적) | `pages/synthesis/` |

---

## 2. frontmatter 필수 키

```yaml
---
type: entity          # 필수: entity | concept | flow | synthesis
title: state-tool     # 필수: 페이지 제목
created: 2026-06-10   # 필수: 생성 날짜 (YYYY-MM-DD)
updated: 2026-06-10   # 필수: 마지막 수정 날짜
status: active        # 필수: active | stale | draft
---
```

## 3. frontmatter 선택 키

```yaml
tags: [tool, pipeline, state]                            # 검색·분류 태그
sources: [code:opal/tools/state-tool/, task:013]         # 근거 출처
related: [[opal-harness]], [[pipeline-state]]             # 교차참조 링크
```

## 4. entity 페이지 추가 키 (@header 시드)

```yaml
module: state_tool          # @header module 필드
layer: util                 # @header layer 필드 (orchestrator|tool|pilot|core|util 등)
domain: opal-pipeline       # @header domain 필드
exports: [cmd_init, cmd_mark]  # @header exports 목록
source_ref: opal/tools/state-tool/state_tool.py  # 소스 파일 경로
header_synced: 2026-06-10   # 마지막 @header 동기화 시각
```

> **단방향 규칙**: @header → brain entity frontmatter 방향만. brain에서 코드를 역방향 수정 금지. 코드가 SSOT.

---

## 5. 네이밍 규칙

- 파일명: `kebab-case.md` (예: `state-tool-design.md`, `pipeline-flow.md`)
- 페이지명 = frontmatter `title`
- 링크는 파일명 기준: `[[state-tool-design]]`
- 타입별 디렉토리 강제: `pages/{type}/` — 다른 위치에 생성 금지

---

## 6. 링크 3종

| 유형 | 형식 | 예시 |
|------|------|------|
| 교차참조 | `[[페이지파일명]]` | `[[opal-harness]]` |
| 코드 참조 | `` `file_path:line` `` | `` `opal/tools/state-tool/state_tool.py:67` `` |
| 외부 소스 참조 | `[[source:source-id]]` | `[[source:karpathy-llm-wiki]]` |

---

## 7. index.md 구조 (brain-tool 자동 생성)

```markdown
# Project Brain Index
> 갱신: <brain-tool 자동>

## 도메인
- [[domain-pipeline]] — 파이프라인 오케스트레이션 (페이지 5)

## 개념
- [[state-tool-design]] — STATE 결정론적 집행 #tool #pipeline

## 엔티티
- [[opal-pilot-project]] — 범용 오케스트레이터

## 흐름
- [[opp-pipeline-flow]] — OPP 파이프라인 흐름

## 합성
- [[interactive-vs-agentic]] — 모드 비교 분석 (질의 2026-06-08 파생)
```

> index.md는 `brain-tool index`로만 갱신한다. LLM 직접 편집 금지.

---

## 8. log.md 구조 (append-only)

```markdown
## [2026-06-10 14:30 KST] init | brain 부트스트랩 — 핵심 엔티티 12개 시드
- 신규: [[state-tool]], [[brain-tool]], [[opal-pilot-project]]
- 출처: task:015

## [2026-06-10 15:00 KST] ingest | 태스크 015 CLOSE
- 신규: [[opal-brain-skill]], [[brain-tool-design]]
- 출처: task:015
```

> log.md는 `brain-tool log`로만 append한다. LLM 직접 편집 금지.

---

## 9. sources/ 구조 (외부 소스 전용)

```
.opal/brain/sources/
  <source-id>/
    raw.md        # wtm-agent/xlsx-tool/Read로 변환된 원본
    meta.yaml     # 출처 메타데이터
```

`meta.yaml` 필수 필드:
```yaml
url: https://example.com/article
collected_at: 2026-06-10
license: CC-BY-4.0  # 또는 unknown
```

> 내부 코드·문서는 `sources/`에 넣지 않는다 — git+code-scan이 SSOT. brain 페이지가 `file_path:line`으로 참조한다.

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-06-10 | 초기 작성 — SCHEMA 규약 사람용 요약 (페이지타입 4종·frontmatter 필수/선택/entity 추가 키·네이밍·링크 3종·index/log 구조·sources/) (015) |
