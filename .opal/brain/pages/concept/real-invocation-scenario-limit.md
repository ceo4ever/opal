---
type: concept
title: 실호출 시나리오 한정 기준
tags:
- test
- scenario
- opal-agent
sources:
- task:172
related: [test-parallel-group-single-agent-only, opal-evaluator-agent]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

TEST 시나리오가 에이전트를 실제로 호출하는 경우를 "모델 판단 자체가 수용 기준"인 때로 한정하고, 호출은 시나리오당 1회로 제한하는 기준이다. 더 싼 계층으로 증명할 수 있으면 실호출을 쓰지 않는다.

## 결정 내용

- 시나리오 작성 가이드는 실호출 행에 `[실호출 1회]` 표지를 요구한다 (`opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`).
- 평가자는 기록된 결과 파일로 같은 계약을 증명할 수 있는 실호출 시나리오를 `cheaper_layer` 권고로 지적한다. 실제 반환이 S-12에서 확인되었다 (근거: task:172 DONE.md AC-1·AC-2).
- 호출은 정식 wrapper `opal-agent`로 하고 원 CLI 직접 호출을 하지 않는다. 원본 JSON 응답을 증거로 저장해 대조한다 (`opal/core/references/harness/test-cycle.md`). 처음에는 raw CLI로 수행했으나 정식 wrapper 우선 규칙에 어긋나 정정했고, 이미 얻은 증거는 유효로 보존했다 (근거: task:172 DONE.md).
- 헤드리스 호출이 불가능하면 blocked로 반환하고 PM이 우회 판정하지 않는다.

## 관련 페이지

- [[test-parallel-group-single-agent-only]]
- [[opal-evaluator-agent]]
