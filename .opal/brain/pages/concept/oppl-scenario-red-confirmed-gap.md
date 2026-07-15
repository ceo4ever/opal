---
type: concept
title: 드라이런 발견 갭 — test-scenario red_confirmed tool-gated 갱신 경로 부재
tags:
- lesson
- test-tool
- oppl
- gap
- enforce-dont-advise
sources:
- task:056
- task:061
related:
- oppl-two-loop-orchestrator
- oppl-3-ssot-tool-gated-separation
created: '2026-07-10'
updated: '2026-07-14'
status: active
---
## 개념 요약

oppl 드라이런 중 `test-scenario.json`의 `red_confirmed` 필드를 RED 증거와 함께 tool-gated로 갱신하는 서브명령이 부재하다는 설계 갭이 발견되었다. `scenario-init`(초기 시드)·`scenario-lock`(동결 게이트)·`scenario-mark`(결과 기록)만 있고, "RED 확인 후 red_confirmed를 증거와 함께 갱신"하는 전용 경로가 없다.

## 배경·문제 (WHY)

SPEC 확정 4종 서브명령에 이 경로가 애초에 포함되지 않아 구현 자체는 SPEC을 준수했다 — 갭은 SPEC 차원의 누락이다. "enforce, don't advise" 원칙 관점에서, red_confirmed를 `scenario-init` 시드로 우회해 채우는 현재 경로는 self-confirming 테스트 위험(H-2)을 완전히 차단하지 못한다는 한계가 있다.

## 결정 내용 (HOW)

056 범위에서는 구현하지 않고 후속 개선 과제로 기록만 한다. 드라이런에서는 "RED 실관찰 → `scenario-init` 시드" 순서로 우회했고, 이 순서를 evidence 로그에 의무 기록하는 것으로 임시 대응했다. 후속 태스크에서 `scenario-red`(가칭) 서브명령을 test-tool에 신설해 RED 증거와 함께 red_confirmed를 tool-gated로 갱신하는 경로를 마련하는 것을 제안한다.

`scenario-red` 서브명령은 이후 태스크 056 추가작업에서 실제로 신설되어(`--evidence` 필수, `red_confirmed`는 오직 이 경로로만 true가 됨) self-confirming 우회는 봉쇄되었다. 그러나 **혼합 트랙 문제는 남아 있다** — `scenario-lock`이 SSOT 내 전 시나리오의 `red_confirmed==true`를 요구하는 전부-아니면-전무 게이트여서, RED 증거가 필요한 시나리오와 필요 없는 시나리오(예: E2E 수동 확인, 캡틴 승인 게이트)가 하나의 `test-scenario.json`에 섞이면 lock 자체가 불가능하다.

**재발 사례(task:061)**: 콘솔 설정 화면 태스크에서 BE 강제 트랙(RED-first) 시나리오와 비RED 트랙(E2E·소유자 승인) 시나리오가 함께 필요했으나, scenario-lock이 혼합 트랙을 지원하지 않아 블로커가 되었다(근거: task:061 AGENTIC-LOG #9~11). 해소책은 이번에도 우회였다 — `test-scenario.json` SSOT를 RED 트랙 시나리오(S-1~S-5)만으로 좁혀 재구성해 lock을 통과시키고, 나머지 비RED 시나리오(S-6~S-10)는 `TEST-SCENARIO.md` 문서에서만 추적했다. 이 우회는 SSOT tool-gated 원칙(→ [[oppl-3-ssot-tool-gated-separation]])을 비RED 시나리오에 대해서는 사실상 포기하는 것이라, 근본 해결이 아니다.

**정제된 후속 제안**: `scenario-init`에 시나리오 단위 `red_required`(트랙 구분) 필드를 도입해, `scenario-lock`이 `red_required: true`인 시나리오에만 `red_confirmed` 게이트를 적용하도록 한다. 이렇게 하면 하나의 SSOT 안에 RED 트랙과 비RED 트랙이 공존하면서도 각자에 맞는 검증 방식으로 lock을 통과할 수 있다.

## 영향·관계

`opal/tools/test-tool/lib/scenario.py`·`test-scenario.schema.json`에 영향을 준다. oppl SKILL T2(테스트 시나리오 RED-first) 단계의 신뢰성과 직결되며, opd(op-task 계열) 파이프라인의 혼합 트랙 태스크에도 동일하게 적용된다.

- [[oppl-two-loop-orchestrator]] — 이 갭이 실행 루프 검증 신뢰성에 영향을 주는 오케스트레이터
- [[oppl-3-ssot-tool-gated-separation]] — test-scenario.json SSOT 축 분리 결정과 연결되는 후속 개선 지점

## 근거 출처

task:056 — AGENTIC-LOG.md #19(IMPROVE), DONE.md 후속 과제 #1. task:061 — AGENTIC-LOG.md #9~11(재발·정제 제안), DONE.md §운영 기록·§잔여 후속 액션 #2.
