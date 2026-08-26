---
type: concept
title: 기획 산출물 비즈니스 용어 우선 원칙
tags: [citation-rules, opal-writing, opwt, brain-ingest, document-standard]
sources: [task:024]
related:
- opwt-v4-output-system
- skill-opal-pilot-write-tech
- op-brain-ingest
- opal-principles-constitution
- brain-business-term-layer
created: 2026-06-16
updated: 2026-06-16
status: active
---

## 개요

정책서·PRD·TRD·IA·외부 API 명세서·brain 페이지 등 기획/지식 산출물의 본문은 비즈니스 용어/자연어로 서술해야 한다. 코드 변수·enum·식별자를 본문 서술의 주어로 나열하는 것은 금지이며, 코드 식별자는 괄호+근거 인용(`경로:줄번호`)으로만 병기한다.

핵심 명제: **"코드는 SSOT 근거이지 본문 서술의 주어가 아니다."**

## 결정 배경 (WHY)

opwt(opal-pilot-write-tech)로 소스 코드를 역설계하여 정책서를 생성할 때, 워커가 코드 변수·enum(`autoSelCancelYn`, `AUTO_SELECT_CANCELABLE` 등)을 본문에 그대로 나열하는 문제가 반복 관찰되었다. 기획 산출물은 비개발 독자(PO, 기획자, 법무 등)가 읽는 문서이므로, 코드 식별자를 주어로 쓰면 가독성·비즈니스 적합성이 저하된다.

## 결정 내용

SSOT 위치를 `opal/core/references/harness/citation-rules.md` §8 "비즈니스 용어 우선 원칙(기획 산출물)"로 확정하고, 4개 적용 지점에 §8 참조 포인터를 주입했다. 원칙 본문은 §8 한 곳에만 존재하며, 나머지 지점은 재서술 없이 참조만 한다(헌법 거버넌스).

### 주요 규칙 (§8 요약)

- **코드 식별자 본문 나열 금지**: 변수·enum·컬럼·함수명을 본문 문장의 주어/서술 대상으로 쓰지 않는다.
- **비즈니스 용어 우선**: 의미를 자연어로 서술하고, 코드 식별자는 괄호+근거 인용(`경로:줄번호`, §2.2)으로만 병기한다.
- **조건·상태군 풀어쓰기**: enum/플래그 비교식은 의미를 풀어 쓴다.

### 적용 대상

기획/지식 산출물(비개발 트랙) — 정책서, PRD, TRD, IA, 외부 API 명세서, 기능 시나리오/화면 흐름도, brain concept/entity 페이지.

> 개발 트랙 산출물(ANALYSIS/PLAN/EXECUTE 등)은 코드 토큰을 직접 인용하는 것이 정상이므로 강제 대상이 아니다.

## 영향 범위

| 지점 | 파일 | 변경 내용 |
|------|------|----------|
| SSOT 본문 | `opal/core/references/harness/citation-rules.md` §8 | 원칙 본문 신설 (8.1~8.5 + 자연어 변환 예시 + 조건·코드 근거 분리 표) |
| opwt 작성 워커 | `opal/skills/opal-pilot-write-tech/references/network-guide.md` §7-0 | §8 참조 공통 작성 원칙 블록 추가 |
| opwt QA 워커 | `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` §3.1 | 비즈니스 용어 우선 검증 절 + §6 절차 연결 |
| brain ingest 워커 | `opal/skills/op-brain-ingest/SKILL.md` STEP 4 | 비즈니스 용어 우선 불릿 추가 |
| 공통 문서 표준 | `opal/core/references/opal-doc-standard.md` §3 정책서 행 | §8 포인터 추가 |
| 확정 기준 영구 기록 | `.opal/AGENT.md` 확정 기준 표 #2 | 캡틴 문안 원문 등록 |

## 관련 페이지

- [[opwt-v4-output-system]]
- [[skill-opal-pilot-write-tech]]
- [[op-brain-ingest]]
- [[opal-principles-constitution]]
- [[brain-business-term-layer]]

