---
type: concept
title: op-oppb-project-slice — OPPB capability 슬라이스 단계 스킬
tags:
- oppb
- slice
- skill
sources:
- skill:op-oppb-project-slice
related: [opal-pilot-project-build, op-oppb-knowledge-finalize]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

승인된 실행 계약(INTENT)을 capability 단위 미니 태스크의 의존 그래프·계약·완료조건 역인덱스로 바꾸는 OPPB P2 단계 스킬이다. 초안 작성자일 뿐이며 승인은 PM, 기계 검증과 상태 생성은 런타임 컨트롤러가 맡는다(`opal/skills/op-oppb-project-slice/SKILL.md:3-7`, `:20`).

## 현재 계약

- 실행 그래프·수용 기준·실행 패킷 파일은 직접 만들지 않고, 컨트롤러가 받아들이는 spec 파일만 쓴다. 범위 해시 계산도 컨트롤러 하나가 소유한다(`opal/skills/op-oppb-project-slice/SKILL.md:24-26`).
- 코드 구현, 사용자 게이트 개방, 상태 전이, 미니 태스크별 작업본·브랜치·문서 파이프라인 설계는 하지 않는다(`opal/skills/op-oppb-project-slice/SKILL.md:28-30`).
- 분할 단위는 같은 비즈니스 개념·변경 이유·정책을 공유하고 사용자가 끝까지 쓸 수 있는 하나의 capability다. 파일 수·레이어 수는 분할 기준이 아니다(`opal/skills/op-oppb-project-slice/SKILL.md:35-38`).
- 화면만, API만, 스키마만 같은 수평 레이어 조각은 별도 미니 태스크로 만들지 않고 capability 안의 작업 항목으로 둔다. 독립 수용 가치와 독립 되돌림 경계가 있을 때만 예외다(`opal/skills/op-oppb-project-slice/SKILL.md:42-54`).

## 관련 페이지

- [[opal-pilot-project-build]]
- [[op-oppb-knowledge-finalize]]
