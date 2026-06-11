---
type: concept
title: opal-pilot-dev-wireframe — Wireframe UI 오케스트레이터
tags:
- skill
- pilot
- orchestrator
- wireframe
- ui
sources:
- skill:opal-pilot-dev-wireframe
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

와이어프레임 UI 오케스트레이터. 와이어프레임 설계부터 UI 구현까지 4단계 파이프라인(TASK → WIREFRAME → EXECUTE → CLOSE)으로 수행한다.

## 배경·문제 (WHY)

신규 UI를 wireframe 단계부터 시작해야 하는 경우 별도 파이프라인이 필요하다. 기존 프로젝트 기반 UI 작업은 opds/opd의 ui-designer plan-driven 모드로 처리한다.

## 결정 내용 (HOW)

입력 유형에 따라 분기: wireframe.md 존재 시 WIREFRAME 스킵, 문서/이미지/구두 요청에 따라 interview 후 WIREFRAME 진행. 출력 모드는 프로토타입(bundle.html) 또는 프로덕션(Next.js) 중 선택.

## 영향·관계

opds/opd와 보완 관계. 신규 UI 전용 진입점으로 WIREFRAME 단계가 추가된 파이프라인이다.

## 관련

- [[op-dev-wireframe]] — WIREFRAME 단계에서 디스패치하는 와이어프레임 워커 스텝
- [[op-dev-execute]] — EXECUTE 단계에서 UI 코드를 실행하는 워커 스텝
- [[opal-project-definition]] — Wireframe 파이프라인의 컨텍스트 로딩 기준 문서

## 근거 출처

file_path: `opal/skills/opal-pilot-dev-wireframe/SKILL.md`
