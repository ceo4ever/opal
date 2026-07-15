---
type: concept
title: 프라임 풀 need 기반 충전 결함 수정
tags:
- brain
- pool
- prewarm
- concurrency
- bugfix
sources:
- task:063
related:
- brain-prime-connection-pool-design
- pool-lock-idiom-contract
- console-settings-incremental-scope-policy
- console-brain-volatile-single-session
created: '2026-07-15'
updated: '2026-07-15'
status: active
---
## 개념 요약

프라임 풀의 목표 크기(pool_size) 상수만 올려서는 풀이 실제로 채워지지 않는 설계 결함(H-1)을 발견하고, 충전 로직을 "부족분(need = pool_size - have)만큼 충전"하도록 수정한 결정이다.

## 배경·문제 (WHY)

- [[console-brain-volatile-single-session]] 전환에 따라, 연속으로 "새 대화"를 여러 번 눌러도 매번 웜 핸들이 즉시 배정되어야 한다는 요구(R-6)가 생겼다. 이를 위해 풀 크기 상수를 1에서 2로 올리는 것만으로 충분해 보였다.
- 그러나 기존 충전 함수는 풀이 목표치보다 부족할 때 정확히 1개의 충전 스레드만 기동하도록 짜여 있었다(task:060 최초 설계 시점에는 풀 크기가 1이었기 때문에 이 결함이 드러나지 않았다). 그 결과 풀 크기 상수를 2로 올려도 단일 충전 트리거로는 풀이 최대 1까지만 차고, 연속 새 대화 2회째는 여전히 콜드로 떨어지는 문제가 있었다.
- 이는 구현 단계의 실수가 아니라 설계 단계의 결함이며, PLAN 단계 코드 분석에서 사전에 발견되어 구현 전에 수정 방향이 이미 확정되었다(리스크 가설 표 H-1).

## 결정 내용 (HOW)

- 충전 함수가 "현재 보유량(진행 중 포함)"과 "목표 풀 크기"의 차이(`need = pool_size - have`)를 계산해, 그 부족분만큼 충전 스레드를 기동하도록 수정했다(`dashboard/backend/adapters/brain_session.py:560-578` `prewarm`). 부족분이 0 이하면 아무 것도 하지 않는다.
- 기존의 락 순서 계약([[pool-lock-idiom-contract]] — 락은 상태 갱신 구간만 짧게 쥐고, subprocess 호출은 락 밖에서 수행)과 동시 프라임 상한(세마포어)은 그대로 유지된다. 부족분만큼 스레드를 여러 개 기동해도, 실제 동시 서브프로세스 실행 수는 세마포어가 상한(`DEFAULT_MAX_CONCURRENT_PRIME=2`, `brain_session.py:49`) 이하로 직렬화한다.
- 풀 목표 크기 자체는 2로 확정했다(`brain_session.py:48` `DEFAULT_POOL_SIZE`). 로컬 단일 사용자 데몬에서 "오픈 1개 소비 + 새 대화 즉시 1개 여유"를 커버하는 수준이며, 더 키우는 것은 매 프라임이 별도 프로세스(토큰·CPU 비용)를 띄우는 점을 고려하면 과함으로 판단했다.

## 영향·관계

- [[brain-prime-connection-pool-design]] — task:060에서 확립된 풀 아키텍처의 충전 로직에 대한 결함 수정.
- [[pool-lock-idiom-contract]] — 이 수정이 그대로 준수하는 락·동시성 계약(락 순서·subprocess 락외 실행 원칙은 변경 없음).
- [[console-settings-incremental-scope-policy]] — 웜 배정 효과는 "프라임 풀 토글이 켜진(opt-in)" 프로젝트에만 적용된다는 범위 한정이 이 결정과 함께 재확인되었다. 풀은 지정 프로젝트에만 적재되므로, 토글이 꺼진 프로젝트는 여전히 매 세션 콜드다.
- [[console-brain-volatile-single-session]] — 이 결함 수정이 뒷받침하는 상위 설계 결정(R-6 연속 새대화 웜 배정).

## 근거 출처

task:063 PLAN.md 리스크 가설 표 H-1(§리스크 가설 표), DONE.md §설계 하이라이트 1.
