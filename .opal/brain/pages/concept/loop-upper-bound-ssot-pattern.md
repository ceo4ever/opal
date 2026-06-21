---
type: concept
title: 루프 상한 SSOT 단일 기재 패턴 — harness 포인터, 수치 복제 금지
tags:
- harness
- ssot
- loop-bound
- anti-pattern
sources:
- task:031
related:
- b7-action-completion-loop
- coding-principles-ssot
created: '2026-06-21'
updated: '2026-06-21'
status: active
---

## 개념 요약

자동 루핑 상한 수치는 `opal/core/references/opal-harness.md` §1 자동 루핑 제약 표에 단독 기재하고, 타 문서는 포인터 참조만 허용하는 패턴. 수치 복제 금지.

## 배경·문제 (WHY)

동일 수치가 여러 문서(harness·agent·guide)에 분산되면 하나 갱신 시 나머지가 드리프트돼 불일치가 재발한다. 태스크 031 ANALYSIS가 "harness·agent·guide 세 곳 모두 수치 기재"를 리스크(R-3)로 식별했다. SSOT를 단일화해야 수치 갱신 시 한 곳만 변경하면 된다.

## 결정 내용 (HOW)

SSOT 위치: `opal/core/references/opal-harness.md` §1 자동 루핑 제약 표.

현재 등록된 상한 행: lint(∞) / build(2) / L3a(3) / L3b(1) / QA(0) / 워커 폴백 반복(1) / PLAN 재진입(재설계 루프, N=2, 태스크 031 신설).

타 문서(AGENT.md, 가이드) = 수치 직접 기재 금지, harness SSOT 포인터 참조만.

위반 패턴: verification-loop-guide, opal-task-action-agent AGENT.md 등에 상한 수치를 직접 기재 → 갱신 시 드리프트 재발.

## 영향·관계

- `opal/core/references/opal-harness.md` — §1 자동 루핑 제약 표 (SSOT 기재)
- `opal/agents/opal-task-action-agent/AGENT.md` — 포인터 참조만
- `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` — 포인터 참조만

교차참조: [[b7-action-completion-loop]], [[coding-principles-ssot]]

## 근거 출처

task:031 — DONE.md §특이사항 "모든 루프 상한 수치는 harness SSOT 단독 기재", PLAN.md §F-026 §H-1
