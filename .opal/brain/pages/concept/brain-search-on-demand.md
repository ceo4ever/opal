---
type: concept
title: brain search 선택 주입 — on-demand 비상주 정책
tags:
- architecture
- brain
- search
- context
- pm
sources:
- task:016
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: active
---
## 개념 요약

brain index를 세션 컨텍스트에 자동 로드하지 않고, search가 후보 목록(본문 X)만 반환하며 선택된 페이지만 주입하는 on-demand 정책. 015의 부트스트랩 index 자동 로드를 폐지하고 컨텍스트 부담을 회피한다.

## 배경·문제 (WHY)

015 AGENT.md Lazy 트리거가 `.opal/brain/index.md`를 PM 컨텍스트 로드 시 자동 로드했다. brain이 50+ 페이지로 성장하면 index 전체가 매 세션 컨텍스트에 상주해 토큰 낭비가 발생한다. "RAG식 전량 로드 금지"는 캡틴이 명시한 우려였다.

## 결정 내용 (HOW)

- **index 비상주**: 부트스트랩은 `.opal/brain/` 존재 여부만 경량 인지. index.md 전체 자동 로드 없음.
- **search 후보 목록 반환**: `brain-tool search <키워드>`는 `page·title·score·snippet`(본문 X) 후보 목록만 반환.
- **선택 주입 흐름**: 후보 제시 → 선택 → 선택된 페이지만 Read하여 컨텍스트 주입. 전량 로드 금지.
- **선택 주체**: `//opbr ask`(사용자 질의)=사용자 선택 / PM 자동(작업·디스패치 전)=PM이 score 상위 선별, 불확실 시 사용자 확인.
- **3시점 on-demand**: 작업·분석·설계 전 / 워커 디스패치 시 / 사용자 질의.
- **3 PM 문서 일관**: AGENT.md·dispatch-process.md·opal-brain SKILL.md 동시 정정으로 "인덱스 자동 로드" 잔재 제거.

## 영향·관계

- `opal/core/AGENT.md` — Lazy 트리거 행을 "존재 여부 경량 인지" 정정 (v3.2)
- `opal/core/references/pm/dispatch-process.md` — Step 1.5 search 3시점 + 선택적 주입 흐름 (v1.3)
- `opal/skills/opal-brain/SKILL.md` — query 모드 "후보→선택→주입" 정정 (v1.2)

## 근거 출처

`task:016` TASK §확정 §8, PLAN §2 U-6/U-7 — `opal/core/AGENT.md:40`(Lazy 트리거 정정), `opal/core/references/pm/dispatch-process.md:111-119`(Step 1.5).

## 관련

- [[opal-brain-system]] — search 선택 주입이 적용되는 brain 시스템
- [[skill-opal-brain]] — 후보→선택→주입 절차가 명문화된 query 모드 스킬
