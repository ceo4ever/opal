---
type: concept
title: 웜 핸들 단일 진입점 주입 결정
tags:
- brain
- session
- api-compat
- dependency-injection
sources:
- task:060
related:
- brain-prime-connection-pool-design
- pool-lock-idiom-contract
- cold-warm-session-separation
created: '2026-07-14'
updated: '2026-07-14'
status: active
---
## 개념 요약

풀에서 체크아웃한 웜 핸들을 새 세션에 이식하는 지점을 `BrainSessionRegistry._get_or_create()` 단일 진입점으로 한정한 결정이다. 이 지점 하나만 확장함으로써 라우터(API 계약)를 전혀 건드리지 않고 웜 주입 기능을 추가했다.

## 배경·문제 (WHY)

- `_get_or_create()`는 `ConversationBrainSession` 생성의 유일한 진입점이며, prime/ask/submit_job/status 등 모든 라우터 경로가 이를 경유한다(`dashboard/backend/adapters/brain_session.py:486-501`) — 여기 한 곳만 확장하면 다른 진입점을 건드릴 필요가 없다.
- 라우터(`routers/brain.py`)의 요청/응답 스키마를 그대로 유지해야 프론트엔드·API 계약에 영향이 없다 — 라우터 무변경이 이 결정의 핵심 제약.
- 웜 이식과 콜드 프라임 경합(동시에 두 경로가 같은 세션 상태를 건드리는 엣지 케이스)이 있을 수 있어, 방어적으로 이미 웜이거나 프라임 진행 중인 세션에는 이식을 적용하지 않도록 가드를 추가했다(대안: 경합 무시는 상태 오염 리스크로 기각, PLAN Gate에서 발견 후 PM 지시로 보강).

## 결정 내용 (HOW)

- **주입 지점**: `_get_or_create()`가 세션을 **신규 생성한 경우에만** 레지스트리 락 해제 후 `checkout_warm_handle()` → `adopt_warm_handle()` 순으로 이식한다. 기존 세션 재사용 시에는 이식을 시도하지 않는다.
- **API 계약 불변**: `routers/brain.py`(prime/query/status 엔드포인트)는 무변경 — 웜 주입은 레지스트리 내부에서 흡수된다.
- **콜드 폴백 회귀 없음**: 풀이 비어 있으면 `checkout_warm_handle()`이 `None`을 반환하고, 세션은 `idle`로 남아 기존 콜드 프라임 경로를 그대로 탄다.
- **`adopt_warm_handle` 방어 가드**: 세션이 이미 웜(warm)이거나 프라임 진행 중(priming)인 상태에서는 이식을 no-op으로 처리한다. 이는 웜 주입과 콜드 프라임이 경합하는 엣지 케이스에 대한 방어책이다.
- **stale 핸들 방어**: 이식된 웜 핸들의 `--resume`가 실패해도, 기존 `_warm_ask()`의 투명 재프라임(콜드 1회) 경로가 그대로 흡수한다(`brain_session.py:359-363`) — 추가 코드 없이 기존 경로 재사용.

## 영향·관계

- `dashboard/backend/adapters/brain_session.py` — `BrainSessionRegistry._get_or_create()`, `ConversationBrainSession.adopt_warm_handle()`.
- `dashboard/backend/routers/brain.py` — 무변경(영향 없음, 검증 대상으로만 포함).
- [[brain-prime-connection-pool-design]] — 이 주입 지점이 소비하는 풀 체크아웃 API.
- [[pool-lock-idiom-contract]] — 체크아웃·이식 시 준수하는 락 관용구.
- [[cold-warm-session-separation]] — 웜/콜드 세션 분리 설계와 연관.

## 근거 출처

- task:060 PLAN.md F-004 §3.4.2 (코드 스니펫·동시성 계약), AGENTIC-LOG #7·#8 (PLAN Gate 경합 발견·가드 보강 지시).
