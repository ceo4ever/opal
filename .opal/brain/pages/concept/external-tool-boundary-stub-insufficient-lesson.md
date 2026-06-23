---
type: concept
title: 외부 도구 경계는 스텁만으로 불충분 — 실연동 검증이 통합 결함을 잡는다
tags: [testing, lesson, integration, test-strategy]
sources: [task:039]
related: [test-real-data-validation-lesson, e2e-cmux-first-playwright-fallback, test-tool, red-test-determinism-abort-trap]
created: 2026-06-23
updated: 2026-06-23
status: active
---

## 개요

외부 도구와의 연동 경계를 스텁(stub) 테스트만으로 검증하면, 스텁이 구현과 동일한 잘못된 가정을 공유할 경우 결함이 가려진다. 실제 외부 도구를 거치는 실연동 검증(감독자 입회)만이 이런 통합 결함을 포착한 사례다.

## 결정 배경 (사례)

태스크 039 — test-tool의 E2E 어댑터가 cmux 연동 도구를 검증하는 과정:

- 어댑터가 cmux 연동 도구를 PATH 명령 이름으로 호출하도록 구현되어, 실제로는 항상 "미설치" 에러코드로 오분류되어 playwright로 폴백하는 결함이 있었다.
- 그런데 스텁 기반 단위 테스트가 **구현과 동일한 잘못된 호출 가정**을 공유했기 때문에, 11개 단위 테스트가 모두 GREEN이었음에도 이 결함을 통과시켰다.
- 캡틴이 입회한 실 cmux 라운드트립 검증(L3 [SUPERVISOR])에서야 결함이 드러났다 — 실제로는 cmux 경로로 동작해야 하는데 폴백이 발동하는 것이 관찰됨.
- 해결: 테스트 작성자가 외부 도구 명령을 환경변수로 주입하도록 RED를 교정하고, 구현자가 어댑터의 호출 경로를 실제 도구 경로(run.sh)로 고치자 단위 테스트가 다시 GREEN이 되었고 실연동 검증에서도 cmux 경로로 동작했다 (근거: task:039 DONE§4·§"S-15가 포착한 진짜 결함").

## 교훈

- **외부 도구 호출은 실제 경로로**: 외부 도구는 PATH 명령 이름이 아니라 실제 설치 경로로 호출해야 한다. 테스트 시에는 환경변수로 명령을 주입(`OPAL_CMUX_TOOL_CMD`)해 실연동을 검증한다.
- **스텁의 한계**: 스텁이 구현과 같은 오가정을 공유하면 단위 테스트는 결함을 보지 못한다. 외부 도구 경계는 스텁만으로 불충분하다.
- **실연동이 통합 결함을 잡는다**: 통합 결함은 실제 도구를 거치는 검증(감독자 입회 L3)이 잡는다. 캡틴의 "대충 체크 금지" 지시가 적중한 사례.

## 영향 범위

- 외부 도구를 subprocess로 호출하는 모든 어댑터의 테스트 전략
- TEST 단계 [SUPERVISOR] 실연동 검증의 필요성 근거

## 관련 페이지

- [[test-real-data-validation-lesson]] — 실데이터 검증이 build-only가 놓친 결함을 잡는 자매 교훈
- [[e2e-cmux-first-playwright-fallback]] — 결함이 발생했던 cmux 에러코드 소비 폴백 로직
- [[test-tool]] — 사례의 대상 도구
- [[red-test-determinism-abort-trap]] — RED 테스트 결정성 관련 교훈
