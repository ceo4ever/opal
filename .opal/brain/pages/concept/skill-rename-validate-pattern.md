---
type: concept
title: 스킬 rename 후 레지스트리 정합 검증 패턴
tags:
- skill-registry
- validate
- rename
- drift-detection
- lesson
sources:
- task:030
related:
- skill-registry-validate-extension
- skill-opal-next
created: '2026-06-21'
updated: '2026-06-21'
status: active
---
## 개념 요약

스킬 rename/추가 태스크 후 레지스트리 정합 검증 시, `validate exit 0`이 아니라 `unregistered:0 + 활성 잔존 0`이 진짜 성공 기준이다. 소스 환경에서 validate는 배포본 경로(`~/.opal/skills/`)를 검증하므로 재배포 전 신규/미배포 스킬은 항상 dangling으로 검출된다.

## 배경·문제 (WHY)

태스크 030(`opal-start → opal-next` 개명) 검증 단계에서 `validate exit 0` 기대가 PLAN 워커에 의해 TEST-SCENARIO에 잘못 기재됐다. 실제로 소스 환경에서 validate를 실행하면:

1. **신규/미배포 스킬 dangling**: `opal/core/references/opal-skills-registry.json`의 `paths`는 `~/.opal/skills/...` 배포본 경로를 가리킨다. 재배포 전에는 해당 경로가 존재하지 않아 dangling으로 잡힌다. 이는 개명/추가의 결함이 아니라 예상된 상태다.
2. **pre-existing dangling**: 태스크 019(데이터 설계 스킬) 등 이전 태스크의 스킬이 소스에 있으나 아직 배포되지 않은 경우 dangling으로 잡힌다. 별건 배포 드리프트이며, 개명 태스크와 무관하다.

따라서 `validate exit 0`을 요구하면 아직 배포되지 않은 모든 스킬을 먼저 배포해야만 검증이 통과되는 비현실적 조건이 된다.

## 결정 내용 (HOW)

**스킬 rename/추가 태스크의 실제 검증 기준**:

| 검증 항목 | 기대값 | 의미 |
|----------|--------|------|
| `unregistered` 건수 | 0 | 소스 폴더↔레지스트리 역방향 정합 (rename된 폴더가 레지스트리에 등록됨) |
| 구 이름 활성 잔존 | 0 | 이전 name/alias/triggers/paths가 레지스트리에서 완전 제거됨 |
| match `//new-trigger` | `found:true` | 신규 트리거가 매칭됨 |
| match `//old-trigger` | `found:false` | 구 트리거가 더 이상 매칭되지 않음 |
| validate exit code | 무관 | 재배포 전 dangling은 예상 상태 — exit 0 요구하지 않음 |

**pre-existing dangling 판별**: validate 출력에서 dangling 항목이 구 이름(`opal-start`)인지, 이번 태스크와 무관한 항목(별건 드리프트)인지 확인한다. 구 이름 dangling이 0건이면 rename 정합 완료.

## 영향·관계

- 이 패턴은 **향후 스킬 rename·추가 태스크 전반에 재사용**된다.
- PLAN.md TEST-SCENARIO 작성 시 `validate exit 0` 대신 `unregistered:0 + 활성 잔존 0` 기준으로 기재해야 한다.
- [[skill-registry-validate-extension]] — validate 도구 설계 (dangling error 격상, unregistered 역방향 감지)
- [[skill-opal-next]] — 이 패턴이 최초 적용된 태스크

## 근거 출처

태스크 030 DONE.md §검증 결과, AGENTIC-LOG #4·#5 (`task:030`). `opal/tools/skill-registry/skill-registry.js`
