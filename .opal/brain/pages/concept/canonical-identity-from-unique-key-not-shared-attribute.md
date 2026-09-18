---
type: concept
title: canonical identity는 공유 가능한 속성이 아니라 고유 키에서 파생한다
tags:
- identity
- data-modeling
- adapter
- lesson
sources:
- task:140
related:
- fixture-vs-real-blind-spot-lesson
- skill-registry-project-scope-4source-merge
created: '2026-09-18'
updated: '2026-09-18'
status: draft
---
## 개요

여러 레코드가 같은 물리 파일이나 속성을 공유하는 것은 정상적인 설계일 수 있다. 이런 데이터에서 화면·카탈로그에 노출할 고유 식별자(canonical identity)를 파생할 때는, 공유될 수 있는 속성이 아니라 레지스트리가 보장하는 고유 키에서 파생해야 한다. 공유 속성을 키로 쓰면 공유 그룹에 속한 레코드가 하나로 병합되거나 소실된다. (근거: task:140 PLAN.md DEC-5, DONE.md)

## 결정 배경 (WHY)

OPAL Console의 스킬 문서 화면(task:140)은 스킬 레지스트리를 병합해 카탈로그를 구성하면서 두 종류의 스킬 프로필이 같은 절차 파일(`SKILL.md`)을 가리키는 케이스(`opal-pilot-dev`와 `opal-pilot-dev-short`)를 만났다. 이는 레지스트리 전체에서 유일한 파일 공유 사례이며, 프로필을 분리해 등록한 정상 설계다. (근거: task:140 DONE.md "canonical identity를 레지스트리 name에서 파생")

개발 과정에서 파일 경로(`paths`) 기반으로 canonical identity를 파생하는 시도가 있었는데, 이 규칙은 `opal-pilot-dev-short`(별칭 `opds`)가 카탈로그에서 소실되는 결과를 낳았다 — 같은 `paths`를 가진 두 레코드가 하나로 합쳐지면서 나중 레코드가 덮어써졌기 때문이다. (추론: 코드패턴 — `paths` 동일 시 병합되는 인덱싱 구조에서 도출)

## 결정 내용

- **원칙**: canonical identity는 레지스트리가 고유함을 보장하는 필드(레지스트리 `name`)에서 파생하고, 여러 레코드가 공유할 수 있는 속성(물리 파일 경로 `paths`, 소스 frontmatter의 `name` 등)에서 파생하지 않는다.
- **frontmatter name과의 구분**: 스킬 파일 자체의 frontmatter `name`은 canonical identity가 아니라 provenance(출처 표시) 필드로만 보존한다. 레지스트리 `name`과 frontmatter `name`이 다를 수 있으며, 이 경우도 레지스트리 `name`이 우선한다.
- **공유는 예외가 아니라 정상 케이스로 설계에 반영한다**: `paths` 공유 자체를 오류로 취급하지 않는다. 레지스트리 전체에서 이런 공유 그룹이 1건뿐이더라도, 식별자 파생 규칙은 "0건"을 전제하지 말고 공유가 있어도 각 레코드가 독립적으로 보존되도록 설계해야 한다.

## 영향 범위

- `dashboard/backend/adapters/skill_docs_adapter.py` — canonical identity를 레지스트리 `name` 기준으로 파생 (task:140)
- 레지스트리·카탈로그처럼 다중 소스를 병합해 고유 식별자를 매기는 모든 어댑터 설계에 재사용 가능한 일반 원칙

## 관련 페이지

- [[fixture-vs-real-blind-spot-lesson]] — 이 오류가 fixture 설계 결함으로 발현된 반복 교훈의 5번째 사례
- [[skill-registry-project-scope-4source-merge]]
