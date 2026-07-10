---
type: concept
title: opal-pilot-project-loop(oppl) — 2-루프 수렴 오케스트레이터
tags:
- skill
- pilot
- orchestrator
- loop
- oppl
sources:
- task:056
related:
- skill-opal-pilot-project-dev
- skill-opal-pilot-sdd
- loop-upper-bound-ssot-pattern
- opal-evaluator-agent
created: '2026-07-10'
updated: '2026-07-10'
status: active
---
## 개념 요약

oppd의 후계 후보로, 선형 Phase 진행 대신 종료조건이 있는 **2-루프 수렴 구조**(설계 루프 D1~D7 / 실행 루프 L0~L✓)로 규모 있는 프로젝트를 완주시키는 오케스트레이터. alias `oppl`.

## 배경·문제 (WHY)

기존 oppd·opsdd 계열은 선형 Phase 파이프라인이라 "목표 충족까지 반복(loop)"하는 요구를 자연스럽게 표현하기 어려웠다. 설계 방향과 실행 진행은 성격이 다른 수렴 과정이므로, 하나의 선형 흐름 대신 설계 수렴 루프와 실행 수렴 루프를 분리하고 각 루프에 종료조건을 부여해 무한 반복·비용 폭주를 막을 필요가 있었다.

## 결정 내용 (HOW)

설계 루프(D1~D7)는 CONTRACT를 1급 산출물로 하여 Planner 작성 → Evaluator 리뷰(구현 전 명세 심판) → PM 반영 순으로 수렴한다. 실행 루프(L0~L✓)는 `backlog.json`(살아있는 백로그)에서 태스크(얇은 수직 슬라이스)를 선택해 완료까지 반복한다. 종료조건 5종(반복상한·예산·무진전·목표체크·사람게이트)으로 루프 자체를 제어한다. 3-way 모드(semi-agentic 기본)를 승계하며 CLOSE 진입은 agentic 모드에서도 auto-pass를 거부해 사람 게이트를 유지한다. oppd는 즉시 폐기하지 않고 병행 유지하며, 실전 적용 검증 후 deprecate 여부를 판단한다.

## 영향·관계

`opal-evaluator-agent`(설계 루프 명세 심판), `backlog-tool`(백로그 SSOT), `test-tool` scenario-*(실행 루프 동작 검증)에 의존한다. skills-registry·agents.md에 등록되어 있다.

- [[skill-opal-pilot-project-dev]] — 목적은 동일하나 선형 Phase 구조인 선행 오케스트레이터 (병행 유지 대상)
- [[skill-opal-pilot-sdd]] — EXECUTE-LOOP·in-file SSOT 행 테이블 등 루프 골격의 최근접 선례
- [[loop-upper-bound-ssot-pattern]] — 루프 종료조건의 상한 수치 기재 원칙과 정합
- [[opal-evaluator-agent]] — 설계 루프에서 디스패치하는 전담 명세 심판 에이전트

## 근거 출처

task:056 — TASK.md 확정 설계 결정 1·4·10, PLAN.md F-006, DONE.md 요약
