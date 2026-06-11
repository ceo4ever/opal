---
type: concept
title: opal-brain — 프로젝트 브레인 지식 위키
tags:
- skill
- brain
- knowledge
- wiki
sources:
- skill:opal-brain
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

프로젝트 브레인 — 영속 지식 위키 생성·누적·질의·정비 스킬. 4가지 모드(init/ingest/query/lint)로 프로젝트 WHY·HOW 지식을 마크다운 네이티브 위키에 쌓는다.

## 배경·문제 (WHY)

프로젝트 지식이 태스크·코드에 분산되어 재활용이 어렵다. brain-tool을 통한 단방향 동기화(origin→wiki 읽기만)로 원본 파일 훼손 없이 지식을 축적한다.

## 결정 내용 (HOW)

모드 라우팅: init(골격 생성) → ingest(지식 누적, 3~6줄 요약+포인터) → query(후보→선택→주입 RAG식) → lint(무결성 정비). brain-tool CLI가 index.md·log.md를 전담하며 LLM 직접 편집 금지.

## 영향·관계

brain-tool, ingest-scan, search 서브커맨드에 의존. 모든 스킬 ingest 시 `pages/concept/` 아래 concept 페이지를 생성한다.

## 관련

- [[opal-brain-system]] — brain 스킬이 의존하는 도구 시스템 아키텍처
- [[op-brain-ingest]] — ingest 모드에서 호출하는 지식 수집 워커 스텝
- [[opal-brain-design-proposal]] — 이 스킬의 설계 원칙과 의사결정(M-1~M-5) SSOT

## 근거 출처

file_path: `opal/skills/opal-brain/SKILL.md`
