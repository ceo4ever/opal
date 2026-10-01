---
type: concept
title: op-gc-security — 보안 검사 단계 스킬
tags:
- gc
- security
- skill
sources:
- skill:op-gc-security
related: [gc-finding-schema, skill-opal-pilot-gc, op-gc-convention, op-gc-report]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

호출자가 정해 준 파일만 읽기 전용으로 보안 점검하고, 발견 사항(finding)을 사람용 보고서와 기계용 JSON으로 함께 돌려주는 단계 스킬이다. GC Pilot의 CHECK 단계나 다른 파이프라인이 보안 검사를 워커에게 맡길 때 쓴다(`opal/skills/op-gc-security/SKILL.md:3-6`).

## 현재 계약

- 기준은 프로젝트 보안 문서(`docs/SECURITY.md`) → 실제로 집행되는 CI·보안 설정 → 승인된 공식 표준(OWASP·CWE·SANS) → 검토된 커뮤니티 참조 순으로 찾고, 상위 기준이 이긴다. 커뮤니티 참조에서 나온 발견 사항은 항상 권고(advisory)로만 남는다(`opal/skills/op-gc-security/SKILL.md:27-34`).
- 대상 파일 확장자나 실재하는 의존성 매니페스트로 근거가 확인된 영역만 켜고, 끈 영역과 그 이유를 결과에 남긴다(`opal/skills/op-gc-security/SKILL.md:36-40`).
- 검사 대상은 호출자가 넘긴 목록 그대로이며 스스로 넓히거나 줄이지 않는다. 실제 검사 목록이 다르면 부분 완료(partial)로 낮춘다(`opal/skills/op-gc-security/SKILL.md:77`).
- 발견 사항의 필드·판정 규칙은 공유 스키마 문서가 소유하고 이 스킬은 복제하지 않는다(`opal/skills/op-gc-security/SKILL.md:11-12`).

## 관련 페이지

- [[gc-finding-schema]] — 발견 사항 필드·판정 원문
- [[skill-opal-pilot-gc]] — 이 스킬을 CHECK 단계에서 호출하는 Pilot
- [[op-gc-convention]] · [[op-gc-report]] — 같은 단계의 형제 스킬
