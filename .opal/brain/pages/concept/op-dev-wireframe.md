---
type: concept
title: op-dev-wireframe — 와이어프레임 생성 단계 스킬
tags:
- dev
- wireframe
- skill
sources:
- skill:op-dev-wireframe
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

TASK.md와 입력물(정책서/이미지/구두 요청)을 기반으로 wireframe-builder 스킬에 위임하여 wireframe.md를 생성하는 WIREFRAME 단계 스킬.

## 역할·호출 시점·핵심 규칙

- **역할**: wireframe.md 생성; 실행 주체는 dtp-wireframe-ui-agent 워커
- **호출 시점**: 오케스트레이터(opal-pilot-dev-wireframe)가 WIREFRAME 단계를 디스패치할 때
- **핵심 규칙**: 필수 입력 TASK.md + 입력물; wireframe-builder 스킬에 위임하는 위임형 구조

## 파일 참조

`file_path: opal/skills/op-dev-wireframe/SKILL.md`

## 관련

- [[skill-opal-pilot-dev-wireframe]] — 이 스킬을 WIREFRAME 단계에서 디스패치하는 Wireframe 전용 오케스트레이터
- [[skill-opal-pilot-dev]] — WIREFRAME 단계를 포함하는 확장 Dev 오케스트레이터
