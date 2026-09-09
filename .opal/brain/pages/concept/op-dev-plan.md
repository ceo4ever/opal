---
type: concept
title: op-dev-plan — 구현 계획 수립 단계 스킬
tags:
- dev
- plan
- skill
sources:
- skill:op-dev-plan
- task:111
related:
- sdlc-v2-development-artifact-contract
- op-dev-analysis
- op-dev-execute
created: '2026-06-11'
updated: '2026-09-09'
status: active
---
## 개요

TASK와 선택적 ANALYSIS를 구현 가능한 결정과 Work items로 바꾸는 설계 단계 스킬이다.

## 현재 계약

PLAN은 Approach, Decisions and contracts, Work items, Risks, Release and recovery를 사용한다. Work item은 담당, 변경 대상, 구체적 변경, 선행 작업, 실행 그룹, 완료 기준 연결을 반드시 제공한다. 실행 그룹이 같고 선행 관계와 파일 충돌이 없는 작업만 병렬 실행할 수 있다. 기능 번호와 구형 실행 체크리스트는 신규 기본 계약이 아니다.

## 근거

`opal/skills/op-dev-plan/SKILL.md:21`, `opal/skills/op-dev-plan/references/plan-guide.md:49`, task:111.

## 관련 페이지

- [[sdlc-v2-development-artifact-contract]]
- [[op-dev-analysis]]
- [[op-dev-execute]]
