---
type: concept
title: 워크트리 tasks 픽스처 구조적 한계 — 절대 수치 대신 기준선 대비 증분
tags:
- worktree
- test-design
- harness
sources:
- task:107
related:
- regression-pin-of-task-time-fact
- regression-only-coverage-gate
created: '2026-09-06'
updated: '2026-09-06'
status: draft
---
## 개요

워크트리 계약상 `tasks/` 디렉터리는 허브에 고정되고 워크트리로 분기하지 않는다. `tasks/` 픽스처를 참조하는 테스트는 이 때문에 워크트리 실행에서 구조적으로 통과할 수 없으며, 회귀 판정은 절대 통과 수치가 아니라 워크트리 기준선 대비 증분으로 해야 한다(근거: `tasks/107-260906-opd-헤더필드-작성기준-이력분리/AGENTIC-LOG.md` "[DECISION] worktree pytest 실패 3건은 진짜 환경 artifact다" 절).

## 결정 배경 (WHY)

- 태스크 107의 Step 7·8 워커가 pytest 실패 3건을 "사전 존재 환경 artifact"로 보고했다. 직전 Step 6에서 같은 주장이 실제로는 오진이었기 때문에 PM이 재현 검증했다(근거: `AGENTIC-LOG.md` 동일 절).
- 재현 결과, 워크트리에서 `python3 -m pytest tests/ -q`는 `3 failed, 394 passed, 6 skipped`였고 실패 원인은 `[RED] 098 TASK.md 실파일 부재: .../.opal-worktrees/task_107/tasks/098-.../TASK.md` — 즉 워크트리에 `tasks/` 디렉터리 자체가 없었다(근거: `AGENTIC-LOG.md` 동일 절).
- 이는 결함이 아니라 워크트리 계약이다 — "태스크 문서(`tasks/`)·`.opal/MEMORY.json`·`.opal/brain/`은 분기하지 않고 허브에 고정"된다(근거: `AGENTIC-LOG.md` 동일 절, `opal-harness.md` §2.5 (3) 인용). 허브에서 동일 스위트를 돌리면 400 passed / 3 skipped / 0 failed였다(근거: `AGENTIC-LOG.md` 동일 절).
- 태스크 107 최종 회귀 4스위트 실측에서도 이 패턴이 재확인됐다 — state-tool 3건 + console BE(저장소 루트 실행) 33건 중 33건이 동일 원인으로 워크트리 전용 실패였고, 총 34건이 "워크트리에서만" 실패했다(근거: `DONE.md` §2 회귀 4스위트 표, §7 (2)).

## 결정 내용

TEST 단계는 워크트리에서 절대 pass 수치("R-5 AC 몇 건 이상 통과")로 판정하면 `tasks/` 픽스처 의존 테스트가 영구히 미달 상태가 되므로, **워크트리 기준선(예: 394/6/3) 대비 증가분이 0인지**로 판정해야 한다(근거: `AGENTIC-LOG.md` 동일 절 "TEST 단계는 「워크트리 기준선(394/6/3) 대비 증가 0」으로 판정해야 한다").

## 영향 범위

`tasks/` 픽스처를 참조하는 모든 pytest/테스트 스위트(state-tool, console BE 등)와, 워크트리 기반 태스크 파이프라인(`--wt`)의 TEST 단계 판정 기준 설계. [[regression-pin-of-task-time-fact]](절대 수치를 영구 계약으로 고정하면 안 된다는 같은 태스크의 자매 발견)와 함께, "절대 기준이 아니라 상대 기준으로 판정하라"는 공통 교훈을 이룬다.

## 관련 페이지

- [[regression-pin-of-task-time-fact]]
- [[regression-only-coverage-gate]]
