---
type: concept
title: 네이티브 todo 패널 LLM 전용 기록 한계 (hook은 트리거·페이로드까지)
tags:
- opal-pipeline
- todo-mirror
- hook
- platform-constraint
- honest-limit
sources:
- task:076
related:
- opal-adapter-platform-isolation
- state-tool
created: '2026-07-23'
updated: '2026-07-23'
status: draft
speculative_override: true
override_note: '''todo''는 미실체 마커가 아니라 네이티브 todo 패널 미러(태스크 076 확정·구현 완료 주제어)임 — 오검출'
---
## 개요

세션 하단의 네이티브 할일 패널은 오직 LLM의 할일 생성·갱신 도구 호출로만 기록된다는 플랫폼 제약과, 그 위에서 자동화가 도달할 수 있는 정직한 최대치를 규정한 지식이다. 파이썬 도구나 셸 hook은 그 도구를 대신 호출할 수 없으므로, 자동화는 트리거·페이로드·타이밍의 결정론화까지이고 최종 도구 호출은 LLM의 몫으로 남는다.

## 결정 배경 (WHY)

- 네이티브 할일 패널은 LLM 도구 호출로만 갱신되고, 외부 프로세스가 그 도구를 주입할 경로가 플랫폼에 없다 (근거: task:076 TASK.md 플랫폼 제약, PLAN§1.2).
- 따라서 "완전 무개입 자동"을 목표로 잡으면 달성 불가능한 약속이 되므로, 설계 목표 자체를 도달 가능한 지점으로 정직하게 재정의할 필요가 있었다 (근거: task:076 PLAN§1.2 설계 전제).

## 결정 내용

- 자동화의 경계는 hook이 트리거·페이로드·타이밍을 결정론화하는 데까지다. hook은 진행 이벤트를 감지해 갱신 지시와 페이로드를 세션에 주입할 수 있을 뿐, 할일 패널을 직접 기록하지 못한다 (`opal/tools/state-tool/todo_mirror_hook.py`).
- 남는 한 스텝, 즉 주입된 페이로드를 실제 할일 도구 호출로 전달하는 것은 LLM(소유자)의 몫이다. 이 몫은 "주입된 페이로드를 그대로 도구로 넘기는" 기계적 1스텝으로 축소되어 사실상 자동에 가깝지만, 원리상 무개입은 아니다.
- 이 한계는 결함이 아니라 플랫폼 계약에서 파생된 하드 제약이며, 관련 문서·설계는 이를 감추지 않고 명시한다. hook이 주입한 지시가 실제 도구 호출을 유발하는지는 플랫폼 PostToolUse 계약에 의존하는 검증 대상이다 (task:076 PLAN 리스크 H-4).
- 할일 도구가 노출되지 않는 세션·플랫폼에서는 능력 감지로 미러를 건너뛴다. 플랫폼 전용 hook은 어댑터 계층에만 격리하고 행위 서술은 플랫폼 독립으로 유지한다.

## 영향 범위

- `opal/tools/state-tool/todo_mirror_hook.py` — 트리거·페이로드 주입까지만 수행하는 릴레이 경계
- `opal/core/references/harness/state.md` — 능력 감지 게이트·정직한 한계 서술
- 파이프라인 미러 자동화의 목표 범위 정의 전반

## 관련 페이지

- [[pipeline-todo-mirror-hook-enforcement]]
- [[opal-adapter-platform-isolation]]
- [[state-tool]]
