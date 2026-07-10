---
type: concept
title: 3-SSOT tool-gated 축 분리 — backlog/state/test-scenario
tags:
- ssot
- tool-gated
- oppl
- architecture
sources:
- task:056
related:
- oppl-two-loop-orchestrator
- state-tool
- test-two-tier-system
created: '2026-07-10'
updated: '2026-07-10'
status: active
---
## 개념 요약

oppl은 진행 상태를 `backlog.json`(신규 backlog-tool)·`state.json`(기존 state-tool 확장)·`test-scenario.json`(기존 test-tool 확장) 3개의 tool-gated JSON SSOT로 축 분리하고, 사람 뷰(BACKLOG.md/STATE.md/TEST-SCENARIO.md)는 각 도구가 자동 렌더한다.

## 배경·문제 (WHY)

backlog(살아있는 백로그)·state(파이프라인 진행)·test-scenario(검증 스펙+결과)는 서로 다른 관심사이자 갱신 주기·소유 주체를 가진다. 하나의 JSON에 섞으면 서로 다른 갱신이 충돌한다. 또한 마크다운 손편집을 허용하면 도구가 렌더한 뷰와 실제 JSON이 어긋나는 double-truth가 재발한다는 리스크가 식별되었다.

## 결정 내용 (HOW)

- `backlog.json`: 신규 `backlog-tool`(6서브명령, fcntl 배타 락, BACKLOG.md 자동 렌더)이 전담
- `state.json`: 기존 `state-tool`을 `--skill` enum에 `oppl` 추가로 소폭 확장(재사용)
- `test-scenario.json`: 기존 `test-tool`에 scenario-init/lock/mark/status 4서브명령 추가(RED-first 동결 게이트)로 확장
- 3종 모두 상호 참조 없이 축 분리하며, 손편집을 금지하고 오직 각 도구 CLI를 통해서만 갱신한다.

## 영향·관계

`opal/tools/backlog-tool/`(신규)·`opal/tools/state-tool/state_tool.py`(enum 확장)·`opal/tools/test-tool/lib/scenario.py`(신규 핸들러)에 반영되었다. oppl SKILL의 D5(백로그 생성)/L0(태스크 선택)/L∞(관찰)/L✓(종료 판정) 단계와 T2(테스트 시나리오 RED-first)/T4a(동작 검증 결과 기록) 단계가 각각 호출한다.

- [[oppl-two-loop-orchestrator]] — 이 SSOT 분리를 소비하는 오케스트레이터
- [[state-tool]] — 3종 중 재사용 확장된 기존 SSOT 도구
- [[test-two-tier-system]] — 검증 계층 구조와의 정합 맥락

## 근거 출처

task:056 — TASK.md 확정 설계 결정 7, PLAN.md F-001/F-002/F-003, 리스크 H-3·H-6
