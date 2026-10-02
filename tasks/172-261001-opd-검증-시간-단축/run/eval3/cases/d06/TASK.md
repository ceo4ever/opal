<!--
원본: 태스크 168(opd-opd2-프레임워크-통합), 설계 게이트 i2 (verdict=fail, rewrite_target=plan)
인용 gaps 원문: "decision_clarity/row mapping: The PLAN does not say which state.json row each lifecycle.py
transition marks, who marks the user_confirm rows in semi-agentic and agentic modes, or who marks
close.done_md through close.final."
axes: completeness=FAIL, decision_clarity=FAIL, executability=PASS, recoverability=PASS
이 fixture는 170 W-5 평가 세트용 합성 최소 재현본이다. design-gate를 이 파일에 실제로 돌리지 않는다.
-->
---
template: sdlc-v2
---
# TASK: opd2 프레임워크 통합(합성 축소판)

## Problem

opd2 lifecycle.py가 state.json 행을 전이시키는데, 어떤 행을 어떤 시점에 마크하는지 PLAN에 명시되지 않았다.

## Proposed outcome

lifecycle.py의 각 전이가 state.json의 어떤 행을 마크하는지, 그리고 user_confirm 행을 누가 마크하는지 명확하다.

## Affected users and systems

opd2 lifecycle.py, state-tool, semi-agentic·agentic 모드 사용자.

## Constraints

- C-1: 기존 state.json 스키마를 변경하지 않는다.

## Acceptance criteria

- AC-1: lifecycle.py의 각 전이가 마크하는 state.json 행이 명시된다.
- AC-2: semi-agentic·agentic 모드에서 user_confirm 행을 누가 마크하는지 명시된다.
