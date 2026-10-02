---
type: concept
title: 원장 재정의의 시험 모드 한정과 별도 무결성 기록
tags:
- event-loader
- security
- compat
sources:
- task:177
related: [legacy-dispatch-compat-sunset-observation, worker-dispatch-contract-v2-binding]
created: '2026-10-02'
updated: '2026-10-02'
status: draft
---
## 개요

호환 종료 판정용 원장의 위치·시각 재정의를 시험 모드 전용으로 묶고, 재정의 사용과 쓰기 실패는 원장과 별개의 무결성 기록에 남겨 판정이 조용히 오염되지 않게 했다.

## 결정 배경 (WHY)

원장 경로와 현재 시각을 환경변수로 바꿀 수 있어, 누군가 원장을 비우거나 시각을 고정하면 호환 종료 판정이 과소 집계될 수 있었다. 이 한계는 [[legacy-dispatch-compat-sunset-observation]]에 알려진 한계로 적혀 있었고 보안 권고(GC-006)였다 (근거: task:177 DONE).

## 결정 내용

- 재정의는 시험 모드 표시가 있을 때만 적용한다. 그 밖의 호출은 재정의를 무시하고 응답 경고에 무시 사실을 남긴다.
- 원장 쓰기 실패와 재정의 사용은 원장 옆 무결성 기록에 남기고, 쓸 수 없으면 임시 폴더(소유자 전용 권한), 그것도 안 되면 표준 오류 순으로 내려간다. 호출은 막지 않는다.
- 구간 조회가 무결성 기록을 읽어 신뢰 가능 여부를 함께 보여준다. 원장 경로는 설치 루트 인자·환경변수로 옮겨지지 않는다.
- 일반 패턴: 시험을 위한 재정의 통로는 시험 모드로 한정하고, 한정이 깨졌을 때를 감지하는 기록을 판정 대상과 분리된 곳에 둔다.
- 남은 낮은 등급 한계: 시험 모드 재정의 사용이 기본 구간 조회에서 눈에 띄지 않음, 임시 폴백 파일 읽기 시 소유자·권한 미검사.

## 영향 범위

구형 호출 원장과 그 구간 조회 서브명령, 호환 종료 판정 절차.

## 관련 페이지

- [[legacy-dispatch-compat-sunset-observation]]
- [[worker-dispatch-contract-v2-binding]]
