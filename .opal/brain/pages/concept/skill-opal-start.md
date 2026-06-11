---
type: concept
title: opal-start — OPAL 재진입 가이드
tags:
- skill
- start
- onboarding
- guide
sources:
- skill:opal-start
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

OPAL 재진입 가이드 스킬(//start). 현재 OPAL 환경 상태를 진단하여 사용자에게 다음 액션 하나를 명확히 권유한다. 첫 사용자 또는 재진입 시 진단 표를 출력한다.

## 배경·문제 (WHY)

사용자가 OPAL을 처음 사용하거나 중단 후 재진입할 때 어디서 시작해야 할지 모를 수 있다. 환경 상태 진단 → 단일 다음 액션 권유로 진입 장벽을 낮춘다.

## 결정 내용 (HOW)

5개 항목 진단: identity.md, AGENT.md(설치), 프로젝트 여부, .opal/AGENT.md(프로젝트 초기화), docs/PROJECT.md. 진단 결과 표 출력 후 분기별 다음 단계 안내. references/start-flow.md 참조.

## 영향·관계

opal-onboarding(identity.md 생성), opal-project-init(프로젝트 초기화)로 연계된다. AGENT.md 부트스트랩의 사용자 대면 가이드 역할.

## 관련

- [[skill-opal-onboarding]] — identity.md 부재 시 연계되는 정체성 설정 스킬
- [[skill-opal-project-init]] — 프로젝트 초기화 미완료 시 연계되는 환경 초기화 스킬
- [[opal-project-definition]] — 진단 항목 중 docs/PROJECT.md 존재 여부 확인 기준

## 근거 출처

file_path: `opal/skills/opal-start/SKILL.md`
