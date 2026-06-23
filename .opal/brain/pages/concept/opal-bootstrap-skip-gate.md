---
type: concept
title: OPAL_BOOTSTRAP=off 부트스트랩 스킵 게이트
tags:
- bootstrap
- platform
- adapter
- session-toggle
sources:
- task:040
related:
- bootstrapper-marker-ssot-single-point
- opal-adapter-platform-isolation
created: '2026-06-24'
updated: '2026-06-24'
status: draft
---
## 개념 요약

환경변수 `OPAL_BOOTSTRAP=off`를 설정하면 OPAL 부트스트랩 전체(정체성·헌법·하네스·PM 컨텍스트 포함)를 건너뛰고 순수 Claude Code로 동작하는 세션 단위 토글이다.

## 배경·문제 (WHY)

OPAL 부트스트랩 Eager 단계는 principles → identity → harness → pm → 프로젝트 AGENT.md → MEMORY → PROJECT 순으로 7개 문서를 로드한다. 이 부하가 비OPAL 단발 잡담이나 프레임워크 자체 디버깅 세션에서 불필요한 토큰·지연을 발생시킨다 (근거: task:040 TASK.md §배경).

기존에도 부트스트랩을 건너뛰는 경로가 있었으나 `[WORKER]` 스킵(디스패치 프롬프트 첫 줄)은 워커 전용이라 캡틴 세션에는 적용되지 않았다 (근거: task:040 TASK.md §배경). 캡틴/세션 전역에서 끌 수 있는 별도 토글이 필요했다.

## 결정 내용 (HOW)

- **발동 방식**: 환경변수 `OPAL_BOOTSTRAP`를 세션/셸 단위로 토글한다. 마커는 LLM이 읽는 산문이라 셸 변수를 직접 판독할 수 없으므로, 마커 텍스트에 "먼저 Bash 도구로 `echo $OPAL_BOOTSTRAP`를 1회 실행하라"는 지시를 삽입해 LLM이 Bash로 값을 확인하게 한다.
- **조건 단순성**: 출력이 **정확히 `off`**일 때만 스킵한다. 미설정/`on`/기타 값은 모두 기존 동작과 동일하게 처리하여 조건을 단일 매칭으로 유지한다.
- **fail-safe 폴백**: `off`가 아니거나 Bash 도구를 사용할 수 없으면 게이트를 무시하고 정상 부트스트랩을 수행한다. 게이트 미동작이 부트스트랩 누락이 아니라 정상 동작으로 안전하게 수렴한다.
- **스킵 범위**: 부분 스킵 없이 정체성을 포함한 전부를 생략한다 — `off`이면 순수 Claude Code로 동작한다.
- **2중 방어선**: 마커(진입점)와 `opal/core/AGENT.md` Eager 절차 step 0(`opal/core/AGENT.md:11-13` 사이 삽입)에 동일 조건·동작의 게이트를 명문화하여 문서 정합을 유지한다. 두 게이트는 별개 경로인 `[WORKER]` 스킵과 명시적으로 구분된다.

## 영향·관계

- 4종 플랫폼 마커 SSOT(`opal/bootstrapper/claude-bootstrap.md`, `codex-bootstrap.md`, `gemini-bootstrap.md`, `cursor-bootstrap.mdc`) 한 곳을 수정하면 macOS·Windows 어댑터가 동일 게이트를 자동 배포한다 — 단일 지점 수정 원리는 [[bootstrapper-marker-ssot-single-point]] 참조.
- 플랫폼 분기를 어댑터 계층에서만 처리하는 원칙([[opal-adapter-platform-isolation]])을 강화한다 — 분기 없이 SSOT 1지점 수정으로 전 플랫폼을 충족한다.
- install 재배포(`scripts/install-mac.sh`) 후에 발효한다. `~/.opal/` 직접 편집은 금지이며 항상 소스(`opal/`)를 수정한 뒤 배포한다.

## 근거 출처

- task:040 — `OPAL_BOOTSTRAP=off` 부트스트랩 스킵 옵션
- 마커 SSOT: `opal/bootstrapper/{claude,codex,gemini}-bootstrap.md`, `opal/bootstrapper/cursor-bootstrap.mdc`
- Eager step 0 게이트: `opal/core/AGENT.md:11-13`
