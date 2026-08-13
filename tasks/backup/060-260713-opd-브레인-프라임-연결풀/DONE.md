# DONE: OPAL Console 브레인 프라임 연결 풀 — 지정 프로젝트 선프라임 + 새 대화 웜 핸들 배정

> 완료일: 2026-07-14 16:23 KST | 적용 스킬: opd (agentic) | 태스크: 060

## 목표 달성

`console.config.json`의 `prewarm_projects`에 지정한 프로젝트를 서버 기동 시(lifespan) 선프라임하여 프로젝트별 웜 핸들 풀(크기 1)에 적재하고, 새 대화 첫 진입 시 풀에서 lock 하 체크아웃→세션 이식(즉시 ready·첫 질의 `--resume` 웜)→백그라운드 리필하는 구조를 신설했다. **실기동 실측: 새 대화 첫 질의 웜 9.6s vs 콜드 26.7s (2.8배 단축).** 기존 브레인 API 5종 계약·FE 불변, 풀은 인메모리 전용(무상태 원칙 유지).

## 변경 파일

| 파일 | 변경 |
|------|------|
| `dashboard/backend/config.py` | `ConsoleConfig.prewarm_projects` 필드 + `_coerce_str_list` 타입 가드 (F-1) |
| `dashboard/backend/adapters/brain_session.py` | 풀 상수 3종 / `BrainSessionRegistry.prewarm`·`_prime_into_pool`·`checkout_warm_handle`(락 하 pop→락 해제→subprocess→재획득 append 관용구, Semaphore(2) 상한) / `ConversationBrainSession.adopt_warm_handle`(웜/priming 시 no-op 방어 가드) / `_get_or_create` 신규 세션 한정 웜 주입 (F-2·F-4) |
| `dashboard/backend/main.py` | `lifespan` asynccontextmanager 신설 — prewarm 비블로킹 디스패치, `FastAPI(lifespan=)` 연결 (F-3) |
| `dashboard/backend/tests/test_brain.py` | 신규 4클래스 15케이스(풀·웜주입·lifespan·픽스처 회귀) + `reset_brain_registry` 풀 클리어 확장 + stale 단언 1건 계약 유지 갱신(400c03a 여파) |
| `dashboard/backend/tests/test_config.py` | 신규 — config 5variant 파싱 5케이스 (S-1) |
| `docs/ARCHITECTURE.md` | §OPAL Console 브레인 표 "프라임 연결 풀" 행 신설 + 변경이력 (S-13 캡틴 리뷰 승인) |

## 검증 증거

- **RED-first(강제 트랙)**: 구현 전 신규 20케이스 전건 RED(TypeError/AttributeError) → scenario-red 13/13 → scenario-lock → `verify --red-check` 통과 → GREEN 전환. 단언 약화 0(플레이키 4건은 Event 동기화로만 수리).
- **자동 검증**: 시나리오 S-1~S-11 전건 Pass, 전체 스위트 235 passed·1 skipped·0 failed (PM 직접 재실행 교차 확인), 신규 클래스 10회 반복 0 flaky.
- **실기동(S-12, 캡틴 승인)**: 선프라임 로그(`prewarm 완료 pool=1`, prime 37.1s) → 새 대화 웜 9.6s / 대조군 콜드 26.7s·선프라임 0건·COLD 폴백 정상. 구독 호출 3회 예산 준수, config·데몬 원복 확인.
- **컨벤션**: GC-CONVENTION-2607141612.md — Critical 0/High 0/Medium 1(사전존재 exports drift)/Low 2.
- **보안**: 시크릿 0건, API 키·SDK·--safe-mode·--bare 미사용(구독 claude -p만), .gitignore 정상.
- scenario-status: `{"total": 13, "red_confirmed": 13, "passed": 13, "failed": 0}` — 상세: TEST-SCENARIO.md.

## 운영 기록 (특이사항)

- ANALYSIS light(haiku) 워커가 API 오류(Connection closed) 3회 연속 중단 → standard(sonnet) 교체 디스패치로 해소 (AGENTIC-LOG #2·#3).
- PLAN Gate에서 웜 주입-콜드 프라임 경합 엣지 발견 → `adopt_warm_handle` 방어 가드(웜/priming 시 no-op)를 PM 지시로 보강 (AGENTIC-LOG #7·#8).
- Step 5를 opal-be-agent→opal-test-agent로 교체 배정 — 테스트 수정 수반 작업의 작성자≠구현자 원칙 유지 (AGENTIC-LOG #14).
- mypy 미설치로 typecheck 게이트 불가(ruff PASS) — 설치는 캡틴 승인 사안이라 미실행 (AGENTIC-LOG #16).

## 잔여·후속 액션

1. **커밋**: 캡틴 지시 대기 — 대상: `dashboard/backend/` 5파일 + `docs/ARCHITECTURE.md` + `tasks/060-*/` + `.opal/MEMORY.md`(채번·히스토리).
2. **배포**: install/update 재배포 후 `~/.opal/dashboard-server/`에 반영 필요 (현재 배포본은 구코드로 정상 가동 중).
3. **후속 태스크(캡틴 확정)**: 콘솔 프로젝트별 환경 설정 화면 — 프라임 풀 토글 + console.config 전반 + 프로젝트 로컬 `.opal/setting.local.json` 편집 (범위 확정: 2026-07-14 AskUserQuestion).
4. **선행 잔여(059 후속)**: `opbr_adapter.py` raw `claude -p` → opal-agent 이관 — 이번 풀 구조와 독립적이며 이관 시 `_prime_into_pool` 경로도 함께 전환.
5. **mypy 도입 검토**: typecheck 게이트 상시화 여부 — 캡틴 결정 사안.

## 산출물

TASK.md / ANALYSIS.md / PLAN.md / TEST-SCENARIO.md / test-scenario.json / AGENTIC-LOG.md / GC-CONVENTION-2607141612.md / DONE.md
