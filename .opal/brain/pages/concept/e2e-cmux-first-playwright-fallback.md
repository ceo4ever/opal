---
type: concept
title: E2E 도구 우선순위 — cmux 1순위 → playwright 폴백 (에러코드 소비)
tags: [testing, e2e, cmux, framework]
sources: [task:039]
related: [test-tool, test-two-tier-system, wtm-agent-cmux-integration, cmux-tool-dispatcher-expansion]
created: 2026-06-23
updated: 2026-06-23
status: active
---

## 개요

통합(TEST) 단계의 E2E 검증에서 도구 우선순위를 cmux 1순위, playwright 폴백으로 고정한 결정이다. cmux 가용성은 별도로 재구현해 판정하지 않고, cmux 연동 도구(cmux-tool)가 반환하는 에러코드를 소비해 폴백/에스컬레이션을 결정한다.

## 결정 배경 (WHY)

이전 문서들에는 E2E 도구 순서가 `playwright/cmux`로 역순 표기되거나 우선순위가 불명확했다. 캡틴이 cmux를 1순위로 정정했고, 동시에 가용성 판정을 "대충 체크 금지"로 못박았다 — 각 도구가 `cmux --version`·`uname` 같은 환경 검사를 제각기 재구현하면 플랫폼 독립 원칙이 깨지고 판정이 중복·불일치하기 때문이다 (근거: task:039 DONE§2 결정 C·E-1).

## 결정 내용

- **우선순위**: cmux 1순위 → playwright 2순위(폴백). cmux 미가용은 폴백 트리거이지 실패가 아니다.
- **가용성 판정 위임**: cmux 가용성은 cmux-tool의 4-gate 에러코드를 소비해 판정한다. test-tool은 cmux 환경 검사를 직접 재구현하지 않는다 (헌법 플랫폼 독립).
- **폴백 트리거 4종**: `not_in_cmux`·`cmux_not_installed`·`surface_parse_failed`·`open_failed` — 이 경우에만 playwright로 폴백한다.
- **에스컬레이션 5종**: `usage`·`invalid_surface`·`goto_failed`·`wait_failed`·`eval_failed` — URL/네트워크/명령 오류이므로 폴백으로 우회하지 않고 즉시 에스컬레이션한다. 실제 결함을 폴백으로 가리는 것을 막는다.
- **mode A 격리**: E2E는 매 테스트마다 신규 surface를 open→navigate→단언→close하는 mode A로 실행한다. 사용자의 기존 surface를 재사용하지 않아 세션 훼손과 재현성 저하를 막는다 (근거: task:039 DONE§2 결정 E-2).

## 영향 범위

- 도구: [[test-tool]]의 E2E 어댑터(`opal/tools/test-tool/lib/e2e_adapter.py`)가 이 분기 로직을 구현한다.
- 문서 정합: 테스트 시나리오 가이드·테스트 에이전트 정의 등 관련 문서의 E2E 순서가 cmux 1순위로 일관되게 교정됨.

## 관련 페이지

- [[test-tool]] — 에러코드 소비 폴백을 집행하는 도구
- [[test-two-tier-system]] — 이 E2E 우선순위가 적용되는 통합 단계
- [[wtm-agent-cmux-integration]] — cmux-tool 폴백 체인의 선행 사례
- [[cmux-tool-dispatcher-expansion]] — cmux-tool 에러코드·디스패처 확장
