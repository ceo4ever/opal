---
type: concept
title: E2E 후보 순서·충실도 소유 경계 — 계약이 소유하고 코드가 복제하지 않는다
tags:
- e2e
- driver
- fidelity
- contract
- ownership
sources:
- task:127
related:
- e2e-integration-gap-pattern
- e2e-frozen-spec-seeding-constraint
created: '2026-09-18'
updated: '2026-09-18'
status: draft
---
## 개념 요약

E2E 후보 순서와 충실도 등급은 **계약이 소유하고 코드가 복제하지 않는다.** 태스크 127과 ADD-1에서 이 소유 경계가 두 번 시험받았고 두 번 다 계약 쪽으로 정리했다.

## 후보 순서 — C-DRV-3이 소유한다

기본 순서: `agent-browser/orca-managed` → `cmux/owned-surface` → `agent-browser/standalone` → `ego-lite/standalone` → `playwright(opt-in)`

### 왜 부분 driver를 1순위에 두지 않는가

ADD-1에서 Ego Lite를 흡수할 때 캡틴 의도는 1순위였다. 실측 후 **더 나쁜 기본값**으로 판단해 뒤로 옮겼다.

- `ego-browser-tool`의 `smoke`는 open과 텍스트 assert가 **융합된 단일 연산**이다. `act`·`wait`·`snapshot`·`capture`가 없다.
- 1순위면 UI 조작이 필요한 시나리오에서도 먼저 `selected`되고, 실행 도중 `driver_operation_unimplemented`로 `blocked`가 된다 — **더 완전한 driver를 가린다.**
- 현재 후보 게이트는 capability(§A.8.1 6키)만 보고 **"이 시나리오가 `act`를 쓰는가"를 표현할 수단이 없다.** 그 게이트가 없는 동안은 순서로 방어하는 것이 맞다.

**해제 조건**: ops 기반 후보 게이트(시나리오 step에서 요구 연산을 뽑아 제공하지 않는 후보를 실행 전에 거름)가 생기면 1순위에 둬도 안전하다. `docs/proposals/e2e-journey-fragment-library.md` Q-6이 이 항목을 소유한다.

### 순서는 기본값이다

ADD-1에서 `resolve_candidates(candidate_order=...)`를 열었다. 코드 상수 `CANDIDATE_ORDER`는 기본값일 뿐이고 호출자·프로젝트가 재정의할 수 있다. smoke 형태만 도는 프로젝트는 이 수단으로 `ego-lite`를 1순위에 올린다.

**순서를 바꿔도 전환 조건은 불변이다** — C-3·`can_try_next_provider()`가 `provider_unavailable`에만 다음 후보를 허용하고 `infra_error`·제품 실패에서는 넘어가지 않는다.

## 충실도 — `FIDELITY_ORDER`가 단독 소유한다

`mock` < `real-http` < `real-usage` 정의는 `lib/scenario.py:119` 한 곳에만 있다. 파이프라인 문서(oppl `verification.md`, opsdd SKILL 등)는 **참조만** 하며 정의 문장을 보유하지 않는다(태스크 127 AC-14).

- `api` profile의 상한은 `real-http`다. `real-usage`는 실제 브라우저 후보가 `selected`될 때만 나온다.
- 이 비대칭이 태스크 127에서 `all_surfaces_green` 도달 불가를 만들었다 — PM이 `api` 표면에 `required_fidelity: real-usage`를 시드했는데 구조적으로 도달할 수 없는 값이었다(B-5 이월).

## 소유 경계가 시험받은 두 사례

| 사례 | 잘못된 방향 | 택한 방향 |
|---|---|---|
| ego-lite 추가로 `test_candidate_order_follows_cdrv3`가 깨짐 | 테스트만 고치고 계약은 방치 | **계약(C-DRV-3)을 먼저 개정**하고 그 계약을 단언하는 테스트를 맞췄다. 순서가 계약이기 때문이다 |
| `match: "contains"`가 `pass`에 도달 불가 | 하네스에서 `contains`를 따로 통과시킴 | `e2e_contract.py`는 C-1로 동결이므로 **기록만** 하고 시나리오는 `equals`로 쓴다 |

## 관련

[[e2e-integration-gap-pattern]] · [[e2e-frozen-spec-seeding-constraint]] · [[oppl-evidence-fidelity-principle]]
