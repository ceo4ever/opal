---
type: concept
title: opd2 사전심사 재검증 정합은 도구 완화가 아니라 문서 수정으로 푼다
tags:
- opd2
- plan-review
- fingerprint
sources:
- task:173
related: [opal-pilot-dev2, opd2-state-tool-integration, opd2-plan-review-fail-limit-and-findings-tracking]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

opd2의 PLAN 사전심사에서 안내 문서가 "실패한 Call만 재실행하고 통과한 Call은 유지한다"고 말했지만 도구는 그렇게 동작하지 않았다. 이 어긋남을 도구를 완화해 맞추지 않고 문서를 도구에 맞춰 고쳤다. 결론은 "plan을 고친 뒤에는 Call A·B를 모두 다시 디스패치한다"이다.

## 결정 배경 (WHY)

사전심사 기록의 지문(fingerprint)에는 plan 해시와 저장소 트리가 들어가고, PLAN에서 BUILD로 가는 전이는 두 Call 모두 현재 지문에서 pass일 것을 요구한다 (근거: task:173 PLAN§접근, `opal/skills/opal-pilot-dev2/scripts/lifecycle.py:225-230`). 따라서 fail을 고치려고 plan을 수정하면 이전에 통과한 Call 기록도 무효가 된다. 문서의 "통과한 Call 유지"는 처음부터 도구와 모순이었다.

## 결정 내용

- 지문 결합을 풀어 통과 기록을 유지하는 길은 택하지 않았다. 아티팩트 지문 결합은 "검증 이후 산출물이 바뀌지 않았다"를 기계적으로 보증하는 기존 게이트라, 풀면 약해진다 (근거: task:173 PLAN Decisions, 제약 C-1).
- 도구가 이미 일관되게 올바른 규칙을 집행하고 있으면, 불일치는 문서 쪽을 고친다. 도구 완화는 비용 절감처럼 보이는 문서 안내를 살리려는 목적이라 정당화되지 않는다.
- 문서에서 "통과한 Call은 재실행하지 않는다", "표적 재검증으로 비용을 줄인다", "기존 재작업 상한을 공유한다"는 문장을 삭제하고 교체 문구를 넣었다. 정적 검사로 삭제 문구 부재와 교체 문구 존재를 확인했다.

## 영향 범위

`opal/skills/opal-pilot-dev2/agents/coordinator.md`, `opal/skills/opal-pilot-dev2/SKILL.md`, `opal/skills/opal-pilot-dev2/references/lifecycle.md`. 도구 코드의 지문·전이 규칙은 무변경.

## 관련 페이지

- [[opal-pilot-dev2]]
- [[opd2-state-tool-integration]]
- [[opd2-plan-review-fail-limit-and-findings-tracking]]
