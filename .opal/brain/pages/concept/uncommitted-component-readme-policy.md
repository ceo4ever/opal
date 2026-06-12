---
type: concept
title: 미커밋 컴포넌트는 공개 README에 미노출
tags: [readme, policy, git, documentation, ppt-builder]
sources: [task:018]
related: [readme-ssot-principle]
created: 2026-06-12
updated: 2026-06-12
status: active
---

## 개요

미커밋(`??` untracked 또는 레지스트리 `M` 상태) 컴포넌트는 공개 README에 등재하지 않는다. 공개 문서에 동작하지 않는 기능을 기술하면 신규 사용자가 혼란을 겪기 때문이다.

## 결정 배경 (WHY)

task:018에서 `skills/ppt-builder/`가 미추적(`??`) 상태이고 레지스트리도 미커밋(`M`) 상태이며, `docs/PROJECT.md` 주요 컴포넌트에도 등재되지 않았다. README는 공개 소개 문서이므로 아직 정식 컴포넌트가 아닌 작업 중 산출물을 노출하면 실제로 동작하지 않는 기능을 사용자에게 안내하게 된다.

## 결정 내용

- 컴포넌트 등재 기준: git 커밋 완료 + 레지스트리 정식 등록 + PROJECT.md 주요 컴포넌트 기재 중 최소 1개 충족.
- `skills/ppt-builder/`는 정식 커밋 후 README 독립 스킬 섹션에 1줄 추가로 등재 전환 가능.
- 미커밋 상태에서는 decision_required 처리하고 캡틴 확정을 기다린다.

## 영향 범위

- `README.md` §독립 스킬 사용법 — task:018에서 ppt-builder 미등재 유지
- 향후 ppt-builder 정식 커밋 시 즉시 등재 가능(이 결정으로 절차 명확화)

## 관련 페이지

- [[readme-ssot-principle]]
