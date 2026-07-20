---
type: entity
title: opal-loop-action-agent
tags:
- agent
- oppl
- executor
- action-agent
sources:
- task:065
related:
- oppl-two-loop-orchestrator
- oppl-executor-delegation-architecture
- oppl-3-ssot-tool-gated-separation
- opal-action-monitor
- oppl-run-record-journal-dual-observability
created: '2026-07-17'
updated: '2026-07-17'
status: active
---

## 개요

oppl(opal-pilot-project-loop) Loop 2에서 태스크당 1회만 디스패치되는 일회용 루프 액션 에이전트다. 태스크 내부 파이프라인(T1 명세·설계 → T2 RED-first 시나리오 → G 명세 리뷰 게이트 → T3 구현 → T4a 테스트 → T4b 규칙검사 → T5 마무리)을 끝까지 완주한 뒤, 압축된 결과 계약 1건만 소유자(PM)에게 반환한다.

## 책임 (WHAT)

- 입력 10필드(task_id, task_goal, task_scope, task_area, acceptance, task_folder, verify_commands, contract_path, project_root, project_context)를 받아 태스크 하나를 완주한다 (`opal/agents/opal-loop-action-agent/AGENT.md`).
- 내부적으로 생성자(FE/BE/DB/task 에이전트, T1/T3)·`opal-evaluator-agent`(G 게이트)·`opal-test-agent`(T2 RED / T4a GREEN)·컨벤션·보안 체커(T4b)를 각각 별도 에이전트로 재디스패치한다.
- `test-tool scenario-*`(init/red/lock/mark/status)만 직접 호출한다 — `backlog-tool`·`state-tool`은 호출하지 않는다.
- 결과 계약 6필드(`task_id, verdict, scenario_results, changed_files, done_md_path, blockers`)를 반환한다.
- T5 단계에서 태스크 DONE.md를 직접 작성한다.

## 설계 배경 (WHY)

- 루프 액션 에이전트 도입 이전 oppl은 PM이 태스크당 노미널 3~4회를 직접 디스패치·게이트 판정·산출물 검토하는 구조였고, 백로그 규모가 커질수록 PM 세션 컨텍스트가 누적되어 판단 품질 저하 위험이 있었다 (근거: task:065 PLAN§1.1, DONE.md 요약).
- 상주형 부-PM이 아니라 태스크 1개 수명의 일회용 루프 액션 에이전트로 설계된 이유는, 상주형이면 누적 문제가 PM에서 루프 액션 에이전트로 자리만 옮길 뿐이기 때문이다 (근거: task:065 TASK.md §확정된 설계 방향 1).
- 생성자≠평가자(H-9) 원칙을 유지하기 위해 루프 액션 에이전트 내부에서도 G(Evaluator)와 test-agent를 별도 에이전트로 분리 디스패치한다 (근거: task:065 PLAN§1.5 M-2).
- 비가역 행동(배포·DB·확정)과 에스컬레이션은 루프 액션 에이전트에게 위임하지 않는다 — 루프 액션 에이전트는 blocked만 반환하고, 소유자에게 실제로 에스컬레이션하는 주체는 PM이다 (근거: task:065 TASK.md §확정된 설계 방향 4, PLAN§1.5 M-7).

## 관계 (HOW)

- [[oppl-two-loop-orchestrator]] — 상위 오케스트레이터. PM(L0 태스크 선택·L∞ 관찰·done-check·사람 게이트·소유자 보고)이 이 루프 액션 에이전트를 태스크당 1회 디스패치한다.
- [[oppl-executor-delegation-architecture]] — 이 엔티티를 낳은 설계 결정(M-1~M-13) 묶음.
- [[oppl-3-ssot-tool-gated-separation]] — 이 루프 액션 에이전트가 준수하는 3-SSOT 도구 호출 경계의 선행 개념.
- `opal-evaluator-agent`, `opal-test-agent`, `opal-convention-checker`, `opal-security-checker` — 내부에서 재디스패치하는 기존 워커(신규 워커 없음).
- oppd `opal-task-action-agent`, opsdd `opal-sdd-action-agent` — 구조·frontmatter 관례상 준거가 된 동형 선례.

## 소스 커버리지

| 식별자 | 경로:줄번호 | 설명 |
|--------|-----------|------|
| `opal-loop-action-agent` | `opal/agents/opal-loop-action-agent/AGENT.md` | 루프 액션 에이전트 정의 본체 (frontmatter/입력명세/실행프로세스/결과계약) |
| 디스패치 개편 | `opal/skills/opal-pilot-project-loop/SKILL.md` | oppl 본문 — 태스크당 루프 액션 에이전트 1회 디스패치 구조로 개편 |
