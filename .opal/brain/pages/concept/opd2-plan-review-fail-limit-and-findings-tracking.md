---
type: concept
title: opd2 사전심사 fail 3회 상한과 지적 해소 추적
tags:
- opd2
- plan-review
- findings
sources:
- task:173
related: [opal-pilot-dev2, opd2-state-tool-integration, design-gate-gaps-resolution-roundtrip, opd2-plan-review-reverify-doc-over-tool-relaxation]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

opd2의 PLAN 사전심사는 재시도에 상한이 없었고, fail 지적이 다음 회차에서 해소됐는지 확인할 방법도 없었다. 도구가 fail 기록 수를 세어 3건이면 사용자 결정 대기로 전환하고, 지적 항목을 `open_findings`로 다음 회차에 잇도록 했다.

## 결정 배경 (WHY)

기존 도구는 되돌리기(rewind)만 세었다(근거: task:173 PLAN§접근, `opal/skills/opal-pilot-dev2/scripts/lifecycle.py:542-543`). 그래서 사전심사 재시도는 무한 반복될 수 있었다. 같은 취지로 설계 게이트에는 지적 해소 왕복 계약이 이미 있었으며(task:170), 같은 발상을 사전심사 Call 단위로 옮겼다.

## 결정 내용

- 상한은 fail 기록 1건 단위로 센다. 3건이 되면 상한 대기가 되어 재심사 기록, PLAN→BUILD 전이, `rewind`, `unblock`을 모두 거부하고 `blocked`로 표시한다. 3번째 fail 자체는 정상 기록된다. 해제는 실명 사용자와 사용자 메시지를 요구하는 `plan-review-reset` 하나뿐이고, 해제 후 3회가 다시 허용된다.
- `rewind`와 `unblock`까지 막는 이유: `rewind`는 원장의 `blocked`와 사전심사 기록을 지우는 기존 탈출구라, 열어 두면 사용자 결정을 우회한다. 반대로 `rewind`가 허용되는 상태(상한 대기 밖)에서는 사전심사 기록과 `plan_review_floor`를 함께 0으로 초기화한다. 이 상한은 기존 rewind 상한(3회)과 별개다.
- 판정은 `blocked` 값이 아니라 fail 수가 소유한다. 다른 사유의 `blocked`가 있어도 게이트는 같다.
- fail은 `{id, location, remaining_choice}` 지적을 남기고, 같은 Call의 다음 기록은 직전 미해소 지적 전건에 `{id, status, evidence}`를 보고해야 한다. id 집합 불일치, 형식 위반, 판정 모순(미해소 지적을 둔 pass, 지적 없는 fail)은 기록 전에 거부되며 상한을 소비하지 않는다. 형식 오류가 상한을 먹으면 도구 오류로 사용자 결정을 부르게 되기 때문이다.
- 도구가 계산한 `open_findings`가 미해소 지적을 다음 회차로 잇는다. 단, `resolved` 보고의 내용상 진위는 도구가 검증하지 못한다(한계, `references/lifecycle.md`에 명시).
- 변경 전 원장은 `findings` 키가 없는 기록을 집계·추적에서 제외해 그대로 읽힌다.

## 영향 범위

`opal/skills/opal-pilot-dev2/scripts/lifecycle.py`, 신규 `opal/skills/opal-pilot-dev2/schemas/plan-review.schema.json`, `opal/skills/opal-pilot-dev2/agents/reviewer.md`, `coordinator.md`. REVIEW 단계 독립 리뷰, `ac_coverage` 검사, rewind 상한은 무변경.

## 관련 페이지

- [[opal-pilot-dev2]]
- [[opd2-state-tool-integration]]
- [[design-gate-gaps-resolution-roundtrip]]
- [[opd2-plan-review-reverify-doc-over-tool-relaxation]]
