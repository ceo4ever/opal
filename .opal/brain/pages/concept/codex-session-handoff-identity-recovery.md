---
type: concept
title: Codex 세션 이관 — 플랫폼 신원 어댑터와 실제 소유자 반영
tags:
- codex
- ownership
- task
sources:
- task:155
related: [ownership-tool, codex-platform-integration, hook-session-identity-from-envelope-only, codex-worktree-boot-ownership-handoff]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

Codex 세션의 고유 신원을 전용 어댑터에서 해석해, 워크트리 세션 이관 때 실제 자식 세션이 소유자로 기록되도록 복구한 결정이다. OPAL 중립 신원, 기존 Claude 우선순위, 훅의 봉투 전용 경계는 보존했다(`tasks/155-260924-opds-코덱스-세션-이관-복구/DONE.md:5`, `opal/tools/ownership-tool/ownership_tool/codex_adapter.py`).

## 핵심 결정

- 공개 세션 기동 명령은 부모 신원을 제거한 뒤 원래 명령을 실행하고, Codex 부트스트랩의 시작 절차는 실제 새 신원으로 등록·소유권 획득·생존 신호를 수행한다. 등록 실패를 성공으로 숨기지 않는다(`tasks/155-260924-opds-코덱스-세션-이관-복구/DONE.md:5`).
- 런처는 시작 신원을 고정해 이관·취소에 명시 전달하고, 신원 부재나 다른 살아 있는 소유자는 변경 전에 거부한다. 최종 등록부는 실제 자식 소유자를 소유권 기록에서 가져와 반영한다(`tasks/155-260924-opds-코덱스-세션-이관-복구/DONE.md:7`).
- 상태 전이·실행 로그 주체·워크트리 체크포인트도 같은 공통 신원 해석기를 쓴다(`tasks/155-260924-opds-코덱스-세션-이관-복구/DONE.md:7`).

## 관련 페이지

- [[ownership-tool]]
- [[codex-platform-integration]]
- [[hook-session-identity-from-envelope-only]] · [[codex-worktree-boot-ownership-handoff]]
