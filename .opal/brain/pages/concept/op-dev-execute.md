---
type: concept
title: op-dev-execute — 코드 실행 단계 스킬
tags:
- dev
- execute
- skill
sources:
- skill:op-dev-execute
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

오케스트레이터가 지정한 체크리스트를 따라 실제 코드를 작성하고 검증하는 EXECUTE 단계 스킬. 에이전트 이름 매핑으로 specialist/generalist 가이드를 자동 선택한다.

## 역할·호출 시점·핵심 규칙

- **역할**: 코드 실행 — 체크리스트(PLAN.md §4 또는 §3) 기반으로 파일 작성/수정/검증
- **호출 시점**: 오케스트레이터(opal-pilot-dev, opal-pilot-dev-short, opal-pilot-dev-wireframe)가 EXECUTE 단계를 디스패치할 때
- **핵심 규칙**: checklist_source 필수 입력; 에이전트 이름→매핑 테이블→실행 가이드 자동 선택; 폴백은 generalist 가이드; 산출물 changed_files 반환

## 파일 참조

`file_path: opal/skills/op-dev-execute/SKILL.md`

## 관련

- [[skill-opal-pilot-dev]] — 이 스킬을 EXECUTE 단계에서 디스패치하는 Dev 오케스트레이터
- [[skill-opal-pilot-dev-short]] — Short Task 경로에서도 이 스킬을 디스패치하는 경량 오케스트레이터
- [[op-dev-plan]] — EXECUTE 단계의 체크리스트 원본을 생성하는 선행 단계 스킬
