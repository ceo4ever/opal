---
type: flow
title: AS-IS 분석 5단계 워크플로우 (PM 대화)
tags:
- pm
- asis-analysis
- workflow
- task-084
sources:
- task:084
related:
- asis-workflow-order-over-new-skill
- pm-conversation-readonly-collection-exception
- degraded-execution-with-explicit-gap
- inherit-new-boundary-fixed-before-writing
- code-scan-mandatory-policy
- brain-answer-layout-content-driven
created: '2026-08-06'
updated: '2026-08-06'
status: draft
---
## 개요

기획·개선 대화에서 소유자가 현행(AS-IS)을 물었을 때 PM이 따르는 5단계 행동 순서다. 좌표를 먼저 고정하고, 이미 가진 지식을 확인한 뒤, 정책·화면·데이터·코드 4축을 좁혀 수집하고, 축 간 대조로 정합을 판정하고, 축 매트릭스와 갭 목록을 붙여 보고한다. 규칙 본문은 대부분 기존 문서에서 상속하고 이 흐름이 소유하는 것은 **순서**다 (`opal/core/references/pm/asis-analysis.md`).

## 흐름 단계

### 진입 판정 — 규모 분기

질의가 지목하는 축이 1개이고 기존 지식만으로 근거가 충족되면 **축약**(0 → 1 → 4), 축이 2개 이상이거나 원천 확인이 필요하면 **전개**(0 → 1 → 2 → 3 → 4)로 간다. 축약이어도 축 매트릭스는 생성하며, 수집하지 않은 축은 미보유 기호로 남기고 사유를 갭 목록에 적는다 (`opal/core/references/pm/asis-analysis.md:45-53`).

### 0단계 — 좌표 고정

무엇을 AS-IS로 볼지(대상 업무 단위·시간 경계·제외 범위)를 1~3줄로 확정하고, 4축 각각의 SSOT 문서를 프로젝트가 선언한 것에서 지목한다. 프레임워크는 특정 문서명을 규정하지 않는다.

여기에 **헤더 블록 우선 읽기** 규율이 붙는다 — 지목한 문서는 본문을 통독하기 전에 상단 헤더 블록을 먼저 읽어 SSOT인지 파생본인지 판별하고, 파생본이면 헤더가 가리키는 원천으로 좌표를 옮긴 뒤 수집한다. 헤더만으로 판별이 불가능하면 추정하지 않고 미판별로 표기해 폴백으로 넘긴다 (`opal/core/references/pm/asis-analysis.md:56-71`).

### 1단계 — 기존 지식 확인

질의 키워드로 brain을 조회하고, 동일 질의에 대한 **재사용·갱신·신규 판정 결과만 소비**한다. 판정 규칙 자체는 브레인 질의 절차가 소유하므로 이 단계에서 재기술하지 않는다. 재사용이면 기존 페이지를 답변 골격으로 삼고 수집 범위를 근거 재확인으로 줄이며, 갱신이면 그 페이지를 4단계 거처 선판정에 넘긴다.

### 2단계 — 4축 수집

정책·화면·데이터·코드 네 축을 각각 "지목 → 좁히기 → 구간 Read" 순으로 수집한다. 정책·데이터는 업무 용어·엔티티명 grep으로 해당 조항·정의 구간만, 화면은 업무 표면 식별자로 화면 정의 블록만, 코드는 code-scan으로 도메인·레이어를 좁힌 뒤 해당 파일만 읽는다 (→ [[code-scan-mandatory-policy]]).

[MUST] 어느 축에서도 문서·코드 전문을 컨텍스트에 올리지 않는다. 0단계에서 확정한 4축을 넘어 임의로 축을 확장하지도 않는다.

여기에 **인용 시점 stale 재확인** 규율이 붙는다 — 1단계에서 확보한 지식을 근거로 인용하는 그 시점에 원문을 다시 확인한다. brain은 ingest 시점 스냅샷이고 코드가 SSOT이므로, 원문과 다르면 원문을 채택하고 차이를 갭 목록에 남긴다 (`opal/core/references/pm/asis-analysis.md:110-115`).

규모가 커서 단일 컨텍스트로 통독이 불가하면 이 단계에 한해 축 단위 읽기 전용 워커 팬아웃이 허용된다 (→ [[pm-conversation-readonly-collection-exception]]).

### 3단계 — 정합 판정

축 간 대조 후 3분류로 판정한다. 판정 기준 자체는 문서/코드 불일치 규칙이 전량 소유하므로 이 단계는 "축 간 대조 후 그 기준을 적용한다"는 연결만 기술한다. 판정과 합성은 워커에 위임하지 않고 PM이 직접 수행한다 (`opal/core/references/pm/asis-analysis.md:134-153`).

### 4단계 — 보고·환류

보고 레이아웃은 브레인 답변 레이아웃 판정 규칙에 위임하고(→ [[brain-answer-layout-content-driven]]), 이 흐름이 새로 얹는 것은 **축 매트릭스**와 **갭 목록** 두 블록뿐이다.

여기에 **산출물 거처 선판정** 규율이 붙는다 — 보고를 산출하기 **전에** 결과물이 어디에 살지 판정한다. 기존 페이지·문서가 이미 같은 내용을 담고 있으면 신규 생성이 아니라 갱신을 택한다(이중 SSOT 금지). 갱신 대상과 brain ingest 후보는 보고 말미에 다음 행동으로 제시한다 (`opal/core/references/pm/asis-analysis.md:178-193`).

## 자산 부재 시의 동작

폴백 5종(brain 부재 · 업무 용어 타입 미채택 · code-scan 미보급 · 축 SSOT 부재 · 기획 산출물 전부 부재) 어느 것도 동작이 "중단"이 아니다 — 축소 실행하되 결측을 반드시 명시한다 (→ [[degraded-execution-with-explicit-gap]]).

## 진입 경로

PM 프로세스 문서에 5단계 stub 절이 있고(`opal/core/references/opal-pm.md:353-359`), 프레임워크 AGENT.md의 Lazy 트리거 테이블에 "기획·개선 대화에서 AS-IS·현황 분석 요청 수신" 조건으로 등록되어 상세 문서가 필요 시점에 로드된다.

## 관련 페이지

- [[asis-workflow-order-over-new-skill]]
- [[pm-conversation-readonly-collection-exception]]
- [[degraded-execution-with-explicit-gap]]
- [[inherit-new-boundary-fixed-before-writing]]
- [[code-scan-mandatory-policy]]
- [[brain-answer-layout-content-driven]]
