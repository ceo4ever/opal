---
type: concept
title: opal-skill-manager — OPAL 커뮤니티 스킬 관리
tags:
- skill
- manager
- community
sources:
- skill:opal-skill-manager
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

OPAL 커뮤니티 스킬 검색·설치·관리 스킬. `npx skills` CLI(vercel-labs/skills)를 활용하여 생태계 스킬을 탐색하고 설치한다.

## 배경·문제 (WHY)

OPAL 프레임워크가 커뮤니티 스킬 생태계와 연동되어야 한다. 설치된 스킬 목록(레지스트리)과 외부 생태계(npx skills)를 통합적으로 관리할 단일 진입점이 필요하다.

## 결정 내용 (HOW)

검색: 설치된 스킬(skill-registry match) 우선 확인 → 없으면 `npx skills find` 생태계 검색. 설치: `npx skills install` + skill-registry 등록. 삭제: skill-registry에서 제거 + 파일 삭제. 목록 조회 지원.

## 영향·관계

skill-registry 도구(~/.opal/tools/skill-registry/)에 의존. opal-skill-creator(OPAL 스킬 생성)와 상호 보완적으로 사용된다.

## 관련

- [[skill-opal-skill-creator]] — 이 스킬과 상호 보완적으로 사용하는 OPAL 스킬 생성 파이프라인
- [[opal-project-definition]] — 스킬 생태계 관리의 프레임워크 정의 기준
- [[opal-conventions]] — 설치된 스킬의 레지스트리 등록 규칙 기준

## 근거 출처

file_path: `opal/skills/opal-skill-manager/SKILL.md`
