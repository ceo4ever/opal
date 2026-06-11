---
type: concept
title: OPAL Principles 헌법 신설 + 테스트 하네스 집행 강화
tags:
- principles
- constitution
- testing
- framework
- task
sources:
- task:012
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

카파시 스킬 철학을 담은 `opal/core/PRINCIPLES.md`를 단일 SSOT로 신설하고 always-on 로드로 등록했다. 테스트 하네스 3개 파일이 헌법 §4("목업 금지·동작 증거")를 참조·집행하도록 강화했다.

## 배경·문제 (WHY)

행동 원칙이 `coding-principles.md`·`qa-standards.md` 등 여러 파일에 분산되어 있었다. "작성자 신뢰"·"grep=Pass"·"구현 목업 대체" 3대 구멍이 실제 회귀 사례에서 발현되었다.

## 결정 내용 (HOW)

- `opal/core/PRINCIPLES.md` 영문 신규 작성 — 흩어진 행동 원칙의 단일 SSOT.
- `AGENT.md` Eager Step 2.5에 헌법 always-on 등록(v2.9).
- `coding-principles.md` 헌법 참조 슬림화 + 목업·증거 체크(v1.3).
- `qa-standards.md` EXECUTE QA 동작 증거 의무화.
- `opal-test-agent/AGENT.md` adversarial + 증거 + 목업 Fail 강화(v1.3).
- install-mac.sh(v2.8)·windows.ps1(v1.10.0)으로 헌법 배포.

## 영향·관계

- [[coding-principles-ssot]] 에서 시작된 원칙 SSOT화의 상위 레이어 완성.
- [[test-scenario-pipeline-redesign]] 의 mock 금지 정책과 연동 강화.

## 근거 출처

`sources: task:012` — DONE.md §완료 요약·성과 참조.
