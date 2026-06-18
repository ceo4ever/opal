---
type: concept
title: skill-registry validate 확장 — dangling error 격상 + unregistered 역방향 감지
tags:
- skill-registry
- validate
- drift-detection
- tooling
sources:
- task:029
related:
- opal-architecture
- opal-brain-not-pilot-decision
- opal-skill-classification-system
created: '2026-06-18'
updated: '2026-06-18'
status: active
---
## 개념 요약

`opal/tools/skill-registry/skill-registry.js`의 기존 `validate()` 함수를 확장하여 레지스트리↔디스크 드리프트를 결정론적으로 감지한다. dangling을 warning에서 error로 격상하고, unregistered를 역방향으로 신규 감지한다.

## 배경·문제 (WHY)

태스크 029 분석에서 레지스트리에 dangling 2건(`op-sdd-tasks`·`opal-orchestrator`)과 미등록 1건(`op-sdd-action-plan`)이 잠복해 있었다. 기존 `validate()`는 no-SKILL.md를 **warning**으로만 처리(exit 0)하여 CI·커밋 훅에서 드리프트를 차단하지 못했다. validate 자체를 강화하여 재발을 결정론적으로 방지한다.

## 결정 내용 (HOW)

### (a) no-SKILL.md error 격상

`opal/tools/skill-registry/skill-registry.js:379`에서 `warnings.push(...)` → `errors.push(...)` 한 줄 변경. `valid:false → process.exit(1)` 자동 전파.

### (b) unregistered 역방향 감지 — 소스 환경 전용

`opal/skills/` + top-level `skills/` 양쪽 스캔으로 SKILL.md가 있으나 레지스트리 미등록 폴더를 감지한다.

- **소스 환경 전용**: `getReferencesDir()`이 `opal/core/references/` 반환 시에만 활성 — 배포 환경(`~/.opal/references/`) false positive 방지
- **standalone 오판 방지**: top-level `skills/` 폴더도 스캔 포함, 등록된 경우 unregistered 제외 (TC5)

### (c) 단위 테스트 신규

`opal/tools/skill-registry/tests/test-validate.js` 5케이스 (TC1 clean / TC2 dangling / TC3 unregistered / TC4 배포환경 / TC5 standalone). RED-first 트랙 적용.

### validate가 즉시 효용 실증

작동 직후 기존 잠복 드리프트 `system-architecture-html`(paths에 `~/.opal/skills/...` 누락)를 추가 검출 → 형제 항목 패턴에 맞춰 보충. 드리프트 감지가 실제로 동작함을 확인.

## 영향·관계

- `opal/tools/skill-registry/skill-registry.js` — validate() 확장, validateUnregistered() 신규
- `opal/tools/skill-registry/tests/test-validate.js` — 단위 테스트 신규
- 후속 계획: validate를 커밋 훅/CI(opgc)에 연결하여 레지스트리 드리프트 상시 차단

## 근거 출처

태스크 029 (`task:029`), `opal/tools/skill-registry/skill-registry.js:277-392,379,448-450`
