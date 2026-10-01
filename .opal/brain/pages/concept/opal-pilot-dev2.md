---
type: concept
title: opal-pilot-dev2 (opd2) — AI-native SDLC Pilot
tags:
- opd2
- pilot
- skill
sources:
- skill:opal-pilot-dev2
related: [opd2-state-tool-integration, skill-opal-pilot-dev, opal-skill-tester]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

아이디어·변경·인시던트를 intent → spec → plan → 구현 → 독립 검증 → 리뷰로 잇는 AI-native 개발 Pilot이다. 기존 opd에서는 진행 모드와 작업본 생성·소유권·체크포인트·마감 절차만 가져오고, 자체 생명주기는 따로 운영한다(`opal/skills/opal-pilot-dev2/SKILL.md:3-13`).

## 현재 계약

- 지원 범위는 빌드까지(리뷰 완료·머지 대기)이며, 배포·관측 요청은 명시 거부하고 빌드로 진행할지 사용자에게 확인한다(`opal/skills/opal-pilot-dev2/SKILL.md:17-23`).
- 시작 시와 각 단계(TASK·DESIGN·PLAN·EXECUTE·VERIFY) 진입마다 FW 이벤트를 로드·검증한다. 전용 VERIFY 이벤트는 새로 만들지 않고 TEST 이벤트를 재사용한다(`opal/skills/opal-pilot-dev2/SKILL.md:24-55`).
- 구현 진입 전 PLAN 사전심사는 두 층이다. 완료조건 전체가 계획에 덮이는지를 도구가 기계적으로 보고, 두 독립 리뷰가 같은 문서 지문에서 모두 통과해야 구현으로 넘어간다(`opal/skills/opal-pilot-dev2/SKILL.md:79-85`).
- 구현자·검증자·리뷰어는 매번 새 독립 에이전트로 호출하며 서로 겸하지 않는다. 구현자는 프로젝트 구성에 맞는 전문 에이전트를 우선 쓰고, 검증자·리뷰어는 범용 워커다(`opal/skills/opal-pilot-dev2/SKILL.md:87-107`).
- 단계 상태의 단일 원천은 태스크 상태 파일이며, 자체 원장은 게이트 판정 후 상태 도구 커밋이 성공해야 함께 커밋된다(`opal/skills/opal-pilot-dev2/SKILL.md:118`).

## 관련 페이지

- [[opd2-state-tool-integration]] — 상태 단일화·FW 계약 연결 결정(task:168)
- [[skill-opal-pilot-dev]] — 진행 모드·작업본 절차를 빌려 온 기존 Pilot
- [[opal-skill-tester]] — opd2 스모크 실행 검증
