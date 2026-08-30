---
type: concept
title: DICT가 MODEL을 선행한다 — 사전이 속성명·타입 SSOT
tags:
- architecture-decision
- data-design
- ssot
- pipeline
sources:
- task:019
- task:104
related:
- opdd-pipeline-flow
- op-data-dictionary-skill
- op-data-model-skill
- opdd-reverse-track-physical-first-order
created: 2026-06-12
updated: '2026-08-30'
status: active
---
## 개요

opdd 파이프라인에서 DICT(표준사전) 단계가 MODEL(데이터 모델링) 단계를 반드시 선행한다. 표준사전이 논리/물리 모델링의 속성명·타입을 결정하는 SSOT이기 때문이다. 이 선행 관계는 역공학(reverse) 트랙에서도 문구 변경 없이 그대로 성립한다 — DICT의 역할만 전환될 뿐이다.

## 결정 배경 (WHY)

- 논리 모델의 속성명은 DICT `표준단어사전.md`의 수식어/분류어 약어 조합 규칙을 따른다.
- 물리 모델의 컬럼 타입은 DICT `도메인사전.md`(D001~D022)의 DBMS별 매핑을 따른다.
- DICT 없이 MODEL을 수행하면 속성명·타입 SSOT가 공백 상태가 되어 하류 DDL까지 오염된다.
- (근거: task:104 PLAN §2.1) 역공학 트랙은 물리(기존 DDL·ORM)를 먼저 확정하고 논리를 역산한다. 이때도 DICT는 여전히 MODEL을 선행하지만, 역할이 「속성명을 결정한다(prescriptive)」에서 「기존 컬럼명을 표준사전에 역등재·검증한다(descriptive)」로 전환된다. 그 등재 결과가 논리 모드 속성명의 SSOT로 소비되므로, 논리가 물리 뒤에 오는 역공학 트랙에서도 `DICT → 논리`의 SSOT 관계는 그대로 유지된다.
- (근거: task:104 PLAN §2.1) 이 전환은 신규 규정을 요구하지 않는다 — SSOT는 이미 "기존 사전이 인풋으로 주입되면 DICT는 '검증·보강' 모드로 축약 가능"을 규정하고, opdd STEP 2 디스패치 프롬프트도 이미 "신규 작성 또는 검증·보강(기존 사전 주입 여부에 따라 자동 분기)" 모드를 갖고 있었다. `[MUST]` DICT 선행 문장을 한 글자도 고치지 않고 성립한다.

## 결정 내용

1. opdd STATE에서 DICT(행 3-5)가 MODEL(행 6-8) 앞에 위치한다. 이 순서는 신규·역공학 두 트랙 공통이다.
2. DICT 단계는 절대 건너뛰지 않는다 — 기존 사전이 있으면 "검증·보강 모드"로 발동, 부재 시 "신규 작성 모드"로 발동. 역공학 트랙에서는 기존 컬럼명을 사전에 역등재·검증하는 형태로 "검증·보강 모드"가 발동한다.
3. DDL은 MODEL 물리(DBML) 완료 이후에만 실행 가능 (state-tool stage-transition guard 자동 차단).

## 영향 범위

- `opal/skills/opal-pilot-data-design/SKILL.md` — 파이프라인 순서 강제, 트랙별 STEP 3 실행 순서 분기
- `opal/skills/op-data-model/SKILL.md` — 논리 모드: "속성명 = DICT 표준사전 용어 [MUST]" (역공학 트랙에서도 동일 요구, 다만 사전 값의 출처가 역등재분)
- `opal/skills/op-data-ddl/SKILL.md` — "물리(DBML) 산출 이후에만 실행 가능 [MUST]"
- `docs/proposals/opal-data-design.md` §3.2 — 원천 설계 결정

## 관련 페이지

- [[opdd-pipeline-flow]]
- [[op-data-dictionary-skill]]
- [[op-data-model-skill]]
- [[opdd-reverse-track-physical-first-order]]
