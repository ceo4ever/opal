---
type: concept
title: 이벤트 응답 본문 단일화
tags:
- event-loader
- bootstrap
- token-economy
sources:
- task:175
- task:177
related: [worker-dispatch-contract-v2-binding, worker-dispatch-target-section-selection, section-lazy-loading-experiment-hold]
created: '2026-10-02'
updated: '2026-10-02'
status: draft
---
## 개요

이벤트 문서 로딩은 같은 본문을 응답 안에 두 번 싣던 구조를 버리고, 본문은 한 곳에만 담고 나머지 목록은 신원 정보만 담는 단일 본문 구조(응답 형식 2판)로 바뀌었다. 문서 내용은 그대로이고 전송량만 줄었다.

## 결정 배경 (WHY)

부트스트랩과 PM 활성화는 필수 문서 전문을 매번 읽는데, 응답이 문서 목록과 본문 묶음에 같은 전문을 각각 실어 응답 바이트가 문서 본문 합계의 약 두 배였다. 저장소에서 목록 쪽 본문을 읽는 소비자는 로더 자신뿐이고 부트·단계 소비자는 본문 묶음만 읽으므로, 한쪽을 메타데이터로 줄여도 규칙 적용에는 영향이 없다고 판단했다.

## 결정 내용

- 모든 이벤트 load 응답은 최상위에 응답 형식 2판 표시를 갖고, 본문은 문서 묶음의 내용 필드에만 둔다(`opal/tools/event-loader/event_loader.py:542`).
- 필수·선택 문서 목록은 식별자·토큰·경로·해시·바이트 수만 담는다.
- 이벤트별 receipt의 스키마 버전은 디스패치 새 계약만 2로 올리고 나머지 이벤트는 1을 유지한다. 필수 문서 집합 자체는 이벤트 매니페스트가 계속 소유한다.
- 실측(설치본): 세션 어시스턴트 응답 26,912 → 14,730바이트, PM 활성화 응답 148,614 → 76,229바이트. 문서 본문 합계는 동일하다.

## 영향 범위

이벤트 로더 응답을 읽는 부트스트랩 5종과 단계 소비자는 문서 묶음의 내용 필드만 읽어야 한다. 측정은 전달 본문·원본 본문·응답 바이트를 따로 보고하며 재검증은 합산하지 않는다(`opal/tools/event-loader/event_loader.py:898`).

## 관련 페이지

- [[worker-dispatch-contract-v2-binding]]
- [[worker-dispatch-target-section-selection]]
- [[section-lazy-loading-experiment-hold]]

