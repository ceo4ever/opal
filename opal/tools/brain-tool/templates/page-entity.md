---
type: entity
title: "<엔티티 제목>"
module: "<code-scan @header module>"
layer: "<code-scan @header layer>"
domain: "<code-scan @header domain>"
exports: []
source_ref: "<코드 파일 경로 — 예: opal/tools/state-tool/state_tool.py>"
header_synced: "<YYYY-MM-DD>"
tags: []
sources: []
related: []
created: "<YYYY-MM-DD>"
updated: "<YYYY-MM-DD>"
status: draft
---

<!-- [MUST] code-scan @header를 본문에 기계 복사 금지 — frontmatter + 소스 커버리지에만.
     본문(개요·책임·설계 배경·관계)은 사고하여 합성한다. @header의 exports/description을
     그대로 붙여넣는 것은 WHAT 덤프이며 brain 품질 위반이다. (citation-rules §8.2) -->

## 개요

<!-- 비즈니스 프레이밍: 이 엔티티가 무엇이고 왜 존재하는지 1~3문장으로 서술한다.
     비즈니스 용어 우선. 코드 식별자(함수명·클래스명·모듈명)를 본문 주어로 쓰지 않는다.
     예) "X는 Y 목적을 위해 Z 역할을 담당하는 레이어다." (citation-rules §8.2) -->

<이 엔티티가 무엇이고 왜 존재하는지 1~3문장 — 비즈니스 용어로>

## 책임 (WHAT)

<!-- 노출 인터페이스·책임을 기능 단위로 서술한다.
     각 책임 항목에 `file_path:line` 인용을 병기한다. (citation-rules §8.4)
     §8.9 비위반 근거: 주 헤딩은 도메인 의미("책임"), WHAT은 괄호 보조 레이블 — `## 무엇을` 형식 아님. -->

<기능 단위 책임 서술 — 각 항목에 `file_path:line` 인용 병기>

## 설계 배경 (WHY)

<!-- 왜 이렇게 설계했는가 — 결정·기각된 대안·맥락을 서술한다.
     각 주장에 provenance 3종 중 하나를 반드시 태깅한다 [MUST]:
       (근거: <doc>/POL-N/task:NNN PLAN§X)  — 문서·정책·태스크에서 확인된 WHY
       (추론: 코드패턴)                      — 코드 구조에서 추론한 WHY (직접 근거 없음)
       (WHY 미확보)                          — WHY 입력 없음, 솔직 표기 (날조 금지)
     HOW 누수 금지: 관계·의존 서술은 §관계 (HOW)로 이동한다.
     §8.9 비위반 근거: 주 헤딩은 "설계 배경", WHY는 괄호 보조 레이블 — `## 왜` 형식 아님. -->

<설계 결정·기각 대안·맥락 — 각 주장에 provenance 태그 필수>

## 관계 (HOW)

<!-- 의존·피의존·협력 엔티티를 wikilink로 서술한다.
     wikilink 형식: 이중 대괄호 + 파일명 슬러그 (SCHEMA §4 링크 규칙 — 파일명 기준).
     §8.9 비위반 근거: 주 헤딩은 "관계", HOW는 괄호 보조 레이블 — `## 어떻게` 형식 아님. -->

<의존·피의존·협력 엔티티를 wikilink 형식으로 서술>

## 소스 커버리지

<!-- 코드 식별자·enum·exports를 line number 포함 부록으로 분리한다.
     본문(개요·책임·설계 배경·관계)에서 강등 배치. (citation-rules §8.8)
     형식: `file_path:line` — 예) `opal/tools/brain-tool/brain_tool.py:42`
     코드 본문은 복제하지 않는다. -->

<`file_path:line` 형식으로 핵심 진입점·exports 목록 — line number 포함>
