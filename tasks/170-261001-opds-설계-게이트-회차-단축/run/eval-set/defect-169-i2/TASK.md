<!--
원본: 태스크 169(opds-워크트리-CLOSE-지식-반영), 설계 게이트 i2 (verdict=fail, rewrite_target=plan)
인용 gaps 원문: "decision_clarity-1: op-brain-ingest 워커가 쓰는 page 집합을 DONE.md 선언 집합 D와 어떻게 맞출지
결정이 없다. ... 선택지는 세 가지다. (a) 워커가 D에 선언된 경로만 쓴다. (b) 워커 결과로 DONE 선언을 갱신한다.
(c) PM이 워커 결과를 선언에 역반영한다. 이 선택이 구현자에게 남아 있다."
axes: completeness=FAIL, decision_clarity=FAIL, executability=PASS, recoverability=FAIL
이 fixture는 170 W-5 평가 세트용 합성 최소 재현본이다. design-gate를 이 파일에 실제로 돌리지 않는다.
-->
---
template: sdlc-v2
---
# TASK: 워크트리 CLOSE 지식 반영(합성 축소판)

## Problem

워크트리 CLOSE 단계에서 op-brain-ingest 워커가 brain 페이지를 쓰는데, 이 페이지 집합이 DONE.md에 선언된
집합과 어긋날 수 있다.

## Proposed outcome

워커가 쓰는 page 집합과 DONE.md 선언 집합이 서로 어긋나지 않도록 맞추는 방법이 명확하다.

## Affected users and systems

op-brain-ingest 워커, worktree-tool finalize, brain-tool.

## Constraints

- C-1: finalize의 선언 밖 변경 차단(ATTRIBUTION_COMMIT_BLOCKED) 동작을 바꾸지 않는다.

## Acceptance criteria

- AC-1: 워커가 쓰는 page 집합과 DONE.md 선언 집합을 맞추는 방법이 명확히 하나로 정해진다.
