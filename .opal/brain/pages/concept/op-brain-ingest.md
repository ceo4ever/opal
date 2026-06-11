---
type: concept
title: op-brain-ingest — CLOSE 경량 ingest 워커
tags:
- knowledge
- close
- ingest
- skill
sources:
- skill:op-brain-ingest
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

CLOSE 단계 파일럿(opp 등)이 DONE.md 생성 직후 디스패치하는 경량 워커 스킬. 완료된 태스크의 의사결정·신규 컴포넌트·인터페이스 변경·도메인 지식을 `brain-tool`을 통해 `.opal/brain/`에 누적한다.

## 역할·호출 시점·핵심 규칙

- **역할**: 태스크 완료 시점에 brain에 지식을 자동 누적하는 CLOSE 전용 경량 ingest 워커
- **호출 시점**: CLOSE 단계 파일럿이 DONE.md 생성 직후 디스패치
- **핵심 규칙**: 포함 기준(아키텍처 결정·신규 컴포넌트·인터페이스 변경·도메인 지식)을 적용하여 concept 페이지 1건 생성; `.opal/brain/`이 없는 프로젝트에서는 즉시 no-op 반환; brain→origin 역수정 절대 금지

## 파일 참조

`file_path: opal/skills/op-brain-ingest/SKILL.md`

## 관련

- [[skill-opal-brain]] — 이 스킬이 지식을 누적하는 OPAL Brain 운영 파일럿
- [[opal-brain-system]] — op-brain-ingest가 페이지를 적재하는 brain 시스템 아키텍처
