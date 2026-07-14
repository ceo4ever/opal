---
type: concept
title: 브레인 프라임 연결 풀 아키텍처 결정
tags:
- brain
- latency
- architecture
- pool
- prewarm
- fastapi
sources:
- task:060
related:
- brain-query-latency-model
- cold-warm-session-separation
- warm-handle-single-entry-injection
- pool-lock-idiom-contract
- brain-tool
created: '2026-07-14'
updated: '2026-07-14'
status: active
---
## 개념 요약

console.config.json의 `prewarm_projects`에 지정한 프로젝트를 서버 기동 시(FastAPI `lifespan`) 선프라임하여 프로젝트별 웜 핸들 풀(크기 1)에 적재하고, 새 대화 첫 진입 시 풀에서 체크아웃한 핸들을 즉시 이식(ready)한 뒤 백그라운드로 리필하는 구조다.

## 배경·문제 (WHY)

- 브레인 질의 콜드 프라임은 서브프로세스(`claude -p`) 기반이라 초 단위 지연이 불가피하다([[brain-query-latency-model]] 참조) — 새 대화 첫 질의마다 이 지연을 겪는 것을 줄이려는 목적.
- 소유자가 자주 여는 지정 프로젝트에 한정해 미리 프라임해두면, 새 대화 시작 시점에 이미 준비된 세션을 이식할 수 있다.
- 무상태 원칙(backend는 Q&A 내용을 저장하지 않는다)을 유지해야 하므로 풀은 DB·파일 영속이 아닌 인메모리 전용으로 결정했다(대안: 파일 영속 캐시는 무상태 원칙 위배로 기각).

## 결정 내용 (HOW)

- **지정 프로젝트 선프라임**: `console.config.json`의 `prewarm_projects` 리스트에 있는 프로젝트만 대상. 필드 부재·빈 배열·비-list 값은 모두 빈 리스트로 폴백한다(`dashboard/backend/config.py` `_coerce_str_list`).
- **프로젝트별 풀(크기 1)**: `BrainSessionRegistry`에 `_pool: dict[project_path, list[session_id]]` 형태로 통합 — 별도 모듈 싱글턴을 신설하지 않고 기존 레지스트리에 속성으로 편입했다(`dashboard/backend/adapters/brain_session.py:190-234` 부근).
- **기동 훅**: FastAPI `@app.on_event`(deprecated) 대신 `lifespan` asynccontextmanager를 신설해 prewarm 대상을 비블로킹 디스패치한다(`dashboard/backend/main.py:33-37`). uvicorn 기본값이 `lifespan="auto"`라 `console.sh`의 CLI 변경이 불요하다.
- **체크아웃+백그라운드 리필**: 새 대화 진입 시 풀에서 lock 하 pop(비블로킹)으로 핸들을 꺼내 즉시 이식하고, 곧바로 백그라운드 스레드로 리필을 트리거한다(관용구 상세는 [[pool-lock-idiom-contract]] 참조).
- **Semaphore(2) 상한**: 동시 프라임(선프라임 N개 + 리필)이 몰려도 구독 API 호출이 폭주하지 않도록 `threading.Semaphore(max_concurrent_prime=2)`로 동시 실행 수를 제한한다.
- **콜드 폴백**: 풀이 비어 있으면 세션은 `idle`로 남고 기존 콜드 프라임 경로를 그대로 탄다 — 회귀 없음.
- **인메모리 전용**: 프로세스 종료 시 풀은 소멸한다. 별도 정리·영속화 로직을 두지 않는다(무상태 원칙 유지).
- **실측**: 새 대화 첫 질의 웜 9.6s vs 콜드 26.7s(2.8배 단축). 선프라임 자체는 37.1s 소요하나 백그라운드 처리라 사용자 대기가 없다.

## 영향·관계

- `dashboard/backend/config.py` — `ConsoleConfig.prewarm_projects` 필드 신설.
- `dashboard/backend/adapters/brain_session.py` — `BrainSessionRegistry` 풀 상수·속성·메서드 3종(`prewarm`/`_prime_into_pool`/`checkout_warm_handle`) 신설.
- `dashboard/backend/main.py` — `lifespan` 훅 신설, `FastAPI(lifespan=...)` 연결.
- `docs/ARCHITECTURE.md` §OPAL Console 브레인 — "프라임 연결 풀" 행 추가.
- API 계약(`routers/brain.py`)·FE는 무변경 — 웜 주입 지점은 `_get_or_create()` 단일 진입점([[warm-handle-single-entry-injection]] 참조).
- [[cold-warm-session-separation]] — 웜/콜드 세션 분리 설계와 개념적으로 연관.
- [[brain-tool]] — 풀 지식 자체가 이 도구를 통해 ingest된다.

## 근거 출처

- task:060 PLAN.md F-002/F-003/F-005, DONE.md 실측 결과.
