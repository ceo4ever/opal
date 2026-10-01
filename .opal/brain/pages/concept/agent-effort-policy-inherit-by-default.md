---
type: concept
title: 에이전트 effort 정책 (미선언은 세션 상속)
tags:
- agent
- effort
- policy
sources:
- task:172
related: [opal-evaluator-agent, convention-precheck]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

에이전트 정의의 `effort` 값을 표시용으로 두지 않고, 측정으로 정한 두 에이전트에만 명시하며 나머지는 호출 세션 값을 상속하게 하는 정책이다.

## 결정 배경 (WHY)

(근거: task:172 DONE.md) 평가 세트로 측정한 뒤 소유자가 결정했다. 컨벤션 검사 4후보×10사례, 평가자 3후보×8사례를 비교했다.

## 결정 내용

- 컨벤션 검사 에이전트 = `standard` + `effort: low`, 평가자 에이전트 = `advanced` + `effort: medium`.
- 표시용으로 쓰던 `effort: default`는 제거했다. 나머지 14개 에이전트는 effort를 선언하지 않아 호출 세션 값을 상속한다.
- 재발 방지: `scripts/tests/test_agent_effort_policy.sh`가 `default` 값 재도입을 막는다.
- 한계: 공식 문서는 서브에이전트 `effort`가 세션 effort보다 우선한다고 명문으로 적지 않는다(생략 시 세션 상속까지만). 배포 파일에 선언 값이 존재함은 시험으로 확인했다 (근거: task:172 DONE.md H-6 부분 확인).

## 관련 페이지

- [[opal-evaluator-agent]]
- [[convention-precheck]]
