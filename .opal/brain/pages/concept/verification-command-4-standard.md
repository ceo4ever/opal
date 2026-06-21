---
type: concept
title: 검증 명령 4종 표준 (SSOT — verification-loop-guide)
tags:
- verification
- lint
- build
- test
- watch-mode
- ssot
- standard
sources:
- task:033
related:
- skill-opal-pilot-project-dev
- analysis-drift-pm-cross-verify-lesson
created: '2026-06-21'
updated: '2026-06-21'
status: active
---

## 개요

OPAL 자동 검증 체계에서 사용하는 검증 명령을 L1~L3b 4종 계층으로 표준화한 결정. SSOT는 `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md`이며, cascade 가이드(wbs-guide·roadmap-guide·parallel-execution-guide 등)는 이 SSOT를 따르는 예시 정합만 수행한다.

## 결정 배경 (WHY)

태스크 033 이전까지 캡틴 제시 4종 표준과 OPAL 가이드 간 부분 불일치가 존재했다: L1 린트가 `:fix` 없는 체크 전용(`npm run lint`), L3a 테스트가 Jest식 `--testPathPattern` 예시(16건 산재), "watch 모드 금지" 규칙 미명문화. 실무상 테스트는 단발 실행을 해왔으나 플래그·규칙으로 강제되지 않아 CI 환경에서 무한 대기 위험이 잠재했다.

## 결정 내용

### 4종 표준 계층 매핑

| 계층 | 표준 명령 (예시) | 원칙 |
|------|----------------|------|
| L1 lint/format | `npm run lint:fix` | 자동 수정 포함 (체크 전용 lint 금지) |
| L2 build/type | `npm run build` / `npx tsc --noEmit` | 기존 표준 유지 |
| L3a unit/integration | `npm test -- --run` | watch 모드 금지(단발 실행 전용) |
| L3b E2E | `npm run test:e2e` / `npx playwright test` | 기존 표준 유지 |

### watch 모드 금지 규칙 (SSOT 단일 기재)

L3a/L3b 테스트는 watch 모드를 금지하고 단발(non-watch) 실행만 허용한다. 자동 검증 루프가 무한 대기에 빠지지 않도록 하기 위한 원칙이며, 러너별 단발 옵션(Vitest `-- --run`, Jest `--ci`/`--watchAll=false`)은 예시로만 제시한다.

이 규칙은 SSOT(`verification-loop-guide.md`)에만 1회 기재된다. cascade 가이드는 규칙을 재서술하지 않고 예시 명령만 정합한다 — SSOT 이원화 방지.

### 플랫폼 독립성 원칙 (PRINCIPLES.md Core Stance)

"watch 모드 금지"는 러너 독립 원칙으로 기술하며, `-- --run`은 Vitest **예시**로만 둔다. 특정 테스트 러너를 하드 강제하지 않는다. 검증 명령은 각 프로젝트의 `package.json` scripts 추론 키(`lint`/`build`/`test`·`test:unit` 등)를 기반으로 추론한다 (`opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md`의 §검증 명령 결정).

### generic 금지 원칙과의 양립

wbs-guide의 "액션별 구체 명령 필수, generic 명령 금지"(L46/L175/L264 원칙 설명문) 원칙은 보존된다. `npm test -- --run` 단독(대상 지정 없는 generic)이 아닌, 액션별 구체 대상(`--run src/**/auth*` 등)을 유지하는 방식으로 Vitest식으로 치환되었다.

## 영향 범위

- `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` — SSOT, §2 계층 표·watch 금지 규칙·`--testPathPattern` 2건 치환
- `opal/skills/opal-pilot-project-dev/references/wbs-guide.md` — `--testPathPattern` 14건 Vitest식 치환, generic 금지 원칙 보존
- `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` — `npm run lint` → `lint:fix` 정합
- `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` — 동일 lint:fix 정합
- `opal/skills/opal-pilot-project-dev/SKILL.md` — WBS 예시 표 lint:fix 정합
- `docs/CONVENTIONS.md` — 검증 명령 4종 표준 SSOT 포인터 등록
- `dashboard/frontend/` — vitest 셋업으로 L3a 표준이 실제 동작(build-only → unit 포함 전환)

## 관련 페이지

- [[skill-opal-pilot-project-dev]]
- [[analysis-drift-pm-cross-verify-lesson]]
