---
type: concept
title: 어댑터 본문 model 레벨 치환 — frontmatter 비대칭 해소 (032)
tags:
- adapter
- install
- model
- platform
- sub-dispatch
- constitution
sources:
- task:032
related:
- opal-adapter-platform-isolation
- model-mapping-latest-tracking
- codex-dispatch-inline-injection
created: '2026-06-21'
updated: '2026-06-21'
status: active
---
## 개념 요약

배포 어댑터가 에이전트 frontmatter의 `model` 키만 플랫폼 실모델명으로 변환하던 비대칭을, 에이전트 **본문(body)의 인라인 sub-dispatch 토큰**(`(..., model: <레벨>)`)까지 동일하게 변환하도록 확장한 패턴이다. 소스는 플랫폼 중립 레벨명(`advanced/standard/light`)을 유지하고, 실모델명 변환은 배포 시점 어댑터에서만 일어난다.

## 배경·문제 (WHY)

OPAL 에이전트 소스는 플랫폼 독립을 위해 모델을 레벨명으로만 기술한다. 배포 어댑터(`emit_platform_agent_adapter`)는 frontmatter `model:`만 실모델명으로 치환했고 본문은 "변경 없이 복사"였다. 그러나 oppd Phase 3 액션 에이전트(opal-task-action-agent·opal-sdd-action-agent)는 본문에 sub-worker 디스패치를 인라인으로 기술하며 그 안에 `(op-dev-plan, model: advanced)` 같은 레벨명 토큰이 들어간다. 배포본 본문이 변환되지 않으면 액션 에이전트가 레벨명을 Agent 도구 `model` enum에 그대로 전달해 디스패치가 실패한다. frontmatter만 변환하는 비대칭이 버그의 근원이었다.

대안으로 소스 본문에 실모델명을 박는 방법은 플랫폼 독립성을 깨므로 기각했다(헌법 — 변환은 어댑터에서만). 캡틴이 AskUserQuestion으로 "옵션 A: 본문도 어댑터에서 변환"을 확정했다.

## 결정 내용 (HOW)

### 본문 치환은 sub-dispatch 토큰만 — 구조적 앵커로 prose 자기참조 차단

순진한 정규식 `model:\s*(light|standard|advanced)\b`는 본문 산문의 자기참조(`` `model: standard`를 따른다 ``)까지 오염시킨다. 따라서 sub-dispatch 토큰의 구조적 특징인 **괄호 내부 등장**을 앵커로 한다: 토큰은 항상 `, model: <레벨>` 또는 `(model: <레벨>` 형태로 등장하고 뒤에 `)`가 따른다. 앵커 정규식 `(?P<lead>[,(]\s*)model:\s*(?P<lvl>light|standard|advanced)\b`로 선행 콤마/여는괄호를 요구해 백틱 내부 prose 자기참조를 미매칭시킨다 (`scripts/install-mac.sh` `_sub_body_model`).

### 3가지 케이스 처리

- **실모델명 매핑 존재**: `model: <레벨>` → `model: <실모델명>` (claude는 `opus`/`sonnet`, gemini는 `gemini-pro-latest`/`gemini-flash-latest`).
- **매핑 부재**(레벨명 오타·미지원 플랫폼): 원문 유지 — 방어적으로 손대지 않는다.
- **cursor `inherit`**: 오버라이드 토큰 자체를 제거한다. 본문에 `model: inherit`를 남기면 Agent 도구 model 파라미터로 오인 시 enum 위반이 나므로, `, model: <레벨>`은 통째로 제거하고 `(model: <레벨>`은 여는 괄호만 보존한다. 결과적으로 액션 에이전트는 model 오버라이드 없이 디스패치 → 타겟 에이전트 frontmatter(cursor=`inherit`)를 상속한다. 백틱-skill 형태에서 남는 빈 괄호 `()`는 `\s*\(\s*\)` 2차 정리로 제거한다(sentinel 정리).

### 이미 실모델명/inherit인 토큰은 미매칭

정규식 alternation이 레벨명 3종(`light|standard|advanced`)만 포함하므로 `opus`·`sonnet`·`haiku`·`inherit`은 매칭되지 않는다. 즉 어떤 플랫폼에서 이미 하드코딩된 실모델명은 변환 대상이 아니다(R-3 오경보의 근거이기도 하다 — 본문 산문 자기참조 외에는 손대지 않음).

### 본문은 frontmatter 변환과 완전 독립

어댑터는 이미 body를 분리 보유하므로 본문 치환은 frontmatter 치환과 독립 적용한다. 정규식은 frontmatter가 아닌 `body` 문자열에만 적용한다.

### macOS ↔ Windows 미러

`scripts/install-mac.sh`의 `_sub_body_model`과 `scripts/install/windows.ps1`의 `Convert-BodyModelTokens`는 문자 단위 동일 정규식·동일 3케이스 로직을 미러한다. Windows는 Markdown 직렬화 경로와 Codex TOML 직렬화 경로 양쪽에 적용한다. ModelMap 4컬럼이 양 스크립트에서 동기되어야 한다.

## 영향·관계

- `scripts/install-mac.sh` — `_LEVEL_RE`+`_sub_body_model`을 `f.write(body)` 직전에 추가.
- `scripts/install/windows.ps1` — `Convert-BodyModelTokens` 신규 + Markdown·Codex TOML 양 경로 적용.
- `opal/core/references/agents.md` — "본문은 변경 없이 복사" 무조건 진술을 제거하고 인라인 model 토큰 변환·cursor·prose 예외를 명시.
- 발효 조건: 소스만 변경이므로 활성 env에 적용하려면 install 재배포 1회가 필요하다(배포본 액션 에이전트 본문이 실모델명으로 변환되어야 sub-dispatch 정상 동작).

이 패턴은 [[opal-adapter-platform-isolation]] 헌법(변환은 어댑터 계층에서만)의 구체 적용이며, [[model-mapping-latest-tracking]] ModelMap을 본문 경로에 재사용한다. Codex 인라인 디스패치 정합은 [[codex-dispatch-inline-injection]]과 인접하다.

## 근거 출처

task:032 — DONE.md(F-001~F-005 GREEN), PLAN.md §3.1.2 `_sub_body_model` 설계잠금-1, §3.2.2 cursor inherit 설계잠금-2, §3.3.2 windows.ps1 미러.
