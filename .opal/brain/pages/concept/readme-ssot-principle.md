---
type: concept
title: README는 SSOT를 따른다 — 문서·코드 불일치 시 SKILL.md가 정본
tags: [readme, ssot, doc-code-mismatch, documentation]
sources: [task:018]
related: [opsdd-pipeline-ssot, uncommitted-component-readme-policy]
created: 2026-06-12
updated: 2026-06-12
status: active
---

## 개요

README.md의 내용은 레지스트리·하네스·각 SKILL.md·PROJECT.md를 근거로만 작성한다. 문서와 코드(SKILL.md 등) 간 불일치가 발생하면 SKILL.md가 정본이며, README는 SKILL.md 표기를 따른다.

## 결정 배경 (WHY)

task:018(README 최신화)에서 opsdd 파이프라인 표기가 레지스트리·PROJECT.md·SKILL.md 세 곳에서 상충함이 발견됐다(TASK §B-2). OPAL 헌법 citation-rules §0 '상상·추정 금지' 원칙 및 TASK §제약 'SSOT 우선'에 따라, 코드 구현의 실제 동작을 기술하는 SKILL.md를 최고 권위 SSOT로 확정했다.

## 결정 내용

- README는 레지스트리·하네스·각 SKILL.md·PROJECT.md를 Read 전용 SSOT로 사용한다.
- 상충 시 우선순위: SKILL.md > PROJECT.md > 레지스트리 (구현 정본 원칙).
- 상상·추정 기재 금지 — 모든 신규 내용은 SSOT 근거가 있어야 한다(citation-rules §0).
- README 내 동일 개념은 모든 등장 위치에서 SSOT와 동일한 문자열을 사용한다.

## 영향 범위

- README.md 갱신 작업 전반
- 후속 README 유지보수 시 동일 원칙 적용
- 레지스트리·PROJECT.md의 상이 표기는 별도 SSOT 정합 태스크에서 처리(README 태스크 범위 밖)

## 관련 페이지

- [[opsdd-pipeline-ssot]]
- [[uncommitted-component-readme-policy]]
