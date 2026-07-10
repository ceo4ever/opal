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
related:
- oppl-two-loop-orchestrator
- oppl-3-ssot-tool-gated-separation
created: '2026-07-10'
updated: '2026-07-10'
status: active
---
## 개념 요약

oppl 드라이런 중 `test-scenario.json`의 `red_confirmed` 필드를 RED 증거와 함께 tool-gated로 갱신하는 서브명령이 부재하다는 설계 갭이 발견되었다. `scenario-init`(초기 시드)·`scenario-lock`(동결 게이트)·`scenario-mark`(결과 기록)만 있고, "RED 확인 후 red_confirmed를 증거와 함께 갱신"하는 전용 경로가 없다.

## 배경·문제 (WHY)

SPEC 확정 4종 서브명령에 이 경로가 애초에 포함되지 않아 구현 자체는 SPEC을 준수했다 — 갭은 SPEC 차원의 누락이다. "enforce, don't advise" 원칙 관점에서, red_confirmed를 `scenario-init` 시드로 우회해 채우는 현재 경로는 self-confirming 테스트 위험(H-2)을 완전히 차단하지 못한다는 한계가 있다.

## 결정 내용 (HOW)

056 범위에서는 구현하지 않고 후속 개선 과제로 기록만 한다. 드라이런에서는 "RED 실관찰 → `scenario-init` 시드" 순서로 우회했고, 이 순서를 evidence 로그에 의무 기록하는 것으로 임시 대응했다. 후속 태스크에서 `scenario-red`(가칭) 서브명령을 test-tool에 신설해 RED 증거와 함께 red_confirmed를 tool-gated로 갱신하는 경로를 마련하는 것을 제안한다.

## 영향·관계

`opal/tools/test-tool/lib/scenario.py`·`test-scenario.schema.json`에 영향을 준다. oppl SKILL T2(테스트 시나리오 RED-first) 단계의 신뢰성과 직결된다.

- [[oppl-two-loop-orchestrator]] — 이 갭이 실행 루프 검증 신뢰성에 영향을 주는 오케스트레이터
- [[oppl-3-ssot-tool-gated-separation]] — test-scenario.json SSOT 축 분리 결정과 연결되는 후속 개선 지점

## 근거 출처

task:056 — AGENTIC-LOG.md #19(IMPROVE), DONE.md 후속 과제 #1
