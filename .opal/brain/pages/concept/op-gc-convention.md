---
type: concept
title: op-gc-convention — 컨벤션 검사 단계 스킬
tags:
- gc
- convention
- skill
sources:
- skill:op-gc-convention
related: [gc-finding-schema, skill-opal-pilot-gc, op-gc-security, op-gc-report]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

호출자가 확정한 파일 목록을 프로젝트 컨벤션 기준으로 읽기 전용 점검하고, 보고서와 발견 사항 JSON을 같은 데이터에서 함께 만드는 단계 스킬이다. GC Pilot CHECK 단계나 PM Gate의 컨벤션 검사에서 호출된다(`opal/skills/op-gc-convention/SKILL.md:3-7`).

## 현재 계약

- 기준은 프로젝트 컨벤션 문서(`docs/CONVENTIONS.md`, 허브+링크 구조) → formatter·linter 등 실행 설정 → 인접 코드에서 관측한 패턴 → 언어 공식 style guide → 커뮤니티 참조(권고 고정) 순으로 찾고, 실제로 쓴 출처를 발견 사항마다 남긴다(`opal/skills/op-gc-convention/SKILL.md:28-36`).
- 컨벤션 문서가 없어도 검사를 건너뛰지 않고, 관측 기반 권고로 수행한다(`docs/PROJECT.md:143`).
- 대상 경로가 없거나 프로젝트 밖이면 검사를 시작하지 않고 오류로 반환한다(`opal/skills/op-gc-convention/SKILL.md:40-41`).
- 발견 사항 필드·판정은 공유 스키마 문서가 소유한다(`opal/skills/op-gc-convention/SKILL.md:12-13`).

## 관련 페이지

- [[gc-finding-schema]]
- [[skill-opal-pilot-gc]]
- [[op-gc-security]] · [[op-gc-report]]
