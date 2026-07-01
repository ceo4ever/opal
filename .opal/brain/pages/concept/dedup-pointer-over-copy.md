---
type: concept
title: dedup 원칙 — 목적지 기존 존재 시 표 복사 금지·포인터 단일화
tags:
- dedup
- ssot
- pointer
- architecture
- principles
sources:
- task:050
related:
- agent-md-digest-pattern
- opal-principles-constitution
- coding-principles-ssot
created: '2026-06-30'
updated: '2026-06-30'
status: active
---

## 개요

문서를 이동·병합할 때, 이동 대상 내용이 목적지 문서 혹은 다른 권위 문서에 이미 존재하는 경우 해당 내용을 다시 복사해 넣는 것을 금지한다. 대신 기존 문서로의 포인터(한 줄 참조)만 남겨 단일 SSOT를 유지한다. 이것이 OPAL dedup 원칙이다.

## 결정 배경 (WHY)

AGENT.md 다이제스트(task:050) 과정에서 PM 섹션을 `opal-pm.md`로 이관할 때 두 지점에서 dedup이 적용됐다.

첫째, AGENT.md의 "하네스 모드 체계(3-way)" 절은 `opal-harness.md §2 모듈 구조`에 이미 semi-agentic/interactive/agentic 3종 정의가 존재했다. `opal-pm.md`에 동일 표를 다시 복사하는 것은 OPAL 헌법 §2 "신규 추상화 금지" 원칙을 위반한다. 따라서 `opal-pm.md` 신규 절에 `opal-harness.md §2` 포인터 1줄만 삽입하고, 3-way 표 자체는 복사하지 않았다 (근거: task:050 PLAN §2.2.2 dedup 핵심 결론 #1).

둘째, "모델 매핑 우선순위" 절은 `opal-harness.md §6` 및 `opal-model-mapping.md §5`에 레벨·오버라이드 우선순위 정의가 이미 존재했다. `opal-pm.md`에 우선순위 표를 재서술하지 않고, "PM 진입 시 models 로드 적용" 같은 PM 행동 측면만 새로 서술하고 나머지는 포인터로 단일화했다 (근거: task:050 PLAN §2.2.2 dedup 핵심 결론 #2).

이 원칙은 OPAL 헌법의 "신규 추상화 금지"(`opal/core/PRINCIPLES.md` §2)와 직접 연결된다. 동일 내용이 두 곳에 존재하면 한 쪽이 갱신될 때 다른 쪽이 staleness 상태에 빠지고, 이를 추적하는 관리 비용이 발생한다 (WHY 미확보 — PRINCIPLES.md 취지에서 추론).

## 결정 내용

이관·병합 작업 시 다음 체크를 먼저 수행한다: "이동 대상 내용이 목적지 혹은 시스템 내 다른 권위 문서에 이미 존재하는가?" 존재할 경우 이동 대상을 원본에서 제거하고 목적지에는 권위 문서로의 포인터 1줄만 삽입한다. 존재하지 않을 경우에만 내용을 신규 수신한다.

포인터 형식은 해당 문서 헤딩 또는 섹션 번호를 명시하는 방식(`> 상세: document.md §섹션명`)을 사용하며, 이 포인터 자체가 이후 단계에서 dangling이 되지 않도록 교차참조 점검을 수행한다 (근거: task:050 PLAN §F-005).

## 영향 범위

이 원칙은 향후 모든 문서 이관·다이제스트 작업에 적용된다. 특히 brain ingest 단계에서도 "목적지 brain 페이지에 동일 내용이 존재하는 경우 멱등 skip"이라는 유사 원칙(`~/.opal/skills/op-brain-ingest/SKILL.md` §STEP 3 제외 기준)이 동일 사상의 연장이다.

## 관련 페이지

- [[agent-md-digest-pattern]]
- [[opal-principles-constitution]]
- [[coding-principles-ssot]]
