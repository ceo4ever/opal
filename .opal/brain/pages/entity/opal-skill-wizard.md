---
type: entity
title: opal-skill-wizard (osw)
module: <code-scan @header module>
layer: <code-scan @header layer>
domain: <code-scan @header domain>
exports: []
source_ref: '<코드 파일 경로 — 예: opal/tools/state-tool/state_tool.py>'
header_synced: <YYYY-MM-DD>
tags:
- skill
- skill-registry
- project-scope
- task-114
sources:
- task:114
related:
- skill-registry-project-scope-4source-merge
- skill-opal-skill-manager
- skill-opal-skill-creator
- skill-opal-project-init
created: '2026-09-09'
updated: '2026-09-09'
status: draft
---
## 개요

`opal-skill-wizard`(약어 `osw`)는 프로젝트에 적합한 커뮤니티 스킬을 인터뷰·분석으로 도출해 제안하고, 승인된 스킬을 **프로젝트 스코프**에 설치하는 스킬이다. 전역 스코프 설치는 `opal-skill-manager`가 계속 전담하며, wizard는 그 스킬을 호출하지 않고 검색·검사·복사·기록을 직접 수행한다(`opal/skills/opal-skill-wizard/SKILL.md`).

## 책임 (WHAT)

- **2모드 판별**: 신규 프로젝트는 인터뷰로, `docs/PROJECT.md`가 이미 있는 기존 프로젝트는 그 문서를 재사용하고 결측 항목(원하는 스킬의 기능 범주)만 인터뷰한다.
- **제안 → 승인 → 설치 3단 흐름**: 커뮤니티 스킬(skills.sh) 후보를 제안하고, 사용자 승인을 받은 뒤 설치를 실행한다. 발견되지 않은 요구는 `opal-skill-creator`에 위임한다.
- **설치 직전 보안 게이트**: 복사 직전 `skill-registry.js scan-risk`를 호출해 SAFE/CAUTION/RISKY/UNKNOWN 4단으로 판정한다. RISKY는 추천에서 제외하고, 도구 실행 실패 시 설치를 진행하지 않는다.
- **프로젝트 registry 기록**: 설치 이력을 프로젝트 스코프 registry(`{project}/.opal/skills-registry.json`)에 남긴다.

## 설계 배경 (WHY)

- **스코프 분리** (근거: task:114 DONE.md §1) — 전역은 `opal-skill-manager`가 계속 담당하고, wizard는 프로젝트 스코프 신설을 전담한다. wizard가 manager를 호출하지 않고 검색·clone·검사·복사·기록을 직접 수행하도록 결정한 것은, 두 스코프의 설치 경로·규칙이 분리되어야 서로의 변경이 상대를 오염시키지 않기 때문이다(근거: task:114 PLAN.md DEC-2).
- **위임 페이로드 재사용** (근거: task:114 PLAN.md F-003, `opal/skills/opal-skill-manager/SKILL.md:92-102`) — `opal-skill-creator` 위임 트리거·7필드 페이로드는 기존 `opal-skill-manager`가 정의한 것을 그대로 재사용한다. wizard 전용 위임 계약을 신설하지 않았다.
- **2모드 골격 재사용** (근거: task:114 PLAN.md F-003, `opal/skills/opal-project-init/SKILL.md`) — 신규/기존 2모드 판별과 `docs/PROJECT.md` 표준 섹션 소비 방식은 `opal-project-init`의 선례를 그대로 계승했다.
- **설치 직전 게이트 원칙 계승** (근거: `opal/skills/opal-skill-manager/SKILL.md` §2 "clone은 임시, 복사가 설치") — "승인 게이트는 복사 직전 1회를 유지한다"는 전역 설치의 원칙을 프로젝트 경로에도 동일하게 적용했다.

## 관계 (HOW)

- [[skill-registry-project-scope-4source-merge]] — wizard가 설치한 스킬이 `//` 커맨드로 발동하려면 이 병합 확장이 선행돼야 한다. wizard와 skill-registry.js 확장은 서로 의존하는 짝 관계다.
- [[skill-opal-skill-manager]] — 전역 스코프 설치를 전담하는 자매 스킬. wizard는 이를 호출하지 않는다(경계 분리).
- [[skill-opal-skill-creator]] — 커뮤니티에서 발견되지 않은 요구를 위임받아 신규 스킬을 생성하는 스킬.
- [[skill-opal-project-init]] — 2모드 판별·`docs/PROJECT.md` 표준 섹션 골격의 선례 원본.

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `opal-skill-wizard SKILL.md` | `opal/skills/opal-skill-wizard/SKILL.md` | 신규 319줄 — 2모드·3단 흐름·scan-risk 게이트·registry 기록 전문 |
