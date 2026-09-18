---
type: concept
title: Stop 강제 차단은 상태 전이 claim일 때만 성립한다
tags:
- stop-hook
- ownership
- agentic
- lease
- task-138
sources:
- task:138
related:
- worktree-locates-hub-by-issued-copy
- ownership-tool
- state-tool
- actor-axis-orthogonal-to-mode
created: '2026-09-18'
updated: '2026-09-18'
status: draft
---
## 개요

Stop 훅의 강제 차단 후보는 "이 세션이 태스크를 **전진시켰을 때만**" 성립한다. 워크트리에서 부팅했다는 사실만으로 생긴 소유권은 소유권으로는 유효하되 차단 근거가 아니다. 구분선은 '부팅이냐'가 아니라 '전진시켰느냐'다(근거: task:138 PLAN.md D-21).

## 결정 배경 (WHY)

- SessionStart가 워크트리 cwd에서 lease를 자동 claim하므로, 사용자가 인사만 해도 현재 세션 소유 후보가 1건 생기고 **첫 Stop이 차단**된다. PM이 그 차단을 사용자 지시로 오인해 태스크에 진입하는 사건이 실재했다(근거: task:138 PLAN.md D-21 결정 경위).
- 대안으로 검토된 **부트스트랩 일괄 면제는 기각**됐다. 부팅 여부로 면제하면 실제로 작업한 세션의 첫 Stop까지 면제되어, 선행 태스크들이 복원한 agentic 실행 지속성이 되돌아간다. 면제 기준을 세션의 **행위**에 두어야 두 요구(헛 차단 제거 · 지속성 유지)가 동시에 만족된다.
- 소유권을 없애는 방식도 선택지가 아니었다 — 자동 claim은 타 세션 claim 거부와 heartbeat·release 대상 판정에 필요하다. 그래서 소유권은 유지하고 **차단 자격만** 분리했다.

## 결정 내용

- lease 레코드에 claim 출처를 폐쇄 enum `claim_source`(`session_start` · `state_transition`)로 기록한다. SessionStart 자동 claim은 `session_start`, 상태 전이 시점의 claim은 `state_transition`이다. enum 밖 값은 예외가 아니라 `claim_source_invalid` 거부이며 파일을 쓰지 않는다(`opal/tools/ownership-tool/ownership_tool/lease.py` @header).
- 같은 세션의 재-claim은 멱등을 유지하되 `session_start` → `state_transition` **승격만** 허용하고 강등은 없다. 승격 시 `generation`·`claimed_at`·`owner_session_id`는 불변이다.
- Stop 판정기는 현재 세션 소유 후보 중 `claim_source == state_transition`만 강제 후보로 세운다. `session_start`이면 강제 후보에서 빼고 `passive_ownership` 진단만 남기며, 소유권 분류 자체는 그대로 유지한다(`opal/tools/ownership-tool/ownership_tool/stop_evaluator.py` @header).
- 판정 입력이 된 `claim_source`는 후보 `evidence`에 노출한다 — 차단·통과 사유를 PM이 사후에 재구성할 수 있어야 한다는 같은 계약의 다른 적용이다.
- `claim_source` 키가 없는 구버전 레코드는 `state_transition`으로 접어 현행 동작을 보전한다(하위호환).

## 영향 범위

`opal/tools/ownership-tool/ownership_tool/lease.py`·`stop_evaluator.py`·`session_start_hook.py`와 상태 전이에서 claim을 거는 `opal/tools/state-tool/state_tool.py`. 일반화하면 — **자동으로 만들어진 소유권은 자동으로 차단 권한을 얻지 않는다**. 소유권을 부여하는 시점과 그 소유권으로 사용자를 막는 시점이 다르면, 둘을 같은 레코드의 한 필드로 구분하고 승격만 허용하는 것이 최소 변경이다.

## 관련 페이지

- [[worktree-locates-hub-by-issued-copy]]
- [[ownership-tool]]
- [[state-tool]]
- [[actor-axis-orthogonal-to-mode]]
