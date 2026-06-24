---
type: concept
title: OPAL 부트스트랩 스킵 게이트 (setting.json Read 기반)
tags:
- bootstrap
- platform
- adapter
- session-toggle
- setting-json
sources:
- task:040
- task:043
related:
- bootstrapper-marker-ssot-single-point
- opal-adapter-platform-isolation
- read-based-gate-pattern
created: '2026-06-24'
updated: '2026-06-24'
status: active
---
## 개념 요약

`~/.opal/setting.json`의 `bootstrap` 필드를 `off`로 설정하면 OPAL 부트스트랩 전체(정체성·헌법·하네스·PM 컨텍스트 포함)를 건너뛰고 순수 Claude Code로 동작하는 세션/캡틴 전역 토글이다. (task:040 도입 → task:043 메커니즘 전환)

## 배경·문제 (WHY)

OPAL 부트스트랩 Eager 단계는 principles → identity → harness → pm → 프로젝트 AGENT.md → MEMORY → PROJECT 순으로 7개 문서를 로드한다. 이 부하가 비OPAL 단발 잡담이나 프레임워크 자체 디버깅 세션에서 불필요한 토큰·지연을 발생시킨다 (근거: task:040 TASK.md §배경).

기존에도 부트스트랩을 건너뛰는 경로가 있었으나 `[WORKER]` 스킵(디스패치 프롬프트 첫 줄)은 워커 전용이라 캡틴 세션에는 적용되지 않았다 (근거: task:040 TASK.md §배경). 캡틴/세션 전역에서 끌 수 있는 별도 토글이 필요했다.

task:040은 `echo $OPAL_BOOTSTRAP`(Bash) 방식으로 게이트를 도입했으나, 셸 변수 확장(simple_expansion)은 Claude Code가 매 세션 권한 프롬프트를 유발했다 (근거: task:043 PLAN §1.2). task:043에서 부트스트랩이 이미 무프롬프트로 사용하는 `Read(~/.opal/**)` 경로에 게이트를 얹어 **새 권한 표면 0**으로 전환했다.

## 결정 내용 (HOW)

- **발동 방식 (043 이후)**: Read 도구로 `~/.opal/setting.json`을 읽어 JSON의 `bootstrap` 필드를 확인한다. 마커 텍스트에 해당 지시를 삽입하여 LLM이 Read로 값을 확인하게 한다. `Read(~/.opal/**)` 글롭이 이미 권한 등록되어 있으므로 새 권한 표면 0 (근거: task:043 PLAN §1.2, §3.2.2).
- **조건 단순성**: 필드 값이 **정확히 `off`**일 때만 스킵한다. 미설정/`on`/기타 값은 모두 기존 동작과 동일하게 처리하여 조건을 단일 매칭으로 유지한다.
- **fail-safe 폴백**: 파일 부재·필드 부재·`off` 아닌 값·JSON 파싱 실패 시 게이트를 무시하고 정상 부트스트랩을 수행한다. 게이트 미동작이 정상 동작으로 안전하게 수렴한다.
- **스킵 범위**: 부분 스킵 없이 정체성을 포함한 전부를 생략한다 — `off`이면 순수 Claude Code로 동작한다.
- **2중 방어선**: 마커(진입점)와 `opal/core/AGENT.md` Eager 절차 step 0에 동일 조건·동작의 게이트를 명문화하여 문서 정합을 유지한다. 두 게이트는 별개 경로인 `[WORKER]` 스킵과 명시적으로 구분된다.
- **setting.json 배포**: `opal/core/setting.default.json` (소스, 기본값 `{"bootstrap":"on"}`) → install이 `~/.opal/setting.json`으로 create-if-absent 배포. 사용자가 `off`로 편집하면 재설치에도 보존(멱등).
- **프로젝트 오버라이드**: 현재 글로벌 `~/.opal/setting.json` 단일 채택. 프로젝트 단위 오버라이드는 후속 태스크(H-8) (근거: task:043 PLAN §3.1.2 결정 D-3).

## 영향·관계

- 4종 플랫폼 마커 SSOT(`opal/bootstrapper/claude-bootstrap.md`, `codex-bootstrap.md`, `gemini-bootstrap.md`, `cursor-bootstrap.mdc`) 한 곳을 수정하면 macOS·Windows 어댑터가 동일 게이트를 자동 배포한다 — 단일 지점 수정 원리는 [[bootstrapper-marker-ssot-single-point]] 참조.
- 플랫폼 분기를 어댑터 계층에서만 처리하는 원칙([[opal-adapter-platform-isolation]])을 강화한다.
- install 재배포(`scripts/install-mac.sh`) 후에 발효한다. `~/.opal/` 직접 편집은 금지이며 항상 소스(`opal/`)를 수정한 뒤 배포한다.
- 설계 패턴 일반화: [[read-based-gate-pattern]] — "매 세션 게이트는 Read 기반 설정파일로 설계" 원칙의 최초 적용 사례.

## 근거 출처

- task:040 — `OPAL_BOOTSTRAP=off` 부트스트랩 스킵 옵션 (최초 도입)
- task:043 — 메커니즘 전환: Bash echo → `~/.opal/setting.json` Read 기반
- 마커 SSOT: `opal/bootstrapper/{claude,codex,gemini}-bootstrap.md`, `opal/bootstrapper/cursor-bootstrap.mdc`
- Eager step 0 게이트: `opal/core/AGENT.md` (step 0)
- 설정 소스: `opal/core/setting.default.json`
