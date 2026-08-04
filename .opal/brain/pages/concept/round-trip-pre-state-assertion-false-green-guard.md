---
type: concept
title: 왕복 검증 사전 상태 단언 — false green 차단 장치
tags:
- testing
- pattern
- task-083
sources:
- task:083
related:
- code-scan-split-execution-precedes-block
- code-scan-fixture-policy-override-absorption
created: '2026-08-04'
updated: '2026-08-04'
status: draft
---
## 개요

"조치 후 위반이 0건"이라는 결과만 단언하는 왕복(round-trip) 시나리오는, 애초에 픽스처 정책이 잘못 잡혀 처음부터 위반이 0건이었던 경우에도 공허하게 참이 된다. 이를 막으려면 조치 **전** 시점에 "위반이 존재한다"는 사실을 먼저 단언해야 검증이 성립한다.

## 결정 배경 (WHY)

083의 완료기준 ④는 초과 매니페스트 1개를 제안(`--plan`) → 집행(`split`) → 재검증(`validate`) 순으로 처리해 초과가 해소되고 엔트리 유실이 0건임을 시나리오로 입증하는 것이었다(근거: task:083 TASK.md §명확화 결과 완료기준 ④). 이 왕복을 검증하는 시나리오(S-16)를 설계하면서, "재검증 결과가 0건"만 확인하면 검증이 무너지는 경로가 있다는 것이 드러났다 — 픽스처의 `shardPolicy`(예: `maxBytes`가 너무 크게 잡혀 있어 애초에 아무것도 초과 판정되지 않는 경우) 설정이 잘못돼도 "재검증 0건"은 똑같이 참이 되기 때문이다(근거: task:083 DONE.md §5.3 "사전 상태 단언이 핵심이다 — 이것 없이 '0건이 되었다'만 보면 픽스처 정책 오설정도 공허하게 참이 되어 false green이 된다").

## 결정 내용

- S-16 시나리오는 시작 시점에 `validate --json`을 호출해 `manifest_oversize === 1`임을 **먼저** 단언한다 — 이 사전 상태 단언이 있어야 뒤이은 "0건이 됐다"는 결과가 실제로 조치의 효과임을 보증할 수 있다(근거: task:083 DONE.md §5.3, TEST-SCENARIO.md S-16 "① 사전 상태 단언(필수)").
- 이 시나리오는 4단계를 전부 관통한다 — `validate`(탐지) → `split --plan --out`(제안) → `split --groups --dry-run`(예행) → `split --groups`(집행) → `validate`(재검증). 중간 산출물인 groups 문서를 사람이 수정하지 않고 그대로 다음 단계의 입력으로 재사용해, "제안 출력이 곧 집행 입력이 된다"는 왕복 계약까지 같은 시나리오 안에서 함께 검증한다(근거: task:083 TEST-SCENARIO.md S-16 "② 전 궤 관통... ④ 왕복").
- 종료 조건은 위반 0건뿐 아니라 **엔트리 총합이 실행 전후 동일**해야 한다(유실 0건, `split`의 절대 조건) — 위반이 사라졌다는 사실과 데이터가 안 없어졌다는 사실은 서로 다른 실패 모드를 잡아내므로 둘 다 단언이 필요하다(근거: task:083 TASK.md 제약 ⑥, TEST-SCENARIO.md S-16 "③ 종료 상태").
- 이 시나리오는 목표-커버 게이트 1회차에서 advisory로 보강됐다 — 사전 상태 단언과 `validate` 시작 링크는 게이트 통과 이후 미리 발견된 개선점을 흡수한 것이며, 게이트 판정 자체는 흡수 이전 시점에 이미 성립해 있었다(근거: task:083 AGENTIC-LOG.md 2026-08-04 11:55 기록).

## 영향 범위

"조치 전/조치 후"를 비교하는 모든 회귀·왕복 검증 시나리오에 적용 가능한 설계 규율이다 — 결과 상태만 단언하는 시나리오는 그 결과가 조치의 효과인지, 애초에 조건이 성립하지 않아서인지를 구분하지 못한다. 사전 상태를 먼저 단언하면 이 구분이 시나리오 안에서 구조적으로 강제된다.

## 관련 페이지

- [[code-scan-split-execution-precedes-block]]
- [[code-scan-fixture-policy-override-absorption]]
