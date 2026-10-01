---
type: concept
title: 태스크 실행 로그 PRD — 무엇을 왜 만드는가
tags:
- run-log
- prd
- docs
sources:
- doc:docs/run-log/PRD.md
related: [run-log-trd, run-log-contract, state-tool, state-md-journal-redefinition]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

태스크 실행 이력을 하나의 순서 있는 표준 사건 기록으로 모으는 "태스크 실행 로그 표준화"의 제품 요구 문서다. 무엇을 왜 만드는가만 소유하고, 스키마·명령은 계약 문서, 구현 방식은 기술 문서가 소유한다(`docs/run-log/PRD.md:4-8`).

## 핵심 결정

- 문제는 정보 부재가 아니라 복원 불가다. 상태 파일은 행마다 시각을 하나만 두고 덮어쓰므로 전이 과정과 워커의 중간 판단·검증·재시도를 되살릴 수 없다(`docs/run-log/PRD.md:20-22`).
- 그 결과 워커 완료가 선언만으로 통과하고, 실제 소요 시간을 사후에 만들 수 없으며, 지울 수 있는 실행 일지 때문에 이력 존재 자체가 보장되지 않는다(`docs/run-log/PRD.md:25-31`).
- 목표는 이력 원천 단일화, 파일 삭제로 우회되지 않는 계약, 기계가 관측한 증거로만 완료 인정, 시간의 결정론적 복원, 장애에도 멈추지 않고 잃지 않음, 표준 파이프라인 전역 선언, 증거의 안전한 보존 7가지다(`docs/run-log/PRD.md:45-58`).

## 관련 페이지

- [[run-log-trd]] · [[run-log-contract]]
- [[state-tool]] — 현재 상태 원천
- [[state-md-journal-redefinition]] — 사람용 저널의 역할 축소
