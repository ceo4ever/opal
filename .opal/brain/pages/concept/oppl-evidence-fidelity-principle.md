---
type: concept
title: 증거 충실도(Evidence Fidelity) 원칙 — mock/real-http/real-usage 사다리
tags:
- oppl
- verification
- evidence-fidelity
- enforce-dont-advise
sources:
- task:069
related:
- oppl-surface-inventory-contract
- oppl-coverage-conformance-axis-split
- oppl-scenario-red-confirmed-gap
- oppl-3-ssot-tool-gated-separation
- test-tool
created: '2026-07-19'
updated: '2026-07-19'
status: active
---
## 개념 요약

oppl의 완료(done) 판정에 "증거 충실도" 개념을 1급 규범으로 도입한다. 시나리오가 어떤 상대·환경에서 실행됐는지를 `mock(0) < real-http(1) < real-usage(2)` 3단계 사다리로 tool-gated 기록하고, 사용자가 실제 접촉하는 표면·여정은 `real-usage` 수준 PASS 없이는 완료로 인정하지 않는다.

## 결정 배경 (WHY)

타 프로젝트에서 `//oppl`로 병렬 개발한 실전 사고 사례 — 목(MSW) 상대로만 검증된 FE, 서버 미기동 상태에서 GREEN 처리된 시나리오, 표본(3개 표면)만 검사하고 "크로스스택 OK"로 오판한 사례 — 가 발생했다. 근본 원인은 개별 결함(auth 누락·CORS 미검사)이 아니라, **판정 기준 자체가 "테스트가 통과했는가"만 보고 "무엇을 상대로 통과했는가"를 반영하지 않았다는 것**이다. 소유자가 이를 "CORS 자체가 아니라 그 수준의 결함이 테스트를 통과한 것이 문제"로 근본 원칙화했다(task:069 TASK.md 확정 방향).

이 원칙은 열거식 결함 체크(auth, CORS 등)의 집합이 아니라, 미열거 결함 클래스까지 구조적으로 봉쇄하는 상위 게이트로 설계되었다.

## 결정 내용 (HOW)

- **사다리 정의**: `mock`(목 상대 테스트 코드, 단위 수준) < `real-http`(실 서버 기동 + 계약 spec 기반 실 HTTP 전수 conformance, auth 토큰 체인 포함) < `real-usage`(실 브라우저 E2E — cmux-tool 우선/playwright 폴백, 실 진입점·실 데이터 흐름).
- **필드 2종 분리(부분 게이트)**: test-scenario.json에 `required_fidelity`(spec존, 요구)와 `fidelity`(result존, 실제 달성)를 분리한다. `scenario-fidelity-check`는 시나리오별로 `result==pass AND fidelity >= required_fidelity`를 판정 — 혼합 트랙(일부는 mock으로 충분, 일부는 real-usage 요구)에서 [[oppl-scenario-red-confirmed-gap]]과 유사하게 발견된 task:061 "전부-아니면-전무 게이트 붕괴" 재발을 피한다.
- **하위 호환 기본값**: `required_fidelity`·`fidelity` 미지정 시 둘 다 `mock` 간주 → 기존 test-scenario.json(양 필드 부재)은 `mock >= mock`로 conformant 처리되어 회귀 0을 보장한다. surfaces.json 자체가 없는 프로젝트는 conformance 게이트가 `applicable:false`로 스킵된다.
- **BE/FE 매핑**: BE 단위=테스트 코드 / 통합=spec 기반 실 HTTP. FE 단위=목 허용 컴포넌트 테스트 / 통합=실 브라우저×실 BE.
- **게이트 에러의 복구가능 분류**: `fidelity_unmet`을 포함한 신규 게이트 에러 4종은 loop-control.md §7 "복구가능(recoverable)" 행에 편입 — 재작업(더 높은 충실도 재검증)으로 해소되며 blocked 전환은 기존 무진전(no-progress)·반복 상한 경로로만 발생한다.
- **실행 주체 분리**: 프레임워크 도구(test-tool)는 규범·게이트만 정의하고, 실 HTTP 호출·브라우저 E2E "실행"의 주체는 대상 프로젝트의 test-agent다 — 프레임워크가 HTTP를 직접 구현하지 않는다.

## 영향 범위

- `opal/tools/test-tool/lib/scenario.py` — `FIDELITY_ORDER`, `required_fidelity`/`fidelity`/`surface_ref` 필드, `scenario-fidelity-check`(exit 13)·`scenario-conformance`(exit 14/15)
- `opal/skills/opal-pilot-project-loop/references/verification.md` §1.5 증거 충실도 사다리·§1.6 스켈레톤 메커니즘
- `opal/skills/opal-pilot-project-loop/references/loop-control.md` §7 신규 게이트 에러 4종 복구가능 분류
- `opal/agents/opal-loop-action-agent/AGENT.md` — 요구 충실도·surfaces_path 주입(T1/T2), T4a fidelity/conformance 게이트 호출
- `opal/agents/opal-evaluator-agent/AGENT.md` — Base 루브릭 ⑩ 워킹 스켈레톤 태스크 존재·구성 판정

## 관련 페이지

- [[oppl-surface-inventory-contract]]
- [[oppl-coverage-conformance-axis-split]]
- [[oppl-scenario-red-confirmed-gap]]
- [[oppl-3-ssot-tool-gated-separation]]
- [[test-tool]]

