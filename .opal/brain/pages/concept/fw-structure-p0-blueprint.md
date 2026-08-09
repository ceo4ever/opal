---
type: concept
title: FW 구조개선 P0 실측 결론 — BLUEPRINT SSOT 확정
tags:
- fw-structure
- architecture-decision
- pipeline
- task-086
sources:
- task:086
related:
- pipeline-json-spec
created: '2026-08-09'
updated: '2026-08-09'
status: draft
---
## 개요

OPAL FW(스킬·레퍼런스·에이전트·도구·레지스트리 5층) 구조개선 4-Phase 계획의 P0(청사진 정식화 + 잔여 실측)가 완료되어, `BLUEPRINT.md`(`tasks/086-260809-opp-fw-구조개선-청사진-실측/BLUEPRINT.md`)가 후속 P1~P3 태스크의 참조 SSOT로 확정되었다.

## 결정 배경 (WHY)

이전에는 pipeline.json↔SKILL.md 중복률, 미보유 pilot의 스키마 확장 소요, 태스크당 디스패치 수(K4), 로드 사슬 실효값 4가지가 미실측 상태였다(근거: task:086 DONE.md §4). 정적 합산 수치("16문서 3,144줄" 등)만으로 개선 계획을 세우면 실제 절감 효과를 과대 추정할 위험이 있어, 4건의 실측 부록(A1~A4)을 먼저 만들고 그 실측치를 근거로만 P1~P3 범위·완료기준을 잠갔다(근거: task:086 BLUEPRINT.md §5 서두).

## 결정 내용

- **P2 1차 범위는 스키마 무확장으로 고정**한다. A1이 제안한 스키마 확장 후보 5필드는 A2의 "미보유 6 pilot 전건 EXPRESSIBLE(확장 불필요)" 판정과 다른 질문에 대한 답이므로 충돌이 아니며, 확장은 P2 1차의 선행 조건이 아니다(근거: `BLUEPRINT.md` §5.2 (0), `A2-스키마소요.md:199-204,247`). 5필드는 착수 게이트 4항(전건 스키마 검증 통과·optional+현행 기본값·재검증 의무·미충족 시 P3 이월)을 전건 충족해야만 P2 2차로 착수한다.
- **WHAT-D/WHAT-P 절단선**: pipeline.json 보유 4 pilot의 산문 685줄(57.4%) 중 pipeline.json에 이미 존재하는 실중복(WHAT-D) 221줄(18.5%)만 P2 1차에서 즉시 절단하고, 잠재중복(WHAT-P) 464줄(38.9%)은 스키마 확장 없이는 절단 불가하므로 1차 범위에서 제외한다(근거: `A1-중복률.md:198-206`).
- **K4(디스패치 하한)·로드 실효값 기준선**: K4 평균이 L1 정적 하한 대비 opd 3.1배·opds 3.2배이며 EXECUTE 단계가 전체의 74.5%를 차지한다는 실측을 근거로 StepCount≥10 조건부 배치 기준선을 채택했고(근거: `A3-스폰실측.md:171`), 표본 3건의 실효 로드가 정적 합산의 60~74%에 불과함을 근거로 P1의 하네스 압축 완료기준(P1-C1~C3)을 잠갔다(근거: `A4-로드사슬.md:136-142,171-186`).

## 영향 범위

`tasks/086-260809-opp-fw-구조개선-청사진-실측/BLUEPRINT.md`가 P1(하네스 압축+Opus 5 정합)·P2(데이터 주도 전환)·P3(액션 에이전트 통합+2차 도구화) 3개 후속 태스크의 범위·완료기준·롤백 단위를 결정한다. 본 태스크는 읽기 전용이며 `opal/`·`skills/`·`agents/`·`~/.opal/` 변경은 0건이다.

## 관련 페이지

- [[pipeline-json-spec]]
- [[dynamic-loop-add-row-not-schema-extension]]
- [[observability-field-design-at-record-time]]
