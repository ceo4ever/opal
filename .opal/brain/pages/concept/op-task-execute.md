---
type: concept
title: op-task-execute — 범용 실행 단계 스킬
tags:
- task
- execute
- skill
sources:
- skill:op-task-execute
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

PLAN.md의 실행 체크리스트를 따라 파일 작성/수정/삭제를 수행하는 범용 실행 스킬. op-dev-execute의 도메인 무관 버전이다.

## 역할·호출 시점·핵심 규칙

- **역할**: 파일 변경 실행 + changed_files 반환; op-dev-execute 대비 언어/프레임워크 특화 가이드 없이 범용으로 동작
- **호출 시점**: 오케스트레이터(opal-pilot-project)가 EXECUTE 단계를 디스패치할 때
- **핵심 규칙**: 필수 입력 checklist_source(PLAN.md §3); 워커 에이전트 실행(PM 매핑 테이블 기준, 폴백: opal-task-agent)

## 파일 참조

`file_path: opal/skills/op-task-execute/SKILL.md`

## 관련

- [[skill-opal-pilot-project]] — 이 스킬을 EXECUTE 단계에서 디스패치하는 Project 오케스트레이터
- [[op-task-plan]] — 이 스킬의 체크리스트 원본(PLAN.md)을 생성하는 선행 단계 스킬
