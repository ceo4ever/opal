---
type: concept
title: 관측 3층 구조 완성 — 데이터 규약·렌더러·발동층 역할 분리
tags:
- oppl
- observability-boundary
- architecture
sources:
- task:068
related:
- opal-action-status
- opal-action-monitor
- oppl-run-record-journal-dual-observability
created: '2026-07-18'
updated: '2026-07-18'
status: active
---
## 개념 요약

루프 액션 에이전트의 진행 현황을 소유자가 확인하는 경로가 데이터 규약(`.oppl-run/` — 이벤트 로그·운행 일지) → 렌더러(도구) → 발동층(스킬)의 3개 층으로 완성됐다. 각 층은 서로 다른 책임을 지며 하위 층의 변경 없이 상위 층만 교체·확장할 수 있다.

## 배경·문제 (WHY)

067에서 데이터 규약과 렌더러(opal-action-monitor)까지는 완성됐지만, 소유자가 그 렌더러를 실제로 발동시키는 진입점이 없어 터미널 명령을 직접 실행하거나 알투에게 자연어로 요청해야 하는 공백이 남아 있었다 — 이 공백이 3번째 층(발동층)의 필요성으로 이어졌다(근거: task:068 TASK.md 배경, PLAN.md §1.1).

## 결정 내용 (HOW)

- **역할 3분할**: ① 데이터 규약(`.oppl-run/` 이벤트 로그·운행 일지, [[oppl-run-record-journal-dual-observability]])이 SSOT를 정의하고, ② 렌더러 도구([[opal-action-monitor]])가 그 SSOT를 읽어 상태 판정·요약을 계산하며, ③ 발동층 스킬([[opal-action-status]])이 자동 탐지 + 도구 호출 + 결과 해석 보고만 수행한다. 도구=결정론 렌더(계산), 스킬=탐지+해석(판단)으로 책임을 나눴다(근거: task:068 PLAN.md §3.1.2).
- **명명으로 층 구분을 드러냄**: 도구는 `opal-action-monitor`(모니터=렌더러), 스킬은 `opal-action-status`(상태=발동층)로 서로 다른 이름을 확정해, 이름만으로도 어느 층인지 구분되게 했다(근거: task:068 DONE.md 명명 절 — 캡틴 확정).
- **자동 탐지는 파일 SSOT 기반**: 발동층의 자동 탐지(loop 루트 backlog.json 우선 → glob 폴백 → 깊이 상한)는 세션 상태가 아니라 파일 시스템 자체(존재·mtime)를 근거로 하므로, 어느 세션에서 발동해도 동일하게 동작한다(근거: task:068 PLAN.md §3.2.2).
- **비복제 원칙**: 상위 층(스킬)은 하위 층(도구)의 상태 판정 규칙·수치·JSON 스키마를 본문에 재서술하지 않고 포인터로만 참조한다 — 층 간 값 drift를 막기 위함이다(근거: task:068 PLAN.md §3.1.2 H-4).
- **커버리지 경계는 전방 호환 설계**: 3층 구조는 현재 oppl(`.oppl-run/` 규약을 준수하는 루프)에만 적용되지만, oppd·opsdd의 액션 에이전트가 동일 규약으로 전환되면 렌더러·발동층 모두 무변경으로 커버리지가 확장되도록 설계했다 — 파일 규약 준수 여부만으로 렌더 대상을 판단하기 때문이다(근거: task:068 PLAN.md §3.1.2 커버리지 경계, 후속 메모 `memory/후속_069_070_액션에이전트_관측_확장.md`).

## 영향·관계

[[opal-action-status]]가 신설된 발동층이며, [[opal-action-monitor]]가 렌더러, [[oppl-run-record-journal-dual-observability]]가 데이터 규약을 정의한다. 이 3층 분리는 069·070에서 oppd·opsdd 액션 에이전트가 같은 규약으로 전환될 때 확장 기준선이 된다.

## 근거 출처

task:068 — TASK.md §배경, PLAN.md §1.1·§3.1.2·§3.2.2, DONE.md 명명 절·후속 백로그.
