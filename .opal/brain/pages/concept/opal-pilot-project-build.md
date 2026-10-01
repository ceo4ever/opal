---
type: concept
title: opal-pilot-project-build (oppb) — 확정 계약 무인 소화 Pilot
tags:
- oppb
- pilot
- skill
sources:
- skill:opal-pilot-project-build
related: [oppb-run-records-follow-task-lifecycle, op-oppb-project-slice, op-oppb-knowledge-finalize, oppl-two-loop-orchestrator, skill-opal-pilot-project-dev]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

한 번의 설계 승인으로 목표·계약·완료조건을 잠글 수 있는 프로젝트를, 프로젝트 작업본 1개·OPAL 태스크 1건·실행 계약 문서(INTENT) 1개 안에서 capability 단위 미니 태스크로 끝까지 소화하는 프로젝트 Pilot이다(`opal/skills/opal-pilot-project-build/SKILL.md:3-12`, `:22-24`).

## 현재 계약

- 선택 기준은 "계약을 한 번에 잠글 수 있는가"이다. 실행 증거로 계약이 계속 바뀌면 수렴형 Pilot(oppl), 명세 작성부터 필요하면 oppd, 단일 태스크 규모면 opd·opds를 쓴다(`opal/skills/opal-pilot-project-build/SKILL.md:31-40`).
- 기존 Pilot을 대체하지 않으며, 한 Pilot 안에 두 실행 경로를 넣는 엔진 선택 옵션을 만들지 않는다(`opal/skills/opal-pilot-project-build/SKILL.md:42-44`).
- 사용자에게 보이는 표면은 P0~P5 여섯 단계와 사용자 게이트 6종뿐이고, 일정·예산·작업 소유 범위(lease)·체크포인트·증거는 런타임 도구(`oppb-runtime-tool`)가 결정론적으로 집행한다(`opal/skills/opal-pilot-project-build/SKILL.md:22-24`).
- 각 단계 진입마다 FW 단계 이벤트를 로드·검증한다(P0 task ~ P5 close 매핑)(`opal/skills/opal-pilot-project-build/SKILL.md:58-70`).
- 무인 실행 구간은 P3~P4뿐이며, P5 merge 게이트는 자동 통과를 거부하고 소유자 발화를 요구한다(`docs/PROJECT.md:86`).

## 관련 페이지

- [[op-oppb-project-slice]] — P2 슬라이스 단계
- [[op-oppb-knowledge-finalize]] — P5 지식 반영 단계
- [[oppb-run-records-follow-task-lifecycle]] — 실행 기록의 태스크 귀속
- [[oppl-two-loop-orchestrator]] · [[skill-opal-pilot-project-dev]] — 병존하는 프로젝트 Pilot
