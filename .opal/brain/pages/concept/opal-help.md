---
type: concept
title: opal-help — 스킬 카탈로그·사용법 안내 스킬
tags:
- help
- catalog
- skill
sources:
- skill:opal-help
related: [skill-registry-validate-extension, skill-registry-index-registration-required-for-discovery]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

사용자가 호출할 수 있는 스킬을 한눈에 보여 주고 특정 스킬의 기능·사용법·예시를 안내하는 읽기 전용 operator 스킬이다. 파일 수정이나 워커 디스패치 없이 스킬 레지스트리 도구 조회만 한다(`opal/skills/opal-help/SKILL.md:3-6`, `:21-22`).

## 현재 계약

- 스킬 메타데이터의 단일 원천은 JSON 레지스트리이고, 도구 호출이 실패할 때만 배포된 스킬 목록 문서로 폴백한다(`opal/skills/opal-help/SKILL.md:26-34`).
- 운영 CLI는 `//` 스킬이 아니므로 레지스트리에 없고, 그 사용법은 CLI 자체 도움말 출력을 그대로 보여 준다(`opal/skills/opal-help/SKILL.md:36`).
- 인자 없으면 사용자 호출 스킬 카탈로그, `--all`이면 내부 단계 스킬까지, 스킬명·별칭을 주면 해당 스킬 상세를 안내한다(`opal/skills/opal-help/SKILL.md:44-47`).

## 관련 페이지

- [[skill-registry-validate-extension]]
- [[skill-registry-index-registration-required-for-discovery]]
