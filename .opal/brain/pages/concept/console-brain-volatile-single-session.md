---
type: concept
title: 콘솔 브레인 휘발성 단일 세션 설계 전환
tags:
- brain
- session-management
- architecture
- console
- ux
sources:
- task:063
related:
- cold-warm-session-separation
- brain-prime-connection-pool-design
- opal-console
- brain-prime-pool-need-based-refill
- console-brain-exit-guard-pattern
created: '2026-07-15'
updated: '2026-07-15'
status: active
---
## 개념 요약

콘솔 프로젝트 브레인을 "멀티 대화 관리 + localStorage 이력 영속" 구조에서 "휘발성 단일 세션 + 진입/새대화 즉시 워밍" 구조로 단순화한 결정이다. 여러 대화 스레드를 만들어 목록에서 고르는 UI와 브라우저별 이력 저장을 걷어내고, 화면을 열 때마다(또는 "새 대화" 클릭 시) 새 세션을 발급하되 세션이 열려 있는 동안은 멀티턴 대화를 유지한다.

## 배경·문제 (WHY)

- 최초 문제 제기는 "브레인 대화가 브라우저 콘솔에 쌓여 다른 브라우저에서 열면 새로운 것이라 공유가 안 된다"였다. 원인은 대화 이력이 브라우저 `localStorage` 단일 키에만 저장되어 브라우저·기기별로 격리되기 때문이었다.
- 논의 과정에서 방향이 두 번 전환되었다. (1) 이력을 서버로 영속화하는 안을 검토했으나, 소유자는 오히려 매번 백지로 시작하는 쪽을 선호해 폐기했다. (2) one-shot 전환(세션 계층 완전 제거)을 검토했으나, "진입마다 빠르게 응답해야 한다"는 요구와 모순되어(One-shot은 매번 콜드 프라임이라 느림) 폐기했다. (3) 최종적으로 "휘발성 단일 세션 + 즉시 워밍"으로 확정했다 — 이력·멀티대화관리는 제거하되, 세션 계층(prime/resume/멀티턴)은 "빠름"의 근거이므로 유지한다.
- 핵심 통찰은 무거움의 실체를 두 축으로 분리한 것이다: (A) 멀티 대화 관리 + 이력 영속(제거 대상)과 (B) 세션 웜 유지 인프라(유지 대상 — 빠름의 근거)는 서로 독립적이며, (A)를 걷어낸다고 (B)까지 함께 버릴 필요는 없다.

## 결정 내용 (HOW)

- **단일 대화창**: 좌측 대화 이력 사이드바, 대화 목록·선택 UI, 다중 대화 배열 상태를 제거하고 화면은 단일 대화창 하나만 렌더한다(근거: `dashboard/frontend/src/pages/brain/BrainPage.tsx`).
- **이력 비영속**: `localStorage` 저장/로드를 제거한다. 새로고침·재오픈·타 브라우저 접속 시 대화는 항상 백지에서 시작한다 — 이는 결함이 아니라 의도된 동작으로 재정의되었다.
- **오픈마다 새 세션**: 화면이 마운트될 때마다 새 세션 ID를 발급하고 즉시 프라임을 트리거한다(`BrainPage.tsx:297` `useState<string>(() => makeSessionId())`, `BrainPage.tsx:123-124` `makeSessionId`).
- **세션 내 멀티턴 유지**: 한 세션(오픈~새대화/재오픈 전) 동안은 연속 질문이 이어진다. 동일 세션 ID로 연속 질의만 보내면 서버가 웜 재개(컨텍스트 이어받기)를 수행하므로, 프론트엔드 쪽에는 별도의 멀티턴 로직이 필요 없다.
- **"새 대화" 버튼**: 클릭 시 현재 대화 내역 초기화 + 새 세션 발급 + 즉시 재프라임을 수행한다(`BrainPage.tsx:506` `handleNewSession`) — 메뉴 재오픈과 동일한 동작으로 통일했다.
- **프라임 풀 여유**: 연속 새 대화를 눌러도 콜드로 떨어지지 않도록 웜 핸들 풀을 확장했다(상세: [[brain-prime-pool-need-based-refill]]). 다만 이 웜 효과는 프라임 풀 토글이 켜진(opt-in) 프로젝트에만 적용된다는 기존 범위(→ [[console-settings-incremental-scope-policy]])는 그대로 유지된다.
- **서버 쪽 세션 계층은 그대로 유지**: prime/resume/status폴링/잡폴링/멀티턴 인프라는 제거하지 않았다. 서버의 세션 계층은 원래부터 세션 ID별로 대화를 격리하는 구조였기 때문에, 프론트엔드의 멀티 대화 관리 UI를 걷어내도 서버 로직 변경은 최소(엔드포인트 5종 그대로 유지, 죽은 필드 정리 정도)로 끝났다 — "휘발성 단일 세션" 결정이 서버 계층에는 거의 영향을 주지 않은 이유다.

## 영향·관계

- FE 브레인 화면(`BrainPage.tsx`) 전면 리팩터 — 멀티대화 타입·헬퍼·좌측 aside 제거, `turns: BrainTurn[]` 단일 상태로 전환.
- [[console-brain-exit-guard-pattern]] — 세션이 화면 이탈과 함께 소멸하도록 바뀌면서, 진행 중 대화를 지키기 위한 이탈 경고 가드가 추가로 필요해졌다(이 결정의 직접적 후속 보강).
- [[brain-prime-pool-need-based-refill]] — 연속 새 대화 시 웜 배정을 보장하기 위한 풀 충전 로직 수정.
- [[cold-warm-session-separation]] / [[brain-prime-connection-pool-design]] — 이 결정이 그대로 유지하기로 한 기존 웜/콜드 세션 인프라.
- [[opal-console]] — 브레인 화면이 속한 상위 엔티티(OPAL Console).

## 근거 출처

task:063 TASK.md §배경·§확정된 설계 방향(대화에서 합의), DONE.md §작업 목표·요구사항 이행.
