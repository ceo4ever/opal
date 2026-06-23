---
type: concept
title: 테스트 2단계 체계 (단위=EXECUTE / 통합=TEST)
tags: [testing, pipeline, framework]
sources: [task:039]
related: [test-tool, e2e-cmux-first-playwright-fallback, test-scenario-pipeline-redesign, verification-command-4-standard]
created: 2026-06-23
updated: 2026-06-23
status: active
---

## 개요

OPAL의 테스트 수행을 두 단계로 재정의한 체계다. 단위 테스트는 EXECUTE 단계에서 구현 워커가 스스로 수행하는 자가검증이고, 통합 테스트는 TEST 단계에서 전담 테스트 에이전트가 수행하는 실연동 검증이다. 각 단계는 프론트엔드/백엔드 영역별로 서로 다른 도구 매트릭스를 갖는다.

## 결정 배경 (WHY)

기존 검증 체계는 여러 축의 "L번호"(검증 계층 L1~L4, 검증 깊이 L1/L2/L3)가 혼재해 워커가 단계를 오해석할 위험이 있었다. 캡틴이 테스트 수행 위상을 파이프라인 단계에 명시적으로 고정해, 어느 검증이 누구의 책임이고 어느 파이프라인 단계에 귀속되는지 못박았다 (근거: task:039 DONE§2 결정 A).

## 결정 내용

- **단위 테스트 = EXECUTE 단계**: lint + build/type + unit 검증을 구현 워커가 자가검증으로 수행한다. 한 계층이 실패하면 다음 계층을 실행하지 않는 stop-on-fail 단발 실행이며 watch 모드를 쓰지 않는다.
- **통합 테스트 = TEST 단계**: E2E + 실DB 기반 검증 + 캡틴 수동 [SUPERVISOR]를 전담 테스트 에이전트가 수행한다. mock을 금지하고 실DB로 검증한다.
- **FE/BE × 단계 도구 매트릭스**: 단위 단계는 FE(eslint·tsc·vitest+RTL·접근성), BE(ruff/eslint·mypy/tsc·pytest/vitest)로, 통합 단계는 BE 실DB API와 FE/BE 공통 E2E로 구성된다. 접근성 도구는 FE 단위 단계에 1종(jest-axe)만 등록해 과설계를 피했다 (근거: task:039 PLAN§3.5.2 H-12).
- **lint 위상 고정**: lint/build/type은 단위(EXECUTE) 귀속이므로, TEST 단계에서 중복 재검하지 않는다.
- **3축 분리 명시**: 검증 계층(실행 비용 순서)·검증 깊이(기능/통합/협업)·파이프라인 단계(단위/통합)는 서로 다른 축이며, 한 곳에 매핑 표로 정의해 동일 "L번호"로 인한 혼동을 제거했다.
- **PASS-or-fix 루프 강제, 한도는 단일 SSOT**: 단계별 PASS-or-fix 재시도는 강제하되 한도 수치는 하네스 §1 한 곳에서만 정의하고 도구·문서에 복제하지 않는다.

## 영향 범위

- 도구: [[test-tool]] resolve/unit/integration 서브명령이 이 2단계를 집행한다.
- 레지스트리: test-tools.yaml/schema가 `tiers`(unit/integration) 구조로 재구조화됨 (`opal/templates/test-tools.yaml`, `opal/core/references/test-tools-schema.yaml`).
- 문서 배선: 테스트 시나리오 가이드·테스트 에이전트·검증 루프 가이드가 2단계 명명과 3축 매핑을 반영하도록 갱신됨.

## 관련 페이지

- [[test-tool]] — 2단계를 집행하는 결정론적 도구
- [[e2e-cmux-first-playwright-fallback]] — 통합 단계 E2E의 도구 우선순위
- [[test-scenario-pipeline-redesign]] — 테스트 시나리오 작성 시점·작성자 분리(선행 재설계)
- [[verification-command-4-standard]] — 검증 명령 표준
