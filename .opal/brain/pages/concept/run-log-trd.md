---
type: concept
title: 태스크 실행 로그 TRD — 기술 결정과 책임 경계
tags:
- run-log
- trd
- docs
sources:
- doc:docs/run-log/TRD.md
related: [run-log-prd, run-log-contract, state-tool, opal-adapter-platform-isolation]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

태스크 실행 로그를 어떻게 만들 것인가를 소유하는 기술 결정 문서다. 결정 D-1~D-9와 구성요소별 소유·금지 경계를 정한다(`docs/run-log/TRD.md:4-8`, `:12-24`).

## 핵심 결정

- 실행 이력은 태스크 폴더 안 append 전용 줄 단위 기록 조각에 두고, 상태 변경과 사건 기록의 원자성은 상태 원천 안의 미전송 사건 보관함으로 푼다(`docs/run-log/TRD.md:16-17`).
- 런타임 색인은 증거 원천이 아닌 파생 인덱스로, 기록 조각에서 전량 재구축할 수 있어야 한다. 태스크마다 배타 락은 하나만 둔다(`docs/run-log/TRD.md:18-19`).
- 의존 방향은 상태 도구 → 기록 코어 단방향이다. 기록 코어는 상태 파일을 읽지 않고 계약 활성·현재 실행·완료 게이트를 판정하지 않으며, 그 조합 판정은 상태 도구가 소유한다(`docs/run-log/TRD.md:20`, `:33`, `:45-47`).
- 플랫폼·채널 차이는 변환 계층에만 두고, 변환기는 자기 채널의 완료 등급을 스스로 선언하지 않는다. 마스킹은 모든 기록 경로가 통과하는 공통 지점 한 곳에 둔다(`docs/run-log/TRD.md:21`, `:24`, `:52`).
- 로그 계약 활성화 여부는 별도 스위치 파일이 아니라 상태 원천의 필수 블록이 소유한다 — 파일 삭제가 계약 해제와 구별되지 않게 되는 것을 막기 위해서다(`docs/run-log/TRD.md:22`).

## 관련 페이지

- [[run-log-prd]] · [[run-log-contract]]
- [[state-tool]]
- [[opal-adapter-platform-isolation]] — 플랫폼 분기 격리 원칙
