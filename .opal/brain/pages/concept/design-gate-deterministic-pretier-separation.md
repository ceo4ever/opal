---
type: concept
title: 설계 게이트 결정론/evaluator 2-tier 분리 — 회차 비소비 사전검사
tags:
- design-gate
- state-tool
- opd
- opds
- pm-path
sources:
- task:170
related: [state-tool, skill-opal-pilot-dev, design-gate-gaps-resolution-roundtrip]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

opd·opds PM 경로(`coordinator` 신규)의 설계 게이트를 "결정론 검사(값싸고 빠름)"와 "evaluator 판정(비싸고 느림, 회차 소비)" 두 티어로 분리하고, 결정론 티어를 evaluator 호출 **이전에** 회차·상태 소비 없이 미리 실행할 수 있게 했다(`state-tool verify --design-gate-check`). evaluator의 판정 기준(설계 4축·시나리오 3축·pass 조건·반복 상한 3회)은 바꾸지 않는다.

## 결정 배경 (WHY)

(근거: task:170 TASK.md) 설계 게이트를 거친 태스크 6건(161·162·163·164·167·168)의 18회차 실측에서 결정론 실패 5회·evaluator rewrite 7회·pass 6회가 나왔다. 결정론 실패는 evaluator를 부르기 전의 규칙 검사(`_design_gate_deterministic_check`)에서 나는데도 `design-gate start`가 회차를 먼저 올려, 사전에 시도 없이 미리 돌려볼 방법이 없던 실패가 반복 상한 3회 중 1회를 소모했다. 반복 상한에 걸린 167·168은 둘 다 1회차가 결정론 실패였다. evaluator rewrite 7회 중 6회가 `decision_clarity` 축 실패였고(167은 2·3회차 연속), PM 경로는 자기 검토 게이트가 없어 PLAN에 새 메커니즘이 추가돼도 대응 시나리오 누락이 다음 evaluator 회차에서야 드러났다(168 2회차 PLAN 보완 → 3회차 시나리오 부족 rewrite).

## 결정 내용

- `verify --design-gate-check`는 새 서브커맨드가 아니라 기존 `verify`의 상호배타 게이트 플래그 그룹(6번째 멤버)으로 구현한다. 기존 `_design_gate_deterministic_check(task_path)`를 그대로 재사용해 `missing` 리스트를 반환하며(비차단, exit 0), 신규 `_decision_clarity_lint(task_path)`가 같은 응답에 "판정이 아닌 후보 목록"을 동봉한다.
- `_decision_clarity_lint()`는 PLAN.md 본문에서 펜스 코드 블록과 인라인 코드 스팬을 제외한 산문만, 고정 패턴 12개(`추후 결정`·`추후 확정`·`추후 논의`·`적절히`·`적절한`·`필요시`·`필요에 따라`·`상황에 따라`·`경우에 따라`·`TBD`·`TODO`·`미정`)로 줄 단위 스캔해 후보 위치만 반환한다 — 그 자체로 FAIL을 선언하지 않는다. 설계 4축의 최종 판정 기준을 코드가 대신 내리면 판정 기준을 바꾸는 것이 되므로, 패턴을 고정 목록으로 못박아 "열린 목록"이 구현자에게 남기는 선택을 없앴다.
- `state.json`이 없으면 다른 5개 게이트 플래그와 동일하게 graceful skip(`{"ok": true, "...": "skipped"}`, exit 0)으로 처리한다 — 두 가지 실패 정책(graceful skip vs 하드 오류)을 동시에 가리켰던 모순을 "항상 graceful skip"으로 확정했다.
- PM 경로 절차(`opal/skills/opal-pilot-dev/SKILL.md` §PM 경로)에 "PLAN 작성 완료 후 `design-gate start` 호출 전에 `verify --design-gate-check`를 실행해 `deterministic_missing`을 모두 해소하고 `decision_clarity_candidates`를 검토한다"를 명문화했다. decision_clarity 자가점검은 evaluator의 Phase 1-D 기준 문구를 그대로 적용한다.
- 같은 절차에 "PLAN에 새 가드·명령·상태·오류 코드 등 새 검증 대상을 추가/변경했으면 같은 회차 안에서 TEST-SCENARIO.md에도 대응 시나리오를 반영한다"를 추가해, 168에서 실재했던 "PLAN 보완 후 다음 회차에야 시나리오 부족이 드러나는" 지연을 PM 자가점검 단계로 앞당겼다.
- 내부 결정론 검사 ①~⑦을 스레드로 병렬화하는 안은 검토 후 기각했다 — 실측 병목은 evaluator 왕복(회차당 4~6분)이지 내부 검사 순서가 아니므로 복잡도 대비 실익이 없다고 판단했다.

## 영향 범위

`opal/tools/state-tool/state_tool.py`(`cmd_verify()`·`build_parser()`의 `p_vfy`, 신규 `_decision_clarity_lint()`), `opal/skills/opal-pilot-dev/SKILL.md`(§PM 경로 절차), `opal/core/references/harness/design-gate.md`(교차참조 1문장), `opal/skills/op-dev-plan/references/plan-guide.md`·`opal/skills/op-dev-test-scenario/SKILL.md`(SSOT 링크만, 본문 중복 없음). evaluator 판정 기준·반복 상한 3회·`reset --owner user` 전용 해제 정책은 무변경.

## 관련 페이지

- [[state-tool]]
- [[skill-opal-pilot-dev]]
- [[design-gate-gaps-resolution-roundtrip]]
