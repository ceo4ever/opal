# AGENTIC-LOG: 001-coding-principles-ssot

> 모드: semi-agentic
> 자율 진입 시점: 2026-05-12 11:11 (PLAN 행 11 user-confirm 직후)
> 자율 종료 시점: CLOSE 진입 직전 (사용자 게이트)

---

## 자율 구간 정의

semi-agentic 모드 경계 — PLAN 사용자 확인(행 11) 통과 후 EXECUTE/QA/PM Gate 구간을 PM 자율로 진행. CLOSE 진입(행 19)은 사용자 승인 필수.

## 진입 시점 사전 결정

| # | 결정 | 근거 |
|---|------|------|
| A-1 | EXECUTE 단일 워커 디스패치 — `opal-task-agent` × `op-task-execute` | opp 파이프라인은 PLAN agent 필드 분배 없음. Framework 영역 단일 에이전트 (PROJECT.md "프로젝트 구성") |
| A-2 | 8 Step 모두 단일 컨텍스트 순차 실행 | 워커가 PLAN.md §4 Phase 구조를 인식하되 단일 디스패치로 통합 처리. 토큰 효율 + 의존 보장 (Step 1 → 나머지) |
| A-3 | EXECUTE 완료 후 QA Gate → PM Gate 자동 진행 | semi-agentic 모드 자율 구간. QA Fail 발견 시 단계별 mark는 PM이 수행 |
| A-4 | install 재실행 안내는 사용자 보고(EXECUTE 완료 후)에 포함 | F-2 에이전트 3종 수정은 `~/.opal/agents/` 배포 필요. 사용자 게이트 |

## 자율 결정 로그 (EXECUTE 진행 중 추가 기록)

### EXECUTE 단계

- (워커 결과 수신 후 갱신)

### QA Gate (EXECUTE)

- (수행 후 갱신)

### PM Gate (EXECUTE)

- (수행 후 갱신)

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-12 11:11 | 초기 생성 — semi-agentic EXECUTE 진입 (001) |
