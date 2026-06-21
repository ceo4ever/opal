---
type: concept
title: ANALYSIS 라이브러리 버전 환각 → PM npm view 실측 차단 패턴
tags:
- analysis
- hallucination
- pm-gate
- version
- npm
- lesson-learned
sources:
- task:033
related:
- analysis-drift-pm-cross-verify-lesson
- verification-command-4-standard
created: '2026-06-21'
updated: '2026-06-21'
status: active
---

## 개요

ANALYSIS 워커(특히 light 모델)가 라이브러리 버전을 훈련 데이터 기반 구버전으로 단정하는 환각 패턴. PM이 `npm view <pkg> version` 실측 교차검증으로 차단한 사례. 기존 [[analysis-drift-pm-cross-verify-lesson]] 패턴의 "버전 환각" 재현 사례다.

## 배경·문제 (WHY)

태스크 033 vitest 셋업 중 ANALYSIS 워커가 구버전(vitest^2.1/RTL^15/happy-dom^12)을 npm 공식 버전으로 단정하고 "공식 입증"이라는 표현과 함께 PLAN에 반영했다. 실제 최신 버전은 vitest^4.1.9 / @testing-library/react^16.3.2 / happy-dom^20.10.6 / @testing-library/jest-dom^6.6.3으로, 주 버전 기준 2~8배 구버전이었다.

## 결정 내용 (HOW)

### 패턴: 라이브러리 버전 PM 실측 교차검증

적용 시점: ANALYSIS가 특정 라이브러리 버전을 제시하고 "공식"·"최신"·"안정"이라 단정할 때.

검증 방법: PM이 `npm view <패키지명> version` 또는 `npm view <패키지명> dist-tags`로 npm 레지스트리 실측값을 확인한 뒤 PLAN에 버전 고정값을 재주입한다. ANALYSIS 단독 값을 그대로 PLAN에 승계하지 않는다.

강화검토 필요 신호:
- "최신 안정 버전은 X.Y.Z다"처럼 구체 버전을 확신 어조로 제시
- 훈련 데이터 기준일(2024년 중반 이전) 이후 메이저 업데이트가 활발한 패키지(vitest, @testing-library, happy-dom 등)
- peer dependency 충족 여부를 ANALYSIS가 단독 판단할 때

왜 ANALYSIS 단독 신뢰가 위험한가: 훈련 데이터 기준 버전과 실제 최신 버전 간 메이저 버전 격차가 크면 peer dependency 불만족·API 변경으로 설치/실행 실패가 발생한다. "공식 입증"이라는 표현이 PM의 경계를 낮추는 것이 핵심 위험이다.

### 재현 관계

이 패턴은 [[analysis-drift-pm-cross-verify-lesson]]에 기록된 "드리프트 분석 환각 → PM 실측 교차검증" 패턴의 버전 환각 변형이다. 소스/배포본 드리프트 방향성 오류(task:031/032)와 라이브러리 버전 오추론(task:033)은 동일한 원인(훈련 데이터 기반 단정)에서 비롯된다. PM의 대응 원칙도 동일하다 — 워커 주장을 수용하기 전 PM이 직접 실측 도구로 교차검증한다.

## 영향·관계

oppd ANALYSIS 단계 후 PM 검수 체크리스트에 "패키지 버전 실측 확인(`npm view`)" 항목 추가 권고.

## 관련 페이지

- [[analysis-drift-pm-cross-verify-lesson]]
- [[verification-command-4-standard]]
