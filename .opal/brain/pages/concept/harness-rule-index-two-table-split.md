---
type: concept
title: 하네스 규칙 인덱스 표 A/B 이원화
tags:
- fw-structure
- harness
- task-087
sources:
- task:087
related:
- fw-structure-p0-blueprint
created: '2026-08-09'
updated: '2026-08-09'
status: draft
---
## 개요

하네스 규칙 인덱스를 표 A(하네스 모듈)와 표 B(규칙 인덱스·직접 참조) 2개로 분리해, `harness/` 모듈이 아닌 문서(단계 스킬·PM 절차 문서)까지 하네스가 직접 지시하는 대상으로 승격했다(근거: task:087 PLAN §2.3, `opal/core/references/opal-harness.md:99-113`).

## 결정 배경 (WHY)

표 등재 완료기준이 "표 행수 == 12"로 상한과 하한을 동시에 고정했는데, 홉 평탄화가 필요한 대상(단계 스킬 등 5~6종)을 같은 표에 넣으면 행수가 12를 넘어 이 기준이 실패한다. 두 요구(표 행수 고정, 3홉 노드 평탄화)가 한 표 안에서는 공존할 수 없어 표를 분리했다(근거: task:087 PLAN §2.3 "설계 결정 D-A", DONE.md §2 P1-C3).

## 결정 내용

- **표 A — 하네스 모듈**: Lazy 로드되는 `harness/` 모듈 전용. 데이터 행을 11에서 12로(PM 검토 게이트 1행 추가) 정확히 맞추고, 이 표에는 다른 행을 추가하지 않는다.
- **표 B — 규칙 인덱스(직접 참조)**: `harness/` 모듈이 아닌 문서(단계 스킬, PM 절차 문서)를 하네스가 직접 참조해 2홉으로 만드는 인덱스. 표 A와 소유 도메인이 다르므로 의미상으로도 분리가 타당하다고 판단했다.
- 표 B 등재 대상은 최초 후보 4건에서 실측(전수 조사)으로 8건까지 확정됐다 — 판별이 모호한 항목은 "모호하면 계상"(보수적 판정) 원칙을 적용했다. 이 원칙을 반대로 적용해 계상 대상을 줄이면 평탄화 필요 대상이 줄어 완료기준을 사후에 쉽게 만드는 결과가 되므로 채택하지 않았다(근거: task:087 AGENTIC-LOG 판단 3, 4).

## 영향 범위

`opal/core/references/opal-harness.md`(표 A·표 B 동시 위치), `opal/core/references/harness/task-process.md`(op-task Read 간선을 표 B 포인터로 대체), `opal/skills/op-task/SKILL.md`(2홉 진입 경로 명시). `opal/core/AGENT.md`의 Lazy 트리거 표·pilot alias 진입 경로는 불변 제약으로 편집 범위에서 제외했다.

## 관련 페이지

- [[fw-structure-p0-blueprint]]
- [[conditional-batch-output-cap-tradeoff]]
