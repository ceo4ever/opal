---
type: concept
title: 구형 호출 원장과 관측 구간 기반 호환 종료 판정
tags:
- event-loader
- dispatch
- compat
sources:
- task:175
- task:177
related: [worker-dispatch-contract-v2-binding, test-mode-bound-override-integrity-record]
created: '2026-10-02'
updated: '2026-10-02'
status: draft
---
## 개요

구형 디스패치 호출을 언제 거부로 전환할지는 누적 총량이 아니라 기준 시점 이후 관측 구간으로 판정한다. 로더가 구형 호출을 직접 원장에 남겨 이 판정의 증거를 만든다. 현재는 전환 기간이며 호환 종료는 켜지지 않았다.

## 결정 배경 (WHY)

호출 증거는 호출자가 보관하는 파일이라 집계할 수 없다. 그래서 로더가 구형 호출을 직접 기록해야 했고, 시험·설치 전 실행이 남긴 흔적이 판정을 오염시키지 않도록 기준 시점을 배포 시각으로 잡는다.

## 결정 내용

- 구형 호출마다 시각·작업 종류·이벤트·프로젝트 루트를 한 줄씩 원장에 추가한다. 쓰기 실패는 호출을 막지 않고 경고로 알린다. 시험이 시각·경로를 고정할 수 있도록 환경변수 재정의를 허용하는데, 이 재정의는 이후 시험 모드로 한정되고 사용·쓰기 실패가 별도 무결성 기록에 남는다. 상세는 [[test-mode-bound-override-integrity-record]]를 따른다.
- 구간 조회 서브명령이 건수·첫/마지막 시각·작업별 건수를 낸다(`opal/tools/event-loader/event_loader.py:927`).
- 종료 조건은 세 가지다: 소비자 문서에 구형 호출 0건(정적 검사), 직접·하위 검증 시나리오 통과, 기준 시점 이후 구형 호출 0건이 연속 168시간 이상 지속.
- 세 조건을 확인한 뒤 매니페스트의 구형 허용 값을 끄는 한 줄로 종료한다(`opal/core/references/events.json:446`).
- 기준 시점은 오염 방지 수정 후 최종 설치 시각이며, 그 이전 원장 줄(시험과 테스트 격리 도입 전 실행)은 판정에서 제외한다. 테스트는 원장을 임시 경로로 돌린다.

## 영향 범위

종료 판정은 후속 운영 조치다. 설치본이 다른 세션의 재설치로 덮이면 원장 구간이 끊길 수 있으므로 병합 후 재설치 시각을 새 기준으로 기록해야 한다.

## 관련 페이지

- [[worker-dispatch-contract-v2-binding]]
- [[test-mode-bound-override-integrity-record]]
