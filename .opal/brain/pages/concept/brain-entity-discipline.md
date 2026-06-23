---
type: concept
title: brain entity 작성 규율 표준화
tags: [brain, knowledge, curation, provenance]
sources: [task:038]
related: [brain-tool, opal-brain-skill, citation-rules]
created: 2026-06-23
updated: 2026-06-23
status: active
---

## 개요

brain의 entity 페이지 품질을 보장하기 위해 **5섹션 표준 구조 + 입력 큐레이션 선행 + provenance 3종 태깅**으로 작성 규율을 표준화했다. code-scan @header의 기계 전사에서 벗어나 설계 의도(WHY)와 관계(HOW)를 사고하여 합성하도록 강제한다.

## 결정 배경 (WHY)

- **문제**: `//opbr init` 시드 과정에서 코드 @header를 기계 전사하여 entity가 WHAT 덤프로 전락한다. 특히 MAMS 프로젝트의 Google Ads API entity가 코드 식별자·enum·DTO 나열로 채워져 brain의 "지식 아티팩트(WHY/HOW)" 취지를 위반했다 (근거: task:038 TASK.md §배경).

- **근본 원인**: 입력이 코드만이면 WHY 정보가 부재하므로, 큐레이션 없이는 합성 불가다. pointail의 좋은 사례(`advertiser-admin-management.md`)는 정책서·cross-repo 코드·task PLAN을 sources에 주입해 진정한 WHY가 나온다 (근거: task:038 TASK.md §배경 분석).

- **설계 원칙**: OPAL 헌법 "Enforce, don't just advise"와 "Don't fake it" — SKILL 절차와 provenance 태깅으로 집행하며, 도구 게이트는 의미 판정 불가라 미채택 (근거: task:038 PLAN.md §3.2.2).

## 결정 내용

#### 5섹션 표준 구조

| # | 섹션 | 역할 | 작성 규율 |
|----|------|------|---------|
| 1 | `## 개요` | 비즈니스 프레이밍 | 비즈니스 용어 우선. 코드 식별자 본문 주어 금지 (`citation-rules:§8.2`) |
| 2 | `## 책임 (WHAT)` | 노출 인터페이스 | 각 책임에 `` `file_path:line` `` 인용 병기 |
| 3 | `## 설계 배경 (WHY)` | 설계 의도·대안·맥락 | 각 주장에 provenance 3종 중 하나 태깅 [MUST] |
| 4 | `## 관계 (HOW)` | 의존·협력 엔티티 | wikilink `[[페이지명]]` 사용 |
| 5 | `## 소스 커버리지` | 코드 식별자 부록 | line number 포함 표로 분리 (`citation-rules:§8.8`) |

#### @header 전사 금지 [MUST]

code-scan @header(module/layer/domain/exports)를 본문 1~4섹션에 기계 복사하지 않는다. @header는 frontmatter와 소스 커버리지 부록에만 둔다. 본문은 **사고하여 합성**한다 (근거: `~/.opal/PRINCIPLES.md` "Don't fake it").

#### provenance 3종 규칙 [MUST]

`## 설계 배경 (WHY)`의 각 주장 문장은 다음 중 하나를 태깅한다:

- `(근거: <doc>/POL-N/task:NNN PLAN§X)` — 문서·정책·태스크에서 확인된 WHY
- `(추론: 코드패턴)` — 코드 구조에서 추론한 WHY (단정 금지)
- `(WHY 미확보)` — WHY 입력이 없어 미확보 (솔직 표기 — 날조 금지)

#### 입력 큐레이션 선행 절차 [MUST]

entity 작성 **전**에 WHY 소스를 큐레이션한다:

1. `docs/PROJECT.md` 문서 레지스트리에서 관련 docs 확인
2. 관련 태스크 `tasks/NNN/PLAN.md` 설계 결정 확인
3. 관련 기존 brain 페이지(concept/entity) 후보 확인
4. 위 입력에서 WHY를 합성. WHY가 없으면 `(추론: 코드패턴)` 또는 `(WHY 미확보)`로 표기

## 영향 범위

- **초기화 경로**: `//opbr init` 시드 과정의 entity 작성 규율 (`opal/skills/opal-brain/SKILL.md`)
- **누적 경로**: CLOSE 단계 ingest entity 작성 규율 (`opal/skills/op-brain-ingest/SKILL.md`)
- **문서 표준**: citation-rules §8.2(코드 식별자 본문 주어 금지)·§8.8(부록 분리) 명문화
- **기존 데이터**: 저품질 entity는 프로젝트별 재생성 런북으로 처리 (소급 보정 미구현)

## 관련 페이지

- [[brain-tool]] — entity 페이지 관리·ingest 도구
- [[opal-brain-skill]] — brain init 시드 및 분석 스킬
- [[citation-rules]] — §8 비즈니스 용어 우선 및 부록 분리 규칙
