---
type: concept
title: OPAL 프로젝트 정의
tags:
- project
- overview
- principle
- component
sources:
- doc:docs/PROJECT.md
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

OPAL(Open Protocol for Agentic Loops)의 프로젝트 정의 SSOT — 개요·원칙·구조·주요 컴포넌트·문서 허브를 한 문서에서 관리한다.

## 핵심 결정

- **5대 원칙**: 표준화>커스터마이징, 재사용성>편의성, 플랫폼 독립성, 컴포지션>모놀리식, 하네스가 품질 보장.
- **주요 파이프라인**: SDD(opsdd), GC(opgc), Project Brain(opbr) 3개 파이프라인이 PROJECT.md §3~5에 등록되어 있다.
- **문서 허브**: 이 문서를 진입점으로 ARCHITECTURE.md·CONVENTIONS.md·SECURITY.md 등 역할별 문서가 링크된다.

## 적용 범위

프레임워크 전체; opgc SCAN/디스패치·PM 컨텍스트 주입 시 영역 매칭과 전문 에이전트 선정의 기준이 된다.

## 관련

- [[opal-architecture]] — 이 문서에서 링크되는 프레임워크 컴포넌트 아키텍처 상세
- [[opal-conventions]] — 이 문서에서 링크되는 코딩·구조 컨벤션 기준
- [[opal-security-model]] — 이 문서에서 링크되는 보안 baseline 문서

## 참조

`file_path: docs/PROJECT.md`
