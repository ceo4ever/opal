---
type: concept
title: 하위 절 번호 삽입으로 외부 인용 보존 — 의미 위치와 주소 안정성 동시 확보
tags:
- documentation
- reference-integrity
- harness
- task-095
sources:
- task:095
- task:084
related:
- section-append-at-tail-preserves-backrefs
- self-edit-line-anchor-drift
- legacy-row-address-gate-insertion-regression
- anchor-load-condition-must-match-target
- scenario-prewrite-goal-series-track
created: '2026-08-19'
updated: '2026-08-19'
status: draft
---
## 개요

절 번호로 외부에서 인용되는 문서에 새 절을 넣을 때, 뒤따르는 절 번호를 미는 중간 삽입 대신 **직전 절의 하위 번호**로 삽입하면 의미상 자연스러운 위치와 외부 인용 무결성을 동시에 지킬 수 있다. 신설 절을 §1.5 직후 §1.6으로 넣어 기존 §2~§6 헤딩을 문자 단위로 보존한 사례다.

## 결정 배경 (WHY)

- 신설 절의 주제는 적용 기준 절 바로 뒤가 의미상 자연스러웠다. 그러나 그 자리에 §2를 새로 만들면 기존 §2~§6이 한 칸씩 밀린다(근거: task:095 PLAN.md §3.1.1, 리스크 가설 H-f).
- 삽입 전 실측에서 이 문서의 §2(작성자≠구현자)·§3(테스트 불변성)·§4(공개 인터페이스 검증)·§5(graceful skip)가 **60건 이상** 외부에서 절 번호로 인용되고 있음이 확인됐다 — 도구 테스트 스위트 8종, 규율 체크리스트(`opal/core/references/harness/coding-principles.md:53`), 테스트 워커 에이전트 정의(`opal/agents/opal-test-agent/AGENT.md:91`)가 인용원이다(근거: task:095 PLAN.md H-f).
- 절 번호는 사실상 주소다. 주소를 밀면 인용 측이 조용히 다른 규칙을 가리키게 되고, 파손 여부가 즉시 드러나지 않는다.

## 결정 내용

- 신설 절을 **하위 번호**(§1.5 직후 §1.6)로 배치했다. 상위 절과 주제적으로 하위 관계이므로 의미 인접성이 성립하고, 정수 번호 절의 순번은 하나도 변하지 않는다(`opal/core/references/harness/red-first.md:50`).
- 회귀 방어는 헤딩 문자열 불변 검사로 집행했다 — 정수 번호 절 헤딩 개수와 문자열이 변경 전과 동일함을 확인했고, 외부 인용의 지시 내용이 여전히 유효함을 대조했다(근거: task:095 TEST-SCENARIO.md 회귀 시나리오, DONE.md §4).
- **선택 기준**: 말미 추가는 참조 무결성을 지키지만 의미 인접성을 포기한다(→ [[section-append-at-tail-preserves-backrefs]]). 하위 번호 삽입은 둘 다 지키지만 **신설 내용이 직전 절의 하위 주제일 때만** 성립한다. 하위 관계가 아니면 말미 추가가 옳다.
- 일반화: 문서 편집 계획을 세울 때 "이 문서의 절 번호가 외부에서 인용되는가"를 먼저 실측하고, 인용이 존재하면 삽입 위치를 의미가 아니라 주소 안정성으로 결정한다.

## 영향 범위

- `opal/core/references/harness/red-first.md:50` — 하위 번호로 삽입된 신설 절.
- 인용 측 무변경 — 도구 테스트 스위트 8종, `opal/core/references/harness/coding-principles.md:53`, `opal/agents/opal-test-agent/AGENT.md:91`.

## 관련 페이지

- [[section-append-at-tail-preserves-backrefs]]
- [[self-edit-line-anchor-drift]]
- [[legacy-row-address-gate-insertion-regression]]
- [[anchor-load-condition-must-match-target]]
- [[scenario-prewrite-goal-series-track]]
