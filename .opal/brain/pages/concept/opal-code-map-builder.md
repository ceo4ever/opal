---
type: concept
title: opal-code-map-builder (opcmb) — @header 자산 구축 스킬
tags:
- code-scan
- header
- skill
sources:
- skill:opal-code-map-builder
related: [code-scan-tool, header-standard-doc, code-scan-manifest-sharding-design]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

프로젝트 코드 설명 헤더(@header)를 어디에 기록할지 소유자 확정으로 정하고, 매니페스트 방식 프로젝트에서는 별도 코드맵 매니페스트를 구축·정비하는 스킬이다. 판정·기록은 코드 스캔 도구가 하고 이 스킬은 확정값 중개와 순서 집행만 맡는 호출층이다(`opal/skills/opal-code-map-builder/SKILL.md:3-6`, `:34`).

## 현재 계약

- 모드는 자산 존재로 자동 판별한다. 설정이 없거나 무효면 초기 구축, 매니페스트 방식인데 색인이 없으면 매니페스트 구축, 색인이 있으면 정비, 소스 파일 안 헤더 방식이면 누락 점검 안내로 끝낸다(`opal/skills/opal-code-map-builder/SKILL.md:45-52`).
- 색인의 검토 상태(draft·reviewed)는 모드 판별에 쓰지 않고 소유자 리뷰 표시로만 쓴다(`opal/skills/opal-code-map-builder/SKILL.md:54`).
- 절차의 원천은 헤더 표준·코드맵 관리·헤더 갱신 규칙 문서이며 이 스킬은 그 순서를 따른다(`opal/skills/opal-code-map-builder/SKILL.md:36-39`).

## 관련 페이지

- [[code-scan-tool]]
- [[header-standard-doc]]
- [[code-scan-manifest-sharding-design]]
