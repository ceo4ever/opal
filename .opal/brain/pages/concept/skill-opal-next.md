---
type: concept
title: opal-next — OPAL 재진입 가이드 (opal-start 개명)
tags:
- skill
- next
- onboarding
- guide
- rename
sources:
- task:030
related:
- skill-opal-start
- skill-opal-onboarding
- skill-opal-project-init
- skill-registry-validate-extension
created: '2026-06-21'
updated: '2026-06-21'
status: active
---
## 개념 요약

`opal-start`(`//start`) 스킬을 `opal-next`(`//next`)로 개명했다. 기능·진단 로직·라우팅 분기는 완전 불변이며, 이름·트리거·참조 경로만 변경된 순수 rename이다.

## 배경·문제 (WHY)

이름 `opal-start`가 실제 기능("현재 상태 진단 → 다음 액션 안내")과 어긋나 `//opi`·`//onboarding`과 혼동을 유발했다. "시작" 이미지가 `//opi`(최초 온보딩)와 겹쳐 역할 경계가 불명확했다. `//next`는 "다음에 뭐 해야" 류 자연어 의도와 직결되며, 곧 만들 `//help`(능력 카탈로그)와 역할을 명확히 구분한다.

## 결정 내용 (HOW)

- `opal/skills/opal-start/` → `opal/skills/opal-next/` (`git mv`, 이력 보존)
- `references/start-flow.md` → `references/next-flow.md` (`git mv` + 내용 치환)
- 레지스트리 `name/alias/triggers/paths` 전부 opal-next 기준 갱신, version 3.5.0 → 3.6.0
- `//start` alias·트리거 완전 제거 (하위호환 미유지)
- 트리거 재설계: `//next`, "다음에 뭐 해야", "어디서부터 시작", "온보딩 다시 보고싶어" 유지. "시작"·"처음부터" 제거 (너무 광범위 / "처음 시작" 연상 혼동)
- `opal-onboarding/SKILL.md:176`·`README.md:125` 교차 참조 갱신
- 진단 로직(5항목 진단·7개 분기) 완전 불변

## 영향·관계

- `opal/skills/opal-next/SKILL.md` — 스킬 정의 (v2.0.0)
- `opal/skills/opal-next/references/next-flow.md` — 진단·라우팅 흐름 가이드
- `opal/core/references/opal-skills-registry.json` — 매칭 SSOT (v3.6.0)
- 재배포(`bash scripts/install-mac.sh`) 전까지 런타임에서 `//next`는 동작하지 않는다. install 글롭 복사 구조상 스크립트 수정 불필요 — 재배포만으로 `~/.opal/skills/opal-next/` 자동 생성.
- [[skill-opal-start]] — 개명 전 원본 스킬 (deprecated)
- [[skill-opal-onboarding]] — identity.md 부재 시 연계 스킬
- [[skill-opal-project-init]] — 프로젝트 초기화 미완료 시 연계 스킬

## 근거 출처

태스크 030 (`task:030`). `opal/skills/opal-next/SKILL.md`, `opal/core/references/opal-skills-registry.json`

## 관련 페이지

- [[skill-registry-validate-extension]]
