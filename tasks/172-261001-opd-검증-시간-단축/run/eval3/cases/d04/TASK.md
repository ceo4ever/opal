<!--
원본: 태스크 162(opd-TEST-단계-소요시간-단축), 설계 게이트 i1 (verdict=fail, rewrite_target=plan)
인용 gaps 원문: "W-1 CLI 입력·출력과 저장 구조, 중복·누락 종료 처리, 상한 초과 상태 전이·재개 방법 미정"
axes: completeness=PASS, decision_clarity=FAIL, executability=FAIL, recoverability=PASS
이 fixture는 170 W-5 평가 세트용 합성 최소 재현본이다. design-gate를 이 파일에 실제로 돌리지 않는다.
-->
---
template: sdlc-v2
---
# TASK: TEST 단계 소요시간 측정 CLI 추가(합성 축소판)

## Problem

TEST 단계 실행 소요시간을 사람이 수작업으로 기록하고 있어 누락·중복이 잦다. 자동 측정 CLI가 필요하다.

## Proposed outcome

TEST 단계 시작·종료 시점을 CLI로 기록하고, 소요시간을 state.json에 반영한다.

## Affected users and systems

TEST 단계를 실행하는 워커·PM, state-tool.

## Constraints

- C-1: 기존 state.json 스키마 키 집합을 변경하지 않는다.
- C-2: 측정 실패 시 기존 TEST 단계 진행을 막지 않는다(fail-safe).

## Acceptance criteria

- AC-1: TEST 단계 시작·종료를 CLI 한 쌍(`start`/`stop`)으로 기록하고 소요시간(분)을 산출한다.
- AC-2: 같은 단계에 대해 `stop` 없이 다시 `start`하거나, `start` 없이 `stop`하는 중복·누락 호출이 안전하게 처리된다.
- AC-3: 측정 상한(예: 8시간)을 넘긴 세션은 명확한 상태로 전이되고 재개 방법이 있다.
