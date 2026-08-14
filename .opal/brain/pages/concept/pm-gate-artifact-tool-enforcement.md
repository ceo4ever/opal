---
type: concept
title: PM Gate 정의 단일화와 산출물 존재 게이트 집행
tags:
- gate-design
- state-tool
- pm-gate
- ssot
- enforce-not-advise
- task-091
sources:
- task:091
related:
- pipeline-todo-mirror-hook-enforcement
- opal-principles-constitution
- state-tool
- state-tool-task-step-key-address
- pipeline-json-spec
created: '2026-08-14'
updated: '2026-08-14'
status: draft
---
## 개요

PM Gate(각 단계 완료 시 확인해야 하는 산출물·체크리스트) 정의가 그동안 파이프라인 스펙과 각 파이프라인 문서 두 곳에 나뉘어 있었고, 실제로 산출물 존재를 확인하는 도구는 없었다. 이 정의를 파이프라인 스펙의 각 단계 항목이 갖는 하나의 자리(`gate`)로 합치고, 진행 상태를 다음 단계로 넘기는 도구가 그 자리를 읽어 산출물이 실제로 있는지 확인한 뒤에만 통과시키도록 바꿨다.

## 결정 배경 (WHY)

- (근거: task:091 DONE.md §1) PM Gate 정의는 스펙에는 존재했지만 진행 갱신 도구가 이를 읽지도 검증하지도 않았고, 실제 판단은 각 파이프라인 문서에 적힌 산문 체크리스트에만 의존했다. 두 정의는 이미 벌어져 있었다 — 한 파이프라인은 게이트 항목 하나가 누락돼 있었고, 다른 파이프라인은 표현이 어긋나 있었다.
- (추론: 코드패턴) "언제나 지켜야 하는 규칙은 산문이 아니라 도구가 강제한다"는 원칙이, 산출물 존재처럼 사람이 판별할 필요 없이 기계적으로 확인 가능한 지점에는 적용되지만 체크리스트 항목처럼 판단이 필요한 지점에는 적용되지 않는다는 경계가 이번에 명시적으로 그어졌다 — [[pipeline-todo-mirror-hook-enforcement]]가 같은 원칙을 진행 현황 미러라는 다른 지점에 적용한 선례다.

## 결정 내용

- 게이트 정의를 파이프라인 스펙의 각 단계 항목이 갖는 `gate` 자리 하나로 합쳤다(스키마: `opal/tools/state-tool/schema/pipeline-spec.schema.json:32`). 이전에 별도로 존재하던 최상위 정의는 삭제했다.
- 진행 상태를 다음 단계로 넘기는 도구 명령이 그 단계의 `gate.artifacts`에 적힌 산출물이 실제로 존재하는지 확인한다(`opal/tools/state-tool/state_tool.py:738`). 하나라도 없으면 통과를 거부하고 무엇이 없는지 알려준다(`:762`).
- 통과하면 `gate.checklist`(도구가 판별할 수 없어 사람이 확인해야 하는 항목 목록)를 응답으로 함께 돌려준다(`:765`) — 이 목록은 세션에 자동 주입되어, 담당자가 해당 파이프라인 문서를 직접 읽지 않아도 게이트 기준을 알 수 있다.
- 산출물이 없어도 강제로 통과시키는 경로는 막지 않되, 그때는 반드시 사유를 남겨야 하고 그 사유는 의사결정 로그에 자동 기재된다(`:1627`) — 강제 이탈이 조용히 지나가지 않는다.
- 산출물 검사를 상태 저장 이전 시점에 배치해, 검사에 걸려 거부되는 경우에도 상태 파일 일부만 바뀌는 일이 없게 했다(가드 호출 `:1527`이 실제 저장 `:1596`보다 앞선다).

## 영향 범위

파이프라인 문서 10종 전체의 게이트 정의가 이 단일 지점으로 합쳐졌다. 앞으로 새 파이프라인 단계를 추가하거나 게이트 기준을 바꿀 때는 파이프라인 문서를 고치는 것이 아니라 이 스펙 자리 하나만 고치면 된다.

## 관련 페이지

- [[pipeline-todo-mirror-hook-enforcement]]
- [[opal-principles-constitution]]
- [[state-tool]]
- [[state-tool-task-step-key-address]]
- [[pipeline-json-spec]]
