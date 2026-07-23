---
type: concept
title: 파이프라인 todo 미러 hook 강제 전환 (prose 지시 → 결정론 트리거)
tags:
- opal-pipeline
- todo-mirror
- hook
- enforce-not-advise
- state-tool
sources:
- task:076
related:
- state-tool
- opal-principles-constitution
- kanban-pipeline-stage-grouping
created: '2026-07-23'
updated: '2026-07-23'
status: draft
speculative_override: true
override_note: '''todo''는 미실체 마커가 아니라 네이티브 todo 패널 미러(태스크 076 확정·구현 완료 주제어)임 — 오검출'
---
## 개요

파이프라인 진행 현황을 세션 하단의 네이티브 할일 패널에 미러하는 규칙을, "소유자가 매 이벤트마다 직접 갱신하라"는 산문 지시에서 도구가 강제하는 결정론 트리거로 전환한 설계다. 진행 SSOT(state-tool) 이벤트가 발생하면 hook이 갱신 지시와 페이로드를 세션에 주입하고, 소유자는 그것을 그대로 할일 도구로 전달한다.

## 결정 배경 (WHY)

- 기존 미러 규칙은 참조 문서에만 산문으로 존재했고 어떤 도구도 강제하지 않아, 소유자가 갱신을 잊으면 미러가 멈추는 결함이 있었다 (근거: task:076 TASK.md 배경, state.md §파이프라인 todo 미러).
- 헌법 Core Stance "Enforce, don't just advise — 항상 지켜야 할 규칙은 산문이 아니라 도구가 게이트한다"에 정면으로 어긋났다 (근거: `~/.opal/PRINCIPLES.md` Core Stance, task:076 PLAN§1.5).
- 진행 상태 집계·그룹핑을 소유자가 매번 손으로 재계산하는 부담을 없애고, 트리거·타이밍·페이로드를 도구가 결정하도록 옮겼다 (근거: task:076 PLAN§3.1.2 DEC-1).

## 결정 내용

- 진행 SSOT 도구가 init/advance/mark/block 응답에 단계 단위 미러 페이로드(`todo_mirror`)를 결정론 생성해 표준출력으로만 내보낸다. 파생 상태 규칙은 단계 내 행 상태를 집계해 전부 완료면 completed, 전부 미착수면 pending, 그 외 혼합·진행·블로커면 in_progress로 매핑한다 (`opal/tools/state-tool/state_tool.py`의 `build_todo_mirror`).
- 세션 확인 행처럼 해당없음(na)인 행은 집계에서 중립 처리하여 미착수 단계가 진행 중으로 오판되지 않게 한다 (task:076 PLAN§3.1.2 DEC-2).
- PostToolUse hook이 SSOT 도구 호출을 감지해 미러 페이로드와 갱신 지시를 세션 컨텍스트에 주입하고, 소유자는 생성(create)이면 새 할일 생성, 갱신(update)이면 단계별 상태 갱신으로 기계적으로 릴레이한다.
- 미러는 읽기 전용 거울이며 진행 SSOT는 여전히 진행 상태 도구다. 미러 페이로드는 상태 파일에 영속하지 않고 응답 페이로드로만 흐른다(스키마 additionalProperties 위반 회피, task:076 PLAN§3.1.2 DEC-4).

## 영향 범위

- `opal/tools/state-tool/state_tool.py` — 미러 페이로드 헬퍼 및 4개 서브명령 응답에 페이로드 추가
- `opal/tools/state-tool/todo_mirror_hook.py` — PostToolUse 릴레이 헬퍼
- `opal/core/hooks/claude-hooks.json` — PostToolUse 이벤트(Bash 매처) 추가
- `opal/core/references/harness/state.md` — §파이프라인 todo 미러를 hook 강제 방식으로 재서술

## 관련 페이지

- [[state-tool]]
- [[opal-principles-constitution]]
- [[native-todo-panel-llm-only-hook-boundary]]
- [[install-hook-ownership-marker-idempotent-upsert]]
- [[kanban-pipeline-stage-grouping]]
