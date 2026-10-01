<!--
원본: 태스크 167(opd-테스트-시나리오-작성-기준-개선), 설계 게이트 i2 (verdict=fail, rewrite_target=plan)
인용 gaps 원문: "decision_clarity-1: evaluator 미디스패치 회차(coverage exit 16/17)의 record 처리 미정"
axes: completeness=PASS, decision_clarity=FAIL, executability=PASS, recoverability=PASS
이 fixture는 170 W-5 평가 세트용 합성 최소 재현본이다. design-gate를 이 파일에 실제로 돌리지 않는다.
-->
---
template: sdlc-v2
---
# TASK: 테스트 시나리오 작성 기준 개선(합성 축소판)

## Problem

scenario-coverage-check가 exit 16/17(evaluator 미디스패치)을 반환하는 회차에서 설계 게이트 record 처리가 불명확하다.

## Proposed outcome

evaluator가 디스패치되지 않은 회차도 설계 게이트 record 절차가 명확하게 정의된다.

## Affected users and systems

state-tool design-gate, scenario-coverage 도구.

## Constraints

- C-1: 기존 record 계약의 필수 필드를 바꾸지 않는다.

## Acceptance criteria

- AC-1: coverage 도구가 exit 16 또는 17을 반환하는 회차에서 PM이 record를 어떻게 처리해야 하는지 명확하다.
