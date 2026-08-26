---
type: concept
title: OPAL 스킬 분류 체계 — opal-pilot / op-* / opal-* 의미 계층
tags:
- skill-registry
- classification
- pilot
- operator
- architecture
sources:
- task:029
related:
- opal-architecture
- opal-brain-not-pilot-decision
- skill-registry-validate-extension
created: '2026-06-18'
updated: '2026-06-18'
status: active
---
## 개념 요약

`opal-skills-registry.json`의 `groups` 키가 OPAL 스킬 의미 계층의 SSOT다. 스킬은 실행 방식에 따라 3종으로 분류되며, 이 체계가 레지스트리 그룹 재배치(태스크 029)를 통해 정합화됐다.

## 배경·문제 (WHY)

`op-spec-validator`·`op-brain-ingest`·`opal-pilot-project-dev` 3건이 잡동사니 `opal` 그룹에 오배치되어 있었다. 분류 비일관은 레지스트리 SSOT의 의미를 훼손하고 validate 검사의 가치를 낮춘다. 태스크 029에서 분류 체계를 명시적으로 정의하고 레지스트리를 정합화했다.

## 결정 내용 (HOW)

### 3종 분류 기준

| 분류 | 그룹 | 특징 |
|------|------|------|
| **오케스트레이터 (pilot)** | `opal-pilot` | 단계 파이프라인 분해 + 워커 지휘. STATE/Gate 관리. op-* 단계 스킬을 디스패치. 예: `opal-pilot-dev`, `opal-pilot-sdd`, `opal-pilot-gc` |
| **단계 스킬 (op-*)** | `op-dev`, `op-sdd`, `op-task`, `op-brain`, `op-data` 등 | pilot이 디스패치하는 단위 실행 스킬. 단독 호출도 가능. 예: `op-dev-execute`, `op-brain-ingest` |
| **Operator (직접 실행)** | `opal` | 단일 스킬이 직접 실행. 워커 디스패치·STATE·Gate 없음. 예: `opal-brain`, `opal-onboarding`, `opal-skill-creator` |

### 태스크 029 재배치 결과

- `op-brain-ingest`: `opal` → 신규 `op-brain` (op-* 단계 스킬 — `op-data` 패턴과 대칭)
- `op-spec-validator`: `opal` → `op-sdd` (SDD 계열 단계 스킬)
- `opal-pilot-project-dev`: `opal` → `opal-pilot` (이름이 pilot인데 pilot 그룹 외부에 있었음)
- `opal-brain`: `opal` 그룹 **불변** (operator 스킬 — 리네임 철회 확정)

### `opal` 그룹 정화 기준

부트/init/메타작성 스킬 + operator 직접 실행 스킬만 잔류. op-* 단계 스킬이나 pilot이 포함되면 validate가 감지해야 한다(향후 validate 규칙 확장 후보).

### 레지스트리 groups가 의미 계층의 SSOT

스킬 분류는 `opal-skills-registry.json`의 `groups` 키에서 확정된다. 문서(PROJECT.md 등)는 파생 표시이며, groups와 불일치하면 문서가 오류다 — 레지스트리가 우선.

## 영향·관계

- `opal/core/references/opal-skills-registry.json` — groups 재배치(v3.5.0, 태스크 029): 신규 `op-brain` 그룹 추가
- 재발 방지: validate unregistered 감지로 미래 오배치 자동 검출

## 근거 출처

태스크 029 (`task:029`), `opal/core/references/opal-skills-registry.json:255,321,552`

## 관련 페이지

- [[opal-architecture]]
- [[opal-brain-not-pilot-decision]]
- [[skill-registry-validate-extension]]
