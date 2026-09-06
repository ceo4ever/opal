---
type: concept
title: 태스크 시점 사실의 영구 회귀 단언 고정 — 3연속 재현
tags:
- regression
- test-design
- header-standard
sources:
- task:107
related:
- regression-only-coverage-gate
- exports-generation-tool-verification-division
- worktree-tasks-fixture-structural-limit
created: '2026-09-06'
updated: '2026-09-06'
status: draft
---
## 개요

한 태스크 시점에 관측한 사실(현재 파일 개수, 현재 diff 상태, 현재 버전 값)을 테스트나 상수로 영구 고정하면, 그 사실이 다음 태스크에서 정당하게 바뀔 때 검증 장치가 구조적으로 막힌다. 태스크 107에서 같은 실패 패턴이 3회 연속 재현됐다(근거: `tasks/107-260906-opd-헤더필드-작성기준-이력분리/DONE.md` §7 (1)).

## 결정 배경 (WHY)

- 태스크 107 진행 중 `test-regression.js:511`의 TS-045가 `git diff --numstat HEAD -- opal/tools/brain-tool/brain_tool.py`를 "빈 문자열이어야 한다"고 단언하고 있었다 — 그 파일에 어떤 워킹트리 변경이라도 있으면 영구 실패하는 계약이었다(근거: `tasks/107-260906-opd-헤더필드-작성기준-이력분리/AGENTIC-LOG.md` "[ERROR] TS-045" 절, `DONE.md` §7 (1)).
- 이 태스크가 `brain_tool.py`의 `@header`를 정리하자 TS-045가 실제로 실패했고, 연쇄로 TS-062·S-19·TS-080까지 스위트 4건이 함께 실패했다(근거: `AGENTIC-LOG.md` "[ERROR] TS-045" 절).
- 같은 태스크 안에서 이전에도 두 차례 동형의 실패가 있었다 — `VERSION` 상수를 특정 값으로 핀하는 회귀 단언, 테스트 파일 **개수**를 `=== 11`로 고정하는 단언. 세 사례 모두 "지금 이 상태"를 "앞으로도 이래야 한다"로 잘못 승격한 것이 원인이다(근거: `DONE.md` §7 (1)).

## 결정 내용

해법은 판정 대상을 명제의 실제 의도에 맞게 좁히는 것이다 — 예컨대 TS-045는 "diff가 없다"는 전건 단언 대신, `@header` 필드를 제외한 나머지 바이트가 동일한지를 검사하도록 좁혀서 **강화**됐다(근거: `DONE.md` §7 (1) "TS-045는 `@header` 제외 후 바이트 동일로 강화"). 절대 수치·절대 diff·절대 카운트를 회귀 게이트의 단언으로 쓰기 전에, 그 수치가 "이 태스크 시점의 관측"인지 "영구히 참이어야 할 불변식"인지를 구분해야 한다.

## 영향 범위

`opal/tools/code-scan/tests/test-regression.js`(TS-045·TS-062·S-19·TS-080) 및 향후 회귀 게이트를 설계하는 모든 태스크. 관련 개념으로 [[worktree-tasks-fixture-structural-limit]](같은 태스크에서 발견된, 절대 수치 기준 판정의 또 다른 실패 사례)가 있다.

## 관련 페이지

- [[regression-only-coverage-gate]]
- [[exports-generation-tool-verification-division]]
- [[worktree-tasks-fixture-structural-limit]]
