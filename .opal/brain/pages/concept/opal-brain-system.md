---
type: concept
title: OPAL Project Brain 시스템
tags: [knowledge, architecture, wiki]
sources: [task:015, design:docs/proposals/opal-brain-design.md, ref:llm-wiki]
related: [brain-tool, state-tool]
created: 2026-06-10
updated: 2026-06-10
status: active
---

# OPAL Project Brain 시스템

## 개요

Karpathy의 llm-wiki 사상("영속·복리 지식 아티팩트")을 OPAL 네이티브로 융합한 프로젝트 지식 위키. 프로젝트의 WHY·HOW를 마크다운 페이지로 누적하고, PM·워커가 작업 시 참조하며, CLOSE 시 자동 누적된다.

## 설계 배경 (WHY)

- **빠진 조각**: OPAL은 Schema(docs/), Log(MEMORY.md), Index(code-scan.json/@header)는 보유했으나 "왜·어떻게 그렇게 되었나"를 담는 **누적 지식 페이지**가 없었다. brain이 이 30% 공백을 채운다.
- **RAG가 아님**: 매 질의 재검색·재합성 대신, 교차참조·결정 맥락이 페이지에 영속 누적되는 복리 아티팩트.
- **마크다운 네이티브**: 사람·LLM·git 모두 접근 가능. understand-anything 그래프는 선택적 보강(의존 아님).

## 경계 정의

- **code-scan** = "무엇이 있나"(WHAT, @header 구조) — brain entity가 @header를 단방향 시드로 흡수.
- **MEMORY.md** = "PM이 어떻게 일하나"(운영 기억·피드백).
- **brain** = "이 프로젝트가 왜·어떻게 그렇게 되었나"(도메인 지식).

## 구성

- 도구 [[brain-tool]] — 8 서브명령, 결정론적 집행 ([[state-tool]] 패턴 복제)
- 스킬 opal-brain(opbr) — 단일 pilot + 4모드(init/ingest/query/lint)
- 워커 op-brain-ingest — CLOSE 자동 누적 훅
- PM 융합 — 부트스트랩 Lazy 로드 + dispatch 사전 참조(code-scan PM 우선 패턴 동형)

## 핵심 결정 (task 015)

- 저장=마크다운 네이티브 / 스킬=단일 pilot 4모드 / @header 단방향 시드 / init=핵심 시드+점진 누적(전체 미러 아님) / CLOSE ingest=opp 단독 파일럿(나머지 7 pilot 후속) / 외부 소스만 sources/ 원본 저장.

## 관련 페이지

- [[brain-tool]] · [[state-tool]]
