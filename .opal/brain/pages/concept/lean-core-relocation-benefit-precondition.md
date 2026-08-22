---
type: concept
title: lean core 이관 이익의 전제 조건 — PM 전용 + Phase B 기 로드
tags:
- lean-core
- agent-md
- relocation
- pm-tier
- assistant-tier
sources:
- task:099
- task:050
related:
- agent-md-digest-pattern
- template-precedence-over-prose-norms
created: '2026-08-22'
updated: '2026-08-22'
status: draft
---
## 개요

섹션을 AGENT.md 밖으로 이관해 lean core 이익을 얻으려면, 그 섹션이 "PM 전용이고 Phase B에서 이미 로드된다"는 조건을 충족해야 한다. 이 조건이 성립하지 않는 섹션(전 tier 공통 규범 등)을 이관하면 토큰 이익이 발생하지 않거나 오히려 늘어난다(근거: task:099 DONE.md §4 D-1, PLAN.md §3.0 쟁점 A).

## 결정 배경 (WHY)

- (근거: task:050, `.opal/brain/pages/concept/agent-md-digest-pattern.md` §결정 내용) 050의 AGENT.md 493→236줄 경감은 "PM 전용 섹션을 Phase B에서 이미 로드되는 opal-pm.md로 이관"함으로써 얻어졌다. 이관 대상 섹션은 애초에 비서 세션에서만 불필요했을 뿐, PM 세션에서는 어차피 로드되고 있었다.
- (근거: task:099 PLAN.md §3.0 쟁점 A) 099는 같은 조건을 보고 형식 섹션에 적용해봤다. 보고 형식은 비서·PM(태스크)·PM(대화) 전 tier 공통 규범이라, 별도 reference로 분리해도 그 reference가 "이미 로드되는 tier"가 존재하지 않는다. Eager 포인터로 재등록하면 원본 인라인 대비 포인터 hop 비용만큼 총 토큰이 오히려 늘고, Lazy 테이블에 등록하면 AGENT.md의 `[LAZY 금지 원칙]`("미리 읽어두면 도움이 될 것 같다는 판단으로 선행 로드하는 것은 금지")과 충돌해 규범 도달에 실패한다.
- (근거: task:099 PLAN.md §3.0 쟁점 A 3안 비교표) 전부 인라인 / 분리+포인터 / 절충 3안을 비교한 결과, "전 tier 공통 규범을 분리하는 것"은 어느 축에서도 이익이 없었다 — 이것이 099가 신규 분리를 채택하지 않은 근거다.

## 결정 내용

- 신규 이관을 검토할 때는 먼저 "이 섹션을 소비하는 tier가 무엇이고, 그 tier가 이관 목적지 파일을 이미 다른 이유로 로드하고 있는가"를 판별한다.
- 판별 결과가 "예"(PM 전용 + Phase B 기 로드)이면 이관이 순이익이다(050 사례).
- 판별 결과가 "아니오"(전 tier 공통이거나 목적지가 별도 Read를 요구)이면 이관은 순이익이 아니며, 오히려 총 토큰 증가 또는 Lazy 경로를 통한 규범 도달 실패로 귀결된다(099 사례). 이 경우 인라인을 유지하고, 무한 증식은 절대 줄 수 상한이 아니라 증식 경계 규정·정기 감사 같은 별도 장치로 방어한다.

## 영향 범위

AGENT.md·opal-pm.md 등 tier별 부트스트랩 파일 사이에서 섹션 이관을 검토하는 모든 후속 설계에 적용된다. "lean core를 위해 분리한다"는 직관만으로 이관을 결정하면 099와 같은 오판(순이익 0 또는 음수인 이관)이 재발할 수 있다. 050의 결정 자체는 유효하지만, 그 이익이 성립하는 조건은 보편적이지 않다 — 이 페이지는 050 결정의 적용 한계를 실증한 사례다.

## 관련 페이지

- [[agent-md-digest-pattern]]
- [[template-precedence-over-prose-norms]]
