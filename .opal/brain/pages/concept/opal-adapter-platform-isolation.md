---
type: concept
title: OPAL 어댑터 계층 플랫폼 분기 격리 원칙
tags:
- adapter
- architecture
- constitution
- platform
- codex
sources:
- task:028
- task:105
related:
- adapter-body-model-level-substitution
- model-mapping-latest-tracking
created: '2026-06-17'
updated: '2026-09-03'
status: active
---
## 개요

플랫폼 sub-agent 어댑터(install-mac.sh / windows.ps1)가 OPAL frontmatter 필드를 각 플랫폼 산출물로 변환할 때, 플랫폼별 분기를 코드 조건문(`if platform == "claude"` 류)이 아니라 **선언적 스펙 테이블**(단일 JSON 리터럴 상수) 안에 가두는 원칙이다. emit 로직은 스펙을 순회할 뿐이며, 플랫폼명은 스펙을 조회하는 키로만 등장한다.

## 결정 배경 (WHY)

- (근거: task:028) 최초 문제의식은 Codex 등 플랫폼별 처리가 늘어날수록 emit 함수 안에 조건 분기가 누적되는 것을 막아야 한다는 것이었다.
- (근거: task:105 PLAN.md §리스크 가설 H-1/H-8) 태스크 105는 이 원칙을 `effort` 필드 추가로 실증했다. 기존 `emit_platform_agent_adapter`는 `name`/`description`/`model` 3필드를 `out_lines`에 무조건 append하는 고정 코드였고, 신규 필드를 넣으려면 매번 이 함수를 다시 열어야 했다. 이를 스펙 순회로 바꾸면 새 필드 추가가 "스펙에 행 추가"로 축소된다.
- (근거: task:105 PLAN.md §3.1.2 D-결정 1) 스펙 표현으로 "언어별 네이티브 리터럴"(Python dict/PS hashtable)이 아니라 **JSON 텍스트 리터럴**을 채택했다 — 두 스크립트가 바이트 동일 텍스트를 품게 되어, 미러 일치를 `diff`로 기계 검증할 수 있기 때문이다. 기존 "문자 단위 동일 정규식이어야 한다"는 사람 규약(`windows.ps1:93`)이 이 취약점 위에 서 있었다.

## 결정 내용 (HOW)

**스펙 스키마**: `{ "fields": [FieldSpec, ...] }`. FieldSpec은 `opal`(키명)·`order`(emit 순서)·`default`·`omit_if_empty` 등과, 플랫폼별 `PlatformSpec`(`mode`/`to`/`values`/`fallback`)을 담는다.

**배치 모드 3종** — 플랫폼별 배치 형태는 조건문이 아니라 `mode` 값 하나로 표현된다. emit 함수는 `mode`에만 분기한다.

| 모드 | 의미 | 예시 |
|---|---|---|
| `key` | 독립 키로 출력 (이름이 같든 다르든 동일 코드 경로) | Claude `effort` / Codex `model_reasoning_effort` |
| `model_param` | model 값 문자열에 `[k=v]` 형태로 파라미터 합성 | Cursor 예약(현재 `omit`, 활성화 시 전환) |
| `omit` | 아무 것도 출력하지 않음 | Gemini(미지원) |

**값 도메인 변환**: `resolve(field, platformSpec, raw)`가 `values` 맵 → 미스 시 `fallback` → 둘 다 없으면 stderr 경고 후 생략(exit 0 유지, install 비중단) 순으로 처리한다. `model` 필드만 `fallback`을 가지며(레벨 매핑 기존 동작 보존), `effort`는 `fallback` 없이 "미정의 값=경고+생략"으로 처리한다.

**"예약"과 "미지원"의 구분**: Cursor의 `effort`는 `model_param`으로 선언하고 값 맵을 비우는 대신, `mode:"omit"` + `note:"reserved: ..."`로 표현한다. 동작은 미지원과 동일하되, `note`로 "훗날 mode 한 줄만 바꾸면 활성화된다"는 의도를 스펙 자체에 남긴다.

**바이트 동일성 3중 보장** — 기존 3필드를 같은 스펙 경로로 흡수하면서 회귀를 막기 위한 장치: ① `order` 오름차순 + 신규 필드는 항상 `order>=40`이라 기존 3필드 뒤에 위치 ② `default` 없는 필드는 미선언 시 pair 자체가 생성되지 않아 출력 델타 0 ③ 기존 `yaml_escape`/`toml_escape` 함수를 그대로 재사용(값 인용 로직 재작성 금지).

## 영향·관계

`scripts/install-mac.sh`의 `emit_platform_agent_adapter()`(md 경로)와 `install_codex_agents()`(TOML 경로) 2벌 모두가 같은 스펙 상수를 소비한다. `scripts/install/windows.ps1`은 동일 JSON을 here-string으로 미러한다. 본문 model 토큰 치환(`_sub_body_model`)은 스펙에서 파생한 `{light,standard,advanced}→실모델명` dict를 그대로 받아 로직 무변경으로 유지된다 — frontmatter 변환 경로와 본문 치환 경로가 값 SSOT를 공유하되 갱신 로직은 분리된 경계다.

플랫폼별 effort 실제 지원 형태(실측, 2026-09-02): Claude Code=독립 필드(`effort`, `low`~`max` 5단), Codex CLI=이름 다른 독립 필드(`model_reasoning_effort`, `minimal`~`xhigh`, `max` 없음 → `xhigh`로 축약), Cursor=model 값 내 대괄호 파라미터(`model: x[effort=high]`, `inherit` 정책상 현재 부착 불가), Gemini=미지원. 이 실측이 위 스펙의 `values`/`mode` 배정 근거다.

## 관련 페이지

- [[adapter-body-model-level-substitution]]
- [[model-mapping-latest-tracking]]
