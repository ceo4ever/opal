"""
@header {
  "module": "e2e",
  "layer": "util",
  "domain": "opal-tools",
  "description": "T01 실행 스켈레톤 — 임대 포트 위에서 source E2E SUT(backend/frontend)를 기동·health-gate·회수하는 최소 골격 패키지. allocator lock·lease record·stale 회수·worktree 동시성(T03)과 run 상태 머신·CLI·verdict(T04)는 이 패키지가 소유하지 않는다(PLAN.md §범위 경계).",
  "exports": []
}

lib.e2e — T01 최소 골격 패키지. 하위 모듈: process, ports, runtime.
re-export를 두지 않는다(PLAN.md D-7) — 소비자는 `from lib.e2e import ports`처럼 하위 모듈을 직접 import한다.
"""
