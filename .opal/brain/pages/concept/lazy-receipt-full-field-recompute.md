---
type: concept
title: 지연 로딩 receipt는 선별 결과 전 필드를 재계산해 대조
tags:
- event-loader
- security
- verification
sources:
- task:177
related: [worker-dispatch-contract-v2-binding, section-lazy-loading-experiment-hold]
created: '2026-10-02'
updated: '2026-10-02'
status: draft
---
## 개요

지연 로딩 호출의 receipt는 선별 결과의 모든 필드를 검증 때 다시 계산해 대조해야 위조를 막는다. 일부 필드만 대조하면 나머지 필드를 바꿔 쓴 receipt가 통과한다.

## 결정 배경 (WHY)

최초 구현은 receipt의 단위 해시와 전달 목록을 현재 문서에서 재계산하지 않아, 위조한 receipt가 통과하는 것이 재현됐다. 보안 검사가 이를 중간 등급 지적(GC-001)으로 잡아 최종 판정 전에 고쳤다 (근거: task:177 DONE 검증절).

## 결정 내용

- 문서별 기록의 전 필드(단위 해시, 전달 목록, 생략 목록)를 현재 문서와 선언에서 다시 선별해 대조한다.
- 추가로 가져온 절의 본문도 현재 문서에서 재계산한 값과 비교하고, 이미 전달된 절 식별자의 재요청은 거부한다.
- 추가 절 receipt는 부모 receipt에 묶이며 부모 검증 인자로 확인한다.
- 일반 원칙: 결속 대상이 늘어나는 변경(선별·대상 한정)은 receipt가 담는 필드 수만큼 검증 필드도 늘어야 한다. 이는 [[worker-dispatch-contract-v2-binding]]의 선별 재수행 검증을 절 단위로 확장한 것이다.
- 알려진 평문 다운그레이드 성질(켠 receipt에서 모드 표시를 지우고 원본 해시를 복사)은 기존 평문 모드의 성질로 수용했다.

## 영향 범위

절 단위 로딩 검증 경로와 그 테스트. 켜지 않은 호출의 검증은 영향이 없다.

## 관련 페이지

- [[worker-dispatch-contract-v2-binding]]
- [[section-lazy-loading-experiment-hold]]
