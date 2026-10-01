---
type: concept
title: 에이전트 effort 정책 (미선언은 세션 상속)
tags:
- agent
- effort
- policy
sources:
- task:172
related: [opal-evaluator-agent, convention-precheck, evaluator-eval-set-label-fixture-measurement-lesson]
created: '2026-10-01'
updated: '2026-10-01'
status: active
---
## 개요

에이전트 정의의 `effort` 값을 표시용으로 두지 않고, 측정으로 정한 두 에이전트에만 명시하며 나머지는 호출 세션 값을 상속하게 하는 정책이다.

## 결정 배경 (WHY)

- (근거: task:172 DONE.md) 평가 세트로 측정한 뒤 소유자가 결정했다. 컨벤션 검사 4후보×10사례, 평가자 3후보×8사례를 비교했다. 이 1차 측정은 사례 라벨이 경로에 노출된 상태였다.
- (근거: task:172 EVAL-RESULT-4·5, ADD_DONE-4.md) 라벨을 가리고 clean 세트를 정비해 평가자 후보를 11사례×3회로 다시 잰 결과, 세 후보(미지정·medium·low) 모두 결함 누락 0·형식 오류 0이었고 차이는 멀쩡한 문서를 fail로 뒤집는 빈도뿐이었다(clean fail 7/9·8/9·3/9). fixture 결손(REQUEST.md)을 고친 보조 측정에서는 medium 9/9, low 2/9였다. 소요는 low가 약 0.45배다. 소유자는 이를 보고 평가자를 `low`로 바꿨다. 사전 고정 규칙으로 "채택 가능"인 후보는 없었으므로 이 선택은 측정된 후보 중 상대적 최선이다.

## 결정 내용

- 컨벤션 검사 에이전트 = `standard` + `effort: low`, 평가자 에이전트 = `advanced` + `effort: low`(1차 결정 `medium`을 task:172 ADD-5에서 변경).
- 표시용으로 쓰던 `effort: default`는 제거했다. 나머지 14개 에이전트는 effort를 선언하지 않아 호출 세션 값을 상속한다.
- 재발 방지: `scripts/tests/test_agent_effort_policy.sh`가 `default` 값 재도입을 막는다.
- 한계: 공식 문서는 서브에이전트 `effort`가 세션 effort보다 우선한다고 명문으로 적지 않는다(생략 시 세션 상속까지만). 배포 파일에 선언 값이 존재함은 시험으로 확인했다 (근거: task:172 DONE.md H-6 부분 확인). 선언 값은 설치본에 install로 배포되어야 적용되며, 머지 전 다른 세션의 재설치가 선언을 덮을 수 있다.

## 관련 페이지

- [[opal-evaluator-agent]]
- [[convention-precheck]]
- [[evaluator-eval-set-label-fixture-measurement-lesson]]
