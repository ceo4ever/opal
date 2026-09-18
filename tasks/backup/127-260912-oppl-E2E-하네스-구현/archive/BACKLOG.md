# BACKLOG: OPAL 범용 E2E 하네스

> 최종 갱신: 2026-09-12 21:54
> 모드: agentic
> 목표: 제안서 태스크 2~9를 구현해, 격리된 소스 트리에서 Browser·API·Hybrid·Collaborative·Manual E2E를 공통 판정·증적 계약으로 실행하고 Playwright 기본 설치를 제거한다

<!-- backlog:start -->
## 백로그

> 상태값: pending / in_progress / done / blocked

| ID | 제목 | 영역 | 우선순위 | 상태 | 의존 | 커버 표면 |
|----|------|------|--------|------|------|----------|
| T01 | 실행 스켈레톤 — 주소 주입·CORS 포함, 임대 포트로 Console BE/FE 기동 + FE→BE 실 호출 1건 관통 | 공통 | P0 | done | - | sut-health, sut-dashboard |
| T02 | Console 프로세스 소유권 — PID 레코드 전환과 광역 pkill 2지점 제거 | 공통 | P0 | done | T01 | console-start, console-stop, console-status |
| T03 | Runtime Manager — target 해석·포트 임대·SUT 기동·health·소유 정리와 e2e run CLI | 공통 | P0 | pending | T01, T02 | e2e-run |
| T04 | e2e status·clean 서브명령과 소유 자원 대장 기반 정리 | 공통 | P1 | pending | T03, T10 | e2e-status, e2e-clean |
| T05 | Browser driver·session 계약 + driver manifest + 증적 수집·redaction 관문 | 공통 | P0 | pending | T03 | driver-probe, driver-open, driver-snapshot, driver-act, driver-wait, driver-assert, driver-capture, driver-close |
| T06 | 판정 부정 검증 — 증적·assertion 누락 시 pass 불가 집행 | 공통 | P0 | pending | T03 | - |
| T07 | agent-browser 공용 driver — orca-managed·standalone 단일 adapter | 공통 | P1 | pending | T05 | - |
| T08 | cmux driver 이전 — mode A 소유권 유지 + assertion 필수화 | 공통 | P1 | pending | T05 | - |
| T09 | API executor — 실제 SUT 호출·후속 상태 assertion·owned fixture 정리 | 공통 | P1 | pending | T03 | api-executor-probe, api-executor-prepare, api-executor-act, api-executor-assert, api-executor-capture, api-executor-cleanup |
| T10 | Human handoff executor — pause·resume·timeout·구조화 증적 | 공통 | P1 | pending | T03 | human-executor-handoff, human-executor-resume, e2e-resume |
| T11 | Hybrid profile 연결과 surface fidelity gate | 공통 | P1 | pending | T07, T09 | - |
| T12 | SUT HTTP 표면 전수 E2E 시나리오 스위트 (통합) | 통합 | P1 | pending | T08, T10, T11 | sut-dashboard, sut-projects-list, sut-projects-detail, sut-projects-doc, sut-tasks-list, sut-tasks-detail, sut-tasks-artifact, sut-memory, sut-doctor, sut-brain-auth, sut-brain-status, sut-brain-prime, sut-brain-query, sut-brain-job, sut-config-get, sut-config-prewarm |
| T13 | Playwright 소비자 이전 — 9개 area + 추가 발견 7건 | 공통 | P2 | pending | T07, T08 | - |
| T14 | Playwright 기본 설치 제거와 clean install 회귀 검증 | 공통 | P2 | pending | T13 | - |
| T15 | 전체 통합 검증 — 수용 기준 AC-1~AC-14 관통과 문서 갱신 (통합) | 통합 | P2 | pending | T04, T06, T12, T14 | - |
| T16 | PID 재사용 방어 — 부팅 시각 기준 stale 판정과 .oppl-run gitignore | 공통 | P0 | pending | T02 | - |
<!-- backlog:end -->
