---
type: concept
title: 브레인 질의 비동기 잡+폴링 전환 — 동기 HTTP 블로킹 제거 패턴
tags: [architecture, brain, async, polling, fetch-timeout]
sources: [task:037]
related: [opal-console, brain-tool, daemon-as-tool-orchestrator]
created: 2026-06-23
updated: 2026-06-23
status: active
---

## 개요

브레인 질의(`POST /api/brain/query`)가 콜드(≈69초)·웜(≈20초) 어느 경로든 동기 블로킹하여 브라우저 fetch 타임아웃(Safari ≈60초)에 끊기는 구조적 결함을, **비동기 잡 제출 + 결과 폴링 패턴**으로 근본 해소한 설계 결정.

## 결정 배경 (WHY)

- 브레인 질의의 실제 처리 시간이 브라우저 fetch 타임아웃(≈60초)을 초과했다. 콜드(in-agent 멀티턴 루프 ≈69초)는 물론 웜(≈20초)도 조건에 따라 타임아웃 위험이 있었다.
- 동기 FastAPI 엔드포인트가 threadpool 스레드를 장시간 점유하고, 프런트엔드 fetch가 OS/브라우저 타임아웃으로 "Load failed"(Safari 전형 증상)를 반환하는 구조였다.
- OPAL Console에는 `prime-on-intent` 패턴(`dashboard/backend/routers/brain.py:182-197`)이 이미 비동기 청사진으로 구현되어 있었다 — 동일 패턴을 query에 재사용.

## 결정 내용

- **POST /query → job_id 즉시 반환**: 엔드포인트가 백그라운드 스레드(`daemon=True`)를 기동하고 `job_id`(uuid4)만 즉시 반환. 실제 `ask` 호출(콜드/웜 분기 포함)은 백그라운드에서 수행.
- **GET /job/{job_id} 신설**: `pending → done/error` 상태 전이를 폴링으로 조회. 잡 결과는 인메모리(`_current_job` dict), DB/파일 영속 금지(무상태 원칙 준수 — `brain_session.py:6`).
- **잡 상태 저장 위치**: `ConversationBrainSession._current_job` (옵션 A) — 세션 1:1 잡 매핑. 단일 사용자 데몬 규모에 적합, 별도 JobRegistry는 과설계.
- **idempotent 제출(RI-2 방어)**: 진행 중 잡이 있으면 기존 job_id 반환(덮어쓰기 없음). FE의 `isPending` disable(1차)과 이중 방어.
- **TTL**: done/error 수신 후 `get_job`이 `_current_job=None`으로 즉시 제거. 시간/개수 상한 없음(세션당 1잡 구조).
- **콜드 잡 흡수**: `_cold_and_ask`의 `_state="priming"` 전이(`brain_session.py:299-301`)가 잡 흐름에 자연 흡수. 인라인 폴백 분기 불필요.
- **FE 폴링**: `["brain-job", project, sessionId, jobId]` 별도 useQuery, `refetchInterval: 2000ms (done/error 시 false)`. status 폴링(`BrainPage.tsx:482-487`) 패턴 재사용.
- **apiClient 타임아웃 가드**: 선택적 `timeoutMs` + AbortController. 미전달 시 5화면 동작 불변. AbortError → "요청 시간이 초과되었습니다" 메시지 변환 (apiClient 내부 catch).

## 영향 범위

- `dashboard/backend/models.py` — `BrainJobSubmitResponse`, `BrainJobResponse` 신규
- `dashboard/backend/adapters/brain_session.py` — `_current_job`, `submit_job`, `get_job`, `_run_job_background`
- `dashboard/backend/routers/brain.py` — `POST /query` 전환, `GET /job/{id}` 신설
- `dashboard/frontend/src/pages/brain/BrainPage.tsx` — submitMutation + 잡 폴링 useQuery + 아코디언 Q&A UI
- `dashboard/frontend/src/lib/api.ts` — `timeoutMs` 옵션 추가

## 관련 페이지

- [[opal-console]]
- [[brain-tool]]
- [[daemon-as-tool-orchestrator]]
