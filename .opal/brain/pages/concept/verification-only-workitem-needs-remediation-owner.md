---
type: concept
title: 검증 전용 Work item은 실패 시 보정 주체를 함께 정의해야 한다
tags:
- process-gap
- verification
- work-item
- task-122
- lesson
sources:
- task:122
related:
- count-notation-scattered-across-docs
- fork-agent-inherits-pm-role
created: '2026-09-12'
updated: '2026-09-12'
status: active
---
## 개요

"검증만 하고 고치지 않는다"는 계약대로 워커가 행동해도, 그 검증 전용 작업 항목에 실패 시 누가 어떻게 고치는지가 계획에 없으면 PM이 그때그때 즉석으로 보정 경로를 설계해야 한다. 계약 준수와 계획 완결성은 별개의 문제다(근거: task:122 AGENTIC-LOG.md 엔트리 #63).

## 결정 배경 (WHY)

- (근거: task:122 AGENTIC-LOG.md 엔트리 #60) install 배포와 소스→설치본 검증을 맡은 W-20(검증 전용, 소스 비변경)에서 `code-scan validate --changed`가 실제로 차단 위반 5건(신규 `.md` 4건의 `newly_uncovered`, `state_tool.py`의 `header_history`)을 냈다.
- (근거: task:122 AGENTIC-LOG.md 엔트리 #62) 워커는 (1)~(5)를 Pass로 반환하고 (6)만 blocked로 PM 판단을 요청했다. `harness/guards.md`가 정한 PRINCIPLES §3(검증 전용 작업은 발견한 결함을 직접 고치지 않는다)을 그대로 지킨, 계약대로의 행동이었다.
- (근거: task:122 AGENTIC-LOG.md 엔트리 #63) 문제는 W-20이 "검증 전용" Work item으로 설계됐는데도 PLAN에 "실패하면 누가·어떻게 보정하는가"의 경로가 없었다는 점이다. 그래서 실패가 나올 때마다 PM이 보정 지시를 즉석에서 설계해야 했다 — 이번에는 PM이 5건 각각에 인라인 `@header`를 넣는 보정을 직접 지시했다(근거: 엔트리 #61).

## 결정 내용

검증 전용 Work item을 설계할 때는 "검증 결과가 fail일 때 보정을 누가(워커 재디스패치인지 PM 직접 판단인지) 어떤 절차로 수행하는가"를 그 Work item 정의 자체에 함께 적어 둔다. 검증자가 결함을 스스로 고치지 않는 것은 옳은 계약이지만, 그 계약이 성립하려면 "고치는 다음 단계"가 계획 어딘가에 반드시 존재해야 한다 — 지금은 그 다음 단계가 PLAN에 없어 매번 PM의 즉석 설계에 의존한다.

## 영향 범위

`op-brain-ingest`처럼 이 프로젝트가 향후 만들 검증 전용 Work item 전반 — 특히 install 배포 검증(W-20 계열)처럼 "소스 비변경, 결과만 확인"으로 정의된 항목에 적용된다. PLAN 작성 가이드에 "검증 전용 Work item은 실패 시 보정 주체·경로를 명시한다"는 규칙을 아직 추가하지 않았다.

## 관련 페이지

- [[count-notation-scattered-across-docs]] — 같은 태스크 EXECUTE 단계에서 함께 드러난 PLAN 작성 단계의 세부 규칙 공백 사례.
- [[fork-agent-inherits-pm-role]] — 같은 태스크에서 함께 드러난, PM의 즉석 판단이 계획 공백을 메워야 했던 또 다른 사례.
