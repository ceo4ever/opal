---
type: concept
title: Codex 워크트리 부팅 — 자식 소유권 확인 후 허브가 소유자 확정
tags:
- codex
- worktree
- task
sources:
- task:163
related: [worktree-session-launch-order-and-ownership, ownership-tool, worktree-tool, codex-session-handoff-identity-recovery]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

Codex 자식 세션이 작업 소유권을 얻은 것을 기다린 뒤에야 허브 런처가 같은 세션 신원을 등록부 소유자로 확정하도록 바꾼 결정이다(`tasks/163-260927-opds-코덱스-워크트리-부팅-소유권-복구/DONE.md:5`).

## 핵심 결정

- 소유자가 확정되지 않은 상태로 "소유자 없는 성공"을 기록하지 않는다. 실패하면 터미널·소유권 확인 결과에 따라 허브 소유로 되돌리거나 복구 필요 상태를 남긴다(`tasks/163-260927-opds-코덱스-워크트리-부팅-소유권-복구/DONE.md:5`).
- 등록부 잠금에서 권한이 거부되면 기다리지 않고 즉시 쓰기 거부 오류로 돌려준다. 소유권을 가진 Codex 자식은 허브 확정에 맡긴다는 진단과 함께 부팅을 이어 간다(`tasks/163-260927-opds-코덱스-워크트리-부팅-소유권-복구/DONE.md:5`).
- 설치본 실측에서 실패 기동은 부팅 시간 초과 뒤 허브 소유로 복귀했고, 성공 기동은 자식의 소유권과 등록부 소유자가 일치했다(`tasks/163-260927-opds-코덱스-워크트리-부팅-소유권-복구/DONE.md:23`).

## 관련 페이지

- [[worktree-session-launch-order-and-ownership]]
- [[ownership-tool]] · [[worktree-tool]]
- [[codex-session-handoff-identity-recovery]]
