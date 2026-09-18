---
type: concept
title: 재실행 생략 키는 실행 정체를 포함해야 한다
tags:
- e2e
- fidelity
- cache
- gate
- evidence
sources:
- task:141
related:
- e2e-candidate-order-and-fidelity-ownership
- e2e-frozen-spec-seeding-constraint
- oppl-evidence-fidelity-principle
created: '2026-09-18'
updated: '2026-09-18'
status: draft
---
## 개념 요약

재실행을 생략하는 게이트의 키에는 **무엇을 검증했는가**뿐 아니라 **무엇이 그것을 검증했는가**가 들어가야 한다. 대상(코드·시나리오)만으로 키를 만들면, 실행 주체를 바꾸는 설정 한 줄이 과거의 약한 증적을 현재의 강한 요구에 재인용하는 경로를 연다.

## 발견 맥락

태스크 141에서 `docs/proposals/e2e-journey-fragment-library.md`를 검토하다 나왔다. 그 제안은 두 가지를 **같은 문서에서** 제안하고 있었다.

- §5 신선도 키 = `(여정 해시, 조각 해시, surface_id, 대상 commit)` — 이 4개가 같으면 이전 `pass`를 재인용하고 재실행을 생략한다.
- §7 후보 우선순위를 코드 상수에서 `.opal/e2e/order.json` 설정 파일로 옮긴다.

둘을 함께 채택하면 이런 순서가 성립한다.

1. 완전한 driver로 여정을 돌려 `pass` 증적을 남긴다.
2. `order.json`에서 부분 driver를 1순위로 올린다. 코드도 시나리오도 commit도 바뀌지 않는다.
3. 신선도 키가 전건 일치하므로 재실행이 생략되고, **부분 driver로는 애초에 도달할 수 없는 충실도의 증적이 그대로 재인용된다.**

키가 대상만 담고 실행 정체를 담지 않아서 생긴 구멍이다.

## 처방

키에 두 값을 더한다.

- **선택 주체의 정체** — 이 프로젝트에서는 `driver` + `session_mode`. 도구 이름만으로는 부족하다. 같은 도구도 실행 모드에 따라 제공 연산이 달라진다.
- **달성 충실도** — 요구 충실도와 비교 가능한 등급값. 비교는 `달성 ≥ 요구`로 판정한다.

등급 정의 자체는 키가 소유하지 않는다. `FIDELITY_ORDER`(`opal/tools/test-tool/lib/scenario.py:119`)가 단독 소유이고 키는 참조만 한다 — 같은 사다리를 두 곳에 적으면 둘이 갈라진다.

## 한계 — 처방이 공짜가 아니다

실행 정체는 환경에 좌우된다. 바이너리 설치 여부와 `probe` 결과에 따라 같은 commit에서도 선택 정체가 달라질 수 있다. 그러면 키가 자주 불일치해 **재실행 생략이 사실상 성립하지 않고**, 게이트를 도입한 원래 목적(전수 재실행 회피)으로 되돌아간다.

즉 이 처방은 "안전"과 "생략률"을 맞바꾼다. 어느 쪽을 택할지는 별개 결정이며, 안전을 택했다면 생략률 저하를 한계로 문서에 남겨야 한다. 남기지 않으면 나중에 생략률이 낮다는 이유로 키에서 정체를 빼는 되돌림이 일어난다.

## 일반화

E2E driver에 한정된 이야기가 아니다. 같은 형태는 캐시 키, 빌드 스킵, 증분 테스트 선택 어디서나 생긴다. 판정식은 하나다.

> **이 게이트를 통과시킨 증적을, 지금 실행했다면 만들 수 없는 조건이 존재하는가?** 존재하면 그 조건을 키에 넣어야 한다.

`.opal/brain/pages/concept/e2e-candidate-order-and-fidelity-ownership.md`가 기록한 "부분 driver를 1순위에 두면 더 완전한 driver를 가린다"가 이 위험의 구체 사례다. 순서를 데이터로 여는 변경은 그 위험을 설정 한 줄 거리로 당긴다.

## 관련

[[e2e-candidate-order-and-fidelity-ownership]] · [[e2e-frozen-spec-seeding-constraint]] · [[oppl-evidence-fidelity-principle]]
