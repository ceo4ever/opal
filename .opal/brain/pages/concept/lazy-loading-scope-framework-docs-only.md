---
type: concept
title: 절 단위 로딩 대상은 프레임워크 문서 4종만
tags:
- event-loader
- decision
sources:
- task:177
related: [section-lazy-loading-experiment-hold, worker-dispatch-target-section-selection]
created: '2026-10-02'
updated: '2026-10-02'
status: draft
---
## 개요

절 단위 로딩 실험의 대상은 프레임워크 규범 문서 4종(인용 규칙, 설계 게이트, PM 검토 게이트, PM 정의 문서)으로 한정했고 프로젝트 소유 문서는 제외했다.

## 결정 배경 (WHY)

프로젝트 문서와 프로젝트 안내 문서는 프로젝트마다 구조가 달라 절 분할 선언을 프레임워크가 일괄 소유할 수 없다 (근거: task:177 DONE 제외 범위). 다만 PM 활성화 본문의 67.6%가 이 프로젝트 문서에 해당해, 이번 실험은 가장 큰 덩어리를 건드리지 못했다는 점이 감소율이 낮은 또 다른 이유다.

## 결정 내용

- 대상: 프레임워크 문서 4종만. 절 선언은 프레임워크 `opal/core/references/sections/` 아래에 두고 각 절에 분류(항상 필수·조건부·요청 시)·의존·조건을 선언한다.
- 프로젝트 문서의 절 분할은 프로젝트가 소유하는 선언 구조가 있어야 가능하므로 범위 밖으로 남겼다.
- 켠 호출에서만 동작하며, 필요한 절은 별도 서브명령으로 가져온다.

## 영향 범위

절 선언 파일과 이벤트 매니페스트의 절 분할 선언. 프로젝트 문서의 로딩 방식은 변하지 않는다.

## 관련 페이지

- [[section-lazy-loading-experiment-hold]]
- [[worker-dispatch-target-section-selection]]
