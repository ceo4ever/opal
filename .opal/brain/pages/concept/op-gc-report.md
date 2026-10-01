---
type: concept
title: op-gc-report — GC 결과 정규화·릴리스 판정 스킬
tags:
- gc
- report
- skill
sources:
- skill:op-gc-report
related: [gc-finding-schema, skill-opal-pilot-gc, op-gc-security, op-gc-convention]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

보안·컨벤션 검사가 낸 결과 JSON을 모아 중복을 합치고, 직전 실행 대비 변화와 하나의 릴리스 판정, 기준 문서 업데이트 제안을 만드는 단계 스킬이다. 검사자가 아니라 정규화와 판정만 소유한다(`opal/skills/op-gc-report/SKILL.md:4-6`, `:19`).

## 현재 계약

- 새 발견 사항을 만들거나 소스를 다시 읽지 않고, 입력에 있는 것만 병합·분류한다(`opal/skills/op-gc-report/SKILL.md:21-23`).
- 같은 지문·위치·규칙일 때만 한 건으로 합치며, 지문이 같아도 규칙이 다르면 별건이다(`opal/skills/op-gc-report/SKILL.md:43-47`).
- 직전 결과가 없으면 전부 신규로 보고, 이번에 검사하지 않은 파일의 이전 발견 사항은 해소로 치지 않는다(`opal/skills/op-gc-report/SKILL.md:51-55`).
- 차단 사유는 차단(blocking)으로 분류된 발견 사항뿐이며, 커뮤니티 참조 권고는 심각도가 높아도 차단으로 올리지 않는다. 검사 결측은 통과와 같은 판정으로 묶지 않는다(`opal/skills/op-gc-report/SKILL.md:59-70`).
- 같은 지문이 3개 이상 파일에서 반복되거나, 심각도 critical·high가 있거나, 기준 문서에 없는 새 분류가 나오면 문서 업데이트를 제안만 하고 기준 문서는 고치지 않는다(`opal/skills/op-gc-report/SKILL.md:80-91`).

## 관련 페이지

- [[gc-finding-schema]] — 판정표·지문·delta 원문
- [[skill-opal-pilot-gc]]
- [[op-gc-security]] · [[op-gc-convention]]
