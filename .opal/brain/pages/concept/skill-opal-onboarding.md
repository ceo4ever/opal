---
type: concept
title: opal-onboarding — 에이전트 정체성 설정
tags:
- skill
- onboarding
- identity
sources:
- skill:opal-onboarding
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

OPAL AI 에이전트 초기 정체성 설정 스킬. ~/.opal/identity.md가 없을 때 자동 실행되어 소유자와 단계별 인터뷰를 통해 에이전트 이름·성격·호칭을 정의한다.

## 배경·문제 (WHY)

AGENT.md 부트스트랩 절차에서 identity.md 부재 시 에이전트가 자신의 정체성 없이 작동하면 사용자 경험이 일관되지 않는다. 1회 온보딩으로 identity.md를 생성한다.

## 결정 내용 (HOW)

1문제씩 순차 인터뷰(객관식 우선). 완료 후 ~/.opal/identity.md에 저장. "정체성 재설정" 또는 //onboarding으로 재호출 가능.

## 영향·관계

AGENT.md 부트스트랩에서 identity.md 부재 시 자동 호출. opal-start 스킬의 환경 진단에서도 identity.md 존재 여부를 확인한다.

## 관련

- [[skill-opal-start]] — 환경 진단 시 identity.md 존재 여부를 확인하고 이 스킬로 연계하는 가이드
- [[opal-project-definition]] — 온보딩 완료 후 프레임워크 전체 정의를 참조하는 기준 문서
- [[skill-opal-project-init]] — 정체성 설정 후 프로젝트 환경 초기화 단계로 연결되는 스킬

## 근거 출처

file_path: `opal/skills/opal-onboarding/SKILL.md`
