---
type: concept
title: opal-agent-creator — OPAL 에이전트 생성 파이프라인
tags:
- skill
- agent
- creator
sources:
- skill:opal-agent-creator
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

OPAL 프레임워크 에이전트 생성 파이프라인. create-subagents 커뮤니티 스킬로 콘텐츠를 설계한 뒤, OPAL 규격 후처리(3플랫폼 파일 생성, 레지스트리 등록, 버전 태깅)를 자동 수행한다.

## 배경·문제 (WHY)

단순히 에이전트 콘텐츠만 만드는 것이 아니라 디렉토리 배치·레지스트리 등록·버전 태깅까지 일관되게 적용해야 OPAL 규격을 유지할 수 있다. 커뮤니티 스킬만으로는 OPAL 프레임워크 규격이 자동 적용되지 않아 래핑 스킬이 필요하다.

## 결정 내용 (HOW)

2단계 파이프라인: Phase 1(create-subagents 위임) → Phase 2(OPAL 후처리). 신규 생성 모드와 기존 에이전트 개선 모드 두 가지 분기를 지원한다. 3플랫폼 파일(Claude/Gemini/Cursor) 배치 + skill-registry 등록까지 완주한다.

## 영향·관계

opal-skill-creator와 동일한 2단계 패턴을 공유. create-subagents 커뮤니티 스킬에 의존한다.

## 관련

- [[skill-opal-skill-creator]] — 동일한 2단계 래핑 패턴을 공유하는 스킬 생성 파이프라인
- [[opal-project-definition]] — 에이전트 생성 후 레지스트리 등록 기준이 되는 프레임워크 정의
- [[opal-conventions]] — 3플랫폼 파일 배치·버전 태깅 규칙의 근거

## 근거 출처

file_path: `opal/skills/opal-agent-creator/SKILL.md`
