---
type: concept
title: opal-grill (opgr) — 산출물 캐묻기 스킬
tags:
- grill
- review
- skill
sources:
- skill:opal-grill
related: [opal-eli5, opal-evaluator-agent]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

문서 산출물 하나를 붙잡고 집요하게 캐묻되, 문서·코드·환경에서 스스로 답을 찾을 수 있는 것은 직접 찾고 사람만 답할 수 있는 결정만 라운드형 질문으로 돌려주는 읽기 전용 스킬이다. 파일을 만들지 않는다(`opal/skills/opal-grill/SKILL.md:3-7`, `:16`).

## 현재 계약

- 산출물은 판정문이 아니라 질문이다. 점수·합격 여부를 내지 않고, 판정이 필요하면 전용 판정 컴포넌트를 쓰라고 안내한다(`opal/skills/opal-grill/SKILL.md:18`, `:24-28`).
- 조사하면 알 수 있는 사실을 사용자에게 묻는 것은 일을 덜 한 것으로 본다(`opal/skills/opal-grill/SKILL.md:30-34`).
- 판정 기준을 대상 프로젝트의 규범 문서에서 가져오지 않는다. 그 규칙으로 검사하면 규칙 자체가 틀린 경우를 볼 수 없기 때문이며, 대신 상류 정합·자기 정합·근거 3축을 자체 보유한다(`opal/skills/opal-grill/SKILL.md:36-42`).

## 관련 페이지

- [[opal-eli5]]
- [[opal-evaluator-agent]] — 판정이 필요할 때 쓰는 별도 심판
