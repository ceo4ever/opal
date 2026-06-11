---
type: concept
title: opal-skill-creator — OPAL 스킬 생성 파이프라인
tags:
- skill
- creator
- framework
sources:
- skill:opal-skill-creator
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

OPAL 프레임워크 스킬 생성 파이프라인. skill-creator 커뮤니티 스킬로 SKILL.md를 생성한 뒤, OPAL 규격 후처리(디렉토리 구조, frontmatter 보정, 레지스트리 등록, 버전 태깅)를 자동 수행한다.

## 배경·문제 (WHY)

커뮤니티 skill-creator만으로는 OPAL 프레임워크 규격(디렉토리 배치·레지스트리 등록·버전 관리)이 자동 적용되지 않는다. opal-agent-creator와 동일한 래핑 패턴을 적용한다.

## 결정 내용 (HOW)

2단계 파이프라인: Phase 1(skill-creator 위임) → Phase 2(OPAL 후처리). 신규 생성/기존 개선 두 분기. 스킬 유형(프레임워크 스킬 vs OPAL 전용 스킬)에 따라 저장 경로가 달라진다.

## 영향·관계

opal-agent-creator와 동일한 2단계 패턴 공유. skill-creator 커뮤니티 스킬과 skill-registry 도구에 의존한다.

## 관련

- [[skill-opal-agent-creator]] — 동일한 2단계 래핑 패턴을 공유하는 에이전트 생성 파이프라인
- [[skill-opal-skill-manager]] — 생성된 스킬을 레지스트리에서 관리하는 스킬
- [[opal-conventions]] — 스킬 디렉토리 구조·frontmatter 규칙의 기준

## 근거 출처

file_path: `opal/skills/opal-skill-creator/SKILL.md`
