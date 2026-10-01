---
type: concept
title: opal-eli5 — 5살 눈높이 설명서 스킬
tags:
- eli5
- explain
- skill
sources:
- skill:opal-eli5
related: [opal-grill]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

주제 하나를 처음 보는 사람이 한 번에 이해하도록, 큰 그림과 적은 글자의 자기완결 설명서 파일 1건으로 만드는 스킬이다. 명시 호출(`//opeli5`)로만 쓴다(`opal/skills/opal-eli5/SKILL.md:3-6`, `:16`).

## 현재 계약

- 구성은 정체 한 문장 → 블록 3~5개 관계도 → 블록별 1~2문장이며, 그림이 본체이고 글은 캡션이다(`opal/skills/opal-eli5/SKILL.md:20`).
- 이 프로젝트 주제면 brain·코드맵·문서·완료 기록에서 실물을 찾아 사실마다 위치를 붙이고, 찾지 못하면 일반 지식으로 쓰되 그 사실을 산출물과 대화에 알린다. 두 방식을 섞지 않는다(`opal/skills/opal-eli5/SKILL.md:22`).
- 저장 위치는 진행 중 태스크가 1건이면 그 태스크 산출물 폴더, 없으면 현재 위치의 설명서 폴더, 2건 이상이면 한 번 묻는다(`opal/skills/opal-eli5/SKILL.md:26-32`).
- 형식은 외부 요청 없는 HTML(기본) 또는 Markdown이며, 그 밖의 값은 기본값으로 바꾸지 않고 오류로 멈춘다(`opal/skills/opal-eli5/SKILL.md:38-40`).

## 관련 페이지

- [[opal-grill]] — 같은 명시 호출형 문서 보조 스킬
