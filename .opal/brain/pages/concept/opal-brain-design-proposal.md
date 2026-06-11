---
type: concept
title: OPAL Project Brain 설계 제안서
tags:
- brain
- design
- llm-wiki
- ingest
- index
sources:
- doc:docs/proposals/opal-brain-design.md
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

Karpathy llm-wiki 사상을 OPAL 네이티브로 융합한 Project Brain 설계 SSOT — 목적·디렉토리 구조·컴포넌트 설계·하네스 융합·구현 의사결정(M-1~M-5)을 명문화한다 (015 코어 + 016 지능화 구현 완료 기준).

## 핵심 결정

- **3계층 기억 모델(M-3 B안)**: 단기(`MEMORY.md`) / 장기 검색(`.opal/brain/`) / 장기 원본(`tasks/NNN/`)으로 분리.
- **index 비상주(016 W5 정정)**: 부트스트랩 시 index.md 전체 자동 로드 금지 — brain 존재 여부만 경량 인지, 지식은 `brain-tool search` 후보→선택 주입으로만 접근.
- **ingest 소스별 깊이(M-2 B안)**: 내부 문서는 3~6줄 요약+포인터(concept), 코드 @header는 entity 시드(본문 복제 금지).
- **이름 결정(M-4 A안)**: 구현 식별자는 `opal-brain/opbr/brain-tool/.opal/brain/`; "opal-wiki-pilot"은 비전 용어로 이 문서에만 병기.

## 적용 범위

`opal-brain` 스킬·`brain-tool` 도구·`op-brain-ingest` 워커·`.opal/brain/` 디렉토리 구조.

## 관련

- [[opal-brain-system]] — 이 설계 제안서가 정의하는 brain 도구 시스템의 아키텍처 구현체
- [[skill-opal-brain]] — 이 설계 원칙을 따르는 brain 스킬의 개념 문서
- [[op-brain-ingest]] — M-2 B안 ingest 깊이 결정을 구현하는 워커 스텝

## 참조

`file_path: docs/proposals/opal-brain-design.md`
