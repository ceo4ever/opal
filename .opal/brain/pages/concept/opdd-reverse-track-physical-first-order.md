---
type: concept
title: 역공학 트랙 MODEL 순서는 물리가 먼저다
tags:
- architecture-decision
- data-design
- pipeline
- reverse-engineering
- task-104
sources:
- task:104
related:
- dict-선행-model-ssot
- opdd-pipeline-flow
- skill-opal-pilot-data-design
created: '2026-08-30'
updated: '2026-08-30'
status: draft
---
## 개요

역공학(reverse) 트랙에서 MODEL 단계의 모드 순서는 `logical → physical`이 아니라 `physical → logical`로 역전된다. 확정된 하위 산출물(물리)에서 상위 추상(논리)을 도출하는 것이 역공학의 정의이기 때문이다.

## 결정 배경 (WHY)

- (근거: task:104 PLAN §2.1) 역공학 트랙은 개념(concept) 모드를 건너뛴다. 이때 순서를 기존과 같이 `logical → physical`로 유지하면, 논리 모드의 입력 전제인 「개념 ERD 존재 또는 주입」이 첫 모드부터 충족되지 않아 시작 지점에서 블로커가 발생한다.
- (근거: task:104 PLAN §2.1) 설계 SSOT의 「모드 의존」 규정은 "기존 ERD가 인풋으로 주입되면 해당 모드부터 시작 가능"이다. 역공학 트랙에 주입되는 것은 물리(기존 DDL·ORM·DBML)이므로, 이 규정을 그대로 적용하면 시작점은 논리가 아니라 물리다.
- (근거: task:104 PLAN §2.1) 개념 없이 논리를 먼저 그리면 기존 DB와 괴리가 생겨 물리 단계에서 재작업이 발생한다. 확정된 물리에서 논리를 역산하면 이 괴리가 구조적으로 없다.

## 결정 내용

- 역공학 트랙의 MODEL 실행 순서를 `physical → logical`(2모드, 개념 제외)로 확정한다. 신규(greenfield) 트랙은 기존과 같이 `concept → logical → physical`(3모드) 순서를 그대로 유지한다.
- 이 역전은 「기존 ERD 주입 시 해당 모드부터 시작」이라는 기존 SSOT 규정의 직접 적용이며, 신규 규정을 필요로 하지 않는다.
- 부수 결정으로 `op-data-model`의 logical·physical 모드 「입력 전제」 문장에 역공학 트랙 예외 포인터를 추가한다 — 표만 고치고 본문을 맞추지 않으면 워커가 입력 전제 미충족으로 블로커를 올릴 수 있다.

## 영향 범위

- `opal/skills/opal-pilot-data-design/SKILL.md` §STEP 3: MODEL — 트랙별 실행 순서 분기
- `opal/skills/op-data-model/SKILL.md` §모드 선택 규칙, logical·physical 입력 전제
- `docs/proposals/opal-data-design.md` §3.2.1 — MODEL 모드 의존 규정

## 관련 페이지

- [[dict-선행-model-ssot]]
- [[opdd-pipeline-flow]]
- [[skill-opal-pilot-data-design]]
