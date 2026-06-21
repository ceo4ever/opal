---
type: concept
title: oppd PRD/TRD 태스크폴더 작성 → docs 승격 프로세스
tags:
- oppd
- prd
- trd
- wbs
- promote
- docs-ssot
sources:
- task:031
related:
- skill-opal-pilot-project-dev
- wbs-세분화-단일책임-수용시나리오
created: '2026-06-21'
updated: '2026-06-21'
status: active
---

## 개념 요약

oppd Phase 1에서 PRD/TRD를 docs/ 직접 작성에서 태스크 폴더 작업본 작성 → 사용자 확정 후 docs/ 승격으로 전환. WBS는 실행 산출물이므로 docs/ 승격 없이 태스크 폴더 전용으로 분리.

## 배경·문제 (WHY)

기존 Phase 1은 opwt가 `docs/PRD.md`·`docs/TRD.md`에 직접 작성했다. 미확정 초안이 프로젝트 SSOT(docs/)를 선오염시키는 문제 — 사용자 확정 전에 정식 문서가 갱신된다.

## 결정 내용 (HOW)

### PRD/TRD 승격 프로세스

1. 작업본 작성: opwt가 `tasks/{NNN}-oppd-…/PRD.md`·`TRD.md`(작업본)로 출력
2. 사용자 확정: 작업본 검토 후 확정 또는 재작업
3. 승격(PM 자동 판단): `docs/PRD.md` 부재 → greenfield(전체 복사) / 존재 → 반복(변경 델타 병합)
4. 후속 등록: `docs/PROJECT.md` 문서 테이블 등록 + `docs/ARCHITECTURE.md` delta

### WBS 비승격 결정

WBS = 실행 산출물 → `tasks/{NNN}-oppd-…/WBS.md` 태스크 폴더 전용. `docs/PROJECT.md` 등록 프로토콜 표에서 WBS.md 행 제거. PRD/TRD 승격과 대비되는 처리.

## 영향·관계

- `opal/skills/opal-pilot-project-dev/SKILL.md` — §Phase 1 절차 표·§1-1 opwt 호출·§1-2 확정 보고·§1-3 승격 단계 신설·§2-5 WBS 등록 제거·문서 등록 프로토콜 표

교차참조: [[skill-opal-pilot-project-dev]], [[wbs-세분화-단일책임-수용시나리오]]

## 근거 출처

task:031 — DONE.md §캡틴 확정 결정 #1, PLAN.md §F-001~F-003
