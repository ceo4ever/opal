---
type: concept
title: OPPL 실행 안정화 — 유한 예산 안의 수렴
tags:
- oppl
- runtime
- proposal
sources:
- doc:docs/proposals/archives/opal-oppl-runtime-stabilization.md
related: [oppl-two-loop-orchestrator, opal-action-monitor, long-running-worker-infra-failure-mitigation]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

수렴형 프로젝트용 독립 Pilot인 OPPL의 장시간 실행, 반복 상한, 완료 판정을 도구로 집행하도록 정한 적용완료 제안서다(`docs/proposals/archives/opal-oppl-runtime-stabilization.md:3-6`).

## 핵심 결정

- OPPL은 확정 계약을 처리하는 다른 프로젝트 Pilot의 대체재나 후계가 아닌 독립 Pilot으로 유지한다(`docs/proposals/archives/opal-oppl-runtime-stabilization.md:12-13`).
- 핵심은 무제한 반복이 아니라 유한 예산 안의 수렴이다. "한 번의 설계 승인으로 목표·계약·백로그를 잠글 수 있는가"에 아니오일 때만 OPPL을 쓰며, 단순 정보 결측이나 기술 난이도만으로는 고르지 않는다(`docs/proposals/archives/opal-oppl-runtime-stabilization.md:15-22`).
- 범위는 두 루프와 태스크 내부 반복의 상한 집행, 장시간 워커의 프로세스 그룹·생존 신호·감시·자식 작업 회수, 결과 이벤트와 프로세스 종료의 결합 판정, 재개 상한, 예산·무진전 시 디스패치 차단이다(`docs/proposals/archives/opal-oppl-runtime-stabilization.md:32-40`).
- 실행 로그 표준화와 잠긴 시나리오 기준선 변경은 다른 결정 영역이라 함께 구현하지 않는다(`docs/proposals/archives/opal-oppl-runtime-stabilization.md:44-54`).

## 관련 페이지

- [[oppl-two-loop-orchestrator]]
- [[opal-action-monitor]]
- [[long-running-worker-infra-failure-mitigation]]
