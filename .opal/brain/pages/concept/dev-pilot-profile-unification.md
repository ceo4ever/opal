---
type: concept
title: 개발 Pilot Full/Short profile 통합 계약
tags:
- pilot
- dev
- opd
- opds
- compatibility
sources:
- task:112
related:
- skill-opal-pilot-dev
- skill-opal-pilot-dev-short
- demote-promote-recursion-guard-timing-threshold-split
- new-ssot-pointer-not-value-copy
created: '2026-09-10'
updated: '2026-09-10'
status: draft
---
## 개요

개발 Pilot은 물리 구현을 하나로 수렴하고, 호출 표면만 Full(`//opd`)과 Short(`//opds`) profile로 분리한다. `opds`는 독립 오케스트레이터 디렉토리가 아니라 canonical `opal-pilot-dev`가 선택하는 Short profile 호환 계층이다.

## 결정 배경 (WHY)

Full과 Short가 별도 `SKILL.md`와 별도 pipeline 파일로 유지되면 공통 하네스 변경, 문서 산출물 계약, 사용자 확인 경계가 서로 드리프트한다. Task 112는 `opds`의 기존 호출·상태 호환성은 유지하면서, 중복 구현을 제거하는 방식이 가장 안전하다고 판단했다.

## 결정 내용

- `//opd`와 `//opds`는 모두 canonical Dev Pilot 구현으로 해석된다.
- Full profile은 기존 16행 pipeline 계약을 유지한다.
- Short profile은 canonical 폴더의 `pipeline-short.json`으로 11행 pipeline 계약과 `skill=opds` 상태 식별자를 유지한다.
- Short→Full 승격 규칙은 canonical Dev Pilot 참조 문서로 이동하고, Full→Short 강등과 승격은 서로 다른 시점에서 1회만 판단해 왕복 재귀를 막는다.
- `opal-pilot-dev-short` 물리 폴더는 제거 대상이지만, logical registry entry와 `opds` alias는 호환 표면으로 남긴다.

## 영향 범위

- `opal/skills/opal-pilot-dev/SKILL.md`
- `opal/skills/opal-pilot-dev/references/pipeline-short.json`
- `opal/skills/opal-pilot-dev/references/track-escalation.md`
- `opal/core/references/harness/track-routing.md`
- `opal/core/references/opal-skills-registry.json`
- `opal/tools/state-tool/tests/test_state_tool.py`

## 검증 기준

검증은 호출 해석, 상태 초기화, 라우팅 시점, 설치본 경로까지 함께 본다. Task 112에서 `//opd`·`//opds`가 같은 canonical 경로로 해석되고, Full 16행·Short 11행 상태 계약과 실제 설치본 경로가 통과했다.

## 관련 페이지

- [[skill-opal-pilot-dev]]
- [[skill-opal-pilot-dev-short]]
- [[demote-promote-recursion-guard-timing-threshold-split]]
- [[new-ssot-pointer-not-value-copy]]
