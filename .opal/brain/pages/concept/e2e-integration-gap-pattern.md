---
type: concept
title: 통합 지점 공백 패턴 — 자체 테스트 통과·연결부 미검증
tags:
- e2e
- integration
- testing
- contract
sources:
- task:127
related:
- e2e-frozen-spec-seeding-constraint
created: '2026-09-18'
updated: '2026-09-18'
status: draft
---
## 개념 요약

워커가 자기 산출물에 대해 테스트를 붙여 전건 통과시켜도, **그 산출물이 다른 워커의 산출물과 만나는 지점**은 아무도 검증하지 않는다. 태스크 127에서 이 형태가 **4회** 반복됐고 매번 자체 테스트는 초록이었다.

## 관측된 4회

| # | 증상 | 자체 테스트가 놓친 이유 |
|---|------|------------------------|
| 1 | `drivers/__init__.py`가 `agent_browser`를 import하지 않아 `registered_drivers()`가 빈 상태. 전 후보가 `no_registered_driver`로 떨어짐 | driver 자체 테스트 30건은 클래스를 직접 인스턴스화해 검증했다. **레지스트리 경유 경로를 타지 않았다** |
| 2 | `orchestrator._resolve_executor_candidates()`의 non-browser 분기가 레지스트리를 조회하지 않고 `no_registered_executor`를 하드코딩. `register()` 호출 효과 0 | executor 자체 테스트 79건이 executor를 직접 호출했다. orchestrator를 우회했다 |
| 3 | `agent_browser.py`가 §B.2 8연산 중 `probe`·`open`·`close` 3개만 구현. AC-4(실 UI 행동 + semantic assertion)가 구조적으로 불가능 | 자체 테스트가 **구현한 범위만** 덮었다. 계약 목록에서 되묻지 않았다 |
| 4 | `_open_executor()`가 executor 종류를 보지 않고 `prepare`를 dispatch. `HUMAN_OPERATIONS`에 없어 `collaborative`·`manual`이 실행 불가(AC-9) | human executor 테스트가 orchestrator를 우회해 직접 호출했다 |

## 왜 생기는가

자체 테스트는 **작성자가 아는 경로**를 검증한다. 통합 지점은 두 작성자 중 누구의 것도 아니어서 양쪽 테스트 범위 밖에 남는다. 파일 소유를 분리해 병렬 작업할 때(그 자체는 옳다) 이 공백이 체계적으로 생긴다.

## 방어 수단

- **계약 목록에서 되묻는 테스트**: 구현 목록이 아니라 계약이 선언한 연산 집합(`DRIVER_OPERATIONS`)을 출발점으로 삼아 각 구현이 기반 클래스 것과 다른지 확인한다. 태스크 127의 `TestEightOperationCompleteness`가 이 형태이며 #3의 재발을 잡는다.
- **미등록을 기록으로 남긴다**: 기본 레지스트리에서 등록되지 않은 후보를 조용히 건너뛰지 않고 `no_registered_driver`로 **후보 배열에 남긴다.** 그 기록이 있어야 #1·#2의 미배선이 보인다. 반대로 명시 주입 레지스트리를 "닫힌 세계"로 만들려는 시도는 `registry={}`로 전수 기록을 검증하는 테스트와 충돌하므로 채택하지 않았다.
- **통합 관통을 별도 Work item으로 둔다**: 태스크 127의 W-14(AC 전건 관통, "코드를 고치지 않고 관측만")가 #4를 잡았다. 만드는 사람과 판정하는 사람을 가르는 것이 이 항목의 존재 이유다.

## 관련

[[e2e-frozen-spec-seeding-constraint]] · [[oppl-evidence-fidelity-principle]]
