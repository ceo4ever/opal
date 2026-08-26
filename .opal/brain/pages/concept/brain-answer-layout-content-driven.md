---
type: concept
title: 브레인 질의 답변 레이아웃 — content-driven 6단계 워크플로우
tags:
- brain
- query
- answer
- layout
- workflow
sources:
- task:062
related:
- skill-opal-brain
- opal-brain-system
- brain-query-latency-model
created: '2026-07-14'
updated: '2026-07-14'
status: active
---
## 개념 요약

`opal-brain` query 답변(대화형 `ask` · 비대화형 `--read-only` 공통)의 레이아웃을 질의 유형이라는 고정 택소노미가 아니라, 주입된 하위 문서의 실제 관계 구조에서 도출하는 content-driven 6단계 내부 워크플로우로 재설계했다.

## 배경·문제 (WHY)

- 기존 규칙은 리드 문단 → 단순/나열/그룹핑/비교 4갈래 표만 제공해 답변마다 구조를 즉흥적으로 선택했고, 동일 질의에도 레이아웃이 흔들렸다.
- 표면적인 주제명(예: "정책")으로 레이아웃을 단정하면 문서의 실제 관계를 놓친다는 판정 오류 사례가 계기가 되었다 — "방문형 캠페인 정책"을 표면상 표로 단정했으나 실제로는 참여 여정(라이프사이클)을 시간축으로 서술한 문서였다.
- 대안(전면 가중합 스코어링)은 self-scoring 편향 우려로 기각하고, 축→후보 1차 매핑 + 동점 시 단순한 쪽 tie-break로 채택했다.

## 결정 내용 (HOW)

- **6단계 내부 워크플로우**: 질의 분해 → 지식 수집 → 구조 분석 → 레이아웃 설계 → 내용 합성 → 자기검증. 앞 4단계는 비출력 내부 사고이고, 뒤 2단계만 답변으로 노출된다.
- **관측 축 6종 → 후보 레이아웃 5종 매핑**: 여정/순서성→Flow, 값 보유→표(GFM), 병렬성→그룹핑, 주제 수→복합, 분량→Flat.
- **불변 가드 3종**: G1(1~4단계 비출력), G2(claude subprocess 호출 1회 — 단계 증가가 호출 증가로 이어지지 않아 콜드 latency를 방어), G3(read-only는 JSON 코드펜스 하나만 출력, 펜스 밖 raw 마크다운 금지로 citations 유실을 방지).
- 표현 규율로 항목 내부 다문장은 하위 불릿으로 분해하고 1라인 1내용을 전 후보 공통 규칙으로 추가했다.
- SSOT는 §답변 구조 — 적응형 마크다운 계층 한 절이며(`opal/skills/opal-brain/SKILL.md:322`), 답변 생성을 위임받는 백엔드 어댑터는 답변 구조를 하드코딩하지 않는 얇은 프록시라 무변경이다(`dashboard/backend/adapters/opbr_adapter.py:133`).

## 영향·관계

- §답변 구조 절(`opal/skills/opal-brain/SKILL.md:322`), §변경이력 v1.8 행(`opal/skills/opal-brain/SKILL.md:559`).
- read-only 경로(`opbr_adapter.py:133`)는 이 절 변경만으로 자동 전파된다(코드 변경 불필요) — read-only 출력 계약과의 관계는 `SKILL.md:469`가 역참조한다.
- 레이아웃 품질 자체는 advisory LLM 행동이라 brain-tool이 강제하지 못하며, 검증은 문서 구조 검사(L1)와 read-only 계약 비파손 스모크(L2)에 한정된다.

## 근거 출처

- `task:062`
- `opal/skills/opal-brain/SKILL.md:322` (§답변 구조), `:469` (read-only 역참조), `:559` (§변경이력 v1.8)
- `dashboard/backend/adapters/opbr_adapter.py:133` (read-only 프롬프트 구성 — 어댑터 무변경 확인 대상)

## 관련 페이지

- [[skill-opal-brain]]
- [[opal-brain-system]]
- [[brain-query-latency-model]]
