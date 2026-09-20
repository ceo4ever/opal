# BACKLOG: 태스크 실행 로그 표준화

> 최종 갱신: 2026-09-12 18:04
> 모드: agentic
> 목표: 태스크 실행 이력의 표준 원천을 하나로 수렴시키고, 지원 채널의 워커 완료를 기계 관측 증거로만 인정하도록 Phase 0~1C를 완주한다

<!-- backlog:start -->
## 백로그

> 상태값: pending / in_progress / done / blocked

| ID | 제목 | 영역 | 우선순위 | 상태 | 의존 | 커버 표면 |
|----|------|------|--------|------|------|----------|
| T01 | Phase 0 — 채널 관측 능력 실측 | 공통 | P0 | done | - | adapter.pm-agent-tool, adapter.oppl-headless-cli |
| T02 | 워킹 스켈레톤 — CLI 관통 1건 | 공통 | P0 | done | T01G | state-tool.init.run-log-mode, run-log-tool.init, run-log-tool.append, run-log-tool.validate-run |
| T03 | 기록 코어 — 스키마·출처·멱등·순번 | 공통 | P0 | done | T02 | run-log-tool.show, run-log-tool.append, run-log-tool.import-agentic, run-log-tool.import-oppl |
| T04 | 동시성 — 태스크 배타 락·런타임 색인·조각 경계 전환 | 공통 | P0 | pending | T02 | run-log-tool.begin-worker |
| T05 | 상태 1.2 — 미전송 사건 보관함·중단 가능 초기화 | 공통 | P0 | done | T02 | run-log-tool.reconcile |
| T06 | 마스킹·원본 상한·추적 경계·시간계 | 공통 | P0 | pending | T02 | run-log-tool.export |
| T07 | 그림자 통합 — opds·oppl 변환기와 정량 표본 수집 | 통합 | P0 | pending | T03, T04, T05, T06 | adapter.pm-agent-tool, adapter.oppl-headless-cli |
| T08 | Phase 1B — 완료 게이트·게이트 사건·워커 쓰기 권한 | 공통 | P1 | pending | T07 | state-tool.mark.completion-gate, state-tool.gate-request, state-tool.gate-resolve, run-log-tool.validate-worker |
| T09 | Phase 1B — 워커 시간 자동 파생과 구버전 호환 | 공통 | P1 | pending | T08 | run-log-tool.reconcile-duration |
| T10 | Phase 1B — 복구·사용자 우회·명시적 재실행 | 공통 | P1 | pending | T08 | state-tool.restart-run, state-tool.log-event |
| T11 | Phase 1B — 단방향 가져오기와 조건부 계약 개정 | 공통 | P1 | pending | T08 | run-log-tool.import-agentic, run-log-tool.import-oppl |
| T12 | Phase 1C 배치1 — opd·opdw 확산 | 공통 | P2 | pending | T09, T10, T11 | - |
| T13 | Phase 1C 배치2 — opp·opwt 확산 | 공통 | P2 | pending | T12 | - |
| T14 | Phase 1C 배치3 — opgc·oppd 확산 | 공통 | P2 | pending | T13 | - |
| T15 | Phase 1C 배치4 — opsdd·opdd 확산과 규범 문서 개정 | 통합 | P2 | pending | T14 | - |
| T01G | 게이트 — Phase 1A 승인 (사람) | 공통 | P0 | done | T01 | - |
<!-- backlog:end -->
