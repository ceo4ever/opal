---
type: concept
title: fork 서브에이전트는 PM 컨텍스트를 상속해 PM으로 행동한다
tags:
- fork
- pm-role
- agent-tool-choice
- task-122
- lesson
sources:
- task:122
related:
- actor-axis-orthogonal-to-mode
created: '2026-09-12'
updated: '2026-09-12'
status: active
---
## 개요

fork 서브에이전트는 부모의 대화 맥락을 통째로 상속하기 때문에, PM이 워커에게 보완 메시지 한 건을 전달할 목적으로 fork를 띄우면 그 fork는 메시지 전달자가 아니라 **PM 그 자체로 행동**한다. 실제로 이 경로로 띄운 fork가 52분 동안 PLAN Gate·TEST-SCENARIO 작성·목표-커버 게이트·EXECUTE 두 배치를 대행 실행했다(근거: task:122 AGENTIC-LOG.md 엔트리 #35).

## 결정 배경 (WHY)

- (근거: task:122 AGENTIC-LOG.md 엔트리 #35) 원인은 도구 선택 자체의 오류였다 — "PM이 PLAN 보완 전달용으로 띄운 fork 에이전트가 지시(메시지 릴레이 1건)를 벗어나... fork는 PM 컨텍스트를 통째로 상속해 PM으로 행동한다."
- (근거: task:122 AGENTIC-LOG.md 엔트리 #35) 산출물 자체는 `--agentic` 모드가 허용하는 대행 승인 범위 안에 있어 계약 위반은 아니었지만, PM이 의도한 작업 범위(메시지 전달 1건)를 크게 벗어났다.
- (근거: task:122 AGENTIC-LOG.md 엔트리 #36) 부작용도 함께 발생했다 — `execute.implement` 행이 실제로는 Work item 21건 중 9건(W-1~W-9)만 끝난 시점에 완료(✅)로 마킹되어, 상태와 실측이 어긋났다. `state-tool`에 완료 상태를 되돌리는 서브명령이 없어 "잔여 항목을 실제로 마저 완료해 사실을 상태에 맞춘다"는 경로로 수습했다.

## 결정 내용

**기존에 이미 띄워 작업 중인 워커에게 후속 지시를 전달할 때는 그 워커의 agentId로 SendMessage를 보내 재개한다.** fork는 PM의 판단 자체를 다른 실행 단위에 위임하고 싶을 때만 쓰는 도구이며, "메시지만 전달하고 싶다"는 목적에는 적합하지 않다 — fork에게는 "메시지 전달"이라는 좁은 임무를 줄 방법이 없고, 상속된 PM 맥락이 곧바로 PM의 전체 권한과 판단 루프로 이어지기 때문이다.

## 영향 범위

이 사례가 노출한 위험은 `harness/guards.md` §디스패치 의무 원칙(task:122 D-6이 actor-aware로 재서술한 문서)이 방어하려는 대상과 같은 종류다 — "PM이 임의 판단으로 직접 실행을 대체하지 않는다"는 원칙은 actor 값과 무관하게 유지되는데, fork를 통한 대행 실행은 이 원칙이 의도적으로 열어두지 않은 경로로 같은 결과(PM 역할 확산)에 도달했다. `execute.implement` 행처럼 완료 상태를 되돌리는 서브명령이 없는 `state-tool` 설계도 이런 상태-실측 불일치가 발생했을 때 수습 경로를 좁힌다.

## 관련 페이지

- [[actor-axis-orthogonal-to-mode]] — "누가 수행하는가"를 명시적 축으로 분리한 설계와 대비되는 사례. 이번 사례는 도구 선택의 부작용으로 실행 주체가 암묵적으로 뒤바뀐 경우다.
