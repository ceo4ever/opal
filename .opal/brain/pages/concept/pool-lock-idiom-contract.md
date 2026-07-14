---
type: concept
title: 프라임 풀 락 관용구 계약
tags:
- brain
- concurrency
- locking
- pattern
sources:
- task:060
related:
- brain-prime-connection-pool-design
- warm-handle-single-entry-injection
created: '2026-07-14'
updated: '2026-07-14'
status: active
---
## 개념 요약

`BrainSessionRegistry`의 프라임 풀에서 서브프로세스(`claude -p`) 호출과 락 보호 상태를 안전하게 분리하기 위한 락 관용구 계약이다. "락 하 pop(비블로킹) → 락 해제 → subprocess → 락 재획득 append" 순서를 지키며, 두 종류 락(`_lock`, `_pool_lock`) 간에는 일방향 획득 순서만 허용한다.

## 배경·문제 (WHY)

- 서브프로세스 호출(`claude -p`)은 초 단위로 블로킹되므로, 락을 쥔 채로 호출하면 다른 요청이 락 대기로 정체된다 — 교착·응답 지연 리스크.
- 레지스트리 전체를 보호하는 기존 `_lock`과 풀 전용 `_pool_lock`을 하나로 합치면 락 경합 범위가 불필요하게 넓어진다 — 별도 락으로 분리하되 순서를 고정해 교착을 원천 차단하기로 결정했다(대안: 단일 락 통합은 경합 범위 확대로 기각).

## 결정 내용 (HOW)

- **관용구**: 상태를 변경하는 모든 풀 연산은 "락 하 비블로킹 작업 → 락 해제 → subprocess(락 미보유) → 락 재획득 → 결과 커밋" 순서를 따른다. 예: `checkout_warm_handle`은 `_pool_lock` 하에서 `pop()`만 수행하고(`brain_session.py` `checkout_warm_handle`), 리필 트리거(`prewarm`)는 락 밖에서 호출한다. `_prime_into_pool`은 서브프로세스 호출 전체를 락 밖에서 실행하고, 완료 후 `_pool_lock`을 재획득해 결과를 append한다.
- **락 순서 계약**: `_lock`(레지스트리) → `_pool_lock`(풀) 방향만 허용한다. 역순 획득이나 `_pool_lock` 보유 중 `_lock`·세션별 `_lock` 획득은 금지한다.
- **subprocess 중 락 보유 금지**: 어떤 락(레지스트리 락·풀 락·세션 락)도 subprocess 호출 구간에서는 보유하지 않는다. 이는 기존 `ConversationBrainSession.prime()`/`_cold_and_ask()`/`_warm_ask()`(`brain_session.py:206-234, 316-339, 342-363`)가 이미 따르던 관용구를 풀에도 동일하게 계승한 것이다.
- **세마포어는 예외**: `_prime_semaphore`(동시 프라임 상한)는 상태 보호용 락이 아니라 동시성 상한 장치이므로, subprocess 구간에서도 보유한 채로 둔다 — 락 관용구와 별개 개념.
- **동시 체크아웃 직렬화**: `_pool_lock` 하의 `pop()`이 동시 체크아웃 요청을 직렬화하므로, 동시에 두 요청이 들어와도 같은 핸들이 중복 배정되지 않는다(서로 다른 핸들이거나 하나는 `None`).

## 영향·관계

- `dashboard/backend/adapters/brain_session.py` — `BrainSessionRegistry.prewarm`/`_prime_into_pool`/`checkout_warm_handle`, `ConversationBrainSession.adopt_warm_handle`이 이 계약을 따른다.
- 후속 풀 확장(풀 크기 증가, 프로젝트 추가 등) 시에도 이 관용구·순서 계약을 유지해야 교착·중복 배정을 피할 수 있다.
- [[brain-prime-connection-pool-design]] — 이 계약이 적용되는 상위 아키텍처 결정.
- [[warm-handle-single-entry-injection]] — 이 관용구를 재사용하는 웜 이식 지점.

## 근거 출처

- task:060 PLAN.md F-002 §3.2.2 (락 순서 계약·코드 스니펫).
