---
type: concept
title: AGENT.md 다이제스트 패턴 — 비서 코어 lean 분리
tags:
- bootstrap
- digest
- lean-core
- assistant-tier
- pm-tier
- architecture
sources:
- task:050
related:
- opal-bootstrap-2tier-model
- dedup-pointer-over-copy
- bootstrapper-marker-ssot-single-point
created: '2026-06-30'
updated: '2026-06-30'
status: active
---

## 개요

부트스트랩이 비서/PM 2-tier 구조로 전환된 이후(task:049), 매 세션 항상 로드되는 전역 AGENT.md는 "비서 코어만 담은 lean core"로 유지해야 한다. PM/프로젝트 전용 섹션은 Phase B에서 이미 로드되는 별도 reference로 이관하고, AGENT.md에는 비서가 알투로 행동하는 데 필요한 최소 집합만 남기는 것이 다이제스트 패턴의 핵심이다.

## 결정 배경 (WHY)

2-tier 부트스트랩 모델 도입 전에는 AGENT.md 단일 파일에 비서 행동 규칙과 PM 행동 규칙이 혼재했다. 2-tier 이후 PM 섹션은 Phase B에서 이미 `opal-pm.md`를 통해 로드되므로, AGENT.md에 PM 전용 섹션이 남아 있으면 비서 세션마다 불필요한 토큰을 소비하는 구조적 낭비가 발생한다 (task:050 DONE.md §핵심 설계 결정 #1, 근거: `opal/core/AGENT.md` 2-tier 구조 / task:049).

OPAL 헌법 Surgical 원칙 (`opal/core/PRINCIPLES.md` §3)상 이관 대상의 의미를 재작성하지 않고 "이동 + dedup + trim"만 수행하는 것이 강제된다 (task:050 PLAN §3.1.2).

## 결정 내용

비서 코어 잔류 필수 7항목은 다음과 같다: 정체성 적용, 보고 형식, 도구·MCP 인지 맵, `//` 진입 불변식(Phase A), 주도성, 핵심 역할(비서/PM 인식), 비서/PM 상태 정의 소형 표. 이 7항목은 비서가 단독으로 완결되게 행동하기 위한 최소 집합이다 (task:050 PLAN §3.1.2 비서 코어 완결성 점검).

PM 전용 섹션(역할 전환 상세, L2 경량 트랙, code-scan/opal-brain 활용 규칙, 메모리 브리핑, 모델매핑 적용, 프로젝트 컨텍스트)은 `opal-pm.md`로 이관한다. 이 파일은 Phase B에서 이미 로드되므로 PM 세션의 토큰은 중립이고, 비서 세션의 부담만 감소한다. 이관 결과 AGENT.md 소스 493줄에서 236줄로, 런타임 기준 약 455줄에서 약 223줄(약 51% 경감)로 축소되었다 (task:050 DONE.md §결과 요약).

부트스트래퍼 자동관리(4개 플랫폼 정책 + 수동 삽입 마커 블록)는 설치 시점 가이드로 매 세션 런타임 행동과 무관하므로 신규 reference `bootstrapper-management.md`로 이관한다. AGENT.md에는 포인터 1줄만 남긴다 (task:050 PLAN §F-003).

## 영향 범위

- `opal/core/AGENT.md` — 이관 섹션 10개 제거 + 교차참조 3건 갱신 + 비서 코어 7항목 완전 보존
- `opal/core/references/opal-pm.md` — §12~§17 신규 수신(역할전환 상세·L2·code-scan/brain 활용·메모리 브리핑·모델매핑 적용·프로젝트 컨텍스트)
- `opal/core/references/bootstrapper-management.md` — 신규 생성(부트스트래퍼 자동관리 이관)

## 관련 페이지

- [[opal-bootstrap-2tier-model]]
- [[dedup-pointer-over-copy]]
- [[bootstrapper-marker-ssot-single-point]]
